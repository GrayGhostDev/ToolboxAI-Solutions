"""
Authentication and Authorization Module for ToolboxAI Roblox Environment

Provides JWT authentication, OAuth for LMS platforms, API key validation,
rate limiting, and user session management.
"""

import hashlib
import json
import logging
import os
import secrets
import time
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any, Dict, List, Optional, cast

import jwt
import redis
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from requests_oauthlib import OAuth1Session

from apps.backend.core.config import settings
from apps.backend.models.schemas import Session, User
from apps.backend.core.security.rate_limiter import get_rate_limit_manager
# Secure JWT secret management
try:
    from apps.backend.core.security.jwt import get_secure_jwt_secret
except ImportError:
    # Fallback for development
    def get_secure_jwt_secret():
        return settings.JWT_SECRET_KEY

logger = logging.getLogger(__name__)

# Constants
DEFAULT_RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_RETRY_AFTER = 60  # seconds

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Security
security = HTTPBearer(
    auto_error=False
)  # Don't auto-error, handle missing auth manually

# Redis client for session management and rate limiting
try:
    redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    redis_client.ping()
    logger.info("Redis connection established for auth module")
except (
    redis.ConnectionError,
    redis.TimeoutError,
    redis.RedisError,
    AttributeError,
) as e:
    logger.warning(f"Redis connection failed: {e}. Using in-memory storage.")
    redis_client = None

# In-memory fallback storage
memory_store: Dict[str, Any] = {}


def _safe_redis_int(value: Any, default: int = 1) -> int:
    """Coerce a redis response to int while being robust to Awaitable stubs."""
    try:
        if hasattr(value, "__int__"):
            return int(value)
        if isinstance(value, (str, bytes, bytearray)):
            return int(value)
    except Exception:
        pass
    return default


class AuthenticationError(HTTPException):
    """Custom authentication error"""

    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(HTTPException):
    """Custom authorization error"""

    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class RateLimitError(HTTPException):
    """Rate limit exceeded error"""

    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers={"Retry-After": str(RATE_LIMIT_RETRY_AFTER)},
        )


class JWTManager:
    """JWT token management"""

    @staticmethod
    def create_access_token(
        data: Dict[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
            )
        # Use integer epoch timestamps for JWT claims
        to_encode.update(
            {
                "exp": int(expire.timestamp()),
                "iat": int(datetime.now(timezone.utc).timestamp()),
            }
        )

        encoded_jwt = jwt.encode(
            to_encode, get_secure_jwt_secret(), algorithm=settings.JWT_ALGORITHM
        )

        return encoded_jwt

    @staticmethod
    def create_refresh_token(
        user_id: str,
        token_family: Optional[str] = None,
        expires_delta: Optional[timedelta] = None
    ) -> tuple[str, str]:
        """Create JWT refresh token with family tracking for rotation

        Returns:
            Tuple of (refresh_token, token_family_id)
        """
        # Generate token family ID if not provided (for initial login)
        if not token_family:
            token_family = secrets.token_urlsafe(32)

        to_encode = {
            "sub": user_id,
            "type": "refresh",
            "family": token_family,
            "jti": secrets.token_urlsafe(16),  # Unique token ID for tracking
        }

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
            )

        to_encode.update({
            "exp": int(expire.timestamp()),
            "iat": int(datetime.now(timezone.utc).timestamp()),
        })

        encoded_jwt = jwt.encode(
            to_encode, get_secure_jwt_secret(), algorithm=settings.JWT_ALGORITHM
        )

        # Store token family in Redis for tracking (detect token reuse)
        if redis_client:
            family_key = f"token_family:{token_family}"
            redis_client.setex(
                family_key,
                int(timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 2).total_seconds()),
                json.dumps({
                    "user_id": user_id,
                    "latest_jti": to_encode["jti"],
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
            )

        return encoded_jwt, token_family

    @staticmethod
    def verify_token(token: str, raise_on_error: bool = True) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token

        Args:
            token: JWT token to verify
            raise_on_error: If True, raise exceptions on errors. If False, return None.

        Returns:
            Decoded payload if valid, None if invalid and raise_on_error is False
        """
        try:
            payload = jwt.decode(
                token, get_secure_jwt_secret(), algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except jwt.ExpiredSignatureError:
            if raise_on_error:
                raise AuthenticationError("Token has expired")
            return None
        except jwt.PyJWTError:
            if raise_on_error:
                raise AuthenticationError("Invalid token")
            return None

    @staticmethod
    def verify_refresh_token(token: str) -> tuple[Optional[Dict[str, Any]], bool]:
        """Verify refresh token and check for reuse attacks

        Returns:
            Tuple of (payload, is_compromised)
            If is_compromised is True, the entire token family should be invalidated
        """
        try:
            payload = jwt.decode(
                token, get_secure_jwt_secret(), algorithms=[settings.JWT_ALGORITHM]
            )

            # Check if this is a refresh token
            if payload.get("type") != "refresh":
                return None, False

            # Check token family for reuse detection
            family_id = payload.get("family")
            token_jti = payload.get("jti")

            if redis_client and family_id:
                family_key = f"token_family:{family_id}"
                family_data = redis_client.get(family_key)

                if family_data:
                    family_info = json.loads(family_data)
                    latest_jti = family_info.get("latest_jti")

                    # If this token's JTI is older than the latest, it's a reuse
                    if latest_jti and token_jti != latest_jti:
                        # Token reuse detected! Invalidate entire family
                        redis_client.delete(family_key)
                        logger.warning(f"Token reuse detected for family {family_id}")
                        return None, True

            return payload, False

        except jwt.ExpiredSignatureError:
            return None, False
        except jwt.PyJWTError:
            return None, False


class SessionManager:
    """User session management"""

    @staticmethod
    def create_session(
        user_id: str,
        roblox_user_id: Optional[str] = None,
        studio_id: Optional[str] = None,
    ) -> Session:
        """Create a new user session"""
        session = Session(
            user_id=user_id,
            roblox_user_id=roblox_user_id,
            studio_id=studio_id,
            expires_at=datetime.now(timezone.utc)
            + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        # Store session
        session_key = f"session:{session.id}"
        # Convert to JSON-serializable dict without relying on Pydantic internals
        session_data = {
            "id": session.id,
            "user_id": session.user_id,
            "roblox_user_id": session.roblox_user_id,
            "studio_id": session.studio_id,
            "created_at": session.created_at.isoformat() if getattr(session, "created_at", None) else datetime.now(timezone.utc).isoformat(),
            "expires_at": session.expires_at.isoformat() if getattr(session, "expires_at", None) else (datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)).isoformat(),
        }

        if redis_client:
            redis_client.setex(
                session_key,
                timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
                json.dumps(session_data, default=str),
            )
        else:
            memory_store[session_key] = session_data

        logger.info(f"Created session {session.id} for user {user_id}")
        return session

    @staticmethod
    def get_session(session_id: str) -> Optional[Session]:
        """Get session by ID"""
        session_key = f"session:{session_id}"

        if redis_client:
            session_data = redis_client.get(session_key)
            if session_data:
                if isinstance(session_data, (str, bytes, bytearray)):
                    data = json.loads(session_data)
                else:
                    data = cast(Dict[str, Any], session_data)
                return Session(**data)
        else:
            session_data = memory_store.get(session_key)
            if session_data:
                if isinstance(session_data, (str, bytes, bytearray)):
                    data = json.loads(session_data)
                else:
                    data = cast(Dict[str, Any], session_data)
                return Session(**data)

        return None

    @staticmethod
    def invalidate_session(session_id: str) -> bool:
        """Invalidate a session"""
        session_key = f"session:{session_id}"

        if redis_client:
            result = redis_client.delete(session_key)
            return result > 0
        else:
            return memory_store.pop(session_key, None) is not None


class RateLimiter:
    """Rate limiting functionality (now uses centralized manager)"""

    @staticmethod
    def check_rate_limit(
        identifier: str,
        window_seconds: int = DEFAULT_RATE_LIMIT_WINDOW,
        max_requests: int = None,
    ) -> bool:
        """Check if request is within rate limit"""
        if max_requests is None:
            max_requests = settings.RATE_LIMIT_PER_MINUTE

        # Use centralized rate limit manager
        manager = get_rate_limit_manager()

        # Convert async call to sync for backward compatibility
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        allowed, _ = loop.run_until_complete(
            manager.check_rate_limit(
                identifier=identifier,
                max_requests=max_requests,
                window_seconds=window_seconds,
                source="auth"
            )
        )
        return allowed

    @staticmethod
    def rate_limit_decorator(
        max_requests: int = None, window_seconds: int = DEFAULT_RATE_LIMIT_WINDOW
    ):
        """Decorator for rate limiting endpoints"""

        def decorator(func):
            @wraps(func)
            async def wrapper(request: Request, *args, **kwargs):
                client_ip = request.client.host
                identifier = f"{client_ip}:{func.__name__}"

                # Convert to async check
                manager = get_rate_limit_manager()
                requests_limit = max_requests if max_requests is not None else settings.RATE_LIMIT_PER_MINUTE

                allowed, _ = await manager.check_rate_limit(
                    identifier=identifier,
                    max_requests=requests_limit,
                    window_seconds=window_seconds,
                    source="auth"
                )

                if not allowed:
                    raise RateLimitError(f"Rate limit exceeded for {func.__name__}")

                return await func(request, *args, **kwargs)

            return wrapper

        return decorator


class LMSAuthenticator:
    """LMS platform authentication"""

    @staticmethod
    def get_schoology_session(
        user_token: str = None, user_secret: str = None
    ) -> OAuth1Session:
        """Create Schoology OAuth1 session"""
        if not settings.SCHOOLOGY_KEY or not settings.SCHOOLOGY_SECRET:
            raise ValueError("Schoology API credentials not configured")

        return OAuth1Session(
            settings.SCHOOLOGY_KEY,
            client_secret=settings.SCHOOLOGY_SECRET,
            resource_owner_key=user_token,
            resource_owner_secret=user_secret,
        )

    @staticmethod
    def get_canvas_headers(user_token: str = None) -> Dict[str, str]:
        """Get Canvas API headers"""
        token = user_token or settings.CANVAS_TOKEN
        if not token:
            raise ValueError("Canvas API token not configured")

        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    @staticmethod
    def verify_lms_credentials(platform: str, credentials: Dict[str, str]) -> bool:
        """Verify LMS credentials"""
        try:
            if platform == "schoology":
                session = LMSAuthenticator.get_schoology_session(
                    credentials.get("token"), credentials.get("secret")
                )
                # Test request to verify credentials
                response = session.get("https://api.schoology.com/v1/users/me")
                return response.status_code == 200

            elif platform == "canvas":
                headers = LMSAuthenticator.get_canvas_headers(credentials.get("token"))
                import requests

                response = requests.get(
                    f"{settings.CANVAS_BASE_URL}/api/v1/users/self", headers=headers
                )
                return response.status_code == 200

        except (requests.RequestException, ValueError, KeyError) as e:
            logger.error(f"LMS credential verification failed: {e}")
            return False

        return False


class APIKeyManager:
    """API key management for service authentication"""

    @staticmethod
    def generate_api_key(user_id: str, service: str) -> str:
        """Generate API key for a user/service"""
        random_part = secrets.token_hex(16)
        data = f"{user_id}:{service}:{random_part}:{int(time.time())}"
        return hashlib.sha256(data.encode()).hexdigest()

    @staticmethod
    def validate_api_key(api_key: str) -> Optional[Dict[str, str]]:
        """Validate API key and return associated data"""
        # In production, this would query a database
        # For now, we'll use a simple validation
        if len(api_key) == 64 and all(c in "0123456789abcdef" for c in api_key):
            return {"valid": True, "user_id": "api_user", "service": "roblox"}
        return None


# Dependency functions for FastAPI
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> User:
    """Get current authenticated user"""
    # SECURE: Development mode bypass ONLY if explicitly enabled via feature flag
    # This prevents accidental bypass activation in production
    try:
        from apps.backend.core.feature_flags import get_feature_flags, FeatureFlag
        feature_flags = get_feature_flags()

        # Triple-check: feature flag + environment + explicit testing opt-out
        development_bypass_enabled = (
            feature_flags.is_enabled(FeatureFlag.DEVELOPMENT_AUTH_BYPASS) and
            settings.DEBUG and
            settings.ENVIRONMENT == "development" and
            not os.getenv("TESTING", "false").lower() == "true" and
            not os.getenv("DISABLE_AUTH_BYPASS", "false").lower() == "true"
        )

        if development_bypass_enabled:
            logger.warning("DEVELOPMENT AUTH BYPASS ACTIVE - NOT FOR PRODUCTION USE")
            # Return a default test user for development (no auth required)
            if not credentials:  # No auth header at all - still allow in dev mode
                return User(
                    id="dev-user-001",
                    username="dev_user",
                    email="dev@toolboxai.com",
                    role="teacher",
                )
            # If there are credentials but they're just for testing, return dev user
            return User(
                id="dev-user-001",
                username="dev_user",
                email="dev@toolboxai.com",
                role="teacher",
            )
    except ImportError:
        # Feature flags not available - fail safe to no bypass
        logger.warning("Feature flags not available - disabling auth bypass")
        pass

    # Production mode or testing mode - credentials required
    if not credentials:
        raise AuthenticationError("Authorization header missing")

    try:
        payload = JWTManager.verify_token(credentials.credentials)
        if not isinstance(payload, dict):
            raise AuthenticationError("Invalid token payload")
        user_id = payload.get("sub")

        if not user_id:
            raise AuthenticationError("Invalid token payload")

        # In production, fetch user from database
        # For now, return a mock user
        user = User(
            id=user_id,
            username=payload.get("username", "unknown"),
            email=payload.get("email", "unknown@example.com"),
            role=payload.get("role", "student"),
        )

        return user

    except AuthenticationError:
        raise
    except (jwt.InvalidTokenError, ValueError, KeyError, AttributeError) as e:
        logger.error(f"Authentication error: {e}")
        raise AuthenticationError("Authentication failed")


def get_current_session(request: Request) -> Optional[Session]:
    """Get current session from request"""
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        return None

    return SessionManager.get_session(session_id)


def require_role(required_role: str):
    """Dependency to require specific user role"""

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role:
            raise AuthorizationError(f"Role '{required_role}' required")
        return current_user

    return role_checker


def require_any_role(allowed_roles: List[str]):
    """Dependency to require any of the specified roles"""

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise AuthorizationError(f"One of roles {allowed_roles} required")
        return current_user

    return role_checker


# Authentication utilities
async def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate user with username and password using real database"""

    # Try real database authentication first
    try:
        from .db_auth import db_auth

        # Authenticate using the database
        user_data = db_auth.authenticate_user(username, password)

        if user_data:
            # Convert database user to User model
            return User(
                id=str(user_data['id']),
                username=user_data['username'],
                email=user_data['email'],
                role=user_data['role'],
                grade_level=None,  # Can be fetched from DB if needed
                last_active=datetime.now(timezone.utc)
            )

    except ImportError:
        logger.warning("db_auth module not available, falling back to connection_manager")
        # Try using connection_manager as fallback
        try:
            import sys
            from pathlib import Path
            # Add parent directory to path for database import
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from apps.backend.core.database.connection_manager import db_manager

            # Initialize if not already done
            if not db_manager._initialized:
                db_manager.initialize()

            # Query the educational_platform database for the user
            with db_manager.get_session("education") as session:
                from sqlalchemy import text
                result = session.execute(
                    text("""
                        SELECT id, username, email, password_hash, role, created_at
                        FROM users
                        WHERE (username = :username OR email = :username) AND is_active = true
                        LIMIT 1
                    """),
                    {"username": username}
                )

                user_row = result.fetchone()

                if user_row:
                    # Verify password
                    stored_hash = user_row.password_hash
                    if verify_password(password, stored_hash):
                        # Return authenticated user
                        return User(
                            id=str(user_row.id),
                            username=user_row.username,
                            email=user_row.email,
                            role=user_row.role
                        )
        except Exception as inner_e:
            logger.error(f"Connection manager authentication error: {inner_e}")

    except Exception as e:
        logger.error(f"Database authentication error: {e}")
        # Fall through to test users if database fails

    # SECURE: Check development test credentials only if feature flag enabled
    try:
        from apps.backend.core.feature_flags import get_feature_flags, FeatureFlag
        feature_flags = get_feature_flags()

        if (feature_flags.is_enabled(FeatureFlag.DEVELOPMENT_AUTH_BYPASS) and
            settings.DEBUG and settings.ENVIRONMENT == "development"):

            # Use secure test data generator instead of hardcoded credentials
            from apps.backend.core.security.test_data_generator import get_development_credentials
            dev_credentials = get_development_credentials()

            # Check against generated development credentials
            for cred in dev_credentials:
                if (username == cred["username"] or username == cred["email"]):
                    # Verify password using the secure hash
                    if verify_password(password, cred["password_hash"]):
                        return User(
                            id=cred["id"],
                            username=cred["username"],
                            email=cred["email"],
                            role=cred["role"],
                        )

            # Also check demo credentials if configured (but only specific ones)
            if (settings.DEMO_USERNAME and settings.DEMO_PASSWORD and
                username == settings.DEMO_USERNAME and password == settings.DEMO_PASSWORD):
                return User(
                    id="demo-user-001",
                    username=settings.DEMO_USERNAME,
                    email="demo@toolboxai.com",
                    role="teacher",
                )
    except ImportError:
        logger.warning("Secure test data generator not available")
        pass

    # SECURE: Generate test users dynamically instead of hardcoded credentials
    # This prevents password leaks and makes credentials unpredictable
    try:
        from apps.backend.core.security.test_data_generator import get_testing_credentials

        # Only allow fallback test users in testing environment or if explicitly enabled
        testing_allowed = (
            os.getenv("TESTING", "false").lower() == "true" or
            os.getenv("ALLOW_TEST_FALLBACK", "false").lower() == "true"
        )

        if not testing_allowed:
            logger.info("Test fallback authentication disabled - use proper database authentication")
            return None

        test_credentials = get_testing_credentials()
        mock_users_data = test_credentials

    except ImportError:
        logger.warning("Secure test data generator not available for fallback authentication")
        return None

    # Create lookup dictionaries for username, email, and short username
    mock_users = {}
    for user in mock_users_data:
        # Add by full username
        mock_users[user["username"]] = user
        # Also add by email if different from username
        if user["email"] != user["username"]:
            mock_users[user["email"]] = user

        # Add short username versions (everything before @)
        if "@" in user["username"]:
            short_username = user["username"].split("@")[0]
            # Only add if it doesn't conflict with existing entries
            if short_username not in mock_users:
                mock_users[short_username] = user

    # Note: No hardcoded special cases - all users come from secure generator

    # Try to find user by username or email
    user_data = mock_users.get(username)
    if not user_data:
        return None

    if not verify_password(password, user_data["password_hash"]):
        return None

    return User(
        id=user_data["id"],
        username=user_data["username"],
        email=user_data["email"],
        role=user_data["role"]
    )


# Import from centralized location to avoid circular dependencies
from core.utils.password import hash_password, verify_password


def create_user_token(user: User) -> str:
    """Create JWT token for user"""
    token_data = {
        "sub": str(user.id),  # Convert UUID to string for JSON serialization
        "username": user.username,
        "email": user.email,
        "role": user.role.value if hasattr(user.role, 'value') else user.role,  # Handle enum
    }
    return JWTManager.create_access_token(token_data)


def check_permission(user: User, required_permission: str) -> bool:
    """Check if user has required permission

    Args:
        user: User object
        required_permission: Permission string (e.g., 'admin', 'teacher', 'student')

    Returns:
        bool: True if user has permission, False otherwise
    """
    # Define permission hierarchy
    permission_hierarchy = {
        "admin": ["admin", "teacher", "student"],
        "teacher": ["teacher", "student"],
        "student": ["student"]
    }

    # Get user's available permissions
    user_permissions = permission_hierarchy.get(user.role, [])

    # Check if required permission is in user's available permissions
    return required_permission in user_permissions


# Rate limiting decorator for use with FastAPI
def rate_limit(
    max_requests: int = None, window_seconds: int = DEFAULT_RATE_LIMIT_WINDOW
):
    """Rate limiting decorator for FastAPI endpoints"""

    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            client_ip = request.client.host
            user_agent = request.headers.get("User-Agent", "unknown")
            identifier = (
                f"{client_ip}:{hashlib.md5(user_agent.encode()).hexdigest()[:8]}"
            )

            # Use centralized rate limit manager
            manager = get_rate_limit_manager()
            allowed, retry_after = await manager.check_rate_limit(
                identifier=identifier,
                max_requests=max_requests or settings.RATE_LIMIT_PER_MINUTE,
                window_seconds=window_seconds,
                source="auth"
            )

            if not allowed:
                raise RateLimitError(
                    f"Rate limit exceeded. Maximum {max_requests or settings.RATE_LIMIT_PER_MINUTE} "
                    f"requests per {window_seconds} seconds."
                )

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


# Initialize auth system
def initialize_auth():
    """Initialize authentication system"""
    logger.info("Initializing authentication system")

    # Test Redis connection
    if redis_client:
        try:
            redis_client.ping()
            logger.info("Redis connection established for authentication")
        except (
            redis.ConnectionError,
            redis.TimeoutError,
            redis.RedisError,
            AttributeError,
        ) as e:
            logger.warning(f"Redis connection failed: {e}")

    # Validate JWT configuration
    if get_secure_jwt_secret() == "your-secret-key-change-in-production":
        logger.warning("Using default JWT secret key - change in production!")

    # Validate LMS credentials
    if settings.SCHOOLOGY_KEY and settings.SCHOOLOGY_SECRET:
        logger.info("Schoology credentials configured")
    else:
        logger.info("Schoology credentials not configured")

    if settings.CANVAS_TOKEN:
        logger.info("Canvas credentials configured")
    else:
        logger.info("Canvas credentials not configured")

    logger.info("Authentication system initialized")


# Export public functions and classes
# Module-level function for verify_token
def verify_token(token: str, raise_on_error: bool = True) -> Optional[Dict[str, Any]]:
    """Verify and decode JWT token (delegates to JWTManager)"""
    return JWTManager.verify_token(token, raise_on_error)


__all__ = [
    "JWTManager",
    "SessionManager",
    "RateLimiter",
    "LMSAuthenticator",
    "APIKeyManager",
    "AuthenticationError",
    "AuthorizationError",
    "RateLimitError",
    "authenticate_user",
    "check_permission",
    "get_current_user",
    "get_current_session",
    "require_role",
    "require_any_role",
    "hash_password",
    "verify_password",
    "verify_token",
    "create_user_token",
    "rate_limit",
    "initialize_auth",
]

# Initialize on import
initialize_auth()


def decode_token(token: str) -> dict:
    """Decode a JWT token"""
    try:
        # Simplified implementation for testing
        import json
        import base64

        # Basic JWT structure: header.payload.signature
        parts = token.split('.')
        if len(parts) != 3:
            return {"error": "Invalid token format"}

        # Decode payload (add padding if needed)
        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding

        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except Exception as e:
        return {"error": str(e)}

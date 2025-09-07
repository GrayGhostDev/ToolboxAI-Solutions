"""
Authentication and Authorization Module for ToolboxAI Roblox Environment

Provides JWT authentication, OAuth for LMS platforms, API key validation,
rate limiting, and user session management.
"""

import hashlib
import json
import logging
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

from .config import settings
from .models import Session, User

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
            to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )

        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.PyJWTError:
            raise AuthenticationError("Invalid token")


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
        session_data = session.dict()

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
    """Rate limiting functionality"""

    @staticmethod
    def check_rate_limit(
        identifier: str,
        window_seconds: int = DEFAULT_RATE_LIMIT_WINDOW,
        max_requests: int = None,
    ) -> bool:
        """Check if request is within rate limit"""
        if max_requests is None:
            max_requests = settings.RATE_LIMIT_PER_MINUTE

        current_time = int(time.time())
        window_start = current_time - window_seconds
        key = f"rate_limit:{identifier}:{window_start // window_seconds}"

        if redis_client:
            current_count = _safe_redis_int(redis_client.incr(key))
            if current_count == 1:
                redis_client.expire(key, window_seconds)
            return current_count <= max_requests
        else:
            # In-memory rate limiting (less accurate)
            if key not in memory_store:
                memory_store[key] = 0
            memory_store[key] += 1
            return memory_store[key] <= max_requests

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

                if not RateLimiter.check_rate_limit(
                    identifier, window_seconds, max_requests
                ):
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

        except (requests.RequestException, requests.Timeout, ValueError, KeyError) as e:
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
    # Development mode bypass for testing
    if settings.DEBUG and settings.ENVIRONMENT == "development":
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

    # Production mode - credentials required
    if not credentials:
        raise AuthenticationError("Authorization header missing")

    try:
        payload = JWTManager.verify_token(credentials.credentials)
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
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_user_token(user: User) -> str:
    """Create JWT token for user"""
    token_data = {
        "sub": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
    }
    return JWTManager.create_access_token(token_data)


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

            if not RateLimiter.check_rate_limit(
                identifier, window_seconds, max_requests
            ):
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
    if settings.JWT_SECRET_KEY == "your-secret-key-change-in-production":
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
__all__ = [
    "JWTManager",
    "SessionManager",
    "RateLimiter",
    "LMSAuthenticator",
    "APIKeyManager",
    "AuthenticationError",
    "AuthorizationError",
    "RateLimitError",
    "get_current_user",
    "get_current_session",
    "require_role",
    "require_any_role",
    "hash_password",
    "verify_password",
    "create_user_token",
    "rate_limit",
    "initialize_auth",
]

# Initialize on import
initialize_auth()

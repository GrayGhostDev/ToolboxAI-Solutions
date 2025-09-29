"""
Secure Authentication Implementation for ToolboxAI
Fixes all JWT and authentication vulnerabilities
"""

import os
import jwt
import bcrypt
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, Security, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, field_validator
import redis
from functools import wraps
import time
import hashlib
import hmac

from apps.backend.core.config import settings

# Security configuration from environment - NEVER hardcode secrets
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY or len(SECRET_KEY) < 32 or SECRET_KEY == "your-secret-key-change-in-production":
    # Generate secure key if not provided or if default key is used
    SECRET_KEY = secrets.token_hex(32)
    print(f"WARNING: Generated new secret key. Set JWT_SECRET_KEY environment variable to: {SECRET_KEY}")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 900  # 15 minutes

# Redis for token blacklist and rate limiting
try:
    redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    redis_client.ping()
except Exception:
    redis_client = None

# Security scheme
security = HTTPBearer()

class TokenData(BaseModel):
    """Token payload with validation"""
    sub: str  # User ID
    role: str
    exp: datetime
    iat: datetime
    jti: str  # JWT ID for revocation
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        allowed_roles = ['admin', 'teacher', 'student', 'parent', 'developer']
        if v not in allowed_roles:
            raise ValueError(f"Invalid role: {v}")
        return v

class SecureAuth:
    """Secure authentication handler"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password with bcrypt"""
        # Validate password strength
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        
        if not any(c.isupper() for c in password):
            raise ValueError("Password must contain uppercase letter")
        
        if not any(c.islower() for c in password):
            raise ValueError("Password must contain lowercase letter")
        
        if not any(c.isdigit() for c in password):
            raise ValueError("Password must contain number")
        
        # Hash with bcrypt
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception:
            return False
    
    @staticmethod
    def create_access_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token with security features"""
        to_encode = data.copy()
        
        # Set expiration
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        # Add security claims
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": secrets.token_hex(16),  # Unique token ID
            "type": "access"
        })
        
        # Encode token
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """Create refresh token"""
        expire = datetime.now(timezone.utc) + timedelta(
            days=REFRESH_TOKEN_EXPIRE_DAYS
        )
        
        to_encode = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": secrets.token_hex(16),
            "type": "refresh"
        }
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        # Store in Redis with expiry if available
        if redis_client:
            redis_client.setex(
                f"refresh_token:{user_id}",
                timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
                encoded_jwt
            )
        
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            # Decode token
            payload = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[ALGORITHM],
                options={"verify_exp": True}
            )
            
            # Verify token type
            if payload.get("type") != token_type:
                raise jwt.InvalidTokenError("Invalid token type")
            
            # Check if token is blacklisted
            if redis_client and redis_client.get(f"blacklist:{payload.get('jti')}"):
                raise jwt.InvalidTokenError("Token has been revoked")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
    
    @staticmethod
    def revoke_token(token: str):
        """Revoke a token by adding to blacklist"""
        try:
            payload = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[ALGORITHM],
                options={"verify_exp": False}
            )
            
            jti = payload.get("jti")
            exp = payload.get("exp")
            
            if jti and exp and redis_client:
                # Calculate TTL until token expiry
                ttl = exp - datetime.now(timezone.utc).timestamp()
                if ttl > 0:
                    redis_client.setex(
                        f"blacklist:{jti}",
                        int(ttl),
                        "revoked"
                    )
                    
        except Exception:
            pass  # Token already invalid
    
    @staticmethod
    def check_login_attempts(username: str) -> bool:
        """Check if user is locked out due to failed attempts"""
        if not redis_client:
            return True
            
        attempts_key = f"login_attempts:{username}"
        lockout_key = f"lockout:{username}"
        
        # Check if locked out
        if redis_client.get(lockout_key):
            return False
        
        # Get attempt count
        attempts = redis_client.get(attempts_key)
        if attempts and int(attempts) >= MAX_LOGIN_ATTEMPTS:
            # Lock out user
            redis_client.setex(lockout_key, LOCKOUT_DURATION, "locked")
            redis_client.delete(attempts_key)
            return False
        
        return True
    
    @staticmethod
    def record_failed_login(username: str):
        """Record failed login attempt"""
        if not redis_client:
            return
            
        attempts_key = f"login_attempts:{username}"
        
        # Increment attempts
        attempts = redis_client.incr(attempts_key)
        
        # Set expiry if first attempt
        if attempts == 1:
            redis_client.expire(attempts_key, 900)  # 15 minutes
    
    @staticmethod
    def clear_login_attempts(username: str):
        """Clear login attempts on successful login"""
        if not redis_client:
            return
            
        redis_client.delete(f"login_attempts:{username}")
        redis_client.delete(f"lockout:{username}")

# Dependency for protected routes
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Dict[str, Any]:
    """Get current user from JWT token"""
    token = credentials.credentials
    
    # Verify token
    payload = SecureAuth.verify_token(token)
    
    # Return user data
    return {
        "id": payload.get("sub"),
        "role": payload.get("role"),
        "token_id": payload.get("jti")
    }

# Role-based access control decorator
def require_role(allowed_roles: list):
    """Decorator for role-based access control"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from kwargs
            current_user = kwargs.get("current_user")
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if current_user.get("role") not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{current_user.get('role')}' not authorized"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

# Rate limiting
class RateLimiter:
    """Rate limiter using Redis"""
    
    @staticmethod
    def check_rate_limit(
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> bool:
        """Check if rate limit exceeded"""
        if not redis_client:
            return True  # Allow if Redis not available
            
        current = redis_client.incr(key)
        
        if current == 1:
            redis_client.expire(key, window_seconds)
        
        return current <= max_requests
    
    @staticmethod
    def rate_limit_decorator(max_requests: int = 100, window: int = 60):
        """Decorator for rate limiting"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Get user ID or IP for rate limiting
                request = kwargs.get("request")
                if request:
                    key = f"rate_limit:{request.client.host}"
                    
                    if not RateLimiter.check_rate_limit(key, max_requests, window):
                        raise HTTPException(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail="Rate limit exceeded"
                        )
                
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator

# CSRF Protection
class CSRFProtection:
    """CSRF token management"""
    
    @staticmethod
    def generate_csrf_token(session_id: str) -> str:
        """Generate CSRF token"""
        message = f"{session_id}:{time.time()}"
        signature = hmac.new(
            SECRET_KEY.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"{message}:{signature}"
    
    @staticmethod
    def verify_csrf_token(token: str, session_id: str) -> bool:
        """Verify CSRF token"""
        try:
            message, signature = token.rsplit(":", 1)
            expected_signature = hmac.new(
                SECRET_KEY.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Verify signature
            if not hmac.compare_digest(signature, expected_signature):
                return False
            
            # Verify session
            token_session = message.split(":")[0]
            if token_session != session_id:
                return False
            
            # Check token age (1 hour)
            token_time = float(message.split(":")[1])
            if time.time() - token_time > 3600:
                return False
            
            return True
            
        except Exception:
            return False

# Export secure authentication components
auth = SecureAuth()
rate_limiter = RateLimiter()
csrf_protection = CSRFProtection()
"""
Simple Ghost framework replacements to get server running
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt
from pydantic import BaseModel


class APIResponse(BaseModel):
    """Standard API response format"""

    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str = None

    def __init__(self, **kwargs):
        if "timestamp" not in kwargs:
            kwargs["timestamp"] = datetime.now(timezone.utc).isoformat()
        super().__init__(**kwargs)

    @classmethod
    def success(cls, data=None, message="Success"):
        """Create a success response"""
        return cls(success=True, message=message, data=data)

    @classmethod
    def error(cls, message="Error", error=None):
        """Create an error response"""
        return cls(success=False, message=message, error=error)


class AuthManager:
    """Simple auth manager for JWT token verification"""

    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """Verify JWT token and return user data"""
        try:
            # Get secret from environment
            secret = os.getenv("JWT_SECRET_KEY", "your-secret-key")
            algorithm = os.getenv("JWT_ALGORITHM", "HS256")

            # Decode token
            payload = jwt.decode(token, secret, algorithms=[algorithm])
            return payload
        except jwt.InvalidTokenError:
            return None

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=1440
            )  # 24 hours default

        # JWT 'exp' should be a numeric timestamp
        to_encode.update({"exp": int(expire.timestamp())})
        secret = os.getenv("JWT_SECRET_KEY", "your-secret-key")
        algorithm = os.getenv("JWT_ALGORITHM", "HS256")

        encoded_jwt = jwt.encode(to_encode, secret, algorithm=algorithm)
        return encoded_jwt

"""
Simple Ghost framework replacements to get server running
"""

import os
from datetime import datetime, timedelta
from typing import Optional

import jwt
from pydantic import BaseModel


class APIResponse(BaseModel):
    """Standard API response format

    This is intentionally lightweight. Use `object` for `data` to avoid
    analyzer configurations that struggle to resolve `typing.Any`.
    """

    success: bool
    message: str
    data: Optional[object] = None
    error: Optional[str] = None
    timestamp: Optional[str] = None

    def __init__(self, **kwargs):
        if "timestamp" not in kwargs:
            kwargs["timestamp"] = datetime.now().isoformat()
        super().__init__(**kwargs)

    @classmethod
    def create_success(cls, data: Optional[object] = None, message: str = "Success"):
        """Create a success response"""
        return cls(success=True, message=message, data=data)

    @classmethod
    def create_error(cls, message: str = "Error", error: Optional[str] = None):
        """Create an error response"""
        return cls(success=False, message=message, error=error)

    # Backwards-compatible aliases used across the codebase
    @classmethod
    def ok(cls, message: str = "Success", data: Optional[object] = None):
        """Create a success response"""
        return cls.create_success(data=data, message=message)

    @classmethod
    def fail(cls, message: str = "Error", error: Optional[str] = None):
        """Create an error response"""
        return cls.create_error(message=message, error=error)


class AuthManager:  # Simple auth manager using JWT tokens
    """Simple auth helper for JWT tokens"""

    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """Verify and decode JWT token"""
        try:
            secret = os.getenv("JWT_SECRET_KEY", "your-secret-key")
            algorithm = os.getenv("JWT_ALGORITHM", "HS256")
            payload = jwt.decode(token, secret, algorithms=[algorithm])
            return payload
        except jwt.InvalidTokenError:
            return None

    @staticmethod
    def create_access_token(
        data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        expire = datetime.now() + (expires_delta or timedelta(minutes=1440))
        to_encode.update({"exp": expire})
        secret = os.getenv("JWT_SECRET_KEY", "your-secret-key")
        algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        return jwt.encode(to_encode, secret, algorithm=algorithm)

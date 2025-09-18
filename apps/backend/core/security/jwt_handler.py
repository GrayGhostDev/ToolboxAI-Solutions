"""
JWT Token Handler for ToolboxAI

Provides JWT token creation, validation, and authentication dependencies
for FastAPI applications with proper security practices.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "development-secret-key-change-in-production-32-chars-minimum")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Security scheme
security = HTTPBearer()

class TokenData(BaseModel):
    """Token payload data model"""
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None
    exp: Optional[datetime] = None

class Token(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    role: Optional[str] = None

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token

    Args:
        data: Payload data to encode in token
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    # Set expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    # Encode the token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> TokenData:
    """
    Verify and decode a JWT token

    Args:
        token: JWT token string

    Returns:
        TokenData object with decoded payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Extract data
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        role: str = payload.get("role")
        exp_timestamp: float = payload.get("exp")

        # Convert expiration timestamp to datetime
        exp = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc) if exp_timestamp else None

        # Validate required fields
        if username is None:
            raise credentials_exception

        return TokenData(
            username=username,
            user_id=user_id,
            role=role,
            exp=exp
        )

    except JWTError:
        raise credentials_exception

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    FastAPI dependency to get current authenticated user

    Args:
        credentials: HTTP bearer token credentials

    Returns:
        TokenData with current user information

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    return verify_token(token)

def require_role(required_role: str):
    """
    Create a dependency that requires a specific user role

    Args:
        required_role: The role required to access the endpoint

    Returns:
        FastAPI dependency function
    """
    async def role_checker(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required_role}"
            )
        return current_user

    return role_checker

def require_roles(*required_roles: str):
    """
    Create a dependency that requires one of multiple roles

    Args:
        required_roles: List of acceptable roles

    Returns:
        FastAPI dependency function
    """
    async def roles_checker(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        if current_user.role not in required_roles:
            roles_str = ", ".join(required_roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {roles_str}"
            )
        return current_user

    return roles_checker

# Export commonly used dependencies
get_admin_user = require_role("admin")
get_teacher_user = require_roles("teacher", "admin")
get_student_user = require_roles("student", "teacher", "admin")

__all__ = [
    "Token",
    "TokenData",
    "create_access_token",
    "verify_token",
    "get_current_user",
    "require_role",
    "require_roles",
    "get_admin_user",
    "get_teacher_user",
    "get_student_user"
]

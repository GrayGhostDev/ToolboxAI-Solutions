"""
Core Dependencies Module

Provides common dependencies for FastAPI endpoints.
"""

from typing import Optional, AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
import jwt
from datetime import datetime, timedelta

from database.database_service import DatabaseService
from database.models import User
from toolboxai_settings import settings

# Security scheme
security = HTTPBearer()

# Database service instance
db_service = DatabaseService()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session.

    Yields:
        AsyncSession: Database session
    """
    try:
        async with db_service.async_session() as session:
            yield session
    except Exception as e:
        # If database is not available, return None
        yield None


def get_db() -> Session:
    """
    Get database session for sync operations.

    Returns:
        Session: Database session or None if not available
    """
    try:
        db = db_service.SessionLocal()
        return db
    except Exception:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Optional[AsyncSession] = Depends(get_async_db)
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP authorization credentials
        db: Database session

    Returns:
        User: Current authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials

    try:
        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # For testing/development, return a mock user if DB is not available
        if db is None:
            return User(
                id=int(user_id) if user_id.isdigit() else 1,
                email=payload.get("email", "test@example.com"),
                username=payload.get("username", "test_user"),
                role=payload.get("role", "student"),
                is_active=True
            )

        # Get user from database
        user = await db.get(User, int(user_id))
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled"
            )

        return user

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user.

    Args:
        current_user: Current authenticated user

    Returns:
        User: Active user

    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    return current_user


def require_role(allowed_roles: list[str]):
    """
    Dependency to require specific user roles.

    Args:
        allowed_roles: List of allowed roles

    Returns:
        Dependency function that checks user role
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' not authorized for this action"
            )
        return current_user

    return role_checker


# Common role dependencies
require_admin = require_role(["admin"])
require_teacher = require_role(["admin", "teacher"])
require_teacher_or_student = require_role(["admin", "teacher", "student"])
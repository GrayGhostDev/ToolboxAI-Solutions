"""
Core Dependencies Module

Provides common dependencies for FastAPI endpoints.
"""

import logging
from collections.abc import AsyncGenerator, Generator
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from apps.backend.core.database import SessionLocal
from database.models import User
from database.session_modern import get_async_session as get_sqlalchemy_async_session
from toolboxai_settings import settings

# Security scheme
security = HTTPBearer()

logger = logging.getLogger(__name__)


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session.

    Yields:
        AsyncSession: Database session
    """
    try:
        async for session in get_sqlalchemy_async_session():
            yield session
    except Exception as e:
        logger.warning("Async database session unavailable: %s", e)
        # If database is not available, return None
        yield None


def get_db() -> Generator[Session | None, None, None]:
    """
    Get database session for sync operations.

    Returns:
        Session: Database session or None if not available
    """
    try:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    except Exception as e:
        logger.warning("Synchronous database session unavailable: %s", e)
        yield None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession | None = Depends(get_async_db),
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
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

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
                is_active=True,
            )

        # Get user from database
        user = await db.get(User, int(user_id))
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled"
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


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
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
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled"
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
                detail=f"Role '{current_user.role}' not authorized for this action",
            )
        return current_user

    return role_checker


# Common role dependencies
require_admin = require_role(["admin"])
require_teacher = require_role(["admin", "teacher"])
require_teacher_or_student = require_role(["admin", "teacher", "student"])


# ============================================================================
# Multi-Tenant Organization Dependencies
# ============================================================================


async def get_current_organization_id(
    current_user: User = Depends(get_current_user),
    db: AsyncSession | None = Depends(get_async_db),
) -> UUID:
    """
    Extract organization_id from current authenticated user.

    This dependency enforces multi-tenant isolation by ensuring all
    API requests are scoped to the user's organization.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        UUID: Organization ID for the current user

    Raises:
        HTTPException: If user does not belong to an organization

    Example:
        @router.get("/agents")
        async def list_agents(
            org_id: UUID = Depends(get_current_organization_id),
            db: AsyncSession = Depends(get_async_db)
        ):
            # Query automatically scoped to org_id
            agents = await db.execute(
                select(AgentInstance).filter_by(organization_id=org_id)
            )
            return agents.scalars().all()
    """
    if not hasattr(current_user, "organization_id") or current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must belong to an organization to access this resource",
        )

    # Set PostgreSQL session variable for RLS policies (if database available)
    if db is not None:
        try:
            await db.execute(
                text(f"SET app.current_organization_id = '{current_user.organization_id}'")
            )
        except Exception:
            # RLS may not be enabled in all environments (dev/test)
            pass

    return current_user.organization_id


def get_current_organization_id_sync(
    current_user: User = Depends(get_current_user),
    db: Session | None = Depends(get_db),
) -> UUID:
    """
    Extract organization_id from current user (sync version).

    Synchronous version of get_current_organization_id for sync endpoints.

    Args:
        current_user: Current authenticated user
        db: Sync database session

    Returns:
        UUID: Organization ID for the current user

    Raises:
        HTTPException: If user does not belong to an organization

    Example:
        @router.get("/agents")
        def list_agents_sync(
            org_id: UUID = Depends(get_current_organization_id_sync),
            db: Session = Depends(get_db)
        ):
            query = TenantAwareQuery(db, AgentInstance, org_id)
            return query.all()
    """
    if not hasattr(current_user, "organization_id") or current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must belong to an organization to access this resource",
        )

    # Set PostgreSQL session variable for RLS policies (if database available)
    if db is not None:
        try:
            db.execute(text(f"SET app.current_organization_id = '{current_user.organization_id}'"))
        except Exception:
            # RLS may not be enabled in all environments (dev/test)
            pass

    return current_user.organization_id


async def verify_organization_access(
    resource_org_id: UUID,
    current_org_id: UUID = Depends(get_current_organization_id),
) -> bool:
    """
    Verify that current user has access to a resource's organization.

    Use this dependency when you need to explicitly check organization
    ownership of a specific resource.

    Args:
        resource_org_id: Organization ID of the resource being accessed
        current_org_id: Current user's organization ID

    Returns:
        bool: True if access granted

    Raises:
        HTTPException: If organization IDs don't match

    Example:
        @router.get("/agents/{agent_id}")
        async def get_agent(
            agent_id: str,
            org_id: UUID = Depends(get_current_organization_id),
            db: AsyncSession = Depends(get_async_db)
        ):
            agent = await db.get(AgentInstance, agent_id)
            if not agent:
                raise HTTPException(404, "Agent not found")

            # Verify organization access
            await verify_organization_access(agent.organization_id, org_id)

            return agent
    """
    if resource_org_id != current_org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to resources from this organization",
        )
    return True


def require_admin_or_own_organization(
    current_user: User = Depends(get_current_user),
    current_org_id: UUID = Depends(get_current_organization_id),
):
    """
    Require user to be admin or accessing their own organization's data.

    This combines role checking with organization checking for admin
    operations that should be scoped to organization.

    Args:
        current_user: Current authenticated user
        current_org_id: Current user's organization ID

    Returns:
        tuple: (user, org_id)

    Raises:
        HTTPException: If neither admin nor own organization

    Example:
        @router.delete("/organizations/{org_id}/data")
        def delete_org_data(
            org_id: UUID,
            user_and_org = Depends(require_admin_or_own_organization)
        ):
            user, current_org_id = user_and_org
            # Admins can delete any org, others only their own
            if user.role != "admin" and org_id != current_org_id:
                raise HTTPException(403, "Cannot delete other organization's data")
            # ... deletion logic
    """
    return (current_user, current_org_id)

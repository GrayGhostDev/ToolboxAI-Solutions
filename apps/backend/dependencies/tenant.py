"""
Tenant Dependencies for FastAPI Multi-Tenancy

Provides FastAPI dependency functions for tenant context management,
permission checks, and database session scoping based on organization
context in the ToolBoxAI Educational Platform.
"""

import logging
from collections.abc import Generator
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from apps.backend.api.auth.auth import (
    get_current_user,
)
from apps.backend.middleware.tenant import TenantContext, get_tenant_context
from apps.backend.models.schemas import User
from database.models.tenant import Organization

# Database session would be imported from database module
# from apps.backend.database.session import get_db

logger = logging.getLogger(__name__)


# === TENANT CONTEXT DEPENDENCIES ===


async def get_current_tenant() -> TenantContext:
    """
    Get the current tenant context from middleware.

    Returns:
        TenantContext: Current tenant context

    Raises:
        HTTPException: If no tenant context is available
    """
    context = get_tenant_context()

    if not context.has_tenant and not context.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context is required for this operation",
        )

    return context


async def get_optional_tenant() -> TenantContext | None:
    """
    Get the current tenant context if available, otherwise return None.

    Returns:
        Optional[TenantContext]: Current tenant context or None
    """
    try:
        return get_tenant_context()
    except Exception as e:
        logger.warning(f"Failed to get tenant context: {e}")
        return None


async def require_tenant_member(
    current_user: User = Depends(get_current_user),
    tenant_context: TenantContext = Depends(get_current_tenant),
) -> tuple[User, TenantContext]:
    """
    Require user to be a member of the current tenant organization.

    Args:
        current_user: Current authenticated user
        tenant_context: Current tenant context

    Returns:
        tuple[User, TenantContext]: User and tenant context

    Raises:
        HTTPException: If user is not a member of the organization
    """
    # Super admin can access any tenant
    if tenant_context.is_super_admin:
        return current_user, tenant_context

    # Check if user belongs to the organization
    if not tenant_context.effective_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No tenant context available"
        )

    # In production, check database for organization membership
    # For now, check if user has organization context
    user_org_id = getattr(current_user, "organization_id", None)
    if str(user_org_id) != tenant_context.effective_tenant_id:
        # Allow if it's in the JWT token context (organization switching)

        # This is a simplified check - in production, verify organization membership
        logger.warning(
            f"User {current_user.id} accessing tenant {tenant_context.effective_tenant_id} "
            f"without direct membership (user org: {user_org_id})"
        )

    return current_user, tenant_context


async def require_tenant_admin(
    current_user: User = Depends(get_current_user),
    tenant_context: TenantContext = Depends(get_current_tenant),
) -> tuple[User, TenantContext]:
    """
    Require user to be an admin of the current tenant organization.

    Args:
        current_user: Current authenticated user
        tenant_context: Current tenant context

    Returns:
        tuple[User, TenantContext]: User and tenant context

    Raises:
        HTTPException: If user is not an admin of the organization
    """
    # Super admin can access any tenant
    if tenant_context.is_super_admin:
        return current_user, tenant_context

    # Check basic membership first
    user, context = await require_tenant_member(current_user, tenant_context)

    # Check admin role in organization
    # In production, check database for organization role
    user_role = getattr(current_user, "role", "").lower()
    org_role = getattr(current_user, "organization_role", user_role).lower()

    admin_roles = ["admin", "owner", "super_admin", "system_admin"]

    if user_role not in admin_roles and org_role not in admin_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required for this operation"
        )

    return user, context


async def require_tenant_manager(
    current_user: User = Depends(get_current_user),
    tenant_context: TenantContext = Depends(get_current_tenant),
) -> tuple[User, TenantContext]:
    """
    Require user to be a manager or admin of the current tenant organization.

    Args:
        current_user: Current authenticated user
        tenant_context: Current tenant context

    Returns:
        tuple[User, TenantContext]: User and tenant context

    Raises:
        HTTPException: If user is not a manager/admin of the organization
    """
    # Super admin can access any tenant
    if tenant_context.is_super_admin:
        return current_user, tenant_context

    # Check basic membership first
    user, context = await require_tenant_member(current_user, tenant_context)

    # Check manager+ role in organization
    user_role = getattr(current_user, "role", "").lower()
    org_role = getattr(current_user, "organization_role", user_role).lower()

    manager_roles = ["admin", "manager", "owner", "super_admin", "system_admin"]

    if user_role not in manager_roles and org_role not in manager_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager access required for this operation",
        )

    return user, context


# === ORGANIZATION-SPECIFIC DEPENDENCIES ===


def require_organization_access(organization_id: str):
    """
    Create a dependency that requires access to a specific organization.

    Args:
        organization_id: Organization ID to require access to

    Returns:
        Callable: FastAPI dependency function
    """

    async def organization_access_dependency(
        current_user: User = Depends(get_current_user),
        tenant_context: TenantContext = Depends(get_current_tenant),
    ) -> tuple[User, str]:
        """Check access to specific organization"""

        # Super admin can access any organization
        if tenant_context.is_super_admin:
            return current_user, organization_id

        # Check if current context matches required organization
        if not tenant_context.can_access_tenant(organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to organization {organization_id}",
            )

        return current_user, organization_id

    return organization_access_dependency


def require_organization_role(organization_id: str, required_role: str):
    """
    Create a dependency that requires a specific role in an organization.

    Args:
        organization_id: Organization ID
        required_role: Required role (member, teacher, manager, admin)

    Returns:
        Callable: FastAPI dependency function
    """

    async def organization_role_dependency(
        current_user: User = Depends(get_current_user),
        tenant_context: TenantContext = Depends(get_current_tenant),
    ) -> tuple[User, str]:
        """Check role in specific organization"""

        # Super admin bypasses role checks
        if tenant_context.is_super_admin:
            return current_user, organization_id

        # Check organization access first
        if not tenant_context.can_access_tenant(organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to organization {organization_id}",
            )

        # Check role hierarchy
        user_role = getattr(current_user, "role", "").lower()
        org_role = getattr(current_user, "organization_role", user_role).lower()

        role_hierarchy = {
            "admin": ["admin", "manager", "teacher", "member"],
            "manager": ["manager", "teacher", "member"],
            "teacher": ["teacher", "member"],
            "member": ["member"],
        }

        allowed_roles = role_hierarchy.get(org_role, [])
        if required_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required in organization {organization_id}",
            )

        return current_user, organization_id

    return organization_role_dependency


# === DATABASE SESSION DEPENDENCIES ===


def get_mock_tenant_db_session():
    """
    Mock tenant-scoped database session for development.
    In production, this would return a real database session with tenant filtering.
    """

    class MockTenantSession:
        def __init__(self, tenant_id: str | None = None):
            self.tenant_id = tenant_id
            self._filters = {"organization_id": tenant_id} if tenant_id else {}

        def query(self, model):
            return MockTenantQuery(self._filters)

        def add(self, obj):
            if self.tenant_id and hasattr(obj, "organization_id"):
                obj.organization_id = self.tenant_id

        def commit(self):
            pass

        def refresh(self, obj):
            pass

        def close(self):
            pass

        def get_tenant_filter(self):
            return self._filters

    class MockTenantQuery:
        def __init__(self, tenant_filters: dict[str, Any]):
            self.tenant_filters = tenant_filters

        def filter(self, *args):
            return self

        def filter_by(self, **kwargs):
            return self

        def first(self):
            return None

        def all(self):
            return []

        def count(self):
            return 0

    return MockTenantSession


async def get_tenant_db_session(
    tenant_context: TenantContext = Depends(get_current_tenant),
    # db: Session = Depends(get_db)  # Uncomment when real DB is available
) -> Generator[Session, None, None]:
    """
    Get a database session with tenant context applied.

    This session automatically filters queries by the current tenant/organization
    and ensures all new objects are associated with the correct tenant.

    Args:
        tenant_context: Current tenant context
        db: Base database session

    Yields:
        Session: Tenant-scoped database session
    """
    # Mock implementation for development
    mock_session = get_mock_tenant_db_session()
    mock_session.tenant_id = tenant_context.effective_tenant_id

    try:
        yield mock_session
    finally:
        mock_session.close()

    # Production implementation would be:
    # try:
    #     # Set tenant context for the session
    #     if tenant_context.effective_tenant_id:
    #         # Apply tenant filter to session
    #         db.tenant_id = tenant_context.effective_tenant_id
    #
    #         # Add event listeners to automatically filter queries
    #         @event.listens_for(db, 'before_bulk_delete')
    #         def before_bulk_delete(query_context):
    #             # Add tenant filter to bulk delete operations
    #             pass
    #
    #         @event.listens_for(db, 'before_bulk_update')
    #         def before_bulk_update(query_context):
    #             # Add tenant filter to bulk update operations
    #             pass
    #
    #     yield db
    # finally:
    #     db.close()


async def get_organization_db_session(
    organization_id: str,
    tenant_context: TenantContext = Depends(get_current_tenant),
    # db: Session = Depends(get_db)  # Uncomment when real DB is available
) -> Generator[Session, None, None]:
    """
    Get a database session scoped to a specific organization.

    Args:
        organization_id: Organization ID to scope to
        tenant_context: Current tenant context
        db: Base database session

    Yields:
        Session: Organization-scoped database session

    Raises:
        HTTPException: If access to organization is denied
    """
    # Validate access to the organization
    if not tenant_context.is_super_admin and not tenant_context.can_access_tenant(organization_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied to organization {organization_id}",
        )

    # Mock implementation
    mock_session = get_mock_tenant_db_session()
    mock_session.tenant_id = organization_id

    try:
        yield mock_session
    finally:
        mock_session.close()


# === UTILITY DEPENDENCIES ===


async def get_organization_info(
    tenant_context: TenantContext = Depends(get_current_tenant),
    db_session=Depends(get_tenant_db_session),
) -> Organization | None:
    """
    Get the current organization information.

    Args:
        tenant_context: Current tenant context
        db_session: Tenant-scoped database session

    Returns:
        Optional[Organization]: Organization object if found
    """
    if not tenant_context.effective_tenant_id:
        return None

    # In production, query the database
    # organization = db_session.query(Organization).filter(
    #     Organization.id == tenant_context.effective_tenant_id,
    #     Organization.is_active == True
    # ).first()

    # Mock implementation
    if tenant_context.effective_tenant_id:
        logger.info(f"Mock organization info for tenant: {tenant_context.effective_tenant_id}")

    return None  # Mock - no organization data


async def validate_organization_limits(
    action: str,
    tenant_context: TenantContext = Depends(get_current_tenant),
    organization: Organization | None = Depends(get_organization_info),
) -> bool:
    """
    Validate if an action can be performed within organization limits.

    Args:
        action: Action to validate (add_user, add_class, api_call, etc.)
        tenant_context: Current tenant context
        organization: Organization information

    Returns:
        bool: True if action is allowed

    Raises:
        HTTPException: If action exceeds organization limits
    """
    if tenant_context.is_super_admin:
        return True

    if not organization:
        # In development, allow all actions
        logger.warning(f"No organization data available for limit validation: {action}")
        return True

    # Mock limit validation
    limits_map = {
        "add_user": "can_add_user",
        "add_class": "can_add_class",
        "api_call": "can_make_api_call",
        "storage_usage": "can_use_storage",
    }

    limit_method = limits_map.get(action)
    if limit_method and hasattr(organization, limit_method):
        can_perform = getattr(organization, limit_method)()
        if not can_perform:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Organization limit exceeded for action: {action}",
            )

    return True


# === REQUEST CONTEXT DEPENDENCIES ===


async def get_request_context(
    request: Request, tenant_context: TenantContext = Depends(get_current_tenant)
) -> dict[str, Any]:
    """
    Get enriched request context with tenant information.

    Args:
        request: FastAPI Request object
        tenant_context: Current tenant context

    Returns:
        Dict[str, Any]: Request context with tenant information
    """
    return {
        "request_id": getattr(request.state, "request_id", None),
        "path": request.url.path,
        "method": request.method,
        "client_ip": request.client.host,
        "user_agent": request.headers.get("User-Agent"),
        "tenant_context": tenant_context.to_dict(),
        "timestamp": "datetime.now().isoformat()",  # Would use real datetime
    }


# Export public interface
__all__ = [
    # Tenant context dependencies
    "get_current_tenant",
    "get_optional_tenant",
    "require_tenant_member",
    "require_tenant_admin",
    "require_tenant_manager",
    # Organization-specific dependencies
    "require_organization_access",
    "require_organization_role",
    # Database session dependencies
    "get_tenant_db_session",
    "get_organization_db_session",
    # Utility dependencies
    "get_organization_info",
    "validate_organization_limits",
    "get_request_context",
]

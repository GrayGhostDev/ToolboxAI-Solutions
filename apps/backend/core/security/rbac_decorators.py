"""
RBAC Decorators for FastAPI Endpoints

Provides convenient decorators for enforcing role-based access control
on API endpoints with fine-grained permission checking.

Usage:
    from apps.backend.core.security.rbac_decorators import (
        require_role,
        require_permission,
        require_resource_access
    )

    @router.post("/content")
    @require_permission("content:create:organization")
    async def create_content(
        user: User = Depends(get_current_user)
    ):
        # Only users with content:create:organization permission can access
        pass

    @router.delete("/content/{content_id}")
    @require_resource_access("content", "delete")
    async def delete_content(
        content_id: int,
        user: User = Depends(get_current_user)
    ):
        # Checks ownership and permissions automatically
        pass
"""

import logging
from functools import wraps
from typing import List, Callable, Optional, Any
from fastapi import HTTPException, status, Depends

from database.models import User
from apps.backend.core.deps import get_current_user
from apps.backend.core.security.rbac_manager import rbac_manager


logger = logging.getLogger(__name__)


def require_role(allowed_roles: List[str]):
    """
    Decorator to require specific role(s) for endpoint access.

    Uses role hierarchy - if user has higher role, access is granted.

    Args:
        allowed_roles: List of role names that can access endpoint

    Example:
        @router.get("/admin/dashboard")
        @require_role(["admin"])
        async def admin_dashboard(user: User = Depends(get_current_user)):
            pass

    Raises:
        HTTPException 403: If user doesn't have required role
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs
            user = kwargs.get('user') or kwargs.get('current_user')

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            # Check if user has any of the allowed roles
            has_access = False
            for role in allowed_roles:
                if rbac_manager.has_role(user, role):
                    has_access = True
                    break

            if not has_access:
                logger.warning(
                    f"Access denied for user {user.id} with role {user.role}. "
                    f"Required roles: {allowed_roles}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required role: {', '.join(allowed_roles)}"
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator


def require_permission(permission: str):
    """
    Decorator to require specific permission for endpoint access.

    Permission format: "resource:action[:scope]"
    Examples:
        - "content:create:organization"
        - "agent:execute:own"
        - "user:delete:all"

    Args:
        permission: Permission string required for access

    Example:
        @router.post("/content")
        @require_permission("content:create:organization")
        async def create_content(user: User = Depends(get_current_user)):
            pass

    Raises:
        HTTPException 403: If user doesn't have required permission
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs
            user = kwargs.get('user') or kwargs.get('current_user')

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            # Check permission
            if not rbac_manager.has_permission(user, permission):
                logger.warning(
                    f"Permission denied for user {user.id} ({user.role}). "
                    f"Required: {permission}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required: {permission}"
                )

            logger.debug(f"Permission granted: {permission} for user {user.id}")
            return await func(*args, **kwargs)

        return wrapper
    return decorator


def require_permissions(permissions: List[str], require_all: bool = True):
    """
    Decorator to require multiple permissions for endpoint access.

    Args:
        permissions: List of permission strings
        require_all: If True, user must have ALL permissions.
                    If False, user needs ANY one permission.

    Example:
        @router.put("/content/{content_id}")
        @require_permissions(["content:update:organization", "content:update:all"], require_all=False)
        async def update_content(user: User = Depends(get_current_user)):
            pass

    Raises:
        HTTPException 403: If user doesn't have required permissions
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get('user') or kwargs.get('current_user')

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            if require_all:
                # User must have ALL permissions
                for perm in permissions:
                    if not rbac_manager.has_permission(user, perm):
                        logger.warning(
                            f"Permission denied for user {user.id}. "
                            f"Missing: {perm}"
                        )
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Insufficient permissions. Missing: {perm}"
                        )
            else:
                # User needs ANY one permission
                has_any = any(
                    rbac_manager.has_permission(user, perm)
                    for perm in permissions
                )

                if not has_any:
                    logger.warning(
                        f"Permission denied for user {user.id}. "
                        f"Required one of: {permissions}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Insufficient permissions. Required one of: {', '.join(permissions)}"
                    )

            return await func(*args, **kwargs)

        return wrapper
    return decorator


def require_resource_access(resource_type: str, action: str):
    """
    Decorator to check resource-level access with ownership validation.

    Automatically extracts resource ID from path parameters and checks:
    1. User permissions for the action
    2. Resource ownership or organization membership
    3. Scope-based access (own/organization/all)

    Args:
        resource_type: Type of resource (content, agent, class, etc.)
        action: Action to perform (create, read, update, delete)

    Example:
        @router.delete("/content/{content_id}")
        @require_resource_access("content", "delete")
        async def delete_content(
            content_id: int,
            user: User = Depends(get_current_user),
            db: Session = Depends(get_db)
        ):
            # Access automatically validated based on ownership
            pass

    Raises:
        HTTPException 403: If user doesn't have access to resource
        HTTPException 404: If resource not found
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get('user') or kwargs.get('current_user')
            db = kwargs.get('db')

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            # Extract resource ID from path parameters
            # Common patterns: content_id, agent_id, class_id, user_id
            resource_id_key = f"{resource_type}_id"
            resource_id = kwargs.get(resource_id_key)

            if not resource_id:
                # Try alternative patterns
                resource_id = kwargs.get('id') or kwargs.get('resource_id')

            # Check scope-based permissions
            access_scope = rbac_manager.get_accessible_resources(user, resource_type, action)

            if access_scope["scope"] == "all":
                # Admin - full access
                logger.debug(f"Admin access granted for {resource_type}:{action}")
                return await func(*args, **kwargs)

            if access_scope["scope"] == "none":
                # No access at all
                logger.warning(
                    f"No access to {resource_type}:{action} for user {user.id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions for {resource_type}:{action}"
                )

            # For organization/own scope, we need to verify the resource
            if resource_id and db:
                # Import here to avoid circular imports
                from database import models

                # Map resource types to models
                model_map = {
                    'content': models.EducationalContent,
                    'agent': models.AgentInstance,
                    'class': models.Class,
                    'user': models.User,
                }

                model_class = model_map.get(resource_type)
                if model_class:
                    resource = db.query(model_class).filter_by(id=resource_id).first()

                    if not resource:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"{resource_type.capitalize()} not found"
                        )

                    # Check ownership for "own" scope
                    if access_scope["scope"] == "own":
                        resource_owner_id = getattr(resource, 'user_id', None) or getattr(resource, 'created_by', None)
                        if resource_owner_id != user.id:
                            logger.warning(
                                f"Ownership check failed: user {user.id} attempting to access "
                                f"{resource_type} {resource_id} owned by {resource_owner_id}"
                            )
                            raise HTTPException(
                                status_code=status.HTTP_403_FORBIDDEN,
                                detail="You can only access your own resources"
                            )

                    # Check organization for "organization" scope
                    elif access_scope["scope"] == "organization":
                        resource_org_id = getattr(resource, 'organization_id', None)
                        if resource_org_id != user.organization_id:
                            logger.warning(
                                f"Organization check failed: user org {user.organization_id} "
                                f"attempting to access {resource_type} in org {resource_org_id}"
                            )
                            raise HTTPException(
                                status_code=status.HTTP_403_FORBIDDEN,
                                detail="You can only access resources in your organization"
                            )

            logger.debug(
                f"Resource access granted: {resource_type}:{action} "
                f"for user {user.id} (scope: {access_scope['scope']})"
            )
            return await func(*args, **kwargs)

        return wrapper
    return decorator


def require_organization_access():
    """
    Decorator to ensure user has organization context.

    Verifies that user belongs to an organization before allowing access.
    Useful for multi-tenant endpoints.

    Example:
        @router.get("/organization/settings")
        @require_organization_access()
        async def get_org_settings(user: User = Depends(get_current_user)):
            # User guaranteed to have organization_id
            pass

    Raises:
        HTTPException 403: If user doesn't belong to an organization
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get('user') or kwargs.get('current_user')

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            if not hasattr(user, 'organization_id') or user.organization_id is None:
                logger.warning(
                    f"Organization access denied for user {user.id}: no organization"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User must belong to an organization"
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator


# Convenience decorators for common roles
require_admin = require_role(["admin"])
require_teacher = require_role(["admin", "teacher"])
require_teacher_or_student = require_role(["admin", "teacher", "student"])

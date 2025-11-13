"""
Role-Based Access Control Middleware for ToolBoxAI

This middleware provides role-based permission checking for API endpoints.
Integrates with Clerk authentication and supports the following roles:
- admin: Full system access
- teacher: Class and student management
- student: Limited access to own data
- parent: Access to child's data only
"""

import logging
from functools import wraps

from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)

# Role hierarchy (higher number = more permissions)
ROLE_HIERARCHY = {
    "admin": 4,
    "teacher": 3,
    "parent": 2,
    "student": 1,
}

# Define role-based permissions
ROLE_PERMISSIONS = {
    "admin": [
        "users:read",
        "users:write",
        "users:delete",
        "schools:read",
        "schools:write",
        "classes:read",
        "classes:write",
        "classes:delete",
        "reports:read",
        "reports:write",
        "analytics:read",
        "analytics:write",
        "roblox:manage",
        "system:configure",
        "compliance:manage",
    ],
    "teacher": [
        "classes:read",
        "classes:write",
        "students:read",
        "students:write",
        "lessons:read",
        "lessons:write",
        "assessments:read",
        "assessments:write",
        "reports:read",
        "messages:read",
        "messages:write",
        "roblox:view",
    ],
    "student": [
        "profile:read",
        "profile:write",
        "missions:read",
        "progress:read",
        "rewards:read",
        "leaderboard:read",
        "avatar:read",
        "avatar:write",
        "play:access",
    ],
    "parent": [
        "profile:read",
        "child_progress:read",
        "child_reports:read",
        "messages:read",
        "messages:write",
    ],
}


class RoleRequiredError(HTTPException):
    """Exception raised when user doesn't have required role"""

    def __init__(self, required_role: str, user_role: str | None = None):
        detail = f"Access denied. Required role: {required_role}"
        if user_role:
            detail += f". Your role: {user_role}"
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class PermissionDeniedError(HTTPException):
    """Exception raised when user doesn't have required permission"""

    def __init__(self, permission: str, user_role: str | None = None):
        detail = f"Access denied. Required permission: {permission}"
        if user_role:
            detail += f". Your role: {user_role}"
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


def get_user_role(request: Request) -> str | None:
    """
    Extract user role from request.
    First checks Clerk JWT token, then falls back to legacy session.
    """
    # Check if user is authenticated
    if not hasattr(request.state, "user") or not request.state.user:
        return None

    user = request.state.user

    # Try to get role from Clerk metadata
    if hasattr(user, "public_metadata") and user.public_metadata:
        role = user.public_metadata.get("role")
        if role:
            return role.lower()

    # Fallback to user object role property
    if hasattr(user, "role"):
        return user.role.lower() if user.role else None

    # Default role for authenticated users
    return "student"


def has_role(user_role: str, required_role: str) -> bool:
    """
    Check if user role meets the required role level.
    Uses role hierarchy for comparison.
    """
    user_level = ROLE_HIERARCHY.get(user_role, 0)
    required_level = ROLE_HIERARCHY.get(required_role, 0)
    return user_level >= required_level


def has_permission(user_role: str, permission: str) -> bool:
    """
    Check if user role has a specific permission.
    """
    permissions = ROLE_PERMISSIONS.get(user_role, [])
    return permission in permissions


def require_role(required_role: str):
    """
    Decorator to enforce role-based access control on endpoints.

    Usage:
        @router.get("/admin/users")
        @require_role("admin")
        async def get_users(request: Request):
            ...
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            user_role = get_user_role(request)

            if not user_role:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            if not has_role(user_role, required_role):
                logger.warning(
                    f"Access denied for user with role '{user_role}' "
                    f"to endpoint requiring '{required_role}'"
                )
                raise RoleRequiredError(required_role, user_role)

            logger.debug(
                f"Access granted for user with role '{user_role}' "
                f"to endpoint requiring '{required_role}'"
            )

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


def require_permission(permission: str):
    """
    Decorator to enforce permission-based access control on endpoints.

    Usage:
        @router.post("/classes")
        @require_permission("classes:write")
        async def create_class(request: Request):
            ...
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            user_role = get_user_role(request)

            if not user_role:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            if not has_permission(user_role, permission):
                logger.warning(
                    f"Permission denied for user with role '{user_role}' "
                    f"for permission '{permission}'"
                )
                raise PermissionDeniedError(permission, user_role)

            logger.debug(
                f"Permission granted for user with role '{user_role}' "
                f"for permission '{permission}'"
            )

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


def require_any_role(*roles: str):
    """
    Decorator to allow access if user has any of the specified roles.

    Usage:
        @router.get("/classes")
        @require_any_role("admin", "teacher")
        async def get_classes(request: Request):
            ...
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            user_role = get_user_role(request)

            if not user_role:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            if user_role not in roles:
                logger.warning(
                    f"Access denied for user with role '{user_role}'. "
                    f"Required one of: {', '.join(roles)}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required one of: {', '.join(roles)}",
                )

            logger.debug(
                f"Access granted for user with role '{user_role}'. "
                f"Allowed roles: {', '.join(roles)}"
            )

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


def require_any_permission(*permissions: str):
    """
    Decorator to allow access if user has any of the specified permissions.

    Usage:
        @router.get("/data")
        @require_any_permission("data:read", "data:write")
        async def get_data(request: Request):
            ...
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            user_role = get_user_role(request)

            if not user_role:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            user_has_permission = any(has_permission(user_role, perm) for perm in permissions)

            if not user_has_permission:
                logger.warning(
                    f"Permission denied for user with role '{user_role}'. "
                    f"Required one of: {', '.join(permissions)}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required one of: {', '.join(permissions)}",
                )

            logger.debug(
                f"Permission granted for user with role '{user_role}'. "
                f"Allowed permissions: {', '.join(permissions)}"
            )

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


# Rate limiting per role
ROLE_RATE_LIMITS = {
    "admin": {"calls": 1000, "period": 60},  # 1000 requests per minute
    "teacher": {"calls": 500, "period": 60},  # 500 requests per minute
    "parent": {"calls": 200, "period": 60},  # 200 requests per minute
    "student": {"calls": 100, "period": 60},  # 100 requests per minute
}


def get_rate_limit_for_role(role: str) -> dict:
    """Get rate limit configuration for a specific role"""
    return ROLE_RATE_LIMITS.get(role, {"calls": 60, "period": 60})

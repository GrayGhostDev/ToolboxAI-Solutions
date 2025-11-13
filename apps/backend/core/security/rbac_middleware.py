"""
RBAC Middleware for FastAPI

Automatic role-based access control enforcement at the middleware level.

Features:
- Automatic permission checking for all API requests
- Path-based permission mapping
- Organization-scoped request filtering
- Audit logging for access attempts
- Bypass rules for public endpoints

Usage:
    from fastapi import FastAPI
    from apps.backend.core.security.rbac_middleware import RBACMiddleware

    app = FastAPI()
    app.add_middleware(RBACMiddleware)
"""

import logging
import re
import time
from collections.abc import Callable

from starlette import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from apps.backend.core.security.rbac_manager import rbac_manager

logger = logging.getLogger(__name__)


class RBACMiddleware(BaseHTTPMiddleware):
    """
    RBAC enforcement middleware.

    Automatically checks permissions for API requests based on path and method.
    """

    def __init__(self, app, **kwargs):
        """
        Initialize RBAC middleware.

        Args:
            app: FastAPI application instance
        """
        super().__init__(app)

        # Public paths that don't require authentication
        self.public_paths: set[str] = {
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/health",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
            "/api/v1/auth/logout",
        }

        # Path patterns that should bypass RBAC (regex)
        self.bypass_patterns: list[re.Pattern] = [
            re.compile(r"^/static/.*"),
            re.compile(r"^/api/health/.*"),
            re.compile(r"^/_internal/.*"),
        ]

        # Map HTTP methods to actions
        self.method_action_map: dict[str, str] = {
            "GET": "read",
            "POST": "create",
            "PUT": "update",
            "PATCH": "update",
            "DELETE": "delete",
        }

        # Path-based permission mapping
        self.path_permissions = self._build_path_permissions()

        # Audit logging enabled
        self.audit_enabled = True

        logger.info("RBACMiddleware initialized")

    def _build_path_permissions(self) -> dict[str, dict[str, str]]:
        """
        Build mapping of paths to required permissions.

        Returns:
            Dictionary mapping path patterns to method-permission mappings
        """
        return {
            # Content endpoints
            r"/api/v1/content/?.*": {
                "GET": "content:read:organization",
                "POST": "content:create:organization",
                "PUT": "content:update:own",
                "PATCH": "content:update:own",
                "DELETE": "content:delete:own",
            },
            # Agent endpoints
            r"/api/v1/agents/?.*": {
                "GET": "agent:read:organization",
                "POST": "agent:create:organization",
                "PUT": "agent:update:own",
                "DELETE": "agent:delete:own",
            },
            r"/api/v1/agents/.*/execute": {
                "POST": "agent:execute:organization",
            },
            # User management
            r"/api/v1/users/?.*": {
                "GET": "user:read:organization",
                "POST": "user:create:all",  # Only admins
                "PUT": "user:update:own",
                "PATCH": "user:update:own",
                "DELETE": "user:delete:all",  # Only admins
            },
            # Organization management
            r"/api/v1/organizations/?.*": {
                "GET": "organization:read:organization",
                "POST": "organization:create:all",  # Only admins
                "PUT": "organization:update:organization",
                "DELETE": "organization:delete:all",  # Only admins
            },
            # Analytics
            r"/api/v1/analytics/?.*": {
                "GET": "analytics:read:organization",
                "POST": "analytics:export:organization",
            },
            # System management (admin only)
            r"/api/v1/system/?.*": {
                "GET": "system:monitor",
                "POST": "system:configure",
                "PUT": "system:configure",
                "DELETE": "system:manage",
            },
        }

    def _should_bypass(self, path: str) -> bool:
        """
        Check if path should bypass RBAC checks.

        Args:
            path: Request path

        Returns:
            True if path should bypass RBAC
        """
        # Check exact matches
        if path in self.public_paths:
            return True

        # Check pattern matches
        for pattern in self.bypass_patterns:
            if pattern.match(path):
                return True

        return False

    def _get_required_permission(self, path: str, method: str) -> str | None:
        """
        Get required permission for path and method.

        Args:
            path: Request path
            method: HTTP method

        Returns:
            Required permission string or None if not found
        """
        for path_pattern, method_permissions in self.path_permissions.items():
            if re.match(path_pattern, path):
                return method_permissions.get(method)

        # Default permission based on method if no specific mapping
        action = self.method_action_map.get(method)
        if action and path.startswith("/api/v1/"):
            # Extract resource from path
            parts = path.split("/")
            if len(parts) >= 4:
                resource = parts[3]  # e.g., /api/v1/content/123 -> "content"
                return f"{resource}:{action}:organization"

        return None

    def _extract_user_from_request(self, request: Request) -> dict | None:
        """
        Extract user from request state (set by auth middleware).

        Args:
            request: Starlette request

        Returns:
            User dictionary or None
        """
        # User should be set by authentication middleware
        return getattr(request.state, "user", None)

    def _log_access_attempt(
        self,
        user_id: int | None,
        path: str,
        method: str,
        permission: str | None,
        granted: bool,
        duration_ms: float,
    ):
        """
        Log access attempt for audit trail.

        Args:
            user_id: User ID attempting access
            path: Request path
            method: HTTP method
            permission: Required permission
            granted: Whether access was granted
            duration_ms: Processing duration in milliseconds
        """
        if not self.audit_enabled:
            return

        log_level = logging.INFO if granted else logging.WARNING
        log_message = (
            f"RBAC {'GRANTED' if granted else 'DENIED'}: "
            f"user={user_id or 'anonymous'} "
            f"method={method} "
            f"path={path} "
            f"permission={permission or 'none'} "
            f"duration={duration_ms:.2f}ms"
        )

        logger.log(log_level, log_message)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and enforce RBAC.

        Args:
            request: Incoming request
            call_next: Next middleware/endpoint in chain

        Returns:
            Response
        """
        start_time = time.time()

        path = request.url.path
        method = request.method

        # Bypass RBAC for public paths
        if self._should_bypass(path):
            return await call_next(request)

        # Extract user from request state
        user = self._extract_user_from_request(request)

        # If no user, check if authentication is required
        if not user:
            # Authentication middleware should have caught this
            # But double-check for security
            duration_ms = (time.time() - start_time) * 1000
            self._log_access_attempt(None, path, method, None, False, duration_ms)

            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authentication required"},
            )

        # Get required permission for this path/method
        required_permission = self._get_required_permission(path, method)

        if not required_permission:
            # No specific permission required - allow by default for authenticated users
            # (Endpoints can still use decorators for fine-grained control)
            return await call_next(request)

        # Check if user has required permission
        # Convert user dict to object-like access for rbac_manager
        class UserProxy:
            def __init__(self, user_dict):
                self.__dict__.update(user_dict)

        user_obj = UserProxy(user)

        has_permission = rbac_manager.has_permission(user_obj, required_permission)

        duration_ms = (time.time() - start_time) * 1000

        if not has_permission:
            self._log_access_attempt(
                user.get("id"), path, method, required_permission, False, duration_ms
            )

            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "detail": f"Insufficient permissions. Required: {required_permission}",
                    "required_permission": required_permission,
                    "user_role": user.get("role"),
                },
            )

        # Permission granted - log and proceed
        self._log_access_attempt(
            user.get("id"), path, method, required_permission, True, duration_ms
        )

        # Add permission info to request state for endpoint use
        request.state.granted_permission = required_permission

        return await call_next(request)


class OrganizationScopingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically scope queries by organization.

    Sets organization context for database queries based on user's organization.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Set organization context for request.

        Args:
            request: Incoming request
            call_next: Next middleware/endpoint

        Returns:
            Response
        """
        user = getattr(request.state, "user", None)

        if user and user.get("organization_id"):
            # Set organization context in request state
            request.state.organization_id = user.get("organization_id")

            # Can also set PostgreSQL session variable for RLS
            # This would be done in database dependency

        return await call_next(request)

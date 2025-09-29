"""
Tenant Middleware for FastAPI Multi-Tenancy Support

This middleware extracts tenant context from JWT tokens and headers,
sets tenant context for each request, and provides request logging
with tenant information for the ToolBoxAI Educational Platform.
"""

import logging
import time
import uuid
from typing import Optional, Dict, Any, Callable, Awaitable
from contextvars import ContextVar

from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from apps.backend.api.auth.auth import JWTManager
from apps.backend.core.config import settings

logger = logging.getLogger(__name__)

# Context variables for storing tenant information during request processing
current_tenant_id: ContextVar[Optional[str]] = ContextVar('current_tenant_id', default=None)
current_organization_id: ContextVar[Optional[str]] = ContextVar('current_organization_id', default=None)
current_user_id: ContextVar[Optional[str]] = ContextVar('current_user_id', default=None)
is_super_admin: ContextVar[bool] = ContextVar('is_super_admin', default=False)


class TenantContext:
    """
    Tenant context container for the current request.
    """

    def __init__(
        self,
        tenant_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        user_id: Optional[str] = None,
        is_super_admin: bool = False,
        permissions: Optional[Dict[str, Any]] = None
    ):
        self.tenant_id = tenant_id
        self.organization_id = organization_id
        self.user_id = user_id
        self.is_super_admin = is_super_admin
        self.permissions = permissions or {}

    @property
    def has_tenant(self) -> bool:
        """Check if tenant context is available"""
        return self.tenant_id is not None or self.organization_id is not None

    @property
    def effective_tenant_id(self) -> Optional[str]:
        """Get the effective tenant ID (organization_id preferred)"""
        return self.organization_id or self.tenant_id

    def can_access_tenant(self, tenant_id: str) -> bool:
        """Check if current context can access the specified tenant"""
        if self.is_super_admin:
            return True
        return self.effective_tenant_id == tenant_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for logging"""
        return {
            "tenant_id": self.tenant_id,
            "organization_id": self.organization_id,
            "user_id": self.user_id,
            "is_super_admin": self.is_super_admin,
            "has_tenant": self.has_tenant,
            "effective_tenant_id": self.effective_tenant_id
        }


def get_tenant_context() -> TenantContext:
    """
    Get the current tenant context from context variables.

    Returns:
        TenantContext: Current tenant context
    """
    return TenantContext(
        tenant_id=current_tenant_id.get(),
        organization_id=current_organization_id.get(),
        user_id=current_user_id.get(),
        is_super_admin=is_super_admin.get()
    )


def set_tenant_context(context: TenantContext) -> None:
    """
    Set the tenant context for the current request.

    Args:
        context: TenantContext to set
    """
    current_tenant_id.set(context.tenant_id)
    current_organization_id.set(context.organization_id)
    current_user_id.set(context.user_id)
    is_super_admin.set(context.is_super_admin)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract and set tenant context for each request.

    This middleware:
    1. Extracts organization_id from JWT token or headers
    2. Sets tenant context for the request
    3. Handles super admin access patterns
    4. Provides detailed request logging with tenant info
    5. Validates tenant access permissions
    """

    def __init__(
        self,
        app: FastAPI,
        require_tenant: bool = True,
        exclude_paths: Optional[list[str]] = None,
        super_admin_header: str = "X-Super-Admin",
        tenant_header: str = "X-Tenant-ID"
    ):
        super().__init__(app)
        self.require_tenant = require_tenant
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/api/v1/health",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/organizations",  # Allow org creation
            "/migration/status"
        ]
        self.super_admin_header = super_admin_header
        self.tenant_header = tenant_header

        logger.info(
            f"TenantMiddleware initialized: require_tenant={require_tenant}, "
            f"exclude_paths={len(self.exclude_paths)} paths"
        )

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request and extract tenant context.

        Args:
            request: FastAPI Request object
            call_next: Next middleware/route handler

        Returns:
            Response: HTTP response
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())

        # Add request ID to request state
        request.state.request_id = request_id

        try:
            # Skip tenant extraction for excluded paths
            if self._should_skip_tenant_check(request.url.path):
                logger.debug(f"Skipping tenant check for path: {request.url.path}")
                response = await call_next(request)
                self._log_request(request, response, start_time, skipped=True)
                return response

            # Extract tenant context
            tenant_context = await self._extract_tenant_context(request)

            # Set context variables for the request
            set_tenant_context(tenant_context)

            # Add tenant info to request state for access in route handlers
            request.state.tenant_context = tenant_context

            # Validate tenant access if required
            if self.require_tenant and not tenant_context.has_tenant and not tenant_context.is_super_admin:
                logger.warning(
                    f"Request {request_id} rejected: No tenant context available",
                    extra={
                        "request_id": request_id,
                        "path": request.url.path,
                        "method": request.method,
                        "client_ip": request.client.host
                    }
                )
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "error": "tenant_required",
                        "message": "Request must include valid tenant context",
                        "details": "Organization ID is required for this operation"
                    }
                )

            # Process request
            response = await call_next(request)

            # Log successful request
            self._log_request(request, response, start_time, tenant_context)

            return response

        except HTTPException as e:
            # Handle HTTP exceptions with tenant context
            logger.warning(
                f"HTTP exception in request {request_id}: {e.status_code} - {e.detail}",
                extra={
                    "request_id": request_id,
                    "status_code": e.status_code,
                    "path": request.url.path,
                    "method": request.method
                }
            )
            raise

        except Exception as e:
            # Handle unexpected errors
            logger.error(
                f"Unexpected error in tenant middleware for request {request_id}: {str(e)}",
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method,
                    "error_type": type(e).__name__
                },
                exc_info=True
            )

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "internal_server_error",
                    "message": "An unexpected error occurred",
                    "request_id": request_id
                }
            )

    def _should_skip_tenant_check(self, path: str) -> bool:
        """
        Check if tenant validation should be skipped for the given path.

        Args:
            path: Request path

        Returns:
            bool: True if tenant check should be skipped
        """
        return any(path.startswith(excluded_path) for excluded_path in self.exclude_paths)

    async def _extract_tenant_context(self, request: Request) -> TenantContext:
        """
        Extract tenant context from request headers and JWT token.

        Args:
            request: FastAPI Request object

        Returns:
            TenantContext: Extracted tenant context
        """
        tenant_id = None
        organization_id = None
        user_id = None
        is_admin = False

        # 1. Check for explicit tenant header (for admin operations)
        if self.tenant_header in request.headers:
            tenant_id = request.headers[self.tenant_header]
            logger.debug(f"Tenant ID from header: {tenant_id}")

        # 2. Check for super admin header
        if self.super_admin_header in request.headers:
            admin_token = request.headers[self.super_admin_header]
            is_admin = await self._validate_super_admin_token(admin_token)
            if is_admin:
                logger.info("Super admin access granted")

        # 3. Extract from JWT token (primary method)
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]

            try:
                payload = JWTManager.verify_token(token, raise_on_error=False)
                if payload:
                    user_id = payload.get("sub")
                    organization_id = payload.get("organization_id")
                    tenant_id = tenant_id or payload.get("tenant_id")

                    # Check if user has super admin role
                    user_role = payload.get("role", "").lower()
                    if user_role in ["super_admin", "system_admin"]:
                        is_admin = True

                    logger.debug(
                        f"JWT context extracted: user_id={user_id}, "
                        f"organization_id={organization_id}, role={user_role}"
                    )

            except Exception as e:
                logger.warning(f"Failed to extract context from JWT: {str(e)}")

        # 4. Create tenant context
        context = TenantContext(
            tenant_id=tenant_id,
            organization_id=organization_id,
            user_id=user_id,
            is_super_admin=is_admin
        )

        logger.debug(f"Final tenant context: {context.to_dict()}")
        return context

    async def _validate_super_admin_token(self, token: str) -> bool:
        """
        Validate super admin token.

        Args:
            token: Super admin token to validate

        Returns:
            bool: True if token is valid
        """
        # In production, this would validate against a secure store
        # For now, check against configured super admin key
        super_admin_key = getattr(settings, 'SUPER_ADMIN_KEY', None)

        if not super_admin_key:
            logger.warning("Super admin key not configured")
            return False

        is_valid = token == super_admin_key
        if is_valid:
            logger.info("Super admin token validated successfully")
        else:
            logger.warning("Invalid super admin token provided")

        return is_valid

    def _log_request(
        self,
        request: Request,
        response: Response,
        start_time: float,
        tenant_context: Optional[TenantContext] = None,
        skipped: bool = False
    ) -> None:
        """
        Log request with tenant context information.

        Args:
            request: FastAPI Request object
            response: FastAPI Response object
            start_time: Request start time
            tenant_context: Tenant context (if available)
            skipped: Whether tenant check was skipped
        """
        duration = time.time() - start_time

        # Build log data
        log_data = {
            "request_id": getattr(request.state, 'request_id', 'unknown'),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
            "client_ip": request.client.host,
            "user_agent": request.headers.get("User-Agent", "unknown"),
            "tenant_check_skipped": skipped
        }

        # Add tenant context if available
        if tenant_context:
            log_data.update({
                "tenant_context": tenant_context.to_dict()
            })

        # Log with appropriate level based on status code
        if response.status_code >= 500:
            logger.error("Request completed with server error", extra=log_data)
        elif response.status_code >= 400:
            logger.warning("Request completed with client error", extra=log_data)
        else:
            logger.info("Request completed successfully", extra=log_data)


def add_tenant_middleware(app: FastAPI, **kwargs) -> None:
    """
    Add tenant middleware to FastAPI application.

    Args:
        app: FastAPI application instance
        **kwargs: Additional middleware configuration
    """
    app.add_middleware(TenantMiddleware, **kwargs)
    logger.info("Tenant middleware added to FastAPI application")


# Utility functions for use in route handlers
def require_tenant_context() -> TenantContext:
    """
    Get tenant context and raise exception if not available.

    Returns:
        TenantContext: Current tenant context

    Raises:
        HTTPException: If no tenant context is available
    """
    context = get_tenant_context()

    if not context.has_tenant and not context.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context is required for this operation"
        )

    return context


def get_current_tenant_id() -> Optional[str]:
    """
    Get the current tenant ID from context.

    Returns:
        Optional[str]: Current tenant/organization ID
    """
    context = get_tenant_context()
    return context.effective_tenant_id


def validate_tenant_access(tenant_id: str) -> bool:
    """
    Validate that current context can access the specified tenant.

    Args:
        tenant_id: Tenant ID to validate access for

    Returns:
        bool: True if access is allowed
    """
    context = get_tenant_context()
    return context.can_access_tenant(tenant_id)


# Export public interface
__all__ = [
    "TenantMiddleware",
    "TenantContext",
    "add_tenant_middleware",
    "get_tenant_context",
    "set_tenant_context",
    "require_tenant_context",
    "get_current_tenant_id",
    "validate_tenant_access",
    "current_tenant_id",
    "current_organization_id",
    "current_user_id",
    "is_super_admin"
]
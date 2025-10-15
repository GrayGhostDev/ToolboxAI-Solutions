"""Compatibility shim for legacy imports.

Historically the application imported ``TenantMiddleware`` from
``apps.backend.middleware.tenant_middleware``.  The fully featured
implementation now lives in ``apps.backend.middleware.tenant``.

This module simply re-exports the modern middleware to avoid widespread import
changes while enabling the richer tenant context logic.
"""

from apps.backend.middleware.tenant import (  # noqa: F401
    TenantMiddleware,
    TenantContext,
    add_tenant_middleware,
    get_tenant_context,
    set_tenant_context,
    require_tenant_context,
    get_current_tenant_id,
    validate_tenant_access,
)

__all__ = [
    "TenantMiddleware",
    "TenantContext",
    "add_tenant_middleware",
    "get_tenant_context",
    "set_tenant_context",
    "require_tenant_context",
    "get_current_tenant_id",
    "validate_tenant_access",
]

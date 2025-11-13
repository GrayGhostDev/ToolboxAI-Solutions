"""
API Key Authentication Dependencies

FastAPI dependencies for API key authentication and authorization.
"""

import logging
from typing import List, Optional

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyCookie, APIKeyHeader, APIKeyQuery

from apps.backend.services.api_key_manager import APIKeyScope, api_key_manager

logger = logging.getLogger(__name__)

# Security schemes
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
api_key_query = APIKeyQuery(name="api_key", auto_error=False)
api_key_cookie = APIKeyCookie(name="api_key", auto_error=False)


async def get_api_key(
    header_key: Optional[str] = Security(api_key_header),
    query_key: Optional[str] = Security(api_key_query),
    cookie_key: Optional[str] = Security(api_key_cookie),
) -> Optional[str]:
    """
    Get API key from header, query parameter, or cookie.

    Priority order:
    1. Header (X-API-Key)
    2. Query parameter (api_key)
    3. Cookie (api_key)
    """
    return header_key or query_key or cookie_key


async def validate_api_key(request: Request, api_key: Optional[str] = Depends(get_api_key)) -> dict:
    """
    Validate API key and return key details.

    Args:
        request: FastAPI request
        api_key: API key from header/query/cookie

    Returns:
        API key model details

    Raises:
        HTTPException: If key is invalid or missing
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Get request details for validation
    client_ip = request.client.host if request.client else None
    origin = request.headers.get("Origin")

    # Validate the key
    is_valid, key_model = await api_key_manager.validate_api_key(
        api_key=api_key, request_ip=client_ip, origin=origin
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Check rate limiting
    allowed, retry_after = await api_key_manager.check_rate_limit(
        api_key=key_model, source=request.url.path
    )

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )

    # Store key info in request state for logging
    request.state.api_key = {
        "key_id": key_model.key_id,
        "name": key_model.name,
        "organization": key_model.organization,
        "scopes": key_model.scopes,
    }

    return request.state.api_key


def require_api_key(scopes: Optional[List[str]] = None):
    """
    Dependency to require API key with specific scopes.

    Usage:
        @router.get("/protected")
        async def protected_endpoint(
            api_key: dict = Depends(require_api_key(["read"]))
        ):
            return {"message": "Protected resource"}

    Args:
        scopes: Required scopes for the endpoint

    Returns:
        Dependency function
    """

    async def dependency(request: Request, api_key: Optional[str] = Depends(get_api_key)) -> dict:
        """Validate API key with required scopes."""
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        # Get request details
        client_ip = request.client.host if request.client else None
        origin = request.headers.get("Origin")

        # Validate with scopes
        is_valid, key_model = await api_key_manager.validate_api_key(
            api_key=api_key, required_scopes=scopes, request_ip=client_ip, origin=origin
        )

        if not is_valid:
            if scopes:
                detail = f"API key lacks required scopes: {', '.join(scopes)}"
            else:
                detail = "Invalid API key"

            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

        # Check rate limiting
        allowed, retry_after = await api_key_manager.check_rate_limit(
            api_key=key_model, source=request.url.path
        )

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(retry_after)},
            )

        # Store in request state
        request.state.api_key = {
            "key_id": key_model.key_id,
            "name": key_model.name,
            "organization": key_model.organization,
            "scopes": key_model.scopes,
        }

        return request.state.api_key

    return dependency


# Pre-configured dependencies for common scopes
require_read_access = require_api_key([APIKeyScope.READ])
require_write_access = require_api_key([APIKeyScope.WRITE])
require_admin_access = require_api_key([APIKeyScope.ADMIN])

# Service-specific dependencies
require_roblox_access = require_api_key([APIKeyScope.ROBLOX])
require_ai_access = require_api_key([APIKeyScope.AI])
require_webhook_access = require_api_key([APIKeyScope.WEBHOOK])
require_analytics_access = require_api_key([APIKeyScope.ANALYTICS])
require_content_access = require_api_key([APIKeyScope.CONTENT])


async def optional_api_key(
    request: Request, api_key: Optional[str] = Depends(get_api_key)
) -> Optional[dict]:
    """
    Optional API key validation.

    If key is provided, it's validated. If not, returns None.
    Useful for endpoints that have enhanced features with API key.
    """
    if not api_key:
        return None

    # Get request details
    client_ip = request.client.host if request.client else None
    origin = request.headers.get("Origin")

    # Validate the key
    is_valid, key_model = await api_key_manager.validate_api_key(
        api_key=api_key, request_ip=client_ip, origin=origin
    )

    if not is_valid:
        # For optional key, just log and return None
        logger.debug(f"Invalid optional API key provided from {client_ip}")
        return None

    # Store in request state
    request.state.api_key = {
        "key_id": key_model.key_id,
        "name": key_model.name,
        "organization": key_model.organization,
        "scopes": key_model.scopes,
    }

    return request.state.api_key


# Export all dependencies
__all__ = [
    "get_api_key",
    "validate_api_key",
    "require_api_key",
    "optional_api_key",
    "require_read_access",
    "require_write_access",
    "require_admin_access",
    "require_roblox_access",
    "require_ai_access",
    "require_webhook_access",
    "require_analytics_access",
    "require_content_access",
]

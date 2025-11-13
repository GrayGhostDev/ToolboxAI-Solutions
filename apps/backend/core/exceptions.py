"""
Application-specific exceptions for ToolBoxAI backend
"""

from typing import Any

from fastapi import HTTPException


class APIError(HTTPException):
    """Base API error class"""

    def __init__(
        self,
        status_code: int = 500,
        detail: str = "Internal server error",
        headers: dict[str, Any] | None = None,
        error_code: str | None = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code


class ValidationError(APIError):
    """Validation error for request data"""

    def __init__(
        self,
        detail: str = "Validation failed",
        field: str | None = None,
        headers: dict[str, Any] | None = None,
    ):
        super().__init__(status_code=422, detail=detail, headers=headers, error_code="E001")
        self.field = field


class AuthenticationError(APIError):
    """Authentication failed error"""

    def __init__(
        self, detail: str = "Authentication required", headers: dict[str, Any] | None = None
    ):
        super().__init__(
            status_code=401,
            detail=detail,
            headers=headers or {"WWW-Authenticate": "Bearer"},
            error_code="E002",
        )


class AuthorizationError(APIError):
    """Authorization/permission error"""

    def __init__(
        self,
        detail: str = "Insufficient permissions",
        resource: str | None = None,
        headers: dict[str, Any] | None = None,
    ):
        super().__init__(status_code=403, detail=detail, headers=headers, error_code="E003")
        self.resource = resource


class NotFoundError(APIError):
    """Resource not found error"""

    def __init__(
        self,
        detail: str = "Resource not found",
        resource_type: str | None = None,
        resource_id: str | None = None,
        headers: dict[str, Any] | None = None,
    ):
        super().__init__(status_code=404, detail=detail, headers=headers, error_code="E004")
        self.resource_type = resource_type
        self.resource_id = resource_id


class ConflictError(APIError):
    """Resource conflict error"""

    def __init__(self, detail: str = "Resource conflict", headers: dict[str, Any] | None = None):
        super().__init__(status_code=409, detail=detail, headers=headers, error_code="E005")


class RateLimitError(APIError):
    """Rate limit exceeded error"""

    def __init__(
        self,
        detail: str = "Rate limit exceeded",
        retry_after: int | None = None,
        headers: dict[str, Any] | None = None,
    ):
        headers = headers or {}
        if retry_after:
            headers["Retry-After"] = str(retry_after)

        super().__init__(status_code=429, detail=detail, headers=headers, error_code="E006")
        self.retry_after = retry_after


class DatabaseError(APIError):
    """Database operation error"""

    def __init__(
        self,
        detail: str = "Database operation failed",
        operation: str | None = None,
        headers: dict[str, Any] | None = None,
    ):
        super().__init__(status_code=500, detail=detail, headers=headers, error_code="E009")
        self.operation = operation


class ContentGenerationError(APIError):
    """Content generation failed error"""

    def __init__(
        self,
        detail: str = "Content generation failed",
        content_type: str | None = None,
        headers: dict[str, Any] | None = None,
    ):
        super().__init__(status_code=500, detail=detail, headers=headers, error_code="E007")
        self.content_type = content_type


class PluginConnectionError(APIError):
    """Plugin connection failed error"""

    def __init__(
        self,
        detail: str = "Plugin connection failed",
        plugin_id: str | None = None,
        headers: dict[str, Any] | None = None,
    ):
        super().__init__(status_code=503, detail=detail, headers=headers, error_code="E008")
        self.plugin_id = plugin_id


class CacheError(APIError):
    """Cache operation error"""

    def __init__(
        self,
        detail: str = "Cache operation failed",
        cache_key: str | None = None,
        headers: dict[str, Any] | None = None,
    ):
        super().__init__(status_code=500, detail=detail, headers=headers, error_code="E010")
        self.cache_key = cache_key


class ExternalServiceError(APIError):
    """External service error"""

    def __init__(
        self,
        detail: str = "External service error",
        service: str | None = None,
        headers: dict[str, Any] | None = None,
    ):
        super().__init__(status_code=503, detail=detail, headers=headers, error_code="E011")
        self.service = service


__all__ = [
    "APIError",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ConflictError",
    "RateLimitError",
    "DatabaseError",
    "ContentGenerationError",
    "PluginConnectionError",
    "CacheError",
    "ExternalServiceError",
]

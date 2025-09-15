"""
Comprehensive Error Handling System

Implements consistent error handling across the application following
FastAPI best practices and security guidelines.

References:
- FastAPI Error Handling: https://fastapi.tiangolo.com/tutorial/handling-errors/
- OWASP Error Handling: https://cheatsheetseries.owasp.org/cheatsheets/Error_Handling_Cheat_Sheet.html
"""

import logging
import traceback
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_serializer, ConfigDict
from starlette.exceptions import HTTPException as StarletteHTTPException

from apps.backend.core.logging import logging_manager, log_error, log_audit

logger = logging_manager.get_logger(__name__)


class ErrorSeverity(str, Enum):
    """Error severity levels for logging and monitoring"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Error categories for classification and routing"""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RATE_LIMIT = "rate_limit"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_SERVICE = "external_service"
    DATABASE = "database"
    INTERNAL = "internal"
    NETWORK = "network"
    CONFIGURATION = "configuration"


class ErrorDetail(BaseModel):
    """Detailed error information for debugging"""
    field: Optional[str] = None
    message: str
    code: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standardized error response following REST best practices"""
    error: bool = True
    error_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status_code: int
    category: ErrorCategory
    message: str
    details: Optional[List[ErrorDetail]] = None
    path: Optional[str] = None
    method: Optional[str] = None
    correlation_id: Optional[str] = None

    @field_serializer('timestamp')
    def serialize_timestamp(self, timestamp: datetime, _info) -> str:
        """Serialize datetime to ISO format string"""
        return timestamp.isoformat()

    # CLAUDE: Fixed - replaced class Config with model_config for Pydantic v2
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        },
        use_enum_values=True,
        validate_assignment=True
    )


class ApplicationError(Exception):
    """Base exception for all application errors"""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        category: ErrorCategory = ErrorCategory.INTERNAL,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[List[ErrorDetail]] = None,
        error_code: Optional[str] = None,
        log_error: bool = True
    ):
        self.message = message
        self.status_code = status_code
        self.category = category
        self.severity = severity
        self.details = details or []
        self.error_code = error_code or self.__class__.__name__
        self.log_error = log_error
        super().__init__(message)


class ValidationError(ApplicationError):
    """Validation error for input data"""

    def __init__(self, message: str, details: Optional[List[ErrorDetail]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            details=details,
            log_error=False
        )


class AuthenticationError(ApplicationError):
    """Authentication failure"""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.MEDIUM
        )


class AuthorizationError(ApplicationError):
    """Authorization failure"""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.MEDIUM
        )


class NotFoundError(ApplicationError):
    """Resource not found"""

    def __init__(self, resource: str, identifier: Optional[str] = None):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            category=ErrorCategory.NOT_FOUND,
            severity=ErrorSeverity.LOW,
            log_error=False
        )


class ConflictError(ApplicationError):
    """Resource conflict"""

    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            category=ErrorCategory.CONFLICT,
            severity=ErrorSeverity.LOW
        )


class RateLimitError(ApplicationError):
    """Rate limit exceeded"""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            category=ErrorCategory.RATE_LIMIT,
            severity=ErrorSeverity.LOW,
            log_error=False
        )
        self.retry_after = retry_after


class ExternalServiceError(ApplicationError):
    """External service failure"""

    def __init__(self, service: str, message: str):
        super().__init__(
            message=f"External service error ({service}): {message}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            category=ErrorCategory.EXTERNAL_SERVICE,
            severity=ErrorSeverity.HIGH
        )


class DatabaseError(ApplicationError):
    """Database operation failure"""

    def __init__(self, message: str, operation: Optional[str] = None):
        details = []
        if operation:
            details.append(ErrorDetail(message=f"Operation: {operation}"))
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            details=details
        )


class ConfigurationError(ApplicationError):
    """Configuration error"""

    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.CRITICAL
        )


class ErrorHandler:
    """Central error handler with consistent formatting and logging"""

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.error_mappers = {}
        self._setup_default_mappers()

    def _setup_default_mappers(self):
        """Setup default error type mappings"""
        self.register_mapper(ApplicationError, self._handle_application_error)
        self.register_mapper(HTTPException, self._handle_http_exception)
        self.register_mapper(RequestValidationError, self._handle_validation_error)
        self.register_mapper(ValueError, self._handle_value_error)
        self.register_mapper(Exception, self._handle_generic_error)

    def register_mapper(self, error_type: type, handler):
        """Register custom error mapper"""
        self.error_mappers[error_type] = handler

    async def handle_error(
        self,
        request: Request,
        exc: Exception
    ) -> JSONResponse:
        """Main error handling entry point"""
        # Get correlation ID from request or generate new one
        correlation_id = getattr(request.state, "correlation_id", None)
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
            request.state.correlation_id = correlation_id

        # Find appropriate handler
        handler = None
        for error_type, mapper in self.error_mappers.items():
            if isinstance(exc, error_type):
                handler = mapper
                break

        if not handler:
            handler = self._handle_generic_error

        # Handle the error
        error_response = await handler(request, exc, correlation_id)

        # Add request context
        error_response.path = str(request.url.path)
        error_response.method = request.method
        error_response.correlation_id = correlation_id

        # Log the error
        self._log_error(error_response, exc)

        # Prepare response headers
        headers = {
            "X-Error-ID": error_response.error_id,
            "X-Correlation-ID": correlation_id,
        }

        # Add retry-after header for rate limit errors
        if isinstance(exc, RateLimitError) and exc.retry_after:
            headers["Retry-After"] = str(exc.retry_after)

        # Create response - use model_dump for Pydantic v2 with JSON-compatible format
        if hasattr(error_response, 'model_dump'):
            # Pydantic v2
            response_dict = error_response.model_dump(exclude_none=True, mode='json')
        else:
            # Pydantic v1 fallback
            response_dict = error_response.dict(exclude_none=True)
            # Convert datetime to ISO format string
            if 'timestamp' in response_dict and hasattr(response_dict['timestamp'], 'isoformat'):
                response_dict['timestamp'] = response_dict['timestamp'].isoformat()

        # Remove sensitive information in production
        if not self.debug:
            response_dict.pop("debug_info", None)

        return JSONResponse(
            status_code=error_response.status_code,
            content=response_dict,
            headers=headers
        )

    async def _handle_application_error(
        self,
        request: Request,
        exc: ApplicationError,
        correlation_id: str
    ) -> ErrorResponse:
        """Handle application-specific errors"""
        return ErrorResponse(
            error_id=str(uuid.uuid4()),
            status_code=exc.status_code,
            category=exc.category,
            message=exc.message,
            details=exc.details,
            correlation_id=correlation_id
        )

    async def _handle_http_exception(
        self,
        request: Request,
        exc: Union[HTTPException, StarletteHTTPException],
        correlation_id: str
    ) -> ErrorResponse:
        """Handle HTTP exceptions"""
        category = self._map_status_to_category(exc.status_code)

        # Extract message
        if hasattr(exc, 'detail'):
            message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        else:
            message = str(exc)

        return ErrorResponse(
            error_id=str(uuid.uuid4()),
            status_code=exc.status_code,
            category=category,
            message=message,
            correlation_id=correlation_id
        )

    async def _handle_validation_error(
        self,
        request: Request,
        exc: RequestValidationError,
        correlation_id: str
    ) -> ErrorResponse:
        """Handle request validation errors"""
        details = []
        for error in exc.errors():
            # Extract field path
            field_path = ".".join(str(loc) for loc in error.get("loc", []))
            if field_path.startswith("body."):
                field_path = field_path[5:]  # Remove "body." prefix

            details.append(ErrorDetail(
                field=field_path,
                message=error.get("msg", "Validation failed"),
                code=error.get("type"),
                context={"input": error.get("input")} if self.debug else None
            ))

        return ErrorResponse(
            error_id=str(uuid.uuid4()),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            category=ErrorCategory.VALIDATION,
            message="Request validation failed",
            details=details,
            correlation_id=correlation_id
        )

    async def _handle_value_error(
        self,
        request: Request,
        exc: ValueError,
        correlation_id: str
    ) -> ErrorResponse:
        """Handle value errors"""
        return ErrorResponse(
            error_id=str(uuid.uuid4()),
            status_code=status.HTTP_400_BAD_REQUEST,
            category=ErrorCategory.VALIDATION,
            message=str(exc) if self.debug else "Invalid input provided",
            correlation_id=correlation_id
        )

    async def _handle_generic_error(
        self,
        request: Request,
        exc: Exception,
        correlation_id: str
    ) -> ErrorResponse:
        """Handle unexpected errors"""
        # Log full exception for unknown errors
        logger.exception(f"Unexpected error: {exc}")

        # Prepare error response
        message = str(exc) if self.debug else "An internal error occurred"

        details = None
        if self.debug:
            details = [ErrorDetail(
                message="Stack trace",
                context={"traceback": traceback.format_exc()}
            )]

        return ErrorResponse(
            error_id=str(uuid.uuid4()),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            category=ErrorCategory.INTERNAL,
            message=message,
            details=details,
            correlation_id=correlation_id
        )

    def _map_status_to_category(self, status_code: int) -> ErrorCategory:
        """Map HTTP status code to error category"""
        mapping = {
            400: ErrorCategory.VALIDATION,
            401: ErrorCategory.AUTHENTICATION,
            403: ErrorCategory.AUTHORIZATION,
            404: ErrorCategory.NOT_FOUND,
            409: ErrorCategory.CONFLICT,
            422: ErrorCategory.VALIDATION,
            429: ErrorCategory.RATE_LIMIT,
            503: ErrorCategory.EXTERNAL_SERVICE,
        }

        if status_code in mapping:
            return mapping[status_code]
        elif 400 <= status_code < 500:
            return ErrorCategory.BUSINESS_LOGIC
        else:
            return ErrorCategory.INTERNAL

    def _log_error(self, error_response: ErrorResponse, exc: Exception):
        """Log error with appropriate level"""
        # Prepare log context
        log_context = {
            "error_id": error_response.error_id,
            "correlation_id": error_response.correlation_id,
            "category": error_response.category.value if hasattr(error_response.category, 'value') else error_response.category,
            "status_code": error_response.status_code,
            "path": error_response.path,
            "method": error_response.method,
        }

        # Determine if we should log this error
        if isinstance(exc, ApplicationError) and not exc.log_error:
            return

        # Determine log level based on status code and severity
        if error_response.status_code >= 500:
            logger.error(
                f"[{error_response.error_id}] {error_response.message}",
                exc_info=exc if self.debug else None,
                extra_fields=log_context
            )
        elif error_response.status_code >= 400:
            if error_response.category in [ErrorCategory.AUTHENTICATION, ErrorCategory.AUTHORIZATION]:
                logger.warning(
                    f"[{error_response.error_id}] {error_response.message}",
                    extra_fields=log_context
                )
            else:
                logger.info(
                    f"[{error_response.error_id}] {error_response.message}",
                    extra_fields=log_context
                )
        else:
            logger.debug(
                f"[{error_response.error_id}] {error_response.message}",
                extra_fields=log_context
            )


# Global error handler instance
_error_handler: Optional[ErrorHandler] = None


def get_error_handler(debug: bool = False) -> ErrorHandler:
    """Get or create the global error handler"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler(debug=debug)
    return _error_handler


async def handle_application_error(request: Request, exc: ApplicationError) -> JSONResponse:
    """FastAPI exception handler for ApplicationError"""
    handler = get_error_handler(debug=getattr(request.app.state, "debug", False))
    return await handler.handle_error(request, exc)


async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    """FastAPI exception handler for HTTPException"""
    handler = get_error_handler(debug=getattr(request.app.state, "debug", False))
    return await handler.handle_error(request, exc)


async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    """FastAPI exception handler for RequestValidationError"""
    handler = get_error_handler(debug=getattr(request.app.state, "debug", False))
    return await handler.handle_error(request, exc)


async def handle_generic_exception(request: Request, exc: Exception) -> JSONResponse:
    """FastAPI exception handler for generic exceptions"""
    handler = get_error_handler(debug=getattr(request.app.state, "debug", False))
    return await handler.handle_error(request, exc)
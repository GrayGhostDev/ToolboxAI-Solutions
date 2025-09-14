"""
Error Handling Module

Provides comprehensive error handling for the application with:
- Consistent error responses
- Exception type hierarchy
- Middleware for catching unhandled errors
- FastAPI exception handlers
"""

# Import from the new error handler module
from .error_handler import (
    # Error types
    ApplicationError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    ConfigurationError,
    DatabaseError,
    ExternalServiceError,
    NotFoundError,
    RateLimitError,
    ValidationError,
    
    # Error models
    ErrorCategory,
    ErrorDetail,
    ErrorResponse,
    ErrorSeverity,
    
    # Handler
    ErrorHandler,
    get_error_handler,
    
    # FastAPI exception handlers
    handle_application_error,
    handle_generic_exception,
    handle_http_exception,
    handle_validation_error,
)

# Import from the middleware module (existing functionality)
from .middleware import (
    ErrorHandlingMiddleware,
    ErrorLevel,
    ErrorContext,
    ErrorMetrics,
    ErrorRecoveryStrategy,
    ErrorAggregator,
    create_error_handling_middleware,
    AppValidationError,
    ResourceNotFoundError,
)

__all__ = [
    # From error_handler.py
    "ApplicationError",
    "AuthenticationError", 
    "AuthorizationError",
    "ConflictError",
    "ConfigurationError",
    "DatabaseError",
    "ExternalServiceError",
    "NotFoundError",
    "RateLimitError",
    "ValidationError",
    "ErrorCategory",
    "ErrorDetail",
    "ErrorResponse",
    "ErrorSeverity",
    "ErrorHandler",
    "get_error_handler",
    "handle_application_error",
    "handle_generic_exception",
    "handle_http_exception",
    "handle_validation_error",
    
    # From middleware.py
    "ErrorHandlingMiddleware",
    "ErrorLevel",
    "ErrorContext",
    "ErrorMetrics",
    "ErrorRecoveryStrategy",
    "ErrorAggregator",
    "create_error_handling_middleware",
    "AppValidationError",
    "ResourceNotFoundError",
]
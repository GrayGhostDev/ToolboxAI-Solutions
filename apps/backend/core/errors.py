"""
Comprehensive Error Handling Middleware

Features:
- Structured error responses
- Error tracking and logging
- User-friendly error messages
- Development vs production modes
- Error recovery strategies
- Circuit breaker integration
- Error metrics collection
"""

import asyncio
import json
import logging
import sys
import traceback
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union

# Import Sentry for error tracking
try:
    from .sentry_config import sentry_manager
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

from fastapi import HTTPException, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ErrorLevel(Enum):
    """Error severity levels"""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification"""

    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RATE_LIMIT = "rate_limit"
    RESOURCE_NOT_FOUND = "resource_not_found"
    CONFLICT = "conflict"
    EXTERNAL_SERVICE = "external_service"
    DATABASE = "database"
    INTERNAL = "internal"
    BUSINESS_LOGIC = "business_logic"


class ErrorContext(BaseModel):
    """Context information for errors"""

    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    path: str
    method: str
    user_id: Optional[str] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    correlation_id: Optional[str] = None


class ErrorDetail(BaseModel):
    """Detailed error information"""

    code: str
    message: str
    field: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    suggestion: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standardized error response"""

    error: bool = True
    error_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status_code: int
    category: ErrorCategory
    message: str
    details: List[ErrorDetail] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    path: Optional[str] = None
    debug_info: Optional[Dict[str, Any]] = None


class ApplicationError(Exception):
    """Base application error"""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        category: ErrorCategory = ErrorCategory.INTERNAL,
        details: Optional[List[ErrorDetail]] = None,
        error_code: Optional[str] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.category = category
        self.details = details or []
        self.error_code = error_code or self.__class__.__name__
        super().__init__(message)


class AppValidationError(ApplicationError):
    """Validation error"""

    def __init__(self, message: str, details: Optional[List[ErrorDetail]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            category=ErrorCategory.VALIDATION,
            details=details,
        )


class AuthenticationError(ApplicationError):
    """Authentication error"""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            category=ErrorCategory.AUTHENTICATION,
        )


class AuthorizationError(ApplicationError):
    """Authorization error"""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            category=ErrorCategory.AUTHORIZATION,
        )


class ResourceNotFoundError(ApplicationError):
    """Resource not found error"""

    def __init__(self, resource: str, identifier: Optional[str] = None):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            category=ErrorCategory.RESOURCE_NOT_FOUND,
        )


class ConflictError(ApplicationError):
    """Resource conflict error"""

    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            category=ErrorCategory.CONFLICT,
        )


class ExternalServiceError(ApplicationError):
    """External service error"""

    def __init__(self, service: str, message: str):
        super().__init__(
            message=f"External service error ({service}): {message}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            category=ErrorCategory.EXTERNAL_SERVICE,
        )


class ErrorRecoveryStrategy:
    """Strategies for error recovery"""

    @staticmethod
    async def exponential_backoff(
        func: Callable,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
    ):
        """Retry with exponential backoff"""
        delay = initial_delay
        last_exception = None

        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(min(delay, max_delay))
                    delay *= exponential_base
                    logger.warning(
                        f"Retry attempt {attempt + 1}/{max_retries} after {delay}s delay"
                    )

        raise last_exception

    @staticmethod
    async def circuit_breaker(
        func: Callable,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_requests: int = 1,
    ):
        """Circuit breaker pattern for error recovery"""
        # This would integrate with the circuit breaker from security_middleware
        # Simplified implementation here
        try:
            return await func()
        except Exception as e:
            logger.error(f"Circuit breaker triggered: {e}")
            raise ExternalServiceError("Service", "Circuit breaker open")


class ErrorMetrics:
    """Collect and track error metrics"""

    def __init__(self):
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.error_rates: Dict[str, List[datetime]] = defaultdict(list)
        self.last_errors: Dict[str, Dict[str, Any]] = {}

    def record_error(self, error: Dict[str, Any], category: str):
        """Record an error occurrence"""
        self.error_counts[category] += 1
        self.error_rates[category].append(datetime.now(timezone.utc))
        self.last_errors[category] = error

        # Clean old entries (keep last hour)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
        self.error_rates[category] = [
            dt for dt in self.error_rates[category] if dt > cutoff
        ]

    def get_error_rate(self, category: str, window_minutes: int = 5) -> float:
        """Get error rate for a category"""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
        recent_errors = [dt for dt in self.error_rates[category] if dt > cutoff]
        return len(recent_errors) / window_minutes if window_minutes > 0 else 0

    def get_metrics(self) -> Dict[str, Any]:
        """Get error metrics summary"""
        return {
            "total_errors": sum(self.error_counts.values()),
            "errors_by_category": dict(self.error_counts),
            "error_rates": {
                category: {
                    "1min": self.get_error_rate(category, 1),
                    "5min": self.get_error_rate(category, 5),
                    "60min": self.get_error_rate(category, 60),
                }
                for category in self.error_counts.keys()
            },
        }


class ErrorHandler:
    """Central error handler"""

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.metrics = ErrorMetrics()
        self.error_mappers: Dict[type, Callable] = {}
        self._setup_default_mappers()

    def _setup_default_mappers(self):
        """Setup default error mappers"""
        self.register_error_mapper(AppValidationError, self._handle_validation_error)
        self.register_error_mapper(
            RequestValidationError, self._handle_request_validation_error
        )
        self.register_error_mapper(HTTPException, self._handle_http_exception)
        self.register_error_mapper(ApplicationError, self._handle_application_error)

    def register_error_mapper(self, error_type: type, mapper: Callable):
        """Register custom error mapper"""
        self.error_mappers[error_type] = mapper

    async def handle_error(self, request: Request, exc: Exception) -> Dict[str, Any]:
        """Handle an error and return standardized response (as dict)"""
        # Create error context
        context = ErrorContext(
            path=str(request.url.path),
            method=request.method,
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        # Get user ID if available
        if hasattr(request.state, "user"):
            context.user_id = getattr(request.state.user, "id", None)

        # Send error to Sentry with context
        if SENTRY_AVAILABLE and sentry_manager.initialized:
            # Set error context in Sentry
            sentry_manager.set_context("error_handling", {
                "request_path": context.path,
                "request_method": context.method,
                "client_ip": context.client_ip,
                "user_agent": context.user_agent,
                "user_id": context.user_id,
                "error_type": type(exc).__name__,
            })
            
            # Add breadcrumb for error occurrence
            sentry_manager.add_breadcrumb(
                message=f"Error occurred: {type(exc).__name__}",
                category="error",
                level="error",
                data={
                    "path": context.path,
                    "method": context.method,
                    "exception_message": str(exc)[:200],  # Limit message length
                }
            )
            
            # Capture the exception
            sentry_manager.capture_exception(exc)

        # Find appropriate handler
        for error_type, mapper in self.error_mappers.items():
            if isinstance(exc, error_type):
                error_dict = await mapper(exc, context)
                break
        else:
            # Default handler for unknown errors
            error_dict = await self._handle_unknown_error(exc, context)

        # Add debug info if in debug mode
        if self.debug:
            error_dict["debug_info"] = {
                "exception_type": type(exc).__name__,
                "traceback": traceback.format_exc(),
                "context": {
                    "request_id": context.request_id,
                    "timestamp": context.timestamp.isoformat(),
                    "path": context.path,
                    "method": context.method,
                    "user_id": context.user_id,
                    "client_ip": context.client_ip,
                    "user_agent": context.user_agent,
                    "correlation_id": context.correlation_id,
                },
            }

        # Record metrics
        self.metrics.record_error(error_dict, str(error_dict.get("category", "unknown")))

        # Log error
        self._log_error(error_dict, exc)

        return error_dict

    async def _handle_validation_error(
        self, exc: AppValidationError, context: ErrorContext
    ) -> Dict[str, Any]:
        """Handle validation errors"""
        return {
            "status_code": exc.status_code,
            "category": exc.category,
            "message": exc.message,
            "details": exc.details,
            "path": context.path,
        }
        return {
            "status_code": exc.status_code,
            "category": exc.category,
            "message": exc.message,
            "details": exc.details,
            "path": context.path,
        }

    async def _handle_request_validation_error(
        self, exc: RequestValidationError, context: ErrorContext
    ) -> Dict[str, Any]:
        """Handle FastAPI request validation errors"""
        details: List[Dict[str, Any]] = []
        for error in exc.errors():
            field_path = ".".join(str(loc) for loc in error.get("loc", []))
            details.append(
                {
                    "code": "validation_error",
                    "message": error.get("msg", "Validation failed"),
                    "field": field_path,
                    "context": {"type": error.get("type")},
                }
            )

        return {
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "category": ErrorCategory.VALIDATION,
            "message": "Request validation failed",
            "details": details,
            "path": context.path,
        }

    async def _handle_http_exception(
        self, exc: Union[HTTPException, StarletteHTTPException], context: ErrorContext
    ) -> Dict[str, Any]:
        """Handle HTTP exceptions"""
        # Map status code to category
        category = self._map_status_to_category(exc.status_code)

        return {
            "status_code": exc.status_code,
            "category": category,
            "message": exc.detail if hasattr(exc, "detail") else str(exc),
            "path": context.path,
        }

    async def _handle_application_error(
        self, exc: ApplicationError, context: ErrorContext
    ) -> Dict[str, Any]:
        """Handle application errors"""
        return {
            "status_code": exc.status_code,
            "category": exc.category,
            "message": exc.message,
            "details": exc.details,
            "path": context.path,
        }

    async def _handle_unknown_error(
        self, exc: Exception, context: ErrorContext
    ) -> Dict[str, Any]:
        """Handle unknown errors"""
        # Log full exception for unknown errors
        logger.exception(f"Unknown error occurred: {exc}")

        # Don't expose internal error details in production
        message = str(exc) if self.debug else "An internal error occurred"

        return {
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "category": ErrorCategory.INTERNAL,
            "message": message,
            "path": context.path,
        }

    def _map_status_to_category(self, status_code: int) -> ErrorCategory:
        """Map HTTP status code to error category"""
        if status_code == 401:
            return ErrorCategory.AUTHENTICATION
        elif status_code == 403:
            return ErrorCategory.AUTHORIZATION
        elif status_code == 404:
            return ErrorCategory.RESOURCE_NOT_FOUND
        elif status_code == 409:
            return ErrorCategory.CONFLICT
        elif status_code == 422:
            return ErrorCategory.VALIDATION
        elif status_code == 429:
            return ErrorCategory.RATE_LIMIT
        elif status_code >= 500:
            return ErrorCategory.INTERNAL
        else:
            return ErrorCategory.BUSINESS_LOGIC

    def _log_error(self, error_dict: Dict[str, Any], exc: Exception):
        """Log error with appropriate level"""
        status_code = int(error_dict.get("status_code", 500))
        msg = str(error_dict.get("message", ""))
        error_id = error_dict.get("error_id", "n/a")
        if status_code >= 500:
            logger.error(
                f"Error {error_id}: {msg}",
                exc_info=exc,
                extra={"error_response": error_dict},
            )
        elif status_code >= 400:
            logger.warning(
                f"Client error {error_id}: {msg}",
                extra={"error_response": error_dict},
            )
        else:
            logger.info(
                f"Error {error_id}: {msg}",
                extra={"error_response": error_dict},
            )


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive error handling"""

    def __init__(self, app, debug: bool = False):
        super().__init__(app)
        self.error_handler = ErrorHandler(debug=debug)

    async def dispatch(self, request: Request, call_next):
        """Process request and handle errors"""
        try:
            # Add request ID if not present
            if not hasattr(request.state, "request_id"):
                request.state.request_id = str(uuid.uuid4())

            response = await call_next(request)
            return response

        except Exception as exc:
            # Handle error
            error_dict = await self.error_handler.handle_error(request, exc)

            # Create JSON response
            headers = {
                "X-Error-ID": str(error_dict.get("error_id", "")),
                "X-Request-ID": getattr(request.state, "request_id", ""),
            }
            return JSONResponse(
                status_code=int(error_dict.get("status_code", 500)),
                content=jsonable_encoder(error_dict),
                headers=headers,
            )


class ErrorAggregator:
    """Aggregate and analyze errors for patterns"""

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.recent_errors: List[ErrorResponse] = []
        self.patterns: Dict[str, int] = defaultdict(int)

    def add_error(self, error: ErrorResponse):
        """Add error to aggregator"""
        self.recent_errors.append(error)

        # Keep window size
        if len(self.recent_errors) > self.window_size:
            self.recent_errors.pop(0)

        # Analyze patterns
        self._analyze_patterns()

    def _analyze_patterns(self):
        """Analyze error patterns"""
        self.patterns.clear()

        for error in self.recent_errors:
            # Count by category
            self.patterns[f"category_{error.category.value}"] += 1

            # Count by status code
            self.patterns[f"status_{error.status_code}"] += 1

            # Count by path
            if error.path:
                self.patterns[f"path_{error.path}"] += 1

    def get_insights(self) -> Dict[str, Any]:
        """Get error insights"""
        if not self.recent_errors:
            return {"message": "No recent errors"}

        return {
            "total_errors": len(self.recent_errors),
            "patterns": dict(self.patterns),
            "most_common_category": max(
                (k for k in self.patterns if k.startswith("category_")),
                key=lambda k: self.patterns[k],
                default=None,
            ),
            "most_common_status": max(
                (k for k in self.patterns if k.startswith("status_")),
                key=lambda k: self.patterns[k],
                default=None,
            ),
            "error_rate": len(self.recent_errors) / self.window_size,
        }


def create_error_handling_middleware(app, debug: bool = False) -> ErrorHandlingMiddleware:
    """Create error handling middleware"""
    return ErrorHandlingMiddleware(app, debug=debug)

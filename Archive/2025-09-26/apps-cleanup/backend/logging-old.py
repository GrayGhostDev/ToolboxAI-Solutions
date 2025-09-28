"""
Comprehensive Logging System with Correlation IDs

Provides structured logging with:
- Correlation ID tracking across requests
- Performance monitoring for slow operations
- Sensitive data masking
- Contextual logging with request metadata
- Integration with error handling and monitoring
"""

import contextvars
import functools
import json
import logging
import logging.handlers
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Union
from uuid import uuid4

from fastapi import Request, Response
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Context variable for correlation ID
correlation_id_context: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "correlation_id", default=None
)

# Context variable for request metadata
request_context: contextvars.ContextVar[Optional[Dict[str, Any]]] = contextvars.ContextVar(
    "request_context", default=None
)


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""
    
    SENSITIVE_FIELDS: Set[str] = {
        "password", "token", "secret", "api_key", "authorization",
        "cookie", "session", "csrf", "jwt", "bearer", "private_key",
        "access_token", "refresh_token", "client_secret"
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        # Build base log entry
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add correlation ID if available
        correlation_id = getattr(record, "correlation_id", None) or correlation_id_context.get()
        if correlation_id:
            log_entry["correlation_id"] = correlation_id
        
        # Add request context if available
        request_ctx = getattr(record, "request_context", None) or request_context.get()
        if request_ctx:
            log_entry["request"] = self._sanitize_data(request_ctx)
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_entry["extra"] = self._sanitize_data(record.extra_fields)
        
        # Add performance metrics if present
        if hasattr(record, "duration"):
            log_entry["performance"] = {
                "duration_ms": record.duration,
                "slow": record.duration > 1000  # Mark as slow if > 1 second
            }
        
        return json.dumps(log_entry, default=str)
    
    def _sanitize_data(self, data: Any) -> Any:
        """Recursively sanitize sensitive data"""
        if isinstance(data, dict):
            return {
                key: "[REDACTED]" if self._is_sensitive(key) else self._sanitize_data(value)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        elif isinstance(data, str) and len(data) > 1000:
            return f"{data[:1000]}... [truncated]"
        return data
    
    def _is_sensitive(self, key: str) -> bool:
        """Check if a key contains sensitive information"""
        key_lower = key.lower()
        return any(sensitive in key_lower for sensitive in self.SENSITIVE_FIELDS)


class LoggerAdapter(logging.LoggerAdapter):
    """Custom logger adapter for adding correlation ID and context"""
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Process log message to add correlation ID and context"""
        # Add correlation ID
        correlation_id = correlation_id_context.get()
        if correlation_id:
            kwargs.setdefault("extra", {})["correlation_id"] = correlation_id
        
        # Add request context
        request_ctx = request_context.get()
        if request_ctx:
            kwargs.setdefault("extra", {})["request_context"] = request_ctx
        
        # Add any extra fields passed directly
        if "extra_fields" in kwargs:
            kwargs.setdefault("extra", {})["extra_fields"] = kwargs.pop("extra_fields")
        
        return msg, kwargs


class LoggingManager:
    """Centralized logging management"""
    
    def __init__(self):
        self.loggers: Dict[str, LoggerAdapter] = {}
        self.root_logger: Optional[logging.Logger] = None
        self.log_dir: Optional[Path] = None
        self.initialized = False
    
    def initialize(
        self,
        log_level: str = "INFO",
        log_dir: Optional[str] = None,
        enable_file_logging: bool = True,
        enable_console_logging: bool = True,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ):
        """Initialize logging system"""
        # Set up root logger
        self.root_logger = logging.getLogger()
        self.root_logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear existing handlers
        self.root_logger.handlers.clear()
        
        # Create structured formatter
        formatter = StructuredFormatter()
        
        # Console handler
        if enable_console_logging:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.INFO)
            self.root_logger.addHandler(console_handler)
        
        # File handler with rotation
        if enable_file_logging and log_dir:
            self.log_dir = Path(log_dir)
            self.log_dir.mkdir(parents=True, exist_ok=True)
            
            # Main application log
            app_log_file = self.log_dir / "app.log"
            file_handler = logging.handlers.RotatingFileHandler(
                app_log_file,
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.DEBUG)
            self.root_logger.addHandler(file_handler)
            
            # Error log
            error_log_file = self.log_dir / "error.log"
            error_handler = logging.handlers.RotatingFileHandler(
                error_log_file,
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            error_handler.setFormatter(formatter)
            error_handler.setLevel(logging.ERROR)
            self.root_logger.addHandler(error_handler)
            
            # Performance log
            perf_log_file = self.log_dir / "performance.log"
            self.perf_handler = logging.handlers.RotatingFileHandler(
                perf_log_file,
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            self.perf_handler.setFormatter(formatter)
            self.perf_handler.setLevel(logging.INFO)
            
            # Create performance logger
            perf_logger = logging.getLogger("performance")
            perf_logger.addHandler(self.perf_handler)
            perf_logger.setLevel(logging.INFO)
            perf_logger.propagate = False
        
        self.initialized = True
    
    def get_logger(self, name: str) -> LoggerAdapter:
        """Get a logger adapter for a specific module"""
        if name not in self.loggers:
            base_logger = logging.getLogger(name)
            self.loggers[name] = LoggerAdapter(base_logger, {})
        return self.loggers[name]
    
    def set_correlation_id(self, correlation_id: Optional[str] = None) -> str:
        """Set correlation ID for current context"""
        if correlation_id is None:
            correlation_id = str(uuid4())
        correlation_id_context.set(correlation_id)
        return correlation_id
    
    def get_correlation_id(self) -> Optional[str]:
        """Get current correlation ID"""
        return correlation_id_context.get()
    
    def set_request_context(self, request: Request):
        """Set request context for logging"""
        context = {
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_host": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }
        request_context.set(context)
    
    def clear_context(self):
        """Clear correlation ID and request context"""
        correlation_id_context.set(None)
        request_context.set(None)
    
    def log_performance(
        self,
        operation: str,
        duration_ms: float,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log performance metrics"""
        perf_logger = logging.getLogger("performance")
        
        log_data = {
            "operation": operation,
            "duration_ms": duration_ms,
            "success": success,
            "correlation_id": self.get_correlation_id(),
        }
        
        if metadata:
            log_data["metadata"] = metadata
        
        level = logging.INFO if duration_ms < 1000 else logging.WARNING
        perf_logger.log(
            level,
            f"Performance: {operation} took {duration_ms:.2f}ms",
            extra={"extra_fields": log_data, "duration": duration_ms}
        )


# Global logging manager
logging_manager = LoggingManager()


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Middleware to inject correlation ID into requests"""
    
    async def dispatch(self, request: Request, call_next):
        # Get or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = str(uuid4())
        
        # Set correlation ID in context and request state
        logging_manager.set_correlation_id(correlation_id)
        request.state.correlation_id = correlation_id
        
        # Set request context
        logging_manager.set_request_context(request)
        
        # Get logger
        logger = logging_manager.get_logger(__name__)
        
        # Log request start
        start_time = time.time()
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra_fields={
                "method": request.method,
                "path": request.url.path,
                "correlation_id": correlation_id
            }
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log request completion
            logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                extra_fields={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "correlation_id": correlation_id
                }
            )
            
            # Log performance metrics
            logging_manager.log_performance(
                f"{request.method} {request.url.path}",
                duration_ms,
                success=response.status_code < 400,
                metadata={"status_code": response.status_code}
            )
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                exc_info=True,
                extra_fields={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                    "correlation_id": correlation_id,
                    "error": str(e)
                }
            )
            
            # Log performance metrics
            logging_manager.log_performance(
                f"{request.method} {request.url.path}",
                duration_ms,
                success=False,
                metadata={"error": str(e)}
            )
            
            raise
        finally:
            # Clear context
            logging_manager.clear_context()


def log_execution_time(threshold_ms: float = 100):
    """Decorator to log function execution time"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = logging_manager.get_logger(func.__module__)
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                if duration_ms > threshold_ms:
                    logger.warning(
                        f"Slow operation: {func.__name__} took {duration_ms:.2f}ms",
                        extra_fields={
                            "function": func.__name__,
                            "duration_ms": duration_ms,
                            "threshold_ms": threshold_ms
                        }
                    )
                else:
                    logger.debug(
                        f"Operation completed: {func.__name__} in {duration_ms:.2f}ms",
                        extra_fields={
                            "function": func.__name__,
                            "duration_ms": duration_ms
                        }
                    )
                
                # Log performance metrics
                logging_manager.log_performance(
                    f"function.{func.__name__}",
                    duration_ms,
                    success=True
                )
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                logger.error(
                    f"Operation failed: {func.__name__} after {duration_ms:.2f}ms",
                    exc_info=True,
                    extra_fields={
                        "function": func.__name__,
                        "duration_ms": duration_ms,
                        "error": str(e)
                    }
                )
                
                # Log performance metrics
                logging_manager.log_performance(
                    f"function.{func.__name__}",
                    duration_ms,
                    success=False,
                    metadata={"error": str(e)}
                )
                
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = logging_manager.get_logger(func.__module__)
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                if duration_ms > threshold_ms:
                    logger.warning(
                        f"Slow operation: {func.__name__} took {duration_ms:.2f}ms",
                        extra_fields={
                            "function": func.__name__,
                            "duration_ms": duration_ms,
                            "threshold_ms": threshold_ms
                        }
                    )
                else:
                    logger.debug(
                        f"Operation completed: {func.__name__} in {duration_ms:.2f}ms",
                        extra_fields={
                            "function": func.__name__,
                            "duration_ms": duration_ms
                        }
                    )
                
                # Log performance metrics
                logging_manager.log_performance(
                    f"function.{func.__name__}",
                    duration_ms,
                    success=True
                )
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                logger.error(
                    f"Operation failed: {func.__name__} after {duration_ms:.2f}ms",
                    exc_info=True,
                    extra_fields={
                        "function": func.__name__,
                        "duration_ms": duration_ms,
                        "error": str(e)
                    }
                )
                
                # Log performance metrics
                logging_manager.log_performance(
                    f"function.{func.__name__}",
                    duration_ms,
                    success=False,
                    metadata={"error": str(e)}
                )
                
                raise
        
        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def log_database_operation(operation_type: str):
    """Decorator to log database operations"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            logger = logging_manager.get_logger(func.__module__)
            start_time = time.time()
            
            logger.debug(
                f"Database operation started: {operation_type}",
                extra_fields={
                    "operation": operation_type,
                    "function": func.__name__
                }
            )
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                logger.info(
                    f"Database operation completed: {operation_type} in {duration_ms:.2f}ms",
                    extra_fields={
                        "operation": operation_type,
                        "function": func.__name__,
                        "duration_ms": duration_ms
                    }
                )
                
                # Log performance metrics
                logging_manager.log_performance(
                    f"db.{operation_type}",
                    duration_ms,
                    success=True
                )
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                logger.error(
                    f"Database operation failed: {operation_type} after {duration_ms:.2f}ms",
                    exc_info=True,
                    extra_fields={
                        "operation": operation_type,
                        "function": func.__name__,
                        "duration_ms": duration_ms,
                        "error": str(e)
                    }
                )
                
                # Log performance metrics
                logging_manager.log_performance(
                    f"db.{operation_type}",
                    duration_ms,
                    success=False,
                    metadata={"error": str(e)}
                )
                
                raise
        
        return wrapper
    
    return decorator


def log_external_api_call(service_name: str):
    """Decorator to log external API calls"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            logger = logging_manager.get_logger(func.__module__)
            start_time = time.time()
            
            logger.info(
                f"External API call started: {service_name}",
                extra_fields={
                    "service": service_name,
                    "function": func.__name__
                }
            )
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                logger.info(
                    f"External API call completed: {service_name} in {duration_ms:.2f}ms",
                    extra_fields={
                        "service": service_name,
                        "function": func.__name__,
                        "duration_ms": duration_ms
                    }
                )
                
                # Log performance metrics
                logging_manager.log_performance(
                    f"api.{service_name}",
                    duration_ms,
                    success=True
                )
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                logger.error(
                    f"External API call failed: {service_name} after {duration_ms:.2f}ms",
                    exc_info=True,
                    extra_fields={
                        "service": service_name,
                        "function": func.__name__,
                        "duration_ms": duration_ms,
                        "error": str(e)
                    }
                )
                
                # Log performance metrics
                logging_manager.log_performance(
                    f"api.{service_name}",
                    duration_ms,
                    success=False,
                    metadata={"error": str(e)}
                )
                
                raise
        
        return wrapper
    
    return decorator


# Utility functions for common logging patterns
def log_request(request: Request, logger: Optional[LoggerAdapter] = None):
    """Log incoming request details"""
    if logger is None:
        logger = logging_manager.get_logger(__name__)
    
    logger.info(
        f"Incoming request: {request.method} {request.url.path}",
        extra_fields={
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": dict(request.headers),
            "client": request.client.host if request.client else None
        }
    )


def log_response(response: Response, duration_ms: float, logger: Optional[LoggerAdapter] = None):
    """Log outgoing response details"""
    if logger is None:
        logger = logging_manager.get_logger(__name__)
    
    logger.info(
        f"Response sent: {response.status_code}",
        extra_fields={
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "headers": dict(response.headers)
        }
    )


def log_error(error: Exception, context: Optional[Dict[str, Any]] = None, logger: Optional[LoggerAdapter] = None):
    """Log error with context"""
    if logger is None:
        logger = logging_manager.get_logger(__name__)
    
    error_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
    }
    
    if context:
        error_data.update(context)
    
    logger.error(
        f"Error occurred: {type(error).__name__}: {str(error)}",
        exc_info=True,
        extra_fields=error_data
    )


def log_audit(
    action: str,
    user_id: Optional[str] = None,
    resource: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    logger: Optional[LoggerAdapter] = None
):
    """Log audit trail for sensitive operations"""
    if logger is None:
        logger = logging_manager.get_logger("audit")
    
    audit_data = {
        "action": action,
        "user_id": user_id,
        "resource": resource,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "correlation_id": logging_manager.get_correlation_id()
    }
    
    if details:
        audit_data["details"] = details
    
    logger.info(
        f"Audit: {action} by user {user_id or 'anonymous'} on {resource or 'system'}",
        extra_fields=audit_data
    )


# Initialize logging on module import with defaults
def initialize_logging(
    log_level: str = "INFO",
    log_dir: Optional[str] = "logs",
    **kwargs
):
    """Initialize the logging system with configuration"""
    logging_manager.initialize(
        log_level=log_level,
        log_dir=log_dir,
        **kwargs
    )


# Export main components
__all__ = [
    "logging_manager",
    "CorrelationIDMiddleware",
    "log_execution_time",
    "log_database_operation",
    "log_external_api_call",
    "log_request",
    "log_response",
    "log_error",
    "log_audit",
    "initialize_logging",
    "LoggerAdapter",
    "StructuredFormatter"
]
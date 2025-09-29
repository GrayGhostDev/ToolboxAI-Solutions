"""
Logging middleware and utilities for request tracking
"""

import logging
import time
import uuid
from typing import Callable, Any
from functools import wraps
from contextvars import ContextVar

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# Context variable for correlation ID
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")

logger = logging.getLogger(__name__)


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add correlation ID to each request for tracking
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or extract correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())

        # Set correlation ID in context
        correlation_id_var.set(correlation_id)

        # Add to request state
        request.state.correlation_id = correlation_id

        # Process request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Process-Time"] = str(process_time)

        # Log request completion
        logger.info(
            f"Request completed",
            extra={
                "correlation_id": correlation_id,
                "path": request.url.path,
                "method": request.method,
                "process_time": process_time,
                "status_code": response.status_code,
            },
        )

        return response


def log_error(error: Exception, context: dict = None) -> None:
    """
    Log an error with context

    Args:
        error: The exception to log
        context: Additional context information
    """
    context = context or {}
    correlation_id = correlation_id_var.get()

    logger.error(
        f"Error occurred: {str(error)}",
        extra={
            "correlation_id": correlation_id,
            "error_type": type(error).__name__,
            "context": context,
        },
        exc_info=True,
    )


def log_audit(action: str, user_id: str = None, details: dict = None) -> None:
    """
    Log an audit event

    Args:
        action: The action being performed
        user_id: ID of the user performing the action
        details: Additional details about the action
    """
    details = details or {}
    correlation_id = correlation_id_var.get()

    logger.info(
        f"Audit log: {action}",
        extra={
            "correlation_id": correlation_id,
            "action": action,
            "user_id": user_id,
            "details": details,
            "timestamp": time.time(),
        },
    )


def log_execution_time(func_name: str = None):
    """
    Decorator to log function execution time

    Args:
        func_name: Optional custom name for the function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            name = func_name or func.__name__
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time

                logger.debug(
                    f"Function {name} executed successfully",
                    extra={
                        "function": name,
                        "execution_time": execution_time,
                        "correlation_id": correlation_id_var.get(),
                    },
                )

                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"Function {name} failed",
                    extra={
                        "function": name,
                        "execution_time": execution_time,
                        "error": str(e),
                        "correlation_id": correlation_id_var.get(),
                    },
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            name = func_name or func.__name__
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                logger.debug(
                    f"Function {name} executed successfully",
                    extra={
                        "function": name,
                        "execution_time": execution_time,
                        "correlation_id": correlation_id_var.get(),
                    },
                )

                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"Function {name} failed",
                    extra={
                        "function": name,
                        "execution_time": execution_time,
                        "error": str(e),
                        "correlation_id": correlation_id_var.get(),
                    },
                )
                raise

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Import asyncio for the decorator
import asyncio

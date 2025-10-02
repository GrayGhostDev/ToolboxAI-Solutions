"""
Performance Monitoring Middleware

Automatically tracks request metrics, response times, and errors
for all API endpoints.

Features:
- Request/response time tracking
- Automatic metric collection
- Error rate monitoring
- Endpoint usage analytics
- Performance logging

Author: ToolBoxAI Team
Created: 2025-10-02
Version: 1.0.0
Standards: Python 3.12, FastAPI async
"""

import logging
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware for monitoring API performance.

    Tracks request duration, status codes, and records metrics
    for each endpoint.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and track performance metrics.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response: API response
        """
        # Record start time
        start_time = time.time()

        # Extract endpoint info
        endpoint = request.url.path
        method = request.method

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Record metrics
            self._record_metrics(
                endpoint=endpoint,
                method=method,
                duration=duration,
                status_code=response.status_code
            )

            # Add performance headers
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            response.headers["X-Request-ID"] = str(request.state.request_id) if hasattr(request.state, "request_id") else "unknown"

            # Log slow requests
            if duration > 1.0:
                logger.warning(
                    f"Slow request: {method} {endpoint} took {duration:.3f}s"
                )

            return response

        except Exception as e:
            # Calculate duration even on error
            duration = time.time() - start_time

            # Record error metrics
            self._record_metrics(
                endpoint=endpoint,
                method=method,
                duration=duration,
                status_code=500
            )

            logger.error(
                f"Request error: {method} {endpoint} - {str(e)}",
                exc_info=True
            )

            raise

    def _record_metrics(self, endpoint: str, method: str,
                       duration: float, status_code: int):
        """
        Record request metrics.

        Args:
            endpoint: Request endpoint
            method: HTTP method
            duration: Request duration in seconds
            status_code: HTTP status code
        """
        try:
            # Import here to avoid circular dependency
            from apps.backend.api.v1.endpoints.api_metrics import record_request_metric

            record_request_metric(endpoint, method, duration, status_code)

        except ImportError:
            # Metrics endpoint not available yet
            logger.debug("Metrics recording not available")
        except Exception as e:
            # Don't fail request if metrics recording fails
            logger.error(f"Failed to record metrics: {e}", exc_info=True)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware for adding unique request IDs.

    Adds a unique ID to each request for tracking and debugging.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Add request ID to request state.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response: API response
        """
        from uuid import uuid4

        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid4()))

        # Store in request state
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add to response headers
        response.headers["X-Request-ID"] = request_id

        return response

"""
Correlation ID Middleware - 2025 Implementation
Adds unique correlation IDs to all requests for distributed tracing and log aggregation.

Features:
- Automatic correlation ID generation
- Request ID propagation across services
- Enhanced logging with context
- OpenTelemetry integration ready
"""

import uuid
import logging
from typing import Callable
from datetime import datetime, timezone

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add correlation IDs to all requests.

    Supports:
    - X-Request-ID header (if provided by client)
    - X-Correlation-ID header (if provided by client)
    - Automatic UUID generation if not provided
    - Propagation to response headers
    - Integration with structured logging
    """

    def __init__(
        self,
        app: ASGIApp,
        header_name: str = "X-Correlation-ID",
        request_id_header: str = "X-Request-ID",
        generate_if_missing: bool = True,
        include_in_response: bool = True,
    ):
        super().__init__(app)
        self.header_name = header_name
        self.request_id_header = request_id_header
        self.generate_if_missing = generate_if_missing
        self.include_in_response = include_in_response

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with correlation ID tracking.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            Response with correlation ID headers
        """
        # Extract or generate correlation ID
        correlation_id = self._get_or_generate_correlation_id(request)

        # Extract or generate request ID
        request_id = self._get_or_generate_request_id(request)

        # Store IDs in request state for access by handlers
        request.state.correlation_id = correlation_id
        request.state.request_id = request_id
        request.state.request_start_time = datetime.now(timezone.utc)

        # Add to logging context (if using structlog or similar)
        logger_context = {
            "correlation_id": correlation_id,
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
        }

        # Log request with correlation ID
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra=logger_context,
        )

        try:
            # Process request
            response = await call_next(request)

            # Add correlation ID to response headers
            if self.include_in_response:
                response.headers[self.header_name] = correlation_id
                response.headers[self.request_id_header] = request_id

            # Calculate request duration
            if hasattr(request.state, "request_start_time"):
                duration = (
                    datetime.now(timezone.utc) - request.state.request_start_time
                ).total_seconds()
                response.headers["X-Request-Duration"] = f"{duration:.3f}s"

                # Log completion with duration
                logger.info(
                    f"Request completed: {request.method} {request.url.path} - "
                    f"Status: {response.status_code} - Duration: {duration:.3f}s",
                    extra={
                        **logger_context,
                        "status_code": response.status_code,
                        "duration_seconds": duration,
                    },
                )

            return response

        except Exception as exc:
            # Log error with correlation ID
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={**logger_context, "error": str(exc)},
                exc_info=True,
            )
            raise

    def _get_or_generate_correlation_id(self, request: Request) -> str:
        """
        Get correlation ID from request headers or generate new one.

        Priority:
        1. X-Correlation-ID header (from upstream service)
        2. X-Request-ID header (alternative)
        3. Generate new UUID v4

        Args:
            request: HTTP request

        Returns:
            Correlation ID string
        """
        # Check for correlation ID in headers
        correlation_id = request.headers.get(self.header_name)

        if correlation_id:
            logger.debug(f"Using existing correlation ID from header: {correlation_id}")
            return correlation_id

        # Fallback to request ID header
        correlation_id = request.headers.get(self.request_id_header)

        if correlation_id:
            logger.debug(f"Using request ID as correlation ID: {correlation_id}")
            return correlation_id

        # Generate new correlation ID
        if self.generate_if_missing:
            correlation_id = self._generate_id()
            logger.debug(f"Generated new correlation ID: {correlation_id}")
            return correlation_id

        # Should not reach here, but provide fallback
        return "unknown"

    def _get_or_generate_request_id(self, request: Request) -> str:
        """
        Get request ID from headers or generate new one.

        Args:
            request: HTTP request

        Returns:
            Request ID string
        """
        request_id = request.headers.get(self.request_id_header)

        if request_id:
            return request_id

        # Generate new request ID
        return self._generate_id()

    def _generate_id(self) -> str:
        """
        Generate a unique ID using UUID v4.

        Returns:
            UUID string
        """
        return str(uuid.uuid4())


class EnhancedCorrelationIDMiddleware(CorrelationIDMiddleware):
    """
    Enhanced correlation ID middleware with additional features:
    - Parent/child request tracking
    - Request chain depth tracking
    - Service name propagation
    - OpenTelemetry trace ID integration
    """

    def __init__(
        self,
        app: ASGIApp,
        service_name: str = "toolboxai-backend",
        max_chain_depth: int = 10,
        **kwargs,
    ):
        super().__init__(app, **kwargs)
        self.service_name = service_name
        self.max_chain_depth = max_chain_depth

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Enhanced dispatch with additional tracking."""

        # Extract parent correlation ID if exists
        parent_correlation_id = request.headers.get("X-Parent-Correlation-ID")

        # Extract chain depth
        chain_depth = self._get_chain_depth(request)

        # Check chain depth limit
        if chain_depth > self.max_chain_depth:
            logger.warning(
                f"Request chain depth exceeded limit: {chain_depth} > {self.max_chain_depth}",
                extra={"chain_depth": chain_depth, "limit": self.max_chain_depth},
            )

        # Store additional context
        request.state.parent_correlation_id = parent_correlation_id
        request.state.chain_depth = chain_depth
        request.state.service_name = self.service_name

        # Call parent dispatch
        response = await super().dispatch(request, call_next)

        # Add enhanced headers
        if parent_correlation_id:
            response.headers["X-Parent-Correlation-ID"] = parent_correlation_id
        response.headers["X-Service-Name"] = self.service_name
        response.headers["X-Chain-Depth"] = str(chain_depth)

        return response

    def _get_chain_depth(self, request: Request) -> int:
        """
        Get request chain depth from headers.

        Args:
            request: HTTP request

        Returns:
            Chain depth integer
        """
        depth_header = request.headers.get("X-Chain-Depth", "0")

        try:
            depth = int(depth_header)
            return depth + 1  # Increment for current request
        except ValueError:
            logger.warning(f"Invalid chain depth header: {depth_header}")
            return 1


def get_correlation_id_from_request(request: Request) -> str:
    """
    Helper function to get correlation ID from request state.

    Args:
        request: HTTP request

    Returns:
        Correlation ID string or "unknown" if not found
    """
    if hasattr(request.state, "correlation_id"):
        return request.state.correlation_id
    return "unknown"


def get_request_id_from_request(request: Request) -> str:
    """
    Helper function to get request ID from request state.

    Args:
        request: HTTP request

    Returns:
        Request ID string or "unknown" if not found
    """
    if hasattr(request.state, "request_id"):
        return request.state.request_id
    return "unknown"


# Export
__all__ = [
    "CorrelationIDMiddleware",
    "EnhancedCorrelationIDMiddleware",
    "get_correlation_id_from_request",
    "get_request_id_from_request",
]

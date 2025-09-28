"""
Resilience Middleware for FastAPI

Integrates circuit breakers, retries, and fault tolerance patterns
into the FastAPI application middleware stack.
"""

import time
import logging
from typing import Callable, Optional, Dict, Any
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from apps.backend.core.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    get_circuit_breaker,
    get_all_circuit_breakers_status,
)

logger = logging.getLogger(__name__)


class ResilienceMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds resilience patterns to FastAPI endpoints
    """

    def __init__(self, app, config: Optional[Dict[str, Any]] = None):
        super().__init__(app)
        self.config = config or {}
        self._setup_circuit_breakers()

    def _setup_circuit_breakers(self):
        """Initialize circuit breakers for different service types"""

        # Database circuit breaker
        self.db_breaker = get_circuit_breaker(
            "database",
            CircuitBreakerConfig(
                failure_threshold=5,
                failure_rate_threshold=0.5,
                reset_timeout=30.0,
                timeout=5.0,
                expected_exceptions=(Exception,),
                excluded_exceptions=(HTTPException,),
            ),
        )

        # External API circuit breaker (OpenAI, etc.)
        self.api_breaker = get_circuit_breaker(
            "external_api",
            CircuitBreakerConfig(
                failure_threshold=3,
                failure_rate_threshold=0.6,
                reset_timeout=60.0,
                timeout=30.0,
            ),
        )

        # Redis circuit breaker
        self.cache_breaker = get_circuit_breaker(
            "redis",
            CircuitBreakerConfig(
                failure_threshold=10,
                failure_rate_threshold=0.7,
                reset_timeout=15.0,
                timeout=2.0,
            ),
        )

        # Agent service circuit breaker
        self.agent_breaker = get_circuit_breaker(
            "agent_service",
            CircuitBreakerConfig(
                failure_threshold=5,
                failure_rate_threshold=0.5,
                reset_timeout=45.0,
                timeout=60.0,  # Agents may take longer
            ),
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with resilience patterns
        """
        start_time = time.time()

        # Identify service type from path
        path = request.url.path
        circuit_breaker = self._get_circuit_breaker_for_path(path)

        try:
            # If a circuit breaker applies to this path, use it
            if circuit_breaker:
                response = await self._call_with_circuit_breaker(
                    circuit_breaker, call_next, request
                )
            else:
                response = await call_next(request)

            # Track successful responses
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except CircuitBreakerError as e:
            logger.warning(f"Circuit breaker open for {e.circuit_name}: {e}")
            return self._create_fallback_response(e)

        except Exception as e:
            logger.error(f"Unhandled error in resilience middleware: {e}")
            process_time = time.time() - start_time
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "message": "Service temporarily unavailable",
                    "process_time": process_time,
                },
            )

    def _get_circuit_breaker_for_path(self, path: str) -> Optional[CircuitBreaker]:
        """Determine which circuit breaker to use based on path"""

        # Database operations
        if any(p in path for p in ["/users", "/content", "/lessons", "/quiz"]):
            return self.db_breaker

        # External API calls
        if any(p in path for p in ["/ai/", "/generate", "/openai", "/gpt"]):
            return self.api_breaker

        # Cache operations
        if any(p in path for p in ["/cache", "/session"]):
            return self.cache_breaker

        # Agent operations
        if any(p in path for p in ["/agents", "/orchestrator", "/swarm"]):
            return self.agent_breaker

        return None

    async def _call_with_circuit_breaker(
        self, circuit_breaker: CircuitBreaker, call_next: Callable, request: Request
    ) -> Response:
        """Execute request with circuit breaker protection"""

        async def wrapped_call():
            return await call_next(request)

        return await circuit_breaker.call(wrapped_call)

    def _create_fallback_response(self, error: CircuitBreakerError) -> Response:
        """Create fallback response when circuit is open"""

        fallback_messages = {
            "database": "Database service is currently unavailable",
            "external_api": "External API service is temporarily unavailable",
            "redis": "Cache service is temporarily unavailable",
            "agent_service": "AI agent service is currently overloaded",
        }

        message = fallback_messages.get(error.circuit_name, "Service is temporarily unavailable")

        return JSONResponse(
            status_code=503,
            content={
                "error": "Service Unavailable",
                "message": message,
                "retry_after": error.wait_time,
                "circuit_breaker": error.circuit_name,
            },
            headers={
                "Retry-After": str(int(error.wait_time)),
                "X-Circuit-Breaker": error.circuit_name,
            },
        )


class RetryMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds automatic retry logic for transient failures
    """

    def __init__(
        self, app, max_retries: int = 3, retry_delay: float = 1.0, exponential_backoff: bool = True
    ):
        super().__init__(app)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.exponential_backoff = exponential_backoff

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with retry logic for transient failures
        """
        retries = 0
        delay = self.retry_delay

        while retries <= self.max_retries:
            try:
                response = await call_next(request)

                # Retry on specific status codes
                if response.status_code in [502, 503, 504] and retries < self.max_retries:
                    retries += 1
                    logger.warning(
                        f"Retrying request {request.url.path} "
                        f"(attempt {retries}/{self.max_retries})"
                    )
                    await asyncio.sleep(delay)

                    if self.exponential_backoff:
                        delay *= 2  # Exponential backoff

                    continue

                return response

            except Exception as e:
                if retries < self.max_retries:
                    retries += 1
                    logger.warning(
                        f"Retrying request {request.url.path} after error: {e} "
                        f"(attempt {retries}/{self.max_retries})"
                    )
                    await asyncio.sleep(delay)

                    if self.exponential_backoff:
                        delay *= 2

                    continue

                raise

        # Max retries exceeded
        return JSONResponse(
            status_code=503,
            content={
                "error": "Service Unavailable",
                "message": "Maximum retry attempts exceeded",
                "retries": self.max_retries,
            },
        )


class BulkheadMiddleware(BaseHTTPMiddleware):
    """
    Middleware that implements the Bulkhead pattern to isolate resources
    and prevent resource exhaustion
    """

    def __init__(self, app, max_concurrent_requests: int = 100, max_queue_size: int = 50):
        super().__init__(app)
        self.max_concurrent_requests = max_concurrent_requests
        self.max_queue_size = max_queue_size
        self.current_requests = 0
        self.queue_size = 0
        self._lock = asyncio.Lock()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with bulkhead isolation
        """
        async with self._lock:
            if self.current_requests >= self.max_concurrent_requests:
                if self.queue_size >= self.max_queue_size:
                    # Reject request if queue is full
                    return JSONResponse(
                        status_code=503,
                        content={
                            "error": "Service Unavailable",
                            "message": "Server is at capacity",
                            "retry_after": 5,
                        },
                        headers={"Retry-After": "5"},
                    )
                self.queue_size += 1

            self.current_requests += 1

        try:
            response = await call_next(request)
            return response
        finally:
            async with self._lock:
                self.current_requests -= 1
                if self.queue_size > 0:
                    self.queue_size -= 1


# Import asyncio only if needed
try:
    import asyncio
except ImportError:
    logger.warning("asyncio not available, some features may be limited")


def setup_resilience_middleware(app):
    """
    Configure all resilience middleware for the FastAPI app
    """

    # Add circuit breaker middleware
    app.add_middleware(ResilienceMiddleware)

    # Add retry middleware for transient failures
    app.add_middleware(RetryMiddleware, max_retries=3, retry_delay=1.0, exponential_backoff=True)

    # Add bulkhead pattern for resource isolation
    app.add_middleware(BulkheadMiddleware, max_concurrent_requests=100, max_queue_size=50)

    logger.info("Resilience middleware configured successfully")


async def get_resilience_status() -> Dict[str, Any]:
    """Get status of all resilience components"""
    return {"circuit_breakers": await get_all_circuit_breakers_status(), "timestamp": time.time()}

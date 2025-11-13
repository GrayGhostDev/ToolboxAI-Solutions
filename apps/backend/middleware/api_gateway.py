"""
API Gateway Middleware
Central request routing, versioning, and circuit breaker implementation
Integrates with Supabase Edge Functions for global distribution
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from collections.abc import Callable
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from apps.backend.core.security.rate_limit_manager import RateLimitManager
from apps.backend.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class APIVersion(str, Enum):
    """Supported API versions"""

    V1 = "v1"
    V2 = "v2"
    V3 = "v3"
    LATEST = "v3"
    DEPRECATED = ["v1"]  # List of deprecated versions


class CircuitState(str, Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failures exceeded threshold, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class RouteConfig:
    """Route configuration for API versioning and features"""

    def __init__(self):
        self.routes: dict[str, dict[str, Any]] = {}
        self.version_mappings: dict[str, str] = {}
        self.deprecated_routes: set[str] = set()
        self._initialize_routes()

    def _initialize_routes(self):
        """Initialize route configurations"""
        # Version mappings for backward compatibility
        self.version_mappings = {
            "/api/v1/users": "/api/v3/users",
            "/api/v1/content": "/api/v3/content",
            "/api/v2/auth": "/api/v3/auth",
        }

        # Route-specific configurations
        self.routes = {
            "/api/*/health": {"bypass_auth": True, "rate_limit": None, "cache": False},
            "/api/*/webhooks/*": {
                "bypass_auth": True,
                "rate_limit": "webhook",
                "validate_signature": True,
            },
            "/api/*/roblox/*": {
                "rate_limit": "roblox",
                "require_api_key": True,
                "circuit_breaker": True,
            },
            "/api/*/ai/*": {"rate_limit": "ai", "cost_tracking": True, "circuit_breaker": True},
        }

    def get_route_config(self, path: str) -> dict[str, Any]:
        """Get configuration for a specific route"""
        for pattern, config in self.routes.items():
            if self._matches_pattern(path, pattern):
                return config
        return {}

    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if path matches pattern with wildcards"""
        import re

        regex_pattern = pattern.replace("*", ".*")
        return bool(re.match(regex_pattern, path))


class CircuitBreaker:
    """Circuit breaker implementation for fault tolerance"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time: datetime | None = None
        self.state = CircuitState.CLOSED
        self._lock = asyncio.Lock()

        # Metrics
        self.total_requests = 0
        self.failed_requests = 0
        self.successful_requests = 0
        self.circuit_opens = 0

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        async with self._lock:
            self.total_requests += 1

            # Check circuit state
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                else:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Service temporarily unavailable (circuit open)",
                    )

            try:
                # Execute the function
                result = (
                    await func(*args, **kwargs)
                    if asyncio.iscoroutinefunction(func)
                    else func(*args, **kwargs)
                )

                # Success - update state
                if self.state == CircuitState.HALF_OPEN:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    logger.info(f"Circuit breaker reset for {func.__name__}")

                self.successful_requests += 1
                return result

            except self.expected_exception as e:
                self.failed_requests += 1
                self._record_failure()

                # Open circuit if threshold exceeded
                if self.failure_count >= self.failure_threshold:
                    self.state = CircuitState.OPEN
                    self.circuit_opens += 1
                    logger.warning(
                        f"Circuit breaker opened for {func.__name__} after {self.failure_count} failures"
                    )

                raise e

    def _record_failure(self):
        """Record a failure"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if not self.last_failure_time:
            return True
        return datetime.utcnow() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)

    def get_metrics(self) -> dict[str, Any]:
        """Get circuit breaker metrics"""
        return {
            "state": self.state,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "failure_count": self.failure_count,
            "circuit_opens": self.circuit_opens,
            "success_rate": self.successful_requests / max(self.total_requests, 1),
        }


class RequestRouter:
    """Route requests based on version and configuration"""

    def __init__(self):
        self.route_config = RouteConfig()
        self.version_stats = defaultdict(int)
        self.route_cache = {}

    def route_request(self, request: Request) -> tuple[str, dict[str, Any]]:
        """Route request to appropriate handler with config"""
        path = request.url.path

        # Check cache
        cache_key = f"{request.method}:{path}"
        if cache_key in self.route_cache:
            return self.route_cache[cache_key]

        # Extract version from path
        version = self._extract_version(path)
        if version:
            self.version_stats[version] += 1

        # Check for deprecated version
        if version in APIVersion.DEPRECATED:
            logger.warning(f"Deprecated API version used: {version} for path {path}")

        # Apply version mapping if needed
        mapped_path = self.route_config.version_mappings.get(path, path)

        # Get route configuration
        config = self.route_config.get_route_config(mapped_path)

        # Cache result
        self.route_cache[cache_key] = (mapped_path, config)

        return mapped_path, config

    def _extract_version(self, path: str) -> str | None:
        """Extract API version from path"""
        parts = path.split("/")
        for part in parts:
            if part in [v.value for v in APIVersion]:
                return part
        return None

    def get_version_stats(self) -> dict[str, int]:
        """Get API version usage statistics"""
        return dict(self.version_stats)


class APIGatewayMiddleware(BaseHTTPMiddleware):
    """
    API Gateway Middleware

    Features:
    - Request routing and versioning
    - Circuit breaker for fault tolerance
    - Integration with rate limiting
    - Metrics collection
    - Supabase Edge Function hooks
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.router = RequestRouter()
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.rate_limiter = RateLimitManager()
        self.metrics = defaultdict(int)
        self.request_times = deque(maxlen=1000)
        self.supabase = SupabaseService() if hasattr(SupabaseService, "__init__") else None

        # Initialize circuit breakers for critical services
        self._initialize_circuit_breakers()

        logger.info("API Gateway Middleware initialized")

    def _initialize_circuit_breakers(self):
        """Initialize circuit breakers for critical services"""
        # Circuit breaker for Roblox API
        self.circuit_breakers["roblox"] = CircuitBreaker(
            failure_threshold=5, recovery_timeout=60, expected_exception=Exception
        )

        # Circuit breaker for AI services
        self.circuit_breakers["ai"] = CircuitBreaker(
            failure_threshold=3, recovery_timeout=120, expected_exception=Exception
        )

        # Circuit breaker for external webhooks
        self.circuit_breakers["webhook"] = CircuitBreaker(
            failure_threshold=10, recovery_timeout=30, expected_exception=Exception
        )

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request through gateway"""
        start_time = time.time()

        try:
            # Route request
            routed_path, config = self.router.route_request(request)

            # Check if route requires circuit breaker
            if config.get("circuit_breaker"):
                service_name = self._get_service_name(routed_path)
                if service_name in self.circuit_breakers:
                    breaker = self.circuit_breakers[service_name]
                    try:
                        response = await breaker.call(call_next, request)
                    except Exception as e:
                        logger.error(f"Circuit breaker triggered for {service_name}: {e}")
                        return JSONResponse(
                            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            content={
                                "error": "Service temporarily unavailable",
                                "service": service_name,
                                "retry_after": breaker.recovery_timeout,
                            },
                        )
                else:
                    response = await call_next(request)
            else:
                response = await call_next(request)

            # Record metrics
            self._record_metrics(request, response, time.time() - start_time)

            # Add gateway headers
            response.headers["X-API-Version"] = self._get_response_version(request)
            response.headers["X-Gateway-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"

            # Log deprecated version usage
            if self._is_deprecated_version(request):
                response.headers["X-API-Deprecated"] = "true"
                response.headers["X-API-Sunset"] = "2025-12-31"

            return response

        except Exception as e:
            logger.error(f"Gateway error: {e}")
            self.metrics["errors"] += 1

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal gateway error",
                    "request_id": request.headers.get("X-Request-ID", "unknown"),
                },
            )

    def _get_service_name(self, path: str) -> str:
        """Extract service name from path"""
        if "roblox" in path.lower():
            return "roblox"
        elif "ai" in path.lower() or "agent" in path.lower():
            return "ai"
        elif "webhook" in path.lower():
            return "webhook"
        return "default"

    def _get_response_version(self, request: Request) -> str:
        """Get API version for response"""
        path = request.url.path
        version = self.router._extract_version(path)
        return version or APIVersion.LATEST.value

    def _is_deprecated_version(self, request: Request) -> bool:
        """Check if request uses deprecated API version"""
        version = self.router._extract_version(request.url.path)
        return version in APIVersion.DEPRECATED

    def _record_metrics(self, request: Request, response: Response, duration: float):
        """Record request metrics"""
        self.metrics["total_requests"] += 1
        self.metrics[f"status_{response.status_code}"] += 1
        self.metrics[f"method_{request.method}"] += 1

        # Record timing
        self.request_times.append(duration)

        # Track version usage
        version = self.router._extract_version(request.url.path)
        if version:
            self.metrics[f"version_{version}"] += 1

        # Log to Supabase Analytics if available
        if self.supabase and hasattr(self.supabase, "track_metric"):
            asyncio.create_task(self._log_to_supabase(request, response, duration))

    async def _log_to_supabase(self, request: Request, response: Response, duration: float):
        """Log metrics to Supabase Analytics"""
        try:
            await self.supabase.track_metric(
                {
                    "type": "api_request",
                    "path": request.url.path,
                    "method": request.method,
                    "status": response.status_code,
                    "duration_ms": duration * 1000,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        except Exception as e:
            logger.debug(f"Failed to log metrics to Supabase: {e}")

    def get_metrics(self) -> dict[str, Any]:
        """Get gateway metrics"""
        avg_time = sum(self.request_times) / len(self.request_times) if self.request_times else 0

        return {
            "total_requests": self.metrics["total_requests"],
            "errors": self.metrics["errors"],
            "average_response_time_ms": avg_time * 1000,
            "version_stats": self.router.get_version_stats(),
            "circuit_breakers": {
                name: breaker.get_metrics() for name, breaker in self.circuit_breakers.items()
            },
            "status_codes": {k: v for k, v in self.metrics.items() if k.startswith("status_")},
        }


# Utility functions for edge function integration
async def sync_with_edge_function(
    function_name: str, payload: dict[str, Any], timeout: int = 5
) -> dict[str, Any] | None:
    """
    Sync with Supabase Edge Function

    Args:
        function_name: Name of the edge function
        payload: Data to send
        timeout: Request timeout in seconds

    Returns:
        Response from edge function or None
    """
    try:
        # This would integrate with Supabase Edge Functions
        # For now, return None as placeholder
        logger.debug(f"Would sync with edge function: {function_name}")
        return None
    except Exception as e:
        logger.error(f"Edge function sync failed: {e}")
        return None


# Export middleware
__all__ = [
    "APIGatewayMiddleware",
    "CircuitBreaker",
    "RequestRouter",
    "APIVersion",
    "sync_with_edge_function",
]

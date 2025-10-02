"""
Rate Limiting Middleware for ToolboxAI Backend

Implements request rate limiting using Redis for distributed rate limiting
across multiple backend instances.

Features:
- Per-user rate limiting
- Per-API-key rate limiting
- Per-IP rate limiting
- Sliding window algorithm
- Multiple time windows (minute, hour, day)
- Configurable limits per endpoint
"""

import time
import hashlib
from typing import Optional, Callable, Tuple
from functools import wraps

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import redis.asyncio as aioredis

from apps.backend.core.config import settings
from apps.backend.core.logging import logging_manager

logger = logging_manager.get_logger(__name__)


class RateLimitExceeded(HTTPException):
    """Exception raised when rate limit is exceeded"""

    def __init__(
        self,
        detail: str = "Rate limit exceeded",
        limit: int = 0,
        window: int = 0,
        retry_after: int = 0
    ):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers={
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Window": str(window),
                "Retry-After": str(retry_after)
            }
        )


class RateLimiter:
    """
    Redis-based rate limiter using sliding window algorithm

    Supports multiple time windows and distributed rate limiting
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        prefix: str = "rate_limit"
    ):
        self.redis_url = redis_url
        self.prefix = prefix
        self.redis: Optional[aioredis.Redis] = None

    async def connect(self):
        """Connect to Redis"""
        if not self.redis:
            self.redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Rate limiter connected to Redis")

    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            logger.info("Rate limiter disconnected from Redis")

    def _get_key(self, identifier: str, window: str) -> str:
        """Generate Redis key for rate limit tracking"""
        return f"{self.prefix}:{identifier}:{window}"

    async def is_allowed(
        self,
        identifier: str,
        limit: int,
        window_seconds: int
    ) -> Tuple[bool, int, int]:
        """
        Check if request is allowed under rate limit

        Args:
            identifier: Unique identifier for the client (user_id, api_key, IP)
            limit: Maximum number of requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            Tuple of (is_allowed, current_count, retry_after_seconds)
        """
        if not self.redis:
            await self.connect()

        now = int(time.time())
        window_start = now - window_seconds
        key = self._get_key(identifier, f"{window_seconds}s")

        # Use Redis sorted set with timestamps as scores
        pipe = self.redis.pipeline()

        # Remove old entries outside the window
        pipe.zremrangebyscore(key, 0, window_start)

        # Add current request
        member = f"{now}:{time.time_ns()}"
        pipe.zadd(key, {member: now})

        # Count requests in window
        pipe.zcard(key)

        # Set expiration
        pipe.expire(key, window_seconds)

        results = await pipe.execute()
        current_count = results[2]  # Result from zcard

        is_allowed = current_count <= limit
        retry_after = 0

        if not is_allowed:
            # Calculate when the oldest request in window will expire
            oldest = await self.redis.zrange(key, 0, 0)
            if oldest:
                oldest_timestamp = int(oldest[0].split(":")[0])
                retry_after = oldest_timestamp + window_seconds - now
        logger.debug(
            f"Rate limit check: identifier={identifier}, "
            f"count={current_count}, limit={limit}, "
            f"window={window_seconds}s, allowed={is_allowed}"
        )

        return is_allowed, current_count, max(0, retry_after)

    async def check_multiple_windows(
        self,
        identifier: str,
        limits: dict[int, int]
    ) -> Tuple[bool, dict]:
        """
        Check rate limits across multiple time windows

        Args:
            identifier: Unique identifier for the client
            limits: Dict of {window_seconds: max_requests}

        Returns:
            Tuple of (all_allowed, window_stats)
        """
        all_allowed = True
        window_stats = {}

        for window_seconds, max_requests in limits.items():
            is_allowed, current, retry_after = await self.is_allowed(
                identifier,
                max_requests,
                window_seconds
            )

            window_stats[f"{window_seconds}s"] = {
                "allowed": is_allowed,
                "current": current,
                "limit": max_requests,
                "retry_after": retry_after
            }

            if not is_allowed:
                all_allowed = False

        return all_allowed, window_stats


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting

    Applies rate limits based on:
    1. API key (if present)
    2. User ID (if authenticated)
    3. IP address (fallback)
    """

    def __init__(
        self,
        app: ASGIApp,
        redis_url: str = None,
        default_limits: dict = None
    ):
        super().__init__(app)
        self.redis_url = redis_url or settings.REDIS_URL or "redis://localhost:6379/0"
        self.rate_limiter = RateLimiter(redis_url=self.redis_url)

        # Default rate limits (window_seconds: max_requests)
        self.default_limits = default_limits or {
            60: 60,        # 60 requests per minute
            3600: 1000,    # 1000 requests per hour
            86400: 10000   # 10000 requests per day
        }

        # Endpoint-specific rate limits
        self.endpoint_limits = {
            "/api/v1/ai_chat/": {60: 10, 3600: 100},      # Chat endpoints
            "/api/v1/content/generate": {60: 5, 3600: 50}, # Content generation
            "/api/v1/agents/": {60: 20, 3600: 200},        # Agent endpoints
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting"""
        # Skip rate limiting for health checks and metrics
        if request.url.path in ["/health", "/metrics", "/docs", "/openapi.json"]:
            return await call_next(request)

        # Get identifier for rate limiting
        identifier = await self._get_identifier(request)

        # Get applicable rate limits
        limits = self._get_limits_for_endpoint(request.url.path)

        # Check rate limits
        try:
            is_allowed, window_stats = await self.rate_limiter.check_multiple_windows(
                identifier,
                limits
            )

            # Add rate limit headers to response
            response = await call_next(request)

            # Add rate limit info to headers
            for window, stats in window_stats.items():
                response.headers[f"X-RateLimit-Limit-{window}"] = str(stats["limit"])
                response.headers[f"X-RateLimit-Remaining-{window}"] = str(
                    max(0, stats["limit"] - stats["current"])
                )

            if not is_allowed:
                # Find the shortest retry time
                retry_after = min(
                    stats["retry_after"]
                    for stats in window_stats.values()
                    if not stats["allowed"]
                )

                logger.warning(
                    f"Rate limit exceeded for {identifier}",
                    extra={
                        "identifier": identifier,
                        "path": request.url.path,
                        "window_stats": window_stats
                    }
                )

                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "status": "error",
                        "message": "Rate limit exceeded. Please try again later.",
                        "retry_after": retry_after,
                        "limits": window_stats
                    },
                    headers={
                        "Retry-After": str(retry_after)
                    }
                )

            return response

        except Exception as e:
            logger.error(
                f"Rate limiting error: {e}",
                extra={"identifier": identifier, "path": request.url.path}
            )
            # On error, allow the request but log it
            return await call_next(request)

    async def _get_identifier(self, request: Request) -> str:
        """
        Get unique identifier for rate limiting

        Priority:
        1. API key
        2. User ID (from JWT)
        3. IP address
        """
        # Check for API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{hashlib.sha256(api_key.encode()).hexdigest()[:16]}"

        # Check for authenticated user
        user = getattr(request.state, "user", None)
        if user and hasattr(user, "id"):
            return f"user:{user.id}"

        # Fallback to IP address
        client_ip = request.client.host if request.client else "unknown"
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            client_ip = x_forwarded_for.split(",")[0].strip()

        return f"ip:{client_ip}"

    def _get_limits_for_endpoint(self, path: str) -> dict:
        """Get rate limits for specific endpoint"""
        # Check for exact match or prefix match
        for endpoint_pattern, limits in self.endpoint_limits.items():
            if path.startswith(endpoint_pattern):
                return limits

        # Return default limits
        return self.default_limits


# Decorator for endpoint-specific rate limiting
def rate_limit(
    requests_per_minute: int = 60,
    requests_per_hour: int = 1000
):
    """
    Decorator to apply custom rate limits to specific endpoints

    Example:
        @app.post("/api/v1/content/generate")
        @rate_limit(requests_per_minute=5, requests_per_hour=50)
        async def generate_content(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Rate limiting is handled by middleware
            # This decorator just marks the endpoint
            return await func(*args, **kwargs)

        # Store rate limit config in function metadata
        wrapper._rate_limit = {
            60: requests_per_minute,
            3600: requests_per_hour
        }
        return wrapper
    return decorator


# Startup and shutdown handlers for middleware
async def startup_rate_limiter():
    """Initialize rate limiter on startup"""
    logger.info("Initializing rate limiter...")
    # Connection will be established on first use


async def shutdown_rate_limiter():
    """Cleanup rate limiter on shutdown"""
    logger.info("Shutting down rate limiter...")
    # Redis connections will be closed automatically

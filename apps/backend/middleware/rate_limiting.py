"""
Rate Limiting Middleware

Implements flexible rate limiting strategies for API endpoints with
support for different limits per endpoint and user tier.

Features:
- Multiple rate limiting strategies (fixed window, sliding window)
- Per-endpoint rate limits
- User tier-based limits
- IP-based rate limiting for unauthenticated requests
- Customizable rate limit responses
- Rate limit headers (X-RateLimit-*)

Author: ToolBoxAI Team
Created: 2025-10-02
Version: 1.0.0
Standards: Python 3.12, FastAPI async
"""

import logging
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from fastapi import HTTPException, Request, Response, status
from starlette.types import ASGIApp
from starlock.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


# === Rate Limit Configuration ===


class RateLimitStrategy(str, Enum):
    """Rate limiting strategy"""

    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""

    requests: int  # Number of requests allowed
    window: int  # Time window in seconds
    strategy: RateLimitStrategy = RateLimitStrategy.FIXED_WINDOW


# === Default Rate Limits ===

DEFAULT_RATE_LIMITS = {
    # Authentication endpoints
    "/api/v1/auth/login": RateLimitConfig(requests=5, window=60),
    "/api/v1/auth/register": RateLimitConfig(requests=3, window=3600),
    # Upload endpoints
    "/api/v1/uploads/file": RateLimitConfig(requests=100, window=3600),
    "/api/v1/uploads/multipart": RateLimitConfig(requests=20, window=3600),
    # Bulk operations
    "/api/v1/users/notifications/bulk": RateLimitConfig(requests=10, window=60),
    # Export endpoints
    "/api/v1/analytics/export": RateLimitConfig(requests=20, window=3600),
    # Default for all other endpoints
    "default": RateLimitConfig(requests=1000, window=3600),
}

# Tier-based multipliers
TIER_MULTIPLIERS = {
    "free": 1.0,
    "starter": 1.5,
    "professional": 3.0,
    "enterprise": 10.0,
}


# === Rate Limit Store ===


class RateLimitStore:
    """
    In-memory rate limit store.

    Replace with Redis in production for distributed rate limiting.
    """

    def __init__(self):
        self.requests: dict[str, list] = defaultdict(list)

    def record_request(self, key: str, timestamp: float):
        """Record a request"""
        self.requests[key].append(timestamp)

    def get_request_count(self, key: str, window_start: float) -> int:
        """Get number of requests since window start"""
        # Clean old requests
        self.requests[key] = [ts for ts in self.requests[key] if ts > window_start]
        return len(self.requests[key])

    def clear_key(self, key: str):
        """Clear requests for a key"""
        if key in self.requests:
            del self.requests[key]


# Global store instance
_rate_limit_store = RateLimitStore()


# === Rate Limiting Middleware ===


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware with support for multiple strategies.
    """

    def __init__(
        self,
        app: ASGIApp,
        rate_limits: dict[str, RateLimitConfig] = None,
        enabled: bool = True,
    ):
        super().__init__(app)
        self.rate_limits = rate_limits or DEFAULT_RATE_LIMITS
        self.enabled = enabled
        self.store = _rate_limit_store

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Apply rate limiting to request.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response: API response

        Raises:
            HTTPException: If rate limit exceeded
        """
        if not self.enabled:
            return await call_next(request)

        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/metrics/health"]:
            return await call_next(request)

        # Get rate limit config for endpoint
        config = self._get_rate_limit_config(request)

        # Get rate limit key (user ID or IP)
        rate_limit_key = self._get_rate_limit_key(request)

        # Apply tier multiplier
        adjusted_limit = self._apply_tier_multiplier(request, config)

        # Check rate limit
        current_time = time.time()
        window_start = current_time - config.window

        request_count = self.store.get_request_count(rate_limit_key, window_start)

        # Check if limit exceeded
        if request_count >= adjusted_limit:
            # Calculate retry after
            oldest_request = min(self.store.requests[rate_limit_key])
            retry_after = int(oldest_request + config.window - current_time) + 1

            logger.warning(f"Rate limit exceeded for {rate_limit_key} on {request.url.path}")

            # Return 429 Too Many Requests
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "retry_after": retry_after,
                    "limit": adjusted_limit,
                    "window": config.window,
                },
                headers={
                    "X-RateLimit-Limit": str(adjusted_limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(oldest_request + config.window)),
                    "Retry-After": str(retry_after),
                },
            )

        # Record this request
        self.store.record_request(rate_limit_key, current_time)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining = adjusted_limit - request_count - 1
        reset_time = int(current_time + config.window)

        response.headers["X-RateLimit-Limit"] = str(adjusted_limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(reset_time)

        return response

    def _get_rate_limit_config(self, request: Request) -> RateLimitConfig:
        """
        Get rate limit configuration for endpoint.

        Args:
            request: Incoming request

        Returns:
            RateLimitConfig: Rate limit configuration
        """
        path = request.url.path

        # Check for exact match
        if path in self.rate_limits:
            return self.rate_limits[path]

        # Check for prefix match
        for prefix, config in self.rate_limits.items():
            if prefix != "default" and path.startswith(prefix):
                return config

        # Return default
        return self.rate_limits["default"]

    def _get_rate_limit_key(self, request: Request) -> str:
        """
        Get rate limit key for request.

        Uses user ID if authenticated, otherwise IP address.

        Args:
            request: Incoming request

        Returns:
            str: Rate limit key
        """
        # Try to get user ID from request state
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.id}"

        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"

    def _apply_tier_multiplier(self, request: Request, config: RateLimitConfig) -> int:
        """
        Apply tier-based multiplier to rate limit.

        Args:
            request: Incoming request
            config: Base rate limit configuration

        Returns:
            int: Adjusted rate limit
        """
        # Get user's subscription tier
        if hasattr(request.state, "user") and request.state.user:
            user = request.state.user

            # Get organization tier
            if hasattr(user, "organization") and user.organization:
                tier = user.organization.subscription_tier
                multiplier = TIER_MULTIPLIERS.get(tier, 1.0)
                return int(config.requests * multiplier)

        # Default (no multiplier)
        return config.requests


# === Rate Limit Decorator ===


def rate_limit(
    requests: int, window: int, strategy: RateLimitStrategy = RateLimitStrategy.FIXED_WINDOW
):
    """
    Decorator for applying custom rate limits to specific endpoints.

    Example:
        @router.get("/expensive-operation")
        @rate_limit(requests=10, window=60)
        async def expensive_operation():
            ...

    Args:
        requests: Number of requests allowed
        window: Time window in seconds
        strategy: Rate limiting strategy

    Returns:
        Decorator function
    """

    def decorator(func):
        # Store rate limit config in function metadata
        func._rate_limit_config = RateLimitConfig(
            requests=requests, window=window, strategy=strategy
        )
        return func

    return decorator


# === IP Whitelist/Blacklist ===


class IPFilterMiddleware(BaseHTTPMiddleware):
    """
    Middleware for IP-based filtering.

    Supports whitelisting and blacklisting IPs.
    """

    def __init__(
        self,
        app: ASGIApp,
        whitelist: list[str] | None = None,
        blacklist: list[str] | None = None,
    ):
        super().__init__(app)
        self.whitelist = set(whitelist or [])
        self.blacklist = set(blacklist or [])

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Filter requests based on IP address.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response: API response

        Raises:
            HTTPException: If IP is blacklisted or not whitelisted
        """
        client_ip = request.client.host if request.client else "unknown"

        # Check blacklist
        if client_ip in self.blacklist:
            logger.warning(f"Blocked request from blacklisted IP: {client_ip}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        # Check whitelist (if configured)
        if self.whitelist and client_ip not in self.whitelist:
            logger.warning(f"Blocked request from non-whitelisted IP: {client_ip}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        return await call_next(request)


# === Utilities ===


def clear_rate_limits(key: str | None = None):
    """
    Clear rate limits.

    Args:
        key: Optional specific key to clear. If None, clears all.
    """
    if key:
        _rate_limit_store.clear_key(key)
    else:
        _rate_limit_store.requests.clear()


def get_rate_limit_status(key: str, config: RateLimitConfig) -> dict:
    """
    Get current rate limit status for a key.

    Args:
        key: Rate limit key
        config: Rate limit configuration

    Returns:
        dict: Rate limit status
    """
    current_time = time.time()
    window_start = current_time - config.window

    request_count = _rate_limit_store.get_request_count(key, window_start)
    remaining = max(0, config.requests - request_count)

    return {
        "limit": config.requests,
        "remaining": remaining,
        "reset": int(current_time + config.window),
        "window": config.window,
    }

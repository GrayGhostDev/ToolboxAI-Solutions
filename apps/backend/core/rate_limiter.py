"""
Distributed Rate Limiting with Redis

Implements advanced rate limiting strategies including sliding windows,
token buckets, and user-specific limits for production environments.
"""

import time
import hashlib
import logging
from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass, field
from enum import Enum
import json
import asyncio
from datetime import datetime, timedelta

import redis.asyncio as aioredis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class RateLimitStrategy(Enum):
    """Rate limiting algorithms"""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"
    SLIDING_LOG = "sliding_log"


class RateLimitScope(Enum):
    """Scope of rate limiting"""
    GLOBAL = "global"
    IP = "ip"
    USER = "user"
    API_KEY = "api_key"
    ENDPOINT = "endpoint"
    COMBINED = "combined"


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting behavior"""

    # Basic limits
    requests_per_second: int = 10
    requests_per_minute: int = 100
    requests_per_hour: int = 1000
    requests_per_day: int = 10000

    # Burst handling
    burst_size: int = 20
    burst_duration: int = 10  # seconds

    # Strategy
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    scope: RateLimitScope = RateLimitScope.IP

    # Token bucket specific
    token_bucket_capacity: int = 100
    token_bucket_refill_rate: float = 10.0  # tokens per second

    # User tiers
    enable_user_tiers: bool = True
    user_tier_multipliers: Dict[str, float] = field(default_factory=lambda: {
        "free": 1.0,
        "basic": 2.0,
        "premium": 5.0,
        "enterprise": 10.0
    })

    # Endpoint-specific limits
    endpoint_limits: Dict[str, Dict[str, int]] = field(default_factory=lambda: {
        "/auth/login": {"requests_per_minute": 5},
        "/auth/register": {"requests_per_hour": 10},
        "/api/v1/generate": {"requests_per_minute": 20},
        "/api/v1/agents": {"requests_per_minute": 30},
        "/api/v1/upload": {"requests_per_hour": 100},
    })

    # Redis settings
    redis_key_prefix: str = "rate_limit"
    redis_ttl: int = 3600  # 1 hour

    # Response headers
    include_headers: bool = True
    header_prefix: str = "X-RateLimit"

    # Penalties
    enable_progressive_penalties: bool = True
    penalty_duration: int = 300  # 5 minutes
    penalty_multiplier: float = 2.0


@dataclass
class RateLimitResult:
    """Result of rate limit check"""
    allowed: bool
    limit: int
    remaining: int
    reset_at: int
    retry_after: Optional[int] = None
    reason: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)


class RateLimiter:
    """
    Distributed rate limiter using Redis for high-performance
    rate limiting across multiple servers.
    """

    def __init__(
        self,
        redis_client: aioredis.Redis,
        config: Optional[RateLimitConfig] = None
    ):
        self.redis = redis_client
        self.config = config or RateLimitConfig()
        self._scripts = {}
        self._initialize_lua_scripts()

    def _initialize_lua_scripts(self):
        """Initialize Lua scripts for atomic Redis operations"""

        # Sliding window rate limiting script
        self._scripts["sliding_window"] = """
        local key = KEYS[1]
        local now = tonumber(ARGV[1])
        local window = tonumber(ARGV[2])
        local limit = tonumber(ARGV[3])

        local clearBefore = now - window

        -- Remove old entries
        redis.call('zremrangebyscore', key, 0, clearBefore)

        -- Count current entries
        local current = redis.call('zcard', key)

        if current < limit then
            -- Add new entry
            redis.call('zadd', key, now, now)
            redis.call('expire', key, window)
            return {1, limit - current - 1, now + window}
        else
            -- Get oldest entry for retry calculation
            local oldest = redis.call('zrange', key, 0, 0, 'WITHSCORES')
            local resetAt = oldest[2] and (oldest[2] + window) or (now + window)
            return {0, 0, resetAt}
        end
        """

        # Token bucket script
        self._scripts["token_bucket"] = """
        local key = KEYS[1]
        local capacity = tonumber(ARGV[1])
        local refill_rate = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])
        local requested = tonumber(ARGV[4])

        local bucket = redis.call('hmget', key, 'tokens', 'last_refill')
        local tokens = tonumber(bucket[1]) or capacity
        local last_refill = tonumber(bucket[2]) or now

        -- Calculate tokens to add
        local time_passed = now - last_refill
        local tokens_to_add = time_passed * refill_rate
        tokens = math.min(capacity, tokens + tokens_to_add)

        if tokens >= requested then
            -- Consume tokens
            tokens = tokens - requested
            redis.call('hmset', key, 'tokens', tokens, 'last_refill', now)
            redis.call('expire', key, 3600)
            return {1, math.floor(tokens), 0}
        else
            -- Calculate retry time
            local tokens_needed = requested - tokens
            local retry_after = tokens_needed / refill_rate
            return {0, math.floor(tokens), math.ceil(retry_after)}
        end
        """

        # Sliding log script for precise rate limiting
        self._scripts["sliding_log"] = """
        local key = KEYS[1]
        local now = tonumber(ARGV[1])
        local window = tonumber(ARGV[2])
        local limit = tonumber(ARGV[3])
        local request_id = ARGV[4]

        local clearBefore = now - window

        -- Clean old entries
        redis.call('zremrangebyscore', key, '-inf', clearBefore)

        -- Count requests in window
        local count = redis.call('zcard', key)

        if count < limit then
            -- Add request with unique ID
            redis.call('zadd', key, now, request_id)
            redis.call('expire', key, window)
            return {1, limit - count - 1, now + window}
        else
            -- Find when we can retry
            local oldest = redis.call('zrange', key, 0, 0, 'WITHSCORES')
            local resetAt = oldest[2] and (oldest[2] + window) or (now + window)
            return {0, 0, math.ceil(resetAt)}
        end
        """

    async def check_rate_limit(
        self,
        identifier: str,
        endpoint: Optional[str] = None,
        user_tier: str = "free",
        custom_limit: Optional[int] = None
    ) -> RateLimitResult:
        """
        Check if request is within rate limits

        Args:
            identifier: Unique identifier (IP, user ID, etc.)
            endpoint: API endpoint being accessed
            user_tier: User subscription tier
            custom_limit: Override default limit

        Returns:
            RateLimitResult with decision and metadata
        """
        try:
            # Determine effective limit
            limit = self._get_effective_limit(endpoint, user_tier, custom_limit)

            # Get current timestamp
            now = time.time()

            # Choose strategy
            if self.config.strategy == RateLimitStrategy.SLIDING_WINDOW:
                result = await self._check_sliding_window(
                    identifier, endpoint, limit, now
                )
            elif self.config.strategy == RateLimitStrategy.TOKEN_BUCKET:
                result = await self._check_token_bucket(
                    identifier, endpoint, limit, now
                )
            elif self.config.strategy == RateLimitStrategy.SLIDING_LOG:
                result = await self._check_sliding_log(
                    identifier, endpoint, limit, now
                )
            else:
                result = await self._check_fixed_window(
                    identifier, endpoint, limit, now
                )

            # Apply progressive penalties if enabled
            if not result.allowed and self.config.enable_progressive_penalties:
                result = await self._apply_penalty(identifier, result)

            # Add headers if enabled
            if self.config.include_headers:
                result.headers = self._generate_headers(result)

            return result

        except RedisError as e:
            logger.error(f"Redis error in rate limiter: {e}")
            # Fail open - allow request if Redis is down
            return RateLimitResult(
                allowed=True,
                limit=limit if 'limit' in locals() else 100,
                remaining=1,
                reset_at=int(now + 60) if 'now' in locals() else int(time.time() + 60),
                reason="Rate limit check failed, allowing request"
            )

    async def _check_sliding_window(
        self,
        identifier: str,
        endpoint: Optional[str],
        limit: int,
        now: float
    ) -> RateLimitResult:
        """Check rate limit using sliding window algorithm"""

        key = self._generate_key(identifier, endpoint, "sliding")
        window = 60  # 1 minute window

        # Execute Lua script atomically
        script = self.redis.register_script(self._scripts["sliding_window"])
        result = await script(
            keys=[key],
            args=[now, window, limit]
        )

        allowed, remaining, reset_at = result

        return RateLimitResult(
            allowed=bool(allowed),
            limit=limit,
            remaining=int(remaining),
            reset_at=int(reset_at),
            retry_after=int(reset_at - now) if not allowed else None
        )

    async def _check_token_bucket(
        self,
        identifier: str,
        endpoint: Optional[str],
        limit: int,
        now: float
    ) -> RateLimitResult:
        """Check rate limit using token bucket algorithm"""

        key = self._generate_key(identifier, endpoint, "token")
        capacity = self.config.token_bucket_capacity
        refill_rate = self.config.token_bucket_refill_rate

        script = self.redis.register_script(self._scripts["token_bucket"])
        result = await script(
            keys=[key],
            args=[capacity, refill_rate, now, 1]  # Request 1 token
        )

        allowed, remaining, retry_after = result

        return RateLimitResult(
            allowed=bool(allowed),
            limit=capacity,
            remaining=int(remaining),
            reset_at=int(now + (capacity - remaining) / refill_rate),
            retry_after=int(retry_after) if retry_after > 0 else None
        )

    async def _check_sliding_log(
        self,
        identifier: str,
        endpoint: Optional[str],
        limit: int,
        now: float
    ) -> RateLimitResult:
        """Check rate limit using sliding log algorithm (most precise)"""

        key = self._generate_key(identifier, endpoint, "log")
        window = 60  # 1 minute window
        request_id = f"{now}:{hashlib.md5(str(now).encode()).hexdigest()[:8]}"

        script = self.redis.register_script(self._scripts["sliding_log"])
        result = await script(
            keys=[key],
            args=[now, window, limit, request_id]
        )

        allowed, remaining, reset_at = result

        return RateLimitResult(
            allowed=bool(allowed),
            limit=limit,
            remaining=int(remaining),
            reset_at=int(reset_at),
            retry_after=int(reset_at - now) if not allowed else None
        )

    async def _check_fixed_window(
        self,
        identifier: str,
        endpoint: Optional[str],
        limit: int,
        now: float
    ) -> RateLimitResult:
        """Check rate limit using fixed window algorithm (simplest)"""

        # Calculate window boundaries
        window = 60  # 1 minute window
        window_start = int(now // window) * window

        key = self._generate_key(identifier, endpoint, f"fixed:{window_start}")

        # Increment counter
        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, window)
        results = await pipe.execute()

        current_count = results[0]
        allowed = current_count <= limit

        return RateLimitResult(
            allowed=allowed,
            limit=limit,
            remaining=max(0, limit - current_count),
            reset_at=window_start + window,
            retry_after=window_start + window - int(now) if not allowed else None
        )

    async def _apply_penalty(
        self,
        identifier: str,
        result: RateLimitResult
    ) -> RateLimitResult:
        """Apply progressive penalties for repeated violations"""

        penalty_key = f"{self.config.redis_key_prefix}:penalty:{identifier}"

        # Check current penalty level
        penalty_level = await self.redis.get(penalty_key)
        penalty_level = int(penalty_level) if penalty_level else 0

        # Increase penalty
        penalty_level += 1
        await self.redis.setex(
            penalty_key,
            self.config.penalty_duration,
            penalty_level
        )

        # Apply penalty multiplier
        penalty_factor = self.config.penalty_multiplier ** (penalty_level - 1)
        result.retry_after = int(
            (result.retry_after or 60) * penalty_factor
        )

        result.reason = f"Progressive penalty level {penalty_level}"

        return result

    def _get_effective_limit(
        self,
        endpoint: Optional[str],
        user_tier: str,
        custom_limit: Optional[int]
    ) -> int:
        """Calculate effective rate limit based on various factors"""

        # Start with base limit
        base_limit = self.config.requests_per_minute

        # Check for custom limit
        if custom_limit:
            base_limit = custom_limit

        # Check endpoint-specific limits
        elif endpoint and endpoint in self.config.endpoint_limits:
            endpoint_config = self.config.endpoint_limits[endpoint]
            base_limit = endpoint_config.get(
                "requests_per_minute",
                base_limit
            )

        # Apply user tier multiplier
        if self.config.enable_user_tiers and user_tier in self.config.user_tier_multipliers:
            multiplier = self.config.user_tier_multipliers[user_tier]
            base_limit = int(base_limit * multiplier)

        return base_limit

    def _generate_key(
        self,
        identifier: str,
        endpoint: Optional[str],
        suffix: str = ""
    ) -> str:
        """Generate Redis key for rate limiting"""

        parts = [self.config.redis_key_prefix]

        if endpoint:
            # Clean endpoint for key
            clean_endpoint = endpoint.replace("/", ":").strip(":")
            parts.append(clean_endpoint)

        parts.append(identifier)

        if suffix:
            parts.append(suffix)

        return ":".join(parts)

    def _generate_headers(self, result: RateLimitResult) -> Dict[str, str]:
        """Generate rate limit headers for response"""

        headers = {
            f"{self.config.header_prefix}-Limit": str(result.limit),
            f"{self.config.header_prefix}-Remaining": str(result.remaining),
            f"{self.config.header_prefix}-Reset": str(result.reset_at),
        }

        if result.retry_after:
            headers["Retry-After"] = str(result.retry_after)

        return headers

    async def reset_limits(self, identifier: str, endpoint: Optional[str] = None):
        """Reset rate limits for an identifier"""

        pattern = self._generate_key(identifier, endpoint, "*")

        # Find all keys matching pattern
        keys = []
        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)

        # Delete all matching keys
        if keys:
            await self.redis.delete(*keys)

        logger.info(f"Reset rate limits for {identifier}: {len(keys)} keys deleted")

    async def get_usage_stats(
        self,
        identifier: str,
        endpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get usage statistics for an identifier"""

        stats = {
            "identifier": identifier,
            "endpoint": endpoint,
            "current_usage": {},
            "limits": {}
        }

        # Check various time windows
        windows = [
            ("minute", 60),
            ("hour", 3600),
            ("day", 86400)
        ]

        for window_name, window_seconds in windows:
            key = self._generate_key(
                identifier,
                endpoint,
                f"stats:{window_name}"
            )

            count = await self.redis.get(key)
            stats["current_usage"][window_name] = int(count) if count else 0

            # Get configured limit for this window
            limit_key = f"requests_per_{window_name}"
            if hasattr(self.config, limit_key):
                stats["limits"][window_name] = getattr(self.config, limit_key)

        return stats


class RateLimitMiddleware:
    """FastAPI middleware for rate limiting"""

    def __init__(
        self,
        redis_client: aioredis.Redis,
        config: Optional[RateLimitConfig] = None
    ):
        self.limiter = RateLimiter(redis_client, config)

    async def __call__(self, request, call_next):
        """Process request with rate limiting"""

        # Extract identifier based on scope
        identifier = self._get_identifier(request)

        # Extract endpoint
        endpoint = request.url.path

        # Get user tier (from JWT or session)
        user_tier = self._get_user_tier(request)

        # Check rate limit
        result = await self.limiter.check_rate_limit(
            identifier,
            endpoint,
            user_tier
        )

        if not result.allowed:
            # Return 429 Too Many Requests
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": result.reason or "Too many requests",
                    "retry_after": result.retry_after
                },
                headers=result.headers
            )

        # Add rate limit headers to response
        response = await call_next(request)
        for header, value in result.headers.items():
            response.headers[header] = value

        return response

    def _get_identifier(self, request) -> str:
        """Extract identifier from request"""
        # Try to get authenticated user ID first
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.id}"

        # Fall back to IP address
        client = request.client
        if client:
            return f"ip:{client.host}"

        return "unknown"

    def _get_user_tier(self, request) -> str:
        """Extract user tier from request"""
        if hasattr(request.state, "user") and request.state.user:
            return getattr(request.state.user, "tier", "free")
        return "free"


# Export main components
__all__ = [
    'RateLimiter',
    'RateLimitConfig',
    'RateLimitMiddleware',
    'RateLimitResult',
    'RateLimitStrategy',
    'RateLimitScope'
]
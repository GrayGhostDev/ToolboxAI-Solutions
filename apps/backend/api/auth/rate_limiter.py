"""
Auth-Specific Rate Limiter
Phase 3 Implementation - Adaptive rate limiting for authentication endpoints
"""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RateLimitType(Enum):
    """Types of rate limits"""

    LOGIN = "login"
    MFA = "mfa"
    OAUTH = "oauth"
    PASSWORD_RESET = "password_reset"
    REGISTRATION = "registration"
    TOKEN_REFRESH = "token_refresh"
    API_KEY = "api_key"


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""

    requests_per_minute: int = 10
    requests_per_hour: int = 100
    requests_per_day: int = 1000
    burst_size: int = 5
    lockout_duration: int = 900  # 15 minutes
    progressive_delay: bool = True
    adaptive_threshold: bool = True
    ip_based: bool = True
    user_based: bool = True


class RateLimitException(Exception):
    """Rate limit exceeded exception"""

    def __init__(self, message: str, retry_after: int = None):
        super().__init__(message)
        self.retry_after = retry_after


class AuthRateLimiter:
    """
    Advanced rate limiter for authentication endpoints

    Features:
    - Multiple time windows (minute, hour, day)
    - Progressive delays for repeated failures
    - Adaptive thresholds based on patterns
    - IP and user-based limiting
    - Distributed rate limiting via Redis
    """

    # Default configurations per endpoint type
    DEFAULT_CONFIGS = {
        RateLimitType.LOGIN: RateLimitConfig(
            requests_per_minute=5,
            requests_per_hour=20,
            requests_per_day=100,
            burst_size=3,
            lockout_duration=1800,  # 30 minutes
            progressive_delay=True,
            adaptive_threshold=True,
        ),
        RateLimitType.MFA: RateLimitConfig(
            requests_per_minute=3,
            requests_per_hour=15,
            requests_per_day=50,
            burst_size=2,
            lockout_duration=3600,  # 1 hour
            progressive_delay=True,
        ),
        RateLimitType.OAUTH: RateLimitConfig(
            requests_per_minute=10, requests_per_hour=100, requests_per_day=1000, burst_size=5
        ),
        RateLimitType.PASSWORD_RESET: RateLimitConfig(
            requests_per_minute=2,
            requests_per_hour=5,
            requests_per_day=10,
            lockout_duration=7200,  # 2 hours
            progressive_delay=True,
        ),
        RateLimitType.REGISTRATION: RateLimitConfig(
            requests_per_minute=2, requests_per_hour=10, requests_per_day=20
        ),
        RateLimitType.TOKEN_REFRESH: RateLimitConfig(
            requests_per_minute=10, requests_per_hour=200, requests_per_day=2000
        ),
        RateLimitType.API_KEY: RateLimitConfig(
            requests_per_minute=100, requests_per_hour=5000, requests_per_day=50000
        ),
    }

    def __init__(
        self, redis_client: redis.Redis, configs: Dict[RateLimitType, RateLimitConfig] = None
    ):
        self.redis = redis_client
        self.configs = configs or self.DEFAULT_CONFIGS
        self.suspicious_ips: set = set()
        self.trusted_ips: set = set()

    async def check_rate_limit(
        self,
        limit_type: RateLimitType,
        identifier: str,
        ip_address: str | None = None,
        user_id: str | None = None,
    ) -> Tuple[bool, int | None]:
        """
        Check if request is within rate limits

        Returns:
            (allowed, retry_after_seconds)
        """

        config = self.configs.get(limit_type, self.DEFAULT_CONFIGS[RateLimitType.LOGIN])

        # Check if IP is trusted
        if ip_address and ip_address in self.trusted_ips:
            return True, None

        # Check if IP is locked out
        if ip_address and await self._is_locked_out(ip_address):
            lockout_remaining = await self._get_lockout_remaining(ip_address)
            return False, lockout_remaining

        # Check multiple time windows
        checks = []

        if config.ip_based and ip_address:
            checks.extend(
                [
                    self._check_window(
                        f"rate:{limit_type.value}:ip:{ip_address}:min",
                        60,
                        config.requests_per_minute,
                    ),
                    self._check_window(
                        f"rate:{limit_type.value}:ip:{ip_address}:hour",
                        3600,
                        config.requests_per_hour,
                    ),
                    self._check_window(
                        f"rate:{limit_type.value}:ip:{ip_address}:day",
                        86400,
                        config.requests_per_day,
                    ),
                ]
            )

        if config.user_based and user_id:
            checks.extend(
                [
                    self._check_window(
                        f"rate:{limit_type.value}:user:{user_id}:min",
                        60,
                        config.requests_per_minute,
                    ),
                    self._check_window(
                        f"rate:{limit_type.value}:user:{user_id}:hour",
                        3600,
                        config.requests_per_hour,
                    ),
                    self._check_window(
                        f"rate:{limit_type.value}:user:{user_id}:day",
                        86400,
                        config.requests_per_day,
                    ),
                ]
            )

        # Execute all checks
        results = await asyncio.gather(*checks)

        # Check if any limit exceeded
        for allowed, retry_after in results:
            if not allowed:
                # Apply progressive delay if enabled
                if config.progressive_delay:
                    retry_after = await self._apply_progressive_delay(identifier, retry_after)

                # Check for suspicious patterns
                if ip_address:
                    await self._check_suspicious_activity(ip_address, limit_type)

                return False, retry_after

        # Check burst limit
        burst_allowed = await self._check_burst(identifier, config.burst_size)
        if not burst_allowed:
            return False, 1  # Retry after 1 second for burst

        return True, None

    async def _check_window(
        self, key: str, window_seconds: int, max_requests: int
    ) -> Tuple[bool, int | None]:
        """Check rate limit for a specific time window"""

        pipeline = self.redis.pipeline()
        now = time.time()

        # Remove old entries
        pipeline.zremrangebyscore(key, 0, now - window_seconds)

        # Count current requests
        pipeline.zcard(key)

        # Add current request
        pipeline.zadd(key, {str(now): now})

        # Set expiry
        pipeline.expire(key, window_seconds)

        results = await pipeline.execute()
        current_count = results[1]

        if current_count >= max_requests:
            # Get oldest request time to calculate retry_after
            oldest = await self.redis.zrange(key, 0, 0, withscores=True)
            if oldest:
                oldest_time = oldest[0][1]
                retry_after = int(window_seconds - (now - oldest_time)) + 1
                return False, retry_after
            return False, window_seconds

        return True, None

    async def _check_burst(self, identifier: str, burst_size: int) -> bool:
        """Check burst limit using token bucket algorithm"""

        key = f"burst:{identifier}"
        now = time.time()

        # Get current tokens
        data = await self.redis.get(key)
        if data:
            tokens_data = json.loads(data)
            tokens = tokens_data["tokens"]
            last_update = tokens_data["last_update"]

            # Replenish tokens (1 token per second)
            elapsed = now - last_update
            tokens = min(burst_size, tokens + elapsed)
        else:
            tokens = burst_size
            last_update = now

        # Check if token available
        if tokens < 1:
            return False

        # Consume token
        tokens -= 1

        # Save state
        await self.redis.setex(
            key, 300, json.dumps({"tokens": tokens, "last_update": now})  # 5 minutes TTL
        )

        return True

    async def _is_locked_out(self, ip_address: str) -> bool:
        """Check if IP is locked out"""

        lockout_key = f"lockout:ip:{ip_address}"
        return await self.redis.exists(lockout_key) > 0

    async def _get_lockout_remaining(self, ip_address: str) -> int:
        """Get remaining lockout time in seconds"""

        lockout_key = f"lockout:ip:{ip_address}"
        ttl = await self.redis.ttl(lockout_key)
        return max(0, ttl)

    async def _apply_progressive_delay(self, identifier: str, base_retry_after: int) -> int:
        """Apply progressive delay based on failure count"""

        failure_key = f"failures:{identifier}"

        # Increment failure count
        failures = await self.redis.incr(failure_key)
        await self.redis.expire(failure_key, 3600)  # Reset after 1 hour

        # Calculate progressive delay (exponential backoff)
        delay_multiplier = min(2 ** (failures - 1), 32)  # Cap at 32x

        return base_retry_after * delay_multiplier

    async def _check_suspicious_activity(self, ip_address: str, limit_type: RateLimitType):
        """Check for suspicious patterns and apply lockout if needed"""

        # Track failed attempts
        pattern_key = f"pattern:{ip_address}"

        # Get recent activity
        recent_activity = await self.redis.get(pattern_key)
        if recent_activity:
            activity = json.loads(recent_activity)
        else:
            activity = {
                "failed_logins": 0,
                "failed_mfa": 0,
                "rapid_requests": 0,
                "different_users": set(),
                "start_time": time.time(),
            }

        # Update activity based on limit type
        if limit_type == RateLimitType.LOGIN:
            activity["failed_logins"] += 1
        elif limit_type == RateLimitType.MFA:
            activity["failed_mfa"] += 1

        # Check for rapid requests (more than 10 in 10 seconds)
        if time.time() - activity["start_time"] < 10:
            activity["rapid_requests"] += 1

        # Detect suspicious patterns
        suspicious_score = (
            activity["failed_logins"] * 2
            + activity["failed_mfa"] * 3
            + activity["rapid_requests"]
            + len(activity.get("different_users", []))
        )

        # Apply lockout if suspicious
        if suspicious_score >= 10:
            await self._apply_lockout(ip_address, 3600)  # 1 hour lockout
            self.suspicious_ips.add(ip_address)

            logger.warning(
                f"Suspicious activity detected from {ip_address}. "
                f"Score: {suspicious_score}, Applying lockout."
            )

        # Save activity
        activity["different_users"] = list(activity.get("different_users", set()))
        await self.redis.setex(pattern_key, 600, json.dumps(activity))  # 10 minutes TTL

    async def _apply_lockout(self, ip_address: str, duration: int):
        """Apply lockout to an IP address"""

        lockout_key = f"lockout:ip:{ip_address}"
        await self.redis.setex(lockout_key, duration, "locked")

        # Log lockout event
        event_key = f"lockout_events:{datetime.utcnow().strftime('%Y%m%d')}"
        await self.redis.rpush(
            event_key,
            json.dumps(
                {"ip": ip_address, "timestamp": datetime.utcnow().isoformat(), "duration": duration}
            ),
        )
        await self.redis.expire(event_key, 86400 * 7)  # Keep for 7 days

    async def record_success(
        self,
        limit_type: RateLimitType,
        identifier: str,
        ip_address: str | None = None,
        user_id: str | None = None,
    ):
        """Record successful authentication to adjust thresholds"""

        # Reset failure counters
        if ip_address:
            await self.redis.delete(f"failures:{ip_address}")
            await self.redis.delete(f"pattern:{ip_address}")

        if user_id:
            await self.redis.delete(f"failures:{user_id}")

        # Track success patterns for adaptive thresholds
        success_key = f"success:{limit_type.value}:{datetime.utcnow().strftime('%Y%m%d')}"
        await self.redis.incr(success_key)
        await self.redis.expire(success_key, 86400 * 30)  # Keep for 30 days

    async def get_rate_limit_status(self, limit_type: RateLimitType, identifier: str) -> Dict:
        """Get current rate limit status for monitoring"""

        config = self.configs.get(limit_type, self.DEFAULT_CONFIGS[RateLimitType.LOGIN])

        status = {
            "limit_type": limit_type.value,
            "identifier": identifier,
            "limits": {
                "per_minute": config.requests_per_minute,
                "per_hour": config.requests_per_hour,
                "per_day": config.requests_per_day,
            },
            "current_usage": {},
        }

        # Get current usage
        for window, seconds in [("min", 60), ("hour", 3600), ("day", 86400)]:
            key = f"rate:{limit_type.value}:ip:{identifier}:{window}"
            count = await self.redis.zcard(key)
            status["current_usage"][window] = count

        # Check if locked out
        if await self._is_locked_out(identifier):
            status["locked_out"] = True
            status["lockout_remaining"] = await self._get_lockout_remaining(identifier)

        return status

    async def whitelist_ip(self, ip_address: str):
        """Add IP to trusted list"""

        self.trusted_ips.add(ip_address)
        await self.redis.sadd("trusted_ips", ip_address)

        # Remove from suspicious if present
        self.suspicious_ips.discard(ip_address)
        await self.redis.srem("suspicious_ips", ip_address)

    async def blacklist_ip(self, ip_address: str, duration: int = 86400):
        """Blacklist an IP address"""

        await self._apply_lockout(ip_address, duration)
        self.suspicious_ips.add(ip_address)
        await self.redis.sadd("suspicious_ips", ip_address)

    async def get_metrics(self) -> Dict:
        """Get rate limiting metrics for monitoring"""

        now = datetime.utcnow()
        today_key = now.strftime("%Y%m%d")

        metrics = {
            "timestamp": now.isoformat(),
            "lockouts_today": 0,
            "success_rates": {},
            "suspicious_ips": len(self.suspicious_ips),
            "trusted_ips": len(self.trusted_ips),
        }

        # Count lockout events
        lockout_events_key = f"lockout_events:{today_key}"
        metrics["lockouts_today"] = await self.redis.llen(lockout_events_key)

        # Get success rates per endpoint
        for limit_type in RateLimitType:
            success_key = f"success:{limit_type.value}:{today_key}"
            count = await self.redis.get(success_key)
            metrics["success_rates"][limit_type.value] = int(count or 0)

        return metrics


# Dependency injection helper
_rate_limiter: AuthRateLimiter | None = None


def get_rate_limiter(redis_client: redis.Redis = None) -> AuthRateLimiter:
    """Get rate limiter instance"""

    global _rate_limiter

    if _rate_limiter is None:
        if redis_client is None:
            raise RuntimeError("Redis client required for rate limiter")
        _rate_limiter = AuthRateLimiter(redis_client)

    return _rate_limiter


# FastAPI dependency
async def check_auth_rate_limit(
    request, rate_limiter: AuthRateLimiter = None  # FastAPI Request object
):
    """
    FastAPI dependency to check rate limits

    Usage:
        @router.post("/login", dependencies=[Depends(check_auth_rate_limit)])
    """

    if rate_limiter is None:
        return  # Skip if no rate limiter configured

    # Extract identifiers
    ip_address = request.client.host
    user_id = request.state.user_id if hasattr(request.state, "user_id") else None

    # Determine limit type based on endpoint
    endpoint = request.url.path

    if "/login" in endpoint:
        limit_type = RateLimitType.LOGIN
    elif "/mfa" in endpoint:
        limit_type = RateLimitType.MFA
    elif "/oauth" in endpoint:
        limit_type = RateLimitType.OAUTH
    elif "/password" in endpoint:
        limit_type = RateLimitType.PASSWORD_RESET
    elif "/register" in endpoint:
        limit_type = RateLimitType.REGISTRATION
    elif "/token/refresh" in endpoint:
        limit_type = RateLimitType.TOKEN_REFRESH
    else:
        limit_type = RateLimitType.API_KEY

    # Check rate limit
    identifier = ip_address or user_id or "unknown"
    allowed, retry_after = await rate_limiter.check_rate_limit(
        limit_type, identifier, ip_address, user_id
    )

    if not allowed:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)} if retry_after else None,
        )

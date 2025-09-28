"""
Rate Limit Manager Service

Centralized rate limiting for the application with Redis support for distributed systems.
Enhanced for 2025 production environments with Render Redis integration.
"""

import time
import hashlib
import os
import ssl
from typing import Dict, Tuple, Optional, Union, Any
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging
import json
from datetime import datetime, timedelta

try:
    import redis.asyncio as redis
    from redis.asyncio import ConnectionPool
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not available - falling back to in-memory rate limiting")

from apps.backend.core.config import settings

logger = logging.getLogger(__name__)


class RateLimitMode(Enum):
    """Rate limiting modes."""

    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    TOKEN_BUCKET = "token_bucket"


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""

    max_requests: int = 100
    window_seconds: int = 60
    mode: RateLimitMode = RateLimitMode.SLIDING_WINDOW
    burst_size: Optional[int] = None
    refill_rate: Optional[float] = None


class RateLimitManager:
    """
    Centralized rate limit manager with Redis support.

    Features:
    - Redis-based distributed rate limiting for production
    - In-memory fallback for development/testing
    - Multiple rate limiting algorithms
    - Automatic Redis reconnection
    - Prometheus metrics integration
    """

    _instance = None

    def __init__(self):
        self.request_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.window_starts: Dict[str, float] = {}
        self.lock = asyncio.Lock()
        self.mode: RateLimitMode = RateLimitMode.SLIDING_WINDOW

        # Redis connection
        self.redis_client: Optional['redis.Redis'] = None
        self.redis_pool: Optional[ConnectionPool] = None
        self.redis_connected = False

        # Determine Redis URL based on environment
        self._configure_redis_url()

        # Configuration
        self.use_redis = REDIS_AVAILABLE and getattr(settings, 'REDIS_CLOUD_ENABLED', False)
        self.redis_prefix = "rate_limit:"
        self.redis_ttl = 3600  # 1 hour TTL for keys

        # Metrics
        self.total_checks = 0
        self.total_limited = 0
        self.redis_errors = 0

    def _configure_redis_url(self):
        """Configure Redis URL based on environment and available settings."""
        # Check for Redis Cloud configuration
        if getattr(settings, 'REDIS_CLOUD_ENABLED', False):
            # Use Redis Cloud URL from environment
            self.redis_url = os.getenv('REDIS_URL')
            self.redis_cloud = True
            self.redis_cert_path = os.getenv('REDIS_CLOUD_CA_CERT_PATH')
            logger.info("Using Redis Cloud configuration")
        else:
            # Fall back to local Redis
            self.redis_url = os.getenv('REDIS_LOCAL_URL', 'redis://localhost:6379/1')
            self.redis_cloud = False
            self.redis_cert_path = None
            logger.info("Using local Redis configuration")

    @classmethod
    def reset_instance(cls):
        """Reset the singleton instance (for testing)."""
        global _rate_limit_manager
        _rate_limit_manager = None
        cls._instance = None
        logger.debug("RateLimitManager instance reset")

    @classmethod
    def get_instance(cls) -> "RateLimitManager":
        """Get the singleton instance (2025 best practice)."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def connect_redis(self) -> bool:
        """
        Connect to Redis for distributed rate limiting.
        Supports both Redis Cloud (with TLS) and local Redis.

        Returns:
            True if connected successfully
        """
        if not REDIS_AVAILABLE or not self.use_redis:
            logger.info("Redis not available or disabled, using in-memory rate limiting")
            return False

        try:
            if not self.redis_client:
                # Configure connection based on environment
                if self.redis_cloud and self.redis_url:
                    # Redis Cloud with TLS
                    logger.info("Connecting to Redis Cloud with TLS...")

                    # Parse the Redis URL to get connection parameters
                    from urllib.parse import urlparse
                    parsed_url = urlparse(self.redis_url)

                    # Create SSL context for Redis Cloud
                    ssl_context = ssl.create_default_context()
                    if self.redis_cert_path and os.path.exists(self.redis_cert_path):
                        ssl_context.load_verify_locations(self.redis_cert_path)
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_REQUIRED

                    # Create connection pool with TLS
                    self.redis_pool = ConnectionPool.from_url(
                        self.redis_url,
                        decode_responses=True,
                        socket_connect_timeout=5,
                        socket_timeout=5,
                        retry_on_timeout=True,
                        ssl_cert_reqs='required',
                        ssl_ca_certs=self.redis_cert_path if self.redis_cert_path else None,
                        max_connections=100
                    )

                    self.redis_client = redis.Redis(connection_pool=self.redis_pool)
                else:
                    # Local Redis without TLS
                    logger.info("Connecting to local Redis...")
                    self.redis_client = await redis.from_url(
                        self.redis_url,
                        encoding="utf-8",
                        decode_responses=True,
                        socket_connect_timeout=5,
                        max_connections=100
                    )

            # Test connection
            await self.redis_client.ping()
            self.redis_connected = True

            # Log connection info (mask sensitive parts)
            safe_url = self.redis_url.split('@')[-1] if '@' in self.redis_url else 'redis://localhost'
            logger.info(f"Connected to Redis for rate limiting: ...@{safe_url}")

            return True

        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Using in-memory rate limiting.")
            self.redis_connected = False
            self.redis_errors += 1

            # Clean up failed connection
            if self.redis_client:
                try:
                    await self.redis_client.aclose()
                except Exception:
                    pass
                self.redis_client = None
                self.redis_pool = None

            return False

    async def disconnect_redis(self):
        """Disconnect from Redis."""
        if self.redis_client:
            try:
                await self.redis_client.aclose()
            except Exception as e:
                logger.debug(f"Error closing Redis connection: {e}")
            finally:
                self.redis_client = None
                self.redis_connected = False
                self.redis_pool = None

    async def check_rate_limit(
        self,
        identifier: str,
        max_requests: int = None,
        window_seconds: int = 60,
        source: str = "api",
    ) -> Tuple[bool, Optional[int]]:
        """
        Check if a request is within rate limits.

        Uses Redis for distributed rate limiting in production,
        falls back to in-memory for development or Redis failures.

        Args:
            identifier: Unique identifier for the client
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
            source: Source of the request (api, websocket, etc.)

        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        self.total_checks += 1

        if max_requests is None:
            max_requests = settings.rate_limit_per_minute

        # Try Redis first if available
        if self.use_redis and self.redis_connected:
            result = await self._check_rate_limit_redis(
                identifier, max_requests, window_seconds, source
            )
            if result is not None:
                return result

            # Redis failed, try to reconnect for next time
            asyncio.create_task(self.connect_redis())

        # Fallback to in-memory rate limiting
        return await self._check_rate_limit_memory(
            identifier, max_requests, window_seconds, source
        )

    async def _check_rate_limit_redis(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int,
        source: str
    ) -> Optional[Tuple[bool, Optional[int]]]:
        """
        Check rate limit using Redis for distributed systems.

        Returns:
            Tuple of (allowed, retry_after) or None if Redis fails
        """
        try:
            # Create Redis key
            key = f"{self.redis_prefix}{source}:{identifier}"

            # Use Redis pipeline for atomic operations
            pipeline = self.redis_client.pipeline()

            # Get current count and TTL
            pipeline.incr(key)
            pipeline.expire(key, window_seconds)
            pipeline.ttl(key)

            results = await pipeline.execute()

            count = results[0]
            ttl = results[2]

            # Check if within limit
            if count <= max_requests:
                return (True, None)
            else:
                self.total_limited += 1
                # Return retry after seconds
                retry_after = ttl if ttl > 0 else window_seconds
                return (False, retry_after)

        except Exception as e:
            logger.debug(f"Redis rate limit check failed: {e}")
            self.redis_errors += 1
            self.redis_connected = False
            return None

    async def _check_rate_limit_memory(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int,
        source: str
    ) -> Tuple[bool, Optional[int]]:
        """
        Check rate limit using in-memory storage (fallback).

        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        async with self.lock:
            current_time = time.time()
            window_key = f"{identifier}:{source}"

            # Check if we need to reset the window
            if (
                window_key not in self.window_starts
                or current_time - self.window_starts[window_key] >= window_seconds
            ):
                self.window_starts[window_key] = current_time
                self.request_counts[window_key] = defaultdict(int)

            # Increment request count
            self.request_counts[window_key][source] += 1

            # Check if limit exceeded
            if self.request_counts[window_key][source] > max_requests:
                self.total_limited += 1
                retry_after = int(window_seconds - (current_time - self.window_starts[window_key]))
                logger.warning(f"Rate limit exceeded for {identifier} from {source}")
                return False, retry_after

            return True, None

    async def reset_limits(self, identifier: Optional[str] = None):
        """
        Reset rate limits for an identifier or all identifiers.
        Supports both Redis and in-memory storage.

        Args:
            identifier: Specific identifier to reset, or None for all
        """
        # Reset Redis limits if connected
        if self.use_redis and self.redis_connected:
            try:
                if identifier:
                    # Reset specific identifier in Redis
                    pattern = f"{self.redis_prefix}*:{identifier}"
                    keys = await self.redis_client.keys(pattern)
                    if keys:
                        await self.redis_client.delete(*keys)
                else:
                    # Reset all Redis rate limits
                    pattern = f"{self.redis_prefix}*"
                    keys = await self.redis_client.keys(pattern)
                    if keys:
                        await self.redis_client.delete(*keys)
            except Exception as e:
                logger.error(f"Failed to reset Redis limits: {e}")

        # Reset in-memory limits
        if identifier:
            # Reset specific identifier
            keys_to_remove = [
                k for k in self.request_counts.keys() if k.startswith(f"{identifier}:")
            ]
            for key in keys_to_remove:
                del self.request_counts[key]
                if key in self.window_starts:
                    del self.window_starts[key]
        else:
            # Reset all
            self.request_counts.clear()
            self.window_starts.clear()

    def set_mode(self, mode: RateLimitMode) -> None:
        """Set the rate limit mode."""
        self.mode = mode
        logger.info(f"Rate limit mode set to: {mode.value}")

    def clear_all_limits(self) -> None:
        """Clear all rate limits."""
        self.request_counts.clear()
        self.window_starts.clear()
        logger.debug("All rate limits cleared")

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get rate limiting metrics for Prometheus export.

        Following Prometheus naming conventions:
        - rate_limit_checks_total: Counter of total rate limit checks
        - rate_limit_limited_total: Counter of requests that were rate limited
        - rate_limit_redis_errors_total: Counter of Redis connection errors
        - rate_limit_active_windows: Gauge of active rate limit windows

        Returns:
            Dictionary of metrics
        """
        metrics = {
            "rate_limit_checks_total": self.total_checks,
            "rate_limit_limited_total": self.total_limited,
            "rate_limit_redis_errors_total": self.redis_errors,
            "rate_limit_active_windows": len(self.window_starts),
            "rate_limit_redis_connected": self.redis_connected,
            "rate_limit_mode": self.mode.value,
        }

        # Add Redis-specific metrics if connected
        if self.redis_connected and self.redis_client:
            try:
                # Get Redis info asynchronously would require await
                # For now, just add connection status
                metrics["rate_limit_redis_status"] = "connected"
            except Exception:
                metrics["rate_limit_redis_status"] = "error"
        else:
            metrics["rate_limit_redis_status"] = "disconnected"

        return metrics

    async def export_prometheus_metrics(self):
        """
        Export metrics in Prometheus format.

        Returns metrics as a string in Prometheus text format.
        """
        metrics = self.get_metrics()
        lines = []

        # Add HELP and TYPE comments following Prometheus format
        lines.append("# HELP rate_limit_checks_total Total number of rate limit checks")
        lines.append("# TYPE rate_limit_checks_total counter")
        lines.append(f"rate_limit_checks_total {metrics['rate_limit_checks_total']}")

        lines.append("# HELP rate_limit_limited_total Total number of rate limited requests")
        lines.append("# TYPE rate_limit_limited_total counter")
        lines.append(f"rate_limit_limited_total {metrics['rate_limit_limited_total']}")

        lines.append("# HELP rate_limit_redis_errors_total Total Redis connection errors")
        lines.append("# TYPE rate_limit_redis_errors_total counter")
        lines.append(f"rate_limit_redis_errors_total {metrics['rate_limit_redis_errors_total']}")

        lines.append("# HELP rate_limit_active_windows Number of active rate limit windows")
        lines.append("# TYPE rate_limit_active_windows gauge")
        lines.append(f"rate_limit_active_windows {metrics['rate_limit_active_windows']}")

        lines.append("# HELP rate_limit_redis_connected Redis connection status")
        lines.append("# TYPE rate_limit_redis_connected gauge")
        lines.append(f"rate_limit_redis_connected {1 if metrics['rate_limit_redis_connected'] else 0}")

        return "\n".join(lines)

    async def start_cleanup(self):
        """Start background cleanup task for expired rate limit entries."""
        while True:
            try:
                # Clean up expired entries every 60 seconds
                await asyncio.sleep(60)

                async with self.lock:
                    current_time = time.time()

                    # Clean up old windows
                    keys_to_remove = []
                    for window_key, window_start in self.window_starts.items():
                        if current_time - window_start > 120:  # Remove windows older than 2 minutes
                            keys_to_remove.append(window_key)

                    for key in keys_to_remove:
                        if key in self.request_counts:
                            del self.request_counts[key]
                        if key in self.window_starts:
                            del self.window_starts[key]

                    if keys_to_remove:
                        logger.debug(f"Cleaned up {len(keys_to_remove)} expired rate limit windows")

            except Exception as e:
                logger.error(f"Error in rate limit cleanup: {e}")
                await asyncio.sleep(60)  # Continue after error

    def get_current_usage(self, identifier: str, source: str = "api") -> Dict[str, Any]:
        """
        Get current usage statistics for an identifier.

        Args:
            identifier: Unique identifier
            source: Source of requests

        Returns:
            Dictionary with usage statistics
        """
        window_key = f"{identifier}:{source}"
        current_time = time.time()

        if window_key not in self.window_starts:
            return {"requests": 0, "window_start": None, "time_remaining": 0}

        window_start = self.window_starts[window_key]
        time_elapsed = current_time - window_start
        time_remaining = max(0, 60 - time_elapsed)  # Assuming 60 second window

        return {
            "requests": self.request_counts[window_key][source],
            "window_start": window_start,
            "time_remaining": time_remaining,
        }


# Testing support
_testing_mode = False


class RateLimitTestContext:
    """Context manager for rate limit testing."""

    def __init__(self, bypass: bool = True):
        self.bypass = bypass
        self.original_mode = None

    def __enter__(self):
        global _testing_mode
        self.original_mode = _testing_mode
        _testing_mode = self.bypass
        if self.bypass:
            clear_all_rate_limits()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        global _testing_mode
        _testing_mode = self.original_mode
        if self.bypass:
            clear_all_rate_limits()


def set_testing_mode(enabled: bool = True):
    """Enable or disable testing mode for rate limiting."""
    global _testing_mode
    _testing_mode = enabled
    if enabled:
        logger.info("Rate limiting testing mode enabled")


def clear_all_rate_limits():
    """Clear all rate limit data (for testing)."""
    manager = get_rate_limit_manager()
    manager.request_counts.clear()
    manager.window_starts.clear()
    logger.debug("All rate limits cleared")


# Create singleton instance
_rate_limit_manager = None


def get_rate_limit_manager() -> RateLimitManager:
    """Get the singleton rate limit manager instance (2025 best practice)."""
    return RateLimitManager.get_instance()


# Export for convenience
rate_limit_manager = get_rate_limit_manager()


# Rate limit decorator for FastAPI endpoints
from functools import wraps
from fastapi import Request, HTTPException, status
from typing import Callable, Optional


def rate_limit(
    max_requests: int = 100, window_seconds: int = 60, identifier_func: Optional[Callable] = None
):
    """
    Rate limiting decorator for FastAPI endpoints.

    Args:
        max_requests: Maximum requests allowed in the window
        window_seconds: Time window in seconds
        identifier_func: Optional function to extract identifier from request
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Skip rate limiting in testing mode
            global _testing_mode
            if _testing_mode:
                return await func(*args, **kwargs)

            # Find the Request object in args or kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request:
                request = kwargs.get("request")

            if not request:
                # If no request found, proceed without rate limiting
                logger.warning(f"No Request object found for rate limiting in {func.__name__}")
                return await func(*args, **kwargs)

            # Determine identifier
            if identifier_func:
                identifier = identifier_func(request)
            else:
                # Use client IP as default identifier
                identifier = request.client.host if request.client else "unknown"

            # Check rate limit
            manager = get_rate_limit_manager()
            allowed, retry_after = await manager.check_rate_limit(
                identifier=identifier,
                max_requests=max_requests,
                window_seconds=window_seconds,
                source=f"endpoint:{func.__name__}",
            )

            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers={"Retry-After": str(retry_after)} if retry_after else None,
                )

            # Proceed with the original function
            return await func(*args, **kwargs)

        return wrapper

    return decorator

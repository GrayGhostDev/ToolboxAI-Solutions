"""
Redis Caching Service for ToolboxAI Backend

Provides a centralized caching layer for frequently accessed data
with support for multiple cache strategies and TTL management.

Features:
- Automatic cache key generation
- Configurable TTL per cache type
- Cache invalidation patterns
- Cache warming for critical data
- Metrics tracking for cache hits/misses
"""

import json
import hashlib
from typing import Any, Optional, Callable, Union
from functools import wraps
from datetime import timedelta

import redis.asyncio as aioredis
from pydantic import BaseModel

from apps.backend.core.config import settings
from apps.backend.core.logging import logging_manager

logger = logging_manager.get_logger(__name__)


class CacheConfig(BaseModel):
    """Configuration for cache settings"""
    ttl: int = 300  # Default 5 minutes
    namespace: str = "default"
    serialize: bool = True


class CacheService:
    """
    Redis-based caching service with automatic serialization and TTL management
    """

    def __init__(
        self,
        redis_url: str = None,
        default_ttl: int = 300,
        prefix: str = "cache"
    ):
        self.redis_url = redis_url or settings.REDIS_URL or "redis://localhost:6379/1"
        self.default_ttl = default_ttl
        self.prefix = prefix
        self.redis: Optional[aioredis.Redis] = None

        # Cache type configurations
        self.cache_configs = {
            "dashboard": CacheConfig(ttl=300, namespace="dashboard"),      # 5 min
            "metrics": CacheConfig(ttl=60, namespace="metrics"),           # 1 min
            "analytics": CacheConfig(ttl=600, namespace="analytics"),      # 10 min
            "user_profile": CacheConfig(ttl=1800, namespace="user"),       # 30 min
            "organization": CacheConfig(ttl=3600, namespace="org"),        # 1 hour
            "content": CacheConfig(ttl=900, namespace="content"),          # 15 min
            "session": CacheConfig(ttl=86400, namespace="session"),        # 24 hours
        }

        # Metrics
        self.cache_hits = 0
        self.cache_misses = 0

    async def connect(self):
        """Connect to Redis"""
        if not self.redis:
            self.redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False  # We'll handle encoding ourselves
            )
            logger.info("Cache service connected to Redis")

    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            logger.info("Cache service disconnected from Redis")

    def _generate_key(
        self,
        namespace: str,
        key: Union[str, dict],
        organization_id: Optional[str] = None
    ) -> str:
        """
        Generate cache key with namespace and optional organization isolation

        Args:
            namespace: Cache namespace (e.g., 'dashboard', 'metrics')
            key: Cache key or dict to hash
            organization_id: Optional organization ID for multi-tenant isolation

        Returns:
            Fully qualified cache key
        """
        # Convert dict to sorted JSON string for consistent hashing
        if isinstance(key, dict):
            key_str = json.dumps(key, sort_keys=True)
        else:
            key_str = str(key)

        # Hash long keys
        if len(key_str) > 100:
            key_hash = hashlib.sha256(key_str.encode()).hexdigest()[:16]
        else:
            key_hash = key_str.replace(":", "_").replace(" ", "_")

        # Build key with organization isolation
        parts = [self.prefix, namespace]
        if organization_id:
            parts.append(f"org:{organization_id}")
        parts.append(key_hash)

        return ":".join(parts)

    async def get(
        self,
        key: Union[str, dict],
        namespace: str = "default",
        organization_id: Optional[str] = None
    ) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key or dict to hash
            namespace: Cache namespace
            organization_id: Optional organization ID

        Returns:
            Cached value or None if not found
        """
        if not self.redis:
            await self.connect()

        cache_key = self._generate_key(namespace, key, organization_id)

        try:
            value = await self.redis.get(cache_key)
            if value:
                self.cache_hits += 1
                logger.debug(f"Cache hit: {cache_key}")
                return json.loads(value)
            else:
                self.cache_misses += 1
                logger.debug(f"Cache miss: {cache_key}")
                return None
        except Exception as e:
            logger.error(f"Cache get error for {cache_key}: {e}")
            return None

    async def set(
        self,
        key: Union[str, dict],
        value: Any,
        namespace: str = "default",
        ttl: Optional[int] = None,
        organization_id: Optional[str] = None
    ) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key or dict to hash
            value: Value to cache (will be JSON serialized)
            namespace: Cache namespace
            ttl: Time to live in seconds (None = use default)
            organization_id: Optional organization ID

        Returns:
            True if successful, False otherwise
        """
        if not self.redis:
            await self.connect()

        cache_key = self._generate_key(namespace, key, organization_id)

        # Get TTL from cache config or use provided/default
        if ttl is None:
            config = self.cache_configs.get(namespace)
            ttl = config.ttl if config else self.default_ttl

        try:
            serialized = json.dumps(value)
            await self.redis.setex(cache_key, ttl, serialized)
            logger.debug(f"Cache set: {cache_key} (ttl={ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache set error for {cache_key}: {e}")
            return False

    async def delete(
        self,
        key: Union[str, dict],
        namespace: str = "default",
        organization_id: Optional[str] = None
    ) -> bool:
        """Delete value from cache"""
        if not self.redis:
            await self.connect()

        cache_key = self._generate_key(namespace, key, organization_id)

        try:
            deleted = await self.redis.delete(cache_key)
            logger.debug(f"Cache delete: {cache_key} (deleted={deleted})")
            return deleted > 0
        except Exception as e:
            logger.error(f"Cache delete error for {cache_key}: {e}")
            return False

    async def delete_pattern(
        self,
        pattern: str,
        namespace: str = "default"
    ) -> int:
        """
        Delete all keys matching pattern

        Args:
            pattern: Pattern to match (e.g., 'user:*', 'dashboard:*')
            namespace: Cache namespace

        Returns:
            Number of keys deleted
        """
        if not self.redis:
            await self.connect()

        full_pattern = f"{self.prefix}:{namespace}:{pattern}"

        try:
            keys = []
            async for key in self.redis.scan_iter(match=full_pattern, count=100):
                keys.append(key)

            if keys:
                deleted = await self.redis.delete(*keys)
                logger.info(f"Cache invalidated: {deleted} keys matching {full_pattern}")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Cache pattern delete error for {full_pattern}: {e}")
            return 0

    async def invalidate_organization(self, organization_id: str) -> int:
        """Invalidate all cache entries for an organization"""
        pattern = f"*:org:{organization_id}:*"
        return await self.delete_pattern(pattern, namespace="*")

    async def get_stats(self) -> dict:
        """Get cache statistics"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "connected": self.redis is not None
        }


# Global cache service instance
cache_service = CacheService()


def cached(
    namespace: str = "default",
    ttl: Optional[int] = None,
    key_builder: Optional[Callable] = None
):
    """
    Decorator to cache function results

    Args:
        namespace: Cache namespace
        ttl: Time to live in seconds
        key_builder: Optional function to build cache key from args

    Example:
        @cached(namespace="dashboard", ttl=300)
        async def get_dashboard_metrics(organization_id: str):
            # Expensive database query
            return metrics

        # With custom key builder
        @cached(
            namespace="analytics",
            ttl=600,
            key_builder=lambda org_id, date_range: f"{org_id}:{date_range}"
        )
        async def get_analytics(org_id: str, date_range: str):
            return analytics
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Use function name and arguments
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)

            # Extract organization_id if present
            organization_id = kwargs.get("organization_id") or (args[0] if args else None)

            # Try to get from cache
            cached_value = await cache_service.get(
                cache_key,
                namespace=namespace,
                organization_id=str(organization_id) if organization_id else None
            )

            if cached_value is not None:
                logger.debug(f"Returning cached result for {func.__name__}")
                return cached_value

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            await cache_service.set(
                cache_key,
                result,
                namespace=namespace,
                ttl=ttl,
                organization_id=str(organization_id) if organization_id else None
            )

            return result
        return wrapper
    return decorator


# Startup and shutdown handlers
async def startup_cache_service():
    """Initialize cache service on startup"""
    logger.info("Initializing cache service...")
    await cache_service.connect()


async def shutdown_cache_service():
    """Cleanup cache service on shutdown"""
    logger.info("Shutting down cache service...")
    await cache_service.close()

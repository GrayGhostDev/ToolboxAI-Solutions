"""
Modern Redis Caching Layer (2025 Standards)

Provides async Redis caching with:
- Decorator-based caching
- Automatic serialization/deserialization
- Cache invalidation strategies
- Connection pooling
- Type-safe operations

Reference: https://redis.readthedocs.io/en/stable/
"""

import hashlib
import json
import logging
from datetime import timedelta
from functools import wraps
from typing import Any, Callable, Optional, ParamSpec, TypeVar, Union
from uuid import UUID

from redis.asyncio import ConnectionPool, Redis
from redis.exceptions import RedisError

from toolboxai_settings.settings import settings

logger = logging.getLogger(__name__)

# Type variables for generic decorators
P = ParamSpec("P")
T = TypeVar("T")


class CacheKeyBuilder:
    """
    Builds consistent cache keys from function calls.

    Ensures cache key uniqueness and handles complex types.
    """

    @staticmethod
    def build_key(
        prefix: str,
        func_name: str,
        args: tuple,
        kwargs: dict,
    ) -> str:
        """
        Build cache key from function call.

        Args:
            prefix: Cache key prefix (e.g., "user", "content")
            func_name: Function name
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Unique cache key string
        """
        # Serialize arguments to create unique key
        args_str = CacheKeyBuilder._serialize_args(args)
        kwargs_str = CacheKeyBuilder._serialize_args(tuple(sorted(kwargs.items())))

        # Create hash for long keys
        combined = f"{func_name}:{args_str}:{kwargs_str}"
        key_hash = hashlib.sha256(combined.encode()).hexdigest()[:16]

        return f"{prefix}:{func_name}:{key_hash}"

    @staticmethod
    def _serialize_args(args: tuple) -> str:
        """
        Serialize arguments for cache key.

        Args:
            args: Arguments to serialize

        Returns:
            Serialized string
        """

        def serialize_value(val: Any) -> str:
            """Serialize single value."""
            if isinstance(val, UUID):
                return str(val)
            elif isinstance(val, (dict, list, tuple)):
                return json.dumps(val, sort_keys=True, default=str)
            else:
                return str(val)

        return ":".join(serialize_value(arg) for arg in args)


class RedisCache:
    """
    Async Redis cache manager with connection pooling.

    Provides:
    - Async get/set operations
    - Automatic serialization
    - Connection pooling
    - Health checks
    """

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize Redis cache manager.

        Args:
            redis_url: Redis connection URL
                      If None, uses settings.REDIS_URL
        """
        self._redis_url = redis_url or settings.REDIS_URL
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[Redis] = None

    def _create_pool(self) -> ConnectionPool:
        """
        Create Redis connection pool.

        Pool settings optimized for async operations:
        - max_connections: 50
        - decode_responses: False (handle binary data)
        - socket_timeout: 5 seconds
        - socket_connect_timeout: 5 seconds
        """
        return ConnectionPool.from_url(
            self._redis_url,
            max_connections=50,
            decode_responses=False,  # Handle binary data
            socket_timeout=5,
            socket_connect_timeout=5,
        )

    @property
    def client(self) -> Redis:
        """
        Get Redis client, creating if needed.

        Returns:
            Async Redis client
        """
        if self._client is None:
            if self._pool is None:
                self._pool = self._create_pool()

            self._client = Redis(connection_pool=self._pool)
            logger.info("Redis client created successfully")

        return self._client

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            value = await self.client.get(key)

            if value is None:
                logger.debug(f"Cache miss: {key}")
                return None

            logger.debug(f"Cache hit: {key}")
            return json.loads(value)

        except RedisError as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[Union[int, timedelta]] = None,
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            expire: Expiration in seconds or timedelta

        Returns:
            True if successful, False otherwise
        """
        try:
            serialized = json.dumps(value, default=str)

            if expire is not None:
                if isinstance(expire, timedelta):
                    expire = int(expire.total_seconds())

                await self.client.setex(key, expire, serialized)
            else:
                await self.client.set(key, serialized)

            logger.debug(f"Cache set: {key} (expire: {expire}s)")
            return True

        except (RedisError, TypeError) as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False otherwise
        """
        try:
            result = await self.client.delete(key)
            logger.debug(f"Cache delete: {key} (existed: {bool(result)})")
            return bool(result)

        except RedisError as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.

        Args:
            pattern: Key pattern (e.g., "user:*")

        Returns:
            Number of keys deleted
        """
        try:
            cursor = 0
            deleted = 0

            while True:
                cursor, keys = await self.client.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100,
                )

                if keys:
                    deleted += await self.client.delete(*keys)

                if cursor == 0:
                    break

            logger.info(f"Deleted {deleted} keys matching pattern: {pattern}")
            return deleted

        except RedisError as e:
            logger.error(f"Redis delete pattern error for {pattern}: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if exists, False otherwise
        """
        try:
            return bool(await self.client.exists(key))
        except RedisError as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment counter.

        Args:
            key: Counter key
            amount: Amount to increment

        Returns:
            New counter value or None on error
        """
        try:
            return await self.client.incrby(key, amount)
        except RedisError as e:
            logger.error(f"Redis increment error for key {key}: {e}")
            return None

    async def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration on existing key.

        Args:
            key: Cache key
            seconds: Expiration in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            return bool(await self.client.expire(key, seconds))
        except RedisError as e:
            logger.error(f"Redis expire error for key {key}: {e}")
            return False

    async def health_check(self) -> bool:
        """
        Check Redis connectivity.

        Returns:
            True if Redis is accessible, False otherwise
        """
        try:
            await self.client.ping()
            logger.info("Redis health check passed")
            return True
        except RedisError as e:
            logger.error(f"Redis health check failed: {e}")
            return False

    async def close(self) -> None:
        """Close Redis connection pool."""
        if self._client is not None:
            await self._client.close()
            self._client = None

        if self._pool is not None:
            await self._pool.disconnect()
            self._pool = None

        logger.info("Redis connection closed")


# Global cache instance
redis_cache = RedisCache()


def cache_result(
    prefix: str = "cache",
    expire: int = 300,  # 5 minutes default
    key_builder: Optional[Callable] = None,
):
    """
    Decorator for caching async function results.

    Args:
        prefix: Cache key prefix
        expire: Expiration in seconds
        key_builder: Custom key builder function

    Usage:
        @cache_result(prefix="user", expire=600)
        async def get_user(user_id: UUID) -> User:
            # Expensive database query
            return user

    Returns:
        Decorated function
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = CacheKeyBuilder.build_key(prefix, func.__name__, args, kwargs)

            # Try to get from cache
            cached = await redis_cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Returning cached result for {func.__name__}")
                return cached

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            await redis_cache.set(cache_key, result, expire=expire)

            return result

        return wrapper

    return decorator


def invalidate_cache(prefix: str):
    """
    Decorator for invalidating cache after function execution.

    Args:
        prefix: Cache key prefix pattern to invalidate

    Usage:
        @invalidate_cache(prefix="user:*")
        async def update_user(user_id: UUID, data: dict):
            # Update user in database
            pass

    Returns:
        Decorated function
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Execute function first
            result = await func(*args, **kwargs)

            # Invalidate cache
            await redis_cache.delete_pattern(f"{prefix}*")
            logger.info(f"Invalidated cache for pattern: {prefix}*")

            return result

        return wrapper

    return decorator


# Export public API
__all__ = [
    "RedisCache",
    "redis_cache",
    "cache_result",
    "invalidate_cache",
    "CacheKeyBuilder",
]

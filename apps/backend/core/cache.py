"""
Redis Caching Layer with Performance Optimizations
Implements intelligent caching strategies to reduce database load and API response times.
Target: Reduce P95 latency from 185ms to <150ms
"""

import asyncio
import hashlib
import logging
import pickle
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, Union

import redis.asyncio as redis

from apps.backend.core.config import settings

logger = logging.getLogger(__name__)

# Type hints
T = TypeVar("T")
CacheValue = Union[str, bytes, dict[str, Any], list[Any], int, float]


class CacheConfig:
    """Configuration for caching behavior"""

    # Default TTL values (in seconds)
    DEFAULT_TTL = 300  # 5 minutes
    SHORT_TTL = 60  # 1 minute
    MEDIUM_TTL = 900  # 15 minutes
    LONG_TTL = 3600  # 1 hour
    VERY_LONG_TTL = 86400  # 24 hours

    # Cache key prefixes
    PREFIX_USER = "user"
    PREFIX_DASHBOARD = "dashboard"
    PREFIX_CONTENT = "content"
    PREFIX_AGENT = "agent"
    PREFIX_API = "api"
    PREFIX_QUERY = "query"

    # Pool settings for performance
    POOL_MIN_CONNECTIONS = 10
    POOL_MAX_CONNECTIONS = 50
    POOL_RETRY_ON_TIMEOUT = True

    # Compression threshold (bytes)
    COMPRESSION_THRESHOLD = 1024


class RedisConnectionManager:
    """Manages Redis connection pool with optimized settings"""

    def __init__(self):
        self.pool: redis.ConnectionPool | None = None
        self.client: redis.Redis | None = None
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Initialize Redis connection pool with performance optimizations"""
        if self.pool is not None:
            return

        async with self._lock:
            if self.pool is not None:  # Double-check pattern
                return

            try:
                # Parse Redis URL from settings
                redis_url = settings.REDIS_URL

                # Create simplified connection pool (macOS-compatible)
                self.pool = redis.ConnectionPool.from_url(
                    redis_url,
                    # Performance optimizations
                    max_connections=CacheConfig.POOL_MAX_CONNECTIONS,
                    retry_on_timeout=CacheConfig.POOL_RETRY_ON_TIMEOUT,
                    # Connection timeout optimizations
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_error=[redis.BusyLoadingError, redis.ConnectionError],
                    # Enable health checks
                    health_check_interval=30,
                )

                # Create Redis client
                self.client = redis.Redis(
                    connection_pool=self.pool,
                    decode_responses=False,  # Keep as bytes for flexibility
                    retry_on_error=[redis.BusyLoadingError],
                )

                # Test connection
                await self.client.ping()
                logger.info(
                    f"Redis connection pool initialized with {CacheConfig.POOL_MAX_CONNECTIONS} max connections"
                )

            except Exception as e:
                logger.error(f"Failed to initialize Redis connection: {e}")
                raise

    async def get_client(self) -> redis.Redis:
        """Get Redis client, initializing if needed"""
        if self.client is None:
            await self.initialize()
        return self.client

    async def close(self):
        """Close Redis connections"""
        if self.client:
            await self.client.aclose()
        if self.pool:
            await self.pool.disconnect()
        logger.info("Redis connections closed")


# Global connection manager
_connection_manager = RedisConnectionManager()


class CacheKey:
    """Utility for generating consistent cache keys"""

    @staticmethod
    def generate(prefix: str, *args: Any, **kwargs: Any) -> str:
        """Generate a consistent cache key from arguments"""
        # Create deterministic key from arguments
        key_parts = [prefix]

        # Add positional arguments
        for arg in args:
            if isinstance(arg, (str, int, float)):
                key_parts.append(str(arg))
            else:
                # Hash complex objects
                key_parts.append(hashlib.md5(str(arg).encode()).hexdigest()[:8])

        # Add keyword arguments (sorted for consistency)
        for k, v in sorted(kwargs.items()):
            if isinstance(v, (str, int, float)):
                key_parts.append(f"{k}:{v}")
            else:
                key_parts.append(f"{k}:{hashlib.md5(str(v).encode()).hexdigest()[:8]}")

        return ":".join(key_parts)

    @staticmethod
    def user_dashboard(user_id: int, role: str) -> str:
        """Generate key for user dashboard data"""
        return CacheKey.generate(CacheConfig.PREFIX_DASHBOARD, user_id, role)

    @staticmethod
    def api_response(endpoint: str, **params) -> str:
        """Generate key for API response caching"""
        return CacheKey.generate(CacheConfig.PREFIX_API, endpoint, **params)

    @staticmethod
    def database_query(query_hash: str, *params) -> str:
        """Generate key for database query results"""
        return CacheKey.generate(CacheConfig.PREFIX_QUERY, query_hash, *params)


def cache_result(ttl: int = None, expire: int = None):
    """Legacy decorator for backward compatibility"""
    cache_ttl = ttl or expire or 300

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache_key = CacheKey.generate(CacheConfig.PREFIX_API, func.__name__, *args, **kwargs)

            # Try to get from cache
            cached = await _cache.get(cache_key)
            if cached is not None:
                return cached

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            await _cache.set(cache_key, result, cache_ttl)
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, use a simpler approach
            result = func(*args, **kwargs)
            return result

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


class CacheSerializer:
    """Handle serialization/deserialization of cache values"""

    @staticmethod
    def serialize(value: Any) -> bytes:
        """Serialize value for cache storage"""
        if isinstance(value, (str, bytes)):
            data = value.encode() if isinstance(value, str) else value
        else:
            # Use pickle for complex objects (faster than JSON for Python objects)
            data = pickle.dumps(value)

        # Compress if data is large
        if len(data) > CacheConfig.COMPRESSION_THRESHOLD:
            import gzip

            data = gzip.compress(data)
            # Add compression marker
            data = b"GZIP:" + data

        return data

    @staticmethod
    def deserialize(data: bytes) -> Any:
        """Deserialize value from cache"""
        if not data:
            return None

        # Check for compression
        if data.startswith(b"GZIP:"):
            import gzip

            data = gzip.decompress(data[5:])

        # Try to deserialize as pickle
        try:
            return pickle.loads(data)
        except (pickle.UnpicklingError, EOFError):
            # Fallback to string
            try:
                return data.decode("utf-8")
            except UnicodeDecodeError:
                return data


class CacheStats:
    """Track cache performance statistics"""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
        self.errors = 0
        self.total_time = 0.0

    def record_hit(self, duration: float):
        self.hits += 1
        self.total_time += duration

    def record_miss(self, duration: float):
        self.misses += 1
        self.total_time += duration

    def record_set(self):
        self.sets += 1

    def record_delete(self):
        self.deletes += 1

    def record_error(self):
        self.errors += 1

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return (self.hits / total) if total > 0 else 0.0

    @property
    def avg_time(self) -> float:
        total = self.hits + self.misses
        return (self.total_time / total) if total > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "errors": self.errors,
            "hit_rate": self.hit_rate,
            "avg_time_ms": self.avg_time * 1000,
        }


class RedisCache:
    """High-performance Redis cache implementation"""

    def __init__(self):
        self.stats = CacheStats()

    async def get_client(self) -> redis.Redis:
        """Get Redis client"""
        return await _connection_manager.get_client()

    async def get(self, key: str) -> Any | None:
        """Get value from cache"""
        start_time = time.time()

        try:
            client = await self.get_client()
            data = await client.get(key)

            duration = time.time() - start_time

            if data is not None:
                self.stats.record_hit(duration)
                return CacheSerializer.deserialize(data)
            else:
                self.stats.record_miss(duration)
                return None

        except Exception as e:
            self.stats.record_error()
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = CacheConfig.DEFAULT_TTL) -> bool:
        """Set value in cache with TTL"""
        try:
            client = await self.get_client()
            data = CacheSerializer.serialize(value)

            result = await client.setex(key, ttl, data)
            self.stats.record_set()
            return bool(result)

        except Exception as e:
            self.stats.record_error()
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            client = await self.get_client()
            result = await client.delete(key)
            self.stats.record_delete()
            return bool(result)

        except Exception as e:
            self.stats.record_error()
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern"""
        try:
            client = await self.get_client()
            keys = await client.keys(pattern)
            if keys:
                deleted = await client.delete(*keys)
                self.stats.deletes += len(keys)
                return deleted
            return 0

        except Exception as e:
            self.stats.record_error()
            logger.error(f"Cache delete pattern error for {pattern}: {e}")
            return 0

    async def mget(self, keys: list[str]) -> list[Any | None]:
        """Get multiple values from cache"""
        try:
            client = await self.get_client()
            data_list = await client.mget(keys)

            results = []
            for data in data_list:
                if data is not None:
                    results.append(CacheSerializer.deserialize(data))
                else:
                    results.append(None)

            return results

        except Exception as e:
            self.stats.record_error()
            logger.error(f"Cache mget error: {e}")
            return [None] * len(keys)

    def get_stats(self) -> dict[str, Any]:
        """Get cache performance statistics"""
        return self.stats.to_dict()


# Global cache instance
_cache = RedisCache()


def cached(
    key_func: Callable[..., str] | None = None,
    ttl: int = CacheConfig.DEFAULT_TTL,
    prefix: str = CacheConfig.PREFIX_API,
):
    """
    Decorator for caching function results

    Args:
        key_func: Function to generate cache key from arguments
        ttl: Time to live in seconds
        prefix: Cache key prefix
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Generate default key from function name and arguments
                func_name = func.__name__
                cache_key = CacheKey.generate(prefix, func_name, *args, **kwargs)

            # Try to get from cache
            cached_result = await _cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function
            result = (
                await func(*args, **kwargs)
                if asyncio.iscoroutinefunction(func)
                else func(*args, **kwargs)
            )

            # Cache result
            await _cache.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


class CacheWarmer:
    """Pre-populate cache with frequently accessed data"""

    def __init__(self, cache: RedisCache):
        self.cache = cache

    async def warm_user_dashboard(self, user_id: int, role: str):
        """Warm cache for user dashboard data"""
        from apps.backend.services.database import db_service

        try:
            # Get dashboard data
            dashboard_data = await db_service.get_dashboard_data(role, user_id)

            # Cache with different TTLs based on data type
            cache_key = CacheKey.user_dashboard(user_id, role)
            await self.cache.set(cache_key, dashboard_data, CacheConfig.MEDIUM_TTL)

            logger.debug(f"Warmed cache for user {user_id} dashboard")

        except Exception as e:
            logger.error(f"Failed to warm cache for user {user_id}: {e}")


class CacheInvalidator:
    """Handle cache invalidation patterns"""

    def __init__(self, cache: RedisCache):
        self.cache = cache

    async def invalidate_user_data(self, user_id: int):
        """Invalidate all cache entries for a user"""
        pattern = f"*:{user_id}:*"
        deleted = await self.cache.delete_pattern(pattern)
        logger.debug(f"Invalidated {deleted} cache entries for user {user_id}")

    async def invalidate_dashboard_data(self, user_id: int, role: str):
        """Invalidate dashboard cache for specific user/role"""
        cache_key = CacheKey.user_dashboard(user_id, role)
        await self.cache.delete(cache_key)


# Initialize cache on import
async def initialize_cache():
    """Initialize the cache system"""
    try:
        await _connection_manager.initialize()
        logger.info("Redis cache system initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize cache system: {e}")


# Export main interface
cache = _cache
warmer = CacheWarmer(_cache)
invalidator = CacheInvalidator(_cache)

# Backward compatibility: CacheService is an alias for RedisCache
# This allows legacy code to import CacheService from this module
CacheService = RedisCache


# Convenience functions for common operations
async def get_cached_dashboard(user_id: int, role: str) -> dict[str, Any] | None:
    """Get cached dashboard data"""
    cache_key = CacheKey.user_dashboard(user_id, role)
    return await cache.get(cache_key)


async def cache_dashboard(user_id: int, role: str, data: dict[str, Any]):
    """Cache dashboard data"""
    cache_key = CacheKey.user_dashboard(user_id, role)
    await cache.set(cache_key, data, CacheConfig.MEDIUM_TTL)


async def get_cache_health() -> dict[str, Any]:
    """Get cache system health metrics"""
    try:
        client = await _connection_manager.get_client()
        info = await client.info("memory")

        return {
            "status": "healthy",
            "stats": cache.get_stats(),
            "memory": {
                "used": info.get("used_memory_human"),
                "peak": info.get("used_memory_peak_human"),
                "fragmentation_ratio": info.get("mem_fragmentation_ratio"),
            },
            "connections": {
                "connected_clients": info.get("connected_clients"),
                "blocked_clients": info.get("blocked_clients"),
            },
        }

    except Exception as e:
        return {"status": "unhealthy", "error": str(e), "stats": cache.get_stats()}

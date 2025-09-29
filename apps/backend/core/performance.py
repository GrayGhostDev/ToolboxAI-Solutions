"""
Performance Optimization Module

Implements caching, query optimization, resource pooling, and monitoring
for optimal performance in production environments.
"""

import asyncio
import functools
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import redis.asyncio as redis
from fastapi import Request, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from toolboxai_settings import settings

settings = settings

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching with Redis and in-memory fallback"""

    def __init__(
        self,
        redis_url: Optional[str] = None,
        default_ttl: int = 300,  # 5 minutes
        max_memory_items: int = 1000,
    ):
        """
        Initialize cache manager

        Args:
            redis_url: Redis connection URL
            default_ttl: Default TTL in seconds
            max_memory_items: Maximum items in memory cache
        """
        self.redis_url = redis_url or getattr(settings, "REDIS_URL", None)
        self.default_ttl = default_ttl
        self.max_memory_items = max_memory_items
        self.redis_client: Optional[redis.Redis] = None
        self.memory_cache: Dict[str, Tuple[Any, float]] = {}
        self.cache_stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0, "errors": 0}

    async def initialize(self):
        """Initialize Redis connection"""
        if self.redis_url:
            try:
                self.redis_client = await redis.from_url(
                    self.redis_url, encoding="utf-8", decode_responses=True
                )
                await self.redis_client.ping()
                logger.info("Redis cache initialized successfully")
            except Exception as e:
                logger.warning(f"Redis connection failed, using memory cache: {e}")
                self.redis_client = None

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.aclose()

    def _generate_key(self, namespace: str, *args, **kwargs) -> str:
        """Generate cache key from namespace and arguments"""
        key_data = {"namespace": namespace, "args": args, "kwargs": kwargs}
        key_str = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return f"{namespace}:{key_hash}"

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            # Try Redis first
            if self.redis_client:
                value = await self.redis_client.get(key)
                if value:
                    self.cache_stats["hits"] += 1
                    return json.loads(value) if value else None

            # Fallback to memory cache
            if key in self.memory_cache:
                value, expiry = self.memory_cache[key]
                if time.time() < expiry:
                    self.cache_stats["hits"] += 1
                    return value
                else:
                    # Expired
                    del self.memory_cache[key]

            self.cache_stats["misses"] += 1
            return None

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.cache_stats["errors"] += 1
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with TTL"""
        try:
            ttl = ttl or self.default_ttl

            # Store in Redis
            if self.redis_client:
                await self.redis_client.setex(key, ttl, json.dumps(value))

            # Store in memory cache
            expiry = time.time() + ttl
            self.memory_cache[key] = (value, expiry)

            # Evict old items if needed
            if len(self.memory_cache) > self.max_memory_items:
                self._evict_memory_cache()

            self.cache_stats["sets"] += 1
            return True

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            self.cache_stats["errors"] += 1
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            # Delete from Redis
            if self.redis_client:
                await self.redis_client.delete(key)

            # Delete from memory cache
            if key in self.memory_cache:
                del self.memory_cache[key]

            self.cache_stats["deletes"] += 1
            return True

        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            self.cache_stats["errors"] += 1
            return False

    async def clear_namespace(self, namespace: str) -> int:
        """Clear all keys in a namespace"""
        count = 0

        try:
            if self.redis_client:
                # Use SCAN to find and delete keys
                cursor = "0"
                pattern = f"{namespace}:*"

                while cursor != 0:
                    cursor, keys = await self.redis_client.scan(
                        cursor=cursor, match=pattern, count=100
                    )

                    if keys:
                        await self.redis_client.delete(*keys)
                        count += len(keys)

            # Clear from memory cache
            keys_to_delete = [k for k in self.memory_cache.keys() if k.startswith(f"{namespace}:")]
            for key in keys_to_delete:
                del self.memory_cache[key]
                count += 1

            return count

        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0

    def _evict_memory_cache(self):
        """Evict expired and oldest items from memory cache"""
        current_time = time.time()

        # Remove expired items
        expired_keys = [k for k, (_, expiry) in self.memory_cache.items() if current_time >= expiry]
        for key in expired_keys:
            del self.memory_cache[key]

        # If still over limit, remove oldest items
        if len(self.memory_cache) > self.max_memory_items:
            items = sorted(self.memory_cache.items(), key=lambda x: x[1][1])  # Sort by expiry time

            # Remove 10% of items
            remove_count = len(self.memory_cache) // 10
            for key, _ in items[:remove_count]:
                del self.memory_cache[key]

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = self.cache_stats["hits"] / total_requests * 100 if total_requests > 0 else 0

        return {
            **self.cache_stats,
            "hit_rate": f"{hit_rate:.2f}%",
            "memory_items": len(self.memory_cache),
            "redis_connected": self.redis_client is not None,
        }


def cache_result(namespace: str, ttl: int = 300, key_params: Optional[List[str]] = None):
    """
    Decorator to cache function results

    Args:
        namespace: Cache namespace
        ttl: Time to live in seconds
        key_params: Parameters to include in cache key

    Usage:
        @cache_result("user_data", ttl=600)
        async def get_user_data(user_id: str):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get cache manager from app state or create new
            cache = getattr(wrapper, "_cache", None)
            if not cache:
                cache = CacheManager()
                await cache.initialize()
                wrapper._cache = cache

            # Generate cache key
            cache_key_data = {}
            if key_params:
                for param in key_params:
                    if param in kwargs:
                        cache_key_data[param] = kwargs[param]
            else:
                cache_key_data = {"args": args, "kwargs": kwargs}

            key = cache._generate_key(namespace, **cache_key_data)

            # Check cache
            cached_value = await cache.get(key)
            if cached_value is not None:
                return cached_value

            # Call function
            result = await func(*args, **kwargs)

            # Store in cache
            await cache.set(key, result, ttl)

            return result

        return wrapper

    return decorator


class QueryOptimizer:
    """Database query optimization utilities"""

    @staticmethod
    async def explain_query(
        session: AsyncSession, query: str, params: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Get query execution plan

        Args:
            session: Database session
            query: SQL query
            params: Query parameters

        Returns:
            Execution plan details
        """
        explain_query = f"EXPLAIN ANALYZE {query}"
        result = await session.execute(text(explain_query), params or {})

        plan = []
        for row in result:
            plan.append({"step": row[0]})

        return plan

    @staticmethod
    async def analyze_table(session: AsyncSession, table_name: str) -> bool:
        """
        Analyze table for query optimization

        Args:
            session: Database session
            table_name: Table to analyze

        Returns:
            Success status
        """
        try:
            await session.execute(text(f"ANALYZE {table_name}"))
            return True
        except Exception as e:
            logger.error(f"Table analysis failed: {e}")
            return False

    @staticmethod
    async def vacuum_table(session: AsyncSession, table_name: str, full: bool = False) -> bool:
        """
        Vacuum table to reclaim space

        Args:
            session: Database session
            table_name: Table to vacuum
            full: Whether to perform full vacuum

        Returns:
            Success status
        """
        try:
            vacuum_cmd = f"VACUUM {'FULL ' if full else ''}{table_name}"
            await session.execute(text(vacuum_cmd))
            return True
        except Exception as e:
            logger.error(f"Table vacuum failed: {e}")
            return False

    @staticmethod
    async def get_slow_queries(session: AsyncSession, threshold_ms: int = 1000) -> List[Dict]:
        """
        Get slow queries from PostgreSQL

        Args:
            session: Database session
            threshold_ms: Threshold in milliseconds

        Returns:
            List of slow queries
        """
        query = text(
            """
            SELECT 
                query,
                calls,
                total_exec_time,
                mean_exec_time,
                max_exec_time
            FROM pg_stat_statements
            WHERE mean_exec_time > :threshold
            ORDER BY mean_exec_time DESC
            LIMIT 20
        """
        )

        try:
            result = await session.execute(query, {"threshold": threshold_ms})

            slow_queries = []
            for row in result:
                slow_queries.append(
                    {
                        "query": row.query,
                        "calls": row.calls,
                        "total_time_ms": row.total_exec_time,
                        "mean_time_ms": row.mean_exec_time,
                        "max_time_ms": row.max_exec_time,
                    }
                )

            return slow_queries

        except Exception as e:
            logger.error(f"Failed to get slow queries: {e}")
            return []


class ConnectionPool:
    """Manages connection pooling for external services"""

    def __init__(self, max_connections: int = 10):
        """
        Initialize connection pool

        Args:
            max_connections: Maximum number of connections
        """
        self.max_connections = max_connections
        self.connections: Dict[str, List[Any]] = {}
        self.in_use: Dict[str, Set[Any]] = {}
        self.stats = {"acquired": 0, "released": 0, "created": 0, "destroyed": 0}

    async def acquire(self, service: str, factory: Callable, timeout: float = 5.0) -> Any:
        """
        Acquire connection from pool

        Args:
            service: Service name
            factory: Connection factory function
            timeout: Acquisition timeout

        Returns:
            Connection object
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            # Initialize service pool if needed
            if service not in self.connections:
                self.connections[service] = []
                self.in_use[service] = set()

            # Try to get existing connection
            if self.connections[service]:
                conn = self.connections[service].pop()
                self.in_use[service].add(conn)
                self.stats["acquired"] += 1
                return conn

            # Create new connection if under limit
            if len(self.in_use[service]) < self.max_connections:
                conn = await factory()
                self.in_use[service].add(conn)
                self.stats["created"] += 1
                self.stats["acquired"] += 1
                return conn

            # Wait and retry
            await asyncio.sleep(0.1)

        raise TimeoutError(f"Failed to acquire connection for {service}")

    async def release(self, service: str, conn: Any):
        """
        Release connection back to pool

        Args:
            service: Service name
            conn: Connection to release
        """
        if service in self.in_use and conn in self.in_use[service]:
            self.in_use[service].remove(conn)
            self.connections[service].append(conn)
            self.stats["released"] += 1

    async def destroy(self, service: str, conn: Any):
        """
        Destroy connection

        Args:
            service: Service name
            conn: Connection to destroy
        """
        if service in self.in_use and conn in self.in_use[service]:
            self.in_use[service].remove(conn)
            self.stats["destroyed"] += 1

        # Call close method if available
        if hasattr(conn, "close"):
            await conn.close()

    async def clear(self, service: Optional[str] = None):
        """Clear connections for service or all services"""
        services = [service] if service else list(self.connections.keys())

        for svc in services:
            if svc in self.connections:
                # Destroy all connections
                for conn in self.connections[svc]:
                    if hasattr(conn, "close"):
                        await conn.close()
                    self.stats["destroyed"] += 1

                for conn in self.in_use.get(svc, set()):
                    if hasattr(conn, "close"):
                        await conn.close()
                    self.stats["destroyed"] += 1

                self.connections[svc] = []
                self.in_use[svc] = set()

    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        service_stats = {}
        for service in self.connections:
            service_stats[service] = {
                "available": len(self.connections[service]),
                "in_use": len(self.in_use[service]),
            }

        return {**self.stats, "services": service_stats}


class PerformanceMonitor:
    """Monitors application performance metrics"""

    def __init__(self):
        """Initialize performance monitor"""
        self.metrics = {
            "requests": 0,
            "errors": 0,
            "response_times": [],
            "db_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }
        self.start_time = time.time()

    def record_request(self, duration: float, status_code: int):
        """Record request metrics"""
        self.metrics["requests"] += 1
        self.metrics["response_times"].append(duration)

        if status_code >= 400:
            self.metrics["errors"] += 1

        # Keep only last 1000 response times
        if len(self.metrics["response_times"]) > 1000:
            self.metrics["response_times"] = self.metrics["response_times"][-1000:]

    def record_db_query(self, duration: float):
        """Record database query"""
        self.metrics["db_queries"] += 1

    def record_cache_hit(self):
        """Record cache hit"""
        self.metrics["cache_hits"] += 1

    def record_cache_miss(self):
        """Record cache miss"""
        self.metrics["cache_misses"] += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        uptime = time.time() - self.start_time
        response_times = self.metrics["response_times"]

        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)]
            p99_response_time = sorted(response_times)[int(len(response_times) * 0.99)]
        else:
            avg_response_time = p95_response_time = p99_response_time = 0

        cache_total = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        cache_hit_rate = self.metrics["cache_hits"] / cache_total * 100 if cache_total > 0 else 0

        return {
            "uptime_seconds": uptime,
            "total_requests": self.metrics["requests"],
            "error_rate": (
                self.metrics["errors"] / self.metrics["requests"] * 100
                if self.metrics["requests"] > 0
                else 0
            ),
            "avg_response_time_ms": avg_response_time * 1000,
            "p95_response_time_ms": p95_response_time * 1000,
            "p99_response_time_ms": p99_response_time * 1000,
            "db_queries": self.metrics["db_queries"],
            "cache_hit_rate": cache_hit_rate,
            "requests_per_second": self.metrics["requests"] / uptime if uptime > 0 else 0,
        }


# Global instances
cache_manager = CacheManager()
connection_pool = ConnectionPool()
performance_monitor = PerformanceMonitor()
query_optimizer = QueryOptimizer()


# Middleware for performance monitoring
async def performance_middleware(request: Request, call_next):
    """Middleware to monitor request performance"""
    start_time = time.time()

    try:
        response = await call_next(request)
        duration = time.time() - start_time
        performance_monitor.record_request(duration, response.status_code)

        # Add performance headers
        response.headers["X-Response-Time"] = f"{duration * 1000:.2f}ms"

        return response

    except Exception as e:
        duration = time.time() - start_time
        performance_monitor.record_request(duration, 500)
        raise e


# Health check endpoint
async def performance_health_check() -> Dict[str, Any]:
    """Get performance health status"""
    metrics = performance_monitor.get_metrics()
    cache_stats = cache_manager.get_stats()
    pool_stats = connection_pool.get_stats()

    # Determine health status
    if metrics["error_rate"] > 10:
        status = "unhealthy"
    elif metrics["error_rate"] > 5 or metrics["avg_response_time_ms"] > 1000:
        status = "degraded"
    else:
        status = "healthy"

    return {
        "status": status,
        "performance_metrics": metrics,
        "cache_statistics": cache_stats,
        "connection_pool": pool_stats,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

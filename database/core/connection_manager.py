"""
Enhanced Database Connection Manager with Optimized Pool Settings
Provides high-performance connection pooling for the educational platform
"""

import asyncio
import logging
import os
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import asyncpg
import redis.asyncio as redis

logger = logging.getLogger(__name__)


@dataclass
class ConnectionConfig:
    """Database connection configuration"""

    host: str
    port: int
    user: str
    password: str
    database: str
    min_size: int = 5
    max_size: int = 20
    max_overflow: int = 40
    pool_timeout: int = 30
    pool_recycle: int = 3600
    command_timeout: int = 60


class PerformanceMonitor:
    """Monitor database performance and connection health"""

    def __init__(self):
        self.query_times: list[float] = []
        self.connection_times: list[float] = []
        self.error_count: int = 0
        self.last_reset: datetime = datetime.now()

    def record_query_time(self, duration: float):
        """Record query execution time"""
        self.query_times.append(duration)
        # Keep only last 1000 queries for memory efficiency
        if len(self.query_times) > 1000:
            self.query_times = self.query_times[-1000:]

    def record_connection_time(self, duration: float):
        """Record connection acquisition time"""
        self.connection_times.append(duration)
        if len(self.connection_times) > 1000:
            self.connection_times = self.connection_times[-1000:]

    def record_error(self):
        """Record database error"""
        self.error_count += 1

    def get_stats(self) -> dict[str, Any]:
        """Get performance statistics"""
        now = datetime.now()
        uptime = (now - self.last_reset).total_seconds()

        query_stats = {}
        if self.query_times:
            query_stats = {
                "avg_query_time": sum(self.query_times) / len(self.query_times),
                "max_query_time": max(self.query_times),
                "min_query_time": min(self.query_times),
                "total_queries": len(self.query_times),
                "slow_queries": len([t for t in self.query_times if t > 0.05]),  # > 50ms
            }

        connection_stats = {}
        if self.connection_times:
            connection_stats = {
                "avg_connection_time": sum(self.connection_times) / len(self.connection_times),
                "max_connection_time": max(self.connection_times),
                "total_connections": len(self.connection_times),
            }

        return {
            "uptime_seconds": uptime,
            "error_count": self.error_count,
            "query_stats": query_stats,
            "connection_stats": connection_stats,
            "last_reset": self.last_reset.isoformat(),
        }

    def reset_stats(self):
        """Reset performance statistics"""
        self.query_times.clear()
        self.connection_times.clear()
        self.error_count = 0
        self.last_reset = datetime.now()


class OptimizedConnectionManager:
    """High-performance database connection manager with advanced pooling"""

    def __init__(self):
        self.pools: dict[str, asyncpg.Pool] = {}
        self.configs: dict[str, ConnectionConfig] = {}
        self.monitor = PerformanceMonitor()
        self._initialized = False
        self._redis_pool: redis.ConnectionPool | None = None

        # Load configurations from environment
        self._load_configurations()

    def _load_configurations(self):
        """Load database configurations from environment variables"""

        # Main educational platform database (primary)
        self.configs["educational_platform"] = ConnectionConfig(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 5432)),
            user=os.getenv("DB_USER", "eduplatform"),
            password=os.getenv("DB_PASSWORD", "eduplatform2024"),
            database=os.getenv("DB_NAME", "educational_platform_dev"),
            min_size=5,
            max_size=20,  # Increased from 10 to 20
            max_overflow=40,  # Increased from 20 to 40
            pool_timeout=30,
            pool_recycle=3600,
            command_timeout=60,
        )

        # Additional database configurations
        self.configs["ghost_backend"] = ConnectionConfig(
            host=os.getenv("DATABASE_HOST", "localhost"),
            port=int(os.getenv("DATABASE_PORT", 5432)),
            user=os.getenv("GHOST_DB_USER", "eduplatform"),
            password=os.getenv("GHOST_DB_PASSWORD", "eduplatform2024"),
            database=os.getenv("GHOST_DB_NAME", "educational_platform_dev"),
            min_size=3,
            max_size=15,
            max_overflow=30,
        )

        self.configs["roblox_data"] = ConnectionConfig(
            host=os.getenv("DATABASE_HOST", "localhost"),
            port=int(os.getenv("DATABASE_PORT", 5432)),
            user=os.getenv("ROBLOX_DB_USER", "eduplatform"),
            password=os.getenv("ROBLOX_DB_PASSWORD", "eduplatform2024"),
            database=os.getenv("ROBLOX_DB_NAME", "educational_platform_dev"),
            min_size=2,
            max_size=10,
            max_overflow=20,
        )

        self.configs["mcp_memory"] = ConnectionConfig(
            host=os.getenv("DATABASE_HOST", "localhost"),
            port=int(os.getenv("DATABASE_PORT", 5432)),
            user=os.getenv("MCP_DB_USER", "eduplatform"),
            password=os.getenv("MCP_DB_PASSWORD", "eduplatform2024"),
            database=os.getenv("MCP_DB_NAME", "educational_platform_dev"),
            min_size=2,
            max_size=8,
            max_overflow=16,
        )

    async def initialize(self):
        """Initialize all database connection pools"""
        if self._initialized:
            return

        logger.info("Initializing optimized database connection pools...")

        # Initialize Redis for caching if available
        await self._initialize_redis()

        # Initialize database pools
        for db_name, config in self.configs.items():
            try:
                await self._create_pool(db_name, config)
                logger.info(f"✅ Database pool '{db_name}' initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize pool '{db_name}': {e}")
                # Continue with other pools even if one fails

        self._initialized = True
        logger.info("🚀 All database connection pools initialized")

    async def _initialize_redis(self):
        """Initialize Redis connection pool for caching"""
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            self._redis_pool = redis.ConnectionPool.from_url(
                redis_url, max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", 50))
            )
            logger.info("✅ Redis connection pool initialized")
        except Exception as e:
            logger.warning(f"⚠️ Redis initialization failed: {e}")
            self._redis_pool = None

    async def _create_pool(self, db_name: str, config: ConnectionConfig):
        """Create an optimized connection pool for a database"""

        # Create connection pool with optimized settings
        pool = await asyncpg.create_pool(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            database=config.database,
            min_size=config.min_size,
            max_size=config.max_size,
            command_timeout=config.command_timeout,
            # Optimized connection parameters
            server_settings={
                "application_name": f"toolboxai_{db_name}",
                "tcp_keepalives_idle": "600",
                "tcp_keepalives_interval": "30",
                "tcp_keepalives_count": "3",
                # Performance optimizations
                "work_mem": "256MB",
                "maintenance_work_mem": "1GB",
                "effective_cache_size": "4GB",
                "random_page_cost": "1.1",
                "max_parallel_workers_per_gather": "4",
            },
        )

        # Test the pool with a simple query
        async with pool.acquire() as conn:
            await conn.execute("SELECT 1")

        self.pools[db_name] = pool

    @asynccontextmanager
    async def get_connection(
        self, db_name: str = "educational_platform"
    ) -> AsyncGenerator[asyncpg.Connection, None]:
        """Get a database connection with performance monitoring"""
        if not self._initialized:
            await self.initialize()

        if db_name not in self.pools:
            raise ValueError(f"Database pool '{db_name}' not found")

        start_time = time.time()

        try:
            async with self.pools[db_name].acquire() as connection:
                connection_time = time.time() - start_time
                self.monitor.record_connection_time(connection_time)

                # Wrap connection to monitor query performance
                yield MonitoredConnection(connection, self.monitor)

        except Exception as e:
            self.monitor.record_error()
            logger.error(f"Database connection error for '{db_name}': {e}")
            raise

    async def execute_query(self, query: str, *args, db_name: str = "educational_platform") -> Any:
        """Execute a query with performance monitoring"""
        start_time = time.time()

        try:
            async with self.get_connection(db_name) as conn:
                result = await conn.fetch(query, *args)

                query_time = time.time() - start_time
                self.monitor.record_query_time(query_time)

                # Log slow queries
                if query_time > 0.05:  # 50ms threshold
                    logger.warning(
                        f"Slow query detected ({query_time*1000:.2f}ms): {query[:100]}..."
                    )

                return result

        except Exception as e:
            self.monitor.record_error()
            logger.error(f"Query execution error: {e}")
            raise

    async def get_performance_stats(self) -> dict[str, Any]:
        """Get comprehensive performance statistics"""
        stats = self.monitor.get_stats()

        # Add pool statistics
        pool_stats = {}
        for db_name, pool in self.pools.items():
            pool_stats[db_name] = {
                "size": pool.get_size(),
                "max_size": pool.get_max_size(),
                "min_size": pool.get_min_size(),
                "idle_connections": pool.get_idle_size(),
                "used_connections": pool.get_size() - pool.get_idle_size(),
            }

        stats["pool_stats"] = pool_stats
        return stats

    async def health_check(self) -> dict[str, bool]:
        """Perform health check on all database connections"""
        results = {}

        for db_name in self.pools.keys():
            try:
                async with self.get_connection(db_name) as conn:
                    await conn.execute("SELECT 1")
                results[db_name] = True
            except Exception as e:
                logger.error(f"Health check failed for '{db_name}': {e}")
                results[db_name] = False

        return results

    async def optimize_connections(self):
        """Optimize database connections and clean up idle connections"""
        logger.info("Optimizing database connections...")

        for db_name, pool in self.pools.items():
            try:
                # Get current pool statistics
                total_connections = pool.get_size()
                idle_connections = pool.get_idle_size()

                logger.info(f"Pool '{db_name}': {total_connections} total, {idle_connections} idle")

                # Optional: implement custom optimization logic here
                # For example, closing excess idle connections during low traffic

            except Exception as e:
                logger.error(f"Error optimizing pool '{db_name}': {e}")

    async def close_all(self):
        """Close all database connection pools"""
        logger.info("Closing all database connection pools...")

        for db_name, pool in self.pools.items():
            try:
                await pool.close()
                logger.info(f"✅ Pool '{db_name}' closed successfully")
            except Exception as e:
                logger.error(f"❌ Error closing pool '{db_name}': {e}")

        if self._redis_pool:
            try:
                await self._redis_pool.disconnect()
                logger.info("✅ Redis pool closed successfully")
            except Exception as e:
                logger.error(f"❌ Error closing Redis pool: {e}")

        self.pools.clear()
        self._initialized = False


class MonitoredConnection:
    """Wrapper for database connection with query monitoring"""

    def __init__(self, connection: asyncpg.Connection, monitor: PerformanceMonitor):
        self.connection = connection
        self.monitor = monitor

    async def execute(self, query: str, *args, timeout: float | None = None) -> str:
        """Execute a query with performance monitoring"""
        start_time = time.time()
        try:
            result = await self.connection.execute(query, *args, timeout=timeout)
            query_time = time.time() - start_time
            self.monitor.record_query_time(query_time)
            return result
        except Exception:
            self.monitor.record_error()
            raise

    async def fetch(self, query: str, *args, timeout: float | None = None) -> list[Any]:
        """Fetch query results with performance monitoring"""
        start_time = time.time()
        try:
            result = await self.connection.fetch(query, *args, timeout=timeout)
            query_time = time.time() - start_time
            self.monitor.record_query_time(query_time)
            return result
        except Exception:
            self.monitor.record_error()
            raise

    async def fetchrow(self, query: str, *args, timeout: float | None = None) -> Any:
        """Fetch single row with performance monitoring"""
        start_time = time.time()
        try:
            result = await self.connection.fetchrow(query, *args, timeout=timeout)
            query_time = time.time() - start_time
            self.monitor.record_query_time(query_time)
            return result
        except Exception:
            self.monitor.record_error()
            raise

    async def fetchval(self, query: str, *args, timeout: float | None = None) -> Any:
        """Fetch single value with performance monitoring"""
        start_time = time.time()
        try:
            result = await self.connection.fetchval(query, *args, timeout=timeout)
            query_time = time.time() - start_time
            self.monitor.record_query_time(query_time)
            return result
        except Exception:
            self.monitor.record_error()
            raise

    def transaction(self):
        """Start a database transaction"""
        return self.connection.transaction()


# Global connection manager instance
db_manager = OptimizedConnectionManager()


# Convenience function for health checks
async def health_check() -> dict[str, bool]:
    """Perform health check on all databases"""
    return await db_manager.health_check()


# Convenience function for performance stats
async def get_performance_stats() -> dict[str, Any]:
    """Get performance statistics"""
    return await db_manager.get_performance_stats()


# Database initialization function
async def initialize_databases():
    """Initialize all database connections"""
    await db_manager.initialize()


# Cleanup function
async def cleanup_databases():
    """Clean up all database connections"""
    await db_manager.close_all()


# Database session functions for compatibility
async def get_async_session(database: str = "educational_platform"):
    """Get async database session (compatibility function)"""
    async with db_manager.get_connection(database) as conn:
        yield conn


def get_session(database: str = "educational_platform"):
    """Get sync database session (compatibility function)"""
    # This is a placeholder for sync session support
    # In async context, use get_async_session instead
    raise NotImplementedError("Sync sessions not supported. Use get_async_session() instead.")


class RedisManager:
    """Redis connection manager with singleton pattern and retry logic"""

    _instance = None
    _redis_pool = None
    _async_redis_pool = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._retry_count = 3
            self._retry_delay = 1.0

    async def get_async_client(self) -> redis.Redis | None:
        """Get async Redis client with retry logic"""
        if self._async_redis_pool is None:
            await self._initialize_async_pool()

        if self._async_redis_pool:
            return redis.Redis(connection_pool=self._async_redis_pool)
        return None

    async def _initialize_async_pool(self):
        """Initialize async Redis connection pool with retry"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        for attempt in range(self._retry_count):
            try:
                self._async_redis_pool = redis.ConnectionPool.from_url(
                    redis_url,
                    max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", 50)),
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )

                # Test connection
                client = redis.Redis(connection_pool=self._async_redis_pool)
                await client.ping()
                logger.info("✅ Redis async connection pool initialized")
                return

            except Exception as e:
                logger.warning(f"Redis connection attempt {attempt + 1} failed: {e}")
                if attempt < self._retry_count - 1:
                    await asyncio.sleep(self._retry_delay * (2**attempt))
                else:
                    logger.error(
                        f"❌ Failed to initialize Redis after {self._retry_count} attempts"
                    )
                    self._async_redis_pool = None

    def get_sync_client(self) -> redis.Redis | None:
        """Get synchronous Redis client"""
        if self._redis_pool is None:
            self._initialize_sync_pool()

        if self._redis_pool:
            import redis as sync_redis

            return sync_redis.Redis(connection_pool=self._redis_pool)
        return None

    def _initialize_sync_pool(self):
        """Initialize synchronous Redis connection pool"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        try:
            import redis as sync_redis

            self._redis_pool = sync_redis.ConnectionPool.from_url(
                redis_url,
                max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", 50)),
                socket_connect_timeout=5,
                socket_timeout=5,
            )

            # Test connection
            client = sync_redis.Redis(connection_pool=self._redis_pool)
            client.ping()
            logger.info("✅ Redis sync connection pool initialized")

        except Exception as e:
            logger.error(f"❌ Failed to initialize sync Redis: {e}")
            self._redis_pool = None

    async def health_check(self) -> bool:
        """Check Redis connection health"""
        try:
            client = await self.get_async_client()
            if client:
                await client.ping()
                return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
        return False

    async def close(self):
        """Close all Redis connections"""
        if self._async_redis_pool:
            await self._async_redis_pool.disconnect()
            self._async_redis_pool = None

        if self._redis_pool:
            self._redis_pool.disconnect()
            self._redis_pool = None

        logger.info("Redis connections closed")


# Global Redis manager instance
redis_manager = RedisManager()


# Redis client function for compatibility
async def get_redis_client():
    """Get Redis client (compatibility function)"""
    # First try the new Redis manager
    client = await redis_manager.get_async_client()
    if client:
        return client

    # Fallback to db_manager's Redis pool
    if db_manager._redis_pool:
        return redis.Redis(connection_pool=db_manager._redis_pool)
    return None


def get_redis_client_sync():
    """Get synchronous Redis client"""
    return redis_manager.get_sync_client()

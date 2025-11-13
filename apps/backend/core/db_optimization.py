"""
Database Connection Pool Optimization
Optimizes SQLAlchemy connection pooling, implements query result caching,
and provides prepared statement patterns for frequent queries.
Target: Reduce database latency from ~50ms to <30ms
"""

import hashlib
import logging
import time
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any

from sqlalchemy import (
    text,
)
from sqlalchemy.engine.events import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import QueuePool

from apps.backend.core.cache import CacheConfig, CacheKey, cache
from apps.backend.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Optimized database configuration"""

    # Connection pool settings for high performance
    POOL_SIZE = 20  # Base connection pool size
    MAX_OVERFLOW = 30  # Additional connections beyond pool_size
    POOL_TIMEOUT = 30  # Timeout to get connection from pool
    POOL_RECYCLE = 3600  # Recycle connections after 1 hour
    POOL_PRE_PING = True  # Verify connections before use

    # Query timeout settings
    QUERY_TIMEOUT = 30  # Seconds
    SLOW_QUERY_THRESHOLD = 0.5  # Log queries taking longer than 500ms

    # Connection optimization parameters
    CONNECTION_PARAMS = {
        "command_timeout": 60,
        "server_settings": {
            "application_name": "toolboxai_backend",
            "jit": "off",  # Disable JIT for predictable performance
            "shared_preload_libraries": "pg_stat_statements",
            # Memory optimization
            "work_mem": "256MB",
            "maintenance_work_mem": "1GB",
            "effective_cache_size": "4GB",
            "random_page_cost": "1.1",  # SSD optimization
            # Connection optimization
            "tcp_keepalives_idle": "600",
            "tcp_keepalives_interval": "30",
            "tcp_keepalives_count": "3",
            # Query optimization
            "default_statistics_target": "100",
            "constraint_exclusion": "partition",
            "checkpoint_completion_target": "0.9",
        },
    }


class QueryStats:
    """Track query performance statistics"""

    def __init__(self):
        self.query_count = 0
        self.total_time = 0.0
        self.slow_queries = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.prepared_statement_usage = 0

    def record_query(
        self,
        duration: float,
        was_slow: bool = False,
        from_cache: bool = False,
        prepared: bool = False,
    ):
        self.query_count += 1
        self.total_time += duration

        if was_slow:
            self.slow_queries += 1
        if from_cache:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
        if prepared:
            self.prepared_statement_usage += 1

    @property
    def avg_query_time(self) -> float:
        return self.total_time / self.query_count if self.query_count > 0 else 0.0

    @property
    def cache_hit_rate(self) -> float:
        total_requests = self.cache_hits + self.cache_misses
        return self.cache_hits / total_requests if total_requests > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_count": self.query_count,
            "total_time": self.total_time,
            "avg_query_time_ms": self.avg_query_time * 1000,
            "slow_queries": self.slow_queries,
            "slow_query_rate": (
                self.slow_queries / self.query_count if self.query_count > 0 else 0.0
            ),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": self.cache_hit_rate,
            "prepared_statement_usage": self.prepared_statement_usage,
        }


# Global query statistics
_query_stats = QueryStats()


class OptimizedAsyncEngine:
    """Optimized async SQLAlchemy engine with connection pooling"""

    def __init__(self):
        self.engine = None
        self.session_maker = None
        self._initialized = False

    async def initialize(self):
        """Initialize the optimized database engine"""
        if self._initialized:
            return

        try:
            # Create optimized engine
            self.engine = create_async_engine(
                settings.DATABASE_URL,
                # Connection pool optimization
                poolclass=QueuePool,
                pool_size=DatabaseConfig.POOL_SIZE,
                max_overflow=DatabaseConfig.MAX_OVERFLOW,
                pool_timeout=DatabaseConfig.POOL_TIMEOUT,
                pool_recycle=DatabaseConfig.POOL_RECYCLE,
                pool_pre_ping=DatabaseConfig.POOL_PRE_PING,
                # Query optimization
                echo=False,  # Disable SQL echo in production
                echo_pool=False,
                # Connection optimization
                connect_args={
                    "server_settings": DatabaseConfig.CONNECTION_PARAMS["server_settings"]
                },
                # Async optimization
                future=True,
            )

            # Create session maker
            self.session_maker = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,  # Manual flush for better control
                autocommit=False,
            )

            # Set up event listeners for performance monitoring
            self._setup_event_listeners()

            self._initialized = True
            logger.info("Optimized database engine initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise

    def _setup_event_listeners(self):
        """Setup event listeners for monitoring"""

        @event.listens_for(self.engine.sync_engine, "before_cursor_execute")
        def receive_before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            context._query_start_time = time.time()

        @event.listens_for(self.engine.sync_engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total_time = time.time() - context._query_start_time
            is_slow = total_time > DatabaseConfig.SLOW_QUERY_THRESHOLD

            if is_slow:
                logger.warning(f"Slow query ({total_time:.3f}s): {statement[:100]}...")

            _query_stats.record_query(total_time, is_slow)

    @asynccontextmanager
    async def get_session(self):
        """Get optimized database session"""
        if not self._initialized:
            await self.initialize()

        async with self.session_maker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


# Global engine instance
_db_engine = OptimizedAsyncEngine()


class QueryCache:
    """Intelligent query result caching"""

    def __init__(self):
        self.cache = cache

    def _generate_query_key(self, query: str, params: tuple = None) -> str:
        """Generate cache key for query and parameters"""
        # Normalize query (remove extra whitespace, convert to lowercase)
        normalized_query = " ".join(query.lower().split())

        # Create hash of query + parameters
        query_hash = hashlib.sha256(normalized_query.encode()).hexdigest()[:16]

        if params:
            params_hash = hashlib.sha256(str(params).encode()).hexdigest()[:8]
            return CacheKey.generate(CacheConfig.PREFIX_QUERY, query_hash, params_hash)

        return CacheKey.generate(CacheConfig.PREFIX_QUERY, query_hash)

    async def get_cached_result(self, query: str, params: tuple = None) -> Any | None:
        """Get cached query result"""
        cache_key = self._generate_query_key(query, params)
        result = await self.cache.get(cache_key)

        if result is not None:
            _query_stats.record_query(0.001, from_cache=True)  # Minimal time for cache hit

        return result

    async def cache_result(
        self, query: str, params: tuple, result: Any, ttl: int = CacheConfig.MEDIUM_TTL
    ):
        """Cache query result"""
        cache_key = self._generate_query_key(query, params)
        await self.cache.set(cache_key, result, ttl)

    async def invalidate_pattern(self, pattern: str):
        """Invalidate cached queries matching pattern"""
        cache_pattern = f"{CacheConfig.PREFIX_QUERY}:*{pattern}*"
        return await self.cache.delete_pattern(cache_pattern)


# Global query cache
_query_cache = QueryCache()


def cached_query(ttl: int = CacheConfig.MEDIUM_TTL):
    """Decorator for caching query results"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = CacheKey.generate(CacheConfig.PREFIX_QUERY, func.__name__, *args, **kwargs)

            # Try to get from cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                _query_stats.record_query(0.001, from_cache=True)
                return cached_result

            # Execute query
            start_time = time.time()
            result = await func(*args, **kwargs)
            duration = time.time() - start_time

            # Record stats
            is_slow = duration > DatabaseConfig.SLOW_QUERY_THRESHOLD
            _query_stats.record_query(duration, is_slow)

            # Cache result
            await cache.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


class PreparedStatements:
    """Management of prepared statements for frequent queries"""

    def __init__(self):
        self.statements = {}
        self._usage_count = {}

    def register_statement(self, name: str, query: str):
        """Register a prepared statement"""
        self.statements[name] = text(query)
        self._usage_count[name] = 0
        logger.debug(f"Registered prepared statement: {name}")

    def get_statement(self, name: str):
        """Get prepared statement and track usage"""
        if name in self.statements:
            self._usage_count[name] += 1
            _query_stats.record_query(0.0, prepared=True)  # Track prepared statement usage
            return self.statements[name]
        return None

    def get_usage_stats(self) -> dict[str, int]:
        """Get usage statistics for prepared statements"""
        return self._usage_count.copy()


# Global prepared statements manager
_prepared_statements = PreparedStatements()


# Common prepared statements for frequent queries
def setup_prepared_statements():
    """Setup common prepared statements"""

    # User authentication
    _prepared_statements.register_statement(
        "get_user_by_email",
        """
        SELECT id, username, email, role, is_active, password_hash
        FROM dashboard_users
        WHERE email = :email AND is_active = true
        """,
    )

    # Dashboard queries
    _prepared_statements.register_statement(
        "get_user_dashboard_base",
        """
        SELECT u.id, u.username, u.role, u.last_login
        FROM dashboard_users u
        WHERE u.id = :user_id AND u.is_active = true
        """,
    )

    # Student progress
    _prepared_statements.register_statement(
        "get_student_progress",
        """
        SELECT xp_points, level, streak_days, total_badges, rank_position
        FROM student_progress
        WHERE student_id = :student_id
        """,
    )

    # Teacher classes
    _prepared_statements.register_statement(
        "get_teacher_classes",
        """
        SELECT c.id, c.name, c.subject, c.grade_level,
               COUNT(DISTINCT cs.student_id) as student_count
        FROM classes c
        LEFT JOIN class_students cs ON c.id = cs.class_id
        WHERE c.teacher_id = :teacher_id AND c.is_active = true
        GROUP BY c.id, c.name, c.subject, c.grade_level
        """,
    )

    # Recent assignments
    _prepared_statements.register_statement(
        "get_recent_assignments",
        """
        SELECT a.id, a.title, a.type, a.due_date, a.class_id,
               COUNT(s.id) as submissions,
               COUNT(CASE WHEN s.status = 'graded' THEN 1 END) as graded
        FROM assignments a
        LEFT JOIN submissions s ON a.id = s.assignment_id
        WHERE a.teacher_id = :teacher_id
            AND a.due_date >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY a.id, a.title, a.type, a.due_date, a.class_id
        ORDER BY a.due_date
        LIMIT 10
        """,
    )

    logger.info("Prepared statements setup complete")


class DatabaseOptimizer:
    """Database optimization utilities"""

    def __init__(self):
        self.engine = _db_engine
        self.query_cache = _query_cache

    async def execute_optimized_query(
        self,
        query: str | Any,
        params: dict[str, Any] = None,
        cache_ttl: int = CacheConfig.MEDIUM_TTL,
        use_cache: bool = True,
    ) -> Any:
        """Execute query with optimizations"""

        # Convert to string for caching if needed
        query_str = str(query) if hasattr(query, "compile") else query
        params_tuple = tuple(sorted(params.items())) if params else None

        # Check cache first if enabled
        if use_cache:
            cached_result = await self.query_cache.get_cached_result(query_str, params_tuple)
            if cached_result is not None:
                return cached_result

        # Execute query
        start_time = time.time()

        async with self.engine.get_session() as session:
            if isinstance(query, str):
                result = await session.execute(text(query), params or {})
            else:
                result = await session.execute(query, params or {})

            # Convert result to list for caching
            if hasattr(result, "fetchall"):
                rows = result.fetchall()
                # Convert to dict format for easier handling
                if rows and hasattr(rows[0], "_mapping"):
                    data = [dict(row._mapping) for row in rows]
                else:
                    data = [dict(row) for row in rows] if rows else []
            else:
                data = result

        duration = time.time() - start_time
        is_slow = duration > DatabaseConfig.SLOW_QUERY_THRESHOLD

        if is_slow:
            logger.warning(f"Slow query ({duration:.3f}s): {query_str[:100]}...")

        _query_stats.record_query(duration, is_slow)

        # Cache result if enabled
        if use_cache and data:
            await self.query_cache.cache_result(query_str, params_tuple, data, cache_ttl)

        return data

    async def execute_prepared_statement(
        self, statement_name: str, params: dict[str, Any] = None
    ) -> Any:
        """Execute prepared statement"""

        statement = _prepared_statements.get_statement(statement_name)
        if not statement:
            raise ValueError(f"Prepared statement '{statement_name}' not found")

        return await self.execute_optimized_query(
            statement,
            params,
            cache_ttl=CacheConfig.SHORT_TTL,  # Shorter TTL for prepared statements
            use_cache=True,
        )

    async def warm_query_cache(self, queries: list[tuple[str, dict[str, Any]]]):
        """Pre-warm query cache with common queries"""
        logger.info(f"Warming query cache with {len(queries)} queries")

        for query, params in queries:
            try:
                await self.execute_optimized_query(query, params, use_cache=True)
            except Exception as e:
                logger.error(f"Failed to warm cache for query: {e}")

        logger.info("Query cache warming completed")

    async def get_connection_pool_stats(self) -> dict[str, Any]:
        """Get connection pool statistics"""
        if not self.engine.engine:
            return {"status": "not_initialized"}

        pool = self.engine.engine.pool

        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "total_connections": pool.size() + pool.overflow(),
            "invalid_connections": pool.invalidated(),
        }

    def get_query_stats(self) -> dict[str, Any]:
        """Get query performance statistics"""
        return _query_stats.to_dict()

    def get_prepared_statement_stats(self) -> dict[str, Any]:
        """Get prepared statement usage statistics"""
        return {
            "registered_statements": len(_prepared_statements.statements),
            "usage_stats": _prepared_statements.get_usage_stats(),
            "total_usage": sum(_prepared_statements.get_usage_stats().values()),
        }


# Global optimizer instance
optimizer = DatabaseOptimizer()


# Convenience functions for common patterns
async def get_user_dashboard_optimized(user_id: int, role: str) -> dict[str, Any] | None:
    """Optimized dashboard data retrieval"""

    # Try to get from cache first
    from apps.backend.core.cache import get_cached_dashboard

    cached_data = await get_cached_dashboard(user_id, role)
    if cached_data:
        return cached_data

    # Use prepared statement for base user info
    user_data = await optimizer.execute_prepared_statement(
        "get_user_dashboard_base", {"user_id": user_id}
    )

    if not user_data:
        return None

    # Get role-specific data using optimized queries
    if role.lower() == "student":
        progress_data = await optimizer.execute_prepared_statement(
            "get_student_progress", {"student_id": user_id}
        )
        # Combine data...

    # Cache the result
    from apps.backend.core.cache import cache_dashboard

    dashboard_data = {"user": user_data[0]} if user_data else None
    if dashboard_data:
        await cache_dashboard(user_id, role, dashboard_data)

    return dashboard_data


async def initialize_db_optimization():
    """Initialize database optimization system"""
    try:
        await _db_engine.initialize()
        setup_prepared_statements()
        logger.info("Database optimization system initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database optimization: {e}")
        raise


async def get_db_health() -> dict[str, Any]:
    """Get database health and performance metrics"""
    try:
        pool_stats = await optimizer.get_connection_pool_stats()
        query_stats = optimizer.get_query_stats()
        prepared_stats = optimizer.get_prepared_statement_stats()

        return {
            "status": "healthy",
            "connection_pool": pool_stats,
            "query_performance": query_stats,
            "prepared_statements": prepared_stats,
            "optimization_enabled": True,
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e), "optimization_enabled": False}


# Export main interfaces
__all__ = [
    "optimizer",
    "cached_query",
    "initialize_db_optimization",
    "get_db_health",
    "get_user_dashboard_optimized",
    "_db_engine",
    "_query_cache",
    "_prepared_statements",
]

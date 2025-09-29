"""
Base Database Agent Module

This module provides the base class for all database-specific agents,
extending the BaseAgent with database-specific capabilities and
integrating with LangGraph patterns for stateful workflows.

Author: ToolboxAI Team
Created: 2025-09-16
Version: 1.0.0
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json

from core.agents.base_agent import BaseAgent, AgentConfig, AgentState, TaskResult, AgentCapability
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.pool import NullPool
import redis.asyncio as redis
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class DatabaseOperation(Enum):
    """Types of database operations."""
    QUERY = "query"
    MIGRATION = "migration"
    BACKUP = "backup"
    RESTORE = "restore"
    OPTIMIZE = "optimize"
    MONITOR = "monitor"
    SYNC = "sync"
    VALIDATE = "validate"
    REPAIR = "repair"
    CACHE = "cache"


class DatabaseHealth(Enum):
    """Database health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class DatabaseMetrics:
    """Database performance metrics."""
    query_count: int = 0
    avg_query_time: float = 0.0
    connection_pool_size: int = 0
    active_connections: int = 0
    cache_hit_ratio: float = 0.0
    replication_lag: float = 0.0
    disk_usage_percent: float = 0.0
    error_rate: float = 0.0
    last_backup: Optional[datetime] = None
    last_optimization: Optional[datetime] = None


@dataclass
class DatabaseAgentConfig(AgentConfig):
    """Configuration for database agents."""
    database_url: str = ""
    redis_url: str = ""
    max_connections: int = 20
    connection_timeout: int = 30
    query_timeout: int = 60
    enable_query_cache: bool = True
    enable_monitoring: bool = True
    monitoring_interval: int = 60
    backup_retention_days: int = 30
    auto_optimize: bool = True
    auto_repair: bool = True
    event_sourcing_enabled: bool = True
    cqrs_enabled: bool = True


class BaseDatabaseAgent(BaseAgent):
    """
    Base class for all database agents with common database operations.

    This class provides:
    - Database connection management
    - Redis cache integration
    - Performance monitoring
    - Error handling and recovery
    - Event logging
    - Health checks
    """

    def __init__(self, config: Optional[DatabaseAgentConfig] = None):
        """Initialize the base database agent."""
        if not config:
            config = DatabaseAgentConfig(
                name="BaseDatabaseAgent",
                capability=AgentCapability.ANALYSIS
            )

        super().__init__(config)
        self.db_config: DatabaseAgentConfig = config
        self.engine: Optional[AsyncEngine] = None
        self.redis_client: Optional[redis.Redis] = None
        self.metrics = DatabaseMetrics()
        self.health_status = DatabaseHealth.UNKNOWN
        self._monitoring_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize database connections and start monitoring."""
        try:
            # Initialize database engine
            if self.db_config.database_url:
                self.engine = create_async_engine(
                    self.db_config.database_url,
                    pool_size=self.db_config.max_connections,
                    max_overflow=10,
                    pool_timeout=self.db_config.connection_timeout,
                    pool_pre_ping=True,
                    poolclass=NullPool if "sqlite" in self.db_config.database_url else None
                )
                logger.info(f"{self.config.name}: Database engine initialized")

            # Initialize Redis client
            if self.db_config.redis_url:
                self.redis_client = await redis.from_url(
                    self.db_config.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                await self.redis_client.ping()
                logger.info(f"{self.config.name}: Redis connection established")

            # Start monitoring if enabled
            if self.db_config.enable_monitoring:
                self._monitoring_task = asyncio.create_task(self._monitor_loop())

            self.health_status = DatabaseHealth.HEALTHY

        except Exception as e:
            logger.error(f"{self.config.name}: Initialization failed: {e}")
            self.health_status = DatabaseHealth.CRITICAL
            raise

    async def cleanup(self):
        """Cleanup database connections and stop monitoring."""
        try:
            # Stop monitoring
            if self._monitoring_task:
                self._monitoring_task.cancel()
                try:
                    await self._monitoring_task
                except asyncio.CancelledError:
                    pass

            # Close database engine
            if self.engine:
                await self.engine.dispose()
                logger.info(f"{self.config.name}: Database engine disposed")

            # Close Redis connection
            if self.redis_client:
                await self.redis_client.close()
                logger.info(f"{self.config.name}: Redis connection closed")

        except Exception as e:
            logger.error(f"{self.config.name}: Cleanup failed: {e}")

    @asynccontextmanager
    async def get_db_session(self):
        """Get a database session context manager."""
        if not self.engine:
            raise RuntimeError("Database engine not initialized")

        async with AsyncSession(self.engine) as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Execute a database query with monitoring.

        Args:
            query: SQL query to execute
            params: Query parameters

        Returns:
            Query results as list of dictionaries
        """
        start_time = asyncio.get_event_loop().time()

        try:
            async with self.get_db_session() as session:
                result = await session.execute(query, params or {})
                rows = result.fetchall()

                # Update metrics
                query_time = asyncio.get_event_loop().time() - start_time
                self.metrics.query_count += 1
                self.metrics.avg_query_time = (
                    (self.metrics.avg_query_time * (self.metrics.query_count - 1) + query_time)
                    / self.metrics.query_count
                )

                # Convert to dictionaries
                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"{self.config.name}: Query execution failed: {e}")
            self.metrics.error_rate += 1
            raise

    async def cache_get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        if not self.redis_client:
            return None

        try:
            value = await self.redis_client.get(key)
            if value:
                self.metrics.cache_hit_ratio += 1
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"{self.config.name}: Cache get failed: {e}")
            return None

    async def cache_set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in Redis cache."""
        if not self.redis_client:
            return False

        try:
            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(value, default=str)
            )
            return True
        except Exception as e:
            logger.error(f"{self.config.name}: Cache set failed: {e}")
            return False

    async def cache_invalidate(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern."""
        if not self.redis_client:
            return 0

        try:
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                await self.redis_client.delete(*keys)

            return len(keys)
        except Exception as e:
            logger.error(f"{self.config.name}: Cache invalidation failed: {e}")
            return 0

    async def publish_event(self, event_type: str, data: Dict[str, Any]) -> bool:
        """
        Publish an event to Redis pub/sub.

        Args:
            event_type: Type of event
            data: Event data

        Returns:
            Success status
        """
        if not self.redis_client:
            return False

        try:
            event = {
                "type": event_type,
                "agent": self.config.name,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }

            await self.redis_client.publish(
                f"db:events:{event_type}",
                json.dumps(event, default=str)
            )

            return True
        except Exception as e:
            logger.error(f"{self.config.name}: Event publishing failed: {e}")
            return False

    async def check_health(self) -> DatabaseHealth:
        """
        Check database health status.

        Returns:
            Current health status
        """
        try:
            # Check database connection
            if self.engine:
                async with self.engine.connect() as conn:
                    await conn.execute("SELECT 1")

            # Check Redis connection
            if self.redis_client:
                await self.redis_client.ping()

            # Check metrics
            if self.metrics.error_rate > 0.1:  # More than 10% errors
                self.health_status = DatabaseHealth.DEGRADED
            elif self.metrics.error_rate > 0.5:  # More than 50% errors
                self.health_status = DatabaseHealth.CRITICAL
            else:
                self.health_status = DatabaseHealth.HEALTHY

            return self.health_status

        except Exception as e:
            logger.error(f"{self.config.name}: Health check failed: {e}")
            self.health_status = DatabaseHealth.CRITICAL
            return self.health_status

    async def _monitor_loop(self):
        """Background monitoring loop."""
        while True:
            try:
                await asyncio.sleep(self.db_config.monitoring_interval)

                # Perform health check
                await self.check_health()

                # Collect metrics
                if self.engine:
                    pool = self.engine.pool
                    self.metrics.connection_pool_size = pool.size()
                    self.metrics.active_connections = pool.checked_out()

                # Publish metrics
                await self.publish_event("metrics", {
                    "health": self.health_status.value,
                    "metrics": {
                        "query_count": self.metrics.query_count,
                        "avg_query_time": self.metrics.avg_query_time,
                        "connection_pool_size": self.metrics.connection_pool_size,
                        "active_connections": self.metrics.active_connections,
                        "cache_hit_ratio": self.metrics.cache_hit_ratio,
                        "error_rate": self.metrics.error_rate
                    }
                })

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"{self.config.name}: Monitoring error: {e}")

    async def _process_task(self, state: "AgentState") -> Any:
        """
        Process a database task.

        This method should be overridden by specific database agents.

        Args:
            state: Current agent state

        Returns:
            Task result
        """
        task = state.get("task", "")
        operation = state.get("operation", DatabaseOperation.QUERY)

        logger.info(f"{self.config.name}: Processing {operation.value} task: {task}")

        # Default implementation
        return TaskResult(
            success=True,
            data={
                "agent": self.config.name,
                "task": task,
                "operation": operation.value,
                "status": "completed"
            },
            metadata={
                "timestamp": datetime.utcnow().isoformat(),
                "health": self.health_status.value
            }
        )

    async def analyze_performance(self) -> Dict[str, Any]:
        """
        Analyze database performance.

        Returns:
            Performance analysis results
        """
        analysis = {
            "timestamp": datetime.utcnow().isoformat(),
            "health": self.health_status.value,
            "metrics": {
                "query_performance": {
                    "total_queries": self.metrics.query_count,
                    "avg_time_ms": self.metrics.avg_query_time * 1000
                },
                "connection_pool": {
                    "size": self.metrics.connection_pool_size,
                    "active": self.metrics.active_connections,
                    "utilization": (
                        self.metrics.active_connections / self.metrics.connection_pool_size * 100
                        if self.metrics.connection_pool_size > 0 else 0
                    )
                },
                "cache": {
                    "hit_ratio": self.metrics.cache_hit_ratio
                },
                "reliability": {
                    "error_rate": self.metrics.error_rate,
                    "uptime": "99.9%"  # Placeholder
                }
            },
            "recommendations": []
        }

        # Add recommendations based on metrics
        if self.metrics.avg_query_time > 1.0:
            analysis["recommendations"].append("Consider query optimization")

        if self.metrics.cache_hit_ratio < 0.8:
            analysis["recommendations"].append("Improve cache utilization")

        if self.metrics.error_rate > 0.01:
            analysis["recommendations"].append("Investigate error sources")

        return analysis
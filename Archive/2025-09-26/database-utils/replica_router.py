"""
Database Read Replica Router

Intelligently routes database queries to read replicas or primary based on:
- Query type (read vs write)
- Consistency requirements
- Replica health and lag
- Load distribution
"""

import asyncio
import logging
import random
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Optional, TypeVar

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ConsistencyLevel(Enum):
    """Consistency levels for read queries"""
    EVENTUAL = "eventual"  # Can use any replica
    BOUNDED_STALENESS = "bounded_staleness"  # Replica lag < threshold
    STRONG = "strong"  # Must use primary
    SESSION = "session"  # Sticky to last write source


class LoadBalancingStrategy(Enum):
    """Strategies for distributing load among replicas"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_RESPONSE_TIME = "weighted_response_time"
    RANDOM = "random"
    STICKY = "sticky"


@dataclass
class ReplicaHealth:
    """Health metrics for a database replica"""
    hostname: str
    is_healthy: bool = True
    lag_seconds: float = 0.0
    active_connections: int = 0
    average_query_time: float = 0.0
    last_health_check: datetime = field(default_factory=datetime.utcnow)
    consecutive_failures: int = 0
    weight: float = 1.0  # For weighted load balancing


@dataclass
class QueryMetrics:
    """Metrics for query routing decisions"""
    query_count: int = 0
    cache_hits: int = 0
    primary_routes: int = 0
    replica_routes: int = 0
    failed_routes: int = 0
    average_routing_time: float = 0.0


class ReplicaRouter:
    """Routes database queries to appropriate replicas or primary"""

    def __init__(
        self,
        primary_url: str,
        replica_urls: list[str],
        max_replica_lag_seconds: float = 5.0,
        health_check_interval: int = 30,
        strategy: LoadBalancingStrategy = LoadBalancingStrategy.WEIGHTED_RESPONSE_TIME,
        enable_query_caching: bool = True,
        pool_size: int = 20,
        max_overflow: int = 10
    ):
        self.primary_url = primary_url
        self.replica_urls = replica_urls
        self.max_replica_lag = max_replica_lag_seconds
        self.health_check_interval = health_check_interval
        self.strategy = strategy
        self.enable_caching = enable_query_caching

        # Create engines
        self.primary_engine = self._create_engine(primary_url, pool_size, max_overflow)
        self.replica_engines = {
            url: self._create_engine(url, pool_size, max_overflow)
            for url in replica_urls
        }

        # Health tracking
        self.replica_health: dict[str, ReplicaHealth] = {
            url: ReplicaHealth(hostname=self._extract_hostname(url))
            for url in replica_urls
        }

        # Session tracking for consistency
        self.session_affinity: dict[str, str] = {}
        self.write_timestamps: dict[str, datetime] = {}

        # Metrics
        self.metrics = QueryMetrics()

        # Round-robin counter
        self.round_robin_counter = 0

        # Start health monitoring
        self.health_check_task: Optional[asyncio.Task] = None

    def _create_engine(self, url: str, pool_size: int, max_overflow: int) -> AsyncEngine:
        """Create async engine with optimized pooling"""
        return create_async_engine(
            url,
            echo=False,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_use_lifo=True,  # Better for connection reuse
            connect_args={
                "server_settings": {
                    "application_name": "replica_router",
                    "jit": "off"  # Disable JIT for more predictable performance
                },
                "command_timeout": 30,
                "connect_timeout": 5,
            }
        )

    def _extract_hostname(self, url: str) -> str:
        """Extract hostname from database URL"""
        # Simple extraction - in production use proper URL parsing
        parts = url.split("@")[-1].split("/")[0]
        return parts.split(":")[0]

    async def start(self):
        """Start health monitoring"""
        self.health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("Replica router started with %d replicas", len(self.replica_urls))

    async def stop(self):
        """Stop health monitoring and close connections"""
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass

        # Close all engines
        await self.primary_engine.dispose()
        for engine in self.replica_engines.values():
            await engine.dispose()

        logger.info("Replica router stopped")

    async def _health_check_loop(self):
        """Continuously monitor replica health"""
        while True:
            try:
                await self._check_all_replicas()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in health check loop: %s", e)
                await asyncio.sleep(5)

    async def _check_all_replicas(self):
        """Check health of all replicas"""
        tasks = [
            self._check_replica_health(url)
            for url in self.replica_urls
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _check_replica_health(self, replica_url: str):
        """Check health and lag of a specific replica"""
        health = self.replica_health[replica_url]
        engine = self.replica_engines[replica_url]

        try:
            async with engine.connect() as conn:
                # Check basic connectivity
                result = await conn.execute(text("SELECT 1"))
                result.scalar()

                # Check replication lag (PostgreSQL specific)
                lag_query = text("""
                    SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp()))
                    AS replication_lag
                """)
                lag_result = await conn.execute(lag_query)
                lag = lag_result.scalar()

                # Get connection count
                conn_query = text("""
                    SELECT count(*) FROM pg_stat_activity
                    WHERE state != 'idle' AND datname = current_database()
                """)
                conn_result = await conn.execute(conn_query)
                active_conns = conn_result.scalar()

                # Update health metrics
                health.is_healthy = True
                health.lag_seconds = float(lag or 0)
                health.active_connections = int(active_conns or 0)
                health.last_health_check = datetime.utcnow()
                health.consecutive_failures = 0

                # Adjust weight based on lag and connections
                if health.lag_seconds > self.max_replica_lag:
                    health.weight = 0.1  # Heavily deprioritize
                else:
                    # Weight based on lag and connection count
                    lag_factor = 1.0 - (health.lag_seconds / self.max_replica_lag)
                    conn_factor = max(0.1, 1.0 - (health.active_connections / 100))
                    health.weight = lag_factor * conn_factor

                logger.debug(
                    "Replica %s health: lag=%.2fs, connections=%d, weight=%.2f",
                    health.hostname, health.lag_seconds, health.active_connections, health.weight
                )

        except Exception as e:
            health.consecutive_failures += 1
            if health.consecutive_failures >= 3:
                health.is_healthy = False
                health.weight = 0
                logger.error("Replica %s marked unhealthy after %d failures: %s",
                           health.hostname, health.consecutive_failures, e)
            else:
                logger.warning("Health check failed for replica %s: %s", health.hostname, e)

    def _select_replica(
        self,
        consistency: ConsistencyLevel,
        session_id: Optional[str] = None
    ) -> Optional[str]:
        """Select the best replica based on strategy and consistency requirements"""

        # Strong consistency always uses primary
        if consistency == ConsistencyLevel.STRONG:
            return None

        # Session consistency checks for recent writes
        if consistency == ConsistencyLevel.SESSION and session_id:
            if session_id in self.write_timestamps:
                write_time = self.write_timestamps[session_id]
                if datetime.utcnow() - write_time < timedelta(seconds=5):
                    return None  # Use primary for recent writes

        # Get healthy replicas
        healthy_replicas = [
            url for url, health in self.replica_health.items()
            if health.is_healthy and health.weight > 0
        ]

        if not healthy_replicas:
            logger.warning("No healthy replicas available, using primary")
            return None

        # Apply bounded staleness filter
        if consistency == ConsistencyLevel.BOUNDED_STALENESS:
            healthy_replicas = [
                url for url in healthy_replicas
                if self.replica_health[url].lag_seconds <= self.max_replica_lag
            ]
            if not healthy_replicas:
                return None

        # Select based on strategy
        return self._apply_strategy(healthy_replicas, session_id)

    def _apply_strategy(
        self,
        replicas: list[str],
        session_id: Optional[str]
    ) -> str:
        """Apply load balancing strategy to select replica"""

        if self.strategy == LoadBalancingStrategy.RANDOM:
            return random.choice(replicas)

        elif self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            selected = replicas[self.round_robin_counter % len(replicas)]
            self.round_robin_counter += 1
            return selected

        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return min(
                replicas,
                key=lambda r: self.replica_health[r].active_connections
            )

        elif self.strategy == LoadBalancingStrategy.WEIGHTED_RESPONSE_TIME:
            # Select based on weights
            weights = [self.replica_health[r].weight for r in replicas]
            total_weight = sum(weights)
            if total_weight == 0:
                return random.choice(replicas)

            probabilities = [w / total_weight for w in weights]
            return random.choices(replicas, weights=probabilities)[0]

        elif self.strategy == LoadBalancingStrategy.STICKY and session_id:
            # Stick to previously used replica if healthy
            if session_id in self.session_affinity:
                preferred = self.session_affinity[session_id]
                if preferred in replicas:
                    return preferred

            # Select new replica and remember it
            selected = random.choice(replicas)
            self.session_affinity[session_id] = selected
            return selected

        return random.choice(replicas)

    @asynccontextmanager
    async def get_session(
        self,
        consistency: ConsistencyLevel = ConsistencyLevel.EVENTUAL,
        session_id: Optional[str] = None,
        for_write: bool = False
    ):
        """Get a database session with appropriate routing"""
        start_time = time.time()

        # Determine target
        if for_write:
            engine = self.primary_engine
            target = "primary"
            self.metrics.primary_routes += 1

            # Track write for session consistency
            if session_id:
                self.write_timestamps[session_id] = datetime.utcnow()
        else:
            replica_url = self._select_replica(consistency, session_id)
            if replica_url:
                engine = self.replica_engines[replica_url]
                target = f"replica:{self.replica_health[replica_url].hostname}"
                self.metrics.replica_routes += 1
            else:
                engine = self.primary_engine
                target = "primary"
                self.metrics.primary_routes += 1

        # Create session
        async_session = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        async with async_session() as session:
            try:
                # Add routing metadata to session
                session.info["routed_to"] = target
                session.info["consistency"] = consistency.value

                yield session

                # Update metrics
                self.metrics.query_count += 1
                routing_time = time.time() - start_time
                self.metrics.average_routing_time = (
                    (self.metrics.average_routing_time * (self.metrics.query_count - 1) + routing_time)
                    / self.metrics.query_count
                )

                logger.debug("Routed query to %s (consistency=%s, time=%.3fs)",
                           target, consistency.value, routing_time)

            except Exception as e:
                self.metrics.failed_routes += 1
                logger.error("Session error with %s: %s", target, e)
                raise

    def get_metrics(self) -> dict:
        """Get routing metrics"""
        total = self.metrics.query_count or 1
        return {
            "total_queries": self.metrics.query_count,
            "primary_routes": self.metrics.primary_routes,
            "replica_routes": self.metrics.replica_routes,
            "failed_routes": self.metrics.failed_routes,
            "primary_percentage": (self.metrics.primary_routes / total) * 100,
            "replica_percentage": (self.metrics.replica_routes / total) * 100,
            "average_routing_time_ms": self.metrics.average_routing_time * 1000,
            "healthy_replicas": sum(
                1 for h in self.replica_health.values() if h.is_healthy
            ),
            "replica_health": {
                h.hostname: {
                    "healthy": h.is_healthy,
                    "lag_seconds": h.lag_seconds,
                    "connections": h.active_connections,
                    "weight": h.weight
                }
                for h in self.replica_health.values()
            }
        }


# Singleton instance management
_router_instance: Optional[ReplicaRouter] = None


def init_replica_router(
    primary_url: str,
    replica_urls: list[str],
    **kwargs
) -> ReplicaRouter:
    """Initialize the global replica router instance"""
    global _router_instance
    _router_instance = ReplicaRouter(primary_url, replica_urls, **kwargs)
    return _router_instance


def get_replica_router() -> Optional[ReplicaRouter]:
    """Get the global replica router instance"""
    return _router_instance


# Decorator for automatic read routing
def read_replica(consistency: ConsistencyLevel = ConsistencyLevel.EVENTUAL):
    """Decorator to automatically route reads to replicas"""
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            router = get_replica_router()
            if not router:
                # Fallback to original function if router not initialized
                return await func(*args, **kwargs)

            # Extract session_id if available
            session_id = kwargs.get("session_id")

            async with router.get_session(
                consistency=consistency,
                session_id=session_id,
                for_write=False
            ) as session:
                kwargs["session"] = session
                return await func(*args, **kwargs)

        return wrapper
    return decorator
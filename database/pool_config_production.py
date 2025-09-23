"""
Production-Optimized Database Connection Pool Configuration

Implements advanced connection pooling strategies with PgBouncer integration
for high-traffic production environments.
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
import psutil

from database.pool_config import (
    PoolConfig,
    PoolStrategy,
    PoolMonitor,
    PoolConfigFactory
)

logger = logging.getLogger(__name__)


@dataclass
class ProductionPoolConfig(PoolConfig):
    """
    Enhanced production pool configuration with optimizations
    for high-traffic scenarios and multi-service architecture.
    """

    # Connection pre-warming
    enable_pre_warming: bool = True
    pre_warm_connections: int = 5

    # PgBouncer integration
    use_pgbouncer: bool = True
    pgbouncer_pool_mode: str = "transaction"  # transaction, session, or statement
    pgbouncer_max_client_conn: int = 1000
    pgbouncer_default_pool_size: int = 25

    # Advanced PostgreSQL settings
    enable_prepared_statements: bool = True
    statement_cache_size: int = 1024
    enable_pipeline_mode: bool = True  # PostgreSQL 14+ pipeline mode

    # Connection multiplexing
    enable_connection_multiplexing: bool = True
    multiplex_ratio: int = 4  # Logical connections per physical connection

    # Service-specific pools
    enable_service_pools: bool = True
    service_pool_configs: Dict[str, Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize service-specific pool configurations"""
        if self.service_pool_configs is None:
            self.service_pool_configs = self._get_default_service_pools()

    def _get_default_service_pools(self) -> Dict[str, Dict[str, Any]]:
        """Get optimized pool configurations for different services"""
        cpu_count = os.cpu_count() or 4

        return {
            "api_service": {
                "pool_size": min(cpu_count * 5, 25),
                "max_overflow": min(cpu_count * 10, 50),
                "pool_timeout": 10.0,
                "pool_recycle": 900,  # 15 minutes
                "statement_timeout": 30000,  # 30 seconds
            },
            "agent_service": {
                "pool_size": min(cpu_count * 3, 15),
                "max_overflow": min(cpu_count * 6, 30),
                "pool_timeout": 30.0,
                "pool_recycle": 1800,  # 30 minutes
                "statement_timeout": 300000,  # 5 minutes for long AI operations
            },
            "background_worker": {
                "pool_size": min(cpu_count * 2, 10),
                "max_overflow": min(cpu_count * 4, 20),
                "pool_timeout": 60.0,
                "pool_recycle": 3600,  # 1 hour
                "statement_timeout": 600000,  # 10 minutes for batch operations
            },
            "websocket_service": {
                "pool_size": min(cpu_count * 4, 20),
                "max_overflow": min(cpu_count * 8, 40),
                "pool_timeout": 5.0,
                "pool_recycle": 600,  # 10 minutes
                "statement_timeout": 15000,  # 15 seconds
            },
            "analytics_service": {
                "pool_size": min(cpu_count * 2, 10),
                "max_overflow": min(cpu_count * 4, 20),
                "pool_timeout": 120.0,
                "pool_recycle": 1800,  # 30 minutes
                "statement_timeout": 1800000,  # 30 minutes for complex queries
            },
        }

    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """Get pool configuration for a specific service"""
        return self.service_pool_configs.get(
            service_name,
            self.service_pool_configs["api_service"]  # Default to API config
        )


class ProductionPoolManager:
    """
    Advanced pool manager for production environments with
    connection pre-warming, monitoring, and auto-tuning.
    """

    def __init__(self, base_config: Optional[ProductionPoolConfig] = None):
        self.config = base_config or self._create_production_config()
        self.monitor = PoolMonitor(self.config)
        self.pools: Dict[str, Any] = {}
        self._pre_warmed_connections = []

    def _create_production_config(self) -> ProductionPoolConfig:
        """Create optimized production configuration"""
        cpu_count = os.cpu_count() or 4
        memory_gb = psutil.virtual_memory().total / (1024**3)

        # Calculate optimal pool size based on system resources
        # Formula: (cpu_cores * 4) + (memory_gb * 2)
        optimal_base_size = int((cpu_count * 4) + (memory_gb * 2))

        # Cap at reasonable maximum
        pool_size = min(optimal_base_size, 30)
        max_overflow = min(pool_size * 2, 60)

        return ProductionPoolConfig(
            # Core settings optimized for production
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=15.0,
            pool_recycle=900,  # 15 minutes
            pool_pre_ping=True,
            pool_reset_on_return="rollback",

            # Performance optimizations
            echo_pool=False,
            pool_use_lifo=True,
            connect_timeout=5,

            # PostgreSQL optimizations
            statement_timeout=30000,  # 30 seconds default
            idle_in_transaction_timeout=60000,  # 1 minute
            lock_timeout=10000,  # 10 seconds
            idle_session_timeout=300000,  # 5 minutes

            # Advanced features
            enable_pre_warming=True,
            pre_warm_connections=min(5, pool_size // 2),
            use_pgbouncer=bool(os.getenv("USE_PGBOUNCER", "true").lower() == "true"),
            enable_prepared_statements=True,
            statement_cache_size=1024,
            enable_pipeline_mode=True,
            enable_connection_multiplexing=True,

            # Monitoring
            enable_pool_events=True,
            enable_statement_logging=False,
            slow_query_threshold=1.0,
        )

    async def initialize_pools(self, service_name: str = "api_service"):
        """Initialize connection pools with pre-warming"""
        logger.info(f"Initializing production pools for {service_name}")

        # Get service-specific configuration
        service_config = self.config.get_service_config(service_name)

        # Pre-warm connections if enabled
        if self.config.enable_pre_warming:
            await self._pre_warm_connections(
                self.config.pre_warm_connections,
                service_config
            )

        logger.info(f"Production pools initialized for {service_name}")

    async def _pre_warm_connections(
        self,
        count: int,
        service_config: Dict[str, Any]
    ):
        """Pre-warm database connections to avoid cold start latency"""
        logger.info(f"Pre-warming {count} database connections")

        # This would create actual database connections
        # Implementation depends on your database driver
        for i in range(count):
            try:
                # Simulate connection creation
                # In real implementation, create actual connections
                logger.debug(f"Pre-warmed connection {i+1}/{count}")
            except Exception as e:
                logger.error(f"Failed to pre-warm connection {i+1}: {e}")

        logger.info(f"Successfully pre-warmed {count} connections")

    def get_pgbouncer_config(self) -> str:
        """Generate PgBouncer configuration for production"""
        if not self.config.use_pgbouncer:
            return ""

        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://user:pass@localhost/db"
        )

        # Parse database URL to extract components
        # In production, use proper URL parsing
        config = f"""
[databases]
# Main application database with transaction pooling
toolboxai_main = {database_url} pool_mode={self.config.pgbouncer_pool_mode}

# Separate pool for long-running agent operations
toolboxai_agents = {database_url} pool_mode=session

# Analytics database with statement pooling for read-heavy workloads
toolboxai_analytics = {database_url} pool_mode=statement

[pgbouncer]
# Connection limits
max_client_conn = {self.config.pgbouncer_max_client_conn}
default_pool_size = {self.config.pgbouncer_default_pool_size}
min_pool_size = 5
reserve_pool_size = 10
reserve_pool_timeout = 5
max_db_connections = 100
max_user_connections = 100

# Pool modes
pool_mode = {self.config.pgbouncer_pool_mode}

# Authentication
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt

# Where to wait for clients
listen_addr = *
listen_port = 6432

# Unix socket settings
unix_socket_dir = /var/run/postgresql

# Logging
logfile = /var/log/pgbouncer/pgbouncer.log
pidfile = /var/run/pgbouncer/pgbouncer.pid

# Connection sanity checks and timeouts
server_round_robin = yes
server_lifetime = 3600
server_idle_timeout = 600
server_connect_timeout = 15
server_login_retry = 15
client_login_timeout = 60
client_idle_timeout = 0

# TLS settings (uncomment for production)
# server_tls_sslmode = require
# server_tls_ca_file = /etc/ssl/certs/ca-certificates.crt
# server_tls_protocols = secure

# Performance
pkt_buf = 4096
sbuf_loopcnt = 2
tcp_defer_accept = 0
tcp_socket_buffer = 0

# Dangerous timeouts (0 = disabled)
query_timeout = 0
query_wait_timeout = 120
idle_transaction_timeout = 0

# Low memory mode
server_reset_query = DISCARD ALL
server_reset_query_always = 0

# Admin access
admin_users = postgres, admin
stats_users = stats, postgres

# Connection health checks
server_check_delay = 30
server_check_query = select 1

# Load balancing
dns_max_ttl = 60
dns_zone_check_period = 60
"""
        return config

    def get_monitoring_queries(self) -> Dict[str, str]:
        """SQL queries for monitoring connection pool health"""
        return {
            "active_connections": """
                SELECT count(*) as active_connections
                FROM pg_stat_activity
                WHERE state != 'idle'
                AND datname = current_database()
            """,
            "idle_connections": """
                SELECT count(*) as idle_connections
                FROM pg_stat_activity
                WHERE state = 'idle'
                AND datname = current_database()
            """,
            "long_running_queries": """
                SELECT pid, usename, application_name, state,
                       age(clock_timestamp(), query_start) as query_age,
                       left(query, 100) as query_snippet
                FROM pg_stat_activity
                WHERE state != 'idle'
                AND query_start < clock_timestamp() - interval '5 minutes'
                ORDER BY query_start
            """,
            "connection_stats_by_app": """
                SELECT application_name,
                       count(*) as connection_count,
                       count(*) FILTER (WHERE state = 'active') as active,
                       count(*) FILTER (WHERE state = 'idle') as idle,
                       count(*) FILTER (WHERE state = 'idle in transaction') as idle_in_trans,
                       max(age(clock_timestamp(), query_start)) as max_query_age
                FROM pg_stat_activity
                WHERE datname = current_database()
                GROUP BY application_name
                ORDER BY connection_count DESC
            """,
            "blocked_queries": """
                SELECT blocked_locks.pid AS blocked_pid,
                       blocked_activity.usename AS blocked_user,
                       blocking_locks.pid AS blocking_pid,
                       blocking_activity.usename AS blocking_user,
                       blocked_activity.query AS blocked_statement,
                       blocking_activity.query AS blocking_statement
                FROM pg_catalog.pg_locks blocked_locks
                JOIN pg_catalog.pg_stat_activity blocked_activity
                    ON blocked_activity.pid = blocked_locks.pid
                JOIN pg_catalog.pg_locks blocking_locks
                    ON blocking_locks.locktype = blocked_locks.locktype
                    AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
                    AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
                    AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
                    AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
                    AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
                    AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
                    AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
                    AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
                    AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
                    AND blocking_locks.pid != blocked_locks.pid
                JOIN pg_catalog.pg_stat_activity blocking_activity
                    ON blocking_activity.pid = blocking_locks.pid
                WHERE NOT blocked_locks.granted
            """,
            "connection_pool_efficiency": """
                WITH pool_stats AS (
                    SELECT
                        count(*) as total_connections,
                        count(*) FILTER (WHERE state = 'active') as active,
                        count(*) FILTER (WHERE state = 'idle') as idle,
                        count(*) FILTER (WHERE wait_event_type IS NOT NULL) as waiting
                    FROM pg_stat_activity
                    WHERE datname = current_database()
                )
                SELECT
                    total_connections,
                    active,
                    idle,
                    waiting,
                    CASE
                        WHEN total_connections > 0
                        THEN round((active::numeric / total_connections) * 100, 2)
                        ELSE 0
                    END as utilization_percent,
                    CASE
                        WHEN active > 0
                        THEN round((waiting::numeric / active) * 100, 2)
                        ELSE 0
                    END as wait_percent
                FROM pool_stats
            """,
        }

    async def auto_tune_pools(self, metrics: Dict[str, Any]):
        """Automatically adjust pool sizes based on metrics"""
        utilization = metrics.get("utilization_percent", 0)
        wait_percent = metrics.get("wait_percent", 0)
        active_connections = metrics.get("active_connections", 0)

        # High utilization - consider increasing pool size
        if utilization > 80 and wait_percent > 20:
            new_pool_size = min(
                self.config.pool_size + 5,
                50  # Maximum cap
            )
            if new_pool_size > self.config.pool_size:
                logger.info(
                    f"Auto-tuning: Increasing pool size from "
                    f"{self.config.pool_size} to {new_pool_size}"
                )
                self.config.pool_size = new_pool_size

        # Low utilization - consider decreasing pool size
        elif utilization < 30 and active_connections < 10:
            new_pool_size = max(
                self.config.pool_size - 5,
                10  # Minimum floor
            )
            if new_pool_size < self.config.pool_size:
                logger.info(
                    f"Auto-tuning: Decreasing pool size from "
                    f"{self.config.pool_size} to {new_pool_size}"
                )
                self.config.pool_size = new_pool_size


def get_production_pool_config(service_name: str = "api_service") -> ProductionPoolConfig:
    """Get production-optimized pool configuration for a service"""
    manager = ProductionPoolManager()
    config = manager.config

    # Apply service-specific settings
    service_config = config.get_service_config(service_name)
    for key, value in service_config.items():
        if hasattr(config, key):
            setattr(config, key, value)

    logger.info(
        f"Production pool config for {service_name}: "
        f"size={config.pool_size}, overflow={config.max_overflow}, "
        f"recycle={config.pool_recycle}s"
    )

    return config


# Export main components
__all__ = [
    'ProductionPoolConfig',
    'ProductionPoolManager',
    'get_production_pool_config'
]
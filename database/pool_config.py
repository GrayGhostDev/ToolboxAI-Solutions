"""
Database Connection Pool Configuration for SQLAlchemy 2.0+ and PostgreSQL 16+

Implements optimized connection pooling following 2025 best practices
with proper sizing, monitoring, and performance tuning.

References:
- https://docs.sqlalchemy.org/en/20/core/pooling.html
- https://www.postgresql.org/docs/current/runtime-config-connection.html
- https://www.postgresql.org/docs/current/runtime-config-resource.html
- https://docs.sqlalchemy.org/en/20/core/events.html#pool-events

Last Updated: January 2025
"""

import os
import logging
import time
import json
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
try:
    import psutil  # For system resource monitoring
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)

class PoolStrategy(Enum):
    """Connection pool strategies for different scenarios"""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    HIGH_TRAFFIC = "high_traffic"
    MICROSERVICE = "microservice"
    TESTING = "testing"

@dataclass
class PoolConfig:
    """
    Database connection pool configuration following SQLAlchemy 2.0+ best practices
    and PostgreSQL 16+ recommendations for 2025.
    """
    
    # Core pool settings (SQLAlchemy 2.0 recommendations)
    pool_size: int = 10  # Number of persistent connections
    max_overflow: int = 20  # Maximum overflow connections
    pool_timeout: float = 30.0  # Seconds to wait for connection
    pool_recycle: int = 1800  # Recycle connections after 30 minutes (PostgreSQL recommendation)
    pool_pre_ping: bool = True  # Test connections before use (essential for cloud databases)
    
    # Performance settings (SQLAlchemy 2.0+ optimizations)
    echo_pool: bool = False  # Log pool checkouts/checkins
    pool_use_lifo: bool = True  # LIFO recommended for better connection reuse
    connect_timeout: int = 10  # Connection establishment timeout
    
    # PostgreSQL 16+ specific settings
    statement_timeout: int = 30000  # Query timeout in milliseconds
    idle_in_transaction_timeout: int = 60000  # Idle transaction timeout
    lock_timeout: int = 10000  # Lock acquisition timeout (new in PG 16)
    idle_session_timeout: int = 600000  # Idle session timeout - 10 minutes
    
    # Resource limits (based on PostgreSQL best practices)
    max_connections_per_worker: int = 5  # Per worker/thread limit
    connection_lifetime: int = 3600  # Maximum connection lifetime (1 hour)
    
    # SQLAlchemy 2.0 async settings
    async_pool_class: str = "AsyncAdaptedQueuePool"  # Default async pool class
    async_pool_use_read_write_split: bool = False  # Enable read/write splitting
    
    # Connection validation (SQLAlchemy 2.0)
    pool_reset_on_return: str = "rollback"  # rollback, commit, or None
    pool_pre_ping_timeout: float = 5.0  # Timeout for pre-ping check
    
    # PostgreSQL prepared statements (performance optimization)
    prepared_statement_cache_size: int = 512  # Number of prepared statements to cache
    jit: str = "off"  # JIT compilation (off for consistent performance)
    
    # Monitoring and observability
    enable_pool_events: bool = True  # Enable SQLAlchemy pool events
    enable_statement_logging: bool = False  # Log all SQL statements
    slow_query_threshold: float = 1.0  # Threshold for slow query logging (seconds)
    
    def to_engine_kwargs(self) -> Dict[str, Any]:
        """
        Convert to SQLAlchemy 2.0 engine kwargs with PostgreSQL 16+ optimizations
        Following psycopg3 documentation: https://www.psycopg.org/psycopg3/docs/
        """
        # Build PostgreSQL options string for server settings
        options_parts = [
            f"-c application_name=toolboxai",
            f"-c jit={self.jit}",
            f"-c statement_timeout={self.statement_timeout}",
            f"-c lock_timeout={self.lock_timeout}",
            f"-c idle_in_transaction_session_timeout={self.idle_in_transaction_timeout}",
            f"-c idle_session_timeout={self.idle_session_timeout}",
            f"-c default_statistics_target=100",
            f"-c random_page_cost=1.1",
        ]
        options_string = " ".join(options_parts)
        
        return {
            # Core pool settings (SQLAlchemy 2.0)
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "pool_pre_ping": self.pool_pre_ping,
            "pool_reset_on_return": self.pool_reset_on_return,
            
            # Performance settings
            "echo_pool": self.echo_pool,
            "pool_use_lifo": self.pool_use_lifo,
            
            # PostgreSQL connection arguments for psycopg2/psycopg3
            "connect_args": {
                "connect_timeout": self.connect_timeout,
                "options": options_string,
                # For psycopg3, we can use prepare_threshold
                "prepare_threshold": 5,  # Use prepared statements after 5 executions
            },
            
            # SQLAlchemy 2.0 execution options
            "execution_options": {
                "isolation_level": "READ COMMITTED",  # PostgreSQL default
                "postgresql_readonly": False,
                "postgresql_deferrable": False,
                "stream_results": False,  # Set to True for large result sets
                "max_row_buffer": 1000,
            }
        }
    
    def to_async_engine_kwargs(self) -> Dict[str, Any]:
        """
        Convert to AsyncEngine kwargs for SQLAlchemy 2.0 with asyncpg driver
        Following asyncpg documentation: https://magicstack.github.io/asyncpg/current/
        """
        return {
            # Core pool settings for SQLAlchemy AsyncEngine
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "pool_pre_ping": self.pool_pre_ping,
            "pool_reset_on_return": self.pool_reset_on_return,
            
            # Performance settings
            "echo_pool": self.echo_pool,
            "pool_use_lifo": self.pool_use_lifo,
            
            # Asyncpg specific connection arguments
            "connect_args": {
                # Server settings for asyncpg (passed as dict)
                "server_settings": {
                    "application_name": "toolboxai_async",
                    "jit": self.jit,
                    "statement_timeout": f"{self.statement_timeout}ms",
                    "lock_timeout": f"{self.lock_timeout}ms",
                    "idle_in_transaction_session_timeout": f"{self.idle_in_transaction_timeout}ms",
                },
                # Connection timeouts
                "timeout": self.connect_timeout,
                "command_timeout": self.connect_timeout,
                
                # Prepared statement cache (asyncpg feature)
                "statement_cache_size": self.prepared_statement_cache_size,
                "max_cached_statement_lifetime": 300,  # 5 minutes
            },
            
            # Async execution options
            "execution_options": {
                "isolation_level": "READ COMMITTED",
                "postgresql_readonly": False,
                "postgresql_deferrable": False,
            }
        }
    

class PoolConfigFactory:
    """Factory for creating optimized pool configurations"""
    
    @staticmethod
    def create_config(
        strategy: PoolStrategy = PoolStrategy.PRODUCTION,
        environment: Optional[str] = None
    ) -> PoolConfig:
        """
        Create pool configuration based on strategy
        
        Args:
            strategy: Pool strategy to use
            environment: Environment name (overrides strategy)
            
        Returns:
            Optimized PoolConfig instance
        """
        if environment:
            strategy = PoolConfigFactory._strategy_from_environment(environment)
        
        if strategy == PoolStrategy.DEVELOPMENT:
            return PoolConfigFactory._development_config()
        elif strategy == PoolStrategy.PRODUCTION:
            return PoolConfigFactory._production_config()
        elif strategy == PoolStrategy.HIGH_TRAFFIC:
            return PoolConfigFactory._high_traffic_config()
        elif strategy == PoolStrategy.MICROSERVICE:
            return PoolConfigFactory._microservice_config()
        elif strategy == PoolStrategy.TESTING:
            return PoolConfigFactory._testing_config()
        else:
            return PoolConfigFactory._production_config()
    
    @staticmethod
    def _strategy_from_environment(environment: str) -> PoolStrategy:
        """Map environment name to pool strategy"""
        env_lower = environment.lower()
        if env_lower in ("development", "dev", "local"):
            return PoolStrategy.DEVELOPMENT
        elif env_lower in ("production", "prod"):
            return PoolStrategy.PRODUCTION
        elif env_lower in ("staging", "stage"):
            return PoolStrategy.PRODUCTION
        elif env_lower in ("testing", "test"):
            return PoolStrategy.TESTING
        else:
            return PoolStrategy.PRODUCTION
    
    @staticmethod
    def _development_config() -> PoolConfig:
        """Development configuration - smaller pool, more logging"""
        return PoolConfig(
            pool_size=5,
            max_overflow=10,
            pool_timeout=10.0,
            pool_recycle=1800,  # 30 minutes (reduced for cloud database compatibility)
            pool_pre_ping=True,
            pool_reset_on_return="rollback",
            echo_pool=bool(os.getenv("DEBUG_POOL", "false").lower() == "true"),
            pool_use_lifo=False,
            connect_timeout=5,
            statement_timeout=60000,  # 60 seconds
            idle_in_transaction_timeout=120000,  # 2 minutes
            lock_timeout=10000,  # 10 seconds
            idle_session_timeout=600000,  # 10 minutes
            max_connections_per_worker=3,
            connection_lifetime=1800,  # 30 minutes
            async_pool_class="AsyncAdaptedQueuePool",
            async_pool_use_read_write_split=False,
            prepared_statement_cache_size=256,
            jit="off",
            enable_pool_events=True,
            enable_statement_logging=bool(os.getenv("DEBUG", "false").lower() == "true"),
            slow_query_threshold=2.0
        )
    
    @staticmethod
    def _production_config() -> PoolConfig:
        """
        Production configuration following 2025 best practices
        - Optimized for typical web application load
        - Based on PostgreSQL 16+ and SQLAlchemy 2.0 recommendations
        """
        # Calculate optimal pool size based on system resources
        cpu_count = os.cpu_count() or 4
        optimal_pool_size = min(
            int(os.getenv("DB_POOL_SIZE", str(cpu_count * 4))),
            100  # PostgreSQL max_connections default / 2
        )
        
        return PoolConfig(
            # Core pool settings
            pool_size=optimal_pool_size,
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", str(optimal_pool_size * 2))),
            pool_timeout=float(os.getenv("DB_POOL_TIMEOUT", "30")),
            pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "1800")),  # 30 minutes
            pool_pre_ping=True,
            pool_reset_on_return="rollback",  # Ensure clean state
            
            # Performance settings
            echo_pool=False,
            pool_use_lifo=True,  # Better for connection reuse
            connect_timeout=10,
            
            # PostgreSQL 16+ settings
            statement_timeout=30000,  # 30 seconds
            idle_in_transaction_timeout=60000,  # 1 minute
            lock_timeout=10000,  # 10 seconds
            idle_session_timeout=600000,  # 10 minutes
            
            # Resource limits
            max_connections_per_worker=5,
            connection_lifetime=3600,  # 1 hour (reduced from 2 hours)
            
            # Async settings
            async_pool_class="AsyncAdaptedQueuePool",
            async_pool_use_read_write_split=False,
            
            # PostgreSQL optimizations
            prepared_statement_cache_size=512,
            jit="off",  # Disable for consistent performance
            
            # Monitoring
            enable_pool_events=True,
            enable_statement_logging=False,
            slow_query_threshold=1.0
        )
    
    @staticmethod
    def _high_traffic_config() -> PoolConfig:
        """High traffic configuration - larger pool, aggressive recycling"""
        return PoolConfig(
            pool_size=int(os.getenv("DB_POOL_SIZE", "50")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "100")),
            pool_timeout=float(os.getenv("DB_POOL_TIMEOUT", "10")),
            pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "900")),  # 15 minutes
            pool_pre_ping=True,
            echo_pool=False,
            pool_use_lifo=True,
            connect_timeout=5,
            statement_timeout=15000,  # 15 seconds
            idle_in_transaction_timeout=30000,  # 30 seconds
            max_connections_per_worker=10,
            connection_lifetime=3600  # 1 hour
        )
    
    @staticmethod
    def _microservice_config() -> PoolConfig:
        """Microservice configuration - minimal pool, quick recycling"""
        return PoolConfig(
            pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
            pool_timeout=float(os.getenv("DB_POOL_TIMEOUT", "5")),
            pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "600")),  # 10 minutes
            pool_pre_ping=True,
            echo_pool=False,
            pool_use_lifo=False,
            connect_timeout=3,
            statement_timeout=10000,  # 10 seconds
            idle_in_transaction_timeout=20000,  # 20 seconds
            max_connections_per_worker=2,
            connection_lifetime=1800  # 30 minutes
        )
    
    @staticmethod
    def _testing_config() -> PoolConfig:
        """Testing configuration - minimal resources"""
        return PoolConfig(
            pool_size=2,
            max_overflow=4,
            pool_timeout=5.0,
            pool_recycle=3600,
            pool_pre_ping=False,  # Skip in tests for speed
            echo_pool=False,
            pool_use_lifo=False,
            connect_timeout=2,
            statement_timeout=5000,  # 5 seconds
            idle_in_transaction_timeout=10000,  # 10 seconds
            max_connections_per_worker=1,
            connection_lifetime=600  # 10 minutes
        )

class PoolMonitor:
    """Monitor and optimize connection pool performance"""
    
    def __init__(self, pool_config: PoolConfig):
        self.config = pool_config
        self.metrics = {
            "connections_created": 0,
            "connections_recycled": 0,
            "connection_overflows": 0,
            "connection_timeouts": 0,
            "connection_errors": 0,
            "total_checkout_time": 0.0,
            "checkout_count": 0
        }
    
    def log_pool_status(self, pool) -> None:
        """Log current pool status"""
        try:
            logger.info(f"Pool Status: size={pool.size()}, "
                       f"checked_in={pool.checkedin()}, "
                       f"overflow={pool.overflow()}, "
                       f"total={pool.size() + pool.overflow()}")
        except AttributeError:
            # Pool might not have all methods
            pass
    
    def calculate_optimal_size(self, 
                              concurrent_requests: int,
                              avg_query_time: float) -> Dict[str, int]:
        """
        Calculate optimal pool size based on load
        
        Args:
            concurrent_requests: Average concurrent requests
            avg_query_time: Average query execution time in seconds
            
        Returns:
            Recommended pool configuration
        """
        # Formula: pool_size = concurrent_requests * (avg_query_time / acceptable_wait_time)
        acceptable_wait_time = 0.1  # 100ms acceptable wait
        
        recommended_pool_size = max(
            5,  # Minimum pool size
            int(concurrent_requests * (avg_query_time / acceptable_wait_time))
        )
        
        # Cap at reasonable maximum
        recommended_pool_size = min(recommended_pool_size, 100)
        
        # Overflow should be 50-100% of pool size
        recommended_overflow = int(recommended_pool_size * 0.75)
        
        return {
            "pool_size": recommended_pool_size,
            "max_overflow": recommended_overflow,
            "total_connections": recommended_pool_size + recommended_overflow
        }
    
    def get_recommendations(self) -> Dict[str, Any]:
        """Get optimization recommendations based on metrics"""
        recommendations = []
        
        if self.metrics["connection_timeouts"] > 10:
            recommendations.append({
                "issue": "High connection timeouts",
                "suggestion": "Increase pool_size or reduce pool_timeout",
                "severity": "high"
            })
        
        if self.metrics["connection_overflows"] > self.config.max_overflow * 0.8:
            recommendations.append({
                "issue": "Frequent use of overflow connections",
                "suggestion": "Increase base pool_size",
                "severity": "medium"
            })
        
        avg_checkout_time = (
            self.metrics["total_checkout_time"] / self.metrics["checkout_count"]
            if self.metrics["checkout_count"] > 0 else 0
        )
        
        if avg_checkout_time > 0.5:  # 500ms average checkout time
            recommendations.append({
                "issue": "Slow connection checkout",
                "suggestion": "Increase pool_size or optimize queries",
                "severity": "high"
            })
        
        return {
            "metrics": self.metrics,
            "recommendations": recommendations,
            "health": "healthy" if not recommendations else "needs_attention"
        }

def get_database_pool_config(
    environment: Optional[str] = None,
    database_type: str = "postgresql"
) -> PoolConfig:
    """
    Get optimized database pool configuration
    
    Args:
        environment: Environment name (development/production/etc)
        database_type: Type of database (postgresql/mysql/etc)
        
    Returns:
        Optimized PoolConfig instance
    """
    if not environment:
        # Check ENVIRONMENT variable, default to development if not set
        environment = os.getenv("ENVIRONMENT", "development")
    
    # Log configuration being used
    logger.info(f"Creating pool configuration for {environment} environment")
    
    # Get base configuration
    config = PoolConfigFactory.create_config(environment=environment)
    
    # Apply database-specific adjustments
    if database_type == "postgresql":
        # PostgreSQL specific optimizations
        config.pool_recycle = min(config.pool_recycle, 1800)  # PG cloud database timeout
    elif database_type == "mysql":
        # MySQL specific optimizations
        config.pool_recycle = min(config.pool_recycle, 28800)  # MySQL default timeout
    
    # Apply environment variable overrides (but not if they conflict with best practices)
    if os.getenv("DB_POOL_SIZE"):
        config.pool_size = int(os.getenv("DB_POOL_SIZE"))
    if os.getenv("DB_MAX_OVERFLOW"):
        config.max_overflow = int(os.getenv("DB_MAX_OVERFLOW"))
    if os.getenv("DB_POOL_TIMEOUT"):
        config.pool_timeout = float(os.getenv("DB_POOL_TIMEOUT"))
    if os.getenv("DB_POOL_RECYCLE"):
        # Ensure pool_recycle doesn't exceed 1800 for PostgreSQL
        recycle = int(os.getenv("DB_POOL_RECYCLE"))
        if database_type == "postgresql":
            config.pool_recycle = min(recycle, 1800)
        else:
            config.pool_recycle = recycle
    
    logger.info(f"Pool configuration: size={config.pool_size}, "
               f"overflow={config.max_overflow}, "
               f"timeout={config.pool_timeout}, "
               f"recycle={config.pool_recycle}")
    
    return config

# Export main components
__all__ = [
    'PoolConfig',
    'PoolConfigFactory',
    'PoolStrategy',
    'PoolMonitor',
    'get_database_pool_config'
]
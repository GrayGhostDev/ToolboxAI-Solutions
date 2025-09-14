"""
Database Connection Pool Configuration

Comprehensive configuration system for SQLAlchemy connection pooling with
PostgreSQL 16+ optimizations and 2025 best practices.
"""

import os
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import threading
import time
import psutil
from collections import deque
import json

logger = logging.getLogger(__name__)


class PoolStrategy(Enum):
    """Database connection pool strategies."""
    
    STATIC = "static"  # Fixed pool size
    DYNAMIC = "dynamic"  # Auto-scaling based on load
    BURST = "burst"  # Allow temporary expansion
    OPTIMIZED = "optimized"  # Smart optimization based on metrics
    MINIMAL = "minimal"  # Minimal connections for testing


class ConnectionState(Enum):
    """Connection states for monitoring."""
    
    IDLE = "idle"
    ACTIVE = "active"
    PENDING = "pending"
    CLOSING = "closing"
    ERROR = "error"


@dataclass
class PoolMetrics:
    """Metrics for connection pool monitoring."""
    
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    pending_connections: int = 0
    failed_connections: int = 0
    
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    
    avg_wait_time_ms: float = 0.0
    max_wait_time_ms: float = 0.0
    min_wait_time_ms: float = float('inf')
    
    connection_errors: List[str] = field(default_factory=list)
    last_error_time: Optional[datetime] = None
    
    pool_efficiency: float = 0.0
    throughput_per_second: float = 0.0
    
    # PostgreSQL specific metrics
    pg_stat_activity: Dict[str, int] = field(default_factory=dict)
    pg_buffer_cache_hit_ratio: float = 0.0
    pg_deadlocks: int = 0
    pg_conflicts: int = 0
    
    # System metrics
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    disk_io_read_mb: float = 0.0
    disk_io_write_mb: float = 0.0
    
    # Time-based metrics
    metrics_start_time: datetime = field(default_factory=datetime.now)
    last_update_time: datetime = field(default_factory=datetime.now)
    
    def calculate_efficiency(self):
        """Calculate pool efficiency metrics."""
        if self.total_requests > 0:
            self.pool_efficiency = (self.successful_requests / self.total_requests) * 100
        
        uptime_seconds = (datetime.now() - self.metrics_start_time).total_seconds()
        if uptime_seconds > 0:
            self.throughput_per_second = self.successful_requests / uptime_seconds
    
    def update_wait_time(self, wait_time_ms: float):
        """Update wait time statistics."""
        self.avg_wait_time_ms = (
            (self.avg_wait_time_ms * self.total_requests + wait_time_ms) /
            (self.total_requests + 1)
        )
        self.max_wait_time_ms = max(self.max_wait_time_ms, wait_time_ms)
        self.min_wait_time_ms = min(self.min_wait_time_ms, wait_time_ms)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "connections": {
                "total": self.total_connections,
                "active": self.active_connections,
                "idle": self.idle_connections,
                "pending": self.pending_connections,
                "failed": self.failed_connections
            },
            "requests": {
                "total": self.total_requests,
                "successful": self.successful_requests,
                "failed": self.failed_requests
            },
            "performance": {
                "avg_wait_time_ms": self.avg_wait_time_ms,
                "max_wait_time_ms": self.max_wait_time_ms,
                "min_wait_time_ms": self.min_wait_time_ms,
                "efficiency_percent": self.pool_efficiency,
                "throughput_per_second": self.throughput_per_second
            },
            "postgresql": self.pg_stat_activity,
            "system": {
                "cpu_percent": self.cpu_usage_percent,
                "memory_mb": self.memory_usage_mb,
                "disk_read_mb": self.disk_io_read_mb,
                "disk_write_mb": self.disk_io_write_mb
            },
            "errors": {
                "count": len(self.connection_errors),
                "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
                "recent_errors": self.connection_errors[-5:]  # Last 5 errors
            }
        }


@dataclass
class PoolConfig:
    """
    Comprehensive database connection pool configuration.
    
    Implements PostgreSQL 16+ optimizations and SQLAlchemy 2.0 best practices.
    """
    
    # Core pool settings
    pool_size: int = 20  # Number of persistent connections
    max_overflow: int = 10  # Maximum overflow connections
    pool_timeout: float = 30.0  # Seconds to wait for connection
    pool_recycle: int = 3600  # Recycle connections after 1 hour
    pool_pre_ping: bool = True  # Test connections before use
    
    # PostgreSQL specific
    pg_max_connections: int = 100  # PostgreSQL max_connections setting
    pg_superuser_reserved: int = 3  # Reserved connections for superuser
    pg_statement_timeout: int = 30000  # Statement timeout in ms
    pg_lock_timeout: int = 10000  # Lock timeout in ms
    pg_idle_in_transaction_timeout: int = 60000  # Idle transaction timeout
    
    # Performance tuning
    echo_pool: bool = False  # Log pool checkouts/checkins
    poolclass: str = "QueuePool"  # SQLAlchemy pool class
    use_lifo: bool = True  # Use LIFO for connection reuse (better cache)
    
    # Connection parameters
    connect_args: Dict[str, Any] = field(default_factory=lambda: {
        "server_settings": {
            "application_name": "toolboxai",
            "jit": "on",
            "log_duration": "off"
        },
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
        "tcp_user_timeout": 30000,
        "connect_timeout": 10,
        "options": "-c statement_timeout=30000 -c lock_timeout=10000"
    })
    
    # Retry configuration
    retry_on_disconnect: bool = True
    max_retries: int = 3
    retry_delay_base: float = 0.5  # Base delay for exponential backoff
    retry_delay_max: float = 10.0  # Maximum retry delay
    
    # Load balancing
    read_write_split: bool = False  # Enable read/write splitting
    read_pool_size: int = 15  # Read replica pool size
    write_pool_size: int = 5  # Write primary pool size
    
    # Monitoring
    enable_metrics: bool = True
    metrics_interval: int = 60  # Seconds between metric collections
    slow_query_threshold: float = 1.0  # Log queries slower than this
    
    # Strategy
    strategy: PoolStrategy = PoolStrategy.OPTIMIZED
    
    # Auto-scaling (for DYNAMIC strategy)
    auto_scale_enabled: bool = True
    scale_up_threshold: float = 0.8  # Scale up at 80% utilization
    scale_down_threshold: float = 0.3  # Scale down at 30% utilization
    scale_interval: int = 300  # Check every 5 minutes
    min_pool_size: int = 5
    max_pool_size: int = 50
    
    # Circuit breaker
    circuit_breaker_enabled: bool = True
    circuit_breaker_threshold: int = 5  # Failures before opening
    circuit_breaker_timeout: int = 60  # Seconds before retry
    
    # Environment-specific
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    
    def __post_init__(self):
        """Validate and adjust configuration after initialization."""
        # Adjust for environment
        if self.environment == "production":
            self.pool_size = max(self.pool_size, 30)
            self.max_overflow = max(self.max_overflow, 20)
            self.pool_pre_ping = True
            self.circuit_breaker_enabled = True
        elif self.environment == "testing":
            self.pool_size = min(self.pool_size, 5)
            self.max_overflow = min(self.max_overflow, 2)
            self.enable_metrics = False
        
        # Validate pool settings
        if self.pool_size + self.max_overflow > self.pg_max_connections - self.pg_superuser_reserved:
            logger.warning(
                f"Pool size ({self.pool_size} + {self.max_overflow}) exceeds "
                f"available PostgreSQL connections ({self.pg_max_connections} - {self.pg_superuser_reserved})"
            )
            # Adjust to fit
            available = self.pg_max_connections - self.pg_superuser_reserved
            self.max_overflow = min(self.max_overflow, available // 3)
            self.pool_size = min(self.pool_size, available - self.max_overflow)
        
        # Ensure min/max bounds
        self.min_pool_size = min(self.min_pool_size, self.pool_size)
        self.max_pool_size = max(self.max_pool_size, self.pool_size + self.max_overflow)
    
    def to_sqlalchemy_config(self) -> Dict[str, Any]:
        """Convert to SQLAlchemy pool configuration."""
        config = {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "pool_pre_ping": self.pool_pre_ping,
            "echo_pool": self.echo_pool,
            "use_lifo": self.use_lifo,
            "connect_args": self.connect_args
        }
        
        # Add poolclass if not default
        if self.poolclass != "QueuePool":
            from sqlalchemy import pool
            config["poolclass"] = getattr(pool, self.poolclass)
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "strategy": self.strategy.value,
            "environment": self.environment,
            "postgresql": {
                "max_connections": self.pg_max_connections,
                "statement_timeout": self.pg_statement_timeout,
                "lock_timeout": self.pg_lock_timeout
            },
            "auto_scaling": {
                "enabled": self.auto_scale_enabled,
                "min_size": self.min_pool_size,
                "max_size": self.max_pool_size
            },
            "circuit_breaker": {
                "enabled": self.circuit_breaker_enabled,
                "threshold": self.circuit_breaker_threshold
            }
        }


class PoolConfigFactory:
    """Factory for creating pool configurations based on context."""
    
    @staticmethod
    def create_config(
        strategy: PoolStrategy = PoolStrategy.OPTIMIZED,
        environment: Optional[str] = None,
        **kwargs
    ) -> PoolConfig:
        """
        Create a pool configuration for the given strategy and environment.
        
        Args:
            strategy: Pool strategy to use
            environment: Environment (production, staging, development, testing)
            **kwargs: Additional configuration overrides
        
        Returns:
            PoolConfig instance
        """
        environment = environment or os.getenv("ENVIRONMENT", "development")
        
        # Base configurations for each strategy
        configs = {
            PoolStrategy.STATIC: {
                "pool_size": 20,
                "max_overflow": 0,
                "auto_scale_enabled": False
            },
            PoolStrategy.DYNAMIC: {
                "pool_size": 10,
                "max_overflow": 20,
                "auto_scale_enabled": True,
                "scale_up_threshold": 0.7,
                "scale_down_threshold": 0.3
            },
            PoolStrategy.BURST: {
                "pool_size": 15,
                "max_overflow": 50,
                "auto_scale_enabled": False,
                "pool_timeout": 5.0
            },
            PoolStrategy.OPTIMIZED: {
                "pool_size": 20,
                "max_overflow": 10,
                "auto_scale_enabled": True,
                "pool_pre_ping": True,
                "use_lifo": True
            },
            PoolStrategy.MINIMAL: {
                "pool_size": 2,
                "max_overflow": 1,
                "auto_scale_enabled": False,
                "enable_metrics": False
            }
        }
        
        # Environment-specific adjustments
        env_configs = {
            "production": {
                "pool_size": 30,
                "max_overflow": 20,
                "pool_pre_ping": True,
                "circuit_breaker_enabled": True,
                "enable_metrics": True,
                "retry_on_disconnect": True
            },
            "staging": {
                "pool_size": 20,
                "max_overflow": 10,
                "pool_pre_ping": True,
                "enable_metrics": True
            },
            "development": {
                "pool_size": 10,
                "max_overflow": 5,
                "echo_pool": False,
                "enable_metrics": True
            },
            "testing": {
                "pool_size": 2,
                "max_overflow": 1,
                "enable_metrics": False,
                "pool_timeout": 5.0
            }
        }
        
        # Start with strategy config
        config_dict = configs.get(strategy, {})
        
        # Apply environment config
        env_config = env_configs.get(environment, {})
        config_dict.update(env_config)
        
        # Apply user overrides
        config_dict.update(kwargs)
        
        # Set strategy and environment
        config_dict["strategy"] = strategy
        config_dict["environment"] = environment
        
        return PoolConfig(**config_dict)
    
    @staticmethod
    def create_from_database_url(database_url: str, **kwargs) -> PoolConfig:
        """
        Create configuration based on database URL analysis.
        
        Args:
            database_url: PostgreSQL connection URL
            **kwargs: Additional configuration overrides
        
        Returns:
            PoolConfig instance
        """
        # Extract environment and strategy from kwargs if present to avoid duplicates
        environment = kwargs.pop('environment', None)
        strategy = kwargs.pop('strategy', None)
        
        # Parse URL to determine appropriate settings
        if "localhost" in database_url or "127.0.0.1" in database_url:
            # Local database - can use more connections
            if not environment:
                environment = "development"
            if not strategy:
                strategy = PoolStrategy.OPTIMIZED
            return PoolConfigFactory.create_config(
                strategy=strategy,
                environment=environment,
                pool_size=kwargs.pop('pool_size', 15),
                max_overflow=kwargs.pop('max_overflow', 10),
                **kwargs
            )
        elif "amazonaws.com" in database_url or "cloud.google.com" in database_url:
            # Cloud database - optimize for network latency
            if not environment:
                environment = "production"
            if not strategy:
                strategy = PoolStrategy.DYNAMIC
            return PoolConfigFactory.create_config(
                strategy=strategy,
                environment=environment,
                pool_size=kwargs.pop('pool_size', 20),
                max_overflow=kwargs.pop('max_overflow', 15),
                pool_recycle=kwargs.pop('pool_recycle', 1800),  # Recycle more frequently
                pool_pre_ping=kwargs.pop('pool_pre_ping', True),
                **kwargs
            )
        else:
            # Default configuration
            if not strategy:
                strategy = PoolStrategy.OPTIMIZED
            return PoolConfigFactory.create_config(
                strategy=strategy,
                environment=environment,
                **kwargs
            )
    
    @staticmethod
    def create_for_testing() -> PoolConfig:
        """Create minimal configuration for testing."""
        return PoolConfigFactory.create_config(
            strategy=PoolStrategy.MINIMAL,
            environment="testing",
            pool_size=2,
            max_overflow=1,
            pool_timeout=5.0,
            enable_metrics=False,
            auto_scale_enabled=False,
            circuit_breaker_enabled=False
        )


class PoolMonitor:
    """
    Monitor and manage database connection pools.
    
    Tracks metrics, detects issues, and provides optimization recommendations.
    """
    
    def __init__(self, config: PoolConfig):
        self.config = config
        self.metrics = PoolMetrics()
        self.metrics_history: deque = deque(maxlen=1440)  # 24 hours at 1-minute intervals
        self._lock = threading.Lock()
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        
        # Circuit breaker state
        self.circuit_breaker_failures = 0
        self.circuit_breaker_open = False
        self.circuit_breaker_open_time: Optional[datetime] = None
        
        # Connection tracking
        self.connection_states: Dict[int, ConnectionState] = {}
        self.connection_start_times: Dict[int, datetime] = {}
        
        logger.info(f"PoolMonitor initialized with strategy: {config.strategy.value}")
    
    def start_monitoring(self):
        """Start background monitoring thread."""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("Pool monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring thread."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("Pool monitoring stopped")
    
    def _monitor_loop(self):
        """Background monitoring loop."""
        while self._monitoring:
            try:
                self.collect_metrics()
                self.check_health()
                
                if self.config.auto_scale_enabled:
                    self.check_scaling()
                
                # Sleep for monitoring interval
                time.sleep(self.config.metrics_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
    
    def collect_metrics(self):
        """Collect current pool metrics."""
        with self._lock:
            # Update system metrics
            self.metrics.cpu_usage_percent = psutil.cpu_percent(interval=1)
            self.metrics.memory_usage_mb = psutil.Process().memory_info().rss / 1024 / 1024
            
            # Calculate efficiency
            self.metrics.calculate_efficiency()
            
            # Store snapshot
            snapshot = {
                "timestamp": datetime.now(),
                "metrics": self.metrics.to_dict()
            }
            self.metrics_history.append(snapshot)
            
            self.metrics.last_update_time = datetime.now()
    
    def check_health(self):
        """Check pool health and trigger alerts if needed."""
        # Check for high wait times
        if self.metrics.avg_wait_time_ms > 1000:
            logger.warning(f"High average wait time: {self.metrics.avg_wait_time_ms:.2f}ms")
        
        # Check for connection errors
        if self.metrics.failed_connections > self.config.circuit_breaker_threshold:
            self.trigger_circuit_breaker()
        
        # Check efficiency
        if self.metrics.pool_efficiency < 90:
            logger.warning(f"Low pool efficiency: {self.metrics.pool_efficiency:.2f}%")
    
    def check_scaling(self):
        """Check if pool needs scaling (for DYNAMIC strategy)."""
        if self.config.strategy != PoolStrategy.DYNAMIC:
            return
        
        utilization = self.metrics.active_connections / self.config.pool_size if self.config.pool_size > 0 else 0
        
        if utilization > self.config.scale_up_threshold:
            self.recommend_scale_up()
        elif utilization < self.config.scale_down_threshold:
            self.recommend_scale_down()
    
    def recommend_scale_up(self):
        """Recommend scaling up the pool."""
        current_size = self.config.pool_size
        recommended_size = min(
            int(current_size * 1.5),
            self.config.max_pool_size
        )
        
        if recommended_size > current_size:
            logger.info(f"Recommend scaling pool from {current_size} to {recommended_size}")
            return recommended_size
        return current_size
    
    def recommend_scale_down(self):
        """Recommend scaling down the pool."""
        current_size = self.config.pool_size
        recommended_size = max(
            int(current_size * 0.7),
            self.config.min_pool_size
        )
        
        if recommended_size < current_size:
            logger.info(f"Recommend scaling pool from {current_size} to {recommended_size}")
            return recommended_size
        return current_size
    
    def trigger_circuit_breaker(self):
        """Trigger circuit breaker to prevent cascading failures."""
        if not self.config.circuit_breaker_enabled:
            return
        
        if not self.circuit_breaker_open:
            self.circuit_breaker_open = True
            self.circuit_breaker_open_time = datetime.now()
            logger.error("Circuit breaker opened due to connection failures")
    
    def check_circuit_breaker(self) -> bool:
        """Check if circuit breaker allows connections."""
        if not self.circuit_breaker_open:
            return True
        
        # Check if timeout has passed
        if self.circuit_breaker_open_time:
            elapsed = (datetime.now() - self.circuit_breaker_open_time).total_seconds()
            if elapsed > self.config.circuit_breaker_timeout:
                self.circuit_breaker_open = False
                self.circuit_breaker_failures = 0
                logger.info("Circuit breaker closed, allowing connections")
                return True
        
        return False
    
    def record_connection_acquired(self, conn_id: int):
        """Record that a connection was acquired."""
        with self._lock:
            self.connection_states[conn_id] = ConnectionState.ACTIVE
            self.connection_start_times[conn_id] = datetime.now()
            self.metrics.active_connections += 1
            self.metrics.idle_connections = max(0, self.metrics.idle_connections - 1)
    
    def record_connection_released(self, conn_id: int):
        """Record that a connection was released."""
        with self._lock:
            if conn_id in self.connection_states:
                self.connection_states[conn_id] = ConnectionState.IDLE
                self.metrics.active_connections = max(0, self.metrics.active_connections - 1)
                self.metrics.idle_connections += 1
                
                # Calculate connection duration
                if conn_id in self.connection_start_times:
                    duration = (datetime.now() - self.connection_start_times[conn_id]).total_seconds()
                    del self.connection_start_times[conn_id]
    
    def record_connection_error(self, error: str):
        """Record a connection error."""
        with self._lock:
            self.metrics.failed_connections += 1
            self.metrics.connection_errors.append(error)
            self.metrics.last_error_time = datetime.now()
            self.circuit_breaker_failures += 1
            
            # Keep only last 100 errors
            if len(self.metrics.connection_errors) > 100:
                self.metrics.connection_errors = self.metrics.connection_errors[-100:]
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get current metrics summary."""
        with self._lock:
            return self.metrics.to_dict()
    
    def get_recommendations(self) -> List[str]:
        """Get optimization recommendations based on metrics."""
        recommendations = []
        
        # Check wait times
        if self.metrics.avg_wait_time_ms > 500:
            recommendations.append(
                f"Consider increasing pool_size (current: {self.config.pool_size})"
            )
        
        # Check efficiency
        if self.metrics.pool_efficiency < 95:
            recommendations.append(
                "Low efficiency detected. Check for connection leaks or long-running queries"
            )
        
        # Check error rate
        if self.metrics.failed_connections > 10:
            recommendations.append(
                "High error rate. Check database connectivity and credentials"
            )
        
        # Check utilization
        utilization = self.metrics.active_connections / self.config.pool_size if self.config.pool_size > 0 else 0
        if utilization > 0.9:
            recommendations.append(
                "High pool utilization. Consider increasing pool size or optimizing queries"
            )
        elif utilization < 0.1 and self.config.pool_size > 5:
            recommendations.append(
                "Low pool utilization. Consider reducing pool size to save resources"
            )
        
        return recommendations


def get_database_pool_config(
    database_url: Optional[str] = None,
    environment: Optional[str] = None,
    strategy: Optional[PoolStrategy] = None,
    **kwargs
) -> PoolConfig:
    """
    Get database pool configuration based on context.
    
    Args:
        database_url: Database connection URL
        environment: Environment name
        strategy: Pool strategy to use
        **kwargs: Additional configuration overrides
    
    Returns:
        PoolConfig instance
    """
    # Get from environment if not provided
    if not database_url:
        database_url = os.getenv("DATABASE_URL", "postgresql://localhost/toolboxai")
    
    if not environment:
        environment = os.getenv("ENVIRONMENT", "development")
    
    if not strategy:
        # Choose strategy based on environment
        if environment == "production":
            strategy = PoolStrategy.OPTIMIZED
        elif environment == "testing":
            strategy = PoolStrategy.MINIMAL
        else:
            strategy = PoolStrategy.DYNAMIC
    
    # Create configuration
    if database_url:
        config = PoolConfigFactory.create_from_database_url(
            database_url,
            environment=environment,
            strategy=strategy,
            **kwargs
        )
    else:
        config = PoolConfigFactory.create_config(
            strategy=strategy,
            environment=environment,
            **kwargs
        )
    
    logger.info(f"Created pool config: {config.strategy.value} for {config.environment}")
    return config


# Convenience instances for common configurations
DEFAULT_CONFIG = get_database_pool_config()
PRODUCTION_CONFIG = PoolConfigFactory.create_config(
    strategy=PoolStrategy.OPTIMIZED,
    environment="production"
)
TESTING_CONFIG = PoolConfigFactory.create_for_testing()


__all__ = [
    "PoolConfig",
    "PoolConfigFactory",
    "PoolStrategy",
    "PoolMonitor",
    "PoolMetrics",
    "ConnectionState",
    "get_database_pool_config",
    "DEFAULT_CONFIG",
    "PRODUCTION_CONFIG",
    "TESTING_CONFIG"
]
"""
Celery Worker Configuration
============================
Advanced worker configuration for the ToolBoxAI platform with multi-tenancy,
Redis clustering, and production-ready monitoring capabilities.

Features:
- Redis cluster support for scaling
- Tenant-aware task execution
- Prometheus metrics integration
- Self-hosted monitoring (no AWS dependencies)
- Production-ready security settings
"""

import os
import socket
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import timedelta

from toolboxai_settings import settings


@dataclass
class WorkerConfig:
    """
    Comprehensive worker configuration for production deployment.
    Follows 2025 Celery best practices with Redis Cluster support.
    """

    # Core Redis Configuration (NO AWS)
    broker_url: str = settings.REDIS_URL or "redis://redis:6379/0"
    result_backend: str = settings.REDIS_URL or "redis://redis:6379/1"

    # Redis Cluster Configuration (for scaling)
    redis_cluster_enabled: bool = os.getenv("REDIS_CLUSTER_ENABLED", "false").lower() == "true"
    redis_cluster_nodes: List[str] = []

    # Worker Concurrency (auto-detected from container limits)
    worker_concurrency: int = int(os.getenv("CELERY_WORKER_CONCURRENCY", "4"))
    worker_pool: str = os.getenv("CELERY_WORKER_POOL", "prefork")  # prefork for CPU, gevent for I/O
    worker_max_tasks_per_child: int = 1000
    worker_prefetch_multiplier: int = 4

    # Task Time Limits
    task_time_limit: int = 300  # 5 minutes hard limit
    task_soft_time_limit: int = 270  # 4.5 minutes soft limit

    # Reliability Settings
    task_acks_late: bool = True
    task_reject_on_worker_lost: bool = True
    worker_cancel_long_running_tasks_on_connection_loss: bool = True

    # Monitoring (Prometheus, not CloudWatch)
    prometheus_enabled: bool = os.getenv("PROMETHEUS_ENABLED", "true").lower() == "true"
    prometheus_port: int = int(os.getenv("PROMETHEUS_PORT", "9090"))

    # Tenant Context Management
    tenant_isolation_enabled: bool = True
    default_organization_id: Optional[str] = None

    # Security Settings
    task_serializer: str = "json"
    result_serializer: str = "json"
    accept_content: List[str] = None

    # Dead Letter Queue (Redis-based, not AWS SQS)
    dead_letter_queue_enabled: bool = True
    dead_letter_queue_name: str = "failed_tasks"
    max_retries: int = 3

    # Flower Monitoring (self-hosted)
    flower_enabled: bool = os.getenv("FLOWER_ENABLED", "true").lower() == "true"
    flower_port: int = int(os.getenv("FLOWER_PORT", "5555"))
    flower_basic_auth: Optional[str] = os.getenv("FLOWER_BASIC_AUTH")  # user:password

    def __post_init__(self):
        """Initialize computed configuration values."""
        if self.accept_content is None:
            self.accept_content = ["json"]  # Security: Only accept JSON

        if self.redis_cluster_enabled:
            # Parse cluster nodes from environment
            cluster_nodes_env = os.getenv("REDIS_CLUSTER_NODES", "")
            if cluster_nodes_env:
                self.redis_cluster_nodes = [
                    node.strip() for node in cluster_nodes_env.split(",")
                    if node.strip()
                ]

    def get_broker_transport_options(self) -> Dict[str, Any]:
        """Get Redis broker transport options with cluster support."""
        options = {
            'visibility_timeout': 43200,  # 12 hours
            'fanout_prefix': True,
            'fanout_patterns': True,
            'socket_keepalive': True,
            'socket_keepalive_options': {
                1: 3,  # TCP_KEEPIDLE
                2: 3,  # TCP_KEEPINTVL
                3: 3,  # TCP_KEEPCNT
            },
            'max_connections': 50,
            'health_check_interval': 30,
        }

        if self.redis_cluster_enabled and self.redis_cluster_nodes:
            options.update({
                'startup_nodes': [
                    {'host': node.split(':')[0], 'port': int(node.split(':')[1])}
                    for node in self.redis_cluster_nodes
                ],
                'skip_full_coverage_check': True,
                'max_connections_per_node': 20
            })

        return options

    def get_task_routes(self) -> Dict[str, Dict[str, str]]:
        """Define task routing to appropriate queues."""
        return {
            "apps.backend.workers.tasks.email_tasks.*": {"queue": "email"},
            "apps.backend.workers.tasks.analytics_tasks.*": {"queue": "analytics"},
            "apps.backend.workers.tasks.content_tasks.*": {"queue": "ai_generation"},
            "apps.backend.workers.tasks.roblox_tasks.*": {"queue": "roblox"},
            "apps.backend.workers.tasks.cleanup_tasks.*": {"queue": "low_priority"},
            "apps.backend.workers.tasks.tenant_tasks.*": {"queue": "tenant_operations"},
        }

    def get_task_annotations(self) -> Dict[str, Dict[str, str]]:
        """Get task annotations with rate limits."""
        return {
            "*": {"rate_limit": "1000/m"},  # Default rate limit
            "apps.backend.workers.tasks.email_tasks.*": {"rate_limit": "100/m"},
            "apps.backend.workers.tasks.content_tasks.*": {"rate_limit": "10/m"},  # AI tasks are slower
            "apps.backend.workers.tasks.analytics_tasks.*": {"rate_limit": "50/m"},
            "apps.backend.workers.tasks.roblox_tasks.*": {"rate_limit": "20/m"},
        }

    def get_prometheus_config(self) -> Dict[str, Any]:
        """Get Prometheus monitoring configuration."""
        if not self.prometheus_enabled:
            return {}

        return {
            'prometheus_metrics_enabled': True,
            'prometheus_port': self.prometheus_port,
            'metrics_prefix': 'celery_',
            'metrics_labels': {
                'service': 'toolboxai',
                'environment': settings.ENV_NAME,
                'hostname': socket.gethostname()
            }
        }

    def get_worker_hostname(self) -> str:
        """Get worker hostname for container identification."""
        container_id = os.getenv("HOSTNAME", socket.gethostname())
        return f"{container_id}@%n"

    def to_celery_config(self) -> Dict[str, Any]:
        """Convert to Celery configuration dictionary."""
        config = {
            # Broker settings
            'broker_url': self.broker_url,
            'result_backend': self.result_backend,
            'broker_transport_options': self.get_broker_transport_options(),
            'broker_connection_retry': True,
            'broker_connection_retry_on_startup': True,
            'broker_connection_max_retries': None,
            'broker_heartbeat': 120.0,

            # Task settings
            'task_serializer': self.task_serializer,
            'result_serializer': self.result_serializer,
            'accept_content': self.accept_content,
            'task_acks_late': self.task_acks_late,
            'task_reject_on_worker_lost': self.task_reject_on_worker_lost,
            'task_track_started': True,
            'task_time_limit': self.task_time_limit,
            'task_soft_time_limit': self.task_soft_time_limit,
            'task_compression': 'gzip',

            # Worker settings
            'worker_concurrency': self.worker_concurrency,
            'worker_pool': self.worker_pool,
            'worker_max_tasks_per_child': self.worker_max_tasks_per_child,
            'worker_prefetch_multiplier': self.worker_prefetch_multiplier,
            'worker_hostname': self.get_worker_hostname(),
            'worker_send_task_events': True,
            'worker_cancel_long_running_tasks_on_connection_loss':
                self.worker_cancel_long_running_tasks_on_connection_loss,
            'worker_enable_remote_control': True,
            'worker_redirect_stdouts': True,
            'worker_redirect_stdouts_level': 'INFO',
            'worker_hijack_root_logger': False,

            # Result backend settings
            'result_expires': 3600,  # 1 hour
            'result_compression': 'gzip',
            'result_persistent': True,

            # Routing
            'task_routes': self.get_task_routes(),
            'task_annotations': self.get_task_annotations(),

            # Default queue settings
            'task_default_queue': 'default',
            'task_default_exchange': 'default',
            'task_default_exchange_type': 'direct',
            'task_default_routing_key': 'default',
        }

        # Add Prometheus config if enabled
        config.update(self.get_prometheus_config())

        return config


def get_worker_config() -> WorkerConfig:
    """
    Get worker configuration instance with environment-specific settings.

    Returns:
        WorkerConfig: Configured worker settings
    """
    return WorkerConfig()


def get_queue_definitions() -> List[Dict[str, Any]]:
    """
    Define Celery queues with priorities and routing.

    Returns:
        List of queue definitions for Celery configuration
    """
    from kombu import Queue, Exchange

    return [
        # High priority queue for critical tasks
        Queue(
            "high_priority",
            Exchange("high_priority"),
            routing_key="high_priority",
            priority=10,
            max_priority=10
        ),

        # Default queue for general tasks
        Queue(
            "default",
            Exchange("default"),
            routing_key="default",
            priority=5,
            max_priority=10
        ),

        # Low priority queue for maintenance tasks
        Queue(
            "low_priority",
            Exchange("low_priority"),
            routing_key="low_priority",
            priority=1,
            max_priority=10
        ),

        # Specialized queues for different task types
        Queue("email", Exchange("email"), routing_key="email"),
        Queue("analytics", Exchange("analytics"), routing_key="analytics"),
        Queue("ai_generation", Exchange("ai_generation"), routing_key="ai_generation"),
        Queue("roblox", Exchange("roblox"), routing_key="roblox"),
        Queue("tenant_operations", Exchange("tenant_operations"), routing_key="tenant_operations"),

        # Dead letter queue for failed tasks
        Queue("failed_tasks", Exchange("failed_tasks"), routing_key="failed_tasks"),
    ]


def get_tenant_context() -> Dict[str, Any]:
    """
    Get tenant context for multi-tenant task execution.

    Returns:
        Dictionary containing tenant-specific configuration
    """
    return {
        'tenant_isolation_enabled': True,
        'default_organization_id': os.getenv("DEFAULT_ORGANIZATION_ID"),
        'tenant_db_routing': True,
        'tenant_cache_prefix': True,
    }


def get_monitoring_config() -> Dict[str, Any]:
    """
    Get monitoring configuration for self-hosted metrics.

    Returns:
        Monitoring configuration (Prometheus, not CloudWatch)
    """
    return {
        'prometheus': {
            'enabled': os.getenv("PROMETHEUS_ENABLED", "true").lower() == "true",
            'port': int(os.getenv("PROMETHEUS_PORT", "9090")),
            'metrics_path': '/metrics',
            'namespace': 'toolboxai_celery'
        },
        'flower': {
            'enabled': os.getenv("FLOWER_ENABLED", "true").lower() == "true",
            'port': int(os.getenv("FLOWER_PORT", "5555")),
            'basic_auth': os.getenv("FLOWER_BASIC_AUTH"),
            'url_prefix': os.getenv("FLOWER_URL_PREFIX", ""),
        },
        'logging': {
            'level': os.getenv("CELERY_LOG_LEVEL", "INFO"),
            'format': "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
            'handlers': ['console', 'file'],
            'structured': True,
        }
    }


def validate_configuration() -> Dict[str, Any]:
    """
    Validate worker configuration and dependencies.

    Returns:
        Validation results with warnings and errors
    """
    config = get_worker_config()
    issues = {'errors': [], 'warnings': [], 'info': []}

    # Check Redis connectivity
    try:
        import redis
        r = redis.from_url(config.broker_url)
        r.ping()
        issues['info'].append("Redis broker connectivity verified")
    except Exception as e:
        issues['errors'].append(f"Redis broker connection failed: {e}")

    # Check result backend
    if config.result_backend == config.broker_url:
        issues['warnings'].append("Broker and result backend using same Redis DB")

    # Check cluster configuration
    if config.redis_cluster_enabled and not config.redis_cluster_nodes:
        issues['errors'].append("Redis cluster enabled but no nodes configured")

    # Check Prometheus configuration
    if config.prometheus_enabled:
        try:
            import prometheus_client
            issues['info'].append("Prometheus client available for metrics")
        except ImportError:
            issues['warnings'].append("Prometheus client not installed")

    # Check worker pool compatibility
    if config.worker_pool == "gevent":
        try:
            import gevent
            issues['info'].append("Gevent pool available for I/O-bound tasks")
        except ImportError:
            issues['errors'].append("Gevent not installed but specified as worker pool")

    return issues
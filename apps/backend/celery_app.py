"""
Celery Application Configuration for ToolBoxAI
==============================================
Production-ready Celery configuration based on official Celery 5.4+ documentation
Implements best practices for Docker deployment with Redis broker

Reference: https://docs.celeryq.dev/en/stable/
Updated: 2025-09-27 - Following latest Celery 5.4 standards
"""

# Ensure repository root is on sys.path even if executed from apps/backend
import sys
from pathlib import Path

try:
    pass  # type: ignore
except Exception:
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

import logging
import os
import socket
from datetime import timedelta
from typing import Any

from celery import Celery, Task
from celery.signals import (
    setup_logging,
    task_failure,
    worker_ready,
    worker_shutdown,
)
from kombu import Exchange, Queue

# Import settings from the shared configuration
from toolboxai_settings import settings

# Configure logging
logger = logging.getLogger(__name__)

# ============================================
# CELERY APPLICATION INSTANCE
# ============================================

# Create Celery app instance with main module name
# Following Celery 5.4 best practice for module discovery
app = Celery("toolboxai", include=["apps.backend.tasks"])

# ============================================
# CELERY CONFIGURATION
# ============================================


class CeleryConfig:
    """
    Production-ready Celery configuration for Docker deployment
    Based on official Celery 5.4 documentation and Docker best practices
    Reference: https://docs.celeryq.dev/en/stable/userguide/configuration.html
    """

    # ----------------------------------------
    # Broker Settings (Redis) - Per Celery 5.4 Redis documentation
    # Reference: https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/redis.html
    # ----------------------------------------
    # Redis URL format: redis://:password@hostname:port/db_number
    broker_url = os.getenv("CELERY_BROKER_URL", settings.REDIS_URL or "redis://redis:6379/0")
    result_backend = os.getenv(
        "CELERY_RESULT_BACKEND",
        settings.REDIS_URL or "redis://redis:6379/1",  # Use different DB for results
    )

    # Redis-specific broker settings (Celery 5.4 recommendations)
    broker_connection_retry = True
    broker_connection_retry_on_startup = True  # Added in Celery 5.3
    broker_connection_max_retries = None  # Retry forever in production
    broker_heartbeat = 120.0  # Heartbeat every 2 minutes

    # Redis visibility timeout (must be larger than task ETA)
    broker_transport_options = {
        "visibility_timeout": 43200,  # 12 hours
        "fanout_prefix": True,
        "fanout_patterns": True,
        # Connection pool settings for redis-py >= 4.5.0
        "socket_keepalive": True,
        "socket_keepalive_options": {
            1: 3,  # TCP_KEEPIDLE
            2: 3,  # TCP_KEEPINTVL
            3: 3,  # TCP_KEEPCNT
        },
        "max_connections": 50,  # Connection pool size
        "health_check_interval": 30,  # Health check every 30 seconds
    }
    broker_pool_limit = None  # Will use connection pool

    # Result backend settings
    result_backend_max_retries = 3
    result_expires = 3600  # Results expire after 1 hour
    result_persistent = True
    result_compression = "gzip"

    # ----------------------------------------
    # Task Execution Settings
    # ----------------------------------------
    task_serializer = "json"
    result_serializer = "json"
    accept_content = ["json"]  # Security: Only accept JSON

    # Task behavior
    task_acks_late = True  # Acknowledge after task completion (reliability)
    task_reject_on_worker_lost = True  # Reject tasks if worker dies
    task_track_started = True
    task_publish_retry = True
    task_publish_retry_policy = {
        "max_retries": 3,
        "interval_start": 0.2,
        "interval_step": 0.2,
        "interval_max": 1,
    }

    # Time limits (based on TODO.md requirements)
    task_time_limit = 300  # 5 minutes hard limit
    task_soft_time_limit = 270  # 4.5 minutes soft limit (allows cleanup)

    # Task compression for performance
    task_compression = "gzip"

    # ----------------------------------------
    # Worker Settings - Docker optimized
    # ----------------------------------------
    # Concurrency based on container CPU limits
    worker_concurrency = int(os.getenv("CELERY_WORKER_CONCURRENCY", "4"))
    worker_prefetch_multiplier = 4
    worker_max_tasks_per_child = 1000  # Restart worker after N tasks (memory management)
    worker_disable_rate_limits = False
    worker_enable_remote_control = True

    # Worker behavior - Celery 5.4 recommendations
    worker_send_task_events = True  # For monitoring with Flower
    worker_cancel_long_running_tasks_on_connection_loss = True  # Added in Celery 5.3
    worker_enable_prefetch_count_reduction = True
    worker_hijack_root_logger = False  # Don't override logging config
    worker_redirect_stdouts = True
    worker_redirect_stdouts_level = "INFO"

    # Docker-specific: Detect container hostname
    worker_hostname = f"{socket.gethostname()}@%n"  # Include container ID

    # Pool settings - optimized for Docker
    worker_pool = os.getenv("CELERY_WORKER_POOL", "prefork")  # prefork for CPU, gevent for I/O
    worker_pool_restarts = True

    # Health check settings (for Docker healthcheck)
    worker_enable_ping = True  # Enable ping command for health checks

    # ----------------------------------------
    # Beat Schedule (Periodic Tasks)
    # ----------------------------------------
    beat_schedule = {
        # Cleanup tasks
        "cleanup-expired-sessions": {
            "task": "apps.backend.tasks.cleanup_tasks.cleanup_expired_sessions",
            "schedule": timedelta(hours=1),
            "options": {"queue": "low_priority"},
        },
        "cleanup-old-logs": {
            "task": "apps.backend.tasks.cleanup_tasks.cleanup_old_logs",
            "schedule": timedelta(days=1),
            "options": {"queue": "low_priority"},
        },
        # Analytics tasks
        "generate-daily-analytics": {
            "task": "apps.backend.tasks.analytics_tasks.generate_daily_report",
            "schedule": timedelta(days=1),
            "options": {"queue": "reports"},
        },
        # Health checks
        "health-check-integrations": {
            "task": "apps.backend.tasks.health_tasks.check_integrations",
            "schedule": timedelta(minutes=5),
            "options": {"queue": "high_priority"},
        },
        # Email tasks
        "send-pending-emails": {
            "task": "apps.backend.tasks.email_tasks.send_pending_emails",
            "schedule": timedelta(minutes=1),
            "options": {"queue": "email"},
        },
        # AI content tasks
        "process-content-generation-queue": {
            "task": "apps.backend.tasks.ai_tasks.process_generation_queue",
            "schedule": timedelta(minutes=2),
            "options": {"queue": "ai_generation"},
        },
    }

    # Beat settings
    beat_scheduler = "celery.beat:PersistentScheduler"
    beat_schedule_filename = "/app/celerybeat-schedule/celerybeat-schedule.db"
    beat_max_loop_interval = 60
    beat_sync_every = 180  # Sync schedule to database every 3 minutes

    # ----------------------------------------
    # Queue Configuration
    # ----------------------------------------
    task_default_queue = "default"
    task_default_exchange = "default"
    task_default_exchange_type = "direct"
    task_default_routing_key = "default"

    # Define queues with different priorities
    task_queues = (
        Queue("default", Exchange("default"), routing_key="default"),
        Queue(
            "high_priority",
            Exchange("high_priority"),
            routing_key="high_priority",
            priority=10,
            max_priority=10,
        ),
        Queue(
            "low_priority",
            Exchange("low_priority"),
            routing_key="low_priority",
            priority=1,
            max_priority=10,
        ),
        Queue("email", Exchange("email"), routing_key="email"),
        Queue("reports", Exchange("reports"), routing_key="reports"),
        Queue("ai_generation", Exchange("ai_generation"), routing_key="ai_generation"),
    )

    # Task routing
    task_routes = {
        "apps.backend.tasks.email_tasks.*": {"queue": "email"},
        "apps.backend.tasks.report_tasks.*": {"queue": "reports"},
        "apps.backend.tasks.ai_tasks.*": {"queue": "ai_generation"},
        "apps.backend.tasks.cleanup_tasks.*": {"queue": "low_priority"},
        "apps.backend.tasks.critical_tasks.*": {"queue": "high_priority"},
    }

    # ----------------------------------------
    # Monitoring & Logging
    # ----------------------------------------
    worker_log_format = "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s"
    worker_task_log_format = (
        "[%(asctime)s: %(levelname)s/%(processName)s] %(task_name)s[%(task_id)s]: %(message)s"
    )

    # Events for monitoring
    worker_send_task_events = True
    task_send_sent_event = True

    # ----------------------------------------
    # Security Settings
    # ----------------------------------------
    # Content type whitelist (security)
    accept_content = ["json"]
    task_serializer = "json"
    result_serializer = "json"

    # Prevent pickle serialization (security risk)
    task_always_eager = False  # Don't run tasks synchronously
    task_eager_propagates = False

    # ----------------------------------------
    # Performance Optimizations
    # ----------------------------------------
    # Connection pool settings
    broker_pool_limit = 10
    redis_max_connections = 20
    redis_socket_keepalive = True
    redis_socket_keepalive_options = {
        1: 3,  # TCP_KEEPIDLE
        2: 3,  # TCP_KEEPINTVL
        3: 3,  # TCP_KEEPCNT
    }

    # Batching for performance
    worker_prefetch_multiplier = 4
    task_annotations = {
        "*": {"rate_limit": "1000/m"},  # Default rate limit
        "apps.backend.tasks.email_tasks.*": {"rate_limit": "100/m"},
        "apps.backend.tasks.ai_tasks.*": {"rate_limit": "10/m"},
    }


# Apply configuration
app.config_from_object(CeleryConfig())

# ============================================
# TASK BASE CLASS
# ============================================


class BaseTask(Task):
    """Base task with automatic retry and error handling"""

    autoretry_for = (Exception,)
    max_retries = 3
    default_retry_delay = 60  # seconds

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Log task failures"""
        logger.error(f"Task {self.name}[{task_id}] failed: {exc}", exc_info=einfo)
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Log task retries"""
        logger.warning(f"Task {self.name}[{task_id}] retrying: {exc}")
        super().on_retry(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        """Log task success"""
        logger.info(f"Task {self.name}[{task_id}] succeeded")
        super().on_success(retval, task_id, args, kwargs)


# Set as default task base
app.Task = BaseTask

# ============================================
# CELERY SIGNALS
# ============================================


@setup_logging.connect
def config_loggers(*args, **kwargs):
    """Configure logging for Celery"""
    from logging.config import dictConfig

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "[%(asctime)s: %(levelname)s/%(name)s] %(message)s",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                },
            },
            "root": {
                "level": os.getenv("LOG_LEVEL", "INFO"),
                "handlers": ["console"],
            },
            "loggers": {
                "celery": {
                    "level": os.getenv("CELERY_LOG_LEVEL", "INFO"),
                },
                "apps.backend.tasks": {
                    "level": "INFO",
                },
            },
        }
    )


@worker_ready.connect
def on_worker_ready(sender, **kwargs):
    """Called when worker is ready to accept tasks"""
    logger.info(f"Celery worker ready: {sender}")


@worker_shutdown.connect
def on_worker_shutdown(sender, **kwargs):
    """Called when worker is shutting down"""
    logger.info(f"Celery worker shutting down: {sender}")


@task_failure.connect
def on_task_failure(sender, task_id, exception, args, kwargs, traceback, einfo, **kw):
    """Handle task failures globally"""
    logger.error(f"Task failed: {sender.name}[{task_id}] - {exception}")


# ============================================
# AUTO-DISCOVERY
# ============================================

# Auto-discover tasks from these modules
app.autodiscover_tasks(
    [
        "apps.backend.tasks.email_tasks",
        "apps.backend.tasks.cleanup_tasks",
        "apps.backend.tasks.report_tasks",
        "apps.backend.tasks.analytics_tasks",
        "apps.backend.tasks.ai_tasks",
        "apps.backend.tasks.health_tasks",
        "apps.backend.tasks.content_tasks",
    ]
)

# ============================================
# HEALTH CHECK TASK
# ============================================


@app.task(bind=True, name="celery.health_check")
def health_check(self) -> dict[str, Any]:
    """Health check task for monitoring"""
    return {
        "status": "healthy",
        "worker": self.request.hostname,
        "task_id": self.request.id,
    }


if __name__ == "__main__":
    app.start()

"""
Enhanced Celery Application Factory
====================================
Creates and configures Celery application instances with tenant-aware task execution,
Redis clustering support, and comprehensive monitoring capabilities.

Features:
- Multi-tenancy with organization context
- Redis Cluster support for scaling
- Prometheus metrics integration
- Task retry with exponential backoff
- Dead letter queue handling
- Self-hosted monitoring (no AWS)
"""

import os
import logging
from typing import Any, Dict, Optional
from celery import Celery, Task
from celery.signals import (
    setup_logging,
    worker_ready,
    worker_shutdown,
    task_prerun,
    task_postrun,
    task_failure,
    task_retry,
    task_success,
    beat_init
)
from kombu import Queue, Exchange
import socket
from datetime import datetime

from .config import get_worker_config, get_queue_definitions, get_monitoring_config
from .beat_schedule import get_beat_schedule
from toolboxai_settings import settings

logger = logging.getLogger(__name__)


class TenantAwareTask(Task):
    """
    Base task class with tenant context management and enhanced error handling.

    Features:
    - Automatic tenant context injection
    - Structured logging with tenant information
    - Retry logic with exponential backoff
    - Dead letter queue integration
    - Performance monitoring
    """

    abstract = True
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3, 'countdown': 60}
    retry_backoff = True
    retry_backoff_max = 700
    retry_jitter = True

    def __init__(self):
        super().__init__()
        self.tenant_context = {}

    def apply_async(self, args=None, kwargs=None, task_id=None,
                   producer=None, link=None, link_error=None,
                   shadow=None, **options):
        """Override to inject tenant context."""
        kwargs = kwargs or {}

        # Inject tenant context if not already present
        if 'organization_id' not in kwargs and hasattr(self, '_current_organization_id'):
            kwargs['organization_id'] = self._current_organization_id

        # Add tenant metadata to task
        if 'tenant_context' not in kwargs and self.tenant_context:
            kwargs['tenant_context'] = self.tenant_context

        return super().apply_async(
            args=args, kwargs=kwargs, task_id=task_id,
            producer=producer, link=link, link_error=link_error,
            shadow=shadow, **options
        )

    def __call__(self, *args, **kwargs):
        """Execute task with tenant context."""
        # Set up tenant context
        organization_id = kwargs.pop('organization_id', None)
        tenant_context = kwargs.pop('tenant_context', {})

        if organization_id:
            self.set_tenant_context(organization_id, tenant_context)

        try:
            return super().__call__(*args, **kwargs)
        finally:
            # Clean up tenant context
            self.clear_tenant_context()

    def set_tenant_context(self, organization_id: str, context: Dict[str, Any] = None):
        """Set tenant context for task execution."""
        self.tenant_context = {
            'organization_id': organization_id,
            'set_at': datetime.utcnow().isoformat(),
            **(context or {})
        }

        # Update logger context
        self.logger = logging.getLogger(f"{self.name}.org_{organization_id}")

    def clear_tenant_context(self):
        """Clear tenant context after task execution."""
        self.tenant_context = {}
        self.logger = logging.getLogger(self.name)

    def get_tenant_id(self) -> Optional[str]:
        """Get current tenant ID."""
        return self.tenant_context.get('organization_id')

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Enhanced failure handling with tenant context and dead letter queue."""
        tenant_id = self.get_tenant_id()

        # Log failure with tenant context
        error_data = {
            'task_name': self.name,
            'task_id': task_id,
            'tenant_id': tenant_id,
            'error': str(exc),
            'args': args,
            'kwargs': kwargs,
            'failed_at': datetime.utcnow().isoformat()
        }

        self.logger.error(f"Task failed: {error_data}")

        # Send to dead letter queue if max retries exceeded
        if self.request.retries >= self.max_retries:
            self._send_to_dead_letter_queue(error_data)

        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Log retry attempts with tenant context."""
        tenant_id = self.get_tenant_id()

        retry_data = {
            'task_name': self.name,
            'task_id': task_id,
            'tenant_id': tenant_id,
            'retry_count': self.request.retries,
            'max_retries': self.max_retries,
            'error': str(exc),
            'retry_at': datetime.utcnow().isoformat()
        }

        self.logger.warning(f"Task retry: {retry_data}")
        super().on_retry(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        """Log successful completion with tenant context."""
        tenant_id = self.get_tenant_id()

        success_data = {
            'task_name': self.name,
            'task_id': task_id,
            'tenant_id': tenant_id,
            'duration': getattr(self.request, 'duration', None),
            'completed_at': datetime.utcnow().isoformat()
        }

        self.logger.info(f"Task completed: {success_data}")
        super().on_success(retval, task_id, args, kwargs)

    def _send_to_dead_letter_queue(self, error_data: Dict[str, Any]):
        """Send failed task to dead letter queue for manual review."""
        try:
            from apps.backend.core.cache import redis_client

            dead_letter_key = f"dead_letter:{error_data['task_name']}:{error_data['task_id']}"
            redis_client.setex(dead_letter_key, 86400 * 7, str(error_data))  # Keep for 7 days

            self.logger.error(f"Task sent to dead letter queue: {dead_letter_key}")
        except Exception as e:
            self.logger.error(f"Failed to send task to dead letter queue: {e}")


def create_celery_app(name: str = "toolboxai_workers") -> Celery:
    """
    Create and configure Celery application with all enhancements.

    Args:
        name: Application name

    Returns:
        Configured Celery application instance
    """
    # Get configuration
    worker_config = get_worker_config()
    monitoring_config = get_monitoring_config()

    # Create Celery app with task discovery
    app = Celery(
        name,
        include=[
            "apps.backend.workers.tasks.content_tasks",
            "apps.backend.workers.tasks.email_tasks",
            "apps.backend.workers.tasks.analytics_tasks",
            "apps.backend.workers.tasks.roblox_tasks",
            "apps.backend.workers.tasks.cleanup_tasks",
            "apps.backend.workers.tasks.tenant_tasks"
        ]
    )

    # Apply worker configuration
    celery_config = worker_config.to_celery_config()
    app.config_from_object(celery_config)

    # Configure queues
    app.conf.task_queues = get_queue_definitions()

    # Configure beat schedule
    app.conf.beat_schedule = get_beat_schedule()

    # Set task base class
    app.Task = TenantAwareTask

    # Configure monitoring
    _configure_monitoring(app, monitoring_config)

    return app


def _configure_monitoring(app: Celery, monitoring_config: Dict[str, Any]):
    """Configure monitoring and metrics collection."""

    # Configure Prometheus metrics if enabled
    if monitoring_config.get('prometheus', {}).get('enabled'):
        try:
            from prometheus_client import Counter, Histogram, Gauge, start_http_server

            # Define metrics
            task_counter = Counter('celery_tasks_total', 'Total Celery tasks', ['task_name', 'status', 'tenant_id'])
            task_duration = Histogram('celery_task_duration_seconds', 'Task duration', ['task_name', 'tenant_id'])
            active_workers = Gauge('celery_active_workers', 'Number of active workers')
            queue_length = Gauge('celery_queue_length', 'Queue length', ['queue_name'])

            # Start Prometheus HTTP server
            prometheus_port = monitoring_config['prometheus']['port']
            start_http_server(prometheus_port)
            logger.info(f"Prometheus metrics server started on port {prometheus_port}")

            # Store metrics for use in signal handlers
            app.metrics = {
                'task_counter': task_counter,
                'task_duration': task_duration,
                'active_workers': active_workers,
                'queue_length': queue_length
            }

        except ImportError:
            logger.warning("Prometheus client not available, metrics disabled")
        except Exception as e:
            logger.error(f"Failed to configure Prometheus metrics: {e}")


# Signal handlers for monitoring and logging
@setup_logging.connect
def config_loggers(*args, **kwargs):
    """Configure structured logging for Celery workers."""
    from logging.config import dictConfig

    monitoring_config = get_monitoring_config()
    log_config = monitoring_config.get('logging', {})

    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "structured": {
                "format": log_config.get('format', "[%(asctime)s: %(levelname)s/%(name)s] %(message)s"),
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "structured",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "/var/log/celery/worker.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "formatter": "structured",
            } if "file" in log_config.get('handlers', []) else None
        },
        "root": {
            "level": log_config.get('level', 'INFO'),
            "handlers": [h for h in ["console", "file"] if h in log_config.get('handlers', ['console'])],
        },
        "loggers": {
            "celery": {"level": "INFO"},
            "apps.backend.workers": {"level": "INFO"},
        },
    })


@worker_ready.connect
def on_worker_ready(sender, **kwargs):
    """Called when worker is ready to accept tasks."""
    hostname = socket.gethostname()
    logger.info(f"Celery worker ready: {sender} on {hostname}")

    # Update worker metrics if available
    if hasattr(sender.app, 'metrics'):
        sender.app.metrics['active_workers'].inc()


@worker_shutdown.connect
def on_worker_shutdown(sender, **kwargs):
    """Called when worker is shutting down."""
    hostname = socket.gethostname()
    logger.info(f"Celery worker shutting down: {sender} on {hostname}")

    # Update worker metrics if available
    if hasattr(sender.app, 'metrics'):
        sender.app.metrics['active_workers'].dec()


@task_prerun.connect
def on_task_prerun(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """Called before task execution."""
    tenant_id = kwargs.get('organization_id', 'unknown') if kwargs else 'unknown'
    logger.info(f"Starting task: {sender.name}[{task_id}] tenant={tenant_id}")


@task_postrun.connect
def on_task_postrun(sender=None, task_id=None, task=None, args=None, kwargs=None,
                   retval=None, state=None, **kwds):
    """Called after task execution."""
    tenant_id = kwargs.get('organization_id', 'unknown') if kwargs else 'unknown'
    logger.info(f"Finished task: {sender.name}[{task_id}] tenant={tenant_id} state={state}")

    # Update Prometheus metrics if available
    if hasattr(sender.app, 'metrics'):
        sender.app.metrics['task_counter'].labels(
            task_name=sender.name,
            status=state.lower(),
            tenant_id=tenant_id
        ).inc()


@task_failure.connect
def on_task_failure(sender=None, task_id=None, exception=None, args=None, kwargs=None,
                   traceback=None, einfo=None, **kwds):
    """Global task failure handler."""
    tenant_id = kwargs.get('organization_id', 'unknown') if kwargs else 'unknown'
    logger.error(f"Task failed: {sender.name}[{task_id}] tenant={tenant_id} error={exception}")


@task_retry.connect
def on_task_retry(sender=None, task_id=None, reason=None, einfo=None, **kwds):
    """Global task retry handler."""
    logger.warning(f"Task retry: {sender.name}[{task_id}] reason={reason}")


@task_success.connect
def on_task_success(sender=None, result=None, **kwds):
    """Global task success handler."""
    logger.debug(f"Task success: {sender.name}")


@beat_init.connect
def on_beat_init(sender=None, **kwargs):
    """Called when beat scheduler starts."""
    logger.info(f"Celery beat scheduler initialized: {sender}")


# Create the main Celery app instance
app = create_celery_app()

# Health check task
@app.task(bind=True, name="celery.health_check")
def health_check(self) -> Dict[str, Any]:
    """Health check task for container monitoring."""
    return {
        "status": "healthy",
        "worker": self.request.hostname,
        "task_id": self.request.id,
        "timestamp": datetime.utcnow().isoformat(),
        "tenant_context": getattr(self, 'tenant_context', {}),
    }


# Monitoring task for queue lengths
@app.task(bind=True, name="celery.monitor_queues")
def monitor_queues(self) -> Dict[str, Any]:
    """Monitor queue lengths for alerting."""
    try:
        inspector = app.control.inspect()
        active = inspector.active() or {}

        queue_stats = {}
        for worker, tasks in active.items():
            for task in tasks:
                queue = task.get('delivery_info', {}).get('routing_key', 'unknown')
                queue_stats[queue] = queue_stats.get(queue, 0) + 1

        # Update Prometheus metrics if available
        if hasattr(app, 'metrics'):
            for queue_name, length in queue_stats.items():
                app.metrics['queue_length'].labels(queue_name=queue_name).set(length)

        return {
            "status": "success",
            "queue_stats": queue_stats,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to monitor queues: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


if __name__ == "__main__":
    app.start()
"""
Prometheus Metrics Exporter for ToolBoxAI Backend
==============================================

This module provides comprehensive metrics collection for the ToolBoxAI backend application,
including API performance, business metrics, and system health indicators.

Features:
- Custom histogram and counter metrics
- Automatic request/response tracking
- Business logic metrics
- Cache performance metrics
- Database query performance
- Real-time agent task metrics
- Pusher event tracking
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any

from fastapi import FastAPI, Response
from fastapi.responses import PlainTextResponse
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    CollectorRegistry,
    Counter,
    Enum,
    Gauge,
    Histogram,
    Info,
    generate_latest,
)

# Import settings
from apps.backend.core.config import settings

logger = logging.getLogger(__name__)


class ToolBoxAIMetrics:
    """
    Central metrics collector for ToolBoxAI application.

    Provides comprehensive monitoring capabilities including:
    - API performance (RED metrics)
    - Business metrics
    - System resource utilization
    - Cache performance
    - Database performance
    """

    def __init__(self, registry: CollectorRegistry | None = None):
        self.registry = registry or REGISTRY
        self._init_metrics()
        self._init_business_metrics()
        self._init_cache_metrics()
        self._init_database_metrics()
        self._init_pusher_metrics()
        self._init_agent_metrics()

        # Internal tracking
        self._active_requests = {}
        self._request_start_times = {}

    def _init_metrics(self):
        """Initialize core API performance metrics (RED pattern)"""

        # Request duration histogram with detailed buckets for <150ms SLA
        self.http_request_duration = Histogram(
            name="http_request_duration_seconds",
            documentation="HTTP request duration in seconds",
            labelnames=["method", "endpoint", "status_code", "handler"],
            buckets=[
                0.001,
                0.005,
                0.01,
                0.025,
                0.05,
                0.075,
                0.1,
                0.15,
                0.25,
                0.5,
                1.0,
                2.0,
                5.0,
            ],
            registry=self.registry,
        )

        # Request counter
        self.http_requests_total = Counter(
            name="http_requests_total",
            documentation="Total number of HTTP requests",
            labelnames=["method", "endpoint", "status_code", "handler"],
            registry=self.registry,
        )

        # Request size histogram
        self.http_request_size_bytes = Histogram(
            name="http_request_size_bytes",
            documentation="HTTP request size in bytes",
            labelnames=["method", "endpoint"],
            registry=self.registry,
        )

        # Response size histogram
        self.http_response_size_bytes = Histogram(
            name="http_response_size_bytes",
            documentation="HTTP response size in bytes",
            labelnames=["method", "endpoint", "status_code"],
            registry=self.registry,
        )

        # Active connections gauge
        self.http_active_requests = Gauge(
            name="http_active_requests",
            documentation="Number of active HTTP requests",
            registry=self.registry,
        )

        # Error rate counter
        self.http_errors_total = Counter(
            name="http_errors_total",
            documentation="Total number of HTTP errors",
            labelnames=["method", "endpoint", "status_code", "error_type"],
            registry=self.registry,
        )

        # Application info
        self.app_info = Info(
            name="toolboxai_app_info",
            documentation="Application information",
            registry=self.registry,
        )
        self.app_info.info(
            {
                "version": settings.APP_VERSION,
                "name": settings.APP_NAME,
                "environment": settings.ENVIRONMENT,
            }
        )

        # Application health status
        self.app_health_status = Enum(
            name="toolboxai_app_health",
            documentation="Application health status",
            states=["healthy", "degraded", "unhealthy"],
            registry=self.registry,
        )
        self.app_health_status.state("healthy")

        # Uptime gauge
        self.app_uptime_seconds = Gauge(
            name="toolboxai_uptime_seconds",
            documentation="Application uptime in seconds",
            registry=self.registry,
        )

    def _init_business_metrics(self):
        """Initialize business-specific metrics"""

        # User metrics
        self.active_users_total = Gauge(
            name="toolboxai_active_users_total",
            documentation="Number of active users",
            labelnames=["user_type"],
            registry=self.registry,
        )

        self.user_registrations_total = Counter(
            name="toolboxai_user_registrations_total",
            documentation="Total user registrations",
            labelnames=["user_type", "source"],
            registry=self.registry,
        )

        # Content generation metrics
        self.content_generation_requests = Counter(
            name="toolboxai_content_generation_requests_total",
            documentation="Total content generation requests",
            labelnames=["content_type", "subject", "grade_level", "status"],
            registry=self.registry,
        )

        self.content_generation_duration = Histogram(
            name="toolboxai_content_generation_duration_seconds",
            documentation="Content generation duration in seconds",
            labelnames=["content_type", "subject", "grade_level"],
            buckets=[1, 5, 10, 30, 60, 120, 300],
            registry=self.registry,
        )

        # Roblox-specific metrics
        self.roblox_script_deployments = Counter(
            name="toolboxai_roblox_script_deployments_total",
            documentation="Total Roblox script deployments",
            labelnames=["script_type", "status"],
            registry=self.registry,
        )

        self.roblox_active_environments = Gauge(
            name="toolboxai_roblox_active_environments",
            documentation="Number of active Roblox environments",
            registry=self.registry,
        )

        # Educational metrics
        self.lessons_created_total = Counter(
            name="toolboxai_lessons_created_total",
            documentation="Total lessons created",
            labelnames=["subject", "grade_level"],
            registry=self.registry,
        )

        self.quiz_completions_total = Counter(
            name="toolboxai_quiz_completions_total",
            documentation="Total quiz completions",
            labelnames=["subject", "grade_level", "score_range"],
            registry=self.registry,
        )

    def _init_cache_metrics(self):
        """Initialize cache performance metrics"""

        # Cache hit/miss counters
        self.cache_operations_total = Counter(
            name="toolboxai_cache_operations_total",
            documentation="Total cache operations",
            labelnames=["cache_type", "operation", "result"],
            registry=self.registry,
        )

        # Cache hit rate gauge
        self.cache_hit_rate = Gauge(
            name="toolboxai_cache_hit_rate",
            documentation="Cache hit rate percentage",
            labelnames=["cache_type"],
            registry=self.registry,
        )

        # Cache size gauge
        self.cache_size_bytes = Gauge(
            name="toolboxai_cache_size_bytes",
            documentation="Cache size in bytes",
            labelnames=["cache_type"],
            registry=self.registry,
        )

        # Redis-specific metrics
        self.redis_connection_pool_size = Gauge(
            name="toolboxai_redis_connection_pool_size",
            documentation="Redis connection pool size",
            registry=self.registry,
        )

        self.redis_operations_duration = Histogram(
            name="toolboxai_redis_operations_duration_seconds",
            documentation="Redis operation duration in seconds",
            labelnames=["operation"],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5],
            registry=self.registry,
        )

    def _init_database_metrics(self):
        """Initialize database performance metrics"""

        # Database query performance
        self.db_query_duration = Histogram(
            name="toolboxai_database_query_duration_seconds",
            documentation="Database query duration in seconds",
            labelnames=["query_type", "table", "operation"],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
            registry=self.registry,
        )

        self.db_queries_total = Counter(
            name="toolboxai_database_queries_total",
            documentation="Total database queries",
            labelnames=["query_type", "table", "operation", "status"],
            registry=self.registry,
        )

        # Connection pool metrics
        self.db_connection_pool_size = Gauge(
            name="toolboxai_database_connection_pool_size",
            documentation="Database connection pool size",
            labelnames=["pool_type"],
            registry=self.registry,
        )

        self.db_connection_pool_active = Gauge(
            name="toolboxai_database_connection_pool_active",
            documentation="Active database connections",
            labelnames=["pool_type"],
            registry=self.registry,
        )

        # Migration metrics
        self.db_migrations_total = Counter(
            name="toolboxai_database_migrations_total",
            documentation="Total database migrations",
            labelnames=["direction", "status"],
            registry=self.registry,
        )

    def _init_pusher_metrics(self):
        """Initialize Pusher/WebSocket metrics"""

        # Pusher event metrics
        self.pusher_events_total = Counter(
            name="toolboxai_pusher_events_total",
            documentation="Total Pusher events sent",
            labelnames=["channel", "event_type", "status"],
            registry=self.registry,
        )

        self.pusher_channel_subscriptions = Gauge(
            name="toolboxai_pusher_channel_subscriptions",
            documentation="Number of active Pusher channel subscriptions",
            labelnames=["channel"],
            registry=self.registry,
        )

        # WebSocket metrics (legacy support)
        self.websocket_connections_total = Gauge(
            name="toolboxai_websocket_connections_total",
            documentation="Total active WebSocket connections",
            registry=self.registry,
        )

        self.websocket_messages_total = Counter(
            name="toolboxai_websocket_messages_total",
            documentation="Total WebSocket messages",
            labelnames=["message_type", "direction", "status"],
            registry=self.registry,
        )

    def _init_agent_metrics(self):
        """Initialize AI agent metrics"""

        # Agent task metrics
        self.agent_tasks_total = Counter(
            name="toolboxai_agent_tasks_total",
            documentation="Total agent tasks",
            labelnames=["agent_type", "task_type", "status"],
            registry=self.registry,
        )

        self.agent_task_duration = Histogram(
            name="toolboxai_agent_task_duration_seconds",
            documentation="Agent task duration in seconds",
            labelnames=["agent_type", "task_type"],
            buckets=[1, 5, 10, 30, 60, 120, 300, 600],
            registry=self.registry,
        )

        self.active_agent_tasks = Gauge(
            name="toolboxai_active_agent_tasks",
            documentation="Number of active agent tasks",
            labelnames=["agent_type"],
            registry=self.registry,
        )

        # LLM API metrics
        self.llm_api_requests_total = Counter(
            name="toolboxai_llm_api_requests_total",
            documentation="Total LLM API requests",
            labelnames=["provider", "model", "status"],
            registry=self.registry,
        )

        self.llm_api_duration = Histogram(
            name="toolboxai_llm_api_duration_seconds",
            documentation="LLM API request duration in seconds",
            labelnames=["provider", "model"],
            buckets=[0.5, 1, 2, 5, 10, 30, 60],
            registry=self.registry,
        )

        self.llm_token_usage_total = Counter(
            name="toolboxai_llm_token_usage_total",
            documentation="Total LLM tokens used",
            labelnames=["provider", "model", "token_type"],
            registry=self.registry,
        )

    # Request tracking methods
    @asynccontextmanager
    async def track_request(self, method: str, endpoint: str, handler: str = "unknown"):
        """Context manager to track request duration and status"""
        request_id = f"{method}:{endpoint}:{time.time()}"
        start_time = time.time()

        # Track active request
        self.http_active_requests.inc()
        self._active_requests[request_id] = {
            "method": method,
            "endpoint": endpoint,
            "handler": handler,
            "start_time": start_time,
        }

        try:
            yield
        finally:
            # Clean up tracking
            time.time() - start_time
            self.http_active_requests.dec()
            if request_id in self._active_requests:
                del self._active_requests[request_id]

    def record_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration: float,
        handler: str = "unknown",
        request_size: int | None = None,
        response_size: int | None = None,
        error_type: str | None = None,
    ):
        """Record a completed HTTP request with all metrics"""

        labels = {
            "method": method,
            "endpoint": endpoint,
            "status_code": str(status_code),
            "handler": handler,
        }

        # Core metrics
        self.http_requests_total.labels(**labels).inc()
        self.http_request_duration.labels(**labels).observe(duration)

        # Size metrics
        if request_size is not None:
            self.http_request_size_bytes.labels(method=method, endpoint=endpoint).observe(
                request_size
            )

        if response_size is not None:
            self.http_response_size_bytes.labels(
                method=method, endpoint=endpoint, status_code=str(status_code)
            ).observe(response_size)

        # Error metrics
        if status_code >= 400:
            error_labels = {
                **labels,
                "error_type": error_type or self._classify_error(status_code),
            }
            self.http_errors_total.labels(**error_labels).inc()

    def _classify_error(self, status_code: int) -> str:
        """Classify error type based on status code"""
        if 400 <= status_code < 500:
            return "client_error"
        elif 500 <= status_code < 600:
            return "server_error"
        else:
            return "unknown_error"

    # Business metrics methods
    def record_user_registration(self, user_type: str = "student", source: str = "web"):
        """Record a new user registration"""
        self.user_registrations_total.labels(user_type=user_type, source=source).inc()

    def update_active_users(self, count: int, user_type: str = "total"):
        """Update active user count"""
        self.active_users_total.labels(user_type=user_type).set(count)

    def record_content_generation(
        self,
        content_type: str,
        subject: str,
        grade_level: str,
        duration: float,
        status: str = "success",
    ):
        """Record content generation metrics"""
        labels = {
            "content_type": content_type,
            "subject": subject,
            "grade_level": grade_level,
        }

        self.content_generation_requests.labels(**labels, status=status).inc()

        if status == "success":
            self.content_generation_duration.labels(**labels).observe(duration)

    def record_lesson_creation(self, subject: str, grade_level: str):
        """Record lesson creation"""
        self.lessons_created_total.labels(subject=subject, grade_level=grade_level).inc()

    def record_quiz_completion(self, subject: str, grade_level: str, score: int):
        """Record quiz completion with score classification"""
        score_range = self._classify_score(score)
        self.quiz_completions_total.labels(
            subject=subject, grade_level=grade_level, score_range=score_range
        ).inc()

    def _classify_score(self, score: int) -> str:
        """Classify quiz score into ranges"""
        if score >= 90:
            return "excellent"
        elif score >= 80:
            return "good"
        elif score >= 70:
            return "satisfactory"
        elif score >= 60:
            return "needs_improvement"
        else:
            return "unsatisfactory"

    # Cache metrics methods
    def record_cache_operation(self, cache_type: str, operation: str, result: str):
        """Record cache operation (hit/miss/error)"""
        self.cache_operations_total.labels(
            cache_type=cache_type, operation=operation, result=result
        ).inc()

    def update_cache_hit_rate(self, cache_type: str, hit_rate: float):
        """Update cache hit rate percentage"""
        self.cache_hit_rate.labels(cache_type=cache_type).set(hit_rate)

    def update_cache_size(self, cache_type: str, size_bytes: int):
        """Update cache size in bytes"""
        self.cache_size_bytes.labels(cache_type=cache_type).set(size_bytes)

    # Database metrics methods
    def record_database_query(
        self,
        query_type: str,
        table: str,
        operation: str,
        duration: float,
        status: str = "success",
    ):
        """Record database query performance"""
        labels = {"query_type": query_type, "table": table, "operation": operation}

        self.db_queries_total.labels(**labels, status=status).inc()

        if status == "success":
            self.db_query_duration.labels(**labels).observe(duration)

    def update_connection_pool_metrics(self, pool_type: str, total: int, active: int):
        """Update database connection pool metrics"""
        self.db_connection_pool_size.labels(pool_type=pool_type).set(total)
        self.db_connection_pool_active.labels(pool_type=pool_type).set(active)

    # Agent metrics methods
    def record_agent_task(
        self, agent_type: str, task_type: str, duration: float, status: str = "success"
    ):
        """Record agent task completion"""
        labels = {"agent_type": agent_type, "task_type": task_type}

        self.agent_tasks_total.labels(**labels, status=status).inc()

        if status == "success":
            self.agent_task_duration.labels(**labels).observe(duration)

    def update_active_agent_tasks(self, agent_type: str, count: int):
        """Update active agent task count"""
        self.active_agent_tasks.labels(agent_type=agent_type).set(count)

    def record_llm_api_call(
        self,
        provider: str,
        model: str,
        duration: float,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        status: str = "success",
    ):
        """Record LLM API call metrics"""
        labels = {"provider": provider, "model": model}

        self.llm_api_requests_total.labels(**labels, status=status).inc()

        if status == "success":
            self.llm_api_duration.labels(**labels).observe(duration)

            if prompt_tokens > 0:
                self.llm_token_usage_total.labels(**labels, token_type="prompt").inc(prompt_tokens)

            if completion_tokens > 0:
                self.llm_token_usage_total.labels(**labels, token_type="completion").inc(
                    completion_tokens
                )

    # Pusher metrics methods
    def record_pusher_event(self, channel: str, event_type: str, status: str = "success"):
        """Record Pusher event"""
        self.pusher_events_total.labels(channel=channel, event_type=event_type, status=status).inc()

    def update_pusher_subscriptions(self, channel: str, count: int):
        """Update Pusher channel subscription count"""
        self.pusher_channel_subscriptions.labels(channel=channel).set(count)

    # Health and status methods
    def set_health_status(self, status: str):
        """Set application health status"""
        if status in ["healthy", "degraded", "unhealthy"]:
            self.app_health_status.state(status)

    def update_uptime(self, start_time: float):
        """Update application uptime"""
        uptime = time.time() - start_time
        self.app_uptime_seconds.set(uptime)

    # Utility methods
    def get_metrics(self) -> str:
        """Get all metrics in Prometheus format"""
        return generate_latest(self.registry).decode("utf-8")


# Global metrics instance
metrics = ToolBoxAIMetrics()


# Decorator for timing functions
def time_function(metric_name: str = None, labels: dict[str, str] = None):
    """Decorator to time function execution"""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                # Record success
                if metric_name and hasattr(metrics, metric_name):
                    metric = getattr(metrics, metric_name)
                    if labels:
                        metric.labels(**labels).observe(duration)
                    else:
                        metric.observe(duration)

                return result
            except Exception:
                duration = time.time() - start_time

                # Record error
                if metric_name and hasattr(metrics, metric_name):
                    error_labels = labels.copy() if labels else {}
                    error_labels["status"] = "error"
                    metric = getattr(metrics, metric_name)
                    if hasattr(metric, "labels"):
                        metric.labels(**error_labels).observe(duration)

                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # Record success
                if metric_name and hasattr(metrics, metric_name):
                    metric = getattr(metrics, metric_name)
                    if labels:
                        metric.labels(**labels).observe(duration)
                    else:
                        metric.observe(duration)

                return result
            except Exception:
                duration = time.time() - start_time

                # Record error
                if metric_name and hasattr(metrics, metric_name):
                    error_labels = labels.copy() if labels else {}
                    error_labels["status"] = "error"
                    metric = getattr(metrics, metric_name)
                    if hasattr(metric, "labels"):
                        metric.labels(**error_labels).observe(duration)

                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


def setup_metrics_endpoint(app: FastAPI, path: str = "/metrics"):
    """Setup metrics endpoint for Prometheus scraping"""

    @app.get(path, response_class=PlainTextResponse)
    async def get_metrics():
        """Prometheus metrics endpoint"""
        try:
            metrics_data = metrics.get_metrics()
            return Response(content=metrics_data, media_type=CONTENT_TYPE_LATEST)
        except Exception as e:
            logger.error(f"Error generating metrics: {e}")
            return Response(
                content="# Error generating metrics\n",
                status_code=500,
                media_type=CONTENT_TYPE_LATEST,
            )

    logger.info(f"Metrics endpoint configured at {path}")


# Health check function for metrics
def check_metrics_health() -> dict[str, Any]:
    """Check metrics system health"""
    try:
        # Test metric generation
        test_metrics = metrics.get_metrics()

        # Count total metrics
        metric_lines = [
            line for line in test_metrics.split("\n") if line and not line.startswith("#")
        ]

        return {
            "status": "healthy",
            "total_metrics": len(metric_lines),
            "registry_size": len(metrics.registry._collector_to_names),
            "last_collection_time": time.time(),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "last_collection_time": time.time(),
        }


# Export main components
__all__ = [
    "ToolBoxAIMetrics",
    "metrics",
    "time_function",
    "setup_metrics_endpoint",
    "check_metrics_health",
]

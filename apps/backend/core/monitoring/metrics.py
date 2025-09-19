"""
Prometheus Metrics for ToolBoxAI Monitoring
Provides comprehensive metrics for authentication, API usage, and security monitoring
"""

import time
from typing import Callable, Dict, Any, Optional
from functools import wraps
import logging
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Summary,
    generate_latest,
    REGISTRY,
    CollectorRegistry,
    CONTENT_TYPE_LATEST
)
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Create custom registry if needed
metrics_registry = REGISTRY

# Authentication Metrics
auth_attempts = Counter(
    'auth_attempts_total',
    'Total number of authentication attempts',
    ['method', 'status'],  # method: jwt, api_key, oauth | status: success, failed, expired
    registry=metrics_registry
)

auth_token_rotations = Counter(
    'auth_token_rotations_total',
    'Total number of JWT token rotations',
    registry=metrics_registry
)

active_sessions = Gauge(
    'active_sessions_count',
    'Number of active user sessions',
    ['user_type'],  # admin, teacher, student
    registry=metrics_registry
)

api_key_validations = Counter(
    'api_key_validations_total',
    'Total number of API key validations',
    ['scope', 'status'],  # scope: read, write, admin | status: valid, invalid, rate_limited
    registry=metrics_registry
)

# Request Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=metrics_registry
)

http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
    registry=metrics_registry
)

http_request_size = Summary(
    'http_request_size_bytes',
    'HTTP request body size',
    ['method', 'endpoint'],
    registry=metrics_registry
)

http_response_size = Summary(
    'http_response_size_bytes',
    'HTTP response body size',
    ['method', 'endpoint'],
    registry=metrics_registry
)

# WebSocket Metrics
websocket_connections = Gauge(
    'websocket_connections_active',
    'Number of active WebSocket connections',
    ['client_type'],  # roblox_studio, dashboard, api
    registry=metrics_registry
)

websocket_messages = Counter(
    'websocket_messages_total',
    'Total number of WebSocket messages',
    ['direction', 'type'],  # direction: sent, received | type: heartbeat, data, error
    registry=metrics_registry
)

# Agent System Metrics
agent_tasks = Counter(
    'agent_tasks_total',
    'Total number of agent tasks executed',
    ['agent_type', 'status'],  # status: success, failed, timeout
    registry=metrics_registry
)

agent_execution_time = Histogram(
    'agent_execution_seconds',
    'Agent task execution time',
    ['agent_type'],
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30, 60, 120, 300),
    registry=metrics_registry
)

agent_pool_size = Gauge(
    'agent_pool_size',
    'Number of agents in pool',
    ['agent_type', 'status'],  # status: idle, busy
    registry=metrics_registry
)

# Roblox Integration Metrics
roblox_deployments = Counter(
    'roblox_deployments_total',
    'Total number of Roblox deployments',
    ['status', 'content_type'],  # status: success, failed | content_type: script, model, place
    registry=metrics_registry
)

roblox_script_generations = Counter(
    'roblox_script_generations_total',
    'Total number of Roblox scripts generated',
    ['script_type', 'difficulty'],
    registry=metrics_registry
)

roblox_validations = Counter(
    'roblox_validations_total',
    'Total number of Roblox script validations',
    ['risk_level', 'status'],  # risk_level: low, medium, high | status: passed, failed
    registry=metrics_registry
)

# Database Metrics
database_queries = Counter(
    'database_queries_total',
    'Total number of database queries',
    ['operation', 'table'],  # operation: select, insert, update, delete
    registry=metrics_registry
)

database_query_duration = Histogram(
    'database_query_duration_seconds',
    'Database query execution time',
    ['operation', 'table'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5),
    registry=metrics_registry
)

database_connections = Gauge(
    'database_connections_active',
    'Number of active database connections',
    registry=metrics_registry
)

# Redis Metrics
redis_operations = Counter(
    'redis_operations_total',
    'Total number of Redis operations',
    ['operation', 'status'],  # operation: get, set, del, expire | status: success, failed
    registry=metrics_registry
)

redis_cache_hits = Counter(
    'redis_cache_hits_total',
    'Total number of Redis cache hits',
    ['cache_type'],  # auth, api_key, content, session
    registry=metrics_registry
)

redis_cache_misses = Counter(
    'redis_cache_misses_total',
    'Total number of Redis cache misses',
    ['cache_type'],
    registry=metrics_registry
)

# Error Metrics
application_errors = Counter(
    'application_errors_total',
    'Total number of application errors',
    ['error_type', 'severity'],  # severity: warning, error, critical
    registry=metrics_registry
)

# System Metrics
cpu_usage = Gauge(
    'cpu_usage_percent',
    'CPU usage percentage',
    registry=metrics_registry
)

memory_usage = Gauge(
    'memory_usage_bytes',
    'Memory usage in bytes',
    ['type'],  # rss, vms, available
    registry=metrics_registry
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP metrics for Prometheus"""

    async def dispatch(self, request: Request, call_next):
        # Skip metrics endpoint to avoid recursion
        if request.url.path == "/metrics":
            return await call_next(request)

        # Start timing
        start_time = time.time()

        # Get request size
        request_size = int(request.headers.get("content-length", 0))

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Get response size
        response_size = int(response.headers.get("content-length", 0))

        # Extract endpoint (remove path parameters)
        endpoint = request.url.path

        # Update metrics
        http_requests_total.labels(
            method=request.method,
            endpoint=endpoint,
            status=response.status_code
        ).inc()

        http_request_duration.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(duration)

        if request_size > 0:
            http_request_size.labels(
                method=request.method,
                endpoint=endpoint
            ).observe(request_size)

        if response_size > 0:
            http_response_size.labels(
                method=request.method,
                endpoint=endpoint
            ).observe(response_size)

        return response


def track_auth_attempt(method: str, success: bool):
    """Track authentication attempts"""
    status = "success" if success else "failed"
    auth_attempts.labels(method=method, status=status).inc()


def track_api_key_validation(scope: str, is_valid: bool, rate_limited: bool = False):
    """Track API key validations"""
    if rate_limited:
        status = "rate_limited"
    else:
        status = "valid" if is_valid else "invalid"
    api_key_validations.labels(scope=scope, status=status).inc()


def track_websocket_connection(client_type: str, connected: bool):
    """Track WebSocket connections"""
    if connected:
        websocket_connections.labels(client_type=client_type).inc()
    else:
        websocket_connections.labels(client_type=client_type).dec()


def track_websocket_message(direction: str, message_type: str):
    """Track WebSocket messages"""
    websocket_messages.labels(direction=direction, type=message_type).inc()


def track_agent_task(agent_type: str, execution_time: float, success: bool):
    """Track agent task execution"""
    status = "success" if success else "failed"
    agent_tasks.labels(agent_type=agent_type, status=status).inc()
    agent_execution_time.labels(agent_type=agent_type).observe(execution_time)


def track_database_query(operation: str, table: str, duration: float):
    """Track database queries"""
    database_queries.labels(operation=operation, table=table).inc()
    database_query_duration.labels(operation=operation, table=table).observe(duration)


def track_redis_operation(operation: str, success: bool):
    """Track Redis operations"""
    status = "success" if success else "failed"
    redis_operations.labels(operation=operation, status=status).inc()


def track_cache_access(cache_type: str, hit: bool):
    """Track cache hits and misses"""
    if hit:
        redis_cache_hits.labels(cache_type=cache_type).inc()
    else:
        redis_cache_misses.labels(cache_type=cache_type).inc()


def track_error(error_type: str, severity: str = "error"):
    """Track application errors"""
    application_errors.labels(error_type=error_type, severity=severity).inc()


def track_roblox_deployment(status: str, content_type: str):
    """Track Roblox deployments"""
    roblox_deployments.labels(status=status, content_type=content_type).inc()


def track_roblox_generation(script_type: str, difficulty: str):
    """Track Roblox script generations"""
    roblox_script_generations.labels(script_type=script_type, difficulty=difficulty).inc()


def track_roblox_validation(risk_level: str, passed: bool):
    """Track Roblox script validations"""
    status = "passed" if passed else "failed"
    roblox_validations.labels(risk_level=risk_level, status=status).inc()


def update_system_metrics():
    """Update system resource metrics"""
    try:
        import psutil

        # CPU usage
        cpu_usage.set(psutil.cpu_percent(interval=1))

        # Memory usage
        memory = psutil.virtual_memory()
        memory_usage.labels(type="rss").set(memory.rss)
        memory_usage.labels(type="vms").set(memory.vms)
        memory_usage.labels(type="available").set(memory.available)

        # Database connections (would need to query the database)
        # This is a placeholder - actual implementation would query pg_stat_activity
        database_connections.set(10)  # Example value

    except ImportError:
        logger.warning("psutil not installed, system metrics unavailable")
    except Exception as e:
        logger.error(f"Failed to update system metrics: {e}")


def metrics_decorator(metric_name: str = None):
    """Decorator to track function execution metrics"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                # Track successful execution
                if metric_name:
                    agent_tasks.labels(agent_type=metric_name, status="success").inc()
                    agent_execution_time.labels(agent_type=metric_name).observe(duration)

                return result
            except Exception as e:
                duration = time.time() - start_time

                # Track failed execution
                if metric_name:
                    agent_tasks.labels(agent_type=metric_name, status="failed").inc()
                    agent_execution_time.labels(agent_type=metric_name).observe(duration)
                    track_error(error_type=type(e).__name__, severity="error")

                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # Track successful execution
                if metric_name:
                    agent_tasks.labels(agent_type=metric_name, status="success").inc()
                    agent_execution_time.labels(agent_type=metric_name).observe(duration)

                return result
            except Exception as e:
                duration = time.time() - start_time

                # Track failed execution
                if metric_name:
                    agent_tasks.labels(agent_type=metric_name, status="failed").inc()
                    agent_execution_time.labels(agent_type=metric_name).observe(duration)
                    track_error(error_type=type(e).__name__, severity="error")

                raise

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


async def get_metrics() -> bytes:
    """Generate Prometheus metrics in text format"""
    # Update system metrics before generating output
    update_system_metrics()

    # Generate metrics
    return generate_latest(metrics_registry)


# Metrics endpoint for FastAPI
async def metrics_endpoint(request: Request) -> Response:
    """FastAPI endpoint to expose Prometheus metrics"""
    metrics_data = await get_metrics()
    return Response(
        content=metrics_data,
        media_type=CONTENT_TYPE_LATEST,
        headers={"Content-Type": CONTENT_TYPE_LATEST}
    )
"""
API Metrics and Performance Monitoring Endpoints

Provides comprehensive performance monitoring, metrics collection,
and health checking for the ToolboxAI API.

Features:
- Real-time performance metrics
- Endpoint usage analytics
- System health monitoring
- Error rate tracking
- Response time analytics
- Resource utilization

Author: ToolBoxAI Team
Created: 2025-10-02
Version: 1.0.0
Standards: Python 3.12, FastAPI async, Pydantic v2
"""

import logging
from collections import defaultdict
from datetime import datetime
from enum import Enum
from typing import Annotated, Any

import psutil
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.api.auth.auth import get_current_user
from apps.backend.core.deps import get_async_db
from apps.backend.models.schemas import User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/metrics",
    tags=["api-metrics"],
    responses={404: {"description": "Metrics not found"}},
)


# === In-Memory Metrics Store (Replace with Redis/Database in production) ===


class MetricsStore:
    """In-memory metrics storage"""

    def __init__(self):
        self.request_counts = defaultdict(int)
        self.response_times = defaultdict(list)
        self.error_counts = defaultdict(int)
        self.endpoint_hits = defaultdict(int)
        self.status_codes = defaultdict(int)
        self.start_time = datetime.utcnow()

    def record_request(self, endpoint: str, method: str, duration: float, status_code: int):
        """Record a request metric"""
        key = f"{method}:{endpoint}"
        self.request_counts[key] += 1
        self.response_times[key].append(duration)
        self.endpoint_hits[endpoint] += 1
        self.status_codes[status_code] += 1

        if status_code >= 400:
            self.error_counts[key] += 1

    def get_metrics(self):
        """Get all metrics"""
        return {
            "request_counts": dict(self.request_counts),
            "response_times": {
                k: {
                    "count": len(v),
                    "avg": sum(v) / len(v) if v else 0,
                    "min": min(v) if v else 0,
                    "max": max(v) if v else 0,
                }
                for k, v in self.response_times.items()
            },
            "error_counts": dict(self.error_counts),
            "endpoint_hits": dict(self.endpoint_hits),
            "status_codes": dict(self.status_codes),
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
        }

    def reset(self):
        """Reset all metrics"""
        self.request_counts.clear()
        self.response_times.clear()
        self.error_counts.clear()
        self.endpoint_hits.clear()
        self.status_codes.clear()


# Global metrics store
_metrics_store = MetricsStore()


# === Enums ===


class HealthStatus(str, Enum):
    """Health status enumeration"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class MetricType(str, Enum):
    """Metric type enumeration"""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


# === Pydantic v2 Models ===


class SystemMetrics(BaseModel):
    """System resource metrics"""

    model_config = ConfigDict(from_attributes=True)

    cpu_percent: float = Field(..., ge=0, le=100)
    memory_percent: float = Field(..., ge=0, le=100)
    memory_used_mb: float
    memory_available_mb: float
    disk_percent: float = Field(..., ge=0, le=100)
    disk_used_gb: float
    disk_free_gb: float


class EndpointMetrics(BaseModel):
    """Endpoint performance metrics"""

    model_config = ConfigDict(from_attributes=True)

    endpoint: str
    method: str
    request_count: int
    error_count: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float


class APIHealthCheck(BaseModel):
    """API health check response"""

    model_config = ConfigDict(from_attributes=True)

    status: HealthStatus
    timestamp: datetime
    version: str = "1.0.0"
    uptime_seconds: float
    checks: dict[str, Any] = Field(default_factory=dict)


class PerformanceMetrics(BaseModel):
    """Overall performance metrics"""

    model_config = ConfigDict(from_attributes=True)

    total_requests: int
    total_errors: int
    error_rate: float
    avg_response_time: float
    requests_per_second: float
    uptime_seconds: float
    system_metrics: SystemMetrics
    top_endpoints: list[EndpointMetrics]


class MetricDataPoint(BaseModel):
    """Individual metric data point"""

    model_config = ConfigDict(from_attributes=True)

    timestamp: datetime
    value: float
    labels: dict[str, str] = Field(default_factory=dict)


class TimeSeriesMetrics(BaseModel):
    """Time series metrics data"""

    model_config = ConfigDict(from_attributes=True)

    metric_name: str
    metric_type: MetricType
    data_points: list[MetricDataPoint]
    start_time: datetime
    end_time: datetime


# === API Endpoints ===


@router.get(
    "/health",
    response_model=APIHealthCheck,
    summary="API health check",
    description="Get API health status and basic checks",
)
async def health_check(
    session: Annotated[AsyncSession, Depends(get_async_db)],
) -> APIHealthCheck:
    """
    Perform API health check.

    Returns health status and basic system checks.

    Args:
        session: Async database session

    Returns:
        APIHealthCheck: Health check results
    """
    try:
        checks = {}

        # Database check
        try:
            await session.execute("SELECT 1")
            checks["database"] = "healthy"
        except Exception as e:
            logger.error(f"Database check failed: {e}")
            checks["database"] = "unhealthy"

        # System resources check
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory().percent

            if cpu > 90 or memory > 90:
                checks["resources"] = "degraded"
            else:
                checks["resources"] = "healthy"
        except Exception as e:
            logger.error(f"Resource check failed: {e}")
            checks["resources"] = "unknown"

        # Determine overall status
        if "unhealthy" in checks.values():
            overall_status = HealthStatus.UNHEALTHY
        elif "degraded" in checks.values():
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        metrics = _metrics_store.get_metrics()

        return APIHealthCheck(
            status=overall_status,
            timestamp=datetime.utcnow(),
            uptime_seconds=metrics["uptime_seconds"],
            checks=checks,
        )

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return APIHealthCheck(
            status=HealthStatus.UNHEALTHY,
            timestamp=datetime.utcnow(),
            uptime_seconds=0,
            checks={"error": str(e)},
        )


@router.get(
    "/system",
    response_model=SystemMetrics,
    summary="Get system metrics",
    description="Get current system resource utilization",
)
async def get_system_metrics() -> SystemMetrics:
    """
    Get system resource metrics.

    Returns current CPU, memory, and disk usage.

    Returns:
        SystemMetrics: System resource metrics
    """
    try:
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)

        # Memory metrics
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_mb = memory.used / (1024 * 1024)
        memory_available_mb = memory.available / (1024 * 1024)

        # Disk metrics
        disk = psutil.disk_usage("/")
        disk_percent = disk.percent
        disk_used_gb = disk.used / (1024 * 1024 * 1024)
        disk_free_gb = disk.free / (1024 * 1024 * 1024)

        return SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_mb=memory_used_mb,
            memory_available_mb=memory_available_mb,
            disk_percent=disk_percent,
            disk_used_gb=disk_used_gb,
            disk_free_gb=disk_free_gb,
        )

    except Exception as e:
        logger.error(f"Failed to get system metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get system metrics"
        )


@router.get(
    "/performance",
    response_model=PerformanceMetrics,
    summary="Get performance metrics",
    description="Get overall API performance metrics",
)
async def get_performance_metrics(
    current_user: Annotated[User, Depends(get_current_user)],
) -> PerformanceMetrics:
    """
    Get API performance metrics.

    Requires authentication. Returns comprehensive performance data.

    Args:
        current_user: Current authenticated user

    Returns:
        PerformanceMetrics: Performance metrics
    """
    try:
        metrics = _metrics_store.get_metrics()

        # Calculate aggregates
        total_requests = sum(metrics["request_counts"].values())
        total_errors = sum(metrics["error_counts"].values())
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0

        # Calculate average response time
        all_response_times = []
        for times in metrics["response_times"].values():
            all_response_times.extend(times["avg"] for _ in range(times["count"]))

        avg_response_time = (
            sum(all_response_times) / len(all_response_times) if all_response_times else 0
        )

        # Calculate requests per second
        uptime = metrics["uptime_seconds"]
        requests_per_second = total_requests / uptime if uptime > 0 else 0

        # Get system metrics
        system_metrics = await get_system_metrics()

        # Get top endpoints
        top_endpoints = []
        for (method, endpoint), count in sorted(
            metrics["request_counts"].items(), key=lambda x: x[1], reverse=True
        )[:10]:
            key = f"{method}:{endpoint}"
            times = metrics["response_times"].get(key, {})
            error_count = metrics["error_counts"].get(key, 0)

            # Calculate percentiles (simplified)
            response_times_list = _metrics_store.response_times.get(key, [])
            if response_times_list:
                sorted_times = sorted(response_times_list)
                p95_idx = int(len(sorted_times) * 0.95)
                p99_idx = int(len(sorted_times) * 0.99)
                p95 = sorted_times[p95_idx] if p95_idx < len(sorted_times) else times.get("max", 0)
                p99 = sorted_times[p99_idx] if p99_idx < len(sorted_times) else times.get("max", 0)
            else:
                p95 = p99 = 0

            top_endpoints.append(
                EndpointMetrics(
                    endpoint=endpoint,
                    method=method,
                    request_count=count,
                    error_count=error_count,
                    avg_response_time=times.get("avg", 0),
                    min_response_time=times.get("min", 0),
                    max_response_time=times.get("max", 0),
                    p95_response_time=p95,
                    p99_response_time=p99,
                )
            )

        return PerformanceMetrics(
            total_requests=total_requests,
            total_errors=total_errors,
            error_rate=error_rate,
            avg_response_time=avg_response_time,
            requests_per_second=requests_per_second,
            uptime_seconds=uptime,
            system_metrics=system_metrics,
            top_endpoints=top_endpoints,
        )

    except Exception as e:
        logger.error(f"Failed to get performance metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get performance metrics",
        )


@router.get(
    "/endpoints",
    response_model=list[EndpointMetrics],
    summary="Get endpoint metrics",
    description="Get performance metrics for all endpoints",
)
async def get_endpoint_metrics(
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(50, ge=1, le=100),
) -> list[EndpointMetrics]:
    """
    Get endpoint-specific metrics.

    Args:
        current_user: Current authenticated user
        limit: Maximum number of endpoints to return

    Returns:
        list[EndpointMetrics]: List of endpoint metrics
    """
    try:
        metrics = _metrics_store.get_metrics()

        endpoint_metrics = []
        for (method, endpoint), count in metrics["request_counts"].items():
            key = f"{method}:{endpoint}"
            times = metrics["response_times"].get(key, {})
            error_count = metrics["error_counts"].get(key, 0)

            # Calculate percentiles
            response_times_list = _metrics_store.response_times.get(key, [])
            if response_times_list:
                sorted_times = sorted(response_times_list)
                p95_idx = int(len(sorted_times) * 0.95)
                p99_idx = int(len(sorted_times) * 0.99)
                p95 = sorted_times[p95_idx] if p95_idx < len(sorted_times) else times.get("max", 0)
                p99 = sorted_times[p99_idx] if p99_idx < len(sorted_times) else times.get("max", 0)
            else:
                p95 = p99 = 0

            endpoint_metrics.append(
                EndpointMetrics(
                    endpoint=endpoint,
                    method=method,
                    request_count=count,
                    error_count=error_count,
                    avg_response_time=times.get("avg", 0),
                    min_response_time=times.get("min", 0),
                    max_response_time=times.get("max", 0),
                    p95_response_time=p95,
                    p99_response_time=p99,
                )
            )

        # Sort by request count
        endpoint_metrics.sort(key=lambda x: x.request_count, reverse=True)

        return endpoint_metrics[:limit]

    except Exception as e:
        logger.error(f"Failed to get endpoint metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get endpoint metrics",
        )


@router.post(
    "/reset",
    summary="Reset metrics",
    description="Reset all collected metrics (admin only)",
)
async def reset_metrics(
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """
    Reset all metrics.

    Requires admin permissions.

    Args:
        current_user: Current authenticated user

    Returns:
        dict: Reset confirmation
    """
    try:
        # Check if user is admin
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Admin permissions required"
            )

        _metrics_store.reset()
        _metrics_store.start_time = datetime.utcnow()

        logger.info(f"Metrics reset by user {current_user.id}")

        return {"message": "Metrics reset successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to reset metrics"
        )


# === Middleware Integration Helper ===


def record_request_metric(endpoint: str, method: str, duration: float, status_code: int):
    """
    Helper function to record request metrics from middleware.

    Args:
        endpoint: Request endpoint path
        method: HTTP method
        duration: Request duration in seconds
        status_code: HTTP status code
    """
    _metrics_store.record_request(endpoint, method, duration, status_code)

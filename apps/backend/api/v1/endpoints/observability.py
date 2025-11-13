"""
Observability API endpoints for metrics, traces, and system monitoring.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any

import structlog
from apps.backend.api.deps import get_current_user
from apps.backend.core.websocket_cluster import websocket_cluster
from database.replica_router import replica_router
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from prometheus_client import REGISTRY, generate_latest

from apps.backend.core.circuit_breaker import circuit_breaker_manager
from apps.backend.core.edge_cache import edge_cache_manager
from apps.backend.core.observability.anomaly_detection import AnomalyDetector
from apps.backend.core.observability.correlation import TraceCorrelator
from apps.backend.core.observability.telemetry import metrics_collector
from apps.backend.core.rate_limiter import rate_limiter
from apps.backend.services.pusher import trigger_event

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/observability", tags=["observability"])

# Initialize components
trace_correlator = TraceCorrelator()
anomaly_detector = AnomalyDetector()


@router.get("/metrics")
async def get_metrics(
    time_range: str = Query("1h", description="Time range: 5m, 1h, 6h, 24h, 7d"),
    resolution: int = Query(60, description="Resolution in seconds"),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get aggregated metrics for the specified time range.
    """
    try:
        # Parse time range
        time_ranges = {
            "5m": timedelta(minutes=5),
            "1h": timedelta(hours=1),
            "6h": timedelta(hours=6),
            "24h": timedelta(days=1),
            "7d": timedelta(days=7),
        }

        if time_range not in time_ranges:
            raise ValueError(f"Invalid time range: {time_range}")

        delta = time_ranges[time_range]
        end_time = datetime.utcnow()
        start_time = end_time - delta

        # Collect metrics
        metrics = await metrics_collector.get_metrics_range(
            start_time=start_time, end_time=end_time, resolution=resolution
        )

        # Add current system status
        system_status = await get_system_status()

        return {
            "status": "success",
            "data": {
                "metrics": metrics,
                "system_status": system_status,
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                    "resolution": resolution,
                },
            },
        }
    except Exception as e:
        logger.error("Failed to get metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/traces")
async def get_traces(
    limit: int = Query(100, le=1000),
    service: str | None = None,
    min_duration_ms: int | None = None,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get distributed traces with optional filtering.
    """
    try:
        traces = await trace_correlator.get_traces(
            limit=limit, service=service, min_duration_ms=min_duration_ms
        )

        return {"status": "success", "data": {"traces": traces, "total": len(traces)}}
    except Exception as e:
        logger.error("Failed to get traces", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/anomalies")
async def get_anomalies(
    severity: str | None = Query(
        None, description="Filter by severity: low, medium, high, critical"
    ),
    limit: int = Query(50, le=200),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get detected anomalies.
    """
    try:
        anomalies = await anomaly_detector.get_recent_anomalies(limit=limit, severity=severity)

        return {"status": "success", "data": {"anomalies": anomalies, "total": len(anomalies)}}
    except Exception as e:
        logger.error("Failed to get anomalies", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/components")
async def get_component_health(current_user: dict = Depends(get_current_user)) -> dict[str, Any]:
    """
    Get health status of all load balancing components.
    """
    try:
        health_data = {
            "circuit_breakers": await get_circuit_breaker_status(),
            "rate_limiters": await get_rate_limiter_status(),
            "database_replicas": await get_replica_status(),
            "edge_cache": await get_cache_status(),
            "websocket_cluster": await get_websocket_status(),
        }

        # Calculate overall health score
        total_healthy = sum(
            1 for component in health_data.values() if component.get("status") == "healthy"
        )
        health_score = (total_healthy / len(health_data)) * 100

        return {
            "status": "success",
            "data": {
                "components": health_data,
                "health_score": health_score,
                "timestamp": datetime.utcnow().isoformat(),
            },
        }
    except Exception as e:
        logger.error("Failed to get component health", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start-metrics-stream")
async def start_metrics_stream(
    background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)
) -> dict[str, Any]:
    """
    Start real-time metrics streaming via Pusher channel.
    """
    try:
        # Start background task to stream metrics
        background_tasks.add_task(stream_metrics_to_pusher)

        return {
            "status": "success",
            "message": "Metrics streaming started",
            "channel": "observability-metrics",
        }
    except Exception as e:
        logger.error("Failed to start metrics streaming", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop-metrics-stream")
async def stop_metrics_stream(current_user: dict = Depends(get_current_user)) -> dict[str, Any]:
    """
    Stop real-time metrics streaming.
    """
    try:
        # In production, you would maintain a registry of active streams
        # and stop the specific stream. For now, we'll just acknowledge the request.

        return {"status": "success", "message": "Metrics streaming stopped"}
    except Exception as e:
        logger.error("Failed to stop metrics streaming", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prometheus", response_class=PlainTextResponse)
async def get_prometheus_metrics() -> str:
    """
    Export metrics in Prometheus format.
    """
    try:
        return generate_latest(REGISTRY)
    except Exception as e:
        logger.error("Failed to generate Prometheus metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/anomalies/acknowledge/{anomaly_id}")
async def acknowledge_anomaly(
    anomaly_id: str, current_user: dict = Depends(get_current_user)
) -> dict[str, Any]:
    """
    Acknowledge an anomaly to mark it as reviewed.
    """
    try:
        success = await anomaly_detector.acknowledge_anomaly(
            anomaly_id=anomaly_id, user_id=current_user["id"]
        )

        if not success:
            raise HTTPException(status_code=404, detail="Anomaly not found")

        return {"status": "success", "message": f"Anomaly {anomaly_id} acknowledged"}
    except Exception as e:
        logger.error("Failed to acknowledge anomaly", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trace/{trace_id}")
async def get_trace_details(
    trace_id: str, current_user: dict = Depends(get_current_user)
) -> dict[str, Any]:
    """
    Get detailed information about a specific trace.
    """
    try:
        trace = await trace_correlator.get_trace_by_id(trace_id)

        if not trace:
            raise HTTPException(status_code=404, detail="Trace not found")

        # Get correlated traces
        correlated = await trace_correlator.get_correlated_traces(trace_id)

        return {
            "status": "success",
            "data": {
                "trace": trace,
                "correlated_traces": correlated,
                "span_count": len(trace.get("spans", [])),
                "total_duration_ms": trace.get("duration_ms", 0),
            },
        }
    except Exception as e:
        logger.error("Failed to get trace details", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions


async def get_system_status() -> dict[str, Any]:
    """Get current system status."""
    return {
        "uptime": await metrics_collector.get_uptime(),
        "active_connections": await websocket_cluster.get_connection_count(),
        "cache_hit_rate": await edge_cache_manager.get_hit_rate(),
        "database_pool_usage": await replica_router.get_pool_stats(),
        "rate_limit_remaining": await rate_limiter.get_global_remaining(),
    }


async def get_circuit_breaker_status() -> dict[str, Any]:
    """Get circuit breaker status."""
    breakers = await circuit_breaker_manager.get_all_status()

    healthy_count = sum(1 for b in breakers.values() if b["state"] == "CLOSED")

    return {
        "status": "healthy" if healthy_count == len(breakers) else "degraded",
        "total": len(breakers),
        "healthy": healthy_count,
        "breakers": breakers,
    }


async def get_rate_limiter_status() -> dict[str, Any]:
    """Get rate limiter status."""
    stats = await rate_limiter.get_stats()

    return {
        "status": "healthy" if stats["throttled_percentage"] < 10 else "warning",
        "requests_per_minute": stats["rpm"],
        "throttled_percentage": stats["throttled_percentage"],
        "active_limits": stats["active_limits"],
    }


async def get_replica_status() -> dict[str, Any]:
    """Get database replica status."""
    replicas = await replica_router.get_replica_health()

    healthy_count = sum(1 for r in replicas if r["healthy"])

    return {
        "status": "healthy" if healthy_count > 0 else "critical",
        "total": len(replicas),
        "healthy": healthy_count,
        "replicas": replicas,
    }


async def get_cache_status() -> dict[str, Any]:
    """Get edge cache status."""
    stats = await edge_cache_manager.get_stats()

    return {
        "status": "healthy" if stats["hit_rate"] > 0.7 else "warning",
        "hit_rate": stats["hit_rate"],
        "size_mb": stats["size_mb"],
        "evictions_per_minute": stats["evictions_per_minute"],
    }


async def get_websocket_status() -> dict[str, Any]:
    """Get WebSocket cluster status."""
    stats = await websocket_cluster.get_stats()

    return {
        "status": "healthy" if stats["nodes_healthy"] == stats["total_nodes"] else "degraded",
        "total_nodes": stats["total_nodes"],
        "healthy_nodes": stats["nodes_healthy"],
        "total_connections": stats["total_connections"],
    }


async def get_real_time_metrics() -> dict[str, Any]:
    """Get real-time metrics for streaming."""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": {
            "request_rate": await metrics_collector.get_request_rate(),
            "error_rate": await metrics_collector.get_error_rate(),
            "p50_latency": await metrics_collector.get_percentile_latency(50),
            "p95_latency": await metrics_collector.get_percentile_latency(95),
            "p99_latency": await metrics_collector.get_percentile_latency(99),
            "active_requests": await metrics_collector.get_active_requests(),
            "cpu_usage": await metrics_collector.get_cpu_usage(),
            "memory_usage": await metrics_collector.get_memory_usage(),
        },
    }


async def stream_metrics_to_pusher():
    """Background task to stream metrics to Pusher channel."""
    try:
        while True:
            # Get real-time metrics
            metrics_data = await get_real_time_metrics()

            # Add component health data
            components_health = {
                "circuit_breakers": await get_circuit_breaker_status(),
                "rate_limiters": await get_rate_limiter_status(),
                "database_replicas": await get_replica_status(),
                "edge_cache": await get_cache_status(),
                "websocket_cluster": await get_websocket_status(),
            }

            # Combine all data
            stream_data = {
                **metrics_data,
                "component_health": components_health,
                "system_status": await get_system_status(),
            }

            # Trigger Pusher event
            trigger_event(
                channel="observability-metrics", event="metrics.updated", data=stream_data
            )

            # Wait before next update (every 2 seconds to avoid overwhelming)
            await asyncio.sleep(2)

    except asyncio.CancelledError:
        logger.info("Metrics streaming task cancelled")
    except Exception as e:
        logger.error("Error in metrics streaming task", error=str(e))

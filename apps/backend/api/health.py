"""
Health check endpoints for monitoring and deployment verification.
Updated 2025-09-21 to include comprehensive health monitoring for all system components.
"""

import os
from datetime import datetime
from typing import Any

import psutil
import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_async_session

# Import new health check routers
try:
    from apps.backend.api.health.agent_health import router as agent_health_router

    AGENT_HEALTH_AVAILABLE = True
except ImportError:
    AGENT_HEALTH_AVAILABLE = False

try:
    from apps.backend.api.health.mcp_health import router as mcp_health_router

    MCP_HEALTH_AVAILABLE = True
except ImportError:
    MCP_HEALTH_AVAILABLE = False

try:
    from apps.backend.api.health.queue_health import router as queue_health_router

    QUEUE_HEALTH_AVAILABLE = True
except ImportError:
    QUEUE_HEALTH_AVAILABLE = False

try:
    from apps.backend.api.health.supabase_health import router as supabase_health_router

    SUPABASE_HEALTH_AVAILABLE = True
except ImportError:
    SUPABASE_HEALTH_AVAILABLE = False

router = APIRouter(tags=["Health"])

# Include specialized health routers
if AGENT_HEALTH_AVAILABLE:
    router.include_router(agent_health_router)

if MCP_HEALTH_AVAILABLE:
    router.include_router(mcp_health_router)

if QUEUE_HEALTH_AVAILABLE:
    router.include_router(queue_health_router)

if SUPABASE_HEALTH_AVAILABLE:
    router.include_router(supabase_health_router)


async def check_database_connection(session: AsyncSession) -> dict[str, Any]:
    """Check database connectivity and basic stats."""
    try:
        # Test database connection
        await session.execute(text("SELECT 1"))
        await session.execute(text("SELECT version()"))
        version_result = await session.execute(text("SELECT version()"))
        db_version = version_result.scalar()

        # Get table count
        table_count_result = await session.execute(
            text(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """
            )
        )
        table_count = table_count_result.scalar()

        return {
            "status": "healthy",
            "version": db_version.split()[0] if db_version else "unknown",
            "tables": table_count or 0,
            "connection": "active",
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e), "connection": "failed"}


async def check_redis_connection() -> dict[str, Any]:
    """Check Redis connectivity."""
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_client = redis.from_url(redis_url, decode_responses=True)

        # Test connection
        await redis_client.ping()

        # Get basic info
        info = await redis_client.info()

        await redis_client.close()

        return {
            "status": "healthy",
            "version": info.get("redis_version", "unknown"),
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", "unknown"),
            "connection": "active",
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e), "connection": "failed"}


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """
    Basic health check endpoint.
    Returns 200 if service is running.
    """
    return {
        "status": "healthy",
        "service": "toolboxai-backend",
        "timestamp": datetime.utcnow().isoformat(),
        "version": os.getenv("GIT_COMMIT", "unknown"),
        "environment": os.getenv("ENVIRONMENT", "development"),
    }


@router.get("/ready")
async def readiness_check(
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Readiness check endpoint.
    Verifies that all dependencies are accessible.
    """
    checks = {
        "service": "ready",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {},
    }

    # Check database
    db_status = await check_database_connection(session)
    checks["checks"]["database"] = db_status

    # Check Redis
    redis_status = await check_redis_connection()
    checks["checks"]["redis"] = redis_status

    # Check if any service is unhealthy
    all_healthy = all(check.get("status") == "healthy" for check in checks["checks"].values())

    if not all_healthy:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=checks)

    return checks


@router.get("/live")
async def liveness_check() -> dict[str, Any]:
    """
    Liveness check endpoint.
    Verifies that the service is still alive and responsive.
    """
    # Check system resources
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    # Define thresholds
    CPU_THRESHOLD = 90.0
    MEMORY_THRESHOLD = 90.0
    DISK_THRESHOLD = 90.0

    health_status = {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "resources": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "disk_percent": disk.percent,
            "memory_available_mb": memory.available / (1024 * 1024),
            "disk_free_gb": disk.free / (1024 * 1024 * 1024),
        },
        "thresholds": {
            "cpu": CPU_THRESHOLD,
            "memory": MEMORY_THRESHOLD,
            "disk": DISK_THRESHOLD,
        },
    }

    # Check if resources are within acceptable limits
    if (
        cpu_percent > CPU_THRESHOLD
        or memory.percent > MEMORY_THRESHOLD
        or disk.percent > DISK_THRESHOLD
    ):
        health_status["status"] = "degraded"
        health_status["warnings"] = []

        if cpu_percent > CPU_THRESHOLD:
            health_status["warnings"].append(f"High CPU usage: {cpu_percent}%")
        if memory.percent > MEMORY_THRESHOLD:
            health_status["warnings"].append(f"High memory usage: {memory.percent}%")
        if disk.percent > DISK_THRESHOLD:
            health_status["warnings"].append(f"High disk usage: {disk.percent}%")

        # Don't fail the health check, just warn
        # Render can use this information for alerting

    return health_status


@router.get("/metrics")
async def metrics_endpoint(
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Metrics endpoint for monitoring.
    Returns detailed metrics about the service.
    """
    # Get database metrics
    db_metrics = {}
    try:
        # Count users
        user_count = await session.execute(text("SELECT COUNT(*) FROM dashboard_users"))
        db_metrics["user_count"] = user_count.scalar() or 0

        # Count sessions
        session_count = await session.execute(
            text("SELECT COUNT(*) FROM user_sessions WHERE expires_at > NOW()")
        )
        db_metrics["active_sessions"] = session_count.scalar() or 0

        # Count content
        content_count = await session.execute(text("SELECT COUNT(*) FROM educational_content"))
        db_metrics["content_count"] = content_count.scalar() or 0
    except Exception as e:
        db_metrics["error"] = str(e)

    # Get system metrics
    process = psutil.Process()
    network = psutil.net_io_counters()

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "service": {
            "name": "toolboxai-backend",
            "version": os.getenv("GIT_COMMIT", "unknown"),
            "environment": os.getenv("ENVIRONMENT", "development"),
            "uptime_seconds": (
                datetime.utcnow() - datetime.fromtimestamp(process.create_time())
            ).total_seconds(),
        },
        "system": {
            "cpu": {
                "percent": psutil.cpu_percent(interval=1),
                "count": psutil.cpu_count(),
            },
            "memory": {
                "percent": psutil.virtual_memory().percent,
                "available_mb": psutil.virtual_memory().available / (1024 * 1024),
                "total_mb": psutil.virtual_memory().total / (1024 * 1024),
            },
            "disk": {
                "percent": psutil.disk_usage("/").percent,
                "free_gb": psutil.disk_usage("/").free / (1024 * 1024 * 1024),
                "total_gb": psutil.disk_usage("/").total / (1024 * 1024 * 1024),
            },
            "network": {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv,
            },
        },
        "application": {
            "database": db_metrics,
            "process": {
                "memory_mb": process.memory_info().rss / (1024 * 1024),
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads(),
                "num_connections": len(process.connections()),
            },
        },
    }

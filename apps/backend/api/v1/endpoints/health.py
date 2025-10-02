"""
Health Check Endpoints for ToolboxAI Backend

Provides comprehensive health monitoring for Docker container health checks
and service monitoring systems like Prometheus, Kubernetes, etc.

Created: October 1, 2025
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, Any
from datetime import datetime, timezone
import asyncio
import logging

# Import dependencies for health checks
from database.connection import get_session_context
from sqlalchemy import text
from redis import asyncio as aioredis
from toolboxai_settings.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["health"])


async def check_database() -> Dict[str, Any]:
    """
    Check PostgreSQL database connectivity and responsiveness

    Returns:
        Dict with status, latency, and details
    """
    try:
        start_time = datetime.now(timezone.utc)

        async with get_session_context() as session:
            # Execute simple query to verify connection
            result = await session.execute(text("SELECT 1"))
            row = result.scalar()

            if row != 1:
                return {
                    "status": "unhealthy",
                    "message": "Database query returned unexpected result",
                    "latency_ms": None
                }

        end_time = datetime.now(timezone.utc)
        latency_ms = (end_time - start_time).total_seconds() * 1000

        return {
            "status": "healthy",
            "message": "Database connection successful",
            "latency_ms": round(latency_ms, 2)
        }
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
            "latency_ms": None
        }


async def check_redis() -> Dict[str, Any]:
    """
    Check Redis connectivity and responsiveness

    Returns:
        Dict with status, latency, and details
    """
    try:
        start_time = datetime.now(timezone.utc)

        # Create Redis client
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )

        # Ping Redis
        pong = await redis_client.ping()

        # Close connection
        await redis_client.close()

        end_time = datetime.now(timezone.utc)
        latency_ms = (end_time - start_time).total_seconds() * 1000

        if not pong:
            return {
                "status": "unhealthy",
                "message": "Redis ping failed",
                "latency_ms": None
            }

        return {
            "status": "healthy",
            "message": "Redis connection successful",
            "latency_ms": round(latency_ms, 2)
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "message": f"Redis connection failed: {str(e)}",
            "latency_ms": None
        }


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Comprehensive health check endpoint for Docker and monitoring systems

    Returns:
        200 OK if all services are healthy
        503 Service Unavailable if any critical service is unhealthy

    Response includes:
        - Overall status
        - Individual service statuses
        - Timestamp
        - Version information
    """
    try:
        # Run health checks concurrently
        db_check, redis_check = await asyncio.gather(
            check_database(),
            check_redis(),
            return_exceptions=True
        )

        # Handle exceptions from gather
        if isinstance(db_check, Exception):
            db_check = {
                "status": "unhealthy",
                "message": str(db_check),
                "latency_ms": None
            }

        if isinstance(redis_check, Exception):
            redis_check = {
                "status": "unhealthy",
                "message": str(redis_check),
                "latency_ms": None
            }

        # Determine overall status
        all_healthy = (
            db_check["status"] == "healthy" and
            redis_check["status"] == "healthy"
        )

        response = {
            "status": "healthy" if all_healthy else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": getattr(settings, "VERSION", "unknown"),
            "environment": settings.ENVIRONMENT,
            "services": {
                "database": db_check,
                "redis": redis_check,
                "api": {
                    "status": "healthy",
                    "message": "API server is running"
                }
            }
        }

        # Return 503 if any critical service is unhealthy
        if not all_healthy:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=response
            )

        return response

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": f"Health check failed: {str(e)}",
                "services": {}
            }
        )


@router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_probe():
    """
    Kubernetes liveness probe - checks if the application is alive

    This is a lightweight check that only verifies the application is running.
    It does not check dependencies like database or Redis.

    Returns:
        200 OK if application is alive
    """
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_probe():
    """
    Kubernetes readiness probe - checks if the application is ready to serve traffic

    This checks critical dependencies to ensure the application can handle requests.

    Returns:
        200 OK if application is ready
        503 Service Unavailable if not ready
    """
    try:
        # Check critical dependencies
        db_check, redis_check = await asyncio.gather(
            check_database(),
            check_redis(),
            return_exceptions=True
        )

        # Handle exceptions
        if isinstance(db_check, Exception):
            db_check = {"status": "unhealthy"}
        if isinstance(redis_check, Exception):
            redis_check = {"status": "unhealthy"}

        # Application is ready only if all critical services are healthy
        is_ready = (
            db_check["status"] == "healthy" and
            redis_check["status"] == "healthy"
        )

        if not is_ready:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "not_ready",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "services": {
                        "database": db_check["status"],
                        "redis": redis_check["status"]
                    }
                }
            )

        return {
            "status": "ready",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {
                "database": "healthy",
                "redis": "healthy"
            }
        }

    except Exception as e:
        logger.error(f"Readiness probe failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": str(e)
            }
        )


@router.get("/health/startup", status_code=status.HTTP_200_OK)
async def startup_probe():
    """
    Kubernetes startup probe - checks if the application has started successfully

    This is similar to readiness but used during initial startup.

    Returns:
        200 OK if application has started
        503 Service Unavailable if still starting
    """
    try:
        # Check if critical services are available
        db_check = await check_database()

        if db_check["status"] != "healthy":
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "starting",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "message": "Database not yet available"
                }
            )

        return {
            "status": "started",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        logger.error(f"Startup probe failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "starting",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": str(e)
            }
        )


@router.get("/ping", status_code=status.HTTP_200_OK)
async def ping():
    """
    Simple ping endpoint for basic connectivity testing

    Returns:
        Always returns 200 OK with "pong" message
    """
    return {"message": "pong"}

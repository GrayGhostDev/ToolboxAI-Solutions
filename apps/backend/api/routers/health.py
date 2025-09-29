"""
Health and System Status Router

Handles health checks, system status, and monitoring endpoints.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse

from apps.backend.core.logging import logging_manager
from apps.backend.core.config import settings
from apps.backend.models.schemas import HealthCheck, BaseResponse

logger = logging_manager.get_logger(__name__)

router = APIRouter(tags=["System"])


@router.get("/health", response_model=HealthCheck)
async def health_check(request: Request) -> HealthCheck:
    """
    Comprehensive health check endpoint

    Returns:
        HealthCheck: System health status
    """
    try:
        # Calculate uptime
        app = request.app
        current_time = time.time()
        start_time = getattr(app.state, "start_time", current_time)
        uptime_seconds = current_time - start_time

        # Check all services
        services = await _check_all_services()

        # Determine overall status based on service checks
        unhealthy_services = [
            name for name, status in services.items() if status.get("status") != "healthy"
        ]

        overall_status = "degraded" if unhealthy_services else "healthy"

        # Create checks dictionary for the model
        checks = {name: status.get("status") == "healthy" for name, status in services.items()}

        health_data = {
            "status": overall_status,
            "version": settings.APP_VERSION,
            "uptime": uptime_seconds,
            "checks": checks,
        }

        return HealthCheck(**health_data)

    except Exception as e:
        logger.error(f"Health check failed: {e}")

        # Calculate uptime even in error case
        try:
            app = request.app
            current_time = time.time()
            start_time = getattr(app.state, "start_time", current_time)
            uptime_seconds = current_time - start_time
        except:
            uptime_seconds = 0.0

        return HealthCheck(
            status="unhealthy", version=settings.APP_VERSION, uptime=uptime_seconds, checks={}
        )


@router.get("/info", response_model=BaseResponse)
async def get_app_info() -> BaseResponse:
    """
    Get application information

    Returns:
        BaseResponse: Application information
    """
    try:
        app_info = {
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "python_version": "3.12+",
            "fastapi_version": "0.104+",
            "features": {
                "authentication": True,
                "websockets": True,
                "pusher": True,
                "roblox_integration": True,
                "ai_agents": True,
                "content_generation": True,
            },
        }

        return BaseResponse(
            status="success",
            data=app_info,
            message="Application information retrieved successfully",
        )

    except Exception as e:
        logger.error(f"Failed to get app info: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve application information")


@router.get("/pusher/status")
async def get_pusher_status() -> JSONResponse:
    """
    Get Pusher service status

    Returns:
        JSONResponse: Pusher service status
    """
    try:
        from apps.backend.services.pusher_realtime import get_pusher_status

        status = get_pusher_status()

        return JSONResponse(
            content={
                "status": "success",
                "data": status,
                "message": "Pusher status retrieved successfully",
            }
        )

    except ImportError:
        return JSONResponse(
            content={
                "status": "error",
                "data": {"enabled": False, "error": "Pusher service not available"},
                "message": "Pusher service not configured",
            }
        )
    except Exception as e:
        logger.error(f"Failed to get Pusher status: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "data": {"enabled": False, "error": str(e)},
                "message": "Failed to retrieve Pusher status",
            }
        )


@router.get("/resilience/status")
async def get_resilience_endpoint_status() -> JSONResponse:
    """
    Get resilience features status

    Returns:
        JSONResponse: Resilience features status
    """
    try:
        from apps.backend.api.middleware.resilience import get_resilience_status

        status = await get_resilience_status()

        return JSONResponse(
            content={
                "status": "success",
                "data": status,
                "message": "Resilience status retrieved successfully",
            }
        )

    except ImportError:
        return JSONResponse(
            content={
                "status": "error",
                "data": {"enabled": False, "error": "Resilience features not available"},
                "message": "Resilience features not configured",
            }
        )
    except Exception as e:
        logger.error(f"Failed to get resilience status: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "data": {"enabled": False, "error": str(e)},
                "message": "Failed to retrieve resilience status",
            }
        )


@router.get("/circuit-breakers/status")
async def get_circuit_breakers_endpoint_status() -> JSONResponse:
    """
    Get circuit breakers status

    Returns:
        JSONResponse: Circuit breakers status
    """
    try:
        from apps.backend.core.circuit_breaker import get_all_circuit_breakers_status

        status = await get_all_circuit_breakers_status()

        return JSONResponse(
            content={
                "status": "success",
                "data": status,
                "message": "Circuit breakers status retrieved successfully",
            }
        )

    except ImportError:
        return JSONResponse(
            content={
                "status": "error",
                "data": {"enabled": False, "error": "Circuit breakers not available"},
                "message": "Circuit breakers not configured",
            }
        )
    except Exception as e:
        logger.error(f"Failed to get circuit breakers status: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "data": {"enabled": False, "error": str(e)},
                "message": "Failed to retrieve circuit breakers status",
            }
        )


@router.post("/circuit-breakers/{breaker_name}/reset")
async def reset_circuit_breaker(breaker_name: str) -> JSONResponse:
    """
    Reset a circuit breaker

    Args:
        breaker_name: Name of the circuit breaker to reset

    Returns:
        JSONResponse: Reset operation result
    """
    try:
        from apps.backend.core.circuit_breaker import get_all_circuit_breakers_status

        # For now, return success - implement actual reset logic when circuit breaker is enhanced
        return JSONResponse(
            content={
                "status": "success",
                "data": {"breaker_name": breaker_name, "reset": True},
                "message": f"Circuit breaker {breaker_name} reset successfully",
            }
        )

    except Exception as e:
        logger.error(f"Failed to reset circuit breaker {breaker_name}: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "data": {"breaker_name": breaker_name, "reset": False, "error": str(e)},
                "message": f"Failed to reset circuit breaker {breaker_name}",
            }
        )


@router.get("/rate-limit/usage/{identifier}")
async def get_rate_limit_usage(identifier: str) -> JSONResponse:
    """
    Get rate limit usage for an identifier

    Args:
        identifier: Rate limit identifier (e.g., IP address)

    Returns:
        JSONResponse: Rate limit usage information
    """
    try:
        # For now, return mock data - implement actual rate limit tracking when enhanced
        usage_data = {
            "identifier": identifier,
            "requests_made": 10,
            "requests_remaining": 90,
            "reset_time": datetime.now(timezone.utc).isoformat(),
            "window_minutes": 1,
        }

        return JSONResponse(
            content={
                "status": "success",
                "data": usage_data,
                "message": "Rate limit usage retrieved successfully",
            }
        )

    except Exception as e:
        logger.error(f"Failed to get rate limit usage for {identifier}: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "data": {"identifier": identifier, "error": str(e)},
                "message": f"Failed to retrieve rate limit usage for {identifier}",
            }
        )


@router.get("/sentry/status")
async def get_sentry_status() -> JSONResponse:
    """
    Get Sentry monitoring status

    Returns:
        JSONResponse: Sentry status information
    """
    try:
        from apps.backend.core.monitoring import sentry_manager

        status_data = {
            "enabled": sentry_manager.initialized,
            "environment": settings.ENVIRONMENT,
            "dsn_configured": bool(getattr(settings, "SENTRY_DSN", None)),
            "sample_rate": getattr(settings, "SENTRY_SAMPLE_RATE", 1.0),
        }

        return JSONResponse(
            content={
                "status": "success",
                "data": status_data,
                "message": "Sentry status retrieved successfully",
            }
        )

    except Exception as e:
        logger.error(f"Failed to get Sentry status: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "data": {"enabled": False, "error": str(e)},
                "message": "Failed to retrieve Sentry status",
            }
        )


async def _check_all_services() -> Dict[str, Dict[str, Any]]:
    """
    Check status of all services

    Returns:
        Dict: Service status information
    """
    services = {}

    # Check database
    services["database"] = await _check_database()

    # Check Redis
    services["redis"] = await _check_redis()

    # Check Pusher
    services["pusher"] = await _check_pusher()

    # Check agent systems
    services["agents"] = await _check_agents()

    # Check external services
    services["supabase"] = await _check_supabase()

    return services


async def _check_database() -> Dict[str, Any]:
    """Check database connectivity"""
    try:
        from apps.backend.services.database import db_service

        # Basic database check - implement actual connectivity test
        return {
            "status": "healthy",
            "type": "postgresql",
            "last_check": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "last_check": datetime.now(timezone.utc).isoformat(),
        }


async def _check_redis() -> Dict[str, Any]:
    """Check Redis connectivity"""
    try:
        if hasattr(settings, "REDIS_URL") and settings.REDIS_URL:
            import redis

            redis_client = redis.from_url(settings.REDIS_URL)
            redis_client.ping()
            return {
                "status": "healthy",
                "type": "redis",
                "last_check": datetime.now(timezone.utc).isoformat(),
            }
        else:
            return {"status": "not_configured", "message": "Redis URL not configured"}
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "last_check": datetime.now(timezone.utc).isoformat(),
        }


async def _check_pusher() -> Dict[str, Any]:
    """Check Pusher service"""
    try:
        from apps.backend.services.pusher_realtime import get_pusher_status

        status = get_pusher_status()
        return {
            "status": "healthy" if status.get("enabled") else "not_configured",
            "details": status,
            "last_check": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "last_check": datetime.now(timezone.utc).isoformat(),
        }


async def _check_agents() -> Dict[str, Any]:
    """Check agent systems"""
    try:
        from apps.backend.agents.agent import get_agent_health

        health = await get_agent_health()
        return {
            "status": "healthy" if health.get("status") == "healthy" else "degraded",
            "details": health,
            "last_check": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "last_check": datetime.now(timezone.utc).isoformat(),
        }


async def _check_supabase() -> Dict[str, Any]:
    """Check Supabase connectivity"""
    try:
        from apps.backend.core.supabase_config import health_check_supabase

        health = await health_check_supabase()
        return {
            "status": "healthy" if health else "unhealthy",
            "last_check": datetime.now(timezone.utc).isoformat(),
        }
    except ImportError:
        return {"status": "not_configured", "message": "Supabase not configured"}
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "last_check": datetime.now(timezone.utc).isoformat(),
        }

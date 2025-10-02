"""
Rojo Health Check Endpoint

Provides health monitoring for the Rojo (Roblox sync) service.
Docker health checks expect this endpoint at /api/rojo/health

Created: October 1, 2025
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
from datetime import datetime, timezone
import logging
import aiohttp

from toolboxai_settings.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rojo", tags=["rojo"])


async def check_rojo_connection() -> Dict[str, Any]:
    """
    Check if Rojo server is accessible

    Returns:
        Dict with connection status and details
    """
    rojo_port = getattr(settings, "ROJO_PORT", 34872)
    rojo_host = getattr(settings, "ROJO_HOST", "localhost")
    base_url = f"http://{rojo_host}:{rojo_port}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/api/rojo", timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "healthy",
                        "message": "Rojo server is accessible",
                        "details": {
                            "server_info": data,
                            "port": rojo_port,
                            "host": rojo_host
                        }
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "message": f"Rojo server returned status {response.status}",
                        "details": {
                            "port": rojo_port,
                            "host": rojo_host,
                            "status_code": response.status
                        }
                    }
    except aiohttp.ClientError as e:
        return {
            "status": "unhealthy",
            "message": f"Cannot connect to Rojo server: {str(e)}",
            "details": {
                "port": rojo_port,
                "host": rojo_host,
                "error": str(e)
            }
        }
    except Exception as e:
        logger.error(f"Rojo health check error: {e}")
        return {
            "status": "unhealthy",
            "message": f"Rojo health check failed: {str(e)}",
            "details": {
                "error": str(e)
            }
        }


@router.get("/health")
async def rojo_health_check():
    """
    Health check endpoint for Rojo (Roblox sync) service

    Docker health checks use this endpoint to verify Rojo is operational.

    Returns:
        200 OK if Rojo is healthy
        503 Service Unavailable if Rojo is unhealthy
    """
    try:
        health_status = await check_rojo_connection()

        response_data = {
            "status": health_status["status"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "rojo",
            "version": "1.0.0",
            "message": health_status["message"],
            "details": health_status.get("details", {})
        }

        # Return 503 if unhealthy
        if health_status["status"] != "healthy":
            return JSONResponse(
                status_code=503,
                content=response_data
            )

        return response_data

    except Exception as e:
        logger.error(f"Rojo health endpoint error: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "service": "rojo",
                "message": f"Health check failed: {str(e)}"
            }
        )


@router.get("/status")
async def rojo_status():
    """
    Detailed status endpoint for Rojo service

    Provides comprehensive information about Rojo server status.
    """
    try:
        health_status = await check_rojo_connection()

        return {
            "status": health_status["status"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "rojo",
            "version": "1.0.0",
            "health": health_status,
            "configuration": {
                "port": getattr(settings, "ROJO_PORT", 34872),
                "host": getattr(settings, "ROJO_HOST", "localhost"),
                "enabled": True
            }
        }

    except Exception as e:
        logger.error(f"Rojo status endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Rojo status: {str(e)}"
        )

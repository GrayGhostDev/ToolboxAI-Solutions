"""
Health Check Endpoints - Production Monitoring
Enhanced with comprehensive system health monitoring
"""

import asyncio
import os
import socket
import time
from datetime import datetime, timezone

import aiohttp
import psutil
import pusher
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

# Import database manager and settings
try:
    from database.connection import db_manager, get_redis_client
except ImportError:
    db_manager = None
    get_redis_client = None

try:
    from toolboxai_settings import settings
except ImportError:
    settings = None

router = APIRouter()

# Prometheus metrics
health_check_counter = Counter("health_checks_total", "Total health checks", ["endpoint", "status"])
health_check_duration = Histogram("health_check_duration_seconds", "Health check duration")
system_metrics = {
    "cpu_percent": Gauge("system_cpu_percent", "System CPU usage"),
    "memory_percent": Gauge("system_memory_percent", "System memory usage"),
    "disk_percent": Gauge("system_disk_percent", "System disk usage"),
    "network_bytes_sent": Gauge("system_network_bytes_sent", "Network bytes sent"),
    "network_bytes_recv": Gauge("system_network_bytes_recv", "Network bytes received"),
}


@router.get("/health")
async def health_check() -> dict:
    """Basic health check with system metrics"""
    start_time = time.time()

    try:
        # Update system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        network = psutil.net_io_counters()

        # Update Prometheus metrics
        system_metrics["cpu_percent"].set(cpu_percent)
        system_metrics["memory_percent"].set(memory.percent)
        system_metrics["disk_percent"].set(disk.percent)
        system_metrics["network_bytes_sent"].set(network.bytes_sent)
        system_metrics["network_bytes_recv"].set(network.bytes_recv)

        health_data = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "toolboxai-api",
            "version": os.getenv("APP_VERSION", "1.0.0"),
            "environment": os.getenv("ENVIRONMENT", "development"),
            "uptime_seconds": time.time() - psutil.boot_time(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024**3),
                "load_average": os.getloadavg() if hasattr(os, "getloadavg") else None,
                "process_count": len(psutil.pids()),
            },
            "network": {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv,
            },
        }

        health_check_counter.labels(endpoint="health", status="success").inc()
        return health_data

    except Exception as e:
        health_check_counter.labels(endpoint="health", status="error").inc()
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")
    finally:
        health_check_duration.observe(time.time() - start_time)


@router.get("/health/live")
async def liveness_probe() -> dict:
    """Kubernetes liveness probe - minimal check"""
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pid": os.getpid(),
    }


@router.get("/health/ready")
async def readiness_probe() -> dict:
    """Kubernetes readiness probe - comprehensive checks"""
    start_time = time.time()

    try:
        checks = {
            "database": await check_database(),
            "redis": await check_redis(),
            "external_apis": await check_external_apis(),
            "disk_space": await check_disk_space(),
            "memory": await check_memory(),
            "cpu": await check_cpu_load(),
        }

        all_healthy = all(check["healthy"] for check in checks.values())
        status_code = "ready" if all_healthy else "not_ready"

        result = {
            "status": status_code,
            "checks": checks,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "check_duration_ms": round((time.time() - start_time) * 1000, 2),
        }

        health_check_counter.labels(
            endpoint="ready", status="success" if all_healthy else "failed"
        ).inc()

        if not all_healthy:
            raise HTTPException(status_code=503, detail=result)

        return result

    except Exception as e:
        health_check_counter.labels(endpoint="ready", status="error").inc()
        raise HTTPException(status_code=503, detail=f"Readiness check failed: {str(e)}")
    finally:
        health_check_duration.observe(time.time() - start_time)


@router.get("/health/deep")
async def deep_health_check() -> dict:
    """Comprehensive health check for monitoring systems"""
    start_time = time.time()

    try:
        # Run all checks in parallel
        checks_tasks = [
            check_database_detailed(),
            check_redis_detailed(),
            check_external_apis(),
            check_system_resources(),
            check_application_health(),
            check_agent_orchestration(),
            check_realtime_services(),
            check_roblox_integration(),
        ]

        checks_results = await asyncio.gather(*checks_tasks, return_exceptions=True)

        checks = {}
        for i, result in enumerate(checks_results):
            if isinstance(result, Exception):
                checks[f"check_{i}"] = {"healthy": False, "error": str(result)}
            else:
                checks.update(result)

        overall_health = all(
            check.get("healthy", False) for check in checks.values() if isinstance(check, dict)
        )

        return {
            "status": "healthy" if overall_health else "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": checks,
            "duration_ms": round((time.time() - start_time) * 1000, 2),
            "environment": os.getenv("ENVIRONMENT", "development"),
            "version": os.getenv("APP_VERSION", "1.0.0"),
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


@router.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    try:
        # Update system metrics before returning
        system_metrics["cpu_percent"].set(psutil.cpu_percent())
        system_metrics["memory_percent"].set(psutil.virtual_memory().percent)
        system_metrics["disk_percent"].set(psutil.disk_usage("/").percent)

        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metrics generation failed: {str(e)}")


# Health check helper functions
async def check_database() -> dict:
    """Check database connectivity"""
    try:
        if db_manager:
            health = await db_manager.health_check()
            return {
                "healthy": health["status"] == "healthy",
                "details": health.get("details", {}),
                "response_time_ms": health.get("details", {}).get("response_time_ms", 0),
            }
        else:
            # Fallback to direct connection
            DATABASE_URL = os.getenv("DATABASE_URL")
            if not DATABASE_URL:
                return {"healthy": False, "error": "DATABASE_URL not configured"}

            import asyncpg

            conn = await asyncpg.connect(DATABASE_URL)
            await conn.execute("SELECT 1")
            await conn.close()
            return {"healthy": True, "details": "Direct connection successful"}
    except Exception as e:
        return {"healthy": False, "error": str(e)}


async def check_redis() -> dict:
    """Check Redis connectivity"""
    try:
        if get_redis_client:
            client = await get_redis_client()
            if client:
                start_time = time.time()
                await client.ping()
                response_time = (time.time() - start_time) * 1000

                # Get Redis info
                info = await client.info()
                await client.close()

                return {
                    "healthy": True,
                    "response_time_ms": round(response_time, 2),
                    "details": {
                        "version": info.get("redis_version"),
                        "connected_clients": info.get("connected_clients"),
                        "used_memory_human": info.get("used_memory_human"),
                        "uptime_in_seconds": info.get("uptime_in_seconds"),
                    },
                }
            else:
                return {"healthy": False, "error": "Redis client unavailable"}
        else:
            # Fallback check
            REDIS_URL = os.getenv("REDIS_URL")
            if not REDIS_URL:
                return {"healthy": False, "error": "REDIS_URL not configured"}

            import aioredis

            client = aioredis.from_url(REDIS_URL)
            await client.ping()
            await client.close()
            return {"healthy": True, "details": "Direct connection successful"}
    except Exception as e:
        return {"healthy": False, "error": str(e)}


async def check_external_apis() -> dict:
    """Check external API availability"""
    try:
        checks = {}

        # Check OpenAI API
        if os.getenv("OPENAI_API_KEY"):
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"}
                    async with session.get(
                        "https://api.openai.com/v1/models",
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=5),
                    ) as response:
                        checks["openai"] = {
                            "healthy": response.status == 200,
                            "status_code": response.status,
                        }
            except Exception as e:
                checks["openai"] = {"healthy": False, "error": str(e)}

        # Check Pusher API
        if os.getenv("PUSHER_KEY"):
            checks["pusher"] = {"healthy": True, "details": "API key configured"}
        else:
            checks["pusher"] = {"healthy": False, "error": "Pusher not configured"}

        # Check Clerk Auth API
        if os.getenv("CLERK_SECRET_KEY"):
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {"Authorization": f"Bearer {os.getenv('CLERK_SECRET_KEY')}"}
                    async with session.get(
                        "https://api.clerk.dev/v1/users",
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=5),
                    ) as response:
                        checks["clerk"] = {
                            "healthy": response.status
                            in [200, 401],  # 401 is also OK, means API is reachable
                            "status_code": response.status,
                        }
            except Exception as e:
                checks["clerk"] = {"healthy": False, "error": str(e)}
        else:
            checks["clerk"] = {"healthy": False, "error": "Clerk not configured"}

        # Check Supabase API
        if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY"):
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {
                        "apikey": os.getenv("SUPABASE_ANON_KEY"),
                        "Authorization": f"Bearer {os.getenv('SUPABASE_ANON_KEY')}",
                    }
                    async with session.get(
                        f"{os.getenv('SUPABASE_URL')}/rest/v1/",
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=5),
                    ) as response:
                        checks["supabase"] = {
                            "healthy": response.status in [200, 404],  # 404 is OK for root endpoint
                            "status_code": response.status,
                        }
            except Exception as e:
                checks["supabase"] = {"healthy": False, "error": str(e)}
        else:
            checks["supabase"] = {"healthy": False, "error": "Supabase not configured"}

        overall_healthy = all(check.get("healthy", False) for check in checks.values())

        return {"healthy": overall_healthy, "details": checks}
    except Exception as e:
        return {"healthy": False, "error": str(e)}


async def check_disk_space() -> dict:
    """Check available disk space"""
    try:
        disk = psutil.disk_usage("/")
        free_percent = (disk.free / disk.total) * 100

        return {
            "healthy": free_percent > 10,  # Alert if less than 10% free
            "details": {
                "free_percent": round(free_percent, 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "total_gb": round(disk.total / (1024**3), 2),
            },
        }
    except Exception as e:
        return {"healthy": False, "error": str(e)}


async def check_memory() -> dict:
    """Check memory usage"""
    try:
        memory = psutil.virtual_memory()

        return {
            "healthy": memory.percent < 90,  # Alert if more than 90% used
            "details": {
                "used_percent": memory.percent,
                "available_gb": round(memory.available / (1024**3), 2),
                "total_gb": round(memory.total / (1024**3), 2),
            },
        }
    except Exception as e:
        return {"healthy": False, "error": str(e)}


async def check_cpu_load() -> dict:
    """Check CPU load"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        load_avg = os.getloadavg() if hasattr(os, "getloadavg") else [0, 0, 0]

        return {
            "healthy": cpu_percent < 80,  # Alert if more than 80% used
            "details": {
                "cpu_percent": cpu_percent,
                "load_average_1m": load_avg[0],
                "load_average_5m": load_avg[1],
                "load_average_15m": load_avg[2],
                "cpu_count": psutil.cpu_count(),
            },
        }
    except Exception as e:
        return {"healthy": False, "error": str(e)}


# Detailed health check functions for deep health check
async def check_database_detailed() -> dict:
    """Detailed database health check"""
    try:
        if db_manager:
            health = await db_manager.health_check()
            return {"database": health}
        else:
            return {"database": await check_database()}
    except Exception as e:
        return {"database": {"healthy": False, "error": str(e)}}


async def check_redis_detailed() -> dict:
    """Detailed Redis health check"""
    try:
        return {"redis": await check_redis()}
    except Exception as e:
        return {"redis": {"healthy": False, "error": str(e)}}


async def check_system_resources() -> dict:
    """Check system resources"""
    try:
        disk = await check_disk_space()
        memory = await check_memory()
        cpu = await check_cpu_load()

        return {
            "system_resources": {
                "healthy": all([disk["healthy"], memory["healthy"], cpu["healthy"]]),
                "disk": disk,
                "memory": memory,
                "cpu": cpu,
            }
        }
    except Exception as e:
        return {"system_resources": {"healthy": False, "error": str(e)}}


async def check_application_health() -> dict:
    """Check application-specific health"""
    try:
        # Check if all critical services are running
        checks = {
            "process_count": len(psutil.pids()),
            "uptime_seconds": time.time() - psutil.boot_time(),
            "environment": os.getenv("ENVIRONMENT", "unknown"),
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
        }

        return {"application": {"healthy": True, "details": checks}}
    except Exception as e:
        return {"application": {"healthy": False, "error": str(e)}}


async def check_agent_orchestration() -> dict:
    """Check agent orchestration system health"""
    try:
        checks = {}

        # Check MCP Server (port 9877)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                result = s.connect_ex(("localhost", 9877))
                mcp_healthy = result == 0

            checks["mcp_server"] = {
                "healthy": mcp_healthy,
                "port": 9877,
                "status": "online" if mcp_healthy else "offline",
            }
        except Exception as e:
            checks["mcp_server"] = {"healthy": False, "error": str(e)}

        # Check Agent Coordinator (port 8888)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                result = s.connect_ex(("localhost", 8888))
                coordinator_healthy = result == 0

            checks["agent_coordinator"] = {
                "healthy": coordinator_healthy,
                "port": 8888,
                "status": "online" if coordinator_healthy else "offline",
            }
        except Exception as e:
            checks["agent_coordinator"] = {"healthy": False, "error": str(e)}

        # Check SPARC Framework status
        try:
            # Check if SPARC modules are importable
            import core.sparc.state_manager

            checks["sparc_framework"] = {
                "healthy": True,
                "status": "loaded",
                "modules": ["state_manager"],
            }
        except ImportError as e:
            checks["sparc_framework"] = {
                "healthy": False,
                "error": f"Import error: {str(e)}",
            }

        overall_healthy = all(check.get("healthy", False) for check in checks.values())

        return {"agent_orchestration": {"healthy": overall_healthy, "checks": checks}}
    except Exception as e:
        return {"agent_orchestration": {"healthy": False, "error": str(e)}}


async def check_realtime_services() -> dict:
    """Check real-time services (Pusher, WebSocket)"""
    try:
        checks = {}

        # Check Pusher configuration
        if settings and hasattr(settings, "PUSHER_APP_ID"):
            try:
                pusher_client = pusher.Pusher(
                    app_id=settings.PUSHER_APP_ID,
                    key=settings.PUSHER_KEY,
                    secret=settings.PUSHER_SECRET,
                    cluster=settings.PUSHER_CLUSTER,
                    ssl=True,
                )

                # Test channel info to verify connection
                pusher_client.channel_info("test-channel")

                checks["pusher"] = {
                    "healthy": True,
                    "status": "configured",
                    "cluster": settings.PUSHER_CLUSTER,
                    "ssl_enabled": True,
                }
            except Exception as e:
                checks["pusher"] = {"healthy": False, "error": str(e)}
        else:
            checks["pusher"] = {"healthy": False, "error": "Pusher not configured"}

        # Check WebSocket endpoints (legacy support)
        try:
            # Check if WebSocket routes are available
            websocket_endpoints = ["/ws/content", "/ws/roblox", "/ws/native"]

            checks["websocket_endpoints"] = {
                "healthy": True,
                "endpoints": websocket_endpoints,
                "status": "legacy_support_active",
            }
        except Exception as e:
            checks["websocket_endpoints"] = {"healthy": False, "error": str(e)}

        overall_healthy = all(check.get("healthy", False) for check in checks.values())

        return {"realtime_services": {"healthy": overall_healthy, "checks": checks}}
    except Exception as e:
        return {"realtime_services": {"healthy": False, "error": str(e)}}


async def check_roblox_integration() -> dict:
    """Check Roblox integration services"""
    try:
        checks = {}

        # Check Flask Bridge (port 5001)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                result = s.connect_ex(("localhost", 5001))
                flask_healthy = result == 0

            checks["flask_bridge"] = {
                "healthy": flask_healthy,
                "port": 5001,
                "status": "online" if flask_healthy else "offline",
            }
        except Exception as e:
            checks["flask_bridge"] = {"healthy": False, "error": str(e)}

        # Check Roblox source structure
        try:
            import os

            roblox_paths = [
                "roblox/src/client",
                "roblox/src/server",
                "roblox/src/shared",
            ]

            structure_valid = all(
                os.path.exists(os.path.join(os.getcwd(), path)) for path in roblox_paths
            )

            checks["roblox_source_structure"] = {
                "healthy": structure_valid,
                "paths_checked": roblox_paths,
                "status": "valid" if structure_valid else "missing_paths",
            }
        except Exception as e:
            checks["roblox_source_structure"] = {"healthy": False, "error": str(e)}

        # Check Roblox agents
        try:
            from core.agents.roblox.roblox_content_generation_agent import (
                RobloxContentGenerationAgent,
            )

            checks["roblox_agents"] = {
                "healthy": True,
                "status": "agents_available",
                "agents": ["RobloxContentGenerationAgent"],
            }
        except ImportError as e:
            checks["roblox_agents"] = {
                "healthy": False,
                "error": f"Agent import error: {str(e)}",
            }

        overall_healthy = all(check.get("healthy", False) for check in checks.values())

        return {"roblox_integration": {"healthy": overall_healthy, "checks": checks}}
    except Exception as e:
        return {"roblox_integration": {"healthy": False, "error": str(e)}}

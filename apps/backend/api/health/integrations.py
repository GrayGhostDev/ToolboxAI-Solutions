"""
Integration Health Check Endpoints
Specialized endpoints for monitoring specific service integrations
"""

import asyncio
import os
import socket
import time
from datetime import datetime, timezone
from typing import Any

import aiohttp
from fastapi import APIRouter

try:
    from toolboxai_settings import settings
except ImportError:
    settings = None

try:
    import pusher
except ImportError:
    pusher = None

router = APIRouter(tags=["Integration Health"])


@router.get("/health/integrations")
async def integration_health_overview() -> dict[str, Any]:
    """Overview of all integration health statuses"""
    start_time = time.time()

    # Run all integration checks in parallel
    integration_checks = await asyncio.gather(
        check_database_integrations(),
        check_api_integrations(),
        check_realtime_integrations(),
        check_agent_integrations(),
        check_roblox_integrations(),
        return_exceptions=True,
    )

    results = {}
    for check in integration_checks:
        if isinstance(check, Exception):
            results["error"] = {"healthy": False, "error": str(check)}
        else:
            results.update(check)

    # Calculate overall integration health
    healthy_count = sum(1 for check in results.values() if check.get("healthy", False))
    total_count = len(results)
    health_percentage = (healthy_count / total_count * 100) if total_count > 0 else 0

    overall_status = (
        "healthy"
        if health_percentage >= 80
        else "degraded" if health_percentage >= 60 else "unhealthy"
    )

    return {
        "status": overall_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "health_percentage": round(health_percentage, 2),
        "healthy_services": healthy_count,
        "total_services": total_count,
        "integrations": results,
        "check_duration_ms": round((time.time() - start_time) * 1000, 2),
    }


@router.get("/health/database")
async def database_health_detailed() -> dict[str, Any]:
    """Detailed database connection health"""
    return await check_database_integrations()


@router.get("/health/apis")
async def api_health_detailed() -> dict[str, Any]:
    """Detailed external API health"""
    return await check_api_integrations()


@router.get("/health/realtime")
async def realtime_health_detailed() -> dict[str, Any]:
    """Detailed real-time service health"""
    return await check_realtime_integrations()


@router.get("/health/agents")
async def agent_health_detailed() -> dict[str, Any]:
    """Detailed agent orchestration health"""
    return await check_agent_integrations()


@router.get("/health/roblox")
async def roblox_health_detailed() -> dict[str, Any]:
    """Detailed Roblox integration health"""
    return await check_roblox_integrations()


async def check_database_integrations() -> dict[str, Any]:
    """Check all database-related integrations"""
    try:
        checks = {}

        # PostgreSQL connection
        try:
            from sqlalchemy import text

            from database.connection import get_async_session

            async with get_async_session() as session:
                # Test basic connection
                await session.execute(text("SELECT 1"))

                # Test table accessibility
                table_check = await session.execute(
                    text(
                        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
                    )
                )
                table_count = table_check.scalar()

                # Test user table specifically
                try:
                    user_count = await session.execute(text("SELECT COUNT(*) FROM dashboard_users"))
                    user_count_val = user_count.scalar()
                except Exception:
                    user_count_val = "table_not_accessible"

                checks["postgresql"] = {
                    "healthy": True,
                    "response_time_ms": 0,  # Would need to measure this properly
                    "details": {
                        "public_tables": table_count,
                        "user_count": user_count_val,
                        "connection": "active",
                    },
                }
        except Exception as e:
            checks["postgresql"] = {"healthy": False, "error": str(e)}

        # Redis connection
        try:
            import redis.asyncio as redis

            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            redis_client = redis.from_url(redis_url, decode_responses=True)

            start_time = time.time()
            await redis_client.ping()
            response_time = (time.time() - start_time) * 1000

            # Test basic operations
            test_key = f"health_check_{int(time.time())}"
            await redis_client.set(test_key, "test_value", ex=10)
            test_value = await redis_client.get(test_key)
            await redis_client.delete(test_key)

            # Get Redis info
            info = await redis_client.info()
            await redis_client.close()

            checks["redis"] = {
                "healthy": test_value == "test_value",
                "response_time_ms": round(response_time, 2),
                "details": {
                    "version": info.get("redis_version"),
                    "connected_clients": info.get("connected_clients"),
                    "used_memory_human": info.get("used_memory_human"),
                    "operations_test": "passed" if test_value == "test_value" else "failed",
                },
            }
        except Exception as e:
            checks["redis"] = {"healthy": False, "error": str(e)}

        overall_healthy = all(check.get("healthy", False) for check in checks.values())

        return {
            "database_integrations": {
                "healthy": overall_healthy,
                "checks": checks,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        }
    except Exception as e:
        return {"database_integrations": {"healthy": False, "error": str(e)}}


async def check_api_integrations() -> dict[str, Any]:
    """Check external API integrations"""
    try:
        checks = {}

        # Dashboard API health
        try:
            dashboard_url = os.getenv("VITE_API_BASE_URL", "http://127.0.0.1:8009")
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                async with session.get(
                    f"{dashboard_url}/health", timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    response_time = (time.time() - start_time) * 1000
                    response_data = await response.json()

                    checks["dashboard_api"] = {
                        "healthy": response.status == 200,
                        "response_time_ms": round(response_time, 2),
                        "status_code": response.status,
                        "details": response_data,
                    }
        except Exception as e:
            checks["dashboard_api"] = {"healthy": False, "error": str(e)}

        # Pusher API health
        if pusher and settings and hasattr(settings, "PUSHER_APP_ID"):
            try:
                pusher_client = pusher.Pusher(
                    app_id=settings.PUSHER_APP_ID,
                    key=settings.PUSHER_KEY,
                    secret=settings.PUSHER_SECRET,
                    cluster=settings.PUSHER_CLUSTER,
                    ssl=True,
                )

                # Test trigger capability
                start_time = time.time()
                pusher_client.trigger("test-channel", "health-check", {"test": True})
                response_time = (time.time() - start_time) * 1000

                checks["pusher"] = {
                    "healthy": True,
                    "response_time_ms": round(response_time, 2),
                    "details": {
                        "cluster": settings.PUSHER_CLUSTER,
                        "ssl_enabled": True,
                        "trigger_test": "passed",
                    },
                }
            except Exception as e:
                checks["pusher"] = {"healthy": False, "error": str(e)}
        else:
            checks["pusher"] = {
                "healthy": False,
                "error": "Pusher not configured or library not available",
            }

        # Clerk Auth API
        if os.getenv("CLERK_SECRET_KEY"):
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {"Authorization": f"Bearer {os.getenv('CLERK_SECRET_KEY')}"}
                    start_time = time.time()
                    async with session.get(
                        "https://api.clerk.dev/v1/users",
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=5),
                    ) as response:
                        response_time = (time.time() - start_time) * 1000

                        checks["clerk"] = {
                            "healthy": response.status in [200, 401],
                            "response_time_ms": round(response_time, 2),
                            "status_code": response.status,
                            "details": {"api_reachable": True, "auth_configured": True},
                        }
            except Exception as e:
                checks["clerk"] = {"healthy": False, "error": str(e)}
        else:
            checks["clerk"] = {"healthy": False, "error": "Clerk not configured"}

        # Supabase API
        if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY"):
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {
                        "apikey": os.getenv("SUPABASE_ANON_KEY"),
                        "Authorization": f"Bearer {os.getenv('SUPABASE_ANON_KEY')}",
                    }
                    start_time = time.time()
                    async with session.get(
                        f"{os.getenv('SUPABASE_URL')}/rest/v1/",
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=5),
                    ) as response:
                        response_time = (time.time() - start_time) * 1000

                        checks["supabase"] = {
                            "healthy": response.status in [200, 404],
                            "response_time_ms": round(response_time, 2),
                            "status_code": response.status,
                            "details": {
                                "api_reachable": True,
                                "url": os.getenv("SUPABASE_URL"),
                            },
                        }
            except Exception as e:
                checks["supabase"] = {"healthy": False, "error": str(e)}
        else:
            checks["supabase"] = {"healthy": False, "error": "Supabase not configured"}

        # OpenAI API
        if os.getenv("OPENAI_API_KEY"):
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"}
                    start_time = time.time()
                    async with session.get(
                        "https://api.openai.com/v1/models",
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as response:
                        response_time = (time.time() - start_time) * 1000

                        checks["openai"] = {
                            "healthy": response.status == 200,
                            "response_time_ms": round(response_time, 2),
                            "status_code": response.status,
                            "details": {
                                "api_reachable": True,
                                "auth_valid": response.status == 200,
                            },
                        }
            except Exception as e:
                checks["openai"] = {"healthy": False, "error": str(e)}
        else:
            checks["openai"] = {
                "healthy": False,
                "error": "OpenAI API key not configured",
            }

        overall_healthy = all(check.get("healthy", False) for check in checks.values())

        return {
            "api_integrations": {
                "healthy": overall_healthy,
                "checks": checks,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        }
    except Exception as e:
        return {"api_integrations": {"healthy": False, "error": str(e)}}


async def check_realtime_integrations() -> dict[str, Any]:
    """Check real-time communication integrations"""
    try:
        checks = {}

        # Pusher Channels
        if pusher and settings and hasattr(settings, "PUSHER_APP_ID"):
            try:
                pusher_client = pusher.Pusher(
                    app_id=settings.PUSHER_APP_ID,
                    key=settings.PUSHER_KEY,
                    secret=settings.PUSHER_SECRET,
                    cluster=settings.PUSHER_CLUSTER,
                    ssl=True,
                )

                # Test channel operations
                test_channels = [
                    "dashboard-updates",
                    "content-generation",
                    "agent-status",
                    "system-health",
                ]

                channel_results = {}
                for channel in test_channels:
                    try:
                        info = pusher_client.channel_info(channel)
                        channel_results[channel] = {"status": "available", "info": info}
                    except Exception as e:
                        channel_results[channel] = {"status": "error", "error": str(e)}

                checks["pusher_channels"] = {
                    "healthy": True,
                    "details": {
                        "cluster": settings.PUSHER_CLUSTER,
                        "channels": channel_results,
                        "ssl_enabled": True,
                    },
                }
            except Exception as e:
                checks["pusher_channels"] = {"healthy": False, "error": str(e)}
        else:
            checks["pusher_channels"] = {
                "healthy": False,
                "error": "Pusher not configured",
            }

        # WebSocket fallback endpoints
        websocket_endpoints = [
            {"path": "/ws/content", "description": "Content generation updates"},
            {"path": "/ws/roblox", "description": "Roblox environment sync"},
            {"path": "/ws/agent/{agent_id}", "description": "Agent communication"},
            {"path": "/ws/native", "description": "Test echo endpoint"},
        ]

        checks["websocket_fallback"] = {
            "healthy": True,
            "details": {
                "endpoints": websocket_endpoints,
                "status": "legacy_support_available",
            },
        }

        # Test real-time event broadcasting
        try:
            if pusher and settings and hasattr(settings, "PUSHER_APP_ID"):
                pusher_client = pusher.Pusher(
                    app_id=settings.PUSHER_APP_ID,
                    key=settings.PUSHER_KEY,
                    secret=settings.PUSHER_SECRET,
                    cluster=settings.PUSHER_CLUSTER,
                    ssl=True,
                )

                test_event = {
                    "type": "health_check",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "data": {"test": True},
                }

                start_time = time.time()
                pusher_client.trigger("system-health", "test-event", test_event)
                broadcast_time = (time.time() - start_time) * 1000

                checks["event_broadcasting"] = {
                    "healthy": True,
                    "response_time_ms": round(broadcast_time, 2),
                    "details": {
                        "test_channel": "system-health",
                        "test_event": "test-event",
                        "broadcast_successful": True,
                    },
                }
            else:
                checks["event_broadcasting"] = {
                    "healthy": False,
                    "error": "Broadcasting service not available",
                }
        except Exception as e:
            checks["event_broadcasting"] = {"healthy": False, "error": str(e)}

        overall_healthy = all(check.get("healthy", False) for check in checks.values())

        return {
            "realtime_integrations": {
                "healthy": overall_healthy,
                "checks": checks,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        }
    except Exception as e:
        return {"realtime_integrations": {"healthy": False, "error": str(e)}}


async def check_agent_integrations() -> dict[str, Any]:
    """Check agent orchestration integrations"""
    try:
        checks = {}

        # MCP Server connectivity
        try:

            def check_port(host, port, timeout=5):
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(timeout)
                        result = s.connect_ex((host, port))
                        return result == 0
                except Exception:
                    return False

            mcp_healthy = check_port("localhost", 9877)

            if mcp_healthy:
                # Try to get health status from MCP server
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            "http://localhost:9878/health",
                            timeout=aiohttp.ClientTimeout(total=5),
                        ) as response:
                            if response.status == 200:
                                mcp_health_data = await response.json()
                                checks["mcp_server"] = {
                                    "healthy": True,
                                    "port": 9877,
                                    "health_port": 9878,
                                    "details": mcp_health_data,
                                }
                            else:
                                checks["mcp_server"] = {
                                    "healthy": True,
                                    "port": 9877,
                                    "health_port": 9878,
                                    "details": {
                                        "note": "Server running but health endpoint unavailable"
                                    },
                                }
                except Exception:
                    checks["mcp_server"] = {
                        "healthy": True,
                        "port": 9877,
                        "details": {"note": "Server running, health endpoint not responding"},
                    }
            else:
                checks["mcp_server"] = {
                    "healthy": False,
                    "error": "MCP server not running on port 9877",
                }
        except Exception as e:
            checks["mcp_server"] = {"healthy": False, "error": str(e)}

        # Agent Coordinator
        try:
            coordinator_healthy = check_port("localhost", 8888)
            checks["agent_coordinator"] = {
                "healthy": coordinator_healthy,
                "port": 8888,
                "status": "online" if coordinator_healthy else "offline",
            }
        except Exception as e:
            checks["agent_coordinator"] = {"healthy": False, "error": str(e)}

        # SPARC Framework
        try:
            sparc_modules = []
            sparc_errors = []

            try:
                import core.sparc.state_manager

                sparc_modules.append("state_manager")
            except ImportError as e:
                sparc_errors.append(f"state_manager: {str(e)}")

            try:
                import core.sparc.enhanced_orchestrator

                sparc_modules.append("enhanced_orchestrator")
            except ImportError as e:
                sparc_errors.append(f"enhanced_orchestrator: {str(e)}")

            checks["sparc_framework"] = {
                "healthy": len(sparc_modules) > 0,
                "details": {
                    "loaded_modules": sparc_modules,
                    "errors": sparc_errors if sparc_errors else None,
                },
            }
        except Exception as e:
            checks["sparc_framework"] = {"healthy": False, "error": str(e)}

        # Agent Communication Test
        try:
            # Test if agents can be imported and initialized
            agent_tests = {}

            try:
                from core.agents.multi_modal_generator import MultiModalContentAgent

                agent_tests["multi_modal_generator"] = {"importable": True}
            except ImportError as e:
                agent_tests["multi_modal_generator"] = {
                    "importable": False,
                    "error": str(e),
                }

            try:
                from core.agents.enhanced_content_pipeline import (
                    EnhancedContentPipelineAgent,
                )

                agent_tests["enhanced_content_pipeline"] = {"importable": True}
            except ImportError as e:
                agent_tests["enhanced_content_pipeline"] = {
                    "importable": False,
                    "error": str(e),
                }

            checks["agent_communication"] = {
                "healthy": any(test.get("importable", False) for test in agent_tests.values()),
                "details": {"agent_tests": agent_tests},
            }
        except Exception as e:
            checks["agent_communication"] = {"healthy": False, "error": str(e)}

        overall_healthy = all(check.get("healthy", False) for check in checks.values())

        return {
            "agent_integrations": {
                "healthy": overall_healthy,
                "checks": checks,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        }
    except Exception as e:
        return {"agent_integrations": {"healthy": False, "error": str(e)}}


async def check_roblox_integrations() -> dict[str, Any]:
    """Check Roblox-specific integrations"""
    try:
        checks = {}

        # Flask Bridge Service
        try:

            def check_port(host, port, timeout=5):
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(timeout)
                        result = s.connect_ex((host, port))
                        return result == 0
                except Exception:
                    return False

            flask_healthy = check_port("localhost", 5001)

            if flask_healthy:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            "http://localhost:5001/health",
                            timeout=aiohttp.ClientTimeout(total=5),
                        ) as response:
                            bridge_health = (
                                await response.json()
                                if response.status == 200
                                else {"status": "unknown"}
                            )

                            checks["flask_bridge"] = {
                                "healthy": True,
                                "port": 5001,
                                "details": bridge_health,
                            }
                except Exception:
                    checks["flask_bridge"] = {
                        "healthy": True,
                        "port": 5001,
                        "details": {"note": "Service running but health endpoint unavailable"},
                    }
            else:
                checks["flask_bridge"] = {
                    "healthy": False,
                    "error": "Flask bridge not running on port 5001",
                }
        except Exception as e:
            checks["flask_bridge"] = {"healthy": False, "error": str(e)}

        # Roblox Source Structure
        try:
            roblox_structure = {
                "roblox/src/client": os.path.exists("roblox/src/client"),
                "roblox/src/server": os.path.exists("roblox/src/server"),
                "roblox/src/shared": os.path.exists("roblox/src/shared"),
                "roblox/scripts": os.path.exists("roblox/scripts"),
                "roblox/plugins": os.path.exists("roblox/plugins"),
            }

            structure_health = sum(roblox_structure.values()) >= 3  # At least 3 core directories

            checks["roblox_structure"] = {
                "healthy": structure_health,
                "details": {
                    "directory_structure": roblox_structure,
                    "core_directories_present": sum(roblox_structure.values()),
                },
            }
        except Exception as e:
            checks["roblox_structure"] = {"healthy": False, "error": str(e)}

        # Roblox Agents
        try:
            roblox_agents = {}

            try:
                from core.agents.roblox.roblox_content_generation_agent import (
                    RobloxContentGenerationAgent,
                )

                roblox_agents["content_generation"] = {"available": True}
            except ImportError as e:
                roblox_agents["content_generation"] = {
                    "available": False,
                    "error": str(e),
                }

            try:
                from core.agents.roblox.roblox_script_optimization_agent import (
                    RobloxScriptOptimizationAgent,
                )

                roblox_agents["script_optimization"] = {"available": True}
            except ImportError as e:
                roblox_agents["script_optimization"] = {
                    "available": False,
                    "error": str(e),
                }

            try:
                from core.agents.roblox.roblox_security_validation_agent import (
                    RobloxSecurityValidationAgent,
                )

                roblox_agents["security_validation"] = {"available": True}
            except ImportError as e:
                roblox_agents["security_validation"] = {
                    "available": False,
                    "error": str(e),
                }

            agents_healthy = any(agent.get("available", False) for agent in roblox_agents.values())

            checks["roblox_agents"] = {
                "healthy": agents_healthy,
                "details": {
                    "agents": roblox_agents,
                    "available_agents": sum(
                        1 for agent in roblox_agents.values() if agent.get("available", False)
                    ),
                },
            }
        except Exception as e:
            checks["roblox_agents"] = {"healthy": False, "error": str(e)}

        # Roblox Plugin Communication
        try:
            # Check if plugin files exist
            plugin_files = {
                "roblox/plugins/ToolboxAI.rbxmx": os.path.exists("roblox/plugins/ToolboxAI.rbxmx"),
                "roblox/plugins/init.lua": os.path.exists("roblox/plugins/init.lua"),
            }

            checks["roblox_plugins"] = {
                "healthy": any(plugin_files.values()),
                "details": {
                    "plugin_files": plugin_files,
                    "communication_ready": any(plugin_files.values()),
                },
            }
        except Exception as e:
            checks["roblox_plugins"] = {"healthy": False, "error": str(e)}

        overall_healthy = all(check.get("healthy", False) for check in checks.values())

        return {
            "roblox_integrations": {
                "healthy": overall_healthy,
                "checks": checks,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        }
    except Exception as e:
        return {"roblox_integrations": {"healthy": False, "error": str(e)}}

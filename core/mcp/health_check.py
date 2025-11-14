"""
MCP Server Health Check Endpoint
Provides comprehensive health monitoring for the Model Context Protocol server.
"""

import asyncio
import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any

import psutil
from aiohttp import web

# Configure logging
logger = logging.getLogger(__name__)


class MCPHealthCheck:
    """Health check manager for MCP server"""

    def __init__(self, mcp_server=None):
        self.mcp_server = mcp_server
        self.start_time = time.time()

    async def basic_health(self) -> dict[str, Any]:
        """Basic health check endpoint"""
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "mcp-server",
            "version": "1.1.0",
            "uptime_seconds": time.time() - self.start_time,
            "process_id": os.getpid(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        }

    async def detailed_health(self) -> dict[str, Any]:
        """Detailed health check with dependencies"""
        start_time = time.time()

        checks = {
            "websocket_server": await self._check_websocket_server(),
            "memory_usage": await self._check_memory_usage(),
            "active_connections": await self._check_active_connections(),
            "context_store": await self._check_context_store(),
            "system_resources": await self._check_system_resources(),
        }

        all_healthy = all(check.get("healthy", False) for check in checks.values())

        return {
            "status": "healthy" if all_healthy else "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "mcp-server",
            "version": "1.1.0",
            "checks": checks,
            "check_duration_ms": round((time.time() - start_time) * 1000, 2),
            "uptime_seconds": time.time() - self.start_time,
        }

    async def _check_websocket_server(self) -> dict[str, Any]:
        """Check WebSocket server status"""
        try:
            if self.mcp_server and hasattr(self.mcp_server, "is_running"):
                is_running = self.mcp_server.is_running()
                return {
                    "healthy": is_running,
                    "details": {
                        "server_running": is_running,
                        "port": getattr(self.mcp_server, "port", 9877),
                    },
                }
            else:
                # Check if port 9877 is in use (indicating server is running)
                import socket

                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    result = s.connect_ex(("localhost", 9877))
                    is_running = result == 0

                return {
                    "healthy": is_running,
                    "details": {"server_running": is_running, "port": 9877},
                }
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    async def _check_memory_usage(self) -> dict[str, Any]:
        """Check memory usage of the MCP server process"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()

            return {
                "healthy": memory_percent < 80,  # Alert if using more than 80% of memory
                "details": {
                    "memory_percent": round(memory_percent, 2),
                    "memory_rss_mb": round(memory_info.rss / (1024 * 1024), 2),
                    "memory_vms_mb": round(memory_info.vms / (1024 * 1024), 2),
                },
            }
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    async def _check_active_connections(self) -> dict[str, Any]:
        """Check active WebSocket connections"""
        try:
            if self.mcp_server and hasattr(self.mcp_server, "clients"):
                active_connections = len(self.mcp_server.clients)
                return {
                    "healthy": True,
                    "details": {
                        "active_connections": active_connections,
                        "max_connections": getattr(self.mcp_server, "max_connections", 100),
                    },
                }
            else:
                return {
                    "healthy": True,
                    "details": {
                        "active_connections": 0,
                        "note": "Connection count not available",
                    },
                }
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    async def _check_context_store(self) -> dict[str, Any]:
        """Check context store health"""
        try:
            if self.mcp_server and hasattr(self.mcp_server, "context_store"):
                context_store = self.mcp_server.context_store

                # Basic operation test
                test_key = f"health_check_{int(time.time())}"
                test_data = {"test": True, "timestamp": time.time()}

                # Test store operation
                await context_store.store_context(test_key, test_data)
                retrieved = await context_store.get_context(test_key)

                # Cleanup
                await context_store.remove_context(test_key)

                return {
                    "healthy": retrieved is not None,
                    "details": {
                        "store_test": "passed",
                        "context_count": len(getattr(context_store, "contexts", {})),
                    },
                }
            else:
                return {
                    "healthy": True,
                    "details": {"note": "Context store not available for testing"},
                }
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    async def _check_system_resources(self) -> dict[str, Any]:
        """Check system resources available to MCP server"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # Memory usage
            memory = psutil.virtual_memory()

            # Disk usage
            disk = psutil.disk_usage("/")

            return {
                "healthy": cpu_percent < 80
                and memory.percent < 90
                and (disk.free / disk.total) > 0.1,
                "details": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_free_percent": round((disk.free / disk.total) * 100, 2),
                    "load_average": os.getloadavg() if hasattr(os, "getloadavg") else None,
                },
            }
        except Exception as e:
            return {"healthy": False, "error": str(e)}


# HTTP server for health checks
class MCPHealthServer:
    """HTTP server for MCP health endpoints"""

    def __init__(self, mcp_server=None, port=9878):
        self.mcp_server = mcp_server
        self.port = port
        self.health_checker = MCPHealthCheck(mcp_server)
        self.app = None

    def setup_routes(self):
        """Setup HTTP routes for health checks"""
        self.app = web.Application()

        # Basic health endpoint
        self.app.router.add_get("/health", self.basic_health_handler)

        # Detailed health endpoint
        self.app.router.add_get("/health/detailed", self.detailed_health_handler)

        # Liveness probe (for Kubernetes)
        self.app.router.add_get("/health/live", self.liveness_handler)

        # Readiness probe (for Kubernetes)
        self.app.router.add_get("/health/ready", self.readiness_handler)

        # Metrics endpoint (basic)
        self.app.router.add_get("/metrics", self.metrics_handler)

    async def basic_health_handler(self, request):
        """Handle basic health check requests"""
        try:
            health_data = await self.health_checker.basic_health()
            return web.json_response(health_data, status=200)
        except Exception as e:
            return web.json_response(
                {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                status=500,
            )

    async def detailed_health_handler(self, request):
        """Handle detailed health check requests"""
        try:
            health_data = await self.health_checker.detailed_health()
            status_code = 200 if health_data["status"] == "healthy" else 503
            return web.json_response(health_data, status=status_code)
        except Exception as e:
            return web.json_response(
                {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                status=500,
            )

    async def liveness_handler(self, request):
        """Handle Kubernetes liveness probe"""
        return web.json_response(
            {
                "status": "alive",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "service": "mcp-server",
            },
            status=200,
        )

    async def readiness_handler(self, request):
        """Handle Kubernetes readiness probe"""
        try:
            health_data = await self.health_checker.detailed_health()
            is_ready = health_data["status"] == "healthy"

            return web.json_response(
                {
                    "status": "ready" if is_ready else "not_ready",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "checks": health_data["checks"],
                },
                status=200 if is_ready else 503,
            )
        except Exception as e:
            return web.json_response(
                {
                    "status": "not_ready",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                status=503,
            )

    async def metrics_handler(self, request):
        """Handle basic metrics endpoint (Prometheus format)"""
        try:
            health_data = await self.health_checker.detailed_health()

            # Convert health data to Prometheus format
            metrics = []
            metrics.append(f'mcp_server_up {{service="mcp-server"}} 1')
            metrics.append(
                f'mcp_server_uptime_seconds {{service="mcp-server"}} {health_data.get("uptime_seconds", 0)}'
            )

            if "active_connections" in health_data.get("checks", {}):
                conn_count = (
                    health_data["checks"]["active_connections"]
                    .get("details", {})
                    .get("active_connections", 0)
                )
                metrics.append(
                    f'mcp_server_active_connections {{service="mcp-server"}} {conn_count}'
                )

            if "memory_usage" in health_data.get("checks", {}):
                memory_percent = (
                    health_data["checks"]["memory_usage"]
                    .get("details", {})
                    .get("memory_percent", 0)
                )
                metrics.append(
                    f'mcp_server_memory_percent {{service="mcp-server"}} {memory_percent}'
                )

            metrics_text = "\n".join(metrics) + "\n"

            return web.Response(
                text=metrics_text,
                content_type="text/plain; version=0.0.4; charset=utf-8",
                status=200,
            )
        except Exception as e:
            logger.error(f"Error generating metrics: {e}")
            return web.Response(
                text=f"# Error generating metrics: {str(e)}\n",
                content_type="text/plain",
                status=500,
            )

    async def start_server(self):
        """Start the health check HTTP server"""
        self.setup_routes()

        runner = web.AppRunner(self.app)
        await runner.setup()

        site = web.TCPSite(runner, "0.0.0.0", self.port)
        await site.start()

        logger.info(f"MCP Health server started on port {self.port}")
        return runner


# Main function for standalone health server
async def run_health_server(mcp_server=None, port=9878):
    """Run the health check server"""
    health_server = MCPHealthServer(mcp_server, port)
    runner = await health_server.start_server()

    try:
        # Keep the server running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down health server...")
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    # Run standalone health server
    import argparse

    parser = argparse.ArgumentParser(description="MCP Health Check Server")
    parser.add_argument("--port", type=int, default=9878, help="Port to run health server on")
    args = parser.parse_args()

    asyncio.run(run_health_server(port=args.port))

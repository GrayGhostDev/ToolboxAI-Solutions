"""
Agent Coordinator Health Check Endpoints
Provides comprehensive health monitoring for the agent coordination system.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import aiohttp
from aiohttp import web
import psutil
import os
import sys

# Configure logging
logger = logging.getLogger(__name__)

class AgentCoordinatorHealthCheck:
    """Health check manager for Agent Coordinator"""

    def __init__(self, coordinator=None):
        self.coordinator = coordinator
        self.start_time = time.time()

    async def basic_health(self) -> Dict[str, Any]:
        """Basic health check endpoint"""
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "agent-coordinator",
            "version": "1.1.0",
            "uptime_seconds": time.time() - self.start_time,
            "process_id": os.getpid(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        }

    async def detailed_health(self) -> Dict[str, Any]:
        """Detailed health check with all agent systems"""
        start_time = time.time()

        checks = {
            "coordinator_service": await self._check_coordinator_service(),
            "active_agents": await self._check_active_agents(),
            "agent_communication": await self._check_agent_communication(),
            "swarm_coordination": await self._check_swarm_coordination(),
            "sparc_framework": await self._check_sparc_framework(),
            "task_queue": await self._check_task_queue(),
            "system_resources": await self._check_system_resources()
        }

        all_healthy = all(check.get("healthy", False) for check in checks.values())

        return {
            "status": "healthy" if all_healthy else "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "agent-coordinator",
            "version": "1.1.0",
            "checks": checks,
            "check_duration_ms": round((time.time() - start_time) * 1000, 2),
            "uptime_seconds": time.time() - self.start_time
        }

    async def _check_coordinator_service(self) -> Dict[str, Any]:
        """Check coordinator service status"""
        try:
            if self.coordinator:
                is_running = hasattr(self.coordinator, 'is_running') and self.coordinator.is_running()
                agent_count = len(getattr(self.coordinator, 'agents', {}))

                return {
                    "healthy": is_running,
                    "details": {
                        "service_running": is_running,
                        "registered_agents": agent_count,
                        "coordinator_type": type(self.coordinator).__name__ if self.coordinator else "Unknown"
                    }
                }
            else:
                # Check if coordinator port 8888 is in use
                import socket
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    result = s.connect_ex(('localhost', 8888))
                    is_running = result == 0

                return {
                    "healthy": is_running,
                    "details": {
                        "service_running": is_running,
                        "port": 8888,
                        "note": "Direct coordinator reference not available"
                    }
                }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }

    async def _check_active_agents(self) -> Dict[str, Any]:
        """Check status of active agents"""
        try:
            agent_stats = {
                "total_agents": 0,
                "healthy_agents": 0,
                "error_agents": 0,
                "agent_types": {}
            }

            if self.coordinator and hasattr(self.coordinator, 'agents'):
                agents = self.coordinator.agents
                agent_stats["total_agents"] = len(agents)

                for agent_id, agent in agents.items():
                    agent_type = type(agent).__name__
                    agent_stats["agent_types"][agent_type] = agent_stats["agent_types"].get(agent_type, 0) + 1

                    # Check if agent has health status
                    if hasattr(agent, 'is_healthy'):
                        if agent.is_healthy():
                            agent_stats["healthy_agents"] += 1
                        else:
                            agent_stats["error_agents"] += 1
                    else:
                        agent_stats["healthy_agents"] += 1  # Assume healthy if no health check

            return {
                "healthy": agent_stats["error_agents"] == 0,
                "details": agent_stats
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }

    async def _check_agent_communication(self) -> Dict[str, Any]:
        """Check agent-to-agent communication health"""
        try:
            communication_stats = {
                "message_queue_size": 0,
                "failed_messages": 0,
                "last_communication": None,
                "communication_channels": 0
            }

            if self.coordinator:
                # Check message queue if available
                if hasattr(self.coordinator, 'message_queue'):
                    communication_stats["message_queue_size"] = len(self.coordinator.message_queue)

                # Check communication channels
                if hasattr(self.coordinator, 'communication_channels'):
                    communication_stats["communication_channels"] = len(self.coordinator.communication_channels)

                # Check for recent communication
                if hasattr(self.coordinator, 'last_activity'):
                    communication_stats["last_communication"] = self.coordinator.last_activity

            return {
                "healthy": communication_stats["message_queue_size"] < 1000,  # Alert if queue is too large
                "details": communication_stats
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }

    async def _check_swarm_coordination(self) -> Dict[str, Any]:
        """Check swarm coordination system"""
        try:
            swarm_stats = {
                "active_swarms": 0,
                "swarm_health": True,
                "coordination_errors": 0
            }

            if self.coordinator and hasattr(self.coordinator, 'swarms'):
                swarms = self.coordinator.swarms
                swarm_stats["active_swarms"] = len(swarms)

                # Check each swarm health
                for swarm_id, swarm in swarms.items():
                    if hasattr(swarm, 'is_healthy') and not swarm.is_healthy():
                        swarm_stats["swarm_health"] = False
                        swarm_stats["coordination_errors"] += 1

            return {
                "healthy": swarm_stats["swarm_health"],
                "details": swarm_stats
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }

    async def _check_sparc_framework(self) -> Dict[str, Any]:
        """Check SPARC framework status"""
        try:
            sparc_stats = {
                "framework_loaded": False,
                "active_workflows": 0,
                "framework_errors": 0
            }

            # Try to import and check SPARC framework
            try:
                from core.sparc.state_manager import SPARCStateManager
                sparc_stats["framework_loaded"] = True

                # Check if coordinator has SPARC integration
                if self.coordinator and hasattr(self.coordinator, 'sparc_manager'):
                    sparc_manager = self.coordinator.sparc_manager
                    if hasattr(sparc_manager, 'active_workflows'):
                        sparc_stats["active_workflows"] = len(sparc_manager.active_workflows)

            except ImportError:
                sparc_stats["framework_errors"] += 1

            return {
                "healthy": sparc_stats["framework_loaded"] and sparc_stats["framework_errors"] == 0,
                "details": sparc_stats
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }

    async def _check_task_queue(self) -> Dict[str, Any]:
        """Check task queue health"""
        try:
            task_stats = {
                "pending_tasks": 0,
                "completed_tasks": 0,
                "failed_tasks": 0,
                "queue_health": True
            }

            if self.coordinator:
                # Check task queue if available
                if hasattr(self.coordinator, 'task_queue'):
                    task_queue = self.coordinator.task_queue
                    task_stats["pending_tasks"] = len(getattr(task_queue, 'pending', []))
                    task_stats["completed_tasks"] = len(getattr(task_queue, 'completed', []))
                    task_stats["failed_tasks"] = len(getattr(task_queue, 'failed', []))

                # Check if queue is overloaded
                if task_stats["pending_tasks"] > 100:
                    task_stats["queue_health"] = False

            return {
                "healthy": task_stats["queue_health"],
                "details": task_stats
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }

    async def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resources for agent coordination"""
        try:
            # Process-specific metrics
            process = psutil.Process()
            cpu_percent = process.cpu_percent()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()

            # System-wide metrics
            system_cpu = psutil.cpu_percent(interval=0.1)
            system_memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            return {
                "healthy": (
                    cpu_percent < 80 and
                    memory_percent < 80 and
                    system_memory.percent < 90 and
                    (disk.free / disk.total) > 0.1
                ),
                "details": {
                    "process_cpu_percent": cpu_percent,
                    "process_memory_percent": memory_percent,
                    "process_memory_mb": round(memory_info.rss / (1024 * 1024), 2),
                    "system_cpu_percent": system_cpu,
                    "system_memory_percent": system_memory.percent,
                    "disk_free_percent": round((disk.free / disk.total) * 100, 2),
                    "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
                }
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }

# HTTP server for health checks
class AgentCoordinatorHealthServer:
    """HTTP server for Agent Coordinator health endpoints"""

    def __init__(self, coordinator=None, port=8889):
        self.coordinator = coordinator
        self.port = port
        self.health_checker = AgentCoordinatorHealthCheck(coordinator)
        self.app = None

    def setup_routes(self):
        """Setup HTTP routes for health checks"""
        self.app = web.Application()

        # Basic health endpoint
        self.app.router.add_get('/health', self.basic_health_handler)

        # Detailed health endpoint
        self.app.router.add_get('/health/detailed', self.detailed_health_handler)

        # Agent-specific endpoints
        self.app.router.add_get('/health/agents', self.agents_health_handler)

        # Liveness probe (for Kubernetes)
        self.app.router.add_get('/health/live', self.liveness_handler)

        # Readiness probe (for Kubernetes)
        self.app.router.add_get('/health/ready', self.readiness_handler)

        # Metrics endpoint
        self.app.router.add_get('/metrics', self.metrics_handler)

    async def basic_health_handler(self, request):
        """Handle basic health check requests"""
        try:
            health_data = await self.health_checker.basic_health()
            return web.json_response(health_data, status=200)
        except Exception as e:
            return web.json_response({
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, status=500)

    async def detailed_health_handler(self, request):
        """Handle detailed health check requests"""
        try:
            health_data = await self.health_checker.detailed_health()
            status_code = 200 if health_data["status"] == "healthy" else 503
            return web.json_response(health_data, status=status_code)
        except Exception as e:
            return web.json_response({
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, status=500)

    async def agents_health_handler(self, request):
        """Handle agent-specific health checks"""
        try:
            agent_health = await self.health_checker._check_active_agents()
            return web.json_response({
                "status": "healthy" if agent_health["healthy"] else "unhealthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent_health": agent_health
            }, status=200)
        except Exception as e:
            return web.json_response({
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, status=500)

    async def liveness_handler(self, request):
        """Handle Kubernetes liveness probe"""
        return web.json_response({
            "status": "alive",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "agent-coordinator"
        }, status=200)

    async def readiness_handler(self, request):
        """Handle Kubernetes readiness probe"""
        try:
            health_data = await self.health_checker.detailed_health()
            is_ready = health_data["status"] == "healthy"

            return web.json_response({
                "status": "ready" if is_ready else "not_ready",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "checks": health_data["checks"]
            }, status=200 if is_ready else 503)
        except Exception as e:
            return web.json_response({
                "status": "not_ready",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, status=503)

    async def metrics_handler(self, request):
        """Handle metrics endpoint (Prometheus format)"""
        try:
            health_data = await self.health_checker.detailed_health()

            # Convert health data to Prometheus format
            metrics = []
            metrics.append(f'agent_coordinator_up {{service="agent-coordinator"}} 1')
            metrics.append(f'agent_coordinator_uptime_seconds {{service="agent-coordinator"}} {health_data.get("uptime_seconds", 0)}')

            # Agent metrics
            if "active_agents" in health_data.get("checks", {}):
                agent_details = health_data["checks"]["active_agents"].get("details", {})
                metrics.append(f'agent_coordinator_total_agents {{service="agent-coordinator"}} {agent_details.get("total_agents", 0)}')
                metrics.append(f'agent_coordinator_healthy_agents {{service="agent-coordinator"}} {agent_details.get("healthy_agents", 0)}')
                metrics.append(f'agent_coordinator_error_agents {{service="agent-coordinator"}} {agent_details.get("error_agents", 0)}')

            # Task queue metrics
            if "task_queue" in health_data.get("checks", {}):
                task_details = health_data["checks"]["task_queue"].get("details", {})
                metrics.append(f'agent_coordinator_pending_tasks {{service="agent-coordinator"}} {task_details.get("pending_tasks", 0)}')
                metrics.append(f'agent_coordinator_completed_tasks {{service="agent-coordinator"}} {task_details.get("completed_tasks", 0)}')
                metrics.append(f'agent_coordinator_failed_tasks {{service="agent-coordinator"}} {task_details.get("failed_tasks", 0)}')

            # Resource metrics
            if "system_resources" in health_data.get("checks", {}):
                resource_details = health_data["checks"]["system_resources"].get("details", {})
                metrics.append(f'agent_coordinator_cpu_percent {{service="agent-coordinator"}} {resource_details.get("process_cpu_percent", 0)}')
                metrics.append(f'agent_coordinator_memory_percent {{service="agent-coordinator"}} {resource_details.get("process_memory_percent", 0)}')

            metrics_text = '\n'.join(metrics) + '\n'

            return web.Response(
                text=metrics_text,
                content_type='text/plain; version=0.0.4; charset=utf-8',
                status=200
            )
        except Exception as e:
            logger.error(f"Error generating metrics: {e}")
            return web.Response(
                text=f'# Error generating metrics: {str(e)}\n',
                content_type='text/plain',
                status=500
            )

    async def start_server(self):
        """Start the health check HTTP server"""
        self.setup_routes()

        runner = web.AppRunner(self.app)
        await runner.setup()

        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()

        logger.info(f"Agent Coordinator Health server started on port {self.port}")
        return runner

# Main function for standalone health server
async def run_health_server(coordinator=None, port=8889):
    """Run the health check server"""
    health_server = AgentCoordinatorHealthServer(coordinator, port)
    runner = await health_server.start_server()

    try:
        # Keep the server running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down Agent Coordinator health server...")
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    # Run standalone health server
    import argparse

    parser = argparse.ArgumentParser(description='Agent Coordinator Health Check Server')
    parser.add_argument('--port', type=int, default=8889, help='Port to run health server on')
    args = parser.parse_args()

    asyncio.run(run_health_server(port=args.port))
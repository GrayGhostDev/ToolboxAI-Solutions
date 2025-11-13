"""
Docker test helper utilities.

This module provides utilities for testing Docker services integration.
"""

import asyncio
import time
from typing import Any

import aiohttp
import asyncpg
import docker
import redis.asyncio as redis


class DockerTestHelper:
    """Helper class for Docker integration testing."""

    def __init__(self):
        """Initialize Docker test helper."""
        self.docker_client = docker.from_env()
        self.containers = {}
        self.networks = {}

    def get_container_by_name(self, name: str) -> docker.models.containers.Container | None:
        """Get container by name."""
        try:
            return self.docker_client.containers.get(name)
        except docker.errors.NotFound:
            return None

    def get_containers_by_label(
        self, label: str, value: str = None
    ) -> list[docker.models.containers.Container]:
        """Get containers by label."""
        filters = {"label": label if value is None else f"{label}={value}"}
        return self.docker_client.containers.list(filters=filters)

    def get_toolboxai_containers(self) -> list[docker.models.containers.Container]:
        """Get all ToolboxAI containers."""
        containers = self.docker_client.containers.list()
        return [c for c in containers if "toolboxai" in c.name.lower()]

    async def wait_for_container_health(self, container_name: str, timeout: int = 60) -> bool:
        """Wait for container to become healthy."""
        container = self.get_container_by_name(container_name)
        if not container:
            return False

        start_time = time.time()
        while time.time() - start_time < timeout:
            container.reload()

            # Check health status
            health = container.attrs.get("State", {}).get("Health", {})
            if health:
                status = health.get("Status", "")
                if status == "healthy":
                    return True
                elif status == "unhealthy":
                    return False

            # If no health check, check if container is running
            if container.status == "running":
                await asyncio.sleep(5)  # Give it some time to fully start
                return True

            await asyncio.sleep(2)

        return False

    async def check_service_connectivity(self, host: str, port: int, timeout: int = 10) -> bool:
        """Check if service is reachable."""
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as session:
                async with session.get(f"http://{host}:{port}/health") as response:
                    return response.status == 200
        except Exception:
            return False

    async def check_database_connectivity(self, host: str = "localhost", port: int = 5434) -> bool:
        """Check database connectivity."""
        try:
            conn = await asyncpg.connect(
                host=host,
                port=port,
                database="educational_platform_dev",
                user="eduplatform",
                password="eduplatform2024",
                timeout=10,
            )
            result = await conn.fetchval("SELECT 1;")
            await conn.close()
            return result == 1
        except Exception:
            return False

    async def check_redis_connectivity(self, host: str = "localhost", port: int = 6381) -> bool:
        """Check Redis connectivity."""
        try:
            redis_client = await redis.from_url(f"redis://{host}:{port}/0", timeout=10)
            result = await redis_client.ping()
            await redis_client.close()
            return result
        except Exception:
            return False

    def get_container_logs(self, container_name: str, tail: int = 100) -> str:
        """Get container logs."""
        container = self.get_container_by_name(container_name)
        if container:
            return container.logs(tail=tail, timestamps=True).decode("utf-8")
        return ""

    def get_container_stats(self, container_name: str) -> dict[str, Any]:
        """Get container resource statistics."""
        container = self.get_container_by_name(container_name)
        if container:
            try:
                stats = container.stats(stream=False)
                return {
                    "memory_usage": stats.get("memory_stats", {}),
                    "cpu_usage": stats.get("cpu_stats", {}),
                    "network": stats.get("networks", {}),
                    "block_io": stats.get("blkio_stats", {}),
                }
            except Exception:
                pass
        return {}

    def restart_container(self, container_name: str) -> bool:
        """Restart a container."""
        container = self.get_container_by_name(container_name)
        if container:
            try:
                container.restart()
                return True
            except Exception:
                pass
        return False

    def stop_container(self, container_name: str) -> bool:
        """Stop a container."""
        container = self.get_container_by_name(container_name)
        if container:
            try:
                container.stop()
                return True
            except Exception:
                pass
        return False

    def start_container(self, container_name: str) -> bool:
        """Start a container."""
        container = self.get_container_by_name(container_name)
        if container:
            try:
                container.start()
                return True
            except Exception:
                pass
        return False

    def get_network_info(self, network_name: str) -> dict[str, Any]:
        """Get network information."""
        try:
            network = self.docker_client.networks.get(network_name)
            return {
                "name": network.name,
                "driver": network.attrs.get("Driver", ""),
                "containers": list(network.attrs.get("Containers", {}).keys()),
                "scope": network.attrs.get("Scope", ""),
                "ipam": network.attrs.get("IPAM", {}),
            }
        except docker.errors.NotFound:
            return {}

    def cleanup_test_containers(self, prefix: str = "test_"):
        """Clean up test containers."""
        containers = self.docker_client.containers.list(all=True)
        cleaned = 0

        for container in containers:
            if container.name.startswith(prefix):
                try:
                    container.remove(force=True)
                    cleaned += 1
                except Exception:
                    pass

        return cleaned

    def get_compose_services_status(
        self, compose_file: str = "docker-compose.dev.yml"
    ) -> dict[str, str]:
        """Get Docker Compose services status."""

        import yaml

        try:
            # Parse compose file to get service names
            with open(compose_file) as f:
                compose_config = yaml.safe_load(f)

            services = compose_config.get("services", {})
            service_status = {}

            for service_name in services.keys():
                # Try to find container for this service
                containers = self.docker_client.containers.list(
                    filters={"label": f"com.docker.compose.service={service_name}"}
                )

                if containers:
                    service_status[service_name] = containers[0].status
                else:
                    service_status[service_name] = "not_found"

            return service_status

        except Exception:
            return {}

    async def wait_for_all_services(
        self, services: dict[str, dict[str, Any]], timeout: int = 120
    ) -> dict[str, bool]:
        """Wait for all services to become healthy."""
        results = {}
        start_time = time.time()

        for service_name, config in services.items():
            host = config.get("host", "localhost")
            port = config.get("port")
            service_timeout = config.get("timeout", 30)

            if port:
                try:
                    # Wait for service with timeout
                    service_start = time.time()
                    while (
                        time.time() - service_start < service_timeout
                        and time.time() - start_time < timeout
                    ):
                        if await self.check_service_connectivity(host, port, 5):
                            results[service_name] = True
                            break
                        await asyncio.sleep(2)
                    else:
                        results[service_name] = False
                except Exception:
                    results[service_name] = False
            else:
                results[service_name] = False

        return results

    def close(self):
        """Close Docker client."""
        if self.docker_client:
            self.docker_client.close()


class ServiceMonitor:
    """Monitor services for testing."""

    def __init__(self):
        """Initialize service monitor."""
        self.monitored_services = {}
        self.monitoring = False

    async def start_monitoring(self, services: dict[str, dict[str, Any]], interval: int = 30):
        """Start monitoring services."""
        self.monitored_services = services
        self.monitoring = True

        while self.monitoring:
            for service_name, config in services.items():
                try:
                    host = config.get("host", "localhost")
                    port = config.get("port")

                    if port:
                        # Check service health
                        healthy = await self._check_service_health(host, port)

                        # Store status
                        if service_name not in self.monitored_services:
                            self.monitored_services[service_name] = {}

                        self.monitored_services[service_name]["last_check"] = time.time()
                        self.monitored_services[service_name]["healthy"] = healthy

                except Exception as e:
                    if service_name not in self.monitored_services:
                        self.monitored_services[service_name] = {}

                    self.monitored_services[service_name]["last_check"] = time.time()
                    self.monitored_services[service_name]["healthy"] = False
                    self.monitored_services[service_name]["error"] = str(e)

            await asyncio.sleep(interval)

    async def _check_service_health(self, host: str, port: int) -> bool:
        """Check individual service health."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"http://{host}:{port}/health") as response:
                    return response.status == 200
        except Exception:
            return False

    def stop_monitoring(self):
        """Stop monitoring services."""
        self.monitoring = False

    def get_service_status(self, service_name: str) -> dict[str, Any]:
        """Get status of specific service."""
        return self.monitored_services.get(service_name, {})

    def get_all_statuses(self) -> dict[str, dict[str, Any]]:
        """Get all service statuses."""
        return self.monitored_services.copy()

    def get_unhealthy_services(self) -> list[str]:
        """Get list of unhealthy services."""
        unhealthy = []
        for service_name, status in self.monitored_services.items():
            if not status.get("healthy", False):
                unhealthy.append(service_name)
        return unhealthy


class IntegrationHealthChecker:
    """Health checker for integration testing."""

    def __init__(self):
        """Initialize health checker."""
        self.health_checks = {}

    async def check_all_services(self) -> dict[str, bool]:
        """Check health of all services."""
        results = {}

        # Database check
        results["database"] = await self._check_database()

        # Redis check
        results["redis"] = await self._check_redis()

        # API services check
        api_services = [
            ("fastapi", "localhost", 8009),
            ("mcp-server", "localhost", 9877),
            ("agent-coordinator", "localhost", 8888),
            ("flask-bridge", "localhost", 5001),
            ("dashboard", "localhost", 5179),
        ]

        for service_name, host, port in api_services:
            results[service_name] = await self._check_http_service(host, port)

        return results

    async def _check_database(self) -> bool:
        """Check database health."""
        try:
            conn = await asyncpg.connect(
                host="localhost",
                port=5434,
                database="educational_platform_dev",
                user="eduplatform",
                password="eduplatform2024",
                timeout=10,
            )
            result = await conn.fetchval("SELECT 1;")
            await conn.close()
            return result == 1
        except Exception:
            return False

    async def _check_redis(self) -> bool:
        """Check Redis health."""
        try:
            redis_client = await redis.from_url("redis://localhost:6381/0", timeout=10)
            result = await redis_client.ping()
            await redis_client.close()
            return result
        except Exception:
            return False

    async def _check_http_service(self, host: str, port: int) -> bool:
        """Check HTTP service health."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                # Try health endpoint first
                try:
                    async with session.get(f"http://{host}:{port}/health") as response:
                        return response.status == 200
                except Exception:
                    pass

                # Try root endpoint as fallback
                try:
                    async with session.get(f"http://{host}:{port}/") as response:
                        return response.status == 200
                except Exception:
                    pass

            return False
        except Exception:
            return False

    def generate_health_report(self, results: dict[str, bool]) -> str:
        """Generate health report."""
        healthy_count = sum(1 for status in results.values() if status)
        total_count = len(results)

        report = f"Health Check Report\n"
        report += f"==================\n"
        report += f"Overall: {healthy_count}/{total_count} services healthy\n\n"

        for service_name, healthy in results.items():
            status = "✓ HEALTHY" if healthy else "✗ UNHEALTHY"
            report += f"{service_name:<20} {status}\n"

        return report

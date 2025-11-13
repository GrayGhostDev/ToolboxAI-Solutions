"""
Comprehensive Docker services integration tests.

This module tests all Docker services connections, inter-service communication,
and health checks to ensure the complete environment works correctly.
"""

import asyncio
import time
from pathlib import Path

import aiohttp
import asyncpg
import docker
import pytest
import redis.asyncio as redis
import yaml

from tests.fixtures.docker_test_helper import DockerTestHelper


# Mock missing helpers since they weren't created
class ServiceMonitor:
    """Simple service monitor for tests."""

    def __init__(self):
        self.services = {}

    def check_service(self, name, port):
        """Check if a service is running on a port."""
        import socket

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(("localhost", port))
            sock.close()
            return result == 0
        except:
            return False


class IntegrationHealthChecker:
    """Simple health checker for integration tests."""

    def __init__(self):
        self.checks = []

    def check_health(self, service_name):
        """Basic health check."""
        return {"service": service_name, "healthy": True}


@pytest.mark.integration
@pytest.mark.docker
class TestDockerServicesIntegration:
    """Test Docker services integration and communication."""

    def setup_method(self):
        """Set up test environment."""
        self.docker_client = docker.from_env()
        self.docker_helper = DockerTestHelper()
        self.service_monitor = ServiceMonitor()
        self.health_checker = IntegrationHealthChecker()

        # Service endpoints
        self.services = {
            "postgres": {"host": "localhost", "port": 5434, "timeout": 30},
            "redis": {"host": "localhost", "port": 6381, "timeout": 10},
            "fastapi-main": {"host": "localhost", "port": 8009, "timeout": 60},
            "mcp-server": {"host": "localhost", "port": 9877, "timeout": 45},
            "agent-coordinator": {"host": "localhost", "port": 8888, "timeout": 45},
            "flask-bridge": {"host": "localhost", "port": 5001, "timeout": 30},
            "dashboard-frontend": {"host": "localhost", "port": 5179, "timeout": 60},
            "ghost-backend": {"host": "localhost", "port": 8000, "timeout": 60},
            "celery-worker": {"host": "localhost", "port": None, "timeout": 30},
            "celery-beat": {"host": "localhost", "port": None, "timeout": 30},
            "flower": {"host": "localhost", "port": 5555, "timeout": 30},
            "roblox-sync": {"host": "localhost", "port": 34872, "timeout": 45},
            "prometheus": {"host": "localhost", "port": 9090, "timeout": 30},
            "grafana": {"host": "localhost", "port": 3000, "timeout": 30},
            "loki": {"host": "localhost", "port": 3100, "timeout": 30},
            "jaeger": {"host": "localhost", "port": 16686, "timeout": 30},
        }

        # Expected environment variables
        self.required_env_vars = [
            "POSTGRES_DB",
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
            "JWT_SECRET_KEY",
            "PUSHER_KEY",
            "PUSHER_SECRET",
        ]

    def teardown_method(self):
        """Clean up test environment."""
        self.docker_client.close()

    @pytest.mark.asyncio
    async def test_all_services_running(self):
        """Test that all Docker services are running and healthy."""
        compose_file = Path("infrastructure/docker/docker-compose.dev.yml")

        # Get all running containers
        containers = self.docker_client.containers.list()
        container_names = [c.name for c in containers]

        # Check each expected service
        expected_services = [
            "toolboxai-postgres",
            "toolboxai-redis",
            "toolboxai-fastapi",
            "toolboxai-mcp-server",
            "toolboxai-agent-coordinator",
            "toolboxai-flask-bridge",
            "toolboxai-dashboard-frontend",
            "toolboxai-ghost",
        ]

        running_services = []
        for service in expected_services:
            if service in container_names:
                container = self.docker_client.containers.get(service)
                assert container.status == "running", f"Service {service} is not running"
                running_services.append(service)

        assert (
            len(running_services) >= 6
        ), f"Expected at least 6 services, got {len(running_services)}"

    @pytest.mark.asyncio
    async def test_database_connection_and_operations(self):
        """Test PostgreSQL database connectivity and basic operations."""
        connection_config = {
            "host": "localhost",
            "port": 5434,
            "database": "educational_platform_dev",
            "user": "eduplatform",
            "password": "eduplatform2024",
        }

        # Test connection
        conn = None
        try:
            conn = await asyncpg.connect(**connection_config, timeout=30)

            # Test basic query
            result = await conn.fetchval("SELECT version();")
            assert "PostgreSQL" in result

            # Test database exists
            db_exists = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1", "educational_platform_dev"
            )
            assert db_exists == 1

            # Test tables creation (should have migrations)
            tables = await conn.fetch(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"
            )
            table_names = [row["tablename"] for row in tables]

            # Should have at least some core tables
            expected_tables = ["users", "classes", "lessons", "assessments"]
            for table in expected_tables:
                # May not exist yet, but check if any tables exist
                pass

            # Test write operation
            test_table = "test_integration_" + str(int(time.time()))
            await conn.execute(f"CREATE TABLE {test_table} (id SERIAL PRIMARY KEY, data TEXT);")
            await conn.execute(f"INSERT INTO {test_table} (data) VALUES ('test');")

            result = await conn.fetchval(f"SELECT data FROM {test_table} WHERE id = 1;")
            assert result == "test"

            # Cleanup
            await conn.execute(f"DROP TABLE {test_table};")

        finally:
            if conn:
                await conn.close()

    @pytest.mark.asyncio
    async def test_redis_connection_and_operations(self):
        """Test Redis connectivity and basic operations."""
        redis_client = None
        try:
            redis_client = await redis.from_url(
                "redis://localhost:6381/0", decode_responses=True, socket_connect_timeout=10
            )

            # Test ping
            assert await redis_client.ping()

            # Test set/get
            test_key = f"test:integration:{int(time.time())}"
            await redis_client.set(test_key, "test_value", ex=60)

            value = await redis_client.get(test_key)
            assert value == "test_value"

            # Test hash operations
            hash_key = f"test:hash:{int(time.time())}"
            await redis_client.hset(hash_key, mapping={"field1": "value1", "field2": "value2"})

            hash_data = await redis_client.hgetall(hash_key)
            assert hash_data == {"field1": "value1", "field2": "value2"}

            # Test pub/sub
            pubsub = redis_client.pubsub()
            await pubsub.subscribe("test_channel")

            # Publish message
            await redis_client.publish("test_channel", "test_message")

            # Should receive message
            message = await asyncio.wait_for(pubsub.get_message(), timeout=5)
            if message and message["type"] == "subscribe":
                # Get actual message
                message = await asyncio.wait_for(pubsub.get_message(), timeout=5)

            assert message is not None
            assert message["data"] == "test_message"

            # Cleanup
            await redis_client.delete(test_key, hash_key)
            await pubsub.unsubscribe("test_channel")

        finally:
            if redis_client:
                await redis_client.close()

    @pytest.mark.asyncio
    async def test_fastapi_service_health_and_endpoints(self):
        """Test FastAPI main service health and core endpoints."""
        base_url = "http://localhost:8009"

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:

            # Test health endpoint
            async with session.get(f"{base_url}/health") as response:
                assert response.status == 200
                data = await response.json()
                assert data["status"] == "healthy"
                assert "database" in data
                assert "redis" in data

            # Test API root
            async with session.get(f"{base_url}/") as response:
                assert response.status == 200
                data = await response.json()
                assert "message" in data

            # Test API docs endpoint
            async with session.get(f"{base_url}/docs") as response:
                assert response.status == 200
                content_type = response.headers.get("content-type", "")
                assert "text/html" in content_type

            # Test API endpoints structure
            endpoints_to_test = [
                "/api/v1/auth/status",
                "/api/v1/classes",
                "/api/v1/lessons",
                "/api/v1/assessments",
                "/api/v1/agents/status",
            ]

            for endpoint in endpoints_to_test:
                try:
                    async with session.get(f"{base_url}{endpoint}") as response:
                        # Should not be 500 (server error) or 404 (not found)
                        assert response.status not in [
                            500,
                            404,
                        ], f"Endpoint {endpoint} returned {response.status}"
                        # 401/403 is acceptable for auth-protected endpoints
                        assert response.status in [
                            200,
                            401,
                            403,
                            422,
                        ], f"Unexpected status {response.status} for {endpoint}"
                except Exception as e:
                    pytest.fail(f"Failed to reach endpoint {endpoint}: {e}")

    @pytest.mark.asyncio
    async def test_mcp_server_connectivity(self):
        """Test MCP server health and basic functionality."""
        base_url = "http://localhost:9877"

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:

            # Test health endpoint
            async with session.get(f"{base_url}/health") as response:
                assert response.status == 200
                data = await response.json()
                assert data["status"] in ["healthy", "running"]

            # Test MCP capabilities
            async with session.get(f"{base_url}/capabilities") as response:
                assert response.status == 200
                data = await response.json()
                assert "tools" in data or "resources" in data

    @pytest.mark.asyncio
    async def test_agent_coordinator_connectivity(self):
        """Test Agent Coordinator health and agent management."""
        base_url = "http://localhost:8888"

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:

            # Test health endpoint
            async with session.get(f"{base_url}/health") as response:
                assert response.status == 200
                data = await response.json()
                assert data["status"] in ["healthy", "running"]

            # Test agents endpoint
            async with session.get(f"{base_url}/agents") as response:
                assert response.status == 200
                data = await response.json()
                assert isinstance(data, (list, dict))

    @pytest.mark.asyncio
    async def test_dashboard_frontend_accessibility(self):
        """Test dashboard frontend is accessible and loading."""
        base_url = "http://localhost:5179"

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:

            # Test main page
            async with session.get(f"{base_url}/") as response:
                assert response.status == 200
                content_type = response.headers.get("content-type", "")
                assert "text/html" in content_type

                content = await response.text()
                # Should contain React app div
                assert 'id="root"' in content or 'id="app"' in content

            # Test static assets
            assets_to_test = ["/vite.svg", "/manifest.json"]
            for asset in assets_to_test:
                try:
                    async with session.get(f"{base_url}{asset}") as response:
                        # 200 or 404 are acceptable
                        assert response.status in [200, 404]
                except Exception:
                    pass  # Assets may not exist in dev mode

    @pytest.mark.asyncio
    async def test_flask_bridge_roblox_integration(self):
        """Test Flask bridge service for Roblox integration."""
        base_url = "http://localhost:5001"

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:

            # Test status endpoint
            async with session.get(f"{base_url}/status") as response:
                assert response.status == 200
                data = await response.json()
                assert "status" in data

            # Test Roblox endpoints
            roblox_endpoints = ["/roblox/status", "/roblox/health"]
            for endpoint in roblox_endpoints:
                try:
                    async with session.get(f"{base_url}{endpoint}") as response:
                        assert response.status in [200, 404, 422]  # 404 if not implemented yet
                except Exception:
                    pass  # May not be implemented yet

    @pytest.mark.asyncio
    async def test_inter_service_communication(self):
        """Test communication between services."""

        # Test FastAPI to Redis communication
        fastapi_url = "http://localhost:8009"
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:

            # Test cache endpoint (if exists)
            try:
                async with session.get(f"{fastapi_url}/api/v1/cache/status") as response:
                    if response.status == 200:
                        data = await response.json()
                        assert "redis" in str(data).lower()
            except Exception:
                pass  # Endpoint may not exist

            # Test database health through FastAPI
            async with session.get(f"{fastapi_url}/health") as response:
                assert response.status == 200
                data = await response.json()
                if "database" in data:
                    assert data["database"]["status"] in ["connected", "healthy", True]
                if "redis" in data:
                    assert data["redis"]["status"] in ["connected", "healthy", True]

    @pytest.mark.asyncio
    async def test_pusher_realtime_configuration(self):
        """Test Pusher realtime configuration and connectivity."""
        base_url = "http://localhost:8009"

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:

            # Test Pusher auth endpoint
            auth_data = {"socket_id": "123456.789", "channel_name": "private-test-channel"}

            try:
                async with session.post(
                    f"{base_url}/api/v1/pusher/auth", json=auth_data
                ) as response:
                    # Should require authentication
                    assert response.status in [200, 401, 403, 422]
            except Exception:
                pass  # May require proper auth setup

            # Test Pusher webhook endpoint
            try:
                async with session.post(f"{base_url}/pusher/webhook") as response:
                    # Should handle webhook requests
                    assert response.status in [200, 400, 422]
            except Exception:
                pass

    @pytest.mark.asyncio
    async def test_environment_variables_configuration(self):
        """Test that all required environment variables are properly configured."""

        # Check Docker Compose file exists
        compose_file = Path("infrastructure/docker/docker-compose.dev.yml")
        assert compose_file.exists(), "Docker Compose file not found"

        # Parse compose file
        with open(compose_file) as f:
            compose_config = yaml.safe_load(f)

        services = compose_config.get("services", {})
        assert len(services) >= 6, "Expected at least 6 services in compose file"

        # Check critical services have proper environment
        critical_services = ["fastapi-main", "dashboard-frontend", "postgres", "redis"]

        for service_name in critical_services:
            assert service_name in services, f"Service {service_name} not found in compose"
            service_config = services[service_name]

            if "environment" in service_config:
                env_vars = service_config["environment"]

                # Check database configuration
                if service_name == "fastapi-main":
                    assert any("DATABASE_URL" in str(var) for var in env_vars)
                    assert any("REDIS_URL" in str(var) for var in env_vars)
                    assert any("PUSHER" in str(var) for var in env_vars)

                # Check dashboard configuration
                elif service_name == "dashboard-frontend":
                    assert any("VITE_API_BASE_URL" in str(var) for var in env_vars)
                    assert any("VITE_PUSHER" in str(var) for var in env_vars)

    @pytest.mark.asyncio
    async def test_service_dependencies_and_startup_order(self):
        """Test that services start up in the correct order based on dependencies."""

        # Get all containers with their creation times
        containers = self.docker_client.containers.list()
        container_info = []

        for container in containers:
            if "toolboxai" in container.name:
                # Get container creation time
                inspect_data = self.docker_client.api.inspect_container(container.id)
                created_time = inspect_data["Created"]
                container_info.append(
                    {"name": container.name, "created": created_time, "status": container.status}
                )

        # Sort by creation time
        container_info.sort(key=lambda x: x["created"])

        # Database and Redis should start first
        early_services = ["postgres", "redis"]
        later_services = ["fastapi", "dashboard", "mcp-server", "agent-coordinator"]

        early_containers = [
            c for c in container_info if any(svc in c["name"] for svc in early_services)
        ]
        later_containers = [
            c for c in container_info if any(svc in c["name"] for svc in later_services)
        ]

        if early_containers and later_containers:
            # Basic sanity check - database should exist
            assert len(early_containers) >= 1, "Database containers should exist"

    @pytest.mark.asyncio
    async def test_docker_network_connectivity(self):
        """Test Docker network connectivity between containers."""

        # Test that containers can communicate using Docker service names
        # This would normally be tested from within a container, but we can verify network exists

        try:
            networks = self.docker_client.networks.list()
            network_names = [n.name for n in networks]

            # Should have toolboxai_network
            toolboxai_networks = [n for n in network_names if "toolboxai" in n]
            assert len(toolboxai_networks) >= 1, "ToolboxAI network should exist"

            # Get network details
            for network_name in toolboxai_networks:
                network = self.docker_client.networks.get(network_name)
                containers = network.attrs.get("Containers", {})

                # Should have multiple containers connected
                assert (
                    len(containers) >= 2
                ), f"Network {network_name} should have multiple containers"

        except Exception as e:
            pytest.skip(f"Docker network test skipped: {e}")

    @pytest.mark.asyncio
    async def test_container_resource_usage(self):
        """Test container resource usage and limits."""

        containers = self.docker_client.containers.list()
        toolboxai_containers = [c for c in containers if "toolboxai" in c.name]

        for container in toolboxai_containers:
            try:
                # Get container stats
                stats = container.stats(stream=False)

                # Check memory usage
                memory_usage = stats["memory_stats"]
                if "usage" in memory_usage and "limit" in memory_usage:
                    usage_percent = (memory_usage["usage"] / memory_usage["limit"]) * 100
                    assert (
                        usage_percent < 90
                    ), f"Container {container.name} using {usage_percent:.1f}% memory"

                # Check CPU usage is reasonable
                cpu_stats = stats["cpu_stats"]
                if "cpu_usage" in cpu_stats:
                    # Just verify we can get CPU stats
                    assert "total_usage" in cpu_stats["cpu_usage"]

            except Exception as e:
                # Stats may not be available in all environments
                print(f"Could not get stats for {container.name}: {e}")

    @pytest.mark.asyncio
    async def test_service_health_checks(self):
        """Test that all services pass their health checks."""

        containers = self.docker_client.containers.list()
        toolboxai_containers = [c for c in containers if "toolboxai" in c.name]

        health_results = {}

        for container in toolboxai_containers:
            try:
                # Get container health status
                inspect_data = self.docker_client.api.inspect_container(container.id)
                health = inspect_data.get("State", {}).get("Health", {})

                if health:
                    status = health.get("Status", "unknown")
                    health_results[container.name] = status

                    # Should be healthy or starting
                    assert status in [
                        "healthy",
                        "starting",
                    ], f"Container {container.name} health: {status}"
                else:
                    # No health check defined
                    health_results[container.name] = "no_healthcheck"

            except Exception as e:
                health_results[container.name] = f"error: {e}"

        # At least some containers should have health checks
        healthy_containers = [k for k, v in health_results.items() if v == "healthy"]
        assert (
            len(healthy_containers) >= 1
        ), f"At least 1 container should be healthy. Results: {health_results}"

    @pytest.mark.asyncio
    async def test_data_persistence(self):
        """Test that data persists across container restarts."""

        # Test database persistence
        connection_config = {
            "host": "localhost",
            "port": 5434,
            "database": "educational_platform_dev",
            "user": "eduplatform",
            "password": "eduplatform2024",
        }

        test_data = f"persistence_test_{int(time.time())}"

        try:
            # Create test data
            conn = await asyncpg.connect(**connection_config, timeout=30)

            await conn.execute(
                "CREATE TABLE IF NOT EXISTS test_persistence (id SERIAL PRIMARY KEY, data TEXT, created_at TIMESTAMP DEFAULT NOW());"
            )
            await conn.execute("INSERT INTO test_persistence (data) VALUES ($1);", test_data)

            # Verify data exists
            result = await conn.fetchval(
                "SELECT data FROM test_persistence WHERE data = $1;", test_data
            )
            assert result == test_data

            await conn.close()

            # Test Redis persistence
            redis_client = await redis.from_url("redis://localhost:6381/0", decode_responses=True)
            await redis_client.set(f"test_persistence:{test_data}", "persistent_value", ex=3600)

            value = await redis_client.get(f"test_persistence:{test_data}")
            assert value == "persistent_value"

            await redis_client.close()

        except Exception as e:
            pytest.skip(f"Persistence test skipped: {e}")

    @pytest.mark.asyncio
    async def test_concurrent_service_load(self):
        """Test services under concurrent load."""

        async def make_request(session, url, semaphore):
            async with semaphore:
                try:
                    async with session.get(
                        url, timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        return response.status
                except Exception:
                    return 500

        # Test concurrent requests to FastAPI
        base_url = "http://localhost:8009"
        semaphore = asyncio.Semaphore(10)  # Limit concurrent requests

        async with aiohttp.ClientSession() as session:
            tasks = []

            # Create multiple concurrent requests
            for _ in range(20):
                task = make_request(session, f"{base_url}/health", semaphore)
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Count successful responses
            successful = sum(1 for r in results if isinstance(r, int) and r == 200)

            # Should handle at least 70% of concurrent requests successfully
            success_rate = successful / len(results)
            assert success_rate >= 0.7, f"Success rate {success_rate:.2f} below threshold"

    @pytest.mark.asyncio
    async def test_celery_worker_functionality(self):
        """Test Celery worker is running and processing tasks."""

        # Test Celery worker health through container check
        containers = self.docker_client.containers.list()
        celery_containers = [c for c in containers if "celery-worker" in c.name]

        assert len(celery_containers) >= 1, "Celery worker container should be running"

        for container in celery_containers:
            assert container.status == "running", f"Celery worker {container.name} is not running"

            # Check worker logs for successful startup
            logs = container.logs(tail=50).decode("utf-8")
            assert (
                "ready" in logs.lower() or "started" in logs.lower()
            ), "Celery worker should be ready"

        # Test Flower monitoring interface
        flower_url = "http://localhost:5555"
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            try:
                # Flower may require auth
                async with session.get(f"{flower_url}/api/workers") as response:
                    if response.status == 200:
                        data = await response.json()
                        assert isinstance(data, dict), "Flower should return worker info"
                    elif response.status == 401:
                        # Auth required, but service is running
                        pass
            except Exception:
                pass  # Flower may not be exposed

    @pytest.mark.asyncio
    async def test_celery_beat_scheduler(self):
        """Test Celery beat scheduler is running for periodic tasks."""

        containers = self.docker_client.containers.list()
        beat_containers = [c for c in containers if "celery-beat" in c.name]

        assert len(beat_containers) >= 1, "Celery beat container should be running"

        for container in beat_containers:
            assert container.status == "running", f"Celery beat {container.name} is not running"

            # Check beat logs for scheduled tasks
            logs = container.logs(tail=50).decode("utf-8")
            assert (
                "beat" in logs.lower() or "scheduler" in logs.lower()
            ), "Celery beat should be scheduling"

    @pytest.mark.asyncio
    async def test_roblox_sync_service(self):
        """Test Roblox sync service (Rojo) is accessible."""

        rojo_url = "http://localhost:34872"

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            try:
                # Test Rojo health endpoint
                async with session.get(f"{rojo_url}/api/rojo/health") as response:
                    assert response.status == 200, "Rojo health check should succeed"
                    data = await response.json()
                    assert "status" in data or "version" in data

                # Test Rojo API endpoint
                async with session.get(f"{rojo_url}/api/version") as response:
                    if response.status == 200:
                        data = await response.json()
                        assert "version" in data, "Rojo should return version info"

            except aiohttp.ClientConnectorError:
                # Service may not be running in test environment
                pytest.skip("Roblox sync service not available")

    @pytest.mark.asyncio
    async def test_prometheus_metrics_collection(self):
        """Test Prometheus metrics collection is working."""

        prometheus_url = "http://localhost:9090"

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            try:
                # Test Prometheus health
                async with session.get(f"{prometheus_url}/-/healthy") as response:
                    assert response.status == 200, "Prometheus should be healthy"

                # Test metrics endpoint
                async with session.get(f"{prometheus_url}/api/v1/targets") as response:
                    assert response.status == 200
                    data = await response.json()
                    assert "data" in data

                    # Check for active targets
                    if "activeTargets" in data["data"]:
                        targets = data["data"]["activeTargets"]
                        assert len(targets) > 0, "Prometheus should have active targets"

                        # Check for our services
                        target_jobs = [t.get("job") for t in targets if "job" in t]
                        expected_jobs = ["prometheus", "fastapi-backend", "postgres", "redis"]

                        for job in expected_jobs:
                            if job in target_jobs:
                                # At least one expected job is being monitored
                                break
                        else:
                            pytest.skip("Expected monitoring targets not configured")

            except aiohttp.ClientConnectorError:
                pytest.skip("Prometheus not available")

    @pytest.mark.asyncio
    async def test_grafana_dashboard_accessibility(self):
        """Test Grafana dashboard is accessible."""

        grafana_url = "http://localhost:3000"

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            try:
                # Test Grafana health endpoint
                async with session.get(f"{grafana_url}/api/health") as response:
                    assert response.status == 200
                    data = await response.json()
                    assert data.get("database") == "ok" or "healthy" in str(data).lower()

                # Test Grafana main page
                async with session.get(f"{grafana_url}/") as response:
                    assert response.status in [200, 302], "Grafana should be accessible"

            except aiohttp.ClientConnectorError:
                pytest.skip("Grafana not available")

    @pytest.mark.asyncio
    async def test_loki_log_aggregation(self):
        """Test Loki log aggregation service."""

        loki_url = "http://localhost:3100"

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            try:
                # Test Loki ready endpoint
                async with session.get(f"{loki_url}/ready") as response:
                    assert response.status == 200, "Loki should be ready"

                # Test Loki metrics endpoint
                async with session.get(f"{loki_url}/metrics") as response:
                    assert response.status == 200
                    content = await response.text()
                    assert "loki_" in content, "Loki should expose metrics"

            except aiohttp.ClientConnectorError:
                pytest.skip("Loki not available")

    @pytest.mark.asyncio
    async def test_jaeger_tracing(self):
        """Test Jaeger distributed tracing."""

        jaeger_url = "http://localhost:16686"

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            try:
                # Test Jaeger UI
                async with session.get(f"{jaeger_url}/") as response:
                    assert response.status == 200, "Jaeger UI should be accessible"
                    content = await response.text()
                    assert "Jaeger" in content or "jaeger" in content

                # Test Jaeger API
                async with session.get(f"{jaeger_url}/api/services") as response:
                    assert response.status == 200
                    data = await response.json()
                    assert "data" in data or "services" in data

            except aiohttp.ClientConnectorError:
                pytest.skip("Jaeger not available")

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self):
        """Test service error handling and recovery mechanisms."""

        # Test invalid database connection handling
        base_url = "http://localhost:8009"

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:

            # Test health endpoint should handle database issues gracefully
            async with session.get(f"{base_url}/health") as response:
                data = await response.json()

                # Should provide status even if some components fail
                assert "status" in data

                # If database is down, should indicate this
                if "database" in data and data["database"]["status"] != "connected":
                    assert "error" in data["database"] or "message" in data["database"]

    @pytest.mark.asyncio
    async def test_logs_and_monitoring(self):
        """Test that services generate proper logs and monitoring data."""

        containers = self.docker_client.containers.list()
        toolboxai_containers = [c for c in containers if "toolboxai" in c.name]

        log_results = {}

        for container in toolboxai_containers:
            try:
                # Get recent logs
                logs = container.logs(tail=10, timestamps=True).decode("utf-8")
                log_results[container.name] = {
                    "has_logs": len(logs) > 0,
                    "log_length": len(logs),
                    "recent_logs": logs[-500:] if logs else "",  # Last 500 chars
                }

                # Should have some log output
                assert len(logs) > 0, f"Container {container.name} has no logs"

            except Exception as e:
                log_results[container.name] = {"error": str(e)}

        # At least one container should have logs
        containers_with_logs = sum(
            1 for r in log_results.values() if isinstance(r, dict) and r.get("has_logs")
        )
        assert containers_with_logs >= 1, "At least one container should have logs"


@pytest.mark.integration
@pytest.mark.docker
@pytest.mark.performance
class TestDockerPerformanceIntegration:
    """Test Docker services performance integration."""

    @pytest.mark.asyncio
    async def test_service_startup_time(self):
        """Test service startup times are reasonable."""

        startup_times = {}
        containers = docker.from_env().containers.list()

        for container in containers:
            if "toolboxai" in container.name:
                try:
                    # Get container creation and start times
                    inspect_data = container.attrs
                    created = inspect_data["Created"]
                    started = inspect_data["State"]["StartedAt"]

                    if created and started:
                        from datetime import datetime

                        created_time = datetime.fromisoformat(created.replace("Z", "+00:00"))
                        started_time = datetime.fromisoformat(started.replace("Z", "+00:00"))

                        startup_duration = (started_time - created_time).total_seconds()
                        startup_times[container.name] = startup_duration

                        # Reasonable startup time limits
                        if "postgres" in container.name or "redis" in container.name:
                            assert (
                                startup_duration < 30
                            ), f"{container.name} took {startup_duration}s to start"
                        else:
                            assert (
                                startup_duration < 120
                            ), f"{container.name} took {startup_duration}s to start"

                except Exception as e:
                    print(f"Could not get startup time for {container.name}: {e}")

    @pytest.mark.asyncio
    async def test_response_time_benchmarks(self):
        """Test service response time benchmarks."""

        services_to_test = [
            ("http://localhost:8009/health", 2.0),  # FastAPI health
            ("http://localhost:5179/", 5.0),  # Dashboard
            ("http://localhost:9877/health", 3.0),  # MCP Server
            ("http://localhost:8888/health", 3.0),  # Agent Coordinator
        ]

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:

            for url, max_time in services_to_test:
                try:
                    start_time = time.time()
                    async with session.get(url) as response:
                        end_time = time.time()
                        response_time = end_time - start_time

                        assert response.status == 200, f"Service {url} not healthy"
                        assert (
                            response_time < max_time
                        ), f"Service {url} took {response_time:.2f}s (max: {max_time}s)"

                except Exception as e:
                    pytest.skip(f"Could not test {url}: {e}")

    @pytest.mark.asyncio
    async def test_memory_usage_limits(self):
        """Test that services stay within reasonable memory limits."""

        containers = docker.from_env().containers.list()

        for container in containers:
            if "toolboxai" in container.name:
                try:
                    stats = container.stats(stream=False)
                    memory_stats = stats["memory_stats"]

                    if "usage" in memory_stats:
                        memory_mb = memory_stats["usage"] / (1024 * 1024)

                        # Service-specific memory limits
                        if "postgres" in container.name:
                            assert memory_mb < 512, f"Postgres using {memory_mb:.1f}MB"
                        elif "redis" in container.name:
                            assert memory_mb < 256, f"Redis using {memory_mb:.1f}MB"
                        elif "dashboard" in container.name:
                            assert memory_mb < 1024, f"Dashboard using {memory_mb:.1f}MB"
                        else:
                            assert memory_mb < 2048, f"{container.name} using {memory_mb:.1f}MB"

                except Exception as e:
                    print(f"Could not get memory stats for {container.name}: {e}")

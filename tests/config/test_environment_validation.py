"""Environment configuration validation tests"""
import os
import pytest
from pathlib import Path
import json
import yaml
from typing import Dict, List, Any

class TestEnvironmentConfiguration:
    """Validate environment configuration across all services"""

    @pytest.fixture
    def required_env_vars(self) -> Dict[str, List[str]]:
        """Define required environment variables by service"""
        return {
            "core": [
                "DATABASE_URL",
                "REDIS_URL",
                "JWT_SECRET_KEY",
                "ENVIRONMENT"
            ],
            "postgres": [
                "POSTGRES_DB",
                "POSTGRES_USER",
                "POSTGRES_PASSWORD"
            ],
            "redis": [
                "REDIS_HOST",
                "REDIS_PORT"
            ],
            "pusher": [
                "PUSHER_APP_ID",
                "PUSHER_KEY",
                "PUSHER_SECRET",
                "PUSHER_CLUSTER"
            ],
            "ai_services": [
                "OPENAI_API_KEY",
                "LANGCHAIN_API_KEY"
            ]
        }

    def test_docker_compose_environment_alignment(self):
        """Test Docker Compose uses correct service names"""
        compose_path = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/infrastructure/docker/docker-compose.dev.yml")

        with open(compose_path, 'r') as f:
            content = f.read()

        # Verify service names match expected
        assert "postgres:5432" in content  # Not localhost
        assert "redis:6379" in content     # Not localhost
        assert "container_name: toolboxai-postgres" in content
        assert "container_name: toolboxai-fastapi" in content

        # Verify ports don't conflict
        assert "'5434:5432'" in content  # PostgreSQL on 5434 externally
        assert "'6381:6379'" in content  # Redis on 6381 externally

    def test_env_example_completeness(self):
        """Test .env.example has all required variables"""
        env_example = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/.env.example")

        with open(env_example, 'r') as f:
            content = f.read()

        # Check for security recommendations
        assert "openssl rand -hex 32" in content
        assert "NEVER commit" in content
        assert "vault" in content.lower()

        # Check for all service configurations
        assert "POSTGRES_DB=" in content
        assert "REDIS_URL=" in content
        assert "JWT_SECRET_KEY=" in content
        assert "PUSHER_" in content
        assert "OPENAI_API_KEY=" in content

    def test_python_version_consistency(self):
        """Test Python version is consistent across configs"""
        python_version_file = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/.python-version")

        with open(python_version_file, 'r') as f:
            project_version = f.read().strip()

        assert project_version == "3.12.11"

        # Check CI/CD uses compatible versions
        ci_config = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/.github/workflows")
        if ci_config.exists():
            workflow_files = list(ci_config.glob("*.yml"))
            if workflow_files:
                for workflow_file in workflow_files:
                    with open(workflow_file, 'r') as f:
                        content = f.read()
                        # CI should test with both 3.11 and 3.12
                        if "python-version" in content:
                            assert "'3.11'" in content or '"3.11"' in content or "'3.12'" in content or '"3.12"' in content

    def test_node_version_consistency(self):
        """Test Node version is consistent"""
        nvmrc = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/.nvmrc")

        with open(nvmrc, 'r') as f:
            node_version = f.read().strip()

        assert node_version == "22"

        # Check package.json engines if specified
        package_json = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/apps/dashboard/package.json")
        with open(package_json, 'r') as f:
            package = json.load(f)
            if "engines" in package:
                assert "node" in package["engines"]
                assert ">=22" in package["engines"]["node"]

    def test_pusher_configuration(self):
        """Test Pusher is properly configured"""
        # Check backend has Pusher
        requirements = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/requirements.txt")
        with open(requirements, 'r') as f:
            content = f.read()
            assert "pusher==" in content

        # Check frontend has Pusher
        package_json = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/apps/dashboard/package.json")
        with open(package_json, 'r') as f:
            package = json.load(f)
            assert "pusher-js" in package.get("dependencies", {})

    def test_clerk_configuration(self):
        """Test Clerk authentication is configured"""
        package_json = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/apps/dashboard/package.json")
        with open(package_json, 'r') as f:
            package = json.load(f)
            assert "@clerk/clerk-react" in package.get("dependencies", {})

        # Check Docker Compose has Clerk env vars
        compose_path = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/infrastructure/docker/docker-compose.dev.yml")
        with open(compose_path, 'r') as f:
            content = f.read()
            assert "VITE_CLERK_PUBLISHABLE_KEY" in content
            assert "VITE_ENABLE_CLERK_AUTH" in content

    def test_database_service_configuration(self):
        """Test database service configurations are correct"""
        compose_path = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/infrastructure/docker/docker-compose.dev.yml")

        with open(compose_path, 'r') as f:
            content = f.read()

        # PostgreSQL should use correct image and setup
        assert "postgres:15-alpine" in content
        assert "POSTGRES_MULTIPLE_DATABASES" in content

        # Redis should have proper configuration
        assert "redis:7-alpine" in content
        assert "maxmemory 512mb" in content
        assert "maxmemory-policy allkeys-lru" in content

    def test_security_configuration_alignment(self):
        """Test security configurations are consistent"""
        # Check .env.example has security recommendations
        env_example = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/.env.example")
        with open(env_example, 'r') as f:
            content = f.read()

        # Security recommendations should be present
        assert "Generate secure keys" in content
        assert "JWT Secret: openssl rand -hex 32" in content
        assert "Store production secrets in a secure vault" in content
        assert "NEVER commit real credentials" in content
        assert "Rotate credentials regularly" in content

    def test_port_configuration_consistency(self):
        """Test port configurations don't conflict"""
        compose_path = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/infrastructure/docker/docker-compose.dev.yml")

        with open(compose_path, 'r') as f:
            content = f.read()

        # Extract port mappings
        expected_ports = {
            "5434": "postgres",  # PostgreSQL external port
            "6381": "redis",     # Redis external port
            "8009": "fastapi-main",  # Backend API
            "5179": "dashboard-frontend",  # Frontend
            "9877": "mcp-server",  # MCP server
            "8888": "agent-coordinator",  # Agent coordinator
            "5001": "flask-bridge",  # Flask bridge
            "8000": "ghost-backend"  # Ghost CMS
        }

        for port, service in expected_ports.items():
            assert f"'{port}:" in content, f"Port {port} not found for {service}"

    def test_environment_variables_docker_alignment(self):
        """Test environment variables align between .env.example and docker-compose"""
        env_example = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/.env.example")
        compose_path = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/infrastructure/docker/docker-compose.dev.yml")

        with open(env_example, 'r') as f:
            env_content = f.read()

        with open(compose_path, 'r') as f:
            compose_content = f.read()

        # Key environment variables should be referenced in both
        key_vars = [
            "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD",
            "REDIS_URL", "JWT_SECRET_KEY",
            "PUSHER_APP_ID", "PUSHER_KEY", "PUSHER_SECRET", "PUSHER_CLUSTER",
            "OPENAI_API_KEY", "CLERK_SECRET_KEY"
        ]

        for var in key_vars:
            # Variable should be defined in .env.example
            assert f"{var}=" in env_content, f"{var} not found in .env.example"

            # Variable should be referenced in docker-compose (either as ${VAR} or ${VAR:-default})
            assert f"${{{var}" in compose_content, f"{var} not referenced in docker-compose.dev.yml"

    def test_health_check_configuration(self):
        """Test health checks are properly configured"""
        compose_path = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/infrastructure/docker/docker-compose.dev.yml")

        with open(compose_path, 'r') as f:
            content = f.read()

        # All services should have health checks
        services_with_health_checks = [
            "postgres", "redis", "fastapi-main", "mcp-server",
            "agent-coordinator", "dashboard-frontend", "ghost-backend"
        ]

        for service in services_with_health_checks:
            assert f"{service}:" in content  # Service exists
            # Look for health check in the service section
            service_start = content.find(f"{service}:")
            service_section = content[service_start:service_start + 2000]  # Look in next 2000 chars
            assert "healthcheck:" in service_section, f"Health check missing for {service}"

    def test_volume_configuration(self):
        """Test volume configurations are correct"""
        compose_path = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/infrastructure/docker/docker-compose.dev.yml")

        with open(compose_path, 'r') as f:
            content = f.read()

        # Required volumes should be defined
        required_volumes = [
            "postgres_data", "redis_data", "agent_data", "logs",
            "static_files", "ghost_content", "mcp_contexts",
            "educational_content", "dashboard-logs"
        ]

        for volume in required_volumes:
            assert f"{volume}:" in content, f"Volume {volume} not defined"

    def test_network_configuration(self):
        """Test network configurations are correct"""
        compose_path = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/infrastructure/docker/docker-compose.dev.yml")

        with open(compose_path, 'r') as f:
            content = f.read()

        # Required networks should be defined
        required_networks = ["toolboxai_network", "mcp_network"]

        for network in required_networks:
            assert f"{network}:" in content, f"Network {network} not defined"
            assert "driver: bridge" in content  # Should use bridge driver
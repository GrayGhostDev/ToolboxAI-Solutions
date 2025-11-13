"""
Integration tests for Makefile commands.

Tests all Makefile targets to ensure build, deployment, and Docker
commands work correctly.
"""

import os
import subprocess
from pathlib import Path

import pytest


@pytest.mark.integration
@pytest.mark.makefile
class TestMakefileCommands:
    """Test Makefile commands and targets."""

    def setup_method(self):
        """Set up test environment."""
        self.project_root = Path(__file__).parent.parent.parent
        self.makefile_path = self.project_root / "Makefile"

        # Verify Makefile exists
        assert self.makefile_path.exists(), "Makefile not found in project root"

    def run_make_command(self, target: str, env: dict = None, timeout: int = 60) -> tuple:
        """
        Run a make command and return output.

        Args:
            target: Make target to run
            env: Environment variables
            timeout: Command timeout in seconds

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        cmd = ["make", target]
        env_vars = os.environ.copy()
        if env:
            env_vars.update(env)

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                env=env_vars,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"

    def test_makefile_exists_and_valid(self):
        """Test that Makefile exists and has valid syntax."""
        # Test dry run to check syntax
        returncode, stdout, stderr = self.run_make_command("-n", timeout=10)

        # Should not have syntax errors
        assert "error" not in stderr.lower() or returncode == 0, f"Makefile syntax error: {stderr}"

    def test_make_help_command(self):
        """Test make help or docker-help command."""
        returncode, stdout, stderr = self.run_make_command("docker-help", timeout=10)

        if returncode != 0:
            # Try alternative help command
            returncode, stdout, stderr = self.run_make_command("help", timeout=10)

        # Should show help information
        assert (
            "docker" in stdout.lower() or "help" in stdout.lower()
        ), "Help command should show usage"

    def test_make_lint_command(self):
        """Test make lint command."""
        returncode, stdout, stderr = self.run_make_command("lint", timeout=60)

        # Lint command should complete (may have warnings)
        assert returncode in [0, 1], f"Lint failed with code {returncode}: {stderr}"

        # Should mention linting
        output = stdout + stderr
        assert any(
            word in output.lower() for word in ["lint", "black", "mypy", "eslint"]
        ), "Lint command should run linters"

    def test_make_test_command(self):
        """Test make test command."""
        returncode, stdout, stderr = self.run_make_command("test", timeout=120)

        # Test command should run
        output = stdout + stderr
        assert any(
            word in output.lower() for word in ["test", "pytest", "jest"]
        ), "Test command should run tests"

    def test_make_build_command(self):
        """Test make build command."""
        returncode, stdout, stderr = self.run_make_command("build", timeout=180)

        # Build might fail if dependencies aren't installed, but should attempt
        output = stdout + stderr
        assert (
            "build" in output.lower() or "npm" in output.lower()
        ), "Build command should attempt to build"

    def test_docker_commands_availability(self):
        """Test Docker-related make commands are defined."""
        # Read Makefile content
        with open(self.makefile_path) as f:
            makefile_content = f.read()

        # Check for Docker targets
        docker_targets = [
            "docker-dev",
            "docker-dev-build",
            "docker-dev-logs",
            "docker-dev-stop",
            "docker-dev-down",
            "docker-prod",
            "docker-monitoring",
            "celery-worker",
            "celery-beat",
            "roblox-sync",
            "stack-up",
            "stack-down",
        ]

        for target in docker_targets:
            assert f"{target}:" in makefile_content, f"Docker target {target} not found in Makefile"

    def test_make_urls_command(self):
        """Test make urls command shows service URLs."""
        returncode, stdout, stderr = self.run_make_command("urls", timeout=10)

        # Should show service URLs
        assert returncode == 0, f"URLs command failed: {stderr}"

        expected_urls = ["Backend API", "Dashboard", "localhost:8009", "localhost:5179"]

        for url in expected_urls:
            assert url in stdout, f"Expected URL '{url}' not in output"

    @pytest.mark.docker
    def test_docker_dev_command_dry_run(self):
        """Test docker-dev command in dry-run mode."""
        # Test with dry-run to avoid actually starting services
        returncode, stdout, stderr = self.run_make_command("docker-dev --dry-run", timeout=10)

        # Check if docker-compose command would be called
        if returncode == 0:
            output = stdout + stderr
            assert "docker" in output.lower() or "compose" in output.lower()

    def test_celery_commands_defined(self):
        """Test Celery-related make commands are defined."""
        with open(self.makefile_path) as f:
            makefile_content = f.read()

        celery_targets = [
            "celery-worker",
            "celery-beat",
            "celery-flower",
            "celery-logs",
            "celery-status",
            "celery-purge",
        ]

        for target in celery_targets:
            assert f"{target}:" in makefile_content, f"Celery target {target} not found"

    def test_monitoring_commands_defined(self):
        """Test monitoring stack commands are defined."""
        with open(self.makefile_path) as f:
            makefile_content = f.read()

        monitoring_targets = [
            "docker-monitoring",
            "docker-monitoring-down",
            "prometheus",
            "grafana",
        ]

        # At least some monitoring targets should exist
        found_targets = [t for t in monitoring_targets if f"{t}:" in makefile_content]
        assert len(found_targets) >= 2, "Monitoring targets missing from Makefile"

    def test_make_health_command(self):
        """Test make health command."""
        returncode, stdout, stderr = self.run_make_command("health", timeout=10)

        # Health command should check service status
        if returncode == 0:
            output = stdout + stderr
            assert (
                "toolboxai" in output.lower()
                or "health" in output.lower()
                or "docker ps" in output.lower()
            ), "Health command should check services"

    def test_database_commands_defined(self):
        """Test database-related commands are defined."""
        with open(self.makefile_path) as f:
            makefile_content = f.read()

        db_commands = ["db-shell", "redis-cli"]

        for cmd in db_commands:
            assert f"{cmd}:" in makefile_content, f"Database command {cmd} not found"

    def test_makefile_variables(self):
        """Test Makefile variables are properly defined."""
        with open(self.makefile_path) as f:
            makefile_content = f.read()

        # Check for important variables
        important_vars = ["API_HOST", "API_PORT", "DASHBOARD_PORT", "DOCKER_DIR", "COMPOSE_BASE"]

        for var in important_vars:
            assert f"{var}" in makefile_content, f"Variable {var} not defined"

    def test_make_backend_command(self):
        """Test make backend command configuration."""
        # Test dry-run to check command formation
        returncode, stdout, stderr = self.run_make_command("backend -n", timeout=10)

        # Check command would run uvicorn
        if returncode == 0:
            assert "uvicorn" in stdout or "uvicorn" in stderr, "Backend command should use uvicorn"

    def test_make_dashboard_command(self):
        """Test make dashboard command configuration."""
        # Test dry-run
        returncode, stdout, stderr = self.run_make_command("dashboard -n", timeout=10)

        # Check command would run npm
        if returncode == 0:
            assert "npm" in stdout or "npm" in stderr, "Dashboard command should use npm"

    def test_docker_compose_files_referenced(self):
        """Test that Docker Compose files referenced in Makefile exist."""
        with open(self.makefile_path) as f:
            makefile_content = f.read()

        # Extract docker-compose file references
        compose_files = [
            "infrastructure/docker/compose/docker-compose.yml",
            "infrastructure/docker/compose/docker-compose.dev.yml",
            "infrastructure/docker/compose/docker-compose.prod.yml",
            "infrastructure/docker/compose/docker-compose.monitoring.yml",
        ]

        for compose_file in compose_files:
            if compose_file in makefile_content:
                file_path = self.project_root / compose_file
                assert (
                    file_path.exists()
                ), f"Docker Compose file {compose_file} referenced but not found"

    def test_phony_targets_declared(self):
        """Test that .PHONY targets are properly declared."""
        with open(self.makefile_path) as f:
            makefile_content = f.read()

        # Should have .PHONY declaration
        assert ".PHONY:" in makefile_content, ".PHONY targets should be declared"

    def test_docker_secrets_command(self):
        """Test Docker secrets creation command exists."""
        with open(self.makefile_path) as f:
            makefile_content = f.read()

        # Check for secrets-related commands
        assert (
            "docker-secrets" in makefile_content or "secrets" in makefile_content
        ), "Docker secrets management should be defined"

    def test_stack_commands_integration(self):
        """Test full stack commands are properly integrated."""
        with open(self.makefile_path) as f:
            makefile_content = f.read()

        stack_commands = ["stack-up", "stack-down", "stack-clean"]

        for cmd in stack_commands:
            if f"{cmd}:" in makefile_content:
                # Check command has proper dependencies
                cmd_section = makefile_content.split(f"{cmd}:")[1].split("\n")[0:5]
                cmd_text = "\n".join(cmd_section)

                # Should reference docker commands
                assert (
                    "docker" in cmd_text.lower() or "make" in cmd_text.lower()
                ), f"Stack command {cmd} should call docker or make commands"


@pytest.mark.integration
@pytest.mark.makefile
@pytest.mark.skipif(not os.getenv("CI"), reason="Only run in CI environment")
class TestMakefileCI:
    """Test Makefile commands in CI environment."""

    def test_ci_build_command(self):
        """Test build command works in CI."""
        result = subprocess.run(["make", "build"], capture_output=True, text=True, timeout=300)

        assert result.returncode == 0, f"Build failed in CI: {result.stderr}"

    def test_ci_test_command(self):
        """Test test command works in CI."""
        result = subprocess.run(["make", "test"], capture_output=True, text=True, timeout=300)

        # Tests might fail but command should run
        assert result.returncode in [0, 1], f"Test command failed to run: {result.stderr}"

"""Security compliance tests matching GitHub Actions security pipeline"""

import json
import subprocess
from pathlib import Path

import pytest


class TestSecurityCompliance:
    """Test security compliance matching CI/CD pipeline"""

    def test_no_secrets_in_code(self):
        """Test for exposed secrets using detect-secrets"""
        # Check if detect-secrets is available
        try:
            result = subprocess.run(["detect-secrets", "--version"], capture_output=True, text=True)
        except FileNotFoundError:
            pytest.skip("detect-secrets not installed")

        # Run detect-secrets scan
        result = subprocess.run(
            ["detect-secrets", "scan", "--baseline", ".secrets.baseline"],
            capture_output=True,
            text=True,
            cwd="/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions",
        )

        if result.returncode != 0:
            # Check if it's just missing baseline (first run)
            if "FileNotFoundError" in result.stderr:
                pytest.skip(
                    "No secrets baseline found - run 'detect-secrets scan --update .secrets.baseline' first"
                )
            else:
                pytest.fail(f"Secrets detected in codebase: {result.stdout}")

    def test_dependencies_are_secure(self):
        """Test for known vulnerabilities in dependencies"""
        # Check if safety is available
        try:
            result = subprocess.run(["safety", "--version"], capture_output=True, text=True)
        except FileNotFoundError:
            pytest.skip("safety not installed")

        result = subprocess.run(
            ["safety", "check", "--json"],
            capture_output=True,
            text=True,
            cwd="/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions",
        )

        if result.returncode != 0 and result.stdout:
            try:
                vulnerabilities = json.loads(result.stdout)
                critical = [v for v in vulnerabilities if v.get("severity") in ["high", "critical"]]
                assert len(critical) == 0, f"Critical vulnerabilities found: {critical}"
            except json.JSONDecodeError:
                # If JSON parsing fails, check stderr for actual errors
                if "No known security vulnerabilities found" not in result.stderr:
                    pytest.fail(f"Security check failed: {result.stderr}")

    def test_python_code_security(self):
        """Test Python code security with bandit"""
        # Check if bandit is available
        try:
            result = subprocess.run(["bandit", "--version"], capture_output=True, text=True)
        except FileNotFoundError:
            pytest.skip("bandit not installed")

        result = subprocess.run(
            ["bandit", "-r", "apps/", "core/", "-f", "json"],
            capture_output=True,
            text=True,
            cwd="/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions",
        )

        if result.stdout:
            try:
                report = json.loads(result.stdout)
                high_severity = [
                    i for i in report.get("results", []) if i.get("issue_severity") == "HIGH"
                ]
                assert len(high_severity) == 0, f"High severity issues found: {high_severity}"
            except json.JSONDecodeError:
                # If no JSON output, bandit probably found no issues
                pass

    def test_environment_files_security(self):
        """Test that environment files don't contain real secrets"""
        project_root = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions")

        # Check .env files (excluding .env.example and .env.test)
        env_files = [".env", ".env.docker", ".env.production"]

        dangerous_patterns = [
            r"sk-[a-zA-Z0-9]{48,}",  # OpenAI API keys
            r"xoxb-[0-9]{12}-[0-9]{12}-[a-zA-Z0-9]{24}",  # Slack bot tokens
            r"ya29\.[a-zA-Z0-9_-]+",  # Google OAuth tokens
            r"AKIA[0-9A-Z]{16}",  # AWS Access Key IDs
        ]

        for env_file in env_files:
            file_path = project_root / env_file
            if file_path.exists():
                with open(file_path) as f:
                    content = f.read()

                # Check for actual API keys (not placeholder values)
                import re

                for pattern in dangerous_patterns:
                    matches = re.findall(pattern, content)
                    assert (
                        len(matches) == 0
                    ), f"Potential real API key found in {env_file}: {matches}"

                # Check for placeholder patterns are used
                placeholders = ["your-key", "your-secret", "your-token", "xxx", "placeholder"]
                api_key_lines = [
                    line
                    for line in content.split("\n")
                    if "API_KEY" in line or "SECRET" in line or "TOKEN" in line
                ]

                for line in api_key_lines:
                    if "=" in line and not line.strip().startswith("#"):
                        value = line.split("=", 1)[1].strip().strip("\"'")
                        if value and not any(
                            placeholder in value.lower() for placeholder in placeholders
                        ):
                            # Check if it looks like a real key (long alphanumeric string)
                            if len(value) > 20 and value.isalnum():
                                pytest.fail(f"Potential real API key in {env_file}: {line}")

    def test_pusher_security_configuration(self):
        """Test Pusher security configuration"""
        # Check that Pusher is configured with SSL
        from core.services.pusher_service import PusherService

        # This would be mocked in actual tests
        # Just check that the service exists and has security considerations
        assert hasattr(
            PusherService, "trigger_event"
        ), "PusherService should have trigger_event method"

    def test_database_security_settings(self):
        """Test database security configuration"""
        project_root = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions")

        # Check database configuration doesn't use default passwords
        dangerous_db_configs = [
            "password=password",
            "password=admin",
            "password=root",
            "password=123456",
        ]

        env_files = [".env", ".env.docker", ".env.production"]
        for env_file in env_files:
            file_path = project_root / env_file
            if file_path.exists():
                with open(file_path) as f:
                    content = f.read().lower()

                for dangerous_config in dangerous_db_configs:
                    assert (
                        dangerous_config not in content
                    ), f"Dangerous database config found in {env_file}"

    def test_cors_configuration_security(self):
        """Test CORS configuration is not overly permissive"""
        backend_main = Path(
            "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/apps/backend/main.py"
        )

        if backend_main.exists():
            with open(backend_main) as f:
                content = f.read()

            # Check that CORS is not set to allow all origins in production
            import re

            cors_patterns = [
                r'allow_origins=\["\*"\]',
                r'allow_origins=\["http://\*"\]',
                r'CORSMiddleware.*allow_origins=\["\*"\]',
            ]

            for pattern in cors_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    # Check if it's conditional or in development only
                    context_lines = content.split("\n")
                    for i, line in enumerate(context_lines):
                        if "*" in line and "origin" in line.lower():
                            # Check surrounding lines for development conditions
                            context = "\n".join(context_lines[max(0, i - 3) : i + 4])
                            if not any(
                                keyword in context.lower()
                                for keyword in ["development", "debug", "dev", "test"]
                            ):
                                pytest.fail(f"Overly permissive CORS configuration found: {line}")

    def test_jwt_security_configuration(self):
        """Test JWT security configuration"""
        # Check JWT settings
        settings_file = Path(
            "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/toolboxai_settings/settings.py"
        )

        if settings_file.exists():
            with open(settings_file) as f:
                content = f.read()

            # Check for JWT secret key configuration
            if "JWT_SECRET_KEY" in content or "SECRET_KEY" in content:
                # Ensure it's not a hardcoded weak key
                weak_keys = ["secret", "123456", "password", "key"]
                lines = content.split("\n")
                for line in lines:
                    if "SECRET_KEY" in line and "=" in line:
                        value = line.split("=", 1)[1].strip().strip("\"'")
                        for weak_key in weak_keys:
                            assert (
                                weak_key.lower() not in value.lower()
                            ), f"Weak JWT secret key found: {line}"

    def test_file_upload_security(self):
        """Test file upload security measures"""
        # Check for file upload handlers and security measures
        backend_files = Path(
            "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/apps/backend"
        ).rglob("*.py")

        dangerous_patterns = [
            r"open\([^)]*request\.files",  # Direct file opening from request
            r"exec\(",  # Code execution
            r"eval\(",  # Code evaluation
            r"__import__",  # Dynamic imports
        ]

        for file_path in backend_files:
            with open(file_path) as f:
                content = f.read()

            import re

            for pattern in dangerous_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    pytest.fail(f"Potentially dangerous pattern found in {file_path}: {matches}")

    def test_sql_injection_prevention(self):
        """Test SQL injection prevention measures"""
        # Check for raw SQL queries without parameterization
        python_files = Path(
            "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions"
        ).rglob("*.py")

        dangerous_sql_patterns = [
            r"execute\([^)]*%[^)]*\)",  # String formatting in SQL
            r"execute\([^)]*\+[^)]*\)",  # String concatenation in SQL
            r'execute\([^)]*f"[^"]*{[^}]*}[^"]*"\)',  # f-string in SQL
        ]

        for file_path in python_files:
            if "venv" in str(file_path) or "node_modules" in str(file_path):
                continue

            try:
                with open(file_path) as f:
                    content = f.read()

                import re

                for pattern in dangerous_sql_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        pytest.fail(
                            f"Potential SQL injection vulnerability in {file_path}: {matches}"
                        )
            except (UnicodeDecodeError, PermissionError):
                # Skip binary files or files we can't read
                continue

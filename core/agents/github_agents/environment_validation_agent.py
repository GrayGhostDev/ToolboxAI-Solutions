"""
Environment Validation Agent for GitHub deployment readiness.

This agent validates environment configurations, secrets, API connectivity,
database connections, and external service dependencies to ensure deployment readiness.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

import aiohttp
import yaml
from pydantic import BaseModel, Field

from .base_github_agent import BaseGitHubAgent

logger = logging.getLogger(__name__)


class ValidationResult(BaseModel):
    """Represents a validation check result."""

    category: str = Field(description="Validation category")
    check_name: str = Field(description="Name of the check")
    status: str = Field(description="Status: pass, fail, warning, skip")
    message: str = Field(description="Human-readable message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details")
    remediation: Optional[str] = Field(None, description="Suggested remediation")


class EnvironmentConfig(BaseModel):
    """Environment configuration metadata."""

    name: str = Field(description="Environment name")
    config_files: List[str] = Field(default_factory=list, description="Configuration files")
    required_vars: List[str] = Field(default_factory=list, description="Required environment variables")
    optional_vars: List[str] = Field(default_factory=list, description="Optional environment variables")
    services: List[str] = Field(default_factory=list, description="Required services")


class ValidationReport(BaseModel):
    """Comprehensive validation report."""

    timestamp: str = Field(description="Report generation timestamp")
    environment: str = Field(description="Target environment")
    overall_status: str = Field(description="Overall validation status")
    summary: Dict[str, int] = Field(default_factory=dict, description="Summary by status")
    results: List[ValidationResult] = Field(default_factory=list, description="Detailed results")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
    deployment_ready: bool = Field(description="Whether environment is deployment ready")


class EnvironmentValidationAgent(BaseGitHubAgent):
    """Agent for validating environment configurations and deployment readiness."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the Environment Validation Agent.

        Args:
            config_path: Path to configuration file
        """
        super().__init__(config_path)
        self.environment_configs = self._load_environment_configs()
        self.validation_results: List[ValidationResult] = []

    def _load_environment_configs(self) -> Dict[str, EnvironmentConfig]:
        """Load environment configuration definitions.

        Returns:
            Dictionary of environment configurations
        """
        return {
            "development": EnvironmentConfig(
                name="development",
                config_files=[".env", ".env.local", "config/database.env"],
                required_vars=[
                    "DATABASE_URL", "REDIS_URL", "OPENAI_API_KEY",
                    "JWT_SECRET_KEY", "API_HOST", "API_PORT"
                ],
                optional_vars=[
                    "DEBUG", "SENTRY_DSN", "PUSHER_APP_ID", "PUSHER_KEY",
                    "PUSHER_SECRET", "PUSHER_CLUSTER", "CANVAS_TOKEN", "SCHOOLOGY_KEY"
                ],
                services=["postgresql", "redis"]
            ),
            "staging": EnvironmentConfig(
                name="staging",
                config_files=[".env.staging", "config/production/production.env"],
                required_vars=[
                    "DATABASE_URL", "REDIS_URL", "OPENAI_API_KEY",
                    "JWT_SECRET_KEY", "API_HOST", "API_PORT", "SENTRY_DSN"
                ],
                optional_vars=[
                    "PUSHER_APP_ID", "PUSHER_KEY", "PUSHER_SECRET",
                    "PUSHER_CLUSTER", "CANVAS_TOKEN", "SCHOOLOGY_KEY"
                ],
                services=["postgresql", "redis", "nginx"]
            ),
            "production": EnvironmentConfig(
                name="production",
                config_files=[".env.production", "config/production/production.env", "render.yaml"],
                required_vars=[
                    "DATABASE_URL", "REDIS_URL", "OPENAI_API_KEY",
                    "JWT_SECRET_KEY", "API_HOST", "API_PORT", "SENTRY_DSN",
                    "PUSHER_APP_ID", "PUSHER_KEY", "PUSHER_SECRET", "PUSHER_CLUSTER"
                ],
                optional_vars=["CANVAS_TOKEN", "SCHOOLOGY_KEY"],
                services=["postgresql", "redis", "nginx", "monitoring"]
            )
        }

    async def analyze(self, environment: str = "development", **kwargs) -> Dict[str, Any]:
        """Main validation entry point.

        Args:
            environment: Target environment to validate
            **kwargs: Additional analysis parameters

        Returns:
            Analysis results with validation report
        """
        try:
            await self.log_operation("environment_validation_started", {
                "environment": environment,
                "timestamp": datetime.now().isoformat()
            })

            self.validation_results = []

            # Get environment configuration
            env_config = self.environment_configs.get(environment)
            if not env_config:
                return {
                    "error": f"Unknown environment: {environment}",
                    "available_environments": list(self.environment_configs.keys())
                }

            # Run all validation checks
            await self._run_validation_suite(env_config)

            # Generate comprehensive report
            report = self.generate_validation_report(environment)

            # Update metrics
            self.update_metrics(
                operations_performed=1,
                files_processed=len(env_config.config_files)
            )

            await self.log_operation("environment_validation_completed", {
                "environment": environment,
                "status": report.overall_status,
                "deployment_ready": report.deployment_ready
            })

            return {
                "status": "success",
                "environment": environment,
                "report": report.model_dump(),
                "deployment_ready": report.deployment_ready,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Environment validation failed: {e}")
            self.update_metrics(errors_encountered=1)
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _run_validation_suite(self, env_config: EnvironmentConfig) -> None:
        """Run the complete validation suite.

        Args:
            env_config: Environment configuration to validate
        """
        validation_tasks = [
            self.check_environment_variables(env_config),
            self.test_database_connectivity(env_config),
            self.test_api_endpoints(env_config),
            self.test_external_services(env_config),
            self.validate_secrets(env_config),
            self._validate_config_files(env_config),
            self._validate_docker_configuration(),
            self._validate_deployment_configuration(env_config)
        ]

        # Run validations concurrently
        await asyncio.gather(*validation_tasks, return_exceptions=True)

    async def check_environment_variables(self, env_config: EnvironmentConfig) -> None:
        """Validate required environment variables.

        Args:
            env_config: Environment configuration
        """
        try:
            # Load environment variables from config files
            env_vars = await self._load_environment_variables(env_config.config_files)

            # Check required variables
            missing_required = []
            for var in env_config.required_vars:
                if var not in env_vars or not env_vars[var]:
                    missing_required.append(var)
                else:
                    self.validation_results.append(ValidationResult(
                        category="environment_variables",
                        check_name=f"required_var_{var}",
                        status="pass",
                        message=f"Required variable {var} is configured",
                        details={"variable": var, "has_value": bool(env_vars[var])}
                    ))

            if missing_required:
                self.validation_results.append(ValidationResult(
                    category="environment_variables",
                    check_name="required_variables",
                    status="fail",
                    message=f"Missing required environment variables: {', '.join(missing_required)}",
                    details={"missing_variables": missing_required},
                    remediation=f"Set the following environment variables: {', '.join(missing_required)}"
                ))

            # Check optional variables
            missing_optional = []
            for var in env_config.optional_vars:
                if var not in env_vars or not env_vars[var]:
                    missing_optional.append(var)
                else:
                    self.validation_results.append(ValidationResult(
                        category="environment_variables",
                        check_name=f"optional_var_{var}",
                        status="pass",
                        message=f"Optional variable {var} is configured"
                    ))

            if missing_optional:
                self.validation_results.append(ValidationResult(
                    category="environment_variables",
                    check_name="optional_variables",
                    status="warning",
                    message=f"Missing optional environment variables: {', '.join(missing_optional)}",
                    details={"missing_optional": missing_optional},
                    remediation="Consider setting optional variables for full functionality"
                ))

        except Exception as e:
            self.validation_results.append(ValidationResult(
                category="environment_variables",
                check_name="env_var_check",
                status="fail",
                message=f"Failed to check environment variables: {str(e)}",
                remediation="Check environment configuration files and permissions"
            ))

    async def test_database_connectivity(self, env_config: EnvironmentConfig) -> None:
        """Test database connectivity.

        Args:
            env_config: Environment configuration
        """
        try:
            env_vars = await self._load_environment_variables(env_config.config_files)
            database_url = env_vars.get("DATABASE_URL")

            if not database_url:
                self.validation_results.append(ValidationResult(
                    category="database",
                    check_name="database_url",
                    status="fail",
                    message="DATABASE_URL not configured",
                    remediation="Set DATABASE_URL environment variable"
                ))
                return

            # Parse database URL
            parsed = urlparse(database_url)
            if not parsed.scheme.startswith('postgresql'):
                self.validation_results.append(ValidationResult(
                    category="database",
                    check_name="database_type",
                    status="fail",
                    message=f"Unsupported database type: {parsed.scheme}",
                    remediation="Use PostgreSQL database URL"
                ))
                return

            # Test connectivity (this would require actual database connection)
            # For now, we'll validate the URL format
            required_components = ['hostname', 'port', 'username', 'password', 'path']
            missing_components = []

            if not parsed.hostname:
                missing_components.append('hostname')
            if not parsed.port:
                missing_components.append('port')
            if not parsed.username:
                missing_components.append('username')
            if not parsed.password:
                missing_components.append('password')
            if not parsed.path or parsed.path == '/':
                missing_components.append('database_name')

            if missing_components:
                self.validation_results.append(ValidationResult(
                    category="database",
                    check_name="database_url_format",
                    status="fail",
                    message=f"Invalid database URL format. Missing: {', '.join(missing_components)}",
                    remediation="Ensure DATABASE_URL includes all required components"
                ))
            else:
                self.validation_results.append(ValidationResult(
                    category="database",
                    check_name="database_url_format",
                    status="pass",
                    message="Database URL format is valid",
                    details={
                        "host": parsed.hostname,
                        "port": parsed.port,
                        "database": parsed.path[1:] if parsed.path else None
                    }
                ))

        except Exception as e:
            self.validation_results.append(ValidationResult(
                category="database",
                check_name="database_connectivity",
                status="fail",
                message=f"Database connectivity check failed: {str(e)}",
                remediation="Verify database configuration and network connectivity"
            ))

    async def test_api_endpoints(self, env_config: EnvironmentConfig) -> None:
        """Validate API endpoints connectivity.

        Args:
            env_config: Environment configuration
        """
        try:
            env_vars = await self._load_environment_variables(env_config.config_files)
            api_host = env_vars.get("API_HOST", "127.0.0.1")
            api_port = env_vars.get("API_PORT", "8008")

            # Construct base URL
            base_url = f"http://{api_host}:{api_port}"

            # Test endpoints
            endpoints_to_test = [
                "/health",
                "/docs",
                "/api/v1/health",
                "/"
            ]

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                for endpoint in endpoints_to_test:
                    try:
                        url = f"{base_url}{endpoint}"
                        async with session.get(url) as response:
                            if response.status < 400:
                                self.validation_results.append(ValidationResult(
                                    category="api_endpoints",
                                    check_name=f"endpoint_{endpoint.replace('/', '_')}",
                                    status="pass",
                                    message=f"Endpoint {endpoint} is accessible",
                                    details={"url": url, "status_code": response.status}
                                ))
                            else:
                                self.validation_results.append(ValidationResult(
                                    category="api_endpoints",
                                    check_name=f"endpoint_{endpoint.replace('/', '_')}",
                                    status="warning",
                                    message=f"Endpoint {endpoint} returned status {response.status}",
                                    details={"url": url, "status_code": response.status}
                                ))
                    except asyncio.TimeoutError:
                        self.validation_results.append(ValidationResult(
                            category="api_endpoints",
                            check_name=f"endpoint_{endpoint.replace('/', '_')}",
                            status="fail",
                            message=f"Endpoint {endpoint} timed out",
                            details={"url": f"{base_url}{endpoint}"},
                            remediation="Check if API server is running and accessible"
                        ))
                    except Exception as e:
                        self.validation_results.append(ValidationResult(
                            category="api_endpoints",
                            check_name=f"endpoint_{endpoint.replace('/', '_')}",
                            status="fail",
                            message=f"Endpoint {endpoint} failed: {str(e)}",
                            details={"url": f"{base_url}{endpoint}", "error": str(e)}
                        ))

        except Exception as e:
            self.validation_results.append(ValidationResult(
                category="api_endpoints",
                check_name="api_connectivity",
                status="fail",
                message=f"API endpoint testing failed: {str(e)}",
                remediation="Check API configuration and server status"
            ))

    async def test_external_services(self, env_config: EnvironmentConfig) -> None:
        """Check external service dependencies.

        Args:
            env_config: Environment configuration
        """
        try:
            env_vars = await self._load_environment_variables(env_config.config_files)

            # Test Redis connectivity
            redis_url = env_vars.get("REDIS_URL")
            if redis_url:
                redis_parsed = urlparse(redis_url)
                if redis_parsed.scheme == 'redis':
                    self.validation_results.append(ValidationResult(
                        category="external_services",
                        check_name="redis_config",
                        status="pass",
                        message="Redis URL format is valid",
                        details={"host": redis_parsed.hostname, "port": redis_parsed.port}
                    ))
                else:
                    self.validation_results.append(ValidationResult(
                        category="external_services",
                        check_name="redis_config",
                        status="fail",
                        message="Invalid Redis URL format",
                        remediation="Ensure REDIS_URL uses redis:// scheme"
                    ))
            else:
                self.validation_results.append(ValidationResult(
                    category="external_services",
                    check_name="redis_config",
                    status="fail",
                    message="REDIS_URL not configured",
                    remediation="Set REDIS_URL environment variable"
                ))

            # Test Pusher configuration
            pusher_vars = ["PUSHER_APP_ID", "PUSHER_KEY", "PUSHER_SECRET", "PUSHER_CLUSTER"]
            pusher_configured = all(env_vars.get(var) for var in pusher_vars)

            if pusher_configured:
                self.validation_results.append(ValidationResult(
                    category="external_services",
                    check_name="pusher_config",
                    status="pass",
                    message="Pusher configuration is complete",
                    details={"cluster": env_vars.get("PUSHER_CLUSTER")}
                ))
            else:
                missing_pusher = [var for var in pusher_vars if not env_vars.get(var)]
                self.validation_results.append(ValidationResult(
                    category="external_services",
                    check_name="pusher_config",
                    status="warning",
                    message=f"Incomplete Pusher configuration. Missing: {', '.join(missing_pusher)}",
                    details={"missing_vars": missing_pusher},
                    remediation="Configure all Pusher variables for real-time features"
                ))

            # Test Sentry configuration
            sentry_dsn = env_vars.get("SENTRY_DSN")
            if sentry_dsn:
                if sentry_dsn.startswith("https://"):
                    self.validation_results.append(ValidationResult(
                        category="external_services",
                        check_name="sentry_config",
                        status="pass",
                        message="Sentry DSN is configured"
                    ))
                else:
                    self.validation_results.append(ValidationResult(
                        category="external_services",
                        check_name="sentry_config",
                        status="warning",
                        message="Sentry DSN format may be invalid",
                        remediation="Ensure Sentry DSN starts with https://"
                    ))
            else:
                status = "warning" if env_config.name == "development" else "fail"
                self.validation_results.append(ValidationResult(
                    category="external_services",
                    check_name="sentry_config",
                    status=status,
                    message="Sentry DSN not configured",
                    remediation="Configure Sentry for error monitoring"
                ))

        except Exception as e:
            self.validation_results.append(ValidationResult(
                category="external_services",
                check_name="external_services_check",
                status="fail",
                message=f"External services check failed: {str(e)}",
                remediation="Review external service configurations"
            ))

    async def validate_secrets(self, env_config: EnvironmentConfig) -> None:
        """Ensure secrets are configured without exposing values.

        Args:
            env_config: Environment configuration
        """
        try:
            env_vars = await self._load_environment_variables(env_config.config_files)

            # Check JWT secret
            jwt_secret = env_vars.get("JWT_SECRET_KEY")
            if jwt_secret:
                if len(jwt_secret) >= 32:
                    # Check for weak secrets
                    weak_secrets = [
                        "dev-secret-key-change-in-production",
                        "your-secret-key-change-in-production",
                        "change-me", "default", "secret", "key"
                    ]
                    if jwt_secret.lower() in [s.lower() for s in weak_secrets]:
                        self.validation_results.append(ValidationResult(
                            category="secrets",
                            check_name="jwt_secret_strength",
                            status="fail",
                            message="JWT secret is using a default/weak value",
                            remediation="Generate a strong, unique JWT secret"
                        ))
                    else:
                        self.validation_results.append(ValidationResult(
                            category="secrets",
                            check_name="jwt_secret_strength",
                            status="pass",
                            message="JWT secret appears to be strong",
                            details={"length": len(jwt_secret)}
                        ))
                else:
                    self.validation_results.append(ValidationResult(
                        category="secrets",
                        check_name="jwt_secret_length",
                        status="fail",
                        message=f"JWT secret is too short ({len(jwt_secret)} chars, minimum 32)",
                        remediation="Use a JWT secret of at least 32 characters"
                    ))
            else:
                self.validation_results.append(ValidationResult(
                    category="secrets",
                    check_name="jwt_secret_missing",
                    status="fail",
                    message="JWT_SECRET_KEY not configured",
                    remediation="Set JWT_SECRET_KEY environment variable"
                ))

            # Check OpenAI API key format
            openai_key = env_vars.get("OPENAI_API_KEY")
            if openai_key:
                if openai_key.startswith("sk-"):
                    self.validation_results.append(ValidationResult(
                        category="secrets",
                        check_name="openai_key_format",
                        status="pass",
                        message="OpenAI API key format is valid"
                    ))
                else:
                    self.validation_results.append(ValidationResult(
                        category="secrets",
                        check_name="openai_key_format",
                        status="warning",
                        message="OpenAI API key format may be invalid",
                        remediation="Ensure OpenAI API key starts with 'sk-'"
                    ))
            else:
                self.validation_results.append(ValidationResult(
                    category="secrets",
                    check_name="openai_key_missing",
                    status="fail",
                    message="OPENAI_API_KEY not configured",
                    remediation="Set OPENAI_API_KEY environment variable"
                ))

        except Exception as e:
            self.validation_results.append(ValidationResult(
                category="secrets",
                check_name="secrets_validation",
                status="fail",
                message=f"Secrets validation failed: {str(e)}",
                remediation="Review secrets configuration"
            ))

    async def _validate_config_files(self, env_config: EnvironmentConfig) -> None:
        """Validate configuration files exist and are readable.

        Args:
            env_config: Environment configuration
        """
        repo_root = self.get_repository_root()
        if not repo_root:
            self.validation_results.append(ValidationResult(
                category="config_files",
                check_name="repository_root",
                status="fail",
                message="Could not determine repository root",
                remediation="Ensure you're running from within a git repository"
            ))
            return

        for config_file in env_config.config_files:
            file_path = repo_root / config_file

            if file_path.exists():
                if file_path.is_file():
                    try:
                        # Test readability
                        with open(file_path, 'r') as f:
                            f.read(1)  # Read first character to test access

                        self.validation_results.append(ValidationResult(
                            category="config_files",
                            check_name=f"file_{config_file.replace('/', '_')}",
                            status="pass",
                            message=f"Configuration file {config_file} exists and is readable",
                            details={"path": str(file_path)}
                        ))
                    except Exception as e:
                        self.validation_results.append(ValidationResult(
                            category="config_files",
                            check_name=f"file_{config_file.replace('/', '_')}",
                            status="fail",
                            message=f"Configuration file {config_file} is not readable: {str(e)}",
                            remediation="Check file permissions"
                        ))
                else:
                    self.validation_results.append(ValidationResult(
                        category="config_files",
                        check_name=f"file_{config_file.replace('/', '_')}",
                        status="fail",
                        message=f"Configuration path {config_file} exists but is not a file",
                        remediation="Ensure the path points to a file, not a directory"
                    ))
            else:
                status = "warning" if config_file.endswith(('.local', '.example')) else "fail"
                self.validation_results.append(ValidationResult(
                    category="config_files",
                    check_name=f"file_{config_file.replace('/', '_')}",
                    status=status,
                    message=f"Configuration file {config_file} does not exist",
                    details={"expected_path": str(file_path)},
                    remediation=f"Create configuration file at {config_file}"
                ))

    async def _validate_docker_configuration(self) -> None:
        """Validate Docker configuration files."""
        repo_root = self.get_repository_root()
        if not repo_root:
            return

        docker_files = [
            "Dockerfile",
            "docker-compose.yml",
            "docker-compose.yaml",
            "config/production/docker-compose.yml"
        ]

        found_docker_files = []
        for docker_file in docker_files:
            file_path = repo_root / docker_file
            if file_path.exists():
                found_docker_files.append(docker_file)

                try:
                    with open(file_path, 'r') as f:
                        content = f.read()

                    if docker_file.startswith('docker-compose'):
                        # Validate docker-compose syntax
                        try:
                            yaml.safe_load(content)
                            self.validation_results.append(ValidationResult(
                                category="docker",
                                check_name=f"docker_compose_syntax",
                                status="pass",
                                message=f"Docker Compose file {docker_file} has valid syntax"
                            ))
                        except yaml.YAMLError as e:
                            self.validation_results.append(ValidationResult(
                                category="docker",
                                check_name=f"docker_compose_syntax",
                                status="fail",
                                message=f"Docker Compose file {docker_file} has invalid syntax: {str(e)}",
                                remediation="Fix YAML syntax errors in docker-compose file"
                            ))

                except Exception as e:
                    self.validation_results.append(ValidationResult(
                        category="docker",
                        check_name=f"docker_file_readable",
                        status="fail",
                        message=f"Cannot read Docker file {docker_file}: {str(e)}"
                    ))

        if found_docker_files:
            self.validation_results.append(ValidationResult(
                category="docker",
                check_name="docker_files_present",
                status="pass",
                message=f"Found Docker configuration files: {', '.join(found_docker_files)}"
            ))
        else:
            self.validation_results.append(ValidationResult(
                category="docker",
                check_name="docker_files_present",
                status="warning",
                message="No Docker configuration files found",
                remediation="Consider adding Dockerfile or docker-compose.yml for containerized deployment"
            ))

    async def _validate_deployment_configuration(self, env_config: EnvironmentConfig) -> None:
        """Validate deployment-specific configuration.

        Args:
            env_config: Environment configuration
        """
        repo_root = self.get_repository_root()
        if not repo_root:
            return

        # Check for render.yaml
        render_config = repo_root / "render.yaml"
        if render_config.exists():
            try:
                with open(render_config, 'r') as f:
                    render_data = yaml.safe_load(f)

                # Validate render.yaml structure
                if 'services' in render_data:
                    self.validation_results.append(ValidationResult(
                        category="deployment",
                        check_name="render_yaml_structure",
                        status="pass",
                        message="render.yaml has valid structure with services"
                    ))

                    # Check for required service types
                    service_types = [service.get('type') for service in render_data['services']]
                    if 'web' in service_types:
                        self.validation_results.append(ValidationResult(
                            category="deployment",
                            check_name="render_web_service",
                            status="pass",
                            message="Found web service in render.yaml"
                        ))

                else:
                    self.validation_results.append(ValidationResult(
                        category="deployment",
                        check_name="render_yaml_structure",
                        status="fail",
                        message="render.yaml missing services section",
                        remediation="Add services section to render.yaml"
                    ))

            except yaml.YAMLError as e:
                self.validation_results.append(ValidationResult(
                    category="deployment",
                    check_name="render_yaml_syntax",
                    status="fail",
                    message=f"render.yaml has invalid syntax: {str(e)}",
                    remediation="Fix YAML syntax errors in render.yaml"
                ))
            except Exception as e:
                self.validation_results.append(ValidationResult(
                    category="deployment",
                    check_name="render_yaml_readable",
                    status="fail",
                    message=f"Cannot read render.yaml: {str(e)}"
                ))
        elif env_config.name == "production":
            self.validation_results.append(ValidationResult(
                category="deployment",
                check_name="render_yaml_missing",
                status="warning",
                message="render.yaml not found for production environment",
                remediation="Create render.yaml for Render.com deployment"
            ))

    async def _load_environment_variables(self, config_files: List[str]) -> Dict[str, str]:
        """Load environment variables from config files.

        Args:
            config_files: List of configuration files to load

        Returns:
            Dictionary of environment variables
        """
        env_vars = dict(os.environ)  # Start with system environment

        repo_root = self.get_repository_root()
        if not repo_root:
            return env_vars

        for config_file in config_files:
            file_path = repo_root / config_file
            if file_path.exists() and file_path.suffix in ['.env', '']:
                try:
                    with open(file_path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#') and '=' in line:
                                key, value = line.split('=', 1)
                                env_vars[key.strip()] = value.strip().strip('"\'')
                except Exception as e:
                    logger.warning(f"Failed to load environment file {config_file}: {e}")

        return env_vars

    def generate_validation_report(self, environment: str) -> ValidationReport:
        """Create comprehensive validation report.

        Args:
            environment: Target environment

        Returns:
            Comprehensive validation report
        """
        # Calculate summary statistics
        summary = {
            "pass": len([r for r in self.validation_results if r.status == "pass"]),
            "fail": len([r for r in self.validation_results if r.status == "fail"]),
            "warning": len([r for r in self.validation_results if r.status == "warning"]),
            "skip": len([r for r in self.validation_results if r.status == "skip"])
        }

        # Determine overall status
        if summary["fail"] > 0:
            overall_status = "fail"
        elif summary["warning"] > 0:
            overall_status = "warning"
        else:
            overall_status = "pass"

        # Determine deployment readiness
        critical_failures = [
            r for r in self.validation_results
            if r.status == "fail" and r.category in ["environment_variables", "secrets", "database"]
        ]
        deployment_ready = len(critical_failures) == 0

        # Generate recommendations
        recommendations = []

        if summary["fail"] > 0:
            recommendations.append(f"Resolve {summary['fail']} critical issues before deployment")

        if summary["warning"] > 0:
            recommendations.append(f"Consider addressing {summary['warning']} warnings for optimal configuration")

        # Add specific recommendations based on failures
        failed_categories = set(r.category for r in self.validation_results if r.status == "fail")
        if "secrets" in failed_categories:
            recommendations.append("Configure all required secrets and ensure they are strong")

        if "external_services" in failed_categories:
            recommendations.append("Verify external service configurations and connectivity")

        if "database" in failed_categories:
            recommendations.append("Fix database configuration and connectivity issues")

        if deployment_ready:
            recommendations.append("Environment appears ready for deployment")

        return ValidationReport(
            timestamp=datetime.now().isoformat(),
            environment=environment,
            overall_status=overall_status,
            summary=summary,
            results=self.validation_results,
            recommendations=recommendations,
            deployment_ready=deployment_ready
        )

    async def execute_action(self, action: str, **kwargs) -> Dict[str, Any]:
        """Handle remediation actions.

        Args:
            action: Action to execute
            **kwargs: Action parameters

        Returns:
            Action execution results
        """
        try:
            if action == "generate_env_template":
                return await self._generate_env_template(kwargs.get("environment", "development"))

            elif action == "validate_environment":
                environment = kwargs.get("environment", "development")
                return await self.analyze(environment=environment)

            elif action == "check_deployment_readiness":
                environment = kwargs.get("environment", "production")
                result = await self.analyze(environment=environment)
                return {
                    "deployment_ready": result.get("deployment_ready", False),
                    "critical_issues": [
                        r for r in result.get("report", {}).get("results", [])
                        if r.get("status") == "fail"
                    ]
                }

            elif action == "generate_config_checklist":
                environment = kwargs.get("environment", "development")
                env_config = self.environment_configs.get(environment)
                if not env_config:
                    return {"error": f"Unknown environment: {environment}"}

                return {
                    "environment": environment,
                    "required_variables": env_config.required_vars,
                    "optional_variables": env_config.optional_vars,
                    "config_files": env_config.config_files,
                    "required_services": env_config.services
                }

            else:
                return {
                    "error": f"Unknown action: {action}",
                    "available_actions": [
                        "generate_env_template",
                        "validate_environment",
                        "check_deployment_readiness",
                        "generate_config_checklist"
                    ]
                }

        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return {
                "error": str(e),
                "action": action
            }

    async def _generate_env_template(self, environment: str) -> Dict[str, Any]:
        """Generate environment variable template.

        Args:
            environment: Target environment

        Returns:
            Environment template
        """
        env_config = self.environment_configs.get(environment)
        if not env_config:
            return {"error": f"Unknown environment: {environment}"}

        template_lines = [
            f"# Environment configuration for {environment}",
            f"# Generated on {datetime.now().isoformat()}",
            "",
            "# Required Variables",
        ]

        for var in env_config.required_vars:
            if var == "JWT_SECRET_KEY":
                template_lines.append(f"{var}=your-secure-jwt-secret-min-32-chars")
            elif var == "DATABASE_URL":
                template_lines.append(f"{var}=postgresql://username:password@localhost/database_name")
            elif var == "REDIS_URL":
                template_lines.append(f"{var}=redis://localhost:6379")
            elif "API_KEY" in var:
                template_lines.append(f"{var}=your-api-key-here")
            else:
                template_lines.append(f"{var}=")

        template_lines.extend([
            "",
            "# Optional Variables",
        ])

        for var in env_config.optional_vars:
            template_lines.append(f"# {var}=")

        return {
            "environment": environment,
            "template": "\n".join(template_lines),
            "filename": f".env.{environment}.template"
        }
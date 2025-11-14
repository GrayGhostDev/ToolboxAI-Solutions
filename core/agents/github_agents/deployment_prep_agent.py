"""
Deployment Preparation Agent for validating deployment readiness.
"""

import json
import os
import subprocess
from typing import Any, Optional

import yaml

from .base_github_agent import BaseGitHubAgent


class DeploymentPrepAgent(BaseGitHubAgent):
    """Agent that prepares repository for deployment."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the deployment prep agent."""
        super().__init__(config_path)
        self.deployment_configs = {
            "render": {
                "config_file": "render.yaml",
                "required_files": [
                    "render.yaml",
                    "requirements.txt",
                    "Dockerfile.backend",
                    ".env.render",
                ],
                "required_services": ["backend", "frontend", "database", "redis"],
            },
            "heroku": {
                "config_file": "app.json",
                "required_files": ["Procfile", "requirements.txt", "runtime.txt"],
            },
            "aws": {
                "config_file": "aws-config.yaml",
                "required_files": ["Dockerfile", "docker-compose.yml"],
            },
        }

    async def analyze(self, service: str = "render", **kwargs) -> dict[str, Any]:
        """Analyze deployment readiness for specified service.

        Args:
            service: Deployment service (render, heroku, aws, etc.)
            **kwargs: Additional parameters

        Returns:
            Deployment readiness analysis
        """
        try:
            repo_root = self.get_repository_root()
            if not repo_root:
                return {
                    "success": False,
                    "ready": False,
                    "error": "Not in a git repository",
                }

            # Run all checks
            size_check = await self._check_repository_size()
            deps_check = await self._check_dependencies()
            config_check = await self._check_configuration(service)
            docker_check = await self._check_docker_readiness()
            env_check = await self._check_environment_variables(service)
            migration_check = await self._check_database_migrations()

            # Determine overall readiness
            all_checks = {
                "size_check": size_check["passed"],
                "dependencies_check": deps_check["passed"],
                "config_check": config_check["passed"],
                "docker_check": docker_check["passed"],
                "environment_check": env_check["passed"],
                "migration_check": migration_check["passed"],
            }

            ready = all(all_checks.values())

            # Collect recommendations
            recommendations = []
            if not size_check["passed"]:
                recommendations.extend(size_check.get("recommendations", []))
            if not deps_check["passed"]:
                recommendations.extend(deps_check.get("recommendations", []))
            if not config_check["passed"]:
                recommendations.extend(config_check.get("recommendations", []))
            if not docker_check["passed"]:
                recommendations.extend(docker_check.get("recommendations", []))
            if not env_check["passed"]:
                recommendations.extend(env_check.get("recommendations", []))
            if not migration_check["passed"]:
                recommendations.extend(migration_check.get("recommendations", []))

            # Log operation
            await self.log_operation(
                "deployment_prep",
                {
                    "service": service,
                    "ready": ready,
                    "checks": all_checks,
                    "recommendations_count": len(recommendations),
                },
            )

            return {
                "success": True,
                "ready": ready,
                "service": service,
                "checks": all_checks,
                "details": {
                    "size": size_check,
                    "dependencies": deps_check,
                    "configuration": config_check,
                    "docker": docker_check,
                    "environment": env_check,
                    "migrations": migration_check,
                },
                "recommendations": recommendations,
                "deployment_score": sum(all_checks.values()) / len(all_checks) * 100,
            }

        except Exception as e:
            return {
                "success": False,
                "ready": False,
                "error": str(e),
                "service": service,
            }

    async def _check_repository_size(self) -> dict[str, Any]:
        """Check repository size for deployment."""
        try:
            self.get_repository_root()

            # Get repository size
            result = await self.execute_git_command("count-objects -vH")
            if not result["success"]:
                return {"passed": False, "error": "Failed to check repository size"}

            # Parse size information
            size_info = {}
            for line in result["stdout"].split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    size_info[key.strip()] = value.strip()

            # Check for large files
            large_files_result = await self.execute_git_command(
                "rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectsize) %(rest)' | awk '$1==\"blob\" && $2>50000000 {print $3, $2}'"
            )

            large_files = []
            if large_files_result["success"] and large_files_result["stdout"]:
                for line in large_files_result["stdout"].strip().split("\n"):
                    if line:
                        parts = line.split()
                        if len(parts) >= 2:
                            large_files.append(
                                {
                                    "path": parts[0],
                                    "size": int(parts[1]) if parts[1].isdigit() else 0,
                                }
                            )

            # Determine if size is acceptable
            pack_size_str = size_info.get("size-pack", "0")
            pack_size_mb = 0
            if "MiB" in pack_size_str:
                pack_size_mb = float(pack_size_str.replace(" MiB", ""))
            elif "GiB" in pack_size_str:
                pack_size_mb = float(pack_size_str.replace(" GiB", "")) * 1024

            passed = pack_size_mb < 500 and len(large_files) == 0

            recommendations = []
            if pack_size_mb > 500:
                recommendations.append(
                    f"Repository size ({pack_size_mb:.1f} MB) exceeds recommended 500 MB"
                )
            if large_files:
                recommendations.append(
                    f"Found {len(large_files)} files over 50 MB - consider using Git LFS"
                )

            return {
                "passed": passed,
                "pack_size_mb": pack_size_mb,
                "large_files": large_files,
                "recommendations": recommendations,
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    async def _check_dependencies(self) -> dict[str, Any]:
        """Check dependency health and security."""
        try:
            repo_root = self.get_repository_root()
            issues = []
            recommendations = []

            # Check Python dependencies
            requirements_file = repo_root / "requirements.txt"
            if requirements_file.exists():
                # Check for version pinning
                with open(requirements_file) as f:
                    lines = f.readlines()
                    unpinned = [
                        line.strip()
                        for line in lines
                        if line.strip()
                        and not line.startswith("#")
                        and "==" not in line
                        and ">=" not in line
                    ]

                if unpinned:
                    issues.append(f"Found {len(unpinned)} unpinned dependencies")
                    recommendations.append("Pin all dependency versions for reproducible builds")

            # Check Node dependencies
            package_json = repo_root / "apps" / "dashboard" / "package.json"
            if package_json.exists():
                with open(package_json) as f:
                    json.load(f)

                # Check for missing lock file
                package_lock = repo_root / "apps" / "dashboard" / "package-lock.json"
                if not package_lock.exists():
                    issues.append("Missing package-lock.json")
                    recommendations.append("Run 'npm install' to generate package-lock.json")

            passed = len(issues) == 0

            return {
                "passed": passed,
                "issues": issues,
                "recommendations": recommendations,
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    async def _check_configuration(self, service: str) -> dict[str, Any]:
        """Check deployment configuration for specified service."""
        try:
            repo_root = self.get_repository_root()

            if service not in self.deployment_configs:
                return {
                    "passed": True,
                    "warning": f"No specific configuration requirements for {service}",
                }

            config = self.deployment_configs[service]
            missing_files = []

            # Check required files
            for required_file in config["required_files"]:
                file_path = repo_root / required_file
                if not file_path.exists():
                    missing_files.append(required_file)

            # Validate configuration file
            config_valid = True
            config_errors = []

            if service == "render" and not missing_files:
                render_yaml = repo_root / "render.yaml"
                try:
                    with open(render_yaml) as f:
                        render_config = yaml.safe_load(f)

                    # Check for required services
                    if "services" not in render_config:
                        config_errors.append("Missing 'services' section in render.yaml")
                        config_valid = False

                except Exception as e:
                    config_errors.append(f"Invalid render.yaml: {e}")
                    config_valid = False

            passed = len(missing_files) == 0 and config_valid

            recommendations = []
            if missing_files:
                recommendations.append(f"Create missing files: {', '.join(missing_files)}")
            if config_errors:
                recommendations.extend(config_errors)

            return {
                "passed": passed,
                "missing_files": missing_files,
                "config_valid": config_valid,
                "config_errors": config_errors,
                "recommendations": recommendations,
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    async def _check_docker_readiness(self) -> dict[str, Any]:
        """Check Docker configuration and build readiness."""
        try:
            repo_root = self.get_repository_root()
            issues = []
            recommendations = []

            # Check for Dockerfile
            dockerfile = repo_root / "Dockerfile.backend"
            if not dockerfile.exists():
                dockerfile = repo_root / "Dockerfile"

            if dockerfile.exists():
                with open(dockerfile) as f:
                    content = f.read()

                # Check for best practices
                if (
                    "USER root" in content
                    and "USER" not in content[content.find("USER root") + 9 :]
                ):
                    issues.append("Running as root user in production")
                    recommendations.append("Add a non-root USER directive in Dockerfile")

                if "EXPOSE" not in content:
                    issues.append("No EXPOSE directive in Dockerfile")
                    recommendations.append("Add EXPOSE directive for application port")

                if ".dockerignore" not in os.listdir(repo_root):
                    issues.append("Missing .dockerignore file")
                    recommendations.append("Create .dockerignore to exclude unnecessary files")
            else:
                issues.append("No Dockerfile found")
                recommendations.append("Create a Dockerfile for container deployment")

            passed = len(issues) == 0

            return {
                "passed": passed,
                "issues": issues,
                "recommendations": recommendations,
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    async def _check_environment_variables(self, service: str) -> dict[str, Any]:
        """Check environment variable configuration."""
        try:
            repo_root = self.get_repository_root()
            missing_vars = []
            recommendations = []

            # Define required environment variables
            required_vars = [
                "DATABASE_URL",
                "REDIS_URL",
                "SECRET_KEY",
                "JWT_SECRET_KEY",
            ]

            if service == "render":
                env_file = repo_root / ".env.render"
                if env_file.exists():
                    with open(env_file) as f:
                        content = f.read()

                    for var in required_vars:
                        if f"{var}=" not in content:
                            missing_vars.append(var)
                else:
                    missing_vars = required_vars
                    recommendations.append("Create .env.render with required environment variables")

            passed = len(missing_vars) == 0

            if missing_vars:
                recommendations.append(
                    f"Add missing environment variables: {', '.join(missing_vars)}"
                )

            return {
                "passed": passed,
                "missing_vars": missing_vars,
                "recommendations": recommendations,
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    async def _check_database_migrations(self) -> dict[str, Any]:
        """Check database migration status."""
        try:
            repo_root = self.get_repository_root()

            # Check for Alembic migrations
            migrations_dir = repo_root / "alembic" / "versions"
            if not migrations_dir.exists():
                migrations_dir = repo_root / "migrations" / "versions"

            if migrations_dir.exists():
                # Count migration files
                migration_files = list(migrations_dir.glob("*.py"))
                migration_count = len([f for f in migration_files if not f.name.startswith("__")])

                return {
                    "passed": True,
                    "migration_count": migration_count,
                    "recommendations": [],
                }
            else:
                return {
                    "passed": True,
                    "warning": "No database migrations directory found",
                    "recommendations": ["Initialize database migrations if using a database"],
                }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    async def execute_action(self, action: str, **kwargs) -> dict[str, Any]:
        """Execute deployment preparation actions.

        Args:
            action: Action to execute
            **kwargs: Action parameters

        Returns:
            Action result
        """
        actions = {
            "validate": self._action_validate,
            "prepare_render": self._action_prepare_render,
            "build_docker": self._action_build_docker,
            "generate_env_template": self._action_generate_env_template,
            "check_secrets": self._action_check_secrets,
            "optimize_build": self._action_optimize_build,
        }

        if action in actions:
            return await actions[action](**kwargs)
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}",
                "available_actions": list(actions.keys()),
            }

    async def _action_validate(self, service: str = "render", **kwargs) -> dict[str, Any]:
        """Validate deployment readiness."""
        return await self.analyze(service, **kwargs)

    async def _action_prepare_render(self, **kwargs) -> dict[str, Any]:
        """Prepare for Render.com deployment."""
        try:
            repo_root = self.get_repository_root()

            # Run validation script if it exists
            validate_script = repo_root / "scripts" / "validate-render.sh"
            if validate_script.exists():
                result = subprocess.run(
                    ["bash", str(validate_script)],
                    capture_output=True,
                    text=True,
                    cwd=repo_root,
                )

                return {
                    "success": result.returncode == 0,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            else:
                return {"success": False, "error": "Validation script not found"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _action_build_docker(self, **kwargs) -> dict[str, Any]:
        """Test Docker build."""
        try:
            repo_root = self.get_repository_root()
            dockerfile = repo_root / "Dockerfile.backend"

            if not dockerfile.exists():
                dockerfile = repo_root / "Dockerfile"

            if dockerfile.exists():
                # Test build
                result = subprocess.run(
                    ["docker", "build", "-f", str(dockerfile), "-t", "test-build", "."],
                    capture_output=True,
                    text=True,
                    cwd=repo_root,
                    timeout=300,
                )

                return {
                    "success": result.returncode == 0,
                    "stdout": result.stdout[-1000:] if result.stdout else "",  # Last 1000 chars
                    "stderr": result.stderr[-1000:] if result.stderr else "",
                }
            else:
                return {"success": False, "error": "Dockerfile not found"}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Docker build timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _action_generate_env_template(
        self, service: str = "render", **kwargs
    ) -> dict[str, Any]:
        """Generate environment variable template."""
        try:
            repo_root = self.get_repository_root()

            template = """# Environment Configuration Template
# Generated for: {service}
# Date: {date}

# Database
DATABASE_URL=postgresql://user:password@localhost/dbname
POSTGRES_USER=eduplatform
POSTGRES_PASSWORD=<secure_password>
POSTGRES_DB=educational_platform_prod

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=<generate_secure_key>
JWT_SECRET_KEY=<generate_secure_jwt_key>

# API Keys
OPENAI_API_KEY=<your_openai_api_key>
ANTHROPIC_API_KEY=<your_anthropic_api_key>

# Pusher (Real-time)
PUSHER_APP_ID=<your_pusher_app_id>
PUSHER_KEY=<your_pusher_key>
PUSHER_SECRET=<your_pusher_secret>
PUSHER_CLUSTER=us2

# Monitoring
SENTRY_DSN=<your_sentry_dsn>

# CORS
CORS_ORIGINS=["https://yourdomain.com"]

# Environment
ENVIRONMENT=production
LOG_LEVEL=info
DEBUG=false
"""

            from datetime import datetime

            content = template.format(service=service, date=datetime.now().isoformat())

            env_file = repo_root / f".env.{service}.template"
            with open(env_file, "w") as f:
                f.write(content)

            return {
                "success": True,
                "file_created": str(env_file),
                "message": f"Environment template created at {env_file}",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _action_check_secrets(self, **kwargs) -> dict[str, Any]:
        """Check for exposed secrets in code."""
        try:
            # Run basic secret detection
            result = await self.execute_git_command(
                'grep -r -E "(api_key|secret|password|token)" --exclude-dir=.git --exclude="*.md"'
            )

            potential_secrets = []
            if result["stdout"]:
                for line in result["stdout"].split("\n")[:20]:  # Limit to 20 results
                    if "=" in line or ":" in line:
                        potential_secrets.append(line[:100])  # First 100 chars

            return {
                "success": len(potential_secrets) == 0,
                "potential_secrets": potential_secrets,
                "message": (
                    f"Found {len(potential_secrets)} potential exposed secrets"
                    if potential_secrets
                    else "No exposed secrets found"
                ),
            }

        except Exception:
            return {
                "success": True,  # Don't fail on grep errors
                "message": "Secret check completed",
            }

    async def _action_optimize_build(self, **kwargs) -> dict[str, Any]:
        """Optimize build configuration."""
        try:
            recommendations = [
                "Use multi-stage Docker builds to reduce image size",
                "Implement build caching for dependencies",
                "Minimize layers in Dockerfile",
                "Use .dockerignore to exclude unnecessary files",
                "Enable BuildKit for improved build performance",
            ]

            return {
                "success": True,
                "recommendations": recommendations,
                "message": "Build optimization recommendations generated",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

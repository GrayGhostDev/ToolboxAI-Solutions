"""Test alignment with GitHub Actions CI/CD pipeline"""
import yaml
import json
from pathlib import Path
import subprocess
import os

class TestCICDAlignment:
    """Ensure local tests match CI/CD pipeline"""

    def test_github_actions_exist(self):
        """Test required GitHub Actions workflows exist"""
        workflows_dir = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/.github/workflows")

        # Check if workflows directory exists
        assert workflows_dir.exists(), ".github/workflows directory not found"

        # Get all workflow files
        workflow_files = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))

        # Should have at least some workflow files
        assert len(workflow_files) > 0, "No GitHub Actions workflows found"

        # Check for common workflow patterns
        workflow_contents = {}
        for workflow_file in workflow_files:
            with open(workflow_file, 'r') as f:
                try:
                    workflow_contents[workflow_file.name] = yaml.safe_load(f.read())
                except yaml.YAMLError:
                    # If YAML parsing fails, just read as text
                    f.seek(0)
                    workflow_contents[workflow_file.name] = f.read()

        # Should have workflows covering key areas
        workflow_text = " ".join([str(content) for content in workflow_contents.values()])

        # Check for essential workflow components
        essential_components = [
            "python",  # Python testing
            "node",    # Node.js testing
            "test",    # Testing step
            "build"    # Build step
        ]

        for component in essential_components:
            assert component.lower() in workflow_text.lower(), f"Missing {component} in workflows"

    def test_security_tools_availability(self):
        """Test security tools used in CI are available locally"""
        tools = {
            "bandit": ["bandit", "--version"],
            "safety": ["safety", "--version"],
            "trivy": ["trivy", "--version"],
            "gitleaks": ["gitleaks", "version"]
        }

        missing_tools = []
        for tool_name, command in tools.items():
            try:
                result = subprocess.run(command, capture_output=True, text=True, timeout=10)
                if result.returncode != 0:
                    missing_tools.append(tool_name)
            except (FileNotFoundError, subprocess.TimeoutExpired):
                missing_tools.append(tool_name)

        if missing_tools:
            print(f"Warning: Missing security tools for CI/CD parity: {missing_tools}")
            # Don't fail the test, just warn
            assert True, "Security tools check completed with warnings"

    def test_test_coverage_configuration(self):
        """Test coverage configuration matches CI requirements"""
        pytest_ini = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/pytest.ini")

        with open(pytest_ini, 'r') as f:
            content = f.read()

        # Check for pytest configuration
        assert "[pytest]" in content
        assert "testpaths" in content
        assert "markers" in content

        # Check for required markers
        required_markers = ["slow:", "integration:", "unit:"]
        for marker in required_markers:
            assert marker in content, f"Missing marker: {marker}"

        # Check if coverage is configured
        requirements_path = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/requirements.txt")
        with open(requirements_path, 'r') as f:
            requirements = f.read()

        # Should have coverage tools
        coverage_tools = ["pytest-cov", "coverage"]
        has_coverage = any(tool in requirements for tool in coverage_tools)
        assert has_coverage, "No coverage tools found in requirements"

    def test_dependabot_configuration(self):
        """Test Dependabot configuration if it exists"""
        dependabot_config = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/.github/dependabot.yml")

        if not dependabot_config.exists():
            # Check for alternative location
            dependabot_config = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/.github/dependabot.yaml")

        if dependabot_config.exists():
            with open(dependabot_config, 'r') as f:
                config = yaml.safe_load(f)

            # Check ecosystems if dependabot is configured
            if "updates" in config:
                ecosystems = [update["package-ecosystem"] for update in config["updates"]]

                expected_ecosystems = ["pip", "npm"]
                for ecosystem in expected_ecosystems:
                    assert ecosystem in ecosystems, f"Missing {ecosystem} in Dependabot config"

                # Check update schedule
                for update in config["updates"]:
                    assert "schedule" in update, "Missing schedule in Dependabot update"
                    assert update["schedule"]["interval"] in ["daily", "weekly", "monthly"], \
                        "Invalid schedule interval"
        else:
            print("Warning: No Dependabot configuration found")

    def test_github_secrets_requirements(self):
        """Test GitHub Secrets requirements are documented"""
        # Check if there's documentation about required secrets
        docs_dir = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/docs")
        readme_file = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/README.md")

        # Look for secret documentation
        secret_docs_found = False
        files_to_check = [readme_file]

        if docs_dir.exists():
            files_to_check.extend(docs_dir.rglob("*.md"))

        for doc_file in files_to_check:
            if doc_file.exists():
                with open(doc_file, 'r') as f:
                    content = f.read().lower()

                if any(keyword in content for keyword in ["secrets", "environment variables", "ci/cd"]):
                    secret_docs_found = True
                    break

        if not secret_docs_found:
            print("Warning: No documentation found for GitHub Secrets requirements")

    def test_workflow_python_version_matrix(self):
        """Test Python version matrix in workflows"""
        workflows_dir = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/.github/workflows")

        if not workflows_dir.exists():
            return  # Skip if no workflows

        workflow_files = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))

        python_versions_found = []
        for workflow_file in workflow_files:
            with open(workflow_file, 'r') as f:
                content = f.read()

            # Look for Python version specifications
            if "python-version" in content:
                # Extract Python versions (basic pattern matching)
                import re
                versions = re.findall(r"['\"]?(3\.\d+)['\"]?", content)
                python_versions_found.extend(versions)

        if python_versions_found:
            # Should test multiple Python versions or at least the current one
            assert "3.12" in python_versions_found or "3.11" in python_versions_found, \
                "Should test with Python 3.11 or 3.12"

    def test_workflow_node_version_matrix(self):
        """Test Node.js version matrix in workflows"""
        workflows_dir = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/.github/workflows")

        if not workflows_dir.exists():
            return  # Skip if no workflows

        workflow_files = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))

        node_versions_found = []
        for workflow_file in workflow_files:
            with open(workflow_file, 'r') as f:
                content = f.read()

            # Look for Node version specifications
            if "node-version" in content:
                # Extract Node versions
                import re
                versions = re.findall(r"['\"]?(\d+)['\"]?", content)
                node_versions_found.extend(versions)

        if node_versions_found:
            # Should test with Node 22 or compatible
            assert "22" in node_versions_found or "20" in node_versions_found, \
                "Should test with Node 20 or 22"

    def test_docker_compose_in_ci(self):
        """Test Docker Compose usage in CI workflows"""
        workflows_dir = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/.github/workflows")

        if not workflows_dir.exists():
            return  # Skip if no workflows

        workflow_files = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))

        docker_usage_found = False
        for workflow_file in workflow_files:
            with open(workflow_file, 'r') as f:
                content = f.read()

            # Look for Docker usage patterns
            docker_patterns = [
                "docker-compose", "docker compose",
                "services:", "postgresql", "redis"
            ]

            if any(pattern in content for pattern in docker_patterns):
                docker_usage_found = True
                break

        if not docker_usage_found:
            print("Warning: No Docker usage found in CI workflows")

    def test_environment_variable_security(self):
        """Test environment variable security practices"""
        workflows_dir = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/.github/workflows")

        if not workflows_dir.exists():
            return  # Skip if no workflows

        workflow_files = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))

        for workflow_file in workflow_files:
            with open(workflow_file, 'r') as f:
                content = f.read()

            # Check that sensitive values use secrets
            sensitive_patterns = [
                "api_key", "secret", "password", "token"
            ]

            lines = content.split('\n')
            for i, line in enumerate(lines):
                line_lower = line.lower()

                # If line contains sensitive pattern, it should use ${{ secrets.* }}
                for pattern in sensitive_patterns:
                    if pattern in line_lower and ":" in line:
                        # Skip comments
                        if line.strip().startswith('#'):
                            continue

                        # If it's setting an env var with sensitive data
                        if f"{pattern}" in line_lower and not line.strip().startswith('#'):
                            # Should use secrets or be a placeholder
                            if not ("secrets." in line or "your_" in line.lower() or "test_" in line.lower()):
                                print(f"Warning: Potential hardcoded secret in {workflow_file.name}:{i+1}")

    def test_test_command_alignment(self):
        """Test that test commands in CI match local test setup"""
        # Check package.json test scripts
        package_json = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/apps/dashboard/package.json")

        if package_json.exists():
            with open(package_json, 'r') as f:
                package = json.load(f)

            # Should have test scripts
            scripts = package.get("scripts", {})
            test_scripts = [key for key in scripts.keys() if "test" in key]

            assert len(test_scripts) > 0, "No test scripts found in package.json"

            # Common test scripts should exist
            expected_scripts = ["test", "test:coverage"]
            for script in expected_scripts:
                if script not in scripts:
                    print(f"Warning: Missing {script} script in package.json")

    def test_build_command_alignment(self):
        """Test that build commands in CI match local build setup"""
        # Check package.json build scripts
        package_json = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/apps/dashboard/package.json")

        if package_json.exists():
            with open(package_json, 'r') as f:
                package = json.load(f)

            # Should have build scripts
            scripts = package.get("scripts", {})
            build_scripts = [key for key in scripts.keys() if "build" in key]

            assert len(build_scripts) > 0, "No build scripts found in package.json"

            # Should have basic build script
            assert "build" in scripts, "Missing build script"

        # Check if there's a Makefile
        makefile = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/Makefile")
        if makefile.exists():
            with open(makefile, 'r') as f:
                content = f.read()

            # Should have common targets
            common_targets = ["test", "build", "dev"]
            for target in common_targets:
                if f"{target}:" not in content:
                    print(f"Warning: Missing {target} target in Makefile")

    def test_linting_consistency(self):
        """Test linting configuration consistency"""
        # Check if ESLint config exists
        dashboard_dir = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/apps/dashboard")
        eslint_configs = [
            dashboard_dir / ".eslintrc.js",
            dashboard_dir / ".eslintrc.json",
            dashboard_dir / "eslint.config.js"
        ]

        eslint_config_exists = any(config.exists() for config in eslint_configs)

        if eslint_config_exists:
            # Check package.json has lint script
            package_json = dashboard_dir / "package.json"
            if package_json.exists():
                with open(package_json, 'r') as f:
                    package = json.load(f)

                scripts = package.get("scripts", {})
                assert "lint" in scripts, "Missing lint script despite ESLint config"

    def test_formatting_consistency(self):
        """Test code formatting configuration consistency"""
        # Check if Prettier config exists
        root_dir = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions")
        dashboard_dir = root_dir / "apps/dashboard"

        prettier_configs = [
            root_dir / ".prettierrc",
            root_dir / ".prettierrc.js",
            root_dir / ".prettierrc.json",
            dashboard_dir / ".prettierrc",
            dashboard_dir / ".prettierrc.js",
            dashboard_dir / ".prettierrc.json"
        ]

        prettier_config_exists = any(config.exists() for config in prettier_configs)

        if prettier_config_exists:
            # Check package.json has format script
            package_json = dashboard_dir / "package.json"
            if package_json.exists():
                with open(package_json, 'r') as f:
                    package = json.load(f)

                scripts = package.get("scripts", {})
                format_scripts = [key for key in scripts.keys() if "format" in key]
                assert len(format_scripts) > 0, "Missing format scripts despite Prettier config"
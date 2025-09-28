"""Project standards compliance tests"""
import pytest
from pathlib import Path
import json
import yaml

class TestProjectStandards:
    """Test compliance with project standards"""

    def test_required_files_exist(self):
        """Test that required project files exist"""
        project_root = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions")

        required_files = [
            "README.md",
            "requirements.txt",
            "pytest.ini",
            ".gitignore",
            ".env.example",
            "apps/dashboard/package.json"
        ]

        missing_files = []
        for file_path in required_files:
            full_path = project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)

        assert not missing_files, f"Missing required files: {missing_files}"

    def test_version_consistency(self):
        """Test version consistency across files"""
        project_root = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions")

        # Check Python version
        python_version_file = project_root / ".python-version"
        if python_version_file.exists():
            with open(python_version_file, 'r') as f:
                python_version = f.read().strip()

            # Should be a valid Python version
            assert python_version.startswith("3."), f"Invalid Python version: {python_version}"
            assert len(python_version.split(".")) >= 2, f"Incomplete Python version: {python_version}"

        # Check Node version
        nvmrc_file = project_root / ".nvmrc"
        if nvmrc_file.exists():
            with open(nvmrc_file, 'r') as f:
                node_version = f.read().strip()

            # Should be a valid Node version
            assert node_version.isdigit() and int(node_version) >= 18, f"Invalid Node version: {node_version}"

    def test_package_json_validity(self):
        """Test package.json files are valid"""
        project_root = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions")

        package_json_files = [
            project_root / "package.json",
            project_root / "apps/dashboard/package.json"
        ]

        for package_file in package_json_files:
            if package_file.exists():
                try:
                    with open(package_file, 'r') as f:
                        package_data = json.load(f)

                    # Should have required fields
                    assert "name" in package_data, f"Missing 'name' in {package_file}"
                    assert "version" in package_data, f"Missing 'version' in {package_file}"

                    # Version should follow semver
                    version = package_data["version"]
                    version_parts = version.split(".")
                    assert len(version_parts) >= 3, f"Invalid version format in {package_file}: {version}"

                except json.JSONDecodeError as e:
                    pytest.fail(f"Invalid JSON in {package_file}: {e}")

    def test_docker_compose_validity(self):
        """Test Docker Compose files are valid"""
        project_root = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions")

        compose_files = [
            project_root / "infrastructure/docker/docker-compose.dev.yml",
            project_root / "docker-compose.yml"
        ]

        for compose_file in compose_files:
            if compose_file.exists():
                try:
                    with open(compose_file, 'r') as f:
                        compose_data = yaml.safe_load(f)

                    # Should have required structure
                    assert "services" in compose_data, f"Missing 'services' in {compose_file}"
                    assert len(compose_data["services"]) > 0, f"No services defined in {compose_file}"

                except yaml.YAMLError as e:
                    pytest.fail(f"Invalid YAML in {compose_file}: {e}")

    def test_gitignore_completeness(self):
        """Test .gitignore covers common patterns"""
        project_root = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions")

        gitignore_file = project_root / ".gitignore"
        assert gitignore_file.exists(), ".gitignore file is missing"

        with open(gitignore_file, 'r') as f:
            gitignore_content = f.read()

        # Should ignore common patterns
        required_patterns = [
            "node_modules",
            "*.pyc",
            "__pycache__",
            ".env",
            "*.log"
        ]

        missing_patterns = []
        for pattern in required_patterns:
            if pattern not in gitignore_content:
                missing_patterns.append(pattern)

        assert not missing_patterns, f"Missing .gitignore patterns: {missing_patterns}"

    def test_environment_template_completeness(self):
        """Test .env.example is comprehensive"""
        project_root = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions")

        env_example_file = project_root / ".env.example"
        assert env_example_file.exists(), ".env.example file is missing"

        with open(env_example_file, 'r') as f:
            env_content = f.read()

        # Should contain key sections
        required_sections = [
            "DATABASE",
            "REDIS",
            "JWT",
            "PUSHER"
        ]

        for section in required_sections:
            assert section in env_content, f"Missing {section} configuration in .env.example"

        # Should have security warnings
        security_keywords = ["NEVER commit", "secure", "production"]
        has_security_warning = any(keyword.lower() in env_content.lower() for keyword in security_keywords)
        assert has_security_warning, "Missing security warnings in .env.example"

    def test_test_structure_compliance(self):
        """Test test directory structure follows standards"""
        project_root = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions")

        tests_dir = project_root / "tests"
        assert tests_dir.exists(), "tests directory is missing"

        # Should have standard test directories
        expected_dirs = ["unit", "integration", "performance"]

        for expected_dir in expected_dirs:
            dir_path = tests_dir / expected_dir
            if not dir_path.exists():
                print(f"Warning: Missing standard test directory: {expected_dir}")

        # Should have pytest configuration
        pytest_ini = project_root / "pytest.ini"
        assert pytest_ini.exists(), "pytest.ini is missing"

    def test_documentation_standards(self):
        """Test documentation follows standards"""
        project_root = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions")

        readme_file = project_root / "README.md"
        assert readme_file.exists(), "README.md is missing"

        with open(readme_file, 'r', encoding='utf-8') as f:
            readme_content = f.read()

        # Should contain key sections
        readme_lower = readme_content.lower()
        expected_sections = ["installation", "usage", "development"]

        missing_sections = []
        for section in expected_sections:
            if section not in readme_lower:
                missing_sections.append(section)

        if missing_sections:
            print(f"Warning: README.md might be missing sections: {missing_sections}")

    def test_dependency_security(self):
        """Test for basic dependency security practices"""
        project_root = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions")

        # Check if there's a requirements.lock or similar
        lock_files = [
            project_root / "requirements.lock",
            project_root / "poetry.lock",
            project_root / "apps/dashboard/package-lock.json"
        ]

        has_lock_file = any(lock_file.exists() for lock_file in lock_files)
        assert has_lock_file, "No dependency lock files found - this is a security risk"

    def test_code_quality_tools_configured(self):
        """Test code quality tools are configured"""
        project_root = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions")

        # Python code quality
        python_quality_files = [
            project_root / "pyproject.toml",
            project_root / ".bandit",
            project_root / "mypy.ini"
        ]

        python_quality_configured = any(file.exists() for file in python_quality_files)
        if not python_quality_configured:
            print("Warning: No Python code quality tools configured")

        # JavaScript/TypeScript code quality
        js_quality_files = [
            project_root / "apps/dashboard/.eslintrc.js",
            project_root / "apps/dashboard/.eslintrc.json",
            project_root / "apps/dashboard/tsconfig.json"
        ]

        js_quality_configured = any(file.exists() for file in js_quality_files)
        if not js_quality_configured:
            print("Warning: No JavaScript/TypeScript code quality tools configured")

    def test_ci_cd_configuration_exists(self):
        """Test CI/CD configuration exists"""
        project_root = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions")

        ci_dirs = [
            project_root / ".github/workflows",
            project_root / ".gitlab-ci.yml",
            project_root / "azure-pipelines.yml"
        ]

        has_ci_config = any(
            (path.exists() and (path.is_file() or (path.is_dir() and any(path.iterdir()))))
            for path in ci_dirs
        )

        if not has_ci_config:
            print("Warning: No CI/CD configuration found")
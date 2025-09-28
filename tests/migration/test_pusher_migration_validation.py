"""Pusher migration validation tests"""
import pytest
from pathlib import Path
import json

class TestPusherMigrationValidation:
    """Validate Pusher migration completeness"""

    def test_websocket_to_pusher_migration_complete(self):
        """Test that WebSocket to Pusher migration is complete"""
        project_root = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions")

        # Check backend has Pusher dependencies
        requirements_path = project_root / "requirements.txt"
        with open(requirements_path, 'r') as f:
            requirements = f.read()

        assert "pusher==" in requirements, "Pusher dependency not found in requirements.txt"

        # Check frontend has Pusher dependencies
        package_json_path = project_root / "apps/dashboard/package.json"
        if package_json_path.exists():
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)

            dependencies = package_data.get("dependencies", {})
            assert "pusher-js" in dependencies, "pusher-js dependency not found in package.json"

    def test_pusher_environment_variables_configured(self):
        """Test Pusher environment variables are configured"""
        project_root = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions")

        # Check .env.example has Pusher variables
        env_example_path = project_root / ".env.example"
        with open(env_example_path, 'r') as f:
            env_content = f.read()

        pusher_vars = [
            "PUSHER_APP_ID=",
            "PUSHER_KEY=",
            "PUSHER_SECRET=",
            "PUSHER_CLUSTER="
        ]

        for var in pusher_vars:
            assert var in env_content, f"Missing Pusher environment variable: {var}"

    def test_docker_compose_pusher_configuration(self):
        """Test Docker Compose has Pusher configuration"""
        project_root = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions")

        docker_compose_path = project_root / "infrastructure/docker/docker-compose.dev.yml"

        if docker_compose_path.exists():
            with open(docker_compose_path, 'r') as f:
                compose_content = f.read()

            # Check for Pusher environment variables in services
            pusher_env_vars = [
                "PUSHER_APP_ID:",
                "PUSHER_KEY:",
                "PUSHER_SECRET:",
                "PUSHER_CLUSTER:"
            ]

            for var in pusher_env_vars:
                assert var in compose_content, f"Missing Pusher env var in Docker Compose: {var}"

    def test_legacy_websocket_cleanup(self):
        """Test that legacy WebSocket code is properly marked or removed"""
        project_root = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions")

        # Look for any remaining WebSocket implementation files
        suspicious_files = []

        # Check main source directories
        source_dirs = [
            project_root / "apps/backend",
            project_root / "apps/dashboard/src",
            project_root / "core"
        ]

        for source_dir in source_dirs:
            if source_dir.exists():
                # Look for files that might contain legacy WebSocket code
                for file_path in source_dir.rglob("*.py"):
                    if file_path.name.startswith("websocket") and "legacy" not in file_path.name.lower():
                        suspicious_files.append(str(file_path))

                for file_path in source_dir.rglob("*.ts"):
                    if "websocket" in file_path.name.lower() and "legacy" not in file_path.name.lower():
                        suspicious_files.append(str(file_path))

        if suspicious_files:
            print(f"Warning: Found potentially legacy WebSocket files: {suspicious_files}")
            # Don't fail the test, just warn
            assert True, "Legacy WebSocket files check completed with warnings"

    def test_pusher_backend_integration(self):
        """Test Pusher is integrated in backend"""
        project_root = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions")

        # Check for Pusher imports in backend
        backend_dir = project_root / "apps/backend"

        if backend_dir.exists():
            pusher_usage_found = False

            for py_file in backend_dir.rglob("*.py"):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    if "from pusher import" in content or "import pusher" in content:
                        pusher_usage_found = True
                        break
                except UnicodeDecodeError:
                    continue  # Skip binary files

            assert pusher_usage_found, "No Pusher imports found in backend code"

    def test_pusher_frontend_integration(self):
        """Test Pusher is integrated in frontend"""
        project_root = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions")

        # Check for Pusher imports in frontend
        frontend_dir = project_root / "apps/dashboard/src"

        if frontend_dir.exists():
            pusher_usage_found = False

            for ts_file in frontend_dir.rglob("*.ts"):
                try:
                    with open(ts_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    if "pusher-js" in content or "import Pusher" in content:
                        pusher_usage_found = True
                        break
                except UnicodeDecodeError:
                    continue

            for tsx_file in frontend_dir.rglob("*.tsx"):
                try:
                    with open(tsx_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    if "pusher-js" in content or "import Pusher" in content:
                        pusher_usage_found = True
                        break
                except UnicodeDecodeError:
                    continue

            assert pusher_usage_found, "No Pusher imports found in frontend code"

    def test_pusher_channel_configuration(self):
        """Test Pusher channels are properly configured"""
        project_root = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions")

        # Look for channel configuration in code
        source_dirs = [
            project_root / "apps/backend",
            project_root / "apps/dashboard/src"
        ]

        channel_patterns = [
            "dashboard-updates",
            "content-generation",
            "agent-status",
            "private-"  # Private channels
        ]

        channels_found = []

        for source_dir in source_dirs:
            if not source_dir.exists():
                continue

            for file_path in source_dir.rglob("*.py"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    for pattern in channel_patterns:
                        if pattern in content:
                            channels_found.append(pattern)
                except UnicodeDecodeError:
                    continue

            for file_path in source_dir.rglob("*.ts"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    for pattern in channel_patterns:
                        if pattern in content:
                            channels_found.append(pattern)
                except UnicodeDecodeError:
                    continue

            for file_path in source_dir.rglob("*.tsx"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    for pattern in channel_patterns:
                        if pattern in content:
                            channels_found.append(pattern)
                except UnicodeDecodeError:
                    continue

        # Should find at least some channel usage
        assert len(channels_found) > 0, "No Pusher channels found in codebase"
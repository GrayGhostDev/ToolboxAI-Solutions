"""
Shared pytest fixtures and configuration for backup system tests.

This module provides common fixtures, mocks, and utilities used across
all backup system tests.
"""

import asyncio
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

# ============================================================================
# Pytest Configuration
# ============================================================================


def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "requires_db: mark test as requiring database")
    config.addinivalue_line("markers", "requires_tools: mark test as requiring external tools")


# ============================================================================
# Event Loop Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def event_loop_policy():
    """Set event loop policy for async tests."""
    return asyncio.get_event_loop_policy()


@pytest.fixture(scope="function")
async def async_context():
    """Provide async context for tests."""
    yield
    # Cleanup any remaining async tasks
    pending = asyncio.all_tasks()
    for task in pending:
        task.cancel()


# ============================================================================
# Temporary Directory Fixtures
# ============================================================================


@pytest.fixture
def temp_dir():
    """Create temporary directory for test isolation."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def backup_test_dir(temp_dir):
    """Create backup-specific test directory structure."""
    backup_dir = temp_dir / "backups"
    backup_dir.mkdir()

    metadata_dir = backup_dir / "metadata"
    metadata_dir.mkdir()

    logs_dir = backup_dir / "logs"
    logs_dir.mkdir()

    return {"root": backup_dir, "metadata": metadata_dir, "logs": logs_dir}


# ============================================================================
# Mock Configuration Fixtures
# ============================================================================


@pytest.fixture
def mock_backup_config(temp_dir):
    """Standard mock backup configuration."""
    return {
        "version": "1.0.0",
        "backup_strategies": {
            "full": {"enabled": True, "schedule": "0 2 * * 0", "retention_days": 30},
            "incremental": {
                "enabled": True,
                "schedule": "0 2 * * 1-6",
                "retention_days": 7,
            },
        },
        "encryption": {
            "enabled": True,
            "algorithm": "AES-256-GCM",
            "key_rotation_days": 90,
        },
        "storage": {
            "local": {
                "path": str(temp_dir / "backups"),
                "enabled": True,
                "max_size_gb": 500,
            }
        },
        "databases": {
            "postgresql": {
                "host": "localhost",
                "port": 5432,
                "database": "test_db",
                "user": "test_user",
                "backup_format": "custom",
                "compress_level": 9,
                "parallel_jobs": 4,
            }
        },
        "compression": {"enabled": True, "algorithm": "gzip", "level": 9},
        "validation": {"enabled": True, "checksum_algorithm": "SHA256"},
        "monitoring": {"prometheus_enabled": True, "prometheus_port": 9090},
        "rto_minutes": 30,
        "rpo_minutes": 60,
    }


# ============================================================================
# Mock Database Fixtures
# ============================================================================


@pytest.fixture
def mock_database_url():
    """Mock database connection URL."""
    return "postgresql://test_user:test_pass@localhost:5432/test_db"


@pytest.fixture
def mock_database_credentials():
    """Mock database credentials dictionary."""
    return {
        "host": "localhost",
        "port": "5432",
        "user": "test_user",
        "password": "test_pass",
        "database": "test_db",
    }


# ============================================================================
# Mock Subprocess Fixtures
# ============================================================================


@pytest.fixture
def mock_pg_dump_success():
    """Mock successful pg_dump subprocess."""
    mock_process = AsyncMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"pg_dump success", b""))
    return mock_process


@pytest.fixture
def mock_pg_dump_failure():
    """Mock failing pg_dump subprocess."""
    mock_process = AsyncMock()
    mock_process.returncode = 1
    mock_process.communicate = AsyncMock(return_value=(b"", b"pg_dump error: connection failed"))
    return mock_process


@pytest.fixture
def mock_pg_restore_success():
    """Mock successful pg_restore subprocess."""
    mock_process = AsyncMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"pg_restore success", b""))
    return mock_process


@pytest.fixture
def mock_pg_restore_failure():
    """Mock failing pg_restore subprocess."""
    mock_process = AsyncMock()
    mock_process.returncode = 1
    mock_process.communicate = AsyncMock(return_value=(b"", b"pg_restore error: invalid backup"))
    return mock_process


# ============================================================================
# Mock Backup Metadata Fixtures
# ============================================================================


@pytest.fixture
def sample_backup_metadata():
    """Sample backup metadata for testing."""
    return {
        "backup_id": "backup_full_20250110_120000",
        "backup_type": "full",
        "timestamp": datetime.now().isoformat(),
        "database_name": "test_db",
        "file_path": "/backups/backup_full_20250110_120000.dump",
        "file_size": 1024 * 1024 * 100,  # 100 MB
        "checksum": "abc123def456789",
        "encrypted": True,
        "compressed": True,
        "status": "completed",
        "duration_seconds": 120.5,
        "retention_until": "2025-02-10T12:00:00",
    }


@pytest.fixture
def multiple_backup_metadata():
    """Multiple backup metadata entries for testing."""
    base_time = datetime.now()

    return [
        {
            "backup_id": f"backup_full_{i:03d}",
            "backup_type": "full",
            "timestamp": (base_time - timedelta(days=i)).isoformat(),
            "database_name": "test_db",
            "file_path": f"/backups/backup_full_{i:03d}.dump",
            "file_size": 1024 * 1024 * 100,
            "checksum": f"checksum_{i}",
            "encrypted": True,
            "compressed": True,
            "status": "completed",
            "duration_seconds": 120.0,
            "retention_until": (base_time + timedelta(days=30 - i)).isoformat(),
        }
        for i in range(5)
    ]


# ============================================================================
# Mock Environment Fixtures
# ============================================================================


@pytest.fixture
def mock_environment():
    """Mock environment variables for testing."""
    env_vars = {
        "DATABASE_URL": "postgresql://test_user:test_pass@localhost:5432/test_db",
        "REDIS_URL": "redis://localhost:6379/0",
        "BACKUP_ENCRYPTION_KEY": "test_key_32_bytes_long_for_fernet!",
        "BACKUP_ALERT_EMAIL": "alerts@example.com",
    }

    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


# ============================================================================
# Mock File System Fixtures
# ============================================================================


@pytest.fixture
def mock_backup_file(temp_dir):
    """Create mock backup file for testing."""
    backup_file = temp_dir / "test_backup.dump"
    backup_content = b"Mock backup data" * 1000  # ~16KB
    backup_file.write_bytes(backup_content)

    return {"path": backup_file, "content": backup_content, "size": len(backup_content)}


# ============================================================================
# Helper Functions
# ============================================================================


def create_test_backup_file(directory: Path, backup_id: str, content: bytes = None) -> Path:
    """
    Create a test backup file.

    Args:
        directory: Directory to create file in
        backup_id: Backup identifier
        content: File content (default: mock data)

    Returns:
        Path to created file
    """
    if content is None:
        content = f"Mock backup data for {backup_id}".encode() * 100

    backup_file = directory / f"{backup_id}.dump"
    backup_file.write_bytes(content)

    return backup_file


def create_test_metadata(directory: Path, backup_id: str, **kwargs) -> Path:
    """
    Create test metadata file.

    Args:
        directory: Metadata directory
        backup_id: Backup identifier
        **kwargs: Additional metadata fields

    Returns:
        Path to created metadata file
    """
    import json

    metadata = {
        "backup_id": backup_id,
        "backup_type": "full",
        "timestamp": datetime.now().isoformat(),
        "database_name": "test_db",
        "file_path": f"/backups/{backup_id}.dump",
        "file_size": 1024 * 1024,
        "checksum": "test_checksum",
        "encrypted": False,
        "compressed": False,
        "status": "completed",
        "duration_seconds": 60.0,
        "retention_until": "2025-12-31T23:59:59",
    }

    # Override with provided kwargs
    metadata.update(kwargs)

    metadata_file = directory / f"{backup_id}.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)

    return metadata_file


# ============================================================================
# Performance Fixtures
# ============================================================================


@pytest.fixture
def performance_timer():
    """Timer for performance testing."""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()

        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None

    return Timer()


# ============================================================================
# Pytest Hooks
# ============================================================================


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Auto-mark tests based on filename
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)

        # Mark async tests
        if asyncio.iscoroutinefunction(item.obj):
            item.add_marker(pytest.mark.asyncio)

        # Mark slow tests (integration tests are usually slow)
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.slow)

"""Simplified root conftest.py for pytest.

This is a refactored version of conftest.py that organizes fixtures into
focused modules for better maintainability and discoverability.

Fixture modules:
- fixtures/async_helpers.py: Event loop and async utilities
- fixtures/auth.py: Authentication and rate limiting
- fixtures/cleanup.py: Cleanup and teardown utilities
- fixtures/database.py: Database fixtures (existing)
- fixtures/api.py: API client fixtures (existing)
- fixtures/agents.py: AI agent fixtures (existing)
- fixtures/common.py: Common utilities (existing)
"""

import os
import sys
from pathlib import Path

import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ============================================
# Import fixtures from organized modules
# ============================================

# Import all fixtures from the fixtures package
from fixtures.agents import *  # noqa: F401, F403
from fixtures.api import *  # noqa: F401, F403
from fixtures.async_helpers import *  # noqa: F401, F403
from fixtures.auth import *  # noqa: F401, F403
from fixtures.cleanup import *  # noqa: F401, F403
from fixtures.common import *  # noqa: F401, F403
from fixtures.database import *  # noqa: F401, F403

# Import specialized fixtures if they exist
try:
    from fixtures.pusher_mocks import *  # noqa: F401, F403
except ImportError:
    pass

try:
    from fixtures.docker_test_helper import *  # noqa: F401, F403
except ImportError:
    pass

# ============================================
# Pytest Configuration
# ============================================


def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    # Register custom markers
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "security: Security tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "requires_db: Tests that require database")
    config.addinivalue_line("markers", "requires_redis: Tests that require Redis")
    config.addinivalue_line("markers", "requires_docker: Tests that require Docker")

    # Set test environment
    os.environ["TESTING"] = "true"
    os.environ["ENVIRONMENT"] = "test"

    # Use test database
    if "DATABASE_URL" in os.environ:
        # Replace database name with test database
        db_url = os.environ["DATABASE_URL"]
        if "educational_platform_dev" in db_url:
            os.environ["DATABASE_URL"] = db_url.replace(
                "educational_platform_dev", "educational_platform_test"
            )

    # Disable external service calls during tests
    os.environ["DISABLE_EXTERNAL_CALLS"] = "true"
    os.environ["USE_MOCK_LLM"] = "true"


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add markers based on test file location
        if "/unit/" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "/integration/" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "/e2e/" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        elif "/performance/" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        elif "/security/" in str(item.fspath):
            item.add_marker(pytest.mark.security)

        # Skip slow tests in CI unless explicitly requested
        if item.get_closest_marker("slow"):
            if os.environ.get("CI") and not os.environ.get("RUN_SLOW_TESTS"):
                item.add_marker(pytest.mark.skip("Skipping slow test in CI"))

        # Skip tests requiring external services unless enabled
        if item.get_closest_marker("requires_docker"):
            if not os.environ.get("DOCKER_AVAILABLE"):
                item.add_marker(pytest.mark.skip("Docker not available"))


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Run slow tests",
    )
    parser.addoption(
        "--run-e2e",
        action="store_true",
        default=False,
        help="Run end-to-end tests",
    )
    parser.addoption(
        "--run-performance",
        action="store_true",
        default=False,
        help="Run performance tests",
    )
    parser.addoption(
        "--run-security",
        action="store_true",
        default=False,
        help="Run security tests",
    )


def pytest_runtest_setup(item):
    """Setup test run based on markers and options."""
    # Check for conditional test execution based on command line options
    if item.get_closest_marker("slow"):
        if not item.config.getoption("--run-slow"):
            pytest.skip("Need --run-slow option to run")

    if item.get_closest_marker("e2e"):
        if not item.config.getoption("--run-e2e"):
            pytest.skip("Need --run-e2e option to run")

    if item.get_closest_marker("performance"):
        if not item.config.getoption("--run-performance"):
            pytest.skip("Need --run-performance option to run")

    if item.get_closest_marker("security"):
        if not item.config.getoption("--run-security"):
            pytest.skip("Need --run-security option to run")


# ============================================
# Session-level fixtures
# ============================================


@pytest.fixture(scope="session", autouse=True)
def test_environment():
    """Setup test environment for the entire test session."""
    # Save original environment
    original_env = os.environ.copy()

    # Set test environment variables
    test_env = {
        "TESTING": "true",
        "ENVIRONMENT": "test",
        "LOG_LEVEL": "WARNING",
        "DISABLE_EXTERNAL_CALLS": "true",
        "USE_MOCK_LLM": "true",
        "BYPASS_RATE_LIMIT_IN_TESTS": "true",
        "DATABASE_POOL_SIZE": "5",
        "DATABASE_MAX_OVERFLOW": "10",
    }

    os.environ.update(test_env)

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# ============================================
# Hooks for better test reporting
# ============================================


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Make test result available to fixtures."""
    outcome = yield
    report = outcome.get_result()

    # Make report available to fixtures
    setattr(item, f"rep_{report.when}", report)


def pytest_sessionstart(session):
    """Called at the start of the test session."""
    print("\n" + "=" * 70)
    print("Starting ToolBoxAI Test Suite")
    print(f"Python: {sys.version}")
    print(f"Test Directory: {session.config.rootdir}")
    print("=" * 70 + "\n")


def pytest_sessionfinish(session, exitstatus):
    """Called at the end of the test session."""
    print("\n" + "=" * 70)
    print("Test Session Complete")
    print(f"Exit Status: {exitstatus}")
    print("=" * 70 + "\n")


# ============================================
# Pytest plugins
# ============================================

# Load pytest plugins
pytest_plugins = [
    "pytest_asyncio",
    "pytest_timeout",
]

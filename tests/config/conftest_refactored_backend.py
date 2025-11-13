"""
Test configuration for refactored backend tests

This file contains shared fixtures and configuration for testing
the refactored backend application.
"""

import asyncio
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Set testing environment variables
os.environ["TESTING"] = "true"
os.environ["SKIP_LIFESPAN"] = "true"
os.environ["ENVIRONMENT"] = "test"

# Import after setting environment
from apps.backend.core.app_factory import create_app, create_test_app
from apps.backend.main import app as main_app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_app() -> FastAPI:
    """Create a test FastAPI application"""
    return create_test_app()


@pytest.fixture
def main_test_app() -> FastAPI:
    """Provide the main application for testing"""
    return main_app


@pytest.fixture
def test_client(test_app) -> TestClient:
    """Create a test client for the test app"""
    return TestClient(test_app)


@pytest.fixture
def main_test_client(main_test_app) -> TestClient:
    """Create a test client for the main app"""
    return TestClient(main_test_app)


@pytest.fixture
def mock_pusher_service():
    """Mock Pusher service for testing"""
    with (
        patch("apps.backend.services.pusher.trigger_event") as mock_trigger,
        patch("apps.backend.services.pusher.authenticate_channel") as mock_auth,
        patch("apps.backend.services.pusher.verify_webhook") as mock_webhook,
    ):

        # Configure mock responses
        mock_trigger.return_value = {"channels": {"public": {}}, "event_id": "test_123"}
        mock_auth.return_value = {"auth": "test_auth_string"}
        mock_webhook.return_value = [{"name": "test_event", "data": {}}]

        yield {"trigger": mock_trigger, "auth": mock_auth, "webhook": mock_webhook}


@pytest.fixture
def mock_agent_service():
    """Mock agent service for testing"""
    with patch("apps.backend.agents.agent.generate_educational_content") as mock_generate:
        mock_generate.return_value = {
            "content": "Test educational content",
            "topic": "test topic",
            "metadata": {"generated_by": "test_agent"},
        }

        yield mock_generate


@pytest.fixture
def mock_database():
    """Mock database connections for testing"""
    with (
        patch("apps.backend.core.database.get_session") as mock_session,
        patch("apps.backend.core.database.get_async_session") as mock_async_session,
    ):

        # Create mock sessions
        mock_db_session = MagicMock()
        mock_async_db_session = MagicMock()

        mock_session.return_value = mock_db_session
        mock_async_session.return_value = mock_async_db_session

        yield {"session": mock_db_session, "async_session": mock_async_db_session}


@pytest.fixture
def mock_redis():
    """Mock Redis connection for testing"""
    with patch("apps.backend.core.redis.get_redis_client") as mock_redis_client:
        mock_client = MagicMock()

        # Configure common Redis operations
        mock_client.get.return_value = None
        mock_client.set.return_value = True
        mock_client.exists.return_value = False
        mock_client.delete.return_value = 1

        mock_redis_client.return_value = mock_client

        yield mock_client


@pytest.fixture
def temp_config_file():
    """Create a temporary configuration file for testing"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write(
            """
TESTING=true
SKIP_LIFESPAN=true
DATABASE_URL=sqlite:///test.db
REDIS_URL=redis://localhost:6379/15
SECRET_KEY=test_secret_key_for_testing_only
ENVIRONMENT=test
APP_NAME=ToolboxAI Test
APP_VERSION=1.0.0-test
        """
        )
        f.flush()

        yield f.name

    # Cleanup
    os.unlink(f.name)


@pytest.fixture
def performance_monitor():
    """Fixture for performance monitoring"""
    from tests.test_refactored_backend_performance import PerformanceMetrics

    return PerformanceMetrics()


@pytest.fixture
def mock_external_services():
    """Mock all external services for isolated testing"""
    with (
        patch("apps.backend.services.pusher.PusherClient") as mock_pusher,
        patch("apps.backend.core.monitoring.sentry_sdk") as mock_sentry,
        patch("apps.backend.services.openai.OpenAI") as mock_openai,
    ):

        # Configure mocks
        mock_pusher_instance = MagicMock()
        mock_pusher.return_value = mock_pusher_instance
        mock_pusher_instance.trigger.return_value = {"event_id": "test_123"}

        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance

        yield {
            "pusher": mock_pusher_instance,
            "sentry": mock_sentry,
            "openai": mock_openai_instance,
        }


@pytest.fixture(scope="function")
def isolated_app():
    """Create a completely isolated app instance for testing"""
    app = create_app(
        skip_lifespan=True,
        skip_sentry=True,
        testing_mode=True,
        title="Isolated Test App",
        version="test",
    )

    yield app

    # Cleanup if needed
    if hasattr(app, "state") and hasattr(app.state, "cleanup"):
        app.state.cleanup()


@pytest.fixture
def mock_auth_user():
    """Mock authenticated user for testing protected endpoints"""
    from apps.backend.models.schemas import User

    mock_user = User(
        id=123, username="test_user", email="test@example.com", role="teacher", is_active=True
    )

    with patch("apps.backend.api.auth.auth.get_current_user") as mock_get_user:
        mock_get_user.return_value = mock_user
        yield mock_user


@pytest.fixture
def benchmark_context():
    """Context manager for benchmarking test operations"""
    import time
    from contextlib import contextmanager

    @contextmanager
    def benchmark(operation_name: str):
        start_time = time.perf_counter()
        try:
            yield
        finally:
            end_time = time.perf_counter()
            duration = end_time - start_time
            print(f"\n{operation_name}: {duration:.3f}s")

    return benchmark


# Test markers
pytest_plugins = ["pytest_asyncio"]


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "performance: mark test as a performance test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "requires_redis: mark test as requiring Redis")
    config.addinivalue_line("markers", "requires_database: mark test as requiring database")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names"""
    for item in items:
        # Add performance marker to performance tests
        if "performance" in item.nodeid.lower():
            item.add_marker(pytest.mark.performance)

        # Add slow marker to tests that might be slow
        if any(keyword in item.nodeid.lower() for keyword in ["load", "stress", "concurrent"]):
            item.add_marker(pytest.mark.slow)

        # Add integration marker to integration tests
        if "integration" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)


# Skip conditions for certain environments
skip_if_no_redis = pytest.mark.skipif(not os.environ.get("REDIS_URL"), reason="Redis not available")

skip_if_no_database = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"), reason="Database not available"
)

skip_performance_tests = pytest.mark.skipif(
    os.environ.get("SKIP_PERFORMANCE_TESTS", "false").lower() == "true",
    reason="Performance tests disabled",
)


# Custom test utilities
class TestUtils:
    """Utility functions for testing"""

    @staticmethod
    def assert_response_format(response_data: dict, expected_status: str = "success"):
        """Assert that response follows expected format"""
        assert "status" in response_data
        assert response_data["status"] == expected_status

        if expected_status == "success":
            assert "data" in response_data or "message" in response_data

    @staticmethod
    def assert_health_response(response_data: dict):
        """Assert that health response has required fields"""
        required_fields = ["status", "timestamp", "version", "environment"]
        for field in required_fields:
            assert field in response_data, f"Health response missing {field}"

        assert response_data["status"] in ["healthy", "unhealthy"]

    @staticmethod
    def assert_performance_acceptable(duration: float, max_duration: float, operation: str):
        """Assert that operation completed within acceptable time"""
        assert (
            duration < max_duration
        ), f"{operation} took {duration:.3f}s, should be < {max_duration}s"


@pytest.fixture
def test_utils():
    """Provide test utilities"""
    return TestUtils


# Environment setup and teardown
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment before running tests"""
    # Ensure test environment variables are set
    os.environ.setdefault("TESTING", "true")
    os.environ.setdefault("SKIP_LIFESPAN", "true")
    os.environ.setdefault("ENVIRONMENT", "test")

    # Setup test database if needed
    # This would typically create test tables, etc.

    yield

    # Cleanup after all tests
    # This would typically clean up test data, temp files, etc.


@pytest.fixture(autouse=True)
def reset_environment_per_test():
    """Reset environment state for each test"""
    # Store original environment
    original_env = os.environ.copy()

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)

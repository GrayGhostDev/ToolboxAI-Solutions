"""
Chaos Engineering Test Configuration

Provides fixtures and configuration for safe chaos engineering testing.
Includes safety mechanisms, isolation, and cleanup procedures.
"""

import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import redis.asyncio as redis_async

# Import test utilities

logger = logging.getLogger(__name__)


class ChaosTestSafetyManager:
    """Manages safety mechanisms for chaos engineering tests"""

    def __init__(self):
        self.safety_enabled = True
        self.max_test_duration = 600  # 10 minutes maximum
        self.test_start_time: float | None = None
        self.emergency_stop_triggered = False
        self.active_patches = []

    def start_test(self):
        """Start test with safety monitoring"""
        self.test_start_time = time.time()
        self.emergency_stop_triggered = False
        logger.info("Chaos test started with safety monitoring")

    def check_safety_limits(self):
        """Check if test should be emergency stopped"""
        if not self.test_start_time:
            return

        elapsed = time.time() - self.test_start_time
        if elapsed > self.max_test_duration:
            self.emergency_stop_triggered = True
            logger.error(f"Emergency stop triggered - test exceeded {self.max_test_duration}s")

    def cleanup_patches(self):
        """Cleanup all active patches"""
        for patch_obj in self.active_patches:
            try:
                patch_obj.stop()
            except Exception as e:
                logger.warning(f"Failed to stop patch: {e}")
        self.active_patches.clear()

    def add_patch(self, patch_obj):
        """Track a patch for cleanup"""
        self.active_patches.append(patch_obj)


@pytest.fixture(scope="session")
def chaos_test_config():
    """Global configuration for chaos tests"""
    return {
        "max_duration": int(os.getenv("CHAOS_MAX_DURATION", "300")),
        "safety_enabled": os.getenv("CHAOS_SAFETY_ENABLED", "true").lower() == "true",
        "mock_external": os.getenv("CHAOS_MOCK_EXTERNAL", "true").lower() == "true",
        "isolated_environment": os.getenv("CHAOS_ISOLATED", "true").lower() == "true",
        "enable_monitoring": os.getenv("CHAOS_MONITORING", "true").lower() == "true",
    }


@pytest.fixture
def chaos_safety_manager():
    """Fixture providing safety management for chaos tests"""
    manager = ChaosTestSafetyManager()
    manager.start_test()

    yield manager

    # Cleanup after test
    manager.cleanup_patches()


@pytest.fixture
async def isolated_redis():
    """Provide isolated Redis instance for chaos testing"""
    # Use test database that can be safely corrupted
    test_redis = await redis_async.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=15,  # Use test database
        decode_responses=True,
    )

    # Clear test database before use
    await test_redis.flushdb()

    yield test_redis

    # Cleanup after test
    await test_redis.flushdb()
    await test_redis.close()


@pytest.fixture
def mock_external_services():
    """Mock external services to prevent real failures during testing"""
    mocks = {}

    # Mock HTTP client
    http_patch = patch("httpx.AsyncClient")
    mock_http = http_patch.start()
    mock_http.return_value.get.return_value.json.return_value = {"mocked": True}
    mocks["http"] = mock_http

    # Mock database connections
    db_patch = patch("asyncpg.connect")
    mock_db = db_patch.start()
    mock_db.return_value = MagicMock()
    mocks["database"] = mock_db

    # Mock WebSocket connections
    ws_patch = patch("websockets.connect")
    mock_ws = ws_patch.start()
    mock_ws.return_value = MagicMock()
    mocks["websocket"] = mock_ws

    # Mock system monitoring
    cpu_patch = patch("psutil.cpu_percent")
    mock_cpu = cpu_patch.start()
    mock_cpu.return_value = 25.0  # Normal CPU usage
    mocks["cpu"] = mock_cpu

    memory_patch = patch("psutil.virtual_memory")
    mock_memory = memory_patch.start()
    mock_memory.return_value.percent = 40.0  # Normal memory usage
    mocks["memory"] = mock_memory

    yield mocks

    # Stop all patches
    http_patch.stop()
    db_patch.stop()
    ws_patch.stop()
    cpu_patch.stop()
    memory_patch.stop()


@pytest.fixture
async def chaos_test_environment(chaos_safety_manager, isolated_redis, mock_external_services):
    """Complete chaos test environment with safety and isolation"""
    environment = {
        "safety_manager": chaos_safety_manager,
        "redis": isolated_redis,
        "mocks": mock_external_services,
        "test_start_time": time.time(),
    }

    # Setup test logging
    logging.getLogger().setLevel(logging.INFO)

    yield environment

    # Safety check before cleanup
    chaos_safety_manager.check_safety_limits()
    if chaos_safety_manager.emergency_stop_triggered:
        logger.error("Emergency stop was triggered during test execution")


@pytest.fixture
def mock_circuit_breakers():
    """Provide mock circuit breakers for testing"""
    from apps.backend.core.circuit_breaker import CircuitBreaker, CircuitBreakerConfig

    # Create test circuit breakers with short timeouts for testing
    breakers = {}

    configs = {
        "database": CircuitBreakerConfig(failure_threshold=2, reset_timeout=5.0),
        "external_api": CircuitBreakerConfig(failure_threshold=3, reset_timeout=10.0),
        "cache": CircuitBreakerConfig(failure_threshold=2, reset_timeout=5.0),
    }

    for name, config in configs.items():
        breakers[name] = CircuitBreaker(name, config)

    yield breakers

    # Reset all circuit breakers after test
    for breaker in breakers.values():
        await breaker.reset()


@pytest.fixture
def mock_rate_limiter():
    """Provide mock rate limiter for testing"""
    from apps.backend.core.security.rate_limit_manager import RateLimitManager

    # Create fresh rate limiter instance for testing
    rate_limiter = RateLimitManager()
    rate_limiter.reset_instance()

    yield rate_limiter

    # Clean up rate limiter state after test
    rate_limiter.request_counts.clear()
    rate_limiter.window_starts.clear()


@pytest.fixture
def monitoring_collector():
    """Collect monitoring data during chaos tests"""
    monitoring_data = {
        "start_time": time.time(),
        "events": [],
        "metrics": [],
        "errors": [],
    }

    def record_event(event_type: str, event_data: dict[str, Any]):
        """Record an event during testing"""
        monitoring_data["events"].append(
            {"timestamp": time.time(), "type": event_type, "data": event_data}
        )

    def record_metric(metric_name: str, value: float):
        """Record a metric during testing"""
        monitoring_data["metrics"].append(
            {"timestamp": time.time(), "name": metric_name, "value": value}
        )

    def record_error(error_type: str, error_message: str):
        """Record an error during testing"""
        monitoring_data["errors"].append(
            {"timestamp": time.time(), "type": error_type, "message": error_message}
        )

    monitoring_data["record_event"] = record_event
    monitoring_data["record_metric"] = record_metric
    monitoring_data["record_error"] = record_error

    yield monitoring_data

    # Log summary after test
    test_duration = time.time() - monitoring_data["start_time"]
    logger.info(f"Chaos test completed in {test_duration:.2f}s")
    logger.info(f"Events recorded: {len(monitoring_data['events'])}")
    logger.info(f"Metrics recorded: {len(monitoring_data['metrics'])}")
    logger.info(f"Errors recorded: {len(monitoring_data['errors'])}")


@pytest.fixture(autouse=True)
def chaos_test_markers(request):
    """Automatically apply safety checks for chaos tests"""
    if "chaos" in request.keywords:
        # Add timeout to chaos tests
        if not hasattr(request.node, "_timeout"):
            request.node._timeout = 300  # 5 minute default timeout

        # Log test start
        logger.info(f"Starting chaos test: {request.node.name}")

    yield

    if "chaos" in request.keywords:
        logger.info(f"Completed chaos test: {request.node.name}")


# Safety hooks
def pytest_runtest_setup(item):
    """Pre-test safety checks"""
    if "chaos" in item.keywords:
        # Verify we're in test environment
        if os.getenv("ENVIRONMENT", "").lower() not in ["test", "chaos_test", "development"]:
            pytest.skip("Chaos tests can only run in test/development environments")

        # Check for required environment variables
        required_vars = ["REDIS_HOST", "DATABASE_URL"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            pytest.skip(f"Missing required environment variables: {missing_vars}")


def pytest_runtest_teardown(item):
    """Post-test safety cleanup"""
    if "chaos" in item.keywords:
        # Ensure no processes are left running
        try:
            import psutil

            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                if "chaos_test" in str(proc.info.get("cmdline", [])):
                    proc.terminate()
        except Exception as e:
            logger.warning(f"Failed to cleanup test processes: {e}")


# Custom markers for chaos tests
def pytest_configure(config):
    """Configure custom markers for chaos tests"""
    config.addinivalue_line("markers", "chaos: mark test as chaos engineering test")
    config.addinivalue_line("markers", "network_chaos: mark test as network chaos test")
    config.addinivalue_line("markers", "resource_chaos: mark test as resource exhaustion test")
    config.addinivalue_line("markers", "database_chaos: mark test as database chaos test")
    config.addinivalue_line("markers", "cache_chaos: mark test as cache chaos test")


# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add timeouts to chaos tests"""
    for item in items:
        if "chaos" in item.keywords:
            # Add timeout marker if not present
            if not any(mark.name == "timeout" for mark in item.iter_markers()):
                item.add_marker(pytest.mark.timeout(300))


@asynccontextmanager
async def temporary_failure_injection(failure_func, duration: float = 10.0):
    """Context manager for temporary failure injection with automatic cleanup"""
    failure_task = None
    try:
        # Start failure injection
        failure_task = asyncio.create_task(failure_func())

        # Let failure run for specified duration
        await asyncio.sleep(duration)

    except Exception as e:
        logger.error(f"Failure injection error: {e}")

    finally:
        # Always cleanup failure injection
        if failure_task and not failure_task.done():
            failure_task.cancel()
            try:
                await failure_task
            except asyncio.CancelledError:
                pass


class ChaosTestValidator:
    """Validates expected behavior during chaos tests"""

    @staticmethod
    async def validate_circuit_breaker_behavior(breaker, expected_state):
        """Validate circuit breaker is in expected state"""
        assert (
            breaker.state == expected_state
        ), f"Circuit breaker state {breaker.state} != expected {expected_state}"

    @staticmethod
    async def validate_rate_limiting_active(rate_limiter, client_id, config):
        """Validate that rate limiting is active and working"""
        # Try to exceed rate limit
        rejected_count = 0
        for _ in range(config.max_requests + 5):
            if not await rate_limiter.check_rate_limit(client_id, config):
                rejected_count += 1

        assert rejected_count > 0, "Rate limiting not active - no requests were rejected"

    @staticmethod
    async def validate_system_recovery(health_check_func, timeout: float = 60.0):
        """Validate that system recovers within timeout"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            if await health_check_func():
                return True
            await asyncio.sleep(1.0)

        assert False, f"System did not recover within {timeout}s"

    @staticmethod
    def validate_performance_degradation(
        baseline_metrics, current_metrics, max_degradation: float = 0.5
    ):
        """Validate that performance degradation is within acceptable limits"""
        for metric_name, baseline_value in baseline_metrics.items():
            if metric_name in current_metrics:
                current_value = current_metrics[metric_name]
                degradation = (current_value - baseline_value) / baseline_value

                assert (
                    degradation <= max_degradation
                ), f"Performance degradation for {metric_name} exceeds limit: {degradation:.2f} > {max_degradation}"

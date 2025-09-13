"""
Pytest configuration and fixtures for the ToolboxAI test suite.

This module provides comprehensive test fixtures and configuration
for proper test isolation, especially for rate limiting state.
"""

import asyncio
import json
import logging
import os
import pytest
import signal
import sys
import tempfile
import threading
from pathlib import Path
from typing import Generator, Dict, Any
from unittest.mock import Mock, patch, AsyncMock

# Import rate limiting components
from apps.backend.core.security.rate_limit_manager import (
    RateLimitManager, 
    RateLimitConfig, 
    RateLimitMode,
    RateLimitTestContext,
    clear_all_rate_limits,
    set_testing_mode
)
from apps.backend.core.config import settings

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def test_environment():
    """Set up test environment variables"""
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["TESTING_MODE"] = "true"
    os.environ["BYPASS_RATE_LIMIT_IN_TESTS"] = "true"
    os.environ["DEBUG"] = "true"
    yield
    # Cleanup after all tests
    os.environ.pop("ENVIRONMENT", None)
    os.environ.pop("TESTING_MODE", None)
    os.environ.pop("BYPASS_RATE_LIMIT_IN_TESTS", None)


@pytest.fixture(scope="function", autouse=True)
def reset_rate_limits():
    """Reset rate limiting state before and after each test"""
    # Before test: reset all rate limit state
    RateLimitManager.reset_instance()
    clear_all_rate_limits()
    set_testing_mode(True)
    
    yield
    
    # After test: clean up rate limit state
    clear_all_rate_limits()
    RateLimitManager.reset_instance()


@pytest.fixture
def rate_limit_context():
    """Provide rate limiting test context"""
    with RateLimitTestContext(bypass=True, clear_on_exit=True) as context:
        yield context


@pytest.fixture
def rate_limit_manager():
    """Provide a fresh rate limit manager for testing"""
    # Reset singleton
    RateLimitManager.reset_instance()
    
    # Create test configuration
    config = RateLimitConfig(
        requests_per_minute=10,  # Low limit for testing
        burst_limit=15,
        window_seconds=60,
        mode=RateLimitMode.TESTING
    )
    
    # Create manager instance
    manager = RateLimitManager.get_instance(config=config)
    manager.set_mode(RateLimitMode.TESTING)
    
    yield manager
    
    # Cleanup
    manager.clear_all_limits()
    RateLimitManager.reset_instance()


@pytest.fixture
def production_rate_limit_manager():
    """Provide a rate limit manager configured for production mode testing"""
    # Reset singleton
    RateLimitManager.reset_instance()
    
    # Create production-like configuration
    config = RateLimitConfig(
        requests_per_minute=5,  # Very low limit for testing
        burst_limit=8,
        window_seconds=30,  # Shorter window for faster tests
        mode=RateLimitMode.PRODUCTION
    )
    
    # Create manager instance
    manager = RateLimitManager.get_instance(config=config)
    manager.set_mode(RateLimitMode.PRODUCTION)
    
    yield manager
    
    # Cleanup
    manager.clear_all_limits()
    RateLimitManager.reset_instance()


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing"""
    mock_redis = Mock()
    mock_redis.ping.return_value = True
    mock_redis.pipeline.return_value.execute.return_value = [None, 0, None, None]
    mock_redis.keys.return_value = []
    mock_redis.delete.return_value = 0
    return mock_redis


@pytest.fixture
def test_client():
    """Create FastAPI test client with proper rate limit isolation"""
    from fastapi.testclient import TestClient
    from apps.backend.main import app
    
    # Clear rate limits before test
    clear_all_rate_limits()
    set_testing_mode(True)
    
    with TestClient(app) as client:
        yield client
        
    # Clear rate limits after test
    clear_all_rate_limits()

# Legacy fixture alias for backward compatibility
@pytest.fixture
def flask_client(test_client):
    """Legacy alias for test_client fixture"""
    return test_client


@pytest.fixture
def sample_plugin_data():
    """Provide sample plugin registration data"""
    return {
        "studio_id": "test-studio-123",
        "port": 64989,
        "version": "1.0.0"
    }


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", 
        "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", 
        "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", 
        "rate_limit: mark test as rate limiting test"
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "benchmark: mark test as a benchmark test"
    )


def pytest_runtest_setup(item):
    """Run setup for each test"""
    # Force rate limit reset for all tests
    RateLimitManager.reset_instance()
    clear_all_rate_limits()
    
    # Set testing mode
    os.environ["TESTING_MODE"] = "true"
    os.environ["BYPASS_RATE_LIMIT_IN_TESTS"] = "true"


def pytest_runtest_teardown(item):
    """Run teardown for each test"""
    # Clean up rate limiting state
    try:
        clear_all_rate_limits()
        RateLimitManager.reset_instance()
    except Exception as e:
        logger.warning(f"Error cleaning up rate limits: {e}")


def pytest_sessionstart(session):
    """Called after the Session object has been created"""
    logger.info("Starting test session with rate limit isolation")
    
    # Ensure clean start
    RateLimitManager.reset_instance()
    clear_all_rate_limits()


def pytest_sessionfinish(session, exitstatus):
    """Called after whole test run finished"""
    logger.info("Test session finished, cleaning up rate limit state")
    
    # Final cleanup
    try:
        clear_all_rate_limits()
        RateLimitManager.reset_instance()
    except Exception as e:
        logger.warning(f"Final cleanup error: {e}")


# Missing fixtures for Roblox integration tests
@pytest.fixture
def mock_websocket():
    """Mock WebSocket for testing real-time communication"""
    class MockWebSocket:
        def __init__(self):
            self.messages = []
            
        async def send(self, message):
            self.messages.append(message)
            
        async def recv(self):
            # Return appropriate mock responses based on sent messages
            if self.messages:
                last_msg = json.loads(self.messages[-1])
                if last_msg.get("type") == "subscribe":
                    return json.dumps({
                        "type": "subscribed",
                        "channel": last_msg.get("channel", "default")
                    })
                elif last_msg.get("type") == "join_lesson":
                    return json.dumps({
                        "type": "lesson_joined",
                        "lesson_id": last_msg.get("lesson_id")
                    })
                elif last_msg.get("type") == "activity_complete":
                    return json.dumps({
                        "type": "peer_progress",
                        "activity_id": last_msg.get("activity_id"),
                        "score": last_msg.get("score")
                    })
            return json.dumps({"type": "default_response"})
            
        async def close(self):
            pass
            
    return MockWebSocket()


@pytest.fixture 
def http_client():
    """Mock HTTP client for testing API requests"""
    from unittest.mock import AsyncMock, MagicMock
    
    class MockResponse:
        def __init__(self, status=200, json_data=None):
            self.status = status
            self._json_data = json_data or {}
            
        async def json(self):
            return self._json_data
            
        async def __aenter__(self):
            return self
            
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
    
    class MockSession:
        def __init__(self):
            pass
            
        def post(self, url, json=None, **kwargs):
            # Return appropriate mock responses based on URL
            if "sync_progress" in url:
                return MockResponse(200, {"status": "synced"})
            elif "publish_to_roblox" in url:
                return MockResponse(200, {"status": "published", "place_url": "https://roblox.com/place/123"})
            elif "upload_asset" in url:
                return MockResponse(200, {"status": "uploaded", "asset_id": "12345"})
            elif "verify_roblox" in url:
                return MockResponse(200, {"verified": True, "access_token": "mock_token"})
            return MockResponse(200, {"success": True})
            
        def get(self, url, **kwargs):
            # Return mock progress data
            if "progress" in url:
                return MockResponse(200, {"progress": 75, "checkpoint": "quiz_started"})
            return MockResponse(200, {"data": "mock_data"})
        
        async def close(self):
            pass
    
    return MockSession()


@pytest.fixture
def agent_cache():
    """Cache fixture for agent performance testing"""
    class MockCache:
        def __init__(self):
            self._cache = {}
            
        async def get(self, key):
            return self._cache.get(key)
            
        async def set(self, key, value):
            self._cache[key] = value
            
        async def clear(self):
            self._cache.clear()
            
    return MockCache()


# Custom test markers
pytestmark = [
    pytest.mark.filterwarnings("ignore::DeprecationWarning"),
    pytest.mark.filterwarnings("ignore::PendingDeprecationWarning")
]


# =============================================================================
# TIMEOUT AND ASYNC HANDLING FIXES
# =============================================================================

@pytest.fixture(scope="function", autouse=True)
def cleanup_async_tasks(request):
    """Clean up any lingering async tasks to prevent hangs"""
    # Setup - ensure clean state
    try:
        # Get or create event loop
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except Exception:
        pass
    
    yield
    
    # Cleanup - cancel all pending tasks
    try:
        loop = asyncio.get_event_loop()
        
        # Cancel all pending tasks
        pending = asyncio.all_tasks(loop) if hasattr(asyncio, 'all_tasks') else asyncio.Task.all_tasks(loop)
        for task in pending:
            task.cancel()
        
        # Wait briefly for cancellation
        if pending and not loop.is_running():
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        
        # Close any open connections
        loop.run_until_complete(asyncio.sleep(0.01))
    except Exception:
        pass  # Ignore errors during cleanup


@pytest.fixture(scope="function", autouse=True)
def mock_external_connections(monkeypatch):
    """Mock external connections that might cause timeouts"""
    
    # Mock Redis connections
    def mock_redis_init(*args, **kwargs):
        mock = Mock()
        mock.ping.return_value = True
        mock.pipeline.return_value.execute.return_value = [None, 0, None, None]
        return mock
    
    # Mock WebSocket connections
    async def mock_websocket_connect(*args, **kwargs):
        mock = AsyncMock()
        mock.send = AsyncMock()
        mock.recv = AsyncMock(return_value='{"type": "pong"}')
        mock.close = AsyncMock()
        return mock
    
    # Mock HTTP session timeouts
    class MockResponse:
        def __init__(self):
            self.status = 200
            self.headers = {}
        
        async def json(self):
            return {"success": True}
        
        async def text(self):
            return "OK"
        
        async def __aenter__(self):
            return self
        
        async def __aexit__(self, *args):
            pass
    
    class MockSession:
        async def get(self, *args, **kwargs):
            return MockResponse()
        
        async def post(self, *args, **kwargs):
            return MockResponse()
        
        async def close(self):
            pass
    
    # Apply mocks conditionally based on test markers
    def apply_mocks(item):
        markers = [m.name for m in item.iter_markers()]
        
        if "requires_redis" not in markers:
            try:
                import redis
                monkeypatch.setattr(redis, "Redis", mock_redis_init)
            except ImportError:
                pass
        
        if "websocket" not in markers:
            try:
                import websockets
                monkeypatch.setattr(websockets, "connect", mock_websocket_connect)
            except ImportError:
                pass
        
        if "integration" not in markers:
            try:
                import aiohttp
                monkeypatch.setattr(aiohttp, "ClientSession", MockSession)
            except ImportError:
                pass
    
    # Store the apply_mocks function for use in collection
    pytest.apply_timeout_mocks = apply_mocks


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add timeout markers and fix async tests"""
    
    for item in items:
        # Apply timeout mocks if available
        if hasattr(pytest, "apply_timeout_mocks"):
            pytest.apply_timeout_mocks(item)
        
        # Add reasonable timeout to all async tests
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.timeout(10))
        
        # Fix async event loop issues
        if "asyncio" in str(item.keywords):
            item.add_marker(pytest.mark.asyncio)


def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--run-all",
        action="store_true",
        default=False,
        help="Run all tests including those that might timeout"
    )


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Set a default timeout for all async operations
    loop.set_debug(False)  # Disable debug mode to improve performance
    
    yield loop
    
    # Cleanup
    try:
        # Cancel all pending tasks
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        # Wait for tasks to complete cancellation
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    except Exception:
        pass
    finally:
        loop.close()





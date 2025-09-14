"""
Common test fixtures for ToolboxAI test suite.

Provides shared fixtures used across multiple test modules.
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json
import yaml
import os
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_file(temp_dir):
    """Create a temporary file for testing."""
    file_path = temp_dir / "test_file.txt"
    file_path.write_text("Test content")
    return file_path


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    env_vars = {
        "DATABASE_URL": "postgresql://test:test@localhost/test_db",
        "REDIS_URL": "redis://localhost:6379/0",
        "SECRET_KEY": "test_secret_key_for_testing_only",
        "DEBUG": "true",
        "OPENAI_API_KEY": "test_openai_key",
        "PUSHER_APP_ID": "test_app_id",
        "PUSHER_KEY": "test_key",
        "PUSHER_SECRET": "test_secret",
        "PUSHER_CLUSTER": "us2",
        "SENTRY_DSN": "",
        "LOG_LEVEL": "DEBUG",
        "CORS_ORIGINS": '["http://localhost:3000", "http://localhost:5179"]',
        "JWT_ALGORITHM": "HS256",
        "JWT_EXPIRATION_HOURS": "24"
    }
    
    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    logger = Mock(spec=logging.Logger)
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.critical = Mock()
    logger.exception = Mock()
    logger.log = Mock()
    logger.setLevel = Mock()
    logger.addHandler = Mock()
    logger.removeHandler = Mock()
    logger.handlers = []
    logger.level = logging.DEBUG
    logger.name = "test_logger"
    return logger


@pytest.fixture
def sample_json_data():
    """Provide sample JSON data for testing."""
    return {
        "metadata": {
            "version": "1.0.0",
            "created_at": datetime.utcnow().isoformat(),
            "author": "test_system"
        },
        "data": {
            "users": [
                {"id": 1, "name": "Alice", "role": "admin"},
                {"id": 2, "name": "Bob", "role": "teacher"},
                {"id": 3, "name": "Charlie", "role": "student"}
            ],
            "settings": {
                "feature_flags": {
                    "new_dashboard": True,
                    "ai_content_generation": True,
                    "realtime_collaboration": False
                },
                "limits": {
                    "max_file_size": 10485760,  # 10MB
                    "max_users_per_class": 30,
                    "max_classes_per_teacher": 10
                }
            }
        }
    }


@pytest.fixture
def sample_yaml_data():
    """Provide sample YAML data for testing."""
    return {
        "application": {
            "name": "ToolboxAI",
            "version": "2.0.0",
            "environment": "test"
        },
        "database": {
            "host": "localhost",
            "port": 5432,
            "name": "test_db",
            "pool_size": 10
        },
        "cache": {
            "type": "redis",
            "ttl": 3600,
            "max_entries": 1000
        },
        "features": [
            "authentication",
            "content_generation",
            "analytics",
            "reporting"
        ]
    }


@pytest.fixture
def mock_datetime():
    """Mock datetime for consistent testing."""
    fixed_datetime = datetime(2025, 9, 14, 12, 0, 0)
    
    with patch('datetime.datetime') as mock_dt:
        mock_dt.utcnow.return_value = fixed_datetime
        mock_dt.now.return_value = fixed_datetime
        mock_dt.today.return_value = fixed_datetime.date()
        mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        yield fixed_datetime


@pytest.fixture
def mock_uuid():
    """Mock UUID generation for consistent testing."""
    fixed_uuid = "12345678-1234-5678-1234-567812345678"
    
    with patch('uuid.uuid4', return_value=fixed_uuid):
        yield fixed_uuid


@pytest.fixture
def mock_random():
    """Mock random for deterministic testing."""
    import random
    
    # Save original state
    original_state = random.getstate()
    
    # Set seed for reproducibility
    random.seed(42)
    
    yield random
    
    # Restore original state
    random.setstate(original_state)


@pytest.fixture
def performance_timer():
    """Timer fixture for performance testing."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.duration = None
        
        def start(self):
            self.start_time = time.perf_counter()
            return self
        
        def stop(self):
            self.end_time = time.perf_counter()
            self.duration = self.end_time - self.start_time
            return self
        
        def __enter__(self):
            self.start()
            return self
        
        def __exit__(self, *args):
            self.stop()
    
    return Timer()


@pytest.fixture
def mock_config():
    """Create a mock configuration object."""
    config = MagicMock()
    config.get = Mock(side_effect=lambda key, default=None: {
        "api_url": "http://localhost:8008",
        "ws_url": "ws://localhost:8008",
        "timeout": 30,
        "retry_count": 3,
        "debug": True,
        "log_level": "DEBUG",
        "cache_enabled": True,
        "cache_ttl": 3600
    }.get(key, default))
    
    config.set = Mock()
    config.update = Mock()
    config.save = Mock()
    config.load = Mock()
    config.reset = Mock()
    
    return config


@pytest.fixture
def mock_cache():
    """Create a mock cache for testing."""
    cache_data = {}
    
    cache = Mock()
    cache.get = Mock(side_effect=lambda key: cache_data.get(key))
    cache.set = Mock(side_effect=lambda key, value, ttl=None: cache_data.update({key: value}))
    cache.delete = Mock(side_effect=lambda key: cache_data.pop(key, None))
    cache.clear = Mock(side_effect=cache_data.clear)
    cache.exists = Mock(side_effect=lambda key: key in cache_data)
    cache.keys = Mock(return_value=list(cache_data.keys()))
    cache.values = Mock(return_value=list(cache_data.values()))
    cache.items = Mock(return_value=list(cache_data.items()))
    
    return cache


@pytest.fixture
def mock_event_emitter():
    """Create a mock event emitter for testing."""
    handlers = {}
    
    emitter = Mock()
    
    def on(event, handler):
        if event not in handlers:
            handlers[event] = []
        handlers[event].append(handler)
    
    def emit(event, *args, **kwargs):
        if event in handlers:
            for handler in handlers[event]:
                handler(*args, **kwargs)
    
    def off(event, handler=None):
        if event in handlers:
            if handler:
                handlers[event].remove(handler)
            else:
                del handlers[event]
    
    emitter.on = Mock(side_effect=on)
    emitter.emit = Mock(side_effect=emit)
    emitter.off = Mock(side_effect=off)
    emitter.once = Mock()
    emitter.listeners = Mock(side_effect=lambda event: handlers.get(event, []))
    emitter.remove_all_listeners = Mock(side_effect=handlers.clear)
    
    return emitter


@pytest.fixture
def mock_metrics():
    """Create a mock metrics collector."""
    metrics_data = {
        "counters": {},
        "gauges": {},
        "histograms": {},
        "timers": {}
    }
    
    metrics = Mock()
    
    def increment(name, value=1, tags=None):
        if name not in metrics_data["counters"]:
            metrics_data["counters"][name] = 0
        metrics_data["counters"][name] += value
    
    def gauge(name, value, tags=None):
        metrics_data["gauges"][name] = value
    
    def histogram(name, value, tags=None):
        if name not in metrics_data["histograms"]:
            metrics_data["histograms"][name] = []
        metrics_data["histograms"][name].append(value)
    
    def timer(name):
        import time
        start = time.time()
        
        class TimerContext:
            def __enter__(self):
                return self
            
            def __exit__(self, *args):
                duration = time.time() - start
                if name not in metrics_data["timers"]:
                    metrics_data["timers"][name] = []
                metrics_data["timers"][name].append(duration)
        
        return TimerContext()
    
    metrics.increment = Mock(side_effect=increment)
    metrics.gauge = Mock(side_effect=gauge)
    metrics.histogram = Mock(side_effect=histogram)
    metrics.timer = Mock(side_effect=timer)
    metrics.get_metrics = Mock(return_value=metrics_data)
    metrics.reset = Mock(side_effect=lambda: metrics_data.clear())
    
    return metrics


@pytest.fixture
def assertion_helpers():
    """Provide helper functions for complex assertions."""
    
    def assert_datetime_close(dt1, dt2, delta_seconds=1):
        """Assert two datetimes are within delta_seconds of each other."""
        if dt1 and dt2:
            diff = abs((dt1 - dt2).total_seconds())
            assert diff <= delta_seconds, f"Datetimes differ by {diff} seconds"
    
    def assert_json_equal(json1, json2, ignore_keys=None):
        """Assert two JSON objects are equal, optionally ignoring certain keys."""
        ignore_keys = ignore_keys or []
        
        def clean_dict(d):
            if isinstance(d, dict):
                return {k: clean_dict(v) for k, v in d.items() if k not in ignore_keys}
            elif isinstance(d, list):
                return [clean_dict(item) for item in d]
            return d
        
        assert clean_dict(json1) == clean_dict(json2)
    
    def assert_in_range(value, min_val, max_val):
        """Assert a value is within a range."""
        assert min_val <= value <= max_val, f"{value} not in range [{min_val}, {max_val}]"
    
    def assert_has_attributes(obj, attributes):
        """Assert an object has all specified attributes."""
        for attr in attributes:
            assert hasattr(obj, attr), f"Object missing attribute: {attr}"
    
    def assert_response_format(response, required_fields=None):
        """Assert API response has correct format."""
        required_fields = required_fields or ["status", "data"]
        for field in required_fields:
            assert field in response, f"Response missing field: {field}"
        
        if "status" in response:
            assert response["status"] in ["success", "error"], f"Invalid status: {response['status']}"
    
    return {
        "assert_datetime_close": assert_datetime_close,
        "assert_json_equal": assert_json_equal,
        "assert_in_range": assert_in_range,
        "assert_has_attributes": assert_has_attributes,
        "assert_response_format": assert_response_format
    }


@pytest.fixture
def cleanup_handlers():
    """Provide cleanup handlers for test teardown."""
    handlers = []
    
    def register(handler):
        """Register a cleanup handler."""
        handlers.append(handler)
    
    yield register
    
    # Execute all cleanup handlers
    for handler in reversed(handlers):
        try:
            handler()
        except Exception as e:
            print(f"Cleanup handler failed: {e}")


@pytest.fixture(autouse=True)
def reset_singleton_instances():
    """Reset singleton instances between tests."""
    # This would reset any singleton patterns in your application
    # Add specific singleton reset logic here as needed
    yield
    # Cleanup after test
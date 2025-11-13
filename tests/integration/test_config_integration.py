"""
Test Configuration Module

Centralized configuration for integration tests including:
- Mock LLM settings
- Database configuration
- Service URLs
- Rate limiting settings
- Test data fixtures
"""

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

# Skip all tests in this module as they require external services
pytestmark = pytest.mark.skipif(
    not os.environ.get("RUN_INTEGRATION_TESTS"),
    reason="Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to enable",
)

# Add project paths for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
PARENT_ROOT = PROJECT_ROOT.parent
sys.path.insert(0, str(PARENT_ROOT))  # For database imports
sys.path.insert(0, str(PROJECT_ROOT))  # For project imports

# Environment configuration
os.environ.setdefault("USE_MOCK_LLM", "true")
os.environ.setdefault("OPENAI_API_KEY", "mock-key-for-testing")
os.environ.setdefault("BYPASS_RATE_LIMIT_IN_TESTS", "true")
os.environ.setdefault("LOG_LEVEL", "WARNING")  # Reduce noise in tests

# Service configuration
SERVICE_CONFIG = {
    "fastapi": {"host": "127.0.0.1", "port": 8008, "url": "http://127.0.0.1:8008"},
    "flask": {"host": "127.0.0.1", "port": 5001, "url": "http://127.0.0.1:5001"},
    "mcp": {"host": "127.0.0.1", "port": 9876, "url": "ws://127.0.0.1:9876"},
    "roblox_plugin": {"host": "127.0.0.1", "port": 64989, "url": "http://127.0.0.1:64989"},
}

# Database configuration
DATABASE_CONFIG = {
    "test": {"url": "sqlite+aiosqlite:///:memory:", "echo": False},
    "production": {
        "url": os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/testdb"),
        "echo": False,
    },
}

# Rate limiting configuration for tests
RATE_LIMIT_CONFIG = {
    "bypass": True,
    "requests_per_minute": 1000,
    "burst_limit": 2000,
    "window_seconds": 60,
}

# Test data fixtures
TEST_DATA = {
    "user": {
        "id": "test-user-123",
        "email": "test@example.com",
        "username": "testuser",
        "role": "teacher",
    },
    "course": {
        "id": "course-123",
        "title": "Introduction to Python",
        "subject": "Computer Science",
        "grade_level": 9,
    },
    "lesson": {
        "id": "lesson-123",
        "title": "Variables and Data Types",
        "duration": 45,
        "objectives": ["Understand variables", "Learn data types"],
    },
    "quiz": {
        "id": "quiz-123",
        "title": "Variables Quiz",
        "questions": [
            {
                "question": "What is a variable?",
                "options": ["A storage location", "A function", "A loop"],
                "correct": 0,
            }
        ],
    },
    "content_request": {
        "subject": "Mathematics",
        "grade_level": 7,
        "learning_objectives": ["Fractions", "Decimals"],
        "environment_type": "classroom",
        "include_quiz": True,
        "include_terrain": True,
    },
}


def get_mock_database():
    """Get mock database session for testing"""
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=Mock())
    mock_db.commit = AsyncMock()
    mock_db.rollback = AsyncMock()
    mock_db.close = AsyncMock()
    return mock_db


def get_mock_repositories():
    """Get mock repository instances"""
    from unittest.mock import Mock

    return {
        "UserRepository": Mock(),
        "CourseRepository": Mock(),
        "LessonRepository": Mock(),
        "QuizRepository": Mock(),
        "ContentRepository": Mock(),
        "ProgressRepository": Mock(),
        "AnalyticsRepository": Mock(),
    }


def configure_rate_limiting():
    """Configure rate limiting for tests"""
    try:
        from apps.backend.rate_limit_manager import (
            RateLimitConfig,
            RateLimitManager,
            RateLimitMode,
        )

        # Get or create manager instance
        manager = RateLimitManager.get_instance()

        # Configure for testing
        config = RateLimitConfig(
            requests_per_minute=RATE_LIMIT_CONFIG["requests_per_minute"],
            burst_limit=RATE_LIMIT_CONFIG["burst_limit"],
            window_seconds=RATE_LIMIT_CONFIG["window_seconds"],
            mode=RateLimitMode.BYPASS if RATE_LIMIT_CONFIG["bypass"] else RateLimitMode.TESTING,
        )

        manager.config = config
        manager.set_mode(config.mode)

        return manager
    except ImportError:
        return None


def configure_mock_llm():
    """Ensure mock LLM is configured"""
    os.environ["USE_MOCK_LLM"] = "true"

    # Import to trigger mock LLM initialization
    try:
        from core.agents.mock_llm import MockLLM

        from core.agents.base_agent import BaseAgent

        # Force mock LLM usage
        BaseAgent._llm = None  # Reset cached LLM
        return True
    except ImportError:
        return False


def setup_test_environment():
    """Setup complete test environment"""
    # Configure environment variables
    os.environ.update(
        {
            "USE_MOCK_LLM": "true",
            "OPENAI_API_KEY": "mock-key-for-testing",
            "BYPASS_RATE_LIMIT_IN_TESTS": "true",
            "LOG_LEVEL": "WARNING",
            "TESTING": "true",
        }
    )

    # Configure rate limiting
    rate_limit_manager = configure_rate_limiting()

    # Configure mock LLM
    mock_llm_configured = configure_mock_llm()

    return {
        "rate_limit_manager": rate_limit_manager,
        "mock_llm_configured": mock_llm_configured,
        "service_config": SERVICE_CONFIG,
        "database_config": DATABASE_CONFIG,
        "test_data": TEST_DATA,
    }


def cleanup_test_environment():
    """Cleanup after tests"""
    try:
        from apps.backend.rate_limit_manager import RateLimitManager

        # Reset rate limiting
        manager = RateLimitManager.get_instance()
        manager.clear_all_limits()
        RateLimitManager.reset_instance()
    except ImportError:
        pass

    # Reset environment variables
    for key in ["USE_MOCK_LLM", "BYPASS_RATE_LIMIT_IN_TESTS", "TESTING"]:
        os.environ.pop(key, None)


# Auto-configure on import
setup_test_environment()

# Export configuration
__all__ = [
    "SERVICE_CONFIG",
    "DATABASE_CONFIG",
    "RATE_LIMIT_CONFIG",
    "TEST_DATA",
    "get_mock_database",
    "get_mock_repositories",
    "configure_rate_limiting",
    "configure_mock_llm",
    "setup_test_environment",
    "cleanup_test_environment",
]

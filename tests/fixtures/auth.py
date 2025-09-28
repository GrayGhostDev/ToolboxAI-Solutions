"""Authentication and rate limiting test fixtures.

This module contains fixtures for testing authentication, authorization,
and rate limiting functionality.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Optional
from unittest.mock import Mock, patch

import jwt
import pytest

from apps.backend.auth.config import settings


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Reset rate limits before each test.

    This fixture ensures that rate limits are reset before each test,
    preventing rate limit errors from affecting test execution.
    """
    # Reset any in-memory rate limit stores
    import apps.backend.api.middleware.rate_limit as rate_limit_module

    if hasattr(rate_limit_module, "_rate_limit_store"):
        rate_limit_module._rate_limit_store.clear()

    if hasattr(rate_limit_module, "RateLimitMiddleware"):
        rate_limit_module.RateLimitMiddleware._request_counts.clear()

    yield

    # Cleanup after test
    if hasattr(rate_limit_module, "_rate_limit_store"):
        rate_limit_module._rate_limit_store.clear()


@pytest.fixture
def rate_limit_context():
    """Provide a rate limit testing context."""
    return {
        "requests_made": 0,
        "limit": 100,
        "window": 60,  # seconds
        "start_time": time.time(),
    }


@pytest.fixture
def rate_limit_manager():
    """Create a rate limit manager for testing.

    This fixture provides a mock rate limit manager that can be used
    to test rate limiting behavior without hitting actual limits.
    """

    class TestRateLimitManager:
        def __init__(self):
            self.limits: Dict[str, Dict] = {}
            self.enabled = True

        def check_rate_limit(self, key: str, limit: int = 100, window: int = 60) -> bool:
            """Check if rate limit is exceeded."""
            if not self.enabled:
                return True

            now = time.time()
            if key not in self.limits:
                self.limits[key] = {"count": 0, "window_start": now}

            limit_data = self.limits[key]

            # Reset window if expired
            if now - limit_data["window_start"] >= window:
                limit_data["count"] = 0
                limit_data["window_start"] = now

            # Check limit
            if limit_data["count"] >= limit:
                return False

            # Increment counter
            limit_data["count"] += 1
            return True

        def reset(self, key: Optional[str] = None):
            """Reset rate limits."""
            if key:
                self.limits.pop(key, None)
            else:
                self.limits.clear()

        def disable(self):
            """Disable rate limiting."""
            self.enabled = False

        def enable(self):
            """Enable rate limiting."""
            self.enabled = True

    return TestRateLimitManager()


@pytest.fixture
def production_rate_limit_manager():
    """Create a production-like rate limit manager.

    This fixture provides a more realistic rate limit manager that
    simulates production rate limiting behavior.
    """

    class ProductionRateLimitManager:
        def __init__(self):
            self.redis_mock = Mock()
            self.redis_mock.get.return_value = None
            self.redis_mock.setex.return_value = True
            self.redis_mock.incr.return_value = 1
            self.redis_mock.expire.return_value = True

        async def check_rate_limit_async(
            self, key: str, limit: int = 60, window: int = 60
        ) -> bool:
            """Async rate limit check."""
            current_count = self.redis_mock.get(key)
            if current_count is None:
                self.redis_mock.setex(key, window, 1)
                return True

            current_count = int(current_count)
            if current_count >= limit:
                return False

            self.redis_mock.incr(key)
            return True

        def get_remaining_quota(self, key: str, limit: int = 60) -> int:
            """Get remaining quota for a key."""
            current_count = self.redis_mock.get(key)
            if current_count is None:
                return limit
            return max(0, limit - int(current_count))

    return ProductionRateLimitManager()


@pytest.fixture
def mock_jwt_token():
    """Create a mock JWT token for testing.

    Returns a function that creates JWT tokens with custom payloads.
    """

    def _create_token(
        user_id: int = 1,
        username: str = "testuser",
        role: str = "student",
        exp_minutes: int = 30,
    ) -> str:
        """Create a JWT token with the given parameters."""
        payload = {
            "sub": str(user_id),
            "username": username,
            "role": role,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=exp_minutes),
        }

        # Use test secret key
        secret_key = "test-jwt-secret-key-only-for-testing"
        return jwt.encode(payload, secret_key, algorithm="HS256")

    return _create_token


@pytest.fixture
def mock_auth_headers(mock_jwt_token):
    """Create mock authorization headers.

    Returns a function that creates authorization headers with JWT tokens.
    """

    def _create_headers(
        user_id: int = 1,
        username: str = "testuser",
        role: str = "student",
    ) -> Dict[str, str]:
        """Create authorization headers."""
        token = mock_jwt_token(user_id=user_id, username=username, role=role)
        return {"Authorization": f"Bearer {token}"}

    return _create_headers


@pytest.fixture
def mock_current_user():
    """Mock the current user for authentication tests."""

    class MockUser:
        def __init__(
            self,
            id: int = 1,
            username: str = "testuser",
            email: str = "test@example.com",
            role: str = "student",
            is_active: bool = True,
        ):
            self.id = id
            self.username = username
            self.email = email
            self.role = role
            self.is_active = is_active
            self.created_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()

        def has_permission(self, permission: str) -> bool:
            """Check if user has a specific permission."""
            role_permissions = {
                "admin": ["read", "write", "delete", "manage"],
                "teacher": ["read", "write", "grade"],
                "student": ["read", "submit"],
            }
            return permission in role_permissions.get(self.role, [])

        def to_dict(self) -> dict:
            """Convert user to dictionary."""
            return {
                "id": self.id,
                "username": self.username,
                "email": self.email,
                "role": self.role,
                "is_active": self.is_active,
            }

    return MockUser()


@pytest.fixture
def mock_session_manager():
    """Mock session manager for testing."""

    class MockSessionManager:
        def __init__(self):
            self.sessions: Dict[str, dict] = {}

        def create_session(self, user_id: int, data: dict = None) -> str:
            """Create a new session."""
            import uuid

            session_id = str(uuid.uuid4())
            self.sessions[session_id] = {
                "user_id": user_id,
                "created_at": datetime.utcnow(),
                "data": data or {},
            }
            return session_id

        def get_session(self, session_id: str) -> Optional[dict]:
            """Get session data."""
            return self.sessions.get(session_id)

        def delete_session(self, session_id: str) -> bool:
            """Delete a session."""
            if session_id in self.sessions:
                del self.sessions[session_id]
                return True
            return False

        def clear_all_sessions(self):
            """Clear all sessions."""
            self.sessions.clear()

    return MockSessionManager()


@pytest.fixture
def bypass_auth(monkeypatch):
    """Bypass authentication for testing.

    This fixture patches authentication decorators to allow
    unauthenticated access during testing.
    """

    def mock_require_auth(func):
        """Mock authentication decorator."""
        return func

    def mock_require_role(*roles):
        """Mock role-based authorization decorator."""

        def decorator(func):
            return func

        return decorator

    # Patch authentication decorators
    monkeypatch.setattr("apps.backend.auth.decorators.require_auth", mock_require_auth)
    monkeypatch.setattr("apps.backend.auth.decorators.require_role", mock_require_role)

    yield

    # Cleanup is automatic with monkeypatch
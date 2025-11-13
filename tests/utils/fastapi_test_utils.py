"""
FastAPI Testing Utilities

Provides helper functions for testing FastAPI applications with proper
dependency injection, authentication, and database mocking.
"""

from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient


def create_mock_user(
    user_id: str = "test_user_123", email: str = "test@example.com", role: str = "student", **kwargs
) -> Mock:
    """
    Create a mock user object for testing

    Args:
        user_id: User identifier
        email: User email address
        role: User role (student, teacher, admin, parent)
        **kwargs: Additional user attributes

    Returns:
        Mock user object with common attributes
    """
    user = Mock()
    user.id = user_id
    user.email = email
    user.role = role
    user.is_active = kwargs.get("is_active", True)
    user.created_at = kwargs.get("created_at", "2025-01-01T00:00:00Z")
    user.updated_at = kwargs.get("updated_at", "2025-01-01T00:00:00Z")
    user.first_name = kwargs.get("first_name", "Test")
    user.last_name = kwargs.get("last_name", "User")
    user.school_id = kwargs.get("school_id", "school_123")
    user.class_ids = kwargs.get("class_ids", [])
    user.preferences = kwargs.get("preferences", {})

    # Add any additional attributes from kwargs
    for key, value in kwargs.items():
        if not hasattr(user, key):
            setattr(user, key, value)

    return user


def create_mock_database_session() -> AsyncMock:
    """
    Create a mock database session for testing

    Returns:
        AsyncMock database session
    """
    session = AsyncMock()
    session.add = Mock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.close = AsyncMock()
    session.execute = AsyncMock()
    session.scalar = AsyncMock()
    session.scalars = AsyncMock()
    session.get = AsyncMock()

    # Mock query builder methods
    session.query = Mock()
    session.query.return_value = session
    session.filter = Mock(return_value=session)
    session.filter_by = Mock(return_value=session)
    session.first = AsyncMock()
    session.all = AsyncMock()
    session.count = AsyncMock()
    session.limit = Mock(return_value=session)
    session.offset = Mock(return_value=session)
    session.order_by = Mock(return_value=session)

    return session


def override_dependency(app, dependency_func, mock_value):
    """
    Override a FastAPI dependency for testing

    Args:
        app: FastAPI application instance
        dependency_func: The dependency function to override
        mock_value: The mock value or function to return
    """
    if callable(mock_value):
        app.dependency_overrides[dependency_func] = mock_value
    else:
        app.dependency_overrides[dependency_func] = lambda: mock_value


def create_authenticated_test_client(
    app, user_role: str = "student", user_attributes: dict[str, Any] | None = None
) -> tuple[TestClient, Mock]:
    """
    Create a test client with an authenticated user

    Args:
        app: FastAPI application instance
        user_role: Role of the authenticated user
        user_attributes: Additional user attributes

    Returns:
        Tuple of (TestClient, mock_user)
    """
    from apps.backend.api.auth.auth import get_current_user

    # Create mock user
    attrs = user_attributes or {}
    mock_user = create_mock_user(role=user_role, **attrs)

    # Create test client
    client = TestClient(app)

    # Override authentication dependency
    override_dependency(app, get_current_user, mock_user)

    return client, mock_user


def create_admin_test_client(app) -> tuple[TestClient, Mock]:
    """Create test client with admin user"""
    return create_authenticated_test_client(
        app, user_role="admin", user_attributes={"permissions": ["admin_access"]}
    )


def create_teacher_test_client(app) -> tuple[TestClient, Mock]:
    """Create test client with teacher user"""
    return create_authenticated_test_client(
        app, user_role="teacher", user_attributes={"class_ids": ["class_1", "class_2"]}
    )


def create_student_test_client(app) -> tuple[TestClient, Mock]:
    """Create test client with student user"""
    return create_authenticated_test_client(
        app, user_role="student", user_attributes={"class_ids": ["class_1"]}
    )


def mock_database_dependency(app):
    """
    Mock the database session dependency

    Args:
        app: FastAPI application instance

    Returns:
        Mock database session
    """
    from apps.backend.core.database import get_session

    mock_session = create_mock_database_session()
    override_dependency(app, get_session, mock_session)

    return mock_session


class MockRoleChecker:
    """
    Mock implementation of role checking for testing require_role decorator
    """

    def __init__(self, required_role: str):
        self.required_role = required_role

    def __call__(self, current_user: Mock) -> None:
        """
        Check if user has required role

        Args:
            current_user: Mock user object

        Raises:
            HTTPException: If user doesn't have required role
        """
        if current_user.role != self.required_role:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required role: {self.required_role}",
            )


def test_require_role_decorator(required_role: str, user_role: str, should_pass: bool):
    """
    Test helper for role requirement decorators

    Args:
        required_role: The role required by the endpoint
        user_role: The role of the test user
        should_pass: Whether the test should pass or raise an exception
    """
    mock_user = create_mock_user(role=user_role)
    role_checker = MockRoleChecker(required_role)

    if should_pass:
        # Should not raise exception
        result = role_checker(mock_user)
        assert result is None
    else:
        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            role_checker(mock_user)
        assert exc_info.value.status_code == 403


def clear_dependency_overrides(app):
    """
    Clear all dependency overrides from the app

    Args:
        app: FastAPI application instance
    """
    app.dependency_overrides.clear()


@pytest.fixture
def mock_current_user():
    """Pytest fixture for mock current user"""
    return create_mock_user()


@pytest.fixture
def mock_admin_user():
    """Pytest fixture for mock admin user"""
    return create_mock_user(role="admin")


@pytest.fixture
def mock_teacher_user():
    """Pytest fixture for mock teacher user"""
    return create_mock_user(role="teacher")


@pytest.fixture
def mock_student_user():
    """Pytest fixture for mock student user"""
    return create_mock_user(role="student")


@pytest.fixture
def mock_db_session():
    """Pytest fixture for mock database session"""
    return create_mock_database_session()


@pytest.fixture
def authenticated_client(app):
    """Pytest fixture for authenticated test client"""
    client, user = create_authenticated_test_client(app)
    yield client, user
    clear_dependency_overrides(app)


@pytest.fixture
def admin_client(app):
    """Pytest fixture for admin test client"""
    client, user = create_admin_test_client(app)
    yield client, user
    clear_dependency_overrides(app)


@pytest.fixture
def teacher_client(app):
    """Pytest fixture for teacher test client"""
    client, user = create_teacher_test_client(app)
    yield client, user
    clear_dependency_overrides(app)


@pytest.fixture
def student_client(app):
    """Pytest fixture for student test client"""
    client, user = create_student_test_client(app)
    yield client, user
    clear_dependency_overrides(app)


# Example usage and test helpers
def assert_success_response(response, expected_status: int = 200):
    """Assert that a response is successful"""
    assert response.status_code == expected_status
    data = response.json()
    assert "error" not in data or data.get("status") == "success"


def assert_error_response(response, expected_status: int, expected_message: str = None):
    """Assert that a response contains an error"""
    assert response.status_code == expected_status
    if expected_message:
        data = response.json()
        assert expected_message in str(data.get("detail", ""))


def assert_unauthorized_response(response):
    """Assert that a response is unauthorized"""
    assert_error_response(response, 401)


def assert_forbidden_response(response):
    """Assert that a response is forbidden"""
    assert_error_response(response, 403)


def assert_not_found_response(response):
    """Assert that a response is not found"""
    assert_error_response(response, 404)


def assert_validation_error_response(response):
    """Assert that a response contains validation errors"""
    assert_error_response(response, 422)

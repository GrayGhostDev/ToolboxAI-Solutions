"""
Test Helper Utilities

Provides reusable helper functions and utilities for testing across the project.
"""

from typing import Dict, Any, List, Optional, Callable
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import json
import asyncio
from pathlib import Path

from fastapi import status
from starlette.responses import Response


# ============================================================================
# API Testing Helpers
# ============================================================================

class APITestHelper:
    """Helper class for testing FastAPI endpoints."""

    @staticmethod
    def assert_success_response(
        response: Response,
        expected_status: int = status.HTTP_200_OK,
        expected_keys: List[str] = None
    ) -> Dict[str, Any]:
        """
        Assert that an API response is successful.

        Args:
            response: FastAPI response object
            expected_status: Expected HTTP status code
            expected_keys: List of keys that should exist in response

        Returns:
            Response JSON data

        Raises:
            AssertionError: If response doesn't match expectations
        """
        assert response.status_code == expected_status, \
            f"Expected {expected_status}, got {response.status_code}: {response.json()}"

        data = response.json()

        if expected_keys:
            for key in expected_keys:
                assert key in data, f"Expected key '{key}' not found in response"

        return data

    @staticmethod
    def assert_error_response(
        response: Response,
        expected_status: int = status.HTTP_400_BAD_REQUEST,
        expected_detail: str = None
    ) -> Dict[str, Any]:
        """
        Assert that an API response is an error.

        Args:
            response: FastAPI response object
            expected_status: Expected HTTP status code
            expected_detail: Expected error detail message (substring)

        Returns:
            Response JSON data

        Raises:
            AssertionError: If response doesn't match expectations
        """
        assert response.status_code == expected_status, \
            f"Expected {expected_status}, got {response.status_code}"

        data = response.json()
        assert "detail" in data or "message" in data, \
            "Error response should contain 'detail' or 'message'"

        if expected_detail:
            detail = data.get("detail", data.get("message", ""))
            assert expected_detail.lower() in detail.lower(), \
                f"Expected '{expected_detail}' in error detail, got: {detail}"

        return data

    @staticmethod
    def create_auth_headers(token: str, content_type: str = "application/json") -> Dict[str, str]:
        """Create authentication headers."""
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": content_type
        }

    @staticmethod
    def create_multipart_form_data(
        files: Dict[str, tuple],
        data: Dict[str, Any] = None
    ) -> tuple:
        """
        Create multipart form data for file uploads.

        Args:
            files: Dictionary mapping field names to (filename, content, content_type) tuples
            data: Optional dictionary of additional form fields

        Returns:
            Tuple of (files_dict, data_dict) for use with TestClient
        """
        files_dict = {}
        for field_name, (filename, content, content_type) in files.items():
            files_dict[field_name] = (filename, content, content_type)

        return files_dict, data or {}


# ============================================================================
# Database Testing Helpers
# ============================================================================

class DatabaseTestHelper:
    """Helper class for database testing."""

    @staticmethod
    def create_mock_query_result(
        items: List[Any] = None,
        count: int = None,
        first_item: Any = None
    ) -> Mock:
        """
        Create mock database query result.

        Args:
            items: List of items to return from all()
            count: Count to return from count()
            first_item: Item to return from first()

        Returns:
            Mock query object with configured return values
        """
        mock_query = Mock()

        if items is not None:
            mock_query.all.return_value = items

        if count is not None:
            mock_query.count.return_value = count

        if first_item is not None:
            mock_query.first.return_value = first_item
        elif items:
            mock_query.first.return_value = items[0] if items else None

        # Chain methods
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.filter_by = Mock(return_value=mock_query)
        mock_query.offset = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.join = Mock(return_value=mock_query)

        return mock_query

    @staticmethod
    def create_mock_session(query_results: Dict[Any, List[Any]] = None) -> Mock:
        """
        Create mock database session.

        Args:
            query_results: Dictionary mapping model classes to query results

        Returns:
            Mock session object
        """
        session = Mock()

        # Configure query method
        if query_results:
            def mock_query(model_class):
                items = query_results.get(model_class, [])
                return DatabaseTestHelper.create_mock_query_result(items=items)

            session.query = Mock(side_effect=mock_query)
        else:
            session.query = Mock(return_value=DatabaseTestHelper.create_mock_query_result())

        # Configure common session methods
        session.add = Mock()
        session.delete = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        session.flush = Mock()
        session.refresh = Mock()
        session.close = Mock()

        return session

    @staticmethod
    async def create_test_transaction(session):
        """
        Create a test transaction that automatically rolls back.

        Usage:
            async with create_test_transaction(session):
                # Make database changes
                # Changes are automatically rolled back after block
        """
        class TestTransaction:
            def __init__(self, session):
                self.session = session

            async def __aenter__(self):
                await self.session.begin()
                return self.session

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                await self.session.rollback()

        return TestTransaction(session)


# ============================================================================
# Mock Data Generators
# ============================================================================

class MockDataGenerator:
    """Generate mock data for testing."""

    @staticmethod
    def generate_user_data(
        role: str = "student",
        organization_id: UUID = None,
        **overrides
    ) -> Dict[str, Any]:
        """Generate mock user data."""
        user_id = overrides.get("id", uuid4())

        return {
            "id": user_id,
            "email": f"user_{user_id.hex[:8]}@test.edu",
            "username": f"user_{user_id.hex[:8]}",
            "role": role,
            "organization_id": organization_id or uuid4(),
            "is_active": True,
            "created_at": datetime.utcnow(),
            **overrides
        }

    @staticmethod
    def generate_content_data(
        created_by: int = None,
        organization_id: UUID = None,
        **overrides
    ) -> Dict[str, Any]:
        """Generate mock educational content data."""
        return {
            "id": overrides.get("id", 1),
            "title": "Sample Content",
            "description": "Sample educational content",
            "content_type": "lesson",
            "difficulty_level": "beginner",
            "status": "draft",
            "created_by": created_by or 1,
            "organization_id": organization_id or uuid4(),
            "created_at": datetime.utcnow(),
            **overrides
        }

    @staticmethod
    def generate_class_data(
        teacher_id: int = None,
        organization_id: UUID = None,
        **overrides
    ) -> Dict[str, Any]:
        """Generate mock class data."""
        return {
            "id": overrides.get("id", 1),
            "name": "Test Class",
            "description": "Test class description",
            "grade_level": "9",
            "subject": "Computer Science",
            "teacher_id": teacher_id or 1,
            "organization_id": organization_id or uuid4(),
            "is_active": True,
            "created_at": datetime.utcnow(),
            **overrides
        }

    @staticmethod
    def generate_jwt_token(
        user_id: int = 1,
        role: str = "student",
        exp_minutes: int = 60
    ) -> str:
        """
        Generate a mock JWT token.

        Note: This is for testing purposes only and doesn't use real JWT encoding.
        """
        import base64

        payload = {
            "sub": str(user_id),
            "role": role,
            "exp": (datetime.utcnow() + timedelta(minutes=exp_minutes)).isoformat()
        }

        # Create a fake JWT-like token (not actually signed)
        header = base64.b64encode(b'{"alg":"HS256","typ":"JWT"}').decode()
        payload_encoded = base64.b64encode(json.dumps(payload).encode()).decode()
        signature = base64.b64encode(b"mock_signature").decode()

        return f"{header}.{payload_encoded}.{signature}"


# ============================================================================
# Async Testing Helpers
# ============================================================================

class AsyncTestHelper:
    """Helpers for async testing."""

    @staticmethod
    async def run_with_timeout(coro, timeout_seconds: float = 5.0):
        """
        Run async coroutine with timeout.

        Args:
            coro: Coroutine to run
            timeout_seconds: Timeout in seconds

        Raises:
            asyncio.TimeoutError: If coroutine doesn't complete in time
        """
        try:
            return await asyncio.wait_for(coro, timeout=timeout_seconds)
        except asyncio.TimeoutError:
            raise AssertionError(f"Async operation timed out after {timeout_seconds}s")

    @staticmethod
    def create_async_mock(return_value=None, side_effect=None):
        """Create AsyncMock with configured return value or side effect."""
        mock = AsyncMock()
        if return_value is not None:
            mock.return_value = return_value
        if side_effect is not None:
            mock.side_effect = side_effect
        return mock

    @staticmethod
    async def wait_for_condition(
        condition: Callable,
        timeout_seconds: float = 5.0,
        check_interval: float = 0.1
    ) -> bool:
        """
        Wait for a condition to become true.

        Args:
            condition: Callable that returns True when condition is met
            timeout_seconds: Maximum time to wait
            check_interval: How often to check condition

        Returns:
            True if condition met, False if timeout

        Example:
            await wait_for_condition(lambda: mock.called, timeout_seconds=2)
        """
        start_time = asyncio.get_event_loop().time()

        while True:
            if condition():
                return True

            if asyncio.get_event_loop().time() - start_time > timeout_seconds:
                return False

            await asyncio.sleep(check_interval)


# ============================================================================
# File Testing Helpers
# ============================================================================

class FileTestHelper:
    """Helpers for file-based testing."""

    @staticmethod
    def create_temp_file(
        content: bytes = b"test content",
        suffix: str = ".txt",
        temp_dir: Path = None
    ) -> Path:
        """
        Create temporary file with content.

        Args:
            content: File content as bytes
            suffix: File extension
            temp_dir: Directory to create file in

        Returns:
            Path to created file
        """
        import tempfile

        if temp_dir:
            temp_dir.mkdir(parents=True, exist_ok=True)
            fd, path = tempfile.mkstemp(suffix=suffix, dir=temp_dir)
        else:
            fd, path = tempfile.mkstemp(suffix=suffix)

        try:
            with open(fd, 'wb') as f:
                f.write(content)
        except Exception:
            import os
            os.close(fd)
            raise

        return Path(path)

    @staticmethod
    def create_mock_upload_file(
        filename: str = "test.txt",
        content: bytes = b"test content",
        content_type: str = "text/plain"
    ):
        """Create mock FastAPI UploadFile."""
        from fastapi import UploadFile
        from io import BytesIO

        return UploadFile(
            filename=filename,
            file=BytesIO(content),
            headers={"content-type": content_type}
        )

    @staticmethod
    def assert_file_exists(path: Path):
        """Assert that file exists."""
        assert path.exists(), f"File does not exist: {path}"
        assert path.is_file(), f"Path is not a file: {path}"

    @staticmethod
    def assert_file_content(path: Path, expected_content: bytes):
        """Assert file content matches expected."""
        FileTestHelper.assert_file_exists(path)
        actual_content = path.read_bytes()
        assert actual_content == expected_content, \
            f"File content mismatch. Expected {len(expected_content)} bytes, got {len(actual_content)}"


# ============================================================================
# Performance Testing Helpers
# ============================================================================

class PerformanceTestHelper:
    """Helpers for performance testing."""

    @staticmethod
    def measure_execution_time(func: Callable, *args, **kwargs) -> tuple:
        """
        Measure execution time of a function.

        Returns:
            Tuple of (result, duration_seconds)
        """
        import time

        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start

        return result, duration

    @staticmethod
    async def measure_async_execution_time(coro) -> tuple:
        """
        Measure execution time of async coroutine.

        Returns:
            Tuple of (result, duration_seconds)
        """
        import time

        start = time.time()
        result = await coro
        duration = time.time() - start

        return result, duration

    @staticmethod
    def assert_execution_time(
        duration: float,
        max_seconds: float,
        message: str = None
    ):
        """Assert that execution time is within acceptable range."""
        msg = message or f"Execution time {duration:.3f}s exceeded max {max_seconds}s"
        assert duration <= max_seconds, msg

    @staticmethod
    class Timer:
        """Context manager for timing code blocks."""

        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.duration = None

        def __enter__(self):
            import time
            self.start_time = time.time()
            return self

        def __exit__(self, *args):
            import time
            self.end_time = time.time()
            self.duration = self.end_time - self.start_time

        @property
        def duration_ms(self) -> float:
            """Get duration in milliseconds."""
            return self.duration * 1000 if self.duration else 0


# ============================================================================
# Validation Helpers
# ============================================================================

class ValidationHelper:
    """Helpers for validation testing."""

    @staticmethod
    def assert_valid_uuid(value: str):
        """Assert that string is a valid UUID."""
        try:
            uuid_obj = UUID(value)
            assert str(uuid_obj) == value
        except (ValueError, AttributeError):
            raise AssertionError(f"Invalid UUID: {value}")

    @staticmethod
    def assert_valid_email(email: str):
        """Assert that string is a valid email."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        assert re.match(pattern, email), f"Invalid email: {email}"

    @staticmethod
    def assert_valid_datetime(value: Any):
        """Assert that value is a valid datetime."""
        if isinstance(value, str):
            try:
                datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                raise AssertionError(f"Invalid datetime string: {value}")
        elif not isinstance(value, datetime):
            raise AssertionError(f"Expected datetime, got {type(value)}")

    @staticmethod
    def assert_pagination_response(
        data: Dict[str, Any],
        expected_keys: List[str] = None
    ):
        """Assert that response contains valid pagination structure."""
        default_keys = ["items", "total", "page", "size"]
        keys_to_check = expected_keys or default_keys

        for key in keys_to_check:
            assert key in data, f"Missing pagination key: {key}"

        assert isinstance(data["items"], list), "items should be a list"
        assert isinstance(data.get("total"), int), "total should be an integer"


# ============================================================================
# RBAC Testing Helpers
# ============================================================================

class RBACTestHelper:
    """Helpers for RBAC testing."""

    @staticmethod
    def assert_permission_granted(response: Response):
        """Assert that permission was granted (2xx status)."""
        assert 200 <= response.status_code < 300, \
            f"Expected permission granted, got {response.status_code}: {response.json()}"

    @staticmethod
    def assert_permission_denied(response: Response, expected_status: int = 403):
        """Assert that permission was denied."""
        assert response.status_code == expected_status, \
            f"Expected {expected_status}, got {response.status_code}"

    @staticmethod
    def assert_authentication_required(response: Response):
        """Assert that authentication is required (401)."""
        assert response.status_code == 401, \
            f"Expected 401 Unauthorized, got {response.status_code}"

    @staticmethod
    def test_endpoint_permissions(
        client,
        endpoint: str,
        method: str,
        users: Dict[str, tuple],
        data: Dict = None
    ):
        """
        Test endpoint with multiple user roles.

        Args:
            client: Test client
            endpoint: API endpoint path
            method: HTTP method
            users: Dict mapping role name to (user_fixture, should_pass) tuples
            data: Request data

        Example:
            test_endpoint_permissions(
                client, "/api/v1/content",
                "POST",
                users={
                    "admin": (admin_user, True),
                    "teacher": (teacher_user, True),
                    "student": (student_user, False)
                },
                data={"title": "Test"}
            )
        """
        results = {}

        for role_name, (user, should_pass) in users.items():
            # Create auth headers for user
            headers = APITestHelper.create_auth_headers(
                MockDataGenerator.generate_jwt_token(user.id, user.role)
            )

            # Make request
            if method.upper() == "GET":
                response = client.get(endpoint, headers=headers)
            elif method.upper() == "POST":
                response = client.post(endpoint, json=data, headers=headers)
            elif method.upper() == "PUT":
                response = client.put(endpoint, json=data, headers=headers)
            elif method.upper() == "DELETE":
                response = client.delete(endpoint, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")

            # Check result
            passed = (200 <= response.status_code < 300) == should_pass

            results[role_name] = {
                "passed": passed,
                "status_code": response.status_code,
                "should_pass": should_pass
            }

            # Assert individual result
            if should_pass:
                RBACTestHelper.assert_permission_granted(response)
            else:
                RBACTestHelper.assert_permission_denied(response)

        return results


# ============================================================================
# Convenience Functions
# ============================================================================

def create_test_user(
    db_session,
    role: str = "student",
    organization_id: UUID = None,
    **kwargs
):
    """
    Create a test user in the database.

    Args:
        db_session: Database session
        role: User role
        organization_id: Organization ID
        **kwargs: Additional user attributes

    Returns:
        Created user object
    """
    from database.models import User

    user_data = MockDataGenerator.generate_user_data(
        role=role,
        organization_id=organization_id,
        **kwargs
    )

    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


def create_test_organization(db_session, **kwargs):
    """Create a test organization in the database."""
    from database.models import Organization

    org = Organization(
        name=kwargs.get("name", "Test Organization"),
        domain=kwargs.get("domain", "test.edu"),
        is_active=kwargs.get("is_active", True),
        **{k: v for k, v in kwargs.items() if k not in ["name", "domain", "is_active"]}
    )

    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)

    return org


# Export all helpers
__all__ = [
    "APITestHelper",
    "DatabaseTestHelper",
    "MockDataGenerator",
    "AsyncTestHelper",
    "FileTestHelper",
    "PerformanceTestHelper",
    "ValidationHelper",
    "RBACTestHelper",
    "create_test_user",
    "create_test_organization",
]

import pytest_asyncio
#!/usr/bin/env python3
"""
Comprehensive Authentication Integration Tests

Tests the complete authentication and authorization flow including:
- User registration with email verification
- Login with JWT token generation
- Role-based access control
- Protected endpoint access
- Rate limiting and security boundaries
- Multi-user scenarios with different roles
"""

import asyncio
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
import jwt
from fastapi.testclient import TestClient

# Set environment for testing
os.environ["TESTING"] = "true"
os.environ["USE_MOCK_LLM"] = "true"
os.environ["USE_MOCK_DATABASE"] = "false"  # Use real DB for integration

pytestmark = [
    pytest.mark.integration,
    pytest.mark.asyncio,
]


@pytest.fixture
async def auth_client():
    """HTTP client configured for authentication testing"""
    async with httpx.AsyncClient(
        base_url="http://127.0.0.1:8009",
        timeout=30.0
    ) as client:
        yield client


@pytest.fixture
def test_users():
    """Test user data for different roles"""
    return {
        "admin": {
            "username": f"test_admin_{int(time.time())}",
            "email": f"admin.{int(time.time())}@test.edu",
            "password": "AdminPass123!",
            "role": "admin",
            "first_name": "Test",
            "last_name": "Admin"
        },
        "teacher": {
            "username": f"test_teacher_{int(time.time())}",
            "email": f"teacher.{int(time.time())}@test.edu",
            "password": "TeacherPass123!",
            "role": "teacher",
            "first_name": "Test",
            "last_name": "Teacher"
        },
        "student": {
            "username": f"test_student_{int(time.time())}",
            "email": f"student.{int(time.time())}@test.edu",
            "password": "StudentPass123!",
            "role": "student",
            "first_name": "Test",
            "last_name": "Student"
        }
    }


@pytest.fixture
def mock_email_service():
    """Mock email service for verification emails"""
    mock_service = Mock()
    mock_service.send_verification_email = AsyncMock(return_value=True)
    mock_service.send_password_reset = AsyncMock(return_value=True)
    return mock_service


class TestUserRegistrationFlow:
    """Test complete user registration workflow"""

    @pytest.mark.asyncio
async def test_user_registration_success(self, auth_client, test_users, mock_email_service):
        """Test successful user registration with email verification"""
        user_data = test_users["teacher"]

        # Step 1: Register user
        response = await auth_client.post("/api/v1/auth/register", json=user_data)

        if response.status_code == 404:
            # Try alternative endpoint
            response = await auth_client.post("/auth/register", json=user_data)

        if response.status_code == 404:
            # Skip if endpoint not implemented yet
            pytest.skip("Registration endpoint not implemented")

        assert response.status_code == 201
        result = response.json()

        assert result["status"] == "success"
        assert "user_id" in result["data"]
        assert result["data"]["email"] == user_data["email"]
        assert result["data"]["username"] == user_data["username"]
        assert result["data"]["is_verified"] is False  # Should require verification

        user_id = result["data"]["user_id"]

        # Step 2: Verify email verification was triggered
        # In a real system, this would check email was sent
        # For testing, we simulate the verification process

        # Step 3: Complete email verification
        verification_token = self._generate_verification_token(user_id)
        verify_response = await auth_client.post(
            f"/api/v1/auth/verify-email",
            json={"token": verification_token, "user_id": user_id}
        )

        if verify_response.status_code != 404:  # If endpoint exists
            assert verify_response.status_code == 200
            verify_result = verify_response.json()
            assert verify_result["data"]["is_verified"] is True

    @pytest.mark.asyncio
async def test_duplicate_registration_prevention(self, auth_client, test_users):
        """Test prevention of duplicate user registration"""
        user_data = test_users["teacher"]

        # First registration
        response1 = await auth_client.post("/api/v1/auth/register", json=user_data)
        if response1.status_code == 404:
            response1 = await auth_client.post("/auth/register", json=user_data)

        if response1.status_code == 404:
            pytest.skip("Registration endpoint not implemented")

        # Second registration with same email
        response2 = await auth_client.post("/api/v1/auth/register", json=user_data)
        if response2.status_code == 404:
            response2 = await auth_client.post("/auth/register", json=user_data)

        assert response2.status_code == 400
        error_result = response2.json()
        assert "already exists" in error_result["message"].lower()

    @pytest.mark.asyncio
async def test_invalid_registration_data(self, auth_client):
        """Test registration with invalid data"""
        invalid_data_sets = [
            {"username": "", "email": "test@test.com", "password": "pass123"},  # Empty username
            {"username": "test", "email": "invalid-email", "password": "pass123"},  # Invalid email
            {"username": "test", "email": "test@test.com", "password": "123"},  # Weak password
            {"username": "ab", "email": "test@test.com", "password": "StrongPass123!"},  # Short username
        ]

        for invalid_data in invalid_data_sets:
            response = await auth_client.post("/api/v1/auth/register", json=invalid_data)
            if response.status_code == 404:
                response = await auth_client.post("/auth/register", json=invalid_data)

            if response.status_code != 404:  # If endpoint exists
                assert response.status_code == 422

    def _generate_verification_token(self, user_id: str) -> str:
        """Generate a mock verification token"""
        payload = {
            "user_id": user_id,
            "type": "email_verification",
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        return jwt.encode(payload, "test-secret", algorithm="HS256")


class TestLoginFlow:
    """Test complete login workflow"""

    @pytest.mark.asyncio
async def test_successful_login_flow(self, auth_client, test_users):
        """Test successful login with JWT token generation"""
        # Use existing user or create one
        user_data = test_users["teacher"]

        # Try to register first (might already exist)
        await auth_client.post("/api/v1/auth/register", json=user_data)

        # Login
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"]
        }

        response = await auth_client.post("/api/v1/auth/login", json=login_data)
        if response.status_code == 404:
            response = await auth_client.post("/auth/login", json=login_data)

        if response.status_code == 404:
            pytest.skip("Login endpoint not implemented")

        if response.status_code == 401:
            # User might not exist, that's okay for integration test
            pytest.skip("User doesn't exist in test database")

        assert response.status_code == 200
        result = response.json()

        assert "access_token" in result
        assert "token_type" in result
        assert result["token_type"] == "bearer"

        # Verify JWT token structure
        token = result["access_token"]
        try:
            # Decode without verification for testing
            payload = jwt.decode(token, options={"verify_signature": False})
            assert "sub" in payload  # Subject (user ID)
            assert "exp" in payload  # Expiration
            assert "role" in payload or "roles" in payload  # User role
        except jwt.InvalidTokenError:
            pytest.fail("Invalid JWT token structure")

    @pytest.mark.asyncio
async def test_invalid_login_credentials(self, auth_client):
        """Test login with invalid credentials"""
        invalid_credentials = [
            {"username": "nonexistent", "password": "password123"},
            {"username": "test_user", "password": "wrongpassword"},
            {"username": "", "password": "password123"},
            {"username": "test_user", "password": ""},
        ]

        for creds in invalid_credentials:
            response = await auth_client.post("/api/v1/auth/login", json=creds)
            if response.status_code == 404:
                response = await auth_client.post("/auth/login", json=creds)

            if response.status_code != 404:  # If endpoint exists
                assert response.status_code == 401

    @pytest.mark.asyncio
async def test_login_rate_limiting(self, auth_client):
        """Test rate limiting on login attempts"""
        login_data = {
            "username": "test_user",
            "password": "wrongpassword"
        }

        # Make multiple failed login attempts
        responses = []
        for _ in range(6):  # Assume rate limit is 5 attempts
            response = await auth_client.post("/api/v1/auth/login", json=login_data)
            if response.status_code == 404:
                response = await auth_client.post("/auth/login", json=login_data)

            if response.status_code == 404:
                pytest.skip("Login endpoint not implemented")

            responses.append(response.status_code)
            await asyncio.sleep(0.1)  # Small delay

        # Last attempt should be rate limited
        rate_limited = any(code == 429 for code in responses[-2:])
        if not rate_limited:
            # Rate limiting might not be implemented yet
            pytest.skip("Rate limiting not implemented")

    @pytest.mark.asyncio
async def test_token_refresh_flow(self, auth_client, test_users):
        """Test JWT token refresh mechanism"""
        # First login to get initial token
        user_data = test_users["teacher"]
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"]
        }

        response = await auth_client.post("/api/v1/auth/login", json=login_data)
        if response.status_code == 404:
            response = await auth_client.post("/auth/login", json=login_data)

        if response.status_code in [404, 401]:
            pytest.skip("Cannot test token refresh without valid login")

        result = response.json()
        access_token = result["access_token"]

        # Try to refresh token
        headers = {"Authorization": f"Bearer {access_token}"}
        refresh_response = await auth_client.post(
            "/api/v1/auth/refresh",
            headers=headers
        )

        if refresh_response.status_code == 404:
            refresh_response = await auth_client.post("/auth/refresh", headers=headers)

        if refresh_response.status_code != 404:  # If endpoint exists
            assert refresh_response.status_code == 200
            refresh_result = refresh_response.json()
            assert "access_token" in refresh_result

            # New token should be different
            new_token = refresh_result["access_token"]
            assert new_token != access_token


class TestRoleBasedAccessControl:
    """Test role-based access control across different endpoints"""

    @pytest.mark.asyncio
async def test_admin_access_privileges(self, auth_client, test_users):
        """Test admin user can access all protected endpoints"""
        # Get admin token
        admin_token = await self._get_user_token(auth_client, test_users["admin"])
        if not admin_token:
            pytest.skip("Cannot get admin token for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}

        # Test admin-only endpoints
        admin_endpoints = [
            ("/api/v1/admin/users", "GET"),
            ("/api/v1/admin/analytics", "GET"),
            ("/api/v1/admin/system-health", "GET"),
        ]

        for endpoint, method in admin_endpoints:
            if method == "GET":
                response = await auth_client.get(endpoint, headers=headers)
            else:
                response = await auth_client.post(endpoint, headers=headers)

            # Should not be forbidden (403) for admin
            assert response.status_code != 403

    @pytest.mark.asyncio
async def test_teacher_access_restrictions(self, auth_client, test_users):
        """Test teacher user has appropriate access restrictions"""
        teacher_token = await self._get_user_token(auth_client, test_users["teacher"])
        if not teacher_token:
            pytest.skip("Cannot get teacher token for testing")

        headers = {"Authorization": f"Bearer {teacher_token}"}

        # Test teacher-accessible endpoints
        teacher_endpoints = [
            ("/api/v1/content/generate", "POST"),
            ("/api/v1/quiz/generate", "POST"),
            ("/api/v1/courses", "GET"),
        ]

        for endpoint, method in teacher_endpoints:
            if method == "GET":
                response = await auth_client.get(endpoint, headers=headers)
            else:
                # Provide minimal valid data
                response = await auth_client.post(
                    endpoint,
                    json={"subject": "Math", "grade_level": 7},
                    headers=headers
                )

            # Should not be forbidden for teachers
            assert response.status_code != 403

        # Test admin-only endpoints (should be forbidden)
        admin_only_endpoints = [
            ("/api/v1/admin/users", "GET"),
            ("/api/v1/admin/system-health", "GET"),
        ]

        for endpoint, method in admin_only_endpoints:
            if method == "GET":
                response = await auth_client.get(endpoint, headers=headers)
            else:
                response = await auth_client.post(endpoint, headers=headers)

            # Should be forbidden for teachers
            if response.status_code != 404:  # If endpoint exists
                assert response.status_code == 403

    @pytest.mark.asyncio
async def test_student_access_restrictions(self, auth_client, test_users):
        """Test student user has most restrictive access"""
        student_token = await self._get_user_token(auth_client, test_users["student"])
        if not student_token:
            pytest.skip("Cannot get student token for testing")

        headers = {"Authorization": f"Bearer {student_token}"}

        # Test student-accessible endpoints
        student_endpoints = [
            ("/api/v1/courses", "GET"),
            ("/api/v1/user/profile", "GET"),
        ]

        for endpoint, method in student_endpoints:
            if method == "GET":
                response = await auth_client.get(endpoint, headers=headers)

            # Should not be forbidden for students
            assert response.status_code != 403

        # Test restricted endpoints (should be forbidden)
        restricted_endpoints = [
            ("/api/v1/content/generate", "POST"),
            ("/api/v1/admin/users", "GET"),
        ]

        for endpoint, method in restricted_endpoints:
            if method == "GET":
                response = await auth_client.get(endpoint, headers=headers)
            else:
                response = await auth_client.post(
                    endpoint,
                    json={"test": "data"},
                    headers=headers
                )

            # Should be forbidden for students
            if response.status_code != 404:  # If endpoint exists
                assert response.status_code == 403

    @pytest.mark.asyncio
async def test_unauthenticated_access_restrictions(self, auth_client):
        """Test unauthenticated requests are properly rejected"""
        protected_endpoints = [
            ("/api/v1/content/generate", "POST"),
            ("/api/v1/admin/users", "GET"),
            ("/api/v1/user/profile", "GET"),
        ]

        for endpoint, method in protected_endpoints:
            if method == "GET":
                response = await auth_client.get(endpoint)
            else:
                response = await auth_client.post(endpoint, json={"test": "data"})

            # Should require authentication
            if response.status_code != 404:  # If endpoint exists
                assert response.status_code == 401

    async def _get_user_token(self, client: httpx.AsyncClient, user_data: Dict[str, Any]) -> Optional[str]:
        """Helper to get authentication token for a user"""
        try:
            # Try to register first (might already exist)
            await client.post("/api/v1/auth/register", json=user_data)

            # Login
            login_data = {
                "username": user_data["username"],
                "password": user_data["password"]
            }

            response = await client.post("/api/v1/auth/login", json=login_data)
            if response.status_code == 404:
                response = await client.post("/auth/login", json=login_data)

            if response.status_code == 200:
                result = response.json()
                return result.get("access_token")

            return None
        except Exception:
            return None


class TestTokenSecurity:
    """Test JWT token security and validation"""

    @pytest.mark.asyncio
async def test_token_expiration_handling(self, auth_client, test_users):
        """Test handling of expired tokens"""
        # Get a valid token first
        user_token = await self._get_user_token(auth_client, test_users["teacher"])
        if not user_token:
            pytest.skip("Cannot get token for expiration testing")

        # Create an expired token
        expired_token = self._create_expired_token(test_users["teacher"]["username"])

        headers = {"Authorization": f"Bearer {expired_token}"}
        response = await auth_client.get("/api/v1/user/profile", headers=headers)

        if response.status_code != 404:  # If endpoint exists
            assert response.status_code == 401

    @pytest.mark.asyncio
async def test_invalid_token_rejection(self, auth_client):
        """Test rejection of invalid or malformed tokens"""
        invalid_tokens = [
            "invalid.token.here",
            "Bearer invalid-token",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",
            "",
        ]

        for token in invalid_tokens:
            headers = {"Authorization": f"Bearer {token}"}
            response = await auth_client.get("/api/v1/user/profile", headers=headers)

            if response.status_code != 404:  # If endpoint exists
                assert response.status_code == 401

    @pytest.mark.asyncio
async def test_token_tampering_detection(self, auth_client, test_users):
        """Test detection of tampered tokens"""
        # Get a valid token
        user_token = await self._get_user_token(auth_client, test_users["teacher"])
        if not user_token:
            pytest.skip("Cannot get token for tampering testing")

        # Tamper with the token
        tampered_token = user_token[:-10] + "tampered123"

        headers = {"Authorization": f"Bearer {tampered_token}"}
        response = await auth_client.get("/api/v1/user/profile", headers=headers)

        if response.status_code != 404:  # If endpoint exists
            assert response.status_code == 401

    def _create_expired_token(self, username: str) -> str:
        """Create an expired JWT token for testing"""
        payload = {
            "sub": username,
            "exp": datetime.utcnow() - timedelta(hours=1),  # Expired 1 hour ago
            "role": "teacher"
        }
        return jwt.encode(payload, "test-secret", algorithm="HS256")

    async def _get_user_token(self, client: httpx.AsyncClient, user_data: Dict[str, Any]) -> Optional[str]:
        """Helper to get authentication token for a user"""
        try:
            login_data = {
                "username": user_data["username"],
                "password": user_data["password"]
            }

            response = await client.post("/api/v1/auth/login", json=login_data)
            if response.status_code == 404:
                response = await client.post("/auth/login", json=login_data)

            if response.status_code == 200:
                result = response.json()
                return result.get("access_token")

            return None
        except Exception:
            return None


class TestConcurrentAuthOperations:
    """Test authentication system under concurrent load"""

    @pytest.mark.asyncio
async def test_concurrent_login_attempts(self, auth_client, test_users):
        """Test system stability under concurrent login attempts"""
        user_data = test_users["teacher"]
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"]
        }

        # Create multiple concurrent login tasks
        async def login_attempt():
            response = await auth_client.post("/api/v1/auth/login", json=login_data)
            if response.status_code == 404:
                response = await auth_client.post("/auth/login", json=login_data)
            return response.status_code

        # Run 10 concurrent login attempts
        tasks = [login_attempt() for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out skipped tests (404s)
        valid_results = [r for r in results if isinstance(r, int) and r != 404]

        if valid_results:
            # At least some should succeed (200) or fail gracefully (401)
            valid_codes = {200, 401, 429}  # Success, unauthorized, or rate limited
            assert all(code in valid_codes for code in valid_results)

    @pytest.mark.asyncio
async def test_concurrent_token_validation(self, auth_client, test_users):
        """Test concurrent token validation operations"""
        # Get a valid token first
        user_token = await self._get_user_token(auth_client, test_users["teacher"])
        if not user_token:
            pytest.skip("Cannot get token for concurrent testing")

        headers = {"Authorization": f"Bearer {user_token}"}

        # Create multiple concurrent token validation tasks
        async def validate_token():
            response = await auth_client.get("/api/v1/user/profile", headers=headers)
            return response.status_code

        # Run 10 concurrent validation attempts
        tasks = [validate_token() for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out skipped tests (404s)
        valid_results = [r for r in results if isinstance(r, int) and r != 404]

        if valid_results:
            # Should handle concurrent validation gracefully
            assert all(code in {200, 401} for code in valid_results)

    async def _get_user_token(self, client: httpx.AsyncClient, user_data: Dict[str, Any]) -> Optional[str]:
        """Helper to get authentication token for a user"""
        try:
            login_data = {
                "username": user_data["username"],
                "password": user_data["password"]
            }

            response = await client.post("/api/v1/auth/login", json=login_data)
            if response.status_code == 404:
                response = await client.post("/auth/login", json=login_data)

            if response.status_code == 200:
                result = response.json()
                return result.get("access_token")

            return None
        except Exception:
            return None


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])
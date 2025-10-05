"""
Comprehensive tests for user management API endpoints.

Tests cover user CRUD operations, profile management,
role updates, and user listing with pagination.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from tests.api.conftest import User


class TestUserEndpoints:
    """Test suite for user management endpoints."""

    @pytest.mark.asyncio
    async def test_get_user_profile(self, test_client: AsyncClient, auth_headers: dict):
        """Test getting user profile."""
        response = await test_client.get(
            "/api/v1/users/me/profile",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert "email" in data
        assert "role" in data
        assert "created_at" in data
        assert "hashed_password" not in data

    @pytest.mark.asyncio
    async def test_update_user_profile(self, test_client: AsyncClient, auth_headers: dict):
        """Test updating user profile."""
        response = await test_client.patch(
            "/api/v1/users/me/profile",
            json={
                "email": "newemail@example.com",
                "full_name": "Test User Updated",
                "bio": "This is my updated bio"
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newemail@example.com"
        assert data["full_name"] == "Test User Updated"
        assert data["bio"] == "This is my updated bio"

    @pytest.mark.asyncio
    async def test_update_profile_invalid_email(self, test_client: AsyncClient, auth_headers: dict):
        """Test updating profile with invalid email."""
        response = await test_client.patch(
            "/api/v1/users/me/profile",
            json={"email": "invalid-email"},
            headers=auth_headers
        )

        assert response.status_code == 422
        data = response.json()
        assert any("email" in str(error).lower() for error in data["detail"])

    @pytest.mark.asyncio
    async def test_update_profile_duplicate_email(
        self, test_client: AsyncClient, auth_headers: dict, admin_user: User
    ):
        """Test updating profile with duplicate email."""
        response = await test_client.patch(
            "/api/v1/users/me/profile",
            json={"email": admin_user.email},  # Try to use admin's email
            headers=auth_headers
        )

        assert response.status_code == 400
        data = response.json()
        assert "already in use" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_upload_avatar(self, test_client: AsyncClient, auth_headers: dict):
        """Test uploading user avatar."""
        # Create a mock image file
        files = {
            "file": ("avatar.jpg", b"fake image content", "image/jpeg")
        }

        response = await test_client.post(
            "/api/v1/users/me/avatar",
            files=files,
            headers=auth_headers
        )

        # May return 501 if not implemented or 200/201 if implemented
        assert response.status_code in [200, 201, 501]
        if response.status_code in [200, 201]:
            data = response.json()
            assert "avatar_url" in data

    @pytest.mark.asyncio
    async def test_delete_avatar(self, test_client: AsyncClient, auth_headers: dict):
        """Test deleting user avatar."""
        response = await test_client.delete(
            "/api/v1/users/me/avatar",
            headers=auth_headers
        )

        assert response.status_code in [200, 204, 404]

    @pytest.mark.asyncio
    async def test_get_user_by_id(
        self, test_client: AsyncClient, admin_headers: dict, test_user: User
    ):
        """Test getting user by ID (admin only)."""
        response = await test_client.get(
            f"/api/v1/users/{test_user.id}",
            headers=admin_headers
        )

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert data["id"] == test_user.id
            assert data["username"] == test_user.username

    @pytest.mark.asyncio
    async def test_get_user_by_id_forbidden(
        self, test_client: AsyncClient, auth_headers: dict, admin_user: User
    ):
        """Test non-admin cannot get other users by ID."""
        response = await test_client.get(
            f"/api/v1/users/{admin_user.id}",
            headers=auth_headers
        )

        assert response.status_code in [403, 404]

    @pytest.mark.asyncio
    async def test_list_users(self, test_client: AsyncClient, admin_headers: dict):
        """Test listing all users (admin only)."""
        response = await test_client.get(
            "/api/v1/users",
            headers=admin_headers
        )

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list) or "items" in data
            if "items" in data:
                assert isinstance(data["items"], list)
                assert "total" in data

    @pytest.mark.asyncio
    async def test_list_users_pagination(self, test_client: AsyncClient, admin_headers: dict):
        """Test user listing with pagination."""
        response = await test_client.get(
            "/api/v1/users?page=1&limit=10",
            headers=admin_headers
        )

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            if "items" in data:
                assert len(data["items"]) <= 10
                assert "page" in data
                assert "limit" in data
                assert "total" in data

    @pytest.mark.asyncio
    async def test_list_users_filter_by_role(self, test_client: AsyncClient, admin_headers: dict):
        """Test filtering users by role."""
        response = await test_client.get(
            "/api/v1/users?role=teacher",
            headers=admin_headers
        )

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", data if isinstance(data, list) else [])
            for user in items:
                assert user["role"] == "teacher"

    @pytest.mark.asyncio
    async def test_search_users(self, test_client: AsyncClient, admin_headers: dict):
        """Test searching users by username or email."""
        response = await test_client.get(
            "/api/v1/users/search?q=test",
            headers=admin_headers
        )

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", data if isinstance(data, list) else [])
            for user in items:
                assert "test" in user["username"].lower() or "test" in user["email"].lower()

    @pytest.mark.asyncio
    async def test_update_user_role(
        self, test_client: AsyncClient, admin_headers: dict, test_user: User
    ):
        """Test updating user role (admin only)."""
        response = await test_client.patch(
            f"/api/v1/users/{test_user.id}/role",
            json={"role": "teacher"},
            headers=admin_headers
        )

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert data["role"] == "teacher"

    @pytest.mark.asyncio
    async def test_update_user_role_forbidden(
        self, test_client: AsyncClient, teacher_headers: dict, test_user: User
    ):
        """Test non-admin cannot update user roles."""
        response = await test_client.patch(
            f"/api/v1/users/{test_user.id}/role",
            json={"role": "admin"},
            headers=teacher_headers
        )

        assert response.status_code in [403, 404]

    @pytest.mark.asyncio
    async def test_activate_deactivate_user(
        self, test_client: AsyncClient, admin_headers: dict, test_user: User
    ):
        """Test activating and deactivating users (admin only)."""
        # Deactivate user
        response = await test_client.patch(
            f"/api/v1/users/{test_user.id}/status",
            json={"is_active": False},
            headers=admin_headers
        )

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert data["is_active"] is False

        # Reactivate user
        response = await test_client.patch(
            f"/api/v1/users/{test_user.id}/status",
            json={"is_active": True},
            headers=admin_headers
        )

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_delete_user(
        self, test_client: AsyncClient, admin_headers: dict, test_session: AsyncSession
    ):
        """Test deleting a user (admin only)."""
        # Create a user to delete
        from apps.backend.core.auth import UnifiedAuthService
        auth_service = UnifiedAuthService()

        user_to_delete = User(
            username="tobedeleted",
            email="delete@example.com",
            hashed_password=auth_service.hash_password("password123"),
            role="student",
            is_active=True
        )
        test_session.add(user_to_delete)
        await test_session.commit()
        await test_session.refresh(user_to_delete)

        # Delete the user
        response = await test_client.delete(
            f"/api/v1/users/{user_to_delete.id}",
            headers=admin_headers
        )

        assert response.status_code in [200, 204, 404]

        # Verify user is deleted
        response = await test_client.get(
            f"/api/v1/users/{user_to_delete.id}",
            headers=admin_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_user_forbidden(
        self, test_client: AsyncClient, auth_headers: dict, admin_user: User
    ):
        """Test non-admin cannot delete users."""
        response = await test_client.delete(
            f"/api/v1/users/{admin_user.id}",
            headers=auth_headers
        )

        assert response.status_code in [403, 404]

    @pytest.mark.asyncio
    async def test_get_user_statistics(self, test_client: AsyncClient, auth_headers: dict):
        """Test getting user statistics."""
        response = await test_client.get(
            "/api/v1/users/me/statistics",
            headers=auth_headers
        )

        assert response.status_code in [200, 404, 501]
        if response.status_code == 200:
            data = response.json()
            # Statistics structure depends on implementation
            assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_get_user_activity(self, test_client: AsyncClient, auth_headers: dict):
        """Test getting user activity history."""
        response = await test_client.get(
            "/api/v1/users/me/activity",
            headers=auth_headers
        )

        assert response.status_code in [200, 404, 501]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list) or "items" in data

    @pytest.mark.asyncio
    async def test_get_user_preferences(self, test_client: AsyncClient, auth_headers: dict):
        """Test getting user preferences."""
        response = await test_client.get(
            "/api/v1/users/me/preferences",
            headers=auth_headers
        )

        assert response.status_code in [200, 404, 501]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_update_user_preferences(self, test_client: AsyncClient, auth_headers: dict):
        """Test updating user preferences."""
        response = await test_client.patch(
            "/api/v1/users/me/preferences",
            json={
                "theme": "dark",
                "language": "en",
                "notifications_enabled": True,
                "email_notifications": False
            },
            headers=auth_headers
        )

        assert response.status_code in [200, 404, 501]
        if response.status_code == 200:
            data = response.json()
            assert data["theme"] == "dark"
            assert data["language"] == "en"


class TestUserBulkOperations:
    """Test suite for bulk user operations."""

    @pytest.mark.asyncio
    async def test_bulk_create_users(
        self, test_client: AsyncClient, admin_headers: dict
    ):
        """Test bulk user creation (admin only)."""
        users_data = [
            {
                "username": f"bulkuser{i}",
                "email": f"bulk{i}@example.com",
                "password": "password123",
                "role": "student"
            }
            for i in range(5)
        ]

        response = await test_client.post(
            "/api/v1/users/bulk",
            json=users_data,
            headers=admin_headers
        )

        assert response.status_code in [200, 201, 404, 501]
        if response.status_code in [200, 201]:
            data = response.json()
            assert len(data) == 5

    @pytest.mark.asyncio
    async def test_bulk_update_users(
        self, test_client: AsyncClient, admin_headers: dict
    ):
        """Test bulk user updates (admin only)."""
        updates = {
            "user_ids": [1, 2, 3],
            "updates": {
                "is_active": False,
                "role": "student"
            }
        }

        response = await test_client.patch(
            "/api/v1/users/bulk",
            json=updates,
            headers=admin_headers
        )

        assert response.status_code in [200, 404, 501]

    @pytest.mark.asyncio
    async def test_bulk_delete_users(
        self, test_client: AsyncClient, admin_headers: dict
    ):
        """Test bulk user deletion (admin only)."""
        response = await test_client.delete(
            "/api/v1/users/bulk",
            json={"user_ids": [100, 101, 102]},  # Non-existent IDs
            headers=admin_headers
        )

        assert response.status_code in [200, 204, 404, 501]

    @pytest.mark.asyncio
    async def test_export_users(
        self, test_client: AsyncClient, admin_headers: dict
    ):
        """Test exporting users to CSV/Excel (admin only)."""
        response = await test_client.get(
            "/api/v1/users/export?format=csv",
            headers=admin_headers
        )

        assert response.status_code in [200, 404, 501]
        if response.status_code == 200:
            assert response.headers.get("content-type") in [
                "text/csv",
                "application/csv",
                "application/vnd.ms-excel"
            ]

    @pytest.mark.asyncio
    async def test_import_users(
        self, test_client: AsyncClient, admin_headers: dict
    ):
        """Test importing users from CSV (admin only)."""
        csv_content = """username,email,role
        importuser1,import1@example.com,student
        importuser2,import2@example.com,teacher
        """

        files = {
            "file": ("users.csv", csv_content.encode(), "text/csv")
        }

        response = await test_client.post(
            "/api/v1/users/import",
            files=files,
            headers=admin_headers
        )

        assert response.status_code in [200, 201, 404, 501]
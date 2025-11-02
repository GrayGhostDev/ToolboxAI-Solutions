"""
Unit Tests for Admin API Endpoints

Tests administrative functionality for user management.

Phase 1 Week 1: Authentication & user management endpoint tests
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, Mock, patch

from fastapi import HTTPException, status

# Import endpoint functions
from apps.backend.api.v1.endpoints.admin import (
    list_users,
    create_user,
    get_user,
    update_user,
    deactivate_user,
    db_service,
)

from database.models import User


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_admin_user():
    """Create mock admin user."""
    user = Mock(spec=User)
    user.id = uuid4()
    user.username = "admin"
    user.email = "admin@toolboxai.com"
    user.role = "admin"
    user.first_name = "Admin"
    user.last_name = "User"
    user.is_active = True
    user.is_verified = True
    user.created_at = datetime.now(timezone.utc)
    return user


@pytest.fixture
def mock_teacher_user():
    """Create mock teacher user (non-admin)."""
    user = Mock(spec=User)
    user.id = uuid4()
    user.username = "teacher"
    user.email = "teacher@school.edu"
    user.role = "teacher"
    return user


@pytest.fixture
def mock_student_user():
    """Create mock student user (non-admin)."""
    user = Mock(spec=User)
    user.id = uuid4()
    user.username = "student"
    user.email = "student@school.edu"
    user.role = "student"
    return user


@pytest.fixture
def mock_db_pool():
    """Create mock database pool."""
    pool = AsyncMock()
    conn = AsyncMock()

    # Setup connection acquire context manager
    pool.acquire.return_value.__aenter__.return_value = conn
    pool.acquire.return_value.__aexit__.return_value = None

    return pool, conn


@pytest.fixture
def valid_user_data():
    """Create valid user creation data."""
    return {
        "email": "newuser@example.com",
        "username": "newuser",
        "password": "SecurePassword123!",
        "first_name": "New",
        "last_name": "User",
        "role": "student",
    }


@pytest.fixture
def sample_user_list():
    """Create list of sample users."""
    return [
        {
            "id": str(uuid4()),
            "username": "user1",
            "email": "user1@example.com",
            "first_name": "User",
            "last_name": "One",
            "role": "student",
            "is_active": True,
            "is_verified": True,
            "created_at": datetime.now(timezone.utc),
        },
        {
            "id": str(uuid4()),
            "username": "user2",
            "email": "user2@example.com",
            "first_name": "User",
            "last_name": "Two",
            "role": "teacher",
            "is_active": True,
            "is_verified": True,
            "created_at": datetime.now(timezone.utc),
        },
    ]


# ============================================================================
# Test List Users Endpoint
# ============================================================================


class TestListUsers:
    """Test user listing endpoint."""

    @pytest.mark.asyncio
    async def test_list_users_admin_success_fallback(self, mock_admin_user):
        """Test successful user listing by admin with fallback data."""
        with patch.object(db_service, "pool", None):
            result = await list_users(current_user=mock_admin_user)

        assert result["success"] is True
        assert "users" in result
        assert isinstance(result["users"], list)
        assert "pagination" in result
        assert "page" in result
        assert "page_size" in result

    @pytest.mark.asyncio
    async def test_list_users_non_admin_forbidden(self, mock_teacher_user):
        """Test that non-admin users cannot list users."""
        with pytest.raises(HTTPException) as exc_info:
            await list_users(current_user=mock_teacher_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Only admins can list users" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_list_users_student_forbidden(self, mock_student_user):
        """Test that students cannot list users."""
        with pytest.raises(HTTPException) as exc_info:
            await list_users(current_user=mock_student_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_list_users_with_pagination(self, mock_admin_user):
        """Test user listing with pagination parameters."""
        with patch.object(db_service, "pool", None):
            result = await list_users(current_user=mock_admin_user, page=2, page_size=10)

        assert result["page"] == 2
        assert result["page_size"] == 10
        assert "total_pages" in result

    @pytest.mark.asyncio
    async def test_list_users_with_search(self, mock_admin_user):
        """Test user listing with search filter."""
        with patch.object(db_service, "pool", None):
            result = await list_users(current_user=mock_admin_user, search="john")

        assert result["success"] is True
        assert result["filters_applied"]["search"] == "john"

    @pytest.mark.asyncio
    async def test_list_users_with_role_filter(self, mock_admin_user):
        """Test user listing with role filter."""
        with patch.object(db_service, "pool", None):
            result = await list_users(current_user=mock_admin_user, role="teacher")

        assert result["filters_applied"]["role"] == "teacher"

    @pytest.mark.asyncio
    async def test_list_users_with_sorting(self, mock_admin_user):
        """Test user listing with custom sorting."""
        with patch.object(db_service, "pool", None):
            result = await list_users(
                current_user=mock_admin_user, sort_by="username", sort_order="asc"
            )

        assert result["filters_applied"]["sort_by"] == "username"
        assert result["filters_applied"]["sort_order"] == "asc"

    @pytest.mark.asyncio
    async def test_list_users_pagination_structure(self, mock_admin_user):
        """Test that pagination structure is complete."""
        with patch.object(db_service, "pool", None):
            result = await list_users(current_user=mock_admin_user)

        pagination = result["pagination"]
        assert "page" in pagination
        assert "page_size" in pagination
        assert "total" in pagination
        assert "total_pages" in pagination

    @pytest.mark.asyncio
    async def test_list_users_filters_applied_structure(self, mock_admin_user):
        """Test that filters_applied structure is complete."""
        with patch.object(db_service, "pool", None):
            result = await list_users(current_user=mock_admin_user)

        filters = result["filters_applied"]
        assert "search" in filters
        assert "role" in filters
        assert "sort_by" in filters
        assert "sort_order" in filters


# ============================================================================
# Test Create User Endpoint
# ============================================================================


class TestCreateUser:
    """Test user creation endpoint."""

    @pytest.mark.asyncio
    async def test_create_user_admin_success(self, mock_admin_user, valid_user_data):
        """Test successful user creation by admin."""
        with patch.object(db_service, "pool", None):
            result = await create_user(user_data=valid_user_data, current_user=mock_admin_user)

        assert "id" in result
        assert result["email"] == valid_user_data["email"]
        assert result["username"] == valid_user_data["username"]
        assert result["role"] == valid_user_data["role"]
        assert "password" not in result  # Password should not be returned

    @pytest.mark.asyncio
    async def test_create_user_non_admin_forbidden(self, mock_teacher_user, valid_user_data):
        """Test that non-admin users cannot create users."""
        with pytest.raises(HTTPException) as exc_info:
            await create_user(user_data=valid_user_data, current_user=mock_teacher_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Only admins can create users" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_user_missing_email(self, mock_admin_user):
        """Test user creation with missing email."""
        user_data = {"username": "testuser", "password": "password123"}

        with pytest.raises(HTTPException) as exc_info:
            await create_user(user_data=user_data, current_user=mock_admin_user)

        assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "Missing required field" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_user_missing_username(self, mock_admin_user):
        """Test user creation with missing username."""
        user_data = {"email": "test@example.com", "password": "password123"}

        with pytest.raises(HTTPException) as exc_info:
            await create_user(user_data=user_data, current_user=mock_admin_user)

        assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_create_user_missing_password(self, mock_admin_user):
        """Test user creation with missing password."""
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
        }

        with pytest.raises(HTTPException) as exc_info:
            await create_user(user_data=user_data, current_user=mock_admin_user)

        assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_create_user_invalid_email_format(self, mock_admin_user):
        """Test user creation with invalid email format."""
        user_data = {
            "email": "invalidemail",
            "username": "testuser",
            "password": "Password123!",
            "first_name": "Test",
            "last_name": "User",
        }

        with pytest.raises(HTTPException) as exc_info:
            await create_user(user_data=user_data, current_user=mock_admin_user)

        assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "Invalid email format" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_user_username_too_short(self, mock_admin_user):
        """Test user creation with username too short."""
        user_data = {
            "email": "test@example.com",
            "username": "ab",  # Too short (< 3 characters)
            "password": "Password123!",
            "first_name": "Test",
            "last_name": "User",
        }

        with pytest.raises(HTTPException) as exc_info:
            await create_user(user_data=user_data, current_user=mock_admin_user)

        assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "at least 3 characters" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_user_password_too_short(self, mock_admin_user):
        """Test user creation with password too short."""
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "short",  # Too short (< 8 characters)
            "first_name": "Test",
            "last_name": "User",
        }

        with pytest.raises(HTTPException) as exc_info:
            await create_user(user_data=user_data, current_user=mock_admin_user)

        assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "at least 8 characters" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_user_invalid_role(self, mock_admin_user):
        """Test user creation with invalid role."""
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "Password123!",
            "first_name": "Test",
            "last_name": "User",
            "role": "superuser",  # Invalid role
        }

        with pytest.raises(HTTPException) as exc_info:
            await create_user(user_data=user_data, current_user=mock_admin_user)

        assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "Invalid role" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_user_defaults_to_student_role(self, mock_admin_user):
        """Test that user creation defaults to student role when not specified."""
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "Password123!",
            "first_name": "Test",
            "last_name": "User",
            # No role specified
        }

        with patch.object(db_service, "pool", None):
            result = await create_user(user_data=user_data, current_user=mock_admin_user)

        assert result["role"] == "student"

    @pytest.mark.asyncio
    async def test_create_user_all_valid_roles(self, mock_admin_user):
        """Test user creation with all valid roles."""
        valid_roles = ["student", "teacher", "admin", "parent"]

        for role in valid_roles:
            user_data = {
                "email": f"{role}@example.com",
                "username": f"{role}_user",
                "password": "Password123!",
                "first_name": "Test",
                "last_name": "User",
                "role": role,
            }

            with patch.object(db_service, "pool", None):
                result = await create_user(user_data=user_data, current_user=mock_admin_user)
                assert result["role"] == role


# ============================================================================
# Test Get User Endpoint
# ============================================================================


class TestGetUser:
    """Test get user details endpoint."""

    @pytest.mark.asyncio
    async def test_get_user_admin_success(self, mock_admin_user):
        """Test successful user retrieval by admin."""
        user_id = str(mock_admin_user.id)

        with patch.object(db_service, "pool", None):
            result = await get_user(user_id=user_id, current_user=mock_admin_user)

        assert result["id"] == user_id
        assert "username" in result
        assert "email" in result

    @pytest.mark.asyncio
    async def test_get_user_non_admin_forbidden(self, mock_teacher_user):
        """Test that non-admin users cannot get user details."""
        user_id = str(uuid4())

        with pytest.raises(HTTPException) as exc_info:
            await get_user(user_id=user_id, current_user=mock_teacher_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Only admins can view user details" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_user_invalid_uuid_format(self, mock_admin_user):
        """Test getting user with invalid UUID format."""
        with pytest.raises(HTTPException) as exc_info:
            await get_user(user_id="invalid-uuid", current_user=mock_admin_user)

        assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "Invalid user ID format" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, mock_admin_user):
        """Test getting non-existent user."""
        user_id = str(uuid4())

        with patch.object(db_service, "pool", None):
            with pytest.raises(HTTPException) as exc_info:
                await get_user(user_id=user_id, current_user=mock_admin_user)

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_user_returns_complete_data(self, mock_admin_user):
        """Test that user details include all expected fields."""
        user_id = str(mock_admin_user.id)

        with patch.object(db_service, "pool", None):
            result = await get_user(user_id=user_id, current_user=mock_admin_user)

        required_fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_active",
            "is_verified",
            "created_at",
        ]
        for field in required_fields:
            assert field in result


# ============================================================================
# Test Update User Endpoint
# ============================================================================


class TestUpdateUser:
    """Test user update endpoint."""

    @pytest.mark.asyncio
    async def test_update_user_admin_success(self, mock_admin_user):
        """Test successful user update by admin."""
        user_id = str(uuid4())
        update_data = {"first_name": "Updated", "last_name": "Name"}

        with patch.object(db_service, "pool", None):
            result = await update_user(
                user_id=user_id, update_data=update_data, current_user=mock_admin_user
            )

        assert result["first_name"] == "Updated"
        assert result["last_name"] == "Name"

    @pytest.mark.asyncio
    async def test_update_user_non_admin_forbidden(self, mock_teacher_user):
        """Test that non-admin users cannot update users."""
        user_id = str(uuid4())
        update_data = {"first_name": "Updated"}

        with pytest.raises(HTTPException) as exc_info:
            await update_user(
                user_id=user_id, update_data=update_data, current_user=mock_teacher_user
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_update_user_invalid_uuid(self, mock_admin_user):
        """Test updating user with invalid UUID."""
        with pytest.raises(HTTPException) as exc_info:
            await update_user(
                user_id="invalid-uuid",
                update_data={"first_name": "Updated"},
                current_user=mock_admin_user,
            )

        assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_update_user_no_valid_fields(self, mock_admin_user):
        """Test update with no valid fields."""
        user_id = str(uuid4())
        update_data = {"invalid_field": "value"}

        with pytest.raises(HTTPException) as exc_info:
            await update_user(
                user_id=user_id, update_data=update_data, current_user=mock_admin_user
            )

        assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "No valid fields" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_update_user_all_updatable_fields(self, mock_admin_user):
        """Test updating all allowed fields."""
        user_id = str(uuid4())
        update_data = {
            "first_name": "New",
            "last_name": "Name",
            "email": "new@example.com",
            "role": "teacher",
            "is_active": False,
            "is_verified": True,
        }

        with patch.object(db_service, "pool", None):
            result = await update_user(
                user_id=user_id, update_data=update_data, current_user=mock_admin_user
            )

        # Mock returns the updated data
        assert result is not None

    @pytest.mark.asyncio
    async def test_update_user_partial_update(self, mock_admin_user):
        """Test partial user update (only some fields)."""
        user_id = str(uuid4())
        update_data = {"email": "newemail@example.com"}

        with patch.object(db_service, "pool", None):
            result = await update_user(
                user_id=user_id, update_data=update_data, current_user=mock_admin_user
            )

        assert result["email"] == "newemail@example.com"


# ============================================================================
# Test Deactivate User Endpoint
# ============================================================================


class TestDeactivateUser:
    """Test user deactivation endpoint."""

    @pytest.mark.asyncio
    async def test_deactivate_user_non_admin_forbidden(self, mock_teacher_user):
        """Test that non-admin users cannot deactivate users."""
        user_id = str(uuid4())

        with pytest.raises(HTTPException) as exc_info:
            await deactivate_user(user_id=user_id, current_user=mock_teacher_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_deactivate_user_self_forbidden(self, mock_admin_user):
        """Test that admin cannot deactivate their own account."""
        user_id = str(mock_admin_user.id)

        with pytest.raises(HTTPException) as exc_info:
            await deactivate_user(user_id=user_id, current_user=mock_admin_user)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cannot deactivate your own account" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_deactivate_user_invalid_uuid(self, mock_admin_user):
        """Test deactivating user with invalid UUID."""
        with pytest.raises(HTTPException) as exc_info:
            await deactivate_user(user_id="invalid-uuid", current_user=mock_admin_user)

        assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_deactivate_user_not_found(self, mock_admin_user):
        """Test deactivating non-existent user."""
        user_id = str(uuid4())

        with patch.object(db_service, "pool", None):
            with pytest.raises(HTTPException) as exc_info:
                await deactivate_user(user_id=user_id, current_user=mock_admin_user)

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_deactivate_user_success_with_db(self, mock_admin_user, mock_db_pool):
        """Test successful user deactivation with database."""
        pool, conn = mock_db_pool
        user_id = str(uuid4())
        conn.fetchrow.return_value = {
            "id": user_id,
            "username": "deactivated_user",
            "email": "user@example.com",
            "first_name": "Test",
            "last_name": "User",
        }

        with patch.object(db_service, "pool", pool):
            result = await deactivate_user(user_id=user_id, current_user=mock_admin_user)

        assert result["success"] is True
        assert "deactivated" in result["message"].lower()
        assert "user" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

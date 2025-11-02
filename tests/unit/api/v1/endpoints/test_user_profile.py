"""
Unit Tests for User Profile Endpoints

Tests user profile retrieval, updates, and preferences endpoints.

Phase 1 Week 1: Authentication & user management endpoint tests
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import Mock, patch

from fastapi import HTTPException

# Import endpoint functions and models
from apps.backend.api.v1.endpoints.user_profile import (
    get_user_profile,
    update_user_profile,
    get_user_preferences,
    UserProfile,
)

# Import User model
from database.models import User


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_user():
    """Create mock authenticated user with full profile."""
    user = Mock(spec=User)
    user.id = uuid4()
    user.username = "testuser"
    user.email = "test@example.com"
    user.role = "teacher"
    user.display_name = "Test User"
    user.avatar_url = "https://example.com/avatar.jpg"
    user.school_id = "school-123"
    user.class_ids = ["class-1", "class-2"]
    user.created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    user.last_login = datetime.now(timezone.utc)
    user.is_active = True
    return user


@pytest.fixture
def mock_minimal_user():
    """Create mock user with minimal profile data."""
    user = Mock(spec=User)
    user.email = "minimal@example.com"
    user.role = "student"
    return user


@pytest.fixture
def mock_student_user():
    """Create mock student user."""
    user = Mock(spec=User)
    user.id = uuid4()
    user.username = "student123"
    user.email = "student@school.edu"
    user.role = "student"
    user.display_name = "Student User"
    user.avatar_url = None
    user.school_id = "school-456"
    user.class_ids = ["class-3"]
    user.created_at = datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
    user.last_login = datetime.now(timezone.utc)
    user.is_active = True
    return user


# ============================================================================
# Test Get User Profile Endpoint
# ============================================================================


class TestGetUserProfile:
    """Test user profile retrieval endpoint."""

    @pytest.mark.asyncio
    async def test_get_profile_success_full_data(self, mock_user):
        """Test successful profile retrieval with full user data."""
        result = await get_user_profile(current_user=mock_user)

        assert isinstance(result, UserProfile)
        assert result.username == "testuser"
        assert result.email == "test@example.com"
        assert result.role == "teacher"
        assert result.displayName == "Test User"
        assert result.avatarUrl == "https://example.com/avatar.jpg"
        assert result.schoolId == "school-123"
        assert result.classIds == ["class-1", "class-2"]
        assert result.isActive is True

    @pytest.mark.asyncio
    async def test_get_profile_success_minimal_data(self, mock_minimal_user):
        """Test profile retrieval with minimal user data."""
        result = await get_user_profile(current_user=mock_minimal_user)

        assert isinstance(result, UserProfile)
        assert result.email == "minimal@example.com"
        assert result.role == "student"
        # Username should be derived from email
        assert result.username == "minimal"
        # displayName should default to email prefix
        assert result.displayName == "minimal"
        assert result.classIds == []

    @pytest.mark.asyncio
    async def test_get_profile_student_role(self, mock_student_user):
        """Test profile retrieval for student user."""
        result = await get_user_profile(current_user=mock_student_user)

        assert result.role == "student"
        assert result.username == "student123"
        assert len(result.classIds) == 1
        assert result.schoolId == "school-456"

    @pytest.mark.asyncio
    async def test_get_profile_unauthenticated(self):
        """Test profile retrieval without authentication."""
        with pytest.raises(HTTPException) as exc_info:
            await get_user_profile(current_user=None)

        assert exc_info.value.status_code == 401
        assert "Not authenticated" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_profile_returns_correct_types(self, mock_user):
        """Test that profile returns correct data types."""
        result = await get_user_profile(current_user=mock_user)

        assert isinstance(result.id, str)
        assert isinstance(result.username, str)
        assert isinstance(result.email, str)
        assert isinstance(result.role, str)
        assert isinstance(result.classIds, list)
        assert isinstance(result.isActive, bool)
        assert isinstance(result.createdAt, datetime)

    @pytest.mark.asyncio
    async def test_get_profile_handles_none_values(self):
        """Test profile handles None values for optional fields."""
        user = Mock(spec=User)
        user.email = "test@example.com"
        user.role = "teacher"
        user.avatar_url = None
        user.school_id = None
        user.last_login = None

        result = await get_user_profile(current_user=user)

        assert result.avatarUrl is None
        assert result.schoolId is None
        assert result.lastLogin is None

    @pytest.mark.asyncio
    async def test_get_profile_teacher_with_multiple_classes(self):
        """Test profile for teacher with multiple classes."""
        user = Mock(spec=User)
        user.id = uuid4()
        user.username = "teacher_multi"
        user.email = "teacher@school.edu"
        user.role = "teacher"
        user.class_ids = ["class-1", "class-2", "class-3", "class-4"]
        user.created_at = datetime.now(timezone.utc)
        user.is_active = True

        result = await get_user_profile(current_user=user)

        assert result.role == "teacher"
        assert len(result.classIds) == 4


# ============================================================================
# Test Update User Profile Endpoint
# ============================================================================


class TestUpdateUserProfile:
    """Test user profile update endpoint."""

    @pytest.mark.asyncio
    async def test_update_profile_success_display_name(self, mock_user):
        """Test successful profile update with displayName."""
        updates = {"displayName": "New Display Name"}

        result = await update_user_profile(updates=updates, current_user=mock_user)

        assert result["success"] is True
        assert "Profile updated successfully" in result["message"]
        assert "displayName" in result["updated_fields"]

    @pytest.mark.asyncio
    async def test_update_profile_success_avatar_url(self, mock_user):
        """Test successful profile update with avatarUrl."""
        updates = {"avatarUrl": "https://example.com/new-avatar.jpg"}

        result = await update_user_profile(updates=updates, current_user=mock_user)

        assert result["success"] is True
        assert "avatarUrl" in result["updated_fields"]

    @pytest.mark.asyncio
    async def test_update_profile_multiple_fields(self, mock_user):
        """Test updating multiple allowed fields."""
        updates = {
            "displayName": "Updated Name",
            "avatarUrl": "https://example.com/updated-avatar.jpg",
        }

        result = await update_user_profile(updates=updates, current_user=mock_user)

        assert result["success"] is True
        assert len(result["updated_fields"]) == 2
        assert "displayName" in result["updated_fields"]
        assert "avatarUrl" in result["updated_fields"]

    @pytest.mark.asyncio
    async def test_update_profile_filters_disallowed_fields(self, mock_user):
        """Test that disallowed fields are filtered out."""
        updates = {
            "displayName": "New Name",
            "email": "hacker@evil.com",  # Should be filtered
            "role": "admin",  # Should be filtered
            "password": "hack123",  # Should be filtered
        }

        result = await update_user_profile(updates=updates, current_user=mock_user)

        assert result["success"] is True
        assert len(result["updated_fields"]) == 1
        assert "displayName" in result["updated_fields"]
        assert "email" not in result["updated_fields"]
        assert "role" not in result["updated_fields"]
        assert "password" not in result["updated_fields"]

    @pytest.mark.asyncio
    async def test_update_profile_no_valid_fields(self, mock_user):
        """Test update with no valid fields to update."""
        updates = {"email": "new@email.com", "role": "admin"}

        with pytest.raises(HTTPException) as exc_info:
            await update_user_profile(updates=updates, current_user=mock_user)

        assert exc_info.value.status_code == 400
        assert "No valid fields to update" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_update_profile_empty_dict(self, mock_user):
        """Test update with empty dictionary."""
        updates = {}

        with pytest.raises(HTTPException) as exc_info:
            await update_user_profile(updates=updates, current_user=mock_user)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_update_profile_unauthenticated(self):
        """Test profile update without authentication."""
        updates = {"displayName": "Hacker"}

        with pytest.raises(HTTPException) as exc_info:
            await update_user_profile(updates=updates, current_user=None)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_update_profile_only_allowed_fields_processed(self, mock_user):
        """Test that only explicitly allowed fields are processed."""
        updates = {
            "displayName": "Valid Update",
            "avatarUrl": "https://example.com/valid.jpg",
            "school_id": "school-999",  # Not allowed
            "class_ids": ["class-999"],  # Not allowed
            "is_active": False,  # Not allowed
        }

        result = await update_user_profile(updates=updates, current_user=mock_user)

        assert len(result["updated_fields"]) == 2
        assert "school_id" not in result["updated_fields"]
        assert "class_ids" not in result["updated_fields"]
        assert "is_active" not in result["updated_fields"]


# ============================================================================
# Test Get User Preferences Endpoint
# ============================================================================


class TestGetUserPreferences:
    """Test user preferences endpoint."""

    @pytest.mark.asyncio
    async def test_get_preferences_success(self, mock_user):
        """Test successful preferences retrieval."""
        result = await get_user_preferences(current_user=mock_user)

        assert "theme" in result
        assert "language" in result
        assert "notifications" in result
        assert "privacy" in result
        assert "accessibility" in result

    @pytest.mark.asyncio
    async def test_get_preferences_has_all_categories(self, mock_user):
        """Test that all preference categories are present."""
        result = await get_user_preferences(current_user=mock_user)

        # Verify all major categories exist
        assert isinstance(result["theme"], str)
        assert isinstance(result["language"], str)
        assert isinstance(result["notifications"], dict)
        assert isinstance(result["privacy"], dict)
        assert isinstance(result["accessibility"], dict)

    @pytest.mark.asyncio
    async def test_get_preferences_notification_settings(self, mock_user):
        """Test notification preferences structure."""
        result = await get_user_preferences(current_user=mock_user)

        notifications = result["notifications"]
        assert "email" in notifications
        assert "push" in notifications
        assert "sms" in notifications
        assert isinstance(notifications["email"], bool)
        assert isinstance(notifications["push"], bool)
        assert isinstance(notifications["sms"], bool)

    @pytest.mark.asyncio
    async def test_get_preferences_privacy_settings(self, mock_user):
        """Test privacy preferences structure."""
        result = await get_user_preferences(current_user=mock_user)

        privacy = result["privacy"]
        assert "profile_visible" in privacy
        assert "show_online_status" in privacy
        assert isinstance(privacy["profile_visible"], bool)
        assert isinstance(privacy["show_online_status"], bool)

    @pytest.mark.asyncio
    async def test_get_preferences_accessibility_settings(self, mock_user):
        """Test accessibility preferences structure."""
        result = await get_user_preferences(current_user=mock_user)

        accessibility = result["accessibility"]
        assert "high_contrast" in accessibility
        assert "font_size" in accessibility
        assert "screen_reader" in accessibility
        assert isinstance(accessibility["high_contrast"], bool)
        assert isinstance(accessibility["font_size"], str)
        assert isinstance(accessibility["screen_reader"], bool)

    @pytest.mark.asyncio
    async def test_get_preferences_unauthenticated(self):
        """Test preferences retrieval without authentication."""
        with pytest.raises(HTTPException) as exc_info:
            await get_user_preferences(current_user=None)

        assert exc_info.value.status_code == 401
        assert "Not authenticated" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_preferences_student_user(self, mock_student_user):
        """Test preferences for student user."""
        result = await get_user_preferences(current_user=mock_student_user)

        # Verify preferences are returned regardless of role
        assert "theme" in result
        assert "notifications" in result

    @pytest.mark.asyncio
    async def test_get_preferences_returns_defaults(self, mock_user):
        """Test that preferences returns default values."""
        result = await get_user_preferences(current_user=mock_user)

        # Verify default values
        assert result["theme"] == "light"
        assert result["language"] == "en"
        assert result["accessibility"]["font_size"] == "medium"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

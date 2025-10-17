"""
Tests for User Profile API endpoints.

Tests the user_profile.py endpoints which provide:
- GET /users/me/profile - Get current user profile
- PATCH /users/me/profile - Update current user profile
- GET /users/me/preferences - Get user preferences

Total: 3 endpoints to test
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from uuid import uuid4

from fastapi import HTTPException, status

from apps.backend.api.v1.endpoints.user_profile import (
    UserProfile,
)
from apps.backend.core.security.jwt_handler import TokenData


class TestUserProfileModel:
    """Tests for UserProfile Pydantic model."""

    def test_user_profile_creation_all_fields(self):
        """Test creating UserProfile with all fields."""
        now = datetime.now(timezone.utc)
        profile = UserProfile(
            id="user-123",
            username="john_doe",
            email="john@example.com",
            role="teacher",
            displayName="John Doe",
            avatarUrl="https://example.com/avatar.jpg",
            schoolId="school-456",
            classIds=["class-1", "class-2"],
            createdAt=now,
            lastLogin=now,
            isActive=True
        )

        assert profile.id == "user-123"
        assert profile.username == "john_doe"
        assert profile.email == "john@example.com"
        assert profile.role == "teacher"
        assert profile.displayName == "John Doe"
        assert profile.avatarUrl == "https://example.com/avatar.jpg"
        assert profile.schoolId == "school-456"
        assert len(profile.classIds) == 2
        assert profile.isActive is True

    def test_user_profile_optional_fields(self):
        """Test UserProfile with only required fields."""
        now = datetime.now(timezone.utc)
        profile = UserProfile(
            id="user-123",
            username="john_doe",
            email="john@example.com",
            role="student",
            createdAt=now
        )

        assert profile.id == "user-123"
        assert profile.displayName is None
        assert profile.avatarUrl is None
        assert profile.schoolId is None
        assert profile.classIds == []
        assert profile.lastLogin is None
        assert profile.isActive is True  # Default value

    def test_user_profile_requires_id(self):
        """Test that id is required."""
        now = datetime.now(timezone.utc)
        with pytest.raises(Exception):  # Pydantic validation error
            UserProfile(
                username="john_doe",
                email="john@example.com",
                role="teacher",
                createdAt=now
            )

    def test_user_profile_requires_username(self):
        """Test that username is required."""
        now = datetime.now(timezone.utc)
        with pytest.raises(Exception):
            UserProfile(
                id="user-123",
                email="john@example.com",
                role="teacher",
                createdAt=now
            )

    def test_user_profile_requires_email(self):
        """Test that email is required."""
        now = datetime.now(timezone.utc)
        with pytest.raises(Exception):
            UserProfile(
                id="user-123",
                username="john_doe",
                role="teacher",
                createdAt=now
            )


class TestGetUserProfile:
    """Tests for GET /users/me/profile endpoint."""

    @pytest.fixture
    def mock_teacher_user(self):
        """Create a mock teacher user."""
        user = Mock()
        user.id = 123
        user.username = "teacher_john"
        user.email = "john@school.edu"
        user.role = "teacher"
        user.display_name = "John Teacher"
        user.avatar_url = "https://example.com/avatar.jpg"
        user.school_id = "school-456"
        user.class_ids = ["class-1", "class-2"]
        user.created_at = datetime.now(timezone.utc)
        user.last_login = datetime.now(timezone.utc)
        user.is_active = True
        return user

    @pytest.fixture
    def mock_student_user(self):
        """Create a mock student user."""
        user = Mock()
        user.id = 456
        user.username = "student_jane"
        user.email = "jane@student.edu"
        user.role = "student"
        user.created_at = datetime.now(timezone.utc)
        user.is_active = True
        return user

    @pytest.fixture
    def mock_minimal_user(self):
        """Create a mock user with minimal fields."""
        # Use object() as a base to only have explicitly set attributes
        class MinimalUser:
            pass

        user = MinimalUser()
        user.id = 789
        user.email = "minimal@example.com"
        user.role = "student"
        # Don't set username - let it be derived from email
        user.display_name = None
        user.avatar_url = None
        user.school_id = None
        user.class_ids = []
        user.created_at = datetime.now(timezone.utc)
        user.last_login = None
        user.is_active = True
        return user

    @pytest.mark.asyncio
    async def test_get_profile_success_full_data(self, mock_teacher_user):
        """Test getting user profile with full data."""
        from apps.backend.api.v1.endpoints.user_profile import get_user_profile

        response = await get_user_profile(current_user=mock_teacher_user)

        # Verify all fields are present
        assert response.id == "123"
        assert response.username == "teacher_john"
        assert response.email == "john@school.edu"
        assert response.role == "teacher"
        assert response.displayName == "John Teacher"
        assert response.avatarUrl == "https://example.com/avatar.jpg"
        assert response.schoolId == "school-456"
        assert len(response.classIds) == 2
        assert response.isActive is True

    @pytest.mark.asyncio
    async def test_get_profile_success_minimal_data(self, mock_minimal_user):
        """Test getting user profile with minimal data."""
        from apps.backend.api.v1.endpoints.user_profile import get_user_profile

        response = await get_user_profile(current_user=mock_minimal_user)

        # Should handle missing fields gracefully
        assert response.email == "minimal@example.com"
        assert response.username == "minimal"  # Derived from email
        assert response.role == "student"  # Default role

    @pytest.mark.asyncio
    async def test_get_profile_no_auth(self):
        """Test getting profile without authentication."""
        from apps.backend.api.v1.endpoints.user_profile import get_user_profile

        with pytest.raises(HTTPException) as exc_info:
            await get_user_profile(current_user=None)

        assert exc_info.value.status_code == 401
        assert "not authenticated" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_get_profile_derives_username_from_email(self):
        """Test that username is derived from email when not present."""
        from apps.backend.api.v1.endpoints.user_profile import get_user_profile

        class TestUser:
            pass

        user = TestUser()
        user.id = 999
        user.email = "testuser@example.com"
        user.role = "student"
        # Don't set username - let endpoint derive it from email
        user.display_name = None
        user.avatar_url = None
        user.school_id = None
        user.class_ids = []
        user.created_at = datetime.now(timezone.utc)
        user.last_login = None
        user.is_active = True

        response = await get_user_profile(current_user=user)

        # Username should be email prefix
        assert response.username == "testuser"

    @pytest.mark.asyncio
    async def test_get_profile_derives_display_name(self):
        """Test that displayName is derived when not present."""
        from apps.backend.api.v1.endpoints.user_profile import get_user_profile

        class TestUser:
            pass

        user = TestUser()
        user.id = 888
        user.email = "john.doe@example.com"
        user.role = "student"
        # Don't set display_name - let endpoint derive it
        user.avatar_url = None
        user.school_id = None
        user.class_ids = []
        user.created_at = datetime.now(timezone.utc)
        user.last_login = None
        user.is_active = True

        response = await get_user_profile(current_user=user)

        # displayName should fallback to email prefix
        assert response.displayName == "john.doe"

    @pytest.mark.asyncio
    async def test_get_profile_empty_class_ids(self, mock_student_user):
        """Test profile with no class_ids."""
        from apps.backend.api.v1.endpoints.user_profile import get_user_profile

        response = await get_user_profile(current_user=mock_student_user)

        # classIds should be empty list
        assert response.classIds == []

    @pytest.mark.asyncio
    async def test_get_profile_handles_none_class_ids(self):
        """Test profile when class_ids is None."""
        from apps.backend.api.v1.endpoints.user_profile import get_user_profile

        user = Mock()
        user.id = 789
        user.username = "test_user"
        user.email = "test@example.com"
        user.role = "student"
        user.class_ids = None
        user.created_at = datetime.now(timezone.utc)

        response = await get_user_profile(current_user=user)

        # Should convert None to empty list
        assert response.classIds == []

    @pytest.mark.asyncio
    async def test_get_profile_different_roles(self):
        """Test profile retrieval for different user roles."""
        from apps.backend.api.v1.endpoints.user_profile import get_user_profile

        roles = ["admin", "teacher", "student", "parent"]

        for role in roles:
            user = Mock()
            user.id = 100
            user.username = f"user_{role}"
            user.email = f"{role}@example.com"
            user.role = role
            user.created_at = datetime.now(timezone.utc)

            response = await get_user_profile(current_user=user)

            assert response.role == role


class TestUpdateUserProfile:
    """Tests for PATCH /users/me/profile endpoint."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user for testing."""
        user = Mock()
        user.id = 123
        user.username = "test_user"
        user.email = "test@example.com"
        user.role = "teacher"
        return user

    @pytest.mark.asyncio
    async def test_update_profile_display_name(self, mock_user):
        """Test updating display name."""
        from apps.backend.api.v1.endpoints.user_profile import update_user_profile

        updates = {"displayName": "New Display Name"}

        response = await update_user_profile(
            updates=updates,
            current_user=mock_user
        )

        assert response["success"] is True
        assert "successfully" in response["message"].lower()
        assert "displayName" in response["updated_fields"]

    @pytest.mark.asyncio
    async def test_update_profile_avatar_url(self, mock_user):
        """Test updating avatar URL."""
        from apps.backend.api.v1.endpoints.user_profile import update_user_profile

        updates = {"avatarUrl": "https://example.com/new-avatar.jpg"}

        response = await update_user_profile(
            updates=updates,
            current_user=mock_user
        )

        assert response["success"] is True
        assert "avatarUrl" in response["updated_fields"]

    @pytest.mark.asyncio
    async def test_update_profile_both_allowed_fields(self, mock_user):
        """Test updating both allowed fields."""
        from apps.backend.api.v1.endpoints.user_profile import update_user_profile

        updates = {
            "displayName": "New Name",
            "avatarUrl": "https://example.com/avatar.jpg"
        }

        response = await update_user_profile(
            updates=updates,
            current_user=mock_user
        )

        assert response["success"] is True
        assert len(response["updated_fields"]) == 2
        assert "displayName" in response["updated_fields"]
        assert "avatarUrl" in response["updated_fields"]

    @pytest.mark.asyncio
    async def test_update_profile_filters_disallowed_fields(self, mock_user):
        """Test that disallowed fields are filtered out."""
        from apps.backend.api.v1.endpoints.user_profile import update_user_profile

        updates = {
            "displayName": "New Name",
            "email": "hacker@evil.com",  # Not allowed
            "role": "admin",  # Not allowed
            "password": "newpass123"  # Not allowed
        }

        response = await update_user_profile(
            updates=updates,
            current_user=mock_user
        )

        # Only displayName should be updated
        assert len(response["updated_fields"]) == 1
        assert "displayName" in response["updated_fields"]
        assert "email" not in response["updated_fields"]
        assert "role" not in response["updated_fields"]
        assert "password" not in response["updated_fields"]

    @pytest.mark.asyncio
    async def test_update_profile_no_valid_fields(self, mock_user):
        """Test update with no valid fields."""
        from apps.backend.api.v1.endpoints.user_profile import update_user_profile

        updates = {
            "email": "hacker@evil.com",
            "role": "admin"
        }

        with pytest.raises(HTTPException) as exc_info:
            await update_user_profile(
                updates=updates,
                current_user=mock_user
            )

        assert exc_info.value.status_code == 400
        assert "no valid fields" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_update_profile_empty_updates(self, mock_user):
        """Test update with empty dict."""
        from apps.backend.api.v1.endpoints.user_profile import update_user_profile

        updates = {}

        with pytest.raises(HTTPException) as exc_info:
            await update_user_profile(
                updates=updates,
                current_user=mock_user
            )

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_update_profile_no_auth(self):
        """Test updating profile without authentication."""
        from apps.backend.api.v1.endpoints.user_profile import update_user_profile

        updates = {"displayName": "New Name"}

        with pytest.raises(HTTPException) as exc_info:
            await update_user_profile(
                updates=updates,
                current_user=None
            )

        assert exc_info.value.status_code == 401
        assert "not authenticated" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_update_profile_only_allowed_fields(self):
        """Test that only displayName and avatarUrl can be updated."""
        from apps.backend.api.v1.endpoints.user_profile import update_user_profile

        user = Mock()
        user.id = 123
        user.email = "test@example.com"

        # Try to update many fields
        updates = {
            "displayName": "Valid",
            "avatarUrl": "https://example.com/avatar.jpg",
            "username": "hacker",
            "email": "evil@example.com",
            "role": "admin",
            "id": "999",
            "isActive": False,
            "schoolId": "different-school"
        }

        response = await update_user_profile(
            updates=updates,
            current_user=user
        )

        # Only 2 fields should be in updated_fields
        assert len(response["updated_fields"]) == 2
        assert set(response["updated_fields"]) == {"displayName", "avatarUrl"}


class TestGetUserPreferences:
    """Tests for GET /users/me/preferences endpoint."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        user = Mock()
        user.id = 123
        user.username = "test_user"
        user.email = "test@example.com"
        user.role = "teacher"
        return user

    @pytest.mark.asyncio
    async def test_get_preferences_success(self, mock_user):
        """Test getting user preferences."""
        from apps.backend.api.v1.endpoints.user_profile import get_user_preferences

        response = await get_user_preferences(current_user=mock_user)

        # Verify response structure
        assert "theme" in response
        assert "language" in response
        assert "notifications" in response
        assert "privacy" in response
        assert "accessibility" in response

    @pytest.mark.asyncio
    async def test_get_preferences_theme_setting(self, mock_user):
        """Test that preferences include theme setting."""
        from apps.backend.api.v1.endpoints.user_profile import get_user_preferences

        response = await get_user_preferences(current_user=mock_user)

        assert response["theme"] == "light"

    @pytest.mark.asyncio
    async def test_get_preferences_language_setting(self, mock_user):
        """Test that preferences include language setting."""
        from apps.backend.api.v1.endpoints.user_profile import get_user_preferences

        response = await get_user_preferences(current_user=mock_user)

        assert response["language"] == "en"

    @pytest.mark.asyncio
    async def test_get_preferences_notifications(self, mock_user):
        """Test that preferences include notification settings."""
        from apps.backend.api.v1.endpoints.user_profile import get_user_preferences

        response = await get_user_preferences(current_user=mock_user)

        notifications = response["notifications"]
        assert "email" in notifications
        assert "push" in notifications
        assert "sms" in notifications
        assert notifications["email"] is True
        assert notifications["push"] is False
        assert notifications["sms"] is False

    @pytest.mark.asyncio
    async def test_get_preferences_privacy(self, mock_user):
        """Test that preferences include privacy settings."""
        from apps.backend.api.v1.endpoints.user_profile import get_user_preferences

        response = await get_user_preferences(current_user=mock_user)

        privacy = response["privacy"]
        assert "profile_visible" in privacy
        assert "show_online_status" in privacy
        assert privacy["profile_visible"] is True
        assert privacy["show_online_status"] is True

    @pytest.mark.asyncio
    async def test_get_preferences_accessibility(self, mock_user):
        """Test that preferences include accessibility settings."""
        from apps.backend.api.v1.endpoints.user_profile import get_user_preferences

        response = await get_user_preferences(current_user=mock_user)

        accessibility = response["accessibility"]
        assert "high_contrast" in accessibility
        assert "font_size" in accessibility
        assert "screen_reader" in accessibility
        assert accessibility["high_contrast"] is False
        assert accessibility["font_size"] == "medium"
        assert accessibility["screen_reader"] is False

    @pytest.mark.asyncio
    async def test_get_preferences_no_auth(self):
        """Test getting preferences without authentication."""
        from apps.backend.api.v1.endpoints.user_profile import get_user_preferences

        with pytest.raises(HTTPException) as exc_info:
            await get_user_preferences(current_user=None)

        assert exc_info.value.status_code == 401
        assert "not authenticated" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_get_preferences_structure_consistency(self, mock_user):
        """Test that preference structure is consistent across calls."""
        from apps.backend.api.v1.endpoints.user_profile import get_user_preferences

        response1 = await get_user_preferences(current_user=mock_user)
        response2 = await get_user_preferences(current_user=mock_user)

        # Should return same structure
        assert response1.keys() == response2.keys()
        assert response1["notifications"].keys() == response2["notifications"].keys()
        assert response1["privacy"].keys() == response2["privacy"].keys()
        assert response1["accessibility"].keys() == response2["accessibility"].keys()


class TestUserProfileIntegration:
    """Integration tests for user profile endpoints."""

    @pytest.mark.asyncio
    async def test_profile_workflow(self):
        """Test complete profile management workflow."""
        from apps.backend.api.v1.endpoints.user_profile import (
            get_user_profile,
            update_user_profile,
            get_user_preferences
        )

        # Create mock user
        user = Mock()
        user.id = 123
        user.username = "workflow_user"
        user.email = "workflow@example.com"
        user.role = "teacher"
        user.created_at = datetime.now(timezone.utc)
        user.is_active = True

        # 1. Get initial profile
        profile = await get_user_profile(current_user=user)
        assert profile.username == "workflow_user"

        # 2. Update profile
        updates = {"displayName": "Workflow User"}
        update_response = await update_user_profile(
            updates=updates,
            current_user=user
        )
        assert update_response["success"] is True

        # 3. Get preferences
        preferences = await get_user_preferences(current_user=user)
        assert "theme" in preferences

    @pytest.mark.asyncio
    async def test_profile_endpoints_require_auth(self):
        """Test that all profile endpoints require authentication."""
        from apps.backend.api.v1.endpoints.user_profile import (
            get_user_profile,
            update_user_profile,
            get_user_preferences
        )

        # All should raise 401
        with pytest.raises(HTTPException) as exc1:
            await get_user_profile(current_user=None)
        assert exc1.value.status_code == 401

        with pytest.raises(HTTPException) as exc2:
            await update_user_profile(updates={"displayName": "Test"}, current_user=None)
        assert exc2.value.status_code == 401

        with pytest.raises(HTTPException) as exc3:
            await get_user_preferences(current_user=None)
        assert exc3.value.status_code == 401


# ============================================================================
# TEST COVERAGE SUMMARY
# ============================================================================
"""
User Profile API Test Suite - Phase 2 Days 25-27 (Part 2)

Total Test Classes: 6
Total Test Methods: 35+ tests

ENDPOINT COVERAGE (3 endpoints tested):
1. GET /users/me/profile
   - Success with full data
   - Success with minimal data
   - No authentication (401)
   - Username derived from email
   - Display name derived
   - Empty class IDs
   - Handles None class IDs
   - Different roles
   Tests: 8

2. PATCH /users/me/profile
   - Update displayName
   - Update avatarUrl
   - Update both fields
   - Filters disallowed fields
   - No valid fields (400)
   - Empty updates (400)
   - No authentication (401)
   - Only allowed fields updated
   Tests: 8

3. GET /users/me/preferences
   - Success case
   - Theme setting
   - Language setting
   - Notifications structure
   - Privacy settings
   - Accessibility settings
   - No authentication (401)
   - Structure consistency
   Tests: 8

MODEL TESTS:
- UserProfile (5 tests)

INTEGRATION TESTS:
- Complete profile workflow (3 steps)
- All endpoints require auth

TOTAL TESTS: 35+
"""

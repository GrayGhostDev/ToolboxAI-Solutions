"""
Unit Tests for Password Management Endpoints

Tests password change, reset, validation, and session management endpoints.

Phase 1 Week 1: Authentication & user management endpoint tests
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException, Request, status

# Import endpoint functions and models directly
from apps.backend.api.v1.endpoints.password import (
    change_password,
    get_active_sessions,
    get_password_requirements,
    logout_all_sessions,
    reset_user_password,
    validate_password_strength,
)

# Import models
from apps.backend.models.schemas import User

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_current_user():
    """Create mock authenticated user."""
    user = Mock(spec=User)
    user.id = uuid4()
    user.username = "testuser"
    user.email = "test@example.com"
    user.role = "teacher"
    return user


@pytest.fixture
def mock_admin_user():
    """Create mock admin user."""
    user = Mock(spec=User)
    user.id = uuid4()
    user.username = "admin"
    user.email = "admin@example.com"
    user.role = "admin"
    return user


@pytest.fixture
def mock_request():
    """Create mock FastAPI request."""
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"
    request.headers = {"User-Agent": "Test Browser/1.0"}
    return request


@pytest.fixture
def mock_password_service():
    """Create mock password service."""
    service = AsyncMock()
    return service


@pytest.fixture
def mock_session_manager():
    """Create mock session manager."""
    manager = Mock()
    manager.max_sessions_per_user = 5
    return manager


@pytest.fixture
def password_change_request():
    """Valid password change request data."""
    from apps.backend.api.auth.password_management import PasswordChangeRequest

    return PasswordChangeRequest(
        current_password="CurrentPassword123!",
        new_password="NewPassword123!",
        confirm_password="NewPassword123!",
        logout_all_devices=True,
    )


@pytest.fixture
def password_reset_request():
    """Valid password reset request data."""
    from apps.backend.api.auth.password_management import PasswordResetRequest

    return PasswordResetRequest(
        user_id=uuid4(),
        new_password="ResetPassword123!",
        reason="User forgot password",
        force_logout=True,
    )


# ============================================================================
# Test Change Password Endpoint
# ============================================================================


class TestChangePassword:
    """Test password change endpoint."""

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.password.get_user_from_db")
    @patch("apps.backend.api.v1.endpoints.password.verify_password")
    @patch("apps.backend.api.v1.endpoints.password.password_service")
    @patch("apps.backend.api.v1.endpoints.password.get_db_session")
    @patch("apps.backend.api.v1.endpoints.password.update_user_password")
    async def test_change_password_success(
        self,
        mock_update_password,
        mock_get_db_session,
        mock_password_service,
        mock_verify_password,
        mock_get_user_from_db,
        mock_request,
        mock_current_user,
        password_change_request,
    ):
        """Test successful password change."""
        # Setup mocks
        mock_get_user_from_db.return_value = {"password_hash": "old_hash"}
        mock_verify_password.return_value = True
        mock_password_service.change_password.return_value = {
            "success": True,
            "message": "Password changed successfully",
            "sessions_invalidated": 2,
            "password_hash": "new_hash",
            "remaining_changes_today": 4,
            "password_strength_score": 85,
            "action_required": "Please login again",
        }

        result = await change_password(
            request=mock_request,
            password_request=password_change_request,
            current_user=mock_current_user,
        )

        assert result["success"] is True
        assert result["sessions_invalidated"] == 2
        assert result["remaining_changes_today"] == 4
        assert "password_hash" not in result  # Should be removed from response

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.password.get_user_from_db")
    @patch("apps.backend.api.v1.endpoints.password.verify_password")
    async def test_change_password_incorrect_current_password(
        self,
        mock_verify_password,
        mock_get_user_from_db,
        mock_request,
        mock_current_user,
        password_change_request,
    ):
        """Test password change with incorrect current password."""
        mock_get_user_from_db.return_value = {"password_hash": "old_hash"}
        mock_verify_password.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await change_password(
                request=mock_request,
                password_request=password_change_request,
                current_user=mock_current_user,
            )

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Current password is incorrect" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.password.get_user_from_db")
    async def test_change_password_user_not_found(
        self, mock_get_user_from_db, mock_request, mock_current_user, password_change_request
    ):
        """Test password change when user not found in database."""
        mock_get_user_from_db.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await change_password(
                request=mock_request,
                password_request=password_change_request,
                current_user=mock_current_user,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.password.get_user_from_db")
    @patch("apps.backend.api.v1.endpoints.password.verify_password")
    @patch("apps.backend.api.v1.endpoints.password.password_service")
    async def test_change_password_service_error(
        self,
        mock_password_service,
        mock_verify_password,
        mock_get_user_from_db,
        mock_request,
        mock_current_user,
        password_change_request,
    ):
        """Test handling of password service errors."""
        mock_get_user_from_db.return_value = {"password_hash": "old_hash"}
        mock_verify_password.return_value = True
        mock_password_service.change_password.side_effect = Exception("Service error")

        with pytest.raises(HTTPException) as exc_info:
            await change_password(
                request=mock_request,
                password_request=password_change_request,
                current_user=mock_current_user,
            )

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


# ============================================================================
# Test Reset Password Endpoint
# ============================================================================


class TestResetPassword:
    """Test password reset endpoint (admin only)."""

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.password.password_service")
    @patch("apps.backend.api.v1.endpoints.password.get_db_session")
    @patch("apps.backend.api.v1.endpoints.password.update_user_password")
    async def test_reset_password_success(
        self,
        mock_update_password,
        mock_get_db_session,
        mock_password_service,
        mock_request,
        mock_admin_user,
        password_reset_request,
    ):
        """Test successful password reset by admin."""
        mock_password_service.reset_password.return_value = {
            "success": True,
            "message": "Password reset successfully",
            "sessions_invalidated": 3,
            "password_hash": "new_hash",
            "reset_by": "admin",
            "reset_reason": "User forgot password",
        }

        result = await reset_user_password(
            request=mock_request,
            reset_request=password_reset_request,
            current_user=mock_admin_user,
        )

        assert result["success"] is True
        assert result["sessions_invalidated"] == 3
        assert result["reset_by"] == "admin"
        assert "password_hash" not in result

    @pytest.mark.asyncio
    async def test_reset_password_non_admin_forbidden(
        self, mock_request, mock_current_user, password_reset_request
    ):
        """Test that non-admin users cannot reset passwords."""
        with pytest.raises(HTTPException) as exc_info:
            await reset_user_password(
                request=mock_request,
                reset_request=password_reset_request,
                current_user=mock_current_user,
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "administrators" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.password.password_service")
    async def test_reset_password_service_error(
        self, mock_password_service, mock_request, mock_admin_user, password_reset_request
    ):
        """Test handling of password service errors during reset."""
        mock_password_service.reset_password.side_effect = Exception("Service error")

        with pytest.raises(HTTPException) as exc_info:
            await reset_user_password(
                request=mock_request,
                reset_request=password_reset_request,
                current_user=mock_admin_user,
            )

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


# ============================================================================
# Test Password Requirements Endpoint
# ============================================================================


class TestPasswordRequirements:
    """Test password requirements endpoint."""

    @pytest.mark.asyncio
    async def test_get_password_requirements(self):
        """Test retrieving password requirements."""
        result = await get_password_requirements()

        # Verify required fields
        assert "min_length" in result
        assert "max_length" in result
        assert "require_uppercase" in result
        assert "require_lowercase" in result
        assert "require_digit" in result
        assert "require_special" in result
        assert "special_characters" in result
        assert "password_history" in result
        assert "max_changes_per_day" in result

        # Verify reasonable values
        assert result["min_length"] >= 8
        assert result["max_length"] > result["min_length"]
        assert isinstance(result["require_uppercase"], bool)

    @pytest.mark.asyncio
    async def test_password_requirements_returns_dict(self):
        """Test that requirements returns a dictionary."""
        result = await get_password_requirements()

        assert isinstance(result, dict)
        assert len(result) >= 9


# ============================================================================
# Test Password Validation Endpoint
# ============================================================================


class TestValidatePasswordStrength:
    """Test password validation endpoint."""

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.password.PasswordValidator")
    async def test_validate_strong_password(self, mock_validator_class, mock_current_user):
        """Test validation of a strong password."""
        mock_validator = Mock()
        mock_result = Mock()
        mock_result.is_valid = True
        mock_result.score = 85
        mock_result.issues = []
        mock_result.suggestions = []

        mock_validator.validate.return_value = mock_result
        mock_validator_class.return_value = mock_validator

        result = await validate_password_strength(
            password="StrongPassword123!", username="testuser", current_user=mock_current_user
        )

        assert result["is_valid"] is True
        assert result["score"] == 85
        assert len(result["issues"]) == 0

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.password.PasswordValidator")
    async def test_validate_weak_password(self, mock_validator_class, mock_current_user):
        """Test validation of a weak password."""
        mock_validator = Mock()
        mock_result = Mock()
        mock_result.is_valid = False
        mock_result.score = 30
        mock_result.issues = ["Password too short", "No special characters"]
        mock_result.suggestions = ["Use at least 8 characters", "Add special characters"]

        mock_validator.validate.return_value = mock_result
        mock_validator_class.return_value = mock_validator

        result = await validate_password_strength(
            password="weak", username=None, current_user=mock_current_user
        )

        assert result["is_valid"] is False
        assert result["score"] == 30
        assert len(result["issues"]) > 0
        assert len(result["suggestions"]) > 0

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.password.PasswordValidator")
    async def test_validate_uses_current_user_username_by_default(
        self, mock_validator_class, mock_current_user
    ):
        """Test that validation uses current user's username if not provided."""
        mock_validator = Mock()
        mock_result = Mock()
        mock_result.is_valid = True
        mock_result.score = 75
        mock_result.issues = []
        mock_result.suggestions = []

        mock_validator.validate.return_value = mock_result
        mock_validator_class.return_value = mock_validator

        await validate_password_strength(
            password="TestPassword123!", username=None, current_user=mock_current_user
        )

        # Verify it was called with current user's username
        mock_validator.validate.assert_called_once_with(
            "TestPassword123!", mock_current_user.username
        )


# ============================================================================
# Test Active Sessions Endpoint
# ============================================================================


class TestGetActiveSessions:
    """Test active sessions endpoint."""

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.password.session_manager")
    async def test_get_active_sessions_success(self, mock_session_manager, mock_current_user):
        """Test retrieving active sessions."""
        mock_session1 = Mock()
        mock_session1.session_id = "session123456789"
        mock_session1.created_at = datetime.now()
        mock_session1.last_activity = datetime.now()
        mock_session1.expires_at = datetime.now()
        mock_session1.ip_address = "192.168.1.1"
        mock_session1.user_agent = "Browser/1.0"
        mock_session1.device_id = "device123"

        mock_session_manager.get_user_sessions.return_value = [mock_session1]
        mock_session_manager.max_sessions_per_user = 5

        result = await get_active_sessions(current_user=mock_current_user)

        assert result["total"] == 1
        assert result["max_allowed"] == 5
        assert len(result["sessions"]) == 1
        assert result["sessions"][0]["ip_address"] == "192.168.1.1"
        # Verify session ID is truncated for security
        assert result["sessions"][0]["session_id"].endswith("...")

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.password.session_manager")
    async def test_get_active_sessions_empty(self, mock_session_manager, mock_current_user):
        """Test retrieving sessions when none exist."""
        mock_session_manager.get_user_sessions.return_value = []
        mock_session_manager.max_sessions_per_user = 5

        result = await get_active_sessions(current_user=mock_current_user)

        assert result["total"] == 0
        assert len(result["sessions"]) == 0

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.password.session_manager")
    async def test_get_active_sessions_multiple(self, mock_session_manager, mock_current_user):
        """Test retrieving multiple active sessions."""
        mock_sessions = []
        for i in range(3):
            mock_session = Mock()
            mock_session.session_id = f"session{i}123456789"
            mock_session.created_at = datetime.now()
            mock_session.last_activity = datetime.now()
            mock_session.expires_at = datetime.now()
            mock_session.ip_address = f"192.168.1.{i}"
            mock_session.user_agent = f"Browser/{i}.0"
            mock_session.device_id = f"device{i}"
            mock_sessions.append(mock_session)

        mock_session_manager.get_user_sessions.return_value = mock_sessions
        mock_session_manager.max_sessions_per_user = 5

        result = await get_active_sessions(current_user=mock_current_user)

        assert result["total"] == 3
        assert len(result["sessions"]) == 3


# ============================================================================
# Test Logout All Sessions Endpoint
# ============================================================================


class TestLogoutAllSessions:
    """Test logout all sessions endpoint."""

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.password.session_manager")
    async def test_logout_all_sessions_success(self, mock_session_manager, mock_current_user):
        """Test successfully logging out from all devices."""
        mock_session_manager.invalidate_all_user_sessions.return_value = 3

        result = await logout_all_sessions(current_user=mock_current_user)

        assert result["success"] is True
        assert result["sessions_invalidated"] == 3
        assert "3 device(s)" in result["message"]

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.password.session_manager")
    async def test_logout_all_sessions_none_active(self, mock_session_manager, mock_current_user):
        """Test logging out when no sessions are active."""
        mock_session_manager.invalidate_all_user_sessions.return_value = 0

        result = await logout_all_sessions(current_user=mock_current_user)

        assert result["success"] is True
        assert result["sessions_invalidated"] == 0

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.password.session_manager")
    async def test_logout_all_sessions_service_error(self, mock_session_manager, mock_current_user):
        """Test handling of service errors during logout."""
        mock_session_manager.invalidate_all_user_sessions.side_effect = Exception("Service error")

        with pytest.raises(HTTPException) as exc_info:
            await logout_all_sessions(current_user=mock_current_user)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

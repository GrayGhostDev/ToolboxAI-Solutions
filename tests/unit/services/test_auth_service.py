"""
Unit tests for Authentication Service

Tests all authentication and authorization operations including user authentication,
token management, permission checking, and resource access control.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta, timezone

from apps.backend.services.auth_service import AuthService, get_auth_service
from apps.backend.models.schemas import User


@pytest.fixture
def auth_service():
    """AuthService instance"""
    return AuthService()


@pytest.fixture
def sample_user():
    """Sample user for testing"""
    return User(
        id="user_123",
        username="testuser",
        email="testuser@example.com",
        role="student",
        is_active=True
    )


@pytest.fixture
def admin_user():
    """Admin user for testing"""
    return User(
        id="admin_123",
        username="adminuser",
        email="admin@example.com",
        role="admin",
        is_active=True
    )


@pytest.fixture
def teacher_user():
    """Teacher user for testing"""
    return User(
        id="teacher_123",
        username="teacheruser",
        email="teacher@example.com",
        role="teacher",
        is_active=True
    )


@pytest.fixture
def inactive_user():
    """Inactive user for testing"""
    return User(
        id="inactive_123",
        username="inactiveuser",
        email="inactive@example.com",
        role="student",
        is_active=False
    )


@pytest.mark.unit
class TestAuthentication:
    """Test user authentication methods"""

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service):
        """Test successful user authentication"""
        user = await auth_service.authenticate_user("testuser", "password123")

        assert user is not None
        assert user.username == "testuser"
        assert user.email == "testuser@example.com"
        assert user.role == "student"
        assert user.is_active is True

    @pytest.mark.asyncio
    async def test_authenticate_user_empty_username(self, auth_service):
        """Test authentication with empty username"""
        user = await auth_service.authenticate_user("", "password123")

        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_empty_password(self, auth_service):
        """Test authentication with empty password"""
        user = await auth_service.authenticate_user("testuser", "")

        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_both_empty(self, auth_service):
        """Test authentication with both credentials empty"""
        user = await auth_service.authenticate_user("", "")

        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_exception(self, auth_service):
        """Test authentication with exception"""
        with patch('apps.backend.services.auth_service.User', side_effect=Exception("Database error")):
            user = await auth_service.authenticate_user("testuser", "password123")

            assert user is None


@pytest.mark.unit
class TestUserRetrieval:
    """Test user retrieval methods"""

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, auth_service):
        """Test successful user retrieval by ID"""
        user = await auth_service.get_user_by_id("user_123")

        assert user is not None
        assert user.id == "user_123"
        assert user.username == "user_user_123"
        assert user.email == "user_user_123@example.com"
        assert user.role == "student"

    @pytest.mark.asyncio
    async def test_get_user_by_id_exception(self, auth_service):
        """Test user retrieval with exception"""
        with patch('apps.backend.services.auth_service.User', side_effect=Exception("Database error")):
            user = await auth_service.get_user_by_id("user_123")

            assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_token_success(self, auth_service, sample_user):
        """Test successful user retrieval by token"""
        mock_payload = {
            "sub": "user_123",
            "username": "testuser",
            "role": "student"
        }

        with patch('apps.backend.services.auth_service.decode_jwt_token', return_value=mock_payload):
            user = await auth_service.get_user_by_token("valid_token")

            assert user is not None
            assert user.id == "user_123"

    @pytest.mark.asyncio
    async def test_get_user_by_token_invalid_token(self, auth_service):
        """Test user retrieval with invalid token"""
        with patch('apps.backend.services.auth_service.decode_jwt_token', return_value=None):
            user = await auth_service.get_user_by_token("invalid_token")

            assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_token_missing_sub(self, auth_service):
        """Test user retrieval with token missing 'sub' claim"""
        mock_payload = {
            "username": "testuser",
            "role": "student"
        }

        with patch('apps.backend.services.auth_service.decode_jwt_token', return_value=mock_payload):
            user = await auth_service.get_user_by_token("token_without_sub")

            assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_token_exception(self, auth_service):
        """Test user retrieval with exception"""
        with patch('apps.backend.services.auth_service.decode_jwt_token', side_effect=Exception("Decode error")):
            user = await auth_service.get_user_by_token("token")

            assert user is None


@pytest.mark.unit
class TestTokenManagement:
    """Test token creation and management"""

    @pytest.mark.asyncio
    async def test_create_access_token_success(self, auth_service, sample_user):
        """Test successful access token creation"""
        mock_token = "mock_jwt_token_abc123"

        with patch('apps.backend.services.auth_service.create_jwt_token', return_value=mock_token):
            result = await auth_service.create_access_token(sample_user)

            assert result["access_token"] == mock_token
            assert result["token_type"] == "bearer"
            assert result["expires_in"] == 30 * 60  # Default 30 minutes
            assert result["user"]["id"] == sample_user.id
            assert result["user"]["username"] == sample_user.username
            assert result["user"]["email"] == sample_user.email
            assert result["user"]["role"] == sample_user.role

    @pytest.mark.asyncio
    async def test_create_access_token_custom_expiry(self, sample_user):
        """Test access token creation with custom expiry"""
        service = AuthService()
        service.token_expire_minutes = 60  # 1 hour

        mock_token = "mock_jwt_token_xyz789"

        with patch('apps.backend.services.auth_service.create_jwt_token', return_value=mock_token):
            result = await service.create_access_token(sample_user)

            assert result["expires_in"] == 60 * 60

    @pytest.mark.asyncio
    async def test_create_access_token_exception(self, auth_service, sample_user):
        """Test access token creation with exception"""
        with patch('apps.backend.services.auth_service.create_jwt_token', side_effect=Exception("JWT error")):
            with pytest.raises(Exception):
                await auth_service.create_access_token(sample_user)

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, auth_service):
        """Test successful token refresh"""
        mock_payload = {"sub": "user_123"}
        mock_new_token = "new_access_token"

        with patch('apps.backend.services.auth_service.decode_jwt_token', return_value=mock_payload):
            with patch('apps.backend.services.auth_service.create_jwt_token', return_value=mock_new_token):
                result = await auth_service.refresh_token("refresh_token")

                assert result is not None
                assert result["access_token"] == mock_new_token
                assert result["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_refresh_token_invalid_token(self, auth_service):
        """Test token refresh with invalid token"""
        with patch('apps.backend.services.auth_service.decode_jwt_token', return_value=None):
            result = await auth_service.refresh_token("invalid_token")

            assert result is None

    @pytest.mark.asyncio
    async def test_refresh_token_exception(self, auth_service):
        """Test token refresh with exception"""
        with patch('apps.backend.services.auth_service.decode_jwt_token', side_effect=Exception("Decode error")):
            result = await auth_service.refresh_token("token")

            assert result is None

    @pytest.mark.asyncio
    async def test_revoke_token_success(self, auth_service):
        """Test successful token revocation"""
        result = await auth_service.revoke_token("token_to_revoke")

        assert result is True

    @pytest.mark.asyncio
    async def test_revoke_token_exception(self, auth_service):
        """Test token revocation with exception"""
        with patch('apps.backend.services.auth_service.logger') as mock_logger:
            mock_logger.info.side_effect = Exception("Logging error")
            result = await auth_service.revoke_token("token")

            assert result is False


@pytest.mark.unit
class TestPermissionChecking:
    """Test permission checking methods"""

    @pytest.mark.asyncio
    async def test_check_user_permissions_admin(self, auth_service, admin_user):
        """Test admin user has all permissions"""
        result = await auth_service.check_user_permissions(admin_user, ["teacher", "student"])

        assert result is True

    @pytest.mark.asyncio
    async def test_check_user_permissions_role_match(self, auth_service, sample_user):
        """Test permission check with matching role"""
        result = await auth_service.check_user_permissions(sample_user, ["student", "teacher"])

        assert result is True

    @pytest.mark.asyncio
    async def test_check_user_permissions_role_mismatch(self, auth_service, sample_user):
        """Test permission check with non-matching role"""
        result = await auth_service.check_user_permissions(sample_user, ["admin", "teacher"])

        assert result is False

    @pytest.mark.asyncio
    async def test_check_user_permissions_inactive_user(self, auth_service, inactive_user):
        """Test permission check for inactive user"""
        result = await auth_service.check_user_permissions(inactive_user, ["student"])

        assert result is False

    @pytest.mark.asyncio
    async def test_check_user_permissions_none_user(self, auth_service):
        """Test permission check with None user"""
        result = await auth_service.check_user_permissions(None, ["student"])

        assert result is False

    @pytest.mark.asyncio
    async def test_check_user_permissions_exception(self, auth_service, sample_user):
        """Test permission check with exception"""
        # Make user.role raise exception
        sample_user.role = None
        sample_user.is_active = None

        result = await auth_service.check_user_permissions(sample_user, ["student"])

        assert result is False


@pytest.mark.unit
class TestResourceAccess:
    """Test resource access control"""

    @pytest.mark.asyncio
    async def test_check_resource_access_admin_all_access(self, auth_service, admin_user):
        """Test admin has access to all resources"""
        result = await auth_service.check_resource_access(
            admin_user, "content", "content_123", "delete"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_check_resource_access_teacher_content(self, auth_service, teacher_user):
        """Test teacher access to content"""
        result = await auth_service.check_resource_access(
            teacher_user, "content", "content_123", "write"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_check_resource_access_teacher_class(self, auth_service, teacher_user):
        """Test teacher access to class"""
        result = await auth_service.check_resource_access(
            teacher_user, "class", "class_123", "write"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_check_resource_access_teacher_lesson(self, auth_service, teacher_user):
        """Test teacher access to lesson"""
        result = await auth_service.check_resource_access(
            teacher_user, "lesson", "lesson_123", "write"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_check_resource_access_student_read(self, auth_service, sample_user):
        """Test student read access to content"""
        result = await auth_service.check_resource_access(
            sample_user, "content", "content_123", "read"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_check_resource_access_student_write_denied(self, auth_service, sample_user):
        """Test student write access denied"""
        result = await auth_service.check_resource_access(
            sample_user, "content", "content_123", "write"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_check_resource_access_own_user_resource(self, auth_service, sample_user):
        """Test user access to own user resource"""
        result = await auth_service.check_resource_access(
            sample_user, "user", "user_123", "read"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_check_resource_access_other_user_resource(self, auth_service, sample_user):
        """Test user access to other user resource denied"""
        result = await auth_service.check_resource_access(
            sample_user, "user", "other_user_456", "read"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_check_resource_access_inactive_user(self, auth_service, inactive_user):
        """Test inactive user denied access"""
        result = await auth_service.check_resource_access(
            inactive_user, "content", "content_123", "read"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_check_resource_access_none_user(self, auth_service):
        """Test None user denied access"""
        result = await auth_service.check_resource_access(
            None, "content", "content_123", "read"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_check_resource_access_exception(self, auth_service, sample_user):
        """Test resource access check with exception"""
        sample_user.is_active = None  # Cause exception

        result = await auth_service.check_resource_access(
            sample_user, "content", "content_123", "read"
        )

        assert result is False


@pytest.mark.unit
class TestUserStats:
    """Test user statistics and activity"""

    @pytest.mark.asyncio
    async def test_get_user_stats_success(self, auth_service):
        """Test successful user stats retrieval"""
        stats = await auth_service.get_user_stats("user_123")

        assert stats["user_id"] == "user_123"
        assert stats["login_count"] == 50
        assert "last_login" in stats
        assert stats["content_generated"] == 25
        assert stats["lessons_completed"] == 10
        assert stats["assessments_taken"] == 8
        assert stats["total_time_spent"] == 3600

    @pytest.mark.asyncio
    async def test_get_user_stats_exception(self, auth_service):
        """Test user stats retrieval with exception"""
        with patch('apps.backend.services.auth_service.datetime', side_effect=Exception("Time error")):
            stats = await auth_service.get_user_stats("user_123")

            assert stats == {}

    @pytest.mark.asyncio
    async def test_update_user_activity_success(self, auth_service):
        """Test successful activity update"""
        result = await auth_service.update_user_activity(
            "user_123",
            "login",
            {"ip_address": "127.0.0.1", "user_agent": "Mozilla"}
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_update_user_activity_different_types(self, auth_service):
        """Test activity updates for different types"""
        # Test content generation
        result1 = await auth_service.update_user_activity(
            "user_123", "content_generated", {"content_id": "content_456"}
        )
        assert result1 is True

        # Test lesson completion
        result2 = await auth_service.update_user_activity(
            "user_123", "lesson_completed", {"lesson_id": "lesson_789"}
        )
        assert result2 is True

    @pytest.mark.asyncio
    async def test_update_user_activity_exception(self, auth_service):
        """Test activity update with exception"""
        with patch('apps.backend.services.auth_service.logger') as mock_logger:
            mock_logger.info.side_effect = Exception("Logging error")
            result = await auth_service.update_user_activity("user_123", "login", {})

            assert result is False


@pytest.mark.unit
class TestServiceInstance:
    """Test global service instance"""

    def test_get_auth_service_returns_instance(self):
        """Test global service instance retrieval"""
        service = get_auth_service()

        assert service is not None
        assert isinstance(service, AuthService)

    def test_get_auth_service_singleton(self):
        """Test service instance is singleton"""
        service1 = get_auth_service()
        service2 = get_auth_service()

        assert service1 is service2


@pytest.mark.unit
class TestServiceConfiguration:
    """Test service configuration"""

    def test_default_token_expiry(self):
        """Test default token expiry is 30 minutes"""
        service = AuthService()

        assert service.token_expire_minutes == 30

    def test_custom_token_expiry_from_settings(self):
        """Test custom token expiry from settings"""
        with patch('apps.backend.services.auth_service.settings') as mock_settings:
            mock_settings.TOKEN_EXPIRE_MINUTES = 60
            service = AuthService()

            assert service.token_expire_minutes == 60

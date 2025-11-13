"""
Unit Tests for Secure User Manager

Tests user management functionality including:
- User creation with validation
- Authentication with lockout protection
- Password management (change, reset, validation)
- Security features (MFA, password history, account lockout)
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from apps.backend.core.security.user_manager import (
    AuthenticationError,
    SecureUserManager,
    UserRole,
)
from database.models import User


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = Mock(spec=Session)
    session.add = Mock()
    session.commit = Mock()
    session.refresh = Mock()
    session.query = Mock()
    return session


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis_client = Mock()
    redis_client.get = Mock(return_value=None)
    redis_client.set = Mock(return_value=True)
    redis_client.setex = Mock(return_value=True)
    redis_client.delete = Mock(return_value=1)
    redis_client.exists = Mock(return_value=0)
    redis_client.lpush = Mock()
    redis_client.lrange = Mock(return_value=[])
    redis_client.ltrim = Mock()
    return redis_client


@pytest.fixture
def user_manager(mock_db_session, mock_redis):
    """User manager instance with mocked dependencies"""
    return SecureUserManager(db_session=mock_db_session, redis_client=mock_redis)


@pytest.fixture
def sample_user():
    """Sample user for testing"""
    user = Mock(spec=User)
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.password_hash = "$2b$12$test_hash"
    user.role = "teacher"
    user.is_active = True
    user.failed_login_attempts = 0
    user.password_changed_at = datetime.now(timezone.utc)
    return user


class TestUserCreation:
    """Test user creation and validation."""

    @pytest.mark.asyncio
    async def test_create_user_success(self, user_manager, mock_db_session):
        """Test successful user creation."""
        # Arrange
        username = "newuser"
        email = "newuser@example.com"
        password = "SecurePass123!@#"
        role = UserRole.TEACHER

        # Mock no existing user
        mock_result = Mock()
        mock_result.first = Mock(return_value=None)
        mock_db_session.query.return_value.filter.return_value = mock_result

        # Act
        user = await user_manager.create_user(username, email, password, role)

        # Assert
        assert user is not None
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_duplicate(self, user_manager, mock_db_session, sample_user):
        """Test user creation with duplicate username/email."""
        # Arrange
        # Mock existing user
        mock_result = Mock()
        mock_result.first = Mock(return_value=sample_user)
        mock_db_session.query.return_value.filter.return_value = mock_result

        # Act & Assert
        with pytest.raises(AuthenticationError) as exc_info:
            await user_manager.create_user(
                "testuser", "test@example.com", "SecurePass123!@#", UserRole.TEACHER
            )

        assert "already exists" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_create_user_invalid_password(self, user_manager, mock_db_session):
        """Test user creation with invalid password."""
        # Arrange
        mock_result = Mock()
        mock_result.first = Mock(return_value=None)
        mock_db_session.query.return_value.filter.return_value = mock_result

        # Act & Assert - Too short
        with pytest.raises(ValueError) as exc_info:
            await user_manager.create_user(
                "newuser", "newuser@example.com", "short", UserRole.TEACHER  # Too short
            )

        assert "at least" in str(exc_info.value).lower()


class TestAuthentication:
    """Test user authentication flow."""

    @pytest.mark.asyncio
    async def test_authenticate_success(
        self, user_manager, mock_db_session, mock_redis, sample_user
    ):
        """Test successful authentication."""
        # Arrange
        mock_redis.exists.return_value = 0  # Not locked out

        # Mock user lookup
        mock_result = Mock()
        mock_result.first = Mock(return_value=sample_user)
        mock_db_session.query.return_value.filter.return_value = mock_result

        # Mock password verification
        with patch.object(user_manager, "_verify_password", return_value=True):
            with patch.object(user_manager, "_is_password_expired", return_value=False):
                with patch.object(
                    user_manager, "_create_session", return_value="session_token_123"
                ):
                    # Act
                    user, token = await user_manager.authenticate(
                        "testuser", "correct_password", ip_address="127.0.0.1"
                    )

                    # Assert
                    assert user == sample_user
                    assert token == "session_token_123"
                    assert sample_user.failed_login_attempts == 0

    @pytest.mark.asyncio
    async def test_authenticate_invalid_credentials(
        self, user_manager, mock_db_session, mock_redis, sample_user
    ):
        """Test authentication with invalid credentials."""
        # Arrange
        mock_redis.exists.return_value = 0

        mock_result = Mock()
        mock_result.first = Mock(return_value=sample_user)
        mock_db_session.query.return_value.filter.return_value = mock_result

        # Mock password verification failure
        with patch.object(user_manager, "_verify_password", return_value=False):
            # Act & Assert
            with pytest.raises(AuthenticationError) as exc_info:
                await user_manager.authenticate(
                    "testuser", "wrong_password", ip_address="127.0.0.1"
                )

            assert "Invalid credentials" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_authenticate_account_lockout(self, user_manager, mock_redis):
        """Test authentication blocked by account lockout."""
        # Arrange
        mock_redis.exists.return_value = 1  # Account is locked out

        # Act & Assert
        with pytest.raises(AuthenticationError) as exc_info:
            await user_manager.authenticate("testuser", "password", ip_address="127.0.0.1")

        assert exc_info.value.status_code == 423  # HTTP_423_LOCKED
        assert "locked" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_authenticate_inactive_account(
        self, user_manager, mock_db_session, mock_redis, sample_user
    ):
        """Test authentication with inactive account."""
        # Arrange
        mock_redis.exists.return_value = 0
        sample_user.is_active = False

        mock_result = Mock()
        mock_result.first = Mock(return_value=sample_user)
        mock_db_session.query.return_value.filter.return_value = mock_result

        # Act & Assert
        with pytest.raises(AuthenticationError) as exc_info:
            await user_manager.authenticate("testuser", "password", ip_address="127.0.0.1")

        assert "deactivated" in str(exc_info.value.detail).lower()


class TestPasswordManagement:
    """Test password change and reset functionality."""

    @pytest.mark.asyncio
    async def test_change_password_success(self, user_manager, mock_db_session, sample_user):
        """Test successful password change."""
        # Arrange
        mock_result = Mock()
        mock_result.first = Mock(return_value=sample_user)
        mock_db_session.query.return_value.filter.return_value = mock_result

        # Mock password verification and validation
        with patch.object(user_manager, "_verify_password", return_value=True):
            with patch.object(user_manager, "_validate_password"):
                with patch.object(user_manager, "_is_password_reused", return_value=False):
                    with patch.object(user_manager, "_add_to_password_history", return_value=None):
                        with patch.object(
                            user_manager, "_invalidate_user_sessions", return_value=None
                        ):
                            # Act
                            result = await user_manager.change_password(
                                user_id=sample_user.id,
                                current_password="old_password",
                                new_password="NewSecurePass123!@#",
                            )

                            # Assert
                            assert result is True
                            mock_db_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_change_password_invalid_current(
        self, user_manager, mock_db_session, sample_user
    ):
        """Test password change with incorrect current password."""
        # Arrange
        mock_result = Mock()
        mock_result.first = Mock(return_value=sample_user)
        mock_db_session.query.return_value.filter.return_value = mock_result

        # Mock password verification failure
        with patch.object(user_manager, "_verify_password", return_value=False):
            # Act & Assert
            with pytest.raises(AuthenticationError) as exc_info:
                await user_manager.change_password(
                    user_id=sample_user.id,
                    current_password="wrong_password",
                    new_password="NewSecurePass123!@#",
                )

            assert "incorrect" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_change_password_reused(self, user_manager, mock_db_session, sample_user):
        """Test password change with recently used password."""
        # Arrange
        mock_result = Mock()
        mock_result.first = Mock(return_value=sample_user)
        mock_db_session.query.return_value.filter.return_value = mock_result

        with patch.object(user_manager, "_verify_password", return_value=True):
            with patch.object(user_manager, "_validate_password"):
                with patch.object(user_manager, "_is_password_reused", return_value=True):
                    # Act & Assert
                    with pytest.raises(AuthenticationError) as exc_info:
                        await user_manager.change_password(
                            user_id=sample_user.id,
                            current_password="old_password",
                            new_password="ReusedPassword123!@#",
                        )

                    assert "used recently" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_reset_password_success(
        self, user_manager, mock_db_session, mock_redis, sample_user
    ):
        """Test successful password reset with token."""
        # Arrange
        reset_token = "valid_reset_token"
        mock_redis.get.return_value = str(sample_user.id)  # Valid token

        mock_result = Mock()
        mock_result.first = Mock(return_value=sample_user)
        mock_db_session.query.return_value.filter.return_value = mock_result

        with patch.object(user_manager, "_validate_password"):
            # Act
            result = await user_manager.reset_password(
                reset_token=reset_token, new_password="NewSecurePass123!@#"
            )

            # Assert
            assert result is True
            mock_redis.delete.assert_called()  # Token invalidated


class TestSecurityFeatures:
    """Test security features like password validation, lockout, MFA."""

    def test_password_validation_policy(self, user_manager):
        """Test password validation against policy."""
        # Arrange
        valid_password = "SecurePass123!@#"
        weak_passwords = [
            "short",  # Too short
            "alllowercase123!@#",  # No uppercase
            "ALLUPPERCASE123!@#",  # No lowercase
            "NoNumbers!@#",  # No numbers
            "NoSpecialChars123",  # No special chars
            "password",  # Common password
        ]

        # Act & Assert - Valid password should not raise
        try:
            user_manager._validate_password(valid_password, "testuser", "test@example.com")
        except ValueError:
            pytest.fail("Valid password should not raise ValueError")

        # Weak passwords should raise
        for weak_pass in weak_passwords:
            with pytest.raises(ValueError):
                user_manager._validate_password(weak_pass, "testuser", "test@example.com")

    @pytest.mark.asyncio
    async def test_account_lockout_after_failed_attempts(
        self, user_manager, mock_db_session, mock_redis, sample_user
    ):
        """Test account lockout after max failed attempts."""
        # Arrange
        sample_user.failed_login_attempts = 5  # At lockout threshold
        mock_result = Mock()
        mock_result.first = Mock(return_value=sample_user)
        mock_db_session.query.return_value.filter.return_value = mock_result

        # Act
        await user_manager._record_failed_attempt(
            identifier="testuser", ip_address="127.0.0.1", user_id=sample_user.id
        )

        # Assert - Redis should set lockout key
        mock_redis.setex.assert_called()
        call_args = mock_redis.setex.call_args
        assert "lockout:testuser" in str(call_args[0])

    @pytest.mark.asyncio
    async def test_password_history_enforcement(self, user_manager, mock_redis):
        """Test password history prevents reuse."""
        # Arrange
        user_id = 1
        old_hashes = [b"$2b$12$old_hash_1", b"$2b$12$old_hash_2", b"$2b$12$old_hash_3"]
        mock_redis.lrange.return_value = old_hashes

        # Mock password verification to match
        with patch.object(user_manager, "_verify_password", return_value=True):
            # Act
            result = await user_manager._is_password_reused(user_id, "reused_password")

            # Assert
            assert result is True

    @pytest.mark.asyncio
    async def test_enable_mfa(self, user_manager, mock_db_session, sample_user):
        """Test MFA enablement for user."""
        # Arrange
        mock_result = Mock()
        mock_result.first = Mock(return_value=sample_user)
        mock_db_session.query.return_value.filter.return_value = mock_result

        sample_user.mfa_secret = None
        sample_user.mfa_enabled = False

        # Act
        mfa_secret = await user_manager.enable_mfa(user_id=sample_user.id)

        # Assert
        assert mfa_secret is not None
        assert isinstance(mfa_secret, str)
        assert len(mfa_secret) > 0
        mock_db_session.commit.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

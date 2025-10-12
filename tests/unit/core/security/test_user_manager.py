"""
Unit Tests for SecureUserManager

Tests user authentication, password management, and security features.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from uuid import uuid4

from apps.backend.core.security.user_manager import (
    SecureUserManager,
    UserRole,
    PasswordPolicy,
    LockoutPolicy,
    AuthenticationError
)


@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    session = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.refresh = Mock()
    session.query = Mock()
    session.delete = Mock()
    return session


@pytest.fixture
def mock_redis_client():
    """Create mock Redis client."""
    redis = MagicMock()
    redis.setex = Mock(return_value=True)
    redis.exists = Mock(return_value=0)
    redis.get = Mock(return_value=None)
    redis.delete = Mock(return_value=1)
    redis.lpush = Mock()
    redis.ltrim = Mock()
    redis.lrange = Mock(return_value=[])
    return redis


@pytest.fixture
def password_policy():
    """Create standard password policy."""
    return PasswordPolicy(
        min_length=12,
        require_uppercase=True,
        require_lowercase=True,
        require_numbers=True,
        require_special=True
    )


@pytest.fixture
def lockout_policy():
    """Create standard lockout policy."""
    return LockoutPolicy(
        max_attempts=5,
        lockout_duration_minutes=15
    )


@pytest.fixture
def user_manager(mock_db_session, mock_redis_client, password_policy, lockout_policy):
    """Create SecureUserManager instance."""
    return SecureUserManager(
        db_session=mock_db_session,
        redis_client=mock_redis_client,
        password_policy=password_policy,
        lockout_policy=lockout_policy
    )


class TestUserCreation:
    """Test user creation functionality."""

    @pytest.mark.asyncio
    async def test_create_user_success(self, user_manager, mock_db_session):
        """Test successful user creation."""
        # Mock user doesn't exist
        mock_db_session.query().filter().first.return_value = None

        user = await user_manager.create_user(
            username="testuser",
            email="test@example.com",
            password="SecurePass123!",
            role=UserRole.STUDENT
        )

        # Verify user was added and committed
        assert mock_db_session.add.called
        assert mock_db_session.commit.called

    @pytest.mark.asyncio
    async def test_create_user_validates_username(self, user_manager):
        """Test username validation."""
        with pytest.raises(ValueError, match="Username must be"):
            await user_manager.create_user(
                username="ab",  # Too short
                email="test@example.com",
                password="SecurePass123!",
                role=UserRole.STUDENT
            )

    @pytest.mark.asyncio
    async def test_create_user_validates_email(self, user_manager):
        """Test email validation."""
        with pytest.raises(ValueError, match="Invalid email"):
            await user_manager.create_user(
                username="testuser",
                email="invalid-email",
                password="SecurePass123!",
                role=UserRole.STUDENT
            )

    @pytest.mark.asyncio
    async def test_create_user_validates_password_length(self, user_manager):
        """Test password length validation."""
        with pytest.raises(ValueError, match="at least"):
            await user_manager.create_user(
                username="testuser",
                email="test@example.com",
                password="Short1!",  # Too short
                role=UserRole.STUDENT
            )

    @pytest.mark.asyncio
    async def test_create_user_prevents_duplicate(self, user_manager, mock_db_session):
        """Test preventing duplicate user creation."""
        # Mock user exists
        mock_user = Mock()
        mock_db_session.query().filter().first.return_value = mock_user

        with pytest.raises(AuthenticationError, match="already exists"):
            await user_manager.create_user(
                username="existing",
                email="existing@example.com",
                password="SecurePass123!",
                role=UserRole.STUDENT
            )

    @pytest.mark.asyncio
    async def test_create_user_hashes_password(self, user_manager, mock_db_session):
        """Test that password is hashed."""
        mock_db_session.query().filter().first.return_value = None

        plain_password = "SecurePass123!"

        # Mock the add method to capture the user object
        captured_user = None
        def capture_user(user):
            nonlocal captured_user
            captured_user = user

        mock_db_session.add = capture_user

        await user_manager.create_user(
            username="testuser",
            email="test@example.com",
            password=plain_password,
            role=UserRole.STUDENT
        )

        # Password should be hashed, not plain
        assert captured_user.password_hash != plain_password
        # Bcrypt hashes start with $2b$
        assert captured_user.password_hash.startswith("$2")


class TestPasswordValidation:
    """Test password policy validation."""

    def test_validate_password_requires_uppercase(self, user_manager):
        """Test uppercase requirement."""
        with pytest.raises(ValueError, match="uppercase"):
            user_manager._validate_password(
                "securepass123!",
                "testuser",
                "test@example.com"
            )

    def test_validate_password_requires_lowercase(self, user_manager):
        """Test lowercase requirement."""
        with pytest.raises(ValueError, match="lowercase"):
            user_manager._validate_password(
                "SECUREPASS123!",
                "testuser",
                "test@example.com"
            )

    def test_validate_password_requires_numbers(self, user_manager):
        """Test numbers requirement."""
        with pytest.raises(ValueError, match="number"):
            user_manager._validate_password(
                "SecurePassword!",
                "testuser",
                "test@example.com"
            )

    def test_validate_password_requires_special(self, user_manager):
        """Test special characters requirement."""
        with pytest.raises(ValueError, match="special"):
            user_manager._validate_password(
                "SecurePass123",
                "testuser",
                "test@example.com"
            )

    def test_validate_password_prevents_common(self, user_manager):
        """Test common password prevention."""
        with pytest.raises(ValueError, match="too common"):
            user_manager._validate_password(
                "Password123!",
                "testuser",
                "test@example.com"
            )

    def test_validate_password_prevents_user_info(self, user_manager):
        """Test prevention of username/email in password."""
        with pytest.raises(ValueError, match="cannot contain username"):
            user_manager._validate_password(
                "Testuser123!",
                "testuser",
                "test@example.com"
            )

    def test_validate_password_success(self, user_manager):
        """Test successful password validation."""
        # Should not raise
        user_manager._validate_password(
            "SecurePass123!",
            "testuser",
            "test@example.com"
        )


class TestAuthentication:
    """Test user authentication."""

    @pytest.mark.asyncio
    async def test_authenticate_success(self, user_manager, mock_db_session):
        """Test successful authentication."""
        # Create mock user
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.is_active = True
        mock_user.failed_login_attempts = 0

        # Hash a test password
        test_password = "SecurePass123!"
        mock_user.password_hash = user_manager._hash_password(test_password)
        mock_user.password_changed_at = datetime.utcnow()

        # Mock DB query
        mock_db_session.query().filter().first.return_value = mock_user

        # Authenticate
        user, session_token = await user_manager.authenticate(
            "testuser",
            test_password,
            ip_address="127.0.0.1"
        )

        assert user == mock_user
        assert isinstance(session_token, str)
        assert len(session_token) > 0

    @pytest.mark.asyncio
    async def test_authenticate_invalid_credentials(self, user_manager, mock_db_session):
        """Test authentication with invalid password."""
        mock_user = Mock()
        mock_user.id = 1
        mock_user.is_active = True
        mock_user.password_hash = user_manager._hash_password("CorrectPass123!")
        mock_user.password_changed_at = datetime.utcnow()

        mock_db_session.query().filter().first.return_value = mock_user

        with pytest.raises(AuthenticationError, match="Invalid credentials"):
            await user_manager.authenticate(
                "testuser",
                "WrongPass123!",
                ip_address="127.0.0.1"
            )

    @pytest.mark.asyncio
    async def test_authenticate_inactive_account(self, user_manager, mock_db_session):
        """Test authentication with inactive account."""
        mock_user = Mock()
        mock_user.is_active = False

        mock_db_session.query().filter().first.return_value = mock_user

        with pytest.raises(AuthenticationError, match="deactivated"):
            await user_manager.authenticate(
                "testuser",
                "SecurePass123!",
                ip_address="127.0.0.1"
            )

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, user_manager, mock_db_session):
        """Test authentication with non-existent user."""
        mock_db_session.query().filter().first.return_value = None

        with pytest.raises(AuthenticationError, match="Invalid credentials"):
            await user_manager.authenticate(
                "nonexistent",
                "SecurePass123!",
                ip_address="127.0.0.1"
            )


class TestAccountLockout:
    """Test account lockout functionality."""

    @pytest.mark.asyncio
    async def test_lockout_after_max_attempts(self, user_manager, mock_redis_client, mock_db_session):
        """Test account locks after max failed attempts."""
        mock_user = Mock()
        mock_user.id = 1
        mock_user.is_active = True
        mock_user.failed_login_attempts = 4  # One below max
        mock_user.password_hash = user_manager._hash_password("CorrectPass123!")
        mock_user.password_changed_at = datetime.utcnow()

        mock_db_session.query().filter().first.return_value = mock_user

        # Fail authentication
        with pytest.raises(AuthenticationError):
            await user_manager.authenticate(
                "testuser",
                "WrongPass123!",
                ip_address="127.0.0.1"
            )

        # Verify lockout was set in Redis
        assert mock_redis_client.setex.called

    @pytest.mark.asyncio
    async def test_locked_account_blocks_authentication(self, user_manager, mock_redis_client):
        """Test locked account prevents authentication."""
        # Mock account is locked
        mock_redis_client.exists.return_value = 1

        with pytest.raises(AuthenticationError, match="temporarily locked"):
            await user_manager.authenticate(
                "testuser",
                "SecurePass123!",
                ip_address="127.0.0.1"
            )


class TestPasswordChange:
    """Test password change functionality."""

    @pytest.mark.asyncio
    async def test_change_password_success(self, user_manager, mock_db_session):
        """Test successful password change."""
        current_password = "CurrentPass123!"
        new_password = "NewSecurePass456!"

        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.password_hash = user_manager._hash_password(current_password)

        mock_db_session.query().filter().first.return_value = mock_user

        result = await user_manager.change_password(
            user_id=1,
            current_password=current_password,
            new_password=new_password
        )

        assert result is True
        assert mock_db_session.commit.called

    @pytest.mark.asyncio
    async def test_change_password_invalid_current(self, user_manager, mock_db_session):
        """Test password change with wrong current password."""
        mock_user = Mock()
        mock_user.id = 1
        mock_user.password_hash = user_manager._hash_password("CurrentPass123!")

        mock_db_session.query().filter().first.return_value = mock_user

        with pytest.raises(AuthenticationError, match="Current password is incorrect"):
            await user_manager.change_password(
                user_id=1,
                current_password="WrongPass123!",
                new_password="NewSecurePass456!"
            )

    @pytest.mark.asyncio
    async def test_change_password_validates_new_password(self, user_manager, mock_db_session):
        """Test new password is validated."""
        current_password = "CurrentPass123!"

        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.password_hash = user_manager._hash_password(current_password)

        mock_db_session.query().filter().first.return_value = mock_user

        with pytest.raises(ValueError, match="at least"):
            await user_manager.change_password(
                user_id=1,
                current_password=current_password,
                new_password="weak"  # Too weak
            )


class TestSessionManagement:
    """Test session creation and management."""

    def test_create_session(self, user_manager, mock_db_session, mock_redis_client):
        """Test session creation."""
        mock_user = Mock()
        mock_user.id = 1

        session_token = user_manager._create_session(
            user=mock_user,
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0"
        )

        assert isinstance(session_token, str)
        assert len(session_token) > 0
        assert mock_db_session.add.called
        assert mock_redis_client.setex.called


class TestPasswordHashing:
    """Test password hashing functions."""

    def test_hash_password_generates_bcrypt(self, user_manager):
        """Test password hashing uses bcrypt."""
        password = "SecurePass123!"
        hashed = user_manager._hash_password(password)

        # Bcrypt hashes start with $2b$ or $2a$
        assert hashed.startswith("$2")
        assert len(hashed) > 50

    def test_hash_password_different_for_same_input(self, user_manager):
        """Test that hashing same password produces different hashes (due to salt)."""
        password = "SecurePass123!"

        hash1 = user_manager._hash_password(password)
        hash2 = user_manager._hash_password(password)

        # Due to salting, hashes should be different
        assert hash1 != hash2

    def test_verify_password_success(self, user_manager):
        """Test password verification success."""
        password = "SecurePass123!"
        hashed = user_manager._hash_password(password)

        result = user_manager._verify_password(password, hashed)
        assert result is True

    def test_verify_password_failure(self, user_manager):
        """Test password verification failure."""
        password = "SecurePass123!"
        hashed = user_manager._hash_password(password)

        result = user_manager._verify_password("WrongPass123!", hashed)
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

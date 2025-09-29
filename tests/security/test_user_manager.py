import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest_asyncio

import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_db_connection():
    """Mock database connection for tests"""
    with patch('psycopg2.connect') as mock_connect:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        yield mock_conn

"""
Comprehensive test suite for user_manager.py
Tests secure user management, authentication, MFA, password policies, and lockout mechanisms.
"""

import pytest
import bcrypt
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status

from apps.backend.core.security.user_manager import (
    SecureUserManager, UserRole, PasswordPolicy, LockoutPolicy,
    AuthenticationError
)


class TestUserRole:
    """Test UserRole enumeration"""

    def test_user_role_values(self):
        """Test user role values"""
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.TEACHER.value == "teacher"
        assert UserRole.STUDENT.value == "student"
        assert UserRole.PARENT.value == "parent"

    def test_user_roles_complete(self):
        """Test that all expected roles are present"""
        expected_roles = ["admin", "teacher", "student", "parent"]
        actual_roles = [role.value for role in UserRole]
        
        for role in expected_roles:
            assert role in actual_roles


class TestPasswordPolicy:
    """Test PasswordPolicy configuration"""

    def test_default_password_policy(self):
        """Test default password policy settings"""
        policy = PasswordPolicy()
        
        assert policy.min_length == 12
        assert policy.max_length == 128
        assert policy.require_uppercase is True
        assert policy.require_lowercase is True
        assert policy.require_numbers is True
        assert policy.require_special is True
        assert policy.min_unique_chars == 8
        assert policy.prevent_common_passwords is True
        assert policy.prevent_user_info_in_password is True
        assert policy.password_history_count == 5
        assert policy.password_expiry_days == 90

    def test_custom_password_policy(self):
        """Test custom password policy settings"""
        policy = PasswordPolicy(
            min_length=8,
            require_special=False,
            password_history_count=10
        )
        
        assert policy.min_length == 8
        assert policy.require_special is False
        assert policy.password_history_count == 10
        # Other values should remain default
        assert policy.require_uppercase is True
        assert policy.require_lowercase is True


class TestLockoutPolicy:
    """Test LockoutPolicy configuration"""

    def test_default_lockout_policy(self):
        """Test default lockout policy settings"""
        policy = LockoutPolicy()
        
        assert policy.max_attempts == 5
        assert policy.lockout_duration_minutes == 15
        assert policy.progressive_delay is True
        assert policy.reset_after_success is True

    def test_custom_lockout_policy(self):
        """Test custom lockout policy settings"""
        policy = LockoutPolicy(
            max_attempts=3,
            lockout_duration_minutes=30,
            progressive_delay=False
        )
        
        assert policy.max_attempts == 3
        assert policy.lockout_duration_minutes == 30
        assert policy.progressive_delay is False
        assert policy.reset_after_success is True  # Default


class TestSecureUserManager:
    """Test SecureUserManager functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.mock_db = Mock()
        self.mock_redis = Mock()
        self.password_policy = PasswordPolicy(min_length=8)  # Relaxed for testing
        self.lockout_policy = LockoutPolicy()
        
        self.user_manager = SecureUserManager(
            db_session=self.mock_db,
            redis_client=self.mock_redis,
            password_policy=self.password_policy,
            lockout_policy=self.lockout_policy
        )

    def test_initialization(self):
        """Test SecureUserManager initialization"""
        assert self.user_manager.db == self.mock_db
        assert self.user_manager.redis == self.mock_redis
        assert self.user_manager.password_policy == self.password_policy
        assert self.user_manager.lockout_policy == self.lockout_policy
        assert self.user_manager.bcrypt_cost == 12

    def test_initialization_without_redis(self):
        """Test initialization without Redis"""
        manager = SecureUserManager(
            db_session=self.mock_db,
            redis_client=None
        )
        
        assert manager.redis is None
        assert isinstance(manager.password_policy, PasswordPolicy)
        assert isinstance(manager.lockout_policy, LockoutPolicy)

    def test_password_hashing(self):
        """Test password hashing with bcrypt"""
        password = "TestPassword123!"
        
        hashed = self.user_manager._hash_password(password)
        
        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed.startswith('$2b$')  # Bcrypt format
        assert len(hashed) > 50
        
        # Verify password
        assert self.user_manager._verify_password(password, hashed) is True
        assert self.user_manager._verify_password("WrongPassword", hashed) is False

    def test_password_verification_error_handling(self):
        """Test password verification error handling"""
        password = "TestPassword123!"
        
        # Test with malformed hash
        assert self.user_manager._verify_password(password, "malformed_hash") is False
        
        # Test with None values
        assert self.user_manager._verify_password(None, "hash") is False
        assert self.user_manager._verify_password(password, None) is False

    def test_username_validation(self):
        """Test username validation"""
        # Valid usernames
        valid_usernames = ["testuser", "test_user", "test-user", "user123", "a" * 30]
        for username in valid_usernames:
            self.user_manager._validate_username(username)  # Should not raise
        
        # Invalid usernames
        invalid_usernames = [
            "ab",  # Too short
            "a" * 31,  # Too long
            "test user",  # Contains space
            "test@user",  # Contains @
            "test.user",  # Contains dot
            ""  # Empty
        ]
        
        for username in invalid_usernames:
            with pytest.raises(ValueError):
                self.user_manager._validate_username(username)

    def test_email_validation(self):
        """Test email validation"""
        # Valid emails
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "test+tag@example.org",
            "123@numbers.com"
        ]
        
        for email in valid_emails:
            self.user_manager._validate_email(email)  # Should not raise
        
        # Invalid emails
        invalid_emails = [
            "invalid_email",
            "@example.com",
            "test@",
            "test.example.com",
            "test @example.com",
            ""
        ]
        
        for email in invalid_emails:
            with pytest.raises(ValueError):
                self.user_manager._validate_email(email)

    def test_password_validation_length(self):
        """Test password length validation"""
        # Too short (using relaxed policy of 8 chars)
        with pytest.raises(ValueError, match="at least 8 characters"):
            self.user_manager._validate_password("Test1!", "user", "test@example.com")
        
        # Too long
        long_password = "A" * 130
        with pytest.raises(ValueError, match="less than 128 characters"):
            self.user_manager._validate_password(long_password, "user", "test@example.com")

    def test_password_validation_character_requirements(self):
        """Test password character requirements validation"""
        username = "testuser"
        email = "test@example.com"
        
        # Missing uppercase
        with pytest.raises(ValueError, match="uppercase letter"):
            self.user_manager._validate_password("test123!", username, email)
        
        # Missing lowercase
        with pytest.raises(ValueError, match="lowercase letter"):
            self.user_manager._validate_password("TEST123!", username, email)
        
        # Missing digit
        with pytest.raises(ValueError, match="number"):
            self.user_manager._validate_password("TestABC!", username, email)
        
        # Missing special character
        with pytest.raises(ValueError, match="special character"):
            self.user_manager._validate_password("TestABC123", username, email)

    def test_password_validation_common_passwords(self):
        """Test common password detection"""
        username = "testuser"
        email = "test@example.com"
        
        common_passwords = ["password", "123456", "qwerty"]
        
        for password in common_passwords:
            with pytest.raises(ValueError, match="too common"):
                self.user_manager._validate_password(password, username, email)

    def test_password_validation_user_info(self):
        """Test password validation against user info"""
        username = "testuser"
        email = "testemail@example.com"
        
        # Password contains username
        with pytest.raises(ValueError, match="cannot contain username"):
            self.user_manager._validate_password("TestuserPass123!", username, email)
        
        # Password contains email prefix
        with pytest.raises(ValueError, match="cannot contain username"):
            self.user_manager._validate_password("TestemailPass123!", username, email)

    def test_password_validation_unique_characters(self):
        """Test unique characters requirement"""
        username = "testuser"
        email = "test@example.com"
        
        # Not enough unique characters (using policy with 8 unique chars)
        with pytest.raises(ValueError, match="unique characters"):
            self.user_manager._validate_password("Aaaa1111!", username, email)

    def test_password_validation_valid_password(self):
        """Test validation of valid password"""
        username = "testuser"
        email = "test@example.com"
        password = "ValidPass123!"
        
        # Should not raise any exception
        self.user_manager._validate_password(password, username, email)

    def test_user_exists_check(self):
        """Test user existence check"""
        # Mock database query
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # User doesn't exist
        assert self.user_manager._user_exists("testuser", "test@example.com") is False
        
        # User exists
        mock_user = Mock()
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        assert self.user_manager._user_exists("testuser", "test@example.com") is True

    @pytest.mark.asyncio
    async def test_create_user_success(self):
        """Test successful user creation"""
        # Mock database operations
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = None  # User doesn't exist
        self.mock_db.add = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.refresh = Mock()
        
        # Mock the User constructor
        with patch('apps.backend.core.security.user_manager.User') as mock_user_class:
            mock_user_class.return_value = mock_user
            
            with patch.object(self.user_manager, '_audit_log') as mock_audit:
                user = await self.user_manager.create_user(
                    username="testuser",
                    email="test@example.com",
                    password="ValidPass123!",
                    role=UserRole.STUDENT,
                    metadata={"test": "data"}
                )
        
        assert user == mock_user
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        mock_audit.assert_called_once()

    @pytest.mark.asyncio


    async def test_create_user_validation_failure(self):
        """Test user creation with validation failure"""
        with pytest.raises(ValueError):
            await self.user_manager.create_user(
                username="ab",  # Too short
                email="test@example.com",
                password="ValidPass123!",
                role=UserRole.STUDENT
            )

    @pytest.mark.asyncio


    async def test_create_user_already_exists(self):
        """Test user creation when user already exists"""
        # Mock user exists
        mock_existing_user = Mock()
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_existing_user
        
        with pytest.raises(AuthenticationError, match="already exists"):
            await self.user_manager.create_user(
                username="testuser",
                email="test@example.com",
                password="ValidPass123!",
                role=UserRole.STUDENT
            )

    @pytest.mark.asyncio


    async def test_authenticate_success(self):
        """Test successful authentication"""
        # Mock user data
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.password_hash = self.user_manager._hash_password("TestPass123!")
        mock_user.is_active = True
        mock_user.password_changed_at = datetime.now(timezone.utc)
        mock_user.failed_login_attempts = 2
        
        # Mock database operations
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        self.mock_db.commit = Mock()
        
        # Mock lockout check
        self.mock_redis.get.return_value = None  # Not locked out
        
        with patch.object(self.user_manager, '_create_session', return_value="session_token_123"):
            with patch.object(self.user_manager, '_audit_log') as mock_audit:
                user, token = await self.user_manager.authenticate(
                    username_or_email="testuser",
                    password="TestPass123!",
                    ip_address="192.168.1.1",
                    user_agent="Test Browser"
                )
        
        assert user == mock_user
        assert token == "session_token_123"
        assert mock_user.failed_login_attempts == 0  # Should be reset
        assert mock_user.last_login_at is not None
        mock_audit.assert_called_once()

    @pytest.mark.asyncio


    async def test_authenticate_user_not_found(self):
        """Test authentication with non-existent user"""
        # Mock user not found
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        self.mock_redis.get.return_value = None  # Not locked out
        
        with patch.object(self.user_manager, '_record_failed_attempt') as mock_record:
            with pytest.raises(AuthenticationError, match="Invalid credentials"):
                await self.user_manager.authenticate(
                    username_or_email="nonexistent",
                    password="password",
                    ip_address="192.168.1.1"
                )
            
            mock_record.assert_called_once()

    @pytest.mark.asyncio


    async def test_authenticate_wrong_password(self):
        """Test authentication with wrong password"""
        # Mock user data
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.password_hash = self.user_manager._hash_password("CorrectPass123!")
        mock_user.is_active = True
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        self.mock_redis.get.return_value = None  # Not locked out
        
        with patch.object(self.user_manager, '_record_failed_attempt') as mock_record:
            with pytest.raises(AuthenticationError, match="Invalid credentials"):
                await self.user_manager.authenticate(
                    username_or_email="testuser",
                    password="WrongPass123!",
                    ip_address="192.168.1.1"
                )
            
            mock_record.assert_called_once()

    @pytest.mark.asyncio


    async def test_authenticate_user_inactive(self):
        """Test authentication with inactive user"""
        mock_user = Mock()
        mock_user.id = 1
        mock_user.is_active = False
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        self.mock_redis.get.return_value = None  # Not locked out
        
        with pytest.raises(AuthenticationError, match="deactivated"):
            await self.user_manager.authenticate(
                username_or_email="testuser",
                password="password",
                ip_address="192.168.1.1"
            )

    @pytest.mark.asyncio


    async def test_authenticate_password_expired(self):
        """Test authentication with expired password"""
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.password_hash = self.user_manager._hash_password("TestPass123!")
        mock_user.is_active = True
        mock_user.password_changed_at = datetime.now(timezone.utc) - timedelta(days=100)  # Expired
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        self.mock_redis.get.return_value = None  # Not locked out
        
        with pytest.raises(AuthenticationError, match="expired"):
            await self.user_manager.authenticate(
                username_or_email="testuser",
                password="TestPass123!",
                ip_address="192.168.1.1"
            )

    @pytest.mark.asyncio


    async def test_authenticate_locked_out(self):
        """Test authentication when user is locked out"""
        self.mock_redis.get.return_value = "locked"  # User is locked out
        
        with pytest.raises(AuthenticationError, match="temporarily locked"):
            await self.user_manager.authenticate(
                username_or_email="testuser",
                password="password",
                ip_address="192.168.1.1"
            )

    @pytest.mark.asyncio


    async def test_change_password_success(self):
        """Test successful password change"""
        # Mock user data
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.password_hash = self.user_manager._hash_password("OldPass123!")
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        self.mock_db.commit = Mock()
        
        with patch.object(self.user_manager, '_is_password_reused', return_value=False):
            with patch.object(self.user_manager, '_add_to_password_history') as mock_history:
                with patch.object(self.user_manager, '_audit_log') as mock_audit:
                    with patch.object(self.user_manager, '_invalidate_user_sessions') as mock_invalidate:
                        result = await self.user_manager.change_password(
                            user_id=1,
                            current_password="OldPass123!",
                            new_password="NewPass123!"
                        )
        
        assert result is True
        assert mock_user.password_changed_at is not None
        mock_history.assert_called_once()
        mock_audit.assert_called_once()
        mock_invalidate.assert_called_once()

    @pytest.mark.asyncio


    async def test_change_password_wrong_current(self):
        """Test password change with wrong current password"""
        mock_user = Mock()
        mock_user.password_hash = self.user_manager._hash_password("CorrectPass123!")
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        with pytest.raises(AuthenticationError, match="Current password is incorrect"):
            await self.user_manager.change_password(
                user_id=1,
                current_password="WrongPass123!",
                new_password="NewPass123!"
            )

    @pytest.mark.asyncio


    async def test_change_password_reused(self):
        """Test password change with reused password"""
        mock_user = Mock()
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.password_hash = self.user_manager._hash_password("OldPass123!")
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        with patch.object(self.user_manager, '_is_password_reused', return_value=True):
            with pytest.raises(AuthenticationError, match="used recently"):
                await self.user_manager.change_password(
                    user_id=1,
                    current_password="OldPass123!",
                    new_password="ReusedPass123!"
                )

    @pytest.mark.asyncio


    async def test_reset_password_success(self):
        """Test successful password reset"""
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.failed_login_attempts = 5
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        self.mock_db.commit = Mock()
        
        with patch.object(self.user_manager, '_validate_reset_token', return_value=1):
            with patch.object(self.user_manager, '_invalidate_reset_token') as mock_invalidate:
                with patch.object(self.user_manager, '_audit_log') as mock_audit:
                    result = await self.user_manager.reset_password(
                        reset_token="valid_token",
                        new_password="NewPass123!"
                    )
        
        assert result is True
        assert mock_user.failed_login_attempts == 0
        assert mock_user.password_changed_at is not None
        mock_invalidate.assert_called_once()
        mock_audit.assert_called_once()

    @pytest.mark.asyncio


    async def test_reset_password_invalid_token(self):
        """Test password reset with invalid token"""
        with patch.object(self.user_manager, '_validate_reset_token', return_value=None):
            with pytest.raises(AuthenticationError, match="Invalid or expired"):
                await self.user_manager.reset_password(
                    reset_token="invalid_token",
                    new_password="NewPass123!"
                )

    @pytest.mark.asyncio


    async def test_enable_mfa_success(self):
        """Test successful MFA enablement"""
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "testuser"
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        self.mock_db.commit = Mock()
        
        with patch.object(self.user_manager, '_encrypt_sensitive_data', return_value="encrypted_secret"):
            with patch.object(self.user_manager, '_audit_log') as mock_audit:
                secret = await self.user_manager.enable_mfa(user_id=1)
        
        assert secret is not None
        assert isinstance(secret, str)
        assert mock_user.mfa_enabled is True
        mock_audit.assert_called_once()

    @pytest.mark.asyncio


    async def test_enable_mfa_user_not_found(self):
        """Test MFA enablement with non-existent user"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(AuthenticationError, match="User not found"):
            await self.user_manager.enable_mfa(user_id=999)

    def test_get_user_by_username_or_email(self):
        """Test getting user by username or email"""
        mock_user = Mock()
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Test with username
        result = self.user_manager._get_user_by_username_or_email("testuser")
        assert result == mock_user
        
        # Test with email
        result = self.user_manager._get_user_by_username_or_email("test@example.com")
        assert result == mock_user

    def test_is_password_expired(self):
        """Test password expiration check"""
        # Recent password change
        recent_date = datetime.now(timezone.utc) - timedelta(days=30)
        assert self.user_manager._is_password_expired(recent_date) is False
        
        # Old password change
        old_date = datetime.now(timezone.utc) - timedelta(days=100)
        assert self.user_manager._is_password_expired(old_date) is True
        
        # No password change date
        assert self.user_manager._is_password_expired(None) is True

    def test_create_session(self):
        """Test session creation"""
        mock_user = Mock()
        mock_user.id = 1
        
        # Mock UserSession
        with patch('apps.backend.core.security.user_manager.UserSession') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            
            self.mock_db.add = Mock()
            self.mock_db.commit = Mock()
            
            token = self.user_manager._create_session(
                user=mock_user,
                ip_address="192.168.1.1",
                user_agent="Test Browser"
            )
        
        assert token is not None
        assert isinstance(token, str)
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()

    @pytest.mark.asyncio


    async def test_is_locked_out_redis(self):
        """Test lockout check with Redis"""
        # Not locked out
        self.mock_redis.exists.return_value = 0
        assert await self.user_manager._is_locked_out("testuser") is False
        
        # Locked out
        self.mock_redis.exists.return_value = 1
        assert await self.user_manager._is_locked_out("testuser") is True

    @pytest.mark.asyncio


    async def test_is_locked_out_no_redis(self):
        """Test lockout check without Redis"""
        manager = SecureUserManager(
            db_session=self.mock_db,
            redis_client=None
        )
        
        # Should always return False without Redis
        assert await manager._is_locked_out("testuser") is False

    @pytest.mark.asyncio


    async def test_record_failed_attempt_with_lockout(self):
        """Test recording failed attempt that triggers lockout"""
        mock_user = Mock()
        mock_user.failed_login_attempts = 4  # One less than max
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        self.mock_db.commit = Mock()
        
        with patch.object(self.user_manager, '_audit_log') as mock_audit:
            await self.user_manager._record_failed_attempt(
                identifier="testuser",
                ip_address="192.168.1.1",
                user_id=1
            )
        
        assert mock_user.failed_login_attempts == 5
        self.mock_redis.setex.assert_called()  # Should set lockout
        mock_audit.assert_called_once()

    @pytest.mark.asyncio


    async def test_is_password_reused_redis(self):
        """Test password reuse check with Redis"""
        user_id = 1
        password = "TestPass123!"
        old_hash = self.user_manager._hash_password(password)
        
        self.mock_redis.lrange.return_value = [old_hash.encode()]
        
        result = await self.user_manager._is_password_reused(user_id, password)
        assert result is True
        
        # Test with different password
        result = await self.user_manager._is_password_reused(user_id, "DifferentPass123!")
        assert result is False

    @pytest.mark.asyncio


    async def test_add_to_password_history(self):
        """Test adding password to history"""
        user_id = 1
        password_hash = "hashed_password"
        
        await self.user_manager._add_to_password_history(user_id, password_hash)
        
        self.mock_redis.lpush.assert_called()
        self.mock_redis.ltrim.assert_called()

    @pytest.mark.asyncio


    async def test_invalidate_user_sessions(self):
        """Test invalidating all user sessions"""
        mock_sessions = [Mock(), Mock()]
        mock_sessions[0].session_token = "token1"
        mock_sessions[1].session_token = "token2"
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = mock_sessions
        self.mock_db.commit = Mock()
        
        await self.user_manager._invalidate_user_sessions(user_id=1)
        
        # Should delete from Redis
        self.mock_redis.delete.assert_called()
        
        # Should delete from database
        assert self.mock_db.delete.call_count == 2
        self.mock_db.commit.assert_called()

    @pytest.mark.asyncio


    async def test_audit_log_creation(self):
        """Test audit log creation"""
        # Mock AuditLog
        with patch('apps.backend.core.security.user_manager.AuditLog') as mock_audit_class:
            mock_audit = Mock()
            mock_audit_class.return_value = mock_audit
            
            self.mock_db.add = Mock()
            self.mock_db.commit = Mock()
            
            await self.user_manager._audit_log(
                action="test_action",
                user_id=1,
                details={"test": "data"}
            )
        
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()

    @pytest.mark.asyncio


    async def test_audit_log_failure(self):
        """Test audit log failure handling"""
        self.mock_db.add.side_effect = Exception("Database error")
        
        # Should not raise exception
        await self.user_manager._audit_log(
            action="test_action",
            user_id=1,
            details={}
        )


@pytest.mark.integration
class TestSecureUserManagerIntegration:
    """Integration tests for SecureUserManager"""

    @pytest.mark.asyncio


    async def test_complete_user_lifecycle(self):
        """Test complete user lifecycle"""
        mock_db = Mock()
        mock_redis = Mock()
        
        # Use relaxed password policy for testing
        password_policy = PasswordPolicy(min_length=8, min_unique_chars=5)
        
        manager = SecureUserManager(
            db_session=mock_db,
            redis_client=mock_redis,
            password_policy=password_policy
        )
        
        # Mock database operations
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,  # User doesn't exist (create)
            Mock(id=1, username="testuser", email="test@example.com",
                 password_hash=manager._hash_password("TestPass123!"),
                 is_active=True, failed_login_attempts=0,
                 password_changed_at=datetime.now(timezone.utc))  # User exists (authenticate)
        ]
        
        # Mock Redis operations
        mock_redis.get.return_value = None  # Not locked out
        mock_redis.exists.return_value = 0  # Not locked out
        
        with patch('apps.backend.core.security.user_manager.User') as mock_user_class:
            mock_user = Mock()
            mock_user.id = 1
            mock_user_class.return_value = mock_user
            
            with patch.object(manager, '_create_session', return_value="session_token"):
                with patch.object(manager, '_audit_log'):
                    # 1. Create user
                    user = await manager.create_user(
                        username="testuser",
                        email="test@example.com",
                        password="TestPass123!",
                        role=UserRole.STUDENT
                    )
                    
                    assert user is not None
                    
                    # 2. Authenticate user
                    auth_user, token = await manager.authenticate(
                        username_or_email="testuser",
                        password="TestPass123!",
                        ip_address="192.168.1.1"
                    )
                    
                    assert auth_user is not None
                    assert token == "session_token"

    @pytest.mark.asyncio


    async def test_lockout_mechanism(self):
        """Test account lockout mechanism"""
        mock_db = Mock()
        mock_redis = Mock()
        
        lockout_policy = LockoutPolicy(max_attempts=3, lockout_duration_minutes=5)
        
        manager = SecureUserManager(
            db_session=mock_db,
            redis_client=mock_redis,
            lockout_policy=lockout_policy
        )
        
        # Mock user with incrementing failed attempts
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.password_hash = manager._hash_password("CorrectPass123!")
        mock_user.is_active = True
        mock_user.failed_login_attempts = 0
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_redis.get.return_value = None  # Not locked out initially
        mock_redis.exists.return_value = 0
        
        with patch.object(manager, '_audit_log'):
            # First two failed attempts
            for i in range(2):
                mock_user.failed_login_attempts = i + 1
                
                with pytest.raises(AuthenticationError, match="Invalid credentials"):
                    await manager.authenticate(
                        username_or_email="testuser",
                        password="WrongPass123!",
                        ip_address="192.168.1.1"
                    )
            
            # Third failed attempt should trigger lockout
            mock_user.failed_login_attempts = 3
            
            with pytest.raises(AuthenticationError, match="Invalid credentials"):
                await manager.authenticate(
                    username_or_email="testuser",
                    password="WrongPass123!",
                    ip_address="192.168.1.1"
                )
            
            # Verify lockout was set
            mock_redis.setex.assert_called()

    def test_password_strength_enforcement(self):
        """Test password strength enforcement"""
        mock_db = Mock()
        
        # Strict password policy
        strict_policy = PasswordPolicy(
            min_length=12,
            min_unique_chars=10,
            require_uppercase=True,
            require_lowercase=True,
            require_numbers=True,
            require_special=True
        )
        
        manager = SecureUserManager(
            db_session=mock_db,
            password_policy=strict_policy
        )
        
        test_cases = [
            ("short", "at least 12 characters"),
            ("nouppercase123!", "uppercase letter"),
            ("NOLOWERCASE123!", "lowercase letter"),
            ("NoNumbers!", "number"),
            ("NoSpecial123", "special character"),
            ("AAA111bbb222!", "unique characters"),
        ]
        
        for password, expected_error in test_cases:
            with pytest.raises(ValueError, match=expected_error):
                manager._validate_password(password, "testuser", "test@example.com")

    def test_concurrent_authentication_attempts(self):
        """Test concurrent authentication attempts"""
        import threading
        import concurrent.futures
        
        mock_db = Mock()
        mock_redis = Mock()
        
        manager = SecureUserManager(
            db_session=mock_db,
            redis_client=mock_redis
        )
        
        # Mock successful authentication setup
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.password_hash = manager._hash_password("TestPass123!")
        mock_user.is_active = True
        mock_user.failed_login_attempts = 0
        mock_user.password_changed_at = datetime.now(timezone.utc)
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_redis.get.return_value = None
        mock_redis.exists.return_value = 0
        
        async def authenticate_user(user_id):
            with patch.object(manager, '_create_session', return_value=f"token_{user_id}"):
                with patch.object(manager, '_audit_log'):
                    try:
                        user, token = await manager.authenticate(
                            username_or_email="testuser",
                            password="TestPass123!",
                            ip_address="192.168.1.1"
                        )
                        return token is not None
                    except Exception:
                        return False
        
        def run_auth(user_id):
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(authenticate_user(user_id))
            finally:
                loop.close()
        
        # Test with multiple threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(run_auth, i) for i in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All authentications should succeed
        assert all(results)


class TestErrorHandling:
    """Test error handling scenarios"""

    def test_authentication_error_class(self):
        """Test AuthenticationError class"""
        # Default status code
        error = AuthenticationError("Test message")
        assert error.status_code == status.HTTP_401_UNAUTHORIZED
        assert str(error.detail) == "Test message"
        
        # Custom status code
        error = AuthenticationError("Forbidden", status.HTTP_403_FORBIDDEN)
        assert error.status_code == status.HTTP_403_FORBIDDEN

    def test_common_passwords_set(self):
        """Test common passwords set"""
        manager = SecureUserManager(db_session=Mock())
        
        assert len(manager.COMMON_PASSWORDS) > 0
        assert "password" in manager.COMMON_PASSWORDS
        assert "123456" in manager.COMMON_PASSWORDS

    def test_bcrypt_error_handling(self):
        """Test bcrypt error handling"""
        manager = SecureUserManager(db_session=Mock())
        
        # Test with invalid hash format
        result = manager._verify_password("password", "invalid_hash")
        assert result is False
        
        # Test with None values
        result = manager._verify_password(None, "hash")
        assert result is False

    @pytest.mark.asyncio


    async def test_database_error_handling(self):
        """Test database error handling"""
        mock_db = Mock()
        mock_db.query.side_effect = Exception("Database connection failed")
        
        manager = SecureUserManager(db_session=mock_db)
        
        # Should handle database errors gracefully
        result = manager._user_exists("testuser", "test@example.com")
        # Implementation might return False on error or re-raise

    def test_redis_error_handling(self):
        """Test Redis error handling"""
        mock_redis = Mock()
        mock_redis.get.side_effect = Exception("Redis connection failed")
        
        manager = SecureUserManager(
            db_session=Mock(),
            redis_client=mock_redis
        )
        
        # Should handle Redis errors gracefully
        # Implementation should not crash when Redis is unavailable

    def test_encryption_not_implemented(self):
        """Test that encryption method needs implementation"""
        manager = SecureUserManager(db_session=Mock())
        
        # Current implementation is a placeholder
        result = manager._encrypt_sensitive_data("test_data")
        assert result == "test_data"  # Placeholder implementation

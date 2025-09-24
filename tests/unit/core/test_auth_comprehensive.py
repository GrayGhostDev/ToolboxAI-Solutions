import pytest_asyncio
"""
Comprehensive Authentication Module Test Suite
Tests all authentication functions with high coverage
"""
import sys
from pathlib import Path
import pytest
import jwt
import json
import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Set test secret key
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only-32-chars-minimum-length"
os.environ["TESTING"] = "true"

from apps.backend.api.auth.auth import (
    JWTManager,
    SessionManager,
    RateLimiter,
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    get_current_user,
    require_role,
    create_user_token,
    verify_token,
    hash_password,
    verify_password,
    _safe_redis_int
)
from apps.backend.models.schemas import User, Session
from apps.backend.core.config import settings


class TestJWTManager:
    """Test JWT token management"""

    def test_create_access_token_basic(self):
        """Test basic token creation"""
        user_data = {"sub": "user123", "role": "teacher"}
        token = JWTManager.create_access_token(user_data)

        assert isinstance(token, str)
        assert len(token) > 50

        # Decode and verify
        payload = JWTManager.verify_token(token)
        assert payload["sub"] == "user123"
        assert payload["role"] == "teacher"
        assert "exp" in payload
        assert "iat" in payload

    def test_create_access_token_with_expiry(self):
        """Test token creation with custom expiry"""
        user_data = {"sub": "user123", "role": "student"}
        expires_delta = timedelta(minutes=30)
        token = JWTManager.create_access_token(user_data, expires_delta)

        payload = JWTManager.verify_token(token)
        assert payload["sub"] == "user123"

        # Check expiry is approximately 30 minutes from now
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        time_diff = (exp_time - now).total_seconds()
        assert 1700 < time_diff < 1900  # 30 minutes ± 1 minute tolerance

    def test_verify_token_valid(self):
        """Test valid token verification"""
        user_data = {"sub": "user123", "role": "admin"}
        token = JWTManager.create_access_token(user_data)

        payload = JWTManager.verify_token(token)
        assert payload["sub"] == "user123"
        assert payload["role"] == "admin"

    def test_verify_token_invalid(self):
        """Test invalid token verification"""
        invalid_token = "invalid.token.here"

        with pytest.raises(AuthenticationError, match="Invalid token"):
            JWTManager.verify_token(invalid_token)

    def test_verify_token_expired(self):
        """Test expired token verification"""
        user_data = {"sub": "user123", "role": "teacher"}
        # Create token with 1 second expiry
        token = JWTManager.create_access_token(user_data, timedelta(seconds=1))

        # Wait for expiry
        import time
        time.sleep(2)

        with pytest.raises(AuthenticationError, match="Token has expired"):
            JWTManager.verify_token(token)

    def test_verify_token_no_raise_on_error(self):
        """Test token verification without raising errors"""
        invalid_token = "invalid.token.here"

        result = JWTManager.verify_token(invalid_token, raise_on_error=False)
        assert result is None

    def test_verify_token_expired_no_raise_on_error(self):
        """Test expired token verification without raising errors"""
        user_data = {"sub": "user123", "role": "teacher"}
        token = JWTManager.create_access_token(user_data, timedelta(seconds=1))

        import time
        time.sleep(2)

        result = JWTManager.verify_token(token, raise_on_error=False)
        assert result is None


class TestSessionManager:
    """Test session management"""

    @patch('apps.backend.api.auth.auth.redis_client')
    def test_create_session_with_redis(self, mock_redis):
        """Test session creation with Redis"""
        mock_redis.setex.return_value = True

        session = SessionManager.create_session("user123", "roblox456", "studio789")

        assert isinstance(session, Session)
        assert session.user_id == "user123"
        assert session.roblox_user_id == "roblox456"
        assert session.studio_id == "studio789"
        assert session.id is not None

        # Verify Redis was called
        mock_redis.setex.assert_called_once()

    @patch('apps.backend.api.auth.auth.redis_client', None)
    def test_create_session_without_redis(self):
        """Test session creation without Redis (memory store)"""
        session = SessionManager.create_session("user123")

        assert isinstance(session, Session)
        assert session.user_id == "user123"
        assert session.roblox_user_id is None
        assert session.studio_id is None
        assert session.id is not None

    @patch('apps.backend.api.auth.auth.redis_client')
    def test_get_session_with_redis(self, mock_redis):
        """Test getting session with Redis"""
        session_data = {
            "id": "session123",
            "user_id": "user123",
            "roblox_user_id": "roblox456",
            "studio_id": "studio789",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        }
        mock_redis.get.return_value = json.dumps(session_data)

        session = SessionManager.get_session("session123")

        assert session is not None
        assert session.id == "session123"
        assert session.user_id == "user123"
        assert session.roblox_user_id == "roblox456"
        assert session.studio_id == "studio789"

    @patch('apps.backend.api.auth.auth.redis_client', None)
    def test_get_session_without_redis(self):
        """Test getting session without Redis"""
        # First create a session to store in memory
        session = SessionManager.create_session("user123")
        session_id = session.id

        # Now retrieve it
        retrieved_session = SessionManager.get_session(session_id)

        assert retrieved_session is not None
        assert retrieved_session.id == session_id
        assert retrieved_session.user_id == "user123"

    @patch('apps.backend.api.auth.auth.redis_client')
    def test_get_session_not_found(self, mock_redis):
        """Test getting non-existent session"""
        mock_redis.get.return_value = None

        session = SessionManager.get_session("nonexistent")
        assert session is None

    @patch('apps.backend.api.auth.auth.redis_client')
    def test_invalidate_session_with_redis(self, mock_redis):
        """Test session invalidation with Redis"""
        mock_redis.delete.return_value = 1

        result = SessionManager.invalidate_session("session123")
        assert result is True
        mock_redis.delete.assert_called_once_with("session:session123")

    @patch('apps.backend.api.auth.auth.redis_client', None)
    def test_invalidate_session_without_redis(self):
        """Test session invalidation without Redis"""
        # Create a session first
        session = SessionManager.create_session("user123")
        session_id = session.id

        # Invalidate it
        result = SessionManager.invalidate_session(session_id)
        assert result is True

        # Verify it's gone
        retrieved_session = SessionManager.get_session(session_id)
        assert retrieved_session is None


class TestRateLimiter:
    """Test rate limiting functionality"""

    @patch('apps.backend.api.auth.auth.get_rate_limit_manager')
    def test_check_rate_limit_allowed(self, mock_get_manager):
        """Test rate limit check when allowed"""
        mock_manager = AsyncMock()
        mock_manager.check_rate_limit.return_value = (True, 5)
        mock_get_manager.return_value = mock_manager

        result = RateLimiter.check_rate_limit("test_identifier")
        assert result is True

    @patch('apps.backend.api.auth.auth.get_rate_limit_manager')
    def test_check_rate_limit_exceeded(self, mock_get_manager):
        """Test rate limit check when exceeded"""
        mock_manager = AsyncMock()
        mock_manager.check_rate_limit.return_value = (False, 100)
        mock_get_manager.return_value = mock_manager

        result = RateLimiter.check_rate_limit("test_identifier")
        assert result is False

    @patch('apps.backend.api.auth.auth.get_rate_limit_manager')
    def test_check_rate_limit_with_custom_params(self, mock_get_manager):
        """Test rate limit check with custom parameters"""
        mock_manager = AsyncMock()
        mock_manager.check_rate_limit.return_value = (True, 10)
        mock_get_manager.return_value = mock_manager

        result = RateLimiter.check_rate_limit(
            "test_identifier",
            window_seconds=120,
            max_requests=50
        )
        assert result is True

        # Verify the manager was called with correct parameters
        mock_manager.check_rate_limit.assert_called_once_with(
            identifier="test_identifier",
            max_requests=50,
            window_seconds=120,
            source="auth"
        )

    @patch('apps.backend.api.auth.auth.get_rate_limit_manager')
    def test_rate_limit_decorator(self, mock_get_manager):
        """Test rate limit decorator"""
        mock_manager = AsyncMock()
        mock_manager.check_rate_limit.return_value = (True, 5)
        mock_get_manager.return_value = mock_manager

        @RateLimiter.rate_limit_decorator(max_requests=10, window_seconds=60)
        @pytest.mark.asyncio
async def test_endpoint(request):
            return {"status": "success"}

        # Mock request
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"

        # Test the decorated function
        result = asyncio.run(test_endpoint(mock_request))
        assert result == {"status": "success"}

    @patch('apps.backend.api.auth.auth.get_rate_limit_manager')
    def test_rate_limit_decorator_exceeded(self, mock_get_manager):
        """Test rate limit decorator when limit exceeded"""
        mock_manager = AsyncMock()
        mock_manager.check_rate_limit.return_value = (False, 100)
        mock_get_manager.return_value = mock_manager

        @RateLimiter.rate_limit_decorator(max_requests=10, window_seconds=60)
        @pytest.mark.asyncio
async def test_endpoint(request):
            return {"status": "success"}

        # Mock request
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"

        # Test the decorated function should raise RateLimitError
        with pytest.raises(RateLimitError, match="Rate limit exceeded for test_endpoint"):
            asyncio.run(test_endpoint(mock_request))


class TestAuthenticationErrors:
    """Test custom authentication errors"""

    def test_authentication_error(self):
        """Test AuthenticationError"""
        error = AuthenticationError("Custom auth error")

        assert error.status_code == 401
        assert error.detail == "Custom auth error"
        assert "WWW-Authenticate" in error.headers
        assert error.headers["WWW-Authenticate"] == "Bearer"

    def test_authorization_error(self):
        """Test AuthorizationError"""
        error = AuthorizationError("Custom authz error")

        assert error.status_code == 403
        assert error.detail == "Custom authz error"

    def test_rate_limit_error(self):
        """Test RateLimitError"""
        error = RateLimitError("Custom rate limit error")

        assert error.status_code == 429
        assert error.detail == "Custom rate limit error"
        assert "Retry-After" in error.headers
        assert error.headers["Retry-After"] == "60"


class TestUserAuthentication:
    """Test user authentication functions"""

    @patch('apps.backend.api.auth.auth.JWTManager.verify_token')
    def test_get_current_user_with_valid_token(self, mock_verify):
        """Test get_current_user with valid token"""
        mock_verify.return_value = {
            "sub": "user123",
            "username": "testuser",
            "email": "test@example.com",
            "role": "teacher"
        }

        # Mock credentials
        mock_credentials = Mock()
        mock_credentials.credentials = "valid.token.here"

        user = asyncio.run(get_current_user(mock_credentials))

        assert isinstance(user, User)
        assert user.id == "user123"
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == "teacher"

    def test_get_current_user_no_credentials(self):
        """Test get_current_user with no credentials"""
        with pytest.raises(AuthenticationError, match="Authorization header missing"):
            asyncio.run(get_current_user(None))

    @patch('apps.backend.api.auth.auth.JWTManager.verify_token')
    def test_get_current_user_invalid_token(self, mock_verify):
        """Test get_current_user with invalid token"""
        mock_verify.side_effect = AuthenticationError("Invalid token")

        mock_credentials = Mock()
        mock_credentials.credentials = "invalid.token.here"

        with pytest.raises(AuthenticationError, match="Invalid token"):
            asyncio.run(get_current_user(mock_credentials))

    @patch('apps.backend.api.auth.auth.JWTManager.verify_token')
    def test_get_current_user_missing_user_id(self, mock_verify):
        """Test get_current_user with missing user ID in token"""
        mock_verify.return_value = {
            "username": "testuser",
            "email": "test@example.com",
            "role": "teacher"
            # Missing "sub" field
        }

        mock_credentials = Mock()
        mock_credentials.credentials = "token.without.sub"

        with pytest.raises(AuthenticationError, match="Invalid token payload"):
            asyncio.run(get_current_user(mock_credentials))

    def test_require_role_admin_success(self):
        """Test require_role with admin role success"""
        # Import here to avoid import issues
        sys.path.append(str(Path(__file__).parent.parent.parent))
        from tests.utils.fastapi_test_utils import create_mock_user, MockRoleChecker

        mock_user = create_mock_user(role="admin")
        role_checker = MockRoleChecker("admin")

        # Should not raise exception for admin user
        result = role_checker(mock_user)
        assert result is None

    def test_require_role_admin_failure(self):
        """Test require_role with admin role failure"""
        # Import here to avoid import issues
        sys.path.append(str(Path(__file__).parent.parent.parent))
        from tests.utils.fastapi_test_utils import create_mock_user, MockRoleChecker

        mock_user = create_mock_user(role="student")
        role_checker = MockRoleChecker("admin")

        # Should raise HTTPException for non-admin user
        with pytest.raises(Exception) as exc_info:
            role_checker(mock_user)

        # Check that it's the right type of exception (HTTPException with 403)
        assert "403" in str(exc_info.value) or "Insufficient permissions" in str(exc_info.value)

    def test_require_role_teacher_success(self):
        """Test require_role with teacher role success"""
        # Import here to avoid import issues
        sys.path.append(str(Path(__file__).parent.parent.parent))
        from tests.utils.fastapi_test_utils import create_mock_user, MockRoleChecker

        mock_user = create_mock_user(role="teacher")
        role_checker = MockRoleChecker("teacher")

        # Should not raise exception for teacher user
        result = role_checker(mock_user)
        assert result is None


class TestPasswordHashing:
    """Test password hashing functions"""

    def test_hash_password(self):
        """Test password hashing"""
        password = "SecurePass123!"
        hashed = hash_password(password)

        assert hashed != password
        assert isinstance(hashed, str)
        assert len(hashed) > 20

    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "SecurePass123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "SecurePass123!"
        wrong_password = "WrongPass456!"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_hash_password_weak_password(self):
        """Test hashing weak password (should still work, validation is elsewhere)"""
        weak_password = "123"
        hashed = hash_password(weak_password)

        assert hashed != weak_password
        assert verify_password(weak_password, hashed) is True


class TestUtilityFunctions:
    """Test utility functions"""

    def test_safe_redis_int_with_int(self):
        """Test _safe_redis_int with integer input"""
        result = _safe_redis_int(42)
        assert result == 42

    def test_safe_redis_int_with_string(self):
        """Test _safe_redis_int with string input"""
        result = _safe_redis_int("42")
        assert result == 42

    def test_safe_redis_int_with_bytes(self):
        """Test _safe_redis_int with bytes input"""
        result = _safe_redis_int(b"42")
        assert result == 42

    def test_safe_redis_int_with_invalid(self):
        """Test _safe_redis_int with invalid input"""
        result = _safe_redis_int("invalid")
        assert result == 1  # default value

    def test_safe_redis_int_with_none(self):
        """Test _safe_redis_int with None input"""
        result = _safe_redis_int(None)
        assert result == 1  # default value

    def test_safe_redis_int_with_custom_default(self):
        """Test _safe_redis_int with custom default"""
        result = _safe_redis_int("invalid", default=5)
        assert result == 5


class TestTokenCreation:
    """Test token creation functions"""

    def test_create_user_token(self):
        """Test create_user_token function"""
        user = User(
            id="user123",
            username="testuser",
            email="test@example.com",
            role="teacher"
        )

        token = create_user_token(user)

        assert isinstance(token, str)
        assert len(token) > 50

        # Verify the token
        payload = verify_token(token)
        assert payload["sub"] == "user123"
        assert payload["username"] == "testuser"
        assert payload["email"] == "test@example.com"
        assert payload["role"] == "teacher"

    def test_verify_user_token_valid(self):
        """Test verify_token with valid token"""
        user = User(
            id="user123",
            username="testuser",
            email="test@example.com",
            role="student"
        )

        token = create_user_token(user)
        payload = verify_token(token)

        assert payload["sub"] == "user123"
        assert payload["username"] == "testuser"
        assert payload["email"] == "test@example.com"
        assert payload["role"] == "student"

    def test_verify_user_token_invalid(self):
        """Test verify_token with invalid token"""
        invalid_token = "invalid.token.here"

        with pytest.raises(AuthenticationError):
            verify_token(invalid_token)


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])

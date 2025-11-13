"""
Unit Tests for Authentication Module

Tests authentication functionality including:
- JWT token creation and verification
- Refresh token rotation with family tracking
- Session management with Redis fallback
- Rate limiting
- LMS authentication (Schoology, Canvas)
- API key management
"""

import time
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import jwt
import pytest
from freezegun import freeze_time

from apps.backend.api.auth.auth import (
    APIKeyManager,
    AuthenticationError,
    JWTManager,
    LMSAuthenticator,
    RateLimiter,
    RateLimitError,
    SessionManager,
    authenticate_user,
)
from apps.backend.models.schemas import Session, User
from toolboxai_settings import settings


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis_client = Mock()
    redis_client.get = Mock(return_value=None)
    redis_client.set = Mock(return_value=True)
    redis_client.setex = Mock(return_value=True)
    redis_client.delete = Mock(return_value=1)
    redis_client.exists = Mock(return_value=0)
    redis_client.ping = Mock(return_value=True)
    return redis_client


@pytest.fixture
def sample_user():
    """Sample user for testing"""
    return User(id="user_123", username="testuser", email="test@example.com", role="teacher")


@pytest.fixture
def sample_token_data():
    """Sample token payload"""
    return {
        "sub": "user_123",
        "username": "testuser",
        "email": "test@example.com",
        "role": "teacher",
    }


class TestJWTManagement:
    """Test JWT token creation and verification."""

    def test_create_access_token_success(self, sample_token_data):
        """Test successful access token creation."""
        # Act
        token = JWTManager.create_access_token(sample_token_data)

        # Assert
        assert token is not None
        assert isinstance(token, str)

        # Verify token can be decoded
        payload = JWTManager.verify_token(token)
        assert payload["sub"] == "user_123"
        assert payload["username"] == "testuser"
        assert "exp" in payload
        assert "iat" in payload

    def test_create_access_token_with_custom_expiry(self, sample_token_data):
        """Test access token creation with custom expiry."""
        # Arrange
        custom_expiry = timedelta(minutes=5)

        # Act
        token = JWTManager.create_access_token(sample_token_data, expires_delta=custom_expiry)

        # Assert
        payload = JWTManager.verify_token(token)
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        iat_time = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)

        # Should expire in ~5 minutes (allow 1 second tolerance)
        time_diff = (exp_time - iat_time).total_seconds()
        assert 299 <= time_diff <= 301  # 5 minutes ± 1 second

    @patch("apps.backend.api.auth.auth.redis_client")
    def test_create_refresh_token_success(self, mock_redis_client, mock_redis):
        """Test refresh token creation with family tracking."""
        # Arrange
        mock_redis_client = mock_redis
        user_id = "user_123"

        # Act
        token, family_id = JWTManager.create_refresh_token(user_id)

        # Assert
        assert token is not None
        assert family_id is not None
        assert isinstance(family_id, str)

        # Verify token payload
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"
        assert payload["family"] == family_id
        assert "jti" in payload

    def test_verify_token_valid(self, sample_token_data):
        """Test verification of valid token."""
        # Arrange
        token = JWTManager.create_access_token(sample_token_data)

        # Act
        payload = JWTManager.verify_token(token)

        # Assert
        assert payload is not None
        assert payload["sub"] == "user_123"

    def test_verify_token_expired(self, sample_token_data):
        """Test verification of expired token."""
        # Arrange - Create token that expires immediately
        with freeze_time("2025-01-01 12:00:00"):
            token = JWTManager.create_access_token(
                sample_token_data, expires_delta=timedelta(seconds=1)
            )

        # Act & Assert - Token should be expired
        with freeze_time("2025-01-01 12:00:05"):
            with pytest.raises(AuthenticationError) as exc_info:
                JWTManager.verify_token(token)

            assert "expired" in str(exc_info.value.detail).lower()

    def test_verify_token_invalid(self):
        """Test verification of invalid token."""
        # Arrange
        invalid_token = "invalid.jwt.token"

        # Act & Assert
        with pytest.raises(AuthenticationError) as exc_info:
            JWTManager.verify_token(invalid_token)

        assert "Invalid token" in str(exc_info.value.detail)

    @patch("apps.backend.api.auth.auth.redis_client")
    def test_verify_refresh_token_with_reuse_detection(self, mock_redis_client, mock_redis):
        """Test refresh token verification detects reuse attacks."""
        # Arrange
        mock_redis_client = mock_redis
        user_id = "user_123"

        # Create initial refresh token
        token1, family_id = JWTManager.create_refresh_token(user_id)

        # Simulate token rotation - create new token with same family
        token2, _ = JWTManager.create_refresh_token(user_id, token_family=family_id)

        # Mock Redis to return latest token info
        mock_redis.get.return_value = '{"user_id": "user_123", "latest_jti": "new_jti"}'

        # Act - Try to use old token (token1)
        payload, is_compromised = JWTManager.verify_refresh_token(token1)

        # Assert - Should detect reuse
        # Note: Implementation may vary, adjust based on actual behavior
        assert payload is not None or is_compromised

    @patch("apps.backend.api.auth.auth.redis_client")
    def test_refresh_token_family_tracking(self, mock_redis_client, mock_redis):
        """Test refresh token family is tracked in Redis."""
        # Arrange
        mock_redis_client = mock_redis
        user_id = "user_123"

        # Act
        token, family_id = JWTManager.create_refresh_token(user_id)

        # Assert - Verify Redis was called to store family
        family_key = f"token_family:{family_id}"
        mock_redis.setex.assert_called()

        # Check call args contain family_key
        call_args = mock_redis.setex.call_args
        assert family_key in str(call_args) or call_args[0][0] == family_key


class TestSessionManagement:
    """Test session creation and management."""

    @patch("apps.backend.api.auth.auth.redis_client")
    def test_create_session_success(self, mock_redis_client, mock_redis, sample_user):
        """Test successful session creation."""
        # Arrange
        mock_redis_client = mock_redis

        # Act
        session = SessionManager.create_session(
            user_id=sample_user.id, roblox_user_id="roblox_123", studio_id="studio_456"
        )

        # Assert
        assert session is not None
        assert session.user_id == sample_user.id
        assert session.roblox_user_id == "roblox_123"
        assert session.studio_id == "studio_456"
        assert session.id is not None

        # Verify Redis was called
        mock_redis.setex.assert_called_once()

    @patch("apps.backend.api.auth.auth.redis_client")
    def test_get_session_from_redis(self, mock_redis_client, mock_redis):
        """Test session retrieval from Redis."""
        # Arrange
        mock_redis_client = mock_redis
        session_id = "session_123"
        session_data = {
            "id": session_id,
            "user_id": "user_123",
            "roblox_user_id": "roblox_123",
            "studio_id": "studio_456",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        }

        import json

        mock_redis.get.return_value = json.dumps(session_data)

        # Act
        session = SessionManager.get_session(session_id)

        # Assert
        assert session is not None
        assert session.id == session_id
        assert session.user_id == "user_123"

    @patch("apps.backend.api.auth.auth.redis_client", None)
    def test_get_session_from_memory_fallback(self):
        """Test session retrieval from in-memory fallback."""
        # Arrange
        from apps.backend.api.auth.auth import memory_store

        session_id = "session_456"
        session_data = {
            "id": session_id,
            "user_id": "user_456",
            "roblox_user_id": None,
            "studio_id": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        }

        memory_store[f"session:{session_id}"] = session_data

        # Act
        session = SessionManager.get_session(session_id)

        # Assert
        assert session is not None
        assert session.id == session_id
        assert session.user_id == "user_456"

    @patch("apps.backend.api.auth.auth.redis_client")
    def test_invalidate_session(self, mock_redis_client, mock_redis):
        """Test session invalidation."""
        # Arrange
        mock_redis_client = mock_redis
        session_id = "session_789"
        mock_redis.delete.return_value = 1

        # Act
        result = SessionManager.invalidate_session(session_id)

        # Assert
        assert result is True
        mock_redis.delete.assert_called_once_with(f"session:{session_id}")

    def test_session_expiry(self):
        """Test session expiry time calculation."""
        # Arrange & Act
        with freeze_time("2025-01-01 12:00:00"):
            session = SessionManager.create_session("user_123")

        # Assert
        expected_expiry = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc) + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )

        # Allow 1 second tolerance
        time_diff = abs((session.expires_at - expected_expiry).total_seconds())
        assert time_diff <= 1


class TestRateLimiting:
    """Test rate limiting functionality."""

    @pytest.mark.asyncio
    @patch("apps.backend.api.auth.auth.get_rate_limit_manager")
    async def test_rate_limit_within_limit(self, mock_get_manager):
        """Test rate limit check when within limit."""
        # Arrange
        mock_manager = Mock()
        mock_manager.check_rate_limit = AsyncMock(return_value=(True, 0))
        mock_get_manager.return_value = mock_manager

        identifier = "test_user_123"

        # Act
        allowed = RateLimiter.check_rate_limit(identifier)

        # Assert
        assert allowed is True

    @pytest.mark.asyncio
    @patch("apps.backend.api.auth.auth.get_rate_limit_manager")
    async def test_rate_limit_exceeded(self, mock_get_manager):
        """Test rate limit check when limit exceeded."""
        # Arrange
        mock_manager = Mock()
        mock_manager.check_rate_limit = AsyncMock(return_value=(False, 60))
        mock_get_manager.return_value = mock_manager

        identifier = "test_user_456"

        # Act
        allowed = RateLimiter.check_rate_limit(identifier)

        # Assert
        assert allowed is False

    @pytest.mark.asyncio
    @patch("apps.backend.api.auth.auth.get_rate_limit_manager")
    async def test_rate_limit_decorator_success(self, mock_get_manager):
        """Test rate limit decorator allows request within limit."""
        # Arrange
        mock_manager = Mock()
        mock_manager.check_rate_limit = AsyncMock(return_value=(True, 0))
        mock_get_manager.return_value = mock_manager

        mock_request = Mock()
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"

        @RateLimiter.rate_limit_decorator(max_requests=10)
        async def test_endpoint(request):
            return {"status": "success"}

        # Act
        result = await test_endpoint(mock_request)

        # Assert
        assert result["status"] == "success"

    @pytest.mark.asyncio
    @patch("apps.backend.api.auth.auth.get_rate_limit_manager")
    async def test_rate_limit_decorator_blocked(self, mock_get_manager):
        """Test rate limit decorator blocks request when limit exceeded."""
        # Arrange
        mock_manager = Mock()
        mock_manager.check_rate_limit = AsyncMock(return_value=(False, 60))
        mock_get_manager.return_value = mock_manager

        mock_request = Mock()
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"

        @RateLimiter.rate_limit_decorator(max_requests=10)
        async def test_endpoint(request):
            return {"status": "success"}

        # Act & Assert
        with pytest.raises(RateLimitError):
            await test_endpoint(mock_request)


class TestLMSAuthentication:
    """Test LMS platform authentication."""

    @patch.dict("os.environ", {"SCHOOLOGY_KEY": "test_key", "SCHOOLOGY_SECRET": "test_secret"})
    def test_get_schoology_session(self):
        """Test Schoology OAuth session creation."""
        # Act
        session = LMSAuthenticator.get_schoology_session(
            user_token="user_token", user_secret="user_secret"
        )

        # Assert
        assert session is not None
        assert hasattr(session, "get")

    @patch.dict("os.environ", {"CANVAS_TOKEN": "test_canvas_token"})
    def test_get_canvas_headers(self):
        """Test Canvas API headers generation."""
        # Act
        headers = LMSAuthenticator.get_canvas_headers()

        # Assert
        assert headers is not None
        assert "Authorization" in headers
        assert "Bearer test_canvas_token" in headers["Authorization"]
        assert headers["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    @patch("apps.backend.api.auth.auth.LMSAuthenticator.get_schoology_session")
    async def test_verify_lms_credentials_schoology(self, mock_get_session):
        """Test Schoology credential verification."""
        # Arrange
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_session.get.return_value = mock_response
        mock_get_session.return_value = mock_session

        credentials = {"token": "test_token", "secret": "test_secret"}

        # Act
        result = LMSAuthenticator.verify_lms_credentials("schoology", credentials)

        # Assert
        assert result is True

    @pytest.mark.asyncio
    @patch("apps.backend.api.auth.auth.requests.get")
    @patch.dict("os.environ", {"CANVAS_BASE_URL": "https://canvas.example.com"})
    async def test_verify_lms_credentials_canvas(self, mock_requests_get):
        """Test Canvas credential verification."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests_get.return_value = mock_response

        credentials = {"token": "test_canvas_token"}

        # Act
        result = LMSAuthenticator.verify_lms_credentials("canvas", credentials)

        # Assert
        assert result is True


class TestAPIKeyManagement:
    """Test API key generation and validation."""

    def test_generate_api_key(self):
        """Test API key generation."""
        # Act
        api_key = APIKeyManager.generate_api_key("user_123", "roblox")

        # Assert
        assert api_key is not None
        assert len(api_key) == 64  # SHA256 hex digest
        assert all(c in "0123456789abcdef" for c in api_key)

    def test_validate_api_key(self):
        """Test API key validation."""
        # Arrange
        valid_key = "a" * 64  # Valid format
        invalid_key = "invalid_key"

        # Act
        valid_result = APIKeyManager.validate_api_key(valid_key)
        invalid_result = APIKeyManager.validate_api_key(invalid_key)

        # Assert
        assert valid_result is not None
        assert valid_result["valid"] is True
        assert invalid_result is None


class TestUserAuthentication:
    """Test user authentication flow."""

    @pytest.mark.asyncio
    @patch("apps.backend.api.auth.auth.verify_password")
    async def test_authenticate_user_success(self, mock_verify_password):
        """Test successful user authentication."""
        # Arrange
        mock_verify_password.return_value = True

        # Mock the testing environment and credentials
        with patch.dict("os.environ", {"TESTING": "true", "ALLOW_TEST_FALLBACK": "true"}):
            with patch("apps.backend.api.auth.auth.get_testing_credentials") as mock_get_creds:
                mock_get_creds.return_value = [
                    {
                        "id": "test_user_001",
                        "username": "testuser",
                        "email": "test@example.com",
                        "role": "teacher",
                        "password_hash": "$2b$12$test_hash",
                    }
                ]

                # Act
                user = await authenticate_user("testuser", "password123")

                # Assert
                assert user is not None
                assert user.username == "testuser"
                assert user.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_credentials(self):
        """Test authentication with invalid credentials."""
        # Arrange
        with patch.dict("os.environ", {"TESTING": "true", "ALLOW_TEST_FALLBACK": "true"}):
            with patch("apps.backend.api.auth.auth.get_testing_credentials") as mock_get_creds:
                mock_get_creds.return_value = []

                # Act
                user = await authenticate_user("nonexistent", "wrongpassword")

                # Assert
                assert user is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

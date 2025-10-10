"""
Unit tests for the Roblox Integration API Router.

Tests cover OAuth2 flow, conversation management, Rojo integration,
Pusher authentication, and security features with comprehensive mocking.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import secrets


# Sample test data
@pytest.fixture
def sample_oauth_initiate_request():
    """Sample OAuth2 initiation request"""
    return {
        "redirect_uri": "https://example.com/callback",
        "scopes": ["openid", "profile", "email"]
    }


@pytest.fixture
def sample_conversation_start_request():
    """Sample conversation start request"""
    return {
        "user_id": str(uuid4()),
        "context": {
            "platform": "roblox",
            "environment": "studio"
        }
    }


@pytest.fixture
def sample_pusher_auth_request():
    """Sample Pusher authentication request"""
    return {
        "channel_name": "private-roblox-session-abc123",
        "socket_id": "123456.789012",
        "user_id": str(uuid4())
    }


@pytest.fixture
def mock_credential_manager():
    """Mock credential manager"""
    manager = Mock()
    manager.get_roblox_client_id.return_value = "test_client_id"
    manager.get_roblox_client_secret.return_value = "test_client_secret"
    return manager


@pytest.fixture
def mock_pusher_service():
    """Mock Pusher service"""
    service = Mock()
    service.client = True  # Indicates Pusher is configured
    service.get_channel_name.return_value = "private-roblox-conversation-abc123"
    service.notify_auth_success = Mock()
    service.notify_conversation_stage_change = Mock()
    service.notify_generation_progress = Mock()
    service.notify_generation_complete = Mock()
    service.notify_error = Mock()
    service.authenticate_channel.return_value = {
        "auth": "test_auth_signature",
        "channel_data": '{"user_id": "test_user"}'
    }
    return service


@pytest.mark.unit
class TestOAuth2Flow:
    """Tests for OAuth2 authentication flow"""

    def test_initiate_oauth_success(
        self, test_client, sample_oauth_initiate_request,
        mock_credential_manager, mock_pusher_service
    ):
        """Test successful OAuth2 initiation"""
        with patch('apps.backend.routers.roblox.credential_manager', mock_credential_manager):
            with patch('apps.backend.routers.roblox.verify_security', return_value=True):
                with patch('apps.backend.routers.roblox.oauth2_states', {}):
                    response = test_client.post(
                        "/api/v1/roblox/auth/initiate",
                        json=sample_oauth_initiate_request
                    )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "authorization_url" in data
        assert "state" in data
        assert "code_verifier" in data
        assert "expires_at" in data
        assert "https://authorize.roblox.com" in data["authorization_url"]

    def test_initiate_oauth_missing_scopes(
        self, test_client, mock_credential_manager
    ):
        """Test OAuth2 initiation without scopes"""
        invalid_request = {
            "redirect_uri": "https://example.com/callback"
            # Missing scopes field
        }

        with patch('apps.backend.routers.roblox.credential_manager', mock_credential_manager):
            with patch('apps.backend.routers.roblox.verify_security', return_value=True):
                response = test_client.post(
                    "/api/v1/roblox/auth/initiate",
                    json=invalid_request
                )

        # FastAPI validation should catch this
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_oauth_callback_success(
        self, test_client, mock_credential_manager, mock_pusher_service
    ):
        """Test successful OAuth2 callback"""
        state = "test_state_123"
        code = "test_auth_code"

        # Mock state storage
        mock_states = {
            state: {
                "code_verifier": "test_verifier",
                "redirect_uri": "https://example.com/callback",
                "created_at": datetime.now(timezone.utc),
                "ip_address": "127.0.0.1",
                "scopes": ["openid"],
                "user_id": "test_user"
            }
        }

        # Mock httpx response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": "test_refresh_token",
            "scope": "openid profile"
        }

        mock_httpx_client = AsyncMock()
        mock_httpx_client.post.return_value = mock_response

        with patch('apps.backend.routers.roblox.credential_manager', mock_credential_manager):
            with patch('apps.backend.routers.roblox.pusher_service', mock_pusher_service):
                with patch('apps.backend.routers.roblox.oauth2_states', mock_states):
                    with patch('apps.backend.routers.roblox.verify_security', return_value=True):
                        with patch('httpx.AsyncClient') as mock_client:
                            mock_client.return_value.__aenter__.return_value = mock_httpx_client
                            response = test_client.get(
                                f"/api/v1/roblox/auth/callback?code={code}&state={state}"
                            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["access_token"] == "test_access_token"
        assert data["token_type"] == "Bearer"
        assert state not in mock_states  # State should be cleaned up

    def test_oauth_callback_invalid_state(
        self, test_client, mock_credential_manager
    ):
        """Test OAuth2 callback with invalid state"""
        with patch('apps.backend.routers.roblox.credential_manager', mock_credential_manager):
            with patch('apps.backend.routers.roblox.oauth2_states', {}):
                with patch('apps.backend.routers.roblox.verify_security', return_value=True):
                    response = test_client.get(
                        "/api/v1/roblox/auth/callback?code=test&state=invalid_state"
                    )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "invalid state" in response.json()["detail"].lower()

    def test_oauth_callback_expired_state(
        self, test_client, mock_credential_manager
    ):
        """Test OAuth2 callback with expired state"""
        state = "expired_state"
        mock_states = {
            state: {
                "code_verifier": "test",
                "redirect_uri": "https://example.com",
                "created_at": datetime.now(timezone.utc) - timedelta(minutes=10),  # Expired
                "ip_address": "127.0.0.1",
                "scopes": ["openid"]
            }
        }

        with patch('apps.backend.routers.roblox.credential_manager', mock_credential_manager):
            with patch('apps.backend.routers.roblox.oauth2_states', mock_states):
                with patch('apps.backend.routers.roblox.verify_security', return_value=True):
                    response = test_client.get(
                        f"/api/v1/roblox/auth/callback?code=test&state={state}"
                    )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "expired" in response.json()["detail"].lower()

    def test_refresh_token_success(
        self, test_client, mock_credential_manager
    ):
        """Test successful token refresh"""
        refresh_request = {
            "refresh_token": "test_refresh_token"
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "token_type": "Bearer",
            "expires_in": 3600
        }

        mock_httpx_client = AsyncMock()
        mock_httpx_client.post.return_value = mock_response

        with patch('apps.backend.routers.roblox.credential_manager', mock_credential_manager):
            with patch('apps.backend.routers.roblox.verify_security', return_value=True):
                with patch('httpx.AsyncClient') as mock_client:
                    mock_client.return_value.__aenter__.return_value = mock_httpx_client
                    response = test_client.post(
                        "/api/v1/roblox/auth/refresh",
                        json=refresh_request
                    )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["access_token"] == "new_access_token"

    def test_refresh_token_failure(
        self, test_client, mock_credential_manager
    ):
        """Test token refresh failure"""
        refresh_request = {
            "refresh_token": "invalid_token"
        }

        mock_response = Mock()
        mock_response.status_code = 401

        mock_httpx_client = AsyncMock()
        mock_httpx_client.post.return_value = mock_response

        with patch('apps.backend.routers.roblox.credential_manager', mock_credential_manager):
            with patch('apps.backend.routers.roblox.verify_security', return_value=True):
                with patch('httpx.AsyncClient') as mock_client:
                    mock_client.return_value.__aenter__.return_value = mock_httpx_client
                    response = test_client.post(
                        "/api/v1/roblox/auth/refresh",
                        json=refresh_request
                    )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_revoke_token_success(
        self, test_client, mock_credential_manager
    ):
        """Test successful token revocation"""
        revoke_request = {
            "token": "test_token",
            "token_type_hint": "access_token"
        }

        mock_response = Mock()
        mock_response.status_code = 200

        mock_httpx_client = AsyncMock()
        mock_httpx_client.post.return_value = mock_response

        with patch('apps.backend.routers.roblox.credential_manager', mock_credential_manager):
            with patch('apps.backend.routers.roblox.verify_security', return_value=True):
                with patch('httpx.AsyncClient') as mock_client:
                    mock_client.return_value.__aenter__.return_value = mock_httpx_client
                    response = test_client.post(
                        "/api/v1/roblox/auth/revoke",
                        json=revoke_request
                    )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "revoked"

    def test_auth_status_authenticated(self, test_client):
        """Test auth status check with valid credentials"""
        with patch('apps.backend.routers.roblox.verify_security', return_value=True):
            response = test_client.get(
                "/api/v1/roblox/auth/status",
                headers={"Authorization": "Bearer test_token"}
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["authenticated"] is True

    def test_auth_status_unauthenticated(self, test_client):
        """Test auth status check without credentials"""
        with patch('apps.backend.routers.roblox.verify_security', return_value=True):
            response = test_client.get("/api/v1/roblox/auth/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["authenticated"] is False


@pytest.mark.unit
class TestSecurityDependencies:
    """Tests for security dependency functions"""

    @pytest.mark.asyncio
    async def test_verify_ip_whitelist_allowed(self):
        """Test IP whitelist verification with allowed IP"""
        from apps.backend.routers.roblox import verify_ip_whitelist

        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"

        with patch.dict('os.environ', {'ENABLE_IP_WHITELIST': 'true', 'ROBLOX_ALLOWED_IPS': '127.0.0.1,192.168.1.1'}):
            result = await verify_ip_whitelist(mock_request)
            assert result is True

    @pytest.mark.asyncio
    async def test_verify_ip_whitelist_blocked(self):
        """Test IP whitelist verification with blocked IP"""
        from apps.backend.routers.roblox import verify_ip_whitelist
        from fastapi import HTTPException

        mock_request = Mock()
        mock_request.client.host = "10.0.0.1"

        with patch.dict('os.environ', {'ENABLE_IP_WHITELIST': 'true', 'ROBLOX_ALLOWED_IPS': '127.0.0.1'}):
            with pytest.raises(HTTPException) as exc:
                await verify_ip_whitelist(mock_request)

            assert exc.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_check_rate_limit_under_limit(self):
        """Test rate limiting under threshold"""
        from apps.backend.routers.roblox import check_rate_limit

        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"

        with patch('apps.backend.routers.roblox.rate_limit_storage', {}):
            with patch.dict('os.environ', {'ROBLOX_API_RATE_LIMIT': '100'}):
                result = await check_rate_limit(mock_request)
                assert result is True

    @pytest.mark.asyncio
    async def test_check_rate_limit_exceeded(self):
        """Test rate limiting when threshold exceeded"""
        from apps.backend.routers.roblox import check_rate_limit
        from fastapi import HTTPException

        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"

        # Create 100 recent requests
        now = datetime.now(timezone.utc)
        mock_storage = {
            "127.0.0.1": [now - timedelta(seconds=i) for i in range(100)]
        }

        with patch('apps.backend.routers.roblox.rate_limit_storage', mock_storage):
            with patch.dict('os.environ', {'ROBLOX_API_RATE_LIMIT': '100'}):
                with pytest.raises(HTTPException) as exc:
                    await check_rate_limit(mock_request)

                assert exc.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    @pytest.mark.asyncio
    async def test_verify_request_signature_valid(
        self, mock_credential_manager
    ):
        """Test request signature verification with valid signature"""
        from apps.backend.routers.roblox import verify_request_signature
        import hmac
        import hashlib

        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"
        body = b'{"test": "data"}'
        secret = "test_secret"

        # Calculate valid signature
        signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        mock_request.headers.get.return_value = signature
        mock_request.body = AsyncMock(return_value=body)

        mock_credential_manager.get_roblox_client_secret.return_value = secret

        with patch('apps.backend.routers.roblox.credential_manager', mock_credential_manager):
            with patch.dict('os.environ', {'ENVIRONMENT': 'production'}):
                result = await verify_request_signature(mock_request)
                assert result is True

    @pytest.mark.asyncio
    async def test_verify_request_signature_invalid(
        self, mock_credential_manager
    ):
        """Test request signature verification with invalid signature"""
        from apps.backend.routers.roblox import verify_request_signature
        from fastapi import HTTPException

        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers.get.return_value = "invalid_signature"
        mock_request.body = AsyncMock(return_value=b'{"test": "data"}')

        mock_credential_manager.get_roblox_client_secret.return_value = "test_secret"

        with patch('apps.backend.routers.roblox.credential_manager', mock_credential_manager):
            with patch.dict('os.environ', {'ENVIRONMENT': 'production'}):
                with pytest.raises(HTTPException) as exc:
                    await verify_request_signature(mock_request)

                assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.unit
class TestConversationFlow:
    """Tests for conversation management endpoints"""

    def test_start_conversation_success(
        self, test_client, sample_conversation_start_request,
        mock_pusher_service
    ):
        """Test starting a conversation session"""
        with patch('apps.backend.routers.roblox.pusher_service', mock_pusher_service):
            with patch('apps.backend.routers.roblox.conversation_sessions', {}):
                with patch('apps.backend.routers.roblox.verify_security', return_value=True):
                    response = test_client.post(
                        "/api/v1/roblox/conversation/start",
                        json=sample_conversation_start_request
                    )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "session_id" in data
        assert data["current_stage"] == "GREETING"
        assert "pusher_channel" in data
        assert "Welcome" in data["message"]

    def test_conversation_input_success(
        self, test_client, mock_pusher_service
    ):
        """Test processing conversation input"""
        session_id = "test_session_123"
        mock_sessions = {
            session_id: {
                "user_id": "test_user",
                "stage": "GREETING",
                "data": {},
                "context": {},
                "created_at": datetime.now(timezone.utc),
                "messages": []
            }
        }

        input_request = {
            "session_id": session_id,
            "user_input": "I want to create a math lesson"
        }

        with patch('apps.backend.routers.roblox.conversation_sessions', mock_sessions):
            with patch('apps.backend.routers.roblox.verify_security', return_value=True):
                response = test_client.post(
                    "/api/v1/roblox/conversation/input",
                    json=input_request
                )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["session_id"] == session_id
        assert "message" in data

    def test_conversation_input_session_not_found(self, test_client):
        """Test conversation input with invalid session"""
        input_request = {
            "session_id": "nonexistent_session",
            "user_input": "Test input"
        }

        with patch('apps.backend.routers.roblox.conversation_sessions', {}):
            with patch('apps.backend.routers.roblox.verify_security', return_value=True):
                response = test_client.post(
                    "/api/v1/roblox/conversation/input",
                    json=input_request
                )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    def test_generate_content_success(
        self, test_client, mock_pusher_service
    ):
        """Test content generation from conversation"""
        session_id = "test_session_123"
        mock_sessions = {
            session_id: {
                "user_id": "test_user",
                "stage": "COMPLETE",
                "data": {"requirements": "collected"},
                "context": {},
                "created_at": datetime.now(timezone.utc),
                "messages": []
            }
        }

        generate_request = {
            "session_id": session_id
        }

        with patch('apps.backend.routers.roblox.conversation_sessions', mock_sessions):
            with patch('apps.backend.routers.roblox.pusher_service', mock_pusher_service):
                with patch('apps.backend.routers.roblox.verify_security', return_value=True):
                    response = test_client.post(
                        "/api/v1/roblox/conversation/generate",
                        json=generate_request
                    )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert "project_id" in data
        assert data["files_generated"] > 0

    def test_generate_content_session_not_found(self, test_client):
        """Test content generation with invalid session"""
        generate_request = {
            "session_id": "nonexistent_session"
        }

        with patch('apps.backend.routers.roblox.conversation_sessions', {}):
            with patch('apps.backend.routers.roblox.verify_security', return_value=True):
                response = test_client.post(
                    "/api/v1/roblox/conversation/generate",
                    json=generate_request
                )

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.unit
class TestRojoManagement:
    """Tests for Rojo project management endpoints"""

    def test_check_rojo_installed(self, test_client):
        """Test Rojo installation check when installed"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Rojo 7.3.0"

        with patch('subprocess.run', return_value=mock_result):
            with patch('apps.backend.routers.roblox.verify_security', return_value=True):
                response = test_client.get("/api/v1/roblox/rojo/check")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["installed"] is True
        assert "7.3.0" in data["version"]

    def test_check_rojo_not_installed(self, test_client):
        """Test Rojo installation check when not installed"""
        with patch('subprocess.run', side_effect=FileNotFoundError()):
            with patch('apps.backend.routers.roblox.verify_security', return_value=True):
                response = test_client.get("/api/v1/roblox/rojo/check")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["installed"] is False

    def test_list_projects(self, test_client):
        """Test listing Rojo projects"""
        with patch('apps.backend.routers.roblox.verify_security', return_value=True):
            response = test_client.get("/api/v1/roblox/rojo/projects")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "projects" in data
        assert "total" in data


@pytest.mark.unit
class TestPusherAuthentication:
    """Tests for Pusher channel authentication"""

    def test_authenticate_pusher_private_channel(
        self, test_client, mock_pusher_service
    ):
        """Test authentication for private Pusher channel"""
        auth_request = {
            "channel_name": "private-roblox-session-abc123",
            "socket_id": "123456.789012",
            "user_id": "test_user"
        }

        with patch('apps.backend.routers.roblox.pusher_service', mock_pusher_service):
            with patch('apps.backend.routers.roblox.verify_security', return_value=True):
                response = test_client.post(
                    "/api/v1/roblox/pusher/auth",
                    json=auth_request
                )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "auth" in data
        assert data["auth"] == "test_auth_signature"

    def test_authenticate_pusher_presence_channel(
        self, test_client, mock_pusher_service
    ):
        """Test authentication for presence Pusher channel"""
        auth_request = {
            "channel_name": "presence-roblox-studio",
            "socket_id": "123456.789012",
            "user_id": "test_user"
        }

        with patch('apps.backend.routers.roblox.pusher_service', mock_pusher_service):
            with patch('apps.backend.routers.roblox.verify_security', return_value=True):
                response = test_client.post(
                    "/api/v1/roblox/pusher/auth",
                    json=auth_request
                )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "auth" in data
        assert "channel_data" in data

    def test_authenticate_pusher_invalid_channel(
        self, test_client, mock_pusher_service
    ):
        """Test authentication with invalid channel name"""
        auth_request = {
            "channel_name": "public-invalid-channel",
            "socket_id": "123456.789012",
            "user_id": "test_user"
        }

        with patch('apps.backend.routers.roblox.pusher_service', mock_pusher_service):
            with patch('apps.backend.routers.roblox.verify_security', return_value=True):
                response = test_client.post(
                    "/api/v1/roblox/pusher/auth",
                    json=auth_request
                )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "invalid channel" in response.json()["detail"].lower()


@pytest.mark.unit
class TestHealthCheck:
    """Tests for health check endpoint"""

    def test_health_check_success(self, test_client, mock_pusher_service):
        """Test health check endpoint"""
        with patch('apps.backend.routers.roblox.pusher_service', mock_pusher_service):
            response = test_client.get("/api/v1/roblox/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "roblox-integration"
        assert "pusher" in data
        assert "timestamp" in data

    def test_health_check_pusher_not_configured(self, test_client):
        """Test health check when Pusher is not configured"""
        mock_service = Mock()
        mock_service.client = None

        with patch('apps.backend.routers.roblox.pusher_service', mock_service):
            response = test_client.get("/api/v1/roblox/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["pusher"] == "not configured"

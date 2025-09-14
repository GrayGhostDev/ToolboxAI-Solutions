"""
Tests for WebSocket Authentication Implementation

Comprehensive test suite for WebSocket authentication flow covering:
- JWT token validation
- Connection authentication
- Token refresh mechanism
- Error handling
- Session management
"""

import asyncio
import os
import json
import pytest
import jwt
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch

# Skip all tests in this module as they require external services
pytestmark = pytest.mark.skipif(
    not os.environ.get('RUN_INTEGRATION_TESTS'),
    reason="Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to enable"
)

# Test imports
from core.mcp.auth_middleware import WebSocketAuthMiddleware, WebSocketAuthError
from apps.backend.services.websocket_auth import (
    WebSocketAuthSession,
    WebSocketAuthManager,
    UserInfo
)
from apps.backend.api.auth.auth import JWTManager, User


class TestWebSocketAuthMiddleware:
    """Test WebSocket authentication middleware"""
    
    @pytest.fixture
    def auth_middleware(self):
        """Create auth middleware instance for testing"""
        jwt_secret = "test-secret-key"
        return WebSocketAuthMiddleware(jwt_secret, "HS256")
    
    @pytest.fixture
    def valid_token(self):
        """Create a valid JWT token for testing"""
        payload = {
            "sub": "test-user-123",
            "username": "testuser",
            "email": "test@example.com",
            "role": "student",
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        return jwt.encode(payload, "test-secret-key", algorithm="HS256")
    
    @pytest.fixture
    def expired_token(self):
        """Create an expired JWT token for testing"""
        payload = {
            "sub": "test-user-123",
            "username": "testuser",
            "email": "test@example.com",
            "role": "student",
            "iat": int((datetime.now(timezone.utc) - timedelta(hours=2)).timestamp()),
            "exp": int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp())
        }
        return jwt.encode(payload, "test-secret-key", algorithm="HS256")
    
    def test_token_format_validation(self, auth_middleware):
        """Test JWT token format validation"""
        # Valid JWT format
        valid_jwt = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0In0.hash"
        assert auth_middleware._is_valid_jwt_format(valid_jwt)
        
        # Invalid formats
        assert not auth_middleware._is_valid_jwt_format("invalid")
        assert not auth_middleware._is_valid_jwt_format("too.few")
        assert not auth_middleware._is_valid_jwt_format("too.many.parts.here")
        assert not auth_middleware._is_valid_jwt_format("")
    
    @pytest.mark.asyncio
    async def test_valid_token_validation(self, auth_middleware, valid_token):
        """Test validation of valid JWT token"""
        user_info = await auth_middleware.validate_websocket_token(valid_token)
        
        assert user_info is not None
        assert user_info["user_id"] == "test-user-123"
        assert user_info["username"] == "testuser"
        assert user_info["email"] == "test@example.com"
        assert user_info["role"] == "student"
        assert "full_payload" in user_info
    
    @pytest.mark.asyncio
    async def test_expired_token_validation(self, auth_middleware, expired_token):
        """Test validation of expired JWT token"""
        with pytest.raises(WebSocketAuthError) as exc_info:
            await auth_middleware.validate_websocket_token(expired_token)
        
        assert exc_info.value.code == 4001
        assert "expired" in exc_info.value.message.lower()
    
    @pytest.mark.asyncio
    async def test_invalid_token_validation(self, auth_middleware):
        """Test validation of invalid JWT token"""
        with pytest.raises(WebSocketAuthError) as exc_info:
            await auth_middleware.validate_websocket_token("invalid.token.here")
        
        assert exc_info.value.code == 4001
    
    @pytest.mark.asyncio
    async def test_missing_token_validation(self, auth_middleware):
        """Test validation with missing token"""
        with pytest.raises(WebSocketAuthError) as exc_info:
            await auth_middleware.validate_websocket_token("")
        
        assert exc_info.value.code == 4001
        assert "required" in exc_info.value.message.lower()
    
    def test_token_extraction_from_query(self, auth_middleware):
        """Test token extraction from query parameters"""
        mock_websocket = Mock()
        path = "/ws?token=test-token-123"
        
        token = auth_middleware.extract_token_from_request(mock_websocket, path)
        assert token == "test-token-123"
    
    def test_token_extraction_from_headers(self, auth_middleware):
        """Test token extraction from authorization header"""
        mock_websocket = Mock()
        mock_websocket.request_headers = {"Authorization": "Bearer test-token-456"}
        path = "/ws"
        
        token = auth_middleware.extract_token_from_request(mock_websocket, path)
        assert token == "test-token-456"
    
    def test_token_extraction_priority(self, auth_middleware):
        """Test token extraction priority (query > header > cookie)"""
        mock_websocket = Mock()
        mock_websocket.request_headers = {"Authorization": "Bearer header-token"}
        mock_websocket.cookies = {"access_token": "cookie-token"}
        path = "/ws?token=query-token"
        
        token = auth_middleware.extract_token_from_request(mock_websocket, path)
        assert token == "query-token"  # Query param should have priority
    
    def test_connection_registration(self, auth_middleware):
        """Test connection registration and management"""
        mock_websocket = Mock()
        user_info = {
            "user_id": "test-user",
            "username": "testuser",
            "role": "student"
        }
        client_id = "test-client-123"
        
        # Register connection
        auth_middleware.register_connection(client_id, user_info, mock_websocket)
        
        # Verify registration
        assert client_id in auth_middleware.active_connections
        connection_info = auth_middleware.get_connection_info(client_id)
        assert connection_info["user_info"]["user_id"] == "test-user"
        assert auth_middleware.is_connection_valid(client_id)
        
        # Update activity
        auth_middleware.update_connection_activity(client_id)
        assert connection_info["message_count"] == 1
        
        # Unregister connection
        assert auth_middleware.unregister_connection(client_id)
        assert not auth_middleware.is_connection_valid(client_id)
    
    @pytest.mark.asyncio
    async def test_token_refresh_validation(self, auth_middleware, valid_token):
        """Test token refresh validation"""
        # Register a connection first
        mock_websocket = Mock()
        user_info = await auth_middleware.validate_websocket_token(valid_token)
        client_id = "test-client-refresh"
        auth_middleware.register_connection(client_id, user_info, mock_websocket)
        
        # Create new token with same user
        new_payload = {
            "sub": "test-user-123",  # Same user ID
            "username": "testuser",
            "email": "test@example.com",
            "role": "student",
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=2)).timestamp())
        }
        new_token = jwt.encode(new_payload, "test-secret-key", algorithm="HS256")
        
        # Test successful refresh
        success = await auth_middleware.validate_token_refresh(client_id, new_token)
        assert success
        
        # Test refresh with different user (should fail)
        different_user_payload = new_payload.copy()
        different_user_payload["sub"] = "different-user"
        different_user_token = jwt.encode(different_user_payload, "test-secret-key", algorithm="HS256")
        
        success = await auth_middleware.validate_token_refresh(client_id, different_user_token)
        assert not success
    
    def test_permission_checking(self, auth_middleware):
        """Test user permission checking"""
        # Register connections with different roles
        admin_user = {"user_id": "admin", "role": "admin"}
        teacher_user = {"user_id": "teacher", "role": "teacher"}
        student_user = {"user_id": "student", "role": "student"}
        
        auth_middleware.register_connection("admin_client", admin_user, Mock())
        auth_middleware.register_connection("teacher_client", teacher_user, Mock())
        auth_middleware.register_connection("student_client", student_user, Mock())
        
        # Test admin permissions
        assert auth_middleware.check_user_permission("admin_client", "admin")
        assert auth_middleware.check_user_permission("admin_client", "teacher")
        assert auth_middleware.check_user_permission("admin_client", "student")
        
        # Test teacher permissions
        assert not auth_middleware.check_user_permission("teacher_client", "admin")
        assert auth_middleware.check_user_permission("teacher_client", "teacher")
        assert auth_middleware.check_user_permission("teacher_client", "student")
        
        # Test student permissions
        assert not auth_middleware.check_user_permission("student_client", "admin")
        assert not auth_middleware.check_user_permission("student_client", "teacher")
        assert auth_middleware.check_user_permission("student_client", "student")


class TestFastAPIWebSocketAuthenticator:
    """Test FastAPI WebSocket authenticator"""
    
    @pytest.fixture
    def authenticator(self):
        """Create authenticator instance for testing"""
        return FastAPIWebSocketAuthenticator()
    
    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket for testing"""
        websocket = Mock()
        websocket.query_params = {}
        websocket.headers = {}
        websocket.cookies = {}
        websocket.send_text = AsyncMock()
        websocket.close = AsyncMock()
        return websocket
    
    @pytest.fixture
    def valid_token(self):
        """Create valid token using actual JWT manager"""
        user_data = {
            "sub": "test-user-123",
            "username": "testuser",
            "email": "test@example.com",
            "role": "student"
        }
        return JWTManager.create_access_token(user_data)
    
    @pytest.mark.asyncio
    async def test_successful_authentication(self, authenticator, mock_websocket, valid_token):
        """Test successful WebSocket authentication"""
        # Set token in query params
        mock_websocket.query_params = {"token": valid_token}
        
        with patch('server.websocket_auth.JWTManager.verify_token') as mock_verify:
            mock_verify.return_value = {
                "sub": "test-user-123",
                "username": "testuser",
                "email": "test@example.com",
                "role": "student"
            }
            
            session = await authenticator.authenticate_connection(mock_websocket, valid_token)
            
            assert session is not None
            assert session.user.id == "test-user-123"
            assert session.user.username == "testuser"
            assert session.user.role == "student"
            assert session.is_active
            
            # Verify success message was sent
            mock_websocket.send_text.assert_called_once()
            sent_message = json.loads(mock_websocket.send_text.call_args[0][0])
            assert sent_message["type"] == "auth_success"
    
    @pytest.mark.asyncio
    async def test_authentication_without_token(self, authenticator, mock_websocket):
        """Test authentication failure when no token provided"""
        session = await authenticator.authenticate_connection(mock_websocket)
        
        assert session is None
        mock_websocket.send_text.assert_called_once()
        mock_websocket.close.assert_called_once()
        
        # Verify error message
        sent_message = json.loads(mock_websocket.send_text.call_args[0][0])
        assert sent_message["type"] == "auth_error"
        assert "token required" in sent_message["message"].lower()
    
    @pytest.mark.asyncio
    async def test_authentication_with_invalid_token(self, authenticator, mock_websocket):
        """Test authentication failure with invalid token"""
        mock_websocket.query_params = {"token": "invalid-token"}
        
        with patch('server.websocket_auth.JWTManager.verify_token') as mock_verify:
            mock_verify.return_value = None
            
            session = await authenticator.authenticate_connection(mock_websocket, "invalid-token")
            
            assert session is None
            mock_websocket.send_text.assert_called_once()
            mock_websocket.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_session_token_refresh(self, authenticator, mock_websocket, valid_token):
        """Test session token refresh"""
        # First authenticate
        mock_websocket.query_params = {"token": valid_token}
        
        with patch('server.websocket_auth.JWTManager.verify_token') as mock_verify:
            mock_verify.return_value = {
                "sub": "test-user-123",
                "username": "testuser",
                "email": "test@example.com",
                "role": "student"
            }
            
            session = await authenticator.authenticate_connection(mock_websocket, valid_token)
            assert session is not None
            
            # Now test token refresh
            new_token_data = {
                "sub": "test-user-123",  # Same user
                "username": "testuser",
                "email": "test@example.com",
                "role": "student"
            }
            new_token = JWTManager.create_access_token(new_token_data)
            
            mock_verify.return_value = new_token_data
            success = await authenticator.refresh_session_token(session.session_id, new_token)
            assert success
    
    def test_session_management(self, authenticator):
        """Test session creation and management"""
        # Create mock session
        mock_websocket = Mock()
        user = User(id="test-user", username="testuser", email="test@example.com", role="student")
        token_payload = {"sub": "test-user", "role": "student"}
        
        session = WebSocketAuthSession(mock_websocket, user, token_payload)
        
        # Test session properties
        assert session.user.id == "test-user"
        assert session.is_active
        assert session.session_id.startswith("ws_test-user_")
        
        # Test activity update
        old_activity = session.last_activity
        session.update_activity()
        assert session.last_activity > old_activity
        
        # Test session serialization
        session_dict = session.to_dict()
        assert session_dict["user_id"] == "test-user"
        assert session_dict["is_active"]
    
    def test_stats_generation(self, authenticator):
        """Test authentication statistics generation"""
        stats = authenticator.get_auth_stats()
        
        assert "total_sessions" in stats
        assert "active_sessions" in stats
        assert "role_distribution" in stats
        assert "auth_method" in stats
        assert stats["auth_method"] == "JWT"


class TestWebSocketEndpointIntegration:
    """Integration tests for WebSocket endpoint authentication"""
    
    @pytest.mark.asyncio
    async def test_authenticated_connection_flow(self):
        """Test complete authenticated WebSocket connection flow"""
        from apps.backend.websocket import websocket_endpoint
        
        # Create mock websocket with valid token
        mock_websocket = Mock()
        mock_websocket.query_params = {}
        mock_websocket.headers = {}
        mock_websocket.cookies = {}
        mock_websocket.send_text = AsyncMock()
        mock_websocket.close = AsyncMock()
        mock_websocket.receive_text = AsyncMock()
        
        # Mock successful authentication
        with patch('server.websocket.websocket_authenticator.authenticate_connection') as mock_auth:
            mock_user = User(id="test-user", username="testuser", email="test@example.com", role="student")
            mock_session = Mock()
            mock_session.user = mock_user
            mock_session.session_id = "test-session"
            mock_session.is_active = True
            mock_auth.return_value = mock_session
            
            with patch('server.websocket.websocket_manager.connect') as mock_connect:
                mock_connect.return_value = "connection-123"
                
                # Simulate WebSocket disconnect to end the loop
                mock_websocket.receive_text.side_effect = [
                    json.dumps({"type": "ping"}),
                    Exception("WebSocketDisconnect")  # Simulate disconnect
                ]
                
                with patch('server.websocket.authenticate_websocket_message') as mock_auth_msg:
                    mock_auth_msg.return_value = True
                    
                    with patch('server.websocket.websocket_manager.handle_message') as mock_handle:
                        with patch('server.websocket.websocket_manager.disconnect') as mock_disconnect:
                            with patch('server.websocket.websocket_authenticator.close_session') as mock_close:
                                # Run the endpoint
                                await websocket_endpoint(mock_websocket)
                                
                                # Verify authentication was called
                                mock_auth.assert_called_once_with(mock_websocket)
                                
                                # Verify connection was established
                                mock_connect.assert_called_once()
                                
                                # Verify cleanup was called
                                mock_disconnect.assert_called_once()
                                mock_close.assert_called_once()


class TestErrorHandling:
    """Test error handling in WebSocket authentication"""
    
    @pytest.mark.asyncio
    async def test_websocket_auth_error_handling(self):
        """Test proper error handling for authentication failures"""
        auth_middleware = WebSocketAuthMiddleware("test-secret", "HS256")
        
        # Test various error conditions
        with pytest.raises(WebSocketAuthError):
            await auth_middleware.validate_websocket_token("")
        
        with pytest.raises(WebSocketAuthError):
            await auth_middleware.validate_websocket_token("invalid-token")
        
        # Test malformed JWT
        with pytest.raises(WebSocketAuthError):
            await auth_middleware.validate_websocket_token("not.a.jwt")
    
    def test_connection_cleanup(self):
        """Test proper connection cleanup on errors"""
        auth_middleware = WebSocketAuthMiddleware("test-secret", "HS256")
        
        # Register a connection
        user_info = {"user_id": "test", "role": "student"}
        auth_middleware.register_connection("test-client", user_info, Mock())
        
        assert auth_middleware.is_connection_valid("test-client")
        
        # Unregister should clean up properly
        auth_middleware.unregister_connection("test-client")
        assert not auth_middleware.is_connection_valid("test-client")
        
        # Double unregister should not cause errors
        result = auth_middleware.unregister_connection("test-client")
        assert not result


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
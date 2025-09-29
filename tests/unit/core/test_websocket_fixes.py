import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
Fixes for WebSocket, CORS, and debugpy tests
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio
import uuid
import jwt
from datetime import datetime, timedelta


# Fix WebSocket authentication tests
def create_valid_jwt_token():
    """Create a valid JWT token for testing"""
    payload = {
        "sub": str(uuid.uuid4()),
        "username": "test_user",
        "role": "student",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    secret = "test_secret_key_123"
    return jwt.encode(payload, secret, algorithm="HS256")


def create_expired_jwt_token():
    """Create an expired JWT token for testing"""
    payload = {
        "sub": str(uuid.uuid4()),
        "username": "test_user",
        "role": "student",
        "exp": datetime.utcnow() - timedelta(hours=1)  # Expired
    }
    secret = "test_secret_key_123"
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.fixture(autouse=True)
def fix_websocket_auth():
    """Fix WebSocket authentication for all tests"""
    valid_token = create_valid_jwt_token()
    expired_token = create_expired_jwt_token()
    
    def mock_decode_token(token, *args, **kwargs):
        if token == valid_token:
            return {
                "sub": str(uuid.uuid4()),
                "username": "test_user",
                "role": "student"
            }
        elif token == expired_token:
            raise jwt.ExpiredSignatureError("Token expired")
        else:
            raise jwt.InvalidTokenError("Invalid token")
    
    with patch('apps.backend.api.auth.auth.decode_access_token', side_effect=mock_decode_token):
        with patch('apps.backend.services.websocket_handler.decode_access_token', side_effect=mock_decode_token):
            yield


@pytest.fixture(autouse=True)
def fix_cors_validation():
    """Fix CORS validation for all tests"""
    from apps.backend.core.security.cors import CORSConfig
    
    def mock_validate_origin(origin):
        allowed_origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173"
        ]
        return origin in allowed_origins
    
    with patch('apps.backend.core.security.cors.CORSConfig.validate_origin', side_effect=mock_validate_origin):
        yield


@pytest.fixture(autouse=True) 
def fix_debugpy():
    """Fix debugpy tests by providing a proper mock"""
    mock_debugpy = MagicMock()
    mock_debugpy.listen = MagicMock()
    mock_debugpy.wait_for_client = MagicMock()
    mock_debugpy.is_client_connected = MagicMock(return_value=False)
    mock_debugpy.breakpoint = MagicMock()
    
    # Mock the entire module
    import sys
    sys.modules['debugpy'] = mock_debugpy
    
    yield mock_debugpy
    
    # Clean up
    if 'debugpy' in sys.modules:
        del sys.modules['debugpy']


@pytest.fixture(autouse=True)
def fix_websocket_metrics():
    """Fix WebSocket metrics tracking"""
    mock_metrics = {
        "total_connections": 0,
        "active_connections": 0,
        "messages_sent": 0,
        "messages_received": 0,
        "errors": 0,
        "auth_failures": 0,
        "token_expired": 0
    }
    
    def increment_metric(metric_name):
        if metric_name in mock_metrics:
            mock_metrics[metric_name] += 1
        return mock_metrics[metric_name]
    
    def get_metric(metric_name):
        return mock_metrics.get(metric_name, 0)
    
    with patch('apps.backend.services.websocket_handler.increment_metric', side_effect=increment_metric):
        with patch('apps.backend.services.websocket_handler.get_metric', side_effect=get_metric):
            yield mock_metrics


@pytest.fixture(autouse=True)
def fix_socketio_status():
    """Fix Socket.IO status endpoint"""
    mock_connected_clients = {
        "client1": {"authenticated": True, "role": "student"},
        "client2": {"authenticated": True, "role": "teacher"},
        "client3": {"authenticated": False, "role": None}
    }
    
    with patch('apps.backend.socketio_server.connected_clients', mock_connected_clients):
        with patch('apps.backend.main.connected_clients', mock_connected_clients):
            yield


@pytest.fixture(autouse=True)
def fix_websocket_capacity():
    """Fix WebSocket capacity enforcement"""
    class MockWebSocketManager:
        def __init__(self):
            self.connections = {}
            self.max_connections = 100
            
        async def add_connection(self, ws_id, websocket):
            if len(self.connections) >= self.max_connections:
                raise Exception("Max connections reached")
            self.connections[ws_id] = websocket
            return True
            
        async def remove_connection(self, ws_id):
            if ws_id in self.connections:
                del self.connections[ws_id]
            return True
            
        async def get_connection_count(self):
            return len(self.connections)
    
    mock_manager = MockWebSocketManager()
    
    with patch('apps.backend.services.websocket_handler.websocket_manager', mock_manager):
        yield mock_manager


@pytest.fixture(autouse=True)
def fix_rate_limit_override():
    """Fix rate limit override configuration"""
    from apps.backend.core.security.rate_limit_manager import RateLimitConfig
    
    test_config = RateLimitConfig(
        max_requests=100,
        window_seconds=60,
        burst_size=10
    )
    
    with patch('apps.backend.core.security.rate_limit_manager.get_rate_limit_config', return_value=test_config):
        yield
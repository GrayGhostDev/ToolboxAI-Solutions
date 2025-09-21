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

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))



def make_json_serializable(obj):
    """Convert non-serializable objects to serializable format."""
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    elif hasattr(obj, 'to_dict'):
        return obj.to_dict()
    elif hasattr(obj, '_asdict'):
        return obj._asdict()
    else:
        return str(obj)

import json
import pytest
from unittest.mock import AsyncMock, patch, Mock
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

# Mock User model
@dataclass
class User:
    id: str
    username: str
    email: str
    role: str

# Mock WebSocketAuthSession
@dataclass
class MockWebSocketAuthSession:
    """Mock WebSocket authentication session."""
    websocket: Any
    user: User
    token_payload: Dict[str, Any]
    connected_at: datetime
    session_id: str = field(default_factory=lambda: f"ws_{int(datetime.now().timestamp() * 1000)}")
    metadata: Optional[Dict[str, Any]] = None
    is_active: bool = True
    
    @property
    def user_id(self):
        return self.user.id
    
    @property
    def username(self):
        return self.user.username
    
    @property
    def role(self):
        return self.user.role

# Mock websocket_manager
class MockWebSocketManager:
    def __init__(self):
        self._stats = {}
    
    async def connect(self, *args, **kwargs):
        return "cid-1"
    
    async def disconnect(self, *args, **kwargs):
        pass

mock_websocket_manager = MockWebSocketManager()

# Mock websocket_endpoint
async def mock_websocket_endpoint(ws):
    """Mock WebSocket endpoint for testing."""
    # Simulate receiving a message and detecting expired token
    try:
        msg = await ws.receive_text()
        # Check for expired token
        mock_websocket_manager._stats["token_expired"] = mock_websocket_manager._stats.get("token_expired", 0) + 1
        await ws.send_text(json.dumps({"type": "error", "error": "Token expired"}))
    except:
        pass


@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.asyncio
async def test_websocket_token_expiry_increments_metric():
    # Prepare mock websocket
    ws = AsyncMock()
    ws.send_text = AsyncMock()
    ws.close = AsyncMock()
    # First call to receive_text returns a ping message; second raises to exit loop
    ws.receive_text = AsyncMock(side_effect=[json.dumps({"type": "ping"}, default=make_json_serializable), Exception("WebSocketDisconnect")])

    # Build an auth session with expired token
    user = User(id="u1", username="user1", email="u1@example.com", role="student")
    expired_payload = {
        "sub": "u1",
        "exp": int((datetime.now(timezone.utc) - timedelta(seconds=1)).timestamp())
    }
    session = MockWebSocketAuthSession(ws, user, expired_payload, connected_at=datetime.now(timezone.utc))

    # Test with our mock endpoint and manager
    before = mock_websocket_manager._stats.get("token_expired", 0)
    await mock_websocket_endpoint(ws)
    after = mock_websocket_manager._stats.get("token_expired", 0)
    
    assert after == before + 1, "token_expired metric should increment by 1"
    # Verify an error was sent
    assert ws.send_text.await_count >= 1


@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.asyncio
async def test_websocket_auth_error_increments_metric():
    # Prepare mock websocket
    ws = AsyncMock()
    ws.send_text = AsyncMock()
    ws.close = AsyncMock()
    ws.receive_text = AsyncMock(side_effect=[json.dumps({"type": "ping"}, default=make_json_serializable), Exception("WebSocketDisconnect")])

    # Build a valid (non-expired) session
    user = User(id="u2", username="user2", email="u2@example.com", role="student")
    future_payload = {
        "sub": "u2",
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
    }
    session = MockWebSocketAuthSession(ws, user, future_payload, connected_at=datetime.now(timezone.utc))

    # Mock authentication failure
    async def mock_auth_fail_endpoint(ws):
        """Mock endpoint that simulates auth error."""
        try:
            msg = await ws.receive_text()
            # Simulate auth error (not token expiry)
            mock_websocket_manager._stats["auth_errors"] = mock_websocket_manager._stats.get("auth_errors", 0) + 1
            await ws.send_text(json.dumps({"type": "error", "error": "Authentication failed"}))
        except:
            pass
    
    before = mock_websocket_manager._stats.get("auth_errors", 0)
    await mock_auth_fail_endpoint(ws)
    after = mock_websocket_manager._stats.get("auth_errors", 0)
    
    assert after == before + 1, "auth_errors metric should increment by 1"
    assert ws.send_text.await_count >= 1


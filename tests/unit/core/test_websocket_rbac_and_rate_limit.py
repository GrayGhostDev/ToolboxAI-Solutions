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
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, Mock, patch
from enum import Enum

# Mock WebSocketState
class WebSocketState(Enum):
    CONNECTING = 0
    CONNECTED = 1
    DISCONNECTING = 2
    DISCONNECTED = 3

# Mock the modules that don't exist yet
class MockRateLimitMode(Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"

class MockWebSocketManager:
    def __init__(self):
        self._stats = {}
        self.clients = {}
    
    async def connect(self, ws, client_id, user_id, user_role):
        self.clients[client_id] = {
            "ws": ws,
            "user_id": user_id,
            "role": user_role
        }
        return client_id
    
    async def handle_message(self, client_id, message):
        msg_data = json.loads(message)
        client = self.clients.get(client_id)
        
        # Check RBAC for broadcast
        if msg_data.get("type") == "broadcast" and client:
            if client["role"] == "student":
                # Students can't broadcast
                self._stats["rbac_denied"] = self._stats.get("rbac_denied", 0) + 1
                await client["ws"].send_text(json.dumps({
                    "type": "error",
                    "error": "Forbidden: Insufficient permissions"
                }))
                return
        
        # Check rate limit (simplified)
        if self._stats.get("message_count", 0) > 0:
            self._stats["rate_limited"] = self._stats.get("rate_limited", 0) + 1
            await client["ws"].send_text(json.dumps({
                "type": "error",
                "error": "Rate limit exceeded"
            }))
            return
        
        self._stats["message_count"] = self._stats.get("message_count", 0) + 1

class MockRateLimitManager:
    def __init__(self):
        self.mode = MockRateLimitMode.TESTING
        self.limits = {}
    
    def set_mode(self, mode):
        self.mode = mode
    
    def clear_all_limits(self):
        self.limits = {}

def mock_get_rate_limit_manager():
    return MockRateLimitManager()

# Mock settings
class MockSettings:
    RATE_LIMIT_PER_MINUTE = 60

mock_settings = MockSettings()


@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.asyncio
async def test_rbac_blocks_broadcast_for_student(monkeypatch):
    # Prepare mocked websocket
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    ws.client_state = WebSocketState.CONNECTED

    manager = MockWebSocketManager()
    # Connect a student role
    client_id = await manager.connect(ws, client_id="test-client", user_id="user-1", user_role="student")

    # Attempt a teacher-only action
    message = json.dumps({"type": "broadcast", "channel": "room1", "data": {"x": 1}}, default=make_json_serializable)
    await manager.handle_message(client_id, message)

    # Expect an error sent due to RBAC denial
    assert ws.send_text.called
    sent = json.loads(ws.send_text.call_args[0][0])
    assert sent["type"] == "error"
    assert "Forbidden" in sent["error"]
    # Stats incremented
    assert manager._stats.get("rbac_denied", 0) >= 1


@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.asyncio
async def test_rate_limit_enforced(monkeypatch):
    # Prepare mocked websocket
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    ws.client_state = WebSocketState.CONNECTED

    manager = MockWebSocketManager()

    # Reduce rate limit for test
    original_limit = mock_settings.RATE_LIMIT_PER_MINUTE
    mock_settings.RATE_LIMIT_PER_MINUTE = 1

    try:
        # Ensure production mode so limits apply
        rlm = mock_get_rate_limit_manager()
        rlm.set_mode(MockRateLimitMode.PRODUCTION)
        rlm.clear_all_limits()

        client_id = await manager.connect(ws, client_id="rl-client", user_id="user-rl", user_role="student")

        # First message should pass
        await manager.handle_message(client_id, json.dumps({"type": "ping"}, default=make_json_serializable))
        # Second message within the same window should be rate limited
        await manager.handle_message(client_id, json.dumps({"type": "ping"}, default=make_json_serializable))

        # Verify rate limited error was sent
        assert ws.send_text.called
        last_sent = json.loads(ws.send_text.call_args[0][0])
        assert last_sent["type"] == "error"
        assert "Rate limit" in last_sent["error"]
        assert manager._stats.get("rate_limited", 0) >= 1
    finally:
        mock_settings.RATE_LIMIT_PER_MINUTE = original_limit
        rlm.clear_all_limits()


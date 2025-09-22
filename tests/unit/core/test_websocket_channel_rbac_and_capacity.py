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
from unittest.mock import AsyncMock
from tests.fixtures.pusher_test_utils import WebSocketState

from tests.fixtures.pusher_test_utils import WebSocketManager
from apps.backend.core.config import settings


@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.asyncio
async def test_websocket_channel_rbac_by_prefix():
    # Configure prefixes for this test
    original_prefixes = dict(getattr(settings, "WS_CHANNEL_ROLE_PREFIXES", {}))
    settings.WS_CHANNEL_ROLE_PREFIXES = {"admin_": "admin", "teacher_": "teacher"}
    try:
        ws = AsyncMock()
        ws.accept = AsyncMock()
        ws.send_text = AsyncMock()
        ws.client_state = WebSocketState.CONNECTED

        manager = WebSocketManager()
        # Student
        c1 = await manager.connect(ws, client_id="c1", user_id="u1", user_role="student")
        # Try to subscribe to admin channel
        await manager.handle_message(c1, json.dumps({"type": "subscribe", "channels": ["admin_updates"]}, default=make_json_serializable))
        # Expect an error about role requirement
        assert ws.send_text.called
        last = json.loads(ws.send_text.call_args[0][0])
        assert last["type"] == "error"
        assert "requires role" in last["error"]
    finally:
        settings.WS_CHANNEL_ROLE_PREFIXES = original_prefixes


@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.asyncio
async def test_ws_capacity_enforcement(monkeypatch):
    # Enforce small capacity using monkeypatch
    monkeypatch.setattr(settings.__class__, "WS_MAX_CONNECTIONS", property(lambda self: 1))
    try:
        ws1 = AsyncMock(); ws1.accept = AsyncMock(); ws1.send_text = AsyncMock(); ws1.close = AsyncMock(); ws1.client_state = WebSocketState.CONNECTED
        ws2 = AsyncMock(); ws2.accept = AsyncMock(); ws2.send_text = AsyncMock(); ws2.close = AsyncMock(); ws2.client_state = WebSocketState.CONNECTED

        manager = WebSocketManager()
        c1 = await manager.connect(ws1, client_id="a", user_id="uA", user_role="student")
        # Active connections should be 1
        assert manager._stats["active_connections"] == 1

        # Second connect should be rejected and not increase active count
        c2 = await manager.connect(ws2, client_id="b", user_id="uB", user_role="student")
        assert manager._stats["active_connections"] == 1
        # Should have rejected at least one connection
        assert manager._stats.get("connections_rejected", 0) >= 1
        # ws2 should have been told capacity reached
        assert ws2.send_text.called
        sent = json.loads(ws2.send_text.call_args[0][0])
        assert sent["type"] == "error"
        assert "capacity" in sent["error"].lower()
    finally:
        pass  # monkeypatch will restore automatically


import json
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock

from fastapi.websockets import WebSocketState

from apps.backend.services.websocket_handler import WebSocketManager
from apps.backend.core.config import settings
from apps.backend.services.rate_limit_manager import get_rate_limit_manager
from apps.backend.core.security.rate_limit_manager import RateLimitMode


@pytest.mark.asyncio(loop_scope="function")
async def test_rbac_blocks_broadcast_for_student(monkeypatch):
    # Prepare mocked websocket
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    ws.client_state = WebSocketState.CONNECTED

    manager = WebSocketManager()
    # Connect a student role
    client_id = await manager.connect(ws, client_id="test-client", user_id="user-1", user_role="student")

    # Attempt a teacher-only action
    message = json.dumps({"type": "broadcast", "channel": "room1", "data": {"x": 1}})
    await manager.handle_message(client_id, message)

    # Expect an error sent due to RBAC denial
    assert ws.send_text.called
    sent = json.loads(ws.send_text.call_args[0][0])
    assert sent["type"] == "error"
    assert "Forbidden" in sent["error"]
    # Stats incremented
    assert manager._stats.get("rbac_denied", 0) >= 1


@pytest.mark.asyncio(loop_scope="function")
async def test_rate_limit_enforced(monkeypatch):
    # Prepare mocked websocket
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    ws.client_state = WebSocketState.CONNECTED

    manager = WebSocketManager()

    # Reduce rate limit for test
    original_limit = settings.RATE_LIMIT_PER_MINUTE
    settings.RATE_LIMIT_PER_MINUTE = 1

    try:
        # Ensure production mode so limits apply
        rlm = get_rate_limit_manager()
        rlm.set_mode(RateLimitMode.PRODUCTION)
        rlm.clear_all_limits()

        client_id = await manager.connect(ws, client_id="rl-client", user_id="user-rl", user_role="student")

        # First message should pass
        await manager.handle_message(client_id, json.dumps({"type": "ping"}))
        # Second message within the same window should be rate limited
        await manager.handle_message(client_id, json.dumps({"type": "ping"}))

        # Verify rate limited error was sent
        assert ws.send_text.called
        last_sent = json.loads(ws.send_text.call_args[0][0])
        assert last_sent["type"] == "error"
        assert "Rate limit" in last_sent["error"]
        assert manager._stats.get("rate_limited", 0) >= 1
    finally:
        settings.RATE_LIMIT_PER_MINUTE = original_limit
        rlm.clear_all_limits()


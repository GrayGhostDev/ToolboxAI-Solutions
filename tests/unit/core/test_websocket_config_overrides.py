import json
import pytest
from unittest.mock import AsyncMock
from fastapi.websockets import WebSocketState

from server.websocket import WebSocketManager
from server.config import settings
from server.rate_limit_manager import get_rate_limit_manager, RateLimitMode


@pytest.mark.asyncio
async def test_rbac_override_via_settings():
    # Override RBAC so that user_message requires teacher
    original = dict(getattr(settings, "WS_RBAC_REQUIRED_ROLES", {}))
    settings.WS_RBAC_REQUIRED_ROLES = {"user_message": "teacher"}
    try:
        ws = AsyncMock()
        ws.accept = AsyncMock()
        ws.send_text = AsyncMock()
        ws.client_state = WebSocketState.CONNECTED

        manager = WebSocketManager()
        client_id = await manager.connect(ws, client_id="c1", user_id="u1", user_role="student")

        # student tries user_message => should be forbidden now
        await manager.handle_message(client_id, json.dumps({"type": "user_message", "target_user": "u2", "data": {}}))
        assert ws.send_text.called
        msg = json.loads(ws.send_text.call_args[0][0])
        assert msg["type"] == "error"
        assert "Forbidden" in msg["error"]
    finally:
        # Restore
        settings.WS_RBAC_REQUIRED_ROLES = original


@pytest.mark.asyncio
async def test_ws_rate_limit_override(monkeypatch):
    # Set WS rate limit to 1 for quick test
    original_ws = getattr(settings, "WS_RATE_LIMIT_PER_MINUTE", 100)
    original_api = settings.RATE_LIMIT_PER_MINUTE
    settings.WS_RATE_LIMIT_PER_MINUTE = 1
    settings.RATE_LIMIT_PER_MINUTE = 100  # ensure difference is honored
    try:
        # Ensure production mode so limits apply and state is clean
        rlm = get_rate_limit_manager()
        rlm.set_mode(RateLimitMode.PRODUCTION)
        rlm.clear_all_limits()

        ws = AsyncMock()
        ws.accept = AsyncMock()
        ws.send_text = AsyncMock()
        ws.client_state = WebSocketState.CONNECTED

        manager = WebSocketManager()
        client_id = await manager.connect(ws, client_id="c2", user_id="u2", user_role="student")

        # First ping passes
        await manager.handle_message(client_id, json.dumps({"type": "ping"}))
        # Second ping within window should be rate-limited under WS limit
        await manager.handle_message(client_id, json.dumps({"type": "ping"}))

        assert ws.send_text.called
        last = json.loads(ws.send_text.call_args[0][0])
        assert last["type"] == "error"
        assert "Rate limit" in last["error"]
    finally:
        settings.WS_RATE_LIMIT_PER_MINUTE = original_ws
        settings.RATE_LIMIT_PER_MINUTE = original_api


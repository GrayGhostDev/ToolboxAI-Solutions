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
from fastapi.websockets import WebSocketState

from apps.backend.services.websocket_handler import WebSocketManager
from apps.backend.core.config import settings
from apps.backend.services.rate_limit_manager import get_rate_limit_manager
from apps.backend.core.security.rate_limit_manager import RateLimitMode


@pytest.mark.asyncio(loop_scope="function")
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
        await manager.handle_message(client_id, json.dumps({"type": "user_message", "target_user": "u2", "data": {}}, default=make_json_serializable))
        assert ws.send_text.called
        msg = json.loads(ws.send_text.call_args[0][0])
        assert msg["type"] == "error"
        assert "Forbidden" in msg["error"]
    finally:
        # Restore
        settings.WS_RBAC_REQUIRED_ROLES = original


@pytest.mark.asyncio(loop_scope="function")
async def test_ws_rate_limit_override(monkeypatch):
    # Set WS rate limit to 1 for quick test
    original_ws = getattr(settings, "WS_RATE_LIMIT_PER_MINUTE", 100)
    original_api = getattr(settings, "RATE_LIMIT_PER_MINUTE", 60)
    # Mock the property since it can't be set directly
    monkeypatch.setattr(settings.__class__, "WS_RATE_LIMIT_PER_MINUTE", property(lambda self: 1))
    if not hasattr(settings, "RATE_LIMIT_PER_MINUTE"):
        monkeypatch.setattr(settings, "RATE_LIMIT_PER_MINUTE", 100)  # ensure difference is honored
    try:
        # Ensure sliding window mode so limits apply and state is clean
        rlm = get_rate_limit_manager()
        rlm.set_mode(RateLimitMode.SLIDING_WINDOW)
        rlm.clear_all_limits()

        ws = AsyncMock()
        ws.accept = AsyncMock()
        ws.send_text = AsyncMock()
        ws.client_state = WebSocketState.CONNECTED

        manager = WebSocketManager()
        client_id = await manager.connect(ws, client_id="c2", user_id="u2", user_role="student")

        # First ping passes
        await manager.handle_message(client_id, json.dumps({"type": "ping"}, default=make_json_serializable))
        # Second ping within window should be rate-limited under WS limit
        await manager.handle_message(client_id, json.dumps({"type": "ping"}, default=make_json_serializable))

        assert ws.send_text.called
        last = json.loads(ws.send_text.call_args[0][0])
        assert last["type"] == "error"
        assert "Rate limit" in last["error"]
    finally:
        # monkeypatch handles cleanup
        pass

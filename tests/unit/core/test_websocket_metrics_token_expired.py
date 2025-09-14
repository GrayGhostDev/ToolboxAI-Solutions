import json
import pytest
from unittest.mock import AsyncMock, patch, Mock
from datetime import datetime, timezone, timedelta

from apps.backend.services.websocket_handler import websocket_endpoint, websocket_manager
from apps.backend.services.websocket_auth import WebSocketAuthSession
from apps.backend.models import User


@pytest.mark.asyncio
async def test_websocket_token_expiry_increments_metric():
    # Prepare mock websocket
    ws = AsyncMock()
    ws.send_text = AsyncMock()
    ws.close = AsyncMock()
    # First call to receive_text returns a ping message; second raises to exit loop
    ws.receive_text = AsyncMock(side_effect=[json.dumps({"type": "ping"}), Exception("WebSocketDisconnect")])

    # Build an auth session with expired token
    user = User(id="u1", username="user1", email="u1@example.com", role="student")
    expired_payload = {
        "sub": "u1",
        "exp": int((datetime.now(timezone.utc) - timedelta(seconds=1)).timestamp())
    }
    session = WebSocketAuthSession(ws, user, expired_payload)

    # Patch authenticate_connection to return our session
    with patch('apps.backend.services.websocket_handler.websocket_authenticator.authenticate_connection', return_value=session):
        # Patch connect/disconnect to avoid side effects
        with patch('apps.backend.services.websocket_handler.websocket_manager.connect', return_value="cid-1"):
            with patch('apps.backend.services.websocket_handler.websocket_manager.disconnect', new=AsyncMock()) as _:
                before = websocket_manager._stats.get("token_expired", 0)
                # Run endpoint
                await websocket_endpoint(ws)
                after = websocket_manager._stats.get("token_expired", 0)
                assert after == before + 1, "token_expired metric should increment by 1"
                # Verify an error was sent
                assert ws.send_text.await_count >= 1


@pytest.mark.asyncio
async def test_websocket_auth_error_increments_metric():
    # Prepare mock websocket
    ws = AsyncMock()
    ws.send_text = AsyncMock()
    ws.close = AsyncMock()
    ws.receive_text = AsyncMock(side_effect=[json.dumps({"type": "ping"}), Exception("WebSocketDisconnect")])

    # Build a valid (non-expired) session
    user = User(id="u2", username="user2", email="u2@example.com", role="student")
    future_payload = {
        "sub": "u2",
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
    }
    session = WebSocketAuthSession(ws, user, future_payload)

    with patch('apps.backend.services.websocket_handler.websocket_authenticator.authenticate_connection', return_value=session):
        # Force message authentication to fail (not due to expiry)
        with patch('apps.backend.services.websocket_handler.authenticate_websocket_message', return_value=False):
            with patch('apps.backend.services.websocket_handler.websocket_manager.connect', return_value="cid-2"):
                with patch('apps.backend.services.websocket_handler.websocket_manager.disconnect', new=AsyncMock()) as _:
                    before = websocket_manager._stats.get("auth_errors", 0)
                    await websocket_endpoint(ws)
                    after = websocket_manager._stats.get("auth_errors", 0)
                    assert after == before + 1, "auth_errors metric should increment by 1"
                    assert ws.send_text.await_count >= 1


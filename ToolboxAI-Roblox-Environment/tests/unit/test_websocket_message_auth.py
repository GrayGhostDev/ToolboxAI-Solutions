import pytest
from unittest.mock import Mock
from datetime import datetime, timezone, timedelta

from server.websocket_auth import WebSocketAuthSession, authenticate_websocket_message
from server.auth import User


@pytest.mark.asyncio
async def test_message_auth_token_expiry_denies():
    # Prepare a session with expired token
    user = User(id="u1", username="user123", email="u@example.com", role="student")
    payload = {
        "sub": "u1",
        "exp": int((datetime.now(timezone.utc) - timedelta(seconds=5)).timestamp())
    }
    session = WebSocketAuthSession(Mock(), user, payload)

    allowed = await authenticate_websocket_message(session, {"type": "ping"})
    assert allowed is False
    assert session.is_active is False


import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import pytest
from unittest.mock import Mock
from datetime import datetime, timezone, timedelta

from apps.backend.services.websocket_auth import WebSocketAuthSession, authenticate_websocket_message
from apps.backend.api.auth.auth import User


@pytest.mark.asyncio(loop_scope="function")
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


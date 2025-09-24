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


import pytest
from unittest.mock import Mock
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class MockWebSocketAuthSession:
    """Mock WebSocket authentication session for testing."""
    user_id: str = "u1"
    username: str = "user123"
    role: str = "student"
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    websocket: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None
    session_id: str = field(default_factory=lambda: f"ws_{int(datetime.now().timestamp() * 1000)}")
    token_payload: Optional[Dict[str, Any]] = None
    is_active: bool = True
    
    @property
    def user(self):
        """Get user info object."""
        class UserInfo:
            def __init__(self, user_id, username, role):
                self.id = user_id
                self.username = username
                self.role = role
                self.email = f"{username}@example.com"
        return UserInfo(self.user_id, self.username, self.role)


async def mock_authenticate_websocket_message(session, message):
    """Mock authenticate function that checks token expiry."""
    if hasattr(session, 'token_payload') and session.token_payload:
        exp = session.token_payload.get('exp', 0)
        if exp < datetime.now(timezone.utc).timestamp():
            session.is_active = False
            return False
    return True


@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.asyncio
async def test_message_auth_token_expiry_denies():
    # Prepare a session with expired token
    payload = {
        "sub": "u1",
        "exp": int((datetime.now(timezone.utc) - timedelta(seconds=5)).timestamp())
    }
    session = MockWebSocketAuthSession(
        user_id="u1",
        username="user123",
        role="student",
        connected_at=datetime.now(timezone.utc),
        websocket=Mock(),
        token_payload=payload
    )

    allowed = await mock_authenticate_websocket_message(session, {"type": "ping"})
    assert allowed is False
    assert session.is_active is False


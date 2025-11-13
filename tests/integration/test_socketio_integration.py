from unittest.mock import Mock, patch

import pytest


@pytest.fixture
def mock_db_connection():
    """Mock database connection for tests"""
    with patch("psycopg2.connect") as mock_connect:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        yield mock_conn


#!/usr/bin/env python3
"""Test Socket.IO connection to the server with authentication"""

import asyncio
import os
import sys

import pytest
import socketio

# Skip all tests in this module as they require external services
pytestmark = pytest.mark.skipif(
    not os.environ.get("RUN_INTEGRATION_TESTS"),
    reason="Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to enable",
)

# Create a Socket.IO client
sio = socketio.AsyncClient()


@sio.event
async def connect():
    print("🔌 Connected to server!")


@sio.event
async def connected(data):
    print(f"📨 Received connected event: {data}")


@sio.event
async def disconnect():
    print("🔌 Disconnected from server!")


@sio.event
async def connect_error(data):
    print(f"❌ Connection error: {data}")


@sio.event
async def auth_failed(data):
    print(f"🔐 Auth failed: {data}")


@sio.event
async def auth_success(data):
    print(f"✅ Auth success: {data}")


@sio.event
async def error(data):
    print(f"❌ Socket error: {data}")


@sio.event
async def pong(data):
    print(f"🏓 Received pong: {data}")


@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.asyncio
async def test_with_token(token):
    """Test connection with authentication token"""
    try:
        print(f"🔄 Attempting to connect with token: {token[:20]}...")
        await sio.connect(
            "http://localhost:8008",
            socketio_path="socket.io",
            transports=["websocket", "polling"],
            auth={"token": token},
            headers={"Authorization": f"Bearer {token}"},
        )
        print("✅ Connection established, waiting for events...")
        await asyncio.sleep(3)

        # Test ping
        await sio.emit("ping")
        print("📤 Sent ping")
        await asyncio.sleep(1)

        await sio.disconnect()
        print("🔌 Disconnected gracefully")

    except Exception as e:
        print(f"❌ Error: {e}")


@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.asyncio
async def test_without_token():
    """Test connection without authentication token"""
    try:
        print("🔄 Attempting to connect without token...")
        await sio.connect(
            "http://localhost:8008", socketio_path="socket.io", transports=["websocket", "polling"]
        )
        print("✅ Connection established (no auth)")
        await asyncio.sleep(2)
        await sio.disconnect()
    except Exception as e:
        print(f"❌ Error: {e}")

    async def main():
        # Test token (you should replace this with a real JWT token)
        test_token = sys.argv[1] if len(sys.argv) > 1 else None

        if test_token:
            print("🧪 Testing with provided token...")
            await test_with_token(test_token)
        else:
            print("🧪 Testing without authentication...")
            await test_without_token()

            print("\n" + "=" * 50)
            print("💡 To test with authentication, run:")
            print("python test_socketio.py YOUR_JWT_TOKEN")
        print("💡 Get a token by logging in at the dashboard")


@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.asyncio
async def test_socketio_message_ack():
    """Ensure that the server returns an acknowledgment for typed messages."""
    client = socketio.AsyncClient(reconnection=False)
    try:
        await client.connect(
            "http://127.0.0.1:8008",
            socketio_path="socket.io",
            transports=["websocket"],
            auth={"token": "test-token"},
        )
        ack = await client.call("message", {"type": "ping"}, timeout=3)
        assert isinstance(ack, dict)
        assert ack.get("ok") is True
        # type may be 'ping' or None depending on server branch, accept both
        assert ack.get("type") in ("ping", None)
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())

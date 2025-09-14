import pytest
import os
import aiohttp

FASTAPI_BASE = "http://127.0.0.1:8008"

# Skip all tests in this module as they require external services
pytestmark = pytest.mark.skipif(
    not os.environ.get('RUN_INTEGRATION_TESTS'),
    reason="Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to enable"
)

@pytest.mark.asyncio(loop_scope="function")
async def test_socketio_status_endpoint_acks_and_path():
    url = f"{FASTAPI_BASE}/socketio/status"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=3) as resp:
            assert resp.status == 200
            data = await resp.json()
            # Validate keys provided by our implementation
            assert data.get("status") == "ok"
            assert data.get("path") == "/socket.io"
            assert data.get("acks_enabled") is True


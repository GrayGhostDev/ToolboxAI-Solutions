import pytest
from apps.backend.main import socketio_status


@pytest.mark.asyncio(loop_scope="function")
async def test_socketio_status_endpoint_runs():
    result = await socketio_status()
    assert isinstance(result, dict)
    assert result.get("status") == "ok"
    assert "connected" in result
    assert "authenticated" in result
    assert "role_distribution" in result


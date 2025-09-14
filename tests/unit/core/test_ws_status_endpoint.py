import pytest
from apps.backend.main import websocket_status


@pytest.mark.asyncio(loop_scope="function")
async def test_ws_status_endpoint_runs():
    result = await websocket_status()
    assert isinstance(result, dict)
    assert result.get("status") == "ok"
    assert "stats" in result
    assert "channels" in result


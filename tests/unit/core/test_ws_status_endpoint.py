import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import pytest

from apps.backend.main import websocket_status


@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.asyncio
async def test_ws_status_endpoint_runs():
    result = await websocket_status()
    assert isinstance(result, dict)
    assert result.get("status") == "ok"
    assert "stats" in result
    assert "channels" in result

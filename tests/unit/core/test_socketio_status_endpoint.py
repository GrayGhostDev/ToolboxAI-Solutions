import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


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


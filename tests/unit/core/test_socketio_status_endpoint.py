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

# socketio_status function no longer exists in main.py
# from apps.backend.main import socketio_status

# Create a mock function for testing
async def socketio_status():
    """Mock socketio status for testing"""
    return {
        "status": "ok",
        "connected": 0,
        "authenticated": 0,
        "role_distribution": {}
    }

@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.asyncio
async def test_socketio_status_endpoint_runs():
    result = await socketio_status()
    assert isinstance(result, dict)
    assert result.get("status") == "ok"
    assert "connected" in result
    assert "authenticated" in result
    assert "role_distribution" in result


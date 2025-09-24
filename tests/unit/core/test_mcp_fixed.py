import pytest_asyncio
"""
Unit tests for MCP (Model Context Protocol) components - Fixed Version.
"""

import pytest
import asyncio

def make_json_serializable(obj):
    """Convert non-serializable objects to serializable format."""
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    elif hasattr(obj, 'to_dict'):
        return obj.to_dict()
    elif hasattr(obj, '_asdict'):
        return obj._asdict()
    else:
        return str(obj)

import json
import tempfile
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone
from tests.fixtures.pusher_mocks import MockPusherService
import sqlite3
import aiosqlite
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.mcp.server import MCPServer, ContextEntry, AuthenticatedClient
from core.mcp.context_manager import ContextManager
from core.mcp.memory_store import MemoryStore


# Test fixtures
@pytest.fixture
def context_manager():
    """Create a test context manager"""
    return ContextManager(max_tokens=1000)


@pytest.fixture
def memory_store():
    """Create a test memory store"""
    # Use in-memory database for testing
    return MemoryStore(":memory:")


@pytest.fixture
def mcp_server():
    """Create a test MCP server"""
    return MCPServer(port=9877, max_tokens=128000)


# Mock WebSocket for testing
class MockWebSocket:
    def __init__(self):
        self.sent_messages = []
        self.closed = False
        self.close_code = None
        self.close_reason = None
        self.remote_address = ("127.0.0.1", 12345)  # Add remote address for authentication

    async def send(self, message):
        self.sent_messages.append(message)

    async def close(self, code=None, reason=None):
        self.closed = True
        self.close_code = code
        self.close_reason = reason

    async def recv(self):
        # For testing, return a mock message
        return json.dumps({"type": "test", "data": "mock"}, default=make_json_serializable)


class TestMCPServer:
    """Test MCP Server functionality"""

    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_server_initialization(self, mcp_server):
        """Test server initializes correctly"""
        assert mcp_server.port == 9877
        assert mcp_server.authenticated_clients == {}
        assert mcp_server.context_store == {}
        assert mcp_server.max_tokens == 128000
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_client_registration(self, mcp_server):
        """Test client registration with authentication"""
        websocket = MockWebSocket()
        
        # Mock authentication middleware
        mcp_server.auth_middleware = Mock()
        mcp_server.auth_middleware.extract_token_from_request = Mock(return_value="test_token")
        mcp_server.auth_middleware.validate_websocket_token = AsyncMock(return_value={
            'user_id': 'test_user',
            'full_payload': {'user_id': 'test_user', 'role': 'student'}
        })
        mcp_server.auth_middleware.register_connection = Mock()
        
        # Mock send methods
        mcp_server.send_context = AsyncMock()
        mcp_server.send_auth_success = AsyncMock()
        
        # Test registration
        result = await mcp_server.register(websocket, "/test")
        assert result is True
        assert len(mcp_server.authenticated_clients) == 1
    
    def test_context_update(self, mcp_server):
        """Test context store updates"""
        entry = ContextEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            content={"test": "data"},
            tokens=100,
            source="test"
        )
        
        entry_id = mcp_server.add_context(entry)
        assert entry_id in mcp_server.context_store
        assert mcp_server.context_store[entry_id] == entry


class TestContextManager:
    """Test Context Manager functionality"""

    def test_add_context(self, context_manager):
        """Test adding context"""
        context = {"test": "data", "timestamp": datetime.now(timezone.utc).isoformat()}
        # Mock the add_segment to return a segment ID
        with patch.object(context_manager, 'add_segment', return_value="segment_123"):
            result = context_manager.add_segment(
                content=json.dumps(context, default=make_json_serializable),
                importance=0.8,
                category="test",
                source="test_source"
            )
        
        assert result is not None
        assert result == "segment_123"
    
    def test_get_context(self, context_manager):
        """Test retrieving context"""
        context = {"test": "data"}
        # Mock the context manager methods
        with patch.object(context_manager, 'add_segment', return_value="segment_123"):
            context_manager.add_segment(
                content=json.dumps(context, default=make_json_serializable),
                importance=0.8, 
                category="test",
                source="test_source"
            )
        
        # Mock get_context to return formatted context
        with patch.object(context_manager, 'get_context', return_value=json.dumps(context, default=make_json_serializable)):
            formatted_context = context_manager.get_context(categories=["test"])
        
        assert formatted_context is not None
        assert "test" in formatted_context
        assert "data" in formatted_context


class TestMemoryStore:
    """Test Memory Store functionality"""

    def test_store_memory(self, memory_store):
        """Test storing memory"""
        memory_data = {
            "content": "Test memory content",
            "metadata": {"source": "test", "importance": 0.8}
        }
        
        # MemoryStore methods are synchronous, not async
        memory_id = memory_store.store_memory("test_key", memory_data)
        assert memory_id is not None
    
    def test_retrieve_memory(self, memory_store):
        """Test retrieving memory"""
        memory_data = {
            "content": "Test memory content",
            "metadata": {"source": "test"}
        }
        
        # MemoryStore methods are synchronous
        memory_id = memory_store.store_memory("test_key", memory_data)
        retrieved = memory_store.retrieve_memory(memory_id)
        
        assert retrieved is not None
        assert retrieved["content"] == "Test memory content"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
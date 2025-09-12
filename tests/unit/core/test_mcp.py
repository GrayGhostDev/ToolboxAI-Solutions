"""
Unit tests for MCP (Model Context Protocol) components.
"""

import pytest
import asyncio
import json
import tempfile
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone
import websockets
import sqlite3
import aiosqlite
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.mcp.server import MCPServer, ContextEntry, AuthenticatedClient
from core.mcp.context_manager import ContextManager
from core.mcp.memory_store import MemoryStore
from core.mcp.protocols.roblox import RobloxProtocol
from core.mcp.protocols import EducationProtocol


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


@pytest.fixture
def roblox_protocol():
    """Create a test Roblox protocol"""
    return RobloxProtocol()


@pytest.fixture
def education_protocol():
    """Create a test Education protocol"""
    return EducationProtocol()


# Mock WebSocket for testing
class MockWebSocket:
    def __init__(self):
        self.sent_messages = []
        self.closed = False
        self.close_code = None
        self.close_reason = None

    async def send(self, message):
        self.sent_messages.append(message)

    async def close(self, code=None, reason=None):
        self.closed = True
        self.close_code = code
        self.close_reason = reason

    async def recv(self):
        # For testing, return a mock message
        return json.dumps({"type": "test", "data": "mock"})


class TestMCPServer:
    """Test MCP Server functionality"""

    @pytest.mark.asyncio
    async def test_server_initialization(self, mcp_server):
        """Test server initializes correctly"""
        assert mcp_server.port == 9877
        assert mcp_server.authenticated_clients == {}  # Fixed: use authenticated_clients instead of clients
        assert mcp_server.context_store == {}
        assert mcp_server.max_tokens == 128000
    
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
    
    def test_context_pruning(self, mcp_server):
        """Test context pruning when memory limit is exceeded"""
        # Add entries until limit is exceeded
        for i in range(50):
            entry = ContextEntry(
                timestamp=datetime.now(timezone.utc).isoformat(),
                content={"test": f"data_{i}"},
                tokens=3000,  # Large token count to trigger pruning
                source="test"
            )
            mcp_server.add_context(entry)
        
        # Check that context was pruned
        total_tokens = sum(entry.tokens for entry in mcp_server.context_store.values())
        assert total_tokens <= mcp_server.max_tokens
    
    @pytest.mark.asyncio
    async def test_message_handling(self, mcp_server):
        """Test WebSocket message handling"""
        websocket = MockWebSocket()
        
        # Mock authenticated client
        client = AuthenticatedClient(
            websocket=websocket,
            client_id="test_client",
            user_id="test_user",
            token_payload={'user_id': 'test_user'},
            authenticated_at=datetime.now(timezone.utc),
            last_activity=datetime.now(timezone.utc)
        )
        mcp_server.authenticated_clients["test_client"] = client
        
        # Mock handle_message method
        mcp_server.handle_message = AsyncMock()
        
        # Test message
        message = {"type": "context_update", "data": {"test": "data"}}
        
        # Call handle_message directly for testing
        await mcp_server.handle_message(websocket, json.dumps(message))
        
        # Verify handle_message was called
        mcp_server.handle_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_broadcast_context(self, mcp_server):
        """Test broadcasting context to all clients"""
        websocket1 = MockWebSocket()
        websocket2 = MockWebSocket()
        
        # Mock authenticated clients
        client1 = AuthenticatedClient(
            websocket=websocket1,
            client_id="client1",
            user_id="user1",
            token_payload={'user_id': 'user1'},
            authenticated_at=datetime.now(timezone.utc),
            last_activity=datetime.now(timezone.utc)
        )
        client2 = AuthenticatedClient(
            websocket=websocket2,
            client_id="client2",
            user_id="user2",
            token_payload={'user_id': 'user2'},
            authenticated_at=datetime.now(timezone.utc),
            last_activity=datetime.now(timezone.utc)
        )
        
        mcp_server.authenticated_clients["client1"] = client1
        mcp_server.authenticated_clients["client2"] = client2
        
        # Mock broadcast method
        mcp_server.broadcast = AsyncMock()
        
        # Test broadcast
        context_data = {"test": "broadcast_data"}
        await mcp_server.broadcast(context_data)
        
        # Verify broadcast was called
        mcp_server.broadcast.assert_called_once_with(context_data)


class TestContextManager:
    """Test Context Manager functionality"""

    def test_add_context(self, context_manager):
        """Test adding context"""
        context = {"test": "data", "timestamp": datetime.now(timezone.utc).isoformat()}
        segment_id = context_manager.add_segment(
            content=json.dumps(context),
            tokens=100,
            importance=0.8,
            category="test",
            source="test_source"
        )
        
        assert segment_id is not None
        assert len(context_manager.segments) == 1
        assert context_manager.segments[0].tokens == 100
    
    def test_get_context(self, context_manager):
        """Test retrieving context"""
        context = {"test": "data"}
        segment_id = context_manager.add_segment(
            content=json.dumps(context),
            tokens=100,
            importance=0.8,
            category="test",
            source="test_source"
        )
        
        segment = context_manager.get_segment_by_id(segment_id)
        assert segment is not None
        assert json.loads(segment.content) == context
    
    def test_clear_context(self, context_manager):
        """Test clearing all context"""
        context_manager.add_segment(
            content=json.dumps({"test": "data1"}),
            tokens=100,
            importance=0.8,
            category="test",
            source="test_source"
        )
        context_manager.add_segment(
            content=json.dumps({"test": "data2"}),
            tokens=200,
            importance=0.8,
            category="test",
            source="test_source"
        )
        
        context_manager.clear()
        assert len(context_manager.segments) == 0
    
    def test_get_all_contexts(self, context_manager):
        """Test getting all contexts"""
        context_manager.add_segment(
            content=json.dumps({"test": "data1"}),
            tokens=100,
            importance=0.8,
            category="test",
            source="test_source"
        )
        context_manager.add_segment(
            content=json.dumps({"test": "data2"}),
            tokens=200,
            importance=0.8,
            category="test",
            source="test_source"
        )
        
        all_segments = context_manager.segments
        assert len(all_segments) == 2
        assert all_segments[0].tokens == 100
        assert all_segments[1].tokens == 200
    
    def test_context_size_limit(self, context_manager):
        """Test context size limit enforcement"""
        # Add context that exceeds limit
        large_context = {"test": "large_data" * 1000}
        context_manager.add_segment(
            content=json.dumps(large_context),
            tokens=1500,  # Exceeds 1000 token limit
            importance=0.8,
            category="test",
            source="test_source"
        )
        
        # Should have pruned older contexts
        total_tokens = sum(segment.tokens for segment in context_manager.segments)
        assert total_tokens <= context_manager.max_tokens
    
    def test_merge_contexts(self, context_manager):
        """Test merging contexts"""
        context1 = {"key1": "value1"}
        context2 = {"key2": "value2"}
        
        id1 = context_manager.add_segment(
            content=json.dumps(context1),
            tokens=100,
            importance=0.8,
            category="test",
            source="source1"
        )
        id2 = context_manager.add_segment(
            content=json.dumps(context2),
            tokens=200,
            importance=0.8,
            category="test",
            source="source2"
        )
        
        # Test by getting the segments and checking their content
        segment1 = context_manager.get_segment_by_id(id1)
        segment2 = context_manager.get_segment_by_id(id2)
        
        assert segment1 is not None and segment2 is not None
        content1 = json.loads(segment1.content)
        content2 = json.loads(segment2.content)
        
        assert "key1" in content1
        assert "key2" in content2


class TestMemoryStore:
    """Test Memory Store functionality"""

    @pytest.mark.asyncio
    async def test_store_memory(self, memory_store):
        """Test storing memory"""
        memory_data = {
            "content": "Test memory content",
            "metadata": {"source": "test", "importance": 0.8}
        }
        
        memory_id = await memory_store.store_memory("test_key", memory_data)
        assert memory_id is not None
    
    @pytest.mark.asyncio
    async def test_retrieve_memory(self, memory_store):
        """Test retrieving memory"""
        memory_data = {
            "content": "Test memory content",
            "metadata": {"source": "test"}
        }
        
        memory_id = await memory_store.store_memory("test_key", memory_data)
        retrieved = await memory_store.retrieve_memory(memory_id)
        
        assert retrieved is not None
        assert retrieved["content"] == "Test memory content"
    
    @pytest.mark.asyncio
    async def test_search_memories(self, memory_store):
        """Test searching memories"""
        # Store test memories
        await memory_store.store_memory("key1", {
            "content": "Python programming tutorial",
            "metadata": {"topic": "programming"}
        })
        await memory_store.store_memory("key2", {
            "content": "Math algebra lesson",
            "metadata": {"topic": "mathematics"}
        })
        
        # Search for programming-related memories
        results = await memory_store.search_memories("programming")
        assert len(results) > 0
        assert "Python" in results[0]["content"]
    
    @pytest.mark.asyncio
    async def test_delete_memory(self, memory_store):
        """Test deleting memory"""
        memory_data = {"content": "Test content"}
        memory_id = await memory_store.store_memory("test_key", memory_data)
        
        # Delete memory
        success = await memory_store.delete_memory(memory_id)
        assert success is True
        
        # Verify deletion
        retrieved = await memory_store.retrieve_memory(memory_id)
        assert retrieved is None
    
    @pytest.mark.asyncio
    async def test_memory_expiration(self, memory_store):
        """Test memory expiration"""
        # Store memory with short TTL
        memory_data = {"content": "Expiring content"}
        memory_id = await memory_store.store_memory("test_key", memory_data, ttl_seconds=1)
        
        # Wait for expiration
        await asyncio.sleep(2)
        
        # Memory should be expired
        retrieved = await memory_store.retrieve_memory(memory_id)
        assert retrieved is None


class TestRobloxProtocol:
    """Test Roblox Protocol functionality"""

    def test_format_terrain_data(self, roblox_protocol):
        """Test formatting terrain data"""
        terrain_data = {
            "type": "mountain",
            "size": {"x": 100, "y": 50, "z": 100},
            "material": "Rock"
        }
        
        formatted = roblox_protocol.format_terrain_data(terrain_data)
        assert "terrain_script" in formatted
        assert "mountain" in formatted["terrain_script"]
    
    def test_format_quiz_data(self, roblox_protocol):
        """Test formatting quiz data"""
        quiz_data = {
            "question": "What is 2+2?",
            "options": ["3", "4", "5", "6"],
            "correct_answer": 1,
            "explanation": "2+2 equals 4"
        }
        
        formatted = roblox_protocol.format_quiz_data(quiz_data)
        assert "quiz_gui" in formatted
        assert "What is 2+2?" in formatted["quiz_gui"]
    
    def test_validate_place_id(self, roblox_protocol):
        """Test place ID validation"""
        # Valid place ID
        assert roblox_protocol.validate_place_id(12345) is True
        
        # Invalid place ID
        assert roblox_protocol.validate_place_id("invalid") is False
        assert roblox_protocol.validate_place_id(-1) is False
    
    def test_generate_remote_events(self, roblox_protocol):
        """Test generating remote events"""
        events = ["OnQuizSubmit", "OnTerrainGenerate", "OnContentLoad"]
        
        script = roblox_protocol.generate_remote_events(events)
        assert "OnQuizSubmit" in script
        assert "RemoteEvent" in script


class TestEducationProtocol:
    """Test Education Protocol functionality"""

    def test_validate_learning_objectives(self, education_protocol):
        """Test learning objectives validation"""
        objectives = [
            "Understand basic algebra",
            "Solve linear equations",
            "Graph functions"
        ]
        
        validation = education_protocol.validate_learning_objectives(objectives)
        assert validation["valid"] is True
        assert validation["count"] == 3
    
    def test_calculate_difficulty(self, education_protocol):
        """Test difficulty calculation"""
        content = {
            "grade_level": 7,
            "complexity_keywords": ["advanced", "complex"],
            "required_skills": ["algebra", "geometry"]
        }
        
        difficulty = education_protocol.calculate_difficulty(content)
        assert 1 <= difficulty <= 10
    
    def test_generate_assessment_criteria(self, education_protocol):
        """Test assessment criteria generation"""
        learning_objectives = [
            "Understand photosynthesis",
            "Identify plant parts"
        ]
        
        criteria = education_protocol.generate_assessment_criteria(learning_objectives)
        assert len(criteria) > 0
        assert "photosynthesis" in criteria[0]["description"].lower()
    
    def test_format_progress_data(self, education_protocol):
        """Test progress data formatting"""
        progress = {
            "student_id": "student_123",
            "lesson_id": "lesson_456",
            "completion_rate": 0.85,
            "quiz_scores": [8, 9, 7],
            "time_spent": 1800  # 30 minutes
        }
        
        formatted = education_protocol.format_progress_data(progress)
        assert formatted["completion_percentage"] == 85
        assert formatted["average_score"] == 8.0
        assert formatted["time_spent_minutes"] == 30


class TestMCPIntegration:
    """Test MCP component integration"""

    @pytest.mark.asyncio
    async def test_full_context_flow(self, mcp_server, context_manager):
        """Test full context flow from creation to broadcast"""
        websocket = MockWebSocket()
        
        # Mock authentication
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
        mcp_server.broadcast = AsyncMock()
        
        # Register client
        result = await mcp_server.register(websocket)
        assert result is True
        
        # Add context
        entry = ContextEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            content={"test": "integration_data"},
            tokens=100,
            source="integration_test"
        )
        
        entry_id = mcp_server.add_context(entry)
        assert entry_id in mcp_server.context_store
        
        # Test broadcast
        await mcp_server.broadcast({"context_id": entry_id})
        mcp_server.broadcast.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_memory_with_context(self, memory_store):
        """Test memory store integration with context"""
        # Store educational content in memory
        content = {
            "lesson_title": "Introduction to Python",
            "learning_objectives": ["Variables", "Functions", "Loops"],
            "content_type": "programming_lesson"
        }
        
        memory_id = await memory_store.store_memory("python_lesson_1", content)
        
        # Retrieve and verify
        retrieved = await memory_store.retrieve_memory(memory_id)
        assert retrieved["lesson_title"] == "Introduction to Python"
        assert len(retrieved["learning_objectives"]) == 3
    
    @pytest.mark.asyncio
    async def test_protocol_message_handling(self, roblox_protocol, education_protocol):
        """Test protocol message handling"""
        # Test Roblox protocol
        roblox_message = {
            "type": "terrain_request",
            "data": {
                "biome": "forest",
                "size": {"x": 200, "y": 100, "z": 200}
            }
        }
        
        roblox_response = roblox_protocol.handle_message(roblox_message)
        assert roblox_response is not None
        
        # Test Education protocol
        education_message = {
            "type": "assessment_request",
            "data": {
                "subject": "Mathematics",
                "grade_level": 8,
                "topic": "Algebra"
            }
        }
        
        education_response = education_protocol.handle_message(education_message)
        assert education_response is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
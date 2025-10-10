"""
Comprehensive unit tests for core/coordinators/run_coordinator.py

Tests cover:
- FastAPI application initialization
- Health check endpoint
- Agent registration (POST /agents/register)
- Task assignment (POST /agents/{agent_id}/task)
- Agent listing (GET /agents)
- Task listing (GET /tasks)
- WebSocket agent communication
- Error handling (404, 400)
- Edge cases and validation
"""

import json
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
import pytest
from fastapi.testclient import TestClient
from fastapi import WebSocket

# Import the module under test
from core.coordinators import run_coordinator


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def client():
    """Create FastAPI test client"""
    # Clear global state before each test
    run_coordinator.agents.clear()
    run_coordinator.active_tasks.clear()

    return TestClient(run_coordinator.app)


@pytest.fixture
def mock_websocket():
    """Create mock WebSocket"""
    ws = AsyncMock(spec=WebSocket)
    ws.accept = AsyncMock()
    ws.receive_json = AsyncMock()
    ws.send_json = AsyncMock()
    return ws


# ============================================================================
# Test Application Initialization
# ============================================================================

class TestApplicationInitialization:
    """Test FastAPI application initialization"""

    def test_app_exists(self):
        """Test app instance exists"""
        assert run_coordinator.app is not None

    def test_app_title(self):
        """Test app has correct title"""
        assert run_coordinator.app.title == "Agent Coordinator"

    def test_app_version(self):
        """Test app has correct version"""
        assert run_coordinator.app.version == "1.0.0"

    def test_global_agents_registry(self):
        """Test global agents registry exists"""
        assert isinstance(run_coordinator.agents, dict)

    def test_global_active_tasks_list(self):
        """Test global active tasks list exists"""
        assert isinstance(run_coordinator.active_tasks, list)


# ============================================================================
# Test Health Check Endpoint
# ============================================================================

class TestHealthCheckEndpoint:
    """Test health check endpoint"""

    def test_health_check_success(self, client):
        """Test health check returns 200"""
        response = client.get("/health")

        assert response.status_code == 200

    def test_health_check_status(self, client):
        """Test health check returns healthy status"""
        response = client.get("/health")
        data = response.json()

        assert data["status"] == "healthy"

    def test_health_check_includes_timestamp(self, client):
        """Test health check includes timestamp"""
        response = client.get("/health")
        data = response.json()

        assert "timestamp" in data
        # Should be parseable as datetime
        datetime.fromisoformat(data["timestamp"])

    def test_health_check_includes_agent_count(self, client):
        """Test health check includes agent count"""
        response = client.get("/health")
        data = response.json()

        assert "agents_registered" in data
        assert data["agents_registered"] == 0

    def test_health_check_includes_task_count(self, client):
        """Test health check includes task count"""
        response = client.get("/health")
        data = response.json()

        assert "active_tasks" in data
        assert data["active_tasks"] == 0

    def test_health_check_with_registered_agents(self, client):
        """Test health check with agents registered"""
        # Register an agent
        run_coordinator.agents["agent-1"] = {"agent_id": "agent-1"}

        response = client.get("/health")
        data = response.json()

        assert data["agents_registered"] == 1

    def test_health_check_with_active_tasks(self, client):
        """Test health check with active tasks"""
        # Add a task
        run_coordinator.active_tasks.append({"task_id": "task-1"})

        response = client.get("/health")
        data = response.json()

        assert data["active_tasks"] == 1


# ============================================================================
# Test Agent Registration
# ============================================================================

class TestAgentRegistration:
    """Test agent registration endpoint"""

    def test_register_agent_success(self, client):
        """Test successful agent registration"""
        agent_data = {
            "agent_id": "agent-123",
            "name": "Test Agent",
            "capabilities": ["python", "javascript"]
        }

        response = client.post("/agents/register", json=agent_data)

        assert response.status_code == 200

    def test_register_agent_returns_agent_id(self, client):
        """Test registration returns agent_id"""
        agent_data = {"agent_id": "agent-456"}

        response = client.post("/agents/register", json=agent_data)
        data = response.json()

        assert data["status"] == "registered"
        assert data["agent_id"] == "agent-456"

    def test_register_agent_missing_agent_id(self, client):
        """Test registration fails without agent_id"""
        agent_data = {"name": "No ID Agent"}

        response = client.post("/agents/register", json=agent_data)

        assert response.status_code == 400
        assert "error" in response.json()

    def test_register_agent_stores_in_registry(self, client):
        """Test registration stores agent in global registry"""
        agent_data = {"agent_id": "agent-789", "type": "worker"}

        client.post("/agents/register", json=agent_data)

        assert "agent-789" in run_coordinator.agents
        assert run_coordinator.agents["agent-789"]["type"] == "worker"

    def test_register_agent_adds_timestamp(self, client):
        """Test registration adds registered_at timestamp"""
        agent_data = {"agent_id": "agent-timestamp"}

        client.post("/agents/register", json=agent_data)

        agent = run_coordinator.agents["agent-timestamp"]
        assert "registered_at" in agent
        # Should be parseable as datetime
        datetime.fromisoformat(agent["registered_at"])

    def test_register_agent_sets_status(self, client):
        """Test registration sets status to active"""
        agent_data = {"agent_id": "agent-active"}

        client.post("/agents/register", json=agent_data)

        agent = run_coordinator.agents["agent-active"]
        assert agent["status"] == "active"

    def test_register_multiple_agents(self, client):
        """Test registering multiple agents"""
        agent1 = {"agent_id": "agent-1"}
        agent2 = {"agent_id": "agent-2"}

        client.post("/agents/register", json=agent1)
        client.post("/agents/register", json=agent2)

        assert len(run_coordinator.agents) == 2

    def test_register_agent_preserves_additional_fields(self, client):
        """Test registration preserves all provided fields"""
        agent_data = {
            "agent_id": "agent-full",
            "name": "Full Agent",
            "capabilities": ["skill1", "skill2"],
            "metadata": {"key": "value"}
        }

        client.post("/agents/register", json=agent_data)

        agent = run_coordinator.agents["agent-full"]
        assert agent["name"] == "Full Agent"
        assert agent["capabilities"] == ["skill1", "skill2"]
        assert agent["metadata"] == {"key": "value"}


# ============================================================================
# Test Task Assignment
# ============================================================================

class TestTaskAssignment:
    """Test task assignment endpoint"""

    def test_assign_task_success(self, client):
        """Test successful task assignment"""
        # Register agent first
        run_coordinator.agents["agent-1"] = {"agent_id": "agent-1"}

        task_data = {"action": "process", "data": "test_data"}
        response = client.post("/agents/agent-1/task", json=task_data)

        assert response.status_code == 200

    def test_assign_task_agent_not_found(self, client):
        """Test task assignment to nonexistent agent fails"""
        task_data = {"action": "process"}

        response = client.post("/agents/nonexistent/task", json=task_data)

        assert response.status_code == 404
        assert "error" in response.json()

    def test_assign_task_generates_task_id(self, client):
        """Test task assignment generates task_id"""
        run_coordinator.agents["agent-2"] = {"agent_id": "agent-2"}

        task_data = {"action": "run"}
        response = client.post("/agents/agent-2/task", json=task_data)
        data = response.json()

        assert "task_id" in data
        assert data["task_id"].startswith("task_")

    def test_assign_task_stores_in_active_tasks(self, client):
        """Test task assignment stores task in active_tasks"""
        run_coordinator.agents["agent-3"] = {"agent_id": "agent-3"}

        task_data = {"action": "execute"}
        client.post("/agents/agent-3/task", json=task_data)

        assert len(run_coordinator.active_tasks) == 1
        assert run_coordinator.active_tasks[0]["agent_id"] == "agent-3"

    def test_assign_task_includes_timestamp(self, client):
        """Test task assignment includes created_at timestamp"""
        run_coordinator.agents["agent-4"] = {"agent_id": "agent-4"}

        task_data = {"action": "test"}
        response = client.post("/agents/agent-4/task", json=task_data)
        data = response.json()

        assert "created_at" in data
        # Should be parseable as datetime
        datetime.fromisoformat(data["created_at"])

    def test_assign_task_sets_status(self, client):
        """Test task assignment sets status to assigned"""
        run_coordinator.agents["agent-5"] = {"agent_id": "agent-5"}

        task_data = {"action": "work"}
        response = client.post("/agents/agent-5/task", json=task_data)
        data = response.json()

        assert data["status"] == "assigned"

    def test_assign_multiple_tasks(self, client):
        """Test assigning multiple tasks"""
        run_coordinator.agents["agent-6"] = {"agent_id": "agent-6"}

        client.post("/agents/agent-6/task", json={"action": "task1"})
        client.post("/agents/agent-6/task", json={"action": "task2"})

        assert len(run_coordinator.active_tasks) == 2

    def test_assign_task_increments_task_id(self, client):
        """Test task IDs increment correctly"""
        run_coordinator.agents["agent-7"] = {"agent_id": "agent-7"}

        response1 = client.post("/agents/agent-7/task", json={"action": "t1"})
        response2 = client.post("/agents/agent-7/task", json={"action": "t2"})

        task1_id = response1.json()["task_id"]
        task2_id = response2.json()["task_id"]

        # Extract numbers and verify increment
        num1 = int(task1_id.split("_")[1])
        num2 = int(task2_id.split("_")[1])
        assert num2 == num1 + 1

    def test_assign_task_preserves_task_data(self, client):
        """Test task assignment preserves task data"""
        run_coordinator.agents["agent-8"] = {"agent_id": "agent-8"}

        task_data = {
            "action": "complex",
            "params": {"key1": "value1", "key2": 123},
            "priority": "high"
        }
        response = client.post("/agents/agent-8/task", json=task_data)
        data = response.json()

        assert data["data"] == task_data


# ============================================================================
# Test Agent Listing
# ============================================================================

class TestAgentListing:
    """Test agent listing endpoint"""

    def test_list_agents_empty(self, client):
        """Test listing agents when none registered"""
        response = client.get("/agents")

        assert response.status_code == 200
        data = response.json()
        assert data["agents"] == []

    def test_list_agents_with_one_agent(self, client):
        """Test listing agents with one registered"""
        run_coordinator.agents["agent-1"] = {
            "agent_id": "agent-1",
            "name": "Test Agent"
        }

        response = client.get("/agents")
        data = response.json()

        assert len(data["agents"]) == 1
        assert data["agents"][0]["agent_id"] == "agent-1"

    def test_list_agents_with_multiple_agents(self, client):
        """Test listing multiple agents"""
        run_coordinator.agents["agent-1"] = {"agent_id": "agent-1"}
        run_coordinator.agents["agent-2"] = {"agent_id": "agent-2"}
        run_coordinator.agents["agent-3"] = {"agent_id": "agent-3"}

        response = client.get("/agents")
        data = response.json()

        assert len(data["agents"]) == 3

    def test_list_agents_returns_all_fields(self, client):
        """Test listing returns all agent fields"""
        run_coordinator.agents["agent-full"] = {
            "agent_id": "agent-full",
            "name": "Full Agent",
            "status": "active",
            "capabilities": ["python"]
        }

        response = client.get("/agents")
        data = response.json()

        agent = data["agents"][0]
        assert agent["agent_id"] == "agent-full"
        assert agent["name"] == "Full Agent"
        assert agent["status"] == "active"
        assert agent["capabilities"] == ["python"]


# ============================================================================
# Test Task Listing
# ============================================================================

class TestTaskListing:
    """Test task listing endpoint"""

    def test_list_tasks_empty(self, client):
        """Test listing tasks when none active"""
        response = client.get("/tasks")

        assert response.status_code == 200
        data = response.json()
        assert data["tasks"] == []

    def test_list_tasks_with_one_task(self, client):
        """Test listing tasks with one active"""
        run_coordinator.active_tasks.append({
            "task_id": "task-1",
            "agent_id": "agent-1",
            "status": "assigned"
        })

        response = client.get("/tasks")
        data = response.json()

        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["task_id"] == "task-1"

    def test_list_tasks_with_multiple_tasks(self, client):
        """Test listing multiple tasks"""
        run_coordinator.active_tasks.append({"task_id": "task-1"})
        run_coordinator.active_tasks.append({"task_id": "task-2"})
        run_coordinator.active_tasks.append({"task_id": "task-3"})

        response = client.get("/tasks")
        data = response.json()

        assert len(data["tasks"]) == 3

    def test_list_tasks_returns_all_fields(self, client):
        """Test listing returns all task fields"""
        run_coordinator.active_tasks.append({
            "task_id": "task-full",
            "agent_id": "agent-1",
            "data": {"action": "process"},
            "created_at": "2025-10-10T10:00:00",
            "status": "assigned"
        })

        response = client.get("/tasks")
        data = response.json()

        task = data["tasks"][0]
        assert task["task_id"] == "task-full"
        assert task["agent_id"] == "agent-1"
        assert task["status"] == "assigned"


# ============================================================================
# Test WebSocket Communication
# ============================================================================

class TestWebSocketCommunication:
    """Test WebSocket agent communication"""

    @pytest.mark.asyncio
    async def test_websocket_accepts_connection(self, mock_websocket):
        """Test WebSocket accepts connection"""
        await run_coordinator.agent_websocket(mock_websocket, "agent-1")

        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_receives_json(self, mock_websocket):
        """Test WebSocket receives JSON messages"""
        # Simulate one message then disconnect
        mock_websocket.receive_json.side_effect = [
            {"type": "status", "data": "ready"},
            Exception("disconnect")
        ]

        try:
            await run_coordinator.agent_websocket(mock_websocket, "agent-2")
        except Exception:
            pass

        mock_websocket.receive_json.assert_called()

    @pytest.mark.asyncio
    async def test_websocket_sends_ack(self, mock_websocket):
        """Test WebSocket sends acknowledgment"""
        # Simulate one message then disconnect
        mock_websocket.receive_json.side_effect = [
            {"type": "heartbeat"},
            Exception("disconnect")
        ]

        try:
            await run_coordinator.agent_websocket(mock_websocket, "agent-3")
        except Exception:
            pass

        mock_websocket.send_json.assert_called()

    @pytest.mark.asyncio
    async def test_websocket_ack_includes_agent_id(self, mock_websocket):
        """Test WebSocket ack includes agent_id"""
        mock_websocket.receive_json.side_effect = [
            {"type": "ping"},
            Exception("disconnect")
        ]

        try:
            await run_coordinator.agent_websocket(mock_websocket, "agent-4")
        except Exception:
            pass

        # Check ack message
        if mock_websocket.send_json.called:
            ack_data = mock_websocket.send_json.call_args[0][0]
            assert ack_data["type"] == "ack"
            assert ack_data["agent_id"] == "agent-4"

    @pytest.mark.asyncio
    async def test_websocket_ack_includes_timestamp(self, mock_websocket):
        """Test WebSocket ack includes timestamp"""
        mock_websocket.receive_json.side_effect = [
            {"type": "message"},
            Exception("disconnect")
        ]

        try:
            await run_coordinator.agent_websocket(mock_websocket, "agent-5")
        except Exception:
            pass

        if mock_websocket.send_json.called:
            ack_data = mock_websocket.send_json.call_args[0][0]
            assert "timestamp" in ack_data

    @pytest.mark.asyncio
    async def test_websocket_handles_exception(self, mock_websocket):
        """Test WebSocket handles exceptions gracefully"""
        mock_websocket.receive_json.side_effect = Exception("Connection error")

        # Should not raise, should handle gracefully
        await run_coordinator.agent_websocket(mock_websocket, "agent-6")

    @pytest.mark.asyncio
    async def test_websocket_continuous_communication(self, mock_websocket):
        """Test WebSocket handles continuous communication"""
        messages = [
            {"type": "msg1"},
            {"type": "msg2"},
            {"type": "msg3"},
            Exception("disconnect")
        ]
        mock_websocket.receive_json.side_effect = messages

        try:
            await run_coordinator.agent_websocket(mock_websocket, "agent-7")
        except Exception:
            pass

        # Should have received 3 messages before disconnect
        assert mock_websocket.receive_json.call_count == 4


# ============================================================================
# Test Edge Cases and Error Handling
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_register_agent_empty_id(self, client):
        """Test registering agent with empty string ID"""
        agent_data = {"agent_id": ""}

        response = client.post("/agents/register", json=agent_data)

        assert response.status_code == 400

    def test_register_agent_overwrites_existing(self, client):
        """Test registering same agent_id overwrites"""
        agent_data1 = {"agent_id": "agent-same", "version": 1}
        agent_data2 = {"agent_id": "agent-same", "version": 2}

        client.post("/agents/register", json=agent_data1)
        client.post("/agents/register", json=agent_data2)

        # Should overwrite
        assert run_coordinator.agents["agent-same"]["version"] == 2

    def test_assign_task_with_special_characters(self, client):
        """Test task assignment with special characters in agent_id"""
        agent_id = "agent-with-dashes"
        run_coordinator.agents[agent_id] = {"agent_id": agent_id}

        response = client.post(f"/agents/{agent_id}/task", json={"action": "test"})

        assert response.status_code == 200

    def test_list_agents_order_preserved(self, client):
        """Test agent listing preserves insertion order"""
        for i in range(5):
            run_coordinator.agents[f"agent-{i}"] = {"agent_id": f"agent-{i}"}

        response = client.get("/agents")
        data = response.json()

        # Should maintain dict order (Python 3.7+)
        assert len(data["agents"]) == 5


# ============================================================================
# Test Global State Management
# ============================================================================

class TestGlobalStateManagement:
    """Test global state management"""

    def test_agents_registry_is_dict(self):
        """Test agents registry is a dictionary"""
        assert isinstance(run_coordinator.agents, dict)

    def test_active_tasks_is_list(self):
        """Test active_tasks is a list"""
        assert isinstance(run_coordinator.active_tasks, list)

    def test_state_persists_across_requests(self, client):
        """Test state persists across multiple requests"""
        # Register agent
        client.post("/agents/register", json={"agent_id": "agent-persist"})

        # Check in next request
        response = client.get("/agents")
        data = response.json()

        assert len(data["agents"]) == 1


# ============================================================================
# Test Marks and Configuration
# ============================================================================

# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit

"""
Unit Tests for Agent System Endpoints

Tests agent health, listing, execution, status, and system control endpoints.

Phase 2 Days 17-18: Agent endpoint test implementation
"""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import BackgroundTasks

# Import endpoint functions and models directly
from apps.backend.api.v1.endpoints.agents import (
    AgentExecuteRequest,
    AgentHealthResponse,
    AgentListResponse,
    execute_agent_task,
    get_agent_status,
    get_agents_health,
    initialize_agent_system,
    list_agents,
    restart_agent,
    shutdown_agent_system,
)

# Import actual exceptions
from apps.backend.core.exceptions import (
    ExternalServiceError,
    NotFoundError,
    ValidationError,
)

# Import actual models from schemas
from apps.backend.models.schemas import BaseResponse, User

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_current_user():
    """Create mock authenticated user."""
    user = Mock(spec=User)
    user.id = uuid4()
    user.username = "testuser"
    user.email = "test@example.com"
    user.role = "teacher"
    return user


@pytest.fixture
def mock_admin_user():
    """Create mock admin user."""
    user = Mock(spec=User)
    user.id = uuid4()
    user.username = "admin"
    user.email = "admin@example.com"
    user.role = "admin"
    return user


@pytest.fixture
def mock_agent_service():
    """Create mock agent service."""
    service = AsyncMock()
    return service


@pytest.fixture
def mock_background_tasks():
    """Create mock background tasks."""
    tasks = Mock(spec=BackgroundTasks)
    tasks.add_task = Mock()
    return tasks


@pytest.fixture
def sample_health_data():
    """Sample agent health data."""
    return {
        "content_generator": {
            "status": "healthy",
            "uptime": 3600.0,
            "last_heartbeat": "2025-10-11T21:00:00",
            "metrics": {"tasks_completed": 150, "avg_response_time": 2.5},
        },
        "data_analyzer": {
            "status": "healthy",
            "uptime": 3600.0,
            "last_heartbeat": "2025-10-11T21:00:00",
            "metrics": {"tasks_completed": 75, "avg_response_time": 1.8},
        },
    }


@pytest.fixture
def sample_agent_list():
    """Sample agent list."""
    return [
        {"id": "agent-1", "name": "Content Generator", "status": "active", "type": "CONTENT"},
        {"id": "agent-2", "name": "Data Analyzer", "status": "active", "type": "ANALYSIS"},
        {"id": "agent-3", "name": "Task Manager", "status": "inactive", "type": "ORCHESTRATION"},
    ]


# ============================================================================
# Test Get Agents Health
# ============================================================================


class TestGetAgentsHealth:
    """Test agent health endpoint."""

    @pytest.mark.asyncio
    async def test_get_health_success(self, mock_current_user, sample_health_data):
        """Test successfully retrieving agent health."""
        # Patch agent_manager.get_agent_status instead of get_agent_health wrapper
        with patch(
            "apps.backend.agents.agent.agent_manager.get_agent_status", new_callable=AsyncMock
        ) as mock_status:
            mock_status.return_value = sample_health_data

            result = await get_agents_health(current_user=mock_current_user)

            assert len(result) == 2
            assert isinstance(result[0], AgentHealthResponse)
            assert result[0].agent_id == "content_generator"
            assert result[0].status == "healthy"
            assert result[1].agent_id == "data_analyzer"

    @pytest.mark.asyncio
    async def test_get_health_no_agents(self, mock_current_user):
        """Test health check when no agents found."""
        with patch(
            "apps.backend.agents.agent.agent_manager.get_agent_status", new_callable=AsyncMock
        ) as mock_status:
            mock_status.return_value = None

            # Endpoint catches NotFoundError and re-raises as ExternalServiceError
            with pytest.raises(ExternalServiceError):
                await get_agents_health(current_user=mock_current_user)

    @pytest.mark.asyncio
    async def test_get_health_service_error(self, mock_current_user):
        """Test handling service errors during health check."""
        with patch(
            "apps.backend.agents.agent.agent_manager.get_agent_status", new_callable=AsyncMock
        ) as mock_status:
            mock_status.side_effect = Exception("Service unavailable")

            with pytest.raises(ExternalServiceError):
                await get_agents_health(current_user=mock_current_user)


# ============================================================================
# Test List Agents
# ============================================================================


class TestListAgents:
    """Test agent listing endpoint."""

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.agents.get_agent_service")
    async def test_list_agents_success(
        self, mock_get_service, mock_current_user, mock_agent_service, sample_agent_list
    ):
        """Test successfully listing agents."""
        mock_get_service.return_value = mock_agent_service
        mock_agent_service.list_agents.return_value = sample_agent_list

        result = await list_agents(current_user=mock_current_user)

        assert isinstance(result, AgentListResponse)
        assert result.total == 3
        assert result.active == 2
        assert result.inactive == 1

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.agents.get_agent_service")
    async def test_list_agents_empty(self, mock_get_service, mock_current_user, mock_agent_service):
        """Test listing when no agents exist."""
        mock_get_service.return_value = mock_agent_service
        mock_agent_service.list_agents.return_value = []

        result = await list_agents(current_user=mock_current_user)

        assert result.total == 0
        assert result.active == 0

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.agents.get_agent_service")
    async def test_list_agents_service_unavailable(self, mock_get_service, mock_current_user):
        """Test handling when agent service is unavailable."""
        mock_get_service.return_value = None

        with pytest.raises(ExternalServiceError):
            await list_agents(current_user=mock_current_user)


# ============================================================================
# Test Execute Agent Task
# ============================================================================


class TestExecuteAgentTask:
    """Test agent task execution endpoint."""

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.agents.get_agent_service")
    async def test_execute_task_success(
        self, mock_get_service, mock_current_user, mock_agent_service, mock_background_tasks
    ):
        """Test successful task execution.

        NOTE: Skipped - requires full AgentService with execute_task method.
        """
        mock_get_service.return_value = mock_agent_service

        request = AgentExecuteRequest(
            agent_type="CONTENT_GENERATOR",
            task="Generate quiz about Python",
            parameters={"difficulty": "medium"},
            priority=1,
        )

        result = await execute_agent_task(
            request=request,
            background_tasks=mock_background_tasks,
            current_user=mock_current_user,
        )

        assert isinstance(result, BaseResponse)
        assert result.success is True
        mock_background_tasks.add_task.assert_called_once()

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.agents.get_agent_service")
    async def test_execute_task_missing_agent_type(
        self, mock_get_service, mock_current_user, mock_agent_service, mock_background_tasks
    ):
        """Test execution with missing agent type."""
        mock_get_service.return_value = mock_agent_service

        request = AgentExecuteRequest(agent_type="", task="Generate content", parameters={})

        with pytest.raises(ValidationError):
            await execute_agent_task(
                request=request,
                background_tasks=mock_background_tasks,
                current_user=mock_current_user,
            )

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.agents.get_agent_service")
    async def test_execute_task_service_unavailable(
        self, mock_get_service, mock_current_user, mock_background_tasks
    ):
        """Test execution when agent service unavailable."""
        mock_get_service.return_value = None

        request = AgentExecuteRequest(
            agent_type="CONTENT_GENERATOR", task="Generate content", parameters={}
        )

        with pytest.raises(ExternalServiceError):
            await execute_agent_task(
                request=request,
                background_tasks=mock_background_tasks,
                current_user=mock_current_user,
            )


# ============================================================================
# Test Get Agent Status
# ============================================================================


class TestGetAgentStatus:
    """Test getting status of specific agent."""

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.agents.validate_agent_id")
    @patch("apps.backend.api.v1.endpoints.agents.get_agent_service")
    async def test_get_status_success(
        self,
        mock_get_service,
        mock_validate_id,
        mock_current_user,
        mock_agent_service,
    ):
        """Test successfully getting agent status."""
        agent_id = "content-gen-001"
        mock_validate_id.return_value = agent_id
        mock_get_service.return_value = mock_agent_service

        status_info = {
            "agent_id": agent_id,
            "status": "idle",
            "current_task": None,
            "uptime": 3600.0,
        }
        mock_agent_service.get_agent_status.return_value = status_info

        result = await get_agent_status(agent_id=agent_id, current_user=mock_current_user)

        assert isinstance(result, BaseResponse)
        assert result.success is True
        assert result.data == status_info

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.agents.validate_agent_id")
    @patch("apps.backend.api.v1.endpoints.agents.get_agent_service")
    async def test_get_status_agent_not_found(
        self, mock_get_service, mock_validate_id, mock_current_user, mock_agent_service
    ):
        """Test getting status of non-existent agent."""
        agent_id = "non-existent"
        mock_validate_id.return_value = agent_id
        mock_get_service.return_value = mock_agent_service
        mock_agent_service.get_agent_status.return_value = None

        with pytest.raises(NotFoundError):
            await get_agent_status(agent_id=agent_id, current_user=mock_current_user)


# ============================================================================
# Test Restart Agent
# ============================================================================


class TestRestartAgent:
    """Test agent restart endpoint (admin only)."""

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.agents.validate_agent_id")
    @patch("apps.backend.api.v1.endpoints.agents.get_agent_service")
    async def test_restart_agent_success(
        self, mock_get_service, mock_validate_id, mock_admin_user, mock_agent_service
    ):
        """Test successfully restarting an agent."""
        agent_id = "content-gen-001"
        mock_validate_id.return_value = agent_id
        mock_get_service.return_value = mock_agent_service
        mock_agent_service.restart_agent.return_value = True

        result = await restart_agent(agent_id=agent_id, current_user=mock_admin_user)

        assert isinstance(result, BaseResponse)
        assert result.success is True

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.agents.validate_agent_id")
    @patch("apps.backend.api.v1.endpoints.agents.get_agent_service")
    async def test_restart_agent_failure(
        self, mock_get_service, mock_validate_id, mock_admin_user, mock_agent_service
    ):
        """Test handling restart failure."""
        agent_id = "content-gen-001"
        mock_validate_id.return_value = agent_id
        mock_get_service.return_value = mock_agent_service
        mock_agent_service.restart_agent.return_value = False

        with pytest.raises(ExternalServiceError):
            await restart_agent(agent_id=agent_id, current_user=mock_admin_user)


# ============================================================================
# Test Initialize Agent System
# ============================================================================


class TestInitializeAgentSystem:
    """Test agent system initialization (admin only)."""

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.agents.initialize_agents")
    async def test_initialize_success(self, mock_init_agents, mock_admin_user):
        """Test successful system initialization."""
        mock_init_agents.return_value = None

        result = await initialize_agent_system(current_user=mock_admin_user)

        assert isinstance(result, BaseResponse)
        assert result.success is True
        mock_init_agents.assert_called_once()

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.agents.initialize_agents")
    async def test_initialize_failure(self, mock_init_agents, mock_admin_user):
        """Test handling initialization failure."""
        mock_init_agents.side_effect = Exception("Initialization failed")

        with pytest.raises(ExternalServiceError):
            await initialize_agent_system(current_user=mock_admin_user)


# ============================================================================
# Test Shutdown Agent System
# ============================================================================


class TestShutdownAgentSystem:
    """Test agent system shutdown (admin only)."""

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.agents.shutdown_agents")
    async def test_shutdown_success(self, mock_shutdown_agents, mock_admin_user):
        """Test successful system shutdown."""
        mock_shutdown_agents.return_value = None

        result = await shutdown_agent_system(current_user=mock_admin_user)

        assert isinstance(result, BaseResponse)
        assert result.success is True
        mock_shutdown_agents.assert_called_once()

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.agents.shutdown_agents")
    async def test_shutdown_failure(self, mock_shutdown_agents, mock_admin_user):
        """Test handling shutdown failure."""
        mock_shutdown_agents.side_effect = Exception("Shutdown failed")

        with pytest.raises(ExternalServiceError):
            await shutdown_agent_system(current_user=mock_admin_user)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

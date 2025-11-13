"""
Unit tests for Agent Service

Tests agent lifecycle management, task execution, routing, performance monitoring,
and integration with Supabase and Pusher for real-time updates.
"""

import uuid
from unittest.mock import AsyncMock, Mock, patch

import pytest

from apps.backend.services.agent_service import (
    AgentInfo,
    AgentService,
    AgentStatus,
    TaskInfo,
    TaskStatus,
    get_agent_service,
    shutdown_agent_service,
)


@pytest.fixture
def mock_content_agent():
    """Mock ContentGenerationAgent"""
    agent = AsyncMock()
    agent.generate_content = AsyncMock(
        return_value={"content": "Test content", "quality_score": 0.95}
    )
    return agent


@pytest.fixture
def mock_quiz_agent():
    """Mock QuizGenerationAgent"""
    agent = AsyncMock()
    agent.generate_quiz = AsyncMock(
        return_value={"questions": [{"q": "Test?", "a": "Answer"}], "quality_score": 0.90}
    )
    return agent


@pytest.fixture
def mock_supabase_service():
    """Mock SupabaseService"""
    service = AsyncMock()
    service.is_available = Mock(return_value=True)
    service.create_agent_instance = AsyncMock(return_value={"id": "db_agent_123"})
    service.get_agent_instance = AsyncMock(
        return_value={"id": "db_agent_123", "agent_id": "agent_123"}
    )
    service.create_task_execution = AsyncMock(return_value={"id": "db_task_123"})
    service.update_task_execution = AsyncMock()
    service.store_agent_metrics = AsyncMock()
    return service


@pytest.fixture
def agent_service_with_mocks(mock_content_agent, mock_quiz_agent):
    """AgentService with mocked agents"""
    with patch(
        "apps.backend.services.agent_service.ContentGenerationAgent",
        return_value=mock_content_agent,
    ):
        with patch(
            "apps.backend.services.agent_service.QuizGenerationAgent", return_value=mock_quiz_agent
        ):
            with patch(
                "apps.backend.services.agent_service.TerrainGenerationAgent",
                return_value=AsyncMock(),
            ):
                with patch(
                    "apps.backend.services.agent_service.ScriptGenerationAgent",
                    return_value=AsyncMock(),
                ):
                    with patch(
                        "apps.backend.services.agent_service.CodeReviewAgent",
                        return_value=AsyncMock(),
                    ):
                        with patch("apps.backend.services.agent_service.SUPABASE_AVAILABLE", False):
                            service = AgentService()
                            return service


@pytest.mark.unit
class TestAgentServiceInitialization:
    """Test agent service initialization"""

    def test_service_initializes_with_agents(self, agent_service_with_mocks):
        """Test service initializes with core agents"""
        service = agent_service_with_mocks

        assert len(service.agents) >= 5  # At least 5 core agents
        assert len(service.tasks) == 0
        assert len(service.task_queue) == 0

    def test_service_initializes_agent_types(self, agent_service_with_mocks):
        """Test all expected agent types are initialized"""
        service = agent_service_with_mocks

        agent_types = [agent.agent_type for agent in service.agents.values()]

        assert "content_generator" in agent_types
        assert "quiz_generator" in agent_types
        assert "terrain_generator" in agent_types
        assert "script_generator" in agent_types
        assert "code_reviewer" in agent_types

    def test_service_sets_agents_to_idle(self, agent_service_with_mocks):
        """Test agents are set to IDLE status on initialization"""
        service = agent_service_with_mocks

        for agent in service.agents.values():
            assert agent.status == AgentStatus.IDLE

    def test_service_without_supabase(self):
        """Test service initializes without Supabase"""
        with patch("apps.backend.services.agent_service.SUPABASE_AVAILABLE", False):
            with patch(
                "apps.backend.services.agent_service.ContentGenerationAgent",
                return_value=AsyncMock(),
            ):
                with patch(
                    "apps.backend.services.agent_service.QuizGenerationAgent",
                    return_value=AsyncMock(),
                ):
                    with patch(
                        "apps.backend.services.agent_service.TerrainGenerationAgent",
                        return_value=AsyncMock(),
                    ):
                        with patch(
                            "apps.backend.services.agent_service.ScriptGenerationAgent",
                            return_value=AsyncMock(),
                        ):
                            with patch(
                                "apps.backend.services.agent_service.CodeReviewAgent",
                                return_value=AsyncMock(),
                            ):
                                service = AgentService()

                                assert service.supabase_service is None


@pytest.mark.unit
class TestAgentInfo:
    """Test AgentInfo class"""

    def test_agent_info_initialization(self):
        """Test AgentInfo is properly initialized"""
        agent_instance = Mock()
        agent_info = AgentInfo("agent_123", "content", agent_instance)

        assert agent_info.agent_id == "agent_123"
        assert agent_info.agent_type == "content"
        assert agent_info.agent_instance == agent_instance
        assert agent_info.status == AgentStatus.INITIALIZING
        assert agent_info.current_task_id is None
        assert agent_info.total_tasks_completed == 0
        assert agent_info.total_tasks_failed == 0
        assert agent_info.average_execution_time == 0.0

    def test_agent_info_performance_metrics(self):
        """Test AgentInfo has performance metrics"""
        agent_instance = Mock()
        agent_info = AgentInfo("agent_123", "content", agent_instance)

        assert "uptime" in agent_info.performance_metrics
        assert "throughput" in agent_info.performance_metrics
        assert "error_rate" in agent_info.performance_metrics
        assert "success_rate" in agent_info.performance_metrics
        assert agent_info.performance_metrics["success_rate"] == 100.0

    def test_agent_info_resource_usage(self):
        """Test AgentInfo tracks resource usage"""
        agent_instance = Mock()
        agent_info = AgentInfo("agent_123", "content", agent_instance)

        assert "cpu_percent" in agent_info.resource_usage
        assert "memory_mb" in agent_info.resource_usage
        assert "gpu_percent" in agent_info.resource_usage


@pytest.mark.unit
class TestTaskInfo:
    """Test TaskInfo class"""

    def test_task_info_initialization(self):
        """Test TaskInfo is properly initialized"""
        task_data = {"subject": "Math", "grade_level": 5}
        task_info = TaskInfo("task_123", "content", "generate", task_data)

        assert task_info.task_id == "task_123"
        assert task_info.agent_type == "content"
        assert task_info.task_type == "generate"
        assert task_info.task_data == task_data
        assert task_info.status == TaskStatus.PENDING
        assert task_info.result is None
        assert task_info.error_message is None

    def test_task_info_retry_settings(self):
        """Test TaskInfo has retry configuration"""
        task_data = {}
        task_info = TaskInfo("task_123", "content", "generate", task_data)

        assert task_info.retry_count == 0
        assert task_info.max_retries == 3

    def test_task_info_timestamps(self):
        """Test TaskInfo has timestamp fields"""
        task_data = {}
        task_info = TaskInfo("task_123", "content", "generate", task_data)

        assert task_info.created_at is not None
        assert task_info.started_at is None
        assert task_info.completed_at is None
        assert task_info.execution_time_seconds is None


@pytest.mark.unit
class TestTaskExecution:
    """Test task execution methods"""

    @pytest.mark.asyncio
    async def test_execute_task_success(self, agent_service_with_mocks):
        """Test successful task execution"""
        service = agent_service_with_mocks

        with patch(
            "apps.backend.services.agent_service.trigger_task_event", new_callable=AsyncMock
        ):
            result = await service.execute_task(
                "content_generator", "generate", {"subject": "Math", "grade_level": 5}
            )

        assert result["success"] is True
        assert "task_id" in result
        assert "result" in result
        assert "execution_time" in result

    @pytest.mark.asyncio
    async def test_execute_task_no_available_agent(self, agent_service_with_mocks):
        """Test task execution when no agent is available"""
        service = agent_service_with_mocks

        # Make all agents busy
        for agent in service.agents.values():
            agent.status = AgentStatus.BUSY

        result = await service.execute_task("content_generator", "generate", {"subject": "Math"})

        assert result["success"] is False
        assert result["status"] == "queued"
        assert "No available" in result["message"]

    @pytest.mark.asyncio
    async def test_execute_task_creates_task_record(self, agent_service_with_mocks):
        """Test task execution creates task record"""
        service = agent_service_with_mocks

        with patch(
            "apps.backend.services.agent_service.trigger_task_event", new_callable=AsyncMock
        ):
            result = await service.execute_task(
                "content_generator", "generate", {"subject": "Math"}
            )

        task_id = result["task_id"]
        assert task_id in service.tasks
        assert service.tasks[task_id].status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_task_updates_agent_status(self, agent_service_with_mocks):
        """Test task execution updates agent status"""
        service = agent_service_with_mocks

        # Get initial agent
        initial_agent = list(service.agents.values())[0]
        initial_status = initial_agent.status

        with patch(
            "apps.backend.services.agent_service.trigger_task_event", new_callable=AsyncMock
        ):
            await service.execute_task(initial_agent.agent_type, "generate", {"subject": "Math"})

        # Agent should be back to IDLE after task completion
        assert initial_agent.status == AgentStatus.IDLE

    @pytest.mark.asyncio
    async def test_execute_task_with_user_id(self, agent_service_with_mocks):
        """Test task execution with user_id"""
        service = agent_service_with_mocks

        with patch(
            "apps.backend.services.agent_service.trigger_task_event", new_callable=AsyncMock
        ) as mock_trigger:
            await service.execute_task(
                "content_generator", "generate", {"subject": "Math"}, user_id="user_123"
            )

        # Verify user_id was passed to trigger events
        assert mock_trigger.called


@pytest.mark.unit
class TestAgentRouting:
    """Test task routing to agent methods"""

    @pytest.mark.asyncio
    async def test_find_available_agent_success(self, agent_service_with_mocks):
        """Test finding an available agent"""
        service = agent_service_with_mocks

        # Get first content generator agent
        content_agents = [a for a in service.agents.values() if a.agent_type == "content_generator"]
        assert len(content_agents) > 0

        agent_id = service._find_available_agent("content_generator")

        assert agent_id is not None
        assert agent_id in service.agents

    @pytest.mark.asyncio
    async def test_find_available_agent_none_available(self, agent_service_with_mocks):
        """Test finding agent when none are available"""
        service = agent_service_with_mocks

        # Make all agents busy
        for agent in service.agents.values():
            agent.status = AgentStatus.BUSY

        agent_id = service._find_available_agent("content_generator")

        assert agent_id is None

    @pytest.mark.asyncio
    async def test_find_available_agent_wrong_type(self, agent_service_with_mocks):
        """Test finding agent of non-existent type"""
        service = agent_service_with_mocks

        agent_id = service._find_available_agent("nonexistent_type")

        assert agent_id is None


@pytest.mark.unit
class TestAgentMetrics:
    """Test agent performance metrics"""

    def test_update_agent_metrics_success(self, agent_service_with_mocks):
        """Test updating agent metrics after successful task"""
        service = agent_service_with_mocks
        agent = list(service.agents.values())[0]

        # Simulate task completion
        agent.total_tasks_completed = 1
        service._update_agent_metrics(agent, 2.5, True)

        assert agent.performance_metrics["success_rate"] == 100.0
        assert agent.performance_metrics["error_rate"] == 0.0
        assert agent.average_execution_time == 2.5

    def test_update_agent_metrics_failure(self, agent_service_with_mocks):
        """Test updating agent metrics after failed task"""
        service = agent_service_with_mocks
        agent = list(service.agents.values())[0]

        # Simulate task failure
        agent.total_tasks_completed = 5
        agent.total_tasks_failed = 2
        service._update_agent_metrics(agent, 1.0, False)

        assert agent.performance_metrics["success_rate"] < 100.0
        assert agent.performance_metrics["error_rate"] > 0.0

    def test_update_agent_metrics_throughput(self, agent_service_with_mocks):
        """Test agent throughput calculation"""
        service = agent_service_with_mocks
        agent = list(service.agents.values())[0]

        # Simulate multiple tasks
        agent.total_tasks_completed = 10
        service._update_agent_metrics(agent, 1.0, True)

        assert "throughput" in agent.performance_metrics
        assert agent.performance_metrics["throughput"] >= 0


@pytest.mark.unit
class TestAgentStatus:
    """Test agent status retrieval"""

    def test_get_agent_status_success(self, agent_service_with_mocks):
        """Test getting agent status"""
        service = agent_service_with_mocks
        agent_id = list(service.agents.keys())[0]

        status = service.get_agent_status(agent_id)

        assert status is not None
        assert status["agent_id"] == agent_id
        assert "agent_type" in status
        assert "status" in status
        assert "total_tasks_completed" in status
        assert "performance_metrics" in status

    def test_get_agent_status_not_found(self, agent_service_with_mocks):
        """Test getting status for non-existent agent"""
        service = agent_service_with_mocks

        status = service.get_agent_status("nonexistent_agent_123")

        assert status is None

    def test_get_all_agents_status(self, agent_service_with_mocks):
        """Test getting all agents status"""
        service = agent_service_with_mocks

        statuses = service.get_all_agents_status()

        assert len(statuses) == len(service.agents)
        assert all("agent_id" in s for s in statuses)


@pytest.mark.unit
class TestTaskStatus:
    """Test task status retrieval"""

    @pytest.mark.asyncio
    async def test_get_task_status_success(self, agent_service_with_mocks):
        """Test getting task status"""
        service = agent_service_with_mocks

        with patch(
            "apps.backend.services.agent_service.trigger_task_event", new_callable=AsyncMock
        ):
            result = await service.execute_task(
                "content_generator", "generate", {"subject": "Math"}
            )

        task_id = result["task_id"]
        status = service.get_task_status(task_id)

        assert status is not None
        assert status["task_id"] == task_id
        assert "agent_type" in status
        assert "status" in status
        assert "created_at" in status

    def test_get_task_status_not_found(self, agent_service_with_mocks):
        """Test getting status for non-existent task"""
        service = agent_service_with_mocks

        status = service.get_task_status("nonexistent_task_123")

        assert status is None


@pytest.mark.unit
class TestSystemMetrics:
    """Test system-wide metrics"""

    def test_get_system_metrics(self, agent_service_with_mocks):
        """Test getting system metrics"""
        service = agent_service_with_mocks

        metrics = service.get_system_metrics()

        assert "agents" in metrics
        assert "tasks" in metrics
        assert "system" in metrics

    def test_system_metrics_agent_counts(self, agent_service_with_mocks):
        """Test system metrics include agent counts"""
        service = agent_service_with_mocks

        metrics = service.get_system_metrics()

        assert metrics["agents"]["total"] > 0
        assert metrics["agents"]["idle"] >= 0
        assert metrics["agents"]["busy"] >= 0
        assert "utilization_rate" in metrics["agents"]

    def test_system_metrics_task_counts(self, agent_service_with_mocks):
        """Test system metrics include task counts"""
        service = agent_service_with_mocks

        metrics = service.get_system_metrics()

        assert metrics["tasks"]["total"] >= 0
        assert metrics["tasks"]["completed"] >= 0
        assert metrics["tasks"]["failed"] >= 0
        assert metrics["tasks"]["queued"] >= 0

    def test_system_metrics_health_status(self, agent_service_with_mocks):
        """Test system health status"""
        service = agent_service_with_mocks

        metrics = service.get_system_metrics()

        assert metrics["system"]["status"] in ["healthy", "degraded"]
        assert "uptime" in metrics["system"]


@pytest.mark.unit
class TestTaskQueue:
    """Test task queue processing"""

    @pytest.mark.asyncio
    async def test_task_queued_when_no_agent(self, agent_service_with_mocks):
        """Test task is queued when no agent available"""
        service = agent_service_with_mocks

        # Make all agents busy
        for agent in service.agents.values():
            agent.status = AgentStatus.BUSY

        result = await service.execute_task("content_generator", "generate", {"subject": "Math"})

        assert len(service.task_queue) > 0
        assert result["status"] == "queued"

    @pytest.mark.asyncio
    async def test_process_task_queue(self, agent_service_with_mocks):
        """Test processing queued tasks"""
        service = agent_service_with_mocks

        # Create a queued task
        task_id = str(uuid.uuid4())
        task = TaskInfo(task_id, "content_generator", "generate", {"subject": "Math"})
        task.status = TaskStatus.QUEUED
        service.tasks[task_id] = task
        service.task_queue.append(task_id)

        with patch(
            "apps.backend.services.agent_service.trigger_task_event", new_callable=AsyncMock
        ):
            await service._process_task_queue()

        # Queue should be empty after processing
        assert len(service.task_queue) == 0


@pytest.mark.unit
class TestSupabaseIntegration:
    """Test Supabase integration"""

    @pytest.mark.asyncio
    async def test_persist_agent_to_supabase(self, mock_supabase_service):
        """Test persisting agent to Supabase"""
        with patch(
            "apps.backend.services.agent_service.get_supabase_service",
            return_value=mock_supabase_service,
        ):
            with patch("apps.backend.services.agent_service.SUPABASE_AVAILABLE", True):
                with patch(
                    "apps.backend.services.agent_service.ContentGenerationAgent",
                    return_value=AsyncMock(),
                ):
                    with patch(
                        "apps.backend.services.agent_service.QuizGenerationAgent",
                        return_value=AsyncMock(),
                    ):
                        with patch(
                            "apps.backend.services.agent_service.TerrainGenerationAgent",
                            return_value=AsyncMock(),
                        ):
                            with patch(
                                "apps.backend.services.agent_service.ScriptGenerationAgent",
                                return_value=AsyncMock(),
                            ):
                                with patch(
                                    "apps.backend.services.agent_service.CodeReviewAgent",
                                    return_value=AsyncMock(),
                                ):
                                    # Create service with Supabase
                                    service = AgentService()

                                    # Wait for async tasks
                                    import asyncio

                                    await asyncio.sleep(0.1)

                                    # Verify Supabase connection
                                    assert service.supabase_service is not None

    @pytest.mark.asyncio
    async def test_persist_task_to_supabase(self, agent_service_with_mocks, mock_supabase_service):
        """Test persisting task to Supabase"""
        service = agent_service_with_mocks
        service.supabase_service = mock_supabase_service

        task = TaskInfo("task_123", "content", "generate", {"subject": "Math"})

        result = await service._persist_task_to_supabase(task, "agent_123", "user_123")

        assert result is not None
        mock_supabase_service.create_task_execution.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_task_in_supabase(self, agent_service_with_mocks, mock_supabase_service):
        """Test updating task in Supabase"""
        service = agent_service_with_mocks
        service.supabase_service = mock_supabase_service

        updates = {"status": "completed", "output_data": {"result": "success"}}

        await service._update_task_in_supabase("task_123", updates)

        mock_supabase_service.update_task_execution.assert_called_once_with("task_123", updates)


@pytest.mark.unit
class TestPusherIntegration:
    """Test Pusher real-time integration"""

    @pytest.mark.asyncio
    async def test_trigger_task_events(self, agent_service_with_mocks):
        """Test triggering task events via Pusher"""
        service = agent_service_with_mocks

        with patch(
            "apps.backend.services.agent_service.trigger_task_event", new_callable=AsyncMock
        ) as mock_trigger:
            await service.execute_task(
                "content_generator", "generate", {"subject": "Math"}, user_id="user_123"
            )

        # Should trigger task_started and task_completed events
        assert mock_trigger.call_count >= 2

    @pytest.mark.asyncio
    async def test_notify_status_update(self, agent_service_with_mocks):
        """Test sending status updates"""
        service = agent_service_with_mocks

        with patch(
            "apps.backend.services.agent_service.trigger_agent_event", new_callable=AsyncMock
        ) as mock_trigger:
            await service._notify_status_update("agent_123", "status_change", {"status": "busy"})

        mock_trigger.assert_called_once()


@pytest.mark.unit
class TestServiceShutdown:
    """Test service shutdown"""

    @pytest.mark.asyncio
    async def test_shutdown_cancels_running_tasks(self, agent_service_with_mocks):
        """Test shutdown cancels running tasks"""
        service = agent_service_with_mocks

        # Create running task
        task = TaskInfo("task_123", "content", "generate", {})
        task.status = TaskStatus.RUNNING
        service.tasks["task_123"] = task

        await service.shutdown()

        assert task.status == TaskStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_shutdown_sets_agents_to_maintenance(self, agent_service_with_mocks):
        """Test shutdown sets all agents to maintenance mode"""
        service = agent_service_with_mocks

        await service.shutdown()

        for agent in service.agents.values():
            assert agent.status == AgentStatus.MAINTENANCE


@pytest.mark.unit
class TestGlobalServiceInstance:
    """Test global service instance"""

    def test_get_agent_service_creates_instance(self):
        """Test get_agent_service creates global instance"""
        with patch("apps.backend.services.agent_service.AgentService") as MockService:
            mock_instance = MockService.return_value

            # Reset global instance
            import apps.backend.services.agent_service as service_module

            service_module._agent_service = None

            service = get_agent_service()

            assert service == mock_instance

    @pytest.mark.asyncio
    async def test_shutdown_agent_service(self):
        """Test global service shutdown"""
        import apps.backend.services.agent_service as service_module

        # Create mock instance
        mock_service = Mock()
        mock_service.shutdown = AsyncMock()
        service_module._agent_service = mock_service

        await shutdown_agent_service()

        mock_service.shutdown.assert_called_once()
        assert service_module._agent_service is None


@pytest.mark.unit
class TestAgentEnums:
    """Test AgentStatus and TaskStatus enums"""

    def test_agent_status_values(self):
        """Test AgentStatus enum values"""
        assert AgentStatus.INITIALIZING == "initializing"
        assert AgentStatus.IDLE == "idle"
        assert AgentStatus.BUSY == "busy"
        assert AgentStatus.ERROR == "error"
        assert AgentStatus.OFFLINE == "offline"
        assert AgentStatus.MAINTENANCE == "maintenance"

    def test_task_status_values(self):
        """Test TaskStatus enum values"""
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.QUEUED == "queued"
        assert TaskStatus.RUNNING == "running"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"
        assert TaskStatus.CANCELLED == "cancelled"


@pytest.mark.unit
class TestErrorHandling:
    """Test error handling in agent service"""

    @pytest.mark.asyncio
    async def test_execute_task_agent_exception(self, agent_service_with_mocks, mock_content_agent):
        """Test task execution handles agent exceptions"""
        service = agent_service_with_mocks

        # Make agent raise exception
        mock_content_agent.generate_content.side_effect = Exception("Agent error")

        with patch(
            "apps.backend.services.agent_service.trigger_task_event", new_callable=AsyncMock
        ):
            result = await service.execute_task(
                "content_generator", "generate", {"subject": "Math"}
            )

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_task_failure_updates_metrics(self, agent_service_with_mocks, mock_content_agent):
        """Test failed task updates agent metrics"""
        service = agent_service_with_mocks

        # Get agent
        agent_id = service._find_available_agent("content_generator")
        agent = service.agents[agent_id]
        initial_failed = agent.total_tasks_failed

        # Make agent raise exception
        mock_content_agent.generate_content.side_effect = Exception("Agent error")

        with patch(
            "apps.backend.services.agent_service.trigger_task_event", new_callable=AsyncMock
        ):
            await service.execute_task("content_generator", "generate", {"subject": "Math"})

        assert agent.total_tasks_failed == initial_failed + 1
        assert agent.status == AgentStatus.IDLE  # Back to idle after failure

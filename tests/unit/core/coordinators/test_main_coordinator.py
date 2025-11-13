"""
Unit tests for Main Coordinator - Master coordination hub
Tests orchestration of agents, swarm, SPARC, and MCP subsystems
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from core.coordinators.main_coordinator import (
    ContentGenerationRequest,
    ContentGenerationResult,
    MainCoordinator,
    SystemHealth,
    create_main_coordinator,
)

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_workflow_coordinator():
    """Mock workflow coordinator"""
    coordinator = AsyncMock()
    coordinator.get_health = AsyncMock(return_value={"status": "healthy"})
    coordinator.get_metrics = AsyncMock(return_value={"workflows_processed": 10})
    coordinator.create_workflow = AsyncMock(return_value="workflow_123")
    return coordinator


@pytest.fixture
def mock_resource_coordinator():
    """Mock resource coordinator"""
    coordinator = AsyncMock()
    coordinator.get_health = AsyncMock(return_value={"status": "healthy"})
    coordinator.get_metrics = AsyncMock(return_value={"cpu_usage": 45.2})
    coordinator.get_utilization = AsyncMock(return_value={"cpu": 0.45, "memory": 0.60, "gpu": 0.30})
    coordinator.allocate_resources = AsyncMock(return_value=True)
    coordinator.release_resources = AsyncMock(return_value=True)
    return coordinator


@pytest.fixture
def mock_sync_coordinator():
    """Mock sync coordinator"""
    coordinator = AsyncMock()
    coordinator.get_health = AsyncMock(return_value={"status": "healthy"})
    return coordinator


@pytest.fixture
def mock_error_coordinator():
    """Mock error coordinator"""
    coordinator = AsyncMock()
    coordinator.handle_error = AsyncMock(return_value=None)
    return coordinator


@pytest.fixture
def mock_agent_system():
    """Mock agent orchestrator system"""
    system = AsyncMock()
    system.initialize = AsyncMock(return_value=None)
    system.shutdown = AsyncMock(return_value=None)
    system.get_health = AsyncMock(return_value={"status": "healthy"})
    system.plan_content = AsyncMock(
        return_value={
            "sections": ["Introduction", "Main Content", "Conclusion"],
            "activities": ["Quiz", "Interactive Demo"],
        }
    )
    return system


@pytest.fixture
def mock_swarm_controller():
    """Mock swarm controller"""
    controller = AsyncMock()
    controller.initialize = AsyncMock(return_value=None)
    controller.shutdown = AsyncMock(return_value=None)
    controller.get_health = AsyncMock(return_value={"status": "healthy"})
    controller.execute_task = AsyncMock(
        return_value={
            "type": "terrain_generation",
            "data": {"terrain": "hills"},
            "scripts": ["terrain_script.lua"],
            "agent_id": "swarm_agent_1",
        }
    )
    return controller


@pytest.fixture
def mock_sparc_manager():
    """Mock SPARC state manager"""
    manager = AsyncMock()
    manager.initialize = AsyncMock(return_value=None)
    manager.shutdown = AsyncMock(return_value=None)
    manager.get_health = AsyncMock(return_value={"status": "healthy"})
    manager.initialize_context = AsyncMock(return_value={"context_id": "ctx_123", "grade_level": 5})
    manager.evaluate_content = AsyncMock(
        return_value={"needs_adaptation": False, "quality_score": 85}
    )
    manager.adapt_content = AsyncMock(return_value=[{"adapted": True, "data": "adapted_content"}])
    return manager


@pytest.fixture
def mock_mcp_client():
    """Mock MCP client"""
    client = AsyncMock()
    client.connect = AsyncMock(return_value=None)
    client.disconnect = AsyncMock(return_value=None)
    client.get_health = AsyncMock(return_value={"status": "healthy"})
    client.update_context = AsyncMock(return_value=None)
    return client


@pytest.fixture
def sample_config():
    """Sample configuration"""
    return {
        "max_concurrent_requests": 5,
        "health_check_interval": 10,
        "enable_caching": True,
    }


@pytest.fixture
def main_coordinator(
    mock_workflow_coordinator,
    mock_resource_coordinator,
    mock_sync_coordinator,
    mock_error_coordinator,
    sample_config,
):
    """MainCoordinator with mocked dependencies"""
    coordinator = MainCoordinator(
        workflow_coordinator=mock_workflow_coordinator,
        resource_coordinator=mock_resource_coordinator,
        sync_coordinator=mock_sync_coordinator,
        error_coordinator=mock_error_coordinator,
        config=sample_config,
    )
    return coordinator


@pytest.fixture
def sample_content_request():
    """Sample content generation request"""
    return ContentGenerationRequest(
        request_id="req_123",
        subject="Mathematics",
        grade_level=5,
        learning_objectives=["Learn addition", "Learn subtraction"],
        environment_type="classroom",
        include_quiz=True,
        custom_parameters={"difficulty": "medium"},
        priority=1,
    )


# ============================================================================
# Test Class: MainCoordinator Initialization
# ============================================================================


@pytest.mark.unit
class TestMainCoordinatorInitialization:
    """Test MainCoordinator initialization"""

    @pytest.mark.asyncio
    async def test_initialization_success(
        self,
        main_coordinator,
        mock_agent_system,
        mock_swarm_controller,
        mock_sparc_manager,
        mock_mcp_client,
    ):
        """Test successful initialization"""
        with patch(
            "core.coordinators.main_coordinator.AgentOrchestrator",
            return_value=mock_agent_system,
        ):
            with patch(
                "core.coordinators.main_coordinator.create_test_swarm_controller",
                return_value=mock_swarm_controller,
            ):
                with patch(
                    "core.coordinators.main_coordinator.StateManager",
                    return_value=mock_sparc_manager,
                ):
                    with patch(
                        "core.coordinators.main_coordinator.MCPClient",
                        return_value=mock_mcp_client,
                    ):
                        await main_coordinator.initialize()

        assert main_coordinator.is_initialized is True
        mock_agent_system.initialize.assert_called_once()
        mock_swarm_controller.initialize.assert_called_once()
        mock_sparc_manager.initialize.assert_called_once()
        mock_mcp_client.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialization_failure_unhealthy(self, main_coordinator):
        """Test initialization fails when system is unhealthy"""
        with patch.object(
            main_coordinator,
            "_initialize_subsystems",
            new_callable=AsyncMock,
        ):
            with patch.object(
                main_coordinator,
                "_start_background_tasks",
                new_callable=AsyncMock,
            ):
                with patch.object(
                    main_coordinator,
                    "get_health_status",
                    new_callable=AsyncMock,
                    return_value=SystemHealth(
                        status="unhealthy",
                        timestamp=datetime.now(),
                        component_health={"agent_system": "unhealthy"},
                        active_workflows=0,
                        resource_utilization={},
                        error_count=1,
                        last_error="Component failure",
                    ),
                ):
                    with pytest.raises(RuntimeError) as exc_info:
                        await main_coordinator.initialize()

                    assert "initialization failed" in str(exc_info.value)
                    assert main_coordinator.is_initialized is False

    @pytest.mark.asyncio
    async def test_initialization_with_import_error(self, main_coordinator):
        """Test initialization handles subsystem import errors gracefully"""
        with patch(
            "core.coordinators.main_coordinator.AgentOrchestrator",
            side_effect=ImportError("Module not found"),
        ):
            with patch.object(
                main_coordinator,
                "_start_background_tasks",
                new_callable=AsyncMock,
            ):
                with patch.object(
                    main_coordinator,
                    "get_health_status",
                    new_callable=AsyncMock,
                    return_value=SystemHealth(
                        status="degraded",
                        timestamp=datetime.now(),
                        component_health={"agent_system": "not_initialized"},
                        active_workflows=0,
                        resource_utilization={},
                        error_count=0,
                    ),
                ):
                    # Should not raise, operates in degraded mode
                    await main_coordinator.initialize()

                    assert main_coordinator.agent_system is None

    @pytest.mark.asyncio
    async def test_background_tasks_started(self, main_coordinator):
        """Test background monitoring tasks are started"""
        with patch.object(
            main_coordinator,
            "_initialize_subsystems",
            new_callable=AsyncMock,
        ):
            with patch.object(
                main_coordinator,
                "get_health_status",
                new_callable=AsyncMock,
                return_value=SystemHealth(
                    status="healthy",
                    timestamp=datetime.now(),
                    component_health={},
                    active_workflows=0,
                    resource_utilization={},
                    error_count=0,
                ),
            ):
                with patch("asyncio.create_task") as mock_create_task:
                    await main_coordinator.initialize()

                    assert mock_create_task.call_count >= 2  # health + metrics tasks

    @pytest.mark.asyncio
    async def test_configuration_applied(self, sample_config):
        """Test configuration is applied correctly"""
        coordinator = MainCoordinator(config=sample_config)

        assert coordinator.max_concurrent_requests == 5
        assert coordinator.health_check_interval == 10
        assert coordinator.enable_caching is True


# ============================================================================
# Test Class: Content Generation Workflow
# ============================================================================


@pytest.mark.unit
class TestContentGenerationWorkflow:
    """Test educational content generation workflow"""

    @pytest.mark.asyncio
    async def test_generate_content_success(
        self,
        main_coordinator,
        mock_agent_system,
        mock_swarm_controller,
        mock_sparc_manager,
    ):
        """Test successful content generation"""
        main_coordinator.is_initialized = True
        main_coordinator.agent_system = mock_agent_system
        main_coordinator.swarm_controller = mock_swarm_controller
        main_coordinator.sparc_manager = mock_sparc_manager

        # Mock swarm task execution with different task types
        async def mock_execute_task(task):
            task_type = task.get("type")
            return {
                "type": task_type,
                "data": {f"{task_type}_data": "generated"},
                "scripts": [f"{task_type}_script.lua"],
                "agent_id": f"{task_type}_agent",
            }

        mock_swarm_controller.execute_task.side_effect = mock_execute_task

        result = await main_coordinator.generate_educational_content(
            subject="Mathematics",
            grade_level=5,
            learning_objectives=["Learn addition", "Learn subtraction"],
            environment_type="classroom",
            include_quiz=True,
        )

        assert result.success is True
        assert result.content is not None
        assert len(result.scripts) >= 2
        assert result.quiz_data is not None
        assert result.metrics["generation_time"] > 0
        assert result.errors == []

    @pytest.mark.asyncio
    async def test_generate_content_capacity_limit(self, main_coordinator):
        """Test capacity limit enforcement"""
        main_coordinator.is_initialized = True
        main_coordinator.max_concurrent_requests = 2

        # Fill active requests to capacity
        main_coordinator.active_requests.add("req_1")
        main_coordinator.active_requests.add("req_2")

        with pytest.raises(HTTPException) as exc_info:
            await main_coordinator.generate_educational_content(
                subject="Math", grade_level=5, learning_objectives=["Test"]
            )

        assert exc_info.value.status_code == 429
        assert "Too many concurrent requests" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_generate_content_with_cache_hit(self, main_coordinator):
        """Test cache hit returns cached result"""
        main_coordinator.is_initialized = True
        main_coordinator.enable_caching = True

        # Pre-populate cache
        cached_result = ContentGenerationResult(
            request_id="cached_req",
            success=True,
            content={"title": "Cached Math Lesson"},
            scripts=["cached_script.lua"],
            quiz_data={"questions": []},
            metrics={"generation_time": 1.5},
            errors=[],
            generation_time=1.5,
        )

        cache_key = "Mathematics_5_" + str(hash(tuple(["Learn addition", "Learn subtraction"])))
        from dataclasses import asdict

        main_coordinator.cache[cache_key] = asdict(cached_result)

        result = await main_coordinator.generate_educational_content(
            subject="Mathematics",
            grade_level=5,
            learning_objectives=["Learn addition", "Learn subtraction"],
        )

        # Should return cached result
        assert result.content["title"] == "Cached Math Lesson"

    @pytest.mark.asyncio
    async def test_generate_content_resource_allocation(
        self, main_coordinator, mock_resource_coordinator
    ):
        """Test resource allocation and cleanup"""
        main_coordinator.is_initialized = True
        main_coordinator.agent_system = AsyncMock()
        main_coordinator.swarm_controller = None  # Disable swarm to simplify

        await main_coordinator.generate_educational_content(
            subject="Science",
            grade_level=6,
            learning_objectives=["Photosynthesis"],
            include_quiz=True,
        )

        # Verify resource allocation called
        mock_resource_coordinator.allocate_resources.assert_called_once()
        call_args = mock_resource_coordinator.allocate_resources.call_args[0]
        assert call_args[1]["cpu_cores"] == 2
        assert call_args[1]["gpu_memory_mb"] == 512  # With quiz

        # Verify resource cleanup
        mock_resource_coordinator.release_resources.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_content_error_handling(self, main_coordinator, mock_error_coordinator):
        """Test error handling during content generation"""
        main_coordinator.is_initialized = True
        main_coordinator.agent_system = AsyncMock()
        main_coordinator.agent_system.plan_content.side_effect = Exception("Planning failed")

        result = await main_coordinator.generate_educational_content(
            subject="Math", grade_level=5, learning_objectives=["Test"]
        )

        assert result.success is False
        assert len(result.errors) == 1
        assert "Planning failed" in result.errors[0]
        mock_error_coordinator.handle_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_content_without_quiz(self, main_coordinator):
        """Test content generation without quiz reduces GPU allocation"""
        main_coordinator.is_initialized = True

        with patch.object(
            main_coordinator.resource_coordinator, "allocate_resources"
        ) as mock_allocate:
            with patch.object(
                main_coordinator, "_orchestrate_content_generation"
            ) as mock_orchestrate:
                mock_orchestrate.return_value = {
                    "content": {},
                    "scripts": [],
                    "agents_used": [],
                }

                await main_coordinator.generate_educational_content(
                    subject="Math",
                    grade_level=5,
                    learning_objectives=["Test"],
                    include_quiz=False,
                )

                call_args = mock_allocate.call_args[0]
                assert call_args[1]["gpu_memory_mb"] == 256  # No quiz = less GPU


# ============================================================================
# Test Class: Content Orchestration
# ============================================================================


@pytest.mark.unit
class TestContentOrchestration:
    """Test multi-phase content orchestration"""

    @pytest.mark.asyncio
    async def test_orchestrate_content_generation_phases(
        self,
        main_coordinator,
        sample_content_request,
        mock_agent_system,
        mock_swarm_controller,
        mock_sparc_manager,
    ):
        """Test all orchestration phases execute correctly"""
        main_coordinator.agent_system = mock_agent_system
        main_coordinator.swarm_controller = mock_swarm_controller
        main_coordinator.sparc_manager = mock_sparc_manager

        # Mock tasks with different types
        async def mock_execute(task):
            task_type = task["type"]
            return {
                "type": task_type,
                "data": {f"{task_type}_result": "data"},
                "scripts": [f"{task_type}.lua"],
                "agent_id": f"{task_type}_agent",
            }

        mock_swarm_controller.execute_task.side_effect = mock_execute

        result = await main_coordinator._orchestrate_content_generation(
            sample_content_request,
            workflow_id="wf_123",
            sparc_context={"context_id": "ctx_123"},
        )

        # Verify all phases executed
        mock_agent_system.plan_content.assert_called_once()  # Phase 1
        assert mock_swarm_controller.execute_task.call_count == 3  # Phase 2
        mock_sparc_manager.evaluate_content.assert_called_once()  # Phase 3
        assert "content_plan" in result  # Phase 4 assembly

    @pytest.mark.asyncio
    async def test_orchestrate_with_sparc_adaptation(
        self, main_coordinator, sample_content_request, mock_sparc_manager
    ):
        """Test SPARC adaptation when content needs improvement"""
        main_coordinator.sparc_manager = mock_sparc_manager
        main_coordinator.swarm_controller = None

        # Mock evaluation indicates adaptation needed
        mock_sparc_manager.evaluate_content.return_value = {
            "needs_adaptation": True,
            "quality_score": 65,
        }

        await main_coordinator._orchestrate_content_generation(
            sample_content_request, workflow_id=None, sparc_context={"ctx": "123"}
        )

        # Verify adaptation was called
        mock_sparc_manager.adapt_content.assert_called_once()

    @pytest.mark.asyncio
    async def test_orchestrate_parallel_task_execution(
        self, main_coordinator, sample_content_request, mock_swarm_controller
    ):
        """Test parallel execution of swarm tasks"""
        main_coordinator.swarm_controller = mock_swarm_controller

        call_count = 0

        async def count_calls(task):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)  # Simulate async work
            return {"type": task["type"], "data": {}}

        mock_swarm_controller.execute_task.side_effect = count_calls

        await main_coordinator._orchestrate_content_generation(
            sample_content_request, workflow_id=None, sparc_context={}
        )

        # 3 tasks should run: terrain, script, quiz
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_assemble_final_content(self, main_coordinator, sample_content_request):
        """Test final content assembly from generation results"""
        content_plan = {"sections": ["Intro", "Main"]}
        generation_results = [
            {
                "type": "terrain_generation",
                "data": {"terrain": "hills"},
                "scripts": ["terrain.lua"],
                "agent_id": "terrain_agent",
            },
            {
                "type": "script_generation",
                "data": {},
                "scripts": ["main.lua", "utils.lua"],
                "agent_id": "script_agent",
            },
            {
                "type": "quiz_generation",
                "data": {"questions": [{"q": "What is 2+2?"}]},
                "agent_id": "quiz_agent",
            },
        ]

        result = await main_coordinator._assemble_final_content(
            content_plan, generation_results, sample_content_request
        )

        assert result["metadata"]["subject"] == "Mathematics"
        assert result["metadata"]["grade_level"] == 5
        assert result["terrain_data"] == {"terrain": "hills"}
        assert len(result["scripts"]) == 3
        assert result["quiz_data"] == {"questions": [{"q": "What is 2+2?"}]}
        assert len(result["agents_used"]) == 3


# ============================================================================
# Test Class: Health Monitoring
# ============================================================================


@pytest.mark.unit
class TestHealthMonitoring:
    """Test system health monitoring"""

    @pytest.mark.asyncio
    async def test_get_health_status_all_healthy(
        self,
        main_coordinator,
        mock_workflow_coordinator,
        mock_resource_coordinator,
        mock_agent_system,
    ):
        """Test health status when all components are healthy"""
        main_coordinator.agent_system = mock_agent_system

        health = await main_coordinator.get_health_status()

        assert health.status == "healthy"
        assert health.component_health["workflow"] == "healthy"
        assert health.component_health["resource"] == "healthy"
        assert health.component_health["agent_system"] == "healthy"
        assert health.error_count == 0

    @pytest.mark.asyncio
    async def test_get_health_status_degraded(self, main_coordinator, mock_workflow_coordinator):
        """Test degraded health status"""
        mock_workflow_coordinator.get_health.return_value = {"status": "degraded"}

        health = await main_coordinator.get_health_status()

        assert health.status == "degraded"
        assert health.component_health["workflow"] == "degraded"

    @pytest.mark.asyncio
    async def test_get_health_status_unhealthy_component(
        self, main_coordinator, mock_resource_coordinator
    ):
        """Test unhealthy status when component fails"""
        mock_resource_coordinator.get_health.side_effect = Exception("Connection lost")

        health = await main_coordinator.get_health_status()

        assert health.status == "unhealthy"
        assert health.component_health["resource"] == "unhealthy"
        assert health.error_count > 0
        assert "Connection lost" in health.last_error

    @pytest.mark.asyncio
    async def test_get_health_status_resource_utilization(
        self, main_coordinator, mock_resource_coordinator
    ):
        """Test resource utilization included in health status"""
        health = await main_coordinator.get_health_status()

        assert "cpu" in health.resource_utilization
        assert "memory" in health.resource_utilization
        assert health.resource_utilization["cpu"] == 0.45

    @pytest.mark.asyncio
    async def test_health_monitor_background_task(self, main_coordinator):
        """Test health monitoring background task"""
        main_coordinator.is_initialized = True
        main_coordinator.health_check_interval = 0.1  # Fast for testing

        with patch.object(main_coordinator, "get_health_status") as mock_get_health:
            mock_get_health.return_value = SystemHealth(
                status="healthy",
                timestamp=datetime.now(),
                component_health={},
                active_workflows=0,
                resource_utilization={},
                error_count=0,
            )

            # Start monitoring task
            task = asyncio.create_task(main_coordinator._health_monitor())

            # Let it run a few iterations
            await asyncio.sleep(0.3)

            # Stop monitoring
            main_coordinator.is_initialized = False
            await asyncio.sleep(0.2)

            # Verify health checks occurred
            assert mock_get_health.call_count >= 2

    @pytest.mark.asyncio
    async def test_handle_health_degradation(self, main_coordinator, mock_error_coordinator):
        """Test handling of health degradation"""
        degraded_health = SystemHealth(
            status="degraded",
            timestamp=datetime.now(),
            component_health={"agent_system": "degraded"},
            active_workflows=1,
            resource_utilization={},
            error_count=0,
        )

        await main_coordinator._handle_health_degradation(degraded_health)

        # Should log warning but not trigger error coordinator

        unhealthy_health = SystemHealth(
            status="unhealthy",
            timestamp=datetime.now(),
            component_health={"agent_system": "unhealthy"},
            active_workflows=0,
            resource_utilization={},
            error_count=1,
            last_error="System failure",
        )

        await main_coordinator._handle_health_degradation(unhealthy_health)

        # Should trigger error coordinator for unhealthy status
        mock_error_coordinator.handle_error.assert_called_once()


# ============================================================================
# Test Class: Caching System
# ============================================================================


@pytest.mark.unit
class TestCachingSystem:
    """Test request/result caching"""

    @pytest.mark.asyncio
    async def test_check_cache_miss(self, main_coordinator, sample_content_request):
        """Test cache miss returns None"""
        result = await main_coordinator._check_cache(sample_content_request)

        assert result is None

    @pytest.mark.asyncio
    async def test_check_cache_hit(self, main_coordinator):
        """Test cache hit returns cached result"""
        from dataclasses import asdict

        cached_result = ContentGenerationResult(
            request_id="old_req",
            success=True,
            content={"title": "Cached Lesson"},
            scripts=["script.lua"],
            quiz_data=None,
            metrics={},
            errors=[],
            generation_time=2.5,
        )

        # Create cache key
        subject = "Math"
        grade_level = 5
        objectives = ["Learn addition"]
        cache_key = f"{subject}_{grade_level}_{hash(tuple(objectives))}"

        main_coordinator.cache[cache_key] = asdict(cached_result)

        # Create matching request
        request = ContentGenerationRequest(
            request_id="new_req",
            subject=subject,
            grade_level=grade_level,
            learning_objectives=objectives,
            environment_type="classroom",
            include_quiz=False,
            custom_parameters={},
        )

        result = await main_coordinator._check_cache(request)

        assert result is not None
        assert result.content["title"] == "Cached Lesson"
        assert result.request_id == "new_req"  # Updated with new request ID

    @pytest.mark.asyncio
    async def test_cache_result(self, main_coordinator, sample_content_request):
        """Test caching successful result"""
        result = ContentGenerationResult(
            request_id="req_123",
            success=True,
            content={"title": "Math Lesson"},
            scripts=["script.lua"],
            quiz_data=None,
            metrics={},
            errors=[],
            generation_time=3.0,
        )

        await main_coordinator._cache_result(sample_content_request, result)

        # Verify cache contains result
        assert len(main_coordinator.cache) == 1
        cached_data = next(iter(main_coordinator.cache.values()))
        assert cached_data["content"]["title"] == "Math Lesson"
        assert cached_data["request_id"] is None  # Removed for caching

    @pytest.mark.asyncio
    async def test_cache_size_limit(self, main_coordinator):
        """Test cache evicts oldest entries when limit exceeded"""
        # Fill cache beyond limit (100)
        for i in range(105):
            cache_key = f"key_{i}"
            main_coordinator.cache[cache_key] = {"data": i}

        # Cache should have evicted oldest entries
        assert len(main_coordinator.cache) <= 100


# ============================================================================
# Test Class: Metrics and Quality Scores
# ============================================================================


@pytest.mark.unit
class TestMetricsAndQuality:
    """Test metrics collection and quality scoring"""

    def test_calculate_complexity_score(self, main_coordinator):
        """Test complexity score calculation"""
        content = {
            "metadata": {"learning_objectives": ["Obj1", "Obj2", "Obj3"]},
            "terrain_data": {"terrain": "hills"},
            "scripts": ["line1\nline2\nline3"] * 50,  # 150 total lines
            "quiz_data": {"questions": [{"q": f"Q{i}"} for i in range(15)]},
        }

        score = main_coordinator._calculate_complexity_score(content)

        # Score components: 30 (3 objectives) + 20 (terrain) + 15 (150/10 capped at 30) + 20 (quiz capped)
        assert 0 <= score <= 100
        assert score > 50  # Should be high due to comprehensive content

    def test_calculate_quality_score(self, main_coordinator):
        """Test quality score calculation"""
        # High quality content
        good_content = {
            "metadata": {"environment_type": "classroom"},
            "scripts": ["script1.lua", "script2.lua", "script3.lua"],
            "terrain_data": {"terrain": "generated"},
            "quiz_data": {"questions": []},
            "errors": [],
        }

        good_score = main_coordinator._calculate_quality_score(good_content)
        assert good_score >= 90

        # Low quality content with errors
        poor_content = {
            "metadata": {"environment_type": "classroom"},
            "scripts": [],
            "terrain_data": None,
            "quiz_data": None,
            "errors": ["Error 1", "Error 2", "Error 3"],
        }

        poor_score = main_coordinator._calculate_quality_score(poor_content)
        assert poor_score < 60

    @pytest.mark.asyncio
    async def test_metrics_collector_background_task(
        self, main_coordinator, mock_resource_coordinator, mock_workflow_coordinator
    ):
        """Test metrics collection background task"""
        main_coordinator.is_initialized = True
        main_coordinator.mcp_client = AsyncMock()

        # Start metrics collector
        task = asyncio.create_task(main_coordinator._metrics_collector())

        # Let it run one iteration
        await asyncio.sleep(0.1)

        # Stop collector
        main_coordinator.is_initialized = False
        await asyncio.sleep(0.1)

        # Verify metrics were collected
        mock_resource_coordinator.get_metrics.assert_called()
        mock_workflow_coordinator.get_metrics.assert_called()

    @pytest.mark.asyncio
    async def test_log_system_state(self, main_coordinator):
        """Test system state logging"""
        main_coordinator.mcp_client = AsyncMock()
        main_coordinator.active_requests.add("req_1")
        main_coordinator.system_metrics["test_metric"] = 123.45

        await main_coordinator._log_system_state("test_event")

        # Verify MCP context update called
        main_coordinator.mcp_client.update_context.assert_called_once()
        call_args = main_coordinator.mcp_client.update_context.call_args[0][0]
        assert call_args["system_state"]["event"] == "test_event"
        assert call_args["system_state"]["active_requests"] == 1


# ============================================================================
# Test Class: FastAPI Routes
# ============================================================================


@pytest.mark.unit
class TestFastAPIRoutes:
    """Test FastAPI endpoint setup"""

    def test_routes_registered(self, main_coordinator):
        """Test all required routes are registered"""
        routes = [route.path for route in main_coordinator.app.routes]

        assert "/generate_content" in routes
        assert "/health" in routes
        assert "/metrics" in routes
        assert "/requests/{request_id}" in routes

    @pytest.mark.asyncio
    async def test_health_endpoint(self, main_coordinator):
        """Test health check endpoint"""
        with patch.object(main_coordinator, "get_health_status") as mock_health:
            mock_health.return_value = SystemHealth(
                status="healthy",
                timestamp=datetime.now(),
                component_health={},
                active_workflows=0,
                resource_utilization={},
                error_count=0,
            )

            # Find health route
            health_route = next(r for r in main_coordinator.app.routes if r.path == "/health")
            response = await health_route.endpoint()

            assert response["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, main_coordinator):
        """Test metrics endpoint"""
        main_coordinator.system_metrics["test_metric"] = 42.0

        # Find metrics route
        metrics_route = next(r for r in main_coordinator.app.routes if r.path == "/metrics")
        response = await metrics_route.endpoint()

        assert "test_metric" in response
        assert response["test_metric"] == 42.0


# ============================================================================
# Test Class: Shutdown and Cleanup
# ============================================================================


@pytest.mark.unit
class TestShutdownAndCleanup:
    """Test graceful shutdown"""

    @pytest.mark.asyncio
    async def test_shutdown_cancels_background_tasks(self, main_coordinator):
        """Test shutdown cancels background monitoring tasks"""
        main_coordinator.health_monitor_task = AsyncMock()
        main_coordinator.metrics_collector_task = AsyncMock()

        await main_coordinator.shutdown()

        main_coordinator.health_monitor_task.cancel.assert_called_once()
        main_coordinator.metrics_collector_task.cancel.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_waits_for_active_requests(self, main_coordinator):
        """Test shutdown waits for active requests to complete"""
        main_coordinator.active_requests.add("req_1")
        main_coordinator.active_requests.add("req_2")

        # Simulate requests completing during shutdown
        async def remove_requests():
            await asyncio.sleep(0.1)
            main_coordinator.active_requests.clear()

        shutdown_task = asyncio.create_task(main_coordinator.shutdown())
        cleanup_task = asyncio.create_task(remove_requests())

        await asyncio.gather(shutdown_task, cleanup_task)

        # Verify shutdown completed after requests cleared
        assert len(main_coordinator.active_requests) == 0

    @pytest.mark.asyncio
    async def test_shutdown_subsystems(
        self,
        main_coordinator,
        mock_agent_system,
        mock_swarm_controller,
        mock_sparc_manager,
        mock_mcp_client,
    ):
        """Test shutdown calls shutdown on all subsystems"""
        main_coordinator.agent_system = mock_agent_system
        main_coordinator.swarm_controller = mock_swarm_controller
        main_coordinator.sparc_manager = mock_sparc_manager
        main_coordinator.mcp_client = mock_mcp_client

        await main_coordinator.shutdown()

        mock_agent_system.shutdown.assert_called_once()
        mock_swarm_controller.shutdown.assert_called_once()
        mock_sparc_manager.shutdown.assert_called_once()
        mock_mcp_client.disconnect.assert_called_once()
        assert main_coordinator.is_initialized is False

    @pytest.mark.asyncio
    async def test_shutdown_handles_errors(self, main_coordinator):
        """Test shutdown handles subsystem errors gracefully"""
        main_coordinator.agent_system = AsyncMock()
        main_coordinator.agent_system.shutdown.side_effect = Exception("Shutdown failed")

        # Should not raise exception
        await main_coordinator.shutdown()

        assert main_coordinator.is_initialized is False


# ============================================================================
# Test Class: Convenience Functions
# ============================================================================


@pytest.mark.unit
class TestConvenienceFunctions:
    """Test module-level convenience functions"""

    @pytest.mark.asyncio
    async def test_create_main_coordinator(self):
        """Test create_main_coordinator factory function"""
        with patch.object(MainCoordinator, "initialize", new_callable=AsyncMock):
            coordinator = await create_main_coordinator(config={"max_concurrent_requests": 3})

            assert isinstance(coordinator, MainCoordinator)
            assert coordinator.max_concurrent_requests == 3
            coordinator.initialize.assert_called_once()

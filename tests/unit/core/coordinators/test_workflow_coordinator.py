"""
Unit tests for Workflow Coordinator

Tests workflow management, step execution, templates, and optimization.
Covers workflow creation, execution, control, metrics, and health monitoring.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from core.coordinators.workflow_coordinator import (
    StepStatus,
    Workflow,
    WorkflowCoordinator,
    WorkflowStatus,
    WorkflowStep,
    WorkflowTemplate,
    create_workflow_coordinator,
)


@pytest.fixture
def workflow_config():
    """Workflow coordinator configuration"""
    return {"max_concurrent_workflows": 3, "cleanup_days": 7, "optimization_interval": 300}


@pytest.fixture
def workflow_coordinator(workflow_config):
    """Create workflow coordinator instance"""
    return WorkflowCoordinator(config=workflow_config)


@pytest.fixture
async def initialized_coordinator(workflow_coordinator):
    """Create and initialize workflow coordinator"""
    with patch.object(workflow_coordinator, "_setup_executors", new_callable=AsyncMock):
        with patch("asyncio.create_task") as mock_create_task:
            await workflow_coordinator.initialize()
            workflow_coordinator.is_initialized = True
            yield workflow_coordinator


@pytest.fixture
def sample_workflow_step():
    """Sample workflow step"""
    return WorkflowStep(
        step_id="test_step_1",
        name="Test Step",
        description="A test step",
        executor="agent_system",
        parameters={"agent_type": "content_agent"},
        timeout=120,
    )


@pytest.fixture
def sample_workflow(sample_workflow_step):
    """Sample workflow"""
    return Workflow(
        workflow_id="test_workflow_1",
        name="Test Workflow",
        description="A test workflow",
        workflow_type="test_workflow",
        steps=[sample_workflow_step],
        parameters={"subject": "math"},
    )


@pytest.mark.unit
@pytest.mark.asyncio
class TestWorkflowCoordinatorInitialization:
    """Test workflow coordinator initialization"""

    async def test_initialization_success(self, workflow_coordinator):
        """Test successful initialization"""
        with patch.object(workflow_coordinator, "_setup_executors", new_callable=AsyncMock):
            with patch("asyncio.create_task") as mock_create_task:
                await workflow_coordinator.initialize()

                assert workflow_coordinator.is_initialized is True
                assert mock_create_task.call_count == 2  # executor and optimizer tasks

    async def test_initialization_creates_default_templates(self, workflow_coordinator):
        """Test default templates are created"""
        assert "educational_content_generation" in workflow_coordinator.templates
        assert "complete_course_generation" in workflow_coordinator.templates
        assert "adaptive_assessment_generation" in workflow_coordinator.templates
        assert len(workflow_coordinator.templates) >= 3

    async def test_initialization_sets_config(self, workflow_config):
        """Test configuration is applied"""
        coordinator = WorkflowCoordinator(config=workflow_config)

        assert coordinator.max_concurrent_workflows == 3
        assert coordinator.config == workflow_config

    async def test_initialization_creates_executor_registry(self, workflow_coordinator):
        """Test executor registry is initialized"""
        with patch.object(
            workflow_coordinator, "_setup_executors", new_callable=AsyncMock
        ) as mock_setup:
            await workflow_coordinator.initialize()

            mock_setup.assert_called_once()

    async def test_initialization_starts_background_tasks(self, workflow_coordinator):
        """Test background tasks are started"""
        with patch.object(workflow_coordinator, "_setup_executors", new_callable=AsyncMock):
            with patch("asyncio.create_task") as mock_create_task:
                await workflow_coordinator.initialize()

                # Check that tasks were created for executor and optimizer
                assert mock_create_task.call_count == 2


@pytest.mark.unit
@pytest.mark.asyncio
class TestWorkflowCreation:
    """Test workflow creation from templates"""

    async def test_create_workflow_success(self, initialized_coordinator):
        """Test successful workflow creation"""
        workflow_id = await initialized_coordinator.create_workflow(
            workflow_type="educational_content_generation",
            parameters={"subject": "science", "grade_level": "5"},
            priority=2,
        )

        assert workflow_id is not None
        assert workflow_id in initialized_coordinator.workflows

        workflow = initialized_coordinator.workflows[workflow_id]
        assert workflow.name == "Educational Content Generation"
        assert workflow.priority == 2
        assert len(workflow.steps) == 6  # Default template has 6 steps

    async def test_create_workflow_invalid_template(self, initialized_coordinator):
        """Test creation with invalid template"""
        with pytest.raises(ValueError, match="Unknown workflow template"):
            await initialized_coordinator.create_workflow(
                workflow_type="nonexistent_template", parameters={"subject": "math"}
            )

    async def test_create_workflow_queues_execution(self, initialized_coordinator):
        """Test workflow is queued for execution"""
        workflow_id = await initialized_coordinator.create_workflow(
            workflow_type="educational_content_generation", parameters={"subject": "math"}
        )

        assert workflow_id in initialized_coordinator.workflow_queue

    async def test_create_workflow_priority_ordering(self, initialized_coordinator):
        """Test workflows are queued by priority"""
        wf1 = await initialized_coordinator.create_workflow(
            workflow_type="educational_content_generation",
            parameters={"subject": "math"},
            priority=1,
        )
        wf2 = await initialized_coordinator.create_workflow(
            workflow_type="educational_content_generation",
            parameters={"subject": "science"},
            priority=5,
        )
        wf3 = await initialized_coordinator.create_workflow(
            workflow_type="educational_content_generation",
            parameters={"subject": "history"},
            priority=3,
        )

        # Queue should be sorted by priority (highest first)
        assert initialized_coordinator.workflow_queue[0] == wf2  # priority 5
        assert initialized_coordinator.workflow_queue[1] == wf3  # priority 3
        assert initialized_coordinator.workflow_queue[2] == wf1  # priority 1

    async def test_create_workflow_updates_metrics(self, initialized_coordinator):
        """Test workflow creation updates metrics"""
        workflow_id = await initialized_coordinator.create_workflow(
            workflow_type="educational_content_generation", parameters={"subject": "math"}
        )

        assert len(initialized_coordinator.execution_metrics["workflows_created"]) == 1
        assert (
            initialized_coordinator.execution_metrics["workflows_created"][0]["workflow_id"]
            == workflow_id
        )


@pytest.mark.unit
@pytest.mark.asyncio
class TestStepExecution:
    """Test individual workflow step execution"""

    async def test_execute_step_success(
        self, initialized_coordinator, sample_workflow_step, sample_workflow
    ):
        """Test successful step execution"""
        mock_executor = AsyncMock(return_value={"result": "success"})
        initialized_coordinator.executor_registry["agent_system"] = mock_executor

        result = await initialized_coordinator._execute_step(sample_workflow_step, sample_workflow)

        assert result == {"result": "success"}
        assert sample_workflow_step.status == StepStatus.RUNNING
        mock_executor.assert_called_once_with(sample_workflow_step)

    async def test_execute_step_with_timeout(
        self, initialized_coordinator, sample_workflow_step, sample_workflow
    ):
        """Test step execution with timeout"""

        async def slow_executor(step):
            await asyncio.sleep(10)
            return {"result": "too slow"}

        initialized_coordinator.executor_registry["agent_system"] = slow_executor
        sample_workflow_step.timeout = 1  # 1 second timeout

        with pytest.raises(RuntimeError, match="timed out"):
            await initialized_coordinator._execute_step(sample_workflow_step, sample_workflow)

    async def test_execute_step_retry_on_failure(
        self, initialized_coordinator, sample_workflow_step, sample_workflow
    ):
        """Test step retry on failure"""
        call_count = 0

        async def failing_executor(step):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RuntimeError("Temporary failure")
            return {"result": "success"}

        initialized_coordinator.executor_registry["agent_system"] = failing_executor
        sample_workflow_step.retry_count = 3

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await initialized_coordinator._execute_step(
                sample_workflow_step, sample_workflow
            )

        assert result == {"result": "success"}
        assert call_count == 3  # Failed 2 times, succeeded on 3rd

    async def test_execute_step_max_retries_exceeded(
        self, initialized_coordinator, sample_workflow_step, sample_workflow
    ):
        """Test step failure after max retries"""

        async def always_failing(step):
            raise RuntimeError("Persistent failure")

        initialized_coordinator.executor_registry["agent_system"] = always_failing
        sample_workflow_step.retry_count = 2

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(RuntimeError, match="Persistent failure"):
                await initialized_coordinator._execute_step(sample_workflow_step, sample_workflow)

    async def test_execute_step_unknown_executor(
        self, initialized_coordinator, sample_workflow_step, sample_workflow
    ):
        """Test execution with unknown executor"""
        sample_workflow_step.executor = "unknown_executor"

        with pytest.raises(ValueError, match="Unknown executor"):
            await initialized_coordinator._execute_step(sample_workflow_step, sample_workflow)

    async def test_execute_step_records_performance(
        self, initialized_coordinator, sample_workflow_step, sample_workflow
    ):
        """Test step execution records performance metrics"""
        mock_executor = AsyncMock(return_value={"result": "success"})
        initialized_coordinator.executor_registry["agent_system"] = mock_executor

        sample_workflow_step.start_time = datetime.now()

        await initialized_coordinator._execute_step(sample_workflow_step, sample_workflow)

        # Performance should be recorded if duration is available
        step_key = f"{sample_workflow_step.executor}_{sample_workflow_step.name}"
        # Duration is calculated in step execution


@pytest.mark.unit
@pytest.mark.asyncio
class TestWorkflowExecution:
    """Test complete workflow execution"""

    async def test_execute_workflow_success(self, initialized_coordinator):
        """Test successful workflow execution"""
        workflow_id = await initialized_coordinator.create_workflow(
            workflow_type="educational_content_generation", parameters={"subject": "math"}
        )

        # Mock all executors
        mock_result = {"content": "generated", "success": True}
        for executor_name in ["agent_system", "swarm_controller", "sparc_manager"]:
            initialized_coordinator.executor_registry[executor_name] = AsyncMock(
                return_value=mock_result
            )

        with patch.object(
            initialized_coordinator, "_record_execution_metrics", new_callable=AsyncMock
        ):
            result = await initialized_coordinator.execute_workflow(workflow_id)

        assert result["workflow_id"] == workflow_id
        workflow = initialized_coordinator.workflows[workflow_id]
        assert workflow.status == WorkflowStatus.COMPLETED
        assert workflow.start_time is not None
        assert workflow.end_time is not None

    async def test_execute_workflow_not_found(self, initialized_coordinator):
        """Test execution of non-existent workflow"""
        with pytest.raises(ValueError, match="Workflow .* not found"):
            await initialized_coordinator.execute_workflow("nonexistent_id")

    async def test_execute_workflow_with_dependencies(self, initialized_coordinator):
        """Test workflow execution respects step dependencies"""
        # Create a workflow with dependencies
        workflow_id = await initialized_coordinator.create_workflow(
            workflow_type="educational_content_generation", parameters={"subject": "science"}
        )

        workflow = initialized_coordinator.workflows[workflow_id]
        execution_order = []

        async def tracking_executor(step):
            execution_order.append(step.name)
            return {"result": f"completed {step.name}"}

        for executor_name in ["agent_system", "swarm_controller", "sparc_manager"]:
            initialized_coordinator.executor_registry[executor_name] = tracking_executor

        with patch.object(
            initialized_coordinator, "_record_execution_metrics", new_callable=AsyncMock
        ):
            await initialized_coordinator.execute_workflow(workflow_id)

        # Verify dependency order (steps with dependencies should execute after their dependencies)
        # In educational_content_generation template:
        # - Curriculum Analysis has no dependencies
        # - Environment Planning depends on Curriculum Analysis
        # etc.
        curriculum_idx = execution_order.index("Curriculum Analysis")
        environment_idx = execution_order.index("Environment Planning")
        assert curriculum_idx < environment_idx

    async def test_execute_workflow_with_failed_step(self, initialized_coordinator):
        """Test workflow execution with failed step"""
        workflow_id = await initialized_coordinator.create_workflow(
            workflow_type="educational_content_generation", parameters={"subject": "math"}
        )

        # Make one executor fail
        initialized_coordinator.executor_registry["agent_system"] = AsyncMock(
            side_effect=RuntimeError("Step execution failed")
        )
        initialized_coordinator.executor_registry["swarm_controller"] = AsyncMock(
            return_value={"result": "success"}
        )
        initialized_coordinator.executor_registry["sparc_manager"] = AsyncMock(
            return_value={"result": "success"}
        )

        with patch.object(
            initialized_coordinator, "_record_execution_metrics", new_callable=AsyncMock
        ):
            with pytest.raises(RuntimeError):
                await initialized_coordinator.execute_workflow(workflow_id)

        workflow = initialized_coordinator.workflows[workflow_id]
        assert workflow.status == WorkflowStatus.FAILED
        assert workflow.error is not None

    async def test_execute_workflow_parallel_steps(self, initialized_coordinator):
        """Test parallel execution of independent steps"""
        workflow_id = await initialized_coordinator.create_workflow(
            workflow_type="educational_content_generation", parameters={"subject": "history"}
        )

        concurrent_steps = []

        async def track_concurrent_execution(step):
            concurrent_steps.append(step.name)
            await asyncio.sleep(0.1)  # Simulate work
            return {"result": f"completed {step.name}"}

        for executor_name in ["agent_system", "swarm_controller", "sparc_manager"]:
            initialized_coordinator.executor_registry[executor_name] = track_concurrent_execution

        with patch.object(
            initialized_coordinator, "_record_execution_metrics", new_callable=AsyncMock
        ):
            await initialized_coordinator.execute_workflow(workflow_id)

        workflow = initialized_coordinator.workflows[workflow_id]
        assert workflow.status == WorkflowStatus.COMPLETED

    async def test_execute_workflow_marks_as_running(self, initialized_coordinator):
        """Test workflow is marked as running during execution"""
        workflow_id = await initialized_coordinator.create_workflow(
            workflow_type="educational_content_generation", parameters={"subject": "biology"}
        )

        execution_started = asyncio.Event()

        async def slow_executor(step):
            execution_started.set()
            await asyncio.sleep(0.2)
            return {"result": "success"}

        for executor_name in ["agent_system", "swarm_controller", "sparc_manager"]:
            initialized_coordinator.executor_registry[executor_name] = slow_executor

        # Start execution in background
        task = asyncio.create_task(initialized_coordinator.execute_workflow(workflow_id))

        # Wait for execution to start
        await execution_started.wait()

        # Check workflow is in active workflows
        assert workflow_id in initialized_coordinator.active_workflows

        # Wait for completion
        await task

        # Should be removed from active after completion
        assert workflow_id not in initialized_coordinator.active_workflows

    async def test_execute_workflow_records_metrics(self, initialized_coordinator):
        """Test workflow execution records metrics"""
        workflow_id = await initialized_coordinator.create_workflow(
            workflow_type="educational_content_generation", parameters={"subject": "chemistry"}
        )

        for executor_name in ["agent_system", "swarm_controller", "sparc_manager"]:
            initialized_coordinator.executor_registry[executor_name] = AsyncMock(
                return_value={"result": "success"}
            )

        with patch.object(
            initialized_coordinator, "_record_execution_metrics", new_callable=AsyncMock
        ) as mock_record:
            await initialized_coordinator.execute_workflow(workflow_id)

            mock_record.assert_called_once()
            recorded_workflow = mock_record.call_args[0][0]
            assert recorded_workflow.workflow_id == workflow_id


@pytest.mark.unit
@pytest.mark.asyncio
class TestWorkflowControl:
    """Test workflow control operations (pause, resume, cancel)"""

    async def test_cancel_workflow_success(self, initialized_coordinator, sample_workflow):
        """Test successful workflow cancellation"""
        workflow_id = sample_workflow.workflow_id
        sample_workflow.status = WorkflowStatus.RUNNING

        initialized_coordinator.workflows[workflow_id] = sample_workflow
        initialized_coordinator.active_workflows.add(workflow_id)

        result = await initialized_coordinator.cancel_workflow(workflow_id)

        assert result is True
        assert sample_workflow.status == WorkflowStatus.CANCELLED
        assert sample_workflow.end_time is not None
        assert workflow_id not in initialized_coordinator.active_workflows

    async def test_cancel_workflow_not_found(self, initialized_coordinator):
        """Test cancellation of non-existent workflow"""
        result = await initialized_coordinator.cancel_workflow("nonexistent_id")

        assert result is False

    async def test_cancel_workflow_not_running(self, initialized_coordinator, sample_workflow):
        """Test cancellation of non-running workflow"""
        workflow_id = sample_workflow.workflow_id
        sample_workflow.status = WorkflowStatus.PENDING

        initialized_coordinator.workflows[workflow_id] = sample_workflow

        result = await initialized_coordinator.cancel_workflow(workflow_id)

        assert result is False
        assert sample_workflow.status == WorkflowStatus.PENDING

    async def test_cancel_workflow_cancels_running_steps(
        self, initialized_coordinator, sample_workflow
    ):
        """Test cancellation marks running steps as skipped"""
        workflow_id = sample_workflow.workflow_id
        sample_workflow.status = WorkflowStatus.RUNNING

        # Add running step
        running_step = WorkflowStep(
            step_id="running_step",
            name="Running Step",
            description="A running step",
            executor="agent_system",
            parameters={},
            status=StepStatus.RUNNING,
        )
        sample_workflow.steps.append(running_step)

        initialized_coordinator.workflows[workflow_id] = sample_workflow
        initialized_coordinator.active_workflows.add(workflow_id)

        await initialized_coordinator.cancel_workflow(workflow_id)

        assert running_step.status == StepStatus.SKIPPED
        assert running_step.end_time is not None

    async def test_pause_workflow_success(self, initialized_coordinator, sample_workflow):
        """Test successful workflow pause"""
        workflow_id = sample_workflow.workflow_id
        sample_workflow.status = WorkflowStatus.RUNNING

        initialized_coordinator.workflows[workflow_id] = sample_workflow

        result = await initialized_coordinator.pause_workflow(workflow_id)

        assert result is True
        assert sample_workflow.status == WorkflowStatus.PAUSED

    async def test_pause_workflow_not_running(self, initialized_coordinator, sample_workflow):
        """Test pause of non-running workflow"""
        workflow_id = sample_workflow.workflow_id
        sample_workflow.status = WorkflowStatus.PENDING

        initialized_coordinator.workflows[workflow_id] = sample_workflow

        result = await initialized_coordinator.pause_workflow(workflow_id)

        assert result is False

    async def test_resume_workflow_success(self, initialized_coordinator, sample_workflow):
        """Test successful workflow resume"""
        workflow_id = sample_workflow.workflow_id
        sample_workflow.status = WorkflowStatus.PAUSED

        initialized_coordinator.workflows[workflow_id] = sample_workflow

        result = await initialized_coordinator.resume_workflow(workflow_id)

        assert result is True
        assert sample_workflow.status == WorkflowStatus.RUNNING

    async def test_resume_workflow_not_paused(self, initialized_coordinator, sample_workflow):
        """Test resume of non-paused workflow"""
        workflow_id = sample_workflow.workflow_id
        sample_workflow.status = WorkflowStatus.RUNNING

        initialized_coordinator.workflows[workflow_id] = sample_workflow

        result = await initialized_coordinator.resume_workflow(workflow_id)

        assert result is False


@pytest.mark.unit
@pytest.mark.asyncio
class TestWorkflowStatus:
    """Test workflow status retrieval"""

    async def test_get_workflow_status_success(self, initialized_coordinator, sample_workflow):
        """Test successful status retrieval"""
        workflow_id = sample_workflow.workflow_id
        sample_workflow.status = WorkflowStatus.RUNNING

        # Set step statuses
        sample_workflow.steps[0].status = StepStatus.COMPLETED
        sample_workflow.steps[0].duration = 10.5

        initialized_coordinator.workflows[workflow_id] = sample_workflow

        status = await initialized_coordinator.get_workflow_status(workflow_id)

        assert status["workflow_id"] == workflow_id
        assert status["name"] == sample_workflow.name
        assert status["status"] == WorkflowStatus.RUNNING.value
        assert status["progress"] == sample_workflow.progress
        assert len(status["steps"]) == len(sample_workflow.steps)

    async def test_get_workflow_status_not_found(self, initialized_coordinator):
        """Test status retrieval for non-existent workflow"""
        with pytest.raises(ValueError, match="Workflow .* not found"):
            await initialized_coordinator.get_workflow_status("nonexistent_id")

    async def test_get_workflow_status_includes_step_details(
        self, initialized_coordinator, sample_workflow
    ):
        """Test status includes detailed step information"""
        workflow_id = sample_workflow.workflow_id

        # Set detailed step info
        sample_workflow.steps[0].status = StepStatus.FAILED
        sample_workflow.steps[0].error = "Test error"
        sample_workflow.steps[0].duration = 5.2

        initialized_coordinator.workflows[workflow_id] = sample_workflow

        status = await initialized_coordinator.get_workflow_status(workflow_id)

        step_status = status["steps"][0]
        assert step_status["name"] == sample_workflow.steps[0].name
        assert step_status["status"] == StepStatus.FAILED.value
        assert step_status["error"] == "Test error"
        assert step_status["duration"] == 5.2


@pytest.mark.unit
@pytest.mark.asyncio
class TestBackgroundTasks:
    """Test background task operations"""

    async def test_workflow_executor_processes_queue(self, initialized_coordinator):
        """Test executor processes queued workflows"""
        initialized_coordinator.is_initialized = True
        initialized_coordinator.max_concurrent_workflows = 2

        # Create workflows
        wf1_id = await initialized_coordinator.create_workflow(
            workflow_type="educational_content_generation", parameters={"subject": "math"}
        )

        # Mock execute_workflow
        with patch.object(
            initialized_coordinator, "execute_workflow", new_callable=AsyncMock
        ) as mock_execute:
            # Run one iteration of executor
            with patch("asyncio.sleep", new_callable=AsyncMock):
                task = asyncio.create_task(initialized_coordinator._workflow_executor())

                # Give it time to process
                await asyncio.sleep(0.1)

                # Stop task
                initialized_coordinator.is_initialized = False
                await asyncio.sleep(0.1)
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    async def test_workflow_executor_respects_concurrency_limit(self, initialized_coordinator):
        """Test executor respects max concurrent workflows"""
        initialized_coordinator.is_initialized = True
        initialized_coordinator.max_concurrent_workflows = 1

        # Fill active workflows
        initialized_coordinator.active_workflows.add("active_workflow_1")

        # Create workflow
        await initialized_coordinator.create_workflow(
            workflow_type="educational_content_generation", parameters={"subject": "science"}
        )

        with patch.object(
            initialized_coordinator, "execute_workflow", new_callable=AsyncMock
        ) as mock_execute:
            with patch("asyncio.sleep", new_callable=AsyncMock):
                # Run one iteration - should not execute because at limit
                task = asyncio.create_task(initialized_coordinator._workflow_executor())
                await asyncio.sleep(0.1)

                initialized_coordinator.is_initialized = False
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    async def test_workflow_optimizer_runs_periodically(self, initialized_coordinator):
        """Test optimizer runs periodically"""
        initialized_coordinator.is_initialized = True

        with patch.object(
            initialized_coordinator, "_analyze_step_performance", new_callable=AsyncMock
        ) as mock_analyze:
            with patch.object(
                initialized_coordinator, "_optimize_templates", new_callable=AsyncMock
            ) as mock_optimize:
                with patch.object(
                    initialized_coordinator, "_cleanup_old_data", new_callable=AsyncMock
                ) as mock_cleanup:
                    with patch("asyncio.sleep", new_callable=AsyncMock):
                        task = asyncio.create_task(initialized_coordinator._workflow_optimizer())

                        # Give it time to run
                        await asyncio.sleep(0.1)

                        initialized_coordinator.is_initialized = False
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass


@pytest.mark.unit
@pytest.mark.asyncio
class TestMetricsAndOptimization:
    """Test metrics collection and optimization"""

    async def test_get_metrics_success(self, initialized_coordinator):
        """Test metrics retrieval"""
        # Create some workflows
        wf1 = await initialized_coordinator.create_workflow(
            workflow_type="educational_content_generation", parameters={"subject": "math"}
        )

        workflow = initialized_coordinator.workflows[wf1]
        workflow.status = WorkflowStatus.COMPLETED
        workflow.start_time = datetime.now() - timedelta(seconds=100)
        workflow.end_time = datetime.now()

        metrics = await initialized_coordinator.get_metrics()

        assert metrics["total_workflows"] == 1
        assert metrics["completed_workflows"] == 1
        assert metrics["failed_workflows"] == 0
        assert metrics["success_rate"] == 1.0
        assert metrics["queued_workflows"] >= 0

    async def test_record_execution_metrics(self, initialized_coordinator, sample_workflow):
        """Test execution metrics recording"""
        sample_workflow.status = WorkflowStatus.COMPLETED
        sample_workflow.start_time = datetime.now() - timedelta(seconds=50)
        sample_workflow.end_time = datetime.now()

        # Set steps as completed
        for step in sample_workflow.steps:
            step.status = StepStatus.COMPLETED

        await initialized_coordinator._record_execution_metrics(sample_workflow)

        assert len(initialized_coordinator.execution_metrics["workflow_executions"]) == 1
        assert len(initialized_coordinator.execution_metrics["successful_workflows"]) == 1

        metrics = initialized_coordinator.execution_metrics["workflow_executions"][0]
        assert metrics["workflow_id"] == sample_workflow.workflow_id
        assert metrics["success"] is True

    async def test_record_execution_metrics_failed_workflow(
        self, initialized_coordinator, sample_workflow
    ):
        """Test metrics recording for failed workflow"""
        sample_workflow.status = WorkflowStatus.FAILED
        sample_workflow.start_time = datetime.now() - timedelta(seconds=30)
        sample_workflow.end_time = datetime.now()

        await initialized_coordinator._record_execution_metrics(sample_workflow)

        assert len(initialized_coordinator.execution_metrics["failed_workflows"]) == 1

    async def test_analyze_step_performance(self, initialized_coordinator):
        """Test step performance analysis"""
        # Add performance data
        initialized_coordinator.step_performance["agent_system_Content Generation"] = 150.5
        initialized_coordinator.step_performance["swarm_controller_Script Generation"] = 400.2

        await initialized_coordinator._analyze_step_performance()

        analysis = initialized_coordinator.optimization_data["step_performance"]
        assert "agent_system" in analysis
        assert "swarm_controller" in analysis

    async def test_optimize_templates(self, initialized_coordinator):
        """Test template optimization"""
        # Create multiple completed workflows
        for i in range(6):
            wf_id = await initialized_coordinator.create_workflow(
                workflow_type="educational_content_generation",
                parameters={"subject": f"subject_{i}"},
            )

            workflow = initialized_coordinator.workflows[wf_id]
            workflow.status = WorkflowStatus.COMPLETED if i < 5 else WorkflowStatus.FAILED
            workflow.start_time = datetime.now() - timedelta(seconds=1000)
            workflow.end_time = datetime.now()

        await initialized_coordinator._optimize_templates()

        # Should have optimization data for template
        assert (
            "educational_content_generation"
            in initialized_coordinator.optimization_data["templates"]
        )

    async def test_cleanup_old_data(self, initialized_coordinator):
        """Test cleanup of old workflow data"""
        # Create old workflows
        old_time = datetime.now() - timedelta(days=10)

        for i in range(3):
            wf_id = f"old_workflow_{i}"
            workflow = Workflow(
                workflow_id=wf_id,
                name="Old Workflow",
                description="Old workflow",
                workflow_type="test",
                steps=[],
                parameters={},
                status=WorkflowStatus.COMPLETED,
                end_time=old_time,
            )
            initialized_coordinator.workflows[wf_id] = workflow

        # Create recent workflow
        recent_wf = Workflow(
            workflow_id="recent_workflow",
            name="Recent Workflow",
            description="Recent workflow",
            workflow_type="test",
            steps=[],
            parameters={},
            status=WorkflowStatus.COMPLETED,
            end_time=datetime.now(),
        )
        initialized_coordinator.workflows["recent_workflow"] = recent_wf

        await initialized_coordinator._cleanup_old_data()

        # Old workflows should be removed
        assert "old_workflow_0" not in initialized_coordinator.workflows
        assert "old_workflow_1" not in initialized_coordinator.workflows
        assert "old_workflow_2" not in initialized_coordinator.workflows

        # Recent workflow should remain
        assert "recent_workflow" in initialized_coordinator.workflows

    async def test_calculate_avg_execution_time(self, initialized_coordinator):
        """Test average execution time calculation"""
        # Create workflows with known durations
        for i, duration in enumerate([100, 200, 300]):
            wf = Workflow(
                workflow_id=f"wf_{i}",
                name="Test Workflow",
                description="Test",
                workflow_type="test",
                steps=[],
                parameters={},
                status=WorkflowStatus.COMPLETED,
                start_time=datetime.now() - timedelta(seconds=duration),
                end_time=datetime.now(),
            )
            initialized_coordinator.workflows[f"wf_{i}"] = wf

        avg_time = initialized_coordinator._calculate_avg_execution_time()

        # Average of 100, 200, 300 is 200
        assert 195 <= avg_time <= 205  # Allow small variance


@pytest.mark.unit
@pytest.mark.asyncio
class TestHealthCheck:
    """Test health check functionality"""

    async def test_get_health_all_healthy(self, initialized_coordinator):
        """Test health check with all executors healthy"""
        # Mock all executors to succeed
        for executor_name in ["agent_system", "swarm_controller", "sparc_manager"]:
            initialized_coordinator.executor_registry[executor_name] = AsyncMock(
                return_value={"status": "ok"}
            )

        health = await initialized_coordinator.get_health()

        assert health["status"] == "healthy"
        assert all(status == "healthy" for status in health["executor_health"].values())

    async def test_get_health_degraded(self, initialized_coordinator):
        """Test health check with some unhealthy executors"""
        # Mock executors with one failing
        initialized_coordinator.executor_registry["agent_system"] = AsyncMock(
            return_value={"status": "ok"}
        )
        initialized_coordinator.executor_registry["swarm_controller"] = AsyncMock(
            side_effect=RuntimeError("Failed")
        )
        initialized_coordinator.executor_registry["sparc_manager"] = AsyncMock(
            return_value={"status": "ok"}
        )

        health = await initialized_coordinator.get_health()

        assert health["status"] == "degraded"  # Less than half unhealthy
        assert health["executor_health"]["swarm_controller"] == "unhealthy"

    async def test_get_health_unhealthy(self, initialized_coordinator):
        """Test health check with majority executors unhealthy"""
        # Mock executors with majority failing
        initialized_coordinator.executor_registry["agent_system"] = AsyncMock(
            side_effect=RuntimeError("Failed")
        )
        initialized_coordinator.executor_registry["swarm_controller"] = AsyncMock(
            side_effect=RuntimeError("Failed")
        )
        initialized_coordinator.executor_registry["sparc_manager"] = AsyncMock(
            return_value={"status": "ok"}
        )

        health = await initialized_coordinator.get_health()

        assert health["status"] == "unhealthy"  # More than half unhealthy

    async def test_get_health_includes_queue_info(self, initialized_coordinator):
        """Test health check includes queue information"""
        # Add some workflows
        await initialized_coordinator.create_workflow(
            workflow_type="educational_content_generation", parameters={"subject": "math"}
        )

        for executor_name in ["agent_system", "swarm_controller", "sparc_manager"]:
            initialized_coordinator.executor_registry[executor_name] = AsyncMock(
                return_value={"status": "ok"}
            )

        health = await initialized_coordinator.get_health()

        assert "queue_length" in health
        assert health["queue_length"] >= 1


@pytest.mark.unit
@pytest.mark.asyncio
class TestFastAPIRoutes:
    """Test FastAPI route registration"""

    async def test_routes_registered(self, workflow_coordinator):
        """Test all routes are registered"""
        routes = [route.path for route in workflow_coordinator.app.routes]

        assert "/workflows" in routes
        assert "/templates" in routes
        assert "/metrics" in routes
        assert "/health" in routes

    async def test_workflow_routes_registered(self, workflow_coordinator):
        """Test workflow-specific routes"""
        routes = [route.path for route in workflow_coordinator.app.routes]

        # Check for workflow ID routes
        workflow_routes = [r for r in routes if "workflows/{workflow_id}" in r]
        assert len(workflow_routes) >= 4  # get, cancel, pause, resume


@pytest.mark.unit
@pytest.mark.asyncio
class TestDataClasses:
    """Test WorkflowStep and Workflow dataclass properties"""

    def test_workflow_step_duration_calculation(self):
        """Test step duration calculation"""
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=50)

        step = WorkflowStep(
            step_id="test",
            name="Test",
            description="Test",
            executor="agent",
            parameters={},
            start_time=start_time,
            end_time=end_time,
        )

        assert step.duration is not None
        assert 49 <= step.duration <= 51  # Allow small variance

    def test_workflow_step_duration_none_without_times(self):
        """Test duration is None without start/end times"""
        step = WorkflowStep(
            step_id="test", name="Test", description="Test", executor="agent", parameters={}
        )

        assert step.duration is None

    def test_workflow_duration_calculation(self):
        """Test workflow duration calculation"""
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=120)

        workflow = Workflow(
            workflow_id="test",
            name="Test",
            description="Test",
            workflow_type="test",
            steps=[],
            parameters={},
            start_time=start_time,
            end_time=end_time,
        )

        assert workflow.duration is not None
        assert 119 <= workflow.duration <= 121

    def test_workflow_progress_calculation(self):
        """Test workflow progress calculation"""
        steps = [
            WorkflowStep(
                step_id=f"step_{i}",
                name=f"Step {i}",
                description="Test",
                executor="agent",
                parameters={},
                status=StepStatus.COMPLETED if i < 3 else StepStatus.PENDING,
            )
            for i in range(5)
        ]

        workflow = Workflow(
            workflow_id="test",
            name="Test",
            description="Test",
            workflow_type="test",
            steps=steps,
            parameters={},
        )

        # 3 out of 5 completed = 60%
        assert workflow.progress == 60.0

    def test_workflow_progress_zero_steps(self):
        """Test progress with no steps"""
        workflow = Workflow(
            workflow_id="test",
            name="Test",
            description="Test",
            workflow_type="test",
            steps=[],
            parameters={},
        )

        assert workflow.progress == 0.0


@pytest.mark.unit
@pytest.mark.asyncio
class TestWorkflowTemplates:
    """Test workflow template functionality"""

    def test_workflow_template_creation(self):
        """Test workflow template creation"""
        template = WorkflowTemplate(
            name="Test Template",
            description="A test template",
            steps=[
                {
                    "name": "Step 1",
                    "description": "First step",
                    "executor": "agent_system",
                    "parameters": {"key": "value"},
                }
            ],
        )

        assert template.name == "Test Template"
        assert len(template.step_templates) == 1

    def test_template_create_workflow(self):
        """Test creating workflow from template"""
        template = WorkflowTemplate(
            name="Test Template",
            description="A test template",
            steps=[
                {
                    "name": "Step 1",
                    "description": "First step",
                    "executor": "agent_system",
                    "parameters": {"key": "value"},
                    "timeout": 200,
                    "retry_count": 5,
                },
                {
                    "name": "Step 2",
                    "description": "Second step",
                    "executor": "swarm_controller",
                    "parameters": {},
                    "dependencies": ["step_1"],
                },
            ],
        )

        workflow = template.create_workflow(workflow_id="test_wf", parameters={"subject": "math"})

        assert workflow.workflow_id == "test_wf"
        assert workflow.name == "Test Template"
        assert len(workflow.steps) == 2

        # Check first step
        assert workflow.steps[0].name == "Step 1"
        assert workflow.steps[0].timeout == 200
        assert workflow.steps[0].retry_count == 5
        assert workflow.steps[0].parameters["key"] == "value"
        assert workflow.steps[0].parameters["subject"] == "math"  # Merged from workflow params

        # Check second step
        assert workflow.steps[1].dependencies == ["step_1"]

    def test_default_templates_exist(self, workflow_coordinator):
        """Test default templates are created"""
        assert "educational_content_generation" in workflow_coordinator.templates
        assert "complete_course_generation" in workflow_coordinator.templates
        assert "adaptive_assessment_generation" in workflow_coordinator.templates

    def test_educational_content_template_structure(self, workflow_coordinator):
        """Test educational content generation template"""
        template = workflow_coordinator.templates["educational_content_generation"]

        assert template.name == "Educational Content Generation"
        assert len(template.step_templates) == 6  # Predefined steps

        # Check step names
        step_names = [step["name"] for step in template.step_templates]
        assert "Curriculum Analysis" in step_names
        assert "Environment Planning" in step_names
        assert "Quality Assurance" in step_names


@pytest.mark.unit
@pytest.mark.asyncio
class TestWorkflowResultAssembly:
    """Test workflow result assembly"""

    async def test_assemble_workflow_result(self, initialized_coordinator):
        """Test assembling final workflow result"""
        workflow = Workflow(
            workflow_id="test_wf",
            name="Test Workflow",
            description="Test",
            workflow_type="test",
            steps=[
                WorkflowStep(
                    step_id="step_1",
                    name="Step 1",
                    description="Test",
                    executor="agent",
                    parameters={},
                    status=StepStatus.COMPLETED,
                    result={"content": {"data": "step1_data"}},
                ),
                WorkflowStep(
                    step_id="step_2",
                    name="Content Integration",
                    description="Test",
                    executor="agent",
                    parameters={},
                    status=StepStatus.COMPLETED,
                    result={"final_output": "assembled_content"},
                ),
            ],
            parameters={"subject": "math"},
            start_time=datetime.now() - timedelta(seconds=100),
            end_time=datetime.now(),
        )

        result = await initialized_coordinator._assemble_workflow_result(workflow)

        assert result["workflow_id"] == "test_wf"
        assert result["name"] == "Test Workflow"
        assert result["success"] is True
        assert result["steps_completed"] == 2
        assert result["total_steps"] == 2

        # Check step results
        assert "Step 1" in result["step_results"]
        assert "Content Integration" in result["step_results"]

        # Check final content
        assert result["final_content"]["final_output"] == "assembled_content"


@pytest.mark.unit
@pytest.mark.asyncio
class TestShutdownAndCleanup:
    """Test coordinator shutdown"""

    async def test_shutdown_cancels_background_tasks(self, initialized_coordinator):
        """Test shutdown cancels background tasks"""
        # Create mock tasks
        initialized_coordinator.executor_task = AsyncMock()
        initialized_coordinator.optimizer_task = AsyncMock()

        await initialized_coordinator.shutdown()

        initialized_coordinator.executor_task.cancel.assert_called_once()
        initialized_coordinator.optimizer_task.cancel.assert_called_once()
        assert initialized_coordinator.is_initialized is False

    async def test_shutdown_cancels_active_workflows(self, initialized_coordinator):
        """Test shutdown cancels active workflows"""
        # Create active workflow
        workflow = Workflow(
            workflow_id="active_wf",
            name="Active Workflow",
            description="Test",
            workflow_type="test",
            steps=[],
            parameters={},
            status=WorkflowStatus.RUNNING,
        )

        initialized_coordinator.workflows["active_wf"] = workflow
        initialized_coordinator.active_workflows.add("active_wf")

        # Mock tasks
        initialized_coordinator.executor_task = AsyncMock()
        initialized_coordinator.optimizer_task = AsyncMock()

        await initialized_coordinator.shutdown()

        # Workflow should be cancelled
        assert workflow.status == WorkflowStatus.CANCELLED


@pytest.mark.unit
@pytest.mark.asyncio
class TestConvenienceFunctions:
    """Test convenience functions"""

    async def test_create_workflow_coordinator(self):
        """Test convenience function creates and initializes coordinator"""
        config = {"max_concurrent_workflows": 5}

        with patch.object(WorkflowCoordinator, "_setup_executors", new_callable=AsyncMock):
            with patch("asyncio.create_task"):
                coordinator = await create_workflow_coordinator(config=config)

                assert coordinator is not None
                assert isinstance(coordinator, WorkflowCoordinator)
                assert coordinator.is_initialized is True
                assert coordinator.max_concurrent_workflows == 5

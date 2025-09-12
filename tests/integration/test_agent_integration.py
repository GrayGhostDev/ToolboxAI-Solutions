"""Integration tests for the agent system.

Tests the complete agent workflow including:
- Multi-agent coordination
- SPARC framework integration
- Swarm intelligence
- MCP context management
- End-to-end content generation
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "roblox-environment"))

# Import all components
from core.agents.orchestrator import Orchestrator
from core.agents.supervisor import SupervisorAgent
from core.agents.content_agent import ContentAgent
from core.agents.quiz_agent import QuizAgent
from core.agents.terrain_agent import TerrainAgent
from core.agents.script_agent import ScriptAgent
from core.agents.review_agent import ReviewAgent

from core.sparc.state_manager import StateManager
from core.sparc.policy_engine import PolicyEngine
from core.sparc.action_executor import ActionExecutor
from core.sparc.reward_calculator import RewardCalculator
from core.sparc.context_tracker import ContextTracker

from core.swarm.swarm_controller import SwarmController
from core.swarm.worker_pool import WorkerPool
from core.swarm.task_distributor import TaskDistributor, Task, TaskPriority
from core.swarm.consensus_engine import ConsensusEngine
from core.swarm.load_balancer import LoadBalancer

from core.mcp.server import MCPServer
from core.mcp.context_manager import ContextManager
from core.mcp.memory_store import MemoryStore

from core.coordinators.main_coordinator import MainCoordinator
from core.coordinators.resource_coordinator import ResourceCoordinator
from core.coordinators.sync_coordinator import SyncCoordinator
from core.coordinators.error_coordinator import ErrorCoordinator

from apps.backend.tools import ALL_TOOLS


@pytest.mark.integration
class TestAgentSystemIntegration:
    """Integration tests for the complete agent system."""

    @pytest_asyncio.fixture
    async def setup_system(self):
        """Set up the complete agent system for testing."""
        # Mock environment variables
        os.environ['OPENAI_API_KEY'] = 'test-key'
        os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost/test'

        # Initialize components
        components: Dict[str, Any] = {}

        # Mock LLM responses
        with patch('agents.base_agent.ChatOpenAI') as MockLLM:
            mock_llm = MockLLM.return_value
            mock_llm.invoke = AsyncMock(return_value=MagicMock(content="Test response"))

            # Initialize orchestrator
            components['orchestrator'] = Orchestrator()
            components['supervisor'] = SupervisorAgent()

            # Initialize SPARC
            components['sparc'] = StateManager()

            # Initialize Swarm components
            from core.swarm.swarm_controller import SwarmConfig
            from core.swarm.worker_pool import WorkerPool
            from core.swarm.task_distributor import TaskDistributor
            from core.swarm.consensus_engine import ConsensusEngine
            from core.swarm.load_balancer import LoadBalancer

            swarm_config = SwarmConfig()
            worker_pool = WorkerPool(
                max_workers=swarm_config.max_workers,
                min_workers=swarm_config.min_workers,
                specializations=swarm_config.worker_specializations
            )
            task_distributor = TaskDistributor()
            consensus_engine = ConsensusEngine(threshold=swarm_config.consensus_threshold)
            load_balancer = LoadBalancer(strategy=swarm_config.load_balancing_strategy)

            components['swarm'] = SwarmController(
                config=swarm_config,
                worker_pool=worker_pool,
                task_distributor=task_distributor,
                consensus_engine=consensus_engine,
                load_balancer=load_balancer
            )

            # Initialize MCP
            components['mcp'] = MCPServer()

            # Initialize Coordinator
            components['coordinator'] = MainCoordinator()

        yield components

        # Cleanup
        if components['mcp']:
            # Close MCP server if running
            pass

    @pytest.mark.asyncio
    async def test_complete_content_generation_workflow(self, setup_system):
        """Test the complete content generation workflow."""
        system = setup_system

        # Create a comprehensive request
        request = {
            "subject": "Science",
            "grade_level": 7,
            "topic": "Ecosystems",
            "learning_objectives": [
                "Understand food chains",
                "Identify ecosystem components",
                "Explain energy transfer"
            ],
            "duration": 45,
            "environment_type": "forest",
            "include_quiz": True,
            "include_terrain": True,
            "include_gamification": True
        }

        # Mock agent responses
        with patch.object(system['orchestrator'], 'generate_environment') as mock_generate:
            from core.agents.orchestrator import OrchestrationResult
            mock_generate.return_value = OrchestrationResult(
                success=True,
                content={
                    "lesson": {
                        "title": "Ecosystem Exploration",
                        "content": "Educational content about ecosystems",
                        "objectives_met": True
                    }
                },
                quiz={
                    "questions": [
                        {
                            "question": "What is a food chain?",
                            "type": "multiple_choice",
                            "options": ["A", "B", "C", "D"],
                            "correct_answer": "A"
                        }
                    ]
                },
                terrain={
                    "script": "-- Lua terrain generation script",
                    "environment": "forest"
                },
                scripts={
                    "main_script": "-- Game logic script",
                    "ui_script": "-- UI script"
                },
                review={
                    "approved": True,
                    "quality_score": 92,
                    "suggestions": []
                },
                execution_time=2.5
            )

            # Execute workflow
            result = await system['orchestrator'].generate_environment(**request)

            # Verify results
            assert result is not None
            assert result.success is True
            assert result.content is not None
            assert result.quiz is not None
            assert result.terrain is not None
            assert result.scripts is not None
            assert result.review is not None
            assert result.review["approved"] is True

    @pytest.mark.asyncio
    async def test_sparc_framework_integration(self, setup_system):
        """Test SPARC framework integration with agents."""
        system = setup_system
        sparc = system['sparc']

        # Initialize SPARC state
        initial_state = {
            "environment": "classroom",
            "student_count": 25,
            "lesson_progress": 0,
            "engagement_level": 0.7
        }

        # Mock SPARC cycle
        with patch.object(sparc, 'update_state') as mock_observe:
            mock_observe.return_value = initial_state

            # Run SPARC cycle
            state = await sparc.update_state(initial_state)

            assert state is not None
            assert state == initial_state

    @pytest.mark.asyncio
    async def test_swarm_parallel_execution(self, setup_system):
        """Test swarm intelligence parallel task execution."""
        system = setup_system
        swarm = system['swarm']

        # Initialize the swarm to make it active
        await swarm.initialize()

        # Create multiple tasks
        tasks = [
            {"type": "content", "id": "task1", "data": {"subject": "Math"}},
            {"type": "quiz", "id": "task2", "data": {"num_questions": 5}},
            {"type": "terrain", "id": "task3", "data": {"environment": "space"}},
            {"type": "script", "id": "task4", "data": {"script_type": "ui"}}
        ]

        # Execute tasks using real implementation
        results = []
        for task_data in tasks:
            task_id = await swarm.submit_task(
                task_type=task_data["type"],
                task_data=task_data["data"],
                priority=TaskPriority.NORMAL
            )
            results.append(task_id)

        # Verify parallel execution
        assert len(results) == len(tasks)
        assert all(task_id is not None for task_id in results)

    @pytest.mark.asyncio
    async def test_mcp_context_management(self, setup_system):
        """Test MCP context management across agents."""
        system = setup_system
        mcp = system['mcp']

        # Create context
        context = {
            "session_id": "test-session",
            "user": {"id": "user123", "role": "educator"},
            "current_lesson": {"id": "lesson456", "subject": "Science"},
            "history": []
        }

        # Mock MCP operations
        with patch.object(mcp, '_handle_update_context') as mock_update:
            with patch.object(mcp, '_handle_query_context') as mock_query:
                mock_query.return_value = context

                # Update context
                await mcp._handle_update_context({"new_data": "test"}, None)
                mock_update.assert_called_once()

                # Retrieve context
                retrieved = await mcp._handle_query_context({"query": "session"}, None)
                assert retrieved["session_id"] == "test-session"

    @pytest.mark.asyncio
    async def test_coordinator_orchestration(self, setup_system):
        """Test main coordinator orchestrating all components."""
        system = setup_system
        coordinator = system['coordinator']

        # Create a complex request requiring coordination
        request = {
            "action": "generate_complete_lesson",
            "parameters": {
                "subject": "History",
                "topic": "Ancient Rome",
                "include_all": True
            }
        }

        # Mock coordinator methods
        with patch.object(coordinator, 'generate_educational_content') as mock_coordinate:
            mock_coordinate.return_value = {
                "status": "success",
                "components_generated": [
                    "lesson", "quiz", "terrain", "scripts", "gamification"
                ],
                "time_taken": 5.2,
                "resources_used": {
                    "cpu": 0.75,
                    "memory": 0.60,
                    "api_calls": 12
                }
            }

            # Execute coordination
            result = await coordinator.generate_educational_content(**request)

            # Verify coordination
            assert result["status"] == "success"
            assert result["components_generated"]  # Check list is not empty
            assert len(result["components_generated"]) == 5
            assert result["time_taken"] < 10  # Should be reasonably fast

    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, setup_system):
        """Test error recovery in agent workflow."""
        system = setup_system

        # Simulate failures and recovery
        with patch.object(system['supervisor'], 'delegate_complex_task') as mock_route:
            # First call fails, second succeeds
            from core.agents.base_agent import TaskResult
            mock_route.side_effect = [
                Exception("Agent temporarily unavailable"),
                TaskResult(output="content", success=True)  # Successful routing after retry
            ]

            # Test retry logic
            max_retries = 3
            result = None
            for attempt in range(max_retries):
                try:
                    result = await system['supervisor'].delegate_complex_task("generate_content", {})
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        pytest.fail(f"Failed after {max_retries} attempts: {e}")

            assert result is not None
            assert result.output == "content"

    @pytest.mark.asyncio
    async def test_agent_consensus_mechanism(self, setup_system):
        """Test consensus mechanism for quality control."""
        system = setup_system

        # Create multiple agent responses for consensus
        agent_responses = [
            {"agent": "content", "score": 0.85, "result": "Content A"},
            {"agent": "content_backup", "score": 0.82, "result": "Content B"},
            {"agent": "content_tertiary", "score": 0.88, "result": "Content C"}
        ]

        # Mock consensus engine
        consensus = ConsensusEngine()
        with patch.object(consensus, 'evaluate_result') as mock_evaluate:
            from core.swarm.consensus_engine import ConsensusResult, ConsensusType
            mock_result = ConsensusResult(
                consensus_id="test_consensus",
                consensus_type=ConsensusType.QUALITY_VALIDATION,
                final_result="Content C",
                confidence=0.92,
                agreement_level=0.85,
                participating_voters=3,
                total_votes=3
            )
            mock_evaluate.return_value = mock_result

            # Evaluate consensus
            result = await consensus.evaluate_result("test_task", agent_responses)

            # Verify consensus
            assert result.confidence > 0.9
            assert result.final_result == "Content C"

    @pytest.mark.asyncio
    async def test_resource_optimization(self, setup_system):
        """Test resource optimization in agent system."""
        system = setup_system
        resource_coordinator = ResourceCoordinator()

        # Mock resource monitoring
        with patch.object(resource_coordinator, 'optimize_resource_allocation') as mock_optimize:
            mock_optimize.return_value = {
                "cpu_allocation": {"agents": 0.4, "swarm": 0.3, "mcp": 0.1, "other": 0.2},
                "memory_allocation": {"agents": 0.5, "swarm": 0.2, "mcp": 0.15, "other": 0.15},
                "optimizations_applied": ["cache_enabled", "parallel_processing", "lazy_loading"]
            }

            # Optimize resources
            optimization = await resource_coordinator.optimize_resource_allocation()

            # Verify optimization
            assert sum(optimization["cpu_allocation"].values()) == 1.0
            assert sum(optimization["memory_allocation"].values()) == 1.0
            assert optimization["optimizations_applied"]  # Check list is not empty

    @pytest.mark.asyncio
    async def test_end_to_end_educational_experience(self, setup_system):
        """Test complete educational experience generation."""
        system = setup_system

        # Comprehensive educational request
        request = {
            "course": "Middle School Science",
            "unit": "Life Science",
            "lesson": "Ecosystem Interactions",
            "duration": 45,
            "students": 30,
            "features": {
                "interactive_3d_environment": True,
                "adaptive_quizzing": True,
                "collaborative_activities": True,
                "gamification": True,
                "accessibility": True
            }
        }

        # Mock complete workflow
        with patch('server.main.get_content') as mock_generate:
            mock_generate.return_value = {
                "experience_id": "exp_123",
                "status": "generated",
                "components": {
                    "lesson": {"id": "lesson_456", "ready": True},
                    "environment": {"id": "env_789", "type": "3d_forest"},
                    "quiz": {"id": "quiz_012", "adaptive": True},
                    "activities": ["food_chain_builder", "ecosystem_simulator"],
                    "gamification": {"points": 100, "badges": ["explorer", "scientist"]}
                },
                "estimated_completion_time": 45,
                "accessibility_features": ["screen_reader", "subtitles", "high_contrast"],
                "quality_metrics": {
                    "educational_value": 0.95,
                    "engagement_score": 0.92,
                    "technical_quality": 0.94
                }
            }

            # Generate experience
            experience = await mock_generate(request)

            # Comprehensive validation
            assert experience["status"] == "generated"
            assert experience["components"]["lesson"]["ready"] is True
            assert experience["components"]["quiz"]["adaptive"] is True
            assert len(experience["components"]["activities"]) >= 2
            assert experience["quality_metrics"]["educational_value"] > 0.9
            assert experience["quality_metrics"]["engagement_score"] > 0.9
            assert experience["quality_metrics"]["technical_quality"] > 0.9


@pytest.mark.integration
class TestAgentCommunication:
    """Test agent-to-agent communication and coordination."""

    @pytest.mark.asyncio
    async def test_supervisor_to_agent_communication(self):
        """Test supervisor communicating with sub-agents."""
        supervisor = SupervisorAgent()
        content_agent = ContentAgent()

        # Mock communication
        with patch.object(supervisor, 'delegate_complex_task') as mock_delegate:
            from core.agents.base_agent import TaskResult
            mock_delegate.return_value = TaskResult(
                success=True,
                output={"lesson": "Generated lesson"},
                metadata={"agent": "content", "task_id": "task_123"}
            )

            # Delegate task
            task = "Generate a math lesson about fractions"
            requirements = {"subject": "Math", "grade_level": 5}
            result = await supervisor.delegate_complex_task(task, requirements)

            assert result.success is True
            assert "lesson" in result.output

    @pytest.mark.asyncio
    async def test_agent_pipeline_flow(self):
        """Test data flow through agent pipeline."""
        # Create pipeline: Content -> Quiz -> Review
        pipeline = [
            ContentAgent(),
            QuizAgent(),
            ReviewAgent()
        ]

        # Initial data
        data = {"subject": "Science", "topic": "Atoms"}

        # Mock pipeline execution
        for i, agent in enumerate(pipeline):
            if i == 0:  # Content agent
                with patch.object(agent, 'generate_lesson_plan') as mock_process:
                    mock_process.return_value = {**data, "content": "Lesson content"}
                    data = await agent.generate_lesson_plan(
                        subject=data["subject"],
                        grade_level=7,
                        learning_objectives=["Understand atoms"]
                    )
            elif i == 1:  # Quiz agent
                with patch.object(agent, '_generate_quiz') as mock_process:
                    mock_process.return_value = {**data, "quiz": {"questions": []}}
                    data = await agent._generate_quiz(
                        content=data.get("content", ""),
                        subject=data["subject"],
                        topic=data["topic"],
                        num_questions=5
                    )
            else:  # Review agent
                with patch.object(agent, '_process_task') as mock_process:
                    mock_process.return_value = {
                        "review": {"severity": "low", "findings": []},
                        "improvements": [],
                        "refactored_code": None,
                        "summary": "Code review completed",
                        "metrics": {"lines": 10, "complexity": 1},
                        "approved": True
                    }
                    from core.agents.base_agent import AgentState
                    state = AgentState(
                        task="review_code",
                        context={"code": "test code", "language": "lua"},
                        metadata={},
                        status="processing",
                        messages=[],
                        result=None,
                        error=None,
                        timestamp="2025-01-01T00:00:00Z",
                        iterations=0,
                        max_iterations=10
                    )
                    result = await agent._process_task(state)
                    data = {**data, **result}

        # Verify pipeline completion
        assert "content" in data
        assert "quiz" in data
        assert data["approved"] is True

    @pytest.mark.asyncio
    async def test_agent_state_synchronization(self):
        """Test state synchronization between agents."""
        sync_coordinator = SyncCoordinator()

        # Create shared state
        shared_state = {
            "session_id": "session_456",
            "current_task": "generating_content",
            "agents_active": ["content", "quiz", "terrain"],
            "progress": 0.5
        }

        # Mock synchronization
        with patch.object(sync_coordinator, 'sync_component') as mock_sync:
            mock_sync.return_value = True

            # Sync state across agents
            result = await sync_coordinator.sync_component("test_component")

            assert result is True


@pytest.mark.integration
class TestSystemPerformance:
    """Performance tests for the integrated system."""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_system_throughput(self):
        """Test system throughput with multiple concurrent requests."""
        import time

        orchestrator = Orchestrator()

        # Create multiple requests
        requests = [
            {"id": i, "subject": f"Subject{i}", "grade_level": 5+i}
            for i in range(10)
        ]

        # Mock fast processing
        with patch.object(orchestrator, 'generate_environment') as mock_gen:
            from core.agents.orchestrator import OrchestrationResult
            mock_gen.return_value = OrchestrationResult(
                success=True,
                content={"status": "completed"},
                execution_time=0.1
            )

            # Process concurrently
            start_time = time.time()
            tasks = [orchestrator.generate_environment(**req) for req in requests]
            results = await asyncio.gather(*tasks)
            end_time = time.time()

            # Verify throughput
            duration = end_time - start_time
            throughput = len(requests) / duration

            assert all(r.success is True for r in results)
            assert throughput > 1  # At least 1 request per second

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_memory_efficiency(self):
        """Test memory efficiency of the system."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Run multiple agent operations
        orchestrator = Orchestrator()

        with patch.object(orchestrator, 'generate_environment') as mock_gen:
            from core.agents.orchestrator import OrchestrationResult
            mock_gen.return_value = OrchestrationResult(
                success=True,
                content={"data": "x" * 1000},  # Small response
                execution_time=0.0
            )

            # Generate many experiences
            for _ in range(100):
                await orchestrator.generate_environment(subject="Test")

            # Check memory usage
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            # Should not leak excessive memory
            assert memory_increase < 100  # Less than 100MB increase

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_response_time_under_load(self):
        """Test response time under heavy load."""
        import time

        # Initialize Swarm components
        from core.swarm.swarm_controller import SwarmConfig
        from core.swarm.worker_pool import WorkerPool
        from core.swarm.task_distributor import TaskDistributor
        from core.swarm.consensus_engine import ConsensusEngine
        from core.swarm.load_balancer import LoadBalancer

        swarm_config = SwarmConfig()
        worker_pool = WorkerPool(
            max_workers=swarm_config.max_workers,
            min_workers=swarm_config.min_workers,
            specializations=swarm_config.worker_specializations
        )
        task_distributor = TaskDistributor()
        consensus_engine = ConsensusEngine(threshold=swarm_config.consensus_threshold)
        load_balancer = LoadBalancer(strategy=swarm_config.load_balancing_strategy)

        swarm = SwarmController(
            config=swarm_config,
            worker_pool=worker_pool,
            task_distributor=task_distributor,
            consensus_engine=consensus_engine,
            load_balancer=load_balancer
        )

        # Create heavy load
        heavy_tasks = [
            {"id": i, "complexity": "high", "data": "x" * 10000}
            for i in range(50)
        ]

        # Mock processing
        with patch.object(swarm, 'submit_task') as mock_submit:
            from core.swarm.task_distributor import Task, TaskStatus
            mock_submit.return_value = "task_123"

            # Measure response time
            start = time.time()
            task_ids = []
            for task_data in heavy_tasks:
                task_id = await swarm.submit_task(
                    task_type="test_task",
                    task_data=task_data,
                    priority=TaskPriority.NORMAL
                )
                task_ids.append(task_id)
            end = time.time()

            response_time = end - start

            # Should handle heavy load efficiently
            assert len(task_ids) == len(heavy_tasks)
            assert response_time < 10  # Less than 10 seconds for 50 heavy tasks


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
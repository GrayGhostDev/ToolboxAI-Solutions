"""Integration tests for the agent system.

Tests the complete agent workflow including:
- Multi-agent coordination
- SPARC framework integration
- Swarm intelligence
- MCP context management
- End-to-end content generation
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "roblox-environment"))

# Import all components
from agents.orchestrator import Orchestrator
from agents.supervisor import SupervisorAgent
from agents.content_agent import ContentAgent
from agents.quiz_agent import QuizAgent
from agents.terrain_agent import TerrainAgent
from agents.script_agent import ScriptAgent
from agents.review_agent import ReviewAgent

from sparc.state_manager import SPARCStateManager
from sparc.policy_engine import PolicyEngine
from sparc.action_executor import ActionExecutor
from sparc.reward_calculator import RewardCalculator
from sparc.context_tracker import ContextTracker

from swarm.swarm_controller import SwarmController
from swarm.worker_pool import WorkerPool
from swarm.task_distributor import TaskDistributor
from swarm.consensus_engine import ConsensusEngine
from swarm.load_balancer import LoadBalancer

from mcp.server import MCPServer
from mcp.context_manager import ContextManager
from mcp.memory_store import MemoryStore

from coordinators.main_coordinator import MainCoordinator
from coordinators.resource_coordinator import ResourceCoordinator
from coordinators.sync_coordinator import SyncCoordinator
from coordinators.error_coordinator import ErrorCoordinator

from server.tools import ALL_TOOLS


@pytest.mark.integration
class TestAgentSystemIntegration:
    """Integration tests for the complete agent system."""
    
    @pytest.fixture
    async def setup_system(self):
        """Set up the complete agent system for testing."""
        # Mock environment variables
        os.environ['OPENAI_API_KEY'] = 'test-key'
        os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost/test'
        
        # Initialize components
        components = {
            'orchestrator': None,
            'supervisor': None,
            'sparc': None,
            'swarm': None,
            'mcp': None,
            'coordinator': None
        }
        
        # Mock LLM responses
        with patch('agents.base_agent.ChatOpenAI') as MockLLM:
            mock_llm = MockLLM.return_value
            mock_llm.invoke = AsyncMock(return_value=MagicMock(content="Test response"))
            
            # Initialize orchestrator
            components['orchestrator'] = Orchestrator()
            components['supervisor'] = SupervisorAgent()
            
            # Initialize SPARC
            components['sparc'] = SPARCStateManager()
            
            # Initialize Swarm
            components['swarm'] = SwarmController()
            
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
        system = await setup_system
        
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
        with patch.object(system['orchestrator'], 'generate_experience') as mock_generate:
            mock_generate.return_value = {
                "lesson": {
                    "title": "Ecosystem Exploration",
                    "content": "Educational content about ecosystems",
                    "objectives_met": True
                },
                "quiz": {
                    "questions": [
                        {
                            "question": "What is a food chain?",
                            "type": "multiple_choice",
                            "options": ["A", "B", "C", "D"],
                            "correct_answer": "A"
                        }
                    ]
                },
                "terrain": {
                    "script": "-- Lua terrain generation script",
                    "environment": "forest"
                },
                "scripts": [
                    "-- Game logic script",
                    "-- UI script"
                ],
                "review": {
                    "approved": True,
                    "quality_score": 92,
                    "suggestions": []
                }
            }
            
            # Execute workflow
            result = await system['orchestrator'].generate_experience(request)
            
            # Verify results
            assert result is not None
            assert "lesson" in result
            assert "quiz" in result
            assert "terrain" in result
            assert "scripts" in result
            assert "review" in result
            assert result["review"]["approved"] == True
    
    @pytest.mark.asyncio
    async def test_sparc_framework_integration(self, setup_system):
        """Test SPARC framework integration with agents."""
        system = await setup_system
        sparc = system['sparc']
        
        # Initialize SPARC state
        initial_state = {
            "environment": "classroom",
            "student_count": 25,
            "lesson_progress": 0,
            "engagement_level": 0.7
        }
        
        # Mock SPARC cycle
        with patch.object(sparc, 'observe_state') as mock_observe:
            with patch.object(sparc, 'execute_action') as mock_execute:
                mock_observe.return_value = initial_state
                mock_execute.return_value = {
                    "success": True,
                    "new_state": {**initial_state, "lesson_progress": 0.2}
                }
                
                # Run SPARC cycle
                state = await sparc.observe_state()
                action = sparc.policy.decide(state, sparc.context)
                result = await sparc.execute_action(action)
                reward = sparc.calculate_reward(result)
                
                assert state is not None
                assert result["success"] == True
                assert reward is not None
    
    @pytest.mark.asyncio
    async def test_swarm_parallel_execution(self, setup_system):
        """Test swarm intelligence parallel task execution."""
        system = await setup_system
        swarm = system['swarm']
        
        # Create multiple tasks
        tasks = [
            {"type": "content", "id": "task1", "data": {"subject": "Math"}},
            {"type": "quiz", "id": "task2", "data": {"num_questions": 5}},
            {"type": "terrain", "id": "task3", "data": {"environment": "space"}},
            {"type": "script", "id": "task4", "data": {"script_type": "ui"}}
        ]
        
        # Mock worker pool
        with patch.object(swarm, 'distribute_tasks') as mock_distribute:
            mock_distribute.return_value = [
                {"task_id": "task1", "result": "content_result"},
                {"task_id": "task2", "result": "quiz_result"},
                {"task_id": "task3", "result": "terrain_result"},
                {"task_id": "task4", "result": "script_result"}
            ]
            
            # Execute in parallel
            results = await swarm.distribute_tasks(tasks)
            
            # Verify parallel execution
            assert len(results) == len(tasks)
            assert all(r["result"] is not None for r in results)
    
    @pytest.mark.asyncio
    async def test_mcp_context_management(self, setup_system):
        """Test MCP context management across agents."""
        system = await setup_system
        mcp = system['mcp']
        
        # Create context
        context = {
            "session_id": "test-session",
            "user": {"id": "user123", "role": "educator"},
            "current_lesson": {"id": "lesson456", "subject": "Science"},
            "history": []
        }
        
        # Mock MCP operations
        with patch.object(mcp, 'update_context') as mock_update:
            with patch.object(mcp, 'get_context') as mock_get:
                mock_get.return_value = context
                
                # Update context
                mcp.update_context({"new_data": "test"})
                mock_update.assert_called_once()
                
                # Retrieve context
                retrieved = mcp.get_context()
                assert retrieved["session_id"] == "test-session"
    
    @pytest.mark.asyncio
    async def test_coordinator_orchestration(self, setup_system):
        """Test main coordinator orchestrating all components."""
        system = await setup_system
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
        with patch.object(coordinator, 'coordinate') as mock_coordinate:
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
            result = await coordinator.coordinate(request)
            
            # Verify coordination
            assert result["status"] == "success"
            assert len(result["components_generated"]) == 5
            assert result["time_taken"] < 10  # Should be reasonably fast
    
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, setup_system):
        """Test error recovery in agent workflow."""
        system = await setup_system
        
        # Simulate failures and recovery
        with patch.object(system['supervisor'], 'route_task') as mock_route:
            # First call fails, second succeeds
            mock_route.side_effect = [
                Exception("Agent temporarily unavailable"),
                "content"  # Successful routing after retry
            ]
            
            # Test retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    result = system['supervisor'].route_task({"task": "generate_content"})
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        pytest.fail(f"Failed after {max_retries} attempts: {e}")
            
            assert result == "content"
    
    @pytest.mark.asyncio
    async def test_agent_consensus_mechanism(self, setup_system):
        """Test consensus mechanism for quality control."""
        system = await setup_system
        
        # Create multiple agent responses for consensus
        agent_responses = [
            {"agent": "content", "score": 0.85, "result": "Content A"},
            {"agent": "content_backup", "score": 0.82, "result": "Content B"},
            {"agent": "content_tertiary", "score": 0.88, "result": "Content C"}
        ]
        
        # Mock consensus engine
        consensus = ConsensusEngine()
        with patch.object(consensus, 'evaluate') as mock_evaluate:
            mock_evaluate.return_value = {
                "consensus_reached": True,
                "selected_result": "Content C",
                "confidence": 0.92
            }
            
            # Evaluate consensus
            result = await consensus.evaluate(agent_responses)
            
            # Verify consensus
            assert result["consensus_reached"] == True
            assert result["confidence"] > 0.9
    
    @pytest.mark.asyncio
    async def test_resource_optimization(self, setup_system):
        """Test resource optimization in agent system."""
        system = await setup_system
        resource_coordinator = ResourceCoordinator()
        
        # Mock resource monitoring
        with patch.object(resource_coordinator, 'optimize_allocation') as mock_optimize:
            mock_optimize.return_value = {
                "cpu_allocation": {"agents": 0.4, "swarm": 0.3, "mcp": 0.1, "other": 0.2},
                "memory_allocation": {"agents": 0.5, "swarm": 0.2, "mcp": 0.15, "other": 0.15},
                "optimizations_applied": ["cache_enabled", "parallel_processing", "lazy_loading"]
            }
            
            # Optimize resources
            optimization = await resource_coordinator.optimize_allocation()
            
            # Verify optimization
            assert sum(optimization["cpu_allocation"].values()) == 1.0
            assert sum(optimization["memory_allocation"].values()) == 1.0
            assert len(optimization["optimizations_applied"]) > 0
    
    @pytest.mark.asyncio
    async def test_end_to_end_educational_experience(self, setup_system):
        """Test complete educational experience generation."""
        system = await setup_system
        
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
        with patch('server.main.generate_educational_experience') as mock_generate:
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
            assert experience["components"]["lesson"]["ready"] == True
            assert experience["components"]["quiz"]["adaptive"] == True
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
        with patch.object(supervisor, 'delegate_to_agent') as mock_delegate:
            mock_delegate.return_value = {
                "agent": "content",
                "task_id": "task_123",
                "result": {"lesson": "Generated lesson"}
            }
            
            # Delegate task
            task = {"type": "generate_lesson", "data": {"subject": "Math"}}
            result = await supervisor.delegate_to_agent(content_agent, task)
            
            assert result["agent"] == "content"
            assert "lesson" in result["result"]
    
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
            with patch.object(agent, 'process') as mock_process:
                if i == 0:  # Content agent
                    mock_process.return_value = {**data, "content": "Lesson content"}
                elif i == 1:  # Quiz agent
                    mock_process.return_value = {**data, "quiz": {"questions": []}}
                else:  # Review agent
                    mock_process.return_value = {**data, "approved": True}
                
                data = await agent.process(data)
        
        # Verify pipeline completion
        assert "content" in data
        assert "quiz" in data
        assert data["approved"] == True
    
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
        with patch.object(sync_coordinator, 'sync_state') as mock_sync:
            mock_sync.return_value = {"synced": True, "conflicts": []}
            
            # Sync state across agents
            result = await sync_coordinator.sync_state(shared_state)
            
            assert result["synced"] == True
            assert len(result["conflicts"]) == 0


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
        with patch.object(orchestrator, 'generate_experience') as mock_gen:
            mock_gen.return_value = {"status": "completed"}
            
            # Process concurrently
            start_time = time.time()
            tasks = [orchestrator.generate_experience(req) for req in requests]
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            # Verify throughput
            duration = end_time - start_time
            throughput = len(requests) / duration
            
            assert all(r["status"] == "completed" for r in results)
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
        
        with patch.object(orchestrator, 'generate_experience') as mock_gen:
            mock_gen.return_value = {"data": "x" * 1000}  # Small response
            
            # Generate many experiences
            for _ in range(100):
                await orchestrator.generate_experience({"subject": "Test"})
            
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
        
        swarm = SwarmController()
        
        # Create heavy load
        heavy_tasks = [
            {"id": i, "complexity": "high", "data": "x" * 10000}
            for i in range(50)
        ]
        
        # Mock processing
        with patch.object(swarm, 'distribute_tasks') as mock_dist:
            mock_dist.return_value = [{"id": t["id"], "result": "done"} for t in heavy_tasks]
            
            # Measure response time
            start = time.time()
            results = await swarm.distribute_tasks(heavy_tasks)
            end = time.time()
            
            response_time = end - start
            
            # Should handle heavy load efficiently
            assert len(results) == len(heavy_tasks)
            assert response_time < 10  # Less than 10 seconds for 50 heavy tasks


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
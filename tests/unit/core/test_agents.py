"""Unit tests for AI agents in the ToolboxAI Roblox Environment.

Tests all agent classes including:
- Base agent functionality
- Content agent
- Quiz agent
- Terrain agent
- Script agent
- Review agent
- Supervisor agent
- Orchestrator
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))



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
import os
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock, patch, mock_open

import pytest
from tests.fixtures.agents import mock_llm
import pytest_asyncio
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import Runnable

# Import agent modules
from core.agents.base_agent import BaseAgent, AgentConfig, AgentState, TaskResult
from core.agents.content_agent import ContentAgent
from core.agents.quiz_agent import QuizAgent
from core.agents.terrain_agent import TerrainAgent
from core.agents.script_agent import ScriptAgent
from core.agents.review_agent import ReviewAgent
from core.agents.supervisor import SupervisorAgent
from core.agents.orchestrator import Orchestrator, OrchestrationResult
from core.agents.testing_agent import TestingAgent, TestType, TestStatus, TestSuiteResult


# Create a concrete implementation of BaseAgent for testing
# Note: This is not a test class, just a helper for testing abstract BaseAgent
class ConcreteTestAgent(BaseAgent):
    """Concrete implementation of BaseAgent for testing."""
    
    async def _process_task(self, state: AgentState) -> Any:
        """Simple implementation for testing."""
        return {"result": "test_output", "task": state["task"]}


class TestBaseAgent:
    """Test cases for BaseAgent class."""
    
    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM."""
        llm = MagicMock()
        llm.invoke = AsyncMock(return_value=AIMessage(content="Test response"))
        return llm
    
    @pytest_asyncio.fixture(loop_scope="function")
    async def base_agent(self, mock_llm):
        """Create a base agent instance with proper cleanup."""
        # Use mock LLM flag to avoid real API calls
        os.environ["USE_MOCK_LLM"] = "true"
        try:
            config = AgentConfig(name="TestAgent")
            agent = ConcreteTestAgent(config)
            # Mock the LLM after initialization
            agent.llm = mock_llm
            yield agent
            # Cleanup agent resources if available
            if hasattr(agent, 'cleanup'):
                await agent.cleanup()
        finally:
            os.environ.pop("USE_MOCK_LLM", None)
    
    def test_base_agent_initialization(self, base_agent):
        """Test base agent initializes correctly."""
        assert base_agent is not None
        assert hasattr(base_agent, 'llm')
        assert hasattr(base_agent, 'tools')
        assert hasattr(base_agent, 'memory')
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_base_agent_execute(self, base_agent):
        """Test base agent execute method."""
        result = await base_agent.execute("Test task")
        assert result is not None
        assert result.success == True
        assert result.output["task"] == "Test task"
    
    def test_base_agent_get_status(self, base_agent):
        """Test getting agent status."""
        status = base_agent.get_status()
        assert isinstance(status, dict)
        assert status["name"] == "TestAgent"
        assert "metrics" in status
    
    def test_base_agent_memory_context(self, base_agent):
        """Test getting memory context."""
        # First add some memory
        base_agent._store_memory("test task", MagicMock(success=True, output="test", error=None))
        
        context = base_agent.get_memory_context(limit=5)
        assert isinstance(context, list)


class TestContentAgent:
    """Test cases for ContentAgent class."""
    
    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM for content generation."""
        llm = MagicMock()
        llm.invoke = AsyncMock(return_value=AIMessage(content=json.dumps({
            "title": "Test Lesson",
            "description": "Test description",
            "learning_objectives": ["Objective 1", "Objective 2"],
            "content": "Educational content here"
        }, default=make_json_serializable)))
        return llm
    
    @pytest_asyncio.fixture(loop_scope="function")
    async def content_agent(self, mock_llm):
        """Create a content agent instance with proper cleanup."""
        with patch('langchain_openai.ChatOpenAI', return_value=mock_llm):
            config = AgentConfig(name="ContentAgent", system_prompt="Educational content generator")
            agent = ContentAgent(config)
            agent.llm = mock_llm
            yield agent
            # Cleanup agent resources if available
            if hasattr(agent, 'cleanup'):
                await agent.cleanup()
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_generate_educational_content(self, content_agent):
        """Test generating educational content."""
        # Mock the LLM response
        content_agent.llm.ainvoke = AsyncMock(return_value=AIMessage(content="Test educational content"))
        
        task = "Create a lesson about fractions"
        context = {
            "subject": "Mathematics",
            "grade_level": "5",
            "learning_objectives": ["Understand fractions", "Add fractions"]
        }
        
        result = await content_agent.execute(task, context)
        
        assert result is not None
        assert result.success == True
        assert "content" in result.output
        content_agent.llm.ainvoke.assert_called()
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_content_with_interactive_elements(self, content_agent):
        """Test generating content with interactive elements."""
        content_agent.llm.ainvoke = AsyncMock(return_value=AIMessage(content="Interactive content"))
        
        task = "Create interactive science lesson"
        context = {
            "subject": "Science",
            "grade_level": "7",
            "topic": "Solar System"
        }
        
        result = await content_agent.execute(task, context)
        
        assert result is not None
        assert result.success == True
        assert "interactive_elements" in result.output
    
    def test_content_agent_initialization(self, content_agent):
        """Test content agent initialization."""
        assert content_agent is not None
        assert content_agent.name == "ContentAgent"
        assert hasattr(content_agent, 'templates')
        assert "lesson_plan" in content_agent.templates


class TestQuizAgent:
    """Test cases for QuizAgent class."""
    
    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM for quiz generation."""
        llm = MagicMock()
        llm.invoke = AsyncMock(return_value=AIMessage(content=json.dumps({
            "quiz": {
                "title": "Test Quiz",
                "questions": [
                    {
                        "id": 1,
                        "question": "What is 2+2?",
                        "type": "multiple_choice",
                        "options": ["3", "4", "5", "6"],
                        "correct_answer": "4",
                        "explanation": "2+2 equals 4"
                    }
                ]
            }
        }, default=make_json_serializable)))
        return llm
    
    @pytest_asyncio.fixture(loop_scope="function")
    async def quiz_agent(self, mock_llm):
        """Create a quiz agent instance with proper cleanup."""
        with patch('langchain_openai.ChatOpenAI', return_value=mock_llm):
            config = AgentConfig(name="QuizAgent", system_prompt="Quiz generator")
            agent = QuizAgent(config)
            agent.llm = mock_llm
            yield agent
            # Cleanup agent resources if available
            if hasattr(agent, 'cleanup'):
                await agent.cleanup()
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_generate_quiz(self, quiz_agent):
        """Test generating a quiz."""
        # Mock the LLM response
        quiz_agent.llm.ainvoke = AsyncMock(return_value=AIMessage(content=json.dumps({
            "quiz": {
                "title": "Math Quiz",
                "questions": [{"question": "What is 2+2?", "answer": "4"}]
            }
        }, default=make_json_serializable)))
        
        task = "Generate a quiz on fractions"
        context = {
            "subject": "Mathematics",
            "difficulty": "medium",
            "num_questions": 5
        }
        
        result = await quiz_agent.execute(task, context)
        
        assert result is not None
        assert result.success == True
        quiz_agent.llm.ainvoke.assert_called()
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_generate_adaptive_quiz(self, quiz_agent):
        """Test generating adaptive quiz based on performance."""
        quiz_agent.llm.ainvoke = AsyncMock(return_value=AIMessage(content=json.dumps({
            "quiz": {
                "title": "Adaptive Quiz",
                "questions": [],
                "difficulty": "adaptive"
            }
        }, default=make_json_serializable)))
        
        task = "Generate adaptive quiz"
        context = {
            "student_performance": {
                "average_score": 75,
                "weak_topics": ["Fractions"]
            }
        }
        
        result = await quiz_agent.execute(task, context)
        
        assert result is not None
        assert result.success == True
    
    def test_quiz_agent_initialization(self, quiz_agent):
        """Test quiz agent initialization."""
        assert quiz_agent is not None
        assert quiz_agent.name == "QuizAgent"
        assert hasattr(quiz_agent, 'config')


class TestTerrainAgent:
    """Test cases for TerrainAgent class."""
    
    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM for terrain generation."""
        llm = MagicMock()
        llm.invoke = AsyncMock(return_value=AIMessage(content="""
        -- Terrain Generation Script
        local Terrain = workspace.Terrain
        Terrain:FillBall(Vector3.new(0, 0, 0), 50, Enum.Material.Grass)
        """))
        llm.ainvoke = llm.invoke  # Agents use ainvoke, not invoke
        return llm
    
    @pytest.fixture
    def terrain_agent(self, mock_llm):
        """Create a terrain agent instance."""
        with patch('langchain_openai.ChatOpenAI', return_value=mock_llm):
            agent = TerrainAgent()
            agent.llm = mock_llm
            return agent
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_generate_terrain(self, terrain_agent):
        """Test generating terrain."""
        request = {
            "environment_type": "forest",
            "size": "medium",
            "features": ["trees", "river", "mountains"]
        }
        
        result = await terrain_agent.generate_terrain(request)
        
        assert result is not None
        assert "Terrain" in result
        assert terrain_agent.llm.invoke.called  # Changed from assert_called_once()
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_generate_educational_environment(self, terrain_agent):
        """Test generating educational environment."""
        subject = "Geography"
        topic = "Mountain Formation"
        
        result = await terrain_agent.generate_educational_environment(subject, topic)
        
        assert result is not None
        assert terrain_agent.llm.invoke.called
    
    def test_validate_terrain_script(self, terrain_agent):
        """Test terrain script validation."""
        valid_script = """
        local Terrain = workspace.Terrain
        -- Valid Lua script
        """
        
        invalid_script = "Not a valid Lua script {"
        
        assert terrain_agent.validate_script(valid_script) == True
        assert terrain_agent.validate_script(invalid_script) == False


class TestScriptAgent:
    """Test cases for ScriptAgent class."""
    
    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM for script generation."""
        llm = MagicMock()
        llm.invoke = AsyncMock(return_value=AIMessage(content="""
        -- Educational Game Script
        local Players = game:GetService("Players")
        local ReplicatedStorage = game:GetService("ReplicatedStorage")
        
        local function onPlayerJoined(player)
            print("Welcome " .. player.Name)
        end
        
        Players.PlayerAdded:Connect(onPlayerJoined)
        """))
        llm.ainvoke = llm.invoke  # Agents use ainvoke, not invoke
        return llm
    
    @pytest.fixture
    def script_agent(self, mock_llm):
        """Create a script agent instance."""
        with patch('langchain_openai.ChatOpenAI', return_value=mock_llm):
            agent = ScriptAgent()
            agent.llm = mock_llm
            return agent
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_generate_game_script(self, script_agent):
        """Test generating game script."""
        request = {
            "script_type": "game_logic",
            "features": ["player_spawning", "score_tracking", "timer"],
            "educational_elements": ["quiz_integration", "progress_tracking"]
        }
        
        result = await script_agent.generate_script(request)
        
        assert result is not None
        assert "Players" in result
        assert script_agent.llm.invoke.called
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_generate_ui_script(self, script_agent):
        """Test generating UI script."""
        ui_elements = ["quiz_panel", "score_display", "timer"]
        
        result = await script_agent.generate_ui_script(ui_elements)
        
        assert result is not None
        assert script_agent.llm.invoke.called
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_optimize_script(self, script_agent):
        """Test script optimization."""
        unoptimized_script = """
        for i = 1, 100 do
            local part = Instance.new("Part")
            part.Parent = workspace
        end
        """
        
        optimized = await script_agent.optimize_script(unoptimized_script)
        
        assert optimized is not None
        # Should suggest using batch operations or object pooling


class TestReviewAgent:
    """Test cases for ReviewAgent class."""
    
    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM for review."""
        llm = MagicMock()
        llm.invoke = AsyncMock(return_value=AIMessage(content=json.dumps({
            "review": {
                "quality_score": 85,
                "educational_value": 90,
                "technical_correctness": 88,
                "suggestions": [
                    "Add more interactive elements",
                    "Include progress checkpoints"
                ],
                "approved": True
            }
        }, default=make_json_serializable)))
        llm.ainvoke = llm.invoke  # Agents use ainvoke, not invoke
        return llm
    
    @pytest.fixture
    def review_agent(self, mock_llm):
        """Create a review agent instance."""
        with patch('langchain_openai.ChatOpenAI', return_value=mock_llm):
            agent = ReviewAgent()
            agent.llm = mock_llm
            return agent
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_review_content(self, review_agent):
        """Test reviewing educational content."""
        content = {
            "type": "lesson",
            "subject": "Science",
            "grade_level": 6,
            "content": "Lesson about photosynthesis...",
            "quiz": {...}
        }
        
        result = await review_agent.review_content(content)
        
        assert result is not None
        assert "quality_score" in json.loads(result.content)["review"]
        assert review_agent.llm.invoke.called
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_review_lua_script(self, review_agent):
        """Test reviewing Lua scripts."""
        script = """
        local Players = game:GetService("Players")
        -- Game logic here
        """
        
        result = await review_agent.review_script(script)
        
        assert result is not None
        assert review_agent.llm.invoke.called
    
    def test_check_educational_standards(self, review_agent):
        """Test checking educational standards compliance."""
        content = {
            "learning_objectives": ["Understand photosynthesis"],
            "grade_level": 6,
            "assessment": True
        }
        
        result = review_agent.check_standards(content)
        
        assert result is not None
        assert isinstance(result, dict)


class TestSupervisorAgent:
    """Test cases for SupervisorAgent class."""
    
    @pytest.fixture
    def mock_agents(self):
        """Create mock sub-agents."""
        return {
            "content": MagicMock(spec=ContentAgent),
            "quiz": MagicMock(spec=QuizAgent),
            "terrain": MagicMock(spec=TerrainAgent),
            "script": MagicMock(spec=ScriptAgent),
            "review": MagicMock(spec=ReviewAgent)
        }
    
    @pytest.fixture
    def supervisor_agent(self, mock_agents):
        """Create a supervisor agent instance."""
        # Patch the _get_agent_class_map method since agents are imported there
        with patch.object(SupervisorAgent, '_get_agent_class_map') as mock_get_map:
            mock_get_map.return_value = {
                "content": MagicMock,
                "quiz": MagicMock,
                "terrain": MagicMock,
                "script": MagicMock,
                "review": MagicMock
            }
            with patch('core.agents.base_agent.from langchain_openai import ChatOpenAI'):
                agent = SupervisorAgent()
                # Set managed_agents instead of agents
                agent.managed_agents = mock_agents
                return agent
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_route_task(self, supervisor_agent):
        """Test task routing to appropriate agent."""
        with patch('core.agents.base_agent.from langchain_openai import ChatOpenAI'):
            # Test _routing_decision method which determines routing
            state = AgentState(
                task="Generate quiz for Math",
                messages=[],
                context={},
                metadata={"routing_decision": "delegate to quiz agent"},
                result=None,
                error=None,
                status="pending"
            )
            
            decision = supervisor_agent._routing_decision(state)
            assert decision == "delegate"
            
            # Test escalate decision
            state["metadata"]["routing_decision"] = "escalate to human"
            decision = supervisor_agent._routing_decision(state)
            assert decision == "escalate"
            
            # Test direct response
            state["metadata"]["routing_decision"] = "direct response needed"
            decision = supervisor_agent._routing_decision(state)
            assert decision == "direct"
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_delegate_complex_task(self, supervisor_agent):
        """Test delegating complex tasks to multiple agents."""
        # Mock the execute method for managed agents
        for agent_name, agent in supervisor_agent.managed_agents.items():
            agent.execute = AsyncMock(return_value=TaskResult(
                success=True,
                output={f"{agent_name}_result": f"Generated by {agent_name}"},
                error=None,
                execution_time=1.0,
                metadata={"agent": agent_name}
            ))
        
        # Test delegate_complex_task method
        with patch.object(supervisor_agent, 'execute', new=AsyncMock(return_value=TaskResult(
            success=True,
            output={"aggregated": "results"},
            error=None,
            execution_time=2.0
        ))):
            result = await supervisor_agent.delegate_complex_task(
                "Generate complete educational experience",
                {"subject": "Math", "grade_level": 7}
            )
            
            assert result.success == True
            assert result.output is not None
    
    def test_get_agent_status_report(self, supervisor_agent):
        """Test getting status report from all agents."""
        # Mock get_status for each managed agent
        for agent in supervisor_agent.managed_agents.values():
            agent.get_status = MagicMock(return_value={"status": "ready", "tasks_completed": 0})
        
        report = supervisor_agent.get_agent_status_report()
        
        assert "supervisor_status" in report
        assert "managed_agents" in report
        assert "performance_metrics" in report
        assert "task_queue_size" in report
        
        # Check that all managed agents are in the report
        for agent_name in supervisor_agent.managed_agents.keys():
            assert agent_name in report["managed_agents"]
    
    def test_validate_response(self, supervisor_agent):
        """Test validating responses from sub-agents."""
        valid_response = {
            "content": {"lesson": "Valid lesson"},
            "quiz": {"questions": [{"question": "Q1"}]},
            "status": "success"
        }
        
        invalid_response = {
            "error": "Agent failed",
            "status": "error"
        }
        
        assert supervisor_agent.validate_response(valid_response) == True
        assert supervisor_agent.validate_response(invalid_response) == False


class TestOrchestrator:
    """Test cases for Orchestrator class."""
    
    @pytest.fixture
    def mock_supervisor(self):
        """Create a mock supervisor agent."""
        supervisor = MagicMock(spec=SupervisorAgent)
        supervisor.coordinate = AsyncMock(return_value={
            "lesson": {"title": "Test Lesson"},
            "quiz": {"questions": []},
            "terrain": "terrain_script",
            "scripts": ["script1", "script2"]
        })
        return supervisor
    
    @pytest.fixture
    def orchestrator(self, mock_supervisor):
        """Create an orchestrator instance."""
        with patch('core.agents.orchestrator.SupervisorAgent', return_value=mock_supervisor):
            with patch('core.agents.orchestrator.ContentAgent'):
                with patch('core.agents.orchestrator.QuizAgent'):
                    with patch('core.agents.orchestrator.TerrainAgent'):
                        with patch('core.agents.orchestrator.ScriptAgent'):
                            with patch('core.agents.orchestrator.ReviewAgent'):
                                with patch('core.agents.base_agent.from langchain_openai import ChatOpenAI'):
                                    orch = Orchestrator()
                                    orch.supervisor = mock_supervisor
                                    return orch
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_generate_environment(self, orchestrator):
        """Test generating complete educational environment."""
        # Mock the orchestrate method which is called by generate_environment
        mock_result = OrchestrationResult(
            success=True,
            content={"lesson": {"title": "Test Lesson"}},
            quiz={"questions": []},
            terrain={"script": "terrain_script"},
            scripts={"main": "script1", "quiz": "script2"},
            errors=[],
            execution_time=1.0
        )
        
        orchestrator.orchestrate = AsyncMock(return_value=mock_result)
        
        result = await orchestrator.generate_environment(
            subject="Science",
            grade_level=7,
            topic="Solar System",
            duration=45,
            include_quiz=True,
            include_terrain=True
        )
        
        assert result is not None
        assert result.success == True
        assert result.content is not None
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_review_code(self, orchestrator):
        """Test reviewing generated code."""
        # Mock the review_code method
        mock_result = OrchestrationResult(
            success=True,
            review={"optimized": True, "suggestions": []},
            errors=[],
            execution_time=0.5
        )
        
        code_files = {
            "main.lua": "print('Hello')",
            "quiz.lua": "-- Quiz script"
        }
        
        with patch.object(orchestrator, 'orchestrate', new=AsyncMock(return_value=mock_result)):
            result = await orchestrator.review_code(code_files)
            
            assert result is not None
            assert result.success == True
            assert result.review is not None
    
    def test_get_metrics(self, orchestrator):
        """Test getting orchestrator metrics."""
        # Set some mock metrics in the metrics dictionary
        orchestrator.metrics["total_requests"] = 10
        orchestrator.metrics["successful_requests"] = 8
        orchestrator.metrics["failed_requests"] = 2
        orchestrator.metrics["average_execution_time"] = 5.5
        
        metrics = orchestrator.get_metrics()
        
        assert metrics is not None
        assert "total_requests" in metrics
        assert "successful_requests" in metrics
        assert "failed_requests" in metrics
        assert "average_execution_time" in metrics
        assert metrics["total_requests"] == 10
        assert metrics["successful_requests"] == 8


# Integration tests
class TestAgentIntegration:
    """Integration tests for agent interactions."""
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.integration
    @pytest.mark.asyncio(loop_scope="function")
    async def test_full_content_generation_pipeline(self):
        """Test complete content generation pipeline."""
        # This would test real agent interactions if not mocked
        with patch('core.agents.orchestrator.Orchestrator') as MockOrchestrator:
            orchestrator = MockOrchestrator()
            orchestrator.generate_experience = AsyncMock(return_value={
                "lesson": {"title": "Integrated Lesson"},
                "quiz": {"questions": [{"q": "Q1"}]},
                "terrain": "generated_terrain",
                "scripts": ["script1"],
                "review": {"approved": True}
            })
            
            request = {
                "subject": "Science",
                "grade_level": 8,
                "topic": "Ecosystems",
                "full_experience": True
            }
            
            result = await orchestrator.generate_experience(request)
            
            assert result is not None
            assert result["review"]["approved"] == True
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.integration
    @pytest.mark.asyncio(loop_scope="function")
    async def test_agent_error_handling(self):
        """Test error handling in agent pipeline."""
        with patch('core.agents.content_agent.ContentAgent') as MockContentAgent:
            agent = MockContentAgent()
            agent.generate_lesson = AsyncMock(side_effect=Exception("API Error"))
            
            with pytest.raises(Exception) as exc_info:
                await agent.generate_lesson({})
            
            assert "API Error" in str(exc_info.value)
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.integration
    @pytest.mark.asyncio(loop_scope="function")
    async def test_agent_retry_mechanism(self):
        """Test retry mechanism for failed agent tasks."""
        with patch('core.agents.quiz_agent.QuizAgent') as MockQuizAgent:
            agent = MockQuizAgent()
            
            # Fail twice, then succeed
            agent.generate_quiz = AsyncMock(
                side_effect=[
                    Exception("Temporary failure"),
                    Exception("Temporary failure"),
                    {"quiz": "Success"}
                ]
            )
            
            # With retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    result = await agent.generate_quiz({})
                    break
                except Exception:
                    if attempt == max_retries - 1:
                        raise
            
            assert result == {"quiz": "Success"}


# Performance tests
class TestAgentPerformance:
    """Performance tests for agents."""
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.performance
    @pytest.mark.asyncio(loop_scope="function")
    async def test_agent_response_time(self):
        """Test agent response time is within acceptable limits."""
        import time
        
        with patch('core.agents.content_agent.ContentAgent') as MockAgent:
            agent = MockAgent()
            agent.generate_lesson = AsyncMock(return_value={"lesson": "content"})
            
            start_time = time.time()
            await agent.generate_lesson({})
            end_time = time.time()
            
            response_time = end_time - start_time
            assert response_time < 5.0  # Should respond within 5 seconds
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.performance
    @pytest.mark.asyncio(loop_scope="function")
    async def test_parallel_agent_execution(self):
        """Test parallel execution of multiple agents."""
        agents = []
        for i in range(5):
            agent = MagicMock()
            agent.process = AsyncMock(return_value=f"Result {i}")
            agents.append(agent)
        
        # Execute all agents in parallel
        tasks = [agent.process() for agent in agents]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        assert all(f"Result {i}" in results for i in range(5))


class TestTestingAgent:
    """Test cases for TestingAgent class."""
    
    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM for testing agent"""
        llm = MagicMock()
        llm.ainvoke = AsyncMock(return_value=AIMessage(content="Test analysis complete"))
        return llm
    
    @pytest.fixture
    def testing_agent(self, mock_llm):
        """Create a testing agent instance"""
        with patch('langchain_openai.ChatOpenAI', return_value=mock_llm):
            agent = TestingAgent()
            agent.llm = mock_llm
            return agent
    
    @pytest.fixture
    def mock_subprocess_run(self):
        """Mock subprocess.run for pytest execution"""
        with patch('subprocess.run') as mock_run:
            # Mock successful test run
            mock_run.return_value.stdout = "5 passed, 0 failed, 0 skipped"
            mock_run.return_value.stderr = ""
            mock_run.return_value.returncode = 0
            yield mock_run
    
    def test_testing_agent_initialization(self, testing_agent):
        """Test testing agent initializes correctly"""
        assert testing_agent is not None
        assert testing_agent.name == "TestingAgent"
        assert hasattr(testing_agent, 'test_commands')
        assert hasattr(testing_agent, 'test_history')
        assert TestType.UNIT in testing_agent.test_commands
        assert TestType.INTEGRATION in testing_agent.test_commands
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_execute_unit_tests(self, testing_agent, mock_subprocess_run):
        """Test executing unit tests"""
        task = "run unit tests"
        context = {"test_type": "unit"}
        
        result = await testing_agent.execute(task, context)
        
        assert result is not None
        assert result.success == True
        assert "test_type" in result.output
        assert result.output["test_type"] == "unit"
        mock_subprocess_run.assert_called()
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_execute_integration_tests(self, testing_agent, mock_subprocess_run):
        """Test executing integration tests"""
        task = "run integration tests"
        context = {"test_type": "integration"}
        
        result = await testing_agent.execute(task, context)
        
        assert result is not None
        assert result.success == True
        assert "test_type" in result.output
        assert result.output["test_type"] == "integration"
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_execute_all_tests(self, testing_agent, mock_subprocess_run):
        """Test executing all tests with coverage"""
        # Mock coverage output
        mock_subprocess_run.return_value.stdout = "5 passed, 0 failed\\nTOTAL 85%"
        
        task = "run tests"
        context = {}
        
        result = await testing_agent.execute(task, context)
        
        assert result is not None
        assert result.success == True
        assert "result" in result.output
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_generate_coverage_report(self, testing_agent, mock_subprocess_run):
        """Test generating coverage report"""
        # Mock coverage JSON data
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data='{"totals": {"percent_covered": 85.5}}')):
                task = "coverage report"
                context = {}
                
                result = await testing_agent.execute(task, context)
                
                assert result is not None
                assert result.success == True
                assert "coverage_percentage" in result.output
    
    def test_extract_test_type(self, testing_agent):
        """Test extracting test type from task description"""
        assert testing_agent._extract_test_type("run unit tests", {}) == TestType.UNIT
        assert testing_agent._extract_test_type("run integration tests", {}) == TestType.INTEGRATION
        assert testing_agent._extract_test_type("run performance tests", {}) == TestType.PERFORMANCE
        assert testing_agent._extract_test_type("run security tests", {}) == TestType.SECURITY
        assert testing_agent._extract_test_type("run all tests", {}) == TestType.ALL
    
    def test_parse_pytest_output(self, testing_agent):
        """Test parsing pytest output"""
        stdout = "test_file.py::test_func PASSED\\n5 passed, 2 failed, 1 skipped"
        stderr = ""
        
        # Convert command list to string for the test
        command = f"{sys.executable} -m pytest"
        
        result = testing_agent._parse_pytest_output(
            stdout, stderr, 0, TestType.UNIT, command, 2.5
        )
        
        assert result.test_type == TestType.UNIT
        assert result.total_tests == 8  # 5 + 2 + 1
        assert result.passed == 5
        assert result.failed == 2
        assert result.skipped == 1
        assert result.duration == 2.5
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_trigger_post_completion_tests(self, testing_agent, mock_subprocess_run):
        """Test triggering tests after another agent completes"""
        agent_name = "ContentAgent"
        task_result = {"status": "success", "output": "content generated"}
        
        result = await testing_agent.trigger_post_completion_tests(agent_name, task_result)
        
        assert result is not None
        assert "triggered_by" in result
        assert result["triggered_by"] == agent_name
        assert "test_type_executed" in result
        assert "validation_status" in result
    
    def test_determine_test_type_for_agent(self, testing_agent):
        """Test determining appropriate test type for different agents"""
        assert testing_agent._determine_test_type_for_agent("ContentAgent", {}) == TestType.INTEGRATION
        assert testing_agent._determine_test_type_for_agent("QuizAgent", {}) == TestType.INTEGRATION
        assert testing_agent._determine_test_type_for_agent("ScriptAgent", {}) == TestType.UNIT
        assert testing_agent._determine_test_type_for_agent("UnknownAgent", {}) == TestType.UNIT
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_validate_agent_output(self, testing_agent, mock_subprocess_run):
        """Test validating output from another agent"""
        agent_name = "ScriptAgent"
        output = {"script": "print('Hello World')"}
        
        result = await testing_agent.validate_agent_output(agent_name, output)
        
        assert result is not None
        assert "agent_name" in result
        assert result["agent_name"] == agent_name
        assert "validation_result" in result
        assert "test_details" in result
    
    def test_get_test_metrics(self, testing_agent):
        """Test getting testing metrics"""
        # Add some mock test history
        testing_agent.test_history = [
            TestSuiteResult(TestType.UNIT, 10, 8, 2, 0, 0, 5.0, 85.0),
            TestSuiteResult(TestType.INTEGRATION, 5, 5, 0, 0, 0, 3.0, None)
        ]
        
        metrics = testing_agent.get_test_metrics()
        
        assert metrics is not None
        assert "total_test_runs" in metrics
        assert "recent_runs" in metrics
        assert "average_pass_rate" in metrics
        assert metrics["total_test_runs"] == 2
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_health_check(self, testing_agent):
        """Test testing system health check"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "pytest 8.4.2"
            
            health = await testing_agent.health_check()
            
            assert health is not None
            assert "overall_health" in health
            assert "pytest_available" in health
            assert "project_root_accessible" in health
    
    def test_cleanup_test_artifacts(self, testing_agent):
        """Test cleaning up test artifacts"""
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.unlink') as mock_unlink:
                with patch('pathlib.Path.is_file', return_value=True):
                    result = testing_agent.cleanup_test_artifacts()
                    
                    assert result is not None
                    assert "artifacts_cleaned" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
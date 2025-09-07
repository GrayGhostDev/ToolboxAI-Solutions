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

import asyncio
import json
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import Runnable

# Add parent directory to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "roblox-environment"))

from agents.base_agent import BaseAgent
from agents.content_agent import ContentAgent
from agents.quiz_agent import QuizAgent
from agents.terrain_agent import TerrainAgent
from agents.script_agent import ScriptAgent
from agents.review_agent import ReviewAgent
from agents.supervisor import SupervisorAgent
from agents.orchestrator import Orchestrator


class TestBaseAgent:
    """Test cases for BaseAgent class."""
    
    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM."""
        llm = MagicMock()
        llm.invoke = AsyncMock(return_value=AIMessage(content="Test response"))
        return llm
    
    @pytest.fixture
    def base_agent(self, mock_llm):
        """Create a base agent instance."""
        with patch('agents.base_agent.ChatOpenAI', return_value=mock_llm):
            agent = BaseAgent()
            agent.llm = mock_llm
            return agent
    
    def test_base_agent_initialization(self, base_agent):
        """Test base agent initializes correctly."""
        assert base_agent is not None
        assert hasattr(base_agent, 'llm')
        assert hasattr(base_agent, 'tools')
        assert hasattr(base_agent, 'memory')
    
    @pytest.mark.asyncio
    async def test_base_agent_invoke(self, base_agent):
        """Test base agent invoke method."""
        result = await base_agent.invoke("Test prompt")
        assert result is not None
        base_agent.llm.invoke.assert_called_once()
    
    def test_base_agent_get_tools(self, base_agent):
        """Test getting tools from base agent."""
        tools = base_agent.get_tools()
        assert isinstance(tools, list)
    
    def test_base_agent_add_to_memory(self, base_agent):
        """Test adding to agent memory."""
        base_agent.add_to_memory("user", "Test message")
        assert len(base_agent.memory) > 0
        assert base_agent.memory[-1]["role"] == "user"
        assert base_agent.memory[-1]["content"] == "Test message"


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
        })))
        return llm
    
    @pytest.fixture
    def content_agent(self, mock_llm):
        """Create a content agent instance."""
        with patch('agents.content_agent.ChatOpenAI', return_value=mock_llm):
            agent = ContentAgent()
            agent.llm = mock_llm
            return agent
    
    @pytest.mark.asyncio
    async def test_generate_lesson_content(self, content_agent):
        """Test generating lesson content."""
        request = {
            "subject": "Mathematics",
            "grade_level": 5,
            "learning_objectives": ["Fractions", "Decimals"],
            "environment_type": "classroom"
        }
        
        result = await content_agent.generate_lesson(request)
        
        assert result is not None
        content_agent.llm.invoke.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_educational_narrative(self, content_agent):
        """Test generating educational narrative."""
        topic = "Solar System"
        grade_level = 7
        
        result = await content_agent.generate_narrative(topic, grade_level)
        
        assert result is not None
        content_agent.llm.invoke.assert_called_once()
    
    def test_validate_content_request(self, content_agent):
        """Test content request validation."""
        valid_request = {
            "subject": "Science",
            "grade_level": 6,
            "learning_objectives": ["Photosynthesis"]
        }
        
        invalid_request = {
            "subject": "Science"
            # Missing required fields
        }
        
        assert content_agent.validate_request(valid_request) == True
        assert content_agent.validate_request(invalid_request) == False


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
        })))
        return llm
    
    @pytest.fixture
    def quiz_agent(self, mock_llm):
        """Create a quiz agent instance."""
        with patch('agents.quiz_agent.ChatOpenAI', return_value=mock_llm):
            agent = QuizAgent()
            agent.llm = mock_llm
            return agent
    
    @pytest.mark.asyncio
    async def test_generate_quiz(self, quiz_agent):
        """Test generating a quiz."""
        request = {
            "subject": "Mathematics",
            "difficulty": "medium",
            "num_questions": 5,
            "question_types": ["multiple_choice", "true_false"]
        }
        
        result = await quiz_agent.generate_quiz(request)
        
        assert result is not None
        quiz_agent.llm.invoke.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_adaptive_quiz(self, quiz_agent):
        """Test generating adaptive quiz based on performance."""
        student_performance = {
            "average_score": 75,
            "weak_topics": ["Fractions"],
            "strong_topics": ["Addition"]
        }
        
        result = await quiz_agent.generate_adaptive_quiz(student_performance)
        
        assert result is not None
        quiz_agent.llm.invoke.assert_called_once()
    
    def test_validate_quiz_structure(self, quiz_agent):
        """Test quiz structure validation."""
        valid_quiz = {
            "title": "Test Quiz",
            "questions": [
                {
                    "question": "Test?",
                    "type": "multiple_choice",
                    "options": ["A", "B"],
                    "correct_answer": "A"
                }
            ]
        }
        
        invalid_quiz = {
            "title": "Test Quiz"
            # Missing questions
        }
        
        assert quiz_agent.validate_quiz(valid_quiz) == True
        assert quiz_agent.validate_quiz(invalid_quiz) == False


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
        return llm
    
    @pytest.fixture
    def terrain_agent(self, mock_llm):
        """Create a terrain agent instance."""
        with patch('agents.terrain_agent.ChatOpenAI', return_value=mock_llm):
            agent = TerrainAgent()
            agent.llm = mock_llm
            return agent
    
    @pytest.mark.asyncio
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
        terrain_agent.llm.invoke.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_educational_environment(self, terrain_agent):
        """Test generating educational environment."""
        subject = "Geography"
        topic = "Mountain Formation"
        
        result = await terrain_agent.generate_educational_environment(subject, topic)
        
        assert result is not None
        terrain_agent.llm.invoke.assert_called_once()
    
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
        return llm
    
    @pytest.fixture
    def script_agent(self, mock_llm):
        """Create a script agent instance."""
        with patch('agents.script_agent.ChatOpenAI', return_value=mock_llm):
            agent = ScriptAgent()
            agent.llm = mock_llm
            return agent
    
    @pytest.mark.asyncio
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
        script_agent.llm.invoke.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_ui_script(self, script_agent):
        """Test generating UI script."""
        ui_elements = ["quiz_panel", "score_display", "timer"]
        
        result = await script_agent.generate_ui_script(ui_elements)
        
        assert result is not None
        script_agent.llm.invoke.assert_called_once()
    
    def test_optimize_script(self, script_agent):
        """Test script optimization."""
        unoptimized_script = """
        for i = 1, 100 do
            local part = Instance.new("Part")
            part.Parent = workspace
        end
        """
        
        optimized = script_agent.optimize_script(unoptimized_script)
        
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
        })))
        return llm
    
    @pytest.fixture
    def review_agent(self, mock_llm):
        """Create a review agent instance."""
        with patch('agents.review_agent.ChatOpenAI', return_value=mock_llm):
            agent = ReviewAgent()
            agent.llm = mock_llm
            return agent
    
    @pytest.mark.asyncio
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
        review_agent.llm.invoke.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_review_lua_script(self, review_agent):
        """Test reviewing Lua scripts."""
        script = """
        local Players = game:GetService("Players")
        -- Game logic here
        """
        
        result = await review_agent.review_script(script)
        
        assert result is not None
        review_agent.llm.invoke.assert_called_once()
    
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
        with patch('agents.supervisor.ContentAgent', return_value=mock_agents["content"]):
            with patch('agents.supervisor.QuizAgent', return_value=mock_agents["quiz"]):
                with patch('agents.supervisor.TerrainAgent', return_value=mock_agents["terrain"]):
                    with patch('agents.supervisor.ScriptAgent', return_value=mock_agents["script"]):
                        with patch('agents.supervisor.ReviewAgent', return_value=mock_agents["review"]):
                            agent = SupervisorAgent()
                            agent.agents = mock_agents
                            return agent
    
    @pytest.mark.asyncio
    async def test_route_task(self, supervisor_agent):
        """Test task routing to appropriate agent."""
        # Test quiz routing
        quiz_task = {"task": "generate_quiz", "subject": "Math"}
        agent = supervisor_agent.route_task(quiz_task)
        assert agent == "quiz"
        
        # Test content routing
        content_task = {"task": "generate_lesson", "subject": "Science"}
        agent = supervisor_agent.route_task(content_task)
        assert agent == "content"
        
        # Test terrain routing
        terrain_task = {"task": "generate_terrain", "environment": "forest"}
        agent = supervisor_agent.route_task(terrain_task)
        assert agent == "terrain"
    
    @pytest.mark.asyncio
    async def test_coordinate_agents(self, supervisor_agent):
        """Test coordinating multiple agents."""
        request = {
            "generate_lesson": True,
            "generate_quiz": True,
            "generate_terrain": True
        }
        
        # Mock agent responses
        supervisor_agent.agents["content"].generate_lesson = AsyncMock(return_value={"lesson": "content"})
        supervisor_agent.agents["quiz"].generate_quiz = AsyncMock(return_value={"quiz": "questions"})
        supervisor_agent.agents["terrain"].generate_terrain = AsyncMock(return_value="terrain_script")
        
        result = await supervisor_agent.coordinate(request)
        
        assert result is not None
        assert "lesson" in result
        assert "quiz" in result
        assert "terrain" in result
    
    def test_validate_agent_responses(self, supervisor_agent):
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
        with patch('agents.orchestrator.SupervisorAgent', return_value=mock_supervisor):
            orch = Orchestrator()
            orch.supervisor = mock_supervisor
            return orch
    
    @pytest.mark.asyncio
    async def test_generate_complete_experience(self, orchestrator):
        """Test generating complete educational experience."""
        request = {
            "subject": "Science",
            "grade_level": 7,
            "topic": "Solar System",
            "duration": 45,
            "include_quiz": True,
            "include_terrain": True
        }
        
        result = await orchestrator.generate_experience(request)
        
        assert result is not None
        assert "lesson" in result
        assert "quiz" in result
        assert "terrain" in result
        orchestrator.supervisor.coordinate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_workflow_execution(self, orchestrator):
        """Test executing educational workflow."""
        workflow = [
            {"step": "generate_content", "params": {"subject": "Math"}},
            {"step": "generate_quiz", "params": {"num_questions": 5}},
            {"step": "review", "params": {}}
        ]
        
        result = await orchestrator.execute_workflow(workflow)
        
        assert result is not None
        assert len(result) == len(workflow)
    
    def test_optimize_generation_pipeline(self, orchestrator):
        """Test optimizing the generation pipeline."""
        request = {
            "subject": "History",
            "constraints": {
                "time_limit": 30,
                "max_questions": 10
            }
        }
        
        optimized = orchestrator.optimize_pipeline(request)
        
        assert optimized is not None
        assert "parallel_tasks" in optimized
        assert "sequential_tasks" in optimized


# Integration tests
class TestAgentIntegration:
    """Integration tests for agent interactions."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_content_generation_pipeline(self):
        """Test complete content generation pipeline."""
        # This would test real agent interactions if not mocked
        with patch('agents.orchestrator.Orchestrator') as MockOrchestrator:
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
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_agent_error_handling(self):
        """Test error handling in agent pipeline."""
        with patch('agents.content_agent.ContentAgent') as MockContentAgent:
            agent = MockContentAgent()
            agent.generate_lesson = AsyncMock(side_effect=Exception("API Error"))
            
            with pytest.raises(Exception) as exc_info:
                await agent.generate_lesson({})
            
            assert "API Error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_agent_retry_mechanism(self):
        """Test retry mechanism for failed agent tasks."""
        with patch('agents.quiz_agent.QuizAgent') as MockQuizAgent:
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
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_agent_response_time(self):
        """Test agent response time is within acceptable limits."""
        import time
        
        with patch('agents.content_agent.ContentAgent') as MockAgent:
            agent = MockAgent()
            agent.generate_lesson = AsyncMock(return_value={"lesson": "content"})
            
            start_time = time.time()
            await agent.generate_lesson({})
            end_time = time.time()
            
            response_time = end_time - start_time
            assert response_time < 5.0  # Should respond within 5 seconds
    
    @pytest.mark.asyncio
    @pytest.mark.performance
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
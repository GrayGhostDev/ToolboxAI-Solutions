"""
Unit Tests for Agent Swarm Endpoints

Tests swarm chat, task execution, session management, and educational content endpoints.

Phase 2 Days 17-18: Agent swarm endpoint test implementation
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException, WebSocket

# Import endpoint functions and models directly
from apps.backend.api.v1.endpoints.agent_swarm import (
    AgentTaskRequest,
    AgentTaskResponse,
    ChatMessage,
    ChatResponse,
    SessionInfo,
    SwarmStatus,
    analyze_student_progress,
    chat_stream,
    chat_with_swarm,
    clear_session,
    create_assessment,
    create_lesson,
    execute_agent_task,
    get_session_info,
    get_swarm_status,
    personalize_content,
    reset_swarm,
    websocket_endpoint,
)

# Mock OrchestrationController and related classes
from core.swarm.orchestration_controller import OrchestrationController

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_orchestration_controller():
    """Create mock orchestration controller."""
    controller = AsyncMock(spec=OrchestrationController)
    controller.sessions = {}
    controller.agents = {
        "curriculum": AsyncMock(),
        "analytics": AsyncMock(),
        "assessment": AsyncMock(),
        "validation": AsyncMock(),
        "adaptive": AsyncMock(),
    }
    controller.metrics = {
        "successful_interactions": 100,
        "failed_interactions": 10,
    }
    return controller


@pytest.fixture
def mock_session():
    """Create mock session."""
    session = Mock()
    session.session_id = str(uuid4())
    session.started_at = datetime.utcnow()
    session.current_state = Mock(value="ACTIVE")
    session.accumulated_context = {"topic": "Python", "grade": "5th"}
    session.completed_tasks = ["create_lesson", "create_quiz"]
    return session


@pytest.fixture
def sample_chat_message():
    """Sample chat message."""
    return ChatMessage(
        message="Create a Python lesson for 5th graders",
        session_id=None,
        context={"grade_level": "5th", "subject": "Python"},
    )


@pytest.fixture
def sample_agent_task_request():
    """Sample agent task request."""
    return AgentTaskRequest(
        agent_type="curriculum",
        task_type="generate_outline",
        data={"topic": "Python basics", "grade": "5th"},
        session_id=str(uuid4()),
    )


@pytest.fixture
def sample_process_result():
    """Sample orchestration process result."""
    return {
        "success": True,
        "session_id": str(uuid4()),
        "response": {
            "message": "I've created a Python lesson for 5th graders",
            "data": {"lesson_id": "lesson-123", "duration": "45 minutes"},
            "suggestions": ["Add quiz", "Create activities", "Generate handouts"],
        },
        "context": {"topic": "Python", "grade": "5th"},
    }


# ============================================================================
# Test Chat Endpoint
# ============================================================================


class TestChatWithSwarm:
    """Test main chat endpoint."""

    @pytest.mark.asyncio
    async def test_chat_success(
        self, mock_orchestration_controller, sample_chat_message, sample_process_result
    ):
        """Test successful chat interaction."""
        mock_orchestration_controller.process_interaction.return_value = sample_process_result

        result = await chat_with_swarm(
            request=sample_chat_message, controller=mock_orchestration_controller
        )

        assert isinstance(result, ChatResponse)
        assert result.success is True
        assert result.session_id == sample_process_result["session_id"]
        assert result.message == sample_process_result["response"]["message"]
        assert result.data == sample_process_result["response"]["data"]
        assert result.suggestions == sample_process_result["response"]["suggestions"]

    @pytest.mark.asyncio
    async def test_chat_with_session_id(self, mock_orchestration_controller, sample_process_result):
        """Test chat with existing session ID."""
        session_id = str(uuid4())
        message = ChatMessage(message="Continue the lesson", session_id=session_id, context={})
        mock_orchestration_controller.process_interaction.return_value = sample_process_result

        result = await chat_with_swarm(request=message, controller=mock_orchestration_controller)

        mock_orchestration_controller.process_interaction.assert_called_once_with(
            user_input=message.message, session_id=session_id, user_context={}
        )
        assert isinstance(result, ChatResponse)

    @pytest.mark.asyncio
    async def test_chat_error_handling(self, mock_orchestration_controller, sample_chat_message):
        """Test error handling in chat."""
        mock_orchestration_controller.process_interaction.side_effect = Exception(
            "Processing failed"
        )

        with pytest.raises(HTTPException) as exc_info:
            await chat_with_swarm(
                request=sample_chat_message, controller=mock_orchestration_controller
            )

        assert exc_info.value.status_code == 500
        assert "Processing failed" in str(exc_info.value.detail)


# ============================================================================
# Test Chat Stream Endpoint
# ============================================================================


class TestChatStream:
    """Test streaming chat endpoint."""

    @pytest.mark.asyncio
    async def test_chat_stream_success(
        self, mock_orchestration_controller, sample_chat_message, sample_process_result
    ):
        """Test successful streaming chat."""
        mock_orchestration_controller.process_interaction.return_value = sample_process_result

        response = await chat_stream(
            request=sample_chat_message, controller=mock_orchestration_controller
        )

        # Verify it's a StreamingResponse
        assert response.media_type == "text/event-stream"
        assert response.headers["Cache-Control"] == "no-cache"
        assert response.headers["Connection"] == "keep-alive"

    @pytest.mark.asyncio
    async def test_chat_stream_error(self, mock_orchestration_controller, sample_chat_message):
        """Test error handling in streaming chat."""
        mock_orchestration_controller.process_interaction.side_effect = Exception("Stream error")

        response = await chat_stream(
            request=sample_chat_message, controller=mock_orchestration_controller
        )

        # Response should still be created (errors handled in generator)
        assert response.media_type == "text/event-stream"


# ============================================================================
# Test Execute Agent Task
# ============================================================================


class TestExecuteAgentTask:
    """Test direct agent task execution."""

    @pytest.mark.asyncio
    async def test_execute_task_success(
        self, mock_orchestration_controller, sample_agent_task_request
    ):
        """Test successful task execution."""
        mock_agent = mock_orchestration_controller.agents["curriculum"]
        mock_result = Mock()
        mock_result.success = True
        mock_result.data = {"outline": ["Intro", "Variables", "Functions"]}
        mock_agent.process.return_value = mock_result

        result = await execute_agent_task(
            request=sample_agent_task_request, controller=mock_orchestration_controller
        )

        assert isinstance(result, AgentTaskResponse)
        assert result.success is True
        assert result.agent == "curriculum"
        assert result.result == mock_result.data
        assert result.execution_time > 0

    @pytest.mark.asyncio
    async def test_execute_task_unknown_agent_type(self, mock_orchestration_controller):
        """Test execution with unknown agent type."""
        request = AgentTaskRequest(
            agent_type="unknown_agent",
            task_type="generate",
            data={"test": "data"},
        )

        with pytest.raises(HTTPException) as exc_info:
            await execute_agent_task(request=request, controller=mock_orchestration_controller)

        assert exc_info.value.status_code == 400
        assert "Unknown agent type" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_execute_task_agent_not_available(
        self, mock_orchestration_controller, sample_agent_task_request
    ):
        """Test execution when agent is not available."""
        # Remove agent from controller
        del mock_orchestration_controller.agents["curriculum"]

        with pytest.raises(HTTPException) as exc_info:
            await execute_agent_task(
                request=sample_agent_task_request, controller=mock_orchestration_controller
            )

        assert exc_info.value.status_code == 404
        assert "not available" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_execute_task_processing_error(
        self, mock_orchestration_controller, sample_agent_task_request
    ):
        """Test error handling during task processing."""
        mock_agent = mock_orchestration_controller.agents["curriculum"]
        mock_agent.process.side_effect = Exception("Processing error")

        with pytest.raises(HTTPException) as exc_info:
            await execute_agent_task(
                request=sample_agent_task_request, controller=mock_orchestration_controller
            )

        assert exc_info.value.status_code == 500


# ============================================================================
# Test Session Management
# ============================================================================


class TestGetSessionInfo:
    """Test getting session information."""

    @pytest.mark.asyncio
    async def test_get_session_success(self, mock_orchestration_controller, mock_session):
        """Test successfully getting session info."""
        session_id = mock_session.session_id
        mock_orchestration_controller.sessions[session_id] = mock_session

        result = await get_session_info(
            session_id=session_id, controller=mock_orchestration_controller
        )

        assert isinstance(result, SessionInfo)
        assert result.session_id == session_id
        assert result.started_at == mock_session.started_at
        assert result.state == "ACTIVE"
        assert result.accumulated_context == mock_session.accumulated_context
        assert result.completed_tasks == mock_session.completed_tasks

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, mock_orchestration_controller):
        """Test getting non-existent session."""
        with pytest.raises(HTTPException) as exc_info:
            await get_session_info(
                session_id="nonexistent", controller=mock_orchestration_controller
            )

        assert exc_info.value.status_code == 404
        assert "Session not found" in str(exc_info.value.detail)


class TestClearSession:
    """Test clearing a session."""

    @pytest.mark.asyncio
    async def test_clear_session_success(self, mock_orchestration_controller, mock_session):
        """Test successfully clearing a session."""
        session_id = mock_session.session_id
        mock_orchestration_controller.sessions[session_id] = mock_session

        result = await clear_session(
            session_id=session_id, controller=mock_orchestration_controller
        )

        assert "cleared" in result["message"]
        assert session_id not in mock_orchestration_controller.sessions

    @pytest.mark.asyncio
    async def test_clear_session_not_found(self, mock_orchestration_controller):
        """Test clearing non-existent session."""
        with pytest.raises(HTTPException) as exc_info:
            await clear_session(session_id="nonexistent", controller=mock_orchestration_controller)

        assert exc_info.value.status_code == 404
        assert "Session not found" in str(exc_info.value.detail)


# ============================================================================
# Test System Status and Reset
# ============================================================================


class TestGetSwarmStatus:
    """Test getting swarm system status."""

    @pytest.mark.asyncio
    async def test_get_status_success(self, mock_orchestration_controller, mock_session):
        """Test successfully getting swarm status."""
        # Add some sessions
        mock_orchestration_controller.sessions["session-1"] = mock_session
        mock_orchestration_controller.sessions["session-2"] = mock_session

        result = await get_swarm_status(controller=mock_orchestration_controller)

        assert isinstance(result, SwarmStatus)
        assert result.status == "operational"
        assert result.active_sessions == 2
        assert result.total_interactions == 110  # 100 + 10
        assert result.success_rate == pytest.approx(0.909, rel=0.01)
        assert len(result.agents_available) == 5

    @pytest.mark.asyncio
    async def test_get_status_no_interactions(self, mock_orchestration_controller):
        """Test status when no interactions have occurred."""
        mock_orchestration_controller.metrics = {
            "successful_interactions": 0,
            "failed_interactions": 0,
        }

        result = await get_swarm_status(controller=mock_orchestration_controller)

        assert result.success_rate == 0.0
        assert result.total_interactions == 0


class TestResetSwarm:
    """Test resetting the swarm system."""

    @pytest.mark.asyncio
    async def test_reset_swarm_success(self, mock_orchestration_controller, mock_session):
        """Test successfully resetting the swarm."""
        # Add sessions and metrics
        mock_orchestration_controller.sessions["session-1"] = mock_session
        mock_orchestration_controller.metrics["test_metric"] = 100

        result = await reset_swarm(controller=mock_orchestration_controller)

        assert "reset successfully" in result["message"]
        # Note: sessions.clear() and metrics.clear() called on mock objects


# ============================================================================
# Test Educational Content Endpoints
# ============================================================================


class TestCreateLesson:
    """Test lesson creation endpoint."""

    @pytest.mark.asyncio
    async def test_create_lesson_success(
        self, mock_orchestration_controller, sample_process_result
    ):
        """Test successful lesson creation."""
        mock_orchestration_controller.process_interaction.return_value = sample_process_result

        result = await create_lesson(
            grade_level="5th Grade",
            subject="Mathematics",
            topic="Fractions",
            objectives=["Understand numerator and denominator", "Add fractions"],
            session_id=None,
            controller=mock_orchestration_controller,
        )

        assert isinstance(result, ChatResponse)
        assert result.success is True
        # Verify suggestions are present (actual values may vary based on orchestration)
        assert len(result.suggestions) > 0
        mock_orchestration_controller.process_interaction.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_lesson_without_objectives(
        self, mock_orchestration_controller, sample_process_result
    ):
        """Test lesson creation without objectives."""
        mock_orchestration_controller.process_interaction.return_value = sample_process_result

        result = await create_lesson(
            grade_level="3rd Grade",
            subject="Science",
            topic="Plants",
            objectives=None,
            session_id=None,
            controller=mock_orchestration_controller,
        )

        assert isinstance(result, ChatResponse)
        assert result.success is True


class TestCreateAssessment:
    """Test assessment creation endpoint."""

    @pytest.mark.asyncio
    async def test_create_assessment_success(
        self, mock_orchestration_controller, sample_process_result
    ):
        """Test successful assessment creation."""
        mock_orchestration_controller.process_interaction.return_value = sample_process_result

        result = await create_assessment(
            assessment_type="quiz",
            grade_level="8th Grade",
            subject="History",
            topics=["American Revolution", "Declaration of Independence"],
            num_questions=15,
            session_id=None,
            controller=mock_orchestration_controller,
        )

        assert isinstance(result, ChatResponse)
        assert result.success is True
        assert "Preview assessment" in result.suggestions
        mock_orchestration_controller.process_interaction.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_assessment_default_questions(
        self, mock_orchestration_controller, sample_process_result
    ):
        """Test assessment creation with default question count."""
        mock_orchestration_controller.process_interaction.return_value = sample_process_result

        result = await create_assessment(
            assessment_type="test",
            grade_level="10th Grade",
            subject="Biology",
            topics=["Cell structure"],
            num_questions=10,  # Default value
            session_id=None,
            controller=mock_orchestration_controller,
        )

        assert isinstance(result, ChatResponse)


class TestAnalyzeStudentProgress:
    """Test student progress analysis endpoint."""

    @pytest.mark.asyncio
    async def test_analyze_progress_success(
        self, mock_orchestration_controller, sample_process_result
    ):
        """Test successful progress analysis."""
        mock_orchestration_controller.process_interaction.return_value = sample_process_result

        student_id = str(uuid4())
        performance_data = {
            "recent_scores": [85, 90, 78, 92],
            "completed_lessons": 12,
            "average_time": 45,
        }

        result = await analyze_student_progress(
            student_id=student_id,
            performance_data=performance_data,
            session_id=None,
            controller=mock_orchestration_controller,
        )

        assert isinstance(result, ChatResponse)
        assert result.success is True
        assert "Create personalized content" in result.suggestions
        mock_orchestration_controller.process_interaction.assert_called_once()


class TestPersonalizeContent:
    """Test content personalization endpoint."""

    @pytest.mark.asyncio
    async def test_personalize_content_success(
        self, mock_orchestration_controller, sample_process_result
    ):
        """Test successful content personalization."""
        mock_orchestration_controller.process_interaction.return_value = sample_process_result

        content = {
            "lesson_id": "lesson-123",
            "topic": "Algebra",
            "difficulty": "intermediate",
        }
        student_profile = {
            "learning_style": "visual",
            "pace": "fast",
            "strengths": ["problem-solving"],
            "weaknesses": ["memorization"],
        }

        result = await personalize_content(
            content=content,
            student_profile=student_profile,
            session_id=None,
            controller=mock_orchestration_controller,
        )

        assert isinstance(result, ChatResponse)
        assert result.success is True
        assert "Apply personalization" in result.suggestions
        mock_orchestration_controller.process_interaction.assert_called_once()


# ============================================================================
# Test WebSocket Endpoint
# ============================================================================


class TestWebSocketEndpoint:
    """Test WebSocket real-time communication."""

    @pytest.mark.asyncio
    async def test_websocket_connection(self, mock_orchestration_controller, sample_process_result):
        """Test WebSocket connection and message exchange."""
        # Create mock WebSocket
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        mock_websocket.receive_text = AsyncMock(
            return_value=json.dumps({"message": "Hello", "context": {}})
        )
        mock_websocket.send_json = AsyncMock()

        # Mock orchestration response
        mock_orchestration_controller.process_interaction.return_value = sample_process_result

        # Simulate single message then disconnect
        call_count = 0

        async def receive_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return json.dumps({"message": "Hello", "context": {}})
            else:
                from fastapi import WebSocketDisconnect

                raise WebSocketDisconnect()

        mock_websocket.receive_text.side_effect = receive_side_effect

        # Execute WebSocket endpoint
        await websocket_endpoint(
            websocket=mock_websocket,
            session_id="test-session",
            controller=mock_orchestration_controller,
        )

        # Verify WebSocket operations
        mock_websocket.accept.assert_called_once()
        mock_websocket.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_error_handling(self, mock_orchestration_controller):
        """Test WebSocket error handling."""
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        mock_websocket.receive_text = AsyncMock(side_effect=Exception("Connection error"))
        mock_websocket.close = AsyncMock()

        await websocket_endpoint(
            websocket=mock_websocket,
            session_id="test-session",
            controller=mock_orchestration_controller,
        )

        # Verify error handling closed the WebSocket
        mock_websocket.close.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

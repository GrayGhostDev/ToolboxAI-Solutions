"""Agent Swarm API Endpoints

Exposes the intelligent agent swarm functionality through REST APIs,
enabling natural, interactive conversations for educational content creation.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# Import the actual orchestration controller with real agents
from core.swarm.orchestration_controller import OrchestrationController


# Pydantic models for API
class ChatMessage(BaseModel):
    """User chat message."""

    message: str
    session_id: str | None = None
    context: dict[str, Any] | None = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """Chat response from agent swarm."""

    success: bool
    session_id: str
    message: str
    data: dict[str, Any] | None = None
    suggestions: list[str] | None = None
    context: dict[str, Any] | None = None


class AgentTaskRequest(BaseModel):
    """Direct agent task request."""

    agent_type: str
    task_type: str
    data: dict[str, Any]
    session_id: str | None = None


class AgentTaskResponse(BaseModel):
    """Agent task response."""

    success: bool
    agent: str
    result: dict[str, Any]
    execution_time: float


class SessionInfo(BaseModel):
    """Session information."""

    session_id: str
    started_at: datetime
    state: str
    accumulated_context: dict[str, Any]
    completed_tasks: list[str]


class SwarmStatus(BaseModel):
    """Swarm system status."""

    status: str
    active_sessions: int
    total_interactions: int
    success_rate: float
    agents_available: list[str]


# Create router
router = APIRouter(prefix="/api/v1/swarm", tags=["Agent Swarm"])

# Initialize orchestration controller
orchestration_controller = None
logger = logging.getLogger(__name__)


def get_orchestration_controller() -> OrchestrationController:
    """Get or create orchestration controller singleton."""
    global orchestration_controller
    if orchestration_controller is None:
        orchestration_controller = OrchestrationController()
        logger.info("Orchestration Controller initialized")
    return orchestration_controller


@router.post("/chat", response_model=ChatResponse)
async def chat_with_swarm(
    request: ChatMessage,
    controller: OrchestrationController = Depends(get_orchestration_controller),
) -> ChatResponse:
    """
    Main chat endpoint for natural language interaction with the agent swarm.

    This endpoint handles conversational interactions, maintaining context
    and providing intelligent, helpful responses for educational content creation.
    """
    try:
        # Process interaction through orchestration
        result = await controller.process_interaction(
            user_input=request.message, session_id=request.session_id, user_context=request.context
        )

        # Extract response components
        response_data = result.get("response", {})

        return ChatResponse(
            success=result["success"],
            session_id=result["session_id"],
            message=response_data.get("message", ""),
            data=response_data.get("data"),
            suggestions=response_data.get("suggestions", []),
            context=result.get("context"),
        )

    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(
    request: ChatMessage,
    controller: OrchestrationController = Depends(get_orchestration_controller),
):
    """
    Streaming chat endpoint for real-time responses.

    Returns server-sent events for progressive response generation.
    """

    async def generate():
        try:
            # Start with thinking indicator
            yield f"data: {json.dumps({'type': 'thinking', 'message': 'Processing your request...'})}\n\n"

            # Process interaction
            result = await controller.process_interaction(
                user_input=request.message,
                session_id=request.session_id,
                user_context=request.context,
            )

            # Stream the response in chunks
            response_data = result.get("response", {})
            message = response_data.get("message", "")

            # Split message into sentences for streaming
            sentences = message.split(". ")
            for i, sentence in enumerate(sentences):
                if sentence:
                    chunk = {
                        "type": "content",
                        "message": sentence + ("." if not sentence.endswith(".") else ""),
                        "progress": (i + 1) / len(sentences),
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"
                    await asyncio.sleep(0.1)  # Small delay for effect

            # Send completion with metadata
            completion = {
                "type": "complete",
                "session_id": result["session_id"],
                "suggestions": response_data.get("suggestions", []),
                "data": response_data.get("data"),
            }
            yield f"data: {json.dumps(completion)}\n\n"

        except Exception as e:
            error = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post("/task", response_model=AgentTaskResponse)
async def execute_agent_task(
    request: AgentTaskRequest,
    controller: OrchestrationController = Depends(get_orchestration_controller),
) -> AgentTaskResponse:
    """
    Execute a specific task on a specific agent.

    This endpoint allows direct agent invocation for specialized tasks.
    """
    try:
        start_time = datetime.now()

        # Map agent type to agent name
        agent_mapping = {
            "curriculum": "curriculum",
            "analytics": "analytics",
            "assessment": "assessment",
            "validation": "validation",
            "adaptive": "adaptive",
        }

        agent_name = agent_mapping.get(request.agent_type)
        if not agent_name:
            raise HTTPException(status_code=400, detail=f"Unknown agent type: {request.agent_type}")

        # Get agent
        if agent_name not in controller.agents:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not available")

        agent = controller.agents[agent_name]

        # Prepare task data
        task_data = {
            **request.data,
            "task_type": request.task_type,
            "session_id": request.session_id,
        }

        # Execute task
        result = await agent.process(task_data)

        execution_time = (datetime.now() - start_time).total_seconds()

        return AgentTaskResponse(
            success=result.success,
            agent=agent_name,
            result=result.data if hasattr(result, "data") else {},
            execution_time=execution_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Task execution error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}", response_model=SessionInfo)
async def get_session_info(
    session_id: str, controller: OrchestrationController = Depends(get_orchestration_controller)
) -> SessionInfo:
    """
    Get information about a specific session.

    Returns session state, context, and completed tasks.
    """
    if session_id not in controller.sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = controller.sessions[session_id]

    return SessionInfo(
        session_id=session_id,
        started_at=session.started_at,
        state=session.current_state.value,
        accumulated_context=session.accumulated_context,
        completed_tasks=session.completed_tasks,
    )


@router.delete("/session/{session_id}")
async def clear_session(
    session_id: str, controller: OrchestrationController = Depends(get_orchestration_controller)
) -> dict[str, str]:
    """
    Clear a specific session.

    Removes session data and resets context.
    """
    if session_id in controller.sessions:
        del controller.sessions[session_id]
        return {"message": f"Session {session_id} cleared"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@router.get("/status", response_model=SwarmStatus)
async def get_swarm_status(
    controller: OrchestrationController = Depends(get_orchestration_controller),
) -> SwarmStatus:
    """
    Get the current status of the agent swarm system.

    Returns system health, metrics, and available agents.
    """
    # Calculate success rate
    total = controller.metrics.get("successful_interactions", 0) + controller.metrics.get(
        "failed_interactions", 0
    )
    success_rate = controller.metrics["successful_interactions"] / total if total > 0 else 0.0

    return SwarmStatus(
        status="operational",
        active_sessions=len(controller.sessions),
        total_interactions=total,
        success_rate=success_rate,
        agents_available=list(controller.agents.keys()),
    )


@router.post("/reset")
async def reset_swarm(
    controller: OrchestrationController = Depends(get_orchestration_controller),
) -> dict[str, str]:
    """
    Reset the agent swarm system.

    Clears all sessions and resets metrics.
    """
    # Clear all sessions
    controller.sessions.clear()

    # Reset metrics
    controller.metrics.clear()

    return {"message": "Swarm system reset successfully"}


# Educational content specific endpoints


@router.post("/lesson/create")
async def create_lesson(
    grade_level: str,
    subject: str,
    topic: str,
    objectives: list[str] | None = None,
    session_id: str | None = None,
    controller: OrchestrationController = Depends(get_orchestration_controller),
) -> ChatResponse:
    """
    Create a complete lesson plan.

    This endpoint orchestrates multiple agents to create a comprehensive,
    standards-aligned lesson with assessments and personalization.
    """
    # Build natural language request
    message = f"Create a {subject} lesson for {grade_level} on {topic}."
    if objectives:
        message += f" The learning objectives are: {', '.join(objectives)}."

    # Process through orchestration
    result = await controller.process_interaction(
        user_input=message,
        session_id=session_id,
        user_context={
            "task": "create_lesson",
            "grade_level": grade_level,
            "subject": subject,
            "topic": topic,
            "objectives": objectives,
        },
    )

    response_data = result.get("response", {})

    return ChatResponse(
        success=result["success"],
        session_id=result["session_id"],
        message=response_data.get("message", ""),
        data=response_data.get("data"),
        suggestions=["Create assessment", "Add game elements", "Generate practice materials"],
    )


@router.post("/assessment/create")
async def create_assessment(
    assessment_type: str,
    grade_level: str,
    subject: str,
    topics: list[str],
    num_questions: int = 10,
    session_id: str | None = None,
    controller: OrchestrationController = Depends(get_orchestration_controller),
) -> ChatResponse:
    """
    Create an assessment or quiz.

    Generates questions, answer keys, and rubrics based on specifications.
    """
    # Build natural language request
    message = (
        f"Create a {assessment_type} for {grade_level} {subject} covering {', '.join(topics)}. "
    )
    message += f"Include {num_questions} questions."

    # Process through orchestration
    result = await controller.process_interaction(
        user_input=message,
        session_id=session_id,
        user_context={
            "task": "create_assessment",
            "assessment_type": assessment_type,
            "grade_level": grade_level,
            "subject": subject,
            "topics": topics,
            "num_questions": num_questions,
        },
    )

    response_data = result.get("response", {})

    return ChatResponse(
        success=result["success"],
        session_id=result["session_id"],
        message=response_data.get("message", ""),
        data=response_data.get("data"),
        suggestions=["Preview assessment", "Add time limit", "Create answer key"],
    )


@router.post("/analyze/progress")
async def analyze_student_progress(
    student_id: str,
    performance_data: dict[str, Any],
    session_id: str | None = None,
    controller: OrchestrationController = Depends(get_orchestration_controller),
) -> ChatResponse:
    """
    Analyze student progress and provide insights.

    Uses learning analytics to identify patterns and recommend interventions.
    """
    # Build natural language request
    message = f"Analyze the progress for student {student_id} and provide recommendations."

    # Process through orchestration
    result = await controller.process_interaction(
        user_input=message,
        session_id=session_id,
        user_context={
            "task": "analyze_progress",
            "student_id": student_id,
            "performance_data": performance_data,
        },
    )

    response_data = result.get("response", {})

    return ChatResponse(
        success=result["success"],
        session_id=result["session_id"],
        message=response_data.get("message", ""),
        data=response_data.get("data"),
        suggestions=["Create personalized content", "Adjust difficulty", "Generate report"],
    )


@router.post("/personalize")
async def personalize_content(
    content: dict[str, Any],
    student_profile: dict[str, Any],
    session_id: str | None = None,
    controller: OrchestrationController = Depends(get_orchestration_controller),
) -> ChatResponse:
    """
    Personalize content for a specific student.

    Adapts content based on learning style, pace, and performance.
    """
    # Build natural language request
    message = "Personalize this content based on the student's learning profile."

    # Process through orchestration
    result = await controller.process_interaction(
        user_input=message,
        session_id=session_id,
        user_context={
            "task": "personalize",
            "content": content,
            "student_profile": student_profile,
        },
    )

    response_data = result.get("response", {})

    return ChatResponse(
        success=result["success"],
        session_id=result["session_id"],
        message=response_data.get("message", ""),
        data=response_data.get("data"),
        suggestions=["Apply personalization", "Preview changes", "Save profile"],
    )


# WebSocket endpoint for real-time interaction (if needed)
from fastapi import WebSocket, WebSocketDisconnect


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    controller: OrchestrationController = Depends(get_orchestration_controller),
):
    """
    WebSocket endpoint for real-time bidirectional communication.

    Maintains persistent connection for interactive conversations.
    """
    await websocket.accept()

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # Process through orchestration
            result = await controller.process_interaction(
                user_input=message_data.get("message", ""),
                session_id=session_id,
                user_context=message_data.get("context", {}),
            )

            # Send response
            await websocket.send_json({"type": "response", "data": result})

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close()

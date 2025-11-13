"""
Coordinator API Router - Exposes Agent Coordinator functionality

This router provides API endpoints for agent coordination, content generation,
and system health monitoring with full LangChain tracing and Pusher integration.
"""

import logging
from datetime import datetime
from typing import Any

from apps.backend.models.user import User
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from apps.backend.core.auth import get_current_user
from apps.backend.services.coordinator_service import (
    CoordinatorService,
    get_coordinator,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/coordinators",
    tags=["coordinators", "agents"],
    responses={404: {"description": "Not found"}, 500: {"description": "Internal server error"}},
)


# Request/Response Models
class ContentGenerationRequest(BaseModel):
    """Request model for content generation."""

    subject: str = Field(..., description="Subject matter for content")
    grade_level: int = Field(..., ge=1, le=12, description="Grade level (1-12)")
    learning_objectives: list[str] = Field(..., description="List of learning objectives")
    environment_type: str = Field(
        default="interactive_classroom", description="Type of Roblox environment to generate"
    )
    include_quiz: bool = Field(default=True, description="Include quiz generation")
    include_gamification: bool = Field(default=True, description="Include gamification elements")
    difficulty_level: str = Field(default="medium", description="Content difficulty level")
    custom_parameters: dict[str, Any] | None = Field(
        default=None, description="Additional custom parameters for generation"
    )

    class Config:
        schema_extra = {
            "example": {
                "subject": "Mathematics",
                "grade_level": 7,
                "learning_objectives": [
                    "Understand fractions",
                    "Perform fraction operations",
                    "Apply fractions in real-world problems",
                ],
                "environment_type": "interactive_classroom",
                "include_quiz": True,
                "include_gamification": True,
                "difficulty_level": "medium",
            }
        }


class ContentGenerationResponse(BaseModel):
    """Response model for content generation."""

    success: bool
    request_id: str
    content: dict[str, Any] | None
    scripts: list[str] | None
    quiz_data: dict[str, Any] | None
    metrics: dict[str, Any]
    generation_time: float
    trace_url: str | None = Field(default=None, description="LangSmith trace URL for debugging")
    message: str | None = None


class HealthResponse(BaseModel):
    """Response model for health checks."""

    status: str
    healthy: bool
    timestamp: str
    components: dict[str, str]
    active_workflows: int
    resource_utilization: dict[str, float]
    error_count: int
    last_error: str | None


class AgentStatusResponse(BaseModel):
    """Response model for agent status."""

    agent_name: str
    status: str
    current_task: str | None
    progress: float
    last_activity: str
    metrics: dict[str, Any]


# API Endpoints
@router.post("/generate", response_model=ContentGenerationResponse)
async def generate_educational_content(
    request: ContentGenerationRequest,
    background_tasks: BackgroundTasks,
    coordinator: CoordinatorService = Depends(get_coordinator),
    current_user: User = Depends(get_current_user),
):
    """
    Generate educational content using the agent coordinator system.

    This endpoint orchestrates multiple AI agents to create comprehensive
    educational environments for Roblox, including content, scripts, terrain,
    quizzes, and more.

    All operations are traced in LangSmith for monitoring and debugging.
    """
    try:
        logger.info(f"Content generation requested by user {current_user.id}")

        # Validate request
        if not request.learning_objectives:
            raise HTTPException(
                status_code=400, detail="At least one learning objective is required"
            )

        # Generate content
        result = await coordinator.generate_educational_content(
            subject=request.subject,
            grade_level=request.grade_level,
            learning_objectives=request.learning_objectives,
            environment_type=request.environment_type,
            include_quiz=request.include_quiz,
            custom_parameters={
                "user_id": current_user.id,
                "include_gamification": request.include_gamification,
                "difficulty_level": request.difficulty_level,
                **(request.custom_parameters or {}),
            },
        )

        # Get LangSmith trace URL if available
        trace_url = None
        if hasattr(coordinator, "tracer") and hasattr(coordinator.tracer, "get_run_url"):
            trace_url = coordinator.tracer.get_run_url()

        return ContentGenerationResponse(
            success=result["success"],
            request_id=result["request_id"],
            content=result.get("content"),
            scripts=result.get("scripts"),
            quiz_data=result.get("quiz_data"),
            metrics=result.get("metrics", {}),
            generation_time=result.get("generation_time", 0.0),
            trace_url=trace_url,
            message="Content generated successfully" if result["success"] else "Generation failed",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Content generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Content generation failed: {str(e)}")


@router.get("/health", response_model=HealthResponse)
async def get_coordinator_health(coordinator: CoordinatorService = Depends(get_coordinator)):
    """
    Get health status of the coordinator system.

    Returns detailed health information about all coordinator components,
    including active workflows, resource utilization, and error counts.
    """
    try:
        health = await coordinator.get_health_status()

        return HealthResponse(
            status=health["status"],
            healthy=health["healthy"],
            timestamp=health["timestamp"],
            components=health.get("components", {}),
            active_workflows=health.get("active_workflows", 0),
            resource_utilization=health.get("resource_utilization", {}),
            error_count=health.get("error_count", 0),
            last_error=health.get("last_error"),
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="error",
            healthy=False,
            timestamp=datetime.now().isoformat(),
            components={},
            active_workflows=0,
            resource_utilization={},
            error_count=1,
            last_error=str(e),
        )


@router.get("/agents", response_model=list[AgentStatusResponse])
async def get_agent_statuses(
    coordinator: CoordinatorService = Depends(get_coordinator),
    current_user: User = Depends(get_current_user),
):
    """
    Get status of all active agents in the system.

    Returns information about each agent's current state, active tasks,
    and performance metrics.
    """
    try:
        # This would typically query the agent registry
        # For now, return mock data showing available agents
        agents = [
            {
                "agent_name": "ContentAgent",
                "status": "idle",
                "current_task": None,
                "progress": 0.0,
                "last_activity": datetime.now().isoformat(),
                "metrics": {"tasks_completed": 0, "avg_time": 0},
            },
            {
                "agent_name": "QuizAgent",
                "status": "idle",
                "current_task": None,
                "progress": 0.0,
                "last_activity": datetime.now().isoformat(),
                "metrics": {"quizzes_generated": 0},
            },
            {
                "agent_name": "ScriptAgent",
                "status": "idle",
                "current_task": None,
                "progress": 0.0,
                "last_activity": datetime.now().isoformat(),
                "metrics": {"scripts_generated": 0},
            },
        ]

        return [AgentStatusResponse(**agent) for agent in agents]

    except Exception as e:
        logger.error(f"Failed to get agent statuses: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve agent statuses: {str(e)}")


@router.post("/agents/{agent_name}/execute")
async def execute_agent_task(
    agent_name: str,
    task: dict[str, Any],
    background_tasks: BackgroundTasks,
    coordinator: CoordinatorService = Depends(get_coordinator),
    current_user: User = Depends(get_current_user),
):
    """
    Execute a specific task on a named agent.

    This endpoint allows direct task execution on individual agents
    for more granular control over the generation process.
    """
    try:
        # Validate agent exists
        valid_agents = ["content", "quiz", "terrain", "script", "review", "testing", "supervisor"]

        if agent_name.lower() not in valid_agents:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

        # This would execute the task on the specific agent
        # For now, return a mock response
        return {
            "success": True,
            "agent": agent_name,
            "task_id": f"task_{datetime.now().timestamp()}",
            "status": "queued",
            "message": f"Task queued for {agent_name}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Task execution failed: {str(e)}")


@router.get("/workflows")
async def get_active_workflows(
    coordinator: CoordinatorService = Depends(get_coordinator),
    current_user: User = Depends(get_current_user),
):
    """
    Get list of active workflows in the coordinator system.

    Returns information about currently running content generation workflows,
    their progress, and estimated completion times.
    """
    try:
        # This would query the workflow coordinator
        # For now, return empty list or mock data
        return {"workflows": [], "total": 0, "timestamp": datetime.now().isoformat()}

    except Exception as e:
        logger.error(f"Failed to get workflows: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve workflows: {str(e)}")


@router.delete("/workflows/{workflow_id}")
async def cancel_workflow(
    workflow_id: str,
    coordinator: CoordinatorService = Depends(get_coordinator),
    current_user: User = Depends(get_current_user),
):
    """
    Cancel an active workflow.

    Attempts to gracefully stop a running workflow and clean up any
    resources that were allocated.
    """
    try:
        # This would cancel the workflow
        # For now, return success
        return {
            "success": True,
            "workflow_id": workflow_id,
            "status": "cancelled",
            "message": "Workflow cancelled successfully",
        }

    except Exception as e:
        logger.error(f"Failed to cancel workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel workflow: {str(e)}")

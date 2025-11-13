"""
Agent system endpoints
"""

import asyncio
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel

from apps.backend.agents.agent import (
    get_agent_health,
    initialize_agents,
    shutdown_agents,
)
from apps.backend.core.dependencies import (
    get_admin_user,
    get_agent_service,
    get_current_active_user,
    validate_agent_id,
)
from apps.backend.core.exceptions import (
    ExternalServiceError,
    NotFoundError,
    ValidationError,
)
from apps.backend.core.logging import logging_manager
from apps.backend.models.schemas import BaseResponse, User

# Initialize logger
logger = logging_manager.get_logger(__name__)

# Create router
router = APIRouter()


# Pydantic models for agent endpoints
class AgentExecuteRequest(BaseModel):
    agent_type: str
    task: str
    parameters: dict[str, Any] | None = {}
    priority: int | None = 1


class AgentHealthResponse(BaseModel):
    agent_id: str
    status: str
    uptime: float
    last_heartbeat: str | None = None
    metrics: dict[str, Any] | None = {}


class AgentListResponse(BaseModel):
    agents: list[dict[str, Any]]
    total: int
    active: int
    inactive: int


@router.get("/health", response_model=list[AgentHealthResponse])
async def get_agents_health(current_user: User = Depends(get_current_active_user)):
    """Get health status of all agents"""
    try:
        health_data = await get_agent_health()

        if not health_data:
            raise NotFoundError("No agents found or agent system not initialized")

        # Transform the health data to match response model
        health_responses = []
        for agent_id, health_info in health_data.items():
            health_responses.append(
                AgentHealthResponse(
                    agent_id=agent_id,
                    status=health_info.get("status", "unknown"),
                    uptime=health_info.get("uptime", 0.0),
                    last_heartbeat=health_info.get("last_heartbeat"),
                    metrics=health_info.get("metrics", {}),
                )
            )

        logger.info(
            f"Retrieved health for {len(health_responses)} agents",
            extra={"user_id": getattr(current_user, "id", "unknown")},
        )

        return health_responses

    except Exception as e:
        logger.error(f"Failed to get agent health: {e}")
        raise ExternalServiceError(
            detail="Failed to retrieve agent health information", service="agent_system"
        )


@router.get("/list", response_model=AgentListResponse)
async def list_agents(current_user: User = Depends(get_current_active_user)):
    """List all available agents"""
    try:
        # Get agent service
        agent_service = get_agent_service()
        if not agent_service:
            raise ExternalServiceError(
                detail="Agent service not available", service="agent_service"
            )

        agents = await agent_service.list_agents()

        active_count = sum(1 for agent in agents if agent.get("status") == "active")
        inactive_count = len(agents) - active_count

        response = AgentListResponse(
            agents=agents, total=len(agents), active=active_count, inactive=inactive_count
        )

        logger.info(
            f"Listed {len(agents)} agents",
            extra={
                "user_id": getattr(current_user, "id", "unknown"),
                "active_agents": active_count,
                "inactive_agents": inactive_count,
            },
        )

        return response

    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise ExternalServiceError(detail="Failed to list agents", service="agent_system")


@router.post("/execute", response_model=BaseResponse)
async def execute_agent_task(
    request: AgentExecuteRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
):
    """Execute a task using an agent"""
    try:
        # Validate request
        if not request.agent_type or not request.task:
            raise ValidationError("Agent type and task are required")

        # Get agent service
        agent_service = get_agent_service()
        if not agent_service:
            raise ExternalServiceError(
                detail="Agent service not available", service="agent_service"
            )

        # Execute task in background
        background_tasks.add_task(
            _execute_agent_task_background,
            agent_service,
            request.agent_type,
            request.task,
            request.parameters,
            getattr(current_user, "id", "unknown"),
        )

        logger.info(
            f"Agent task queued: {request.agent_type}",
            extra={
                "agent_type": request.agent_type,
                "user_id": getattr(current_user, "id", "unknown"),
                "task_length": len(request.task),
            },
        )

        return BaseResponse(
            success=True,
            message=f"Task queued for {request.agent_type} agent",
            data={
                "agent_type": request.agent_type,
                "task_id": f"task_{asyncio.current_task().get_name()}",
            },
        )

    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Failed to execute agent task: {e}")
        raise ExternalServiceError(detail="Failed to execute agent task", service="agent_system")


@router.get("/{agent_id}/status")
async def get_agent_status(
    agent_id: str = Depends(validate_agent_id),
    current_user: User = Depends(get_current_active_user),
):
    """Get status of a specific agent"""
    try:
        agent_service = get_agent_service()
        if not agent_service:
            raise ExternalServiceError(
                detail="Agent service not available", service="agent_service"
            )

        status_info = await agent_service.get_agent_status(agent_id)

        if not status_info:
            raise NotFoundError(
                detail=f"Agent {agent_id} not found", resource_type="agent", resource_id=agent_id
            )

        logger.info(
            f"Retrieved status for agent {agent_id}",
            extra={"agent_id": agent_id, "user_id": getattr(current_user, "id", "unknown")},
        )

        return BaseResponse(
            success=True,
            message=f"Agent {agent_id} status retrieved successfully",
            data=status_info,
        )

    except (NotFoundError, ExternalServiceError):
        raise
    except Exception as e:
        logger.error(f"Failed to get agent status: {e}")
        raise ExternalServiceError(detail="Failed to retrieve agent status", service="agent_system")


@router.post("/{agent_id}/restart")
async def restart_agent(
    agent_id: str = Depends(validate_agent_id), current_user: User = Depends(get_admin_user)
):
    """Restart a specific agent (admin only)"""
    try:
        agent_service = get_agent_service()
        if not agent_service:
            raise ExternalServiceError(
                detail="Agent service not available", service="agent_service"
            )

        success = await agent_service.restart_agent(agent_id)

        if not success:
            raise ExternalServiceError(
                detail=f"Failed to restart agent {agent_id}", service="agent_system"
            )

        logger.info(
            f"Agent {agent_id} restarted by admin",
            extra={"agent_id": agent_id, "admin_id": getattr(current_user, "id", "unknown")},
        )

        return BaseResponse(success=True, message=f"Agent {agent_id} restarted successfully")

    except ExternalServiceError:
        raise
    except Exception as e:
        logger.error(f"Failed to restart agent: {e}")
        raise ExternalServiceError(detail="Failed to restart agent", service="agent_system")


@router.post("/initialize")
async def initialize_agent_system(current_user: User = Depends(get_admin_user)):
    """Initialize the agent system (admin only)"""
    try:
        await initialize_agents()

        logger.info(
            "Agent system initialized",
            extra={"admin_id": getattr(current_user, "id", "unknown")},
        )

        return BaseResponse(success=True, message="Agent system initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize agent system: {e}")
        raise ExternalServiceError(
            detail="Failed to initialize agent system", service="agent_system"
        )


@router.post("/shutdown")
async def shutdown_agent_system(current_user: User = Depends(get_admin_user)):
    """Shutdown the agent system (admin only)"""
    try:
        await shutdown_agents()

        logger.warning(
            "Agent system shutdown",
            extra={"admin_id": getattr(current_user, "id", "unknown")},
        )

        return BaseResponse(success=True, message="Agent system shutdown successfully")

    except Exception as e:
        logger.error(f"Failed to shutdown agent system: {e}")
        raise ExternalServiceError(detail="Failed to shutdown agent system", service="agent_system")


# Background task function
async def _execute_agent_task_background(
    agent_service, agent_type: str, task: str, parameters: dict[str, Any], user_id: str
):
    """Execute agent task in background"""
    try:
        result = await agent_service.execute_task(
            agent_type=agent_type, task=task, parameters=parameters, user_id=user_id
        )

        logger.info(
            f"Agent task completed: {agent_type}",
            extra={
                "agent_type": agent_type,
                "user_id": user_id,
                "result_status": result.get("status", "unknown"),
            },
        )

    except Exception as e:
        logger.error(
            f"Background agent task failed: {e}",
            extra={"agent_type": agent_type, "user_id": user_id},
        )

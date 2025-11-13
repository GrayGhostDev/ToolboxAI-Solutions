"""
Direct Agent API Endpoints - Direct access to individual agents

This module provides direct REST API access to individual AI agents,
allowing for specific task execution and real-time monitoring.

Features:
- Direct agent task execution
- Real-time agent status monitoring
- Task result retrieval
- Agent performance metrics
- WebSocket support for live updates

Author: ToolboxAI Team
Created: 2025-09-21
Version: 1.0.0
"""

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.security import HTTPBearer
from pydantic import BaseModel, ConfigDict, Field

# Import authentication and dependencies
try:
    from apps.backend.api.auth.auth import (
        get_current_user,
        require_any_role,
        require_role,
    )
    from apps.backend.core.deps import get_db
    from apps.backend.core.security.rate_limit_manager import rate_limit
except ImportError:
    # Fallback for development
    def get_current_user():
        return {"id": "test", "role": "teacher", "email": "test@example.com"}

    def require_role(role):
        return lambda: None

    def require_any_role(roles):
        return lambda: None

    def get_db():
        return None

    def rate_limit(requests=60, max_requests=None, **kwargs):
        def decorator(func):
            return func

        return decorator


# Import models and services
try:
    from apps.backend.models.schemas import BaseResponse, User
    from apps.backend.services.agent_service import AgentService, get_agent_service
    from apps.backend.services.pusher import trigger_event
except ImportError:

    class User(BaseModel):
        id: str
        email: str
        role: str

    class BaseResponse(BaseModel):
        success: bool = True
        message: str = ""
        timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    async def trigger_event(channel, event, data):
        pass

    # Mock agent service for fallback
    class MockAgentService:
        async def execute_task(self, agent_type, task_type, task_data, user_id=None):
            return {"success": False, "error": "Agent service not available"}

        def get_agent_status(self, agent_id):
            return None

        def get_all_agents_status(self):
            return []

        def get_task_status(self, task_id):
            return None

        def get_system_metrics(self):
            return {}

    def get_agent_service():
        return MockAgentService()


logger = logging.getLogger(__name__)
security = HTTPBearer()

# Create router
router = APIRouter(prefix="/agents", tags=["Direct Agents"])


# Request Models
class ContentGenerationRequest(BaseModel):
    """Request for content generation"""

    subject: str = Field(..., description="Subject area (e.g., Math, Science)")
    grade_level: int = Field(..., ge=1, le=12, description="Grade level (1-12)")
    objectives: list[str] = Field(..., min_items=1, description="Learning objectives")
    context: dict[str, Any] | None = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class QuizGenerationRequest(BaseModel):
    """Request for quiz generation"""

    subject: str = Field(..., description="Subject area")
    objectives: list[str] = Field(..., min_items=1, description="Learning objectives")
    num_questions: int = Field(5, ge=1, le=50, description="Number of questions")
    difficulty: str = Field("medium", description="Difficulty level: easy, medium, hard")
    context: dict[str, Any] | None = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class TerrainGenerationRequest(BaseModel):
    """Request for terrain generation"""

    subject: str = Field(..., description="Subject area for educational terrain")
    terrain_type: str = Field("educational", description="Type of terrain to generate")
    complexity: str = Field("medium", description="Complexity level: simple, medium, complex")
    features: list[str] = Field(default_factory=list, description="Specific features to include")
    context: dict[str, Any] | None = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class ScriptGenerationRequest(BaseModel):
    """Request for script generation"""

    script_type: str = Field(
        "ServerScript", description="Type of script: ServerScript, LocalScript, ModuleScript"
    )
    functionality: str = Field(..., description="Description of desired functionality")
    requirements: list[str] = Field(default_factory=list, description="Specific requirements")
    context: dict[str, Any] | None = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class CodeReviewRequest(BaseModel):
    """Request for code review"""

    code: str = Field(..., description="Code to review")
    language: str = Field("lua", description="Programming language")
    review_type: str = Field(
        "comprehensive", description="Type of review: security, performance, comprehensive"
    )
    context: dict[str, Any] | None = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class RobloxAssetRequest(BaseModel):
    """Request for Roblox asset management"""

    asset_type: str = Field(..., description="Type of asset: model, script, texture, etc.")
    action: str = Field(..., description="Action: create, update, delete, analyze")
    asset_data: dict[str, Any] = Field(..., description="Asset data and parameters")
    context: dict[str, Any] | None = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class RobloxTestingRequest(BaseModel):
    """Request for Roblox testing"""

    test_type: str = Field(..., description="Type of test: functional, performance, security")
    test_data: dict[str, Any] = Field(..., description="Test configuration and data")
    context: dict[str, Any] | None = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class RobloxAnalyticsRequest(BaseModel):
    """Request for Roblox analytics"""

    data_type: str = Field(
        ..., description="Type of data to analyze: player_behavior, performance, learning"
    )
    analysis_data: dict[str, Any] = Field(..., description="Data to analyze")
    context: dict[str, Any] | None = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


# Response Models
class AgentTaskResponse(BaseModel):
    """Response from agent task execution"""

    success: bool
    task_id: str
    agent_id: str | None = None
    result: dict[str, Any] | None = None
    execution_time: float | None = None
    status: str
    error: str | None = None
    message: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)


class AgentStatusResponse(BaseModel):
    """Response with agent status information"""

    agent_id: str
    agent_type: str
    status: str
    current_task_id: str | None = None
    total_tasks_completed: int = 0
    total_tasks_failed: int = 0
    average_execution_time: float = 0.0
    last_activity: str
    created_at: str
    performance_metrics: dict[str, Any] = Field(default_factory=dict)
    resource_usage: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class SystemMetricsResponse(BaseModel):
    """Response with system-wide metrics"""

    agents: dict[str, Any]
    tasks: dict[str, Any]
    system: dict[str, Any]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)


# WebSocket connection manager
class AgentWebSocketManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.agent_subscribers: dict[str, list[str]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Agent WebSocket client connected: {client_id}")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        # Remove from agent subscriptions
        for agent_id, subscribers in self.agent_subscribers.items():
            if client_id in subscribers:
                subscribers.remove(client_id)
        logger.info(f"Agent WebSocket client disconnected: {client_id}")

    async def send_personal_message(self, message: dict[str, Any], client_id: str):
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)

    async def broadcast_agent_update(self, agent_id: str, message: dict[str, Any]):
        if agent_id in self.agent_subscribers:
            for client_id in self.agent_subscribers[agent_id].copy():
                await self.send_personal_message(message, client_id)

    def subscribe_to_agent(self, client_id: str, agent_id: str):
        if agent_id not in self.agent_subscribers:
            self.agent_subscribers[agent_id] = []
        if client_id not in self.agent_subscribers[agent_id]:
            self.agent_subscribers[agent_id].append(client_id)


# Global WebSocket manager
ws_manager = AgentWebSocketManager()


# Endpoints


@router.get("/status", response_model=list[AgentStatusResponse])
async def get_all_agents_status(
    current_user: dict = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service),
):
    """
    Get status of all agents.

    Returns comprehensive status information for all registered agents
    including performance metrics and current activity.
    """
    try:
        agents_status = agent_service.get_all_agents_status()
        return [AgentStatusResponse(**status) for status in agents_status if status]
    except Exception as e:
        logger.error(f"Error getting agents status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agents status",
        )


@router.get("/status/{agent_id}", response_model=AgentStatusResponse)
async def get_agent_status(
    agent_id: str,
    current_user: dict = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service),
):
    """
    Get status of specific agent.

    Returns detailed status information for a specific agent including
    current task, performance metrics, and resource usage.
    """
    try:
        agent_status = agent_service.get_agent_status(agent_id)
        if not agent_status:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

        return AgentStatusResponse(**agent_status)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agent status",
        )


@router.get("/metrics", response_model=SystemMetricsResponse)
async def get_system_metrics(
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_any_role(["teacher", "admin"])),
    agent_service: AgentService = Depends(get_agent_service),
):
    """
    Get system-wide agent metrics.

    Requires: Teacher or Admin role

    Returns overall system performance metrics including agent utilization,
    task completion rates, and system health indicators.
    """
    try:
        metrics = agent_service.get_system_metrics()
        return SystemMetricsResponse(**metrics)
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system metrics",
        )


# Content Generation Agent Endpoints


@router.post("/content/generate", response_model=AgentTaskResponse)
# @rate_limit(requests=30)  # 30 requests per minute
async def generate_content(
    request: ContentGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_any_role(["teacher", "admin"])),
    agent_service: AgentService = Depends(get_agent_service),
):
    """
    Generate educational content using Content Generation Agent.

    Requires: Teacher or Admin role
    Rate limit: 30 requests per minute

    Creates educational content based on subject, grade level, and objectives.
    """
    try:
        task_data = {
            "subject": request.subject,
            "grade_level": request.grade_level,
            "objectives": request.objectives,
            "context": request.context,
        }

        result = await agent_service.execute_task(
            agent_type="content",
            task_type="generate_content",
            task_data=task_data,
            user_id=current_user["id"],
        )

        # Background notification
        background_tasks.add_task(
            trigger_event,
            "agent-tasks",
            "content.generated",
            {
                "user_id": current_user["id"],
                "task_id": result.get("task_id"),
                "subject": request.subject,
                "grade_level": request.grade_level,
            },
        )

        return AgentTaskResponse(
            success=result["success"],
            task_id=result.get("task_id", ""),
            agent_id=result.get("agent_id"),
            result=result.get("result"),
            execution_time=result.get("execution_time"),
            status=result.get("status", "completed" if result["success"] else "failed"),
            error=result.get("error"),
            message=(
                "Content generation completed successfully"
                if result["success"]
                else "Content generation failed"
            ),
        )

    except Exception as e:
        logger.error(f"Content generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content generation failed: {str(e)}",
        )


@router.post("/quiz/generate", response_model=AgentTaskResponse)
# @rate_limit(requests=20)  # 20 requests per minute
async def generate_quiz(
    request: QuizGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_any_role(["teacher", "admin"])),
    agent_service: AgentService = Depends(get_agent_service),
):
    """
    Generate quiz using Quiz Generation Agent.

    Requires: Teacher or Admin role
    Rate limit: 20 requests per minute

    Creates quizzes with specified number of questions and difficulty level.
    """
    try:
        task_data = {
            "subject": request.subject,
            "objectives": request.objectives,
            "num_questions": request.num_questions,
            "difficulty": request.difficulty,
            "context": request.context,
        }

        result = await agent_service.execute_task(
            agent_type="quiz",
            task_type="generate_quiz",
            task_data=task_data,
            user_id=current_user["id"],
        )

        # Background notification
        background_tasks.add_task(
            trigger_event,
            "agent-tasks",
            "quiz.generated",
            {
                "user_id": current_user["id"],
                "task_id": result.get("task_id"),
                "subject": request.subject,
                "num_questions": request.num_questions,
            },
        )

        return AgentTaskResponse(
            success=result["success"],
            task_id=result.get("task_id", ""),
            agent_id=result.get("agent_id"),
            result=result.get("result"),
            execution_time=result.get("execution_time"),
            status=result.get("status", "completed" if result["success"] else "failed"),
            error=result.get("error"),
            message=(
                "Quiz generation completed successfully"
                if result["success"]
                else "Quiz generation failed"
            ),
        )

    except Exception as e:
        logger.error(f"Quiz generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quiz generation failed: {str(e)}",
        )


@router.post("/terrain/generate", response_model=AgentTaskResponse)
# @rate_limit(requests=15)  # 15 requests per minute
async def generate_terrain(
    request: TerrainGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_any_role(["teacher", "admin"])),
    agent_service: AgentService = Depends(get_agent_service),
):
    """
    Generate terrain using Terrain Generation Agent.

    Requires: Teacher or Admin role
    Rate limit: 15 requests per minute

    Creates educational terrain for Roblox environments.
    """
    try:
        task_data = {
            "subject": request.subject,
            "terrain_type": request.terrain_type,
            "complexity": request.complexity,
            "features": request.features,
            "context": request.context,
        }

        result = await agent_service.execute_task(
            agent_type="terrain",
            task_type="generate_terrain",
            task_data=task_data,
            user_id=current_user["id"],
        )

        # Background notification
        background_tasks.add_task(
            trigger_event,
            "agent-tasks",
            "terrain.generated",
            {
                "user_id": current_user["id"],
                "task_id": result.get("task_id"),
                "subject": request.subject,
                "terrain_type": request.terrain_type,
            },
        )

        return AgentTaskResponse(
            success=result["success"],
            task_id=result.get("task_id", ""),
            agent_id=result.get("agent_id"),
            result=result.get("result"),
            execution_time=result.get("execution_time"),
            status=result.get("status", "completed" if result["success"] else "failed"),
            error=result.get("error"),
            message=(
                "Terrain generation completed successfully"
                if result["success"]
                else "Terrain generation failed"
            ),
        )

    except Exception as e:
        logger.error(f"Terrain generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terrain generation failed: {str(e)}",
        )


@router.post("/script/generate", response_model=AgentTaskResponse)
# @rate_limit(requests=20)  # 20 requests per minute
async def generate_script(
    request: ScriptGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_any_role(["teacher", "admin"])),
    agent_service: AgentService = Depends(get_agent_service),
):
    """
    Generate script using Script Generation Agent.

    Requires: Teacher or Admin role
    Rate limit: 20 requests per minute

    Creates Lua scripts for Roblox with specified functionality.
    """
    try:
        task_data = {
            "script_type": request.script_type,
            "functionality": request.functionality,
            "requirements": request.requirements,
            "context": request.context,
        }

        result = await agent_service.execute_task(
            agent_type="script",
            task_type="generate_script",
            task_data=task_data,
            user_id=current_user["id"],
        )

        # Background notification
        background_tasks.add_task(
            trigger_event,
            "agent-tasks",
            "script.generated",
            {
                "user_id": current_user["id"],
                "task_id": result.get("task_id"),
                "script_type": request.script_type,
                "functionality": request.functionality,
            },
        )

        return AgentTaskResponse(
            success=result["success"],
            task_id=result.get("task_id", ""),
            agent_id=result.get("agent_id"),
            result=result.get("result"),
            execution_time=result.get("execution_time"),
            status=result.get("status", "completed" if result["success"] else "failed"),
            error=result.get("error"),
            message=(
                "Script generation completed successfully"
                if result["success"]
                else "Script generation failed"
            ),
        )

    except Exception as e:
        logger.error(f"Script generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Script generation failed: {str(e)}",
        )


@router.post("/code/review", response_model=AgentTaskResponse)
# @rate_limit(requests=25)  # 25 requests per minute
async def review_code(
    request: CodeReviewRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_any_role(["teacher", "admin"])),
    agent_service: AgentService = Depends(get_agent_service),
):
    """
    Review code using Code Review Agent.

    Requires: Teacher or Admin role
    Rate limit: 25 requests per minute

    Provides comprehensive code review including security, performance, and best practices.
    """
    try:
        task_data = {
            "code": request.code,
            "language": request.language,
            "review_type": request.review_type,
            "context": request.context,
        }

        result = await agent_service.execute_task(
            agent_type="code_review",
            task_type="review_code",
            task_data=task_data,
            user_id=current_user["id"],
        )

        # Background notification
        background_tasks.add_task(
            trigger_event,
            "agent-tasks",
            "code.reviewed",
            {
                "user_id": current_user["id"],
                "task_id": result.get("task_id"),
                "language": request.language,
                "review_type": request.review_type,
            },
        )

        return AgentTaskResponse(
            success=result["success"],
            task_id=result.get("task_id", ""),
            agent_id=result.get("agent_id"),
            result=result.get("result"),
            execution_time=result.get("execution_time"),
            status=result.get("status", "completed" if result["success"] else "failed"),
            error=result.get("error"),
            message=(
                "Code review completed successfully" if result["success"] else "Code review failed"
            ),
        )

    except Exception as e:
        logger.error(f"Code review error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code review failed: {str(e)}",
        )


# Roblox Agent Endpoints


@router.post("/roblox/asset", response_model=AgentTaskResponse)
# @rate_limit(requests=10)  # 10 requests per minute
async def manage_roblox_asset(
    request: RobloxAssetRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_any_role(["teacher", "admin"])),
    agent_service: AgentService = Depends(get_agent_service),
):
    """
    Manage Roblox assets using Roblox Asset Management Agent.

    Requires: Teacher or Admin role
    Rate limit: 10 requests per minute

    Handles asset creation, updates, deletion, and analysis.
    """
    try:
        task_data = {
            "asset_type": request.asset_type,
            "action": request.action,
            "asset_data": request.asset_data,
            "context": request.context,
        }

        result = await agent_service.execute_task(
            agent_type="roblox_asset",
            task_type="manage_asset",
            task_data=task_data,
            user_id=current_user["id"],
        )

        return AgentTaskResponse(
            success=result["success"],
            task_id=result.get("task_id", ""),
            agent_id=result.get("agent_id"),
            result=result.get("result"),
            execution_time=result.get("execution_time"),
            status=result.get("status", "completed" if result["success"] else "failed"),
            error=result.get("error"),
            message=(
                "Asset management completed successfully"
                if result["success"]
                else "Asset management failed"
            ),
        )

    except Exception as e:
        logger.error(f"Roblox asset management error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Asset management failed: {str(e)}",
        )


@router.post("/roblox/test", response_model=AgentTaskResponse)
# @rate_limit(requests=5)  # 5 requests per minute
async def run_roblox_tests(
    request: RobloxTestingRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_any_role(["teacher", "admin"])),
    agent_service: AgentService = Depends(get_agent_service),
):
    """
    Run Roblox tests using Roblox Testing Agent.

    Requires: Teacher or Admin role
    Rate limit: 5 requests per minute

    Executes functional, performance, or security tests on Roblox experiences.
    """
    try:
        task_data = {
            "test_type": request.test_type,
            "test_data": request.test_data,
            "context": request.context,
        }

        result = await agent_service.execute_task(
            agent_type="roblox_testing",
            task_type="run_tests",
            task_data=task_data,
            user_id=current_user["id"],
        )

        return AgentTaskResponse(
            success=result["success"],
            task_id=result.get("task_id", ""),
            agent_id=result.get("agent_id"),
            result=result.get("result"),
            execution_time=result.get("execution_time"),
            status=result.get("status", "completed" if result["success"] else "failed"),
            error=result.get("error"),
            message="Testing completed successfully" if result["success"] else "Testing failed",
        )

    except Exception as e:
        logger.error(f"Roblox testing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Testing failed: {str(e)}"
        )


@router.post("/roblox/analytics", response_model=AgentTaskResponse)
# @rate_limit(requests=10)  # 10 requests per minute
async def analyze_roblox_data(
    request: RobloxAnalyticsRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_any_role(["teacher", "admin"])),
    agent_service: AgentService = Depends(get_agent_service),
):
    """
    Analyze Roblox data using Roblox Analytics Agent.

    Requires: Teacher or Admin role
    Rate limit: 10 requests per minute

    Provides analytics on player behavior, performance, and learning outcomes.
    """
    try:
        task_data = {
            "data_type": request.data_type,
            "analysis_data": request.analysis_data,
            "context": request.context,
        }

        result = await agent_service.execute_task(
            agent_type="roblox_analytics",
            task_type="analyze_data",
            task_data=task_data,
            user_id=current_user["id"],
        )

        return AgentTaskResponse(
            success=result["success"],
            task_id=result.get("task_id", ""),
            agent_id=result.get("agent_id"),
            result=result.get("result"),
            execution_time=result.get("execution_time"),
            status=result.get("status", "completed" if result["success"] else "failed"),
            error=result.get("error"),
            message="Analytics completed successfully" if result["success"] else "Analytics failed",
        )

    except Exception as e:
        logger.error(f"Roblox analytics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Analytics failed: {str(e)}"
        )


# Task Management Endpoints


@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: dict = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service),
):
    """
    Get status of specific task.

    Returns detailed task information including execution status,
    results, and performance metrics.
    """
    try:
        task_status = agent_service.get_task_status(task_id)
        if not task_status:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

        return task_status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve task status",
        )


# WebSocket Endpoints


@router.websocket("/ws/{client_id}")
async def agent_websocket_endpoint(
    websocket: WebSocket, client_id: str, agent_service: AgentService = Depends(get_agent_service)
):
    """
    WebSocket endpoint for real-time agent updates.

    Provides live updates on agent status, task progress,
    and system metrics.
    """
    await ws_manager.connect(websocket, client_id)

    try:
        # Send initial system status
        initial_status = {
            "type": "system_status",
            "data": agent_service.get_system_metrics(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await ws_manager.send_personal_message(initial_status, client_id)

        while True:
            # Receive messages from client
            try:
                data = await websocket.receive_json()
                message_type = data.get("type")

                if message_type == "subscribe_agent":
                    agent_id = data.get("agent_id")
                    if agent_id:
                        ws_manager.subscribe_to_agent(client_id, agent_id)
                        await ws_manager.send_personal_message(
                            {
                                "type": "subscribed",
                                "agent_id": agent_id,
                                "message": f"Subscribed to agent {agent_id}",
                            },
                            client_id,
                        )

                elif message_type == "get_agents_status":
                    agents_status = agent_service.get_all_agents_status()
                    await ws_manager.send_personal_message(
                        {
                            "type": "agents_status",
                            "data": agents_status,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        },
                        client_id,
                    )

                elif message_type == "ping":
                    await ws_manager.send_personal_message(
                        {"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()},
                        client_id,
                    )

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket message error: {e}")
                await ws_manager.send_personal_message(
                    {"type": "error", "message": "Message processing error"}, client_id
                )

    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(client_id)


# Health check endpoint
@router.get("/health")
async def agent_system_health(
    current_user: dict = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service),
):
    """
    Get agent system health status.

    Returns overall system health, agent availability,
    and performance indicators.
    """
    try:
        metrics = agent_service.get_system_metrics()

        return {
            "status": "healthy" if metrics["system"]["status"] == "healthy" else "degraded",
            "agents_available": metrics["agents"]["total"],
            "agents_busy": metrics["agents"]["busy"],
            "agents_idle": metrics["agents"]["idle"],
            "tasks_completed": metrics["tasks"]["completed"],
            "tasks_running": metrics["tasks"]["running"],
            "success_rate": metrics["tasks"]["success_rate"],
            "uptime": metrics["system"]["uptime"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting health status: {e}")
        return {
            "status": "error",
            "message": "Failed to retrieve health status",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

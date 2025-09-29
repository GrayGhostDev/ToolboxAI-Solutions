"""
Master Orchestrator API Endpoints

Provides REST API access to the Master Orchestrator and agent management system,
enabling task submission, status monitoring, and agent coordination.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import logging

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from uuid import uuid4

from core.agents.master_orchestrator import (
    MasterOrchestrator,
    OrchestratorConfig,
    AgentSystemType,
    TaskPriority,
    TaskStatus,
)
from core.agents.agent_registry import AgentRegistry, AgentFactory
from core.agents.worktree_coordinator import (
    WorktreeAgentCoordinator,
    WorktreeTaskType,
    TaskDistributionStrategy as DistributionStrategy,
)
from core.agents.github_agents.resource_monitor_agent import ResourceMonitorAgent

logger = logging.getLogger(__name__)

# Router setup
router = APIRouter(tags=["Agent Orchestrator"])

# Global instances (initialized on startup)
_orchestrator: Optional[MasterOrchestrator] = None
_registry: Optional[AgentRegistry] = None
_factory: Optional[AgentFactory] = None
_worktree_coordinator: Optional[WorktreeAgentCoordinator] = None
_resource_monitor: Optional[ResourceMonitorAgent] = None


# =================== Pydantic Models ===================


class TaskSubmission(BaseModel):
    """Request model for task submission."""

    agent_type: AgentSystemType
    task_data: Dict[str, Any]
    priority: TaskPriority = TaskPriority.MEDIUM
    metadata: Optional[Dict[str, Any]] = None


class TaskResponse(BaseModel):
    """Response model for task operations."""

    task_id: str
    status: TaskStatus
    agent_type: str
    created_at: datetime
    message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class AgentInfo(BaseModel):
    """Information about a registered agent."""

    name: str
    category: str
    description: str
    capabilities: List[str]
    status: str
    metrics: Optional[Dict[str, Any]] = None


class SystemStatus(BaseModel):
    """Overall system status."""

    orchestrator: Dict[str, Any]
    agents: Dict[str, int]
    tasks: Dict[str, int]
    resources: Dict[str, Any]
    worktrees: Optional[Dict[str, Any]] = None


class WorktreeTask(BaseModel):
    """Request model for worktree task distribution."""

    task_type: WorktreeTaskType
    description: str
    requirements: List[str] = Field(default_factory=list)
    files: List[str] = Field(default_factory=list)
    strategy: DistributionStrategy = DistributionStrategy.CAPABILITY_BASED


# =================== Initialization ===================


async def get_orchestrator() -> MasterOrchestrator:
    """Get or create the orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        config = OrchestratorConfig(
            max_agents_per_type=5,
            enable_health_checks=True,
            health_check_interval=30,
            enable_metrics=True,
        )
        _orchestrator = MasterOrchestrator(config)
        await _orchestrator.start()
        logger.info("Master Orchestrator initialized")
    return _orchestrator


async def get_registry() -> AgentRegistry:
    """Get or create the agent registry."""
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
        # Registry auto-discovers agents on init
        logger.info(f"Agent Registry initialized with {len(_registry.registered_agents)} agents")
    return _registry


async def get_factory() -> AgentFactory:
    """Get or create the agent factory."""
    global _factory
    if _factory is None:
        registry = await get_registry()
        _factory = AgentFactory(registry)
        logger.info("Agent Factory initialized")
    return _factory


async def get_worktree_coordinator() -> WorktreeAgentCoordinator:
    """Get or create the worktree coordinator."""
    global _worktree_coordinator
    if _worktree_coordinator is None:
        orchestrator = await get_orchestrator()
        _worktree_coordinator = WorktreeAgentCoordinator(orchestrator)
        logger.info("Worktree Coordinator initialized")
    return _worktree_coordinator


async def get_resource_monitor() -> ResourceMonitorAgent:
    """Get or create the resource monitor."""
    global _resource_monitor
    if _resource_monitor is None:
        from core.agents.base_agent import AgentConfig

        config = AgentConfig(name="ResourceMonitor")
        _resource_monitor = ResourceMonitorAgent(config)
        logger.info("Resource Monitor initialized")
    return _resource_monitor


# =================== API Endpoints ===================


@router.post("/submit", response_model=TaskResponse)
async def submit_task(
    submission: TaskSubmission,
    background_tasks: BackgroundTasks,
    orchestrator: MasterOrchestrator = Depends(get_orchestrator),
) -> TaskResponse:
    """
    Submit a task to the orchestrator for processing.

    The task will be queued and processed by the appropriate agent(s).
    """
    try:
        task_id = await orchestrator.submit_task(
            agent_type=submission.agent_type,
            task_data=submission.task_data,
            priority=submission.priority,
        )

        # Get task status
        status = await orchestrator.get_task_status(task_id)

        return TaskResponse(
            task_id=task_id,
            status=status.get("status", TaskStatus.PENDING),
            agent_type=submission.agent_type.value,
            created_at=datetime.now(),
            message=f"Task {task_id} submitted successfully",
        )

    except Exception as e:
        logger.error(f"Failed to submit task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{task_id}", response_model=TaskResponse)
async def get_task_status(
    task_id: str, orchestrator: MasterOrchestrator = Depends(get_orchestrator)
) -> TaskResponse:
    """
    Get the status of a submitted task.
    """
    try:
        status = await orchestrator.get_task_status(task_id)

        if not status:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        return TaskResponse(
            task_id=task_id,
            status=status.get("status", TaskStatus.UNKNOWN),
            agent_type=status.get("agent_type", "unknown"),
            created_at=status.get("created_at", datetime.now()),
            message=status.get("message"),
            result=status.get("result"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents", response_model=List[AgentInfo])
async def list_agents(
    category: Optional[str] = None, registry: AgentRegistry = Depends(get_registry)
) -> List[AgentInfo]:
    """
    List all registered agents, optionally filtered by category.
    """
    try:
        agents = []

        for name, metadata in registry.registered_agents.items():
            if category and metadata.category.value != category:
                continue

            agents.append(
                AgentInfo(
                    name=name,
                    category=metadata.category.value,
                    description=metadata.description,
                    capabilities=[cap.value for cap in metadata.capabilities],
                    status="available",  # All registered agents are considered available
                    metrics={},  # No per-agent metrics in metadata
                )
            )

        return agents

    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/status", response_model=SystemStatus)
async def get_system_status(
    orchestrator: MasterOrchestrator = Depends(get_orchestrator),
    registry: AgentRegistry = Depends(get_registry),
    resource_monitor: ResourceMonitorAgent = Depends(get_resource_monitor),
) -> SystemStatus:
    """
    Get comprehensive system status including orchestrator, agents, and resources.
    """
    try:
        # Get orchestrator statistics
        orch_stats = await orchestrator.get_statistics()

        # Get agent counts by category
        agent_counts = {}
        for metadata in registry.registered_agents.values():
            category = metadata.category.value
            agent_counts[category] = agent_counts.get(category, 0) + 1

        # Get task statistics
        task_stats = {
            "pending": orch_stats.get("queued_tasks", 0),
            "active": orch_stats.get("active_tasks", 0),
            "completed": orch_stats.get("completed_tasks", 0),
            "failed": orch_stats.get("failed_tasks", 0),
        }

        # Get resource snapshot
        resource_result = await resource_monitor.monitor_resources()
        resources = resource_result.output if resource_result.success else {}

        return SystemStatus(
            orchestrator={
                "is_running": orchestrator.is_running,
                "uptime": orch_stats.get("uptime", 0),
                "total_processed": orch_stats.get("total_tasks_processed", 0),
            },
            agents=agent_counts,
            tasks=task_stats,
            resources=resources.get("snapshot", {}),
        )

    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/worktree/distribute", response_model=TaskResponse)
async def distribute_worktree_task(
    task: WorktreeTask, coordinator: WorktreeAgentCoordinator = Depends(get_worktree_coordinator)
) -> TaskResponse:
    """
    Distribute a task across available worktrees.
    """
    try:
        task_id = await coordinator.distribute_task(
            task_type=task.task_type,
            description=task.description,
            requirements=task.requirements,
            files=task.files,
            strategy=task.strategy,
        )

        return TaskResponse(
            task_id=task_id,
            status=TaskStatus.DISTRIBUTED,
            agent_type="worktree",
            created_at=datetime.now(),
            message=f"Task distributed to worktrees using {task.strategy.value} strategy",
        )

    except Exception as e:
        logger.error(f"Failed to distribute worktree task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/worktree/sessions")
async def get_worktree_sessions(
    coordinator: WorktreeAgentCoordinator = Depends(get_worktree_coordinator),
) -> Dict[str, Any]:
    """
    Get information about active worktree sessions.
    """
    try:
        return coordinator.get_active_worktrees()

    except Exception as e:
        logger.error(f"Failed to get worktree sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resources/monitor")
async def monitor_resources(
    monitor: ResourceMonitorAgent = Depends(get_resource_monitor),
) -> Dict[str, Any]:
    """
    Get current resource utilization snapshot.
    """
    try:
        result = await monitor.monitor_resources()

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)

        return result.output

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to monitor resources: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resources/alerts")
async def get_resource_alerts(
    monitor: ResourceMonitorAgent = Depends(get_resource_monitor),
) -> Dict[str, Any]:
    """
    Get active resource alerts.
    """
    try:
        result = await monitor.get_active_alerts()

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)

        return result.output

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get resource alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resources/optimize")
async def optimize_resources(
    monitor: ResourceMonitorAgent = Depends(get_resource_monitor),
) -> Dict[str, Any]:
    """
    Apply resource optimization recommendations.
    """
    try:
        result = await monitor.apply_optimizations()

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)

        return result.output

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to optimize resources: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/shutdown")
async def shutdown_orchestrator(
    orchestrator: MasterOrchestrator = Depends(get_orchestrator),
) -> Dict[str, str]:
    """
    Gracefully shutdown the orchestrator.
    """
    try:
        await orchestrator.stop()

        # Clear global instances
        global _orchestrator, _registry, _factory, _worktree_coordinator, _resource_monitor
        _orchestrator = None
        _registry = None
        _factory = None
        _worktree_coordinator = None
        _resource_monitor = None

        return {"message": "Orchestrator shutdown successfully"}

    except Exception as e:
        logger.error(f"Failed to shutdown orchestrator: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =================== WebSocket Endpoint (Optional) ===================


@router.websocket("/ws")
async def websocket_endpoint(websocket):
    """
    WebSocket endpoint for real-time task updates.
    """
    await websocket.accept()
    orchestrator = await get_orchestrator()

    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_json()

            if data.get("type") == "subscribe":
                task_id = data.get("task_id")

                # Send periodic updates
                while True:
                    status = await orchestrator.get_task_status(task_id)
                    if status:
                        await websocket.send_json(
                            {"type": "status_update", "task_id": task_id, "status": status}
                        )

                        if status.get("status") in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                            break

                    await asyncio.sleep(1)

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()

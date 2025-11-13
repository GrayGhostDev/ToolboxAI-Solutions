"""
Database Agent Swarm API Endpoints

This module provides FastAPI endpoints for interacting with the database
agent swarm, including workflow execution, monitoring, and management.

Author: ToolboxAI Team
Created: 2025-09-16
Version: 1.0.0
"""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.api.auth.auth import get_current_user
from apps.backend.core.config import settings
from apps.backend.core.deps import get_async_db
from apps.backend.models.schemas import User
from core.agents.database import (
    DatabaseOperation,
    DatabaseSupervisorAgent,
    DatabaseWorkflow,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/database", tags=["database-swarm"])

# Global instance of workflow (initialized on first use)
_workflow_instance: DatabaseWorkflow | None = None
_supervisor_instance: DatabaseSupervisorAgent | None = None


# Pydantic models for API requests/responses


class DatabaseWorkflowRequest(BaseModel):
    """Request model for database workflow execution."""

    operation: str = Field(..., description="Natural language or structured database operation")
    priority: str = Field(
        default="medium", description="Priority level: critical, high, medium, low, background"
    )
    params: dict[str, Any] = Field(default_factory=dict, description="Additional parameters")
    thread_id: str | None = Field(default=None, description="Thread ID for stateful execution")


class DatabaseCommandRequest(BaseModel):
    """Request model for specific database commands."""

    command_type: DatabaseOperation = Field(..., description="Type of database operation")
    aggregate_type: str = Field(..., description="Type of aggregate/entity")
    aggregate_id: UUID | None = Field(None, description="ID of the aggregate")
    data: dict[str, Any] = Field(..., description="Command data")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class EventRequest(BaseModel):
    """Request model for appending events."""

    event_type: str = Field(..., description="Type of event")
    aggregate_type: str = Field(..., description="Type of aggregate")
    aggregate_id: UUID = Field(..., description="Aggregate ID")
    event_data: dict[str, Any] = Field(..., description="Event data")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Event metadata")


class QueryRequest(BaseModel):
    """Request model for database queries."""

    query: str = Field(..., description="SQL query or natural language query")
    params: dict[str, Any] = Field(default_factory=dict, description="Query parameters")
    optimize: bool = Field(default=True, description="Whether to optimize the query")


class BackupRequest(BaseModel):
    """Request model for backup operations."""

    backup_type: str = Field(
        default="full", description="Type of backup: full, incremental, differential"
    )
    targets: list[str] = Field(
        default_factory=list, description="Specific tables/schemas to backup"
    )
    compression: bool = Field(default=True, description="Whether to compress the backup")
    encryption: bool = Field(default=True, description="Whether to encrypt the backup")


class MigrationRequest(BaseModel):
    """Request model for schema migrations."""

    migration_name: str = Field(..., description="Name of the migration")
    direction: str = Field(default="up", description="Migration direction: up or down")
    target_version: int | None = Field(None, description="Target schema version")
    dry_run: bool = Field(default=False, description="Whether to perform a dry run")


class MonitoringRequest(BaseModel):
    """Request model for monitoring queries."""

    metric_type: str = Field(..., description="Type of metric to retrieve")
    time_range: str = Field(default="1h", description="Time range for metrics")
    aggregation: str = Field(default="avg", description="Aggregation method")


class WorkflowResponse(BaseModel):
    """Response model for workflow execution."""

    success: bool
    workflow_id: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    execution_time: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentStatusResponse(BaseModel):
    """Response model for agent status."""

    supervisor: dict[str, Any]
    agents: dict[str, dict[str, Any]]
    overall_health: str
    active_workflows: int
    timestamp: datetime


class EventResponse(BaseModel):
    """Response model for event operations."""

    event_id: UUID
    event_version: int
    aggregate_id: UUID
    created_at: datetime


# Helper functions


async def get_workflow_instance() -> DatabaseWorkflow:
    """Get or create workflow instance."""
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = DatabaseWorkflow(
            database_url=settings.DATABASE_URL, redis_url=settings.REDIS_URL
        )
        await _workflow_instance.initialize()
    return _workflow_instance


async def get_supervisor_instance() -> DatabaseSupervisorAgent:
    """Get or create supervisor instance."""
    global _supervisor_instance
    if _supervisor_instance is None:
        from core.agents.database import DatabaseAgentConfig

        config = DatabaseAgentConfig(
            database_url=settings.DATABASE_URL, redis_url=settings.REDIS_URL
        )
        _supervisor_instance = DatabaseSupervisorAgent(config)
        await _supervisor_instance.initialize()
    return _supervisor_instance


# API Endpoints


@router.post("/workflow/execute", response_model=WorkflowResponse)
async def execute_workflow(
    request: DatabaseWorkflowRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """
    Execute a database workflow using natural language or structured commands.

    This endpoint supports:
    - Natural language queries ("optimize slow queries in the users table")
    - Structured operations (migration, backup, sync, etc.)
    - Stateful execution with thread IDs
    - Priority-based scheduling
    """
    try:
        workflow = await get_workflow_instance()

        # Generate thread ID if not provided
        thread_id = request.thread_id or f"user_{current_user.id}_{datetime.utcnow().timestamp()}"

        # Execute workflow
        start_time = datetime.utcnow()
        result = await workflow.execute(request=request.operation, thread_id=thread_id)
        execution_time = (datetime.utcnow() - start_time).total_seconds()

        return WorkflowResponse(
            success=result.get("success", False),
            workflow_id=thread_id,
            result=result,
            execution_time=execution_time,
            metadata={
                "user_id": str(current_user.id),
                "priority": request.priority,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflow/state/{thread_id}")
async def get_workflow_state(thread_id: str, current_user: User = Depends(get_current_user)):
    """Get the current state of a workflow execution."""
    try:
        workflow = await get_workflow_instance()
        state = await workflow.get_state(thread_id)

        if state is None:
            raise HTTPException(status_code=404, detail="Workflow not found")

        return {"thread_id": thread_id, "state": state, "timestamp": datetime.utcnow().isoformat()}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/status", response_model=AgentStatusResponse)
async def get_agents_status(current_user: User = Depends(get_current_user)):
    """Get the status of all database agents."""
    try:
        supervisor = await get_supervisor_instance()
        status = await supervisor.get_agent_status()

        # Determine overall health
        agent_healths = [agent["health"] for agent in status["agents"].values()]
        if any(h == "critical" for h in agent_healths):
            overall_health = "critical"
        elif any(h == "degraded" for h in agent_healths):
            overall_health = "degraded"
        else:
            overall_health = "healthy"

        return AgentStatusResponse(
            supervisor=status["supervisor"],
            agents=status["agents"],
            overall_health=overall_health,
            active_workflows=status["supervisor"]["active_workflows"],
            timestamp=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"Failed to get agent status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events/append", response_model=EventResponse)
async def append_event(
    request: EventRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Append an event to the event store."""
    try:
        supervisor = await get_supervisor_instance()
        event_agent = supervisor.agents.get("event")

        if not event_agent:
            raise HTTPException(status_code=503, detail="Event sourcing agent not available")

        # Prepare event data
        event_data = {
            "event_type": request.event_type,
            "aggregate_type": request.aggregate_type,
            "aggregate_id": str(request.aggregate_id),
            "event_data": request.event_data,
            "metadata": {
                **request.metadata,
                "user_id": str(current_user.id),
                "timestamp": datetime.utcnow().isoformat(),
            },
        }

        # Append event
        from core.agents.base_agent import AgentState

        state = AgentState(
            {"task": "append_event", "operation": DatabaseOperation.QUERY, "params": event_data}
        )

        result = await event_agent.process(state)

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)

        return EventResponse(
            event_id=result.data["event_id"],
            event_version=result.data["event_version"],
            aggregate_id=request.aggregate_id,
            created_at=datetime.utcnow(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to append event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/replay/{aggregate_id}")
async def replay_events(
    aggregate_id: UUID,
    from_version: int = Query(0, ge=0),
    to_version: int | None = Query(None, ge=0),
    current_user: User = Depends(get_current_user),
):
    """Replay events for an aggregate."""
    try:
        supervisor = await get_supervisor_instance()
        event_agent = supervisor.agents.get("event")

        if not event_agent:
            raise HTTPException(status_code=503, detail="Event sourcing agent not available")

        # Replay events
        from core.agents.base_agent import AgentState

        state = AgentState(
            {
                "task": "replay_events",
                "operation": DatabaseOperation.QUERY,
                "params": {
                    "aggregate_id": str(aggregate_id),
                    "from_version": from_version,
                    "to_version": to_version,
                },
            }
        )

        result = await event_agent.process(state)

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)

        return {
            "aggregate_id": str(aggregate_id),
            "events": result.data["events"],
            "count": len(result.data["events"]),
            "from_version": from_version,
            "to_version": to_version or result.data.get("latest_version"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to replay events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/optimize")
async def optimize_query(request: QueryRequest, current_user: User = Depends(get_current_user)):
    """Optimize a database query."""
    try:
        supervisor = await get_supervisor_instance()
        query_agent = supervisor.agents.get("query")

        if not query_agent:
            raise HTTPException(status_code=503, detail="Query optimization agent not available")

        # Optimize query
        from core.agents.base_agent import AgentState

        state = AgentState(
            {
                "task": "optimize_query",
                "operation": DatabaseOperation.OPTIMIZE,
                "params": {
                    "query": request.query,
                    "params": request.params,
                    "auto_optimize": request.optimize,
                },
            }
        )

        result = await query_agent.process(state)

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)

        return {
            "original_query": request.query,
            "optimized_query": result.data.get("optimized_query"),
            "improvements": result.data.get("improvements", []),
            "estimated_improvement": result.data.get("estimated_improvement"),
            "execution_plan": result.data.get("execution_plan"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to optimize query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backup/create")
async def create_backup(
    request: BackupRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """Create a database backup."""
    try:
        supervisor = await get_supervisor_instance()
        backup_agent = supervisor.agents.get("backup")

        if not backup_agent:
            raise HTTPException(status_code=503, detail="Backup agent not available")

        # Create backup
        from core.agents.base_agent import AgentState

        state = AgentState(
            {
                "task": "create_backup",
                "operation": DatabaseOperation.BACKUP,
                "params": {
                    "backup_type": request.backup_type,
                    "targets": request.targets,
                    "compression": request.compression,
                    "encryption": request.encryption,
                    "user_id": str(current_user.id),
                },
            }
        )

        # Execute in background
        async def run_backup():
            return await backup_agent.process(state)

        background_tasks.add_task(run_backup)

        return {
            "message": "Backup initiated",
            "backup_type": request.backup_type,
            "status": "processing",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/migration/execute")
async def execute_migration(
    request: MigrationRequest, current_user: User = Depends(get_current_user)
):
    """Execute a database migration."""
    try:
        supervisor = await get_supervisor_instance()
        schema_agent = supervisor.agents.get("schema")

        if not schema_agent:
            raise HTTPException(status_code=503, detail="Schema management agent not available")

        # Execute migration
        from core.agents.base_agent import AgentState

        state = AgentState(
            {
                "task": "execute_migration",
                "operation": DatabaseOperation.MIGRATION,
                "params": {
                    "migration_name": request.migration_name,
                    "direction": request.direction,
                    "target_version": request.target_version,
                    "dry_run": request.dry_run,
                },
            }
        )

        result = await schema_agent.process(state)

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)

        return {
            "migration_name": request.migration_name,
            "direction": request.direction,
            "success": result.success,
            "changes": result.data.get("changes", []),
            "new_version": result.data.get("new_version"),
            "dry_run": request.dry_run,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute migration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/metrics")
async def get_monitoring_metrics(
    metric_type: str = Query(..., description="Type of metric"),
    time_range: str = Query("1h", description="Time range"),
    current_user: User = Depends(get_current_user),
):
    """Get database monitoring metrics."""
    try:
        supervisor = await get_supervisor_instance()
        monitor_agent = supervisor.agents.get("monitor")

        if not monitor_agent:
            raise HTTPException(status_code=503, detail="Monitoring agent not available")

        # Get metrics
        from core.agents.base_agent import AgentState

        state = AgentState(
            {
                "task": "get_metrics",
                "operation": DatabaseOperation.MONITOR,
                "params": {"metric_type": metric_type, "time_range": time_range},
            }
        )

        result = await monitor_agent.process(state)

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)

        return {
            "metric_type": metric_type,
            "time_range": time_range,
            "metrics": result.data.get("metrics", {}),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/invalidate")
async def invalidate_cache(
    pattern: str = Query(..., description="Cache key pattern to invalidate"),
    current_user: User = Depends(get_current_user),
):
    """Invalidate cache entries matching a pattern."""
    try:
        supervisor = await get_supervisor_instance()
        cache_agent = supervisor.agents.get("cache")

        if not cache_agent:
            raise HTTPException(status_code=503, detail="Cache management agent not available")

        # Invalidate cache
        from core.agents.base_agent import AgentState

        state = AgentState(
            {
                "task": "invalidate_cache",
                "operation": DatabaseOperation.CACHE,
                "params": {"pattern": pattern},
            }
        )

        result = await cache_agent.process(state)

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)

        return {
            "pattern": pattern,
            "invalidated_count": result.data.get("invalidated_count", 0),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to invalidate cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Check the health of the database agent swarm."""
    try:
        supervisor = await get_supervisor_instance()
        health = await supervisor.check_health()

        return {"status": health.value, "timestamp": datetime.utcnow().isoformat()}

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "critical", "error": str(e), "timestamp": datetime.utcnow().isoformat()}

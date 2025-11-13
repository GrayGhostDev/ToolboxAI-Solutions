"""
Integration API Endpoints - HTTP Interface for Agent Swarm

This module provides REST API endpoints for interacting with the integration
agent swarm, including workflow management, schema registration, and health monitoring.
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from apps.backend.api.auth.auth import get_current_user
from apps.backend.models.schemas import User
from apps.backend.services.integration_agents import (
    execute_integration_workflow,
    get_integration_manager,
)
from core.agents.integration import IntegrationPlatform

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integration", tags=["integration"])


# Request/Response Models
class AgentStatusResponse(BaseModel):
    """Response model for agent status"""

    initialized: bool
    timestamp: str
    agents: dict[str, dict[str, Any]]
    overall_health: str = Field(description="Overall health: healthy, degraded, unhealthy")


class WorkflowCreateRequest(BaseModel):
    """Request model for creating a workflow"""

    name: str = Field(..., description="Workflow name")
    description: str = Field(..., description="Workflow description")
    template: str | None = Field(None, description="Template name to use")
    custom_tasks: list[dict[str, Any]] | None = Field(None, description="Custom task definitions")
    parameters: dict[str, Any] | None = Field(
        default_factory=dict, description="Workflow parameters"
    )


class WorkflowExecuteRequest(BaseModel):
    """Request model for executing a workflow"""

    parameters: dict[str, Any] | None = Field(
        default_factory=dict, description="Execution parameters"
    )
    async_execution: bool = Field(False, description="Execute asynchronously")


class WorkflowResponse(BaseModel):
    """Response model for workflow operations"""

    workflow_id: str | None
    success: bool
    output: dict[str, Any] | None
    error: str | None
    execution_time: float | None


class SchemaRegistrationRequest(BaseModel):
    """Request model for schema registration"""

    schema_name: str = Field(..., description="Schema name")
    schema_type: str = Field("json_schema", description="Schema type (json_schema, protobuf, avro)")
    definition: dict[str, Any] = Field(..., description="Schema definition")
    platform: str = Field(..., description="Platform (backend, frontend, roblox)")
    version: str = Field("1.0.0", description="Schema version")


class DataSyncRequest(BaseModel):
    """Request model for data synchronization"""

    source_platform: str = Field(..., description="Source platform")
    target_platform: str = Field(..., description="Target platform")
    data: dict[str, Any] = Field(..., description="Data to synchronize")
    sync_mode: str = Field("immediate", description="Sync mode: immediate, batch, scheduled")


class EventBroadcastRequest(BaseModel):
    """Request model for broadcasting events"""

    channel: str = Field(..., description="Channel name")
    event: str = Field(..., description="Event name")
    data: Any = Field(..., description="Event data")


# Endpoints


@router.get("/status", response_model=AgentStatusResponse)
async def get_integration_status(
    agent_name: str | None = Query(None, description="Specific agent name to check"),
    current_user: User = Depends(get_current_user),
):
    """
    Get the status of integration agents

    Returns health status and metrics for all agents or a specific agent.
    """
    try:
        manager = await get_integration_manager()
        status = await manager.get_agent_status(agent_name)

        # Calculate overall health
        overall_health = "healthy"
        if status.get("agents"):
            unhealthy_count = sum(
                1 for agent in status["agents"].values() if agent.get("status") != "healthy"
            )
            if unhealthy_count > 0:
                overall_health = (
                    "degraded" if unhealthy_count < len(status["agents"]) / 2 else "unhealthy"
                )

        return AgentStatusResponse(
            initialized=status["initialized"],
            timestamp=status["timestamp"],
            agents=status["agents"],
            overall_health=overall_health,
        )

    except Exception as e:
        logger.error(f"Error getting integration status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
async def list_available_agents(current_user: User = Depends(get_current_user)):
    """
    List all available integration agents and their capabilities
    """
    try:
        manager = await get_integration_manager()

        agent_info = {
            "api_gateway": {
                "name": "API Gateway Agent",
                "description": "Manages API endpoints, versioning, and documentation",
                "capabilities": [
                    "endpoint_registration",
                    "api_versioning",
                    "openapi_generation",
                    "rate_limiting",
                ],
            },
            "database_sync": {
                "name": "Database Sync Agent",
                "description": "Synchronizes data between PostgreSQL and Redis",
                "capabilities": ["data_sync", "cache_management", "conflict_resolution"],
            },
            "ui_sync": {
                "name": "UI Sync Agent",
                "description": "Manages real-time UI state synchronization",
                "capabilities": ["state_sync", "component_updates", "optimistic_updates"],
            },
            "realtime_update": {
                "name": "Realtime Update Agent",
                "description": "Handles Pusher channels and WebSocket fallback",
                "capabilities": ["event_broadcast", "channel_management", "message_queue"],
            },
            "studio_bridge": {
                "name": "Studio Bridge Agent",
                "description": "Communicates with Roblox Studio",
                "capabilities": ["script_sync", "studio_commands", "debug_routing"],
            },
            "schema_validator": {
                "name": "Schema Validator Agent",
                "description": "Validates and transforms data across platforms",
                "capabilities": ["schema_validation", "data_transformation", "version_migration"],
            },
        }

        # Check which agents are actually initialized
        status = await manager.get_agent_status()
        for agent_key in agent_info:
            agent_info[agent_key]["initialized"] = agent_key in status.get("agents", {})
            if agent_key in status.get("agents", {}):
                agent_info[agent_key]["health"] = status["agents"][agent_key].get(
                    "status", "unknown"
                )

        return JSONResponse(
            content={"status": "success", "agents": agent_info, "total_agents": len(agent_info)}
        )

    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflow/create", response_model=WorkflowResponse)
async def create_workflow(
    request: WorkflowCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """
    Create and optionally execute an integration workflow

    Workflows coordinate multiple agents to perform complex integration tasks.
    """
    try:
        start_time = datetime.utcnow()

        # Execute workflow
        result = await execute_integration_workflow(
            workflow_name=request.name,
            workflow_description=request.description,
            template=request.template,
            custom_tasks=request.custom_tasks,
            parameters=request.parameters,
        )

        execution_time = (datetime.utcnow() - start_time).total_seconds()

        return WorkflowResponse(
            workflow_id=result.get("workflow_id"),
            success=result["success"],
            output=result.get("output"),
            error=result.get("error"),
            execution_time=execution_time,
        )

    except Exception as e:
        logger.error(f"Error creating workflow: {e}")
        return WorkflowResponse(
            workflow_id=None, success=False, output=None, error=str(e), execution_time=None
        )


@router.post("/workflow/templates")
async def list_workflow_templates(current_user: User = Depends(get_current_user)):
    """
    List available workflow templates
    """
    templates = {
        "content_generation": {
            "name": "Content Generation Workflow",
            "description": "Generate educational content and sync across platforms",
            "tasks": [
                "validate_input",
                "generate_content",
                "store_in_database",
                "update_frontend",
                "sync_to_roblox",
            ],
        },
        "user_sync": {
            "name": "User Synchronization Workflow",
            "description": "Sync user data between backend and frontend",
            "tasks": ["fetch_user_data", "validate_data", "update_database", "broadcast_update"],
        },
        "roblox_deployment": {
            "name": "Roblox Deployment Workflow",
            "description": "Deploy content to Roblox Studio",
            "tasks": [
                "prepare_scripts",
                "validate_scripts",
                "deploy_to_studio",
                "verify_deployment",
            ],
        },
        "api_migration": {
            "name": "API Migration Workflow",
            "description": "Migrate API endpoints to new version",
            "tasks": [
                "analyze_endpoints",
                "create_new_version",
                "migrate_schemas",
                "deprecate_old_endpoints",
            ],
        },
    }

    return JSONResponse(content={"status": "success", "templates": templates})


@router.post("/schema/register")
async def register_schema(
    request: SchemaRegistrationRequest, current_user: User = Depends(get_current_user)
):
    """
    Register a new schema for cross-platform validation
    """
    try:
        manager = await get_integration_manager()

        # Get the schema validator agent
        if "schema_validator" not in manager.agents:
            raise HTTPException(status_code=503, detail="Schema validator agent not available")

        schema_validator = manager.agents["schema_validator"]

        # Import SchemaType enum
        from core.agents.integration.data_flow import SchemaType

        # Map string to enum
        schema_type_map = {
            "json_schema": SchemaType.JSON_SCHEMA,
            "protobuf": SchemaType.PROTOBUF,
            "avro": SchemaType.AVRO,
        }

        schema_type = schema_type_map.get(request.schema_type, SchemaType.JSON_SCHEMA)
        platform = IntegrationPlatform[request.platform.upper()]

        # Register the schema
        result = await schema_validator.register_schema(
            schema_name=request.schema_name,
            schema_type=schema_type,
            definition=request.definition,
            platform=platform,
            version=request.version,
        )

        return JSONResponse(
            content={
                "status": "success",
                "message": f"Schema '{request.schema_name}' registered successfully",
                "result": result,
            }
        )

    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid platform: {request.platform}")
    except Exception as e:
        logger.error(f"Error registering schema: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/trigger")
async def trigger_data_sync(
    request: DataSyncRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """
    Trigger manual data synchronization between platforms
    """
    try:
        manager = await get_integration_manager()

        # Execute sync
        result = await manager.sync_data(
            source_platform=request.source_platform,
            target_platform=request.target_platform,
            data=request.data,
        )

        if request.sync_mode == "batch":
            # For batch mode, queue the sync
            background_tasks.add_task(
                manager.sync_data, request.source_platform, request.target_platform, request.data
            )

            return JSONResponse(
                content={"status": "success", "message": "Sync queued for batch processing"}
            )

        return JSONResponse(
            content={
                "status": "success" if result["success"] else "error",
                "output": result.get("output"),
                "error": result.get("error"),
            }
        )

    except Exception as e:
        logger.error(f"Error triggering sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/event/broadcast")
async def broadcast_event(
    request: EventBroadcastRequest, current_user: User = Depends(get_current_user)
):
    """
    Broadcast an event through the realtime update agent
    """
    try:
        manager = await get_integration_manager()

        result = await manager.broadcast_event(
            channel=request.channel, event=request.event, data=request.data
        )

        return JSONResponse(
            content={
                "status": "success" if result["success"] else "error",
                "message": (
                    "Event broadcast successfully" if result["success"] else result.get("error")
                ),
                "output": result.get("output"),
            }
        )

    except Exception as e:
        logger.error(f"Error broadcasting event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_integration_metrics(
    platform: str | None = Query(None, description="Filter by platform"),
    current_user: User = Depends(get_current_user),
):
    """
    Get detailed metrics for integration operations
    """
    try:
        manager = await get_integration_manager()
        status = await manager.get_agent_status()

        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "agents": {},
            "platforms": {},
            "totals": {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "events_processed": 0,
            },
        }

        # Aggregate metrics from all agents
        for agent_name, agent_status in status.get("agents", {}).items():
            if "metrics" in agent_status:
                agent_metrics = agent_status["metrics"]
                metrics["agents"][agent_name] = agent_metrics

                # Update totals
                metrics["totals"]["total_requests"] += agent_metrics.get("total_requests", 0)
                metrics["totals"]["successful_requests"] += agent_metrics.get(
                    "successful_requests", 0
                )
                metrics["totals"]["failed_requests"] += agent_metrics.get("failed_requests", 0)
                metrics["totals"]["events_processed"] += agent_metrics.get("events_processed", 0)

        # Calculate success rate
        if metrics["totals"]["total_requests"] > 0:
            metrics["totals"]["success_rate"] = (
                metrics["totals"]["successful_requests"] / metrics["totals"]["total_requests"]
            )
        else:
            metrics["totals"]["success_rate"] = 0.0

        # Platform-specific filtering
        if platform:
            try:
                platform_enum = IntegrationPlatform[platform.upper()]
                # Filter metrics for specific platform if needed
                # This would require platform-specific metric tracking in agents
            except KeyError:
                raise HTTPException(status_code=400, detail=f"Invalid platform: {platform}")

        return JSONResponse(content=metrics)

    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/health/check")
async def perform_health_check(
    deep_check: bool = Query(False, description="Perform deep health check"),
    current_user: User = Depends(get_current_user),
):
    """
    Perform a health check on all integration components
    """
    try:
        manager = await get_integration_manager()

        health_report = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "components": {},
        }

        # Check each agent
        status = await manager.get_agent_status()

        for agent_name, agent_health in status.get("agents", {}).items():
            component_health = {
                "status": agent_health.get("status", "unknown"),
                "metrics": agent_health.get("metrics", {}),
            }

            if deep_check:
                # Perform additional checks
                component_health["platforms"] = agent_health.get("platforms", {})
                component_health["circuit_breakers"] = agent_health.get("circuit_breakers", {})

            health_report["components"][agent_name] = component_health

            # Update overall status
            if component_health["status"] != "healthy":
                health_report["status"] = "degraded"

        # Check external services if deep_check
        if deep_check:
            # Check database connectivity
            try:
                from database.connection import DatabaseManager

                db_manager = DatabaseManager()
                await db_manager.initialize()
                health_report["components"]["database"] = {"status": "healthy"}
            except Exception as e:
                health_report["components"]["database"] = {"status": "unhealthy", "error": str(e)}
                health_report["status"] = "degraded"

            # Check Redis connectivity
            try:
                import redis.asyncio as redis

                from apps.backend.core.config import settings

                if hasattr(settings, "REDIS_URL") and settings.REDIS_URL:
                    redis_client = await redis.from_url(settings.REDIS_URL)
                    await redis_client.ping()
                    health_report["components"]["redis"] = {"status": "healthy"}
                else:
                    health_report["components"]["redis"] = {"status": "not_configured"}
            except Exception as e:
                health_report["components"]["redis"] = {"status": "unhealthy", "error": str(e)}
                health_report["status"] = "degraded"

        return JSONResponse(content=health_report)

    except Exception as e:
        logger.error(f"Error performing health check: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error",
                "error": str(e),
            },
        )


@router.post("/maintenance/cleanup")
async def cleanup_integration(
    force: bool = Query(False, description="Force cleanup even if agents are busy"),
    current_user: User = Depends(get_current_user),
):
    """
    Perform cleanup operations on integration agents

    This endpoint should be used for maintenance tasks.
    """
    try:
        # Check if user is admin
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")

        manager = await get_integration_manager()

        cleanup_report = {"timestamp": datetime.utcnow().isoformat(), "cleaned": []}

        # Get current status
        status = await manager.get_agent_status()

        # Check if safe to cleanup
        busy_agents = []
        for agent_name, agent_status in status.get("agents", {}).items():
            metrics = agent_status.get("metrics", {})
            # Check if agent has recent activity
            if metrics.get("events_processed", 0) > 0:
                busy_agents.append(agent_name)

        if busy_agents and not force:
            return JSONResponse(
                status_code=409,
                content={
                    "status": "error",
                    "message": "Some agents are busy processing events",
                    "busy_agents": busy_agents,
                },
            )

        # Perform cleanup on each agent
        for agent_name in manager.agents:
            try:
                agent = manager.agents[agent_name]
                await agent.cleanup()
                cleanup_report["cleaned"].append(agent_name)
            except Exception as e:
                logger.error(f"Error cleaning up agent {agent_name}: {e}")

        return JSONResponse(content={"status": "success", "report": cleanup_report})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

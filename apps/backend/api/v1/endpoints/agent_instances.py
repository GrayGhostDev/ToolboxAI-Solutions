"""
Agent Instance Management Endpoints with Multi-Tenant Organization Filtering

This module provides CRUD endpoints for AgentInstance models with automatic
organization-level isolation. All operations are scoped to the authenticated
user's organization.

Phase 1 Task 1.4: Multi-tenant API endpoint implementation
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.core.deps import (
    get_async_db,
    get_current_active_user,
    get_current_organization_id,
)
from apps.backend.core.logging import logging_manager
from database.models import User
from database.models.agent_models import AgentExecution, AgentInstance, AgentMetrics

# Initialize logger
logger = logging_manager.get_logger(__name__)

# Create router
router = APIRouter(prefix="/instances", tags=["agent-instances"])


# ============================================================================
# Pydantic Schemas
# ============================================================================


class AgentInstanceCreate(BaseModel):
    """Schema for creating a new agent instance"""

    agent_id: str = Field(..., description="Unique identifier for the agent")
    agent_type: str = Field(..., description="Type of agent (CONTENT_GENERATOR, etc.)")
    configuration: dict | None = Field(default_factory=dict, description="Agent configuration")

    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "content-gen-001",
                "agent_type": "CONTENT_GENERATOR",
                "configuration": {"model": "gpt-4", "temperature": 0.7},
            }
        }


class AgentInstanceUpdate(BaseModel):
    """Schema for updating an agent instance"""

    status: str | None = Field(None, description="Agent status")
    configuration: dict | None = Field(None, description="Updated configuration")

    class Config:
        json_schema_extra = {
            "example": {"status": "IDLE", "configuration": {"model": "gpt-4", "temperature": 0.8}}
        }


class AgentInstanceResponse(BaseModel):
    """Schema for agent instance response"""

    id: UUID
    agent_id: str
    agent_type: str
    status: str
    organization_id: UUID
    created_by_id: UUID | None
    created_at: str
    updated_at: str | None
    configuration: dict | None

    class Config:
        from_attributes = True


class AgentInstanceListResponse(BaseModel):
    """Schema for paginated agent instance list"""

    items: list[AgentInstanceResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# ============================================================================
# Endpoints
# ============================================================================


@router.get("", response_model=AgentInstanceListResponse)
async def list_agent_instances(
    org_id: UUID = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
    status_filter: str | None = Query(None, description="Filter by status"),
    agent_type_filter: str | None = Query(None, description="Filter by agent type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
):
    """
    List all agent instances for the current organization.

    This endpoint automatically filters agents to show only those belonging
    to the authenticated user's organization. Supports pagination and filtering.

    **Multi-tenant Security:**
    - Automatically scoped to user's organization
    - RLS policies enforce database-level isolation
    - No cross-organization data leakage

    **Query Parameters:**
    - `status_filter`: Filter by agent status (IDLE, BUSY, ERROR, etc.)
    - `agent_type_filter`: Filter by agent type
    - `page`: Page number for pagination
    - `page_size`: Number of items per page (max 100)

    **Returns:**
    - List of agent instances with pagination metadata
    """
    try:
        # Build base query with organization filter
        query = select(AgentInstance).filter_by(organization_id=org_id)

        # Apply filters if provided
        if status_filter:
            query = query.filter_by(status=status_filter)

        if agent_type_filter:
            query = query.filter_by(agent_type=agent_type_filter)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Order by created_at descending
        query = query.order_by(AgentInstance.created_at.desc())

        # Execute query
        result = await db.execute(query)
        agents = result.scalars().all()

        # Calculate pagination metadata
        has_more = (offset + len(agents)) < total

        logger.info(
            f"Listed {len(agents)} agent instances",
            extra={
                "organization_id": str(org_id),
                "user_id": str(current_user.id),
                "total": total,
                "page": page,
            },
        )

        return AgentInstanceListResponse(
            items=agents,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more,
        )

    except Exception as e:
        logger.error(f"Failed to list agent instances: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agent instances",
        )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=AgentInstanceResponse)
async def create_agent_instance(
    data: AgentInstanceCreate,
    org_id: UUID = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new agent instance for the current organization.

    The `organization_id` is automatically set from the authenticated user's
    organization. Users cannot create agents for other organizations.

    **Multi-tenant Security:**
    - organization_id automatically set from current user
    - Cannot create agents for other organizations
    - created_by_id tracks who created the agent

    **Request Body:**
    - `agent_id`: Unique identifier (must be unique within organization)
    - `agent_type`: Type of agent
    - `configuration`: Optional configuration dict

    **Returns:**
    - The created agent instance
    """
    try:
        # Check if agent_id already exists in this organization
        existing_query = select(AgentInstance).filter_by(
            agent_id=data.agent_id, organization_id=org_id
        )
        existing_result = await db.execute(existing_query)
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent with ID '{data.agent_id}' already exists in your organization",
            )

        # Create agent instance with organization_id
        agent = AgentInstance(
            agent_id=data.agent_id,
            agent_type=data.agent_type,
            status="INITIALIZING",
            configuration=data.configuration,
            organization_id=org_id,  # Multi-tenant isolation
            created_by_id=current_user.id,  # Audit trail
        )

        db.add(agent)
        await db.commit()
        await db.refresh(agent)

        logger.info(
            f"Created agent instance: {agent.agent_id}",
            extra={
                "agent_id": agent.agent_id,
                "organization_id": str(org_id),
                "user_id": str(current_user.id),
            },
        )

        return agent

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create agent instance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create agent instance",
        )


@router.get("/{agent_id}", response_model=AgentInstanceResponse)
async def get_agent_instance(
    agent_id: str,
    org_id: UUID = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get a specific agent instance by ID.

    Only returns agents that belong to the current organization.
    Returns 404 if the agent doesn't exist or belongs to another organization.

    **Multi-tenant Security:**
    - Query includes organization_id filter
    - Returns 404 for cross-organization access attempts
    - No information leakage about other organizations

    **Path Parameters:**
    - `agent_id`: The unique identifier of the agent

    **Returns:**
    - The agent instance if found in current organization
    - 404 if not found or no access
    """
    try:
        # Query with organization filter (defense in depth with RLS)
        query = select(AgentInstance).filter_by(agent_id=agent_id, organization_id=org_id)
        result = await db.execute(query)
        agent = result.scalar_one_or_none()

        if not agent:
            # Don't reveal whether agent exists in another organization
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found or you don't have access",
            )

        logger.info(
            f"Retrieved agent instance: {agent_id}",
            extra={
                "agent_id": agent_id,
                "organization_id": str(org_id),
                "user_id": str(current_user.id),
            },
        )

        return agent

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent instance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agent instance",
        )


@router.put("/{agent_id}", response_model=AgentInstanceResponse)
async def update_agent_instance(
    agent_id: str,
    data: AgentInstanceUpdate,
    org_id: UUID = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update an agent instance.

    Only updates agents that belong to the current organization.
    Returns 404 if the agent doesn't exist or belongs to another organization.

    **Multi-tenant Security:**
    - Query includes organization_id filter
    - Cannot update agents from other organizations
    - updated_by_id tracks who made changes

    **Path Parameters:**
    - `agent_id`: The unique identifier of the agent

    **Request Body:**
    - `status`: Optional new status
    - `configuration`: Optional updated configuration

    **Returns:**
    - The updated agent instance
    """
    try:
        # Query with organization filter
        query = select(AgentInstance).filter_by(agent_id=agent_id, organization_id=org_id)
        result = await db.execute(query)
        agent = result.scalar_one_or_none()

        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found or you don't have access",
            )

        # Update fields if provided
        if data.status is not None:
            agent.status = data.status

        if data.configuration is not None:
            agent.configuration = data.configuration

        # Set audit trail
        agent.updated_by_id = current_user.id

        await db.commit()
        await db.refresh(agent)

        logger.info(
            f"Updated agent instance: {agent_id}",
            extra={
                "agent_id": agent_id,
                "organization_id": str(org_id),
                "user_id": str(current_user.id),
                "updated_fields": [k for k, v in data.dict(exclude_unset=True).items()],
            },
        )

        return agent

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update agent instance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update agent instance",
        )


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent_instance(
    agent_id: str,
    org_id: UUID = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete an agent instance.

    Only deletes agents that belong to the current organization.
    Returns 404 if the agent doesn't exist or belongs to another organization.

    **Multi-tenant Security:**
    - Query includes organization_id filter
    - Cannot delete agents from other organizations
    - Audit logged before deletion

    **Path Parameters:**
    - `agent_id`: The unique identifier of the agent

    **Returns:**
    - 204 No Content on success
    - 404 if not found or no access
    """
    try:
        # Query with organization filter
        query = select(AgentInstance).filter_by(agent_id=agent_id, organization_id=org_id)
        result = await db.execute(query)
        agent = result.scalar_one_or_none()

        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found or you don't have access",
            )

        # Log before deletion
        logger.warning(
            f"Deleting agent instance: {agent_id}",
            extra={
                "agent_id": agent_id,
                "organization_id": str(org_id),
                "user_id": str(current_user.id),
            },
        )

        await db.delete(agent)
        await db.commit()

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete agent instance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete agent instance",
        )


@router.get("/{agent_id}/executions", response_model=list[dict])
async def get_agent_executions(
    agent_id: str,
    org_id: UUID = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of executions to return"),
):
    """
    Get execution history for a specific agent.

    Only returns executions for agents in the current organization.

    **Multi-tenant Security:**
    - Verifies agent belongs to current organization first
    - Execution query also filtered by organization_id (defense in depth)
    - Returns 404 for cross-organization access attempts

    **Path Parameters:**
    - `agent_id`: The unique identifier of the agent

    **Query Parameters:**
    - `limit`: Maximum number of executions to return (default 50, max 100)

    **Returns:**
    - List of agent execution records
    """
    try:
        # First verify agent belongs to current organization
        agent_query = select(AgentInstance).filter_by(agent_id=agent_id, organization_id=org_id)
        agent_result = await db.execute(agent_query)
        agent = agent_result.scalar_one_or_none()

        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found or you don't have access",
            )

        # Get executions (also filtered by organization_id for defense in depth)
        exec_query = (
            select(AgentExecution)
            .filter_by(agent_instance_id=agent.id, organization_id=org_id)
            .order_by(AgentExecution.created_at.desc())
            .limit(limit)
        )
        exec_result = await db.execute(exec_query)
        executions = exec_result.scalars().all()

        logger.info(
            f"Retrieved {len(executions)} executions for agent {agent_id}",
            extra={
                "agent_id": agent_id,
                "organization_id": str(org_id),
                "user_id": str(current_user.id),
                "execution_count": len(executions),
            },
        )

        # Convert to dict for response
        return [
            {
                "id": str(exec.id),
                "execution_id": exec.execution_id,
                "status": exec.status,
                "created_at": exec.created_at.isoformat() if exec.created_at else None,
                "completed_at": exec.completed_at.isoformat() if exec.completed_at else None,
            }
            for exec in executions
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent executions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agent executions",
        )


@router.get("/{agent_id}/metrics", response_model=dict)
async def get_agent_metrics(
    agent_id: str,
    org_id: UUID = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get performance metrics for a specific agent.

    Only returns metrics for agents in the current organization.

    **Multi-tenant Security:**
    - Verifies agent belongs to current organization first
    - Metrics query also filtered by organization_id
    - Returns 404 for cross-organization access attempts

    **Path Parameters:**
    - `agent_id`: The unique identifier of the agent

    **Returns:**
    - Agent performance metrics
    """
    try:
        # First verify agent belongs to current organization
        agent_query = select(AgentInstance).filter_by(agent_id=agent_id, organization_id=org_id)
        agent_result = await db.execute(agent_query)
        agent = agent_result.scalar_one_or_none()

        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found or you don't have access",
            )

        # Get latest metrics
        metrics_query = (
            select(AgentMetrics)
            .filter_by(agent_instance_id=agent.id, organization_id=org_id)
            .order_by(AgentMetrics.created_at.desc())
            .limit(1)
        )
        metrics_result = await db.execute(metrics_query)
        metrics = metrics_result.scalar_one_or_none()

        if not metrics:
            return {
                "agent_id": agent_id,
                "message": "No metrics available yet",
            }

        logger.info(
            f"Retrieved metrics for agent {agent_id}",
            extra={
                "agent_id": agent_id,
                "organization_id": str(org_id),
                "user_id": str(current_user.id),
            },
        )

        return {
            "agent_id": agent_id,
            "total_executions": metrics.total_executions,
            "successful_executions": metrics.successful_executions,
            "failed_executions": metrics.failed_executions,
            "average_execution_time": metrics.average_execution_time,
            "last_execution_time": (
                metrics.last_execution_time.isoformat() if metrics.last_execution_time else None
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agent metrics",
        )

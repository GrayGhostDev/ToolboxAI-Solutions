"""
Agent Health Check Endpoints - 2025 Implementation

This module provides comprehensive health monitoring for all agent types
in the ToolBoxAI system. Includes individual agent status, performance metrics,
and system-wide agent health indicators.

Features:
- Individual agent health status
- System-wide agent health overview
- Performance metrics and quality scores
- Error tracking and diagnostics
- Real-time status updates

Author: ToolboxAI Team
Created: 2025-09-21
Version: 1.0.0
"""

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Create router for agent health endpoints
router = APIRouter(prefix="/health", tags=["Health", "Agents"])


class AgentHealthResponse(BaseModel):
    """Response model for agent health status"""

    agent_id: str = Field(description="Unique agent identifier")
    agent_type: str = Field(description="Type of agent (content, quiz, etc.)")
    status: str = Field(description="Current agent status")
    last_activity: str | None = Field(description="Last activity timestamp")
    error_count: int = Field(description="Number of recent errors", default=0)
    quality_score: float | None = Field(description="Average quality score", ge=0.0, le=1.0)
    performance_metrics: dict[str, Any] = Field(
        description="Performance metrics", default_factory=dict
    )
    timestamp: str = Field(description="Health check timestamp")


class SystemAgentHealthResponse(BaseModel):
    """Response model for system-wide agent health"""

    status: str = Field(description="Overall system status")
    total_agents: int = Field(description="Total number of agents")
    healthy_agents: int = Field(description="Number of healthy agents")
    agents: dict[str, AgentHealthResponse] = Field(description="Individual agent statuses")
    system_metrics: dict[str, Any] = Field(description="System-wide metrics", default_factory=dict)
    timestamp: str = Field(description="Health check timestamp")


async def get_agent_service():
    """Get agent service instance with error handling"""
    try:
        from apps.backend.services.agent_service import (
            get_agent_service as _get_agent_service,
        )

        return _get_agent_service()
    except ImportError as e:
        logger.warning(f"Agent service not available: {e}")
        return None


@router.get("/agents", response_model=SystemAgentHealthResponse)
async def get_agents_health():
    """
    Get health status of all agents in the system

    Returns comprehensive health information including:
    - Overall system status
    - Individual agent statuses
    - Performance metrics
    - Error counts and diagnostics
    """
    try:
        agent_service = await get_agent_service()
        if not agent_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Agent service unavailable"
            )

        # Get system metrics
        try:
            system_metrics = agent_service.get_system_metrics()
        except Exception as e:
            logger.warning(f"Failed to get system metrics: {e}")
            system_metrics = {
                "error": "Metrics unavailable",
                "agents": {"total": 0},
                "system": {"status": "unknown"},
            }

        # Build health status for each agent
        agents_health = {}
        healthy_count = 0
        total_count = 0

        # Check if agents are available
        if hasattr(agent_service, "agents") and agent_service.agents:
            for agent_id, agent in agent_service.agents.items():
                try:
                    # Get agent status with error handling
                    agent_status = "healthy"
                    last_activity = None
                    error_count = 0
                    quality_score = None
                    performance_metrics = {}

                    # Try to get detailed status
                    if hasattr(agent, "get_status"):
                        try:
                            agent_status = agent.get_status()
                        except Exception:
                            agent_status = "unknown"

                    if hasattr(agent, "last_activity"):
                        try:
                            last_activity = agent.last_activity
                            if isinstance(last_activity, datetime):
                                last_activity = last_activity.isoformat()
                        except Exception:
                            pass

                    if hasattr(agent, "error_count"):
                        try:
                            error_count = agent.error_count or 0
                        except Exception:
                            error_count = 0

                    if hasattr(agent, "get_average_quality_score"):
                        try:
                            quality_score = agent.get_average_quality_score()
                        except Exception:
                            quality_score = 0.85  # Default quality score

                    # Get performance metrics if available
                    if hasattr(agent, "get_performance_metrics"):
                        try:
                            performance_metrics = agent.get_performance_metrics()
                        except Exception:
                            performance_metrics = {}

                    # Determine agent type
                    agent_type = getattr(agent, "agent_type", "unknown")

                    agents_health[agent_id] = AgentHealthResponse(
                        agent_id=agent_id,
                        agent_type=agent_type,
                        status=agent_status,
                        last_activity=last_activity,
                        error_count=error_count,
                        quality_score=quality_score,
                        performance_metrics=performance_metrics,
                        timestamp=datetime.now(timezone.utc).isoformat(),
                    )

                    total_count += 1
                    if agent_status in ["healthy", "idle", "ready"]:
                        healthy_count += 1

                except Exception as e:
                    logger.warning(f"Failed to get health for agent {agent_id}: {e}")
                    # Add unhealthy agent entry
                    agents_health[agent_id] = AgentHealthResponse(
                        agent_id=agent_id,
                        agent_type="unknown",
                        status="unhealthy",
                        last_activity=None,
                        error_count=1,
                        quality_score=0.0,
                        performance_metrics={"error": str(e)},
                        timestamp=datetime.now(timezone.utc).isoformat(),
                    )
                    total_count += 1

        # Determine overall system status
        if total_count == 0:
            overall_status = "no_agents"
        elif healthy_count == total_count:
            overall_status = "healthy"
        elif healthy_count >= total_count * 0.8:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"

        return SystemAgentHealthResponse(
            status=overall_status,
            total_agents=total_count,
            healthy_agents=healthy_count,
            agents=agents_health,
            system_metrics=system_metrics,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agents health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.get("/agents/{agent_id}", response_model=AgentHealthResponse)
async def get_agent_health(agent_id: str):
    """
    Get health status of a specific agent

    Args:
        agent_id: Unique identifier of the agent to check

    Returns:
        Detailed health information for the specified agent
    """
    try:
        agent_service = await get_agent_service()
        if not agent_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Agent service unavailable"
            )

        # Check if agent exists
        if not hasattr(agent_service, "agents") or not agent_service.agents:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No agents available")

        agent = agent_service.agents.get(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent {agent_id} not found"
            )

        # Get detailed agent information
        agent_status = "healthy"
        last_activity = None
        error_count = 0
        quality_score = None
        performance_metrics = {}

        # Try to get detailed status
        if hasattr(agent, "get_status"):
            try:
                agent_status = agent.get_status()
            except Exception as e:
                logger.warning(f"Failed to get status for agent {agent_id}: {e}")
                agent_status = "unknown"

        if hasattr(agent, "last_activity"):
            try:
                last_activity = agent.last_activity
                if isinstance(last_activity, datetime):
                    last_activity = last_activity.isoformat()
            except Exception:
                pass

        if hasattr(agent, "error_count"):
            try:
                error_count = agent.error_count or 0
            except Exception:
                error_count = 0

        if hasattr(agent, "get_average_quality_score"):
            try:
                quality_score = agent.get_average_quality_score()
            except Exception:
                quality_score = 0.85  # Default quality score

        # Get performance metrics if available
        if hasattr(agent, "get_performance_metrics"):
            try:
                performance_metrics = agent.get_performance_metrics()
            except Exception as e:
                performance_metrics = {"metrics_error": str(e)}

        # Determine agent type
        agent_type = getattr(agent, "agent_type", "unknown")

        return AgentHealthResponse(
            agent_id=agent_id,
            agent_type=agent_type,
            status=agent_status,
            last_activity=last_activity,
            error_count=error_count,
            quality_score=quality_score,
            performance_metrics=performance_metrics,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get health for agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.get("/agents/type/{agent_type}")
async def get_agents_health_by_type(agent_type: str):
    """
    Get health status of all agents of a specific type

    Args:
        agent_type: Type of agents to check (content, quiz, terrain, script, code_review)

    Returns:
        Health information for all agents of the specified type
    """
    try:
        agent_service = await get_agent_service()
        if not agent_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Agent service unavailable"
            )

        # Filter agents by type
        filtered_agents = {}
        if hasattr(agent_service, "agents") and agent_service.agents:
            for agent_id, agent in agent_service.agents.items():
                if getattr(agent, "agent_type", None) == agent_type:
                    try:
                        # Get agent health information
                        agent_status = "healthy"
                        if hasattr(agent, "get_status"):
                            agent_status = agent.get_status()

                        last_activity = None
                        if hasattr(agent, "last_activity"):
                            last_activity = agent.last_activity
                            if isinstance(last_activity, datetime):
                                last_activity = last_activity.isoformat()

                        error_count = getattr(agent, "error_count", 0) or 0
                        quality_score = None
                        if hasattr(agent, "get_average_quality_score"):
                            quality_score = agent.get_average_quality_score()

                        performance_metrics = {}
                        if hasattr(agent, "get_performance_metrics"):
                            performance_metrics = agent.get_performance_metrics()

                        filtered_agents[agent_id] = {
                            "agent_id": agent_id,
                            "agent_type": agent_type,
                            "status": agent_status,
                            "last_activity": last_activity,
                            "error_count": error_count,
                            "quality_score": quality_score,
                            "performance_metrics": performance_metrics,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    except Exception as e:
                        logger.warning(f"Failed to get health for agent {agent_id}: {e}")

        if not filtered_agents:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No agents of type '{agent_type}' found",
            )

        return {
            "agent_type": agent_type,
            "total_agents": len(filtered_agents),
            "agents": filtered_agents,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get health for agent type {agent_type}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.get("/agents/metrics/summary")
async def get_agent_metrics_summary():
    """
    Get summarized performance metrics for all agents

    Returns:
        Aggregated performance metrics and quality scores
    """
    try:
        agent_service = await get_agent_service()
        if not agent_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Agent service unavailable"
            )

        # Get system metrics
        try:
            system_metrics = agent_service.get_system_metrics()
        except Exception as e:
            logger.warning(f"Failed to get system metrics: {e}")
            system_metrics = {}

        # Calculate summary metrics
        total_agents = 0
        total_quality_score = 0.0
        total_errors = 0
        agent_types = {}

        if hasattr(agent_service, "agents") and agent_service.agents:
            for agent_id, agent in agent_service.agents.items():
                total_agents += 1

                # Count by type
                agent_type = getattr(agent, "agent_type", "unknown")
                if agent_type not in agent_types:
                    agent_types[agent_type] = 0
                agent_types[agent_type] += 1

                # Sum quality scores
                if hasattr(agent, "get_average_quality_score"):
                    try:
                        quality = agent.get_average_quality_score()
                        if quality:
                            total_quality_score += quality
                    except Exception:
                        total_quality_score += 0.85  # Default

                # Sum error counts
                if hasattr(agent, "error_count"):
                    try:
                        errors = agent.error_count or 0
                        total_errors += errors
                    except Exception:
                        pass

        avg_quality = total_quality_score / total_agents if total_agents > 0 else 0.0

        return {
            "summary": {
                "total_agents": total_agents,
                "average_quality_score": avg_quality,
                "total_errors": total_errors,
                "agent_types": agent_types,
            },
            "system_metrics": system_metrics,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent metrics summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


# Export router
__all__ = ["router"]

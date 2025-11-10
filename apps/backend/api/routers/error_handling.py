"""
Error Handling Swarm API Endpoints

FastAPI router for error handling agent swarm operations.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import json

from core.agents.error_handling import (
    ErrorHandlingSwarmCoordinator,
    ErrorState,
    ErrorType,
    ErrorPriority,
)
from core.swarm.error_handling.error_handling_workflow import ErrorHandlingWorkflow

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/error-handling",
    tags=["error-handling"],
    responses={404: {"description": "Not found"}},
)

# Initialize swarm coordinator and workflow
swarm_coordinator = ErrorHandlingSwarmCoordinator()
error_workflow = ErrorHandlingWorkflow()

# Track active workflows
active_workflows = {}


class ErrorReport(BaseModel):
    """Model for error report submission"""

    error_message: str = Field(description="Error message")
    error_type: str = Field(description="Type of error")
    stack_trace: Optional[str] = Field(default=None, description="Stack trace")
    file_path: Optional[str] = Field(default=None, description="File path where error occurred")
    line_number: Optional[int] = Field(default=None, description="Line number")
    priority: Optional[str] = Field(default="MEDIUM", description="Error priority")
    affected_components: Optional[List[str]] = Field(default=[], description="Affected components")
    context: Optional[Dict[str, Any]] = Field(default={}, description="Additional context")


class SwarmRequest(BaseModel):
    """Model for swarm processing request"""

    errors: List[ErrorReport] = Field(description="List of errors to process")
    strategy: Optional[str] = Field(default="auto", description="Processing strategy")
    async_processing: bool = Field(default=True, description="Process asynchronously")
    context: Optional[Dict[str, Any]] = Field(default={}, description="Processing context")


class WorkflowStatus(BaseModel):
    """Model for workflow status response"""

    workflow_id: str = Field(description="Workflow identifier")
    status: str = Field(description="Current status")
    errors_processed: int = Field(description="Number of errors processed")
    agents_active: List[str] = Field(description="Active agents")
    progress_percentage: float = Field(description="Progress percentage")
    estimated_completion: Optional[str] = Field(description="Estimated completion time")


@router.post("/report-error", response_model=Dict[str, Any])
async def report_error(error_report: ErrorReport, background_tasks: BackgroundTasks):
    """
    Report a single error for processing.

    Args:
        error_report: Error details
        background_tasks: FastAPI background tasks

    Returns:
        Response with error ID and processing status
    """
    try:
        # Convert to ErrorState
        error_state: ErrorState = {
            "error_id": f"err_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "error_type": ErrorType[error_report.error_type.upper()],
            "priority": ErrorPriority[error_report.priority.upper()],
            "description": error_report.error_message,
            "stack_trace": error_report.stack_trace,
            "file_path": error_report.file_path,
            "line_number": error_report.line_number,
            "context": error_report.context,
            "attempted_fixes": [],
            "resolution_status": "reported",
            "timestamp": datetime.now().isoformat(),
            "affected_components": error_report.affected_components,
            "potential_impact": "Unknown",
            "recovery_strategy": None,
            "metadata": {},
        }

        # Process in background
        background_tasks.add_task(process_single_error, error_state)

        return {
            "status": "success",
            "error_id": error_state["error_id"],
            "message": "Error reported successfully",
            "processing": "initiated",
        }

    except Exception as e:
        logger.error(f"Error reporting failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-errors", response_model=Dict[str, Any])
async def process_errors(swarm_request: SwarmRequest, background_tasks: BackgroundTasks):
    """
    Process multiple errors using the swarm.

    Args:
        swarm_request: Swarm processing request
        background_tasks: FastAPI background tasks

    Returns:
        Response with workflow ID and initial status
    """
    try:
        # Convert error reports to ErrorStates
        error_states = []
        for report in swarm_request.errors:
            error_state: ErrorState = {
                "error_id": f"err_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(error_states)}",
                "error_type": ErrorType[report.error_type.upper()],
                "priority": ErrorPriority[report.priority.upper()],
                "description": report.error_message,
                "stack_trace": report.stack_trace,
                "file_path": report.file_path,
                "line_number": report.line_number,
                "context": report.context,
                "attempted_fixes": [],
                "resolution_status": "pending",
                "timestamp": datetime.now().isoformat(),
                "affected_components": report.affected_components,
                "potential_impact": "Unknown",
                "recovery_strategy": None,
                "metadata": {},
            }
            error_states.append(error_state)

        # Create workflow ID
        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        if swarm_request.async_processing:
            # Process asynchronously
            background_tasks.add_task(
                run_swarm_workflow, workflow_id, error_states, swarm_request.context
            )

            return {
                "status": "success",
                "workflow_id": workflow_id,
                "message": f"Processing {len(error_states)} errors asynchronously",
                "async": True,
            }
        else:
            # Process synchronously
            result = await swarm_coordinator.orchestrate_error_handling(
                error_states, swarm_request.context
            )

            return {
                "status": "success",
                "workflow_id": workflow_id,
                "result": result.model_dump(),
                "async": False,
            }

    except Exception as e:
        logger.error(f"Error processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflow/{workflow_id}/status", response_model=WorkflowStatus)
async def get_workflow_status(workflow_id: str):
    """
    Get status of a workflow.

    Args:
        workflow_id: Workflow identifier

    Returns:
        Workflow status
    """
    if workflow_id not in active_workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow = active_workflows[workflow_id]

    return WorkflowStatus(
        workflow_id=workflow_id,
        status=workflow.get("status", "unknown"),
        errors_processed=workflow.get("errors_processed", 0),
        agents_active=workflow.get("agents_active", []),
        progress_percentage=workflow.get("progress", 0.0),
        estimated_completion=workflow.get("estimated_completion"),
    )


@router.get("/patterns/analyze", response_model=Dict[str, Any])
async def analyze_error_patterns(timeframe_days: int = 7):
    """
    Analyze error patterns over a timeframe.

    Args:
        timeframe_days: Number of days to analyze

    Returns:
        Pattern analysis results
    """
    try:
        # Get pattern analysis agent
        pattern_analyzer = swarm_coordinator.agents["pattern_analysis"]

        # Get error history (in production, would fetch from database)
        error_history = []  # Would fetch from database

        # Analyze patterns
        analysis = await pattern_analyzer.analyze_error_patterns(error_history, timeframe_days)

        return {"status": "success", "analysis": analysis, "timeframe_days": timeframe_days}

    except Exception as e:
        logger.error(f"Pattern analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict-errors", response_model=Dict[str, Any])
async def predict_errors(timeframe_hours: int = 24):
    """
    Predict future errors based on patterns.

    Args:
        timeframe_hours: Prediction timeframe in hours

    Returns:
        Predictions
    """
    try:
        # Get pattern analysis agent
        pattern_analyzer = swarm_coordinator.agents["pattern_analysis"]

        # Generate predictions (simplified)
        predictions = []  # Would generate actual predictions

        return {
            "status": "success",
            "predictions": predictions,
            "timeframe_hours": timeframe_hours,
            "confidence": 0.0,
        }

    except Exception as e:
        logger.error(f"Error prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/swarm/status", response_model=Dict[str, Any])
async def get_swarm_status():
    """
    Get current status of the error handling swarm.

    Returns:
        Swarm status including active agents and metrics
    """
    try:
        status = await swarm_coordinator.get_swarm_status()

        return {
            "status": "success",
            "swarm_status": status,
            "active_workflows": len(active_workflows),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get swarm status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recovery/trigger", response_model=Dict[str, Any])
async def trigger_recovery(
    component: str, strategy: Optional[str] = None, background_tasks: BackgroundTasks = None
):
    """
    Trigger recovery for a specific component.

    Args:
        component: Component to recover
        strategy: Recovery strategy to use
        background_tasks: FastAPI background tasks

    Returns:
        Recovery initiation status
    """
    try:
        # Get recovery orchestrator
        recovery_orchestrator = swarm_coordinator.agents["recovery"]

        # Create error state for recovery
        error_state: ErrorState = {
            "error_id": f"recovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "error_type": ErrorType.RUNTIME,
            "priority": ErrorPriority.HIGH,
            "description": f"Manual recovery triggered for {component}",
            "stack_trace": None,
            "file_path": None,
            "line_number": None,
            "context": {"component": component},
            "attempted_fixes": [],
            "resolution_status": "recovery_initiated",
            "timestamp": datetime.now().isoformat(),
            "affected_components": [component],
            "potential_impact": "Component failure",
            "recovery_strategy": strategy,
            "metadata": {},
        }

        # Trigger recovery
        if background_tasks:
            background_tasks.add_task(recovery_orchestrator.orchestrate_recovery, error_state)
            return {
                "status": "success",
                "message": f"Recovery initiated for {component}",
                "async": True,
            }
        else:
            recovery_result = await recovery_orchestrator.orchestrate_recovery(error_state)
            return {
                "status": "success",
                "recovery_result": recovery_result.model_dump(),
                "async": False,
            }

    except Exception as e:
        logger.error(f"Recovery trigger failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=Dict[str, Any])
async def get_error_metrics():
    """
    Get comprehensive error handling metrics.

    Returns:
        Metrics from all agents
    """
    try:
        metrics = {}

        # Collect metrics from all agents
        for agent_name, agent in swarm_coordinator.agents.items():
            agent_metrics = await agent.get_error_metrics()
            metrics[agent_name] = agent_metrics

        # Add workflow metrics
        metrics["workflows"] = {
            "active": len(active_workflows),
            "total_processed": sum(w.get("errors_processed", 0) for w in active_workflows.values()),
        }

        return {"status": "success", "metrics": metrics, "timestamp": datetime.now().isoformat()}

    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Background task functions


async def process_single_error(error_state: ErrorState):
    """Process a single error in the background"""
    try:
        # Use aggregation agent to process single error
        aggregator = swarm_coordinator.agents["aggregation"]
        await aggregator.aggregate_errors([error_state], source="api")

        logger.info(f"Processed error {error_state['error_id']}")
    except Exception as e:
        logger.error(f"Background error processing failed: {e}")


async def run_swarm_workflow(
    workflow_id: str, error_states: List[ErrorState], context: Dict[str, Any]
):
    """Run swarm workflow in the background"""
    try:
        # Track workflow
        active_workflows[workflow_id] = {
            "status": "running",
            "errors_processed": 0,
            "agents_active": [],
            "progress": 0.0,
            "started": datetime.now().isoformat(),
        }

        # Execute workflow
        result = await swarm_coordinator.orchestrate_error_handling(error_states, context)

        # Update workflow status
        active_workflows[workflow_id].update(
            {
                "status": "completed",
                "errors_processed": result.errors_processed,
                "agents_active": result.agents_involved,
                "progress": 100.0,
                "completed": datetime.now().isoformat(),
                "result": result.model_dump(),
            }
        )

        logger.info(f"Workflow {workflow_id} completed successfully")

    except Exception as e:
        logger.error(f"Workflow {workflow_id} failed: {e}")
        active_workflows[workflow_id]["status"] = "failed"
        active_workflows[workflow_id]["error"] = str(e)

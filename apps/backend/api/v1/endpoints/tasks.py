"""
Tasks API endpoints for Celery background job management.

Provides endpoints to manage and monitor background tasks including:
- Task status checking
- Task submission
- Task cancellation
- Worker health monitoring
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from apps.backend.celery_app import app as celery_app
from apps.backend.core.security.jwt_handler import get_current_user
from apps.backend.tasks import (
    aggregate_usage_metrics,
    cleanup_expired_sessions,
    cleanup_old_files,
    generate_educational_content,
    send_notification,
)

router = APIRouter(prefix="/tasks", tags=["Background Tasks"])


class TaskSubmission(BaseModel):
    """Task submission request model."""

    task_type: str = Field(..., description="Type of task to execute")
    task_data: dict[str, Any] = Field(default_factory=dict, description="Task parameters")
    priority: int = Field(default=5, ge=0, le=10, description="Task priority (0-10)")


class TaskStatus(BaseModel):
    """Task status response model."""

    task_id: str
    status: str
    result: Any | None = None
    error: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None


class WorkerStatus(BaseModel):
    """Worker status information."""

    worker_name: str
    status: str
    active_tasks: int
    processed_tasks: int
    uptime: float


@router.get("/status")
async def get_tasks_status():
    """
    Get overall tasks system status.

    Returns information about:
    - Celery app configuration
    - Registered tasks
    - Active workers
    - Queue statistics
    """
    try:
        # Get Celery inspector
        inspector = celery_app.control.inspect()

        # Get active workers
        active_workers = inspector.active()
        inspector.registered()
        stats = inspector.stats()

        # Count total active tasks
        total_active = 0
        if active_workers:
            for worker, tasks in active_workers.items():
                total_active += len(tasks)

        return {
            "status": "operational",
            "broker_url": celery_app.conf.broker_url.replace(
                celery_app.conf.broker_url.split("@")[0], "redis://***"
            ),
            "registered_tasks": len(celery_app.tasks),
            "task_names": list(celery_app.tasks.keys())[:10],  # Show first 10 task names
            "workers": {
                "count": len(active_workers) if active_workers else 0,
                "names": list(active_workers.keys()) if active_workers else [],
                "active_tasks": total_active,
            },
            "stats": stats or {},
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "workers": {"count": 0, "names": [], "active_tasks": 0},
        }


@router.post("/submit", response_model=TaskStatus)
async def submit_task(
    task: TaskSubmission,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """
    Submit a new background task for execution.

    Available task types:
    - cleanup: Clean up old files
    - content_generation: Generate educational content
    - notification: Send notifications
    - analytics: Aggregate usage metrics
    """
    try:
        # Map task types to actual Celery tasks
        task_map = {
            "cleanup": cleanup_old_files,
            "content_generation": generate_educational_content,
            "notification": send_notification,
            "analytics": aggregate_usage_metrics,
            "cleanup_sessions": cleanup_expired_sessions,
        }

        if task.task_type not in task_map:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown task type: {task.task_type}. Available: {list(task_map.keys())}",
            )

        # Submit task with priority
        celery_task = task_map[task.task_type]
        result = celery_task.apply_async(kwargs=task.task_data, priority=task.priority)

        return TaskStatus(task_id=result.id, status="submitted", created_at=datetime.utcnow())

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit task: {str(e)}")


@router.get("/task/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """
    Get the status of a specific task by ID.

    Returns task state which can be:
    - PENDING: Task waiting for execution
    - STARTED: Task has been started
    - SUCCESS: Task executed successfully
    - FAILURE: Task execution failed
    - RETRY: Task is being retried
    - REVOKED: Task was revoked
    """
    try:
        from celery.result import AsyncResult

        result = AsyncResult(task_id, app=celery_app)

        response = TaskStatus(task_id=task_id, status=result.state)

        if result.ready():
            if result.successful():
                response.result = result.result
                response.completed_at = datetime.utcnow()
            else:
                response.error = str(result.info)

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


@router.delete("/task/{task_id}")
async def cancel_task(task_id: str, current_user: dict = Depends(get_current_user)):
    """
    Cancel a pending or running task.

    Note: Tasks that have already completed cannot be cancelled.
    """
    try:
        celery_app.control.revoke(task_id, terminate=True)

        return {
            "task_id": task_id,
            "status": "cancelled",
            "message": "Task cancellation requested",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")


@router.get("/workers", response_model=list[WorkerStatus])
async def get_workers_status():
    """
    Get status of all Celery workers.

    Returns information about each worker including:
    - Worker name and status
    - Number of active tasks
    - Total processed tasks
    - Worker uptime
    """
    try:
        inspector = celery_app.control.inspect()

        active = inspector.active() or {}
        stats = inspector.stats() or {}

        workers = []
        for worker_name in stats.keys():
            worker_stats = stats[worker_name]
            active_tasks = len(active.get(worker_name, []))

            workers.append(
                WorkerStatus(
                    worker_name=worker_name,
                    status="online",
                    active_tasks=active_tasks,
                    processed_tasks=worker_stats.get("total", {}).get("tasks.cleanup_old_files", 0),
                    uptime=worker_stats.get("clock", 0),
                )
            )

        return workers

    except Exception:
        return []


@router.post("/trigger-cleanup")
async def trigger_cleanup(
    directory: str = Query("/tmp", description="Directory to clean"),
    days_old: int = Query(7, description="Files older than this many days"),
    current_user: dict = Depends(get_current_user),
):
    """
    Trigger a cleanup task for old files.

    This endpoint demonstrates how to trigger specific Celery tasks.
    """
    try:
        result = cleanup_old_files.delay(directory=directory, days_old=days_old)

        return {
            "task_id": result.id,
            "status": "submitted",
            "message": f"Cleanup task submitted for {directory} (files older than {days_old} days)",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger cleanup: {str(e)}")


@router.get("/queue-stats")
async def get_queue_statistics():
    """
    Get statistics about task queues.

    Returns information about:
    - Queue lengths
    - Task distribution
    - Priority queue status
    """
    try:
        inspector = celery_app.control.inspect()

        # Get queue information
        active = inspector.active() or {}
        scheduled = inspector.scheduled() or {}
        reserved = inspector.reserved() or {}

        total_active = sum(len(tasks) for tasks in active.values())
        total_scheduled = sum(len(tasks) for tasks in scheduled.values())
        total_reserved = sum(len(tasks) for tasks in reserved.values())

        return {
            "queues": {
                "active": total_active,
                "scheduled": total_scheduled,
                "reserved": total_reserved,
                "total": total_active + total_scheduled + total_reserved,
            },
            "workers": len(active),
            "details": {
                "active_by_worker": {w: len(t) for w, t in active.items()},
                "scheduled_by_worker": {w: len(t) for w, t in scheduled.items()},
                "reserved_by_worker": {w: len(t) for w, t in reserved.items()},
            },
        }

    except Exception as e:
        return {
            "queues": {"active": 0, "scheduled": 0, "reserved": 0, "total": 0},
            "workers": 0,
            "error": str(e),
        }


# Export router with expected name
__all__ = ["router"]

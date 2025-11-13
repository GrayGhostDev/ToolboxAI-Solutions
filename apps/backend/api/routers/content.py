"""
Content Generation Router

Handles content generation, retrieval, and management endpoints.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from apps.backend.api.auth.auth import get_current_user, require_any_role
from apps.backend.core.logging import log_audit, log_execution_time, logging_manager
from apps.backend.models.schemas import (
    ContentRequest,
    ContentResponse,
    User,
)

logger = logging_manager.get_logger(__name__)

router = APIRouter(tags=["Content Generation"])


# Request/Response Models for Celery Tasks
class GenerateLessonRequest(BaseModel):
    """Request model for lesson content generation"""

    lesson_id: str = Field(..., description="Unique lesson identifier")
    subject: str = Field(..., description="Subject area (e.g., Mathematics, Science)")
    topic: str = Field(..., description="Specific topic for the lesson")
    grade_level: str = Field(..., description="Target grade level (e.g., 3-5, 6-8)")
    learning_objectives: list[str] | None = Field(None, description="List of learning objectives")
    duration: int = Field(45, description="Lesson duration in minutes")


class GenerateQuizRequest(BaseModel):
    """Request model for quiz generation"""

    assessment_id: str = Field(..., description="Unique assessment identifier")
    subject: str = Field(..., description="Subject area")
    topic: str = Field(..., description="Specific topic for questions")
    grade_level: str = Field(..., description="Target grade level")
    num_questions: int = Field(10, description="Number of questions to generate")
    difficulty: str = Field("medium", description="Difficulty level (easy, medium, hard, expert)")
    question_types: list[str] | None = Field(
        None, description="Question types (multiple_choice, true_false)"
    )
    learning_objectives: list[str] | None = Field(None, description="Learning objectives to assess")
    lesson_id: str | None = Field(None, description="Associated lesson ID")


class OptimizeScriptRequest(BaseModel):
    """Request model for Roblox script optimization"""

    script_id: str = Field(..., description="Unique script identifier")
    script_code: str = Field(..., description="Luau script code to optimize")
    script_name: str = Field(..., description="Name/description of the script")
    optimization_level: str = Field(
        "balanced", description="Optimization level (conservative, balanced, aggressive)"
    )
    preserve_comments: bool = Field(True, description="Whether to preserve comments")
    generate_report: bool = Field(True, description="Whether to generate detailed report")


@router.post("/api/v1/content/generate", response_model=ContentResponse)
async def generate_content(
    content_request: ContentRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> ContentResponse:
    """
    Generate educational content using AI agents

    Args:
        content_request: Content generation request
        background_tasks: FastAPI background tasks
        request: Request object
        current_user: Authenticated user

    Returns:
        ContentResponse: Generated content
    """
    start_time = datetime.now()
    request_id = str(uuid.uuid4())

    logger.info(
        f"Content generation request started",
        extra_fields={
            "request_id": request_id,
            "user_id": current_user.id,
            "topic": content_request.topic,
            "content_type": getattr(content_request, "content_type", "general"),
        },
    )

    try:
        # Import content generation function
        from apps.backend.agents.agent import generate_educational_content

        # Generate content using agents
        result = await generate_educational_content(
            topic=content_request.topic,
            subject=getattr(content_request, "subject", None),
            grade_level=getattr(content_request, "grade_level", None),
            content_type=getattr(content_request, "content_type", "lesson"),
            user_id=current_user.id,
        )

        # Log successful generation
        log_execution_time("content_generation", start_time)
        log_audit(
            action="content_generated",
            user_id=current_user.id,
            resource_type="educational_content",
            resource_id=request_id,
            details={"topic": content_request.topic, "result_length": len(str(result))},
        )

        # Broadcast update via Pusher
        background_tasks.add_task(
            _broadcast_content_update,
            user_id=current_user.id,
            content_id=request_id,
            status="completed",
            result=result,
        )

        return ContentResponse(
            status="success",
            content=result,
            metadata={
                "request_id": request_id,
                "generation_time": (datetime.now() - start_time).total_seconds(),
                "agent_used": "educational_content_agent",
                "user_id": current_user.id,
            },
        )

    except Exception as e:
        logger.error(
            f"Content generation failed: {e}",
            extra_fields={"request_id": request_id, "user_id": current_user.id, "error": str(e)},
        )

        # Broadcast error via Pusher
        background_tasks.add_task(
            _broadcast_content_update,
            user_id=current_user.id,
            content_id=request_id,
            status="failed",
            error=str(e),
        )

        raise HTTPException(status_code=500, detail=f"Content generation failed: {str(e)}")


@router.get("/content/{content_id}")
async def get_content(
    content_id: str, current_user: User = Depends(get_current_user)
) -> JSONResponse:
    """
    Retrieve generated content by ID

    Args:
        content_id: Content identifier
        current_user: Authenticated user

    Returns:
        JSONResponse: Content data
    """
    try:
        # For now, return a placeholder response
        # In a full implementation, this would retrieve from database
        content_data = {
            "id": content_id,
            "status": "completed",
            "content": f"Retrieved content for ID: {content_id}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "user_id": current_user.id,
        }

        log_audit(
            action="content_retrieved",
            user_id=current_user.id,
            resource_type="educational_content",
            resource_id=content_id,
        )

        return JSONResponse(
            content={
                "status": "success",
                "data": content_data,
                "message": "Content retrieved successfully",
            }
        )

    except Exception as e:
        logger.error(f"Failed to retrieve content {content_id}: {e}")
        raise HTTPException(status_code=404, detail=f"Content not found: {content_id}")


@router.get("/content/{content_id}/stream")
async def stream_content_generation(
    content_id: str, current_user: User = Depends(get_current_user)
) -> StreamingResponse:
    """
    Stream content generation progress

    Args:
        content_id: Content identifier
        current_user: Authenticated user

    Returns:
        StreamingResponse: Streaming response with generation progress
    """
    try:

        async def generate_stream():
            """Generate streaming content updates"""
            # Simulate streaming content generation
            stages = [
                "Initializing content generation...",
                "Analyzing topic and requirements...",
                "Generating content structure...",
                "Creating detailed content...",
                "Finalizing and formatting...",
                "Content generation completed!",
            ]

            for i, stage in enumerate(stages):
                progress = (i + 1) / len(stages) * 100
                data = {
                    "content_id": content_id,
                    "stage": stage,
                    "progress": progress,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                yield f"data: {data}\n\n"

                # Simulate processing time
                import asyncio

                await asyncio.sleep(1)

        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Encoding": "identity",
            },
        )

    except Exception as e:
        logger.error(f"Failed to stream content generation {content_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to stream content generation: {str(e)}"
        )


@router.delete("/content/{content_id}")
async def delete_content(
    content_id: str, current_user: User = Depends(require_any_role(["admin", "teacher"]))
) -> JSONResponse:
    """
    Delete generated content

    Args:
        content_id: Content identifier
        current_user: Authenticated user with appropriate role

    Returns:
        JSONResponse: Deletion result
    """
    try:
        # For now, return a placeholder response
        # In a full implementation, this would delete from database

        log_audit(
            action="content_deleted",
            user_id=current_user.id,
            resource_type="educational_content",
            resource_id=content_id,
        )

        return JSONResponse(
            content={
                "status": "success",
                "data": {"content_id": content_id, "deleted": True},
                "message": "Content deleted successfully",
            }
        )

    except Exception as e:
        logger.error(f"Failed to delete content {content_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete content: {str(e)}")


@router.get("/content/user/{user_id}")
async def get_user_content(
    user_id: str, current_user: User = Depends(get_current_user), limit: int = 10, offset: int = 0
) -> JSONResponse:
    """
    Get content generated by a specific user

    Args:
        user_id: User identifier
        current_user: Authenticated user
        limit: Maximum number of results
        offset: Results offset for pagination

    Returns:
        JSONResponse: User's content list
    """
    try:
        # Check if user can access this data
        if current_user.id != user_id and not _user_has_role(current_user, ["admin", "teacher"]):
            raise HTTPException(
                status_code=403, detail="Insufficient permissions to access user content"
            )

        # For now, return placeholder data
        # In a full implementation, this would query the database
        content_list = [
            {
                "id": f"content_{i}",
                "topic": f"Sample Topic {i}",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "completed",
            }
            for i in range(offset, offset + limit)
        ]

        return JSONResponse(
            content={
                "status": "success",
                "data": {
                    "content": content_list,
                    "total": 50,  # Placeholder total
                    "limit": limit,
                    "offset": offset,
                },
                "message": "User content retrieved successfully",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user content for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user content: {str(e)}")


async def _broadcast_content_update(
    user_id: str,
    content_id: str,
    status: str,
    result: str | None = None,
    error: str | None = None,
) -> None:
    """
    Broadcast content generation update via Pusher

    Args:
        user_id: User identifier
        content_id: Content identifier
        status: Generation status
        result: Generated content (if successful)
        error: Error message (if failed)
    """
    try:
        from apps.backend.services.pusher_handler import broadcast_content_update

        await broadcast_content_update(
            user_id=user_id, content_id=content_id, status=status, result=result, error=error
        )

    except Exception as e:
        logger.warning(f"Failed to broadcast content update: {e}")


def _user_has_role(user: User, required_roles: list) -> bool:
    """
    Check if user has any of the required roles

    Args:
        user: User object
        required_roles: List of required roles

    Returns:
        bool: True if user has any required role
    """
    user_role = getattr(user, "role", None)
    return user_role in required_roles if user_role else False


# ============================================================================
# Celery Task Endpoints - Content Generation via Background Jobs
# ============================================================================


@router.post("/api/v1/content/lessons/generate")
async def generate_lesson_content(
    request: GenerateLessonRequest,
    current_user: User = Depends(require_any_role(["admin", "teacher"])),
) -> JSONResponse:
    """
    Generate educational lesson content using Celery background task

    Args:
        request: Lesson generation parameters
        current_user: Authenticated user (admin/teacher only)

    Returns:
        JSONResponse: Task ID and status for tracking progress

    Permissions:
        - admin: Can generate lessons for any organization
        - teacher: Can generate lessons for their organization
    """
    try:
        # Import Celery task
        from apps.backend.workers.tasks.content_tasks import (
            generate_lesson_content_sync,
        )

        # Get organization ID from user context
        organization_id = getattr(current_user, "organization_id", "default_org")

        # Queue the task
        task = generate_lesson_content_sync.delay(
            lesson_id=request.lesson_id,
            organization_id=organization_id,
            subject=request.subject,
            topic=request.topic,
            grade_level=request.grade_level,
            learning_objectives=request.learning_objectives,
            duration=request.duration,
        )

        # Log task queued
        log_audit(
            action="lesson_generation_queued",
            user_id=current_user.id,
            resource_type="lesson",
            resource_id=request.lesson_id,
            details={
                "task_id": task.id,
                "subject": request.subject,
                "topic": request.topic,
                "organization_id": organization_id,
            },
        )

        logger.info(f"Lesson generation task queued: {task.id} for lesson {request.lesson_id}")

        return JSONResponse(
            content={
                "status": "success",
                "data": {
                    "task_id": task.id,
                    "lesson_id": request.lesson_id,
                    "organization_id": organization_id,
                    "status": "queued",
                    "message": "Lesson generation task started. Use Pusher channel to track progress.",
                    "pusher_channel": f"org-{organization_id}",
                    "pusher_events": [
                        "content-generation-started",
                        "content-generation-progress",
                        "content-generation-completed",
                        "content-generation-failed",
                    ],
                },
                "message": "Lesson generation task queued successfully",
            },
            status_code=202,  # Accepted - processing asynchronously
        )

    except Exception as e:
        logger.error(f"Failed to queue lesson generation task: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to queue lesson generation task: {str(e)}"
        )


@router.post("/api/v1/content/assessments/generate")
async def generate_quiz_questions(
    request: GenerateQuizRequest,
    current_user: User = Depends(require_any_role(["admin", "teacher"])),
) -> JSONResponse:
    """
    Generate quiz questions using Celery background task

    Args:
        request: Quiz generation parameters
        current_user: Authenticated user (admin/teacher only)

    Returns:
        JSONResponse: Task ID and status for tracking progress

    Permissions:
        - admin: Can generate quizzes for any organization
        - teacher: Can generate quizzes for their organization
    """
    try:
        # Import Celery task
        from apps.backend.workers.tasks.content_tasks import (
            generate_quiz_questions_sync,
        )

        # Get organization ID from user context
        organization_id = getattr(current_user, "organization_id", "default_org")

        # Queue the task
        task = generate_quiz_questions_sync.delay(
            assessment_id=request.assessment_id,
            organization_id=organization_id,
            subject=request.subject,
            topic=request.topic,
            grade_level=request.grade_level,
            num_questions=request.num_questions,
            difficulty=request.difficulty,
            question_types=request.question_types,
            learning_objectives=request.learning_objectives,
            lesson_id=request.lesson_id,
        )

        # Log task queued
        log_audit(
            action="quiz_generation_queued",
            user_id=current_user.id,
            resource_type="assessment",
            resource_id=request.assessment_id,
            details={
                "task_id": task.id,
                "subject": request.subject,
                "topic": request.topic,
                "num_questions": request.num_questions,
                "organization_id": organization_id,
            },
        )

        logger.info(
            f"Quiz generation task queued: {task.id} for assessment {request.assessment_id}"
        )

        return JSONResponse(
            content={
                "status": "success",
                "data": {
                    "task_id": task.id,
                    "assessment_id": request.assessment_id,
                    "organization_id": organization_id,
                    "status": "queued",
                    "message": "Quiz generation task started. Use Pusher channel to track progress.",
                    "pusher_channel": f"org-{organization_id}",
                    "pusher_events": [
                        "quiz-generation-started",
                        "quiz-generation-completed",
                        "quiz-generation-failed",
                    ],
                },
                "message": "Quiz generation task queued successfully",
            },
            status_code=202,  # Accepted - processing asynchronously
        )

    except Exception as e:
        logger.error(f"Failed to queue quiz generation task: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to queue quiz generation task: {str(e)}"
        )


@router.post("/api/v1/roblox/optimize-script")
async def optimize_roblox_script(
    request: OptimizeScriptRequest,
    current_user: User = Depends(require_any_role(["admin", "teacher"])),
) -> JSONResponse:
    """
    Optimize Roblox Luau script using Celery background task

    Args:
        request: Script optimization parameters
        current_user: Authenticated user (admin/teacher only)

    Returns:
        JSONResponse: Task ID and status for tracking progress

    Permissions:
        - admin: Can optimize scripts for any organization
        - teacher: Can optimize scripts for their organization
    """
    try:
        # Import Celery task
        from apps.backend.workers.tasks.roblox_tasks import optimize_roblox_script_sync

        # Get organization ID from user context
        organization_id = getattr(current_user, "organization_id", "default_org")

        # Validate optimization level
        valid_levels = ["conservative", "balanced", "aggressive"]
        if request.optimization_level not in valid_levels:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid optimization level. Must be one of: {', '.join(valid_levels)}",
            )

        # Queue the task
        task = optimize_roblox_script_sync.delay(
            script_id=request.script_id,
            organization_id=organization_id,
            script_code=request.script_code,
            script_name=request.script_name,
            optimization_level=request.optimization_level,
            preserve_comments=request.preserve_comments,
            generate_report=request.generate_report,
        )

        # Log task queued
        log_audit(
            action="script_optimization_queued",
            user_id=current_user.id,
            resource_type="roblox_script",
            resource_id=request.script_id,
            details={
                "task_id": task.id,
                "script_name": request.script_name,
                "optimization_level": request.optimization_level,
                "organization_id": organization_id,
            },
        )

        logger.info(f"Script optimization task queued: {task.id} for script {request.script_id}")

        return JSONResponse(
            content={
                "status": "success",
                "data": {
                    "task_id": task.id,
                    "script_id": request.script_id,
                    "organization_id": organization_id,
                    "status": "queued",
                    "message": "Script optimization task started. Use Pusher channel to track progress.",
                    "pusher_channel": f"org-{organization_id}",
                    "pusher_events": [
                        "script-optimization-started",
                        "script-optimization-progress",
                        "script-optimization-completed",
                        "script-optimization-failed",
                    ],
                },
                "message": "Script optimization task queued successfully",
            },
            status_code=202,  # Accepted - processing asynchronously
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to queue script optimization task: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to queue script optimization task: {str(e)}"
        )

"""
Content Generation Router

Handles content generation, retrieval, and management endpoints.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from fastapi.responses import JSONResponse, StreamingResponse

from apps.backend.core.logging import logging_manager, log_execution_time, log_audit
from apps.backend.core.config import settings
from apps.backend.models.schemas import (
    ContentRequest,
    ContentResponse,
    BaseResponse,
    ErrorResponse,
    User
)
from apps.backend.api.auth.auth import get_current_user, require_any_role

logger = logging_manager.get_logger(__name__)

router = APIRouter(tags=["Content Generation"])


@router.post("/api/v1/content/generate", response_model=ContentResponse)
async def generate_content(
    content_request: ContentRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(get_current_user)
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
            "content_type": getattr(content_request, 'content_type', 'general')
        }
    )

    try:
        # Import content generation function
        from apps.backend.agents.agent import generate_educational_content

        # Generate content using agents
        result = await generate_educational_content(
            topic=content_request.topic,
            subject=getattr(content_request, 'subject', None),
            grade_level=getattr(content_request, 'grade_level', None),
            content_type=getattr(content_request, 'content_type', 'lesson'),
            user_id=current_user.id
        )

        # Log successful generation
        log_execution_time("content_generation", start_time)
        log_audit(
            action="content_generated",
            user_id=current_user.id,
            resource_type="educational_content",
            resource_id=request_id,
            details={
                "topic": content_request.topic,
                "result_length": len(str(result))
            }
        )

        # Broadcast update via Pusher
        background_tasks.add_task(
            _broadcast_content_update,
            user_id=current_user.id,
            content_id=request_id,
            status="completed",
            result=result
        )

        return ContentResponse(
            status="success",
            content=result,
            metadata={
                "request_id": request_id,
                "generation_time": (datetime.now() - start_time).total_seconds(),
                "agent_used": "educational_content_agent",
                "user_id": current_user.id
            }
        )

    except Exception as e:
        logger.error(
            f"Content generation failed: {e}",
            extra_fields={
                "request_id": request_id,
                "user_id": current_user.id,
                "error": str(e)
            }
        )

        # Broadcast error via Pusher
        background_tasks.add_task(
            _broadcast_content_update,
            user_id=current_user.id,
            content_id=request_id,
            status="failed",
            error=str(e)
        )

        raise HTTPException(
            status_code=500,
            detail=f"Content generation failed: {str(e)}"
        )


@router.get("/content/{content_id}")
async def get_content(
    content_id: str,
    current_user: User = Depends(get_current_user)
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
            "user_id": current_user.id
        }

        log_audit(
            action="content_retrieved",
            user_id=current_user.id,
            resource_type="educational_content",
            resource_id=content_id
        )

        return JSONResponse(content={
            "status": "success",
            "data": content_data,
            "message": "Content retrieved successfully"
        })

    except Exception as e:
        logger.error(f"Failed to retrieve content {content_id}: {e}")
        raise HTTPException(
            status_code=404,
            detail=f"Content not found: {content_id}"
        )


@router.get("/content/{content_id}/stream")
async def stream_content_generation(
    content_id: str,
    current_user: User = Depends(get_current_user)
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
                "Content generation completed!"
            ]

            for i, stage in enumerate(stages):
                progress = (i + 1) / len(stages) * 100
                data = {
                    "content_id": content_id,
                    "stage": stage,
                    "progress": progress,
                    "timestamp": datetime.now(timezone.utc).isoformat()
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
                "Content-Encoding": "identity"
            }
        )

    except Exception as e:
        logger.error(f"Failed to stream content generation {content_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stream content generation: {str(e)}"
        )


@router.delete("/content/{content_id}")
async def delete_content(
    content_id: str,
    current_user: User = Depends(require_any_role(["admin", "teacher"]))
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
            resource_id=content_id
        )

        return JSONResponse(content={
            "status": "success",
            "data": {"content_id": content_id, "deleted": True},
            "message": "Content deleted successfully"
        })

    except Exception as e:
        logger.error(f"Failed to delete content {content_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete content: {str(e)}"
        )


@router.get("/content/user/{user_id}")
async def get_user_content(
    user_id: str,
    current_user: User = Depends(get_current_user),
    limit: int = 10,
    offset: int = 0
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
                status_code=403,
                detail="Insufficient permissions to access user content"
            )

        # For now, return placeholder data
        # In a full implementation, this would query the database
        content_list = [
            {
                "id": f"content_{i}",
                "topic": f"Sample Topic {i}",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "completed"
            }
            for i in range(offset, offset + limit)
        ]

        return JSONResponse(content={
            "status": "success",
            "data": {
                "content": content_list,
                "total": 50,  # Placeholder total
                "limit": limit,
                "offset": offset
            },
            "message": "User content retrieved successfully"
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user content for {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve user content: {str(e)}"
        )


async def _broadcast_content_update(
    user_id: str,
    content_id: str,
    status: str,
    result: Optional[str] = None,
    error: Optional[str] = None
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
            user_id=user_id,
            content_id=content_id,
            status=status,
            result=result,
            error=error
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
    user_role = getattr(user, 'role', None)
    return user_role in required_roles if user_role else False
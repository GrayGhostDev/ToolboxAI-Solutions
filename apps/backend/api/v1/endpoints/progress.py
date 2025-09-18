"""
Progress Tracking API Endpoints

This module provides endpoints for tracking user progress and achievements.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from apps.backend.core.deps import get_db, get_current_user
from database.models import User

router = APIRouter(
    prefix="/progress",
    tags=["progress"],
    responses={404: {"description": "Not found"}},
)


# Pydantic models for request/response
class ProgressItem(BaseModel):
    """Model for a progress item"""
    item_id: str = Field(..., description="Unique identifier for the progress item")
    item_type: str = Field(..., description="Type of progress item (lesson, assessment, etc.)")
    status: str = Field("pending", description="Status of the progress item")
    percentage: float = Field(0.0, ge=0.0, le=100.0, description="Completion percentage")
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class UserProgress(BaseModel):
    """Model for user progress overview"""
    user_id: int
    total_items: int = 0
    completed_items: int = 0
    in_progress_items: int = 0
    overall_percentage: float = 0.0
    last_activity: Optional[datetime] = None
    items: List[ProgressItem] = []


class UpdateProgressRequest(BaseModel):
    """Request model for updating progress"""
    item_id: str
    item_type: str
    status: str = Field(..., description="Status: pending, in_progress, completed")
    percentage: float = Field(..., ge=0.0, le=100.0)
    metadata: Optional[dict] = None


class ProgressResponse(BaseModel):
    """Response model for progress operations"""
    success: bool
    message: str
    data: Optional[ProgressItem] = None


class UserProgressResponse(BaseModel):
    """Response model for user progress"""
    success: bool
    data: UserProgress


# In-memory storage for demonstration (replace with database)
progress_storage = {}


@router.get("/", response_model=UserProgressResponse)
async def get_user_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's progress overview"""
    user_id = current_user.id

    # Get or create user progress
    if user_id not in progress_storage:
        progress_storage[user_id] = {
            "items": {},
            "last_activity": None
        }

    user_data = progress_storage[user_id]
    items = list(user_data["items"].values())

    # Calculate statistics
    total_items = len(items)
    completed_items = sum(1 for item in items if item.get("status") == "completed")
    in_progress_items = sum(1 for item in items if item.get("status") == "in_progress")

    overall_percentage = 0.0
    if total_items > 0:
        overall_percentage = (completed_items / total_items) * 100.0

    progress = UserProgress(
        user_id=user_id,
        total_items=total_items,
        completed_items=completed_items,
        in_progress_items=in_progress_items,
        overall_percentage=overall_percentage,
        last_activity=user_data["last_activity"],
        items=[ProgressItem(**item) for item in items]
    )

    return UserProgressResponse(
        success=True,
        data=progress
    )


@router.get("/{item_id}", response_model=ProgressResponse)
async def get_item_progress(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get progress for a specific item"""
    user_id = current_user.id

    if user_id not in progress_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No progress data found for user"
        )

    items = progress_storage[user_id]["items"]

    if item_id not in items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Progress item {item_id} not found"
        )

    return ProgressResponse(
        success=True,
        message="Progress item retrieved successfully",
        data=ProgressItem(**items[item_id])
    )


@router.post("/update", response_model=ProgressResponse)
async def update_progress(
    request: UpdateProgressRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update progress for an item"""
    user_id = current_user.id

    # Initialize user progress if not exists
    if user_id not in progress_storage:
        progress_storage[user_id] = {
            "items": {},
            "last_activity": None
        }

    user_data = progress_storage[user_id]

    # Get or create item
    if request.item_id not in user_data["items"]:
        user_data["items"][request.item_id] = {
            "item_id": request.item_id,
            "item_type": request.item_type,
            "status": "pending",
            "percentage": 0.0,
            "started_at": None,
            "completed_at": None,
            "metadata": {}
        }

    item = user_data["items"][request.item_id]

    # Update item
    old_status = item["status"]
    item["status"] = request.status
    item["percentage"] = request.percentage

    # Update timestamps
    now = datetime.utcnow()
    if old_status == "pending" and request.status == "in_progress":
        item["started_at"] = now
    elif request.status == "completed":
        item["completed_at"] = now
        item["percentage"] = 100.0

    # Update metadata if provided
    if request.metadata:
        item["metadata"].update(request.metadata)

    # Update last activity
    user_data["last_activity"] = now

    return ProgressResponse(
        success=True,
        message=f"Progress updated for item {request.item_id}",
        data=ProgressItem(**item)
    )


@router.delete("/{item_id}", response_model=ProgressResponse)
async def reset_item_progress(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reset progress for a specific item"""
    user_id = current_user.id

    if user_id not in progress_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No progress data found for user"
        )

    items = progress_storage[user_id]["items"]

    if item_id not in items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Progress item {item_id} not found"
        )

    # Reset the item
    item = items[item_id]
    item["status"] = "pending"
    item["percentage"] = 0.0
    item["started_at"] = None
    item["completed_at"] = None

    progress_storage[user_id]["last_activity"] = datetime.utcnow()

    return ProgressResponse(
        success=True,
        message=f"Progress reset for item {item_id}",
        data=ProgressItem(**item)
    )


@router.delete("/", response_model=ProgressResponse)
async def reset_all_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reset all progress for the current user"""
    user_id = current_user.id

    # Clear user progress
    if user_id in progress_storage:
        del progress_storage[user_id]

    return ProgressResponse(
        success=True,
        message="All progress has been reset",
        data=None
    )


# Export router
__all__ = ["router"]
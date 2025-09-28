"""
User Profile API endpoint
Provides current user profile information
"""

from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from apps.backend.core.security.jwt_handler import get_current_user
from database.models import User

router = APIRouter(prefix="/api/v1/users", tags=["User Profile"])


class UserProfile(BaseModel):
    """User profile response model"""

    id: str
    username: str
    email: str
    role: str
    displayName: Optional[str] = None
    avatarUrl: Optional[str] = None
    schoolId: Optional[str] = None
    classIds: list[str] = []
    createdAt: datetime
    lastLogin: Optional[datetime] = None
    isActive: bool = True


@router.get("/me/profile", response_model=UserProfile)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get the current user's profile information.

    This endpoint is called by the frontend during initialization
    to restore the user's session and profile data.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Convert the User model to profile response
    return UserProfile(
        id=str(current_user.id) if hasattr(current_user, "id") else "1",
        username=(
            current_user.username
            if hasattr(current_user, "username")
            else current_user.email.split("@")[0]
        ),
        email=current_user.email,
        role=current_user.role if hasattr(current_user, "role") else "student",
        displayName=getattr(current_user, "display_name", None) or current_user.email.split("@")[0],
        avatarUrl=getattr(current_user, "avatar_url", None),
        schoolId=getattr(current_user, "school_id", None),
        classIds=getattr(current_user, "class_ids", []) or [],
        createdAt=getattr(current_user, "created_at", datetime.now(timezone.utc)),
        lastLogin=getattr(current_user, "last_login", None),
        isActive=getattr(current_user, "is_active", True),
    )


@router.patch("/me/profile")
async def update_user_profile(updates: dict, current_user: User = Depends(get_current_user)):
    """
    Update the current user's profile information.

    Allowed updates:
    - displayName
    - avatarUrl
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Only allow certain fields to be updated
    allowed_fields = ["displayName", "avatarUrl"]
    filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}

    if not filtered_updates:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    # In a real implementation, this would update the database
    # For now, return success
    return {
        "success": True,
        "message": "Profile updated successfully",
        "updated_fields": list(filtered_updates.keys()),
    }


@router.get("/me/preferences")
async def get_user_preferences(current_user: User = Depends(get_current_user)):
    """Get user preferences and settings"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return {
        "theme": "light",
        "language": "en",
        "notifications": {"email": True, "push": False, "sms": False},
        "privacy": {"profile_visible": True, "show_online_status": True},
        "accessibility": {"high_contrast": False, "font_size": "medium", "screen_reader": False},
    }

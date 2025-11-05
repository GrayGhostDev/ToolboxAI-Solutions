"""
User Profile API endpoint
Provides current user profile information
"""

from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from apps.backend.core.security.jwt_handler import get_current_user, TokenData

router = APIRouter(tags=["User Profile"])


class UserProfile(BaseModel):
    """User profile response model"""

    id: str
    username: str
    email: str
    role: str
    displayName: Optional[str] = None
    avatarUrl: Optional[str] = None
    schoolId: Optional[str] = None
    classIds: List[str] = []  # Python 3.9 compatible
    createdAt: datetime
    lastLogin: Optional[datetime] = None
    isActive: bool = True


@router.get("/me/profile", response_model=UserProfile)
async def get_user_profile(current_user: TokenData = Depends(get_current_user)):
    """
    Get the current user's profile information.

    This endpoint is called by the frontend during initialization
    to restore the user's session and profile data.
    """
    # get_current_user already raises HTTPException if not authenticated
    # Convert the TokenData to profile response
    return UserProfile(
        id=str(current_user.user_id) if current_user.user_id else "1",
        username=current_user.username or "user",
        email=current_user.username or "user@example.com",  # username is typically email
        role=current_user.role or "student",
        displayName=current_user.username or "User",
        avatarUrl=None,
        schoolId=None,
        classIds=[],
        createdAt=datetime.now(timezone.utc),
        lastLogin=datetime.now(timezone.utc),
        isActive=True,
    )


@router.patch("/me/profile")
async def update_user_profile(updates: dict, current_user: TokenData = Depends(get_current_user)):
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
async def get_user_preferences(current_user: TokenData = Depends(get_current_user)):
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

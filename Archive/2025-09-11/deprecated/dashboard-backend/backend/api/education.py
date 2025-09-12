"""
Educational Platform API Endpoints
Integrates with Ghost Backend Framework
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
import sys
import os

from .simple_ghost import APIResponse, AuthManager

# Import local education manager
from .education_manager import EducationalAPIManager as APIManager

# Create router
router = APIRouter(prefix="/api/v1", tags=["education"])
security = HTTPBearer()

# ==================== Pydantic Models ====================

class UserRole(BaseModel):
    role: str = Field(..., pattern="^(Admin|Teacher|Student|Parent)$")

class LessonCreate(BaseModel):
    title: str
    description: str
    subject: str
    status: str = "draft"
    classIds: List[str] = []
    content: Dict[str, Any] = {}

class AssessmentCreate(BaseModel):
    title: str
    lessonId: Optional[str] = None
    classId: str
    type: str = Field(..., pattern="^(quiz|test|assignment|project)$")
    questions: List[Dict[str, Any]]
    dueDate: Optional[datetime] = None
    maxSubmissions: int = 1

class XPTransaction(BaseModel):
    studentId: str
    amount: int
    reason: str
    source: str = Field(..., pattern="^(lesson|assessment|achievement|bonus)$")

class MessageCreate(BaseModel):
    toUserId: str
    subject: str
    content: str
    attachments: List[str] = []

class ConsentRequest(BaseModel):
    type: str = Field(..., pattern="^(coppa|ferpa|gdpr)$")
    userId: str

# ==================== Authentication ====================

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return current user"""
    # For development, return mock user
    # TODO: Integrate with Ghost AuthManager when authentication is set up
    return {
        "id": "user123",
        "email": "teacher@school.edu",
        "role": "Teacher",
        "displayName": "Jane Smith"
    }

# ==================== Dashboard Endpoints ====================

@router.get("/dashboard/overview/{role}")
async def get_dashboard_overview(role: str, current_user: dict = Depends(get_current_user)):
    data = APIManager.get_dashboard_overview(role, current_user)
    # Return data directly for frontend compatibility
    return data

# ==================== Lessons Endpoints ====================

@router.get("/lessons")
async def list_lessons(classId: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    lessons = APIManager.get_lessons(classId, current_user)
    return lessons

@router.post("/lessons")
async def create_lesson(lesson: LessonCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["Teacher", "Admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    result = APIManager.create_lesson(lesson.dict(), current_user)
    return result

# ==================== Gamification Endpoints ====================

@router.get("/gamification/xp/{studentId}")
async def get_student_xp(studentId: str, current_user: dict = Depends(get_current_user)):
    xp = APIManager.get_xp(studentId, current_user)
    return xp

@router.post("/gamification/xp/{studentId}")
async def add_xp(studentId: str, transaction: XPTransaction, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["Teacher", "Admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    result = APIManager.add_xp(studentId, transaction.dict(), current_user)
    return result

@router.get("/gamification/badges")
async def get_badges(studentId: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    badges = APIManager.get_badges(studentId, current_user)
    return badges

@router.get("/gamification/leaderboard")
async def get_leaderboard(classId: Optional[str] = None, timeframe: str = "weekly", current_user: dict = Depends(get_current_user)):
    leaderboard = APIManager.get_leaderboard(classId, timeframe, current_user)
    return leaderboard

# ==================== Roblox Integration ====================

@router.post("/roblox/push/{lessonId}")
async def push_lesson_to_roblox(lessonId: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["Teacher", "Admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    result = APIManager.roblox_push_lesson(lessonId, current_user)
    return result

@router.get("/roblox/join/{classId}")
async def get_roblox_join_url(classId: str, current_user: dict = Depends(get_current_user)):
    result = APIManager.roblox_join_class(classId, current_user)
    return result

# ==================== Compliance Endpoints ====================

@router.get("/compliance/status")
async def get_compliance_status(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    status_data = APIManager.get_compliance_status(current_user)
    return status_data

@router.post("/compliance/consent")
async def record_consent(consent_request: ConsentRequest, current_user: dict = Depends(get_current_user)):
    # Map 'type' from frontend to 'consent_type' for backend
    result = APIManager.submit_compliance_consent(consent_request.type, consent_request.userId, current_user)
    return result

# ==================== Analytics Endpoints ====================

@router.get("/analytics/weekly_xp")
async def get_weekly_xp(studentId: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    data = APIManager.get_weekly_xp(studentId, current_user)
    return data

@router.get("/analytics/subject_mastery")
async def get_subject_mastery(studentId: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    data = APIManager.get_subject_mastery(studentId, current_user)
    return data

# ==================== WebSocket Events (Documentation) ====================
"""
WebSocket Events Documentation:

The platform supports real-time updates through WebSocket connections.
Connect to ws://localhost:8001 with authentication token.

Events emitted by server:
- notification: General notifications
- xp_gained: When student gains XP
- badge_earned: When student earns a badge
- leaderboard_update: Leaderboard changes
- class_online: Class goes online
- assignment_due: Assignment deadline reminder
- new_message: New message received
- activity: New activity in class
- event: New calendar event

Events accepted from client:
- join_room: Join a class room for updates
- leave_room: Leave a class room
- request_leaderboard: Request leaderboard update
- heartbeat: Keep connection alive
"""

# Export router for main app
__all__ = ["router"]
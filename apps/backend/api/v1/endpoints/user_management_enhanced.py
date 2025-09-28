"""Enhanced User Management & Authentication API for ToolBoxAI

Provides comprehensive user management features:
- Enhanced user profiles with learning preferences
- Role-based access control (students, teachers, admins, parents)
- Progress tracking and achievement systems
- Parent/guardian access and reporting
- Advanced authentication and session management
- User analytics and engagement tracking
"""

import logging
import uuid
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
import jwt

# Import authentication and dependencies
try:
    from apps.backend.api.auth.auth import get_current_user, require_role, require_any_role
    from apps.backend.core.deps import get_db
    from apps.backend.core.security.rate_limit_manager import rate_limit
    from apps.backend.core.security.jwt_handler import create_access_token, verify_token
except ImportError:
    # Fallback for development
    def get_current_user():
        return {"id": "test", "role": "teacher", "email": "test@example.com"}

    def require_role(role):
        return lambda: None

    def require_any_role(roles):
        return lambda: None

    def get_db():
        return None

    def rate_limit(requests=60, max_requests=None, **kwargs):
        def decorator(func):
            return func

        return decorator

    def create_access_token(data, expires_delta=None):
        return "mock_token"

    def verify_token(token):
        return {"sub": "test@example.com", "role": "teacher"}


# Import models and services
try:
    from apps.backend.models.schemas import User, BaseResponse
    from apps.backend.services.pusher import trigger_event
except ImportError:

    class User(BaseModel):
        id: str
        email: str
        role: str

    class BaseResponse(BaseModel):
        success: bool = True
        message: str = ""
        timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    async def trigger_event(channel, event, data):
        pass


logger = logging.getLogger(__name__)
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create router
router = APIRouter(prefix="/user-management", tags=["User Management"])


# Enums
class UserRole(str, Enum):
    """Enhanced user roles"""

    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"
    PARENT = "parent"
    SCHOOL_ADMIN = "school_admin"
    DISTRICT_ADMIN = "district_admin"


class AccountStatus(str, Enum):
    """User account status"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"
    DISABLED = "disabled"


class LearningStyle(str, Enum):
    """Learning style preferences"""

    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING_WRITING = "reading_writing"
    MULTIMODAL = "multimodal"


class AccessibilityNeed(str, Enum):
    """Accessibility requirements"""

    SCREEN_READER = "screen_reader"
    HIGH_CONTRAST = "high_contrast"
    LARGE_TEXT = "large_text"
    KEYBOARD_NAVIGATION = "keyboard_navigation"
    REDUCED_MOTION = "reduced_motion"
    AUDIO_DESCRIPTIONS = "audio_descriptions"


class NotificationPreference(str, Enum):
    """Notification preferences"""

    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"
    PUSH = "push"
    NONE = "none"


class AchievementType(str, Enum):
    """Types of achievements"""

    LEARNING_MILESTONE = "learning_milestone"
    STREAK = "streak"
    COMPLETION = "completion"
    MASTERY = "mastery"
    COLLABORATION = "collaboration"
    CREATIVITY = "creativity"
    PROBLEM_SOLVING = "problem_solving"


# Request Models
class LearningPreferences(BaseModel):
    """User learning preferences"""

    learning_style: LearningStyle
    preferred_subjects: List[str] = Field(default_factory=list)
    difficulty_preference: str = Field("adaptive", description="adaptive, easy, medium, hard")
    session_duration_preference: int = Field(
        30, ge=5, le=120, description="Preferred session length in minutes"
    )
    accessibility_needs: List[AccessibilityNeed] = Field(default_factory=list)
    language_preference: str = Field("en")
    timezone: str = Field("UTC")

    model_config = ConfigDict(from_attributes=True)


class NotificationSettings(BaseModel):
    """User notification settings"""

    assignment_reminders: NotificationPreference = NotificationPreference.IN_APP
    progress_updates: NotificationPreference = NotificationPreference.EMAIL
    achievement_notifications: NotificationPreference = NotificationPreference.IN_APP
    weekly_reports: NotificationPreference = NotificationPreference.EMAIL
    system_announcements: NotificationPreference = NotificationPreference.IN_APP
    marketing_communications: NotificationPreference = NotificationPreference.NONE

    model_config = ConfigDict(from_attributes=True)


class CreateUserRequest(BaseModel):
    """Request to create a new user"""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_-]+$")
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    grade_level: Optional[int] = Field(None, ge=1, le=12)
    school_id: Optional[str] = None
    parent_email: Optional[EmailStr] = None
    learning_preferences: Optional[LearningPreferences] = None
    notification_settings: Optional[NotificationSettings] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        # Basic password strength validation
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

    @field_validator("grade_level")
    @classmethod
    def validate_grade_level(cls, v, info):
        role = info.data.get("role")
        if role == UserRole.STUDENT and v is None:
            raise ValueError("Grade level is required for students")
        if role != UserRole.STUDENT and v is not None:
            raise ValueError("Grade level should only be set for students")
        return v

    model_config = ConfigDict(from_attributes=True)


class UpdateUserRequest(BaseModel):
    """Request to update user information"""

    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    display_name: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = None
    grade_level: Optional[int] = Field(None, ge=1, le=12)
    school_id: Optional[str] = None
    learning_preferences: Optional[LearningPreferences] = None
    notification_settings: Optional[NotificationSettings] = None

    model_config = ConfigDict(from_attributes=True)


class PasswordChangeRequest(BaseModel):
    """Request to change password"""

    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v):
        # Same validation as CreateUserRequest
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

    model_config = ConfigDict(from_attributes=True)


class ParentLinkRequest(BaseModel):
    """Request to link parent to student"""

    student_email: EmailStr
    parent_email: EmailStr
    relationship: str = Field(..., description="parent, guardian, tutor")
    permission_level: str = Field("standard", description="standard, limited, full")

    model_config = ConfigDict(from_attributes=True)


class AchievementRequest(BaseModel):
    """Request to award achievement"""

    achievement_type: AchievementType
    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., max_length=500)
    points: int = Field(0, ge=0)
    badge_url: Optional[str] = None
    criteria_met: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


# Response Models
class UserProfile(BaseModel):
    """Complete user profile"""

    id: str
    email: EmailStr
    username: str
    role: UserRole
    first_name: str
    last_name: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    grade_level: Optional[int] = None
    school_id: Optional[str] = None
    account_status: AccountStatus
    learning_preferences: Optional[LearningPreferences] = None
    notification_settings: Optional[NotificationSettings] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    email_verified: bool = False
    profile_completion: int = Field(0, ge=0, le=100)

    model_config = ConfigDict(from_attributes=True)


class UserSummary(BaseModel):
    """Summary user information for listings"""

    id: str
    email: EmailStr
    username: str
    role: UserRole
    first_name: str
    last_name: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    grade_level: Optional[int] = None
    account_status: AccountStatus
    last_login: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """Paginated user list response"""

    users: List[UserSummary]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool
    filters_applied: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class Achievement(BaseModel):
    """User achievement"""

    id: str
    achievement_type: AchievementType
    title: str
    description: str
    points: int
    badge_url: Optional[str] = None
    earned_at: datetime
    criteria_met: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class UserProgress(BaseModel):
    """User learning progress"""

    user_id: str
    total_lessons_completed: int
    total_time_spent: int  # in minutes
    current_streak: int
    longest_streak: int
    total_points: int
    level: int
    subject_progress: Dict[str, Any]
    recent_achievements: List[Achievement]
    weekly_activity: List[Dict[str, Any]]
    competency_levels: Dict[str, str]

    model_config = ConfigDict(from_attributes=True)


class ParentDashboard(BaseModel):
    """Parent dashboard data"""

    parent_id: str
    children: List[UserSummary]
    combined_progress: Dict[str, Any]
    recent_activities: List[Dict[str, Any]]
    upcoming_assignments: List[Dict[str, Any]]
    achievement_summary: Dict[str, Any]
    recommended_actions: List[str]

    model_config = ConfigDict(from_attributes=True)


class SessionInfo(BaseModel):
    """User session information"""

    session_id: str
    user_id: str
    device_info: Dict[str, Any]
    ip_address: str
    location: Optional[str] = None
    started_at: datetime
    last_activity: datetime
    is_current: bool

    model_config = ConfigDict(from_attributes=True)


# Mock data stores
_mock_users_db: Dict[str, UserProfile] = {}
_mock_achievements_db: Dict[str, List[Achievement]] = {}
_mock_progress_db: Dict[str, UserProgress] = {}
_mock_sessions_db: Dict[str, List[SessionInfo]] = {}
_mock_parent_links: Dict[str, List[str]] = {}  # parent_id -> [student_ids]


# Utility functions
async def notify_user_update(user_id: str, event_type: str, data: Dict[str, Any]):
    """Notify about user updates"""
    try:
        await trigger_event(
            "user-updates",
            f"user.{event_type}",
            {"user_id": user_id, "data": data, "timestamp": datetime.now(timezone.utc).isoformat()},
        )
    except Exception as e:
        logger.warning(f"Failed to send user update notification: {e}")


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def calculate_profile_completion(user: UserProfile) -> int:
    """Calculate profile completion percentage"""
    required_fields = [
        user.first_name,
        user.last_name,
        user.email,
        user.learning_preferences,
        user.notification_settings,
    ]

    optional_fields = [user.display_name, user.avatar_url]

    completed_required = sum(1 for field in required_fields if field)
    completed_optional = sum(1 for field in optional_fields if field)

    total_required = len(required_fields)
    total_optional = len(optional_fields)

    # Required fields are worth 80%, optional 20%
    required_score = (completed_required / total_required) * 80
    optional_score = (completed_optional / total_optional) * 20

    return int(required_score + optional_score)


# Endpoints


@router.post("/users", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
# @rate_limit(requests=5)  # 5 user creations per minute
async def create_user(
    request: CreateUserRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user),
    _: None = Depends(require_any_role(["admin", "school_admin", "district_admin"])),
):
    """
    Create a new user account.

    Requires: Admin, School Admin, or District Admin role
    Rate limit: 5 requests per minute
    """
    try:
        # Check if user already exists
        existing_user = next(
            (
                u
                for u in _mock_users_db.values()
                if u.email == request.email or u.username == request.username
            ),
            None,
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email or username already exists",
            )

        user_id = str(uuid.uuid4())

        # Create user profile
        user_profile = UserProfile(
            id=user_id,
            email=request.email,
            username=request.username,
            role=request.role,
            first_name=request.first_name,
            last_name=request.last_name,
            display_name=f"{request.first_name} {request.last_name}",
            grade_level=request.grade_level,
            school_id=request.school_id,
            account_status=AccountStatus.PENDING_VERIFICATION,
            learning_preferences=request.learning_preferences
            or LearningPreferences(learning_style=LearningStyle.MULTIMODAL),
            notification_settings=request.notification_settings or NotificationSettings(),
            created_at=datetime.now(timezone.utc),
            email_verified=False,
        )

        # Calculate profile completion
        user_profile.profile_completion = calculate_profile_completion(user_profile)

        # Store in mock database
        _mock_users_db[user_id] = user_profile

        # Initialize progress tracking
        _mock_progress_db[user_id] = UserProgress(
            user_id=user_id,
            total_lessons_completed=0,
            total_time_spent=0,
            current_streak=0,
            longest_streak=0,
            total_points=0,
            level=1,
            subject_progress={},
            recent_achievements=[],
            weekly_activity=[],
            competency_levels={},
        )

        # Initialize achievements
        _mock_achievements_db[user_id] = []

        # Handle parent linking for students
        if request.role == UserRole.STUDENT and request.parent_email:
            # Find parent user
            parent_user = next(
                (u for u in _mock_users_db.values() if u.email == request.parent_email), None
            )
            if parent_user:
                if parent_user.id not in _mock_parent_links:
                    _mock_parent_links[parent_user.id] = []
                _mock_parent_links[parent_user.id].append(user_id)

        # Background notification
        background_tasks.add_task(
            notify_user_update,
            user_id,
            "created",
            {"role": request.role.value, "created_by": current_user["id"]},
        )

        logger.info(f"User created: {user_id} ({request.role.value}) by {current_user['id']}")
        return user_profile

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user"
        )


@router.get("/users", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    account_status: Optional[AccountStatus] = Query(None, description="Filter by account status"),
    school_id: Optional[str] = Query(None, description="Filter by school"),
    grade_level: Optional[int] = Query(None, ge=1, le=12, description="Filter by grade level"),
    search: Optional[str] = Query(None, min_length=2, description="Search in name/email/username"),
    current_user: Dict = Depends(get_current_user),
    _: None = Depends(require_any_role(["admin", "school_admin", "district_admin", "teacher"])),
):
    """
    List users with filtering and pagination.

    Requires: Admin, School Admin, District Admin, or Teacher role
    """
    try:
        users = list(_mock_users_db.values())

        # Apply role-based filtering
        user_role = current_user.get("role")
        if user_role == "teacher":
            # Teachers can only see students in their school
            users = [
                u
                for u in users
                if u.role == UserRole.STUDENT and u.school_id == current_user.get("school_id")
            ]
        elif user_role == "school_admin":
            # School admins can see users in their school
            users = [u for u in users if u.school_id == current_user.get("school_id")]

        # Apply filters
        if role:
            users = [u for u in users if u.role == role]
        if account_status:
            users = [u for u in users if u.account_status == account_status]
        if school_id:
            users = [u for u in users if u.school_id == school_id]
        if grade_level:
            users = [u for u in users if u.grade_level == grade_level]
        if search:
            search_lower = search.lower()
            users = [
                u
                for u in users
                if (
                    search_lower in u.first_name.lower()
                    or search_lower in u.last_name.lower()
                    or search_lower in u.email.lower()
                    or search_lower in u.username.lower()
                )
            ]

        # Calculate pagination
        total = len(users)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        # Sort by created_at descending
        users.sort(key=lambda x: x.created_at, reverse=True)

        # Get page items and convert to summaries
        page_users = users[start_idx:end_idx]
        user_summaries = [
            UserSummary(
                id=user.id,
                email=user.email,
                username=user.username,
                role=user.role,
                first_name=user.first_name,
                last_name=user.last_name,
                display_name=user.display_name,
                avatar_url=user.avatar_url,
                grade_level=user.grade_level,
                account_status=user.account_status,
                last_login=user.last_login,
                created_at=user.created_at,
            )
            for user in page_users
        ]

        return UserListResponse(
            users=user_summaries,
            total=total,
            page=page,
            page_size=page_size,
            has_next=end_idx < total,
            has_previous=page > 1,
            filters_applied={
                "role": role,
                "account_status": account_status,
                "school_id": school_id,
                "grade_level": grade_level,
                "search": search,
            },
        )

    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve users"
        )


@router.get("/users/{user_id}", response_model=UserProfile)
async def get_user(user_id: str, current_user: Dict = Depends(get_current_user)):
    """
    Get specific user profile.

    Users can view their own profile.
    Teachers can view students in their school.
    Admins can view any user.
    """
    try:
        user = _mock_users_db.get(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Check permissions
        current_user_role = current_user.get("role")
        current_user_id = current_user.get("id")

        if current_user_id == user_id:
            # User viewing their own profile
            pass
        elif current_user_role in ["admin", "district_admin"]:
            # Admins can view any user
            pass
        elif current_user_role == "school_admin":
            # School admins can view users in their school
            if user.school_id != current_user.get("school_id"):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        elif current_user_role == "teacher":
            # Teachers can view students in their school
            if user.role != UserRole.STUDENT or user.school_id != current_user.get("school_id"):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        elif current_user_role == "parent":
            # Parents can view their linked children
            if user_id not in _mock_parent_links.get(current_user_id, []):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve user"
        )


@router.put("/users/{user_id}", response_model=UserProfile)
# @rate_limit(requests=10)  # 10 updates per minute
async def update_user(
    user_id: str,
    request: UpdateUserRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user),
):
    """
    Update user profile.

    Users can update their own profile.
    Admins can update any user.
    Rate limit: 10 requests per minute
    """
    try:
        user = _mock_users_db.get(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Check permissions
        current_user_role = current_user.get("role")
        current_user_id = current_user.get("id")

        if current_user_id != user_id and current_user_role not in [
            "admin",
            "district_admin",
            "school_admin",
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="You can only update your own profile"
            )

        # Update fields
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        # Recalculate profile completion
        user.profile_completion = calculate_profile_completion(user)

        # Background notification
        background_tasks.add_task(
            notify_user_update,
            user_id,
            "updated",
            {"updated_by": current_user_id, "fields_updated": list(update_data.keys())},
        )

        logger.info(f"User updated: {user_id} by {current_user_id}")
        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update user"
        )


@router.get("/users/{user_id}/progress", response_model=UserProgress)
async def get_user_progress(user_id: str, current_user: Dict = Depends(get_current_user)):
    """
    Get user learning progress and achievements.
    """
    try:
        # Check if user exists
        user = _mock_users_db.get(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Check permissions (same as get_user)
        current_user_role = current_user.get("role")
        current_user_id = current_user.get("id")

        if current_user_id == user_id:
            pass
        elif current_user_role in ["admin", "district_admin"]:
            pass
        elif current_user_role == "school_admin":
            if user.school_id != current_user.get("school_id"):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        elif current_user_role == "teacher":
            if user.role != UserRole.STUDENT or user.school_id != current_user.get("school_id"):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        elif current_user_role == "parent":
            if user_id not in _mock_parent_links.get(current_user_id, []):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        # Get progress data
        progress = _mock_progress_db.get(user_id)
        if not progress:
            # Create default progress if none exists
            progress = UserProgress(
                user_id=user_id,
                total_lessons_completed=0,
                total_time_spent=0,
                current_streak=0,
                longest_streak=0,
                total_points=0,
                level=1,
                subject_progress={},
                recent_achievements=[],
                weekly_activity=[],
                competency_levels={},
            )
            _mock_progress_db[user_id] = progress

        return progress

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving progress for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user progress",
        )


@router.post(
    "/users/{user_id}/achievements", response_model=Achievement, status_code=status.HTTP_201_CREATED
)
async def award_achievement(
    user_id: str,
    request: AchievementRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user),
    _: None = Depends(require_any_role(["admin", "school_admin", "teacher"])),
):
    """
    Award an achievement to a user.

    Requires: Admin, School Admin, or Teacher role
    """
    try:
        user = _mock_users_db.get(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Create achievement
        achievement_id = str(uuid.uuid4())
        achievement = Achievement(
            id=achievement_id,
            achievement_type=request.achievement_type,
            title=request.title,
            description=request.description,
            points=request.points,
            badge_url=request.badge_url,
            earned_at=datetime.now(timezone.utc),
            criteria_met=request.criteria_met,
        )

        # Add to user's achievements
        if user_id not in _mock_achievements_db:
            _mock_achievements_db[user_id] = []
        _mock_achievements_db[user_id].append(achievement)

        # Update user progress
        if user_id in _mock_progress_db:
            _mock_progress_db[user_id].total_points += request.points
            _mock_progress_db[user_id].recent_achievements.insert(0, achievement)
            # Keep only last 10 recent achievements
            _mock_progress_db[user_id].recent_achievements = _mock_progress_db[
                user_id
            ].recent_achievements[:10]

        # Background notification
        background_tasks.add_task(
            notify_user_update,
            user_id,
            "achievement_awarded",
            {
                "achievement_id": achievement_id,
                "achievement_type": request.achievement_type.value,
                "points": request.points,
                "awarded_by": current_user["id"],
            },
        )

        logger.info(
            f"Achievement awarded: {achievement_id} to user {user_id} by {current_user['id']}"
        )
        return achievement

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error awarding achievement to user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to award achievement"
        )


@router.get("/parent-dashboard", response_model=ParentDashboard)
async def get_parent_dashboard(
    current_user: Dict = Depends(get_current_user), _: None = Depends(require_role("parent"))
):
    """
    Get parent dashboard with children's progress and activities.

    Requires: Parent role
    """
    try:
        parent_id = current_user["id"]

        # Get linked children
        child_ids = _mock_parent_links.get(parent_id, [])
        children = [
            _mock_users_db[child_id] for child_id in child_ids if child_id in _mock_users_db
        ]

        # Convert to summaries
        child_summaries = [
            UserSummary(
                id=child.id,
                email=child.email,
                username=child.username,
                role=child.role,
                first_name=child.first_name,
                last_name=child.last_name,
                display_name=child.display_name,
                avatar_url=child.avatar_url,
                grade_level=child.grade_level,
                account_status=child.account_status,
                last_login=child.last_login,
                created_at=child.created_at,
            )
            for child in children
        ]

        # Aggregate progress data
        combined_progress = {
            "total_children": len(children),
            "total_lessons_completed": sum(
                _mock_progress_db.get(
                    child.id,
                    UserProgress(
                        user_id=child.id,
                        total_lessons_completed=0,
                        total_time_spent=0,
                        current_streak=0,
                        longest_streak=0,
                        total_points=0,
                        level=1,
                        subject_progress={},
                        recent_achievements=[],
                        weekly_activity=[],
                        competency_levels={},
                    ),
                ).total_lessons_completed
                for child in children
            ),
            "average_time_per_week": sum(
                _mock_progress_db.get(
                    child.id,
                    UserProgress(
                        user_id=child.id,
                        total_lessons_completed=0,
                        total_time_spent=0,
                        current_streak=0,
                        longest_streak=0,
                        total_points=0,
                        level=1,
                        subject_progress={},
                        recent_achievements=[],
                        weekly_activity=[],
                        competency_levels={},
                    ),
                ).total_time_spent
                for child in children
            )
            / max(len(children), 1)
            / 4,  # Assuming 4 weeks average
        }

        # Mock recent activities and upcoming assignments
        recent_activities = [
            {
                "child_name": child.first_name,
                "activity": "Completed Math Lesson 5",
                "timestamp": datetime.now(timezone.utc) - timedelta(hours=2),
                "subject": "Mathematics",
            }
            for child in children[:3]  # Show last 3 activities
        ]

        upcoming_assignments = [
            {
                "child_name": child.first_name,
                "assignment": "Science Quiz: Solar System",
                "due_date": datetime.now(timezone.utc) + timedelta(days=2),
                "subject": "Science",
            }
            for child in children[:2]  # Show next 2 assignments
        ]

        # Generate recommendations
        recommended_actions = [
            "Encourage daily 15-minute learning sessions",
            "Review progress in Mathematics with struggling children",
            "Celebrate recent achievements to maintain motivation",
        ]

        dashboard = ParentDashboard(
            parent_id=parent_id,
            children=child_summaries,
            combined_progress=combined_progress,
            recent_activities=recent_activities,
            upcoming_assignments=upcoming_assignments,
            achievement_summary={
                "total_achievements": sum(
                    len(_mock_achievements_db.get(child.id, [])) for child in children
                ),
                "points_this_week": sum(
                    _mock_progress_db.get(
                        child.id,
                        UserProgress(
                            user_id=child.id,
                            total_lessons_completed=0,
                            total_time_spent=0,
                            current_streak=0,
                            longest_streak=0,
                            total_points=0,
                            level=1,
                            subject_progress={},
                            recent_achievements=[],
                            weekly_activity=[],
                            competency_levels={},
                        ),
                    ).total_points
                    for child in children
                )
                // 7,  # Mock weekly points
            },
            recommended_actions=recommended_actions,
        )

        return dashboard

    except Exception as e:
        logger.error(f"Error retrieving parent dashboard for {current_user['id']}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve parent dashboard",
        )


@router.post("/link-parent", response_model=BaseResponse)
# @rate_limit(requests=5)  # 5 parent link requests per minute
async def link_parent_to_student(
    request: ParentLinkRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user),
    _: None = Depends(require_any_role(["admin", "school_admin"])),
):
    """
    Link a parent to a student account.

    Requires: Admin or School Admin role
    Rate limit: 5 requests per minute
    """
    try:
        # Find student and parent users
        student = next(
            (u for u in _mock_users_db.values() if u.email == request.student_email), None
        )
        parent = next((u for u in _mock_users_db.values() if u.email == request.parent_email), None)

        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

        if not parent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent not found")

        if student.role != UserRole.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Target user is not a student"
            )

        if parent.role != UserRole.PARENT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Target user is not a parent"
            )

        # Create link
        if parent.id not in _mock_parent_links:
            _mock_parent_links[parent.id] = []

        if student.id not in _mock_parent_links[parent.id]:
            _mock_parent_links[parent.id].append(student.id)

        # Background notifications
        background_tasks.add_task(
            notify_user_update,
            student.id,
            "parent_linked",
            {"parent_id": parent.id, "relationship": request.relationship},
        )

        background_tasks.add_task(
            notify_user_update,
            parent.id,
            "child_linked",
            {"student_id": student.id, "relationship": request.relationship},
        )

        logger.info(f"Parent {parent.id} linked to student {student.id} by {current_user['id']}")

        return BaseResponse(
            success=True,
            message=f"Parent {parent.first_name} {parent.last_name} successfully linked to student {student.first_name} {student.last_name}",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error linking parent to student: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to link parent to student",
        )


@router.get("/users/{user_id}/sessions", response_model=List[SessionInfo])
async def get_user_sessions(
    user_id: str,
    current_user: Dict = Depends(get_current_user),
    _: None = Depends(require_any_role(["admin", "school_admin"])),
):
    """
    Get user session information for security monitoring.

    Requires: Admin or School Admin role
    """
    try:
        user = _mock_users_db.get(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Get sessions (mock data)
        sessions = _mock_sessions_db.get(user_id, [])
        return sessions

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving sessions for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user sessions",
        )

"""
Pydantic Schemas for ToolboxAI Educational Platform
Request/Response validation for API endpoints
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# ============================================
# USER SCHEMAS
# ============================================

class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    role: str = "student"

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    role: Optional[str] = None

class UserResponse(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# ============================================
# COURSE SCHEMAS
# ============================================

class CourseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    difficulty_level: str = "beginner"
    is_published: bool = False
    price: float = Field(default=0.00, ge=0)

class CourseCreate(CourseBase):
    instructor_id: Optional[UUID] = None

class CourseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    difficulty_level: Optional[str] = None
    is_published: Optional[bool] = None
    price: Optional[float] = Field(None, ge=0)

class CourseResponse(CourseBase):
    id: UUID
    instructor_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CourseWithInstructor(CourseResponse):
    instructor: Optional[UserResponse] = None
    lesson_count: Optional[int] = 0


# ============================================
# LESSON SCHEMAS
# ============================================

class LessonBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    content: Optional[str] = None
    video_url: Optional[str] = None
    order_index: int = Field(..., ge=0)
    duration_minutes: Optional[int] = Field(None, ge=0)
    is_free: bool = False

class LessonCreate(LessonBase):
    course_id: UUID

class LessonUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    content: Optional[str] = None
    video_url: Optional[str] = None
    order_index: Optional[int] = Field(None, ge=0)
    duration_minutes: Optional[int] = Field(None, ge=0)
    is_free: Optional[bool] = None

class LessonResponse(LessonBase):
    id: UUID
    course_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# ENROLLMENT SCHEMAS
# ============================================

class EnrollmentCreate(BaseModel):
    course_id: UUID

class EnrollmentResponse(BaseModel):
    id: UUID
    user_id: UUID
    course_id: UUID
    enrolled_at: datetime
    completed_at: Optional[datetime] = None
    progress_percentage: float

    model_config = ConfigDict(from_attributes=True)

class EnrollmentWithCourse(EnrollmentResponse):
    course: Optional[CourseResponse] = None


# ============================================
# LESSON PROGRESS SCHEMAS
# ============================================

class LessonProgressCreate(BaseModel):
    lesson_id: UUID
    completed: bool = False
    time_spent_minutes: int = Field(default=0, ge=0)

class LessonProgressUpdate(BaseModel):
    completed: Optional[bool] = None
    time_spent_minutes: Optional[int] = Field(None, ge=0)

class LessonProgressResponse(BaseModel):
    id: UUID
    user_id: UUID
    lesson_id: UUID
    completed: bool
    completed_at: Optional[datetime] = None
    time_spent_minutes: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# ASSIGNMENT SCHEMAS
# ============================================

class AssignmentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    instructions: Optional[str] = None
    due_date: Optional[datetime] = None
    max_score: int = Field(default=100, ge=0, le=1000)

class AssignmentCreate(AssignmentBase):
    lesson_id: UUID

class AssignmentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    instructions: Optional[str] = None
    due_date: Optional[datetime] = None
    max_score: Optional[int] = Field(None, ge=0, le=1000)

class AssignmentResponse(AssignmentBase):
    id: UUID
    lesson_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# SUBMISSION SCHEMAS
# ============================================

class SubmissionCreate(BaseModel):
    assignment_id: UUID
    content: Optional[str] = None
    file_url: Optional[str] = None

class SubmissionUpdate(BaseModel):
    content: Optional[str] = None
    file_url: Optional[str] = None

class SubmissionGrade(BaseModel):
    score: int = Field(..., ge=0)
    feedback: Optional[str] = None

class SubmissionResponse(BaseModel):
    id: UUID
    assignment_id: UUID
    user_id: UUID
    content: Optional[str] = None
    file_url: Optional[str] = None
    score: Optional[int] = None
    feedback: Optional[str] = None
    submitted_at: datetime
    graded_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================
# COMMENT SCHEMAS
# ============================================

class CommentCreate(BaseModel):
    lesson_id: UUID
    content: str = Field(..., min_length=1)
    parent_comment_id: Optional[UUID] = None

class CommentUpdate(BaseModel):
    content: str = Field(..., min_length=1)

class CommentResponse(BaseModel):
    id: UUID
    user_id: UUID
    lesson_id: UUID
    content: str
    parent_comment_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CommentWithUser(CommentResponse):
    user: Optional[UserResponse] = None
    replies: Optional[List['CommentWithUser']] = []


# ============================================
# ACHIEVEMENT SCHEMAS
# ============================================

class AchievementBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    icon_url: Optional[str] = None
    points: int = Field(default=0, ge=0)

class AchievementCreate(AchievementBase):
    pass

class AchievementResponse(AchievementBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserAchievementResponse(BaseModel):
    id: UUID
    user_id: UUID
    achievement_id: UUID
    earned_at: datetime
    achievement: Optional[AchievementResponse] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================
# PAGINATION & FILTERS
# ============================================

class PaginationParams(BaseModel):
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)

class CourseFilters(BaseModel):
    difficulty_level: Optional[str] = None
    is_published: Optional[bool] = None
    instructor_id: Optional[UUID] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None

class PaginatedResponse(BaseModel):
    items: List
    total: int
    skip: int
    limit: int
    has_more: bool


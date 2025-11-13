"""
Pydantic Schemas for ToolboxAI Educational Platform
Request/Response validation for API endpoints
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# ============================================
# USER SCHEMAS
# ============================================


class UserBase(BaseModel):
    email: EmailStr
    username: str | None = None
    full_name: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    role: str = "student"


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    username: str | None = None
    full_name: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    role: str | None = None


class UserResponse(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# ============================================
# COURSE SCHEMAS
# ============================================


class CourseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    thumbnail_url: str | None = None
    difficulty_level: str = "beginner"
    is_published: bool = False
    price: float = Field(default=0.00, ge=0)


class CourseCreate(CourseBase):
    instructor_id: UUID | None = None


class CourseUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    thumbnail_url: str | None = None
    difficulty_level: str | None = None
    is_published: bool | None = None
    price: float | None = Field(None, ge=0)


class CourseResponse(CourseBase):
    id: UUID
    instructor_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CourseWithInstructor(CourseResponse):
    instructor: UserResponse | None = None
    lesson_count: int | None = 0


# ============================================
# LESSON SCHEMAS
# ============================================


class LessonBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    content: str | None = None
    video_url: str | None = None
    order_index: int = Field(..., ge=0)
    duration_minutes: int | None = Field(None, ge=0)
    is_free: bool = False


class LessonCreate(LessonBase):
    course_id: UUID


class LessonUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    content: str | None = None
    video_url: str | None = None
    order_index: int | None = Field(None, ge=0)
    duration_minutes: int | None = Field(None, ge=0)
    is_free: bool | None = None


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
    completed_at: datetime | None = None
    progress_percentage: float

    model_config = ConfigDict(from_attributes=True)


class EnrollmentWithCourse(EnrollmentResponse):
    course: CourseResponse | None = None


# ============================================
# LESSON PROGRESS SCHEMAS
# ============================================


class LessonProgressCreate(BaseModel):
    lesson_id: UUID
    completed: bool = False
    time_spent_minutes: int = Field(default=0, ge=0)


class LessonProgressUpdate(BaseModel):
    completed: bool | None = None
    time_spent_minutes: int | None = Field(None, ge=0)


class LessonProgressResponse(BaseModel):
    id: UUID
    user_id: UUID
    lesson_id: UUID
    completed: bool
    completed_at: datetime | None = None
    time_spent_minutes: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# ASSIGNMENT SCHEMAS
# ============================================


class AssignmentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    instructions: str | None = None
    due_date: datetime | None = None
    max_score: int = Field(default=100, ge=0, le=1000)


class AssignmentCreate(AssignmentBase):
    lesson_id: UUID


class AssignmentUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    instructions: str | None = None
    due_date: datetime | None = None
    max_score: int | None = Field(None, ge=0, le=1000)


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
    content: str | None = None
    file_url: str | None = None


class SubmissionUpdate(BaseModel):
    content: str | None = None
    file_url: str | None = None


class SubmissionGrade(BaseModel):
    score: int = Field(..., ge=0)
    feedback: str | None = None


class SubmissionResponse(BaseModel):
    id: UUID
    assignment_id: UUID
    user_id: UUID
    content: str | None = None
    file_url: str | None = None
    score: int | None = None
    feedback: str | None = None
    submitted_at: datetime
    graded_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================
# COMMENT SCHEMAS
# ============================================


class CommentCreate(BaseModel):
    lesson_id: UUID
    content: str = Field(..., min_length=1)
    parent_comment_id: UUID | None = None


class CommentUpdate(BaseModel):
    content: str = Field(..., min_length=1)


class CommentResponse(BaseModel):
    id: UUID
    user_id: UUID
    lesson_id: UUID
    content: str
    parent_comment_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CommentWithUser(CommentResponse):
    user: UserResponse | None = None
    replies: list["CommentWithUser"] | None = []


# ============================================
# ACHIEVEMENT SCHEMAS
# ============================================


class AchievementBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    icon_url: str | None = None
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
    achievement: AchievementResponse | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================
# PAGINATION & FILTERS
# ============================================


class PaginationParams(BaseModel):
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)


class CourseFilters(BaseModel):
    difficulty_level: str | None = None
    is_published: bool | None = None
    instructor_id: UUID | None = None
    min_price: float | None = None
    max_price: float | None = None


class PaginatedResponse(BaseModel):
    items: list
    total: int
    skip: int
    limit: int
    has_more: bool

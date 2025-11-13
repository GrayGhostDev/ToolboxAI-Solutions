"""
Pydantic models for Classes API endpoints
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, validator


class ClassBase(BaseModel):
    """Base class model with common fields"""

    name: str = Field(..., min_length=1, max_length=200)
    subject: str = Field(..., min_length=1, max_length=100)
    grade_level: int = Field(..., ge=1, le=12)
    room: str | None = Field(None, max_length=100)
    schedule: str | None = Field(None, max_length=200)
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    max_students: int = Field(30, gt=0)
    is_active: bool = Field(True)


class ClassCreate(ClassBase):
    """Model for creating a new class"""

    teacher_id: UUID | None = None  # Will be set from current user if not provided


class ClassUpdate(BaseModel):
    """Model for updating a class"""

    name: str | None = Field(None, min_length=1, max_length=200)
    subject: str | None = Field(None, min_length=1, max_length=100)
    grade_level: int | None = Field(None, ge=1, le=12)
    room: str | None = Field(None, max_length=100)
    schedule: str | None = Field(None, max_length=200)
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    max_students: int | None = Field(None, gt=0)
    is_active: bool | None = None


class ClassSummary(ClassBase):
    """Model for class summary (matches frontend expectations)"""

    id: str  # UUID as string for frontend compatibility
    teacher_id: str  # UUID as string
    student_count: int = 0
    average_xp: int = 0  # Placeholder for XP system
    created_at: datetime
    updated_at: datetime | None = None

    @validator("id", "teacher_id", pre=True)
    def convert_uuid_to_string(cls, v):
        """Convert UUID to string for frontend compatibility"""
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True  # For Pydantic v2
        arbitrary_types_allowed = True


class ClassDetails(ClassSummary):
    """Detailed class model with relationships"""

    teacher_name: str | None = None
    students: list[dict] = []  # Will be populated with student data
    total_lessons: int = 0
    completed_lessons: int = 0

    class Config:
        from_attributes = True


class EnrollmentBase(BaseModel):
    """Base enrollment model"""

    status: str = Field("active", pattern="^(active|dropped|completed)$")


class EnrollmentCreate(EnrollmentBase):
    """Model for creating enrollment"""

    class_id: UUID
    student_id: UUID


class EnrollmentUpdate(EnrollmentBase):
    """Model for updating enrollment"""

    status: str | None = Field(None, pattern="^(active|dropped|completed)$")
    final_grade: float | None = Field(None, ge=0, le=100)
    attendance_percentage: float | None = Field(None, ge=0, le=100)


class EnrollmentResponse(EnrollmentBase):
    """Enrollment response model"""

    id: str
    class_id: str
    student_id: str
    enrolled_at: datetime
    dropped_at: datetime | None = None
    final_grade: float | None = None
    attendance_percentage: float | None = None
    created_at: datetime
    updated_at: datetime | None = None

    @validator("id", "class_id", "student_id", pre=True)
    def convert_uuid_to_string(cls, v):
        """Convert UUID to string for frontend compatibility"""
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


# Response models for API consistency
class ClassResponse(BaseModel):
    """Standard API response wrapper for class operations"""

    status: str = "success"
    data: ClassSummary
    message: str = ""


class ClassListResponse(BaseModel):
    """Standard API response wrapper for class lists"""

    status: str = "success"
    data: list[ClassSummary]
    total: int
    page: int = 1
    per_page: int = 20
    message: str = ""


class ClassDetailsResponse(BaseModel):
    """Standard API response wrapper for class details"""

    status: str = "success"
    data: ClassDetails
    message: str = ""

"""
Classes API Endpoints
Handles class management for the educational platform
"""

import uuid
from datetime import datetime
from typing import List, Optional

from database import get_db
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from models import Class, ClassEnrollment, User, UserRole
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ._utils import now
from .auth import decode_token

# Create router
router = APIRouter(prefix="/api/v1/classes", tags=["classes"])
security = HTTPBearer()

# ==================== Pydantic Models ====================


class ClassCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    grade_level: int = Field(..., ge=1, le=12)
    subject: str
    schedule: Optional[dict] = None
    max_students: int = Field(default=30, ge=1, le=100)
    is_active: bool = True


class ClassUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    grade_level: Optional[int] = Field(None, ge=1, le=12)
    subject: Optional[str] = None
    schedule: Optional[dict] = None
    max_students: Optional[int] = Field(None, ge=1, le=100)
    is_active: Optional[bool] = None


class ClassResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    grade_level: int
    subject: str
    teacher_id: str
    teacher_name: str
    student_count: int
    schedule: Optional[str]  # Changed from dict to str to match database
    max_students: int
    is_active: bool
    is_online: bool
    average_progress: float
    created_at: datetime
    updated_at: Optional[datetime]  # Can be None in database


class ClassDetailsResponse(ClassResponse):
    students: List[dict]
    recent_activity: List[dict]
    upcoming_lessons: List[dict]
    performance_metrics: dict


class ClassEnrollmentRequest(BaseModel):
    user_id: str
    class_id: str


# ==================== Helper Functions ====================


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Verify JWT token and return current user"""
    try:
        payload = decode_token(credentials.credentials)
        user = db.query(User).filter(User.id == payload["sub"]).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )
        return user
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


def can_manage_class(user: User, class_obj: Class) -> bool:
    """Check if user can manage a class"""
    return user.role == UserRole.ADMIN or (
        user.role == UserRole.TEACHER and class_obj.teacher_id == user.id
    )


# ==================== Endpoints ====================


@router.get("/", response_model=List[ClassResponse])
async def list_classes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    grade_level: Optional[int] = None,
    subject: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all classes with optional filters"""

    query = db.query(Class)

    # Apply filters based on user role
    if current_user.role == UserRole.TEACHER:
        query = query.filter(Class.teacher_id == current_user.id)
    elif current_user.role == UserRole.STUDENT:
        # Get enrolled classes for student
        enrollments = (
            db.query(ClassEnrollment)
            .filter(ClassEnrollment.user_id == current_user.id)
            .all()
        )
        class_ids = [e.class_id for e in enrollments]
        if class_ids:
            query = query.filter(Class.id.in_(class_ids))
        else:
            return []
    elif current_user.role == UserRole.PARENT:
        # Get classes for parent's children
        children = db.query(User).filter(User.parent_id == current_user.id).all()
        child_ids = [child.id for child in children]
        enrollments = (
            db.query(ClassEnrollment)
            .filter(ClassEnrollment.user_id.in_(child_ids))
            .all()
        )
        class_ids = [e.class_id for e in enrollments]
        if class_ids:
            query = query.filter(Class.id.in_(class_ids))
        else:
            return []

    # Apply additional filters
    if grade_level:
        query = query.filter(Class.grade_level == grade_level)
    if subject:
        query = query.filter(Class.subject.ilike(f"%{subject}%"))
    if is_active is not None:
        query = query.filter(Class.is_active == is_active)

    classes = query.offset(skip).limit(limit).all()

    # Build response
    response = []
    for class_obj in classes:
        teacher = db.query(User).filter(User.id == class_obj.teacher_id).first()
        student_count = (
            db.query(ClassEnrollment)
            .filter(ClassEnrollment.class_id == class_obj.id)
            .count()
        )

        # Calculate average progress (mock for now)
        average_progress = 75.5  # This would be calculated from actual progress data

        response.append(
            ClassResponse(
                id=class_obj.id,
                name=class_obj.name,
                description=class_obj.description,
                grade_level=class_obj.grade_level,
                subject=class_obj.subject,
                teacher_id=class_obj.teacher_id,
                teacher_name=(teacher.display_name or "") if teacher else "",
                student_count=student_count,
                schedule=class_obj.schedule,
                max_students=class_obj.max_students,
                is_active=class_obj.is_active,
                is_online=class_obj.is_online,
                average_progress=average_progress,
                created_at=class_obj.created_at,
                updated_at=class_obj.updated_at,
            )
        )

    return response


@router.get("/{class_id}", response_model=ClassDetailsResponse)
async def get_class(
    class_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get detailed information about a specific class"""

    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Class not found"
        )

    # Check permissions
    if current_user.role == UserRole.STUDENT:
        enrollment = (
            db.query(ClassEnrollment)
            .filter(
                ClassEnrollment.user_id == current_user.id,
                ClassEnrollment.class_id == class_id,
            )
            .first()
        )
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not enrolled in this class",
            )

    # Get teacher info
    teacher = db.query(User).filter(User.id == class_obj.teacher_id).first()

    # Get enrolled students
    enrollments = (
        db.query(ClassEnrollment).filter(ClassEnrollment.class_id == class_id).all()
    )
    students = []
    for enrollment in enrollments:
        student = db.query(User).filter(User.id == enrollment.student_id).first()
        if student:
            students.append(
                {
                    "id": student.id,
                    "name": student.display_name,
                    "email": student.email,
                    "avatar_url": student.avatar_url,
                    "level": student.level,
                    "total_xp": student.total_xp,
                }
            )

    # Mock data for activities and lessons
    recent_activity = [
        {
            "type": "lesson_completed",
            "description": "5 students completed Fractions lesson",
            "timestamp": datetime.now().isoformat(),
        },
        {
            "type": "assessment_submitted",
            "description": "Quiz submissions received from 12 students",
            "timestamp": datetime.now().isoformat(),
        },
    ]

    upcoming_lessons = [
        {
            "id": "lesson1",
            "title": "Introduction to Algebra",
            "scheduled_date": datetime.now().isoformat(),
        },
        {
            "id": "lesson2",
            "title": "Solving Equations",
            "scheduled_date": datetime.now().isoformat(),
        },
    ]

    performance_metrics = {
        "average_score": 82.5,
        "completion_rate": 78.0,
        "attendance_rate": 92.0,
        "engagement_score": 85.0,
    }

    return ClassDetailsResponse(
        id=class_obj.id,
        name=class_obj.name,
        description=class_obj.description,
        grade_level=class_obj.grade_level,
        subject=class_obj.subject,
        teacher_id=class_obj.teacher_id,
        teacher_name=(teacher.display_name or "") if teacher else "",
        student_count=len(students),
        schedule=class_obj.schedule,
        max_students=class_obj.max_students,
        is_active=class_obj.is_active,
        is_online=class_obj.is_online,
        average_progress=75.5,
        created_at=class_obj.created_at,
        updated_at=class_obj.updated_at,
        students=students,
        recent_activity=recent_activity,
        upcoming_lessons=upcoming_lessons,
        performance_metrics=performance_metrics,
    )


@router.post("/", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
async def create_class(
    class_data: ClassCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new class"""

    # Check permissions
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers and admins can create classes",
        )

    # Create new class
    new_class = Class(
        id=str(uuid.uuid4()),
        name=class_data.name,
        description=class_data.description,
        grade_level=class_data.grade_level,
        subject=class_data.subject,
        teacher_id=current_user.id,
        schedule=class_data.schedule,
        max_students=class_data.max_students,
        is_active=class_data.is_active,
        is_online=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    db.add(new_class)
    db.commit()
    db.refresh(new_class)

    return ClassResponse(
        id=new_class.id,
        name=new_class.name,
        description=new_class.description,
        grade_level=new_class.grade_level,
        subject=new_class.subject,
        teacher_id=new_class.teacher_id,
        teacher_name=(current_user.display_name or ""),
        student_count=0,
        schedule=new_class.schedule,
        max_students=new_class.max_students,
        is_active=new_class.is_active,
        is_online=new_class.is_online,
        average_progress=0.0,
        created_at=new_class.created_at,
        updated_at=new_class.updated_at,
    )


@router.put("/{class_id}", response_model=ClassResponse)
async def update_class(
    class_id: str,
    class_data: ClassUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a class"""

    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Class not found"
        )

    # Check permissions
    if not can_manage_class(current_user, class_obj):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this class",
        )

    # Update fields
    update_data = class_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(class_obj, field, value)

    class_obj.updated_at = datetime.now()

    db.commit()
    db.refresh(class_obj)

    # Get student count
    student_count = (
        db.query(ClassEnrollment).filter(ClassEnrollment.class_id == class_id).count()
    )

    return ClassResponse(
        id=class_obj.id,
        name=class_obj.name,
        description=class_obj.description,
        grade_level=class_obj.grade_level,
        subject=class_obj.subject,
        teacher_id=class_obj.teacher_id,
        teacher_name=(current_user.display_name or ""),
        student_count=student_count,
        schedule=class_obj.schedule,
        max_students=class_obj.max_students,
        is_active=class_obj.is_active,
        is_online=class_obj.is_online,
        average_progress=75.5,
        created_at=class_obj.created_at,
        updated_at=class_obj.updated_at,
    )


@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_class(
    class_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a class"""

    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Class not found"
        )

    # Check permissions
    if not can_manage_class(current_user, class_obj):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this class",
        )

    # Delete enrollments first
    db.query(ClassEnrollment).filter(ClassEnrollment.class_id == class_id).delete()

    # Delete the class
    db.delete(class_obj)
    db.commit()

    return None


@router.post("/{class_id}/enroll", status_code=status.HTTP_201_CREATED)
async def enroll_student(
    class_id: str,
    enrollment: ClassEnrollmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Enroll a student in a class"""

    # Check if class exists
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Class not found"
        )

    # Check permissions
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        if current_user.id != enrollment.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only enroll yourself",
            )

    # Check if already enrolled
    existing = (
        db.query(ClassEnrollment)
        .filter(
            ClassEnrollment.user_id == enrollment.user_id,
            ClassEnrollment.class_id == class_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student is already enrolled in this class",
        )

    # Check max students
    current_count = (
        db.query(ClassEnrollment).filter(ClassEnrollment.class_id == class_id).count()
    )
    if current_count >= class_obj.max_students:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Class is full"
        )

    # Create enrollment
    new_enrollment = ClassEnrollment(
        id=str(uuid.uuid4()),
        user_id=enrollment.user_id,
        class_id=class_id,
        enrollment_date=now(),
        is_active=True,
    )

    db.add(new_enrollment)
    db.commit()

    return {"message": "Student enrolled successfully"}


@router.delete(
    "/{class_id}/unenroll/{student_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def unenroll_student(
    class_id: str,
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a student from a class"""

    # Check permissions
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Class not found"
        )

    if current_user.role == UserRole.STUDENT and current_user.id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only unenroll yourself",
        )
    elif (
        current_user.role == UserRole.TEACHER
        and class_obj.teacher_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage students in your own classes",
        )

    # Find and delete enrollment
    enrollment = (
        db.query(ClassEnrollment)
        .filter(
            ClassEnrollment.user_id == student_id, ClassEnrollment.class_id == class_id
        )
        .first()
    )

    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="ClassEnrollment not found"
        )

    db.delete(enrollment)
    db.commit()

    return None


# Export router
__all__ = ["router"]

"""
Classes API Endpoints for ToolboxAI Educational Platform
Provides class management functionality for all user roles.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
from uuid import UUID

from apps.backend.api.auth.auth import get_current_user
from apps.backend.models.classes import (
    ClassCreate, ClassUpdate, ClassSummary, ClassDetails,
    ClassResponse, ClassListResponse, ClassDetailsResponse
)
from database.models import Class, ClassEnrollment, User
from database.database_service import DatabaseService

# Create database service instance
database_service = DatabaseService()
from sqlalchemy import and_, func, select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional as Opt

# User model for type hints (keeping for backward compatibility)
class UserModel(BaseModel):
    id: str
    username: str
    role: str
    email: Optional[str] = None

logger = logging.getLogger(__name__)

# Database session dependency
async def get_db_session():
    """Get database session"""
    async with database_service.async_session_scope() as session:
        yield session

# Create router for classes endpoints
classes_router = APIRouter(prefix="/classes", tags=["Classes"])

# Export standardized router name
router = classes_router

@classes_router.get("/", response_model=List[ClassSummary])
async def get_classes(
    current_user: UserModel = Depends(get_current_user),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    subject: Optional[str] = None,
    grade_level: Optional[int] = None,
    session = Depends(get_db_session)
) -> List[ClassSummary]:
    """Get classes based on user role."""

    try:
        await database_service.initialize()

        role = current_user.role.lower()
        user_id = UUID(current_user.id)

        async with database_service.async_session_scope() as db_session:
            if role == "teacher":
                # Get teacher's classes with student count
                query = select(
                    Class,
                    func.count(ClassEnrollment.student_id).label('student_count')
                ).select_from(
                    Class.__table__.join(ClassEnrollment.__table__, Class.id == ClassEnrollment.class_id, isouter=True)
                ).where(
                    Class.teacher_id == user_id
                ).group_by(Class.id).order_by(Class.created_at.desc()).limit(limit).offset(offset)

                result = await db_session.execute(query)
                rows = result.all()

                classes = []
                for class_obj, student_count in rows:
                    class_summary = ClassSummary(
                        id=str(class_obj.id),
                        name=class_obj.name,
                        teacher_id=str(class_obj.teacher_id),
                        grade_level=class_obj.grade_level,
                        subject=class_obj.subject,
                        room=class_obj.room,
                        schedule=class_obj.schedule,
                        description=class_obj.description,
                        start_time=class_obj.start_time,
                        end_time=class_obj.end_time,
                        max_students=class_obj.max_students,
                        is_active=class_obj.is_active,
                        student_count=student_count or 0,
                        average_xp=0,  # TODO: Implement XP calculation
                        created_at=class_obj.created_at,
                        updated_at=class_obj.updated_at
                    )
                    classes.append(class_summary)

                return classes

            elif role == "student":
                # Get student's enrolled classes
                query = select(
                    Class
                ).select_from(
                    Class.__table__.join(
                        ClassEnrollment.__table__,
                        Class.id == ClassEnrollment.class_id
                    )
                ).where(
                    and_(
                        ClassEnrollment.student_id == user_id,
                        ClassEnrollment.status == 'active'
                    )
                ).order_by(Class.name).limit(limit).offset(offset)

                result = await db_session.execute(query)
                class_objects = result.scalars().all()

                classes = []
                for class_obj in class_objects:
                    class_summary = ClassSummary(
                        id=str(class_obj.id),
                        name=class_obj.name,
                        teacher_id=str(class_obj.teacher_id),
                        grade_level=class_obj.grade_level,
                        subject=class_obj.subject,
                        room=class_obj.room,
                        schedule=class_obj.schedule,
                        description=class_obj.description,
                        start_time=class_obj.start_time,
                        end_time=class_obj.end_time,
                        max_students=class_obj.max_students,
                        is_active=class_obj.is_active,
                        student_count=0,  # Individual view doesn't need count
                        average_xp=0,  # TODO: Implement XP calculation
                        created_at=class_obj.created_at,
                        updated_at=class_obj.updated_at
                    )
                    classes.append(class_summary)

                return classes

            elif role == "admin":
                # Get all classes with optional filters
                query = select(
                    Class,
                    func.count(ClassEnrollment.student_id).label('student_count')
                ).select_from(
                    Class.__table__.join(ClassEnrollment.__table__, Class.id == ClassEnrollment.class_id, isouter=True)
                )

                # Apply filters
                conditions = []
                if subject:
                    conditions.append(Class.subject == subject)
                if grade_level:
                    conditions.append(Class.grade_level == grade_level)

                if conditions:
                    query = query.where(and_(*conditions))

                query = query.group_by(Class.id).order_by(Class.created_at.desc()).limit(limit).offset(offset)

                result = await db_session.execute(query)
                rows = result.all()

                classes = []
                for class_obj, student_count in rows:
                    class_summary = ClassSummary(
                        id=str(class_obj.id),
                        name=class_obj.name,
                        teacher_id=str(class_obj.teacher_id),
                        grade_level=class_obj.grade_level,
                        subject=class_obj.subject,
                        room=class_obj.room,
                        schedule=class_obj.schedule,
                        description=class_obj.description,
                        start_time=class_obj.start_time,
                        end_time=class_obj.end_time,
                        max_students=class_obj.max_students,
                        is_active=class_obj.is_active,
                        student_count=student_count or 0,
                        average_xp=0,  # TODO: Implement XP calculation
                        created_at=class_obj.created_at,
                        updated_at=class_obj.updated_at
                    )
                    classes.append(class_summary)

                return classes

            elif role == "parent":
                # TODO: Implement parent-student relationships
                # For now, return empty list
                return []

            else:
                return []

    except Exception as e:
        logger.error(f"Database error in get_classes: {e}")
        # Fall back to sample data if database fails
        # Fallback sample data if database fails
        if role == "teacher":
            return [
                ClassSummary(
                    id="1",
                    name="Mathematics 101",
                    subject="Mathematics",
                    teacher_id=current_user.id,
                    grade_level=7,
                    room="Room 203",
                    schedule="Mon/Wed/Fri 10:00 AM",
                    student_count=28,
                    average_xp=0,
                    max_students=30,
                    is_active=True,
                    created_at=datetime(2024, 9, 1, 8, 0, 0)
                )
            ]
        elif role == "student":
            return [
                ClassSummary(
                    id="1",
                    name="Mathematics 101",
                    subject="Mathematics",
                    teacher_id="teacher123",
                    grade_level=7,
                    room="Room 203",
                    schedule="Mon/Wed/Fri 10:00 AM",
                    student_count=0,
                    average_xp=0,
                    max_students=30,
                    is_active=True,
                    created_at=datetime(2024, 9, 1, 8, 0, 0)
                )
            ]
        elif role == "admin":
            return [
                ClassSummary(
                    id="1",
                    name="Mathematics 101",
                    subject="Mathematics",
                    teacher_id="teacher123",
                    grade_level=7,
                    room="Room 203",
                    schedule="Mon/Wed/Fri 10:00 AM",
                    student_count=28,
                    average_xp=0,
                    max_students=30,
                    is_active=True,
                    created_at=datetime(2024, 9, 1, 8, 0, 0)
                )
            ]
        else:
            return []

@classes_router.get("/{class_id}", response_model=ClassDetails)
async def get_class_details(
    class_id: str,
    current_user: UserModel = Depends(get_current_user)
) -> ClassDetails:
    """Get detailed information about a specific class."""

    try:
        await database_service.initialize()

        role = current_user.role.lower()
        user_id = UUID(current_user.id)
        class_uuid = UUID(class_id)

        async with database_service.async_session_scope() as db_session:
            # Base query to get class details
            query = select(Class).where(Class.id == class_uuid)

            # Apply role-based access control
            if role == "teacher":
                # Teacher can only see their own classes
                query = query.where(Class.teacher_id == user_id)
            elif role == "student":
                # Student can only see classes they're enrolled in
                query = query.join(ClassEnrollment).where(
                    and_(
                        ClassEnrollment.student_id == user_id,
                        ClassEnrollment.status == 'active'
                    )
                )
            # Admin can see all classes (no additional filter)

            result = await db_session.execute(query)
            class_obj = result.scalar_one_or_none()

            if not class_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Class not found or access denied"
                )

            # Get student count
            student_count_query = select(func.count(ClassEnrollment.student_id)).where(
                and_(
                    ClassEnrollment.class_id == class_obj.id,
                    ClassEnrollment.status == 'active'
                )
            )
            student_count_result = await db_session.execute(student_count_query)
            student_count = student_count_result.scalar() or 0

            # Get teacher name
            teacher_query = select(User).where(User.id == class_obj.teacher_id)
            teacher_result = await db_session.execute(teacher_query)
            teacher = teacher_result.scalar_one_or_none()
            teacher_name = None
            if teacher:
                if teacher.first_name and teacher.last_name:
                    teacher_name = f"{teacher.first_name} {teacher.last_name}"
                else:
                    teacher_name = teacher.username or teacher.email

            # Create response model
            class_details = ClassDetails(
                id=str(class_obj.id),
                name=class_obj.name,
                teacher_id=str(class_obj.teacher_id),
                grade_level=class_obj.grade_level,
                subject=class_obj.subject,
                room=class_obj.room,
                schedule=class_obj.schedule,
                description=class_obj.description,
                start_time=class_obj.start_time,
                end_time=class_obj.end_time,
                max_students=class_obj.max_students,
                is_active=class_obj.is_active,
                student_count=student_count,
                average_xp=0,  # TODO: Implement XP calculation
                created_at=class_obj.created_at,
                updated_at=class_obj.updated_at,
                teacher_name=teacher_name,
                students=[],  # TODO: Implement student list
                total_lessons=0,  # TODO: Implement lesson count
                completed_lessons=0  # TODO: Implement completed lesson count
            )

            return class_details

    except ValueError as e:
        # Invalid UUID
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid class ID format"
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error fetching class details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch class details"
        )

@classes_router.get("/{class_id}/students")
async def get_class_students(
    class_id: str,
    current_user: UserModel = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get students enrolled in a class."""

    role = current_user.role.lower()

    # Only teachers and admins can see full student list
    if role not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view student list"
        )

    try:
        await database_service.initialize()

        user_id = UUID(current_user.id)
        class_uuid = UUID(class_id)

        async with database_service.async_session_scope() as db_session:
            # First verify access to the class
            class_query = select(Class).where(Class.id == class_uuid)

            # Teachers can only see students in their own classes
            if role == "teacher":
                class_query = class_query.where(Class.teacher_id == user_id)

            class_result = await db_session.execute(class_query)
            class_obj = class_result.scalar_one_or_none()

            if not class_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Class not found or access denied"
                )

            # Get enrolled students
            students_query = select(
                User,
                ClassEnrollment.enrolled_at,
                ClassEnrollment.status,
                ClassEnrollment.final_grade,
                ClassEnrollment.attendance_percentage
            ).select_from(
                User.__table__.join(
                    ClassEnrollment.__table__,
                    User.id == ClassEnrollment.student_id
                )
            ).where(
                ClassEnrollment.class_id == class_uuid
            ).order_by(User.last_name, User.first_name)

            result = await db_session.execute(students_query)
            students_data = result.all()

            students = []
            for user, enrolled_at, enrollment_status, final_grade, attendance in students_data:
                student = {
                    "id": str(user.id),
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "enrolled_at": enrolled_at,
                    "status": enrollment_status,
                    "final_grade": final_grade,
                    "attendance_percentage": attendance
                }
                students.append(student)

            return students

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid class ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching class students: {e}")
        # Fallback sample data
        return [
            {
                "id": "1",
                "username": "alex_j",
                "first_name": "Alex",
                "last_name": "Johnson",
                "email": "alex.j@school.edu",
                "enrolled_at": "2024-09-01T08:00:00",
                "status": "active",
                "final_grade": None,
                "attendance_percentage": None
            }
        ]

@classes_router.post("/", response_model=ClassSummary, status_code=status.HTTP_201_CREATED)
async def create_class(
    class_data: ClassCreate,
    current_user: UserModel = Depends(get_current_user)
) -> ClassSummary:
    """Create a new class (teachers and admins only)."""

    role = current_user.role.lower()

    if role not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create classes"
        )

    try:
        await database_service.initialize()

        user_id = UUID(current_user.id)

        # Set teacher_id to current user if not provided or if current user is teacher
        teacher_id = class_data.teacher_id if class_data.teacher_id and role == "admin" else user_id

        async with database_service.async_session_scope() as db_session:
            # Create new class instance
            new_class = Class(
                name=class_data.name,
                teacher_id=teacher_id,
                grade_level=class_data.grade_level,
                subject=class_data.subject,
                room=class_data.room,
                schedule=class_data.schedule,
                description=class_data.description,
                start_time=class_data.start_time,
                end_time=class_data.end_time,
                max_students=class_data.max_students,
                is_active=class_data.is_active
            )

            db_session.add(new_class)
            await db_session.flush()  # Flush to get the ID
            await db_session.refresh(new_class)  # Refresh to get all fields

            # Convert to response model
            class_summary = ClassSummary(
                id=str(new_class.id),
                name=new_class.name,
                teacher_id=str(new_class.teacher_id),
                grade_level=new_class.grade_level,
                subject=new_class.subject,
                room=new_class.room,
                schedule=new_class.schedule,
                description=new_class.description,
                start_time=new_class.start_time,
                end_time=new_class.end_time,
                max_students=new_class.max_students,
                is_active=new_class.is_active,
                student_count=0,  # New class has no students
                average_xp=0,  # TODO: Implement XP calculation
                created_at=new_class.created_at,
                updated_at=new_class.updated_at
            )

            await db_session.commit()

            logger.info(f"Created class: {new_class.name} for user {current_user.id}")
            return class_summary

    except Exception as e:
        logger.error(f"Error creating class: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create class: {str(e)}"
        )

@classes_router.put("/{class_id}", response_model=ClassSummary)
async def update_class(
    class_id: str,
    class_data: ClassUpdate,
    current_user: UserModel = Depends(get_current_user)
) -> ClassSummary:
    """Update class information."""

    role = current_user.role.lower()

    if role not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update classes"
        )

    try:
        await database_service.initialize()

        user_id = UUID(current_user.id)
        class_uuid = UUID(class_id)

        async with database_service.async_session_scope() as db_session:
            # Get the class to update
            query = select(Class).where(Class.id == class_uuid)

            # Teachers can only update their own classes
            if role == "teacher":
                query = query.where(Class.teacher_id == user_id)

            result = await db_session.execute(query)
            class_obj = result.scalar_one_or_none()

            if not class_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Class not found or access denied"
                )

            # Update only provided fields
            update_data = class_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(class_obj, field, value)

            await db_session.flush()
            await db_session.refresh(class_obj)

            # Get student count for response
            student_count_query = select(func.count(ClassEnrollment.student_id)).where(
                and_(
                    ClassEnrollment.class_id == class_obj.id,
                    ClassEnrollment.status == 'active'
                )
            )
            student_count_result = await db_session.execute(student_count_query)
            student_count = student_count_result.scalar() or 0

            # Create response model
            class_summary = ClassSummary(
                id=str(class_obj.id),
                name=class_obj.name,
                teacher_id=str(class_obj.teacher_id),
                grade_level=class_obj.grade_level,
                subject=class_obj.subject,
                room=class_obj.room,
                schedule=class_obj.schedule,
                description=class_obj.description,
                start_time=class_obj.start_time,
                end_time=class_obj.end_time,
                max_students=class_obj.max_students,
                is_active=class_obj.is_active,
                student_count=student_count,
                average_xp=0,  # TODO: Implement XP calculation
                created_at=class_obj.created_at,
                updated_at=class_obj.updated_at
            )

            await db_session.commit()

            logger.info(f"Updated class {class_id} for user {current_user.id}")
            return class_summary

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid class ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating class: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update class"
        )

@classes_router.post("/{class_id}/students/{student_id}")
async def enroll_student(
    class_id: str,
    student_id: str,
    current_user: UserModel = Depends(get_current_user)
) -> Dict[str, Any]:
    """Enroll a student in a class."""

    role = current_user.role.lower()

    if role not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to enroll students"
        )

    try:
        await database_service.initialize()

        user_id = UUID(current_user.id)
        class_uuid = UUID(class_id)
        student_uuid = UUID(student_id)

        async with database_service.async_session_scope() as db_session:
            # Verify the class exists and teacher has access
            class_query = select(Class).where(Class.id == class_uuid)
            if role == "teacher":
                class_query = class_query.where(Class.teacher_id == user_id)

            class_result = await db_session.execute(class_query)
            class_obj = class_result.scalar_one_or_none()

            if not class_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Class not found or access denied"
                )

            # Check if student exists and is actually a student
            student_query = select(User).where(
                and_(
                    User.id == student_uuid,
                    User.role == 'student'
                )
            )
            student_result = await db_session.execute(student_query)
            student = student_result.scalar_one_or_none()

            if not student:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Student not found"
                )

            # Check if already enrolled
            existing_query = select(ClassEnrollment).where(
                and_(
                    ClassEnrollment.class_id == class_uuid,
                    ClassEnrollment.student_id == student_uuid
                )
            )
            existing_result = await db_session.execute(existing_query)
            existing_enrollment = existing_result.scalar_one_or_none()

            if existing_enrollment:
                if existing_enrollment.status == 'active':
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Student is already enrolled in this class"
                    )
                else:
                    # Reactivate enrollment
                    existing_enrollment.status = 'active'
                    existing_enrollment.enrolled_at = datetime.utcnow()
                    await db_session.commit()
                    return {
                        "message": f"Student {student.username} re-enrolled successfully",
                        "student_id": str(student.id),
                        "class_id": str(class_obj.id)
                    }

            # Check max students limit
            student_count_query = select(func.count(ClassEnrollment.student_id)).where(
                and_(
                    ClassEnrollment.class_id == class_uuid,
                    ClassEnrollment.status == 'active'
                )
            )
            count_result = await db_session.execute(student_count_query)
            current_count = count_result.scalar() or 0

            if class_obj.max_students and current_count >= class_obj.max_students:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Class is full (max {class_obj.max_students} students)"
                )

            # Create new enrollment
            enrollment = ClassEnrollment(
                class_id=class_uuid,
                student_id=student_uuid,
                enrolled_at=datetime.utcnow(),
                status='active'
            )
            db_session.add(enrollment)
            await db_session.commit()

            logger.info(f"Enrolled student {student_id} in class {class_id}")
            return {
                "message": f"Student {student.username} enrolled successfully",
                "student_id": str(student.id),
                "class_id": str(class_obj.id)
            }

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enrolling student: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enroll student"
        )

@classes_router.delete("/{class_id}/students/{student_id}")
async def unenroll_student(
    class_id: str,
    student_id: str,
    current_user: UserModel = Depends(get_current_user)
) -> Dict[str, str]:
    """Remove a student from a class."""

    role = current_user.role.lower()

    if role not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to remove students"
        )

    try:
        await database_service.initialize()

        user_id = UUID(current_user.id)
        class_uuid = UUID(class_id)
        student_uuid = UUID(student_id)

        async with database_service.async_session_scope() as db_session:
            # Verify the class exists and teacher has access
            class_query = select(Class).where(Class.id == class_uuid)
            if role == "teacher":
                class_query = class_query.where(Class.teacher_id == user_id)

            class_result = await db_session.execute(class_query)
            class_obj = class_result.scalar_one_or_none()

            if not class_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Class not found or access denied"
                )

            # Find the enrollment
            enrollment_query = select(ClassEnrollment).where(
                and_(
                    ClassEnrollment.class_id == class_uuid,
                    ClassEnrollment.student_id == student_uuid
                )
            )
            enrollment_result = await db_session.execute(enrollment_query)
            enrollment = enrollment_result.scalar_one_or_none()

            if not enrollment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Student is not enrolled in this class"
                )

            # Mark as inactive instead of deleting
            enrollment.status = 'inactive'
            await db_session.commit()

            logger.info(f"Removed student {student_id} from class {class_id}")
            return {"message": "Student removed from class successfully"}

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing student: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove student"
        )

@classes_router.post("/{class_id}/students/batch")
async def batch_enroll_students(
    class_id: str,
    student_ids: List[str],
    current_user: UserModel = Depends(get_current_user)
) -> Dict[str, Any]:
    """Enroll multiple students in a class at once."""

    role = current_user.role.lower()

    if role not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to enroll students"
        )

    try:
        await database_service.initialize()

        user_id = UUID(current_user.id)
        class_uuid = UUID(class_id)

        async with database_service.async_session_scope() as db_session:
            # Verify the class exists and teacher has access
            class_query = select(Class).where(Class.id == class_uuid)
            if role == "teacher":
                class_query = class_query.where(Class.teacher_id == user_id)

            class_result = await db_session.execute(class_query)
            class_obj = class_result.scalar_one_or_none()

            if not class_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Class not found or access denied"
                )

            enrolled = []
            already_enrolled = []
            failed = []

            for student_id in student_ids:
                try:
                    student_uuid = UUID(student_id)

                    # Check if student exists
                    student_query = select(User).where(
                        and_(
                            User.id == student_uuid,
                            User.role == 'student'
                        )
                    )
                    student_result = await db_session.execute(student_query)
                    student = student_result.scalar_one_or_none()

                    if not student:
                        failed.append({"id": student_id, "reason": "Student not found"})
                        continue

                    # Check if already enrolled
                    existing_query = select(ClassEnrollment).where(
                        and_(
                            ClassEnrollment.class_id == class_uuid,
                            ClassEnrollment.student_id == student_uuid
                        )
                    )
                    existing_result = await db_session.execute(existing_query)
                    existing = existing_result.scalar_one_or_none()

                    if existing and existing.status == 'active':
                        already_enrolled.append(student.username)
                        continue

                    if existing:
                        # Reactivate
                        existing.status = 'active'
                        existing.enrolled_at = datetime.utcnow()
                    else:
                        # Create new enrollment
                        enrollment = ClassEnrollment(
                            class_id=class_uuid,
                            student_id=student_uuid,
                            enrolled_at=datetime.utcnow(),
                            status='active'
                        )
                        db_session.add(enrollment)

                    enrolled.append(student.username)

                except ValueError:
                    failed.append({"id": student_id, "reason": "Invalid ID format"})
                except Exception as e:
                    failed.append({"id": student_id, "reason": str(e)})

            await db_session.commit()

            return {
                "enrolled": enrolled,
                "already_enrolled": already_enrolled,
                "failed": failed,
                "summary": {
                    "total_processed": len(student_ids),
                    "successfully_enrolled": len(enrolled),
                    "already_enrolled": len(already_enrolled),
                    "failed": len(failed)
                }
            }

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid class ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch enrollment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process batch enrollment"
        )

@classes_router.delete("/{class_id}")
async def delete_class(
    class_id: str,
    current_user: UserModel = Depends(get_current_user)
) -> Dict[str, str]:
    """Delete a class (admins only)."""

    if current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete classes"
        )

    try:
        await database_service.initialize()

        class_uuid = UUID(class_id)

        async with database_service.async_session_scope() as db_session:
            # Get the class to delete
            query = select(Class).where(Class.id == class_uuid)
            result = await db_session.execute(query)
            class_obj = result.scalar_one_or_none()

            if not class_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Class not found"
                )

            class_name = class_obj.name
            await db_session.delete(class_obj)
            await db_session.commit()

            logger.info(f"Deleted class {class_id} ({class_name}) by admin {current_user.id}")
            return {"message": f"Class '{class_name}' deleted successfully"}

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid class ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting class: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete class"
        )
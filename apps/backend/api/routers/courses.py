"""
API Router for Course Management
Handles CRUD operations for courses, lessons, and enrollments
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from apps.backend.core.database import get_db
from apps.backend.models.education import (
    Course,
    Enrollment,
    Lesson,
    LessonProgress,
    User,
)
from apps.backend.schemas.education import (
    CourseCreate,
    CourseResponse,
    CourseUpdate,
    CourseWithInstructor,
    EnrollmentResponse,
    EnrollmentWithCourse,
    LessonCreate,
    LessonResponse,
    LessonUpdate,
)

router = APIRouter(prefix="/api/v1/courses", tags=["courses"])


# ============================================
# COURSE ENDPOINTS
# ============================================


@router.get("/", response_model=list[CourseResponse])
async def list_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    is_published: bool | None = None,
    difficulty_level: str | None = None,
    instructor_id: UUID | None = None,
    db: Session = Depends(get_db),
):
    """
    List all courses with optional filters
    """
    query = db.query(Course)

    if is_published is not None:
        query = query.filter(Course.is_published == is_published)
    if difficulty_level:
        query = query.filter(Course.difficulty_level == difficulty_level)
    if instructor_id:
        query = query.filter(Course.instructor_id == instructor_id)

    courses = query.offset(skip).limit(limit).all()
    return courses


@router.get("/{course_id}", response_model=CourseWithInstructor)
async def get_course(course_id: UUID, db: Session = Depends(get_db)):
    """
    Get a single course by ID with instructor details
    """
    course = db.query(Course).filter(Course.id == course_id).first()

    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    # Get lesson count
    lesson_count = db.query(func.count(Lesson.id)).filter(Lesson.course_id == course_id).scalar()

    course_dict = CourseResponse.model_validate(course).model_dump()
    course_dict["lesson_count"] = lesson_count

    return course_dict


@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(course_data: CourseCreate, db: Session = Depends(get_db)):
    """
    Create a new course
    """
    # Verify instructor exists if provided
    if course_data.instructor_id:
        instructor = db.query(User).filter(User.id == course_data.instructor_id).first()
        if not instructor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Instructor not found"
            )

    new_course = Course(**course_data.model_dump())
    db.add(new_course)
    db.commit()
    db.refresh(new_course)

    return new_course


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(course_id: UUID, course_data: CourseUpdate, db: Session = Depends(get_db)):
    """
    Update a course
    """
    course = db.query(Course).filter(Course.id == course_id).first()

    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    # Update fields
    update_data = course_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(course, field, value)

    db.commit()
    db.refresh(course)

    return course


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(course_id: UUID, db: Session = Depends(get_db)):
    """
    Delete a course
    """
    course = db.query(Course).filter(Course.id == course_id).first()

    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    db.delete(course)
    db.commit()

    return None


# ============================================
# LESSON ENDPOINTS
# ============================================


@router.get("/{course_id}/lessons", response_model=list[LessonResponse])
async def list_course_lessons(course_id: UUID, db: Session = Depends(get_db)):
    """
    List all lessons for a course, ordered by order_index
    """
    # Verify course exists
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    lessons = (
        db.query(Lesson).filter(Lesson.course_id == course_id).order_by(Lesson.order_index).all()
    )

    return lessons


@router.get("/{course_id}/lessons/{lesson_id}", response_model=LessonResponse)
async def get_lesson(course_id: UUID, lesson_id: UUID, db: Session = Depends(get_db)):
    """
    Get a single lesson by ID
    """
    lesson = (
        db.query(Lesson).filter(and_(Lesson.id == lesson_id, Lesson.course_id == course_id)).first()
    )

    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

    return lesson


@router.post(
    "/{course_id}/lessons", response_model=LessonResponse, status_code=status.HTTP_201_CREATED
)
async def create_lesson(course_id: UUID, lesson_data: LessonCreate, db: Session = Depends(get_db)):
    """
    Create a new lesson for a course
    """
    # Verify course exists
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    # Ensure lesson belongs to this course
    lesson_dict = lesson_data.model_dump()
    lesson_dict["course_id"] = course_id

    new_lesson = Lesson(**lesson_dict)
    db.add(new_lesson)
    db.commit()
    db.refresh(new_lesson)

    return new_lesson


@router.put("/{course_id}/lessons/{lesson_id}", response_model=LessonResponse)
async def update_lesson(
    course_id: UUID, lesson_id: UUID, lesson_data: LessonUpdate, db: Session = Depends(get_db)
):
    """
    Update a lesson
    """
    lesson = (
        db.query(Lesson).filter(and_(Lesson.id == lesson_id, Lesson.course_id == course_id)).first()
    )

    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

    # Update fields
    update_data = lesson_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lesson, field, value)

    db.commit()
    db.refresh(lesson)

    return lesson


@router.delete("/{course_id}/lessons/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson(course_id: UUID, lesson_id: UUID, db: Session = Depends(get_db)):
    """
    Delete a lesson
    """
    lesson = (
        db.query(Lesson).filter(and_(Lesson.id == lesson_id, Lesson.course_id == course_id)).first()
    )

    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

    db.delete(lesson)
    db.commit()

    return None


# ============================================
# ENROLLMENT ENDPOINTS
# ============================================


@router.post(
    "/{course_id}/enroll", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED
)
async def enroll_in_course(
    course_id: UUID,
    user_id: UUID,  # In production, get from auth token
    db: Session = Depends(get_db),
):
    """
    Enroll a user in a course
    """
    # Verify course exists
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    # Check if already enrolled
    existing = (
        db.query(Enrollment)
        .filter(and_(Enrollment.user_id == user_id, Enrollment.course_id == course_id))
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Already enrolled in this course"
        )

    # Create enrollment
    enrollment = Enrollment(user_id=user_id, course_id=course_id)
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)

    return enrollment


@router.get("/enrollments/user/{user_id}", response_model=list[EnrollmentWithCourse])
async def get_user_enrollments(user_id: UUID, db: Session = Depends(get_db)):
    """
    Get all enrollments for a user
    """
    enrollments = db.query(Enrollment).filter(Enrollment.user_id == user_id).all()

    return enrollments


@router.get("/{course_id}/progress/{user_id}")
async def get_course_progress(course_id: UUID, user_id: UUID, db: Session = Depends(get_db)):
    """
    Get detailed progress for a user in a course
    """
    # Get enrollment
    enrollment = (
        db.query(Enrollment)
        .filter(and_(Enrollment.user_id == user_id, Enrollment.course_id == course_id))
        .first()
    )

    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Not enrolled in this course"
        )

    # Get lesson progress
    lessons = db.query(Lesson).filter(Lesson.course_id == course_id).all()
    lesson_ids = [lesson.id for lesson in lessons]

    progress = (
        db.query(LessonProgress)
        .filter(and_(LessonProgress.user_id == user_id, LessonProgress.lesson_id.in_(lesson_ids)))
        .all()
    )

    return {
        "enrollment": EnrollmentResponse.model_validate(enrollment),
        "total_lessons": len(lessons),
        "completed_lessons": sum(1 for p in progress if p.completed),
        "progress_percentage": enrollment.progress_percentage,
        "lesson_progress": [
            {
                "lesson_id": p.lesson_id,
                "completed": p.completed,
                "time_spent_minutes": p.time_spent_minutes,
            }
            for p in progress
        ],
    }

"""
GraphQL Query resolvers
"""

import uuid
from typing import Optional, List, Dict, Any

from ariadne import QueryType
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from database.models import User, Course, Lesson, Quiz, Enrollment
from apps.backend.core.config import settings

# Create Query type
query = QueryType()


@query.field("health")
async def resolve_health(obj, info) -> str:
    """Health check resolver"""
    return "GraphQL service is healthy"


@query.field("version")
async def resolve_version(obj, info) -> str:
    """Version resolver"""
    return f"ToolBoxAI GraphQL API v{settings.VERSION if hasattr(settings, 'VERSION') else '1.0.0'}"


# User resolvers
@query.field("me")
async def resolve_me(obj, info) -> Optional[User]:
    """Get current authenticated user"""

    user = info.context.get("user")
    if not user:
        raise Exception("Not authenticated")

    return user


@query.field("user")
async def resolve_user(obj, info, id: str) -> Optional[User]:
    """Get user by ID"""

    db = info.context["db"]
    loader = info.context["loaders"]["user"]

    # Use DataLoader for efficient loading
    user_id = uuid.UUID(id)
    user = await loader.load(user_id)

    return user


@query.field("users")
async def resolve_users(
    obj,
    info,
    filter: Optional[Dict] = None,
    sort: Optional[Dict] = None,
    pagination: Optional[Dict] = None
) -> Dict[str, Any]:
    """List users with filtering and pagination"""

    db = info.context["db"]

    # Build query
    stmt = select(User)

    # Apply filters
    if filter:
        if filter.get("role"):
            stmt = stmt.where(User.role == filter["role"])
        if filter.get("isActive") is not None:
            stmt = stmt.where(User.is_active == filter["isActive"])
        if filter.get("search"):
            search_term = f"%{filter['search']}%"
            stmt = stmt.where(
                (User.username.ilike(search_term)) |
                (User.email.ilike(search_term)) |
                (User.first_name.ilike(search_term)) |
                (User.last_name.ilike(search_term))
            )

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_count = await db.scalar(count_stmt)

    # Apply pagination
    limit = 10
    offset = 0

    if pagination:
        limit = pagination.get("first", 10)
        if pagination.get("after"):
            # Simple offset-based pagination
            offset = int(pagination["after"])

    stmt = stmt.limit(limit).offset(offset)

    # Execute query
    result = await db.execute(stmt)
    users = result.scalars().all()

    # Build connection response
    return {
        "nodes": users,
        "pageInfo": {
            "hasNextPage": offset + limit < total_count,
            "hasPreviousPage": offset > 0,
            "startCursor": str(offset) if offset > 0 else None,
            "endCursor": str(offset + limit) if offset + limit < total_count else None
        },
        "totalCount": total_count
    }


# Course resolvers
@query.field("course")
async def resolve_course(obj, info, id: str) -> Optional[Course]:
    """Get course by ID"""

    loader = info.context["loaders"]["course"]
    course_id = uuid.UUID(id)
    course = await loader.load(course_id)

    return course


@query.field("courses")
async def resolve_courses(
    obj,
    info,
    filter: Optional[Dict] = None,
    sort: Optional[Dict] = None,
    pagination: Optional[Dict] = None
) -> Dict[str, Any]:
    """List courses with filtering and pagination"""

    db = info.context["db"]

    # Build query with eager loading
    stmt = select(Course).options(
        selectinload(Course.teacher)
    )

    # Apply filters
    if filter:
        if filter.get("subject"):
            stmt = stmt.where(Course.subject == filter["subject"])
        if filter.get("difficulty"):
            stmt = stmt.where(Course.difficulty == filter["difficulty"])
        if filter.get("status"):
            stmt = stmt.where(Course.status == filter["status"])
        if filter.get("teacherId"):
            teacher_id = uuid.UUID(filter["teacherId"])
            stmt = stmt.where(Course.teacher_id == teacher_id)

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_count = await db.scalar(count_stmt)

    # Apply pagination
    limit = 10
    offset = 0

    if pagination:
        limit = pagination.get("first", 10)
        if pagination.get("after"):
            offset = int(pagination["after"])

    stmt = stmt.limit(limit).offset(offset)

    # Execute query
    result = await db.execute(stmt)
    courses = result.scalars().all()

    # Build connection response
    return {
        "nodes": courses,
        "pageInfo": {
            "hasNextPage": offset + limit < total_count,
            "hasPreviousPage": offset > 0,
            "startCursor": str(offset) if offset > 0 else None,
            "endCursor": str(offset + limit) if offset + limit < total_count else None
        },
        "totalCount": total_count
    }


@query.field("enrolledCourses")
async def resolve_enrolled_courses(
    obj,
    info,
    studentId: Optional[str] = None,
    status: Optional[str] = None,
    pagination: Optional[Dict] = None
) -> Dict[str, Any]:
    """Get courses enrolled by a student"""

    db = info.context["db"]
    user = info.context["user"]

    # Use current user if no studentId provided
    if not studentId:
        if not user:
            raise Exception("Not authenticated")
        student_id = user.id
    else:
        student_id = uuid.UUID(studentId)

    # Query enrollments
    stmt = select(Enrollment).options(
        selectinload(Enrollment.course)
    ).where(Enrollment.student_id == student_id)

    if status:
        stmt = stmt.where(Enrollment.status == status)

    result = await db.execute(stmt)
    enrollments = result.scalars().all()

    # Extract courses
    courses = [enrollment.course for enrollment in enrollments]

    return {
        "nodes": courses,
        "pageInfo": {
            "hasNextPage": False,
            "hasPreviousPage": False,
            "startCursor": None,
            "endCursor": None
        },
        "totalCount": len(courses)
    }


# Lesson resolvers
@query.field("lesson")
async def resolve_lesson(obj, info, id: str) -> Optional[Lesson]:
    """Get lesson by ID"""

    loader = info.context["loaders"]["lesson"]
    lesson_id = uuid.UUID(id)
    lesson = await loader.load(lesson_id)

    return lesson


@query.field("courseLessons")
async def resolve_course_lessons(
    obj,
    info,
    courseId: str,
    includeHidden: bool = False
) -> List[Lesson]:
    """Get lessons for a course"""

    db = info.context["db"]
    course_id = uuid.UUID(courseId)

    stmt = select(Lesson).where(Lesson.course_id == course_id)

    if not includeHidden:
        stmt = stmt.where(Lesson.status != "HIDDEN")

    stmt = stmt.order_by(Lesson.order)

    result = await db.execute(stmt)
    lessons = result.scalars().all()

    return lessons


# Quiz resolvers
@query.field("quiz")
async def resolve_quiz(obj, info, id: str) -> Optional[Quiz]:
    """Get quiz by ID"""

    loader = info.context["loaders"]["quiz"]
    quiz_id = uuid.UUID(id)
    quiz = await loader.load(quiz_id)

    return quiz


@query.field("courseQuizzes")
async def resolve_course_quizzes(
    obj,
    info,
    courseId: str,
    type: Optional[str] = None,
    status: Optional[str] = None,
    includeHidden: bool = False
) -> List[Quiz]:
    """Get quizzes for a course"""

    db = info.context["db"]
    course_id = uuid.UUID(courseId)

    stmt = select(Quiz).where(Quiz.course_id == course_id)

    if type:
        stmt = stmt.where(Quiz.type == type)

    if status:
        stmt = stmt.where(Quiz.status == status)

    result = await db.execute(stmt)
    quizzes = result.scalars().all()

    return quizzes
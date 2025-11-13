"""
Optimized Database Repositories

Provides repository pattern implementation with N+1 query prevention
and performance optimizations for all models.
"""

from typing import Any, TypeVar
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

try:
    from database.models import (
        Analytics,
        Content,
        Course,
        Enrollment,
        Lesson,
        Quiz,
        QuizAttempt,
        User,
        UserAchievement,
        UserProgress,
    )
except ImportError:
    # Try the root import path
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))
    from database.models import (
        Content,
        Course,
        Enrollment,
        Lesson,
        Quiz,
        QuizAttempt,
        User,
        UserProgress,
    )

from apps.backend.core.logging import log_database_operation, logging_manager

from .query_optimizer import DataLoader, QueryOptimizer, optimize_query

logger = logging_manager.get_logger(__name__)

T = TypeVar("T")


class BaseRepository:
    """Base repository with common database operations"""

    def __init__(self, session: AsyncSession, model: type[T]):
        self.session = session
        self.model = model
        self.optimizer = QueryOptimizer()
        self.data_loader = DataLoader(session)

    @log_database_operation("SELECT")
    async def get_by_id(
        self,
        id: UUID,
        relationships: list[str] | None = None,
        columns: list[str] | None = None,
    ) -> T | None:
        """
        Get entity by ID with optional eager loading

        Args:
            id: Entity ID
            relationships: Relationships to eager load
            columns: Specific columns to select

        Returns:
            Entity or None
        """
        query = select(self.model).where(self.model.id == id)

        if relationships:
            query = self.optimizer.optimize_relationships(query, self.model, relationships)

        if columns:
            query = self.optimizer.select_columns(query, self.model, columns)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    @log_database_operation("SELECT")
    async def get_many(self, ids: list[UUID], relationships: list[str] | None = None) -> list[T]:
        """
        Get multiple entities by IDs with batch loading

        Args:
            ids: List of entity IDs
            relationships: Relationships to eager load

        Returns:
            List of entities
        """
        return await self.data_loader.load_many(self.model, ids, relationships)

    @log_database_operation("SELECT")
    async def get_all(
        self, limit: int = 100, offset: int = 0, relationships: list[str] | None = None
    ) -> list[T]:
        """
        Get all entities with pagination

        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            relationships: Relationships to eager load

        Returns:
            List of entities
        """
        query = select(self.model).limit(limit).offset(offset)

        if relationships:
            query = self.optimizer.optimize_relationships(query, self.model, relationships)

        result = await self.session.execute(query)
        return result.scalars().all()

    @log_database_operation("INSERT")
    async def create(self, **kwargs) -> T:
        """
        Create new entity

        Args:
            **kwargs: Entity attributes

        Returns:
            Created entity
        """
        entity = self.model(**kwargs)
        self.session.add(entity)
        await self.session.flush()
        return entity

    @log_database_operation("UPDATE")
    async def update(self, id: UUID, **kwargs) -> T | None:
        """
        Update entity by ID

        Args:
            id: Entity ID
            **kwargs: Attributes to update

        Returns:
            Updated entity or None
        """
        entity = await self.get_by_id(id)
        if entity:
            for key, value in kwargs.items():
                setattr(entity, key, value)
            await self.session.flush()
        return entity

    @log_database_operation("DELETE")
    async def delete(self, id: UUID) -> bool:
        """
        Delete entity by ID

        Args:
            id: Entity ID

        Returns:
            True if deleted, False if not found
        """
        entity = await self.get_by_id(id)
        if entity:
            await self.session.delete(entity)
            await self.session.flush()
            return True
        return False

    @log_database_operation("COUNT")
    async def count(self, **filters) -> int:
        """
        Count entities with optional filters

        Args:
            **filters: Filter conditions

        Returns:
            Count of entities
        """
        query = select(func.count(self.model.id))

        for key, value in filters.items():
            query = query.where(getattr(self.model, key) == value)

        result = await self.session.execute(query)
        return result.scalar() or 0


class UserRepository(BaseRepository):
    """Optimized repository for User model"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    @optimize_query(relationships=["enrollments", "achievements"], cache_ttl=60)
    async def get_user_with_enrollments(self, user_id: UUID) -> User | None:
        """Get user with enrollments and achievements (optimized)"""
        query = (
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.enrollments).selectinload(Enrollment.course),
                selectinload(User.achievements),
            )
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    @optimize_query(cache_ttl=300)
    async def get_users_by_role(self, role: str, limit: int = 100, offset: int = 0) -> list[User]:
        """Get users by role with pagination"""
        query = (
            select(User)
            .where(User.role == role)
            .limit(limit)
            .offset(offset)
            .options(load_only(User.id, User.email, User.username, User.role))
        )

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_user_dashboard_data(self, user_id: UUID) -> dict[str, Any]:
        """Get optimized dashboard data for user (prevents N+1)"""
        # Single query with all needed relationships
        query = (
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.enrollments).selectinload(Enrollment.course),
                selectinload(User.progress_records).selectinload(UserProgress.lesson),
                selectinload(User.quiz_attempts).selectinload(QuizAttempt.quiz),
                selectinload(User.achievements),
            )
        )

        result = await self.session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return {}

        # Process data without additional queries
        return {
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "role": user.role.value,
            },
            "enrollments": [
                {
                    "course_id": str(e.course_id),
                    "course_name": e.course.title,
                    "enrolled_at": e.enrolled_at.isoformat(),
                }
                for e in user.enrollments
            ],
            "progress": [
                {
                    "lesson_id": str(p.lesson_id),
                    "lesson_title": p.lesson.title,
                    "progress_percentage": p.progress_percentage,
                    "completed": p.completed,
                }
                for p in user.progress_records
            ],
            "recent_quizzes": [
                {
                    "quiz_id": str(q.quiz_id),
                    "quiz_title": q.quiz.title,
                    "score": q.score,
                    "attempted_at": q.attempted_at.isoformat(),
                }
                for q in sorted(user.quiz_attempts, key=lambda x: x.attempted_at, reverse=True)[:5]
            ],
            "achievements": [
                {"id": str(a.id), "title": a.title, "earned_at": a.earned_at.isoformat()}
                for a in user.achievements
            ],
        }


class CourseRepository(BaseRepository):
    """Optimized repository for Course model"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Course)

    @optimize_query(relationships=["lessons", "enrollments"])
    async def get_course_with_lessons(self, course_id: UUID) -> Course | None:
        """Get course with all lessons (optimized)"""
        query = (
            select(Course)
            .where(Course.id == course_id)
            .options(
                selectinload(Course.lessons).selectinload(Lesson.content_items),
                selectinload(Course.lessons).selectinload(Lesson.quizzes),
            )
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_courses_with_enrollment_count(
        self, limit: int = 20, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Get courses with enrollment count (single query)"""
        # Use subquery for enrollment count
        enrollment_count_subquery = (
            select(Enrollment.course_id, func.count(Enrollment.id).label("enrollment_count"))
            .group_by(Enrollment.course_id)
            .subquery()
        )

        # Main query with join
        query = (
            select(
                Course,
                func.coalesce(enrollment_count_subquery.c.enrollment_count, 0).label(
                    "enrollment_count"
                ),
            )
            .outerjoin(
                enrollment_count_subquery, Course.id == enrollment_count_subquery.c.course_id
            )
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(query)

        courses_with_count = []
        for row in result:
            course = row[0]
            enrollment_count = row[1]
            courses_with_count.append(
                {
                    "id": str(course.id),
                    "title": course.title,
                    "code": course.code,
                    "subject": course.subject,
                    "grade_level": course.grade_level,
                    "enrollment_count": enrollment_count,
                }
            )

        return courses_with_count


class LessonRepository(BaseRepository):
    """Optimized repository for Lesson model"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Lesson)

    async def get_lessons_with_content(self, course_id: UUID) -> list[Lesson]:
        """Get all lessons for a course with content (prevents N+1)"""
        query = (
            select(Lesson)
            .where(Lesson.course_id == course_id)
            .options(
                selectinload(Lesson.content_items),
                selectinload(Lesson.quizzes).selectinload(Quiz.questions),
            )
            .order_by(Lesson.order_index)
        )

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_lesson_complete_data(self, lesson_id: UUID) -> dict[str, Any]:
        """Get complete lesson data in single query"""
        query = (
            select(Lesson)
            .where(Lesson.id == lesson_id)
            .options(
                joinedload(Lesson.course),
                selectinload(Lesson.content_items),
                selectinload(Lesson.quizzes).selectinload(Quiz.questions),
                selectinload(Lesson.progress_records),
            )
        )

        result = await self.session.execute(query)
        lesson = result.scalar_one_or_none()

        if not lesson:
            return {}

        return {
            "lesson": {
                "id": str(lesson.id),
                "title": lesson.title,
                "description": lesson.description,
                "order_index": lesson.order_index,
                "difficulty": lesson.difficulty.value if lesson.difficulty else None,
            },
            "course": {"id": str(lesson.course.id), "title": lesson.course.title},
            "content": [
                {"id": str(c.id), "title": c.title, "type": c.content_type, "data": c.content_data}
                for c in lesson.content_items
            ],
            "quizzes": [
                {
                    "id": str(q.id),
                    "title": q.title,
                    "question_count": len(q.questions) if hasattr(q, "questions") else 0,
                }
                for q in lesson.quizzes
            ],
            "student_count": len(lesson.progress_records),
        }


class ContentRepository(BaseRepository):
    """Optimized repository for Content model"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Content)

    async def get_content_by_status(self, status: str, limit: int = 50) -> list[Content]:
        """Get content by status with creator info"""
        query = (
            select(Content)
            .where(Content.status == status)
            .options(joinedload(Content.creator), joinedload(Content.lesson))
            .limit(limit)
        )

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_ai_generated_content(
        self, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Get AI-generated content with metadata"""
        query = (
            select(Content)
            .where(Content.ai_generated == True)
            .options(selectinload(Content.lesson), selectinload(Content.creator))
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(query)
        content_items = result.scalars().all()

        return [
            {
                "id": str(c.id),
                "title": c.title,
                "type": c.content_type,
                "ai_model": c.ai_model,
                "lesson_title": c.lesson.title if c.lesson else None,
                "creator_name": c.creator.username if c.creator else "System",
                "created_at": c.created_at.isoformat(),
            }
            for c in content_items
        ]


class ProgressRepository(BaseRepository):
    """Optimized repository for UserProgress model"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, UserProgress)

    async def get_user_course_progress(self, user_id: UUID, course_id: UUID) -> dict[str, Any]:
        """Get user's progress for entire course (optimized)"""
        # Get course with lessons
        course_query = (
            select(Course).where(Course.id == course_id).options(selectinload(Course.lessons))
        )

        course_result = await self.session.execute(course_query)
        course = course_result.scalar_one_or_none()

        if not course:
            return {}

        lesson_ids = [lesson.id for lesson in course.lessons]

        # Get all progress records for user in this course
        progress_query = select(UserProgress).where(
            and_(UserProgress.user_id == user_id, UserProgress.lesson_id.in_(lesson_ids))
        )

        progress_result = await self.session.execute(progress_query)
        progress_records = progress_result.scalars().all()

        # Calculate statistics
        progress_by_lesson = {p.lesson_id: p for p in progress_records}

        total_lessons = len(course.lessons)
        completed_lessons = sum(1 for p in progress_records if p.completed)

        total_progress = sum(p.progress_percentage for p in progress_records)

        return {
            "course_id": str(course_id),
            "course_title": course.title,
            "total_lessons": total_lessons,
            "completed_lessons": completed_lessons,
            "overall_progress": (total_progress / total_lessons if total_lessons > 0 else 0),
            "lessons": [
                {
                    "lesson_id": str(lesson.id),
                    "lesson_title": lesson.title,
                    "progress": (
                        progress_by_lesson[lesson.id].progress_percentage
                        if lesson.id in progress_by_lesson
                        else 0
                    ),
                    "completed": (
                        progress_by_lesson[lesson.id].completed
                        if lesson.id in progress_by_lesson
                        else False
                    ),
                }
                for lesson in sorted(course.lessons, key=lambda l: l.order_index)
            ],
        }


# Export repository classes
__all__ = [
    "BaseRepository",
    "UserRepository",
    "CourseRepository",
    "LessonRepository",
    "ContentRepository",
    "ProgressRepository",
]

"""
DataLoaders for batch loading and N+1 query prevention
"""

import uuid
from typing import List, Dict, Any, Optional
from collections import defaultdict

from aiodataloader import DataLoader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.models import User, Course, Lesson, Quiz, Enrollment


class UserLoader(DataLoader):
    """DataLoader for batch loading users"""

    def __init__(self, db: AsyncSession):
        super().__init__()
        self.db = db

    async def batch_load_fn(self, user_ids: List[uuid.UUID]) -> List[Optional[User]]:
        """Batch load users by IDs"""

        # Query all users with matching IDs
        stmt = select(User).where(User.id.in_(user_ids))
        result = await self.db.execute(stmt)
        users = result.scalars().all()

        # Create mapping of ID to user
        user_map = {user.id: user for user in users}

        # Return users in the same order as requested IDs
        return [user_map.get(user_id) for user_id in user_ids]


class CourseLoader(DataLoader):
    """DataLoader for batch loading courses"""

    def __init__(self, db: AsyncSession):
        super().__init__()
        self.db = db

    async def batch_load_fn(self, course_ids: List[uuid.UUID]) -> List[Optional[Course]]:
        """Batch load courses by IDs"""

        # Query all courses with matching IDs
        stmt = select(Course).where(Course.id.in_(course_ids))
        result = await self.db.execute(stmt)
        courses = result.scalars().all()

        # Create mapping of ID to course
        course_map = {course.id: course for course in courses}

        # Return courses in the same order as requested IDs
        return [course_map.get(course_id) for course_id in course_ids]


class LessonLoader(DataLoader):
    """DataLoader for batch loading lessons"""

    def __init__(self, db: AsyncSession):
        super().__init__()
        self.db = db

    async def batch_load_fn(self, lesson_ids: List[uuid.UUID]) -> List[Optional[Lesson]]:
        """Batch load lessons by IDs"""

        # Query all lessons with matching IDs
        stmt = select(Lesson).where(Lesson.id.in_(lesson_ids))
        result = await self.db.execute(stmt)
        lessons = result.scalars().all()

        # Create mapping of ID to lesson
        lesson_map = {lesson.id: lesson for lesson in lessons}

        # Return lessons in the same order as requested IDs
        return [lesson_map.get(lesson_id) for lesson_id in lesson_ids]


class QuizLoader(DataLoader):
    """DataLoader for batch loading quizzes"""

    def __init__(self, db: AsyncSession):
        super().__init__()
        self.db = db

    async def batch_load_fn(self, quiz_ids: List[uuid.UUID]) -> List[Optional[Quiz]]:
        """Batch load quizzes by IDs"""

        # Query all quizzes with matching IDs
        stmt = select(Quiz).where(Quiz.id.in_(quiz_ids))
        result = await self.db.execute(stmt)
        quizzes = result.scalars().all()

        # Create mapping of ID to quiz
        quiz_map = {quiz.id: quiz for quiz in quizzes}

        # Return quizzes in the same order as requested IDs
        return [quiz_map.get(quiz_id) for quiz_id in quiz_ids]


class EnrollmentLoader(DataLoader):
    """DataLoader for batch loading enrollments by course"""

    def __init__(self, db: AsyncSession):
        super().__init__()
        self.db = db

    async def batch_load_fn(self, course_ids: List[uuid.UUID]) -> List[List[Enrollment]]:
        """Batch load enrollments for multiple courses"""

        # Query all enrollments for the given course IDs
        stmt = select(Enrollment).where(
            Enrollment.course_id.in_(course_ids)
        ).options(selectinload(Enrollment.student))

        result = await self.db.execute(stmt)
        enrollments = result.scalars().all()

        # Group enrollments by course ID
        enrollment_map = defaultdict(list)
        for enrollment in enrollments:
            enrollment_map[enrollment.course_id].append(enrollment)

        # Return enrollments in the same order as requested course IDs
        return [enrollment_map.get(course_id, []) for course_id in course_ids]


class StudentEnrollmentLoader(DataLoader):
    """DataLoader for batch loading enrollments by student"""

    def __init__(self, db: AsyncSession):
        super().__init__()
        self.db = db

    async def batch_load_fn(self, student_ids: List[uuid.UUID]) -> List[List[Enrollment]]:
        """Batch load enrollments for multiple students"""

        # Query all enrollments for the given student IDs
        stmt = select(Enrollment).where(
            Enrollment.student_id.in_(student_ids)
        ).options(selectinload(Enrollment.course))

        result = await self.db.execute(stmt)
        enrollments = result.scalars().all()

        # Group enrollments by student ID
        enrollment_map = defaultdict(list)
        for enrollment in enrollments:
            enrollment_map[enrollment.student_id].append(enrollment)

        # Return enrollments in the same order as requested student IDs
        return [enrollment_map.get(student_id, []) for student_id in student_ids]


def create_loaders(db: AsyncSession) -> Dict[str, DataLoader]:
    """
    Create all DataLoader instances for a request

    Args:
        db: Database session

    Returns:
        Dictionary of DataLoader instances
    """

    return {
        "user": UserLoader(db),
        "course": CourseLoader(db),
        "lesson": LessonLoader(db),
        "quiz": QuizLoader(db),
        "enrollment": EnrollmentLoader(db),
        "student_enrollment": StudentEnrollmentLoader(db),
    }
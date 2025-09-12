"""
Repository Pattern Implementation for Database CRUD Operations

Provides clean abstraction layer for database operations with async support,
validation, and business logic separation.
"""

import uuid
from typing import Optional, List, Dict, Any, Generic, TypeVar, Type
from datetime import datetime, timezone
from abc import ABC, abstractmethod

from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import IntegrityError, NoResultFound

from core.database.models import (
    Base, User, Course, Lesson, Content, Quiz, QuizQuestion,
    QuizAttempt, QuizResponse, UserProgress, Analytics,
    Achievement, UserAchievement, Leaderboard, Enrollment,
    UserRole, ContentStatus, DifficultyLevel
)
from server.auth import hash_password, verify_password

import logging

logger = logging.getLogger(__name__)

# Generic type for models
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(ABC, Generic[ModelType]):
    """Base repository with common CRUD operations"""
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """
        Initialize repository
        
        Args:
            model: SQLAlchemy model class
            session: Database session
        """
        self.model = model
        self.session = session
    
    async def get(self, id: uuid.UUID) -> Optional[ModelType]:
        """Get single record by ID"""
        stmt = select(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> List[ModelType]:
        """Get all records with optional filtering and pagination"""
        stmt = select(self.model)
        
        # Apply filters
        for key, value in filters.items():
            if hasattr(self.model, key) and value is not None:
                stmt = stmt.where(getattr(self.model, key) == value)
        
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def create(self, **data) -> ModelType:
        """Create new record"""
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.flush()
        return instance
    
    async def update(self, id: uuid.UUID, **data) -> Optional[ModelType]:
        """Update existing record"""
        instance = await self.get(id)
        if instance:
            for key, value in data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await self.session.flush()
        return instance
    
    async def delete(self, id: uuid.UUID) -> bool:
        """Delete record"""
        stmt = delete(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0
    
    async def count(self, **filters) -> int:
        """Count records with optional filtering"""
        stmt = select(func.count()).select_from(self.model)
        
        for key, value in filters.items():
            if hasattr(self.model, key) and value is not None:
                stmt = stmt.where(getattr(self.model, key) == value)
        
        result = await self.session.execute(stmt)
        return result.scalar() or 0
    
    async def exists(self, **filters) -> bool:
        """Check if record exists"""
        stmt = select(self.model.id)
        
        for key, value in filters.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)
        
        stmt = stmt.limit(1)
        result = await self.session.execute(stmt)
        return result.scalar() is not None


class UserRepository(BaseRepository[User]):
    """Repository for User operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)
    
    async def create_user(
        self,
        email: str,
        username: str,
        password: str,
        role: UserRole = UserRole.STUDENT,
        **kwargs
    ) -> User:
        """Create new user with hashed password"""
        # Check if user exists
        if await self.exists(email=email):
            raise IntegrityError("Email already exists", None, None)
        if await self.exists(username=username):
            raise IntegrityError("Username already exists", None, None)
        
        # Hash password
        password_hash = hash_password(password)
        
        # Create user
        user = await self.create(
            email=email,
            username=username,
            password_hash=password_hash,
            role=role,
            **kwargs
        )
        
        # Create initial leaderboard entry
        leaderboard = Leaderboard(user_id=user.id)
        self.session.add(leaderboard)
        await self.session.flush()
        
        return user
    
    async def authenticate(
        self,
        username_or_email: str,
        password: str
    ) -> Optional[User]:
        """Authenticate user by username/email and password"""
        # Try to find user by email or username
        stmt = select(User).where(
            or_(
                User.email == username_or_email,
                User.username == username_or_email
            )
        )
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user and verify_password(password, user.password_hash):
            # Update last login
            user.last_login = datetime.now(timezone.utc)
            user.failed_login_attempts = 0
            await self.session.flush()
            return user
        elif user:
            # Track failed attempt
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                # Lock account for 15 minutes
                from datetime import timedelta
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
            await self.session.flush()
        
        return None
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_roblox_id(self, roblox_user_id: str) -> Optional[User]:
        """Get user by Roblox user ID"""
        stmt = select(User).where(User.roblox_user_id == roblox_user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_with_progress(self, user_id: uuid.UUID) -> Optional[User]:
        """Get user with progress records loaded"""
        stmt = select(User).options(
            selectinload(User.progress_records),
            selectinload(User.achievements)
        ).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class CourseRepository(BaseRepository[Course]):
    """Repository for Course operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Course, session)
    
    async def get_with_lessons(self, course_id: uuid.UUID) -> Optional[Course]:
        """Get course with all lessons loaded"""
        stmt = select(Course).options(
            selectinload(Course.lessons)
        ).where(Course.id == course_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_code(self, code: str) -> Optional[Course]:
        """Get course by code"""
        stmt = select(Course).where(Course.code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_subject_grade(
        self,
        subject: str,
        grade_level: int
    ) -> List[Course]:
        """Get courses by subject and grade level"""
        stmt = select(Course).where(
            and_(
                Course.subject == subject,
                Course.grade_level == grade_level,
                Course.is_active == True
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_user_courses(self, user_id: uuid.UUID) -> List[Course]:
        """Get all courses enrolled by a user"""
        stmt = select(Course).join(Enrollment).where(
            Enrollment.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class LessonRepository(BaseRepository[Lesson]):
    """Repository for Lesson operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Lesson, session)
    
    async def get_with_content(self, lesson_id: uuid.UUID) -> Optional[Lesson]:
        """Get lesson with all content loaded"""
        stmt = select(Lesson).options(
            selectinload(Lesson.content_items),
            selectinload(Lesson.quizzes)
        ).where(Lesson.id == lesson_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_course(
        self,
        course_id: uuid.UUID,
        only_published: bool = True
    ) -> List[Lesson]:
        """Get all lessons for a course"""
        stmt = select(Lesson).where(Lesson.course_id == course_id)
        
        if only_published:
            stmt = stmt.where(Lesson.is_published == True)
        
        stmt = stmt.order_by(Lesson.order_index)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_next_lesson(
        self,
        course_id: uuid.UUID,
        current_order: int
    ) -> Optional[Lesson]:
        """Get next lesson in sequence"""
        stmt = select(Lesson).where(
            and_(
                Lesson.course_id == course_id,
                Lesson.order_index > current_order,
                Lesson.is_published == True
            )
        ).order_by(Lesson.order_index).limit(1)
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class ContentRepository(BaseRepository[Content]):
    """Repository for Content operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Content, session)
    
    async def get_by_lesson(
        self,
        lesson_id: uuid.UUID,
        content_type: Optional[str] = None,
        status: Optional[ContentStatus] = None
    ) -> List[Content]:
        """Get content items for a lesson"""
        stmt = select(Content).where(Content.lesson_id == lesson_id)
        
        if content_type:
            stmt = stmt.where(Content.content_type == content_type)
        if status:
            stmt = stmt.where(Content.status == status)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def approve_content(
        self,
        content_id: uuid.UUID,
        reviewer_id: uuid.UUID,
        quality_score: float,
        notes: Optional[str] = None
    ) -> Optional[Content]:
        """Approve content item"""
        content = await self.get(content_id)
        if content:
            content.status = ContentStatus.APPROVED
            content.reviewed_by_id = reviewer_id
            content.quality_score = quality_score
            content.review_notes = notes
            content.approved_at = datetime.now(timezone.utc)
            await self.session.flush()
        return content


class QuizRepository(BaseRepository[Quiz]):
    """Repository for Quiz operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Quiz, session)
    
    async def get_with_questions(self, quiz_id: uuid.UUID) -> Optional[Quiz]:
        """Get quiz with all questions loaded"""
        stmt = select(Quiz).options(
            selectinload(Quiz.questions)
        ).where(Quiz.id == quiz_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_lesson(self, lesson_id: uuid.UUID) -> List[Quiz]:
        """Get all quizzes for a lesson"""
        stmt = select(Quiz).where(
            and_(
                Quiz.lesson_id == lesson_id,
                Quiz.is_active == True
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def create_quiz_attempt(
        self,
        quiz_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> QuizAttempt:
        """Create new quiz attempt"""
        # Get attempt number
        stmt = select(func.count()).select_from(QuizAttempt).where(
            and_(
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.user_id == user_id
            )
        )
        result = await self.session.execute(stmt)
        attempt_number = (result.scalar() or 0) + 1
        
        # Create attempt
        attempt = QuizAttempt(
            quiz_id=quiz_id,
            user_id=user_id,
            attempt_number=attempt_number,
            started_at=datetime.now(timezone.utc),
            status="in_progress"
        )
        self.session.add(attempt)
        await self.session.flush()
        return attempt
    
    async def submit_quiz_response(
        self,
        attempt_id: uuid.UUID,
        question_id: uuid.UUID,
        user_answer: Any
    ) -> QuizResponse:
        """Submit answer for a quiz question"""
        # Get question to check answer
        stmt = select(QuizQuestion).where(QuizQuestion.id == question_id)
        result = await self.session.execute(stmt)
        question = result.scalar_one_or_none()
        
        if not question:
            raise ValueError("Question not found")
        
        # Check if answer is correct
        is_correct = user_answer == question.correct_answer
        points_earned = question.points if is_correct else 0
        
        # Create or update response
        stmt = select(QuizResponse).where(
            and_(
                QuizResponse.attempt_id == attempt_id,
                QuizResponse.question_id == question_id
            )
        )
        result = await self.session.execute(stmt)
        response = result.scalar_one_or_none()
        
        if response:
            response.user_answer = user_answer
            response.is_correct = is_correct
            response.points_earned = points_earned
        else:
            response = QuizResponse(
                attempt_id=attempt_id,
                question_id=question_id,
                user_answer=user_answer,
                is_correct=is_correct,
                points_earned=points_earned
            )
            self.session.add(response)
        
        await self.session.flush()
        return response
    
    async def complete_quiz_attempt(
        self,
        attempt_id: uuid.UUID
    ) -> Optional[QuizAttempt]:
        """Complete and score a quiz attempt"""
        # Get attempt with responses
        stmt = select(QuizAttempt).options(
            selectinload(QuizAttempt.responses),
            selectinload(QuizAttempt.quiz).selectinload(Quiz.questions)
        ).where(QuizAttempt.id == attempt_id)
        result = await self.session.execute(stmt)
        attempt = result.scalar_one_or_none()
        
        if not attempt:
            return None
        
        # Calculate score
        total_points = sum(q.points for q in attempt.quiz.questions)
        earned_points = sum(r.points_earned for r in attempt.responses)
        percentage = (earned_points / total_points * 100) if total_points > 0 else 0
        
        # Update attempt
        attempt.score = earned_points
        attempt.percentage = percentage
        attempt.passed = percentage >= attempt.quiz.passing_score
        attempt.completed_at = datetime.now(timezone.utc)
        attempt.time_taken = int(
            (attempt.completed_at - attempt.started_at).total_seconds()
        )
        attempt.status = "completed"
        
        await self.session.flush()
        return attempt


class ProgressRepository(BaseRepository[UserProgress]):
    """Repository for Progress tracking operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(UserProgress, session)
    
    async def get_or_create(
        self,
        user_id: uuid.UUID,
        lesson_id: uuid.UUID
    ) -> UserProgress:
        """Get or create progress record"""
        stmt = select(UserProgress).where(
            and_(
                UserProgress.user_id == user_id,
                UserProgress.lesson_id == lesson_id
            )
        )
        result = await self.session.execute(stmt)
        progress = result.scalar_one_or_none()
        
        if not progress:
            progress = UserProgress(
                user_id=user_id,
                lesson_id=lesson_id,
                started_at=datetime.now(timezone.utc),
                last_accessed_at=datetime.now(timezone.utc)
            )
            self.session.add(progress)
            await self.session.flush()
        else:
            progress.last_accessed_at = datetime.now(timezone.utc)
            await self.session.flush()
        
        return progress
    
    async def update_progress(
        self,
        user_id: uuid.UUID,
        lesson_id: uuid.UUID,
        progress_percentage: float,
        checkpoint: Optional[str] = None
    ) -> Optional[UserProgress]:
        """Update user progress for a lesson"""
        progress = await self.get_or_create(user_id, lesson_id)
        
        progress.progress_percentage = min(progress_percentage, 100)
        progress.last_accessed_at = datetime.now(timezone.utc)
        
        if checkpoint:
            progress.last_checkpoint = checkpoint
            if checkpoint not in (progress.checkpoints_completed or []):
                if not progress.checkpoints_completed:
                    progress.checkpoints_completed = []
                progress.checkpoints_completed.append(checkpoint)
        
        if progress_percentage >= 100:
            progress.completion_status = "completed"
            progress.completed_at = datetime.now(timezone.utc)
        elif progress_percentage > 0:
            progress.completion_status = "in_progress"
        
        await self.session.flush()
        return progress
    
    async def get_course_progress(
        self,
        user_id: uuid.UUID,
        course_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get overall course progress for a user"""
        # Get all lessons in course
        stmt = select(Lesson).where(Lesson.course_id == course_id)
        result = await self.session.execute(stmt)
        lessons = result.scalars().all()
        
        if not lessons:
            return {"progress": 0, "completed": 0, "total": 0}
        
        # Get progress for each lesson
        lesson_ids = [lesson.id for lesson in lessons]
        stmt = select(UserProgress).where(
            and_(
                UserProgress.user_id == user_id,
                UserProgress.lesson_id.in_(lesson_ids)
            )
        )
        result = await self.session.execute(stmt)
        progress_records = result.scalars().all()
        
        # Calculate overall progress
        total_progress = sum(p.progress_percentage for p in progress_records)
        completed = sum(1 for p in progress_records if p.completion_status == "completed")
        
        return {
            "progress": total_progress / len(lessons) if lessons else 0,
            "completed": completed,
            "total": len(lessons),
            "lessons": [
                {
                    "lesson_id": lesson.id,
                    "title": lesson.title,
                    "progress": next(
                        (p.progress_percentage for p in progress_records if p.lesson_id == lesson.id),
                        0
                    )
                }
                for lesson in lessons
            ]
        }


class AnalyticsRepository(BaseRepository[Analytics]):
    """Repository for Analytics operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Analytics, session)
    
    async def track_event(
        self,
        event_type: str,
        user_id: Optional[uuid.UUID] = None,
        event_data: Optional[Dict] = None,
        **kwargs
    ) -> Analytics:
        """Track an analytics event"""
        event = Analytics(
            user_id=user_id,
            event_type=event_type,
            event_data=event_data or {},
            **kwargs
        )
        self.session.add(event)
        await self.session.flush()
        return event
    
    async def get_user_analytics(
        self,
        user_id: uuid.UUID,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Analytics]:
        """Get analytics events for a user"""
        stmt = select(Analytics).where(Analytics.user_id == user_id)
        
        if event_type:
            stmt = stmt.where(Analytics.event_type == event_type)
        
        stmt = stmt.order_by(Analytics.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_event_statistics(
        self,
        event_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get statistics for an event type"""
        stmt = select(
            func.count(Analytics.id).label("count"),
            func.count(func.distinct(Analytics.user_id)).label("unique_users")
        ).where(Analytics.event_type == event_type)
        
        if start_date:
            stmt = stmt.where(Analytics.created_at >= start_date)
        if end_date:
            stmt = stmt.where(Analytics.created_at <= end_date)
        
        result = await self.session.execute(stmt)
        row = result.first()
        
        return {
            "event_type": event_type,
            "total_events": row.count if row else 0,
            "unique_users": row.unique_users if row else 0,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None
        }


class AchievementRepository(BaseRepository[Achievement]):
    """Repository for Achievement operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Achievement, session)
    
    async def check_user_achievements(
        self,
        user_id: uuid.UUID,
        user_stats: Dict[str, Any]
    ) -> List[Achievement]:
        """Check which achievements a user has earned"""
        # Get all active achievements
        stmt = select(Achievement).where(Achievement.is_active == True)
        result = await self.session.execute(stmt)
        all_achievements = result.scalars().all()
        
        # Get user's existing achievements
        stmt = select(UserAchievement.achievement_id).where(
            and_(
                UserAchievement.user_id == user_id,
                UserAchievement.completed == True
            )
        )
        result = await self.session.execute(stmt)
        completed_ids = set(result.scalars().all())
        
        # Check each achievement
        newly_earned = []
        for achievement in all_achievements:
            if achievement.id in completed_ids:
                continue
            
            # Check if requirements are met
            if self._check_requirements(achievement.requirements, user_stats):
                # Award achievement
                user_achievement = UserAchievement(
                    user_id=user_id,
                    achievement_id=achievement.id,
                    progress=100,
                    completed=True,
                    completed_at=datetime.now(timezone.utc)
                )
                self.session.add(user_achievement)
                newly_earned.append(achievement)
        
        if newly_earned:
            await self.session.flush()
        
        return newly_earned
    
    def _check_requirements(
        self,
        requirements: Dict[str, Any],
        user_stats: Dict[str, Any]
    ) -> bool:
        """Check if achievement requirements are met"""
        for key, required_value in requirements.items():
            user_value = user_stats.get(key, 0)
            
            if isinstance(required_value, dict):
                # Complex requirement (e.g., {"min": 10, "max": 20})
                if "min" in required_value and user_value < required_value["min"]:
                    return False
                if "max" in required_value and user_value > required_value["max"]:
                    return False
            elif user_value < required_value:
                return False
        
        return True


class LeaderboardRepository(BaseRepository[Leaderboard]):
    """Repository for Leaderboard operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Leaderboard, session)
    
    async def update_user_score(
        self,
        user_id: uuid.UUID,
        points: int,
        update_streak: bool = True
    ) -> Optional[Leaderboard]:
        """Update user's leaderboard entry"""
        stmt = select(Leaderboard).where(Leaderboard.user_id == user_id)
        result = await self.session.execute(stmt)
        entry = result.scalar_one_or_none()
        
        if not entry:
            entry = Leaderboard(user_id=user_id)
            self.session.add(entry)
        
        # Update scores
        entry.total_score += points
        entry.weekly_score += points
        entry.monthly_score += points
        
        # Update streak if needed
        if update_streak:
            today = datetime.now(timezone.utc).date()
            if entry.last_activity_date:
                days_diff = (today - entry.last_activity_date.date()).days
                if days_diff == 1:
                    entry.current_streak += 1
                    entry.longest_streak = max(entry.longest_streak, entry.current_streak)
                elif days_diff > 1:
                    entry.current_streak = 1
            else:
                entry.current_streak = 1
                entry.longest_streak = 1
            
            entry.last_activity_date = datetime.now(timezone.utc)
        
        await self.session.flush()
        return entry
    
    async def get_top_users(
        self,
        limit: int = 10,
        timeframe: str = "all"
    ) -> List[Dict[str, Any]]:
        """Get top users from leaderboard"""
        # Select score column based on timeframe
        if timeframe == "weekly":
            score_column = Leaderboard.weekly_score
        elif timeframe == "monthly":
            score_column = Leaderboard.monthly_score
        else:
            score_column = Leaderboard.total_score
        
        stmt = select(
            Leaderboard,
            User.username,
            User.display_name,
            User.avatar_url
        ).join(
            User, Leaderboard.user_id == User.id
        ).order_by(
            score_column.desc()
        ).limit(limit)
        
        result = await self.session.execute(stmt)
        rows = result.all()
        
        return [
            {
                "rank": idx + 1,
                "user_id": row.Leaderboard.user_id,
                "username": row.username,
                "display_name": row.display_name,
                "avatar_url": row.avatar_url,
                "score": getattr(row.Leaderboard, score_column.key),
                "total_score": row.Leaderboard.total_score,
                "current_streak": row.Leaderboard.current_streak,
                "achievements": row.Leaderboard.achievement_points
            }
            for idx, row in enumerate(rows)
        ]
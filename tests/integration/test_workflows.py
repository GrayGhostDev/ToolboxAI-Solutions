"""
Integration Tests for End-to-End Workflows

Tests complete workflows including content generation, agent coordination,
and database integration for the ToolboxAI platform.
"""

import asyncio
import pytest
from typing import Dict, Any, List
from datetime import datetime, timezone
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add project paths
import sys
from pathlib import Path
# Add parent directory for database imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
# Add current project for agent imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from core.database.connection import DatabaseManager, get_db
    from core.database.repositories import (
        UserRepository, CourseRepository, LessonRepository,
        QuizRepository, ProgressRepository, AnalyticsRepository
    )
    from core.database.models import Base, UserRole
except ImportError:
    # Fallback to mock implementations for testing
    from unittest.mock import Mock
    DatabaseManager = Mock
    get_db = Mock
    UserRepository = Mock
    CourseRepository = Mock
    LessonRepository = Mock
    QuizRepository = Mock
    ProgressRepository = Mock
    AnalyticsRepository = Mock
    Base = Mock
    Base.metadata = Mock
    Base.metadata.create_all = Mock
    UserRole = Mock
from core.agents.orchestrator import Orchestrator
from core.agents.supervisor import SupervisorAgent
from apps.backend.auth import JWTManager


@pytest.fixture
async def test_db():
    """Create test database session"""
    # Use in-memory SQLite for testing
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture
async def test_user(test_db):
    """Create test user"""
    user_repo = UserRepository(test_db)
    user = await user_repo.create_user(
        email="test@example.com",
        username="testuser",
        password="testpass123",
        role=UserRole.TEACHER,
        first_name="Test",
        last_name="User"
    )
    await test_db.commit()
    return user


@pytest.fixture
async def test_course(test_db, test_user):
    """Create test course"""
    course_repo = CourseRepository(test_db)
    course = await course_repo.create(
        title="Test Mathematics Course",
        code="MATH101",
        description="Introduction to Algebra",
        subject="Mathematics",
        grade_level=7,
        objectives=["Understand variables", "Solve equations"],
        max_students=30
    )
    await test_db.commit()
    return course


@pytest.fixture
async def test_lesson(test_db, test_course):
    """Create test lesson"""
    lesson_repo = LessonRepository(test_db)
    lesson = await lesson_repo.create(
        course_id=test_course.id,
        title="Introduction to Variables",
        description="Learn about algebraic variables",
        order_index=1,
        learning_objectives=["Define variables", "Use variables in expressions"],
        estimated_duration=45
    )
    await test_db.commit()
    return lesson


class TestContentGenerationWorkflow:
    """Test end-to-end content generation workflow"""
    
    @pytest.mark.asyncio
    async def test_complete_content_generation(self, test_db, test_user, test_course, test_lesson):
        """Test generating complete educational content"""
        # Initialize orchestrator
        orchestrator = Orchestrator()
        
        # Create content generation request
        request = {
            "user_id": str(test_user.id),
            "course_id": str(test_course.id),
            "lesson_id": str(test_lesson.id),
            "subject": "Mathematics",
            "grade_level": 7,
            "topic": "Variables and Expressions",
            "learning_objectives": [
                "Understand what variables represent",
                "Write algebraic expressions using variables"
            ],
            "environment_type": "classroom",
            "include_quiz": True,
            "include_terrain": True,
            "include_gamification": True
        }
        
        # Execute content generation
        result = await orchestrator.generate_educational_content(request)
        
        # Verify all components generated
        assert result["status"] == "success"
        assert "lesson_content" in result
        assert "quiz" in result
        assert "terrain" in result
        assert "gamification" in result
        
        # Verify content quality
        assert len(result["lesson_content"]) > 0
        assert len(result["quiz"]["questions"]) >= 5
        assert result["terrain"]["script"] is not None
        assert len(result["gamification"]["achievements"]) > 0
    
    @pytest.mark.asyncio
    async def test_content_persistence(self, test_db, test_lesson):
        """Test saving generated content to database"""
        from core.database.repositories import ContentRepository
        
        content_repo = ContentRepository(test_db)
        
        # Create content
        content = await content_repo.create(
            lesson_id=test_lesson.id,
            title="Variables Introduction",
            content_type="interactive",
            content_data={
                "slides": ["Introduction", "Examples", "Practice"],
                "activities": ["Variable matching", "Expression builder"]
            },
            ai_generated=True,
            ai_model="gpt-4",
            ai_parameters={"temperature": 0.7}
        )
        
        await test_db.commit()
        
        # Verify persistence
        retrieved = await content_repo.get(content.id)
        assert retrieved is not None
        assert retrieved.title == "Variables Introduction"
        assert retrieved.ai_generated is True
    
    @pytest.mark.asyncio
    async def test_content_approval_workflow(self, test_db, test_user, test_lesson):
        """Test content review and approval workflow"""
        from core.database.repositories import ContentRepository
        from core.database.models import ContentStatus
        
        content_repo = ContentRepository(test_db)
        
        # Create draft content
        content = await content_repo.create(
            lesson_id=test_lesson.id,
            title="Draft Lesson",
            content_type="lesson",
            content_data={"text": "Lesson content"},
            status=ContentStatus.DRAFT
        )
        
        await test_db.commit()
        
        # Submit for review
        content = await content_repo.update(
            content.id,
            status=ContentStatus.PENDING
        )
        
        # Approve content
        approved = await content_repo.approve_content(
            content_id=content.id,
            reviewer_id=test_user.id,
            quality_score=95.0,
            notes="Excellent content, approved for use"
        )
        
        await test_db.commit()
        
        assert approved.status == ContentStatus.APPROVED
        assert approved.quality_score == 95.0


class TestQuizWorkflow:
    """Test quiz creation and attempt workflow"""
    
    @pytest.mark.asyncio
    async def test_quiz_generation_and_attempt(self, test_db, test_user, test_lesson):
        """Test complete quiz workflow from generation to completion"""
        quiz_repo = QuizRepository(test_db)
        
        # Create quiz
        quiz = await quiz_repo.create(
            lesson_id=test_lesson.id,
            title="Variables Quiz",
            description="Test your understanding of variables",
            quiz_type="multiple_choice",
            passing_score=70.0,
            time_limit=600  # 10 minutes
        )
        
        # Add questions
        from core.database.models import QuizQuestion
        questions = [
            QuizQuestion(
                quiz_id=quiz.id,
                question_text="What is a variable in algebra?",
                question_type="multiple_choice",
                order_index=1,
                points=10,
                options=[
                    "A fixed number",
                    "A letter representing an unknown value",
                    "An equation",
                    "A graph"
                ],
                correct_answer=1
            ),
            QuizQuestion(
                quiz_id=quiz.id,
                question_text="Solve for x: x + 5 = 12",
                question_type="multiple_choice",
                order_index=2,
                points=10,
                options=["5", "6", "7", "8"],
                correct_answer=2
            )
        ]
        
        for question in questions:
            test_db.add(question)
        
        await test_db.commit()
        
        # Create quiz attempt
        attempt = await quiz_repo.create_quiz_attempt(
            quiz_id=quiz.id,
            user_id=test_user.id
        )
        
        # Submit answers
        await quiz_repo.submit_quiz_response(
            attempt_id=attempt.id,
            question_id=questions[0].id,
            user_answer=1  # Correct
        )
        
        await quiz_repo.submit_quiz_response(
            attempt_id=attempt.id,
            question_id=questions[1].id,
            user_answer=2  # Correct
        )
        
        # Complete attempt
        completed = await quiz_repo.complete_quiz_attempt(attempt.id)
        await test_db.commit()
        
        assert completed.percentage == 100.0
        assert completed.passed is True
        assert completed.score == 20  # Both questions correct
    
    @pytest.mark.asyncio
    async def test_adaptive_quiz_generation(self, test_db, test_user, test_lesson):
        """Test adaptive quiz generation based on user performance"""
        progress_repo = ProgressRepository(test_db)
        
        # Track initial progress
        progress = await progress_repo.update_progress(
            user_id=test_user.id,
            lesson_id=test_lesson.id,
            progress_percentage=50.0,
            checkpoint="quiz_started"
        )
        
        # Generate adaptive quiz based on progress
        orchestrator = Orchestrator()
        quiz_request = {
            "user_id": str(test_user.id),
            "lesson_id": str(test_lesson.id),
            "current_progress": progress.progress_percentage,
            "difficulty_adjustment": "adaptive"
        }
        
        quiz = await orchestrator.generate_adaptive_quiz(quiz_request)
        
        assert quiz is not None
        assert "questions" in quiz
        assert "difficulty_level" in quiz
        
        # Verify difficulty matches progress
        if progress.progress_percentage < 30:
            assert quiz["difficulty_level"] == "easy"
        elif progress.progress_percentage < 70:
            assert quiz["difficulty_level"] == "medium"
        else:
            assert quiz["difficulty_level"] == "hard"


class TestProgressTrackingWorkflow:
    """Test user progress tracking workflow"""
    
    @pytest.mark.asyncio
    async def test_lesson_progress_tracking(self, test_db, test_user, test_course, test_lesson):
        """Test tracking user progress through lessons"""
        progress_repo = ProgressRepository(test_db)
        
        # Start lesson
        progress = await progress_repo.get_or_create(
            user_id=test_user.id,
            lesson_id=test_lesson.id
        )
        
        # Update progress at checkpoints
        checkpoints = [
            ("introduction_viewed", 20.0),
            ("activity_1_completed", 40.0),
            ("activity_2_completed", 60.0),
            ("quiz_started", 70.0),
            ("quiz_completed", 90.0),
            ("lesson_summary_viewed", 100.0)
        ]
        
        for checkpoint, percentage in checkpoints:
            progress = await progress_repo.update_progress(
                user_id=test_user.id,
                lesson_id=test_lesson.id,
                progress_percentage=percentage,
                checkpoint=checkpoint
            )
            await test_db.commit()
            
            assert progress.progress_percentage == percentage
            assert checkpoint in progress.checkpoints_completed
        
        # Verify completion
        assert progress.completion_status == "completed"
        assert progress.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_course_progress_calculation(self, test_db, test_user, test_course):
        """Test calculating overall course progress"""
        lesson_repo = LessonRepository(test_db)
        progress_repo = ProgressRepository(test_db)
        
        # Create multiple lessons
        lessons = []
        for i in range(3):
            lesson = await lesson_repo.create(
                course_id=test_course.id,
                title=f"Lesson {i+1}",
                order_index=i+1
            )
            lessons.append(lesson)
        
        await test_db.commit()
        
        # Complete first two lessons
        for i, lesson in enumerate(lessons[:2]):
            await progress_repo.update_progress(
                user_id=test_user.id,
                lesson_id=lesson.id,
                progress_percentage=100.0
            )
        
        # Partial progress on third lesson
        await progress_repo.update_progress(
            user_id=test_user.id,
            lesson_id=lessons[2].id,
            progress_percentage=50.0
        )
        
        await test_db.commit()
        
        # Calculate course progress
        course_progress = await progress_repo.get_course_progress(
            user_id=test_user.id,
            course_id=test_course.id
        )
        
        # Should be (100 + 100 + 50) / 3 = 83.33%
        assert course_progress["progress"] == pytest.approx(83.33, rel=0.01)
        assert course_progress["completed"] == 2
        assert course_progress["total"] == 3


class TestAnalyticsWorkflow:
    """Test analytics tracking and reporting workflow"""
    
    @pytest.mark.asyncio
    async def test_event_tracking(self, test_db, test_user):
        """Test tracking various analytics events"""
        analytics_repo = AnalyticsRepository(test_db)
        
        # Track different event types
        events = [
            ("lesson_started", {"lesson_id": "123"}),
            ("quiz_completed", {"quiz_id": "456", "score": 85}),
            ("achievement_unlocked", {"achievement": "first_perfect_score"}),
            ("content_generated", {"type": "terrain", "theme": "forest"})
        ]
        
        tracked_events = []
        for event_type, event_data in events:
            event = await analytics_repo.track_event(
                event_type=event_type,
                user_id=test_user.id,
                event_data=event_data,
                event_category="learning"
            )
            tracked_events.append(event)
        
        await test_db.commit()
        
        # Retrieve user analytics
        user_events = await analytics_repo.get_user_analytics(
            user_id=test_user.id,
            limit=10
        )
        
        assert len(user_events) == len(events)
        
        # Get event statistics
        stats = await analytics_repo.get_event_statistics(
            event_type="quiz_completed"
        )
        
        assert stats["total_events"] == 1
        assert stats["unique_users"] == 1
    
    @pytest.mark.asyncio
    async def test_performance_analytics(self, test_db, test_user, test_course):
        """Test performance analytics generation"""
        analytics_repo = AnalyticsRepository(test_db)
        quiz_repo = QuizRepository(test_db)
        
        # Simulate multiple quiz attempts
        quiz_scores = [70, 80, 85, 90, 95]
        
        for score in quiz_scores:
            await analytics_repo.track_event(
                event_type="quiz_completed",
                user_id=test_user.id,
                event_data={
                    "course_id": str(test_course.id),
                    "score": score
                }
            )
        
        await test_db.commit()
        
        # Generate performance report
        events = await analytics_repo.get_user_analytics(
            user_id=test_user.id,
            event_type="quiz_completed"
        )
        
        scores = [e.event_data["score"] for e in events]
        average_score = sum(scores) / len(scores)
        improvement = scores[-1] - scores[0]
        
        assert average_score == 84.0
        assert improvement == 25  # 95 - 70


class TestDatabaseIntegration:
    """Test database transaction and relationship handling"""
    
    @pytest.mark.asyncio
    async def test_cascade_deletion(self, test_db, test_user, test_course, test_lesson):
        """Test cascade deletion of related records"""
        from core.database.repositories import ContentRepository, QuizRepository
        
        content_repo = ContentRepository(test_db)
        quiz_repo = QuizRepository(test_db)
        
        # Create related content and quiz
        content = await content_repo.create(
            lesson_id=test_lesson.id,
            title="Test Content",
            content_type="lesson",
            content_data={}
        )
        
        quiz = await quiz_repo.create(
            lesson_id=test_lesson.id,
            title="Test Quiz"
        )
        
        await test_db.commit()
        
        # Delete lesson (should cascade)
        lesson_repo = LessonRepository(test_db)
        await lesson_repo.delete(test_lesson.id)
        await test_db.commit()
        
        # Verify cascaded deletion
        assert await content_repo.get(content.id) is None
        assert await quiz_repo.get(quiz.id) is None
    
    @pytest.mark.asyncio
    async def test_transaction_rollback(self, test_db, test_user):
        """Test transaction rollback on error"""
        user_repo = UserRepository(test_db)
        
        try:
            async with test_db.begin():
                # Create user with duplicate email (should fail)
                await user_repo.create_user(
                    email=test_user.email,  # Duplicate
                    username="another_user",
                    password="password"
                )
                # This should not be reached
                assert False, "Should have raised IntegrityError"
        except Exception:
            # Transaction should be rolled back
            pass
        
        # Verify no new user was created
        all_users = await user_repo.get_all()
        assert len(all_users) == 1  # Only original test user


class TestAgentCoordination:
    """Test multi-agent coordination in workflows"""
    
    @pytest.mark.asyncio
    async def test_parallel_agent_execution(self):
        """Test parallel execution of multiple agents"""
        supervisor = SupervisorAgent()
        
        # Create multiple tasks
        tasks = [
            {"type": "content", "data": {"topic": "Algebra"}},
            {"type": "quiz", "data": {"num_questions": 5}},
            {"type": "terrain", "data": {"theme": "classroom"}},
            {"type": "script", "data": {"functionality": "quiz_ui"}}
        ]
        
        # Execute in parallel
        start_time = asyncio.get_event_loop().time()
        results = await supervisor.execute_parallel_tasks(tasks)
        execution_time = asyncio.get_event_loop().time() - start_time
        
        # Verify all tasks completed
        assert len(results) == len(tasks)
        for result in results:
            assert result["status"] == "success"
        
        # Verify parallel execution (should be faster than serial)
        # Assuming each task takes at least 0.5 seconds if serial
        assert execution_time < len(tasks) * 0.5
    
    @pytest.mark.asyncio
    async def test_agent_error_recovery(self):
        """Test agent error handling and recovery"""
        orchestrator = Orchestrator()
        
        # Create request that will cause an error
        invalid_request = {
            "subject": None,  # Invalid
            "grade_level": "invalid",  # Should be int
            "learning_objectives": []  # Empty
        }
        
        # Execute with error handling
        result = await orchestrator.generate_educational_content(invalid_request)
        
        # Should handle error gracefully
        assert result["status"] == "error"
        assert "error_message" in result
        assert "fallback_content" in result  # Should provide fallback


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
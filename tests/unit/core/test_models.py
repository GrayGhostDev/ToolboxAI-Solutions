"""
Unit tests for database models

Tests all SQLAlchemy models including EducationalContent/Content alias compatibility
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch

from core.database.models import (
    Base, User, UserRole, Course, Lesson, Content, EducationalContent,
    Quiz, QuizQuestion, ContentStatus, DifficultyLevel,
    Progress, Achievement, AchievementType, Session
)

class TestUserModel:
    """Test User model"""
    
    def test_user_creation(self):
        """Test creating a user instance"""
        user = User(
            email="test@example.com",
            username="testuser",
            password_hash="hashed_password",
            role=UserRole.STUDENT,
            is_active=True,
            is_verified=False
        )
        
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.role == UserRole.STUDENT
        assert user.is_active == True
        assert user.is_verified == False
    
    def test_user_roles(self):
        """Test different user roles"""
        roles = [UserRole.STUDENT, UserRole.TEACHER, UserRole.ADMIN, UserRole.PARENT]
        
        for role in roles:
            user = User(
                email=f"{role.value}@example.com",
                username=f"user_{role.value}",
                password_hash="hash",
                role=role
            )
            assert user.role == role
    
    def test_user_profile_fields(self):
        """Test user profile fields"""
        user = User(
            email="profile@example.com",
            username="profileuser",
            password_hash="hash",
            first_name="John",
            last_name="Doe",
            display_name="JohnD",
            avatar_url="https://example.com/avatar.jpg",
            bio="Test bio"
        )
        
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.display_name == "JohnD"
        assert user.avatar_url == "https://example.com/avatar.jpg"
        assert user.bio == "Test bio"
    
    def test_roblox_integration_fields(self):
        """Test Roblox integration fields"""
        user = User(
            email="roblox@example.com",
            username="robloxuser",
            password_hash="hash",
            roblox_user_id="123456",
            roblox_username="RobloxPlayer",
            roblox_verified=True
        )
        
        assert user.roblox_user_id == "123456"
        assert user.roblox_username == "RobloxPlayer"
        assert user.roblox_verified == True


class TestCourseModel:
    """Test Course model"""
    
    def test_course_creation(self):
        """Test creating a course"""
        course = Course(
            title="Mathematics 101",
            code="MATH101",
            description="Introduction to Mathematics",
            subject="Mathematics",
            grade_level=8,
            is_active=True,
            is_public=True
        )
        
        assert course.title == "Mathematics 101"
        assert course.code == "MATH101"
        assert course.subject == "Mathematics"
        assert course.grade_level == 8
        assert course.is_active == True
        assert course.is_public == True
    
    def test_course_metadata(self):
        """Test course metadata fields"""
        course = Course(
            title="Science",
            code="SCI101",
            subject="Science",
            grade_level=7,
            objectives=["Learn basics", "Understand concepts"],
            prerequisites=["Basic math"],
            tags=["science", "grade7", "basics"],
            max_students=30
        )
        
        assert len(course.objectives) == 2
        assert "Learn basics" in course.objectives
        assert len(course.prerequisites) == 1
        assert "science" in course.tags
        assert course.max_students == 30


class TestLessonModel:
    """Test Lesson model"""
    
    def test_lesson_creation(self):
        """Test creating a lesson"""
        lesson = Lesson(
            course_id=uuid.uuid4(),
            title="Introduction to Algebra",
            description="Learn the basics of algebra",
            order_index=1,
            difficulty=DifficultyLevel.BEGINNER,
            estimated_duration=45,
            content_type="interactive"
        )
        
        assert lesson.title == "Introduction to Algebra"
        assert lesson.order_index == 1
        assert lesson.difficulty == DifficultyLevel.BEGINNER
        assert lesson.estimated_duration == 45
        assert lesson.content_type == "interactive"
    
    def test_lesson_roblox_fields(self):
        """Test Roblox-specific lesson fields"""
        lesson = Lesson(
            course_id=uuid.uuid4(),
            title="Roblox Lesson",
            order_index=1,
            roblox_place_id="987654321",
            terrain_config={"type": "educational_world"}
        )
        
        assert lesson.roblox_place_id == "987654321"
        assert lesson.terrain_config["type"] == "educational_world"


class TestContentModel:
    """Test Content/EducationalContent model"""
    
    def test_content_creation(self):
        """Test creating content"""
        content = Content(
            lesson_id=uuid.uuid4(),
            title="Video: Introduction",
            content_type="video",
            content_data={"url": "https://example.com/video.mp4"},
            subject="Mathematics",
            grade_level=8,
            difficulty="intermediate",
            content_metadata={"duration": 300, "format": "mp4"}
        )
        
        assert content.title == "Video: Introduction"
        assert content.content_type == "video"
        assert content.subject == "Mathematics"
        assert content.grade_level == 8
        assert content.difficulty == "intermediate"
        assert "duration" in content.content_metadata
        assert content.content_metadata["duration"] == 300
    
    def test_educational_content_alias(self):
        """Test that EducationalContent is an alias for Content"""
        # Both should refer to the same class
        assert EducationalContent is Content
        
        # Should be able to create using either name
        content1 = Content(
            lesson_id=uuid.uuid4(),
            title="Content 1",
            content_type="document",
            content_data={}
        )
        
        content2 = EducationalContent(
            lesson_id=uuid.uuid4(),
            title="Content 2",
            content_type="activity",
            content_data={}
        )
        
        # Both should have the same table name
        assert content1.__tablename__ == content2.__tablename__
        assert content1.__tablename__ == "content"
    
    def test_content_ai_fields(self):
        """Test AI-generated content fields"""
        content = Content(
            lesson_id=uuid.uuid4(),
            title="AI Generated Quiz",
            content_type="quiz",
            content_data={},
            ai_generated=True,
            ai_model="gpt-4",
            ai_parameters={"temperature": 0.7, "max_tokens": 1000}
        )
        
        assert content.ai_generated == True
        assert content.ai_model == "gpt-4"
        assert content.ai_parameters["temperature"] == 0.7
    
    def test_content_review_fields(self):
        """Test content review and approval fields"""
        reviewer_id = uuid.uuid4()
        content = Content(
            lesson_id=uuid.uuid4(),
            title="Pending Content",
            content_type="document",
            content_data={},
            status=ContentStatus.PENDING,
            reviewed_by_id=reviewer_id,
            review_notes="Needs minor edits",
            quality_score=8.5
        )
        
        assert content.status == ContentStatus.PENDING
        assert content.reviewed_by_id == reviewer_id
        assert content.review_notes == "Needs minor edits"
        assert content.quality_score == 8.5
    
    def test_content_with_all_educational_fields(self):
        """Test content with all educational fields populated"""
        content = EducationalContent(
            lesson_id=uuid.uuid4(),
            creator_id=uuid.uuid4(),
            title="Complete Educational Content",
            content_type="interactive",
            content_data={
                "sections": ["intro", "main", "quiz"],
                "interactive_elements": True
            },
            subject="Science",
            grade_level=9,
            difficulty="advanced",
            content_metadata={
                "standards": ["NGSS", "Common Core"],
                "learning_objectives": ["Understand physics", "Apply formulas"],
                "estimated_time": 60
            },
            ai_generated=False,
            status=ContentStatus.APPROVED,
            quality_score=9.2
        )
        
        assert content.title == "Complete Educational Content"
        assert content.subject == "Science"
        assert content.grade_level == 9
        assert content.difficulty == "advanced"
        assert "standards" in content.content_metadata
        assert len(content.content_metadata["standards"]) == 2
        assert content.status == ContentStatus.APPROVED
        assert content.quality_score == 9.2


class TestQuizModel:
    """Test Quiz and QuizQuestion models"""
    
    def test_quiz_creation(self):
        """Test creating a quiz"""
        quiz = Quiz(
            lesson_id=uuid.uuid4(),
            title="Chapter 1 Quiz",
            description="Test your knowledge",
            quiz_type="multiple_choice",
            difficulty=DifficultyLevel.INTERMEDIATE,
            time_limit=1800,
            passing_score=75.0,
            max_attempts=3
        )
        
        assert quiz.title == "Chapter 1 Quiz"
        assert quiz.quiz_type == "multiple_choice"
        assert quiz.difficulty == DifficultyLevel.INTERMEDIATE
        assert quiz.time_limit == 1800
        assert quiz.passing_score == 75.0
        assert quiz.max_attempts == 3
    
    def test_quiz_settings(self):
        """Test quiz settings"""
        quiz = Quiz(
            lesson_id=uuid.uuid4(),
            title="Quiz",
            randomize_questions=False,
            randomize_answers=False,
            show_correct_answers=False,
            allow_review=False
        )
        
        assert quiz.randomize_questions == False
        assert quiz.randomize_answers == False
        assert quiz.show_correct_answers == False
        assert quiz.allow_review == False
    
    def test_quiz_question_creation(self):
        """Test creating quiz questions"""
        question = QuizQuestion(
            quiz_id=uuid.uuid4(),
            question_text="What is 2 + 2?",
            question_type="multiple_choice",
            order_index=1,
            points=1.0,
            options=["2", "3", "4", "5"],
            correct_answer={"answer": "4", "index": 2},
            explanation="2 + 2 equals 4",
            hints=["Think about counting", "Use your fingers"]
        )
        
        assert question.question_text == "What is 2 + 2?"
        assert question.question_type == "multiple_choice"
        assert question.order_index == 1
        assert question.points == 1.0
        assert len(question.options) == 4
        assert question.correct_answer["answer"] == "4"
        assert len(question.hints) == 2


class TestProgressModel:
    """Test Progress tracking model"""
    
    def test_progress_creation(self):
        """Test creating progress records"""
        progress = Progress(
            user_id=uuid.uuid4(),
            lesson_id=uuid.uuid4(),
            progress_percentage=75.0,
            time_spent=3600,
            completion_status="in_progress",
            last_accessed_at=datetime.utcnow()
        )
        
        assert progress.progress_percentage == 75.0
        assert progress.time_spent == 3600
        assert progress.completion_status == "in_progress"
        assert progress.last_accessed_at is not None


class TestAchievementModel:
    """Test Achievement model"""
    
    def test_achievement_creation(self):
        """Test creating achievements"""
        achievement = Achievement(
            name="First Quiz Completed",
            description="Complete your first quiz",
            achievement_type=AchievementType.MILESTONE,
            points=100,
            icon_url="https://example.com/badge.png",
            requirements={"type": "quiz_completion", "count": 1}
        )
        
        assert achievement.achievement_type == AchievementType.MILESTONE
        assert achievement.name == "First Quiz Completed"
        assert achievement.points == 100
        assert achievement.icon_url == "https://example.com/badge.png"
        assert achievement.requirements["type"] == "quiz_completion"


class TestSessionModel:
    """Test Session model"""
    
    def test_session_creation(self):
        """Test creating user sessions"""
        session = Session(
            user_id=uuid.uuid4(),
            session_token="token123",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            expires_at=datetime.utcnow()
        )
        
        assert session.session_token == "token123"
        assert session.ip_address == "192.168.1.1"
        assert session.user_agent == "Mozilla/5.0"
        assert session.expires_at is not None


# Integration test for model relationships
@pytest.mark.asyncio
async def test_model_relationships():
    """Test relationships between models"""
    # This would require a database session in a real test
    # For now, we just verify the relationships are defined
    
    # User relationships
    user = User(email="test@example.com", username="test", password_hash="hash")
    assert hasattr(user, 'courses_enrolled')
    assert hasattr(user, 'courses_teaching')
    assert hasattr(user, 'progress')
    assert hasattr(user, 'achievements')
    
    # Course relationships
    course = Course(title="Test", code="TEST", subject="Test", grade_level=1)
    assert hasattr(course, 'lessons')
    assert hasattr(course, 'enrolled_students')
    
    # Content relationships
    content = Content(lesson_id=uuid.uuid4(), title="Test", content_type="test", content_data={})
    assert hasattr(content, 'lesson')
    assert hasattr(content, 'creator')
    
    # Quiz relationships
    quiz = Quiz(lesson_id=uuid.uuid4(), title="Test Quiz")
    assert hasattr(quiz, 'questions')
    assert hasattr(quiz, 'attempts')
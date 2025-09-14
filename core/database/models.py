"""
SQLAlchemy Database Models for ToolboxAI Roblox Environment

Implements all database models with async SQLAlchemy ORM for:
- User management and authentication
- Educational content storage
- Progress tracking and analytics
- Quiz and assessment data
- Gamification elements
"""

import uuid
from datetime import datetime
from typing import Optional, List
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, JSON,
    ForeignKey, UniqueConstraint, Index, CheckConstraint, Enum
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func

Base = declarative_base()


# Enum Types
class UserRole(PyEnum):
    """User role enumeration"""
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"
    PARENT = "parent"


class ContentStatus(PyEnum):
    """Content approval status"""
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class DifficultyLevel(PyEnum):
    """Difficulty level for educational content"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class AchievementType(PyEnum):
    """Types of achievements"""
    MILESTONE = "milestone"
    STREAK = "streak"
    COMPLETION = "completion"
    MASTERY = "mastery"
    SPECIAL = "special"


# User Models
class User(Base):
    """Main user model for authentication and profile management"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.STUDENT, nullable=False)
    
    # Profile information
    first_name = Column(String(100))
    last_name = Column(String(100))
    display_name = Column(String(150))
    avatar_url = Column(String(500))
    bio = Column(Text)
    
    # Roblox integration
    roblox_user_id = Column(String(100), unique=True, index=True)
    roblox_username = Column(String(100))
    roblox_verified = Column(Boolean, default=False)
    
    # Settings and preferences
    preferences = Column(JSONB, default={})
    notification_settings = Column(JSONB, default={})
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime(timezone=True))
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    enrollments = relationship("Enrollment", back_populates="user", cascade="all, delete-orphan")
    progress_records = relationship("UserProgress", back_populates="user", cascade="all, delete-orphan")
    quiz_attempts = relationship("QuizAttempt", back_populates="user", cascade="all, delete-orphan")
    achievements = relationship("UserAchievement", back_populates="user", cascade="all, delete-orphan")
    created_content = relationship("Content", back_populates="creator", foreign_keys="Content.creator_id")
    analytics = relationship("Analytics", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_user_email_active', 'email', 'is_active'),
        Index('idx_user_roblox_id', 'roblox_user_id'),
    )


# Educational Content Models
class Course(Base):
    """Course/subject model"""
    __tablename__ = "courses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    subject = Column(String(100), nullable=False)
    grade_level = Column(Integer, nullable=False)
    
    # Course metadata
    objectives = Column(JSONB, default=[])
    prerequisites = Column(JSONB, default=[])
    tags = Column(ARRAY(String), default=[])
    
    # Configuration
    max_students = Column(Integer, default=30)
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=True)
    
    # Timestamps
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    lessons = relationship("Lesson", back_populates="course", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint('grade_level >= 1 AND grade_level <= 12'),
        Index('idx_course_subject_grade', 'subject', 'grade_level'),
    )


class Lesson(Base):
    """Individual lesson within a course"""
    __tablename__ = "lessons"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    order_index = Column(Integer, nullable=False)
    
    # Content configuration
    content_type = Column(String(50), default="interactive")
    difficulty = Column(Enum(DifficultyLevel), default=DifficultyLevel.INTERMEDIATE)
    estimated_duration = Column(Integer)  # in minutes
    
    # Educational content
    learning_objectives = Column(JSONB, default=[])
    content_data = Column(JSONB, default={})
    resources = Column(JSONB, default=[])
    
    # Roblox integration
    roblox_place_id = Column(String(100))
    terrain_config = Column(JSONB)
    game_mechanics = Column(JSONB)
    
    # Status
    is_published = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    published_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    course = relationship("Course", back_populates="lessons")
    content_items = relationship("Content", back_populates="lesson", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="lesson", cascade="all, delete-orphan")
    progress_records = relationship("UserProgress", back_populates="lesson", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('course_id', 'order_index'),
        Index('idx_lesson_course_order', 'course_id', 'order_index'),
    )


class Content(Base):
    """Educational content items (videos, documents, activities)"""
    __tablename__ = "content"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.id"), nullable=False)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    title = Column(String(200), nullable=False)
    content_type = Column(String(50), nullable=False)  # video, document, activity, etc.
    content_data = Column(JSONB, nullable=False)
    
    # Direct educational fields (for EducationalContent compatibility)
    subject = Column(String(100))
    grade_level = Column(Integer)
    difficulty = Column(String(20))
    content_metadata = Column(JSONB, default={})
    
    # AI-generated content metadata
    ai_generated = Column(Boolean, default=False)
    ai_model = Column(String(100))
    ai_parameters = Column(JSONB)
    
    # Review and approval
    status = Column(Enum(ContentStatus), default=ContentStatus.DRAFT)
    reviewed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    review_notes = Column(Text)
    quality_score = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    approved_at = Column(DateTime(timezone=True))
    
    # Relationships
    lesson = relationship("Lesson", back_populates="content_items")
    creator = relationship("User", back_populates="created_content", foreign_keys=[creator_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
    
    __table_args__ = (
        Index('idx_content_lesson_type', 'lesson_id', 'content_type'),
        Index('idx_content_status', 'status'),
        Index('idx_content_subject_grade', 'subject', 'grade_level'),
        Index('idx_content_difficulty', 'difficulty'),
    )


# Quiz and Assessment Models
class Quiz(Base):
    """Quiz/assessment model"""
    __tablename__ = "quizzes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Quiz configuration
    quiz_type = Column(String(50), default="multiple_choice")
    difficulty = Column(Enum(DifficultyLevel), default=DifficultyLevel.INTERMEDIATE)
    time_limit = Column(Integer)  # in seconds
    passing_score = Column(Float, default=70.0)
    max_attempts = Column(Integer, default=3)
    
    # Settings
    randomize_questions = Column(Boolean, default=True)
    randomize_answers = Column(Boolean, default=True)
    show_correct_answers = Column(Boolean, default=True)
    allow_review = Column(Boolean, default=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_published = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    lesson = relationship("Lesson", back_populates="quizzes")
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint('passing_score >= 0 AND passing_score <= 100'),
        Index('idx_quiz_lesson', 'lesson_id'),
    )


class QuizQuestion(Base):
    """Individual quiz questions"""
    __tablename__ = "quiz_questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id"), nullable=False)
    
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=False)  # multiple_choice, true_false, etc.
    order_index = Column(Integer, nullable=False)
    points = Column(Float, default=1.0)
    
    # Question content
    options = Column(JSONB)  # For multiple choice
    correct_answer = Column(JSONB, nullable=False)
    explanation = Column(Text)
    hints = Column(JSONB, default=[])
    
    # Media attachments
    image_url = Column(String(500))
    audio_url = Column(String(500))
    video_url = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    quiz = relationship("Quiz", back_populates="questions")
    responses = relationship("QuizResponse", back_populates="question", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('quiz_id', 'order_index'),
        CheckConstraint('points >= 0'),
    )


class QuizAttempt(Base):
    """User quiz attempt records"""
    __tablename__ = "quiz_attempts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    attempt_number = Column(Integer, nullable=False, default=1)
    score = Column(Float)
    percentage = Column(Float)
    passed = Column(Boolean, default=False)
    
    # Timing
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True))
    time_taken = Column(Integer)  # in seconds
    
    # Status
    status = Column(String(50), default="in_progress")  # in_progress, completed, abandoned
    
    # Relationships
    quiz = relationship("Quiz", back_populates="attempts")
    user = relationship("User", back_populates="quiz_attempts")
    responses = relationship("QuizResponse", back_populates="attempt", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('quiz_id', 'user_id', 'attempt_number'),
        Index('idx_attempt_user_quiz', 'user_id', 'quiz_id'),
    )


class QuizResponse(Base):
    """Individual question responses in a quiz attempt"""
    __tablename__ = "quiz_responses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attempt_id = Column(UUID(as_uuid=True), ForeignKey("quiz_attempts.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("quiz_questions.id"), nullable=False)
    
    user_answer = Column(JSONB)
    is_correct = Column(Boolean, default=False)
    points_earned = Column(Float, default=0)
    time_taken = Column(Integer)  # in seconds
    
    # Timestamps
    answered_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    attempt = relationship("QuizAttempt", back_populates="responses")
    question = relationship("QuizQuestion", back_populates="responses")
    
    __table_args__ = (
        UniqueConstraint('attempt_id', 'question_id'),
        Index('idx_response_attempt', 'attempt_id'),
    )


# Progress and Analytics Models
class UserProgress(Base):
    """User progress tracking for lessons"""
    __tablename__ = "user_progress"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.id"), nullable=False)
    
    # Progress metrics
    progress_percentage = Column(Float, default=0)
    time_spent = Column(Integer, default=0)  # in seconds
    completion_status = Column(String(50), default="not_started")  # not_started, in_progress, completed
    
    # Checkpoints
    checkpoints_completed = Column(JSONB, default=[])
    last_checkpoint = Column(String(100))
    
    # Timestamps
    started_at = Column(DateTime(timezone=True))
    last_accessed_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="progress_records")
    lesson = relationship("Lesson", back_populates="progress_records")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'lesson_id'),
        Index('idx_progress_user_lesson', 'user_id', 'lesson_id'),
        CheckConstraint('progress_percentage >= 0 AND progress_percentage <= 100'),
    )


class Analytics(Base):
    """Analytics and event tracking"""
    __tablename__ = "analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    event_type = Column(String(100), nullable=False)
    event_category = Column(String(100))
    event_data = Column(JSONB, default={})
    
    # Context
    session_id = Column(String(100))
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    platform = Column(String(50))
    
    # Roblox specific
    roblox_place_id = Column(String(100))
    roblox_server_id = Column(String(100))
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="analytics")
    
    __table_args__ = (
        Index('idx_analytics_user_event', 'user_id', 'event_type'),
        Index('idx_analytics_created', 'created_at'),
    )


# Gamification Models
class Achievement(Base):
    """Achievement definitions"""
    __tablename__ = "achievements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    
    # Achievement configuration
    achievement_type = Column(Enum(AchievementType), nullable=False)
    points = Column(Integer, default=10)
    icon_url = Column(String(500))
    badge_color = Column(String(7))  # Hex color
    
    # Requirements
    requirements = Column(JSONB, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_secret = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user_achievements = relationship("UserAchievement", back_populates="achievement", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_achievement_type', 'achievement_type'),
    )


class UserAchievement(Base):
    """User achievement records"""
    __tablename__ = "user_achievements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    achievement_id = Column(UUID(as_uuid=True), ForeignKey("achievements.id"), nullable=False)
    
    # Progress
    progress = Column(Float, default=0)
    completed = Column(Boolean, default=False)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="user_achievements")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'achievement_id'),
        Index('idx_user_achievement', 'user_id', 'achievement_id'),
        CheckConstraint('progress >= 0 AND progress <= 100'),
    )


class Leaderboard(Base):
    """Leaderboard entries"""
    __tablename__ = "leaderboard"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Scores
    total_score = Column(Integer, default=0)
    weekly_score = Column(Integer, default=0)
    monthly_score = Column(Integer, default=0)
    
    # Statistics
    lessons_completed = Column(Integer, default=0)
    quizzes_passed = Column(Integer, default=0)
    perfect_scores = Column(Integer, default=0)
    achievement_points = Column(Integer, default=0)
    
    # Streaks
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_activity_date = Column(DateTime(timezone=True))
    
    # Rankings (cached)
    global_rank = Column(Integer)
    grade_rank = Column(Integer)
    school_rank = Column(Integer)
    
    # Timestamps
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref=backref("leaderboard_entry", uselist=False))
    
    __table_args__ = (
        UniqueConstraint('user_id'),
        Index('idx_leaderboard_scores', 'total_score', 'weekly_score', 'monthly_score'),
    )


# Enrollment and Class Management
class Enrollment(Base):
    """Course enrollment records"""
    __tablename__ = "enrollments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    
    # Enrollment details
    enrollment_date = Column(DateTime(timezone=True), server_default=func.now())
    completion_date = Column(DateTime(timezone=True))
    status = Column(String(50), default="active")  # active, completed, dropped, suspended
    
    # Progress
    overall_progress = Column(Float, default=0)
    current_lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.id"))
    
    # Grades
    current_grade = Column(Float)
    final_grade = Column(Float)
    
    # Relationships
    user = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")
    current_lesson = relationship("Lesson")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'course_id'),
        Index('idx_enrollment_user_course', 'user_id', 'course_id'),
        CheckConstraint('overall_progress >= 0 AND overall_progress <= 100'),
    )


# Session Management
class Session(Base):
    """User session tracking"""
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Session data
    session_token = Column(String(255), unique=True, nullable=False)
    refresh_token = Column(String(255), unique=True)
    
    # Device information
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    platform = Column(String(50))
    
    # Roblox session
    roblox_session_id = Column(String(100))
    roblox_server_id = Column(String(100))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", backref="sessions")
    
    __table_args__ = (
        Index('idx_session_token', 'session_token'),
        Index('idx_session_user', 'user_id'),
        Index('idx_session_expires', 'expires_at'),
    )


class Class(Base):
    """Class/classroom model for educational grouping"""
    __tablename__ = "classes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    code = Column(String(20), unique=True, nullable=False)  # Class join code
    
    # Teacher information
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Course association
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"))
    
    # Settings
    grade_level = Column(String(50))
    subject = Column(String(100))
    schedule = Column(JSONB, default={})
    settings = Column(JSONB, default={})
    
    # Status
    is_active = Column(Boolean, default=True)
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    teacher = relationship("User", backref="taught_classes")
    course = relationship("Course", backref="classes")
    
    __table_args__ = (
        Index('idx_class_teacher', 'teacher_id'),
        Index('idx_class_code', 'code'),
    )


class Assignment(Base):
    """Assignment model for student tasks"""
    __tablename__ = "assignments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    instructions = Column(Text)
    
    # Class association
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    
    # Content association (optional)
    content_id = Column(UUID(as_uuid=True), ForeignKey("content.id"))
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.id"))
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id"))
    
    # Assignment details
    assignment_type = Column(String(50))  # homework, project, quiz, etc.
    points = Column(Integer, default=100)
    due_date = Column(DateTime(timezone=True))
    
    # Settings
    allow_late_submission = Column(Boolean, default=True)
    max_attempts = Column(Integer, default=1)
    time_limit = Column(Integer)  # in minutes
    resources = Column(JSONB, default=[])
    rubric = Column(JSONB, default={})
    
    # Status
    is_published = Column(Boolean, default=False)
    is_graded = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True))
    
    # Relationships
    class_ = relationship("Class", backref="assignments")
    content = relationship("Content", backref="assignments")
    lesson = relationship("Lesson", backref="assignments")
    quiz = relationship("Quiz", backref="assignments")
    
    __table_args__ = (
        Index('idx_assignment_class', 'class_id'),
        Index('idx_assignment_due_date', 'due_date'),
    )


class Submission(Base):
    """Student submission for assignments"""
    __tablename__ = "submissions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Association
    assignment_id = Column(UUID(as_uuid=True), ForeignKey("assignments.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Submission content
    content = Column(Text)  # Text submission
    file_urls = Column(JSONB, default=[])  # File attachments
    roblox_place_id = Column(String(100))  # For Roblox projects
    submission_metadata = Column(JSONB, default={})
    
    # Grading
    score = Column(Float)
    grade = Column(String(10))
    feedback = Column(Text)
    graded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    graded_at = Column(DateTime(timezone=True))
    
    # Status
    status = Column(String(50), default="draft")  # draft, submitted, graded, returned
    attempt_number = Column(Integer, default=1)
    is_late = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    submitted_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    assignment = relationship("Assignment", backref="submissions")
    student = relationship("User", foreign_keys=[student_id], backref="submissions")
    grader = relationship("User", foreign_keys=[graded_by], backref="graded_submissions")
    
    __table_args__ = (
        UniqueConstraint('assignment_id', 'student_id', 'attempt_number', 
                        name='uq_submission_attempt'),
        Index('idx_submission_assignment', 'assignment_id'),
        Index('idx_submission_student', 'student_id'),
        Index('idx_submission_status', 'status'),
    )


# Backward compatibility aliases
# Some older code expects EducationalContent instead of Content
EducationalContent = Content
# Alias for backward compatibility with tests
Progress = UserProgress
# Some code expects UserSession instead of Session
UserSession = Session
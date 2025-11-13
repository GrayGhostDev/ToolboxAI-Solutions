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
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import backref, declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

# Import agent models to ensure they're registered with Base
__all__ = []  # Will be extended with model names for wildcard imports

try:
    from database.models.agent_models import (
        AgentConfiguration,
        AgentExecution,
        AgentInstance,
        AgentMetrics,
        AgentStatus,
        AgentTaskQueue,
        AgentType,
        SystemHealth,
        TaskPriority,
        TaskStatus,
    )

    __all__.extend(
        [
            "AgentInstance",
            "AgentExecution",
            "AgentMetrics",
            "AgentTaskQueue",
            "SystemHealth",
            "AgentConfiguration",
            "AgentType",
            "AgentStatus",
            "TaskStatus",
            "TaskPriority",
        ]
    )
except ImportError:
    # Agent models not available
    pass


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


class RobloxSessionStatus(PyEnum):
    """Roblox session status"""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class RobloxContentType(PyEnum):
    """Roblox content types"""

    SCRIPT = "script"
    MODEL = "model"
    TERRAIN = "terrain"
    GUI = "gui"
    ANIMATION = "animation"
    SOUND = "sound"
    TEXTURE = "texture"
    MESH = "mesh"


# User Models
class User(Base):
    """Main user model for authentication and profile management"""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(
        Enum(UserRole, values_callable=lambda x: [e.value for e in x]),
        default=UserRole.STUDENT,
        nullable=False,
    )

    # Multi-tenancy
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Tenant identifier",
    )
    organization_role = Column(String(50), default="member")  # admin, manager, teacher, member

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
    organization = relationship(
        "Organization", backref="users", foreign_keys=[organization_id], lazy="joined"
    )
    enrollments = relationship("Enrollment", back_populates="user", cascade="all, delete-orphan")
    progress_records = relationship(
        "UserProgress", back_populates="user", cascade="all, delete-orphan"
    )
    quiz_attempts = relationship("QuizAttempt", back_populates="user", cascade="all, delete-orphan")
    achievements = relationship(
        "UserAchievement", back_populates="user", cascade="all, delete-orphan"
    )
    created_content = relationship(
        "Content", back_populates="creator", foreign_keys="Content.creator_id"
    )
    analytics = relationship("Analytics", back_populates="user", cascade="all, delete-orphan")
    plugin_requests = relationship(
        "PluginRequest", back_populates="user", cascade="all, delete-orphan"
    )
    teaching_sessions = relationship(
        "RobloxSession", back_populates="teacher", foreign_keys="RobloxSession.teacher_id"
    )
    student_progress = relationship(
        "StudentProgress", back_populates="student", foreign_keys="StudentProgress.student_id"
    )
    roblox_student_progress = relationship(
        "RobloxPlayerProgress",
        back_populates="student",
        foreign_keys="RobloxPlayerProgress.student_id",
    )
    deployments = relationship(
        "RobloxDeployment", back_populates="deployer", cascade="all, delete-orphan"
    )
    terrain_templates = relationship(
        "TerrainTemplate", back_populates="creator", cascade="all, delete-orphan"
    )
    quiz_templates = relationship(
        "QuizTemplate", back_populates="creator", cascade="all, delete-orphan"
    )
    roblox_templates = relationship(
        "RobloxTemplate", back_populates="creator", cascade="all, delete-orphan"
    )
    taught_classes = relationship("Class", back_populates="teacher", cascade="all, delete-orphan")
    class_enrollments = relationship(
        "ClassEnrollment", back_populates="student", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_user_email_active", "email", "is_active"),
        Index("idx_user_roblox_id", "roblox_user_id"),
        Index("idx_user_org_role", "organization_id", "organization_role"),
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
        CheckConstraint("grade_level >= 1 AND grade_level <= 12"),
        Index("idx_course_subject_grade", "subject", "grade_level"),
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
    difficulty = Column(
        Enum(DifficultyLevel, name="difficultylevel", create_type=False),
        default=DifficultyLevel.INTERMEDIATE,
    )
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
    progress_records = relationship(
        "UserProgress", back_populates="lesson", cascade="all, delete-orphan"
    )
    roblox_contents = relationship(
        "RobloxContent", back_populates="lesson", cascade="all, delete-orphan"
    )
    sessions = relationship("RobloxSession", back_populates="lesson", cascade="all, delete-orphan")
    student_progress = relationship(
        "StudentProgress", back_populates="lesson", cascade="all, delete-orphan"
    )
    roblox_player_progress = relationship(
        "RobloxPlayerProgress", back_populates="lesson", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("course_id", "order_index"),
        Index("idx_lesson_course_order", "course_id", "order_index"),
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

    # AI-generated content metadata
    ai_generated = Column(Boolean, default=False)
    ai_model = Column(String(100))
    ai_parameters = Column(JSONB)

    # Review and approval
    status = Column(
        Enum(ContentStatus, name="contentstatus", create_type=False), default=ContentStatus.DRAFT
    )
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
        Index("idx_content_lesson_type", "lesson_id", "content_type"),
        Index("idx_content_status", "status"),
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
    difficulty = Column(
        Enum(DifficultyLevel, name="difficultylevel", create_type=False),
        default=DifficultyLevel.INTERMEDIATE,
    )
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
        CheckConstraint("passing_score >= 0 AND passing_score <= 100"),
        Index("idx_quiz_lesson", "lesson_id"),
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
    responses = relationship(
        "QuizResponse", back_populates="question", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("quiz_id", "order_index"),
        CheckConstraint("points >= 0"),
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
        UniqueConstraint("quiz_id", "user_id", "attempt_number"),
        Index("idx_attempt_user_quiz", "user_id", "quiz_id"),
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
        UniqueConstraint("attempt_id", "question_id"),
        Index("idx_response_attempt", "attempt_id"),
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
    completion_status = Column(
        String(50), default="not_started"
    )  # not_started, in_progress, completed

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
        UniqueConstraint("user_id", "lesson_id"),
        Index("idx_progress_user_lesson", "user_id", "lesson_id"),
        CheckConstraint("progress_percentage >= 0 AND progress_percentage <= 100"),
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
        Index("idx_analytics_user_event", "user_id", "event_type"),
        Index("idx_analytics_created", "created_at"),
    )


# Gamification Models
class Achievement(Base):
    """Achievement definitions"""

    __tablename__ = "achievements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)

    # Achievement configuration
    achievement_type = Column(
        Enum(AchievementType, name="achievementtype", create_type=False), nullable=False
    )
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
    user_achievements = relationship(
        "UserAchievement", back_populates="achievement", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_achievement_type", "achievement_type"),)


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
        UniqueConstraint("user_id", "achievement_id"),
        Index("idx_user_achievement", "user_id", "achievement_id"),
        CheckConstraint("progress >= 0 AND progress <= 100"),
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
        UniqueConstraint("user_id"),
        Index("idx_leaderboard_scores", "total_score", "weekly_score", "monthly_score"),
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
        UniqueConstraint("user_id", "course_id"),
        Index("idx_enrollment_user_course", "user_id", "course_id"),
        CheckConstraint("overall_progress >= 0 AND overall_progress <= 100"),
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
        Index("idx_session_token", "session_token"),
        Index("idx_session_user", "user_id"),
        Index("idx_session_expires", "expires_at"),
    )


# Roblox Integration Models
class RobloxSession(Base):
    """Active Roblox game sessions tracking"""

    __tablename__ = "roblox_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.id"), nullable=False)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Roblox connection details
    universe_id = Column(String(100), nullable=False, default="8505376973")
    place_id = Column(String(100), nullable=False)
    server_id = Column(String(200))
    job_id = Column(String(200))

    # OAuth2 and authentication
    client_id = Column(String(100), nullable=False, default="2214511122270781418")
    access_token_hash = Column(String(255))  # Hashed for security
    refresh_token_hash = Column(String(255))  # Hashed for security
    token_expires_at = Column(DateTime(timezone=True))

    # WebSocket session data
    websocket_session_id = Column(String(200), unique=True)
    websocket_connection_active = Column(Boolean, default=False)
    last_heartbeat = Column(DateTime(timezone=True))

    # Session management
    status = Column(
        Enum(RobloxSessionStatus, name="robloxsessionstatus", create_type=False),
        default=RobloxSessionStatus.ACTIVE,
    )
    max_players = Column(Integer, default=30)
    current_players = Column(Integer, default=0)

    # Real-time sync data
    sync_frequency_seconds = Column(Integer, default=5)
    last_sync_at = Column(DateTime(timezone=True))
    sync_errors = Column(Integer, default=0)
    sync_data = Column(JSONB, default={})

    # COPPA compliance and audit trail
    coppa_consent_verified = Column(Boolean, default=False)
    audit_log = Column(JSONB, default=[])  # Track all session events
    parental_consent_ids = Column(ARRAY(String), default=[])  # For under-13 users

    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True))
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    lesson = relationship("Lesson", back_populates="sessions")
    teacher = relationship("User", back_populates="teaching_sessions", foreign_keys=[teacher_id])
    player_progress = relationship(
        "RobloxPlayerProgress", back_populates="session", cascade="all, delete-orphan"
    )
    quiz_results = relationship(
        "RobloxQuizResult", back_populates="session", cascade="all, delete-orphan"
    )
    achievements_earned = relationship(
        "RobloxAchievement", back_populates="session", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_roblox_session_lesson", "lesson_id"),
        Index("idx_roblox_session_teacher", "teacher_id"),
        Index("idx_roblox_session_universe", "universe_id", "place_id"),
        Index("idx_roblox_session_status", "status"),
        Index("idx_roblox_session_active", "websocket_connection_active"),
        Index("idx_roblox_session_last_activity", "last_activity_at"),
    )


class RobloxContent(Base):
    """Generated educational content for Roblox"""

    __tablename__ = "roblox_content"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.id"), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey("roblox_templates.id"))

    # Content identification
    title = Column(String(200), nullable=False)
    content_type = Column(
        Enum(RobloxContentType, name="robloxcontenttype", create_type=False), nullable=False
    )
    version = Column(String(20), default="1.0.0")

    # Roblox-specific data
    place_id = Column(String(100))
    asset_id = Column(String(100))
    model_id = Column(String(100))
    script_content = Column(Text)  # Lua script content

    # Content data and metadata
    content_data = Column(JSONB, nullable=False)  # Main content structure
    roblox_properties = Column(JSONB, default={})  # Roblox-specific properties
    educational_metadata = Column(JSONB, default={})  # Learning objectives, etc.

    # AI generation tracking
    ai_generated = Column(Boolean, default=True)
    ai_model = Column(String(100), default="gpt-4")
    generation_parameters = Column(JSONB, default={})
    generation_prompt = Column(Text)

    # Version control and deployment
    is_deployed = Column(Boolean, default=False)
    deployed_at = Column(DateTime(timezone=True))
    deployment_hash = Column(String(64))  # SHA256 hash of content

    # Performance and usage tracking
    usage_count = Column(Integer, default=0)
    performance_metrics = Column(JSONB, default={})
    user_feedback = Column(JSONB, default={})

    # COPPA compliance
    coppa_compliant = Column(Boolean, default=True)
    content_rating = Column(String(10), default="E")  # Everyone, T for Teen, etc.

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    lesson = relationship("Lesson", back_populates="roblox_contents")
    template = relationship("RobloxTemplate", back_populates="content_instances")

    __table_args__ = (
        Index("idx_roblox_content_lesson", "lesson_id"),
        Index("idx_roblox_content_type", "content_type"),
        Index("idx_roblox_content_deployed", "is_deployed"),
        Index("idx_roblox_content_place", "place_id"),
        Index("idx_roblox_content_version", "version"),
    )


class RobloxPlayerProgress(Base):
    """Student progress tracking within Roblox sessions"""

    __tablename__ = "roblox_player_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("roblox_sessions.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.id"), nullable=False)

    # Roblox player identification
    roblox_user_id = Column(String(100), nullable=False)
    roblox_username = Column(String(100), nullable=False)

    # Progress metrics
    progress_percentage = Column(Float, default=0.0)
    checkpoints_completed = Column(JSONB, default=[])  # Array of checkpoint IDs
    objectives_met = Column(JSONB, default=[])  # Learning objectives achieved

    # In-game performance
    score = Column(Integer, default=0)
    time_spent_seconds = Column(Integer, default=0)
    actions_completed = Column(Integer, default=0)
    mistakes_made = Column(Integer, default=0)
    hints_used = Column(Integer, default=0)

    # Real-time tracking data
    current_position = Column(JSONB)  # X, Y, Z coordinates in game
    current_activity = Column(String(200))  # Current learning activity
    last_interaction = Column(DateTime(timezone=True))

    # Collaboration and social features
    team_id = Column(String(100))  # If working in teams
    collaborative_actions = Column(Integer, default=0)
    peer_interactions = Column(Integer, default=0)

    # Adaptive learning data
    difficulty_adjustments = Column(JSONB, default=[])  # Track difficulty changes
    learning_path = Column(JSONB, default=[])  # Sequence of activities completed
    performance_trends = Column(JSONB, default={})  # Performance over time

    # COPPA compliance
    age_verified = Column(Boolean, default=False)
    parental_consent_given = Column(Boolean, default=False)
    data_collection_consent = Column(Boolean, default=False)

    # Session tracking
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    left_at = Column(DateTime(timezone=True))
    session_duration_seconds = Column(Integer, default=0)
    disconnections = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    session = relationship("RobloxSession", back_populates="player_progress")
    student = relationship(
        "User", back_populates="roblox_student_progress", foreign_keys=[student_id]
    )
    lesson = relationship("Lesson", back_populates="roblox_player_progress")
    quiz_results = relationship(
        "RobloxQuizResult", back_populates="player_progress", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("session_id", "student_id", "roblox_user_id"),
        Index("idx_roblox_progress_session", "session_id"),
        Index("idx_roblox_progress_student", "student_id"),
        Index("idx_roblox_progress_lesson", "lesson_id"),
        Index("idx_roblox_progress_roblox_user", "roblox_user_id"),
        CheckConstraint("progress_percentage >= 0 AND progress_percentage <= 100"),
        CheckConstraint("score >= 0"),
        CheckConstraint("time_spent_seconds >= 0"),
    )


class RobloxQuizResult(Base):
    """Quiz performance data from Roblox sessions"""

    __tablename__ = "roblox_quiz_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("roblox_sessions.id"), nullable=False)
    player_progress_id = Column(
        UUID(as_uuid=True), ForeignKey("roblox_player_progress.id"), nullable=False
    )
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id"))

    # Quiz identification
    quiz_name = Column(String(200), nullable=False)
    quiz_type = Column(String(100), default="interactive")
    difficulty_level = Column(
        Enum(DifficultyLevel, name="difficultylevel", create_type=False),
        default=DifficultyLevel.INTERMEDIATE,
    )

    # Performance metrics
    total_questions = Column(Integer, nullable=False)
    correct_answers = Column(Integer, default=0)
    incorrect_answers = Column(Integer, default=0)
    skipped_questions = Column(Integer, default=0)

    # Scoring
    raw_score = Column(Float, default=0.0)
    percentage_score = Column(Float, default=0.0)
    weighted_score = Column(Float, default=0.0)  # Adjusted for difficulty
    bonus_points = Column(Integer, default=0)

    # Timing data
    time_allocated_seconds = Column(Integer)
    time_taken_seconds = Column(Integer)
    average_time_per_question = Column(Float)

    # Detailed response data
    question_responses = Column(JSONB, default=[])  # Array of question-response pairs
    response_patterns = Column(JSONB, default={})  # Analysis of response patterns
    learning_gaps = Column(JSONB, default=[])  # Identified knowledge gaps

    # Real-time game integration
    in_game_location = Column(JSONB)  # Where in the game the quiz was taken
    game_context = Column(JSONB, default={})  # Context of the quiz within the game
    interactive_elements = Column(JSONB, default=[])  # Interactive game elements used

    # Adaptive learning
    difficulty_adjustments = Column(JSONB, default=[])  # Real-time difficulty changes
    hints_provided = Column(Integer, default=0)
    help_requests = Column(Integer, default=0)

    # Performance analytics
    improvement_from_previous = Column(Float)  # Percentage improvement
    consistency_score = Column(Float)  # How consistent the performance was
    confidence_indicators = Column(JSONB, default={})  # Confidence level per topic

    # Status and completion
    completed = Column(Boolean, default=False)
    passed = Column(Boolean, default=False)
    retry_count = Column(Integer, default=0)

    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("RobloxSession", back_populates="quiz_results")
    player_progress = relationship("RobloxPlayerProgress", back_populates="quiz_results")
    quiz = relationship("Quiz")

    __table_args__ = (
        Index("idx_roblox_quiz_session", "session_id"),
        Index("idx_roblox_quiz_player", "player_progress_id"),
        Index("idx_roblox_quiz_performance", "percentage_score"),
        Index("idx_roblox_quiz_completion", "completed", "passed"),
        CheckConstraint("percentage_score >= 0 AND percentage_score <= 100"),
        CheckConstraint("correct_answers >= 0"),
        CheckConstraint("total_questions > 0"),
    )


class RobloxAchievement(Base):
    """Gamification achievements earned in Roblox"""

    __tablename__ = "roblox_achievements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("roblox_sessions.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    base_achievement_id = Column(UUID(as_uuid=True), ForeignKey("achievements.id"))

    # Achievement details
    achievement_name = Column(String(200), nullable=False)
    achievement_type = Column(
        Enum(AchievementType, name="achievementtype", create_type=False), nullable=False
    )
    description = Column(Text)

    # Roblox-specific data
    in_game_badge_id = Column(String(100))  # Roblox badge ID if applicable
    roblox_asset_id = Column(String(100))  # Associated Roblox asset
    game_location_earned = Column(JSONB)  # Where in game it was earned

    # Achievement metrics
    points_awarded = Column(Integer, default=10)
    difficulty_multiplier = Column(Float, default=1.0)
    rarity_bonus = Column(Integer, default=0)

    # Context and conditions
    trigger_conditions = Column(JSONB, nullable=False)  # What triggered the achievement
    performance_context = Column(JSONB, default={})  # Performance when earned
    peer_comparison = Column(JSONB, default={})  # How it compares to peers

    # Visual and presentation
    icon_url = Column(String(500))
    badge_color = Column(String(7))  # Hex color code
    animation_data = Column(JSONB)  # Animation for earning the achievement

    # Social features
    is_shareable = Column(Boolean, default=True)
    shared_count = Column(Integer, default=0)
    likes_received = Column(Integer, default=0)

    # Progress tracking
    current_progress = Column(Float, default=100.0)  # Percentage progress when earned
    milestone_data = Column(JSONB, default={})  # Milestone progression

    # Timestamps
    earned_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("RobloxSession", back_populates="achievements_earned")
    student = relationship("User")
    base_achievement = relationship("Achievement")

    __table_args__ = (
        Index("idx_roblox_achievement_session", "session_id"),
        Index("idx_roblox_achievement_student", "student_id"),
        Index("idx_roblox_achievement_type", "achievement_type"),
        Index("idx_roblox_achievement_earned", "earned_at"),
    )


class RobloxTemplate(Base):
    """Content templates for Roblox educational content"""

    __tablename__ = "roblox_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Template identification
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100), nullable=False)  # e.g., "math", "science", "coding"
    subject_area = Column(String(100), nullable=False)
    grade_level_min = Column(Integer, nullable=False)
    grade_level_max = Column(Integer, nullable=False)

    # Template structure
    template_type = Column(
        Enum(RobloxContentType, name="robloxcontenttype", create_type=False), nullable=False
    )
    base_structure = Column(JSONB, nullable=False)  # Core template structure
    customization_points = Column(JSONB, default=[])  # Points where content can be customized
    variable_definitions = Column(JSONB, default={})  # Template variables

    # Educational framework
    learning_objectives_template = Column(JSONB, default=[])
    assessment_criteria = Column(JSONB, default={})
    difficulty_scales = Column(JSONB, default={})
    adaptation_rules = Column(JSONB, default={})

    # Roblox-specific template data
    required_assets = Column(JSONB, default=[])  # Required Roblox assets
    script_templates = Column(JSONB, default={})  # Lua script templates
    ui_templates = Column(JSONB, default={})  # GUI templates
    model_specifications = Column(JSONB, default={})

    # Generation parameters
    ai_generation_prompts = Column(JSONB, default={})  # Prompts for AI generation
    parameter_constraints = Column(JSONB, default={})  # Constraints for generated content
    quality_thresholds = Column(JSONB, default={})  # Quality requirements

    # Usage and performance
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)  # Success rate of generated content
    average_rating = Column(Float, default=0.0)
    performance_metrics = Column(JSONB, default={})

    # Versioning
    version = Column(String(20), default="1.0.0")
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)

    # COPPA compliance
    coppa_compliant = Column(Boolean, default=True)
    age_appropriate_content = Column(Boolean, default=True)
    content_warnings = Column(JSONB, default=[])

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    creator = relationship("User", back_populates="roblox_templates")
    content_instances = relationship(
        "RobloxContent", back_populates="template", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_roblox_template_category", "category"),
        Index("idx_roblox_template_subject", "subject_area"),
        Index("idx_roblox_template_grade", "grade_level_min", "grade_level_max"),
        Index("idx_roblox_template_type", "template_type"),
        Index("idx_roblox_template_active", "is_active", "is_public"),
        CheckConstraint("grade_level_min >= 1 AND grade_level_min <= 12"),
        CheckConstraint("grade_level_max >= 1 AND grade_level_max <= 12"),
        CheckConstraint("grade_level_min <= grade_level_max"),
        CheckConstraint("success_rate >= 0 AND success_rate <= 100"),
        CheckConstraint("average_rating >= 0 AND average_rating <= 5"),
    )


# Additional relationship updates needed

# Add to User model relationships (these would be added in a migration)
# roblox_templates = relationship("RobloxTemplate", back_populates="creator", cascade="all, delete-orphan")
# student_progress = relationship("RobloxPlayerProgress", back_populates="student", foreign_keys="RobloxPlayerProgress.student_id")
# teaching_sessions = relationship("RobloxSession", back_populates="teacher", foreign_keys="RobloxSession.teacher_id")

# Add to Lesson model relationships (these would be added in a migration)
# roblox_contents = relationship("RobloxContent", back_populates="lesson", cascade="all, delete-orphan")
# sessions = relationship("RobloxSession", back_populates="lesson", cascade="all, delete-orphan")
# student_progress = relationship("RobloxPlayerProgress", back_populates="lesson", cascade="all, delete-orphan")


# Additional Models for Integration Agents


class StudentProgress(Base):
    """Student progress tracking (compatibility model)"""

    __tablename__ = "student_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.id"), nullable=False)

    # Progress metrics
    progress_percentage = Column(Float, default=0.0)
    score = Column(Float)
    time_spent_minutes = Column(Integer, default=0)
    completed_at = Column(DateTime(timezone=True))
    attempts = Column(Integer, default=0)
    last_accessed = Column(DateTime(timezone=True), server_default=func.now())

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    lesson = relationship("Lesson", foreign_keys=[lesson_id])

    __table_args__ = (
        UniqueConstraint("student_id", "lesson_id"),
        Index("idx_student_progress_student", "student_id"),
        Index("idx_student_progress_lesson", "lesson_id"),
        CheckConstraint("progress_percentage >= 0 AND progress_percentage <= 100"),
    )


class SchemaDefinition(Base):
    """Cross-platform schema definitions for validation"""

    __tablename__ = "schema_definitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    schema_id = Column(String(255), unique=True, nullable=False)
    schema_name = Column(String(200), nullable=False)
    schema_type = Column(String(50), nullable=False)  # json_schema, pydantic, etc.
    version = Column(String(20), nullable=False)
    definition = Column(JSONB, nullable=False)
    platform = Column(String(50), nullable=False)  # backend, frontend, roblox

    # Metadata
    deprecated = Column(Boolean, default=False)
    compatible_versions = Column(ARRAY(String), default=[])

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("idx_schema_definitions_platform", "platform"),
        Index("idx_schema_definitions_type", "schema_type"),
    )


class SchemaMapping(Base):
    """Cross-platform data transformation mappings"""

    __tablename__ = "schema_mappings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mapping_id = Column(String(255), unique=True, nullable=False)
    source_schema_id = Column(String(255), nullable=False)
    target_schema_id = Column(String(255), nullable=False)

    # Mapping data
    field_mappings = Column(JSONB, nullable=False)  # source_field -> target_field
    transformations = Column(JSONB, default={})  # field -> transformation function
    bidirectional = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_schema_mappings_source", "source_schema_id"),
        Index("idx_schema_mappings_target", "target_schema_id"),
    )


class AgentHealthStatus(Base):
    """Integration agent health monitoring"""

    __tablename__ = "agent_health_status"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name = Column(String(100), nullable=False)
    agent_type = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False)  # healthy, unhealthy, error, etc.
    healthy = Column(Boolean, default=True)
    message = Column(Text)
    error_details = Column(JSONB)
    metrics = Column(JSONB, default={})

    # Timestamps
    last_check_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_agent_health_name", "agent_name"),
        Index("idx_agent_health_type", "agent_type"),
        Index("idx_agent_health_status", "status", "healthy"),
    )


class IntegrationEvent(Base):
    """Event bus tracking for integration events"""

    __tablename__ = "integration_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(String(255), nullable=False)
    event_type = Column(String(100), nullable=False)
    source_platform = Column(String(50), nullable=False)
    target_platform = Column(String(50))
    payload = Column(JSONB, nullable=False)
    correlation_id = Column(String(255))

    # Processing status
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_integration_events_type", "event_type"),
        Index("idx_integration_events_platform", "source_platform"),
        Index("idx_integration_events_processed", "processed"),
        Index("idx_integration_events_created", "created_at"),
    )


# Class Management Models
class Class(Base):
    """Class model for managing educational classes"""

    __tablename__ = "classes"
    __table_args__ = (
        CheckConstraint("grade_level >= 1 AND grade_level <= 12"),
        CheckConstraint("max_students > 0"),
        Index("idx_class_teacher", "teacher_id"),
        Index("idx_class_subject_grade", "subject", "grade_level"),
        Index("idx_class_active", "is_active"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    grade_level = Column(Integer, nullable=False)
    subject = Column(String(100), nullable=False)
    room = Column(String(100))
    schedule = Column(String(200))
    description = Column(Text)
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    max_students = Column(Integer, default=30)
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    teacher = relationship("User", back_populates="taught_classes")
    enrollments = relationship(
        "ClassEnrollment", back_populates="class_obj", cascade="all, delete-orphan"
    )


class ClassEnrollment(Base):
    """Many-to-many relationship between classes and students"""

    __tablename__ = "class_enrollments"
    __table_args__ = (
        UniqueConstraint("class_id", "student_id"),
        Index("idx_enrollment_class", "class_id"),
        Index("idx_enrollment_student", "student_id"),
        Index("idx_enrollment_status", "status"),
        CheckConstraint("attendance_percentage >= 0 AND attendance_percentage <= 100"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Enrollment details
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())
    dropped_at = Column(DateTime(timezone=True))
    status = Column(String(50), default="active")  # active, dropped, completed

    # Academic tracking
    final_grade = Column(Float)
    attendance_percentage = Column(Float)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    class_obj = relationship("Class", back_populates="enrollments")
    student = relationship("User", back_populates="class_enrollments")


# Additional Models for Missing Relationships (stub implementations)


class PluginRequest(Base):
    """Plugin request tracking (stub for relationship)"""

    __tablename__ = "plugin_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    plugin_name = Column(String(200), nullable=False)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="plugin_requests")


class RobloxDeployment(Base):
    """Roblox deployment tracking (stub for relationship)"""

    __tablename__ = "roblox_deployments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deployer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    deployment_name = Column(String(200), nullable=False)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    deployer = relationship("User", back_populates="deployments")


class TerrainTemplate(Base):
    """Terrain template model (stub for relationship)"""

    __tablename__ = "terrain_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    template_name = Column(String(200), nullable=False)
    template_data = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    creator = relationship("User", back_populates="terrain_templates")


class QuizTemplate(Base):
    """Quiz template model (stub for relationship)"""

    __tablename__ = "quiz_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    template_name = Column(String(200), nullable=False)
    template_data = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    creator = relationship("User", back_populates="quiz_templates")


# Backward compatibility alias
# Some older code expects EducationalContent instead of Content
EducationalContent = Content


class EnhancedContentGeneration(Base):
    """Model for tracking enhanced content generation requests and results"""

    __tablename__ = "enhanced_content_generations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Request details
    original_request = Column(JSONB, nullable=False)
    content_type = Column(String(50), nullable=False)  # lesson, quiz, activity, scenario
    subject = Column(String(100))
    grade_level = Column(String(50))
    difficulty_level = Column(String(20))  # beginner, intermediate, advanced

    # Generated content
    generated_content = Column(JSONB)
    roblox_script = Column(Text)
    lesson_plan = Column(Text)

    # Status and timing
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    # Quality metrics
    quality_score = Column(Float)
    user_rating = Column(Float)

    # Relationships
    user = relationship("User", backref="enhanced_content_generations")


class ContentGenerationBatch(Base):
    """Batch processing for multiple content generations"""

    __tablename__ = "content_generation_batches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_name = Column(String(200))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Batch configuration
    batch_config = Column(JSONB)  # common parameters for all items
    total_items = Column(Integer)
    completed_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)

    # Status tracking
    status = Column(String(50), default="pending")  # pending, processing, completed, failed

    # Performance
    estimated_completion_time = Column(DateTime(timezone=True))
    actual_completion_time = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", backref="content_generation_batches")


# Ensure key models are exported when using `from database.models import *`
__all__.extend(
    [
        "Base",
        "User",
        "Course",
        "Content",
        "Class",
        "Lesson",
        "Quiz",
        "QuizQuestion",
        "QuizAttempt",
        "QuizResponse",
        "UserProgress",  # Mobile endpoint dependency
        "StudentProgress",
        "Analytics",
        "Achievement",
        "UserAchievement",
        "Enrollment",
        "ClassEnrollment",
        "Session",
        "RobloxSession",
        "RobloxContent",
        "RobloxPlayerProgress",
        "EnhancedContentGeneration",
        "ContentGenerationBatch",
    ]
)

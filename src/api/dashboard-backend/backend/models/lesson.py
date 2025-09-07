"""
Lesson and lesson progress models
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import JSON, Boolean, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    # Import model names for type checking only to avoid runtime import cycles
    from .badge import Badge
    from .class_model import Class
    from .user import User


# Many-to-many association table for lessons and classes
class_lessons = Table(
    "class_lessons",
    Base.metadata,
    Column("class_id", String(36), ForeignKey("classes.id"), primary_key=True),
    Column("lesson_id", String(36), ForeignKey("lessons.id"), primary_key=True),
)


class LessonStatus(enum.Enum):
    """Lesson publication status"""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class LessonDifficulty(enum.Enum):
    """Lesson difficulty levels"""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class Lesson(Base, TimestampMixin):
    """Lesson model"""

    __tablename__ = "lessons"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Basic information
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    grade_level: Mapped[int] = mapped_column(Integer, nullable=False)

    # Teacher/Author
    teacher_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )

    # Content
    content: Mapped[dict] = mapped_column(JSON, nullable=False, default={})
    resources: Mapped[Optional[dict]] = mapped_column(JSON, default={})

    # Settings
    status: Mapped[LessonStatus] = mapped_column(
        SQLEnum(LessonStatus), default=LessonStatus.DRAFT, nullable=False
    )
    difficulty: Mapped[LessonDifficulty] = mapped_column(
        SQLEnum(LessonDifficulty), default=LessonDifficulty.BEGINNER, nullable=False
    )
    estimated_time_minutes: Mapped[int] = mapped_column(
        Integer, default=45, nullable=False
    )

    # Gamification
    xp_reward: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    badge_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("badges.id"))

    # Roblox integration
    roblox_world_id: Mapped[Optional[str]] = mapped_column(String(100))
    roblox_place_id: Mapped[Optional[str]] = mapped_column(String(100))
    roblox_assets: Mapped[Optional[dict]] = mapped_column(JSON)

    # Media
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500))
    video_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Tags and categorization
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, default=[])
    prerequisites: Mapped[Optional[List[str]]] = mapped_column(
        JSON, default=[]
    )  # List of lesson IDs

    # Statistics
    times_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_rating: Mapped[Optional[float]] = mapped_column(Integer)
    average_completion_time: Mapped[Optional[int]] = mapped_column(Integer)

    # Relationships
    teacher: Mapped["User"] = relationship("User", back_populates="lessons_created")
    classes: Mapped[List["Class"]] = relationship(
        "Class", secondary=class_lessons, back_populates="lessons"
    )
    progress_records: Mapped[List["LessonProgress"]] = relationship(
        "LessonProgress", back_populates="lesson"
    )
    reward_badge: Mapped[Optional["Badge"]] = relationship(
        "Badge", foreign_keys=[badge_id]
    )

    def __repr__(self):
        return f"<Lesson {self.title}>"


class LessonProgress(Base, TimestampMixin):
    """Track student progress through lessons"""

    __tablename__ = "lesson_progress"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Foreign keys
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    lesson_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("lessons.id"), nullable=False
    )
    class_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("classes.id")
    )

    # Progress tracking
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Completion details
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    time_spent_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Scoring
    score: Mapped[Optional[int]] = mapped_column(Integer)
    attempts: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # XP and rewards
    xp_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    badge_earned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Progress data (quiz answers, checkpoints, etc.)
    progress_data: Mapped[Optional[dict]] = mapped_column(JSON, default={})

    # Relationships
    user: Mapped["User"] = relationship("User")
    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="progress_records")
    class_: Mapped[Optional["Class"]] = relationship("Class")

    def __repr__(self):
        return f"<LessonProgress {self.user_id} - {self.lesson_id} ({self.progress_percentage}%)>"

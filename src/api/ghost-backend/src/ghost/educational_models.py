"""
Educational Content Models for ToolboxAI Roblox Environment

This module extends the base Ghost models with comprehensive educational content models
covering learning objectives, content generation, and curriculum alignment.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    ARRAY,
    DECIMAL,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import declared_attr, relationship

from .database import Base
from .models import AuditMixin, SoftDeleteMixin, TimestampMixin


# Educational Enums
class SubjectType(str, Enum):
    """Educational subjects supported by the platform"""

    MATHEMATICS = "Mathematics"
    SCIENCE = "Science"
    HISTORY = "History"
    ENGLISH = "English"
    ART = "Art"
    GEOGRAPHY = "Geography"
    COMPUTER_SCIENCE = "Computer Science"
    PHYSICS = "Physics"
    CHEMISTRY = "Chemistry"
    BIOLOGY = "Biology"


class DifficultyLevel(str, Enum):
    """Content and assessment difficulty levels"""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class EnvironmentType(str, Enum):
    """Roblox environment types for educational content"""

    CLASSROOM = "classroom"
    LABORATORY = "laboratory"
    OUTDOOR = "outdoor"
    HISTORICAL = "historical"
    FUTURISTIC = "futuristic"
    UNDERWATER = "underwater"
    SPACE_STATION = "space_station"
    FANTASY = "fantasy"
    CUSTOM = "custom"


class BloomLevel(str, Enum):
    """Bloom's Taxonomy levels for learning objectives"""

    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


# Educational Content Models
class LearningObjective(Base, TimestampMixin, AuditMixin):
    """Learning objectives aligned with curriculum standards"""

    __tablename__ = "learning_objectives"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    subject = Column(String(50), nullable=False)
    grade_level = Column(Integer, nullable=False)
    bloom_level = Column(String(20), nullable=True)
    curriculum_standard = Column(String(100), nullable=True)
    measurable = Column(Boolean, default=True, nullable=False)

    # Relationships
    content_objectives = relationship(
        "ContentObjective", back_populates="objective", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("ix_learning_objectives_subject_grade", "subject", "grade_level"),
        Index("ix_learning_objectives_bloom_level", "bloom_level"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "subject": self.subject,
            "grade_level": self.grade_level,
            "bloom_level": self.bloom_level,
            "curriculum_standard": self.curriculum_standard,
            "measurable": self.measurable,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class EducationalContent(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    """Main educational content with AI-generated materials"""

    __tablename__ = "educational_content"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    subject = Column(String(50), nullable=False)
    grade_level = Column(Integer, nullable=False)
    environment_type = Column(String(50), nullable=False)
    terrain_size = Column(String(20), default="medium")
    difficulty_level = Column(String(20), default="medium")
    duration_minutes = Column(Integer, default=30)
    max_students = Column(Integer, default=30)

    # Generated content data
    content_data = Column(JSONB, nullable=False)
    generated_scripts = Column(ARRAY(JSONB), default=list)
    terrain_config = Column(JSONB, nullable=True)
    game_mechanics = Column(JSONB, nullable=True)

    # Educational features
    accessibility_features = Column(Boolean, default=False)
    multilingual = Column(Boolean, default=False)
    is_template = Column(Boolean, default=False)
    version = Column(Integer, default=1)

    # User tracking
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_id])
    content_objectives = relationship(
        "ContentObjective", back_populates="content", cascade="all, delete-orphan"
    )
    quizzes = relationship(
        "Quiz", back_populates="content", cascade="all, delete-orphan"
    )
    roblox_scripts = relationship(
        "RobloxScript", back_populates="content", cascade="all, delete-orphan"
    )
    terrain_data = relationship(
        "RobloxTerrain", back_populates="content", cascade="all, delete-orphan"
    )
    game_sessions = relationship(
        "RobloxGameSession", back_populates="content", cascade="all, delete-orphan"
    )
    user_progress = relationship(
        "UserProgress", back_populates="content", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("ix_educational_content_subject_grade", "subject", "grade_level"),
        Index("ix_educational_content_environment", "environment_type"),
        Index("ix_educational_content_difficulty", "difficulty_level"),
        Index("ix_educational_content_template", "is_template"),
        Index("ix_educational_content_created_by", "created_by_id"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "subject": self.subject,
            "grade_level": self.grade_level,
            "environment_type": self.environment_type,
            "terrain_size": self.terrain_size,
            "difficulty_level": self.difficulty_level,
            "duration_minutes": self.duration_minutes,
            "max_students": self.max_students,
            "content_data": self.content_data,
            "generated_scripts": self.generated_scripts,
            "terrain_config": self.terrain_config,
            "game_mechanics": self.game_mechanics,
            "accessibility_features": self.accessibility_features,
            "multilingual": self.multilingual,
            "is_template": self.is_template,
            "version": self.version,
            "created_by_id": str(self.created_by_id) if self.created_by_id else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class ContentObjective(Base, TimestampMixin):
    """Association table for content and learning objectives"""

    __tablename__ = "content_objectives"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id = Column(
        UUID(as_uuid=True),
        ForeignKey("educational_content.id", ondelete="CASCADE"),
        nullable=False,
    )
    objective_id = Column(
        UUID(as_uuid=True),
        ForeignKey("learning_objectives.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Additional metadata for the relationship
    priority = Column(Integer, default=1)  # Objective priority in content
    coverage_percentage = Column(
        DECIMAL(5, 2), default=100.0
    )  # How much content covers this objective

    # Relationships
    content = relationship("EducationalContent", back_populates="content_objectives")
    objective = relationship("LearningObjective", back_populates="content_objectives")

    # Unique constraint
    __table_args__ = (
        Index(
            "ix_content_objectives_unique", "content_id", "objective_id", unique=True
        ),
        Index("ix_content_objectives_priority", "content_id", "priority"),
    )


# Export models
__all__ = [
    "SubjectType",
    "DifficultyLevel",
    "EnvironmentType",
    "BloomLevel",
    "LearningObjective",
    "EducationalContent",
    "ContentObjective",
]

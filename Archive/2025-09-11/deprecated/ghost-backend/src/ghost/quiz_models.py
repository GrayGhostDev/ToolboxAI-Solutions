"""
Quiz and Assessment Models for ToolboxAI Roblox Environment

This module provides comprehensive quiz and assessment functionality including
adaptive difficulty, multiple question types, and detailed analytics.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    DECIMAL,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from .database import Base
from .educational_models import DifficultyLevel, SubjectType
from .models import AuditMixin, SoftDeleteMixin, TimestampMixin


class QuizType(str, Enum):
    """Types of quiz questions supported"""

    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    FILL_BLANK = "fill_blank"
    MATCHING = "matching"
    ORDERING = "ordering"
    DRAG_DROP = "drag_drop"
    HOTSPOT = "hotspot"


class MasteryLevel(str, Enum):
    """Student mastery levels for adaptive learning"""

    NOVICE = "novice"
    DEVELOPING = "developing"
    PROFICIENT = "proficient"
    ADVANCED = "advanced"
    EXPERT = "expert"


class Quiz(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    """Quiz definitions with adaptive learning capabilities"""

    __tablename__ = "quizzes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    subject = Column(String(50), nullable=False)
    grade_level = Column(Integer, nullable=False)

    # Quiz configuration
    time_limit = Column(Integer, nullable=True)  # Total quiz time in seconds
    passing_score = Column(Integer, default=70)  # Percentage
    max_attempts = Column(Integer, default=3)
    shuffle_questions = Column(Boolean, default=True)
    shuffle_options = Column(Boolean, default=True)
    show_results = Column(Boolean, default=True)
    show_correct_answers = Column(Boolean, default=True)

    # Adaptive learning features
    is_adaptive = Column(Boolean, default=False)
    difficulty_progression = Column(
        JSONB, nullable=True
    )  # Rules for difficulty adjustment
    prerequisite_quizzes = Column(JSONB, default=list)  # Required quiz IDs

    # Integration
    content_id = Column(
        UUID(as_uuid=True),
        ForeignKey("educational_content.id", ondelete="CASCADE"),
        nullable=True,
    )
    lms_assignment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("lms_assignments.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Authoring
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    content = relationship("EducationalContent", back_populates="quizzes")
    created_by = relationship("User", foreign_keys=[created_by_id])
    questions = relationship(
        "QuizQuestion",
        back_populates="quiz",
        cascade="all, delete-orphan",
        order_by="QuizQuestion.order_index",
    )
    attempts = relationship(
        "QuizAttempt", back_populates="quiz", cascade="all, delete-orphan"
    )
    lms_assignment = relationship("LMSAssignment", back_populates="toolboxai_quiz")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "passing_score >= 0 AND passing_score <= 100", name="valid_passing_score"
        ),
        CheckConstraint("max_attempts > 0", name="positive_max_attempts"),
        CheckConstraint(
            "grade_level >= 1 AND grade_level <= 12", name="valid_grade_level"
        ),
        Index("ix_quizzes_subject_grade", "subject", "grade_level"),
        Index("ix_quizzes_content", "content_id"),
        Index("ix_quizzes_adaptive", "is_adaptive"),
        Index("ix_quizzes_created_by", "created_by_id"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "subject": self.subject,
            "grade_level": self.grade_level,
            "time_limit": self.time_limit,
            "passing_score": self.passing_score,
            "max_attempts": self.max_attempts,
            "shuffle_questions": self.shuffle_questions,
            "shuffle_options": self.shuffle_options,
            "show_results": self.show_results,
            "show_correct_answers": self.show_correct_answers,
            "is_adaptive": self.is_adaptive,
            "difficulty_progression": self.difficulty_progression,
            "prerequisite_quizzes": self.prerequisite_quizzes,
            "content_id": str(self.content_id) if self.content_id else None,
            "created_by_id": str(self.created_by_id) if self.created_by_id else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class QuizQuestion(Base, TimestampMixin):
    """Individual quiz questions with multiple types support"""

    __tablename__ = "quiz_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id = Column(
        UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False
    )
    question_type = Column(String(20), nullable=False)
    question_text = Column(Text, nullable=False)
    correct_answer = Column(Text, nullable=True)  # For non-multiple choice
    difficulty = Column(String(20), default="medium")
    points = Column(Integer, default=1)
    time_limit = Column(Integer, nullable=True)  # Per question time in seconds
    hint = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    order_index = Column(Integer, nullable=False)

    # Additional question data (varies by type)
    question_data = Column(JSONB, nullable=True)

    # Learning analytics
    bloom_level = Column(String(20), nullable=True)
    cognitive_load = Column(String(20), default="medium")  # low, medium, high

    # Relationships
    quiz = relationship("Quiz", back_populates="questions")
    options = relationship(
        "QuizOption",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="QuizOption.order_index",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("points > 0", name="positive_points"),
        CheckConstraint("order_index >= 0", name="non_negative_order"),
        Index("ix_quiz_questions_quiz_order", "quiz_id", "order_index"),
        Index("ix_quiz_questions_type", "question_type"),
        Index("ix_quiz_questions_difficulty", "difficulty"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": str(self.id),
            "quiz_id": str(self.quiz_id),
            "question_type": self.question_type,
            "question_text": self.question_text,
            "correct_answer": self.correct_answer,
            "difficulty": self.difficulty,
            "points": self.points,
            "time_limit": self.time_limit,
            "hint": self.hint,
            "explanation": self.explanation,
            "order_index": self.order_index,
            "question_data": self.question_data,
            "bloom_level": self.bloom_level,
            "cognitive_load": self.cognitive_load,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class QuizOption(Base, TimestampMixin):
    """Answer options for multiple choice questions"""

    __tablename__ = "quiz_options"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(
        UUID(as_uuid=True),
        ForeignKey("quiz_questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    option_text = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)
    explanation = Column(Text, nullable=True)
    order_index = Column(Integer, nullable=False)

    # Additional option data
    option_data = Column(JSONB, nullable=True)  # For special question types

    # Relationships
    question = relationship("QuizQuestion", back_populates="options")

    # Constraints
    __table_args__ = (
        Index("ix_quiz_options_question_order", "question_id", "order_index"),
        Index("ix_quiz_options_correct", "question_id", "is_correct"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": str(self.id),
            "question_id": str(self.question_id),
            "option_text": self.option_text,
            "is_correct": self.is_correct,
            "explanation": self.explanation,
            "order_index": self.order_index,
            "option_data": self.option_data,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class QuizAttempt(Base, TimestampMixin):
    """Student quiz attempts with detailed analytics"""

    __tablename__ = "quiz_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id = Column(
        UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Attempt tracking
    attempt_number = Column(Integer, nullable=False)
    started_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Scoring
    score = Column(DECIMAL(5, 2), nullable=True)  # Percentage score
    points_earned = Column(Integer, default=0)
    points_possible = Column(Integer, default=0)
    passed = Column(Boolean, nullable=True)

    # Time tracking
    time_taken = Column(Integer, nullable=True)  # Seconds
    time_per_question = Column(JSONB, nullable=True)  # Question-level timing

    # Response data
    answers = Column(JSONB, nullable=True)  # Student answers
    question_sequence = Column(JSONB, nullable=True)  # Order questions were presented

    # AI feedback and analytics
    feedback = Column(JSONB, nullable=True)  # AI-generated feedback
    adaptive_adjustments = Column(JSONB, nullable=True)  # Difficulty adjustments made
    learning_insights = Column(JSONB, nullable=True)  # Learning pattern analysis

    # Performance metrics
    mastery_level = Column(String(20), nullable=True)  # Calculated mastery level
    confidence_score = Column(DECIMAL(5, 2), nullable=True)  # 0-100 confidence
    engagement_score = Column(DECIMAL(5, 2), nullable=True)  # 0-100 engagement

    # Relationships
    quiz = relationship("Quiz", back_populates="attempts")
    user = relationship("User", back_populates="quiz_attempts")
    session = relationship("UserSession", back_populates="quiz_attempts")

    # Constraints
    __table_args__ = (
        CheckConstraint("attempt_number > 0", name="positive_attempt_number"),
        CheckConstraint(
            "score IS NULL OR (score >= 0 AND score <= 100)", name="valid_score"
        ),
        CheckConstraint("points_earned >= 0", name="non_negative_points_earned"),
        CheckConstraint("points_possible >= 0", name="non_negative_points_possible"),
        Index(
            "ix_quiz_attempts_unique",
            "quiz_id",
            "user_id",
            "attempt_number",
            unique=True,
        ),
        Index("ix_quiz_attempts_user", "user_id"),
        Index("ix_quiz_attempts_quiz", "quiz_id"),
        Index("ix_quiz_attempts_completed", "completed_at"),
        Index("ix_quiz_attempts_score", "score"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": str(self.id),
            "quiz_id": str(self.quiz_id),
            "user_id": str(self.user_id),
            "session_id": str(self.session_id) if self.session_id else None,
            "attempt_number": self.attempt_number,
            "started_at": self.started_at.isoformat(),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "score": float(self.score) if self.score else None,
            "points_earned": self.points_earned,
            "points_possible": self.points_possible,
            "passed": self.passed,
            "time_taken": self.time_taken,
            "time_per_question": self.time_per_question,
            "answers": self.answers,
            "question_sequence": self.question_sequence,
            "feedback": self.feedback,
            "adaptive_adjustments": self.adaptive_adjustments,
            "learning_insights": self.learning_insights,
            "mastery_level": self.mastery_level,
            "confidence_score": (
                float(self.confidence_score) if self.confidence_score else None
            ),
            "engagement_score": (
                float(self.engagement_score) if self.engagement_score else None
            ),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# Export models
__all__ = [
    "QuizType",
    "MasteryLevel",
    "Quiz",
    "QuizQuestion",
    "QuizOption",
    "QuizAttempt",
]

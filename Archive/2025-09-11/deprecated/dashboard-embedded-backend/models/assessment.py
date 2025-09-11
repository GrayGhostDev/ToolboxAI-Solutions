"""
Assessment and submission models
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import JSON, Boolean, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .class_model import Class
    from .gamification import Badge
    from .lesson import Lesson
    from .user import User


class AssessmentType(enum.Enum):
    """Types of assessments"""

    QUIZ = "quiz"
    TEST = "test"
    ASSIGNMENT = "assignment"
    PROJECT = "project"
    HOMEWORK = "homework"
    EXAM = "exam"


class QuestionType(enum.Enum):
    """Types of questions"""

    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    MATCHING = "matching"
    FILL_BLANK = "fill_blank"
    CODING = "coding"


class Assessment(Base, TimestampMixin):
    """Assessment model"""

    __tablename__ = "assessments"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Basic information
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[AssessmentType] = mapped_column(
        SQLEnum(AssessmentType), nullable=False
    )

    # Associations
    teacher_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    class_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("classes.id"), nullable=False
    )
    lesson_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("lessons.id")
    )

    # Timing
    available_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    time_limit_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    # Compatibility alias used by API: duration_minutes
    # Expose as a property that maps to the DB-backed time_limit_minutes column

    # Settings
    max_attempts: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    passing_score: Mapped[int] = mapped_column(Integer, default=70, nullable=False)
    total_points: Mapped[int] = mapped_column(Integer, default=100, nullable=False)

    # Features
    shuffle_questions: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    shuffle_answers: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    show_correct_answers: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    allow_late_submission: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    late_penalty_percent: Mapped[int] = mapped_column(
        Integer, default=10, nullable=False
    )
    # Compatibility aliases
    # API expects randomize_questions and show_results names
    # We'll expose properties that map to the existing columns

    # Gamification
    xp_reward: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    badge_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("badges.id"))

    # Instructions and resources
    instructions: Mapped[Optional[str]] = mapped_column(Text)
    resources: Mapped[Optional[dict]] = mapped_column(JSON, default={})

    # Statistics
    times_taken: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_score: Mapped[Optional[float]] = mapped_column(Float)
    highest_score: Mapped[Optional[float]] = mapped_column(Float)

    # Relationships
    teacher: Mapped["User"] = relationship("User", back_populates="assessments_created")
    class_: Mapped["Class"] = relationship("Class", back_populates="assessments")
    lesson: Mapped[Optional["Lesson"]] = relationship("Lesson")
    questions: Mapped[List["AssessmentQuestion"]] = relationship(
        "AssessmentQuestion", back_populates="assessment", cascade="all, delete-orphan"
    )
    submissions: Mapped[List["AssessmentSubmission"]] = relationship(
        "AssessmentSubmission", back_populates="assessment"
    )
    reward_badge: Mapped[Optional["Badge"]] = relationship(
        "Badge", foreign_keys=[badge_id]
    )

    def __repr__(self):
        return f"<Assessment {self.title} ({self.type.value})>"

    # Backwards-compatible fields expected by API
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    @property
    def duration_minutes(self) -> Optional[int]:
        return self.time_limit_minutes

    @duration_minutes.setter
    def duration_minutes(self, value: Optional[int]) -> None:
        self.time_limit_minutes = value

    @property
    def randomize_questions(self) -> bool:
        return self.shuffle_questions

    @randomize_questions.setter
    def randomize_questions(self, value: bool) -> None:
        self.shuffle_questions = value

    @property
    def show_results(self) -> bool:
        return self.show_correct_answers

    @show_results.setter
    def show_results(self, value: bool) -> None:
        self.show_correct_answers = value


class AssessmentQuestion(Base, TimestampMixin):
    """Individual questions in an assessment"""

    __tablename__ = "assessment_questions"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Association
    assessment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessments.id"), nullable=False
    )

    # Question details
    question_type: Mapped[QuestionType] = mapped_column(
        SQLEnum(QuestionType), nullable=False
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_order: Mapped[int] = mapped_column(Integer, nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Answer options (for multiple choice, matching, etc.)
    options: Mapped[Optional[dict]] = mapped_column(JSON)  # List of options
    correct_answer: Mapped[dict] = mapped_column(
        JSON, nullable=False
    )  # Correct answer(s)

    # Additional content
    hint: Mapped[Optional[str]] = mapped_column(Text)
    explanation: Mapped[Optional[str]] = mapped_column(Text)
    media_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Grading
    partial_credit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auto_grade: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    assessment: Mapped["Assessment"] = relationship(
        "Assessment", back_populates="questions"
    )

    def __repr__(self):
        return (
            f"<AssessmentQuestion {self.question_order} ({self.question_type.value})>"
        )


class AssessmentSubmission(Base, TimestampMixin):
    """Student submissions for assessments"""

    __tablename__ = "assessment_submissions"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Associations
    assessment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessments.id"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )

    # Submission details
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    time_spent_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Status
    is_submitted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_late: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_graded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Answers and scoring
    answers: Mapped[dict] = mapped_column(JSON, nullable=False)  # Student's answers
    score: Mapped[Optional[float]] = mapped_column(Float)
    percentage: Mapped[Optional[float]] = mapped_column(Float)
    passed: Mapped[Optional[bool]] = mapped_column(Boolean)

    # Feedback
    feedback: Mapped[Optional[str]] = mapped_column(Text)
    graded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    graded_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"))

    # XP and rewards
    xp_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    badge_earned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    assessment: Mapped["Assessment"] = relationship(
        "Assessment", back_populates="submissions"
    )
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    grader: Mapped[Optional["User"]] = relationship("User", foreign_keys=[graded_by])

    def __repr__(self):
        return f"<AssessmentSubmission {self.user_id} - {self.assessment_id} (Attempt {self.attempt_number})>"

    # Backwards-compatible aliases expected by API
    @property
    def student_id(self) -> str:
        return self.user_id

    @student_id.setter
    def student_id(self, value: str) -> None:
        self.user_id = value

    @property
    def auto_graded(self) -> bool:
        return getattr(self, "auto_grade", False)

    @auto_graded.setter
    def auto_graded(self, value: bool) -> None:
        self.auto_grade = value

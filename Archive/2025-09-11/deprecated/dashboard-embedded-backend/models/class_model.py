"""
Class and enrollment models
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .assessment import Assessment
    from .lesson import Lesson
    from .user import User

# ClassEnrollment is defined in this module; do not import it here to avoid a duplicate definition


class Class(Base, TimestampMixin):
    """Class/Course model"""

    __tablename__ = "classes"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Basic information
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    description: Mapped[Optional[str]] = mapped_column(Text)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    grade_level: Mapped[int] = mapped_column(Integer, nullable=False)

    # Teacher and School
    teacher_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    school_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("schools.id")
    )

    # Schedule
    schedule: Mapped[Optional[str]] = mapped_column(
        String(200)
    )  # e.g., "MWF 9:00-10:00"
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Settings
    max_students: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_online: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allow_late_enrollment: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    # Roblox integration
    roblox_world_id: Mapped[Optional[str]] = mapped_column(String(100))
    roblox_place_id: Mapped[Optional[str]] = mapped_column(String(100))

    # Additional settings
    settings: Mapped[Optional[dict]] = mapped_column(JSON, default={})

    # Relationships
    teacher: Mapped["User"] = relationship("User", back_populates="classes_taught")
    enrollments: Mapped[List["ClassEnrollment"]] = relationship(
        "ClassEnrollment", back_populates="class_"
    )
    lessons: Mapped[List["Lesson"]] = relationship(
        "Lesson", secondary="class_lessons", back_populates="classes"
    )
    assessments: Mapped[List["Assessment"]] = relationship(
        "Assessment", back_populates="class_"
    )

    @property
    def student_count(self) -> int:
        """Get the number of enrolled students"""
        return len([e for e in self.enrollments if e.is_active])

    @property
    def lesson_ids(self) -> List[str]:
        """Return a list of lesson ids associated with this class."""
        return [l.id for l in self.lessons] if self.lessons else []

    # Backwards-compatible relationship alias expected by some API modules
    students: Mapped[List["User"]] = relationship(
        "User",
        secondary="class_enrollments",
        viewonly=True,
    )

    def __repr__(self):
        return f"<Class {self.code}: {self.name}>"


class ClassEnrollment(Base, TimestampMixin):
    """Student enrollment in classes"""

    __tablename__ = "class_enrollments"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Foreign keys
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    class_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("classes.id"), nullable=False
    )

    # Enrollment details
    enrollment_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    completion_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Progress tracking
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lessons_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    assessments_completed: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    average_score: Mapped[Optional[float]] = mapped_column(Float)

    # Gamification
    class_xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    class_rank: Mapped[Optional[int]] = mapped_column(Integer)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="enrollments")
    class_: Mapped["Class"] = relationship("Class", back_populates="enrollments")

    # Static-only alias for tools and type-checkers: some API code accesses
    # `ClassEnrollment.student_id` on the class/ORM descriptor. This annotation
    # is guarded by TYPE_CHECKING so it doesn't affect runtime SQLAlchemy
    # mappings but satisfies static analysis.
    if TYPE_CHECKING:  # pragma: no cover - type-only
        student_id: Mapped[str]

    def __repr__(self):
        return f"<Enrollment {self.user_id} in {self.class_id}>"


# Backwards-compat alias: some code expects `student_id` on the enrollment model.
# Create a runtime alias to the existing `user_id` attribute so both
# `enrollment.user_id` and `enrollment.student_id` are available at runtime.
setattr(ClassEnrollment, "student_id", ClassEnrollment.user_id)

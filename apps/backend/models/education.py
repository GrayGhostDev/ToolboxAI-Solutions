"""
SQLAlchemy Models for ToolboxAI Educational Platform
Matches Supabase database schema
"""

import uuid

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Column,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from apps.backend.core.database import Base


class User(Base):
    """User account model"""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, index=True)
    full_name = Column(String(255))
    avatar_url = Column(Text)
    bio = Column(Text)
    role = Column(String(50), default="student")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login_at = Column(TIMESTAMP(timezone=True))
    is_active = Column(Boolean, default=True)

    # Relationships
    courses_taught = relationship(
        "Course", back_populates="instructor", foreign_keys="Course.instructor_id"
    )
    enrollments = relationship("Enrollment", back_populates="user", cascade="all, delete-orphan")
    lesson_progress = relationship(
        "LessonProgress", back_populates="user", cascade="all, delete-orphan"
    )
    submissions = relationship("Submission", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    user_achievements = relationship(
        "UserAchievement", back_populates="user", cascade="all, delete-orphan"
    )


class Course(Base):
    """Course model"""

    __tablename__ = "courses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    thumbnail_url = Column(Text)
    instructor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    difficulty_level = Column(String(50), default="beginner")
    is_published = Column(Boolean, default=False)
    price = Column(Float, default=0.00)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    instructor = relationship("User", back_populates="courses_taught", foreign_keys=[instructor_id])
    lessons = relationship("Lesson", back_populates="course", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (Index("idx_courses_instructor", "instructor_id"),)


class Lesson(Base):
    """Lesson model"""

    __tablename__ = "lessons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String(255), nullable=False)
    description = Column(Text)
    content = Column(Text)
    video_url = Column(Text)
    order_index = Column(Integer, nullable=False)
    duration_minutes = Column(Integer)
    is_free = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    course = relationship("Course", back_populates="lessons")
    assignments = relationship("Assignment", back_populates="lesson", cascade="all, delete-orphan")
    lesson_progress = relationship(
        "LessonProgress", back_populates="lesson", cascade="all, delete-orphan"
    )
    comments = relationship("Comment", back_populates="lesson", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_lessons_course", "course_id"),
        Index("idx_lessons_order", "course_id", "order_index"),
    )


class Enrollment(Base):
    """Course enrollment model"""

    __tablename__ = "enrollments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    enrolled_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    completed_at = Column(TIMESTAMP(timezone=True))
    progress_percentage = Column(Float, default=0.00)

    # Relationships
    user = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")

    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_user_course"),
        Index("idx_enrollments_user", "user_id"),
        Index("idx_enrollments_course", "course_id"),
    )


class LessonProgress(Base):
    """Lesson progress tracking model"""

    __tablename__ = "lesson_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lesson_id = Column(
        UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False
    )
    completed = Column(Boolean, default=False)
    completed_at = Column(TIMESTAMP(timezone=True))
    time_spent_minutes = Column(Integer, default=0)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="lesson_progress")
    lesson = relationship("Lesson", back_populates="lesson_progress")

    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson"),
        Index("idx_lesson_progress_user", "user_id"),
    )


class Assignment(Base):
    """Assignment model"""

    __tablename__ = "assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lesson_id = Column(
        UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String(255), nullable=False)
    description = Column(Text)
    instructions = Column(Text)
    due_date = Column(TIMESTAMP(timezone=True))
    max_score = Column(Integer, default=100)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    lesson = relationship("Lesson", back_populates="assignments")
    submissions = relationship(
        "Submission", back_populates="assignment", cascade="all, delete-orphan"
    )


class Submission(Base):
    """Assignment submission model"""

    __tablename__ = "submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id = Column(
        UUID(as_uuid=True), ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text)
    file_url = Column(Text)
    score = Column(Integer)
    feedback = Column(Text)
    submitted_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    graded_at = Column(TIMESTAMP(timezone=True))

    # Relationships
    assignment = relationship("Assignment", back_populates="submissions")
    user = relationship("User", back_populates="submissions")

    # Constraints
    __table_args__ = (UniqueConstraint("assignment_id", "user_id", name="uq_assignment_user"),)


class Comment(Base):
    """Comment model"""

    __tablename__ = "comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lesson_id = Column(
        UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False
    )
    content = Column(Text, nullable=False)
    parent_comment_id = Column(UUID(as_uuid=True), ForeignKey("comments.id", ondelete="CASCADE"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="comments")
    lesson = relationship("Lesson", back_populates="comments")
    parent_comment = relationship("Comment", remote_side=[id], backref="replies")

    # Indexes
    __table_args__ = (
        Index("idx_comments_lesson", "lesson_id"),
        Index("idx_comments_user", "user_id"),
    )


class Achievement(Base):
    """Achievement model"""

    __tablename__ = "achievements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    icon_url = Column(Text)
    points = Column(Integer, default=0)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    user_achievements = relationship(
        "UserAchievement", back_populates="achievement", cascade="all, delete-orphan"
    )


class UserAchievement(Base):
    """User achievement model"""

    __tablename__ = "user_achievements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    achievement_id = Column(
        UUID(as_uuid=True), ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False
    )
    earned_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="user_achievements")
    achievement = relationship("Achievement", back_populates="user_achievements")

    # Constraints
    __table_args__ = (UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),)

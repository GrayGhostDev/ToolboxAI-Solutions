"""
User model for the educational platform
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import JSON, Boolean, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .assessment import Assessment
    from .class_model import Class, ClassEnrollment
    from .gamification import UserBadge, XPTransaction
    from .lesson import Lesson
    from .message import Message, MessageRecipient


class UserRole(enum.Enum):
    """User roles in the platform"""

    ADMIN = "Admin"
    TEACHER = "Teacher"
    STUDENT = "Student"
    PARENT = "Parent"


class User(Base, TimestampMixin):
    """User model"""

    __tablename__ = "users"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Authentication
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    username: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Profile
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(200))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Role and permissions
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Gamification
    total_xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    streak_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    best_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timestamps
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    # COPPA/FERPA/GDPR compliance
    birth_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    parent_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"))
    consent_given: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Additional settings
    preferences: Mapped[Optional[dict]] = mapped_column(JSON, default={})
    language: Mapped[str] = mapped_column(String(5), default="en", nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)

    # Relationships
    parent: Mapped[Optional["User"]] = relationship(
        "User", remote_side=[id], backref="children"
    )
    enrollments: Mapped[List["ClassEnrollment"]] = relationship(
        "ClassEnrollment", back_populates="user"
    )
    xp_transactions: Mapped[List["XPTransaction"]] = relationship(
        "XPTransaction", back_populates="user"
    )
    badges: Mapped[List["UserBadge"]] = relationship("UserBadge", back_populates="user")
    sent_messages: Mapped[List["Message"]] = relationship(
        "Message", foreign_keys="Message.sender_id", back_populates="sender"
    )
    received_messages: Mapped[List["MessageRecipient"]] = relationship(
        "MessageRecipient", back_populates="recipient"
    )

    # For teachers
    classes_taught: Mapped[List["Class"]] = relationship(
        "Class", back_populates="teacher"
    )
    lessons_created: Mapped[List["Lesson"]] = relationship(
        "Lesson", back_populates="teacher"
    )
    assessments_created: Mapped[List["Assessment"]] = relationship(
        "Assessment", back_populates="teacher"
    )

    def __repr__(self):
        return f"<User {self.username} ({self.role.value})>"

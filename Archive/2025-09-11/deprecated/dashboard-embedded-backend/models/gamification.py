"""
Gamification models for XP, badges, and leaderboards
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, Boolean, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .assessment import Assessment
    from .class_model import Class
    from .lesson import Lesson
    from .user import User


class XPSource(enum.Enum):
    """Source of XP gain"""

    LESSON = "lesson"
    ASSESSMENT = "assessment"
    ACHIEVEMENT = "achievement"
    BONUS = "bonus"
    DAILY = "daily"
    STREAK = "streak"
    CHALLENGE = "challenge"


class BadgeCategory(enum.Enum):
    """Badge categories"""

    ACHIEVEMENT = "achievement"
    MILESTONE = "milestone"
    SOCIAL = "social"
    CONSISTENCY = "consistency"
    MASTERY = "mastery"
    SPECIAL = "special"


class BadgeRarity(enum.Enum):
    """Badge rarity levels"""

    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class XPTransaction(Base, TimestampMixin):
    """Track all XP transactions"""

    __tablename__ = "xp_transactions"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # User
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )

    # XP details
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[XPSource] = mapped_column(SQLEnum(XPSource), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)

    # Related entities
    lesson_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("lessons.id")
    )
    assessment_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("assessments.id")
    )
    class_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("classes.id")
    )

    # Multipliers and bonuses
    multiplier: Mapped[float] = mapped_column(Integer, default=1.0, nullable=False)
    bonus_applied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # User stats at time of transaction
    total_xp_after: Mapped[int] = mapped_column(Integer, nullable=False)
    level_after: Mapped[int] = mapped_column(Integer, nullable=False)
    level_up: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="xp_transactions")
    lesson: Mapped[Optional["Lesson"]] = relationship("Lesson")
    assessment: Mapped[Optional["Assessment"]] = relationship("Assessment")
    class_: Mapped[Optional["Class"]] = relationship("Class")

    def __repr__(self):
        return f"<XPTransaction {self.user_id} +{self.amount} ({self.source.value})>"


class Badge(Base, TimestampMixin):
    """Badge definitions"""

    __tablename__ = "badges"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Badge information
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[BadgeCategory] = mapped_column(
        SQLEnum(BadgeCategory), nullable=False
    )
    rarity: Mapped[BadgeRarity] = mapped_column(SQLEnum(BadgeRarity), nullable=False)

    # Visual
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    icon_url: Mapped[Optional[str]] = mapped_column(String(500))
    color: Mapped[str] = mapped_column(String(7), default="#FFD700")  # Hex color

    # Requirements
    requirements: Mapped[dict] = mapped_column(
        JSON, nullable=False
    )  # JSON structure for requirements
    xp_reward: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Availability
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    available_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    available_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Statistics
    times_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    user_badges: Mapped[list["UserBadge"]] = relationship(
        "UserBadge", back_populates="badge"
    )

    def __repr__(self):
        return f"<Badge {self.name} ({self.rarity.value})>"


class UserBadge(Base, TimestampMixin):
    """Track badges earned by users"""

    __tablename__ = "user_badges"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Foreign keys
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    badge_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("badges.id"), nullable=False
    )

    # Earning details
    earned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    progress: Mapped[int] = mapped_column(
        Integer, default=100, nullable=False
    )  # Percentage

    # Context
    lesson_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("lessons.id")
    )
    assessment_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("assessments.id")
    )
    class_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("classes.id")
    )

    # Display
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="badges")
    badge: Mapped["Badge"] = relationship("Badge", back_populates="user_badges")
    lesson: Mapped[Optional["Lesson"]] = relationship("Lesson")
    assessment: Mapped[Optional["Assessment"]] = relationship("Assessment")
    class_: Mapped[Optional["Class"]] = relationship("Class")

    def __repr__(self):
        return f"<UserBadge {self.user_id} - {self.badge_id}>"


class LeaderboardEntry(Base, TimestampMixin):
    """Cached leaderboard entries for performance"""

    __tablename__ = "leaderboard_entries"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # User and scope
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    class_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("classes.id")
    )

    # Time period
    period_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "daily", "weekly", "monthly", "all_time"
    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Rankings
    rank: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    previous_rank: Mapped[Optional[int]] = mapped_column(Integer)

    # Stats
    xp_earned: Mapped[int] = mapped_column(Integer, nullable=False)
    lessons_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    badges_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    streak_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User")
    class_: Mapped[Optional["Class"]] = relationship("Class")

    def __repr__(self):
        return (
            f"<LeaderboardEntry {self.user_id} Rank #{self.rank} ({self.period_type})>"
        )

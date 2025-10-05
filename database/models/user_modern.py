"""
Modern User Models with SQLAlchemy 2.0 (2025 Standards)

Implements user management models with:
- Type-safe Mapped annotations
- Async-compatible relationships
- Modern SQLAlchemy 2.0 patterns
- Row-level security support

Reference: https://docs.sqlalchemy.org/en/20/
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List
from uuid import UUID

from sqlalchemy import String, Boolean, Index, CheckConstraint, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY

from database.models.base_modern import TenantBaseModel, GlobalBaseModel, Base


class UserRole(PyEnum):
    """User role enumeration for access control."""
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"
    PARENT = "parent"


class UserStatus(PyEnum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class User(TenantBaseModel):
    """
    User model with multi-tenant support.

    Includes:
    - Authentication credentials
    - Profile information
    - Role-based access control
    - Email verification
    - Account status tracking
    """
    __tablename__ = "users"

    # Authentication
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    username: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Profile
    full_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    # Role and Status
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=False),
        nullable=False,
        default=UserRole.STUDENT,
        index=True,
    )

    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="user_status", native_enum=False),
        nullable=False,
        default=UserStatus.PENDING,
        index=True,
    )

    # Email Verification
    email_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    email_verified_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
    )

    # Security
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
    )

    last_login_ip: Mapped[Optional[str]] = mapped_column(
        String(45),  # Support IPv6
        nullable=True,
    )

    failed_login_attempts: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    locked_until: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
    )

    # Preferences
    timezone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="UTC",
    )

    language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="en",
    )

    # Relationships
    profile: Mapped[Optional["UserProfile"]] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",  # Eager loading for single relationship
    )

    sessions: Mapped[List["UserSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",  # Lazy load for collections
    )

    # Table constraints
    __table_args__ = (
        # Composite unique constraint for email + tenant
        Index(
            "idx_user_email_org",
            "email",
            "organization_id",
            unique=True,
        ),
        # Composite unique constraint for username + tenant
        Index(
            "idx_user_username_org",
            "username",
            "organization_id",
            unique=True,
        ),
        # Index for active users query
        Index(
            "idx_user_active",
            "organization_id",
            "status",
            postgresql_where=(status == UserStatus.ACTIVE),
        ),
        # Check constraint for email format
        CheckConstraint(
            "email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'",
            name="check_user_email_format",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<User(id='{self.id}', email='{self.email}', "
            f"role='{self.role.value}', status='{self.status.value}')>"
        )

    @property
    def is_active(self) -> bool:
        """Check if user account is active."""
        return self.status == UserStatus.ACTIVE and not self.is_deleted

    @property
    def is_locked(self) -> bool:
        """Check if account is locked."""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until

    def verify_email(self) -> None:
        """Mark email as verified."""
        self.email_verified = True
        self.email_verified_at = datetime.utcnow()

    def record_login(self, ip_address: str) -> None:
        """Record successful login."""
        self.last_login_at = datetime.utcnow()
        self.last_login_ip = ip_address
        self.failed_login_attempts = 0
        self.locked_until = None

    def record_failed_login(self, max_attempts: int = 5) -> bool:
        """
        Record failed login attempt.

        Args:
            max_attempts: Maximum attempts before locking account

        Returns:
            True if account is now locked, False otherwise
        """
        self.failed_login_attempts += 1

        if self.failed_login_attempts >= max_attempts:
            # Lock account for 30 minutes
            from datetime import timedelta
            self.locked_until = datetime.utcnow() + timedelta(minutes=30)
            return True

        return False


class UserProfile(TenantBaseModel):
    """
    Extended user profile information.

    One-to-one relationship with User model.
    """
    __tablename__ = "user_profiles"

    # Foreign key to User
    user_id: Mapped[UUID] = mapped_column(
        nullable=False,
        index=True,
        unique=True,  # One-to-one relationship
    )

    # Profile fields
    bio: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    date_of_birth: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
    )

    phone_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )

    # Social links
    website_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    github_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    linkedin_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    # Skills and interests (PostgreSQL array)
    skills: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(50)),
        nullable=True,
        default=list,
    )

    interests: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(50)),
        nullable=True,
        default=list,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="profile",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<UserProfile(user_id='{self.user_id}')>"


class UserSession(TenantBaseModel):
    """
    User session tracking for security and analytics.

    Tracks active user sessions with JWT tokens.
    """
    __tablename__ = "user_sessions"

    # Foreign key to User
    user_id: Mapped[UUID] = mapped_column(
        nullable=False,
        index=True,
    )

    # Session data
    token_jti: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    refresh_token_jti: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
    )

    # Session metadata
    ip_address: Mapped[str] = mapped_column(
        String(45),
        nullable=False,
    )

    user_agent: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    device_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    # Session status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        nullable=False,
        index=True,
    )

    last_activity_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="sessions",
        lazy="selectin",
    )

    # Table constraints
    __table_args__ = (
        # Index for active sessions query
        Index(
            "idx_session_active_user",
            "user_id",
            "is_active",
            postgresql_where=(is_active == True),
        ),
        # Index for expired sessions cleanup
        Index(
            "idx_session_expires",
            "expires_at",
            "is_active",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<UserSession(user_id='{self.user_id}', "
            f"active={self.is_active}, expires='{self.expires_at}')>"
        )

    @property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.utcnow() >= self.expires_at

    def invalidate(self) -> None:
        """Invalidate this session."""
        self.is_active = False

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity_at = datetime.utcnow()


# Export all models
__all__ = [
    "User",
    "UserProfile",
    "UserSession",
    "UserRole",
    "UserStatus",
]

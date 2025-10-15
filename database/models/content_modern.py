"""
Modern Content Models with SQLAlchemy 2.0 (2025 Standards)

Implements educational content models with:
- Type-safe Mapped annotations
- Full-text search support
- Version control
- Async-compatible relationships

Reference: https://docs.sqlalchemy.org/en/20/
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import (
    String,
    Text,
    Integer,
    Boolean,
    Index,
    CheckConstraint,
    Enum,
    Computed,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, TSVECTOR
from sqlalchemy.ext.hybrid import hybrid_property

from database.models.base_modern import TenantBaseModel


class ContentStatus(PyEnum):
    """Content approval and workflow status."""
    DRAFT = "draft"
    PENDING = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"
    PUBLISHED = "published"


class DifficultyLevel(PyEnum):
    """Difficulty level for educational content."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class ContentType(PyEnum):
    """Type of educational content."""
    LESSON = "lesson"
    TUTORIAL = "tutorial"
    EXERCISE = "exercise"
    QUIZ = "quiz"
    PROJECT = "project"
    REFERENCE = "reference"


class EducationalContent(TenantBaseModel):
    """
    Educational content with versioning and full-text search.

    Features:
    - Multi-tenant isolation
    - Version control
    - Full-text search (PostgreSQL tsvector)
    - Metadata storage (JSONB)
    - Status workflow
    """
    __tablename__ = "educational_content"

    # Basic Information
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    slug: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Classification
    content_type: Mapped[ContentType] = mapped_column(
        Enum(ContentType, name="content_type", native_enum=False),
        nullable=False,
        index=True,
    )

    difficulty_level: Mapped[DifficultyLevel] = mapped_column(
        Enum(DifficultyLevel, name="difficulty_level", native_enum=False),
        nullable=False,
        index=True,
    )

    # Status and Workflow
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus, name="content_status", native_enum=False),
        nullable=False,
        default=ContentStatus.DRAFT,
        index=True,
    )

    published_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        index=True,
    )

    # Authorship
    author_id: Mapped[UUID] = mapped_column(
        nullable=False,
        index=True,
    )

    reviewer_id: Mapped[Optional[UUID]] = mapped_column(
        nullable=True,
    )

    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
    )

    # Version Control
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    is_latest_version: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    parent_content_id: Mapped[Optional[UUID]] = mapped_column(
        nullable=True,
        index=True,
    )

    # Metadata and Settings
    content_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    settings: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    # Tags and Categories
    tags: Mapped[List[str]] = mapped_column(
        ARRAY(String(50)),
        nullable=False,
        default=list,
    )

    # Statistics
    view_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    completion_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    average_rating: Mapped[Optional[float]] = mapped_column(
        nullable=True,
    )

    # Duration and Prerequisites
    estimated_duration_minutes: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    prerequisites: Mapped[List[str]] = mapped_column(
        ARRAY(String(100)),
        nullable=False,
        default=list,
    )

    # Learning Objectives
    learning_objectives: Mapped[List[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        default=list,
    )

    # Full-text Search Vector (PostgreSQL specific)
    search_vector: Mapped[Optional[str]] = mapped_column(
        TSVECTOR,
        Computed(
            "to_tsvector('english', "
            "coalesce(title, '') || ' ' || "
            "coalesce(description, '') || ' ' || "
            "coalesce(content, ''))",
            persisted=True,
        ),
    )

    # Relationships
    attachments: Mapped[List["ContentAttachment"]] = relationship(
        back_populates="content",
        cascade="all, delete-orphan",
        lazy="select",
    )

    comments: Mapped[List["ContentComment"]] = relationship(
        back_populates="content",
        cascade="all, delete-orphan",
        lazy="select",
    )

    ratings: Mapped[List["ContentRating"]] = relationship(
        back_populates="content",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # Table constraints and indexes
    __table_args__ = (
        # Unique slug per organization
        Index(
            "idx_content_slug_org",
            "slug",
            "organization_id",
            unique=True,
        ),
        # Published content index
        Index(
            "idx_content_published",
            "organization_id",
            "status",
            "published_at",
            postgresql_where=(status == ContentStatus.PUBLISHED),
        ),
        # Full-text search index (GIN)
        Index(
            "idx_content_search",
            "search_vector",
            postgresql_using="gin",
        ),
        # Latest version index
        Index(
            "idx_content_latest",
            "organization_id",
            "is_latest_version",
            postgresql_where=(is_latest_version == True),
        ),
        # Check constraints
        CheckConstraint(
            "version > 0",
            name="check_content_version_positive",
        ),
        CheckConstraint(
            "view_count >= 0",
            name="check_content_view_count_positive",
        ),
        CheckConstraint(
            "average_rating IS NULL OR (average_rating >= 0 AND average_rating <= 5)",
            name="check_content_rating_range",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<EducationalContent(id='{self.id}', title='{self.title}', "
            f"status='{self.status.value}', version={self.version})>"
        )

    @hybrid_property
    def is_published(self) -> bool:
        """Check if content is published."""
        return self.status == ContentStatus.PUBLISHED

    def publish(self, reviewer_id: UUID) -> None:
        """Publish content."""
        self.status = ContentStatus.PUBLISHED
        self.published_at = datetime.utcnow()
        self.reviewer_id = reviewer_id
        self.reviewed_at = datetime.utcnow()

    def unpublish(self) -> None:
        """Unpublish content."""
        self.status = ContentStatus.DRAFT
        self.published_at = None

    def increment_views(self) -> None:
        """Increment view counter."""
        self.view_count += 1

    def increment_completions(self) -> None:
        """Increment completion counter."""
        self.completion_count += 1


class ContentAttachment(TenantBaseModel):
    """
    File attachments for educational content.

    Supports images, documents, videos, etc.
    """
    __tablename__ = "content_attachments"

    # Foreign key to content
    content_id: Mapped[UUID] = mapped_column(
        nullable=False,
        index=True,
    )

    # File information
    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    file_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    file_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    file_size_bytes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # Metadata
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    attachment_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    # Order for display
    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Relationships
    content: Mapped["EducationalContent"] = relationship(
        back_populates="attachments",
        lazy="selectin",
    )

    __table_args__ = (
        Index(
            "idx_attachment_content",
            "content_id",
            "display_order",
        ),
    )

    def __repr__(self) -> str:
        return f"<ContentAttachment(filename='{self.filename}', type='{self.file_type}')>"


class ContentComment(TenantBaseModel):
    """
    User comments on educational content.

    Supports threaded discussions.
    """
    __tablename__ = "content_comments"

    # Foreign keys
    content_id: Mapped[UUID] = mapped_column(
        nullable=False,
        index=True,
    )

    user_id: Mapped[UUID] = mapped_column(
        nullable=False,
        index=True,
    )

    # Threading support
    parent_comment_id: Mapped[Optional[UUID]] = mapped_column(
        nullable=True,
        index=True,
    )

    # Comment content
    comment_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Moderation
    is_approved: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    is_flagged: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # Engagement
    upvotes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Relationships
    content: Mapped["EducationalContent"] = relationship(
        back_populates="comments",
        lazy="selectin",
    )

    __table_args__ = (
        Index(
            "idx_comment_content_user",
            "content_id",
            "user_id",
        ),
        Index(
            "idx_comment_approved",
            "content_id",
            "is_approved",
            postgresql_where=(is_approved == True),
        ),
    )

    def __repr__(self) -> str:
        return f"<ContentComment(user_id='{self.user_id}', flagged={self.is_flagged})>"


class ContentRating(TenantBaseModel):
    """
    User ratings for educational content.

    One rating per user per content item.
    """
    __tablename__ = "content_ratings"

    # Foreign keys
    content_id: Mapped[UUID] = mapped_column(
        nullable=False,
        index=True,
    )

    user_id: Mapped[UUID] = mapped_column(
        nullable=False,
        index=True,
    )

    # Rating value (1-5 stars)
    rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Optional review text
    review_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Helpfulness votes
    helpful_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Relationships
    content: Mapped["EducationalContent"] = relationship(
        back_populates="ratings",
        lazy="selectin",
    )

    __table_args__ = (
        # One rating per user per content
        Index(
            "idx_rating_content_user",
            "content_id",
            "user_id",
            unique=True,
        ),
        CheckConstraint(
            "rating >= 1 AND rating <= 5",
            name="check_rating_range",
        ),
    )

    def __repr__(self) -> str:
        return f"<ContentRating(rating={self.rating}, helpful={self.helpful_count})>"


# Export all models
__all__ = [
    "EducationalContent",
    "ContentAttachment",
    "ContentComment",
    "ContentRating",
    "ContentStatus",
    "DifficultyLevel",
    "ContentType",
]

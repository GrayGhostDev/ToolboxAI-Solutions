"""
Roblox Environment Database Models
Defines SQLAlchemy models for Roblox environment storage and management

Multi-tenant: All models use organization_id for tenant isolation
Updated: 2025-10-10 (Added multi-tenant support)
"""

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, JSON, Text,
    ForeignKey, Enum as SQLEnum, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any

# Import tenant-aware base models
from database.models.base import TenantBaseModel


class EnvironmentStatus(str, Enum):
    """Environment status enum"""
    CREATING = "creating"
    ACTIVE = "active"
    UPDATING = "updating"
    INACTIVE = "inactive"
    FAILED = "failed"
    DELETED = "deleted"


class EnvironmentVisibility(str, Enum):
    """Environment visibility enum"""
    PRIVATE = "private"
    PUBLIC = "public"
    SHARED = "shared"
    CLASS = "class"


class RobloxEnvironment(TenantBaseModel):
    """
    Roblox Environment model - Stores created Roblox environments

    Multi-tenant: organization_id inherited from TenantBaseModel
    Note: Uses Integer ID for backwards compatibility (overrides UUID default)
    """
    __tablename__ = "roblox_environments"

    # Override id to use Integer for backwards compatibility
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Note: organization_id, created_at, updated_at, deleted_at inherited from TenantBaseModel

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Environment identification
    name = Column(String(255), nullable=False)
    description = Column(Text)
    project_path = Column(String(512))
    rojo_url = Column(String(512))

    # Educational metadata
    grade_level = Column(String(50))
    subject = Column(String(100))
    learning_objectives = Column(JSON)

    # Configuration
    max_players = Column(Integer, default=20)
    status = Column(SQLEnum(EnvironmentStatus), default=EnvironmentStatus.CREATING, index=True)
    visibility = Column(SQLEnum(EnvironmentVisibility), default=EnvironmentVisibility.PRIVATE)

    # Environment structure and components
    components = Column(JSON)  # Parsed components from description
    structure = Column(JSON)   # Rojo structure data
    visualization_data = Column(JSON)  # 3D visualization metadata

    # Usage statistics
    total_sessions = Column(Integer, default=0)
    total_playtime_minutes = Column(Integer, default=0)
    average_players = Column(Float, default=0.0)
    last_accessed = Column(DateTime(timezone=True))

    # Versioning
    version = Column(Integer, default=1)
    parent_environment_id = Column(Integer, ForeignKey("roblox_environments.id"), nullable=True)

    # Additional settings
    settings = Column(JSON)
    environment_metadata = Column(JSON)  # Renamed from 'metadata' to avoid SQLAlchemy reserved word

    # Additional timestamps (created_at, updated_at, deleted_at inherited from TenantBaseModel)
    published_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="roblox_environments")
    sessions = relationship("RobloxSession", back_populates="environment", cascade="all, delete-orphan")
    versions = relationship("RobloxEnvironment", backref="parent_environment", remote_side=[id])
    shared_with = relationship("EnvironmentShare", back_populates="environment", cascade="all, delete-orphan")

    # Constraints and indexes (organization_id index auto-created by TenantMixin)
    __table_args__ = (
        Index("idx_roblox_env_org_user_status", "organization_id", "user_id", "status"),
        Index("idx_roblox_env_org_created", "organization_id", "created_at"),
        UniqueConstraint("organization_id", "user_id", "name", name="uq_org_user_environment_name"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert environment to dictionary."""
        return {
            "id": self.id,
            "organization_id": str(self.organization_id),
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "project_path": self.project_path,
            "rojo_url": self.rojo_url,
            "grade_level": self.grade_level,
            "subject": self.subject,
            "learning_objectives": self.learning_objectives,
            "max_players": self.max_players,
            "status": self.status.value if self.status else None,
            "visibility": self.visibility.value if self.visibility else None,
            "components": self.components,
            "structure": self.structure,
            "visualization_data": self.visualization_data,
            "total_sessions": self.total_sessions,
            "total_playtime_minutes": self.total_playtime_minutes,
            "average_players": self.average_players,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "version": self.version,
            "settings": self.settings,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
        }


class RobloxSession(TenantBaseModel):
    """
    Roblox Session model - Tracks individual play sessions in environments

    Multi-tenant: organization_id inherited from TenantBaseModel
    Note: Uses Integer ID for backwards compatibility (overrides UUID default)
    """
    __tablename__ = "roblox_sessions"

    # Override id to use Integer for backwards compatibility
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Note: organization_id, created_at, updated_at inherited from TenantBaseModel

    environment_id = Column(Integer, ForeignKey("roblox_environments.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Session info
    session_uuid = Column(String(36), unique=True, index=True)
    player_count = Column(Integer, default=1)
    duration_minutes = Column(Integer)

    # Performance metrics
    avg_fps = Column(Float)
    peak_memory_mb = Column(Float)
    errors_count = Column(Integer, default=0)

    # Educational tracking
    learning_milestones = Column(JSON)
    quiz_scores = Column(JSON)
    achievements_unlocked = Column(JSON)

    # Session metadata
    client_info = Column(JSON)  # Browser, OS, etc.
    interaction_data = Column(JSON)  # Click paths, usage patterns

    # Session timestamps (created_at, updated_at inherited from TenantBaseModel)
    # started_at maps to created_at for sessions
    ended_at = Column(DateTime(timezone=True))

    # Relationships
    environment = relationship("RobloxEnvironment", back_populates="sessions")
    user = relationship("User", back_populates="roblox_sessions")

    # Constraints and indexes (organization_id index auto-created by TenantMixin)
    __table_args__ = (
        Index("idx_roblox_session_org_env_user", "organization_id", "environment_id", "user_id"),
        Index("idx_roblox_session_org_created", "organization_id", "created_at"),
    )


class EnvironmentShare(TenantBaseModel):
    """
    Environment Share model - Tracks sharing permissions for environments

    Multi-tenant: organization_id inherited from TenantBaseModel
    Note: Uses Integer ID for backwards compatibility (overrides UUID default)
    """
    __tablename__ = "environment_shares"

    # Override id to use Integer for backwards compatibility
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Note: organization_id, created_at, updated_at inherited from TenantBaseModel

    environment_id = Column(Integer, ForeignKey("roblox_environments.id"), nullable=False, index=True)
    shared_with_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    shared_with_class_id = Column(Integer, ForeignKey("classes.id"), nullable=True, index=True)

    # Permissions
    can_view = Column(Boolean, default=True)
    can_edit = Column(Boolean, default=False)
    can_clone = Column(Boolean, default=True)
    can_reshare = Column(Boolean, default=False)

    # Share metadata
    share_message = Column(Text)
    expires_at = Column(DateTime(timezone=True))
    accessed_at = Column(DateTime(timezone=True))

    # Note: created_at, updated_at timestamps inherited from TenantBaseModel

    # Relationships
    environment = relationship("RobloxEnvironment", back_populates="shared_with")
    user = relationship("User", backref="environment_shares")

    # Constraints and indexes (organization_id index auto-created by TenantMixin)
    __table_args__ = (
        Index("idx_env_share_org_user", "organization_id", "shared_with_user_id"),
        Index("idx_env_share_org_class", "organization_id", "shared_with_class_id"),
        UniqueConstraint("organization_id", "environment_id", "shared_with_user_id", name="uq_org_env_user_share"),
    )


class EnvironmentTemplate(TenantBaseModel):
    """
    Environment Template model - Pre-built environment templates

    Multi-tenant: organization_id inherited from TenantBaseModel
    Note: Uses Integer ID for backwards compatibility (overrides UUID default)
    """
    __tablename__ = "environment_templates"

    # Override id to use Integer for backwards compatibility
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Note: organization_id, created_at, updated_at, created_by_id inherited from TenantBaseModel

    # Template info
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))  # Science, Math, History, etc.
    difficulty = Column(String(50))  # Beginner, Intermediate, Advanced

    # Template structure
    base_components = Column(JSON)
    default_settings = Column(JSON)
    required_features = Column(JSON)

    # Educational metadata
    grade_levels = Column(JSON)  # Array of applicable grades
    subjects = Column(JSON)      # Array of subjects
    standards_aligned = Column(JSON)  # Educational standards

    # Usage stats
    usage_count = Column(Integer, default=0)
    average_rating = Column(Float)
    is_featured = Column(Boolean, default=False)
    is_public = Column(Boolean, default=True)

    # Thumbnails and media
    thumbnail_url = Column(String(512))
    preview_images = Column(JSON)

    # Additional timestamps (created_at, updated_at, created_by_id inherited from TenantBaseModel)
    published_at = Column(DateTime(timezone=True))

    # Relationships
    creator = relationship("User", backref="environment_templates")

    # Constraints and indexes (organization_id index auto-created by TenantMixin)
    __table_args__ = (
        Index("idx_template_org_category", "organization_id", "category"),
        Index("idx_template_org_public_featured", "organization_id", "is_public", "is_featured"),
    )


# Export models
__all__ = [
    "RobloxEnvironment",
    "RobloxSession",
    "EnvironmentShare",
    "EnvironmentTemplate",
    "EnvironmentStatus",
    "EnvironmentVisibility",
]

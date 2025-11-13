"""
Storage Models for ToolBoxAI Educational Platform

Implements file storage with multi-tenant isolation, version tracking,
and compliance features for educational content.

Features:
- Multi-tenant file isolation with organization_id
- File versioning and history tracking
- Sharing capabilities with expiration
- Storage quota management per organization
- COPPA/FERPA compliance fields
- Soft delete with retention policies

Author: ToolBoxAI Team
Created: 2025-01-27
Version: 1.0.0
"""

import enum
from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func

from database.models.base import AuditMixin, GlobalBaseModel, TenantBaseModel, TimestampMixin


class FileStatus(enum.Enum):
    """File status enumeration"""

    PENDING = "pending"  # Upload in progress
    PROCESSING = "processing"  # Virus scanning, optimization
    AVAILABLE = "available"  # Ready for use
    QUARANTINED = "quarantined"  # Failed virus scan
    DELETED = "deleted"  # Soft deleted
    ARCHIVED = "archived"  # Long-term archive
    ERROR = "error"  # Processing error


class FileCategory(enum.Enum):
    """File category for compliance and retention"""

    EDUCATIONAL_CONTENT = "educational_content"
    STUDENT_SUBMISSION = "student_submission"
    ASSESSMENT = "assessment"
    ADMINISTRATIVE = "administrative"
    MEDIA_RESOURCE = "media_resource"
    TEMPORARY = "temporary"
    AVATAR = "avatar"
    REPORT = "report"


class ShareType(enum.Enum):
    """File sharing type"""

    PUBLIC_LINK = "public_link"
    ORGANIZATION = "organization"
    SPECIFIC_USERS = "specific_users"
    CLASS = "class"
    TEMPORARY = "temporary"


class File(TenantBaseModel, TimestampMixin, AuditMixin):
    """
    Main file storage model with multi-tenant isolation
    """

    __tablename__ = "files"
    __table_args__ = (
        Index("idx_files_organization_status", "organization_id", "status"),
        Index("idx_files_category", "category"),
        Index("idx_files_uploaded_by", "uploaded_by"),
        Index("idx_files_created_at", "created_at"),
        CheckConstraint("file_size > 0", name="check_file_size_positive"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # File metadata
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)  # Size in bytes
    mime_type = Column(String(127), nullable=False)
    file_extension = Column(String(20))

    # Storage information
    storage_path = Column(Text, nullable=False)  # Path in Supabase storage
    bucket_name = Column(String(255), nullable=False)
    cdn_url = Column(Text)  # CDN URL for optimized delivery
    thumbnail_url = Column(Text)  # Thumbnail for images/videos

    # File properties
    status = Column(Enum(FileStatus), default=FileStatus.PENDING, nullable=False)
    category = Column(Enum(FileCategory), default=FileCategory.MEDIA_RESOURCE, nullable=False)
    checksum = Column(String(64))  # SHA256 hash

    # Security and scanning
    virus_scanned = Column(Boolean, default=False)
    virus_scan_result = Column(JSON)  # Scan details
    last_scanned_at = Column(DateTime(timezone=True))

    # Compliance fields
    contains_pii = Column(Boolean, default=False)
    requires_consent = Column(Boolean, default=False)
    retention_days = Column(Integer)  # Days to retain before auto-delete
    deletion_date = Column(DateTime(timezone=True))  # Scheduled deletion

    # User relationship
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Metadata
    title = Column(String(255))
    description = Column(Text)
    tags = Column(JSON, default=list)  # Array of tags
    file_metadata = Column(
        JSON, default=dict
    )  # Additional metadata (renamed from 'metadata' to avoid SQLAlchemy reserved word)

    # Access tracking
    download_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime(timezone=True))

    # Relationships
    versions = relationship("FileVersion", back_populates="file", cascade="all, delete-orphan")
    shares = relationship("FileShare", back_populates="file", cascade="all, delete-orphan")

    @validates("mime_type")
    def validate_mime_type(self, key, mime_type):
        """Validate MIME type format"""
        if not mime_type or "/" not in mime_type:
            raise ValueError(f"Invalid MIME type: {mime_type}")
        return mime_type

    @property
    def is_image(self) -> bool:
        """Check if file is an image"""
        return self.mime_type.startswith("image/")

    @property
    def is_video(self) -> bool:
        """Check if file is a video"""
        return self.mime_type.startswith("video/")

    @property
    def is_document(self) -> bool:
        """Check if file is a document"""
        return self.mime_type in [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]

    def get_size_mb(self) -> float:
        """Get file size in MB"""
        return self.file_size / (1024 * 1024)

    def should_be_deleted(self) -> bool:
        """Check if file should be deleted based on retention policy"""
        if self.deletion_date:
            return datetime.utcnow() >= self.deletion_date
        return False


class FileVersion(TenantBaseModel, TimestampMixin):
    """
    File version tracking for audit and rollback
    """

    __tablename__ = "file_versions"
    __table_args__ = (
        Index("idx_file_versions_file_id", "file_id"),
        Index("idx_file_versions_created_at", "created_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id"), nullable=False)

    # Version information
    version_number = Column(Integer, nullable=False)
    storage_path = Column(Text, nullable=False)
    file_size = Column(BigInteger, nullable=False)
    checksum = Column(String(64))

    # Change tracking
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    change_description = Column(Text)

    # Relationships
    file = relationship("File", back_populates="versions")


class FileShare(TenantBaseModel, TimestampMixin):
    """
    File sharing and access control
    """

    __tablename__ = "file_shares"
    __table_args__ = (
        Index("idx_file_shares_file_id", "file_id"),
        Index("idx_file_shares_share_token", "share_token"),
        UniqueConstraint("share_token", name="uq_file_shares_token"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id"), nullable=False)

    # Share configuration
    share_type = Column(Enum(ShareType), default=ShareType.PUBLIC_LINK, nullable=False)
    share_token = Column(String(64), nullable=False, default=lambda: str(uuid4()))

    # Access control
    password_protected = Column(Boolean, default=False)
    password_hash = Column(String(255))  # Bcrypt hash if protected

    # Permissions
    can_download = Column(Boolean, default=True)
    can_view_only = Column(Boolean, default=False)

    # Expiration
    expires_at = Column(DateTime(timezone=True))
    max_downloads = Column(Integer)  # Limit number of downloads
    download_count = Column(Integer, default=0)

    # Sharing details
    shared_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    shared_with_users = Column(JSON, default=list)  # Array of user IDs
    shared_with_class = Column(UUID(as_uuid=True), ForeignKey("classes.id"))

    # Access tracking
    last_accessed_at = Column(DateTime(timezone=True))
    access_log = Column(JSON, default=list)  # Array of access events

    # Relationships
    file = relationship("File", back_populates="shares")

    def is_expired(self) -> bool:
        """Check if share link is expired"""
        if self.expires_at:
            return datetime.utcnow() >= self.expires_at
        return False

    def has_exceeded_downloads(self) -> bool:
        """Check if download limit exceeded"""
        if self.max_downloads:
            return self.download_count >= self.max_downloads
        return False


class StorageQuota(GlobalBaseModel, TimestampMixin):
    """
    Storage quota management per organization
    """

    __tablename__ = "storage_quotas"
    __table_args__ = (
        Index("idx_storage_quotas_organization", "organization_id"),
        UniqueConstraint("organization_id", name="uq_storage_quotas_org"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, unique=True
    )

    # Quota limits (in bytes)
    total_quota = Column(BigInteger, nullable=False, default=1073741824)  # 1GB default
    used_storage = Column(BigInteger, nullable=False, default=0)

    # File count limits
    max_files = Column(Integer, default=10000)
    file_count = Column(Integer, default=0)

    # Category-specific limits (in MB)
    max_file_size_mb = Column(Integer, default=100)
    max_video_size_mb = Column(Integer, default=500)
    max_image_size_mb = Column(Integer, default=50)
    max_document_size_mb = Column(Integer, default=100)

    # Usage tracking
    last_calculated_at = Column(DateTime(timezone=True), default=func.now())

    # Alerts
    warning_threshold_percent = Column(Integer, default=80)
    critical_threshold_percent = Column(Integer, default=95)
    last_warning_sent_at = Column(DateTime(timezone=True))

    @property
    def used_percentage(self) -> float:
        """Calculate storage usage percentage"""
        if self.total_quota == 0:
            return 0
        return (self.used_storage / self.total_quota) * 100

    @property
    def available_storage(self) -> int:
        """Calculate available storage in bytes"""
        return max(0, self.total_quota - self.used_storage)

    def has_storage_available(self, file_size: int) -> bool:
        """Check if there's enough storage for a file"""
        return self.available_storage >= file_size

    def is_warning_threshold_reached(self) -> bool:
        """Check if warning threshold reached"""
        return self.used_percentage >= self.warning_threshold_percent

    def is_critical_threshold_reached(self) -> bool:
        """Check if critical threshold reached"""
        return self.used_percentage >= self.critical_threshold_percent


class FileAccessLog(GlobalBaseModel):
    """
    Audit log for file access (FERPA compliance)
    """

    __tablename__ = "file_access_logs"
    __table_args__ = (
        Index("idx_file_access_logs_file", "file_id"),
        Index("idx_file_access_logs_user", "user_id"),
        Index("idx_file_access_logs_timestamp", "accessed_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)

    # Access details
    action = Column(String(50), nullable=False)  # view, download, share, delete
    accessed_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    ip_address = Column(String(45))  # IPv6 support
    user_agent = Column(Text)

    # Additional context
    access_granted = Column(Boolean, default=True)
    denial_reason = Column(String(255))
    access_metadata = Column(
        JSON, default=dict
    )  # Renamed from 'metadata' to avoid SQLAlchemy reserved word

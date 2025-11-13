"""Add file storage system with multi-tenancy

Revision ID: 005_add_file_storage
Revises: 004_add_multi_tenancy
Create Date: 2025-01-27

This migration adds comprehensive file storage system with:
- Multi-tenant file isolation
- Version tracking
- Sharing capabilities
- Storage quota management
- COPPA/FERPA compliance
- Audit logging
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "005_add_file_storage"
down_revision = "004_add_multi_tenancy"
branch_labels = None
depends_on = None


def upgrade():
    """Add file storage tables and update organization table"""

    # Create file status enum
    op.execute(
        """
        CREATE TYPE file_status AS ENUM (
            'pending', 'processing', 'available',
            'quarantined', 'deleted', 'archived', 'error'
        );
    """
    )

    # Create file category enum
    op.execute(
        """
        CREATE TYPE file_category AS ENUM (
            'educational_content', 'student_submission', 'assessment',
            'administrative', 'media_resource', 'temporary',
            'avatar', 'report'
        );
    """
    )

    # Create share type enum
    op.execute(
        """
        CREATE TYPE share_type AS ENUM (
            'public_link', 'organization', 'specific_users',
            'class', 'temporary'
        );
    """
    )

    # Create files table
    op.create_table(
        "files",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        # File metadata
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("mime_type", sa.String(127), nullable=False),
        sa.Column("file_extension", sa.String(20)),
        # Storage information
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("bucket_name", sa.String(255), nullable=False),
        sa.Column("cdn_url", sa.Text()),
        sa.Column("thumbnail_url", sa.Text()),
        # File properties
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "processing",
                "available",
                "quarantined",
                "deleted",
                "archived",
                "error",
                name="file_status",
            ),
            nullable=False,
        ),
        sa.Column(
            "category",
            postgresql.ENUM(
                "educational_content",
                "student_submission",
                "assessment",
                "administrative",
                "media_resource",
                "temporary",
                "avatar",
                "report",
                name="file_category",
            ),
            nullable=False,
        ),
        sa.Column("checksum", sa.String(64)),
        # Security and scanning
        sa.Column("virus_scanned", sa.Boolean(), default=False),
        sa.Column("virus_scan_result", postgresql.JSON()),
        sa.Column("last_scanned_at", sa.DateTime(timezone=True)),
        # Compliance fields
        sa.Column("contains_pii", sa.Boolean(), default=False),
        sa.Column("requires_consent", sa.Boolean(), default=False),
        sa.Column("retention_days", sa.Integer()),
        sa.Column("deletion_date", sa.DateTime(timezone=True)),
        # User relationship
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=False),
        # Metadata
        sa.Column("title", sa.String(255)),
        sa.Column("description", sa.Text()),
        sa.Column("tags", postgresql.JSON(), default=[]),
        sa.Column("metadata", postgresql.JSON(), default={}),
        # Access tracking
        sa.Column("download_count", sa.Integer(), default=0),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True)),
        # Audit fields
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("is_deleted", sa.Boolean(), default=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
        sa.CheckConstraint("file_size > 0", name="check_file_size_positive"),
    )

    # Create indexes for files table
    op.create_index("idx_files_organization_status", "files", ["organization_id", "status"])
    op.create_index("idx_files_category", "files", ["category"])
    op.create_index("idx_files_uploaded_by", "files", ["uploaded_by"])
    op.create_index("idx_files_created_at", "files", ["created_at"])

    # Create file_versions table
    op.create_table(
        "file_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Version information
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("checksum", sa.String(64)),
        # Change tracking
        sa.Column("changed_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("change_description", sa.Text()),
        # Timestamps
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"]),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"]),
    )

    # Create indexes for file_versions
    op.create_index("idx_file_versions_file_id", "file_versions", ["file_id"])
    op.create_index("idx_file_versions_created_at", "file_versions", ["created_at"])

    # Create file_shares table
    op.create_table(
        "file_shares",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Share configuration
        sa.Column(
            "share_type",
            postgresql.ENUM(
                "public_link",
                "organization",
                "specific_users",
                "class",
                "temporary",
                name="share_type",
            ),
            nullable=False,
        ),
        sa.Column("share_token", sa.String(64), nullable=False),
        # Access control
        sa.Column("password_protected", sa.Boolean(), default=False),
        sa.Column("password_hash", sa.String(255)),
        # Permissions
        sa.Column("can_download", sa.Boolean(), default=True),
        sa.Column("can_view_only", sa.Boolean(), default=False),
        # Expiration
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("max_downloads", sa.Integer()),
        sa.Column("download_count", sa.Integer(), default=0),
        # Sharing details
        sa.Column("shared_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("shared_with_users", postgresql.JSON(), default=[]),
        sa.Column("shared_with_class", postgresql.UUID(as_uuid=True)),
        # Access tracking
        sa.Column("last_accessed_at", sa.DateTime(timezone=True)),
        sa.Column("access_log", postgresql.JSON(), default=[]),
        # Timestamps
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"]),
        sa.ForeignKeyConstraint(["shared_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["shared_with_class"], ["classes.id"]),
        sa.UniqueConstraint("share_token", name="uq_file_shares_token"),
    )

    # Create indexes for file_shares
    op.create_index("idx_file_shares_file_id", "file_shares", ["file_id"])
    op.create_index("idx_file_shares_share_token", "file_shares", ["share_token"])

    # Create storage_quotas table
    op.create_table(
        "storage_quotas",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Quota limits (in bytes)
        sa.Column(
            "total_quota", sa.BigInteger(), nullable=False, default=1073741824
        ),  # 1GB default
        sa.Column("used_storage", sa.BigInteger(), nullable=False, default=0),
        # File count limits
        sa.Column("max_files", sa.Integer(), default=10000),
        sa.Column("file_count", sa.Integer(), default=0),
        # Category-specific limits (in MB)
        sa.Column("max_file_size_mb", sa.Integer(), default=100),
        sa.Column("max_video_size_mb", sa.Integer(), default=500),
        sa.Column("max_image_size_mb", sa.Integer(), default=50),
        sa.Column("max_document_size_mb", sa.Integer(), default=100),
        # Usage tracking
        sa.Column("last_calculated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        # Alerts
        sa.Column("warning_threshold_percent", sa.Integer(), default=80),
        sa.Column("critical_threshold_percent", sa.Integer(), default=95),
        sa.Column("last_warning_sent_at", sa.DateTime(timezone=True)),
        # Timestamps
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.UniqueConstraint("organization_id", name="uq_storage_quotas_org"),
    )

    # Create indexes for storage_quotas
    op.create_index("idx_storage_quotas_organization", "storage_quotas", ["organization_id"])

    # Create file_access_logs table for audit
    op.create_table(
        "file_access_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Access details
        sa.Column("action", sa.String(50), nullable=False),  # view, download, share, delete
        sa.Column(
            "accessed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("ip_address", sa.String(45)),  # IPv6 support
        sa.Column("user_agent", sa.Text()),
        # Additional context
        sa.Column("access_granted", sa.Boolean(), default=True),
        sa.Column("denial_reason", sa.String(255)),
        sa.Column("metadata", postgresql.JSON(), default={}),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
    )

    # Create indexes for file_access_logs
    op.create_index("idx_file_access_logs_file", "file_access_logs", ["file_id"])
    op.create_index("idx_file_access_logs_user", "file_access_logs", ["user_id"])
    op.create_index("idx_file_access_logs_timestamp", "file_access_logs", ["accessed_at"])

    # Add storage-related columns to organizations table
    op.add_column(
        "organizations",
        sa.Column("storage_quota_gb", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "organizations",
        sa.Column("enable_file_sharing", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.add_column(
        "organizations",
        sa.Column("enable_virus_scanning", sa.Boolean(), nullable=False, server_default="true"),
    )

    # Create storage quota for existing organizations
    op.execute(
        """
        INSERT INTO storage_quotas (id, organization_id, total_quota, created_at, updated_at)
        SELECT
            gen_random_uuid(),
            id,
            CASE
                WHEN subscription_tier = 'FREE' THEN 1073741824  -- 1GB
                WHEN subscription_tier = 'BASIC' THEN 5368709120  -- 5GB
                WHEN subscription_tier = 'PROFESSIONAL' THEN 21474836480  -- 20GB
                WHEN subscription_tier = 'ENTERPRISE' THEN 107374182400  -- 100GB
                WHEN subscription_tier = 'EDUCATION' THEN 53687091200  -- 50GB
                ELSE 1073741824  -- 1GB default
            END as total_quota,
            NOW(),
            NOW()
        FROM organizations
        WHERE NOT EXISTS (
            SELECT 1 FROM storage_quotas WHERE organization_id = organizations.id
        );
    """
    )


def downgrade():
    """Remove file storage system"""

    # Remove storage columns from organizations
    op.drop_column("organizations", "storage_quota_gb")
    op.drop_column("organizations", "enable_file_sharing")
    op.drop_column("organizations", "enable_virus_scanning")

    # Drop tables in reverse order of creation
    op.drop_table("file_access_logs")
    op.drop_table("storage_quotas")
    op.drop_table("file_shares")
    op.drop_table("file_versions")
    op.drop_table("files")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS file_status CASCADE")
    op.execute("DROP TYPE IF EXISTS file_category CASCADE")
    op.execute("DROP TYPE IF EXISTS share_type CASCADE")

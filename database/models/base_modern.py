"""
Modern Base Models for SQLAlchemy 2.0 (2025 Standards)

Provides base classes with Mapped type annotations for proper type safety
and modern async patterns. All models use SQLAlchemy 2.0+ syntax.

Reference: https://docs.sqlalchemy.org/en/20/
"""

import uuid
from datetime import datetime
from typing import Any, Optional, TypeVar
from uuid import UUID

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

# Type variable for generic base models
T = TypeVar("T")


class Base(DeclarativeBase):
    """
    Modern declarative base class for SQLAlchemy 2.0+

    All models inherit from this class to get proper type mapping
    and async support.
    """

    pass


class TimestampMixin:
    """
    Mixin for adding created_at and updated_at timestamps.

    Uses server-side defaults for reliability and consistency.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
    )


class SoftDeleteMixin:
    """
    Mixin for soft delete functionality.

    Allows records to be marked as deleted without physical removal,
    enabling audit trails and data recovery.
    """

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    deleted_by_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )

    @property
    def is_deleted(self) -> bool:
        """Check if the record is soft deleted."""
        return self.deleted_at is not None

    def soft_delete(self, deleted_by_id: Optional[UUID] = None) -> None:
        """
        Mark record as deleted.

        Args:
            deleted_by_id: UUID of the user performing the deletion
        """
        self.deleted_at = datetime.utcnow()
        if deleted_by_id:
            self.deleted_by_id = deleted_by_id

    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.deleted_at = None
        self.deleted_by_id = None


class AuditMixin:
    """
    Mixin for audit tracking - who created and updated records.

    Essential for compliance and change tracking in multi-user systems.
    """

    created_by_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    updated_by_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )


class TenantMixin:
    """
    Mixin for multi-tenant data isolation.

    Adds organization_id for Row-Level Security (RLS) support.
    All tenant-scoped data should use this mixin.
    """

    @declared_attr
    def organization_id(cls) -> Mapped[UUID]:
        """
        Foreign key to organization table for tenant isolation.

        Indexed for query performance with tenant filtering.
        """
        return mapped_column(
            PG_UUID(as_uuid=True),
            nullable=False,
            index=True,
        )

    @property
    def tenant_id(self) -> UUID:
        """Alias for organization_id to match common tenant patterns."""
        return self.organization_id


class BaseModel(Base, TimestampMixin):
    """
    Base model for all entities with timestamps.

    Provides UUID primary key and automatic timestamp tracking.
    Use this for simple models without soft delete or audit needs.
    """

    __abstract__ = True

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id='{self.id}')>"

    def to_dict(self) -> dict[str, Any]:
        """
        Convert model to dictionary representation.

        Returns:
            Dictionary with all column values
        """
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class FullBaseModel(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    """
    Full-featured base model with all mixins.

    Includes:
    - UUID primary key
    - Timestamps (created_at, updated_at)
    - Audit fields (created_by_id, updated_by_id)
    - Soft delete (deleted_at, deleted_by_id)

    Use this for models requiring complete audit trail and soft delete.
    """

    __abstract__ = True

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id='{self.id}', deleted={self.is_deleted})>"

    def to_dict(self, include_deleted: bool = False) -> dict[str, Any]:
        """
        Convert model to dictionary representation.

        Args:
            include_deleted: Include soft-deleted marker in output

        Returns:
            Dictionary with all column values
        """
        result = {column.name: getattr(self, column.name) for column in self.__table__.columns}

        if include_deleted:
            result["is_deleted"] = self.is_deleted

        return result


class TenantBaseModel(Base, TenantMixin, TimestampMixin, AuditMixin, SoftDeleteMixin):
    """
    Base model for tenant-scoped (multi-tenant) entities.

    Combines all necessary mixins for multi-tenant applications:
    - Tenant isolation (organization_id)
    - Timestamps
    - Audit tracking
    - Soft delete

    All tenant-scoped models should inherit from this.
    """

    __abstract__ = True

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__}("
            f"id='{self.id}', "
            f"tenant='{self.organization_id}', "
            f"deleted={self.is_deleted})>"
        )

    def to_dict(self, include_tenant: bool = True) -> dict[str, Any]:
        """
        Convert model to dictionary representation.

        Args:
            include_tenant: Include organization_id in output

        Returns:
            Dictionary with all column values
        """
        result = {column.name: getattr(self, column.name) for column in self.__table__.columns}

        result["is_deleted"] = self.is_deleted

        if include_tenant:
            result["tenant_id"] = self.tenant_id

        return result


class GlobalBaseModel(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    """
    Base model for global (non-tenant) entities.

    For models shared across all organizations or system-wide data
    (e.g., Organization model itself, system settings).

    Includes everything except tenant isolation.
    """

    __abstract__ = True

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id='{self.id}')>"

    def to_dict(self) -> dict[str, Any]:
        """
        Convert model to dictionary representation.

        Returns:
            Dictionary with all column values
        """
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


# Export all base classes and mixins
__all__ = [
    "Base",
    "BaseModel",
    "FullBaseModel",
    "TenantBaseModel",
    "GlobalBaseModel",
    "TimestampMixin",
    "SoftDeleteMixin",
    "AuditMixin",
    "TenantMixin",
]

"""
Base Models and Mixins for Multi-Tenant Database Architecture

Provides base classes and mixins for tenant-aware models with proper
isolation and audit capabilities.
"""

import uuid
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, declared_attr, relationship
from sqlalchemy.sql import func

# Create the declarative base
Base = declarative_base()


class TimestampMixin:
    """
    Mixin for adding created_at and updated_at timestamps to models.
    """

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class SoftDeleteMixin:
    """
    Mixin for adding soft delete functionality to models.
    """

    deleted_at = Column(DateTime(timezone=True))
    deleted_by_id = Column(UUID(as_uuid=True))

    @property
    def is_deleted(self) -> bool:
        """Check if the record is soft deleted"""
        return self.deleted_at is not None

    def soft_delete(self, deleted_by_id: Optional[UUID] = None) -> None:
        """Soft delete the record"""
        self.deleted_at = func.now()
        if deleted_by_id:
            self.deleted_by_id = deleted_by_id


class AuditMixin:
    """
    Mixin for adding audit fields to track who created/updated records.
    """

    created_by_id = Column(UUID(as_uuid=True))
    updated_by_id = Column(UUID(as_uuid=True))


class TenantMixin:
    """
    Mixin for adding tenant isolation to models.

    This mixin adds the organization_id field and relationships needed
    for multi-tenant data isolation using Row Level Security (RLS).
    """

    @declared_attr
    def organization_id(cls):
        """
        Foreign key to the organization table for tenant isolation.
        This field is required for all tenant-scoped models.
        """
        return Column(
            UUID(as_uuid=True),
            ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
            index=True,  # Index for query performance
        )

    @declared_attr
    def organization(cls):
        """
        Relationship to the organization for easy access.
        Note: This assumes the Organization model is available.
        """
        return relationship("Organization", back_populates=f"{cls.__tablename__}")


class TenantBaseModel(Base, TenantMixin, TimestampMixin, AuditMixin, SoftDeleteMixin):
    """
    Base model class for all tenant-scoped models.

    Combines all the mixins needed for a proper multi-tenant model:
    - Tenant isolation via organization_id
    - Audit fields for tracking changes
    - Timestamps for record lifecycle
    - Soft delete for data retention
    """

    __abstract__ = True

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__}(id='{self.id}', organization_id='{self.organization_id}')>"
        )

    @property
    def tenant_id(self) -> UUID:
        """Alias for organization_id to match common tenant patterns"""
        return self.organization_id


class GlobalBaseModel(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    """
    Base model class for global (non-tenant) models.

    For models that are shared across all organizations or are
    organization-independent (like the Organization model itself).
    """

    __abstract__ = True

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id='{self.id}')>"


class TenantAwareQuery:
    """
    Query helper methods for tenant-aware operations.

    This class provides static methods to help with tenant-scoped queries
    and can be mixed into repository classes.
    """

    @staticmethod
    def filter_by_tenant(query, organization_id: UUID):
        """
        Filter a query to only include records for the specified tenant.

        Args:
            query: SQLAlchemy query object
            organization_id: UUID of the organization (tenant)

        Returns:
            Filtered query object
        """
        return query.filter_by(organization_id=organization_id)

    @staticmethod
    def exclude_deleted(query):
        """
        Filter a query to exclude soft-deleted records.

        Args:
            query: SQLAlchemy query object

        Returns:
            Filtered query object
        """
        return query.filter_by(deleted_at=None)

    @staticmethod
    def tenant_scoped_query(query, organization_id: UUID, include_deleted: bool = False):
        """
        Apply both tenant filtering and soft delete filtering.

        Args:
            query: SQLAlchemy query object
            organization_id: UUID of the organization (tenant)
            include_deleted: Whether to include soft-deleted records

        Returns:
            Filtered query object
        """
        query = TenantAwareQuery.filter_by_tenant(query, organization_id)

        if not include_deleted:
            query = TenantAwareQuery.exclude_deleted(query)

        return query


class TenantContext:
    """
    Context manager for tenant-aware operations.

    This class can be used to set the current tenant context
    for database operations, particularly useful for RLS policies.
    """

    def __init__(self, organization_id: UUID):
        self.organization_id = organization_id
        self._previous_context = None

    def __enter__(self):
        # Store current context if any
        self._previous_context = getattr(TenantContext, "_current_tenant", None)
        # Set new context
        TenantContext._current_tenant = self.organization_id
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore previous context
        if self._previous_context:
            TenantContext._current_tenant = self._previous_context
        else:
            TenantContext._current_tenant = None

    @classmethod
    def get_current_tenant(cls) -> Optional[UUID]:
        """Get the current tenant ID from context"""
        return getattr(cls, "_current_tenant", None)

    @classmethod
    def set_current_tenant(cls, organization_id: UUID) -> None:
        """Set the current tenant ID in context"""
        cls._current_tenant = organization_id

    @classmethod
    def clear_current_tenant(cls) -> None:
        """Clear the current tenant context"""
        cls._current_tenant = None


# Re-export for convenience
__all__ = [
    "Base",
    "TimestampMixin",
    "SoftDeleteMixin",
    "AuditMixin",
    "TenantMixin",
    "TenantBaseModel",
    "GlobalBaseModel",
    "TenantAwareQuery",
    "TenantContext",
]

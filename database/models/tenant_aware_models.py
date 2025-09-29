"""
Tenant-Aware Database Models Update

This module provides updated imports and relationships for multi-tenant
database models. It should be used instead of models.py after the
multi-tenancy migration is applied.
"""

# Import all existing enums and non-model classes
from database.models.models import (
    UserRole, ContentStatus, DifficultyLevel, AchievementType,
    RobloxSessionStatus, RobloxContentType
)

# Import the tenant-aware base classes
from database.models.base import (
    Base, TenantBaseModel, GlobalBaseModel, TenantMixin,
    TimestampMixin, SoftDeleteMixin, AuditMixin, TenantContext
)

# Import the organization models
from database.models.tenant import (
    Organization, OrganizationInvitation, OrganizationUsageLog,
    OrganizationStatus, SubscriptionTier
)

# Re-export Base for compatibility
__all__ = [
    'Base',
    'TenantBaseModel',
    'GlobalBaseModel',
    'Organization',
    'OrganizationInvitation',
    'OrganizationUsageLog',
    'TenantContext',
    'UserRole',
    'ContentStatus',
    'DifficultyLevel',
    'AchievementType',
    'RobloxSessionStatus',
    'RobloxContentType',
    'OrganizationStatus',
    'SubscriptionTier'
]

# Note: After migration, the existing models in models.py will automatically
# become tenant-aware through the organization_id column and RLS policies.
# No changes to the model definitions are required immediately, but new models
# should inherit from TenantBaseModel for proper tenant isolation.

# Example of how to create new tenant-aware models:
"""
from database.models.tenant_aware_models import TenantBaseModel

class NewTenantModel(TenantBaseModel):
    __tablename__ = "new_tenant_table"

    name = Column(String(100), nullable=False)
    description = Column(Text)

    # organization_id, id, timestamps, audit fields, soft delete
    # are automatically inherited from TenantBaseModel
"""

# For existing models, they will work with multi-tenancy through:
# 1. The organization_id column added by migration
# 2. RLS policies that filter by organization_id
# 3. Application-level tenant context setting

# Eventually, you may want to update existing models to inherit from
# TenantBaseModel for consistency, but it's not required for functionality.
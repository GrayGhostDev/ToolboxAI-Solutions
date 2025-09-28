"""
Tenant-Aware Repository Classes

Provides repository pattern implementations for multi-tenant operations
with proper tenant isolation and context management.
"""

from typing import Optional, List, Dict, Any, Type, TypeVar, Generic
from uuid import UUID
from datetime import datetime, timedelta
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.exc import IntegrityError, NoResultFound

from database.models.base import TenantBaseModel, TenantContext, TenantAwareQuery
from database.models.tenant import Organization, OrganizationInvitation, OrganizationUsageLog
from database.models.models import User  # Import existing User model


logger = logging.getLogger(__name__)

# Type variable for generic repository
T = TypeVar('T', bound=TenantBaseModel)


class TenantRepository(Generic[T]):
    """
    Generic repository for tenant-aware database operations.

    Provides CRUD operations with automatic tenant isolation and context management.
    """

    def __init__(self, session: AsyncSession, model_class: Type[T], organization_id: UUID):
        self.session = session
        self.model_class = model_class
        self.organization_id = organization_id

    async def get_by_id(self, id: UUID, include_deleted: bool = False) -> Optional[T]:
        """Get a record by ID with tenant isolation"""
        query = select(self.model_class).where(
            and_(
                self.model_class.id == id,
                self.model_class.organization_id == self.organization_id
            )
        )

        if not include_deleted:
            query = query.where(self.model_class.deleted_at.is_(None))

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        include_deleted: bool = False,
        order_by: Optional[str] = None
    ) -> List[T]:
        """Get all records for the current tenant"""
        query = select(self.model_class).where(
            self.model_class.organization_id == self.organization_id
        )

        if not include_deleted:
            query = query.where(self.model_class.deleted_at.is_(None))

        if order_by:
            if hasattr(self.model_class, order_by):
                query = query.order_by(getattr(self.model_class, order_by))

        if offset:
            query = query.offset(offset)

        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def create(self, **kwargs) -> T:
        """Create a new record with tenant isolation"""
        # Ensure organization_id is set
        kwargs['organization_id'] = self.organization_id

        # Set audit fields if available
        kwargs.setdefault('created_at', func.now())

        instance = self.model_class(**kwargs)
        self.session.add(instance)

        try:
            await self.session.flush()
            return instance
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Failed to create {self.model_class.__name__}: {e}")
            raise

    async def update(self, id: UUID, **kwargs) -> Optional[T]:
        """Update a record with tenant isolation"""
        # Get the existing record
        instance = await self.get_by_id(id)
        if not instance:
            return None

        # Update fields
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        # Set audit fields
        instance.updated_at = func.now()

        try:
            await self.session.flush()
            return instance
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Failed to update {self.model_class.__name__} {id}: {e}")
            raise

    async def soft_delete(self, id: UUID, deleted_by_id: Optional[UUID] = None) -> bool:
        """Soft delete a record with tenant isolation"""
        instance = await self.get_by_id(id)
        if not instance:
            return False

        instance.deleted_at = func.now()
        if deleted_by_id:
            instance.deleted_by_id = deleted_by_id

        try:
            await self.session.flush()
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to soft delete {self.model_class.__name__} {id}: {e}")
            raise

    async def hard_delete(self, id: UUID) -> bool:
        """Hard delete a record with tenant isolation"""
        query = delete(self.model_class).where(
            and_(
                self.model_class.id == id,
                self.model_class.organization_id == self.organization_id
            )
        )

        try:
            result = await self.session.execute(query)
            return result.rowcount > 0
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to hard delete {self.model_class.__name__} {id}: {e}")
            raise

    async def count(self, include_deleted: bool = False, **filters) -> int:
        """Count records for the current tenant"""
        query = select(func.count(self.model_class.id)).where(
            self.model_class.organization_id == self.organization_id
        )

        if not include_deleted:
            query = query.where(self.model_class.deleted_at.is_(None))

        # Apply additional filters
        for key, value in filters.items():
            if hasattr(self.model_class, key):
                query = query.where(getattr(self.model_class, key) == value)

        result = await self.session.execute(query)
        return result.scalar()

    async def exists(self, **filters) -> bool:
        """Check if a record exists for the current tenant"""
        query = select(self.model_class.id).where(
            self.model_class.organization_id == self.organization_id
        )

        for key, value in filters.items():
            if hasattr(self.model_class, key):
                query = query.where(getattr(self.model_class, key) == value)

        query = query.limit(1)
        result = await self.session.execute(query)
        return result.scalar() is not None


class OrganizationRepository:
    """Repository for organization management operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> Optional[Organization]:
        """Get organization by ID"""
        query = select(Organization).where(Organization.id == id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Organization]:
        """Get organization by slug"""
        query = select(Organization).where(Organization.slug == slug)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> Organization:
        """Create a new organization"""
        # Generate API key if not provided
        if 'api_key' not in kwargs:
            import secrets
            kwargs['api_key'] = f"org_{secrets.token_urlsafe(32)}"

        # Set trial period if not provided
        if 'trial_started_at' not in kwargs:
            kwargs['trial_started_at'] = func.now()
            kwargs['trial_expires_at'] = func.now() + timedelta(days=30)

        org = Organization(**kwargs)
        self.session.add(org)

        try:
            await self.session.flush()
            return org
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Failed to create organization: {e}")
            raise

    async def update_usage(self, org_id: UUID, metric: str, amount: int = 1) -> bool:
        """Update usage metrics for an organization"""
        org = await self.get_by_id(org_id)
        if not org:
            return False

        org.increment_usage(metric, amount)

        try:
            await self.session.flush()
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update usage for org {org_id}: {e}")
            raise

    async def check_limits(self, org_id: UUID, metric: str, additional: int = 1) -> bool:
        """Check if organization can use additional resources"""
        org = await self.get_by_id(org_id)
        if not org:
            return False

        if metric == 'users':
            return org.can_add_user()
        elif metric == 'classes':
            return org.can_add_class()
        elif metric == 'storage':
            return org.can_use_storage(additional)
        else:
            return True

    async def get_usage_stats(self, org_id: UUID) -> Dict[str, Any]:
        """Get usage statistics for an organization"""
        org = await self.get_by_id(org_id)
        if not org:
            return {}

        return {
            'current_usage': {
                'users': org.current_users,
                'classes': org.current_classes,
                'storage_gb': org.current_storage_gb,
                'api_calls': org.current_api_calls_this_month,
                'roblox_sessions': org.current_roblox_sessions
            },
            'limits': {
                'users': org.max_users,
                'classes': org.max_classes,
                'storage_gb': org.max_storage_gb,
                'api_calls': org.max_api_calls_per_month,
                'roblox_sessions': org.max_roblox_sessions
            },
            'usage_percentage': org.usage_percentage,
            'subscription_tier': org.subscription_tier.value,
            'status': org.status.value
        }

    async def log_usage(self, org_id: UUID, log_type: str = "daily") -> OrganizationUsageLog:
        """Create a usage log entry for an organization"""
        org = await self.get_by_id(org_id)
        if not org:
            raise ValueError(f"Organization {org_id} not found")

        # Count active users for this period
        active_users_query = select(func.count(User.id)).where(
            and_(
                User.organization_id == org_id,
                User.is_active == True,
                User.last_login > func.now() - timedelta(days=1)
            )
        )
        active_users_result = await self.session.execute(active_users_query)
        active_users_count = active_users_result.scalar() or 0

        usage_log = OrganizationUsageLog(
            organization_id=org_id,
            users_count=org.current_users,
            classes_count=org.current_classes,
            storage_gb=org.current_storage_gb,
            api_calls_count=org.current_api_calls_this_month,
            roblox_sessions_count=org.current_roblox_sessions,
            active_users_count=active_users_count,
            log_type=log_type,
            usage_data={
                'subscription_tier': org.subscription_tier.value,
                'status': org.status.value,
                'limits': {
                    'users': org.max_users,
                    'classes': org.max_classes,
                    'storage_gb': org.max_storage_gb,
                    'api_calls': org.max_api_calls_per_month,
                    'roblox_sessions': org.max_roblox_sessions
                }
            }
        )

        self.session.add(usage_log)

        try:
            await self.session.flush()
            return usage_log
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to log usage for org {org_id}: {e}")
            raise


class TenantContextManager:
    """Context manager for tenant-aware database operations"""

    def __init__(self, session: AsyncSession, organization_id: UUID):
        self.session = session
        self.organization_id = organization_id

    async def __aenter__(self):
        # Set tenant context in PostgreSQL session
        await self.session.execute(
            select(func.set_config('app.current_organization_id', str(self.organization_id), True))
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Clear tenant context
        await self.session.execute(
            select(func.set_config('app.current_organization_id', '', True))
        )

    def get_repository(self, model_class: Type[T]) -> TenantRepository[T]:
        """Get a tenant-aware repository for the specified model"""
        return TenantRepository(self.session, model_class, self.organization_id)

    def get_organization_repository(self) -> OrganizationRepository:
        """Get an organization repository"""
        return OrganizationRepository(self.session)


# Convenience function for creating tenant context
async def with_tenant_context(session: AsyncSession, organization_id: UUID) -> TenantContextManager:
    """Create a tenant context manager for database operations"""
    return TenantContextManager(session, organization_id)


# Repository factory for common models
class RepositoryFactory:
    """Factory for creating tenant-aware repositories"""

    def __init__(self, session: AsyncSession, organization_id: UUID):
        self.session = session
        self.organization_id = organization_id

    def user_repository(self) -> TenantRepository:
        """Get user repository with tenant isolation"""
        return TenantRepository(self.session, User, self.organization_id)

    def organization_repository(self) -> OrganizationRepository:
        """Get organization repository"""
        return OrganizationRepository(self.session)

    # Add more repository methods as needed for other models
    # def course_repository(self) -> TenantRepository:
    #     return TenantRepository(self.session, Course, self.organization_id)

    # def class_repository(self) -> TenantRepository:
    #     return TenantRepository(self.session, Class, self.organization_id)
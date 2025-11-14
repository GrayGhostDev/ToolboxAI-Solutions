"""
Tenant Management Service Layer

Provides high-level business logic for multi-tenant operations including
organization management, user provisioning, and subscription handling.
"""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.models import User, UserRole
from database.models.tenant import (
    Organization,
    OrganizationInvitation,
    OrganizationStatus,
    OrganizationUsageLog,
    SubscriptionTier,
)
from database.repositories.tenant_repository import (
    OrganizationRepository,
    TenantContextManager,
)

logger = logging.getLogger(__name__)


class TenantService:
    """Service layer for tenant management operations"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.org_repo = OrganizationRepository(session)

    async def create_organization(
        self,
        name: str,
        admin_email: str,
        admin_password: str,
        admin_first_name: str = "",
        admin_last_name: str = "",
        organization_type: str = "education",
        subscription_tier: SubscriptionTier = SubscriptionTier.FREE,
    ) -> tuple[Organization, User]:
        """
        Create a new organization with an admin user.

        Args:
            name: Organization name
            admin_email: Admin user email
            admin_password: Admin user password (will be hashed)
            admin_first_name: Admin first name
            admin_last_name: Admin last name
            organization_type: Type of organization
            subscription_tier: Initial subscription tier

        Returns:
            Tuple of (Organization, Admin User)
        """
        try:
            # Generate unique slug
            slug = await self._generate_organization_slug(name)

            # Create organization
            org = await self.org_repo.create(
                name=name,
                slug=slug,
                organization_type=organization_type,
                subscription_tier=subscription_tier,
                status=OrganizationStatus.TRIAL,
                email=admin_email,
                trial_started_at=func.now(),
                trial_expires_at=func.now() + timedelta(days=30),
            )

            # Create admin user within the organization context
            async with TenantContextManager(self.session, org.id) as ctx:
                user_repo = ctx.get_repository(User)

                # Hash password (in real implementation, use proper password hashing)
                password_hash = hashlib.sha256(admin_password.encode()).hexdigest()

                admin_user = await user_repo.create(
                    email=admin_email,
                    username=admin_email,  # Use email as username initially
                    password_hash=password_hash,
                    role=UserRole.ADMIN,
                    first_name=admin_first_name,
                    last_name=admin_last_name,
                    display_name=f"{admin_first_name} {admin_last_name}".strip(),
                    is_active=True,
                    is_verified=True,
                )

            # Update organization usage
            await self.org_repo.update_usage(org.id, "users", 1)

            await self.session.commit()

            logger.info(f"Created organization '{name}' with admin user '{admin_email}'")
            return org, admin_user

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create organization: {e}")
            raise

    async def invite_user(
        self,
        organization_id: UUID,
        email: str,
        role: UserRole,
        invited_by_id: UUID,
        invitation_message: Optional[str] = None,
        expires_in_days: int = 7,
    ) -> OrganizationInvitation:
        """
        Invite a user to join an organization.

        Args:
            organization_id: Organization to invite user to
            email: Email address to invite
            role: Role for the invited user
            invited_by_id: ID of user sending invitation
            invitation_message: Optional message to include
            expires_in_days: Days until invitation expires

        Returns:
            OrganizationInvitation instance
        """
        # Check if organization has capacity for new users
        if not await self.org_repo.check_limits(organization_id, "users"):
            raise ValueError("Organization has reached maximum user limit")

        # Generate secure invitation token
        invitation_token = secrets.token_urlsafe(32)

        invitation = OrganizationInvitation(
            organization_id=organization_id,
            email=email,
            role=role.value,
            invited_by_id=invited_by_id,
            invitation_token=invitation_token,
            expires_at=func.now() + timedelta(days=expires_in_days),
            invitation_message=invitation_message,
        )

        self.session.add(invitation)

        try:
            await self.session.flush()
            logger.info(f"Created invitation for {email} to organization {organization_id}")
            return invitation
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Failed to create invitation: {e}")
            raise

    async def accept_invitation(
        self,
        invitation_token: str,
        user_id: UUID,
        password: str,
        first_name: str = "",
        last_name: str = "",
    ) -> tuple[User, Organization]:
        """
        Accept an organization invitation and create user account.

        Args:
            invitation_token: Invitation token
            user_id: ID for the new user (or existing user)
            password: User password
            first_name: User first name
            last_name: User last name

        Returns:
            Tuple of (User, Organization)
        """
        # Find invitation
        query = select(OrganizationInvitation).where(
            OrganizationInvitation.invitation_token == invitation_token
        )
        result = await self.session.execute(query)
        invitation = result.scalar_one_or_none()

        if not invitation:
            raise ValueError("Invalid invitation token")

        if not invitation.is_valid:
            raise ValueError("Invitation has expired or is no longer valid")

        # Get organization
        org = await self.org_repo.get_by_id(invitation.organization_id)
        if not org:
            raise ValueError("Organization not found")

        # Check if organization can accept new users
        if not await self.org_repo.check_limits(org.id, "users"):
            raise ValueError("Organization has reached maximum user limit")

        try:
            # Create user within organization context
            async with TenantContextManager(self.session, org.id) as ctx:
                user_repo = ctx.get_repository(User)

                # Check if user already exists with this email
                existing_users = await user_repo.get_all()
                existing_user = next(
                    (u for u in existing_users if u.email == invitation.email), None
                )

                if existing_user:
                    # User already exists, just update role if needed
                    user = await user_repo.update(
                        existing_user.id, role=UserRole(invitation.role), is_active=True
                    )
                else:
                    # Create new user
                    password_hash = hashlib.sha256(password.encode()).hexdigest()

                    user = await user_repo.create(
                        email=invitation.email,
                        username=invitation.email,
                        password_hash=password_hash,
                        role=UserRole(invitation.role),
                        first_name=first_name,
                        last_name=last_name,
                        display_name=f"{first_name} {last_name}".strip(),
                        is_active=True,
                        is_verified=True,
                    )

                    # Update organization usage
                    await self.org_repo.update_usage(org.id, "users", 1)

            # Mark invitation as accepted
            invitation.accepted_at = func.now()
            invitation.accepted_by_id = user.id

            await self.session.commit()

            logger.info(f"User {invitation.email} accepted invitation to organization {org.name}")
            return user, org

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to accept invitation: {e}")
            raise

    async def upgrade_subscription(
        self,
        organization_id: UUID,
        new_tier: SubscriptionTier,
        updated_by_id: Optional[UUID] = None,
    ) -> Organization:
        """
        Upgrade organization subscription tier.

        Args:
            organization_id: Organization to upgrade
            new_tier: New subscription tier
            updated_by_id: ID of user making the change

        Returns:
            Updated Organization
        """
        org = await self.org_repo.get_by_id(organization_id)
        if not org:
            raise ValueError("Organization not found")

        # Define tier limits
        tier_limits = {
            SubscriptionTier.FREE: {
                "max_users": 5,
                "max_classes": 2,
                "max_storage_gb": 0.5,
                "max_api_calls_per_month": 500,
                "max_roblox_sessions": 2,
            },
            SubscriptionTier.BASIC: {
                "max_users": 25,
                "max_classes": 10,
                "max_storage_gb": 5.0,
                "max_api_calls_per_month": 5000,
                "max_roblox_sessions": 10,
            },
            SubscriptionTier.PROFESSIONAL: {
                "max_users": 100,
                "max_classes": 50,
                "max_storage_gb": 25.0,
                "max_api_calls_per_month": 25000,
                "max_roblox_sessions": 25,
            },
            SubscriptionTier.ENTERPRISE: {
                "max_users": 1000,
                "max_classes": 500,
                "max_storage_gb": 100.0,
                "max_api_calls_per_month": 100000,
                "max_roblox_sessions": 100,
            },
            SubscriptionTier.EDUCATION: {
                "max_users": 500,
                "max_classes": 100,
                "max_storage_gb": 50.0,
                "max_api_calls_per_month": 50000,
                "max_roblox_sessions": 50,
            },
        }

        limits = tier_limits.get(new_tier, tier_limits[SubscriptionTier.FREE])

        # Update organization
        for key, value in limits.items():
            setattr(org, key, value)

        org.subscription_tier = new_tier
        org.status = OrganizationStatus.ACTIVE
        org.subscription_started_at = func.now()
        org.subscription_expires_at = func.now() + timedelta(days=365)  # 1 year
        org.updated_by_id = updated_by_id

        try:
            await self.session.flush()
            logger.info(f"Upgraded organization {organization_id} to {new_tier.value}")
            return org
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to upgrade subscription: {e}")
            raise

    async def check_usage_limits(self, organization_id: UUID) -> dict[str, Any]:
        """
        Check current usage against limits for an organization.

        Args:
            organization_id: Organization to check

        Returns:
            Dictionary with usage status and warnings
        """
        org = await self.org_repo.get_by_id(organization_id)
        if not org:
            raise ValueError("Organization not found")

        usage_percentage = org.usage_percentage
        warnings = []
        limits_exceeded = []

        # Check for warnings (>80% usage)
        for metric, percentage in usage_percentage.items():
            if percentage > 80:
                warnings.append(f"{metric}: {percentage:.1f}% used")
            if percentage >= 100:
                limits_exceeded.append(metric)

        return {
            "organization_id": organization_id,
            "usage_percentage": usage_percentage,
            "warnings": warnings,
            "limits_exceeded": limits_exceeded,
            "subscription_tier": org.subscription_tier.value,
            "subscription_active": org.is_subscription_active,
            "trial_days_remaining": org.trial_days_remaining,
        }

    async def generate_usage_report(
        self,
        organization_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """
        Generate usage report for an organization.

        Args:
            organization_id: Organization to report on
            start_date: Start date for report (defaults to 30 days ago)
            end_date: End date for report (defaults to now)

        Returns:
            Dictionary with usage report data
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        # Get usage logs for the period
        query = (
            select(OrganizationUsageLog)
            .where(
                and_(
                    OrganizationUsageLog.organization_id == organization_id,
                    OrganizationUsageLog.log_date >= start_date,
                    OrganizationUsageLog.log_date <= end_date,
                )
            )
            .order_by(OrganizationUsageLog.log_date)
        )

        result = await self.session.execute(query)
        usage_logs = result.scalars().all()

        # Get current organization data
        org = await self.org_repo.get_by_id(organization_id)
        current_stats = await self.org_repo.get_usage_stats(organization_id)

        return {
            "organization_id": organization_id,
            "organization_name": org.name if org else "Unknown",
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "current_stats": current_stats,
            "historical_data": [
                {
                    "date": log.log_date.isoformat(),
                    "users_count": log.users_count,
                    "classes_count": log.classes_count,
                    "storage_gb": log.storage_gb,
                    "api_calls_count": log.api_calls_count,
                    "roblox_sessions_count": log.roblox_sessions_count,
                    "active_users_count": log.active_users_count,
                }
                for log in usage_logs
            ],
            "summary": {
                "total_logs": len(usage_logs),
                "peak_users": max((log.users_count for log in usage_logs), default=0),
                "peak_storage": max((log.storage_gb for log in usage_logs), default=0),
                "total_api_calls": sum(log.api_calls_count for log in usage_logs),
            },
        }

    async def _generate_organization_slug(self, name: str) -> str:
        """Generate a unique slug for an organization"""
        base_slug = name.lower().replace(" ", "-").replace("_", "-")
        base_slug = "".join(c for c in base_slug if c.isalnum() or c == "-")

        # Try the base slug first
        if not await self._slug_exists(base_slug):
            return base_slug

        # Add numbers until we find a unique slug
        counter = 1
        while True:
            test_slug = f"{base_slug}-{counter}"
            if not await self._slug_exists(test_slug):
                return test_slug
            counter += 1

    async def _slug_exists(self, slug: str) -> bool:
        """Check if a slug already exists"""
        org = await self.org_repo.get_by_slug(slug)
        return org is not None


class TenantContextService:
    """Service for managing tenant context in application operations"""

    @staticmethod
    async def set_tenant_context(session: AsyncSession, organization_id: UUID):
        """Set the tenant context for the current database session"""
        await session.execute(
            select(func.set_config("app.current_organization_id", str(organization_id), True))
        )

    @staticmethod
    async def clear_tenant_context(session: AsyncSession):
        """Clear the tenant context for the current database session"""
        await session.execute(select(func.set_config("app.current_organization_id", "", True)))

    @staticmethod
    async def get_current_tenant(session: AsyncSession) -> Optional[UUID]:
        """Get the current tenant from the database session"""
        result = await session.execute(
            select(func.current_setting("app.current_organization_id", True))
        )
        tenant_id_str = result.scalar()

        if tenant_id_str:
            try:
                return UUID(tenant_id_str)
            except ValueError:
                return None
        return None

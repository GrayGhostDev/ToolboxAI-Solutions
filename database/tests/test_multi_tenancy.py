"""
Multi-Tenancy Tests

Test suite for multi-tenant database functionality including
tenant isolation, RLS policies, and organization management.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Generator
from uuid import uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from database.config.multi_tenant_config import TenantConfig
from database.models.base import Base
from database.models.models import User, UserRole
from database.models.tenant import (
    Organization,
    OrganizationStatus,
    SubscriptionTier,
)
from database.repositories.tenant_repository import TenantContextManager
from database.services.tenant_service import TenantService

# Test configuration
TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test_pass@localhost/test_db"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine():
    """Create test database engine"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session(engine) -> AsyncSession:
    """Create test database session"""
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        yield session

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def tenant_service(session: AsyncSession) -> TenantService:
    """Create tenant service instance"""
    return TenantService(session)


@pytest.fixture
async def sample_organization(tenant_service: TenantService) -> Organization:
    """Create a sample organization for testing"""
    org, admin_user = await tenant_service.create_organization(
        name="Test Organization",
        admin_email="admin@test.com",
        admin_password="test_password_123",
        admin_first_name="Test",
        admin_last_name="Admin",
    )
    return org


@pytest.fixture
async def second_organization(tenant_service: TenantService) -> Organization:
    """Create a second organization for isolation testing"""
    org, admin_user = await tenant_service.create_organization(
        name="Second Test Organization",
        admin_email="admin2@test.com",
        admin_password="test_password_123",
        admin_first_name="Second",
        admin_last_name="Admin",
    )
    return org


class TestOrganizationManagement:
    """Test organization CRUD operations"""

    async def test_create_organization(self, tenant_service: TenantService):
        """Test creating a new organization"""
        org, admin_user = await tenant_service.create_organization(
            name="New Test Org",
            admin_email="admin@newtest.com",
            admin_password="secure_password_123",
            admin_first_name="New",
            admin_last_name="Admin",
            organization_type="education",
            subscription_tier=SubscriptionTier.BASIC,
        )

        assert org.name == "New Test Org"
        assert org.slug == "new-test-org"
        assert org.subscription_tier == SubscriptionTier.BASIC
        assert org.status == OrganizationStatus.TRIAL
        assert org.current_users == 1

        assert admin_user.email == "admin@newtest.com"
        assert admin_user.role == UserRole.ADMIN
        assert admin_user.organization_id == org.id

    async def test_organization_slug_generation(self, tenant_service: TenantService):
        """Test unique slug generation"""
        # Create first organization
        org1, _ = await tenant_service.create_organization(
            name="Test Company", admin_email="admin1@testcompany.com", admin_password="password123"
        )

        # Create second organization with same name
        org2, _ = await tenant_service.create_organization(
            name="Test Company", admin_email="admin2@testcompany.com", admin_password="password123"
        )

        assert org1.slug == "test-company"
        assert org2.slug == "test-company-1"

    async def test_organization_limits(self, sample_organization: Organization):
        """Test organization subscription limits"""
        org = sample_organization

        # Check default free tier limits
        if org.subscription_tier == SubscriptionTier.FREE:
            limits = TenantConfig.get_subscription_limits(SubscriptionTier.FREE)
            assert org.max_users == limits["max_users"]
            assert org.max_classes == limits["max_classes"]
            assert org.max_storage_gb == limits["max_storage_gb"]

    async def test_upgrade_subscription(
        self, tenant_service: TenantService, sample_organization: Organization
    ):
        """Test subscription upgrade"""
        org_id = sample_organization.id
        original_max_users = sample_organization.max_users

        # Upgrade to professional
        upgraded_org = await tenant_service.upgrade_subscription(
            organization_id=org_id, new_tier=SubscriptionTier.PROFESSIONAL
        )

        assert upgraded_org.subscription_tier == SubscriptionTier.PROFESSIONAL
        assert upgraded_org.status == OrganizationStatus.ACTIVE
        assert upgraded_org.max_users > original_max_users

    async def test_usage_tracking(
        self, tenant_service: TenantService, sample_organization: Organization
    ):
        """Test usage tracking and limits"""
        org_id = sample_organization.id

        # Test adding users
        await tenant_service.org_repo.update_usage(org_id, "users", 2)
        updated_org = await tenant_service.org_repo.get_by_id(org_id)
        assert updated_org.current_users == 3  # Initial 1 + 2 added

        # Test usage statistics
        stats = await tenant_service.org_repo.get_usage_stats(org_id)
        assert "current_usage" in stats
        assert "limits" in stats
        assert "usage_percentage" in stats


class TestUserInvitations:
    """Test user invitation system"""

    async def test_invite_user(
        self,
        tenant_service: TenantService,
        sample_organization: Organization,
        session: AsyncSession,
    ):
        """Test inviting a user to organization"""
        # Get admin user
        async with TenantContextManager(session, sample_organization.id) as ctx:
            user_repo = ctx.get_repository(User)
            admin_users = await user_repo.get_all()
            admin_user = next(u for u in admin_users if u.role == UserRole.ADMIN)

        invitation = await tenant_service.invite_user(
            organization_id=sample_organization.id,
            email="teacher@test.com",
            role=UserRole.TEACHER,
            invited_by_id=admin_user.id,
            invitation_message="Welcome to our organization!",
        )

        assert invitation.email == "teacher@test.com"
        assert invitation.role == UserRole.TEACHER.value
        assert invitation.organization_id == sample_organization.id
        assert invitation.is_valid
        assert not invitation.is_expired

    async def test_accept_invitation(
        self,
        tenant_service: TenantService,
        sample_organization: Organization,
        session: AsyncSession,
    ):
        """Test accepting an invitation"""
        # Create invitation
        async with TenantContextManager(session, sample_organization.id) as ctx:
            user_repo = ctx.get_repository(User)
            admin_users = await user_repo.get_all()
            admin_user = next(u for u in admin_users if u.role == UserRole.ADMIN)

        invitation = await tenant_service.invite_user(
            organization_id=sample_organization.id,
            email="student@test.com",
            role=UserRole.STUDENT,
            invited_by_id=admin_user.id,
        )

        # Accept invitation
        new_user, org = await tenant_service.accept_invitation(
            invitation_token=invitation.invitation_token,
            user_id=uuid4(),
            password="student_password",
            first_name="Test",
            last_name="Student",
        )

        assert new_user.email == "student@test.com"
        assert new_user.role == UserRole.STUDENT
        assert new_user.organization_id == sample_organization.id
        assert org.id == sample_organization.id

        # Check invitation is marked as accepted
        await session.refresh(invitation)
        assert invitation.accepted_at is not None
        assert invitation.accepted_by_id == new_user.id


class TestTenantIsolation:
    """Test tenant isolation and Row Level Security"""

    async def test_tenant_context_isolation(
        self,
        session: AsyncSession,
        sample_organization: Organization,
        second_organization: Organization,
    ):
        """Test that tenant context properly isolates data"""
        # Create users in different organizations
        async with TenantContextManager(session, sample_organization.id) as ctx:
            user_repo = ctx.get_repository(User)
            user1 = await user_repo.create(
                email="user1@org1.com",
                username="user1",
                password_hash="hash1",
                role=UserRole.STUDENT,
            )

        async with TenantContextManager(session, second_organization.id) as ctx:
            user_repo = ctx.get_repository(User)
            user2 = await user_repo.create(
                email="user2@org2.com",
                username="user2",
                password_hash="hash2",
                role=UserRole.STUDENT,
            )

        # Test isolation - each tenant should only see their own users
        async with TenantContextManager(session, sample_organization.id) as ctx:
            user_repo = ctx.get_repository(User)
            org1_users = await user_repo.get_all()
            user_emails = [u.email for u in org1_users]
            assert "user1@org1.com" in user_emails
            assert "user2@org2.com" not in user_emails

        async with TenantContextManager(session, second_organization.id) as ctx:
            user_repo = ctx.get_repository(User)
            org2_users = await user_repo.get_all()
            user_emails = [u.email for u in org2_users]
            assert "user2@org2.com" in user_emails
            assert "user1@org1.com" not in user_emails

    async def test_cross_tenant_access_prevention(
        self,
        session: AsyncSession,
        sample_organization: Organization,
        second_organization: Organization,
    ):
        """Test that users cannot access data from other tenants"""
        # Create user in first organization
        async with TenantContextManager(session, sample_organization.id) as ctx:
            user_repo = ctx.get_repository(User)
            user1 = await user_repo.create(
                email="isolated@org1.com",
                username="isolated",
                password_hash="hash",
                role=UserRole.STUDENT,
            )

        # Try to access from second organization context
        async with TenantContextManager(session, second_organization.id) as ctx:
            user_repo = ctx.get_repository(User)
            retrieved_user = await user_repo.get_by_id(user1.id)
            # Should not be able to access user from different organization
            assert retrieved_user is None

    async def test_rls_policy_enforcement(self, session: AsyncSession):
        """Test that RLS policies are properly enforced"""
        # This test would verify that RLS policies prevent cross-tenant access
        # when tenant context is not set or is set incorrectly

        # Test 1: Query without tenant context should return no results
        result = await session.execute(select(User))
        users_no_context = result.scalars().all()
        # Depending on RLS configuration, this might return empty or raise error

        # Test 2: Set invalid tenant context
        await session.execute(
            text("SELECT set_config('app.current_organization_id', :org_id, true)"),
            {"org_id": str(uuid4())},
        )
        result = await session.execute(select(User))
        users_invalid_context = result.scalars().all()
        # Should return empty results for non-existent organization


class TestUsageReporting:
    """Test usage logging and reporting"""

    async def test_usage_log_creation(
        self, tenant_service: TenantService, sample_organization: Organization
    ):
        """Test creating usage logs"""
        usage_log = await tenant_service.org_repo.log_usage(
            org_id=sample_organization.id, log_type="daily"
        )

        assert usage_log.organization_id == sample_organization.id
        assert usage_log.log_type == "daily"
        assert usage_log.users_count >= 0
        assert usage_log.usage_data is not None

    async def test_usage_report_generation(
        self, tenant_service: TenantService, sample_organization: Organization
    ):
        """Test generating usage reports"""
        # Create some usage logs
        await tenant_service.org_repo.log_usage(sample_organization.id, "daily")

        # Generate report
        report = await tenant_service.generate_usage_report(
            organization_id=sample_organization.id,
            start_date=datetime.utcnow() - timedelta(days=7),
            end_date=datetime.utcnow(),
        )

        assert report["organization_id"] == sample_organization.id
        assert "current_stats" in report
        assert "historical_data" in report
        assert "summary" in report

    async def test_usage_limit_checking(
        self, tenant_service: TenantService, sample_organization: Organization
    ):
        """Test usage limit checking"""
        # Check current limits
        limit_status = await tenant_service.check_usage_limits(sample_organization.id)

        assert "usage_percentage" in limit_status
        assert "warnings" in limit_status
        assert "limits_exceeded" in limit_status
        assert "subscription_tier" in limit_status


class TestErrorHandling:
    """Test error handling and edge cases"""

    async def test_duplicate_organization_slug(self, tenant_service: TenantService):
        """Test handling of duplicate organization slugs"""
        # This should be handled by the slug generation logic
        org1, _ = await tenant_service.create_organization(
            name="Duplicate Test", admin_email="admin1@duplicate.com", admin_password="password123"
        )

        org2, _ = await tenant_service.create_organization(
            name="Duplicate Test", admin_email="admin2@duplicate.com", admin_password="password123"
        )

        assert org1.slug != org2.slug

    async def test_invalid_invitation_token(self, tenant_service: TenantService):
        """Test handling of invalid invitation tokens"""
        with pytest.raises(ValueError, match="Invalid invitation token"):
            await tenant_service.accept_invitation(
                invitation_token="invalid_token",
                user_id=uuid4(),
                password="password",
                first_name="Test",
                last_name="User",
            )

    async def test_organization_not_found(self, tenant_service: TenantService):
        """Test handling of non-existent organization"""
        non_existent_id = uuid4()
        org = await tenant_service.org_repo.get_by_id(non_existent_id)
        assert org is None

    async def test_subscription_limit_exceeded(
        self, tenant_service: TenantService, sample_organization: Organization
    ):
        """Test behavior when subscription limits are exceeded"""
        # Set usage to maximum
        org = sample_organization
        org.current_users = org.max_users

        # Try to add one more user
        can_add = await tenant_service.org_repo.check_limits(org.id, "users")
        assert not can_add


# Integration test examples
class TestIntegrationScenarios:
    """Test realistic integration scenarios"""

    async def test_complete_organization_setup(self, tenant_service: TenantService):
        """Test complete organization setup workflow"""
        # 1. Create organization
        org, admin = await tenant_service.create_organization(
            name="Complete Test Org",
            admin_email="admin@complete.com",
            admin_password="admin_password_123",
            admin_first_name="Admin",
            admin_last_name="User",
        )

        # 2. Invite teacher
        teacher_invitation = await tenant_service.invite_user(
            organization_id=org.id,
            email="teacher@complete.com",
            role=UserRole.TEACHER,
            invited_by_id=admin.id,
        )

        # 3. Accept teacher invitation
        teacher, _ = await tenant_service.accept_invitation(
            invitation_token=teacher_invitation.invitation_token,
            user_id=uuid4(),
            password="teacher_password",
            first_name="Teacher",
            last_name="User",
        )

        # 4. Invite student
        student_invitation = await tenant_service.invite_user(
            organization_id=org.id,
            email="student@complete.com",
            role=UserRole.STUDENT,
            invited_by_id=admin.id,
        )

        # 5. Accept student invitation
        student, _ = await tenant_service.accept_invitation(
            invitation_token=student_invitation.invitation_token,
            user_id=uuid4(),
            password="student_password",
            first_name="Student",
            last_name="User",
        )

        # 6. Verify organization state
        updated_org = await tenant_service.org_repo.get_by_id(org.id)
        assert updated_org.current_users == 3  # admin + teacher + student

        # 7. Upgrade subscription
        final_org = await tenant_service.upgrade_subscription(
            organization_id=org.id, new_tier=SubscriptionTier.PROFESSIONAL, updated_by_id=admin.id
        )

        assert final_org.subscription_tier == SubscriptionTier.PROFESSIONAL
        assert final_org.status == OrganizationStatus.ACTIVE


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

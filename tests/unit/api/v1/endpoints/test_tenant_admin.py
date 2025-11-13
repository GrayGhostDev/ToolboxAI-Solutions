"""
Unit Tests for Tenant Admin Endpoints

Tests tenant administration functionality including:
- Tenant CRUD operations
- Tenant provisioning workflow
- Tenant limits management
- Subscription tier updates
- Multi-tenant isolation
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.api.v1.endpoints.tenant_admin import (
    TenantCreateRequest,
    TenantLimitsUpdateRequest,
    TenantProvisionRequest,
    TenantUpdateRequest,
    create_tenant,
    delete_tenant,
    get_tenant,
    list_tenants,
    provision_tenant,
    update_tenant,
    update_tenant_limits,
)
from database.models.tenant import Organization, OrganizationStatus, SubscriptionTier


@pytest.fixture
def mock_session():
    """Mock async database session"""
    session = Mock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.add = Mock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    session.rollback = AsyncMock()
    session.get = AsyncMock()
    return session


@pytest.fixture
def mock_admin_user():
    """Mock super admin user"""
    user = Mock()
    user.id = 1
    user.username = "superadmin"
    user.email = "admin@toolboxai.com"
    user.role = "admin"
    return user


@pytest.fixture
def sample_organization():
    """Sample organization for testing"""
    org = Mock(spec=Organization)
    org.id = uuid4()
    org.name = "Test Organization"
    org.slug = "test-org"
    org.email = "contact@test-org.com"
    org.status = OrganizationStatus.ACTIVE
    org.subscription_tier = SubscriptionTier.PROFESSIONAL
    org.is_active = True
    org.created_at = datetime.now(timezone.utc)
    org.updated_at = None
    org.current_users = 5
    org.current_classes = 3
    org.current_storage_gb = 2.5
    org.max_users = 50
    org.max_classes = 20
    org.max_storage_gb = 100.0
    return org


class TestTenantCreation:
    """Test tenant creation functionality."""

    @pytest.mark.asyncio
    async def test_create_tenant_success(self, mock_session, mock_admin_user):
        """Test successful tenant creation."""
        # Arrange
        request = TenantCreateRequest(
            name="New Organization",
            slug="new-org",
            email="new@org.com",
            subscription_tier=SubscriptionTier.BASIC,
            trial_days=14,
        )

        # Mock no existing tenant
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(return_value=None)
        mock_session.execute.return_value = mock_result

        # Act
        result = await create_tenant(request, mock_session, mock_admin_user)

        # Assert
        assert result.name == "New Organization"
        assert result.slug == "new-org"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tenant_duplicate_slug(self, mock_session, mock_admin_user):
        """Test tenant creation with duplicate slug."""
        # Arrange
        request = TenantCreateRequest(
            name="New Organization", slug="existing-slug", email="new@org.com"
        )

        # Mock existing tenant
        existing_org = Mock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(return_value=existing_org)
        mock_session.execute.return_value = mock_result

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await create_tenant(request, mock_session, mock_admin_user)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert "already exists" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_create_tenant_with_trial(self, mock_session, mock_admin_user):
        """Test tenant creation with trial period."""
        # Arrange
        request = TenantCreateRequest(
            name="Trial Organization", slug="trial-org", email="trial@org.com", trial_days=30
        )

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(return_value=None)
        mock_session.execute.return_value = mock_result

        # Act
        result = await create_tenant(request, mock_session, mock_admin_user)

        # Assert
        assert result.status == OrganizationStatus.TRIAL
        mock_session.commit.assert_called_once()


class TestTenantListing:
    """Test tenant listing and filtering."""

    @pytest.mark.asyncio
    async def test_list_tenants_success(self, mock_session):
        """Test successful tenant listing."""
        # Arrange
        mock_orgs = [Mock(spec=Organization) for _ in range(3)]
        for i, org in enumerate(mock_orgs):
            org.id = uuid4()
            org.name = f"Organization {i+1}"
            org.slug = f"org-{i+1}"
            org.is_active = True
            org.status = OrganizationStatus.ACTIVE
            org.subscription_tier = SubscriptionTier.BASIC

        # Mock query results
        mock_count_result = AsyncMock()
        mock_count_result.scalar = AsyncMock(return_value=3)

        mock_list_result = AsyncMock()
        mock_list_result.scalars = Mock(return_value=Mock(all=Mock(return_value=mock_orgs)))

        mock_session.execute.side_effect = [mock_count_result, mock_list_result]

        # Act
        result = await list_tenants(mock_session, page=1, page_size=10)

        # Assert
        assert result.total == 3
        assert len(result.tenants) == 3
        assert result.page == 1

    @pytest.mark.asyncio
    async def test_list_tenants_with_filters(self, mock_session):
        """Test tenant listing with status and tier filters."""
        # Arrange
        mock_orgs = [Mock(spec=Organization)]
        mock_orgs[0].id = uuid4()
        mock_orgs[0].status = OrganizationStatus.TRIAL
        mock_orgs[0].subscription_tier = SubscriptionTier.PROFESSIONAL

        mock_count_result = AsyncMock()
        mock_count_result.scalar = AsyncMock(return_value=1)

        mock_list_result = AsyncMock()
        mock_list_result.scalars = Mock(return_value=Mock(all=Mock(return_value=mock_orgs)))

        mock_session.execute.side_effect = [mock_count_result, mock_list_result]

        # Act
        result = await list_tenants(
            mock_session,
            status_filter=OrganizationStatus.TRIAL,
            tier_filter=SubscriptionTier.PROFESSIONAL,
        )

        # Assert
        assert result.total == 1
        assert result.tenants[0].status == OrganizationStatus.TRIAL

    @pytest.mark.asyncio
    async def test_list_tenants_pagination(self, mock_session):
        """Test tenant listing pagination."""
        # Arrange
        mock_count_result = AsyncMock()
        mock_count_result.scalar = AsyncMock(return_value=50)

        mock_list_result = AsyncMock()
        mock_list_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[])))

        mock_session.execute.side_effect = [mock_count_result, mock_list_result]

        # Act
        result = await list_tenants(mock_session, page=2, page_size=20)

        # Assert
        assert result.page == 2
        assert result.page_size == 20
        assert result.total == 50


class TestTenantRetrieval:
    """Test individual tenant retrieval."""

    @pytest.mark.asyncio
    async def test_get_tenant_success(self, mock_session, sample_organization):
        """Test successful tenant retrieval."""
        # Arrange
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(return_value=sample_organization)
        mock_session.execute.return_value = mock_result

        # Act
        result = await get_tenant(sample_organization.id, mock_session)

        # Assert
        assert result.id == sample_organization.id
        assert result.name == sample_organization.name

    @pytest.mark.asyncio
    async def test_get_tenant_not_found(self, mock_session):
        """Test tenant retrieval when not found."""
        # Arrange
        tenant_id = uuid4()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(return_value=None)
        mock_session.execute.return_value = mock_result

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_tenant(tenant_id, mock_session)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestTenantUpdate:
    """Test tenant update functionality."""

    @pytest.mark.asyncio
    async def test_update_tenant_success(self, mock_session, sample_organization):
        """Test successful tenant update."""
        # Arrange
        request = TenantUpdateRequest(name="Updated Name", description="Updated description")

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(return_value=sample_organization)
        mock_session.execute.return_value = mock_result

        # Act
        result = await update_tenant(sample_organization.id, request, mock_session)

        # Assert
        assert result.name == "Updated Name"
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_tenant_not_found(self, mock_session):
        """Test tenant update when not found."""
        # Arrange
        tenant_id = uuid4()
        request = TenantUpdateRequest(name="Updated")

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(return_value=None)
        mock_session.execute.return_value = mock_result

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await update_tenant(tenant_id, request, mock_session)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestTenantDeletion:
    """Test tenant deletion (soft and hard)."""

    @pytest.mark.asyncio
    async def test_delete_tenant_soft_delete(self, mock_session, sample_organization):
        """Test soft delete (default)."""
        # Arrange
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(return_value=sample_organization)
        mock_session.execute.return_value = mock_result

        # Act
        await delete_tenant(sample_organization.id, mock_session, permanent=False)

        # Assert
        assert sample_organization.is_active is False
        assert sample_organization.status == OrganizationStatus.CANCELLED
        mock_session.commit.assert_called_once()
        mock_session.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_tenant_hard_delete(self, mock_session, sample_organization):
        """Test permanent deletion."""
        # Arrange
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(return_value=sample_organization)
        mock_session.execute.return_value = mock_result

        # Act
        await delete_tenant(sample_organization.id, mock_session, permanent=True)

        # Assert
        mock_session.delete.assert_called_once_with(sample_organization)
        mock_session.commit.assert_called_once()


class TestTenantProvisioning:
    """Test tenant provisioning workflow."""

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.tenant_admin.TenantProvisioner")
    async def test_provision_tenant_success(
        self, mock_provisioner_class, mock_session, sample_organization
    ):
        """Test successful tenant provisioning."""
        # Arrange
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(return_value=sample_organization)
        mock_session.execute.return_value = mock_result

        request = TenantProvisionRequest(
            create_admin_user=True, admin_email="admin@test.com", send_welcome_email=True
        )

        mock_provisioner = Mock()
        mock_provisioner.provision_tenant = AsyncMock(
            return_value={
                "status": "success",
                "admin_user_id": str(uuid4()),
                "message": "Tenant provisioned successfully",
            }
        )
        mock_provisioner_class.return_value = mock_provisioner

        # Act
        result = await provision_tenant(
            sample_organization.id, request, mock_session, Mock()  # background_tasks
        )

        # Assert
        assert result.status == "success"
        assert result.tenant_id == sample_organization.id
        mock_provisioner.provision_tenant.assert_called_once()

    @pytest.mark.asyncio
    async def test_provision_tenant_not_found(self, mock_session):
        """Test provisioning non-existent tenant."""
        # Arrange
        tenant_id = uuid4()
        request = TenantProvisionRequest()

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(return_value=None)
        mock_session.execute.return_value = mock_result

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await provision_tenant(tenant_id, request, mock_session, Mock())

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestTenantLimits:
    """Test tenant limits management."""

    @pytest.mark.asyncio
    async def test_update_tenant_limits_success(self, mock_session, sample_organization):
        """Test successful limits update."""
        # Arrange
        request = TenantLimitsUpdateRequest(max_users=100, max_classes=50, max_storage_gb=200.0)

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(return_value=sample_organization)
        mock_session.execute.return_value = mock_result

        # Act
        result = await update_tenant_limits(sample_organization.id, request, mock_session)

        # Assert
        assert result.max_users == 100
        assert result.max_classes == 50
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_tenant_limits_not_found(self, mock_session):
        """Test limits update when tenant not found."""
        # Arrange
        tenant_id = uuid4()
        request = TenantLimitsUpdateRequest(max_users=100)

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(return_value=None)
        mock_session.execute.return_value = mock_result

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await update_tenant_limits(tenant_id, request, mock_session)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

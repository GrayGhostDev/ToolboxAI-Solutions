"""
Unit Tests for Tenant Provisioner Service

Tests tenant provisioning workflow including:
- Tenant initialization and admin setup
- Default settings and features configuration
- Welcome email notifications
- Tenant deprovisioning workflow
"""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from apps.backend.services.tenant_provisioner import TenantProvisioner
from database.models.tenant import Organization, OrganizationStatus, SubscriptionTier
from database.models.user_modern import User


@pytest.fixture
def mock_session():
    """Mock async database session"""
    session = Mock()
    session.get = AsyncMock()
    session.add = Mock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def mock_organization():
    """Mock organization for testing"""
    org = Mock(spec=Organization)
    org.id = uuid4()
    org.name = "Test Organization"
    org.slug = "test-org"
    org.email = "contact@test-org.com"
    org.status = OrganizationStatus.PENDING
    org.subscription_tier = SubscriptionTier.BASIC
    org.is_verified = False
    org.is_active = True
    org.trial_expires_at = None
    org.settings = {}
    org.features = []
    org.created_by_id = None
    org.updated_at = None
    org.deleted_at = None
    org.increment_usage = Mock()
    return org


@pytest.fixture
def provisioner(mock_session):
    """Tenant provisioner instance with mocked session"""
    return TenantProvisioner(session=mock_session)


class TestProvisionTenant:
    """Test tenant provisioning workflow."""

    @pytest.mark.asyncio
    async def test_provision_tenant_success(self, provisioner, mock_session, mock_organization):
        """Test successful complete tenant provisioning."""
        # Arrange
        mock_session.get.return_value = mock_organization

        with (
            patch.object(
                provisioner, "_create_admin_user", new_callable=AsyncMock
            ) as mock_create_admin,
            patch.object(provisioner, "_initialize_default_settings", new_callable=AsyncMock),
            patch.object(provisioner, "_configure_default_features", new_callable=AsyncMock),
            patch.object(provisioner, "_send_welcome_email", new_callable=AsyncMock),
        ):
            mock_create_admin.return_value = {
                "user_id": 1,
                "email": "admin@test-org.com",
                "username": "admin_test-org",
                "password": "generated_password",
            }

            # Act
            result = await provisioner.provision_tenant(
                organization_id=mock_organization.id,
                admin_email="admin@test-org.com",
                admin_username="admin_test-org",
                create_admin=True,
                initialize_defaults=True,
                send_welcome_email=True,
            )

            # Assert
            assert result["status"] == "success"
            assert result["organization_id"] == str(mock_organization.id)
            assert result["admin_user_id"] is not None
            assert "admin_user_created" in result["steps_completed"]
            assert "default_settings_initialized" in result["steps_completed"]
            assert "default_features_configured" in result["steps_completed"]
            assert "organization_verified" in result["steps_completed"]
            assert "welcome_email_sent" in result["steps_completed"]
            assert len(result["errors"]) == 0
            mock_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_provision_tenant_already_provisioned(
        self, provisioner, mock_session, mock_organization
    ):
        """Test provisioning attempt for already provisioned organization."""
        # Arrange
        mock_organization.status = OrganizationStatus.ACTIVE
        mock_organization.is_verified = True
        mock_session.get.return_value = mock_organization

        # Act
        result = await provisioner.provision_tenant(
            organization_id=mock_organization.id, create_admin=True
        )

        # Assert
        assert result["status"] == "already_provisioned"
        assert "already provisioned and active" in result["message"]
        assert result["organization_id"] == str(mock_organization.id)

    @pytest.mark.asyncio
    async def test_provision_tenant_organization_not_found(self, provisioner, mock_session):
        """Test provisioning when organization doesn't exist."""
        # Arrange
        organization_id = uuid4()
        mock_session.get.return_value = None

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await provisioner.provision_tenant(organization_id=organization_id, create_admin=True)

        assert "Organization not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_provision_tenant_partial_success(
        self, provisioner, mock_session, mock_organization
    ):
        """Test provisioning with some steps failing."""
        # Arrange
        mock_session.get.return_value = mock_organization

        with (
            patch.object(
                provisioner, "_create_admin_user", new_callable=AsyncMock
            ) as mock_create_admin,
            patch.object(
                provisioner, "_initialize_default_settings", new_callable=AsyncMock
            ) as mock_init_settings,
            patch.object(
                provisioner, "_configure_default_features", new_callable=AsyncMock
            ) as mock_config_features,
            patch.object(
                provisioner, "_send_welcome_email", new_callable=AsyncMock
            ) as mock_send_email,
        ):
            # Make admin creation fail
            mock_create_admin.side_effect = Exception("Email service unavailable")

            mock_init_settings.return_value = None
            mock_config_features.return_value = None
            mock_send_email.return_value = None

            # Act
            result = await provisioner.provision_tenant(
                organization_id=mock_organization.id,
                create_admin=True,
                initialize_defaults=True,
            )

            # Assert
            assert result["status"] == "partial_success"
            assert len(result["errors"]) > 0
            assert "Failed to create admin user" in result["errors"][0]
            assert len(result["steps_completed"]) > 0  # Some steps completed

    @pytest.mark.asyncio
    async def test_provision_tenant_without_admin(
        self, provisioner, mock_session, mock_organization
    ):
        """Test provisioning without creating admin user."""
        # Arrange
        mock_session.get.return_value = mock_organization

        with (
            patch.object(
                provisioner, "_initialize_default_settings", new_callable=AsyncMock
            ) as mock_init_settings,
            patch.object(
                provisioner, "_configure_default_features", new_callable=AsyncMock
            ) as mock_config_features,
        ):
            mock_init_settings.return_value = None
            mock_config_features.return_value = None

            # Act
            result = await provisioner.provision_tenant(
                organization_id=mock_organization.id,
                create_admin=False,
                initialize_defaults=True,
                send_welcome_email=False,
            )

            # Assert
            assert result["status"] == "success"
            assert result["admin_user_id"] is None
            assert "admin_user_created" not in result["steps_completed"]
            assert "default_settings_initialized" in result["steps_completed"]


class TestCreateAdminUser:
    """Test admin user creation."""

    @pytest.mark.asyncio
    async def test_create_admin_user_success(self, provisioner, mock_session, mock_organization):
        """Test successful admin user creation."""
        # Arrange
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.email = "admin@test-org.com"
        mock_user.username = "admin_test-org"

        with patch("apps.backend.services.tenant_provisioner.User", return_value=mock_user):
            # Act
            result = await provisioner._create_admin_user(
                org=mock_organization,
                email="admin@test-org.com",
                username="admin_test-org",
                password="SecurePassword123!",
            )

            # Assert
            assert result["user_id"] == mock_user.id
            assert result["email"] == "admin@test-org.com"
            assert result["username"] == "admin_test-org"
            assert "password" not in result  # Not auto-generated
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_admin_user_auto_generated_credentials(
        self, provisioner, mock_session, mock_organization
    ):
        """Test admin user creation with auto-generated credentials."""
        # Arrange
        mock_user = Mock(spec=User)
        mock_user.id = 1

        with patch("apps.backend.services.tenant_provisioner.User", return_value=mock_user):
            # Act
            result = await provisioner._create_admin_user(
                org=mock_organization,
                email=None,  # Should use org email
                username=None,  # Should be auto-generated
                password=None,  # Should be auto-generated
            )

            # Assert
            assert result["email"] == mock_organization.email
            assert result["username"] == f"admin_{mock_organization.slug}"
            assert "password" in result  # Auto-generated password returned
            assert len(result["password"]) > 0

    @pytest.mark.asyncio
    async def test_create_admin_user_no_email(self, provisioner, mock_session, mock_organization):
        """Test admin user creation fails when no email available."""
        # Arrange
        mock_organization.email = None

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await provisioner._create_admin_user(
                org=mock_organization,
                email=None,  # No email provided and org has no email
            )

        assert "Admin email is required" in str(exc_info.value)


class TestInitializeDefaultSettings:
    """Test default settings initialization."""

    @pytest.mark.asyncio
    async def test_initialize_default_settings_success(
        self, provisioner, mock_session, mock_organization
    ):
        """Test successful default settings initialization."""
        # Arrange
        mock_organization.settings = {}

        # Act
        await provisioner._initialize_default_settings(mock_organization)

        # Assert
        assert isinstance(mock_organization.settings, dict)
        assert "email_notifications" in mock_organization.settings
        assert "session_timeout_minutes" in mock_organization.settings
        assert "require_parental_consent" in mock_organization.settings
        assert mock_organization.settings["email_notifications"] is True
        assert mock_organization.settings["session_timeout_minutes"] == 60
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_default_settings_merge_existing(
        self, provisioner, mock_session, mock_organization
    ):
        """Test that default settings merge with existing settings."""
        # Arrange
        mock_organization.settings = {
            "custom_setting": "custom_value",
            "email_notifications": False,  # Will be overridden
        }

        # Act
        await provisioner._initialize_default_settings(mock_organization)

        # Assert
        assert mock_organization.settings["custom_setting"] == "custom_value"  # Preserved
        assert mock_organization.settings["email_notifications"] is True  # Overridden
        assert "session_timeout_minutes" in mock_organization.settings  # Added


class TestConfigureDefaultFeatures:
    """Test default features configuration."""

    @pytest.mark.asyncio
    async def test_configure_default_features_by_tier(
        self, provisioner, mock_session, mock_organization
    ):
        """Test that features are configured correctly for each tier."""
        # Test FREE tier
        mock_organization.subscription_tier = SubscriptionTier.FREE
        await provisioner._configure_default_features(mock_organization)
        assert "ai_chat" in mock_organization.features
        assert "gamification" in mock_organization.features
        assert "api_access" not in mock_organization.features

        # Test PROFESSIONAL tier
        mock_organization.subscription_tier = SubscriptionTier.PROFESSIONAL
        await provisioner._configure_default_features(mock_organization)
        assert "ai_chat" in mock_organization.features
        assert "roblox_integration" in mock_organization.features
        assert "advanced_analytics" in mock_organization.features
        assert "custom_branding" in mock_organization.features

        # Test ENTERPRISE tier
        mock_organization.subscription_tier = SubscriptionTier.ENTERPRISE
        await provisioner._configure_default_features(mock_organization)
        assert "sso" in mock_organization.features
        assert "api_access" in mock_organization.features
        assert "webhooks" in mock_organization.features
        assert "advanced_security" in mock_organization.features

    @pytest.mark.asyncio
    async def test_configure_default_features_unknown_tier(self, provisioner, mock_session):
        """Test features configuration with unknown tier defaults to free."""
        # Arrange - create org with minimal mock
        org = Mock()
        org.id = uuid4()
        org.subscription_tier = Mock()
        org.subscription_tier.value = "unknown_tier"
        org.features = []

        # Act
        await provisioner._configure_default_features(org)

        # Assert - should default to free tier
        assert "ai_chat" in org.features
        assert "gamification" in org.features
        mock_session.commit.assert_called()


class TestDeprovisionTenant:
    """Test tenant deprovisioning workflow."""

    @pytest.mark.asyncio
    async def test_deprovision_tenant_soft_delete(
        self, provisioner, mock_session, mock_organization
    ):
        """Test soft delete deprovisioning."""
        # Arrange
        mock_session.get.return_value = mock_organization

        # Act
        result = await provisioner.deprovision_tenant(
            organization_id=mock_organization.id, delete_data=False, backup_data=True
        )

        # Assert
        assert result["status"] == "success"
        assert mock_organization.is_active is False
        assert mock_organization.status == OrganizationStatus.SUSPENDED
        assert "organization_deactivated" in result["steps_completed"]
        mock_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_deprovision_tenant_hard_delete(
        self, provisioner, mock_session, mock_organization
    ):
        """Test hard delete deprovisioning."""
        # Arrange
        mock_session.get.return_value = mock_organization

        # Act
        result = await provisioner.deprovision_tenant(
            organization_id=mock_organization.id, delete_data=True, backup_data=True
        )

        # Assert
        assert result["status"] == "success"
        assert mock_organization.is_active is False
        assert mock_organization.status == OrganizationStatus.CANCELLED
        assert mock_organization.deleted_at is not None
        assert "organization_deleted" in result["steps_completed"]
        mock_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_deprovision_tenant_organization_not_found(self, provisioner, mock_session):
        """Test deprovisioning when organization doesn't exist."""
        # Arrange
        organization_id = uuid4()
        mock_session.get.return_value = None

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await provisioner.deprovision_tenant(organization_id=organization_id, delete_data=False)

        assert "Organization not found" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

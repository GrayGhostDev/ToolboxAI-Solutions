"""
Tests for Organization API endpoints.

Tests the organizations.py endpoints which provide:
- GET /organizations/current - Get current organization
- POST /organizations - Create organization
- GET /organizations/{id} - Get organization by ID
- PATCH /organizations/{id} - Update organization
- GET /organizations/{id}/members - List members
- POST /organizations/{id}/invite - Create invitation
- PATCH /organizations/{id}/subscription - Update subscription
- DELETE /organizations/{id}/members/{user_id} - Remove member
- GET /organizations/{id}/usage - Get usage statistics
- GET /organizations/{id}/features - Get features

Total: 10 endpoints to test
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import HTTPException

from apps.backend.api.v1.endpoints.organizations import (
    get_current_organization_info,
    create_organization,
    get_organization,
    update_organization,
    get_organization_members,
    create_invitation,
    update_subscription,
    remove_organization_member,
    get_organization_usage,
    get_organization_features,
    OrganizationCreateRequest,
    OrganizationUpdateRequest,
    InvitationCreateRequest,
    SubscriptionUpdateRequest,
)


class TestGetCurrentOrganization:
    """Tests for GET /organizations/current endpoint."""

    @pytest.fixture
    def mock_user(self):
        user = MagicMock()
        user.id = str(uuid4())
        user.username = "test_user"
        return user

    @pytest.mark.asyncio
    async def test_get_current_organization_success(self, mock_user):
        """Test successful retrieval of current organization."""
        organization_id = str(uuid4())

        response = await get_current_organization_info(
            current_user=mock_user,
            organization_id=organization_id
        )

        assert response.id == organization_id
        assert response.name == "Development Organization"
        assert response.slug == "dev-org"
        assert response.subscription_tier == "professional"
        assert response.is_active == True
        assert response.is_trial == False

    @pytest.mark.asyncio
    async def test_get_current_organization_no_context(self, mock_user):
        """Test error when no organization context found."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_organization_info(
                current_user=mock_user,
                organization_id=None
            )

        assert exc_info.value.status_code == 400
        assert "No organization context found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_organization_response_structure(self, mock_user):
        """Test that response has correct structure."""
        organization_id = str(uuid4())

        response = await get_current_organization_info(
            current_user=mock_user,
            organization_id=organization_id
        )

        # Verify required fields
        required_fields = [
            "id", "name", "slug", "subscription_tier", "status",
            "is_active", "is_trial", "usage_percentage", "settings",
            "features", "created_at"
        ]

        for field in required_fields:
            assert hasattr(response, field), f"Missing field: {field}"

        # Verify data types
        assert isinstance(response.usage_percentage, dict)
        assert isinstance(response.settings, dict)
        assert isinstance(response.features, list)


class TestCreateOrganization:
    """Tests for POST /organizations endpoint."""

    @pytest.fixture
    def mock_user(self):
        user = MagicMock()
        user.id = str(uuid4())
        user.username = "test_user"
        user.email = "test@example.com"
        return user

    @pytest.fixture
    def valid_org_request(self):
        return OrganizationCreateRequest(
            name="Test Organization",
            slug="test-org",
            display_name="Test Org Display",
            description="A test organization",
            email="contact@testorg.com",
            organization_type="education",
            timezone="America/New_York",
            locale="en-US"
        )

    @pytest.mark.asyncio
    async def test_create_organization_success(self, mock_user, valid_org_request):
        """Test successful organization creation."""
        response = await create_organization(
            request=valid_org_request,
            current_user=mock_user
        )

        assert response.name == valid_org_request.name
        assert response.slug == valid_org_request.slug
        assert response.display_name == valid_org_request.display_name
        assert response.subscription_tier == "trial"
        assert response.is_trial == True
        assert response.trial_days_remaining == 14
        assert response.is_active == True

    @pytest.mark.asyncio
    async def test_create_organization_with_minimal_fields(self, mock_user):
        """Test organization creation with only required fields."""
        request = OrganizationCreateRequest(
            name="Minimal Org",
            slug="minimal-org"
        )

        response = await create_organization(
            request=request,
            current_user=mock_user
        )

        assert response.name == "Minimal Org"
        assert response.slug == "minimal-org"
        assert response.is_active == True

    def test_slug_validation(self):
        """Test slug format validation."""
        # Valid slug
        valid_request = OrganizationCreateRequest(
            name="Test",
            slug="test-org-123"
        )
        assert valid_request.slug == "test-org-123"

        # Invalid slug with uppercase
        with pytest.raises(ValueError):
            OrganizationCreateRequest(
                name="Test",
                slug="Test-Org"
            )

        # Invalid slug with special characters
        with pytest.raises(ValueError):
            OrganizationCreateRequest(
                name="Test",
                slug="test_org!"
            )


class TestGetOrganization:
    """Tests for GET /organizations/{organization_id} endpoint."""

    @pytest.fixture
    def mock_user(self):
        user = MagicMock()
        user.id = str(uuid4())
        return user

    @pytest.mark.asyncio
    async def test_get_organization_success(self, mock_user):
        """Test successful organization retrieval."""
        organization_id = str(uuid4())

        response = await get_organization(
            organization_id=organization_id,
            current_user=mock_user
        )

        assert response.id == organization_id
        assert "Organization" in response.name
        assert response.is_active == True
        assert isinstance(response.usage_percentage, dict)

    @pytest.mark.asyncio
    async def test_get_organization_returns_mock_data(self, mock_user):
        """Test that endpoint returns mock data for development."""
        organization_id = str(uuid4())

        response = await get_organization(
            organization_id=organization_id,
            current_user=mock_user
        )

        # Should return mock data
        assert response.subscription_tier == "basic"
        assert response.organization_type == "education"
        assert response.status == "active"


class TestUpdateOrganization:
    """Tests for PATCH /organizations/{organization_id} endpoint."""

    @pytest.fixture
    def mock_user(self):
        user = MagicMock()
        user.id = str(uuid4())
        return user

    @pytest.fixture
    def update_request(self):
        return OrganizationUpdateRequest(
            name="Updated Organization Name",
            display_name="Updated Display Name",
            description="Updated description",
            email="updated@example.com"
        )

    @pytest.mark.asyncio
    async def test_update_organization_not_found(self, mock_user, update_request):
        """Test update when organization doesn't exist."""
        organization_id = str(uuid4())

        with pytest.raises(HTTPException) as exc_info:
            await update_organization(
                organization_id=organization_id,
                request=update_request,
                current_user=mock_user
            )

        assert exc_info.value.status_code == 404
        assert "Organization not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_update_organization_partial_update(self, mock_user):
        """Test partial update with only some fields."""
        organization_id = str(uuid4())

        request = OrganizationUpdateRequest(
            name="New Name Only"
        )

        # Note: This will fail with 404 in current mock implementation
        # In real implementation with DB, would test partial updates
        with pytest.raises(HTTPException) as exc_info:
            await update_organization(
                organization_id=organization_id,
                request=request,
                current_user=mock_user
            )

        assert exc_info.value.status_code == 404


class TestGetOrganizationMembers:
    """Tests for GET /organizations/{organization_id}/members endpoint."""

    @pytest.fixture
    def mock_user(self):
        user = MagicMock()
        user.id = str(uuid4())
        return user

    @pytest.mark.asyncio
    async def test_get_organization_members_success(self, mock_user):
        """Test successful retrieval of organization members."""
        organization_id = str(uuid4())

        response = await get_organization_members(
            organization_id=organization_id,
            current_user=mock_user,
            limit=50,
            offset=0
        )

        assert isinstance(response, list)
        assert len(response) == 3  # Mock returns 3 members
        assert response[0].username == "admin_user"
        assert response[0].organization_role == "admin"
        assert response[1].organization_role == "teacher"

    @pytest.mark.asyncio
    async def test_get_organization_members_pagination(self, mock_user):
        """Test pagination with limit and offset."""
        organization_id = str(uuid4())

        # Get first page
        response = await get_organization_members(
            organization_id=organization_id,
            current_user=mock_user,
            limit=2,
            offset=0
        )

        assert len(response) == 2

        # Get second page
        response = await get_organization_members(
            organization_id=organization_id,
            current_user=mock_user,
            limit=2,
            offset=2
        )

        assert len(response) == 1  # Only 1 member left

    @pytest.mark.asyncio
    async def test_get_organization_members_response_structure(self, mock_user):
        """Test member response structure."""
        organization_id = str(uuid4())

        response = await get_organization_members(
            organization_id=organization_id,
            current_user=mock_user,
            limit=10,
            offset=0
        )

        member = response[0]
        required_fields = [
            "id", "username", "email", "role", "organization_role",
            "joined_at", "is_active"
        ]

        for field in required_fields:
            assert hasattr(member, field), f"Missing field: {field}"


class TestCreateInvitation:
    """Tests for POST /organizations/{organization_id}/invite endpoint."""

    @pytest.fixture
    def mock_admin_user(self):
        user = MagicMock()
        user.id = str(uuid4())
        user.username = "admin_user"
        return user

    @pytest.fixture
    def invitation_request(self):
        return InvitationCreateRequest(
            email="newuser@example.com",
            role="member",
            invitation_message="Welcome to our organization!"
        )

    @pytest.mark.asyncio
    async def test_create_invitation_success(self, mock_admin_user, invitation_request):
        """Test successful invitation creation."""
        organization_id = str(uuid4())

        response = await create_invitation(
            organization_id=organization_id,
            request=invitation_request,
            current_user=mock_admin_user
        )

        assert response.email == invitation_request.email
        assert response.role == invitation_request.role
        assert response.is_pending == True
        assert response.is_expired == False
        assert response.is_valid == True
        assert response.invited_by_id == mock_admin_user.id
        assert len(response.invitation_token) > 0

    @pytest.mark.asyncio
    async def test_create_invitation_expiration(self, mock_admin_user, invitation_request):
        """Test that invitation has 7-day expiration."""
        organization_id = str(uuid4())

        response = await create_invitation(
            organization_id=organization_id,
            request=invitation_request,
            current_user=mock_admin_user
        )

        # Should expire in approximately 7 days
        time_until_expiry = response.expires_at - datetime.now(timezone.utc)
        assert 6.9 <= time_until_expiry.days <= 7.1  # Allow small variance

    def test_invitation_role_validation(self):
        """Test role validation for invitations."""
        # Valid roles
        for role in ["admin", "manager", "teacher", "member"]:
            request = InvitationCreateRequest(
                email="test@example.com",
                role=role
            )
            assert request.role == role

        # Invalid role
        with pytest.raises(ValueError):
            InvitationCreateRequest(
                email="test@example.com",
                role="invalid_role"
            )


class TestUpdateSubscription:
    """Tests for PATCH /organizations/{organization_id}/subscription endpoint."""

    @pytest.fixture
    def mock_admin_user(self):
        user = MagicMock()
        user.id = str(uuid4())
        return user

    @pytest.fixture
    def subscription_request(self):
        return SubscriptionUpdateRequest(
            subscription_tier="professional",
            max_users=100,
            max_classes=50,
            max_storage_gb=100.0,
            max_api_calls_per_month=50000
        )

    @pytest.mark.asyncio
    async def test_update_subscription_not_found(self, mock_admin_user, subscription_request):
        """Test subscription update when organization not found."""
        organization_id = str(uuid4())

        with pytest.raises(HTTPException) as exc_info:
            await update_subscription(
                organization_id=organization_id,
                request=subscription_request,
                current_user=mock_admin_user
            )

        assert exc_info.value.status_code == 404

    def test_subscription_tier_validation(self):
        """Test subscription tier validation."""
        # Valid tiers
        valid_tiers = ["free", "basic", "professional", "enterprise", "education"]
        for tier in valid_tiers:
            request = SubscriptionUpdateRequest(subscription_tier=tier)
            assert request.subscription_tier == tier

        # Invalid tier
        with pytest.raises(ValueError):
            SubscriptionUpdateRequest(subscription_tier="premium")

    def test_subscription_limits_validation(self):
        """Test that subscription limits are validated."""
        # Valid limits
        request = SubscriptionUpdateRequest(
            subscription_tier="professional",
            max_users=100,
            max_storage_gb=50.0
        )
        assert request.max_users == 100
        assert request.max_storage_gb == 50.0

        # Invalid limit (negative users)
        with pytest.raises(ValueError):
            SubscriptionUpdateRequest(
                subscription_tier="professional",
                max_users=-10
            )


class TestRemoveOrganizationMember:
    """Tests for DELETE /organizations/{organization_id}/members/{user_id} endpoint."""

    @pytest.fixture
    def mock_admin_user(self):
        user = MagicMock()
        user.id = str(uuid4())
        return user

    @pytest.mark.asyncio
    async def test_remove_member_success(self, mock_admin_user):
        """Test successful member removal."""
        organization_id = str(uuid4())
        user_to_remove = str(uuid4())

        response = await remove_organization_member(
            organization_id=organization_id,
            user_id=user_to_remove,
            current_user=mock_admin_user
        )

        assert response["message"] == "Member removed successfully"

    @pytest.mark.asyncio
    async def test_remove_member_cannot_remove_self(self, mock_admin_user):
        """Test that admin cannot remove themselves."""
        organization_id = str(uuid4())

        with pytest.raises(HTTPException) as exc_info:
            await remove_organization_member(
                organization_id=organization_id,
                user_id=mock_admin_user.id,
                current_user=mock_admin_user
            )

        assert exc_info.value.status_code == 400
        assert "Cannot remove yourself" in str(exc_info.value.detail)


class TestGetOrganizationUsage:
    """Tests for GET /organizations/{organization_id}/usage endpoint."""

    @pytest.fixture
    def mock_user(self):
        user = MagicMock()
        user.id = str(uuid4())
        return user

    @pytest.mark.asyncio
    async def test_get_usage_current_period(self, mock_user):
        """Test getting current period usage."""
        organization_id = str(uuid4())

        response = await get_organization_usage(
            organization_id=organization_id,
            current_user=mock_user,
            period="current"
        )

        assert response["period"] == "current"
        assert response["organization_id"] == organization_id
        assert "usage" in response
        assert "trends" in response
        assert "generated_at" in response

    @pytest.mark.asyncio
    async def test_get_usage_structure(self, mock_user):
        """Test usage response structure."""
        organization_id = str(uuid4())

        response = await get_organization_usage(
            organization_id=organization_id,
            current_user=mock_user,
            period="current"
        )

        # Verify usage categories
        usage = response["usage"]
        expected_categories = ["users", "classes", "storage_gb", "api_calls", "roblox_sessions"]

        for category in expected_categories:
            assert category in usage
            assert "current" in usage[category]
            assert "limit" in usage[category]
            assert "percentage" in usage[category]

    @pytest.mark.asyncio
    async def test_get_usage_different_periods(self, mock_user):
        """Test usage with different time periods."""
        organization_id = str(uuid4())

        for period in ["current", "last_month", "last_year"]:
            response = await get_organization_usage(
                organization_id=organization_id,
                current_user=mock_user,
                period=period
            )

            assert response["period"] == period


class TestGetOrganizationFeatures:
    """Tests for GET /organizations/{organization_id}/features endpoint."""

    @pytest.fixture
    def mock_user(self):
        user = MagicMock()
        user.id = str(uuid4())
        return user

    @pytest.mark.asyncio
    async def test_get_features_success(self, mock_user):
        """Test successful feature retrieval."""
        organization_id = str(uuid4())

        response = await get_organization_features(
            organization_id=organization_id,
            current_user=mock_user
        )

        assert response["organization_id"] == organization_id
        assert "subscription_tier" in response
        assert "enabled_features" in response
        assert "available_upgrades" in response
        assert "feature_limits" in response

    @pytest.mark.asyncio
    async def test_get_features_structure(self, mock_user):
        """Test features response structure."""
        organization_id = str(uuid4())

        response = await get_organization_features(
            organization_id=organization_id,
            current_user=mock_user
        )

        # Verify enabled features is a list
        assert isinstance(response["enabled_features"], list)
        assert len(response["enabled_features"]) > 0

        # Verify feature limits is a dict
        assert isinstance(response["feature_limits"], dict)
        expected_limits = [
            "content_generation_per_month",
            "api_calls_per_minute",
            "storage_gb",
            "concurrent_sessions"
        ]

        for limit in expected_limits:
            assert limit in response["feature_limits"]


@pytest.mark.integration
class TestOrganizationsIntegration:
    """Integration tests for organizations endpoints."""

    @pytest.mark.asyncio
    async def test_organization_lifecycle(self):
        """Test complete organization lifecycle."""
        # TODO: Implement with real database
        # 1. Create organization
        # 2. Get organization
        # 3. Update organization
        # 4. Add members
        # 5. Create invitations
        # 6. Update subscription
        # 7. Remove members
        # 8. Check usage and features
        pass

    @pytest.mark.asyncio
    async def test_organization_authorization(self):
        """Test authorization across different organization operations."""
        # TODO: Implement authorization matrix testing
        # Test admin, manager, teacher, member roles
        pass

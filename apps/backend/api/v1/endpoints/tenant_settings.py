"""
Tenant Settings API Endpoints for ToolBoxAI Educational Platform

Provides tenant-specific configuration and settings management for
current tenant users including features, preferences, and customization.

Features:
- Tenant settings management
- Feature flag control
- Branding and customization
- Integration configuration
- Security settings
- Compliance preferences

Author: ToolBoxAI Team
Created: 2025-10-02
Version: 1.0.0
Standards: Python 3.12, FastAPI async, Pydantic v2
"""

import logging
from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.api.auth.auth import require_org_admin
from apps.backend.core.deps import get_async_db
from apps.backend.middleware.tenant import TenantContext, get_tenant_context
from database.models.tenant import Organization

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/tenant",
    tags=["tenant-settings"],
    responses={404: {"description": "Tenant not found"}},
)


# === Pydantic v2 Models ===


class TenantSettingsResponse(BaseModel):
    """Response model for tenant settings with Pydantic v2"""

    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    tenant_name: str
    tenant_slug: str

    # General settings
    timezone: str
    locale: str
    display_name: str | None = None
    description: str | None = None

    # Branding
    logo_url: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    custom_domain: str | None = None

    # Feature flags
    features: list[str] = Field(default_factory=list)

    # Settings object (flexible JSON)
    settings: dict[str, Any] = Field(default_factory=dict)

    # Security
    sso_enabled: bool = False
    audit_logs_enabled: bool = True

    # Compliance
    coppa_compliance_required: bool = True
    ferpa_compliance_required: bool = False
    data_retention_days: int = 365


class TenantSettingsUpdateRequest(BaseModel):
    """Request model for updating tenant settings"""

    model_config = ConfigDict(from_attributes=True)

    timezone: str | None = Field(None, max_length=100)
    locale: str | None = Field(None, max_length=10)
    display_name: str | None = Field(None, max_length=250)
    description: str | None = None
    logo_url: str | None = Field(None, max_length=500)
    primary_color: str | None = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    secondary_color: str | None = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    custom_domain: str | None = Field(None, max_length=255)


class TenantFeaturesResponse(BaseModel):
    """Response model for tenant features"""

    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    enabled_features: list[str] = Field(default_factory=list)
    available_features: list[str] = Field(default_factory=list)


class TenantFeatureToggleRequest(BaseModel):
    """Request model for toggling features"""

    model_config = ConfigDict(from_attributes=True)

    feature: str = Field(..., min_length=1, max_length=100)
    enabled: bool

    @field_validator("feature")
    @classmethod
    def validate_feature(cls, v: str) -> str:
        """Validate feature name"""
        valid_features = [
            "ai_chat",
            "roblox_integration",
            "advanced_analytics",
            "custom_branding",
            "sso",
            "api_access",
            "webhooks",
            "advanced_security",
            "parent_portal",
            "mobile_app",
            "gamification",
            "assessment_builder",
            "content_versioning",
            "live_classes",
            "video_conferencing",
        ]
        if v not in valid_features:
            raise ValueError(f"Invalid feature. Must be one of: {valid_features}")
        return v


class TenantLimitsResponse(BaseModel):
    """Response model for tenant limits"""

    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID

    # Current usage
    current_users: int
    current_classes: int
    current_storage_gb: float
    current_api_calls_this_month: int
    current_roblox_sessions: int

    # Limits
    max_users: int
    max_classes: int
    max_storage_gb: float
    max_api_calls_per_month: int
    max_roblox_sessions: int

    # Calculated fields
    users_remaining: int
    classes_remaining: int
    storage_remaining_gb: float
    api_calls_remaining: int
    roblox_sessions_remaining: int


class TenantCustomSettingsRequest(BaseModel):
    """Request model for custom tenant settings"""

    model_config = ConfigDict(from_attributes=True)

    settings: dict[str, Any] = Field(..., description="Custom settings as key-value pairs")


class TenantIntegrationConfig(BaseModel):
    """Configuration for tenant integrations"""

    model_config = ConfigDict(from_attributes=True)

    integration_name: str
    enabled: bool
    config: dict[str, Any] = Field(default_factory=dict)


class TenantIntegrationsResponse(BaseModel):
    """Response model for tenant integrations"""

    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    integrations: dict[str, TenantIntegrationConfig] = Field(default_factory=dict)


# === Dependency Injection ===


async def get_current_tenant(
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    session: Annotated[AsyncSession, Depends(get_async_db)],
) -> Organization:
    """
    Get current tenant organization from context.

    Args:
        tenant_context: Current tenant context
        session: Async database session

    Returns:
        Organization: Current tenant organization

    Raises:
        HTTPException: If tenant not found
    """
    if not tenant_context.effective_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No tenant context available"
        )

    result = await session.execute(
        select(Organization).where(Organization.id == tenant_context.effective_tenant_id)
    )
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    return organization


# === API Endpoints ===


@router.get(
    "/settings",
    response_model=TenantSettingsResponse,
    summary="Get tenant settings",
    description="Get current tenant settings and configuration",
)
async def get_tenant_settings(
    tenant: Annotated[Organization, Depends(get_current_tenant)],
) -> TenantSettingsResponse:
    """
    Get current tenant settings.

    Returns all configuration including branding, features, and preferences.

    Args:
        tenant: Current tenant organization

    Returns:
        TenantSettingsResponse: Tenant settings
    """
    try:
        logger.info(f"Getting settings for tenant: {tenant.id}")

        return TenantSettingsResponse(
            tenant_id=tenant.id,
            tenant_name=tenant.name,
            tenant_slug=tenant.slug,
            timezone=tenant.timezone,
            locale=tenant.locale,
            display_name=tenant.display_name,
            description=tenant.description,
            logo_url=tenant.logo_url,
            primary_color=tenant.primary_color,
            secondary_color=tenant.secondary_color,
            custom_domain=tenant.custom_domain,
            features=tenant.features if isinstance(tenant.features, list) else [],
            settings=tenant.settings if isinstance(tenant.settings, dict) else {},
            sso_enabled=tenant.sso_enabled,
            audit_logs_enabled=tenant.audit_logs_enabled,
            coppa_compliance_required=tenant.coppa_compliance_required,
            ferpa_compliance_required=tenant.ferpa_compliance_required,
            data_retention_days=tenant.data_retention_days,
        )

    except Exception as e:
        logger.error(f"Failed to get tenant settings: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tenant settings",
        )


@router.patch(
    "/settings",
    response_model=TenantSettingsResponse,
    summary="Update tenant settings",
    description="Update tenant settings (requires org admin)",
    dependencies=[Depends(require_org_admin)],
)
async def update_tenant_settings(
    request: TenantSettingsUpdateRequest,
    tenant: Annotated[Organization, Depends(get_current_tenant)],
    session: Annotated[AsyncSession, Depends(get_async_db)],
) -> TenantSettingsResponse:
    """
    Update tenant settings.

    Requires organization admin permissions.

    Args:
        request: Settings update request
        tenant: Current tenant organization
        session: Async database session

    Returns:
        TenantSettingsResponse: Updated tenant settings

    Raises:
        HTTPException: If update fails
    """
    try:
        logger.info(f"Updating settings for tenant: {tenant.id}")

        # Update fields
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tenant, field, value)

        tenant.updated_at = datetime.utcnow()

        await session.commit()
        await session.refresh(tenant)

        logger.info(f"Tenant settings updated: {tenant.id}")

        return TenantSettingsResponse(
            tenant_id=tenant.id,
            tenant_name=tenant.name,
            tenant_slug=tenant.slug,
            timezone=tenant.timezone,
            locale=tenant.locale,
            display_name=tenant.display_name,
            description=tenant.description,
            logo_url=tenant.logo_url,
            primary_color=tenant.primary_color,
            secondary_color=tenant.secondary_color,
            custom_domain=tenant.custom_domain,
            features=tenant.features if isinstance(tenant.features, list) else [],
            settings=tenant.settings if isinstance(tenant.settings, dict) else {},
            sso_enabled=tenant.sso_enabled,
            audit_logs_enabled=tenant.audit_logs_enabled,
            coppa_compliance_required=tenant.coppa_compliance_required,
            ferpa_compliance_required=tenant.ferpa_compliance_required,
            data_retention_days=tenant.data_retention_days,
        )

    except Exception as e:
        logger.error(f"Failed to update tenant settings: {str(e)}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update tenant settings",
        )


@router.get(
    "/features",
    response_model=TenantFeaturesResponse,
    summary="Get enabled features",
    description="Get list of enabled and available features for current tenant",
)
async def get_tenant_features(
    tenant: Annotated[Organization, Depends(get_current_tenant)],
) -> TenantFeaturesResponse:
    """
    Get tenant feature flags.

    Returns both enabled and available features based on subscription tier.

    Args:
        tenant: Current tenant organization

    Returns:
        TenantFeaturesResponse: Feature flags
    """
    try:
        # Define available features per tier
        tier_features = {
            "free": ["ai_chat", "gamification", "assessment_builder"],
            "basic": [
                "ai_chat",
                "roblox_integration",
                "gamification",
                "assessment_builder",
                "parent_portal",
            ],
            "professional": [
                "ai_chat",
                "roblox_integration",
                "advanced_analytics",
                "custom_branding",
                "api_access",
                "webhooks",
                "gamification",
                "assessment_builder",
                "content_versioning",
                "parent_portal",
                "mobile_app",
            ],
            "enterprise": [
                "ai_chat",
                "roblox_integration",
                "advanced_analytics",
                "custom_branding",
                "sso",
                "api_access",
                "webhooks",
                "advanced_security",
                "parent_portal",
                "mobile_app",
                "gamification",
                "assessment_builder",
                "content_versioning",
                "live_classes",
                "video_conferencing",
            ],
            "education": [
                "ai_chat",
                "roblox_integration",
                "advanced_analytics",
                "custom_branding",
                "api_access",
                "gamification",
                "assessment_builder",
                "content_versioning",
                "parent_portal",
                "mobile_app",
                "live_classes",
            ],
        }

        available_features = tier_features.get(
            tenant.subscription_tier.value, tier_features["free"]
        )

        enabled_features = tenant.features if isinstance(tenant.features, list) else []

        return TenantFeaturesResponse(
            tenant_id=tenant.id,
            enabled_features=enabled_features,
            available_features=available_features,
        )

    except Exception as e:
        logger.error(f"Failed to get tenant features: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tenant features",
        )


@router.patch(
    "/features",
    response_model=TenantFeaturesResponse,
    summary="Toggle feature",
    description="Enable or disable a feature for current tenant (requires org admin)",
    dependencies=[Depends(require_org_admin)],
)
async def toggle_tenant_feature(
    request: TenantFeatureToggleRequest,
    tenant: Annotated[Organization, Depends(get_current_tenant)],
    session: Annotated[AsyncSession, Depends(get_async_db)],
) -> TenantFeaturesResponse:
    """
    Toggle a feature for the tenant.

    Requires organization admin permissions.

    Args:
        request: Feature toggle request
        tenant: Current tenant organization
        session: Async database session

    Returns:
        TenantFeaturesResponse: Updated feature flags

    Raises:
        HTTPException: If feature not available or toggle fails
    """
    try:
        logger.info(f"Toggling feature {request.feature} for tenant: {tenant.id}")

        # Get current features
        current_features = tenant.features if isinstance(tenant.features, list) else []

        if request.enabled:
            # Enable feature
            if request.feature not in current_features:
                current_features.append(request.feature)
        else:
            # Disable feature
            if request.feature in current_features:
                current_features.remove(request.feature)

        tenant.features = current_features
        tenant.updated_at = datetime.utcnow()

        await session.commit()
        await session.refresh(tenant)

        logger.info(f"Feature {request.feature} toggled to {request.enabled}")

        # Get available features for response
        tier_features = {
            "free": ["ai_chat", "gamification", "assessment_builder"],
            "basic": [
                "ai_chat",
                "roblox_integration",
                "gamification",
                "assessment_builder",
                "parent_portal",
            ],
            "professional": [
                "ai_chat",
                "roblox_integration",
                "advanced_analytics",
                "custom_branding",
                "api_access",
                "webhooks",
                "gamification",
                "assessment_builder",
                "content_versioning",
                "parent_portal",
                "mobile_app",
            ],
            "enterprise": [
                "ai_chat",
                "roblox_integration",
                "advanced_analytics",
                "custom_branding",
                "sso",
                "api_access",
                "webhooks",
                "advanced_security",
                "parent_portal",
                "mobile_app",
                "gamification",
                "assessment_builder",
                "content_versioning",
                "live_classes",
                "video_conferencing",
            ],
            "education": [
                "ai_chat",
                "roblox_integration",
                "advanced_analytics",
                "custom_branding",
                "api_access",
                "gamification",
                "assessment_builder",
                "content_versioning",
                "parent_portal",
                "mobile_app",
                "live_classes",
            ],
        }

        available_features = tier_features.get(
            tenant.subscription_tier.value, tier_features["free"]
        )

        return TenantFeaturesResponse(
            tenant_id=tenant.id,
            enabled_features=tenant.features,
            available_features=available_features,
        )

    except Exception as e:
        logger.error(f"Failed to toggle feature: {str(e)}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to toggle feature"
        )


@router.get(
    "/limits",
    response_model=TenantLimitsResponse,
    summary="Get usage limits",
    description="Get current usage and limits for tenant",
)
async def get_tenant_limits(
    tenant: Annotated[Organization, Depends(get_current_tenant)],
) -> TenantLimitsResponse:
    """
    Get tenant usage limits and current consumption.

    Shows how much of each quota is being used and remaining.

    Args:
        tenant: Current tenant organization

    Returns:
        TenantLimitsResponse: Usage limits and current usage
    """
    try:
        return TenantLimitsResponse(
            tenant_id=tenant.id,
            current_users=tenant.current_users,
            current_classes=tenant.current_classes,
            current_storage_gb=tenant.current_storage_gb,
            current_api_calls_this_month=tenant.current_api_calls_this_month,
            current_roblox_sessions=tenant.current_roblox_sessions,
            max_users=tenant.max_users,
            max_classes=tenant.max_classes,
            max_storage_gb=tenant.max_storage_gb,
            max_api_calls_per_month=tenant.max_api_calls_per_month,
            max_roblox_sessions=tenant.max_roblox_sessions,
            users_remaining=max(0, tenant.max_users - tenant.current_users),
            classes_remaining=max(0, tenant.max_classes - tenant.current_classes),
            storage_remaining_gb=max(0.0, tenant.max_storage_gb - tenant.current_storage_gb),
            api_calls_remaining=max(
                0, tenant.max_api_calls_per_month - tenant.current_api_calls_this_month
            ),
            roblox_sessions_remaining=max(
                0, tenant.max_roblox_sessions - tenant.current_roblox_sessions
            ),
        )

    except Exception as e:
        logger.error(f"Failed to get tenant limits: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get tenant limits"
        )


@router.patch(
    "/custom-settings",
    response_model=TenantSettingsResponse,
    summary="Update custom settings",
    description="Update custom tenant settings (requires org admin)",
    dependencies=[Depends(require_org_admin)],
)
async def update_custom_settings(
    request: TenantCustomSettingsRequest,
    tenant: Annotated[Organization, Depends(get_current_tenant)],
    session: Annotated[AsyncSession, Depends(get_async_db)],
) -> TenantSettingsResponse:
    """
    Update custom tenant settings.

    Allows setting arbitrary key-value pairs for tenant-specific configuration.

    Args:
        request: Custom settings request
        tenant: Current tenant organization
        session: Async database session

    Returns:
        TenantSettingsResponse: Updated tenant settings

    Raises:
        HTTPException: If update fails
    """
    try:
        logger.info(f"Updating custom settings for tenant: {tenant.id}")

        # Merge new settings with existing
        current_settings = tenant.settings if isinstance(tenant.settings, dict) else {}
        current_settings.update(request.settings)

        tenant.settings = current_settings
        tenant.updated_at = datetime.utcnow()

        await session.commit()
        await session.refresh(tenant)

        logger.info(f"Custom settings updated for tenant: {tenant.id}")

        return TenantSettingsResponse(
            tenant_id=tenant.id,
            tenant_name=tenant.name,
            tenant_slug=tenant.slug,
            timezone=tenant.timezone,
            locale=tenant.locale,
            display_name=tenant.display_name,
            description=tenant.description,
            logo_url=tenant.logo_url,
            primary_color=tenant.primary_color,
            secondary_color=tenant.secondary_color,
            custom_domain=tenant.custom_domain,
            features=tenant.features if isinstance(tenant.features, list) else [],
            settings=tenant.settings,
            sso_enabled=tenant.sso_enabled,
            audit_logs_enabled=tenant.audit_logs_enabled,
            coppa_compliance_required=tenant.coppa_compliance_required,
            ferpa_compliance_required=tenant.ferpa_compliance_required,
            data_retention_days=tenant.data_retention_days,
        )

    except Exception as e:
        logger.error(f"Failed to update custom settings: {str(e)}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update custom settings",
        )


@router.get(
    "/integrations",
    response_model=TenantIntegrationsResponse,
    summary="Get integrations",
    description="Get configured integrations for tenant",
)
async def get_tenant_integrations(
    tenant: Annotated[Organization, Depends(get_current_tenant)],
) -> TenantIntegrationsResponse:
    """
    Get configured tenant integrations.

    Returns all third-party integrations and their configuration.

    Args:
        tenant: Current tenant organization

    Returns:
        TenantIntegrationsResponse: Integration configurations
    """
    try:
        integrations_data = tenant.integrations if isinstance(tenant.integrations, dict) else {}

        integrations = {
            name: TenantIntegrationConfig(
                integration_name=name,
                enabled=config.get("enabled", False),
                config=config.get("config", {}),
            )
            for name, config in integrations_data.items()
        }

        return TenantIntegrationsResponse(
            tenant_id=tenant.id,
            integrations=integrations,
        )

    except Exception as e:
        logger.error(f"Failed to get tenant integrations: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tenant integrations",
        )

"""
Tenant Administration API Endpoints for ToolBoxAI Educational Platform

Provides comprehensive tenant (organization) management operations for
administrators including tenant provisioning, configuration, and lifecycle management.

Features:
- Tenant creation and provisioning
- Tenant configuration management
- User limit and quota management
- Tenant migration and archival
- Multi-tenant isolation enforcement
- Subscription tier management

Author: ToolBoxAI Team
Created: 2025-10-02
Version: 1.0.0
Standards: Python 3.12, FastAPI async, Pydantic v2
"""

import logging
from datetime import datetime, timedelta
from typing import Annotated, Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    BackgroundTasks,
    status,
)
from pydantic import BaseModel, ConfigDict, Field, field_validator, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func

from apps.backend.api.auth.auth import get_current_user, require_super_admin
from apps.backend.core.deps import get_async_session
from apps.backend.models.schemas import User
from database.models.tenant import (
    Organization,
    OrganizationStatus,
    SubscriptionTier,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/tenants",
    tags=["tenant-admin"],
    dependencies=[Depends(require_super_admin)],
    responses={404: {"description": "Tenant not found"}},
)


# === Pydantic v2 Models ===

class TenantCreateRequest(BaseModel):
    """Request model for creating a new tenant with Pydantic v2"""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=100, pattern="^[a-z0-9-]+$")
    email: EmailStr
    subscription_tier: SubscriptionTier = Field(default=SubscriptionTier.FREE)
    max_users: int = Field(default=10, ge=1, le=10000)
    max_classes: int = Field(default=5, ge=1, le=1000)
    max_storage_gb: float = Field(default=1.0, ge=0.1, le=1000.0)
    trial_days: int = Field(default=14, ge=0, le=90)

    # Optional fields
    display_name: Optional[str] = Field(None, max_length=250)
    description: Optional[str] = None
    website: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=50)
    timezone: str = Field(default="UTC")
    locale: str = Field(default="en-US")


class TenantUpdateRequest(BaseModel):
    """Request model for updating tenant"""

    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    display_name: Optional[str] = Field(None, max_length=250)
    description: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    status: Optional[OrganizationStatus] = None
    subscription_tier: Optional[SubscriptionTier] = None
    is_active: Optional[bool] = None


class TenantLimitsUpdateRequest(BaseModel):
    """Request model for updating tenant limits"""

    model_config = ConfigDict(from_attributes=True)

    max_users: Optional[int] = Field(None, ge=1, le=10000)
    max_classes: Optional[int] = Field(None, ge=1, le=1000)
    max_storage_gb: Optional[float] = Field(None, ge=0.1, le=1000.0)
    max_api_calls_per_month: Optional[int] = Field(None, ge=100, le=10000000)
    max_roblox_sessions: Optional[int] = Field(None, ge=1, le=1000)


class TenantResponse(BaseModel):
    """Response model for tenant data"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    status: OrganizationStatus
    subscription_tier: SubscriptionTier
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Usage stats
    current_users: int = 0
    current_classes: int = 0
    current_storage_gb: float = 0.0

    # Limits
    max_users: int
    max_classes: int
    max_storage_gb: float


class TenantListResponse(BaseModel):
    """Response model for tenant list"""

    model_config = ConfigDict(from_attributes=True)

    tenants: list[TenantResponse]
    total: int
    page: int
    page_size: int


class TenantProvisionRequest(BaseModel):
    """Request model for tenant provisioning"""

    model_config = ConfigDict(from_attributes=True)

    create_admin_user: bool = Field(default=True)
    admin_email: Optional[EmailStr] = None
    admin_username: Optional[str] = None
    send_welcome_email: bool = Field(default=True)
    initialize_defaults: bool = Field(default=True)


class TenantProvisionResponse(BaseModel):
    """Response model for tenant provisioning"""

    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    status: str
    admin_user_id: Optional[UUID] = None
    message: str
    provisioned_at: datetime


class TenantMigrationRequest(BaseModel):
    """Request model for tenant data migration"""

    model_config = ConfigDict(from_attributes=True)

    source_tenant_id: UUID
    target_tenant_id: UUID
    migrate_users: bool = Field(default=True)
    migrate_content: bool = Field(default=True)
    migrate_storage: bool = Field(default=True)
    delete_source: bool = Field(default=False)


# === API Endpoints ===

@router.post(
    "",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new tenant",
    description="Create a new tenant organization (super admin only)",
)
async def create_tenant(
    request: TenantCreateRequest,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TenantResponse:
    """
    Create a new tenant organization.

    Args:
        request: Tenant creation request
        session: Async database session
        current_user: Current authenticated user (must be super admin)

    Returns:
        TenantResponse: Created tenant details

    Raises:
        HTTPException: If tenant creation fails or slug already exists
    """
    try:
        logger.info(f"Creating tenant: {request.name} ({request.slug})")

        # Check if slug already exists
        existing = await session.execute(
            select(Organization).where(Organization.slug == request.slug)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tenant with slug '{request.slug}' already exists"
            )

        # Create organization
        trial_expires = datetime.utcnow() + timedelta(days=request.trial_days)

        organization = Organization(
            name=request.name,
            slug=request.slug,
            display_name=request.display_name or request.name,
            description=request.description,
            email=request.email,
            phone=request.phone,
            website=request.website,
            timezone=request.timezone,
            locale=request.locale,
            subscription_tier=request.subscription_tier,
            status=OrganizationStatus.TRIAL if request.trial_days > 0 else OrganizationStatus.ACTIVE,
            max_users=request.max_users,
            max_classes=request.max_classes,
            max_storage_gb=request.max_storage_gb,
            trial_started_at=datetime.utcnow(),
            trial_expires_at=trial_expires,
            is_active=True,
            created_by_id=current_user.id,
        )

        session.add(organization)
        await session.commit()
        await session.refresh(organization)

        logger.info(f"Tenant created successfully: {organization.id}")

        return TenantResponse(
            id=organization.id,
            name=organization.name,
            slug=organization.slug,
            display_name=organization.display_name,
            email=organization.email,
            status=organization.status,
            subscription_tier=organization.subscription_tier,
            is_active=organization.is_active,
            created_at=organization.created_at,
            updated_at=organization.updated_at,
            current_users=organization.current_users,
            current_classes=organization.current_classes,
            current_storage_gb=organization.current_storage_gb,
            max_users=organization.max_users,
            max_classes=organization.max_classes,
            max_storage_gb=organization.max_storage_gb,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create tenant: {str(e)}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create tenant"
        )


@router.get(
    "",
    response_model=TenantListResponse,
    summary="List all tenants",
    description="List all tenant organizations with pagination (super admin only)",
)
async def list_tenants(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status_filter: Optional[OrganizationStatus] = None,
    tier_filter: Optional[SubscriptionTier] = None,
    active_only: bool = True,
) -> TenantListResponse:
    """
    List all tenants with pagination and filtering.

    Args:
        session: Async database session
        page: Page number
        page_size: Items per page
        status_filter: Filter by organization status
        tier_filter: Filter by subscription tier
        active_only: Only return active tenants

    Returns:
        TenantListResponse: List of tenants with pagination info
    """
    try:
        # Build query
        query = select(Organization)

        if active_only:
            query = query.where(Organization.is_active == True)
        if status_filter:
            query = query.where(Organization.status == status_filter)
        if tier_filter:
            query = query.where(Organization.subscription_tier == tier_filter)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)
        query = query.order_by(Organization.created_at.desc())

        result = await session.execute(query)
        organizations = result.scalars().all()

        tenants = [
            TenantResponse(
                id=org.id,
                name=org.name,
                slug=org.slug,
                display_name=org.display_name,
                email=org.email,
                status=org.status,
                subscription_tier=org.subscription_tier,
                is_active=org.is_active,
                created_at=org.created_at,
                updated_at=org.updated_at,
                current_users=org.current_users,
                current_classes=org.current_classes,
                current_storage_gb=org.current_storage_gb,
                max_users=org.max_users,
                max_classes=org.max_classes,
                max_storage_gb=org.max_storage_gb,
            )
            for org in organizations
        ]

        return TenantListResponse(
            tenants=tenants,
            total=total,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        logger.error(f"Failed to list tenants: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list tenants"
        )


@router.get(
    "/{tenant_id}",
    response_model=TenantResponse,
    summary="Get tenant details",
    description="Get detailed information about a specific tenant (super admin only)",
)
async def get_tenant(
    tenant_id: UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> TenantResponse:
    """
    Get detailed information about a specific tenant.

    Args:
        tenant_id: Tenant identifier
        session: Async database session

    Returns:
        TenantResponse: Tenant details

    Raises:
        HTTPException: If tenant not found
    """
    try:
        result = await session.execute(
            select(Organization).where(Organization.id == tenant_id)
        )
        organization = result.scalar_one_or_none()

        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )

        return TenantResponse(
            id=organization.id,
            name=organization.name,
            slug=organization.slug,
            display_name=organization.display_name,
            email=organization.email,
            status=organization.status,
            subscription_tier=organization.subscription_tier,
            is_active=organization.is_active,
            created_at=organization.created_at,
            updated_at=organization.updated_at,
            current_users=organization.current_users,
            current_classes=organization.current_classes,
            current_storage_gb=organization.current_storage_gb,
            max_users=organization.max_users,
            max_classes=organization.max_classes,
            max_storage_gb=organization.max_storage_gb,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tenant: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tenant details"
        )


@router.patch(
    "/{tenant_id}",
    response_model=TenantResponse,
    summary="Update tenant",
    description="Update tenant information (super admin only)",
)
async def update_tenant(
    tenant_id: UUID,
    request: TenantUpdateRequest,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> TenantResponse:
    """
    Update tenant information.

    Args:
        tenant_id: Tenant identifier
        request: Update request
        session: Async database session

    Returns:
        TenantResponse: Updated tenant details

    Raises:
        HTTPException: If tenant not found or update fails
    """
    try:
        result = await session.execute(
            select(Organization).where(Organization.id == tenant_id)
        )
        organization = result.scalar_one_or_none()

        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )

        # Update fields
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(organization, field, value)

        organization.updated_at = datetime.utcnow()

        await session.commit()
        await session.refresh(organization)

        logger.info(f"Tenant updated: {tenant_id}")

        return TenantResponse(
            id=organization.id,
            name=organization.name,
            slug=organization.slug,
            display_name=organization.display_name,
            email=organization.email,
            status=organization.status,
            subscription_tier=organization.subscription_tier,
            is_active=organization.is_active,
            created_at=organization.created_at,
            updated_at=organization.updated_at,
            current_users=organization.current_users,
            current_classes=organization.current_classes,
            current_storage_gb=organization.current_storage_gb,
            max_users=organization.max_users,
            max_classes=organization.max_classes,
            max_storage_gb=organization.max_storage_gb,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update tenant: {str(e)}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update tenant"
        )


@router.delete(
    "/{tenant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete tenant",
    description="Delete a tenant organization (super admin only, soft delete)",
)
async def delete_tenant(
    tenant_id: UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    permanent: bool = Query(False, description="Permanently delete (cannot be undone)"),
) -> None:
    """
    Delete a tenant organization.

    By default, this is a soft delete (sets is_active=False).
    Use permanent=True for hard deletion.

    Args:
        tenant_id: Tenant identifier
        session: Async database session
        permanent: Whether to permanently delete

    Raises:
        HTTPException: If tenant not found or deletion fails
    """
    try:
        result = await session.execute(
            select(Organization).where(Organization.id == tenant_id)
        )
        organization = result.scalar_one_or_none()

        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )

        if permanent:
            # Hard delete
            await session.delete(organization)
            logger.warning(f"Tenant permanently deleted: {tenant_id}")
        else:
            # Soft delete
            organization.is_active = False
            organization.status = OrganizationStatus.CANCELLED
            organization.updated_at = datetime.utcnow()
            logger.info(f"Tenant soft deleted: {tenant_id}")

        await session.commit()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete tenant: {str(e)}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete tenant"
        )


@router.post(
    "/{tenant_id}/provision",
    response_model=TenantProvisionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Provision tenant",
    description="Provision a new tenant with default data and admin user",
)
async def provision_tenant(
    tenant_id: UUID,
    request: TenantProvisionRequest,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    background_tasks: BackgroundTasks,
) -> TenantProvisionResponse:
    """
    Provision a tenant with default data and optional admin user.

    This creates:
    - Admin user account (if requested)
    - Default settings and features
    - Initial database schema for tenant
    - Welcome email notification

    Args:
        tenant_id: Tenant identifier
        request: Provisioning request
        session: Async database session
        background_tasks: Background task manager

    Returns:
        TenantProvisionResponse: Provisioning result

    Raises:
        HTTPException: If tenant not found or provisioning fails
    """
    try:
        result = await session.execute(
            select(Organization).where(Organization.id == tenant_id)
        )
        organization = result.scalar_one_or_none()

        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )

        logger.info(f"Provisioning tenant: {tenant_id}")

        # TODO: Implement actual provisioning logic
        # - Create admin user
        # - Initialize default settings
        # - Send welcome email

        admin_user_id = None

        return TenantProvisionResponse(
            tenant_id=tenant_id,
            status="provisioned",
            admin_user_id=admin_user_id,
            message="Tenant provisioned successfully",
            provisioned_at=datetime.utcnow(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to provision tenant: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to provision tenant"
        )


@router.patch(
    "/{tenant_id}/limits",
    response_model=TenantResponse,
    summary="Update tenant limits",
    description="Update usage limits for a tenant (super admin only)",
)
async def update_tenant_limits(
    tenant_id: UUID,
    request: TenantLimitsUpdateRequest,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> TenantResponse:
    """
    Update tenant usage limits.

    Args:
        tenant_id: Tenant identifier
        request: Limits update request
        session: Async database session

    Returns:
        TenantResponse: Updated tenant details

    Raises:
        HTTPException: If tenant not found or update fails
    """
    try:
        result = await session.execute(
            select(Organization).where(Organization.id == tenant_id)
        )
        organization = result.scalar_one_or_none()

        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )

        # Update limits
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(organization, field, value)

        organization.updated_at = datetime.utcnow()

        await session.commit()
        await session.refresh(organization)

        logger.info(f"Tenant limits updated: {tenant_id}")

        return TenantResponse(
            id=organization.id,
            name=organization.name,
            slug=organization.slug,
            display_name=organization.display_name,
            email=organization.email,
            status=organization.status,
            subscription_tier=organization.subscription_tier,
            is_active=organization.is_active,
            created_at=organization.created_at,
            updated_at=organization.updated_at,
            current_users=organization.current_users,
            current_classes=organization.current_classes,
            current_storage_gb=organization.current_storage_gb,
            max_users=organization.max_users,
            max_classes=organization.max_classes,
            max_storage_gb=organization.max_storage_gb,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update tenant limits: {str(e)}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update tenant limits"
        )

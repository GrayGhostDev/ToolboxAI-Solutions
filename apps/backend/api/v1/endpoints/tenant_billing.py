"""
Tenant Billing API Endpoints for ToolBoxAI Educational Platform

Provides billing, subscription, and usage tracking endpoints for tenants.

Features:
- Current usage tracking
- Invoice management
- Subscription management
- Usage history and reports
- Payment method management
- Billing alerts

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
    status,
)
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.api.auth.auth import get_current_user
from apps.backend.core.deps import get_async_db
from apps.backend.middleware.tenant import get_tenant_context, TenantContext
from apps.backend.models.schemas import User
from database.models.tenant import Organization, SubscriptionTier

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/tenant/billing",
    tags=["tenant-billing"],
    responses={404: {"description": "Billing information not found"}},
)


# === Pydantic v2 Models ===

class UsageMetrics(BaseModel):
    """Current usage metrics with Pydantic v2"""

    model_config = ConfigDict(from_attributes=True)

    users: int = 0
    classes: int = 0
    storage_gb: float = 0.0
    api_calls: int = 0
    roblox_sessions: int = 0


class UsageLimits(BaseModel):
    """Usage limits"""

    model_config = ConfigDict(from_attributes=True)

    max_users: int
    max_classes: int
    max_storage_gb: float
    max_api_calls_per_month: int
    max_roblox_sessions: int


class BillingUsageResponse(BaseModel):
    """Response model for current billing usage"""

    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    tenant_name: str
    billing_period_start: datetime
    billing_period_end: datetime
    current_usage: UsageMetrics
    limits: UsageLimits
    subscription_tier: SubscriptionTier

    # Calculated fields
    usage_percentage: dict[str, float] = Field(default_factory=dict)
    over_limit: bool = False
    warnings: list[str] = Field(default_factory=list)


class Invoice(BaseModel):
    """Invoice model"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invoice_number: str
    amount: float
    currency: str = "USD"
    status: str
    issued_date: datetime
    due_date: datetime
    paid_date: Optional[datetime] = None
    description: str
    line_items: list[dict[str, str | float | int]] = Field(default_factory=list)


class InvoiceListResponse(BaseModel):
    """Response model for invoice list"""

    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    invoices: list[Invoice]
    total: int
    page: int
    page_size: int


class SubscriptionInfo(BaseModel):
    """Subscription information"""

    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    subscription_tier: SubscriptionTier
    status: str
    started_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    trial_started_at: Optional[datetime] = None
    trial_expires_at: Optional[datetime] = None
    auto_renew: bool = True
    next_billing_date: Optional[datetime] = None
    is_trial: bool = False
    days_remaining: Optional[int] = None


class SubscriptionUpdateRequest(BaseModel):
    """Request model for subscription update"""

    model_config = ConfigDict(from_attributes=True)

    subscription_tier: SubscriptionTier
    auto_renew: Optional[bool] = None


class SubscriptionUpdateResponse(BaseModel):
    """Response model for subscription update"""

    model_config = ConfigDict(from_attributes=True)

    subscription: SubscriptionInfo
    message: str
    effective_date: datetime


class UsageHistoryEntry(BaseModel):
    """Historical usage entry"""

    model_config = ConfigDict(from_attributes=True)

    date: datetime
    users: int
    classes: int
    storage_gb: float
    api_calls: int
    roblox_sessions: int


class UsageHistoryResponse(BaseModel):
    """Response model for usage history"""

    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    start_date: datetime
    end_date: datetime
    entries: list[UsageHistoryEntry]


class PaymentMethod(BaseModel):
    """Payment method information"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: str  # "card", "bank_account", "paypal"
    last_four: str
    brand: Optional[str] = None
    expiry_month: Optional[int] = None
    expiry_year: Optional[int] = None
    is_default: bool = False


class PaymentMethodsResponse(BaseModel):
    """Response model for payment methods"""

    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    payment_methods: list[PaymentMethod]


# === Dependency Injection ===

async def get_current_tenant_org(
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    session: Annotated[AsyncSession, Depends(get_async_db)],
) -> Organization:
    """Get current tenant organization"""
    from sqlalchemy import select

    if not tenant_context.effective_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No tenant context available"
        )

    result = await session.execute(
        select(Organization).where(Organization.id == tenant_context.effective_tenant_id)
    )
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    return organization


# === API Endpoints ===

@router.get(
    "/usage",
    response_model=BillingUsageResponse,
    summary="Get current usage",
    description="Get current billing period usage and limits",
)
async def get_current_usage(
    tenant: Annotated[Organization, Depends(get_current_tenant_org)],
) -> BillingUsageResponse:
    """
    Get current billing usage for tenant.

    Shows current usage vs limits for the billing period.

    Args:
        tenant: Current tenant organization

    Returns:
        BillingUsageResponse: Current usage details
    """
    try:
        # Calculate billing period (typically start of month)
        now = datetime.utcnow()
        billing_start = datetime(now.year, now.month, 1)
        if now.month == 12:
            billing_end = datetime(now.year + 1, 1, 1) - timedelta(seconds=1)
        else:
            billing_end = datetime(now.year, now.month + 1, 1) - timedelta(seconds=1)

        current_usage = UsageMetrics(
            users=tenant.current_users,
            classes=tenant.current_classes,
            storage_gb=tenant.current_storage_gb,
            api_calls=tenant.current_api_calls_this_month,
            roblox_sessions=tenant.current_roblox_sessions,
        )

        limits = UsageLimits(
            max_users=tenant.max_users,
            max_classes=tenant.max_classes,
            max_storage_gb=tenant.max_storage_gb,
            max_api_calls_per_month=tenant.max_api_calls_per_month,
            max_roblox_sessions=tenant.max_roblox_sessions,
        )

        # Calculate usage percentages
        usage_percentage = {
            "users": (tenant.current_users / tenant.max_users * 100) if tenant.max_users > 0 else 0,
            "classes": (tenant.current_classes / tenant.max_classes * 100) if tenant.max_classes > 0 else 0,
            "storage": (tenant.current_storage_gb / tenant.max_storage_gb * 100) if tenant.max_storage_gb > 0 else 0,
            "api_calls": (tenant.current_api_calls_this_month / tenant.max_api_calls_per_month * 100) if tenant.max_api_calls_per_month > 0 else 0,
            "roblox_sessions": (tenant.current_roblox_sessions / tenant.max_roblox_sessions * 100) if tenant.max_roblox_sessions > 0 else 0,
        }

        # Check for overages and warnings
        warnings = []
        over_limit = False

        for key, percentage in usage_percentage.items():
            if percentage >= 100:
                over_limit = True
                warnings.append(f"{key.replace('_', ' ').title()} limit exceeded")
            elif percentage >= 80:
                warnings.append(f"{key.replace('_', ' ').title()} usage at {percentage:.0f}%")

        return BillingUsageResponse(
            tenant_id=tenant.id,
            tenant_name=tenant.name,
            billing_period_start=billing_start,
            billing_period_end=billing_end,
            current_usage=current_usage,
            limits=limits,
            subscription_tier=tenant.subscription_tier,
            usage_percentage=usage_percentage,
            over_limit=over_limit,
            warnings=warnings,
        )

    except Exception as e:
        logger.error(f"Failed to get billing usage: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get billing usage"
        )


@router.get(
    "/invoices",
    response_model=InvoiceListResponse,
    summary="List invoices",
    description="Get list of invoices for tenant",
)
async def list_invoices(
    tenant: Annotated[Organization, Depends(get_current_tenant_org)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, pattern="^(paid|unpaid|overdue|pending)$"),
) -> InvoiceListResponse:
    """
    List invoices for tenant.

    Args:
        tenant: Current tenant organization
        page: Page number
        page_size: Items per page
        status_filter: Filter by invoice status

    Returns:
        InvoiceListResponse: List of invoices
    """
    try:
        logger.info(f"Listing invoices for tenant: {tenant.id}")

        # TODO: Implement actual invoice retrieval from database
        # For now, return empty list
        invoices: list[Invoice] = []

        return InvoiceListResponse(
            tenant_id=tenant.id,
            invoices=invoices,
            total=0,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        logger.error(f"Failed to list invoices: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list invoices"
        )


@router.get(
    "/subscription",
    response_model=SubscriptionInfo,
    summary="Get subscription",
    description="Get current subscription information",
)
async def get_subscription(
    tenant: Annotated[Organization, Depends(get_current_tenant_org)],
) -> SubscriptionInfo:
    """
    Get current subscription information.

    Args:
        tenant: Current tenant organization

    Returns:
        SubscriptionInfo: Subscription details
    """
    try:
        # Check if in trial
        is_trial = (
            tenant.trial_expires_at is not None and
            tenant.trial_expires_at > datetime.utcnow()
        )

        days_remaining = None
        if is_trial and tenant.trial_expires_at:
            days_remaining = (tenant.trial_expires_at - datetime.utcnow()).days

        return SubscriptionInfo(
            tenant_id=tenant.id,
            subscription_tier=tenant.subscription_tier,
            status=tenant.status.value,
            started_at=tenant.subscription_started_at,
            expires_at=tenant.subscription_expires_at,
            trial_started_at=tenant.trial_started_at,
            trial_expires_at=tenant.trial_expires_at,
            auto_renew=True,  # TODO: Get from database
            next_billing_date=tenant.next_billing_date,
            is_trial=is_trial,
            days_remaining=days_remaining,
        )

    except Exception as e:
        logger.error(f"Failed to get subscription: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get subscription"
        )


@router.post(
    "/subscription",
    response_model=SubscriptionUpdateResponse,
    summary="Update subscription",
    description="Update subscription tier (requires org admin)",
)
async def update_subscription(
    request: SubscriptionUpdateRequest,
    tenant: Annotated[Organization, Depends(get_current_tenant_org)],
    session: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> SubscriptionUpdateResponse:
    """
    Update subscription tier.

    Changes take effect immediately.

    Args:
        request: Subscription update request
        tenant: Current tenant organization
        session: Async database session
        current_user: Current authenticated user

    Returns:
        SubscriptionUpdateResponse: Update confirmation

    Raises:
        HTTPException: If update fails
    """
    try:
        logger.info(
            f"Updating subscription for tenant {tenant.id} "
            f"from {tenant.subscription_tier} to {request.subscription_tier}"
        )

        old_tier = tenant.subscription_tier
        tenant.subscription_tier = request.subscription_tier

        # Update subscription dates
        now = datetime.utcnow()
        if not tenant.subscription_started_at:
            tenant.subscription_started_at = now

        # Set expiration to 1 month from now
        tenant.subscription_expires_at = now + timedelta(days=30)
        tenant.next_billing_date = now + timedelta(days=30)

        # Update limits based on tier
        tier_limits = {
            SubscriptionTier.FREE: {
                "max_users": 10,
                "max_classes": 5,
                "max_storage_gb": 1.0,
                "max_api_calls_per_month": 1000,
                "max_roblox_sessions": 5,
            },
            SubscriptionTier.BASIC: {
                "max_users": 50,
                "max_classes": 20,
                "max_storage_gb": 10.0,
                "max_api_calls_per_month": 10000,
                "max_roblox_sessions": 25,
            },
            SubscriptionTier.PROFESSIONAL: {
                "max_users": 200,
                "max_classes": 100,
                "max_storage_gb": 50.0,
                "max_api_calls_per_month": 100000,
                "max_roblox_sessions": 100,
            },
            SubscriptionTier.ENTERPRISE: {
                "max_users": 10000,
                "max_classes": 1000,
                "max_storage_gb": 1000.0,
                "max_api_calls_per_month": 1000000,
                "max_roblox_sessions": 1000,
            },
            SubscriptionTier.EDUCATION: {
                "max_users": 500,
                "max_classes": 200,
                "max_storage_gb": 100.0,
                "max_api_calls_per_month": 500000,
                "max_roblox_sessions": 200,
            },
        }

        limits = tier_limits.get(request.subscription_tier, tier_limits[SubscriptionTier.FREE])
        for key, value in limits.items():
            setattr(tenant, key, value)

        tenant.updated_at = now

        await session.commit()
        await session.refresh(tenant)

        logger.info(f"Subscription updated successfully for tenant: {tenant.id}")

        subscription_info = SubscriptionInfo(
            tenant_id=tenant.id,
            subscription_tier=tenant.subscription_tier,
            status=tenant.status.value,
            started_at=tenant.subscription_started_at,
            expires_at=tenant.subscription_expires_at,
            trial_started_at=tenant.trial_started_at,
            trial_expires_at=tenant.trial_expires_at,
            auto_renew=True,
            next_billing_date=tenant.next_billing_date,
            is_trial=False,
        )

        return SubscriptionUpdateResponse(
            subscription=subscription_info,
            message=f"Subscription upgraded from {old_tier.value} to {request.subscription_tier.value}",
            effective_date=now,
        )

    except Exception as e:
        logger.error(f"Failed to update subscription: {str(e)}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update subscription"
        )


@router.get(
    "/usage/history",
    response_model=UsageHistoryResponse,
    summary="Get usage history",
    description="Get historical usage data for tenant",
)
async def get_usage_history(
    tenant: Annotated[Organization, Depends(get_current_tenant_org)],
    days: int = Query(30, ge=1, le=365, description="Number of days of history"),
) -> UsageHistoryResponse:
    """
    Get historical usage data.

    Args:
        tenant: Current tenant organization
        days: Number of days of history to retrieve

    Returns:
        UsageHistoryResponse: Historical usage data
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        logger.info(f"Getting usage history for tenant {tenant.id}: {days} days")

        # TODO: Implement actual historical data retrieval
        # For now, return empty list
        entries: list[UsageHistoryEntry] = []

        return UsageHistoryResponse(
            tenant_id=tenant.id,
            start_date=start_date,
            end_date=end_date,
            entries=entries,
        )

    except Exception as e:
        logger.error(f"Failed to get usage history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get usage history"
        )


@router.get(
    "/payment-methods",
    response_model=PaymentMethodsResponse,
    summary="Get payment methods",
    description="Get saved payment methods for tenant",
)
async def get_payment_methods(
    tenant: Annotated[Organization, Depends(get_current_tenant_org)],
) -> PaymentMethodsResponse:
    """
    Get saved payment methods.

    Args:
        tenant: Current tenant organization

    Returns:
        PaymentMethodsResponse: List of payment methods
    """
    try:
        logger.info(f"Getting payment methods for tenant: {tenant.id}")

        # TODO: Implement actual payment method retrieval
        # For now, return empty list
        payment_methods: list[PaymentMethod] = []

        return PaymentMethodsResponse(
            tenant_id=tenant.id,
            payment_methods=payment_methods,
        )

    except Exception as e:
        logger.error(f"Failed to get payment methods: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get payment methods"
        )

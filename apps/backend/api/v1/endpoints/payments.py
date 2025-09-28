"""
Payment API Endpoints
Handles all payment-related API endpoints including subscriptions, checkout, and webhooks
@module payments
@version 1.0.0
@since 2025-09-26
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Header, status, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
import stripe

from apps.backend.services.stripe_service import stripe_service
from apps.backend.core.auth import get_current_user, require_auth
from apps.backend.core.config import settings
from apps.backend.core.rate_limiter import rate_limit
from database.connection import get_session
from database.models.payment import Customer, Subscription, Payment, Invoice
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["payments"])


# Request/Response Models
class CreateCustomerRequest(BaseModel):
    """Request model for creating a customer"""

    email: str = Field(..., description="Customer email")
    name: Optional[str] = Field(None, description="Customer name")
    phone: Optional[str] = Field(None, description="Customer phone")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class CreateSubscriptionRequest(BaseModel):
    """Request model for creating a subscription"""

    price_id: str = Field(..., description="Stripe price ID")
    trial_days: int = Field(14, ge=0, le=30, description="Trial period in days")
    payment_method_id: Optional[str] = Field(None, description="Payment method ID")
    coupon: Optional[str] = Field(None, description="Coupon code")


class UpdateSubscriptionRequest(BaseModel):
    """Request model for updating a subscription"""

    price_id: Optional[str] = Field(None, description="New price ID for upgrade/downgrade")
    quantity: Optional[int] = Field(None, ge=1, description="Subscription quantity")
    cancel_at_period_end: Optional[bool] = Field(None, description="Cancel at period end")


class CreatePaymentIntentRequest(BaseModel):
    """Request model for creating a payment intent"""

    amount: int = Field(..., ge=50, description="Amount in cents (minimum 50)")
    currency: str = Field("usd", description="Currency code")
    description: Optional[str] = Field(None, description="Payment description")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AttachPaymentMethodRequest(BaseModel):
    """Request model for attaching a payment method"""

    payment_method_id: str = Field(..., description="Stripe payment method ID")
    set_as_default: bool = Field(True, description="Set as default payment method")


class CreateCheckoutSessionRequest(BaseModel):
    """Request model for creating a checkout session"""

    price_id: Optional[str] = Field(None, description="Price ID for subscriptions")
    mode: str = Field("payment", description="Checkout mode: payment or subscription")
    success_url: Optional[str] = Field(None, description="Success redirect URL")
    cancel_url: Optional[str] = Field(None, description="Cancel redirect URL")
    line_items: Optional[List[Dict[str, Any]]] = Field(None, description="Custom line items")
    trial_days: Optional[int] = Field(
        None, ge=0, le=30, description="Trial period for subscriptions"
    )


class CreateRefundRequest(BaseModel):
    """Request model for creating a refund"""

    payment_id: Optional[str] = Field(None, description="Payment ID to refund")
    charge_id: Optional[str] = Field(None, description="Charge ID to refund")
    amount: Optional[int] = Field(None, ge=1, description="Amount to refund in cents")
    reason: str = Field("requested_by_customer", description="Refund reason")

    @validator("payment_id")
    def validate_ids(cls, v, values):
        if not v and not values.get("charge_id"):
            raise ValueError("Either payment_id or charge_id must be provided")
        return v


# Customer Endpoints
@router.post("/customers", response_model=Dict[str, Any])
@rate_limit(max_calls=10, time_window=60)
async def create_customer(
    request: CreateCustomerRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Create a new Stripe customer for the current user
    """
    try:
        # Check if customer already exists
        result = await db.execute(select(Customer).filter(Customer.user_id == current_user.id))
        existing_customer = result.scalar_one_or_none()

        if existing_customer and existing_customer.stripe_customer_id:
            return {
                "message": "Customer already exists",
                "customer_id": existing_customer.stripe_customer_id,
            }

        # Create Stripe customer
        stripe_customer = await stripe_service.create_customer(
            user_id=str(current_user.id),
            email=request.email or current_user.email,
            name=request.name or current_user.full_name,
            metadata={
                **request.metadata,
                "user_id": str(current_user.id),
                "username": current_user.username,
            },
        )

        # Save to database
        if existing_customer:
            existing_customer.stripe_customer_id = stripe_customer["id"]
            existing_customer.email = request.email or current_user.email
            existing_customer.name = request.name or current_user.full_name
        else:
            customer = Customer(
                user_id=current_user.id,
                stripe_customer_id=stripe_customer["id"],
                email=request.email or current_user.email,
                name=request.name or current_user.full_name,
                metadata=request.metadata,
            )
            db.add(customer)

        await db.commit()

        return {
            "message": "Customer created successfully",
            "customer_id": stripe_customer["id"],
            "customer": stripe_customer,
        }

    except Exception as e:
        logger.error(f"Error creating customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customers/me", response_model=Dict[str, Any])
async def get_my_customer(
    current_user=Depends(get_current_user), db: AsyncSession = Depends(get_session)
):
    """
    Get the current user's customer information
    """
    try:
        result = await db.execute(select(Customer).filter(Customer.user_id == current_user.id))
        customer = result.scalar_one_or_none()

        if not customer or not customer.stripe_customer_id:
            raise HTTPException(status_code=404, detail="Customer not found")

        stripe_customer = await stripe_service.get_customer(customer.stripe_customer_id)

        return {
            "customer": stripe_customer,
            "subscription_status": (
                customer.subscriptions[0].status if customer.subscriptions else None
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Subscription Endpoints
@router.post("/subscriptions", response_model=Dict[str, Any])
@rate_limit(max_calls=5, time_window=60)
async def create_subscription(
    request: CreateSubscriptionRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Create a new subscription for the current user
    """
    try:
        # Get customer
        result = await db.execute(select(Customer).filter(Customer.user_id == current_user.id))
        customer = result.scalar_one_or_none()

        if not customer or not customer.stripe_customer_id:
            raise HTTPException(status_code=400, detail="Please create a customer account first")

        # Attach payment method if provided
        if request.payment_method_id:
            await stripe_service.attach_payment_method(
                payment_method_id=request.payment_method_id,
                customer_id=customer.stripe_customer_id,
                set_as_default=True,
            )

        # Create subscription
        subscription = await stripe_service.create_subscription(
            customer_id=customer.stripe_customer_id,
            price_id=request.price_id,
            trial_days=request.trial_days,
            coupon=request.coupon,
            metadata={"user_id": str(current_user.id), "created_via": "api"},
        )

        # Save to database
        db_subscription = Subscription(
            customer_id=customer.id,
            stripe_subscription_id=subscription["subscription_id"],
            status=subscription["status"],
            price_id=request.price_id,
            current_period_start=datetime.fromtimestamp(subscription["current_period_start"]),
            current_period_end=datetime.fromtimestamp(subscription["current_period_end"]),
            trial_end=(
                datetime.fromtimestamp(subscription["trial_end"])
                if subscription.get("trial_end")
                else None
            ),
            metadata={"stripe_response": subscription},
        )
        db.add(db_subscription)
        await db.commit()

        return {"message": "Subscription created successfully", "subscription": subscription}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subscriptions", response_model=Dict[str, Any])
async def get_my_subscriptions(
    current_user=Depends(get_current_user), db: AsyncSession = Depends(get_session)
):
    """
    Get all subscriptions for the current user
    """
    try:
        result = await db.execute(select(Customer).filter(Customer.user_id == current_user.id))
        customer = result.scalar_one_or_none()

        if not customer:
            return {"subscriptions": []}

        # Get subscriptions from database
        result = await db.execute(
            select(Subscription)
            .filter(Subscription.customer_id == customer.id)
            .order_by(Subscription.created_at.desc())
        )
        subscriptions = result.scalars().all()

        return {
            "subscriptions": [
                {
                    "id": sub.stripe_subscription_id,
                    "status": sub.status,
                    "tier": sub.tier,
                    "current_period_start": (
                        sub.current_period_start.isoformat() if sub.current_period_start else None
                    ),
                    "current_period_end": (
                        sub.current_period_end.isoformat() if sub.current_period_end else None
                    ),
                    "cancel_at_period_end": sub.cancel_at_period_end,
                    "trial_end": sub.trial_end.isoformat() if sub.trial_end else None,
                }
                for sub in subscriptions
            ]
        }

    except Exception as e:
        logger.error(f"Error getting subscriptions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/subscriptions/{subscription_id}", response_model=Dict[str, Any])
@rate_limit(max_calls=5, time_window=60)
async def update_subscription(
    subscription_id: str,
    request: UpdateSubscriptionRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Update a subscription (upgrade/downgrade/cancel)
    """
    try:
        # Verify ownership
        result = await db.execute(
            select(Subscription)
            .join(Customer)
            .filter(
                Subscription.stripe_subscription_id == subscription_id,
                Customer.user_id == current_user.id,
            )
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")

        # Handle cancellation
        if request.cancel_at_period_end is not None:
            if request.cancel_at_period_end:
                updated = await stripe_service.cancel_subscription(
                    subscription_id=subscription_id,
                    immediately=False,
                    reason="User requested cancellation",
                )
                subscription.cancel_at_period_end = True
            else:
                # Reactivate subscription
                updated = await stripe_service.update_subscription(subscription_id=subscription_id)
                subscription.cancel_at_period_end = False
        else:
            # Update subscription
            updated = await stripe_service.update_subscription(
                subscription_id=subscription_id,
                price_id=request.price_id,
                quantity=request.quantity,
            )

        await db.commit()

        return {"message": "Subscription updated successfully", "subscription": updated}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/subscriptions/{subscription_id}", response_model=Dict[str, Any])
@rate_limit(max_calls=5, time_window=60)
async def cancel_subscription(
    subscription_id: str,
    immediately: bool = False,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Cancel a subscription
    """
    try:
        # Verify ownership
        result = await db.execute(
            select(Subscription)
            .join(Customer)
            .filter(
                Subscription.stripe_subscription_id == subscription_id,
                Customer.user_id == current_user.id,
            )
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")

        # Cancel subscription
        cancelled = await stripe_service.cancel_subscription(
            subscription_id=subscription_id,
            immediately=immediately,
            reason="User requested cancellation via API",
        )

        # Update database
        subscription.status = "canceled" if immediately else subscription.status
        subscription.cancel_at_period_end = not immediately
        subscription.canceled_at = datetime.now()
        subscription.cancellation_reason = "User requested"

        await db.commit()

        return {"message": "Subscription cancelled successfully", "subscription": cancelled}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Payment Method Endpoints
@router.post("/payment-methods", response_model=Dict[str, Any])
@rate_limit(max_calls=10, time_window=60)
async def attach_payment_method(
    request: AttachPaymentMethodRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Attach a payment method to the current user
    """
    try:
        # Get customer
        result = await db.execute(select(Customer).filter(Customer.user_id == current_user.id))
        customer = result.scalar_one_or_none()

        if not customer or not customer.stripe_customer_id:
            raise HTTPException(status_code=400, detail="Please create a customer account first")

        # Attach payment method
        payment_method = await stripe_service.attach_payment_method(
            payment_method_id=request.payment_method_id,
            customer_id=customer.stripe_customer_id,
            set_as_default=request.set_as_default,
        )

        return {"message": "Payment method attached successfully", "payment_method": payment_method}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error attaching payment method: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payment-methods", response_model=Dict[str, Any])
async def get_payment_methods(
    current_user=Depends(get_current_user), db: AsyncSession = Depends(get_session)
):
    """
    Get all payment methods for the current user
    """
    try:
        # Get customer
        result = await db.execute(select(Customer).filter(Customer.user_id == current_user.id))
        customer = result.scalar_one_or_none()

        if not customer or not customer.stripe_customer_id:
            return {"payment_methods": []}

        # Get payment methods from Stripe
        payment_methods = await stripe_service.list_payment_methods(
            customer_id=customer.stripe_customer_id
        )

        return {"payment_methods": payment_methods}

    except Exception as e:
        logger.error(f"Error getting payment methods: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# One-time Payment Endpoints
@router.post("/payment-intents", response_model=Dict[str, Any])
@rate_limit(max_calls=10, time_window=60)
async def create_payment_intent(
    request: CreatePaymentIntentRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Create a payment intent for one-time payment
    """
    try:
        # Get customer if exists
        result = await db.execute(select(Customer).filter(Customer.user_id == current_user.id))
        customer = result.scalar_one_or_none()

        # Create payment intent
        payment_intent = await stripe_service.create_payment_intent(
            amount=request.amount,
            currency=request.currency,
            customer_id=customer.stripe_customer_id if customer else None,
            description=request.description,
            metadata={**request.metadata, "user_id": str(current_user.id)},
        )

        return {"message": "Payment intent created", "payment_intent": payment_intent}

    except Exception as e:
        logger.error(f"Error creating payment intent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Checkout Session Endpoints
@router.post("/checkout/sessions", response_model=Dict[str, Any])
@rate_limit(max_calls=5, time_window=60)
async def create_checkout_session(
    request: CreateCheckoutSessionRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Create a Stripe Checkout session
    """
    try:
        # Get customer if exists
        result = await db.execute(select(Customer).filter(Customer.user_id == current_user.id))
        customer = result.scalar_one_or_none()

        # Create checkout session
        session = await stripe_service.create_checkout_session(
            customer_id=customer.stripe_customer_id if customer else None,
            price_id=request.price_id,
            line_items=request.line_items,
            mode=request.mode,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            trial_period_days=request.trial_days,
            metadata={"user_id": str(current_user.id), "username": current_user.username},
        )

        return {
            "message": "Checkout session created",
            "checkout_url": session["url"],
            "session_id": session["id"],
        }

    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Webhook Endpoint
@router.post("/webhooks/stripe", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_session),
):
    """
    Handle Stripe webhook events
    """
    try:
        # Get raw body
        payload = await request.body()

        # Handle webhook
        success, result = await stripe_service.handle_webhook(
            payload=payload, signature=stripe_signature
        )

        if not success:
            logger.error(f"Webhook validation failed: {result}")
            raise HTTPException(status_code=400, detail=result.get("error"))

        # Process webhook in background
        # background_tasks.add_task(process_webhook_event, result, db)

        return JSONResponse(status_code=200, content={"status": "success", "result": result})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        # Return 200 to prevent retries for unexpected errors
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


# Invoice Endpoints
@router.get("/invoices", response_model=Dict[str, Any])
async def get_invoices(
    limit: int = 10, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_session)
):
    """
    Get invoices for the current user
    """
    try:
        # Get customer
        result = await db.execute(select(Customer).filter(Customer.user_id == current_user.id))
        customer = result.scalar_one_or_none()

        if not customer or not customer.stripe_customer_id:
            return {"invoices": []}

        # Get invoices from Stripe
        invoices = await stripe_service.get_invoices(
            customer_id=customer.stripe_customer_id, limit=limit
        )

        return {"invoices": invoices}

    except Exception as e:
        logger.error(f"Error getting invoices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Refund Endpoints
@router.post("/refunds", response_model=Dict[str, Any])
@rate_limit(max_calls=5, time_window=60)
async def create_refund(
    request: CreateRefundRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Create a refund for a payment (admin only)
    """
    # Check admin privileges
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        refund = await stripe_service.create_refund(
            charge_id=request.charge_id,
            payment_intent_id=request.payment_id,
            amount=request.amount,
            reason=request.reason,
            metadata={
                "refunded_by": str(current_user.id),
                "refunded_at": datetime.now().isoformat(),
            },
        )

        return {"message": "Refund created successfully", "refund": refund}

    except Exception as e:
        logger.error(f"Error creating refund: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Revenue Analytics Endpoints (Admin only)
@router.get("/analytics/revenue", response_model=Dict[str, Any])
async def get_revenue_analytics(
    start_date: datetime, end_date: datetime, current_user=Depends(get_current_user)
):
    """
    Get revenue analytics (admin only)
    """
    # Check admin privileges
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        metrics = await stripe_service.get_revenue_metrics(start_date=start_date, end_date=end_date)

        return {
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "metrics": metrics,
        }

    except Exception as e:
        logger.error(f"Error getting revenue analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

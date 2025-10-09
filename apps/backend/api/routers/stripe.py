"""
Stripe Payment Router

Handles Stripe checkout sessions, subscriptions, and webhook events.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from apps.backend.core.logging import logging_manager, log_audit
from apps.backend.core.config import settings
from apps.backend.models.schemas import User
from apps.backend.api.auth.auth import get_current_user
from apps.backend.services.stripe_service import StripeService

logger = logging_manager.get_logger(__name__)
router = APIRouter(tags=["Payments"])

# Initialize Stripe service
stripe_service = StripeService()


# Request/Response Models
class CheckoutSessionRequest(BaseModel):
    """Request model for creating a Stripe Checkout session"""

    price_id: Optional[str] = Field(None, description="Stripe Price ID for subscription")
    line_items: Optional[List[Dict[str, Any]]] = Field(None, description="Line items for one-time payments")
    mode: str = Field("payment", description="Checkout mode: payment, subscription, or setup")
    success_url: Optional[str] = Field(None, description="URL to redirect after successful payment")
    cancel_url: Optional[str] = Field(None, description="URL to redirect after cancellation")
    metadata: Optional[Dict[str, str]] = Field(None, description="Additional metadata")


class SubscriptionRequest(BaseModel):
    """Request model for creating a subscription"""

    price_id: str = Field(..., description="Stripe Price ID")
    trial_days: int = Field(14, description="Number of trial days")
    payment_method_id: Optional[str] = Field(None, description="Payment method ID")
    metadata: Optional[Dict[str, str]] = Field(None, description="Additional metadata")


class SubscriptionUpdateRequest(BaseModel):
    """Request model for updating a subscription"""

    price_id: Optional[str] = Field(None, description="New price ID")
    cancel_at_period_end: Optional[bool] = Field(None, description="Cancel at period end")
    metadata: Optional[Dict[str, str]] = Field(None, description="Additional metadata")


@router.post("/stripe/checkout")
async def create_checkout_session(
    request: CheckoutSessionRequest,
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """
    Create a Stripe Checkout session for payment or subscription

    Args:
        request: Checkout session parameters
        current_user: Authenticated user

    Returns:
        JSONResponse: Checkout session data including URL
    """
    try:
        # Get or create Stripe customer
        customer = await stripe_service.create_customer(
            user_id=str(current_user.id),
            email=current_user.email,
            name=getattr(current_user, "name", None),
            metadata={"user_id": str(current_user.id), "role": getattr(current_user, "role", "student")},
        )

        # Set success and cancel URLs with defaults
        success_url = request.success_url or f"{settings.FRONTEND_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = request.cancel_url or f"{settings.FRONTEND_URL}/billing/cancel"

        # Create checkout session
        session = await stripe_service.create_checkout_session(
            customer_id=customer["id"],
            price_id=request.price_id,
            line_items=request.line_items,
            mode=request.mode,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=request.metadata or {},
        )

        # Log checkout session creation
        log_audit(
            action="stripe_checkout_created",
            user_id=current_user.id,
            resource_type="checkout_session",
            resource_id=session["id"],
            details={
                "mode": request.mode,
                "price_id": request.price_id,
                "amount": session.get("amount_total"),
            },
        )

        return JSONResponse(
            content={
                "status": "success",
                "data": {
                    "session_id": session["id"],
                    "url": session["url"],
                    "customer_id": customer["id"],
                },
                "message": "Checkout session created successfully",
            }
        )

    except Exception as e:
        logger.error(f"Failed to create checkout session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create checkout session: {str(e)}")


@router.post("/stripe/subscriptions")
async def create_subscription(
    request: SubscriptionRequest,
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """
    Create a new Stripe subscription for the current user

    Args:
        request: Subscription parameters
        current_user: Authenticated user

    Returns:
        JSONResponse: Subscription data
    """
    try:
        # Get or create Stripe customer
        customer = await stripe_service.create_customer(
            user_id=str(current_user.id),
            email=current_user.email,
            name=getattr(current_user, "name", None),
            payment_method_id=request.payment_method_id,
        )

        # Create subscription
        subscription = await stripe_service.create_subscription(
            customer_id=customer["id"],
            price_id=request.price_id,
            trial_days=request.trial_days,
            metadata=request.metadata or {"user_id": str(current_user.id)},
        )

        # Log subscription creation
        log_audit(
            action="stripe_subscription_created",
            user_id=current_user.id,
            resource_type="subscription",
            resource_id=subscription["id"],
            details={
                "price_id": request.price_id,
                "status": subscription["status"],
                "trial_days": request.trial_days,
            },
        )

        return JSONResponse(
            content={
                "status": "success",
                "data": {
                    "subscription_id": subscription["id"],
                    "status": subscription["status"],
                    "current_period_end": subscription.get("current_period_end"),
                    "trial_end": subscription.get("trial_end"),
                    "customer_id": customer["id"],
                },
                "message": "Subscription created successfully",
            }
        )

    except Exception as e:
        logger.error(f"Failed to create subscription: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create subscription: {str(e)}")


@router.patch("/stripe/subscriptions/{subscription_id}")
async def update_subscription(
    subscription_id: str,
    request: SubscriptionUpdateRequest,
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """
    Update an existing Stripe subscription

    Args:
        subscription_id: Stripe subscription ID
        request: Update parameters
        current_user: Authenticated user

    Returns:
        JSONResponse: Updated subscription data
    """
    try:
        # Build update kwargs
        update_kwargs = {}
        if request.price_id:
            update_kwargs["items"] = [{"price": request.price_id}]
        if request.cancel_at_period_end is not None:
            update_kwargs["cancel_at_period_end"] = request.cancel_at_period_end
        if request.metadata:
            update_kwargs["metadata"] = request.metadata

        # Update subscription
        subscription = await stripe_service.update_subscription(subscription_id, **update_kwargs)

        # Log subscription update
        log_audit(
            action="stripe_subscription_updated",
            user_id=current_user.id,
            resource_type="subscription",
            resource_id=subscription_id,
            details=update_kwargs,
        )

        return JSONResponse(
            content={
                "status": "success",
                "data": {
                    "subscription_id": subscription["id"],
                    "status": subscription["status"],
                    "cancel_at_period_end": subscription.get("cancel_at_period_end"),
                },
                "message": "Subscription updated successfully",
            }
        )

    except Exception as e:
        logger.error(f"Failed to update subscription: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update subscription: {str(e)}")


@router.delete("/stripe/subscriptions/{subscription_id}")
async def cancel_subscription(
    subscription_id: str,
    immediately: bool = False,
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """
    Cancel a Stripe subscription

    Args:
        subscription_id: Stripe subscription ID
        immediately: If True, cancel immediately instead of at period end
        current_user: Authenticated user

    Returns:
        JSONResponse: Cancellation confirmation
    """
    try:
        subscription = await stripe_service.cancel_subscription(
            subscription_id=subscription_id,
            immediately=immediately,
        )

        # Log subscription cancellation
        log_audit(
            action="stripe_subscription_cancelled",
            user_id=current_user.id,
            resource_type="subscription",
            resource_id=subscription_id,
            details={"immediately": immediately, "status": subscription["status"]},
        )

        return JSONResponse(
            content={
                "status": "success",
                "data": {
                    "subscription_id": subscription["id"],
                    "status": subscription["status"],
                    "cancelled_at": subscription.get("canceled_at"),
                },
                "message": f"Subscription {'cancelled immediately' if immediately else 'will cancel at period end'}",
            }
        )

    except Exception as e:
        logger.error(f"Failed to cancel subscription: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel subscription: {str(e)}")


@router.get("/stripe/customer")
async def get_customer_info(
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """
    Get Stripe customer information for the current user

    Args:
        current_user: Authenticated user

    Returns:
        JSONResponse: Customer data
    """
    try:
        # Try to get existing customer by metadata
        # Note: This requires implementing a method to search customers by metadata
        # For now, we'll create if not exists
        customer = await stripe_service.create_customer(
            user_id=str(current_user.id),
            email=current_user.email,
            name=getattr(current_user, "name", None),
        )

        return JSONResponse(
            content={
                "status": "success",
                "data": {
                    "customer_id": customer["id"],
                    "email": customer["email"],
                    "name": customer.get("name"),
                    "default_source": customer.get("default_source"),
                },
                "message": "Customer information retrieved successfully",
            }
        )

    except Exception as e:
        logger.error(f"Failed to get customer info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get customer information: {str(e)}")


@router.get("/stripe/invoices")
async def get_customer_invoices(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """
    Get invoices for the current user

    Args:
        limit: Maximum number of invoices to return
        current_user: Authenticated user

    Returns:
        JSONResponse: List of invoices
    """
    try:
        # Get customer
        customer = await stripe_service.create_customer(
            user_id=str(current_user.id),
            email=current_user.email,
        )

        # Get invoices
        invoices = await stripe_service.get_invoices(
            customer_id=customer["id"],
            limit=limit,
        )

        return JSONResponse(
            content={
                "status": "success",
                "data": {
                    "invoices": [
                        {
                            "id": inv["id"],
                            "number": inv.get("number"),
                            "amount_due": inv["amount_due"],
                            "amount_paid": inv["amount_paid"],
                            "status": inv["status"],
                            "created": inv["created"],
                            "due_date": inv.get("due_date"),
                            "invoice_pdf": inv.get("invoice_pdf"),
                        }
                        for inv in invoices
                    ]
                },
                "message": "Invoices retrieved successfully",
            }
        )

    except Exception as e:
        logger.error(f"Failed to get invoices: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get invoices: {str(e)}")


@router.post("/stripe/webhook")
async def handle_stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
) -> JSONResponse:
    """
    Handle Stripe webhook events

    Args:
        request: Request object containing webhook payload
        stripe_signature: Stripe webhook signature for verification

    Returns:
        JSONResponse: Webhook processing result
    """
    try:
        # Get raw body
        payload = await request.body()

        # Verify and process webhook
        success, result = await stripe_service.handle_webhook(
            payload=payload,
            signature=stripe_signature,
        )

        if not success:
            raise HTTPException(status_code=400, detail=result.get("error", "Webhook verification failed"))

        # Log webhook processing
        logger.info(f"Processed Stripe webhook: {result.get('event_type')}")

        return JSONResponse(
            content={
                "status": "success",
                "data": {
                    "event_type": result.get("event_type"),
                    "event_id": result.get("event_id"),
                    "processed": True,
                },
                "message": "Webhook processed successfully",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")

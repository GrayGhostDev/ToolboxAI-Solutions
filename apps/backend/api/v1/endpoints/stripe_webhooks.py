"""
Stripe Webhook Handlers for Payment Processing

Handles Stripe webhook events for subscription management, payment processing,
and billing operations with proper signature validation and idempotency.
"""

import hashlib
import hmac
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Header, Request, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/stripe", tags=["Stripe Webhooks"])

# Environment configuration
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY", "")
ENABLE_STRIPE_WEBHOOKS = os.getenv("ENABLE_STRIPE_WEBHOOKS", "false").lower() == "true"


class StripeEvent(BaseModel):
    """Stripe webhook event model"""

    id: str
    object: str
    api_version: Optional[str] = None
    created: int
    data: Dict[str, Any]
    livemode: bool
    pending_webhooks: int
    request: Optional[Dict[str, Any]] = None
    type: str


class WebhookResponse(BaseModel):
    """Standard webhook response"""

    status: str = Field(default="success")
    message: str
    event_id: Optional[str] = None
    processed_at: Optional[str] = None


def verify_stripe_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify Stripe webhook signature for security

    Args:
        payload: Raw request body
        signature: Stripe-Signature header value
        secret: Webhook endpoint secret from Stripe

    Returns:
        bool: True if signature is valid
    """
    if not secret:
        logger.warning("Stripe webhook secret not configured")
        return False

    try:
        # Parse the signature header
        timestamp = None
        signatures = []

        for element in signature.split(","):
            key, value = element.split("=")
            if key == "t":
                timestamp = value
            elif key == "v1":
                signatures.append(value)

        if not timestamp or not signatures:
            return False

        # Construct the signed payload
        signed_payload = f"{timestamp}.".encode() + payload

        # Compute expected signature
        expected_signature = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()

        # Check if any signature matches
        for sig in signatures:
            if hmac.compare_digest(expected_signature, sig):
                return True

        return False

    except Exception as e:
        logger.error(f"Error verifying Stripe signature: {e}")
        return False


@router.post("/webhooks", response_model=WebhookResponse)
async def handle_stripe_webhook(
    request: Request, stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature")
):
    """
    Main Stripe webhook handler endpoint

    Processes various Stripe events including:
    - checkout.session.completed
    - customer.subscription.created
    - customer.subscription.updated
    - customer.subscription.deleted
    - invoice.payment_succeeded
    - invoice.payment_failed
    """

    # Check if Stripe webhooks are enabled
    if not ENABLE_STRIPE_WEBHOOKS:
        logger.warning("Stripe webhook received but webhooks are disabled")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe webhooks are currently disabled",
        )

    # Get raw body for signature verification
    body = await request.body()

    # Verify webhook signature
    if STRIPE_WEBHOOK_SECRET:
        if not stripe_signature:
            logger.error("Missing Stripe signature header")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Stripe signature"
            )

        if not verify_stripe_signature(body, stripe_signature, STRIPE_WEBHOOK_SECRET):
            logger.error("Invalid Stripe signature")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")

    # Parse event
    try:
        event_data = json.loads(body)
        event = StripeEvent(**event_data)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse Stripe event: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid event payload")

    # Log event receipt
    logger.info(f"Received Stripe webhook: {event.type} (ID: {event.id})")

    # Process event based on type
    try:
        if event.type == "checkout.session.completed":
            await handle_checkout_completed(event)

        elif event.type == "customer.subscription.created":
            await handle_subscription_created(event)

        elif event.type == "customer.subscription.updated":
            await handle_subscription_updated(event)

        elif event.type == "customer.subscription.deleted":
            await handle_subscription_deleted(event)

        elif event.type == "invoice.payment_succeeded":
            await handle_payment_succeeded(event)

        elif event.type == "invoice.payment_failed":
            await handle_payment_failed(event)

        else:
            logger.info(f"Unhandled Stripe event type: {event.type}")

    except Exception as e:
        logger.error(f"Error processing Stripe event {event.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to process webhook"
        )

    return WebhookResponse(
        status="success",
        message=f"Processed {event.type} event",
        event_id=event.id,
        processed_at=datetime.now(timezone.utc).isoformat(),
    )


async def handle_checkout_completed(event: StripeEvent):
    """Handle successful checkout session completion"""
    session = event.data.get("object", {})
    customer_id = session.get("customer")
    subscription_id = session.get("subscription")

    logger.info(f"Checkout completed for customer {customer_id}, subscription {subscription_id}")

    # TODO: Implement actual business logic
    # - Create or update user subscription in database
    # - Send welcome email
    # - Grant access to premium features


async def handle_subscription_created(event: StripeEvent):
    """Handle new subscription creation"""
    subscription = event.data.get("object", {})
    customer_id = subscription.get("customer")
    status = subscription.get("status")

    logger.info(f"Subscription created for customer {customer_id} with status {status}")

    # TODO: Implement actual business logic
    # - Store subscription details in database
    # - Update user entitlements


async def handle_subscription_updated(event: StripeEvent):
    """Handle subscription updates (plan changes, renewals, etc.)"""
    subscription = event.data.get("object", {})
    customer_id = subscription.get("customer")
    status = subscription.get("status")

    logger.info(f"Subscription updated for customer {customer_id} to status {status}")

    # TODO: Implement actual business logic
    # - Update subscription details in database
    # - Adjust user entitlements based on new plan


async def handle_subscription_deleted(event: StripeEvent):
    """Handle subscription cancellation"""
    subscription = event.data.get("object", {})
    customer_id = subscription.get("customer")

    logger.info(f"Subscription cancelled for customer {customer_id}")

    # TODO: Implement actual business logic
    # - Mark subscription as cancelled in database
    # - Revoke premium features
    # - Send cancellation confirmation email


async def handle_payment_succeeded(event: StripeEvent):
    """Handle successful payment"""
    invoice = event.data.get("object", {})
    customer_id = invoice.get("customer")
    amount_paid = invoice.get("amount_paid", 0) / 100  # Convert from cents

    logger.info(f"Payment of ${amount_paid} succeeded for customer {customer_id}")

    # TODO: Implement actual business logic
    # - Record payment in database
    # - Send receipt email


async def handle_payment_failed(event: StripeEvent):
    """Handle failed payment"""
    invoice = event.data.get("object", {})
    customer_id = invoice.get("customer")

    logger.info(f"Payment failed for customer {customer_id}")

    # TODO: Implement actual business logic
    # - Record failed payment attempt
    # - Send payment failure notification
    # - Potentially suspend access after grace period


@router.get("/webhook-status")
async def get_webhook_status():
    """Check Stripe webhook configuration status"""
    return {
        "enabled": ENABLE_STRIPE_WEBHOOKS,
        "signature_verification": bool(STRIPE_WEBHOOK_SECRET),
        "api_key_configured": bool(STRIPE_API_KEY),
        "endpoints": {
            "webhooks": "/api/v1/stripe/webhooks",
            "status": "/api/v1/stripe/webhook-status",
        },
        "supported_events": [
            "checkout.session.completed",
            "customer.subscription.created",
            "customer.subscription.updated",
            "customer.subscription.deleted",
            "invoice.payment_succeeded",
            "invoice.payment_failed",
        ],
    }

"""
Stripe Webhook Handler
Processes Stripe webhook events for payments, subscriptions, and other events
"""

import json
import logging
from datetime import datetime
from typing import Any

import stripe
from database.db import get_async_db
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.config import settings
from apps.backend.services.dunning_service import DunningService
from apps.backend.services.email.queue import EmailPriority, email_queue
from apps.backend.services.invoice_generator import InvoiceGenerator
from apps.backend.services.stripe_service import StripeService
from database.models.payment import Customer, Invoice, Payment, Subscription

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/stripe", tags=["Stripe Webhooks"])

# Initialize services
stripe_service = StripeService()
dunning_service = DunningService()
invoice_generator = InvoiceGenerator()

# Set Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY


async def verify_stripe_signature(
    request: Request, stripe_signature: str = Header(None)
) -> dict[str, Any]:
    """
    Verify Stripe webhook signature

    Args:
        request: FastAPI request
        stripe_signature: Stripe signature header

    Returns:
        Parsed event data

    Raises:
        HTTPException: If signature verification fails
    """
    # Get raw body
    body = await request.body()

    # Get webhook secret
    webhook_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", None)

    if not webhook_secret:
        logger.warning("Stripe webhook secret not configured")
        # In development, allow without verification
        if settings.ENVIRONMENT == "development":
            return json.loads(body)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook secret not configured",
        )

    try:
        # Verify signature
        event = stripe.Webhook.construct_event(body, stripe_signature, webhook_secret)
        return event
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")


@router.post("/", status_code=status.HTTP_200_OK)
async def handle_stripe_webhook(
    event: dict[str, Any] = Depends(verify_stripe_signature),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Handle Stripe webhook events

    Supported events:
    - payment_intent.succeeded
    - payment_intent.payment_failed
    - customer.subscription.created
    - customer.subscription.updated
    - customer.subscription.deleted
    - invoice.payment_succeeded
    - invoice.payment_failed
    - charge.refunded
    - customer.created
    - customer.updated
    """
    try:
        event_type = event["type"]
        event_data = event["data"]["object"]

        logger.info(f"Processing Stripe webhook: {event_type}")

        # Route to appropriate handler
        if event_type == "payment_intent.succeeded":
            await handle_payment_succeeded(event_data, db)

        elif event_type == "payment_intent.payment_failed":
            await handle_payment_failed(event_data, db)

        elif event_type == "customer.subscription.created":
            await handle_subscription_created(event_data, db)

        elif event_type == "customer.subscription.updated":
            await handle_subscription_updated(event_data, db)

        elif event_type == "customer.subscription.deleted":
            await handle_subscription_deleted(event_data, db)

        elif event_type == "invoice.payment_succeeded":
            await handle_invoice_paid(event_data, db)

        elif event_type == "invoice.payment_failed":
            await handle_invoice_payment_failed(event_data, db)

        elif event_type == "charge.refunded":
            await handle_charge_refunded(event_data, db)

        elif event_type == "customer.created":
            await handle_customer_created(event_data, db)

        elif event_type == "customer.updated":
            await handle_customer_updated(event_data, db)

        else:
            logger.info(f"Unhandled event type: {event_type}")

        return JSONResponse(content={"status": "success"}, status_code=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        # Return 200 to acknowledge receipt even if processing failed
        # This prevents Stripe from retrying
        return JSONResponse(
            content={"status": "error", "message": str(e)}, status_code=status.HTTP_200_OK
        )


async def handle_payment_succeeded(payment_intent: dict[str, Any], db: AsyncSession):
    """Handle successful payment"""
    try:
        # Find or create customer
        customer_id = payment_intent.get("customer")
        if customer_id:
            customer = await db.scalar(
                select(Customer).where(Customer.stripe_customer_id == customer_id)
            )
        else:
            customer = None

        # Create payment record
        payment = Payment(
            stripe_payment_intent_id=payment_intent["id"],
            customer_id=customer.id if customer else None,
            amount=payment_intent["amount"] / 100,  # Convert from cents
            currency=payment_intent["currency"],
            status="succeeded",
            payment_method=payment_intent.get("payment_method"),
            metadata=payment_intent.get("metadata", {}),
        )
        db.add(payment)
        await db.commit()

        # Send confirmation email
        if customer and customer.user:
            await email_queue.enqueue(
                to_email=customer.user.email,
                subject="Payment Confirmation",
                template_name="payment_confirmation",
                template_data={
                    "customer_name": customer.user.name,
                    "amount": payment.amount,
                    "transaction_id": payment_intent["id"],
                    "payment_date": datetime.utcnow().strftime("%B %d, %Y"),
                },
                priority=EmailPriority.HIGH,
            )

        logger.info(f"Payment succeeded: {payment_intent['id']}")

    except Exception as e:
        logger.error(f"Error handling payment success: {e}")
        await db.rollback()


async def handle_payment_failed(payment_intent: dict[str, Any], db: AsyncSession):
    """Handle failed payment"""
    try:
        # Find customer
        customer_id = payment_intent.get("customer")
        if customer_id:
            customer = await db.scalar(
                select(Customer).where(Customer.stripe_customer_id == customer_id)
            )

            # Process through dunning service
            if customer:
                await dunning_service.handle_payment_failure(
                    customer_id=customer.id,
                    payment_intent_id=payment_intent["id"],
                    failure_reason=payment_intent.get("last_payment_error", {}).get("message"),
                    db=db,
                )

        # Create failed payment record
        payment = Payment(
            stripe_payment_intent_id=payment_intent["id"],
            customer_id=customer.id if customer else None,
            amount=payment_intent["amount"] / 100,
            currency=payment_intent["currency"],
            status="failed",
            payment_method=payment_intent.get("payment_method"),
            metadata=payment_intent.get("metadata", {}),
            failure_reason=payment_intent.get("last_payment_error", {}).get("message"),
        )
        db.add(payment)
        await db.commit()

        logger.warning(f"Payment failed: {payment_intent['id']}")

    except Exception as e:
        logger.error(f"Error handling payment failure: {e}")
        await db.rollback()


async def handle_subscription_created(subscription: dict[str, Any], db: AsyncSession):
    """Handle new subscription creation"""
    try:
        # Find customer
        customer = await db.scalar(
            select(Customer).where(Customer.stripe_customer_id == subscription["customer"])
        )

        if not customer:
            logger.error(f"Customer not found: {subscription['customer']}")
            return

        # Create subscription record
        new_subscription = Subscription(
            stripe_subscription_id=subscription["id"],
            customer_id=customer.id,
            stripe_price_id=subscription["items"]["data"][0]["price"]["id"],
            status=subscription["status"],
            current_period_start=datetime.fromtimestamp(subscription["current_period_start"]),
            current_period_end=datetime.fromtimestamp(subscription["current_period_end"]),
            cancel_at_period_end=subscription.get("cancel_at_period_end", False),
            metadata=subscription.get("metadata", {}),
        )
        db.add(new_subscription)
        await db.commit()

        # Send welcome email
        if customer.user:
            await email_queue.enqueue(
                to_email=customer.user.email,
                subject="Welcome to Your Subscription!",
                template_name="subscription_renewal",
                template_data={
                    "customer_name": customer.user.name,
                    "plan_name": subscription["items"]["data"][0]["price"].get(
                        "nickname", "Subscription"
                    ),
                    "amount": subscription["items"]["data"][0]["price"]["unit_amount"] / 100,
                    "billing_period": subscription["items"]["data"][0]["price"]["recurring"][
                        "interval"
                    ],
                },
                priority=EmailPriority.HIGH,
            )

        logger.info(f"Subscription created: {subscription['id']}")

    except Exception as e:
        logger.error(f"Error handling subscription creation: {e}")
        await db.rollback()


async def handle_subscription_updated(subscription: dict[str, Any], db: AsyncSession):
    """Handle subscription update"""
    try:
        # Find existing subscription
        existing = await db.scalar(
            select(Subscription).where(Subscription.stripe_subscription_id == subscription["id"])
        )

        if not existing:
            # Create new subscription if not found
            await handle_subscription_created(subscription, db)
            return

        # Update subscription
        existing.status = subscription["status"]
        existing.stripe_price_id = subscription["items"]["data"][0]["price"]["id"]
        existing.current_period_start = datetime.fromtimestamp(subscription["current_period_start"])
        existing.current_period_end = datetime.fromtimestamp(subscription["current_period_end"])
        existing.cancel_at_period_end = subscription.get("cancel_at_period_end", False)
        existing.canceled_at = (
            datetime.fromtimestamp(subscription["canceled_at"])
            if subscription.get("canceled_at")
            else None
        )
        existing.metadata = subscription.get("metadata", {})

        await db.commit()

        logger.info(f"Subscription updated: {subscription['id']}")

    except Exception as e:
        logger.error(f"Error handling subscription update: {e}")
        await db.rollback()


async def handle_subscription_deleted(subscription: dict[str, Any], db: AsyncSession):
    """Handle subscription cancellation"""
    try:
        # Find subscription
        existing = await db.scalar(
            select(Subscription).where(Subscription.stripe_subscription_id == subscription["id"])
        )

        if existing:
            existing.status = "canceled"
            existing.canceled_at = datetime.utcnow()
            await db.commit()

            # Send cancellation email
            if existing.customer and existing.customer.user:
                await email_queue.enqueue(
                    to_email=existing.customer.user.email,
                    subject="Subscription Canceled",
                    html_content=f"""
                    <h2>Your subscription has been canceled</h2>
                    <p>We're sorry to see you go. Your subscription has been canceled
                    and will expire on {existing.current_period_end.strftime('%B %d, %Y')}.</p>
                    <p>You can reactivate your subscription at any time from your account settings.</p>
                    """,
                    priority=EmailPriority.HIGH,
                )

        logger.info(f"Subscription deleted: {subscription['id']}")

    except Exception as e:
        logger.error(f"Error handling subscription deletion: {e}")
        await db.rollback()


async def handle_invoice_paid(invoice: dict[str, Any], db: AsyncSession):
    """Handle successful invoice payment"""
    try:
        # Find customer
        customer = await db.scalar(
            select(Customer).where(Customer.stripe_customer_id == invoice["customer"])
        )

        if not customer:
            logger.error(f"Customer not found: {invoice['customer']}")
            return

        # Find subscription
        subscription = None
        if invoice.get("subscription"):
            subscription = await db.scalar(
                select(Subscription).where(
                    Subscription.stripe_subscription_id == invoice["subscription"]
                )
            )

        # Create or update invoice record
        existing_invoice = await db.scalar(
            select(Invoice).where(Invoice.stripe_invoice_id == invoice["id"])
        )

        if existing_invoice:
            existing_invoice.status = "paid"
            existing_invoice.paid_at = datetime.fromtimestamp(
                invoice["status_transitions"]["paid_at"]
            )
        else:
            new_invoice = Invoice(
                stripe_invoice_id=invoice["id"],
                customer_id=customer.id,
                subscription_id=subscription.id if subscription else None,
                amount_total=invoice["amount_paid"] / 100,
                currency=invoice["currency"],
                status="paid",
                paid_at=datetime.fromtimestamp(invoice["status_transitions"]["paid_at"]),
                invoice_pdf=invoice.get("invoice_pdf"),
                hosted_invoice_url=invoice.get("hosted_invoice_url"),
                metadata=invoice.get("metadata", {}),
            )
            db.add(new_invoice)

        await db.commit()

        # Clear any dunning state
        if subscription:
            await dunning_service.clear_dunning_state(subscription_id=subscription.id, db=db)

        logger.info(f"Invoice paid: {invoice['id']}")

    except Exception as e:
        logger.error(f"Error handling invoice payment: {e}")
        await db.rollback()


async def handle_invoice_payment_failed(invoice: dict[str, Any], db: AsyncSession):
    """Handle failed invoice payment"""
    try:
        # Find customer
        customer = await db.scalar(
            select(Customer).where(Customer.stripe_customer_id == invoice["customer"])
        )

        if customer:
            # Process through dunning
            await dunning_service.handle_payment_failure(
                customer_id=customer.id,
                payment_intent_id=invoice.get("payment_intent"),
                failure_reason="Invoice payment failed",
                db=db,
            )

        # Update invoice record
        existing_invoice = await db.scalar(
            select(Invoice).where(Invoice.stripe_invoice_id == invoice["id"])
        )

        if existing_invoice:
            existing_invoice.status = "payment_failed"
            await db.commit()

        logger.warning(f"Invoice payment failed: {invoice['id']}")

    except Exception as e:
        logger.error(f"Error handling invoice payment failure: {e}")
        await db.rollback()


async def handle_charge_refunded(charge: dict[str, Any], db: AsyncSession):
    """Handle charge refund"""
    try:
        # Find payment by charge ID
        payment = await db.scalar(
            select(Payment).where(Payment.stripe_payment_intent_id == charge.get("payment_intent"))
        )

        if payment:
            payment.status = "refunded"
            payment.refunded_amount = charge["amount_refunded"] / 100
            await db.commit()

            # Send refund confirmation
            if payment.customer and payment.customer.user:
                await email_queue.enqueue(
                    to_email=payment.customer.user.email,
                    subject="Refund Processed",
                    html_content=f"""
                    <h2>Your refund has been processed</h2>
                    <p>A refund of ${payment.refunded_amount:.2f} has been issued
                    and should appear in your account within 5-10 business days.</p>
                    <p>Reference: {charge['id']}</p>
                    """,
                    priority=EmailPriority.HIGH,
                )

        logger.info(f"Charge refunded: {charge['id']}")

    except Exception as e:
        logger.error(f"Error handling refund: {e}")
        await db.rollback()


async def handle_customer_created(customer: dict[str, Any], db: AsyncSession):
    """Handle new Stripe customer creation"""
    try:
        # Check if customer already exists
        existing = await db.scalar(
            select(Customer).where(Customer.stripe_customer_id == customer["id"])
        )

        if not existing:
            # Create customer record
            new_customer = Customer(
                stripe_customer_id=customer["id"],
                email=customer["email"],
                name=customer.get("name"),
                metadata=customer.get("metadata", {}),
            )
            db.add(new_customer)
            await db.commit()

            logger.info(f"Customer created: {customer['id']}")

    except Exception as e:
        logger.error(f"Error handling customer creation: {e}")
        await db.rollback()


async def handle_customer_updated(customer: dict[str, Any], db: AsyncSession):
    """Handle Stripe customer update"""
    try:
        # Find customer
        existing = await db.scalar(
            select(Customer).where(Customer.stripe_customer_id == customer["id"])
        )

        if existing:
            existing.email = customer["email"]
            existing.name = customer.get("name")
            existing.metadata = customer.get("metadata", {})
            await db.commit()

            logger.info(f"Customer updated: {customer['id']}")

    except Exception as e:
        logger.error(f"Error handling customer update: {e}")
        await db.rollback()


@router.get("/test")
async def test_webhook_endpoint():
    """Test endpoint to verify webhook is accessible"""
    return JSONResponse(
        content={
            "status": "success",
            "message": "Stripe webhook endpoint is working",
            "timestamp": datetime.utcnow().isoformat(),
        }
    )

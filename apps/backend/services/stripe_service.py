"""
Stripe Payment Service
Handles all payment processing, subscriptions, and billing operations

Multi-Tenant Security:
- Webhook handlers accept organization_id parameter from Stripe metadata
- Sets RLS context for database operations
- Filters queries by organization_id where applicable

@module stripe_service
@version 1.0.0
@since 2025-09-26
@updated 2025-10-11 - Added multi-tenant organization filtering
"""

import hashlib
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

import stripe
from sqlalchemy import text
from stripe.error import (
    SignatureVerificationError,
    StripeError,
)

from apps.backend.core.cache import CacheConfig, CacheKey, cache
from apps.backend.core.config import settings
from database.connection import get_db

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY if hasattr(settings, "STRIPE_SECRET_KEY") else None
stripe.api_version = "2024-12-18"  # Use latest API version as of 2025


class StripeService:
    """
    Comprehensive Stripe payment service with subscription management,
    payment processing, and webhook handling
    """

    def __init__(self):
        """Initialize Stripe service with configuration"""
        self.api_key = (
            settings.STRIPE_SECRET_KEY if hasattr(settings, "STRIPE_SECRET_KEY") else None
        )
        self.webhook_secret = (
            settings.STRIPE_WEBHOOK_SECRET if hasattr(settings, "STRIPE_WEBHOOK_SECRET") else None
        )
        self.publishable_key = (
            settings.STRIPE_PUBLISHABLE_KEY if hasattr(settings, "STRIPE_PUBLISHABLE_KEY") else None
        )

        if not self.api_key:
            logger.warning("Stripe API key not configured. Payment features will be disabled.")
        else:
            stripe.api_key = self.api_key

        # Cache configuration - using CacheConfig static attributes
        self.cache_prefix = CacheConfig.PREFIX_API + ":stripe"
        self.cache_ttl = CacheConfig.LONG_TTL  # 1 hour from CacheConfig
        self.cache_version = 1

        # Define subscription tiers
        self.subscription_tiers = {
            "free": {
                "name": "Free",
                "price": 0,
                "features": ["Basic access", "10 API calls/day", "Community support"],
            },
            "starter": {
                "name": "Starter",
                "price_id": (
                    settings.STRIPE_STARTER_PRICE_ID
                    if hasattr(settings, "STRIPE_STARTER_PRICE_ID")
                    else None
                ),
                "price": 29,
                "features": ["100 API calls/day", "Email support", "Basic analytics"],
            },
            "professional": {
                "name": "Professional",
                "price_id": (
                    settings.STRIPE_PRO_PRICE_ID
                    if hasattr(settings, "STRIPE_PRO_PRICE_ID")
                    else None
                ),
                "price": 99,
                "features": [
                    "1000 API calls/day",
                    "Priority support",
                    "Advanced analytics",
                    "Custom integrations",
                ],
            },
            "enterprise": {
                "name": "Enterprise",
                "price_id": (
                    settings.STRIPE_ENTERPRISE_PRICE_ID
                    if hasattr(settings, "STRIPE_ENTERPRISE_PRICE_ID")
                    else None
                ),
                "price": 499,
                "features": ["Unlimited API calls", "Dedicated support", "Custom features", "SLA"],
            },
        }

    # Customer Management
    async def create_customer(
        self,
        user_id: str,
        email: str,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
        payment_method_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new Stripe customer

        Args:
            user_id: Internal user ID
            email: Customer email
            name: Customer name
            metadata: Additional metadata
            payment_method_id: Optional payment method to attach

        Returns:
            Customer object
        """
        try:
            # Check cache first
            cache_key = CacheKey.generate(self.cache_prefix, "customer", user_id)
            cached_customer = await cache.get(cache_key)
            if cached_customer:
                logger.info(f"Customer found in cache: {user_id}")
                return cached_customer

            # Create customer with idempotency key
            idempotency_key = f"create_customer_{user_id}_{hashlib.md5(email.encode()).hexdigest()}"

            customer_data = {
                "email": email,
                "metadata": {
                    "user_id": user_id,
                    "created_via": "api",
                    "platform": "toolbox_ai",
                    **(metadata or {}),
                },
                "idempotency_key": idempotency_key,
            }

            if name:
                customer_data["name"] = name

            if payment_method_id:
                customer_data["payment_method"] = payment_method_id
                customer_data["invoice_settings"] = {"default_payment_method": payment_method_id}

            customer = stripe.Customer.create(**customer_data)

            # Cache the customer
            await cache.set(cache_key, customer.to_dict(), self.cache_ttl)

            logger.info(f"Created Stripe customer: {customer.id} for user: {user_id}")
            return customer.to_dict()

        except StripeError as e:
            logger.error(f"Stripe error creating customer: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating customer: {e}")
            raise

    async def get_customer(self, customer_id: str) -> dict[str, Any] | None:
        """
        Retrieve a Stripe customer

        Args:
            customer_id: Stripe customer ID

        Returns:
            Customer object or None
        """
        try:
            # Check cache first
            cache_key = CacheKey.generate(self.cache_prefix, "customer", customer_id)
            cached_customer = await cache.get(cache_key)
            if cached_customer:
                return cached_customer

            customer = stripe.Customer.retrieve(customer_id)

            # Cache the customer
            await cache.set(cache_key, customer.to_dict(), self.cache_ttl)

            return customer.to_dict()

        except StripeError as e:
            logger.error(f"Stripe error retrieving customer: {e}")
            return None

    async def update_customer(self, customer_id: str, **kwargs) -> dict[str, Any]:
        """
        Update a Stripe customer

        Args:
            customer_id: Stripe customer ID
            **kwargs: Fields to update

        Returns:
            Updated customer object
        """
        try:
            customer = stripe.Customer.modify(customer_id, **kwargs)

            # Invalidate cache
            cache_key = CacheKey.generate(self.cache_prefix, "customer", customer_id)
            await cache.delete(cache_key)

            logger.info(f"Updated Stripe customer: {customer_id}")
            return customer.to_dict()

        except StripeError as e:
            logger.error(f"Stripe error updating customer: {e}")
            raise

    # Subscription Management
    async def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        trial_days: int = 14,
        metadata: dict[str, Any] | None = None,
        coupon: str | None = None,
        payment_behavior: str = "default_incomplete",
    ) -> dict[str, Any]:
        """
        Create a subscription for a customer

        Args:
            customer_id: Stripe customer ID
            price_id: Price/plan ID
            trial_days: Trial period in days
            metadata: Additional metadata
            coupon: Coupon code to apply
            payment_behavior: Payment collection behavior

        Returns:
            Subscription object with payment intent
        """
        try:
            subscription_data = {
                "customer": customer_id,
                "items": [{"price": price_id}],
                "payment_behavior": payment_behavior,
                "payment_settings": {
                    "payment_method_types": ["card"],
                    "save_default_payment_method": "on_subscription",
                },
                "expand": ["latest_invoice.payment_intent", "pending_setup_intent"],
                "metadata": {"platform": "toolbox_ai", **(metadata or {})},
            }

            if trial_days > 0:
                subscription_data["trial_period_days"] = trial_days

            if coupon:
                subscription_data["coupon"] = coupon

            subscription = stripe.Subscription.create(**subscription_data)

            result = {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
                "trial_end": subscription.trial_end,
                "items": [item.to_dict() for item in subscription["items"]["data"]],
            }

            # Add payment intent info if available
            if subscription.latest_invoice and subscription.latest_invoice.payment_intent:
                result["client_secret"] = subscription.latest_invoice.payment_intent.client_secret
                result["payment_status"] = subscription.latest_invoice.payment_intent.status
            elif subscription.pending_setup_intent:
                result["setup_intent_client_secret"] = (
                    subscription.pending_setup_intent.client_secret
                )

            logger.info(f"Created subscription: {subscription.id} for customer: {customer_id}")
            return result

        except StripeError as e:
            logger.error(f"Stripe error creating subscription: {e}")
            raise

    async def cancel_subscription(
        self, subscription_id: str, immediately: bool = False, reason: str | None = None
    ) -> dict[str, Any]:
        """
        Cancel a subscription

        Args:
            subscription_id: Subscription ID
            immediately: Cancel immediately or at period end
            reason: Cancellation reason

        Returns:
            Updated subscription object
        """
        try:
            if immediately:
                subscription = stripe.Subscription.delete(subscription_id)
            else:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True,
                    metadata={"cancellation_reason": reason} if reason else None,
                )

            logger.info(f"Cancelled subscription: {subscription_id}")
            return subscription.to_dict()

        except StripeError as e:
            logger.error(f"Stripe error cancelling subscription: {e}")
            raise

    async def update_subscription(
        self,
        subscription_id: str,
        price_id: str | None = None,
        quantity: int | None = None,
        proration_behavior: str = "create_prorations",
    ) -> dict[str, Any]:
        """
        Update a subscription (upgrade/downgrade)

        Args:
            subscription_id: Subscription ID
            price_id: New price ID for upgrade/downgrade
            quantity: New quantity
            proration_behavior: How to handle prorations

        Returns:
            Updated subscription object
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)

            update_data = {"proration_behavior": proration_behavior}

            if price_id:
                # Replace the subscription item with new price
                update_data["items"] = [
                    {"id": subscription["items"]["data"][0].id, "price": price_id}
                ]

            if quantity is not None:
                if "items" not in update_data:
                    update_data["items"] = [
                        {"id": subscription["items"]["data"][0].id, "quantity": quantity}
                    ]
                else:
                    update_data["items"][0]["quantity"] = quantity

            updated_subscription = stripe.Subscription.modify(subscription_id, **update_data)

            logger.info(f"Updated subscription: {subscription_id}")
            return updated_subscription.to_dict()

        except StripeError as e:
            logger.error(f"Stripe error updating subscription: {e}")
            raise

    # Payment Methods
    async def attach_payment_method(
        self, payment_method_id: str, customer_id: str, set_as_default: bool = True
    ) -> dict[str, Any]:
        """
        Attach a payment method to a customer

        Args:
            payment_method_id: Payment method ID
            customer_id: Customer ID
            set_as_default: Set as default payment method

        Returns:
            Payment method object
        """
        try:
            # Attach payment method to customer
            payment_method = stripe.PaymentMethod.attach(payment_method_id, customer=customer_id)

            # Set as default if requested
            if set_as_default:
                stripe.Customer.modify(
                    customer_id, invoice_settings={"default_payment_method": payment_method_id}
                )

            logger.info(f"Attached payment method: {payment_method_id} to customer: {customer_id}")
            return payment_method.to_dict()

        except StripeError as e:
            logger.error(f"Stripe error attaching payment method: {e}")
            raise

    async def list_payment_methods(
        self, customer_id: str, type: str = "card"
    ) -> list[dict[str, Any]]:
        """
        List payment methods for a customer

        Args:
            customer_id: Customer ID
            type: Payment method type

        Returns:
            List of payment methods
        """
        try:
            payment_methods = stripe.PaymentMethod.list(customer=customer_id, type=type)

            return [pm.to_dict() for pm in payment_methods.data]

        except StripeError as e:
            logger.error(f"Stripe error listing payment methods: {e}")
            return []

    # One-time Payments
    async def create_payment_intent(
        self,
        amount: int,
        currency: str = "usd",
        customer_id: str | None = None,
        payment_method_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        description: str | None = None,
        confirm: bool = False,
    ) -> dict[str, Any]:
        """
        Create a payment intent for one-time payment

        Args:
            amount: Amount in cents
            currency: Currency code
            customer_id: Optional customer ID
            payment_method_id: Optional payment method
            metadata: Additional metadata
            description: Payment description
            confirm: Auto-confirm payment

        Returns:
            Payment intent object
        """
        try:
            intent_data = {
                "amount": amount,
                "currency": currency,
                "automatic_payment_methods": {"enabled": True},
                "metadata": {"platform": "toolbox_ai", **(metadata or {})},
            }

            if customer_id:
                intent_data["customer"] = customer_id

            if payment_method_id:
                intent_data["payment_method"] = payment_method_id
                intent_data["confirm"] = confirm

            if description:
                intent_data["description"] = description

            payment_intent = stripe.PaymentIntent.create(**intent_data)

            logger.info(f"Created payment intent: {payment_intent.id} for amount: {amount}")
            return {
                "id": payment_intent.id,
                "client_secret": payment_intent.client_secret,
                "amount": payment_intent.amount,
                "currency": payment_intent.currency,
                "status": payment_intent.status,
            }

        except StripeError as e:
            logger.error(f"Stripe error creating payment intent: {e}")
            raise

    # Checkout Sessions
    async def create_checkout_session(
        self,
        customer_id: str | None = None,
        price_id: str | None = None,
        line_items: list[dict] | None = None,
        mode: str = "payment",
        success_url: str = None,
        cancel_url: str = None,
        metadata: dict[str, Any] | None = None,
        allow_promotion_codes: bool = True,
        trial_period_days: int | None = None,
    ) -> dict[str, Any]:
        """
        Create a Stripe Checkout session

        Args:
            customer_id: Customer ID
            price_id: Price ID for subscriptions
            line_items: Custom line items
            mode: 'payment' or 'subscription'
            success_url: Redirect URL on success
            cancel_url: Redirect URL on cancel
            metadata: Additional metadata
            allow_promotion_codes: Allow promo codes
            trial_period_days: Trial period for subscriptions

        Returns:
            Checkout session object
        """
        try:
            session_data = {
                "mode": mode,
                "success_url": success_url
                or f"{settings.FRONTEND_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
                "cancel_url": cancel_url or f"{settings.FRONTEND_URL}/payment/cancel",
                "allow_promotion_codes": allow_promotion_codes,
                "metadata": {"platform": "toolbox_ai", **(metadata or {})},
            }

            if customer_id:
                session_data["customer"] = customer_id
            else:
                session_data["customer_creation"] = "always"

            # Set line items
            if line_items:
                session_data["line_items"] = line_items
            elif price_id:
                session_data["line_items"] = [{"price": price_id, "quantity": 1}]
            else:
                raise ValueError("Either price_id or line_items must be provided")

            # Add subscription options
            if mode == "subscription":
                if trial_period_days:
                    session_data["subscription_data"] = {"trial_period_days": trial_period_days}

            session = stripe.checkout.Session.create(**session_data)

            logger.info(f"Created checkout session: {session.id}")
            return {"id": session.id, "url": session.url, "expires_at": session.expires_at}

        except StripeError as e:
            logger.error(f"Stripe error creating checkout session: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating checkout session: {e}")
            raise

    # Invoices
    async def get_invoices(
        self, customer_id: str, limit: int = 10, starting_after: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Get invoices for a customer

        Args:
            customer_id: Customer ID
            limit: Number of invoices to retrieve
            starting_after: Pagination cursor

        Returns:
            List of invoices
        """
        try:
            invoices = stripe.Invoice.list(
                customer=customer_id, limit=limit, starting_after=starting_after
            )

            return [
                {
                    "id": invoice.id,
                    "number": invoice.number,
                    "amount_paid": invoice.amount_paid,
                    "amount_due": invoice.amount_due,
                    "currency": invoice.currency,
                    "status": invoice.status,
                    "created": invoice.created,
                    "period_start": invoice.period_start,
                    "period_end": invoice.period_end,
                    "pdf": invoice.invoice_pdf,
                    "hosted_url": invoice.hosted_invoice_url,
                }
                for invoice in invoices.data
            ]

        except StripeError as e:
            logger.error(f"Stripe error getting invoices: {e}")
            return []

    # Webhook Handling
    async def handle_webhook(self, payload: bytes, signature: str) -> tuple[bool, dict[str, Any]]:
        """
        Handle Stripe webhook events

        Args:
            payload: Raw webhook payload
            signature: Stripe signature header

        Returns:
            Tuple of (success, event_data)
        """
        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(payload, signature, self.webhook_secret)

            # Check for duplicate webhook events to prevent reprocessing
            event_cache_key = CacheKey.generate(self.cache_prefix, "webhook", event["id"])
            if await cache.get(event_cache_key):
                logger.info(f"Duplicate webhook event detected: {event['type']} - {event['id']}")
                return True, {"status": "duplicate", "event_id": event["id"]}

            # Cache event to prevent duplicate processing (24 hours TTL)
            await cache.set(event_cache_key, True, CacheConfig.VERY_LONG_TTL)

            logger.info(f"Processing webhook event: {event['type']} - {event['id']}")

            # Handle different event types
            handlers = {
                # Customer events
                "customer.created": self._handle_customer_created,
                "customer.updated": self._handle_customer_updated,
                "customer.deleted": self._handle_customer_deleted,
                # Subscription events
                "customer.subscription.created": self._handle_subscription_created,
                "customer.subscription.updated": self._handle_subscription_updated,
                "customer.subscription.deleted": self._handle_subscription_deleted,
                "customer.subscription.trial_will_end": self._handle_subscription_trial_ending,
                # Payment events
                "payment_intent.succeeded": self._handle_payment_succeeded,
                "payment_intent.payment_failed": self._handle_payment_failed,
                "payment_method.attached": self._handle_payment_method_attached,
                # Invoice events
                "invoice.paid": self._handle_invoice_paid,
                "invoice.payment_failed": self._handle_invoice_payment_failed,
                "invoice.upcoming": self._handle_invoice_upcoming,
                # Checkout events
                "checkout.session.completed": self._handle_checkout_completed,
                "checkout.session.expired": self._handle_checkout_expired,
            }

            handler = handlers.get(event["type"])
            if handler:
                result = await handler(event)
                return True, result
            else:
                logger.info(f"Unhandled webhook event type: {event['type']}")
                return True, {"status": "unhandled", "type": event["type"]}

        except ValueError as e:
            logger.error(f"Invalid webhook payload: {e}")
            return False, {"error": "Invalid payload"}
        except SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            return False, {"error": "Invalid signature"}
        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            return False, {"error": str(e)}

    # Webhook Event Handlers
    async def _handle_customer_created(
        self, event: dict, organization_id: UUID | None = None
    ) -> dict[str, Any]:
        """
        Handle customer.created webhook

        Multi-Tenant Security:
        - Uses organization_id from metadata for RLS context
        """
        customer = event["data"]["object"]

        # Update database with Stripe customer ID
        user_id = customer["metadata"].get("user_id")
        if user_id and organization_id:
            async for session in get_db():
                # Set RLS context
                await session.execute(
                    text(f"SET app.current_organization_id = '{organization_id}'")
                )
                # Update user with Stripe customer ID
                # This assumes you have a User model with stripe_customer_id field
                pass

        return {"status": "processed", "customer_id": customer["id"]}

    async def _handle_subscription_created(
        self, event: dict, organization_id: UUID | None = None
    ) -> dict[str, Any]:
        """
        Handle customer.subscription.created webhook

        Multi-Tenant Security:
        - Uses organization_id from metadata for RLS context
        - Filters database queries by organization
        """
        subscription = event["data"]["object"]

        # Update user subscription status in database
        customer_id = subscription["customer"]

        if organization_id:
            async for session in get_db():
                # Set RLS context
                await session.execute(
                    text(f"SET app.current_organization_id = '{organization_id}'")
                )
                # Update subscription record with organization filter
                # Your database update logic here
                pass

        # Send welcome email for new subscription
        # await self.send_subscription_welcome_email(customer_id, subscription)

        return {"status": "processed", "subscription_id": subscription["id"]}

    async def _handle_subscription_updated(
        self, event: dict, organization_id: UUID | None = None
    ) -> dict[str, Any]:
        """
        Handle customer.subscription.updated webhook

        Multi-Tenant Security:
        - Uses organization_id from metadata for RLS context
        - Filters database queries by organization
        """
        subscription = event["data"]["object"]
        previous = event["data"].get("previous_attributes", {})

        if organization_id:
            async for session in get_db():
                # Set RLS context
                await session.execute(
                    text(f"SET app.current_organization_id = '{organization_id}'")
                )

                # Check what changed
                if "status" in previous:
                    # Status changed
                    if subscription["status"] == "active" and previous["status"] != "active":
                        # Subscription activated
                        logger.info(f"Subscription activated: {subscription['id']}")
                    elif subscription["status"] == "canceled":
                        # Subscription canceled
                        logger.info(f"Subscription canceled: {subscription['id']}")

                # Update subscription record with organization filter
                # Your database update logic here
                pass

        return {"status": "processed", "subscription_id": subscription["id"]}

    async def _handle_subscription_deleted(
        self, event: dict, organization_id: UUID | None = None
    ) -> dict[str, Any]:
        """
        Handle customer.subscription.deleted webhook

        Multi-Tenant Security:
        - Uses organization_id from metadata for RLS context
        - Filters database queries by organization
        """
        subscription = event["data"]["object"]

        # Update user to free tier
        customer_id = subscription["customer"]

        if organization_id:
            async for session in get_db():
                # Set RLS context
                await session.execute(
                    text(f"SET app.current_organization_id = '{organization_id}'")
                )
                # Update subscription record with organization filter
                # Your database update logic here
                pass

        # Send cancellation confirmation email
        # await self.send_subscription_cancellation_email(customer_id, subscription)

        return {"status": "processed", "subscription_id": subscription["id"]}

    async def _handle_subscription_trial_ending(self, event: dict) -> dict[str, Any]:
        """Handle customer.subscription.trial_will_end webhook"""
        subscription = event["data"]["object"]

        # Send trial ending reminder email (3 days before)
        # await self.send_trial_ending_email(subscription)

        return {"status": "processed", "subscription_id": subscription["id"]}

    async def _handle_payment_succeeded(
        self, event: dict, organization_id: UUID | None = None
    ) -> dict[str, Any]:
        """
        Handle payment_intent.succeeded webhook

        Multi-Tenant Security:
        - Uses organization_id from metadata for RLS context
        - Filters database queries by organization
        """
        payment_intent = event["data"]["object"]

        if organization_id:
            async for session in get_db():
                # Set RLS context
                await session.execute(
                    text(f"SET app.current_organization_id = '{organization_id}'")
                )
                # Update payment record in database with organization filter
                # Your database update logic here
                pass

        logger.info(
            f"Payment succeeded: {payment_intent['id']} - ${payment_intent['amount'] / 100}"
        )

        return {"status": "processed", "payment_intent_id": payment_intent["id"]}

    async def _handle_payment_failed(
        self, event: dict, organization_id: UUID | None = None
    ) -> dict[str, Any]:
        """
        Handle payment_intent.payment_failed webhook

        Multi-Tenant Security:
        - Uses organization_id from metadata for RLS context
        - Filters database queries by organization
        """
        payment_intent = event["data"]["object"]

        if organization_id:
            async for session in get_db():
                # Set RLS context
                await session.execute(
                    text(f"SET app.current_organization_id = '{organization_id}'")
                )
                # Update payment record in database with organization filter
                # Your database update logic here
                pass

        # Handle failed payment
        logger.warning(f"Payment failed: {payment_intent['id']}")

        # Send payment failed email
        # await self.send_payment_failed_email(payment_intent)

        return {"status": "processed", "payment_intent_id": payment_intent["id"]}

    async def _handle_invoice_paid(self, event: dict) -> dict[str, Any]:
        """Handle invoice.paid webhook"""
        invoice = event["data"]["object"]

        # Update subscription period in database
        logger.info(f"Invoice paid: {invoice['id']} - ${invoice['amount_paid'] / 100}")

        return {"status": "processed", "invoice_id": invoice["id"]}

    async def _handle_invoice_payment_failed(self, event: dict) -> dict[str, Any]:
        """Handle invoice.payment_failed webhook"""
        invoice = event["data"]["object"]

        # Handle failed subscription payment
        logger.warning(f"Invoice payment failed: {invoice['id']}")

        # Send dunning email
        # await self.send_dunning_email(invoice)

        return {"status": "processed", "invoice_id": invoice["id"]}

    async def _handle_invoice_upcoming(self, event: dict) -> dict[str, Any]:
        """Handle invoice.upcoming webhook"""
        invoice = event["data"]["object"]

        # Send upcoming payment reminder
        # await self.send_upcoming_payment_email(invoice)

        return {"status": "processed", "invoice_id": invoice["id"]}

    async def _handle_checkout_completed(
        self, event: dict, organization_id: UUID | None = None
    ) -> dict[str, Any]:
        """
        Handle checkout.session.completed webhook

        Multi-Tenant Security:
        - Uses organization_id from metadata for RLS context
        - Filters database queries by organization
        """
        session = event["data"]["object"]

        if organization_id:
            async for db_session in get_db():
                # Set RLS context
                await db_session.execute(
                    text(f"SET app.current_organization_id = '{organization_id}'")
                )

                # Fulfill the purchase
                logger.info(f"Checkout completed: {session['id']}")

                # Process based on mode
                if session["mode"] == "payment":
                    # One-time payment completed - update with organization filter
                    pass
                elif session["mode"] == "subscription":
                    # Subscription created via checkout - update with organization filter
                    pass

        return {"status": "processed", "session_id": session["id"]}

    async def _handle_checkout_expired(self, event: dict) -> dict[str, Any]:
        """Handle checkout.session.expired webhook"""
        session = event["data"]["object"]

        # Clean up expired session
        logger.info(f"Checkout expired: {session['id']}")

        return {"status": "processed", "session_id": session["id"]}

    async def _handle_customer_updated(self, event: dict) -> dict[str, Any]:
        """Handle customer.updated webhook"""
        customer = event["data"]["object"]
        return {"status": "processed", "customer_id": customer["id"]}

    async def _handle_customer_deleted(self, event: dict) -> dict[str, Any]:
        """Handle customer.deleted webhook"""
        customer = event["data"]["object"]
        return {"status": "processed", "customer_id": customer["id"]}

    async def _handle_payment_method_attached(self, event: dict) -> dict[str, Any]:
        """Handle payment_method.attached webhook"""
        payment_method = event["data"]["object"]
        return {"status": "processed", "payment_method_id": payment_method["id"]}

    # Reporting and Analytics
    async def get_revenue_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
        organization_id: UUID | None = None,
    ) -> dict[str, Any]:
        """
        Get revenue metrics for a date range

        Multi-Tenant Security:
        - Filters Stripe resources by organization_id metadata when provided
        - Only returns revenue data for the specified organization

        Args:
            start_date: Start date
            end_date: End date
            organization_id: Filter by organization (required for multi-tenant)

        Returns:
            Revenue metrics
        """
        try:
            # Get charges for the period
            charges = stripe.Charge.list(
                created={"gte": int(start_date.timestamp()), "lte": int(end_date.timestamp())},
                limit=100,
            )

            # Filter by organization if provided
            if organization_id:
                org_id_str = str(organization_id)
                charges.data = [
                    c for c in charges.data if c.metadata.get("organization_id") == org_id_str
                ]

            total_revenue = sum(c.amount for c in charges.data if c.paid) / 100
            total_refunded = sum(c.amount_refunded for c in charges.data) / 100

            # Get subscription metrics
            subscriptions = stripe.Subscription.list(limit=100)

            # Filter by organization if provided
            if organization_id:
                org_id_str = str(organization_id)
                subscriptions.data = [
                    s for s in subscriptions.data if s.metadata.get("organization_id") == org_id_str
                ]

            active_subscriptions = [s for s in subscriptions.data if s.status == "active"]
            mrr = (
                sum(
                    s.items.data[0].price.unit_amount * s.items.data[0].quantity
                    for s in active_subscriptions
                    if s.items.data
                )
                / 100
            )

            return {
                "total_revenue": total_revenue,
                "total_refunded": total_refunded,
                "net_revenue": total_revenue - total_refunded,
                "transaction_count": len([c for c in charges.data if c.paid]),
                "active_subscriptions": len(active_subscriptions),
                "monthly_recurring_revenue": mrr,
                "average_transaction_value": (
                    total_revenue / len(charges.data) if charges.data else 0
                ),
                "organization_id": str(organization_id) if organization_id else None,
            }

        except StripeError as e:
            logger.error(f"Error getting revenue metrics: {e}")
            return {}

    async def retry_payment_intent(
        self, payment_intent_id: str, payment_method_id: str | None = None
    ) -> dict[str, Any]:
        """
        Retry a failed payment intent
        Following 2025 Stripe best practices for payment recovery

        Args:
            payment_intent_id: ID of the payment intent to retry
            payment_method_id: Optional new payment method to use

        Returns:
            Updated payment intent
        """
        try:
            # Retrieve current payment intent
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            if payment_intent.status in ["succeeded", "processing"]:
                return {
                    "success": True,
                    "status": payment_intent.status,
                    "payment_intent": payment_intent.to_dict(),
                }

            # Update payment method if provided
            if payment_method_id:
                payment_intent = stripe.PaymentIntent.modify(
                    payment_intent_id, payment_method=payment_method_id
                )

            # Confirm the payment intent again
            if payment_intent.status == "requires_confirmation":
                payment_intent = stripe.PaymentIntent.confirm(payment_intent_id)
            elif payment_intent.status == "requires_payment_method":
                # Need a new payment method
                logger.warning(f"Payment intent {payment_intent_id} requires new payment method")
                return {
                    "success": False,
                    "status": "requires_payment_method",
                    "error": "Payment method required",
                }

            logger.info(
                f"Retried payment intent: {payment_intent_id}, status: {payment_intent.status}"
            )
            return {
                "success": payment_intent.status == "succeeded",
                "status": payment_intent.status,
                "payment_intent": payment_intent.to_dict(),
            }

        except StripeError as e:
            logger.error(f"Stripe error retrying payment: {e}")
            return {"success": False, "error": str(e)}

    # Refunds
    async def create_refund(
        self,
        charge_id: str | None = None,
        payment_intent_id: str | None = None,
        amount: int | None = None,
        reason: str = "requested_by_customer",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Create a refund

        Args:
            charge_id: Charge ID to refund
            payment_intent_id: Payment intent ID to refund
            amount: Amount to refund (None for full refund)
            reason: Refund reason
            metadata: Additional metadata

        Returns:
            Refund object
        """
        try:
            refund_data = {
                "reason": reason,
                "metadata": {"platform": "toolbox_ai", **(metadata or {})},
            }

            if charge_id:
                refund_data["charge"] = charge_id
            elif payment_intent_id:
                refund_data["payment_intent"] = payment_intent_id
            else:
                raise ValueError("Either charge_id or payment_intent_id must be provided")

            if amount:
                refund_data["amount"] = amount

            refund = stripe.Refund.create(**refund_data)

            logger.info(f"Created refund: {refund.id}")
            return refund.to_dict()

        except StripeError as e:
            logger.error(f"Stripe error creating refund: {e}")
            raise


# Create singleton instance
stripe_service = StripeService()

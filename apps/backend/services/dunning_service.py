"""
Dunning Service for Failed Payments
Handles payment failure recovery, retry scheduling, and customer communication
Following 2025 best practices for payment recovery
@module dunning_service
@version 1.0.0
@since 2025-09-27
"""

import logging
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.backend.core.config import settings
from apps.backend.services.email import email_service
from apps.backend.services.stripe_service import stripe_service
from database.models.payment import (
    Customer,
    Invoice,
    Payment,
    PaymentStatus,
    Subscription,
    SubscriptionStatus,
)

logger = logging.getLogger(__name__)


class DunningState(str, Enum):
    """Dunning process states"""

    ACTIVE = "active"
    GRACE_PERIOD = "grace_period"
    RETRY_1 = "retry_1"
    RETRY_2 = "retry_2"
    RETRY_3 = "retry_3"
    FINAL_NOTICE = "final_notice"
    SUSPENDED = "suspended"
    CANCELED = "canceled"


class DunningService:
    """
    Service for handling payment failures and recovery attempts
    Implements smart retry logic with customer communication
    """

    def __init__(self):
        """Initialize dunning service with configuration"""
        self.max_retries = getattr(settings, "DUNNING_MAX_RETRIES", 3)
        self.grace_period_days = getattr(settings, "DUNNING_GRACE_PERIOD_DAYS", 3)
        self.retry_intervals = [1, 3, 5, 7]  # Days between retries
        self.final_notice_days = 10  # Days before cancellation

    async def process_failed_payment(self, payment_id: int, db: AsyncSession) -> dict[str, Any]:
        """
        Process a failed payment and initiate dunning process

        Args:
            payment_id: ID of the failed payment
            db: Database session

        Returns:
            Dunning process result
        """
        try:
            # Get payment with related data
            payment_query = (
                select(Payment)
                .where(Payment.id == payment_id)
                .options(selectinload(Payment.customer), selectinload(Payment.invoice))
            )
            payment = await db.execute(payment_query)
            payment = payment.scalar_one_or_none()

            if not payment:
                logger.error(f"Payment {payment_id} not found")
                return {"success": False, "error": "Payment not found"}

            # Check if already in dunning
            if payment.metadata and payment.metadata.get("dunning_state"):
                logger.info(f"Payment {payment_id} already in dunning process")
                return await self._continue_dunning(payment, db)

            # Initialize dunning process
            return await self._initiate_dunning(payment, db)

        except Exception as e:
            logger.error(f"Error processing failed payment: {e}")
            return {"success": False, "error": str(e)}

    async def _initiate_dunning(self, payment: Payment, db: AsyncSession) -> dict[str, Any]:
        """
        Initiate dunning process for a payment

        Args:
            payment: Payment object
            db: Database session

        Returns:
            Dunning initiation result
        """
        try:
            customer = payment.customer
            invoice = payment.invoice

            # Update payment metadata with dunning state
            dunning_metadata = {
                "dunning_state": DunningState.GRACE_PERIOD,
                "retry_count": 0,
                "dunning_started_at": datetime.now(timezone.utc).isoformat(),
                "next_retry_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            }

            if not payment.metadata:
                payment.metadata = {}
            payment.metadata.update(dunning_metadata)

            # Update subscription if applicable
            if invoice and invoice.subscription_id:
                subscription_query = select(Subscription).where(
                    Subscription.id == invoice.subscription_id
                )
                subscription = await db.execute(subscription_query)
                subscription = subscription.scalar_one_or_none()

                if subscription:
                    subscription.status = SubscriptionStatus.PAST_DUE
                    if not subscription.metadata:
                        subscription.metadata = {}
                    subscription.metadata["dunning_active"] = True

            # Send initial failure notification
            await self._send_payment_failed_email(
                customer=customer,
                payment=payment,
                invoice=invoice,
                retry_date=datetime.now(timezone.utc) + timedelta(days=1),
            )

            # Schedule first retry
            await self._schedule_retry(payment, days=1)

            await db.commit()

            logger.info(f"Dunning initiated for payment {payment.id}")
            return {
                "success": True,
                "payment_id": payment.id,
                "dunning_state": DunningState.GRACE_PERIOD,
                "next_retry": dunning_metadata["next_retry_at"],
            }

        except Exception as e:
            logger.error(f"Error initiating dunning: {e}")
            await db.rollback()
            return {"success": False, "error": str(e)}

    async def _continue_dunning(self, payment: Payment, db: AsyncSession) -> dict[str, Any]:
        """
        Continue existing dunning process

        Args:
            payment: Payment object
            db: Database session

        Returns:
            Dunning continuation result
        """
        try:
            payment.metadata.get("dunning_state")
            retry_count = payment.metadata.get("retry_count", 0)

            # Attempt payment retry
            retry_result = await self._retry_payment(payment)

            if retry_result["success"]:
                # Payment succeeded, end dunning
                return await self._end_dunning(payment, db, success=True)

            # Payment failed again
            retry_count += 1
            payment.metadata["retry_count"] = retry_count

            # Determine next action based on retry count
            if retry_count >= self.max_retries:
                # Max retries reached, move to final notice
                return await self._final_notice(payment, db)
            else:
                # Schedule next retry
                next_state = getattr(DunningState, f"RETRY_{retry_count}")
                payment.metadata["dunning_state"] = next_state

                days_until_retry = self.retry_intervals[
                    min(retry_count, len(self.retry_intervals) - 1)
                ]
                await self._schedule_retry(payment, days=days_until_retry)

                # Send retry notification
                await self._send_retry_notification(
                    payment=payment,
                    retry_number=retry_count,
                    next_retry_date=datetime.now(timezone.utc) + timedelta(days=days_until_retry),
                )

                await db.commit()

                return {
                    "success": False,
                    "payment_id": payment.id,
                    "dunning_state": next_state,
                    "retry_count": retry_count,
                    "next_retry": payment.metadata.get("next_retry_at"),
                }

        except Exception as e:
            logger.error(f"Error continuing dunning: {e}")
            await db.rollback()
            return {"success": False, "error": str(e)}

    async def _retry_payment(self, payment: Payment) -> dict[str, Any]:
        """
        Attempt to retry a failed payment

        Args:
            payment: Payment object

        Returns:
            Retry result
        """
        try:
            # Use Stripe service to retry payment
            if payment.stripe_payment_intent_id:
                result = await stripe_service.retry_payment_intent(
                    payment_intent_id=payment.stripe_payment_intent_id
                )

                if result.get("status") == "succeeded":
                    payment.status = PaymentStatus.SUCCEEDED
                    payment.paid_at = datetime.now(timezone.utc)
                    return {"success": True}

            return {"success": False}

        except Exception as e:
            logger.error(f"Payment retry failed: {e}")
            return {"success": False, "error": str(e)}

    async def _final_notice(self, payment: Payment, db: AsyncSession) -> dict[str, Any]:
        """
        Send final notice before subscription cancellation

        Args:
            payment: Payment object
            db: Database session

        Returns:
            Final notice result
        """
        try:
            payment.metadata["dunning_state"] = DunningState.FINAL_NOTICE
            cancellation_date = datetime.now(timezone.utc) + timedelta(days=self.final_notice_days)
            payment.metadata["scheduled_cancellation"] = cancellation_date.isoformat()

            # Send final notice email
            await self._send_final_notice_email(
                customer=payment.customer,
                payment=payment,
                cancellation_date=cancellation_date,
            )

            # Schedule cancellation
            await self._schedule_cancellation(payment, cancellation_date)

            await db.commit()

            logger.warning(f"Final notice sent for payment {payment.id}")
            return {
                "success": False,
                "payment_id": payment.id,
                "dunning_state": DunningState.FINAL_NOTICE,
                "scheduled_cancellation": cancellation_date.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error sending final notice: {e}")
            await db.rollback()
            return {"success": False, "error": str(e)}

    async def _end_dunning(
        self, payment: Payment, db: AsyncSession, success: bool
    ) -> dict[str, Any]:
        """
        End the dunning process

        Args:
            payment: Payment object
            db: Database session
            success: Whether payment was recovered

        Returns:
            End result
        """
        try:
            if success:
                # Payment recovered
                payment.metadata["dunning_state"] = None
                payment.metadata["dunning_ended_at"] = datetime.now(timezone.utc).isoformat()
                payment.metadata["dunning_result"] = "recovered"

                # Update subscription status
                if payment.invoice and payment.invoice.subscription_id:
                    subscription_query = select(Subscription).where(
                        Subscription.id == payment.invoice.subscription_id
                    )
                    subscription = await db.execute(subscription_query)
                    subscription = subscription.scalar_one_or_none()

                    if subscription:
                        subscription.status = SubscriptionStatus.ACTIVE
                        if subscription.metadata:
                            subscription.metadata["dunning_active"] = False

                # Send success email
                await self._send_payment_recovered_email(payment)

                logger.info(f"Payment {payment.id} recovered through dunning")

            else:
                # Payment not recovered, cancel subscription
                payment.metadata["dunning_state"] = DunningState.CANCELED
                payment.metadata["dunning_ended_at"] = datetime.now(timezone.utc).isoformat()
                payment.metadata["dunning_result"] = "canceled"

                # Cancel subscription
                if payment.invoice and payment.invoice.subscription_id:
                    await self._cancel_subscription(payment.invoice.subscription_id, db)

                # Send cancellation email
                await self._send_subscription_canceled_email(payment)

                logger.warning(f"Payment {payment.id} dunning failed, subscription canceled")

            await db.commit()

            return {
                "success": success,
                "payment_id": payment.id,
                "dunning_result": payment.metadata["dunning_result"],
            }

        except Exception as e:
            logger.error(f"Error ending dunning: {e}")
            await db.rollback()
            return {"success": False, "error": str(e)}

    async def _cancel_subscription(self, subscription_id: int, db: AsyncSession) -> None:
        """Cancel a subscription due to payment failure"""
        subscription_query = select(Subscription).where(Subscription.id == subscription_id)
        subscription = await db.execute(subscription_query)
        subscription = subscription.scalar_one_or_none()

        if subscription:
            subscription.status = SubscriptionStatus.CANCELED
            subscription.canceled_at = datetime.now(timezone.utc)
            subscription.cancellation_reason = "payment_failure_dunning"
            subscription.ended_at = datetime.now(timezone.utc)

            # Cancel in Stripe
            if subscription.stripe_subscription_id:
                await stripe_service.cancel_subscription(
                    subscription.stripe_subscription_id, immediately=True
                )

    async def _schedule_retry(self, payment: Payment, days: int) -> None:
        """Schedule a payment retry"""
        next_retry = datetime.now(timezone.utc) + timedelta(days=days)
        payment.metadata["next_retry_at"] = next_retry.isoformat()

        # In production, this would schedule a background job
        # For now, we're just updating metadata
        logger.info(f"Scheduled retry for payment {payment.id} at {next_retry}")

    async def _schedule_cancellation(self, payment: Payment, date: datetime) -> None:
        """Schedule subscription cancellation"""
        # In production, this would schedule a background job
        logger.info(f"Scheduled cancellation for payment {payment.id} at {date}")

    # Email notification methods
    async def _send_payment_failed_email(
        self,
        customer: Customer,
        payment: Payment,
        invoice: Invoice | None,
        retry_date: datetime,
    ) -> None:
        """Send payment failed notification"""
        await email_service.send_email(
            to_emails=customer.email,
            subject="Payment Failed - Action Required",
            template_name="payment_failed",
            template_context={
                "customer_name": customer.name,
                "amount": float(payment.amount),
                "retry_date": retry_date.strftime("%B %d, %Y"),
                "update_payment_url": f"{settings.FRONTEND_URL}/account/payment-methods",
            },
        )

    async def _send_retry_notification(
        self, payment: Payment, retry_number: int, next_retry_date: datetime
    ) -> None:
        """Send retry notification"""
        await email_service.send_email(
            to_emails=payment.customer.email,
            subject=f"Payment Retry #{retry_number} - Update Payment Method",
            template_name="payment_retry",
            template_context={
                "customer_name": payment.customer.name,
                "retry_number": retry_number,
                "next_retry_date": next_retry_date.strftime("%B %d, %Y"),
                "update_payment_url": f"{settings.FRONTEND_URL}/account/payment-methods",
            },
        )

    async def _send_final_notice_email(
        self, customer: Customer, payment: Payment, cancellation_date: datetime
    ) -> None:
        """Send final notice before cancellation"""
        await email_service.send_email(
            to_emails=customer.email,
            subject="Final Notice - Subscription Will Be Canceled",
            template_name="payment_final_notice",
            template_context={
                "customer_name": customer.name,
                "cancellation_date": cancellation_date.strftime("%B %d, %Y"),
                "amount": float(payment.amount),
                "update_payment_url": f"{settings.FRONTEND_URL}/account/payment-methods",
            },
        )

    async def _send_payment_recovered_email(self, payment: Payment) -> None:
        """Send payment recovery success email"""
        await email_service.send_email(
            to_emails=payment.customer.email,
            subject="Payment Successful - Thank You!",
            template_name="payment_recovered",
            template_context={
                "customer_name": payment.customer.name,
                "amount": float(payment.amount),
            },
        )

    async def _send_subscription_canceled_email(self, payment: Payment) -> None:
        """Send subscription cancellation email"""
        await email_service.send_email(
            to_emails=payment.customer.email,
            subject="Subscription Canceled",
            template_name="subscription_canceled",
            template_context={
                "customer_name": payment.customer.name,
                "reactivate_url": f"{settings.FRONTEND_URL}/pricing",
            },
        )

    async def check_pending_retries(self, db: AsyncSession) -> list[dict[str, Any]]:
        """
        Check for payments that need retry attempts
        Called by scheduled job

        Args:
            db: Database session

        Returns:
            List of retry results
        """
        try:
            # Find payments scheduled for retry
            now = datetime.now(timezone.utc)

            payments_query = select(Payment).where(
                and_(Payment.status == PaymentStatus.FAILED, Payment.metadata.isnot(None))
            )

            result = await db.execute(payments_query)
            payments = result.scalars().all()

            retry_results = []

            for payment in payments:
                if payment.metadata and payment.metadata.get("next_retry_at"):
                    next_retry = datetime.fromisoformat(payment.metadata["next_retry_at"])

                    if next_retry <= now:
                        # Time to retry
                        result = await self._continue_dunning(payment, db)
                        retry_results.append(result)

            return retry_results

        except Exception as e:
            logger.error(f"Error checking pending retries: {e}")
            return []


# Create singleton instance
dunning_service = DunningService()

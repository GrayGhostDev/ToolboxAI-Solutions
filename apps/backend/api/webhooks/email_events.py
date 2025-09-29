"""
Email Event Webhooks
Handles bounce, complaint, and other email event notifications from SendGrid
"""

import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field

from apps.backend.config import settings
from apps.backend.services.email_queue import email_queue

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/email", tags=["Email Webhooks"])


class EmailEvent(BaseModel):
    """SendGrid event model"""
    email: EmailStr
    event: str
    timestamp: int
    sg_message_id: Optional[str] = Field(None, alias="sg_message_id")
    sg_event_id: Optional[str] = Field(None, alias="sg_event_id")
    category: Optional[List[str]] = None
    reason: Optional[str] = None
    status: Optional[str] = None
    attempt: Optional[int] = None
    response: Optional[str] = None
    tls: Optional[int] = None
    ip: Optional[str] = None
    useragent: Optional[str] = None
    url: Optional[str] = None
    url_offset: Optional[Dict[str, int]] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        populate_by_name = True


class SendGridWebhookValidator:
    """Validates SendGrid webhook signatures"""

    @staticmethod
    def validate_signature(
        body: bytes,
        signature: str,
        timestamp: str,
        webhook_key: str
    ) -> bool:
        """
        Validate SendGrid webhook signature

        Args:
            body: Raw request body
            signature: Signature from header
            timestamp: Timestamp from header
            webhook_key: Webhook verification key

        Returns:
            True if valid, False otherwise
        """
        try:
            # Concatenate timestamp and body
            signed_content = timestamp.encode() + body

            # Generate expected signature
            expected_signature = hmac.new(
                webhook_key.encode(),
                signed_content,
                hashlib.sha256
            ).hexdigest()

            # Compare signatures
            return hmac.compare_digest(expected_signature, signature)

        except Exception as e:
            logger.error(f"Signature validation error: {e}")
            return False


# Initialize validator
validator = SendGridWebhookValidator()


async def verify_sendgrid_webhook(
    request: Request,
    x_twilio_email_event_webhook_signature: Optional[str] = Header(None),
    x_twilio_email_event_webhook_timestamp: Optional[str] = Header(None)
) -> bytes:
    """
    Dependency to verify SendGrid webhook signature

    Args:
        request: FastAPI request
        x_twilio_email_event_webhook_signature: Signature header
        x_twilio_email_event_webhook_timestamp: Timestamp header

    Returns:
        Raw request body

    Raises:
        HTTPException: If verification fails
    """
    # Get raw body
    body = await request.body()

    # Skip validation in development if webhook key not set
    webhook_key = getattr(settings, "SENDGRID_WEBHOOK_KEY", None)
    if not webhook_key:
        logger.warning("SendGrid webhook key not configured, skipping validation")
        return body

    # Validate signature
    if not x_twilio_email_event_webhook_signature or not x_twilio_email_event_webhook_timestamp:
        logger.error("Missing SendGrid webhook headers")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing webhook signature headers"
        )

    if not validator.validate_signature(
        body,
        x_twilio_email_event_webhook_signature,
        x_twilio_email_event_webhook_timestamp,
        webhook_key
    ):
        logger.error("Invalid SendGrid webhook signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature"
        )

    return body


@router.post("/sendgrid", status_code=status.HTTP_200_OK)
async def handle_sendgrid_events(
    body: bytes = Depends(verify_sendgrid_webhook)
):
    """
    Handle SendGrid webhook events

    Events handled:
    - bounce: Email bounced
    - dropped: Email dropped
    - deferred: Email temporarily delayed
    - delivered: Email delivered
    - open: Email opened
    - click: Link clicked
    - spamreport: Marked as spam
    - unsubscribe: User unsubscribed
    - group_unsubscribe: Group unsubscribe
    - group_resubscribe: Group resubscribe
    """
    try:
        # Parse events
        events = json.loads(body)
        if not isinstance(events, list):
            events = [events]

        # Process each event
        for event_data in events:
            try:
                event = EmailEvent(**event_data)
                await process_email_event(event)
            except Exception as e:
                logger.error(f"Error processing event: {e}, data: {event_data}")

        return JSONResponse(
            content={"status": "success", "events_processed": len(events)},
            status_code=status.HTTP_200_OK
        )

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    except Exception as e:
        logger.error(f"Error handling SendGrid webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


async def process_email_event(event: EmailEvent):
    """
    Process individual email event

    Args:
        event: Email event to process
    """
    try:
        event_type = event.event.lower()
        email_address = event.email
        timestamp = datetime.fromtimestamp(event.timestamp)

        logger.info(f"Processing {event_type} event for {email_address}")

        # Handle different event types
        if event_type == "bounce":
            await handle_bounce_event(event)

        elif event_type == "dropped":
            await handle_dropped_event(event)

        elif event_type == "spamreport":
            await handle_spam_report_event(event)

        elif event_type == "unsubscribe":
            await handle_unsubscribe_event(event)

        elif event_type == "deferred":
            await handle_deferred_event(event)

        elif event_type == "delivered":
            await handle_delivered_event(event)

        elif event_type == "open":
            await handle_open_event(event)

        elif event_type == "click":
            await handle_click_event(event)

        elif event_type in ["group_unsubscribe", "group_resubscribe"]:
            await handle_group_subscription_event(event)

        else:
            logger.warning(f"Unhandled event type: {event_type}")

        # Store event for analytics
        await store_event_for_analytics(event)

    except Exception as e:
        logger.error(f"Error processing {event.event} event: {e}")


async def handle_bounce_event(event: EmailEvent):
    """Handle bounce event"""
    # Determine bounce type
    bounce_type = "hard" if "5." in (event.status or "") else "soft"

    # Handle bounce in queue service
    await email_queue.handle_bounce(
        email_address=event.email,
        bounce_type=bounce_type,
        details={
            "reason": event.reason,
            "status": event.status,
            "response": event.response,
            "timestamp": event.timestamp
        }
    )

    logger.warning(f"Bounce ({bounce_type}): {event.email} - {event.reason}")


async def handle_dropped_event(event: EmailEvent):
    """Handle dropped email event"""
    # Treat drops as hard bounces
    await email_queue.handle_bounce(
        email_address=event.email,
        bounce_type="hard",
        details={
            "reason": event.reason or "dropped",
            "timestamp": event.timestamp
        }
    )

    logger.warning(f"Dropped: {event.email} - {event.reason}")


async def handle_spam_report_event(event: EmailEvent):
    """Handle spam report event"""
    await email_queue.handle_complaint(
        email_address=event.email,
        complaint_type="spam",
        details={
            "timestamp": event.timestamp,
            "ip": event.ip,
            "useragent": event.useragent
        }
    )

    logger.warning(f"Spam report: {event.email}")


async def handle_unsubscribe_event(event: EmailEvent):
    """Handle unsubscribe event"""
    # Add to suppression list
    await email_queue._add_to_suppression_list(
        email_address=event.email,
        reason="unsubscribe"
    )

    # Store unsubscribe record
    # You may want to update user preferences in database here

    logger.info(f"Unsubscribe: {event.email}")


async def handle_deferred_event(event: EmailEvent):
    """Handle deferred delivery event"""
    # Log deferred attempts
    logger.warning(
        f"Deferred delivery: {event.email} - "
        f"Attempt {event.attempt} - {event.response}"
    )

    # If too many deferrals, consider as soft bounce
    if event.attempt and event.attempt > 5:
        await email_queue.handle_bounce(
            email_address=event.email,
            bounce_type="soft",
            details={
                "reason": "excessive_deferrals",
                "attempts": event.attempt,
                "response": event.response,
                "timestamp": event.timestamp
            }
        )


async def handle_delivered_event(event: EmailEvent):
    """Handle successful delivery event"""
    # Update metrics
    await email_queue._increment_metric("delivered")

    # Log delivery
    logger.info(f"Delivered: {event.email} - {event.response}")


async def handle_open_event(event: EmailEvent):
    """Handle email open event"""
    # Update metrics
    await email_queue._increment_metric("opens")

    # Store engagement data
    logger.debug(f"Opened: {event.email} at {event.timestamp}")


async def handle_click_event(event: EmailEvent):
    """Handle link click event"""
    # Update metrics
    await email_queue._increment_metric("clicks")

    # Store engagement data
    logger.debug(f"Click: {event.email} - URL: {event.url}")


async def handle_group_subscription_event(event: EmailEvent):
    """Handle group subscription changes"""
    action = "unsubscribed" if "unsubscribe" in event.event else "resubscribed"

    logger.info(f"Group {action}: {event.email}")

    # Update user preferences based on group
    # Implementation depends on your group structure


async def store_event_for_analytics(event: EmailEvent):
    """
    Store event for analytics and reporting

    This can be extended to store in database or analytics service
    """
    try:
        # Store in Redis for short-term analytics
        if email_queue.redis_client:
            event_key = f"email_events:{event.email}:{event.event}"
            await email_queue.redis_client.lpush(
                event_key,
                json.dumps({
                    "timestamp": event.timestamp,
                    "sg_message_id": event.sg_message_id,
                    "sg_event_id": event.sg_event_id,
                    "category": event.category,
                    "metadata": event.metadata
                })
            )
            # Expire after 30 days
            await email_queue.redis_client.expire(event_key, 86400 * 30)

    except Exception as e:
        logger.error(f"Error storing analytics event: {e}")


@router.get("/stats/{email}")
async def get_email_stats(email: EmailStr):
    """
    Get statistics for a specific email address

    Args:
        email: Email address to get stats for

    Returns:
        Email statistics including bounces, complaints, opens, clicks
    """
    try:
        stats = {
            "email": email,
            "suppressed": await email_queue.is_suppressed(email),
            "events": {}
        }

        if email_queue.redis_client:
            # Get bounce information
            bounce_key = f"{email_queue.queue_prefix}:bounces:{email}"
            bounces = await email_queue.redis_client.hgetall(bounce_key)
            if bounces:
                stats["bounces"] = bounces

            # Get complaint information
            complaint_key = f"{email_queue.queue_prefix}:complaints:{email}"
            complaints = await email_queue.redis_client.hgetall(complaint_key)
            if complaints:
                stats["complaints"] = complaints

            # Get recent events
            for event_type in ["delivered", "open", "click", "bounce", "spamreport"]:
                event_key = f"email_events:{email}:{event_type}"
                events = await email_queue.redis_client.lrange(event_key, 0, 9)
                if events:
                    stats["events"][event_type] = [
                        json.loads(e) for e in events
                    ]

        return JSONResponse(content=stats)

    except Exception as e:
        logger.error(f"Error getting email stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve email statistics"
        )


@router.post("/test-webhook")
async def test_webhook_endpoint():
    """
    Test webhook endpoint for development

    Simulates various SendGrid events for testing
    """
    test_events = [
        {
            "email": "test@example.com",
            "event": "delivered",
            "timestamp": int(datetime.utcnow().timestamp()),
            "sg_message_id": "test-msg-001",
            "sg_event_id": "test-event-001",
            "response": "250 OK"
        },
        {
            "email": "bounce@example.com",
            "event": "bounce",
            "timestamp": int(datetime.utcnow().timestamp()),
            "sg_message_id": "test-msg-002",
            "sg_event_id": "test-event-002",
            "reason": "550 5.1.1 User unknown",
            "status": "5.1.1"
        }
    ]

    for event_data in test_events:
        event = EmailEvent(**event_data)
        await process_email_event(event)

    return JSONResponse(
        content={
            "status": "success",
            "message": "Test events processed",
            "events": len(test_events)
        }
    )
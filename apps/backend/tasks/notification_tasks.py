"""
Notification Tasks
==================
Background tasks for sending notifications via Pusher and webhooks
"""

import json
from datetime import datetime
from typing import Any

import httpx
from celery import group, shared_task
from celery.utils.log import get_task_logger

from apps.backend.core.database import SessionLocal
from apps.backend.services.pusher import pusher_service as pusher_client
from database.models import Notification

logger = get_task_logger(__name__)


@shared_task(
    bind=True,
    name="tasks.send_notification",
    max_retries=3,
    default_retry_delay=30,
    queue="notifications",
    priority=7,
)
def send_notification(
    self,
    user_id: str,
    notification_type: str,
    title: str,
    message: str,
    data: dict[str, Any] | None = None,
    channels: list[str] | None = None,
) -> dict[str, Any]:
    """
    Send notification to a specific user

    Args:
        user_id: Target user ID
        notification_type: Type of notification (info, warning, error, success)
        title: Notification title
        message: Notification message
        data: Additional data to include
        channels: Delivery channels (pusher, email, webhook)

    Returns:
        Notification delivery results
    """
    try:
        task_id = self.request.id
        channels = channels or ["pusher"]
        delivery_results = {}

        # Save notification to database
        notification_id = None
        try:
            with SessionLocal() as session:
                notification = Notification(
                    user_id=user_id,
                    type=notification_type,
                    title=title,
                    message=message,
                    data=json.dumps(data or {}),
                    status="pending",
                    created_at=datetime.utcnow(),
                )
                session.add(notification)
                session.commit()
                notification_id = notification.id
                logger.info(f"Notification {notification_id} created for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to save notification: {e}")

        # Send via Pusher
        if "pusher" in channels and pusher_client:
            try:
                # Send to user's private channel
                pusher_result = pusher_client.trigger(
                    f"private-user-{user_id}",
                    "notification",
                    {
                        "id": notification_id,
                        "type": notification_type,
                        "title": title,
                        "message": message,
                        "data": data,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )

                delivery_results["pusher"] = {
                    "success": True,
                    "message_id": pusher_result.get("message_id"),
                }
                logger.info(f"Pusher notification sent to user {user_id}")

            except Exception as e:
                logger.error(f"Pusher delivery failed: {e}")
                delivery_results["pusher"] = {"success": False, "error": str(e)}

        # Send via Email
        if "email" in channels:
            try:
                from apps.backend.workers.tasks.email_tasks import (
                    send_notification_email,
                )

                # Queue email notification task
                email_result = send_notification_email.apply_async(
                    kwargs={
                        "user_id": user_id,
                        "notification_type": notification_type,
                        "title": title,
                        "message": message,
                        "action_url": data.get("action_url") if data else None,
                        "organization_id": data.get("organization_id") if data else None,
                    },
                    countdown=5,  # Delay email by 5 seconds to ensure Pusher notification arrives first
                )

                delivery_results["email"] = {
                    "success": True,
                    "message_id": str(email_result.id),
                    "status": "queued",
                }
                logger.info(f"Email notification queued for user {user_id}: {title}")

            except Exception as e:
                logger.error(f"Email delivery failed: {e}")
                delivery_results["email"] = {"success": False, "error": str(e)}

        # Send via Webhook
        if "webhook" in channels and data and data.get("webhook_url"):
            try:
                with httpx.Client() as client:
                    webhook_response = client.post(
                        data["webhook_url"],
                        json={
                            "notification_id": notification_id,
                            "user_id": user_id,
                            "type": notification_type,
                            "title": title,
                            "message": message,
                            "data": data,
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                        headers={
                            "Content-Type": "application/json",
                            "X-Notification-Type": notification_type,
                        },
                        timeout=10.0,
                    )

                    delivery_results["webhook"] = {
                        "success": webhook_response.status_code == 200,
                        "status_code": webhook_response.status_code,
                    }
                    logger.info(f"Webhook notification sent to {data['webhook_url']}")

            except Exception as e:
                logger.error(f"Webhook delivery failed: {e}")
                delivery_results["webhook"] = {"success": False, "error": str(e)}

        # Update notification status in database
        if notification_id:
            try:
                with SessionLocal() as session:
                    notification = session.query(Notification).filter_by(id=notification_id).first()

                    if notification:
                        # Check if any channel succeeded
                        any_success = any(
                            result.get("success", False) for result in delivery_results.values()
                        )

                        notification.status = "delivered" if any_success else "failed"
                        notification.delivery_results = json.dumps(delivery_results)
                        notification.delivered_at = datetime.utcnow() if any_success else None
                        session.commit()

            except Exception as e:
                logger.error(f"Failed to update notification status: {e}")

        return {
            "status": "success",
            "task_id": task_id,
            "notification_id": notification_id,
            "user_id": user_id,
            "channels_attempted": channels,
            "delivery_results": delivery_results,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Notification task failed: {e}")
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    name="tasks.send_bulk_notifications",
    max_retries=2,
    default_retry_delay=60,
    queue="notifications",
    priority=5,
)
def send_bulk_notifications(
    self,
    user_ids: list[str],
    notification_type: str,
    title: str,
    message: str,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Send notifications to multiple users in parallel

    Args:
        user_ids: List of target user IDs
        notification_type: Type of notification
        title: Notification title
        message: Notification message
        data: Additional data

    Returns:
        Bulk send results
    """
    try:
        task_id = self.request.id

        # Create a group of individual notification tasks
        job = group(
            send_notification.s(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                message=message,
                data=data,
                channels=["pusher"],  # Use Pusher for bulk notifications
            )
            for user_id in user_ids
        )

        # Execute all tasks in parallel
        result = job.apply_async()

        # Wait for results with timeout
        try:
            results = result.get(timeout=30)
            successful = sum(1 for r in results if r.get("status") == "success")
            failed = len(results) - successful

            logger.info(
                f"Bulk notification sent to {len(user_ids)} users: "
                f"{successful} successful, {failed} failed"
            )

            return {
                "status": "success",
                "task_id": task_id,
                "total_users": len(user_ids),
                "successful": successful,
                "failed": failed,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Bulk notification timeout or error: {e}")
            return {
                "status": "partial",
                "task_id": task_id,
                "total_users": len(user_ids),
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    except Exception as e:
        logger.error(f"Bulk notification task failed: {e}")
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    name="tasks.process_webhook_event",
    max_retries=3,
    default_retry_delay=30,
    queue="webhooks",
    priority=6,
)
def process_webhook_event(
    self, event_type: str, event_data: dict[str, Any], source: str = "external"
) -> dict[str, Any]:
    """
    Process incoming webhook events

    Args:
        event_type: Type of webhook event
        event_data: Event payload
        source: Source of the webhook

    Returns:
        Processing results
    """
    try:
        task_id = self.request.id
        logger.info(f"Processing webhook event: {event_type} from {source}")

        # Route based on event type
        if event_type == "pusher.channel_occupied":
            # Handle Pusher channel occupied event
            channel = event_data.get("channel")
            logger.info(f"Channel {channel} is now occupied")

            # Could trigger additional actions here
            if channel.startswith("private-classroom-"):
                channel.replace("private-classroom-", "")
                # Notify instructor that students have joined
                # This would typically update classroom status

        elif event_type == "pusher.channel_vacated":
            # Handle Pusher channel vacated event
            channel = event_data.get("channel")
            logger.info(f"Channel {channel} is now vacant")

        elif event_type == "roblox.place_updated":
            # Handle Roblox place update webhook
            place_id = event_data.get("place_id")
            universe_id = event_data.get("universe_id")

            logger.info(f"Roblox place {place_id} updated in universe {universe_id}")

            # Trigger sync task
            from apps.backend.tasks.roblox_tasks import sync_roblox_environment

            sync_roblox_environment.delay(
                universe_id=universe_id, place_id=place_id, sync_type="incremental"
            )

        elif event_type == "stripe.payment_succeeded":
            # Handle Stripe payment webhook (placeholder)
            customer_id = event_data.get("customer_id")
            amount = event_data.get("amount")

            logger.info(f"Payment succeeded for customer {customer_id}: ${amount/100:.2f}")

            # Update user subscription status
            # Send confirmation notification

        elif event_type == "github.push":
            # Handle GitHub push webhook
            repository = event_data.get("repository", {}).get("name")
            branch = event_data.get("ref", "").replace("refs/heads/", "")

            logger.info(f"GitHub push to {repository}/{branch}")

            # Could trigger CI/CD pipeline or content sync

        else:
            logger.warning(f"Unhandled webhook event type: {event_type}")

        # Store webhook event for audit
        try:
            from apps.backend.core.database import SessionLocal
            from database.models import WebhookEvent

            with SessionLocal() as session:
                webhook_event = WebhookEvent(
                    event_type=event_type,
                    source=source,
                    payload=json.dumps(event_data),
                    processed_at=datetime.utcnow(),
                    status="processed",
                )
                session.add(webhook_event)
                session.commit()

        except Exception as e:
            logger.error(f"Failed to store webhook event: {e}")

        return {
            "status": "success",
            "task_id": task_id,
            "event_type": event_type,
            "source": source,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise self.retry(exc=e)

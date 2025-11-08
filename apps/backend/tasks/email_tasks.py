"""
Email Tasks
===========
Background tasks for email sending and notifications
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from celery import shared_task
from celery.utils.log import get_task_logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.backend.core.database import get_db
from apps.backend.core.config import settings
from apps.backend.services.email_service import email_service
from apps.backend.services.email_queue import email_queue, EmailPriority

logger = get_task_logger(__name__)


@shared_task(
    bind=True,
    name="tasks.send_pending_emails",
    max_retries=3,
    default_retry_delay=60,
    queue="email",
    priority=5,
)
def send_pending_emails(self, batch_size: int = 50) -> Dict[str, Any]:
    """
    Process and send pending emails from queue

    Args:
        batch_size: Number of emails to process in this batch

    Returns:
        Dictionary with processing statistics
    """

    async def process_queue_batch():
        """Async helper to process email queue"""
        try:
            # Connect to Redis queue
            await email_queue.connect()

            emails_processed = 0
            emails_sent = 0
            emails_failed = 0

            # Process priority queues in order (CRITICAL -> HIGH -> NORMAL -> LOW -> BULK)
            for priority in [EmailPriority.CRITICAL, EmailPriority.HIGH, EmailPriority.NORMAL]:
                if emails_processed >= batch_size:
                    break

                # Get queue for this priority
                queue_name = email_queue.queues[priority]

                # Process emails from this priority queue
                batch_limit = min(batch_size - emails_processed, 10)

                for _ in range(batch_limit):
                    if not email_queue.redis_client:
                        break

                    try:
                        # Pop job from queue
                        job_data = await email_queue.redis_client.rpop(queue_name)
                        if not job_data:
                            break

                        # Parse and process job
                        from apps.backend.services.email_queue import EmailJob
                        job = EmailJob.parse_raw(job_data)

                        await email_queue._process_email_job(job)

                        emails_sent += 1
                        emails_processed += 1

                    except Exception as e:
                        logger.error(f"Failed to process email from {priority} queue: {e}")
                        emails_failed += 1
                        emails_processed += 1

            return {
                "emails_processed": emails_processed,
                "emails_sent": emails_sent,
                "emails_failed": emails_failed
            }

        finally:
            # Don't disconnect - leave connection open for reuse
            pass

    try:
        logger.info(f"Processing pending emails (batch size: {batch_size})")

        # Run async queue processing
        result = asyncio.run(process_queue_batch())

        return {
            "status": "success",
            **result,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to process pending emails: {e}")
        raise self.retry(exc=e, countdown=60)


@shared_task(
    bind=True,
    name="tasks.send_email",
    max_retries=3,
    default_retry_delay=30,
    queue="email",
    priority=6,
)
def send_email(
    self,
    to_email: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None,
    attachments: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """
    Send a single email

    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Plain text email body
        html_body: Optional HTML email body
        attachments: Optional list of attachments

    Returns:
        Dictionary with send status
    """
    try:
        logger.info(f"Sending email to {to_email}: {subject}")

        # Call async email service from sync Celery task
        result = asyncio.run(email_service.send_email(
            to_emails=to_email,
            subject=subject,
            text_content=body,
            html_content=html_body,
            attachments=attachments if attachments else None
        ))

        return {
            "status": "success" if result.get("success") else "failed",
            "to": to_email,
            "subject": subject,
            "sent_at": datetime.utcnow().isoformat(),
            "message_id": result.get("message_id"),
            "result": result
        }

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        raise self.retry(exc=e, countdown=30)


@shared_task(
    bind=True,
    name="tasks.send_bulk_emails",
    max_retries=2,
    default_retry_delay=120,
    queue="email",
    priority=3,
)
def send_bulk_emails(
    self,
    recipients: List[str],
    subject: str,
    body: str,
    html_body: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send bulk emails to multiple recipients

    Args:
        recipients: List of recipient email addresses
        subject: Email subject
        body: Plain text email body
        html_body: Optional HTML email body

    Returns:
        Dictionary with bulk send statistics
    """
    try:
        logger.info(f"Sending bulk email to {len(recipients)} recipients")

        sent_count = 0
        failed_count = 0

        # Process each recipient
        for recipient in recipients:
            try:
                result = asyncio.run(email_service.send_email(
                    to_emails=recipient,
                    subject=subject,
                    text_content=body,
                    html_content=html_body
                ))

                if result.get("success"):
                    sent_count += 1
                else:
                    failed_count += 1
                    logger.warning(f"Bulk email to {recipient} reported not successful")

            except Exception as e:
                logger.error(f"Failed to send bulk email to {recipient}: {e}")
                failed_count += 1
                # Continue with other recipients

        return {
            "status": "success",
            "total_recipients": len(recipients),
            "sent": sent_count,
            "failed": failed_count,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to send bulk emails: {e}")
        raise self.retry(exc=e, countdown=120)

"""
Email Queue Service with Retry Logic
Implements reliable email delivery with retry mechanism, dead letter queue,
and monitoring capabilities for production environments.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import uuid4

import redis.asyncio as redis
from pydantic import BaseModel, EmailStr, Field

from apps.backend.core.cache import CacheService
from apps.backend.core.config import settings
from apps.backend.services.email import email_service

logger = logging.getLogger(__name__)


class EmailPriority(str, Enum):
    """Email priority levels for queue processing"""

    CRITICAL = "critical"  # System critical emails (password reset, security)
    HIGH = "high"  # Transactional emails (payments, confirmations)
    NORMAL = "normal"  # Standard communications
    LOW = "low"  # Newsletters, marketing
    BULK = "bulk"  # Mass mailings


class EmailStatus(str, Enum):
    """Email processing status"""

    QUEUED = "queued"
    PROCESSING = "processing"
    SENT = "sent"
    FAILED = "failed"
    RETRY = "retry"
    DEAD_LETTER = "dead_letter"
    BOUNCED = "bounced"
    COMPLAINED = "complained"


class EmailJob(BaseModel):
    """Email job model for queue processing"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    to_email: EmailStr | list[EmailStr]
    subject: str
    template_name: str | None = None
    template_data: dict[str, Any] | None = None
    html_content: str | None = None
    text_content: str | None = None
    from_email: EmailStr | None = None
    from_name: str | None = None
    reply_to: EmailStr | None = None
    cc: list[EmailStr] | None = None
    bcc: list[EmailStr] | None = None
    attachments: list[dict[str, Any]] | None = None
    priority: EmailPriority = EmailPriority.NORMAL
    status: EmailStatus = EmailStatus.QUEUED
    attempts: int = 0
    max_retries: int = 3
    retry_delay: int = 60  # Base delay in seconds
    created_at: datetime = Field(default_factory=datetime.utcnow)
    scheduled_for: datetime | None = None
    sent_at: datetime | None = None
    last_attempt_at: datetime | None = None
    error_message: str | None = None
    metadata: dict[str, Any] | None = None
    correlation_id: str | None = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class EmailQueueService:
    """
    Email queue service with retry logic and monitoring

    Features:
    - Priority-based queue processing
    - Exponential backoff retry mechanism
    - Dead letter queue for failed emails
    - Bounce and complaint handling
    - Real-time monitoring and metrics
    - Scheduled email support
    """

    def __init__(self):
        self.redis_client: redis.Redis | None = None
        self.cache_service = CacheService()
        self.processing = False
        self._initialize_queues()

    def _initialize_queues(self):
        """Initialize Redis queue names"""
        self.queue_prefix = "email_queue"
        self.queues = {
            EmailPriority.CRITICAL: f"{self.queue_prefix}:critical",
            EmailPriority.HIGH: f"{self.queue_prefix}:high",
            EmailPriority.NORMAL: f"{self.queue_prefix}:normal",
            EmailPriority.LOW: f"{self.queue_prefix}:low",
            EmailPriority.BULK: f"{self.queue_prefix}:bulk",
        }
        self.retry_queue = f"{self.queue_prefix}:retry"
        self.dead_letter_queue = f"{self.queue_prefix}:dead_letter"
        self.processing_set = f"{self.queue_prefix}:processing"
        self.metrics_key = f"{self.queue_prefix}:metrics"

    async def connect(self):
        """Connect to Redis"""
        if not self.redis_client:
            try:
                redis_url = settings.REDIS_URL or "redis://localhost:6379/0"
                self.redis_client = await redis.from_url(
                    redis_url, encoding="utf-8", decode_responses=True
                )
                await self.redis_client.ping()
                logger.info("Email queue service connected to Redis")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                # Fallback to in-memory queue if Redis unavailable
                self.redis_client = None

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.aclose()
            self.redis_client = None

    async def enqueue(
        self,
        to_email: str | list[str],
        subject: str,
        template_name: str | None = None,
        template_data: dict[str, Any] | None = None,
        html_content: str | None = None,
        text_content: str | None = None,
        priority: EmailPriority = EmailPriority.NORMAL,
        scheduled_for: datetime | None = None,
        max_retries: int = 3,
        metadata: dict[str, Any] | None = None,
        **kwargs,
    ) -> str:
        """
        Add email to queue for processing

        Args:
            to_email: Recipient email(s)
            subject: Email subject
            template_name: Optional template name
            template_data: Optional template variables
            html_content: Optional HTML content
            text_content: Optional plain text content
            priority: Email priority level
            scheduled_for: Optional scheduled send time
            max_retries: Maximum retry attempts
            metadata: Optional metadata
            **kwargs: Additional email parameters

        Returns:
            Job ID
        """
        await self.connect()

        # Create email job
        job = EmailJob(
            to_email=to_email,
            subject=subject,
            template_name=template_name,
            template_data=template_data,
            html_content=html_content,
            text_content=text_content,
            priority=priority,
            scheduled_for=scheduled_for,
            max_retries=max_retries,
            metadata=metadata,
            **kwargs,
        )

        # Add to appropriate queue
        if self.redis_client:
            try:
                # Scheduled emails go to a sorted set
                if scheduled_for and scheduled_for > datetime.utcnow():
                    score = scheduled_for.timestamp()
                    await self.redis_client.zadd(
                        f"{self.queue_prefix}:scheduled", {job.json(): score}
                    )
                    logger.info(f"Email {job.id} scheduled for {scheduled_for}")
                else:
                    # Add to priority queue
                    queue_name = self.queues[priority]
                    await self.redis_client.lpush(queue_name, job.json())
                    logger.info(f"Email {job.id} added to {priority} queue")

                # Update metrics
                await self._increment_metric("queued")
                await self._increment_metric(f"queued_{priority}")

                return job.id

            except Exception as e:
                logger.error(f"Failed to enqueue email: {e}")
                # Fallback to direct sending
                return await self._send_direct(job)
        else:
            # No Redis, send directly
            return await self._send_direct(job)

    async def _send_direct(self, job: EmailJob) -> str:
        """Send email directly without queue"""
        try:
            if isinstance(job.to_email, list):
                to_emails = job.to_email
            else:
                to_emails = [job.to_email]

            for to_email in to_emails:
                if job.template_name:
                    await email_service.send_templated_email(
                        to_email=to_email,
                        subject=job.subject,
                        template_name=job.template_name,
                        template_data=job.template_data or {},
                        from_email=job.from_email,
                        from_name=job.from_name,
                    )
                else:
                    await email_service.send_email(
                        to_email=to_email,
                        subject=job.subject,
                        html_content=job.html_content,
                        text_content=job.text_content,
                        from_email=job.from_email,
                        from_name=job.from_name,
                    )

            logger.info(f"Email {job.id} sent directly (no queue)")
            return job.id

        except Exception as e:
            logger.error(f"Failed to send email directly: {e}")
            raise

    async def process_queue(self):
        """Main queue processing loop"""
        if self.processing:
            logger.warning("Queue processing already running")
            return

        self.processing = True
        await self.connect()

        try:
            while self.processing:
                # Process scheduled emails first
                await self._process_scheduled()

                # Process priority queues in order
                for priority in EmailPriority.__members__.values():
                    await self._process_priority_queue(priority)

                # Process retry queue
                await self._process_retry_queue()

                # Small delay between cycles
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Queue processing error: {e}")
        finally:
            self.processing = False

    async def _process_priority_queue(self, priority: EmailPriority):
        """Process emails from a priority queue"""
        if not self.redis_client:
            return

        queue_name = self.queues[priority]
        batch_size = self._get_batch_size(priority)

        for _ in range(batch_size):
            try:
                # Pop from queue
                job_data = await self.redis_client.rpop(queue_name)
                if not job_data:
                    break

                # Add to processing set
                await self.redis_client.sadd(self.processing_set, job_data)

                # Process email
                job = EmailJob.parse_raw(job_data)
                await self._process_email_job(job)

                # Remove from processing set
                await self.redis_client.srem(self.processing_set, job_data)

            except Exception as e:
                logger.error(f"Error processing {priority} queue: {e}")

    def _get_batch_size(self, priority: EmailPriority) -> int:
        """Get batch size based on priority"""
        batch_sizes = {
            EmailPriority.CRITICAL: 10,
            EmailPriority.HIGH: 5,
            EmailPriority.NORMAL: 3,
            EmailPriority.LOW: 2,
            EmailPriority.BULK: 1,
        }
        return batch_sizes.get(priority, 1)

    async def _process_email_job(self, job: EmailJob):
        """Process individual email job"""
        try:
            job.status = EmailStatus.PROCESSING
            job.attempts += 1
            job.last_attempt_at = datetime.utcnow()

            # Send email
            if isinstance(job.to_email, list):
                to_emails = job.to_email
            else:
                to_emails = [job.to_email]

            for to_email in to_emails:
                if job.template_name:
                    await email_service.send_templated_email(
                        to_email=to_email,
                        subject=job.subject,
                        template_name=job.template_name,
                        template_data=job.template_data or {},
                        from_email=job.from_email,
                        from_name=job.from_name,
                    )
                else:
                    await email_service.send_email(
                        to_email=to_email,
                        subject=job.subject,
                        html_content=job.html_content,
                        text_content=job.text_content,
                        from_email=job.from_email,
                        from_name=job.from_name,
                        attachments=job.attachments,
                    )

            # Mark as sent
            job.status = EmailStatus.SENT
            job.sent_at = datetime.utcnow()

            # Update metrics
            await self._increment_metric("sent")
            await self._increment_metric(f"sent_{job.priority}")

            logger.info(f"Email {job.id} sent successfully")

        except Exception as e:
            logger.error(f"Failed to send email {job.id}: {e}")
            job.error_message = str(e)

            # Handle retry logic
            if job.attempts < job.max_retries:
                await self._schedule_retry(job)
            else:
                await self._move_to_dead_letter(job)

    async def _schedule_retry(self, job: EmailJob):
        """Schedule email for retry with exponential backoff"""
        if not self.redis_client:
            return

        job.status = EmailStatus.RETRY

        # Calculate exponential backoff
        delay = job.retry_delay * (2 ** (job.attempts - 1))
        retry_time = datetime.utcnow() + timedelta(seconds=delay)

        # Add to retry queue with score as timestamp
        await self.redis_client.zadd(self.retry_queue, {job.json(): retry_time.timestamp()})

        # Update metrics
        await self._increment_metric("retries")

        logger.info(f"Email {job.id} scheduled for retry at {retry_time}")

    async def _process_retry_queue(self):
        """Process emails ready for retry"""
        if not self.redis_client:
            return

        now = datetime.utcnow().timestamp()

        # Get emails ready for retry
        ready = await self.redis_client.zrangebyscore(self.retry_queue, 0, now, start=0, num=10)

        for job_data in ready:
            try:
                # Remove from retry queue
                await self.redis_client.zrem(self.retry_queue, job_data)

                # Process email
                job = EmailJob.parse_raw(job_data)
                await self._process_email_job(job)

            except Exception as e:
                logger.error(f"Error processing retry: {e}")

    async def _process_scheduled(self):
        """Process scheduled emails"""
        if not self.redis_client:
            return

        now = datetime.utcnow().timestamp()

        # Get emails ready to send
        ready = await self.redis_client.zrangebyscore(
            f"{self.queue_prefix}:scheduled", 0, now, start=0, num=10
        )

        for job_data in ready:
            try:
                # Remove from scheduled queue
                await self.redis_client.zrem(f"{self.queue_prefix}:scheduled", job_data)

                # Add to priority queue
                job = EmailJob.parse_raw(job_data)
                queue_name = self.queues[job.priority]
                await self.redis_client.lpush(queue_name, job_data)

                logger.info(f"Scheduled email {job.id} moved to {job.priority} queue")

            except Exception as e:
                logger.error(f"Error processing scheduled email: {e}")

    async def _move_to_dead_letter(self, job: EmailJob):
        """Move failed email to dead letter queue"""
        if not self.redis_client:
            return

        job.status = EmailStatus.DEAD_LETTER

        # Add to dead letter queue
        await self.redis_client.lpush(self.dead_letter_queue, job.json())

        # Update metrics
        await self._increment_metric("dead_letter")

        logger.error(f"Email {job.id} moved to dead letter queue after {job.attempts} attempts")

        # Optionally notify administrators
        if job.priority in [EmailPriority.CRITICAL, EmailPriority.HIGH]:
            await self._notify_admin_failure(job)

    async def _notify_admin_failure(self, job: EmailJob):
        """Notify administrators of critical email failure"""
        try:
            admin_email = settings.ADMIN_EMAIL or "admin@example.com"

            await self.enqueue(
                to_email=admin_email,
                subject="Critical Email Delivery Failure",
                html_content=f"""
                <h2>Email Delivery Failed</h2>
                <p>A critical email failed to deliver after {job.attempts} attempts.</p>
                <h3>Details:</h3>
                <ul>
                    <li><strong>Job ID:</strong> {job.id}</li>
                    <li><strong>To:</strong> {job.to_email}</li>
                    <li><strong>Subject:</strong> {job.subject}</li>
                    <li><strong>Priority:</strong> {job.priority}</li>
                    <li><strong>Error:</strong> {job.error_message}</li>
                    <li><strong>Created:</strong> {job.created_at}</li>
                </ul>
                <p>The email has been moved to the dead letter queue for manual review.</p>
                """,
                priority=EmailPriority.HIGH,
            )
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")

    async def handle_bounce(self, email_address: str, bounce_type: str, details: dict[str, Any]):
        """
        Handle email bounce

        Args:
            email_address: Bounced email address
            bounce_type: Type of bounce (hard/soft)
            details: Bounce details
        """
        logger.warning(f"Email bounce: {email_address} ({bounce_type})")

        # Update metrics
        await self._increment_metric(f"bounce_{bounce_type}")

        # Store bounce information
        if self.redis_client:
            bounce_key = f"{self.queue_prefix}:bounces:{email_address}"
            await self.redis_client.hincrby(bounce_key, bounce_type, 1)
            await self.redis_client.hset(
                bounce_key,
                "last_bounce",
                json.dumps(
                    {
                        "type": bounce_type,
                        "timestamp": datetime.utcnow().isoformat(),
                        "details": details,
                    }
                ),
            )
            await self.redis_client.expire(bounce_key, 86400 * 30)  # 30 days

        # If hard bounce, add to suppression list
        if bounce_type == "hard":
            await self._add_to_suppression_list(email_address, "bounce")

    async def handle_complaint(
        self, email_address: str, complaint_type: str, details: dict[str, Any]
    ):
        """
        Handle email complaint

        Args:
            email_address: Complaining email address
            complaint_type: Type of complaint
            details: Complaint details
        """
        logger.warning(f"Email complaint: {email_address} ({complaint_type})")

        # Update metrics
        await self._increment_metric("complaints")

        # Store complaint information
        if self.redis_client:
            complaint_key = f"{self.queue_prefix}:complaints:{email_address}"
            await self.redis_client.hincrby(complaint_key, complaint_type, 1)
            await self.redis_client.hset(
                complaint_key,
                "last_complaint",
                json.dumps(
                    {
                        "type": complaint_type,
                        "timestamp": datetime.utcnow().isoformat(),
                        "details": details,
                    }
                ),
            )
            await self.redis_client.expire(complaint_key, 86400 * 90)  # 90 days

        # Add to suppression list
        await self._add_to_suppression_list(email_address, "complaint")

    async def _add_to_suppression_list(self, email_address: str, reason: str):
        """Add email to suppression list"""
        if self.redis_client:
            suppression_key = f"{self.queue_prefix}:suppression_list"
            await self.redis_client.hset(
                suppression_key,
                email_address,
                json.dumps({"reason": reason, "timestamp": datetime.utcnow().isoformat()}),
            )
            logger.info(f"Email {email_address} added to suppression list ({reason})")

    async def is_suppressed(self, email_address: str) -> bool:
        """Check if email is in suppression list"""
        if not self.redis_client:
            return False

        suppression_key = f"{self.queue_prefix}:suppression_list"
        return await self.redis_client.hexists(suppression_key, email_address)

    async def get_metrics(self) -> dict[str, Any]:
        """Get queue metrics"""
        if not self.redis_client:
            return {}

        metrics = {}

        # Get counter metrics
        for key in ["queued", "sent", "retries", "dead_letter", "complaints"]:
            value = await self.redis_client.hget(self.metrics_key, key)
            metrics[key] = int(value) if value else 0

        # Get queue lengths
        for priority in EmailPriority.__members__.values():
            queue_name = self.queues[priority]
            length = await self.redis_client.llen(queue_name)
            metrics[f"queue_{priority.value}"] = length

        # Get retry queue length
        retry_length = await self.redis_client.zcard(self.retry_queue)
        metrics["retry_queue"] = retry_length

        # Get dead letter queue length
        dead_letter_length = await self.redis_client.llen(self.dead_letter_queue)
        metrics["dead_letter_queue"] = dead_letter_length

        # Get scheduled queue length
        scheduled_length = await self.redis_client.zcard(f"{self.queue_prefix}:scheduled")
        metrics["scheduled_queue"] = scheduled_length

        # Get suppression list size
        suppression_size = await self.redis_client.hlen(f"{self.queue_prefix}:suppression_list")
        metrics["suppression_list"] = suppression_size

        return metrics

    async def _increment_metric(self, metric: str, value: int = 1):
        """Increment a metric counter"""
        if self.redis_client:
            await self.redis_client.hincrby(self.metrics_key, metric, value)

    async def reprocess_dead_letter(self, limit: int = 10) -> int:
        """
        Reprocess emails from dead letter queue

        Args:
            limit: Maximum number of emails to reprocess

        Returns:
            Number of emails reprocessed
        """
        if not self.redis_client:
            return 0

        count = 0

        for _ in range(limit):
            job_data = await self.redis_client.rpop(self.dead_letter_queue)
            if not job_data:
                break

            try:
                job = EmailJob.parse_raw(job_data)
                job.attempts = 0  # Reset attempts
                job.status = EmailStatus.QUEUED

                # Add back to priority queue
                queue_name = self.queues[job.priority]
                await self.redis_client.lpush(queue_name, job.json())

                count += 1
                logger.info(f"Reprocessed dead letter email {job.id}")

            except Exception as e:
                logger.error(f"Error reprocessing dead letter: {e}")

        return count

    async def clear_metrics(self):
        """Clear all metrics"""
        if self.redis_client:
            await self.redis_client.delete(self.metrics_key)
            logger.info("Email queue metrics cleared")


# Create singleton instance
email_queue = EmailQueueService()


# Background task runner
async def run_email_queue_processor():
    """Run email queue processor as background task"""
    try:
        logger.info("Starting email queue processor")
        await email_queue.process_queue()
    except Exception as e:
        logger.error(f"Email queue processor error: {e}")
    finally:
        await email_queue.disconnect()

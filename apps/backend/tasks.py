"""
Celery Tasks for ToolBoxAI
==========================
Following Celery 5.4+ API Reference: https://docs.celeryq.dev/en/stable/reference/index.html

Implements:
- Proper task signatures and binding
- Retry mechanisms with exponential backoff
- Task routing to appropriate queues
- Canvas workflows (chain, group, chord)
- Result backend usage
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Any

from celery import Task, chain, chord, group, shared_task
from celery.exceptions import SoftTimeLimitExceeded
from celery.utils.log import get_task_logger

# Get task-specific logger
logger = get_task_logger(__name__)


# ============================================
# BASE TASK CLASS - Celery 5.4 Best Practice
# ============================================
class BaseTaskWithRetry(Task):
    """
    Base task with automatic retry logic and error handling.
    Based on Celery 5.4 Task API reference.
    """

    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True
    retry_backoff_max = 700
    retry_jitter = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called on task failure."""
        logger.error(f"Task {self.name}[{task_id}] failed: {exc}")
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried."""
        logger.warning(f"Task {self.name}[{task_id}] retry attempt: {exc}")
        super().on_retry(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        """Called on task success."""
        logger.info(f"Task {self.name}[{task_id}] succeeded")
        super().on_success(retval, task_id, args, kwargs)


# ============================================
# CLEANUP TASKS
# ============================================
@shared_task(
    bind=True,
    base=BaseTaskWithRetry,
    name="tasks.cleanup.old_files",
    queue="low_priority",
    time_limit=300,
    soft_time_limit=270,
)
def cleanup_old_files(self, directory: str = "/tmp", days_old: int = 7) -> dict[str, Any]:
    """
    Clean up files older than specified days.

    Args:
        directory: Directory to clean
        days_old: Files older than this many days will be removed

    Returns:
        Dictionary with cleanup results
    """
    try:
        cleaned_count = 0
        errors = []
        path = Path(directory)

        if not path.exists():
            return {
                "status": "skipped",
                "message": f"Directory {directory} does not exist",
                "files_removed": 0,
            }

        cutoff_time = time.time() - (days_old * 24 * 60 * 60)

        for file_path in path.iterdir():
            try:
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    cleaned_count += 1
                    logger.debug(f"Removed old file: {file_path}")
            except Exception as e:
                errors.append(str(e))
                logger.warning(f"Could not remove {file_path}: {e}")

        return {
            "status": "success",
            "files_removed": cleaned_count,
            "directory": directory,
            "errors": errors if errors else None,
            "task_id": self.request.id,
        }

    except SoftTimeLimitExceeded:
        logger.error("Task cleanup_old_files exceeded soft time limit")
        return {
            "status": "timeout",
            "files_removed": cleaned_count if "cleaned_count" in locals() else 0,
            "error": "Task exceeded time limit",
        }
    except Exception as exc:
        logger.error(f"Error in cleanup_old_files: {exc}")
        self.retry(exc=exc)


@shared_task(
    bind=True, base=BaseTaskWithRetry, name="tasks.cleanup.expired_sessions", queue="low_priority"
)
def cleanup_expired_sessions(self) -> dict[str, Any]:
    """Clean up expired user sessions from Redis."""
    try:
        from apps.backend.core.cache import redis_client

        pattern = "session:*"
        expired_count = 0

        # Scan for session keys
        for key in redis_client.scan_iter(match=pattern):
            ttl = redis_client.ttl(key)
            if ttl == -2 or ttl == 0:  # Key expired or doesn't exist
                redis_client.delete(key)
                expired_count += 1

        logger.info(f"Cleaned up {expired_count} expired sessions")

        return {"status": "success", "sessions_removed": expired_count, "task_id": self.request.id}

    except Exception as exc:
        logger.error(f"Error cleaning expired sessions: {exc}")
        self.retry(exc=exc)


@shared_task(bind=True, name="tasks.cleanup.temp_storage", queue="low_priority")
def cleanup_temp_storage(self) -> dict[str, Any]:
    """Clean temporary storage directories."""
    temp_dirs = ["/tmp/toolboxai", "/tmp/uploads", "/tmp/exports"]
    total_cleaned = 0

    for temp_dir in temp_dirs:
        result = cleanup_old_files.apply_async(
            args=[temp_dir, 1], queue="low_priority"  # Clean files older than 1 day
        ).get(timeout=60)

        if result.get("status") == "success":
            total_cleaned += result.get("files_removed", 0)

    return {
        "status": "success",
        "total_files_removed": total_cleaned,
        "directories_cleaned": temp_dirs,
    }


# ============================================
# CONTENT GENERATION TASKS
# ============================================
@shared_task(
    bind=True,
    base=BaseTaskWithRetry,
    name="tasks.content.generate_educational",
    queue="high_priority",
    time_limit=180,
    soft_time_limit=150,
)
def generate_educational_content(
    self, request_data: dict[str, Any], callback_channel: str | None = None
) -> dict[str, Any]:
    """
    Generate educational content using AI.

    Args:
        request_data: Content generation parameters
        callback_channel: Optional Pusher channel for progress updates

    Returns:
        Generated content with metadata
    """
    try:
        # Import here to avoid circular imports
        from apps.backend.services.pusher_realtime import pusher_service

        topic = request_data.get("topic")
        grade_level = request_data.get("grade_level")
        content_type = request_data.get("content_type", "lesson")

        # Send progress update
        if callback_channel and pusher_service:
            pusher_service.trigger(
                callback_channel,
                "progress",
                {
                    "task_id": self.request.id,
                    "progress": 10,
                    "message": "Starting content generation...",
                },
            )

        # Simulate content generation (replace with actual AI call)
        import time

        time.sleep(2)  # Simulate processing

        # Generate mock content
        content = {
            "title": f"{content_type.title()}: {topic}",
            "grade_level": grade_level,
            "content": f"Generated content for {topic} at {grade_level} level.",
            "sections": [
                {"title": "Introduction", "content": "Introduction content..."},
                {"title": "Main Content", "content": "Main lesson content..."},
                {"title": "Summary", "content": "Summary content..."},
            ],
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "word_count": 500,
                "reading_time": "5 minutes",
            },
        }

        # Generate quiz if requested
        quiz = None
        if request_data.get("metadata", {}).get("include_quiz"):
            quiz = process_quiz_generation.apply_async(
                args=[content["content"], request_data.get("metadata", {}).get("quiz_questions", 5)]
            ).get(timeout=30)

        # Send completion update
        if callback_channel and pusher_service:
            pusher_service.trigger(
                callback_channel, "complete", {"task_id": self.request.id, "result": content}
            )

        return {"status": "success", "content": content, "quiz": quiz, "task_id": self.request.id}

    except SoftTimeLimitExceeded:
        logger.error("Content generation exceeded time limit")
        return {"status": "timeout", "error": "Content generation took too long"}
    except Exception as exc:
        logger.error(f"Error generating content: {exc}")
        self.retry(exc=exc)


@shared_task(bind=True, name="tasks.content.generate_quiz", queue="default")
def process_quiz_generation(self, content: str, num_questions: int = 5) -> dict[str, Any]:
    """Generate quiz questions from content."""
    try:
        # Mock quiz generation
        questions = []
        for i in range(num_questions):
            questions.append(
                {
                    "question": f"Question {i+1} about the content?",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer": "Option A",
                    "explanation": "This is why Option A is correct.",
                }
            )

        return {"status": "success", "questions": questions, "num_questions": num_questions}

    except Exception as exc:
        logger.error(f"Error generating quiz: {exc}")
        self.retry(exc=exc)


@shared_task(bind=True, name="tasks.content.analyze_quality", queue="low_priority")
def analyze_content_quality(self, content_id: str) -> dict[str, Any]:
    """Analyze content quality metrics."""
    try:
        # Mock quality analysis
        metrics = {
            "readability_score": 85,
            "engagement_score": 72,
            "completeness": 90,
            "accuracy": 95,
            "suggestions": ["Add more interactive elements", "Include real-world examples"],
        }

        return {
            "status": "success",
            "content_id": content_id,
            "metrics": metrics,
            "analyzed_at": datetime.utcnow().isoformat(),
        }

    except Exception as exc:
        logger.error(f"Error analyzing content: {exc}")
        self.retry(exc=exc)


# ============================================
# NOTIFICATION TASKS
# ============================================
@shared_task(
    bind=True,
    base=BaseTaskWithRetry,
    name="tasks.notifications.send",
    queue="high_priority",
    rate_limit="100/m",  # Rate limit: 100 per minute
)
def send_notification(
    self,
    user_id: str,
    notification_type: str,
    title: str,
    message: str,
    data: dict | None = None,
    channels: list[str] = None,
) -> dict[str, Any]:
    """
    Send notification to user.

    Args:
        user_id: Target user ID
        notification_type: Type of notification (info, warning, error, success)
        title: Notification title
        message: Notification message
        data: Additional data
        channels: Delivery channels (pusher, email, sms)
    """
    try:
        channels = channels or ["pusher"]
        delivery_results = {}

        for channel in channels:
            if channel == "pusher":
                from apps.backend.services.pusher_realtime import pusher_service

                if pusher_service:
                    pusher_service.trigger(
                        f"private-user-{user_id}",
                        "notification",
                        {
                            "type": notification_type,
                            "title": title,
                            "message": message,
                            "data": data,
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    )
                    delivery_results["pusher"] = "sent"

            elif channel == "email":
                # Email implementation would go here
                delivery_results["email"] = "not_implemented"

            elif channel == "sms":
                # SMS implementation would go here
                delivery_results["sms"] = "not_implemented"

        logger.info(f"Notification sent to user {user_id} via {channels}")

        return {
            "status": "success",
            "user_id": user_id,
            "delivery_results": delivery_results,
            "task_id": self.request.id,
        }

    except Exception as exc:
        logger.error(f"Error sending notification: {exc}")
        self.retry(exc=exc)


@shared_task(bind=True, name="tasks.notifications.send_bulk", queue="low_priority")
def send_bulk_notifications(
    self, user_ids: list[str], notification_type: str, title: str, message: str
) -> dict[str, Any]:
    """Send notifications to multiple users using group."""
    try:
        # Use Celery group for parallel execution
        job = group(
            send_notification.s(user_id, notification_type, title, message, None, ["pusher"])
            for user_id in user_ids
        )

        results = job.apply_async().get(timeout=60)

        successful = sum(1 for r in results if r.get("status") == "success")

        return {
            "status": "success" if successful == len(user_ids) else "partial",
            "total_users": len(user_ids),
            "successful": successful,
            "failed": len(user_ids) - successful,
        }

    except Exception as exc:
        logger.error(f"Error in bulk notifications: {exc}")
        self.retry(exc=exc)


@shared_task(bind=True, name="tasks.webhook.process", queue="default")
def process_webhook_event(
    self, event_type: str, event_data: dict[str, Any], source: str
) -> dict[str, Any]:
    """Process incoming webhook events."""
    try:
        logger.info(f"Processing webhook: {event_type} from {source}")

        # Route to appropriate handler based on event type
        handlers = {
            "pusher.channel_occupied": handle_channel_occupied,
            "pusher.channel_vacated": handle_channel_vacated,
            "stripe.payment_succeeded": handle_payment_success,
            "stripe.payment_failed": handle_payment_failure,
        }

        handler = handlers.get(event_type)
        if handler:
            result = handler(event_data)
        else:
            result = {"status": "unhandled", "event_type": event_type}

        return {
            "status": "success",
            "event_type": event_type,
            "source": source,
            "result": result,
            "processed_at": datetime.utcnow().isoformat(),
        }

    except Exception as exc:
        logger.error(f"Error processing webhook: {exc}")
        self.retry(exc=exc)


def handle_channel_occupied(data: dict) -> dict:
    """Handle Pusher channel occupied event."""
    return {"action": "channel_occupied", "channel": data.get("channel")}


def handle_channel_vacated(data: dict) -> dict:
    """Handle Pusher channel vacated event."""
    return {"action": "channel_vacated", "channel": data.get("channel")}


def handle_payment_success(data: dict) -> dict:
    """Handle successful payment."""
    return {"action": "payment_recorded", "amount": data.get("amount")}


def handle_payment_failure(data: dict) -> dict:
    """Handle failed payment."""
    return {"action": "payment_failed", "reason": data.get("failure_reason")}


# ============================================
# ANALYTICS TASKS
# ============================================
@shared_task(
    bind=True, name="tasks.analytics.aggregate_metrics", queue="low_priority", time_limit=600
)
def aggregate_usage_metrics(self, period: str = "daily", date: str | None = None) -> dict[str, Any]:
    """Aggregate usage metrics for analytics."""
    try:
        target_date = date or datetime.utcnow().isoformat()

        # Mock metrics aggregation
        metrics = {
            "users": {"total": 1250, "active": 450, "new": 25},
            "content": {"views": 3500, "generated": 45, "shared": 120},
            "engagement_rate": 0.72,
            "average_session_duration": 1250,  # seconds
        }

        logger.info(f"Aggregated {period} metrics for {target_date}")

        return {
            "status": "success",
            "period": period,
            "date": target_date,
            "metrics": metrics,
            "task_id": self.request.id,
        }

    except Exception as exc:
        logger.error(f"Error aggregating metrics: {exc}")
        self.retry(exc=exc)


@shared_task(bind=True, name="tasks.analytics.generate_report", queue="low_priority")
def generate_reports(
    self, report_type: str, start_date: str, end_date: str, filters: dict | None = None
) -> dict[str, Any]:
    """Generate analytics reports."""
    try:
        import uuid

        report_id = str(uuid.uuid4())

        # Mock report generation
        report_path = f"/tmp/reports/{report_id}.json"

        report_data = {
            "report_id": report_id,
            "type": report_type,
            "period": {"start": start_date, "end": end_date},
            "filters": filters,
            "data": {"summary": "Report summary here", "details": []},
            "generated_at": datetime.utcnow().isoformat(),
        }

        # Save report (mock)
        logger.info(f"Generated {report_type} report: {report_id}")

        return {
            "status": "success",
            "report_id": report_id,
            "report_path": report_path,
            "report_type": report_type,
            "task_id": self.request.id,
        }

    except Exception as exc:
        logger.error(f"Error generating report: {exc}")
        self.retry(exc=exc)


@shared_task(bind=True, name="tasks.analytics.export_data", queue="low_priority")
def export_analytics_data(
    self, export_format: str = "json", data_type: str = "all"
) -> dict[str, Any]:
    """Export analytics data."""
    try:
        import uuid

        export_id = str(uuid.uuid4())

        formats = ["json", "csv", "excel"]
        if export_format not in formats:
            raise ValueError(f"Invalid format. Must be one of {formats}")

        export_path = f"/tmp/exports/{export_id}.{export_format}"

        # Mock export
        logger.info(f"Exported {data_type} data to {export_path}")

        return {
            "status": "success",
            "export_id": export_id,
            "export_path": export_path,
            "format": export_format,
            "data_type": data_type,
        }

    except Exception as exc:
        logger.error(f"Error exporting data: {exc}")
        self.retry(exc=exc)


# ============================================
# ROBLOX SYNC TASKS
# ============================================
@shared_task(bind=True, name="tasks.roblox.sync_environment", queue="default")
def sync_roblox_environment(
    self, universe_id: str, sync_type: str = "incremental"
) -> dict[str, Any]:
    """Sync data with Roblox environment."""
    try:
        logger.info(f"Starting {sync_type} sync for universe {universe_id}")

        # Mock Roblox sync
        synced_items = {"assets": 25, "scripts": 10, "data_stores": 5}

        return {
            "status": "success",
            "universe_id": universe_id,
            "sync_type": sync_type,
            "results": synced_items,
            "synced_at": datetime.utcnow().isoformat(),
        }

    except Exception as exc:
        logger.error(f"Error syncing Roblox: {exc}")
        self.retry(exc=exc)


@shared_task(bind=True, name="tasks.roblox.deploy", queue="high_priority")
def deploy_to_roblox(
    self, place_id: str, deployment_type: str, assets: list[str]
) -> dict[str, Any]:
    """Deploy assets to Roblox place."""
    try:
        logger.info(f"Deploying {len(assets)} assets to place {place_id}")

        deployed = []
        failed = []

        for asset in assets:
            # Mock deployment
            if "error" not in asset:
                deployed.append(asset)
            else:
                failed.append(asset)

        return {
            "status": "success" if not failed else "partial",
            "place_id": place_id,
            "deployment_type": deployment_type,
            "deployed": deployed,
            "failed": failed,
            "deployed_at": datetime.utcnow().isoformat(),
        }

    except Exception as exc:
        logger.error(f"Error deploying to Roblox: {exc}")
        self.retry(exc=exc)


@shared_task(bind=True, name="tasks.roblox.validate_assets", queue="low_priority")
def validate_roblox_assets(self, asset_ids: list[str]) -> dict[str, Any]:
    """Validate Roblox assets."""
    try:
        valid = []
        invalid = []

        for asset_id in asset_ids:
            # Mock validation
            if len(asset_id) > 5:
                valid.append(asset_id)
            else:
                invalid.append(asset_id)

        return {
            "status": "success",
            "total": len(asset_ids),
            "valid": valid,
            "invalid": invalid,
            "validated_at": datetime.utcnow().isoformat(),
        }

    except Exception as exc:
        logger.error(f"Error validating assets: {exc}")
        self.retry(exc=exc)


# ============================================
# CANVAS WORKFLOWS - Celery 5.4 Patterns
# ============================================
def daily_maintenance_workflow():
    """
    Chain multiple maintenance tasks.
    Reference: https://docs.celeryq.dev/en/stable/userguide/canvas.html
    """
    workflow = chain(
        cleanup_expired_sessions.s(),
        cleanup_old_files.s("/tmp", 7),
        cleanup_temp_storage.s(),
        aggregate_usage_metrics.s("daily"),
    )
    return workflow.apply_async()


def content_generation_workflow(topic: str, grade_level: str):
    """
    Complex workflow using chord for parallel execution with callback.
    """
    header = group(
        generate_educational_content.s(
            {"topic": topic, "grade_level": grade_level, "content_type": "lesson"}
        ),
        generate_educational_content.s(
            {"topic": topic, "grade_level": grade_level, "content_type": "worksheet"}
        ),
        generate_educational_content.s(
            {"topic": topic, "grade_level": grade_level, "content_type": "quiz"}
        ),
    )

    # Callback to analyze quality after all content is generated
    callback = analyze_content_quality.s()

    workflow = chord(header)(callback)
    return workflow


def analytics_pipeline(start_date: str, end_date: str):
    """
    Analytics pipeline using chain and group.
    """
    workflow = chain(
        # First aggregate metrics
        aggregate_usage_metrics.s("daily"),
        # Then generate reports in parallel
        group(
            generate_reports.s("usage", start_date, end_date),
            generate_reports.s("engagement", start_date, end_date),
            generate_reports.s("performance", start_date, end_date),
        ),
        # Finally export data
        export_analytics_data.s("json", "all"),
    )
    return workflow.apply_async()


# ============================================
# TASK RESULT HELPERS
# ============================================
def get_task_result(task_id: str) -> dict[str, Any]:
    """
    Get task result by ID.
    Uses Celery AsyncResult API.
    """
    from celery.result import AsyncResult

    from apps.backend.celery_app import app

    result = AsyncResult(task_id, app=app)

    return {
        "task_id": task_id,
        "state": result.state,
        "result": result.result if result.ready() else None,
        "info": result.info,
        "successful": result.successful() if result.ready() else None,
        "failed": result.failed() if result.ready() else None,
    }


def revoke_task(task_id: str, terminate: bool = True) -> bool:
    """
    Revoke a task by ID.
    """
    from apps.backend.celery_app import app

    app.control.revoke(task_id, terminate=terminate)
    logger.info(f"Task {task_id} revoked (terminate={terminate})")
    return True

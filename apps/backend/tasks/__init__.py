"""
ToolBoxAI Background Tasks Module
================================
Celery tasks for asynchronous processing
"""

from .ai_tasks import (
    batch_content_generation,
    generate_content,
    process_generation_queue,
)
from .analytics_tasks import (
    aggregate_usage_metrics,
    export_analytics_data,
    generate_reports,
)
from .cleanup_tasks import (
    cleanup_expired_sessions,
    cleanup_old_files,
    cleanup_temp_storage,
)
from .content_tasks import (
    analyze_content_quality,
    generate_educational_content,
    process_quiz_generation,
)
from .email_tasks import send_bulk_emails, send_email, send_pending_emails
from .health_tasks import check_database_health, check_integrations, check_redis_health
from .notification_tasks import (
    process_webhook_event,
    send_bulk_notifications,
    send_notification,
)
from .roblox_tasks import (
    deploy_to_roblox,
    sync_roblox_environment,
    validate_roblox_assets,
)

__all__ = [
    # Cleanup tasks
    "cleanup_old_files",
    "cleanup_expired_sessions",
    "cleanup_temp_storage",
    # Content tasks
    "generate_educational_content",
    "process_quiz_generation",
    "analyze_content_quality",
    # Roblox tasks
    "sync_roblox_environment",
    "deploy_to_roblox",
    "validate_roblox_assets",
    # Notification tasks
    "send_notification",
    "send_bulk_notifications",
    "process_webhook_event",
    # Analytics tasks
    "aggregate_usage_metrics",
    "generate_reports",
    "export_analytics_data",
    # Health tasks
    "check_integrations",
    "check_database_health",
    "check_redis_health",
    # Email tasks
    "send_pending_emails",
    "send_email",
    "send_bulk_emails",
    # AI tasks
    "process_generation_queue",
    "generate_content",
    "batch_content_generation",
]

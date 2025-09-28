"""
ToolBoxAI Background Tasks Module
================================
Celery tasks for asynchronous processing
"""

from .cleanup_tasks import cleanup_old_files, cleanup_expired_sessions, cleanup_temp_storage
from .content_tasks import (
    generate_educational_content,
    process_quiz_generation,
    analyze_content_quality,
)
from .roblox_tasks import sync_roblox_environment, deploy_to_roblox, validate_roblox_assets
from .notification_tasks import send_notification, send_bulk_notifications, process_webhook_event
from .analytics_tasks import aggregate_usage_metrics, generate_reports, export_analytics_data

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
]

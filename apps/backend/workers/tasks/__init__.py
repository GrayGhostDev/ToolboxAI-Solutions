"""
ToolBoxAI Workers Tasks Module
==============================
Comprehensive background task implementations with tenant isolation,
Redis-based coordination, and self-hosted monitoring.

Task Categories:
- Content Tasks: AI content generation with OpenAI
- Email Tasks: SMTP email sending (no AWS SES)
- Analytics Tasks: Data aggregation to PostgreSQL
- Roblox Tasks: Roblox sync operations
- Cleanup Tasks: Database/storage maintenance
- Tenant Tasks: Organization-specific operations
"""

# Import all task modules for auto-discovery
from . import (
    analytics_tasks,
    cleanup_tasks,
    content_tasks,
    email_tasks,
    roblox_tasks,
    tenant_tasks,
)
from .analytics_tasks import (
    aggregate_usage_metrics,
    export_analytics_data,
    generate_daily_report,
    generate_weekly_reports,
)
from .cleanup_tasks import (
    cleanup_dead_letter_queue,
    cleanup_expired_sessions,
    cleanup_old_files,
    cleanup_temp_storage,
)

# Import specific tasks for easy access
from .content_tasks import (
    analyze_content_quality,
    generate_educational_content,
    process_generation_queue,
    process_quiz_generation,
)
from .email_tasks import (
    process_email_queue,
    send_bulk_emails,
    send_email,
    send_notification_email,
)
from .roblox_tasks import (
    deploy_to_roblox,
    sync_all_environments,
    sync_roblox_environment,
    validate_roblox_assets,
)
from .tenant_tasks import (
    cleanup_tenant_data,
    generate_tenant_report,
    sync_billing_data,
    track_usage_metrics,
)

__all__ = [
    # Content tasks
    "generate_educational_content",
    "process_quiz_generation",
    "analyze_content_quality",
    "process_generation_queue",
    # Email tasks
    "send_email",
    "send_bulk_emails",
    "process_email_queue",
    "send_notification_email",
    # Analytics tasks
    "aggregate_usage_metrics",
    "generate_daily_report",
    "generate_weekly_reports",
    "export_analytics_data",
    # Roblox tasks
    "sync_roblox_environment",
    "deploy_to_roblox",
    "validate_roblox_assets",
    "sync_all_environments",
    # Cleanup tasks
    "cleanup_old_files",
    "cleanup_expired_sessions",
    "cleanup_temp_storage",
    "cleanup_dead_letter_queue",
    # Tenant tasks
    "generate_tenant_report",
    "cleanup_tenant_data",
    "sync_billing_data",
    "track_usage_metrics",
]

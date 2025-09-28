"""
Celery Beat Schedule Configuration
==================================
Defines periodic tasks using Redis for coordination (no AWS CloudWatch Events).

Features:
- Tenant-specific scheduled tasks
- Database cleanup schedules
- Analytics report generation
- Health monitoring tasks
- Resource usage monitoring
"""

from datetime import timedelta
from typing import Dict, Any
import os

from toolboxai_settings import settings


def get_beat_schedule() -> Dict[str, Any]:
    """
    Get Celery Beat schedule configuration with Redis-based coordination.

    Returns:
        Dictionary of scheduled tasks for Celery Beat
    """
    return {
        # ========================================
        # STORAGE TASKS (Hourly/Daily)
        # ========================================
        "storage-usage-calculation": {
            "task": "apps.backend.workers.tasks.storage_tasks.calculate_storage_usage",
            "schedule": timedelta(hours=1),
            "options": {"queue": "storage"},
            "kwargs": {
                "organization_id": None,  # Calculate for all organizations
                "force_recalculation": False
            },
        },

        "storage-quota-alerts": {
            "task": "apps.backend.workers.tasks.storage_tasks.send_quota_alerts",
            "schedule": timedelta(hours=6),
            "options": {"queue": "storage"},
            "kwargs": {},
        },

        "cleanup-expired-storage-files": {
            "task": "apps.backend.workers.tasks.storage_tasks.cleanup_expired_files",
            "schedule": timedelta(days=1),
            "options": {"queue": "storage"},
            "kwargs": {
                "organization_id": None,  # All organizations
                "cleanup_type": "expired_files",
                "older_than_days": 30,
                "dry_run": False
            },
        },

        "cleanup-deleted-storage-files": {
            "task": "apps.backend.workers.tasks.storage_tasks.cleanup_expired_files",
            "schedule": timedelta(days=7),
            "options": {"queue": "storage"},
            "kwargs": {
                "organization_id": None,  # All organizations
                "cleanup_type": "deleted_files",
                "older_than_days": 90,
                "dry_run": False
            },
        },

        "optimize-storage": {
            "task": "apps.backend.workers.tasks.storage_tasks.optimize_storage",
            "schedule": timedelta(days=7),
            "options": {"queue": "low_priority"},
            "kwargs": {
                "organization_id": None  # Global optimization
            },
        },

        "generate-monthly-storage-reports": {
            "task": "apps.backend.workers.tasks.storage_tasks.generate_storage_report",
            "schedule": timedelta(days=30),
            "options": {"queue": "analytics"},
            "kwargs": {
                "organization_id": None,  # All organizations
                "report_type": "monthly"
            },
        },

        # ========================================
        # CLEANUP TASKS (Daily/Hourly)
        # ========================================
        "cleanup-expired-sessions": {
            "task": "apps.backend.workers.tasks.cleanup_tasks.cleanup_expired_sessions",
            "schedule": timedelta(hours=1),
            "options": {"queue": "low_priority"},
            "kwargs": {},
        },

        "cleanup-old-files": {
            "task": "apps.backend.workers.tasks.cleanup_tasks.cleanup_old_files",
            "schedule": timedelta(hours=6),
            "options": {"queue": "low_priority"},
            "kwargs": {
                "directory": "/tmp/toolboxai",
                "days_old": 7
            },
        },

        "cleanup-old-logs": {
            "task": "apps.backend.workers.tasks.cleanup_tasks.cleanup_old_logs",
            "schedule": timedelta(days=1),
            "options": {"queue": "low_priority"},
            "kwargs": {
                "log_directory": "/var/log/celery",
                "days_old": 30
            },
        },

        "cleanup-dead-letter-queue": {
            "task": "apps.backend.workers.tasks.cleanup_tasks.cleanup_dead_letter_queue",
            "schedule": timedelta(hours=12),
            "options": {"queue": "low_priority"},
            "kwargs": {
                "max_age_days": 7
            },
        },

        # ========================================
        # ANALYTICS TASKS (Daily/Weekly)
        # ========================================
        "generate-daily-analytics": {
            "task": "apps.backend.workers.tasks.analytics_tasks.generate_daily_report",
            "schedule": timedelta(days=1),
            "options": {"queue": "analytics"},
            "kwargs": {
                "report_type": "daily_usage",
                "include_tenant_breakdown": True
            },
        },

        "aggregate-usage-metrics": {
            "task": "apps.backend.workers.tasks.analytics_tasks.aggregate_usage_metrics",
            "schedule": timedelta(hours=4),
            "options": {"queue": "analytics"},
            "kwargs": {
                "period": "hourly"
            },
        },

        "generate-weekly-reports": {
            "task": "apps.backend.workers.tasks.analytics_tasks.generate_weekly_reports",
            "schedule": timedelta(days=7),
            "options": {"queue": "analytics"},
            "kwargs": {
                "include_performance_metrics": True,
                "include_tenant_analytics": True
            },
        },

        "export-analytics-data": {
            "task": "apps.backend.workers.tasks.analytics_tasks.export_analytics_data",
            "schedule": timedelta(days=1),
            "options": {"queue": "analytics"},
            "kwargs": {
                "export_format": "json",
                "data_type": "daily_summary",
                "retention_days": 90
            },
        },

        # ========================================
        # EMAIL TASKS (Frequent)
        # ========================================
        "process-email-queue": {
            "task": "apps.backend.workers.tasks.email_tasks.process_email_queue",
            "schedule": timedelta(minutes=2),
            "options": {"queue": "email"},
            "kwargs": {
                "batch_size": 50,
                "max_retries": 3
            },
        },

        "send-pending-notifications": {
            "task": "apps.backend.workers.tasks.email_tasks.send_pending_notifications",
            "schedule": timedelta(minutes=5),
            "options": {"queue": "email"},
            "kwargs": {
                "notification_types": ["urgent", "important"]
            },
        },

        "cleanup-email-logs": {
            "task": "apps.backend.workers.tasks.email_tasks.cleanup_email_logs",
            "schedule": timedelta(days=7),
            "options": {"queue": "low_priority"},
            "kwargs": {
                "retention_days": 30
            },
        },

        # ========================================
        # CONTENT GENERATION TASKS
        # ========================================
        "process-content-generation-queue": {
            "task": "apps.backend.workers.tasks.content_tasks.process_generation_queue",
            "schedule": timedelta(minutes=3),
            "options": {"queue": "ai_generation"},
            "kwargs": {
                "max_concurrent_generations": 5
            },
        },

        "cleanup-generated-content": {
            "task": "apps.backend.workers.tasks.content_tasks.cleanup_generated_content",
            "schedule": timedelta(days=1),
            "options": {"queue": "low_priority"},
            "kwargs": {
                "cleanup_drafts_older_than_days": 30,
                "cleanup_temp_files": True
            },
        },

        # ========================================
        # ROBLOX SYNC TASKS
        # ========================================
        "sync-roblox-environments": {
            "task": "apps.backend.workers.tasks.roblox_tasks.sync_all_environments",
            "schedule": timedelta(hours=2),
            "options": {"queue": "roblox"},
            "kwargs": {
                "sync_type": "incremental",
                "include_analytics": True
            },
        },

        "validate-roblox-deployments": {
            "task": "apps.backend.workers.tasks.roblox_tasks.validate_deployments",
            "schedule": timedelta(hours=6),
            "options": {"queue": "roblox"},
            "kwargs": {
                "check_asset_integrity": True,
                "verify_api_endpoints": True
            },
        },

        # ========================================
        # TENANT MANAGEMENT TASKS
        # ========================================
        "generate-tenant-usage-reports": {
            "task": "apps.backend.workers.tasks.tenant_tasks.generate_usage_reports",
            "schedule": timedelta(days=1),
            "options": {"queue": "tenant_operations"},
            "kwargs": {
                "report_period": "daily",
                "include_billing_data": True
            },
        },

        "cleanup-tenant-data": {
            "task": "apps.backend.workers.tasks.tenant_tasks.cleanup_tenant_data",
            "schedule": timedelta(days=7),
            "options": {"queue": "tenant_operations"},
            "kwargs": {
                "cleanup_inactive_tenants": True,
                "retention_days": 365
            },
        },

        "sync-tenant-billing": {
            "task": "apps.backend.workers.tasks.tenant_tasks.sync_billing_data",
            "schedule": timedelta(hours=12),
            "options": {"queue": "tenant_operations"},
            "kwargs": {
                "include_usage_metrics": True,
                "update_stripe_metadata": True
            },
        },

        # ========================================
        # HEALTH MONITORING TASKS
        # ========================================
        "health-check-integrations": {
            "task": "apps.backend.workers.tasks.health_tasks.check_integrations",
            "schedule": timedelta(minutes=5),
            "options": {"queue": "high_priority"},
            "kwargs": {
                "check_redis": True,
                "check_postgres": True,
                "check_external_apis": True
            },
        },

        "monitor-system-resources": {
            "task": "apps.backend.workers.tasks.health_tasks.monitor_system_resources",
            "schedule": timedelta(minutes=10),
            "options": {"queue": "default"},
            "kwargs": {
                "alert_thresholds": {
                    "memory_usage": 85,
                    "cpu_usage": 90,
                    "disk_usage": 80
                }
            },
        },

        "check-worker-health": {
            "task": "apps.backend.workers.tasks.health_tasks.check_worker_health",
            "schedule": timedelta(minutes=2),
            "options": {"queue": "high_priority"},
            "kwargs": {
                "max_response_time": 30,
                "alert_on_failure": True
            },
        },

        # ========================================
        # MONITORING & MAINTENANCE
        # ========================================
        "update-prometheus-metrics": {
            "task": "apps.backend.workers.tasks.monitoring_tasks.update_prometheus_metrics",
            "schedule": timedelta(minutes=1),
            "options": {"queue": "default"},
            "kwargs": {
                "metrics_types": ["worker_status", "queue_lengths", "task_rates"]
            },
        },

        "rotate-log-files": {
            "task": "apps.backend.workers.tasks.maintenance_tasks.rotate_log_files",
            "schedule": timedelta(days=1),
            "options": {"queue": "low_priority"},
            "kwargs": {
                "log_directories": ["/var/log/celery", "/var/log/nginx"],
                "max_size_mb": 100
            },
        },

        "backup-redis-data": {
            "task": "apps.backend.workers.tasks.maintenance_tasks.backup_redis_data",
            "schedule": timedelta(hours=6),
            "options": {"queue": "low_priority"},
            "kwargs": {
                "backup_location": "/backups/redis",
                "retention_days": 7
            },
        } if not settings.ENV_NAME.lower().startswith('dev') else None,
    }


def get_tenant_specific_schedule(organization_id: str) -> Dict[str, Any]:
    """
    Get tenant-specific scheduled tasks.

    Args:
        organization_id: Tenant organization ID

    Returns:
        Dictionary of tenant-specific scheduled tasks
    """
    return {
        f"tenant-{organization_id}-daily-report": {
            "task": "apps.backend.workers.tasks.tenant_tasks.generate_tenant_report",
            "schedule": timedelta(days=1),
            "options": {"queue": "tenant_operations"},
            "kwargs": {
                "organization_id": organization_id,
                "report_type": "daily_summary",
                "include_usage_analytics": True
            },
        },

        f"tenant-{organization_id}-weekly-backup": {
            "task": "apps.backend.workers.tasks.tenant_tasks.backup_tenant_data",
            "schedule": timedelta(days=7),
            "options": {"queue": "tenant_operations"},
            "kwargs": {
                "organization_id": organization_id,
                "backup_type": "incremental",
                "include_user_data": True
            },
        },

        f"tenant-{organization_id}-usage-tracking": {
            "task": "apps.backend.workers.tasks.tenant_tasks.track_usage_metrics",
            "schedule": timedelta(hours=1),
            "options": {"queue": "analytics"},
            "kwargs": {
                "organization_id": organization_id,
                "track_api_usage": True,
                "track_content_generation": True,
                "track_storage_usage": True
            },
        },
    }


def get_development_schedule() -> Dict[str, Any]:
    """
    Get reduced schedule for development environment.

    Returns:
        Simplified schedule for development
    """
    return {
        "dev-health-check": {
            "task": "apps.backend.workers.tasks.health_tasks.simple_health_check",
            "schedule": timedelta(minutes=5),
            "options": {"queue": "default"},
            "kwargs": {},
        },

        "dev-cleanup-temp": {
            "task": "apps.backend.workers.tasks.cleanup_tasks.cleanup_temp_files",
            "schedule": timedelta(hours=2),
            "options": {"queue": "low_priority"},
            "kwargs": {
                "temp_directory": "/tmp/toolboxai-dev"
            },
        },
    }


def get_production_schedule() -> Dict[str, Any]:
    """
    Get enhanced schedule for production environment.

    Returns:
        Comprehensive schedule for production
    """
    base_schedule = get_beat_schedule()

    # Add production-specific tasks
    production_tasks = {
        "security-audit-log": {
            "task": "apps.backend.workers.tasks.security_tasks.audit_security_logs",
            "schedule": timedelta(hours=1),
            "options": {"queue": "high_priority"},
            "kwargs": {
                "check_failed_logins": True,
                "check_suspicious_activity": True,
                "alert_threshold": 10
            },
        },

        "performance-monitoring": {
            "task": "apps.backend.workers.tasks.monitoring_tasks.monitor_performance",
            "schedule": timedelta(minutes=5),
            "options": {"queue": "default"},
            "kwargs": {
                "check_response_times": True,
                "check_error_rates": True,
                "alert_on_degradation": True
            },
        },

        "database-optimization": {
            "task": "apps.backend.workers.tasks.maintenance_tasks.optimize_database",
            "schedule": timedelta(days=1),
            "options": {"queue": "low_priority"},
            "kwargs": {
                "analyze_tables": True,
                "update_statistics": True,
                "cleanup_orphaned_records": True
            },
        },
    }

    base_schedule.update(production_tasks)
    return base_schedule


def get_environment_schedule() -> Dict[str, Any]:
    """
    Get schedule based on current environment.

    Returns:
        Environment-appropriate schedule
    """
    env = settings.ENV_NAME.lower()

    if env in ('development', 'dev', 'local'):
        return get_development_schedule()
    elif env in ('production', 'prod'):
        return get_production_schedule()
    else:
        # Default to base schedule for staging/testing
        return get_beat_schedule()


# Configuration for beat scheduler persistence
def get_beat_scheduler_config() -> Dict[str, Any]:
    """
    Get beat scheduler configuration with Redis coordination.

    Returns:
        Beat scheduler configuration
    """
    return {
        'beat_scheduler': 'celery.beat:PersistentScheduler',
        'beat_schedule_filename': '/app/celerybeat-schedule/celerybeat-schedule.db',
        'beat_max_loop_interval': 60,
        'beat_sync_every': 180,  # Sync to storage every 3 minutes

        # Redis coordination for multiple beat instances
        'beat_redis_coordination': {
            'enabled': True,
            'redis_url': settings.REDIS_URL,
            'lock_key': 'celery_beat_lock',
            'lock_timeout': 300,  # 5 minutes
        } if not settings.ENV_NAME.lower().startswith('dev') else {'enabled': False},
    }
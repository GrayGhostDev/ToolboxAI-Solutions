"""
Multi-Tenant Database Configuration

Configuration settings and utilities for multi-tenant database operations.
"""

import os
from typing import Dict, Any, Optional
from uuid import UUID
from enum import Enum

from database.models.tenant import SubscriptionTier, OrganizationStatus


class TenantConfig:
    """Configuration class for multi-tenant settings"""

    # Default subscription limits
    SUBSCRIPTION_LIMITS = {
        SubscriptionTier.FREE: {
            'max_users': 5,
            'max_classes': 2,
            'max_storage_gb': 0.5,
            'max_api_calls_per_month': 500,
            'max_roblox_sessions': 2,
            'features': ['basic_lessons', 'basic_quizzes'],
            'support_level': 'community'
        },
        SubscriptionTier.BASIC: {
            'max_users': 25,
            'max_classes': 10,
            'max_storage_gb': 5.0,
            'max_api_calls_per_month': 5000,
            'max_roblox_sessions': 10,
            'features': ['basic_lessons', 'basic_quizzes', 'progress_tracking', 'basic_analytics'],
            'support_level': 'email'
        },
        SubscriptionTier.PROFESSIONAL: {
            'max_users': 100,
            'max_classes': 50,
            'max_storage_gb': 25.0,
            'max_api_calls_per_month': 25000,
            'max_roblox_sessions': 25,
            'features': [
                'basic_lessons', 'basic_quizzes', 'progress_tracking', 'advanced_analytics',
                'custom_branding', 'sso_integration', 'advanced_reporting'
            ],
            'support_level': 'priority'
        },
        SubscriptionTier.ENTERPRISE: {
            'max_users': 1000,
            'max_classes': 500,
            'max_storage_gb': 100.0,
            'max_api_calls_per_month': 100000,
            'max_roblox_sessions': 100,
            'features': [
                'basic_lessons', 'basic_quizzes', 'progress_tracking', 'advanced_analytics',
                'custom_branding', 'sso_integration', 'advanced_reporting', 'api_access',
                'webhook_integration', 'custom_integrations', 'dedicated_support'
            ],
            'support_level': 'dedicated'
        },
        SubscriptionTier.EDUCATION: {
            'max_users': 500,
            'max_classes': 100,
            'max_storage_gb': 50.0,
            'max_api_calls_per_month': 50000,
            'max_roblox_sessions': 50,
            'features': [
                'basic_lessons', 'basic_quizzes', 'progress_tracking', 'advanced_analytics',
                'custom_branding', 'student_privacy_compliance', 'gradebook_integration',
                'parent_portal'
            ],
            'support_level': 'education'
        }
    }

    # Trial configuration
    TRIAL_DURATION_DAYS = int(os.getenv('TRIAL_DURATION_DAYS', '30'))
    TRIAL_TIER = SubscriptionTier.PROFESSIONAL  # Give trial users professional features

    # Organization defaults
    DEFAULT_ORGANIZATION_SETTINGS = {
        'theme': 'default',
        'language': 'en-US',
        'timezone': 'UTC',
        'coppa_compliance': True,
        'ferpa_compliance': False,
        'audit_logs_retention_days': 365,
        'session_timeout_minutes': 60,
        'password_policy': {
            'min_length': 8,
            'require_uppercase': True,
            'require_lowercase': True,
            'require_numbers': True,
            'require_symbols': False,
            'expiration_days': 0  # 0 = no expiration
        },
        'notification_settings': {
            'email_notifications': True,
            'weekly_reports': True,
            'usage_alerts': True,
            'security_alerts': True
        }
    }

    # Feature flags
    FEATURE_FLAGS = {
        'enable_multi_tenancy': os.getenv('ENABLE_MULTI_TENANCY', 'true').lower() == 'true',
        'enable_rls': os.getenv('ENABLE_RLS', 'true').lower() == 'true',
        'enable_usage_tracking': os.getenv('ENABLE_USAGE_TRACKING', 'true').lower() == 'true',
        'enable_subscription_limits': os.getenv('ENABLE_SUBSCRIPTION_LIMITS', 'true').lower() == 'true',
        'enable_tenant_isolation_strict': os.getenv('ENABLE_TENANT_ISOLATION_STRICT', 'true').lower() == 'true'
    }

    @classmethod
    def get_subscription_limits(cls, tier: SubscriptionTier) -> Dict[str, Any]:
        """Get subscription limits for a tier"""
        return cls.SUBSCRIPTION_LIMITS.get(tier, cls.SUBSCRIPTION_LIMITS[SubscriptionTier.FREE])

    @classmethod
    def get_trial_limits(cls) -> Dict[str, Any]:
        """Get limits for trial organizations"""
        return cls.SUBSCRIPTION_LIMITS.get(cls.TRIAL_TIER, cls.SUBSCRIPTION_LIMITS[SubscriptionTier.FREE])

    @classmethod
    def is_feature_enabled(cls, feature: str) -> bool:
        """Check if a feature is enabled"""
        return cls.FEATURE_FLAGS.get(feature, False)

    @classmethod
    def get_default_settings(cls) -> Dict[str, Any]:
        """Get default organization settings"""
        return cls.DEFAULT_ORGANIZATION_SETTINGS.copy()


class DatabaseConfig:
    """Database-specific configuration for multi-tenancy"""

    # Connection pool settings
    POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '10'))
    MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '20'))
    POOL_TIMEOUT = int(os.getenv('DB_POOL_TIMEOUT', '30'))
    POOL_RECYCLE = int(os.getenv('DB_POOL_RECYCLE', '3600'))

    # RLS settings
    RLS_ENABLED = os.getenv('RLS_ENABLED', 'true').lower() == 'true'
    RLS_BYPASS_ROLE = os.getenv('RLS_BYPASS_ROLE', 'super_admin')

    # Query optimization
    QUERY_TIMEOUT_SECONDS = int(os.getenv('QUERY_TIMEOUT_SECONDS', '30'))
    ENABLE_QUERY_LOGGING = os.getenv('ENABLE_QUERY_LOGGING', 'false').lower() == 'true'

    # Tenant context settings
    TENANT_CONTEXT_REQUIRED = os.getenv('TENANT_CONTEXT_REQUIRED', 'true').lower() == 'true'
    ALLOW_CROSS_TENANT_QUERIES = os.getenv('ALLOW_CROSS_TENANT_QUERIES', 'false').lower() == 'true'

    # Backup and maintenance
    BACKUP_RETENTION_DAYS = int(os.getenv('BACKUP_RETENTION_DAYS', '30'))
    ENABLE_AUDIT_LOGGING = os.getenv('ENABLE_AUDIT_LOGGING', 'true').lower() == 'true'


class SecurityConfig:
    """Security configuration for multi-tenant operations"""

    # Encryption settings
    ENABLE_FIELD_ENCRYPTION = os.getenv('ENABLE_FIELD_ENCRYPTION', 'false').lower() == 'true'
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', '')

    # Access control
    SUPER_ADMIN_EMAILS = os.getenv('SUPER_ADMIN_EMAILS', '').split(',') if os.getenv('SUPER_ADMIN_EMAILS') else []
    ENABLE_IP_WHITELIST = os.getenv('ENABLE_IP_WHITELIST', 'false').lower() == 'true'
    ALLOWED_IP_RANGES = os.getenv('ALLOWED_IP_RANGES', '').split(',') if os.getenv('ALLOWED_IP_RANGES') else []

    # Session security
    SESSION_TIMEOUT_MINUTES = int(os.getenv('SESSION_TIMEOUT_MINUTES', '60'))
    ENABLE_SESSION_PINNING = os.getenv('ENABLE_SESSION_PINNING', 'true').lower() == 'true'

    # Data protection
    ENABLE_DATA_MASKING = os.getenv('ENABLE_DATA_MASKING', 'true').lower() == 'true'
    ENABLE_PII_DETECTION = os.getenv('ENABLE_PII_DETECTION', 'true').lower() == 'true'

    # Compliance
    COPPA_COMPLIANCE_REQUIRED = os.getenv('COPPA_COMPLIANCE_REQUIRED', 'true').lower() == 'true'
    FERPA_COMPLIANCE_REQUIRED = os.getenv('FERPA_COMPLIANCE_REQUIRED', 'false').lower() == 'true'
    GDPR_COMPLIANCE_REQUIRED = os.getenv('GDPR_COMPLIANCE_REQUIRED', 'true').lower() == 'true'


class UsageTrackingConfig:
    """Configuration for usage tracking and billing"""

    # Tracking intervals
    USAGE_LOG_INTERVAL_HOURS = int(os.getenv('USAGE_LOG_INTERVAL_HOURS', '24'))  # Daily by default
    REAL_TIME_TRACKING = os.getenv('REAL_TIME_TRACKING', 'false').lower() == 'true'

    # Billing configuration
    BILLING_CYCLE_DAYS = int(os.getenv('BILLING_CYCLE_DAYS', '30'))
    GRACE_PERIOD_DAYS = int(os.getenv('GRACE_PERIOD_DAYS', '7'))

    # Usage alerts
    USAGE_WARNING_THRESHOLD = float(os.getenv('USAGE_WARNING_THRESHOLD', '0.8'))  # 80%
    USAGE_CRITICAL_THRESHOLD = float(os.getenv('USAGE_CRITICAL_THRESHOLD', '0.95'))  # 95%

    # Overage handling
    ALLOW_OVERAGE = os.getenv('ALLOW_OVERAGE', 'true').lower() == 'true'
    OVERAGE_MULTIPLIER = float(os.getenv('OVERAGE_MULTIPLIER', '1.5'))


class TenantValidator:
    """Validator for tenant-related operations"""

    @staticmethod
    def validate_organization_name(name: str) -> bool:
        """Validate organization name"""
        if not name or len(name.strip()) < 2:
            return False
        if len(name) > 200:
            return False
        return True

    @staticmethod
    def validate_organization_slug(slug: str) -> bool:
        """Validate organization slug"""
        if not slug or len(slug) < 2:
            return False
        if len(slug) > 100:
            return False
        # Allow only alphanumeric characters and hyphens
        if not all(c.isalnum() or c == '-' for c in slug):
            return False
        # Cannot start or end with hyphen
        if slug.startswith('-') or slug.endswith('-'):
            return False
        return True

    @staticmethod
    def validate_subscription_tier(tier: str) -> bool:
        """Validate subscription tier"""
        try:
            SubscriptionTier(tier)
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_usage_limits(limits: Dict[str, Any]) -> bool:
        """Validate usage limits"""
        required_fields = ['max_users', 'max_classes', 'max_storage_gb', 'max_api_calls_per_month']
        for field in required_fields:
            if field not in limits:
                return False
            if not isinstance(limits[field], (int, float)) or limits[field] < 0:
                return False
        return True


# Global configuration instance
tenant_config = TenantConfig()
database_config = DatabaseConfig()
security_config = SecurityConfig()
usage_tracking_config = UsageTrackingConfig()
validator = TenantValidator()

# Export commonly used items
__all__ = [
    'TenantConfig',
    'DatabaseConfig',
    'SecurityConfig',
    'UsageTrackingConfig',
    'TenantValidator',
    'tenant_config',
    'database_config',
    'security_config',
    'usage_tracking_config',
    'validator'
]
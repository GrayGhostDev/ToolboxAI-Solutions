"""
Backend Services Module
Central location for all backend services
"""

# Import the unified email service MODULE, not individual attributes
# This prevents the module from being replaced with an instance
from . import email_service

# Import specific classes and enums for convenience
# But avoid importing 'email_service' as an instance to prevent module replacement
from .email_service import (
    # Classes only - no instances with conflicting names
    SendGridEmailService,
    MockEmailService,
    EmailService,  # Legacy alias for SendGridEmailService

    # Factory functions
    get_email_service,
    get_email_service_singleton,

    # Enums and models
    EmailType,
    EmailPriority,
    EmailRecipient,
    EmailAttachment,

    # Utility
    get_active_service_type,
)

# For backwards compatibility, create service instances with different names
# to avoid conflicting with the module name
email_service_instance = email_service.email_service
default_email_service = email_service.default_email_service
sendgrid_email_service = email_service.sendgrid_email_service
mock_email_service = email_service.mock_email_service
SendGridServiceInstance = email_service.SendGridServiceInstance
MockEmailServiceInstance = email_service.MockEmailServiceInstance

# Import other services as they exist
try:
    from .stripe_service import stripe_service
except ImportError:
    stripe_service = None

try:
    from .pusher_service import pusher_service
except ImportError:
    pusher_service = None

try:
    from .tenant_manager import TenantManager, get_tenant_manager
except ImportError:  # pragma: no cover - optional dependency during bootstrap
    TenantManager = None
    get_tenant_manager = None

# Export all services - maintaining backwards compatibility
__all__ = [
    # Email service MODULE (not instance)
    "email_service",  # This is the MODULE

    # Email service instances (with clear names)
    "email_service_instance",
    "default_email_service",
    "sendgrid_email_service",
    "mock_email_service",

    # Email service classes
    "EmailService",
    "SendGridEmailService",
    "MockEmailService",

    # Instance aliases
    "SendGridServiceInstance",
    "MockEmailServiceInstance",

    # Factory functions
    "get_email_service",
    "get_email_service_singleton",

    # Enums and models
    "EmailPriority",
    "EmailType",
    "EmailRecipient",
    "EmailAttachment",

    # Utility
    "get_active_service_type",

    # Other services
    "stripe_service",
    "pusher_service",
    "TenantManager",
    "get_tenant_manager",
]

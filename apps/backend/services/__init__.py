"""
Backend Services Module
Central location for all backend services
"""

# Import the email package (not email_service)
from . import email as email_pkg

# Import specific classes and enums for convenience from the email package
from .email import (
    EmailAttachment,
    EmailPriority,
    EmailRecipient,
    EmailType,
    MockEmailService,
    SendGridEmailService,
    email_service,  # Default instance
    get_email_service,
    get_email_service_singleton,
)

# For backwards compatibility, create service instances with different names
# EmailService is an alias for SendGridEmailService
EmailService = SendGridEmailService
email_service_instance = email_service
default_email_service = email_service
sendgrid_email_service = email_service  # All point to the same default instance
mock_email_service = MockEmailService()  # Create a mock instance

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
    # Email package and service
    "email_pkg",  # The email package module
    "email_service",  # Default email service instance
    # Email service instances (with clear names)
    "email_service_instance",
    "default_email_service",
    "sendgrid_email_service",
    "mock_email_service",
    # Email service classes
    "EmailService",
    "SendGridEmailService",
    "MockEmailService",
    # Factory functions
    "get_email_service",
    "get_email_service_singleton",
    # Enums and models
    "EmailPriority",
    "EmailType",
    "EmailRecipient",
    "EmailAttachment",
    # Other services
    "stripe_service",
    "pusher_service",
    "TenantManager",
    "get_tenant_manager",
]

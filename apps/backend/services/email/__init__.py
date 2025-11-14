"""
Email Service Module for ToolBoxAI Educational Platform

Comprehensive email delivery system with SendGrid integration, queue management,
retry logic, and template rendering for production deployments.

Features:
- SendGrid email delivery (production)
- Mock email service (development/testing)
- Email queue with retry logic
- Priority-based processing
- Dead letter queue
- Template engine with Jinja2
- Monitoring and analytics

Author: ToolBoxAI Team
Created: 2025-11-09
Version: 1.0.0
"""

# Factory for automatic service selection
from .factory import get_email_service, get_email_service_singleton

# Mock implementation for development
from .mock import MockEmailService

# Queue service for reliable delivery
from .queue import EmailJob, EmailQueueService, EmailStatus

# SendGrid implementation and types
from .sendgrid import (
    EmailAttachment,
    EmailPriority,
    EmailRecipient,
    EmailType,
    SendGridEmailService,
)

# Template engine
from .templates import EmailTemplateEngine

# Backward compatibility - provide email_service with lazy initialization
# Use __getattr__ to defer initialization until first access, avoiding circular imports
_email_service_instance = None


def __getattr__(name):
    """
    Lazy initialization of email_service to avoid circular imports.

    This function is called when an attribute is not found in the module.
    We use it to defer the initialization of email_service until it's actually needed.
    """
    global _email_service_instance

    if name == "email_service":
        if _email_service_instance is None:
            _email_service_instance = get_email_service_singleton()
        return _email_service_instance

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    # Service implementations
    "SendGridEmailService",
    "MockEmailService",
    # Factory functions
    "get_email_service",
    "get_email_service_singleton",
    # Queue service
    "EmailQueueService",
    "EmailStatus",
    "EmailJob",
    # Template engine
    "EmailTemplateEngine",
    # Types and enums
    "EmailPriority",
    "EmailType",
    "EmailRecipient",
    "EmailAttachment",
    # Default instance
    "email_service",
]

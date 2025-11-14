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

# Backward compatibility - provide email_service as a lazy-loaded singleton
# Don't import from .base to avoid circular imports during module initialization
# Instead, create a module-level singleton that's initialized on first access
_email_service_instance = None


def _get_email_service_lazy():
    """Lazy initialization of email service to avoid circular imports"""
    global _email_service_instance
    if _email_service_instance is None:
        _email_service_instance = get_email_service_singleton()
    return _email_service_instance


# For backwards compatibility, provide email_service as the singleton
# This will be initialized on first import, after the module is fully loaded
email_service = get_email_service_singleton()

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

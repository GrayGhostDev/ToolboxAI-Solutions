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

# SendGrid implementation and types
from .sendgrid import (
    SendGridEmailService,
    EmailPriority,
    EmailType,
    EmailRecipient,
    EmailAttachment,
)

# Mock implementation for development
from .mock import MockEmailService

# Factory for automatic service selection
from .factory import (
    get_email_service,
    get_email_service_singleton,
)

# Queue service for reliable delivery
from .queue import (
    EmailQueueService,
    EmailStatus,
    EmailJob,
)

# Template engine
from .templates import EmailTemplateEngine

# Backward compatibility - import from base if it has a default instance
try:
    from .base import email_service
except ImportError:
    # Create default instance if base doesn't provide one
    email_service = get_email_service()

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

"""
Unified Email Service Interface
Maintains both production (SendGrid) and mock implementations
Preserves ALL global instances for backwards compatibility
@version 3.1.0
@since 2025-09-27
"""

import os
import logging

logger = logging.getLogger(__name__)

# Import the actual implementations with error handling
# Avoid importing 'email_service' from factory to prevent naming conflicts
try:
    from apps.backend.services.email_service_factory import (
        get_email_service,
        get_email_service_singleton
    )
    # Don't import 'email_service' from factory - we'll create our own
except ImportError as e:
    logger.error(f"Could not import email factory: {e}")
    get_email_service = None
    get_email_service_singleton = None

try:
    from apps.backend.services.email_service_sendgrid import (
        SendGridEmailService,
        email_service as sendgrid_instance,  # Rename to avoid conflict
        EmailService as SendGridEmailServiceClass,
        EmailType,
        EmailPriority,
        EmailRecipient,
        EmailAttachment
    )
except ImportError as e:
    logger.error(f"Could not import SendGrid service: {e}")
    SendGridEmailService = None
    sendgrid_instance = None
    SendGridEmailServiceClass = None

    # Create fallback enums if SendGrid not available
    from enum import Enum

    class EmailType(str, Enum):
        TRANSACTIONAL = "transactional"
        MARKETING = "marketing"
        NOTIFICATION = "notification"
        SYSTEM = "system"
        WELCOME = "welcome"
        PASSWORD_RESET = "password_reset"
        VERIFICATION = "verification"

    class EmailPriority(str, Enum):
        LOW = "low"
        NORMAL = "normal"
        HIGH = "high"
        URGENT = "urgent"

    class EmailRecipient:
        def __init__(self, email: str, name: str = None):
            self.email = email
            self.name = name

    class EmailAttachment:
        def __init__(self, content: bytes, filename: str, content_type: str = None):
            self.content = content
            self.filename = filename
            self.content_type = content_type

try:
    from apps.backend.services.email_service_mock import (
        MockEmailService,
        mock_email_service as mock_instance,  # Rename to avoid conflict
        MockEmailServiceInstance
    )
except ImportError as e:
    logger.error(f"Could not import Mock service: {e}")
    MockEmailService = None
    mock_instance = None
    MockEmailServiceInstance = None

# Create our own email_service instance using the SINGLETON factory
# This ensures consistency across all imports
if get_email_service_singleton:
    email_service = get_email_service_singleton()
    logger.info(f"Primary email service initialized: {type(email_service).__name__}")
else:
    # Fallback to mock if factory not available
    if mock_instance:
        email_service = mock_instance
        logger.warning("Using mock email service as fallback")
    else:
        logger.error("No email service available!")
        email_service = None

# PRESERVE ALL GLOBAL INSTANCES FOR BOTH PRODUCTION AND MOCK
# These are maintained for backwards compatibility and to ensure
# both implementations are always accessible

# Production (SendGrid) instances
if sendgrid_instance:
    sendgrid_email_service = sendgrid_instance  # Global SendGrid instance
    SendGridServiceInstance = sendgrid_instance  # Alternative alias
else:
    sendgrid_email_service = None
    SendGridServiceInstance = None

# SendGrid class alias for compatibility
if SendGridEmailServiceClass:
    EmailService = SendGridEmailServiceClass  # Legacy name for compatibility
else:
    EmailService = SendGridEmailService  # Use the actual class if available

# Mock instances
if mock_instance:
    mock_email_service = mock_instance  # Global Mock instance
    MockEmailServiceInstance = mock_instance  # Keep the original alias
else:
    mock_email_service = None
    MockEmailServiceInstance = None

# Factory function exports - these are functions, not instances
get_email_service = get_email_service  # Factory function
get_email_service_singleton = get_email_service_singleton  # Singleton factory

# Default service (uses factory to determine which to use)
default_email_service = email_service  # Points to whichever service is active

# Additional utility function for testing
def get_active_service_type():
    """Get the type of the currently active email service"""
    if email_service:
        return type(email_service).__name__
    return None

# Log the final configuration
logger.info(f"""
Email Service Configuration:
- Active Service: {get_active_service_type()}
- SendGrid Available: {sendgrid_email_service is not None}
- Mock Available: {mock_email_service is not None}
- Factory Available: {get_email_service is not None}
""")

# Export all globals for backwards compatibility
__all__ = [
    # Main service instance
    'email_service',
    'default_email_service',

    # SendGrid instances and classes
    'sendgrid_email_service',
    'SendGridEmailService',
    'SendGridServiceInstance',
    'EmailService',  # Legacy alias for SendGridEmailService

    # Mock instances and classes
    'mock_email_service',
    'MockEmailService',
    'MockEmailServiceInstance',

    # Factory functions
    'get_email_service',
    'get_email_service_singleton',

    # Enums and models
    'EmailType',
    'EmailPriority',
    'EmailRecipient',
    'EmailAttachment',

    # Utility
    'get_active_service_type',
]
"""
Email Service Factory
Automatically selects the appropriate email service based on configuration
"""

import logging
import os

logger = logging.getLogger(__name__)


def get_email_service(force_mock: bool = False):
    """
    Get the appropriate email service based on configuration

    Args:
        force_mock: Force use of mock service even if SendGrid is configured

    Returns:
        Email service instance (SendGrid or Mock)
    """
    # Check if we should use mock
    use_mock = (
        force_mock
        or os.getenv("EMAIL_USE_MOCK", "false").lower() == "true"
        or os.getenv("ENVIRONMENT", "development").lower() in ["test", "testing"]
    )

    if use_mock:
        logger.info("📧 Using MockEmailService (emails will be logged, not sent)")
        from apps.backend.services.email.mock import MockEmailService

        return MockEmailService()

    # Try to use SendGrid
    api_key = os.getenv("SENDGRID_API_KEY")

    if not api_key:
        logger.warning("⚠️  No SENDGRID_API_KEY found, using MockEmailService")
        from apps.backend.services.email.mock import MockEmailService

        return MockEmailService()

    # Validate API key format
    if not api_key.startswith("SG."):
        logger.warning("⚠️  Invalid SENDGRID_API_KEY format, using MockEmailService")
        from apps.backend.services.email.mock import MockEmailService

        return MockEmailService()

    # Try to initialize SendGrid
    try:
        from sendgrid import SendGridAPIClient

        from apps.backend.services.email.sendgrid import SendGridEmailService

        # Test if the API key is valid by trying a simple API call
        try:
            sg = SendGridAPIClient(api_key)
            # Try to get API key scopes (this will fail with 401 if invalid)
            sg.client.scopes.get()

            logger.info("✅ Using SendGridEmailService (API key validated)")
            return SendGridEmailService()

        except Exception as auth_error:
            error_str = str(auth_error)
            if "401" in error_str or "Unauthorized" in error_str:
                logger.warning("⚠️  SendGrid API key is invalid (401 Unauthorized)")
                logger.info("   Using MockEmailService as fallback")
                from apps.backend.services.email.mock import MockEmailService

                return MockEmailService()
            elif "Maximum credits exceeded" in error_str:
                logger.warning("⚠️  SendGrid daily limit exceeded")
                logger.info("   Using MockEmailService as fallback")
                from apps.backend.services.email.mock import MockEmailService

                return MockEmailService()
            else:
                # Try to use it anyway, might be a network issue
                logger.warning(f"⚠️  Could not validate API key: {auth_error}")
                logger.info("   Attempting to use SendGridEmailService anyway")
                return SendGridEmailService()

    except ImportError as e:
        logger.error(f"❌ SendGrid not installed: {e}")
        logger.info("   Install with: pip install sendgrid")
        logger.info("   Using MockEmailService as fallback")
        from apps.backend.services.email.mock import MockEmailService

        return MockEmailService()

    except Exception as e:
        logger.error(f"❌ Error initializing SendGrid: {e}")
        logger.info("   Using MockEmailService as fallback")
        from apps.backend.services.email.mock import MockEmailService

        return MockEmailService()


# Create a singleton instance
_email_service: object | None = None


def get_email_service_singleton(force_mock: bool = False):
    """
    Get singleton email service instance

    Args:
        force_mock: Force use of mock service

    Returns:
        Singleton email service instance
    """
    global _email_service

    # Only create new instance if none exists
    # force_mock only affects which type is created, not whether to create new
    if _email_service is None:
        _email_service = get_email_service(force_mock)

    return _email_service


# Convenience export
email_service = get_email_service_singleton()

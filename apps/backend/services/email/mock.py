"""
Mock Email Service for Development/Testing
Implements the same interface as SendGrid but logs emails instead of sending
"""

import logging
from datetime import datetime, timezone
from typing import Any

from apps.backend.services.email.sendgrid import (
    EmailRecipient,
    EmailType,
)

logger = logging.getLogger(__name__)


class MockEmailService:
    """
    Mock email service that logs instead of sending
    Useful for development when SendGrid API key is not available
    """

    def __init__(self):
        """Initialize mock email service"""
        self.from_email = "noreply@toolboxai.com"
        self.from_name = "ToolBoxAI"
        self.sent_emails = []  # Store sent emails for inspection
        logger.info("🎭 MockEmailService initialized (emails will be logged, not sent)")

    async def send_email(
        self,
        to_emails: str | list[str] | list[EmailRecipient],
        subject: str,
        html_content: str | None = None,
        text_content: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Mock send email - logs the email instead of sending
        """
        # Normalize recipients
        if isinstance(to_emails, str):
            recipients = [to_emails]
        elif isinstance(to_emails, EmailRecipient):
            recipients = [to_emails.email]
        elif isinstance(to_emails, list):
            recipients = []
            for r in to_emails:
                if isinstance(r, str):
                    recipients.append(r)
                elif isinstance(r, EmailRecipient):
                    recipients.append(r.email)
        else:
            recipients = []

        # Create mock message ID
        message_id = f"mock-{datetime.now(timezone.utc).timestamp()}"

        # Store email data
        email_data = {
            "message_id": message_id,
            "to": recipients,
            "subject": subject,
            "html_content": html_content[:200] if html_content else None,
            "text_content": text_content[:200] if text_content else None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **kwargs,
        }
        self.sent_emails.append(email_data)

        # Log the email
        logger.info("=" * 60)
        logger.info("📧 MOCK EMAIL SENT (not actually sent)")
        logger.info("=" * 60)
        logger.info(f"To: {', '.join(recipients)}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Message ID: {message_id}")

        if html_content:
            logger.info(f"HTML Preview: {html_content[:100]}...")
        if text_content:
            logger.info(f"Text Preview: {text_content[:100]}...")

        logger.info("=" * 60)

        # Return success response
        return {
            "success": True,
            "message_id": message_id,
            "status_code": 202,
            "provider": "mock",
            "note": "Email logged but not sent (mock mode)",
        }

    async def send_welcome_email(
        self, user_email: str, user_name: str, verification_url: str | None = None, **kwargs
    ) -> dict[str, Any]:
        """Mock welcome email"""
        return await self.send_email(
            to_emails=user_email,
            subject=f"Welcome to {self.from_name}, {user_name}!",
            html_content=kwargs.get("html_content", f"<h2>Welcome {user_name}!</h2>"),
            text_content=kwargs.get("text_content", f"Welcome {user_name}!"),
            email_type=EmailType.WELCOME,
        )

    async def send_password_reset_email(
        self, user_email: str, user_name: str, reset_token: str, reset_url: str, **kwargs
    ) -> dict[str, Any]:
        """Mock password reset email"""
        return await self.send_email(
            to_emails=user_email,
            subject="Reset Your Password",
            html_content=kwargs.get("html_content", f"<p>Reset password for {user_name}</p>"),
            text_content=kwargs.get("text_content", f"Reset password for {user_name}"),
            email_type=EmailType.PASSWORD_RESET,
        )

    async def send_verification_email(
        self,
        user_email: str,
        user_name: str,
        verification_code: str,
        verification_url: str,
        **kwargs,
    ) -> dict[str, Any]:
        """Mock verification email"""
        return await self.send_email(
            to_emails=user_email,
            subject="Verify Your Email",
            html_content=kwargs.get("html_content", f"<p>Verify email for {user_name}</p>"),
            text_content=kwargs.get("text_content", f"Verify email for {user_name}"),
            email_type=EmailType.VERIFICATION,
        )

    def get_sent_emails(self) -> list[dict[str, Any]]:
        """Get all sent emails (for testing)"""
        return self.sent_emails

    def clear_sent_emails(self):
        """Clear sent emails log"""
        self.sent_emails = []
        logger.info("Cleared mock email log")


# Global singleton instances for consistency with production
mock_email_service = MockEmailService()

# Alias for compatibility
MockEmailServiceInstance = mock_email_service

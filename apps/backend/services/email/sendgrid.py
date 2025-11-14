"""
SendGrid Email Service Implementation
Production-ready email service using SendGrid for Render/Supabase deployment
Implements full SendGrid v3 API with comprehensive features
@module email_service_sendgrid
@version 3.0.0
@since 2025-09-26
"""

import base64
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

# Configure logger
logger = logging.getLogger(__name__)

# SendGrid imports with proper error handling
try:
    from python_http_client.exceptions import HTTPError
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import (  # SandBoxMode removed - now use mail_settings.sandbox_mode = True/False directly
        Asm,
        Attachment,
        BatchId,
        Bcc,
        BypassListManagement,
        Category,
        Cc,
        ClickTracking,
        Content,
        CustomArg,
        Disposition,
        Email,
        FileContent,
        FileName,
        FileType,
        FooterSettings,
        Ganalytics,
        GroupId,
        GroupsToDisplay,
        Header,
        IpPoolName,
        Mail,
        MailSettings,
        OpenTracking,
        Personalization,
        ReplyTo,
        SubscriptionTracking,
        Substitution,
        To,
        TrackingSettings,
    )

    SENDGRID_AVAILABLE = True
    logger.info("SendGrid SDK loaded successfully")
except ImportError as e:
    logger.error(f"SendGrid SDK not available: {e}")
    logger.error("Install with: pip install sendgrid")
    SENDGRID_AVAILABLE = False

    # Create dummy classes for type hints
    class Mail:
        pass

    class SendGridAPIClient:
        pass

    class HTTPError(Exception):
        pass


# Jinja2 for templates
try:
    import jinja2
    from jinja2 import Environment, FileSystemLoader, select_autoescape

    JINJA2_AVAILABLE = True
except ImportError:
    logger.warning("Jinja2 not available. Install with: pip install jinja2")
    JINJA2_AVAILABLE = False

# HTML processing
try:
    import bleach
    from bs4 import BeautifulSoup
    from premailer import transform

    HTML_PROCESSING_AVAILABLE = True
except ImportError:
    logger.warning("HTML processing libraries not available")
    logger.warning("Install with: pip install bleach beautifulsoup4 premailer")
    HTML_PROCESSING_AVAILABLE = False

from apps.backend.core.cache import CacheConfig, CacheKey, cache
from apps.backend.core.config import settings


class EmailPriority(str, Enum):
    """Email priority levels"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class EmailType(str, Enum):
    """Email types for categorization"""

    TRANSACTIONAL = "transactional"
    MARKETING = "marketing"
    NOTIFICATION = "notification"
    SYSTEM = "system"
    WELCOME = "welcome"
    VERIFICATION = "verification"
    PASSWORD_RESET = "password_reset"
    SUBSCRIPTION = "subscription"
    INVOICE = "invoice"


@dataclass
class EmailRecipient:
    """Email recipient with optional personalization"""

    email: str
    name: str | None = None
    substitutions: dict[str, Any] = field(default_factory=dict)
    custom_args: dict[str, str] = field(default_factory=dict)


@dataclass
class EmailAttachment:
    """Email attachment data"""

    filename: str
    content: str | bytes
    type: str
    disposition: str = "attachment"
    content_id: str | None = None


class SendGridEmailService:
    """
    Complete SendGrid email service implementation
    Handles all email operations through SendGrid v3 API
    """

    def __init__(self):
        """Initialize SendGrid email service"""
        self.api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = (
            settings.DEFAULT_FROM_EMAIL
            if hasattr(settings, "DEFAULT_FROM_EMAIL")
            else "noreply@toolboxai.com"
        )
        self.from_name = (
            settings.DEFAULT_FROM_NAME if hasattr(settings, "DEFAULT_FROM_NAME") else "ToolBoxAI"
        )
        self.sandbox_mode = (
            settings.EMAIL_SANDBOX_MODE if hasattr(settings, "EMAIL_SANDBOX_MODE") else False
        )

        # Initialize SendGrid client
        self.client = self._initialize_client()

        # Initialize template environment
        self.template_env = self._initialize_templates()

        # Email tracking settings
        self.enable_tracking = (
            settings.EMAIL_ENABLE_TRACKING if hasattr(settings, "EMAIL_ENABLE_TRACKING") else True
        )
        self.enable_click_tracking = (
            settings.EMAIL_ENABLE_CLICK_TRACKING
            if hasattr(settings, "EMAIL_ENABLE_CLICK_TRACKING")
            else True
        )
        self.enable_open_tracking = (
            settings.EMAIL_ENABLE_OPEN_TRACKING
            if hasattr(settings, "EMAIL_ENABLE_OPEN_TRACKING")
            else True
        )

        # Unsubscribe settings
        self.enable_unsubscribe = (
            settings.EMAIL_ENABLE_UNSUBSCRIBE
            if hasattr(settings, "EMAIL_ENABLE_UNSUBSCRIBE")
            else True
        )
        self.unsubscribe_group_id = (
            settings.SENDGRID_UNSUBSCRIBE_GROUP_ID
            if hasattr(settings, "SENDGRID_UNSUBSCRIBE_GROUP_ID")
            else None
        )

        logger.info(f"SendGrid Email Service initialized (sandbox={self.sandbox_mode})")

    def _initialize_client(self) -> SendGridAPIClient | None:
        """Initialize SendGrid API client"""
        if not SENDGRID_AVAILABLE:
            logger.error("SendGrid SDK not available")
            return None

        if not self.api_key:
            logger.error("SendGrid API key not configured")
            return None

        try:
            client = SendGridAPIClient(self.api_key)
            # Test the connection
            # Note: SendGrid doesn't have a direct ping, but we can validate the key format
            if not self.api_key.startswith("SG."):
                logger.warning("SendGrid API key format may be invalid")
            logger.info("SendGrid client initialized successfully")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize SendGrid client: {e}")
            return None

    def _initialize_templates(self) -> Environment | None:
        """Initialize Jinja2 template environment"""
        if not JINJA2_AVAILABLE:
            logger.warning("Jinja2 not available, templates disabled")
            return None

        try:
            template_dir = Path(__file__).parent.parent / "templates" / "emails"
            if not template_dir.exists():
                template_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created template directory: {template_dir}")

            env = Environment(
                loader=FileSystemLoader(str(template_dir)),
                autoescape=select_autoescape(["html", "xml"]),
                enable_async=True,
            )
            logger.info("Template environment initialized")
            return env
        except Exception as e:
            logger.error(f"Failed to initialize templates: {e}")
            return None

    async def send_email(
        self,
        to_emails: str | list[str] | list[EmailRecipient],
        subject: str,
        html_content: str | None = None,
        text_content: str | None = None,
        template_name: str | None = None,
        template_context: dict[str, Any] | None = None,
        from_email: str | None = None,
        from_name: str | None = None,
        reply_to: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        attachments: list[EmailAttachment] | None = None,
        categories: list[str] | None = None,
        custom_args: dict[str, str] | None = None,
        send_at: int | None = None,
        batch_id: str | None = None,
        asm_group_id: int | None = None,
        ip_pool_name: str | None = None,
        priority: EmailPriority = EmailPriority.NORMAL,
        email_type: EmailType = EmailType.TRANSACTIONAL,
    ) -> dict[str, Any]:
        """
        Send email through SendGrid

        Args:
            to_emails: Recipient email(s) or EmailRecipient objects
            subject: Email subject
            html_content: HTML content
            text_content: Plain text content
            template_name: Template name to render
            template_context: Template context data
            from_email: Override sender email
            from_name: Override sender name
            reply_to: Reply-to email
            cc: CC recipients
            bcc: BCC recipients
            attachments: List of attachments
            categories: Email categories for analytics
            custom_args: Custom arguments for tracking
            send_at: Unix timestamp to send email
            batch_id: Batch ID for bulk sending
            asm_group_id: Unsubscribe group ID
            ip_pool_name: IP pool for sending
            priority: Email priority
            email_type: Email type for categorization

        Returns:
            Dict with success status and message ID
        """
        try:
            if not self.client:
                raise ValueError("SendGrid client not initialized")

            # Render template if provided
            if template_name and self.template_env:
                html_content, text_content = await self._render_template(
                    template_name, template_context or {}
                )

            # Process HTML content
            if html_content:
                html_content = self._process_html(html_content)

            # Generate text from HTML if not provided
            if html_content and not text_content:
                text_content = self._html_to_text(html_content)

            # Create mail object
            mail = self._create_mail_object(
                to_emails=to_emails,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                from_email=from_email or self.from_email,
                from_name=from_name or self.from_name,
                reply_to=reply_to,
                cc=cc,
                bcc=bcc,
                categories=categories or [email_type.value],
                custom_args=custom_args,
                send_at=send_at,
                batch_id=batch_id,
                asm_group_id=asm_group_id or self.unsubscribe_group_id,
                ip_pool_name=ip_pool_name,
            )

            # Add attachments
            if attachments:
                self._add_attachments(mail, attachments)

            # Configure tracking settings
            self._configure_tracking(mail)

            # Configure mail settings
            self._configure_mail_settings(mail)

            # Send email
            response = self.client.send(mail)

            # Extract message ID from response
            message_id = None
            if hasattr(response, "headers"):
                headers = response.headers
                # SendGrid python client returns headers as a special object
                # Try to access it safely
                try:
                    if isinstance(headers, dict):
                        message_id = headers.get("X-Message-Id")
                    elif hasattr(headers, "__getitem__"):
                        # Headers object supports bracket notation
                        message_id = (
                            headers.get("X-Message-Id", None)
                            if hasattr(headers, "get")
                            else headers["X-Message-Id"]
                        )
                    else:
                        # Try direct attribute access
                        for attr in ["X-Message-Id", "x-message-id", "X_Message_Id"]:
                            if hasattr(headers, attr):
                                message_id = getattr(headers, attr)
                                break
                except (KeyError, AttributeError, TypeError):
                    # If we can't get message ID, we'll generate one
                    pass

            # Generate fallback message ID if needed
            if not message_id:
                import uuid

                message_id = f"sg-{uuid.uuid4()}"

            # Cache email metadata
            await self._cache_email_metadata(
                message_id=message_id,
                to_emails=to_emails,
                subject=subject,
                email_type=email_type,
            )

            logger.info(f"Email sent successfully: {message_id}")

            return {
                "success": True,
                "message_id": message_id,
                "status_code": getattr(response, "status_code", 202),
                "provider": "sendgrid",
            }

        except HTTPError as e:
            error_detail = str(e)
            # Try to get error details if available
            if hasattr(e, "to_dict"):
                try:
                    error_detail = str(e.to_dict)
                except Exception:
                    pass
            elif hasattr(e, "body"):
                error_detail = str(e.body)

            logger.error(f"SendGrid API error: {error_detail}")
            return {
                "success": False,
                "error": error_detail,
                "status_code": getattr(e, "status_code", 500),
                "provider": "sendgrid",
            }
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return {"success": False, "error": str(e), "provider": "sendgrid"}

    def _create_mail_object(
        self,
        to_emails: str | list[str] | list[EmailRecipient],
        subject: str,
        html_content: str | None,
        text_content: str | None,
        from_email: str,
        from_name: str,
        reply_to: str | None,
        cc: list[str] | None,
        bcc: list[str] | None,
        categories: list[str],
        custom_args: dict[str, str] | None,
        send_at: int | None,
        batch_id: str | None,
        asm_group_id: int | None,
        ip_pool_name: str | None,
    ) -> Mail:
        """Create SendGrid Mail object"""
        mail = Mail()

        # Set sender
        mail.from_email = Email(from_email, from_name)

        # Set subject
        mail.subject = subject

        # Set content
        if text_content:
            mail.add_content(Content("text/plain", text_content))
        if html_content:
            mail.add_content(Content("text/html", html_content))

        # Process recipients
        if isinstance(to_emails, str):
            to_emails = [to_emails]
        elif isinstance(to_emails, EmailRecipient):
            to_emails = [to_emails]

        personalization = Personalization()

        for recipient in to_emails:
            if isinstance(recipient, EmailRecipient):
                to = To(recipient.email, recipient.name)
                personalization.add_to(to)

                # Add substitutions
                for key, value in recipient.substitutions.items():
                    personalization.add_substitution(Substitution(key, value))

                # Add custom args
                for key, value in recipient.custom_args.items():
                    personalization.add_custom_arg(CustomArg(key, value))
            else:
                personalization.add_to(To(recipient))

        # Add CC recipients
        if cc:
            for cc_email in cc:
                personalization.add_cc(Cc(cc_email))

        # Add BCC recipients
        if bcc:
            for bcc_email in bcc:
                personalization.add_bcc(Bcc(bcc_email))

        mail.add_personalization(personalization)

        # Set reply-to
        if reply_to:
            mail.reply_to = ReplyTo(reply_to)

        # Add categories
        for category in categories:
            mail.add_category(Category(category))

        # Add custom args
        if custom_args:
            for key, value in custom_args.items():
                mail.add_custom_arg(CustomArg(key, value))

        # Set send time
        if send_at:
            mail.send_at = send_at

        # Set batch ID
        if batch_id:
            mail.batch_id = BatchId(batch_id)

        # Set ASM group
        if asm_group_id:
            mail.asm = Asm(group_id=GroupId(asm_group_id))

        # Set IP pool
        if ip_pool_name:
            mail.ip_pool_name = IpPoolName(ip_pool_name)

        return mail

    def _add_attachments(self, mail: Mail, attachments: list[EmailAttachment]):
        """Add attachments to email"""
        for att in attachments:
            attachment = Attachment()

            # Encode content if needed
            if isinstance(att.content, bytes):
                content = base64.b64encode(att.content).decode()
            elif not att.content.startswith("data:"):
                content = base64.b64encode(att.content.encode()).decode()
            else:
                content = att.content

            attachment.file_content = FileContent(content)
            attachment.file_name = FileName(att.filename)
            attachment.file_type = FileType(att.type)
            attachment.disposition = Disposition(att.disposition)

            if att.content_id:
                attachment.content_id = att.content_id

            mail.add_attachment(attachment)

    def _configure_tracking(self, mail: Mail):
        """Configure email tracking settings"""
        tracking_settings = TrackingSettings()

        if self.enable_click_tracking:
            tracking_settings.click_tracking = ClickTracking(enable=True, enable_text=True)

        if self.enable_open_tracking:
            tracking_settings.open_tracking = OpenTracking(enable=True)

        if self.enable_unsubscribe:
            tracking_settings.subscription_tracking = SubscriptionTracking(
                enable=True,
                text="Unsubscribe",
                html="<a href='<%asm_group_unsubscribe_raw_url%>'>Unsubscribe</a>",
            )

        mail.tracking_settings = tracking_settings

    def _configure_mail_settings(self, mail: Mail):
        """Configure mail settings"""
        mail_settings = MailSettings()

        # Sandbox mode for testing (SendGrid v6+ uses boolean directly)
        if self.sandbox_mode:
            mail_settings.sandbox_mode = True

        mail.mail_settings = mail_settings

    def _process_html(self, html_content: str) -> str:
        """Process HTML content for email"""
        if not HTML_PROCESSING_AVAILABLE:
            return html_content

        try:
            # Inline CSS
            html_content = transform(html_content)

            # Sanitize HTML
            html_content = bleach.clean(
                html_content,
                tags=[
                    "a",
                    "abbr",
                    "acronym",
                    "b",
                    "blockquote",
                    "code",
                    "em",
                    "i",
                    "li",
                    "ol",
                    "strong",
                    "ul",
                    "p",
                    "br",
                    "span",
                    "div",
                    "table",
                    "thead",
                    "tbody",
                    "tr",
                    "td",
                    "th",
                    "h1",
                    "h2",
                    "h3",
                    "h4",
                    "h5",
                    "h6",
                    "img",
                    "hr",
                ],
                attributes={"*": ["style"], "a": ["href", "title"], "img": ["src", "alt"]},
                strip=True,  # Remove disallowed tags instead of escaping
            )
        except Exception as e:
            logger.warning(f"HTML processing failed: {e}")

        return html_content

    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML to plain text"""
        if not HTML_PROCESSING_AVAILABLE:
            # Simple fallback
            import re

            text = re.sub("<[^<]+?>", "", html_content)
            return " ".join(text.split())

        try:
            soup = BeautifulSoup(html_content, "html.parser")
            for script in soup(["script", "style"]):
                script.decompose()
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            return "\n".join(chunk for chunk in chunks if chunk)
        except Exception as e:
            logger.warning(f"HTML to text conversion failed: {e}")
            return html_content

    async def _render_template(
        self, template_name: str, context: dict[str, Any]
    ) -> tuple[str, str]:
        """Render email template"""
        if not self.template_env:
            raise ValueError("Template environment not initialized")

        try:
            # Add default context
            context["current_year"] = datetime.now().year
            context["app_name"] = self.from_name
            context["frontend_url"] = (
                settings.FRONTEND_URL
                if hasattr(settings, "FRONTEND_URL")
                else "https://toolboxai.com"
            )

            # Render HTML template
            html_template = self.template_env.get_template(f"{template_name}.html")
            html_content = await html_template.render_async(**context)

            # Try to render text template
            text_content = None
            try:
                text_template = self.template_env.get_template(f"{template_name}.txt")
                text_content = await text_template.render_async(**context)
            except jinja2.TemplateNotFound:
                # Generate from HTML
                text_content = self._html_to_text(html_content)

            return html_content, text_content

        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            raise

    async def _cache_email_metadata(
        self,
        message_id: str,
        to_emails: str | list[str] | list[EmailRecipient],
        subject: str,
        email_type: EmailType,
    ):
        """Cache email metadata for tracking"""
        try:
            if isinstance(to_emails, str):
                recipients = [to_emails]
            elif isinstance(to_emails[0], EmailRecipient):
                recipients = [r.email for r in to_emails]
            else:
                recipients = to_emails

            metadata = {
                "message_id": message_id,
                "recipients": recipients,
                "subject": subject,
                "type": email_type.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "provider": "sendgrid",
            }

            cache_key = CacheKey.generate("email", "sent", message_id)
            await cache.set(cache_key, metadata, ttl=CacheConfig.VERY_LONG_TTL)

        except Exception as e:
            logger.warning(f"Failed to cache email metadata: {e}")

    # Convenience methods for common email types

    async def send_welcome_email(
        self, user_email: str, user_name: str, verification_url: str | None = None
    ) -> dict[str, Any]:
        """Send welcome email to new user"""
        context = {
            "user_name": user_name,
            "verification_url": verification_url,
            "support_email": "support@toolboxai.com",
        }

        return await self.send_email(
            to_emails=EmailRecipient(email=user_email, name=user_name),
            subject=f"Welcome to {self.from_name}, {user_name}!",
            template_name="welcome",
            template_context=context,
            email_type=EmailType.WELCOME,
            priority=EmailPriority.HIGH,
        )

    async def send_password_reset_email(
        self, user_email: str, user_name: str, reset_token: str, reset_url: str
    ) -> dict[str, Any]:
        """Send password reset email"""
        context = {
            "user_name": user_name,
            "reset_token": reset_token,
            "reset_url": reset_url,
            "expiry_hours": 24,
        }

        return await self.send_email(
            to_emails=EmailRecipient(email=user_email, name=user_name),
            subject="Reset Your Password",
            template_name="password_reset",
            template_context=context,
            email_type=EmailType.PASSWORD_RESET,
            priority=EmailPriority.URGENT,
        )

    async def send_verification_email(
        self, user_email: str, user_name: str, verification_code: str, verification_url: str
    ) -> dict[str, Any]:
        """Send email verification"""
        context = {
            "user_name": user_name,
            "verification_code": verification_code,
            "verification_url": verification_url,
        }

        return await self.send_email(
            to_emails=EmailRecipient(email=user_email, name=user_name),
            subject="Verify Your Email Address",
            template_name="email_verification",
            template_context=context,
            email_type=EmailType.VERIFICATION,
            priority=EmailPriority.HIGH,
        )

    async def send_subscription_confirmation_email(
        self,
        user_email: str,
        user_name: str,
        plan_name: str,
        amount: float,
        next_billing_date: datetime,
        invoice_url: str | None = None,
    ) -> dict[str, Any]:
        """Send subscription confirmation email"""
        context = {
            "user_name": user_name,
            "plan_name": plan_name,
            "amount": amount,
            "next_billing_date": next_billing_date.strftime("%B %d, %Y"),
            "invoice_url": invoice_url,
        }

        return await self.send_email(
            to_emails=EmailRecipient(email=user_email, name=user_name),
            subject=f"Subscription Confirmed: {plan_name}",
            template_name="subscription_confirmation",
            template_context=context,
            email_type=EmailType.SUBSCRIPTION,
            priority=EmailPriority.HIGH,
        )

    # Webhook handling for SendGrid events

    async def handle_webhook(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Handle SendGrid webhook events

        Args:
            events: List of SendGrid event objects

        Returns:
            Processing result
        """
        try:
            processed = 0
            errors = 0

            for event in events:
                try:
                    await self._process_webhook_event(event)
                    processed += 1
                except Exception as e:
                    logger.error(f"Failed to process webhook event: {e}")
                    errors += 1

            return {"success": True, "processed": processed, "errors": errors}

        except Exception as e:
            logger.error(f"Webhook handling failed: {e}")
            return {"success": False, "error": str(e)}

    async def _process_webhook_event(self, event: dict[str, Any]):
        """Process individual webhook event"""
        event_type = event.get("event")
        email = event.get("email")
        message_id = event.get("sg_message_id")
        timestamp = event.get("timestamp")

        # Cache event
        cache_key = CacheKey.generate("email", "event", f"{message_id}:{event_type}")
        await cache.set(cache_key, event, ttl=CacheConfig.LONG_TTL)

        # Handle specific events
        if event_type == "bounce":
            await self._handle_bounce(email, event)
        elif event_type == "dropped":
            await self._handle_dropped(email, event)
        elif event_type == "spam_report":
            await self._handle_spam_report(email, event)
        elif event_type == "unsubscribe":
            await self._handle_unsubscribe(email, event)

        logger.info(f"Processed {event_type} event for {email}")

    async def _handle_bounce(self, email: str, event: dict[str, Any]):
        """Handle bounce event"""
        # Add to suppression list
        bounce_type = event.get("type", "hard")
        if bounce_type == "hard":
            # Permanently suppress
            await self.add_to_suppression_list(email, "bounce")

    async def _handle_dropped(self, email: str, event: dict[str, Any]):
        """Handle dropped email event"""
        reason = event.get("reason", "unknown")
        logger.warning(f"Email dropped for {email}: {reason}")

    async def _handle_spam_report(self, email: str, event: dict[str, Any]):
        """Handle spam report"""
        # Add to global suppression
        await self.add_to_suppression_list(email, "spam_report")

    async def _handle_unsubscribe(self, email: str, event: dict[str, Any]):
        """Handle unsubscribe event"""
        # Add to unsubscribe group
        await self.add_to_suppression_list(email, "unsubscribe")

    async def add_to_suppression_list(self, email: str, suppression_type: str) -> bool:
        """
        Add email to suppression list

        Args:
            email: Email address to suppress
            suppression_type: Type of suppression (bounce, spam_report, unsubscribe)

        Returns:
            Success status
        """
        try:
            if not self.client:
                return False

            # Use SendGrid suppression API
            if suppression_type == "bounce":
                response = self.client.client.suppression.bounces.post(
                    request_body=[{"email": email}]
                )
            elif suppression_type == "spam_report":
                response = self.client.client.suppression.spam_reports.post(
                    request_body=[{"email": email}]
                )
            elif suppression_type == "unsubscribe" and self.unsubscribe_group_id:
                response = self.client.client.asm.groups._(
                    self.unsubscribe_group_id
                ).suppressions.post(request_body={"recipient_emails": [email]})
            else:
                # Global unsubscribe - use getattr for 'global' keyword
                global_api = getattr(self.client.client.suppression, "global")
                response = global_api.post(request_body=[{"email": email}])

            logger.info(f"Added {email} to {suppression_type} suppression list")
            return response.status_code in [200, 201]

        except Exception as e:
            logger.error(f"Failed to add to suppression list: {e}")
            return False

    async def remove_from_suppression_list(self, email: str, suppression_type: str) -> bool:
        """
        Remove email from suppression list

        Args:
            email: Email address to unsuppress
            suppression_type: Type of suppression

        Returns:
            Success status
        """
        try:
            if not self.client:
                return False

            if suppression_type == "bounce":
                response = self.client.client.suppression.bounces._(email).delete()
            elif suppression_type == "spam_report":
                response = self.client.client.suppression.spam_reports._(email).delete()
            elif suppression_type == "unsubscribe" and self.unsubscribe_group_id:
                response = (
                    self.client.client.asm.groups._(self.unsubscribe_group_id)
                    .suppressions._(email)
                    .delete()
                )
            else:
                global_api = getattr(self.client.client.suppression, "global")
                response = global_api._(email).delete()

            logger.info(f"Removed {email} from {suppression_type} suppression list")
            return response.status_code == 204

        except Exception as e:
            logger.error(f"Failed to remove from suppression list: {e}")
            return False

    async def verify_email_address(self, email: str) -> bool:
        """
        Verify if email address is valid

        Args:
            email: Email address to verify

        Returns:
            True if valid
        """
        import re

        # Basic regex validation
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, email):
            return False

        # Check suppression lists
        try:
            if self.client:
                # Check various suppression lists
                for list_type in ["bounces", "spam_reports", "invalid_emails"]:
                    response = self.client.client.suppression._(list_type)._(email).get()
                    if response.status_code == 200:
                        logger.warning(f"Email {email} is on {list_type} list")
                        return False
        except Exception as e:
            logger.debug(f"Suppression check: {e}")

        return True

    async def get_email_status(self, message_id: str) -> dict[str, Any] | None:
        """
        Get email status from cache

        Args:
            message_id: SendGrid message ID

        Returns:
            Email status data
        """
        try:
            cache_key = CacheKey.generate("email", "sent", message_id)
            return await cache.get(cache_key)
        except Exception as e:
            logger.error(f"Failed to get email status: {e}")
            return None

    # ==========================================
    # LEGACY TRANSACTIONAL TEMPLATES API
    # ==========================================
    # Following SendGrid v3 API Documentation for 2025
    # Supports up to 300 templates with versioning

    async def create_template(self, name: str, generation: str = "legacy") -> str | None:
        """
        Create a new legacy transactional template

        Args:
            name: Template name (max 100 characters)
            generation: Template generation type (legacy or dynamic)

        Returns:
            Template ID if successful
        """
        try:
            if not self.client:
                logger.error("SendGrid client not initialized")
                return None

            # Validate name length
            if len(name) > 100:
                logger.error("Template name exceeds 100 character limit")
                return None

            data = {"name": name, "generation": generation}

            response = self.client.client.templates.post(request_body=data)

            if response.status_code == 201:
                template_data = json.loads(response.body)
                template_id = template_data.get("id")
                logger.info(f"Created template '{name}' with ID: {template_id}")
                return template_id
            else:
                logger.error(f"Failed to create template: {response.status_code}")
                return None

        except HTTPError as e:
            logger.error(f"SendGrid API error creating template: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating template: {e}")
            return None

    async def create_template_version(
        self,
        template_id: str,
        name: str,
        subject: str,
        html_content: str,
        plain_content: str | None = None,
        active: bool = True,
        test_data: dict[str, Any] | None = None,
    ) -> str | None:
        """
        Create a new version for an existing template

        Args:
            template_id: Parent template ID
            name: Version name
            subject: Email subject line (supports substitution tags)
            html_content: HTML content with table-based layout
            plain_content: Plain text content (auto-generated if not provided)
            active: Whether this version is active
            test_data: Test data for substitution tags

        Returns:
            Version ID if successful
        """
        try:
            if not self.client:
                logger.error("SendGrid client not initialized")
                return None

            # Auto-generate plain content from HTML if not provided
            if not plain_content and HTML_PROCESSING_AVAILABLE:
                soup = BeautifulSoup(html_content, "html.parser")
                plain_content = soup.get_text(separator="\n", strip=True)
            elif not plain_content:
                plain_content = "Please view this email in HTML format"

            # Ensure unsubscribe links are present
            if "<%asm_group_unsubscribe_raw_url%>" not in html_content:
                html_content += """
                <br><br>
                <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                        <td align="center" style="font-size: 12px; color: #666;">
                            <a href="<%asm_group_unsubscribe_raw_url%>" style="color: #666;">Unsubscribe</a> |
                            <a href="<%asm_preferences_raw_url%>" style="color: #666;">Manage Preferences</a>
                        </td>
                    </tr>
                </table>
                """

            if "<%asm_group_unsubscribe_raw_url%>" not in plain_content:
                plain_content += "\n\nUnsubscribe: <%asm_group_unsubscribe_raw_url%>\n"
                plain_content += "Manage Preferences: <%asm_preferences_raw_url%>"

            data = {
                "template_id": template_id,
                "name": name,
                "subject": subject,
                "html_content": html_content,
                "plain_content": plain_content,
                "active": 1 if active else 0,
            }

            # Add test data if provided
            if test_data:
                data["test_data"] = json.dumps(test_data)

            response = self.client.client.templates._(template_id).versions.post(request_body=data)

            if response.status_code == 201:
                version_data = json.loads(response.body)
                version_id = version_data.get("id")
                logger.info(f"Created template version '{name}' with ID: {version_id}")
                return version_id
            else:
                logger.error(f"Failed to create template version: {response.status_code}")
                return None

        except HTTPError as e:
            logger.error(f"SendGrid API error creating template version: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating template version: {e}")
            return None

    async def update_template(self, template_id: str, name: str) -> bool:
        """
        Update template name

        Args:
            template_id: Template ID to update
            name: New template name

        Returns:
            Success status
        """
        try:
            if not self.client:
                return False

            data = {"name": name}
            response = self.client.client.templates._(template_id).patch(request_body=data)

            if response.status_code == 200:
                logger.info(f"Updated template {template_id} name to '{name}'")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to update template: {e}")
            return False

    async def update_template_version(
        self,
        template_id: str,
        version_id: str,
        name: str | None = None,
        subject: str | None = None,
        html_content: str | None = None,
        plain_content: str | None = None,
        active: bool | None = None,
    ) -> bool:
        """
        Update an existing template version

        Args:
            template_id: Parent template ID
            version_id: Version ID to update
            name: New version name
            subject: New subject line
            html_content: New HTML content
            plain_content: New plain text content
            active: New active status

        Returns:
            Success status
        """
        try:
            if not self.client:
                return False

            data = {}
            if name is not None:
                data["name"] = name
            if subject is not None:
                data["subject"] = subject
            if html_content is not None:
                data["html_content"] = html_content
            if plain_content is not None:
                data["plain_content"] = plain_content
            if active is not None:
                data["active"] = 1 if active else 0

            response = (
                self.client.client.templates._(template_id)
                .versions._(version_id)
                .patch(request_body=data)
            )

            if response.status_code == 200:
                logger.info(f"Updated template version {version_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to update template version: {e}")
            return False

    async def get_template(self, template_id: str) -> dict[str, Any] | None:
        """
        Get template details

        Args:
            template_id: Template ID

        Returns:
            Template data including all versions
        """
        try:
            if not self.client:
                return None

            response = self.client.client.templates._(template_id).get()

            if response.status_code == 200:
                return json.loads(response.body)
            return None

        except Exception as e:
            logger.error(f"Failed to get template: {e}")
            return None

    async def get_template_version(
        self, template_id: str, version_id: str
    ) -> dict[str, Any] | None:
        """
        Get specific template version details

        Args:
            template_id: Parent template ID
            version_id: Version ID

        Returns:
            Template version data
        """
        try:
            if not self.client:
                return None

            response = self.client.client.templates._(template_id).versions._(version_id).get()

            if response.status_code == 200:
                return json.loads(response.body)
            return None

        except Exception as e:
            logger.error(f"Failed to get template version: {e}")
            return None

    async def list_templates(
        self,
        generations: str = "legacy,dynamic",
        page_size: int = 20,
        page_token: str | None = None,
    ) -> dict[str, Any] | None:
        """
        List all templates

        Args:
            generations: Comma-separated generation types
            page_size: Results per page
            page_token: Pagination token

        Returns:
            Templates list with metadata
        """
        try:
            if not self.client:
                return None

            params = {"generations": generations, "page_size": page_size}

            if page_token:
                params["page_token"] = page_token

            response = self.client.client.templates.get(query_params=params)

            if response.status_code == 200:
                data = json.loads(response.body)
                logger.info(f"Retrieved {len(data.get('result', []))} templates")
                return data
            return None

        except Exception as e:
            logger.error(f"Failed to list templates: {e}")
            return None

    async def activate_template_version(self, template_id: str, version_id: str) -> bool:
        """
        Activate a specific template version

        Args:
            template_id: Parent template ID
            version_id: Version ID to activate

        Returns:
            Success status
        """
        try:
            if not self.client:
                return False

            response = (
                self.client.client.templates._(template_id).versions._(version_id).activate.post()
            )

            if response.status_code == 200:
                logger.info(f"Activated template version {version_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to activate template version: {e}")
            return False

    async def delete_template(self, template_id: str) -> bool:
        """
        Delete a template and all its versions

        Args:
            template_id: Template ID to delete

        Returns:
            Success status
        """
        try:
            if not self.client:
                return False

            response = self.client.client.templates._(template_id).delete()

            if response.status_code == 204:
                logger.info(f"Deleted template {template_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to delete template: {e}")
            return False

    async def delete_template_version(self, template_id: str, version_id: str) -> bool:
        """
        Delete a specific template version

        Args:
            template_id: Parent template ID
            version_id: Version ID to delete

        Returns:
            Success status
        """
        try:
            if not self.client:
                return False

            response = self.client.client.templates._(template_id).versions._(version_id).delete()

            if response.status_code == 204:
                logger.info(f"Deleted template version {version_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to delete template version: {e}")
            return False

    async def duplicate_template(self, template_id: str, new_name: str) -> str | None:
        """
        Duplicate an existing template with all versions

        Args:
            template_id: Template ID to duplicate
            new_name: Name for the duplicate

        Returns:
            New template ID if successful
        """
        try:
            # Get original template
            original = await self.get_template(template_id)
            if not original:
                return None

            # Create new template
            new_template_id = await self.create_template(
                name=new_name, generation=original.get("generation", "legacy")
            )

            if not new_template_id:
                return None

            # Copy all versions
            for version in original.get("versions", []):
                await self.create_template_version(
                    template_id=new_template_id,
                    name=version.get("name", "Copy"),
                    subject=version.get("subject", ""),
                    html_content=version.get("html_content", ""),
                    plain_content=version.get("plain_content", ""),
                    active=version.get("active", 0) == 1,
                )

            logger.info(f"Duplicated template {template_id} as {new_template_id}")
            return new_template_id

        except Exception as e:
            logger.error(f"Failed to duplicate template: {e}")
            return None

    async def send_with_template(
        self,
        template_id: str,
        to_emails: str | list[str],
        substitutions: dict[str, str] | None = None,
        from_email: str | None = None,
        from_name: str | None = None,
        reply_to: str | None = None,
        categories: list[str] | None = None,
        send_at: int | None = None,
    ) -> str | None:
        """
        Send email using a template

        Args:
            template_id: Template ID to use
            to_emails: Recipient email(s)
            substitutions: Dynamic data for template tags
            from_email: Sender email
            from_name: Sender name
            reply_to: Reply-to email
            categories: Email categories for analytics
            send_at: Unix timestamp for scheduled send

        Returns:
            Message ID if successful
        """
        try:
            if not self.client:
                logger.error("SendGrid client not initialized")
                return None

            # Prepare recipients
            if isinstance(to_emails, str):
                to_emails = [to_emails]

            # Build message
            message = Mail()

            # Set from
            message.from_email = Email(
                email=from_email or self.from_email, name=from_name or self.from_name
            )

            # Set template
            message.template_id = template_id

            # Add personalizations for each recipient
            for to_email in to_emails:
                personalization = Personalization()
                personalization.add_to(Email(to_email))

                # Add substitutions
                if substitutions:
                    for key, value in substitutions.items():
                        personalization.add_substitution(Substitution(key, value))

                message.add_personalization(personalization)

            # Set reply-to
            if reply_to:
                message.reply_to = ReplyTo(reply_to)

            # Add categories
            if categories:
                for category in categories[:10]:  # Max 10 categories
                    message.add_category(Category(category))

            # Schedule send
            if send_at:
                message.send_at = send_at

            # Add tracking
            if self.enable_tracking:
                tracking = TrackingSettings()
                tracking.click_tracking = ClickTracking(True, True)
                tracking.open_tracking = OpenTracking(True)
                message.tracking_settings = tracking

            # Send email
            response = self.client.send(message)

            if response.status_code in [200, 202]:
                # Extract message ID
                message_id = response.headers.get("X-Message-Id")
                logger.info(f"Sent template email {template_id} to {len(to_emails)} recipients")
                return message_id
            else:
                logger.error(f"Failed to send template email: {response.status_code}")
                return None

        except HTTPError as e:
            logger.error(f"SendGrid API error sending template: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error sending template: {e}")
            return None

    async def preview_template(
        self,
        template_id: str,
        version_id: str | None = None,
        substitutions: dict[str, str] | None = None,
    ) -> dict[str, str] | None:
        """
        Preview template with substitutions applied

        Args:
            template_id: Template ID
            version_id: Specific version ID (uses active if not specified)
            substitutions: Test data for substitution tags

        Returns:
            Dict with rendered subject, html, and plain content
        """
        try:
            # Get template version
            if version_id:
                version = await self.get_template_version(template_id, version_id)
            else:
                template = await self.get_template(template_id)
                if not template:
                    return None
                # Find active version
                version = None
                for v in template.get("versions", []):
                    if v.get("active") == 1:
                        version = v
                        break

            if not version:
                logger.error("No active template version found")
                return None

            # Apply substitutions
            subject = version.get("subject", "")
            html_content = version.get("html_content", "")
            plain_content = version.get("plain_content", "")

            if substitutions:
                for key, value in substitutions.items():
                    tag = f"<%{key}%>"  # Legacy template syntax
                    subject = subject.replace(tag, str(value))
                    html_content = html_content.replace(tag, str(value))
                    plain_content = plain_content.replace(tag, str(value))

            return {
                "subject": subject,
                "html_content": html_content,
                "plain_content": plain_content,
            }

        except Exception as e:
            logger.error(f"Failed to preview template: {e}")
            return None

    async def export_template(self, template_id: str, file_path: str) -> bool:
        """
        Export template to JSON file

        Args:
            template_id: Template ID to export
            file_path: Path to save JSON file

        Returns:
            Success status
        """
        try:
            template = await self.get_template(template_id)
            if not template:
                return False

            # Write to file
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding="utf-8") as f:
                json.dump(template, f, indent=2)

            logger.info(f"Exported template {template_id} to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export template: {e}")
            return False

    async def import_template(self, file_path: str, new_name: str | None = None) -> str | None:
        """
        Import template from JSON file

        Args:
            file_path: Path to JSON file
            new_name: Override template name

        Returns:
            New template ID if successful
        """
        try:
            # Read template data
            with open(file_path, encoding="utf-8") as f:
                template_data = json.load(f)

            # Create template
            template_name = new_name or template_data.get("name", "Imported Template")
            new_template_id = await self.create_template(
                name=template_name, generation=template_data.get("generation", "legacy")
            )

            if not new_template_id:
                return None

            # Import versions
            for version in template_data.get("versions", []):
                await self.create_template_version(
                    template_id=new_template_id,
                    name=version.get("name", "Imported Version"),
                    subject=version.get("subject", ""),
                    html_content=version.get("html_content", ""),
                    plain_content=version.get("plain_content", ""),
                    active=version.get("active", 0) == 1,
                )

            logger.info(f"Imported template from {file_path} as {new_template_id}")
            return new_template_id

        except Exception as e:
            logger.error(f"Failed to import template: {e}")
            return None


# Create singleton instance
email_service = SendGridEmailService()

# Export for backward compatibility
EmailService = SendGridEmailService

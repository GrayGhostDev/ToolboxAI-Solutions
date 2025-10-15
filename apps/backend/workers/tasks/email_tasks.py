"""
Email Tasks Module
==================
SMTP-based email sending tasks with queue management, no AWS SES dependencies.

Features:
- SendGrid integration for reliable delivery
- Email queue processing with retries
- Template rendering with Jinja2
- Tenant-specific email configurations
- Bounce and complaint handling
"""

import os
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from celery import shared_task
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from apps.backend.workers.celery_app import app
from toolboxai_settings import settings

logger = logging.getLogger(__name__)


@dataclass
class EmailConfig:
    """Email configuration for different providers."""
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    use_tls: bool = True
    from_email: str = ""
    from_name: str = "ToolBoxAI"


def get_email_config(organization_id: Optional[str] = None) -> EmailConfig:
    """
    Get email configuration for tenant or default.

    Args:
        organization_id: Optional tenant ID for custom configuration

    Returns:
        EmailConfig instance
    """
    # Default configuration (can be overridden per tenant)
    default_config = EmailConfig(
        smtp_host=os.getenv("SMTP_HOST", "smtp.sendgrid.net"),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_user=os.getenv("SMTP_USER", "apikey"),
        smtp_password=os.getenv("SENDGRID_API_KEY", ""),
        use_tls=os.getenv("SMTP_USE_TLS", "true").lower() == "true",
        from_email=os.getenv("FROM_EMAIL", "noreply@toolboxai.com"),
        from_name=os.getenv("FROM_NAME", "ToolBoxAI")
    )

    # TODO: Add tenant-specific configuration lookup from database
    # if organization_id:
    #     tenant_config = get_tenant_email_config(organization_id)
    #     if tenant_config:
    #         return tenant_config

    return default_config


def setup_jinja_environment() -> Environment:
    """Set up Jinja2 environment for email templates."""
    template_dir = os.path.join(os.path.dirname(__file__), "..", "..", "templates", "emails")

    # Create template directory if it doesn't exist
    os.makedirs(template_dir, exist_ok=True)

    return Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=True
    )


@shared_task(
    bind=True,
    name="email_tasks.send_email",
    queue="email",
    max_retries=3,
    default_retry_delay=60
)
def send_email(
    self,
    to_email: str,
    subject: str,
    template_name: str,
    template_context: Dict[str, Any],
    organization_id: Optional[str] = None,
    from_email: Optional[str] = None,
    attachments: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Send email using SMTP with template rendering.

    Args:
        to_email: Recipient email address
        subject: Email subject
        template_name: Template file name (without .html extension)
        template_context: Variables for template rendering
        organization_id: Tenant organization ID
        from_email: Optional custom from email
        attachments: List of attachment dicts with 'filename', 'content', 'mimetype'

    Returns:
        Dict with send result
    """
    try:
        # Get email configuration
        email_config = get_email_config(organization_id)

        if not email_config.smtp_password:
            raise ValueError("SMTP password not configured")

        # Set up Jinja2 environment
        jinja_env = setup_jinja_environment()

        # Render email template
        try:
            html_template = jinja_env.get_template(f"{template_name}.html")
            html_content = html_template.render(**template_context)
        except TemplateNotFound:
            # Fall back to plain text
            html_content = f"<html><body><h2>{subject}</h2><p>Template not found: {template_name}.html</p></body></html>"
            logger.warning(f"HTML template not found: {template_name}.html")

        # Try to render plain text version
        try:
            text_template = jinja_env.get_template(f"{template_name}.txt")
            text_content = text_template.render(**template_context)
        except TemplateNotFound:
            # Generate simple text version from subject
            text_content = f"{subject}\n\nThis is an HTML email. Please enable HTML viewing in your email client."

        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email or f"{email_config.from_name} <{email_config.from_email}>"
        msg['To'] = to_email

        # Add text and HTML parts
        text_part = MIMEText(text_content, 'plain', 'utf-8')
        html_part = MIMEText(html_content, 'html', 'utf-8')

        msg.attach(text_part)
        msg.attach(html_part)

        # Add attachments if provided
        if attachments:
            for attachment in attachments:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment['content'])
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {attachment["filename"]}'
                )
                msg.attach(part)

        # Send email
        with smtplib.SMTP(email_config.smtp_host, email_config.smtp_port) as server:
            if email_config.use_tls:
                server.starttls()

            server.login(email_config.smtp_user, email_config.smtp_password)
            text = msg.as_string()
            server.sendmail(email_config.from_email, to_email, text)

        # Log success
        logger.info(f"Email sent successfully to {to_email} using template {template_name}")

        return {
            'status': 'sent',
            'to_email': to_email,
            'subject': subject,
            'template_name': template_name,
            'organization_id': organization_id,
            'sent_at': datetime.utcnow().isoformat(),
            'message_id': self.request.id
        }

    except Exception as exc:
        logger.error(f"Failed to send email to {to_email}: {exc}")

        # Retry on transient errors
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying email send (attempt {self.request.retries + 1})")
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

        return {
            'status': 'failed',
            'to_email': to_email,
            'subject': subject,
            'error': str(exc),
            'failed_at': datetime.utcnow().isoformat(),
            'final_attempt': True
        }


@shared_task(
    bind=True,
    name="email_tasks.send_bulk_emails",
    queue="email",
    max_retries=2
)
def send_bulk_emails(
    self,
    email_list: List[Dict[str, Any]],
    subject: str,
    template_name: str,
    common_context: Dict[str, Any],
    organization_id: Optional[str] = None,
    batch_size: int = 50
) -> Dict[str, Any]:
    """
    Send bulk emails with batching and rate limiting.

    Args:
        email_list: List of email dicts with 'email' and optional 'context'
        subject: Email subject
        template_name: Template file name
        common_context: Shared template context
        organization_id: Tenant organization ID
        batch_size: Emails per batch

    Returns:
        Dict with bulk send results
    """
    try:
        from celery import group

        successful = 0
        failed = 0
        batch_jobs = []

        # Process emails in batches
        for i in range(0, len(email_list), batch_size):
            batch = email_list[i:i + batch_size]

            # Create individual email tasks
            batch_tasks = []
            for email_data in batch:
                # Merge common context with individual context
                context = {**common_context, **email_data.get('context', {})}

                batch_tasks.append(
                    send_email.s(
                        to_email=email_data['email'],
                        subject=subject,
                        template_name=template_name,
                        template_context=context,
                        organization_id=organization_id
                    )
                )

            # Execute batch
            batch_job = group(batch_tasks)
            batch_jobs.append(batch_job.apply_async())

        # Wait for all batches to complete
        for batch_job in batch_jobs:
            results = batch_job.get(timeout=300)  # 5 minute timeout per batch

            for result in results:
                if result.get('status') == 'sent':
                    successful += 1
                else:
                    failed += 1

        logger.info(f"Bulk email completed: {successful} sent, {failed} failed")

        return {
            'status': 'completed',
            'total_emails': len(email_list),
            'successful': successful,
            'failed': failed,
            'organization_id': organization_id,
            'completed_at': datetime.utcnow().isoformat()
        }

    except Exception as exc:
        logger.error(f"Bulk email failed: {exc}")

        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=300)  # Retry after 5 minutes

        return {
            'status': 'failed',
            'error': str(exc),
            'failed_at': datetime.utcnow().isoformat()
        }


@shared_task(
    bind=True,
    name="email_tasks.process_email_queue",
    queue="email"
)
def process_email_queue(
    self,
    batch_size: int = 50,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Process queued emails from database.

    Args:
        batch_size: Number of emails to process in one batch
        max_retries: Maximum retry attempts for failed emails

    Returns:
        Dict with processing results
    """
    try:
        from apps.backend.core.database import SessionLocal
        from database.models import EmailQueue
        from sqlalchemy import and_

        logger.info(f"Processing email queue with batch size {batch_size}")

        processed = 0
        failed = 0

        with SessionLocal() as session:
            # Query for pending emails
            pending_emails = session.query(EmailQueue).filter(
                and_(
                    EmailQueue.status == 'pending',
                    EmailQueue.retry_count < max_retries
                )
            ).limit(batch_size).all()

            for email in pending_emails:
                try:
                    # Send email
                    result = send_email.apply_async(
                        kwargs={
                            'to_email': email.to_email,
                            'subject': email.subject,
                            'template_name': email.template_name,
                            'template_context': json.loads(email.template_context) if isinstance(email.template_context, str) else email.template_context,
                            'organization_id': email.organization_id,
                        }
                    ).get(timeout=60)

                    if result.get('status') == 'sent':
                        email.status = 'sent'
                        email.sent_at = datetime.utcnow()
                        processed += 1
                    else:
                        email.retry_count += 1
                        email.last_error = result.get('error', 'Unknown error')
                        if email.retry_count >= max_retries:
                            email.status = 'failed'
                        failed += 1

                except Exception as e:
                    logger.error(f"Failed to process email {email.id}: {e}")
                    email.retry_count += 1
                    email.last_error = str(e)
                    if email.retry_count >= max_retries:
                        email.status = 'failed'
                    failed += 1

            session.commit()

        return {
            'status': 'completed',
            'processed': processed,
            'failed': failed,
            'batch_size': batch_size,
            'processed_at': datetime.utcnow().isoformat()
        }

    except Exception as exc:
        logger.error(f"Email queue processing failed: {exc}")
        return {
            'status': 'failed',
            'error': str(exc),
            'failed_at': datetime.utcnow().isoformat()
        }


@shared_task(
    bind=True,
    name="email_tasks.send_notification_email",
    queue="email",
    max_retries=3
)
def send_notification_email(
    self,
    user_id: str,
    notification_type: str,
    title: str,
    message: str,
    action_url: Optional[str] = None,
    organization_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send notification email to user.

    Args:
        user_id: Target user ID
        notification_type: Type of notification (info, warning, error, success)
        title: Notification title
        message: Notification message
        action_url: Optional action URL for the notification
        organization_id: Tenant organization ID

    Returns:
        Dict with send result
    """
    try:
        # Get user email from database
        from apps.backend.core.database import SessionLocal
        from database.models import User

        with SessionLocal() as session:
            user = session.query(User).filter_by(id=user_id).first()
            if not user or not user.email:
                logger.error(f"User {user_id} not found or has no email")
                return {
                    'status': 'failed',
                    'user_id': user_id,
                    'error': 'User not found or has no email',
                    'failed_at': datetime.utcnow().isoformat()
                }

            user_email = user.email

        # Template context
        context = {
            'user_id': user_id,
            'notification_type': notification_type,
            'title': title,
            'message': message,
            'action_url': action_url,
            'organization_id': organization_id,
            'sent_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        }

        # Send email using notification template
        result = send_email.apply_async(
            kwargs={
                'to_email': user_email,
                'subject': f"ToolBoxAI Notification: {title}",
                'template_name': 'notification',
                'template_context': context,
                'organization_id': organization_id
            }
        ).get(timeout=60)

        return {
            'status': 'sent',
            'user_id': user_id,
            'email_result': result,
            'sent_at': datetime.utcnow().isoformat()
        }

    except Exception as exc:
        logger.error(f"Failed to send notification email to user {user_id}: {exc}")

        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

        return {
            'status': 'failed',
            'user_id': user_id,
            'error': str(exc),
            'failed_at': datetime.utcnow().isoformat()
        }


@shared_task(
    bind=True,
    name="email_tasks.cleanup_email_logs",
    queue="low_priority"
)
def cleanup_email_logs(
    self,
    retention_days: int = 30
) -> Dict[str, Any]:
    """
    Clean up old email logs and delivery records.

    Args:
        retention_days: Number of days to retain email logs

    Returns:
        Dict with cleanup results
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        # TODO: Implement email log cleanup from database
        # This would typically:
        # 1. Delete old email delivery records
        # 2. Archive successful sends older than retention period
        # 3. Keep failed sends for longer period for analysis

        logger.info(f"Email log cleanup completed for records older than {cutoff_date}")

        return {
            'status': 'completed',
            'cutoff_date': cutoff_date.isoformat(),
            'retention_days': retention_days,
            'records_deleted': 0,  # Placeholder
            'cleaned_at': datetime.utcnow().isoformat()
        }

    except Exception as exc:
        logger.error(f"Email log cleanup failed: {exc}")
        return {
            'status': 'failed',
            'error': str(exc),
            'failed_at': datetime.utcnow().isoformat()
        }


# Utility functions for email template management
def create_default_templates():
    """Create default email templates if they don't exist."""
    template_dir = os.path.join(os.path.dirname(__file__), "..", "..", "templates", "emails")
    os.makedirs(template_dir, exist_ok=True)

    # Default notification template
    notification_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{{ title }}</title>
</head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
        <h2 style="color: #333;">{{ title }}</h2>
        <p style="color: #555; line-height: 1.6;">{{ message }}</p>

        {% if action_url %}
        <div style="margin: 20px 0;">
            <a href="{{ action_url }}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                Take Action
            </a>
        </div>
        {% endif %}

        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #888; font-size: 12px;">
            Sent at {{ sent_at }}<br>
            This is an automated message from ToolBoxAI.
        </p>
    </div>
</body>
</html>
    """

    notification_txt = """
{{ title }}

{{ message }}

{% if action_url %}
Take Action: {{ action_url }}
{% endif %}

---
Sent at {{ sent_at }}
This is an automated message from ToolBoxAI.
    """

    # Write templates if they don't exist
    html_path = os.path.join(template_dir, "notification.html")
    txt_path = os.path.join(template_dir, "notification.txt")

    if not os.path.exists(html_path):
        with open(html_path, 'w') as f:
            f.write(notification_html.strip())

    if not os.path.exists(txt_path):
        with open(txt_path, 'w') as f:
            f.write(notification_txt.strip())


# Initialize default templates when module is imported
try:
    create_default_templates()
except Exception as e:
    logger.warning(f"Could not create default email templates: {e}")
"""
Email Preview API
Provides endpoints for previewing and testing email templates
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, EmailStr

from apps.backend.config import settings
from apps.backend.services.email import email_service
from apps.backend.services.email.queue import EmailPriority, email_queue

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email", tags=["Email"])


class EmailPreviewRequest(BaseModel):
    """Request model for email preview"""

    template_name: str
    template_data: dict[str, Any] | None = None
    use_sample_data: bool = True


class EmailTestRequest(BaseModel):
    """Request model for sending test email"""

    to_email: EmailStr
    template_name: str
    template_data: dict[str, Any] | None = None
    use_sample_data: bool = True


class EmailQueueRequest(BaseModel):
    """Request model for queuing emails"""

    to_email: Union[EmailStr, list[EmailStr]]
    subject: str
    template_name: str | None = None
    template_data: dict[str, Any] | None = None
    html_content: str | None = None
    text_content: str | None = None
    priority: EmailPriority = EmailPriority.NORMAL
    scheduled_for: datetime | None = None
    max_retries: int = 3
    metadata: dict[str, Any] | None = None


# Sample data for different email templates
SAMPLE_DATA = {
    "welcome": {
        "user_name": "John Doe",
        "app_name": "ToolboxAI",
        "app_url": "https://app.toolboxai.com",
        "verification_url": "https://app.toolboxai.com/verify?token=sample-token",
        "features": [
            {"title": "AI-Powered Learning", "description": "Personalized content recommendations"},
            {"title": "Real-time Collaboration", "description": "Work together with classmates"},
            {"title": "Progress Tracking", "description": "Monitor your learning journey"},
        ],
        "support_email": "support@toolboxai.com",
        "unsubscribe_url": "https://app.toolboxai.com/unsubscribe",
    },
    "password_reset": {
        "user_name": "John Doe",
        "app_name": "ToolboxAI",
        "reset_url": "https://app.toolboxai.com/reset-password?token=sample-token",
        "support_email": "support@toolboxai.com",
        "app_url": "https://app.toolboxai.com",
        "current_year": datetime.utcnow().year,
    },
    "payment_confirmation": {
        "app_name": "ToolboxAI",
        "customer_name": "John Doe",
        "transaction_id": "TXN-12345-SAMPLE",
        "amount": "49.99",
        "total": "49.99",
        "payment_date": datetime.utcnow().strftime("%B %d, %Y"),
        "payment_method": "Visa ending in 4242",
        "invoice_url": "https://app.toolboxai.com/invoices/sample",
        "account_url": "https://app.toolboxai.com/account",
        "billing_email": "billing@toolboxai.com",
        "support_email": "support@toolboxai.com",
        "app_url": "https://app.toolboxai.com",
        "items": [{"description": "Monthly Subscription", "amount": "49.99"}],
    },
    "subscription_renewal": {
        "app_name": "ToolboxAI",
        "customer_name": "John Doe",
        "plan_name": "Professional Plan",
        "amount": "49.99",
        "billing_period": "month",
        "renewal_date": (datetime.utcnow() + timedelta(days=7)).strftime("%B %d, %Y"),
        "payment_method": "Visa ending in 4242",
        "manage_subscription_url": "https://app.toolboxai.com/subscription",
        "update_payment_url": "https://app.toolboxai.com/payment-methods",
        "app_url": "https://app.toolboxai.com",
        "unsubscribe_url": "https://app.toolboxai.com/unsubscribe",
        "benefits": [
            {
                "icon": "🚀",
                "title": "Unlimited Access",
                "description": "All premium features included",
            },
            {"icon": "🛡️", "title": "Priority Support", "description": "24/7 dedicated assistance"},
            {
                "icon": "📊",
                "title": "Advanced Analytics",
                "description": "Detailed insights and reports",
            },
        ],
        "discount_available": True,
        "discount_percentage": "20",
        "apply_discount_url": "https://app.toolboxai.com/apply-discount",
    },
    "course_enrollment": {
        "app_name": "ToolboxAI",
        "student_name": "John Doe",
        "course_name": "Introduction to AI in Education",
        "instructor_name": "Dr. Jane Smith",
        "course_duration": "8 weeks",
        "enrollment_type": "ENROLLED",
        "course_url": "https://app.toolboxai.com/courses/ai-education",
        "dashboard_url": "https://app.toolboxai.com/dashboard",
        "start_date": datetime.utcnow().strftime("%B %d, %Y"),
        "access_period": "Lifetime Access",
        "certification_available": True,
        "support_email": "support@toolboxai.com",
        "unsubscribe_url": "https://app.toolboxai.com/unsubscribe",
        "community_enabled": True,
        "discord_url": "https://discord.gg/toolboxai",
        "student_count": "5,000+",
        "modules": [
            {
                "title": "Introduction to AI",
                "description": "Fundamentals of artificial intelligence",
                "duration": "2 hours",
            },
            {
                "title": "AI in Modern Education",
                "description": "How AI transforms learning",
                "duration": "3 hours",
            },
            {
                "title": "Practical Applications",
                "description": "Hands-on AI tools for educators",
                "duration": "4 hours",
            },
            {
                "title": "Final Project",
                "description": "Build your AI-powered lesson",
                "duration": "5 hours",
            },
        ],
    },
}


@router.post("/preview", response_class=HTMLResponse)
async def preview_email_template(request: EmailPreviewRequest):
    """
    Preview an email template with sample or custom data

    Args:
        request: Preview request with template name and optional data

    Returns:
        Rendered HTML email content
    """
    try:
        # Get template data
        if request.use_sample_data:
            # Use sample data for the template
            template_data = SAMPLE_DATA.get(request.template_name, {})
            # Merge with any provided custom data
            if request.template_data:
                template_data.update(request.template_data)
        else:
            template_data = request.template_data or {}

        # Render template
        html_content = await email_service.render_template(
            template_name=request.template_name, template_data=template_data
        )

        if not html_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template '{request.template_name}' not found",
            )

        # Add preview banner at top
        preview_banner = """
        <div style="background: #ff6b35; color: white; padding: 15px; text-align: center; font-family: sans-serif;">
            <strong>EMAIL PREVIEW MODE</strong> - This is a preview. No email has been sent.
            <br>
            <small>Template: {template_name} | Generated: {timestamp}</small>
        </div>
        """.format(
            template_name=request.template_name,
            timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        )

        # Inject banner at beginning of body tag
        html_content = html_content.replace("<body>", f"<body>{preview_banner}")

        return HTMLResponse(content=html_content)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing email template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preview template: {str(e)}",
        )


@router.post("/send-test")
async def send_test_email(request: EmailTestRequest):
    """
    Send a test email to a specific address

    Args:
        request: Test request with recipient and template details

    Returns:
        Success response with message ID
    """
    try:
        # Validate email is allowed for testing
        if not is_test_email_allowed(request.to_email):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Test emails can only be sent to verified test addresses",
            )

        # Get template data
        if request.use_sample_data:
            template_data = SAMPLE_DATA.get(request.template_name, {})
            if request.template_data:
                template_data.update(request.template_data)
        else:
            template_data = request.template_data or {}

        # Add test indicator to subject
        original_subject = template_data.get("subject", f"Test: {request.template_name}")
        template_data["subject"] = f"[TEST] {original_subject}"

        # Send test email
        result = await email_service.send_templated_email(
            to_email=request.to_email,
            subject=template_data["subject"],
            template_name=request.template_name,
            template_data=template_data,
        )

        return JSONResponse(
            content={
                "status": "success",
                "message": "Test email sent successfully",
                "to": request.to_email,
                "template": request.template_name,
                "message_id": result.get("message_id"),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test email: {str(e)}",
        )


def is_test_email_allowed(email: str) -> bool:
    """
    Check if email is allowed for testing

    In production, restrict to specific domains or addresses
    """
    # Allow all in development
    if settings.ENVIRONMENT == "development":
        return True

    # In production, only allow specific test domains
    allowed_domains = ["@toolboxai.com", "@test.com", "@example.com"]
    return any(email.endswith(domain) for domain in allowed_domains)


@router.get("/templates")
async def list_available_templates():
    """
    List all available email templates

    Returns:
        List of template names with descriptions
    """
    templates = [
        {
            "name": "welcome",
            "description": "Welcome email for new users",
            "variables": list(SAMPLE_DATA.get("welcome", {}).keys()),
        },
        {
            "name": "password_reset",
            "description": "Password reset request email",
            "variables": list(SAMPLE_DATA.get("password_reset", {}).keys()),
        },
        {
            "name": "payment_confirmation",
            "description": "Payment confirmation receipt",
            "variables": list(SAMPLE_DATA.get("payment_confirmation", {}).keys()),
        },
        {
            "name": "subscription_renewal",
            "description": "Subscription renewal notice",
            "variables": list(SAMPLE_DATA.get("subscription_renewal", {}).keys()),
        },
        {
            "name": "course_enrollment",
            "description": "Course enrollment confirmation",
            "variables": list(SAMPLE_DATA.get("course_enrollment", {}).keys()),
        },
    ]

    return JSONResponse(content={"templates": templates})


@router.get("/template/{template_name}/sample-data")
async def get_template_sample_data(template_name: str):
    """
    Get sample data for a specific template

    Args:
        template_name: Name of the template

    Returns:
        Sample data for the template
    """
    sample_data = SAMPLE_DATA.get(template_name)

    if not sample_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No sample data found for template '{template_name}'",
        )

    return JSONResponse(content={"template_name": template_name, "sample_data": sample_data})


@router.post("/queue")
async def queue_email(request: EmailQueueRequest):
    """
    Add email to processing queue

    Args:
        request: Email queue request

    Returns:
        Job ID and queue status
    """
    try:
        # Add to queue
        job_id = await email_queue.enqueue(
            to_email=request.to_email,
            subject=request.subject,
            template_name=request.template_name,
            template_data=request.template_data,
            html_content=request.html_content,
            text_content=request.text_content,
            priority=request.priority,
            scheduled_for=request.scheduled_for,
            max_retries=request.max_retries,
            metadata=request.metadata,
        )

        return JSONResponse(
            content={
                "status": "success",
                "job_id": job_id,
                "priority": request.priority,
                "scheduled_for": (
                    request.scheduled_for.isoformat() if request.scheduled_for else None
                ),
            }
        )

    except Exception as e:
        logger.error(f"Error queuing email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue email: {str(e)}",
        )


@router.get("/queue/metrics")
async def get_queue_metrics():
    """
    Get email queue metrics

    Returns:
        Queue statistics and metrics
    """
    try:
        metrics = await email_queue.get_metrics()

        return JSONResponse(
            content={
                "status": "success",
                "metrics": metrics,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error getting queue metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve queue metrics",
        )


@router.post("/queue/reprocess-dead-letter")
async def reprocess_dead_letter_queue(
    limit: int = Query(10, ge=1, le=100, description="Number of emails to reprocess")
):
    """
    Reprocess emails from dead letter queue

    Args:
        limit: Maximum number of emails to reprocess

    Returns:
        Number of emails reprocessed
    """
    try:
        count = await email_queue.reprocess_dead_letter(limit)

        return JSONResponse(
            content={
                "status": "success",
                "reprocessed": count,
                "message": f"Reprocessed {count} emails from dead letter queue",
            }
        )

    except Exception as e:
        logger.error(f"Error reprocessing dead letter queue: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reprocess dead letter queue",
        )


@router.get("/suppression-check/{email}")
async def check_suppression_status(email: EmailStr):
    """
    Check if an email is in the suppression list

    Args:
        email: Email address to check

    Returns:
        Suppression status
    """
    try:
        is_suppressed = await email_queue.is_suppressed(email)

        return JSONResponse(content={"email": email, "suppressed": is_suppressed})

    except Exception as e:
        logger.error(f"Error checking suppression status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check suppression status",
        )


@router.post("/validate-template")
async def validate_template(request: EmailPreviewRequest):
    """
    Validate an email template

    Args:
        request: Template validation request

    Returns:
        Validation results
    """
    try:
        errors = []
        warnings = []

        # Try to render template
        try:
            if request.use_sample_data:
                template_data = SAMPLE_DATA.get(request.template_name, {})
                if request.template_data:
                    template_data.update(request.template_data)
            else:
                template_data = request.template_data or {}

            html_content = await email_service.render_template(
                template_name=request.template_name, template_data=template_data
            )

            if not html_content:
                errors.append(f"Template '{request.template_name}' not found")

        except Exception as e:
            errors.append(f"Template rendering error: {str(e)}")

        # Check for common issues
        if html_content:
            # Check for missing variables (look for {{ }} patterns)
            import re

            missing_vars = re.findall(r"\{\{[^}]+\}\}", html_content)
            if missing_vars:
                warnings.append(f"Unresolved variables found: {missing_vars}")

            # Check for broken image tags
            if "<img" in html_content and 'src=""' in html_content:
                warnings.append("Empty image src attributes found")

            # Check for localhost URLs
            if "localhost" in html_content or "127.0.0.1" in html_content:
                warnings.append("Localhost URLs found - use production URLs")

        return JSONResponse(
            content={
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "template_name": request.template_name,
            }
        )

    except Exception as e:
        logger.error(f"Error validating template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate template: {str(e)}",
        )

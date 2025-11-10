"""
Email Service Router

Handles email sending, templates, and SendGrid webhook events.
"""

import logging
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, HTTPException, Request, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, EmailStr

from apps.backend.core.logging import logging_manager, log_audit
from apps.backend.core.config import settings
from apps.backend.models.schemas import User
from apps.backend.api.auth.auth import get_current_user
from apps.backend.services.email import (
    email_service,
    EmailType,
    EmailPriority,
    EmailRecipient,
    EmailAttachment,
)

logger = logging_manager.get_logger(__name__)
router = APIRouter(tags=["Email"])


# Request/Response Models
class SendEmailRequest(BaseModel):
    """Request model for sending an email"""

    to_email: EmailStr = Field(..., description="Recipient email address")
    to_name: Optional[str] = Field(None, description="Recipient name")
    subject: str = Field(..., description="Email subject")
    html_content: Optional[str] = Field(None, description="HTML email content")
    text_content: Optional[str] = Field(None, description="Plain text email content")
    template_id: Optional[str] = Field(None, description="SendGrid template ID")
    template_data: Optional[Dict[str, Any]] = Field(None, description="Template variables")
    email_type: str = Field(EmailType.TRANSACTIONAL, description="Email type")
    priority: str = Field(EmailPriority.NORMAL, description="Email priority")
    cc: Optional[List[EmailStr]] = Field(None, description="CC recipients")
    bcc: Optional[List[EmailStr]] = Field(None, description="BCC recipients")
    reply_to: Optional[EmailStr] = Field(None, description="Reply-to email address")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="Email attachments")


class WelcomeEmailRequest(BaseModel):
    """Request model for sending a welcome email"""

    user_email: EmailStr = Field(..., description="User's email address")
    user_name: str = Field(..., description="User's name")
    additional_data: Optional[Dict[str, Any]] = Field(None, description="Additional template data")


class PasswordResetEmailRequest(BaseModel):
    """Request model for sending password reset email"""

    user_email: EmailStr = Field(..., description="User's email address")
    user_name: str = Field(..., description="User's name")
    reset_token: str = Field(..., description="Password reset token")
    reset_url: Optional[str] = Field(None, description="Custom reset URL")


class VerificationEmailRequest(BaseModel):
    """Request model for sending verification email"""

    user_email: EmailStr = Field(..., description="User's email address")
    user_name: str = Field(..., description="User's name")
    verification_token: str = Field(..., description="Verification token")
    verification_url: Optional[str] = Field(None, description="Custom verification URL")


class CreateTemplateRequest(BaseModel):
    """Request model for creating an email template"""

    name: str = Field(..., description="Template name")
    subject: str = Field(..., description="Template subject")
    html_content: str = Field(..., description="HTML template content")
    text_content: Optional[str] = Field(None, description="Plain text template content")
    generation: str = Field("legacy", description="Template generation: legacy or dynamic")


@router.post("/email/send")
async def send_email(
    request: SendEmailRequest,
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """
    Send an email using SendGrid

    Args:
        request: Email parameters
        current_user: Authenticated user (admin/teacher only)

    Returns:
        JSONResponse: Email send confirmation
    """
    try:
        # Check permissions - only admin and teacher can send emails
        user_role = getattr(current_user, "role", "student")
        if user_role not in ["admin", "teacher"]:
            raise HTTPException(
                status_code=403, detail="Only admins and teachers can send emails"
            )

        # Convert attachments if provided
        attachments = None
        if request.attachments:
            attachments = [
                EmailAttachment(
                    content=att.get("content", b""),
                    filename=att.get("filename", "attachment"),
                    content_type=att.get("content_type"),
                )
                for att in request.attachments
            ]

        # Send email
        result = await email_service.send_email(
            to_email=request.to_email,
            to_name=request.to_name,
            subject=request.subject,
            html_content=request.html_content,
            text_content=request.text_content,
            template_id=request.template_id,
            template_data=request.template_data,
            email_type=request.email_type,
            priority=request.priority,
            cc=request.cc,
            bcc=request.bcc,
            reply_to=request.reply_to,
            attachments=attachments,
        )

        # Log email sent
        log_audit(
            action="email_sent",
            user_id=current_user.id,
            resource_type="email",
            resource_id=result.get("message_id", "unknown"),
            details={
                "to": request.to_email,
                "subject": request.subject,
                "type": request.email_type,
            },
        )

        return JSONResponse(
            content={
                "status": "success",
                "data": {
                    "message_id": result.get("message_id"),
                    "sent": True,
                    "to": request.to_email,
                },
                "message": "Email sent successfully",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")


@router.post("/email/welcome")
async def send_welcome_email(
    request: WelcomeEmailRequest,
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """
    Send a welcome email to a new user

    Args:
        request: Welcome email parameters
        current_user: Authenticated user (admin only)

    Returns:
        JSONResponse: Email send confirmation
    """
    try:
        # Check permissions - only admin can send welcome emails
        if getattr(current_user, "role", None) != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")

        # Send welcome email
        result = await email_service.send_welcome_email(
            user_email=request.user_email,
            user_name=request.user_name,
            additional_data=request.additional_data or {},
        )

        # Log welcome email sent
        log_audit(
            action="welcome_email_sent",
            user_id=current_user.id,
            resource_type="email",
            resource_id=result.get("message_id", "unknown"),
            details={"to": request.user_email, "name": request.user_name},
        )

        return JSONResponse(
            content={
                "status": "success",
                "data": {
                    "message_id": result.get("message_id"),
                    "sent": True,
                },
                "message": "Welcome email sent successfully",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send welcome email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send welcome email: {str(e)}")


@router.post("/email/password-reset")
async def send_password_reset_email(
    request: PasswordResetEmailRequest,
) -> JSONResponse:
    """
    Send a password reset email (public endpoint for password reset flow)

    Args:
        request: Password reset email parameters

    Returns:
        JSONResponse: Email send confirmation
    """
    try:
        # Build reset URL
        reset_url = request.reset_url or f"{settings.FRONTEND_URL}/reset-password?token={request.reset_token}"

        # Send password reset email
        result = await email_service.send_password_reset_email(
            user_email=request.user_email,
            user_name=request.user_name,
            reset_token=request.reset_token,
            reset_url=reset_url,
        )

        # Log password reset email sent (without user_id since this is public)
        logger.info(f"Password reset email sent to {request.user_email}")

        return JSONResponse(
            content={
                "status": "success",
                "data": {
                    "message_id": result.get("message_id"),
                    "sent": True,
                },
                "message": "Password reset email sent successfully",
            }
        )

    except Exception as e:
        logger.error(f"Failed to send password reset email: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to send password reset email: {str(e)}"
        )


@router.post("/email/verification")
async def send_verification_email(
    request: VerificationEmailRequest,
) -> JSONResponse:
    """
    Send an email verification link (public endpoint for registration flow)

    Args:
        request: Verification email parameters

    Returns:
        JSONResponse: Email send confirmation
    """
    try:
        # Build verification URL
        verification_url = (
            request.verification_url
            or f"{settings.FRONTEND_URL}/verify-email?token={request.verification_token}"
        )

        # Send verification email
        result = await email_service.send_verification_email(
            user_email=request.user_email,
            user_name=request.user_name,
            verification_token=request.verification_token,
            verification_url=verification_url,
        )

        # Log verification email sent
        logger.info(f"Verification email sent to {request.user_email}")

        return JSONResponse(
            content={
                "status": "success",
                "data": {
                    "message_id": result.get("message_id"),
                    "sent": True,
                },
                "message": "Verification email sent successfully",
            }
        )

    except Exception as e:
        logger.error(f"Failed to send verification email: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to send verification email: {str(e)}"
        )


@router.post("/email/templates")
async def create_email_template(
    request: CreateTemplateRequest,
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """
    Create a new email template in SendGrid

    Args:
        request: Template parameters
        current_user: Authenticated user (admin only)

    Returns:
        JSONResponse: Template creation confirmation
    """
    try:
        # Check permissions - only admin can create templates
        if getattr(current_user, "role", None) != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")

        # Create template
        template_id = await email_service.create_template(
            name=request.name,
            generation=request.generation,
        )

        if not template_id:
            raise HTTPException(status_code=500, detail="Failed to create template")

        # Create template version with content
        version_id = await email_service.create_template_version(
            template_id=template_id,
            name=f"{request.name} - v1",
            subject=request.subject,
            html_content=request.html_content,
            text_content=request.text_content,
        )

        # Log template creation
        log_audit(
            action="email_template_created",
            user_id=current_user.id,
            resource_type="email_template",
            resource_id=template_id,
            details={"name": request.name, "version_id": version_id},
        )

        return JSONResponse(
            content={
                "status": "success",
                "data": {
                    "template_id": template_id,
                    "version_id": version_id,
                    "name": request.name,
                },
                "message": "Email template created successfully",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create email template: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create email template: {str(e)}")


@router.post("/email/webhook")
async def handle_sendgrid_webhook(request: Request) -> JSONResponse:
    """
    Handle SendGrid webhook events

    Args:
        request: Request object containing webhook events

    Returns:
        JSONResponse: Webhook processing result
    """
    try:
        # Parse webhook events
        events = await request.json()

        # Process webhook events
        result = await email_service.handle_webhook(events=events)

        # Log webhook processing
        logger.info(f"Processed {result.get('processed_count', 0)} SendGrid webhook events")

        return JSONResponse(
            content={
                "status": "success",
                "data": {
                    "processed_count": result.get("processed_count", 0),
                    "events": result.get("events", []),
                },
                "message": "Webhook processed successfully",
            }
        )

    except Exception as e:
        logger.error(f"Failed to process SendGrid webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")


@router.get("/email/status/{message_id}")
async def get_email_status(
    message_id: str,
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """
    Get the status of a sent email

    Args:
        message_id: SendGrid message ID
        current_user: Authenticated user

    Returns:
        JSONResponse: Email status information
    """
    try:
        # Get email status
        status = await email_service.get_email_status(message_id=message_id)

        if not status:
            raise HTTPException(status_code=404, detail="Email status not found")

        return JSONResponse(
            content={
                "status": "success",
                "data": status,
                "message": "Email status retrieved successfully",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get email status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get email status: {str(e)}")

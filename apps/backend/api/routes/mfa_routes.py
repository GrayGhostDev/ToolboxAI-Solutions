"""
MFA API Routes
Phase 3 Implementation - Complete MFA endpoints
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from apps.backend.api.auth.auth import get_current_user
from apps.backend.api.auth.mfa import (
    MFAFeatureFlags,
    MFAMethod,
    MFARateLimitError,
    MFAService,
    get_mfa_feature_flags,
    get_mfa_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mfa", tags=["MFA"])

# ===== Request/Response Models =====


class MFASetupInitRequest(BaseModel):
    """Request to initialize MFA setup"""

    method: MFAMethod
    phone_number: str | None = Field(None, description="Phone for SMS method")
    email: str | None = Field(None, description="Email for email method")


class MFASetupConfirmRequest(BaseModel):
    """Request to confirm MFA setup"""

    method: MFAMethod
    code: str = Field(..., min_length=6, max_length=6, description="Verification code")


class MFAVerifyRequest(BaseModel):
    """Request to verify MFA code"""

    method: MFAMethod
    code: str = Field(..., description="Verification code or backup code")
    device_id: str | None = Field(None, description="Device identifier for trust")
    trust_device: bool = Field(False, description="Whether to trust this device")


class MFADisableRequest(BaseModel):
    """Request to disable MFA"""

    method: MFAMethod | None = Field(None, description="Specific method to disable")
    password: str = Field(..., description="Current password for verification")


class MFABackupCodesRequest(BaseModel):
    """Request new backup codes"""

    regenerate: bool = Field(True, description="Generate new codes")


# ===== Setup Endpoints =====


@router.post("/setup/init", status_code=status.HTTP_200_OK)
async def init_mfa_setup(
    request: MFASetupInitRequest,
    current_user: dict = Depends(get_current_user),
    mfa_service: MFAService = Depends(get_mfa_service),
    feature_flags: MFAFeatureFlags = Depends(get_mfa_feature_flags),
):
    """
    Initialize MFA setup for a specific method.

    Returns setup information based on method:
    - TOTP: QR code and secret
    - SMS: Sends code to phone
    - Email: Sends code to email
    """

    user_id = current_user["id"]

    # Check feature flag
    if not feature_flags.is_mfa_enabled_for_user(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="MFA is not available for your account yet",
        )

    try:
        if request.method == MFAMethod.TOTP:
            # Generate TOTP secret and QR code
            secret = mfa_service.generate_totp_secret(user_id)
            qr_code = mfa_service.generate_qr_code(
                current_user.get("email", "user@toolboxai.com"), secret
            )

            # Generate backup codes
            backup_codes = mfa_service.generate_backup_codes(user_id)

            return {
                "method": "totp",
                "setup_required": True,
                "qr_code": f"data:image/png;base64,{qr_code}",
                "secret": secret,
                "backup_codes": backup_codes,
                "instructions": "Scan the QR code with your authenticator app",
            }

        elif request.method == MFAMethod.SMS:
            if not request.phone_number:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Phone number required for SMS method",
                )

            # Send SMS code
            success = await mfa_service.send_sms_code(user_id, request.phone_number)

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="SMS service temporarily unavailable",
                )

            return {
                "method": "sms",
                "code_sent": True,
                "phone_number": f"***{request.phone_number[-4:]}",
                "expires_in": 300,
                "instructions": "Enter the 6-digit code sent to your phone",
            }

        elif request.method == MFAMethod.EMAIL:
            email = request.email or current_user.get("email")
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Email address required"
                )

            # Send email code
            success = await mfa_service.send_email_code(user_id, email)

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Email service temporarily unavailable",
                )

            return {
                "method": "email",
                "code_sent": True,
                "email": f"{email[:3]}***@{email.split('@')[1]}",
                "expires_in": 600,
                "instructions": "Enter the 6-digit code sent to your email",
            }

    except Exception as e:
        logger.error(f"MFA setup init failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize MFA setup",
        )


@router.post("/setup/confirm", status_code=status.HTTP_201_CREATED)
async def confirm_mfa_setup(
    request: MFASetupConfirmRequest,
    current_user: dict = Depends(get_current_user),
    mfa_service: MFAService = Depends(get_mfa_service),
):
    """Confirm MFA setup by verifying initial code"""

    user_id = current_user["id"]

    try:
        # Verify the setup code
        is_valid = False

        if request.method == MFAMethod.TOTP:
            is_valid = mfa_service.verify_totp(user_id, request.code)
        elif request.method in [MFAMethod.SMS, MFAMethod.EMAIL]:
            is_valid = mfa_service.verify_code(user_id, request.code, request.method)

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code"
            )

        # Enable MFA method for user
        mfa_service.enable_mfa(user_id, request.method)

        return {
            "success": True,
            "method": request.method.value,
            "message": f"MFA {request.method.value} successfully enabled",
            "backup_codes_available": request.method == MFAMethod.TOTP,
        }

    except MFARateLimitError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Please try again later.",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MFA setup confirm failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to confirm MFA setup"
        )


# ===== Verification Endpoints =====


@router.post("/verify", status_code=status.HTTP_200_OK)
async def verify_mfa(
    request: MFAVerifyRequest,
    current_user: dict = Depends(get_current_user),
    mfa_service: MFAService = Depends(get_mfa_service),
):
    """Verify MFA code during authentication"""

    user_id = current_user["id"]

    try:
        is_valid = False

        if request.method == MFAMethod.TOTP:
            is_valid = mfa_service.verify_totp(user_id, request.code)

        elif request.method == MFAMethod.BACKUP_CODE:
            is_valid = mfa_service.verify_backup_code(user_id, request.code)

        elif request.method in [MFAMethod.SMS, MFAMethod.EMAIL]:
            is_valid = mfa_service.verify_code(user_id, request.code, request.method)

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid verification code"
            )

        # Trust device if requested
        device_token = None
        if request.trust_device and request.device_id:
            device_token = mfa_service.trust_device(user_id, request.device_id)

        return {
            "verified": True,
            "method": request.method.value,
            "device_token": device_token,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except MFARateLimitError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Please try again in 15 minutes.",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MFA verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Verification failed"
        )


@router.post("/resend", status_code=status.HTTP_200_OK)
async def resend_mfa_code(
    method: MFAMethod,
    phone_number: str | None = None,
    email: str | None = None,
    current_user: dict = Depends(get_current_user),
    mfa_service: MFAService = Depends(get_mfa_service),
):
    """Resend MFA code via SMS or Email"""

    if method not in [MFAMethod.SMS, MFAMethod.EMAIL]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Can only resend SMS or Email codes"
        )

    user_id = current_user["id"]

    try:
        if method == MFAMethod.SMS:
            if not phone_number:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number required"
                )

            success = await mfa_service.send_sms_code(user_id, phone_number)
            expires_in = 300

        else:  # Email
            if not email:
                email = current_user.get("email")
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Email address required"
                )

            success = await mfa_service.send_email_code(user_id, email)
            expires_in = 600

        if not success:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"{method.value} service temporarily unavailable",
            )

        return {
            "success": True,
            "method": method.value,
            "expires_in": expires_in,
            "message": f"New code sent via {method.value}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MFA resend failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to resend code"
        )


# ===== Management Endpoints =====


@router.get("/status", status_code=status.HTTP_200_OK)
async def get_mfa_status(
    current_user: dict = Depends(get_current_user),
    mfa_service: MFAService = Depends(get_mfa_service),
    feature_flags: MFAFeatureFlags = Depends(get_mfa_feature_flags),
):
    """Get user's MFA configuration status"""

    user_id = current_user["id"]

    status = mfa_service.get_user_mfa_status(user_id)
    mfa_available = feature_flags.is_mfa_enabled_for_user(user_id)

    return {
        "mfa_available": mfa_available,
        "mfa_enabled": status["mfa_enabled"],
        "methods": status["methods"],
        "backup_codes_remaining": status["backup_codes_remaining"],
        "require_setup": mfa_service.require_mfa_setup(user_id) and mfa_available,
    }


@router.post("/disable", status_code=status.HTTP_200_OK)
async def disable_mfa(
    request: MFADisableRequest,
    current_user: dict = Depends(get_current_user),
    mfa_service: MFAService = Depends(get_mfa_service),
):
    """Disable MFA method(s) for user"""

    user_id = current_user["id"]

    # TODO: Verify password before disabling
    # This would require importing password verification from auth module

    try:
        if request.method:
            # Disable specific method
            success = mfa_service.disable_mfa(user_id, request.method)
            message = f"MFA method {request.method.value} disabled"
        else:
            # Disable all MFA
            success = mfa_service.disable_mfa(user_id)
            message = "All MFA methods disabled"

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to disable MFA"
            )

        return {"success": True, "message": message}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MFA disable failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to disable MFA"
        )


@router.post("/backup-codes", status_code=status.HTTP_200_OK)
async def manage_backup_codes(
    request: MFABackupCodesRequest,
    current_user: dict = Depends(get_current_user),
    mfa_service: MFAService = Depends(get_mfa_service),
):
    """Generate new backup codes"""

    user_id = current_user["id"]

    # Check if MFA is enabled
    status = mfa_service.get_user_mfa_status(user_id)
    if not status["mfa_enabled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA must be enabled to generate backup codes",
        )

    try:
        if request.regenerate:
            codes = mfa_service.generate_backup_codes(user_id)

            return {
                "success": True,
                "backup_codes": codes,
                "message": "New backup codes generated. Store them securely.",
                "warning": "Previous backup codes have been invalidated.",
            }
        else:
            # Just return count
            return {"success": True, "backup_codes_remaining": status["backup_codes_remaining"]}

    except Exception as e:
        logger.error(f"Backup codes generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate backup codes",
        )


# ===== Admin Endpoints =====


@router.post("/admin/rollout", status_code=status.HTTP_200_OK)
async def set_mfa_rollout(
    percentage: int = Field(..., ge=0, le=100),
    current_user: dict = Depends(get_current_user),
    feature_flags: MFAFeatureFlags = Depends(get_mfa_feature_flags),
):
    """Set MFA rollout percentage (admin only)"""

    # Check if user is admin
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    feature_flags.set_mfa_rollout_percentage(percentage)

    return {
        "success": True,
        "rollout_percentage": percentage,
        "message": f"MFA rollout set to {percentage}%",
    }


@router.post("/admin/enable-role", status_code=status.HTTP_200_OK)
async def enable_mfa_for_role(
    role: str,
    current_user: dict = Depends(get_current_user),
    feature_flags: MFAFeatureFlags = Depends(get_mfa_feature_flags),
):
    """Enable MFA for specific role (admin only)"""

    # Check if user is admin
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    feature_flags.enable_mfa_for_role(role)

    return {"success": True, "role": role, "message": f"MFA enabled for role: {role}"}


@router.post("/admin/enable-user", status_code=status.HTTP_200_OK)
async def enable_mfa_for_user(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    feature_flags: MFAFeatureFlags = Depends(get_mfa_feature_flags),
):
    """Enable MFA for specific user (admin only)"""

    # Check if user is admin
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    feature_flags.enable_mfa_for_user(user_id)

    return {"success": True, "user_id": user_id, "message": f"MFA enabled for user: {user_id}"}

"""
Password Management API Endpoints

Provides secure endpoints for password change and reset operations
with comprehensive security features including session invalidation.
"""

import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ....api.auth.password_management import (
    PasswordChangeRequest,
    PasswordResetRequest,
    get_password_service,
    PasswordChangeService
)
from ....api.auth.auth import get_current_user, redis_client
from ....core.security.session_manager import get_session_manager, initialize_session_manager
from ....models.schemas import User
from ....services.database import get_db_session, update_user_password

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/password",
    tags=["password"],
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized"},
        429: {"description": "Too many requests"}
    }
)

# Initialize session manager with Redis
session_manager = initialize_session_manager(redis_client=redis_client)

# Initialize password service
password_service = get_password_service(
    session_manager=session_manager,
    redis_client=redis_client
)


@router.post("/change", response_model=Dict[str, Any])
async def change_password(
    request: Request,
    password_request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Change the current user's password.
    
    This endpoint:
    1. Validates the current password
    2. Checks new password strength
    3. Ensures password wasn't recently used
    4. Invalidates all existing sessions
    5. Requires re-authentication
    
    **Security Features:**
    - Rate limiting (5 changes per day)
    - Password strength validation
    - Password history check
    - Automatic session invalidation
    - Audit logging
    
    **Request Body:**
    - `current_password`: Current password for verification
    - `new_password`: New password (min 8 characters)
    - `confirm_password`: Password confirmation
    - `logout_all_devices`: Whether to logout from all devices (default: true)
    
    **Response:**
    - `success`: Operation status
    - `message`: Success message
    - `sessions_invalidated`: Number of sessions invalidated
    - `action_required`: Next steps for the user
    """
    try:
        # Get client information for audit logging
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("User-Agent")
        
        # Verify current password
        from ....api.auth.auth import verify_password, get_user_from_db
        
        # Get user from database with current password hash
        user_data = await get_user_from_db(current_user.username)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password matches
        if not verify_password(password_request.current_password, user_data.get("password_hash", "")):
            logger.warning(f"Invalid current password for user {current_user.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )
        
        # Change password with security checks
        result = await password_service.change_password(
            user_id=current_user.id,
            username=current_user.username,
            current_password=password_request.current_password,
            new_password=password_request.new_password,
            request_ip=client_ip,
            user_agent=user_agent
        )
        
        # Update password in database
        async with get_db_session() as db:
            await update_user_password(
                db=db,
                user_id=current_user.id,
                password_hash=result.get("password_hash")
            )
        
        # Return success response (password hash removed)
        return {
            "success": result["success"],
            "message": result["message"],
            "sessions_invalidated": result["sessions_invalidated"],
            "remaining_changes_today": result.get("remaining_changes_today", 0),
            "password_strength_score": result.get("password_strength_score", 0),
            "action_required": result["action_required"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change failed for user {current_user.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed. Please try again."
        )


@router.post("/reset", response_model=Dict[str, Any])
async def reset_user_password(
    request: Request,
    reset_request: PasswordResetRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Reset a user's password (Admin only).
    
    This endpoint allows administrators to reset any user's password.
    It automatically invalidates all sessions for the target user.
    
    **Required Role:** admin
    
    **Request Body:**
    - `user_id`: ID of the user whose password to reset
    - `new_password`: New password to set
    - `reason`: Reason for the password reset
    - `force_logout`: Force logout from all devices (default: true)
    
    **Response:**
    - `success`: Operation status
    - `message`: Success message
    - `sessions_invalidated`: Number of sessions invalidated
    - `reset_by`: Admin who performed the reset
    """
    # Check if current user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can reset passwords"
        )
    
    try:
        # Reset password with admin privileges
        result = await password_service.reset_password(
            admin_user_id=current_user.id,
            target_user_id=reset_request.user_id,
            new_password=reset_request.new_password,
            reason=reset_request.reason,
            force_logout=reset_request.force_logout
        )
        
        # Update password in database
        async with get_db_session() as db:
            await update_user_password(
                db=db,
                user_id=reset_request.user_id,
                password_hash=result["password_hash"]
            )
        
        # Return success response (password hash removed)
        return {
            "success": result["success"],
            "message": result["message"],
            "sessions_invalidated": result["sessions_invalidated"],
            "reset_by": result["reset_by"],
            "reset_reason": result["reset_reason"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset failed by admin {current_user.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed. Please try again."
        )


@router.get("/strength-requirements", response_model=Dict[str, Any])
async def get_password_requirements() -> Dict[str, Any]:
    """
    Get password strength requirements.
    
    Returns the current password policy requirements for the system.
    
    **Response:**
    - `min_length`: Minimum password length
    - `max_length`: Maximum password length
    - `require_uppercase`: Whether uppercase letters are required
    - `require_lowercase`: Whether lowercase letters are required
    - `require_digit`: Whether digits are required
    - `require_special`: Whether special characters are required
    - `special_characters`: Allowed special characters
    """
    from ....api.auth.password_management import PasswordStrengthRequirements
    
    requirements = PasswordStrengthRequirements()
    
    return {
        "min_length": requirements.MIN_LENGTH,
        "max_length": requirements.MAX_LENGTH,
        "require_uppercase": requirements.REQUIRE_UPPERCASE,
        "require_lowercase": requirements.REQUIRE_LOWERCASE,
        "require_digit": requirements.REQUIRE_DIGIT,
        "require_special": requirements.REQUIRE_SPECIAL,
        "special_characters": requirements.SPECIAL_CHARS,
        "password_history": 5,
        "max_changes_per_day": 5
    }


@router.post("/validate", response_model=Dict[str, Any])
async def validate_password_strength(
    password: str,
    username: Optional[str] = None,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Validate password strength without changing it.
    
    This endpoint allows users to check if a password meets
    security requirements before attempting to change it.
    
    **Query Parameters:**
    - `password`: Password to validate
    - `username`: Username to check against (optional)
    
    **Response:**
    - `is_valid`: Whether the password meets requirements
    - `score`: Password strength score (0-100)
    - `issues`: List of validation issues
    - `suggestions`: List of improvement suggestions
    """
    from ....api.auth.password_management import PasswordValidator
    
    validator = PasswordValidator()
    
    # Use provided username or current user's username
    check_username = username or current_user.username
    
    # Validate password
    result = validator.validate(password, check_username)
    
    return {
        "is_valid": result.is_valid,
        "score": result.score,
        "issues": result.issues,
        "suggestions": result.suggestions
    }


@router.get("/sessions", response_model=Dict[str, Any])
async def get_active_sessions(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get all active sessions for the current user.
    
    Returns a list of all active sessions across different devices.
    
    **Response:**
    - `sessions`: List of active sessions
    - `total`: Total number of active sessions
    - `max_allowed`: Maximum sessions allowed per user
    """
    sessions = session_manager.get_user_sessions(current_user.id)
    
    session_list = []
    for session in sessions:
        session_list.append({
            "session_id": session.session_id[:8] + "...",  # Partial ID for security
            "created_at": session.created_at,
            "last_activity": session.last_activity,
            "expires_at": session.expires_at,
            "ip_address": session.ip_address,
            "user_agent": session.user_agent,
            "device_id": session.device_id,
            "is_current": False  # Would need to check against current session
        })
    
    return {
        "sessions": session_list,
        "total": len(session_list),
        "max_allowed": session_manager.max_sessions_per_user
    }


@router.post("/logout-all", response_model=Dict[str, Any])
async def logout_all_sessions(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Logout from all devices.
    
    Invalidates all active sessions for the current user,
    forcing re-authentication on all devices.
    
    **Response:**
    - `success`: Operation status
    - `sessions_invalidated`: Number of sessions invalidated
    - `message`: Success message
    """
    try:
        count = session_manager.invalidate_all_user_sessions(
            user_id=current_user.id,
            reason="manual_logout_all"
        )
        
        return {
            "success": True,
            "sessions_invalidated": count,
            "message": f"Successfully logged out from {count} device(s)"
        }
        
    except Exception as e:
        logger.error(f"Failed to logout all sessions for user {current_user.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to logout from all devices"
        )
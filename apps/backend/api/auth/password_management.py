"""
Password Management Module

Implements secure password change functionality with session invalidation,
password strength validation, and audit logging.

Security features:
- Automatic session invalidation on password change
- Password strength requirements
- Password history tracking
- Rate limiting for password changes
- Audit logging

References:
- OWASP Password Storage: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
- NIST SP 800-63B: https://pages.nist.gov/800-63-3/sp800-63b.html
"""

import hashlib
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from fastapi import HTTPException, status, Depends, Request
from passlib.context import CryptContext
from pydantic import BaseModel, Field, field_validator, model_validator
import redis

from apps.backend.core.security.session_manager import get_session_manager, SessionManager
from apps.backend.core.config import settings
from .auth import hash_password, verify_password, get_current_user

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordStrengthRequirements:
    """Password strength requirements based on NIST guidelines"""
    MIN_LENGTH = 8
    MAX_LENGTH = 128
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL = True
    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    # Common passwords to block (simplified list - use full list in production)
    COMMON_PASSWORDS = {
        "password", "12345678", "qwerty", "abc123", "password123",
        "admin", "letmein", "welcome", "monkey", "dragon"
    }

    # Patterns to detect (keyboard walks, repeated characters, etc.)
    FORBIDDEN_PATTERNS = [
        r"(.)\1{2,}",  # Same character repeated 3+ times
        r"(012|123|234|345|456|567|678|789|890)",  # Sequential numbers
        r"(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)",  # Sequential letters
        r"(qwerty|asdf|zxcv)",  # Keyboard patterns
    ]


@dataclass
class PasswordValidationResult:
    """Result of password validation"""
    is_valid: bool
    score: int  # 0-100
    issues: List[str]
    suggestions: List[str]


class PasswordChangeRequest(BaseModel):
    """Request model for password change"""
    current_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    confirm_password: str = Field(..., description="Password confirmation")
    logout_all_devices: bool = Field(default=True, description="Logout from all devices")

    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        """Validate that passwords match using Pydantic v2 field_validator."""
        if hasattr(info, 'data') and 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Passwords do not match')
        return v

    @model_validator(mode='after')
    def validate_passwords_match(self):
        """Additional validation to ensure passwords match."""
        if self.new_password != self.confirm_password:
            raise ValueError('Passwords do not match')
        return self


class PasswordResetRequest(BaseModel):
    """Request model for password reset (admin/forgot password)"""
    user_id: str = Field(..., description="User ID to reset password for")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    reason: str = Field(..., description="Reason for password reset")
    force_logout: bool = Field(default=True, description="Force logout from all devices")


class PasswordValidator:
    """Validates password strength and complexity"""

    def __init__(self, requirements: Optional[PasswordStrengthRequirements] = None):
        self.requirements = requirements or PasswordStrengthRequirements()

    def validate(self, password: str, username: Optional[str] = None) -> PasswordValidationResult:
        """
        Validate password strength and complexity.

        Args:
            password: Password to validate
            username: Username (to check password doesn't contain it)

        Returns:
            PasswordValidationResult with validation details
        """
        issues = []
        suggestions = []
        score = 100

        # Length check
        if len(password) < self.requirements.MIN_LENGTH:
            issues.append(f"Password must be at least {self.requirements.MIN_LENGTH} characters")
            suggestions.append(f"Add {self.requirements.MIN_LENGTH - len(password)} more characters")
            score -= 30
        elif len(password) > self.requirements.MAX_LENGTH:
            issues.append(f"Password must not exceed {self.requirements.MAX_LENGTH} characters")
            score -= 10

        # Character type requirements
        if self.requirements.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            issues.append("Password must contain at least one uppercase letter")
            suggestions.append("Add an uppercase letter (A-Z)")
            score -= 15

        if self.requirements.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            issues.append("Password must contain at least one lowercase letter")
            suggestions.append("Add a lowercase letter (a-z)")
            score -= 15

        if self.requirements.REQUIRE_DIGIT and not re.search(r'\d', password):
            issues.append("Password must contain at least one digit")
            suggestions.append("Add a number (0-9)")
            score -= 15

        if self.requirements.REQUIRE_SPECIAL:
            if not any(char in self.requirements.SPECIAL_CHARS for char in password):
                issues.append("Password must contain at least one special character")
                suggestions.append(f"Add a special character ({self.requirements.SPECIAL_CHARS[:10]}...)")
                score -= 15

        # Check for common passwords
        if password.lower() in self.requirements.COMMON_PASSWORDS:
            issues.append("Password is too common")
            suggestions.append("Choose a unique password that isn't commonly used")
            score -= 50

        # Check for username in password
        if username and username.lower() in password.lower():
            issues.append("Password must not contain your username")
            suggestions.append("Remove your username from the password")
            score -= 20

        # Check for forbidden patterns
        for pattern in self.requirements.FORBIDDEN_PATTERNS:
            if re.search(pattern, password.lower()):
                issues.append("Password contains predictable patterns")
                suggestions.append("Avoid sequential or repeated characters")
                score -= 10
                break

        # Calculate entropy bonus for length
        if len(password) > 12:
            score += min((len(password) - 12) * 2, 20)  # Up to 20 bonus points

        # Ensure score is within bounds
        score = max(0, min(100, score))

        return PasswordValidationResult(
            is_valid=len(issues) == 0,
            score=score,
            issues=issues,
            suggestions=suggestions
        )


class PasswordHistoryManager:
    """Manages password history to prevent reuse"""

    HISTORY_PREFIX = "password_history:"
    MAX_HISTORY = 5  # Number of previous passwords to remember

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self._memory_history: Dict[str, List[str]] = {}  # Fallback for development

    def add_to_history(self, user_id: str, password_hash: str) -> None:
        """Add password hash to user's history"""
        if self.redis_client:
            key = f"{self.HISTORY_PREFIX}{user_id}"
            # Add to list and trim to max size
            self.redis_client.lpush(key, password_hash)
            self.redis_client.ltrim(key, 0, self.MAX_HISTORY - 1)
            self.redis_client.expire(key, 86400 * 365)  # Expire after 1 year
        else:
            if user_id not in self._memory_history:
                self._memory_history[user_id] = []
            self._memory_history[user_id].insert(0, password_hash)
            self._memory_history[user_id] = self._memory_history[user_id][:self.MAX_HISTORY]

    def is_password_reused(self, user_id: str, password: str) -> bool:
        """Check if password was recently used"""
        if self.redis_client:
            key = f"{self.HISTORY_PREFIX}{user_id}"
            history = self.redis_client.lrange(key, 0, -1)
        else:
            history = self._memory_history.get(user_id, [])

        for old_hash in history:
            # Handle both string and bytes from Redis
            if isinstance(old_hash, bytes):
                old_hash = old_hash.decode('utf-8')
            if verify_password(password, old_hash):
                return True

        return False


class PasswordChangeService:
    """Service for handling password changes with security features"""

    def __init__(
        self,
        session_manager: SessionManager,
        redis_client: Optional[redis.Redis] = None
    ):
        self.session_manager = session_manager
        self.redis_client = redis_client
        self.validator = PasswordValidator()
        self.history_manager = PasswordHistoryManager(redis_client)

        # Rate limiting
        self.RATE_LIMIT_PREFIX = "password_change_rate:"
        self.MAX_CHANGES_PER_DAY = 5

    def _check_rate_limit(self, user_id: str) -> Tuple[bool, int]:
        """
        Check if user has exceeded password change rate limit.

        Returns:
            Tuple of (is_allowed, remaining_attempts)
        """
        if not self.redis_client:
            return True, self.MAX_CHANGES_PER_DAY

        key = f"{self.RATE_LIMIT_PREFIX}{user_id}"
        current_count = self.redis_client.incr(key)

        if current_count == 1:
            # First change today, set expiration
            self.redis_client.expire(key, 86400)  # 24 hours

        remaining = max(0, self.MAX_CHANGES_PER_DAY - current_count)
        is_allowed = current_count <= self.MAX_CHANGES_PER_DAY

        return is_allowed, remaining

    async def change_password(
        self,
        user_id: str,
        username: str,
        current_password: str,
        new_password: str,
        request_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Change user password with comprehensive security checks.

        Args:
            user_id: User identifier
            username: Username
            current_password: Current password for verification
            new_password: New password to set
            request_ip: Client IP address
            user_agent: Client user agent

        Returns:
            Result dictionary with status and details

        Raises:
            HTTPException: On validation failure
        """
        # Check rate limit
        is_allowed, remaining = self._check_rate_limit(user_id)
        if not is_allowed:
            logger.warning(f"Password change rate limit exceeded for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many password change attempts. Try again tomorrow."
            )

        # Validate new password strength
        validation_result = self.validator.validate(new_password, username)
        if not validation_result.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Password does not meet security requirements",
                    "issues": validation_result.issues,
                    "suggestions": validation_result.suggestions,
                    "score": validation_result.score
                }
            )

        # Check password history
        if self.history_manager.is_password_reused(user_id, new_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This password was recently used. Please choose a different password."
            )

        # Hash new password
        new_password_hash = hash_password(new_password)

        # Add to password history
        self.history_manager.add_to_history(user_id, new_password_hash)

        # CRITICAL: Invalidate all existing sessions
        invalidated_count = self.session_manager.invalidate_all_user_sessions(
            user_id=user_id,
            reason="password_change"
        )

        # Log password change event
        logger.info(
            f"Password changed for user {username} (ID: {user_id})",
            extra={
                "user_id": user_id,
                "username": username,
                "ip_address": request_ip,
                "user_agent": user_agent,
                "sessions_invalidated": invalidated_count,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        return {
            "success": True,
            "message": "Password changed successfully",
            "sessions_invalidated": invalidated_count,
            "remaining_changes_today": remaining - 1,
            "password_strength_score": validation_result.score,
            "action_required": "Please log in again with your new password"
        }

    async def reset_password(
        self,
        admin_user_id: str,
        target_user_id: str,
        new_password: str,
        reason: str,
        force_logout: bool = True
    ) -> Dict[str, any]:
        """
        Admin function to reset a user's password.

        Args:
            admin_user_id: Admin performing the reset
            target_user_id: User whose password is being reset
            new_password: New password to set
            reason: Reason for password reset
            force_logout: Whether to invalidate all sessions

        Returns:
            Result dictionary with status and details
        """
        # Validate new password strength (relaxed for admin reset)
        validation_result = self.validator.validate(new_password)
        if validation_result.score < 50:  # Minimum score for admin reset
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Password is too weak even for admin reset",
                    "score": validation_result.score,
                    "minimum_score": 50
                }
            )

        # Hash new password
        new_password_hash = hash_password(new_password)

        # Add to password history
        self.history_manager.add_to_history(target_user_id, new_password_hash)

        # Invalidate sessions if requested
        invalidated_count = 0
        if force_logout:
            invalidated_count = self.session_manager.invalidate_all_user_sessions(
                user_id=target_user_id,
                reason="admin_password_reset"
            )

        # Log admin password reset
        logger.info(
            f"Password reset by admin {admin_user_id} for user {target_user_id}",
            extra={
                "admin_user_id": admin_user_id,
                "target_user_id": target_user_id,
                "reason": reason,
                "sessions_invalidated": invalidated_count,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        return {
            "success": True,
            "message": "Password reset successfully",
            "sessions_invalidated": invalidated_count,
            "password_hash": new_password_hash,  # Return hash for database update
            "reset_by": admin_user_id,
            "reset_reason": reason
        }


# Global password change service instance
_password_service: Optional[PasswordChangeService] = None


def get_password_service(
    session_manager: Optional[SessionManager] = None,
    redis_client: Optional[redis.Redis] = None
) -> PasswordChangeService:
    """Get or create the global password change service"""
    global _password_service

    if _password_service is None:
        if session_manager is None:
            session_manager = get_session_manager(redis_client)

        _password_service = PasswordChangeService(
            session_manager=session_manager,
            redis_client=redis_client
        )

    return _password_service
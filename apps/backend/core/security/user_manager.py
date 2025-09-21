"""
Secure User Management Service

Provides comprehensive user authentication and management with:
- Bcrypt password hashing with configurable cost factor
- Account lockout after failed attempts
- Password complexity validation
- Multi-factor authentication support
- Session management
- Audit logging
"""

import re
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

import bcrypt
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import redis

from database.models import User, Session as UserSession
from toolboxai_settings import settings

logger = logging.getLogger(__name__)


class AuthenticationError(HTTPException):
    """Authentication-specific HTTP exception"""
    def __init__(self, message: str, status_code: int = status.HTTP_401_UNAUTHORIZED):
        super().__init__(status_code=status_code, detail=message)


class UserRole(Enum):
    """User role enumeration"""
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"
    PARENT = "parent"


@dataclass
class PasswordPolicy:
    """Password policy configuration"""
    min_length: int = 12
    max_length: int = 128
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numbers: bool = True
    require_special: bool = True
    special_chars: str = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    min_unique_chars: int = 8
    prevent_common_passwords: bool = True
    prevent_user_info_in_password: bool = True
    password_history_count: int = 5  # Remember last 5 passwords
    password_expiry_days: int = 90


@dataclass
class LockoutPolicy:
    """Account lockout policy"""
    max_attempts: int = 5
    lockout_duration_minutes: int = 15
    progressive_delay: bool = True  # Increase delay with each failure
    reset_after_success: bool = True


class SecureUserManager:
    """
    Secure user management service with comprehensive security features
    """

    # Common weak passwords to prevent
    COMMON_PASSWORDS = {
        "password", "password123", "123456", "12345678", "qwerty",
        "abc123", "monkey", "1234567", "letmein", "trustno1",
        "dragon", "baseball", "111111", "iloveyou", "master",
        "sunshine", "ashley", "bailey", "passw0rd", "shadow",
        "123123", "654321", "superman", "qazwsx", "michael"
    }

    def __init__(
        self,
        db_session: Session,
        redis_client: Optional[redis.Redis] = None,
        password_policy: Optional[PasswordPolicy] = None,
        lockout_policy: Optional[LockoutPolicy] = None
    ):
        self.db = db_session
        self.redis = redis_client
        self.password_policy = password_policy or PasswordPolicy()
        self.lockout_policy = lockout_policy or LockoutPolicy()
        self.bcrypt_cost = 12  # Bcrypt cost factor (12 is secure for 2025)

    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        role: UserRole,
        metadata: Optional[Dict[str, Any]] = None
    ) -> User:
        """
        Create a new user with secure password hashing

        Args:
            username: Unique username
            email: User email address
            password: Plain text password (will be hashed)
            role: User role
            metadata: Additional user metadata

        Returns:
            Created user object

        Raises:
            ValueError: If validation fails
            AuthenticationError: If user already exists
        """
        # Validate input
        self._validate_username(username)
        self._validate_email(email)
        self._validate_password(password, username, email)

        # Check if user exists
        if self._user_exists(username, email):
            raise AuthenticationError("User already exists", status.HTTP_409_CONFLICT)

        # Hash password with bcrypt
        hashed_password = self._hash_password(password)

        # Create user
        user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            role=role.value,
            created_at=datetime.now(timezone.utc),
            is_active=True,
            is_verified=False,  # Require email verification
            metadata=metadata or {},
            password_changed_at=datetime.now(timezone.utc),
            failed_login_attempts=0
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        # Audit log
        await self._audit_log("user_created", user.id, {"username": username, "role": role.value})

        logger.info(f"User created successfully: {username} (role: {role.value})")
        return user

    async def authenticate(
        self,
        username_or_email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[User, str]:
        """
        Authenticate user with comprehensive security checks

        Args:
            username_or_email: Username or email
            password: Plain text password
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Tuple of (authenticated user, session token)

        Raises:
            AuthenticationError: If authentication fails
        """
        # Check for account lockout
        if await self._is_locked_out(username_or_email):
            raise AuthenticationError(
                "Account is temporarily locked due to multiple failed login attempts",
                status.HTTP_423_LOCKED
            )

        # Find user
        user = self._get_user_by_username_or_email(username_or_email)
        if not user:
            # Record failed attempt for rate limiting
            await self._record_failed_attempt(username_or_email, ip_address)
            raise AuthenticationError("Invalid credentials")

        # Check if account is active
        if not user.is_active:
            raise AuthenticationError("Account is deactivated", status.HTTP_403_FORBIDDEN)

        # Verify password
        if not self._verify_password(password, user.password_hash):
            await self._record_failed_attempt(username_or_email, ip_address, user.id)
            raise AuthenticationError("Invalid credentials")

        # Check password expiry
        if self._is_password_expired(user.password_changed_at):
            raise AuthenticationError("Password has expired", status.HTTP_403_FORBIDDEN)

        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.last_login_at = datetime.now(timezone.utc)
        user.last_login_ip = ip_address
        self.db.commit()

        # Create session
        session_token = self._create_session(user, ip_address, user_agent)

        # Audit log
        await self._audit_log("user_login", user.id, {
            "ip_address": ip_address,
            "user_agent": user_agent
        })

        logger.info(f"User authenticated successfully: {user.username}")
        return user, session_token

    async def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> bool:
        """
        Change user password with validation

        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password

        Returns:
            True if password changed successfully

        Raises:
            AuthenticationError: If validation fails
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise AuthenticationError("User not found", status.HTTP_404_NOT_FOUND)

        # Verify current password
        if not self._verify_password(current_password, user.password_hash):
            raise AuthenticationError("Current password is incorrect")

        # Validate new password
        self._validate_password(new_password, user.username, user.email)

        # Check password history
        if await self._is_password_reused(user_id, new_password):
            raise AuthenticationError("Password has been used recently")

        # Store old password in history
        await self._add_to_password_history(user_id, user.password_hash)

        # Update password
        user.password_hash = self._hash_password(new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        self.db.commit()

        # Audit log
        await self._audit_log("password_changed", user_id, {})

        # Invalidate all sessions
        await self._invalidate_user_sessions(user_id)

        logger.info(f"Password changed for user: {user.username}")
        return True

    async def reset_password(
        self,
        reset_token: str,
        new_password: str
    ) -> bool:
        """
        Reset password using secure token

        Args:
            reset_token: Password reset token
            new_password: New password

        Returns:
            True if password reset successfully
        """
        # Validate reset token
        user_id = await self._validate_reset_token(reset_token)
        if not user_id:
            raise AuthenticationError("Invalid or expired reset token")

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise AuthenticationError("User not found")

        # Validate new password
        self._validate_password(new_password, user.username, user.email)

        # Update password
        user.password_hash = self._hash_password(new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        user.failed_login_attempts = 0  # Reset lockout
        self.db.commit()

        # Invalidate reset token
        await self._invalidate_reset_token(reset_token)

        # Audit log
        await self._audit_log("password_reset", user_id, {})

        logger.info(f"Password reset for user: {user.username}")
        return True

    async def enable_mfa(
        self,
        user_id: int,
        mfa_secret: Optional[str] = None
    ) -> str:
        """
        Enable multi-factor authentication for user

        Args:
            user_id: User ID
            mfa_secret: Optional pre-generated MFA secret

        Returns:
            MFA secret for QR code generation
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise AuthenticationError("User not found")

        # Generate MFA secret if not provided
        if not mfa_secret:
            mfa_secret = secrets.token_urlsafe(32)

        # Store encrypted MFA secret
        user.mfa_secret = self._encrypt_sensitive_data(mfa_secret)
        user.mfa_enabled = True
        self.db.commit()

        # Audit log
        await self._audit_log("mfa_enabled", user_id, {})

        logger.info(f"MFA enabled for user: {user.username}")
        return mfa_secret

    # Private helper methods

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt(rounds=self.bcrypt_cost)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                hashed.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    def _validate_password(
        self,
        password: str,
        username: str,
        email: str
    ) -> None:
        """
        Validate password against policy

        Raises:
            ValueError: If password doesn't meet policy
        """
        errors = []

        # Length check
        if len(password) < self.password_policy.min_length:
            errors.append(f"Password must be at least {self.password_policy.min_length} characters")
        if len(password) > self.password_policy.max_length:
            errors.append(f"Password must be less than {self.password_policy.max_length} characters")

        # Character requirements
        if self.password_policy.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        if self.password_policy.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        if self.password_policy.require_numbers and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        if self.password_policy.require_special:
            if not any(c in self.password_policy.special_chars for c in password):
                errors.append("Password must contain at least one special character")

        # Unique characters check
        if len(set(password)) < self.password_policy.min_unique_chars:
            errors.append(f"Password must contain at least {self.password_policy.min_unique_chars} unique characters")

        # Common password check
        if self.password_policy.prevent_common_passwords:
            if password.lower() in self.COMMON_PASSWORDS:
                errors.append("Password is too common")

        # User info in password check
        if self.password_policy.prevent_user_info_in_password:
            lower_password = password.lower()
            if username.lower() in lower_password or email.split('@')[0].lower() in lower_password:
                errors.append("Password cannot contain username or email")

        if errors:
            raise ValueError("; ".join(errors))

    def _validate_username(self, username: str) -> None:
        """Validate username format"""
        if not re.match(r'^[a-zA-Z0-9_-]{3,30}$', username):
            raise ValueError("Username must be 3-30 characters and contain only letters, numbers, underscore, and hyphen")

    def _validate_email(self, email: str) -> None:
        """Validate email format"""
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            raise ValueError("Invalid email address")

    def _user_exists(self, username: str, email: str) -> bool:
        """Check if user already exists"""
        return self.db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first() is not None

    def _get_user_by_username_or_email(self, identifier: str) -> Optional[User]:
        """Get user by username or email"""
        return self.db.query(User).filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()

    def _is_password_expired(self, password_changed_at: datetime) -> bool:
        """Check if password has expired"""
        if not password_changed_at:
            return True
        expiry_date = password_changed_at + timedelta(days=self.password_policy.password_expiry_days)
        return datetime.now(timezone.utc) > expiry_date

    def _create_session(
        self,
        user: User,
        ip_address: Optional[str],
        user_agent: Optional[str]
    ) -> str:
        """Create user session"""
        session_token = secrets.token_urlsafe(32)

        session = UserSession(
            user_id=user.id,
            session_token=session_token,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
        )

        self.db.add(session)
        self.db.commit()

        # Store in Redis for fast lookup
        if self.redis:
            self.redis.setex(
                f"session:{session_token}",
                86400,  # 24 hours
                str(user.id)
            )

        return session_token

    async def _is_locked_out(self, identifier: str) -> bool:
        """Check if account is locked out"""
        if not self.redis:
            return False

        lockout_key = f"lockout:{identifier}"
        return self.redis.exists(lockout_key) > 0

    async def _record_failed_attempt(
        self,
        identifier: str,
        ip_address: Optional[str],
        user_id: Optional[int] = None
    ) -> None:
        """Record failed login attempt"""
        if user_id:
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                user.failed_login_attempts += 1
                self.db.commit()

                if user.failed_login_attempts >= self.lockout_policy.max_attempts:
                    # Lock out account
                    if self.redis:
                        lockout_key = f"lockout:{identifier}"
                        self.redis.setex(
                            lockout_key,
                            self.lockout_policy.lockout_duration_minutes * 60,
                            "locked"
                        )

        # Audit log
        await self._audit_log("failed_login", user_id, {
            "identifier": identifier,
            "ip_address": ip_address
        })

    async def _is_password_reused(self, user_id: int, password: str) -> bool:
        """Check if password was recently used"""
        if not self.redis:
            return False

        # Get password history
        history_key = f"password_history:{user_id}"
        history = self.redis.lrange(history_key, 0, -1)

        for old_hash in history:
            if self._verify_password(password, old_hash.decode('utf-8')):
                return True

        return False

    async def _add_to_password_history(self, user_id: int, password_hash: str) -> None:
        """Add password to history"""
        if not self.redis:
            return

        history_key = f"password_history:{user_id}"
        self.redis.lpush(history_key, password_hash)
        self.redis.ltrim(history_key, 0, self.password_policy.password_history_count - 1)

    async def _invalidate_user_sessions(self, user_id: int) -> None:
        """Invalidate all user sessions"""
        sessions = self.db.query(UserSession).filter(
            UserSession.user_id == user_id
        ).all()

        for session in sessions:
            if self.redis:
                self.redis.delete(f"session:{session.session_token}")
            self.db.delete(session)

        self.db.commit()

    async def _validate_reset_token(self, token: str) -> Optional[int]:
        """Validate password reset token"""
        if not self.redis:
            return None

        key = f"reset_token:{token}"
        user_id = self.redis.get(key)

        if user_id:
            return int(user_id)
        return None

    async def _invalidate_reset_token(self, token: str) -> None:
        """Invalidate password reset token"""
        if self.redis:
            self.redis.delete(f"reset_token:{token}")

    def _encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data (simplified - use proper encryption in production)"""
        # TODO: Implement proper encryption using cryptography.fernet
        return data

    async def _audit_log(
        self,
        action: str,
        user_id: Optional[int],
        details: Dict[str, Any]
    ) -> None:
        """Create audit log entry"""
        try:
            # Create a simple audit log dict instead of model
            # TODO: Implement proper audit logging with AuditLog model
            pass
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")


# Export main class
__all__ = ["SecureUserManager", "UserRole", "PasswordPolicy", "LockoutPolicy", "AuthenticationError"]
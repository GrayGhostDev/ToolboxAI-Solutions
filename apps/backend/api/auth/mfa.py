"""
Multi-Factor Authentication (MFA) System
Phase 3 Implementation - Complete MFA with TOTP, SMS, and Email support
"""

import pyotp
import qrcode
import io
import base64
import secrets
import hashlib
import json
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import redis
from twilio.rest import Client
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger(__name__)

class MFAMethod(Enum):
    """Supported MFA methods"""
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"
    BACKUP_CODE = "backup"

@dataclass
class MFAConfig:
    """MFA System Configuration"""
    issuer_name: str = "ToolBoxAI"
    totp_digits: int = 6
    totp_interval: int = 30
    backup_codes_count: int = 10
    sms_enabled: bool = True
    email_enabled: bool = True
    totp_enabled: bool = True
    remember_device_days: int = 30
    max_attempts: int = 5
    lockout_duration: int = 900  # 15 minutes
    code_expiry_sms: int = 300  # 5 minutes
    code_expiry_email: int = 600  # 10 minutes

class MFARateLimitError(Exception):
    """Raised when rate limit is exceeded"""
    pass

class MFAService:
    """Complete Multi-Factor Authentication Service"""

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        config: Optional[MFAConfig] = None
    ):
        self.redis = redis_client or self._create_redis_client()
        self.config = config or MFAConfig()
        self._init_twilio()
        self._init_email()

    def _create_redis_client(self) -> redis.Redis:
        """Create Redis client with defaults"""
        return redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            db=int(os.getenv('REDIS_DB', '0')),
            decode_responses=True
        )

    def _init_twilio(self):
        """Initialize Twilio client for SMS"""
        try:
            self.twilio_client = Client(
                os.getenv('TWILIO_ACCOUNT_SID'),
                os.getenv('TWILIO_AUTH_TOKEN')
            )
            self.twilio_from = os.getenv('TWILIO_PHONE_NUMBER')
            self.sms_available = bool(self.twilio_client and self.twilio_from)
        except Exception as e:
            logger.warning(f"Twilio initialization failed: {e}")
            self.sms_available = False

    def _init_email(self):
        """Initialize email configuration"""
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_pass = os.getenv('SMTP_PASS')
        self.email_available = bool(self.smtp_user and self.smtp_pass)

    # ===== TOTP Implementation =====

    def generate_totp_secret(self, user_id: str) -> str:
        """Generate and store TOTP secret for user"""
        secret = pyotp.random_base32()

        # Store encrypted secret (in production, use proper encryption)
        key = f"mfa:totp_secret:{user_id}"
        self.redis.set(key, secret)

        return secret

    def generate_qr_code(self, user_email: str, secret: str) -> str:
        """Generate QR code for TOTP setup"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name=self.config.issuer_name
        )

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(totp_uri)
        qr.make(fit=True)

        # Convert to base64 image
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')

        return base64.b64encode(buffer.getvalue()).decode()

    def verify_totp(
        self,
        user_id: str,
        token: str,
        window: int = 1
    ) -> bool:
        """Verify TOTP token"""
        # Check rate limiting
        if self._is_rate_limited(user_id):
            raise MFARateLimitError("Too many attempts. Please try again later.")

        # Get stored secret
        key = f"mfa:totp_secret:{user_id}"
        secret = self.redis.get(key)

        if not secret:
            self._track_attempt(user_id, False)
            return False

        # Verify token
        totp = pyotp.TOTP(secret)
        is_valid = totp.verify(token, valid_window=window)

        # Track attempt
        self._track_attempt(user_id, is_valid)

        return is_valid

    # ===== SMS Implementation =====

    async def send_sms_code(
        self,
        user_id: str,
        phone_number: str
    ) -> bool:
        """Send SMS verification code"""
        if not self.config.sms_enabled or not self.sms_available:
            logger.warning("SMS sending not available")
            return False

        # Generate 6-digit code
        code = str(secrets.randbelow(999999)).zfill(6)

        # Store code with expiration
        key = f"mfa:code:sms:{user_id}"
        self.redis.setex(key, self.config.code_expiry_sms, code)

        # Send SMS via Twilio
        try:
            message = self.twilio_client.messages.create(
                body=f"Your ToolBoxAI verification code: {code}\n\nThis code expires in 5 minutes.",
                from_=self.twilio_from,
                to=phone_number
            )

            logger.info(f"SMS sent to {phone_number[-4:]} for user {user_id}")
            return bool(message.sid)

        except Exception as e:
            logger.error(f"SMS send failed: {e}")
            return False

    # ===== Email Implementation =====

    async def send_email_code(
        self,
        user_id: str,
        email: str
    ) -> bool:
        """Send email verification code"""
        if not self.config.email_enabled or not self.email_available:
            logger.warning("Email sending not available")
            return False

        # Generate code
        code = str(secrets.randbelow(999999)).zfill(6)

        # Store code
        key = f"mfa:code:email:{user_id}"
        self.redis.setex(key, self.config.code_expiry_email, code)

        # Send email
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = email
            msg['Subject'] = 'ToolBoxAI Security Code'

            body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        .container {{ padding: 20px; font-family: Arial, sans-serif; }}
        .code {{ font-size: 32px; font-weight: bold; color: #2c3e50; padding: 20px; background: #ecf0f1; border-radius: 8px; text-align: center; }}
        .footer {{ margin-top: 20px; color: #7f8c8d; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Your Verification Code</h2>
        <div class="code">{code}</div>
        <p>This code will expire in 10 minutes.</p>
        <p>If you didn't request this code, please ignore this email and ensure your account is secure.</p>
        <div class="footer">
            <p>This is an automated message from ToolBoxAI. Please do not reply.</p>
        </div>
    </div>
</body>
</html>
"""
            msg.attach(MIMEText(body, 'html'))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)

            logger.info(f"Email sent to {email} for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return False

    def verify_code(
        self,
        user_id: str,
        code: str,
        method: MFAMethod
    ) -> bool:
        """Verify SMS/Email code"""
        # Check rate limiting
        if self._is_rate_limited(user_id):
            raise MFARateLimitError("Too many attempts")

        # Get stored code
        key = f"mfa:code:{method.value}:{user_id}"
        stored_code = self.redis.get(key)

        if not stored_code:
            self._track_attempt(user_id, False)
            return False

        # Verify code (constant time comparison)
        is_valid = secrets.compare_digest(stored_code, code)

        # Track attempt
        self._track_attempt(user_id, is_valid)

        if is_valid:
            # Clear code after successful verification
            self.redis.delete(key)

        return is_valid

    # ===== Backup Codes =====

    def generate_backup_codes(self, user_id: str) -> List[str]:
        """Generate backup codes for user"""
        codes = []
        hashed_codes = []

        for _ in range(self.config.backup_codes_count):
            # Generate 8-character alphanumeric code
            code = ''.join(
                secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
                for _ in range(8)
            )
            codes.append(code)

            # Hash for storage
            hashed = hashlib.sha256(code.encode()).hexdigest()
            hashed_codes.append(hashed)

        # Store hashed codes
        key = f"mfa:backup_codes:{user_id}"
        self.redis.set(key, json.dumps(hashed_codes))

        return codes

    def verify_backup_code(
        self,
        user_id: str,
        code: str
    ) -> bool:
        """Verify and consume backup code"""
        # Get stored codes
        key = f"mfa:backup_codes:{user_id}"
        stored_json = self.redis.get(key)

        if not stored_json:
            return False

        stored_codes = json.loads(stored_json)
        code_hash = hashlib.sha256(code.encode()).hexdigest()

        # Check if code exists
        if code_hash in stored_codes:
            # Remove used code
            stored_codes.remove(code_hash)
            self.redis.set(key, json.dumps(stored_codes))

            logger.info(f"Backup code used for user {user_id}")
            return True

        return False

    # ===== Device Trust =====

    def trust_device(
        self,
        user_id: str,
        device_id: str
    ) -> str:
        """Generate device trust token"""
        token = secrets.token_urlsafe(32)

        # Store trusted device
        key = f"mfa:trusted_device:{user_id}:{device_id}"
        self.redis.setex(
            key,
            timedelta(days=self.config.remember_device_days).total_seconds(),
            token
        )

        return token

    def is_device_trusted(
        self,
        user_id: str,
        device_id: str,
        token: str
    ) -> bool:
        """Check if device is trusted"""
        key = f"mfa:trusted_device:{user_id}:{device_id}"
        stored_token = self.redis.get(key)

        if not stored_token:
            return False

        return secrets.compare_digest(stored_token, token)

    # ===== Rate Limiting =====

    def _is_rate_limited(self, user_id: str) -> bool:
        """Check if user is rate limited"""
        key = f"mfa:attempts:{user_id}"
        attempts = int(self.redis.get(key) or 0)

        return attempts >= self.config.max_attempts

    def _track_attempt(self, user_id: str, success: bool):
        """Track verification attempt"""
        key = f"mfa:attempts:{user_id}"

        if success:
            # Reset on success
            self.redis.delete(key)
        else:
            # Increment and set expiry
            pipe = self.redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, self.config.lockout_duration)
            pipe.execute()

    # ===== User Management =====

    def enable_mfa(
        self,
        user_id: str,
        method: MFAMethod,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Enable MFA method for user"""
        key = f"mfa:enabled:{user_id}"
        current = self.redis.get(key)

        if current:
            methods = json.loads(current)
        else:
            methods = {}

        methods[method.value] = {
            "enabled": True,
            "enabled_at": datetime.utcnow().isoformat(),
            "data": data or {}
        }

        self.redis.set(key, json.dumps(methods))

        logger.info(f"MFA method {method.value} enabled for user {user_id}")
        return True

    def disable_mfa(
        self,
        user_id: str,
        method: Optional[MFAMethod] = None
    ) -> bool:
        """Disable MFA method(s) for user"""
        if method:
            # Disable specific method
            key = f"mfa:enabled:{user_id}"
            current = self.redis.get(key)

            if current:
                methods = json.loads(current)
                if method.value in methods:
                    del methods[method.value]
                    self.redis.set(key, json.dumps(methods))
        else:
            # Disable all MFA
            keys = [
                f"mfa:enabled:{user_id}",
                f"mfa:totp_secret:{user_id}",
                f"mfa:backup_codes:{user_id}"
            ]
            for key in keys:
                self.redis.delete(key)

        logger.info(f"MFA disabled for user {user_id}")
        return True

    def get_user_mfa_status(self, user_id: str) -> Dict[str, Any]:
        """Get user's MFA status"""
        key = f"mfa:enabled:{user_id}"
        current = self.redis.get(key)

        if not current:
            return {
                "mfa_enabled": False,
                "methods": {}
            }

        methods = json.loads(current)

        # Check backup codes count
        backup_key = f"mfa:backup_codes:{user_id}"
        backup_json = self.redis.get(backup_key)
        backup_count = len(json.loads(backup_json)) if backup_json else 0

        return {
            "mfa_enabled": True,
            "methods": methods,
            "backup_codes_remaining": backup_count
        }

    def require_mfa_setup(self, user_id: str) -> bool:
        """Check if user needs to set up MFA"""
        status = self.get_user_mfa_status(user_id)
        return not status["mfa_enabled"]

# ===== Feature Flags =====

class MFAFeatureFlags:
    """Feature flags for gradual MFA rollout"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client or redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            db=int(os.getenv('REDIS_DB', '0')),
            decode_responses=True
        )

    def is_mfa_enabled_for_user(self, user_id: str) -> bool:
        """Check if MFA is enabled for specific user"""
        # Check user-specific flag
        user_key = f"feature:mfa:user:{user_id}"
        if self.redis.get(user_key):
            return True

        # Check role-based enablement
        role_key = f"feature:mfa:role:{self._get_user_role(user_id)}"
        if self.redis.get(role_key):
            return True

        # Check percentage rollout
        rollout_percentage = int(self.redis.get("feature:mfa:rollout_percentage") or 0)

        if rollout_percentage >= 100:
            return True
        elif rollout_percentage <= 0:
            return False

        # Use consistent hashing for gradual rollout
        user_hash = int(hashlib.md5(user_id.encode()).hexdigest()[:8], 16)
        return (user_hash % 100) < rollout_percentage

    def set_mfa_rollout_percentage(self, percentage: int):
        """Set MFA rollout percentage (0-100)"""
        percentage = max(0, min(100, percentage))
        self.redis.set("feature:mfa:rollout_percentage", percentage)
        logger.info(f"MFA rollout set to {percentage}%")

    def enable_mfa_for_role(self, role: str):
        """Enable MFA for specific role"""
        key = f"feature:mfa:role:{role}"
        self.redis.set(key, "1")
        logger.info(f"MFA enabled for role: {role}")

    def enable_mfa_for_user(self, user_id: str):
        """Enable MFA for specific user"""
        key = f"feature:mfa:user:{user_id}"
        self.redis.set(key, "1")
        logger.info(f"MFA enabled for user: {user_id}")

    def _get_user_role(self, user_id: str) -> str:
        """Get user role (mock implementation)"""
        # In production, fetch from database
        return "student"

# ===== Singleton Instances =====

_mfa_service: Optional[MFAService] = None
_feature_flags: Optional[MFAFeatureFlags] = None

def get_mfa_service() -> MFAService:
    """Get or create MFA service singleton"""
    global _mfa_service
    if _mfa_service is None:
        _mfa_service = MFAService()
    return _mfa_service

def get_mfa_feature_flags() -> MFAFeatureFlags:
    """Get or create feature flags singleton"""
    global _feature_flags
    if _feature_flags is None:
        _feature_flags = MFAFeatureFlags()
    return _feature_flags
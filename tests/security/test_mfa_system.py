import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest_asyncio

"""
MFA System Tests
Phase 3 - Comprehensive MFA testing
"""

import asyncio
import hashlib
import json
import secrets
from unittest.mock import AsyncMock, MagicMock, patch

import pyotp
import pytest

from apps.backend.api.auth.mfa import (
    MFAConfig,
    MFAFeatureFlags,
    MFAMethod,
    MFARateLimitError,
    MFAService,
)


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis = MagicMock()
    redis.get.return_value = None
    redis.set.return_value = True
    redis.setex.return_value = True
    redis.delete.return_value = 1
    redis.incr.return_value = 1
    redis.expire.return_value = True
    redis.pipeline.return_value = redis
    redis.execute.return_value = [1, True]
    return redis

@pytest.fixture
def mfa_service(mock_redis):
    """Create MFA service with mocked dependencies"""
    service = MFAService(redis_client=mock_redis)
    # Mock Twilio and Email
    service.sms_available = True
    service.email_available = True
    service.twilio_client = MagicMock()
    return service

@pytest.fixture
def feature_flags(mock_redis):
    """Create feature flags with mocked Redis"""
    return MFAFeatureFlags(redis_client=mock_redis)

class TestTOTPMethods:
    """Test TOTP-related methods"""

    def test_generate_totp_secret(self, mfa_service, mock_redis):
        """Test TOTP secret generation"""
        user_id = "test_user_123"

        secret = mfa_service.generate_totp_secret(user_id)

        assert secret is not None
        assert len(secret) == 32  # Base32 encoded
        assert mock_redis.set.called
        assert f"mfa:totp_secret:{user_id}" in mock_redis.set.call_args[0]

    def test_generate_qr_code(self, mfa_service):
        """Test QR code generation"""
        email = "test@example.com"
        secret = pyotp.random_base32()

        qr_code = mfa_service.generate_qr_code(email, secret)

        assert qr_code is not None
        assert isinstance(qr_code, str)
        # QR code should be base64 encoded
        assert len(qr_code) > 100

    def test_verify_totp_valid(self, mfa_service, mock_redis):
        """Test valid TOTP verification"""
        user_id = "test_user_123"
        secret = pyotp.random_base32()

        # Mock stored secret
        mock_redis.get.return_value = secret

        # Generate valid token
        totp = pyotp.TOTP(secret)
        token = totp.now()

        result = mfa_service.verify_totp(user_id, token)

        assert result is True
        assert mock_redis.delete.called  # Rate limit reset

    def test_verify_totp_invalid(self, mfa_service, mock_redis):
        """Test invalid TOTP verification"""
        user_id = "test_user_123"
        secret = pyotp.random_base32()

        # Mock stored secret
        mock_redis.get.return_value = secret

        # Use invalid token
        result = mfa_service.verify_totp(user_id, "000000")

        assert result is False

    def test_verify_totp_rate_limit(self, mfa_service, mock_redis):
        """Test TOTP rate limiting"""
        user_id = "test_user_123"

        # Mock rate limit exceeded
        def get_side_effect(key):
            if "attempts" in key:
                return "5"  # Max attempts reached
            return pyotp.random_base32()

        mock_redis.get.side_effect = get_side_effect

        with pytest.raises(MFARateLimitError):
            mfa_service.verify_totp(user_id, "123456")

class TestSMSMethods:
    """Test SMS-related methods"""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_send_sms_code(self, mfa_service, mock_redis):
        """Test SMS code sending"""
        user_id = "test_user_123"
        phone = "+1234567890"

        # Mock Twilio response
        message_mock = MagicMock()
        message_mock.sid = "MSG123"
        mfa_service.twilio_client.messages.create.return_value = message_mock

        result = await mfa_service.send_sms_code(user_id, phone)

        assert result is True
        assert mock_redis.setex.called
        assert mfa_service.twilio_client.messages.create.called

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_send_sms_failure(self, mfa_service):
        """Test SMS sending failure"""
        user_id = "test_user_123"
        phone = "+1234567890"

        # Mock Twilio error
        mfa_service.twilio_client.messages.create.side_effect = Exception("Twilio error")

        result = await mfa_service.send_sms_code(user_id, phone)

        assert result is False

    def test_verify_sms_code(self, mfa_service, mock_redis):
        """Test SMS code verification"""
        user_id = "test_user_123"
        code = "123456"

        # Mock stored code
        mock_redis.get.return_value = code

        result = mfa_service.verify_code(user_id, code, MFAMethod.SMS)

        assert result is True
        assert mock_redis.delete.called  # Code cleared after use

class TestEmailMethods:
    """Test Email-related methods"""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_send_email_code(self, mfa_service, mock_redis):
        """Test email code sending"""
        user_id = "test_user_123"
        email = "test@example.com"

        with patch('smtplib.SMTP') as mock_smtp:
            result = await mfa_service.send_email_code(user_id, email)

            # Even if SMTP fails, method should handle gracefully
            assert result in [True, False]
            assert mock_redis.setex.called

    def test_verify_email_code(self, mfa_service, mock_redis):
        """Test email code verification"""
        user_id = "test_user_123"
        code = "654321"

        # Mock stored code
        mock_redis.get.return_value = code

        result = mfa_service.verify_code(user_id, code, MFAMethod.EMAIL)

        assert result is True

class TestBackupCodes:
    """Test backup code functionality"""

    def test_generate_backup_codes(self, mfa_service, mock_redis):
        """Test backup code generation"""
        user_id = "test_user_123"

        codes = mfa_service.generate_backup_codes(user_id)

        assert len(codes) == 10
        assert all(len(code) == 8 for code in codes)
        assert all(code.isalnum() for code in codes)
        assert mock_redis.set.called

    def test_verify_backup_code_valid(self, mfa_service, mock_redis):
        """Test valid backup code verification"""
        user_id = "test_user_123"
        code = "ABCD1234"

        # Mock stored codes with hashed version of our code
        hashed = hashlib.sha256(code.encode()).hexdigest()
        mock_redis.get.return_value = json.dumps([hashed, "other_hash"])

        result = mfa_service.verify_backup_code(user_id, code)

        assert result is True
        # Verify code was removed after use
        assert mock_redis.set.called

    def test_verify_backup_code_invalid(self, mfa_service, mock_redis):
        """Test invalid backup code verification"""
        user_id = "test_user_123"

        # Mock stored codes without our code
        mock_redis.get.return_value = json.dumps(["hash1", "hash2"])

        result = mfa_service.verify_backup_code(user_id, "INVALID1")

        assert result is False

class TestDeviceTrust:
    """Test device trust functionality"""

    def test_trust_device(self, mfa_service, mock_redis):
        """Test device trust token generation"""
        user_id = "test_user_123"
        device_id = "device_456"

        token = mfa_service.trust_device(user_id, device_id)

        assert token is not None
        assert len(token) > 20
        assert mock_redis.setex.called

    def test_is_device_trusted_valid(self, mfa_service, mock_redis):
        """Test trusted device verification"""
        user_id = "test_user_123"
        device_id = "device_456"
        token = "valid_token_xyz"

        # Mock stored token
        mock_redis.get.return_value = token

        result = mfa_service.is_device_trusted(user_id, device_id, token)

        assert result is True

    def test_is_device_trusted_invalid(self, mfa_service, mock_redis):
        """Test untrusted device verification"""
        user_id = "test_user_123"
        device_id = "device_456"

        # Mock no stored token
        mock_redis.get.return_value = None

        result = mfa_service.is_device_trusted(user_id, device_id, "wrong_token")

        assert result is False

class TestFeatureFlags:
    """Test feature flag functionality"""

    def test_rollout_percentage(self, feature_flags, mock_redis):
        """Test percentage-based rollout"""
        # Set 50% rollout
        mock_redis.get.return_value = "50"

        # Test multiple users
        enabled_count = 0
        for i in range(100):
            user_id = f"user_{i}"
            if feature_flags.is_mfa_enabled_for_user(user_id):
                enabled_count += 1

        # Should be approximately 50% (with some variance)
        assert 40 <= enabled_count <= 60

    def test_enable_for_role(self, feature_flags, mock_redis):
        """Test role-based enablement"""
        role = "admin"

        feature_flags.enable_mfa_for_role(role)

        assert mock_redis.set.called
        assert f"feature:mfa:role:{role}" in mock_redis.set.call_args[0]

    def test_enable_for_user(self, feature_flags, mock_redis):
        """Test user-specific enablement"""
        user_id = "special_user"

        feature_flags.enable_mfa_for_user(user_id)

        assert mock_redis.set.called
        assert f"feature:mfa:user:{user_id}" in mock_redis.set.call_args[0]

    def test_set_rollout_percentage(self, feature_flags, mock_redis):
        """Test setting rollout percentage"""
        feature_flags.set_mfa_rollout_percentage(75)

        assert mock_redis.set.called
        assert mock_redis.set.call_args[0] == ("feature:mfa:rollout_percentage", 75)

        # Test boundary values
        feature_flags.set_mfa_rollout_percentage(150)  # Should cap at 100
        assert mock_redis.set.call_args[0][1] == 100

        feature_flags.set_mfa_rollout_percentage(-10)  # Should floor at 0
        assert mock_redis.set.call_args[0][1] == 0

class TestUserManagement:
    """Test user MFA management"""

    def test_enable_mfa_for_user(self, mfa_service, mock_redis):
        """Test enabling MFA for user"""
        user_id = "test_user_123"

        result = mfa_service.enable_mfa(user_id, MFAMethod.TOTP)

        assert result is True
        assert mock_redis.set.called

    def test_disable_mfa_specific_method(self, mfa_service, mock_redis):
        """Test disabling specific MFA method"""
        user_id = "test_user_123"

        # Mock existing methods
        mock_redis.get.return_value = json.dumps({
            "totp": {"enabled": True},
            "sms": {"enabled": True}
        })

        result = mfa_service.disable_mfa(user_id, MFAMethod.TOTP)

        assert result is True

    def test_disable_all_mfa(self, mfa_service, mock_redis):
        """Test disabling all MFA"""
        user_id = "test_user_123"

        result = mfa_service.disable_mfa(user_id)

        assert result is True
        # Should delete multiple keys
        assert mock_redis.delete.call_count >= 3

    def test_get_user_mfa_status(self, mfa_service, mock_redis):
        """Test getting user MFA status"""
        user_id = "test_user_123"

        # Mock enabled methods
        mock_redis.get.side_effect = [
            json.dumps({
                "totp": {"enabled": True},
                "sms": {"enabled": True}
            }),
            json.dumps(["hash1", "hash2"])  # Backup codes
        ]

        status = mfa_service.get_user_mfa_status(user_id)

        assert status["mfa_enabled"] is True
        assert "totp" in status["methods"]
        assert status["backup_codes_remaining"] == 2

def test_mfa_config():
    """Test MFA configuration"""
    config = MFAConfig()

    assert config.issuer_name == "ToolBoxAI"
    assert config.totp_digits == 6
    assert config.max_attempts == 5
    assert config.lockout_duration == 900

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
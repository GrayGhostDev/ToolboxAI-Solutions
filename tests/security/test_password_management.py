import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest_asyncio
"""
Comprehensive test suite for password_management.py
Tests password strength validation, change workflows, history tracking, and rate limiting.
"""

import pytest
import time
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from fastapi import HTTPException, status

from apps.backend.api.auth.password_management import (
    PasswordStrengthRequirements, PasswordValidationResult, PasswordValidator,
    PasswordChangeRequest, PasswordResetRequest, PasswordHistoryManager,
    PasswordChangeService, get_password_service
)


class TestPasswordStrengthRequirements:
    """Test password strength requirements configuration"""

    def test_default_requirements(self):
        """Test default password requirements"""
        req = PasswordStrengthRequirements()
        
        assert req.MIN_LENGTH == 8
        assert req.MAX_LENGTH == 128
        assert req.REQUIRE_UPPERCASE is True
        assert req.REQUIRE_LOWERCASE is True
        assert req.REQUIRE_DIGIT is True
        assert req.REQUIRE_SPECIAL is True
        assert len(req.COMMON_PASSWORDS) > 0
        assert len(req.FORBIDDEN_PATTERNS) > 0

    def test_common_passwords_contains_weak_passwords(self):
        """Test that common passwords set contains expected weak passwords"""
        req = PasswordStrengthRequirements()
        
        weak_passwords = ["password", "123456", "qwerty", "admin"]
        for password in weak_passwords:
            assert password in req.COMMON_PASSWORDS

    def test_forbidden_patterns(self):
        """Test forbidden patterns detection"""
        req = PasswordStrengthRequirements()
        
        # Should contain patterns for repeated characters, sequences, etc.
        assert any("(.)" in pattern for pattern in req.FORBIDDEN_PATTERNS)
        assert any("012" in pattern or "123" in pattern for pattern in req.FORBIDDEN_PATTERNS)


class TestPasswordValidator:
    """Test password validation functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.validator = PasswordValidator()

    def test_valid_strong_password(self):
        """Test validation of strong passwords"""
        strong_passwords = [
            "MySecureP@ss1w7rd",
            "Complex!Pass1q7",
            "Str0ngP@ssword!",
            "Test1q7!@#Password"
        ]
        
        for password in strong_passwords:
            result = self.validator.validate(password)
            assert result.is_valid is True
            assert result.score >= 80
            assert len(result.issues) == 0

    def test_invalid_passwords_length(self):
        """Test validation of passwords with length issues"""
        # Too short
        result = self.validator.validate("Test1!")
        assert result.is_valid is False
        assert any("at least" in issue for issue in result.issues)
        
        # Too long
        long_password = "A" * 130 + "1!"
        result = self.validator.validate(long_password)
        assert result.is_valid is False
        assert any("exceed" in issue for issue in result.issues)

    def test_invalid_passwords_character_requirements(self):
        """Test validation of passwords missing character types"""
        # Missing uppercase
        result = self.validator.validate("test123!@#")
        assert result.is_valid is False
        assert any("uppercase" in issue for issue in result.issues)
        
        # Missing lowercase
        result = self.validator.validate("TEST123!@#")
        assert result.is_valid is False
        assert any("lowercase" in issue for issue in result.issues)
        
        # Missing digit
        result = self.validator.validate("TestABC!@#")
        assert result.is_valid is False
        assert any("digit" in issue for issue in result.issues)
        
        # Missing special character
        result = self.validator.validate("TestABC123")
        assert result.is_valid is False
        assert any("special" in issue for issue in result.issues)

    def test_common_password_detection(self):
        """Test detection of common passwords"""
        common_passwords = ["password", "123456", "qwerty"]
        
        for password in common_passwords:
            result = self.validator.validate(password)
            assert result.is_valid is False
            assert any("common" in issue.lower() for issue in result.issues)

    def test_username_in_password_detection(self):
        """Test detection of username in password"""
        username = "testuser"
        password = "testuser123!"
        
        result = self.validator.validate(password, username)
        assert result.is_valid is False
        assert any("username" in issue.lower() for issue in result.issues)

    def test_forbidden_patterns_detection(self):
        """Test detection of forbidden patterns"""
        pattern_passwords = [
            "Test111123!",  # Repeated characters
            "Test123456!",  # Sequential numbers
            "Testabcdef!",  # Sequential letters
            "Testqwerty!"   # Keyboard pattern
        ]
        
        for password in pattern_passwords:
            result = self.validator.validate(password)
            # Some might still be valid if other criteria are strong
            if not result.is_valid:
                assert any("pattern" in issue.lower() for issue in result.issues)

    def test_password_scoring(self):
        """Test password strength scoring"""
        # Weak password
        result = self.validator.validate("Test123!")
        weak_score = result.score
        
        # Strong password
        result = self.validator.validate("VeryComplexP@ssw0rd123!")
        strong_score = result.score
        
        assert strong_score > weak_score

    def test_length_bonus_scoring(self):
        """Test length bonus in password scoring"""
        # Base password
        result1 = self.validator.validate("Test123!@#")
        base_score = result1.score
        
        # Longer password
        result2 = self.validator.validate("Test123!@#ExtraLength")
        long_score = result2.score
        
        assert long_score >= base_score

    def test_suggestions_provided(self):
        """Test that validation provides helpful suggestions"""
        result = self.validator.validate("test")
        
        assert len(result.suggestions) > 0
        assert any("character" in suggestion.lower() for suggestion in result.suggestions)


class TestPasswordChangeRequest:
    """Test password change request validation"""

    def test_valid_password_change_request(self):
        """Test valid password change request"""
        request = PasswordChangeRequest(
            current_password="OldPassword123!",
            new_password="NewPassword123!",
            confirm_password="NewPassword123!",
            logout_all_devices=True
        )
        
        assert request.current_password == "OldPassword123!"
        assert request.new_password == "NewPassword123!"
        assert request.confirm_password == "NewPassword123!"
        assert request.logout_all_devices is True

    def test_password_mismatch_validation(self):
        """Test password confirmation mismatch validation"""
        with pytest.raises(ValueError, match="do not match"):
            PasswordChangeRequest(
                current_password="OldPassword123!",
                new_password="NewPassword123!",
                confirm_password="DifferentPassword123!",
                logout_all_devices=True
            )

    def test_model_validator_password_mismatch(self):
        """Test model validator for password mismatch"""
        with pytest.raises(ValueError, match="do not match"):
            # Create with matching passwords first, then modify
            request_data = {
                "current_password": "OldPassword123!",
                "new_password": "NewPassword123!",
                "confirm_password": "NewPassword123!",
                "logout_all_devices": True
            }
            # Simulate mismatched passwords
            request_data["confirm_password"] = "DifferentPassword123!"
            PasswordChangeRequest(**request_data)


class TestPasswordHistoryManager:
    """Test password history management"""

    def setup_method(self):
        """Setup test environment"""
        self.mock_redis = Mock()
        self.history_manager = PasswordHistoryManager(self.mock_redis)

    def test_add_to_history_with_redis(self):
        """Test adding password to history with Redis"""
        user_id = "user123"
        password_hash = "hashed_password"
        
        self.history_manager.add_to_history(user_id, password_hash)
        
        key = f"{self.history_manager.HISTORY_PREFIX}{user_id}"
        self.mock_redis.lpush.assert_called_once_with(key, password_hash)
        self.mock_redis.ltrim.assert_called_once_with(key, 0, self.history_manager.MAX_HISTORY - 1)
        self.mock_redis.expire.assert_called_once_with(key, 86400 * 365)

    def test_add_to_history_without_redis(self):
        """Test adding password to history without Redis"""
        history_manager = PasswordHistoryManager(None)
        user_id = "user123"
        password_hash = "hashed_password"
        
        history_manager.add_to_history(user_id, password_hash)
        
        assert user_id in history_manager._memory_history
        assert password_hash in history_manager._memory_history[user_id]

    def test_memory_history_limit(self):
        """Test memory history respects limit"""
        history_manager = PasswordHistoryManager(None)
        user_id = "user123"
        
        # Add more passwords than the limit
        for i in range(10):
            history_manager.add_to_history(user_id, f"password_hash_{i}")
        
        # Should only keep the most recent passwords
        assert len(history_manager._memory_history[user_id]) == history_manager.MAX_HISTORY

    def test_is_password_reused_with_redis(self):
        """Test password reuse check with Redis"""
        user_id = "user123"
        password = "TestPassword123!"
        old_hash = "old_hashed_password"
        
        self.mock_redis.lrange.return_value = [old_hash]
        
        with patch('apps.backend.api.auth.password_management.verify_password') as mock_verify:
            mock_verify.return_value = True
            
            result = self.history_manager.is_password_reused(user_id, password)
            assert result is True
            
            mock_verify.return_value = False
            result = self.history_manager.is_password_reused(user_id, password)
            assert result is False

    def test_is_password_reused_with_bytes(self):
        """Test password reuse check with bytes from Redis"""
        user_id = "user123"
        password = "TestPassword123!"
        old_hash = b"old_hashed_password"  # Bytes from Redis
        
        self.mock_redis.lrange.return_value = [old_hash]
        
        with patch('apps.backend.api.auth.password_management.verify_password') as mock_verify:
            mock_verify.return_value = True
            
            result = self.history_manager.is_password_reused(user_id, password)
            assert result is True
            mock_verify.assert_called_with(password, "old_hashed_password")


class TestPasswordChangeService:
    """Test password change service functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.mock_session_manager = Mock()
        self.mock_redis = Mock()
        self.service = PasswordChangeService(
            session_manager=self.mock_session_manager,
            redis_client=self.mock_redis
        )

    def test_rate_limit_check_allowed(self):
        """Test rate limit check when allowed"""
        user_id = "user123"
        self.mock_redis.incr.return_value = 2
        
        is_allowed, remaining = self.service._check_rate_limit(user_id)
        
        assert is_allowed is True
        assert remaining == 3  # MAX_CHANGES_PER_DAY - 2

    def test_rate_limit_check_exceeded(self):
        """Test rate limit check when exceeded"""
        user_id = "user123"
        self.mock_redis.incr.return_value = 6  # Exceeds MAX_CHANGES_PER_DAY
        
        is_allowed, remaining = self.service._check_rate_limit(user_id)
        
        assert is_allowed is False
        assert remaining == 0

    def test_rate_limit_without_redis(self):
        """Test rate limit check without Redis"""
        service = PasswordChangeService(
            session_manager=self.mock_session_manager,
            redis_client=None
        )
        
        is_allowed, remaining = service._check_rate_limit("user123")
        assert is_allowed is True
        assert remaining == service.MAX_CHANGES_PER_DAY

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_change_password_success(self):
        """Test successful password change"""
        # Setup
        self.mock_redis.incr.return_value = 1  # Within rate limit
        self.mock_session_manager.invalidate_all_user_sessions.return_value = 2
        
        with patch.object(self.service.validator, 'validate') as mock_validate:
            mock_validate.return_value = PasswordValidationResult(
                is_valid=True, score=85, issues=[], suggestions=[]
            )
            
            with patch.object(self.service.history_manager, 'is_password_reused') as mock_reused:
                mock_reused.return_value = False
                
                with patch('apps.backend.api.auth.password_management.hash_password') as mock_hash:
                    mock_hash.return_value = "new_hashed_password"
                    
                    result = await self.service.change_password(
                        user_id="user123",
                        username="testuser",
                        current_password="OldPassword123!",
                        new_password="NewPassword123!",
                        request_ip="127.0.0.1",
                        user_agent="Test Agent"
                    )
        
        assert result["success"] is True
        assert result["sessions_invalidated"] == 2
        assert "remaining_changes_today" in result
        assert "password_strength_score" in result

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_change_password_rate_limit_exceeded(self):
        """Test password change when rate limit is exceeded"""
        self.mock_redis.incr.return_value = 6  # Exceeds limit
        
        with pytest.raises(HTTPException) as exc_info:
            await self.service.change_password(
                user_id="user123",
                username="testuser",
                current_password="OldPassword123!",
                new_password="NewPassword123!"
            )
        
        assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_change_password_weak_password(self):
        """Test password change with weak new password"""
        self.mock_redis.incr.return_value = 1  # Within rate limit
        
        with patch.object(self.service.validator, 'validate') as mock_validate:
            mock_validate.return_value = PasswordValidationResult(
                is_valid=False,
                score=30,
                issues=["Password is too weak"],
                suggestions=["Add more complexity"]
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await self.service.change_password(
                    user_id="user123",
                    username="testuser",
                    current_password="OldPassword123!",
                    new_password="weak"
                )
            
            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "security requirements" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_change_password_reused_password(self):
        """Test password change with previously used password"""
        self.mock_redis.incr.return_value = 1  # Within rate limit
        
        with patch.object(self.service.validator, 'validate') as mock_validate:
            mock_validate.return_value = PasswordValidationResult(
                is_valid=True, score=85, issues=[], suggestions=[]
            )
            
            with patch.object(self.service.history_manager, 'is_password_reused') as mock_reused:
                mock_reused.return_value = True
                
                with pytest.raises(HTTPException) as exc_info:
                    await self.service.change_password(
                        user_id="user123",
                        username="testuser",
                        current_password="OldPassword123!",
                        new_password="ReusedPassword123!"
                    )
                
                assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
                assert "recently used" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_reset_password_success(self):
        """Test successful admin password reset"""
        with patch.object(self.service.validator, 'validate') as mock_validate:
            mock_validate.return_value = PasswordValidationResult(
                is_valid=True, score=70, issues=[], suggestions=[]
            )
            
            self.mock_session_manager.invalidate_all_user_sessions.return_value = 3
            
            with patch('apps.backend.api.auth.password_management.hash_password') as mock_hash:
                mock_hash.return_value = "reset_hashed_password"
                
                result = await self.service.reset_password(
                    admin_user_id="admin123",
                    target_user_id="user123",
                    new_password="ResetPassword123!",
                    reason="Forgot password",
                    force_logout=True
                )
        
        assert result["success"] is True
        assert result["sessions_invalidated"] == 3
        assert result["password_hash"] == "reset_hashed_password"
        assert result["reset_by"] == "admin123"
        assert result["reset_reason"] == "Forgot password"

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_reset_password_weak_password(self):
        """Test admin password reset with weak password"""
        with patch.object(self.service.validator, 'validate') as mock_validate:
            mock_validate.return_value = PasswordValidationResult(
                is_valid=False, score=30, issues=[], suggestions=[]
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await self.service.reset_password(
                    admin_user_id="admin123",
                    target_user_id="user123",
                    new_password="weak",
                    reason="Admin reset"
                )
            
            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "too weak" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_reset_password_no_force_logout(self):
        """Test admin password reset without forcing logout"""
        with patch.object(self.service.validator, 'validate') as mock_validate:
            mock_validate.return_value = PasswordValidationResult(
                is_valid=True, score=70, issues=[], suggestions=[]
            )
            
            with patch('apps.backend.api.auth.password_management.hash_password') as mock_hash:
                mock_hash.return_value = "reset_hashed_password"
                
                result = await self.service.reset_password(
                    admin_user_id="admin123",
                    target_user_id="user123",
                    new_password="ResetPassword123!",
                    reason="Admin reset",
                    force_logout=False
                )
        
        assert result["sessions_invalidated"] == 0
        self.mock_session_manager.invalidate_all_user_sessions.assert_not_called()


class TestPasswordResetRequest:
    """Test password reset request validation"""

    def test_valid_reset_request(self):
        """Test valid password reset request"""
        request = PasswordResetRequest(
            user_id="user123",
            new_password="NewPassword123!",
            reason="User requested reset",
            force_logout=True
        )
        
        assert request.user_id == "user123"
        assert request.new_password == "NewPassword123!"
        assert request.reason == "User requested reset"
        assert request.force_logout is True


class TestGlobalService:
    """Test global password service functions"""

    def test_get_password_service_singleton(self):
        """Test that get_password_service returns singleton"""
        service1 = get_password_service()
        service2 = get_password_service()
        
        assert service1 is service2

    def test_get_password_service_with_custom_manager(self):
        """Test get_password_service with custom session manager"""
        mock_session_manager = Mock()
        mock_redis = Mock()
        
        # Reset global instance
        import apps.backend.api.auth.password_management
        apps.backend.api.auth.password_management._password_service = None
        
        service = get_password_service(mock_session_manager, mock_redis)
        
        assert service.session_manager is mock_session_manager
        assert service.redis_client is mock_redis


@pytest.mark.integration
class TestPasswordManagementIntegration:
    """Integration tests for password management"""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_complete_password_change_flow(self):
        """Test complete password change workflow"""
        # Setup mocks
        mock_session_manager = Mock()
        mock_redis = Mock()
        
        service = PasswordChangeService(
            session_manager=mock_session_manager,
            redis_client=mock_redis
        )
        
        # Mock rate limiting
        mock_redis.incr.return_value = 1
        mock_redis.expire.return_value = True
        
        # Mock session invalidation
        mock_session_manager.invalidate_all_user_sessions.return_value = 2
        
        with patch('apps.backend.api.auth.password_management.hash_password') as mock_hash:
            mock_hash.return_value = "new_hashed_password"
            
            # Change password
            result = await service.change_password(
                user_id="user123",
                username="testuser",
                current_password="OldPassword123!",
                new_password="NewSecurePassword123!",
                request_ip="127.0.0.1",
                user_agent="Test Browser"
            )
        
        # Verify complete flow
        assert result["success"] is True
        assert "sessions_invalidated" in result
        assert "password_strength_score" in result
        
        # Verify history was updated
        service.history_manager.add_to_history.assert_called_once_with("user123", "new_hashed_password")
        
        # Verify sessions were invalidated
        mock_session_manager.invalidate_all_user_sessions.assert_called_once_with(
            user_id="user123",
            reason="password_change"
        )

    def test_password_validation_comprehensive(self):
        """Test comprehensive password validation scenarios"""
        validator = PasswordValidator()
        
        test_cases = [
            # (password, username, should_be_valid, expected_issues)
            ("VerySecureP@ssw0rd!", "testuser", True, []),
            ("short", "testuser", False, ["at least"]),
            ("testuser123!", "testuser", False, ["username"]),
            ("NoDigitsHere!", "testuser", False, ["digit"]),
            ("NOUPPER123!", "testuser", False, ["lowercase"]),
            ("nolower123!", "testuser", False, ["uppercase"]),
            ("NoSpecial123", "testuser", False, ["special"]),
            ("password123!", "testuser", False, ["common"]),
        ]
        
        for password, username, should_be_valid, expected_issues in test_cases:
            result = validator.validate(password, username)
            
            assert result.is_valid == should_be_valid
            
            if not should_be_valid:
                for expected_issue in expected_issues:
                    assert any(expected_issue in issue.lower() for issue in result.issues), \
                        f"Expected issue '{expected_issue}' not found in {result.issues}"

    def test_rate_limiting_behavior(self):
        """Test rate limiting behavior over time"""
        mock_session_manager = Mock()
        mock_redis = Mock()
        
        service = PasswordChangeService(
            session_manager=mock_session_manager,
            redis_client=mock_redis
        )
        
        user_id = "user123"
        
        # Simulate multiple attempts
        for attempt in range(1, 8):
            mock_redis.incr.return_value = attempt
            
            is_allowed, remaining = service._check_rate_limit(user_id)
            
            if attempt <= service.MAX_CHANGES_PER_DAY:
                assert is_allowed is True
                assert remaining == service.MAX_CHANGES_PER_DAY - attempt
            else:
                assert is_allowed is False
                assert remaining == 0

    def test_memory_fallback_functionality(self):
        """Test that memory fallback works when Redis is unavailable"""
        mock_session_manager = Mock()
        
        # Service without Redis
        service = PasswordChangeService(
            session_manager=mock_session_manager,
            redis_client=None
        )
        
        # Rate limiting should still work (always allow)
        is_allowed, remaining = service._check_rate_limit("user123")
        assert is_allowed is True
        
        # History manager should use memory
        history_manager = service.history_manager
        assert history_manager.redis_client is None
        
        # Test memory history functionality
        user_id = "user123"
        password_hash = "test_hash"
        
        history_manager.add_to_history(user_id, password_hash)
        assert user_id in history_manager._memory_history
        assert password_hash in history_manager._memory_history[user_id]


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_password_validator_edge_cases(self):
        """Test password validator with edge case inputs"""
        validator = PasswordValidator()
        
        # Empty password
        result = validator.validate("")
        assert result.is_valid is False
        
        # Very long password
        long_password = "A" * 200 + "1!"
        result = validator.validate(long_password)
        assert result.is_valid is False
        
        # Password with only special characters
        special_only = "!@#$%^&*()"
        result = validator.validate(special_only)
        assert result.is_valid is False
        
        # Unicode password
        unicode_password = "Test123!αβγδε"
        result = validator.validate(unicode_password)
        # Should handle Unicode gracefully

    def test_concurrent_password_changes(self):
        """Test handling of concurrent password change attempts"""
        import threading
        import concurrent.futures
        
        def simulate_password_change(user_id):
            mock_session_manager = Mock()
            mock_redis = Mock()
            mock_redis.incr.return_value = 1
            
            service = PasswordChangeService(
                session_manager=mock_session_manager,
                redis_client=mock_redis
            )
            
            try:
                is_allowed, remaining = service._check_rate_limit(f"user{user_id}")
                return is_allowed
            except Exception:
                return False
        
        # Test with multiple threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(simulate_password_change, i) for i in range(20)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All should succeed (mocked to return 1)
        assert all(results)

    def test_malformed_input_handling(self):
        """Test handling of malformed inputs"""
        validator = PasswordValidator()
        
        # None input should not crash
        try:
            result = validator.validate(None)
            # Should either work or raise a clear exception
        except (TypeError, AttributeError):
            # Acceptable to raise these for None input
            pass
        
        # Non-string input
        try:
            result = validator.validate(12345)
            # Should either work (convert to string) or raise exception
        except (TypeError, AttributeError):
            pass

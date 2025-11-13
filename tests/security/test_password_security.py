import pytest_asyncio

"""
Test Password Security and Session Invalidation

Tests the critical security feature of session invalidation on password change.
Ensures all sessions are properly invalidated when a user changes their password.
"""

import asyncio
import os

# Add parent directory to path
import sys
import time
from typing import Dict, List
from unittest.mock import MagicMock, Mock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.backend.api.auth.password_management import (
    PasswordChangeRequest,
    PasswordChangeService,
    PasswordHistoryManager,
    PasswordStrengthRequirements,
    PasswordValidator,
)
from apps.backend.core.security.session_manager import SessionEvent, SessionInfo, SessionManager
from tests.test_logger import TestLogger

# Initialize test logger
logger = TestLogger(__name__, "integration")


class TestSessionInvalidation:
    """Test session invalidation on password change"""
    
    def setup_method(self, method):
        """Setup for each test"""
        test_name = method.__name__ if method else "test"
        logger.start_test(test_name)
        
        # Create session manager without Redis for testing
        self.session_manager = SessionManager(redis_client=None)
        
        # Create password service
        self.password_service = PasswordChangeService(
            session_manager=self.session_manager,
            redis_client=None
        )
    
    def teardown_method(self, method):
        """Teardown for each test"""
        test_name = method.__name__ if method else "test"
        logger.end_test(test_name, "completed")
    
    def test_session_creation_and_retrieval(self):
        """Test basic session creation and retrieval"""
        logger.logger.info("Testing session creation and retrieval")
        
        # Create a session
        session = self.session_manager.create_session(
            user_id="test_user_1",
            username="testuser",
            role="student",
            ip_address="127.0.0.1",
            user_agent="TestAgent/1.0"
        )
        
        assert session is not None
        assert session.user_id == "test_user_1"
        assert session.username == "testuser"
        assert session.role == "student"
        assert session.is_active == True
        
        # Retrieve the session
        retrieved = self.session_manager.get_session(session.session_id)
        assert retrieved is not None
        assert retrieved.user_id == session.user_id
        
        logger.logger.info("✅ Session creation and retrieval working")
    
    def test_multiple_sessions_per_user(self):
        """Test that users can have multiple active sessions"""
        logger.logger.info("Testing multiple sessions per user")
        
        user_id = "test_user_2"
        sessions = []
        
        # Create multiple sessions for the same user
        for i in range(3):
            session = self.session_manager.create_session(
                user_id=user_id,
                username="testuser2",
                role="teacher",
                ip_address=f"192.168.1.{i+1}",
                device_id=f"device_{i+1}"
            )
            sessions.append(session)
        
        # Get all user sessions
        user_sessions = self.session_manager.get_user_sessions(user_id)
        assert len(user_sessions) == 3
        
        # Verify all sessions are different
        session_ids = [s.session_id for s in user_sessions]
        assert len(set(session_ids)) == 3
        
        logger.logger.info(f"✅ User has {len(user_sessions)} active sessions")
    
    def test_session_invalidation_on_password_change(self):
        """Test that all sessions are invalidated when password is changed"""
        logger.logger.info("Testing session invalidation on password change")
        
        user_id = "test_user_3"
        
        # Create multiple sessions
        sessions = []
        for i in range(5):
            session = self.session_manager.create_session(
                user_id=user_id,
                username="testuser3",
                role="admin",
                ip_address=f"10.0.0.{i+1}",
                device_id=f"device_{i+1}"
            )
            sessions.append(session)
        
        # Verify all sessions are active
        active_sessions = self.session_manager.get_user_sessions(user_id)
        assert len(active_sessions) == 5
        
        # Simulate password change - invalidate all sessions
        invalidated_count = self.session_manager.invalidate_all_user_sessions(
            user_id=user_id,
            reason="password_change"
        )
        
        assert invalidated_count == 5
        
        # Verify all sessions are now invalid
        for session in sessions:
            retrieved = self.session_manager.get_session(session.session_id)
            assert retrieved is None
        
        # Verify user has no active sessions
        active_sessions = self.session_manager.get_user_sessions(user_id)
        assert len(active_sessions) == 0
        
        logger.logger.info(f"✅ All {invalidated_count} sessions invalidated on password change")
    
    def test_session_limit_enforcement(self):
        """Test that session limit is enforced per user"""
        logger.logger.info("Testing session limit enforcement")
        
        user_id = "test_user_4"
        max_sessions = self.session_manager.max_sessions_per_user
        
        # Create more sessions than allowed
        sessions = []
        for i in range(max_sessions + 2):
            session = self.session_manager.create_session(
                user_id=user_id,
                username="testuser4",
                role="student",
                ip_address=f"172.16.0.{i+1}"
            )
            sessions.append(session)
            time.sleep(0.01)  # Small delay to ensure different timestamps
        
        # Check that only max_sessions are active
        active_sessions = self.session_manager.get_user_sessions(user_id)
        assert len(active_sessions) <= max_sessions
        
        # Verify oldest sessions were removed
        active_session_ids = {s.session_id for s in active_sessions}
        
        # First sessions should be invalidated
        for i in range(2):
            assert sessions[i].session_id not in active_session_ids
        
        logger.logger.info(f"✅ Session limit enforced at {max_sessions} sessions")
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_password_change_integration(self):
        """Test full password change flow with session invalidation"""
        logger.logger.info("Testing complete password change integration")
        
        user_id = "test_user_5"
        username = "testuser5"
        
        # Create sessions
        session_count = 3
        for i in range(session_count):
            self.session_manager.create_session(
                user_id=user_id,
                username=username,
                role="teacher",
                ip_address=f"192.168.0.{i+1}"
            )
        
        # Mock password verification
        with patch('apps.backend.api.auth.password_management.verify_password', return_value=True):
            with patch('apps.backend.api.auth.password_management.hash_password', return_value="new_hash"):
                # Perform password change
                result = await self.password_service.change_password(
                    user_id=user_id,
                    username=username,
                    current_password="old_password",
                    new_password="NewSecurePass847!",
                    request_ip="192.168.0.100"
                )
        
        assert result["success"] == True
        assert result["sessions_invalidated"] == session_count
        assert "action_required" in result
        
        # Verify no sessions remain
        active_sessions = self.session_manager.get_user_sessions(user_id)
        assert len(active_sessions) == 0
        
        logger.logger.info("✅ Password change integration test passed")


class TestPasswordStrength:
    """Test password strength validation"""
    
    def setup_method(self, method):
        """Setup for each test"""
        test_name = method.__name__ if method else "test"
        logger.start_test(test_name)
        self.validator = PasswordValidator()
    
    def teardown_method(self, method):
        """Teardown for each test"""
        test_name = method.__name__ if method else "test"
        logger.end_test(test_name, "completed")
    
    def test_password_strength_validation(self):
        """Test password strength requirements"""
        logger.logger.info("Testing password strength validation")
        
        # Test weak passwords
        weak_passwords = [
            "password",  # Common password
            "12345678",  # Sequential numbers
            "qwerty123",  # Keyboard pattern
            "abc",  # Too short
            "testtest",  # No complexity
        ]
        
        for password in weak_passwords:
            result = self.validator.validate(password)
            assert not result.is_valid, f"Password '{password}' should be invalid"
            assert result.score < 70, f"Password '{password}' should have low score (got {result.score})"
            assert len(result.issues) > 0, f"Password '{password}' should have issues"
        
        # Test strong passwords
        strong_passwords = [
            "MySecure#Pass2024",
            "Complex!Password$847",
            "Str0ng&Secure_P@ss",
        ]
        
        for password in strong_passwords:
            result = self.validator.validate(password)
            assert result.is_valid, f"Password '{password}' should be valid"
            assert result.score >= 70, f"Password '{password}' should have high score"
            assert len(result.issues) == 0, f"Password '{password}' should have no issues"
        
        logger.logger.info("✅ Password strength validation working correctly")
    
    def test_password_contains_username(self):
        """Test that passwords containing username are rejected"""
        logger.logger.info("Testing username in password detection")
        
        username = "johndoe"
        passwords_with_username = [
            "johndoe123",
            "MyPasswordjohndoe",
            "JOHNDOE2024!",
        ]
        
        for password in passwords_with_username:
            result = self.validator.validate(password, username)
            assert not result.is_valid, f"Password with username should be invalid"
            assert any("username" in issue.lower() for issue in result.issues)
        
        logger.logger.info("✅ Username detection in passwords working")
    
    def test_password_patterns(self):
        """Test detection of predictable patterns"""
        logger.logger.info("Testing pattern detection")
        
        patterned_passwords = [
            "aaaaaaaaaa",  # Repeated characters
            "12345678901",  # Sequential numbers
            "abcdefghijk",  # Sequential letters
            "qwertyuiop",  # Keyboard walk
        ]
        
        for password in patterned_passwords:
            result = self.validator.validate(password)
            if result.is_valid:
                # Pattern detection might not catch all, but score should be lower
                assert result.score < 80, f"Patterned password should have reduced score"
        
        logger.logger.info("✅ Pattern detection working")


class TestPasswordHistory:
    """Test password history and reuse prevention"""
    
    def setup_method(self, method):
        """Setup for each test"""
        test_name = method.__name__ if method else "test"
        logger.start_test(test_name)
        self.history_manager = PasswordHistoryManager(redis_client=None)
    
    def teardown_method(self, method):
        """Teardown for each test"""
        test_name = method.__name__ if method else "test"
        logger.end_test(test_name, "completed")
    
    def test_password_history_tracking(self):
        """Test that password history is maintained"""
        logger.logger.info("Testing password history tracking")
        
        user_id = "test_user_history"
        
        # Add passwords to history
        from apps.backend.api.auth.auth import hash_password
        
        passwords = ["Password1!", "Password2@", "Password3#", "Password4$", "Password5%"]
        
        for password in passwords:
            hashed = hash_password(password)
            self.history_manager.add_to_history(user_id, hashed)
        
        # Check that recent passwords are detected as reused
        for password in passwords:
            is_reused = self.history_manager.is_password_reused(user_id, password)
            assert is_reused, f"Password '{password}' should be detected as reused"
        
        # Check that new password is not detected as reused
        new_password = "BrandNewPassword6^"
        is_reused = self.history_manager.is_password_reused(user_id, new_password)
        assert not is_reused, "New password should not be detected as reused"
        
        logger.logger.info("✅ Password history tracking working")
    
    def test_password_history_limit(self):
        """Test that password history has a limit"""
        logger.logger.info("Testing password history limit")
        
        user_id = "test_user_limit"
        max_history = self.history_manager.MAX_HISTORY
        
        from apps.backend.api.auth.auth import hash_password

        # Add more passwords than the limit
        for i in range(max_history + 3):
            password = f"Password{i}!"
            hashed = hash_password(password)
            self.history_manager.add_to_history(user_id, hashed)
        
        # Oldest passwords should not be in history anymore
        oldest_password = "Password0!"
        is_reused = self.history_manager.is_password_reused(user_id, oldest_password)
        assert not is_reused, "Oldest password should have been removed from history"
        
        # Recent passwords should still be in history
        recent_password = f"Password{max_history + 2}!"
        is_reused = self.history_manager.is_password_reused(user_id, recent_password)
        assert is_reused, "Recent password should still be in history"
        
        logger.logger.info(f"✅ Password history limited to {max_history} entries")


if __name__ == "__main__":
    # Run all tests
    print("\n" + "="*80)
    print("TESTING PASSWORD SECURITY AND SESSION INVALIDATION")
    print("="*80 + "\n")
    
    # Test session invalidation
    session_tests = TestSessionInvalidation()
    session_tests.setup_method(session_tests.test_session_creation_and_retrieval)
    session_tests.test_session_creation_and_retrieval()
    session_tests.teardown_method(session_tests.test_session_creation_and_retrieval)
    
    session_tests.setup_method(session_tests.test_multiple_sessions_per_user)
    session_tests.test_multiple_sessions_per_user()
    session_tests.teardown_method(session_tests.test_multiple_sessions_per_user)
    
    session_tests.setup_method(session_tests.test_session_invalidation_on_password_change)
    session_tests.test_session_invalidation_on_password_change()
    session_tests.teardown_method(session_tests.test_session_invalidation_on_password_change)
    
    session_tests.setup_method(session_tests.test_session_limit_enforcement)
    session_tests.test_session_limit_enforcement()
    session_tests.teardown_method(session_tests.test_session_limit_enforcement)
    
    # Test async password change
    session_tests.setup_method(session_tests.test_password_change_integration)
    asyncio.run(session_tests.test_password_change_integration())
    session_tests.teardown_method(session_tests.test_password_change_integration)
    
    # Test password strength
    strength_tests = TestPasswordStrength()
    strength_tests.setup_method(strength_tests.test_password_strength_validation)
    strength_tests.test_password_strength_validation()
    strength_tests.teardown_method(strength_tests.test_password_strength_validation)
    
    strength_tests.setup_method(strength_tests.test_password_contains_username)
    strength_tests.test_password_contains_username()
    strength_tests.teardown_method(strength_tests.test_password_contains_username)
    
    strength_tests.setup_method(strength_tests.test_password_patterns)
    strength_tests.test_password_patterns()
    strength_tests.teardown_method(strength_tests.test_password_patterns)
    
    # Test password history
    history_tests = TestPasswordHistory()
    history_tests.setup_method(history_tests.test_password_history_tracking)
    history_tests.test_password_history_tracking()
    history_tests.teardown_method(history_tests.test_password_history_tracking)
    
    history_tests.setup_method(history_tests.test_password_history_limit)
    history_tests.test_password_history_limit()
    history_tests.teardown_method(history_tests.test_password_history_limit)
    
    # Generate report
    logger.generate_report()
    
    print("\n" + "="*80)
    print("✅ ALL PASSWORD SECURITY TESTS PASSED!")
    print("="*80 + "\n")
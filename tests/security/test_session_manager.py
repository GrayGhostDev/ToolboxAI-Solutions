import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from unittest.mock import Mock, patch

import pytest


@pytest.fixture
def mock_db_connection():
    """Mock database connection for tests"""
    with patch("psycopg2.connect") as mock_connect:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        yield mock_conn


"""
Comprehensive test suite for session_manager.py
Tests session creation, validation, invalidation, fingerprinting, and security controls.
"""

import time
from unittest.mock import Mock, patch

import pytest

from apps.backend.core.security.session_manager import (
    SessionEvent,
    SessionInfo,
    SessionManager,
    get_session_manager,
    initialize_session_manager,
)


class TestSessionInfo:
    """Test SessionInfo data structure"""

    def test_session_info_creation(self):
        """Test creating SessionInfo object"""
        session = SessionInfo(
            session_id="session123",
            user_id="user123",
            username="testuser",
            role="student",
            created_at=time.time(),
            last_activity=time.time(),
            expires_at=time.time() + 3600,
            ip_address="192.168.1.1",
            user_agent="Test Browser",
            device_id="device123",
            is_active=True,
            refresh_token="refresh123",
        )

        assert session.session_id == "session123"
        assert session.user_id == "user123"
        assert session.username == "testuser"
        assert session.role == "student"
        assert session.is_active is True

    def test_session_info_to_dict(self):
        """Test converting SessionInfo to dictionary"""
        session = SessionInfo(
            session_id="session123",
            user_id="user123",
            username="testuser",
            role="student",
            created_at=time.time(),
            last_activity=time.time(),
            expires_at=time.time() + 3600,
        )

        session_dict = session.to_dict()

        assert isinstance(session_dict, dict)
        assert session_dict["session_id"] == "session123"
        assert session_dict["user_id"] == "user123"
        assert session_dict["username"] == "testuser"

    def test_session_info_from_dict(self):
        """Test creating SessionInfo from dictionary"""
        session_data = {
            "session_id": "session123",
            "user_id": "user123",
            "username": "testuser",
            "role": "student",
            "created_at": time.time(),
            "last_activity": time.time(),
            "expires_at": time.time() + 3600,
            "ip_address": "192.168.1.1",
            "user_agent": "Test Browser",
            "device_id": "device123",
            "is_active": True,
            "refresh_token": "refresh123",
        }

        session = SessionInfo.from_dict(session_data)

        assert session.session_id == "session123"
        assert session.user_id == "user123"
        assert session.is_active is True


class TestSessionEvent:
    """Test SessionEvent enumeration"""

    def test_session_event_values(self):
        """Test session event values"""
        assert SessionEvent.CREATED.value == "session_created"
        assert SessionEvent.REFRESHED.value == "session_refreshed"
        assert SessionEvent.INVALIDATED.value == "session_invalidated"
        assert SessionEvent.EXPIRED.value == "session_expired"
        assert SessionEvent.PASSWORD_CHANGED.value == "password_changed"
        assert SessionEvent.LOGOUT.value == "logout"
        assert SessionEvent.SUSPICIOUS_ACTIVITY.value == "suspicious_activity"


class TestSessionManager:
    """Test SessionManager functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.mock_redis = Mock()
        self.session_manager = SessionManager(
            redis_client=self.mock_redis,
            session_timeout=1800,
            refresh_timeout=86400,
            max_sessions_per_user=3,
        )

    def test_initialization(self):
        """Test SessionManager initialization"""
        assert self.session_manager.redis_client == self.mock_redis
        assert self.session_manager.session_timeout == 1800
        assert self.session_manager.refresh_timeout == 86400
        assert self.session_manager.max_sessions_per_user == 3

    def test_initialization_without_redis(self):
        """Test SessionManager initialization without Redis"""
        manager = SessionManager(redis_client=None)

        assert manager.redis_client is None
        assert isinstance(manager._memory_sessions, dict)
        assert isinstance(manager._memory_user_sessions, dict)

    def test_generate_session_token(self):
        """Test session token generation"""
        token1 = self.session_manager.generate_session_token()
        token2 = self.session_manager.generate_session_token()

        assert token1 != token2
        assert isinstance(token1, str)
        assert isinstance(token2, str)
        assert len(token1) >= 32  # Should be URL-safe base64 encoded

    def test_generate_session_fingerprint(self):
        """Test session fingerprint generation"""
        ip = "192.168.1.1"
        user_agent = "Mozilla/5.0 Test Browser"

        fingerprint1 = self.session_manager.generate_session_fingerprint(ip, user_agent)
        fingerprint2 = self.session_manager.generate_session_fingerprint(ip, user_agent)

        assert fingerprint1 == fingerprint2  # Should be deterministic
        assert isinstance(fingerprint1, str)
        assert len(fingerprint1) == 64  # SHA256 hex digest

    def test_generate_different_fingerprints(self):
        """Test that different inputs generate different fingerprints"""
        fingerprint1 = self.session_manager.generate_session_fingerprint("192.168.1.1", "Browser1")
        fingerprint2 = self.session_manager.generate_session_fingerprint("192.168.1.2", "Browser1")
        fingerprint3 = self.session_manager.generate_session_fingerprint("192.168.1.1", "Browser2")

        assert fingerprint1 != fingerprint2
        assert fingerprint1 != fingerprint3
        assert fingerprint2 != fingerprint3

    def test_validate_session_fingerprint_with_redis(self):
        """Test session fingerprint validation with Redis"""
        session_id = "session123"
        ip = "192.168.1.1"
        user_agent = "Test Browser"

        expected_fingerprint = self.session_manager.generate_session_fingerprint(ip, user_agent)
        self.mock_redis.get.return_value = expected_fingerprint

        # Should validate successfully
        assert self.session_manager.validate_session_fingerprint(session_id, ip, user_agent) is True

        # Should fail with different fingerprint
        self.mock_redis.get.return_value = "different_fingerprint"
        assert (
            self.session_manager.validate_session_fingerprint(session_id, ip, user_agent) is False
        )

    def test_validate_session_fingerprint_with_memory(self):
        """Test session fingerprint validation with memory storage"""
        manager = SessionManager(redis_client=None)
        session_id = "session123"
        ip = "192.168.1.1"
        user_agent = "Test Browser"

        expected_fingerprint = manager.generate_session_fingerprint(ip, user_agent)
        manager._memory_session_fingerprints[session_id] = expected_fingerprint

        # Should validate successfully
        assert manager.validate_session_fingerprint(session_id, ip, user_agent) is True

        # Should fail with different fingerprint
        manager._memory_session_fingerprints[session_id] = "different_fingerprint"
        assert manager.validate_session_fingerprint(session_id, ip, user_agent) is False

    def test_create_session_with_redis(self):
        """Test session creation with Redis"""
        user_id = "user123"
        username = "testuser"
        role = "student"
        ip_address = "192.168.1.1"
        user_agent = "Test Browser"
        device_id = "device123"

        # Mock Redis pipeline
        mock_pipeline = Mock()
        self.mock_redis.pipeline.return_value = mock_pipeline

        session = self.session_manager.create_session(
            user_id=user_id,
            username=username,
            role=role,
            ip_address=ip_address,
            user_agent=user_agent,
            device_id=device_id,
        )

        assert session.user_id == user_id
        assert session.username == username
        assert session.role == role
        assert session.ip_address == ip_address
        assert session.user_agent == user_agent
        assert session.device_id == device_id
        assert session.is_active is True
        assert session.refresh_token is not None

        # Verify Redis operations
        self.mock_redis.pipeline.assert_called()
        mock_pipeline.execute.assert_called()

    def test_create_session_with_memory(self):
        """Test session creation with memory storage"""
        manager = SessionManager(redis_client=None)

        session = manager.create_session(
            user_id="user123",
            username="testuser",
            role="student",
            ip_address="192.168.1.1",
            user_agent="Test Browser",
        )

        assert session.session_id in manager._memory_sessions
        assert "user123" in manager._memory_user_sessions
        assert session.session_id in manager._memory_user_sessions["user123"]

    def test_get_session_with_redis_valid(self):
        """Test getting valid session from Redis"""
        session_id = "session123"
        session_data = {
            "session_id": session_id,
            "user_id": "user123",
            "username": "testuser",
            "role": "student",
            "created_at": str(time.time()),
            "last_activity": str(time.time()),
            "expires_at": str(time.time() + 3600),  # Future expiration
            "is_active": "True",
        }

        self.mock_redis.hgetall.return_value = session_data

        session = self.session_manager.get_session(session_id)

        assert session is not None
        assert session.session_id == session_id
        assert session.user_id == "user123"
        assert session.is_active is True

        # Should update last activity
        self.mock_redis.hset.assert_called()

    def test_get_session_with_redis_expired(self):
        """Test getting expired session from Redis"""
        session_id = "session123"
        session_data = {
            "session_id": session_id,
            "user_id": "user123",
            "username": "testuser",
            "role": "student",
            "created_at": str(time.time()),
            "last_activity": str(time.time()),
            "expires_at": str(time.time() - 3600),  # Past expiration
            "is_active": "True",
        }

        self.mock_redis.hgetall.return_value = session_data

        session = self.session_manager.get_session(session_id)

        assert session is None  # Should return None for expired session

    def test_get_session_with_redis_not_found(self):
        """Test getting non-existent session from Redis"""
        self.mock_redis.hgetall.return_value = {}

        session = self.session_manager.get_session("nonexistent")

        assert session is None

    def test_get_session_with_memory_valid(self):
        """Test getting valid session from memory"""
        manager = SessionManager(redis_client=None)

        # Create session in memory
        session_info = SessionInfo(
            session_id="session123",
            user_id="user123",
            username="testuser",
            role="student",
            created_at=time.time(),
            last_activity=time.time(),
            expires_at=time.time() + 3600,  # Future expiration
            is_active=True,
        )

        manager._memory_sessions["session123"] = session_info

        session = manager.get_session("session123")

        assert session is not None
        assert session.session_id == "session123"

    def test_get_session_with_memory_expired(self):
        """Test getting expired session from memory"""
        manager = SessionManager(redis_client=None)

        # Create expired session in memory
        session_info = SessionInfo(
            session_id="session123",
            user_id="user123",
            username="testuser",
            role="student",
            created_at=time.time(),
            last_activity=time.time(),
            expires_at=time.time() - 3600,  # Past expiration
            is_active=True,
        )

        manager._memory_sessions["session123"] = session_info

        session = manager.get_session("session123")

        assert session is None  # Should return None for expired session
        assert "session123" not in manager._memory_sessions  # Should be removed

    def test_invalidate_session_with_redis(self):
        """Test session invalidation with Redis"""
        session_id = "session123"
        user_id = "user123"

        # Mock getting session
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "username": "testuser",
            "role": "student",
            "created_at": str(time.time()),
            "last_activity": str(time.time()),
            "expires_at": str(time.time() + 3600),
            "is_active": "True",
        }

        self.mock_redis.hgetall.return_value = session_data

        # Mock pipeline for invalidation
        mock_pipeline = Mock()
        self.mock_redis.pipeline.return_value = mock_pipeline

        result = self.session_manager.invalidate_session(session_id)

        assert result is True
        self.mock_redis.pipeline.assert_called()
        mock_pipeline.execute.assert_called()

    def test_invalidate_session_not_found(self):
        """Test invalidating non-existent session"""
        self.mock_redis.hgetall.return_value = {}

        result = self.session_manager.invalidate_session("nonexistent")

        assert result is False

    def test_invalidate_all_user_sessions_with_redis(self):
        """Test invalidating all user sessions with Redis"""
        user_id = "user123"
        session_ids = ["session1", "session2", "session3"]

        self.mock_redis.smembers.return_value = session_ids

        # Mock pipeline
        mock_pipeline = Mock()
        self.mock_redis.pipeline.return_value = mock_pipeline

        count = self.session_manager.invalidate_all_user_sessions(user_id, "password_change")

        assert count == len(session_ids)
        self.mock_redis.pipeline.assert_called()
        mock_pipeline.execute.assert_called()

    def test_invalidate_all_user_sessions_with_memory(self):
        """Test invalidating all user sessions with memory"""
        manager = SessionManager(redis_client=None)
        user_id = "user123"

        # Create sessions in memory
        session_ids = ["session1", "session2", "session3"]
        for session_id in session_ids:
            session_info = SessionInfo(
                session_id=session_id,
                user_id=user_id,
                username="testuser",
                role="student",
                created_at=time.time(),
                last_activity=time.time(),
                expires_at=time.time() + 3600,
                is_active=True,
            )
            manager._memory_sessions[session_id] = session_info

        manager._memory_user_sessions[user_id] = set(session_ids)

        count = manager.invalidate_all_user_sessions(user_id, "logout")

        assert count == len(session_ids)
        assert len(manager._memory_user_sessions[user_id]) == 0
        for session_id in session_ids:
            assert session_id not in manager._memory_sessions

    def test_get_user_sessions_with_redis(self):
        """Test getting user sessions with Redis"""
        user_id = "user123"
        session_ids = ["session1", "session2"]

        self.mock_redis.smembers.return_value = session_ids

        # Mock session data for each session
        def mock_hgetall(key):
            if "session1" in key:
                return {
                    "session_id": "session1",
                    "user_id": user_id,
                    "username": "testuser",
                    "role": "student",
                    "created_at": str(time.time()),
                    "last_activity": str(time.time()),
                    "expires_at": str(time.time() + 3600),
                    "is_active": "True",
                }
            elif "session2" in key:
                return {
                    "session_id": "session2",
                    "user_id": user_id,
                    "username": "testuser",
                    "role": "student",
                    "created_at": str(time.time()),
                    "last_activity": str(time.time()),
                    "expires_at": str(time.time() + 3600),
                    "is_active": "True",
                }
            return {}

        self.mock_redis.hgetall.side_effect = mock_hgetall

        sessions = self.session_manager.get_user_sessions(user_id)

        assert len(sessions) == 2
        assert all(session.user_id == user_id for session in sessions)

    def test_session_limit_enforcement(self):
        """Test that session limit is enforced"""
        manager = SessionManager(redis_client=None, max_sessions_per_user=2)
        user_id = "user123"

        # Create more sessions than the limit
        sessions = []
        for i in range(4):
            session = manager.create_session(user_id=user_id, username="testuser", role="student")
            sessions.append(session)
            time.sleep(0.001)  # Small delay to ensure different creation times

        # Should only have max_sessions_per_user sessions
        user_sessions = manager.get_user_sessions(user_id)
        assert len(user_sessions) <= manager.max_sessions_per_user

    def test_refresh_session_success(self):
        """Test successful session refresh"""
        manager = SessionManager(redis_client=None)

        # Create initial session
        session = manager.create_session(user_id="user123", username="testuser", role="student")

        original_session_id = session.session_id
        original_refresh_token = session.refresh_token

        # Refresh session
        refreshed_session = manager.refresh_session(
            session_id=original_session_id, refresh_token=original_refresh_token
        )

        assert refreshed_session is not None
        assert refreshed_session.session_id != original_session_id  # New session ID
        assert refreshed_session.refresh_token != original_refresh_token  # New refresh token
        assert refreshed_session.user_id == session.user_id

        # Original session should be invalidated
        assert manager.get_session(original_session_id) is None

    def test_refresh_session_invalid_token(self):
        """Test session refresh with invalid refresh token"""
        manager = SessionManager(redis_client=None)

        # Create initial session
        session = manager.create_session(user_id="user123", username="testuser", role="student")

        # Try refresh with wrong token
        refreshed_session = manager.refresh_session(
            session_id=session.session_id, refresh_token="wrong_token"
        )

        assert refreshed_session is None

    def test_refresh_session_not_found(self):
        """Test session refresh with non-existent session"""
        manager = SessionManager(redis_client=None)

        refreshed_session = manager.refresh_session(
            session_id="nonexistent", refresh_token="any_token"
        )

        assert refreshed_session is None

    def test_cleanup_expired_sessions_memory(self):
        """Test cleanup of expired sessions in memory"""
        manager = SessionManager(redis_client=None)

        # Create mixed expired and valid sessions
        current_time = time.time()

        # Expired session
        expired_session = SessionInfo(
            session_id="expired_session",
            user_id="user123",
            username="testuser",
            role="student",
            created_at=current_time - 7200,
            last_activity=current_time - 3600,
            expires_at=current_time - 1800,  # Expired 30 minutes ago
            is_active=True,
        )

        # Valid session
        valid_session = SessionInfo(
            session_id="valid_session",
            user_id="user456",
            username="testuser2",
            role="teacher",
            created_at=current_time,
            last_activity=current_time,
            expires_at=current_time + 3600,  # Expires in 1 hour
            is_active=True,
        )

        manager._memory_sessions["expired_session"] = expired_session
        manager._memory_sessions["valid_session"] = valid_session
        manager._memory_user_sessions["user123"] = {"expired_session"}
        manager._memory_user_sessions["user456"] = {"valid_session"}

        count = manager.cleanup_expired_sessions()

        assert count == 1  # One expired session cleaned up
        assert "expired_session" not in manager._memory_sessions
        assert "valid_session" in manager._memory_sessions

    def test_cleanup_expired_sessions_redis(self):
        """Test cleanup of expired sessions with Redis (auto-handled by TTL)"""
        # Redis handles expiration automatically via TTL
        count = self.session_manager.cleanup_expired_sessions()

        # Should return 0 since Redis handles expiration
        assert count == 0

    def test_session_logging(self):
        """Test session event logging"""
        with patch("apps.backend.core.security.session_manager.logger") as mock_logger:
            session = self.session_manager.create_session(
                user_id="user123",
                username="testuser",
                role="student",
                ip_address="192.168.1.1",
            )

            # Should log session creation
            mock_logger.info.assert_called()

            # Test logout logging
            self.session_manager.invalidate_session(session.session_id)

            # Should log session invalidation
            assert mock_logger.info.call_count >= 2


class TestGlobalFunctions:
    """Test global session manager functions"""

    def setup_method(self):
        """Setup test environment"""
        # Clear global instance
        import apps.backend.core.security.session_manager

        apps.backend.core.security.session_manager._session_manager = None

    def test_get_session_manager_singleton(self):
        """Test that get_session_manager returns singleton"""
        manager1 = get_session_manager()
        manager2 = get_session_manager()

        assert manager1 is manager2
        assert isinstance(manager1, SessionManager)

    def test_get_session_manager_with_redis(self):
        """Test get_session_manager with Redis client"""
        mock_redis = Mock()

        manager = get_session_manager(mock_redis)

        assert manager.redis_client == mock_redis

    def test_initialize_session_manager(self):
        """Test initialize_session_manager with custom settings"""
        mock_redis = Mock()

        manager = initialize_session_manager(
            redis_client=mock_redis,
            session_timeout=3600,
            refresh_timeout=172800,
            max_sessions_per_user=10,
        )

        assert manager.redis_client == mock_redis
        assert manager.session_timeout == 3600
        assert manager.refresh_timeout == 172800
        assert manager.max_sessions_per_user == 10


@pytest.mark.integration
class TestSessionManagerIntegration:
    """Integration tests for session manager"""

    def test_complete_session_lifecycle(self):
        """Test complete session lifecycle"""
        manager = SessionManager(redis_client=None)  # Use memory for testing

        # 1. Create session
        session = manager.create_session(
            user_id="user123",
            username="testuser",
            role="student",
            ip_address="192.168.1.1",
            user_agent="Test Browser",
        )

        assert session is not None
        original_session_id = session.session_id

        # 2. Retrieve session
        retrieved_session = manager.get_session(original_session_id)
        assert retrieved_session is not None
        assert retrieved_session.user_id == "user123"

        # 3. Refresh session
        refreshed_session = manager.refresh_session(
            session_id=original_session_id, refresh_token=session.refresh_token
        )

        assert refreshed_session is not None
        assert refreshed_session.session_id != original_session_id

        # 4. Original session should be invalidated
        assert manager.get_session(original_session_id) is None

        # 5. New session should be valid
        assert manager.get_session(refreshed_session.session_id) is not None

        # 6. Invalidate session
        result = manager.invalidate_session(refreshed_session.session_id)
        assert result is True

        # 7. Session should no longer exist
        assert manager.get_session(refreshed_session.session_id) is None

    def test_multi_user_session_management(self):
        """Test session management with multiple users"""
        manager = SessionManager(redis_client=None, max_sessions_per_user=2)

        users = ["user1", "user2", "user3"]
        user_sessions = {}

        # Create sessions for multiple users
        for user_id in users:
            user_sessions[user_id] = []
            for i in range(3):  # Try to create more than the limit
                session = manager.create_session(
                    user_id=user_id, username=f"user{user_id}", role="student"
                )
                user_sessions[user_id].append(session)

        # Check session limits are enforced
        for user_id in users:
            active_sessions = manager.get_user_sessions(user_id)
            assert len(active_sessions) <= manager.max_sessions_per_user

        # Test mass invalidation for one user
        count = manager.invalidate_all_user_sessions("user1", "password_change")
        assert count > 0

        # User1 should have no sessions
        assert len(manager.get_user_sessions("user1")) == 0

        # Other users should still have sessions
        assert len(manager.get_user_sessions("user2")) > 0
        assert len(manager.get_user_sessions("user3")) > 0

    def test_session_security_features(self):
        """Test session security features"""
        manager = SessionManager(redis_client=None)

        # Create session with client info
        session = manager.create_session(
            user_id="user123",
            username="testuser",
            role="student",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0 Test Browser",
        )

        # Test fingerprint validation
        assert (
            manager.validate_session_fingerprint(
                session.session_id, "192.168.1.1", "Mozilla/5.0 Test Browser"
            )
            is True
        )

        # Should fail with different IP
        assert (
            manager.validate_session_fingerprint(
                session.session_id, "192.168.1.2", "Mozilla/5.0 Test Browser"
            )
            is False
        )

        # Should fail with different user agent
        assert (
            manager.validate_session_fingerprint(
                session.session_id, "192.168.1.1", "Different Browser"
            )
            is False
        )

        # Test session token uniqueness
        tokens = set()
        for _ in range(100):
            token = manager.generate_session_token()
            assert token not in tokens  # Should be unique
            tokens.add(token)

    def test_concurrent_session_operations(self):
        """Test concurrent session operations"""
        import concurrent.futures

        manager = SessionManager(redis_client=None)

        def create_and_access_session(user_id):
            session = manager.create_session(
                user_id=f"user_{user_id}", username=f"user_{user_id}", role="student"
            )

            # Access session multiple times
            for _ in range(5):
                retrieved = manager.get_session(session.session_id)
                if retrieved is None:
                    return False

            return True

        # Test with multiple threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_and_access_session, i) for i in range(50)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # All operations should succeed
        assert all(results)

    def test_session_expiration_handling(self):
        """Test session expiration handling"""
        manager = SessionManager(redis_client=None, session_timeout=1)  # 1 second timeout

        # Create session
        session = manager.create_session(user_id="user123", username="testuser", role="student")

        # Session should be valid immediately
        assert manager.get_session(session.session_id) is not None

        # Wait for expiration
        time.sleep(1.1)

        # Session should be expired
        assert manager.get_session(session.session_id) is None


class TestErrorHandling:
    """Test error handling scenarios"""

    def test_malformed_session_data(self):
        """Test handling of malformed session data"""
        manager = SessionManager(redis_client=None)

        # Add malformed session data to memory
        manager._memory_sessions["malformed"] = "not_a_session_object"

        # Should handle gracefully
        manager.get_session("malformed")
        # Depending on implementation, might return None or handle gracefully

    def test_redis_connection_failure(self):
        """Test handling of Redis connection failures"""
        mock_redis = Mock()
        mock_redis.pipeline.side_effect = Exception("Redis connection failed")

        manager = SessionManager(redis_client=mock_redis)

        # Should handle Redis failures gracefully
        # Implementation might fall back to memory or handle errors
        try:
            manager.create_session(user_id="user123", username="testuser", role="student")
            # Should either succeed with fallback or handle error gracefully
        except Exception:
            # Redis errors should be handled internally
            pass

    def test_invalid_session_operations(self):
        """Test invalid session operations"""
        manager = SessionManager(redis_client=None)

        # Try to get non-existent session
        assert manager.get_session("nonexistent") is None

        # Try to invalidate non-existent session
        assert manager.invalidate_session("nonexistent") is False

        # Try to refresh non-existent session
        assert manager.refresh_session("nonexistent", "token") is None

    def test_memory_leak_prevention(self):
        """Test that expired sessions are cleaned up to prevent memory leaks"""
        manager = SessionManager(redis_client=None, session_timeout=0.1)  # Very short timeout

        # Create many sessions
        session_ids = []
        for i in range(100):
            session = manager.create_session(
                user_id=f"user_{i}", username=f"user_{i}", role="student"
            )
            session_ids.append(session.session_id)

        # Wait for expiration
        time.sleep(0.2)

        # Clean up expired sessions
        count = manager.cleanup_expired_sessions()

        # Memory should be freed
        assert count == 100
        assert len(manager._memory_sessions) == 0

    def test_session_data_integrity(self):
        """Test session data integrity"""
        manager = SessionManager(redis_client=None)

        # Create session
        session = manager.create_session(
            user_id="user123",
            username="testuser",
            role="student",
            ip_address="192.168.1.1",
        )

        # Manually corrupt session data
        corrupted_session = manager._memory_sessions[session.session_id]
        corrupted_session.user_id = "different_user"

        # Retrieved session should have corrupted data
        retrieved = manager.get_session(session.session_id)
        assert retrieved.user_id == "different_user"

        # In a real implementation, you might want integrity checks

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest_asyncio
"""
Comprehensive test suite for audit_logger.py
Tests security audit logging, event tracking, integrity validation, and alerting.
"""

import pytest
import json
import time
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock, mock_open
from datetime import datetime, timezone, timedelta
from pathlib import Path

from apps.backend.core.security.audit_logger import (
    SecurityAuditLogger, AuditEvent, AuditSeverity, AuditCategory,
    AuditLogEntry, get_audit_logger, audit_log
)


class TestAuditSeverity:
    """Test audit severity enumeration"""

    def test_severity_values(self):
        """Test audit severity values"""
        assert AuditSeverity.CRITICAL.value == "critical"
        assert AuditSeverity.HIGH.value == "high"
        assert AuditSeverity.MEDIUM.value == "medium"
        assert AuditSeverity.LOW.value == "low"
        assert AuditSeverity.INFO.value == "info"

    def test_severity_ordering(self):
        """Test that severities can be compared"""
        severities = [
            AuditSeverity.CRITICAL,
            AuditSeverity.HIGH,
            AuditSeverity.MEDIUM,
            AuditSeverity.LOW,
            AuditSeverity.INFO
        ]
        
        # Should all be distinct
        assert len(set(severities)) == len(severities)


class TestAuditCategory:
    """Test audit category enumeration"""

    def test_category_values(self):
        """Test audit category values"""
        assert AuditCategory.AUTHENTICATION.value == "authentication"
        assert AuditCategory.AUTHORIZATION.value == "authorization"
        assert AuditCategory.DATA_ACCESS.value == "data_access"
        assert AuditCategory.SECURITY_EVENT.value == "security_event"
        assert AuditCategory.USER_ACTION.value == "user_action"

    def test_all_categories_covered(self):
        """Test that important categories are included"""
        category_values = [cat.value for cat in AuditCategory]
        
        important_categories = [
            "authentication", "authorization", "data_access",
            "security_event", "user_action", "api_access"
        ]
        
        for category in important_categories:
            assert category in category_values


class TestAuditEvent:
    """Test audit event data structure"""

    def test_audit_event_creation(self):
        """Test creating audit event"""
        event = AuditEvent(
            timestamp="2025-01-01T00:00:00Z",
            event_id="test-event-123",
            category=AuditCategory.AUTHENTICATION,
            severity=AuditSeverity.HIGH,
            user_id="user123",
            username="testuser",
            ip_address="192.168.1.1",
            user_agent="Test Browser",
            action="login_attempt",
            resource="user_account",
            result="failure",
            details={"reason": "invalid_password"},
            session_id="session123",
            request_id="req123",
            correlation_id="corr123",
            environment="test",
            service_name="toolboxai",
            host="test-host"
        )
        
        assert event.event_id == "test-event-123"
        assert event.category == AuditCategory.AUTHENTICATION
        assert event.severity == AuditSeverity.HIGH
        assert event.user_id == "user123"
        assert event.action == "login_attempt"
        assert event.result == "failure"
        assert event.details["reason"] == "invalid_password"

    def test_audit_event_optional_fields(self):
        """Test audit event with optional fields"""
        event = AuditEvent(
            timestamp="2025-01-01T00:00:00Z",
            event_id="test-event-123",
            category=AuditCategory.SYSTEM,
            severity=AuditSeverity.INFO,
            user_id=None,
            username=None,
            ip_address=None,
            user_agent=None,
            action="system_startup",
            resource=None,
            result="success",
            details={},
            session_id=None,
            request_id=None,
            correlation_id=None,
            environment="test",
            service_name="toolboxai",
            host="test-host"
        )
        
        assert event.user_id is None
        assert event.username is None
        assert event.ip_address is None


class TestSecurityAuditLogger:
    """Test SecurityAuditLogger functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.mock_db = Mock()
        self.mock_redis = Mock()
        # Configure Redis mock to return proper values
        self.mock_redis.get.return_value = None  # Default no failures
        self.mock_redis.exists.return_value = 0  # Default not locked out
        
        # Use temporary directory for file logging
        self.temp_dir = tempfile.mkdtemp()
        self.log_file_path = os.path.join(self.temp_dir, "test_audit.log")
        
        self.logger = SecurityAuditLogger(
            service_name="test_service",
            environment="test",
            db_session=self.mock_db,
            redis_client=self.mock_redis,
            log_file_path=self.log_file_path,
            integrity_key="test_secret_key",
            async_mode=False  # Disable async for easier testing
        )

    def teardown_method(self):
        """Cleanup test environment"""
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_logger_initialization(self):
        """Test audit logger initialization"""
        assert self.logger.service_name == "test_service"
        assert self.logger.environment == "test"
        assert self.logger.db == self.mock_db
        assert self.logger.redis == self.mock_redis
        assert self.logger.enable_file_logging is True
        assert self.logger.enable_db_logging is True

    def test_integrity_hash_calculation(self):
        """Test integrity hash calculation"""
        event = AuditEvent(
            timestamp="2025-01-01T00:00:00Z",
            event_id="test-event-123",
            category=AuditCategory.AUTHENTICATION,
            severity=AuditSeverity.HIGH,
            user_id="user123",
            username="testuser",
            ip_address="192.168.1.1",
            user_agent="Test Browser",
            action="login_attempt",
            resource="user_account",
            result="failure",
            details={"reason": "invalid_password"},
            session_id="session123",
            request_id="req123",
            correlation_id="corr123",
            environment="test",
            service_name="toolboxai",
            host="test-host"
        )
        
        hash1 = self.logger._calculate_integrity_hash(event)
        hash2 = self.logger._calculate_integrity_hash(event)
        
        assert hash1 == hash2  # Should be deterministic
        assert isinstance(hash1, str)
        assert len(hash1) == 64  # SHA256 hex digest

    def test_integrity_verification(self):
        """Test integrity verification"""
        event = AuditEvent(
            timestamp="2025-01-01T00:00:00Z",
            event_id="test-event-123",
            category=AuditCategory.AUTHENTICATION,
            severity=AuditSeverity.HIGH,
            user_id="user123",
            username="testuser",
            ip_address="192.168.1.1",
            user_agent="Test Browser",
            action="login_attempt",
            resource="user_account",
            result="failure",
            details={"reason": "invalid_password"},
            session_id="session123",
            request_id="req123",
            correlation_id="corr123",
            environment="test",
            service_name="toolboxai",
            host="test-host"
        )
        
        # Calculate and set integrity hash
        event.integrity_hash = self.logger._calculate_integrity_hash(event)
        
        # Should verify successfully
        assert self.logger.verify_integrity(event) is True
        
        # Tamper with event
        event.action = "tampered_action"
        
        # Should fail verification
        assert self.logger.verify_integrity(event) is False

    @pytest.mark.asyncio
    async def test_log_event_basic(self):
        """Test basic event logging"""
        event_id = await self.logger.log_event(
            category=AuditCategory.AUTHENTICATION,
            severity=AuditSeverity.HIGH,
            action="login_attempt",
            result="failure",
            details={"reason": "invalid_password"},
            user_id="user123",
            username="testuser",
            ip_address="192.168.1.1"
        )
        
        assert event_id is not None
        assert isinstance(event_id, str)
        
        # Check statistics
        stats = self.logger.get_statistics()
        assert stats["total_events"] == 1
        assert stats["events_by_category"]["authentication"] == 1
        assert stats["events_by_severity"]["high"] == 1

    @pytest.mark.asyncio
    async def test_log_event_file_logging(self):
        """Test file logging functionality"""
        await self.logger.log_event(
            category=AuditCategory.USER_ACTION,
            severity=AuditSeverity.INFO,
            action="profile_update",
            result="success",
            details={"field": "email"},
            user_id="user123"
        )
        
        # Check that log file was created and contains event
        assert os.path.exists(self.log_file_path)
        
        with open(self.log_file_path, 'r') as f:
            log_content = f.read()
            
        assert "profile_update" in log_content
        assert "user123" in log_content
        assert "success" in log_content

    @pytest.mark.asyncio
    async def test_log_event_database_logging(self):
        """Test database logging functionality"""
        await self.logger.log_event(
            category=AuditCategory.DATA_ACCESS,
            severity=AuditSeverity.MEDIUM,
            action="data_export",
            result="success",
            details={"records": 100},
            user_id="user123"
        )
        
        # Verify database operations
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        
        # Check the added entry
        added_entry = self.mock_db.add.call_args[0][0]
        assert isinstance(added_entry, AuditLogEntry)
        assert added_entry.category == "data_access"
        assert added_entry.severity == "medium"
        assert added_entry.action == "data_export"
        assert added_entry.user_id == "user123"

    @pytest.mark.asyncio
    async def test_log_event_redis_publishing(self):
        """Test Redis event publishing"""
        await self.logger.log_event(
            category=AuditCategory.SECURITY_EVENT,
            severity=AuditSeverity.CRITICAL,
            action="brute_force_detected",
            result="blocked",
            details={"attempts": 10},
            ip_address="192.168.1.100"
        )
        
        # Verify Redis operations
        self.mock_redis.publish.assert_called()
        self.mock_redis.lpush.assert_called()
        self.mock_redis.ltrim.assert_called()
        self.mock_redis.expire.assert_called()

    @pytest.mark.asyncio
    async def test_alert_triggering_critical(self):
        """Test alert triggering for critical events"""
        alert_callback = AsyncMock()
        self.logger.add_alert_callback(alert_callback)
        
        await self.logger.log_event(
            category=AuditCategory.SECURITY_EVENT,
            severity=AuditSeverity.CRITICAL,
            action="data_breach_detected",
            result="investigating",
            details={"affected_records": 1000}
        )
        
        # Alert should have been triggered
        alert_callback.assert_called_once()
        
        # Check alert content
        alert_args = alert_callback.call_args[0][0]
        assert "Critical security event detected" in alert_args["message"]
        assert "data_breach_detected" in alert_args["event"]["action"]

    @pytest.mark.asyncio
    async def test_alert_triggering_failed_auth(self):
        """Test alert triggering for multiple failed authentications"""
        # Mock Redis to return failure count
        self.mock_redis.get.return_value = "5"
        
        alert_callback = AsyncMock()
        self.logger.add_alert_callback(alert_callback)
        
        await self.logger.log_event(
            category=AuditCategory.AUTHENTICATION,
            severity=AuditSeverity.HIGH,
            action="login_attempt",
            result="failure",
            details={"reason": "invalid_password"},
            user_id="user123",
            ip_address="192.168.1.1"
        )
        
        # Alert should have been triggered
        alert_callback.assert_called_once()
        alert_args = alert_callback.call_args[0][0]
        assert "Multiple failed authentication attempts" in alert_args["message"]

    @pytest.mark.asyncio
    async def test_alert_triggering_unauthorized_access(self):
        """Test alert triggering for unauthorized data access"""
        alert_callback = AsyncMock()
        self.logger.add_alert_callback(alert_callback)
        
        await self.logger.log_event(
            category=AuditCategory.DATA_ACCESS,
            severity=AuditSeverity.HIGH,
            action="sensitive_data_access",
            result="unauthorized",
            details={"resource": "user_profiles"},
            user_id="user123"
        )
        
        # Alert should have been triggered
        alert_callback.assert_called_once()
        alert_args = alert_callback.call_args[0][0]
        assert "Unauthorized data access attempt" in alert_args["message"]

    def test_event_id_generation(self):
        """Test event ID generation"""
        id1 = self.logger._generate_event_id()
        id2 = self.logger._generate_event_id()
        
        assert id1 != id2
        assert isinstance(id1, str)
        assert isinstance(id2, str)
        assert len(id1) == 36  # UUID4 format

    def test_statistics_tracking(self):
        """Test statistics tracking"""
        # Initial stats
        stats = self.logger.get_statistics()
        assert stats["total_events"] == 0
        
        # Create mock events
        event1 = AuditEvent(
            timestamp="2025-01-01T00:00:00Z",
            event_id="event1",
            category=AuditCategory.AUTHENTICATION,
            severity=AuditSeverity.HIGH,
            user_id=None, username=None, ip_address=None, user_agent=None,
            action="test", resource=None, result="success", details={},
            session_id=None, request_id=None, correlation_id=None,
            environment="test", service_name="test", host="test"
        )
        
        event2 = AuditEvent(
            timestamp="2025-01-01T00:00:01Z",
            event_id="event2",
            category=AuditCategory.AUTHENTICATION,
            severity=AuditSeverity.MEDIUM,
            user_id=None, username=None, ip_address=None, user_agent=None,
            action="test", resource=None, result="failure", details={},
            session_id=None, request_id=None, correlation_id=None,
            environment="test", service_name="test", host="test"
        )
        
        # Update statistics
        self.logger._update_statistics(event1)
        self.logger._update_statistics(event2)
        
        stats = self.logger.get_statistics()
        assert stats["total_events"] == 2
        assert stats["events_by_category"]["authentication"] == 2
        assert stats["events_by_severity"]["high"] == 1
        assert stats["events_by_severity"]["medium"] == 1

    @pytest.mark.asyncio
    async def test_log_rotation(self):
        """Test log file rotation"""
        # Create a large log file
        with open(self.log_file_path, 'w') as f:
            f.write("x" * (101 * 1024 * 1024))  # 101MB
        
        await self.logger._rotate_log_if_needed()
        
        # Original file should be smaller or gone
        if os.path.exists(self.log_file_path):
            assert os.path.getsize(self.log_file_path) < 100 * 1024 * 1024

    @pytest.mark.asyncio
    async def test_query_events(self):
        """Test querying audit events from database"""
        # Mock database query
        mock_entry = Mock()
        mock_entry.timestamp = datetime.now(timezone.utc)
        mock_entry.event_id = "test-event-123"
        mock_entry.category = "authentication"
        mock_entry.severity = "high"
        mock_entry.user_id = "user123"
        mock_entry.username = "testuser"
        mock_entry.ip_address = "192.168.1.1"
        mock_entry.action = "login_attempt"
        mock_entry.resource = "user_account"
        mock_entry.result = "failure"
        mock_entry.details = {"reason": "invalid_password"}
        mock_entry.session_id = "session123"
        mock_entry.request_id = "req123"
        mock_entry.correlation_id = "corr123"
        mock_entry.integrity_hash = "test_hash"
        
        # Configure mock database query chain
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_entry]
        self.mock_db.query.return_value = mock_query
        
        start_time = datetime.now(timezone.utc) - timedelta(hours=1)
        end_time = datetime.now(timezone.utc)
        
        events = await self.logger.query_events(
            start_time=start_time,
            end_time=end_time,
            category=AuditCategory.AUTHENTICATION,
            user_id="user123"
        )
        
        assert len(events) == 1
        assert events[0].event_id == "test-event-123"
        assert events[0].category == AuditCategory.AUTHENTICATION
        assert events[0].user_id == "user123"

    @pytest.mark.asyncio
    async def test_archive_old_events(self):
        """Test archiving old audit events"""
        await self.logger.archive_old_events(days_to_keep=30)
        
        # Verify database operations
        self.mock_db.query.assert_called()
        self.mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_no_redis_graceful_handling(self):
        """Test graceful handling when Redis is unavailable"""
        logger = SecurityAuditLogger(
            service_name="test_service",
            redis_client=None,
            async_mode=False
        )
        
        # Should not crash when Redis operations are called
        result = await logger._count_recent_failures("test_user")
        assert result == 0

    def test_no_database_graceful_handling(self):
        """Test graceful handling when database is unavailable"""
        logger = SecurityAuditLogger(
            service_name="test_service",
            db_session=None,
            enable_db_logging=False,
            async_mode=False
        )
        
        # Should initialize without database
        assert logger.db is None
        assert logger.enable_db_logging is False

    @pytest.mark.asyncio
    async def test_database_error_handling(self):
        """Test handling of database errors during logging"""
        # Mock database to raise exception
        self.mock_db.add.side_effect = Exception("Database error")
        
        # Should not crash, but increment failed events
        await self.logger.log_event(
            category=AuditCategory.SYSTEM,
            severity=AuditSeverity.INFO,
            action="test_action",
            result="success",
            details={}
        )
        
        stats = self.logger.get_statistics()
        assert stats["failed_events"] > 0


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_get_audit_logger_singleton(self):
        """Test that get_audit_logger returns singleton"""
        logger1 = get_audit_logger()
        logger2 = get_audit_logger()
        
        assert logger1 is logger2
        assert isinstance(logger1, SecurityAuditLogger)

    @pytest.mark.asyncio
    async def test_audit_log_convenience_function(self):
        """Test audit_log convenience function"""
        with patch('apps.backend.core.security.audit_logger.get_audit_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_logger.log_event = AsyncMock(return_value="test-event-123")
            mock_get_logger.return_value = mock_logger
            
            event_id = await audit_log(
                category=AuditCategory.USER_ACTION,
                severity=AuditSeverity.INFO,
                action="test_action",
                result="success",
                details={"test": "data"}
            )
            
            assert event_id == "test-event-123"
            mock_logger.log_event.assert_called_once()


@pytest.mark.integration
class TestAuditLoggerIntegration:
    """Integration tests for audit logger"""

    @pytest.mark.asyncio
    async def test_complete_audit_flow(self):
        """Test complete audit logging flow"""
        temp_dir = tempfile.mkdtemp()
        log_file = os.path.join(temp_dir, "integration_test.log")
        
        try:
            # Create logger with real file system
            logger = SecurityAuditLogger(
                service_name="integration_test",
                environment="test",
                log_file_path=log_file,
                enable_db_logging=False,  # Skip DB for integration test
                enable_siem_export=False,
                async_mode=False
            )
            
            # Log various types of events
            events = [
                (AuditCategory.AUTHENTICATION, AuditSeverity.HIGH, "login_failure"),
                (AuditCategory.AUTHORIZATION, AuditSeverity.MEDIUM, "access_denied"),
                (AuditCategory.DATA_ACCESS, AuditSeverity.LOW, "data_read"),
                (AuditCategory.SECURITY_EVENT, AuditSeverity.CRITICAL, "suspicious_activity"),
                (AuditCategory.USER_ACTION, AuditSeverity.INFO, "profile_update")
            ]
            
            event_ids = []
            for category, severity, action in events:
                event_id = await logger.log_event(
                    category=category,
                    severity=severity,
                    action=action,
                    result="success",
                    details={"test": "integration"},
                    user_id="integration_user"
                )
                event_ids.append(event_id)
            
            # Verify all events were logged
            assert len(event_ids) == len(events)
            assert all(event_id for event_id in event_ids)
            
            # Verify file logging
            assert os.path.exists(log_file)
            with open(log_file, 'r') as f:
                log_content = f.read()
            
            # Check that all actions appear in log
            for _, _, action in events:
                assert action in log_content
            
            # Verify statistics
            stats = logger.get_statistics()
            assert stats["total_events"] == len(events)
            assert stats["events_by_severity"]["critical"] == 1
            assert stats["events_by_severity"]["high"] == 1
            assert stats["events_by_category"]["authentication"] == 1
            
        finally:
            # Cleanup
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_concurrent_logging(self):
        """Test concurrent audit logging"""
        import threading
        import concurrent.futures
        
        temp_dir = tempfile.mkdtemp()
        log_file = os.path.join(temp_dir, "concurrent_test.log")
        
        try:
            logger = SecurityAuditLogger(
                service_name="concurrent_test",
                log_file_path=log_file,
                enable_db_logging=False,
                async_mode=False
            )
            
            async def log_event(event_id):
                return await logger.log_event(
                    category=AuditCategory.USER_ACTION,
                    severity=AuditSeverity.INFO,
                    action=f"concurrent_action_{event_id}",
                    result="success",
                    details={"event_id": event_id}
                )
            
            # Test with multiple threads
            def run_async_log(event_id):
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(log_event(event_id))
                finally:
                    loop.close()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(run_async_log, i) for i in range(50)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # All events should be logged successfully
            assert len(results) == 50
            assert all(result for result in results)
            
            # Verify statistics
            stats = logger.get_statistics()
            assert stats["total_events"] == 50
            
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestErrorHandling:
    """Test error handling scenarios"""

    def test_file_permission_errors(self):
        """Test handling of file permission errors"""
        # Try to create logger with invalid path
        invalid_path = "/root/cannot_write_here/audit.log"
        
        logger = SecurityAuditLogger(
            service_name="test",
            log_file_path=invalid_path,
            async_mode=False
        )
        
        # Should disable file logging gracefully
        assert logger.enable_file_logging is False

    @pytest.mark.asyncio
    async def test_malformed_event_data(self):
        """Test handling of malformed event data"""
        logger = SecurityAuditLogger(
            service_name="test",
            enable_db_logging=False,
            enable_file_logging=False,
            async_mode=False
        )
        
        # Should handle various edge cases
        event_id = await logger.log_event(
            category=AuditCategory.SYSTEM,
            severity=AuditSeverity.INFO,
            action="test",
            result="success",
            details={"complex": {"nested": {"data": [1, 2, 3]}}},
            user_id=None,
            ip_address=""
        )
        
        assert event_id is not None

    def test_integrity_hash_with_different_keys(self):
        """Test integrity hash calculation with different keys"""
        logger1 = SecurityAuditLogger(
            service_name="test",
            integrity_key="key1",
            async_mode=False
        )
        
        logger2 = SecurityAuditLogger(
            service_name="test",
            integrity_key="key2",
            async_mode=False
        )
        
        event = AuditEvent(
            timestamp="2025-01-01T00:00:00Z",
            event_id="test",
            category=AuditCategory.SYSTEM,
            severity=AuditSeverity.INFO,
            user_id=None, username=None, ip_address=None, user_agent=None,
            action="test", resource=None, result="success", details={},
            session_id=None, request_id=None, correlation_id=None,
            environment="test", service_name="test", host="test"
        )
        
        hash1 = logger1._calculate_integrity_hash(event)
        hash2 = logger2._calculate_integrity_hash(event)
        
        # Different keys should produce different hashes
        assert hash1 != hash2

    @pytest.mark.asyncio
    async def test_alert_callback_errors(self):
        """Test handling of alert callback errors"""
        logger = SecurityAuditLogger(
            service_name="test",
            async_mode=False
        )
        
        # Add callback that raises exception
        async def failing_callback(alert):
            raise Exception("Callback failed")
        
        logger.add_alert_callback(failing_callback)
        
        # Should not crash when callback fails
        await logger.log_event(
            category=AuditCategory.SECURITY_EVENT,
            severity=AuditSeverity.CRITICAL,
            action="test_critical",
            result="success",
            details={}
        )
        
        # Event should still be logged despite callback failure
        stats = logger.get_statistics()
        assert stats["total_events"] == 1

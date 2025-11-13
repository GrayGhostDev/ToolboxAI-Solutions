import pytest_asyncio

"""
import pytest
Test Comprehensive Logging System with Correlation IDs

Verifies that the logging system correctly:
- Tracks correlation IDs across requests
- Logs structured data in JSON format
- Masks sensitive information
- Tracks performance metrics
- Integrates with error handling
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))



import asyncio
import json
import logging
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient

from apps.backend.core.logging import (
    CorrelationIDMiddleware,
    LoggerAdapter,
    StructuredFormatter,
    correlation_id_context,
    initialize_logging,
    log_audit,
    log_database_operation,
    log_error,
    log_execution_time,
    log_external_api_call,
    logging_manager,
    request_context,
)


@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for logs"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def initialized_logging(temp_log_dir):
    """Initialize logging system with test configuration"""
    initialize_logging(
        log_level="DEBUG",
        log_dir=temp_log_dir,
        enable_file_logging=True,
        enable_console_logging=False
    )
    yield logging_manager
    # Clear handlers after test and close file handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        if hasattr(handler, 'close'):
            handler.close()
        root_logger.removeHandler(handler)
    root_logger.handlers.clear()


class TestLoggingManager:
    """Test the logging manager functionality"""
    
    def test_initialization(self, temp_log_dir):
        """Test logging system initialization"""
        initialize_logging(
            log_level="INFO",
            log_dir=temp_log_dir,
            enable_file_logging=True
        )
        
        assert logging_manager.initialized
        assert logging_manager.log_dir == Path(temp_log_dir)
        
        # Check log files were created
        log_files = list(Path(temp_log_dir).glob("*.log"))
        assert len(log_files) >= 2  # app.log and error.log
    
    def test_correlation_id_management(self, initialized_logging):
        """Test correlation ID setting and retrieval"""
        # Test setting correlation ID
        correlation_id = initialized_logging.set_correlation_id()
        assert correlation_id is not None
        assert initialized_logging.get_correlation_id() == correlation_id
        
        # Test setting custom correlation ID
        custom_id = "test-correlation-123"
        initialized_logging.set_correlation_id(custom_id)
        assert initialized_logging.get_correlation_id() == custom_id
        
        # Test clearing context
        initialized_logging.clear_context()
        assert initialized_logging.get_correlation_id() is None
    
    def test_logger_adapter(self, initialized_logging):
        """Test logger adapter functionality"""
        logger = initialized_logging.get_logger("test_module")
        assert isinstance(logger, LoggerAdapter)
        
        # Test that same logger is returned for same module
        logger2 = initialized_logging.get_logger("test_module")
        assert logger is logger2
        
        # Test different logger for different module
        logger3 = initialized_logging.get_logger("other_module")
        assert logger is not logger3


class TestStructuredFormatter:
    """Test the structured JSON formatter"""
    
    def test_basic_formatting(self):
        """Test basic log formatting"""
        formatter = StructuredFormatter()
        
        # Create a log record
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Format the record
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test_logger"
        assert log_data["message"] == "Test message"
        assert log_data["line"] == 42
        assert "timestamp" in log_data
    
    def test_sensitive_data_masking(self):
        """Test that sensitive data is masked"""
        formatter = StructuredFormatter()
        
        # Create a record with sensitive data
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="User login",
            args=(),
            exc_info=None
        )
        record.extra_fields = {
            "username": "john_doe",
            "password": "secret123",
            "api_key": "key_abc123",
            "token": "jwt_token_here",
            "safe_field": "visible_data"
        }
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        assert log_data["extra"]["password"] == "[REDACTED]"
        assert log_data["extra"]["api_key"] == "[REDACTED]"
        assert log_data["extra"]["token"] == "[REDACTED]"
        assert log_data["extra"]["safe_field"] == "visible_data"
    
    def test_correlation_id_inclusion(self, initialized_logging):
        """Test that correlation ID is included in logs"""
        formatter = StructuredFormatter()
        
        # Set correlation ID
        correlation_id = "test-corr-456"
        initialized_logging.set_correlation_id(correlation_id)
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test with correlation",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        assert log_data["correlation_id"] == correlation_id


class TestCorrelationIDMiddleware:
    """Test the correlation ID middleware"""
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_middleware_sets_correlation_id(self):
        """Test that middleware sets correlation ID"""
        app = FastAPI()
        app.add_middleware(CorrelationIDMiddleware)
        
        @app.get("/test")
        @pytest.mark.asyncio(loop_scope="function")
        @pytest.mark.asyncio
async def test_endpoint(request: Request):
            return {
                "correlation_id": request.state.correlation_id,
                "context_id": logging_manager.get_correlation_id()
            }
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 200
        data = response.json()
        assert data["correlation_id"] is not None
        assert data["context_id"] == data["correlation_id"]
        assert "X-Correlation-ID" in response.headers
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_middleware_uses_existing_correlation_id(self):
        """Test that middleware uses existing correlation ID from headers"""
        app = FastAPI()
        app.add_middleware(CorrelationIDMiddleware)
        
        @app.get("/test")
        @pytest.mark.asyncio(loop_scope="function")
        @pytest.mark.asyncio
async def test_endpoint(request: Request):
            return {"correlation_id": request.state.correlation_id}
        
        client = TestClient(app)
        custom_id = "client-correlation-789"
        response = client.get("/test", headers={"X-Correlation-ID": custom_id})
        
        assert response.status_code == 200
        assert response.json()["correlation_id"] == custom_id
        assert response.headers["X-Correlation-ID"] == custom_id


class TestLoggingDecorators:
    """Test logging decorators"""
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_execution_time_decorator_async(self, initialized_logging, caplog):
        """Test execution time decorator for async functions"""
        
        @log_execution_time(threshold_ms=50)
        async def slow_function():
            await asyncio.sleep(0.1)  # 100ms
            return "done"
        
        with caplog.at_level(logging.WARNING):
            result = await slow_function()
        
        assert result == "done"
        # Check that slow operation was logged
        assert any("Slow operation" in record.message for record in caplog.records)
    
    def test_execution_time_decorator_sync(self, initialized_logging, caplog):
        """Test execution time decorator for sync functions"""
        
        @log_execution_time(threshold_ms=50)
        def fast_function():
            time.sleep(0.01)  # 10ms
            return "done"
        
        with caplog.at_level(logging.DEBUG):
            result = fast_function()
        
        assert result == "done"
        # Check that operation was logged at debug level
        assert any("Operation completed" in record.message for record in caplog.records)
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_database_operation_decorator(self, initialized_logging, caplog):
        """Test database operation logging decorator"""
        
        @log_database_operation("SELECT")
        async def db_query():
            await asyncio.sleep(0.01)
            return ["row1", "row2"]
        
        with caplog.at_level(logging.DEBUG):
            result = await db_query()
        
        assert result == ["row1", "row2"]
        assert any("Database operation started: SELECT" in record.message for record in caplog.records)
        assert any("Database operation completed: SELECT" in record.message for record in caplog.records)
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_external_api_call_decorator(self, initialized_logging, caplog):
        """Test external API call logging decorator"""
        
        @log_external_api_call("PaymentService")
        async def call_payment_api():
            await asyncio.sleep(0.01)
            return {"status": "success"}
        
        with caplog.at_level(logging.INFO):
            result = await call_payment_api()
        
        assert result == {"status": "success"}
        assert any("External API call started: PaymentService" in record.message for record in caplog.records)
        assert any("External API call completed: PaymentService" in record.message for record in caplog.records)


class TestUtilityFunctions:
    """Test logging utility functions"""
    
    def test_log_error(self, initialized_logging, caplog):
        """Test error logging function"""
        try:
            raise ValueError("Test error")
        except ValueError as e:
            with caplog.at_level(logging.ERROR):
                log_error(e, context={"user_id": "123", "action": "test"})
        
        assert any("Error occurred: ValueError: Test error" in record.message for record in caplog.records)
    
    def test_log_audit(self, initialized_logging, caplog):
        """Test audit logging function"""
        with caplog.at_level(logging.INFO):
            log_audit(
                action="USER_LOGIN",
                user_id="user123",
                resource="auth_system",
                details={"ip": "192.168.1.1", "method": "password"}
            )
        
        assert any("Audit: USER_LOGIN by user user123" in record.message for record in caplog.records)


class TestPerformanceLogging:
    """Test performance logging functionality"""
    
    def test_performance_logging(self, initialized_logging, temp_log_dir):
        """Test that performance metrics are logged"""
        # Log some performance metrics
        initialized_logging.log_performance(
            "api.endpoint",
            duration_ms=150.5,
            success=True,
            metadata={"status_code": 200}
        )
        
        initialized_logging.log_performance(
            "db.query",
            duration_ms=2500.0,  # Slow query
            success=False,
            metadata={"error": "timeout"}
        )
        
        # Check performance log file
        perf_log = Path(temp_log_dir) / "performance.log"
        assert perf_log.exists()
        
        # Read and verify log content
        with open(perf_log, "r") as f:
            logs = f.readlines()
        
        assert len(logs) >= 2
        
        # Parse and verify first log entry
        log1 = json.loads(logs[0])
        assert "api.endpoint" in log1["message"]
        assert log1["extra"]["metadata"]["status_code"] == 200
        
        # Parse and verify second log entry (should be warning level due to slow duration)
        log2 = json.loads(logs[1])
        assert "db.query" in log2["message"]
        assert log2["level"] == "WARNING"  # Slow query should be warning
        assert log2["extra"]["metadata"]["error"] == "timeout"


class TestIntegrationWithErrorHandling:
    """Test integration with error handling system"""
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_error_handler_uses_correlation_id(self):
        """Test that error handler includes correlation ID in logs"""
        from apps.backend.core.errors.error_handler import ApplicationError, ErrorHandler
        
        app = FastAPI()
        app.add_middleware(CorrelationIDMiddleware)
        
        @app.get("/error")
        async def error_endpoint():
            raise ApplicationError("Test error", status_code=500)
        
        # Create mock request with correlation ID
        request = Mock(spec=Request)
        request.state.correlation_id = "test-correlation-999"
        request.url.path = "/error"
        request.method = "GET"
        request.app.state.debug = False
        
        # Create error handler and handle the error
        handler = ErrorHandler(debug=False)
        error = ApplicationError("Test error", status_code=500)
        
        response = await handler.handle_error(request, error)
        
        # Check response includes correlation ID
        response_data = json.loads(response.body)
        assert response_data["correlation_id"] == "test-correlation-999"
        assert response.headers["X-Correlation-ID"] == "test-correlation-999"


class TestLogRotation:
    """Test log file rotation"""
    
    def test_log_rotation_configuration(self, temp_log_dir):
        """Test that log rotation is properly configured"""
        initialize_logging(
            log_level="DEBUG",
            log_dir=temp_log_dir,
            max_bytes=1024,  # Small size to trigger rotation
            backup_count=3
        )
        
        logger = logging_manager.get_logger("test")
        
        # Write enough logs to trigger rotation
        for i in range(100):
            logger.info(
                f"Test log message {i} with some extra data to increase size",
                extra_fields={"index": i, "data": "x" * 100}
            )
        
        # Check that backup files were created
        log_files = list(Path(temp_log_dir).glob("app.log*"))
        assert len(log_files) > 1  # Should have main file and at least one backup


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
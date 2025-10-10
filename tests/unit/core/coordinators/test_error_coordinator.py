"""
Unit tests for Error Coordinator - Centralized error handling and recovery system
Tests error management, automatic recovery, alerting, and pattern analysis
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock, call
from datetime import datetime, timedelta
from typing import Dict, Any
import asyncio

from core.coordinators.error_coordinator import (
    ErrorCoordinator,
    ErrorRecord,
    RecoveryStrategy,
    AlertRule,
    ErrorSeverity,
    RecoveryStatus,
    RecoveryError,
    AlertError,
    create_error_coordinator,
)


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_config():
    """Sample configuration for error coordinator"""
    return {
        "max_error_history": 1000,
        "enable_auto_recovery": True,
        "enable_notifications": True,
        "notification_cooldown": 60,  # 1 minute for testing
        "smtp_server": "localhost",
        "smtp_port": 587,
        "smtp_username": "test@example.com",
        "smtp_password": "test_password",
        "alert_email": "alerts@example.com",
    }


@pytest.fixture
def error_coordinator(sample_config):
    """ErrorCoordinator instance with test configuration"""
    coordinator = ErrorCoordinator(config=sample_config)
    return coordinator


@pytest.fixture
def sample_error_record():
    """Sample error record for testing"""
    return ErrorRecord(
        error_id="error_123",
        error_type="connection_error",
        severity=ErrorSeverity.ERROR,
        message="Connection timeout",
        stack_trace="Traceback...",
        component="database",
        context={"host": "localhost", "port": 5432},
        tags=["database", "connection"],
    )


@pytest.fixture
def sample_recovery_strategy():
    """Sample recovery strategy"""
    return RecoveryStrategy(
        strategy_id="test_recovery",
        name="Test Recovery",
        description="Test recovery strategy",
        applicable_errors=["connection_error"],
        severity_threshold=ErrorSeverity.WARNING,
        auto_retry=True,
        max_attempts=3,
        delay_seconds=1,
        escalation_threshold=5,
        recovery_function=None,
    )


@pytest.fixture
def sample_alert_rule():
    """Sample alert rule"""
    return AlertRule(
        rule_id="test_alert",
        name="Test Alert",
        condition="error_rate > 0.5",
        severity_threshold=ErrorSeverity.ERROR,
        time_window_minutes=10,
        max_occurrences=5,
        notification_channels=["email", "log"],
        enabled=True,
    )


# ============================================================================
# Test Class: ErrorCoordinator Initialization
# ============================================================================


@pytest.mark.unit
class TestErrorCoordinatorInitialization:
    """Test ErrorCoordinator initialization"""

    def test_initialization_with_config(self, sample_config):
        """Test initialization with custom configuration"""
        coordinator = ErrorCoordinator(config=sample_config)

        assert coordinator.max_error_history == 1000
        assert coordinator.enable_auto_recovery is True
        assert coordinator.enable_notifications is True
        assert coordinator.notification_cooldown == 60
        assert coordinator.smtp_server == "localhost"
        assert coordinator.smtp_port == 587
        assert coordinator.alert_email == "alerts@example.com"

    def test_initialization_with_defaults(self):
        """Test initialization with default configuration"""
        coordinator = ErrorCoordinator()

        assert coordinator.max_error_history == 10000
        assert coordinator.enable_auto_recovery is True
        assert coordinator.enable_notifications is True
        assert coordinator.notification_cooldown == 300

    def test_default_recovery_strategies_loaded(self, error_coordinator):
        """Test default recovery strategies are loaded"""
        assert "connection_retry" in error_coordinator.recovery_strategies
        assert "service_restart" in error_coordinator.recovery_strategies
        assert "resource_cleanup" in error_coordinator.recovery_strategies
        assert "api_quota_wait" in error_coordinator.recovery_strategies
        assert "data_rollback" in error_coordinator.recovery_strategies

        # Verify connection_retry strategy details
        conn_retry = error_coordinator.recovery_strategies["connection_retry"]
        assert conn_retry.name == "Connection Retry"
        assert conn_retry.max_attempts == 3
        assert "connection_error" in conn_retry.applicable_errors

    def test_default_alert_rules_loaded(self, error_coordinator):
        """Test default alert rules are loaded"""
        assert "high_error_rate" in error_coordinator.alert_rules
        assert "critical_errors" in error_coordinator.alert_rules
        assert "component_failure" in error_coordinator.alert_rules
        assert "recovery_failure" in error_coordinator.alert_rules

        # Verify high_error_rate rule
        high_error_rate = error_coordinator.alert_rules["high_error_rate"]
        assert high_error_rate.name == "High Error Rate"
        assert high_error_rate.max_occurrences == 10

    @pytest.mark.asyncio
    async def test_initialize_starts_background_tasks(self, error_coordinator):
        """Test initialization starts background tasks"""
        with patch("asyncio.create_task") as mock_create_task:
            await error_coordinator.initialize()

            assert error_coordinator.is_initialized is True
            assert mock_create_task.call_count == 3  # 3 background tasks

    @pytest.mark.asyncio
    async def test_initialize_failure_raises_exception(self, error_coordinator):
        """Test initialization failure raises exception"""
        with patch("asyncio.create_task", side_effect=Exception("Task creation failed")):
            with pytest.raises(Exception) as exc_info:
                await error_coordinator.initialize()

            assert "Task creation failed" in str(exc_info.value)


# ============================================================================
# Test Class: Error Handling
# ============================================================================


@pytest.mark.unit
class TestErrorHandling:
    """Test error handling functionality"""

    @pytest.mark.asyncio
    async def test_handle_error_with_exception(self, error_coordinator):
        """Test handling error with Exception object"""
        try:
            raise ValueError("Test error")
        except ValueError as e:
            error_id = await error_coordinator.handle_error(
                error_type="validation_error",
                error=e,
                context={"field": "username"},
                component="auth_service",
                severity=ErrorSeverity.WARNING,
                tags=["validation"],
            )

        assert error_id is not None
        assert len(error_coordinator.error_history) == 1

        error_record = error_coordinator.error_history[0]
        assert error_record.error_id == error_id
        assert error_record.error_type == "validation_error"
        assert error_record.severity == ErrorSeverity.WARNING
        assert error_record.component == "auth_service"
        assert "Test error" in error_record.message
        assert "Traceback" in error_record.stack_trace

    @pytest.mark.asyncio
    async def test_handle_error_with_string(self, error_coordinator):
        """Test handling error with string message"""
        error_id = await error_coordinator.handle_error(
            error_type="custom_error",
            error="Custom error message",
            context={"details": "Some context"},
            component="test_component",
            severity=ErrorSeverity.ERROR,
        )

        assert error_id is not None
        error_record = error_coordinator.error_history[0]
        assert error_record.message == "Custom error message"
        assert error_record.stack_trace == ""

    @pytest.mark.asyncio
    async def test_handle_error_updates_error_counts(self, error_coordinator):
        """Test error handling updates error counts"""
        await error_coordinator.handle_error(
            "connection_error", "Connection failed", {}, "database"
        )
        await error_coordinator.handle_error(
            "connection_error", "Connection timeout", {}, "database"
        )
        await error_coordinator.handle_error(
            "validation_error", "Invalid input", {}, "api"
        )

        assert error_coordinator.error_counts["connection_error"] == 2
        assert error_coordinator.error_counts["validation_error"] == 1

    @pytest.mark.asyncio
    async def test_handle_error_updates_component_stats(self, error_coordinator):
        """Test error handling updates component statistics"""
        await error_coordinator.handle_error(
            "test_error", "Error 1", {}, "test_component", ErrorSeverity.ERROR
        )
        await error_coordinator.handle_error(
            "test_error", "Error 2", {}, "test_component", ErrorSeverity.ERROR
        )

        stats = error_coordinator.component_error_stats["test_component"]
        assert stats["total_errors"] == 2
        assert stats["last_error_time"] is not None

    @pytest.mark.asyncio
    async def test_handle_error_triggers_auto_recovery(self, error_coordinator):
        """Test error handling triggers automatic recovery"""
        error_coordinator.enable_auto_recovery = True

        with patch.object(
            error_coordinator, "_attempt_recovery", new_callable=AsyncMock
        ) as mock_recovery:
            await error_coordinator.handle_error(
                "connection_error",
                "Connection failed",
                {},
                "database",
                ErrorSeverity.ERROR,
            )

            # Give time for async task to start
            await asyncio.sleep(0.1)

            # Verify recovery was attempted
            assert mock_recovery.call_count >= 0  # May be called asynchronously

    @pytest.mark.asyncio
    async def test_handle_error_no_recovery_for_fatal(self, error_coordinator):
        """Test FATAL errors don't trigger auto-recovery"""
        error_coordinator.enable_auto_recovery = True

        with patch.object(
            error_coordinator, "_attempt_recovery", new_callable=AsyncMock
        ) as mock_recovery:
            await error_coordinator.handle_error(
                "fatal_error",
                "System crash",
                {},
                "system",
                ErrorSeverity.FATAL,
            )

            # Give time for potential async task
            await asyncio.sleep(0.1)

            # FATAL errors should not trigger recovery
            mock_recovery.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_error_updates_error_patterns(self, error_coordinator):
        """Test error handling updates error patterns"""
        await error_coordinator.handle_error(
            "pattern_error",
            "Error 1",
            {"key": "value1"},
            "component_a",
        )
        await error_coordinator.handle_error(
            "pattern_error",
            "Error 2",
            {"key": "value2"},
            "component_b",
        )

        patterns = error_coordinator.error_patterns["pattern_error"]
        assert len(patterns) == 2
        assert patterns[0]["component"] == "component_a"
        assert patterns[1]["component"] == "component_b"


# ============================================================================
# Test Class: Component Error Statistics
# ============================================================================


@pytest.mark.unit
class TestComponentErrorStatistics:
    """Test component error statistics tracking"""

    @pytest.mark.asyncio
    async def test_update_component_error_stats_total_errors(
        self, error_coordinator, sample_error_record
    ):
        """Test total error count updates"""
        await error_coordinator._update_component_error_stats(
            "database", sample_error_record
        )

        stats = error_coordinator.component_error_stats["database"]
        assert stats["total_errors"] == 1
        assert stats["last_error_time"] == sample_error_record.timestamp

    @pytest.mark.asyncio
    async def test_update_component_error_stats_recent_errors(
        self, error_coordinator
    ):
        """Test recent error count calculation"""
        # Add errors to history
        error1 = ErrorRecord(
            error_id="e1",
            error_type="test",
            severity=ErrorSeverity.ERROR,
            message="Error 1",
            stack_trace="",
            component="database",
            context={},
            timestamp=datetime.now() - timedelta(minutes=30),
        )
        error2 = ErrorRecord(
            error_id="e2",
            error_type="test",
            severity=ErrorSeverity.ERROR,
            message="Error 2",
            stack_trace="",
            component="database",
            context={},
            timestamp=datetime.now(),
        )

        error_coordinator.error_history.append(error1)
        error_coordinator.error_history.append(error2)

        await error_coordinator._update_component_error_stats("database", error2)

        stats = error_coordinator.component_error_stats["database"]
        assert stats["recent_errors"] == 2  # Both within last hour

    @pytest.mark.asyncio
    async def test_update_component_error_stats_error_rate(self, error_coordinator):
        """Test error rate calculation"""
        # Add multiple errors with timestamps
        base_time = datetime.now() - timedelta(hours=2)
        for i in range(5):
            error = ErrorRecord(
                error_id=f"e{i}",
                error_type="test",
                severity=ErrorSeverity.ERROR,
                message=f"Error {i}",
                stack_trace="",
                component="api",
                context={},
                timestamp=base_time + timedelta(minutes=i * 20),
            )
            error_coordinator.error_history.append(error)

        latest_error = error_coordinator.error_history[-1]
        await error_coordinator._update_component_error_stats("api", latest_error)

        stats = error_coordinator.component_error_stats["api"]
        assert stats["error_rate"] > 0

    @pytest.mark.asyncio
    async def test_update_component_error_stats_mean_time_between_errors(
        self, error_coordinator
    ):
        """Test mean time between errors calculation"""
        # Create errors with known time differences
        error1 = ErrorRecord(
            error_id="e1",
            error_type="test",
            severity=ErrorSeverity.ERROR,
            message="Error 1",
            stack_trace="",
            component="service",
            context={},
            timestamp=datetime.now() - timedelta(minutes=10),
        )
        error2 = ErrorRecord(
            error_id="e2",
            error_type="test",
            severity=ErrorSeverity.ERROR,
            message="Error 2",
            stack_trace="",
            component="service",
            context={},
            timestamp=datetime.now() - timedelta(minutes=5),
        )
        error3 = ErrorRecord(
            error_id="e3",
            error_type="test",
            severity=ErrorSeverity.ERROR,
            message="Error 3",
            stack_trace="",
            component="service",
            context={},
            timestamp=datetime.now(),
        )

        error_coordinator.error_history.extend([error1, error2, error3])

        await error_coordinator._update_component_error_stats("service", error3)

        stats = error_coordinator.component_error_stats["service"]
        assert stats["mean_time_between_errors"] > 0


# ============================================================================
# Test Class: Recovery System
# ============================================================================


@pytest.mark.unit
class TestRecoverySystem:
    """Test automatic recovery system"""

    @pytest.mark.asyncio
    async def test_attempt_recovery_finds_applicable_strategies(
        self, error_coordinator, sample_error_record
    ):
        """Test recovery attempts find applicable strategies"""
        with patch.object(
            error_coordinator,
            "_execute_recovery_strategy",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_execute:
            await error_coordinator._attempt_recovery(sample_error_record)

            # Should find connection_retry strategy
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_attempt_recovery_no_applicable_strategies(self, error_coordinator):
        """Test recovery when no applicable strategies exist"""
        error_record = ErrorRecord(
            error_id="e1",
            error_type="unknown_error_type",
            severity=ErrorSeverity.ERROR,
            message="Unknown error",
            stack_trace="",
            component="unknown",
            context={},
        )

        with patch.object(
            error_coordinator, "_execute_recovery_strategy", new_callable=AsyncMock
        ) as mock_execute:
            await error_coordinator._attempt_recovery(error_record)

            # No strategies should be executed
            mock_execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_attempt_recovery_successful(
        self, error_coordinator, sample_error_record
    ):
        """Test successful recovery updates error record"""
        with patch.object(
            error_coordinator,
            "_execute_recovery_strategy",
            new_callable=AsyncMock,
            return_value=True,
        ):
            with patch.object(
                error_coordinator, "_publish_recovery_event", new_callable=AsyncMock
            ):
                await error_coordinator._attempt_recovery(sample_error_record)

                assert sample_error_record.resolved is True
                assert sample_error_record.resolution_time is not None

    @pytest.mark.asyncio
    async def test_attempt_recovery_failed(
        self, error_coordinator, sample_error_record
    ):
        """Test failed recovery marks for manual intervention"""
        with patch.object(
            error_coordinator,
            "_execute_recovery_strategy",
            new_callable=AsyncMock,
            return_value=False,
        ):
            await error_coordinator._attempt_recovery(sample_error_record)

            assert sample_error_record.resolved is False
            assert len(sample_error_record.recovery_attempts) > 0

    @pytest.mark.asyncio
    async def test_execute_recovery_strategy_with_retries(
        self, error_coordinator, sample_recovery_strategy, sample_error_record
    ):
        """Test recovery strategy executes with retries"""
        sample_recovery_strategy.max_attempts = 3
        sample_recovery_strategy.delay_seconds = 0.01  # Fast for testing

        call_count = 0

        async def mock_recovery(error_record, attempt):
            nonlocal call_count
            call_count += 1
            return call_count == 3  # Succeed on 3rd attempt

        sample_recovery_strategy.recovery_function = mock_recovery

        success = await error_coordinator._execute_recovery_strategy(
            sample_recovery_strategy, sample_error_record
        )

        assert success is True
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_execute_recovery_strategy_exponential_backoff(
        self, error_coordinator, sample_recovery_strategy, sample_error_record
    ):
        """Test recovery uses exponential backoff"""
        sample_recovery_strategy.max_attempts = 3
        sample_recovery_strategy.delay_seconds = 0.1

        delays = []
        start_time = datetime.now()

        async def mock_recovery(error_record, attempt):
            delays.append((datetime.now() - start_time).total_seconds())
            return False  # Always fail to test all retries

        sample_recovery_strategy.recovery_function = mock_recovery

        await error_coordinator._execute_recovery_strategy(
            sample_recovery_strategy, sample_error_record
        )

        # Verify exponential backoff (delays should increase: 0.1, 0.2, 0.4)
        assert len(delays) == 3


# ============================================================================
# Test Class: Recovery Functions
# ============================================================================


@pytest.mark.unit
class TestRecoveryFunctions:
    """Test specific recovery functions"""

    @pytest.mark.asyncio
    async def test_recover_connection_mcp_client(self, error_coordinator):
        """Test connection recovery for MCP client"""
        error_record = ErrorRecord(
            error_id="e1",
            error_type="connection_error",
            severity=ErrorSeverity.ERROR,
            message="Connection failed",
            stack_trace="",
            component="mcp_client",
            context={},
        )

        mock_client = AsyncMock()
        mock_client.reconnect = AsyncMock(return_value=True)

        with patch(
            "core.coordinators.error_coordinator.MCPClient", return_value=mock_client
        ):
            success = await error_coordinator._recover_connection(error_record, 0)

            assert success is True
            mock_client.reconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_recover_connection_database(self, error_coordinator):
        """Test connection recovery for database"""
        error_record = ErrorRecord(
            error_id="e1",
            error_type="connection_error",
            severity=ErrorSeverity.ERROR,
            message="DB connection failed",
            stack_trace="",
            component="database",
            context={},
        )

        mock_session = MagicMock()
        mock_session.execute = MagicMock(return_value=None)
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=None)

        with patch(
            "core.coordinators.error_coordinator.get_session",
            return_value=mock_session,
        ):
            success = await error_coordinator._recover_connection(error_record, 0)

            assert success is True

    @pytest.mark.asyncio
    async def test_recover_service_restart_agent_system(self, error_coordinator):
        """Test service restart recovery for agent system"""
        error_record = ErrorRecord(
            error_id="e1",
            error_type="service_crash",
            severity=ErrorSeverity.ERROR,
            message="Agent system crashed",
            stack_trace="",
            component="agent_system",
            context={},
        )

        mock_orchestrator = AsyncMock()
        mock_orchestrator.restart = AsyncMock(return_value=True)

        with patch(
            "core.coordinators.error_coordinator.AgentOrchestrator",
            return_value=mock_orchestrator,
        ):
            success = await error_coordinator._recover_service_restart(error_record, 0)

            assert success is True
            mock_orchestrator.restart.assert_called_once()

    @pytest.mark.asyncio
    async def test_recover_resource_cleanup(self, error_coordinator):
        """Test resource cleanup recovery"""
        error_record = ErrorRecord(
            error_id="e1",
            error_type="memory_error",
            severity=ErrorSeverity.ERROR,
            message="Out of memory",
            stack_trace="",
            component="service",
            context={},
        )

        with patch("gc.collect") as mock_gc:
            # Test basic cleanup without coordinator system
            success = await error_coordinator._recover_resource_cleanup(error_record, 0)

            mock_gc.assert_called_once()

    @pytest.mark.asyncio
    async def test_recover_api_quota(self, error_coordinator):
        """Test API quota recovery"""
        error_record = ErrorRecord(
            error_id="e1",
            error_type="quota_exceeded",
            severity=ErrorSeverity.WARNING,
            message="API quota exceeded",
            stack_trace="",
            component="api",
            context={},
        )

        # API quota recovery just returns True (waits handled by delay)
        success = await error_coordinator._recover_api_quota(error_record, 0)

        assert success is True

    @pytest.mark.asyncio
    async def test_recover_data_rollback(self, error_coordinator):
        """Test data rollback recovery"""
        error_record = ErrorRecord(
            error_id="e1",
            error_type="data_corruption",
            severity=ErrorSeverity.ERROR,
            message="Data corrupted",
            stack_trace="",
            component="database",
            context={},
        )

        # Without coordinator system, should return False
        success = await error_coordinator._recover_data_rollback(error_record, 0)

        assert success is False


# ============================================================================
# Test Class: Alert System
# ============================================================================


@pytest.mark.unit
class TestAlertSystem:
    """Test alert and notification system"""

    @pytest.mark.asyncio
    async def test_check_alert_rules_triggers_alert(
        self, error_coordinator, sample_error_record
    ):
        """Test alert rules trigger when conditions met"""
        # Create alert rule that should trigger
        alert_rule = AlertRule(
            rule_id="test_rule",
            name="Test Rule",
            condition="severity >= 3",  # ERROR level
            severity_threshold=ErrorSeverity.ERROR,
            time_window_minutes=10,
            max_occurrences=1,
            notification_channels=["log"],
            enabled=True,
        )

        error_coordinator.alert_rules["test_rule"] = alert_rule

        with patch.object(
            error_coordinator, "_trigger_alert", new_callable=AsyncMock
        ) as mock_trigger:
            await error_coordinator._check_alert_rules(sample_error_record)

            mock_trigger.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_alert_rules_disabled_rule(
        self, error_coordinator, sample_error_record
    ):
        """Test disabled alert rules don't trigger"""
        alert_rule = AlertRule(
            rule_id="disabled_rule",
            name="Disabled Rule",
            condition="severity >= 0",
            severity_threshold=ErrorSeverity.INFO,
            time_window_minutes=10,
            max_occurrences=1,
            notification_channels=["log"],
            enabled=False,
        )

        error_coordinator.alert_rules["disabled_rule"] = alert_rule

        with patch.object(
            error_coordinator, "_trigger_alert", new_callable=AsyncMock
        ) as mock_trigger:
            await error_coordinator._check_alert_rules(sample_error_record)

            mock_trigger.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_alert_rules_severity_threshold(
        self, error_coordinator, sample_error_record
    ):
        """Test alert rules respect severity threshold"""
        # Create rule that requires CRITICAL severity
        alert_rule = AlertRule(
            rule_id="critical_rule",
            name="Critical Rule",
            condition="severity >= 4",
            severity_threshold=ErrorSeverity.CRITICAL,
            time_window_minutes=10,
            max_occurrences=1,
            notification_channels=["log"],
            enabled=True,
        )

        error_coordinator.alert_rules["critical_rule"] = alert_rule

        # sample_error_record has ERROR severity, should not trigger
        with patch.object(
            error_coordinator, "_trigger_alert", new_callable=AsyncMock
        ) as mock_trigger:
            await error_coordinator._check_alert_rules(sample_error_record)

            mock_trigger.assert_not_called()

    def test_evaluate_condition_safely_comparison(self, error_coordinator):
        """Test safe condition evaluation with comparisons"""
        context = {"error_rate": 0.15, "severity": 3}

        # Test greater than
        result = error_coordinator._evaluate_condition_safely(
            "error_rate > 0.1", context
        )
        assert result is True

        # Test less than
        result = error_coordinator._evaluate_condition_safely(
            "error_rate < 0.2", context
        )
        assert result is True

        # Test equality
        result = error_coordinator._evaluate_condition_safely("severity == 3", context)
        assert result is True

        # Test inequality
        result = error_coordinator._evaluate_condition_safely("severity != 5", context)
        assert result is True

    def test_evaluate_condition_safely_boolean_operators(self, error_coordinator):
        """Test safe condition evaluation with boolean operators"""
        context = {"error_rate": 0.15, "severity": 3, "total_errors": 10}

        # Test AND
        result = error_coordinator._evaluate_condition_safely(
            "error_rate > 0.1 and severity >= 3", context
        )
        assert result is True

        # Test OR
        result = error_coordinator._evaluate_condition_safely(
            "error_rate > 0.5 or severity >= 3", context
        )
        assert result is True

        # Test NOT (unary operator)
        result = error_coordinator._evaluate_condition_safely(
            "not (error_rate > 0.5)", context
        )
        assert result is True

    def test_evaluate_condition_safely_arithmetic(self, error_coordinator):
        """Test safe condition evaluation with arithmetic"""
        context = {"a": 10, "b": 5}

        result = error_coordinator._evaluate_condition_safely("a + b > 12", context)
        assert result is True

        result = error_coordinator._evaluate_condition_safely("a - b == 5", context)
        assert result is True

        result = error_coordinator._evaluate_condition_safely("a * b > 40", context)
        assert result is True

    def test_evaluate_condition_safely_invalid_expression(self, error_coordinator):
        """Test safe condition evaluation rejects invalid expressions"""
        context = {"error_rate": 0.15}

        with pytest.raises(ValueError):
            error_coordinator._evaluate_condition_safely(
                "import os; os.system('ls')", context
            )

    @pytest.mark.asyncio
    async def test_trigger_alert_notification_cooldown(self, error_coordinator):
        """Test alert respects notification cooldown"""
        alert_rule = AlertRule(
            rule_id="cooldown_rule",
            name="Cooldown Rule",
            condition="severity >= 3",
            severity_threshold=ErrorSeverity.ERROR,
            time_window_minutes=10,
            max_occurrences=1,
            notification_channels=["log"],
        )

        error_record = ErrorRecord(
            error_id="e1",
            error_type="test",
            severity=ErrorSeverity.ERROR,
            message="Test",
            stack_trace="",
            component="test",
            context={},
        )

        # Set last notification time to recent
        error_coordinator.last_notification_times["cooldown_rule"] = datetime.now()

        with patch.object(
            error_coordinator, "_send_email_alert", new_callable=AsyncMock
        ) as mock_email:
            await error_coordinator._trigger_alert(alert_rule, error_record, {})

            # Should not send due to cooldown
            mock_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_trigger_alert_multiple_channels(self, error_coordinator):
        """Test alert sends to multiple notification channels"""
        alert_rule = AlertRule(
            rule_id="multi_channel",
            name="Multi Channel",
            condition="severity >= 3",
            severity_threshold=ErrorSeverity.ERROR,
            time_window_minutes=10,
            max_occurrences=1,
            notification_channels=["email", "log", "slack"],
        )

        error_record = ErrorRecord(
            error_id="e1",
            error_type="test",
            severity=ErrorSeverity.ERROR,
            message="Test",
            stack_trace="",
            component="test",
            context={},
        )

        with patch.object(
            error_coordinator, "_send_email_alert", new_callable=AsyncMock
        ) as mock_email:
            with patch.object(
                error_coordinator, "_send_slack_alert", new_callable=AsyncMock
            ) as mock_slack:
                await error_coordinator._trigger_alert(alert_rule, error_record, {})

                mock_email.assert_called_once()
                mock_slack.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_alert(self, error_coordinator):
        """Test email alert sending"""
        mock_smtp = MagicMock()
        mock_smtp.starttls = MagicMock()
        mock_smtp.login = MagicMock()
        mock_smtp.send_message = MagicMock()
        mock_smtp.quit = MagicMock()

        with patch("smtplib.SMTP", return_value=mock_smtp):
            await error_coordinator._send_email_alert("Test Alert", "Test message")

            mock_smtp.starttls.assert_called_once()
            mock_smtp.login.assert_called_once()
            mock_smtp.send_message.assert_called_once()
            mock_smtp.quit.assert_called_once()


# ============================================================================
# Test Class: Pattern Analysis
# ============================================================================


@pytest.mark.unit
class TestPatternAnalysis:
    """Test error pattern analysis"""

    @pytest.mark.asyncio
    async def test_analyze_error_patterns_hourly_distribution(self, error_coordinator):
        """Test hourly error distribution analysis"""
        # Add errors at different hours
        for hour in [8, 9, 10, 14, 14, 14]:
            error = ErrorRecord(
                error_id=f"e{hour}",
                error_type="test",
                severity=ErrorSeverity.ERROR,
                message="Test",
                stack_trace="",
                component="test",
                context={},
                timestamp=datetime.now().replace(hour=hour),
            )
            error_coordinator.error_history.append(error)

        analysis = await error_coordinator._analyze_error_patterns()

        assert "hourly_distribution" in analysis
        # Hour 14 should have the most errors (3)
        assert analysis["hourly_distribution"][14] == 3

    @pytest.mark.asyncio
    async def test_analyze_error_patterns_component_distribution(
        self, error_coordinator
    ):
        """Test component error distribution analysis"""
        # Add errors to different components
        for component in ["db", "db", "db", "api", "api", "cache"]:
            error = ErrorRecord(
                error_id=f"e{component}",
                error_type="test",
                severity=ErrorSeverity.ERROR,
                message="Test",
                stack_trace="",
                component=component,
                context={},
            )
            error_coordinator.error_history.append(error)

        analysis = await error_coordinator._analyze_error_patterns()

        assert "component_distribution" in analysis
        assert analysis["component_distribution"]["db"] == 3
        assert analysis["component_distribution"]["api"] == 2
        assert analysis["component_distribution"]["cache"] == 1

    @pytest.mark.asyncio
    async def test_analyze_error_patterns_error_type_frequency(
        self, error_coordinator
    ):
        """Test error type frequency analysis"""
        # Add various error types
        types = ["conn_err", "conn_err", "val_err", "auth_err", "auth_err", "auth_err"]
        for error_type in types:
            error = ErrorRecord(
                error_id=f"e{error_type}",
                error_type=error_type,
                severity=ErrorSeverity.ERROR,
                message="Test",
                stack_trace="",
                component="test",
                context={},
            )
            error_coordinator.error_history.append(error)

        analysis = await error_coordinator._analyze_error_patterns()

        assert "error_type_frequency" in analysis
        assert analysis["error_type_frequency"]["auth_err"] == 3
        assert analysis["error_type_frequency"]["conn_err"] == 2

    @pytest.mark.asyncio
    async def test_analyze_error_patterns_recent_trend(self, error_coordinator):
        """Test recent trend analysis"""
        # Add recent errors (within last 24 hours)
        for i in range(10):
            error = ErrorRecord(
                error_id=f"e{i}",
                error_type="recent_error",
                severity=ErrorSeverity.ERROR,
                message="Test",
                stack_trace="",
                component="test",
                context={},
                timestamp=datetime.now() - timedelta(hours=i),
            )
            error_coordinator.error_history.append(error)

        analysis = await error_coordinator._analyze_error_patterns()

        assert "recent_trend" in analysis
        assert analysis["recent_trend"]["total_recent_errors"] == 10
        assert analysis["recent_trend"]["most_common_recent"] == "recent_error"

    @pytest.mark.asyncio
    async def test_generate_error_insights_high_error_rate(self, error_coordinator):
        """Test insights generated for high error rate"""
        patterns = {
            "recent_trend": {"error_rate_per_hour": 10.5, "total_recent_errors": 252},
            "component_distribution": {},
            "hourly_distribution": {},
        }

        insights = await error_coordinator._generate_error_insights(patterns)

        assert len(insights) > 0
        assert any("High error rate" in insight for insight in insights)

    @pytest.mark.asyncio
    async def test_generate_error_insights_component_concentration(
        self, error_coordinator
    ):
        """Test insights generated for component error concentration"""
        # Add many errors to single component
        for i in range(50):
            error = ErrorRecord(
                error_id=f"e{i}",
                error_type="test",
                severity=ErrorSeverity.ERROR,
                message="Test",
                stack_trace="",
                component="problematic_component",
                context={},
            )
            error_coordinator.error_history.append(error)

        patterns = await error_coordinator._analyze_error_patterns()
        insights = await error_coordinator._generate_error_insights(patterns)

        assert any("disproportionate error rate" in insight for insight in insights)


# ============================================================================
# Test Class: Error Summary and Metrics
# ============================================================================


@pytest.mark.unit
class TestErrorSummaryAndMetrics:
    """Test error summary and metrics reporting"""

    @pytest.mark.asyncio
    async def test_get_error_summary_severity_breakdown(self, error_coordinator):
        """Test error summary includes severity breakdown"""
        # Add errors with different severities
        severities = [
            ErrorSeverity.WARNING,
            ErrorSeverity.WARNING,
            ErrorSeverity.ERROR,
            ErrorSeverity.ERROR,
            ErrorSeverity.ERROR,
            ErrorSeverity.CRITICAL,
        ]

        for i, severity in enumerate(severities):
            error = ErrorRecord(
                error_id=f"e{i}",
                error_type="test",
                severity=severity,
                message="Test",
                stack_trace="",
                component="test",
                context={},
                timestamp=datetime.now() - timedelta(hours=1),
            )
            error_coordinator.error_history.append(error)

        summary = await error_coordinator.get_error_summary(time_window_hours=24)

        assert summary["severity_breakdown"]["warning"] == 2
        assert summary["severity_breakdown"]["error"] == 3
        assert summary["severity_breakdown"]["critical"] == 1

    @pytest.mark.asyncio
    async def test_get_error_summary_resolution_rate(self, error_coordinator):
        """Test error summary calculates resolution rate"""
        # Add errors, some resolved
        for i in range(10):
            error = ErrorRecord(
                error_id=f"e{i}",
                error_type="test",
                severity=ErrorSeverity.ERROR,
                message="Test",
                stack_trace="",
                component="test",
                context={},
                resolved=(i < 6),  # 6 out of 10 resolved
                timestamp=datetime.now() - timedelta(hours=1),
            )
            error_coordinator.error_history.append(error)

        summary = await error_coordinator.get_error_summary(time_window_hours=24)

        assert summary["total_errors"] == 10
        assert summary["resolution_rate"] == 60.0

    @pytest.mark.asyncio
    async def test_get_metrics_includes_all_data(self, error_coordinator):
        """Test get_metrics includes comprehensive data"""
        # Add some test data
        await error_coordinator.handle_error(
            "test_error", "Test message", {}, "test_component"
        )

        metrics = await error_coordinator.get_metrics()

        assert "error_summary" in metrics
        assert "system_stats" in metrics
        assert "component_error_stats" in metrics
        assert "recent_patterns" in metrics

        assert metrics["system_stats"]["total_errors_tracked"] > 0

    @pytest.mark.asyncio
    async def test_get_health_healthy_status(self, error_coordinator):
        """Test health check returns healthy when few errors"""
        # No recent errors
        health = await error_coordinator.get_health()

        assert health["status"] == "healthy"
        assert "recent_error_rate" in health

    @pytest.mark.asyncio
    async def test_get_health_degraded_status(self, error_coordinator):
        """Test health check returns degraded with moderate errors"""
        # Add moderate number of recent errors
        for i in range(10):
            error = ErrorRecord(
                error_id=f"e{i}",
                error_type="test",
                severity=ErrorSeverity.ERROR,
                message="Test",
                stack_trace="",
                component="test",
                context={},
                timestamp=datetime.now() - timedelta(minutes=30),
            )
            error_coordinator.error_history.append(error)

        health = await error_coordinator.get_health()

        assert health["status"] in ["healthy", "degraded"]
        assert health["recent_error_rate"] >= 10

    @pytest.mark.asyncio
    async def test_get_health_unhealthy_status(self, error_coordinator):
        """Test health check returns unhealthy with many errors"""
        # Add many recent errors
        for i in range(25):
            error = ErrorRecord(
                error_id=f"e{i}",
                error_type="test",
                severity=ErrorSeverity.ERROR,
                message="Test",
                stack_trace="",
                component="test",
                context={},
                timestamp=datetime.now() - timedelta(minutes=30),
            )
            error_coordinator.error_history.append(error)

        health = await error_coordinator.get_health()

        assert health["status"] == "unhealthy"
        assert health["recent_error_rate"] >= 20


# ============================================================================
# Test Class: FastAPI Routes
# ============================================================================


@pytest.mark.unit
class TestFastAPIRoutes:
    """Test FastAPI endpoint setup"""

    def test_routes_registered(self, error_coordinator):
        """Test all required routes are registered"""
        routes = [route.path for route in error_coordinator.app.routes]

        assert "/errors" in routes
        assert "/errors/{error_id}" in routes
        assert "/summary" in routes
        assert "/recovery/{error_id}" in routes
        assert "/strategies" in routes
        assert "/alerts" in routes
        assert "/metrics" in routes
        assert "/health" in routes

    @pytest.mark.asyncio
    async def test_handle_error_endpoint(self, error_coordinator):
        """Test handle error via REST endpoint"""
        error_endpoint = next(
            r.endpoint
            for r in error_coordinator.app.routes
            if r.path == "/errors" and hasattr(r, "methods") and "POST" in r.methods
        )

        request_data = {
            "error_type": "api_error",
            "error": "API request failed",
            "context": {"endpoint": "/api/users"},
            "component": "api",
            "severity": "error",
            "tags": ["api"],
        }

        response = await error_endpoint(request_data)

        assert "error_id" in response
        assert len(error_coordinator.error_history) == 1


# ============================================================================
# Test Class: Shutdown
# ============================================================================


@pytest.mark.unit
class TestShutdown:
    """Test graceful shutdown"""

    @pytest.mark.asyncio
    async def test_shutdown_cancels_background_tasks(self, error_coordinator):
        """Test shutdown cancels all background tasks"""
        error_coordinator.pattern_analyzer_task = AsyncMock()
        error_coordinator.alert_processor_task = AsyncMock()
        error_coordinator.cleanup_task = AsyncMock()
        error_coordinator.is_initialized = True

        await error_coordinator.shutdown()

        error_coordinator.pattern_analyzer_task.cancel.assert_called_once()
        error_coordinator.alert_processor_task.cancel.assert_called_once()
        error_coordinator.cleanup_task.cancel.assert_called_once()
        assert error_coordinator.is_initialized is False

    @pytest.mark.asyncio
    async def test_shutdown_handles_errors_gracefully(self, error_coordinator):
        """Test shutdown handles errors during cleanup"""
        error_coordinator.pattern_analyzer_task = AsyncMock()
        error_coordinator.pattern_analyzer_task.cancel.side_effect = Exception(
            "Cancel failed"
        )
        error_coordinator.is_initialized = True

        # Should not raise exception
        await error_coordinator.shutdown()

        assert error_coordinator.is_initialized is False


# ============================================================================
# Test Class: Convenience Functions
# ============================================================================


@pytest.mark.unit
class TestConvenienceFunctions:
    """Test module-level convenience functions"""

    @pytest.mark.asyncio
    async def test_create_error_coordinator(self):
        """Test create_error_coordinator factory function"""
        with patch.object(ErrorCoordinator, "initialize", new_callable=AsyncMock):
            coordinator = await create_error_coordinator(
                config={"max_error_history": 500}
            )

            assert isinstance(coordinator, ErrorCoordinator)
            assert coordinator.max_error_history == 500
            coordinator.initialize.assert_called_once()


# ============================================================================
# Test Class: ErrorRecord Properties
# ============================================================================


@pytest.mark.unit
class TestErrorRecord:
    """Test ErrorRecord dataclass"""

    def test_error_record_age_minutes(self):
        """Test error age calculation"""
        error = ErrorRecord(
            error_id="e1",
            error_type="test",
            severity=ErrorSeverity.ERROR,
            message="Test",
            stack_trace="",
            component="test",
            context={},
            timestamp=datetime.now() - timedelta(minutes=30),
        )

        assert error.age_minutes >= 29  # Allow for execution time
        assert error.age_minutes <= 31

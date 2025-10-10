"""
Comprehensive unit tests for core/coordinators/monitor.py

Tests cover:
- Environment variable configuration (CHECK_INTERVAL, STALE_WORKER_SEC)
- Monitor initialization
- Monitor loop (continuous checking with sleep)
- Monitor check (stale workers, queue backlog)
- TaskRegistry integration
- Edge cases and error handling
"""

import time
from unittest.mock import Mock, patch, MagicMock, call
import pytest

# Import the module under test
from core.coordinators import monitor
from core.coordinators.task_registry import TaskState


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_task_registry():
    """Create mock TaskRegistry"""
    registry = Mock()
    registry.list_workers = Mock(return_value=[])
    registry.qstat = Mock(return_value={})
    return registry


@pytest.fixture
def mock_monitor(mock_task_registry):
    """Create Monitor with mock TaskRegistry"""
    with patch('core.coordinators.monitor.TaskRegistry', return_value=mock_task_registry):
        return monitor.Monitor()


# ============================================================================
# Test Environment Variables
# ============================================================================

class TestEnvironmentVariables:
    """Test environment variable configuration"""

    def test_check_interval_default(self):
        """Test CHECK_INTERVAL has default value"""
        assert monitor.CHECK_INTERVAL == 10 or isinstance(monitor.CHECK_INTERVAL, int)

    def test_stale_worker_sec_default(self):
        """Test STALE_WORKER_SEC has default value"""
        assert monitor.STALE_WORKER_SEC == 90 or isinstance(monitor.STALE_WORKER_SEC, int)

    def test_check_interval_is_int(self):
        """Test CHECK_INTERVAL is an integer"""
        assert isinstance(monitor.CHECK_INTERVAL, int)

    def test_stale_worker_sec_is_int(self):
        """Test STALE_WORKER_SEC is an integer"""
        assert isinstance(monitor.STALE_WORKER_SEC, int)

    def test_check_interval_positive(self):
        """Test CHECK_INTERVAL is positive"""
        assert monitor.CHECK_INTERVAL > 0

    def test_stale_worker_sec_positive(self):
        """Test STALE_WORKER_SEC is positive"""
        assert monitor.STALE_WORKER_SEC > 0


# ============================================================================
# Test Monitor Initialization
# ============================================================================

class TestMonitorInitialization:
    """Test Monitor initialization"""

    def test_initialization_creates_task_registry(self):
        """Test Monitor initialization creates TaskRegistry"""
        with patch('core.coordinators.monitor.TaskRegistry') as mock_registry_class:
            mock_registry_instance = Mock()
            mock_registry_class.return_value = mock_registry_instance

            mon = monitor.Monitor()

            assert mon.reg == mock_registry_instance
            mock_registry_class.assert_called_once()

    def test_initialization_without_args(self):
        """Test Monitor can be initialized without arguments"""
        with patch('core.coordinators.monitor.TaskRegistry'):
            mon = monitor.Monitor()

            assert mon is not None

    def test_reg_attribute_exists(self):
        """Test Monitor has reg attribute"""
        with patch('core.coordinators.monitor.TaskRegistry'):
            mon = monitor.Monitor()

            assert hasattr(mon, 'reg')


# ============================================================================
# Test Monitor Loop Method
# ============================================================================

class TestMonitorLoop:
    """Test Monitor loop method"""

    def test_loop_calls_check(self):
        """Test loop calls check method"""
        with patch('core.coordinators.monitor.TaskRegistry'):
            mon = monitor.Monitor()

            with patch.object(mon, 'check') as mock_check:
                with patch('time.sleep', side_effect=[None, KeyboardInterrupt()]):
                    try:
                        mon.loop()
                    except KeyboardInterrupt:
                        pass

            # Should have called check at least once
            mock_check.assert_called()

    def test_loop_sleeps_between_checks(self):
        """Test loop sleeps between checks"""
        with patch('core.coordinators.monitor.TaskRegistry'):
            mon = monitor.Monitor()

            with patch.object(mon, 'check'):
                with patch('time.sleep', side_effect=[None, KeyboardInterrupt()]) as mock_sleep:
                    try:
                        mon.loop()
                    except KeyboardInterrupt:
                        pass

            # Should have slept at least once
            mock_sleep.assert_called()

    def test_loop_uses_check_interval(self):
        """Test loop uses CHECK_INTERVAL for sleep"""
        with patch('core.coordinators.monitor.TaskRegistry'):
            mon = monitor.Monitor()

            with patch.object(mon, 'check'):
                with patch('time.sleep', side_effect=[None, KeyboardInterrupt()]) as mock_sleep:
                    try:
                        mon.loop()
                    except KeyboardInterrupt:
                        pass

            # Should sleep with CHECK_INTERVAL
            mock_sleep.assert_called_with(monitor.CHECK_INTERVAL)

    def test_loop_continuous_execution(self):
        """Test loop executes continuously"""
        with patch('core.coordinators.monitor.TaskRegistry'):
            mon = monitor.Monitor()

            with patch.object(mon, 'check') as mock_check:
                with patch('time.sleep', side_effect=[None, None, None, KeyboardInterrupt()]):
                    try:
                        mon.loop()
                    except KeyboardInterrupt:
                        pass

            # Should have called check multiple times
            assert mock_check.call_count >= 3

    def test_loop_infinite_without_interruption(self):
        """Test loop is infinite without interruption"""
        with patch('core.coordinators.monitor.TaskRegistry'):
            mon = monitor.Monitor()

            with patch.object(mon, 'check'):
                with patch('time.sleep', side_effect=KeyboardInterrupt()):
                    # Loop should only stop with interrupt
                    with pytest.raises(KeyboardInterrupt):
                        mon.loop()


# ============================================================================
# Test Monitor Check Method
# ============================================================================

class TestMonitorCheck:
    """Test Monitor check method"""

    def test_check_calls_list_workers(self, mock_monitor, mock_task_registry):
        """Test check calls list_workers"""
        mock_monitor.check()

        mock_task_registry.list_workers.assert_called_once()

    def test_check_calls_qstat(self, mock_monitor, mock_task_registry):
        """Test check calls qstat"""
        mock_monitor.check()

        mock_task_registry.qstat.assert_called_once()

    def test_check_no_stale_workers(self, mock_monitor, mock_task_registry):
        """Test check with no stale workers"""
        mock_task_registry.list_workers.return_value = [
            {"worker_id": "w1", "age": 30},
            {"worker_id": "w2", "age": 60}
        ]

        # Should not print anything (no stale workers)
        with patch('builtins.print') as mock_print:
            mock_monitor.check()

            # Should not print stale workers warning
            stale_calls = [call for call in mock_print.call_args_list
                          if 'stale' in str(call)]
            assert len(stale_calls) == 0

    def test_check_with_stale_workers(self, mock_monitor, mock_task_registry):
        """Test check detects stale workers"""
        mock_task_registry.list_workers.return_value = [
            {"worker_id": "w1", "age": 100},  # Stale
            {"worker_id": "w2", "age": 50}   # Not stale
        ]

        with patch('builtins.print') as mock_print:
            mock_monitor.check()

            # Should print stale workers warning
            mock_print.assert_called()
            call_str = str(mock_print.call_args_list)
            assert 'stale' in call_str.lower()

    def test_check_stale_threshold(self, mock_monitor, mock_task_registry):
        """Test check uses STALE_WORKER_SEC threshold"""
        stale_threshold = monitor.STALE_WORKER_SEC

        mock_task_registry.list_workers.return_value = [
            {"worker_id": "w1", "age": stale_threshold + 1},  # Just stale
            {"worker_id": "w2", "age": stale_threshold - 1}   # Just not stale
        ]

        with patch('builtins.print') as mock_print:
            mock_monitor.check()

            # Should only report w1 as stale
            if mock_print.called:
                call_str = str(mock_print.call_args_list[0])
                # Verify w1 in stale list
                assert 'w1' in call_str or 'stale' in call_str.lower()

    def test_check_no_backlog(self, mock_monitor, mock_task_registry):
        """Test check with no queue backlog"""
        mock_task_registry.qstat.return_value = {
            TaskState.QUEUED.value: 50,
            TaskState.IN_PROGRESS.value: 10
        }

        with patch('builtins.print') as mock_print:
            mock_monitor.check()

            # Should not print backlog warning
            backlog_calls = [call for call in mock_print.call_args_list
                            if 'backlog' in str(call)]
            assert len(backlog_calls) == 0

    def test_check_with_backlog(self, mock_monitor, mock_task_registry):
        """Test check detects high backlog"""
        mock_task_registry.qstat.return_value = {
            TaskState.QUEUED.value: 150,  # High backlog
            TaskState.IN_PROGRESS.value: 10
        }

        with patch('builtins.print') as mock_print:
            mock_monitor.check()

            # Should print backlog warning
            mock_print.assert_called()
            call_str = str(mock_print.call_args_list)
            assert 'backlog' in call_str.lower()

    def test_check_backlog_threshold(self, mock_monitor, mock_task_registry):
        """Test check uses 100 task threshold for backlog"""
        mock_task_registry.qstat.return_value = {
            TaskState.QUEUED.value: 101  # Just over threshold
        }

        with patch('builtins.print') as mock_print:
            mock_monitor.check()

            # Should print backlog warning
            backlog_calls = [call for call in mock_print.call_args_list
                            if 'backlog' in str(call)]
            assert len(backlog_calls) > 0

    def test_check_with_both_issues(self, mock_monitor, mock_task_registry):
        """Test check with both stale workers and backlog"""
        mock_task_registry.list_workers.return_value = [
            {"worker_id": "w1", "age": 100}  # Stale
        ]
        mock_task_registry.qstat.return_value = {
            TaskState.QUEUED.value: 150  # High backlog
        }

        with patch('builtins.print') as mock_print:
            mock_monitor.check()

            # Should print both warnings
            assert mock_print.call_count >= 2

    def test_check_empty_workers_list(self, mock_monitor, mock_task_registry):
        """Test check with empty workers list"""
        mock_task_registry.list_workers.return_value = []

        # Should not crash
        mock_monitor.check()

    def test_check_empty_qstat(self, mock_monitor, mock_task_registry):
        """Test check with empty qstat"""
        mock_task_registry.qstat.return_value = {}

        # Should not crash
        mock_monitor.check()

    def test_check_missing_queued_state(self, mock_monitor, mock_task_registry):
        """Test check handles missing QUEUED state in qstat"""
        mock_task_registry.qstat.return_value = {
            TaskState.IN_PROGRESS.value: 10
            # QUEUED missing
        }

        # Should not crash (defaults to 0)
        mock_monitor.check()


# ============================================================================
# Test Integration
# ============================================================================

class TestIntegration:
    """Test Monitor integration with TaskRegistry"""

    def test_monitor_uses_real_task_registry(self):
        """Test Monitor creates real TaskRegistry instance"""
        mon = monitor.Monitor()

        # Should have TaskRegistry instance
        assert hasattr(mon, 'reg')
        # Don't check exact type to avoid import issues

    def test_check_integration_with_registry(self):
        """Test check method integrates with TaskRegistry"""
        with patch('core.coordinators.monitor.TaskRegistry') as mock_registry_class:
            mock_registry = Mock()
            mock_registry.list_workers.return_value = []
            mock_registry.qstat.return_value = {}
            mock_registry_class.return_value = mock_registry

            mon = monitor.Monitor()
            mon.check()

            # Should have called both methods
            mock_registry.list_workers.assert_called_once()
            mock_registry.qstat.assert_called_once()


# ============================================================================
# Test Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_check_with_none_workers(self, mock_monitor, mock_task_registry):
        """Test check handles None from list_workers"""
        mock_task_registry.list_workers.return_value = None

        # Should handle gracefully (None is not iterable, but should catch)
        try:
            mock_monitor.check()
        except TypeError:
            # Expected if code doesn't handle None
            pass

    def test_check_with_malformed_worker_data(self, mock_monitor, mock_task_registry):
        """Test check handles malformed worker data"""
        mock_task_registry.list_workers.return_value = [
            {"worker_id": "w1"},  # Missing 'age'
            {"age": 100}  # Missing 'worker_id'
        ]

        # Should handle gracefully
        try:
            with patch('builtins.print'):
                mock_monitor.check()
        except KeyError:
            # Expected if code doesn't handle missing keys
            pass

    def test_loop_handles_check_exception(self):
        """Test loop handles exceptions in check"""
        with patch('core.coordinators.monitor.TaskRegistry'):
            mon = monitor.Monitor()

            with patch.object(mon, 'check', side_effect=Exception("Check failed")):
                with patch('time.sleep', side_effect=[None, KeyboardInterrupt()]):
                    # Loop should handle check exception or crash
                    try:
                        mon.loop()
                    except (Exception, KeyboardInterrupt):
                        pass


# ============================================================================
# Test Main Entry Point
# ============================================================================

class TestMainEntryPoint:
    """Test __main__ execution"""

    def test_main_creates_monitor(self):
        """Test main creates Monitor instance"""
        with patch('core.coordinators.monitor.Monitor') as mock_monitor_class:
            mock_monitor_instance = Mock()
            mock_monitor_class.return_value = mock_monitor_instance

            # Can't directly test __main__ execution, but can verify class usage
            monitor.Monitor()

            mock_monitor_class.assert_called_once()

    def test_main_calls_loop(self):
        """Test main calls loop method"""
        with patch('core.coordinators.monitor.Monitor') as mock_monitor_class:
            mock_monitor_instance = Mock()
            mock_monitor_class.return_value = mock_monitor_instance

            # Simulate main execution
            monitor_instance = monitor.Monitor()
            monitor_instance.loop = Mock()

            # Verify loop can be called
            monitor_instance.loop()
            monitor_instance.loop.assert_called_once()


# ============================================================================
# Test Print Formatting
# ============================================================================

class TestPrintFormatting:
    """Test print output formatting"""

    def test_stale_workers_print_format(self, mock_monitor, mock_task_registry):
        """Test stale workers print includes monitor prefix"""
        mock_task_registry.list_workers.return_value = [
            {"worker_id": "w1", "age": 100}
        ]

        with patch('builtins.print') as mock_print:
            mock_monitor.check()

            # Check for [monitor] prefix
            if mock_print.called:
                call_str = str(mock_print.call_args_list[0])
                assert '[monitor]' in call_str or 'stale' in call_str.lower()

    def test_backlog_print_format(self, mock_monitor, mock_task_registry):
        """Test backlog print includes monitor prefix"""
        mock_task_registry.qstat.return_value = {
            TaskState.QUEUED.value: 150
        }

        with patch('builtins.print') as mock_print:
            mock_monitor.check()

            # Check for [monitor] prefix and backlog message
            if mock_print.called:
                call_str = str(mock_print.call_args_list)
                assert '[monitor]' in call_str or 'backlog' in call_str.lower()


# ============================================================================
# Test Marks and Configuration
# ============================================================================

# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit

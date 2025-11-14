"""
Comprehensive unit tests for core/coordinators/health_check.py

Tests cover:
- AgentCoordinatorHealthCheck: Basic and detailed health monitoring
- Individual subsystem health checks (7 different checks)
- AgentCoordinatorHealthServer: HTTP server and route handlers
- Kubernetes probes (liveness, readiness)
- Prometheus metrics generation
- Error handling and edge cases
- Server lifecycle management
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from aiohttp import web

# Import the module under test
from core.coordinators.health_check import (
    AgentCoordinatorHealthCheck,
    AgentCoordinatorHealthServer,
    run_health_server,
)

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator with full agent system"""
    coordinator = Mock()
    coordinator.is_running = Mock(return_value=True)

    # Mock agents
    mock_agent1 = Mock()
    mock_agent1.is_healthy = Mock(return_value=True)
    mock_agent2 = Mock()
    mock_agent2.is_healthy = Mock(return_value=True)

    coordinator.agents = {"agent_1": mock_agent1, "agent_2": mock_agent2}

    # Mock communication
    coordinator.message_queue = []
    coordinator.communication_channels = ["channel_1", "channel_2"]
    coordinator.last_activity = datetime.now(timezone.utc).isoformat()

    # Mock swarms
    mock_swarm = Mock()
    mock_swarm.is_healthy = Mock(return_value=True)
    coordinator.swarms = {"swarm_1": mock_swarm}

    # Mock SPARC manager
    mock_sparc = Mock()
    mock_sparc.active_workflows = []
    coordinator.sparc_manager = mock_sparc

    # Mock task queue
    mock_task_queue = Mock()
    mock_task_queue.pending = []
    mock_task_queue.completed = []
    mock_task_queue.failed = []
    coordinator.task_queue = mock_task_queue

    return coordinator


@pytest.fixture
def health_checker(mock_coordinator):
    """Create health checker with mock coordinator"""
    return AgentCoordinatorHealthCheck(coordinator=mock_coordinator)


@pytest.fixture
def health_checker_no_coordinator():
    """Create health checker without coordinator"""
    return AgentCoordinatorHealthCheck(coordinator=None)


@pytest.fixture
def health_server(mock_coordinator):
    """Create health server with mock coordinator"""
    return AgentCoordinatorHealthServer(coordinator=mock_coordinator, port=8889)


# ============================================================================
# Test AgentCoordinatorHealthCheck Initialization
# ============================================================================


class TestHealthCheckInitialization:
    """Test health check initialization"""

    def test_initialization_with_coordinator(self, mock_coordinator):
        """Test initialization with coordinator reference"""
        checker = AgentCoordinatorHealthCheck(coordinator=mock_coordinator)

        assert checker.coordinator == mock_coordinator
        assert isinstance(checker.start_time, float)
        assert checker.start_time <= time.time()

    def test_initialization_without_coordinator(self):
        """Test initialization without coordinator"""
        checker = AgentCoordinatorHealthCheck(coordinator=None)

        assert checker.coordinator is None
        assert isinstance(checker.start_time, float)

    def test_start_time_tracking(self):
        """Test start time is recorded correctly"""
        before = time.time()
        checker = AgentCoordinatorHealthCheck()
        after = time.time()

        assert before <= checker.start_time <= after


# ============================================================================
# Test Basic Health Check
# ============================================================================


class TestBasicHealthCheck:
    """Test basic health check functionality"""

    @pytest.mark.asyncio
    async def test_basic_health_success(self, health_checker):
        """Test successful basic health check"""
        result = await health_checker.basic_health()

        assert result["status"] == "healthy"
        assert "timestamp" in result
        assert result["service"] == "agent-coordinator"
        assert result["version"] == "1.1.0"
        assert "uptime_seconds" in result
        assert result["process_id"] == os.getpid()
        assert (
            result["python_version"]
            == f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        )

    @pytest.mark.asyncio
    async def test_basic_health_uptime(self, health_checker):
        """Test uptime calculation in basic health"""
        await asyncio.sleep(0.1)  # Wait a bit
        result = await health_checker.basic_health()

        assert result["uptime_seconds"] >= 0.1

    @pytest.mark.asyncio
    async def test_basic_health_timestamp_format(self, health_checker):
        """Test timestamp is in ISO format"""
        result = await health_checker.basic_health()

        # Should be able to parse as ISO timestamp
        timestamp = datetime.fromisoformat(result["timestamp"].replace("Z", "+00:00"))
        assert isinstance(timestamp, datetime)

    @pytest.mark.asyncio
    async def test_basic_health_process_info(self, health_checker):
        """Test process information is included"""
        result = await health_checker.basic_health()

        assert isinstance(result["process_id"], int)
        assert result["process_id"] > 0
        assert "python_version" in result


# ============================================================================
# Test Detailed Health Check
# ============================================================================


class TestDetailedHealthCheck:
    """Test detailed health check functionality"""

    @pytest.mark.asyncio
    async def test_detailed_health_all_healthy(self, health_checker):
        """Test detailed health when all systems healthy"""
        with (
            patch.object(
                health_checker,
                "_check_coordinator_service",
                new=AsyncMock(return_value={"healthy": True}),
            ),
            patch.object(
                health_checker,
                "_check_active_agents",
                new=AsyncMock(return_value={"healthy": True}),
            ),
            patch.object(
                health_checker,
                "_check_agent_communication",
                new=AsyncMock(return_value={"healthy": True}),
            ),
            patch.object(
                health_checker,
                "_check_swarm_coordination",
                new=AsyncMock(return_value={"healthy": True}),
            ),
            patch.object(
                health_checker,
                "_check_sparc_framework",
                new=AsyncMock(return_value={"healthy": True}),
            ),
            patch.object(
                health_checker,
                "_check_task_queue",
                new=AsyncMock(return_value={"healthy": True}),
            ),
            patch.object(
                health_checker,
                "_check_system_resources",
                new=AsyncMock(return_value={"healthy": True}),
            ),
        ):
            result = await health_checker.detailed_health()

            assert result["status"] == "healthy"
            assert "checks" in result
            assert len(result["checks"]) == 7
            assert all(check["healthy"] for check in result["checks"].values())

    @pytest.mark.asyncio
    async def test_detailed_health_one_unhealthy(self, health_checker):
        """Test detailed health when one system unhealthy"""
        with (
            patch.object(
                health_checker,
                "_check_coordinator_service",
                new=AsyncMock(return_value={"healthy": True}),
            ),
            patch.object(
                health_checker,
                "_check_active_agents",
                new=AsyncMock(return_value={"healthy": False}),
            ),
            patch.object(
                health_checker,
                "_check_agent_communication",
                new=AsyncMock(return_value={"healthy": True}),
            ),
            patch.object(
                health_checker,
                "_check_swarm_coordination",
                new=AsyncMock(return_value={"healthy": True}),
            ),
            patch.object(
                health_checker,
                "_check_sparc_framework",
                new=AsyncMock(return_value={"healthy": True}),
            ),
            patch.object(
                health_checker,
                "_check_task_queue",
                new=AsyncMock(return_value={"healthy": True}),
            ),
            patch.object(
                health_checker,
                "_check_system_resources",
                new=AsyncMock(return_value={"healthy": True}),
            ),
        ):
            result = await health_checker.detailed_health()

            assert result["status"] == "unhealthy"
            assert result["checks"]["active_agents"]["healthy"] is False

    @pytest.mark.asyncio
    async def test_detailed_health_includes_duration(self, health_checker):
        """Test detailed health includes check duration"""
        with (
            patch.object(
                health_checker,
                "_check_coordinator_service",
                new=AsyncMock(return_value={"healthy": True}),
            ),
            patch.object(
                health_checker,
                "_check_active_agents",
                new=AsyncMock(return_value={"healthy": True}),
            ),
            patch.object(
                health_checker,
                "_check_agent_communication",
                new=AsyncMock(return_value={"healthy": True}),
            ),
            patch.object(
                health_checker,
                "_check_swarm_coordination",
                new=AsyncMock(return_value={"healthy": True}),
            ),
            patch.object(
                health_checker,
                "_check_sparc_framework",
                new=AsyncMock(return_value={"healthy": True}),
            ),
            patch.object(
                health_checker,
                "_check_task_queue",
                new=AsyncMock(return_value={"healthy": True}),
            ),
            patch.object(
                health_checker,
                "_check_system_resources",
                new=AsyncMock(return_value={"healthy": True}),
            ),
        ):
            result = await health_checker.detailed_health()

            assert "check_duration_ms" in result
            assert isinstance(result["check_duration_ms"], (int, float))
            assert result["check_duration_ms"] >= 0

    @pytest.mark.asyncio
    async def test_detailed_health_includes_uptime(self, health_checker):
        """Test detailed health includes uptime"""
        with (
            patch.object(
                health_checker,
                "_check_coordinator_service",
                new=AsyncMock(return_value={"healthy": True}),
            ),
            patch.object(
                health_checker,
                "_check_active_agents",
                new=AsyncMock(return_value={"healthy": True}),
            ),
            patch.object(
                health_checker,
                "_check_agent_communication",
                new=AsyncMock(return_value={"healthy": True}),
            ),
            patch.object(
                health_checker,
                "_check_swarm_coordination",
                new=AsyncMock(return_value={"healthy": True}),
            ),
            patch.object(
                health_checker,
                "_check_sparc_framework",
                new=AsyncMock(return_value={"healthy": True}),
            ),
            patch.object(
                health_checker,
                "_check_task_queue",
                new=AsyncMock(return_value={"healthy": True}),
            ),
            patch.object(
                health_checker,
                "_check_system_resources",
                new=AsyncMock(return_value={"healthy": True}),
            ),
        ):
            result = await health_checker.detailed_health()

            assert "uptime_seconds" in result
            assert isinstance(result["uptime_seconds"], (int, float))


# ============================================================================
# Test Coordinator Service Check
# ============================================================================


class TestCoordinatorServiceCheck:
    """Test coordinator service health check"""

    @pytest.mark.asyncio
    async def test_check_coordinator_with_reference(self, health_checker):
        """Test coordinator check with direct reference"""
        result = await health_checker._check_coordinator_service()

        assert result["healthy"] is True
        assert result["details"]["service_running"] is True
        assert result["details"]["registered_agents"] == 2

    @pytest.mark.asyncio
    async def test_check_coordinator_not_running(self, health_checker):
        """Test coordinator check when service not running"""
        health_checker.coordinator.is_running = Mock(return_value=False)

        result = await health_checker._check_coordinator_service()

        assert result["healthy"] is False
        assert result["details"]["service_running"] is False

    @pytest.mark.asyncio
    async def test_check_coordinator_without_reference(self, health_checker_no_coordinator):
        """Test coordinator check without direct reference"""
        with patch("socket.socket") as mock_socket:
            mock_sock_instance = MagicMock()
            mock_sock_instance.__enter__ = Mock(return_value=mock_sock_instance)
            mock_sock_instance.__exit__ = Mock(return_value=False)
            mock_sock_instance.connect_ex = Mock(return_value=0)  # Port is open
            mock_socket.return_value = mock_sock_instance

            result = await health_checker_no_coordinator._check_coordinator_service()

            assert result["healthy"] is True
            assert result["details"]["port"] == 8888

    @pytest.mark.asyncio
    async def test_check_coordinator_port_not_open(self, health_checker_no_coordinator):
        """Test coordinator check when port not open"""
        with patch("socket.socket") as mock_socket:
            mock_sock_instance = MagicMock()
            mock_sock_instance.__enter__ = Mock(return_value=mock_sock_instance)
            mock_sock_instance.__exit__ = Mock(return_value=False)
            mock_sock_instance.connect_ex = Mock(return_value=1)  # Port is closed
            mock_socket.return_value = mock_sock_instance

            result = await health_checker_no_coordinator._check_coordinator_service()

            assert result["healthy"] is False

    @pytest.mark.asyncio
    async def test_check_coordinator_exception(self, health_checker):
        """Test coordinator check with exception"""
        health_checker.coordinator.is_running = Mock(side_effect=Exception("Test error"))

        result = await health_checker._check_coordinator_service()

        assert result["healthy"] is False
        assert "error" in result


# ============================================================================
# Test Active Agents Check
# ============================================================================


class TestActiveAgentsCheck:
    """Test active agents health check"""

    @pytest.mark.asyncio
    async def test_check_agents_all_healthy(self, health_checker):
        """Test agents check when all healthy"""
        result = await health_checker._check_active_agents()

        assert result["healthy"] is True
        assert result["details"]["total_agents"] == 2
        assert result["details"]["healthy_agents"] == 2
        assert result["details"]["error_agents"] == 0

    @pytest.mark.asyncio
    async def test_check_agents_one_unhealthy(self, health_checker):
        """Test agents check with one unhealthy agent"""
        health_checker.coordinator.agents["agent_1"].is_healthy = Mock(return_value=False)

        result = await health_checker._check_active_agents()

        assert result["healthy"] is False
        assert result["details"]["healthy_agents"] == 1
        assert result["details"]["error_agents"] == 1

    @pytest.mark.asyncio
    async def test_check_agents_by_type(self, health_checker):
        """Test agents check tracks agent types"""
        health_checker.coordinator.agents["agent_1"].__class__.__name__ = "ContentAgent"
        health_checker.coordinator.agents["agent_2"].__class__.__name__ = "QuizAgent"

        result = await health_checker._check_active_agents()

        assert "ContentAgent" in result["details"]["agent_types"]
        assert "QuizAgent" in result["details"]["agent_types"]

    @pytest.mark.asyncio
    async def test_check_agents_no_coordinator(self, health_checker_no_coordinator):
        """Test agents check without coordinator"""
        result = await health_checker_no_coordinator._check_active_agents()

        assert result["details"]["total_agents"] == 0

    @pytest.mark.asyncio
    async def test_check_agents_no_health_method(self, health_checker):
        """Test agents without is_healthy method assumed healthy"""
        # Create agent without is_healthy method
        mock_agent = Mock(spec=[])  # No methods
        health_checker.coordinator.agents = {"agent_1": mock_agent}

        result = await health_checker._check_active_agents()

        assert result["details"]["healthy_agents"] == 1
        assert result["details"]["error_agents"] == 0

    @pytest.mark.asyncio
    async def test_check_agents_exception(self, health_checker):
        """Test agents check with exception"""
        health_checker.coordinator.agents = {
            "agent_1": Mock(is_healthy=Mock(side_effect=Exception("Test error")))
        }

        result = await health_checker._check_active_agents()

        assert result["healthy"] is False
        assert "error" in result


# ============================================================================
# Test Agent Communication Check
# ============================================================================


class TestAgentCommunicationCheck:
    """Test agent communication health check"""

    @pytest.mark.asyncio
    async def test_check_communication_healthy(self, health_checker):
        """Test communication check when healthy"""
        result = await health_checker._check_agent_communication()

        assert result["healthy"] is True
        assert result["details"]["message_queue_size"] == 0
        assert result["details"]["communication_channels"] == 2

    @pytest.mark.asyncio
    async def test_check_communication_large_queue(self, health_checker):
        """Test communication check with large queue"""
        health_checker.coordinator.message_queue = list(range(1001))  # 1001 messages

        result = await health_checker._check_agent_communication()

        assert result["healthy"] is False
        assert result["details"]["message_queue_size"] == 1001

    @pytest.mark.asyncio
    async def test_check_communication_last_activity(self, health_checker):
        """Test communication check includes last activity"""
        result = await health_checker._check_agent_communication()

        assert result["details"]["last_communication"] is not None

    @pytest.mark.asyncio
    async def test_check_communication_no_coordinator(self, health_checker_no_coordinator):
        """Test communication check without coordinator"""
        result = await health_checker_no_coordinator._check_agent_communication()

        assert result["details"]["message_queue_size"] == 0
        assert result["details"]["communication_channels"] == 0

    @pytest.mark.asyncio
    async def test_check_communication_exception(self, health_checker):
        """Test communication check with exception"""
        health_checker.coordinator.message_queue = Mock(side_effect=Exception("Test error"))

        result = await health_checker._check_agent_communication()

        assert result["healthy"] is False
        assert "error" in result


# ============================================================================
# Test Swarm Coordination Check
# ============================================================================


class TestSwarmCoordinationCheck:
    """Test swarm coordination health check"""

    @pytest.mark.asyncio
    async def test_check_swarm_healthy(self, health_checker):
        """Test swarm check when healthy"""
        result = await health_checker._check_swarm_coordination()

        assert result["healthy"] is True
        assert result["details"]["active_swarms"] == 1
        assert result["details"]["swarm_health"] is True
        assert result["details"]["coordination_errors"] == 0

    @pytest.mark.asyncio
    async def test_check_swarm_unhealthy(self, health_checker):
        """Test swarm check with unhealthy swarm"""
        health_checker.coordinator.swarms["swarm_1"].is_healthy = Mock(return_value=False)

        result = await health_checker._check_swarm_coordination()

        assert result["healthy"] is False
        assert result["details"]["swarm_health"] is False
        assert result["details"]["coordination_errors"] == 1

    @pytest.mark.asyncio
    async def test_check_swarm_multiple_swarms(self, health_checker):
        """Test swarm check with multiple swarms"""
        mock_swarm2 = Mock()
        mock_swarm2.is_healthy = Mock(return_value=True)
        health_checker.coordinator.swarms["swarm_2"] = mock_swarm2

        result = await health_checker._check_swarm_coordination()

        assert result["details"]["active_swarms"] == 2

    @pytest.mark.asyncio
    async def test_check_swarm_no_coordinator(self, health_checker_no_coordinator):
        """Test swarm check without coordinator"""
        result = await health_checker_no_coordinator._check_swarm_coordination()

        assert result["details"]["active_swarms"] == 0

    @pytest.mark.asyncio
    async def test_check_swarm_exception(self, health_checker):
        """Test swarm check with exception"""
        health_checker.coordinator.swarms = {
            "swarm_1": Mock(is_healthy=Mock(side_effect=Exception("Test error")))
        }

        result = await health_checker._check_swarm_coordination()

        assert result["healthy"] is False
        assert "error" in result


# ============================================================================
# Test SPARC Framework Check
# ============================================================================


class TestSPARCFrameworkCheck:
    """Test SPARC framework health check"""

    @pytest.mark.asyncio
    async def test_check_sparc_healthy(self, health_checker):
        """Test SPARC check when healthy"""
        with patch.dict("sys.modules", {"core.sparc.state_manager": Mock()}):
            result = await health_checker._check_sparc_framework()

            assert result["healthy"] is True
            assert result["details"]["framework_loaded"] is True
            assert result["details"]["framework_errors"] == 0

    @pytest.mark.asyncio
    async def test_check_sparc_active_workflows(self, health_checker):
        """Test SPARC check with active workflows"""
        with patch.dict("sys.modules", {"core.sparc.state_manager": Mock()}):
            health_checker.coordinator.sparc_manager.active_workflows = [
                "workflow_1",
                "workflow_2",
            ]

            result = await health_checker._check_sparc_framework()

            assert result["details"]["active_workflows"] == 2

    @pytest.mark.asyncio
    async def test_check_sparc_import_error(self, health_checker):
        """Test SPARC check with import error"""
        with patch.dict("sys.modules", {"core.sparc.state_manager": None}):
            with patch("builtins.__import__", side_effect=ImportError("Module not found")):
                result = await health_checker._check_sparc_framework()

                assert result["healthy"] is False
                assert result["details"]["framework_errors"] == 1

    @pytest.mark.asyncio
    async def test_check_sparc_no_coordinator(self, health_checker_no_coordinator):
        """Test SPARC check without coordinator"""
        with patch.dict("sys.modules", {"core.sparc.state_manager": Mock()}):
            result = await health_checker_no_coordinator._check_sparc_framework()

            assert result["details"]["active_workflows"] == 0

    @pytest.mark.asyncio
    async def test_check_sparc_exception(self, health_checker):
        """Test SPARC check with exception"""
        with patch("builtins.__import__", side_effect=Exception("Test error")):
            result = await health_checker._check_sparc_framework()

            assert result["healthy"] is False
            assert "error" in result


# ============================================================================
# Test Task Queue Check
# ============================================================================


class TestTaskQueueCheck:
    """Test task queue health check"""

    @pytest.mark.asyncio
    async def test_check_queue_healthy(self, health_checker):
        """Test queue check when healthy"""
        result = await health_checker._check_task_queue()

        assert result["healthy"] is True
        assert result["details"]["pending_tasks"] == 0
        assert result["details"]["queue_health"] is True

    @pytest.mark.asyncio
    async def test_check_queue_overloaded(self, health_checker):
        """Test queue check when overloaded"""
        health_checker.coordinator.task_queue.pending = list(range(101))  # 101 tasks

        result = await health_checker._check_task_queue()

        assert result["healthy"] is False
        assert result["details"]["pending_tasks"] == 101
        assert result["details"]["queue_health"] is False

    @pytest.mark.asyncio
    async def test_check_queue_completed_and_failed(self, health_checker):
        """Test queue check tracks completed and failed"""
        health_checker.coordinator.task_queue.completed = ["task_1", "task_2"]
        health_checker.coordinator.task_queue.failed = ["task_3"]

        result = await health_checker._check_task_queue()

        assert result["details"]["completed_tasks"] == 2
        assert result["details"]["failed_tasks"] == 1

    @pytest.mark.asyncio
    async def test_check_queue_no_coordinator(self, health_checker_no_coordinator):
        """Test queue check without coordinator"""
        result = await health_checker_no_coordinator._check_task_queue()

        assert result["details"]["pending_tasks"] == 0

    @pytest.mark.asyncio
    async def test_check_queue_exception(self, health_checker):
        """Test queue check with exception"""
        health_checker.coordinator.task_queue = Mock(side_effect=Exception("Test error"))

        result = await health_checker._check_task_queue()

        assert result["healthy"] is False
        assert "error" in result


# ============================================================================
# Test System Resources Check
# ============================================================================


class TestSystemResourcesCheck:
    """Test system resources health check"""

    @pytest.mark.asyncio
    async def test_check_resources_healthy(self, health_checker):
        """Test resources check when healthy"""
        with (
            patch("psutil.Process") as mock_process,
            patch("psutil.cpu_percent", return_value=50.0),
            patch("psutil.virtual_memory") as mock_memory,
            patch("psutil.disk_usage") as mock_disk,
        ):
            # Mock process metrics
            mock_proc_instance = Mock()
            mock_proc_instance.cpu_percent.return_value = 30.0
            mock_memory_info = Mock()
            mock_memory_info.rss = 500 * 1024 * 1024  # 500 MB
            mock_proc_instance.memory_info.return_value = mock_memory_info
            mock_proc_instance.memory_percent.return_value = 40.0
            mock_process.return_value = mock_proc_instance

            # Mock system metrics
            mock_memory.return_value = Mock(percent=60.0)
            mock_disk.return_value = Mock(
                free=100 * 1024 * 1024 * 1024, total=500 * 1024 * 1024 * 1024
            )  # 100GB free of 500GB

            result = await health_checker._check_system_resources()

            assert result["healthy"] is True
            assert result["details"]["process_cpu_percent"] == 30.0
            assert result["details"]["process_memory_percent"] == 40.0
            assert result["details"]["system_cpu_percent"] == 50.0
            assert result["details"]["system_memory_percent"] == 60.0

    @pytest.mark.asyncio
    async def test_check_resources_high_cpu(self, health_checker):
        """Test resources check with high CPU"""
        with (
            patch("psutil.Process") as mock_process,
            patch("psutil.cpu_percent", return_value=50.0),
            patch("psutil.virtual_memory") as mock_memory,
            patch("psutil.disk_usage") as mock_disk,
        ):
            mock_proc_instance = Mock()
            mock_proc_instance.cpu_percent.return_value = 85.0  # High CPU
            mock_memory_info = Mock()
            mock_memory_info.rss = 500 * 1024 * 1024
            mock_proc_instance.memory_info.return_value = mock_memory_info
            mock_proc_instance.memory_percent.return_value = 40.0
            mock_process.return_value = mock_proc_instance

            mock_memory.return_value = Mock(percent=60.0)
            mock_disk.return_value = Mock(
                free=100 * 1024 * 1024 * 1024, total=500 * 1024 * 1024 * 1024
            )

            result = await health_checker._check_system_resources()

            assert result["healthy"] is False

    @pytest.mark.asyncio
    async def test_check_resources_high_memory(self, health_checker):
        """Test resources check with high memory"""
        with (
            patch("psutil.Process") as mock_process,
            patch("psutil.cpu_percent", return_value=50.0),
            patch("psutil.virtual_memory") as mock_memory,
            patch("psutil.disk_usage") as mock_disk,
        ):
            mock_proc_instance = Mock()
            mock_proc_instance.cpu_percent.return_value = 30.0
            mock_memory_info = Mock()
            mock_memory_info.rss = 500 * 1024 * 1024
            mock_proc_instance.memory_info.return_value = mock_memory_info
            mock_proc_instance.memory_percent.return_value = 85.0  # High memory
            mock_process.return_value = mock_proc_instance

            mock_memory.return_value = Mock(percent=60.0)
            mock_disk.return_value = Mock(
                free=100 * 1024 * 1024 * 1024, total=500 * 1024 * 1024 * 1024
            )

            result = await health_checker._check_system_resources()

            assert result["healthy"] is False

    @pytest.mark.asyncio
    async def test_check_resources_low_disk(self, health_checker):
        """Test resources check with low disk space"""
        with (
            patch("psutil.Process") as mock_process,
            patch("psutil.cpu_percent", return_value=50.0),
            patch("psutil.virtual_memory") as mock_memory,
            patch("psutil.disk_usage") as mock_disk,
        ):
            mock_proc_instance = Mock()
            mock_proc_instance.cpu_percent.return_value = 30.0
            mock_memory_info = Mock()
            mock_memory_info.rss = 500 * 1024 * 1024
            mock_proc_instance.memory_info.return_value = mock_memory_info
            mock_proc_instance.memory_percent.return_value = 40.0
            mock_process.return_value = mock_proc_instance

            mock_memory.return_value = Mock(percent=60.0)
            mock_disk.return_value = Mock(
                free=5 * 1024 * 1024 * 1024, total=500 * 1024 * 1024 * 1024
            )  # Only 5GB free

            result = await health_checker._check_system_resources()

            assert result["healthy"] is False

    @pytest.mark.asyncio
    async def test_check_resources_includes_load_average(self, health_checker):
        """Test resources check includes load average if available"""
        with (
            patch("psutil.Process") as mock_process,
            patch("psutil.cpu_percent", return_value=50.0),
            patch("psutil.virtual_memory") as mock_memory,
            patch("psutil.disk_usage") as mock_disk,
            patch("os.getloadavg", return_value=(1.0, 1.5, 2.0)),
        ):
            mock_proc_instance = Mock()
            mock_proc_instance.cpu_percent.return_value = 30.0
            mock_memory_info = Mock()
            mock_memory_info.rss = 500 * 1024 * 1024
            mock_proc_instance.memory_info.return_value = mock_memory_info
            mock_proc_instance.memory_percent.return_value = 40.0
            mock_process.return_value = mock_proc_instance

            mock_memory.return_value = Mock(percent=60.0)
            mock_disk.return_value = Mock(
                free=100 * 1024 * 1024 * 1024, total=500 * 1024 * 1024 * 1024
            )

            result = await health_checker._check_system_resources()

            assert result["details"]["load_average"] == (1.0, 1.5, 2.0)

    @pytest.mark.asyncio
    async def test_check_resources_exception(self, health_checker):
        """Test resources check with exception"""
        with patch("psutil.Process", side_effect=Exception("Test error")):
            result = await health_checker._check_system_resources()

            assert result["healthy"] is False
            assert "error" in result


# ============================================================================
# Test AgentCoordinatorHealthServer Initialization
# ============================================================================


class TestHealthServerInitialization:
    """Test health server initialization"""

    def test_server_initialization_with_coordinator(self, mock_coordinator):
        """Test server initialization with coordinator"""
        server = AgentCoordinatorHealthServer(coordinator=mock_coordinator, port=8889)

        assert server.coordinator == mock_coordinator
        assert server.port == 8889
        assert isinstance(server.health_checker, AgentCoordinatorHealthCheck)
        assert server.app is None  # Not set up yet

    def test_server_initialization_default_port(self, mock_coordinator):
        """Test server initialization with default port"""
        server = AgentCoordinatorHealthServer(coordinator=mock_coordinator)

        assert server.port == 8889

    def test_server_initialization_custom_port(self, mock_coordinator):
        """Test server initialization with custom port"""
        server = AgentCoordinatorHealthServer(coordinator=mock_coordinator, port=9999)

        assert server.port == 9999

    def test_server_setup_routes(self, health_server):
        """Test route setup"""
        health_server.setup_routes()

        assert health_server.app is not None
        assert isinstance(health_server.app, web.Application)

        # Check routes are registered
        routes = [route.path for route in health_server.app.router.routes()]
        assert "/health" in routes
        assert "/health/detailed" in routes
        assert "/health/agents" in routes
        assert "/health/live" in routes
        assert "/health/ready" in routes
        assert "/metrics" in routes


# ============================================================================
# Test Health Server Route Handlers
# ============================================================================


class TestHealthServerRouteHandlers:
    """Test health server HTTP route handlers"""

    @pytest.mark.asyncio
    async def test_basic_health_handler_success(self, health_server):
        """Test basic health handler returns 200"""
        mock_request = Mock()

        with patch.object(
            health_server.health_checker,
            "basic_health",
            new=AsyncMock(
                return_value={
                    "status": "healthy",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
        ):
            response = await health_server.basic_health_handler(mock_request)

            assert response.status == 200
            body = json.loads(response.body)
            assert body["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_basic_health_handler_exception(self, health_server):
        """Test basic health handler with exception"""
        mock_request = Mock()

        with patch.object(
            health_server.health_checker,
            "basic_health",
            new=AsyncMock(side_effect=Exception("Test error")),
        ):
            response = await health_server.basic_health_handler(mock_request)

            assert response.status == 500
            body = json.loads(response.body)
            assert body["status"] == "error"

    @pytest.mark.asyncio
    async def test_detailed_health_handler_healthy(self, health_server):
        """Test detailed health handler when healthy"""
        mock_request = Mock()

        with patch.object(
            health_server.health_checker,
            "detailed_health",
            new=AsyncMock(return_value={"status": "healthy", "checks": {}}),
        ):
            response = await health_server.detailed_health_handler(mock_request)

            assert response.status == 200

    @pytest.mark.asyncio
    async def test_detailed_health_handler_unhealthy(self, health_server):
        """Test detailed health handler when unhealthy"""
        mock_request = Mock()

        with patch.object(
            health_server.health_checker,
            "detailed_health",
            new=AsyncMock(return_value={"status": "unhealthy", "checks": {}}),
        ):
            response = await health_server.detailed_health_handler(mock_request)

            assert response.status == 503

    @pytest.mark.asyncio
    async def test_agents_health_handler_success(self, health_server):
        """Test agents health handler"""
        mock_request = Mock()

        with patch.object(
            health_server.health_checker,
            "_check_active_agents",
            new=AsyncMock(return_value={"healthy": True, "details": {"total_agents": 2}}),
        ):
            response = await health_server.agents_health_handler(mock_request)

            assert response.status == 200
            body = json.loads(response.body)
            assert body["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_liveness_handler(self, health_server):
        """Test Kubernetes liveness handler"""
        mock_request = Mock()

        response = await health_server.liveness_handler(mock_request)

        assert response.status == 200
        body = json.loads(response.body)
        assert body["status"] == "alive"
        assert body["service"] == "agent-coordinator"

    @pytest.mark.asyncio
    async def test_readiness_handler_ready(self, health_server):
        """Test Kubernetes readiness handler when ready"""
        mock_request = Mock()

        with patch.object(
            health_server.health_checker,
            "detailed_health",
            new=AsyncMock(return_value={"status": "healthy", "checks": {}}),
        ):
            response = await health_server.readiness_handler(mock_request)

            assert response.status == 200
            body = json.loads(response.body)
            assert body["status"] == "ready"

    @pytest.mark.asyncio
    async def test_readiness_handler_not_ready(self, health_server):
        """Test Kubernetes readiness handler when not ready"""
        mock_request = Mock()

        with patch.object(
            health_server.health_checker,
            "detailed_health",
            new=AsyncMock(return_value={"status": "unhealthy", "checks": {}}),
        ):
            response = await health_server.readiness_handler(mock_request)

            assert response.status == 503
            body = json.loads(response.body)
            assert body["status"] == "not_ready"

    @pytest.mark.asyncio
    async def test_readiness_handler_exception(self, health_server):
        """Test readiness handler with exception"""
        mock_request = Mock()

        with patch.object(
            health_server.health_checker,
            "detailed_health",
            new=AsyncMock(side_effect=Exception("Test error")),
        ):
            response = await health_server.readiness_handler(mock_request)

            assert response.status == 503


# ============================================================================
# Test Prometheus Metrics Handler
# ============================================================================


class TestPrometheusMetricsHandler:
    """Test Prometheus metrics generation"""

    @pytest.mark.asyncio
    async def test_metrics_handler_success(self, health_server):
        """Test metrics handler generates Prometheus format"""
        mock_request = Mock()

        with patch.object(
            health_server.health_checker,
            "detailed_health",
            new=AsyncMock(
                return_value={
                    "uptime_seconds": 123.45,
                    "checks": {
                        "active_agents": {
                            "details": {
                                "total_agents": 5,
                                "healthy_agents": 4,
                                "error_agents": 1,
                            }
                        },
                        "task_queue": {
                            "details": {
                                "pending_tasks": 10,
                                "completed_tasks": 50,
                                "failed_tasks": 2,
                            }
                        },
                        "system_resources": {
                            "details": {
                                "process_cpu_percent": 30.0,
                                "process_memory_percent": 40.0,
                            }
                        },
                    },
                }
            ),
        ):
            response = await health_server.metrics_handler(mock_request)

            assert response.status == 200
            assert response.content_type == "text/plain; version=0.0.4; charset=utf-8"

            # Check metrics are in response
            text = response.text
            assert "agent_coordinator_up" in text
            assert "agent_coordinator_uptime_seconds" in text
            assert "agent_coordinator_total_agents" in text
            assert "agent_coordinator_pending_tasks" in text

    @pytest.mark.asyncio
    async def test_metrics_handler_exception(self, health_server):
        """Test metrics handler with exception"""
        mock_request = Mock()

        with patch.object(
            health_server.health_checker,
            "detailed_health",
            new=AsyncMock(side_effect=Exception("Test error")),
        ):
            response = await health_server.metrics_handler(mock_request)

            assert response.status == 500
            assert "# Error generating metrics" in response.text

    @pytest.mark.asyncio
    async def test_metrics_handler_format(self, health_server):
        """Test metrics are in correct Prometheus format"""
        mock_request = Mock()

        with patch.object(
            health_server.health_checker,
            "detailed_health",
            new=AsyncMock(return_value={"uptime_seconds": 100, "checks": {}}),
        ):
            response = await health_server.metrics_handler(mock_request)

            text = response.text
            lines = text.strip().split("\n")

            # Each line should be in format: metric_name {labels} value
            for line in lines:
                if line.strip():
                    assert "{" in line or "}" in line or line.startswith("#")


# ============================================================================
# Test Server Lifecycle
# ============================================================================


class TestHealthServerLifecycle:
    """Test health server lifecycle management"""

    @pytest.mark.asyncio
    async def test_start_server(self, health_server):
        """Test server startup"""
        with (
            patch("aiohttp.web.AppRunner") as mock_runner,
            patch("aiohttp.web.TCPSite") as mock_site,
        ):
            mock_runner_instance = Mock()
            mock_runner_instance.setup = AsyncMock()
            mock_runner.return_value = mock_runner_instance

            mock_site_instance = Mock()
            mock_site_instance.start = AsyncMock()
            mock_site.return_value = mock_site_instance

            await health_server.start_server()

            assert health_server.app is not None
            mock_runner_instance.setup.assert_called_once()
            mock_site_instance.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_health_server_with_interrupt(self):
        """Test run_health_server handles KeyboardInterrupt"""
        mock_coordinator = Mock()

        with patch(
            "core.coordinators.health_check.AgentCoordinatorHealthServer"
        ) as mock_server_class:
            mock_server = Mock()
            mock_runner = Mock()
            mock_runner.cleanup = AsyncMock()
            mock_server.start_server = AsyncMock(return_value=mock_runner)
            mock_server_class.return_value = mock_server

            # Simulate KeyboardInterrupt after short delay
            async def sleep_then_interrupt(duration):
                if duration == 1:
                    raise KeyboardInterrupt()
                await asyncio.sleep(duration)

            with patch("asyncio.sleep", side_effect=sleep_then_interrupt):
                await run_health_server(coordinator=mock_coordinator, port=8889)

            mock_runner.cleanup.assert_called_once()


# ============================================================================
# Test Edge Cases and Error Handling
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_health_check_with_none_coordinator(self):
        """Test health check with None coordinator"""
        checker = AgentCoordinatorHealthCheck(coordinator=None)

        # Should not raise exception
        result = await checker.basic_health()
        assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_with_missing_attributes(self):
        """Test health check with coordinator missing expected attributes"""
        coordinator = Mock(spec=[])  # No attributes
        checker = AgentCoordinatorHealthCheck(coordinator=coordinator)

        # Should handle gracefully
        result = await checker.detailed_health()
        assert "status" in result

    @pytest.mark.asyncio
    async def test_concurrent_health_checks(self, health_checker):
        """Test multiple concurrent health checks"""
        # Run multiple checks concurrently
        tasks = [health_checker.basic_health() for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # All should succeed
        assert len(results) == 10
        assert all(r["status"] == "healthy" for r in results)

    @pytest.mark.asyncio
    async def test_uptime_increases_over_time(self, health_checker):
        """Test uptime calculation increases"""
        result1 = await health_checker.basic_health()
        uptime1 = result1["uptime_seconds"]

        await asyncio.sleep(0.1)

        result2 = await health_checker.basic_health()
        uptime2 = result2["uptime_seconds"]

        assert uptime2 > uptime1


# ============================================================================
# Test Data Classes and Helpers
# ============================================================================


class TestDataClasses:
    """Test data classes and helper functions"""

    def test_health_checker_start_time_precision(self):
        """Test start time has sufficient precision"""
        checker = AgentCoordinatorHealthCheck()

        # Should be float with microsecond precision
        assert isinstance(checker.start_time, float)
        assert checker.start_time > 0

    @pytest.mark.asyncio
    async def test_timestamp_format_consistency(self, health_checker):
        """Test all timestamps use consistent ISO format"""
        basic = await health_checker.basic_health()

        with (
            patch.object(
                health_checker,
                "_check_coordinator_service",
                new=AsyncMock(return_value={"healthy": True}),
            ),
            patch.object(
                health_checker,
                "_check_active_agents",
                new=AsyncMock(return_value={"healthy": True}),
            ),
            patch.object(
                health_checker,
                "_check_agent_communication",
                new=AsyncMock(return_value={"healthy": True}),
            ),
            patch.object(
                health_checker,
                "_check_swarm_coordination",
                new=AsyncMock(return_value={"healthy": True}),
            ),
            patch.object(
                health_checker,
                "_check_sparc_framework",
                new=AsyncMock(return_value={"healthy": True}),
            ),
            patch.object(
                health_checker,
                "_check_task_queue",
                new=AsyncMock(return_value={"healthy": True}),
            ),
            patch.object(
                health_checker,
                "_check_system_resources",
                new=AsyncMock(return_value={"healthy": True}),
            ),
        ):
            detailed = await health_checker.detailed_health()

        # Both should have parseable timestamps
        basic_ts = datetime.fromisoformat(basic["timestamp"].replace("Z", "+00:00"))
        detailed_ts = datetime.fromisoformat(detailed["timestamp"].replace("Z", "+00:00"))

        assert isinstance(basic_ts, datetime)
        assert isinstance(detailed_ts, datetime)


# ============================================================================
# Test Marks and Configuration
# ============================================================================

# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit

"""
Unit tests for Coordinator Service

Tests coordinator service initialization, content generation orchestration,
health status monitoring, Pusher notifications, and service lifecycle.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import json

from apps.backend.services.coordinator_service import (
    CoordinatorService,
    get_coordinator
)


@pytest.fixture
def mock_redis_client():
    """Mock Redis async client"""
    client = AsyncMock()
    client.ping = AsyncMock(return_value=True)
    client.hset = AsyncMock()
    client.hdel = AsyncMock()
    client.expire = AsyncMock()
    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_main_coordinator():
    """Mock MainCoordinator"""
    coordinator = AsyncMock()
    coordinator.initialize = AsyncMock()
    coordinator.shutdown = AsyncMock()
    coordinator.generate_educational_content = AsyncMock()
    coordinator.get_health_status = AsyncMock()
    return coordinator


@pytest.fixture
def mock_pusher_service():
    """Mock Pusher service"""
    service = AsyncMock()
    service.trigger = AsyncMock()
    return service


@pytest.fixture
def mock_langchain_tracer():
    """Mock LangChain tracer"""
    tracer = MagicMock()
    tracer.__enter__ = Mock(return_value=tracer)
    tracer.__exit__ = Mock(return_value=False)
    return tracer


@pytest.fixture
def coordinator_service_with_mocks(
    mock_redis_client,
    mock_main_coordinator,
    mock_pusher_service,
    mock_langchain_tracer
):
    """CoordinatorService with all dependencies mocked"""
    with patch('apps.backend.services.coordinator_service.redis.from_url', return_value=mock_redis_client):
        with patch('apps.backend.services.coordinator_service.MainCoordinator', return_value=mock_main_coordinator):
            with patch('apps.backend.services.coordinator_service.WorkflowCoordinator', return_value=AsyncMock()):
                with patch('apps.backend.services.coordinator_service.ResourceCoordinator', return_value=AsyncMock()):
                    with patch('apps.backend.services.coordinator_service.SyncCoordinator', return_value=AsyncMock()):
                        with patch('apps.backend.services.coordinator_service.ErrorCoordinator', return_value=AsyncMock()):
                            with patch('apps.backend.services.coordinator_service.pusher_service', mock_pusher_service):
                                with patch('apps.backend.services.coordinator_service.LangChainTracer', return_value=mock_langchain_tracer):
                                    with patch('apps.backend.services.coordinator_service.Client', return_value=AsyncMock()):
                                        service = CoordinatorService()
                                        service.redis_client = mock_redis_client
                                        service.main_coordinator = mock_main_coordinator
                                        return service


@pytest.mark.unit
class TestCoordinatorServiceInitialization:
    """Test coordinator service initialization"""

    def test_coordinator_service_construction(self):
        """Test coordinator service construction"""
        with patch('apps.backend.services.coordinator_service.MainCoordinator', return_value=AsyncMock()):
            with patch('apps.backend.services.coordinator_service.WorkflowCoordinator', return_value=AsyncMock()):
                with patch('apps.backend.services.coordinator_service.ResourceCoordinator', return_value=AsyncMock()):
                    with patch('apps.backend.services.coordinator_service.SyncCoordinator', return_value=AsyncMock()):
                        with patch('apps.backend.services.coordinator_service.ErrorCoordinator', return_value=AsyncMock()):
                            with patch('apps.backend.services.coordinator_service.LangChainTracer', return_value=MagicMock()):
                                with patch('apps.backend.services.coordinator_service.Client', return_value=AsyncMock()):
                                    service = CoordinatorService()

        assert service.is_initialized is False
        assert service.redis_url == "redis://localhost:55007/2"
        assert service.workflow_coordinator is not None
        assert service.resource_coordinator is not None
        assert service.sync_coordinator is not None
        assert service.error_coordinator is not None
        assert service.main_coordinator is not None

    @pytest.mark.asyncio
    async def test_initialize_success(self, coordinator_service_with_mocks, mock_redis_client, mock_main_coordinator, mock_pusher_service):
        """Test successful service initialization"""
        service = coordinator_service_with_mocks

        await service.initialize()

        assert service.is_initialized is True
        mock_redis_client.ping.assert_awaited_once()
        mock_main_coordinator.initialize.assert_awaited_once()
        mock_redis_client.hset.assert_awaited()
        mock_redis_client.expire.assert_awaited()
        mock_pusher_service.trigger.assert_awaited()

    @pytest.mark.asyncio
    async def test_initialize_redis_connection_failure(self, coordinator_service_with_mocks, mock_redis_client):
        """Test initialization with Redis connection failure"""
        service = coordinator_service_with_mocks
        mock_redis_client.ping.side_effect = Exception("Redis connection failed")

        with pytest.raises(Exception) as exc_info:
            await service.initialize()

        assert "Redis connection failed" in str(exc_info.value)
        assert service.is_initialized is False

    @pytest.mark.asyncio
    async def test_initialize_coordinator_failure(self, coordinator_service_with_mocks, mock_main_coordinator):
        """Test initialization with coordinator initialization failure"""
        service = coordinator_service_with_mocks
        mock_main_coordinator.initialize.side_effect = Exception("Coordinator init failed")

        with pytest.raises(Exception) as exc_info:
            await service.initialize()

        assert "Coordinator init failed" in str(exc_info.value)
        assert service.is_initialized is False


@pytest.mark.unit
class TestServiceRegistration:
    """Test service registration in Redis"""

    @pytest.mark.asyncio
    async def test_register_service_success(self, coordinator_service_with_mocks, mock_redis_client):
        """Test successful service registration in Redis"""
        service = coordinator_service_with_mocks

        await service._register_service()

        # Verify service info was registered
        mock_redis_client.hset.assert_awaited_once()
        call_args = mock_redis_client.hset.call_args
        assert call_args[0][0] == "services:registry"
        assert call_args[0][1] == "coordinator-service"

        # Verify service info structure
        service_info = json.loads(call_args[0][2])
        assert service_info["name"] == "coordinator-service"
        assert service_info["type"] == "orchestration"
        assert service_info["status"] == "active"
        assert "agent-orchestration" in service_info["capabilities"]
        assert service_info["langchain_enabled"] is True
        assert service_info["pusher_enabled"] is True

        # Verify expiry was set
        mock_redis_client.expire.assert_awaited_once()


@pytest.mark.unit
class TestPusherNotifications:
    """Test Pusher notification integration"""

    @pytest.mark.asyncio
    async def test_notify_initialization_success(self, coordinator_service_with_mocks, mock_pusher_service):
        """Test successful initialization notification via Pusher"""
        service = coordinator_service_with_mocks

        await service._notify_initialization()

        mock_pusher_service.trigger.assert_awaited_once()
        call_args = mock_pusher_service.trigger.call_args
        assert call_args[1]["channel"] == "private-system"
        assert call_args[1]["event"] == "coordinator.initialized"
        assert "coordinator-service" in str(call_args[1]["data"])

    @pytest.mark.asyncio
    async def test_notify_initialization_failure_handled(self, coordinator_service_with_mocks, mock_pusher_service):
        """Test initialization notification failure is handled gracefully"""
        service = coordinator_service_with_mocks
        mock_pusher_service.trigger.side_effect = Exception("Pusher error")

        # Should not raise exception
        await service._notify_initialization()

        mock_pusher_service.trigger.assert_awaited_once()


@pytest.mark.unit
class TestContentGeneration:
    """Test educational content generation orchestration"""

    @pytest.mark.asyncio
    async def test_generate_content_success(self, coordinator_service_with_mocks, mock_main_coordinator, mock_pusher_service, mock_langchain_tracer):
        """Test successful content generation"""
        service = coordinator_service_with_mocks
        service.is_initialized = True

        # Mock generation result
        mock_result = Mock()
        mock_result.success = True
        mock_result.request_id = "req_123"
        mock_result.content = {"title": "Math Lesson"}
        mock_result.scripts = ["script1.lua"]
        mock_result.quiz_data = {"question1": "What is 2+2?"}
        mock_result.metrics = {"generation_time": 5.0}
        mock_result.generation_time = 5.0

        mock_main_coordinator.generate_educational_content.return_value = mock_result

        result = await service.generate_educational_content(
            subject="Mathematics",
            grade_level=5,
            learning_objectives=["Learn addition", "Learn subtraction"]
        )

        assert result["success"] is True
        assert result["content"] == {"title": "Math Lesson"}
        assert result["scripts"] == ["script1.lua"]

        # Verify Pusher events
        assert mock_pusher_service.trigger.await_count == 2  # start + complete

    @pytest.mark.asyncio
    async def test_generate_content_not_initialized(self, coordinator_service_with_mocks):
        """Test content generation when service not initialized"""
        service = coordinator_service_with_mocks
        service.is_initialized = False

        with pytest.raises(RuntimeError) as exc_info:
            await service.generate_educational_content(
                subject="Math",
                grade_level=5,
                learning_objectives=["Objective 1"]
            )

        assert "not initialized" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_content_with_custom_parameters(self, coordinator_service_with_mocks, mock_main_coordinator):
        """Test content generation with custom parameters"""
        service = coordinator_service_with_mocks
        service.is_initialized = True

        mock_result = Mock()
        mock_result.success = True
        mock_result.request_id = "req_456"
        mock_result.content = {}
        mock_result.scripts = []
        mock_result.quiz_data = {}
        mock_result.metrics = {}
        mock_result.generation_time = 3.0

        mock_main_coordinator.generate_educational_content.return_value = mock_result

        custom_params = {"difficulty": "advanced", "style": "interactive"}

        result = await service.generate_educational_content(
            subject="Science",
            grade_level=8,
            learning_objectives=["Objective 1"],
            environment_type="virtual_lab",
            include_quiz=False,
            custom_parameters=custom_params
        )

        assert result["success"] is True
        mock_main_coordinator.generate_educational_content.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_generate_content_coordinator_failure(self, coordinator_service_with_mocks, mock_main_coordinator, mock_pusher_service):
        """Test content generation with coordinator failure"""
        service = coordinator_service_with_mocks
        service.is_initialized = True

        mock_main_coordinator.generate_educational_content.side_effect = Exception("Generation failed")

        with pytest.raises(Exception) as exc_info:
            await service.generate_educational_content(
                subject="Math",
                grade_level=5,
                learning_objectives=["Objective 1"]
            )

        assert "Generation failed" in str(exc_info.value)

        # Verify error event was sent
        error_calls = [call for call in mock_pusher_service.trigger.await_args_list
                      if "generation.error" in str(call)]
        assert len(error_calls) > 0


@pytest.mark.unit
class TestHealthStatus:
    """Test health status monitoring"""

    @pytest.mark.asyncio
    async def test_get_health_status_success(self, coordinator_service_with_mocks, mock_main_coordinator):
        """Test successful health status retrieval"""
        service = coordinator_service_with_mocks
        service.is_initialized = True

        # Mock health response
        mock_health = Mock()
        mock_health.status = "healthy"
        mock_health.timestamp = datetime.now()
        mock_health.component_health = {
            "workflow": "healthy",
            "resource": "healthy",
            "sync": "healthy",
            "error": "healthy"
        }
        mock_health.active_workflows = 3
        mock_health.resource_utilization = 0.45
        mock_health.error_count = 0
        mock_health.last_error = None

        mock_main_coordinator.get_health_status.return_value = mock_health

        health = await service.get_health_status()

        assert health["status"] == "healthy"
        assert health["healthy"] is True
        assert health["active_workflows"] == 3
        assert health["error_count"] == 0

    @pytest.mark.asyncio
    async def test_get_health_status_not_initialized(self, coordinator_service_with_mocks):
        """Test health status when service not initialized"""
        service = coordinator_service_with_mocks
        service.is_initialized = False

        health = await service.get_health_status()

        assert health["status"] == "not_initialized"
        assert health["healthy"] is False

    @pytest.mark.asyncio
    async def test_get_health_status_degraded(self, coordinator_service_with_mocks, mock_main_coordinator):
        """Test health status when system degraded"""
        service = coordinator_service_with_mocks
        service.is_initialized = True

        mock_health = Mock()
        mock_health.status = "degraded"
        mock_health.timestamp = datetime.now()
        mock_health.component_health = {
            "workflow": "healthy",
            "resource": "unhealthy",
            "sync": "healthy",
            "error": "healthy"
        }
        mock_health.active_workflows = 1
        mock_health.resource_utilization = 0.85
        mock_health.error_count = 5
        mock_health.last_error = "Resource allocation failed"

        mock_main_coordinator.get_health_status.return_value = mock_health

        health = await service.get_health_status()

        assert health["status"] == "degraded"
        assert health["healthy"] is False
        assert health["error_count"] == 5
        assert "Resource allocation failed" in health["last_error"]

    @pytest.mark.asyncio
    async def test_get_health_status_exception(self, coordinator_service_with_mocks, mock_main_coordinator):
        """Test health status with exception"""
        service = coordinator_service_with_mocks
        service.is_initialized = True

        mock_main_coordinator.get_health_status.side_effect = Exception("Health check failed")

        health = await service.get_health_status()

        assert health["status"] == "error"
        assert health["healthy"] is False
        assert "Health check failed" in health["error"]


@pytest.mark.unit
class TestServiceShutdown:
    """Test service shutdown and cleanup"""

    @pytest.mark.asyncio
    async def test_shutdown_success(self, coordinator_service_with_mocks, mock_main_coordinator, mock_redis_client, mock_pusher_service):
        """Test successful service shutdown"""
        service = coordinator_service_with_mocks
        service.is_initialized = True

        await service.shutdown()

        assert service.is_initialized is False
        mock_main_coordinator.shutdown.assert_awaited_once()
        mock_redis_client.hdel.assert_awaited_once_with("services:registry", "coordinator-service")
        mock_redis_client.close.assert_awaited_once()
        mock_pusher_service.trigger.assert_awaited()

    @pytest.mark.asyncio
    async def test_shutdown_with_coordinator_error(self, coordinator_service_with_mocks, mock_main_coordinator):
        """Test shutdown with coordinator shutdown error"""
        service = coordinator_service_with_mocks
        service.is_initialized = True

        mock_main_coordinator.shutdown.side_effect = Exception("Shutdown error")

        # Should not raise exception
        await service.shutdown()

    @pytest.mark.asyncio
    async def test_shutdown_without_redis_client(self, coordinator_service_with_mocks):
        """Test shutdown when Redis client not available"""
        service = coordinator_service_with_mocks
        service.is_initialized = True
        service.redis_client = None

        # Should not raise exception
        await service.shutdown()


@pytest.mark.unit
class TestLangChainConfiguration:
    """Test LangChain configuration"""

    def test_configure_langchain_sets_defaults(self):
        """Test LangChain configuration sets default values"""
        with patch('apps.backend.services.coordinator_service.os.getenv') as mock_getenv:
            with patch('apps.backend.services.coordinator_service.os.environ', {}) as mock_environ:
                with patch('apps.backend.services.coordinator_service.MainCoordinator', return_value=AsyncMock()):
                    with patch('apps.backend.services.coordinator_service.WorkflowCoordinator', return_value=AsyncMock()):
                        with patch('apps.backend.services.coordinator_service.ResourceCoordinator', return_value=AsyncMock()):
                            with patch('apps.backend.services.coordinator_service.SyncCoordinator', return_value=AsyncMock()):
                                with patch('apps.backend.services.coordinator_service.ErrorCoordinator', return_value=AsyncMock()):
                                    with patch('apps.backend.services.coordinator_service.LangChainTracer', return_value=MagicMock()):
                                        with patch('apps.backend.services.coordinator_service.Client', return_value=AsyncMock()):
                                            mock_getenv.return_value = None

                                            service = CoordinatorService()

                                            # Verify defaults were set
                                            assert "LANGCHAIN_PROJECT" in mock_environ
                                            assert "LANGCHAIN_TRACING_V2" in mock_environ
                                            assert "LANGCHAIN_ENDPOINT" in mock_environ

    def test_configure_langchain_warns_missing_api_key(self):
        """Test warning when LANGCHAIN_API_KEY missing"""
        with patch('apps.backend.services.coordinator_service.os.getenv', return_value=None):
            with patch('apps.backend.services.coordinator_service.logger') as mock_logger:
                with patch('apps.backend.services.coordinator_service.MainCoordinator', return_value=AsyncMock()):
                    with patch('apps.backend.services.coordinator_service.WorkflowCoordinator', return_value=AsyncMock()):
                        with patch('apps.backend.services.coordinator_service.ResourceCoordinator', return_value=AsyncMock()):
                            with patch('apps.backend.services.coordinator_service.SyncCoordinator', return_value=AsyncMock()):
                                with patch('apps.backend.services.coordinator_service.ErrorCoordinator', return_value=AsyncMock()):
                                    with patch('apps.backend.services.coordinator_service.LangChainTracer', return_value=MagicMock()):
                                        with patch('apps.backend.services.coordinator_service.Client', return_value=AsyncMock()):
                                            service = CoordinatorService()

                                            # Verify warning was logged
                                            mock_logger.warning.assert_called()


@pytest.mark.unit
class TestGlobalServiceInstance:
    """Test global singleton service instance"""

    @pytest.mark.asyncio
    async def test_get_coordinator_creates_instance(self, mock_redis_client, mock_main_coordinator, mock_pusher_service):
        """Test get_coordinator creates singleton instance"""
        with patch('apps.backend.services.coordinator_service.coordinator_service', None):
            with patch('apps.backend.services.coordinator_service.redis.from_url', return_value=mock_redis_client):
                with patch('apps.backend.services.coordinator_service.MainCoordinator', return_value=mock_main_coordinator):
                    with patch('apps.backend.services.coordinator_service.WorkflowCoordinator', return_value=AsyncMock()):
                        with patch('apps.backend.services.coordinator_service.ResourceCoordinator', return_value=AsyncMock()):
                            with patch('apps.backend.services.coordinator_service.SyncCoordinator', return_value=AsyncMock()):
                                with patch('apps.backend.services.coordinator_service.ErrorCoordinator', return_value=AsyncMock()):
                                    with patch('apps.backend.services.coordinator_service.pusher_service', mock_pusher_service):
                                        with patch('apps.backend.services.coordinator_service.LangChainTracer', return_value=MagicMock()):
                                            with patch('apps.backend.services.coordinator_service.Client', return_value=AsyncMock()):
                                                coordinator = await get_coordinator()

        assert coordinator is not None
        assert isinstance(coordinator, CoordinatorService)

    @pytest.mark.asyncio
    async def test_get_coordinator_returns_same_instance(self, mock_redis_client, mock_main_coordinator, mock_pusher_service):
        """Test get_coordinator returns same singleton instance"""
        with patch('apps.backend.services.coordinator_service.redis.from_url', return_value=mock_redis_client):
            with patch('apps.backend.services.coordinator_service.MainCoordinator', return_value=mock_main_coordinator):
                with patch('apps.backend.services.coordinator_service.WorkflowCoordinator', return_value=AsyncMock()):
                    with patch('apps.backend.services.coordinator_service.ResourceCoordinator', return_value=AsyncMock()):
                        with patch('apps.backend.services.coordinator_service.SyncCoordinator', return_value=AsyncMock()):
                            with patch('apps.backend.services.coordinator_service.ErrorCoordinator', return_value=AsyncMock()):
                                with patch('apps.backend.services.coordinator_service.pusher_service', mock_pusher_service):
                                    with patch('apps.backend.services.coordinator_service.LangChainTracer', return_value=MagicMock()):
                                        with patch('apps.backend.services.coordinator_service.Client', return_value=AsyncMock()):
                                            # Reset global instance
                                            import apps.backend.services.coordinator_service as cs_module
                                            cs_module.coordinator_service = None

                                            coordinator1 = await get_coordinator()
                                            coordinator2 = await get_coordinator()

        assert coordinator1 is coordinator2

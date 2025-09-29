import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest_asyncio

import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_db_connection():
    """Mock database connection for tests"""
    with patch('psycopg2.connect') as mock_connect:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        yield mock_conn

"""
Integration Test for Agent Swarm Startup

Tests that the integration agents initialize correctly with the backend server.
"""

import pytest
import asyncio
import os
from unittest.mock import patch, MagicMock
from datetime import datetime


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_manager_initialization():
    """Test that the integration manager can be initialized"""
    # Set environment to skip actual service connections in test
    os.environ['SKIP_INTEGRATION_AGENTS'] = 'false'

    # Mock external services to avoid actual connections in tests
    with patch('database.connection.DatabaseManager') as mock_db, \
         patch('redis.asyncio.from_url') as mock_redis, \
         patch('apps.backend.services.integration_agents.get_pusher_service') as mock_pusher:

        # Setup mocks
        mock_db_instance = MagicMock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.initialize = MagicMock(return_value=asyncio.Future())
        mock_db_instance.initialize.return_value.set_result(None)

        mock_redis.return_value = MagicMock()
        mock_pusher.return_value = MagicMock()

        # Import after setting environment
        from apps.backend.services.integration_agents import IntegrationAgentsManager

        # Create manager instance
        manager = IntegrationAgentsManager()

        # Initialize
        await manager.initialize()

        # Verify initialization
        assert manager.initialized == True
        assert len(manager.agents) > 0
        assert 'api_gateway' in manager.agents
        assert 'database_sync' in manager.agents
        assert 'ui_sync' in manager.agents
        assert 'realtime_update' in manager.agents
        assert 'studio_bridge' in manager.agents
        assert 'schema_validator' in manager.agents
        assert manager.coordinator is not None

        # Cleanup
        await manager.shutdown()


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_endpoints_available():
    """Test that integration endpoints are properly registered"""
    from apps.backend.api.v1.endpoints.integration import router

    # Check that router has endpoints
    endpoint_paths = set()
    for route in router.routes:
        if hasattr(route, 'path'):
            endpoint_paths.add(route.path)

    # Verify key endpoints exist (they have the /integration prefix)
    assert '/integration/status' in endpoint_paths
    assert '/integration/agents' in endpoint_paths
    assert '/integration/workflow/create' in endpoint_paths
    assert '/integration/schema/register' in endpoint_paths
    assert '/integration/sync/trigger' in endpoint_paths
    assert '/integration/event/broadcast' in endpoint_paths
    assert '/integration/health/check' in endpoint_paths
    assert '/integration/metrics' in endpoint_paths


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_status_endpoint_response():
    """Test the agent status endpoint returns expected structure"""
    from apps.backend.services.integration_agents import IntegrationAgentsManager

    # Create manager
    manager = IntegrationAgentsManager()

    # Get status without initialization (should show not initialized)
    status = await manager.get_agent_status()

    assert 'initialized' in status
    assert status['initialized'] == False
    assert 'timestamp' in status
    assert 'agents' in status


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.asyncio
async def test_workflow_execution_structure():
    """Test workflow execution returns expected structure"""
    from apps.backend.services.integration_agents import IntegrationAgentsManager

    manager = IntegrationAgentsManager()

    # Mock coordinator to avoid actual workflow execution
    with patch.object(manager, 'coordinator') as mock_coordinator:
        # Setup mock workflow
        mock_workflow = MagicMock()
        mock_workflow.workflow_id = "test-workflow-123"

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.output = {"test": "output"}
        mock_result.error = None

        mock_coordinator.create_workflow.return_value = asyncio.Future()
        mock_coordinator.create_workflow.return_value.set_result(mock_workflow)

        mock_coordinator.execute_workflow.return_value = asyncio.Future()
        mock_coordinator.execute_workflow.return_value.set_result(mock_result)

        # Execute workflow
        result = await manager.execute_workflow(
            workflow_name="test-workflow",
            workflow_description="Test workflow",
            parameters={"test": "param"}
        )

        # Verify structure
        assert 'workflow_id' in result
        assert 'success' in result
        assert 'output' in result
        assert result['success'] == True
        assert result['workflow_id'] == "test-workflow-123"


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.asyncio
async def test_all_agents_import():
    """Test that all integration agents can be imported"""
    agents_to_test = [
        ('core.agents.integration.backend', 'APIGatewayAgent'),
        ('core.agents.integration.backend', 'DatabaseSyncAgent'),
        ('core.agents.integration.frontend', 'UISyncAgent'),
        ('core.agents.integration.frontend', 'RealtimeUpdateAgent'),
        ('core.agents.integration.roblox', 'StudioBridgeAgent'),
        ('core.agents.integration.orchestration', 'IntegrationCoordinator'),
        ('core.agents.integration.data_flow', 'SchemaValidatorAgent'),
    ]

    for module_name, class_name in agents_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            assert cls is not None, f"Failed to get class {class_name} from {module_name}"
        except ImportError as e:
            pytest.fail(f"Failed to import {class_name} from {module_name}: {e}")


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.asyncio
async def test_circuit_breaker_functionality():
    """Test that circuit breaker pattern works in base agent"""
    from core.agents.integration.base_integration_agent import CircuitBreaker, CircuitBreakerState

    breaker = CircuitBreaker(failure_threshold=3)

    # Initially closed
    assert breaker.state == CircuitBreakerState.CLOSED
    assert breaker.can_execute() == True

    # Record failures
    for _ in range(3):
        breaker.record_failure()

    # Should be open after threshold
    assert breaker.state == CircuitBreakerState.OPEN
    assert breaker.can_execute() == False

    # Record success when half-open
    breaker.state = CircuitBreakerState.HALF_OPEN
    breaker.record_success()
    breaker.record_success()
    breaker.record_success()

    # Should be closed again
    assert breaker.state == CircuitBreakerState.CLOSED


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_event_model():
    """Test the IntegrationEvent model structure"""
    from core.agents.integration import IntegrationEvent, IntegrationPlatform

    event = IntegrationEvent(
        event_id="test-123",
        event_type="test_event",
        source_platform=IntegrationPlatform.BACKEND,
        target_platform=IntegrationPlatform.FRONTEND,
        payload={"test": "data"}
    )

    assert event.event_id == "test-123"
    assert event.event_type == "test_event"
    assert event.source_platform == IntegrationPlatform.BACKEND
    assert event.target_platform == IntegrationPlatform.FRONTEND
    assert event.payload == {"test": "data"}
    assert event.retry_count == 0
    assert event.max_retries == 3
    assert isinstance(event.timestamp, datetime)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
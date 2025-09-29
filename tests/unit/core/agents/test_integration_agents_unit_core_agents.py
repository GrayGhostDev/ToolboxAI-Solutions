import pytest_asyncio
"""
Unit tests for Integration Agent Swarm

Tests the basic functionality of the integration agents including:
- Base integration agent capabilities
- API Gateway agent endpoint management
- Database sync agent operations
- Integration coordinator workflow execution
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch

from core.agents.integration import (
    BaseIntegrationAgent,
    IntegrationPlatform,
    IntegrationEvent,
    CircuitBreaker,
    CircuitBreakerState
)
from core.agents.integration.backend import APIGatewayAgent, APIEndpoint, APIVersion
# DatabaseSyncAgent and SyncStrategy not currently exported
# from core.agents.integration.backend import DatabaseSyncAgent, SyncStrategy

# Mock these for now
class SyncStrategy:
    FULL_SYNC = "full_sync"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"

class DatabaseSyncAgent:
    pass
from core.agents.integration.orchestration import (
    IntegrationCoordinator,
    IntegrationWorkflow,
    IntegrationTask,
    WorkflowStatus,
    TaskPriority
)


class TestBaseIntegrationAgent:
    """Test base integration agent functionality"""

    @pytest.fixture
    def agent(self):
        """Create a test implementation of base integration agent"""

        class TestIntegrationAgent(BaseIntegrationAgent):
            """Concrete test implementation"""

            async def _process_integration_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
                """Test implementation of abstract method"""
                return {"processed": True, "event": event}

            async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
                """Test implementation of process_task"""
                return {"success": True, "task": task}

        return TestIntegrationAgent()

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_circuit_breaker(self, agent):
        """Test circuit breaker functionality"""
        # Test normal operation
        breaker = CircuitBreaker(failure_threshold=3)
        assert breaker.state == CircuitBreakerState.CLOSED
        assert breaker.can_execute()

        # Record failures
        for _ in range(3):
            breaker.record_failure()

        # Circuit should be open after threshold
        assert breaker.state == CircuitBreakerState.OPEN
        assert not breaker.can_execute()

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_retry_logic(self, agent):
        """Test retry with exponential backoff"""
        call_count = 0

        async def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Test failure")
            return "success"

        result = await agent.execute_with_retry(
            failing_function,
            max_retries=3
        )

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_event_emission(self, agent):
        """Test event emission and handling"""
        received_events = []

        async def handler(event):
            received_events.append(event)

        agent.register_event_handler("test_event", handler)

        event = IntegrationEvent(
            event_id="test_1",
            event_type="test_event",
            source_platform=IntegrationPlatform.BACKEND,
            payload={"test": "data"}
        )

        await agent.emit_event(event)
        # Give time for async handler
        await asyncio.sleep(0.01)

        assert len(received_events) == 1
        assert received_events[0].event_id == "test_1"

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_platform_connection(self, agent):
        """Test platform connection management"""
        mock_client = Mock()

        await agent.connect_platform(IntegrationPlatform.DATABASE, mock_client)
        assert IntegrationPlatform.DATABASE in agent.platform_clients

        await agent.disconnect_platform(IntegrationPlatform.DATABASE)
        assert IntegrationPlatform.DATABASE not in agent.platform_clients

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_health_check(self, agent):
        """Test agent health check"""
        health = await agent.health_check()

        assert health["status"] == "healthy"
        assert "metrics" in health
        assert health["metrics"]["total_requests"] == 0


class TestAPIGatewayAgent:
    """Test API Gateway agent functionality"""

    @pytest.fixture
    def agent(self):
        """Create an API Gateway agent"""
        return APIGatewayAgent()

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_endpoint_registration(self, agent):
        """Test API endpoint registration"""
        endpoint = APIEndpoint(
            path="/test",
            method="GET",
            version=APIVersion.V1,
            description="Test endpoint",
            tags=["test"],
            rate_limit=100
        )

        result = await agent.register_endpoint(endpoint)

        assert result.success
        assert "v1:GET:/test" in agent.endpoints
        assert "v1:GET:/test" in agent.rate_limiters

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_endpoint_deprecation(self, agent):
        """Test endpoint deprecation"""
        endpoint = APIEndpoint(
            path="/old",
            method="POST",
            version=APIVersion.V1
        )

        await agent.register_endpoint(endpoint)
        result = await agent.deprecate_endpoint("/old", "POST", APIVersion.V1)

        assert result.success
        assert agent.endpoints["v1:POST:/old"].deprecated

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_request_transformation(self, agent):
        """Test request transformation between versions"""
        request_data = {"user_id": "123", "data": "test"}

        transformed = await agent.transform_request(
            request_data,
            APIVersion.V1,
            APIVersion.V2
        )

        assert "userId" in transformed
        assert transformed["userId"] == "123"
        assert transformed["_api_version"] == "v2"

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_rate_limiting(self, agent):
        """Test rate limiting functionality"""
        endpoint = APIEndpoint(
            path="/limited",
            method="GET",
            version=APIVersion.V1,
            rate_limit=2  # 2 requests per minute
        )

        await agent.register_endpoint(endpoint)
        endpoint_key = "v1:GET:/limited"

        # Should allow first 2 requests
        valid1, _ = await agent.validate_request(endpoint_key, {}, "client1")
        valid2, _ = await agent.validate_request(endpoint_key, {}, "client1")
        assert valid1 and valid2

        # Should block third request
        valid3, error = await agent.validate_request(endpoint_key, {}, "client1")
        assert not valid3
        assert "Rate limit exceeded" in error

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_openapi_generation(self, agent):
        """Test OpenAPI specification generation"""
        endpoint = APIEndpoint(
            path="/api/test",
            method="GET",
            version=APIVersion.V1,
            description="Test API",
            tags=["test"],
            authentication_required=True
        )

        await agent.register_endpoint(endpoint)
        spec = await agent.generate_openapi_spec(APIVersion.V1)

        assert spec["openapi"] == "3.0.0"
        assert "/api/test" in spec["paths"]
        assert "get" in spec["paths"]["/api/test"]


class TestDatabaseSyncAgent:
    """Test Database Sync agent functionality"""

    @pytest.fixture
    def agent(self):
        """Create a Database Sync agent"""
        return DatabaseSyncAgent()

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_cache_key_generation(self, agent):
        """Test cache key generation"""
        key = agent._generate_cache_key("users", 123)
        assert key == "users:123"

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_sync_to_cache(self, agent):
        """Test data synchronization to cache"""
        mock_redis = AsyncMock()
        await agent.connect_platform(IntegrationPlatform.CACHE, mock_redis)

        result = await agent.sync_data_to_cache(
            table_name="users",
            primary_key=1,
            data={"name": "Test User", "email": "test@example.com"},
            ttl=3600
        )

        assert result.success
        assert result.output["cache_key"] == "users:1"
        assert result.output["ttl"] == 3600

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_consistency_validation(self, agent):
        """Test data consistency validation"""
        check = await agent.validate_consistency("users")

        # With no real connections, should show as consistent but empty
        assert check.table_name == "users"
        assert check.postgresql_count == 0
        assert check.redis_count == 0
        assert check.is_consistent

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_sync_strategy(self, agent):
        """Test different sync strategies"""
        agent.sync_strategy = SyncStrategy.WRITE_THROUGH
        assert agent.sync_strategy == SyncStrategy.WRITE_THROUGH

        agent.sync_strategy = SyncStrategy.WRITE_BEHIND
        assert agent.sync_strategy == SyncStrategy.WRITE_BEHIND

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_cache_invalidation(self, agent):
        """Test cache invalidation"""
        mock_redis = AsyncMock()
        await agent.connect_platform(IntegrationPlatform.CACHE, mock_redis)

        result = await agent.invalidate_cache(table_name="users")

        assert result.success
        assert result.output["table"] == "users"


class TestIntegrationCoordinator:
    """Test Integration Coordinator functionality"""

    @pytest.fixture
    def coordinator(self):
        """Create an Integration Coordinator"""
        return IntegrationCoordinator()

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_workflow_creation(self, coordinator):
        """Test workflow creation from template"""
        workflow = await coordinator.create_workflow(
            name="Test Workflow",
            description="Test Description",
            template="full_sync"
        )

        assert workflow.workflow_id.startswith("workflow_")
        assert workflow.name == "Test Workflow"
        assert len(workflow.tasks) == 4  # Full sync has 4 tasks
        assert workflow.status == WorkflowStatus.PENDING

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_custom_workflow_creation(self, coordinator):
        """Test custom workflow creation"""
        custom_tasks = [
            {
                "type": "test_task",
                "agent": "TestAgent",
                "platform": "BACKEND",
                "priority": "HIGH",
                "dependencies": []
            }
        ]

        workflow = await coordinator.create_workflow(
            name="Custom Workflow",
            description="Custom Test",
            custom_tasks=custom_tasks
        )

        assert len(workflow.tasks) == 1
        task = list(workflow.tasks.values())[0]
        assert task.task_type == "test_task"
        assert task.priority == TaskPriority.HIGH

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_workflow_execution(self, coordinator):
        """Test workflow execution"""
        workflow = await coordinator.create_workflow(
            name="Simple Workflow",
            description="Simple test workflow",
            custom_tasks=[
                {
                    "type": "task1",
                    "agent": "Agent1",
                    "platform": "BACKEND",
                    "dependencies": []
                }
            ]
        )

        result = await coordinator.execute_workflow(workflow.workflow_id)

        assert result.success
        assert result.output["completed_tasks"] == 1
        assert workflow.status == WorkflowStatus.COMPLETED

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_workflow_dependency_resolution(self, coordinator):
        """Test task dependency resolution"""
        custom_tasks = [
            {
                "type": "task1",
                "agent": "Agent1",
                "platform": "BACKEND",
                "dependencies": []
            },
            {
                "type": "task2",
                "agent": "Agent2",
                "platform": "BACKEND",
                "dependencies": ["custom_task_workflow_test_0"]  # Depends on task1
            }
        ]

        workflow = await coordinator.create_workflow(
            name="Dependency Test",
            description="Test dependencies",
            custom_tasks=custom_tasks
        )

        # Get ready tasks should only return task1 initially
        ready_tasks = workflow.get_ready_tasks()
        assert len(ready_tasks) == 1
        assert ready_tasks[0].task_type == "task1"

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_workflow_cancellation(self, coordinator):
        """Test workflow cancellation"""
        workflow = await coordinator.create_workflow(
            name="Cancel Test",
            description="Test cancellation"
        )

        result = await coordinator.cancel_workflow(workflow.workflow_id)

        assert result.success
        assert workflow.status == WorkflowStatus.CANCELLED

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_workflow_status(self, coordinator):
        """Test workflow status retrieval"""
        workflow = await coordinator.create_workflow(
            name="Status Test",
            description="Test status"
        )

        status = await coordinator.get_workflow_status(workflow.workflow_id)

        assert status["workflow_id"] == workflow.workflow_id
        assert status["name"] == "Status Test"
        assert status["status"] == "pending"
        assert "task_summary" in status

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_agent_registration(self, coordinator):
        """Test agent registration"""
        mock_agent = Mock()

        await coordinator.register_agent("TestAgent", mock_agent)

        assert "TestAgent" in coordinator.agent_registry
        assert coordinator.agent_registry["TestAgent"] == mock_agent


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
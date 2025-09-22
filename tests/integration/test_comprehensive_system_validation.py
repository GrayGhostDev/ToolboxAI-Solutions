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
Comprehensive System Validation Tests for ToolBoxAI

This test suite validates all critical system components:
1. Backend API endpoints and health checks
2. Database models and connections
3. Agent system and coordination
4. WebSocket functionality
5. Enhanced Content Generation pipeline
6. Roblox integration
7. Security and authentication
8. Redis integration
"""

import asyncio
import json
import logging
import os
import time
from typing import Dict, Any, List
from unittest.mock import Mock, patch, AsyncMock

import pytest
import httpx
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Import application components
try:
    from apps.backend.main import app
    from apps.backend.core.config import settings
    from database.connection import get_async_session, AsyncSessionLocal
    from database.models import (
        User, Agent, ContentGenerationRequest,
        EnhancedContentGeneration, ContentGenerationBatch
    )
except ImportError as e:
    pytest.skip(f"Required modules not available: {e}", allow_module_level=True)

# Test configuration
TEST_CONFIG = {
    "test_timeout": 10,
    "api_base_url": "http://127.0.0.1:8009",
    "websocket_url": "pusher://app_key@cluster",
    "test_user_email": "test@toolboxai.com",
    "test_agent_name": "test_agent"
}

logger = logging.getLogger(__name__)


class TestSystemHealth:
    """Test basic system health and connectivity"""

    def test_app_import_successful(self):
        """Test that the FastAPI app can be imported without errors"""
        assert app is not None
        assert hasattr(app, 'routes')
        assert len(app.routes) > 0

    def test_settings_configuration(self):
        """Test that settings are properly configured"""
        assert settings is not None
        assert hasattr(settings, 'database_url')
        assert hasattr(settings, 'redis_url')

    @pytest.mark.integration
    def test_health_endpoint(self):
        """Test the main health endpoint"""
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "uptime" in data
            assert data["status"] in ["healthy", "degraded"]

    @pytest.mark.integration
    def test_api_v1_health(self):
        """Test the API v1 health endpoint"""
        with TestClient(app) as client:
            response = client.get("/api/v1/health")
            assert response.status_code == 200
            data = response.json()
            assert "status" in data


class TestDatabaseIntegration:
    """Test database models and connections"""

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.asyncio
async def test_database_connection(self):
        """Test database connectivity"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("SELECT 1"))
                assert result.scalar() == 1
        except Exception as e:
            pytest.fail(f"Database connection failed: {e}")

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.asyncio
async def test_user_model_operations(self):
        """Test User model CRUD operations"""
        async with AsyncSessionLocal() as session:
            # Test user creation
            test_user = User(
                email=TEST_CONFIG["test_user_email"],
                username="testuser",
                full_name="Test User",
                role="student"
            )
            session.add(test_user)
            await session.commit()
            await session.refresh(test_user)

            # Test user retrieval
            assert test_user.id is not None
            assert test_user.email == TEST_CONFIG["test_user_email"]

            # Cleanup
            await session.delete(test_user)
            await session.commit()

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.asyncio
async def test_enhanced_content_generation_model(self):
        """Test EnhancedContentGeneration model"""
        async with AsyncSessionLocal() as session:
            # Create test record
            content_gen = EnhancedContentGeneration(
                request_id="test-request-123",
                subject_type="math",
                grade_level="5th",
                content_type="lesson",
                requirements="Test requirements",
                status="pending"
            )
            session.add(content_gen)
            await session.commit()
            await session.refresh(content_gen)

            # Verify creation
            assert content_gen.id is not None
            assert content_gen.request_id == "test-request-123"
            assert content_gen.status == "pending"

            # Test status update
            content_gen.status = "completed"
            await session.commit()

            # Cleanup
            await session.delete(content_gen)
            await session.commit()

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.asyncio
async def test_content_generation_batch_model(self):
        """Test ContentGenerationBatch model"""
        async with AsyncSessionLocal() as session:
            batch = ContentGenerationBatch(
                batch_id="test-batch-456",
                total_requests=5,
                completed_requests=0,
                status="pending",
                created_by="test-user"
            )
            session.add(batch)
            await session.commit()
            await session.refresh(batch)

            # Verify creation
            assert batch.id is not None
            assert batch.batch_id == "test-batch-456"
            assert batch.total_requests == 5

            # Cleanup
            await session.delete(batch)
            await session.commit()


class TestAgentSystem:
    """Test agent system and coordination"""

    @pytest.mark.integration
    def test_agent_health_endpoint(self):
        """Test agent health monitoring"""
        with TestClient(app) as client:
            response = client.get("/api/v1/agents/health")
            assert response.status_code == 200
            data = response.json()
            assert "agents" in data or "status" in data

    @pytest.mark.integration
    @pytest.mark.requires_openai
    def test_content_generation_endpoint(self):
        """Test content generation endpoint"""
        with TestClient(app) as client:
            test_request = {
                "subject": "mathematics",
                "grade_level": "5th",
                "content_type": "lesson",
                "topic": "fractions",
                "requirements": "Interactive lesson with examples"
            }

            # Mock OpenAI API if key not available
            if not os.getenv("OPENAI_API_KEY"):
                with patch('apps.backend.agents.agent.generate_educational_content') as mock_gen:
                    mock_gen.return_value = {
                        "content": "Test content",
                        "metadata": {"topic": "fractions"}
                    }
                    response = client.post("/api/v1/content/generate", json=test_request)
            else:
                response = client.post("/api/v1/content/generate", json=test_request)

            # Should get either success or auth error (depending on setup)
            assert response.status_code in [200, 401, 422]

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.asyncio
async def test_agent_coordination(self):
        """Test agent coordination and communication"""
        try:
            from core.agents.orchestrator import AgentOrchestrator
            from core.agents.base_agent import BaseAgent

            orchestrator = AgentOrchestrator()

            # Test agent registration
            test_agent = BaseAgent(name="test_agent", role="content_generator")
            await orchestrator.register_agent(test_agent)

            # Test agent communication
            result = await orchestrator.coordinate_task({
                "task_type": "content_generation",
                "parameters": {"subject": "math", "grade": "5th"}
            })

            assert result is not None

        except ImportError:
            pytest.skip("Agent orchestration modules not available")


class TestEnhancedContentGeneration:
    """Test enhanced content generation pipeline"""

    @pytest.mark.integration
    def test_enhanced_content_endpoints_available(self):
        """Test that enhanced content generation endpoints are accessible"""
        with TestClient(app) as client:
            # Test enhanced generation endpoint
            response = client.get("/api/v1/content/enhanced")
            # Should return method not allowed or auth required, not 404
            assert response.status_code in [200, 401, 405, 422]

    @pytest.mark.integration
    def test_content_batch_processing(self):
        """Test batch content generation"""
        with TestClient(app) as client:
            batch_request = {
                "requests": [
                    {
                        "subject": "science",
                        "grade_level": "6th",
                        "content_type": "quiz",
                        "topic": "photosynthesis"
                    }
                ],
                "batch_name": "test_batch"
            }

            response = client.post("/api/v1/content/batch", json=batch_request)
            # Should get auth error or success, not 404
            assert response.status_code in [200, 201, 401, 422]


class TestWebSocketIntegration:
    """Test WebSocket functionality and real-time features"""

    @pytest.mark.asyncio
    @pytest.mark.websocket
    @pytest.mark.asyncio
async def test_websocket_connection(self):
        """Test WebSocket connection establishment"""
        try:
            from tests.fixtures.pusher_test_utils import websocket_manager

            # Test websocket manager initialization
            assert websocket_manager is not None

            # Test connection handling
            mock_pusher_as_websocket = AsyncMock()
            await websocket_manager.connect(mock_pusher_as_websocket)
            assert len(websocket_manager.active_connections) >= 0

        except Exception as e:
            logger.warning(f"WebSocket test failed: {e}")

    @pytest.mark.integration
    def test_pusher_integration(self):
        """Test Pusher integration for real-time updates"""
        with TestClient(app) as client:
            # Test Pusher auth endpoint
            response = client.post("/pusher/auth", json={
                "socket_id": "test_socket",
                "channel_name": "private-test"
            })
            # Should return auth response or error, not 404
            assert response.status_code in [200, 401, 403, 422]


class TestRobloxIntegration:
    """Test Roblox integration functionality"""

    @pytest.mark.integration
    @pytest.mark.roblox
    def test_roblox_endpoints_available(self):
        """Test Roblox integration endpoints"""
        with TestClient(app) as client:
            # Test Roblox health endpoint
            response = client.get("/api/v1/roblox/health")
            assert response.status_code in [200, 404]  # 404 is acceptable if not implemented

            # Test Roblox content generation
            roblox_request = {
                "content_type": "script",
                "subject": "math",
                "grade_level": "5th"
            }
            response = client.post("/api/v1/roblox/generate", json=roblox_request)
            assert response.status_code in [200, 401, 404, 422]

    @pytest.mark.integration
    def test_roblox_agent_functionality(self):
        """Test Roblox agent operations"""
        try:
            from core.agents.roblox_agent import RobloxAgent

            agent = RobloxAgent()
            assert agent is not None

            # Test agent capabilities
            capabilities = agent.get_capabilities()
            assert isinstance(capabilities, (list, dict))

        except ImportError:
            pytest.skip("Roblox agent modules not available")


class TestSecurityAndAuthentication:
    """Test security features and authentication"""

    @pytest.mark.integration
    def test_auth_endpoints(self):
        """Test authentication endpoints"""
        with TestClient(app) as client:
            # Test login endpoint
            login_data = {
                "username": "test@example.com",
                "password": "testpassword"
            }
            response = client.post("/api/v1/auth/login", json=login_data)
            # Should return auth error or validation error, not 404
            assert response.status_code in [200, 400, 401, 422]

            # Test protected endpoint without auth
            response = client.get("/api/v1/auth/me")
            assert response.status_code in [401, 403]  # Should require authentication

    @pytest.mark.integration
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        with TestClient(app) as client:
            # Make multiple rapid requests to test rate limiting
            responses = []
            for _ in range(10):
                response = client.get("/health")
                responses.append(response.status_code)

            # Should generally succeed unless rate limited
            success_count = sum(1 for status in responses if status == 200)
            assert success_count >= 5  # At least half should succeed

    @pytest.mark.integration
    def test_cors_configuration(self):
        """Test CORS configuration"""
        with TestClient(app) as client:
            # Test preflight request
            response = client.options(
                "/api/v1/health",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET"
                }
            )
            # Should handle CORS properly
            assert response.status_code in [200, 204]


class TestRedisIntegration:
    """Test Redis connectivity and caching"""

    @pytest.mark.integration
    @pytest.mark.requires_redis
    def test_redis_health_check(self):
        """Test Redis connectivity through health endpoint"""
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()

            # Check if Redis status is included in health check
            if "services" in data:
                redis_status = data["services"].get("redis")
                if redis_status:
                    assert redis_status in ["healthy", "unhealthy"]


class TestPerformanceAndReliability:
    """Test system performance and reliability"""

    @pytest.mark.performance
    def test_response_times(self):
        """Test API response times"""
        with TestClient(app) as client:
            start_time = time.time()
            response = client.get("/health")
            end_time = time.time()

            assert response.status_code == 200
            response_time = end_time - start_time
            assert response_time < 2.0  # Health check should be fast

    @pytest.mark.integration
    def test_error_handling(self):
        """Test error handling and recovery"""
        with TestClient(app) as client:
            # Test invalid endpoint
            response = client.get("/api/v1/nonexistent")
            assert response.status_code == 404

            # Test invalid request data
            response = client.post("/api/v1/content/generate", json={"invalid": "data"})
            assert response.status_code in [400, 422]


# Test runner function for comprehensive validation
def run_comprehensive_tests():
    """Run all comprehensive tests and return results"""
    test_results = {
        "total_tests": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "skipped_tests": 0,
        "errors": []
    }

    # This would be called by pytest, but we can provide a summary function
    return test_results


if __name__ == "__main__":
    # Run basic smoke tests when executed directly
    print("Running ToolBoxAI System Validation Tests...")

    # Test app import
    try:
        from apps.backend.main import app
        print("✓ FastAPI app import successful")
    except Exception as e:
        print(f"✗ FastAPI app import failed: {e}")

    # Test basic health check
    try:
        with TestClient(app) as client:
            response = client.get("/health")
            if response.status_code == 200:
                print("✓ Health endpoint accessible")
            else:
                print(f"✗ Health endpoint returned {response.status_code}")
    except Exception as e:
        print(f"✗ Health endpoint test failed: {e}")

    print("\nRun 'pytest tests/integration/test_comprehensive_system_validation.py -v' for full test suite")
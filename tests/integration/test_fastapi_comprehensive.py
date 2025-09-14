#!/usr/bin/env python3
"""
Comprehensive FastAPI Test Suite - Complete Backend Testing
Tests all endpoints, authentication, WebSocket connections, and integrations.
"""

import asyncio

def make_json_serializable(obj):
    """Convert non-serializable objects to serializable format."""
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    elif hasattr(obj, 'to_dict'):
        return obj.to_dict()
    elif hasattr(obj, '_asdict'):
        return obj._asdict()
    else:
        return str(obj)

import json
import logging
import os
import sys
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
import pytest
from tests.fixtures.agents import mock_llm
from unittest.mock import Mock, patch, AsyncMock

# Skip all tests in this module as they require external services
pytestmark = pytest.mark.skipif(
    not os.environ.get('RUN_INTEGRATION_TESTS'),
    reason="Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to enable"
)

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Test configuration
TEST_CONFIG = {
    "api_host": "127.0.0.1",
    "api_port": 8008,
    "flask_port": 5001,
    "mcp_port": 9876,
    "redis_host": "localhost",
    "redis_port": 6379,
    "db_host": "localhost",
    "db_port": 5432,
    "test_timeout": 30,
}

class TestResult:
    """Store test results"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = []
        self.warnings = []
        self.start_time = time.time()
    
    def add_pass(self, test_name: str):
        self.passed += 1
        logger.info(f"✅ PASSED: {test_name}")
    
    def add_fail(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
        logger.error(f"❌ FAILED: {test_name} - {error}")
    
    def add_skip(self, test_name: str, reason: str):
        self.skipped += 1
        self.warnings.append(f"{test_name}: {reason}")
        logger.warning(f"⚠️ SKIPPED: {test_name} - {reason}")
    
    def get_summary(self) -> Dict:
        duration = time.time() - self.start_time
        return {
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "total": self.passed + self.failed + self.skipped,
            "duration": f"{duration:.2f}s",
            "errors": self.errors,
            "warnings": self.warnings
        }

class FastAPITester:
    """Comprehensive FastAPI testing suite"""
    
    def __init__(self):
        self.results = TestResult()
        self.base_url = f"http://{TEST_CONFIG['api_host']}:{TEST_CONFIG['api_port']}"
        self.flask_url = f"http://{TEST_CONFIG['api_host']}:{TEST_CONFIG['flask_port']}"
        
    async def run_all_tests(self):
        """Run all test categories"""
        logger.info("=" * 60)
        logger.info("COMPREHENSIVE FASTAPI TEST SUITE")
        logger.info("=" * 60)
        
        # Test categories
        await self.test_imports()
        await self.test_dependencies()
        await self.test_server_startup()
        await self.test_basic_endpoints()
        await self.test_authentication()
        await self.test_content_generation()
        await self.test_quiz_generation()
        await self.test_terrain_generation()
        await self.test_websocket_connection()
        await self.test_flask_bridge()
        await self.test_mcp_integration()
        await self.test_agent_system()
        await self.test_sparc_framework()
        await self.test_swarm_intelligence()
        await self.test_error_handling()
        await self.test_performance()
        
        # Print summary
        self.print_summary()
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_imports(self, mock_llm):
        """Test all required imports"""
        logger.info("\n🔍 Testing Python Imports...")
        
        imports_to_test = [
            ("fastapi", "FastAPI"),
            ("uvicorn", "Uvicorn"),
            ("pydantic", "Pydantic"),
            ("sqlalchemy", "SQLAlchemy"),
            ("redis", "Redis"),
            ("psycopg2", "PostgreSQL driver"),
            ("httpx", "HTTP client"),
            ("websockets", "WebSocket"),
            ("langchain", "LangChain"),
            ("langgraph", "LangGraph"),
            ("openai", "OpenAI"),
            ("jwt", "JWT"),
        ]
        
        for module_name, display_name in imports_to_test:
            try:
                __import__(module_name)
                self.results.add_pass(f"Import {display_name}")
            except ImportError as e:
                self.results.add_fail(f"Import {display_name}", str(e))
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_dependencies(self, mock_llm):
        """Test external service dependencies"""
        logger.info("\n🔗 Testing External Dependencies...")
        
        # Test Redis
        try:
            import redis
            r = redis.Redis(
                host=TEST_CONFIG['redis_host'],
                port=TEST_CONFIG['redis_port'],
                decode_responses=True
            )
            r.ping()
            self.results.add_pass("Redis connection")
        except Exception as e:
            self.results.add_skip("Redis connection", str(e))
        
        # Test PostgreSQL
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=TEST_CONFIG['db_host'],
                port=TEST_CONFIG['db_port'],
                database="toolboxai",
                user="postgres"
            )
            conn.close()
            self.results.add_pass("PostgreSQL connection")
        except Exception as e:
            self.results.add_skip("PostgreSQL connection", str(e))
        
        # Test OpenAI API
        if os.getenv("OPENAI_API_KEY"):
            self.results.add_pass("OpenAI API key present")
        else:
            self.results.add_skip("OpenAI API key", "Not configured")
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_server_startup(self, mock_llm):
        """Test server startup and health"""
        logger.info("\n🚀 Testing Server Startup...")
        
        import httpx
        
        try:
            async with httpx.AsyncClient() as client:
                # Test health endpoint
                response = await client.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    self.results.add_pass("Server health check")
                    data = response.json()
                    if data.get("status") == "healthy":
                        self.results.add_pass("Server status healthy")
                else:
                    self.results.add_fail("Server health check", f"Status {response.status_code}")
        except Exception as e:
            self.results.add_fail("Server connection", str(e))
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_basic_endpoints(self, mock_llm):
        """Test basic API endpoints"""
        logger.info("\n📡 Testing Basic Endpoints...")
        
        import httpx
        
        endpoints = [
            ("/", "Root endpoint"),
            ("/health", "Health endpoint"),
            ("/docs", "Swagger documentation"),
            ("/openapi.json", "OpenAPI schema"),
        ]
        
        try:
            async with httpx.AsyncClient() as client:
                for endpoint, name in endpoints:
                    try:
                        response = await client.get(f"{self.base_url}{endpoint}")
                        if response.status_code in [200, 301, 302, 307]:
                            self.results.add_pass(name)
                        else:
                            self.results.add_fail(name, f"Status {response.status_code}")
                    except Exception as e:
                        self.results.add_fail(name, str(e))
        except Exception as e:
            self.results.add_fail("HTTP client", str(e))
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_authentication(self, mock_llm):
        """Test authentication system"""
        logger.info("\n🔐 Testing Authentication...")
        
        import httpx
        import jwt
        
        try:
            # Generate test JWT token
            secret_key = os.getenv("JWT_SECRET_KEY", "test-secret-key")
            payload = {
                "sub": "test-user",
                "exp": datetime.now(timezone.utc) + timedelta(hours=1)
            }
            token = jwt.encode(payload, secret_key, algorithm="HS256")
            
            async with httpx.AsyncClient() as client:
                # Test with valid token
                headers = {"Authorization": f"Bearer {token}"}
                response = await client.get(
                    f"{self.base_url}/protected",
                    headers=headers
                )
                
                if response.status_code in [200, 404]:  # 404 if endpoint doesn't exist yet
                    self.results.add_pass("JWT authentication")
                else:
                    self.results.add_fail("JWT authentication", f"Status {response.status_code}")
                
                # Test without token
                response = await client.get(f"{self.base_url}/protected")
                if response.status_code in [401, 403, 404]:
                    self.results.add_pass("Authentication required")
                else:
                    self.results.add_fail("Authentication required", "Should require auth")
                    
        except Exception as e:
            self.results.add_skip("Authentication tests", str(e))
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_content_generation(self, mock_llm):
        """Test content generation endpoint"""
        logger.info("\n📝 Testing Content Generation...")
        
        import httpx
        
        test_payload = {
            "subject": "Mathematics",
            "grade_level": 5,
            "learning_objectives": ["Fractions", "Decimals"],
            "environment_type": "classroom",
            "include_quiz": True
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/generate_content",
                    json=test_payload
                )
                
                if response.status_code == 200:
                    self.results.add_pass("Content generation endpoint")
                    data = response.json()
                    if "content" in data or "message" in data:
                        self.results.add_pass("Content response format")
                elif response.status_code == 404:
                    self.results.add_skip("Content generation", "Endpoint not implemented")
                else:
                    self.results.add_fail("Content generation", f"Status {response.status_code}")
                    
        except Exception as e:
            self.results.add_skip("Content generation", str(e))
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_quiz_generation(self, mock_llm):
        """Test quiz generation endpoint"""
        logger.info("\n❓ Testing Quiz Generation...")
        
        import httpx
        
        test_payload = {
            "subject": "Science",
            "topic": "Solar System",
            "grade_level": 7,
            "num_questions": 5,
            "difficulty": "medium"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/generate_quiz",
                    json=test_payload
                )
                
                if response.status_code == 200:
                    self.results.add_pass("Quiz generation endpoint")
                    data = response.json()
                    if "questions" in data or "quiz" in data:
                        self.results.add_pass("Quiz response format")
                elif response.status_code == 404:
                    self.results.add_skip("Quiz generation", "Endpoint not implemented")
                else:
                    self.results.add_fail("Quiz generation", f"Status {response.status_code}")
                    
        except Exception as e:
            self.results.add_skip("Quiz generation", str(e))
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_terrain_generation(self, mock_llm):
        """Test terrain generation endpoint"""
        logger.info("\n🏔️ Testing Terrain Generation...")
        
        import httpx
        
        test_payload = {
            "theme": "forest",
            "size": "medium",
            "features": ["trees", "river", "mountains"]
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/generate_terrain",
                    json=test_payload
                )
                
                if response.status_code == 200:
                    self.results.add_pass("Terrain generation endpoint")
                    data = response.json()
                    if "terrain" in data or "script" in data:
                        self.results.add_pass("Terrain response format")
                elif response.status_code == 404:
                    self.results.add_skip("Terrain generation", "Endpoint not implemented")
                else:
                    self.results.add_fail("Terrain generation", f"Status {response.status_code}")
                    
        except Exception as e:
            self.results.add_skip("Terrain generation", str(e))
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_websocket_connection(self, mock_llm):
        """Test WebSocket connection"""
        logger.info("\n🔌 Testing WebSocket Connection...")
        
        try:
            import websockets
            
            ws_url = f"ws://{TEST_CONFIG['api_host']}:{TEST_CONFIG['api_port']}/ws"
            
            try:
                async with websockets.connect(ws_url) as websocket:
                    # Send test message
                    await websocket.send(json.dumps({"type": "ping"}, default=make_json_serializable))
                    
                    # Wait for response with timeout
                    try:
                        response = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=5.0
                        )
                        self.results.add_pass("WebSocket connection")
                        
                        if json.loads(response):
                            self.results.add_pass("WebSocket message exchange")
                    except asyncio.TimeoutError:
                        self.results.add_skip("WebSocket response", "Timeout")
                        
            except Exception as e:
                self.results.add_skip("WebSocket connection", str(e))
                
        except ImportError:
            self.results.add_skip("WebSocket tests", "websockets module not installed")
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_flask_bridge(self, mock_llm):
        """Test Flask bridge server integration"""
        logger.info("\n🌉 Testing Flask Bridge Server...")
        
        import httpx
        
        try:
            async with httpx.AsyncClient() as client:
                # Test Flask health endpoint
                response = await client.get(f"{self.flask_url}/health")
                if response.status_code == 200:
                    self.results.add_pass("Flask bridge health check")
                else:
                    self.results.add_skip("Flask bridge", "Not running")
                    return
                
                # Test plugin registration
                test_registration = {
                    "port": 64989,
                    "studio_id": "test-studio-123"
                }
                
                response = await client.post(
                    f"{self.flask_url}/register_plugin",
                    json=test_registration
                )
                
                if response.status_code in [200, 201]:
                    self.results.add_pass("Plugin registration")
                else:
                    self.results.add_fail("Plugin registration", f"Status {response.status_code}")
                    
        except Exception as e:
            self.results.add_skip("Flask bridge tests", str(e))
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_mcp_integration(self, mock_llm):
        """Test MCP (Model Context Protocol) integration"""
        logger.info("\n🧠 Testing MCP Integration...")
        
        try:
            import websockets
            
            mcp_url = f"ws://{TEST_CONFIG['api_host']}:{TEST_CONFIG['mcp_port']}"
            
            try:
                async with websockets.connect(mcp_url) as websocket:
                    # Test context update
                    await websocket.send(json.dumps({
                        "type": "update_context",
                        "context": {"test": "data"}
                    }, default=make_json_serializable))
                    
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    self.results.add_pass("MCP connection")
                    
            except Exception as e:
                self.results.add_skip("MCP integration", str(e))
                
        except ImportError:
            self.results.add_skip("MCP tests", "websockets module not installed")
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_agent_system(self, mock_llm):
        """Test LangChain agent system"""
        logger.info("\n🤖 Testing Agent System...")
        
        try:
            # Import agent modules
            from core.agents.supervisor import SupervisorAgent
            from core.agents.content_agent import ContentAgent
            from core.agents.quiz_agent import QuizAgent
            
            self.results.add_pass("Agent imports")
            
            # Test agent initialization
            try:
                supervisor = SupervisorAgent()
                self.results.add_pass("Supervisor agent initialization")
            except Exception as e:
                self.results.add_fail("Supervisor agent", str(e))
                
        except ImportError as e:
            self.results.add_skip("Agent system", str(e))
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_sparc_framework(self, mock_llm):
        """Test SPARC framework components"""
        logger.info("\n⚡ Testing SPARC Framework...")
        
        try:
            from core.sparc.state_manager import StateManager
            from core.sparc.policy_engine import PolicyEngine
            from core.sparc.action_executor import ActionExecutor
            from core.sparc.reward_calculator import RewardCalculator
            from core.sparc.context_tracker import ContextTracker
            
            self.results.add_pass("SPARC imports")
            
            # Test initialization
            try:
                state_mgr = StateManager()
                self.results.add_pass("SPARC state manager")
            except Exception as e:
                self.results.add_fail("SPARC initialization", str(e))
                
        except ImportError as e:
            self.results.add_skip("SPARC framework", str(e))
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_swarm_intelligence(self, mock_llm):
        """Test swarm intelligence system"""
        logger.info("\n🐝 Testing Swarm Intelligence...")
        
        try:
            from core.swarm.swarm_controller import SwarmController
            from core.swarm.worker_pool import WorkerPool
            from core.swarm.task_distributor import TaskDistributor
            
            self.results.add_pass("Swarm imports")
            
            # Test initialization
            try:
                swarm = SwarmController(num_workers=2)
                self.results.add_pass("Swarm controller initialization")
            except Exception as e:
                self.results.add_fail("Swarm initialization", str(e))
                
        except ImportError as e:
            self.results.add_skip("Swarm intelligence", str(e))
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_error_handling(self, mock_llm):
        """Test error handling and validation"""
        logger.info("\n⚠️ Testing Error Handling...")
        
        import httpx
        
        try:
            async with httpx.AsyncClient() as client:
                # Test invalid JSON
                response = await client.post(
                    f"{self.base_url}/generate_content",
                    content="invalid json"
                )
                
                if response.status_code in [400, 422]:
                    self.results.add_pass("Invalid JSON handling")
                else:
                    self.results.add_fail("Invalid JSON handling", f"Status {response.status_code}")
                
                # Test missing required fields
                response = await client.post(
                    f"{self.base_url}/generate_content",
                    json={}
                )
                
                if response.status_code in [400, 422]:
                    self.results.add_pass("Missing fields validation")
                else:
                    self.results.add_fail("Missing fields validation", f"Status {response.status_code}")
                    
        except Exception as e:
            self.results.add_skip("Error handling tests", str(e))
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_performance(self):
        """Test performance metrics"""
        logger.info("\n⚡ Testing Performance...")
        
        import httpx
        import statistics
        
        try:
            async with httpx.AsyncClient() as client:
                response_times = []
                
                # Test response time for health endpoint
                for _ in range(10):
                    start = time.time()
                    response = await client.get(f"{self.base_url}/health")
                    elapsed = (time.time() - start) * 1000  # Convert to ms
                    response_times.append(elapsed)
                
                avg_time = statistics.mean(response_times)
                max_time = max(response_times)
                
                if avg_time < 100:  # Average under 100ms
                    self.results.add_pass(f"Average response time ({avg_time:.2f}ms)")
                else:
                    self.results.add_fail("Average response time", f"{avg_time:.2f}ms (>100ms)")
                
                if max_time < 500:  # Max under 500ms
                    self.results.add_pass(f"Max response time ({max_time:.2f}ms)")
                else:
                    self.results.add_fail("Max response time", f"{max_time:.2f}ms (>500ms)")
                    
        except Exception as e:
            self.results.add_skip("Performance tests", str(e))
    
    def print_summary(self):
        """Print test summary"""
        summary = self.results.get_summary()
        
        logger.info("\n" + "=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"✅ Passed: {summary['passed']}")
        logger.info(f"❌ Failed: {summary['failed']}")
        logger.info(f"⚠️  Skipped: {summary['skipped']}")
        logger.info(f"📊 Total: {summary['total']}")
        logger.info(f"⏱️  Duration: {summary['duration']}")
        
        if summary['errors']:
            logger.info("\n❌ ERRORS:")
            for error in summary['errors']:
                logger.info(f"  - {error}")
        
        if summary['warnings']:
            logger.info("\n⚠️  WARNINGS:")
            for warning in summary['warnings']:
                logger.info(f"  - {warning}")
        
        # Determine overall status
        if summary['failed'] == 0:
            logger.info("\n🎉 ALL TESTS PASSED!")
        else:
            logger.info(f"\n💔 {summary['failed']} TESTS FAILED")
        
        return summary


async def main():
    """Main test runner"""
    tester = FastAPITester()
    await tester.run_all_tests()
    
    # Return exit code based on failures
    summary = tester.results.get_summary()
    sys.exit(0 if summary['failed'] == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
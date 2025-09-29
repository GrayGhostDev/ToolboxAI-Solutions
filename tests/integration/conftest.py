"""
Integration Test Configuration and Fixtures

Provides service orchestration, mocking factories, and connection management
for integration tests.
"""

import asyncio
import os
import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from unittest.mock import Mock, AsyncMock, MagicMock
import pytest
import pytest_asyncio
import aiohttp
from tests.fixtures.pusher_mocks import MockPusherService
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
PARENT_ROOT = PROJECT_ROOT.parent
sys.path.insert(0, str(PARENT_ROOT))  # For database imports
sys.path.insert(0, str(PROJECT_ROOT))  # For project imports

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import environment configuration
try:
    from toolboxai_settings import settings, Environment
    env_config = settings
except ImportError:
    # Fallback if environment module not available
    env_config = None
    logger.warning("Environment configuration module not available")

# Service configuration
SERVICE_CONFIG = {
    "fastapi": {
        "host": "127.0.0.1",
        "port": 8008,
        "http_url": "http://127.0.0.1:8008",
        "ws_url": "pusher://app_key@cluster",
        "health_endpoint": "/health"
    },
    "flask": {
        "host": "127.0.0.1",
        "port": 5001,
        "http_url": "http://127.0.0.1:5001",
        "health_endpoint": "/health"
    },
    "mcp": {
        "host": "127.0.0.1",
        "port": 9876,
        "ws_url": "ws://127.0.0.1:9876",
        "health_endpoint": None  # WebSocket only
    },
    "roblox_plugin": {
        "host": "127.0.0.1",
        "port": 64989,
        "http_url": "http://127.0.0.1:64989"
    }
}

# ================== Service Management ==================

async def wait_for_service(url: str, timeout: int = 30, service_name: str = "") -> bool:
    """Wait for a service to be available with retry logic"""
    start_time = time.time()
    
    while (time.time() - start_time) < timeout:
        try:
            if url.startswith("ws://"):
                # WebSocket check
                async with async_mock_pusher_context() as pusher:
        # Connect using Pusherurl, close_timeout=1) as ws:
                    await ws.close()
                    logger.info(f"✓ {service_name} WebSocket service is ready at {url}")
                    return True
            else:
                # HTTP check
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=1) as response:
                        if response.status in [200, 404]:  # 404 is ok for base URL
                            logger.info(f"✓ {service_name} HTTP service is ready at {url}")
                            return True
        except Exception as e:
            await asyncio.sleep(0.5)
    
    logger.warning(f"✗ {service_name} service not available at {url} after {timeout}s")
    return False

async def check_all_services() -> Dict[str, bool]:
    """Check availability of all services"""
    results = {}
    
    for name, config in SERVICE_CONFIG.items():
        if config.get("ws_url"):
            results[f"{name}_ws"] = await wait_for_service(
                config["ws_url"], 
                timeout=5,
                service_name=f"{name.upper()} WebSocket"
            )
        elif config.get("http_url") and config.get("health_endpoint"):
            url = config["http_url"] + config["health_endpoint"]
            results[f"{name}_http"] = await wait_for_service(
                url,
                timeout=5, 
                service_name=f"{name.upper()}"
            )
    
    return results

# ================== Mock Factories ==================

class MockWebSocketConnection:
    """Mock WebSocket connection for testing"""
    def __init__(self):
        self.messages = []
        self.closed = False
        self.sent_messages = []
        
    async def send(self, message: str):
        """Mock sending a message"""
        self.sent_messages.append(message)
        # Echo back for testing
        if isinstance(message, str):
            data = json.loads(message) if message else {}
        else:
            data = message
            
        # Simulate response based on message type
        if data.get("type") == "subscribe":
            response = {
                "type": "subscribed",
                "channel": data.get("channel"),
                "timestamp": datetime.now().isoformat()
            }
            self.messages.append(json.dumps(response))
        elif data.get("type") == "join_lesson":
            response = {
                "type": "lesson_joined",
                "lesson_id": data.get("lesson_id"),
                "user_id": data.get("user_id")
            }
            self.messages.append(json.dumps(response))
        elif data.get("type") == "activity_complete":
            response = {
                "type": "peer_progress", 
                "activity_id": data.get("activity_id"),
                "score": data.get("score"),
                "user_id": data.get("user_id")
            }
            self.messages.append(json.dumps(response))
            
    async def recv(self):
        """Mock receiving a message"""
        if self.messages:
            return self.messages.pop(0)
        await asyncio.sleep(0.1)
        return json.dumps({"type": "ping", "timestamp": time.time()})
        
    async def close(self):
        """Mock closing connection"""
        self.closed = True
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

class MockWebSocketManager:
    """Mock WebSocket manager for testing"""
    def __init__(self):
        self.connections = {}
        self.messages = []
        
    async def connect(self, websocket, client_id=None, user_id=None):
        """Mock connection"""
        conn_id = client_id or str(uuid.uuid4())
        self.connections[conn_id] = {
            "websocket": websocket,
            "user_id": user_id,
            "connected_at": datetime.now()
        }
        return conn_id
        
    async def disconnect(self, client_id: str):
        """Mock disconnection"""
        if client_id in self.connections:
            del self.connections[client_id]
            
    async def send_message(self, client_id: str, message: Dict):
        """Mock sending message to client"""
        self.messages.append({
            "client_id": client_id,
            "message": message,
            "timestamp": datetime.now()
        })
        
    async def broadcast(self, message: Dict, exclude=None):
        """Mock broadcasting message"""
        for client_id in self.connections:
            if exclude and client_id in exclude:
                continue
            await self.send_message(client_id, message)

class MockDatabaseSession:
    """Mock database session for testing"""
    def __init__(self):
        self.data = {}
        self.committed = False
        self.rolled_back = False
        
    async def execute(self, query):
        """Mock query execution"""
        return Mock(scalars=lambda: Mock(all=lambda: []))
        
    async def commit(self):
        """Mock commit"""
        self.committed = True
        
    async def rollback(self):
        """Mock rollback"""
        self.rolled_back = True
        
    async def close(self):
        """Mock close"""
        pass
        
    def add(self, obj):
        """Mock adding object"""
        obj_type = type(obj).__name__
        if obj_type not in self.data:
            self.data[obj_type] = []
        self.data[obj_type].append(obj)
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.rollback()
        else:
            await self.commit()
        await self.close()

# ================== Fixtures ==================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def check_services():
    """Check and report service availability"""
    results = await check_all_services()
    
    # Report status
    logger.info("\n" + "="*50)
    logger.info("Service Availability Report:")
    for service, available in results.items():
        status = "✓" if available else "✗"
        logger.info(f"  {status} {service}: {'Available' if available else 'Not Available'}")
    logger.info("="*50 + "\n")
    
    return results

@pytest_asyncio.fixture
async def mock_pusher_as_websocket():
    """Provide mock WebSocket connection"""
    return MockWebSocketConnection()

@pytest_asyncio.fixture
async def mock_ws_manager():
    """Provide mock WebSocket manager"""
    return MockWebSocketManager()

@pytest_asyncio.fixture
async def mock_db_session():
    """Provide mock database session"""
    return MockDatabaseSession()

@pytest_asyncio.fixture
async def test_db():
    """Create test database session based on environment configuration"""
    # Check if we should use mock database
    should_use_mock = True
    if env_config:
        should_use_mock = env_config.use_mock_database
        if env_config.is_production:
            # NEVER use mock in production, even for tests
            should_use_mock = False
    
    if should_use_mock:
        logger.info("Using mock database session (environment: testing/development)")
        yield MockDatabaseSession()
    else:
        try:
            # Use real test database
            from database.connection import DatabaseManager, get_db
            
            # Get database URL from environment config
            db_url = env_config.get_database_url() if env_config else "sqlite+aiosqlite:///:memory:"
            
            engine = create_async_engine(db_url, echo=False)
            
            # Create tables
            from database.models.models import Base
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            # Create session factory
            async_session = sessionmaker(
                engine, 
                class_=AsyncSession, 
                expire_on_commit=False
            )
            
            async with async_session() as session:
                yield session
                
            await engine.dispose()
            
        except ImportError as e:
            # Only fallback to mock if not in production
            if env_config and env_config.is_production:
                raise RuntimeError("Cannot use mock database in production environment") from e
            logger.warning("Using mock database session - real database not available")
            yield MockDatabaseSession()

@pytest_asyncio.fixture
async def http_client():
    """Provide aiohttp client session"""
    async with aiohttp.ClientSession() as session:
        yield session

@pytest.fixture
def service_urls():
    """Provide service URLs for testing"""
    return SERVICE_CONFIG

@pytest.fixture
def mock_repositories():
    """Provide mock repository instances"""
    return {
        "UserRepository": Mock(
            create=AsyncMock(return_value=Mock(id="user-123")),
            get=AsyncMock(return_value=Mock(id="user-123", username="testuser")),
            update=AsyncMock(return_value=True),
            delete=AsyncMock(return_value=True)
        ),
        "CourseRepository": Mock(
            create=AsyncMock(return_value=Mock(id="course-123")),
            get=AsyncMock(return_value=Mock(id="course-123", title="Test Course")),
            list=AsyncMock(return_value=[])
        ),
        "LessonRepository": Mock(
            create=AsyncMock(return_value=Mock(id="lesson-123")),
            get=AsyncMock(return_value=Mock(id="lesson-123", title="Test Lesson"))
        ),
        "QuizRepository": Mock(
            create=AsyncMock(return_value=Mock(id="quiz-123")),
            get=AsyncMock(return_value=Mock(id="quiz-123", title="Test Quiz")),
            submit_attempt=AsyncMock(return_value=Mock(score=80))
        ),
        "ContentRepository": Mock(
            create=AsyncMock(return_value=Mock(id="content-123")),
            get=AsyncMock(return_value=Mock(id="content-123", title="Test Content"))
        ),
        "ProgressRepository": Mock(
            track=AsyncMock(return_value=True),
            get_progress=AsyncMock(return_value=Mock(completion=75))
        ),
        "AnalyticsRepository": Mock(
            track_event=AsyncMock(return_value=True),
            get_analytics=AsyncMock(return_value={})
        )
    }

@pytest.fixture
def mock_agents():
    """Provide mock agent instances"""
    from unittest.mock import AsyncMock
    
    return {
        "ContentAgent": Mock(
            generate_content=AsyncMock(return_value={
                "title": "Test Content",
                "body": "Generated content",
                "metadata": {}
            })
        ),
        "QuizAgent": Mock(
            generate_quiz=AsyncMock(return_value={
                "questions": [
                    {
                        "question": "Test question?",
                        "options": ["A", "B", "C"],
                        "correct": 0
                    }
                ]
            })
        ),
        "TerrainAgent": Mock(
            generate_terrain=AsyncMock(return_value="-- Lua terrain script")
        ),
        "ScriptAgent": Mock(
            generate_script=AsyncMock(return_value="-- Lua game script")
        )
    }

# ================== Test Environment Setup ==================

def pytest_configure(config):
    """Configure pytest environment"""
    # Set test environment
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["TESTING"] = "true"
    
    # Check if we're in production (should NEVER run tests in production)
    if os.getenv("ENVIRONMENT") == "production" or os.getenv("NODE_ENV") == "production":
        raise RuntimeError("Cannot run tests in production environment!")
    
    # Only set mock flags if not explicitly set
    if "USE_MOCK_LLM" not in os.environ:
        os.environ["USE_MOCK_LLM"] = "true"
    if "USE_MOCK_DATABASE" not in os.environ:
        os.environ["USE_MOCK_DATABASE"] = "true"
    if "USE_MOCK_SERVICES" not in os.environ:
        os.environ["USE_MOCK_SERVICES"] = "false"  # Try real services first
    
    os.environ["BYPASS_RATE_LIMIT_IN_TESTS"] = "true"
    os.environ["LOG_LEVEL"] = "WARNING"
    
    # Configure rate limiting for tests
    try:
        from apps.backend.rate_limit_manager import (
            RateLimitManager, 
            RateLimitMode,
            RateLimitConfig
        )
        
        manager = RateLimitManager.get_instance()
        manager.set_mode(RateLimitMode.BYPASS)
    except ImportError:
        pass
    
    # Log environment configuration
    if env_config:
        logger.info(f"Test environment configured: {env_config}")
        logger.info(f"Using mock LLM: {env_config.use_mock_llm}")
        logger.info(f"Using mock database: {env_config.use_mock_database}")
        logger.info(f"Using mock services: {env_config.use_mock_services}")

def pytest_unconfigure(config):
    """Clean up test environment"""
    # Reset environment variables
    for key in ["TESTING", "USE_MOCK_LLM", "BYPASS_RATE_LIMIT_IN_TESTS"]:
        os.environ.pop(key, None)
    
    # Clean up rate limiting
    try:
        from apps.backend.rate_limit_manager import RateLimitManager
        
        manager = RateLimitManager.get_instance()
        manager.clear_all_limits()
        RateLimitManager.reset_instance()
    except ImportError:
        pass

# ================== Utility Functions ==================

async def retry_async(
    func, 
    max_attempts: int = 3, 
    delay: float = 1.0,
    backoff: float = 2.0
) -> Any:
    """Retry an async function with exponential backoff"""
    attempt = 0
    current_delay = delay
    
    while attempt < max_attempts:
        try:
            return await func()
        except Exception as e:
            attempt += 1
            if attempt >= max_attempts:
                raise
            logger.warning(f"Attempt {attempt} failed: {e}. Retrying in {current_delay}s...")
            await asyncio.sleep(current_delay)
            current_delay *= backoff

# Import required modules for JSON
import json
import uuid
from datetime import datetime

__all__ = [
    "SERVICE_CONFIG",
    "wait_for_service",
    "check_all_services",
    "check_services",
    "mock_pusher_as_websocket",
    "mock_ws_manager",
    "mock_db_session",
    "test_db",
    "http_client",
    "service_urls",
    "mock_repositories",
    "mock_agents",
    "MockWebSocketConnection",
    "MockWebSocketManager",
    "MockDatabaseSession",
    "retry_async"
]
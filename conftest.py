import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import pytest
import asyncio

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure async event loop
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Mock Redis client
@pytest.fixture
def mock_redis():
    with patch('redis.Redis') as mock:
        redis_instance = MagicMock()
        redis_instance.get.return_value = None
        redis_instance.set.return_value = True
        redis_instance.setex.return_value = True
        redis_instance.delete.return_value = 1
        redis_instance.exists.return_value = False
        redis_instance.incr.return_value = 1
        redis_instance.expire.return_value = True
        redis_instance.ttl.return_value = 3600
        mock.return_value = redis_instance
        yield redis_instance

# Mock database session
@pytest.fixture
def mock_db_session():
    session = MagicMock()
    session.query.return_value.filter.return_value.first.return_value = None
    session.add.return_value = None
    session.commit.return_value = None
    session.rollback.return_value = None
    return session

# Mock user for authentication tests
@pytest.fixture
def mock_user():
    return {
        'id': 'test_user_123',
        'username': 'test_user',
        'email': 'test@example.com',
        'role': 'student',
        'is_active': True
    }

# Mock API client
@pytest.fixture
def mock_api_client():
    client = MagicMock()
    client.get.return_value = MagicMock(
        status_code=200,
        json=lambda: {'status': 'success', 'data': {}}
    )
    client.post.return_value = MagicMock(
        status_code=201,
        json=lambda: {'status': 'success', 'data': {}}
    )
    return client

# Mock WebSocket
@pytest.fixture
def mock_websocket():
    ws = AsyncMock()
    ws.send_text = AsyncMock()
    ws.receive_text = AsyncMock(return_value='{"type": "test"}')
    ws.close = AsyncMock()
    return ws

# Mock LLM client
@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content="Generated response")
    llm.ainvoke = AsyncMock(return_value=MagicMock(content="Async response"))
    return llm

# Mock implementations module
@pytest.fixture(autouse=True)
def mock_implementations():
    with patch('apps.backend.agents.implementations') as mock:
        mock.get_llm = MagicMock(return_value=MagicMock())
        mock.create_content_agent = MagicMock(return_value=MagicMock())
        mock.create_quiz_agent = MagicMock(return_value=MagicMock())
        mock.create_terrain_agent = MagicMock(return_value=MagicMock())
        mock.create_script_agent = MagicMock(return_value=MagicMock())
        mock.create_review_agent = MagicMock(return_value=MagicMock())
        mock.create_testing_agent = MagicMock(return_value=MagicMock())
        yield mock

# Environment setup
@pytest.fixture(autouse=True)
def setup_test_env():
    os.environ['TESTING'] = 'true'
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    os.environ['REDIS_URL'] = 'redis://localhost:6379/0'
    os.environ['JWT_SECRET'] = 'test_secret_key'
    yield
    os.environ.pop('TESTING', None)

# Skip slow tests in CI
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "slow: marks tests as slow"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )

# Timeout for async tests
pytest_plugins = ('pytest_asyncio',)

"""
API test fixtures for ToolboxAI test suite.

Provides reusable API fixtures for testing.
"""
import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from typing import Dict, Any, Optional
import json
import jwt
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient
import redis
from faker import Faker

# Add parent directory to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

fake = Faker()


@pytest.fixture
def mock_request():
    """Create a mock FastAPI request object."""
    request = Mock()
    request.headers = {
        "content-type": "application/json",
        "user-agent": "TestClient/1.0",
        "host": "localhost:8008"
    }
    request.query_params = {}
    request.path_params = {}
    request.cookies = {}
    request.client = Mock(host="127.0.0.1", port=12345)
    request.url = Mock(path="/api/v1/test")
    request.method = "GET"
    request.state = Mock()
    return request


@pytest.fixture
def mock_auth_headers(test_user):
    """Create mock authentication headers with JWT token."""
    secret_key = "test_secret_key"
    algorithm = "HS256"
    
    payload = {
        "sub": test_user["id"],
        "username": test_user["username"],
        "role": test_user["role"],
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    
    token = jwt.encode(payload, secret_key, algorithm=algorithm)
    
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }


@pytest.fixture(scope="session")
def anyio_backend():
    """
    Configure anyio backend for async testing (2025 best practice).
    This ensures FastAPI uses asyncio for running async tests.
    """
    return "asyncio"


@pytest.fixture(scope="function")
def event_loop():
    """
    Create a new event loop for each test (2025 best practice).
    Prevents "event loop already running" errors.
    """
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_client():
    """Create a test client for FastAPI application."""
    app = FastAPI()
    
    # Add test routes
    @app.get("/health")
    def health_check():
        return {"status": "healthy"}
    
    @app.post("/api/v1/auth/login")
    def login(username: str, password: str):
        return {
            "access_token": "test_token",
            "token_type": "bearer",
            "user": {
                "id": "test_id",
                "username": username,
                "role": "student"
            }
        }
    
    @app.get("/api/v1/users/me")
    def get_current_user():
        return {
            "id": "test_id",
            "username": "test_user",
            "email": "test@example.com",
            "role": "student"
        }
    
    return TestClient(app)


@pytest.fixture
async def async_test_client():
    """
    Create an async test client for FastAPI application (2025 pattern).
    Uses proper context manager to ensure resources are cleaned up.
    """
    from httpx import AsyncClient, ASGITransport
    
    app = FastAPI()
    
    # Add test routes
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}
    
    @app.post("/api/v1/auth/login")
    async def login(username: str, password: str):
        return {
            "access_token": "test_token",
            "token_type": "bearer",
            "user": {
                "id": "test_id",
                "username": username,
                "role": "student"
            }
        }
    
    # Use ASGITransport for proper async testing (2025 best practice)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client."""
    client = Mock(spec=redis.Redis)
    client.get = Mock(return_value=None)
    client.set = Mock(return_value=True)
    client.delete = Mock(return_value=1)
    client.exists = Mock(return_value=False)
    client.expire = Mock(return_value=True)
    client.ttl = Mock(return_value=-1)
    client.keys = Mock(return_value=[])
    client.hget = Mock(return_value=None)
    client.hset = Mock(return_value=1)
    client.hdel = Mock(return_value=1)
    client.hgetall = Mock(return_value={})
    client.lpush = Mock(return_value=1)
    client.rpop = Mock(return_value=None)
    client.llen = Mock(return_value=0)
    client.publish = Mock(return_value=1)
    client.ping = Mock(return_value=True)
    return client


@pytest.fixture
def mock_async_redis_client():
    """Create a mock async Redis client."""
    client = AsyncMock()
    client.get = AsyncMock(return_value=None)
    client.set = AsyncMock(return_value=True)
    client.delete = AsyncMock(return_value=1)
    client.exists = AsyncMock(return_value=False)
    client.expire = AsyncMock(return_value=True)
    client.ttl = AsyncMock(return_value=-1)
    client.keys = AsyncMock(return_value=[])
    client.hget = AsyncMock(return_value=None)
    client.hset = AsyncMock(return_value=1)
    client.hdel = AsyncMock(return_value=1)
    client.hgetall = AsyncMock(return_value={})
    client.lpush = AsyncMock(return_value=1)
    client.rpop = AsyncMock(return_value=None)
    client.llen = AsyncMock(return_value=0)
    client.publish = AsyncMock(return_value=1)
    client.ping = AsyncMock(return_value=True)
    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection."""
    websocket = AsyncMock()
    websocket.accept = AsyncMock()
    websocket.send_text = AsyncMock()
    websocket.send_json = AsyncMock()
    websocket.send_bytes = AsyncMock()
    websocket.receive_text = AsyncMock(return_value='{"type": "ping"}')
    websocket.receive_json = AsyncMock(return_value={"type": "ping"})
    websocket.receive_bytes = AsyncMock(return_value=b"test")
    websocket.close = AsyncMock()
    websocket.client = Mock(host="127.0.0.1", port=12345)
    websocket.state = Mock()
    return websocket


@pytest.fixture
def mock_pusher_client():
    """Create a mock Pusher client."""
    client = Mock()
    client.trigger = Mock(return_value={"success": True})
    client.trigger_batch = Mock(return_value={"success": True})
    client.authenticate = Mock(return_value={
        "auth": "test_auth_string",
        "channel_data": "{}"
    })
    client.validate_webhook = Mock(return_value=True)
    client.get_channel_info = Mock(return_value={
        "occupied": True,
        "user_count": 5
    })
    return client


@pytest.fixture
def api_response_factory():
    """Factory for creating standard API responses."""
    def create_response(
        status: str = "success",
        data: Optional[Any] = None,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        status_code: int = 200
    ):
        response = {
            "status": status,
            "data": data or {},
            "message": message or "",
            "metadata": metadata or {}
        }
        return response, status_code
    
    return create_response


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client for external API calls."""
    client = Mock()
    
    # Mock GET request
    get_response = Mock()
    get_response.status_code = 200
    get_response.json = Mock(return_value={"result": "success"})
    get_response.text = '{"result": "success"}'
    get_response.headers = {"content-type": "application/json"}
    client.get = Mock(return_value=get_response)
    
    # Mock POST request
    post_response = Mock()
    post_response.status_code = 201
    post_response.json = Mock(return_value={"id": "created_id"})
    post_response.text = '{"id": "created_id"}'
    post_response.headers = {"content-type": "application/json"}
    client.post = Mock(return_value=post_response)
    
    # Mock PUT request
    put_response = Mock()
    put_response.status_code = 200
    put_response.json = Mock(return_value={"updated": True})
    put_response.text = '{"updated": true}'
    put_response.headers = {"content-type": "application/json"}
    client.put = Mock(return_value=put_response)
    
    # Mock DELETE request
    delete_response = Mock()
    delete_response.status_code = 204
    delete_response.text = ""
    delete_response.headers = {}
    client.delete = Mock(return_value=delete_response)
    
    return client


@pytest.fixture
def mock_oauth_provider():
    """Create a mock OAuth provider."""
    provider = Mock()
    provider.authorize_url = "https://oauth.example.com/authorize"
    provider.token_url = "https://oauth.example.com/token"
    provider.get_authorize_url = Mock(return_value="https://oauth.example.com/authorize?client_id=test")
    provider.get_token = Mock(return_value={
        "access_token": "mock_access_token",
        "refresh_token": "mock_refresh_token",
        "expires_in": 3600,
        "token_type": "Bearer"
    })
    provider.get_user_info = Mock(return_value={
        "id": "oauth_user_id",
        "email": "oauth@example.com",
        "name": "OAuth User"
    })
    return provider


@pytest.fixture
def mock_rate_limiter():
    """Create a mock rate limiter."""
    limiter = Mock()
    limiter.check = Mock(return_value=True)
    limiter.consume = Mock(return_value=True)
    limiter.reset = Mock()
    limiter.get_remaining = Mock(return_value=10)
    limiter.get_reset_time = Mock(return_value=datetime.utcnow() + timedelta(minutes=1))
    return limiter


@pytest.fixture
def mock_file_upload():
    """Create a mock file upload object."""
    file_upload = Mock()
    file_upload.filename = "test_file.pdf"
    file_upload.content_type = "application/pdf"
    file_upload.size = 1024 * 100  # 100KB
    file_upload.file = Mock()
    file_upload.file.read = Mock(return_value=b"fake file content")
    file_upload.file.seek = Mock()
    file_upload.file.tell = Mock(return_value=0)
    return file_upload


@pytest.fixture
def mock_background_task():
    """Create a mock background task."""
    task = Mock()
    task.id = "task_123"
    task.status = "pending"
    task.result = None
    task.error = None
    task.created_at = datetime.utcnow()
    task.updated_at = datetime.utcnow()
    task.run = AsyncMock()
    task.cancel = Mock()
    task.get_status = Mock(return_value="pending")
    task.get_result = Mock(return_value=None)
    return task


@pytest.fixture
def api_test_data():
    """Generate test data for API testing."""
    return {
        "users": [
            {
                "id": fake.uuid4(),
                "username": fake.user_name(),
                "email": fake.email(),
                "role": fake.random_element(["student", "teacher", "admin"])
            }
            for _ in range(5)
        ],
        "courses": [
            {
                "id": fake.uuid4(),
                "title": fake.sentence(nb_words=4),
                "description": fake.text(max_nb_chars=200),
                "subject": fake.random_element(["Mathematics", "Science", "English", "History"])
            }
            for _ in range(3)
        ],
        "assessments": [
            {
                "id": fake.uuid4(),
                "title": fake.sentence(nb_words=3),
                "type": fake.random_element(["quiz", "test", "assignment"]),
                "points": fake.random_int(min=10, max=100, step=10)
            }
            for _ in range(4)
        ]
    }
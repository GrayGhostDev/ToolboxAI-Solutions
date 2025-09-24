"""Common test mocks"""
from unittest.mock import Mock, MagicMock, patch

def mock_redis_client():
    """Mock Redis client"""
    client = MagicMock()
    client.get.return_value = None
    client.set.return_value = True
    client.delete.return_value = True
    client.exists.return_value = False
    return client

def mock_openai_client():
    """Mock OpenAI client"""
    client = MagicMock()
    client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Test response"))]
    )
    return client

def mock_database_connection():
    """Mock database connection"""
    conn = MagicMock()
    cursor = MagicMock()
    cursor.fetchone.return_value = (1,)
    cursor.fetchall.return_value = []
    conn.cursor.return_value = cursor
    return conn

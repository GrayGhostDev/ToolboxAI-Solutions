"""
Shared fixtures for core unit tests.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import os

# Mock OpenAI API for all tests in this directory
@pytest.fixture(autouse=True)
def mock_openai_api():
    """Automatically mock OpenAI API for all tests."""
    with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
        with patch('openai.ChatCompletion.create') as mock_create:
            mock_create.return_value = {
                'choices': [{
                    'message': {
                        'content': 'Mocked response'
                    }
                }]
            }
            yield mock_create

@pytest.fixture(autouse=True)
def disable_external_calls():
    """Disable external API calls in tests."""
    with patch.dict(os.environ, {
        'TESTING': 'true',
        'DISABLE_EXTERNAL_APIS': 'true'
    }):
        yield

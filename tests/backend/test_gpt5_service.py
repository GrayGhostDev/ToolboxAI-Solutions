import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest_asyncio
"""
Test suite for GPT-5 Service Implementation
Validates GPT-5 migration with fallback mechanisms
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import os

# Set test environment variables
os.environ["OPENAI_API_KEY"] = "test-api-key"
os.environ["GPT5_DEFAULT_MODEL"] = "gpt-5"
os.environ["GPT5_FALLBACK_ENABLED"] = "true"
os.environ["GPT5_FALLBACK_MODEL"] = "gpt-4o"

from apps.backend.services.openai_gpt5_service import GPT5Service, get_gpt5_service
from apps.backend.core.feature_flags import FeatureFlag


class TestGPT5Service:
    """Test suite for GPT-5 service"""

    @pytest.fixture
    def gpt5_service(self):
        """Create GPT-5 service instance for testing"""
        with patch('apps.backend.services.openai_gpt5_service.AsyncOpenAI'):
            with patch('apps.backend.services.openai_gpt5_service.OpenAI'):
                service = GPT5Service()
                # Mock feature flags
                service.feature_flags = Mock()
                return service

    @pytest.fixture
    def sample_messages(self):
        """Sample messages for testing"""
        return [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Explain quantum computing in simple terms."}
        ]

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_chat_completion_gpt5_enabled(self, gpt5_service, sample_messages):
        """Test chat completion with GPT-5 enabled"""
        # Setup mocks
        gpt5_service.feature_flags.is_enabled = Mock(return_value=True)

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Test response"), finish_reason="stop")]
        mock_response.model = "gpt-5"
        mock_response.usage = Mock(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            model_dump=Mock(return_value={"prompt_tokens": 100, "completion_tokens": 50})
        )

        gpt5_service.async_client.chat.completions.create = AsyncMock(return_value=mock_response)

        # Execute
        result = await gpt5_service.chat_completion(
            messages=sample_messages,
            model="gpt-4o",
            temperature=0.7
        )

        # Assert
        assert result["content"] == "Test response"
        assert result["model"] == "gpt-5"
        assert result["usage"]["prompt_tokens"] == 100
        assert gpt5_service.usage_stats["successful_requests"] == 1

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_chat_completion_gpt5_disabled(self, gpt5_service, sample_messages):
        """Test chat completion with GPT-5 disabled (uses fallback)"""
        # Setup mocks
        gpt5_service.feature_flags.is_enabled = Mock(return_value=False)

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="GPT-4 response"), finish_reason="stop")]
        mock_response.model = "gpt-4o"
        mock_response.usage = Mock(
            prompt_tokens=80,
            completion_tokens=40,
            model_dump=Mock(return_value={"prompt_tokens": 80, "completion_tokens": 40})
        )

        gpt5_service.async_client.chat.completions.create = AsyncMock(return_value=mock_response)

        # Execute
        result = await gpt5_service.chat_completion(
            messages=sample_messages,
            temperature=0.7
        )

        # Assert
        assert result["content"] == "GPT-4 response"
        assert result["model"] == "gpt-4o"
        assert "gpt5_features" in result

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_fallback_on_gpt5_failure(self, gpt5_service, sample_messages):
        """Test fallback mechanism when GPT-5 fails"""
        # Setup mocks
        gpt5_service.feature_flags.is_enabled = Mock(return_value=True)

        # First call fails (GPT-5)
        gpt5_service.async_client.chat.completions.create = AsyncMock(
            side_effect=[
                Exception("GPT-5 API error"),
                Mock(
                    choices=[Mock(message=Mock(content="Fallback response"), finish_reason="stop")],
                    model="gpt-4o",
                    usage=Mock(
                        prompt_tokens=75,
                        completion_tokens=35,
                        model_dump=Mock(return_value={"prompt_tokens": 75, "completion_tokens": 35})
                    )
                )
            ]
        )

        # Execute
        result = await gpt5_service.chat_completion(
            messages=sample_messages,
            model="gpt-5"
        )

        # Assert
        assert result["content"] == "Fallback response"
        assert result["fallback"] == True
        assert result["fallback_reason"] == "GPT-5 unavailable"
        assert gpt5_service.usage_stats["fallback_requests"] == 1

    def test_model_mapping(self, gpt5_service):
        """Test model mapping from GPT-4 to GPT-5"""
        # Test various mappings
        assert gpt5_service._get_gpt5_model("gpt-4") == "gpt-5-mini"
        assert gpt5_service._get_gpt5_model("gpt-4o") == "gpt-5"
        assert gpt5_service._get_gpt5_model("gpt-4o-mini") == "gpt-5-nano"
        assert gpt5_service._get_gpt5_model("gpt-4-turbo") == "gpt-5"
        assert gpt5_service._get_gpt5_model("gpt-3.5-turbo") == "gpt-5-nano"

        # Test GPT-5 models pass through
        assert gpt5_service._get_gpt5_model("gpt-5") == "gpt-5"
        assert gpt5_service._get_gpt5_model("gpt-5-mini") == "gpt-5-mini"

        # Test unknown model defaults to GPT-5
        assert gpt5_service._get_gpt5_model("unknown-model") == "gpt-5"

    def test_gpt5_parameters_complex(self, gpt5_service):
        """Test GPT-5 parameter addition for complex requests"""
        messages = [
            {"role": "user", "content": "Analyze this complex dataset and provide comprehensive insights with detailed explanations of patterns and anomalies."}
        ]

        kwargs = {}
        result = gpt5_service._add_gpt5_parameters(kwargs, messages)

        assert result["reasoning_effort"] == "high"
        assert result["verbosity"] == "high"

    def test_gpt5_parameters_simple(self, gpt5_service):
        """Test GPT-5 parameter addition for simple requests"""
        messages = [
            {"role": "user", "content": "What is 2+2?"}
        ]

        kwargs = {}
        result = gpt5_service._add_gpt5_parameters(kwargs, messages)

        assert result["reasoning_effort"] == "minimal"
        assert result["verbosity"] == "medium"  # Default

    def test_gpt5_parameters_brief(self, gpt5_service):
        """Test GPT-5 parameter addition for brief requests"""
        messages = [
            {"role": "user", "content": "Give me a brief summary of machine learning."}
        ]

        kwargs = {}
        result = gpt5_service._add_gpt5_parameters(kwargs, messages)

        assert result["verbosity"] == "low"

    def test_usage_tracking(self, gpt5_service):
        """Test usage statistics tracking"""
        # Create mock response
        mock_response = Mock()
        mock_response.usage = Mock(
            prompt_tokens=1000,
            completion_tokens=500
        )

        # Track usage for GPT-5
        gpt5_service._track_usage(mock_response, "gpt-5")

        assert gpt5_service.usage_stats["total_input_tokens"] == 1000
        assert gpt5_service.usage_stats["total_output_tokens"] == 500

        # Calculate expected cost: (1000/1M * 1.25) + (500/1M * 10.00)
        expected_cost = (1000 / 1_000_000 * 1.25) + (500 / 1_000_000 * 10.00)
        assert gpt5_service.usage_stats["total_cost"] == pytest.approx(expected_cost, rel=1e-6)

    def test_gpt5_features_extraction(self, gpt5_service):
        """Test extraction of GPT-5 specific features"""
        # Mock response with GPT-5 features
        mock_response = Mock()
        mock_response.usage = Mock(reasoning_tokens=250)
        mock_response.structured_output = {"key": "value"}

        features = gpt5_service._extract_gpt5_features(mock_response)

        assert features["reasoning_tokens"] == 250
        assert features["structured_output"] == {"key": "value"}

    def test_usage_stats_calculation(self, gpt5_service):
        """Test usage statistics calculations"""
        # Set up test stats
        gpt5_service.usage_stats = {
            "total_requests": 100,
            "successful_requests": 90,
            "fallback_requests": 10,
            "total_input_tokens": 50000,
            "total_output_tokens": 25000,
            "total_cost": 12.50
        }

        stats = gpt5_service.get_usage_stats()

        assert stats["average_cost_per_request"] == 0.125
        assert stats["fallback_rate"] == 0.1

    def test_reset_usage_stats(self, gpt5_service):
        """Test resetting usage statistics"""
        # Modify stats
        gpt5_service.usage_stats["total_requests"] = 50
        gpt5_service.usage_stats["total_cost"] = 10.0

        # Reset
        gpt5_service.reset_usage_stats()

        # Verify reset
        assert gpt5_service.usage_stats["total_requests"] == 0
        assert gpt5_service.usage_stats["total_cost"] == 0.0
        assert gpt5_service.usage_stats["successful_requests"] == 0

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_health_check(self, gpt5_service):
        """Test service health check"""
        # Mock feature flag check
        gpt5_service.feature_flags.is_enabled = Mock(return_value=True)

        # Mock API test
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="test"))]
        gpt5_service.async_client.chat.completions.create = AsyncMock(return_value=mock_response)

        health = await gpt5_service.health_check()

        assert health["service"] == "GPT5Service"
        assert health["status"] == "healthy"
        assert health["gpt5_enabled"] == True
        assert health["fallback_enabled"] == True
        assert "gpt-5" in health["models_available"]
        assert health["api_status"] == "connected"

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_stream_completion(self, gpt5_service, sample_messages):
        """Test streaming chat completion"""
        # Mock streaming response
        async def mock_stream():
            chunks = ["Hello", " ", "world", "!"]
            for chunk_text in chunks:
                chunk = Mock()
                chunk.choices = [Mock(delta=Mock(content=chunk_text))]
                yield chunk

        gpt5_service.feature_flags.is_enabled = Mock(return_value=True)
        gpt5_service.async_client.chat.completions.create = AsyncMock(return_value=mock_stream())

        # Execute
        result = await gpt5_service.chat_completion(
            messages=sample_messages,
            model="gpt-5",
            stream=True
        )

        # Collect streamed content
        content = ""
        async for chunk in result:
            content += chunk

        assert content == "Hello world!"

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_stream_completion_fallback(self, gpt5_service, sample_messages):
        """Test streaming with fallback on error"""
        # Mock error then successful fallback
        async def mock_error_stream():
            raise Exception("Streaming error")
            yield  # Never reached

        async def mock_fallback_stream():
            chunks = ["Fallback", " ", "response"]
            for chunk_text in chunks:
                chunk = Mock()
                chunk.choices = [Mock(delta=Mock(content=chunk_text))]
                yield chunk

        gpt5_service.feature_flags.is_enabled = Mock(return_value=True)
        gpt5_service.async_client.chat.completions.create = AsyncMock(
            side_effect=[mock_error_stream(), mock_fallback_stream()]
        )

        # Execute
        result = await gpt5_service.chat_completion(
            messages=sample_messages,
            model="gpt-5",
            stream=True
        )

        # Should get fallback response
        content = ""
        async for chunk in result:
            content += chunk

        assert content == "Fallback response"


class TestGPT5ServiceIntegration:
    """Integration tests for GPT-5 service"""

    @pytest.mark.asyncio
    @pytest.mark.skipif(not os.getenv("RUN_INTEGRATION_TESTS"), reason="Integration tests disabled")
    @pytest.mark.asyncio
async def test_real_api_connection(self):
        """Test real API connection (requires valid API key)"""
        service = get_gpt5_service()

        health = await service.health_check()

        assert health["status"] in ["healthy", "degraded"]
        assert "api_status" in health

    def test_singleton_pattern(self):
        """Test that get_gpt5_service returns singleton"""
        service1 = get_gpt5_service()
        service2 = get_gpt5_service()

        assert service1 is service2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=apps.backend.services.openai_gpt5_service"])
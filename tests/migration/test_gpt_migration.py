import pytest_asyncio
"""
Comprehensive test suite for GPT API migration
September 2025 - Phase 2 Implementation
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from freezegun import freeze_time

from core.api.gpt_migration_client import (
    GPTMigrationClient,
    GPTModel,
    MigrationConfig,
    ResponseCompatibilityLayer,
    PerformanceMonitor,
    MODEL_CAPABILITIES
)


class TestGPTMigrationClient:
    """Test suite for GPT migration client"""

    @pytest.fixture
    async def client(self):
        """Create test client instance"""
        config = MigrationConfig(
            primary_model=GPTModel.GPT_5,
            fallback_model=GPTModel.GPT_4_5,
            rollout_percentage=50.0,
            enable_fallback=True
        )
        client = GPTMigrationClient(
            api_key="test-api-key",
            config=config
        )
        yield client
        await client.close()

    @pytest.fixture
    def mock_response(self):
        """Mock API response"""
        return {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1695000000,
            "model": "gpt-5",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Test response"
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        }

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_model_selection_based_on_rollout(self, client):
        """Test model selection based on rollout percentage"""
        # Test with 50% rollout
        client.config.rollout_percentage = 50.0

        # Generate multiple requests and check distribution
        models_selected = []
        for i in range(100):
            request_hash = f"test-{i}"
            use_new = client._should_use_new_model(request_hash)
            models_selected.append(use_new)

        # Should be approximately 50/50 distribution
        new_model_count = sum(models_selected)
        assert 40 <= new_model_count <= 60  # Allow some variance

        # Test with 100% rollout
        client.config.rollout_percentage = 100.0
        assert client._should_use_new_model("any-request") is True

        # Test with 0% rollout
        client.config.rollout_percentage = 0.0
        assert client._should_use_new_model("any-request") is False

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_fallback_on_primary_failure(self, client, mock_response):
        """Test fallback mechanism when primary model fails"""

        with patch.object(client, '_make_request') as mock_request:
            # First call fails, second succeeds
            mock_request.side_effect = [
                Exception("Primary model failed"),
                mock_response
            ]

            response = await client.chat_completion(
                messages=[{"role": "user", "content": "test"}]
            )

            assert response is not None
            assert mock_request.call_count == 2

            # Verify models used
            calls = mock_request.call_args_list
            assert calls[0][0][0] in [GPTModel.GPT_5, GPTModel.GPT_4_5]
            assert calls[1][0][0] == client.config.fallback_model

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_response_normalization(self):
        """Test response format normalization across models"""
        compatibility = ResponseCompatibilityLayer()

        # Test GPT-5 enhanced format
        gpt5_response = {
            "id": "test-123",
            "enhanced_content": {
                "primary": "Main response content",
                "metadata": {"confidence": 0.95, "sources": ["doc1", "doc2"]}
            },
            "choices": [{
                "message": {"role": "assistant", "content": ""}
            }],
            "usage": {"total_tokens": 100}
        }

        normalized = compatibility.normalize_response(gpt5_response, GPTModel.GPT_5)

        assert normalized["choices"][0]["message"]["content"] == "Main response content"
        assert "function_call" in normalized["choices"][0]["message"]
        assert normalized["_migration_metadata"]["source_model"] == GPTModel.GPT_5.value

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_cache_functionality(self, client, mock_response):
        """Test response caching"""

        with patch.object(client, '_make_request', return_value=mock_response) as mock_request:
            messages = [{"role": "user", "content": "test"}]

            # First request should hit API
            response1 = await client.chat_completion(messages)
            assert mock_request.call_count == 1

            # Second identical request should use cache
            response2 = await client.chat_completion(messages)
            assert mock_request.call_count == 1  # No additional call

            assert response1 == response2

            # Different request should hit API again
            await client.chat_completion([{"role": "user", "content": "different"}])
            assert mock_request.call_count == 2

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_deprecation_warning(self, client):
        """Test deprecation warnings for old models"""

        # Set GPT-4.1 as primary with past deprecation date
        client.config.primary_model = GPTModel.GPT_4_1

        with freeze_time("2025-07-15"):  # After deprecation date
            with patch.object(client.client, 'post') as mock_post:
                mock_post.return_value = AsyncMock(
                    status_code=200,
                    json=lambda: {"choices": [{"message": {"content": "test"}}]}
                )

                with patch('structlog.get_logger') as mock_logger:
                    logger_instance = MagicMock()
                    mock_logger.return_value = logger_instance

                    await client.chat_completion(
                        messages=[{"role": "user", "content": "test"}]
                    )

                    # Verify deprecation warning was logged
                    logger_instance.warning.assert_called()
                    call_args = logger_instance.warning.call_args
                    assert call_args[0][0] == "using_deprecated_model"

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_streaming_support(self, client):
        """Test streaming chat completion"""

        async def mock_stream():
            """Mock streaming response"""
            chunks = [
                'data: {"choices": [{"delta": {"content": "Hello"}}]}',
                'data: {"choices": [{"delta": {"content": " world"}}]}',
                'data: [DONE]'
            ]
            for chunk in chunks:
                yield chunk

        with patch.object(client.client, 'stream') as mock_stream_ctx:
            mock_response = AsyncMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.aiter_lines = mock_stream
            mock_stream_ctx.return_value.__aenter__.return_value = mock_response

            chunks_received = []
            async for chunk in client.stream_chat_completion(
                messages=[{"role": "user", "content": "test"}]
            ):
                chunks_received.append(chunk)

            assert len(chunks_received) == 2

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_performance_metrics_collection(self, client, mock_response):
        """Test performance metrics are collected"""

        with patch.object(client.performance_monitor, 'record_request') as mock_record:
            with patch.object(client, '_make_request', return_value=mock_response):
                await client.chat_completion(
                    messages=[{"role": "user", "content": "test"}]
                )

                mock_record.assert_called_once()
                call_args = mock_record.call_args[1]
                assert call_args['success'] is True
                assert call_args['tokens_used'] == 30
                assert 'latency' in call_args

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_rollout_percentage_update(self, client):
        """Test dynamic rollout percentage updates"""

        initial_percentage = client.config.rollout_percentage

        await client.update_rollout_percentage(75.0)
        assert client.config.rollout_percentage == 75.0

        # Test invalid percentages
        with pytest.raises(ValueError):
            await client.update_rollout_percentage(150.0)

        with pytest.raises(ValueError):
            await client.update_rollout_percentage(-10.0)

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_health_check(self, client):
        """Test health check functionality"""

        with patch.object(client, '_make_request') as mock_request:
            # Mock healthy responses
            mock_request.return_value = {
                "choices": [{"message": {"content": "pong"}}],
                "usage": {"total_tokens": 1}
            }

            health = await client.health_check()

            assert "timestamp" in health
            assert "models" in health
            assert GPTModel.GPT_5.value in health["models"]
            assert GPTModel.GPT_4_5.value in health["models"]

            for model_status in health["models"].values():
                assert model_status["status"] == "healthy"
                assert "latency_ms" in model_status

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_max_tokens_adjustment(self, client):
        """Test max_tokens adjustment based on model capabilities"""

        client.config.primary_model = GPTModel.GPT_4_1

        with patch.object(client.client, 'post') as mock_post:
            mock_post.return_value = AsyncMock(
                status_code=200,
                json=lambda: {"choices": [{"message": {"content": "test"}}]}
            )

            # Request more tokens than model supports
            await client.chat_completion(
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10000  # More than GPT-4.1's 4096 limit
            )

            # Verify adjusted max_tokens in request
            call_args = mock_post.call_args[1]["json"]
            assert call_args["max_tokens"] <= MODEL_CAPABILITIES[GPTModel.GPT_4_1].max_tokens

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_concurrent_requests(self, client, mock_response):
        """Test handling of concurrent requests"""

        with patch.object(client, '_make_request', return_value=mock_response):
            # Create multiple concurrent requests
            tasks = [
                client.chat_completion(
                    messages=[{"role": "user", "content": f"test {i}"}]
                )
                for i in range(10)
            ]

            responses = await asyncio.gather(*tasks)

            assert len(responses) == 10
            assert all(r is not None for r in responses)


class TestPerformanceMonitor:
    """Test suite for performance monitoring"""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_metrics_recording(self):
        """Test metrics recording and buffering"""
        monitor = PerformanceMonitor()

        await monitor.record_request(
            model=GPTModel.GPT_5,
            latency=0.5,
            tokens_used=100,
            success=True
        )

        assert len(monitor.metrics_buffer) == 1
        metric = monitor.metrics_buffer[0]
        assert metric['model'] == GPTModel.GPT_5.value
        assert metric['latency_ms'] == 500
        assert metric['tokens_used'] == 100
        assert metric['success'] is True

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_metrics_buffer_flush(self):
        """Test automatic buffer flushing"""
        monitor = PerformanceMonitor()
        monitor.max_buffer_size = 5

        # Fill buffer beyond max size
        for i in range(6):
            await monitor.record_request(
                model=GPTModel.GPT_5,
                latency=0.1,
                tokens_used=10,
                success=True
            )

        # Buffer should have been flushed
        assert len(monitor.metrics_buffer) == 1


class TestMigrationIntegration:
    """Integration tests for migration process"""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_gradual_rollout_simulation(self):
        """Simulate gradual rollout from 0% to 100%"""
        config = MigrationConfig(
            primary_model=GPTModel.GPT_5,
            fallback_model=GPTModel.GPT_4_5,
            rollout_percentage=0.0
        )

        client = GPTMigrationClient(
            api_key="test-key",
            config=config
        )

        try:
            # Simulate gradual rollout
            rollout_stages = [0, 10, 25, 50, 75, 90, 100]

            for percentage in rollout_stages:
                await client.update_rollout_percentage(percentage)

                # Verify model selection matches rollout
                if percentage == 0:
                    assert not client._should_use_new_model("test")
                elif percentage == 100:
                    assert client._should_use_new_model("test")

        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_zero_downtime_migration(self):
        """Test zero-downtime migration scenario"""

        async def simulate_traffic(client: GPTMigrationClient, duration_seconds: int):
            """Simulate continuous traffic during migration"""
            start_time = time.time()
            request_count = 0
            errors = []

            while time.time() - start_time < duration_seconds:
                try:
                    with patch.object(client, '_make_request', return_value={"choices": []}):
                        await client.chat_completion(
                            messages=[{"role": "user", "content": f"request-{request_count}"}]
                        )
                    request_count += 1

                except Exception as e:
                    errors.append(str(e))

                await asyncio.sleep(0.1)

            return request_count, errors

        config = MigrationConfig(
            primary_model=GPTModel.GPT_4_5,
            fallback_model=GPTModel.GPT_4_1,
            rollout_percentage=0.0,
            enable_fallback=True
        )

        client = GPTMigrationClient("test-key", config)

        try:
            # Start traffic simulation
            traffic_task = asyncio.create_task(simulate_traffic(client, 2))

            # Perform gradual migration during traffic
            await asyncio.sleep(0.5)
            await client.update_rollout_percentage(50.0)
            await asyncio.sleep(0.5)
            await client.update_rollout_percentage(100.0)

            # Wait for traffic to complete
            request_count, errors = await traffic_task

            # Verify no errors during migration
            assert len(errors) == 0
            assert request_count > 0

        finally:
            await client.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=core.api.gpt_migration_client"])
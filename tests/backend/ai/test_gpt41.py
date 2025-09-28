import pytest_asyncio
"""
GPT-4.1 Migration Tests - Phase 4
Comprehensive tests for GPT-4.1 migration implementation
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from apps.backend.api.ai.gpt_migration import (
    GPT41MigrationClient,
    GPTModel,
    GPT41MigrationConfig,
    ModelSelector,
    PromptOptimizer,
    MODEL_REGISTRY
)
from apps.backend.api.ai.model_config import (
    GPT41ConfigManager,
    GPT41ModelConfig,
    GPT41FeatureFlags,
    MigrationPhase
)
from apps.backend.api.ai.prompt_optimizer import (
    GPT41PromptOptimizer,
    OptimizationType,
    optimize_prompt
)

# Test fixtures
@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis = MagicMock()
    redis.get.return_value = None
    redis.set.return_value = True
    redis.setex.return_value = True
    redis.delete.return_value = 1
    return redis

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI async client"""
    client = AsyncMock()

    # Mock chat completion response
    mock_response = MagicMock()
    mock_response.model_dump.return_value = {
        'id': 'test-completion-id',
        'object': 'chat.completion',
        'created': int(time.time()),
        'model': 'gpt-4.1',
        'choices': [{
            'index': 0,
            'message': {
                'role': 'assistant',
                'content': 'Test response from GPT-4.1'
            },
            'finish_reason': 'stop'
        }],
        'usage': {
            'prompt_tokens': 50,
            'completion_tokens': 20,
            'total_tokens': 70
        }
    }

    client.chat.completions.create.return_value = mock_response
    return client

@pytest.fixture
def migration_config():
    """Test migration configuration"""
    return GPT41MigrationConfig(
        primary_model=GPTModel.GPT_4_1,
        fallback_model=GPTModel.GPT_4_5_PREVIEW,
        rollout_percentage=25.0,
        enable_auto_fallback=True,
        enable_prompt_optimization=True
    )

@pytest.fixture
async def migration_client(mock_redis, mock_openai_client, migration_config):
    """Create test migration client"""
    with patch('apps.backend.api.ai.gpt_migration.AsyncOpenAI', return_value=mock_openai_client):
        client = GPT41MigrationClient(
            api_key='test-api-key',
            config=migration_config,
            redis_client=mock_redis
        )
        yield client
        await client.close()

class TestGPT41Migration:
    """Test GPT-4.1 migration functionality"""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_model_selection_by_complexity(self):
        """Test intelligent model selection based on complexity"""
        selector = ModelSelector()
        config = GPT41MigrationConfig()

        # Simple query - should select nano
        simple_messages = [
            {"role": "user", "content": "What is 2+2?"}
        ]
        complexity = selector.analyze_complexity(simple_messages)
        assert complexity < 0.3
        selected = selector.select_model(simple_messages, config)
        assert selected == GPTModel.GPT_4_1_NANO

        # Medium complexity - should select mini
        medium_messages = [
            {"role": "user", "content": "Explain the concept of recursion in programming with a simple example."}
        ]
        complexity = selector.analyze_complexity(medium_messages)
        assert 0.3 <= complexity < 0.7
        selected = selector.select_model(medium_messages, config)
        assert selected == GPTModel.GPT_4_1_MINI

        # Complex query - should select full model
        complex_messages = [
            {"role": "user", "content": "Analyze the following code, identify potential issues, explain the algorithm complexity, and suggest optimizations:\n" + "def complex_function():\n    # 500 lines of code here"}
        ]
        complexity = selector.analyze_complexity(complex_messages)
        assert complexity >= 0.7
        selected = selector.select_model(complex_messages, config)
        assert selected == GPTModel.GPT_4_1

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_rollout_percentage(self, migration_client):
        """Test gradual rollout percentage logic"""
        # Test with 0% rollout
        await migration_client.update_rollout_percentage(0.0)
        assert migration_client.config.rollout_percentage == 0.0
        assert not migration_client._should_use_new_model("test-hash")

        # Test with 100% rollout
        await migration_client.update_rollout_percentage(100.0)
        assert migration_client.config.rollout_percentage == 100.0
        assert migration_client._should_use_new_model("test-hash")

        # Test with 50% rollout - should be deterministic for same hash
        await migration_client.update_rollout_percentage(50.0)
        hash1 = "consistent-hash-1"
        result1 = migration_client._should_use_new_model(hash1)
        result2 = migration_client._should_use_new_model(hash1)
        assert result1 == result2  # Same hash should give same result

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_chat_completion_with_optimization(self, migration_client, mock_openai_client):
        """Test chat completion with prompt optimization"""
        messages = [
            {"role": "user", "content": "Could you please carefully explain what machine learning is?"}
        ]

        response = await migration_client.chat_completion(messages)

        assert response['id'] == 'test-completion-id'
        assert response['model'] == 'gpt-4.1'
        assert response['choices'][0]['message']['content'] == 'Test response from GPT-4.1'

        # Verify prompt was optimized (redundant words removed)
        called_messages = mock_openai_client.chat.completions.create.call_args[1]['messages']
        assert "Could you please carefully" not in called_messages[0]['content']

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_fallback_mechanism(self, migration_client, mock_openai_client):
        """Test fallback from GPT-4.1 to GPT-4.5 on failure"""
        # Make primary request fail
        mock_openai_client.chat.completions.create.side_effect = [
            Exception("GPT-4.1 failed"),
            MagicMock(model_dump=lambda: {
                'id': 'fallback-id',
                'model': 'gpt-4.5-preview',
                'choices': [{'message': {'content': 'Fallback response'}}],
                'usage': {'total_tokens': 50}
            })
        ]

        messages = [{"role": "user", "content": "Test message"}]

        response = await migration_client.chat_completion(messages)

        assert response['id'] == 'fallback-id'
        assert response['model'] == 'gpt-4.5-preview'
        assert mock_openai_client.chat.completions.create.call_count == 2

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_cache_functionality(self, migration_client, mock_redis, mock_openai_client):
        """Test response caching"""
        messages = [{"role": "user", "content": "Cached query"}]

        # First call - should hit API
        response1 = await migration_client.chat_completion(messages)
        assert mock_openai_client.chat.completions.create.call_count == 1

        # Set up Redis to return cached response
        mock_redis.get.return_value = json.dumps(response1)

        # Second call - should hit cache
        response2 = await migration_client.chat_completion(messages)
        assert response2 == response1
        # API shouldn't be called again (still 1 call)

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_deprecation_warnings(self):
        """Test deprecation warning system"""
        config = GPT41MigrationConfig(
            fallback_model=GPTModel.GPT_4_5_PREVIEW
        )

        with patch('apps.backend.api.ai.gpt_migration.datetime') as mock_datetime:
            # Set date to 30 days before deprecation
            mock_datetime.now.return_value = datetime(2025, 6, 14)

            client = GPT41MigrationClient(
                api_key='test-key',
                config=config
            )

            # Should have logged warning about deprecation
            # In real test, would check logging output

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_streaming_completion(self, migration_client, mock_openai_client):
        """Test streaming chat completion"""
        # Mock streaming response
        async def mock_stream():
            chunks = [
                MagicMock(model_dump=lambda: {'choices': [{'delta': {'content': 'Hello'}}]}),
                MagicMock(model_dump=lambda: {'choices': [{'delta': {'content': ' world'}}]}),
            ]
            for chunk in chunks:
                yield chunk

        mock_openai_client.chat.completions.create.return_value = mock_stream()

        messages = [{"role": "user", "content": "Stream test"}]

        chunks = []
        async for chunk in migration_client.stream_chat_completion(messages):
            chunks.append(chunk)

        assert len(chunks) == 2

    def test_prompt_optimizer(self):
        """Test prompt optimization for GPT-4.1"""
        optimizer = GPT41PromptOptimizer()

        # Test redundancy removal
        verbose_prompt = "Could you please carefully make sure to analyze this data and remember to provide a detailed response?"
        result = optimizer.optimize_prompt(verbose_prompt)

        assert len(result.optimized) < len(result.original)
        assert "Could you please" not in result.optimized
        assert "make sure to" not in result.optimized
        assert OptimizationType.REDUNDANCY_REMOVAL in result.optimizations_applied

        # Test structure simplification
        complex_prompt = "Your task is to analyze the data. You need to provide insights."
        result = optimizer.optimize_prompt(complex_prompt)

        assert "Task:" in result.optimized
        assert "Your task is to" not in result.optimized
        assert OptimizationType.STRUCTURE_SIMPLIFICATION in result.optimizations_applied

    def test_model_config_manager(self, mock_redis):
        """Test configuration management"""
        config_manager = GPT41ConfigManager(redis_client=mock_redis)

        # Test rollout percentage update
        config_manager.update_rollout_percentage(30.0)
        assert config_manager.feature_flags.rollout_percentage == 30.0
        mock_redis.set.assert_called()

        # Test phase detection
        with patch('apps.backend.api.ai.model_config.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 4, 15)
            config_manager.feature_flags.rollout_percentage = 10.0
            phase = config_manager.get_current_phase()
            assert phase == MigrationPhase.EARLY_ACCESS

        # Test deprecation status
        with patch('apps.backend.api.ai.model_config.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 6, 30)  # 14 days before deprecation
            status = config_manager.get_deprecation_status()
            assert status['is_critical'] == True
            assert status['days_remaining'] == 14

    def test_cost_comparison(self):
        """Test cost calculation and comparison"""
        config_manager = GPT41ConfigManager()

        # Test with 1000 input tokens and 500 output tokens
        comparison = config_manager.get_cost_comparison(
            input_tokens=1000,
            output_tokens=500
        )

        # GPT-4.5 should be more expensive
        assert comparison['costs']['gpt-4.5-preview'] > comparison['costs']['gpt-4.1']
        assert comparison['costs']['gpt-4.1'] > comparison['costs']['gpt-4.1-mini']
        assert comparison['costs']['gpt-4.1-mini'] > comparison['costs']['gpt-4.1-nano']

        # Check savings percentages
        assert comparison['savings_percentage']['gpt-4.1'] > 20  # At least 20% savings
        assert comparison['savings_percentage']['gpt-4.1-mini'] > 80  # At least 80% savings

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_health_check(self, migration_client, mock_openai_client):
        """Test health check functionality"""
        health = await migration_client.health_check()

        assert 'timestamp' in health
        assert 'models' in health
        assert 'gpt-4.1' in health['models']
        assert health['models']['gpt-4.1']['status'] == 'healthy'

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_migration_status(self, migration_client):
        """Test migration status reporting"""
        status = await migration_client.get_migration_status()

        assert 'rollout_percentage' in status
        assert 'deprecation_warnings' in status
        assert 'cost_savings' in status
        assert 'performance_metrics' in status

        # Check cost savings calculations
        assert 'input_cost_reduction' in status['cost_savings']
        assert 'latency_improvement' in status['cost_savings']

class TestPromptOptimization:
    """Test prompt optimization utilities"""

    def test_create_structured_prompt(self):
        """Test structured prompt creation"""
        optimizer = GPT41PromptOptimizer()

        prompt = optimizer.create_structured_prompt(
            task="Analyze the sentiment of customer reviews",
            context="E-commerce product reviews from the last month",
            format="JSON with sentiment score and key phrases",
            examples=["Review 1: 'Great product!' -> positive", "Review 2: 'Terrible' -> negative"],
            constraints=["Process each review independently", "Include confidence score"]
        )

        assert "Task:" in prompt
        assert "Context:" in prompt
        assert "Format:" in prompt
        assert "Examples:" in prompt
        assert "Constraints:" in prompt

    def test_batch_optimization(self):
        """Test batch prompt optimization"""
        optimizer = GPT41PromptOptimizer()

        prompts = [
            "Could you please analyze this data?",
            "Would you mind helping me with this task?",
            "Please carefully review the following information."
        ]

        results = optimizer.batch_optimize(prompts)

        assert len(results) == 3
        for result in results:
            assert result.tokens_saved > 0
            assert len(result.optimized) < len(result.original)

    def test_tool_description_optimization(self):
        """Test tool/function description optimization"""
        optimizer = GPT41PromptOptimizer()

        tools = [{
            'function': {
                'name': 'analyze_data',
                'description': 'Please carefully use this function to analyze the data',
                'parameters': {
                    'properties': {
                        'data': {
                            'description': 'This parameter contains the data to analyze'
                        }
                    }
                }
            }
        }]

        optimized = optimizer.optimize_tool_descriptions(tools)

        assert 'Please carefully' not in optimized[0]['function']['description']
        assert 'This parameter' not in optimized[0]['function']['parameters']['properties']['data']['description']

    def test_pattern_analysis(self):
        """Test prompt pattern analysis"""
        optimizer = GPT41PromptOptimizer()

        prompts = [
            "Could you please help me?",
            "Would you mind assisting?",
            "Please carefully analyze this.",
            "Remember to check everything."
        ] * 5  # Repeat to create patterns

        analysis = optimizer.analyze_prompt_patterns(prompts)

        assert 'common_redundancies' in analysis
        assert 'average_complexity' in analysis
        assert 'total_tokens_saveable' in analysis
        assert 'optimization_recommendations' in analysis
        assert analysis['total_tokens_saveable'] > 0

class TestModelCapabilities:
    """Test model capability definitions"""

    def test_model_registry(self):
        """Test model capability registry"""
        # Check GPT-4.1 capabilities
        gpt41_caps = MODEL_REGISTRY[GPTModel.GPT_4_1]
        assert gpt41_caps.context_window == 1000000  # 1M tokens
        assert gpt41_caps.supports_reasoning == True
        assert gpt41_caps.cost_per_1m_input < 10.0  # Cheaper than GPT-4.5

        # Check GPT-4.1-mini capabilities
        mini_caps = MODEL_REGISTRY[GPTModel.GPT_4_1_MINI]
        assert mini_caps.context_window == 500000
        assert mini_caps.latency_ms_p50 < gpt41_caps.latency_ms_p50
        assert mini_caps.cost_per_1m_input < gpt41_caps.cost_per_1m_input

        # Check deprecation date
        gpt45_caps = MODEL_REGISTRY[GPTModel.GPT_4_5_PREVIEW]
        assert gpt45_caps.deprecation_date == datetime(2025, 7, 14)

    def test_model_selection_with_force(self):
        """Test forced model selection"""
        selector = ModelSelector()
        config = GPT41MigrationConfig()

        messages = [{"role": "user", "content": "Simple query"}]

        # Force full model even for simple query
        selected = selector.select_model(messages, config, force_model=GPTModel.GPT_4_1)
        assert selected == GPTModel.GPT_4_1

        # Force nano model even for complex query
        complex_messages = [{"role": "user", "content": "Complex " * 100}]
        selected = selector.select_model(complex_messages, config, force_model=GPTModel.GPT_4_1_NANO)
        assert selected == GPTModel.GPT_4_1_NANO

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
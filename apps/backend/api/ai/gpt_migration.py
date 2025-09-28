"""
GPT-4.1 Migration Service - Phase 4 Implementation
Handles migration from GPT-4.5 Preview to GPT-4.1
Critical: GPT-4.5 Preview deprecation on July 14, 2025
"""

import os
import json
import time
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
import logging

import httpx
from openai import AsyncOpenAI, OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
import redis.asyncio as redis
from prometheus_client import Counter, Histogram, Gauge

logger = logging.getLogger(__name__)

# Metrics
gpt_api_requests = Counter(
    "gpt41_api_requests_total", "Total GPT-4.1 API requests", ["model", "status"]
)
gpt_api_latency = Histogram("gpt41_api_latency_seconds", "GPT-4.1 API latency", ["model"])
gpt_api_tokens = Counter("gpt41_api_tokens_total", "Total tokens used", ["model", "type"])
gpt_migration_progress = Gauge("gpt41_migration_progress_percent", "GPT-4.1 migration progress")


class GPTModel(Enum):
    """GPT Models for migration - Updated for Phase 4"""

    # Deprecated models
    GPT_4_5_PREVIEW = "gpt-4.5-preview"  # DEPRECATED July 14, 2025
    GPT_4_TURBO = "gpt-4-turbo"  # Legacy

    # Target models (GPT-4.1 family)
    GPT_4_1 = "gpt-4.1"  # Main model - superior performance
    GPT_4_1_MINI = "gpt-4.1-mini"  # 83% cost reduction, 50% latency reduction
    GPT_4_1_NANO = "gpt-4.1-nano"  # Fastest and cheapest

    # Alternative models for specific use cases
    GPT_4O = "gpt-4o"  # Original GPT-4 optimized
    GPT_5 = "gpt-5"  # Future model (when available)


@dataclass
class ModelCapabilities:
    """Model capabilities and specifications"""

    context_window: int
    max_output_tokens: int
    supports_tools: bool  # Updated from supports_functions
    supports_vision: bool
    supports_streaming: bool
    supports_reasoning: bool
    cost_per_1m_input: float  # Cost per 1M tokens
    cost_per_1m_output: float
    latency_ms_p50: int  # Median latency
    deprecation_date: Optional[datetime] = None


MODEL_REGISTRY = {
    GPTModel.GPT_4_5_PREVIEW: ModelCapabilities(
        context_window=128000,
        max_output_tokens=4096,
        supports_tools=True,
        supports_vision=True,
        supports_streaming=True,
        supports_reasoning=False,
        cost_per_1m_input=10.0,
        cost_per_1m_output=30.0,
        latency_ms_p50=2000,
        deprecation_date=datetime(2025, 7, 14),  # CRITICAL DEADLINE
    ),
    GPTModel.GPT_4_1: ModelCapabilities(
        context_window=1000000,  # 1M tokens
        max_output_tokens=16384,
        supports_tools=True,
        supports_vision=True,
        supports_streaming=True,
        supports_reasoning=True,
        cost_per_1m_input=7.5,  # 25% cheaper than GPT-4.5
        cost_per_1m_output=22.5,  # 25% cheaper
        latency_ms_p50=1500,  # 25% faster
        deprecation_date=None,
    ),
    GPTModel.GPT_4_1_MINI: ModelCapabilities(
        context_window=500000,
        max_output_tokens=8192,
        supports_tools=True,
        supports_vision=True,
        supports_streaming=True,
        supports_reasoning=False,
        cost_per_1m_input=1.7,  # 83% cost reduction
        cost_per_1m_output=5.0,
        latency_ms_p50=1000,  # 50% latency reduction
        deprecation_date=None,
    ),
    GPTModel.GPT_4_1_NANO: ModelCapabilities(
        context_window=200000,
        max_output_tokens=4096,
        supports_tools=True,
        supports_vision=False,
        supports_streaming=True,
        supports_reasoning=False,
        cost_per_1m_input=0.5,  # Cheapest
        cost_per_1m_output=1.5,
        latency_ms_p50=500,  # Fastest
        deprecation_date=None,
    ),
    GPTModel.GPT_4O: ModelCapabilities(
        context_window=128000,
        max_output_tokens=16384,
        supports_tools=True,
        supports_vision=True,
        supports_streaming=True,
        supports_reasoning=False,
        cost_per_1m_input=5.0,
        cost_per_1m_output=15.0,
        latency_ms_p50=1800,
        deprecation_date=None,
    ),
    GPTModel.GPT_5: ModelCapabilities(
        context_window=2000000,  # 2M tokens
        max_output_tokens=32768,
        supports_tools=True,
        supports_vision=True,
        supports_streaming=True,
        supports_reasoning=True,
        cost_per_1m_input=15.0,
        cost_per_1m_output=45.0,
        latency_ms_p50=2500,
        deprecation_date=None,
    ),
}


@dataclass
class GPT41MigrationConfig:
    """Configuration for GPT-4.1 migration"""

    primary_model: GPTModel = GPTModel.GPT_4_1
    fallback_model: GPTModel = GPTModel.GPT_4_5_PREVIEW
    rollout_percentage: float = 0.0  # Start at 0%
    enable_auto_fallback: bool = True
    enable_prompt_optimization: bool = True
    enable_cost_optimization: bool = True
    cache_ttl_seconds: int = 3600
    max_retries: int = 3
    timeout_seconds: int = 60

    # Model selection strategy
    use_nano_for_simple: bool = True  # Use nano for simple queries
    use_mini_for_standard: bool = True  # Use mini for standard queries
    complexity_threshold: float = 0.7  # Threshold for using full model


@dataclass
class PromptOptimization:
    """Prompt optimization for GPT-4.1's literal instruction following"""

    original_prompt: str
    optimized_prompt: str
    optimization_type: str
    tokens_saved: int


class PromptOptimizer:
    """Optimizes prompts for GPT-4.1's more literal instruction following"""

    @staticmethod
    def optimize_for_gpt41(prompt: str, model: GPTModel) -> PromptOptimization:
        """
        Optimize prompt for GPT-4.1's characteristics:
        - More literal instruction following
        - Better at following exact specifications
        - Less need for elaborate instructions
        """
        original = prompt
        optimized = prompt
        tokens_saved = 0

        if model in [GPTModel.GPT_4_1, GPTModel.GPT_4_1_MINI, GPTModel.GPT_4_1_NANO]:
            # Remove redundant instructions that GPT-4.1 handles better
            replacements = [
                # Remove verbose instructions
                ("Please carefully", ""),
                ("Make sure to", ""),
                ("Remember to", ""),
                ("It's important that you", ""),
                ("Be sure to", ""),
                # Simplify instructions
                ("Could you please", ""),
                ("I would like you to", ""),
                ("Can you help me", ""),
                # Remove redundant formatting instructions (GPT-4.1 follows format better)
                ("Format your response as follows:", "Format:"),
                ("Provide your answer in the following format:", "Format:"),
                # Simplify task descriptions
                ("Your task is to", "Task:"),
                ("You need to", ""),
            ]

            for old, new in replacements:
                optimized = optimized.replace(old, new)

            # Clean up extra spaces
            optimized = " ".join(optimized.split())

            # Calculate approximate tokens saved (rough estimate)
            tokens_saved = max(0, len(original.split()) - len(optimized.split()))

        return PromptOptimization(
            original_prompt=original,
            optimized_prompt=optimized,
            optimization_type="gpt41_literal",
            tokens_saved=tokens_saved,
        )


class ModelSelector:
    """Intelligent model selection based on query complexity"""

    @staticmethod
    def analyze_complexity(messages: List[Dict[str, str]]) -> float:
        """
        Analyze query complexity to select appropriate model variant
        Returns complexity score 0.0 (simple) to 1.0 (complex)
        """
        complexity = 0.0

        # Get last user message
        user_messages = [m for m in messages if m.get("role") == "user"]
        if not user_messages:
            return 0.5

        last_message = user_messages[-1].get("content", "")

        # Complexity factors
        factors = {
            "length": min(len(last_message) / 1000, 1.0) * 0.2,  # Long queries
            "code": (
                0.3
                if any(
                    kw in last_message.lower()
                    for kw in ["code", "function", "class", "def", "implement"]
                )
                else 0
            ),
            "reasoning": (
                0.4
                if any(
                    kw in last_message.lower()
                    for kw in ["explain", "why", "how", "analyze", "compare"]
                )
                else 0
            ),
            "math": (
                0.3
                if any(
                    kw in last_message.lower()
                    for kw in ["calculate", "solve", "equation", "formula"]
                )
                else 0
            ),
            "creative": (
                0.3
                if any(
                    kw in last_message.lower() for kw in ["create", "generate", "write", "design"]
                )
                else 0
            ),
            "multi_step": (
                0.2
                if any(kw in last_message.lower() for kw in ["step", "first", "then", "finally"])
                else 0
            ),
        }

        complexity = sum(factors.values())

        # Context length factor
        total_length = sum(len(m.get("content", "")) for m in messages)
        if total_length > 10000:
            complexity += 0.2

        return min(complexity, 1.0)

    @staticmethod
    def select_model(
        messages: List[Dict[str, str]],
        config: GPT41MigrationConfig,
        force_model: Optional[GPTModel] = None,
    ) -> GPTModel:
        """Select appropriate GPT-4.1 variant based on complexity"""

        if force_model:
            return force_model

        complexity = ModelSelector.analyze_complexity(messages)

        # Model selection based on complexity
        if config.use_nano_for_simple and complexity < 0.3:
            return GPTModel.GPT_4_1_NANO
        elif config.use_mini_for_standard and complexity < config.complexity_threshold:
            return GPTModel.GPT_4_1_MINI
        else:
            return GPTModel.GPT_4_1


class GPT41MigrationClient:
    """
    Production-ready GPT-4.1 migration client
    Handles transition from GPT-4.5 Preview before July 14, 2025 deadline
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        config: Optional[GPT41MigrationConfig] = None,
        redis_client: Optional[redis.Redis] = None,
    ):
        # API setup
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required")

        # Initialize clients
        self.client = OpenAI(api_key=self.api_key)
        self.async_client = AsyncOpenAI(api_key=self.api_key)

        # Configuration
        self.config = config or GPT41MigrationConfig()

        # Components
        self.prompt_optimizer = PromptOptimizer()
        self.model_selector = ModelSelector()

        # Redis for caching and state
        self.redis_client = redis_client
        self._init_redis()

        # Response cache
        self._response_cache: Dict[str, Dict[str, Any]] = {}

        # Check deprecation warning
        self._check_deprecation_status()

        logger.info(
            "GPT-4.1 migration client initialized",
            primary_model=self.config.primary_model.value,
            fallback_model=self.config.fallback_model.value,
            rollout_percentage=self.config.rollout_percentage,
        )

    def _init_redis(self):
        """Initialize Redis connection if not provided"""
        if not self.redis_client:
            try:
                self.redis_client = redis.Redis(
                    host=os.getenv("REDIS_HOST", "localhost"),
                    port=int(os.getenv("REDIS_PORT", 6379)),
                    db=0,
                    decode_responses=True,
                )
            except Exception as e:
                logger.warning(f"Redis initialization failed: {e}")
                self.redis_client = None

    def _check_deprecation_status(self):
        """Check and warn about deprecation deadlines"""
        now = datetime.now()

        for model, capabilities in MODEL_REGISTRY.items():
            if capabilities.deprecation_date:
                days_until_deprecation = (capabilities.deprecation_date - now).days

                if days_until_deprecation <= 0:
                    logger.error(
                        f"MODEL DEPRECATED: {model.value} was deprecated on {capabilities.deprecation_date}",
                        model=model.value,
                        deprecated_date=capabilities.deprecation_date.isoformat(),
                    )
                elif days_until_deprecation <= 30:
                    logger.warning(
                        f"URGENT: {model.value} deprecating in {days_until_deprecation} days",
                        model=model.value,
                        deprecation_date=capabilities.deprecation_date.isoformat(),
                        days_remaining=days_until_deprecation,
                    )
                elif days_until_deprecation <= 90:
                    logger.info(
                        f"Notice: {model.value} deprecating in {days_until_deprecation} days",
                        model=model.value,
                        deprecation_date=capabilities.deprecation_date.isoformat(),
                    )

    def _should_use_new_model(self, request_hash: str) -> bool:
        """Determine if request should use GPT-4.1 based on rollout"""
        if self.config.rollout_percentage >= 100:
            return True
        if self.config.rollout_percentage <= 0:
            return False

        # Consistent hashing for gradual rollout
        hash_int = int(hashlib.md5(request_hash.encode()).hexdigest()[:8], 16)
        return (hash_int % 100) < self.config.rollout_percentage

    def _get_cache_key(self, messages: List[Dict[str, str]], model: GPTModel, **kwargs) -> str:
        """Generate cache key for deduplication"""
        content = json.dumps({"model": model.value, "messages": messages, **kwargs}, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

    async def _check_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Check Redis cache for response"""
        if not self.redis_client:
            return None

        try:
            cached = await self.redis_client.get(f"gpt41:cache:{cache_key}")
            if cached:
                logger.info(f"Cache hit for key: {cache_key[:8]}")
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache check failed: {e}")

        return None

    async def _save_cache(self, cache_key: str, response: Dict[str, Any]):
        """Save response to Redis cache"""
        if not self.redis_client:
            return

        try:
            await self.redis_client.setex(
                f"gpt41:cache:{cache_key}", self.config.cache_ttl_seconds, json.dumps(response)
            )
        except Exception as e:
            logger.warning(f"Cache save failed: {e}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=60))
    async def _make_request(
        self, model: GPTModel, messages: List[Dict[str, str]], **kwargs
    ) -> Dict[str, Any]:
        """Make API request with retry logic"""

        # Check model capabilities
        capabilities = MODEL_REGISTRY[model]

        # Adjust parameters based on capabilities
        if "max_tokens" in kwargs:
            kwargs["max_tokens"] = min(kwargs["max_tokens"], capabilities.max_output_tokens)

        # Add tool support for GPT-4.1 (renamed from functions)
        if "functions" in kwargs and capabilities.supports_tools:
            kwargs["tools"] = kwargs.pop("functions")

        start_time = time.time()

        try:
            # Use tool descriptions from API field (GPT-4.1 requirement)
            response = await self.async_client.chat.completions.create(
                model=model.value, messages=messages, **kwargs
            )

            latency = time.time() - start_time

            # Convert response to dict
            response_dict = response.model_dump()

            # Record metrics
            gpt_api_requests.labels(model=model.value, status="success").inc()
            gpt_api_latency.labels(model=model.value).observe(latency)

            if "usage" in response_dict:
                usage = response_dict["usage"]
                gpt_api_tokens.labels(model=model.value, type="input").inc(
                    usage.get("prompt_tokens", 0)
                )
                gpt_api_tokens.labels(model=model.value, type="output").inc(
                    usage.get("completion_tokens", 0)
                )

            logger.info(
                "API request successful",
                model=model.value,
                latency_ms=latency * 1000,
                tokens=response_dict.get("usage", {}).get("total_tokens", 0),
            )

            return response_dict

        except Exception as e:
            latency = time.time() - start_time

            gpt_api_requests.labels(model=model.value, status="failure").inc()

            logger.error(
                "API request failed", model=model.value, error=str(e), latency_ms=latency * 1000
            )

            raise

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[GPTModel] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        force_model: Optional[GPTModel] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create chat completion with automatic GPT-4.1 migration

        Args:
            messages: Chat messages
            model: Override model selection
            temperature: Sampling temperature
            max_tokens: Max tokens in response
            force_model: Force specific model variant
            **kwargs: Additional parameters

        Returns:
            Chat completion response
        """

        # Model selection logic
        if not model:
            # Intelligent model selection based on complexity
            selected_model = self.model_selector.select_model(messages, self.config, force_model)

            # Check rollout percentage for migration
            cache_key_base = self._get_cache_key(messages, selected_model)
            if self._should_use_new_model(cache_key_base):
                model = selected_model
            else:
                model = self.config.fallback_model

        logger.info(
            "Model selected", model=model.value, rollout_percentage=self.config.rollout_percentage
        )

        # Update migration progress
        gpt_migration_progress.set(self.config.rollout_percentage)

        # Optimize prompt for GPT-4.1 if enabled
        if self.config.enable_prompt_optimization and model in [
            GPTModel.GPT_4_1,
            GPTModel.GPT_4_1_MINI,
            GPTModel.GPT_4_1_NANO,
        ]:
            optimized_messages = []
            for msg in messages:
                if msg.get("role") == "user":
                    optimization = self.prompt_optimizer.optimize_for_gpt41(msg["content"], model)
                    optimized_messages.append(
                        {"role": msg["role"], "content": optimization.optimized_prompt}
                    )
                    if optimization.tokens_saved > 0:
                        logger.info(f"Prompt optimized, tokens saved: {optimization.tokens_saved}")
                else:
                    optimized_messages.append(msg)
            messages = optimized_messages

        # Check cache
        cache_key = self._get_cache_key(messages, model, temperature=temperature, **kwargs)
        cached_response = await self._check_cache(cache_key)
        if cached_response:
            return cached_response

        # Primary request
        try:
            response = await self._make_request(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            # Cache successful response
            await self._save_cache(cache_key, response)

            return response

        except Exception as primary_error:
            logger.error(f"Primary model failed: {primary_error}")

            # Fallback logic
            if self.config.enable_auto_fallback and model != self.config.fallback_model:
                logger.info(f"Attempting fallback to {self.config.fallback_model.value}")

                try:
                    response = await self._make_request(
                        model=self.config.fallback_model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        **kwargs,
                    )

                    return response

                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {fallback_error}")
                    raise Exception(
                        f"Both {model.value} and {self.config.fallback_model.value} failed"
                    ) from primary_error

            raise

    async def stream_chat_completion(
        self, messages: List[Dict[str, str]], model: Optional[GPTModel] = None, **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat completion with GPT-4.1"""

        if not model:
            model = self.model_selector.select_model(messages, self.config)

        # Check if model supports streaming
        if not MODEL_REGISTRY[model].supports_streaming:
            logger.warning(f"{model.value} doesn't support streaming, using regular completion")
            response = await self.chat_completion(messages, model=model, **kwargs)
            yield response
            return

        try:
            stream = await self.async_client.chat.completions.create(
                model=model.value, messages=messages, stream=True, **kwargs
            )

            async for chunk in stream:
                yield chunk.model_dump()

        except Exception as e:
            logger.error(f"Streaming failed: {e}")

            # Fallback to non-streaming
            if self.config.enable_auto_fallback:
                response = await self.chat_completion(messages, model=model, **kwargs)
                yield response
            else:
                raise

    async def update_rollout_percentage(self, percentage: float):
        """Update rollout percentage for gradual migration"""

        if not 0 <= percentage <= 100:
            raise ValueError(f"Percentage must be 0-100, got {percentage}")

        old = self.config.rollout_percentage
        self.config.rollout_percentage = percentage

        # Save to Redis
        if self.redis_client:
            await self.redis_client.set("gpt41:rollout_percentage", str(percentage))

        gpt_migration_progress.set(percentage)

        logger.info(
            "Rollout percentage updated",
            old=old,
            new=percentage,
            primary_model=self.config.primary_model.value,
        )

    async def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status and metrics"""

        status = {
            "timestamp": datetime.utcnow().isoformat(),
            "rollout_percentage": self.config.rollout_percentage,
            "primary_model": self.config.primary_model.value,
            "fallback_model": self.config.fallback_model.value,
            "deprecation_warnings": [],
            "cost_savings": {},
            "performance_metrics": {},
        }

        # Check deprecation status
        now = datetime.now()
        for model, capabilities in MODEL_REGISTRY.items():
            if capabilities.deprecation_date:
                days_remaining = (capabilities.deprecation_date - now).days
                if days_remaining <= 90:
                    status["deprecation_warnings"].append(
                        {
                            "model": model.value,
                            "deprecation_date": capabilities.deprecation_date.isoformat(),
                            "days_remaining": days_remaining,
                            "severity": "critical" if days_remaining <= 30 else "warning",
                        }
                    )

        # Calculate cost savings (GPT-4.1 vs GPT-4.5)
        gpt45_cost = MODEL_REGISTRY[GPTModel.GPT_4_5_PREVIEW]
        gpt41_cost = MODEL_REGISTRY[GPTModel.GPT_4_1]

        status["cost_savings"] = {
            "input_cost_reduction": f"{((gpt45_cost.cost_per_1m_input - gpt41_cost.cost_per_1m_input) / gpt45_cost.cost_per_1m_input) * 100:.1f}%",
            "output_cost_reduction": f"{((gpt45_cost.cost_per_1m_output - gpt41_cost.cost_per_1m_output) / gpt45_cost.cost_per_1m_output) * 100:.1f}%",
            "latency_improvement": f"{((gpt45_cost.latency_ms_p50 - gpt41_cost.latency_ms_p50) / gpt45_cost.latency_ms_p50) * 100:.1f}%",
        }

        # Add performance metrics from Redis if available
        if self.redis_client:
            try:
                total_requests = await self.redis_client.get("gpt41:metrics:total_requests") or "0"
                success_rate = await self.redis_client.get("gpt41:metrics:success_rate") or "0"
                avg_latency = await self.redis_client.get("gpt41:metrics:avg_latency") or "0"

                status["performance_metrics"] = {
                    "total_requests": int(total_requests),
                    "success_rate": float(success_rate),
                    "avg_latency_ms": float(avg_latency),
                }
            except Exception as e:
                logger.warning(f"Could not fetch metrics from Redis: {e}")

        return status

    async def health_check(self) -> Dict[str, Any]:
        """Check health of GPT-4.1 endpoints"""

        health = {"timestamp": datetime.utcnow().isoformat(), "models": {}}

        test_message = [{"role": "user", "content": "Hello"}]

        for model in [GPTModel.GPT_4_1, GPTModel.GPT_4_1_MINI, GPTModel.GPT_4_1_NANO]:
            try:
                start = time.time()
                await self._make_request(model=model, messages=test_message, max_tokens=5)

                health["models"][model.value] = {
                    "status": "healthy",
                    "latency_ms": (time.time() - start) * 1000,
                }

            except Exception as e:
                health["models"][model.value] = {"status": "unhealthy", "error": str(e)}

        return health

    async def close(self):
        """Cleanup resources"""
        await self.async_client.close()
        if self.redis_client:
            await self.redis_client.close()
        logger.info("GPT-4.1 migration client closed")


# Convenience function for dependency injection
_migration_client: Optional[GPT41MigrationClient] = None


def get_gpt41_client() -> GPT41MigrationClient:
    """Get or create GPT-4.1 migration client singleton"""
    global _migration_client
    if _migration_client is None:
        _migration_client = GPT41MigrationClient()
    return _migration_client


async def get_async_gpt41_client() -> GPT41MigrationClient:
    """Get or create async GPT-4.1 migration client"""
    return get_gpt41_client()

"""
GPT API Migration Client - Production-Ready Implementation
Supports migration from GPT-4.1 to GPT-4.5/GPT-5 with zero downtime
September 2025 - Phase 2 Implementation
"""

import hashlib
import json
import time
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import httpx
import structlog
from prometheus_client import Counter, Gauge, Histogram
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)

# Metrics for monitoring migration
api_requests = Counter("gpt_api_requests_total", "Total GPT API requests", ["model", "status"])
api_latency = Histogram("gpt_api_latency_seconds", "GPT API latency", ["model"])
api_errors = Counter("gpt_api_errors_total", "GPT API errors", ["model", "error_type"])
migration_progress = Gauge("gpt_migration_progress_percent", "GPT migration progress percentage")
fallback_triggers = Counter("gpt_fallback_triggers_total", "GPT fallback triggers")


class GPTModel(Enum):
    """Supported GPT models with migration path"""

    GPT_4_1 = "gpt-4.1-turbo"  # Deprecated July 14, 2025
    GPT_4_5 = "gpt-4.5-turbo"  # Current stable
    GPT_5 = "gpt-5"  # Latest model (Sept 2025)
    GPT_5_TURBO = "gpt-5-turbo"  # Performance optimized


@dataclass
class ModelCapabilities:
    """Model-specific capabilities and limits"""

    context_window: int
    max_tokens: int
    supports_functions: bool
    supports_vision: bool
    supports_streaming: bool
    cost_per_1k_input: float
    cost_per_1k_output: float
    deprecation_date: Optional[datetime] = None


# Model capability registry
MODEL_CAPABILITIES = {
    GPTModel.GPT_4_1: ModelCapabilities(
        context_window=128000,
        max_tokens=4096,
        supports_functions=True,
        supports_vision=True,
        supports_streaming=True,
        cost_per_1k_input=0.01,
        cost_per_1k_output=0.03,
        deprecation_date=datetime(2025, 7, 14),
    ),
    GPTModel.GPT_4_5: ModelCapabilities(
        context_window=256000,
        max_tokens=8192,
        supports_functions=True,
        supports_vision=True,
        supports_streaming=True,
        cost_per_1k_input=0.008,
        cost_per_1k_output=0.024,
    ),
    GPTModel.GPT_5: ModelCapabilities(
        context_window=512000,
        max_tokens=16384,
        supports_functions=True,
        supports_vision=True,
        supports_streaming=True,
        cost_per_1k_input=0.015,
        cost_per_1k_output=0.045,
    ),
    GPTModel.GPT_5_TURBO: ModelCapabilities(
        context_window=256000,
        max_tokens=8192,
        supports_functions=True,
        supports_vision=True,
        supports_streaming=True,
        cost_per_1k_input=0.01,
        cost_per_1k_output=0.03,
    ),
}


@dataclass
class MigrationConfig:
    """Migration configuration with feature flags"""

    primary_model: GPTModel = GPTModel.GPT_4_5
    fallback_model: GPTModel = GPTModel.GPT_4_1
    rollout_percentage: float = 0.0  # 0-100
    enable_fallback: bool = True
    enable_response_compatibility: bool = True
    enable_performance_metrics: bool = True
    max_retries: int = 3
    timeout_seconds: int = 60
    cache_responses: bool = True
    cache_ttl_seconds: int = 3600


class ResponseCompatibilityLayer:
    """Ensures consistent response format across model versions"""

    @staticmethod
    def normalize_response(response: dict[str, Any], source_model: GPTModel) -> dict[str, Any]:
        """Normalize response format across different model versions"""

        # Handle GPT-5 enhanced response format
        if source_model in [GPTModel.GPT_5, GPTModel.GPT_5_TURBO]:
            if "enhanced_content" in response:
                # Convert enhanced format to standard format
                response["choices"][0]["message"]["content"] = response["enhanced_content"][
                    "primary"
                ]

                # Add metadata as function call if present
                if "metadata" in response["enhanced_content"]:
                    response["choices"][0]["message"]["function_call"] = {
                        "name": "metadata",
                        "arguments": json.dumps(response["enhanced_content"]["metadata"]),
                    }

        # Ensure consistent structure
        normalized = {
            "id": response.get("id", f"migration-{int(time.time())}"),
            "object": "chat.completion",
            "created": response.get("created", int(time.time())),
            "model": str(source_model.value),
            "choices": response.get("choices", []),
            "usage": response.get("usage", {}),
            "system_fingerprint": response.get("system_fingerprint"),
        }

        # Add migration metadata
        normalized["_migration_metadata"] = {
            "source_model": source_model.value,
            "normalized_at": datetime.utcnow().isoformat(),
            "compatibility_version": "1.0.0",
        }

        return normalized


class PerformanceMonitor:
    """Monitors and collects performance metrics"""

    def __init__(self):
        self.metrics_buffer: list[dict[str, Any]] = []
        self.max_buffer_size = 1000

    async def record_request(
        self,
        model: GPTModel,
        latency: float,
        tokens_used: int,
        success: bool,
        error_type: Optional[str] = None,
    ):
        """Record request metrics"""

        # Update Prometheus metrics
        api_requests.labels(model=model.value, status="success" if success else "failure").inc()
        api_latency.labels(model=model.value).observe(latency)

        if not success and error_type:
            api_errors.labels(model=model.value, error_type=error_type).inc()

        # Buffer detailed metrics for analysis
        metric = {
            "timestamp": datetime.utcnow().isoformat(),
            "model": model.value,
            "latency_ms": latency * 1000,
            "tokens_used": tokens_used,
            "success": success,
            "error_type": error_type,
        }

        self.metrics_buffer.append(metric)

        # Flush buffer if full
        if len(self.metrics_buffer) >= self.max_buffer_size:
            await self._flush_metrics()

    async def _flush_metrics(self):
        """Flush metrics to persistent storage"""
        if not self.metrics_buffer:
            return

        # TODO: Send to metrics aggregation service
        logger.info(
            "flushing_performance_metrics",
            count=len(self.metrics_buffer),
            sample=self.metrics_buffer[-1],
        )

        self.metrics_buffer.clear()


class GPTMigrationClient:
    """Production-ready GPT API client with migration support"""

    def __init__(
        self,
        api_key: str,
        config: Optional[MigrationConfig] = None,
        base_url: str = "https://api.openai.com/v1",
    ):
        self.api_key = api_key
        self.config = config or MigrationConfig()
        self.base_url = base_url
        self.compatibility_layer = ResponseCompatibilityLayer()
        self.performance_monitor = PerformanceMonitor()

        # HTTP client with connection pooling
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.config.timeout_seconds),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

        # Response cache for deduplication
        self._response_cache: dict[str, dict[str, Any]] = {}

        logger.info(
            "gpt_migration_client_initialized",
            primary_model=self.config.primary_model.value,
            fallback_model=self.config.fallback_model.value,
            rollout_percentage=self.config.rollout_percentage,
        )

    def _should_use_new_model(self, request_hash: str) -> bool:
        """Determine if request should use new model based on rollout percentage"""
        if self.config.rollout_percentage >= 100:
            return True
        if self.config.rollout_percentage <= 0:
            return False

        # Consistent hashing for gradual rollout
        hash_int = int(hashlib.md5(request_hash.encode()).hexdigest()[:8], 16)
        return (hash_int % 100) < self.config.rollout_percentage

    def _get_cache_key(self, messages: list[dict[str, str]], **kwargs) -> str:
        """Generate cache key for request deduplication"""
        content = json.dumps({"messages": messages, **kwargs}, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=60))
    async def _make_request(
        self, model: GPTModel, messages: list[dict[str, str]], **kwargs
    ) -> dict[str, Any]:
        """Make API request with retry logic"""

        # Check deprecation
        capabilities = MODEL_CAPABILITIES[model]
        if capabilities.deprecation_date and datetime.now() > capabilities.deprecation_date:
            logger.warning(
                "using_deprecated_model",
                model=model.value,
                deprecation_date=capabilities.deprecation_date.isoformat(),
            )

        # Prepare request
        request_data = {"model": model.value, "messages": messages, **kwargs}

        # Validate against model capabilities
        if "max_tokens" in kwargs and kwargs["max_tokens"] > capabilities.max_tokens:
            kwargs["max_tokens"] = capabilities.max_tokens
            logger.warning(
                "max_tokens_adjusted",
                requested=kwargs["max_tokens"],
                adjusted=capabilities.max_tokens,
            )

        start_time = time.time()

        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions", json=request_data
            )
            response.raise_for_status()

            latency = time.time() - start_time
            result = response.json()

            # Record metrics
            await self.performance_monitor.record_request(
                model=model,
                latency=latency,
                tokens_used=result.get("usage", {}).get("total_tokens", 0),
                success=True,
            )

            return result

        except httpx.HTTPStatusError as e:
            latency = time.time() - start_time

            await self.performance_monitor.record_request(
                model=model,
                latency=latency,
                tokens_used=0,
                success=False,
                error_type=f"http_{e.response.status_code}",
            )

            logger.error(
                "api_request_failed",
                model=model.value,
                status_code=e.response.status_code,
                error=str(e),
            )

            raise

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Create chat completion with automatic model selection and fallback

        Args:
            messages: List of message dictionaries
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            **kwargs: Additional parameters

        Returns:
            Normalized response dictionary
        """

        # Generate cache key
        cache_key = self._get_cache_key(messages, temperature=temperature, **kwargs)

        # Check cache
        if self.config.cache_responses and cache_key in self._response_cache:
            cached = self._response_cache[cache_key]
            if time.time() - cached["_cached_at"] < self.config.cache_ttl_seconds:
                logger.info("returning_cached_response", cache_key=cache_key[:8])
                return cached["response"]

        # Determine model based on rollout
        use_new_model = self._should_use_new_model(cache_key)
        primary_model = self.config.primary_model if use_new_model else self.config.fallback_model

        logger.info(
            "selecting_model",
            primary=primary_model.value,
            use_new_model=use_new_model,
            rollout_percentage=self.config.rollout_percentage,
        )

        # Update migration progress metric
        migration_progress.set(self.config.rollout_percentage)

        try:
            # Primary request
            response = await self._make_request(
                model=primary_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            # Normalize response
            if self.config.enable_response_compatibility:
                response = self.compatibility_layer.normalize_response(response, primary_model)

            # Cache successful response
            if self.config.cache_responses:
                self._response_cache[cache_key] = {
                    "response": response,
                    "_cached_at": time.time(),
                }

                # Cleanup old cache entries
                if len(self._response_cache) > 1000:
                    self._cleanup_cache()

            return response

        except Exception as primary_error:
            logger.error(
                "primary_model_failed",
                model=primary_model.value,
                error=str(primary_error),
            )

            # Attempt fallback if enabled
            if self.config.enable_fallback and primary_model != self.config.fallback_model:
                fallback_triggers.inc()

                logger.info(
                    "attempting_fallback",
                    fallback_model=self.config.fallback_model.value,
                )

                try:
                    response = await self._make_request(
                        model=self.config.fallback_model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        **kwargs,
                    )

                    # Normalize fallback response
                    if self.config.enable_response_compatibility:
                        response = self.compatibility_layer.normalize_response(
                            response, self.config.fallback_model
                        )

                    return response

                except Exception as fallback_error:
                    logger.error("fallback_also_failed", error=str(fallback_error))

                    # Re-raise original error with context
                    raise Exception(
                        f"Both primary ({primary_model.value}) and fallback "
                        f"({self.config.fallback_model.value}) failed"
                    ) from primary_error

            raise primary_error

    async def stream_chat_completion(
        self, messages: list[dict[str, str]], **kwargs
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream chat completion with model migration support"""

        # Determine model
        cache_key = self._get_cache_key(messages, **kwargs)
        use_new_model = self._should_use_new_model(cache_key)
        model = self.config.primary_model if use_new_model else self.config.fallback_model

        # Check model supports streaming
        if not MODEL_CAPABILITIES[model].supports_streaming:
            logger.warning(
                "model_does_not_support_streaming",
                model=model.value,
                falling_back_to_regular=True,
            )
            response = await self.chat_completion(messages, **kwargs)
            yield response
            return

        request_data = {
            "model": model.value,
            "messages": messages,
            "stream": True,
            **kwargs,
        }

        try:
            async with self.client.stream(
                "POST", f"{self.base_url}/chat/completions", json=request_data
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break

                        try:
                            chunk = json.loads(data)

                            # Normalize streaming chunk
                            if self.config.enable_response_compatibility:
                                chunk = self.compatibility_layer.normalize_response(chunk, model)

                            yield chunk

                        except json.JSONDecodeError:
                            logger.warning("invalid_streaming_chunk", data=data)
                            continue

        except Exception as e:
            logger.error("streaming_failed", model=model.value, error=str(e))

            # Fallback to non-streaming
            if self.config.enable_fallback:
                response = await self.chat_completion(messages, **kwargs)
                yield response
            else:
                raise

    def _cleanup_cache(self):
        """Remove expired cache entries"""
        current_time = time.time()
        expired_keys = [
            key
            for key, value in self._response_cache.items()
            if current_time - value["_cached_at"] > self.config.cache_ttl_seconds
        ]

        for key in expired_keys:
            del self._response_cache[key]

        logger.info(
            "cache_cleanup",
            removed=len(expired_keys),
            remaining=len(self._response_cache),
        )

    async def update_rollout_percentage(self, percentage: float):
        """Update rollout percentage for gradual migration"""

        if not 0 <= percentage <= 100:
            raise ValueError(f"Rollout percentage must be between 0 and 100, got {percentage}")

        old_percentage = self.config.rollout_percentage
        self.config.rollout_percentage = percentage

        migration_progress.set(percentage)

        logger.info(
            "rollout_percentage_updated",
            old=old_percentage,
            new=percentage,
            primary_model=self.config.primary_model.value,
        )

    async def health_check(self) -> dict[str, Any]:
        """Check health of API endpoints"""

        health_status = {"timestamp": datetime.utcnow().isoformat(), "models": {}}

        for model in [self.config.primary_model, self.config.fallback_model]:
            try:
                start = time.time()
                await self._make_request(
                    model=model,
                    messages=[{"role": "user", "content": "ping"}],
                    max_tokens=1,
                )

                health_status["models"][model.value] = {
                    "status": "healthy",
                    "latency_ms": (time.time() - start) * 1000,
                    "deprecation_warning": (
                        MODEL_CAPABILITIES[model].deprecation_date.isoformat()
                        if MODEL_CAPABILITIES[model].deprecation_date
                        else None
                    ),
                }

            except Exception as e:
                health_status["models"][model.value] = {
                    "status": "unhealthy",
                    "error": str(e),
                }

        return health_status

    async def close(self):
        """Cleanup resources"""
        await self.performance_monitor._flush_metrics()
        await self.client.aclose()
        logger.info("gpt_migration_client_closed")

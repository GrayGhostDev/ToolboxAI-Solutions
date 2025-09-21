"""
OpenAI GPT-5 Service Implementation
Handles migration from GPT-4 to GPT-5 with fallback support
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime
import json

from openai import AsyncOpenAI, OpenAI
from openai.types.chat import ChatCompletionMessage
from openai.types.chat.chat_completion import Choice

from apps.backend.core.feature_flags import get_feature_flags, FeatureFlag

logger = logging.getLogger(__name__)

class GPT5Service:
    """
    OpenAI GPT-5 service with backward compatibility and fallback support
    Implements the latest GPT-5 features while maintaining GPT-4 compatibility
    """

    def __init__(self):
        """Initialize GPT-5 service with API clients"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not configured in environment")

        # Initialize OpenAI clients
        self.client = OpenAI(api_key=api_key)
        self.async_client = AsyncOpenAI(api_key=api_key)

        # Get feature flags manager
        self.feature_flags = get_feature_flags()

        # GPT-5 model configurations
        self.gpt5_models = {
            "gpt-5": {
                "name": "gpt-5",
                "context_window": 400000,
                "max_output": 128000,
                "supports_reasoning": True,
                "cost_input": 1.25,  # per 1M tokens
                "cost_output": 10.00  # per 1M tokens
            },
            "gpt-5-mini": {
                "name": "gpt-5-mini",
                "context_window": 200000,
                "max_output": 64000,
                "supports_reasoning": True,
                "cost_input": 0.25,
                "cost_output": 2.00
            },
            "gpt-5-nano": {
                "name": "gpt-5-nano",
                "context_window": 100000,
                "max_output": 32000,
                "supports_reasoning": False,
                "cost_input": 0.05,
                "cost_output": 0.40
            },
            "gpt-5-chat-latest": {
                "name": "gpt-5-chat-latest",
                "context_window": 400000,
                "max_output": 128000,
                "supports_reasoning": False,
                "cost_input": 1.25,
                "cost_output": 10.00
            }
        }

        # Model migration mapping (GPT-4 -> GPT-5)
        self.model_mapping = {
            "gpt-4": "gpt-5-mini",
            "gpt-4o": "gpt-5",
            "gpt-4o-mini": "gpt-5-nano",
            "gpt-4-turbo": "gpt-5",
            "gpt-4-1106-preview": "gpt-5",
            "gpt-3.5-turbo": "gpt-5-nano"
        }

        # Fallback configuration
        self.fallback_enabled = os.getenv("GPT5_FALLBACK_ENABLED", "true").lower() == "true"
        self.fallback_model = os.getenv("GPT5_FALLBACK_MODEL", "gpt-4o")

        # Default GPT-5 parameters
        self.default_reasoning_effort = os.getenv("GPT5_REASONING_EFFORT", "medium")
        self.default_verbosity = os.getenv("GPT5_VERBOSITY", "medium")

        # Usage tracking
        self.usage_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "fallback_requests": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0.0
        }

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Enhanced chat completion with GPT-5 features and fallback support

        Args:
            messages: List of message dictionaries
            model: Model to use (will be mapped to GPT-5 if enabled)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional parameters

        Returns:
            Dict containing response content and metadata
        """
        self.usage_stats["total_requests"] += 1

        # Check if GPT-5 migration is enabled
        if self.feature_flags and self.feature_flags.is_enabled(FeatureFlag.GPT5_MIGRATION):
            model = self._get_gpt5_model(model)
            kwargs = self._add_gpt5_parameters(kwargs, messages)
            logger.info(f"Using GPT-5 model: {model}")
        else:
            model = model or self.fallback_model
            logger.info(f"GPT-5 migration disabled, using: {model}")

        try:
            # Make the API call
            if stream:
                return await self._stream_completion(model, messages, temperature, max_tokens, **kwargs)
            else:
                response = await self.async_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )

                # Track usage
                self._track_usage(response, model)
                self.usage_stats["successful_requests"] += 1

                return {
                    "content": response.choices[0].message.content,
                    "model": response.model,
                    "usage": response.usage.model_dump() if response.usage else None,
                    "finish_reason": response.choices[0].finish_reason,
                    "gpt5_features": self._extract_gpt5_features(response)
                }

        except Exception as e:
            logger.error(f"GPT-5 API error: {e}")

            # Attempt fallback if enabled
            if self.fallback_enabled and model.startswith("gpt-5"):
                logger.warning(f"Falling back from {model} to {self.fallback_model}")
                return await self._fallback_completion(messages, temperature, max_tokens, stream, **kwargs)

            raise

    async def _stream_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: Optional[int],
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Handle streaming completions"""
        try:
            stream = await self.async_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            if self.fallback_enabled:
                # Fallback for streaming
                kwargs.pop("reasoning_effort", None)
                kwargs.pop("verbosity", None)
                stream = await self.async_client.chat.completions.create(
                    model=self.fallback_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                    **kwargs
                )
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content

    def _get_gpt5_model(self, requested_model: Optional[str]) -> str:
        """
        Get appropriate GPT-5 model based on request

        Args:
            requested_model: Model requested by user

        Returns:
            GPT-5 model name
        """
        if requested_model and requested_model.startswith("gpt-5"):
            # Already a GPT-5 model
            return requested_model

        # Map old models to GPT-5 equivalents
        if requested_model in self.model_mapping:
            mapped_model = self.model_mapping[requested_model]
            logger.debug(f"Mapped {requested_model} -> {mapped_model}")
            return mapped_model

        # Default to GPT-5
        return os.getenv("GPT5_DEFAULT_MODEL", "gpt-5")

    def _add_gpt5_parameters(self, kwargs: Dict, messages: List[Dict]) -> Dict:
        """
        Add GPT-5 specific parameters based on context

        Args:
            kwargs: Existing parameters
            messages: Message history

        Returns:
            Updated parameters dict
        """
        # Calculate message complexity
        total_length = sum(len(m.get("content", "")) for m in messages)
        has_complex_request = any(
            keyword in str(m.get("content", "")).lower()
            for m in messages
            for keyword in ["analyze", "explain", "complex", "detailed", "comprehensive"]
        )

        # Set reasoning effort based on complexity
        if "reasoning_effort" not in kwargs:
            if total_length > 2000 or has_complex_request:
                kwargs["reasoning_effort"] = "high"
            elif total_length > 500:
                kwargs["reasoning_effort"] = "medium"
            else:
                kwargs["reasoning_effort"] = "minimal"

        # Set verbosity based on user preference
        if "verbosity" not in kwargs:
            if any(word in str(messages).lower() for word in ["detailed", "comprehensive", "thorough"]):
                kwargs["verbosity"] = "high"
            elif any(word in str(messages).lower() for word in ["brief", "short", "concise", "summary"]):
                kwargs["verbosity"] = "low"
            else:
                kwargs["verbosity"] = self.default_verbosity

        logger.debug(f"GPT-5 parameters: reasoning={kwargs.get('reasoning_effort')}, verbosity={kwargs.get('verbosity')}")
        return kwargs

    async def _fallback_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fallback to GPT-4 models when GPT-5 fails

        Args:
            messages: Message history
            temperature: Sampling temperature
            max_tokens: Max tokens
            stream: Whether to stream
            **kwargs: Additional parameters

        Returns:
            Fallback response
        """
        self.usage_stats["fallback_requests"] += 1

        # Remove GPT-5 specific parameters
        gpt5_params = ["reasoning_effort", "verbosity"]
        for param in gpt5_params:
            kwargs.pop(param, None)

        try:
            if stream:
                return await self._stream_completion(
                    self.fallback_model,
                    messages,
                    temperature,
                    max_tokens,
                    **kwargs
                )

            response = await self.async_client.chat.completions.create(
                model=self.fallback_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            self._track_usage(response, self.fallback_model)

            return {
                "content": response.choices[0].message.content,
                "model": response.model,
                "usage": response.usage.model_dump() if response.usage else None,
                "finish_reason": response.choices[0].finish_reason,
                "fallback": True,
                "fallback_reason": "GPT-5 unavailable"
            }

        except Exception as e:
            logger.error(f"Fallback also failed: {e}")
            raise

    def _track_usage(self, response: Any, model: str):
        """Track token usage and costs"""
        if not response.usage:
            return

        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens

        self.usage_stats["total_input_tokens"] += input_tokens
        self.usage_stats["total_output_tokens"] += output_tokens

        # Calculate cost based on model
        if model in self.gpt5_models:
            model_info = self.gpt5_models[model]
            input_cost = (input_tokens / 1_000_000) * model_info["cost_input"]
            output_cost = (output_tokens / 1_000_000) * model_info["cost_output"]
            total_cost = input_cost + output_cost
            self.usage_stats["total_cost"] += total_cost

            logger.debug(f"Usage: {input_tokens} input, {output_tokens} output, ${total_cost:.4f}")

    def _extract_gpt5_features(self, response: Any) -> Dict[str, Any]:
        """Extract GPT-5 specific features from response"""
        features = {}

        # Check for reasoning tokens (GPT-5 specific)
        if hasattr(response.usage, "reasoning_tokens"):
            features["reasoning_tokens"] = response.usage.reasoning_tokens

        # Check for structured output
        if hasattr(response, "structured_output"):
            features["structured_output"] = response.structured_output

        return features if features else None

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            **self.usage_stats,
            "average_cost_per_request": (
                self.usage_stats["total_cost"] / self.usage_stats["total_requests"]
                if self.usage_stats["total_requests"] > 0
                else 0
            ),
            "fallback_rate": (
                self.usage_stats["fallback_requests"] / self.usage_stats["total_requests"]
                if self.usage_stats["total_requests"] > 0
                else 0
            )
        }

    def reset_usage_stats(self):
        """Reset usage statistics"""
        self.usage_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "fallback_requests": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0.0
        }

    async def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        health = {
            "service": "GPT5Service",
            "status": "healthy",
            "gpt5_enabled": self.feature_flags.is_enabled(FeatureFlag.GPT5_MIGRATION) if self.feature_flags else False,
            "fallback_enabled": self.fallback_enabled,
            "models_available": list(self.gpt5_models.keys()),
            "usage_stats": self.get_usage_stats()
        }

        # Test API connectivity
        try:
            test_response = await self.async_client.chat.completions.create(
                model="gpt-4o-mini",  # Use a cheap model for testing
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            health["api_status"] = "connected"
        except Exception as e:
            health["status"] = "degraded"
            health["api_status"] = f"error: {str(e)}"

        return health

# Global instance for application-wide use
try:
    gpt5_service = GPT5Service()
    logger.info("GPT-5 service initialized")
except Exception as e:
    logger.error(f"Failed to initialize GPT-5 service: {e}")
    gpt5_service = None

def get_gpt5_service() -> GPT5Service:
    """Get or create the GPT-5 service instance"""
    global gpt5_service
    if gpt5_service is None:
        gpt5_service = GPT5Service()
    return gpt5_service
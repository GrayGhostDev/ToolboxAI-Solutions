"""
Cached AI Service - Integration of AI models with semantic caching

This service wraps AI model calls with semantic caching to reduce API costs
and improve response times.
"""

import logging
from datetime import datetime
from typing import Any

from apps.backend.core.config import settings
from apps.backend.services.semantic_cache import semantic_cache

logger = logging.getLogger(__name__)


class CachedAIService:
    """
    Service that integrates AI models with semantic caching.

    This provides a unified interface for AI calls with automatic caching,
    fallback handling, and cost optimization.
    """

    def __init__(self):
        self.cache = semantic_cache
        self.total_api_calls = 0
        self.cached_responses = 0

    async def generate_completion(
        self,
        prompt: str,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 500,
        use_cache: bool = True,
        cache_ttl: int | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Generate AI completion with semantic caching.

        Args:
            prompt: The input prompt
            model: Model to use
            temperature: Temperature setting
            max_tokens: Maximum tokens to generate
            use_cache: Whether to use caching
            cache_ttl: Optional cache TTL in seconds
            **kwargs: Additional model-specific parameters

        Returns:
            Response dictionary with completion and metadata
        """
        start_time = datetime.utcnow()

        # Check cache first if enabled
        if use_cache:
            cached_response = await self.cache.get(prompt, model, temperature)
            if cached_response:
                self.cached_responses += 1
                logger.info(
                    f"Cache hit for model {model} (similarity: {cached_response.get('similarity', 1.0)})"
                )

                return {
                    "completion": cached_response["response"],
                    "model": model,
                    "cached": True,
                    "cache_similarity": cached_response.get("similarity", 1.0),
                    "processing_time": (datetime.utcnow() - start_time).total_seconds(),
                    "tokens_used": 0,  # No tokens used for cached response
                    "cost": 0.0,
                }

        # Generate new completion
        self.total_api_calls += 1

        try:
            # Import the appropriate client based on model
            if model.startswith("gpt"):
                response = await self._call_openai(prompt, model, temperature, max_tokens, **kwargs)
            elif model.startswith("claude"):
                response = await self._call_anthropic(
                    prompt, model, temperature, max_tokens, **kwargs
                )
            else:
                response = await self._call_langchain(
                    prompt, model, temperature, max_tokens, **kwargs
                )

            # Cache the response if caching is enabled
            if use_cache and response.get("completion"):
                cache_metadata = {
                    "tokens_used": response.get("tokens_used", 0),
                    "cost": response.get("cost", 0.0),
                    "processing_time": response.get("processing_time", 0),
                }

                await self.cache.set(
                    prompt=prompt,
                    response=response["completion"],
                    model=model,
                    temperature=temperature,
                    metadata=cache_metadata,
                )

            response["cached"] = False
            response["processing_time"] = (datetime.utcnow() - start_time).total_seconds()

            return response

        except Exception as e:
            logger.error(f"Error generating completion: {e}")
            raise

    async def _call_openai(
        self, prompt: str, model: str, temperature: float, max_tokens: int, **kwargs
    ) -> dict[str, Any]:
        """Call OpenAI API."""
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            completion_text = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0

            # Calculate approximate cost
            cost = self._calculate_openai_cost(model, tokens_used)

            return {
                "completion": completion_text,
                "model": model,
                "tokens_used": tokens_used,
                "cost": cost,
            }

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    async def _call_anthropic(
        self, prompt: str, model: str, temperature: float, max_tokens: int, **kwargs
    ) -> dict[str, Any]:
        """Call Anthropic API."""
        try:
            import anthropic

            client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

            response = await client.messages.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            completion_text = response.content[0].text if response.content else ""
            tokens_used = (
                response.usage.input_tokens + response.usage.output_tokens if response.usage else 0
            )

            # Calculate approximate cost
            cost = self._calculate_anthropic_cost(model, tokens_used)

            return {
                "completion": completion_text,
                "model": model,
                "tokens_used": tokens_used,
                "cost": cost,
            }

        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise

    async def _call_langchain(
        self, prompt: str, model: str, temperature: float, max_tokens: int, **kwargs
    ) -> dict[str, Any]:
        """Call through LangChain for advanced features."""
        try:
            from langchain_core.messages import HumanMessage
            from langchain_openai import ChatOpenAI

            # Create LangChain model
            llm = ChatOpenAI(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=settings.OPENAI_API_KEY,
            )

            # Generate response
            response = await llm.ainvoke([HumanMessage(content=prompt)])

            completion_text = response.content
            # LangChain doesn't always provide token counts
            tokens_used = len(prompt.split()) + len(completion_text.split())  # Rough estimate

            return {
                "completion": completion_text,
                "model": model,
                "tokens_used": tokens_used,
                "cost": self._calculate_openai_cost(model, tokens_used),
            }

        except Exception as e:
            logger.error(f"LangChain error: {e}")
            raise

    def _calculate_openai_cost(self, model: str, tokens: int) -> float:
        """Calculate approximate cost for OpenAI models."""
        # Prices per 1K tokens (as of 2025)
        pricing = {
            "gpt-4": 0.03,
            "gpt-4-turbo": 0.01,
            "gpt-4-turbo-preview": 0.01,
            "gpt-3.5-turbo": 0.002,
            "gpt-3.5-turbo-16k": 0.003,
        }

        price_per_1k = pricing.get(model, 0.002)
        return (tokens / 1000) * price_per_1k

    def _calculate_anthropic_cost(self, model: str, tokens: int) -> float:
        """Calculate approximate cost for Anthropic models."""
        # Prices per 1K tokens (as of 2025)
        pricing = {
            "claude-3-opus": 0.015,
            "claude-3-sonnet": 0.003,
            "claude-3-haiku": 0.00025,
            "claude-2.1": 0.008,
            "claude-2": 0.008,
        }

        price_per_1k = pricing.get(model, 0.008)
        return (tokens / 1000) * price_per_1k

    async def batch_generate(
        self,
        prompts: list[str],
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        use_cache: bool = True,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """
        Generate completions for multiple prompts with caching.

        Args:
            prompts: List of prompts
            model: Model to use
            temperature: Temperature setting
            use_cache: Whether to use caching
            **kwargs: Additional parameters

        Returns:
            List of response dictionaries
        """
        responses = []

        for prompt in prompts:
            try:
                response = await self.generate_completion(
                    prompt=prompt,
                    model=model,
                    temperature=temperature,
                    use_cache=use_cache,
                    **kwargs,
                )
                responses.append(response)
            except Exception as e:
                logger.error(f"Error processing prompt: {e}")
                responses.append(
                    {"completion": None, "error": str(e), "model": model, "cached": False}
                )

        return responses

    async def get_embedding(
        self, text: str, model: str = "text-embedding-ada-002", use_cache: bool = True
    ) -> list[float] | None:
        """
        Get embedding for text with caching.

        Args:
            text: Text to embed
            model: Embedding model to use
            use_cache: Whether to use caching

        Returns:
            Embedding vector or None if failed
        """
        # Check cache first
        if use_cache:
            cached = await self.cache.get(f"embedding:{text}", model, 0.0)
            if cached:
                import json

                return json.loads(cached["response"])

        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.embeddings.create(input=text, model=model)

            embedding = response.data[0].embedding

            # Cache the embedding
            if use_cache:
                import json

                await self.cache.set(
                    prompt=f"embedding:{text}",
                    response=json.dumps(embedding),
                    model=model,
                    temperature=0.0,
                )

            return embedding

        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return None

    def get_statistics(self) -> dict[str, Any]:
        """Get service statistics."""
        cache_stats = self.cache.get_statistics()

        return {
            "total_api_calls": self.total_api_calls,
            "cached_responses": self.cached_responses,
            "cache_hit_rate": self.cached_responses
            / max(self.total_api_calls + self.cached_responses, 1),
            "estimated_cost_saved": cache_stats["total_cost_saved"],
            "cache_statistics": cache_stats,
        }

    async def clear_cache(self, model: str | None = None):
        """Clear the semantic cache."""
        return await self.cache.clear_cache(model)

    async def warm_cache_from_history(self, history: list[dict[str, Any]]):
        """
        Warm cache from conversation history.

        Args:
            history: List of conversation entries with 'prompt', 'response', and optional 'model'
        """
        entries = [
            (entry["prompt"], entry["response"], entry.get("model"))
            for entry in history
            if "prompt" in entry and "response" in entry
        ]

        return await self.cache.warm_cache(entries)


# Singleton instance
_cached_ai_service = None


def get_cached_ai_service() -> CachedAIService:
    """Get singleton instance of the cached AI service."""
    global _cached_ai_service
    if _cached_ai_service is None:
        _cached_ai_service = CachedAIService()
    return _cached_ai_service


# Export for convenience
cached_ai = get_cached_ai_service()

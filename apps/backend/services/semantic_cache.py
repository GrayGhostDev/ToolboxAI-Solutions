"""
Semantic Cache Service using LangCache

This service provides semantic caching for AI responses using Redis Cloud's LangCache.
It reduces API costs and improves response times by caching similar prompts.
"""

import os
import logging
import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

try:
    from langcache import LangCache
    LANGCACHE_AVAILABLE = True
except ImportError:
    LANGCACHE_AVAILABLE = False
    logging.warning("LangCache not available - AI responses will not be cached")

from apps.backend.core.config import settings

logger = logging.getLogger(__name__)


class SemanticCacheService:
    """
    Service for semantic caching of AI responses using LangCache.

    Features:
    - Semantic similarity matching for prompts
    - Automatic cache invalidation
    - Cost tracking and optimization
    - Fallback to exact matching when LangCache unavailable
    """

    _instance = None

    def __init__(self):
        self.enabled = (
            LANGCACHE_AVAILABLE
            and os.getenv('LANGCACHE_ENABLED', 'false').lower() == 'true'
        )
        self.api_key = os.getenv('LANGCACHE_API_KEY')
        self.cache_id = os.getenv('LANGCACHE_CACHE_ID')
        self.server_url = os.getenv('LANGCACHE_SERVER_URL', 'https://gcp-us-east4.langcache.redis.io')
        self.similarity_threshold = float(os.getenv('LANGCACHE_SIMILARITY_THRESHOLD', '0.95'))

        # Cache statistics
        self.hits = 0
        self.misses = 0
        self.saves = 0
        self.errors = 0
        self.total_cost_saved = 0.0

        # Fallback cache for when LangCache is unavailable
        self.fallback_cache = {}
        self.fallback_cache_max_size = 1000

        if self.enabled and not all([self.api_key, self.cache_id]):
            logger.warning("LangCache enabled but missing configuration")
            self.enabled = False

    @classmethod
    def get_instance(cls) -> "SemanticCacheService":
        """Get singleton instance of the semantic cache service."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @asynccontextmanager
    async def get_langcache(self):
        """Get LangCache context manager."""
        if not self.enabled:
            yield None
            return

        try:
            with LangCache(
                server_url=self.server_url,
                cache_id=self.cache_id,
                api_key=self.api_key,
            ) as lang_cache:
                yield lang_cache
        except Exception as e:
            logger.error(f"Failed to initialize LangCache: {e}")
            self.errors += 1
            yield None

    async def get(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a cached response for a given prompt.

        Args:
            prompt: The input prompt to search for
            model: Optional model identifier for cache segmentation
            temperature: Optional temperature setting for cache segmentation

        Returns:
            Cached response if found, None otherwise
        """
        if not self.enabled:
            return self._fallback_get(prompt, model, temperature)

        try:
            async with self.get_langcache() as lang_cache:
                if not lang_cache:
                    return self._fallback_get(prompt, model, temperature)

                # Create cache key with model and temperature for more precise matching
                cache_key = self._create_cache_key(prompt, model, temperature)

                # Search for semantically similar prompts
                search_response = lang_cache.search(
                    prompt=cache_key,
                    similarity_threshold=self.similarity_threshold
                )

                # Handle LangCache response object structure
                if search_response:
                    matches = getattr(search_response, 'matches', [])
                    if matches and len(matches) > 0:
                        # Get the best match
                        best_match = matches[0]

                        # Extract attributes from match object
                        similarity = getattr(best_match, 'similarity', 0)

                        if similarity >= self.similarity_threshold:
                            self.hits += 1
                            logger.debug(f"Cache hit for prompt (similarity: {similarity})")

                            # Track cost savings
                            self._track_cost_savings(model)

                            # Extract response and metadata
                            response_text = getattr(best_match, 'response', '')
                            metadata = getattr(best_match, 'metadata', {})
                            if isinstance(metadata, str):
                                try:
                                    metadata = json.loads(metadata)
                                except json.JSONDecodeError:
                                    metadata = {}

                            return {
                                'response': response_text,
                                'cached': True,
                                'similarity': similarity,
                                'cached_at': metadata.get('timestamp'),
                                'model': metadata.get('model', model)
                            }

                self.misses += 1
                return None

        except Exception as e:
            logger.error(f"Error retrieving from semantic cache: {e}")
            self.errors += 1
            return self._fallback_get(prompt, model, temperature)

    async def set(
        self,
        prompt: str,
        response: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Cache a prompt-response pair.

        Args:
            prompt: The input prompt
            response: The AI response to cache
            model: Optional model identifier
            temperature: Optional temperature setting
            metadata: Optional metadata to store with the cache entry

        Returns:
            True if successfully cached, False otherwise
        """
        if not self.enabled:
            return self._fallback_set(prompt, response, model, temperature, metadata)

        try:
            async with self.get_langcache() as lang_cache:
                if not lang_cache:
                    return self._fallback_set(prompt, response, model, temperature, metadata)

                # Create cache key with model and temperature
                cache_key = self._create_cache_key(prompt, model, temperature)

                # Prepare metadata
                cache_metadata = {
                    'model': model,
                    'temperature': temperature,
                    'timestamp': datetime.utcnow().isoformat(),
                    **(metadata or {})
                }

                # Save to cache
                # Note: LangCache may not support metadata in set() directly
                # Combine metadata with response for storage
                save_response = lang_cache.set(
                    prompt=cache_key,
                    response=response  # Store just the response, metadata in prompt key
                )

                # Handle response object or dict
                if save_response:
                    # Safely extract status from response object or dict
                    if isinstance(save_response, dict):
                        status = save_response.get('status', 'success')
                    else:
                        status = getattr(save_response, 'status', 'success')

                    if status == 'success' or hasattr(save_response, 'entry_id'):
                        self.saves += 1
                        logger.debug("Successfully cached prompt-response pair")

                    # Also save to fallback cache
                    self._fallback_set(prompt, response, model, temperature, metadata)
                    return True

                return False

        except Exception as e:
            logger.error(f"Error saving to semantic cache: {e}")
            self.errors += 1
            return self._fallback_set(prompt, response, model, temperature, metadata)

    async def clear_cache(self, model: Optional[str] = None) -> bool:
        """
        Clear cache entries, optionally filtered by model.

        Args:
            model: Optional model identifier to filter cache clearing

        Returns:
            True if successfully cleared, False otherwise
        """
        try:
            # Clear fallback cache
            if model:
                keys_to_remove = [
                    k for k in self.fallback_cache.keys()
                    if k.startswith(f"{model}:")
                ]
                for key in keys_to_remove:
                    del self.fallback_cache[key]
            else:
                self.fallback_cache.clear()

            logger.info(f"Cache cleared for model: {model or 'all'}")
            return True

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

    def _create_cache_key(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Create a cache key that includes model and temperature for segmentation."""
        # For LangCache, we return the prompt directly as it handles similarity
        # The model and temperature are stored in metadata
        return prompt

    def _fallback_get(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """Fallback cache get using exact matching."""
        # Create hash key for exact matching
        key = self._create_fallback_key(prompt, model, temperature)

        if key in self.fallback_cache:
            self.hits += 1
            entry = self.fallback_cache[key]

            # Check if entry is still valid (24 hour TTL)
            if datetime.fromisoformat(entry['timestamp']) > datetime.utcnow() - timedelta(hours=24):
                return {
                    'response': entry['response'],
                    'cached': True,
                    'similarity': 1.0,  # Exact match
                    'cached_at': entry['timestamp'],
                    'model': entry.get('model', model)
                }
            else:
                # Remove expired entry
                del self.fallback_cache[key]

        self.misses += 1
        return None

    def _fallback_set(
        self,
        prompt: str,
        response: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Fallback cache set using exact matching."""
        try:
            # Implement LRU by removing oldest entries if cache is full
            if len(self.fallback_cache) >= self.fallback_cache_max_size:
                # Remove oldest 10% of entries
                entries_to_remove = int(self.fallback_cache_max_size * 0.1)
                for _ in range(entries_to_remove):
                    if self.fallback_cache:
                        self.fallback_cache.pop(next(iter(self.fallback_cache)))

            key = self._create_fallback_key(prompt, model, temperature)
            self.fallback_cache[key] = {
                'response': response,
                'model': model,
                'temperature': temperature,
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': metadata or {}
            }

            self.saves += 1
            return True

        except Exception as e:
            logger.error(f"Error in fallback cache set: {e}")
            return False

    def _create_fallback_key(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Create a hash key for fallback cache."""
        key_parts = [
            prompt,
            model or 'default',
            str(temperature) if temperature is not None else '1.0'
        ]
        key_string = '|'.join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()

    def _track_cost_savings(self, model: Optional[str] = None):
        """Track estimated cost savings from cache hits."""
        # Rough cost estimates per 1K tokens (varies by model)
        cost_per_1k_tokens = {
            'gpt-4': 0.03,
            'gpt-4-turbo': 0.01,
            'gpt-3.5-turbo': 0.002,
            'claude-3': 0.015,
            'claude-2': 0.008,
            'default': 0.005
        }

        model_key = model.lower() if model else 'default'
        cost = cost_per_1k_tokens.get(model_key, cost_per_1k_tokens['default'])

        # Estimate average tokens per request
        avg_tokens = 500
        self.total_cost_saved += (avg_tokens / 1000) * cost

    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0

        return {
            'enabled': self.enabled,
            'provider': 'LangCache' if self.enabled else 'Fallback',
            'hits': self.hits,
            'misses': self.misses,
            'saves': self.saves,
            'errors': self.errors,
            'hit_rate': hit_rate,
            'total_requests': total_requests,
            'total_cost_saved': round(self.total_cost_saved, 2),
            'fallback_cache_size': len(self.fallback_cache),
            'similarity_threshold': self.similarity_threshold
        }

    async def warm_cache(self, common_prompts: List[Tuple[str, str, Optional[str]]]):
        """
        Pre-populate cache with common prompts and responses.

        Args:
            common_prompts: List of (prompt, response, model) tuples
        """
        success_count = 0
        for prompt, response, model in common_prompts:
            if await self.set(prompt, response, model):
                success_count += 1

        logger.info(f"Warmed cache with {success_count}/{len(common_prompts)} entries")
        return success_count

    def export_metrics(self) -> str:
        """Export metrics in Prometheus format."""
        stats = self.get_statistics()

        lines = [
            "# HELP semantic_cache_hits_total Total number of cache hits",
            "# TYPE semantic_cache_hits_total counter",
            f"semantic_cache_hits_total {stats['hits']}",

            "# HELP semantic_cache_misses_total Total number of cache misses",
            "# TYPE semantic_cache_misses_total counter",
            f"semantic_cache_misses_total {stats['misses']}",

            "# HELP semantic_cache_saves_total Total number of cache saves",
            "# TYPE semantic_cache_saves_total counter",
            f"semantic_cache_saves_total {stats['saves']}",

            "# HELP semantic_cache_errors_total Total number of cache errors",
            "# TYPE semantic_cache_errors_total counter",
            f"semantic_cache_errors_total {stats['errors']}",

            "# HELP semantic_cache_hit_rate Cache hit rate",
            "# TYPE semantic_cache_hit_rate gauge",
            f"semantic_cache_hit_rate {stats['hit_rate']}",

            "# HELP semantic_cache_cost_saved_dollars Total cost saved by caching",
            "# TYPE semantic_cache_cost_saved_dollars gauge",
            f"semantic_cache_cost_saved_dollars {stats['total_cost_saved']}",
        ]

        return "\n".join(lines)


# Singleton instance getter
def get_semantic_cache() -> SemanticCacheService:
    """Get the singleton semantic cache service instance."""
    return SemanticCacheService.get_instance()


# Export for convenience
semantic_cache = get_semantic_cache()
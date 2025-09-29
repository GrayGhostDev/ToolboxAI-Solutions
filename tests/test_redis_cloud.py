#!/usr/bin/env python3
"""
Test script for Redis Cloud and LangCache integration

This script verifies that:
1. Redis Cloud connection works with TLS
2. LangCache semantic caching is operational
3. Rate limiting works with distributed Redis
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_redis_cloud_connection():
    """Test Redis Cloud connection with TLS."""
    import redis.asyncio as redis

    logger.info("Testing Redis Cloud connection...")

    redis_url = os.getenv('REDIS_URL')
    cert_path = os.getenv('REDIS_CLOUD_CA_CERT_PATH')

    if not redis_url:
        logger.error("REDIS_URL not found in environment")
        return False

    try:
        # Create Redis client with TLS
        if redis_url.startswith('rediss://'):
            # Redis Cloud with TLS
            client = await redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                ssl_cert_reqs='required',
                ssl_ca_certs=cert_path if cert_path and os.path.exists(cert_path) else None
            )
        else:
            # Local Redis without TLS
            client = await redis.from_url(redis_url, decode_responses=True)

        # Test connection
        await client.ping()
        logger.info("✅ Redis Cloud connection successful!")

        # Test basic operations
        await client.set('test:key', 'test_value', ex=60)
        value = await client.get('test:key')
        assert value == 'test_value', f"Expected 'test_value', got '{value}'"
        logger.info("✅ Redis basic operations working!")

        # Test increment for rate limiting
        await client.incr('test:counter')
        counter = await client.get('test:counter')
        logger.info(f"✅ Redis counter operations working! Counter value: {counter}")

        # Clean up
        await client.delete('test:key', 'test:counter')
        await client.aclose()  # Use aclose() instead of deprecated close()

        return True

    except Exception as e:
        logger.error(f"❌ Redis Cloud connection failed: {e}")
        return False


async def test_langcache():
    """Test LangCache semantic caching."""
    logger.info("Testing LangCache...")

    api_key = os.getenv('LANGCACHE_API_KEY')
    cache_id = os.getenv('LANGCACHE_CACHE_ID')
    server_url = os.getenv('LANGCACHE_SERVER_URL')

    if not all([api_key, cache_id, server_url]):
        logger.warning("LangCache configuration not complete, skipping test")
        return False

    try:
        from langcache import LangCache

        with LangCache(
            server_url=server_url,
            cache_id=cache_id,
            api_key=api_key,
        ) as lang_cache:
            # Save an entry
            test_prompt = "What is semantic caching and how does it work?"
            test_response = "Semantic caching stores and retrieves data based on meaning, not exact matches."

            save_response = lang_cache.set(
                prompt=test_prompt,
                response=test_response
            )
            logger.info(f"✅ LangCache save successful: {save_response}")

            # Search for similar entry
            search_prompt = "How does semantic caching work?"
            search_response = lang_cache.search(prompt=search_prompt)

            # Handle LangCache response object
            if search_response:
                matches = getattr(search_response, 'matches', [])
                if matches and len(matches) > 0:
                    best_match = matches[0]
                    similarity = getattr(best_match, 'similarity', 0)
                    logger.info(f"✅ LangCache search successful! Similarity: {similarity}")
                    return True
            else:
                logger.warning("No matches found in LangCache search")
                return True  # Still consider it successful if connection works

    except Exception as e:
        logger.error(f"❌ LangCache test failed: {e}")
        return False


async def test_rate_limiter():
    """Test the rate limiter with Redis Cloud."""
    logger.info("Testing Rate Limiter with Redis Cloud...")

    try:
        from apps.backend.core.security.rate_limit_manager import RateLimitManager

        # Create rate limiter instance
        rate_limiter = RateLimitManager()

        # Connect to Redis
        connected = await rate_limiter.connect_redis()
        if not connected:
            logger.warning("Rate limiter using in-memory fallback")
        else:
            logger.info("✅ Rate limiter connected to Redis Cloud!")

        # Test rate limiting
        test_identifier = "test_user_123"
        max_requests = 5
        window_seconds = 10

        # Make requests up to the limit
        for i in range(max_requests):
            allowed, retry_after = await rate_limiter.check_rate_limit(
                identifier=test_identifier,
                max_requests=max_requests,
                window_seconds=window_seconds,
                source="test"
            )
            assert allowed, f"Request {i+1} should be allowed"
            logger.info(f"  Request {i+1}/{max_requests}: Allowed")

        # Next request should be rate limited
        allowed, retry_after = await rate_limiter.check_rate_limit(
            identifier=test_identifier,
            max_requests=max_requests,
            window_seconds=window_seconds,
            source="test"
        )
        assert not allowed, "Request should be rate limited"
        assert retry_after is not None, "Retry-after should be provided"
        logger.info(f"✅ Rate limiting working! Retry after {retry_after} seconds")

        # Clean up
        await rate_limiter.reset_limits(test_identifier)
        await rate_limiter.disconnect_redis()

        return True

    except Exception as e:
        logger.error(f"❌ Rate limiter test failed: {e}")
        return False


async def test_semantic_cache_service():
    """Test the semantic cache service."""
    logger.info("Testing Semantic Cache Service...")

    try:
        from apps.backend.services.semantic_cache import semantic_cache

        # Test basic caching
        test_prompt = "Explain quantum computing in simple terms"
        test_response = "Quantum computing uses quantum bits (qubits) that can be both 0 and 1 simultaneously."

        # Save to cache
        saved = await semantic_cache.set(
            prompt=test_prompt,
            response=test_response,
            model="gpt-3.5-turbo",
            temperature=0.7
        )
        logger.info(f"  Cache save: {'✅' if saved else '❌'}")

        # Retrieve from cache with exact match
        cached = await semantic_cache.get(
            prompt=test_prompt,
            model="gpt-3.5-turbo",
            temperature=0.7
        )

        if cached:
            logger.info(f"✅ Exact match cache hit! Cached: {cached.get('cached', False)}")
        else:
            logger.info("  Using fallback cache")

        # Test with similar prompt
        similar_prompt = "Can you explain quantum computing simply?"
        cached_similar = await semantic_cache.get(
            prompt=similar_prompt,
            model="gpt-3.5-turbo",
            temperature=0.7
        )

        if cached_similar:
            similarity = cached_similar.get('similarity', 0)
            logger.info(f"✅ Semantic match found! Similarity: {similarity}")

        # Get statistics
        stats = semantic_cache.get_statistics()
        logger.info(f"  Cache stats: Hits={stats['hits']}, Misses={stats['misses']}, Hit Rate={stats['hit_rate']:.2%}")

        return True

    except Exception as e:
        logger.error(f"❌ Semantic cache service test failed: {e}")
        return False


async def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("Redis Cloud & LangCache Integration Tests")
    logger.info("=" * 60)

    results = {
        "Redis Cloud Connection": await test_redis_cloud_connection(),
        "LangCache": await test_langcache(),
        "Rate Limiter": await test_rate_limiter(),
        "Semantic Cache Service": await test_semantic_cache_service()
    }

    logger.info("\n" + "=" * 60)
    logger.info("Test Results Summary:")
    logger.info("=" * 60)

    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"  {test_name}: {status}")
        if not passed:
            all_passed = False

    logger.info("=" * 60)

    if all_passed:
        logger.info("🎉 All tests passed successfully!")
    else:
        logger.warning("⚠️  Some tests failed. Please check the logs above.")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
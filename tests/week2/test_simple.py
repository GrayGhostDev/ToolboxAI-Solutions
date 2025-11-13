#!/usr/bin/env python
"""
Simple, direct tests for Week 2 services without complex imports.
"""

import asyncio
import json
import os
import sys
from unittest.mock import AsyncMock, Mock, patch

# Set environment to prevent external connections
os.environ["TESTING"] = "true"
os.environ["REDIS_CLOUD_ENABLED"] = "false"
os.environ["LANGCACHE_ENABLED"] = "false"
os.environ["SKIP_STARTUP"] = "true"
os.environ["SKIP_LIFESPAN"] = "true"

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_week2_services():
    """Test Week 2 services with complete mocking."""

    print("=" * 60)
    print("🧪 Week 2 Services Direct Test")
    print("=" * 60)

    results = {}

    # Test 1: Rate Limit Manager
    print("\n1. Testing Rate Limit Manager...")
    try:
        with patch("redis.asyncio.from_url") as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            mock_client.get = AsyncMock(return_value=None)
            mock_client.setex = AsyncMock(return_value=True)
            mock_client.incr = AsyncMock(return_value=1)
            mock_client.expire = AsyncMock(return_value=True)
            mock_client.aclose = AsyncMock()

            # Now import after mocking
            from apps.backend.core.security.rate_limit_manager import RateLimitManager

            manager = RateLimitManager()

            # Test check_rate_limit
            async def test_rate_limit():
                result = await manager.check_rate_limit("test_key", 100, 60)
                return result

            loop = asyncio.new_event_loop()
            allowed, remaining, reset = loop.run_until_complete(test_rate_limit())
            loop.close()

            assert allowed == True
            assert remaining >= 0
            results["RateLimitManager"] = "✅ PASS"
            print("   ✅ Rate limit check passed")

    except Exception as e:
        results["RateLimitManager"] = f"❌ FAIL: {e}"
        print(f"   ❌ Failed: {e}")

    # Test 2: Semantic Cache Service
    print("\n2. Testing Semantic Cache Service...")
    try:
        with patch("redis.asyncio.from_url") as mock_redis, patch("requests.post") as mock_post:

            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            mock_client.get = AsyncMock(return_value=None)
            mock_client.set = AsyncMock(return_value=True)
            mock_client.aclose = AsyncMock()

            # Mock LangCache API
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "stored"}
            mock_post.return_value = mock_response

            from apps.backend.services.semantic_cache import SemanticCacheService

            service = SemanticCacheService()

            # Test store_response
            async def test_store():
                await service.store_response(prompt="test", response="response", metadata={})

            loop = asyncio.new_event_loop()
            loop.run_until_complete(test_store())
            loop.close()

            results["SemanticCacheService"] = "✅ PASS"
            print("   ✅ Semantic cache store passed")

    except Exception as e:
        results["SemanticCacheService"] = f"❌ FAIL: {e}"
        print(f"   ❌ Failed: {e}")

    # Test 3: Cached AI Service
    print("\n3. Testing Cached AI Service...")
    try:
        with (
            patch("apps.backend.services.semantic_cache.SemanticCacheService") as mock_cache_class,
            patch("openai.AsyncOpenAI") as mock_openai,
        ):

            mock_cache = AsyncMock()
            mock_cache_class.return_value = mock_cache
            mock_cache.search_similar = AsyncMock(
                return_value={"response": "cached", "similarity": 0.95}
            )

            mock_client = AsyncMock()
            mock_openai.return_value = mock_client

            from apps.backend.services.cached_ai_service import CachedAIService

            service = CachedAIService()

            # Test get_completion with cache hit
            async def test_completion():
                result = await service.get_completion("test prompt")
                return result

            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(test_completion())
            loop.close()

            assert result is not None
            results["CachedAIService"] = "✅ PASS"
            print("   ✅ Cached AI completion passed")

    except Exception as e:
        results["CachedAIService"] = f"❌ FAIL: {e}"
        print(f"   ❌ Failed: {e}")

    # Test 4: API Key Manager
    print("\n4. Testing API Key Manager...")
    try:
        with patch("redis.asyncio.from_url") as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            mock_client.hset = AsyncMock(return_value=True)
            mock_client.hget = AsyncMock(
                return_value=json.dumps(
                    {"user_id": "test", "scopes": ["read"], "active": True}
                ).encode()
            )
            mock_client.setex = AsyncMock(return_value=True)
            mock_client.aclose = AsyncMock()

            from apps.backend.services.api_key_manager import APIKeyManager

            manager = APIKeyManager()

            # Test generate_api_key
            async def test_generate():
                key = await manager.generate_api_key("user123", ["read"])
                return key

            loop = asyncio.new_event_loop()
            api_key = loop.run_until_complete(test_generate())
            loop.close()

            assert api_key is not None
            assert len(api_key) > 0
            results["APIKeyManager"] = "✅ PASS"
            print(f"   ✅ API key generated: {api_key[:10]}...")

    except Exception as e:
        results["APIKeyManager"] = f"❌ FAIL: {e}"
        print(f"   ❌ Failed: {e}")

    # Test 5: Supabase Migration Manager
    print("\n5. Testing Supabase Migration Manager...")
    try:
        with patch("supabase.create_client") as mock_create:
            mock_client = Mock()
            mock_create.return_value = mock_client
            mock_client.rpc = Mock(return_value=Mock(execute=Mock(return_value=Mock(data=[]))))
            mock_client.table = Mock(
                return_value=Mock(
                    select=Mock(
                        return_value=Mock(
                            eq=Mock(
                                return_value=Mock(
                                    order=Mock(
                                        return_value=Mock(execute=Mock(return_value=Mock(data=[])))
                                    )
                                )
                            )
                        )
                    )
                )
            )

            from apps.backend.services.supabase_migration_manager import (
                SupabaseMigrationManager,
            )

            manager = SupabaseMigrationManager()
            migrations = manager.load_migrations_from_files()

            # Test get_status
            async def test_status():
                return await manager.get_status()

            loop = asyncio.new_event_loop()
            status = loop.run_until_complete(test_status())
            loop.close()

            assert status is not None
            results["SupabaseMigrationManager"] = "✅ PASS"
            print("   ✅ Migration manager status passed")

    except Exception as e:
        results["SupabaseMigrationManager"] = f"❌ FAIL: {e}"
        print(f"   ❌ Failed: {e}")

    # Test 6: Roblox Deployment Service
    print("\n6. Testing Roblox Deployment Service...")
    try:
        with (
            patch("redis.asyncio.from_url") as mock_redis,
            patch("aiofiles.open") as mock_aiofiles,
            patch("os.walk") as mock_walk,
            patch("builtins.open", create=True) as mock_open,
        ):

            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            mock_client.hset = AsyncMock(return_value=True)
            mock_client.aclose = AsyncMock()

            # Mock file operations
            mock_file = AsyncMock()
            mock_file.__aenter__ = AsyncMock(return_value=mock_file)
            mock_file.__aexit__ = AsyncMock()
            mock_file.write = AsyncMock()
            mock_aiofiles.return_value = mock_file

            mock_walk.return_value = [("/roblox", [], ["script.lua"])]

            mock_open.return_value.__enter__.return_value.read.return_value = 'print("test")'

            from apps.backend.services.roblox.deployment import RobloxDeploymentService

            service = RobloxDeploymentService()

            # Test bundle_assets
            async def test_bundle():
                bundle = await service.bundle_assets("/test")
                return bundle

            loop = asyncio.new_event_loop()
            bundle = loop.run_until_complete(test_bundle())
            loop.close()

            assert bundle is not None
            results["RobloxDeploymentService"] = "✅ PASS"
            print(f"   ✅ Roblox bundle created: {bundle.get('bundle_id', 'N/A')}")

    except Exception as e:
        results["RobloxDeploymentService"] = f"❌ FAIL: {e}"
        print(f"   ❌ Failed: {e}")

    # Test 7: Backup Disaster Recovery Service
    print("\n7. Testing Backup Disaster Recovery Service...")
    try:
        with (
            patch("supabase.create_client") as mock_supabase,
            patch("redis.asyncio.from_url") as mock_redis,
            patch("aiofiles.open") as mock_aiofiles,
        ):

            mock_supabase_client = Mock()
            mock_supabase.return_value = mock_supabase_client
            mock_supabase_client.table = Mock(
                return_value=Mock(
                    select=Mock(
                        return_value=Mock(
                            execute=Mock(return_value=Mock(data=[{"id": 1, "data": "test"}]))
                        )
                    )
                )
            )

            mock_redis_client = AsyncMock()
            mock_redis.return_value = mock_redis_client
            mock_redis_client.keys = AsyncMock(return_value=[])
            mock_redis_client.aclose = AsyncMock()

            mock_file = AsyncMock()
            mock_file.__aenter__ = AsyncMock(return_value=mock_file)
            mock_file.__aexit__ = AsyncMock()
            mock_file.write = AsyncMock()
            mock_aiofiles.return_value = mock_file

            from apps.backend.services.backup_disaster_recovery import (
                BackupDisasterRecoveryService,
            )

            service = BackupDisasterRecoveryService()

            # Test create_backup
            async def test_backup():
                backup_id = await service.create_backup()
                return backup_id

            loop = asyncio.new_event_loop()
            backup_id = loop.run_until_complete(test_backup())
            loop.close()

            assert backup_id is not None
            results["BackupDisasterRecoveryService"] = "✅ PASS"
            print(f"   ✅ Backup created: {backup_id}")

    except Exception as e:
        results["BackupDisasterRecoveryService"] = f"❌ FAIL: {e}"
        print(f"   ❌ Failed: {e}")

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = 0
    failed = 0

    for service, result in results.items():
        print(f"{service:35} {result}")
        if "✅ PASS" in result:
            passed += 1
        else:
            failed += 1

    print("=" * 60)
    print(f"Total: {passed}/{len(results)} passed")

    if failed > 0:
        print(f"⚠️  {failed} test(s) failed")
        return 1
    else:
        print("✅ All Week 2 services tested successfully!")
        return 0


if __name__ == "__main__":
    exit_code = test_week2_services()
    sys.exit(exit_code)

#!/usr/bin/env python
"""
Isolated Week 2 services test runner.
Tests each service independently with proper mocking.
"""

import sys
import os
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone

# Disable external services during import
os.environ['TESTING'] = 'true'
os.environ['REDIS_CLOUD_ENABLED'] = 'false'
os.environ['LANGCACHE_ENABLED'] = 'false'
os.environ['STRIPE_ENABLED'] = 'false'
os.environ['PUSHER_ENABLED'] = 'false'
os.environ['EMAIL_ENABLED'] = 'false'
os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
os.environ['SUPABASE_KEY'] = 'test-key'
os.environ['SUPABASE_SERVICE_KEY'] = 'test-service-key'
os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost/test'
os.environ['JWT_SECRET_KEY'] = 'test-secret-key-for-testing-only'

# Add project to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_rate_limit_manager():
    """Test RateLimitManager initialization and basic functionality."""
    print("\n" + "="*60)
    print("Testing RateLimitManager")
    print("="*60)

    try:
        # Mock Redis before import
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client

            from apps.backend.core.security.rate_limit_manager import RateLimitManager

            # Test initialization
            manager = RateLimitManager()
            assert manager is not None
            print("✅ RateLimitManager initialized")

            # Test configuration
            assert hasattr(manager, 'default_limit')
            assert hasattr(manager, 'default_window')
            print("✅ RateLimitManager has required attributes")

            # Test rate limit check (sync wrapper)
            async def test_check():
                result = await manager.check_rate_limit("test_key")
                return result

            # Mock Redis responses
            mock_client.get = AsyncMock(return_value=None)
            mock_client.setex = AsyncMock(return_value=True)
            mock_client.incr = AsyncMock(return_value=1)
            mock_client.expire = AsyncMock(return_value=True)

            # Run async test
            loop = asyncio.new_event_loop()
            allowed, remaining, reset_time = loop.run_until_complete(test_check())
            loop.close()

            assert allowed == True
            assert remaining >= 0
            print("✅ Rate limit check works")

            return True

    except Exception as e:
        print(f"❌ RateLimitManager test failed: {e}")
        return False


def test_semantic_cache():
    """Test SemanticCacheService initialization and basic functionality."""
    print("\n" + "="*60)
    print("Testing SemanticCacheService")
    print("="*60)

    try:
        # Mock dependencies before import
        with patch('redis.asyncio.from_url') as mock_redis, \
             patch('langcache.LangCacheAPI') as mock_langcache:

            mock_redis_client = AsyncMock()
            mock_redis.return_value = mock_redis_client

            mock_langcache_instance = Mock()
            mock_langcache.return_value = mock_langcache_instance

            from apps.backend.services.semantic_cache import SemanticCacheService

            # Test initialization
            service = SemanticCacheService()
            assert service is not None
            print("✅ SemanticCacheService initialized")

            # Test cache storage
            async def test_store():
                await service.store_response(
                    prompt="test prompt",
                    response="test response",
                    metadata={"model": "gpt-4"}
                )

            mock_langcache_instance.store = AsyncMock()

            loop = asyncio.new_event_loop()
            loop.run_until_complete(test_store())
            loop.close()

            print("✅ SemanticCacheService store_response works")

            # Test cache retrieval
            async def test_search():
                # Create mock response object with attributes
                mock_match = Mock()
                mock_match.response = "cached response"
                mock_match.similarity = 0.95
                mock_match.metadata = {"model": "gpt-4"}

                mock_search_response = Mock()
                mock_search_response.matches = [mock_match]

                mock_langcache_instance.search = AsyncMock(return_value=mock_search_response)

                result = await service.search_similar(
                    prompt="test prompt",
                    threshold=0.8
                )
                return result

            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(test_search())
            loop.close()

            assert result is not None
            print("✅ SemanticCacheService search_similar works")

            return True

    except Exception as e:
        print(f"❌ SemanticCacheService test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cached_ai_service():
    """Test CachedAIService initialization and basic functionality."""
    print("\n" + "="*60)
    print("Testing CachedAIService")
    print("="*60)

    try:
        # Mock all dependencies
        with patch('apps.backend.services.semantic_cache.SemanticCacheService') as mock_cache_class, \
             patch('openai.AsyncOpenAI') as mock_openai_class:

            mock_cache = AsyncMock()
            mock_cache_class.return_value = mock_cache

            mock_openai = AsyncMock()
            mock_openai_class.return_value = mock_openai

            from apps.backend.services.cached_ai_service import CachedAIService

            # Test initialization
            service = CachedAIService()
            assert service is not None
            print("✅ CachedAIService initialized")

            # Test cached response
            async def test_cached():
                mock_cache.search_similar = AsyncMock(return_value={
                    "response": "cached answer",
                    "similarity": 0.95,
                    "metadata": {"cached": True}
                })

                result = await service.get_completion(
                    prompt="What is Python?",
                    use_cache=True
                )
                return result

            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(test_cached())
            loop.close()

            assert result is not None
            assert "cached answer" in str(result)
            print("✅ CachedAIService cache hit works")

            # Test cache miss
            async def test_miss():
                mock_cache.search_similar = AsyncMock(return_value=None)

                # Mock OpenAI response
                mock_response = Mock()
                mock_response.choices = [Mock(message=Mock(content="new response"))]
                mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
                mock_cache.store_response = AsyncMock()

                result = await service.get_completion(
                    prompt="What is AI?",
                    use_cache=True
                )
                return result

            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(test_miss())
            loop.close()

            assert result is not None
            print("✅ CachedAIService cache miss works")

            return True

    except Exception as e:
        print(f"❌ CachedAIService test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_key_manager():
    """Test APIKeyManager initialization and basic functionality."""
    print("\n" + "="*60)
    print("Testing APIKeyManager")
    print("="*60)

    try:
        # Mock Redis
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client

            from apps.backend.services.api_key_manager import APIKeyManager

            # Test initialization
            manager = APIKeyManager()
            assert manager is not None
            print("✅ APIKeyManager initialized")

            # Test key generation
            async def test_generate():
                mock_client.hset = AsyncMock(return_value=True)
                mock_client.setex = AsyncMock(return_value=True)

                key = await manager.generate_api_key(
                    user_id="test_user",
                    scopes=["read", "write"]
                )
                return key

            loop = asyncio.new_event_loop()
            api_key = loop.run_until_complete(test_generate())
            loop.close()

            assert api_key is not None
            assert len(api_key) > 0
            print(f"✅ API key generated: {api_key[:10]}...")

            # Test key validation
            async def test_validate():
                mock_client.hget = AsyncMock(return_value='{"user_id": "test_user", "scopes": ["read"], "active": true}'.encode())

                is_valid = await manager.validate_api_key(api_key)
                return is_valid

            loop = asyncio.new_event_loop()
            is_valid = loop.run_until_complete(test_validate())
            loop.close()

            assert is_valid == True
            print("✅ API key validation works")

            return True

    except Exception as e:
        print(f"❌ APIKeyManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_supabase_migration_manager():
    """Test SupabaseMigrationManager initialization and basic functionality."""
    print("\n" + "="*60)
    print("Testing SupabaseMigrationManager")
    print("="*60)

    try:
        # Mock Supabase client
        with patch('supabase.create_client') as mock_create_client:
            mock_client = Mock()
            mock_create_client.return_value = mock_client

            # Mock RPC calls
            mock_client.rpc = Mock(return_value=Mock(execute=Mock(return_value=Mock(data=[]))))
            mock_client.table = Mock(return_value=Mock(
                select=Mock(return_value=Mock(
                    eq=Mock(return_value=Mock(
                        order=Mock(return_value=Mock(
                            execute=Mock(return_value=Mock(data=[]))
                        ))
                    ))
                ))
            ))

            from apps.backend.services.supabase_migration_manager import SupabaseMigrationManager, get_migration_manager

            # Test initialization
            manager = SupabaseMigrationManager()
            assert manager is not None
            print("✅ SupabaseMigrationManager initialized")

            # Test singleton pattern
            manager2 = get_migration_manager()
            assert manager2 is not None
            print("✅ Singleton pattern works")

            # Test loading migrations
            migrations = manager.load_migrations_from_files()
            assert migrations is not None
            print(f"✅ Loaded {len(migrations)} migrations")

            # Test migration status
            async def test_status():
                status = await manager.get_status()
                return status

            loop = asyncio.new_event_loop()
            status = loop.run_until_complete(test_status())
            loop.close()

            assert status is not None
            assert "pending_migrations" in status
            print("✅ Migration status check works")

            return True

    except Exception as e:
        print(f"❌ SupabaseMigrationManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_roblox_deployment():
    """Test RobloxDeploymentService initialization and basic functionality."""
    print("\n" + "="*60)
    print("Testing RobloxDeploymentService")
    print("="*60)

    try:
        # Mock dependencies
        with patch('redis.asyncio.from_url') as mock_redis, \
             patch('aiofiles.open') as mock_aiofiles:

            mock_client = AsyncMock()
            mock_redis.return_value = mock_client

            from apps.backend.services.roblox.deployment import RobloxDeploymentService

            # Test initialization
            service = RobloxDeploymentService()
            assert service is not None
            print("✅ RobloxDeploymentService initialized")

            # Test asset bundling
            async def test_bundle():
                # Mock file operations
                mock_file = AsyncMock()
                mock_file.__aenter__ = AsyncMock(return_value=mock_file)
                mock_file.__aexit__ = AsyncMock()
                mock_file.write = AsyncMock()
                mock_aiofiles.return_value = mock_file

                # Mock os.walk
                with patch('os.walk') as mock_walk:
                    mock_walk.return_value = [
                        ('/roblox', [], ['script1.lua', 'script2.lua'])
                    ]

                    with patch('builtins.open', mock_open(read_data='print("test")')):
                        bundle = await service.bundle_assets('/roblox')
                        return bundle

            from unittest.mock import mock_open
            loop = asyncio.new_event_loop()
            bundle = loop.run_until_complete(test_bundle())
            loop.close()

            assert bundle is not None
            assert "bundle_id" in bundle
            print(f"✅ Asset bundling works: {bundle['bundle_id']}")

            return True

    except Exception as e:
        print(f"❌ RobloxDeploymentService test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backup_disaster_recovery():
    """Test BackupDisasterRecoveryService initialization and basic functionality."""
    print("\n" + "="*60)
    print("Testing BackupDisasterRecoveryService")
    print("="*60)

    try:
        # Mock dependencies
        with patch('supabase.create_client') as mock_supabase, \
             patch('redis.asyncio.from_url') as mock_redis, \
             patch('aiofiles.open') as mock_aiofiles:

            mock_supabase_client = Mock()
            mock_supabase.return_value = mock_supabase_client

            mock_redis_client = AsyncMock()
            mock_redis.return_value = mock_redis_client

            from apps.backend.services.backup_disaster_recovery import BackupDisasterRecoveryService

            # Test initialization
            service = BackupDisasterRecoveryService()
            assert service is not None
            print("✅ BackupDisasterRecoveryService initialized")

            # Test backup creation
            async def test_backup():
                # Mock Supabase export
                mock_supabase_client.table = Mock(return_value=Mock(
                    select=Mock(return_value=Mock(
                        execute=Mock(return_value=Mock(data=[
                            {"id": 1, "name": "test"}
                        ]))
                    ))
                ))

                # Mock file operations
                mock_file = AsyncMock()
                mock_file.__aenter__ = AsyncMock(return_value=mock_file)
                mock_file.__aexit__ = AsyncMock()
                mock_file.write = AsyncMock()
                mock_aiofiles.return_value = mock_file

                backup_id = await service.create_backup()
                return backup_id

            loop = asyncio.new_event_loop()
            backup_id = loop.run_until_complete(test_backup())
            loop.close()

            assert backup_id is not None
            print(f"✅ Backup created: {backup_id}")

            # Test backup listing
            backups = service.list_backups()
            assert backups is not None
            print(f"✅ Listed {len(backups)} backups")

            return True

    except Exception as e:
        print(f"❌ BackupDisasterRecoveryService test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Week 2 service tests."""
    print("="*60)
    print("🧪 Week 2 Services Test Suite")
    print("="*60)

    results = {
        "RateLimitManager": test_rate_limit_manager(),
        "SemanticCacheService": test_semantic_cache(),
        "CachedAIService": test_cached_ai_service(),
        "APIKeyManager": test_api_key_manager(),
        "SupabaseMigrationManager": test_supabase_migration_manager(),
        "RobloxDeploymentService": test_roblox_deployment(),
        "BackupDisasterRecoveryService": test_backup_disaster_recovery()
    }

    # Print summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    passed = sum(1 for v in results.values() if v)
    failed = len(results) - passed

    for service, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{service:35} {status}")

    print("="*60)
    print(f"Total: {passed}/{len(results)} passed")

    if failed > 0:
        print(f"⚠️  {failed} test(s) failed")
        return 1
    else:
        print("✅ All tests passed!")
        return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
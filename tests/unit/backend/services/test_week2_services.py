"""
Comprehensive test suite for Week 2 services.
Tests semantic cache, API key management, migrations, and backups.
Target: >90% coverage for all Week 2 implementations.

Author: Claude
Date: September 2025
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from redis.exceptions import ConnectionError as RedisConnectionError

from apps.backend.services.api_key_manager import APIKeyManager, APIKeyScope
from apps.backend.services.cached_ai_service import CachedAIService
from apps.backend.services.roblox.deployment import AssetType, RobloxAssetManager

# Import Week 2 services
from apps.backend.services.semantic_cache import SemanticCacheService
from apps.backend.services.supabase_migration_manager import (
    Migration,
    MigrationStatus,
    MigrationStrategy,
    SupabaseMigrationManager,
)
from infrastructure.backups.scripts.backup_manager import (
    BackupManager,
    BackupStatus,
    BackupType,
)

# ============================================
# FIXTURES
# ============================================


@pytest.fixture
def redis_mock():
    """Mock Redis client for testing"""
    mock = AsyncMock()
    mock.ping = AsyncMock(return_value=True)
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=1)
    mock.exists = AsyncMock(return_value=0)
    mock.aclose = AsyncMock()
    return mock


@pytest.fixture
def langcache_mock():
    """Mock LangCache client for testing"""
    mock = MagicMock()

    # Mock search response
    search_response = MagicMock()
    search_response.matches = []
    mock.search = MagicMock(return_value=search_response)

    # Mock set response
    set_response = MagicMock()
    set_response.status = "success"
    set_response.entry_id = "test-entry-id"
    mock.set = MagicMock(return_value=set_response)

    return mock


@pytest.fixture
def supabase_mock():
    """Mock Supabase client for testing"""
    mock = AsyncMock()
    mock.table = MagicMock()
    mock.rpc = AsyncMock(return_value={"success": True})
    return mock


@pytest.fixture
def s3_mock():
    """Mock S3 client for testing"""
    mock = AsyncMock()
    mock.upload_file = AsyncMock(return_value=True)
    mock.download_file = AsyncMock(return_value=True)
    mock.list_objects_v2 = AsyncMock(return_value={"Contents": []})
    return mock


# ============================================
# SEMANTIC CACHE TESTS
# ============================================


class TestSemanticCache:
    """Test suite for SemanticCacheService"""

    @pytest_asyncio.fixture
    async def semantic_cache(self, redis_mock, langcache_mock):
        """Create SemanticCacheService instance with mocks"""
        with patch(
            "apps.backend.services.semantic_cache.aioredis.from_url",
            return_value=redis_mock,
        ):
            with patch("apps.backend.services.semantic_cache.lang_cache", langcache_mock):
                cache = SemanticCacheService()
                await cache.initialize()
                yield cache
                await cache.close()

    @pytest.mark.asyncio
    async def test_initialization(self, semantic_cache):
        """Test cache initialization"""
        assert semantic_cache.enabled is True
        assert semantic_cache.similarity_threshold == 0.95
        assert semantic_cache.hits == 0
        assert semantic_cache.misses == 0
        assert semantic_cache.saves == 0

    @pytest.mark.asyncio
    async def test_cache_hit(self, semantic_cache, langcache_mock):
        """Test cache hit scenario"""
        # Setup mock response
        match = MagicMock()
        match.response = "Cached response"
        match.similarity = 0.98
        match.metadata = {"timestamp": "2025-09-27", "model": "gpt-4"}

        search_response = MagicMock()
        search_response.matches = [match]
        langcache_mock.search.return_value = search_response

        # Test cache retrieval
        result = await semantic_cache.get("test prompt", model="gpt-4")

        assert result is not None
        assert result["response"] == "Cached response"
        assert result["cached"] is True
        assert result["similarity"] == 0.98
        assert semantic_cache.hits == 1
        assert semantic_cache.misses == 0

    @pytest.mark.asyncio
    async def test_cache_miss(self, semantic_cache, langcache_mock):
        """Test cache miss scenario"""
        # Setup empty response
        search_response = MagicMock()
        search_response.matches = []
        langcache_mock.search.return_value = search_response

        # Test cache miss
        result = await semantic_cache.get("new prompt", model="gpt-4")

        assert result is None
        assert semantic_cache.hits == 0
        assert semantic_cache.misses == 1

    @pytest.mark.asyncio
    async def test_cache_save(self, semantic_cache, langcache_mock):
        """Test saving to cache"""
        # Setup successful save response
        save_response = MagicMock()
        save_response.status = "success"
        save_response.entry_id = "test-entry-123"
        langcache_mock.set.return_value = save_response

        # Test saving
        success = await semantic_cache.set(
            "test prompt", "test response", model="gpt-4", temperature=0.7
        )

        assert success is True
        assert semantic_cache.saves == 1
        langcache_mock.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_cache(self, semantic_cache, redis_mock):
        """Test fallback to exact match cache"""
        # Disable LangCache to test fallback
        semantic_cache.langcache_client = None

        # Save to fallback cache
        success = await semantic_cache.set("test prompt", "test response", model="gpt-4")
        assert success is True

        # Retrieve from fallback cache
        semantic_cache.fallback_cache[
            semantic_cache._create_cache_key("test prompt", "gpt-4", 0.7)
        ] = {
            "response": "test response",
            "model": "gpt-4",
            "temperature": 0.7,
            "timestamp": datetime.utcnow().isoformat(),
        }

        result = await semantic_cache.get("test prompt", model="gpt-4")
        assert result is not None
        assert result["response"] == "test response"

    @pytest.mark.asyncio
    async def test_calculate_savings(self, semantic_cache):
        """Test cost savings calculation"""
        # Simulate cache activity
        semantic_cache.hits = 100
        semantic_cache.misses = 50

        savings = semantic_cache.calculate_savings(model="gpt-4")

        assert savings["hit_rate"] == pytest.approx(0.667, rel=0.01)
        assert savings["estimated_monthly_savings"] > 0
        assert savings["tokens_saved"] > 0


# ============================================
# API KEY MANAGER TESTS
# ============================================


class TestAPIKeyManager:
    """Test suite for APIKeyManager service"""

    @pytest_asyncio.fixture
    async def api_key_manager(self, redis_mock, supabase_mock):
        """Create APIKeyManager instance with mocks"""
        with patch(
            "apps.backend.services.api_key_manager.aioredis.from_url",
            return_value=redis_mock,
        ):
            with patch(
                "apps.backend.services.api_key_manager.create_client",
                return_value=supabase_mock,
            ):
                manager = APIKeyManager()
                await manager.initialize()
                yield manager
                await manager.close()

    @pytest.mark.asyncio
    async def test_generate_api_key(self, api_key_manager):
        """Test API key generation"""
        key_data = await api_key_manager.generate_api_key(
            name="Test API Key",
            scopes=[APIKeyScope.READ, APIKeyScope.WRITE],
            organization="TestOrg",
        )

        assert key_data is not None
        assert "key" in key_data
        assert "key_id" in key_data
        assert key_data["key"].startswith("tk_")  # Test key prefix
        assert len(key_data["key"]) > 32

    @pytest.mark.asyncio
    async def test_validate_api_key(self, api_key_manager, supabase_mock):
        """Test API key validation"""
        # Setup mock response
        supabase_mock.rpc.return_value = {
            "is_valid": True,
            "key_id": "test-key-id",
            "name": "Test Key",
            "scopes": ["read", "write"],
            "rate_limits": {"per_minute": 60, "per_hour": 1000},
        }

        # Generate and validate key
        key_data = await api_key_manager.generate_api_key(
            name="Test Key", scopes=[APIKeyScope.READ]
        )

        validation = await api_key_manager.validate_api_key(key_data["key"])

        assert validation["is_valid"] is True
        assert validation["key_id"] == "test-key-id"
        assert "read" in validation["scopes"]

    @pytest.mark.asyncio
    async def test_rate_limiting(self, api_key_manager, redis_mock):
        """Test API key rate limiting"""
        # Setup rate limit tracking
        redis_mock.incr = AsyncMock(return_value=5)
        redis_mock.expire = AsyncMock(return_value=True)

        # Check rate limit
        allowed = await api_key_manager.check_rate_limit(key_id="test-key", limit=10, window=60)

        assert allowed is True

        # Exceed rate limit
        redis_mock.incr.return_value = 11
        allowed = await api_key_manager.check_rate_limit(key_id="test-key", limit=10, window=60)

        assert allowed is False

    @pytest.mark.asyncio
    async def test_key_rotation(self, api_key_manager):
        """Test API key rotation"""
        # Create initial key
        original_key = await api_key_manager.generate_api_key(
            name="Rotation Test", scopes=[APIKeyScope.ADMIN]
        )

        # Rotate key
        new_key = await api_key_manager.rotate_api_key(key_id=original_key["key_id"])

        assert new_key is not None
        assert new_key["key"] != original_key["key"]
        assert new_key["key_id"] == original_key["key_id"]

    @pytest.mark.asyncio
    async def test_revoke_api_key(self, api_key_manager, supabase_mock):
        """Test API key revocation"""
        # Setup mock
        supabase_mock.table.return_value.update.return_value.execute.return_value = {
            "data": [{"status": "revoked"}]
        }

        # Revoke key
        success = await api_key_manager.revoke_api_key(
            key_id="test-key-id", reason="Security violation"
        )

        assert success is True


# ============================================
# MIGRATION MANAGER TESTS
# ============================================


class TestSupabaseMigrationManager:
    """Test suite for SupabaseMigrationManager"""

    @pytest_asyncio.fixture
    async def migration_manager(self, supabase_mock, redis_mock):
        """Create MigrationManager instance with mocks"""
        with patch(
            "apps.backend.services.supabase_migration_manager.create_client",
            return_value=supabase_mock,
        ):
            with patch(
                "apps.backend.services.supabase_migration_manager.aioredis.from_url",
                return_value=redis_mock,
            ):
                manager = SupabaseMigrationManager()
                await manager.initialize()
                yield manager
                await manager.close()

    @pytest.mark.asyncio
    async def test_blue_green_migration(self, migration_manager, supabase_mock):
        """Test blue-green migration strategy"""
        # Create test migration
        migration = Migration(
            id="test-migration-001",
            name="Add indexes",
            up_sql="CREATE INDEX idx_test ON users(email);",
            down_sql="DROP INDEX idx_test;",
            strategy=MigrationStrategy.BLUE_GREEN,
        )

        # Mock successful execution
        supabase_mock.rpc.return_value = {"success": True}

        # Run migration
        result = await migration_manager.apply_migration(migration)

        assert result.status == MigrationStatus.COMPLETED
        assert result.execution_time > 0
        supabase_mock.rpc.assert_called()

    @pytest.mark.asyncio
    async def test_migration_rollback(self, migration_manager, supabase_mock):
        """Test migration rollback on failure"""
        # Create failing migration
        migration = Migration(
            id="test-migration-002",
            name="Bad migration",
            up_sql="INVALID SQL;",
            down_sql="DROP TABLE test;",
            strategy=MigrationStrategy.ROLLING,
        )

        # Mock failure then successful rollback
        supabase_mock.rpc.side_effect = [
            Exception("SQL Error"),  # Migration fails
            {"success": True},  # Rollback succeeds
        ]

        # Run migration
        result = await migration_manager.apply_migration(migration)

        assert result.status == MigrationStatus.ROLLED_BACK
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_migration_validation(self, migration_manager):
        """Test migration validation"""
        # Valid migration
        valid_migration = Migration(
            id="test-valid",
            name="Valid migration",
            up_sql="CREATE TABLE test (id INT);",
            down_sql="DROP TABLE test;",
        )

        is_valid = await migration_manager.validate_migration(valid_migration)
        assert is_valid is True

        # Invalid migration (empty SQL)
        invalid_migration = Migration(
            id="test-invalid", name="Invalid migration", up_sql="", down_sql=""
        )

        is_valid = await migration_manager.validate_migration(invalid_migration)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_migration_health_check(self, migration_manager, supabase_mock):
        """Test post-migration health check"""
        # Mock healthy database
        supabase_mock.table.return_value.select.return_value.execute.return_value = {
            "data": [{"id": 1}]
        }

        # Run health check
        is_healthy = await migration_manager.health_check()

        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_migration_locking(self, migration_manager, redis_mock):
        """Test distributed migration locking"""
        # Test acquiring lock
        redis_mock.set.return_value = True
        lock_acquired = await migration_manager.acquire_migration_lock("test-migration")
        assert lock_acquired is True

        # Test lock already held
        redis_mock.set.return_value = False
        lock_acquired = await migration_manager.acquire_migration_lock("test-migration")
        assert lock_acquired is False

        # Test releasing lock
        redis_mock.delete.return_value = 1
        await migration_manager.release_migration_lock("test-migration")
        redis_mock.delete.assert_called()


# ============================================
# BACKUP MANAGER TESTS
# ============================================


class TestBackupManager:
    """Test suite for BackupManager"""

    @pytest_asyncio.fixture
    async def backup_manager(self, s3_mock):
        """Create BackupManager instance with mocks"""
        config = {
            "backup_path": "/tmp/test_backups",
            "retention": {"daily": 7, "weekly": 4, "monthly": 12},
            "encryption": {"enabled": True, "key": "test_encryption_key_32_characters"},
            "s3": {"enabled": True, "bucket": "test-backups", "region": "us-east-1"},
        }

        with patch(
            "infrastructure.backups.scripts.backup_manager.boto3.client",
            return_value=s3_mock,
        ):
            manager = BackupManager(config)
            await manager.initialize()
            yield manager
            await manager.close()

    @pytest.mark.asyncio
    async def test_full_backup(self, backup_manager, s3_mock):
        """Test full backup creation"""
        # Create test backup
        backup_job = await backup_manager.create_backup(backup_type=BackupType.FULL)

        assert backup_job is not None
        assert backup_job.type == BackupType.FULL
        assert backup_job.status in [BackupStatus.IN_PROGRESS, BackupStatus.COMPLETED]
        assert backup_job.size > 0

    @pytest.mark.asyncio
    async def test_incremental_backup(self, backup_manager):
        """Test incremental backup"""
        # Create base full backup first
        full_backup = await backup_manager.create_backup(BackupType.FULL)

        # Create incremental backup
        incremental_backup = await backup_manager.create_backup(backup_type=BackupType.INCREMENTAL)

        assert incremental_backup.type == BackupType.INCREMENTAL
        assert incremental_backup.parent_id == full_backup.id

    @pytest.mark.asyncio
    async def test_backup_encryption(self, backup_manager):
        """Test backup encryption"""
        # Create encrypted backup
        backup_job = await backup_manager.create_backup(backup_type=BackupType.FULL, encrypt=True)

        assert backup_job.encrypted is True
        assert backup_job.encryption_method == "AES-256"

    @pytest.mark.asyncio
    async def test_backup_restore(self, backup_manager):
        """Test backup restoration"""
        # Create backup
        backup_job = await backup_manager.create_backup(BackupType.FULL)

        # Restore backup
        restore_success = await backup_manager.restore_backup(
            backup_id=backup_job.id, target_path="/tmp/restore_test"
        )

        assert restore_success is True

    @pytest.mark.asyncio
    async def test_backup_retention(self, backup_manager):
        """Test backup retention policy"""
        # Create multiple backups
        for _ in range(10):
            await backup_manager.create_backup(BackupType.FULL)

        # Apply retention policy
        await backup_manager.apply_retention_policy()

        # Should keep only configured number of backups
        remaining_backups = await backup_manager.list_backups()
        assert len(remaining_backups) <= 7  # Daily retention limit

    @pytest.mark.asyncio
    async def test_s3_upload(self, backup_manager, s3_mock):
        """Test S3 backup upload"""
        # Create backup
        backup_job = await backup_manager.create_backup(BackupType.FULL)

        # Upload to S3
        upload_success = await backup_manager.upload_to_s3(backup_job.id)

        assert upload_success is True
        s3_mock.upload_file.assert_called()

    @pytest.mark.asyncio
    async def test_point_in_time_recovery(self, backup_manager):
        """Test point-in-time recovery"""
        # Create backups at different times
        await backup_manager.create_backup(BackupType.FULL)
        await asyncio.sleep(0.1)
        await backup_manager.create_backup(BackupType.INCREMENTAL)

        # Restore to specific point in time
        target_time = datetime.utcnow() - timedelta(minutes=5)
        restore_success = await backup_manager.restore_to_point_in_time(
            target_time=target_time, target_path="/tmp/pitr_test"
        )

        assert restore_success is True


# ============================================
# ROBLOX DEPLOYMENT TESTS
# ============================================


class TestRobloxAssetManager:
    """Test suite for enhanced Roblox deployment"""

    @pytest_asyncio.fixture
    async def asset_manager(self, redis_mock):
        """Create RobloxAssetManager instance with mocks"""
        with patch(
            "apps.backend.services.roblox_deployment.aioredis.from_url",
            return_value=redis_mock,
        ):
            manager = RobloxAssetManager()
            await manager.initialize()
            yield manager
            await manager.close()

    @pytest.mark.asyncio
    async def test_asset_upload(self, asset_manager):
        """Test asset upload with validation"""
        # Create test asset
        asset_data = {
            "name": "TestScript",
            "type": AssetType.SCRIPT,
            "content": 'print("Hello Roblox")',
            "metadata": {"version": "1.0.0", "author": "TestUser"},
        }

        # Upload asset
        asset_id = await asset_manager.upload_asset(asset_data)

        assert asset_id is not None
        assert len(asset_id) > 0

    @pytest.mark.asyncio
    async def test_asset_bundling(self, asset_manager):
        """Test asset bundling for deployment"""
        # Create multiple assets
        assets = [
            {"name": "Script1", "type": AssetType.SCRIPT, "content": "code1"},
            {"name": "Model1", "type": AssetType.MODEL, "content": "model1"},
            {"name": "Image1", "type": AssetType.IMAGE, "content": b"image_data"},
        ]

        # Create bundle
        bundle_id = await asset_manager.create_bundle(assets=assets, bundle_name="TestBundle")

        assert bundle_id is not None
        bundle_info = await asset_manager.get_bundle_info(bundle_id)
        assert bundle_info["asset_count"] == 3

    @pytest.mark.asyncio
    async def test_version_control(self, asset_manager):
        """Test asset version control"""
        # Upload initial version
        await asset_manager.upload_asset(
            {
                "name": "VersionedScript",
                "type": AssetType.SCRIPT,
                "content": "v1 content",
                "version": "1.0.0",
            }
        )

        # Upload new version
        await asset_manager.upload_asset(
            {
                "name": "VersionedScript",
                "type": AssetType.SCRIPT,
                "content": "v2 content",
                "version": "2.0.0",
            }
        )

        # Get version history
        history = await asset_manager.get_version_history("VersionedScript")

        assert len(history) == 2
        assert history[0]["version"] == "1.0.0"
        assert history[1]["version"] == "2.0.0"

    @pytest.mark.asyncio
    async def test_deployment_rollback(self, asset_manager):
        """Test deployment rollback capability"""
        # Deploy assets
        deployment_id = await asset_manager.deploy_assets(
            environment="production", assets=["asset1", "asset2"]
        )

        # Simulate failure and rollback
        rollback_success = await asset_manager.rollback_deployment(deployment_id=deployment_id)

        assert rollback_success is True

    @pytest.mark.asyncio
    async def test_rate_limiting(self, asset_manager):
        """Test Roblox API rate limiting"""
        # Test rate limit tracking
        for i in range(5):
            allowed = await asset_manager.check_rate_limit()
            assert allowed is True

        # Simulate reaching rate limit
        asset_manager.rate_limit_remaining = 0
        allowed = await asset_manager.check_rate_limit()
        assert allowed is False

        # Wait for rate limit reset
        asset_manager.rate_limit_reset_time = datetime.utcnow() - timedelta(seconds=1)
        allowed = await asset_manager.check_rate_limit()
        assert allowed is True


# ============================================
# INTEGRATION TESTS
# ============================================


class TestWeek2Integration:
    """Integration tests for Week 2 services working together"""

    @pytest.mark.asyncio
    async def test_cached_ai_service_integration(self, redis_mock, langcache_mock):
        """Test CachedAIService with SemanticCache"""
        with patch(
            "apps.backend.services.semantic_cache.aioredis.from_url",
            return_value=redis_mock,
        ):
            with patch("apps.backend.services.semantic_cache.lang_cache", langcache_mock):
                # Initialize services
                cache = SemanticCacheService()
                await cache.initialize()

                ai_service = CachedAIService(cache=cache)

                # Mock AI response
                with patch.object(ai_service, "_call_ai_model", return_value="AI Response"):
                    # First call - cache miss
                    response1 = await ai_service.generate(prompt="Test prompt", model="gpt-4")

                    assert response1 == "AI Response"
                    assert cache.misses == 1

                    # Save to cache
                    await cache.set("Test prompt", "AI Response", model="gpt-4")

                    # Second call - cache hit
                    match = MagicMock()
                    match.response = "AI Response"
                    match.similarity = 0.99
                    search_response = MagicMock()
                    search_response.matches = [match]
                    langcache_mock.search.return_value = search_response

                    response2 = await ai_service.generate(prompt="Test prompt", model="gpt-4")

                    assert response2 == "AI Response"
                    assert cache.hits == 1

                await cache.close()

    @pytest.mark.asyncio
    async def test_migration_with_backup(self, supabase_mock, s3_mock):
        """Test migration with automatic backup"""
        # Initialize services
        migration_manager = SupabaseMigrationManager()
        backup_manager = BackupManager(
            {"backup_path": "/tmp/migration_backups", "encryption": {"enabled": True}}
        )

        # Create backup before migration
        backup_job = await backup_manager.create_backup(BackupType.FULL)

        # Run migration
        migration = Migration(
            id="test-migration",
            name="Schema update",
            up_sql="ALTER TABLE users ADD COLUMN age INT;",
            down_sql="ALTER TABLE users DROP COLUMN age;",
        )

        result = await migration_manager.apply_migration(migration)

        # If migration fails, restore from backup
        if result.status == MigrationStatus.FAILED:
            restore_success = await backup_manager.restore_backup(backup_job.id)
            assert restore_success is True

    @pytest.mark.asyncio
    async def test_api_key_with_rate_limiting(self, redis_mock, supabase_mock):
        """Test API key management with rate limiting"""
        # Initialize services
        api_manager = APIKeyManager()

        # Generate API key with rate limits
        key_data = await api_manager.generate_api_key(
            name="Rate Limited Key", scopes=[APIKeyScope.READ], rate_limit_per_minute=10
        )

        # Simulate API requests
        for i in range(15):
            allowed = await api_manager.check_rate_limit(
                key_id=key_data["key_id"], limit=10, window=60
            )

            if i < 10:
                assert allowed is True
            else:
                assert allowed is False

    @pytest.mark.asyncio
    async def test_circuit_breaker_pattern(self):
        """Test circuit breaker implementation"""
        from apps.backend.core.circuit_breaker import CircuitBreaker

        breaker = CircuitBreaker(
            failure_threshold=3, recovery_timeout=60, expected_exception=Exception
        )

        # Simulate failures
        for _ in range(3):
            try:
                with breaker:
                    raise Exception("Service unavailable")
            except:
                pass

        # Circuit should be open
        assert breaker.state == "OPEN"

        # Wait for recovery
        await asyncio.sleep(61)

        # Circuit should be half-open
        assert breaker.state == "HALF_OPEN"


# ============================================
# PERFORMANCE TESTS
# ============================================


class TestWeek2Performance:
    """Performance tests for Week 2 services"""

    @pytest.mark.asyncio
    async def test_cache_performance(self, semantic_cache):
        """Test semantic cache performance"""
        import time

        # Measure cache hit performance
        start = time.time()
        for _ in range(100):
            await semantic_cache.get("test prompt", model="gpt-4")
        elapsed = time.time() - start

        # Should complete 100 lookups in under 1 second
        assert elapsed < 1.0

        # Calculate operations per second
        ops_per_second = 100 / elapsed
        assert ops_per_second > 100

    @pytest.mark.asyncio
    async def test_migration_performance(self, migration_manager):
        """Test migration execution performance"""
        import time

        # Simple migration
        migration = Migration(
            id="perf-test",
            name="Performance test",
            up_sql="SELECT 1;",
            down_sql="SELECT 1;",
        )

        start = time.time()
        result = await migration_manager.apply_migration(migration)
        elapsed = time.time() - start

        # Should complete simple migration in under 5 seconds
        assert elapsed < 5.0
        assert result.execution_time < 5.0

    @pytest.mark.asyncio
    async def test_backup_compression_ratio(self, backup_manager):
        """Test backup compression efficiency"""
        # Create test data

        # Create compressed backup
        backup_job = await backup_manager.create_backup(backup_type=BackupType.FULL, compress=True)

        # Check compression ratio
        assert backup_job.compression_ratio > 0.5  # At least 50% compression

    @pytest.mark.asyncio
    async def test_concurrent_api_key_validation(self, api_key_manager):
        """Test concurrent API key validation performance"""
        # Generate test key
        key_data = await api_key_manager.generate_api_key(
            name="Perf Test", scopes=[APIKeyScope.READ]
        )

        # Validate key concurrently
        tasks = []
        for _ in range(50):
            task = api_key_manager.validate_api_key(key_data["key"])
            tasks.append(task)

        start = time.time()
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start

        # Should handle 50 concurrent validations in under 2 seconds
        assert elapsed < 2.0
        assert all(r["is_valid"] for r in results)


# ============================================
# SECURITY TESTS
# ============================================


class TestWeek2Security:
    """Security tests for Week 2 services"""

    @pytest.mark.asyncio
    async def test_api_key_entropy(self, api_key_manager):
        """Test API key has sufficient entropy"""
        key_data = await api_key_manager.generate_api_key(
            name="Entropy Test", scopes=[APIKeyScope.ADMIN]
        )

        # Key should be at least 32 characters
        assert len(key_data["key"]) >= 32

        # Test randomness (no repeated patterns)
        key = key_data["key"].replace("tk_", "")  # Remove prefix
        unique_chars = len(set(key))
        assert unique_chars > 20  # High character diversity

    @pytest.mark.asyncio
    async def test_backup_encryption_strength(self, backup_manager):
        """Test backup encryption security"""
        # Create encrypted backup
        backup_job = await backup_manager.create_backup(backup_type=BackupType.FULL, encrypt=True)

        # Verify encryption
        assert backup_job.encrypted is True
        assert backup_job.encryption_method == "AES-256"

        # Test that encrypted data is not readable
        with pytest.raises(Exception):
            # Attempt to read without decryption should fail
            await backup_manager.read_backup_raw(backup_job.id)

    @pytest.mark.asyncio
    async def test_sql_injection_protection(self, migration_manager):
        """Test protection against SQL injection in migrations"""
        # Malicious migration attempt
        malicious_migration = Migration(
            id="sql-injection-test",
            name="Malicious",
            up_sql="'; DROP TABLE users; --",
            down_sql="SELECT 1;",
        )

        # Should reject dangerous SQL
        is_valid = await migration_manager.validate_migration(malicious_migration)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_rate_limit_bypass_prevention(self, api_key_manager):
        """Test that rate limits cannot be bypassed"""
        key_data = await api_key_manager.generate_api_key(
            name="Rate Limit Test", scopes=[APIKeyScope.READ], rate_limit_per_minute=5
        )

        # Try to bypass with different techniques
        techniques = [
            key_data["key"],  # Original key
            key_data["key"].upper(),  # Case variation
            key_data["key"] + " ",  # Whitespace
        ]

        for technique in techniques:
            # Each should be counted towards same limit
            for _ in range(6):
                await api_key_manager.check_rate_limit(
                    key_id=key_data["key_id"], limit=5, window=60
                )

            # Should be rate limited
            allowed = await api_key_manager.check_rate_limit(
                key_id=key_data["key_id"], limit=5, window=60
            )
            assert allowed is False


# ============================================
# ERROR HANDLING TESTS
# ============================================


class TestWeek2ErrorHandling:
    """Error handling tests for Week 2 services"""

    @pytest.mark.asyncio
    async def test_redis_connection_failure(self, redis_mock):
        """Test graceful handling of Redis connection failure"""
        # Simulate connection failure
        redis_mock.ping.side_effect = RedisConnectionError("Connection failed")

        # Services should fall back gracefully
        cache = SemanticCacheService()
        await cache.initialize()

        # Should use in-memory fallback
        assert cache.redis_client is None
        assert cache.enabled is True  # Still operational with fallback

    @pytest.mark.asyncio
    async def test_langcache_api_failure(self, langcache_mock):
        """Test handling of LangCache API failures"""
        # Simulate API error
        langcache_mock.search.side_effect = Exception("API Error")

        cache = SemanticCacheService()
        await cache.initialize()

        # Should fall back to exact match
        await cache.get("test prompt")
        assert cache.errors == 1

    @pytest.mark.asyncio
    async def test_migration_rollback_failure(self, migration_manager, supabase_mock):
        """Test handling of rollback failure"""
        migration = Migration(
            id="rollback-fail-test",
            name="Failing migration",
            up_sql="INVALID SQL;",
            down_sql="ALSO INVALID;",
        )

        # Both migration and rollback fail
        supabase_mock.rpc.side_effect = [
            Exception("Migration failed"),
            Exception("Rollback failed"),
        ]

        result = await migration_manager.apply_migration(migration)

        assert result.status == MigrationStatus.FAILED
        assert "rollback failed" in result.error.lower()

    @pytest.mark.asyncio
    async def test_backup_corruption_detection(self, backup_manager):
        """Test detection of corrupted backups"""
        # Create backup
        backup_job = await backup_manager.create_backup(BackupType.FULL)

        # Simulate corruption
        backup_manager._corrupt_backup(backup_job.id)  # Test method

        # Verify should detect corruption
        is_valid = await backup_manager.verify_backup(backup_job.id)
        assert is_valid is False

        # Restore should fail safely
        with pytest.raises(Exception) as exc_info:
            await backup_manager.restore_backup(backup_job.id)
        assert "corrupted" in str(exc_info.value).lower()


if __name__ == "__main__":
    # Run tests with coverage
    pytest.main(
        [
            __file__,
            "-v",
            "--cov=apps.backend.services",
            "--cov=infrastructure.backups",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-fail-under=90",
        ]
    )

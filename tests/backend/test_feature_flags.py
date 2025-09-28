import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
Test suite for Feature Flag Management System
Validates feature flag functionality for Phase 1
"""

import pytest
import os
import hashlib
from unittest.mock import Mock, patch, MagicMock
import redis
from redis.exceptions import RedisError

from apps.backend.core.feature_flags import (
    FeatureFlag,
    FeatureFlagManager,
    get_feature_flags
)


class TestFeatureFlags:
    """Test FeatureFlag enum"""

    def test_feature_flag_values(self):
        """Test feature flag enum values"""
        assert FeatureFlag.GPT5_MIGRATION.value == "gpt5_migration"
        assert FeatureFlag.OAUTH21_COMPLIANCE.value == "oauth21_compliance"
        assert FeatureFlag.ENHANCED_MONITORING.value == "enhanced_monitoring"
        assert FeatureFlag.PKCE_ENFORCEMENT.value == "pkce_enforcement"
        assert FeatureFlag.RATE_LIMITING.value == "rate_limiting"
        assert FeatureFlag.SECURITY_HEADERS.value == "security_headers"
        assert FeatureFlag.JWT_ROTATION.value == "jwt_rotation"


class TestFeatureFlagManager:
    """Test FeatureFlagManager"""

    @pytest.fixture
    def redis_mock(self):
        """Mock Redis client"""
        mock = Mock(spec=redis.Redis)
        mock.ping = Mock(return_value=True)
        mock.get = Mock(return_value=None)
        mock.set = Mock(return_value=True)
        mock.keys = Mock(return_value=[])
        mock.delete = Mock(return_value=True)
        return mock

    @pytest.fixture
    def manager(self, redis_mock):
        """Create feature flag manager with mocked Redis"""
        with patch('apps.backend.core.feature_flags.redis.Redis', return_value=redis_mock):
            manager = FeatureFlagManager()
            manager.redis_client = redis_mock
            manager.redis_available = True
            return manager

    @pytest.fixture
    def manager_no_redis(self):
        """Create feature flag manager without Redis"""
        with patch('apps.backend.core.feature_flags.redis.Redis', side_effect=RedisError("Connection failed")):
            manager = FeatureFlagManager()
            return manager

    def test_initialization_with_redis(self, redis_mock):
        """Test manager initialization with Redis available"""
        with patch('apps.backend.core.feature_flags.redis.Redis', return_value=redis_mock):
            manager = FeatureFlagManager()

            assert manager.redis_available == True
            assert manager.redis_client is not None

    def test_initialization_without_redis(self):
        """Test manager initialization when Redis is unavailable"""
        with patch('apps.backend.core.feature_flags.redis.Redis', side_effect=RedisError("Connection failed")):
            manager = FeatureFlagManager()

            assert manager.redis_available == False
            assert manager.redis_client is None

    def test_default_flags(self, manager):
        """Test default flag states"""
        defaults = manager.default_flags

        # Phase 1 flags should start disabled
        assert defaults[FeatureFlag.GPT5_MIGRATION.value] == False
        assert defaults[FeatureFlag.OAUTH21_COMPLIANCE.value] == False

        # Monitoring should be enabled by default
        assert defaults[FeatureFlag.ENHANCED_MONITORING.value] == True
        assert defaults[FeatureFlag.RATE_LIMITING.value] == True
        assert defaults[FeatureFlag.SECURITY_HEADERS.value] == True

        # Advanced features start disabled
        assert defaults[FeatureFlag.PKCE_ENFORCEMENT.value] == False
        assert defaults[FeatureFlag.JWT_ROTATION.value] == False

    def test_is_enabled_default(self, manager):
        """Test flag evaluation with defaults"""
        manager.redis_client.get = Mock(return_value=None)

        # Should return default value
        assert manager.is_enabled(FeatureFlag.GPT5_MIGRATION) == False
        assert manager.is_enabled(FeatureFlag.ENHANCED_MONITORING) == True

    def test_is_enabled_redis_global(self, manager):
        """Test flag evaluation with Redis global value"""
        manager.redis_client.get = Mock(return_value='true')

        assert manager.is_enabled(FeatureFlag.GPT5_MIGRATION) == True

        manager.redis_client.get = Mock(return_value='false')
        assert manager.is_enabled(FeatureFlag.GPT5_MIGRATION) == False

    def test_is_enabled_user_specific(self, manager):
        """Test user-specific flag evaluation"""
        # User-specific flag overrides global
        manager.redis_client.get = Mock(side_effect=['true', None])  # User flag, then global

        assert manager.is_enabled(FeatureFlag.GPT5_MIGRATION, user_id="user-123") == True

        # Called twice: once for user flag, once for global (if user not found)
        assert manager.redis_client.get.call_count == 1
        manager.redis_client.get.assert_called_with("feature_flag:gpt5_migration:user:user-123")

    def test_is_enabled_env_override(self, manager):
        """Test environment variable override"""
        manager.redis_client.get = Mock(return_value='false')

        # Set environment variable
        with patch.dict(os.environ, {'FF_GPT5_MIGRATION': 'true'}):
            # Recreate manager to pick up env var
            manager = FeatureFlagManager()
            manager.redis_client = Mock()
            manager.redis_client.get = Mock(return_value=None)
            manager.redis_available = True

            assert manager.is_enabled(FeatureFlag.GPT5_MIGRATION) == True

    def test_is_enabled_priority_order(self, manager):
        """Test flag evaluation priority order"""
        # Priority: User > Redis > Env > Default

        # Setup: User=true, Redis=false, Default=false
        manager.redis_client.get = Mock(side_effect=['true', 'false'])
        assert manager.is_enabled(FeatureFlag.GPT5_MIGRATION, user_id="user-123") == True

        # Setup: No user, Redis=true, Default=false
        manager.redis_client.get = Mock(side_effect=[None, 'true'])
        assert manager.is_enabled(FeatureFlag.GPT5_MIGRATION, user_id="user-456") == True

        # Setup: No user, No Redis, Default=false
        manager.redis_client.get = Mock(return_value=None)
        assert manager.is_enabled(FeatureFlag.GPT5_MIGRATION) == False

    def test_set_flag_global(self, manager):
        """Test setting global flag"""
        result = manager.set_flag(FeatureFlag.GPT5_MIGRATION, True)

        assert result == True
        manager.redis_client.set.assert_called_with(
            "feature_flag:gpt5_migration",
            "true"
        )

    def test_set_flag_user_specific(self, manager):
        """Test setting user-specific flag"""
        result = manager.set_flag(FeatureFlag.GPT5_MIGRATION, False, user_id="user-123")

        assert result == True
        manager.redis_client.set.assert_called_with(
            "feature_flag:gpt5_migration:user:user-123",
            "false"
        )

    def test_set_flag_no_redis(self, manager_no_redis):
        """Test setting flag when Redis unavailable"""
        result = manager_no_redis.set_flag(FeatureFlag.GPT5_MIGRATION, True)

        assert result == False  # Should fail gracefully

    def test_get_all_flags(self, manager):
        """Test getting all flag states"""
        manager.redis_client.get = Mock(return_value=None)

        flags = manager.get_all_flags()

        assert flags[FeatureFlag.GPT5_MIGRATION.value] == False
        assert flags[FeatureFlag.ENHANCED_MONITORING.value] == True
        assert len(flags) == len(FeatureFlag)

    def test_get_all_flags_with_user(self, manager):
        """Test getting all flags for specific user"""
        # Mock different responses for different flags
        manager.redis_client.get = Mock(side_effect=[
            'true',   # User-specific GPT5_MIGRATION
            None,     # No global GPT5_MIGRATION
            None,     # No user-specific OAUTH21_COMPLIANCE
            'false',  # Global OAUTH21_COMPLIANCE
            None, None,  # ENHANCED_MONITORING defaults
            None, None,  # PKCE_ENFORCEMENT defaults
            None, None,  # RATE_LIMITING defaults
            None, None,  # SECURITY_HEADERS defaults
            None, None,  # JWT_ROTATION defaults
        ])

        flags = manager.get_all_flags(user_id="user-123")

        assert flags[FeatureFlag.GPT5_MIGRATION.value] == True
        assert flags[FeatureFlag.OAUTH21_COMPLIANCE.value] == False

    def test_percentage_rollout_set(self, manager):
        """Test setting percentage rollout"""
        result = manager.enable_percentage_rollout(FeatureFlag.GPT5_MIGRATION, 25)

        assert result == True
        manager.redis_client.set.assert_called_with(
            "feature_flag:gpt5_migration:rollout",
            "25"
        )

    def test_percentage_rollout_invalid(self, manager):
        """Test invalid percentage rollout"""
        with pytest.raises(ValueError):
            manager.enable_percentage_rollout(FeatureFlag.GPT5_MIGRATION, 101)

        with pytest.raises(ValueError):
            manager.enable_percentage_rollout(FeatureFlag.GPT5_MIGRATION, -1)

    def test_check_percentage_rollout_enabled(self, manager):
        """Test checking if user is in percentage rollout"""
        manager.redis_client.get = Mock(return_value='50')  # 50% rollout

        # Test with multiple users
        enabled_count = 0
        for i in range(100):
            if manager.check_percentage_rollout(FeatureFlag.GPT5_MIGRATION, f"user-{i}"):
                enabled_count += 1

        # Should be roughly 50% (with some variance)
        assert 35 <= enabled_count <= 65  # Allow for statistical variance

    def test_check_percentage_rollout_consistent(self, manager):
        """Test percentage rollout is consistent for same user"""
        manager.redis_client.get = Mock(return_value='50')

        # Same user should always get same result
        user_id = "consistent-user"
        first_result = manager.check_percentage_rollout(FeatureFlag.GPT5_MIGRATION, user_id)

        for _ in range(10):
            result = manager.check_percentage_rollout(FeatureFlag.GPT5_MIGRATION, user_id)
            assert result == first_result

    def test_check_percentage_rollout_boundaries(self, manager):
        """Test percentage rollout boundary conditions"""
        # 0% rollout - no users
        manager.redis_client.get = Mock(return_value='0')
        assert manager.check_percentage_rollout(FeatureFlag.GPT5_MIGRATION, "user-1") == False

        # 100% rollout - all users
        manager.redis_client.get = Mock(return_value='100')
        assert manager.check_percentage_rollout(FeatureFlag.GPT5_MIGRATION, "user-1") == True

        # No rollout configured
        manager.redis_client.get = Mock(return_value=None)
        assert manager.check_percentage_rollout(FeatureFlag.GPT5_MIGRATION, "user-1") == False

    def test_reset_all_flags(self, manager):
        """Test resetting all flags"""
        manager.redis_client.keys = Mock(return_value=[
            "feature_flag:gpt5_migration",
            "feature_flag:oauth21_compliance",
            "feature_flag:gpt5_migration:user:user-123"
        ])

        result = manager.reset_all_flags()

        assert result == True
        manager.redis_client.delete.assert_called_once()
        call_args = manager.redis_client.delete.call_args[0]
        assert len(call_args) == 3

    def test_reset_all_flags_no_redis(self, manager_no_redis):
        """Test resetting flags when Redis unavailable"""
        result = manager_no_redis.reset_all_flags()

        assert result == False

    def test_health_check_healthy(self, manager):
        """Test health check with healthy Redis"""
        manager.redis_client.ping = Mock(return_value=True)

        health = manager.health_check()

        assert health["redis_available"] == True
        assert health["redis_status"] == "healthy"
        assert health["flags_configured"] == len(manager.default_flags)

    def test_health_check_unhealthy(self, manager):
        """Test health check with unhealthy Redis"""
        manager.redis_client.ping = Mock(side_effect=RedisError("Connection lost"))

        health = manager.health_check()

        assert health["redis_status"].startswith("unhealthy")
        assert manager.redis_available == False  # Should update status

    def test_health_check_no_redis(self, manager_no_redis):
        """Test health check without Redis"""
        health = manager_no_redis.health_check()

        assert health["redis_available"] == False
        assert health["redis_status"] == "not configured"

    def test_redis_error_handling(self, manager):
        """Test graceful handling of Redis errors"""
        manager.redis_client.get = Mock(side_effect=RedisError("Connection error"))

        # Should fall back to default
        result = manager.is_enabled(FeatureFlag.ENHANCED_MONITORING)
        assert result == True  # Default value

        # Setting should fail gracefully
        manager.redis_client.set = Mock(side_effect=RedisError("Connection error"))
        result = manager.set_flag(FeatureFlag.GPT5_MIGRATION, True)
        assert result == False


class TestFeatureFlagIntegration:
    """Integration tests for feature flags"""

    def test_singleton_pattern(self):
        """Test that get_feature_flags returns singleton"""
        with patch('apps.backend.core.feature_flags.redis.Redis'):
            flags1 = get_feature_flags()
            flags2 = get_feature_flags()

            assert flags1 is flags2

    @pytest.mark.integration
    @pytest.mark.skipif(not os.getenv("REDIS_HOST"), reason="Redis not configured")
    def test_real_redis_connection(self):
        """Test with real Redis connection"""
        manager = get_feature_flags()

        if manager and manager.redis_available:
            # Test basic operations
            manager.set_flag(FeatureFlag.GPT5_MIGRATION, True)
            assert manager.is_enabled(FeatureFlag.GPT5_MIGRATION) == True

            manager.set_flag(FeatureFlag.GPT5_MIGRATION, False)
            assert manager.is_enabled(FeatureFlag.GPT5_MIGRATION) == False

            # Clean up
            manager.reset_all_flags()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=apps.backend.core.feature_flags"])
"""
Feature Flag Management System for Phase 1 Implementation
Provides centralized control for GPT-5 migration and OAuth 2.1 compliance rollout
"""

import logging
import os
from enum import Enum
from typing import Any

import redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class FeatureFlag(Enum):
    """Feature flags for Phase 1 implementation"""

    GPT5_MIGRATION = "gpt5_migration"
    OAUTH21_COMPLIANCE = "oauth21_compliance"
    ENHANCED_MONITORING = "enhanced_monitoring"
    PKCE_ENFORCEMENT = "pkce_enforcement"
    RATE_LIMITING = "rate_limiting"
    SECURITY_HEADERS = "security_headers"
    JWT_ROTATION = "jwt_rotation"
    DEVELOPMENT_AUTH_BYPASS = "development_auth_bypass"  # Secure gated development bypass


class FeatureFlagManager:
    """Centralized feature flag management with Redis backend"""

    def __init__(self):
        """Initialize feature flag manager with Redis connection"""
        try:
            self.redis_client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                password=os.getenv("REDIS_PASSWORD"),
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            self.redis_client.ping()
            self.redis_available = True
            logger.info("Feature flag manager connected to Redis")
        except (RedisError, Exception) as e:
            logger.warning(f"Redis not available for feature flags: {e}")
            self.redis_client = None
            self.redis_available = False

        # Default flag states for Phase 1
        self.default_flags = {
            FeatureFlag.GPT5_MIGRATION.value: False,  # Start disabled
            FeatureFlag.OAUTH21_COMPLIANCE.value: False,  # Start disabled
            FeatureFlag.ENHANCED_MONITORING.value: True,  # Enable monitoring
            FeatureFlag.PKCE_ENFORCEMENT.value: False,  # Start disabled
            FeatureFlag.RATE_LIMITING.value: True,  # Enable rate limiting
            FeatureFlag.SECURITY_HEADERS.value: True,  # Enable security headers
            FeatureFlag.JWT_ROTATION.value: False,  # Start disabled
            FeatureFlag.DEVELOPMENT_AUTH_BYPASS.value: False,  # MUST be explicitly enabled, never default
        }

        # Environment variable overrides (for testing/deployment)
        self.env_overrides = {
            flag.value: os.getenv(f"FF_{flag.value.upper()}") for flag in FeatureFlag
        }

    def is_enabled(self, flag: FeatureFlag, user_id: str | None = None) -> bool:
        """
        Check if a feature flag is enabled

        Priority order:
        1. User-specific flag (if user_id provided)
        2. Redis global flag
        3. Environment variable override
        4. Default value
        """
        flag_key = f"feature_flag:{flag.value}"

        # Check user-specific flag if user_id provided
        if user_id and self.redis_available:
            user_flag_key = f"{flag_key}:user:{user_id}"
            try:
                user_value = self.redis_client.get(user_flag_key)
                if user_value is not None:
                    return user_value.lower() == "true"
            except (RedisError, Exception) as e:
                logger.error(f"Error checking user flag {user_flag_key}: {e}")

        # Check Redis global flag
        if self.redis_available:
            try:
                redis_value = self.redis_client.get(flag_key)
                if redis_value is not None:
                    return redis_value.lower() == "true"
            except (RedisError, Exception) as e:
                logger.error(f"Error checking flag {flag_key}: {e}")

        # Check environment variable override
        env_value = self.env_overrides.get(flag.value)
        if env_value is not None:
            return env_value.lower() in ("true", "1", "yes", "on")

        # Return default value
        return self.default_flags.get(flag.value, False)

    def set_flag(self, flag: FeatureFlag, enabled: bool, user_id: str | None = None):
        """
        Set a feature flag value

        Args:
            flag: The feature flag to set
            enabled: Whether to enable or disable the flag
            user_id: Optional user ID for user-specific flags
        """
        if not self.redis_available:
            logger.warning(f"Cannot set flag {flag.value} - Redis not available")
            return False

        try:
            if user_id:
                flag_key = f"feature_flag:{flag.value}:user:{user_id}"
            else:
                flag_key = f"feature_flag:{flag.value}"

            self.redis_client.set(flag_key, str(enabled).lower())
            logger.info(f"Set {flag_key} to {enabled}")
            return True
        except (RedisError, Exception) as e:
            logger.error(f"Error setting flag {flag.value}: {e}")
            return False

    def get_all_flags(self, user_id: str | None = None) -> dict[str, bool]:
        """Get the status of all feature flags"""
        return {flag.value: self.is_enabled(flag, user_id) for flag in FeatureFlag}

    def enable_percentage_rollout(self, flag: FeatureFlag, percentage: int):
        """
        Enable a feature for a percentage of users

        Args:
            flag: The feature flag to roll out
            percentage: Percentage of users (0-100)
        """
        if not 0 <= percentage <= 100:
            raise ValueError("Percentage must be between 0 and 100")

        if not self.redis_available:
            logger.warning(f"Cannot set percentage rollout - Redis not available")
            return False

        try:
            rollout_key = f"feature_flag:{flag.value}:rollout"
            self.redis_client.set(rollout_key, str(percentage))
            logger.info(f"Set {flag.value} rollout to {percentage}%")
            return True
        except (RedisError, Exception) as e:
            logger.error(f"Error setting rollout for {flag.value}: {e}")
            return False

    def check_percentage_rollout(self, flag: FeatureFlag, user_id: str) -> bool:
        """Check if a user falls within the percentage rollout"""
        if not self.redis_available:
            return False

        try:
            rollout_key = f"feature_flag:{flag.value}:rollout"
            percentage = self.redis_client.get(rollout_key)

            if percentage is None:
                return False

            percentage = int(percentage)
            if percentage <= 0:
                return False
            if percentage >= 100:
                return True

            # Use consistent hashing for user assignment
            import hashlib

            user_hash = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
            return (user_hash % 100) < percentage

        except (RedisError, ValueError, Exception) as e:
            logger.error(f"Error checking rollout for {flag.value}: {e}")
            return False

    def reset_all_flags(self):
        """Reset all flags to default values (for testing)"""
        if not self.redis_available:
            logger.warning("Cannot reset flags - Redis not available")
            return False

        try:
            # Find all feature flag keys
            pattern = "feature_flag:*"
            keys = self.redis_client.keys(pattern)

            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Reset {len(keys)} feature flags")

            return True
        except (RedisError, Exception) as e:
            logger.error(f"Error resetting flags: {e}")
            return False

    def health_check(self) -> dict[str, Any]:
        """Check the health of the feature flag system"""
        health = {
            "redis_available": self.redis_available,
            "flags_configured": len(self.default_flags),
            "env_overrides": sum(1 for v in self.env_overrides.values() if v is not None),
        }

        if self.redis_available:
            try:
                self.redis_client.ping()
                health["redis_status"] = "healthy"
            except (RedisError, Exception) as e:
                health["redis_status"] = f"unhealthy: {str(e)}"
                self.redis_available = False
        else:
            health["redis_status"] = "not configured"

        return health


# Global instance for application-wide use
try:
    feature_flags = FeatureFlagManager()
    logger.info("Feature flag manager initialized")
except Exception as e:
    logger.error(f"Failed to initialize feature flag manager: {e}")
    # Create a minimal fallback instance
    feature_flags = None


def get_feature_flags() -> FeatureFlagManager:
    """Get or create the feature flag manager instance"""
    global feature_flags
    if feature_flags is None:
        feature_flags = FeatureFlagManager()
    return feature_flags

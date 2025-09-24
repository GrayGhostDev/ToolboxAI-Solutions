"""
GPT-4.1 Model Configuration - Phase 4
Configuration and feature flags for GPT-4.1 migration
"""

import os
import json
from datetime import datetime
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, field, asdict
from enum import Enum
import redis

@dataclass
class GPT41ModelConfig:
    """GPT-4.1 model configuration settings"""

    # Model versions
    primary_model: str = "gpt-4.1"
    mini_model: str = "gpt-4.1-mini"
    nano_model: str = "gpt-4.1-nano"
    fallback_model: str = "gpt-4.5-preview"  # Until July 14, 2025

    # Context windows (tokens)
    max_context_gpt41: int = 1000000  # 1M tokens
    max_context_mini: int = 500000
    max_context_nano: int = 200000

    # Output limits
    max_output_gpt41: int = 16384
    max_output_mini: int = 8192
    max_output_nano: int = 4096

    # Cost per 1M tokens (USD)
    cost_input_gpt41: float = 7.50
    cost_output_gpt41: float = 22.50
    cost_input_mini: float = 1.70
    cost_output_mini: float = 5.00
    cost_input_nano: float = 0.50
    cost_output_nano: float = 1.50

    # Performance targets (milliseconds)
    target_latency_gpt41: int = 1500
    target_latency_mini: int = 1000
    target_latency_nano: int = 500

    # Feature support
    supports_reasoning: Dict[str, bool] = field(default_factory=lambda: {
        "gpt-4.1": True,
        "gpt-4.1-mini": False,
        "gpt-4.1-nano": False
    })

    supports_vision: Dict[str, bool] = field(default_factory=lambda: {
        "gpt-4.1": True,
        "gpt-4.1-mini": True,
        "gpt-4.1-nano": False
    })

    # Migration settings
    deprecation_date: str = "2025-07-14"  # GPT-4.5 Preview deprecation
    rollout_start_date: str = "2025-04-01"
    rollout_target_date: str = "2025-06-30"

    # Model selection thresholds
    nano_complexity_threshold: float = 0.3
    mini_complexity_threshold: float = 0.7
    reasoning_complexity_threshold: float = 0.8

@dataclass
class GPT41FeatureFlags:
    """Feature flags for GPT-4.1 migration"""

    # Core migration flags
    enable_gpt41: bool = False
    rollout_percentage: float = 0.0  # 0-100%

    # Model variant flags
    enable_nano_for_simple: bool = True
    enable_mini_for_standard: bool = True
    enable_auto_model_selection: bool = True

    # Optimization flags
    enable_prompt_optimization: bool = True
    enable_response_caching: bool = True
    enable_cost_optimization: bool = True

    # Safety flags
    enable_auto_fallback: bool = True
    enable_deprecation_warnings: bool = True
    enable_performance_monitoring: bool = True

    # Advanced features
    enable_reasoning_mode: bool = False  # GPT-4.1 reasoning capability
    enable_tool_use_optimization: bool = True  # GPT-4.1 improved tool usage
    enable_context_compression: bool = True

    # A/B testing
    enable_ab_testing: bool = True
    ab_test_group_size: float = 10.0  # Percentage for A/B test

    # Rollback
    enable_instant_rollback: bool = True
    rollback_on_error_rate: float = 5.0  # Rollback if error rate > 5%

class MigrationPhase(Enum):
    """Migration phases for GPT-4.1 rollout"""
    TESTING = "testing"  # Internal testing only
    CANARY = "canary"  # 1% of traffic
    EARLY_ACCESS = "early_access"  # 10% of traffic
    BETA = "beta"  # 25% of traffic
    ROLLOUT = "rollout"  # 50% of traffic
    GENERAL_AVAILABILITY = "ga"  # 100% of traffic

@dataclass
class MigrationSchedule:
    """Schedule for GPT-4.1 migration phases"""

    phase: MigrationPhase
    start_date: str
    target_percentage: float
    success_criteria: Dict[str, Any] = field(default_factory=dict)
    rollback_criteria: Dict[str, Any] = field(default_factory=dict)

# Migration schedule
MIGRATION_SCHEDULE = [
    MigrationSchedule(
        phase=MigrationPhase.TESTING,
        start_date="2025-04-01",
        target_percentage=0.0,
        success_criteria={
            "internal_tests_pass": True,
            "performance_baseline_met": True
        }
    ),
    MigrationSchedule(
        phase=MigrationPhase.CANARY,
        start_date="2025-04-07",
        target_percentage=1.0,
        success_criteria={
            "error_rate": {"max": 1.0},
            "latency_p95": {"max": 2000},
            "user_reports": {"max": 5}
        },
        rollback_criteria={
            "error_rate": {"threshold": 2.0},
            "user_reports": {"threshold": 10}
        }
    ),
    MigrationSchedule(
        phase=MigrationPhase.EARLY_ACCESS,
        start_date="2025-04-14",
        target_percentage=10.0,
        success_criteria={
            "error_rate": {"max": 0.5},
            "latency_p95": {"max": 1800},
            "cost_reduction": {"min": 15.0}
        }
    ),
    MigrationSchedule(
        phase=MigrationPhase.BETA,
        start_date="2025-05-01",
        target_percentage=25.0,
        success_criteria={
            "error_rate": {"max": 0.3},
            "latency_p95": {"max": 1600},
            "cost_reduction": {"min": 20.0},
            "user_satisfaction": {"min": 4.5}
        }
    ),
    MigrationSchedule(
        phase=MigrationPhase.ROLLOUT,
        start_date="2025-05-15",
        target_percentage=50.0,
        success_criteria={
            "error_rate": {"max": 0.2},
            "latency_p95": {"max": 1500},
            "cost_reduction": {"min": 25.0}
        }
    ),
    MigrationSchedule(
        phase=MigrationPhase.GENERAL_AVAILABILITY,
        start_date="2025-06-01",
        target_percentage=100.0,
        success_criteria={
            "all_metrics_green": True,
            "deprecation_ready": True
        }
    )
]

class GPT41ConfigManager:
    """Manages GPT-4.1 configuration and feature flags"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client or self._init_redis()
        self.config = GPT41ModelConfig()
        self.feature_flags = GPT41FeatureFlags()
        self._load_from_env()
        self._load_from_redis()

    def _init_redis(self) -> Optional[redis.Redis]:
        """Initialize Redis connection"""
        try:
            return redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=0,
                decode_responses=True
            )
        except Exception as e:
            print(f"Redis initialization failed: {e}")
            return None

    def _load_from_env(self):
        """Load configuration from environment variables"""
        # Feature flags from env
        if os.getenv('GPT41_ENABLED'):
            self.feature_flags.enable_gpt41 = os.getenv('GPT41_ENABLED', 'false').lower() == 'true'

        if os.getenv('GPT41_ROLLOUT_PERCENTAGE'):
            self.feature_flags.rollout_percentage = float(os.getenv('GPT41_ROLLOUT_PERCENTAGE', '0'))

        if os.getenv('GPT41_ENABLE_FALLBACK'):
            self.feature_flags.enable_auto_fallback = os.getenv('GPT41_ENABLE_FALLBACK', 'true').lower() == 'true'

        # Model config from env
        if os.getenv('GPT41_PRIMARY_MODEL'):
            self.config.primary_model = os.getenv('GPT41_PRIMARY_MODEL', 'gpt-4.1')

    def _load_from_redis(self):
        """Load configuration from Redis"""
        if not self.redis_client:
            return

        try:
            # Load feature flags
            flags_json = self.redis_client.get('gpt41:feature_flags')
            if flags_json:
                flags_dict = json.loads(flags_json)
                for key, value in flags_dict.items():
                    if hasattr(self.feature_flags, key):
                        setattr(self.feature_flags, key, value)

            # Load rollout percentage
            rollout = self.redis_client.get('gpt41:rollout_percentage')
            if rollout:
                self.feature_flags.rollout_percentage = float(rollout)

        except Exception as e:
            print(f"Error loading from Redis: {e}")

    def save_to_redis(self):
        """Save current configuration to Redis"""
        if not self.redis_client:
            return

        try:
            # Save feature flags
            flags_dict = asdict(self.feature_flags)
            self.redis_client.set('gpt41:feature_flags', json.dumps(flags_dict))

            # Save rollout percentage separately for easy access
            self.redis_client.set('gpt41:rollout_percentage', str(self.feature_flags.rollout_percentage))

            # Save config
            config_dict = asdict(self.config)
            self.redis_client.set('gpt41:model_config', json.dumps(config_dict))

        except Exception as e:
            print(f"Error saving to Redis: {e}")

    def get_current_phase(self) -> MigrationPhase:
        """Get current migration phase based on date and rollout percentage"""
        now = datetime.now()
        current_phase = MigrationPhase.TESTING

        for schedule in MIGRATION_SCHEDULE:
            schedule_date = datetime.strptime(schedule.start_date, "%Y-%m-%d")
            if now >= schedule_date and self.feature_flags.rollout_percentage >= schedule.target_percentage:
                current_phase = schedule.phase
            else:
                break

        return current_phase

    def should_use_gpt41(self, user_id: Optional[str] = None) -> bool:
        """Determine if a request should use GPT-4.1"""
        if not self.feature_flags.enable_gpt41:
            return False

        if self.feature_flags.rollout_percentage >= 100:
            return True

        if self.feature_flags.rollout_percentage <= 0:
            return False

        # Use user_id for consistent hashing if provided
        if user_id:
            import hashlib
            hash_val = int(hashlib.md5(user_id.encode()).hexdigest()[:8], 16)
            return (hash_val % 100) < self.feature_flags.rollout_percentage

        # Random selection otherwise
        import random
        return random.random() * 100 < self.feature_flags.rollout_percentage

    def get_model_for_complexity(self, complexity: float) -> str:
        """Select appropriate model variant based on complexity"""
        if not self.feature_flags.enable_auto_model_selection:
            return self.config.primary_model

        if complexity < self.config.nano_complexity_threshold and self.feature_flags.enable_nano_for_simple:
            return self.config.nano_model
        elif complexity < self.config.mini_complexity_threshold and self.feature_flags.enable_mini_for_standard:
            return self.config.mini_model
        else:
            return self.config.primary_model

    def update_rollout_percentage(self, percentage: float):
        """Update rollout percentage"""
        if not 0 <= percentage <= 100:
            raise ValueError(f"Percentage must be 0-100, got {percentage}")

        old = self.feature_flags.rollout_percentage
        self.feature_flags.rollout_percentage = percentage
        self.save_to_redis()

        print(f"Rollout percentage updated: {old}% -> {percentage}%")

    def enable_phase(self, phase: MigrationPhase):
        """Enable a specific migration phase"""
        for schedule in MIGRATION_SCHEDULE:
            if schedule.phase == phase:
                self.feature_flags.enable_gpt41 = True
                self.feature_flags.rollout_percentage = schedule.target_percentage
                self.save_to_redis()
                print(f"Enabled phase {phase.value} with {schedule.target_percentage}% rollout")
                return

        raise ValueError(f"Unknown phase: {phase}")

    def get_deprecation_status(self) -> Dict[str, Any]:
        """Get deprecation status for GPT-4.5 Preview"""
        deprecation_date = datetime.strptime(self.config.deprecation_date, "%Y-%m-%d")
        now = datetime.now()
        days_remaining = (deprecation_date - now).days

        status = {
            "model": "gpt-4.5-preview",
            "deprecation_date": self.config.deprecation_date,
            "days_remaining": days_remaining,
            "is_deprecated": days_remaining <= 0,
            "is_critical": days_remaining <= 30,
            "is_warning": days_remaining <= 90,
            "migration_progress": {
                "current_phase": self.get_current_phase().value,
                "rollout_percentage": self.feature_flags.rollout_percentage,
                "target_date": self.config.rollout_target_date
            }
        }

        if status["is_deprecated"]:
            status["severity"] = "CRITICAL - Model is deprecated"
        elif status["is_critical"]:
            status["severity"] = "CRITICAL - Deprecation imminent"
        elif status["is_warning"]:
            status["severity"] = "WARNING - Plan migration"
        else:
            status["severity"] = "INFO"

        return status

    def get_cost_comparison(self, input_tokens: int, output_tokens: int) -> Dict[str, Any]:
        """Compare costs between GPT-4.5 and GPT-4.1 variants"""
        # GPT-4.5 costs (for comparison)
        gpt45_input_cost = 10.0  # per 1M tokens
        gpt45_output_cost = 30.0

        gpt45_total = (input_tokens / 1_000_000 * gpt45_input_cost) + (output_tokens / 1_000_000 * gpt45_output_cost)
        gpt41_total = (input_tokens / 1_000_000 * self.config.cost_input_gpt41) + (output_tokens / 1_000_000 * self.config.cost_output_gpt41)
        mini_total = (input_tokens / 1_000_000 * self.config.cost_input_mini) + (output_tokens / 1_000_000 * self.config.cost_output_mini)
        nano_total = (input_tokens / 1_000_000 * self.config.cost_input_nano) + (output_tokens / 1_000_000 * self.config.cost_output_nano)

        return {
            "tokens": {
                "input": input_tokens,
                "output": output_tokens
            },
            "costs": {
                "gpt-4.5-preview": round(gpt45_total, 4),
                "gpt-4.1": round(gpt41_total, 4),
                "gpt-4.1-mini": round(mini_total, 4),
                "gpt-4.1-nano": round(nano_total, 4)
            },
            "savings": {
                "gpt-4.1": round(gpt45_total - gpt41_total, 4),
                "gpt-4.1-mini": round(gpt45_total - mini_total, 4),
                "gpt-4.1-nano": round(gpt45_total - nano_total, 4)
            },
            "savings_percentage": {
                "gpt-4.1": round((gpt45_total - gpt41_total) / gpt45_total * 100, 1),
                "gpt-4.1-mini": round((gpt45_total - mini_total) / gpt45_total * 100, 1),
                "gpt-4.1-nano": round((gpt45_total - nano_total) / gpt45_total * 100, 1)
            }
        }

# Singleton instance
_config_manager: Optional[GPT41ConfigManager] = None

def get_gpt41_config() -> GPT41ConfigManager:
    """Get or create GPT-4.1 config manager singleton"""
    global _config_manager
    if _config_manager is None:
        _config_manager = GPT41ConfigManager()
    return _config_manager
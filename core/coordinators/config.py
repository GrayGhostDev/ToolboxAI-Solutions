"""
Coordinator System Configuration

Centralized configuration management for all coordinator components
in the ToolboxAI Roblox Environment.
"""

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional

import yaml


@dataclass
class MainCoordinatorConfig:
    """Configuration for Main Coordinator"""

    max_concurrent_requests: int = 10
    health_check_interval: int = 30
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600
    metrics_collection_interval: int = 60


@dataclass
class WorkflowCoordinatorConfig:
    """Configuration for Workflow Coordinator"""

    max_concurrent_workflows: int = 5
    default_step_timeout: int = 300
    enable_workflow_optimization: bool = True
    optimization_interval: int = 3600
    workflow_history_limit: int = 1000


@dataclass
class ResourceCoordinatorConfig:
    """Configuration for Resource Coordinator"""

    max_cpu_allocation: float = 0.8
    max_memory_allocation: float = 0.7
    reserve_cpu_cores: int = 1
    reserve_memory_mb: int = 1024
    enable_cost_tracking: bool = True
    daily_budget: float = 50.0
    cost_per_api_call: float = 0.002
    cost_per_1k_tokens: float = 0.02

    # API Quotas
    openai_requests_per_minute: int = 60
    openai_tokens_per_minute: int = 150000
    schoology_requests_per_minute: int = 30
    canvas_requests_per_minute: int = 60
    roblox_requests_per_minute: int = 30


@dataclass
class SyncCoordinatorConfig:
    """Configuration for Sync Coordinator"""

    event_buffer_size: int = 10000
    state_history_size: int = 100
    sync_interval: int = 5
    enable_conflict_resolution: bool = True
    default_conflict_strategy: str = "timestamp_wins"
    websocket_timeout: int = 300


@dataclass
class ErrorCoordinatorConfig:
    """Configuration for Error Coordinator"""

    max_error_history: int = 10000
    enable_auto_recovery: bool = True
    enable_notifications: bool = True
    notification_cooldown: int = 300

    # Email configuration
    smtp_server: str = "localhost"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    alert_email: Optional[str] = None

    # Recovery strategies
    max_recovery_attempts: int = 3
    recovery_timeout: int = 300
    escalation_threshold_minutes: int = 30


@dataclass
class CoordinatorSystemConfig:
    """Complete coordinator system configuration"""

    main: MainCoordinatorConfig = None
    workflow: WorkflowCoordinatorConfig = None
    resource: ResourceCoordinatorConfig = None
    sync: SyncCoordinatorConfig = None
    error: ErrorCoordinatorConfig = None

    # Global settings
    environment: str = "development"  # development, staging, production
    log_level: str = "INFO"
    enable_metrics: bool = True
    enable_health_monitoring: bool = True

    def __post_init__(self):
        if self.main is None:
            self.main = MainCoordinatorConfig()
        if self.workflow is None:
            self.workflow = WorkflowCoordinatorConfig()
        if self.resource is None:
            self.resource = ResourceCoordinatorConfig()
        if self.sync is None:
            self.sync = SyncCoordinatorConfig()
        if self.error is None:
            self.error = ErrorCoordinatorConfig()

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "main": asdict(self.main),
            "workflow": asdict(self.workflow),
            "resource": asdict(self.resource),
            "sync": asdict(self.sync),
            "error": asdict(self.error),
            "environment": self.environment,
            "log_level": self.log_level,
            "enable_metrics": self.enable_metrics,
            "enable_health_monitoring": self.enable_health_monitoring,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CoordinatorSystemConfig":
        """Create configuration from dictionary"""
        config = cls(
            environment=data.get("environment", "development"),
            log_level=data.get("log_level", "INFO"),
            enable_metrics=data.get("enable_metrics", True),
            enable_health_monitoring=data.get("enable_health_monitoring", True),
        )

        if "main" in data:
            config.main = MainCoordinatorConfig(**data["main"])
        if "workflow" in data:
            config.workflow = WorkflowCoordinatorConfig(**data["workflow"])
        if "resource" in data:
            config.resource = ResourceCoordinatorConfig(**data["resource"])
        if "sync" in data:
            config.sync = SyncCoordinatorConfig(**data["sync"])
        if "error" in data:
            config.error = ErrorCoordinatorConfig(**data["error"])

        return config


class ConfigurationManager:
    """Configuration manager for coordinator system"""

    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir or os.path.dirname(__file__))
        self.config_file = self.config_dir / "coordinator_config.yaml"
        self.env_config_file = (
            self.config_dir / f"coordinator_config_{os.getenv('ENVIRONMENT', 'development')}.yaml"
        )

        self._config: Optional[CoordinatorSystemConfig] = None

    def load_config(self) -> CoordinatorSystemConfig:
        """Load configuration from files and environment"""

        # Start with default configuration
        config_data = {}

        # Load base configuration file
        if self.config_file.exists():
            with open(self.config_file) as f:
                config_data.update(yaml.safe_load(f) or {})

        # Load environment-specific configuration
        if self.env_config_file.exists():
            with open(self.env_config_file) as f:
                env_config = yaml.safe_load(f) or {}
                self._deep_merge(config_data, env_config)

        # Override with environment variables
        env_overrides = self._load_env_overrides()
        self._deep_merge(config_data, env_overrides)

        # Create configuration object
        self._config = CoordinatorSystemConfig.from_dict(config_data)

        return self._config

    def _load_env_overrides(self) -> dict[str, Any]:
        """Load configuration overrides from environment variables"""
        overrides = {}

        # Main coordinator overrides
        if os.getenv("COORDINATOR_MAX_CONCURRENT_REQUESTS"):
            overrides.setdefault("main", {})["max_concurrent_requests"] = int(
                os.getenv("COORDINATOR_MAX_CONCURRENT_REQUESTS")
            )

        if os.getenv("COORDINATOR_ENABLE_CACHING"):
            overrides.setdefault("main", {})["enable_caching"] = (
                os.getenv("COORDINATOR_ENABLE_CACHING").lower() == "true"
            )

        # Resource coordinator overrides
        if os.getenv("COORDINATOR_DAILY_BUDGET"):
            overrides.setdefault("resource", {})["daily_budget"] = float(
                os.getenv("COORDINATOR_DAILY_BUDGET")
            )

        if os.getenv("COORDINATOR_MAX_CPU_ALLOCATION"):
            overrides.setdefault("resource", {})["max_cpu_allocation"] = float(
                os.getenv("COORDINATOR_MAX_CPU_ALLOCATION")
            )

        # Error coordinator overrides
        if os.getenv("COORDINATOR_ALERT_EMAIL"):
            overrides.setdefault("error", {})["alert_email"] = os.getenv("COORDINATOR_ALERT_EMAIL")

        if os.getenv("COORDINATOR_SMTP_SERVER"):
            overrides.setdefault("error", {})["smtp_server"] = os.getenv("COORDINATOR_SMTP_SERVER")

        if os.getenv("COORDINATOR_SMTP_USERNAME"):
            overrides.setdefault("error", {})["smtp_username"] = os.getenv(
                "COORDINATOR_SMTP_USERNAME"
            )

        if os.getenv("COORDINATOR_SMTP_PASSWORD"):
            overrides.setdefault("error", {})["smtp_password"] = os.getenv(
                "COORDINATOR_SMTP_PASSWORD"
            )

        # Global overrides
        if os.getenv("COORDINATOR_LOG_LEVEL"):
            overrides["log_level"] = os.getenv("COORDINATOR_LOG_LEVEL")

        if os.getenv("COORDINATOR_ENVIRONMENT"):
            overrides["environment"] = os.getenv("COORDINATOR_ENVIRONMENT")

        return overrides

    def _deep_merge(self, base: dict[str, Any], override: dict[str, Any]):
        """Deep merge configuration dictionaries"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def save_config(self, config: CoordinatorSystemConfig, environment: Optional[str] = None):
        """Save configuration to file"""
        config_data = config.to_dict()

        if environment:
            config_file = self.config_dir / f"coordinator_config_{environment}.yaml"
        else:
            config_file = self.config_file

        # Ensure directory exists
        config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(config_file, "w") as f:
            yaml.dump(config_data, f, default_flow_style=False, indent=2)

        logger.info(f"Configuration saved to {config_file}")

    def get_config(self) -> CoordinatorSystemConfig:
        """Get current configuration"""
        if self._config is None:
            self._config = self.load_config()
        return self._config

    def reload_config(self) -> CoordinatorSystemConfig:
        """Reload configuration from files"""
        self._config = None
        return self.load_config()


# Pre-defined configurations for different environments


def get_development_config() -> CoordinatorSystemConfig:
    """Get development environment configuration"""
    return CoordinatorSystemConfig(
        main=MainCoordinatorConfig(
            max_concurrent_requests=5, enable_caching=True, health_check_interval=30
        ),
        workflow=WorkflowCoordinatorConfig(
            max_concurrent_workflows=3, enable_workflow_optimization=True
        ),
        resource=ResourceCoordinatorConfig(
            max_cpu_allocation=0.6,  # Conservative for development
            max_memory_allocation=0.6,
            enable_cost_tracking=False,
            daily_budget=10.0,
        ),
        sync=SyncCoordinatorConfig(
            enable_conflict_resolution=True,
            sync_interval=10,  # More frequent syncing for development
        ),
        error=ErrorCoordinatorConfig(
            enable_auto_recovery=True,
            enable_notifications=False,  # Disable email notifications for dev
            max_error_history=5000,
        ),
        environment="development",
        log_level="DEBUG",
    )


def get_production_config() -> CoordinatorSystemConfig:
    """Get production environment configuration"""
    return CoordinatorSystemConfig(
        main=MainCoordinatorConfig(
            max_concurrent_requests=20, enable_caching=True, health_check_interval=15
        ),
        workflow=WorkflowCoordinatorConfig(
            max_concurrent_workflows=10,
            enable_workflow_optimization=True,
            optimization_interval=1800,  # More frequent optimization
        ),
        resource=ResourceCoordinatorConfig(
            max_cpu_allocation=0.8,
            max_memory_allocation=0.7,
            enable_cost_tracking=True,
            daily_budget=200.0,  # Higher budget for production
            openai_requests_per_minute=180,  # Higher limits
            openai_tokens_per_minute=500000,
        ),
        sync=SyncCoordinatorConfig(
            enable_conflict_resolution=True,
            sync_interval=5,
            event_buffer_size=50000,  # Larger buffer for production
        ),
        error=ErrorCoordinatorConfig(
            enable_auto_recovery=True,
            enable_notifications=True,
            max_error_history=50000,
            escalation_threshold_minutes=15,  # Faster escalation
        ),
        environment="production",
        log_level="INFO",
    )


def get_testing_config() -> CoordinatorSystemConfig:
    """Get testing environment configuration"""
    return CoordinatorSystemConfig(
        main=MainCoordinatorConfig(
            max_concurrent_requests=2,
            enable_caching=False,  # Disable caching for testing
            health_check_interval=60,
        ),
        workflow=WorkflowCoordinatorConfig(
            max_concurrent_workflows=1,
            enable_workflow_optimization=False,
            default_step_timeout=60,  # Shorter timeouts for testing
        ),
        resource=ResourceCoordinatorConfig(
            max_cpu_allocation=0.5,
            max_memory_allocation=0.5,
            enable_cost_tracking=False,
            daily_budget=5.0,
        ),
        sync=SyncCoordinatorConfig(
            enable_conflict_resolution=True,
            sync_interval=2,  # Very frequent for testing
            event_buffer_size=1000,
        ),
        error=ErrorCoordinatorConfig(
            enable_auto_recovery=True,
            enable_notifications=False,
            max_error_history=1000,
            max_recovery_attempts=1,  # Quick failure for testing
        ),
        environment="testing",
        log_level="DEBUG",
    )


# Configuration factory
def create_config(environment: str = None) -> CoordinatorSystemConfig:
    """
    Create configuration for specified environment

    Args:
        environment: Target environment (development, production, testing)

    Returns:
        CoordinatorSystemConfig instance
    """
    env = environment or os.getenv("ENVIRONMENT", "development")

    if env == "production":
        return get_production_config()
    elif env == "testing":
        return get_testing_config()
    else:
        return get_development_config()


# Default configuration templates
DEFAULT_CONFIG_YAML = """
# ToolboxAI Coordinator System Configuration

environment: development
log_level: INFO
enable_metrics: true
enable_health_monitoring: true

main:
  max_concurrent_requests: 10
  health_check_interval: 30
  enable_caching: true
  cache_ttl_seconds: 3600
  metrics_collection_interval: 60

workflow:
  max_concurrent_workflows: 5
  default_step_timeout: 300
  enable_workflow_optimization: true
  optimization_interval: 3600
  workflow_history_limit: 1000

resource:
  max_cpu_allocation: 0.8
  max_memory_allocation: 0.7
  reserve_cpu_cores: 1
  reserve_memory_mb: 1024
  enable_cost_tracking: true
  daily_budget: 50.0
  cost_per_api_call: 0.002
  cost_per_1k_tokens: 0.02

  # API Quotas
  openai_requests_per_minute: 60
  openai_tokens_per_minute: 150000
  schoology_requests_per_minute: 30
  canvas_requests_per_minute: 60
  roblox_requests_per_minute: 30

sync:
  event_buffer_size: 10000
  state_history_size: 100
  sync_interval: 5
  enable_conflict_resolution: true
  default_conflict_strategy: "timestamp_wins"
  websocket_timeout: 300

error:
  max_error_history: 10000
  enable_auto_recovery: true
  enable_notifications: true
  notification_cooldown: 300

  # Email configuration (set via environment variables)
  smtp_server: "localhost"
  smtp_port: 587

  # Recovery settings
  max_recovery_attempts: 3
  recovery_timeout: 300
  escalation_threshold_minutes: 30
"""


def create_default_config_file(config_dir: str = None):
    """Create default configuration file"""
    if config_dir is None:
        config_dir = os.path.dirname(__file__)

    config_path = Path(config_dir) / "coordinator_config.yaml"

    if not config_path.exists():
        with open(config_path, "w") as f:
            f.write(DEFAULT_CONFIG_YAML)

        print(f"Created default configuration file: {config_path}")
    else:
        print(f"Configuration file already exists: {config_path}")


def validate_config(config: CoordinatorSystemConfig) -> list[str]:
    """
    Validate configuration and return list of issues

    Args:
        config: Configuration to validate

    Returns:
        List of validation issues (empty if valid)
    """
    issues = []

    # Validate main coordinator config
    if config.main.max_concurrent_requests <= 0:
        issues.append("main.max_concurrent_requests must be > 0")

    if config.main.health_check_interval <= 0:
        issues.append("main.health_check_interval must be > 0")

    # Validate resource coordinator config
    if not 0 < config.resource.max_cpu_allocation <= 1:
        issues.append("resource.max_cpu_allocation must be between 0 and 1")

    if not 0 < config.resource.max_memory_allocation <= 1:
        issues.append("resource.max_memory_allocation must be between 0 and 1")

    if config.resource.daily_budget <= 0:
        issues.append("resource.daily_budget must be > 0")

    # Validate sync coordinator config
    if config.sync.event_buffer_size <= 0:
        issues.append("sync.event_buffer_size must be > 0")

    if config.sync.sync_interval <= 0:
        issues.append("sync.sync_interval must be > 0")

    # Validate error coordinator config
    if config.error.max_error_history <= 0:
        issues.append("error.max_error_history must be > 0")

    if config.error.notification_cooldown < 0:
        issues.append("error.notification_cooldown must be >= 0")

    # Environment validation
    if config.environment not in ["development", "staging", "production", "testing"]:
        issues.append("environment must be one of: development, staging, production, testing")

    return issues


def setup_logging(config: CoordinatorSystemConfig):
    """Setup logging based on configuration"""
    import logging

    log_level = getattr(logging, config.log_level.upper(), logging.INFO)

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Set specific logger levels for coordinator components
    coordinator_loggers = [
        "coordinators.main_coordinator",
        "coordinators.workflow_coordinator",
        "coordinators.resource_coordinator",
        "coordinators.sync_coordinator",
        "coordinators.error_coordinator",
    ]

    for logger_name in coordinator_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)

    # Reduce noise from external libraries in production
    if config.environment == "production":
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_config_for_environment(environment: str = None) -> dict[str, Any]:
    """
    Get configuration dictionary for specific environment

    Args:
        environment: Target environment name

    Returns:
        Configuration dictionary suitable for coordinator initialization
    """
    config = create_config(environment)

    # Validate configuration
    issues = validate_config(config)
    if issues:
        raise ValueError(f"Configuration validation failed: {issues}")

    # Setup logging
    setup_logging(config)

    return config.to_dict()


# Educational-specific configuration presets
def get_elementary_school_config() -> dict[str, Any]:
    """Get configuration optimized for elementary school usage"""
    config = get_development_config()

    # Adjust for younger students - simpler content, lower resource usage
    config.main.max_concurrent_requests = 3
    config.workflow.max_concurrent_workflows = 2
    config.resource.max_cpu_allocation = 0.5
    config.resource.daily_budget = 20.0

    return config.to_dict()


def get_high_school_config() -> dict[str, Any]:
    """Get configuration optimized for high school usage"""
    config = get_development_config()

    # Adjust for older students - more complex content, higher resource usage
    config.main.max_concurrent_requests = 8
    config.workflow.max_concurrent_workflows = 4
    config.resource.max_cpu_allocation = 0.7
    config.resource.daily_budget = 40.0

    return config.to_dict()


def get_university_config() -> dict[str, Any]:
    """Get configuration optimized for university usage"""
    config = get_production_config()

    # Adjust for advanced content and research
    config.main.max_concurrent_requests = 15
    config.workflow.max_concurrent_workflows = 8
    config.resource.daily_budget = 100.0

    return config.to_dict()


# Configuration utilities
def export_config_template(file_path: str, environment: str = "development"):
    """Export configuration template to file"""
    config = create_config(environment)

    with open(file_path, "w") as f:
        yaml.dump(config.to_dict(), f, default_flow_style=False, indent=2)

    print(f"Configuration template exported to: {file_path}")


def import_config_from_file(file_path: str) -> CoordinatorSystemConfig:
    """Import configuration from file"""
    with open(file_path) as f:
        if file_path.endswith(".json"):
            config_data = json.load(f)
        else:
            config_data = yaml.safe_load(f)

    return CoordinatorSystemConfig.from_dict(config_data)


# Example usage
if __name__ == "__main__":
    # Create configuration manager
    config_manager = ConfigurationManager()

    # Create default config file if it doesn't exist
    create_default_config_file()

    # Load and validate configuration
    config = config_manager.load_config()

    issues = validate_config(config)
    if issues:
        print(f"Configuration issues found: {issues}")
    else:
        print("Configuration is valid")

    # Setup logging
    setup_logging(config)

    # Example: Export different environment configs
    export_config_template("coordinator_config_dev.yaml", "development")
    export_config_template("coordinator_config_prod.yaml", "production")

    print("Configuration setup complete")

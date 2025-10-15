"""
Comprehensive unit tests for core/coordinators/config.py

Tests cover:
- Configuration dataclasses (5 different configs + system config)
- Configuration serialization (to_dict/from_dict)
- ConfigurationManager (file loading, env overrides, deep merge)
- Environment-specific configurations (dev, prod, testing)
- Educational presets (elementary, high school, university)
- Configuration validation
- Logging setup
- File import/export utilities
- Edge cases and error handling
"""

import os
import json
import yaml
import logging
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import pytest

# Import the module under test
from core.coordinators.config import (
    MainCoordinatorConfig,
    WorkflowCoordinatorConfig,
    ResourceCoordinatorConfig,
    SyncCoordinatorConfig,
    ErrorCoordinatorConfig,
    CoordinatorSystemConfig,
    ConfigurationManager,
    get_development_config,
    get_production_config,
    get_testing_config,
    create_config,
    create_default_config_file,
    validate_config,
    setup_logging,
    get_config_for_environment,
    get_elementary_school_config,
    get_high_school_config,
    get_university_config,
    export_config_template,
    import_config_from_file,
    DEFAULT_CONFIG_YAML
)


# ============================================================================
# Test MainCoordinatorConfig Dataclass
# ============================================================================

class TestMainCoordinatorConfig:
    """Test MainCoordinatorConfig dataclass"""

    def test_default_initialization(self):
        """Test default initialization values"""
        config = MainCoordinatorConfig()

        assert config.max_concurrent_requests == 10
        assert config.health_check_interval == 30
        assert config.enable_caching is True
        assert config.cache_ttl_seconds == 3600
        assert config.metrics_collection_interval == 60

    def test_custom_initialization(self):
        """Test initialization with custom values"""
        config = MainCoordinatorConfig(
            max_concurrent_requests=20,
            health_check_interval=15,
            enable_caching=False,
            cache_ttl_seconds=1800,
            metrics_collection_interval=30
        )

        assert config.max_concurrent_requests == 20
        assert config.health_check_interval == 15
        assert config.enable_caching is False
        assert config.cache_ttl_seconds == 1800
        assert config.metrics_collection_interval == 30

    def test_as_dict_conversion(self):
        """Test conversion to dictionary via asdict"""
        from dataclasses import asdict

        config = MainCoordinatorConfig()
        config_dict = asdict(config)

        assert isinstance(config_dict, dict)
        assert config_dict['max_concurrent_requests'] == 10
        assert config_dict['health_check_interval'] == 30


# ============================================================================
# Test WorkflowCoordinatorConfig Dataclass
# ============================================================================

class TestWorkflowCoordinatorConfig:
    """Test WorkflowCoordinatorConfig dataclass"""

    def test_default_initialization(self):
        """Test default initialization values"""
        config = WorkflowCoordinatorConfig()

        assert config.max_concurrent_workflows == 5
        assert config.default_step_timeout == 300
        assert config.enable_workflow_optimization is True
        assert config.optimization_interval == 3600
        assert config.workflow_history_limit == 1000

    def test_custom_initialization(self):
        """Test initialization with custom values"""
        config = WorkflowCoordinatorConfig(
            max_concurrent_workflows=10,
            default_step_timeout=600,
            enable_workflow_optimization=False
        )

        assert config.max_concurrent_workflows == 10
        assert config.default_step_timeout == 600
        assert config.enable_workflow_optimization is False


# ============================================================================
# Test ResourceCoordinatorConfig Dataclass
# ============================================================================

class TestResourceCoordinatorConfig:
    """Test ResourceCoordinatorConfig dataclass"""

    def test_default_initialization(self):
        """Test default initialization values"""
        config = ResourceCoordinatorConfig()

        assert config.max_cpu_allocation == 0.8
        assert config.max_memory_allocation == 0.7
        assert config.reserve_cpu_cores == 1
        assert config.reserve_memory_mb == 1024
        assert config.enable_cost_tracking is True
        assert config.daily_budget == 50.0
        assert config.cost_per_api_call == 0.002
        assert config.cost_per_1k_tokens == 0.02

    def test_api_quota_defaults(self):
        """Test API quota default values"""
        config = ResourceCoordinatorConfig()

        assert config.openai_requests_per_minute == 60
        assert config.openai_tokens_per_minute == 150000
        assert config.schoology_requests_per_minute == 30
        assert config.canvas_requests_per_minute == 60
        assert config.roblox_requests_per_minute == 30

    def test_custom_cost_settings(self):
        """Test custom cost settings"""
        config = ResourceCoordinatorConfig(
            daily_budget=100.0,
            cost_per_api_call=0.005,
            cost_per_1k_tokens=0.05
        )

        assert config.daily_budget == 100.0
        assert config.cost_per_api_call == 0.005
        assert config.cost_per_1k_tokens == 0.05


# ============================================================================
# Test SyncCoordinatorConfig Dataclass
# ============================================================================

class TestSyncCoordinatorConfig:
    """Test SyncCoordinatorConfig dataclass"""

    def test_default_initialization(self):
        """Test default initialization values"""
        config = SyncCoordinatorConfig()

        assert config.event_buffer_size == 10000
        assert config.state_history_size == 100
        assert config.sync_interval == 5
        assert config.enable_conflict_resolution is True
        assert config.default_conflict_strategy == "timestamp_wins"
        assert config.websocket_timeout == 300

    def test_conflict_resolution_settings(self):
        """Test conflict resolution settings"""
        config = SyncCoordinatorConfig(
            enable_conflict_resolution=False,
            default_conflict_strategy="version_wins"
        )

        assert config.enable_conflict_resolution is False
        assert config.default_conflict_strategy == "version_wins"


# ============================================================================
# Test ErrorCoordinatorConfig Dataclass
# ============================================================================

class TestErrorCoordinatorConfig:
    """Test ErrorCoordinatorConfig dataclass"""

    def test_default_initialization(self):
        """Test default initialization values"""
        config = ErrorCoordinatorConfig()

        assert config.max_error_history == 10000
        assert config.enable_auto_recovery is True
        assert config.enable_notifications is True
        assert config.notification_cooldown == 300

    def test_email_configuration(self):
        """Test email configuration defaults"""
        config = ErrorCoordinatorConfig()

        assert config.smtp_server == "localhost"
        assert config.smtp_port == 587
        assert config.smtp_username is None
        assert config.smtp_password is None
        assert config.alert_email is None

    def test_recovery_settings(self):
        """Test recovery settings"""
        config = ErrorCoordinatorConfig()

        assert config.max_recovery_attempts == 3
        assert config.recovery_timeout == 300
        assert config.escalation_threshold_minutes == 30

    def test_custom_email_settings(self):
        """Test custom email settings"""
        config = ErrorCoordinatorConfig(
            smtp_server="smtp.example.com",
            smtp_port=465,
            smtp_username="user@example.com",
            smtp_password="password",
            alert_email="admin@example.com"
        )

        assert config.smtp_server == "smtp.example.com"
        assert config.smtp_port == 465
        assert config.smtp_username == "user@example.com"


# ============================================================================
# Test CoordinatorSystemConfig Dataclass
# ============================================================================

class TestCoordinatorSystemConfig:
    """Test CoordinatorSystemConfig dataclass"""

    def test_default_initialization(self):
        """Test default initialization creates sub-configs"""
        config = CoordinatorSystemConfig()

        assert isinstance(config.main, MainCoordinatorConfig)
        assert isinstance(config.workflow, WorkflowCoordinatorConfig)
        assert isinstance(config.resource, ResourceCoordinatorConfig)
        assert isinstance(config.sync, SyncCoordinatorConfig)
        assert isinstance(config.error, ErrorCoordinatorConfig)

    def test_global_settings_defaults(self):
        """Test global settings defaults"""
        config = CoordinatorSystemConfig()

        assert config.environment == "development"
        assert config.log_level == "INFO"
        assert config.enable_metrics is True
        assert config.enable_health_monitoring is True

    def test_custom_initialization(self):
        """Test initialization with custom sub-configs"""
        main_config = MainCoordinatorConfig(max_concurrent_requests=20)
        config = CoordinatorSystemConfig(main=main_config)

        assert config.main.max_concurrent_requests == 20

    def test_to_dict_conversion(self):
        """Test conversion to dictionary"""
        config = CoordinatorSystemConfig()
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert 'main' in config_dict
        assert 'workflow' in config_dict
        assert 'resource' in config_dict
        assert 'sync' in config_dict
        assert 'error' in config_dict
        assert config_dict['environment'] == "development"

    def test_from_dict_conversion(self):
        """Test creation from dictionary"""
        data = {
            'environment': 'production',
            'log_level': 'DEBUG',
            'enable_metrics': False,
            'main': {
                'max_concurrent_requests': 15
            }
        }

        config = CoordinatorSystemConfig.from_dict(data)

        assert config.environment == 'production'
        assert config.log_level == 'DEBUG'
        assert config.enable_metrics is False
        assert config.main.max_concurrent_requests == 15

    def test_from_dict_with_all_sub_configs(self):
        """Test from_dict with all sub-configurations"""
        data = {
            'environment': 'testing',
            'main': {'max_concurrent_requests': 5},
            'workflow': {'max_concurrent_workflows': 2},
            'resource': {'daily_budget': 10.0},
            'sync': {'sync_interval': 10},
            'error': {'max_error_history': 5000}
        }

        config = CoordinatorSystemConfig.from_dict(data)

        assert config.main.max_concurrent_requests == 5
        assert config.workflow.max_concurrent_workflows == 2
        assert config.resource.daily_budget == 10.0
        assert config.sync.sync_interval == 10
        assert config.error.max_error_history == 5000


# ============================================================================
# Test ConfigurationManager Initialization
# ============================================================================

class TestConfigurationManagerInitialization:
    """Test ConfigurationManager initialization"""

    def test_initialization_with_default_dir(self):
        """Test initialization with default directory"""
        manager = ConfigurationManager()

        assert isinstance(manager.config_dir, Path)
        assert manager.config_file.name == "coordinator_config.yaml"
        assert manager._config is None

    def test_initialization_with_custom_dir(self):
        """Test initialization with custom directory"""
        manager = ConfigurationManager(config_dir="/custom/path")

        assert str(manager.config_dir) == "/custom/path"
        assert manager.config_file == Path("/custom/path/coordinator_config.yaml")

    def test_environment_specific_config_file(self):
        """Test environment-specific config file path"""
        with patch.dict(os.environ, {'ENVIRONMENT': 'production'}):
            manager = ConfigurationManager()

            assert 'production' in str(manager.env_config_file)


# ============================================================================
# Test ConfigurationManager Load Configuration
# ============================================================================

class TestConfigurationManagerLoadConfig:
    """Test configuration loading"""

    def test_load_config_default_when_no_files(self):
        """Test loading config when no files exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigurationManager(config_dir=tmpdir)

            config = manager.load_config()

            assert isinstance(config, CoordinatorSystemConfig)
            assert config.environment == "development"  # Default

    def test_load_config_from_base_file(self):
        """Test loading config from base file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "coordinator_config.yaml"

            config_data = {
                'environment': 'production',
                'log_level': 'WARNING',
                'main': {'max_concurrent_requests': 25}
            }

            with open(config_file, 'w') as f:
                yaml.dump(config_data, f)

            manager = ConfigurationManager(config_dir=tmpdir)
            config = manager.load_config()

            assert config.environment == 'production'
            assert config.log_level == 'WARNING'
            assert config.main.max_concurrent_requests == 25

    def test_load_config_with_environment_override(self):
        """Test environment-specific config overrides base config"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Base config
            base_file = Path(tmpdir) / "coordinator_config.yaml"
            with open(base_file, 'w') as f:
                yaml.dump({'main': {'max_concurrent_requests': 10}}, f)

            # Environment config
            with patch.dict(os.environ, {'ENVIRONMENT': 'testing'}):
                env_file = Path(tmpdir) / "coordinator_config_testing.yaml"
                with open(env_file, 'w') as f:
                    yaml.dump({'main': {'max_concurrent_requests': 2}}, f)

                manager = ConfigurationManager(config_dir=tmpdir)
                config = manager.load_config()

                # Environment config should override base
                assert config.main.max_concurrent_requests == 2

    def test_load_config_with_env_variable_overrides(self):
        """Test environment variables override file config"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "coordinator_config.yaml"
            with open(config_file, 'w') as f:
                yaml.dump({'main': {'max_concurrent_requests': 10}}, f)

            with patch.dict(os.environ, {'COORDINATOR_MAX_CONCURRENT_REQUESTS': '50'}):
                manager = ConfigurationManager(config_dir=tmpdir)
                config = manager.load_config()

                # Env variable should override file
                assert config.main.max_concurrent_requests == 50

    def test_load_config_deep_merge(self):
        """Test deep merge of configurations"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Base config
            base_file = Path(tmpdir) / "coordinator_config.yaml"
            with open(base_file, 'w') as f:
                yaml.dump({
                    'main': {
                        'max_concurrent_requests': 10,
                        'enable_caching': True
                    }
                }, f)

            # Environment config with partial override
            with patch.dict(os.environ, {'ENVIRONMENT': 'testing'}):
                env_file = Path(tmpdir) / "coordinator_config_testing.yaml"
                with open(env_file, 'w') as f:
                    yaml.dump({
                        'main': {
                            'max_concurrent_requests': 2
                            # enable_caching not specified, should keep base value
                        }
                    }, f)

                manager = ConfigurationManager(config_dir=tmpdir)
                config = manager.load_config()

                # Merged values
                assert config.main.max_concurrent_requests == 2  # Overridden
                assert config.main.enable_caching is True  # From base


# ============================================================================
# Test ConfigurationManager Environment Overrides
# ============================================================================

class TestConfigurationManagerEnvOverrides:
    """Test environment variable overrides"""

    def test_main_coordinator_overrides(self):
        """Test main coordinator env overrides"""
        with patch.dict(os.environ, {
            'COORDINATOR_MAX_CONCURRENT_REQUESTS': '100',
            'COORDINATOR_ENABLE_CACHING': 'false'
        }):
            with tempfile.TemporaryDirectory() as tmpdir:
                manager = ConfigurationManager(config_dir=tmpdir)
                config = manager.load_config()

                assert config.main.max_concurrent_requests == 100
                assert config.main.enable_caching is False

    def test_resource_coordinator_overrides(self):
        """Test resource coordinator env overrides"""
        with patch.dict(os.environ, {
            'COORDINATOR_DAILY_BUDGET': '150.0',
            'COORDINATOR_MAX_CPU_ALLOCATION': '0.9'
        }):
            with tempfile.TemporaryDirectory() as tmpdir:
                manager = ConfigurationManager(config_dir=tmpdir)
                config = manager.load_config()

                assert config.resource.daily_budget == 150.0
                assert config.resource.max_cpu_allocation == 0.9

    def test_error_coordinator_email_overrides(self):
        """Test error coordinator email overrides"""
        with patch.dict(os.environ, {
            'COORDINATOR_ALERT_EMAIL': 'admin@example.com',
            'COORDINATOR_SMTP_SERVER': 'smtp.example.com',
            'COORDINATOR_SMTP_USERNAME': 'user@example.com',
            'COORDINATOR_SMTP_PASSWORD': 'secret'
        }):
            with tempfile.TemporaryDirectory() as tmpdir:
                manager = ConfigurationManager(config_dir=tmpdir)
                config = manager.load_config()

                assert config.error.alert_email == 'admin@example.com'
                assert config.error.smtp_server == 'smtp.example.com'
                assert config.error.smtp_username == 'user@example.com'
                assert config.error.smtp_password == 'secret'

    def test_global_overrides(self):
        """Test global setting overrides"""
        with patch.dict(os.environ, {
            'COORDINATOR_LOG_LEVEL': 'DEBUG',
            'COORDINATOR_ENVIRONMENT': 'staging'
        }):
            with tempfile.TemporaryDirectory() as tmpdir:
                manager = ConfigurationManager(config_dir=tmpdir)
                config = manager.load_config()

                assert config.log_level == 'DEBUG'
                assert config.environment == 'staging'


# ============================================================================
# Test ConfigurationManager Save Configuration
# ============================================================================

class TestConfigurationManagerSaveConfig:
    """Test saving configuration"""

    def test_save_config_default_file(self):
        """Test saving config to default file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigurationManager(config_dir=tmpdir)
            config = CoordinatorSystemConfig(environment='testing')

            with patch('core.coordinators.config.logger'):
                manager.save_config(config)

            # Check file was created
            assert (Path(tmpdir) / "coordinator_config.yaml").exists()

    def test_save_config_environment_specific(self):
        """Test saving config to environment-specific file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigurationManager(config_dir=tmpdir)
            config = CoordinatorSystemConfig(environment='production')

            with patch('core.coordinators.config.logger'):
                manager.save_config(config, environment='production')

            # Check environment file was created
            assert (Path(tmpdir) / "coordinator_config_production.yaml").exists()

    def test_save_config_creates_directory(self):
        """Test save_config creates directory if needed"""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_dir = Path(tmpdir) / "nested" / "config"
            manager = ConfigurationManager(config_dir=str(nested_dir))
            config = CoordinatorSystemConfig()

            with patch('core.coordinators.config.logger'):
                manager.save_config(config)

            assert nested_dir.exists()
            assert (nested_dir / "coordinator_config.yaml").exists()


# ============================================================================
# Test ConfigurationManager Get/Reload Config
# ============================================================================

class TestConfigurationManagerGetReloadConfig:
    """Test getting and reloading configuration"""

    def test_get_config_loads_if_not_cached(self):
        """Test get_config loads if not already loaded"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigurationManager(config_dir=tmpdir)

            assert manager._config is None

            config = manager.get_config()

            assert manager._config is not None
            assert config == manager._config

    def test_get_config_returns_cached(self):
        """Test get_config returns cached config"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigurationManager(config_dir=tmpdir)

            config1 = manager.get_config()
            config2 = manager.get_config()

            # Should return same instance
            assert config1 is config2

    def test_reload_config_clears_cache(self):
        """Test reload_config clears cache and reloads"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigurationManager(config_dir=tmpdir)

            config1 = manager.get_config()
            config2 = manager.reload_config()

            # Should be different instances
            assert config1 is not config2


# ============================================================================
# Test Environment-Specific Configurations
# ============================================================================

class TestEnvironmentSpecificConfigurations:
    """Test environment-specific configuration functions"""

    def test_development_config(self):
        """Test development environment configuration"""
        config = get_development_config()

        assert config.environment == "development"
        assert config.log_level == "DEBUG"
        assert config.main.max_concurrent_requests == 5
        assert config.resource.enable_cost_tracking is False
        assert config.error.enable_notifications is False

    def test_production_config(self):
        """Test production environment configuration"""
        config = get_production_config()

        assert config.environment == "production"
        assert config.log_level == "INFO"
        assert config.main.max_concurrent_requests == 20
        assert config.resource.enable_cost_tracking is True
        assert config.error.enable_notifications is True
        assert config.resource.daily_budget == 200.0

    def test_testing_config(self):
        """Test testing environment configuration"""
        config = get_testing_config()

        assert config.environment == "testing"
        assert config.log_level == "DEBUG"
        assert config.main.max_concurrent_requests == 2
        assert config.main.enable_caching is False
        assert config.error.max_recovery_attempts == 1

    def test_create_config_factory_development(self):
        """Test create_config factory for development"""
        config = create_config('development')

        assert config.environment == "development"

    def test_create_config_factory_production(self):
        """Test create_config factory for production"""
        config = create_config('production')

        assert config.environment == "production"

    def test_create_config_factory_testing(self):
        """Test create_config factory for testing"""
        config = create_config('testing')

        assert config.environment == "testing"

    def test_create_config_default_environment(self):
        """Test create_config uses default when no environment specified"""
        config = create_config()

        assert config.environment == "development"

    def test_create_config_from_env_variable(self):
        """Test create_config reads from ENVIRONMENT variable"""
        with patch.dict(os.environ, {'ENVIRONMENT': 'production'}):
            config = create_config()

            assert config.environment == "production"


# ============================================================================
# Test Educational Presets
# ============================================================================

class TestEducationalPresets:
    """Test educational-specific configuration presets"""

    def test_elementary_school_config(self):
        """Test elementary school configuration"""
        config_dict = get_elementary_school_config()

        assert config_dict['main']['max_concurrent_requests'] == 3
        assert config_dict['workflow']['max_concurrent_workflows'] == 2
        assert config_dict['resource']['max_cpu_allocation'] == 0.5
        assert config_dict['resource']['daily_budget'] == 20.0

    def test_high_school_config(self):
        """Test high school configuration"""
        config_dict = get_high_school_config()

        assert config_dict['main']['max_concurrent_requests'] == 8
        assert config_dict['workflow']['max_concurrent_workflows'] == 4
        assert config_dict['resource']['max_cpu_allocation'] == 0.7
        assert config_dict['resource']['daily_budget'] == 40.0

    def test_university_config(self):
        """Test university configuration"""
        config_dict = get_university_config()

        assert config_dict['main']['max_concurrent_requests'] == 15
        assert config_dict['workflow']['max_concurrent_workflows'] == 8
        assert config_dict['resource']['daily_budget'] == 100.0
        assert config_dict['environment'] == "production"


# ============================================================================
# Test Configuration Validation
# ============================================================================

class TestConfigurationValidation:
    """Test configuration validation"""

    def test_validate_valid_config(self):
        """Test validation of valid configuration"""
        config = get_development_config()
        issues = validate_config(config)

        assert issues == []

    def test_validate_invalid_max_concurrent_requests(self):
        """Test validation catches invalid max_concurrent_requests"""
        config = CoordinatorSystemConfig()
        config.main.max_concurrent_requests = 0

        issues = validate_config(config)

        assert len(issues) > 0
        assert any("max_concurrent_requests" in issue for issue in issues)

    def test_validate_invalid_cpu_allocation(self):
        """Test validation catches invalid CPU allocation"""
        config = CoordinatorSystemConfig()
        config.resource.max_cpu_allocation = 1.5  # > 1

        issues = validate_config(config)

        assert len(issues) > 0
        assert any("max_cpu_allocation" in issue for issue in issues)

    def test_validate_invalid_memory_allocation(self):
        """Test validation catches invalid memory allocation"""
        config = CoordinatorSystemConfig()
        config.resource.max_memory_allocation = 0  # <= 0

        issues = validate_config(config)

        assert len(issues) > 0
        assert any("max_memory_allocation" in issue for issue in issues)

    def test_validate_invalid_daily_budget(self):
        """Test validation catches invalid daily budget"""
        config = CoordinatorSystemConfig()
        config.resource.daily_budget = -10

        issues = validate_config(config)

        assert len(issues) > 0
        assert any("daily_budget" in issue for issue in issues)

    def test_validate_invalid_environment(self):
        """Test validation catches invalid environment"""
        config = CoordinatorSystemConfig(environment='invalid_env')

        issues = validate_config(config)

        assert len(issues) > 0
        assert any("environment" in issue for issue in issues)

    def test_validate_multiple_issues(self):
        """Test validation reports multiple issues"""
        config = CoordinatorSystemConfig()
        config.main.max_concurrent_requests = 0
        config.resource.daily_budget = -10
        config.sync.sync_interval = 0

        issues = validate_config(config)

        assert len(issues) >= 3


# ============================================================================
# Test Logging Setup
# ============================================================================

class TestLoggingSetup:
    """Test logging setup function"""

    def test_setup_logging_info_level(self):
        """Test logging setup with INFO level"""
        config = CoordinatorSystemConfig(log_level='INFO')

        with patch('logging.basicConfig') as mock_basic:
            setup_logging(config)

            mock_basic.assert_called_once()
            args, kwargs = mock_basic.call_args
            assert kwargs['level'] == logging.INFO

    def test_setup_logging_debug_level(self):
        """Test logging setup with DEBUG level"""
        config = CoordinatorSystemConfig(log_level='DEBUG')

        with patch('logging.basicConfig') as mock_basic:
            setup_logging(config)

            args, kwargs = mock_basic.call_args
            assert kwargs['level'] == logging.DEBUG

    def test_setup_logging_production_reduces_noise(self):
        """Test production environment reduces external library logging"""
        config = CoordinatorSystemConfig(environment='production', log_level='INFO')

        with patch('logging.basicConfig'):
            with patch('logging.getLogger') as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger

                setup_logging(config)

                # Should have set WARNING level for external libraries
                mock_logger.setLevel.assert_called()


# ============================================================================
# Test File Import/Export
# ============================================================================

class TestFileImportExport:
    """Test configuration file import/export"""

    def test_export_config_template_yaml(self):
        """Test exporting configuration template to YAML"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            file_path = f.name

        try:
            with patch('builtins.print'):
                export_config_template(file_path, environment='development')

            # Check file was created and is valid YAML
            with open(file_path, 'r') as f:
                config_data = yaml.safe_load(f)

            assert config_data is not None
            assert 'main' in config_data
            assert 'environment' in config_data
        finally:
            os.unlink(file_path)

    def test_import_config_from_yaml(self):
        """Test importing configuration from YAML file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                'environment': 'production',
                'main': {'max_concurrent_requests': 25}
            }
            yaml.dump(config_data, f)
            file_path = f.name

        try:
            config = import_config_from_file(file_path)

            assert config.environment == 'production'
            assert config.main.max_concurrent_requests == 25
        finally:
            os.unlink(file_path)

    def test_import_config_from_json(self):
        """Test importing configuration from JSON file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                'environment': 'testing',
                'main': {'max_concurrent_requests': 2}
            }
            json.dump(config_data, f)
            file_path = f.name

        try:
            config = import_config_from_file(file_path)

            assert config.environment == 'testing'
            assert config.main.max_concurrent_requests == 2
        finally:
            os.unlink(file_path)


# ============================================================================
# Test Create Default Config File
# ============================================================================

class TestCreateDefaultConfigFile:
    """Test creating default configuration file"""

    def test_create_default_config_file_creates_file(self):
        """Test default config file creation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('builtins.print'):
                create_default_config_file(config_dir=tmpdir)

            config_path = Path(tmpdir) / "coordinator_config.yaml"
            assert config_path.exists()

    def test_create_default_config_file_valid_yaml(self):
        """Test created default config file is valid YAML"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('builtins.print'):
                create_default_config_file(config_dir=tmpdir)

            config_path = Path(tmpdir) / "coordinator_config.yaml"
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)

            assert config_data is not None
            assert 'main' in config_data

    def test_create_default_config_file_skips_if_exists(self):
        """Test creation skips if file already exists"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "coordinator_config.yaml"

            # Create existing file
            with open(config_path, 'w') as f:
                f.write("existing: content")

            with patch('builtins.print') as mock_print:
                create_default_config_file(config_dir=tmpdir)

                # Should print already exists message
                mock_print.assert_called_once()
                assert "already exists" in str(mock_print.call_args)


# ============================================================================
# Test Get Config For Environment
# ============================================================================

class TestGetConfigForEnvironment:
    """Test get_config_for_environment function"""

    def test_get_config_for_environment_valid(self):
        """Test getting config for valid environment"""
        with patch('core.coordinators.config.setup_logging'):
            config_dict = get_config_for_environment('development')

            assert isinstance(config_dict, dict)
            assert config_dict['environment'] == 'development'

    def test_get_config_for_environment_validates(self):
        """Test validation is performed"""
        # Create invalid config by patching create_config
        with patch('core.coordinators.config.create_config') as mock_create:
            invalid_config = CoordinatorSystemConfig()
            invalid_config.main.max_concurrent_requests = 0  # Invalid
            mock_create.return_value = invalid_config

            with patch('core.coordinators.config.setup_logging'):
                with pytest.raises(ValueError) as exc_info:
                    get_config_for_environment('development')

                assert "validation failed" in str(exc_info.value).lower()

    def test_get_config_for_environment_sets_up_logging(self):
        """Test logging is set up"""
        with patch('core.coordinators.config.setup_logging') as mock_setup:
            get_config_for_environment('production')

            mock_setup.assert_called_once()


# ============================================================================
# Test Edge Cases and Error Handling
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_deep_merge_with_none_values(self):
        """Test deep merge handles None values"""
        manager = ConfigurationManager()

        base = {'main': {'max_concurrent_requests': 10}}
        override = {'main': {'enable_caching': None}}

        manager._deep_merge(base, override)

        assert base['main']['enable_caching'] is None

    def test_deep_merge_non_dict_override(self):
        """Test deep merge with non-dict override"""
        manager = ConfigurationManager()

        base = {'main': {'max_concurrent_requests': 10}}
        override = {'main': 'not_a_dict'}

        manager._deep_merge(base, override)

        assert base['main'] == 'not_a_dict'

    def test_config_from_dict_partial_data(self):
        """Test from_dict with only some sub-configs"""
        data = {
            'environment': 'testing',
            'main': {'max_concurrent_requests': 5}
            # Other sub-configs not provided
        }

        config = CoordinatorSystemConfig.from_dict(data)

        # Should still create defaults for missing configs
        assert config.workflow is not None
        assert config.resource is not None

    def test_config_with_empty_dict(self):
        """Test from_dict with empty dictionary"""
        config = CoordinatorSystemConfig.from_dict({})

        # Should use all defaults
        assert config.environment == 'development'
        assert config.main.max_concurrent_requests == 10


# ============================================================================
# Test DEFAULT_CONFIG_YAML Content
# ============================================================================

class TestDefaultConfigYAML:
    """Test DEFAULT_CONFIG_YAML template"""

    def test_default_config_yaml_is_valid(self):
        """Test DEFAULT_CONFIG_YAML is valid YAML"""
        config_data = yaml.safe_load(DEFAULT_CONFIG_YAML)

        assert config_data is not None
        assert 'main' in config_data
        assert 'workflow' in config_data
        assert 'resource' in config_data
        assert 'sync' in config_data
        assert 'error' in config_data

    def test_default_config_yaml_has_comments(self):
        """Test DEFAULT_CONFIG_YAML has comments/documentation"""
        assert '# ToolboxAI' in DEFAULT_CONFIG_YAML
        assert '# API Quotas' in DEFAULT_CONFIG_YAML


# ============================================================================
# Test Dataclass Field Modifications
# ============================================================================

class TestDataclassFieldModifications:
    """Test modifying dataclass fields"""

    def test_main_config_field_update(self):
        """Test updating MainCoordinatorConfig fields"""
        config = MainCoordinatorConfig()
        config.max_concurrent_requests = 50

        assert config.max_concurrent_requests == 50

    def test_nested_config_update(self):
        """Test updating nested configuration"""
        config = CoordinatorSystemConfig()
        config.main.max_concurrent_requests = 100
        config.resource.daily_budget = 200.0

        assert config.main.max_concurrent_requests == 100
        assert config.resource.daily_budget == 200.0


# ============================================================================
# Test Post-Init Validation
# ============================================================================

class TestPostInitValidation:
    """Test __post_init__ validation"""

    def test_post_init_creates_sub_configs(self):
        """Test __post_init__ creates sub-configs if None"""
        config = CoordinatorSystemConfig(
            main=None,
            workflow=None,
            resource=None,
            sync=None,
            error=None
        )

        # __post_init__ should have created them
        assert isinstance(config.main, MainCoordinatorConfig)
        assert isinstance(config.workflow, WorkflowCoordinatorConfig)
        assert isinstance(config.resource, ResourceCoordinatorConfig)
        assert isinstance(config.sync, SyncCoordinatorConfig)
        assert isinstance(config.error, ErrorCoordinatorConfig)


# ============================================================================
# Test Marks and Configuration
# ============================================================================

# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit

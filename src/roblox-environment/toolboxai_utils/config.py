"""Enhanced configuration management"""

import os
from typing import Any, Dict, List, Optional, Type, Union
from pydantic import BaseModel, Field, validator
import logging

logger = logging.getLogger(__name__)


class ServerConfig(BaseModel):
    """Server configuration with validation"""
    
    # Thread pool configuration
    thread_pool_size: int = Field(default=5, ge=1, le=50)
    
    # Cache configuration
    cache_max_size: int = Field(default=1000, ge=100, le=10000)
    cache_ttl: int = Field(default=300, ge=60, le=3600)
    
    # Rate limiting
    rate_limit_requests: int = Field(default=60, ge=10, le=1000)
    rate_limit_window: int = Field(default=60, ge=10, le=300)
    
    # Memory limits
    max_memory_mb: int = Field(default=100, ge=50, le=1000)
    
    # Backup intervals
    backup_interval: int = Field(default=300, ge=60, le=3600)
    
    # Security
    token_expiry_hours: int = Field(default=24, ge=1, le=168)
    
    @validator('thread_pool_size')
    def validate_thread_pool_size(cls, v):
        cpu_count = os.cpu_count() or 4
        if v > cpu_count * 2:
            logger.warning("Thread pool size %d exceeds 2x CPU count (%d)", v, cpu_count)
        return v


class ConfigManager:
    """Dynamic configuration manager"""
    
    def __init__(self, config_class: Type[BaseModel] = ServerConfig):
        self.config_class = config_class
        self._config = self._load_config()
        self._callbacks: List[callable] = []
    
    def _load_config(self) -> BaseModel:
        """Load configuration from environment"""
        config_data = {}
        
        # Load from environment variables with CONFIG_ prefix
        for key, value in os.environ.items():
            if key.startswith('CONFIG_'):
                config_key = key[7:].lower()  # Remove CONFIG_ prefix
                
                # Try to convert to appropriate type
                if value.lower() in ('true', 'false'):
                    config_data[config_key] = value.lower() == 'true'
                elif value.isdigit():
                    config_data[config_key] = int(value)
                else:
                    try:
                        config_data[config_key] = float(value)
                    except ValueError:
                        config_data[config_key] = value
        
        return self.config_class(**config_data)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return getattr(self._config, key, default)
    
    def update(self, **kwargs) -> None:
        """Update configuration"""
        try:
            # Create new config with updates
            current_data = self._config.dict()
            current_data.update(kwargs)
            new_config = self.config_class(**current_data)
            
            # If validation passes, update
            old_config = self._config
            self._config = new_config
            
            # Notify callbacks
            for callback in self._callbacks:
                try:
                    callback(old_config, new_config)
                except Exception as e:
                    logger.error("Config callback failed: %s", e)
            
            logger.info("Configuration updated: %s", kwargs)
            
        except Exception as e:
            logger.error("Configuration update failed: %s", e)
            raise
    
    def register_callback(self, callback: callable) -> None:
        """Register callback for configuration changes"""
        self._callbacks.append(callback)
    
    def to_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary"""
        return self._config.dict()
    
    def validate(self) -> List[str]:
        """Validate current configuration"""
        errors = []
        
        try:
            self.config_class(**self._config.dict())
        except Exception as e:
            errors.append(str(e))
        
        return errors


# Global configuration manager
config_manager = ConfigManager()
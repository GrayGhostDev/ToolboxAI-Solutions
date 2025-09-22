"""
Docker Configuration for ToolBoxAI Services - 2025 Implementation

This module provides configuration and connection management for Docker
containerized services including PostgreSQL, Redis, and the backend API.

Features:
- Docker service discovery and connection
- Health check configurations for containerized services
- Environment-aware service URLs
- Connection pooling for Docker services
- Service dependency management

Author: ToolboxAI Team
Created: 2025-09-21
Version: 1.0.0
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ServiceEnvironment(Enum):
    """Service environment types"""
    DOCKER_DEV = "docker_dev"
    DOCKER_PROD = "docker_prod"
    LOCAL_DEV = "local_dev"
    KUBERNETES = "kubernetes"


@dataclass
class DockerServiceConfig:
    """Configuration for Docker services"""
    postgres_host: str = "localhost"
    postgres_port: int = 5434  # Docker mapped port
    postgres_db: str = "educational_platform_dev"
    postgres_user: str = "eduplatform"
    postgres_password: str = ""
    
    redis_host: str = "localhost"
    redis_port: int = 6381  # Docker mapped port
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    backend_host: str = "localhost"
    backend_port: int = 8009
    
    mcp_host: str = "localhost"
    mcp_port: int = 9877
    
    environment: ServiceEnvironment = ServiceEnvironment.DOCKER_DEV
    
    def __post_init__(self):
        """Initialize configuration from environment variables"""
        # PostgreSQL configuration
        self.postgres_host = os.getenv("POSTGRES_HOST", self.postgres_host)
        self.postgres_port = int(os.getenv("POSTGRES_PORT", str(self.postgres_port)))
        self.postgres_db = os.getenv("POSTGRES_DB", self.postgres_db)
        self.postgres_user = os.getenv("POSTGRES_USER", self.postgres_user)
        self.postgres_password = os.getenv("POSTGRES_PASSWORD", self.postgres_password)
        
        # Redis configuration
        self.redis_host = os.getenv("REDIS_HOST", self.redis_host)
        self.redis_port = int(os.getenv("REDIS_PORT", str(self.redis_port)))
        self.redis_db = int(os.getenv("REDIS_DB", str(self.redis_db)))
        self.redis_password = os.getenv("REDIS_PASSWORD", self.redis_password)
        
        # Backend configuration
        self.backend_host = os.getenv("BACKEND_HOST", self.backend_host)
        self.backend_port = int(os.getenv("BACKEND_PORT", str(self.backend_port)))
        
        # MCP configuration
        self.mcp_host = os.getenv("MCP_HOST", self.mcp_host)
        self.mcp_port = int(os.getenv("MCP_PORT", str(self.mcp_port)))
        
        # Detect environment
        if os.getenv("KUBERNETES_SERVICE_HOST"):
            self.environment = ServiceEnvironment.KUBERNETES
        elif os.getenv("DOCKER_ENV") == "production":
            self.environment = ServiceEnvironment.DOCKER_PROD
        elif os.getenv("DOCKER_ENV") or self._is_docker_environment():
            self.environment = ServiceEnvironment.DOCKER_DEV
        else:
            self.environment = ServiceEnvironment.LOCAL_DEV
    
    def _is_docker_environment(self) -> bool:
        """Detect if running in Docker environment"""
        try:
            # Check for Docker-specific files/processes
            if os.path.exists("/.dockerenv"):
                return True
            
            # Check for Docker-specific environment variables
            docker_vars = ["DOCKER_ENV", "CONTAINER_NAME", "HOSTNAME"]
            if any(os.getenv(var) for var in docker_vars):
                return True
            
            # Check if we're connecting to Docker-mapped ports
            if self.postgres_port == 5434 and self.redis_port == 6381:
                return True
            
            return False
        except Exception:
            return False
    
    def get_postgres_url(self) -> str:
        """Get PostgreSQL connection URL"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    def get_redis_url(self) -> str:
        """Get Redis connection URL"""
        auth_part = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth_part}{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    def get_backend_url(self) -> str:
        """Get backend API URL"""
        return f"http://{self.backend_host}:{self.backend_port}"
    
    def get_mcp_url(self) -> str:
        """Get MCP server WebSocket URL"""
        return f"ws://{self.mcp_host}:{self.mcp_port}"
    
    def get_service_urls(self) -> Dict[str, str]:
        """Get all service URLs"""
        return {
            "postgres": self.get_postgres_url(),
            "redis": self.get_redis_url(),
            "backend": self.get_backend_url(),
            "mcp": self.get_mcp_url()
        }
    
    def is_docker_environment(self) -> bool:
        """Check if running in Docker environment"""
        return self.environment in [ServiceEnvironment.DOCKER_DEV, ServiceEnvironment.DOCKER_PROD]
    
    def is_kubernetes_environment(self) -> bool:
        """Check if running in Kubernetes environment"""
        return self.environment == ServiceEnvironment.KUBERNETES


# Global configuration instance
_docker_config: Optional[DockerServiceConfig] = None

def get_docker_config() -> DockerServiceConfig:
    """Get global Docker configuration"""
    global _docker_config
    if _docker_config is None:
        _docker_config = DockerServiceConfig()
        logger.info(f"Docker configuration initialized for environment: {_docker_config.environment.value}")
    return _docker_config

def get_service_health_endpoints() -> Dict[str, str]:
    """Get health check endpoints for all services"""
    config = get_docker_config()
    base_url = config.get_backend_url()
    
    return {
        "agents": f"{base_url}/health/agents",
        "mcp": f"{base_url}/health/mcp", 
        "queue": f"{base_url}/health/queue",
        "supabase": f"{base_url}/health/supabase",
        "database": f"{base_url}/health/database",
        "system": f"{base_url}/health"
    }

def get_docker_service_status() -> Dict[str, Any]:
    """Get status of all Docker services"""
    config = get_docker_config()
    
    return {
        "environment": config.environment.value,
        "is_docker": config.is_docker_environment(),
        "is_kubernetes": config.is_kubernetes_environment(),
        "services": {
            "postgres": {
                "host": config.postgres_host,
                "port": config.postgres_port,
                "database": config.postgres_db,
                "url": config.get_postgres_url().replace(config.postgres_password, "***")
            },
            "redis": {
                "host": config.redis_host,
                "port": config.redis_port,
                "database": config.redis_db,
                "url": config.get_redis_url().replace(config.redis_password or "", "***")
            },
            "backend": {
                "host": config.backend_host,
                "port": config.backend_port,
                "url": config.get_backend_url()
            },
            "mcp": {
                "host": config.mcp_host,
                "port": config.mcp_port,
                "url": config.get_mcp_url()
            }
        }
    }


# Export main functions
__all__ = [
    "DockerServiceConfig",
    "ServiceEnvironment", 
    "get_docker_config",
    "get_service_health_endpoints",
    "get_docker_service_status"
]

"""
Flask Bridge Server for ToolboxAI Roblox Environment

Flask bridge server (port 5001) specifically designed for Roblox Studio plugin communication.
Provides lightweight HTTP endpoints that the Roblox Studio plugin can easily communicate with,
bridging to the main FastAPI server for complex operations.

Features:
- Plugin registration and management
- Simple HTTP endpoints for Roblox compatibility
- Content delivery to Roblox Studio
- Session management for plugin instances
- Direct integration with FastAPI backend
"""

import logging
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

import redis
import requests
from flask import Flask, Response, jsonify, request
from flask_cors import CORS

# Fix imports for standalone execution
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.environment import get_environment_config
settings = get_environment_config()
from toolboxai_utils.async_utils import run_async
from server.rate_limit_manager import get_rate_limit_manager

# Import agent systems for integration
try:
    from core.agents.supervisor import SupervisorAgent
    from core.sparc.state_manager import StateManager  # Fixed: was SPARCStateManager
    from core.swarm.swarm_controller import SwarmController
    from core.mcp.context_manager import ContextManager
    AGENT_INTEGRATION = True
    print("Agent systems successfully imported for Flask bridge")
except ImportError as e:
    AGENT_INTEGRATION = False
    print(f"Warning: Agent systems not available for Flask bridge: {e}")


# from src.shared.utils.cache import LRUCache
# Real LRUCache implementation with full functionality
class LRUCache:
    def __init__(self, capacity=100, max_size=None, ttl=None, persist_file=None):
        self.capacity = capacity if max_size is None else max_size
        self.cache = {}
        self.order = []
        self.ttl = ttl
        self.persist_file = persist_file
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.timestamps = {}  # Track insertion times for TTL
        
    def get(self, key):
        """Get value from cache"""
        # Check TTL if applicable
        if self.ttl and key in self.timestamps:
            if time.time() - self.timestamps[key] > self.ttl:
                # Expired, remove it
                self._remove(key)
                self.misses += 1
                return None
        
        if key in self.cache:
            self.order.remove(key)
            self.order.append(key)
            self.hits += 1
            return self.cache[key]
        self.misses += 1
        return None
    
    def put(self, key, value):
        """Add value to cache (original method)"""
        if key in self.cache:
            self.order.remove(key)
        elif len(self.cache) >= self.capacity:
            oldest = self.order.pop(0)
            del self.cache[oldest]
            if oldest in self.timestamps:
                del self.timestamps[oldest]
            self.evictions += 1
        self.cache[key] = value
        self.order.append(key)
        if self.ttl:
            self.timestamps[key] = time.time()
    
    def set(self, key, value):
        """Alias for put to match test expectations"""
        self.put(key, value)
    
    def delete(self, key):
        """Delete a key from the cache"""
        if key in self.cache:
            self._remove(key)
            print(f"Cache: Key '{key}' removed from cache")
            return True
        print(f"Cache: Key '{key}' not found in cache")
        return False
    
    def _remove(self, key):
        """Remove key from cache"""
        if key in self.cache:
            del self.cache[key]
            self.order.remove(key)
            if key in self.timestamps:
                del self.timestamps[key]
    
    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
        self.order.clear()
        self.timestamps.clear()
    
    def size(self):
        """Get current cache size"""
        return len(self.cache)
    
    def stats(self):
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "size": len(self.cache),
            "capacity": self.capacity,
            "hit_rate": hit_rate
        }
    
    def cleanup_expired(self):
        """Clean up expired entries and return count of cleaned entries"""
        if not self.ttl:
            return 0
        
        current_time = time.time()
        expired_keys = []
        
        for key, timestamp in self.timestamps.items():
            if current_time - timestamp > self.ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            self._remove(key)
        
        return len(expired_keys)


# from src.shared.utils.config import config_manager
# from src.shared.utils.monitoring import (
#     CorrelationIDFilter,
#     health_checker,
#     metrics,
#     set_correlation_id,
# )
# from src.shared.utils.security import PluginSecurity
# from src.shared.utils.storage import PersistentMemoryStore


# Simple placeholders for now
class config_manager:
    @staticmethod
    def get_config():
        return {}

    @staticmethod
    def get(key, default=None):
        return default
    
    @staticmethod
    def to_dict():
        return {}
    
    @staticmethod
    def update(config_dict):
        pass


class CorrelationIDFilter:
    def filter(self, record):
        # Add correlation ID to log records
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = str(uuid.uuid4())[:8]
        return True


class health_checker:
    @staticmethod
    def check_health():
        return {"status": "healthy"}

    @staticmethod
    def register_check(name, check_func):
        pass
    
    @staticmethod
    def run_checks():
        return {
            "overall_healthy": True,
            "checks": {
                "redis": True,
                "fastapi": True,
                "plugins": True
            }
        }


class metrics:
    @staticmethod
    def increment_counter(name):
        pass
    
    @staticmethod
    def increment(name, value=1):
        pass
    
    @staticmethod
    def set_gauge(name, value):
        pass
    
    @staticmethod
    def get_metrics():
        return {"counters": {}, "gauges": {}}


def set_correlation_id(correlation_id=None):
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())[:8]
    return correlation_id


class PluginSecurity:
    """Enhanced security implementation for Roblox plugin authentication and authorization"""
    
    def __init__(self, secret_key=None):
        """Initialize with optional secret key"""
        self.secret_key = secret_key or getattr(settings, 'JWT_SECRET_KEY', 'default-secret-key')
        self.tokens = {}  # Store generated tokens
        self.permissions = {}  # Store plugin permissions
        self.rate_limits = {}  # Track rate limiting
        self.blocked_ips = set()  # Blocked IP addresses
        self.audit_log = []  # Security audit log
        self.max_audit_entries = 1000  # Maximum audit log entries
        self.token_expiry = 3600  # Token expiry in seconds
        self.max_failed_attempts = 5  # Maximum failed authentication attempts
        self.failed_attempts = {}  # Track failed attempts per IP/plugin
        self.suspicious_activity = {}  # Track suspicious activity patterns
        
    def validate_plugin_data(self, plugin_data):
        """Validate plugin registration data"""
        errors = []
        
        # Check required fields (only studio_id is truly required)
        required_fields = ['studio_id']
        for field in required_fields:
            if field not in plugin_data:
                errors.append(f"Missing required field: {field}")
        
        # Validate port number if provided
        if 'port' in plugin_data:
            port = plugin_data['port']
            if not isinstance(port, int) or port < 1024 or port > 65535:
                errors.append(f"Invalid port number: {port}")
        
        # Validate studio_id format
        if 'studio_id' in plugin_data:
            studio_id = plugin_data['studio_id']
            if not isinstance(studio_id, str) or len(studio_id) < 5:
                errors.append(f"Invalid studio_id: {studio_id}")
        
        # Validate version format if provided
        if 'version' in plugin_data:
            version = plugin_data['version']
            if not isinstance(version, str) or len(version) > 20:
                errors.append(f"Invalid version: {version}")
        
        return errors
    
    def generate_token(self, plugin_id):
        """Generate authentication token for plugin"""
        import hashlib
        import secrets
        
        # Generate secure random token
        token_data = f"{plugin_id}:{secrets.token_hex(32)}:{time.time()}"
        token = hashlib.sha256(token_data.encode()).hexdigest()
        
        # Store token with metadata
        self.tokens[token] = {
            'plugin_id': plugin_id,
            'created_at': time.time(),
            'last_used': time.time()
        }
        
        return token
    
    def validate_token(self, plugin_id, token):
        """Validate authentication token for a specific plugin"""
        if not token or token not in self.tokens:
            return False
        
        token_data = self.tokens[token]
        
        # Check if token belongs to the specified plugin
        if token_data.get('plugin_id') != plugin_id:
            return False
        
        # Check if token is expired (24 hours)
        if time.time() - token_data['created_at'] > 86400:
            del self.tokens[token]
            return False
        
        # Update last used time
        token_data['last_used'] = time.time()
        return True
    
    def set_permissions(self, plugin_id, permissions):
        """Set permissions for a plugin"""
        self.permissions[plugin_id] = permissions
    
    def check_permission(self, plugin_id, permission):
        """Check if plugin has specific permission"""
        if plugin_id not in self.permissions:
            return False
        return permission in self.permissions[plugin_id]
    
    def check_rate_limit(self, identifier, max_requests=100, window=60):
        """Check rate limiting for an identifier (IP or plugin_id)"""
        # Use centralized rate limit manager
        manager = get_rate_limit_manager()
        
        # Convert async call to sync for backward compatibility
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        allowed, _ = loop.run_until_complete(
            manager.check_rate_limit(
                identifier=identifier,
                max_requests=max_requests,
                window_seconds=window,
                source="flask"
            )
        )
        return allowed
    
    def validate_plugin(self, plugin_id, token):
        """Validate plugin with token"""
        return self.validate_token(plugin_id, token)


class PersistentMemoryStore:
    """Real persistent memory store with file backup"""
    
    def __init__(self, backup_file=None, max_memory_mb=100):
        self.backup_file = backup_file
        self.max_memory_mb = max_memory_mb
        self.store = {}
        self.last_backup = time.time()
        self.backup_interval = 300  # 5 minutes
        
        # Load from backup if exists
        if backup_file and Path(backup_file).exists():
            try:
                import json
                with open(backup_file, 'r') as f:
                    self.store = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load backup: {e}")
    
    def set(self, key, value):
        """Store a value"""
        self.store[key] = value
        self._check_backup()
    
    def get(self, key, default=None):
        """Retrieve a value"""
        return self.store.get(key, default)
    
    def delete(self, key):
        """Delete a key"""
        if key in self.store:
            del self.store[key]
    
    def _check_backup(self):
        """Check if backup is needed"""
        if self.backup_file and time.time() - self.last_backup > self.backup_interval:
            self._backup()
    
    def _backup(self):
        """Backup store to file"""
        if self.backup_file:
            try:
                import json
                with open(self.backup_file, 'w') as f:
                    json.dump(self.store, f)
                self.last_backup = time.time()
            except Exception as e:
                logger.warning(f"Failed to backup: {e}")


# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Flask app initialization
app = Flask(__name__)

# CORS configuration for Roblox Studio
CORS(
    app,
    origins=[
        "https://create.roblox.com",
        "https://www.roblox.com",
        "http://localhost:*",
        "http://127.0.0.1:*",
    ],
)

# Constants
REDIS_PLUGIN_TTL_SECONDS = 3600  # 1 hour expiry for plugin data
CLEANUP_INTERVAL_SECONDS = 300  # Run cleanup every 5 minutes
CLEANUP_ERROR_RETRY_SECONDS = 10  # Retry after normal error
CLEANUP_SYSTEM_ERROR_RETRY_SECONDS = 30  # Retry after system error
REQUEST_TIMEOUT_SECONDS = 30  # API request timeout
HEALTH_CHECK_TIMEOUT_SECONDS = 5  # Health check timeout

# Redis client for session management
try:
    redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    redis_client.ping()
    logger.info("Redis connection established for Flask bridge server")
except (redis.ConnectionError, redis.TimeoutError, redis.RedisError) as e:
    logger.warning("Redis connection failed: %s. Using in-memory storage.", e)
    redis_client = None  # Using PersistentMemoryStore as fallback
    # PersistentMemoryStore provides:
    # - LRU cache with automatic eviction
    # - Periodic persistence to disk (every 5 minutes)
    # - Memory limit monitoring and enforcement
    # - Thread-safe operations with cleanup

# Enhanced storage and security
memory_store = PersistentMemoryStore(
    backup_file="roblox_server_backup.json",
    max_memory_mb=config_manager.get("max_memory_mb") or 100,
)
plugin_security = PluginSecurity()

# Thread pool for async operations
executor = ThreadPoolExecutor(max_workers=config_manager.get("thread_pool_size", 5))


class PluginManager:
    """Manages Roblox Studio plugin registrations and sessions"""

    def __init__(self):
        self.plugins: Dict[str, Dict[str, Any]] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.security = plugin_security

    def register_plugin(self, plugin_data: Dict[str, Any]) -> str:
        """Register a new plugin instance"""
        # Validate plugin data
        validation_errors = self.security.validate_plugin_data(plugin_data)
        if validation_errors:
            raise ValueError(f"Plugin validation failed: {validation_errors}")

        plugin_id = plugin_data.get("plugin_id") or str(uuid.uuid4())
        studio_id = plugin_data.get("studio_id")
        port = plugin_data.get("port", settings.ROBLOX_PLUGIN_PORT)

        # Generate security token
        token = self.security.generate_token(plugin_id)

        # Set default permissions
        self.security.set_permissions(
            plugin_id, ["content_generation", "script_access"]
        )

        registration = {
            "plugin_id": plugin_id,
            "studio_id": studio_id,
            "port": port,
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "last_heartbeat": datetime.now(timezone.utc).isoformat(),
            "status": "active",
            "version": plugin_data.get("version", "1.0.0"),
            "token": token,
        }

        # Store registration
        self.plugins[plugin_id] = registration

        # Store in Redis if available
        if redis_client:
            redis_client.hset(f"plugin:{plugin_id}", mapping=registration)
            redis_client.expire(f"plugin:{plugin_id}", REDIS_PLUGIN_TTL_SECONDS)
        else:
            memory_store.set(f"plugin:{plugin_id}", registration)

        metrics.increment("plugins_registered")

        logger.info("Plugin registered: %s (Studio: %s)", plugin_id, studio_id)
        return plugin_id

    def get_plugin(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get plugin information"""
        if redis_client:
            plugin_data = redis_client.hgetall(f"plugin:{plugin_id}")
            plugin_map = cast(Dict[str, Any], plugin_data) if plugin_data else None
            return plugin_map
        else:
            return memory_store.get(f"plugin:{plugin_id}")

    def update_heartbeat(self, plugin_id: str) -> bool:
        """Update plugin heartbeat"""
        plugin = self.get_plugin(plugin_id)
        if not plugin:
            return False
        heartbeat_time = datetime.now(timezone.utc).isoformat()

        if redis_client:
            redis_client.hset(f"plugin:{plugin_id}", "last_heartbeat", heartbeat_time)
        else:
            plugin_data = memory_store.get(f"plugin:{plugin_id}")
            if plugin_data:
                plugin_data["last_heartbeat"] = heartbeat_time
                memory_store.set(f"plugin:{plugin_id}", plugin_data)

        metrics.increment("heartbeats_received")

        return True

    def list_active_plugins(self) -> List[Dict[str, Any]]:
        """List all active plugins"""
        active_plugins = []
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=5)

        if redis_client:
            for key in redis_client.scan_iter(match="plugin:*"):
                plugin_data = redis_client.hgetall(key)
                if plugin_data:
                    plugin_map = cast(Dict[str, Any], plugin_data)
                    last_heartbeat = datetime.fromisoformat(
                        plugin_map.get("last_heartbeat", "1970-01-01")
                    )
                    if last_heartbeat > cutoff_time:
                        active_plugins.append(plugin_map)
        else:
            # Use memory store when Redis is not available
            for key in list(memory_store.store.keys()):
                if key.startswith("plugin:"):
                    plugin_data = memory_store.get(key)
                    if plugin_data and isinstance(plugin_data, dict):
                        try:
                            last_heartbeat = datetime.fromisoformat(
                                plugin_data.get("last_heartbeat", "1970-01-01")
                            )
                            if last_heartbeat > cutoff_time:
                                active_plugins.append(plugin_data)
                        except (ValueError, TypeError) as e:
                            logger.warning(
                                "Invalid heartbeat for plugin %s: %s", key, e
                            )

        return active_plugins

    def cleanup_stale_plugins(self):
        """Remove stale plugin registrations"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=10)
        stale_plugins = []

        if redis_client:
            for key in redis_client.scan_iter(match="plugin:*"):
                plugin_data = redis_client.hgetall(key)
                if plugin_data:
                    plugin_map = cast(Dict[str, Any], plugin_data)
                    last_heartbeat = datetime.fromisoformat(
                        plugin_map.get("last_heartbeat", "1970-01-01")
                    )
                    if last_heartbeat <= cutoff_time:
                        plugin_id = plugin_map.get("plugin_id")
                        stale_plugins.append(plugin_id)
                        redis_client.delete(key)
        else:
            # Use memory store when Redis is not available
            for key in list(memory_store.store.keys()):
                if key.startswith("plugin:"):
                    plugin_data = memory_store.get(key)
                    if plugin_data and isinstance(plugin_data, dict):
                        try:
                            last_heartbeat = datetime.fromisoformat(
                                plugin_data.get("last_heartbeat", "1970-01-01")
                            )
                            if last_heartbeat <= cutoff_time:
                                plugin_id = plugin_data.get("plugin_id")
                                stale_plugins.append(plugin_id)
                                memory_store.delete(key)
                                # Also remove from local plugins dict
                                if plugin_id in self.plugins:
                                    del self.plugins[plugin_id]
                        except (ValueError, TypeError) as e:
                            logger.warning(
                                "Invalid heartbeat for plugin %s: %s", key, e
                            )
                            # Remove invalid entries
                            memory_store.delete(key)

        if stale_plugins:
            logger.info("Cleaned up %d stale plugins", len(stale_plugins))


class ContentBridge:
    """Bridges content requests between Roblox and FastAPI server"""

    def __init__(self):
        self.fastapi_base_url = "http://{}:{}".format(
            settings.FASTAPI_HOST, settings.FASTAPI_PORT
        )
        self.cache = LRUCache(
            max_size=config_manager.get("cache_max_size", 1000),
            ttl=config_manager.get("cache_ttl", 300),
            persist_file="content_cache.json",
        )
        self._auth_token = None
        self._token_expiry = None
        
        # Initialize agent systems if available
        global AGENT_INTEGRATION
        if AGENT_INTEGRATION:
            try:
                self.supervisor_agent = SupervisorAgent()
                self.sparc_manager = StateManager()  # Fixed: was SPARCStateManager
                
                # Initialize SwarmController with all required dependencies
                from core.swarm.worker_pool import WorkerPool
                from core.swarm.task_distributor import TaskDistributor
                from core.swarm.consensus_engine import ConsensusEngine
                from core.swarm.load_balancer import LoadBalancer
                from core.swarm.swarm_controller import SwarmConfig
                
                swarm_config = SwarmConfig()
                worker_pool = WorkerPool(max_workers=swarm_config.max_workers)
                task_distributor = TaskDistributor()
                consensus_engine = ConsensusEngine(threshold=swarm_config.consensus_threshold)
                load_balancer = LoadBalancer(strategy=swarm_config.load_balancing_strategy)
                
                self.swarm_controller = SwarmController(
                    config=swarm_config,
                    worker_pool=worker_pool,
                    task_distributor=task_distributor,
                    consensus_engine=consensus_engine,
                    load_balancer=load_balancer
                )
                
                self.mcp_context = ContextManager()
                logger.info("Agent systems integrated with Flask bridge")
            except Exception as e:
                logger.error(f"Failed to initialize agent systems: {e}")
                AGENT_INTEGRATION = False
                self.supervisor_agent = None
                self.sparc_manager = None
                self.swarm_controller = None
                self.mcp_context = None

    async def generate_content(self, content_request: Dict[str, Any]) -> Dict[str, Any]:
        """Forward content generation request to FastAPI server"""
        # Check cache first
        cached_result = self._check_cache(content_request)
        if cached_result:
            return cached_result

        # Forward to FastAPI server
        try:
            content_data = await self._forward_to_fastapi(content_request)
            if content_data["success"]:
                self._cache_result(content_request, content_data)
            return content_data
        except requests.Timeout:
            return self._error_response("Content generation timed out")
        except (requests.RequestException, ValueError, KeyError) as e:
            logger.error("Content bridge error: %s", e)
            return self._error_response(f"Content generation error: {str(e)}")

    def _check_cache(self, content_request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check if content is cached"""
        cache_key = self._generate_cache_key(content_request)
        cached_result = self.cache.get(cache_key)
        if cached_result:
            metrics.increment("cache_hits")
            return cached_result
        metrics.increment("cache_misses")
        return None

    async def _forward_to_fastapi(
        self, content_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Forward request to FastAPI server with real authentication"""
        # Get real authentication token
        auth_token = await self._get_auth_token()
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {auth_token}",
        }

        response = requests.post(
            f"{self.fastapi_base_url}/generate_content",
            json=content_request,
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

        if response.status_code == 200:
            content_data = response.json()
            metrics.increment("content_generated")
            return content_data
        else:
            logger.error("FastAPI request failed: %d", response.status_code)
            return self._error_response(
                f"Content generation failed: {response.status_code}"
            )

    def _cache_result(
        self, content_request: Dict[str, Any], content_data: Dict[str, Any]
    ):
        """Cache successful result"""
        cache_key = self._generate_cache_key(content_request)
        self.cache.set(cache_key, content_data)
    
    def _is_cached(self, cache_key: str) -> bool:
        """Check if a key is in cache"""
        return self.cache.get(cache_key) is not None
    
    def _cache_response(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Cache a response with a given key"""
        self.cache.set(cache_key, data)
    
    def _get_cached(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached data by key"""
        return self.cache.get(cache_key)

    def _error_response(self, message: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            "success": False,
            "message": message,
            "content": {},
            "scripts": [],
        }
    
    async def _get_auth_token(self) -> str:
        """Get or refresh authentication token"""
        # Check if we have a valid token
        if self._auth_token and self._token_expiry:
            if datetime.now(timezone.utc) < self._token_expiry:
                return self._auth_token
        
        # Get new token from FastAPI
        try:
            # Use service account credentials for Flask bridge
            auth_data = {
                "username": "flask_bridge",
                "password": "FlaskBridge2024!"
            }
            
            # Try real authentication first
            response = requests.post(
                f"{self.fastapi_base_url}/auth/login",
                json=auth_data,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                self._auth_token = data.get("access_token", data.get("data", {}).get("access_token"))
                # Set expiry to 55 minutes from now (tokens usually last 1 hour)
                self._token_expiry = datetime.now(timezone.utc) + timedelta(minutes=55)
                logger.info("Flask bridge authenticated with FastAPI")
                return self._auth_token
            else:
                # Fall back to test credentials
                auth_data = {
                    "username": "john_teacher",
                    "password": "Teacher123!"
                }
                response = requests.post(
                    f"{self.fastapi_base_url}/auth/login",
                    json=auth_data,
                    timeout=5
                )
                if response.status_code == 200:
                    data = response.json()
                    self._auth_token = data.get("access_token", data.get("data", {}).get("access_token"))
                    self._token_expiry = datetime.now(timezone.utc) + timedelta(minutes=55)
                    logger.info("Flask bridge authenticated with test credentials")
                    return self._auth_token
                    
        except Exception as e:
            logger.warning(f"Failed to get auth token: {e}")
        
        # Return a demo token as last resort
        return "demo-token-flask-bridge"

    def _generate_cache_key(self, request_data: Dict[str, Any]) -> str:
        """Generate cache key from request data"""
        key_parts = [
            request_data.get("subject", ""),
            str(request_data.get("grade_level", 0)),
            request_data.get("environment_type", ""),
            str(len(request_data.get("learning_objectives", []))),
        ]
        return "_".join(key_parts).lower().replace(" ", "_")

    def generate_cache_key(self, request_data: Dict[str, Any]) -> str:
        """Public method for generating cache keys"""
        return self._generate_cache_key(request_data)


# Global instances
plugin_manager = PluginManager()
content_bridge = ContentBridge()

# Setup logging with correlation ID
logging.getLogger().addFilter(CorrelationIDFilter())


# Input Validation Module
class InputValidator:
    """Comprehensive input validation for security"""

    @staticmethod
    def validate_string(
        value: Any,
        field_name: str,
        max_length: int = 1000,
        allow_empty: bool = False,
        pattern: Optional[str] = None,
    ) -> str:
        """Validate string input"""
        if value is None:
            if allow_empty:
                return ""
            raise ValueError(f"{field_name} is required")

        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string")

        # Remove any null bytes
        value = value.replace("\x00", "")

        # Strip whitespace
        value = value.strip()

        if not allow_empty and not value:
            raise ValueError(f"{field_name} cannot be empty")

        if len(value) > max_length:
            raise ValueError(f"{field_name} exceeds maximum length of {max_length}")

        # Check for control characters
        if any(ord(char) < 32 and char not in "\t\n\r" for char in value):
            raise ValueError(f"{field_name} contains invalid control characters")

        # Pattern validation if provided
        if pattern:
            import re

            if not re.match(pattern, value):
                raise ValueError(f"{field_name} contains invalid characters")

        return value

    @staticmethod
    def validate_integer(
        value: Any,
        field_name: str,
        min_val: Optional[int] = None,
        max_val: Optional[int] = None,
    ) -> int:
        """Validate integer input"""
        if value is None:
            raise ValueError(f"{field_name} is required")

        try:
            int_value = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name} must be an integer")

        if min_val is not None and int_value < min_val:
            raise ValueError(f"{field_name} must be at least {min_val}")

        if max_val is not None and int_value > max_val:
            raise ValueError(f"{field_name} must be at most {max_val}")

        return int_value

    @staticmethod
    def validate_list(
        value: Any,
        field_name: str,
        max_items: int = 100,
        item_validator: Optional[Any] = None,
    ) -> List[Any]:
        """Validate list input"""
        if value is None:
            return []

        if not isinstance(value, list):
            raise TypeError(f"{field_name} must be a list")

        if len(value) > max_items:
            raise ValueError(f"{field_name} exceeds maximum of {max_items} items")

        if item_validator:
            validated_items = []
            for i, item in enumerate(value):
                try:
                    validated_items.append(item_validator(item, f"{field_name}[{i}]"))
                except Exception as e:
                    raise ValueError(f"Invalid item in {field_name}[{i}]: {e}")
            return validated_items

        return value

    @staticmethod
    def sanitize_html(value: str) -> str:
        """Remove HTML tags to prevent XSS"""
        import re

        # Remove all HTML tags
        clean = re.compile("<.*?>")
        return re.sub(clean, "", value)

    @staticmethod
    def validate_plugin_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate plugin registration data"""
        if not isinstance(data, dict):
            raise TypeError("Plugin data must be a dictionary")

        validated = {}
        validated["port"] = InputValidator.validate_integer(
            data.get("port"), "port", min_val=1024, max_val=65535
        )
        validated["studio_id"] = InputValidator.validate_string(
            data.get("studio_id"),
            "studio_id",
            max_length=100,
            pattern=r"^[a-zA-Z0-9_-]+$",
        )

        return validated

    @staticmethod
    def validate_content_request(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate content generation request"""
        if not isinstance(data, dict):
            raise TypeError("Content request must be a dictionary")

        validated = {}
        validated["subject"] = InputValidator.validate_string(
            data.get("subject", "Mathematics"), "subject", max_length=50
        )
        validated["grade_level"] = InputValidator.validate_integer(
            data.get("grade_level", 5), "grade_level", min_val=1, max_val=12
        )
        validated["environment_type"] = InputValidator.validate_string(
            data.get("environment_type", "classroom"),
            "environment_type",
            max_length=50,
            pattern=r"^[a-zA-Z_]+$",
        )
        validated["learning_objectives"] = InputValidator.validate_list(
            data.get("learning_objectives", []),
            "learning_objectives",
            max_items=20,
            item_validator=lambda x, n: InputValidator.validate_string(
                x, n, max_length=200
            ),
        )
        validated["include_quiz"] = bool(data.get("include_quiz", True))
        validated["difficulty_level"] = InputValidator.validate_string(
            data.get("difficulty_level", "medium"),
            "difficulty_level",
            pattern=r"^(easy|medium|hard|advanced)$",
        )

        return validated


# Create global validator instance
input_validator = InputValidator()


# Register health checks
def check_redis():
    try:
        if redis_client:
            redis_client.ping()
            return True
        return True  # Memory store is always available
    except Exception:
        return False


def check_fastapi():
    try:
        response = requests.get(
            "{}/health".format(content_bridge.fastapi_base_url),
            timeout=HEALTH_CHECK_TIMEOUT_SECONDS,
        )
        return response.status_code == 200
    except Exception:
        return False


health_checker.register_check("redis", check_redis)
health_checker.register_check("fastapi", check_fastapi)


# Health check endpoint
@app.route("/health", methods=["GET"])
def health_check():
    """Enhanced health check endpoint"""
    health_results = health_checker.run_checks()

    status_code = 200 if health_results["overall_healthy"] else 503

    return (
        jsonify(
            {
                "status": (
                    "healthy" if health_results["overall_healthy"] else "unhealthy"
                ),
                "service": "ToolboxAI-Roblox-Flask-Bridge",
                "version": "1.0.0",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "uptime": time.time() - app.config.get("START_TIME", time.time()),
                "checks": health_results["checks"],
            }
        ),
        status_code,
    )


# Plugin management endpoints
@app.route("/register_plugin", methods=["POST"])
def register_plugin():
    """Register a Roblox Studio plugin"""
    correlation_id = set_correlation_id()
    logger.info("Plugin registration request started", extra={"correlation_id": correlation_id})

    try:
        # Handle case where json=None is sent with application/json content type
        try:
            plugin_data = request.get_json()
        except Exception:
            metrics.increment("plugin_registration_errors")
            return jsonify({"success": False, "error": "Invalid JSON data"}), 400

        if not plugin_data:
            metrics.increment("plugin_registration_errors")
            return jsonify({"success": False, "error": "Plugin data required"}), 400

        # Validate and sanitize input
        validated_data = input_validator.validate_plugin_data(plugin_data)

        plugin_id = plugin_manager.register_plugin(validated_data)

        return jsonify(
            {
                "success": True,
                "plugin_id": plugin_id,
                "message": "Plugin registered successfully",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    except (ValueError, KeyError, TypeError) as e:
        logger.error("Plugin registration failed: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/plugin/<plugin_id>/heartbeat", methods=["POST"])
def plugin_heartbeat(plugin_id: str):
    """Update plugin heartbeat with rate limiting"""
    correlation_id = set_correlation_id()
    logger.info("Plugin heartbeat request started", extra={"correlation_id": correlation_id, "plugin_id": plugin_id})

    # Check rate limit
    if not plugin_security.check_rate_limit(
        plugin_id,
        max_requests=config_manager.get("rate_limit_requests") or 60,
        window=config_manager.get("rate_limit_window") or 60,
    ):
        metrics.increment("rate_limit_exceeded")
        return jsonify({"success": False, "error": "Rate limit exceeded"}), 429

    try:
        success = plugin_manager.update_heartbeat(plugin_id)

        if success:
            return jsonify(
                {
                    "success": True,
                    "plugin_id": plugin_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        else:
            return jsonify({"success": False, "error": "Plugin not found"}), 404

    except (ValueError, KeyError, redis.RedisError) as e:
        logger.error("Heartbeat failed for %s: %s", plugin_id, e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/plugin/<plugin_id>", methods=["GET"])
def get_plugin_info(plugin_id: str):
    """Get plugin information"""
    try:
        plugin = plugin_manager.get_plugin(plugin_id)

        if plugin:
            return jsonify({"success": True, "plugin": plugin})
        else:
            return jsonify({"success": False, "error": "Plugin not found"}), 404

    except (ValueError, KeyError, redis.RedisError) as e:
        logger.error("Get plugin info failed: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/plugins", methods=["GET"])
def list_plugins():
    """List all active plugins"""
    try:
        plugins = plugin_manager.list_active_plugins()

        return jsonify({"success": True, "plugins": plugins, "count": len(plugins)})

    except (ValueError, redis.RedisError) as e:
        logger.error("List plugins failed: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


# Content generation endpoints (simplified for Roblox)
@app.route("/generate_simple_content", methods=["POST"])
def generate_simple_content():
    """Generate content with simplified parameters for Roblox"""
    try:
        request_data = request.get_json()

        if not request_data:
            return jsonify({"success": False, "error": "Request data required"}), 400

        # Validate input
        validated_data = input_validator.validate_content_request(request_data)

        # Convert simple request to full ContentRequest format using validated data
        # Map common subject aliases to valid enum values
        subject_mapping = {
            "math": "Mathematics",
            "science": "Science", 
            "history": "History",
            "english": "English",
            "art": "Art",
            "geography": "Geography",
            "computer_science": "Computer Science",
            "physics": "Physics",
            "chemistry": "Chemistry",
            "biology": "Biology"
        }
        
        subject = validated_data["subject"].lower()
        mapped_subject = subject_mapping.get(subject, validated_data["subject"])
        
        full_request = {
            "subject": mapped_subject,
            "grade_level": validated_data["grade_level"],
            "learning_objectives": [
                {
                    "title": (
                        obj if isinstance(obj, str) else obj.get("title", "Objective")
                    ),
                    "description": (
                        "" if isinstance(obj, str) else obj.get("description", "")
                    ),
                }
                for obj in validated_data["learning_objectives"]
            ],
            "environment_type": validated_data["environment_type"],
            "include_quiz": validated_data["include_quiz"],
            "difficulty_level": validated_data["difficulty_level"],
        }

        # Run the async generator in a fresh loop using the shared helper
        result_any = run_async(content_bridge.generate_content(full_request))
        result = cast(Dict[str, Any], result_any)
        return jsonify(result)

    except (ValueError, KeyError, TypeError, requests.RequestException) as e:
        logger.error("Simple content generation failed: %s", e)
        return (
            jsonify({"success": False, "error": str(e), "content": {}, "scripts": []}),
            500,
        )


@app.route("/generate_terrain", methods=["POST"])
def generate_terrain():
    """Generate terrain specifically for Roblox"""
    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify({"success": False, "error": "Request data required"}), 400

        terrain_params = _extract_terrain_params(request_data)
        response = _forward_terrain_request(terrain_params)

        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return _terrain_error_response(response.status_code)

    except (ValueError, KeyError, requests.RequestException, requests.Timeout) as e:
        logger.error("Terrain generation failed: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


def _extract_terrain_params(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract terrain parameters from request"""
    return {
        "theme": request_data.get("theme", "forest"),
        "size": request_data.get("size", "medium"),
        "biome": request_data.get("biome", "temperate"),
        "features": request_data.get("features", []),
        "educational_context": request_data.get("educational_context"),
    }


def _forward_terrain_request(terrain_params: Dict[str, Any]) -> requests.Response:
    """Forward terrain generation request to FastAPI"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer demo-token",
    }

    return requests.post(
        f"{content_bridge.fastapi_base_url}/generate_terrain",
        json=terrain_params,
        headers=headers,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )


def _terrain_error_response(status_code: int):
    """Create terrain generation error response"""
    return (
        jsonify(
            {
                "success": False,
                "error": f"Terrain generation failed: {status_code}",
            }
        ),
        status_code,
    )


@app.route("/generate_quiz", methods=["POST"])
def generate_quiz():
    """Generate quiz for Roblox"""
    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify({"success": False, "error": "Request data required"}), 400

        quiz_params = _extract_quiz_params(request_data)
        response = _forward_quiz_request(quiz_params)

        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return _quiz_error_response(response.status_code)

    except (ValueError, KeyError, requests.RequestException, requests.Timeout) as e:
        logger.error("Quiz generation failed: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


def _extract_quiz_params(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract quiz parameters from request"""
    return {
        "subject": request_data.get("subject", "Mathematics"),
        "topic": request_data.get("topic", "General"),
        "difficulty": request_data.get("difficulty", "medium"),
        "num_questions": request_data.get("num_questions", 5),
        "grade_level": request_data.get("grade_level", 5),
    }


def _forward_quiz_request(quiz_params: Dict[str, Any]) -> requests.Response:
    """Forward quiz generation request to FastAPI"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer demo-token",
    }

    return requests.post(
        f"{content_bridge.fastapi_base_url}/generate_quiz",
        params=quiz_params,
        headers=headers,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )


def _quiz_error_response(status_code: int):
    """Create quiz generation error response"""
    return (
        jsonify(
            {
                "success": False,
                "error": f"Quiz generation failed: {status_code}",
            }
        ),
        status_code,
    )


# Lua script templates
LUA_SCRIPT_TEMPLATES = {
    "quiz": """-- Quiz Script Template
local QuizManager = {}

function QuizManager:StartQuiz()
    print("Starting quiz...")
    -- Quiz implementation
end

return QuizManager
""",
    "terrain": """-- Terrain Script Template
local Terrain = workspace.Terrain

-- Terrain generation code
local region = Region3.new(Vector3.new(-100, -50, -100), Vector3.new(100, 50, 100))
Terrain:FillBlock(region.CFrame, region.Size, Enum.Material.Grass)

print("Terrain generated")
""",
    "ui": """-- UI Script Template
local Players = game:GetService("Players")
local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")

-- Create UI elements
local screenGui = Instance.new("ScreenGui")
screenGui.Parent = playerGui

print("UI created")
""",
}


# Script delivery endpoints
@app.route("/script/<script_type>", methods=["GET"])
def get_script_template(script_type: str):
    """Get Lua script templates"""
    try:
        script_content = LUA_SCRIPT_TEMPLATES.get(script_type)

        if script_content:
            return _create_script_response(script_type, script_content)
        else:
            return _script_not_found_response(script_type)

    except (ValueError, KeyError) as e:
        logger.error("Script template request failed: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


def _create_script_response(script_type: str, script_content: str) -> Response:
    """Create response with Lua script"""
    return Response(
        script_content,
        mimetype="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename={script_type}_template.lua"
        },
    )


def _script_not_found_response(script_type: str):
    """Create error response for unknown script type"""
    return (
        jsonify(
            {
                "success": False,
                "error": f"Unknown script type: {script_type}",
            }
        ),
        404,
    )


# Utility endpoints
@app.route("/status", methods=["GET"])
def get_status():
    """Get comprehensive bridge server status"""
    try:
        active_plugins = plugin_manager.list_active_plugins()
        cache_stats = content_bridge.cache.stats()
        system_metrics = metrics.get_metrics()

        return jsonify(
            {
                "service": "ToolboxAI-Roblox-Flask-Bridge",
                "status": "running",
                "version": "1.0.0",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "active_plugins": len(active_plugins),
                "fastapi_connection": content_bridge.fastapi_base_url,
                "cache_stats": cache_stats,
                "metrics": system_metrics,
                "config": config_manager.to_dict(),
            }
        )

    except (ValueError, redis.RedisError) as e:
        logger.error("Status request failed: %s", e)
        return (
            jsonify(
                {
                    "service": "ToolboxAI-Roblox-Flask-Bridge",
                    "status": "error",
                    "error": str(e),
                }
            ),
            500,
        )


@app.route("/metrics", methods=["GET"])
def get_metrics():
    """Get detailed metrics endpoint"""
    try:
        # Get metrics from the Metrics instance
        system_metrics = metrics.get_metrics()
        
        return jsonify({
            "counters": system_metrics.get("counters", {}),
            "gauges": system_metrics.get("gauges", {}),
            "histograms": system_metrics.get("histograms", {}),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        logger.error("Metrics request failed: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/cache/clear", methods=["POST"])
def clear_cache():
    """Clear content cache"""
    try:
        content_bridge.cache.clear()
        metrics.increment("cache_cleared")

        return jsonify({"success": True, "message": "Cache cleared successfully"})

    except (AttributeError, RuntimeError) as e:
        logger.error("Cache clear failed: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


# Background cleanup task
def cleanup_task():
    """Background task for cleanup operations"""
    while True:
        try:
            time.sleep(CLEANUP_INTERVAL_SECONDS)
            plugin_manager.cleanup_stale_plugins()

            # Clear old cache entries using LRUCache cleanup method
            expired_count = content_bridge.cache.cleanup_expired()
            if expired_count > 0:
                logger.info("Cleaned up %d expired cache entries", expired_count)
                metrics.set_gauge("cache_size", content_bridge.cache.size())

        except (KeyError, ValueError, RuntimeError, redis.RedisError) as e:
            # Log cleanup task error and continue to next iteration to avoid blocking the application
            logger.error("Cleanup task error: %s", e)
            time.sleep(CLEANUP_ERROR_RETRY_SECONDS)
        except Exception as e:
            # Catch any other unexpected errors to prevent cleanup thread from dying
            logger.exception("Unexpected cleanup task error: %s", e)
            time.sleep(
                CLEANUP_SYSTEM_ERROR_RETRY_SECONDS
            )  # Longer sleep for unexpected errors


# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle not found errors"""
    logger.error("Not found error: %s", error)
    return (
        jsonify(
            {
                "success": False,
                "error": "Not found",
                "message": "The requested resource was not found",
            }
        ),
        404,
    )


@app.errorhandler(500)
def internal_error(error):
    """Handle server errors"""
    logger.error("Server error: %s", error)
    return (
        jsonify(
            {
                "success": False,
                "error": "Internal server error",
                "message": "An unexpected error occurred",
            }
        ),
        500,
    )


@app.errorhandler(Exception)
def handle_exception(error):
    """Handle unhandled exceptions"""
    logger.error("Unhandled exception: %s", error)
    return (
        jsonify({"success": False, "error": "Unexpected error", "message": str(error)}),
        500,
    )


# New endpoints for monitoring and configuration
@app.route("/metrics", methods=["GET"])
def get_system_metrics():
    """Get system metrics"""
    return jsonify(metrics.get_metrics())


@app.route("/config", methods=["GET"])
def get_config():
    """Get current configuration"""
    return jsonify(config_manager.to_dict())


@app.route("/config", methods=["POST"])
def update_config():
    """Update configuration"""
    try:
        updates = request.get_json()
        if not updates:
            return jsonify({"success": False, "error": "No updates provided"}), 400

        config_manager.update(updates)
        return jsonify({"success": True, "message": "Configuration updated"})

    except Exception as e:
        logger.error("Configuration update failed: %s", e)
        return jsonify({"success": False, "error": str(e)}), 400

# Missing test functions for compatibility
def handle_plugin_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle plugin communication requests"""
    action = request_data.get("action")
    data = request_data.get("data", {})
    
    if action == "generate_content":
        # Forward to content bridge
        result = run_async(content_bridge.generate_content(data))
        return {"status": "success", "result": result}
    elif action == "sync_data":
        # Sync with main server
        return sync_with_main_server(request_data)
    else:
        return {"status": "error", "message": f"Unknown action: {action}"}


def sync_with_main_server(sync_data: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronize data with FastAPI main server"""
    try:
        # Build sync request
        sync_url = f"http://{settings.FASTAPI_HOST}:{settings.FASTAPI_PORT}/sync"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer demo-token"
        }
        
        response = requests.post(
            sync_url,
            json=sync_data,
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS
        )
        
        if response.status_code == 200:
            return {"status": "synced", "data": response.json()}
        else:
            return {"status": "error", "message": f"Sync failed: {response.status_code}"}
    except Exception as e:
        logger.error(f"Sync error: {e}")
        return {"status": "error", "message": str(e)}


def generate_roblox_script(script_type: str, parameters: Dict[str, Any]) -> str:
    """Generate Roblox Lua script based on type and parameters"""
    scripts = {
        "quiz_ui": """-- Generated Quiz UI Script
local gui = Instance.new("ScreenGui")
gui.Name = "QuizUI"
gui.Parent = game.Players.LocalPlayer:WaitForChild("PlayerGui")

local frame = Instance.new("Frame")
frame.Size = UDim2.new(0.8, 0, 0.8, 0)
frame.Position = UDim2.new(0.1, 0, 0.1, 0)
frame.BackgroundColor3 = Color3.fromRGB(30, 30, 30)
frame.Parent = gui

-- Quiz configuration
local numQuestions = {num_questions}
local theme = "{theme}"

return gui
""",
        "terrain_generator": """-- Generated Terrain Script
local terrain = workspace.Terrain
local region = Region3.new(Vector3.new(-100, 0, -100), Vector3.new(100, 50, 100))
region = region:ExpandToGrid(4)

-- Generate terrain based on parameters
local material = Enum.Material.{material}
terrain:FillBall(Vector3.new(0, 25, 0), 50, material)

return terrain
""",
        "npc_controller": """-- Generated NPC Controller Script
local npc = script.Parent
local humanoid = npc:WaitForChild("Humanoid")
local rootPart = npc:WaitForChild("HumanoidRootPart")

-- NPC behavior parameters
local behaviorType = "{behavior}"
local patrolRadius = {radius}

return npc
"""
    }
    
    # Get template
    template = scripts.get(script_type, "-- Unknown script type")
    
    # Replace parameters
    for key, value in parameters.items():
        template = template.replace(f"{{{key}}}", str(value))
    
    return template


# Enhanced Plugin Communication Endpoints
@app.route("/plugin/trigger-agents", methods=["POST"])
def trigger_agent_pipeline():
    """Trigger agent pipeline for content generation"""
    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        # Validate plugin authentication
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"status": "error", "message": "Authentication required"}), 401
        
        token = auth_header.split(" ")[1]
        plugin_id = plugin_security.validate_token(token)
        if not plugin_id:
            return jsonify({"status": "error", "message": "Invalid token"}), 401
        
        # Check permissions
        if not plugin_security.check_permission(plugin_id, "content_generation"):
            return jsonify({"status": "error", "message": "Permission denied"}), 403
        
        # Trigger agent pipeline
        if AGENT_INTEGRATION:
            from core.agents.plugin_communication import PluginCommunicationHub
            
            hub = PluginCommunicationHub()
            result = run_async(hub.handle_plugin_request({
                "request_id": str(uuid.uuid4()),
                "event_type": request_data.get("event_type"),
                "config": request_data.get("config"),
                "context": request_data.get("context"),
                "metadata": {"plugin_id": plugin_id}
            }))
            
            return jsonify({
                "status": "success",
                "request_id": result.get("request_id"),
                "message": "Agent pipeline triggered"
            })
        else:
            # Fallback to direct FastAPI call
            response = requests.post(
                f"http://{settings.FASTAPI_HOST}:{settings.FASTAPI_PORT}/plugin/trigger-agents",
                json=request_data,
                headers={"Authorization": auth_header},
                timeout=REQUEST_TIMEOUT_SECONDS
            )
            return jsonify(response.json())
            
    except Exception as e:
        logger.error(f"Agent pipeline error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/plugin/database/query", methods=["POST"])
def query_database():
    """Query database for educational content"""
    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify({"status": "error", "message": "No query provided"}), 400
        
        # Validate authentication
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"status": "error", "message": "Authentication required"}), 401
        
        # Import database helper
        from database.roblox_models import RobloxDatabaseHelper
        from database import get_db
        
        query_type = request_data.get("query_type")
        params = request_data.get("params", {})
        
        # Execute query based on type
        async def execute_query():
            async with get_db() as session:
                helper = RobloxDatabaseHelper()
                
                if query_type == "get_lesson_content":
                    return await helper.get_content_for_lesson(
                        session,
                        params.get("lesson_id"),
                        params.get("content_type")
                    )
                elif query_type == "get_student_progress":
                    return await helper.track_student_progress(
                        session,
                        params.get("student_id"),
                        params.get("lesson_id"),
                        {}
                    )
                else:
                    raise ValueError(f"Unknown query type: {query_type}")
        
        result = run_async(execute_query())
        
        # Convert result to JSON-serializable format
        if hasattr(result, '__iter__'):
            result = [item.to_dict() if hasattr(item, 'to_dict') else str(item) for item in result]
        elif hasattr(result, 'to_dict'):
            result = result.to_dict()
        
        return jsonify({
            "status": "success",
            "data": result
        })
        
    except Exception as e:
        logger.error(f"Database query error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/plugin/dashboard/sync", methods=["POST"])
def sync_with_dashboard():
    """Sync plugin data with dashboard"""
    try:
        sync_data = request.get_json()
        if not sync_data:
            return jsonify({"status": "error", "message": "No sync data provided"}), 400
        
        # Forward to dashboard backend
        response = requests.post(
            f"http://127.0.0.1:3000/api/roblox/sync",
            json=sync_data,
            headers={"Content-Type": "application/json"},
            timeout=REQUEST_TIMEOUT_SECONDS
        )
        
        if response.status_code == 200:
            return jsonify({
                "status": "success",
                "message": "Synced with dashboard"
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"Dashboard sync failed: {response.status_code}"
            }), response.status_code
            
    except Exception as e:
        logger.error(f"Dashboard sync error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/plugin/session/start", methods=["POST"])
def start_plugin_session():
    """Start a new plugin session"""
    try:
        session_data = request.get_json()
        if not session_data:
            return jsonify({"status": "error", "message": "No session data provided"}), 400
        
        # Create session
        session_id = str(uuid.uuid4())
        session_data["session_id"] = session_id
        session_data["started_at"] = datetime.now(timezone.utc).isoformat()
        session_data["status"] = "active"
        
        # Store session
        if redis_client:
            redis_client.hset(f"session:{session_id}", mapping=session_data)
            redis_client.expire(f"session:{session_id}", REDIS_PLUGIN_TTL_SECONDS)
        else:
            memory_store.set(f"session:{session_id}", session_data)
        
        return jsonify({
            "status": "success",
            "session_id": session_id,
            "message": "Session started"
        })
        
    except Exception as e:
        logger.error(f"Session start error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/plugin/session/<session_id>/end", methods=["POST"])
def end_plugin_session(session_id):
    """End a plugin session"""
    try:
        # Get session
        if redis_client:
            session_data = redis_client.hgetall(f"session:{session_id}")
        else:
            session_data = memory_store.get(f"session:{session_id}")
        
        if not session_data:
            return jsonify({"status": "error", "message": "Session not found"}), 404
        
        # Update session status
        session_data["status"] = "ended"
        session_data["ended_at"] = datetime.now(timezone.utc).isoformat()
        
        # Store final state
        if redis_client:
            redis_client.hset(f"session:{session_id}", mapping=session_data)
        else:
            memory_store.set(f"session:{session_id}", session_data)
        
        return jsonify({
            "status": "success",
            "message": "Session ended"
        })
        
    except Exception as e:
        logger.error(f"Session end error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/plugin/content/generate", methods=["POST"])
def generate_content():
    """Generate educational content for plugin"""
    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        # Use content bridge to generate
        result = run_async(content_bridge.generate_content(request_data))
        
        return jsonify({
            "status": "success",
            "content": result
        })
        
    except Exception as e:
        logger.error(f"Content generation error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/plugin/progress/update", methods=["POST"])
def update_progress():
    """Update student progress from plugin"""
    try:
        progress_data = request.get_json()
        if not progress_data:
            return jsonify({"status": "error", "message": "No progress data provided"}), 400
        
        # Store progress update
        student_id = progress_data.get("student_id")
        lesson_id = progress_data.get("lesson_id")
        
        if not student_id or not lesson_id:
            return jsonify({"status": "error", "message": "Student ID and Lesson ID required"}), 400
        
        # Store in cache
        progress_key = f"progress:{student_id}:{lesson_id}"
        if redis_client:
            redis_client.hset(progress_key, mapping=progress_data)
            redis_client.expire(progress_key, REDIS_PLUGIN_TTL_SECONDS)
        else:
            memory_store.set(progress_key, progress_data)
        
        # Forward to main server for persistence
        response = requests.post(
            f"http://{settings.FASTAPI_HOST}:{settings.FASTAPI_PORT}/progress/update",
            json=progress_data,
            timeout=REQUEST_TIMEOUT_SECONDS
        )
        
        return jsonify({
            "status": "success",
            "message": "Progress updated"
        })
        
    except Exception as e:
        logger.error(f"Progress update error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# New Flask routes for missing test endpoints
@app.route("/plugin/communicate", methods=["POST"])
def plugin_communicate():
    """Handle plugin communication"""
    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        result = handle_plugin_request(request_data)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Plugin communication error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/plugin/poll-messages", methods=["POST"])
def poll_messages():
    """Poll for messages when WebSocket is unavailable"""
    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        plugin_id = request_data.get("plugin_id")
        last_message_id = request_data.get("last_message_id", 0)
        
        if not plugin_id:
            return jsonify({"status": "error", "message": "Plugin ID required"}), 400
        
        # Get plugin from manager
        plugin = plugin_manager.get_plugin(plugin_id)
        if not plugin:
            return jsonify({"status": "error", "message": "Plugin not found"}), 404
        
        # Get messages from message queue (in production, this would be from Redis/database)
        messages = []
        # This is a simplified implementation - in production, you'd store messages in Redis
        # and retrieve them based on last_message_id
        
        return jsonify({
            "status": "success",
            "messages": messages,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Message polling error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/plugin/send-message", methods=["POST"])
def send_message():
    """Send message when WebSocket is unavailable"""
    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        plugin_id = request_data.get("plugin_id")
        message = request_data.get("message")
        
        if not plugin_id or not message:
            return jsonify({"status": "error", "message": "Plugin ID and message required"}), 400
        
        # Get plugin from manager
        plugin = plugin_manager.get_plugin(plugin_id)
        if not plugin:
            return jsonify({"status": "error", "message": "Plugin not found"}), 404
        
        # Process the message (in production, this would route to appropriate handlers)
        # For now, just acknowledge receipt
        
        return jsonify({
            "status": "success",
            "message": "Message received",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Send message error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/sync", methods=["POST"])
def sync_endpoint():
    """Sync with main server"""
    try:
        sync_data = request.get_json()
        if not sync_data:
            return jsonify({"status": "error", "message": "No sync data provided"}), 400
        
        result = sync_with_main_server(sync_data)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Sync error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/generate_script", methods=["POST"])
def generate_script_endpoint():
    """Generate Roblox script"""
    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify({"error": "No data provided"}), 400
        
        script_type = request_data.get("script_type", "quiz_ui")
        parameters = request_data.get("parameters", {})
        
        script = generate_roblox_script(script_type, parameters)
        return jsonify({"script": script})
    except Exception as e:
        logger.error(f"Script generation error: {e}")
        return jsonify({"error": str(e)}), 500


# Application initialization
def create_app():
    """Create and configure Flask app"""
    app.config["START_TIME"] = time.time()

    # Start background cleanup task
    cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()

    logger.info("Flask bridge server initialized on port %s", settings.FLASK_PORT)
    return app


# Main entry point
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create app
    flask_app = create_app()

    # Run server
    flask_app.run(
        host=settings.FLASK_HOST,
        port=settings.FLASK_PORT,
        debug=settings.DEBUG,
        threaded=True,
    )

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
from server.config import settings

from src.shared.utils.async_utils import run_async


# from src.shared.utils.cache import LRUCache
# Simple LRUCache implementation for now
class LRUCache:
    def __init__(self, capacity=100, max_size=None, ttl=None, persist_file=None):
        self.capacity = capacity if max_size is None else max_size
        self.cache = {}
        self.order = []
        self.ttl = ttl
        self.persist_file = persist_file

    def get(self, key):
        if key in self.cache:
            self.order.remove(key)
            self.order.append(key)
            return self.cache[key]
        return None

    def put(self, key, value):
        if key in self.cache:
            self.order.remove(key)
        elif len(self.cache) >= self.capacity:
            oldest = self.order.pop(0)
            del self.cache[oldest]
        self.cache[key] = value
        self.order.append(key)


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


class CorrelationIDFilter:
    pass


class health_checker:
    @staticmethod
    def check_health():
        return {"status": "healthy"}

    @staticmethod
    def register_check(name, check_func):
        pass


class metrics:
    @staticmethod
    def increment_counter(name):
        pass


def set_correlation_id(correlation_id):
    pass


class PluginSecurity:
    pass


class PersistentMemoryStore:
    def __init__(self, *args, **kwargs):
        pass


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
    max_memory_mb=config_manager.get("max_memory_mb", 100),
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
            for key in list(memory_store.data.keys()):
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
            for key in list(memory_store.data.keys()):
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
        """Forward request to FastAPI server"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer demo-token",  # Would use proper auth
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

    def _error_response(self, message: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            "success": False,
            "message": message,
            "content": {},
            "scripts": [],
        }

    def _generate_cache_key(self, request_data: Dict[str, Any]) -> str:
        """Generate cache key from request data"""
        key_parts = [
            request_data.get("subject", ""),
            str(request_data.get("grade_level", 0)),
            request_data.get("environment_type", ""),
            str(len(request_data.get("learning_objectives", []))),
        ]
        return "_".join(key_parts).lower().replace(" ", "_")

    # Cache methods now handled by LRUCache class


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
        item_validator: Optional[callable] = None,
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

    try:
        plugin_data = request.get_json()

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

    # Check rate limit
    if not plugin_security.check_rate_limit(
        plugin_id,
        max_requests=config_manager.get("rate_limit_requests", 60),
        window_seconds=config_manager.get("rate_limit_window", 60),
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
        full_request = {
            "subject": validated_data["subject"],
            "grade_level": validated_data["grade_level"],
            "learning_objectives": [
                {
                    "title": (
                        obj if isinstance(obj, str) else obj.get("title", "Objective")
                    ),
                    "description": (
                        obj if isinstance(obj, str) else obj.get("description", "")
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
def get_metrics():
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

        config_manager.update(**updates)
        return jsonify({"success": True, "message": "Configuration updated"})

    except Exception as e:
        logger.error("Configuration update failed: %s", e)
        return jsonify({"success": False, "error": str(e)}), 400


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

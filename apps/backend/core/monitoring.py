"""
Sentry Configuration and Helper Functions

Provides comprehensive Sentry integration for the ToolboxAI FastAPI application including:
- Performance monitoring and profiling
- Error tracking with context enrichment
- Custom breadcrumbs and tags
- User context management
- Production-ready configuration
"""

import functools
import json
import logging
import socket
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from ..config import settings

logger = logging.getLogger(__name__)


class SentryManager:
    """Centralized Sentry management and configuration"""
    
    def __init__(self):
        self.initialized = False
        self.config = None
        
    def initialize(self, dsn: Optional[str] = None, **kwargs) -> bool:
        """Initialize Sentry SDK with comprehensive configuration"""
        try:
            # Use provided DSN or get from settings
            sentry_dsn = dsn or settings.SENTRY_DSN
            
            # If no DSN provided, set default for production
            if not sentry_dsn:
                if settings.ENVIRONMENT == "production":
                    sentry_dsn = "https://af64bfdc2bd0cd6cd870bfeb7f26c22c@o4509912543199232.ingest.us.sentry.io/4509991438581760"
                else:
                    logger.info("Sentry DSN not configured, skipping initialization")
                    return False
            
            # Get Sentry configuration from settings
            sentry_config = settings.get_sentry_config()
            sentry_config.update(kwargs)  # Allow overrides
            
            # Configure integrations
            integrations = [
                FastApiIntegration(),
                StarletteIntegration(),
                SqlalchemyIntegration(),
                LoggingIntegration(
                    level=logging.INFO,  # Capture info and above
                    event_level=logging.ERROR  # Send error and above as events
                ),
            ]
            
            # Add Redis integration if available
            try:
                from sentry_sdk.integrations.redis import RedisIntegration
                integrations.append(RedisIntegration())
            except (ImportError, AttributeError):
                logger.warning("Redis integration not available in this Sentry SDK version")
            
            # Initialize Sentry SDK
            sentry_sdk.init(
                dsn=sentry_dsn,
                environment=sentry_config["environment"],
                release=sentry_config["release"],
                server_name=sentry_config["server_name"] or socket.gethostname(),
                integrations=integrations,
                traces_sample_rate=sentry_config["traces_sample_rate"],
                profiles_sample_rate=sentry_config["profiles_sample_rate"],
                send_default_pii=sentry_config["send_default_pii"],
                attach_stacktrace=True,
                max_breadcrumbs=50,
                debug=settings.DEBUG,
                before_send=self._before_send_filter,
                before_send_transaction=self._before_send_transaction_filter,
            )
            
            # Set default tags
            sentry_sdk.set_tag("service", "toolboxai-fastapi")
            sentry_sdk.set_tag("environment", settings.ENVIRONMENT)
            sentry_sdk.set_tag("version", settings.APP_VERSION)
            sentry_sdk.set_tag("component", "api-server")
            
            # Set initial context
            sentry_sdk.set_context("application", {
                "name": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "environment": settings.ENVIRONMENT,
                "debug": settings.DEBUG,
            })
            
            sentry_sdk.set_context("server", {
                "host": settings.FASTAPI_HOST,
                "port": settings.FASTAPI_PORT,
                "hostname": socket.gethostname(),
            })
            
            self.config = sentry_config
            self.initialized = True
            
            # Test Sentry connection
            self.add_breadcrumb(
                message="Sentry initialized successfully",
                category="sentry",
                level="info"
            )
            
            logger.info(f"Sentry initialized successfully for environment: {settings.ENVIRONMENT}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Sentry: {e}")
            self.initialized = False
            return False
    
    def _before_send_filter(self, event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Filter and modify events before sending to Sentry"""
        try:
            # Skip certain errors in production
            if settings.ENVIRONMENT == "production":
                if "exc_info" in hint:
                    exc_type = hint["exc_info"][0].__name__ if hint["exc_info"] else None
                    
                    # Skip common client errors
                    if exc_type in ["ValidationError", "HTTPException"]:
                        if event.get("level") in ["info", "warning"]:
                            return None
            
            # Add custom context
            event.setdefault("extra", {}).update({
                "server_time": datetime.utcnow().isoformat(),
                "settings_environment": settings.ENVIRONMENT,
                "debug_mode": settings.DEBUG,
            })
            
            # Sanitize sensitive data
            self._sanitize_event_data(event)
            
            return event
            
        except Exception as e:
            logger.error(f"Error in Sentry before_send filter: {e}")
            return event
    
    def _before_send_transaction_filter(self, event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Filter transactions before sending to Sentry"""
        try:
            # Skip health check transactions in production
            if settings.ENVIRONMENT == "production":
                transaction_name = event.get("transaction", "")
                if transaction_name in ["/health", "/metrics", "/ping"]:
                    return None
            
            # Add performance context
            event.setdefault("extra", {}).update({
                "performance_monitoring": True,
                "environment": settings.ENVIRONMENT,
            })
            
            return event
            
        except Exception as e:
            logger.error(f"Error in Sentry transaction filter: {e}")
            return event
    
    def _sanitize_event_data(self, event: Dict[str, Any]):
        """Sanitize sensitive data from Sentry events"""
        sensitive_keys = {
            "password", "token", "secret", "api_key", "authorization", 
            "cookie", "session", "csrf", "jwt", "bearer"
        }
        
        def sanitize_dict(data: Dict[str, Any]):
            for key, value in list(data.items()):
                if isinstance(key, str) and any(sensitive in key.lower() for sensitive in sensitive_keys):
                    data[key] = "[Filtered]"
                elif isinstance(value, dict):
                    sanitize_dict(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            sanitize_dict(item)
        
        # Sanitize various event sections
        for section in ["request", "extra", "contexts", "tags"]:
            if section in event and isinstance(event[section], dict):
                sanitize_dict(event[section])
    
    def set_user_context(self, user_id: str, username: str = None, email: str = None, **kwargs):
        """Set user context for error tracking"""
        if not self.initialized:
            return
        
        user_data = {
            "id": user_id,
            "username": username,
            "email": email,
        }
        user_data.update(kwargs)
        
        # Remove None values
        user_data = {k: v for k, v in user_data.items() if v is not None}
        
        sentry_sdk.set_user(user_data)
    
    def clear_user_context(self):
        """Clear user context"""
        if not self.initialized:
            return
        
        sentry_sdk.set_user({})
    
    def set_request_context(self, request_id: str, method: str, path: str, **kwargs):
        """Set request context for tracking"""
        if not self.initialized:
            return
        
        context_data = {
            "request_id": request_id,
            "method": method,
            "path": path,
            "timestamp": datetime.utcnow().isoformat(),
        }
        context_data.update(kwargs)
        
        sentry_sdk.set_context("request", context_data)
    
    def add_breadcrumb(self, message: str, category: str = "default", level: str = "info", data: Dict[str, Any] = None):
        """Add custom breadcrumb for debugging"""
        if not self.initialized:
            return
        
        sentry_sdk.add_breadcrumb(
            message=message,
            category=category,
            level=level,
            data=data or {},
            timestamp=datetime.utcnow()
        )
    
    def set_tag(self, key: str, value: str):
        """Set custom tag"""
        if not self.initialized:
            return
        
        sentry_sdk.set_tag(key, value)
    
    def set_tags(self, tags: Dict[str, str]):
        """Set multiple custom tags"""
        if not self.initialized:
            return
        
        for key, value in tags.items():
            sentry_sdk.set_tag(key, str(value))
    
    def set_context(self, name: str, data: Dict[str, Any]):
        """Set custom context"""
        if not self.initialized:
            return
        
        sentry_sdk.set_context(name, data)
    
    def capture_exception(self, exception: Exception, **kwargs) -> Optional[str]:
        """Capture exception with context"""
        if not self.initialized:
            logger.error(f"Exception (Sentry disabled): {exception}")
            return None
        
        return sentry_sdk.capture_exception(exception, **kwargs)
    
    def capture_message(self, message: str, level: str = "info", **kwargs) -> Optional[str]:
        """Capture custom message"""
        if not self.initialized:
            logger.log(getattr(logging, level.upper(), logging.INFO), message)
            return None
        
        return sentry_sdk.capture_message(message, level=level, **kwargs)
    
    def start_transaction(self, name: str, op: str = "http.request", **kwargs):
        """Start a performance transaction"""
        if not self.initialized:
            return None
        
        return sentry_sdk.start_transaction(name=name, op=op, **kwargs)
    
    def start_span(self, op: str, description: str = None, **kwargs):
        """Start a performance span"""
        if not self.initialized:
            return None
        
        return sentry_sdk.start_span(op=op, description=description, **kwargs)


# Global Sentry manager instance
sentry_manager = SentryManager()


def sentry_performance_monitor(operation: str = None, description: str = None):
    """Decorator for monitoring function performance with Sentry"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not sentry_manager.initialized:
                return await func(*args, **kwargs)
            
            op = operation or f"function.{func.__name__}"
            desc = description or f"Execution of {func.__name__}"
            
            with sentry_manager.start_span(op=op, description=desc):
                try:
                    result = await func(*args, **kwargs)
                    sentry_manager.add_breadcrumb(
                        message=f"Function {func.__name__} completed successfully",
                        category="function",
                        level="info"
                    )
                    return result
                except Exception as e:
                    sentry_manager.add_breadcrumb(
                        message=f"Function {func.__name__} failed",
                        category="function",
                        level="error",
                        data={"error": str(e)}
                    )
                    sentry_manager.capture_exception(e)
                    raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not sentry_manager.initialized:
                return func(*args, **kwargs)
            
            op = operation or f"function.{func.__name__}"
            desc = description or f"Execution of {func.__name__}"
            
            with sentry_manager.start_span(op=op, description=desc):
                try:
                    result = func(*args, **kwargs)
                    sentry_manager.add_breadcrumb(
                        message=f"Function {func.__name__} completed successfully",
                        category="function",
                        level="info"
                    )
                    return result
                except Exception as e:
                    sentry_manager.add_breadcrumb(
                        message=f"Function {func.__name__} failed",
                        category="function",
                        level="error",
                        data={"error": str(e)}
                    )
                    sentry_manager.capture_exception(e)
                    raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def sentry_database_monitor(operation: str = None):
    """Decorator for monitoring database operations"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if not sentry_manager.initialized:
                return await func(*args, **kwargs)
            
            op = operation or f"db.{func.__name__}"
            
            with sentry_manager.start_span(op=op, description=f"Database operation: {func.__name__}"):
                try:
                    result = await func(*args, **kwargs)
                    sentry_manager.set_tag("db_operation", "success")
                    return result
                except Exception as e:
                    sentry_manager.set_tag("db_operation", "error")
                    sentry_manager.capture_exception(e)
                    raise
        
        return wrapper
    return decorator


def sentry_external_api_monitor(service_name: str):
    """Decorator for monitoring external API calls"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if not sentry_manager.initialized:
                return await func(*args, **kwargs)
            
            with sentry_manager.start_span(op="http.client", description=f"External API call to {service_name}"):
                try:
                    sentry_manager.set_tag("external_service", service_name)
                    result = await func(*args, **kwargs)
                    sentry_manager.add_breadcrumb(
                        message=f"External API call to {service_name} succeeded",
                        category="http",
                        level="info"
                    )
                    return result
                except Exception as e:
                    sentry_manager.add_breadcrumb(
                        message=f"External API call to {service_name} failed",
                        category="http",
                        level="error",
                        data={"error": str(e), "service": service_name}
                    )
                    sentry_manager.capture_exception(e)
                    raise
        
        return wrapper
    return decorator


def configure_sentry_logging():
    """Configure Python logging to integrate with Sentry"""
    if not sentry_manager.initialized:
        return
    
    # Configure root logger to send logs to Sentry
    root_logger = logging.getLogger()
    
    # Add Sentry handler for errors
    class SentryLogHandler(logging.Handler):
        def emit(self, record):
            if record.levelno >= logging.ERROR:
                # Extract exception info if available
                exc_info = getattr(record, 'exc_info', None)
                
                # Add log record as breadcrumb
                sentry_manager.add_breadcrumb(
                    message=record.getMessage(),
                    category="log",
                    level="error" if record.levelno >= logging.ERROR else "info",
                    data={
                        "logger": record.name,
                        "level": record.levelname,
                        "module": record.module,
                        "function": record.funcName,
                        "line": record.lineno,
                    }
                )
                
                if exc_info:
                    sentry_manager.capture_exception(exc_info[1])
                else:
                    sentry_manager.capture_message(record.getMessage(), level="error")
    
    # Add handler only if Sentry is properly configured
    if settings.SENTRY_ENABLE_LOGS:
        sentry_handler = SentryLogHandler()
        sentry_handler.setLevel(logging.ERROR)
        root_logger.addHandler(sentry_handler)


def initialize_sentry(dsn: Optional[str] = None) -> bool:
    """Initialize Sentry SDK with production-ready configuration"""
    return sentry_manager.initialize(dsn)


# Context managers for Sentry operations
class SentryTransactionContext:
    """Context manager for Sentry transactions"""
    
    def __init__(self, name: str, op: str = "http.request"):
        self.name = name
        self.op = op
        self.transaction = None
    
    def __enter__(self):
        if sentry_manager.initialized:
            self.transaction = sentry_manager.start_transaction(name=self.name, op=self.op)
        return self.transaction
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.transaction:
            if exc_type:
                sentry_manager.set_tag("transaction_status", "error")
                sentry_manager.capture_exception(exc_val)
            else:
                sentry_manager.set_tag("transaction_status", "success")
            self.transaction.finish()


class SentrySpanContext:
    """Context manager for Sentry spans"""
    
    def __init__(self, op: str, description: str = None):
        self.op = op
        self.description = description
        self.span = None
    
    def __enter__(self):
        if sentry_manager.initialized:
            self.span = sentry_manager.start_span(op=self.op, description=self.description)
        return self.span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            if exc_type:
                sentry_manager.capture_exception(exc_val)
            self.span.finish()


# Utility functions
def capture_educational_content_error(content_request: Dict[str, Any], error: Exception, user_id: str = None):
    """Capture educational content generation errors with context"""
    if not sentry_manager.initialized:
        return
    
    sentry_manager.set_context("content_generation", {
        "subject": content_request.get("subject"),
        "grade_level": content_request.get("grade_level"),
        "learning_objectives": content_request.get("learning_objectives"),
        "environment_type": content_request.get("environment_type"),
    })
    
    if user_id:
        sentry_manager.set_tag("user_id", user_id)
    
    sentry_manager.capture_exception(error)


def capture_roblox_plugin_error(plugin_id: str, action: str, error: Exception):
    """Capture Roblox plugin errors with context"""
    if not sentry_manager.initialized:
        return
    
    sentry_manager.set_context("roblox_plugin", {
        "plugin_id": plugin_id,
        "action": action,
        "timestamp": datetime.utcnow().isoformat(),
    })
    
    sentry_manager.set_tag("component", "roblox_plugin")
    sentry_manager.capture_exception(error)


def capture_agent_system_error(agent_name: str, task_type: str, error: Exception):
    """Capture agent system errors with context"""
    if not sentry_manager.initialized:
        return
    
    sentry_manager.set_context("agent_system", {
        "agent": agent_name,
        "task_type": task_type,
        "timestamp": datetime.utcnow().isoformat(),
    })
    
    sentry_manager.set_tag("component", "ai_agents")
    sentry_manager.capture_exception(error)


# Export main functions and classes
__all__ = [
    "sentry_manager",
    "initialize_sentry",
    "configure_sentry_logging",
    "sentry_performance_monitor",
    "sentry_database_monitor",
    "sentry_external_api_monitor",
    "SentryTransactionContext",
    "SentrySpanContext",
    "capture_educational_content_error",
    "capture_roblox_plugin_error",
    "capture_agent_system_error",
]
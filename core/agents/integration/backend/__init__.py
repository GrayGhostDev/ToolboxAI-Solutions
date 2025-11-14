"""
Backend Integration Agents

This module provides agents for backend system integration including:
- API Gateway management
- Database synchronization
- Authentication and authorization
- Service discovery and health monitoring
"""

from .api_gateway_agent import APIEndpoint, APIGatewayAgent, APIMetrics, APIVersion

# Import other agents when available
_available_exports = ["APIGatewayAgent", "APIEndpoint", "APIVersion", "APIMetrics"]

try:
    from .database_sync_agent import DatabaseSyncAgent

    _available_exports.append("DatabaseSyncAgent")
except ImportError:
    pass

try:
    from .authentication_agent import AuthenticationAgent

    _available_exports.append("AuthenticationAgent")
except ImportError:
    pass

try:
    from .service_discovery_agent import ServiceDiscoveryAgent

    _available_exports.append("ServiceDiscoveryAgent")
except ImportError:
    pass

__all__ = _available_exports

"""
Backend Integration Agents

This module provides agents for backend system integration including:
- API Gateway management
- Database synchronization
- Authentication and authorization
- Service discovery and health monitoring
"""

from .api_gateway_agent import APIGatewayAgent, APIEndpoint, APIVersion, APIMetrics

# Import other agents when available
try:
    from .database_sync_agent import DatabaseSyncAgent
except ImportError:
    pass

try:
    from .authentication_agent import AuthenticationAgent
except ImportError:
    pass

try:
    from .service_discovery_agent import ServiceDiscoveryAgent
except ImportError:
    pass

__all__ = [
    "APIGatewayAgent",
    "APIEndpoint",
    "APIVersion",
    "APIMetrics",
    "DatabaseSyncAgent",
    "AuthenticationAgent",
    "ServiceDiscoveryAgent"
]
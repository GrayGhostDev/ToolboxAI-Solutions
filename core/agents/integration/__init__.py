"""
Integration Agent Swarm - Multi-platform integration for ToolboxAI Educational Platform

This module provides a comprehensive set of AI agents for seamless integration
across Backend, Frontend/Dashboard, and Roblox/Studio components.
"""

from .base_integration_agent import (
    BaseIntegrationAgent,
    IntegrationPlatform,
    IntegrationEvent,
    CircuitBreaker,
    CircuitBreakerState,
    IntegrationMetrics
)

# Import backend agents when available
try:
    from .backend import (
        APIGatewayAgent,
        DatabaseSyncAgent,
        AuthenticationAgent,
        ServiceDiscoveryAgent
    )
except ImportError:
    pass  # Agents not yet implemented

# Import frontend agents when available
try:
    from .frontend import (
        UISyncAgent,
        RealtimeUpdateAgent,
        ComponentGeneratorAgent,
        StateManagementAgent
    )
except ImportError:
    pass

# Import Roblox agents when available
try:
    from .roblox import (
        StudioBridgeAgent,
        AssetDeploymentAgent,
        GameInstanceAgent,
        EducationalContentIntegrationAgent
    )
except ImportError:
    pass

# Import orchestration agents when available
try:
    from .orchestration import (
        IntegrationCoordinator,
        ErrorRecoveryAgent,
        PerformanceMonitorAgent,
        DeploymentPipelineAgent
    )
except ImportError:
    pass

# Import data flow agents when available
try:
    from .data_flow import (
        SchemaValidatorAgent,
        EventBusAgent,
        CacheInvalidationAgent,
        ConflictResolutionAgent
    )
except ImportError:
    pass


__all__ = [
    # Base classes
    "BaseIntegrationAgent",
    "IntegrationPlatform",
    "IntegrationEvent",
    "CircuitBreaker",
    "CircuitBreakerState",
    "IntegrationMetrics",

    # Backend agents
    "APIGatewayAgent",
    "DatabaseSyncAgent",
    "AuthenticationAgent",
    "ServiceDiscoveryAgent",

    # Frontend agents
    "UISyncAgent",
    "RealtimeUpdateAgent",
    "ComponentGeneratorAgent",
    "StateManagementAgent",

    # Roblox agents
    "StudioBridgeAgent",
    "AssetDeploymentAgent",
    "GameInstanceAgent",
    "EducationalContentIntegrationAgent",

    # Orchestration agents
    "IntegrationCoordinator",
    "ErrorRecoveryAgent",
    "PerformanceMonitorAgent",
    "DeploymentPipelineAgent",

    # Data flow agents
    "SchemaValidatorAgent",
    "EventBusAgent",
    "CacheInvalidationAgent",
    "ConflictResolutionAgent"
]
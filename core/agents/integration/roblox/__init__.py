"""
Roblox Integration Agents

This module provides agents for Roblox/Studio integration including:
- Studio communication bridge
- Asset deployment management
- Game instance coordination
- Educational content integration
"""

from .studio_bridge_agent import (
    StudioBridgeAgent,
    StudioSession,
    StudioConnectionType,
    CommandType,
    ScriptSync,
    PluginCommand
)

# Import other agents when available
try:
    from .asset_deployment_agent import AssetDeploymentAgent
except ImportError:
    pass

try:
    from .game_instance_agent import GameInstanceAgent
except ImportError:
    pass

try:
    from .educational_content_agent import EducationalContentIntegrationAgent
except ImportError:
    pass

__all__ = [
    # Studio Bridge
    "StudioBridgeAgent",
    "StudioSession",
    "StudioConnectionType",
    "CommandType",
    "ScriptSync",
    "PluginCommand",

    # Asset Deployment (future)
    "AssetDeploymentAgent",

    # Game Instance (future)
    "GameInstanceAgent",

    # Educational Content (future)
    "EducationalContentIntegrationAgent"
]
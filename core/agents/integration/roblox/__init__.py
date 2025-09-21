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

# Track available exports dynamically
_available_exports = [
    "StudioBridgeAgent",
    "StudioSession",
    "StudioConnectionType",
    "CommandType",
    "ScriptSync",
    "PluginCommand"
]

# Import other agents when available
try:
    from .asset_deployment_agent import AssetDeploymentAgent
    _available_exports.append("AssetDeploymentAgent")
except ImportError:
    pass

try:
    from .game_instance_agent import GameInstanceAgent
    _available_exports.append("GameInstanceAgent")
except ImportError:
    pass

try:
    from .educational_content_agent import EducationalContentIntegrationAgent
    _available_exports.append("EducationalContentIntegrationAgent")
except ImportError:
    pass

__all__ = _available_exports
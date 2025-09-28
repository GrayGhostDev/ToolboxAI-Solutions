"""
Roblox Integration Module

This module handles all Roblox-related functionality including:
- WebSocket communication with Roblox Studio/Games
- Content generation and deployment
- Script validation and security
- Terrain and environment generation
"""

from typing import TYPE_CHECKING

# Import from the main roblox_server module
if TYPE_CHECKING:
    from roblox_server import RobloxServer, RobloxMessage, RobloxContentRequest, roblox_server


# For runtime imports
def get_roblox_server():
    """Get the global Roblox server instance"""
    from roblox_server import roblox_server

    return roblox_server


__all__ = [
    "get_roblox_server",
]

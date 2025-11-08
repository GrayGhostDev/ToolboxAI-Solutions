"""Roblox-specific agents module - Compatibility shim"""
import logging

logger = logging.getLogger(__name__)

__all__ = [
    'RobloxAnalyticsAgent',
    'RobloxAssetManagementAgent',
    'RobloxTestingAgent',
]

# These are placeholders for Roblox-specific agents
# Actual implementations would be added here when needed

logger.info("Roblox agents module initialized")

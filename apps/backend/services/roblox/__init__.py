"""
Roblox Integration Module for ToolBoxAI Educational Platform

Comprehensive Roblox integration system with Flask bridge, OAuth2 authentication,
AI-powered content generation, deployment pipeline, and real-time communication.

Features:
- Flask bridge server for Roblox Studio plugin communication (port 5001)
- OAuth2 2.0 authentication with PKCE flow
- Rojo 7.5.1 integration for Studio file synchronization
- Open Cloud API v2 client for asset management and DataStore operations
- AI-powered content generation with LangChain
- Content transformation pipeline (AI → Luau/Roblox format)
- Redis-based deployment queue with retry logic
- Pusher real-time events and notifications
- Comprehensive error handling and monitoring

Integration Layers:
1. Plugin Communication: Flask bridge for Roblox Studio plugin
2. API Services: OAuth2, Open Cloud, Rojo integration
3. Content & Deployment: AI agent, content bridge, deployment pipeline
4. Real-time: Pusher-based event system

Author: ToolBoxAI Team
Created: 2025-11-10
Version: 1.0.0
"""

# Flask Bridge Server (Port 5001)
from .bridge import (
    app as roblox_bridge_app,
    PluginManager,
    ContentBridge,
    PluginSecurity,
    PersistentMemoryStore,
)

# Authentication (OAuth2 with PKCE)
from .auth import (
    RobloxOAuth2Service,
    OAuth2Config,
    TokenResponse,
    UserInfo,
    roblox_auth_service,  # Singleton instance
)

# AI Agent (LangChain-powered)
from .ai_agent import (
    RobloxAIAgent,
    roblox_ai_agent,  # Singleton instance
)

# Content Pipeline (AI → Roblox transformation)
from .content_bridge import (
    RobloxContentBridge,
    RobloxAssetConverter,
    LuauScriptGenerator,
    RobloxAsset,
    RobloxAssetType,
    RobloxContentType,
)

# Deployment Pipeline (Redis queue-based)
from .deployment import (
    RobloxDeploymentPipeline,
    RobloxAssetManager,
    DeploymentStatus,
    ContentType,
    DeploymentRequest,
    DeploymentResult,
    AssetMetadata,
    AssetBundle,
)

# Rojo Integration (Studio sync)
from .rojo_manager import (
    EnhancedRojoManager,
    RojoProject,
    RojoProjectConfig,
    RojoSyncStatus,
)

# Open Cloud API Client (v2)
from .open_cloud import (
    OpenCloudAPIClient,
    AssetType,
    CreationContext,
    AssetDescription,
    DataStoreEntry,
    MessagingServiceMessage,
    PlacePublishRequest,
)

# Roblox Service Wrapper (Simple API wrapper)
from .service import (
    RobloxService,
    roblox_service,  # Singleton instance
)

# Real-time Communication (Pusher)
from .pusher import (
    RobloxPusherService,
    get_roblox_pusher_service,
    RobloxChannelType,
    RobloxEventType,
    PusherEvent,
)

__all__ = [
    # Flask Bridge (Port 5001)
    "roblox_bridge_app",
    "PluginManager",
    "ContentBridge",
    "PluginSecurity",
    "PersistentMemoryStore",

    # Authentication
    "RobloxOAuth2Service",
    "roblox_auth_service",
    "OAuth2Config",
    "TokenResponse",
    "UserInfo",

    # AI Agent
    "RobloxAIAgent",
    "roblox_ai_agent",

    # Content Pipeline
    "RobloxContentBridge",
    "RobloxAssetConverter",
    "LuauScriptGenerator",
    "RobloxAsset",
    "RobloxAssetType",
    "RobloxContentType",

    # Deployment
    "RobloxDeploymentPipeline",
    "RobloxAssetManager",
    "DeploymentStatus",
    "ContentType",
    "DeploymentRequest",
    "DeploymentResult",
    "AssetMetadata",
    "AssetBundle",

    # Rojo Integration
    "EnhancedRojoManager",
    "RojoProject",
    "RojoProjectConfig",
    "RojoSyncStatus",

    # Open Cloud API
    "OpenCloudAPIClient",
    "AssetType",
    "CreationContext",
    "AssetDescription",
    "DataStoreEntry",
    "MessagingServiceMessage",
    "PlacePublishRequest",

    # Service Wrapper
    "RobloxService",
    "roblox_service",

    # Real-time
    "RobloxPusherService",
    "get_roblox_pusher_service",
    "RobloxChannelType",
    "RobloxEventType",
    "PusherEvent",
]

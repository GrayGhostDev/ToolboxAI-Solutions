"""
Frontend Integration Agents

This module provides agents for frontend/dashboard integration including:
- UI state synchronization
- Real-time update management
- Component generation
- State management coordination
"""

from .ui_sync_agent import (
    UISyncAgent,
    UIComponent,
    ComponentType,
    UIUpdateStrategy,
    UIStateSnapshot,
    UIUpdateBatch
)

from .realtime_update_agent import (
    RealtimeUpdateAgent,
    Channel,
    ChannelType,
    ConnectionState,
    RealtimeMessage,
    ConnectionMetrics,
    MessageQueue
)

# Import other agents when available
try:
    from .component_generator_agent import ComponentGeneratorAgent
except ImportError:
    pass

try:
    from .state_management_agent import StateManagementAgent
except ImportError:
    pass

__all__ = [
    # UI Sync
    "UISyncAgent",
    "UIComponent",
    "ComponentType",
    "UIUpdateStrategy",
    "UIStateSnapshot",
    "UIUpdateBatch",

    # Realtime Updates
    "RealtimeUpdateAgent",
    "Channel",
    "ChannelType",
    "ConnectionState",
    "RealtimeMessage",
    "ConnectionMetrics",
    "MessageQueue",

    # Component Generation (future)
    "ComponentGeneratorAgent",

    # State Management (future)
    "StateManagementAgent"
]
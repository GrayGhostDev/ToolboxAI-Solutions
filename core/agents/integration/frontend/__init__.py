"""
Frontend Integration Agents

This module provides agents for frontend/dashboard integration including:
- UI state synchronization
- Real-time update management
- Component generation
- State management coordination
"""

from .realtime_update_agent import (
    Channel,
    ChannelType,
    ConnectionMetrics,
    ConnectionState,
    MessageQueue,
    RealtimeMessage,
    RealtimeUpdateAgent,
)
from .ui_sync_agent import (
    ComponentType,
    UIComponent,
    UIStateSnapshot,
    UISyncAgent,
    UIUpdateBatch,
    UIUpdateStrategy,
)

# Track available exports dynamically
_available_exports = [
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
]

# Import other agents when available
try:
    from .component_generator_agent import ComponentGeneratorAgent

    _available_exports.append("ComponentGeneratorAgent")
except ImportError:
    pass

try:
    from .state_management_agent import StateManagementAgent

    _available_exports.append("StateManagementAgent")
except ImportError:
    pass

__all__ = _available_exports

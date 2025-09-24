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

# Track available exports dynamically
_available_exports = [
    "BaseIntegrationAgent",
    "IntegrationPlatform",
    "IntegrationEvent",
    "CircuitBreaker",
    "CircuitBreakerState",
    "IntegrationMetrics"
]

# Import backend agents when available
try:
    from .backend import *
    import importlib
    backend_module = importlib.import_module('.backend', __name__)
    _available_exports.extend(getattr(backend_module, '__all__', []))
except ImportError:
    pass  # Agents not yet implemented

# Import frontend agents when available
try:
    from .frontend import *
    import importlib
    frontend_module = importlib.import_module('.frontend', __name__)
    _available_exports.extend(getattr(frontend_module, '__all__', []))
except ImportError:
    pass

# Import Roblox agents when available
try:
    from .roblox import *
    import importlib
    roblox_module = importlib.import_module('.roblox', __name__)
    _available_exports.extend(getattr(roblox_module, '__all__', []))
except ImportError:
    pass

# Import orchestration agents when available
try:
    from .orchestration import *
    import importlib
    orchestration_module = importlib.import_module('.orchestration', __name__)
    _available_exports.extend(getattr(orchestration_module, '__all__', []))
except ImportError:
    pass

# Import data flow agents when available
try:
    from .data_flow import *
    import importlib
    data_flow_module = importlib.import_module('.data_flow', __name__)
    _available_exports.extend(getattr(data_flow_module, '__all__', []))
except ImportError:
    pass

__all__ = _available_exports
"""
Orchestration Integration Agents

This module provides agents for cross-platform orchestration including:
- Integration workflow coordination
- Error recovery and fault tolerance
- Performance monitoring and optimization
- Deployment pipeline management
"""

from .integration_coordinator import (
    IntegrationCoordinator,
    IntegrationTask,
    IntegrationWorkflow,
    TaskPriority,
    WorkflowStatus,
)

# Track available exports dynamically
_available_exports = [
    "IntegrationCoordinator",
    "IntegrationWorkflow",
    "IntegrationTask",
    "WorkflowStatus",
    "TaskPriority"
]

# Import other agents when available
try:
    from .error_recovery_agent import ErrorRecoveryAgent
    _available_exports.append("ErrorRecoveryAgent")
except ImportError:
    pass

try:
    from .performance_monitor_agent import PerformanceMonitorAgent
    _available_exports.append("PerformanceMonitorAgent")
except ImportError:
    pass

try:
    from .deployment_pipeline_agent import DeploymentPipelineAgent
    _available_exports.append("DeploymentPipelineAgent")
except ImportError:
    pass

__all__ = _available_exports
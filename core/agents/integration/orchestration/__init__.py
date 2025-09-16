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
    IntegrationWorkflow,
    IntegrationTask,
    WorkflowStatus,
    TaskPriority
)

# Import other agents when available
try:
    from .error_recovery_agent import ErrorRecoveryAgent
except ImportError:
    pass

try:
    from .performance_monitor_agent import PerformanceMonitorAgent
except ImportError:
    pass

try:
    from .deployment_pipeline_agent import DeploymentPipelineAgent
except ImportError:
    pass

__all__ = [
    "IntegrationCoordinator",
    "IntegrationWorkflow",
    "IntegrationTask",
    "WorkflowStatus",
    "TaskPriority",
    "ErrorRecoveryAgent",
    "PerformanceMonitorAgent",
    "DeploymentPipelineAgent"
]
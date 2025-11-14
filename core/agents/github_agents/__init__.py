"""
GitHub Agent System for Large File Management and Repository Health.

This system provides automated agents to:
- Detect and handle large files
- Migrate files to Git LFS
- Monitor repository health
- Optimize assets before commit
- Prepare for deployment
- Scan dependencies for security vulnerabilities and license compliance
- Analyze test coverage and generate coverage reports
- Optimize build processes, Docker images, and cache efficiency
- Validate environment configurations and deployment readiness
- Manage deployment rollbacks and failure recovery
- Monitor CI/CD pipeline performance and provide optimization insights
"""

from .asset_optimization_agent import AssetOptimizationAgent
from .base_github_agent import BaseGitHubAgent
from .build_optimization_agent import BuildOptimizationAgent
from .dependency_security_agent import DependencySecurityAgent
from .deployment_prep_agent import DeploymentPrepAgent
from .environment_validation_agent import EnvironmentValidationAgent
from .error_recovery import ErrorRecoveryAgent
from .git_lfs_migration_agent import GitLFSMigrationAgent
from .large_file_detection_agent import LargeFileDetectionAgent
from .monitoring import GitHubAgentMonitoring
from .orchestrator import GitHubAgentOrchestrator
from .pipeline_monitoring_agent import PipelineMonitoringAgent
# from .orchestrator import GitHubAgentOrchestrator  # Archived - now in core.orchestration.github module
from .resource_monitor_agent import ResourceMonitorAgent
from .rollback_management_agent import RollbackManagementAgent

# from .worktree_orchestrator_agent import WorktreeOrchestratorAgent  # Archived - now in orchestration module
from .session_manager_agent import SessionManagerAgent
from .test_coverage_agent import TestCoverageAgent

__all__ = [
    "BaseGitHubAgent",
    "LargeFileDetectionAgent",
    "GitLFSMigrationAgent",
    "RepoHealthMonitorAgent",
    "AssetOptimizationAgent",
    "DeploymentPrepAgent",
    "DependencySecurityAgent",
    "TestCoverageAgent",
    "BuildOptimizationAgent",
    "EnvironmentValidationAgent",
    "RollbackManagementAgent",
    # "GitHubAgentOrchestrator",  # Archived - now in core.orchestration.github module
    "GitHubAgentOrchestrator",
    "ErrorRecoveryAgent",
    "GitHubAgentMonitoring",
    # "WorktreeOrchestratorAgent",  # Archived
    "SessionManagerAgent",
    "ResourceMonitorAgent",
]

__version__ = "1.0.0"

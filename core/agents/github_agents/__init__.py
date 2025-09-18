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

from .base_github_agent import BaseGitHubAgent
from .large_file_detection_agent import LargeFileDetectionAgent
from .git_lfs_migration_agent import GitLFSMigrationAgent
from .repo_health_monitor_agent import RepoHealthMonitorAgent
from .asset_optimization_agent import AssetOptimizationAgent
from .deployment_prep_agent import DeploymentPrepAgent
from .dependency_security_agent import DependencySecurityAgent
from .test_coverage_agent import TestCoverageAgent
from .build_optimization_agent import BuildOptimizationAgent
from .environment_validation_agent import EnvironmentValidationAgent
from .rollback_management_agent import RollbackManagementAgent
from .pipeline_monitoring_agent import PipelineMonitoringAgent
from .orchestrator import GitHubAgentOrchestrator
from .error_recovery import ErrorRecoveryAgent
from .monitoring import GitHubAgentMonitoring
from .worktree_orchestrator_agent import WorktreeOrchestratorAgent
from .session_manager_agent import SessionManagerAgent
from .resource_monitor_agent import ResourceMonitorAgent

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
    "PipelineMonitoringAgent",
    "GitHubAgentOrchestrator",
    "ErrorRecoveryAgent",
    "GitHubAgentMonitoring",
    "WorktreeOrchestratorAgent",
    "SessionManagerAgent",
    "ResourceMonitorAgent",
]

__version__ = "1.0.0"
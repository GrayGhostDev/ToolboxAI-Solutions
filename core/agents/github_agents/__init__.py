"""
GitHub Agent System for Large File Management and Repository Health.

This system provides automated agents to:
- Detect and handle large files
- Migrate files to Git LFS
- Monitor repository health
- Optimize assets before commit
- Prepare for deployment
"""

from .base_github_agent import BaseGitHubAgent
from .large_file_detection_agent import LargeFileDetectionAgent
from .git_lfs_migration_agent import GitLFSMigrationAgent
from .repo_health_monitor_agent import RepoHealthMonitorAgent
from .asset_optimization_agent import AssetOptimizationAgent
from .deployment_prep_agent import DeploymentPrepAgent
from .orchestrator import GitHubAgentOrchestrator
from .error_recovery import ErrorRecoveryAgent
from .monitoring import GitHubAgentMonitoring

__all__ = [
    "BaseGitHubAgent",
    "LargeFileDetectionAgent",
    "GitLFSMigrationAgent",
    "RepoHealthMonitorAgent",
    "AssetOptimizationAgent",
    "DeploymentPrepAgent",
    "GitHubAgentOrchestrator",
    "ErrorRecoveryAgent",
    "GitHubAgentMonitoring",
]

__version__ = "1.0.0"
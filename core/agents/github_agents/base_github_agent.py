"""
Base class for GitHub agents.
"""

import asyncio
import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from core.agents.base_agent import BaseAgent, AgentConfig

logger = logging.getLogger(__name__)


class BaseGitHubAgent(BaseAgent, ABC):
    """Base class for all GitHub management agents."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the GitHub agent.

        Args:
            config_path: Path to configuration file
        """
        # Create a proper AgentConfig object for BaseAgent
        agent_config = AgentConfig(
            name=self.__class__.__name__,
            model="gpt-3.5-turbo",  # Not used, but required
            temperature=0.1,  # Low temperature for deterministic behavior
            verbose=False,
            memory_enabled=False,  # GitHub agents don't need memory
            system_prompt=f"You are a {self.__class__.__name__} that helps manage GitHub repositories."
        )
        super().__init__(agent_config)
        self.config = self._load_config(config_path)
        self.metrics = {
            "operations_performed": 0,
            "errors_encountered": 0,
            "files_processed": 0,
            "start_time": datetime.now()
        }

    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load agent configuration from file.

        Args:
            config_path: Path to configuration file

        Returns:
            Configuration dictionary
        """
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__),
                "../../../config/github_agents.yaml"
            )

        if not os.path.exists(config_path):
            logger.warning(f"Config file not found at {config_path}, using defaults")
            return self._get_default_config()

        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config.get('github_agents', {})
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration.

        Returns:
            Default configuration dictionary
        """
        return {
            "large_file_detection": {
                "size_thresholds": {
                    "warning_mb": 25,
                    "critical_mb": 50,
                    "github_limit_mb": 100
                },
                "exempt_patterns": [
                    ".git/",
                    "node_modules/",
                    "__pycache__/",
                    "venv/"
                ]
            },
            "monitoring": {
                "enabled": True,
                "log_level": "INFO"
            }
        }

    async def execute_git_command(self, command: str) -> Dict[str, Any]:
        """Execute a git command and return the result.

        Args:
            command: Git command to execute

        Returns:
            Dictionary with command output and status
        """
        try:
            process = await asyncio.create_subprocess_shell(
                f"git {command}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            return {
                "success": process.returncode == 0,
                "stdout": stdout.decode('utf-8'),
                "stderr": stderr.decode('utf-8'),
                "command": command
            }
        except Exception as e:
            logger.error(f"Error executing git command: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": command
            }

    def get_repository_root(self) -> Optional[Path]:
        """Get the root directory of the git repository.

        Returns:
            Path to repository root or None if not in a git repo
        """
        try:
            result = os.popen("git rev-parse --show-toplevel").read().strip()
            if result:
                return Path(result)
        except Exception as e:
            logger.error(f"Error finding repository root: {e}")
        return None

    def format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format.

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted size string
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def update_metrics(self, **kwargs):
        """Update agent metrics.

        Args:
            **kwargs: Metric updates
        """
        for key, value in kwargs.items():
            if key in self.metrics:
                if isinstance(self.metrics[key], int):
                    self.metrics[key] += value
                else:
                    self.metrics[key] = value

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of agent metrics.

        Returns:
            Metrics summary dictionary
        """
        runtime = (datetime.now() - self.metrics["start_time"]).total_seconds()
        return {
            **self.metrics,
            "runtime_seconds": runtime,
            "success_rate": (
                (self.metrics["operations_performed"] - self.metrics["errors_encountered"])
                / max(self.metrics["operations_performed"], 1) * 100
            )
        }

    async def log_operation(self, operation: str, details: Dict[str, Any]):
        """Log an operation for auditing.

        Args:
            operation: Operation name
            details: Operation details
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": self.__class__.__name__,
            "operation": operation,
            "details": details
        }
        logger.info(f"Operation: {json.dumps(log_entry, indent=2)}")

        # Optionally write to audit log file
        log_dir = Path("logs/github_agents")
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"{self.__class__.__name__}_{datetime.now().strftime('%Y%m%d')}.json"

        try:
            if log_file.exists():
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []

            logs.append(log_entry)

            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)
        except Exception as e:
            logger.error(f"Error writing to audit log: {e}")

    @abstractmethod
    async def analyze(self, **kwargs) -> Dict[str, Any]:
        """Perform analysis specific to this agent.

        Args:
            **kwargs: Analysis parameters

        Returns:
            Analysis results
        """
        pass

    @abstractmethod
    async def execute_action(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute a specific action.

        Args:
            action: Action to execute
            **kwargs: Action parameters

        Returns:
            Action results
        """
        pass

    async def validate_environment(self) -> Dict[str, bool]:
        """Validate that the environment is properly configured.

        Returns:
            Validation results
        """
        validations = {}

        # Check git is available
        git_result = await self.execute_git_command("--version")
        validations["git_available"] = git_result["success"]

        # Check we're in a git repository
        repo_root = self.get_repository_root()
        validations["in_git_repo"] = repo_root is not None

        # Check for required directories
        if repo_root:
            validations["logs_directory"] = (repo_root / "logs").exists()

        return validations

    async def _process_task(self, state: Dict[str, Any]) -> Any:
        """Process the task - delegates to analyze or execute_action.

        Args:
            state: Current task state

        Returns:
            Processed result
        """
        # Default implementation that delegates to analyze
        return await self.analyze(**state)
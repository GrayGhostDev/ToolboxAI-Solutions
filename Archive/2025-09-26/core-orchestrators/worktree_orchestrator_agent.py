"""
Worktree Orchestrator Agent for managing parallel Claude Code sessions.

This agent orchestrates multiple git worktrees to enable concurrent development
with parallel Claude Code sessions, following Anthropic's best practices.
"""

import asyncio
import json
import logging
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .base_github_agent import BaseGitHubAgent

logger = logging.getLogger(__name__)


@dataclass
class WorktreeConfig:
    """Configuration for a worktree."""
    branch_name: str
    worktree_path: Path
    backend_port: int
    frontend_port: int
    redis_db: int
    created_at: datetime
    last_accessed: datetime
    status: str = "active"
    claude_session_active: bool = False
    services_running: Dict[str, bool] = field(default_factory=dict)
    resource_usage: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorktreeMetrics:
    """Metrics for worktree operations."""
    total_worktrees: int = 0
    active_sessions: int = 0
    total_commits: int = 0
    total_runtime_hours: float = 0.0
    peak_concurrent_sessions: int = 0
    average_session_duration: float = 0.0
    resource_efficiency: float = 0.0


class WorktreeOrchestratorAgent(BaseGitHubAgent):
    """Orchestrates multiple git worktrees for parallel Claude Code sessions."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the worktree orchestrator agent.

        Args:
            config_path: Path to configuration file
        """
        super().__init__(config_path)
        self.repo_root = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions")
        self.worktrees_dir = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions-worktrees")
        self.session_log = self.worktrees_dir / ".sessions.log"
        self.config_file = self.worktrees_dir / ".worktree-config.yaml"

        # Port allocation
        self.backend_port_start = 8008
        self.frontend_port_start = 5179
        self.port_range = 20

        # Active worktrees
        self.worktrees: Dict[str, WorktreeConfig] = {}

        # Metrics
        self.metrics = WorktreeMetrics()

        # Initialize worktree directory
        self._initialize_worktree_directory()

    def _initialize_worktree_directory(self) -> None:
        """Initialize the worktree directory structure."""
        self.worktrees_dir.mkdir(parents=True, exist_ok=True)

        # Create default configuration if it doesn't exist
        if not self.config_file.exists():
            default_config = {
                "worktrees": {
                    "max_parallel": 10,
                    "auto_cleanup": True,
                    "cleanup_after_days": 7
                },
                "port_allocation": {
                    "backend_start": self.backend_port_start,
                    "frontend_start": self.frontend_port_start,
                    "range": self.port_range
                },
                "resources": {
                    "max_memory_per_worktree": "4GB",
                    "max_cpu_per_worktree": 2
                },
                "defaults": {
                    "branch_prefix": "worktree",
                    "auto_install_deps": True,
                    "copy_env_files": True
                }
            }

            import yaml
            with open(self.config_file, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False)

    async def analyze(self, files: List[str]) -> Dict[str, Any]:
        """Analyze files (required by BaseGitHubAgent).

        Args:
            files: List of files to analyze

        Returns:
            Analysis results
        """
        # Not needed for worktree orchestration
        return {"message": "Worktree orchestrator doesn't analyze files"}

    async def execute_action(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an action (required by BaseGitHubAgent).

        Args:
            action: Action to execute
            context: Action context

        Returns:
            Action result
        """
        # Delegate to execute method
        task = context.copy()
        task["action"] = action
        return await self.execute(task)

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute worktree orchestration task.

        Args:
            task: Task configuration with action and parameters

        Returns:
            Result of the orchestration task
        """
        action = task.get("action", "status")

        try:
            if action == "create":
                return await self.create_worktree(
                    branch_name=task.get("branch_name"),
                    launch_claude=task.get("launch_claude", False)
                )
            elif action == "remove":
                return await self.remove_worktree(
                    branch_name=task.get("branch_name")
                )
            elif action == "list":
                return await self.list_worktrees()
            elif action == "status":
                return await self.get_status()
            elif action == "cleanup":
                return await self.cleanup_old_worktrees(
                    days=task.get("days", 7)
                )
            elif action == "optimize":
                return await self.optimize_resources()
            elif action == "launch_claude":
                return await self.launch_claude_session(
                    branch_name=task.get("branch_name")
                )
            elif action == "coordinate":
                return await self.coordinate_sessions(
                    tasks=task.get("tasks", [])
                )
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
        except Exception as e:
            logger.error(f"Error executing worktree task: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def create_worktree(
        self,
        branch_name: str,
        launch_claude: bool = False
    ) -> Dict[str, Any]:
        """Create a new worktree.

        Args:
            branch_name: Name of the branch for the worktree
            launch_claude: Whether to launch Claude Code session

        Returns:
            Creation result with worktree details
        """
        logger.info(f"Creating worktree for branch: {branch_name}")

        # Find available ports
        backend_port = await self._find_available_port(self.backend_port_start)
        frontend_port = await self._find_available_port(self.frontend_port_start)
        redis_db = await self._allocate_redis_db()

        # Create worktree path
        worktree_path = self.worktrees_dir / branch_name

        # Create git worktree
        cmd = [
            "git", "worktree", "add",
            "-b", branch_name,
            str(worktree_path),
            "HEAD"
        ]

        result = subprocess.run(
            cmd,
            cwd=str(self.repo_root),
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": f"Failed to create worktree: {result.stderr}"
            }

        # Create worktree configuration
        config = WorktreeConfig(
            branch_name=branch_name,
            worktree_path=worktree_path,
            backend_port=backend_port,
            frontend_port=frontend_port,
            redis_db=redis_db,
            created_at=datetime.now(),
            last_accessed=datetime.now()
        )

        # Set up environment
        await self._setup_worktree_environment(config)

        # Store configuration
        self.worktrees[branch_name] = config

        # Log session creation
        self._log_session_event("CREATE", branch_name, config)

        # Update metrics
        self.metrics.total_worktrees += 1
        self.metrics.peak_concurrent_sessions = max(
            self.metrics.peak_concurrent_sessions,
            len(self.worktrees)
        )

        # Launch Claude if requested
        if launch_claude:
            await self.launch_claude_session(branch_name)

        return {
            "success": True,
            "worktree": {
                "branch": branch_name,
                "path": str(worktree_path),
                "backend_port": backend_port,
                "frontend_port": frontend_port,
                "redis_db": redis_db
            },
            "message": f"Worktree created successfully at {worktree_path}"
        }

    async def remove_worktree(self, branch_name: str) -> Dict[str, Any]:
        """Remove a worktree.

        Args:
            branch_name: Name of the branch to remove

        Returns:
            Removal result
        """
        logger.info(f"Removing worktree: {branch_name}")

        if branch_name not in self.worktrees:
            return {
                "success": False,
                "error": f"Worktree not found: {branch_name}"
            }

        config = self.worktrees[branch_name]

        # Stop services
        await self._stop_worktree_services(config)

        # Remove git worktree
        cmd = ["git", "worktree", "remove", str(config.worktree_path), "--force"]
        result = subprocess.run(
            cmd,
            cwd=str(self.repo_root),
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            logger.warning(f"Git worktree removal warning: {result.stderr}")

        # Clean up directory if it still exists
        if config.worktree_path.exists():
            import shutil
            shutil.rmtree(config.worktree_path)

        # Remove from active worktrees
        del self.worktrees[branch_name]

        # Log removal
        self._log_session_event("REMOVE", branch_name, config)

        return {
            "success": True,
            "message": f"Worktree {branch_name} removed successfully"
        }

    async def list_worktrees(self) -> Dict[str, Any]:
        """List all active worktrees.

        Returns:
            List of worktree configurations
        """
        # Update worktree status
        await self._update_worktree_status()

        worktree_list = []
        for branch_name, config in self.worktrees.items():
            worktree_list.append({
                "branch": branch_name,
                "path": str(config.worktree_path),
                "backend_port": config.backend_port,
                "frontend_port": config.frontend_port,
                "status": config.status,
                "claude_active": config.claude_session_active,
                "services": config.services_running,
                "created_at": config.created_at.isoformat(),
                "last_accessed": config.last_accessed.isoformat()
            })

        return {
            "success": True,
            "worktrees": worktree_list,
            "total": len(worktree_list),
            "active_sessions": sum(1 for w in self.worktrees.values() if w.claude_session_active)
        }

    async def get_status(self) -> Dict[str, Any]:
        """Get overall worktree system status.

        Returns:
            System status including metrics and resource usage
        """
        # Update status
        await self._update_worktree_status()

        # Calculate resource usage
        total_memory = 0
        total_cpu = 0
        for config in self.worktrees.values():
            if config.resource_usage:
                total_memory += config.resource_usage.get("memory", 0)
                total_cpu += config.resource_usage.get("cpu", 0)

        # Available ports
        available_backend_ports = await self._count_available_ports(
            self.backend_port_start,
            self.port_range
        )
        available_frontend_ports = await self._count_available_ports(
            self.frontend_port_start,
            self.port_range
        )

        return {
            "success": True,
            "status": {
                "total_worktrees": len(self.worktrees),
                "active_sessions": sum(1 for w in self.worktrees.values() if w.claude_session_active),
                "running_services": sum(
                    len([s for s in w.services_running.values() if s])
                    for w in self.worktrees.values()
                ),
                "available_backend_ports": available_backend_ports,
                "available_frontend_ports": available_frontend_ports,
                "resource_usage": {
                    "total_memory_mb": total_memory,
                    "total_cpu_percent": total_cpu
                },
                "metrics": {
                    "total_worktrees_created": self.metrics.total_worktrees,
                    "peak_concurrent_sessions": self.metrics.peak_concurrent_sessions,
                    "average_session_duration_hours": self.metrics.average_session_duration
                }
            }
        }

    async def cleanup_old_worktrees(self, days: int = 7) -> Dict[str, Any]:
        """Clean up worktrees older than specified days.

        Args:
            days: Number of days to keep worktrees

        Returns:
            Cleanup result
        """
        logger.info(f"Cleaning up worktrees older than {days} days")

        cutoff_date = datetime.now() - timedelta(days=days)
        removed = []

        for branch_name, config in list(self.worktrees.items()):
            if config.last_accessed < cutoff_date:
                result = await self.remove_worktree(branch_name)
                if result["success"]:
                    removed.append(branch_name)

        return {
            "success": True,
            "removed": removed,
            "count": len(removed),
            "message": f"Removed {len(removed)} old worktrees"
        }

    async def optimize_resources(self) -> Dict[str, Any]:
        """Optimize resource allocation for worktrees.

        Returns:
            Optimization results
        """
        logger.info("Optimizing worktree resources")

        optimizations = []

        # Stop services for inactive worktrees
        for branch_name, config in self.worktrees.items():
            if not config.claude_session_active and config.services_running:
                await self._stop_worktree_services(config)
                optimizations.append(f"Stopped services for inactive worktree: {branch_name}")

        # Clean up abandoned worktrees
        for branch_name, config in list(self.worktrees.items()):
            if config.status == "abandoned":
                await self.remove_worktree(branch_name)
                optimizations.append(f"Removed abandoned worktree: {branch_name}")

        # Compact port allocation
        await self._compact_port_allocation()

        return {
            "success": True,
            "optimizations": optimizations,
            "message": f"Applied {len(optimizations)} optimizations"
        }

    async def launch_claude_session(self, branch_name: str) -> Dict[str, Any]:
        """Launch Claude Code session in a worktree.

        Args:
            branch_name: Branch name of the worktree

        Returns:
            Launch result
        """
        if branch_name not in self.worktrees:
            return {
                "success": False,
                "error": f"Worktree not found: {branch_name}"
            }

        config = self.worktrees[branch_name]

        # Create launch script
        launch_script = config.worktree_path / ".claude-launch.sh"
        launch_script.write_text(f"""#!/bin/bash
cd {config.worktree_path}
export WORKTREE_NAME={branch_name}
export BACKEND_PORT={config.backend_port}
export FRONTEND_PORT={config.frontend_port}
claude --continue
""")
        launch_script.chmod(0o755)

        # Launch in terminal (macOS specific)
        cmd = f"""osascript -e '
        tell application "Terminal"
            do script "cd \\"{config.worktree_path}\\" && ./.claude-launch.sh"
            activate
        end tell
        '"""

        subprocess.run(cmd, shell=True)

        # Update configuration
        config.claude_session_active = True
        config.last_accessed = datetime.now()

        # Log event
        self._log_session_event("LAUNCH_CLAUDE", branch_name, config)

        return {
            "success": True,
            "message": f"Claude Code session launched for {branch_name}"
        }

    async def coordinate_sessions(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Coordinate multiple Claude sessions for parallel work.

        Args:
            tasks: List of tasks to distribute across sessions

        Returns:
            Coordination result
        """
        logger.info(f"Coordinating {len(tasks)} tasks across worktrees")

        results = []

        for task in tasks:
            # Find or create worktree for task
            branch_name = task.get("branch", f"task-{task.get('id', 'unknown')}")

            if branch_name not in self.worktrees:
                create_result = await self.create_worktree(branch_name, launch_claude=True)
                if not create_result["success"]:
                    results.append({
                        "task": task,
                        "success": False,
                        "error": create_result.get("error")
                    })
                    continue

            # Assign task to worktree
            config = self.worktrees[branch_name]

            # Create task file for Claude
            task_file = config.worktree_path / ".claude-task.md"
            task_content = f"""# Task: {task.get('name', 'Unnamed Task')}

## Description
{task.get('description', 'No description provided')}

## Requirements
{json.dumps(task.get('requirements', []), indent=2)}

## Context
- Branch: {branch_name}
- Backend Port: {config.backend_port}
- Frontend Port: {config.frontend_port}

## Instructions
Please complete this task in the current worktree.
"""
            task_file.write_text(task_content)

            results.append({
                "task": task,
                "success": True,
                "worktree": branch_name,
                "message": f"Task assigned to worktree: {branch_name}"
            })

        # Update metrics
        self.metrics.active_sessions = len([w for w in self.worktrees.values() if w.claude_session_active])

        return {
            "success": True,
            "results": results,
            "active_worktrees": len(self.worktrees),
            "message": f"Coordinated {len(tasks)} tasks across worktrees"
        }

    async def _find_available_port(self, start_port: int) -> int:
        """Find an available port starting from the given port.

        Args:
            start_port: Starting port number

        Returns:
            Available port number
        """
        import socket

        for port in range(start_port, start_port + self.port_range):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(("127.0.0.1", port))
                    return port
                except OSError:
                    continue

        raise RuntimeError(f"No available ports in range {start_port}-{start_port + self.port_range}")

    async def _allocate_redis_db(self) -> int:
        """Allocate a Redis database number.

        Returns:
            Redis database number
        """
        used_dbs = {config.redis_db for config in self.worktrees.values()}

        for db in range(1, 16):
            if db not in used_dbs:
                return db

        # If all are used, return a random one
        import random
        return random.randint(1, 15)

    async def _setup_worktree_environment(self, config: WorktreeConfig) -> None:
        """Set up the environment for a worktree.

        Args:
            config: Worktree configuration
        """
        # Create environment file
        env_file = config.worktree_path / ".env.worktree"
        env_content = f"""# Worktree environment configuration
WORKTREE_NAME={config.branch_name}
BACKEND_PORT={config.backend_port}
FRONTEND_PORT={config.frontend_port}
REDIS_DB={config.redis_db}
LOG_DIR={config.worktree_path}/logs
CACHE_DIR={config.worktree_path}/.cache
"""
        env_file.write_text(env_content)

        # Copy main .env files
        main_env = self.repo_root / ".env"
        if main_env.exists():
            import shutil
            shutil.copy(main_env, config.worktree_path / ".env.main")

        # Create necessary directories
        (config.worktree_path / "logs").mkdir(exist_ok=True)
        (config.worktree_path / ".cache").mkdir(exist_ok=True)

    async def _stop_worktree_services(self, config: WorktreeConfig) -> None:
        """Stop all services for a worktree.

        Args:
            config: Worktree configuration
        """
        # Kill processes on worktree ports
        for port in [config.backend_port, config.frontend_port]:
            cmd = f"lsof -ti:$port | xargs kill -9 2>/dev/null || true"
            subprocess.run(cmd, shell=True)

        config.services_running = {}

    async def _update_worktree_status(self) -> None:
        """Update the status of all worktrees."""
        for branch_name, config in self.worktrees.items():
            # Check if path exists
            if not config.worktree_path.exists():
                config.status = "missing"
                continue

            # Check services
            config.services_running = {
                "backend": await self._is_port_in_use(config.backend_port),
                "frontend": await self._is_port_in_use(config.frontend_port)
            }

            # Check Claude session
            cmd = f"pgrep -f 'claude.*{config.worktree_path}'"
            result = subprocess.run(cmd, shell=True, capture_output=True)
            config.claude_session_active = result.returncode == 0

            # Update status
            if config.claude_session_active:
                config.status = "active"
            elif any(config.services_running.values()):
                config.status = "running"
            else:
                config.status = "idle"

    async def _is_port_in_use(self, port: int) -> bool:
        """Check if a port is in use.

        Args:
            port: Port number to check

        Returns:
            True if port is in use
        """
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return False
            except OSError:
                return True

    async def _count_available_ports(self, start: int, count: int) -> int:
        """Count available ports in a range.

        Args:
            start: Starting port
            count: Number of ports to check

        Returns:
            Number of available ports
        """
        available = 0
        for port in range(start, start + count):
            if not await self._is_port_in_use(port):
                available += 1
        return available

    async def _compact_port_allocation(self) -> None:
        """Compact port allocation to free up port ranges."""
        # This would reassign ports to use lower numbers first
        # Implementation depends on specific requirements
        pass

    def _log_session_event(self, event: str, branch_name: str, config: WorktreeConfig) -> None:
        """Log a session event.

        Args:
            event: Event type
            branch_name: Branch name
            config: Worktree configuration
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp}|{event}|{branch_name}|{config.worktree_path}|backend:{config.backend_port}|frontend:{config.frontend_port}\n"

        with open(self.session_log, "a") as f:
            f.write(log_entry)

    def get_report(self) -> Dict[str, Any]:
        """Generate a report of worktree orchestration activities.

        Returns:
            Report data
        """
        return {
            "agent": "WorktreeOrchestratorAgent",
            "status": "operational",
            "worktrees": {
                "total": len(self.worktrees),
                "active": sum(1 for w in self.worktrees.values() if w.status == "active"),
                "idle": sum(1 for w in self.worktrees.values() if w.status == "idle")
            },
            "metrics": {
                "total_created": self.metrics.total_worktrees,
                "peak_concurrent": self.metrics.peak_concurrent_sessions,
                "active_sessions": self.metrics.active_sessions
            },
            "resources": {
                "ports_in_use": {
                    "backend": len([w for w in self.worktrees.values() if w.services_running.get("backend")]),
                    "frontend": len([w for w in self.worktrees.values() if w.services_running.get("frontend")])
                }
            }
        }
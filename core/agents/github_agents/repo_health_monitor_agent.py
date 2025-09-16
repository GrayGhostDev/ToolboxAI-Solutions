"""
Repository Health Monitor Agent for tracking repository metrics.
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base_github_agent import BaseGitHubAgent


class RepoHealthMonitorAgent(BaseGitHubAgent):
    """Agent that monitors repository health and metrics."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the repository health monitor agent."""
        super().__init__(config_path)
        self.health_config = self.config.get('monitoring', {}).get('health_checks', {})
        self.thresholds = {
            'repo_size_warning_gb': self.health_config.get('repo_size_warning_gb', 1),
            'repo_size_critical_gb': self.health_config.get('repo_size_critical_gb', 5),
            'file_count_warning': self.health_config.get('file_count_warning', 50000),
            'file_count_critical': self.health_config.get('file_count_critical', 100000),
            'max_file_depth': self.health_config.get('max_file_depth', 20)
        }

    async def analyze(self, detailed: bool = True) -> Dict[str, Any]:
        """Analyze repository health.

        Args:
            detailed: Whether to perform detailed analysis

        Returns:
            Health analysis results
        """
        repo_root = self.get_repository_root()
        if not repo_root:
            return {"success": False, "error": "Not in a git repository"}

        health_data = {
            "timestamp": datetime.now().isoformat(),
            "repository_path": str(repo_root),
            "metrics": {},
            "issues": [],
            "recommendations": [],
            "overall_status": "healthy"
        }

        # Collect metrics
        health_data["metrics"]["size"] = await self._analyze_repository_size()
        health_data["metrics"]["files"] = await self._analyze_file_metrics()
        health_data["metrics"]["git"] = await self._analyze_git_metrics()
        health_data["metrics"]["dependencies"] = await self._analyze_dependencies()

        if detailed:
            health_data["metrics"]["performance"] = await self._analyze_performance()
            health_data["metrics"]["security"] = await self._analyze_security()

        # Evaluate health status
        health_data = self._evaluate_health_status(health_data)

        # Generate recommendations
        health_data["recommendations"] = self._generate_health_recommendations(health_data)

        await self.log_operation("health_check", {
            "status": health_data["overall_status"],
            "issues_count": len(health_data["issues"])
        })

        return health_data

    async def _analyze_repository_size(self) -> Dict[str, Any]:
        """Analyze repository size metrics.

        Returns:
            Size metrics
        """
        metrics = {
            "total_size_bytes": 0,
            "git_size_bytes": 0,
            "working_tree_size_bytes": 0
        }

        repo_root = self.get_repository_root()

        # Get total repository size
        try:
            total_size = 0
            for path in repo_root.rglob("*"):
                if path.is_file():
                    total_size += path.stat().st_size
            metrics["total_size_bytes"] = total_size
            metrics["total_size_formatted"] = self.format_size(total_size)
        except Exception as e:
            logger.error(f"Error calculating repository size: {e}")

        # Get .git directory size
        git_dir = repo_root / ".git"
        if git_dir.exists():
            try:
                git_size = 0
                for path in git_dir.rglob("*"):
                    if path.is_file():
                        git_size += path.stat().st_size
                metrics["git_size_bytes"] = git_size
                metrics["git_size_formatted"] = self.format_size(git_size)
            except Exception as e:
                logger.error(f"Error calculating .git size: {e}")

        metrics["working_tree_size_bytes"] = metrics["total_size_bytes"] - metrics["git_size_bytes"]
        metrics["working_tree_size_formatted"] = self.format_size(metrics["working_tree_size_bytes"])

        return metrics

    async def _analyze_file_metrics(self) -> Dict[str, Any]:
        """Analyze file-related metrics.

        Returns:
            File metrics
        """
        metrics = {
            "total_files": 0,
            "total_directories": 0,
            "max_depth": 0,
            "file_types": {},
            "largest_files": []
        }

        repo_root = self.get_repository_root()

        # Count files and directories
        file_sizes = []
        for path in repo_root.rglob("*"):
            if ".git" in path.parts:
                continue

            if path.is_file():
                metrics["total_files"] += 1
                size = path.stat().st_size
                file_sizes.append((path, size))

                # Track file types
                ext = path.suffix
                if ext:
                    metrics["file_types"][ext] = metrics["file_types"].get(ext, 0) + 1

                # Track depth
                depth = len(path.relative_to(repo_root).parts)
                metrics["max_depth"] = max(metrics["max_depth"], depth)

            elif path.is_dir():
                metrics["total_directories"] += 1

        # Get largest files
        file_sizes.sort(key=lambda x: x[1], reverse=True)
        for path, size in file_sizes[:10]:
            metrics["largest_files"].append({
                "path": str(path.relative_to(repo_root)),
                "size": self.format_size(size)
            })

        return metrics

    async def _analyze_git_metrics(self) -> Dict[str, Any]:
        """Analyze git-related metrics.

        Returns:
            Git metrics
        """
        metrics = {
            "branch_count": 0,
            "current_branch": "",
            "commit_count": 0,
            "contributors": 0,
            "last_commit": None,
            "uncommitted_changes": False,
            "stash_count": 0
        }

        # Get current branch
        result = await self.execute_git_command("branch --show-current")
        if result["success"]:
            metrics["current_branch"] = result["stdout"].strip()

        # Count branches
        result = await self.execute_git_command("branch -a")
        if result["success"]:
            metrics["branch_count"] = len(result["stdout"].splitlines())

        # Count commits
        result = await self.execute_git_command("rev-list --count HEAD")
        if result["success"]:
            metrics["commit_count"] = int(result["stdout"].strip())

        # Count contributors
        result = await self.execute_git_command("shortlog -sn")
        if result["success"]:
            metrics["contributors"] = len(result["stdout"].splitlines())

        # Get last commit info
        result = await self.execute_git_command("log -1 --format='%H|%an|%ae|%at|%s'")
        if result["success"]:
            parts = result["stdout"].strip().split("|")
            if len(parts) >= 5:
                metrics["last_commit"] = {
                    "hash": parts[0],
                    "author": parts[1],
                    "email": parts[2],
                    "timestamp": datetime.fromtimestamp(int(parts[3])).isoformat(),
                    "message": parts[4]
                }

        # Check for uncommitted changes
        result = await self.execute_git_command("status --porcelain")
        if result["success"]:
            metrics["uncommitted_changes"] = bool(result["stdout"].strip())

        # Count stashes
        result = await self.execute_git_command("stash list")
        if result["success"]:
            metrics["stash_count"] = len(result["stdout"].splitlines())

        return metrics

    async def _analyze_dependencies(self) -> Dict[str, Any]:
        """Analyze project dependencies.

        Returns:
            Dependency metrics
        """
        metrics = {
            "python": {},
            "node": {}
        }

        repo_root = self.get_repository_root()

        # Check Python dependencies
        requirements_file = repo_root / "requirements.txt"
        if requirements_file.exists():
            with open(requirements_file, 'r') as f:
                lines = f.readlines()
                metrics["python"]["dependency_count"] = len(
                    [l for l in lines if l.strip() and not l.startswith("#")]
                )
                metrics["python"]["has_requirements"] = True
        else:
            metrics["python"]["has_requirements"] = False

        # Check Node dependencies
        package_json = repo_root / "package.json"
        if package_json.exists():
            with open(package_json, 'r') as f:
                package_data = json.load(f)
                deps = package_data.get("dependencies", {})
                dev_deps = package_data.get("devDependencies", {})
                metrics["node"]["dependency_count"] = len(deps)
                metrics["node"]["dev_dependency_count"] = len(dev_deps)
                metrics["node"]["has_package_json"] = True
        else:
            metrics["node"]["has_package_json"] = False

        # Check node_modules size
        node_modules = repo_root / "node_modules"
        if node_modules.exists():
            try:
                size = sum(f.stat().st_size for f in node_modules.rglob("*") if f.is_file())
                metrics["node"]["node_modules_size"] = self.format_size(size)
            except:
                metrics["node"]["node_modules_size"] = "Unknown"

        return metrics

    async def _analyze_performance(self) -> Dict[str, Any]:
        """Analyze repository performance metrics.

        Returns:
            Performance metrics
        """
        metrics = {
            "git_gc_needed": False,
            "large_pack_files": [],
            "index_size": 0
        }

        repo_root = self.get_repository_root()

        # Check if git gc is needed
        gc_result = await self.execute_git_command("count-objects -v")
        if gc_result["success"]:
            for line in gc_result["stdout"].splitlines():
                if "garbage" in line and int(line.split(":")[1].strip()) > 100:
                    metrics["git_gc_needed"] = True

        # Check pack files
        pack_dir = repo_root / ".git/objects/pack"
        if pack_dir.exists():
            for pack_file in pack_dir.glob("*.pack"):
                size = pack_file.stat().st_size
                if size > 100 * 1024 * 1024:  # > 100MB
                    metrics["large_pack_files"].append({
                        "file": pack_file.name,
                        "size": self.format_size(size)
                    })

        # Check index size
        index_file = repo_root / ".git/index"
        if index_file.exists():
            metrics["index_size"] = self.format_size(index_file.stat().st_size)

        return metrics

    async def _analyze_security(self) -> Dict[str, Any]:
        """Analyze security-related metrics.

        Returns:
            Security metrics
        """
        metrics = {
            "secrets_found": [],
            "vulnerable_patterns": []
        }

        # Common secret patterns to check
        secret_patterns = [
            ("AWS Key", r"AKIA[0-9A-Z]{16}"),
            ("API Key", r"api[_-]?key[_-]?=[\'\"][a-zA-Z0-9]{20,}[\'\"]"),
            ("Private Key", r"-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----")
        ]

        # Check for potential secrets in tracked files
        # (simplified check - real implementation would be more thorough)
        result = await self.execute_git_command("grep -l 'password\\|secret\\|key' --cached")
        if result["success"] and result["stdout"]:
            for file_path in result["stdout"].splitlines():
                metrics["secrets_found"].append({
                    "file": file_path,
                    "type": "Potential secret in file name or content"
                })

        return metrics

    def _evaluate_health_status(self, health_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate overall health status based on metrics.

        Args:
            health_data: Current health data

        Returns:
            Updated health data with status
        """
        issues = []
        severity = "healthy"

        # Check repository size
        size_gb = health_data["metrics"]["size"]["total_size_bytes"] / (1024 ** 3)
        if size_gb > self.thresholds["repo_size_critical_gb"]:
            issues.append(f"Critical: Repository size ({size_gb:.2f}GB) exceeds critical threshold")
            severity = "critical"
        elif size_gb > self.thresholds["repo_size_warning_gb"]:
            issues.append(f"Warning: Repository size ({size_gb:.2f}GB) exceeds warning threshold")
            if severity == "healthy":
                severity = "warning"

        # Check file count
        file_count = health_data["metrics"]["files"]["total_files"]
        if file_count > self.thresholds["file_count_critical"]:
            issues.append(f"Critical: File count ({file_count}) exceeds critical threshold")
            severity = "critical"
        elif file_count > self.thresholds["file_count_warning"]:
            issues.append(f"Warning: File count ({file_count}) exceeds warning threshold")
            if severity == "healthy":
                severity = "warning"

        # Check for uncommitted changes
        if health_data["metrics"]["git"]["uncommitted_changes"]:
            issues.append("Info: Repository has uncommitted changes")

        health_data["issues"] = issues
        health_data["overall_status"] = severity

        return health_data

    def _generate_health_recommendations(self, health_data: Dict[str, Any]) -> List[str]:
        """Generate health recommendations.

        Args:
            health_data: Health data

        Returns:
            List of recommendations
        """
        recommendations = []

        # Size recommendations
        size_gb = health_data["metrics"]["size"]["total_size_bytes"] / (1024 ** 3)
        if size_gb > 1:
            recommendations.append("Consider using Git LFS for large files")
            recommendations.append("Run 'git gc' to optimize repository")

        # Performance recommendations
        if "performance" in health_data["metrics"]:
            if health_data["metrics"]["performance"]["git_gc_needed"]:
                recommendations.append("Run 'git gc --aggressive' to clean up repository")

        # File recommendations
        if health_data["metrics"]["files"]["max_depth"] > self.thresholds["max_file_depth"]:
            recommendations.append("Consider flattening directory structure")

        # Git recommendations
        if health_data["metrics"]["git"]["stash_count"] > 5:
            recommendations.append(f"Clean up git stashes ({health_data['metrics']['git']['stash_count']} found)")

        return recommendations

    async def execute_action(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute a specific action.

        Args:
            action: Action to execute
            **kwargs: Action parameters

        Returns:
            Action results
        """
        if action == "check":
            return await self.analyze(**kwargs)

        elif action == "optimize":
            # Run git gc
            gc_result = await self.execute_git_command("gc --aggressive")
            return {
                "success": gc_result["success"],
                "message": "Repository optimized" if gc_result["success"] else "Optimization failed"
            }

        elif action == "clean":
            # Clean up various artifacts
            commands = [
                "clean -fd",  # Remove untracked files
                "gc",  # Garbage collection
                "prune"  # Prune unreachable objects
            ]

            results = []
            for cmd in commands:
                result = await self.execute_git_command(cmd)
                results.append({
                    "command": cmd,
                    "success": result["success"]
                })

            return {"success": True, "actions": results}

        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    async def generate_health_report(self, output_format: str = "markdown") -> str:
        """Generate a health report.

        Args:
            output_format: Output format

        Returns:
            Formatted health report
        """
        health_data = await self.analyze()

        if output_format == "json":
            return json.dumps(health_data, indent=2)

        elif output_format == "markdown":
            lines = [
                "# Repository Health Report",
                f"Generated: {health_data['timestamp']}",
                f"Repository: {health_data['repository_path']}",
                "",
                f"## Overall Status: {health_data['overall_status'].upper()}",
                "",
                "## Metrics",
                "",
                "### Size Metrics",
                f"- Total Size: {health_data['metrics']['size']['total_size_formatted']}",
                f"- Git Size: {health_data['metrics']['size']['git_size_formatted']}",
                f"- Working Tree: {health_data['metrics']['size']['working_tree_size_formatted']}",
                "",
                "### File Metrics",
                f"- Total Files: {health_data['metrics']['files']['total_files']}",
                f"- Total Directories: {health_data['metrics']['files']['total_directories']}",
                f"- Max Depth: {health_data['metrics']['files']['max_depth']}",
                "",
                "### Git Metrics",
                f"- Current Branch: {health_data['metrics']['git']['current_branch']}",
                f"- Commit Count: {health_data['metrics']['git']['commit_count']}",
                f"- Contributors: {health_data['metrics']['git']['contributors']}",
                f"- Uncommitted Changes: {health_data['metrics']['git']['uncommitted_changes']}",
                ""
            ]

            if health_data["issues"]:
                lines.extend(["## Issues"])
                for issue in health_data["issues"]:
                    lines.append(f"- {issue}")
                lines.append("")

            if health_data["recommendations"]:
                lines.extend(["## Recommendations"])
                for rec in health_data["recommendations"]:
                    lines.append(f"- {rec}")

            return "\n".join(lines)

        return str(health_data)
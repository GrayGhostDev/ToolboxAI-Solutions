"""
Git LFS Migration Agent for managing large files.
"""

import asyncio
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base_github_agent import BaseGitHubAgent


class GitLFSMigrationAgent(BaseGitHubAgent):
    """Agent that manages Git LFS migration for large files."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the Git LFS migration agent."""
        super().__init__(config_path)
        self.lfs_config = self.config.get('git_lfs', {})
        self.auto_migrate = self.lfs_config.get('auto_migrate', False)
        self.track_patterns = self.lfs_config.get('track_patterns', [
            '*.png', '*.jpg', '*.jpeg', '*.gif', '*.webp',
            '*.fig', '*.sketch', '*.xd', '*.psd',
            '*.blend', '*.obj', '*.fbx', '*.dae',
            '*.mp4', '*.mov', '*.avi',
            '*.zip', '*.tar', '*.gz'
        ])
        self.size_threshold_mb = self.lfs_config.get('size_threshold_mb', 50)

    async def analyze(self, check_status: bool = True) -> Dict[str, Any]:
        """Analyze Git LFS status and configuration.

        Args:
            check_status: Whether to check current LFS status

        Returns:
            LFS analysis results
        """
        results = {
            "lfs_installed": False,
            "lfs_initialized": False,
            "tracked_patterns": [],
            "lfs_files": [],
            "candidates_for_lfs": [],
            "recommendations": []
        }

        # Check if Git LFS is installed
        lfs_version = await self.execute_git_command("lfs version")
        results["lfs_installed"] = lfs_version["success"]

        if not results["lfs_installed"]:
            results["recommendations"].append("Install Git LFS: brew install git-lfs")
            return results

        # Check if LFS is initialized in repo
        lfs_status = await self.execute_git_command("lfs status")
        results["lfs_initialized"] = lfs_status["success"]

        if not results["lfs_initialized"]:
            results["recommendations"].append("Initialize Git LFS: git lfs install")

        # Get tracked patterns
        gitattributes_path = self.get_repository_root() / ".gitattributes"
        if gitattributes_path.exists():
            with open(gitattributes_path, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    if "filter=lfs" in line:
                        pattern = line.split()[0]
                        results["tracked_patterns"].append(pattern)

        # Get LFS files
        if check_status:
            lfs_files = await self.execute_git_command("lfs ls-files")
            if lfs_files["success"]:
                results["lfs_files"] = [
                    line.strip() for line in lfs_files["stdout"].splitlines()
                ]

        # Find candidates for LFS migration
        candidates = await self._find_lfs_candidates()
        results["candidates_for_lfs"] = candidates

        if candidates:
            results["recommendations"].append(
                f"Migrate {len(candidates)} file(s) to Git LFS to improve repository performance"
            )

        await self.log_operation("analyze", {
            "lfs_installed": results["lfs_installed"],
            "tracked_patterns": len(results["tracked_patterns"]),
            "candidates": len(candidates)
        })

        return results

    async def _find_lfs_candidates(self) -> List[Dict[str, Any]]:
        """Find files that are candidates for LFS migration.

        Returns:
            List of candidate file info
        """
        candidates = []
        repo_root = self.get_repository_root()
        if not repo_root:
            return candidates

        # Get tracked files
        result = await self.execute_git_command("ls-files")
        if not result["success"]:
            return candidates

        threshold_bytes = self.size_threshold_mb * 1024 * 1024

        for file_path in result["stdout"].splitlines():
            if not file_path:
                continue

            full_path = repo_root / file_path
            if not full_path.exists():
                continue

            size = full_path.stat().st_size
            if size >= threshold_bytes:
                # Check if already in LFS
                lfs_check = await self.execute_git_command(f"check-attr filter {file_path}")
                is_lfs = "lfs" in lfs_check.get("stdout", "")

                if not is_lfs:
                    candidates.append({
                        "path": file_path,
                        "size_bytes": size,
                        "size_formatted": self.format_size(size),
                        "file_type": full_path.suffix
                    })

        return candidates

    async def setup_lfs(self) -> Dict[str, Any]:
        """Set up Git LFS in the repository.

        Returns:
            Setup results
        """
        results = {"success": False, "actions": []}

        # Check if Git LFS is installed
        lfs_version = await self.execute_git_command("lfs version")
        if not lfs_version["success"]:
            return {
                "success": False,
                "error": "Git LFS is not installed. Install with: brew install git-lfs"
            }

        # Initialize Git LFS
        init_result = await self.execute_git_command("lfs install")
        if init_result["success"]:
            results["actions"].append("Initialized Git LFS")

        # Set up tracking patterns
        for pattern in self.track_patterns:
            track_result = await self.execute_git_command(f"lfs track '{pattern}'")
            if track_result["success"]:
                results["actions"].append(f"Tracking pattern: {pattern}")

        # Add .gitattributes to git
        add_result = await self.execute_git_command("add .gitattributes")
        if add_result["success"]:
            results["actions"].append("Added .gitattributes to git")
            results["success"] = True

        await self.log_operation("setup_lfs", results)

        return results

    async def migrate_file_to_lfs(self, file_path: str) -> Dict[str, Any]:
        """Migrate a specific file to Git LFS.

        Args:
            file_path: Path to file to migrate

        Returns:
            Migration results
        """
        results = {
            "success": False,
            "file_path": file_path,
            "actions": [],
            "errors": []
        }

        repo_root = self.get_repository_root()
        if not repo_root:
            results["errors"].append("Not in a git repository")
            return results

        full_path = repo_root / file_path
        if not full_path.exists():
            results["errors"].append(f"File not found: {file_path}")
            return results

        # Get file extension for tracking pattern
        file_ext = full_path.suffix
        if file_ext:
            pattern = f"*{file_ext}"
        else:
            pattern = full_path.name

        # Track the pattern
        track_result = await self.execute_git_command(f"lfs track '{pattern}'")
        if track_result["success"]:
            results["actions"].append(f"Added LFS tracking for pattern: {pattern}")
        else:
            results["errors"].append(f"Failed to track pattern: {track_result.get('stderr', '')}")

        # Add .gitattributes
        attr_result = await self.execute_git_command("add .gitattributes")
        if attr_result["success"]:
            results["actions"].append("Updated .gitattributes")

        # Remove file from git index
        rm_result = await self.execute_git_command(f"rm --cached '{file_path}'")
        if rm_result["success"]:
            results["actions"].append(f"Removed {file_path} from git index")

        # Re-add file (will be added as LFS)
        add_result = await self.execute_git_command(f"add '{file_path}'")
        if add_result["success"]:
            results["actions"].append(f"Re-added {file_path} as LFS file")
            results["success"] = True
        else:
            results["errors"].append(f"Failed to re-add file: {add_result.get('stderr', '')}")

        await self.log_operation("migrate_file", results)
        self.update_metrics(operations_performed=1, files_processed=1)

        return results

    async def batch_migrate_directory(self, directory: str) -> Dict[str, Any]:
        """Migrate all large files in a directory to Git LFS.

        Args:
            directory: Directory path

        Returns:
            Migration results
        """
        results = {
            "success": False,
            "directory": directory,
            "migrated_files": [],
            "failed_files": [],
            "total_size_migrated": 0
        }

        repo_root = self.get_repository_root()
        if not repo_root:
            return {"success": False, "error": "Not in a git repository"}

        dir_path = repo_root / directory
        if not dir_path.exists():
            return {"success": False, "error": f"Directory not found: {directory}"}

        # Find large files in directory
        threshold_bytes = self.size_threshold_mb * 1024 * 1024
        large_files = []

        for file_path in dir_path.rglob("*"):
            if file_path.is_file():
                size = file_path.stat().st_size
                if size >= threshold_bytes:
                    relative_path = file_path.relative_to(repo_root)
                    large_files.append({
                        "path": str(relative_path),
                        "size": size
                    })

        # Migrate each file
        for file_info in large_files:
            migration_result = await self.migrate_file_to_lfs(file_info["path"])
            if migration_result["success"]:
                results["migrated_files"].append(file_info["path"])
                results["total_size_migrated"] += file_info["size"]
            else:
                results["failed_files"].append({
                    "path": file_info["path"],
                    "errors": migration_result.get("errors", [])
                })

        results["success"] = len(results["migrated_files"]) > 0
        results["total_size_formatted"] = self.format_size(results["total_size_migrated"])

        await self.log_operation("batch_migrate", results)

        return results

    async def verify_lfs_status(self) -> Dict[str, Any]:
        """Verify the current LFS status and integrity.

        Returns:
            Verification results
        """
        results = {
            "success": True,
            "checks": {},
            "issues": []
        }

        # Check LFS installation
        version_check = await self.execute_git_command("lfs version")
        results["checks"]["lfs_installed"] = version_check["success"]

        # Check LFS hooks
        hooks_check = await self.execute_git_command("lfs env")
        results["checks"]["hooks_configured"] = hooks_check["success"]

        # Check for missing LFS objects
        fsck_result = await self.execute_git_command("lfs fsck")
        if fsck_result["success"]:
            results["checks"]["objects_valid"] = True
        else:
            results["checks"]["objects_valid"] = False
            results["issues"].append("Some LFS objects are missing or corrupted")

        # Check for files that should be in LFS
        candidates = await self._find_lfs_candidates()
        if candidates:
            results["issues"].append(
                f"{len(candidates)} file(s) should be migrated to LFS"
            )

        # Get LFS storage info
        storage_info = await self.execute_git_command("lfs ls-files -s")
        if storage_info["success"]:
            lines = storage_info["stdout"].splitlines()
            results["lfs_file_count"] = len(lines)

        results["success"] = len(results["issues"]) == 0

        return results

    async def execute_action(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute a specific action.

        Args:
            action: Action to execute
            **kwargs: Action parameters

        Returns:
            Action results
        """
        if action == "analyze":
            return await self.analyze(**kwargs)

        elif action == "setup":
            return await self.setup_lfs()

        elif action == "migrate_file":
            file_path = kwargs.get("file_path")
            if not file_path:
                return {"success": False, "error": "file_path required"}
            return await self.migrate_file_to_lfs(file_path)

        elif action == "batch_migrate":
            directory = kwargs.get("directory", ".")
            return await self.batch_migrate_directory(directory)

        elif action == "verify":
            return await self.verify_lfs_status()

        elif action == "clean":
            # Clean up old LFS files
            prune_result = await self.execute_git_command("lfs prune")
            return {
                "success": prune_result["success"],
                "output": prune_result.get("stdout", "")
            }

        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    async def generate_migration_plan(self) -> Dict[str, Any]:
        """Generate a migration plan for large files.

        Returns:
            Migration plan
        """
        candidates = await self._find_lfs_candidates()

        plan = {
            "total_files": len(candidates),
            "total_size": sum(f["size_bytes"] for f in candidates),
            "estimated_time_minutes": len(candidates) * 0.5,  # Rough estimate
            "steps": [],
            "files_by_type": {}
        }

        # Group by file type
        for file_info in candidates:
            file_type = file_info["file_type"]
            if file_type not in plan["files_by_type"]:
                plan["files_by_type"][file_type] = []
            plan["files_by_type"][file_type].append(file_info)

        # Generate steps
        plan["steps"] = [
            "1. Ensure Git LFS is installed: brew install git-lfs",
            "2. Initialize Git LFS: git lfs install",
            f"3. Track file patterns: {', '.join(self.track_patterns[:5])}",
            f"4. Migrate {len(candidates)} large file(s)",
            "5. Commit changes: git commit -m 'Migrate large files to Git LFS'",
            "6. Clean up: git lfs prune"
        ]

        plan["total_size_formatted"] = self.format_size(plan["total_size"])

        return plan
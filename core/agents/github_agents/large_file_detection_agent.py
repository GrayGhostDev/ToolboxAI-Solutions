"""
Large File Detection Agent for GitHub repositories.
"""

from pathlib import Path
from typing import Any, Optional

from .base_github_agent import BaseGitHubAgent


class LargeFileDetectionAgent(BaseGitHubAgent):
    """Agent that detects large files in git repositories."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the large file detection agent."""
        super().__init__(config_path)
        self.size_thresholds = self.config.get("large_file_detection", {}).get(
            "size_thresholds",
            {"warning_mb": 25, "critical_mb": 50, "github_limit_mb": 100},
        )
        self.exempt_patterns = self.config.get("large_file_detection", {}).get(
            "exempt_patterns", [".git/", "node_modules/", "__pycache__/", "venv/"]
        )

    async def analyze(self, path: str = ".", check_staged: bool = True) -> dict[str, Any]:
        """Analyze repository for large files.

        Args:
            path: Directory path to analyze
            check_staged: Whether to check staged files

        Returns:
            Analysis results with large files detected
        """
        repo_root = self.get_repository_root()
        if not repo_root:
            return {"success": False, "error": "Not in a git repository"}

        large_files = []

        # Check staged files
        if check_staged:
            staged_files = await self._get_staged_files()
            for file_path in staged_files:
                full_path = repo_root / file_path
                if full_path.exists():
                    size = full_path.stat().st_size
                    file_info = self._analyze_file(full_path, size)
                    if file_info:
                        large_files.append(file_info)

        # Check tracked files
        tracked_files = await self._get_tracked_files()
        for file_path in tracked_files:
            full_path = repo_root / file_path
            if full_path.exists():
                size = full_path.stat().st_size
                file_info = self._analyze_file(full_path, size)
                if file_info:
                    large_files.append(file_info)

        # Check untracked files in working directory
        if path != ".":
            target_path = repo_root / path
            if target_path.exists() and target_path.is_dir():
                for file_path in target_path.rglob("*"):
                    if file_path.is_file() and not self._is_exempt(file_path):
                        size = file_path.stat().st_size
                        file_info = self._analyze_file(file_path, size)
                        if file_info:
                            large_files.append(file_info)

        # Sort by size descending
        large_files.sort(key=lambda x: x["size_bytes"], reverse=True)

        # Generate summary
        summary = self._generate_summary(large_files)

        await self.log_operation(
            "analyze",
            {
                "path": str(path),
                "files_found": len(large_files),
                "total_size": summary["total_size"],
            },
        )

        self.update_metrics(
            operations_performed=1,
            files_processed=len(tracked_files) + len(staged_files),
        )

        return {
            "success": True,
            "large_files": large_files,
            "summary": summary,
            "recommendations": self._generate_recommendations(large_files),
        }

    def _analyze_file(self, file_path: Path, size: int) -> Optional[dict[str, Any]]:
        """Analyze a single file for size issues.

        Args:
            file_path: Path to file
            size: File size in bytes

        Returns:
            File info if it's large, None otherwise
        """
        size_mb = size / (1024 * 1024)

        warning_threshold = self.size_thresholds["warning_mb"]
        critical_threshold = self.size_thresholds["critical_mb"]
        github_limit = self.size_thresholds["github_limit_mb"]

        if size_mb < warning_threshold:
            return None

        severity = "warning"
        if size_mb >= github_limit:
            severity = "blocker"
        elif size_mb >= critical_threshold:
            severity = "critical"

        return {
            "path": str(file_path),
            "size_bytes": size,
            "size_formatted": self.format_size(size),
            "size_mb": round(size_mb, 2),
            "severity": severity,
            "file_type": file_path.suffix,
            "exceeds_github_limit": size_mb >= github_limit,
        }

    async def _get_staged_files(self) -> list[str]:
        """Get list of staged files.

        Returns:
            List of staged file paths
        """
        result = await self.execute_git_command("diff --cached --name-only")
        if result["success"]:
            return [f.strip() for f in result["stdout"].splitlines() if f.strip()]
        return []

    async def _get_tracked_files(self) -> list[str]:
        """Get list of tracked files.

        Returns:
            List of tracked file paths
        """
        result = await self.execute_git_command("ls-files")
        if result["success"]:
            return [f.strip() for f in result["stdout"].splitlines() if f.strip()]
        return []

    def _is_exempt(self, file_path: Path) -> bool:
        """Check if file path is exempt from checking.

        Args:
            file_path: Path to check

        Returns:
            True if exempt, False otherwise
        """
        str_path = str(file_path)
        for pattern in self.exempt_patterns:
            if pattern in str_path:
                return True
        return False

    def _generate_summary(self, large_files: list[dict[str, Any]]) -> dict[str, Any]:
        """Generate summary statistics.

        Args:
            large_files: List of large file info

        Returns:
            Summary dictionary
        """
        if not large_files:
            return {
                "total_files": 0,
                "total_size": "0 B",
                "total_size_mb": 0,
                "blockers": 0,
                "critical": 0,
                "warnings": 0,
            }

        total_size = sum(f["size_bytes"] for f in large_files)

        return {
            "total_files": len(large_files),
            "total_size": self.format_size(total_size),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "blockers": sum(1 for f in large_files if f["severity"] == "blocker"),
            "critical": sum(1 for f in large_files if f["severity"] == "critical"),
            "warnings": sum(1 for f in large_files if f["severity"] == "warning"),
        }

    def _generate_recommendations(self, large_files: list[dict[str, Any]]) -> list[str]:
        """Generate recommendations based on findings.

        Args:
            large_files: List of large file info

        Returns:
            List of recommendations
        """
        recommendations = []

        blockers = [f for f in large_files if f["severity"] == "blocker"]
        if blockers:
            recommendations.append(
                f"URGENT: {len(blockers)} file(s) exceed GitHub's 100MB limit and must be removed or migrated to Git LFS"
            )

        critical = [f for f in large_files if f["severity"] == "critical"]
        if critical:
            recommendations.append(
                f"Consider migrating {len(critical)} file(s) over 50MB to Git LFS for better performance"
            )

        # Type-specific recommendations
        image_files = [
            f for f in large_files if f["file_type"] in [".png", ".jpg", ".jpeg", ".gif"]
        ]
        if image_files:
            recommendations.append(
                f"Optimize {len(image_files)} image file(s) using compression tools"
            )

        json_files = [f for f in large_files if f["file_type"] == ".json"]
        if json_files:
            recommendations.append(
                f"Consider compressing or splitting {len(json_files)} large JSON file(s)"
            )

        design_files = [f for f in large_files if f["file_type"] in [".fig", ".sketch", ".xd"]]
        if design_files:
            recommendations.append(
                f"Move {len(design_files)} design file(s) to external storage or use Git LFS"
            )

        return recommendations

    async def execute_action(self, action: str, **kwargs) -> dict[str, Any]:
        """Execute a specific action.

        Args:
            action: Action to execute
            **kwargs: Action parameters

        Returns:
            Action results
        """
        if action == "scan":
            return await self.analyze(**kwargs)

        elif action == "check_file":
            file_path = kwargs.get("file_path")
            if not file_path:
                return {"success": False, "error": "file_path required"}

            path = Path(file_path)
            if not path.exists():
                return {"success": False, "error": "File not found"}

            size = path.stat().st_size
            file_info = self._analyze_file(path, size)

            return {
                "success": True,
                "is_large": file_info is not None,
                "file_info": file_info,
            }

        elif action == "pre_commit_check":
            # Check only staged files
            staged_files = await self._get_staged_files()
            if not staged_files:
                return {"success": True, "message": "No staged files"}

            large_files = []
            repo_root = self.get_repository_root()

            for file_path in staged_files:
                full_path = repo_root / file_path
                if full_path.exists():
                    size = full_path.stat().st_size
                    file_info = self._analyze_file(full_path, size)
                    if file_info and file_info["severity"] in ["critical", "blocker"]:
                        large_files.append(file_info)

            if large_files:
                return {
                    "success": False,
                    "message": "Large files detected in commit",
                    "large_files": large_files,
                    "recommendations": self._generate_recommendations(large_files),
                }

            return {"success": True, "message": "All files within size limits"}

        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    async def generate_report(self, output_format: str = "json") -> str:
        """Generate a report of large files.

        Args:
            output_format: Output format (json, markdown, html)

        Returns:
            Formatted report string
        """
        analysis = await self.analyze()

        if output_format == "json":
            import json

            return json.dumps(analysis, indent=2)

        elif output_format == "markdown":
            lines = [
                "# Large File Detection Report",
                f"Generated: {self.metrics['start_time'].isoformat()}",
                "",
                "## Summary",
                f"- Total large files: {analysis['summary']['total_files']}",
                f"- Total size: {analysis['summary']['total_size']}",
                f"- Blockers (>100MB): {analysis['summary']['blockers']}",
                f"- Critical (>50MB): {analysis['summary']['critical']}",
                f"- Warnings (>25MB): {analysis['summary']['warnings']}",
                "",
                "## Large Files",
            ]

            for file_info in analysis["large_files"][:20]:  # Top 20
                lines.append(
                    f"- **{file_info['path']}** - {file_info['size_formatted']} "
                    f"[{file_info['severity'].upper()}]"
                )

            if analysis["recommendations"]:
                lines.extend(["", "## Recommendations"])
                for rec in analysis["recommendations"]:
                    lines.append(f"- {rec}")

            return "\n".join(lines)

        else:
            return str(analysis)

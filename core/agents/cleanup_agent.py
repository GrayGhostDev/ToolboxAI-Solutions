"""
Cleanup Agent - File system organization and maintenance

Performs folder cleanup, PATH updates, and loose file reassignment.
"""

import hashlib
import logging
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from .base_agent import AgentConfig, AgentState, BaseAgent

logger = logging.getLogger(__name__)


class CleanupType:
    """Cleanup operation types"""

    TEMP_FILES = "temp_files"
    CACHE_FILES = "cache_files"
    LOG_FILES = "log_files"
    DUPLICATE_FILES = "duplicate_files"
    EMPTY_DIRS = "empty_directories"
    ORPHANED_FILES = "orphaned_files"
    BUILD_ARTIFACTS = "build_artifacts"
    TEST_ARTIFACTS = "test_artifacts"
    ORGANIZE_FILES = "organize_files"
    PATH_CLEANUP = "path_cleanup"


class CleanupAgent(BaseAgent):
    """
    Agent responsible for file system cleanup and organization.

    Capabilities:
    - Remove temporary and cache files
    - Clean build and test artifacts
    - Organize loose files
    - Remove empty directories
    - Detect and handle duplicates
    - Update PATH configurations
    - Archive old files
    - Maintain project structure
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        if not config:
            config = AgentConfig(
                name="CleanupAgent",
                model="gpt-3.5-turbo",
                temperature=0.2,
                system_prompt=self._get_cleanup_prompt(),
            )
        super().__init__(config)

        self.cleanup_stats = {
            "files_removed": 0,
            "files_organized": 0,
            "space_freed": 0,
            "directories_cleaned": 0,
            "duplicates_found": 0,
        }

        # Define project structure
        self.project_structure = {
            "agents": ["*.py"],
            "server": ["*.py", "*.json"],
            "mcp": ["*.py"],
            "coordinators": ["*.py"],
            "sparc": ["*.py"],
            "swarm": ["*.py"],
            "tests": ["test_*.py", "*_test.py", "conftest.py"],
            "tests/unit": ["test_*.py"],
            "tests/integration": ["test_*.py"],
            "tests/e2e": ["test_*.py"],
            "database": ["*.sql", "*.py"],
            "Documentation": ["*.md", "*.txt"],
            "config": ["*.json", "*.yaml", "*.yml", "*.env.example"],
            "scripts": ["*.sh", "*.py"],
            "Roblox": ["*.lua", "*.rbxm", "*.rbxl"],
        }

        # Patterns to clean
        self.cleanup_patterns = {
            "temp_files": ["*.tmp", "*.temp", "~*", ".~*"],
            "cache_files": [
                "__pycache__",
                "*.pyc",
                "*.pyo",
                ".pytest_cache",
                ".coverage",
            ],
            "log_files": ["*.log", "logs/*.log"],
            "build_artifacts": ["dist/", "build/", "*.egg-info"],
            "test_artifacts": [
                "htmlcov/",
                "coverage.xml",
                ".coverage*",
                "test-results/",
            ],
            "system_files": [".DS_Store", "Thumbs.db", "desktop.ini"],
        }

        # Files to preserve
        self.preserve_patterns = [
            ".git",
            ".env",
            "venv*",
            "node_modules",
            "*.sqlite",
            "*.db",
        ]

    def _get_cleanup_prompt(self) -> str:
        """Get specialized cleanup prompt"""
        return """You are a Cleanup Agent specialized in file system organization and maintenance.

Your responsibilities:
- Clean temporary and cache files
- Organize project files into proper directories
- Remove duplicate files
- Clean empty directories
- Archive old files
- Maintain clean project structure
- Update PATH configurations
- Free up disk space
- Ensure system cleanliness

Always preserve important files and maintain project integrity.
"""

    async def _process_task(self, state: AgentState) -> Any:
        """Process cleanup tasks"""
        state["task"]
        context = state["context"]

        # Determine cleanup type
        cleanup_type = context.get("cleanup_type", CleanupType.TEMP_FILES)
        target_path = context.get("target_path", ".")

        # Execute appropriate cleanup
        if cleanup_type == CleanupType.TEMP_FILES:
            return await self._clean_temp_files(target_path, context)
        elif cleanup_type == CleanupType.CACHE_FILES:
            return await self._clean_cache_files(target_path, context)
        elif cleanup_type == CleanupType.DUPLICATE_FILES:
            return await self._find_and_remove_duplicates(target_path, context)
        elif cleanup_type == CleanupType.EMPTY_DIRS:
            return await self._remove_empty_directories(target_path, context)
        elif cleanup_type == CleanupType.ORGANIZE_FILES:
            return await self._organize_files(target_path, context)
        elif cleanup_type == CleanupType.PATH_CLEANUP:
            return await self._cleanup_path_config(context)
        else:
            return await self._comprehensive_cleanup(target_path, context)

    async def _clean_temp_files(self, target_path: str, context: dict[str, Any]) -> dict[str, Any]:
        """Clean temporary files"""
        logger.info(f"Cleaning temporary files in {target_path}")

        removed_files = []
        space_freed = 0

        path = Path(target_path)

        for pattern in self.cleanup_patterns["temp_files"]:
            for file_path in path.rglob(pattern):
                if self._should_preserve(file_path):
                    continue

                try:
                    file_size = file_path.stat().st_size

                    if file_path.is_file():
                        file_path.unlink()
                    elif file_path.is_dir():
                        shutil.rmtree(file_path)

                    removed_files.append(str(file_path))
                    space_freed += file_size
                    self.cleanup_stats["files_removed"] += 1

                except Exception as e:
                    logger.warning(f"Could not remove {file_path}: {e}")

        self.cleanup_stats["space_freed"] += space_freed

        return {
            "cleanup_type": "temp_files",
            "removed_count": len(removed_files),
            "space_freed": self._format_size(space_freed),
            "removed_files": removed_files[:20],  # First 20
            "stats": self.cleanup_stats,
        }

    async def _clean_cache_files(self, target_path: str, context: dict[str, Any]) -> dict[str, Any]:
        """Clean cache files"""
        logger.info(f"Cleaning cache files in {target_path}")

        removed_items = []
        space_freed = 0

        path = Path(target_path)

        # Clean Python cache
        for cache_dir in path.rglob("__pycache__"):
            if self._should_preserve(cache_dir):
                continue

            try:
                size = self._get_directory_size(cache_dir)
                shutil.rmtree(cache_dir)
                removed_items.append(str(cache_dir))
                space_freed += size
                self.cleanup_stats["directories_cleaned"] += 1
            except Exception as e:
                logger.warning(f"Could not remove {cache_dir}: {e}")

        # Clean pytest cache
        for cache_dir in path.rglob(".pytest_cache"):
            if self._should_preserve(cache_dir):
                continue

            try:
                size = self._get_directory_size(cache_dir)
                shutil.rmtree(cache_dir)
                removed_items.append(str(cache_dir))
                space_freed += size
                self.cleanup_stats["directories_cleaned"] += 1
            except Exception as e:
                logger.warning(f"Could not remove {cache_dir}: {e}")

        # Clean .pyc and .pyo files
        for pattern in ["*.pyc", "*.pyo"]:
            for file_path in path.rglob(pattern):
                try:
                    size = file_path.stat().st_size
                    file_path.unlink()
                    removed_items.append(str(file_path))
                    space_freed += size
                    self.cleanup_stats["files_removed"] += 1
                except Exception as e:
                    logger.warning(f"Could not remove {file_path}: {e}")

        self.cleanup_stats["space_freed"] += space_freed

        return {
            "cleanup_type": "cache_files",
            "removed_count": len(removed_items),
            "space_freed": self._format_size(space_freed),
            "removed_items": removed_items[:20],
            "stats": self.cleanup_stats,
        }

    async def _find_and_remove_duplicates(
        self, target_path: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Find and remove duplicate files"""
        logger.info(f"Finding duplicate files in {target_path}")

        file_hashes = {}
        duplicates = []
        space_freed = 0

        path = Path(target_path)

        # Calculate hashes for all files
        for file_path in path.rglob("*"):
            if not file_path.is_file():
                continue

            if self._should_preserve(file_path):
                continue

            try:
                file_hash = self._calculate_file_hash(file_path)

                if file_hash in file_hashes:
                    # Duplicate found
                    original = file_hashes[file_hash]
                    duplicates.append(
                        {
                            "original": str(original),
                            "duplicate": str(file_path),
                            "size": file_path.stat().st_size,
                        }
                    )

                    # Remove duplicate if requested
                    if context.get("remove_duplicates", False):
                        size = file_path.stat().st_size
                        file_path.unlink()
                        space_freed += size
                        self.cleanup_stats["files_removed"] += 1
                else:
                    file_hashes[file_hash] = file_path

            except Exception as e:
                logger.warning(f"Error processing {file_path}: {e}")

        self.cleanup_stats["duplicates_found"] += len(duplicates)
        self.cleanup_stats["space_freed"] += space_freed

        return {
            "cleanup_type": "duplicate_files",
            "duplicates_found": len(duplicates),
            "space_freed": self._format_size(space_freed),
            "duplicates": duplicates[:20],
            "action_taken": "removed" if context.get("remove_duplicates") else "identified",
            "stats": self.cleanup_stats,
        }

    async def _remove_empty_directories(
        self, target_path: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Remove empty directories"""
        logger.info(f"Removing empty directories in {target_path}")

        removed_dirs = []
        path = Path(target_path)

        # Walk directories bottom-up to remove nested empty dirs
        for dirpath in sorted(path.rglob("*"), reverse=True):
            if not dirpath.is_dir():
                continue

            if self._should_preserve(dirpath):
                continue

            try:
                if not any(dirpath.iterdir()):
                    dirpath.rmdir()
                    removed_dirs.append(str(dirpath))
                    self.cleanup_stats["directories_cleaned"] += 1
            except Exception as e:
                logger.debug(f"Could not remove {dirpath}: {e}")

        return {
            "cleanup_type": "empty_directories",
            "removed_count": len(removed_dirs),
            "removed_dirs": removed_dirs[:20],
            "stats": self.cleanup_stats,
        }

    async def _organize_files(self, target_path: str, context: dict[str, Any]) -> dict[str, Any]:
        """Organize loose files into proper directories"""
        logger.info(f"Organizing files in {target_path}")

        organized_files = []
        path = Path(target_path)

        # Find loose files in root
        for file_path in path.glob("*"):
            if not file_path.is_file():
                continue

            if self._should_preserve(file_path):
                continue

            # Determine proper location
            target_dir = self._determine_file_location(file_path)

            if target_dir:
                try:
                    target_dir_path = path / target_dir
                    target_dir_path.mkdir(parents=True, exist_ok=True)

                    new_path = target_dir_path / file_path.name

                    # Check if file already exists
                    if new_path.exists():
                        # Add timestamp to filename
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        new_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
                        new_path = target_dir_path / new_name

                    shutil.move(str(file_path), str(new_path))
                    organized_files.append(
                        {
                            "file": file_path.name,
                            "from": str(file_path.parent),
                            "to": str(target_dir_path),
                        }
                    )
                    self.cleanup_stats["files_organized"] += 1

                except Exception as e:
                    logger.warning(f"Could not move {file_path}: {e}")

        return {
            "cleanup_type": "organize_files",
            "organized_count": len(organized_files),
            "organized_files": organized_files[:20],
            "stats": self.cleanup_stats,
        }

    async def _cleanup_path_config(self, context: dict[str, Any]) -> dict[str, Any]:
        """Clean up PATH configuration"""
        logger.info("Cleaning up PATH configuration")

        # Get current PATH
        current_path = os.environ.get("PATH", "").split(os.pathsep)

        # Remove duplicates while preserving order
        seen = set()
        cleaned_path = []
        invalid_paths = []

        for path in current_path:
            if path and path not in seen:
                # Check if path exists
                if os.path.exists(path):
                    cleaned_path.append(path)
                    seen.add(path)
                else:
                    invalid_paths.append(path)

        # Update PATH if changed
        if len(cleaned_path) != len(current_path):
            new_path = os.pathsep.join(cleaned_path)
            os.environ["PATH"] = new_path

            return {
                "cleanup_type": "path_cleanup",
                "original_entries": len(current_path),
                "cleaned_entries": len(cleaned_path),
                "removed_duplicates": len(current_path) - len(cleaned_path) - len(invalid_paths),
                "invalid_paths": invalid_paths[:10],
                "path_updated": True,
            }

        return {
            "cleanup_type": "path_cleanup",
            "entries": len(current_path),
            "path_updated": False,
            "message": "PATH is already clean",
        }

    async def _comprehensive_cleanup(
        self, target_path: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Perform comprehensive cleanup"""
        logger.info(f"Performing comprehensive cleanup in {target_path}")

        results = {}

        # Run all cleanup operations
        operations = [
            ("temp_files", self._clean_temp_files),
            ("cache_files", self._clean_cache_files),
            ("empty_dirs", self._remove_empty_directories),
            ("organize", self._organize_files),
            ("path", self._cleanup_path_config),
        ]

        for op_name, op_func in operations:
            try:
                if op_name == "path":
                    result = await op_func(context)
                else:
                    result = await op_func(target_path, context)
                results[op_name] = result
            except Exception as e:
                logger.error(f"Error in {op_name}: {e}")
                results[op_name] = {"error": str(e)}

        # Archive old files if requested
        if context.get("archive_old_files", False):
            archive_result = await self._archive_old_files(target_path, context)
            results["archive"] = archive_result

        return {
            "cleanup_type": "comprehensive",
            "operations": results,
            "summary": {
                "files_removed": self.cleanup_stats["files_removed"],
                "files_organized": self.cleanup_stats["files_organized"],
                "directories_cleaned": self.cleanup_stats["directories_cleaned"],
                "space_freed": self._format_size(self.cleanup_stats["space_freed"]),
                "duplicates_found": self.cleanup_stats["duplicates_found"],
            },
        }

    async def _archive_old_files(self, target_path: str, context: dict[str, Any]) -> dict[str, Any]:
        """Archive old files"""
        logger.info("Archiving old files")

        days_old = context.get("archive_days_old", 90)
        cutoff_date = datetime.now() - timedelta(days=days_old)

        archive_dir = Path(target_path) / "_archive" / datetime.now().strftime("%Y%m%d")
        archive_dir.mkdir(parents=True, exist_ok=True)

        archived_files = []

        path = Path(target_path)

        for file_path in path.rglob("*"):
            if not file_path.is_file():
                continue

            if self._should_preserve(file_path) or "_archive" in str(file_path):
                continue

            try:
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)

                if mtime < cutoff_date:
                    relative_path = file_path.relative_to(path)
                    archive_path = archive_dir / relative_path
                    archive_path.parent.mkdir(parents=True, exist_ok=True)

                    shutil.move(str(file_path), str(archive_path))
                    archived_files.append(str(relative_path))

            except Exception as e:
                logger.warning(f"Could not archive {file_path}: {e}")

        return {
            "archived_count": len(archived_files),
            "archive_location": str(archive_dir),
            "archived_files": archived_files[:20],
        }

    def _should_preserve(self, path: Path) -> bool:
        """Check if file/directory should be preserved"""
        path_str = str(path)

        for pattern in self.preserve_patterns:
            if pattern in path_str:
                return True

        # Don't remove git files
        if ".git" in path.parts:
            return True

        # Don't remove virtual environments
        if any(part.startswith("venv") for part in path.parts):
            return True

        return False

    def _determine_file_location(self, file_path: Path) -> Optional[str]:
        """Determine proper location for a file"""
        name = file_path.name
        suffix = file_path.suffix

        # Test files
        if name.startswith("test_") or name.endswith("_test.py"):
            return "tests"

        # Python files
        if suffix == ".py":
            # Check content for agent/server/etc
            try:
                content = file_path.read_text()
                if "Agent" in content and "BaseAgent" in content:
                    return "agents"
                elif "FastAPI" in content or "Flask" in content:
                    return "server"
                elif "coordinator" in content.lower():
                    return "coordinators"
            except:
                pass

        # Documentation
        if suffix in [".md", ".txt", ".rst"]:
            return "Documentation"

        # Configuration
        if suffix in [".json", ".yaml", ".yml"] or name.endswith(".env.example"):
            return "config"

        # Scripts
        if suffix == ".sh":
            return "scripts"

        # SQL files
        if suffix == ".sql":
            return "database"

        # Lua files
        if suffix == ".lua":
            return "Roblox/Scripts"

        return None

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()

    def _get_directory_size(self, directory: Path) -> int:
        """Get total size of directory"""
        total_size = 0

        for path in directory.rglob("*"):
            if path.is_file():
                total_size += path.stat().st_size

        return total_size

    def _format_size(self, size_bytes: int) -> str:
        """Format size in human-readable format"""
        size = float(size_bytes)
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"

    async def schedule_cleanup(self, schedule: dict[str, Any]) -> dict[str, Any]:
        """Schedule regular cleanup operations"""
        logger.info("Scheduling cleanup operations")

        # This would integrate with a scheduler like APScheduler
        # For now, return the schedule configuration

        return {
            "schedule_created": True,
            "daily_cleanup": schedule.get("daily", ["temp_files", "cache_files"]),
            "weekly_cleanup": schedule.get("weekly", ["duplicates", "empty_dirs"]),
            "monthly_cleanup": schedule.get("monthly", ["comprehensive", "archive"]),
        }

    def get_cleanup_report(self) -> dict[str, Any]:
        """Generate cleanup report"""
        return {
            "stats": self.cleanup_stats,
            "space_freed_total": self._format_size(self.cleanup_stats["space_freed"]),
            "files_processed": {
                "removed": self.cleanup_stats["files_removed"],
                "organized": self.cleanup_stats["files_organized"],
            },
            "directories_cleaned": self.cleanup_stats["directories_cleaned"],
            "duplicates_found": self.cleanup_stats["duplicates_found"],
            "timestamp": datetime.now().isoformat(),
        }

    def reset_stats(self):
        """Reset cleanup statistics"""
        self.cleanup_stats = {
            "files_removed": 0,
            "files_organized": 0,
            "space_freed": 0,
            "directories_cleaned": 0,
            "duplicates_found": 0,
        }

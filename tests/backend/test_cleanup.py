"""
Test Cleanup Utility
Automatically cleans up old test logs and reports to keep the filesystem organized
"""

import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path


def make_json_serializable(obj):
    """Convert non-serializable objects to serializable format."""
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    elif hasattr(obj, "to_dict"):
        return obj.to_dict()
    elif hasattr(obj, "_asdict"):
        return obj._asdict()
    else:
        return str(obj)


import json
import logging

logger = logging.getLogger(__name__)


class TestCleanupManager:
    """Manages cleanup of old test logs and reports"""

    def __init__(
        self,
        test_log_dir: Path = None,
        retention_days: int = 7,
        max_files_per_type: int = 10,
        auto_cleanup: bool = True,
    ):
        """
        Initialize the cleanup manager

        Args:
            test_log_dir: Directory containing test logs
            retention_days: Number of days to keep logs
            max_files_per_type: Maximum number of files to keep per test type
            auto_cleanup: Whether to automatically cleanup on init
        """
        self.test_log_dir = test_log_dir or Path(__file__).parent / "logs"
        self.retention_days = retention_days
        self.max_files_per_type = max_files_per_type
        self.cleanup_report = []

        if auto_cleanup:
            self.cleanup()

    def cleanup(self) -> dict[str, int]:
        """
        Perform cleanup of old test files

        Returns:
            Dictionary with cleanup statistics
        """
        stats = {"files_removed": 0, "bytes_freed": 0, "files_kept": 0, "errors": 0}

        try:
            # Cleanup by age
            stats_age = self._cleanup_by_age()
            stats["files_removed"] += stats_age["files_removed"]
            stats["bytes_freed"] += stats_age["bytes_freed"]

            # Cleanup by count
            stats_count = self._cleanup_by_count()
            stats["files_removed"] += stats_count["files_removed"]
            stats["bytes_freed"] += stats_count["bytes_freed"]

            # Cleanup empty directories
            self._cleanup_empty_dirs()

            # Count remaining files
            stats["files_kept"] = self._count_files()

            # Generate cleanup report
            self._generate_cleanup_report(stats)

            logger.info(
                f"Cleanup completed: {stats['files_removed']} files removed, "
                f"{stats['bytes_freed'] / 1024 / 1024:.2f} MB freed"
            )

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            stats["errors"] += 1

        return stats

    def _cleanup_by_age(self) -> dict[str, int]:
        """Remove files older than retention_days"""
        stats = {"files_removed": 0, "bytes_freed": 0}
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)

        for root, dirs, files in os.walk(self.test_log_dir):
            # Skip the reports directory for important files
            if "reports" in root and "coverage" not in root:
                continue

            for file in files:
                file_path = Path(root) / file

                # Skip important files
                if self._is_important_file(file_path):
                    continue

                try:
                    # Check file age
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_mtime < cutoff_date:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        stats["files_removed"] += 1
                        stats["bytes_freed"] += file_size
                        self.cleanup_report.append(
                            {
                                "file": str(file_path),
                                "reason": "age",
                                "age_days": (datetime.now() - file_mtime).days,
                                "size_bytes": file_size,
                            }
                        )
                except Exception as e:
                    logger.warning(f"Could not remove file {file_path}: {e}")

        return stats

    def _cleanup_by_count(self) -> dict[str, int]:
        """Keep only the most recent max_files_per_type files per directory"""
        stats = {"files_removed": 0, "bytes_freed": 0}

        for subdir in ["unit", "integration", "e2e", "debug"]:
            dir_path = self.test_log_dir / subdir
            if not dir_path.exists():
                continue

            # Get all files with modification times
            files_with_time = []
            for file_path in dir_path.glob("*.log"):
                try:
                    mtime = file_path.stat().st_mtime
                    files_with_time.append((mtime, file_path))
                except:
                    continue

            # Sort by modification time (newest first)
            files_with_time.sort(reverse=True)

            # Remove excess files
            for _, file_path in files_with_time[self.max_files_per_type :]:
                try:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    stats["files_removed"] += 1
                    stats["bytes_freed"] += file_size
                    self.cleanup_report.append(
                        {"file": str(file_path), "reason": "count_limit", "size_bytes": file_size}
                    )
                except Exception as e:
                    logger.warning(f"Could not remove file {file_path}: {e}")

        return stats

    def _cleanup_empty_dirs(self):
        """Remove empty directories"""
        for root, dirs, files in os.walk(self.test_log_dir, topdown=False):
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                try:
                    if not any(dir_path.iterdir()):
                        dir_path.rmdir()
                        logger.debug(f"Removed empty directory: {dir_path}")
                except:
                    pass

    def _is_important_file(self, file_path: Path) -> bool:
        """Check if a file should be preserved"""
        important_patterns = [
            "pytest_report.html",
            "coverage.xml",
            "junit_report.xml",
            "test_report_",
            "all_tests.log",
        ]

        file_name = file_path.name
        return any(pattern in file_name for pattern in important_patterns)

    def _count_files(self) -> int:
        """Count remaining files"""
        count = 0
        for root, dirs, files in os.walk(self.test_log_dir):
            count += len(files)
        return count

    def _generate_cleanup_report(self, stats: dict[str, int]):
        """Generate a cleanup report"""
        report_file = (
            self.test_log_dir
            / "reports"
            / f"cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        report_file.parent.mkdir(exist_ok=True)

        report = {
            "timestamp": datetime.now().isoformat(),
            "retention_days": self.retention_days,
            "max_files_per_type": self.max_files_per_type,
            "statistics": stats,
            "files_removed": self.cleanup_report,
        }

        try:
            with open(report_file, "w") as f:
                json.dump(report, f, indent=2)
            logger.info(f"Cleanup report saved to: {report_file}")
        except Exception as e:
            logger.error(f"Could not save cleanup report: {e}")

    def archive_old_reports(self, archive_dir: Path | None = None):
        """Archive old test reports instead of deleting them"""
        archive_dir = archive_dir or self.test_log_dir / "archive"
        archive_dir.mkdir(exist_ok=True)

        # Create archive with timestamp
        archive_subdir = archive_dir / datetime.now().strftime("%Y%m%d")
        archive_subdir.mkdir(exist_ok=True)

        reports_dir = self.test_log_dir / "reports"
        if not reports_dir.exists():
            return

        cutoff_date = datetime.now() - timedelta(days=self.retention_days)

        for file_path in reports_dir.glob("*"):
            try:
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_mtime < cutoff_date and not self._is_important_file(file_path):
                    # Move to archive
                    dest_path = archive_subdir / file_path.name
                    shutil.move(str(file_path), str(dest_path))
                    logger.info(f"Archived: {file_path.name}")
            except Exception as e:
                logger.warning(f"Could not archive {file_path}: {e}")


# Pytest hook for automatic cleanup
def pytest_sessionstart(session):
    """Called after the Session object has been created and before performing collection"""
    cleanup_manager = TestCleanupManager(auto_cleanup=True)
    session.cleanup_manager = cleanup_manager


def pytest_sessionfinish(session, exitstatus):
    """Called after whole test run finished"""
    if hasattr(session, "cleanup_manager"):
        # Perform final cleanup
        session.cleanup_manager.cleanup()


# CLI utility for manual cleanup
def main():
    """Command-line interface for test cleanup"""
    import argparse

    parser = argparse.ArgumentParser(description="Clean up old test logs and reports")
    parser.add_argument("--days", type=int, default=7, help="Number of days to retain logs")
    parser.add_argument("--max-files", type=int, default=10, help="Max files per test type")
    parser.add_argument(
        "--archive", action="store_true", help="Archive old reports instead of deleting"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be deleted without deleting"
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    manager = TestCleanupManager(
        retention_days=args.days, max_files_per_type=args.max_files, auto_cleanup=False
    )

    if args.dry_run:
        logger.info("DRY RUN - No files will be deleted")
        # Just count files
        count = manager._count_files()
        logger.info(f"Total files: {count}")
    else:
        if args.archive:
            manager.archive_old_reports()
        stats = manager.cleanup()
        print(f"\nCleanup Summary:")
        print(f"  Files removed: {stats['files_removed']}")
        print(f"  Space freed: {stats['bytes_freed'] / 1024 / 1024:.2f} MB")
        print(f"  Files kept: {stats['files_kept']}")
        print(f"  Errors: {stats['errors']}")


if __name__ == "__main__":
    main()

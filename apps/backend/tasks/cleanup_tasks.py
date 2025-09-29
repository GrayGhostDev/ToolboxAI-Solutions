"""
Cleanup Tasks
============
Background tasks for cleaning up old data, files, and sessions
"""

import os
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Any
from celery import shared_task
from celery.utils.log import get_task_logger
import redis
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from apps.backend.core.database import get_session
from apps.backend.core.config import settings
from database.models import User, Session as DBSession

logger = get_task_logger(__name__)


@shared_task(
    bind=True,
    name="tasks.cleanup_old_files",
    max_retries=3,
    default_retry_delay=60,
    queue="maintenance",
    priority=1,
)
def cleanup_old_files(self, directory: str = "/tmp/toolboxai", days_old: int = 7) -> Dict[str, Any]:
    """
    Clean up temporary files older than specified days

    Args:
        directory: Directory to clean
        days_old: Age threshold in days

    Returns:
        Dictionary with cleanup statistics
    """
    try:
        if not os.path.exists(directory):
            return {"status": "skipped", "reason": "Directory does not exist"}

        cutoff_time = datetime.now() - timedelta(days=days_old)
        files_removed = 0
        bytes_freed = 0
        errors = []

        for root, dirs, files in os.walk(directory):
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    file_stat = os.stat(filepath)
                    file_modified = datetime.fromtimestamp(file_stat.st_mtime)

                    if file_modified < cutoff_time:
                        bytes_freed += file_stat.st_size
                        os.remove(filepath)
                        files_removed += 1
                        logger.info(f"Removed old file: {filepath}")
                except Exception as e:
                    errors.append(f"Error removing {filepath}: {str(e)}")
                    logger.warning(f"Could not remove {filepath}: {e}")

        # Remove empty directories
        for root, dirs, files in os.walk(directory, topdown=False):
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    if not os.listdir(dir_path):
                        os.rmdir(dir_path)
                        logger.info(f"Removed empty directory: {dir_path}")
                except Exception as e:
                    logger.warning(f"Could not remove directory {dir_path}: {e}")

        result = {
            "status": "success",
            "files_removed": files_removed,
            "bytes_freed": bytes_freed,
            "mb_freed": round(bytes_freed / (1024 * 1024), 2),
            "errors": errors if errors else None,
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(
            f"Cleanup completed: {files_removed} files removed, {result['mb_freed']} MB freed"
        )
        return result

    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    name="tasks.cleanup_expired_sessions",
    max_retries=3,
    default_retry_delay=60,
    queue="maintenance",
    priority=2,
)
def cleanup_expired_sessions(self, hours_old: int = 24) -> Dict[str, Any]:
    """
    Clean up expired database sessions and Redis session keys

    Args:
        hours_old: Age threshold in hours

    Returns:
        Dictionary with cleanup statistics
    """
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_old)
        db_sessions_removed = 0
        redis_keys_removed = 0

        # Clean database sessions
        with get_session() as session:
            # Find and delete expired sessions
            stmt = delete(DBSession).where(DBSession.last_activity < cutoff_time)
            result = session.execute(stmt)
            db_sessions_removed = result.rowcount
            session.commit()
            logger.info(f"Removed {db_sessions_removed} expired database sessions")

        # Clean Redis session keys
        try:
            redis_client = redis.from_url(settings.REDIS_URL)

            # Pattern for session keys (adjust based on your session key pattern)
            pattern = "session:*"
            cursor = 0

            while True:
                cursor, keys = redis_client.scan(cursor=cursor, match=pattern, count=100)

                for key in keys:
                    try:
                        # Check if key has expired or should be deleted
                        ttl = redis_client.ttl(key)
                        if ttl == -1:  # No TTL set
                            # Check last access time if stored in key
                            redis_client.delete(key)
                            redis_keys_removed += 1
                    except Exception as e:
                        logger.warning(f"Error processing Redis key {key}: {e}")

                if cursor == 0:
                    break

            logger.info(f"Removed {redis_keys_removed} expired Redis session keys")

        except Exception as e:
            logger.warning(f"Redis cleanup error: {e}")

        return {
            "status": "success",
            "db_sessions_removed": db_sessions_removed,
            "redis_keys_removed": redis_keys_removed,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Session cleanup failed: {e}")
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    name="tasks.cleanup_temp_storage",
    max_retries=2,
    default_retry_delay=120,
    queue="maintenance",
    priority=1,
)
def cleanup_temp_storage(self) -> Dict[str, Any]:
    """
    Clean up various temporary storage locations

    Returns:
        Dictionary with cleanup statistics
    """
    try:
        results = {
            "upload_temp": None,
            "export_temp": None,
            "cache_temp": None,
            "total_freed_mb": 0,
        }

        # Define temp directories to clean
        temp_dirs = {
            "upload_temp": os.path.join(settings.BASE_DIR, "temp", "uploads"),
            "export_temp": os.path.join(settings.BASE_DIR, "temp", "exports"),
            "cache_temp": os.path.join(settings.BASE_DIR, "temp", "cache"),
        }

        for name, directory in temp_dirs.items():
            if os.path.exists(directory):
                # Use the cleanup_old_files task logic
                cleanup_result = cleanup_old_files.apply(
                    args=[directory, 1]  # Clean files older than 1 day
                ).get()

                results[name] = cleanup_result
                if cleanup_result.get("mb_freed"):
                    results["total_freed_mb"] += cleanup_result["mb_freed"]

        # Clean up old log files
        log_dir = os.path.join(settings.BASE_DIR, "logs")
        if os.path.exists(log_dir):
            for log_file in os.listdir(log_dir):
                if log_file.endswith(".log"):
                    filepath = os.path.join(log_dir, log_file)
                    try:
                        # Rotate logs older than 30 days
                        file_stat = os.stat(filepath)
                        file_age_days = (
                            datetime.now() - datetime.fromtimestamp(file_stat.st_mtime)
                        ).days

                        if file_age_days > 30:
                            # Archive old logs
                            archive_path = os.path.join(
                                log_dir,
                                "archive",
                                f"{log_file}.{datetime.now().strftime('%Y%m%d')}",
                            )
                            os.makedirs(os.path.dirname(archive_path), exist_ok=True)
                            shutil.move(filepath, archive_path)
                            logger.info(f"Archived old log: {log_file}")

                    except Exception as e:
                        logger.warning(f"Error processing log file {log_file}: {e}")

        results["status"] = "success"
        results["timestamp"] = datetime.utcnow().isoformat()

        logger.info(f"Temp storage cleanup completed: {results['total_freed_mb']} MB freed total")
        return results

    except Exception as e:
        logger.error(f"Temp storage cleanup failed: {e}")
        raise self.retry(exc=e)

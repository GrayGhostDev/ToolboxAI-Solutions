"""
Centralized logging configuration with automatic log rotation
Implements rotating file handlers to prevent unbounded log growth
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path


class LoggingConfig:
    """
    Centralized logging configuration with rotation support

    Features:
    - Automatic log rotation based on size and time
    - Different log levels for different components
    - Structured logging format
    - Performance optimized
    """

    # Default configuration values
    DEFAULT_LOG_LEVEL = logging.INFO
    DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB per file
    DEFAULT_BACKUP_COUNT = 5  # Keep 5 backup files
    DEFAULT_LOG_FORMAT = (
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    )
    DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    # Log directory configuration
    LOG_DIR = Path(__file__).parent.parent.parent.parent / "logs"

    @classmethod
    def setup_logging(
        cls,
        app_name: str = "toolboxai",
        log_level: str | None = None,
        enable_console: bool = True,
        enable_file: bool = True,
        log_dir: Path | None = None,
    ) -> None:
        """
        Setup application-wide logging configuration

        Args:
            app_name: Name of the application for log files
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            enable_console: Enable console output
            enable_file: Enable file output with rotation
            log_dir: Custom log directory (defaults to project logs/)
        """
        # Determine log level from environment or parameter
        if log_level is None:
            log_level = os.getenv("LOG_LEVEL", "INFO")

        numeric_level = getattr(logging, log_level.upper(), cls.DEFAULT_LOG_LEVEL)

        # Setup log directory
        if log_dir is None:
            log_dir = cls.LOG_DIR
        log_dir.mkdir(parents=True, exist_ok=True)

        # Create formatter
        formatter = logging.Formatter(fmt=cls.DEFAULT_LOG_FORMAT, datefmt=cls.DEFAULT_DATE_FORMAT)

        # Get root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)

        # Clear existing handlers to avoid duplicates
        root_logger.handlers.clear()

        # Console handler
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(numeric_level)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)

        # File handlers with rotation
        if enable_file:
            # Main application log
            app_log_file = log_dir / f"{app_name}.log"
            app_file_handler = logging.handlers.RotatingFileHandler(
                filename=str(app_log_file),
                maxBytes=cls.DEFAULT_MAX_BYTES,
                backupCount=cls.DEFAULT_BACKUP_COUNT,
                encoding="utf-8",
            )
            app_file_handler.setLevel(numeric_level)
            app_file_handler.setFormatter(formatter)
            root_logger.addHandler(app_file_handler)

            # Error log (separate file for errors and above)
            error_log_file = log_dir / f"{app_name}_errors.log"
            error_file_handler = logging.handlers.RotatingFileHandler(
                filename=str(error_log_file),
                maxBytes=cls.DEFAULT_MAX_BYTES,
                backupCount=cls.DEFAULT_BACKUP_COUNT,
                encoding="utf-8",
            )
            error_file_handler.setLevel(logging.ERROR)
            error_file_handler.setFormatter(formatter)
            root_logger.addHandler(error_file_handler)

            # Access log for HTTP requests
            access_log_file = log_dir / f"{app_name}_access.log"
            access_logger = logging.getLogger("uvicorn.access")
            access_handler = logging.handlers.RotatingFileHandler(
                filename=str(access_log_file),
                maxBytes=cls.DEFAULT_MAX_BYTES,
                backupCount=cls.DEFAULT_BACKUP_COUNT,
                encoding="utf-8",
            )
            access_handler.setFormatter(formatter)
            access_logger.addHandler(access_handler)
            access_logger.propagate = False

        # Configure specific loggers
        cls._configure_component_loggers(numeric_level)

        # Log initialization
        logger = logging.getLogger(__name__)
        logger.info(f"Logging initialized for {app_name}")
        logger.info(f"Log level: {log_level}")
        logger.info(f"Log directory: {log_dir}")
        if enable_file:
            logger.info(f"Max log size: {cls.DEFAULT_MAX_BYTES / 1024 / 1024:.1f} MB")
            logger.info(f"Backup count: {cls.DEFAULT_BACKUP_COUNT}")

    @classmethod
    def _configure_component_loggers(cls, default_level: int) -> None:
        """
        Configure logging levels for specific components

        Args:
            default_level: Default logging level
        """
        # Reduce verbosity of third-party libraries
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("asyncio").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)

        # Pusher client logging
        logging.getLogger("pusher").setLevel(logging.INFO)

        # Reduce noise from development servers
        if default_level > logging.DEBUG:
            logging.getLogger("uvicorn").setLevel(logging.INFO)
            logging.getLogger("fastapi").setLevel(logging.INFO)

    @classmethod
    def setup_test_logging(cls, test_name: str = "test") -> None:
        """
        Setup logging configuration for tests

        Args:
            test_name: Name prefix for test log files
        """
        test_log_dir = cls.LOG_DIR / "tests"
        cls.setup_logging(
            app_name=f"test_{test_name}",
            log_level="DEBUG",
            enable_console=False,  # Reduce noise during tests
            enable_file=True,
            log_dir=test_log_dir,
        )

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get a logger instance with the given name

        Args:
            name: Logger name (usually __name__)

        Returns:
            Configured logger instance
        """
        return logging.getLogger(name)

    @classmethod
    def cleanup_old_logs(cls, days: int = 30) -> None:
        """
        Clean up log files older than specified days

        Args:
            days: Number of days to keep logs
        """
        import time

        cutoff_time = time.time() - (days * 24 * 60 * 60)

        logger = logging.getLogger(__name__)

        for log_dir in [cls.LOG_DIR, cls.LOG_DIR / "tests"]:
            if not log_dir.exists():
                continue

            for log_file in log_dir.glob("*.log*"):
                if log_file.stat().st_mtime < cutoff_time:
                    try:
                        log_file.unlink()
                        logger.info(f"Deleted old log file: {log_file}")
                    except Exception as e:
                        logger.error(f"Failed to delete {log_file}: {e}")


class TimedRotatingLogger:
    """
    Time-based rotating logger for daily log rotation
    """

    @classmethod
    def setup_daily_rotation(cls, app_name: str, log_dir: Path | None = None) -> logging.Logger:
        """
        Setup a logger with daily rotation

        Args:
            app_name: Application name for the logger
            log_dir: Directory for log files

        Returns:
            Configured logger with daily rotation
        """
        if log_dir is None:
            log_dir = LoggingConfig.LOG_DIR
        log_dir.mkdir(parents=True, exist_ok=True)

        logger = logging.getLogger(f"{app_name}_daily")
        logger.setLevel(logging.INFO)

        # Daily rotating file handler
        log_file = log_dir / f"{app_name}_daily.log"
        handler = logging.handlers.TimedRotatingFileHandler(
            filename=str(log_file),
            when="midnight",
            interval=1,
            backupCount=7,  # Keep 7 days of logs
            encoding="utf-8",
            utc=False,
        )

        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)

        logger.addHandler(handler)

        return logger


# Convenience function for quick setup
def setup_logging(app_name: str = "toolboxai", **kwargs) -> None:
    """
    Quick setup for application logging with rotation

    Args:
        app_name: Name of the application
        **kwargs: Additional arguments for LoggingConfig.setup_logging
    """
    LoggingConfig.setup_logging(app_name=app_name, **kwargs)


# Convenience function to get a logger
def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return LoggingConfig.get_logger(name)


# Initialize logging function for app_factory
def initialize_logging() -> None:
    """
    Initialize application logging with default configuration
    Used by app_factory during application startup
    """
    setup_logging(app_name="toolboxai")


# Logging manager singleton for app_factory
class LoggingManager:
    """
    Singleton logging manager for centralized logging access
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance"""
        return get_logger(name)

    def setup(self, app_name: str = "toolboxai", **kwargs) -> None:
        """Setup logging configuration"""
        setup_logging(app_name=app_name, **kwargs)


# Create singleton instance for import
logging_manager = LoggingManager()

# Import middleware and utilities for backward compatibility
try:
    from .logging_middleware import (
        CorrelationIDMiddleware,
        log_audit,
        log_error,
        log_execution_time,
    )
except ImportError:
    # If middleware module doesn't exist, provide dummy implementations
    pass

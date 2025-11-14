"""
Debug Configuration for ToolBoxAI Solutions

This module provides comprehensive debugging configuration for the development environment.
It includes settings for logging, profiling, testing, and debugging tools.
"""

import os
import sys
from pathlib import Path
from typing import Any

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src" / "shared"))


class DebugConfig:
    """Debug configuration for ToolBoxAI Solutions"""

    # Debug flags
    DEBUG = True
    TESTING = True
    PROFILING = False
    MEMORY_PROFILING = False
    COVERAGE = True

    # Logging configuration
    LOG_LEVEL = "DEBUG"
    LOG_FORMAT = "%(asctime)s [%(levelname)8s] %(name)s: %(message)s"
    LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    LOG_FILE = "logs/debug.log"
    LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5

    # Debugging tools
    DEBUGPY_PORT = 5678
    DEBUGPY_HOST = "localhost"
    DEBUGPY_WAIT_FOR_CLIENT = True

    # Testing configuration
    TEST_TIMEOUT = 30
    TEST_PARALLEL = False
    TEST_COVERAGE_THRESHOLD = 80

    # Performance profiling
    PROFILE_OUTPUT_DIR = "debug-reports/profiles"
    MEMORY_OUTPUT_DIR = "debug-reports/memory"
    COVERAGE_OUTPUT_DIR = "debug-reports/coverage"

    # Database debugging
    DB_ECHO = True
    DB_ECHO_POOL = True
    DB_POOL_PRE_PING = True

    # API debugging
    API_DEBUG = True
    API_LOG_REQUESTS = True
    API_LOG_RESPONSES = True

    # WebSocket debugging
    WS_DEBUG = True
    WS_LOG_MESSAGES = True

    # Rate limiting debugging
    RATE_LIMIT_DEBUG = True
    RATE_LIMIT_LOG_ATTEMPTS = True

    @classmethod
    def get_logging_config(cls) -> dict[str, Any]:
        """Get logging configuration dictionary"""
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {"format": cls.LOG_FORMAT, "datefmt": cls.LOG_DATE_FORMAT},
                "detailed": {
                    "format": "%(asctime)s [%(levelname)8s] %(name)s:%(lineno)d: %(message)s",
                    "datefmt": cls.LOG_DATE_FORMAT,
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": cls.LOG_LEVEL,
                    "formatter": "standard",
                    "stream": "ext://sys.stdout",
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": cls.LOG_LEVEL,
                    "formatter": "detailed",
                    "filename": cls.LOG_FILE,
                    "maxBytes": cls.LOG_MAX_SIZE,
                    "backupCount": cls.LOG_BACKUP_COUNT,
                },
            },
            "loggers": {
                "": {
                    "handlers": ["console", "file"],
                    "level": cls.LOG_LEVEL,
                    "propagate": False,
                },
                "uvicorn": {
                    "handlers": ["console", "file"],
                    "level": "INFO",
                    "propagate": False,
                },
                "fastapi": {
                    "handlers": ["console", "file"],
                    "level": "INFO",
                    "propagate": False,
                },
                "sqlalchemy": {
                    "handlers": ["console", "file"],
                    "level": "WARNING",
                    "propagate": False,
                },
            },
        }

    @classmethod
    def get_pytest_config(cls) -> dict[str, Any]:
        """Get pytest configuration dictionary"""
        return {
            "testpaths": ["tests"],
            "python_files": "test_*.py",
            "python_classes": "Test*",
            "python_functions": "test_*",
            "addopts": [
                "-v",
                "--tb=long",
                "--log-cli-level=DEBUG",
                "--log-cli-format=%(asctime)s [%(levelname)8s] %(name)s: %(message)s",
                "--log-cli-date-format=%Y-%m-%d %H:%M:%S",
                "--capture=no",
                "--pdb",
                "--pdbcls=debugpy:Debugger",
                "--debug",
                f"--timeout={cls.TEST_TIMEOUT}",
                "--timeout-method=thread",
                "--asyncio-mode=auto",
                "--strict-markers",
                "--disable-warnings",
                "-p",
                "no:unraisableexception",
            ],
            "markers": [
                "unit: Unit tests",
                "integration: Integration tests requiring external services",
                "e2e: End-to-end tests",
                "performance: Performance tests",
                "slow: Slow tests (>5s)",
                "asyncio: Async tests",
                "skip_in_ci: Skip in CI environment",
                "websocket: Tests requiring WebSocket connections",
                "requires_redis: Tests requiring Redis connection",
                "requires_db: Tests requiring database connection",
                "debug: Debug-specific tests",
                "profiling: Performance profiling tests",
                "memory: Memory usage tests",
            ],
            "log_cli": True,
            "log_cli_level": "DEBUG",
            "log_cli_format": "%(asctime)s [%(levelname)8s] %(name)s: %(message)s",
            "log_cli_date_format": "%Y-%m-%d %H:%M:%S",
            "capture": "no",
            "timeout": cls.TEST_TIMEOUT,
            "timeout_method": "thread",
            "asyncio_mode": "auto",
        }

    @classmethod
    def setup_pytest_debugpy(cls) -> None:
        """Setup debugpy for pytest debugging"""
        if not cls.DEBUG:
            return

        try:
            import debugpy
            import pytest

            # Setup debugpy for pytest
            if not debugpy.is_client_connected():
                debugpy.listen((cls.DEBUGPY_HOST, cls.DEBUGPY_PORT))
                print(
                    f"Debugpy listening on {cls.DEBUGPY_HOST}:{cls.DEBUGPY_PORT} for pytest debugging"
                )

            # Configure pytest to use debugpy
            pytest_config = cls.get_pytest_config()

            # Add debugpy integration to pytest
            if "--pdbcls=debugpy:Debugger" not in pytest_config["addopts"]:
                pytest_config["addopts"].append("--pdbcls=debugpy:Debugger")

            print("Pytest debugpy integration configured")

        except ImportError:
            print("debugpy not available for pytest debugging")
        except Exception as e:
            print(f"Failed to setup pytest debugpy: {e}")

    @classmethod
    def get_coverage_config(cls) -> dict[str, Any]:
        """Get coverage configuration dictionary"""
        return {
            "source": ["."],
            "omit": [
                "*/tests/*",
                "*/test_*",
                "*/venv/*",
                "*/venv_clean/*",
                "*/node_modules/*",
                "*/migrations/*",
                "*/__pycache__/*",
                "*/.*",
                "setup.py",
                "conftest.py",
            ],
            "exclude_lines": [
                "pragma: no cover",
                "def __repr__",
                "if self.debug:",
                "if settings.DEBUG",
                "raise AssertionError",
                "raise NotImplementedError",
                "if 0:",
                "if __name__ == .__main__.:",
                "class .*\\bProtocol\\):",
                "@(abc\\.)?abstractmethod",
            ],
        }

    @classmethod
    def setup_debugpy(cls) -> None:
        """Setup debugpy for remote debugging"""
        if not cls.DEBUG:
            return

        try:
            import debugpy

            debugpy.listen((cls.DEBUGPY_HOST, cls.DEBUGPY_PORT))
            print(f"Debugpy listening on {cls.DEBUGPY_HOST}:{cls.DEBUGPY_PORT}")

            if cls.DEBUGPY_WAIT_FOR_CLIENT:
                print("Waiting for debugger to attach...")
                debugpy.wait_for_client()
                print("Debugger attached!")

        except ImportError:
            print("debugpy not installed. Install with: pip install debugpy")
        except Exception as e:
            print(f"Failed to setup debugpy: {e}")

    @classmethod
    def setup_profiling(cls) -> None:
        """Setup performance profiling"""
        if not cls.PROFILING:
            return

        try:
            import cProfile
            import pstats
            from io import StringIO

            # Create output directory
            Path(cls.PROFILE_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

            # Start profiling
            cls.profiler = cProfile.Profile()
            cls.profiler.enable()
            print("Performance profiling enabled")

        except ImportError:
            print("cProfile not available")
        except Exception as e:
            print(f"Failed to setup profiling: {e}")

    @classmethod
    def setup_memory_profiling(cls) -> None:
        """Setup memory profiling"""
        if not cls.MEMORY_PROFILING:
            return

        try:
            import memory_profiler
            import psutil

            # Create output directory
            Path(cls.MEMORY_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

            # Monitor memory usage
            process = psutil.Process()
            print(
                f"Memory profiling enabled. Initial memory: {process.memory_info().rss / 1024 / 1024:.2f} MB"
            )

        except ImportError:
            print("memory_profiler or psutil not installed")
        except Exception as e:
            print(f"Failed to setup memory profiling: {e}")

    @classmethod
    def setup_environment(cls) -> None:
        """Setup debug environment variables"""
        os.environ["ENVIRONMENT"] = "development"
        os.environ["DEBUG"] = "true" if cls.DEBUG else "false"
        os.environ["TESTING"] = "true" if cls.TESTING else "false"
        os.environ["LOG_LEVEL"] = cls.LOG_LEVEL
        os.environ["PROFILING"] = "true" if cls.PROFILING else "false"
        os.environ["MEMORY_PROFILING"] = "true" if cls.MEMORY_PROFILING else "false"
        os.environ["COVERAGE"] = "true" if cls.COVERAGE else "false"

    @classmethod
    def initialize(cls) -> None:
        """Initialize debug configuration"""
        cls.setup_environment()
        cls.setup_debugpy()
        cls.setup_profiling()
        cls.setup_memory_profiling()

        print("Debug configuration initialized")
        print(f"Debug: {cls.DEBUG}")
        print(f"Testing: {cls.TESTING}")
        print(f"Profiling: {cls.PROFILING}")
        print(f"Memory Profiling: {cls.MEMORY_PROFILING}")
        print(f"Coverage: {cls.COVERAGE}")


# Initialize debug configuration when imported
if __name__ == "__main__":
    DebugConfig.initialize()

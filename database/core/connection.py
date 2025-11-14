"""
Database Connection Compatibility Module

This module provides backward compatibility for imports.
It re-exports the enhanced ConnectionManager from connection_manager.py

Use this for legacy code that imports from database.core.connection
"""

#  Re-export all public APIs from connection_manager
from database.core.connection_manager import (
    ConnectionConfig,
    ConnectionManager,
    PerformanceMonitor,
    get_connection_manager,
)

__all__ = [
    "ConnectionConfig",
    "ConnectionManager",
    "PerformanceMonitor",
    "get_connection_manager",
]

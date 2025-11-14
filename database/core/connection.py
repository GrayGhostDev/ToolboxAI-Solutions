"""
Database Connection Compatibility Module

This module provides backward compatibility for imports.
It re-exports the enhanced ConnectionManager from connection_manager.py

Use this for legacy code that imports from database.core.connection
"""

#  Re-export all public APIs from connection_manager
from database.core.connection_manager import (
    ConnectionConfig,
    OptimizedConnectionManager,
    PerformanceMonitor,
)

# Backward compatibility alias
ConnectionManager = OptimizedConnectionManager

__all__ = [
    "ConnectionConfig",
    "ConnectionManager",
    "OptimizedConnectionManager",
    "PerformanceMonitor",
]

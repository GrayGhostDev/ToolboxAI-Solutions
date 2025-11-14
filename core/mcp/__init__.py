"""
Model Context Protocol (MCP) Implementation for ToolboxAI Roblox Environment

This module provides context management for AI agents with:
- WebSocket server for real-time updates
- Memory persistence with token limits
- Vector embedding storage
- Protocol handlers for Roblox and educational contexts
"""

from .context_manager import ContextManager
from .memory_store import MemoryStore
from .server import MCPServer

__all__ = ["MCPServer", "ContextManager", "MemoryStore"]
__version__ = "1.0.0"

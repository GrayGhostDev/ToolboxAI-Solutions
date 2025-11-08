"""MCP Context Manager - Manages conversation context

Official MCP Documentation:
- https://modelcontextprotocol.io/
"""
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MCPContextManager:
    """
    Model Context Protocol Context Manager

    Manages context, memory, and state across agent interactions.
    Implements context window management and memory retrieval.
    """

    def __init__(self, max_context_length: int = 4000):
        """
        Initialize context manager

        Args:
            max_context_length: Maximum context window size
        """
        self.max_context_length = max_context_length
        self.context_store = {}
        self.message_history = []
        logger.info(f"MCPContextManager initialized with max length: {max_context_length}")

    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add message to context"""
        message = {
            "role": role,
            "content": content,
            "metadata": metadata or {}
        }
        self.message_history.append(message)

        # Trim if exceeds max length
        if len(self.message_history) > self.max_context_length:
            self.message_history = self.message_history[-self.max_context_length:]

    def get_context(self, n_messages: Optional[int] = None) -> List[Dict]:
        """Retrieve recent context"""
        if n_messages:
            return self.message_history[-n_messages:]
        return self.message_history

    def clear_context(self):
        """Clear all context"""
        self.message_history = []
        logger.info("Context cleared")


__all__ = ['MCPContextManager']

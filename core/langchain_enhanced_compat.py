"""
Compatibility module for langchain_enhanced_compat imports.

This module provides backward compatibility for imports that expect
langchain_enhanced_compat to be directly under core/, when it's actually
located at core/agents/integration/langchain_compat/langchain_enhanced_compat.py

Re-exports everything from the actual module location.
"""

from core.agents.integration.langchain_compat.langchain_enhanced_compat import *

__all__ = [
    "get_chat_model",
    "ChatPromptTemplate",
    "HumanMessage",
    "SystemMessage",
    "AIMessage",
    "BaseMessage",
]

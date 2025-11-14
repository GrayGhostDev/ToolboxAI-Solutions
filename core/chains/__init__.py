"""
LCEL Chain Components for LangChain

Modern chain builders using LangChain Expression Language (LCEL).
"""

from .agent_chains import (
    create_code_review_chain,
    create_content_generation_chain,
    create_quiz_generation_chain,
    create_script_generation_chain,
    create_terrain_generation_chain,
)
from .base_chains import (
    ChainExecutor,
    create_agent_chain,
    create_conditional_chain,
    create_parallel_chain,
    create_retrieval_chain,
    create_simple_chain,
)
from .utils import (
    chain_with_fallback,
    chain_with_retry,
    create_batch_processor,
    create_streaming_handler,
)

__all__ = [
    # Base chains
    "create_simple_chain",
    "create_agent_chain",
    "create_retrieval_chain",
    "create_parallel_chain",
    "create_conditional_chain",
    "ChainExecutor",
    # Agent-specific chains
    "create_content_generation_chain",
    "create_quiz_generation_chain",
    "create_code_review_chain",
    "create_terrain_generation_chain",
    "create_script_generation_chain",
    # Utilities
    "create_streaming_handler",
    "create_batch_processor",
    "chain_with_retry",
    "chain_with_fallback",
]

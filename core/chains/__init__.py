"""
LCEL Chain Components for LangChain

Modern chain builders using LangChain Expression Language (LCEL).
"""

from .base_chains import (
    create_simple_chain,
    create_agent_chain,
    create_retrieval_chain,
    create_parallel_chain,
    create_conditional_chain,
    ChainExecutor
)

from .agent_chains import (
    create_content_generation_chain,
    create_quiz_generation_chain,
    create_code_review_chain,
    create_terrain_generation_chain,
    create_script_generation_chain
)

from .utils import (
    create_streaming_handler,
    create_batch_processor,
    chain_with_retry,
    chain_with_fallback
)

__all__ = [
    # Base chains
    'create_simple_chain',
    'create_agent_chain',
    'create_retrieval_chain',
    'create_parallel_chain',
    'create_conditional_chain',
    'ChainExecutor',

    # Agent-specific chains
    'create_content_generation_chain',
    'create_quiz_generation_chain',
    'create_code_review_chain',
    'create_terrain_generation_chain',
    'create_script_generation_chain',

    # Utilities
    'create_streaming_handler',
    'create_batch_processor',
    'chain_with_retry',
    'chain_with_fallback'
]
"""
LangChain Modern Integration Layer

Provides modern LangChain v0.3+ imports and utilities following official best practices.
Includes LCEL (LangChain Expression Language) components and helpers.
"""

import logging
import os
from functools import lru_cache
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Core imports with modern patterns
try:
    # Models - Using modern initialization patterns
    # Note: init_chat_model has been deprecated/moved in LangChain 0.3+
    from langchain_anthropic import ChatAnthropic
    from langchain_openai import AzureChatOpenAI, ChatOpenAI

    # Try to import init_chat_model, but don't fail if not available
    try:
        from langchain_community.chat_models import init_chat_model
    except ImportError:
        init_chat_model = None

    # Messages
    # Callbacks for streaming and monitoring
    from langchain_core.callbacks import (
        AsyncCallbackManagerForLLMRunForChainRun,
        CallbackManagerForLLMRunForChainRun,
        StreamingStdOutCallbackHandler,
    )

    # Memory components - Note: LangChain legacy memory has Pydantic v2 compatibility issues
    # Use LangGraph's MemorySaver instead for state persistence
    # ConversationBufferMemory and ConversationSummaryMemory are deprecated
    # Document processing
    from langchain_core.documents import Document
    from langchain_core.messages import (
        AIMessage,
        BaseMessage,
        FunctionMessage,
        HumanMessage,
        SystemMessage,
        ToolMessage,
    )

    # Output Parsers - Including structured output parsers
    from langchain_core.output_parsers import (
        JsonOutputParser,
        PydanticOutputParser,
        ResponseSchema,
        StrOutputParser,
        StructuredOutputParser,
    )

    # Prompts - Modern prompt templates
    from langchain_core.prompts import (
        ChatPromptTemplate,
        FewShotChatMessagePromptTemplate,
        MessagesPlaceholder,
        PromptTemplate,
    )

    # LCEL Components - Core of modern LangChain
    from langchain_core.runnables import (
        Runnable,
        RunnableBranch,
        RunnableLambda,
        RunnableParallel,
        RunnablePassthrough,
        RunnableSequence,
        RunnableWithMessageHistory,
    )

    # Tools and Functions
    from langchain_core.tools import StructuredTool, Tool, tool
    from langchain_core.utils.function_calling import convert_to_openai_function
    from langgraph.checkpoint.memory import MemorySaver

    # LangGraph - Modern agent framework
    from langgraph.graph import END, StateGraph
    from langgraph.prebuilt import ToolExecutor, ToolInvocation

    # Retry and error handling - skip if not available
    try:
        from langchain_core.runnables.retry import Retry
    except ImportError:
        Retry = None

    LANGCHAIN_AVAILABLE = True

except ImportError as e:
    logger.warning(f"Some LangChain imports failed: {e}")
    LANGCHAIN_AVAILABLE = False

    # Provide fallback classes to prevent import errors
    class Runnable:
        pass

    class RunnablePassthrough:
        pass

    class ChatPromptTemplate:
        @classmethod
        def from_messages(cls, messages):
            return cls()

    class StrOutputParser:
        pass


def get_chat_model(
    model_name: Optional[str] = None,
    provider: Optional[str] = None,
    temperature: float = 0.7,
    **kwargs,
) -> Any:
    """
    Initialize a chat model using modern LangChain patterns.

    Args:
        model_name: Model identifier (e.g., "gpt-3.5-turbo", "claude-3-opus")
        provider: Provider name (e.g., "openai", "anthropic", "azure")
        temperature: Model temperature for response generation
        **kwargs: Additional model-specific parameters

    Returns:
        Initialized chat model instance
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("LangChain is not properly installed")

    # Use environment variables for defaults if not specified
    if not model_name:
        model_name = os.getenv("DEFAULT_MODEL", "gpt-3.5-turbo")

    if not provider:
        # Auto-detect provider based on model name
        if "gpt" in model_name.lower() or "turbo" in model_name.lower():
            provider = "openai"
        elif "claude" in model_name.lower():
            provider = "anthropic"
        else:
            provider = "openai"  # Default fallback

    # Try to use init_chat_model if available, otherwise use direct initialization
    if init_chat_model is not None:
        try:
            return init_chat_model(
                model_name, model_provider=provider, temperature=temperature, **kwargs
            )
        except Exception as e:
            logger.warning(
                f"Failed to initialize model with init_chat_model: {e}, falling back to direct initialization"
            )

    # Direct initialization (always works with current LangChain versions)
    if provider == "openai":
        return ChatOpenAI(model=model_name, temperature=temperature, **kwargs)
    elif provider == "anthropic":
        return ChatAnthropic(model=model_name, temperature=temperature, **kwargs)
    elif provider == "azure":
        return AzureChatOpenAI(model=model_name, temperature=temperature, **kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}")


@lru_cache(maxsize=32)
def create_chain_template(
    system_prompt: str,
    include_history: bool = False,
    output_parser: Optional[Any] = None,
) -> Any:
    """
    Create a reusable LCEL chain template.

    Args:
        system_prompt: System message for the chain
        include_history: Whether to include conversation history
        output_parser: Optional output parser (defaults to StrOutputParser)

    Returns:
        LCEL chain ready for execution
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("LangChain is not properly installed")

    messages = [
        SystemMessage(content=system_prompt),
    ]

    if include_history:
        messages.append(MessagesPlaceholder(variable_name="history", optional=True))

    messages.append(HumanMessage(content="{input}"))

    prompt = ChatPromptTemplate.from_messages(messages)

    if output_parser is None:
        output_parser = StrOutputParser()

    # Return LCEL chain using pipe operator pattern
    return prompt | output_parser


def create_parallel_chain(chains: dict[str, Any]) -> RunnableParallel:
    """
    Create a parallel execution chain for concurrent operations.

    Args:
        chains: Dictionary of chain name to chain instance

    Returns:
        RunnableParallel for concurrent execution
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("LangChain is not properly installed")

    return RunnableParallel(chains)


def create_tool_from_function(
    func: callable, name: str, description: str, args_schema: Optional[type] = None
) -> StructuredTool:
    """
    Create a structured tool from a Python function.

    Args:
        func: The function to wrap as a tool
        name: Tool name
        description: Tool description
        args_schema: Optional Pydantic model for arguments

    Returns:
        StructuredTool instance
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("LangChain is not properly installed")

    return StructuredTool.from_function(
        func=func, name=name, description=description, args_schema=args_schema
    )


# Export all modern components
__all__ = [
    # Models
    "get_chat_model",
    "ChatOpenAI",
    "AzureChatOpenAI",
    "ChatAnthropic",
    # Messages
    "BaseMessage",
    "HumanMessage",
    "AIMessage",
    "SystemMessage",
    "ToolMessage",
    "FunctionMessage",
    # Prompts
    "ChatPromptTemplate",
    "MessagesPlaceholder",
    "PromptTemplate",
    # Parsers
    "StrOutputParser",
    "JsonOutputParser",
    "PydanticOutputParser",
    "StructuredOutputParser",
    # LCEL Components
    "Runnable",
    "RunnablePassthrough",
    "RunnableParallel",
    "RunnableLambda",
    "RunnableSequence",
    "RunnableBranch",
    # Tools
    "Tool",
    "StructuredTool",
    "tool",
    # LangGraph
    "StateGraph",
    "END",
    "MemorySaver",
    # Helper functions
    "create_chain_template",
    "create_parallel_chain",
    "create_tool_from_function",
    # Flags
    "LANGCHAIN_AVAILABLE",
]

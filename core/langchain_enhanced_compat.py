"""
LangChain 0.3.x Enhanced Compatibility Layer - 2025 Phase 1.5 Implementation

Provides modern LangChain v0.3+ imports and utilities following official best practices.
Includes LCEL (LangChain Expression Language) components and helpers.

Updated for 2025 standards:
- Pydantic v2 compatibility (required by LangChain 0.3.x)
- Modern init_chat_model patterns
- Enhanced LCEL chain composition
- Structured output parsing
- LangGraph integration for agent workflows
- Comprehensive error handling and fallbacks
- Mock LLM integration for testing
"""

import os
import sys
import warnings
from typing import Any, Optional, Dict, List, Union, Type, Callable, AsyncGenerator, Generator
from functools import lru_cache, wraps
import logging
from contextlib import contextmanager, asynccontextmanager
import asyncio
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# Suppress Pydantic v1 deprecation warnings during transition
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")
warnings.filterwarnings("ignore", message=".*pydantic.*", category=FutureWarning)

# Configuration for LangChain mode
class LangChainMode(Enum):
    """LangChain operation modes"""
    PRODUCTION = "production"
    DEVELOPMENT = "development" 
    TESTING = "testing"
    MOCK = "mock"

@dataclass
class LangChainConfig:
    """Configuration for LangChain integration"""
    mode: LangChainMode = LangChainMode.DEVELOPMENT
    default_model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    timeout: int = 30
    enable_streaming: bool = False
    enable_callbacks: bool = True
    mock_responses: bool = None  # Auto-detect based on API key availability
    
    def __post_init__(self):
        if self.mock_responses is None:
            self.mock_responses = not os.getenv("OPENAI_API_KEY") or os.getenv("USE_MOCK_LLM", "false").lower() == "true"

# Global configuration instance
_config = LangChainConfig()

def get_langchain_config() -> LangChainConfig:
    """Get current LangChain configuration"""
    return _config

def set_langchain_config(config: LangChainConfig):
    """Set LangChain configuration"""
    global _config
    _config = config

# Core imports with modern patterns
try:
    # Models - Using modern initialization patterns
    try:
        from langchain_community.chat_models import init_chat_model
    except ImportError:
        # Fallback if init_chat_model not available in this version
        init_chat_model = None
    from langchain_openai import ChatOpenAI, AzureChatOpenAI
    from langchain_anthropic import ChatAnthropic
    
    # Messages - LangChain 0.3.x message types
    from langchain_core.messages import (
        BaseMessage,
        HumanMessage,
        AIMessage,
        SystemMessage,
        ToolMessage,
        FunctionMessage,
        ChatMessage
    )
    
    # Prompts - Modern prompt templates with LCEL support
    from langchain_core.prompts import (
        ChatPromptTemplate,
        MessagesPlaceholder,
        PromptTemplate,
        FewShotChatMessagePromptTemplate,
        PipelinePromptTemplate
    )
    
    # Output Parsers - Including structured output parsers
    from langchain_core.output_parsers import (
        StrOutputParser,
        JsonOutputParser,
        PydanticOutputParser,
        XMLOutputParser,
        YamlOutputParser
    )
    
    # LCEL Components - Core of modern LangChain
    from langchain_core.runnables import (
        Runnable,
        RunnablePassthrough,
        RunnableParallel,
        RunnableLambda,
        RunnableSequence,
        RunnableBranch,
        RunnableWithMessageHistory,
        RunnableConfig,
        RunnableBinding
    )
    
    # Tools and Functions - Modern tool patterns
    from langchain_core.tools import Tool, StructuredTool, tool
    from langchain_core.utils.function_calling import convert_to_openai_function
    
    # LangGraph - Modern agent framework
    from langgraph.graph import StateGraph, END, START
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.prebuilt import ToolExecutor, ToolInvocation
    
    # Callbacks for streaming and monitoring
    from langchain_core.callbacks import (
        AsyncCallbackManagerForChainRun,
        CallbackManagerForChainRun,
        StreamingStdOutCallbackHandler,
        BaseCallbackHandler
    )
    
    # Memory components - LangChain 0.3.x patterns
    from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
    from langchain_core.memory import BaseMemory
    
    # Document processing
    from langchain_core.documents import Document
    
    # Language models base classes
    from langchain_core.language_models import BaseLLM, BaseChatModel
    
    # Embeddings
    from langchain_core.embeddings import Embeddings
    
    # Schema definitions
    from langchain_core.schema import BaseRetriever, BaseOutputParser
    
    LANGCHAIN_AVAILABLE = True
    logger.info("LangChain 0.3.x imports successful")

except ImportError as e:
    logger.warning(f"Some LangChain imports failed: {e}")
    LANGCHAIN_AVAILABLE = False
    
    # Provide fallback classes to prevent import errors
    class Runnable:
        def __init__(self, *args, **kwargs):
            pass
        
        def invoke(self, input_data, **kwargs):
            return input_data
        
        async def ainvoke(self, input_data, **kwargs):
            return input_data
        
        def __or__(self, other):
            return RunnableSequence([self, other])
    
    class RunnablePassthrough(Runnable):
        pass
    
    class RunnableParallel(Runnable):
        def __init__(self, steps: Dict[str, Any]):
            self.steps = steps
    
    class ChatPromptTemplate:
        @classmethod
        def from_messages(cls, messages):
            return cls()
        
        def invoke(self, input_data):
            return {"messages": []}
    
    class StrOutputParser:
        def invoke(self, input_data):
            return str(input_data)
    
    class BaseMessage:
        def __init__(self, content: str):
            self.content = content
    
    class HumanMessage(BaseMessage):
        pass
    
    class AIMessage(BaseMessage):
        pass
    
    class SystemMessage(BaseMessage):
        pass

# Enhanced mock LLM for testing
try:
    from .agents.mock_llm import MockChatModel, MockLLM, get_mock_chat_model
    MOCK_LLM_AVAILABLE = True
except ImportError:
    logger.warning("Mock LLM not available, creating inline mock")
    
    class MockChatModel:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
        
        def invoke(self, messages, **kwargs):
            return AIMessage(content="Mock response for testing")
        
        async def ainvoke(self, messages, **kwargs):
            await asyncio.sleep(0.1)
            return AIMessage(content="Mock async response for testing")
    
    def get_mock_chat_model(**kwargs):
        return MockChatModel(**kwargs)
    
    MOCK_LLM_AVAILABLE = True

def get_chat_model(
    model_name: Optional[str] = None,
    provider: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    streaming: bool = False,
    **kwargs
) -> Any:
    """
    Initialize a chat model using modern LangChain 0.3.x patterns.
    
    Args:
        model_name: Model identifier (e.g., "gpt-3.5-turbo", "claude-3-opus")
        provider: Provider name (e.g., "openai", "anthropic", "azure")
        temperature: Model temperature for response generation
        max_tokens: Maximum tokens for response
        streaming: Enable streaming responses
        **kwargs: Additional model-specific parameters
    
    Returns:
        Initialized chat model instance
    """
    if not LANGCHAIN_AVAILABLE:
        logger.warning("LangChain not available, using mock model")
        return get_mock_chat_model(model=model_name or "mock", **kwargs)
    
    config = get_langchain_config()
    
    # Use environment variables for defaults if not specified
    if not model_name:
        model_name = config.default_model
    
    # Check if we should use mock
    if config.mock_responses or config.mode == LangChainMode.TESTING:
        logger.info(f"Using mock LLM for model: {model_name}")
        return get_mock_chat_model(model=model_name, temperature=temperature, **kwargs)
    
    if not provider:
        # Auto-detect provider based on model name
        if "gpt" in model_name.lower() or "turbo" in model_name.lower():
            provider = "openai"
        elif "claude" in model_name.lower():
            provider = "anthropic"
        elif "azure" in model_name.lower():
            provider = "azure"
        else:
            provider = "openai"  # Default fallback
    
    try:
        # Use the modern init_chat_model for automatic provider detection if available
        if init_chat_model:
            return init_chat_model(
                model_name,
                model_provider=provider,
                temperature=temperature,
                max_tokens=max_tokens,
                streaming=streaming,
                **kwargs
            )
        else:
            # Direct initialization if init_chat_model not available
            raise ImportError("init_chat_model not available")
    except Exception as e:
        logger.warning(f"Failed to initialize model with init_chat_model: {e}, falling back to direct initialization")
        
        # Fallback to direct initialization
        if provider == "openai":
            return ChatOpenAI(
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                streaming=streaming,
                **kwargs
            )
        elif provider == "anthropic":
            return ChatAnthropic(
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                streaming=streaming,
                **kwargs
            )
        elif provider == "azure":
            return AzureChatOpenAI(
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                streaming=streaming,
                **kwargs
            )
        else:
            logger.error(f"Unknown provider: {provider}, using mock model")
            return get_mock_chat_model(model=model_name, temperature=temperature, **kwargs)

@lru_cache(maxsize=32)
def create_chain_template(
    system_prompt: str,
    include_history: bool = False,
    output_parser: Optional[Any] = None,
    enable_streaming: bool = False
) -> Any:
    """
    Create a reusable LCEL chain template using LangChain 0.3.x patterns.
    
    Args:
        system_prompt: System message for the chain
        include_history: Whether to include conversation history
        output_parser: Optional output parser (defaults to StrOutputParser)
        enable_streaming: Enable streaming responses
    
    Returns:
        LCEL chain ready for execution
    """
    if not LANGCHAIN_AVAILABLE:
        # Return a simple mock chain
        class MockChain:
            def invoke(self, input_data):
                return f"Mock response for: {input_data.get('input', 'no input')}"
            async def ainvoke(self, input_data):
                await asyncio.sleep(0.1)
                return self.invoke(input_data)
        return MockChain()
    
    messages = [SystemMessage(content=system_prompt)]
    
    if include_history:
        messages.append(MessagesPlaceholder(variable_name="history"))
    
    messages.append(HumanMessage(content="{input}"))
    
    prompt = ChatPromptTemplate.from_messages(messages)
    
    if output_parser is None:
        output_parser = StrOutputParser()
    
    # Get appropriate model
    model = get_chat_model(streaming=enable_streaming)
    
    # Return LCEL chain using pipe operator pattern
    return prompt | model | output_parser

def create_parallel_chain(chains: Dict[str, Any]) -> Any:
    """
    Create a parallel execution chain for concurrent operations using LangChain 0.3.x.
    
    Args:
        chains: Dictionary of chain name to chain instance
    
    Returns:
        RunnableParallel for concurrent execution
    """
    if not LANGCHAIN_AVAILABLE:
        class MockParallelChain:
            def __init__(self, chains):
                self.chains = chains
            
            def invoke(self, input_data):
                return {name: f"Mock result for {name}" for name in self.chains.keys()}
            
            async def ainvoke(self, input_data):
                await asyncio.sleep(0.1)
                return self.invoke(input_data)
        
        return MockParallelChain(chains)
    
    return RunnableParallel(chains)

def create_tool_from_function(
    func: Callable,
    name: str,
    description: str,
    args_schema: Optional[Type] = None
) -> Any:
    """
    Create a structured tool from a Python function using LangChain 0.3.x patterns.
    
    Args:
        func: The function to wrap as a tool
        name: Tool name
        description: Tool description
        args_schema: Optional Pydantic model for arguments
    
    Returns:
        StructuredTool instance
    """
    if not LANGCHAIN_AVAILABLE:
        class MockTool:
            def __init__(self, func, name, description):
                self.func = func
                self.name = name
                self.description = description
            
            def invoke(self, input_data):
                try:
                    return self.func(input_data)
                except Exception as e:
                    return f"Mock tool error: {e}"
        
        return MockTool(func, name, description)
    
    return StructuredTool.from_function(
        func=func,
        name=name,
        description=description,
        args_schema=args_schema
    )

def create_agent_workflow(
    agent_function: Callable,
    tools: List[Any] = None,
    memory: Optional[Any] = None
) -> Any:
    """
    Create a LangGraph-based agent workflow using 0.3.x patterns.
    
    Args:
        agent_function: Main agent logic function
        tools: List of available tools
        memory: Optional memory component
    
    Returns:
        Compiled StateGraph for agent execution
    """
    if not LANGCHAIN_AVAILABLE:
        class MockAgentWorkflow:
            def __init__(self, agent_function, tools, memory):
                self.agent_function = agent_function
                self.tools = tools or []
                self.memory = memory
            
            def invoke(self, input_data):
                return {"output": f"Mock agent result for: {input_data}"}
            
            async def ainvoke(self, input_data):
                await asyncio.sleep(0.1)
                return self.invoke(input_data)
        
        return MockAgentWorkflow(agent_function, tools, memory)
    
    # Create StateGraph
    workflow = StateGraph(dict)
    
    # Add agent node
    workflow.add_node("agent", agent_function)
    
    # Add tool execution if tools provided
    if tools:
        tool_executor = ToolExecutor(tools)
        workflow.add_node("tools", tool_executor)
        
        # Add conditional edge for tool usage
        def should_continue(state):
            messages = state.get("messages", [])
            last_message = messages[-1] if messages else None
            return "tools" if last_message and hasattr(last_message, "tool_calls") else END
        
        workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
        workflow.add_edge("tools", "agent")
    else:
        workflow.add_edge("agent", END)
    
    # Set entry point
    workflow.set_entry_point("agent")
    
    # Add memory if provided
    if memory:
        return workflow.compile(checkpointer=memory)
    else:
        return workflow.compile()

@contextmanager
def langchain_context(config: Optional[LangChainConfig] = None):
    """
    Context manager for LangChain configuration.
    
    Args:
        config: Optional configuration to use within context
    """
    if config is None:
        yield
        return
    
    old_config = get_langchain_config()
    try:
        set_langchain_config(config)
        yield
    finally:
        set_langchain_config(old_config)

def enable_langchain_debugging():
    """Enable verbose debugging for LangChain operations"""
    import langchain
    langchain.debug = True
    logger.setLevel(logging.DEBUG)

def disable_langchain_debugging():
    """Disable verbose debugging for LangChain operations"""
    import langchain
    langchain.debug = False

# Structured output helpers for LangChain 0.3.x
def create_structured_output_chain(
    model: Any,
    output_schema: Type,
    system_prompt: str = "You are a helpful assistant that provides structured responses."
) -> Any:
    """
    Create a chain that produces structured output using Pydantic v2 schemas.
    
    Args:
        model: Language model to use
        output_schema: Pydantic v2 model for output structure
        system_prompt: System prompt for the model
    
    Returns:
        Chain that produces structured output
    """
    if not LANGCHAIN_AVAILABLE:
        class MockStructuredChain:
            def invoke(self, input_data):
                return {"structured": True, "mock": True}
            async def ainvoke(self, input_data):
                await asyncio.sleep(0.1)
                return self.invoke(input_data)
        return MockStructuredChain()
    
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_prompt),
        HumanMessage(content="{input}")
    ])
    
    parser = PydanticOutputParser(pydantic_object=output_schema)
    
    return prompt | model | parser

# Compatibility checks and validation
def validate_langchain_environment() -> Dict[str, Any]:
    """
    Validate the LangChain environment and return status information.
    
    Returns:
        Dictionary with validation results
    """
    results = {
        "langchain_available": LANGCHAIN_AVAILABLE,
        "mock_llm_available": MOCK_LLM_AVAILABLE,
        "openai_api_key": bool(os.getenv("OPENAI_API_KEY")),
        "use_mock_llm": os.getenv("USE_MOCK_LLM", "false").lower() == "true",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "config": None  # Will be set below with proper serialization
    }
    
    # Check for common issues
    issues = []
    
    if not LANGCHAIN_AVAILABLE:
        issues.append("LangChain not properly installed")
    
    if not results["openai_api_key"] and not results["use_mock_llm"]:
        issues.append("No OpenAI API key and mock LLM not enabled")
    
    # Check Pydantic version
    try:
        import pydantic
        pydantic_version = pydantic.version.VERSION
        results["pydantic_version"] = pydantic_version
        
        if pydantic_version.startswith("1."):
            issues.append("Pydantic v1 detected - LangChain 0.3.x requires Pydantic v2")
    except ImportError:
        issues.append("Pydantic not installed")
    
    # Make config JSON serializable
    if _config:
        config_dict = get_langchain_config().__dict__.copy()
        if "mode" in config_dict:
            config_dict["mode"] = config_dict["mode"].value  # Convert enum to string
        results["config"] = config_dict
    
    results["issues"] = issues
    results["status"] = "healthy" if not issues else "issues_detected"
    
    return results

# Migration helpers
def migrate_from_langchain_legacy(legacy_chain: Any) -> Any:
    """
    Helper to migrate legacy LangChain chains to 0.3.x LCEL patterns.
    
    Args:
        legacy_chain: Legacy LangChain chain
    
    Returns:
        Modern LCEL chain
    """
    logger.warning("Legacy chain migration not fully implemented")
    return legacy_chain

# Export all modern components
__all__ = [
    # Configuration
    'LangChainMode',
    'LangChainConfig',
    'get_langchain_config',
    'set_langchain_config',
    'langchain_context',
    
    # Models
    'get_chat_model',
    'ChatOpenAI',
    'AzureChatOpenAI', 
    'ChatAnthropic',
    
    # Messages
    'BaseMessage',
    'HumanMessage',
    'AIMessage',
    'SystemMessage',
    'ToolMessage',
    'FunctionMessage',
    
    # Prompts
    'ChatPromptTemplate',
    'MessagesPlaceholder',
    'PromptTemplate',
    
    # Parsers
    'StrOutputParser',
    'JsonOutputParser',
    'PydanticOutputParser',
    
    # LCEL Components
    'Runnable',
    'RunnablePassthrough',
    'RunnableParallel',
    'RunnableLambda',
    'RunnableSequence',
    'RunnableBranch',
    
    # Tools
    'Tool',
    'StructuredTool',
    'tool',
    
    # LangGraph
    'StateGraph',
    'END',
    'START',
    'MemorySaver',
    
    # Helper functions
    'create_chain_template',
    'create_parallel_chain',
    'create_tool_from_function',
    'create_agent_workflow',
    'create_structured_output_chain',
    
    # Validation and migration
    'validate_langchain_environment',
    'migrate_from_langchain_legacy',
    
    # Debugging
    'enable_langchain_debugging',
    'disable_langchain_debugging',
    
    # Flags
    'LANGCHAIN_AVAILABLE',
    'MOCK_LLM_AVAILABLE'
]

# Auto-configure based on environment
if __name__ == "__main__":
    # Run validation when module is executed directly
    import json
    import sys
    
    print("LangChain 0.3.x Enhanced Compatibility Layer")
    print("=" * 50)
    
    validation_results = validate_langchain_environment()
    print(json.dumps(validation_results, indent=2))
    
    if validation_results["issues"]:
        print("\n⚠️  Issues detected:")
        for issue in validation_results["issues"]:
            print(f"  - {issue}")
        sys.exit(1)
    else:
        print("\n✅ Environment is healthy")
        sys.exit(0)
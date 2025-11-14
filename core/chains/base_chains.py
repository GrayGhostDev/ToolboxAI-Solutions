"""
Base LCEL Chain Implementations

Provides modern LangChain Expression Language (LCEL) chain builders.
Following official LangChain v0.3+ patterns and best practices.
"""

import asyncio
import logging
from functools import lru_cache
from typing import Any, Callable, Optional, Union

from pydantic import BaseModel, Field

from core.langchain_compat import (
    LANGCHAIN_AVAILABLE,
    ChatPromptTemplate,
    HumanMessage,
    MessagesPlaceholder,
    RunnableBranch,
    RunnableParallel,
    RunnablePassthrough,
    RunnableSequence,
    StrOutputParser,
    SystemMessage,
    get_chat_model,
)

logger = logging.getLogger(__name__)


class ChainConfig(BaseModel):
    """Configuration for chain creation"""

    model_name: str = Field(default="gpt-3.5-turbo", description="Model to use")
    temperature: float = Field(default=0.7, description="Temperature for generation")
    max_tokens: Optional[int] = Field(default=None, description="Max tokens to generate")
    streaming: bool = Field(default=False, description="Enable streaming responses")
    timeout: int = Field(default=60, description="Timeout in seconds")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")
    cache_enabled: bool = Field(default=True, description="Enable caching")


def create_simple_chain(
    system_prompt: str, config: Optional[ChainConfig] = None
) -> RunnableSequence:
    """
    Create a simple LCEL chain with prompt | model | parser pattern.

    Args:
        system_prompt: System prompt for the chain
        config: Chain configuration

    Returns:
        LCEL chain ready for execution
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("LangChain not available")

    config = config or ChainConfig()

    # Create prompt template
    prompt = ChatPromptTemplate.from_messages(
        [SystemMessage(content=system_prompt), HumanMessage(content="{input}")]
    )

    # Get model
    model = get_chat_model(
        model_name=config.model_name,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )

    # Create parser
    parser = StrOutputParser()

    # Build LCEL chain using pipe operator
    chain = prompt | model | parser

    logger.debug(f"Created simple chain with model {config.model_name}")
    return chain


def create_agent_chain(
    system_prompt: str,
    tools: list[Any],
    config: Optional[ChainConfig] = None,
    include_history: bool = True,
) -> RunnableSequence:
    """
    Create an agent chain with tool execution capabilities.

    Args:
        system_prompt: System prompt for the agent
        tools: List of tools available to the agent
        config: Chain configuration
        include_history: Whether to include conversation history

    Returns:
        LCEL agent chain with tool execution
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("LangChain not available")

    config = config or ChainConfig()

    # Build messages for prompt
    messages = [SystemMessage(content=system_prompt)]

    if include_history:
        messages.append(MessagesPlaceholder(variable_name="history", optional=True))

    messages.extend(
        [
            HumanMessage(content="{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad", optional=True),
        ]
    )

    prompt = ChatPromptTemplate.from_messages(messages)

    # Get model with tool binding
    model = get_chat_model(model_name=config.model_name, temperature=config.temperature)

    if tools:
        model = model.bind_tools(tools)

    # Create agent chain
    chain = (
        RunnablePassthrough.assign(agent_scratchpad=lambda x: x.get("intermediate_steps", []))
        | prompt
        | model
        | StrOutputParser()
    )

    logger.debug(f"Created agent chain with {len(tools)} tools")
    return chain


def create_retrieval_chain(
    system_prompt: str, retriever: Any, config: Optional[ChainConfig] = None
) -> RunnableSequence:
    """
    Create a retrieval-augmented generation (RAG) chain.

    Args:
        system_prompt: System prompt for the chain
        retriever: Document retriever
        config: Chain configuration

    Returns:
        LCEL RAG chain
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("LangChain not available")

    config = config or ChainConfig()

    # Create prompt with context
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content="""Context: {context}

Question: {question}

Answer based on the context provided."""
            ),
        ]
    )

    model = get_chat_model(model_name=config.model_name, temperature=config.temperature)

    # Build RAG chain
    chain = (
        RunnableParallel(context=retriever, question=RunnablePassthrough())
        | prompt
        | model
        | StrOutputParser()
    )

    logger.debug("Created retrieval chain")
    return chain


def create_parallel_chain(chains: dict[str, RunnableSequence]) -> RunnableParallel:
    """
    Create a parallel execution chain for concurrent operations.

    Args:
        chains: Dictionary of chain name to chain instance

    Returns:
        RunnableParallel for concurrent execution
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("LangChain not available")

    parallel = RunnableParallel(chains)
    logger.debug(f"Created parallel chain with {len(chains)} branches")
    return parallel


def create_conditional_chain(
    condition: Callable[[dict], str],
    branches: dict[str, RunnableSequence],
    default: Optional[RunnableSequence] = None,
) -> RunnableBranch:
    """
    Create a conditional chain that routes based on input.

    Args:
        condition: Function to determine which branch to take
        branches: Dictionary of branch name to chain
        default: Default chain if no condition matches

    Returns:
        RunnableBranch for conditional execution
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("LangChain not available")

    # Build branch conditions
    branch_list = []
    for branch_name, branch_chain in branches.items():
        branch_list.append((lambda x, name=branch_name: condition(x) == name, branch_chain))

    # Create branch with default
    if default:
        chain = RunnableBranch(*branch_list, default)
    else:
        # Use first branch as default if not specified
        chain = RunnableBranch(*branch_list, list(branches.values())[0])

    logger.debug(f"Created conditional chain with {len(branches)} branches")
    return chain


class ChainExecutor:
    """
    Executor for running LCEL chains with enhanced features.
    Provides streaming, batching, retries, and monitoring.
    """

    def __init__(self, chain: RunnableSequence, config: Optional[ChainConfig] = None):
        """
        Initialize chain executor.

        Args:
            chain: LCEL chain to execute
            config: Execution configuration
        """
        self.chain = chain
        self.config = config or ChainConfig()
        self.execution_count = 0
        self.total_tokens = 0

    async def execute(
        self,
        input_data: Union[str, dict[str, Any]],
        callbacks: Optional[list[Any]] = None,
    ) -> Any:
        """
        Execute the chain with input data.

        Args:
            input_data: Input for the chain
            callbacks: Optional callbacks for execution

        Returns:
            Chain execution result
        """
        # Normalize input
        if isinstance(input_data, str):
            input_data = {"input": input_data}

        # Track execution
        self.execution_count += 1

        try:
            # Execute with retry logic
            for attempt in range(self.config.retry_attempts):
                try:
                    if self.config.streaming:
                        # Stream response
                        result = ""
                        async for chunk in self.chain.astream(
                            input_data, config={"callbacks": callbacks}
                        ):
                            result += chunk
                        return result
                    else:
                        # Regular execution
                        result = await self.chain.ainvoke(
                            input_data, config={"callbacks": callbacks}
                        )
                        return result

                except Exception as e:
                    if attempt == self.config.retry_attempts - 1:
                        raise
                    logger.warning(f"Chain execution attempt {attempt + 1} failed: {e}")
                    await asyncio.sleep(2**attempt)  # Exponential backoff

        except Exception as e:
            logger.error(f"Chain execution failed after {self.config.retry_attempts} attempts: {e}")
            raise

    async def batch_execute(
        self, inputs: list[Union[str, dict[str, Any]]], max_concurrency: int = 5
    ) -> list[Any]:
        """
        Execute chain on multiple inputs concurrently.

        Args:
            inputs: List of inputs
            max_concurrency: Maximum concurrent executions

        Returns:
            List of results
        """
        # Normalize inputs
        normalized = []
        for inp in inputs:
            if isinstance(inp, str):
                normalized.append({"input": inp})
            else:
                normalized.append(inp)

        # Execute in batches
        results = []
        semaphore = asyncio.Semaphore(max_concurrency)

        async def execute_with_semaphore(input_data):
            async with semaphore:
                return await self.execute(input_data)

        tasks = [execute_with_semaphore(inp) for inp in normalized]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        return [r for r in results if not isinstance(r, Exception)]

    def get_metrics(self) -> dict[str, Any]:
        """
        Get execution metrics.

        Returns:
            Dictionary of metrics
        """
        return {
            "execution_count": self.execution_count,
            "total_tokens": self.total_tokens,
            "config": self.config.dict(),
        }


# Factory functions for common chain patterns
@lru_cache(maxsize=32)
def get_qa_chain(temperature: float = 0.7) -> RunnableSequence:
    """Get a question-answering chain"""
    return create_simple_chain(
        "You are a helpful assistant that answers questions accurately and concisely.",
        ChainConfig(temperature=temperature),
    )


@lru_cache(maxsize=32)
def get_summarization_chain(temperature: float = 0.3) -> RunnableSequence:
    """Get a summarization chain"""
    return create_simple_chain(
        "You are an expert at summarizing text. Provide clear, concise summaries.",
        ChainConfig(temperature=temperature),
    )


@lru_cache(maxsize=32)
def get_code_generation_chain(
    language: str = "python", temperature: float = 0.5
) -> RunnableSequence:
    """Get a code generation chain"""
    return create_simple_chain(
        f"You are an expert {language} programmer. Generate clean, efficient, well-commented code.",
        ChainConfig(temperature=temperature),
    )

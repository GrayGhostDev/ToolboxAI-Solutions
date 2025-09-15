"""
LCEL Chain Utilities

Helper functions and utilities for LCEL chains.
"""

import asyncio
import logging
from typing import Any, AsyncIterator, Callable, Dict, List, Optional
from functools import wraps
import time

from core.langchain_compat import (
    LANGCHAIN_AVAILABLE,
    RunnableLambda,
    RunnableSequence,
    StreamingStdOutCallbackHandler
)

logger = logging.getLogger(__name__)


class StreamingHandler:
    """
    Handler for streaming chain responses.
    """

    def __init__(self, callback: Optional[Callable[[str], None]] = None):
        """
        Initialize streaming handler.

        Args:
            callback: Optional callback for each chunk
        """
        self.callback = callback or print
        self.chunks = []
        self.complete_response = ""

    async def handle_chunk(self, chunk: str):
        """Handle a streaming chunk"""
        self.chunks.append(chunk)
        self.complete_response += chunk
        if self.callback:
            self.callback(chunk)

    def get_response(self) -> str:
        """Get the complete response"""
        return self.complete_response

    def reset(self):
        """Reset the handler"""
        self.chunks = []
        self.complete_response = ""


def create_streaming_handler(
    callback: Optional[Callable[[str], None]] = None
) -> StreamingHandler:
    """
    Create a streaming handler for chain responses.

    Args:
        callback: Optional callback for each chunk

    Returns:
        StreamingHandler instance
    """
    return StreamingHandler(callback)


class BatchProcessor:
    """
    Processor for batch chain execution.
    """

    def __init__(
        self,
        chain: RunnableSequence,
        max_concurrency: int = 5,
        batch_size: int = 10
    ):
        """
        Initialize batch processor.

        Args:
            chain: Chain to execute
            max_concurrency: Maximum concurrent executions
            batch_size: Size of each batch
        """
        self.chain = chain
        self.max_concurrency = max_concurrency
        self.batch_size = batch_size
        self.results = []
        self.errors = []

    async def process(
        self,
        inputs: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Process inputs in batches.

        Args:
            inputs: List of inputs to process
            progress_callback: Optional progress callback

        Returns:
            Dictionary with results and errors
        """
        self.results = []
        self.errors = []

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrency)

        async def process_item(item: Dict[str, Any], index: int):
            async with semaphore:
                try:
                    result = await self.chain.ainvoke(item)
                    self.results.append({"index": index, "result": result})
                except Exception as e:
                    self.errors.append({"index": index, "error": str(e)})
                finally:
                    if progress_callback:
                        progress_callback(index + 1, len(inputs))

        # Process all inputs
        tasks = [
            process_item(item, i)
            for i, item in enumerate(inputs)
        ]

        await asyncio.gather(*tasks, return_exceptions=True)

        return {
            "successful": len(self.results),
            "failed": len(self.errors),
            "results": self.results,
            "errors": self.errors
        }


def create_batch_processor(
    chain: RunnableSequence,
    max_concurrency: int = 5,
    batch_size: int = 10
) -> BatchProcessor:
    """
    Create a batch processor for chain execution.

    Args:
        chain: Chain to execute
        max_concurrency: Maximum concurrent executions
        batch_size: Size of each batch

    Returns:
        BatchProcessor instance
    """
    return BatchProcessor(chain, max_concurrency, batch_size)


def chain_with_retry(
    chain: RunnableSequence,
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    retry_exceptions: tuple = (Exception,)
) -> RunnableSequence:
    """
    Wrap a chain with retry logic.

    Args:
        chain: Chain to wrap
        max_retries: Maximum number of retries
        backoff_factor: Exponential backoff factor
        retry_exceptions: Exceptions to retry on

    Returns:
        Chain with retry logic
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("LangChain not available")

    async def retry_wrapper(input_data: Dict[str, Any]) -> Any:
        """Execute chain with retries"""
        last_exception = None

        for attempt in range(max_retries):
            try:
                return await chain.ainvoke(input_data)
            except retry_exceptions as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    logger.warning(
                        f"Chain execution failed (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {wait_time}s: {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Chain execution failed after {max_retries} attempts")

        raise last_exception

    return RunnableLambda(retry_wrapper)


def chain_with_fallback(
    primary_chain: RunnableSequence,
    fallback_chain: RunnableSequence,
    fallback_on: tuple = (Exception,)
) -> RunnableSequence:
    """
    Create a chain with fallback logic.

    Args:
        primary_chain: Primary chain to execute
        fallback_chain: Fallback chain if primary fails
        fallback_on: Exceptions to trigger fallback

    Returns:
        Chain with fallback logic
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("LangChain not available")

    async def fallback_wrapper(input_data: Dict[str, Any]) -> Any:
        """Execute primary chain with fallback"""
        try:
            return await primary_chain.ainvoke(input_data)
        except fallback_on as e:
            logger.warning(f"Primary chain failed, using fallback: {e}")
            return await fallback_chain.ainvoke(input_data)

    return RunnableLambda(fallback_wrapper)


def chain_with_timeout(
    chain: RunnableSequence,
    timeout: int = 60
) -> RunnableSequence:
    """
    Wrap a chain with timeout.

    Args:
        chain: Chain to wrap
        timeout: Timeout in seconds

    Returns:
        Chain with timeout
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("LangChain not available")

    async def timeout_wrapper(input_data: Dict[str, Any]) -> Any:
        """Execute chain with timeout"""
        try:
            async with asyncio.timeout(timeout):
                return await chain.ainvoke(input_data)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Chain execution timed out after {timeout} seconds")

    return RunnableLambda(timeout_wrapper)


def chain_with_cache(
    chain: RunnableSequence,
    cache_ttl: int = 3600
) -> RunnableSequence:
    """
    Wrap a chain with caching.

    Args:
        chain: Chain to wrap
        cache_ttl: Cache TTL in seconds

    Returns:
        Chain with caching
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("LangChain not available")

    cache = {}
    cache_times = {}

    async def cache_wrapper(input_data: Dict[str, Any]) -> Any:
        """Execute chain with caching"""
        # Create cache key from input
        cache_key = str(sorted(input_data.items()))

        # Check cache
        if cache_key in cache:
            cached_time = cache_times.get(cache_key, 0)
            if time.time() - cached_time < cache_ttl:
                logger.debug("Returning cached result")
                return cache[cache_key]

        # Execute and cache
        result = await chain.ainvoke(input_data)
        cache[cache_key] = result
        cache_times[cache_key] = time.time()

        return result

    return RunnableLambda(cache_wrapper)


def chain_with_metrics(
    chain: RunnableSequence,
    metrics_callback: Optional[Callable[[Dict[str, Any]], None]] = None
) -> RunnableSequence:
    """
    Wrap a chain with metrics collection.

    Args:
        chain: Chain to wrap
        metrics_callback: Optional callback for metrics

    Returns:
        Chain with metrics collection
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("LangChain not available")

    async def metrics_wrapper(input_data: Dict[str, Any]) -> Any:
        """Execute chain with metrics"""
        start_time = time.time()
        error = None
        result = None

        try:
            result = await chain.ainvoke(input_data)
            return result
        except Exception as e:
            error = e
            raise
        finally:
            execution_time = time.time() - start_time
            metrics = {
                "execution_time": execution_time,
                "success": error is None,
                "error": str(error) if error else None,
                "input_size": len(str(input_data)),
                "output_size": len(str(result)) if result else 0
            }

            if metrics_callback:
                metrics_callback(metrics)
            else:
                logger.info(f"Chain metrics: {metrics}")

    return RunnableLambda(metrics_wrapper)


# Decorator versions for convenience
def with_retry(max_retries: int = 3, backoff_factor: float = 2.0):
    """Decorator to add retry logic to a chain function"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            chain = func(*args, **kwargs)
            return chain_with_retry(chain, max_retries, backoff_factor)
        return wrapper
    return decorator


def with_timeout(timeout: int = 60):
    """Decorator to add timeout to a chain function"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            chain = func(*args, **kwargs)
            return chain_with_timeout(chain, timeout)
        return wrapper
    return decorator


def with_cache(cache_ttl: int = 3600):
    """Decorator to add caching to a chain function"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            chain = func(*args, **kwargs)
            return chain_with_cache(chain, cache_ttl)
        return wrapper
    return decorator
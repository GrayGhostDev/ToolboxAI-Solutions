"""Supervisor Agent - Compatibility Shim
Re-exports SupervisorAgent from apps.backend.agents.agent
"""

try:
    from apps.backend.agents.agent import SupervisorAgent
except ImportError:
    # Fallback if SupervisorAgent not available
    import logging

    from langchain_core.chat_history import InMemoryChatMessageHistory
    from langchain_openai import ChatOpenAI

    logger = logging.getLogger(__name__)

    class SupervisorAgent:
        """Placeholder supervisor agent for hierarchical task orchestration"""

        def __init__(self, llm=None, *args, **kwargs):
            """Initialize supervisor agent"""
            self.llm = llm or ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7, http_client=None, http_async_client=None)
            self.chat_history = InMemoryChatMessageHistory()
            self.agents = {}
            self._agents_initialized = False
            logger.info("SupervisorAgent placeholder initialized")


__all__ = ["SupervisorAgent"]

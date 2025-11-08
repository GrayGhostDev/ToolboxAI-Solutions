"""Supervisor Agent - Compatibility Shim
Re-exports SupervisorAgent from apps.backend.agents.agent
"""
try:
    from apps.backend.agents.agent import SupervisorAgent
except ImportError:
    # Fallback if SupervisorAgent not available
    from langchain_core.chat_history import InMemoryChatMessageHistory
    from langchain_openai import ChatOpenAI
    import logging

    logger = logging.getLogger(__name__)

    class SupervisorAgent:
        """Placeholder supervisor agent for hierarchical task orchestration"""

        def __init__(self, llm=None, *args, **kwargs):
            """Initialize supervisor agent"""
            self.llm = llm or ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)
            self.chat_history = InMemoryChatMessageHistory()
            self.agents = {}
            self._agents_initialized = False
            logger.info("SupervisorAgent placeholder initialized")

__all__ = ['SupervisorAgent']

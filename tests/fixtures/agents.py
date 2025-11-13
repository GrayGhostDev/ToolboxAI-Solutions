"""
Agent test fixtures for ToolboxAI test suite.

Provides reusable agent fixtures for testing.
"""


# Add parent directory to path for imports
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@dataclass
class MockTaskResult:
    """Mock task result for agent testing."""

    success: bool
    result: Any
    error: str | None = None
    metadata: dict[str, Any] | None = None

    @classmethod
    def create(cls, success: bool = True, result: Any = None, error: str | None = None):
        """Create a mock task result."""
        return cls(
            success=success,
            result=result or {},
            error=error,
            metadata={"timestamp": datetime.utcnow().isoformat()},
        )


@pytest.fixture
def mock_llm():
    """
    Create a mock LLM for agent testing (2025 LangChain patterns).
    Includes proper message handling and caching simulation.
    """
    from unittest.mock import MagicMock

    llm = MagicMock()
    llm.model_name = "mock-gpt-4"
    llm.temperature = 0.7
    llm.max_tokens = 2000
    llm.cache = None  # Can be set to mock cache for testing

    # Mock invoke method with AIMessage response (2025 pattern)
    def mock_invoke(messages, **kwargs):
        if isinstance(messages, list) and messages:
            return MagicMock(
                content="This is a mock LLM response",
                additional_kwargs={},
                response_metadata={
                    "model": "mock-gpt-4",
                    "tokens_used": 150,
                    "finish_reason": "stop",
                },
            )
        return MagicMock(content="Empty response")

    llm.invoke = Mock(side_effect=mock_invoke)

    # Mock async invoke with proper async generator
    async def mock_ainvoke(messages, **kwargs):
        if isinstance(messages, list) and messages:
            return MagicMock(
                content="This is a mock async LLM response",
                additional_kwargs={},
                response_metadata={
                    "model": "mock-gpt-4",
                    "tokens_used": 150,
                    "finish_reason": "stop",
                },
            )
        return MagicMock(content="Empty async response")

    llm.ainvoke = AsyncMock(side_effect=mock_ainvoke)

    # Mock streaming with async generator (2025 pattern)
    async def mock_astream(messages, **kwargs):
        chunks = ["This ", "is ", "an ", "async ", "streaming ", "response"]
        for chunk in chunks:
            yield MagicMock(content=chunk)

    llm.astream = mock_astream

    # Mock batch processing (2025 LangChain feature)
    llm.batch = Mock(return_value=[MagicMock(content=f"Batch response {i}") for i in range(3)])

    llm.abatch = AsyncMock(
        return_value=[MagicMock(content=f"Async batch response {i}") for i in range(3)]
    )

    # Mock generate method for legacy compatibility
    llm.generate = Mock(
        return_value={
            "generations": [
                [{"text": "Generated text response", "generation_info": {"finish_reason": "stop"}}]
            ],
            "llm_output": {"token_usage": {"total_tokens": 100}},
        }
    )

    return llm


@pytest.fixture
def mock_agent_config():
    """Create a mock agent configuration."""
    return {
        "name": "test_agent",
        "description": "A test agent for automated testing",
        "model": "gpt-4",
        "temperature": 0.7,
        "max_retries": 3,
        "timeout": 30,
        "tools": ["search", "calculator", "code_executor"],
        "memory": {"type": "conversation_buffer", "max_tokens": 2000},
        "system_prompt": "You are a helpful assistant for testing purposes.",
        "capabilities": {
            "can_execute_code": True,
            "can_search_web": True,
            "can_access_database": False,
        },
    }


@pytest.fixture
def mock_agent():
    """Create a mock agent."""
    agent = Mock()
    agent.name = "test_agent"
    agent.config = mock_agent_config()
    agent.llm = mock_llm()
    agent.memory = Mock()
    agent.tools = []

    # Mock execute method
    agent.execute = Mock(
        return_value=MockTaskResult.create(
            success=True, result={"message": "Task completed successfully"}
        )
    )

    # Mock async execute
    agent.aexecute = AsyncMock(
        return_value=MockTaskResult.create(
            success=True, result={"message": "Async task completed successfully"}
        )
    )

    # Mock planning
    agent.plan = Mock(
        return_value={
            "steps": [
                "Step 1: Analyze the problem",
                "Step 2: Generate solution",
                "Step 3: Validate results",
            ],
            "estimated_time": 5,
        }
    )

    # Mock reasoning
    agent.reason = Mock(
        return_value={
            "thought": "I need to solve this step by step",
            "action": "execute_code",
            "action_input": {"code": "print('Hello')"},
        }
    )

    return agent


@pytest.fixture
def mock_swarm_controller():
    """Create a mock swarm controller for multi-agent systems."""
    controller = Mock()
    controller.agents = {}
    controller.tasks = []
    controller.results = {}

    # Mock agent management
    controller.add_agent = Mock()
    controller.remove_agent = Mock()
    controller.get_agent = Mock(return_value=mock_agent())
    controller.list_agents = Mock(return_value=["agent1", "agent2", "agent3"])

    # Mock task execution
    controller.execute_task = AsyncMock(
        return_value=MockTaskResult.create(
            success=True, result={"completed_by": "agent1", "output": "Task result"}
        )
    )

    # Mock coordination
    controller.coordinate = AsyncMock(
        return_value={
            "plan": "Multi-agent execution plan",
            "assignments": {
                "agent1": ["task1", "task2"],
                "agent2": ["task3"],
                "agent3": ["task4", "task5"],
            },
        }
    )

    # Mock communication
    controller.broadcast = AsyncMock()
    controller.send_message = AsyncMock()
    controller.receive_message = AsyncMock(
        return_value={
            "from": "agent1",
            "to": "controller",
            "content": "Status update",
            "timestamp": datetime.utcnow().isoformat(),
        }
    )

    return controller


@pytest.fixture
def mock_tool():
    """Create a mock tool for agent use."""
    tool = Mock()
    tool.name = "test_tool"
    tool.description = "A test tool for agent testing"
    tool.parameters = {
        "type": "object",
        "properties": {"input": {"type": "string", "description": "Tool input"}},
        "required": ["input"],
    }

    # Mock run method
    tool.run = Mock(return_value="Tool execution result")
    tool.arun = AsyncMock(return_value="Async tool execution result")

    # Mock validation
    tool.validate_input = Mock(return_value=True)
    tool.format_output = Mock(return_value={"result": "formatted output"})

    return tool


@pytest.fixture
def mock_memory():
    """Create a mock memory system for agents."""
    memory = Mock()
    memory.messages = []
    memory.max_tokens = 2000

    # Mock memory operations
    memory.add_message = Mock()
    memory.get_messages = Mock(
        return_value=[
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
    )
    memory.clear = Mock()
    memory.save = Mock()
    memory.load = Mock()

    # Mock search
    memory.search = Mock(
        return_value=[
            {"content": "Relevant memory 1", "score": 0.95},
            {"content": "Relevant memory 2", "score": 0.87},
        ]
    )

    return memory


@pytest.fixture
def mock_vector_store():
    """Create a mock vector store for RAG systems."""
    store = Mock()
    store.name = "test_vector_store"
    store.dimension = 1536

    # Mock operations
    store.add_documents = AsyncMock(return_value=["doc1", "doc2", "doc3"])
    store.delete_documents = AsyncMock(return_value=True)

    # Mock search
    store.similarity_search = AsyncMock(
        return_value=[
            {
                "content": "Similar document 1",
                "metadata": {"source": "test.pdf", "page": 1},
                "score": 0.92,
            },
            {
                "content": "Similar document 2",
                "metadata": {"source": "test.pdf", "page": 3},
                "score": 0.85,
            },
        ]
    )

    store.max_marginal_relevance_search = AsyncMock(
        return_value=[
            {"content": "Diverse result 1", "metadata": {"source": "doc1.pdf"}, "score": 0.90},
            {"content": "Diverse result 2", "metadata": {"source": "doc2.pdf"}, "score": 0.82},
        ]
    )

    return store


@pytest.fixture
def mock_embeddings():
    """Create a mock embeddings model."""
    embeddings = Mock()
    embeddings.model_name = "text-embedding-ada-002"
    embeddings.dimension = 1536

    # Mock embedding generation
    embeddings.embed_documents = Mock(
        return_value=[[0.1] * 1536, [0.2] * 1536, [0.3] * 1536]  # Mock embedding vector
    )

    embeddings.embed_query = Mock(return_value=[0.15] * 1536)

    # Async versions
    embeddings.aembed_documents = AsyncMock(return_value=[[0.1] * 1536, [0.2] * 1536, [0.3] * 1536])

    embeddings.aembed_query = AsyncMock(return_value=[0.15] * 1536)

    return embeddings


@pytest.fixture
def mock_chain():
    """Create a mock LangChain chain."""
    chain = Mock()
    chain.name = "test_chain"

    # Mock invoke
    chain.invoke = Mock(
        return_value={"output": "Chain execution result", "intermediate_steps": ["step1", "step2"]}
    )

    chain.ainvoke = AsyncMock(
        return_value={
            "output": "Async chain execution result",
            "intermediate_steps": ["step1", "step2"],
        }
    )

    # Mock batch processing
    chain.batch = Mock(
        return_value=[{"output": "Result 1"}, {"output": "Result 2"}, {"output": "Result 3"}]
    )

    chain.abatch = AsyncMock(
        return_value=[
            {"output": "Async Result 1"},
            {"output": "Async Result 2"},
            {"output": "Async Result 3"},
        ]
    )

    # Mock streaming
    chain.stream = Mock(
        return_value=iter([{"token": "This "}, {"token": "is "}, {"token": "streaming"}])
    )

    return chain


@pytest.fixture
def mock_workflow():
    """Create a mock workflow for complex agent operations."""
    workflow = Mock()
    workflow.id = str(uuid.uuid4())
    workflow.name = "test_workflow"
    workflow.status = "pending"
    workflow.steps = []
    workflow.results = {}

    # Mock workflow operations
    workflow.add_step = Mock()
    workflow.remove_step = Mock()
    workflow.execute = AsyncMock(
        return_value={
            "status": "completed",
            "results": {
                "step1": {"output": "Step 1 result"},
                "step2": {"output": "Step 2 result"},
                "step3": {"output": "Step 3 result"},
            },
            "duration": 5.2,
        }
    )

    workflow.pause = Mock()
    workflow.resume = Mock()
    workflow.cancel = Mock()
    workflow.get_status = Mock(return_value="running")

    return workflow


@pytest.fixture
def mock_rag_pipeline():
    """Create a mock RAG (Retrieval-Augmented Generation) pipeline."""
    pipeline = Mock()
    pipeline.retriever = mock_vector_store()
    pipeline.generator = mock_llm()

    # Mock pipeline execution
    pipeline.run = AsyncMock(
        return_value={
            "query": "Test query",
            "retrieved_documents": [
                {"content": "Doc 1", "score": 0.9},
                {"content": "Doc 2", "score": 0.85},
            ],
            "generated_answer": "This is the generated answer based on retrieved context",
            "metadata": {"retrieval_time": 0.5, "generation_time": 1.2, "total_time": 1.7},
        }
    )

    # Mock configuration
    pipeline.configure = Mock()
    pipeline.get_config = Mock(
        return_value={"retriever_k": 5, "reranker_enabled": True, "generation_temperature": 0.7}
    )

    return pipeline


@pytest.fixture
def mock_sparc_reasoner():
    """Create a mock SPARC (Situation, Problem, Action, Result, Conclusion) reasoner."""
    reasoner = Mock()

    # Mock SPARC analysis
    reasoner.analyze = Mock(
        return_value={
            "situation": "Current context and state analysis",
            "problem": "Identified problem or challenge",
            "action": "Proposed action or solution",
            "result": "Expected or actual result",
            "conclusion": "Final conclusion and learnings",
        }
    )

    reasoner.aanalyze = AsyncMock(
        return_value={
            "situation": "Async situation analysis",
            "problem": "Async problem identification",
            "action": "Async action proposal",
            "result": "Async result prediction",
            "conclusion": "Async conclusion",
        }
    )

    return reasoner


@pytest.fixture
def mock_langgraph_state():
    """
    Create a mock LangGraph state for workflow testing (2025 pattern).
    Supports state management and checkpointing.
    """
    from collections.abc import Sequence
    from typing import TypedDict

    class GraphState(TypedDict):
        messages: Sequence[str]
        next: str
        metadata: dict

    state = {"messages": [], "next": "start", "metadata": {}}

    return state


@pytest.fixture
def mock_langgraph_workflow():
    """
    Create a mock LangGraph workflow for testing (2025 pattern).
    Includes node mocking and routing logic testing.
    """
    workflow = Mock()
    workflow.nodes = {}
    workflow.edges = {}
    workflow.conditional_edges = {}
    workflow.checkpointer = None

    # Mock add_node method
    def add_node(name, func):
        workflow.nodes[name] = func

    workflow.add_node = Mock(side_effect=add_node)

    # Mock add_edge method
    def add_edge(from_node, to_node):
        if from_node not in workflow.edges:
            workflow.edges[from_node] = []
        workflow.edges[from_node].append(to_node)

    workflow.add_edge = Mock(side_effect=add_edge)

    # Mock add_conditional_edges
    def add_conditional_edges(from_node, condition_func, edge_map):
        workflow.conditional_edges[from_node] = {"condition": condition_func, "edges": edge_map}

    workflow.add_conditional_edges = Mock(side_effect=add_conditional_edges)

    # Mock compile method
    def compile_workflow(**kwargs):
        compiled = Mock()
        compiled.invoke = AsyncMock(return_value={"final_output": "Success"})
        compiled.stream = AsyncMock()
        compiled.get_graph = Mock(return_value=Mock(nodes=workflow.nodes, edges=workflow.edges))
        return compiled

    workflow.compile = Mock(side_effect=compile_workflow)

    return workflow


@pytest.fixture
def mock_langgraph_checkpointer():
    """
    Create a mock checkpointer for LangGraph state persistence (2025 pattern).
    """
    checkpointer = Mock()
    checkpointer.checkpoint = AsyncMock()
    checkpointer.restore = AsyncMock(return_value={"messages": [], "next": "start"})
    checkpointer.list_checkpoints = AsyncMock(return_value=[])
    checkpointer.delete_checkpoint = AsyncMock()

    return checkpointer


@pytest.fixture
def agent_test_scenarios():
    """Provide common test scenarios for agents."""
    return {
        "simple_task": {
            "input": "What is 2 + 2?",
            "expected_output": "4",
            "agent_type": "calculator",
        },
        "complex_task": {
            "input": "Create a lesson plan for teaching algebra to 9th graders",
            "expected_steps": ["analyze_curriculum", "design_activities", "create_assessments"],
            "agent_type": "content_creator",
        },
        "error_case": {
            "input": "Invalid task that should fail",
            "expected_error": "Task validation failed",
            "agent_type": "any",
        },
        "multi_agent": {
            "input": "Research and summarize recent AI developments",
            "required_agents": ["researcher", "summarizer", "validator"],
            "coordination_type": "sequential",
        },
        "langgraph_workflow": {
            "input": "Execute a multi-step workflow",
            "nodes": ["start", "process", "validate", "end"],
            "expected_flow": ["start", "process", "validate", "end"],
            "checkpoints": True,
        },
    }

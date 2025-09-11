"""
Orchestrator - Main entry point for the multi-agent system

Coordinates all agents to generate complete Roblox educational environments.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json
from enum import Enum
from dataclasses import dataclass

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END

# from langgraph.checkpoint import MemorySaver  # Not available in current version
from langgraph.checkpoint.memory import MemorySaver  # Updated import path

from .base_agent import BaseAgent, AgentConfig, AgentState, TaskResult
from .supervisor import SupervisorAgent
from .content_agent import ContentAgent
from .quiz_agent import QuizAgent
from .terrain_agent import TerrainAgent
from .script_agent import ScriptAgent
from .review_agent import ReviewAgent
from .testing_agent import TestingAgent

logger = logging.getLogger(__name__)


class WorkflowType(Enum):
    """Types of orchestration workflows"""

    FULL_ENVIRONMENT = "full_environment"  # Complete educational environment
    CONTENT_ONLY = "content_only"  # Just educational content
    QUIZ_ONLY = "quiz_only"  # Just quiz generation
    TERRAIN_ONLY = "terrain_only"  # Just terrain generation
    SCRIPT_ONLY = "script_only"  # Just script development
    REVIEW_OPTIMIZE = "review_optimize"  # Review and optimize existing
    TESTING_VALIDATION = "testing_validation"  # Testing and quality validation
    CUSTOM = "custom"  # Custom workflow


@dataclass
class OrchestrationRequest:
    """Request for orchestration"""

    workflow_type: WorkflowType
    subject: str
    grade_level: str
    learning_objectives: List[str]
    environment_theme: Optional[str] = None
    include_quiz: bool = True
    include_gamification: bool = True
    custom_requirements: Optional[Dict[str, Any]] = None


@dataclass
class OrchestrationResult:
    """Result from orchestration"""

    success: bool
    content: Optional[Dict[str, Any]] = None
    scripts: Optional[Dict[str, str]] = None
    terrain: Optional[Dict[str, Any]] = None
    quiz: Optional[Dict[str, Any]] = None
    review: Optional[Dict[str, Any]] = None
    testing: Optional[Dict[str, Any]] = None
    errors: List[str] = None
    execution_time: float = 0.0
    workflow_path: List[str] = None


class Orchestrator:
    """
    Main orchestrator for the multi-agent system.

    Responsibilities:
    - Workflow management
    - Agent coordination
    - State management
    - Error recovery
    - Result aggregation
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

        # Initialize supervisor
        self.supervisor = SupervisorAgent()

        # Initialize specialized agents
        self.agents = {
            "content": ContentAgent(),
            "quiz": QuizAgent(),
            "terrain": TerrainAgent(),
            "script": ScriptAgent(),
            "review": ReviewAgent(),
            "testing": TestingAgent(),
        }

        # State management - Initialize before workflows
        self.memory = MemorySaver()

        # Workflow definitions - After memory initialization
        self.workflows = self._define_workflows()
        self.current_state = None

        # Metrics
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_execution_time": 0.0,
        }

        logger.info("Orchestrator initialized with all agents")

    def _define_workflows(self) -> Dict[WorkflowType, StateGraph]:
        """Define orchestration workflows"""
        workflows = {}

        # Full environment workflow
        full_workflow = StateGraph(AgentState)
        full_workflow.add_node("analyze", self._analyze_request)
        full_workflow.add_node("generate_content", self._generate_content)
        full_workflow.add_node("create_quiz", self._create_quiz)
        full_workflow.add_node("build_terrain", self._build_terrain)
        full_workflow.add_node("develop_scripts", self._develop_scripts)
        full_workflow.add_node("review_code", self._review_code)
        full_workflow.add_node("run_tests", self._run_tests)
        full_workflow.add_node("integrate", self._integrate_components)
        full_workflow.add_node("finalize", self._finalize_environment)

        # Define flow
        full_workflow.set_entry_point("analyze")
        full_workflow.add_edge("analyze", "generate_content")
        full_workflow.add_edge("generate_content", "create_quiz")
        full_workflow.add_edge("create_quiz", "build_terrain")
        full_workflow.add_edge("build_terrain", "develop_scripts")
        full_workflow.add_edge("develop_scripts", "review_code")
        full_workflow.add_edge("review_code", "run_tests")
        full_workflow.add_edge("run_tests", "integrate")
        full_workflow.add_edge("integrate", "finalize")
        full_workflow.add_edge("finalize", END)

        workflows[WorkflowType.FULL_ENVIRONMENT] = full_workflow.compile(
            checkpointer=self.memory
        )

        # Content-only workflow
        content_workflow = StateGraph(AgentState)
        content_workflow.add_node("analyze", self._analyze_request)
        content_workflow.add_node("generate_content", self._generate_content)
        content_workflow.add_node("finalize", self._finalize_environment)

        content_workflow.set_entry_point("analyze")
        content_workflow.add_edge("analyze", "generate_content")
        content_workflow.add_edge("generate_content", "finalize")
        content_workflow.add_edge("finalize", END)

        workflows[WorkflowType.CONTENT_ONLY] = content_workflow.compile(
            checkpointer=self.memory
        )

        # Quiz-only workflow
        quiz_workflow = StateGraph(AgentState)
        quiz_workflow.add_node("analyze", self._analyze_request)
        quiz_workflow.add_node("create_quiz", self._create_quiz)
        quiz_workflow.add_node("develop_scripts", self._develop_quiz_scripts)
        quiz_workflow.add_node("finalize", self._finalize_environment)

        quiz_workflow.set_entry_point("analyze")
        quiz_workflow.add_edge("analyze", "create_quiz")
        quiz_workflow.add_edge("create_quiz", "develop_scripts")
        quiz_workflow.add_edge("develop_scripts", "finalize")
        quiz_workflow.add_edge("finalize", END)

        workflows[WorkflowType.QUIZ_ONLY] = quiz_workflow.compile(
            checkpointer=self.memory
        )

        # Review workflow
        review_workflow = StateGraph(AgentState)
        review_workflow.add_node("analyze", self._analyze_request)
        review_workflow.add_node("review_code", self._review_existing_code)
        review_workflow.add_node("optimize", self._optimize_code)
        review_workflow.add_node("finalize", self._finalize_environment)

        review_workflow.set_entry_point("analyze")
        review_workflow.add_edge("analyze", "review_code")
        review_workflow.add_edge("review_code", "optimize")
        review_workflow.add_edge("optimize", "finalize")
        review_workflow.add_edge("finalize", END)

        workflows[WorkflowType.REVIEW_OPTIMIZE] = review_workflow.compile(
            checkpointer=self.memory
        )

        # Testing validation workflow
        testing_workflow = StateGraph(AgentState)
        testing_workflow.add_node("analyze", self._analyze_request)
        testing_workflow.add_node("run_tests", self._run_tests)
        testing_workflow.add_node("generate_coverage", self._generate_coverage_report)
        testing_workflow.add_node("analyze_failures", self._analyze_test_failures)
        testing_workflow.add_node("finalize", self._finalize_environment)

        testing_workflow.set_entry_point("analyze")
        testing_workflow.add_edge("analyze", "run_tests")
        testing_workflow.add_edge("run_tests", "generate_coverage")
        testing_workflow.add_edge("generate_coverage", "analyze_failures")
        testing_workflow.add_edge("analyze_failures", "finalize")
        testing_workflow.add_edge("finalize", END)

        workflows[WorkflowType.TESTING_VALIDATION] = testing_workflow.compile(
            checkpointer=self.memory
        )

        return workflows

    async def orchestrate(self, request: OrchestrationRequest) -> OrchestrationResult:
        """
        Main orchestration entry point.

        Args:
            request: Orchestration request with requirements

        Returns:
            Complete orchestration result
        """
        start_time = datetime.now()
        self.metrics["total_requests"] += 1

        try:
            logger.info(f"Starting orchestration: {request.workflow_type.value}")

            # Prepare initial state
            initial_state = self._prepare_initial_state(request)

            # Select workflow
            workflow = self.workflows.get(
                request.workflow_type, self.workflows[WorkflowType.FULL_ENVIRONMENT]
            )

            # Execute workflow
            config = {
                "configurable": {"thread_id": f"thread_{datetime.now().timestamp()}"}
            }
            final_state = await workflow.ainvoke(initial_state, config)

            # Extract results
            result = self._extract_results(final_state)

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            result.execution_time = execution_time

            # Update metrics
            self.metrics["successful_requests"] += 1
            self._update_average_execution_time(execution_time)

            logger.info(f"Orchestration completed in {execution_time:.2f}s")

            return result

        except (ValueError, TypeError, KeyError, AttributeError, RuntimeError) as e:
            logger.error(f"Orchestration failed: {e}")
            self.metrics["failed_requests"] += 1

            return OrchestrationResult(
                success=False,
                errors=[str(e)],
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

    def _prepare_initial_state(self, request: OrchestrationRequest) -> AgentState:
        """Prepare initial state from request"""

        task_description = f"""Create a Roblox educational environment:
        Subject: {request.subject}
        Grade Level: {request.grade_level}
        Learning Objectives: {', '.join(request.learning_objectives)}
        Theme: {request.environment_theme or 'classroom'}
        Include Quiz: {request.include_quiz}
        Include Gamification: {request.include_gamification}"""

        return AgentState(
            messages=[HumanMessage(content=task_description)],
            task=task_description,
            context={
                "subject": request.subject,
                "grade_level": request.grade_level,
                "learning_objectives": request.learning_objectives,
                "environment_theme": request.environment_theme,
                "include_quiz": request.include_quiz,
                "include_gamification": request.include_gamification,
                "custom_requirements": request.custom_requirements or {},
                "workflow_type": request.workflow_type.value,
            },
            metadata={
                "orchestrator_version": "1.0.0",
                "request_id": f"req_{datetime.now().timestamp()}",
                "workflow_path": [],
            },
            status="processing",
            result=None,
            error=None,
            timestamp=datetime.now().isoformat(),
            iterations=0,
            max_iterations=20,
        )

    async def _analyze_request(self, state: AgentState) -> AgentState:
        """Analyze the orchestration request"""
        state["metadata"]["workflow_path"].append("analyze")

        # Use supervisor to analyze
        analysis_result = await self.supervisor.execute(
            "Analyze this educational content request and determine requirements",
            state["context"],
        )

        if analysis_result.success:
            state["metadata"]["analysis"] = analysis_result.output
            state["messages"].append(
                AIMessage(content=f"Analysis complete: {analysis_result.output}")
            )
        else:
            state["error"] = f"Analysis failed: {analysis_result.error}"

        return state

    async def _generate_content(self, state: AgentState) -> AgentState:
        """Generate educational content"""
        state["metadata"]["workflow_path"].append("generate_content")

        content_agent = self.agents["content"]
        result = await content_agent.execute(
            "Generate educational content", state["context"]
        )

        if result.success:
            state["metadata"]["content"] = result.output
            state["messages"].append(
                AIMessage(content="Educational content generated successfully")
            )
        else:
            state["error"] = f"Content generation failed: {result.error}"

        return state

    async def _create_quiz(self, state: AgentState) -> AgentState:
        """Create interactive quiz"""
        state["metadata"]["workflow_path"].append("create_quiz")

        if not state["context"].get("include_quiz", True):
            state["messages"].append(AIMessage(content="Quiz generation skipped"))
            return state

        quiz_agent = self.agents["quiz"]

        # Pass content to quiz agent
        quiz_context = state["context"].copy()
        quiz_context["content"] = state["metadata"].get("content", {})

        result = await quiz_agent.execute(
            "Create interactive quiz based on content", quiz_context
        )

        if result.success:
            state["metadata"]["quiz"] = result.output
            state["messages"].append(
                AIMessage(content="Interactive quiz created successfully")
            )
        else:
            state["error"] = f"Quiz creation failed: {result.error}"

        return state

    async def _build_terrain(self, state: AgentState) -> AgentState:
        """Build 3D terrain"""
        state["metadata"]["workflow_path"].append("build_terrain")

        terrain_agent = self.agents["terrain"]

        # Determine terrain theme
        theme = state["context"].get("environment_theme", "classroom")

        terrain_context = {
            "theme": theme,
            "size": "medium",
            "educational_elements": state["metadata"]
            .get("content", {})
            .get("key_concepts", []),
        }

        result = await terrain_agent.execute(
            f"Generate {theme} terrain", terrain_context
        )

        if result.success:
            state["metadata"]["terrain"] = result.output
            state["messages"].append(
                AIMessage(content="Terrain generated successfully")
            )
        else:
            state["error"] = f"Terrain generation failed: {result.error}"

        return state

    async def _develop_scripts(self, state: AgentState) -> AgentState:
        """Develop Lua scripts"""
        state["metadata"]["workflow_path"].append("develop_scripts")

        script_agent = self.agents["script"]

        # Gather all components needing scripts
        scripts_needed = []

        if state["metadata"].get("quiz"):
            scripts_needed.append(
                {"type": "quiz_system", "data": state["metadata"]["quiz"]}
            )

        if state["metadata"].get("terrain"):
            scripts_needed.append(
                {"type": "terrain_interaction", "data": state["metadata"]["terrain"]}
            )

        if state["context"].get("include_gamification"):
            scripts_needed.append(
                {"type": "gamification", "data": {"points": True, "achievements": True}}
            )

        # Generate scripts
        all_scripts = {}

        for script_need in scripts_needed:
            result = await script_agent.execute(
                f"Generate {script_need['type']} scripts",
                {"script_type": script_need["type"], "data": script_need["data"]},
            )

            if result.success:
                all_scripts[script_need["type"]] = result.output

        state["metadata"]["scripts"] = all_scripts
        state["messages"].append(
            AIMessage(content=f"Generated {len(all_scripts)} script systems")
        )

        return state

    async def _develop_quiz_scripts(self, state: AgentState) -> AgentState:
        """Develop quiz-specific scripts"""
        state["metadata"]["workflow_path"].append("develop_quiz_scripts")

        script_agent = self.agents["script"]

        quiz_data = state["metadata"].get("quiz", {})

        result = await script_agent.execute(
            "Generate complete quiz system scripts",
            {"script_type": "quiz_system", "data": quiz_data},
        )

        if result.success:
            state["metadata"]["scripts"] = {"quiz_system": result.output}
            state["messages"].append(
                AIMessage(content="Quiz scripts generated successfully")
            )
        else:
            state["error"] = f"Script generation failed: {result.error}"

        return state

    async def _review_code(self, state: AgentState) -> AgentState:
        """Review generated code"""
        state["metadata"]["workflow_path"].append("review_code")

        review_agent = self.agents["review"]

        # Collect all scripts for review
        scripts = state["metadata"].get("scripts", {})

        review_results = {}

        for script_type, script_data in scripts.items():
            if isinstance(script_data, dict) and "script" in script_data:
                code = script_data["script"]
            else:
                code = str(script_data)

            result = await review_agent.execute(
                f"Review {script_type} code",
                {"code": code, "language": "lua", "review_type": "comprehensive"},
            )

            if result.success:
                review_results[script_type] = result.output

                # Apply refactored code if available
                if result.output.get("refactored_code"):
                    scripts[script_type]["script"] = result.output["refactored_code"]

        state["metadata"]["review"] = review_results
        state["metadata"]["scripts"] = scripts  # Update with refactored versions

        state["messages"].append(
            AIMessage(
                content=f"Code review completed for {len(review_results)} components"
            )
        )

        return state

    async def _review_existing_code(self, state: AgentState) -> AgentState:
        """Review existing code provided in request"""
        state["metadata"]["workflow_path"].append("review_existing_code")

        review_agent = self.agents["review"]

        existing_code = (
            state["context"].get("custom_requirements", {}).get("existing_code", "")
        )

        if not existing_code:
            state["error"] = "No existing code provided for review"
            return state

        result = await review_agent.execute(
            "Review and analyze existing code",
            {"code": existing_code, "language": "lua", "review_type": "comprehensive"},
        )

        if result.success:
            state["metadata"]["review"] = result.output
            state["messages"].append(AIMessage(content="Code review completed"))
        else:
            state["error"] = f"Code review failed: {result.error}"

        return state

    async def _optimize_code(self, state: AgentState) -> AgentState:
        """Optimize code based on review"""
        state["metadata"]["workflow_path"].append("optimize_code")

        review = state["metadata"].get("review", {})

        if review.get("refactored_code"):
            state["metadata"]["optimized_code"] = review["refactored_code"]
            state["messages"].append(
                AIMessage(content="Code optimized based on review findings")
            )
        else:
            state["messages"].append(AIMessage(content="No optimization needed"))

        return state

    async def _integrate_components(self, state: AgentState) -> AgentState:
        """Integrate all components"""
        state["metadata"]["workflow_path"].append("integrate")

        # Create integration manifest
        integration = {
            "components": [],
            "dependencies": [],
            "installation_order": [],
            "configuration": {},
        }

        # Add components
        if state["metadata"].get("content"):
            integration["components"].append("educational_content")
            integration["installation_order"].append("content")

        if state["metadata"].get("quiz"):
            integration["components"].append("quiz_system")
            integration["installation_order"].append("quiz")
            integration["dependencies"].append("ReplicatedStorage")

        if state["metadata"].get("terrain"):
            integration["components"].append("terrain")
            integration["installation_order"].append("terrain")

        if state["metadata"].get("scripts"):
            integration["components"].append("scripts")
            integration["installation_order"].append("scripts")
            integration["dependencies"].append("ServerScriptService")
            integration["dependencies"].append("StarterPlayer")

        # Generate integration instructions
        integration["instructions"] = self._generate_integration_instructions(state)

        state["metadata"]["integration"] = integration
        state["messages"].append(
            AIMessage(content="Components integrated successfully")
        )

        return state

    def _generate_integration_instructions(self, state: AgentState) -> str:
        """Generate step-by-step integration instructions"""

        instructions = ["# Integration Instructions\n"]

        # Content integration
        if state["metadata"].get("content"):
            instructions.append("## 1. Educational Content")
            instructions.append("- Review learning objectives in content documentation")
            instructions.append("- Ensure alignment with curriculum standards\n")

        # Terrain integration
        if state["metadata"].get("terrain"):
            instructions.append("## 2. Terrain Setup")
            instructions.append("- Open Roblox Studio")
            instructions.append("- Run terrain generation script in Command Bar")
            instructions.append("- Adjust terrain properties as needed\n")

        # Script integration
        if state["metadata"].get("scripts"):
            instructions.append("## 3. Script Installation")
            instructions.append("### Server Scripts")
            instructions.append("- Place server scripts in ServerScriptService")
            instructions.append("### Client Scripts")
            instructions.append(
                "- Place client scripts in StarterPlayer > StarterPlayerScripts"
            )
            instructions.append("### Module Scripts")
            instructions.append("- Place modules in ReplicatedStorage\n")

        # Quiz integration
        if state["metadata"].get("quiz"):
            instructions.append("## 4. Quiz System")
            instructions.append("- Create RemoteEvents in ReplicatedStorage")
            instructions.append("- Install quiz UI in StarterGui")
            instructions.append("- Configure quiz settings\n")

        instructions.append("## 5. Testing")
        instructions.append("- Run in Studio Test mode")
        instructions.append("- Verify all features work")
        instructions.append("- Check console for errors")

        return "\n".join(instructions)

    async def _run_tests(self, state: AgentState) -> AgentState:
        """Run comprehensive test suite using TestingAgent"""
        state["metadata"]["workflow_path"].append("run_tests")
        
        try:
            # Get testing context from previous steps
            testing_context = {
                "test_type": "all",
                "triggered_by": "orchestrator",
                "validate_components": True
            }
            
            # Execute tests
            result = await self.agents["testing"].execute("run comprehensive tests", testing_context)
            
            if result.success:
                state["metadata"]["testing"] = result.output
                state["messages"].append(AIMessage(content=f"Testing completed: {result.output}"))
            else:
                state["error"] = f"Testing failed: {result.error}"
                state["messages"].append(AIMessage(content=f"Testing failed: {result.error}"))
            
        except Exception as e:
            logger.error(f"Error running tests: {e}")
            state["error"] = f"Testing error: {str(e)}"
            state["messages"].append(AIMessage(content=f"Testing error: {str(e)}"))
            
        return state

    async def _generate_coverage_report(self, state: AgentState) -> AgentState:
        """Generate code coverage report using TestingAgent"""
        state["metadata"]["workflow_path"].append("generate_coverage")
        
        try:
            # Generate coverage report
            result = await self.agents["testing"].execute("generate coverage report", {})
            
            if result.success:
                coverage_data = result.output
                state["metadata"]["coverage"] = coverage_data
                state["messages"].append(AIMessage(content=f"Coverage report generated: {coverage_data.get('coverage_percentage', 'N/A')}%"))
                
                # Check if coverage meets threshold
                if coverage_data.get('meets_threshold', False):
                    state["messages"].append(AIMessage(content="Code coverage meets quality threshold"))
                else:
                    state["messages"].append(AIMessage(content="Code coverage below threshold - review needed"))
            else:
                state["error"] = f"Coverage generation failed: {result.error}"
                state["messages"].append(AIMessage(content=f"Coverage generation failed: {result.error}"))
                
        except Exception as e:
            logger.error(f"Error generating coverage: {e}")
            state["error"] = f"Coverage error: {str(e)}"
            state["messages"].append(AIMessage(content=f"Coverage error: {str(e)}"))
            
        return state

    async def _analyze_test_failures(self, state: AgentState) -> AgentState:
        """Analyze test failures and provide recommendations using TestingAgent"""
        state["metadata"]["workflow_path"].append("analyze_failures")
        
        try:
            # Analyze any test failures
            result = await self.agents["testing"].execute("analyze test failures", {})
            
            if result.success:
                failure_analysis = result.output
                state["metadata"]["failure_analysis"] = failure_analysis
                
                if failure_analysis.get("recent_failures_count", 0) > 0:
                    state["messages"].append(AIMessage(content=f"Test failures analyzed: {failure_analysis}"))
                else:
                    state["messages"].append(AIMessage(content="No recent test failures to analyze"))
            else:
                # Not critical if failure analysis fails
                state["messages"].append(AIMessage(content=f"Failure analysis unavailable: {result.error}"))
                
        except Exception as e:
            logger.warning(f"Error analyzing test failures: {e}")
            state["messages"].append(AIMessage(content=f"Failure analysis error: {str(e)}"))
            
        return state

    async def _finalize_environment(self, state: AgentState) -> AgentState:
        """Finalize the environment generation"""
        state["metadata"]["workflow_path"].append("finalize")

        # Compile final result
        final_result = {
            "success": state["error"] is None,
            "workflow_path": state["metadata"]["workflow_path"],
            "components": {
                "content": state["metadata"].get("content"),
                "quiz": state["metadata"].get("quiz"),
                "terrain": state["metadata"].get("terrain"),
                "scripts": state["metadata"].get("scripts"),
                "review": state["metadata"].get("review"),
                "testing": state["metadata"].get("testing"),
                "coverage": state["metadata"].get("coverage"),
                "failure_analysis": state["metadata"].get("failure_analysis"),
                "integration": state["metadata"].get("integration"),
            },
            "errors": [state["error"]] if state["error"] else [],
            "messages": [
                msg.content for msg in state["messages"][-5:]
            ],  # Last 5 messages
        }

        state["result"] = final_result
        state["status"] = "completed" if final_result["success"] else "failed"

        return state

    def _extract_results(self, final_state: AgentState) -> OrchestrationResult:
        """Extract results from final state"""

        result_data = final_state.get("result", {}) if final_state.get("result") else {}
        components = result_data.get("components", {}) if result_data.get("components") else {}

        # Combine testing data
        testing_data = {}
        if components.get("testing"):
            testing_data.update(components["testing"])
        if components.get("coverage"):
            testing_data["coverage"] = components["coverage"]
        if components.get("failure_analysis"):
            testing_data["failure_analysis"] = components["failure_analysis"]

        return OrchestrationResult(
            success=result_data.get("success", False),
            content=components.get("content"),
            scripts=components.get("scripts"),
            terrain=components.get("terrain"),
            quiz=components.get("quiz"),
            review=components.get("review"),
            testing=testing_data if testing_data else None,
            errors=result_data.get("errors", []),
            workflow_path=result_data.get("workflow_path", []),
        )

    def _update_average_execution_time(self, new_time: float):
        """Update average execution time metric"""
        total_successful = self.metrics["successful_requests"]
        current_avg = self.metrics["average_execution_time"]

        if total_successful == 1:
            self.metrics["average_execution_time"] = new_time
        else:
            self.metrics["average_execution_time"] = (
                current_avg * (total_successful - 1) + new_time
            ) / total_successful

    async def generate_environment(self, **kwargs) -> OrchestrationResult:
        """
        Convenience method to generate a complete environment.

        Args:
            subject: Educational subject
            grade_level: Target grade level
            learning_objectives: List of learning objectives
            environment_theme: Optional theme
            include_quiz: Whether to include quiz
            include_gamification: Whether to include gamification

        Returns:
            Complete environment generation result
        """
        request = OrchestrationRequest(
            workflow_type=WorkflowType.FULL_ENVIRONMENT,
            subject=kwargs.get("subject", "General"),
            grade_level=kwargs.get("grade_level", "5-7"),
            learning_objectives=kwargs.get("learning_objectives", []),
            environment_theme=kwargs.get("environment_theme"),
            include_quiz=kwargs.get("include_quiz", True),
            include_gamification=kwargs.get("include_gamification", True),
            custom_requirements=kwargs.get("custom_requirements"),
        )

        return await self.orchestrate(request)

    async def review_code(
        self, code: str, language: str = "lua"
    ) -> OrchestrationResult:
        """
        Convenience method to review existing code.

        Args:
            code: Code to review
            language: Programming language

        Returns:
            Review result
        """
        request = OrchestrationRequest(
            workflow_type=WorkflowType.REVIEW_OPTIMIZE,
            subject="Code Review",
            grade_level="N/A",
            learning_objectives=[],
            custom_requirements={"existing_code": code, "language": language},
        )

        return await self.orchestrate(request)

    def get_metrics(self) -> Dict[str, Any]:
        """Get orchestrator metrics"""
        return {
            **self.metrics,
            "agent_statuses": {
                name: agent.get_status() for name, agent in self.agents.items()
            },
            "supervisor_status": self.supervisor.get_status(),
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all components"""
        health = {"orchestrator": "healthy", "agents": {}, "workflows": {}}

        # Check agents
        for name, agent in self.agents.items():
            try:
                status = agent.get_status()
                health["agents"][name] = (
                    "healthy" if status["status"] != "error" else "unhealthy"
                )
            except (AttributeError, KeyError, TypeError) as e:
                logger.debug(f"Agent {name} health check failed: {e}")
                health["agents"][name] = "unhealthy"

        # Check workflows
        for workflow_type in WorkflowType:
            health["workflows"][workflow_type.value] = (
                "available" if workflow_type in self.workflows else "unavailable"
            )

        return health

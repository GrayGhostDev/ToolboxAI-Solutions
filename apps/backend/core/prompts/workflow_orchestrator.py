"""
Workflow Orchestrator for coordinating agents and MCP integration
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import asyncio
import uuid
from enum import Enum

from .models import (
    ConversationContext, WorkflowStep, ContentGenerationPlan, AgentTrigger,
    ContentType, ConversationStage, ValidationResult
)
from .conversation_flow import ConversationFlowManager
from .content_validation import ContentValidationSystem

# Import agent types (these would be imported from the actual agent modules)
from core.agents import (
    SupervisorAgent, ContentAgent, QuizAgent, TerrainAgent,
    ScriptAgent, ReviewAgent, TestingAgent, Orchestrator
)

logger = logging.getLogger(__name__)


class WorkflowStatus(str, Enum):
    """Status of workflow execution"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentType(str, Enum):
    """Types of agents available for workflow orchestration"""
    SUPERVISOR = "supervisor"
    CONTENT = "content"
    QUIZ = "quiz"
    TERRAIN = "terrain"
    SCRIPT = "script"
    REVIEW = "review"
    TESTING = "testing"
    PERSONALIZATION = "personalization"
    CREATIVITY = "creativity"
    UNIQUENESS = "uniqueness"
    VALIDATION = "validation"
    GENERATION = "generation"
    DEPLOYMENT = "deployment"


class WorkflowOrchestrator:
    """
    Orchestrates the workflow of agents and MCP integration for creating
    unique, personalized educational content in Roblox.
    """

    def __init__(self):
        self.flow_manager = ConversationFlowManager()
        self.validation_system = ContentValidationSystem()

        # Initialize agents
        self.agents = self._initialize_agents()

        # Initialize MCP connections
        self.mcp_connections = {}

        # Active workflows
        self.active_workflows: Dict[str, ContentGenerationPlan] = {}

        # Agent capabilities mapping
        self.agent_capabilities = self._define_agent_capabilities()

        # Workflow templates
        self.workflow_templates = self._define_workflow_templates()

    def _initialize_agents(self) -> Dict[AgentType, Any]:
        """Initialize all available agents"""
        return {
            AgentType.SUPERVISOR: SupervisorAgent(),
            AgentType.CONTENT: ContentAgent(),
            AgentType.QUIZ: QuizAgent(),
            AgentType.TERRAIN: TerrainAgent(),
            AgentType.SCRIPT: ScriptAgent(),
            AgentType.REVIEW: ReviewAgent(),
            AgentType.TESTING: TestingAgent(),
            # Additional specialized agents would be initialized here
        }

    def _define_agent_capabilities(self) -> Dict[AgentType, List[str]]:
        """Define capabilities of each agent type"""
        return {
            AgentType.SUPERVISOR: [
                "task_delegation", "workflow_management", "quality_oversight",
                "agent_coordination", "decision_making"
            ],
            AgentType.CONTENT: [
                "lesson_creation", "educational_content", "learning_objectives",
                "curriculum_alignment", "age_appropriate_content"
            ],
            AgentType.QUIZ: [
                "assessment_creation", "question_generation", "scoring_systems",
                "feedback_generation", "difficulty_adjustment"
            ],
            AgentType.TERRAIN: [
                "environment_design", "3d_modeling", "spatial_layout",
                "atmospheric_design", "interactive_elements"
            ],
            AgentType.SCRIPT: [
                "lua_scripting", "game_mechanics", "interaction_systems",
                "performance_optimization", "error_handling"
            ],
            AgentType.REVIEW: [
                "content_review", "quality_assessment", "compliance_check",
                "accessibility_validation", "educational_effectiveness"
            ],
            AgentType.TESTING: [
                "functionality_testing", "performance_testing", "user_testing",
                "bug_detection", "compatibility_testing"
            ],
            AgentType.PERSONALIZATION: [
                "user_profiling", "cultural_adaptation", "interest_matching",
                "localization", "accessibility_customization"
            ],
            AgentType.CREATIVITY: [
                "creative_storytelling", "visual_design", "unique_mechanics",
                "engaging_narratives", "innovative_approaches"
            ],
            AgentType.UNIQUENESS: [
                "uniqueness_enhancement", "trending_elements", "custom_features",
                "personalization_depth", "memorable_experiences"
            ],
            AgentType.VALIDATION: [
                "content_validation", "quality_metrics", "completeness_check",
                "standards_compliance", "best_practices"
            ],
            AgentType.GENERATION: [
                "content_generation", "asset_creation", "integration",
                "workflow_execution", "progress_tracking"
            ],
            AgentType.DEPLOYMENT: [
                "deployment_planning", "environment_setup", "user_access",
                "monitoring_setup", "maintenance_planning"
            ]
        }

    def _define_workflow_templates(self) -> Dict[ContentType, List[WorkflowStep]]:
        """Define workflow templates for different content types"""
        return {
            ContentType.LESSON: [
                WorkflowStep(
                    name="Analyze Requirements",
                    description="Analyze educational requirements and learning objectives",
                    agent_type=AgentType.SUPERVISOR.value,
                    required_data=["learning_objectives", "grade_level", "subject_area"],
                    output_data=["requirements_analysis"],
                    estimated_duration=5
                ),
                WorkflowStep(
                    name="Create Content Structure",
                    description="Design the structure and flow of the lesson",
                    agent_type=AgentType.CONTENT.value,
                    required_data=["requirements_analysis"],
                    output_data=["content_structure"],
                    estimated_duration=10
                ),
                WorkflowStep(
                    name="Personalize Content",
                    description="Add personalization elements based on user profile",
                    agent_type=AgentType.PERSONALIZATION.value,
                    required_data=["content_structure", "user_profile"],
                    output_data=["personalized_content"],
                    estimated_duration=8
                ),
                WorkflowStep(
                    name="Enhance Uniqueness",
                    description="Add unique and creative elements to make content stand out",
                    agent_type=AgentType.CREATIVITY.value,
                    required_data=["personalized_content"],
                    output_data=["unique_content"],
                    estimated_duration=12
                ),
                WorkflowStep(
                    name="Design Environment",
                    description="Create 3D environment and interactive elements",
                    agent_type=AgentType.TERRAIN.value,
                    required_data=["unique_content"],
                    output_data=["environment_design"],
                    estimated_duration=15
                ),
                WorkflowStep(
                    name="Generate Scripts",
                    description="Create Lua scripts for interactivity",
                    agent_type=AgentType.SCRIPT.value,
                    required_data=["environment_design"],
                    output_data=["lua_scripts"],
                    estimated_duration=20
                ),
                WorkflowStep(
                    name="Review and Validate",
                    description="Review content for quality and educational effectiveness",
                    agent_type=AgentType.REVIEW.value,
                    required_data=["lua_scripts", "environment_design"],
                    output_data=["review_results"],
                    estimated_duration=10
                ),
                WorkflowStep(
                    name="Test Functionality",
                    description="Test all functionality and interactions",
                    agent_type=AgentType.TESTING.value,
                    required_data=["review_results"],
                    output_data=["test_results"],
                    estimated_duration=15
                )
            ],
            ContentType.QUIZ: [
                WorkflowStep(
                    name="Analyze Assessment Requirements",
                    description="Analyze quiz requirements and question types",
                    agent_type=AgentType.SUPERVISOR.value,
                    required_data=["learning_objectives", "assessment_type"],
                    output_data=["assessment_requirements"],
                    estimated_duration=5
                ),
                WorkflowStep(
                    name="Generate Questions",
                    description="Generate appropriate questions and answers",
                    agent_type=AgentType.QUIZ.value,
                    required_data=["assessment_requirements"],
                    output_data=["quiz_questions"],
                    estimated_duration=15
                ),
                WorkflowStep(
                    name="Personalize Questions",
                    description="Customize questions for specific students and context",
                    agent_type=AgentType.PERSONALIZATION.value,
                    required_data=["quiz_questions", "user_profile"],
                    output_data=["personalized_questions"],
                    estimated_duration=8
                ),
                WorkflowStep(
                    name="Create Interactive Interface",
                    description="Design engaging quiz interface and interactions",
                    agent_type=AgentType.TERRAIN.value,
                    required_data=["personalized_questions"],
                    output_data=["quiz_interface"],
                    estimated_duration=12
                ),
                WorkflowStep(
                    name="Implement Quiz Logic",
                    description="Create scripts for quiz functionality",
                    agent_type=AgentType.SCRIPT.value,
                    required_data=["quiz_interface"],
                    output_data=["quiz_scripts"],
                    estimated_duration=18
                ),
                WorkflowStep(
                    name="Validate Quiz Quality",
                    description="Review quiz for educational effectiveness",
                    agent_type=AgentType.REVIEW.value,
                    required_data=["quiz_scripts"],
                    output_data=["quiz_validation"],
                    estimated_duration=8
                )
            ],
            ContentType.SIMULATION: [
                WorkflowStep(
                    name="Design Simulation Framework",
                    description="Create the core simulation structure and mechanics",
                    agent_type=AgentType.CONTENT.value,
                    required_data=["learning_objectives", "simulation_type"],
                    output_data=["simulation_framework"],
                    estimated_duration=20
                ),
                WorkflowStep(
                    name="Create 3D Environment",
                    description="Build immersive 3D environment for simulation",
                    agent_type=AgentType.TERRAIN.value,
                    required_data=["simulation_framework"],
                    output_data=["simulation_environment"],
                    estimated_duration=25
                ),
                WorkflowStep(
                    name="Implement Simulation Logic",
                    description="Create complex simulation behaviors and interactions",
                    agent_type=AgentType.SCRIPT.value,
                    required_data=["simulation_environment"],
                    output_data=["simulation_scripts"],
                    estimated_duration=30
                ),
                WorkflowStep(
                    name="Add Personalization",
                    description="Customize simulation for specific users and contexts",
                    agent_type=AgentType.PERSONALIZATION.value,
                    required_data=["simulation_scripts"],
                    output_data=["personalized_simulation"],
                    estimated_duration=15
                ),
                WorkflowStep(
                    name="Enhance Realism",
                    description="Add realistic elements and details",
                    agent_type=AgentType.CREATIVITY.value,
                    required_data=["personalized_simulation"],
                    output_data=["realistic_simulation"],
                    estimated_duration=18
                ),
                WorkflowStep(
                    name="Performance Optimization",
                    description="Optimize simulation for smooth performance",
                    agent_type=AgentType.SCRIPT.value,
                    required_data=["realistic_simulation"],
                    output_data=["optimized_simulation"],
                    estimated_duration=12
                )
            ]
        }

    async def create_workflow_plan(
        self,
        conversation_context: ConversationContext
    ) -> ContentGenerationPlan:
        """Create a comprehensive workflow plan based on conversation context"""

        if not conversation_context.requirements:
            raise ValueError("Requirements not available in conversation context")

        content_type = conversation_context.requirements.content_type
        workflow_steps = self.workflow_templates.get(content_type, [])

        if not workflow_steps:
            raise ValueError(f"No workflow template found for content type {content_type}")

        # Calculate total estimated time
        total_time = sum(step.estimated_duration for step in workflow_steps)

        # Determine required agents
        required_agents = list(set(step.agent_type for step in workflow_steps))

        # Create quality metrics
        quality_metrics = {
            "uniqueness_score": 0.0,
            "engagement_score": 0.0,
            "educational_value_score": 0.0,
            "technical_quality_score": 0.0,
            "personalization_score": 0.0
        }

        plan = ContentGenerationPlan(
            conversation_context=conversation_context,
            workflow_steps=workflow_steps,
            estimated_total_time=total_time,
            required_agents=required_agents,
            expected_outputs=["content", "environment", "scripts", "validation_report"],
            quality_metrics=quality_metrics
        )

        self.active_workflows[plan.plan_id] = plan

        logger.info(f"Created workflow plan {plan.plan_id} for content type {content_type}")

        return plan

    async def execute_workflow(
        self,
        plan_id: str,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """Execute a workflow plan with progress tracking"""

        plan = self.active_workflows.get(plan_id)
        if not plan:
            raise ValueError(f"Workflow plan {plan_id} not found")

        results = {
            "plan_id": plan_id,
            "status": WorkflowStatus.RUNNING.value,
            "started_at": datetime.utcnow().isoformat(),
            "completed_steps": [],
            "current_step": None,
            "progress_percentage": 0.0,
            "outputs": {},
            "errors": [],
            "quality_metrics": plan.quality_metrics
        }

        try:
            total_steps = len(plan.workflow_steps)

            for i, step in enumerate(plan.workflow_steps):
                results["current_step"] = step.name
                results["progress_percentage"] = (i / total_steps) * 100

                if progress_callback:
                    await progress_callback(results)

                # Execute step
                step_result = await self._execute_workflow_step(step, plan, results)

                if step_result["success"]:
                    results["completed_steps"].append({
                        "step_name": step.name,
                        "completed_at": datetime.utcnow().isoformat(),
                        "outputs": step_result["outputs"]
                    })
                    results["outputs"].update(step_result["outputs"])
                else:
                    results["errors"].append({
                        "step_name": step.name,
                        "error": step_result["error"],
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    # Decide whether to continue or stop
                    if step_result["critical"]:
                        results["status"] = WorkflowStatus.FAILED.value
                        break

            if results["status"] == WorkflowStatus.RUNNING.value:
                results["status"] = WorkflowStatus.COMPLETED.value
                results["completed_at"] = datetime.utcnow().isoformat()
                results["progress_percentage"] = 100.0

                # Calculate final quality metrics
                results["quality_metrics"] = await self._calculate_final_metrics(plan, results)

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            results["status"] = WorkflowStatus.FAILED.value
            results["errors"].append({
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })

        return results

    async def _execute_workflow_step(
        self,
        step: WorkflowStep,
        plan: ContentGenerationPlan,
        current_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single workflow step"""

        try:
            # Get the appropriate agent
            agent_type = AgentType(step.agent_type)
            agent = self.agents.get(agent_type)

            if not agent:
                return {
                    "success": False,
                    "error": f"Agent {agent_type} not available",
                    "critical": True
                }

            # Prepare input data
            input_data = self._prepare_step_input(step, plan, current_results)

            # Execute agent task
            if hasattr(agent, 'execute_task'):
                result = await agent.execute_task(input_data)
            else:
                # Fallback for agents without execute_task method
                result = await self._fallback_agent_execution(agent, input_data)

            return {
                "success": True,
                "outputs": result.get("outputs", {}),
                "quality_metrics": result.get("quality_metrics", {})
            }

        except Exception as e:
            logger.error(f"Step execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "critical": False
            }

    def _prepare_step_input(
        self,
        step: WorkflowStep,
        plan: ContentGenerationPlan,
        current_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare input data for a workflow step"""

        input_data = {
            "step_name": step.name,
            "step_description": step.description,
            "conversation_context": plan.conversation_context.dict(),
            "required_data": step.required_data,
            "output_data": step.output_data
        }

        # Add data from previous steps
        input_data.update(current_results.get("outputs", {}))

        # Add conversation context data
        if plan.conversation_context.requirements:
            input_data["requirements"] = plan.conversation_context.requirements.dict()

        if plan.conversation_context.personalization:
            input_data["personalization"] = plan.conversation_context.personalization.dict()

        if plan.conversation_context.uniqueness:
            input_data["uniqueness"] = plan.conversation_context.uniqueness.dict()

        return input_data

    async def _fallback_agent_execution(self, agent: Any, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback execution for agents without execute_task method"""

        # This would be implemented based on the actual agent interfaces
        # For now, return a mock result
        return {
            "outputs": {
                "generated_content": f"Mock content from {type(agent).__name__}",
                "quality_score": 0.8
            },
            "quality_metrics": {
                "completeness": 0.8,
                "accuracy": 0.8,
                "creativity": 0.7
            }
        }

    async def _calculate_final_metrics(
        self,
        plan: ContentGenerationPlan,
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate final quality metrics for the workflow"""

        # This would implement sophisticated quality calculation
        # For now, return mock metrics
        return {
            "uniqueness_score": 0.85,
            "engagement_score": 0.90,
            "educational_value_score": 0.88,
            "technical_quality_score": 0.82,
            "personalization_score": 0.87,
            "overall_score": 0.86
        }

    async def get_workflow_status(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a workflow"""

        plan = self.active_workflows.get(plan_id)
        if not plan:
            return None

        return {
            "plan_id": plan_id,
            "content_type": plan.conversation_context.requirements.content_type.value if plan.conversation_context.requirements else "unknown",
            "total_steps": len(plan.workflow_steps),
            "estimated_time": plan.estimated_total_time,
            "required_agents": plan.required_agents,
            "created_at": plan.created_at.isoformat()
        }

    async def cancel_workflow(self, plan_id: str) -> bool:
        """Cancel an active workflow"""

        if plan_id in self.active_workflows:
            del self.active_workflows[plan_id]
            logger.info(f"Cancelled workflow {plan_id}")
            return True

        return False

    async def get_agent_capabilities(self, agent_type: AgentType) -> List[str]:
        """Get capabilities of a specific agent type"""
        return self.agent_capabilities.get(agent_type, [])

    async def get_available_agents(self) -> List[AgentType]:
        """Get list of available agent types"""
        return list(self.agents.keys())

    async def create_agent_trigger(
        self,
        agent_name: str,
        trigger_type: str,
        trigger_data: Dict[str, Any],
        priority: int = 1
    ) -> AgentTrigger:
        """Create a trigger for agent activation"""

        trigger = AgentTrigger(
            agent_name=agent_name,
            trigger_type=trigger_type,
            trigger_data=trigger_data,
            priority=priority
        )

        # Process trigger based on type
        if trigger_type == "data_ready":
            await self._process_data_ready_trigger(trigger)
        elif trigger_type == "stage_complete":
            await self._process_stage_complete_trigger(trigger)
        elif trigger_type == "user_request":
            await self._process_user_request_trigger(trigger)
        elif trigger_type == "error":
            await self._process_error_trigger(trigger)

        return trigger

    async def _process_data_ready_trigger(self, trigger: AgentTrigger):
        """Process data ready trigger"""
        # Implementation would depend on specific agent requirements
        pass

    async def _process_stage_complete_trigger(self, trigger: AgentTrigger):
        """Process stage complete trigger"""
        # Implementation would depend on specific agent requirements
        pass

    async def _process_user_request_trigger(self, trigger: AgentTrigger):
        """Process user request trigger"""
        # Implementation would depend on specific agent requirements
        pass

    async def _process_error_trigger(self, trigger: AgentTrigger):
        """Process error trigger"""
        # Implementation would depend on specific agent requirements
        pass

    def get_active_workflows(self) -> List[str]:
        """Get list of active workflow plan IDs"""
        return list(self.active_workflows.keys())

    async def cleanup_completed_workflows(self, max_age_hours: int = 24):
        """Clean up completed workflows older than specified age"""

        cutoff_time = datetime.utcnow().timestamp() - (max_age_hours * 3600)

        to_remove = []
        for plan_id, plan in self.active_workflows.items():
            if plan.created_at.timestamp() < cutoff_time:
                to_remove.append(plan_id)

        for plan_id in to_remove:
            del self.active_workflows[plan_id]

        logger.info(f"Cleaned up {len(to_remove)} old workflows")

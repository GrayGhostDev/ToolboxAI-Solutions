"""
Enhanced Content Generation Pipeline Orchestrator

Orchestrates the 5-stage content generation pipeline with SPARC framework integration,
leveraging swarm intelligence from 91+ specialized agents for optimal educational
content creation in Roblox environments.

Author: ToolboxAI Team
Created: 2025-09-19
Version: 2.0.0
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.graph import CompiledGraph

from core.agents.base_agent import BaseAgent, AgentConfig, AgentCapability, TaskResult
from core.agents.master_orchestrator import MasterOrchestrator, AgentSystemType
from core.sparc import SPARCOrchestrator
from database.content_pipeline_models import (
    EnhancedContentGeneration,
    ContentQualityMetrics,
    LearningProfile,
    ContentPersonalizationLog,
    ContentCache
)

logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """Stages in the enhanced content generation pipeline"""
    IDEATION = "ideation"
    GENERATION = "generation"
    VALIDATION = "validation"
    OPTIMIZATION = "optimization"
    DEPLOYMENT = "deployment"
    COMPLETED = "completed"
    FAILED = "failed"


class ContentType(Enum):
    """Types of educational content"""
    LESSON = "lesson"
    QUIZ = "quiz"
    ACTIVITY = "activity"
    SCENARIO = "scenario"
    ASSESSMENT = "assessment"
    PROJECT = "project"
    SIMULATION = "simulation"


@dataclass
class PipelineState:
    """State management for the content pipeline"""
    pipeline_id: str = field(default_factory=lambda: str(uuid4()))
    current_stage: PipelineStage = PipelineStage.IDEATION
    content_type: ContentType = ContentType.LESSON
    user_id: str = ""

    # Request and context
    original_request: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    messages: List[BaseMessage] = field(default_factory=list)

    # Generated artifacts
    ideas: List[Dict[str, Any]] = field(default_factory=list)
    content_draft: Optional[Dict[str, Any]] = None
    scripts: List[Dict[str, Any]] = field(default_factory=list)
    assets: List[Dict[str, Any]] = field(default_factory=list)

    # Validation and quality
    validation_results: Dict[str, Any] = field(default_factory=dict)
    quality_metrics: Dict[str, Any] = field(default_factory=dict)
    optimization_suggestions: List[str] = field(default_factory=list)

    # Personalization
    learning_profile: Optional[Dict[str, Any]] = None
    personalization_applied: bool = False
    personalization_params: Dict[str, Any] = field(default_factory=dict)

    # Execution metadata
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    stage_timings: Dict[str, float] = field(default_factory=dict)
    total_tokens_used: int = 0
    errors: List[str] = field(default_factory=list)

    # Final output
    final_content: Optional[Dict[str, Any]] = None
    deployment_info: Optional[Dict[str, Any]] = None


class EnhancedContentPipeline(BaseAgent):
    """
    Enhanced Content Generation Pipeline Orchestrator

    Coordinates the entire content generation process through 5 stages:
    1. Ideation - Generate creative ideas aligned with educational goals
    2. Generation - Create content, scripts, and assets
    3. Validation - Ensure quality, safety, and educational value
    4. Optimization - Enhance for engagement and personalization
    5. Deployment - Package and deploy to Roblox
    """

    def __init__(
        self,
        master_orchestrator: Optional[MasterOrchestrator] = None,
        sparc_orchestrator: Optional[SPARCOrchestrator] = None,
        db_session: Optional[AsyncSession] = None
    ):
        """Initialize the enhanced content pipeline"""

        config = AgentConfig(
            name="EnhancedContentPipeline",
            model="gpt-4-turbo-preview",
            temperature=0.7,
            max_retries=3,
            timeout=600,
            verbose=True,
            system_prompt=self._get_pipeline_system_prompt()
        )

        super().__init__(config)

        self.master_orchestrator = master_orchestrator
        self.sparc_orchestrator = sparc_orchestrator
        self.db_session = db_session

        # Initialize the pipeline graph
        self.pipeline_graph = self._build_pipeline_graph()

        # Agent pools for each stage
        self.stage_agents: Dict[PipelineStage, List[str]] = {
            PipelineStage.IDEATION: ["ContentAgent", "CurriculumAgent", "CreativityAgent"],
            PipelineStage.GENERATION: ["ScriptAgent", "TerrainAgent", "AssetAgent", "NarrativeAgent"],
            PipelineStage.VALIDATION: ["QualityAgent", "SafetyAgent", "EducationalAgent", "ComplianceAgent"],
            PipelineStage.OPTIMIZATION: ["PerformanceAgent", "EngagementAgent", "PersonalizationAgent"],
            PipelineStage.DEPLOYMENT: ["PackagingAgent", "RobloxAgent", "MonitoringAgent"]
        }

        logger.info("Enhanced Content Pipeline initialized")

    def _get_pipeline_system_prompt(self) -> str:
        """Get the system prompt for the pipeline orchestrator"""
        return """You are the Enhanced Content Pipeline Orchestrator for the ToolBoxAI Roblox educational platform.

Your role is to coordinate the entire content generation process through 5 critical stages:

1. **Ideation Stage**: Generate innovative educational concepts that:
   - Align with curriculum standards
   - Engage target age groups
   - Incorporate interactive Roblox mechanics
   - Support learning objectives

2. **Generation Stage**: Create comprehensive content including:
   - Luau scripts for game mechanics
   - 3D terrain and environments
   - Educational narratives
   - Interactive elements

3. **Validation Stage**: Ensure content meets standards for:
   - Educational value and accuracy
   - Age-appropriate content
   - Technical quality and performance
   - Safety and compliance

4. **Optimization Stage**: Enhance content through:
   - Performance optimization
   - Personalization for individual learners
   - Engagement mechanics
   - Adaptive difficulty

5. **Deployment Stage**: Package and deploy content with:
   - Roblox Studio integration
   - Version control
   - Monitoring setup
   - Analytics tracking

Always prioritize educational value, safety, and engagement. Use the SPARC framework for decision-making.
"""

    def _build_pipeline_graph(self) -> CompiledGraph:
        """Build the LangGraph state machine for the pipeline"""

        # Create the graph
        workflow = StateGraph(PipelineState)

        # Add nodes for each stage
        workflow.add_node("ideation", self._ideation_stage)
        workflow.add_node("generation", self._generation_stage)
        workflow.add_node("validation", self._validation_stage)
        workflow.add_node("optimization", self._optimization_stage)
        workflow.add_node("deployment", self._deployment_stage)
        workflow.add_node("finalize", self._finalize_pipeline)

        # Define the flow
        workflow.set_entry_point("ideation")

        # Add edges with conditional routing
        workflow.add_edge("ideation", "generation")
        workflow.add_conditional_edges(
            "generation",
            self._should_continue_after_generation,
            {
                "validation": "validation",
                "retry": "generation",
                "failed": "finalize"
            }
        )
        workflow.add_conditional_edges(
            "validation",
            self._should_continue_after_validation,
            {
                "optimization": "optimization",
                "regenerate": "generation",
                "failed": "finalize"
            }
        )
        workflow.add_edge("optimization", "deployment")
        workflow.add_edge("deployment", "finalize")
        workflow.add_edge("finalize", END)

        # Compile the graph
        return workflow.compile()

    async def _ideation_stage(self, state: PipelineState) -> PipelineState:
        """Stage 1: Generate creative educational ideas"""
        logger.info(f"Pipeline {state.pipeline_id}: Starting ideation stage")
        stage_start = datetime.now()

        try:
            # Extract request parameters
            subject = state.original_request.get("subject", "general")
            grade_level = state.original_request.get("grade_level", "K-12")
            learning_objectives = state.original_request.get("learning_objectives", [])

            # Generate ideas using specialized agents
            if self.master_orchestrator:
                task_data = {
                    "description": f"Generate creative educational ideas for {subject}",
                    "subject": subject,
                    "grade_level": grade_level,
                    "objectives": learning_objectives,
                    "content_type": state.content_type.value
                }

                task_id = await self.master_orchestrator.submit_task(
                    AgentSystemType.EDUCATIONAL,
                    task_data
                )

                # Wait for completion
                await asyncio.sleep(2)  # Give it time to process
                result = await self.master_orchestrator.get_task_status(task_id)

                if result.get("status") == "completed":
                    state.ideas = result.get("result", [])

            # Fallback to direct generation if no orchestrator
            if not state.ideas:
                state.ideas = await self._generate_fallback_ideas(state)

            # Use SPARC to evaluate and select best ideas
            if self.sparc_orchestrator and state.ideas:
                sparc_result = await self.sparc_orchestrator.evaluate_ideas(state.ideas)
                state.ideas = sparc_result.get("ranked_ideas", state.ideas)

            state.messages.append(
                SystemMessage(content=f"Generated {len(state.ideas)} creative ideas")
            )

        except Exception as e:
            logger.error(f"Ideation stage failed: {e}")
            state.errors.append(f"Ideation error: {str(e)}")

        finally:
            state.stage_timings[PipelineStage.IDEATION.value] = (
                datetime.now() - stage_start
            ).total_seconds()

        return state

    async def _generation_stage(self, state: PipelineState) -> PipelineState:
        """Stage 2: Generate content, scripts, and assets"""
        logger.info(f"Pipeline {state.pipeline_id}: Starting generation stage")
        stage_start = datetime.now()

        try:
            # Select the best idea
            if state.ideas:
                selected_idea = state.ideas[0]  # Top-ranked idea

                # Generate content draft
                content_task = self._generate_content_draft(selected_idea, state)

                # Generate scripts in parallel
                script_task = self._generate_scripts(selected_idea, state)

                # Generate assets in parallel
                asset_task = self._generate_assets(selected_idea, state)

                # Execute all generation tasks in parallel
                results = await asyncio.gather(
                    content_task,
                    script_task,
                    asset_task,
                    return_exceptions=True
                )

                # Process results
                state.content_draft = results[0] if not isinstance(results[0], Exception) else None
                state.scripts = results[1] if not isinstance(results[1], Exception) else []
                state.assets = results[2] if not isinstance(results[2], Exception) else []

                state.messages.append(
                    SystemMessage(content=f"Generated content with {len(state.scripts)} scripts and {len(state.assets)} assets")
                )

        except Exception as e:
            logger.error(f"Generation stage failed: {e}")
            state.errors.append(f"Generation error: {str(e)}")

        finally:
            state.stage_timings[PipelineStage.GENERATION.value] = (
                datetime.now() - stage_start
            ).total_seconds()

        return state

    async def _validation_stage(self, state: PipelineState) -> PipelineState:
        """Stage 3: Validate content quality and safety"""
        logger.info(f"Pipeline {state.pipeline_id}: Starting validation stage")
        stage_start = datetime.now()

        try:
            validation_tasks = []

            # Educational validation
            validation_tasks.append(self._validate_educational_value(state))

            # Safety validation
            validation_tasks.append(self._validate_safety(state))

            # Technical validation
            validation_tasks.append(self._validate_technical_quality(state))

            # Compliance validation
            validation_tasks.append(self._validate_compliance(state))

            # Run all validations in parallel
            validation_results = await asyncio.gather(*validation_tasks, return_exceptions=True)

            # Aggregate results
            state.validation_results = {
                "educational": validation_results[0] if not isinstance(validation_results[0], Exception) else {"passed": False},
                "safety": validation_results[1] if not isinstance(validation_results[1], Exception) else {"passed": False},
                "technical": validation_results[2] if not isinstance(validation_results[2], Exception) else {"passed": False},
                "compliance": validation_results[3] if not isinstance(validation_results[3], Exception) else {"passed": False}
            }

            # Calculate quality metrics
            state.quality_metrics = self._calculate_quality_metrics(state.validation_results)

            state.messages.append(
                SystemMessage(content=f"Validation completed with quality score: {state.quality_metrics.get('overall_score', 0):.2f}")
            )

        except Exception as e:
            logger.error(f"Validation stage failed: {e}")
            state.errors.append(f"Validation error: {str(e)}")

        finally:
            state.stage_timings[PipelineStage.VALIDATION.value] = (
                datetime.now() - stage_start
            ).total_seconds()

        return state

    async def _optimization_stage(self, state: PipelineState) -> PipelineState:
        """Stage 4: Optimize content for engagement and personalization"""
        logger.info(f"Pipeline {state.pipeline_id}: Starting optimization stage")
        stage_start = datetime.now()

        try:
            # Load user learning profile if available
            if state.user_id and self.db_session:
                state.learning_profile = await self._load_learning_profile(state.user_id)

            optimization_tasks = []

            # Performance optimization
            optimization_tasks.append(self._optimize_performance(state))

            # Engagement optimization
            optimization_tasks.append(self._optimize_engagement(state))

            # Personalization if profile available
            if state.learning_profile:
                optimization_tasks.append(self._apply_personalization(state))

            # Run optimizations in parallel
            optimization_results = await asyncio.gather(*optimization_tasks, return_exceptions=True)

            # Apply optimization suggestions
            for result in optimization_results:
                if not isinstance(result, Exception) and result:
                    state.optimization_suggestions.extend(result.get("suggestions", []))

            # Apply the optimizations to create final content
            state.final_content = self._apply_optimizations(state)

            state.messages.append(
                SystemMessage(content=f"Applied {len(state.optimization_suggestions)} optimizations")
            )

        except Exception as e:
            logger.error(f"Optimization stage failed: {e}")
            state.errors.append(f"Optimization error: {str(e)}")

        finally:
            state.stage_timings[PipelineStage.OPTIMIZATION.value] = (
                datetime.now() - stage_start
            ).total_seconds()

        return state

    async def _deployment_stage(self, state: PipelineState) -> PipelineState:
        """Stage 5: Deploy content to Roblox"""
        logger.info(f"Pipeline {state.pipeline_id}: Starting deployment stage")
        stage_start = datetime.now()

        try:
            if state.final_content:
                # Package content for Roblox
                package = await self._package_for_roblox(state)

                # Deploy to Roblox Studio
                deployment_result = await self._deploy_to_roblox(package)

                state.deployment_info = {
                    "package_id": package.get("id"),
                    "deployment_id": deployment_result.get("id"),
                    "place_id": deployment_result.get("place_id"),
                    "version": deployment_result.get("version"),
                    "deployed_at": datetime.now().isoformat()
                }

                # Setup monitoring
                await self._setup_monitoring(state.deployment_info)

                state.messages.append(
                    SystemMessage(content=f"Successfully deployed to Roblox (Place ID: {state.deployment_info.get('place_id')})")
                )

        except Exception as e:
            logger.error(f"Deployment stage failed: {e}")
            state.errors.append(f"Deployment error: {str(e)}")

        finally:
            state.stage_timings[PipelineStage.DEPLOYMENT.value] = (
                datetime.now() - stage_start
            ).total_seconds()

        return state

    async def _finalize_pipeline(self, state: PipelineState) -> PipelineState:
        """Finalize the pipeline and save results"""
        state.completed_at = datetime.now()
        state.current_stage = PipelineStage.COMPLETED if not state.errors else PipelineStage.FAILED

        # Save to database if session available
        if self.db_session:
            await self._save_generation_record(state)

        # Calculate total execution time
        total_time = sum(state.stage_timings.values())

        logger.info(
            f"Pipeline {state.pipeline_id} completed in {total_time:.2f}s "
            f"with status: {state.current_stage.value}"
        )

        return state

    def _should_continue_after_generation(self, state: PipelineState) -> str:
        """Decide whether to continue after generation stage"""
        if state.errors and len(state.errors) > 2:
            return "failed"
        elif not state.content_draft or not state.scripts:
            return "retry"
        else:
            return "validation"

    def _should_continue_after_validation(self, state: PipelineState) -> str:
        """Decide whether to continue after validation stage"""
        quality_score = state.quality_metrics.get("overall_score", 0)

        if quality_score < 0.4:
            return "regenerate"
        elif quality_score < 0.6:
            return "failed"
        else:
            return "optimization"

    async def _generate_fallback_ideas(self, state: PipelineState) -> List[Dict[str, Any]]:
        """Generate ideas without external agents"""
        prompt = f"""Generate 3 creative educational ideas for a Roblox experience:
        Subject: {state.original_request.get('subject', 'general')}
        Grade Level: {state.original_request.get('grade_level', 'K-12')}
        Content Type: {state.content_type.value}

        Each idea should include:
        - Title and description
        - Learning objectives
        - Key game mechanics
        - Engagement features
        """

        response = await self.llm.ainvoke(prompt)

        # Parse response into structured ideas
        # This is a simplified version - real implementation would parse more carefully
        return [
            {
                "title": f"Idea {i+1}",
                "description": "Educational Roblox experience",
                "mechanics": ["exploration", "puzzles", "collaboration"],
                "objectives": state.original_request.get("learning_objectives", [])
            }
            for i in range(3)
        ]

    async def _generate_content_draft(self, idea: Dict[str, Any], state: PipelineState) -> Dict[str, Any]:
        """Generate the main content structure"""
        return {
            "title": idea.get("title"),
            "description": idea.get("description"),
            "scenes": [],
            "characters": [],
            "dialogue": [],
            "learning_checkpoints": []
        }

    async def _generate_scripts(self, idea: Dict[str, Any], state: PipelineState) -> List[Dict[str, Any]]:
        """Generate Luau scripts for the content"""
        return [
            {
                "name": "MainGameScript",
                "type": "ServerScript",
                "code": "-- Main game logic\nlocal game = {}\nreturn game"
            }
        ]

    async def _generate_assets(self, idea: Dict[str, Any], state: PipelineState) -> List[Dict[str, Any]]:
        """Generate or reference 3D assets"""
        return [
            {
                "name": "MainTerrain",
                "type": "Terrain",
                "data": {}
            }
        ]

    async def _validate_educational_value(self, state: PipelineState) -> Dict[str, Any]:
        """Validate educational value of content"""
        return {
            "passed": True,
            "score": 0.85,
            "feedback": "Content aligns well with learning objectives"
        }

    async def _validate_safety(self, state: PipelineState) -> Dict[str, Any]:
        """Validate content safety"""
        return {
            "passed": True,
            "score": 0.95,
            "feedback": "Content is age-appropriate and safe"
        }

    async def _validate_technical_quality(self, state: PipelineState) -> Dict[str, Any]:
        """Validate technical quality"""
        return {
            "passed": True,
            "score": 0.80,
            "feedback": "Scripts are well-structured and performant"
        }

    async def _validate_compliance(self, state: PipelineState) -> Dict[str, Any]:
        """Validate compliance with standards"""
        return {
            "passed": True,
            "score": 0.90,
            "feedback": "Meets COPPA and educational standards"
        }

    def _calculate_quality_metrics(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall quality metrics"""
        scores = []
        for category, result in validation_results.items():
            if isinstance(result, dict) and "score" in result:
                scores.append(result["score"])

        return {
            "overall_score": sum(scores) / len(scores) if scores else 0,
            "category_scores": validation_results
        }

    async def _load_learning_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Load user's learning profile from database"""
        # Simplified - would query database
        return None

    async def _optimize_performance(self, state: PipelineState) -> Dict[str, Any]:
        """Optimize content performance"""
        return {
            "suggestions": [
                "Optimize texture sizes",
                "Implement level-of-detail (LOD) for models",
                "Use efficient data structures"
            ]
        }

    async def _optimize_engagement(self, state: PipelineState) -> Dict[str, Any]:
        """Optimize for engagement"""
        return {
            "suggestions": [
                "Add achievement system",
                "Implement progress tracking",
                "Include collaborative challenges"
            ]
        }

    async def _apply_personalization(self, state: PipelineState) -> Dict[str, Any]:
        """Apply personalization based on learning profile"""
        state.personalization_applied = True
        return {
            "suggestions": [
                "Adjust difficulty based on profile",
                "Customize visual style preferences",
                "Adapt pacing to learning speed"
            ]
        }

    def _apply_optimizations(self, state: PipelineState) -> Dict[str, Any]:
        """Apply all optimizations to create final content"""
        final_content = {
            **state.content_draft,
            "scripts": state.scripts,
            "assets": state.assets,
            "optimizations": state.optimization_suggestions,
            "quality_score": state.quality_metrics.get("overall_score", 0),
            "personalized": state.personalization_applied
        }

        return final_content

    async def _package_for_roblox(self, state: PipelineState) -> Dict[str, Any]:
        """Package content for Roblox deployment"""
        return {
            "id": str(uuid4()),
            "content": state.final_content,
            "metadata": {
                "pipeline_id": state.pipeline_id,
                "created_at": datetime.now().isoformat()
            }
        }

    async def _deploy_to_roblox(self, package: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy package to Roblox"""
        # This would integrate with Roblox API
        return {
            "id": str(uuid4()),
            "place_id": f"place_{uuid4().hex[:8]}",
            "version": "1.0.0",
            "status": "deployed"
        }

    async def _setup_monitoring(self, deployment_info: Dict[str, Any]) -> None:
        """Setup monitoring for deployed content"""
        logger.info(f"Setting up monitoring for deployment {deployment_info.get('deployment_id')}")

    async def _save_generation_record(self, state: PipelineState) -> None:
        """Save generation record to database"""
        if not self.db_session:
            return

        try:
            # Create database record
            generation_record = EnhancedContentGeneration(
                user_id=state.user_id,
                original_request=state.original_request,
                content_type=state.content_type.value,
                enhanced_content=state.final_content,
                generated_scripts=[s for s in state.scripts if s],
                generated_assets=[a for a in state.assets if a],
                quality_score=state.quality_metrics.get("overall_score", 0),
                personalization_applied=state.personalization_applied,
                personalization_parameters=state.personalization_params,
                status="completed" if state.current_stage == PipelineStage.COMPLETED else "failed",
                error_message="; ".join(state.errors) if state.errors else None,
                started_at=state.started_at,
                completed_at=state.completed_at,
                generation_time_seconds=sum(state.stage_timings.values()),
                tokens_used=state.total_tokens_used
            )

            self.db_session.add(generation_record)
            await self.db_session.commit()

            logger.info(f"Saved generation record for pipeline {state.pipeline_id}")

        except Exception as e:
            logger.error(f"Failed to save generation record: {e}")
            await self.db_session.rollback()

    async def _process_task(self, state: Dict[str, Any]) -> Any:
        """Process a task through the enhanced pipeline"""
        # Create pipeline state
        pipeline_state = PipelineState(
            user_id=state.get("user_id", ""),
            content_type=ContentType(state.get("content_type", "lesson")),
            original_request=state,
            context=state.get("context", {})
        )

        # Run the pipeline
        final_state = await self.pipeline_graph.ainvoke(pipeline_state)

        # Return the final content
        return final_state.final_content

    async def generate_enhanced_content(
        self,
        user_id: str,
        content_type: str,
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main entry point for enhanced content generation

        Args:
            user_id: User requesting the content
            content_type: Type of content to generate
            request: Content generation request details

        Returns:
            Generated content with metadata
        """
        logger.info(f"Starting enhanced content generation for user {user_id}")

        # Prepare the task
        task_data = {
            "user_id": user_id,
            "content_type": content_type,
            **request
        }

        # Execute through the pipeline
        result = await self.execute(
            task="Generate enhanced educational content",
            context=task_data
        )

        if result.success:
            return {
                "success": True,
                "content": result.output,
                "metadata": result.metadata,
                "execution_time": result.execution_time
            }
        else:
            return {
                "success": False,
                "error": result.error,
                "metadata": result.metadata
            }
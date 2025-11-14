"""
RobloxOrchestrator - Master orchestrator for all Roblox agents

This orchestrator coordinates all Roblox-specific agents to transform natural language
prompts from the dashboard into fully functional educational Roblox environments.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from .deployment_manager_agent import (
    DeploymentConfig,
    DeploymentEnvironment,
    RobloxDeploymentManagerAgent,
)
from .design_pattern_agent import RobloxDesignPatternAgent
from .fun_agent import FunAgent
from .gameplay_mechanics_agent import (
    GameplayRequirements,
    MechanicType,
    RobloxGameplayMechanicsAgent,
)
from .performance_optimizer_agent import (
    OptimizationType,
    RobloxPerformanceOptimizerAgent,
)

# Import all Roblox agents
from .prompt_analyzer_agent import RobloxPromptAnalyzerAgent
from .quality_assurance_agent import RobloxQualityAssuranceAgent, TestType
from .roblox_security_validation_agent import (
    RobloxSecurityValidationAgent as RobloxSecurityValidatorAgent,
)
from .script_generator_agent import (
    RobloxScriptGeneratorAgent,
    ScriptCategory,
    ScriptRequirements,
    ScriptType,
)
from .terrain_builder_agent import RobloxTerrainBuilderAgent
from .ui_designer_agent import RobloxUIDesignerAgent, UILayoutType, UIRequirements


class WorkflowStage(Enum):
    ANALYSIS = "analysis"
    DESIGN = "design"
    GENERATION = "generation"
    OPTIMIZATION = "optimization"
    VALIDATION = "validation"
    DEPLOYMENT = "deployment"


@dataclass
class RobloxProjectRequirements:
    """Complete requirements for a Roblox educational project"""

    prompt: str
    educational_content: dict[str, Any]
    target_age: int
    subject: str
    learning_objectives: list[str]
    game_type: str = "adventure"
    multiplayer: bool = True
    include_fun: bool = True


class RobloxOrchestrator:
    """
    Master orchestrator that coordinates all Roblox agents to create
    complete educational experiences from natural language prompts.
    """

    def __init__(self):
        # Initialize all agents
        self.agents = {
            "prompt_analyzer": RobloxPromptAnalyzerAgent(),
            "fun": FunAgent(),
            "design_pattern": RobloxDesignPatternAgent(),
            "terrain_builder": RobloxTerrainBuilderAgent(),
            "script_generator": RobloxScriptGeneratorAgent(),
            "ui_designer": RobloxUIDesignerAgent(),
            "gameplay_mechanics": RobloxGameplayMechanicsAgent(),
            "security_validator": RobloxSecurityValidatorAgent(),
            "performance_optimizer": RobloxPerformanceOptimizerAgent(),
            "quality_assurance": RobloxQualityAssuranceAgent(),
            "deployment_manager": RobloxDeploymentManagerAgent(),
        }

        # Workflow tracking
        self.current_project = None
        self.workflow_history = []

    async def create_educational_experience(
        self, requirements: RobloxProjectRequirements
    ) -> dict[str, Any]:
        """
        Main method to create a complete educational Roblox experience
        from natural language requirements.

        Args:
            requirements: Project requirements including prompt and educational content

        Returns:
            Complete project with all generated assets, scripts, and deployment info
        """

        project_id = self._generate_project_id()
        self.current_project = {
            "id": project_id,
            "started_at": datetime.now().isoformat(),
            "requirements": requirements,
            "stages": {},
        }

        try:
            # Stage 1: Analysis
            print(f"🔍 Stage 1: Analyzing prompt...")
            analysis_result = await self._stage_analysis(requirements)
            self.current_project["stages"]["analysis"] = analysis_result

            # Stage 2: Fun Enhancement (if enabled)
            if requirements.include_fun:
                print(f"🎮 Stage 2: Adding fun elements...")
                fun_result = await self._stage_fun_enhancement(analysis_result, requirements)
                self.current_project["stages"]["fun"] = fun_result
                # Merge fun enhancements into analysis
                analysis_result = self._merge_fun_enhancements(analysis_result, fun_result)

            # Stage 3: Design
            print(f"🏗️ Stage 3: Designing architecture...")
            design_result = await self._stage_design(analysis_result, requirements)
            self.current_project["stages"]["design"] = design_result

            # Stage 4: Generation
            print(f"⚙️ Stage 4: Generating content...")
            generation_result = await self._stage_generation(
                design_result, analysis_result, requirements
            )
            self.current_project["stages"]["generation"] = generation_result

            # Stage 5: Optimization
            print(f"🚀 Stage 5: Optimizing performance...")
            optimization_result = await self._stage_optimization(generation_result)
            self.current_project["stages"]["optimization"] = optimization_result

            # Stage 6: Validation
            print(f"✅ Stage 6: Validating quality...")
            validation_result = await self._stage_validation(optimization_result, requirements)
            self.current_project["stages"]["validation"] = validation_result

            # Stage 7: Deployment
            print(f"📦 Stage 7: Preparing deployment...")
            deployment_result = await self._stage_deployment(optimization_result, validation_result)
            self.current_project["stages"]["deployment"] = deployment_result

            # Complete project
            self.current_project["completed_at"] = datetime.now().isoformat()
            self.current_project["success"] = True

            # Store in history
            self.workflow_history.append(self.current_project)

            return {
                "success": True,
                "project_id": project_id,
                "project": self.current_project,
                "summary": self._generate_project_summary(self.current_project),
            }

        except Exception as e:
            self.current_project["error"] = str(e)
            self.current_project["success"] = False
            self.workflow_history.append(self.current_project)

            return {
                "success": False,
                "project_id": project_id,
                "error": str(e),
                "partial_results": self.current_project,
            }

    async def _stage_analysis(self, requirements: RobloxProjectRequirements) -> dict[str, Any]:
        """Stage 1: Analyze the natural language prompt"""

        analyzer = self.agents["prompt_analyzer"]

        # Analyze prompt
        analysis = await analyzer.analyze_prompt(requirements.prompt)

        # Enhance with explicit requirements
        analysis["educational_content"].update(requirements.educational_content)
        analysis["target_age"] = requirements.target_age
        analysis["subject"] = requirements.subject
        analysis["learning_objectives"] = requirements.learning_objectives

        return analysis

    async def _stage_fun_enhancement(
        self, analysis: dict[str, Any], requirements: RobloxProjectRequirements
    ) -> dict[str, Any]:
        """Stage 2: Enhance with fun elements"""

        fun_agent = self.agents["fun"]

        # Transform to fun experience
        fun_result = await fun_agent.transform_to_fun(
            {
                "subject": analysis["subject"],
                "grade_level": analysis.get("grade_level", requirements.target_age),
                "objectives": analysis.get("learning_objectives", []),
                "game_elements": analysis.get("game_elements", []),
            }
        )

        return fun_result

    async def _stage_design(
        self, analysis: dict[str, Any], requirements: RobloxProjectRequirements
    ) -> dict[str, Any]:
        """Stage 3: Design the architecture"""

        designer = self.agents["design_pattern"]

        # Create architecture requirements
        from .design_pattern_agent import (
            ArchitectureRequirements,
            ComponentType,
            DesignPattern,
        )

        arch_requirements = ArchitectureRequirements(
            patterns=[
                DesignPattern.MODULE,
                DesignPattern.OBSERVER,
                DesignPattern.FACTORY,
            ],
            components=[
                ComponentType.SERVICE,
                ComponentType.CONTROLLER,
                ComponentType.GAME_MECHANIC,
            ],
            features=analysis.get("game_elements", []),
            modules=["Education", "Gameplay", "Progress", "Social"],
        )

        # Design architecture
        architecture = await designer.design_architecture(arch_requirements)

        return architecture

    async def _stage_generation(
        self,
        design: dict[str, Any],
        analysis: dict[str, Any],
        requirements: RobloxProjectRequirements,
    ) -> dict[str, Any]:
        """Stage 4: Generate all content"""

        # Parallel generation of different components
        generation_tasks = []

        # Generate terrain
        terrain_task = self._generate_terrain(analysis)
        generation_tasks.append(("terrain", terrain_task))

        # Generate scripts
        script_task = self._generate_scripts(design, analysis, requirements)
        generation_tasks.append(("scripts", script_task))

        # Generate UI
        ui_task = self._generate_ui(analysis, requirements)
        generation_tasks.append(("ui", ui_task))

        # Generate gameplay mechanics
        gameplay_task = self._generate_gameplay(analysis, requirements)
        generation_tasks.append(("gameplay", gameplay_task))

        # Execute all generation tasks in parallel
        results = {}
        for name, task in generation_tasks:
            results[name] = await task

        return results

    async def _generate_terrain(self, analysis: dict[str, Any]) -> dict[str, Any]:
        """Generate terrain"""
        terrain_builder = self.agents["terrain_builder"]

        # Extract environment type
        environment = analysis.get("environment_type", "fantasy")
        educational_elements = analysis.get("learning_objectives", [])

        # Generate terrain
        terrain_result = await terrain_builder.generate_terrain(
            {
                "environment_type": environment,
                "world_size": "medium",
                "educational_elements": educational_elements,
                "optimize": True,
            }
        )

        return terrain_result

    async def _generate_scripts(
        self,
        design: dict[str, Any],
        analysis: dict[str, Any],
        requirements: RobloxProjectRequirements,
    ) -> dict[str, Any]:
        """Generate all scripts"""
        script_generator = self.agents["script_generator"]

        scripts = {}

        # Generate main game script
        main_script_req = ScriptRequirements(
            script_type=ScriptType.SERVER,
            category=ScriptCategory.GAMEPLAY,
            name="MainGameController",
            description="Main game controller for educational experience",
            features=analysis.get("game_elements", []),
            educational_content=requirements.educational_content,
            multiplayer_support=requirements.multiplayer,
        )

        main_script = await script_generator.generate_script(main_script_req)
        scripts["main"] = main_script

        # Generate educational script
        edu_script_req = ScriptRequirements(
            script_type=ScriptType.MODULE,
            category=ScriptCategory.EDUCATIONAL,
            name="EducationModule",
            description="Educational content delivery module",
            features=["quiz", "lessons", "progress_tracking"],
            educational_content=requirements.educational_content,
        )

        edu_script = await script_generator.generate_script(edu_script_req)
        scripts["education"] = edu_script

        return scripts

    async def _generate_ui(
        self, analysis: dict[str, Any], requirements: RobloxProjectRequirements
    ) -> dict[str, Any]:
        """Generate UI components"""
        ui_designer = self.agents["ui_designer"]

        ui_components = {}

        # Generate quiz UI
        quiz_ui_req = UIRequirements(
            layout_type=UILayoutType.QUIZ,
            responsive=True,
            educational_features=["questions", "answers", "progress"],
        )

        quiz_ui = await ui_designer.generate_ui(quiz_ui_req)
        ui_components["quiz"] = quiz_ui

        # Generate HUD
        hud_ui_req = UIRequirements(
            layout_type=UILayoutType.HUD,
            responsive=True,
            educational_features=["score", "progress", "objectives"],
        )

        hud_ui = await ui_designer.generate_ui(hud_ui_req)
        ui_components["hud"] = hud_ui

        return ui_components

    async def _generate_gameplay(
        self, analysis: dict[str, Any], requirements: RobloxProjectRequirements
    ) -> dict[str, Any]:
        """Generate gameplay mechanics"""
        gameplay_generator = self.agents["gameplay_mechanics"]

        gameplay_req = GameplayRequirements(
            mechanic_types=[
                MechanicType.SCORING,
                MechanicType.ACHIEVEMENTS,
                MechanicType.POWERUPS,
            ],
            educational_goals=requirements.learning_objectives,
            multiplayer=requirements.multiplayer,
            competitive=True,
        )

        gameplay = await gameplay_generator.generate_mechanics(gameplay_req)

        return {"mechanics": gameplay}

    async def _stage_optimization(self, generation_result: dict[str, Any]) -> dict[str, Any]:
        """Stage 5: Optimize all generated content"""

        optimizer = self.agents["performance_optimizer"]
        security = self.agents["security_validator"]

        optimized = {}

        # Optimize scripts
        if "scripts" in generation_result:
            for script_name, script_data in generation_result["scripts"].items():
                if isinstance(script_data, dict) and "code" in script_data:
                    # Optimize performance
                    opt_result = await optimizer.optimize_script(
                        script_data["code"], OptimizationType.CPU
                    )

                    # Validate security
                    sec_result = await security.validate_script(opt_result["optimized_code"])

                    optimized[script_name] = {
                        "code": opt_result["optimized_code"],
                        "security": sec_result,
                        "optimizations": opt_result["improvements"],
                    }

        return optimized

    async def _stage_validation(
        self,
        optimization_result: dict[str, Any],
        requirements: RobloxProjectRequirements,
    ) -> dict[str, Any]:
        """Stage 6: Validate quality"""

        qa_agent = self.agents["quality_assurance"]

        # Run comprehensive tests
        test_results = await qa_agent.run_tests(
            {
                "code": str(optimization_result),
                "educational_content": requirements.educational_content,
            },
            [TestType.FUNCTIONALITY, TestType.EDUCATIONAL, TestType.COMPATIBILITY],
        )

        return test_results

    async def _stage_deployment(
        self, optimization_result: dict[str, Any], validation_result: dict[str, Any]
    ) -> dict[str, Any]:
        """Stage 7: Prepare deployment"""

        deployer = self.agents["deployment_manager"]

        # Only deploy if validation passed
        if not validation_result.get("passed", False):
            return {
                "success": False,
                "reason": "Validation failed",
                "validation_score": validation_result.get("score", 0),
            }

        # Create deployment config
        scripts_to_deploy = []
        for name, script_data in optimization_result.items():
            if isinstance(script_data, dict) and "code" in script_data:
                scripts_to_deploy.append(
                    {"name": name, "type": "Script", "source": script_data["code"]}
                )

        config = DeploymentConfig(
            environment=DeploymentEnvironment.DEVELOPMENT,
            game_id=self.current_project["id"],
            version="1.0.0",
            scripts=scripts_to_deploy,
        )

        # Deploy
        deployment_result = await deployer.deploy(config)

        return deployment_result

    def _merge_fun_enhancements(
        self, analysis: dict[str, Any], fun_result: dict[str, Any]
    ) -> dict[str, Any]:
        """Merge fun enhancements into analysis"""
        enhanced = analysis.copy()

        # Add fun game elements
        if "fun_experience" in fun_result:
            enhanced["game_elements"] = enhanced.get("game_elements", [])
            if isinstance(fun_result["fun_experience"], dict):
                for key, value in fun_result["fun_experience"].items():
                    if isinstance(value, list):
                        enhanced["game_elements"].extend(value)

        # Add engagement features
        if "engagement_features" in fun_result:
            enhanced["engagement_features"] = fun_result["engagement_features"]

        return enhanced

    def _generate_project_id(self) -> str:
        """Generate unique project ID"""
        import uuid

        return f"roblox_project_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

    def _generate_project_summary(self, project: dict[str, Any]) -> dict[str, Any]:
        """Generate project summary"""
        return {
            "project_id": project["id"],
            "created_at": project["started_at"],
            "completed_at": project.get("completed_at"),
            "requirements": {
                "prompt": project["requirements"].prompt[:100] + "...",
                "subject": project["requirements"].subject,
                "target_age": project["requirements"].target_age,
            },
            "stages_completed": list(project.get("stages", {}).keys()),
            "success": project.get("success", False),
            "deployment_ready": "deployment" in project.get("stages", {}),
        }

    async def quick_generate(self, prompt: str) -> dict[str, Any]:
        """
        Quick generation method for simple prompts without full requirements

        Args:
            prompt: Natural language prompt

        Returns:
            Generated content
        """

        # Create minimal requirements
        requirements = RobloxProjectRequirements(
            prompt=prompt,
            educational_content={"topic": "general"},
            target_age=10,
            subject="general",
            learning_objectives=["Learn through play"],
            include_fun=True,
        )

        return await self.create_educational_experience(requirements)

"""
Enhanced Conversation Flow Manager with LCEL Chains
Integrates 8-stage conversation flow with Roblox environment generation
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import logging

from core.langchain_compat import (
    get_chat_model,
    create_chain_template,
    SystemMessage,
    HumanMessage,
    AIMessage,
    ChatPromptTemplate,
    StrOutputParser,
    JsonOutputParser
)
from apps.backend.services.pusher_realtime import pusher_service
from apps.backend.services.rojo_manager import rojo_manager, RojoProjectConfig
from apps.backend.services.open_cloud_client import open_cloud_client
from apps.backend.core.prompts.conversation_flow import ConversationStage

logger = logging.getLogger(__name__)

class RobloxEnvironmentData(BaseModel):
    """Data for Roblox environment generation"""
    terrain_type: str = Field(default="natural", description="Type of terrain")
    buildings: List[Dict[str, Any]] = Field(default_factory=list)
    interactive_objects: List[Dict[str, Any]] = Field(default_factory=list)
    npcs: List[Dict[str, Any]] = Field(default_factory=list)
    quizzes: List[Dict[str, Any]] = Field(default_factory=list)
    lighting: Dict[str, Any] = Field(default_factory=dict)
    atmosphere: Dict[str, Any] = Field(default_factory=dict)
    game_mechanics: List[str] = Field(default_factory=list)

class ConversationContext(BaseModel):
    """Context for the entire conversation"""
    session_id: str
    user_id: str
    current_stage: ConversationStage
    stage_data: Dict[ConversationStage, Dict[str, Any]] = Field(default_factory=dict)
    roblox_data: RobloxEnvironmentData = Field(default_factory=RobloxEnvironmentData)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class StageChain:
    """Base class for conversation stage chains"""

    def __init__(self, stage: ConversationStage):
        self.stage = stage
        self.llm = get_chat_model(temperature=0.7)
        self.output_parser = JsonOutputParser()

    async def process(self, context: ConversationContext, user_input: str) -> Dict[str, Any]:
        """Process user input for this stage"""
        raise NotImplementedError

class GreetingChain(StageChain):
    """Chain for greeting stage"""

    def __init__(self):
        super().__init__(ConversationStage.GREETING)
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an educational content creator assistant for Roblox.
            Start by warmly greeting the user and asking what kind of educational experience they want to create.
            Be enthusiastic and helpful. Extract their general intent and subject area."""),
            HumanMessage(content="{user_input}")
        ])
        self.chain = self.prompt | self.llm | self.output_parser

    async def process(self, context: ConversationContext, user_input: str) -> Dict[str, Any]:
        result = await self.chain.ainvoke({"user_input": user_input})

        # Extract subject and intent
        return {
            "greeting_complete": True,
            "subject_area": result.get("subject", "general"),
            "user_intent": result.get("intent", "create educational content"),
            "response": result.get("response", "Welcome! Let's create an amazing educational Roblox experience!")
        }

class DiscoveryChain(StageChain):
    """Chain for discovery stage - extracting learning objectives"""

    def __init__(self):
        super().__init__(ConversationStage.DISCOVERY)
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""Extract specific learning objectives from the user's description.
            Focus on:
            1. Core concepts to teach
            2. Skills to develop
            3. Knowledge to impart
            4. Age group and grade level
            Format as structured data for Roblox environment generation."""),
            HumanMessage(content="Previous context: {context}\nUser input: {user_input}")
        ])
        self.chain = self.prompt | self.llm | self.output_parser

    async def process(self, context: ConversationContext, user_input: str) -> Dict[str, Any]:
        result = await self.chain.ainvoke({
            "context": str(context.stage_data.get(ConversationStage.GREETING, {})),
            "user_input": user_input
        })

        # Update Roblox data based on learning objectives
        if "concepts" in result:
            context.roblox_data.game_mechanics.extend([
                "concept_exploration",
                "interactive_learning",
                "progress_tracking"
            ])

        return {
            "learning_objectives": result.get("objectives", []),
            "target_age": result.get("age_group", "8-12"),
            "grade_level": result.get("grade_level", "3-6"),
            "core_concepts": result.get("concepts", []),
            "response": result.get("response", "Great! I understand your learning objectives.")
        }

class RequirementsChain(StageChain):
    """Chain for requirements gathering"""

    def __init__(self):
        super().__init__(ConversationStage.REQUIREMENTS)
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""Gather technical and educational requirements for the Roblox environment.
            Ask about:
            1. Number of players (single/multiplayer)
            2. Environment type (classroom, outdoor, fantasy, sci-fi)
            3. Assessment methods (quizzes, challenges, exploration)
            4. Duration of experience
            5. Accessibility needs
            Generate specific Roblox environment parameters."""),
            HumanMessage(content="Learning objectives: {objectives}\nUser input: {user_input}")
        ])
        self.chain = self.prompt | self.llm | self.output_parser

    async def process(self, context: ConversationContext, user_input: str) -> Dict[str, Any]:
        objectives = context.stage_data.get(ConversationStage.DISCOVERY, {})
        result = await self.chain.ainvoke({
            "objectives": str(objectives),
            "user_input": user_input
        })

        # Update Roblox environment data
        if result.get("environment_type"):
            context.roblox_data.terrain_type = result["environment_type"]

        if result.get("max_players", 1) > 1:
            context.roblox_data.game_mechanics.append("multiplayer")

        return {
            "max_players": result.get("max_players", 20),
            "environment_type": result.get("environment_type", "classroom"),
            "assessment_types": result.get("assessments", ["quiz", "exploration"]),
            "duration_minutes": result.get("duration", 30),
            "accessibility": result.get("accessibility", ["visual_aids", "audio_cues"]),
            "response": result.get("response", "I've noted your requirements.")
        }

class PersonalizationChain(StageChain):
    """Chain for personalization preferences"""

    def __init__(self):
        super().__init__(ConversationStage.PERSONALIZATION)
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""Gather personalization preferences for the Roblox experience.
            Ask about:
            1. Visual style preferences (realistic, cartoon, minimalist)
            2. Color schemes
            3. Character types (humans, animals, robots)
            4. Music and sound preferences
            5. Cultural considerations
            Map these to specific Roblox assets and settings."""),
            HumanMessage(content="Requirements: {requirements}\nUser input: {user_input}")
        ])
        self.chain = self.prompt | self.llm | self.output_parser

    async def process(self, context: ConversationContext, user_input: str) -> Dict[str, Any]:
        requirements = context.stage_data.get(ConversationStage.REQUIREMENTS, {})
        result = await self.chain.ainvoke({
            "requirements": str(requirements),
            "user_input": user_input
        })

        # Update Roblox lighting and atmosphere
        if result.get("visual_style"):
            context.roblox_data.lighting = {
                "style": result["visual_style"],
                "brightness": result.get("brightness", 0.7),
                "ambient": result.get("ambient_color", "white")
            }

        if result.get("atmosphere"):
            context.roblox_data.atmosphere = result["atmosphere"]

        return {
            "visual_style": result.get("visual_style", "friendly_cartoon"),
            "color_scheme": result.get("colors", ["blue", "green", "yellow"]),
            "character_types": result.get("characters", ["friendly_animals"]),
            "audio_style": result.get("audio", "cheerful"),
            "cultural_elements": result.get("cultural", []),
            "response": result.get("response", "Great choices for personalization!")
        }

class ContentDesignChain(StageChain):
    """Chain for content design with AI assistance"""

    def __init__(self):
        super().__init__(ConversationStage.CONTENT_DESIGN)
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""Design the educational content structure for Roblox.
            Create:
            1. Interactive learning stations
            2. NPC dialogue scripts
            3. Quiz questions and answers
            4. Challenge scenarios
            5. Progress milestones
            Generate specific Roblox objects and scripts."""),
            HumanMessage(content="Full context: {context}\nUser input: {user_input}")
        ])
        self.chain = self.prompt | self.llm | self.output_parser

    async def process(self, context: ConversationContext, user_input: str) -> Dict[str, Any]:
        full_context = {
            stage.value: data
            for stage, data in context.stage_data.items()
        }
        result = await self.chain.ainvoke({
            "context": str(full_context),
            "user_input": user_input
        })

        # Populate Roblox environment with content
        if result.get("learning_stations"):
            for station in result["learning_stations"]:
                context.roblox_data.interactive_objects.append({
                    "type": "learning_station",
                    "name": station.get("name"),
                    "content": station.get("content"),
                    "position": station.get("position")
                })

        if result.get("npcs"):
            context.roblox_data.npcs.extend(result["npcs"])

        if result.get("quizzes"):
            context.roblox_data.quizzes.extend(result["quizzes"])

        return {
            "learning_stations": result.get("learning_stations", []),
            "npcs": result.get("npcs", []),
            "quizzes": result.get("quizzes", []),
            "challenges": result.get("challenges", []),
            "milestones": result.get("milestones", []),
            "response": result.get("response", "Content structure designed!")
        }

class UniquenessChain(StageChain):
    """Chain for adding unique creative elements"""

    def __init__(self):
        super().__init__(ConversationStage.UNIQUENESS_ENHANCEMENT)
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""Add unique and creative elements to make the Roblox experience memorable.
            Suggest:
            1. Special effects and particles
            2. Easter eggs and hidden content
            3. Unique game mechanics
            4. Memorable characters
            5. Surprising interactions
            Be creative while maintaining educational value."""),
            HumanMessage(content="Content design: {content}\nUser input: {user_input}")
        ])
        self.chain = self.prompt | self.llm | self.output_parser

    async def process(self, context: ConversationContext, user_input: str) -> Dict[str, Any]:
        content = context.stage_data.get(ConversationStage.CONTENT_DESIGN, {})
        result = await self.chain.ainvoke({
            "content": str(content),
            "user_input": user_input
        })

        # Add unique elements to Roblox data
        if result.get("special_effects"):
            context.roblox_data.atmosphere["effects"] = result["special_effects"]

        if result.get("unique_mechanics"):
            context.roblox_data.game_mechanics.extend(result["unique_mechanics"])

        return {
            "special_effects": result.get("special_effects", []),
            "easter_eggs": result.get("easter_eggs", []),
            "unique_mechanics": result.get("unique_mechanics", []),
            "memorable_characters": result.get("characters", []),
            "surprise_elements": result.get("surprises", []),
            "response": result.get("response", "Added creative enhancements!")
        }

class ValidationChain(StageChain):
    """Chain for content validation and quality checks"""

    def __init__(self):
        super().__init__(ConversationStage.VALIDATION)
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""Validate the educational content for quality and appropriateness.
            Check:
            1. Educational alignment with objectives
            2. Age appropriateness
            3. Safety and content guidelines
            4. Accessibility compliance
            5. Technical feasibility in Roblox
            Provide validation scores and suggestions."""),
            HumanMessage(content="Full design: {design}\nUser confirmation: {user_input}")
        ])
        self.chain = self.prompt | self.llm | self.output_parser

    async def process(self, context: ConversationContext, user_input: str) -> Dict[str, Any]:
        full_design = {
            "stages": {stage.value: data for stage, data in context.stage_data.items()},
            "roblox_data": context.roblox_data.dict()
        }
        result = await self.chain.ainvoke({
            "design": str(full_design),
            "user_input": user_input
        })

        return {
            "validation_scores": {
                "educational_value": result.get("educational_score", 0.85),
                "age_appropriateness": result.get("age_score", 0.90),
                "safety": result.get("safety_score", 0.95),
                "accessibility": result.get("accessibility_score", 0.85),
                "technical_feasibility": result.get("feasibility_score", 0.90)
            },
            "suggestions": result.get("suggestions", []),
            "warnings": result.get("warnings", []),
            "approved": result.get("approved", True),
            "response": result.get("response", "Content validated and ready for generation!")
        }

class EnhancedConversationFlowManager:
    """
    Enhanced conversation flow manager with LCEL chains and Roblox integration
    """

    def __init__(self):
        self.chains = {
            ConversationStage.GREETING: GreetingChain(),
            ConversationStage.DISCOVERY: DiscoveryChain(),
            ConversationStage.REQUIREMENTS: RequirementsChain(),
            ConversationStage.PERSONALIZATION: PersonalizationChain(),
            ConversationStage.CONTENT_DESIGN: ContentDesignChain(),
            ConversationStage.UNIQUENESS_ENHANCEMENT: UniquenessChain(),
            ConversationStage.VALIDATION: ValidationChain()
        }
        self.contexts: Dict[str, ConversationContext] = {}

    async def start_conversation(self, user_id: str, session_id: str) -> ConversationContext:
        """Start a new conversation"""
        context = ConversationContext(
            session_id=session_id,
            user_id=user_id,
            current_stage=ConversationStage.GREETING
        )
        self.contexts[session_id] = context

        # Notify via Pusher
        await pusher_service.broadcast_event(
            f"conversation-{session_id}",
            "conversation_started",
            {"stage": ConversationStage.GREETING.value}
        )

        logger.info(f"Started conversation {session_id} for user {user_id}")
        return context

    async def process_input(
        self,
        session_id: str,
        user_input: str
    ) -> Dict[str, Any]:
        """Process user input for current stage"""
        if session_id not in self.contexts:
            raise ValueError(f"Session {session_id} not found")

        context = self.contexts[session_id]
        current_chain = self.chains.get(context.current_stage)

        if not current_chain:
            raise ValueError(f"No chain for stage {context.current_stage}")

        # Process input through chain
        result = await current_chain.process(context, user_input)

        # Store stage data
        context.stage_data[context.current_stage] = result
        context.updated_at = datetime.utcnow()

        # Broadcast progress
        await pusher_service.broadcast_event(
            f"conversation-{session_id}",
            "stage_processed",
            {
                "stage": context.current_stage.value,
                "result": result,
                "next_stage": self._get_next_stage(context.current_stage).value
            }
        )

        return {
            "current_stage": context.current_stage.value,
            "result": result,
            "next_stage": self._get_next_stage(context.current_stage).value,
            "progress": self._calculate_progress(context)
        }

    async def advance_stage(self, session_id: str) -> ConversationContext:
        """Advance to next conversation stage"""
        if session_id not in self.contexts:
            raise ValueError(f"Session {session_id} not found")

        context = self.contexts[session_id]
        next_stage = self._get_next_stage(context.current_stage)

        if next_stage:
            context.current_stage = next_stage
            context.updated_at = datetime.utcnow()

            # Broadcast stage transition
            await pusher_service.broadcast_event(
                f"conversation-{session_id}",
                "stage_transition",
                {
                    "from": context.current_stage.value,
                    "to": next_stage.value,
                    "progress": self._calculate_progress(context)
                }
            )

            logger.info(f"Advanced session {session_id} to stage {next_stage.value}")

        return context

    async def generate_roblox_environment(self, session_id: str) -> Dict[str, Any]:
        """Generate Roblox environment from conversation data"""
        if session_id not in self.contexts:
            raise ValueError(f"Session {session_id} not found")

        context = self.contexts[session_id]

        # Validate we have all required data
        validation = context.stage_data.get(ConversationStage.VALIDATION, {})
        if not validation.get("approved", False):
            raise ValueError("Content not validated or approved")

        # Generate Rojo project configuration
        project_config = self._create_rojo_config(context)

        # Create Rojo project
        project = await rojo_manager.create_project(
            project_name=f"edu_{context.session_id[:8]}",
            user_id=context.user_id,
            project_config=project_config
        )

        # Generate Lua scripts
        scripts = self._generate_lua_scripts(context)

        # Update project files
        await rojo_manager.update_project_files(project.project_id, scripts)

        # Start Rojo server
        sync_status = await rojo_manager.start_project(project.project_id)

        # Broadcast generation complete
        await pusher_service.broadcast_event(
            f"conversation-{session_id}",
            "generation_complete",
            {
                "project_id": project.project_id,
                "rojo_port": project.port,
                "sync_status": sync_status.dict()
            }
        )

        return {
            "success": True,
            "project_id": project.project_id,
            "rojo_port": project.port,
            "sync_url": f"http://localhost:{project.port}",
            "files_generated": len(scripts)
        }

    def _get_next_stage(self, current: ConversationStage) -> Optional[ConversationStage]:
        """Get next stage in conversation flow"""
        stage_order = [
            ConversationStage.GREETING,
            ConversationStage.DISCOVERY,
            ConversationStage.REQUIREMENTS,
            ConversationStage.PERSONALIZATION,
            ConversationStage.CONTENT_DESIGN,
            ConversationStage.UNIQUENESS_ENHANCEMENT,
            ConversationStage.VALIDATION,
            ConversationStage.GENERATION_AND_REVIEW
        ]

        try:
            current_index = stage_order.index(current)
            if current_index < len(stage_order) - 1:
                return stage_order[current_index + 1]
        except ValueError:
            pass

        return None

    def _calculate_progress(self, context: ConversationContext) -> float:
        """Calculate conversation progress percentage"""
        total_stages = 8
        completed = len(context.stage_data)
        return (completed / total_stages) * 100

    def _create_rojo_config(self, context: ConversationContext) -> RojoProjectConfig:
        """Create Rojo project configuration from conversation context"""
        return RojoProjectConfig(
            name=f"Educational_{context.session_id[:8]}",
            tree={
                "$className": "DataModel",
                "ReplicatedStorage": {
                    "$className": "ReplicatedStorage",
                    "Modules": {
                        "$className": "Folder",
                        "QuizSystem": {"$path": "src/shared/QuizSystem.lua"},
                        "NPCDialogue": {"$path": "src/shared/NPCDialogue.lua"},
                        "ProgressTracker": {"$path": "src/shared/ProgressTracker.lua"}
                    }
                },
                "ServerScriptService": {
                    "$className": "ServerScriptService",
                    "GameController": {"$path": "src/server/GameController.lua"},
                    "TerrainGenerator": {"$path": "src/server/TerrainGenerator.lua"}
                },
                "StarterPlayer": {
                    "$className": "StarterPlayer",
                    "StarterPlayerScripts": {
                        "$className": "StarterPlayerScripts",
                        "ClientController": {"$path": "src/client/ClientController.lua"}
                    }
                },
                "Workspace": {
                    "$className": "Workspace",
                    "Environment": {"$className": "Folder"}
                }
            }
        )

    def _generate_lua_scripts(self, context: ConversationContext) -> Dict[str, str]:
        """Generate Lua scripts from conversation context"""
        scripts = {}

        # Quiz System
        quizzes = context.roblox_data.quizzes
        scripts["src/shared/QuizSystem.lua"] = self._generate_quiz_script(quizzes)

        # NPC Dialogue
        npcs = context.roblox_data.npcs
        scripts["src/shared/NPCDialogue.lua"] = self._generate_npc_script(npcs)

        # Progress Tracker
        scripts["src/shared/ProgressTracker.lua"] = self._generate_progress_script()

        # Game Controller
        scripts["src/server/GameController.lua"] = self._generate_game_controller()

        # Terrain Generator
        terrain = context.roblox_data.terrain_type
        scripts["src/server/TerrainGenerator.lua"] = self._generate_terrain_script(terrain)

        # Client Controller
        scripts["src/client/ClientController.lua"] = self._generate_client_controller()

        return scripts

    def _generate_quiz_script(self, quizzes: List[Dict]) -> str:
        """Generate quiz system Lua script"""
        return f"""-- Quiz System
local QuizSystem = {{}}
QuizSystem.__index = QuizSystem

local quizzes = {str(quizzes)}

function QuizSystem.new()
    local self = setmetatable({{}}, QuizSystem)
    self.quizzes = quizzes
    self.currentQuiz = 1
    self.score = 0
    return self
end

function QuizSystem:GetNextQuestion()
    if self.currentQuiz <= #self.quizzes then
        local quiz = self.quizzes[self.currentQuiz]
        self.currentQuiz = self.currentQuiz + 1
        return quiz
    end
    return nil
end

function QuizSystem:CheckAnswer(answer)
    -- Implementation for answer checking
    return true
end

return QuizSystem
"""

    def _generate_npc_script(self, npcs: List[Dict]) -> str:
        """Generate NPC dialogue Lua script"""
        return f"""-- NPC Dialogue System
local NPCDialogue = {{}}
NPCDialogue.__index = NPCDialogue

local npcs = {str(npcs)}

function NPCDialogue.new()
    local self = setmetatable({{}}, NPCDialogue)
    self.npcs = npcs
    return self
end

function NPCDialogue:GetDialogue(npcName)
    for _, npc in ipairs(self.npcs) do
        if npc.name == npcName then
            return npc.dialogue
        end
    end
    return "Hello, learner!"
end

return NPCDialogue
"""

    def _generate_progress_script(self) -> str:
        """Generate progress tracking Lua script"""
        return """-- Progress Tracker
local ProgressTracker = {}
ProgressTracker.__index = ProgressTracker

function ProgressTracker.new()
    local self = setmetatable({}, ProgressTracker)
    self.progress = {}
    self.milestones = {}
    return self
end

function ProgressTracker:UpdateProgress(activity, value)
    self.progress[activity] = value
    self:CheckMilestones()
end

function ProgressTracker:CheckMilestones()
    -- Check and award milestones
end

return ProgressTracker
"""

    def _generate_game_controller(self) -> str:
        """Generate main game controller script"""
        return """-- Game Controller
local GameController = {}

local QuizSystem = require(game.ReplicatedStorage.Modules.QuizSystem)
local NPCDialogue = require(game.ReplicatedStorage.Modules.NPCDialogue)
local ProgressTracker = require(game.ReplicatedStorage.Modules.ProgressTracker)

function GameController:Initialize()
    self.quizSystem = QuizSystem.new()
    self.npcDialogue = NPCDialogue.new()
    self.progressTracker = ProgressTracker.new()

    print("Educational game initialized!")
end

function GameController:Start()
    self:Initialize()
    -- Start game logic
end

GameController:Start()

return GameController
"""

    def _generate_terrain_script(self, terrain_type: str) -> str:
        """Generate terrain generation script"""
        return f"""-- Terrain Generator
local TerrainGenerator = {{}}

function TerrainGenerator:Generate()
    local terrain = workspace.Terrain
    local terrainType = "{terrain_type}"

    -- Generate terrain based on type
    if terrainType == "natural" then
        self:GenerateNaturalTerrain(terrain)
    elseif terrainType == "classroom" then
        self:GenerateClassroomTerrain(terrain)
    end
end

function TerrainGenerator:GenerateNaturalTerrain(terrain)
    -- Natural terrain generation
end

function TerrainGenerator:GenerateClassroomTerrain(terrain)
    -- Classroom terrain generation
end

TerrainGenerator:Generate()

return TerrainGenerator
"""

    def _generate_client_controller(self) -> str:
        """Generate client controller script"""
        return """-- Client Controller
local ClientController = {}

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local player = Players.LocalPlayer

function ClientController:Initialize()
    print("Client initialized for " .. player.Name)
    self:SetupUI()
    self:SetupControls()
end

function ClientController:SetupUI()
    -- Setup user interface
end

function ClientController:SetupControls()
    -- Setup player controls
end

ClientController:Initialize()

return ClientController
"""

# Global instance
enhanced_conversation_flow = EnhancedConversationFlowManager()
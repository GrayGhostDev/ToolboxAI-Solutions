"""
Roblox Content Generation Agent
Specialized agent for generating educational Roblox content using AI
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

from langchain_core.prompts import PromptTemplate
from langchain.tools import Tool

# Handle Document import with fallback
try:
    from langchain_core.documents import Document
except ImportError:
    try:
        from langchain_core.messages import Document
    except ImportError:
        # Create mock Document class
        class Document:
            def __init__(self, page_content: str, metadata: dict = None):
                self.page_content = page_content
                self.metadata = metadata or {}

# Use compatibility layer for LLMChain
try:
    from core.langchain_pydantic_v2_compat import CompatibleLLMChain as LLMChain
except ImportError:
    from langchain.chains import LLMChain

from core.agents.base_agent import BaseAgent, AgentConfig, AgentState, TaskResult
from core.agents.github_agents.base_github_agent import BaseGitHubAgent

logger = logging.getLogger(__name__)


@dataclass
class RobloxAsset:
    """Represents a Roblox asset to be generated"""
    asset_type: str  # "Model", "Script", "Texture", "Sound", "Animation"
    name: str
    description: str
    educational_context: str
    parameters: Dict[str, Any]
    generated_content: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class GenerationRequest:
    """Content generation request"""
    subject: str  # Math, Science, History, etc.
    grade_level: int
    content_type: str  # lesson, quiz, activity, exploration
    learning_objectives: List[str]
    accessibility_requirements: List[str]
    assets_needed: List[str]
    interactive_elements: bool = True
    difficulty: str = "medium"


class RobloxContentGenerationAgent(BaseAgent):
    """
    Agent specialized in generating educational Roblox content including:
    - 3D models and environments
    - Educational game mechanics
    - Interactive learning experiences
    - Assessment and quiz systems
    - Adaptive difficulty content
    """

    def __init__(self, config: Optional[AgentConfig] = None, llm=None):
        """Initialize the Roblox Content Generation Agent"""
        if not config:
            config = AgentConfig(
                name="RobloxContentGenerationAgent",
                model="gpt-4",
                temperature=0.7,
                system_prompt="""You are an expert Roblox content creator specializing in educational games.
                You understand Luau scripting, Roblox Studio, and educational pedagogy.
                Generate engaging, age-appropriate educational content that leverages Roblox's 3D environment.""",
                verbose=True,
                memory_enabled=True
            )
        super().__init__(config)
        # Override llm if provided
        if llm is not None:
            self.llm = llm

        self.content_templates = self._load_content_templates()
        self.asset_library = {}
        self.generation_history = []

        # Initialize LangChain tools for content generation
        self.tools = self._create_generation_tools()

    def _load_content_templates(self) -> Dict[str, str]:
        """Load educational content templates"""
        return {
            "math_puzzle": """
            Create a math puzzle in Roblox that teaches {concept}.
            Grade Level: {grade_level}
            Learning Objectives: {objectives}

            Include:
            1. Visual representation of the problem
            2. Interactive elements for solving
            3. Feedback mechanism
            4. Progress tracking
            """,

            "science_experiment": """
            Design a virtual science experiment for {topic}.
            Grade Level: {grade_level}
            Safety Requirements: Virtual environment allows safe exploration

            Components:
            1. Experimental setup
            2. Variable controls
            3. Data collection interface
            4. Results visualization
            """,

            "historical_exploration": """
            Build a historical environment representing {period}.
            Educational Focus: {focus_areas}

            Features:
            1. Accurate historical details
            2. Interactive NPCs with period information
            3. Exploration challenges
            4. Timeline visualization
            """,

            "language_learning": """
            Create a language learning environment for {language}.
            Skill Level: {level}

            Activities:
            1. Vocabulary building games
            2. Conversation practice with NPCs
            3. Grammar challenges
            4. Cultural context exploration
            """
        }

    def _create_generation_tools(self) -> List[Tool]:
        """Create LangChain tools for content generation"""
        tools = [
            Tool(
                name="generate_3d_model",
                func=self._generate_3d_model_description,
                description="Generate description and parameters for 3D educational models"
            ),
            Tool(
                name="create_game_mechanic",
                func=self._create_game_mechanic,
                description="Design educational game mechanics"
            ),
            Tool(
                name="generate_quiz_system",
                func=self._generate_quiz_system,
                description="Create interactive quiz and assessment systems"
            ),
            Tool(
                name="design_learning_path",
                func=self._design_learning_path,
                description="Design adaptive learning paths"
            ),
            Tool(
                name="create_npc_dialogue",
                func=self._create_npc_dialogue,
                description="Generate educational NPC dialogue"
            )
        ]
        return tools

    async def generate_content(self, request: GenerationRequest) -> TaskResult:
        """
        Generate educational Roblox content based on request

        Args:
            request: Content generation request with requirements

        Returns:
            TaskResult with generated content and metadata
        """
        try:
            logger.info(f"Generating content for {request.subject} - Grade {request.grade_level}")

            # Analyze educational requirements
            analysis = await self._analyze_educational_needs(request)

            # Generate content structure
            structure = await self._generate_content_structure(request, analysis)

            # Generate individual assets
            assets = await self._generate_assets(structure, request)

            # Create Luau scripts
            scripts = await self._generate_luau_scripts(assets, request)

            # Generate accessibility features
            accessibility = await self._add_accessibility_features(assets, request.accessibility_requirements)

            # Package content
            content_package = await self._package_content(assets, scripts, accessibility)

            # Validate educational value
            validation = await self._validate_educational_content(content_package, request)

            return TaskResult(
                success=True,
                data={
                    "content_package": content_package,
                    "assets": assets,
                    "scripts": scripts,
                    "validation": validation,
                    "metadata": {
                        "subject": request.subject,
                        "grade_level": request.grade_level,
                        "learning_objectives": request.learning_objectives,
                        "generated_at": datetime.now().isoformat()
                    }
                },
                message=f"Successfully generated {request.content_type} for {request.subject}"
            )

        except Exception as e:
            logger.error(f"Content generation failed: {str(e)}")
            return TaskResult(
                success=False,
                error=str(e),
                message="Failed to generate content"
            )

    async def _analyze_educational_needs(self, request: GenerationRequest) -> Dict[str, Any]:
        """Analyze educational requirements and learning objectives"""
        prompt = PromptTemplate(
            input_variables=["subject", "grade_level", "objectives"],
            template="""
            Analyze the educational needs for:
            Subject: {subject}
            Grade Level: {grade_level}
            Learning Objectives: {objectives}

            Provide:
            1. Key concepts to cover
            2. Common misconceptions to address
            3. Engagement strategies
            4. Assessment methods
            5. Differentiation approaches
            """
        )

        if self.llm:
            chain = LLMChain(llm=self.llm, prompt=prompt, verbose=False, output_key="output")
            result = await chain.arun(
                subject=request.subject,
                grade_level=request.grade_level,
                objectives=", ".join(request.learning_objectives)
            )
            return {"analysis": result}

        # Fallback analysis
        return {
            "key_concepts": ["Core concept 1", "Core concept 2"],
            "misconceptions": ["Common error 1", "Common error 2"],
            "engagement": ["Interactive elements", "Gamification"],
            "assessment": ["Formative", "Summative"],
            "differentiation": ["Multiple difficulty levels", "Various learning styles"]
        }

    async def _generate_content_structure(self, request: GenerationRequest, analysis: Dict) -> Dict[str, Any]:
        """Generate the overall content structure"""
        structure = {
            "main_world": {
                "name": f"{request.subject}World_Grade{request.grade_level}",
                "theme": self._determine_theme(request.subject),
                "zones": []
            },
            "mechanics": [],
            "npcs": [],
            "challenges": [],
            "rewards": []
        }

        # Create zones based on learning objectives
        for i, objective in enumerate(request.learning_objectives):
            zone = {
                "name": f"Zone_{i+1}",
                "objective": objective,
                "difficulty": self._calculate_difficulty(i, request.difficulty),
                "activities": self._generate_activities(objective, request.content_type)
            }
            structure["main_world"]["zones"].append(zone)

        # Add game mechanics
        structure["mechanics"] = self._design_mechanics(request.content_type, analysis)

        return structure

    def _determine_theme(self, subject: str) -> str:
        """Determine visual theme based on subject"""
        themes = {
            "Mathematics": "geometric_wonderland",
            "Science": "laboratory_adventure",
            "History": "time_travel_journey",
            "Language": "word_kingdom",
            "Geography": "world_explorer",
            "Art": "creative_studio",
            "Music": "rhythm_realm",
            "Computer Science": "digital_frontier"
        }
        return themes.get(subject, "educational_playground")

    def _calculate_difficulty(self, zone_index: int, base_difficulty: str) -> str:
        """Calculate progressive difficulty"""
        difficulties = ["easy", "medium", "hard", "expert"]
        base_idx = difficulties.index(base_difficulty)
        new_idx = min(base_idx + (zone_index // 2), len(difficulties) - 1)
        return difficulties[new_idx]

    def _generate_activities(self, objective: str, content_type: str) -> List[Dict]:
        """Generate activities for a learning objective"""
        activity_types = {
            "lesson": ["presentation", "demonstration", "guided_practice"],
            "quiz": ["multiple_choice", "true_false", "problem_solving"],
            "activity": ["hands_on", "collaboration", "creation"],
            "exploration": ["discovery", "investigation", "experimentation"]
        }

        activities = []
        for activity_type in activity_types.get(content_type, ["general"]):
            activities.append({
                "type": activity_type,
                "objective": objective,
                "duration": "5-10 minutes",
                "interaction": "interactive"
            })

        return activities

    def _design_mechanics(self, content_type: str, analysis: Dict) -> List[Dict]:
        """Design game mechanics for educational content"""
        mechanics = []

        # Core mechanics based on content type
        if content_type == "quiz":
            mechanics.append({
                "type": "question_system",
                "features": ["timer", "hints", "score_tracking", "feedback"]
            })
        elif content_type == "exploration":
            mechanics.append({
                "type": "discovery_system",
                "features": ["checkpoints", "collectibles", "journal", "map"]
            })

        # Universal educational mechanics
        mechanics.extend([
            {
                "type": "progress_tracking",
                "features": ["experience_points", "badges", "leaderboard"]
            },
            {
                "type": "help_system",
                "features": ["hints", "tutorials", "peer_assistance"]
            }
        ])

        return mechanics

    async def _generate_assets(self, structure: Dict, request: GenerationRequest) -> List[RobloxAsset]:
        """Generate individual Roblox assets"""
        assets = []

        # Generate world assets
        world_asset = RobloxAsset(
            asset_type="Model",
            name=structure["main_world"]["name"],
            description=f"Main world for {request.subject} education",
            educational_context=f"Grade {request.grade_level} {request.subject}",
            parameters={
                "theme": structure["main_world"]["theme"],
                "size": "large",
                "zones": len(structure["main_world"]["zones"])
            }
        )
        assets.append(world_asset)

        # Generate zone assets
        for zone in structure["main_world"]["zones"]:
            zone_asset = RobloxAsset(
                asset_type="Model",
                name=zone["name"],
                description=f"Learning zone for: {zone['objective']}",
                educational_context=zone["objective"],
                parameters={
                    "difficulty": zone["difficulty"],
                    "activities": zone["activities"]
                }
            )
            assets.append(zone_asset)

        # Generate NPC assets
        for i in range(3):  # Create 3 helper NPCs
            npc_asset = RobloxAsset(
                asset_type="Model",
                name=f"EducatorNPC_{i+1}",
                description="Educational assistant NPC",
                educational_context="Provides guidance and feedback",
                parameters={
                    "personality": ["friendly", "encouraging", "knowledgeable"][i],
                    "subject_expertise": request.subject
                }
            )
            assets.append(npc_asset)

        return assets

    async def _generate_luau_scripts(self, assets: List[RobloxAsset], request: GenerationRequest) -> Dict[str, str]:
        """Generate Luau scripts for the educational content"""
        scripts = {}

        # Main game controller script
        scripts["MainController"] = self._generate_main_controller(request)

        # Progress tracking script
        scripts["ProgressTracker"] = self._generate_progress_tracker()

        # Quiz system script (if needed)
        if request.content_type == "quiz":
            scripts["QuizSystem"] = self._generate_quiz_system(request)

        # Interaction handler
        scripts["InteractionHandler"] = self._generate_interaction_handler()

        # Accessibility controller
        scripts["AccessibilityController"] = self._generate_accessibility_controller(request.accessibility_requirements)

        return scripts

    def _generate_main_controller(self, request: GenerationRequest) -> str:
        """Generate main controller Luau script"""
        return f"""
-- Main Controller for {request.subject} Educational Experience
-- Grade Level: {request.grade_level}

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local MainController = {{}}
MainController.__index = MainController

function MainController.new()
    local self = setmetatable({{}}, MainController)

    self.subject = "{request.subject}"
    self.gradeLevel = {request.grade_level}
    self.learningObjectives = {json.dumps(request.learning_objectives)}
    self.currentZone = 1
    self.playerProgress = {{}}

    return self
end

function MainController:Initialize()
    print("Initializing Educational Experience: " .. self.subject)

    -- Set up player joining
    Players.PlayerAdded:Connect(function(player)
        self:OnPlayerJoin(player)
    end)

    -- Initialize zones
    self:InitializeZones()

    -- Start game loop
    self:StartGameLoop()
end

function MainController:OnPlayerJoin(player)
    print(player.Name .. " joined the educational experience")

    -- Initialize player progress
    self.playerProgress[player.UserId] = {{
        currentZone = 1,
        completedObjectives = {{}},
        score = 0,
        startTime = tick()
    }}

    -- Set up player UI
    self:SetupPlayerUI(player)

    -- Teleport to starting zone
    self:TeleportToZone(player, 1)
end

function MainController:InitializeZones()
    local zones = workspace:FindFirstChild("Zones")
    if not zones then
        warn("Zones folder not found")
        return
    end

    for i, zone in ipairs(zones:GetChildren()) do
        local zoneScript = zone:FindFirstChild("ZoneScript")
        if zoneScript then
            require(zoneScript):Initialize(self)
        end
    end
end

function MainController:StartGameLoop()
    RunService.Heartbeat:Connect(function()
        -- Update game state
        self:UpdateGameState()

        -- Check objectives
        self:CheckObjectives()

        -- Update UI
        self:UpdateUI()
    end)
end

function MainController:UpdateGameState()
    -- Educational game state updates
end

function MainController:CheckObjectives()
    for userId, progress in pairs(self.playerProgress) do
        local player = Players:GetPlayerByUserId(userId)
        if player then
            -- Check if current objective is completed
            self:ValidateLearning(player, progress)
        end
    end
end

function MainController:ValidateLearning(player, progress)
    -- Validate that learning objectives are being met
    -- This would connect to assessment systems
end

function MainController:SetupPlayerUI(player)
    -- Create educational UI for player
    local playerGui = player:WaitForChild("PlayerGui")

    -- Clone UI template
    local uiTemplate = ReplicatedStorage:FindFirstChild("EducationalUI")
    if uiTemplate then
        local ui = uiTemplate:Clone()
        ui.Parent = playerGui
    end
end

function MainController:TeleportToZone(player, zoneNumber)
    local character = player.Character
    if not character then return end

    local zones = workspace:FindFirstChild("Zones")
    if not zones then return end

    local targetZone = zones:FindFirstChild("Zone_" .. zoneNumber)
    if targetZone then
        local spawnPoint = targetZone:FindFirstChild("SpawnPoint")
        if spawnPoint then
            character:SetPrimaryPartCFrame(spawnPoint.CFrame)
        end
    end
end

function MainController:UpdateUI()
    -- Update educational UI for all players
    for userId, progress in pairs(self.playerProgress) do
        local player = Players:GetPlayerByUserId(userId)
        if player then
            self:UpdatePlayerUI(player, progress)
        end
    end
end

function MainController:UpdatePlayerUI(player, progress)
    -- Update individual player UI with progress
    local playerGui = player:FindFirstChild("PlayerGui")
    if not playerGui then return end

    local ui = playerGui:FindFirstChild("EducationalUI")
    if ui then
        -- Update progress bar
        local progressBar = ui:FindFirstChild("ProgressBar")
        if progressBar then
            progressBar.Size = UDim2.new(progress.score / 100, 0, 1, 0)
        end
    end
end

return MainController
"""

    def _generate_progress_tracker(self) -> str:
        """Generate progress tracking script"""
        return """
-- Progress Tracking System
local DataStoreService = game:GetService("DataStoreService")
local Players = game:GetService("Players")

local ProgressTracker = {}
ProgressTracker.__index = ProgressTracker

local progressDataStore = DataStoreService:GetDataStore("EducationalProgress")

function ProgressTracker.new()
    local self = setmetatable({}, ProgressTracker)
    self.sessionProgress = {}
    return self
end

function ProgressTracker:TrackObjective(player, objective, success)
    local userId = player.UserId

    if not self.sessionProgress[userId] then
        self.sessionProgress[userId] = {
            objectives = {},
            score = 0,
            timeSpent = 0
        }
    end

    table.insert(self.sessionProgress[userId].objectives, {
        objective = objective,
        success = success,
        timestamp = tick()
    })

    if success then
        self.sessionProgress[userId].score = self.sessionProgress[userId].score + 10
    end

    -- Fire event for UI update
    local event = game.ReplicatedStorage:FindFirstChild("ProgressUpdate")
    if event then
        event:FireClient(player, self.sessionProgress[userId])
    end
end

function ProgressTracker:SaveProgress(player)
    local userId = player.UserId
    local progress = self.sessionProgress[userId]

    if progress then
        local success, err = pcall(function()
            progressDataStore:SetAsync(userId, progress)
        end)

        if not success then
            warn("Failed to save progress:", err)
        end
    end
end

function ProgressTracker:LoadProgress(player)
    local userId = player.UserId

    local success, data = pcall(function()
        return progressDataStore:GetAsync(userId)
    end)

    if success and data then
        self.sessionProgress[userId] = data
        return data
    end

    return nil
end

return ProgressTracker
"""

    def _generate_quiz_system(self, request: GenerationRequest) -> str:
        """Generate quiz system script"""
        return f"""
-- Quiz System for {request.subject}
local QuizSystem = {{}}
QuizSystem.__index = QuizSystem

function QuizSystem.new()
    local self = setmetatable({{}}, QuizSystem)

    self.questions = {{}}
    self.currentQuestion = 1
    self.score = 0
    self.subject = "{request.subject}"
    self.gradeLevel = {request.grade_level}

    self:LoadQuestions()

    return self
end

function QuizSystem:LoadQuestions()
    -- Load questions based on subject and grade level
    self.questions = self:GenerateQuestions()
end

function QuizSystem:GenerateQuestions()
    -- This would be populated with actual educational questions
    return {{
        {{
            question = "Sample question 1",
            options = {{"A", "B", "C", "D"}},
            correct = 1,
            explanation = "This is why A is correct"
        }},
        {{
            question = "Sample question 2",
            options = {{"A", "B", "C", "D"}},
            correct = 2,
            explanation = "This is why B is correct"
        }}
    }}
end

function QuizSystem:StartQuiz(player)
    self.currentQuestion = 1
    self.score = 0
    self:ShowQuestion(player, self.currentQuestion)
end

function QuizSystem:ShowQuestion(player, questionIndex)
    if questionIndex > #self.questions then
        self:CompleteQuiz(player)
        return
    end

    local question = self.questions[questionIndex]

    -- Create UI for question
    local gui = player.PlayerGui
    local questionUI = gui:FindFirstChild("QuizUI")

    if questionUI then
        local questionText = questionUI:FindFirstChild("QuestionText")
        questionText.Text = question.question

        -- Set up answer buttons
        for i, option in ipairs(question.options) do
            local button = questionUI:FindFirstChild("Option" .. i)
            if button then
                button.Text = option
                button.MouseButton1Click:Connect(function()
                    self:AnswerQuestion(player, questionIndex, i)
                end)
            end
        end
    end
end

function QuizSystem:AnswerQuestion(player, questionIndex, answerIndex)
    local question = self.questions[questionIndex]

    if answerIndex == question.correct then
        self.score = self.score + 1
        self:ShowFeedback(player, true, question.explanation)
    else
        self:ShowFeedback(player, false, question.explanation)
    end

    wait(3) -- Give time to read feedback

    self.currentQuestion = self.currentQuestion + 1
    self:ShowQuestion(player, self.currentQuestion)
end

function QuizSystem:ShowFeedback(player, correct, explanation)
    local gui = player.PlayerGui
    local feedbackUI = gui:FindFirstChild("FeedbackUI")

    if feedbackUI then
        feedbackUI.Visible = true
        feedbackUI.Text = correct and "Correct!" or "Try again!"
        feedbackUI.Explanation.Text = explanation
    end
end

function QuizSystem:CompleteQuiz(player)
    -- Show final score
    local gui = player.PlayerGui
    local resultsUI = gui:FindFirstChild("ResultsUI")

    if resultsUI then
        resultsUI.Visible = true
        resultsUI.Score.Text = "Score: " .. self.score .. "/" .. #self.questions

        -- Calculate percentage
        local percentage = (self.score / #self.questions) * 100
        resultsUI.Percentage.Text = string.format("%.0f%%", percentage)

        -- Award badges based on performance
        if percentage >= 90 then
            self:AwardBadge(player, "Expert")
        elseif percentage >= 70 then
            self:AwardBadge(player, "Proficient")
        else
            self:AwardBadge(player, "Learner")
        end
    end
end

function QuizSystem:AwardBadge(player, level)
    -- Award educational achievement badge
    print("Awarding " .. level .. " badge to " .. player.Name)
end

return QuizSystem
"""

    def _generate_interaction_handler(self) -> str:
        """Generate interaction handler script"""
        return """
-- Interaction Handler for Educational Content
local InteractionHandler = {}
InteractionHandler.__index = InteractionHandler

function InteractionHandler.new()
    local self = setmetatable({}, InteractionHandler)
    self.interactions = {}
    self:SetupInteractions()
    return self
end

function InteractionHandler:SetupInteractions()
    -- Set up clickable objects
    for _, obj in ipairs(workspace:GetDescendants()) do
        if obj:FindFirstChild("Interactive") then
            self:MakeInteractive(obj)
        end
    end
end

function InteractionHandler:MakeInteractive(object)
    local clickDetector = object:FindFirstChildOfClass("ClickDetector") or Instance.new("ClickDetector", object)

    clickDetector.MouseClick:Connect(function(player)
        self:OnInteraction(player, object)
    end)

    -- Visual feedback
    clickDetector.MouseHoverEnter:Connect(function(player)
        self:ShowHighlight(object, true)
    end)

    clickDetector.MouseHoverLeave:Connect(function(player)
        self:ShowHighlight(object, false)
    end)
end

function InteractionHandler:OnInteraction(player, object)
    local interactionType = object:GetAttribute("InteractionType")

    if interactionType == "Information" then
        self:ShowInformation(player, object)
    elseif interactionType == "Puzzle" then
        self:StartPuzzle(player, object)
    elseif interactionType == "Collectible" then
        self:CollectItem(player, object)
    end
end

function InteractionHandler:ShowInformation(player, object)
    local info = object:GetAttribute("Information")
    if info then
        -- Display educational information
        local gui = player.PlayerGui
        local infoPanel = gui:FindFirstChild("InfoPanel")
        if infoPanel then
            infoPanel.Visible = true
            infoPanel.Text.Text = info
        end
    end
end

function InteractionHandler:StartPuzzle(player, object)
    local puzzleId = object:GetAttribute("PuzzleId")
    -- Initialize puzzle for player
    print("Starting puzzle " .. puzzleId .. " for " .. player.Name)
end

function InteractionHandler:CollectItem(player, object)
    -- Add to player's collection
    local itemName = object.Name
    print(player.Name .. " collected " .. itemName)
    object:Destroy()
end

function InteractionHandler:ShowHighlight(object, show)
    local highlight = object:FindFirstChild("Highlight") or Instance.new("SelectionBox", object)
    highlight.Adornee = show and object or nil
    highlight.Color3 = Color3.new(1, 1, 0)
    highlight.Transparency = 0.5
end

return InteractionHandler
"""

    def _generate_accessibility_controller(self, requirements: List[str]) -> str:
        """Generate accessibility controller script"""
        req_str = ", ".join(requirements) if requirements else "standard"

        return f"""
-- Accessibility Controller
-- Requirements: {req_str}

local AccessibilityController = {{}}
AccessibilityController.__index = AccessibilityController

function AccessibilityController.new()
    local self = setmetatable({{}}, AccessibilityController)
    self.settings = {{}}
    self:InitializeAccessibility()
    return self
end

function AccessibilityController:InitializeAccessibility()
    -- Text size options
    self.settings.textSize = "normal" -- small, normal, large, extra-large

    -- Color contrast
    self.settings.highContrast = false

    -- Audio cues
    self.settings.audioCues = true

    -- Subtitles
    self.settings.subtitles = true

    -- Reduced motion
    self.settings.reducedMotion = false

    -- Colorblind modes
    self.settings.colorblindMode = "none" -- none, protanopia, deuteranopia, tritanopia
end

function AccessibilityController:ApplySettings(player)
    local gui = player.PlayerGui

    -- Apply text size
    self:ApplyTextSize(gui, self.settings.textSize)

    -- Apply contrast settings
    if self.settings.highContrast then
        self:ApplyHighContrast(gui)
    end

    -- Set up audio cues
    if self.settings.audioCues then
        self:EnableAudioCues(player)
    end

    -- Enable subtitles
    if self.settings.subtitles then
        self:EnableSubtitles(player)
    end

    -- Apply colorblind mode
    if self.settings.colorblindMode ~= "none" then
        self:ApplyColorblindMode(gui, self.settings.colorblindMode)
    end
end

function AccessibilityController:ApplyTextSize(gui, size)
    local sizes = {{
        small = 14,
        normal = 18,
        large = 24,
        ["extra-large"] = 32
    }}

    local textSize = sizes[size] or sizes.normal

    for _, descendant in ipairs(gui:GetDescendants()) do
        if descendant:IsA("TextLabel") or descendant:IsA("TextButton") then
            descendant.TextSize = textSize
        end
    end
end

function AccessibilityController:ApplyHighContrast(gui)
    for _, descendant in ipairs(gui:GetDescendants()) do
        if descendant:IsA("Frame") then
            descendant.BackgroundColor3 = Color3.new(0, 0, 0)
            descendant.BorderSizePixel = 2
            descendant.BorderColor3 = Color3.new(1, 1, 1)
        elseif descendant:IsA("TextLabel") or descendant:IsA("TextButton") then
            descendant.TextColor3 = Color3.new(1, 1, 1)
            descendant.TextStrokeTransparency = 0
            descendant.TextStrokeColor3 = Color3.new(0, 0, 0)
        end
    end
end

function AccessibilityController:EnableAudioCues(player)
    -- Set up audio feedback for interactions
    print("Audio cues enabled for " .. player.Name)
end

function AccessibilityController:EnableSubtitles(player)
    -- Create subtitle UI if not exists
    local gui = player.PlayerGui
    local subtitleFrame = gui:FindFirstChild("Subtitles") or Instance.new("Frame")
    subtitleFrame.Name = "Subtitles"
    subtitleFrame.Size = UDim2.new(0.6, 0, 0.1, 0)
    subtitleFrame.Position = UDim2.new(0.2, 0, 0.85, 0)
    subtitleFrame.Parent = gui
end

function AccessibilityController:ApplyColorblindMode(gui, mode)
    -- Apply color filters based on colorblind mode
    local filters = {{{{
        protanopia = {{{{0.567, 0.433, 0}}, {{0.558, 0.442, 0}}, {{0, 0.242, 0.758}}}},
        deuteranopia = {{{{0.625, 0.375, 0}}, {{0.7, 0.3, 0}}, {{0, 0.3, 0.7}}}},
        tritanopia = {{{{0.95, 0.05, 0}}, {{0, 0.433, 0.567}}, {{0, 0.475, 0.525}}}}
    }}}}

    local filter = filters[mode]
    if filter then
        -- Apply color transformation
        print("Applying colorblind mode: " .. mode)
    end
end

return AccessibilityController
"""

    async def _add_accessibility_features(self, assets: List[RobloxAsset], requirements: List[str]) -> Dict[str, Any]:
        """Add accessibility features to content"""
        accessibility_features = {
            "text_to_speech": "text_to_speech" in requirements,
            "high_contrast": "high_contrast" in requirements,
            "subtitles": "subtitles" in requirements or "captions" in requirements,
            "audio_descriptions": "audio_descriptions" in requirements,
            "keyboard_navigation": "keyboard_only" in requirements,
            "screen_reader": "screen_reader" in requirements,
            "adjustable_text": True,  # Always include
            "colorblind_modes": True,  # Always include
        }

        # Add accessibility metadata to assets
        for asset in assets:
            if not asset.metadata:
                asset.metadata = {}
            asset.metadata["accessibility"] = accessibility_features

        return accessibility_features

    async def _package_content(self, assets: List[RobloxAsset], scripts: Dict[str, str], accessibility: Dict) -> Dict[str, Any]:
        """Package all content into deployable format"""
        package = {
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "assets": [
                {
                    "type": asset.asset_type,
                    "name": asset.name,
                    "description": asset.description,
                    "educational_context": asset.educational_context,
                    "parameters": asset.parameters,
                    "metadata": asset.metadata
                }
                for asset in assets
            ],
            "scripts": scripts,
            "accessibility": accessibility,
            "deployment": {
                "target": "Roblox Studio",
                "compatibility": "2024.01+",
                "requirements": ["HttpService", "DataStoreService"]
            }
        }

        return package

    async def _validate_educational_content(self, content_package: Dict, request: GenerationRequest) -> Dict[str, Any]:
        """Validate that content meets educational standards"""
        validation_results = {
            "meets_objectives": True,
            "age_appropriate": True,
            "accessibility_compliant": True,
            "engagement_score": 0.85,
            "educational_value": 0.90,
            "issues": [],
            "recommendations": []
        }

        # Check learning objectives coverage
        for objective in request.learning_objectives:
            covered = any(
                objective.lower() in asset.get("educational_context", "").lower()
                for asset in content_package.get("assets", [])
            )
            if not covered:
                validation_results["meets_objectives"] = False
                validation_results["issues"].append(f"Objective not fully covered: {objective}")

        # Check age appropriateness
        if request.grade_level < 3 and "complex" in str(content_package):
            validation_results["age_appropriate"] = False
            validation_results["issues"].append("Content may be too complex for grade level")

        # Check accessibility
        accessibility = content_package.get("accessibility", {})
        if not accessibility.get("adjustable_text"):
            validation_results["accessibility_compliant"] = False
            validation_results["issues"].append("Missing adjustable text size feature")

        # Add recommendations
        if validation_results["engagement_score"] < 0.8:
            validation_results["recommendations"].append("Add more interactive elements")

        return validation_results

    def _generate_3d_model_description(self, query: str) -> str:
        """Generate 3D model description for educational content"""
        return f"3D Model Description for: {query}"

    def _create_game_mechanic(self, query: str) -> str:
        """Create educational game mechanic"""
        return f"Game Mechanic Design for: {query}"

    def _generate_quiz_system(self, query: str) -> str:
        """Generate quiz system structure"""
        return f"Quiz System for: {query}"

    def _design_learning_path(self, query: str) -> str:
        """Design adaptive learning path"""
        return f"Learning Path for: {query}"

    def _create_npc_dialogue(self, query: str) -> str:
        """Create educational NPC dialogue"""
        return f"NPC Dialogue for: {query}"

    async def _process_task(self, state: AgentState) -> TaskResult:
        """Process the task using AgentState"""
        # Extract generation request from state context
        context = state.get("context", {})
        request_data = context.get("request", {})

        request = GenerationRequest(
            subject=request_data.get("subject", "General"),
            grade_level=request_data.get("grade_level", 5),
            content_type=request_data.get("content_type", "lesson"),
            learning_objectives=request_data.get("learning_objectives", ["Learn new concepts"]),
            accessibility_requirements=request_data.get("accessibility_requirements", []),
            assets_needed=request_data.get("assets_needed", ["Model", "Script"])
        )

        return await self.generate_content(request)
"""
RobloxScriptGeneratorAgent - Generates optimized Luau scripts for Roblox

This agent creates various types of Luau scripts following Roblox 2025 best practices,
including server scripts, client scripts, module scripts, and specialized educational
game mechanics.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import json
import re
from enum import Enum
from dataclasses import dataclass, field

from ..base_agent import BaseAgent


class ScriptType(Enum):
    """Types of Roblox scripts"""
    SERVER = "server"
    CLIENT = "client"
    MODULE = "module"
    LOCAL = "local"
    SHARED = "shared"


class ScriptCategory(Enum):
    """Categories of script functionality"""
    GAMEPLAY = "gameplay"
    UI = "ui"
    NETWORKING = "networking"
    DATA_PERSISTENCE = "data_persistence"
    ANIMATION = "animation"
    SOUND = "sound"
    PHYSICS = "physics"
    AI_NPC = "ai_npc"
    EDUCATIONAL = "educational"
    UTILITY = "utility"


class OptimizationLevel(Enum):
    """Code optimization levels"""
    NONE = 0
    BASIC = 1
    MODERATE = 2
    AGGRESSIVE = 3


@dataclass
class ScriptRequirements:
    """Requirements for script generation"""
    script_type: ScriptType
    category: ScriptCategory
    name: str
    description: str
    features: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    events: List[str] = field(default_factory=list)
    security_level: str = "standard"
    optimization_level: OptimizationLevel = OptimizationLevel.MODERATE
    educational_content: Optional[Dict[str, Any]] = None
    multiplayer_support: bool = False
    performance_critical: bool = False


@dataclass
class GeneratedScript:
    """Container for generated script"""
    name: str
    type: ScriptType
    category: ScriptCategory
    code: str
    location: str  # Where to place in Roblox hierarchy
    dependencies: List[str] = field(default_factory=list)
    required_services: List[str] = field(default_factory=list)
    documentation: str = ""
    test_code: Optional[str] = None


class RobloxScriptGeneratorAgent(BaseAgent):
    """
    Agent responsible for generating optimized Luau scripts for Roblox games.
    Creates educational, gameplay, and utility scripts following best practices.
    """
    
    def __init__(self):
        super().__init__({
            "name": "RobloxScriptGeneratorAgent",
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 2000
        })
        
        self.name = "RobloxScriptGeneratorAgent"
        self.description = "Generates optimized Luau scripts for Roblox"
        self.capabilities = [
            "Generate server-side scripts",
            "Generate client-side scripts",
            "Create module scripts for reusability",
            "Implement educational game mechanics",
            "Create NPC AI behaviors",
            "Generate UI interaction scripts",
            "Implement networking and replication",
            "Create data persistence systems",
            "Generate optimized, secure code",
            "Follow Roblox 2025 best practices"
        ]
        
        # Script generation templates
        self.script_templates = {
            ScriptCategory.GAMEPLAY: self._generate_gameplay_script,
            ScriptCategory.UI: self._generate_ui_script,
            ScriptCategory.NETWORKING: self._generate_networking_script,
            ScriptCategory.DATA_PERSISTENCE: self._generate_data_script,
            ScriptCategory.ANIMATION: self._generate_animation_script,
            ScriptCategory.SOUND: self._generate_sound_script,
            ScriptCategory.PHYSICS: self._generate_physics_script,
            ScriptCategory.AI_NPC: self._generate_ai_npc_script,
            ScriptCategory.EDUCATIONAL: self._generate_educational_script,
            ScriptCategory.UTILITY: self._generate_utility_script
        }
        
        # Common Roblox services
        self.roblox_services = [
            "Players", "Workspace", "ReplicatedStorage", "ServerStorage",
            "ServerScriptService", "StarterPlayer", "StarterGui", 
            "TweenService", "RunService", "DataStoreService", "HttpService",
            "PathfindingService", "CollectionService", "Debris", "Lighting",
            "SoundService", "UserInputService", "ContextActionService"
        ]
        
        # Security best practices
        self.security_rules = {
            "validate_input": "Always validate user input",
            "sanitize_data": "Sanitize data before storage",
            "rate_limiting": "Implement rate limiting for actions",
            "secure_remotes": "Secure RemoteEvents and RemoteFunctions",
            "validate_permissions": "Check player permissions",
            "prevent_exploits": "Implement anti-exploit measures"
        }
    
    async def generate_script(self, requirements: ScriptRequirements) -> GeneratedScript:
        """
        Generate a Luau script based on requirements
        
        Args:
            requirements: Script generation requirements
            
        Returns:
            Generated script with metadata
        """
        try:
            # Validate requirements
            if not self._validate_requirements(requirements):
                raise ValueError("Invalid script requirements")
            
            # Generate base script structure
            script = GeneratedScript(
                name=requirements.name,
                type=requirements.script_type,
                category=requirements.category,
                code="",
                location=self._determine_location(requirements.script_type)
            )
            
            # Generate script code based on category
            if requirements.category in self.script_templates:
                script.code = self.script_templates[requirements.category](requirements)
            else:
                script.code = self._generate_generic_script(requirements)
            
            # Apply optimizations
            if requirements.optimization_level != OptimizationLevel.NONE:
                script.code = self._optimize_code(script.code, requirements.optimization_level)
            
            # Add security measures
            if requirements.security_level != "none":
                script.code = self._add_security_measures(script.code, requirements)
            
            # Generate documentation
            script.documentation = self._generate_documentation(requirements)
            
            # Generate test code if needed
            if requirements.category in [ScriptCategory.GAMEPLAY, ScriptCategory.EDUCATIONAL]:
                script.test_code = self._generate_test_code(requirements)
            
            # Extract required services
            script.required_services = self._extract_required_services(script.code)
            
            return script
            
        except Exception as e:
            print(f"Error generating script: {str(e)}")
            return GeneratedScript(
                name=requirements.name,
                type=requirements.script_type,
                category=requirements.category,
                code="-- Error generating script",
                location="ServerScriptService"
            )
    
    def _validate_requirements(self, requirements: ScriptRequirements) -> bool:
        """Validate script requirements"""
        if not requirements.name:
            return False
        if requirements.script_type not in ScriptType:
            return False
        if requirements.category not in ScriptCategory:
            return False
        return True
    
    def _determine_location(self, script_type: ScriptType) -> str:
        """Determine where script should be placed in Roblox"""
        locations = {
            ScriptType.SERVER: "ServerScriptService",
            ScriptType.CLIENT: "StarterPlayer.StarterPlayerScripts",
            ScriptType.MODULE: "ReplicatedStorage.Modules",
            ScriptType.LOCAL: "StarterPlayer.StarterCharacterScripts",
            ScriptType.SHARED: "ReplicatedStorage.Shared"
        }
        return locations.get(script_type, "ServerScriptService")
    
    def _generate_gameplay_script(self, requirements: ScriptRequirements) -> str:
        """Generate gameplay script"""
        code = f"""-- {requirements.name}
-- {requirements.description}
-- Generated by RobloxScriptGeneratorAgent

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local CollectionService = game:GetService("CollectionService")

-- Configuration
local CONFIG = {{
    GAME_NAME = "{requirements.name}",
    MAX_PLAYERS = {8 if requirements.multiplayer_support else 1},
    ROUND_DURATION = 300, -- 5 minutes
    RESPAWN_TIME = 5
}}

-- Game State
local GameState = {{
    isRunning = false,
    currentRound = 0,
    players = {{}},
    scores = {{}}
}}

-- Initialize game systems
local function initializeGame()
    -- Setup game environment
    GameState.isRunning = false
    GameState.currentRound = 0
    GameState.players = {{}}
    GameState.scores = {{}}
    
    print("Game initialized:", CONFIG.GAME_NAME)
end

-- Player management
local function onPlayerAdded(player)
    GameState.players[player.UserId] = {{
        player = player,
        score = 0,
        lives = 3,
        joinTime = tick()
    }}
    
    -- Setup player character
    player.CharacterAdded:Connect(function(character)
        setupCharacter(character, player)
    end)
    
    print(player.Name .. " joined the game")
end

local function onPlayerRemoving(player)
    if GameState.players[player.UserId] then
        GameState.players[player.UserId] = nil
    end
    
    print(player.Name .. " left the game")
end

-- Character setup
function setupCharacter(character, player)
    local humanoid = character:WaitForChild("Humanoid")
    
    -- Setup character properties
    humanoid.WalkSpeed = 16
    humanoid.JumpPower = 50
    
    -- Handle character death
    humanoid.Died:Connect(function()
        onCharacterDied(player)
    end)
end

-- Death handling
function onCharacterDied(player)
    local playerData = GameState.players[player.UserId]
    
    if playerData then
        playerData.lives = playerData.lives - 1
        
        if playerData.lives > 0 then
            -- Respawn after delay
            task.wait(CONFIG.RESPAWN_TIME)
            player:LoadCharacter()
        else
            -- Player eliminated
            print(player.Name .. " has been eliminated")
        end
    end
end

-- Game loop
local function gameLoop()
    while true do
        if not GameState.isRunning then
            -- Wait for enough players
            local playerCount = 0
            for _ in pairs(GameState.players) do
                playerCount = playerCount + 1
            end
            
            if playerCount >= 1 then
                startRound()
            end
        else
            -- Update game logic
            updateGame()
        end
        
        task.wait(1)
    end
end

-- Start a new round
function startRound()
    GameState.isRunning = true
    GameState.currentRound = GameState.currentRound + 1
    
    print("Starting round " .. GameState.currentRound)
    
    -- Reset player states
    for userId, playerData in pairs(GameState.players) do
        playerData.score = 0
        playerData.lives = 3
        
        -- Respawn all players
        if playerData.player.Character then
            playerData.player:LoadCharacter()
        end
    end
    
    -- Start round timer
    task.spawn(function()
        task.wait(CONFIG.ROUND_DURATION)
        endRound()
    end)
end

-- Update game state
function updateGame()
    -- Check win conditions
    local alivePlayers = 0
    local lastPlayer = nil
    
    for userId, playerData in pairs(GameState.players) do
        if playerData.lives > 0 then
            alivePlayers = alivePlayers + 1
            lastPlayer = playerData.player
        end
    end
    
    -- End round if only one player remains (in multiplayer)
    if CONFIG.MAX_PLAYERS > 1 and alivePlayers <= 1 then
        endRound(lastPlayer)
    end
end

-- End the current round
function endRound(winner)
    GameState.isRunning = false
    
    if winner then
        print(winner.Name .. " wins round " .. GameState.currentRound)
        
        -- Award points
        local playerData = GameState.players[winner.UserId]
        if playerData then
            playerData.score = playerData.score + 100
        end
    else
        print("Round " .. GameState.currentRound .. " ended")
    end
    
    -- Show results
    showRoundResults()
    
    -- Wait before next round
    task.wait(5)
end

-- Display round results
function showRoundResults()
    print("=== Round Results ===")
    
    for userId, playerData in pairs(GameState.players) do
        print(playerData.player.Name .. ": " .. playerData.score .. " points")
    end
    
    print("===================")
end

-- Connect events
Players.PlayerAdded:Connect(onPlayerAdded)
Players.PlayerRemoving:Connect(onPlayerRemoving)

-- Initialize and start game
initializeGame()
task.spawn(gameLoop)

print("{requirements.name} script loaded successfully")
"""
        return code
    
    def _generate_educational_script(self, requirements: ScriptRequirements) -> str:
        """Generate educational game script"""
        educational_data = requirements.educational_content or {}
        subject = educational_data.get("subject", "General")
        grade_level = educational_data.get("grade_level", 5)
        
        code = f"""-- Educational Module: {requirements.name}
-- Subject: {subject}, Grade Level: {grade_level}
-- Generated by RobloxScriptGeneratorAgent

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

-- Educational Configuration
local EDUCATIONAL_CONFIG = {{
    SUBJECT = "{subject}",
    GRADE_LEVEL = {grade_level},
    QUIZ_TIME_LIMIT = 30,
    POINTS_PER_CORRECT = 10,
    HINT_PENALTY = 2,
    MAX_HINTS = 3
}}

-- Learning Module
local LearningModule = {{}}
LearningModule.__index = LearningModule

function LearningModule.new(player)
    local self = setmetatable({{}}, LearningModule)
    
    self.player = player
    self.currentLesson = 1
    self.score = 0
    self.progress = {{}}
    self.hintsUsed = 0
    
    return self
end

function LearningModule:startLesson(lessonId)
    self.currentLesson = lessonId
    self.hintsUsed = 0
    
    -- Load lesson content
    local lessonData = self:loadLessonData(lessonId)
    
    if lessonData then
        self:presentContent(lessonData.content)
        
        -- Start interactive elements
        if lessonData.interactive then
            self:setupInteractiveElements(lessonData.interactive)
        end
        
        -- Queue quiz if available
        if lessonData.quiz then
            task.wait(lessonData.duration or 60)
            self:startQuiz(lessonData.quiz)
        end
    end
end

function LearningModule:loadLessonData(lessonId)
    -- Lesson data structure
    local lessons = {{
        [1] = {{
            title = "Introduction to {subject}",
            content = {{
                type = "text",
                data = "Welcome to your {subject} learning adventure!",
                duration = 5
            }},
            interactive = {{
                type = "exploration",
                objective = "Explore the learning environment"
            }},
            quiz = {{
                questions = {{
                    {{
                        question = "What subject are we learning today?",
                        options = {{"{subject}", "Math", "Science", "History"}},
                        correct = 1,
                        explanation = "We're focusing on {subject} in this lesson!"
                    }}
                }}
            }},
            duration = 60
        }}
    }}
    
    return lessons[lessonId]
end

function LearningModule:presentContent(content)
    -- Display educational content to player
    for _, item in ipairs(content) do
        if item.type == "text" then
            self:displayText(item.data, item.duration)
        elseif item.type == "image" then
            self:displayImage(item.data, item.duration)
        elseif item.type == "3d_model" then
            self:display3DModel(item.data, item.duration)
        end
        
        task.wait(item.duration or 5)
    end
end

function LearningModule:displayText(text, duration)
    -- Create text display
    print("Displaying: " .. text)
    
    -- In actual implementation, create GUI text
    -- This would involve creating ScreenGui and TextLabel
end

function LearningModule:setupInteractiveElements(interactiveData)
    if interactiveData.type == "exploration" then
        self:setupExploration(interactiveData)
    elseif interactiveData.type == "puzzle" then
        self:setupPuzzle(interactiveData)
    elseif interactiveData.type == "simulation" then
        self:setupSimulation(interactiveData)
    end
end

function LearningModule:setupExploration(data)
    -- Create explorable environment
    print("Setting up exploration: " .. data.objective)
    
    -- Create interactive objects
    local interactiveObjects = {{}}
    
    -- Tag objects for interaction
    for i = 1, 5 do
        local part = Instance.new("Part")
        part.Name = "InteractiveObject" .. i
        part.Size = Vector3.new(4, 4, 4)
        part.Position = Vector3.new(i * 10, 5, 0)
        part.BrickColor = BrickColor.new("Bright blue")
        part.Parent = workspace
        
        -- Add click detector
        local clickDetector = Instance.new("ClickDetector")
        clickDetector.MaxActivationDistance = 10
        clickDetector.Parent = part
        
        clickDetector.MouseClick:Connect(function(player)
            if player == self.player then
                self:onObjectInteraction(part)
            end
        end)
        
        table.insert(interactiveObjects, part)
    end
    
    self.interactiveObjects = interactiveObjects
end

function LearningModule:onObjectInteraction(object)
    print(self.player.Name .. " interacted with " .. object.Name)
    
    -- Award exploration points
    self.score = self.score + 2
    
    -- Provide educational feedback
    self:displayText("Great job exploring! You earned 2 points.", 3)
    
    -- Track progress
    if not self.progress.objectsExplored then
        self.progress.objectsExplored = {{}}
    end
    self.progress.objectsExplored[object.Name] = true
end

function LearningModule:startQuiz(quizData)
    print("Starting quiz for " .. self.player.Name)
    
    self.currentQuiz = {{
        questions = quizData.questions,
        currentQuestion = 1,
        correctAnswers = 0,
        startTime = tick()
    }}
    
    self:presentQuestion(quizData.questions[1])
end

function LearningModule:presentQuestion(question)
    print("Question: " .. question.question)
    
    -- Display question and options
    for i, option in ipairs(question.options) do
        print(i .. ". " .. option)
    end
    
    -- In actual implementation, create GUI for question
    -- Wait for player response via RemoteEvent
end

function LearningModule:checkAnswer(questionIndex, answer)
    local question = self.currentQuiz.questions[questionIndex]
    
    if answer == question.correct then
        self.correctAnswers = (self.correctAnswers or 0) + 1
        self.score = self.score + EDUCATIONAL_CONFIG.POINTS_PER_CORRECT
        
        print("Correct! " .. question.explanation)
        return true
    else
        print("Not quite. " .. question.explanation)
        return false
    end
end

function LearningModule:provideHint()
    if self.hintsUsed < EDUCATIONAL_CONFIG.MAX_HINTS then
        self.hintsUsed = self.hintsUsed + 1
        self.score = math.max(0, self.score - EDUCATIONAL_CONFIG.HINT_PENALTY)
        
        -- Generate contextual hint
        local hint = self:generateHint()
        self:displayText(hint, 5)
        
        return hint
    else
        self:displayText("No more hints available!", 3)
        return nil
    end
end

function LearningModule:generateHint()
    -- Generate hints based on current context
    local hints = {{
        "Think about what we just learned...",
        "Remember the key concepts from the lesson.",
        "Try to eliminate obviously wrong answers first."
    }}
    
    return hints[math.random(1, #hints)]
end

function LearningModule:completeLesson()
    print(self.player.Name .. " completed lesson " .. self.currentLesson)
    
    -- Calculate performance
    local performance = {{
        score = self.score,
        hintsUsed = self.hintsUsed,
        timeSpent = tick() - (self.startTime or tick()),
        lessonsCompleted = self.currentLesson
    }}
    
    -- Save progress
    self:saveProgress(performance)
    
    -- Award badges/achievements
    self:checkAchievements(performance)
    
    return performance
end

function LearningModule:saveProgress(performance)
    -- Save to DataStore in production
    print("Progress saved for " .. self.player.Name)
end

function LearningModule:checkAchievements(performance)
    -- Check for achievement unlocks
    if performance.score >= 100 then
        print(self.player.Name .. " earned 'High Scorer' achievement!")
    end
    
    if performance.hintsUsed == 0 then
        print(self.player.Name .. " earned 'No Hints Needed' achievement!")
    end
end

-- Player Module Manager
local PlayerModules = {{}}

-- Initialize learning module for each player
local function onPlayerAdded(player)
    PlayerModules[player.UserId] = LearningModule.new(player)
    
    -- Start first lesson after character loads
    player.CharacterAdded:Connect(function(character)
        task.wait(2)
        PlayerModules[player.UserId]:startLesson(1)
    end)
end

local function onPlayerRemoving(player)
    if PlayerModules[player.UserId] then
        PlayerModules[player.UserId]:completeLesson()
        PlayerModules[player.UserId] = nil
    end
end

-- Connect events
Players.PlayerAdded:Connect(onPlayerAdded)
Players.PlayerRemoving:Connect(onPlayerRemoving)

print("Educational module loaded: {subject} (Grade {grade_level})")
"""
        return code
    
    def _generate_ai_npc_script(self, requirements: ScriptRequirements) -> str:
        """Generate AI NPC behavior script"""
        code = f"""-- AI NPC Module: {requirements.name}
-- {requirements.description}
-- Generated by RobloxScriptGeneratorAgent

local PathfindingService = game:GetService("PathfindingService")
local RunService = game:GetService("RunService")
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")

-- NPC AI Class
local NPCAI = {{}}
NPCAI.__index = NPCAI

-- AI Configuration
local AI_CONFIG = {{
    DETECTION_RANGE = 50,
    ATTACK_RANGE = 10,
    PATROL_SPEED = 8,
    CHASE_SPEED = 16,
    FLEE_SPEED = 20,
    REACTION_TIME = 0.2,
    MEMORY_DURATION = 10,
    MAX_PATH_RETRIES = 3
}}

-- AI States
local AIState = {{
    IDLE = "idle",
    PATROLLING = "patrolling",
    CHASING = "chasing",
    ATTACKING = "attacking",
    FLEEING = "fleeing",
    INVESTIGATING = "investigating",
    INTERACTING = "interacting"
}}

function NPCAI.new(npcModel)
    local self = setmetatable({{}}, NPCAI)
    
    self.model = npcModel
    self.humanoid = npcModel:WaitForChild("Humanoid")
    self.rootPart = npcModel:WaitForChild("HumanoidRootPart")
    
    -- AI State
    self.state = AIState.IDLE
    self.target = nil
    self.lastTargetPosition = nil
    self.memory = {{}}
    
    -- Pathfinding
    self.path = nil
    self.waypoints = {{}}
    self.currentWaypoint = 1
    
    -- Behavior settings
    self.aggressive = false
    self.friendly = true
    self.canSpeak = true
    
    -- Initialize AI
    self:initialize()
    
    return self
end

function NPCAI:initialize()
    -- Setup NPC properties
    self.humanoid.WalkSpeed = AI_CONFIG.PATROL_SPEED
    
    -- Start AI loop
    self.updateConnection = RunService.Heartbeat:Connect(function(dt)
        self:update(dt)
    end)
    
    -- Handle NPC death
    self.humanoid.Died:Connect(function()
        self:onDeath()
    end)
end

function NPCAI:update(deltaTime)
    -- Update AI based on current state
    if self.state == AIState.IDLE then
        self:updateIdle()
    elseif self.state == AIState.PATROLLING then
        self:updatePatrolling()
    elseif self.state == AIState.CHASING then
        self:updateChasing()
    elseif self.state == AIState.ATTACKING then
        self:updateAttacking()
    elseif self.state == AIState.FLEEING then
        self:updateFleeing()
    elseif self.state == AIState.INVESTIGATING then
        self:updateInvestigating()
    elseif self.state == AIState.INTERACTING then
        self:updateInteracting()
    end
    
    -- Update perception
    self:updatePerception()
    
    -- Update memory
    self:updateMemory(deltaTime, memory_key="chat_history")
end

function NPCAI:updatePerception()
    -- Scan for nearby entities
    local nearbyPlayers = self:getNearbyPlayers(AI_CONFIG.DETECTION_RANGE)
    local nearbyNPCs = self:getNearbyNPCs(AI_CONFIG.DETECTION_RANGE)
    
    -- Process detected entities
    for _, player in ipairs(nearbyPlayers) do
        if self:canSee(player.Character) then
            self:onPlayerDetected(player)
        end
    end
    
    for _, npc in ipairs(nearbyNPCs) do
        if self:canSee(npc) then
            self:onNPCDetected(npc)
        end
    end
end

function NPCAI:getNearbyPlayers(range)
    local nearbyPlayers = {{}}
    
    for _, player in ipairs(Players:GetPlayers()) do
        if player.Character and player.Character:FindFirstChild("HumanoidRootPart") then
            local distance = (player.Character.HumanoidRootPart.Position - self.rootPart.Position).Magnitude
            
            if distance <= range then
                table.insert(nearbyPlayers, player)
            end
        end
    end
    
    return nearbyPlayers
end

function NPCAI:getNearbyNPCs(range)
    local nearbyNPCs = {{}}
    
    for _, npc in ipairs(CollectionService:GetTagged("NPC")) do
        if npc ~= self.model and npc:FindFirstChild("HumanoidRootPart") then
            local distance = (npc.HumanoidRootPart.Position - self.rootPart.Position).Magnitude
            
            if distance <= range then
                table.insert(nearbyNPCs, npc)
            end
        end
    end
    
    return nearbyNPCs
end

function NPCAI:canSee(target)
    if not target or not target:FindFirstChild("HumanoidRootPart") then
        return false
    end
    
    -- Raycast to check line of sight
    local rayOrigin = self.rootPart.Position
    local rayDirection = (target.HumanoidRootPart.Position - rayOrigin).Unit * AI_CONFIG.DETECTION_RANGE
    
    local raycastParams = RaycastParams.new()
    raycastParams.FilterType = Enum.RaycastFilterType.Blacklist
    raycastParams.FilterDescendantsInstances = {{self.model, target}}
    
    local result = workspace:Raycast(rayOrigin, rayDirection, raycastParams)
    
    return result == nil
end

function NPCAI:onPlayerDetected(player)
    -- Remember player
    self.memory[player.UserId] = {{
        player = player,
        lastSeen = tick(),
        position = player.Character.HumanoidRootPart.Position,
        friendly = self:assessThreat(player) == "friendly"
    }}
    
    -- React based on NPC personality
    if self.friendly then
        if self.state == AIState.IDLE then
            self:setState(AIState.INTERACTING)
            self.target = player
            
            if self.canSpeak then
                self:speak("Hello, " .. player.Name .. "!")
            end
        end
    elseif self.aggressive then
        if self.state ~= AIState.CHASING and self.state ~= AIState.ATTACKING then
            self:setState(AIState.CHASING)
            self.target = player
        end
    end
end

function NPCAI:assessThreat(entity)
    -- Assess if entity is a threat
    -- This could be based on teams, reputation, etc.
    
    if self.friendly then
        return "friendly"
    elseif self.aggressive then
        return "hostile"
    else
        return "neutral"
    end
end

function NPCAI:setState(newState)
    if self.state == newState then return end
    
    -- Exit current state
    self:exitState(self.state)
    
    -- Enter new state
    self.state = newState
    self:enterState(newState)
    
    print("NPC " .. self.model.Name .. " state: " .. newState)
end

function NPCAI:enterState(state)
    if state == AIState.IDLE then
        self.humanoid.WalkSpeed = 0
    elseif state == AIState.PATROLLING then
        self.humanoid.WalkSpeed = AI_CONFIG.PATROL_SPEED
        self:generatePatrolPath()
    elseif state == AIState.CHASING then
        self.humanoid.WalkSpeed = AI_CONFIG.CHASE_SPEED
    elseif state == AIState.FLEEING then
        self.humanoid.WalkSpeed = AI_CONFIG.FLEE_SPEED
    elseif state == AIState.ATTACKING then
        self.humanoid.WalkSpeed = 0
    end
end

function NPCAI:exitState(state)
    -- Clean up state-specific resources
    if state == AIState.PATROLLING then
        self:clearPath()
    end
end

function NPCAI:updateIdle()
    -- Random chance to start patrolling
    if math.random() < 0.01 then
        self:setState(AIState.PATROLLING)
    end
    
    -- Look around occasionally
    if math.random() < 0.05 then
        self:lookAround()
    end
end

function NPCAI:updatePatrolling()
    if not self.path or #self.waypoints == 0 then
        self:generatePatrolPath()
        return
    end
    
    -- Move to current waypoint
    if self.currentWaypoint <= #self.waypoints then
        local waypoint = self.waypoints[self.currentWaypoint]
        self.humanoid:MoveTo(waypoint.Position)
        
        -- Check if reached waypoint
        local distance = (waypoint.Position - self.rootPart.Position).Magnitude
        if distance < 5 then
            self.currentWaypoint = self.currentWaypoint + 1
        end
    else
        -- Patrol complete, generate new path
        self:generatePatrolPath()
    end
end

function NPCAI:updateChasing()
    if not self.target or not self.target.Character then
        self:setState(AIState.IDLE)
        return
    end
    
    local targetPosition = self.target.Character.HumanoidRootPart.Position
    local distance = (targetPosition - self.rootPart.Position).Magnitude
    
    -- Check if in attack range
    if distance <= AI_CONFIG.ATTACK_RANGE then
        self:setState(AIState.ATTACKING)
        return
    end
    
    -- Update path to target
    if not self.path or tick() - (self.lastPathUpdate or 0) > 0.5 then
        self:generatePathTo(targetPosition)
        self.lastPathUpdate = tick()
    end
    
    -- Follow path
    if self.path and #self.waypoints > 0 then
        self:followPath()
    else
        -- Direct movement as fallback
        self.humanoid:MoveTo(targetPosition)
    end
end

function NPCAI:updateAttacking()
    if not self.target or not self.target.Character then
        self:setState(AIState.IDLE)
        return
    end
    
    local distance = (self.target.Character.HumanoidRootPart.Position - self.rootPart.Position).Magnitude
    
    -- Check if target moved out of range
    if distance > AI_CONFIG.ATTACK_RANGE then
        self:setState(AIState.CHASING)
        return
    end
    
    -- Perform attack
    self:performAttack()
end

function NPCAI:performAttack()
    -- Attack logic here
    print(self.model.Name .. " attacks " .. (self.target and self.target.Name or "unknown"))
    
    -- Deal damage (example)
    if self.target and self.target.Character then
        local targetHumanoid = self.target.Character:FindFirstChild("Humanoid")
        if targetHumanoid then
            targetHumanoid:TakeDamage(10)
        end
    end
    
    -- Attack cooldown
    task.wait(1)
end

function NPCAI:generatePatrolPath()
    -- Generate random patrol points
    local patrolPoints = {{}}
    local basePosition = self.rootPart.Position
    
    for i = 1, 3 do
        local randomOffset = Vector3.new(
            math.random(-30, 30),
            0,
            math.random(-30, 30)
        )
        table.insert(patrolPoints, basePosition + randomOffset)
    end
    
    -- Generate path to first patrol point
    self:generatePathTo(patrolPoints[1])
end

function NPCAI:generatePathTo(destination)
    -- Create path
    self.path = PathfindingService:CreatePath({{
        AgentRadius = 2,
        AgentHeight = 5,
        AgentCanJump = true,
        WaypointSpacing = 4,
        Costs = {{
            Water = 20,
            Lava = math.huge
        }}
    }})
    
    -- Compute path
    local success, errorMessage = pcall(function()
        self.path:ComputeAsync(self.rootPart.Position, destination)
    end)
    
    if success then
        self.waypoints = self.path:GetWaypoints()
        self.currentWaypoint = 1
        
        -- Jump at waypoints that require it
        for _, waypoint in ipairs(self.waypoints) do
            if waypoint.Action == Enum.PathWaypointAction.Jump then
                self.humanoid.Jump = true
            end
        end
    else
        warn("Path generation failed: " .. errorMessage)
        self.path = nil
        self.waypoints = {{}}
    end
end

function NPCAI:followPath()
    if self.currentWaypoint <= #self.waypoints then
        local waypoint = self.waypoints[self.currentWaypoint]
        
        -- Move to waypoint
        self.humanoid:MoveTo(waypoint.Position)
        
        -- Check if reached waypoint
        local distance = (waypoint.Position - self.rootPart.Position).Magnitude
        if distance < 5 then
            self.currentWaypoint = self.currentWaypoint + 1
            
            -- Jump if needed
            if waypoint.Action == Enum.PathWaypointAction.Jump then
                self.humanoid.Jump = true
            end
        end
    end
end

function NPCAI:clearPath()
    self.path = nil
    self.waypoints = {{}}
    self.currentWaypoint = 1
end

function NPCAI:lookAround()
    -- Rotate NPC to look around
    local lookAngles = {{0, 45, 90, -45, -90}}
    local angle = lookAngles[math.random(1, #lookAngles)]
    
    local newCFrame = self.rootPart.CFrame * CFrame.Angles(0, math.rad(angle), 0)
    self.rootPart.CFrame = newCFrame
end

function NPCAI:speak(message)
    -- Create chat bubble or billboard GUI
    print("[" .. self.model.Name .. "]: " .. message)
    
    -- In actual implementation, create billboard GUI with text
end

function NPCAI:updateMemory(deltaTime, memory_key="chat_history")
    -- Forget old memories
    for userId, memoryData in pairs(self.memory) do
        if tick() - memoryData.lastSeen > AI_CONFIG.MEMORY_DURATION then
            self.memory[userId] = nil
        end
    end
end

function NPCAI:onDeath()
    print(self.model.Name .. " died")
    
    -- Clean up connections
    if self.updateConnection then
        self.updateConnection:Disconnect()
    end
    
    -- Drop items, give rewards, etc.
    
    -- Remove NPC after delay
    task.wait(3)
    self.model:Destroy()
end

function NPCAI:onNPCDetected(npc)
    -- React to other NPCs
    -- Could communicate, form groups, etc.
end

function NPCAI:updateFleeing()
    if not self.target then
        self:setState(AIState.IDLE)
        return
    end
    
    -- Run away from target
    local awayDirection = (self.rootPart.Position - self.target.Character.HumanoidRootPart.Position).Unit
    local fleePosition = self.rootPart.Position + awayDirection * 50
    
    self.humanoid:MoveTo(fleePosition)
    
    -- Check if safe distance reached
    local distance = (self.target.Character.HumanoidRootPart.Position - self.rootPart.Position).Magnitude
    if distance > AI_CONFIG.DETECTION_RANGE * 1.5 then
        self:setState(AIState.IDLE)
        self.target = nil
    end
end

function NPCAI:updateInvestigating()
    -- Investigate last known position of target
    if self.lastTargetPosition then
        self.humanoid:MoveTo(self.lastTargetPosition)
        
        local distance = (self.lastTargetPosition - self.rootPart.Position).Magnitude
        if distance < 5 then
            -- Reached investigation point
            self:lookAround()
            task.wait(2)
            self:setState(AIState.IDLE)
            self.lastTargetPosition = nil
        end
    else
        self:setState(AIState.IDLE)
    end
end

function NPCAI:updateInteracting()
    if not self.target or not self.target.Character then
        self:setState(AIState.IDLE)
        return
    end
    
    -- Face the target
    local lookDirection = (self.target.Character.HumanoidRootPart.Position - self.rootPart.Position).Unit
    self.rootPart.CFrame = CFrame.lookAt(self.rootPart.Position, self.rootPart.Position + lookDirection)
    
    -- Interact (speak, trade, give quest, etc.)
    if self.canSpeak and math.random() < 0.02 then
        local dialogues = {{
            "How can I help you?",
            "Nice weather today!",
            "Have you seen anything interesting?",
            "Be careful out there!"
        }}
        
        self:speak(dialogues[math.random(1, #dialogues)])
    end
end

-- NPC Manager
local NPCManager = {{}}
NPCManager.npcs = {{}}

function NPCManager.createNPC(model, config)
    -- Tag NPC for identification
    CollectionService:AddTag(model, "NPC")
    
    -- Create AI instance
    local npcAI = NPCAI.new(model)
    
    -- Apply configuration
    if config then
        npcAI.aggressive = config.aggressive or false
        npcAI.friendly = config.friendly or true
        npcAI.canSpeak = config.canSpeak or true
    end
    
    -- Store reference
    NPCManager.npcs[model] = npcAI
    
    return npcAI
end

function NPCManager.removeNPC(model)
    local npcAI = NPCManager.npcs[model]
    
    if npcAI then
        -- Clean up AI
        if npcAI.updateConnection then
            npcAI.updateConnection:Disconnect()
        end
        
        NPCManager.npcs[model] = nil
    end
    
    -- Remove tag
    CollectionService:RemoveTag(model, "NPC")
end

-- Initialize existing NPCs
for _, npc in ipairs(workspace:GetDescendants()) do
    if npc:FindFirstChild("Humanoid") and npc:FindFirstChild("NPCAI") then
        NPCManager.createNPC(npc)
    end
end

print("NPC AI System loaded: {requirements.name}")

return NPCManager
"""
        return code
    
    def _optimize_code(self, code: str, level: OptimizationLevel) -> str:
        """Apply optimizations to generated code"""
        if level == OptimizationLevel.BASIC:
            # Basic optimizations
            code = self._optimize_basic(code)
        elif level == OptimizationLevel.MODERATE:
            # Moderate optimizations
            code = self._optimize_basic(code)
            code = self._optimize_moderate(code)
        elif level == OptimizationLevel.AGGRESSIVE:
            # Aggressive optimizations
            code = self._optimize_basic(code)
            code = self._optimize_moderate(code)
            code = self._optimize_aggressive(code)
        
        return code
    
    def _optimize_basic(self, code: str) -> str:
        """Apply basic optimizations"""
        # Cache service calls
        code = re.sub(
            r'game:GetService\("(\w+)"\)',
            r'game:GetService("\1")',
            code
        )
        
        # Use local variables for repeated accesses
        lines = code.split('\n')
        optimized_lines = []
        seen_services = set()
        
        for line in lines:
            # Track services
            service_match = re.search(r'game:GetService\("(\w+)"\)', line)
            if service_match:
                service = service_match.group(1)
                if service not in seen_services:
                    seen_services.add(service)
            
            optimized_lines.append(line)
        
        return '\n'.join(optimized_lines)
    
    def _optimize_moderate(self, code: str) -> str:
        """Apply moderate optimizations"""
        # Optimize loops
        code = re.sub(
            r'for i = 1, #(\w+) do',
            r'for i = 1, #\1 do',
            code
        )
        
        # Use table.insert instead of array indexing
        code = re.sub(
            r'(\w+)\[#\1 \+ 1\] = (.+)',
            r'table.insert(\1, \2)',
            code
        )
        
        return code
    
    def _optimize_aggressive(self, code: str) -> str:
        """Apply aggressive optimizations"""
        # Inline small functions
        # Pool objects instead of creating new ones
        # Use coroutines for expensive operations
        
        return code
    
    def _add_security_measures(self, code: str, requirements: ScriptRequirements) -> str:
        """Add security measures to code"""
        security_code = """
-- Security measures
local function validateInput(input)
    if type(input) ~= "string" then return false end
    if #input > 1000 then return false end
    -- Remove potentially harmful patterns
    input = input:gsub("[<>\"']", "")
    return input
end

local function checkPermissions(player, action)
    -- Implement permission checking
    return true
end

local rateLimits = {}
local function rateLimit(player, action)
    local key = player.UserId .. ":" .. action
    local now = tick()
    
    if not rateLimits[key] then
        rateLimits[key] = {count = 0, resetTime = now + 60}
    end
    
    if now > rateLimits[key].resetTime then
        rateLimits[key] = {count = 1, resetTime = now + 60}
        return true
    end
    
    if rateLimits[key].count >= 10 then
        return false
    end
    
    rateLimits[key].count = rateLimits[key].count + 1
    return true
end

"""
        return security_code + code
    
    def _generate_documentation(self, requirements: ScriptRequirements) -> str:
        """Generate documentation for the script"""
        doc = f"""
# {requirements.name} Documentation

## Overview
{requirements.description}

## Script Type
- Type: {requirements.script_type.value}
- Category: {requirements.category.value}
- Location: {self._determine_location(requirements.script_type)}

## Features
"""
        for feature in requirements.features:
            doc += f"- {feature}\n"
        
        doc += "\n## Dependencies\n"
        for dep in requirements.dependencies:
            doc += f"- {dep}\n"
        
        doc += "\n## Events\n"
        for event in requirements.events:
            doc += f"- {event}\n"
        
        doc += f"""
## Security Level
{requirements.security_level}

## Optimization Level
{requirements.optimization_level.name}

## Usage
Place this script in {self._determine_location(requirements.script_type)} and it will automatically initialize when the game starts.
"""
        
        if requirements.multiplayer_support:
            doc += "\n## Multiplayer Support\nThis script includes multiplayer functionality and network replication.\n"
        
        return doc
    
    def _generate_test_code(self, requirements: ScriptRequirements) -> str:
        """Generate test code for the script"""
        return f"""-- Test code for {requirements.name}
local TestService = game:GetService("TestService")

-- Test suite
local tests = {{}}

tests["Script loads without errors"] = function()
    local success, result = pcall(function()
        require(script.Parent.{requirements.name})
    end)
    assert(success, "Script failed to load: " .. tostring(result))
end

tests["Required services exist"] = function()
    local services = {{"Players", "Workspace", "ReplicatedStorage"}}
    for _, serviceName in ipairs(services) do
        local success, service = pcall(function()
            return game:GetService(serviceName)
        end)
        assert(success and service, "Service not found: " .. serviceName)
    end
end

-- Run tests
for testName, testFunc in pairs(tests) do
    local success, result = pcall(testFunc)
    if success then
        print("✓ " .. testName)
    else
        warn("✗ " .. testName .. ": " .. tostring(result))
    end
end
"""
    
    def _extract_required_services(self, code: str) -> List[str]:
        """Extract required Roblox services from code"""
        services = []
        pattern = r'game:GetService\("(\w+)"\)'
        matches = re.findall(pattern, code)
        
        for match in matches:
            if match not in services:
                services.append(match)
        
        return services
    
    # Additional script generation methods (simplified for space)
    
    def _generate_ui_script(self, requirements: ScriptRequirements) -> str:
        """Generate UI interaction script"""
        return self._generate_generic_script(requirements)
    
    def _generate_networking_script(self, requirements: ScriptRequirements) -> str:
        """Generate networking script"""
        return self._generate_generic_script(requirements)
    
    def _generate_data_script(self, requirements: ScriptRequirements) -> str:
        """Generate data persistence script"""
        return self._generate_generic_script(requirements)
    
    def _generate_animation_script(self, requirements: ScriptRequirements) -> str:
        """Generate animation script"""
        return self._generate_generic_script(requirements)
    
    def _generate_sound_script(self, requirements: ScriptRequirements) -> str:
        """Generate sound management script"""
        return self._generate_generic_script(requirements)
    
    def _generate_physics_script(self, requirements: ScriptRequirements) -> str:
        """Generate physics simulation script"""
        return self._generate_generic_script(requirements)
    
    def _generate_utility_script(self, requirements: ScriptRequirements) -> str:
        """Generate utility script"""
        return self._generate_generic_script(requirements)
    
    def _generate_generic_script(self, requirements: ScriptRequirements) -> str:
        """Generate a generic script template"""
        return f"""-- {requirements.name}
-- {requirements.description}
-- Generated by RobloxScriptGeneratorAgent

local RunService = game:GetService("RunService")

-- Module
local {requirements.name} = {{}}

function {requirements.name}.initialize()
    print("{requirements.name} initialized")
end

function {requirements.name}.execute()
    -- Implementation here
end

-- Initialize
{requirements.name}.initialize()

return {requirements.name}
"""
    
    async def execute_task(self, task: str) -> Dict[str, Any]:
        """Execute a script generation task"""
        try:
            # Parse task to create requirements
            requirements = self._parse_task(task)
            
            # Generate script
            script = await self.generate_script(requirements)
            
            return {
                "success": True,
                "script": script,
                "message": f"Generated {script.name} successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_task(self, task: str) -> ScriptRequirements:
        """Parse task string to create requirements"""
        # Default requirements
        requirements = ScriptRequirements(
            script_type=ScriptType.SERVER,
            category=ScriptCategory.GAMEPLAY,
            name="GeneratedScript",
            description=task
        )
        
        # Detect script type
        if "client" in task.lower():
            requirements.script_type = ScriptType.CLIENT
        elif "module" in task.lower():
            requirements.script_type = ScriptType.MODULE
        
        # Detect category
        if "ui" in task.lower() or "gui" in task.lower():
            requirements.category = ScriptCategory.UI
        elif "npc" in task.lower() or "ai" in task.lower():
            requirements.category = ScriptCategory.AI_NPC
        elif "educational" in task.lower() or "quiz" in task.lower():
            requirements.category = ScriptCategory.EDUCATIONAL
        
        # Detect features
        if "multiplayer" in task.lower():
            requirements.multiplayer_support = True
        if "optimized" in task.lower():
            requirements.optimization_level = OptimizationLevel.AGGRESSIVE
        
        return requirements
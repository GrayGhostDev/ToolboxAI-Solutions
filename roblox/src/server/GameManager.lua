--[[
    ToolboxAI Game Manager Module
    Version: 1.0.0
    Description: Manages game state, educational content delivery, and coordinates
                 between different game systems
--]]

local GameManager = {}
GameManager.__index = GameManager

-- Services
local HttpService = game:GetService("HttpService")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Debris = game:GetService("Debris")
local Lighting = game:GetService("Lighting")
local SoundService = game:GetService("SoundService")
local Teams = game:GetService("Teams")
local BadgeService = game:GetService("BadgeService")
local MarketplaceService = game:GetService("MarketplaceService")

-- Module dependencies (these would be required from ServerStorage)
local QuizSystem = nil -- Will be loaded when available
local GamificationHub = nil -- Will be loaded when available

-- Game States Enum
GameManager.GameStates = {
    WAITING = "waiting",
    STARTING = "starting",
    IN_PROGRESS = "in_progress",
    QUIZ_MODE = "quiz_mode",
    REVIEW_MODE = "review_mode",
    COMPLETED = "completed",
    PAUSED = "paused"
}

-- Difficulty Levels
GameManager.Difficulty = {
    BEGINNER = {
        name = "Beginner",
        multiplier = 0.5,
        hintCost = 0,
        timeBonus = 2
    },
    INTERMEDIATE = {
        name = "Intermediate",
        multiplier = 1.0,
        hintCost = 5,
        timeBonus = 1.5
    },
    ADVANCED = {
        name = "Advanced",
        multiplier = 1.5,
        hintCost = 10,
        timeBonus = 1.2
    },
    EXPERT = {
        name = "Expert",
        multiplier = 2.0,
        hintCost = 15,
        timeBonus = 1.0
    }
}

-- Constructor
function GameManager.new(config)
    local self = setmetatable({}, GameManager)
    
    -- Configuration
    self.config = config or {}
    self.config.maxPlayers = self.config.maxPlayers or 30
    self.config.minPlayers = self.config.minPlayers or 1
    self.config.roundDuration = self.config.roundDuration or 600 -- 10 minutes
    self.config.intermissionDuration = self.config.intermissionDuration or 30
    
    -- State
    self.currentState = GameManager.GameStates.WAITING
    self.currentLesson = nil
    self.currentQuiz = nil
    self.currentDifficulty = GameManager.Difficulty.INTERMEDIATE
    self.roundStartTime = 0
    self.roundNumber = 0
    
    -- Players
    self.activePlayers = {}
    self.spectators = {}
    self.teams = {}
    
    -- Content
    self.loadedContent = {}
    self.environmentAssets = {}
    self.soundEffects = {}
    
    -- Statistics
    self.statistics = {
        totalRounds = 0,
        totalQuestions = 0,
        correctAnswers = 0,
        totalHints = 0,
        averageScore = 0,
        topScore = 0,
        topPlayer = nil
    }
    
    -- Events
    self.events = {}
    self.eventConnections = {}
    
    self:Initialize()
    
    return self
end

-- Initialize game systems
function GameManager:Initialize()
    -- Create teams if needed
    self:SetupTeams()
    
    -- Setup environment
    self:SetupEnvironment()
    
    -- Load sound effects
    self:LoadSoundEffects()
    
    -- Start game loop
    self:StartGameLoop()
    
    print("[GameManager] Initialized successfully")
end

-- Setup teams for collaborative learning
function GameManager:SetupTeams()
    -- Clear existing teams
    for _, team in ipairs(Teams:GetTeams()) do
        team:Destroy()
    end
    
    -- Create default teams
    local teamColors = {
        BrickColor.new("Bright blue"),
        BrickColor.new("Bright red"),
        BrickColor.new("Bright green"),
        BrickColor.new("Bright yellow")
    }
    
    local teamNames = {"Alpha", "Beta", "Gamma", "Delta"}
    
    for i = 1, 4 do
        local team = Instance.new("Team")
        team.Name = "Team " .. teamNames[i]
        team.TeamColor = teamColors[i]
        team.AutoAssignable = true
        team.Parent = Teams
        
        self.teams[teamNames[i]] = team
    end
end

-- Setup environment defaults
function GameManager:SetupEnvironment()
    -- Lighting settings for educational environment
    Lighting.Brightness = 1.5
    Lighting.OutdoorAmbient = Color3.fromRGB(140, 140, 140)
    Lighting.Ambient = Color3.fromRGB(100, 100, 100)
    Lighting.ColorShift_Top = Color3.fromRGB(255, 255, 200)
    Lighting.ColorShift_Bottom = Color3.fromRGB(200, 200, 255)
    Lighting.ClockTime = 14 -- 2 PM for good lighting
    
    -- Create spawn location if needed
    if not workspace:FindFirstChild("SpawnLocation") then
        local spawn = Instance.new("SpawnLocation")
        spawn.Name = "MainSpawn"
        spawn.Position = Vector3.new(0, 5, 0)
        spawn.Size = Vector3.new(10, 1, 10)
        spawn.TopSurface = Enum.SurfaceType.Smooth
        spawn.Anchored = true
        spawn.CanCollide = true
        spawn.Parent = workspace
    end
end

-- Load sound effects
function GameManager:LoadSoundEffects()
    local sounds = {
        correct = {id = "rbxassetid://1836830755", volume = 0.5},
        incorrect = {id = "rbxassetid://2767090", volume = 0.5},
        levelUp = {id = "rbxassetid://1836830426", volume = 0.7},
        countdown = {id = "rbxassetid://1836829977", volume = 0.5},
        victory = {id = "rbxassetid://1836833474", volume = 0.8},
        notification = {id = "rbxassetid://2767087", volume = 0.3}
    }
    
    for name, config in pairs(sounds) do
        local sound = Instance.new("Sound")
        sound.Name = name
        sound.SoundId = config.id
        sound.Volume = config.volume
        sound.Parent = SoundService
        self.soundEffects[name] = sound
    end
end

-- Play sound effect
function GameManager:PlaySound(soundName, playOnClient)
    local sound = self.soundEffects[soundName]
    if sound then
        if playOnClient then
            -- Play for all clients
            for _, player in ipairs(game.Players:GetPlayers()) do
                local clientSound = sound:Clone()
                clientSound.Parent = player.PlayerGui
                clientSound:Play()
                Debris:AddItem(clientSound, clientSound.TimeLength + 1)
            end
        else
            sound:Play()
        end
    end
end

-- State management
function GameManager:SetState(newState)
    local oldState = self.currentState
    self.currentState = newState
    
    print(string.format("[GameManager] State changed: %s -> %s", oldState, newState))
    
    -- Fire state change event
    self:FireEvent("StateChanged", oldState, newState)
    
    -- Handle state-specific logic
    if newState == GameManager.GameStates.STARTING then
        self:OnRoundStarting()
    elseif newState == GameManager.GameStates.IN_PROGRESS then
        self:OnRoundInProgress()
    elseif newState == GameManager.GameStates.QUIZ_MODE then
        self:OnQuizMode()
    elseif newState == GameManager.GameStates.COMPLETED then
        self:OnRoundCompleted()
    end
end

-- Game loop
function GameManager:StartGameLoop()
    spawn(function()
        while true do
            if self.currentState == GameManager.GameStates.WAITING then
                -- Wait for minimum players
                if self:GetActivePlayerCount() >= self.config.minPlayers then
                    self:SetState(GameManager.GameStates.STARTING)
                end
                
            elseif self.currentState == GameManager.GameStates.STARTING then
                -- Countdown before starting
                for i = 10, 1, -1 do
                    self:BroadcastMessage(string.format("Round starting in %d seconds...", i))
                    if i <= 3 then
                        self:PlaySound("countdown", true)
                    end
                    wait(1)
                end
                self:SetState(GameManager.GameStates.IN_PROGRESS)
                
            elseif self.currentState == GameManager.GameStates.IN_PROGRESS then
                -- Main game logic
                local elapsed = tick() - self.roundStartTime
                if elapsed >= self.config.roundDuration then
                    self:SetState(GameManager.GameStates.COMPLETED)
                end
                
            elseif self.currentState == GameManager.GameStates.COMPLETED then
                -- Show results and prepare for next round
                self:ShowRoundResults()
                wait(self.config.intermissionDuration)
                self:SetState(GameManager.GameStates.WAITING)
            end
            
            wait(1)
        end
    end)
end

-- Round event handlers
function GameManager:OnRoundStarting()
    self.roundNumber = self.roundNumber + 1
    self.roundStartTime = tick()
    
    -- Reset player states
    for _, player in pairs(self.activePlayers) do
        self:ResetPlayerState(player)
    end
    
    -- Load lesson content if available
    if self.currentLesson then
        self:LoadLessonContent(self.currentLesson)
    end
    
    self:BroadcastMessage("Round " .. self.roundNumber .. " is starting!")
end

function GameManager:OnRoundInProgress()
    -- Enable game mechanics
    self:EnableGameMechanics()
    
    -- Start tracking progress
    self:StartProgressTracking()
    
    self:PlaySound("notification", true)
end

function GameManager:OnQuizMode()
    -- Initialize quiz if available
    if self.currentQuiz then
        self:StartQuiz(self.currentQuiz)
    end
end

function GameManager:OnRoundCompleted()
    self.statistics.totalRounds = self.statistics.totalRounds + 1
    
    -- Disable game mechanics
    self:DisableGameMechanics()
    
    -- Calculate and award points
    self:CalculateRoundPoints()
    
    -- Play victory sound
    self:PlaySound("victory", true)
    
    self:BroadcastMessage("Round completed! Great job everyone!")
end

-- Content management
function GameManager:LoadLessonContent(lessonData)
    print(string.format("[GameManager] Loading lesson: %s", lessonData.name or "Unknown"))
    
    -- Apply environment modifications
    if lessonData.environment then
        self:ApplyEnvironment(lessonData.environment)
    end
    
    -- Load interactive objects
    if lessonData.objects then
        self:LoadInteractiveObjects(lessonData.objects)
    end
    
    -- Setup quiz if present
    if lessonData.quiz then
        self.currentQuiz = lessonData.quiz
    end
    
    self.currentLesson = lessonData
end

function GameManager:ApplyEnvironment(environmentData)
    -- Terrain modifications
    if environmentData.terrain and environmentData.terrain ~= "" then
        local success, err = pcall(function()
            -- Use safe terrain application instead of loadstring
            local TerrainManager = require(script.Parent.Parent.ModuleScripts.TerrainManager)
            if TerrainManager then
                TerrainManager:ApplyTerrainData(environmentData.terrain)
            end
        end)
        if not success then
            warn("[GameManager] Failed to apply terrain: " .. tostring(err))
        end
    end
    
    -- Lighting modifications
    if environmentData.lighting then
        for property, value in pairs(environmentData.lighting) do
            pcall(function()
                Lighting[property] = value
            end)
        end
    end
    
    -- Skybox modifications
    if environmentData.skybox then
        local sky = Lighting:FindFirstChild("Sky") or Instance.new("Sky", Lighting)
        for property, value in pairs(environmentData.skybox) do
            pcall(function()
                sky[property] = value
            end)
        end
    end
end

function GameManager:LoadInteractiveObjects(objects)
    -- Clear existing objects
    local objectFolder = workspace:FindFirstChild("InteractiveObjects")
    if objectFolder then
        objectFolder:Destroy()
    end
    objectFolder = Instance.new("Folder")
    objectFolder.Name = "InteractiveObjects"
    objectFolder.Parent = workspace
    
    -- Create new objects
    for _, objData in ipairs(objects) do
        local part = Instance.new("Part")
        part.Name = objData.name or "InteractiveObject"
        part.Position = objData.position or Vector3.new(0, 10, 0)
        part.Size = objData.size or Vector3.new(4, 4, 4)
        part.BrickColor = BrickColor.new(objData.color or "Bright blue")
        part.Material = objData.material or Enum.Material.Neon
        part.Anchored = true
        part.CanCollide = true
        part.Parent = objectFolder
        
        -- Add interaction
        if objData.interaction then
            local clickDetector = Instance.new("ClickDetector")
            clickDetector.MaxActivationDistance = 20
            clickDetector.Parent = part
            
            clickDetector.MouseClick:Connect(function(player)
                self:OnObjectInteraction(player, part, objData)
            end)
        end
        
        -- Add label
        if objData.label then
            local billboardGui = Instance.new("BillboardGui")
            billboardGui.Size = UDim2.new(0, 200, 0, 50)
            billboardGui.StudsOffset = Vector3.new(0, 3, 0)
            billboardGui.Parent = part
            
            local textLabel = Instance.new("TextLabel")
            textLabel.Size = UDim2.new(1, 0, 1, 0)
            textLabel.Text = objData.label
            textLabel.TextScaled = true
            textLabel.BackgroundTransparency = 0.5
            textLabel.BackgroundColor3 = Color3.new(0, 0, 0)
            textLabel.TextColor3 = Color3.new(1, 1, 1)
            textLabel.Parent = billboardGui
        end
    end
end

function GameManager:OnObjectInteraction(player, object, data)
    print(string.format("[GameManager] Player %s interacted with %s", player.Name, object.Name))
    
    -- Award points for interaction
    local playerData = self.activePlayers[player]
    if playerData then
        playerData.score = playerData.score + (data.points or 5)
        self:UpdatePlayerScore(player, playerData.score)
    end
    
    -- Trigger any associated events
    if data.event then
        self:FireEvent("ObjectInteraction", player, object, data)
    end
    
    -- Play feedback sound
    self:PlaySound("correct", false)
end

-- Player management
function GameManager:AddPlayer(player)
    if not self.activePlayers[player] then
        self.activePlayers[player] = {
            score = 0,
            progress = 0,
            hints = 0,
            correctAnswers = 0,
            totalAnswers = 0,
            achievements = {},
            team = nil
        }
        
        -- Auto-assign team
        local smallestTeam = self:GetSmallestTeam()
        if smallestTeam then
            player.Team = smallestTeam
            self.activePlayers[player].team = smallestTeam
        end
        
        print(string.format("[GameManager] Added player: %s", player.Name))
    end
end

function GameManager:RemovePlayer(player)
    if self.activePlayers[player] then
        self.activePlayers[player] = nil
        print(string.format("[GameManager] Removed player: %s", player.Name))
    end
end

function GameManager:GetActivePlayerCount()
    local count = 0
    for _ in pairs(self.activePlayers) do
        count = count + 1
    end
    return count
end

function GameManager:GetSmallestTeam()
    local teamCounts = {}
    for name, team in pairs(self.teams) do
        teamCounts[team] = 0
    end
    
    for _, playerData in pairs(self.activePlayers) do
        if playerData.team then
            teamCounts[playerData.team] = teamCounts[playerData.team] + 1
        end
    end
    
    local smallestTeam = nil
    local smallestCount = math.huge
    
    for team, count in pairs(teamCounts) do
        if count < smallestCount then
            smallestTeam = team
            smallestCount = count
        end
    end
    
    return smallestTeam
end

function GameManager:ResetPlayerState(player)
    local playerData = self.activePlayers[player]
    if playerData then
        playerData.progress = 0
        playerData.hints = 0
        playerData.correctAnswers = 0
        playerData.totalAnswers = 0
        
        -- Reset player character position
        if player.Character and player.Character:FindFirstChild("HumanoidRootPart") then
            player.Character.HumanoidRootPart.CFrame = CFrame.new(0, 10, 0)
        end
    end
end

function GameManager:UpdatePlayerScore(player, score)
    local playerData = self.activePlayers[player]
    if playerData then
        playerData.score = score
        
        -- Update leaderboard
        if player:FindFirstChild("leaderstats") then
            local scoreValue = player.leaderstats:FindFirstChild("Score")
            if scoreValue then
                scoreValue.Value = score
            end
        end
        
        -- Check for achievements
        self:CheckAchievements(player, playerData)
        
        -- Update statistics
        if score > self.statistics.topScore then
            self.statistics.topScore = score
            self.statistics.topPlayer = player.Name
        end
    end
end

-- Achievement system
function GameManager:CheckAchievements(player, playerData)
    local achievements = {
        {id = "first_points", threshold = 10, points = 10, name = "First Steps"},
        {id = "quick_learner", threshold = 50, points = 25, name = "Quick Learner"},
        {id = "scholar", threshold = 100, points = 50, name = "Scholar"},
        {id = "expert", threshold = 500, points = 100, name = "Expert"},
        {id = "master", threshold = 1000, points = 200, name = "Master"}
    }
    
    for _, achievement in ipairs(achievements) do
        if playerData.score >= achievement.threshold and not playerData.achievements[achievement.id] then
            playerData.achievements[achievement.id] = true
            self:AwardAchievement(player, achievement)
        end
    end
end

function GameManager:AwardAchievement(player, achievement)
    print(string.format("[GameManager] Player %s earned achievement: %s", player.Name, achievement.name))
    
    -- Play achievement sound
    self:PlaySound("levelUp", false)
    
    -- Fire achievement event
    self:FireEvent("AchievementUnlocked", player, achievement)
    
    -- Show notification to player
    self:SendPlayerMessage(player, string.format("🏆 Achievement Unlocked: %s!", achievement.name))
end

-- Scoring and results
function GameManager:CalculateRoundPoints()
    local totalScore = 0
    local playerCount = 0
    
    for player, playerData in pairs(self.activePlayers) do
        -- Time bonus
        local timeBonus = math.floor((self.config.roundDuration - (tick() - self.roundStartTime)) * self.currentDifficulty.timeBonus)
        playerData.score = playerData.score + math.max(0, timeBonus)
        
        -- Accuracy bonus
        if playerData.totalAnswers > 0 then
            local accuracy = playerData.correctAnswers / playerData.totalAnswers
            local accuracyBonus = math.floor(accuracy * 100 * self.currentDifficulty.multiplier)
            playerData.score = playerData.score + accuracyBonus
        end
        
        totalScore = totalScore + playerData.score
        playerCount = playerCount + 1
        
        self:UpdatePlayerScore(player, playerData.score)
    end
    
    -- Update statistics
    if playerCount > 0 then
        self.statistics.averageScore = math.floor(totalScore / playerCount)
    end
end

function GameManager:ShowRoundResults()
    local results = {}
    
    for player, playerData in pairs(self.activePlayers) do
        table.insert(results, {
            name = player.Name,
            score = playerData.score,
            correctAnswers = playerData.correctAnswers,
            totalAnswers = playerData.totalAnswers,
            accuracy = playerData.totalAnswers > 0 and 
                      math.floor((playerData.correctAnswers / playerData.totalAnswers) * 100) or 0
        })
    end
    
    -- Sort by score
    table.sort(results, function(a, b)
        return a.score > b.score
    end)
    
    -- Display results
    local message = "📊 Round Results:\n"
    for i, result in ipairs(results) do
        if i <= 5 then -- Show top 5
            message = message .. string.format("%d. %s - %d points (%d%% accuracy)\n", 
                                              i, result.name, result.score, result.accuracy)
        end
    end
    
    self:BroadcastMessage(message)
end

-- Messaging system
function GameManager:BroadcastMessage(message)
    for player, _ in pairs(self.activePlayers) do
        self:SendPlayerMessage(player, message)
    end
end

function GameManager:SendPlayerMessage(player, message)
    -- This would typically fire a RemoteEvent to show the message on the client
    print(string.format("[GameManager -> %s] %s", player.Name, message))
end

-- Event system
function GameManager:FireEvent(eventName, ...)
    if not self.events[eventName] then
        self.events[eventName] = {}
    end
    
    for _, callback in ipairs(self.events[eventName]) do
        spawn(function()
            callback(...)
        end)
    end
end

function GameManager:ConnectEvent(eventName, callback)
    if not self.events[eventName] then
        self.events[eventName] = {}
    end
    
    table.insert(self.events[eventName], callback)
    
    return {
        Disconnect = function()
            for i, cb in ipairs(self.events[eventName]) do
                if cb == callback then
                    table.remove(self.events[eventName], i)
                    break
                end
            end
        end
    }
end

-- Game mechanics control
function GameManager:EnableGameMechanics()
    -- Enable interactive objects
    local objects = workspace:FindFirstChild("InteractiveObjects")
    if objects then
        for _, obj in ipairs(objects:GetChildren()) do
            local clickDetector = obj:FindFirstChild("ClickDetector")
            if clickDetector then
                clickDetector.MaxActivationDistance = 20
            end
        end
    end
end

function GameManager:DisableGameMechanics()
    -- Disable interactive objects
    local objects = workspace:FindFirstChild("InteractiveObjects")
    if objects then
        for _, obj in ipairs(objects:GetChildren()) do
            local clickDetector = obj:FindFirstChild("ClickDetector")
            if clickDetector then
                clickDetector.MaxActivationDistance = 0
            end
        end
    end
end

-- Progress tracking
function GameManager:StartProgressTracking()
    spawn(function()
        while self.currentState == GameManager.GameStates.IN_PROGRESS do
            for player, playerData in pairs(self.activePlayers) do
                -- Update progress based on various factors
                local progress = 0
                
                -- Time-based progress
                local elapsed = tick() - self.roundStartTime
                local timeProgress = math.min(100, (elapsed / self.config.roundDuration) * 100)
                progress = progress + timeProgress * 0.3
                
                -- Score-based progress
                local scoreProgress = math.min(100, (playerData.score / 100) * 100)
                progress = progress + scoreProgress * 0.4
                
                -- Interaction-based progress
                local interactionProgress = math.min(100, (playerData.correctAnswers * 10))
                progress = progress + interactionProgress * 0.3
                
                playerData.progress = math.floor(progress)
                
                -- Update progress display
                if player:FindFirstChild("leaderstats") then
                    local progressValue = player.leaderstats:FindFirstChild("Progress")
                    if progressValue then
                        progressValue.Value = playerData.progress
                    end
                end
            end
            
            wait(1)
        end
    end)
end

-- Quiz management
function GameManager:StartQuiz(quizData)
    if not QuizSystem then
        -- Try to load QuizSystem module
        local success, module = pcall(function()
            return require(game.ServerStorage.Modules:FindFirstChild("QuizSystem"))
        end)
        if success then
            QuizSystem = module
        else
            warn("[GameManager] QuizSystem module not found")
            return
        end
    end
    
    -- Initialize quiz
    local quiz = QuizSystem.new(quizData)
    self.currentQuiz = quiz
    
    -- Start quiz for all players
    self:BroadcastMessage("Quiz starting! Get ready to answer questions.")
    
    -- Fire quiz start event
    self:FireEvent("QuizStarted", quiz)
end

-- Cleanup
function GameManager:Cleanup()
    -- Disconnect all events
    for _, connections in pairs(self.eventConnections) do
        for _, connection in ipairs(connections) do
            connection:Disconnect()
        end
    end
    
    -- Clear game objects
    local objects = workspace:FindFirstChild("InteractiveObjects")
    if objects then
        objects:Destroy()
    end
    
    -- Reset environment
    self:SetupEnvironment()
    
    print("[GameManager] Cleanup completed")
end

return GameManager
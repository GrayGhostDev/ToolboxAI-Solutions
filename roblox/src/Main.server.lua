--[[
    ToolboxAI Educational Platform - Main Server Script
    Version: 1.0.0
    Description: Core server-side script that manages the educational game environment,
                 handles player connections, manages educational sessions, and 
                 coordinates with the AI backend
--]]

-- Services
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local RunService = game:GetService("RunService")
local DataStoreService = game:GetService("DataStoreService")
local HttpService = game:GetService("HttpService")
local MessagingService = game:GetService("MessagingService")
local TeleportService = game:GetService("TeleportService")
local Chat = game:GetService("Chat")

-- Configuration
local CONFIG = {
    DATA_STORE_NAME = "ToolboxAI_PlayerData",
    SESSION_TIMEOUT = 3600, -- 1 hour in seconds
    AUTOSAVE_INTERVAL = 60, -- seconds
    MAX_PLAYERS_PER_SESSION = 30,
    DEBUG_MODE = true
}

-- Initialize folders
local function initializeFolders()
    -- ReplicatedStorage folders
    local remotes = Instance.new("Folder")
    remotes.Name = "Remotes"
    remotes.Parent = ReplicatedStorage
    
    local events = Instance.new("Folder")
    events.Name = "Events"
    events.Parent = remotes
    
    local functions = Instance.new("Folder")
    functions.Name = "Functions"
    functions.Parent = remotes
    
    -- ServerStorage folders
    local modules = Instance.new("Folder")
    modules.Name = "Modules"
    modules.Parent = ServerStorage
    
    local gameData = Instance.new("Folder")
    gameData.Name = "GameData"
    gameData.Parent = ServerStorage
    
    return remotes, modules, gameData
end

local remotes, modules, gameData = initializeFolders()

-- Create Remote Events and Functions
local remoteEvents = {
    PlayerReady = Instance.new("RemoteEvent"),
    UpdateProgress = Instance.new("RemoteEvent"),
    SubmitAnswer = Instance.new("RemoteEvent"),
    RequestHint = Instance.new("RemoteEvent"),
    ReportIssue = Instance.new("RemoteEvent"),
    SendChatMessage = Instance.new("RemoteEvent"),
    UpdateSettings = Instance.new("RemoteEvent"),
    TriggerAnimation = Instance.new("RemoteEvent"),
    AchievementUnlocked = Instance.new("RemoteEvent")
}

local remoteFunctions = {
    GetSessionData = Instance.new("RemoteFunction"),
    GetPlayerProgress = Instance.new("RemoteFunction"),
    GetQuizQuestion = Instance.new("RemoteFunction"),
    GetLeaderboard = Instance.new("RemoteFunction"),
    GetAvailableLessons = Instance.new("RemoteFunction"),
    ValidateAnswer = Instance.new("RemoteFunction"),
    GetHint = Instance.new("RemoteFunction")
}

-- Parent remote events and functions
for name, event in pairs(remoteEvents) do
    event.Name = name
    event.Parent = remotes.Events
end

for name, func in pairs(remoteFunctions) do
    func.Name = name
    func.Parent = remotes.Functions
end

-- Data Stores
local playerDataStore = DataStoreService:GetDataStore(CONFIG.DATA_STORE_NAME)
local sessionDataStore = DataStoreService:GetDataStore("Sessions")
local analyticsDataStore = DataStoreService:GetDataStore("Analytics")

-- Game State
local GameState = {
    currentSession = nil,
    activePlayers = {},
    lessonData = {},
    quizData = {},
    leaderboard = {},
    achievements = {},
    startTime = os.time()
}

-- Player Management
local PlayerManager = {}
PlayerManager.__index = PlayerManager

function PlayerManager.new(player)
    local self = setmetatable({}, PlayerManager)
    self.player = player
    self.userId = tostring(player.UserId)
    self.data = {
        joinTime = os.time(),
        progress = {},
        score = 0,
        achievements = {},
        completedLessons = {},
        currentLesson = nil,
        sessionTime = 0,
        lastSave = os.time()
    }
    self.isReady = false
    return self
end

function PlayerManager:LoadData()
    local success, data = pcall(function()
        return playerDataStore:GetAsync(self.userId)
    end)
    
    if success and data then
        -- Merge saved data with defaults
        for key, value in pairs(data) do
            if self.data[key] ~= nil then
                self.data[key] = value
            end
        end
        print(string.format("Loaded data for player %s", self.player.Name))
    else
        print(string.format("No saved data for player %s, using defaults", self.player.Name))
    end
end

function PlayerManager:SaveData()
    local success, err = pcall(function()
        playerDataStore:SetAsync(self.userId, self.data)
    end)
    
    if success then
        self.data.lastSave = os.time()
        if CONFIG.DEBUG_MODE then
            print(string.format("Saved data for player %s", self.player.Name))
        end
    else
        warn(string.format("Failed to save data for player %s: %s", self.player.Name, tostring(err)))
    end
end

function PlayerManager:UpdateProgress(lessonId, progress)
    self.data.progress[lessonId] = progress
    
    -- Send to backend securely
    spawn(function()
        local requestData = {
            student_id = self.userId,
            lesson_id = lessonId,
            progress = progress,
            timestamp = os.time()
        }
        pcall(function()
            local ApiClient = require(game.ServerScriptService:WaitForChild("ApiClient"))
            ApiClient.postKey("progress", requestData)
        end)
    end)
end

function PlayerManager:AwardAchievement(achievementId, points)
    if not self.data.achievements[achievementId] then
        self.data.achievements[achievementId] = {
            unlocked = true,
            unlockedAt = os.time(),
            points = points
        }
        self.data.score = self.data.score + points
        
        -- Notify client
        remoteEvents.AchievementUnlocked:FireClient(
            self.player,
            achievementId,
            points
        )
        
        return true
    end
    return false
end

-- Session Management
local SessionManager = {}
SessionManager.__index = SessionManager

function SessionManager.new()
    local self = setmetatable({}, SessionManager)
    self.sessionId = HttpService:GenerateGUID(false)
    self.startTime = os.time()
    self.isActive = true
    self.lessonId = nil
    self.participants = {}
    self.settings = {
        maxPlayers = CONFIG.MAX_PLAYERS_PER_SESSION,
        difficulty = "medium",
        mode = "collaborative",
        allowHints = true,
        timeLimit = nil
    }
    return self
end

function SessionManager:AddPlayer(playerManager)
    if #self.participants >= self.settings.maxPlayers then
        return false, "Session is full"
    end
    
    table.insert(self.participants, playerManager)
    playerManager.data.currentSession = self.sessionId
    
    -- Notify backend (session join)
    spawn(function()
        pcall(function()
            local ApiClient = require(game.ServerScriptService:WaitForChild("ApiClient"))
            ApiClient.postKeyWithSuffix("sessions", "/" .. self.sessionId .. "/players", {
                player_id = playerManager.userId,
                player_name = playerManager.player.Name
            })
        end)
    end)
    
    return true
end

function SessionManager:RemovePlayer(playerManager)
    for i, pm in ipairs(self.participants) do
        if pm == playerManager then
            table.remove(self.participants, i)
            playerManager.data.currentSession = nil
            break
        end
    end
end

function SessionManager:LoadLesson(lessonData)
    self.lessonId = lessonData.id
    GameState.lessonData = lessonData
    
    -- Load quiz if present
    if lessonData.quiz then
        GameState.quizData = lessonData.quiz
    end
    
    -- Apply environment changes
    if lessonData.environment then
        self:ApplyEnvironment(lessonData.environment)
    end
    
    -- Notify all players
    for _, pm in ipairs(self.participants) do
        remoteEvents.UpdateProgress:FireClient(pm.player, {
            type = "lesson_loaded",
            lessonId = self.lessonId,
            lessonName = lessonData.name
        })
    end
end

function SessionManager:ApplyEnvironment(environmentData)
    -- This would apply terrain, lighting, and other environmental changes
    -- Based on the AI-generated content
    if environmentData.terrain then
        -- Apply terrain changes using safe predefined functions
        local TerrainManager = require(script.Parent.Parent.ModuleScripts.TerrainManager)
        if TerrainManager then
            pcall(function()
                TerrainManager:ApplyTerrainData(environmentData.terrain)
            end)
        end
    end
    
    if environmentData.lighting then
        -- Apply lighting changes
        local lighting = game:GetService("Lighting")
        for property, value in pairs(environmentData.lighting) do
            pcall(function()
                lighting[property] = value
            end)
        end
    end
end

function SessionManager:EndSession()
    self.isActive = false
    
    -- Save all player data
    for _, pm in ipairs(self.participants) do
        pm:SaveData()
    end
    
    -- Send session summary to backend
    spawn(function()
        pcall(function()
            local ApiClient = require(game.ServerScriptService:WaitForChild("ApiClient"))
            ApiClient.postKeyWithSuffix("sessions", "/" .. self.sessionId .. "/end", {
                end_time = os.time(),
                duration = os.time() - self.startTime,
                participants = #self.participants
            })
        end)
    end)
end

-- Quiz System
local QuizSystem = {}
QuizSystem.__index = QuizSystem

function QuizSystem.new(quizData)
    local self = setmetatable({}, QuizSystem)
    self.questions = quizData.questions or {}
    self.currentQuestionIndex = 1
    self.playerAnswers = {}
    self.startTime = os.time()
    return self
end

function QuizSystem:GetCurrentQuestion()
    if self.currentQuestionIndex <= #self.questions then
        return self.questions[self.currentQuestionIndex]
    end
    return nil
end

function QuizSystem:SubmitAnswer(playerManager, answer)
    local question = self:GetCurrentQuestion()
    if not question then return false, "No active question" end
    
    local isCorrect = answer == question.correct_answer
    local points = isCorrect and (question.points or 10) or 0
    
    -- Record answer
    if not self.playerAnswers[playerManager.userId] then
        self.playerAnswers[playerManager.userId] = {}
    end
    
    self.playerAnswers[playerManager.userId][self.currentQuestionIndex] = {
        answer = answer,
        correct = isCorrect,
        points = points,
        timestamp = os.time()
    }
    
    -- Update player score
    if isCorrect then
        playerManager.data.score = playerManager.data.score + points
    end
    
    return isCorrect, points
end

function QuizSystem:NextQuestion()
    self.currentQuestionIndex = self.currentQuestionIndex + 1
    return self:GetCurrentQuestion()
end

function QuizSystem:GetResults()
    local results = {}
    for userId, answers in pairs(self.playerAnswers) do
        local correct = 0
        local total = 0
        local score = 0
        
        for _, answer in pairs(answers) do
            total = total + 1
            if answer.correct then
                correct = correct + 1
                score = score + answer.points
            end
        end
        
        results[userId] = {
            correct = correct,
            total = total,
            score = score,
            percentage = total > 0 and (correct / total * 100) or 0
        }
    end
    
    return results
end

-- Initialize game session
local currentSession = SessionManager.new()
GameState.currentSession = currentSession

-- Player join handler
Players.PlayerAdded:Connect(function(player)
    print(string.format("Player %s joined", player.Name))
    
    -- Create player manager
    local playerManager = PlayerManager.new(player)
    GameState.activePlayers[player] = playerManager
    
    -- Load player data
    playerManager:LoadData()
    
    -- Add to session
    currentSession:AddPlayer(playerManager)
    
    -- Create leaderstats
    local leaderstats = Instance.new("Folder")
    leaderstats.Name = "leaderstats"
    leaderstats.Parent = player
    
    local score = Instance.new("IntValue")
    score.Name = "Score"
    score.Value = playerManager.data.score
    score.Parent = leaderstats
    
    local progress = Instance.new("IntValue")
    progress.Name = "Progress"
    progress.Value = 0
    progress.Parent = leaderstats
    
    -- Notify backend of player join
    spawn(function()
        pcall(function()
            local ApiClient = require(game.ServerScriptService:WaitForChild("ApiClient"))
            ApiClient.postKey("playersJoin", {
                player_id = tostring(player.UserId),
                player_name = player.Name,
                session_id = currentSession.sessionId
            })
        end)
    end)
end)

-- Player leave handler
Players.PlayerRemoving:Connect(function(player)
    print(string.format("Player %s left", player.Name))
    
    local playerManager = GameState.activePlayers[player]
    if playerManager then
        -- Save data
        playerManager:SaveData()
        
        -- Remove from session
        currentSession:RemovePlayer(playerManager)
        
        -- Clean up
        GameState.activePlayers[player] = nil
        
        -- Notify backend
        spawn(function()
            pcall(function()
                local ApiClient = require(game.ServerScriptService:WaitForChild("ApiClient"))
                ApiClient.postKey("playersLeave", {
                    player_id = tostring(player.UserId),
                    session_time = os.time() - playerManager.data.joinTime
                })
            end)
        end)
    end
end)

-- Remote Event Handlers
remoteEvents.PlayerReady.OnServerEvent:Connect(function(player)
    local playerManager = GameState.activePlayers[player]
    if playerManager then
        playerManager.isReady = true
        print(string.format("Player %s is ready", player.Name))
    end
end)

remoteEvents.SubmitAnswer.OnServerEvent:Connect(function(player, answer)
    local playerManager = GameState.activePlayers[player]
    if not playerManager then return end
    
    if GameState.currentQuiz then
        local correct, points = GameState.currentQuiz:SubmitAnswer(playerManager, answer)
        
        -- Send result to player
        remoteEvents.UpdateProgress:FireClient(player, {
            type = "answer_result",
            correct = correct,
            points = points
        })
        
        -- Update leaderboard
        player.leaderstats.Score.Value = playerManager.data.score
    end
end)

remoteEvents.RequestHint.OnServerEvent:Connect(function(player, questionId)
    local playerManager = GameState.activePlayers[player]
    if not playerManager then return end
    
    if currentSession.settings.allowHints then
        -- Deduct points for hint
        playerManager.data.score = math.max(0, playerManager.data.score - 5)
        player.leaderstats.Score.Value = playerManager.data.score
        
        -- Send hint (would come from quiz data)
        remoteEvents.UpdateProgress:FireClient(player, {
            type = "hint",
            hint = "Think about the relationship between the numbers..."
        })
    end
end)

-- Remote Function Handlers
remoteFunctions.GetSessionData.OnServerInvoke = function(player)
    return {
        sessionId = currentSession.sessionId,
        lessonId = currentSession.lessonId,
        participants = #currentSession.participants,
        settings = currentSession.settings
    }
end

remoteFunctions.GetPlayerProgress.OnServerInvoke = function(player)
    local playerManager = GameState.activePlayers[player]
    if playerManager then
        return playerManager.data.progress
    end
    return {}
end

remoteFunctions.GetQuizQuestion.OnServerInvoke = function(player)
    if GameState.currentQuiz then
        local question = GameState.currentQuiz:GetCurrentQuestion()
        if question then
            -- Remove correct answer before sending
            local safeQuestion = {
                id = question.id,
                text = question.text,
                options = question.options,
                type = question.type,
                points = question.points
            }
            return safeQuestion
        end
    end
    return nil
end

remoteFunctions.GetLeaderboard.OnServerInvoke = function(player)
    local leaderboard = {}
    for p, pm in pairs(GameState.activePlayers) do
        table.insert(leaderboard, {
            name = p.Name,
            score = pm.data.score,
            progress = pm.data.progress
        })
    end
    
    -- Sort by score
    table.sort(leaderboard, function(a, b)
        return a.score > b.score
    end)
    
    return leaderboard
end

-- Auto-save loop
spawn(function()
    while true do
        wait(CONFIG.AUTOSAVE_INTERVAL)
        
        for _, playerManager in pairs(GameState.activePlayers) do
            if os.time() - playerManager.data.lastSave >= CONFIG.AUTOSAVE_INTERVAL then
                playerManager:SaveData()
            end
        end
    end
end)

-- Session timeout check
spawn(function()
    while true do
        wait(60) -- Check every minute
        
        if currentSession.isActive then
            local elapsed = os.time() - currentSession.startTime
            if elapsed >= CONFIG.SESSION_TIMEOUT then
                print("Session timeout reached, ending session")
                currentSession:EndSession()
                
                -- Create new session
                currentSession = SessionManager.new()
                GameState.currentSession = currentSession
                
                -- Re-add all players to new session
                for _, pm in pairs(GameState.activePlayers) do
                    currentSession:AddPlayer(pm)
                end
            end
        end
    end
end)

print("ToolboxAI Educational Platform - Server initialized successfully")

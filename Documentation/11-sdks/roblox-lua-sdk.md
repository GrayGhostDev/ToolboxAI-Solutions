# ToolBoxAI Roblox Lua SDK

Native Lua SDK optimized for Roblox Studio integration and in-game educational experiences.

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Authentication](#authentication)
4. [Core Features](#core-features)
5. [API Reference](#api-reference)
6. [Roblox-Specific Features](#roblox-specific-features)
7. [Event System](#event-system)
8. [Error Handling](#error-handling)
9. [Best Practices](#best-practices)
10. [Examples](#examples)
11. [Studio Plugin Development](#studio-plugin-development)
12. [Performance Optimization](#performance-optimization)
13. [Security](#security)
14. [Troubleshooting](#troubleshooting)

## Installation

### Method 1: Roblox Studio Model (Recommended)

1. Open Roblox Studio
2. Go to Toolbox → Models
3. Search for "ToolBoxAI SDK"
4. Insert into ServerScriptService

### Method 2: Module Script

```lua
-- Create a ModuleScript in ServerScriptService
local ToolBoxAI = {}
ToolBoxAI.__index = ToolBoxAI

-- SDK implementation (see GitHub for full code)
return ToolBoxAI
```

### Method 3: Wally Package Manager

```toml
# wally.toml
[dependencies]
toolboxai = "toolboxai/sdk@1.0.0"
```

```bash
wally install
```

### Method 4: GitHub Release

```lua
-- Download from GitHub releases
-- https://github.com/toolboxai/roblox-sdk/releases
-- Place in ServerScriptService or ReplicatedStorage
```

## Quick Start

### Basic Setup

```lua
-- In ServerScriptService
local ToolBoxAI = require(game.ServerScriptService.ToolBoxAI)

-- Initialize client
local client = ToolBoxAI.new({
    apiKey = "your-api-key-here",
    environment = "production", -- or "sandbox"
    baseUrl = "https://api.toolboxai.com", -- optional
    timeout = 30, -- seconds
    retryCount = 3
})

-- Test connection
client:testConnection():andThen(function(result)
    print("Connected to ToolBoxAI:", result.message)
end):catch(function(error)
    warn("Connection failed:", error.message)
end)
```

### Studio Plugin Setup

```lua
-- In Plugin Script
local toolbar = plugin:CreateToolbar("ToolBoxAI")
local button = toolbar:CreateButton(
    "Deploy Lesson",
    "Deploy educational content to workspace",
    "rbxasset://textures/ui/Settings/Help/PreviewIcon.png"
)

button.Click:Connect(function()
    local ToolBoxAI = require(game.ServerScriptService.ToolBoxAI)
    local client = ToolBoxAI.new({ apiKey = settings.apiKey })

    -- Deploy lesson
    client:deployLesson(lessonId, workspace)
end)
```

## Authentication

### API Key Authentication

```lua
-- Recommended: Store in ServerStorage
local ServerStorage = game:GetService("ServerStorage")
local config = require(ServerStorage.Config)

local client = ToolBoxAI.new({
    apiKey = config.TOOLBOXAI_API_KEY
})
```

### Studio Plugin Authentication

```lua
-- For Studio plugins, use plugin settings
local apiKey = plugin:GetSetting("ToolBoxAIApiKey")

if not apiKey then
    -- Prompt for API key
    apiKey = PromptForApiKey() -- Custom function
    plugin:SetSetting("ToolBoxAIApiKey", apiKey)
end

local client = ToolBoxAI.new({ apiKey = apiKey })
```

### User Authentication (In-Game)

```lua
-- Authenticate player
local function authenticatePlayer(player)
    return client:authenticateUser({
        robloxId = tostring(player.UserId),
        username = player.Name,
        displayName = player.DisplayName
    }):andThen(function(session)
        -- Store session for player
        playerSessions[player] = session
        return session
    end)
end

game.Players.PlayerAdded:Connect(authenticatePlayer)
```

## Core Features

### Lessons Management

#### List Lessons

```lua
client:getLessons({
    grade = 5,
    subject = "math",
    limit = 10
}):andThen(function(lessons)
    for _, lesson in ipairs(lessons) do
        print(lesson.title, lesson.id)
    end
end)
```

#### Get Lesson Details

```lua
client:getLesson(lessonId):andThen(function(lesson)
    print("Lesson:", lesson.title)
    print("Objectives:", table.concat(lesson.objectives, ", "))
    print("Duration:", lesson.duration, "minutes")
end)
```

#### Deploy Lesson to Workspace

```lua
-- Deploy a lesson as 3D environment
client:deployLesson(lessonId, workspace):andThen(function(environment)
    print("Environment deployed:", environment.name)

    -- Setup spawned objects
    for _, object in ipairs(environment.objects) do
        local part = workspace:FindFirstChild(object.name)
        if part then
            -- Add interactive behavior
            local clickDetector = Instance.new("ClickDetector")
            clickDetector.Parent = part
            clickDetector.MouseClick:Connect(function(player)
                client:trackInteraction(player, object.id)
            end)
        end
    end
end)
```

### Quiz System

#### Create Quiz Instance

```lua
local quiz = client:createQuizInstance({
    quizId = "quiz-123",
    position = Vector3.new(0, 10, 0),
    parent = workspace
})

-- Add to workspace
quiz:deploy():andThen(function(quizModel)
    print("Quiz deployed at:", quizModel.PrimaryPart.Position)
end)
```

#### Submit Quiz Answer

```lua
client:submitAnswer({
    quizId = quizId,
    questionId = questionId,
    answer = selectedAnswer,
    playerId = player.UserId,
    timestamp = os.time()
}):andThen(function(result)
    if result.correct then
        -- Award XP
        client:awardXP(player, result.xpEarned)
        -- Visual feedback
        ShowCorrectFeedback(player)
    else
        ShowIncorrectFeedback(player, result.hint)
    end
end)
```

### Progress Tracking

#### Track Player Progress

```lua
-- Track lesson completion
client:trackProgress({
    playerId = player.UserId,
    lessonId = lessonId,
    progress = 100,
    timeSpent = 300, -- seconds
    completedObjectives = { "obj1", "obj2", "obj3" }
}):andThen(function(result)
    print("Progress saved:", result.totalProgress)
end)

-- Track checkpoint
client:saveCheckpoint({
    playerId = player.UserId,
    lessonId = lessonId,
    checkpoint = "section-2",
    position = player.Character.HumanoidRootPart.Position,
    inventory = GetPlayerInventory(player)
})
```

#### Get Player Statistics

```lua
client:getPlayerStats(player.UserId):andThen(function(stats)
    -- Update leaderboard
    local leaderstats = player:FindFirstChild("leaderstats")
    if leaderstats then
        leaderstats.XP.Value = stats.totalXP
        leaderstats.Level.Value = stats.level
        leaderstats.Achievements.Value = #stats.achievements
    end
end)
```

### Gamification

#### Award XP and Achievements

```lua
-- Award XP
client:awardXP(player.UserId, 100, "quiz_completion"):andThen(function(result)
    if result.levelUp then
        -- Player leveled up!
        ShowLevelUpAnimation(player, result.newLevel)
    end
end)

-- Unlock achievement
client:unlockAchievement(player.UserId, "first_lesson"):andThen(function(achievement)
    ShowAchievementNotification(player, achievement)
end)
```

#### Leaderboards

```lua
-- Get leaderboard
client:getLeaderboard({
    type = "weekly_xp",
    limit = 10
}):andThen(function(leaderboard)
    UpdateLeaderboardDisplay(leaderboard.entries)
end)

-- Submit score
client:submitScore({
    playerId = player.UserId,
    score = score,
    leaderboardId = "weekly_challenge"
})
```

## API Reference

### Client Initialization

```lua
ToolBoxAI.new(options: table) -> ToolBoxAIClient

Options:
- apiKey: string (required)
- environment: string = "production"
- baseUrl: string = "https://api.toolboxai.com"
- timeout: number = 30
- retryCount: number = 3
- cacheEnabled: boolean = true
- cacheTTL: number = 300
```

### Lessons API

```lua
-- List lessons
client:getLessons(filters: table) -> Promise<Lesson[]>

-- Get single lesson
client:getLesson(lessonId: string) -> Promise<Lesson>

-- Deploy lesson to workspace
client:deployLesson(lessonId: string, parent: Instance) -> Promise<Environment>

-- Create lesson (Studio only)
client:createLesson(lessonData: table) -> Promise<Lesson>
```

### Quiz API

```lua
-- Get quiz
client:getQuiz(quizId: string) -> Promise<Quiz>

-- Create quiz instance
client:createQuizInstance(options: table) -> QuizInstance

-- Submit answer
client:submitAnswer(data: table) -> Promise<Result>

-- Get quiz results
client:getQuizResults(attemptId: string) -> Promise<QuizResults>
```

### Progress API

```lua
-- Track progress
client:trackProgress(data: table) -> Promise<void>

-- Get progress
client:getProgress(playerId: string, lessonId: string) -> Promise<Progress>

-- Save checkpoint
client:saveCheckpoint(data: table) -> Promise<void>

-- Load checkpoint
client:loadCheckpoint(playerId: string, lessonId: string) -> Promise<Checkpoint>
```

### Gamification API

```lua
-- Award XP
client:awardXP(playerId: string, amount: number, reason: string) -> Promise<XPResult>

-- Get achievements
client:getAchievements(playerId: string) -> Promise<Achievement[]>

-- Unlock achievement
client:unlockAchievement(playerId: string, achievementId: string) -> Promise<Achievement>

-- Get leaderboard
client:getLeaderboard(options: table) -> Promise<Leaderboard>

-- Submit score
client:submitScore(data: table) -> Promise<void>
```

### Analytics API

```lua
-- Track event
client:trackEvent(eventName: string, data: table) -> Promise<void>

-- Track interaction
client:trackInteraction(player: Player, objectId: string) -> Promise<void>

-- Get analytics
client:getAnalytics(filters: table) -> Promise<Analytics>
```

## Roblox-Specific Features

### 3D Environment Generation

```lua
-- Generate environment from lesson
local environmentGenerator = client:createEnvironmentGenerator()

environmentGenerator:generate({
    lesson = lesson,
    theme = "science_lab",
    difficulty = "medium",
    parent = workspace
}):andThen(function(environment)
    -- Environment created with:
    -- - Interactive objects
    -- - NPCs
    -- - Learning stations
    -- - Quiz zones
end)
```

### Interactive Objects

```lua
-- Create interactive learning object
local function createInteractiveObject(objectData)
    local part = Instance.new("Part")
    part.Name = objectData.name
    part.Position = objectData.position
    part.Parent = workspace

    -- Add interaction
    local proximity = Instance.new("ProximityPrompt")
    proximity.ActionText = objectData.action
    proximity.ObjectText = objectData.label
    proximity.Parent = part

    proximity.Triggered:Connect(function(player)
        client:handleInteraction({
            player = player,
            object = objectData,
            action = "examine"
        }):andThen(function(result)
            -- Show educational content
            ShowEducationalUI(player, result.content)
        end)
    end)

    return part
end
```

### NPC Tutors

```lua
-- Create AI tutor NPC
local function createTutorNPC(tutorData)
    local npc = game.ServerStorage.NPCTemplate:Clone()
    npc.Name = tutorData.name
    npc.Parent = workspace

    -- Setup dialog system
    local dialog = Instance.new("Dialog")
    dialog.Parent = npc.Head

    -- Add conversation options
    for _, topic in ipairs(tutorData.topics) do
        local choice = Instance.new("DialogChoice")
        choice.UserDialog = topic.question
        choice.ResponseDialog = topic.answer
        choice.Parent = dialog
    end

    -- Track interactions
    dialog.DialogChoiceSelected:Connect(function(player, choice)
        client:trackTutorInteraction({
            player = player,
            tutor = tutorData.id,
            topic = choice.Name
        })
    end)

    return npc
end
```

### Adaptive Difficulty

```lua
-- Adjust difficulty based on performance
local function adjustDifficulty(player)
    client:getPlayerPerformance(player.UserId):andThen(function(performance)
        local difficulty = "medium"

        if performance.accuracy > 0.9 then
            difficulty = "hard"
        elseif performance.accuracy < 0.6 then
            difficulty = "easy"
        end

        -- Apply difficulty adjustments
        ApplyDifficultySettings(player, difficulty)

        -- Update server
        client:updatePlayerDifficulty(player.UserId, difficulty)
    end)
end
```

## Event System

### Event Subscription

```lua
-- Subscribe to events
client:on("lessonCompleted", function(data)
    print("Lesson completed:", data.lessonId)
    ShowCompletionUI(data.player)
end)

client:on("achievementUnlocked", function(data)
    ShowAchievementNotification(data.achievement)
end)

client:on("levelUp", function(data)
    PlayLevelUpEffect(data.player, data.newLevel)
end)
```

### Custom Events

```lua
-- Fire custom event
client:fireEvent("customEvent", {
    player = player,
    action = "discovered_secret",
    location = "hidden_room"
})

-- Listen for custom events
client:on("customEvent", function(data)
    if data.action == "discovered_secret" then
        client:unlockAchievement(data.player.UserId, "explorer")
    end
end)
```

### Real-time Updates

```lua
-- Connect to real-time updates
client:connectRealtime():andThen(function()
    print("Connected to real-time updates")
end)

-- Listen for real-time events
client:onRealtimeUpdate("quiz_started", function(data)
    NotifyPlayers("Quiz starting in 10 seconds!")
end)

client:onRealtimeUpdate("leaderboard_update", function(data)
    UpdateLeaderboardDisplay(data.leaderboard)
end)
```

## Error Handling

### Promise-based Error Handling

```lua
client:getLesson(lessonId)
    :andThen(function(lesson)
        -- Success
        return client:deployLesson(lesson.id, workspace)
    end)
    :andThen(function(environment)
        print("Environment deployed")
    end)
    :catch(function(error)
        -- Handle error
        if error.code == "NOT_FOUND" then
            warn("Lesson not found")
        elseif error.code == "NETWORK_ERROR" then
            warn("Network error, retrying...")
            -- Retry logic
        else
            warn("Unexpected error:", error.message)
        end
    end)
    :finally(function()
        -- Cleanup
        HideLoadingScreen()
    end)
```

### Error Types

```lua
-- Custom error types
local ErrorTypes = {
    NETWORK_ERROR = "NETWORK_ERROR",
    AUTH_ERROR = "AUTH_ERROR",
    VALIDATION_ERROR = "VALIDATION_ERROR",
    RATE_LIMIT = "RATE_LIMIT",
    NOT_FOUND = "NOT_FOUND",
    SERVER_ERROR = "SERVER_ERROR"
}

-- Error handler
local function handleError(error)
    local handlers = {
        [ErrorTypes.NETWORK_ERROR] = function()
            ShowNetworkErrorUI()
        end,
        [ErrorTypes.AUTH_ERROR] = function()
            RedirectToLogin()
        end,
        [ErrorTypes.RATE_LIMIT] = function()
            wait(error.retryAfter)
            -- Retry
        end
    }

    local handler = handlers[error.code]
    if handler then
        handler()
    else
        warn("Unhandled error:", error)
    end
end
```

## Best Practices

### 1. Security

```lua
-- Never expose API keys in LocalScripts
-- Bad:
local LocalScript = script.Parent
local apiKey = "sk-1234567890" -- NEVER DO THIS

-- Good:
-- Use RemoteEvents/RemoteFunctions to communicate with server
local RemoteEvent = game.ReplicatedStorage.ToolBoxAIRemote

RemoteEvent.OnServerEvent:Connect(function(player, action, data)
    -- Server-side API calls only
    if action == "getLesson" then
        client:getLesson(data.lessonId):andThen(function(lesson)
            RemoteEvent:FireClient(player, "lessonData", lesson)
        end)
    end
end)
```

### 2. Performance

```lua
-- Cache frequently accessed data
local lessonCache = {}
local CACHE_TTL = 300 -- 5 minutes

local function getCachedLesson(lessonId)
    local cached = lessonCache[lessonId]
    if cached and (os.time() - cached.timestamp) < CACHE_TTL then
        return Promise.resolve(cached.data)
    end

    return client:getLesson(lessonId):andThen(function(lesson)
        lessonCache[lessonId] = {
            data = lesson,
            timestamp = os.time()
        }
        return lesson
    end)
end
```

### 3. Memory Management

```lua
-- Clean up when players leave
game.Players.PlayerRemoving:Connect(function(player)
    -- Clean up player data
    playerSessions[player] = nil
    playerProgress[player] = nil

    -- Cancel pending requests
    if playerRequests[player] then
        for _, request in ipairs(playerRequests[player]) do
            request:cancel()
        end
        playerRequests[player] = nil
    end
end)
```

### 4. Rate Limiting

```lua
-- Implement client-side rate limiting
local RateLimiter = {}
RateLimiter.__index = RateLimiter

function RateLimiter.new(maxRequests, timeWindow)
    return setmetatable({
        maxRequests = maxRequests,
        timeWindow = timeWindow,
        requests = {}
    }, RateLimiter)
end

function RateLimiter:canRequest()
    local now = os.time()
    -- Clean old requests
    self.requests = table.filter(self.requests, function(timestamp)
        return (now - timestamp) < self.timeWindow
    end)

    if #self.requests < self.maxRequests then
        table.insert(self.requests, now)
        return true
    end
    return false
end

-- Usage
local limiter = RateLimiter.new(10, 60) -- 10 requests per minute

if limiter:canRequest() then
    client:getLesson(lessonId)
else
    warn("Rate limit exceeded")
end
```

## Examples

### Complete Learning Game Example

```lua
-- Main game script
local ToolBoxAI = require(game.ServerScriptService.ToolBoxAI)
local client = ToolBoxAI.new({ apiKey = getApiKey() })

-- Game state
local gameState = {
    currentLesson = nil,
    activePlayers = {},
    quizInProgress = false
}

-- Initialize game
local function initializeGame()
    -- Load lesson
    client:getLesson("math-fractions-101"):andThen(function(lesson)
        gameState.currentLesson = lesson

        -- Deploy environment
        return client:deployLesson(lesson.id, workspace)
    end):andThen(function(environment)
        -- Setup game mechanics
        SetupLearningStations(environment.stations)
        SetupQuizZones(environment.quizZones)
        SpawnNPCTutors(environment.npcs)

        print("Game initialized successfully")
    end):catch(function(error)
        warn("Failed to initialize game:", error)
    end)
end

-- Player joined
game.Players.PlayerAdded:Connect(function(player)
    -- Authenticate player
    client:authenticateUser({
        robloxId = tostring(player.UserId),
        username = player.Name
    }):andThen(function(session)
        gameState.activePlayers[player] = {
            session = session,
            progress = 0,
            score = 0
        }

        -- Setup player UI
        SetupPlayerUI(player)

        -- Load previous progress
        return client:getProgress(player.UserId, gameState.currentLesson.id)
    end):andThen(function(progress)
        if progress and progress.checkpoint then
            -- Resume from checkpoint
            LoadCheckpoint(player, progress.checkpoint)
        else
            -- Start fresh
            SpawnPlayerAtStart(player)
        end
    end)
end)

-- Learning station interaction
local function onStationInteraction(player, station)
    local playerData = gameState.activePlayers[player]
    if not playerData then return end

    -- Track interaction
    client:trackInteraction(player, station.id)

    -- Show educational content
    ShowEducationalContent(player, station.content)

    -- Award XP for interaction
    client:awardXP(player.UserId, 10, "station_interaction"):andThen(function(result)
        UpdatePlayerXP(player, result.totalXP)

        if result.levelUp then
            ShowLevelUpEffect(player, result.newLevel)
        end
    end)
end

-- Quiz completion
local function onQuizComplete(player, quizId, score)
    client:submitQuizResults({
        playerId = player.UserId,
        quizId = quizId,
        score = score,
        answers = GetPlayerAnswers(player)
    }):andThen(function(results)
        -- Show results
        ShowQuizResults(player, results)

        -- Award achievements
        if results.perfectScore then
            client:unlockAchievement(player.UserId, "perfect_quiz")
        end

        -- Update leaderboard
        return client:submitScore({
            playerId = player.UserId,
            score = score,
            leaderboardId = "daily_quiz"
        })
    end):andThen(function()
        -- Refresh leaderboard display
        RefreshLeaderboard()
    end)
end

-- Start game
initializeGame()
```

### Studio Plugin Example

```lua
-- ToolBoxAI Studio Plugin
local toolbar = plugin:CreateToolbar("ToolBoxAI Education")
local ToolBoxAI = require(game.ServerScriptService.ToolBoxAI)

-- Create buttons
local deployButton = toolbar:CreateButton(
    "Deploy Lesson",
    "Deploy a lesson to workspace",
    "rbxasset://textures/ui/Settings/Help/PreviewIcon.png"
)

local syncButton = toolbar:CreateButton(
    "Sync Content",
    "Sync with ToolBoxAI platform",
    "rbxasset://textures/ui/Refresh.png"
)

-- Plugin state
local pluginState = {
    apiKey = plugin:GetSetting("ToolBoxAIApiKey"),
    selectedLesson = nil,
    client = nil
}

-- Initialize client
if pluginState.apiKey then
    pluginState.client = ToolBoxAI.new({ apiKey = pluginState.apiKey })
end

-- Deploy button clicked
deployButton.Click:Connect(function()
    if not pluginState.client then
        -- Prompt for API key
        local apiKey = PromptForApiKey()
        plugin:SetSetting("ToolBoxAIApiKey", apiKey)
        pluginState.client = ToolBoxAI.new({ apiKey = apiKey })
    end

    -- Show lesson selector
    ShowLessonSelector(function(lessonId)
        -- Deploy selected lesson
        pluginState.client:deployLesson(lessonId, workspace):andThen(function(environment)
            print("Lesson deployed:", environment.name)

            -- Select deployed models
            game.Selection:Set(environment.objects)
        end):catch(function(error)
            warn("Deployment failed:", error)
        end)
    end)
end)

-- Sync button clicked
syncButton.Click:Connect(function()
    if not pluginState.client then
        warn("Please configure API key first")
        return
    end

    -- Sync local changes with platform
    local changes = DetectLocalChanges()

    pluginState.client:syncChanges(changes):andThen(function(result)
        print("Sync complete:", result.message)
    end):catch(function(error)
        warn("Sync failed:", error)
    end)
end)
```

## Studio Plugin Development

### Plugin Architecture

```lua
-- Plugin structure
local Plugin = {
    toolbar = nil,
    widgets = {},
    client = nil,
    settings = {},
    activeDeployments = {}
}

-- Initialize plugin
function Plugin:init()
    self.toolbar = plugin:CreateToolbar("ToolBoxAI")
    self:loadSettings()
    self:createUI()
    self:connectEvents()

    if self.settings.apiKey then
        self.client = ToolBoxAI.new({ apiKey = self.settings.apiKey })
    end
end

-- Create UI
function Plugin:createUI()
    -- Main widget
    self.widgets.main = plugin:CreateDockWidgetPluginGui(
        "ToolBoxAIMain",
        DockWidgetPluginGuiInfo.new(
            Enum.InitialDockState.Left,
            false, -- enabled
            false, -- override previous enabled state
            300,   -- width
            500,   -- height
            250,   -- min width
            200    -- min height
        )
    )

    self.widgets.main.Title = "ToolBoxAI Education"

    -- Add UI components
    self:createLessonBrowser()
    self:createDeploymentPanel()
    self:createSettingsPanel()
end
```

### Lesson Browser

```lua
-- Browse and search lessons
function Plugin:createLessonBrowser()
    local browser = Instance.new("Frame")
    browser.Size = UDim2.new(1, 0, 0.5, 0)
    browser.Parent = self.widgets.main

    -- Search bar
    local searchBar = Instance.new("TextBox")
    searchBar.PlaceholderText = "Search lessons..."
    searchBar.Parent = browser

    -- Results list
    local resultsList = Instance.new("ScrollingFrame")
    resultsList.Parent = browser

    -- Search functionality
    searchBar.FocusLost:Connect(function()
        if searchBar.Text ~= "" then
            self:searchLessons(searchBar.Text)
        end
    end)
end

function Plugin:searchLessons(query)
    self.client:searchLessons({
        query = query,
        limit = 20
    }):andThen(function(results)
        self:displaySearchResults(results)
    end)
end
```

### Deployment Panel

```lua
-- Deploy and manage lessons
function Plugin:createDeploymentPanel()
    local panel = Instance.new("Frame")
    panel.Size = UDim2.new(1, 0, 0.5, 0)
    panel.Position = UDim2.new(0, 0, 0.5, 0)
    panel.Parent = self.widgets.main

    -- Deploy button
    local deployBtn = Instance.new("TextButton")
    deployBtn.Text = "Deploy to Workspace"
    deployBtn.Parent = panel

    deployBtn.MouseButton1Click:Connect(function()
        if self.selectedLesson then
            self:deployLesson(self.selectedLesson)
        end
    end)

    -- Options
    local options = {
        includeScripts = true,
        includeModels = true,
        includeUI = true,
        targetLocation = workspace
    }

    -- Create option checkboxes
    for optionName, defaultValue in pairs(options) do
        local checkbox = self:createCheckbox(optionName, defaultValue)
        checkbox.Parent = panel
    end
end

function Plugin:deployLesson(lesson)
    -- Show progress
    local progressBar = self:createProgressBar()

    self.client:deployLesson(lesson.id, workspace, {
        onProgress = function(progress)
            progressBar:Update(progress)
        end
    }):andThen(function(deployment)
        -- Track deployment
        table.insert(self.activeDeployments, deployment)

        -- Select deployed objects
        game.Selection:Set(deployment.objects)

        -- Show success
        self:showNotification("Lesson deployed successfully!")
    end):catch(function(error)
        self:showError("Deployment failed: " .. error.message)
    end)
end
```

## Performance Optimization

### Batching Requests

```lua
-- Batch multiple API calls
local BatchProcessor = {}
BatchProcessor.__index = BatchProcessor

function BatchProcessor.new(client, batchSize, delay)
    return setmetatable({
        client = client,
        batchSize = batchSize or 10,
        delay = delay or 0.1,
        queue = {},
        processing = false
    }, BatchProcessor)
end

function BatchProcessor:add(request)
    table.insert(self.queue, request)

    if not self.processing then
        self:processBatch()
    end
end

function BatchProcessor:processBatch()
    self.processing = true

    spawn(function()
        while #self.queue > 0 do
            local batch = {}
            for i = 1, math.min(self.batchSize, #self.queue) do
                table.insert(batch, table.remove(self.queue, 1))
            end

            -- Process batch
            self.client:processBatch(batch):andThen(function(results)
                -- Handle results
                for i, result in ipairs(results) do
                    batch[i].callback(result)
                end
            end)

            wait(self.delay)
        end

        self.processing = false
    end)
end

-- Usage
local batcher = BatchProcessor.new(client, 10, 0.1)

for _, player in ipairs(game.Players:GetPlayers()) do
    batcher:add({
        type = "getProgress",
        data = { playerId = player.UserId },
        callback = function(progress)
            UpdatePlayerProgress(player, progress)
        end
    })
end
```

### Caching Strategy

```lua
-- Multi-level cache
local Cache = {}
Cache.__index = Cache

function Cache.new(ttl)
    return setmetatable({
        memory = {},      -- In-memory cache
        ttl = ttl or 300  -- 5 minutes default
    }, Cache)
end

function Cache:get(key)
    local entry = self.memory[key]
    if entry and (os.time() - entry.timestamp) < self.ttl then
        return entry.value
    end
    return nil
end

function Cache:set(key, value)
    self.memory[key] = {
        value = value,
        timestamp = os.time()
    }
end

function Cache:invalidate(pattern)
    for key in pairs(self.memory) do
        if string.match(key, pattern) then
            self.memory[key] = nil
        end
    end
end

-- Global cache instance
local globalCache = Cache.new(300)

-- Cached API calls
local function getCachedLesson(lessonId)
    local cached = globalCache:get("lesson:" .. lessonId)
    if cached then
        return Promise.resolve(cached)
    end

    return client:getLesson(lessonId):andThen(function(lesson)
        globalCache:set("lesson:" .. lessonId, lesson)
        return lesson
    end)
end
```

### Memory Management

```lua
-- Memory-aware object pooling
local ObjectPool = {}
ObjectPool.__index = ObjectPool

function ObjectPool.new(createFunc, resetFunc, maxSize)
    return setmetatable({
        createFunc = createFunc,
        resetFunc = resetFunc,
        maxSize = maxSize or 100,
        available = {},
        inUse = {}
    }, ObjectPool)
end

function ObjectPool:acquire()
    local obj = table.remove(self.available)

    if not obj then
        if #self.inUse < self.maxSize then
            obj = self.createFunc()
        else
            -- Wait for available object
            repeat
                wait(0.1)
                obj = table.remove(self.available)
            until obj
        end
    end

    table.insert(self.inUse, obj)
    return obj
end

function ObjectPool:release(obj)
    local index = table.find(self.inUse, obj)
    if index then
        table.remove(self.inUse, index)
        self.resetFunc(obj)
        table.insert(self.available, obj)
    end
end

-- Usage for quiz UI elements
local quizUIPool = ObjectPool.new(
    function() return CreateQuizUI() end,
    function(ui) ResetQuizUI(ui) end,
    10
)
```

## Security

### API Key Management

```lua
-- Secure API key storage
local SecurityManager = {}

function SecurityManager.getApiKey()
    -- For Studio plugins
    if plugin then
        return plugin:GetSetting("ToolBoxAIApiKey")
    end

    -- For server scripts
    local ServerStorage = game:GetService("ServerStorage")
    local configModule = ServerStorage:FindFirstChild("APIConfig")

    if configModule then
        local config = require(configModule)
        return config.TOOLBOXAI_API_KEY
    end

    error("API key not configured")
end

-- Never expose to clients
local function isServerContext()
    return game:GetService("RunService"):IsServer()
end

if not isServerContext() then
    error("ToolBoxAI SDK can only be used on the server")
end
```

### Input Validation

```lua
-- Validate and sanitize inputs
local Validator = {}

function Validator.validateLessonId(id)
    if type(id) ~= "string" then
        error("Lesson ID must be a string")
    end

    if not string.match(id, "^[a-zA-Z0-9%-]+$") then
        error("Invalid lesson ID format")
    end

    return true
end

function Validator.sanitizeUserInput(input)
    -- Remove potentially harmful characters
    input = string.gsub(input, "[<>\"']", "")

    -- Limit length
    if #input > 1000 then
        input = string.sub(input, 1, 1000)
    end

    return input
end

-- Use in API calls
local function safeGetLesson(lessonId)
    Validator.validateLessonId(lessonId)
    return client:getLesson(lessonId)
end
```

### Rate Limiting Protection

```lua
-- Protect against abuse
local RateLimitProtection = {}
RateLimitProtection.limits = {}

function RateLimitProtection.check(player, action)
    local key = tostring(player.UserId) .. ":" .. action
    local now = os.time()

    if not RateLimitProtection.limits[key] then
        RateLimitProtection.limits[key] = {
            count = 0,
            resetTime = now + 60
        }
    end

    local limit = RateLimitProtection.limits[key]

    if now > limit.resetTime then
        limit.count = 0
        limit.resetTime = now + 60
    end

    if limit.count >= 10 then -- 10 requests per minute
        return false, "Rate limit exceeded"
    end

    limit.count = limit.count + 1
    return true
end

-- Apply to remote events
game.ReplicatedStorage.RemoteEvent.OnServerEvent:Connect(function(player, action, data)
    local allowed, reason = RateLimitProtection.check(player, action)

    if not allowed then
        warn("Rate limit exceeded for", player.Name, "-", reason)
        return
    end

    -- Process request
end)
```

## Troubleshooting

### Common Issues

#### Connection Issues

```lua
-- Problem: Cannot connect to API
-- Solution: Check network and retry with backoff

local function connectWithRetry(maxAttempts)
    local attempts = 0

    local function attempt()
        attempts = attempts + 1

        return client:testConnection():catch(function(error)
            if attempts < maxAttempts then
                local delay = math.pow(2, attempts) -- Exponential backoff
                wait(delay)
                return attempt()
            else
                error("Failed to connect after " .. maxAttempts .. " attempts")
            end
        end)
    end

    return attempt()
end
```

#### Memory Leaks

```lua
-- Problem: Memory usage increases over time
-- Solution: Proper cleanup and connection management

local connections = {}

local function trackConnection(connection)
    table.insert(connections, connection)
    return connection
end

local function cleanupConnections()
    for _, connection in ipairs(connections) do
        connection:Disconnect()
    end
    connections = {}
end

-- Clean up on shutdown
game:BindToClose(function()
    cleanupConnections()
    -- Other cleanup
end)
```

#### Studio Plugin Issues

```lua
-- Problem: Plugin doesn't load
-- Solution: Check for errors and validate setup

local function debugPlugin()
    -- Check if running in Studio
    if not plugin then
        error("Not running as a plugin")
    end

    -- Check permissions
    local success, result = pcall(function()
        return plugin:GetSetting("test")
    end)

    if not success then
        error("Plugin doesn't have settings permission")
    end

    -- Check HTTP service
    local HttpService = game:GetService("HttpService")
    if not HttpService.HttpEnabled then
        error("HTTP requests are not enabled")
    end

    print("Plugin environment OK")
end
```

### Debug Mode

```lua
-- Enable debug logging
local DEBUG = true

local function debugLog(...)
    if DEBUG then
        print("[ToolBoxAI Debug]", ...)
    end
end

-- Add to client
client.debug = true
client:on("debug", function(message)
    debugLog(message)
end)
```

### Performance Profiling

```lua
-- Profile API calls
local Profiler = {}
Profiler.calls = {}

function Profiler:start(name)
    self.calls[name] = {
        startTime = tick(),
        count = (self.calls[name] and self.calls[name].count or 0) + 1
    }
end

function Profiler:stop(name)
    if self.calls[name] then
        local duration = tick() - self.calls[name].startTime
        self.calls[name].totalTime = (self.calls[name].totalTime or 0) + duration
        self.calls[name].avgTime = self.calls[name].totalTime / self.calls[name].count
    end
end

function Profiler:report()
    for name, data in pairs(self.calls) do
        print(string.format("%s: %d calls, avg %.2fms",
            name, data.count, data.avgTime * 1000))
    end
end

-- Usage
Profiler:start("getLesson")
client:getLesson(lessonId):finally(function()
    Profiler:stop("getLesson")
end)
```

## Migration Guide

### From Version 0.x to 1.0

```lua
-- Old API (deprecated)
local lesson = client:fetchLesson(lessonId) -- Synchronous

-- New API (current)
client:getLesson(lessonId):andThen(function(lesson)
    -- Handle lesson
end) -- Promise-based

-- Migration helper
local function migrateOldCode()
    -- Add compatibility layer
    client.fetchLesson = function(self, lessonId)
        local result = nil
        self:getLesson(lessonId):andThen(function(lesson)
            result = lesson
        end):await()
        return result
    end
end
```

## Support and Resources

### Documentation

- [API Reference](https://docs.toolboxai.com/api)
- [Roblox Integration Guide](https://docs.toolboxai.com/roblox)
- [Examples Repository](https://github.com/toolboxai/roblox-examples)

### Community

- Discord: [discord.gg/toolboxai](https://discord.gg/toolboxai)
- Forum: [forum.toolboxai.com/roblox](https://forum.toolboxai.com/roblox)
- GitHub: [github.com/toolboxai/roblox-sdk](https://github.com/toolboxai/roblox-sdk)

### Getting Help

```lua
-- Built-in help system
client:help("deployLesson")
-- Returns documentation for the method

-- Version information
print(ToolBoxAI.VERSION) -- "1.0.0"
print(ToolBoxAI.API_VERSION) -- "v1"

-- Diagnostic information
client:getDiagnostics():andThen(function(diagnostics)
    print("SDK Version:", diagnostics.sdkVersion)
    print("API Status:", diagnostics.apiStatus)
    print("Latency:", diagnostics.latency, "ms")
end)
```

---

_ToolBoxAI Roblox Lua SDK - Bringing education to life in 3D_

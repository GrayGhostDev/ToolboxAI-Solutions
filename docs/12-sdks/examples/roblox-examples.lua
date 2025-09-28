--[[
    ToolBoxAI Roblox Lua SDK Examples
    Complete examples demonstrating SDK usage in Roblox Studio
]]

-- ============================================
-- SETUP AND INITIALIZATION
-- ============================================

-- Load the SDK
local ServerScriptService = game:GetService("ServerScriptService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local ToolBoxAI = require(ServerScriptService.ToolBoxAI)

-- Initialize client with API key
local client = ToolBoxAI.new({
    apiKey = "your-api-key-here", -- Store securely in ServerStorage
    environment = "production",
    baseUrl = "https://api.toolboxai.com",
    timeout = 30,
    retryCount = 3
})

-- Test connection
client:testConnection():andThen(function(result)
    print("Connected to ToolBoxAI:", result.message)
end):catch(function(error)
    warn("Connection failed:", error.message)
end)

-- ============================================
-- LESSON DEPLOYMENT EXAMPLE
-- ============================================

local function deployLessonExample()
    local lessonId = "math-fractions-101"
    
    -- Get lesson details
    client:getLesson(lessonId):andThen(function(lesson)
        print("Deploying lesson:", lesson.title)
        
        -- Deploy to workspace
        return client:deployLesson(lesson.id, workspace)
    end):andThen(function(environment)
        print("Environment deployed successfully")
        
        -- Setup interactive objects
        for _, objectData in ipairs(environment.objects) do
            local part = workspace:FindFirstChild(objectData.name)
            if part then
                setupInteractiveObject(part, objectData)
            end
        end
        
        -- Spawn NPCs
        for _, npcData in ipairs(environment.npcs) do
            spawnEducationalNPC(npcData)
        end
        
        -- Create quiz zones
        for _, quizZone in ipairs(environment.quizZones) do
            createQuizZone(quizZone)
        end
        
    end):catch(function(error)
        warn("Deployment failed:", error.message)
    end)
end

-- ============================================
-- INTERACTIVE OBJECTS
-- ============================================

local function setupInteractiveObject(part, objectData)
    -- Add ProximityPrompt for interaction
    local prompt = Instance.new("ProximityPrompt")
    prompt.ActionText = objectData.action or "Examine"
    prompt.ObjectText = objectData.label
    prompt.HoldDuration = objectData.holdDuration or 0
    prompt.RequiresLineOfSight = false
    prompt.Parent = part
    
    -- Add visual indicator
    local highlight = Instance.new("Highlight")
    highlight.FillColor = Color3.fromRGB(100, 200, 255)
    highlight.FillTransparency = 0.8
    highlight.OutlineColor = Color3.fromRGB(50, 150, 255)
    highlight.Parent = part
    highlight.Enabled = false
    
    -- Handle interactions
    prompt.Triggered:Connect(function(player)
        -- Track interaction
        client:trackInteraction(player, objectData.id)
        
        -- Get educational content
        client:getObjectContent(objectData.id):andThen(function(content)
            -- Show educational UI
            showEducationalContent(player, content)
            
            -- Award XP for interaction
            return client:awardXP(player.UserId, 10, "object_interaction")
        end):andThen(function(xpResult)
            if xpResult.levelUp then
                showLevelUpEffect(player, xpResult.newLevel)
            end
        end)
    end)
    
    -- Hover effects
    prompt.PromptShown:Connect(function()
        highlight.Enabled = true
    end)
    
    prompt.PromptHidden:Connect(function()
        highlight.Enabled = false
    end)
end

-- ============================================
-- EDUCATIONAL NPC SYSTEM
-- ============================================

local function spawnEducationalNPC(npcData)
    -- Clone NPC model from storage
    local ServerStorage = game:GetService("ServerStorage")
    local npcTemplate = ServerStorage:FindFirstChild("NPCTemplate")
    if not npcTemplate then
        warn("NPC template not found")
        return
    end
    
    local npc = npcTemplate:Clone()
    npc.Name = npcData.name
    npc:SetPrimaryPartCFrame(CFrame.new(npcData.position))
    npc.Parent = workspace
    
    -- Setup dialog
    local head = npc:FindFirstChild("Head")
    if head then
        local dialog = Instance.new("Dialog")
        dialog.InitialPrompt = npcData.greeting or "Hello! How can I help you learn today?"
        dialog.GoodbyeMessage = "Keep up the great work!"
        dialog.Parent = head
        
        -- Add conversation topics
        for _, topic in ipairs(npcData.topics) do
            local choice = Instance.new("DialogChoice")
            choice.UserDialog = topic.question
            choice.ResponseDialog = topic.answer
            choice.Parent = dialog
            
            -- Add sub-topics if available
            if topic.subTopics then
                for _, subTopic in ipairs(topic.subTopics) do
                    local subChoice = Instance.new("DialogChoice")
                    subChoice.UserDialog = subTopic.question
                    subChoice.ResponseDialog = subTopic.answer
                    subChoice.Parent = choice
                end
            end
        end
        
        -- Track NPC interactions
        dialog.DialogChoiceSelected:Connect(function(player, choice)
            client:trackTutorInteraction({
                player = player,
                tutor = npcData.id,
                topic = choice.Name,
                timestamp = os.time()
            })
        end)
    end
    
    -- Add AI behavior
    spawn(function()
        while npc.Parent do
            -- Simple patrol behavior
            local humanoid = npc:FindFirstChildOfClass("Humanoid")
            if humanoid then
                for _, waypoint in ipairs(npcData.waypoints or {}) do
                    humanoid:MoveTo(waypoint)
                    humanoid.MoveToFinished:Wait()
                    wait(2) -- Pause at each waypoint
                end
            end
            wait(1)
        end
    end)
end

-- ============================================
-- QUIZ ZONE SYSTEM
-- ============================================

local function createQuizZone(zoneData)
    -- Create quiz trigger zone
    local zone = Instance.new("Part")
    zone.Name = "QuizZone_" .. zoneData.id
    zone.Size = zoneData.size or Vector3.new(20, 10, 20)
    zone.Position = zoneData.position
    zone.Transparency = 0.8
    zone.BrickColor = BrickColor.new("Lime green")
    zone.CanCollide = false
    zone.Anchored = true
    zone.Parent = workspace
    
    -- Visual indicator
    local selectionBox = Instance.new("SelectionBox")
    selectionBox.Adornee = zone
    selectionBox.Color3 = Color3.fromRGB(0, 255, 0)
    selectionBox.LineThickness = 0.1
    selectionBox.Transparency = 0.5
    selectionBox.Parent = zone
    
    -- Track players in zone
    local playersInZone = {}
    
    zone.Touched:Connect(function(hit)
        local humanoid = hit.Parent:FindFirstChildOfClass("Humanoid")
        if humanoid then
            local player = Players:GetPlayerFromCharacter(hit.Parent)
            if player and not playersInZone[player] then
                playersInZone[player] = true
                onPlayerEnterQuizZone(player, zoneData)
            end
        end
    end)
    
    zone.TouchEnded:Connect(function(hit)
        local humanoid = hit.Parent:FindFirstChildOfClass("Humanoid")
        if humanoid then
            local player = Players:GetPlayerFromCharacter(hit.Parent)
            if player and playersInZone[player] then
                playersInZone[player] = nil
                onPlayerExitQuizZone(player, zoneData)
            end
        end
    end)
end

local function onPlayerEnterQuizZone(player, zoneData)
    -- Show quiz prompt
    local promptGui = createQuizPromptGui(zoneData)
    promptGui.Parent = player.PlayerGui
    
    -- Start quiz when accepted
    local startButton = promptGui:FindFirstChild("StartButton", true)
    if startButton then
        startButton.MouseButton1Click:Connect(function()
            startQuiz(player, zoneData.quizId)
            promptGui:Destroy()
        end)
    end
end

local function onPlayerExitQuizZone(player, zoneData)
    -- Remove quiz prompt if exists
    local playerGui = player:FindFirstChild("PlayerGui")
    if playerGui then
        local prompt = playerGui:FindFirstChild("QuizPrompt")
        if prompt then
            prompt:Destroy()
        end
    end
end

-- ============================================
-- QUIZ SYSTEM
-- ============================================

local function startQuiz(player, quizId)
    -- Get quiz from API
    client:getQuiz(quizId):andThen(function(quiz)
        -- Create quiz UI
        local quizGui = createQuizGui(quiz)
        quizGui.Parent = player.PlayerGui
        
        -- Track quiz start
        return client:startQuizAttempt({
            quizId = quiz.id,
            playerId = player.UserId,
            timestamp = os.time()
        })
    end):andThen(function(attempt)
        -- Store attempt ID for submission
        player:SetAttribute("CurrentQuizAttempt", attempt.id)
        
        -- Start timer if time limit exists
        if attempt.timeLimit then
            startQuizTimer(player, attempt.timeLimit)
        end
    end):catch(function(error)
        warn("Failed to start quiz:", error.message)
    end)
end

local function submitQuizAnswer(player, questionId, answer)
    local attemptId = player:GetAttribute("CurrentQuizAttempt")
    if not attemptId then
        warn("No active quiz attempt")
        return
    end
    
    client:submitAnswer({
        attemptId = attemptId,
        questionId = questionId,
        answer = answer,
        playerId = player.UserId,
        timestamp = os.time()
    }):andThen(function(result)
        -- Show immediate feedback
        if result.correct then
            showCorrectFeedback(player, result.explanation)
            -- Award XP for correct answer
            return client:awardXP(player.UserId, result.points, "quiz_correct")
        else
            showIncorrectFeedback(player, result.hint)
        end
    end):andThen(function(xpResult)
        if xpResult and xpResult.levelUp then
            showLevelUpEffect(player, xpResult.newLevel)
        end
    end)
end

local function completeQuiz(player)
    local attemptId = player:GetAttribute("CurrentQuizAttempt")
    if not attemptId then return end
    
    client:completeQuizAttempt(attemptId):andThen(function(results)
        -- Show results screen
        showQuizResults(player, results)
        
        -- Check for achievements
        if results.perfectScore then
            return client:unlockAchievement(player.UserId, "perfect_quiz")
        elseif results.score >= 90 then
            return client:unlockAchievement(player.UserId, "quiz_master")
        end
    end):andThen(function(achievement)
        if achievement then
            showAchievementUnlocked(player, achievement)
        end
    end):finally(function()
        -- Clean up
        player:SetAttribute("CurrentQuizAttempt", nil)
    end)
end

-- ============================================
-- PROGRESS TRACKING
-- ============================================

local function trackPlayerProgress()
    -- Track progress for all players periodically
    RunService.Heartbeat:Connect(function()
        for _, player in ipairs(Players:GetPlayers()) do
            if player.Character then
                local humanoid = player.Character:FindFirstChildOfClass("Humanoid")
                if humanoid and humanoid.Health > 0 then
                    -- Track position for checkpoints
                    local position = player.Character.HumanoidRootPart.Position
                    
                    -- Update progress every 30 seconds
                    if tick() - (player:GetAttribute("LastProgressUpdate") or 0) > 30 then
                        player:SetAttribute("LastProgressUpdate", tick())
                        
                        client:updateProgress({
                            playerId = player.UserId,
                            lessonId = getCurrentLessonId(),
                            position = {position.X, position.Y, position.Z},
                            timeSpent = tick() - (player:GetAttribute("SessionStart") or tick())
                        })
                    end
                end
            end
        end
    end)
end

-- Player joined handler
Players.PlayerAdded:Connect(function(player)
    print(player.Name .. " joined the game")
    
    -- Set session start time
    player:SetAttribute("SessionStart", tick())
    
    -- Authenticate player
    client:authenticateUser({
        robloxId = tostring(player.UserId),
        username = player.Name,
        displayName = player.DisplayName
    }):andThen(function(session)
        print("Player authenticated:", session.sessionId)
        
        -- Load player progress
        return client:getProgress(player.UserId, getCurrentLessonId())
    end):andThen(function(progress)
        -- Setup player based on progress
        if progress and progress.checkpoint then
            loadPlayerCheckpoint(player, progress.checkpoint)
        else
            spawnPlayerAtStart(player)
        end
        
        -- Setup leaderboard
        setupPlayerLeaderstats(player, progress)
    end):catch(function(error)
        warn("Failed to authenticate player:", error.message)
    end)
end)

-- Player leaving handler
Players.PlayerRemoving:Connect(function(player)
    -- Save final progress
    client:saveCheckpoint({
        playerId = player.UserId,
        lessonId = getCurrentLessonId(),
        checkpoint = createCheckpoint(player),
        timestamp = os.time()
    }):andThen(function()
        print("Progress saved for", player.Name)
    end)
end)

-- ============================================
-- GAMIFICATION
-- ============================================

local function setupPlayerLeaderstats(player, progress)
    local leaderstats = Instance.new("Folder")
    leaderstats.Name = "leaderstats"
    leaderstats.Parent = player
    
    local xp = Instance.new("IntValue")
    xp.Name = "XP"
    xp.Value = progress and progress.totalXP or 0
    xp.Parent = leaderstats
    
    local level = Instance.new("IntValue")
    level.Name = "Level"
    level.Value = progress and progress.level or 1
    level.Parent = leaderstats
    
    local streak = Instance.new("IntValue")
    streak.Name = "Streak"
    streak.Value = progress and progress.streakDays or 0
    streak.Parent = leaderstats
    
    local achievements = Instance.new("IntValue")
    achievements.Name = "Achievements"
    achievements.Value = progress and #progress.achievements or 0
    achievements.Parent = leaderstats
end

local function showLevelUpEffect(player, newLevel)
    -- Create level up particle effect
    local character = player.Character
    if not character then return end
    
    local humanoidRootPart = character:FindFirstChild("HumanoidRootPart")
    if not humanoidRootPart then return end
    
    -- Create particle emitter
    local particle = Instance.new("ParticleEmitter")
    particle.Texture = "rbxasset://textures/particles/sparkles_main.dds"
    particle.Rate = 100
    particle.Lifetime = NumberRange.new(1, 2)
    particle.VelocitySpread = 360
    particle.Speed = NumberRange.new(5, 10)
    particle.Parent = humanoidRootPart
    
    -- Sound effect
    local sound = Instance.new("Sound")
    sound.SoundId = "rbxassetid://131961136" -- Level up sound
    sound.Volume = 0.5
    sound.Parent = humanoidRootPart
    sound:Play()
    
    -- GUI notification
    showNotification(player, "LEVEL UP! You are now level " .. newLevel)
    
    -- Clean up after 3 seconds
    wait(3)
    particle:Destroy()
    sound:Destroy()
end

local function showAchievementUnlocked(player, achievement)
    -- Create achievement notification GUI
    local gui = Instance.new("ScreenGui")
    gui.Name = "AchievementNotification"
    gui.ResetOnSpawn = false
    gui.Parent = player.PlayerGui
    
    local frame = Instance.new("Frame")
    frame.Size = UDim2.new(0, 400, 0, 100)
    frame.Position = UDim2.new(0.5, -200, 0, -100)
    frame.BackgroundColor3 = Color3.fromRGB(50, 50, 50)
    frame.BorderSizePixel = 0
    frame.Parent = gui
    
    local icon = Instance.new("ImageLabel")
    icon.Size = UDim2.new(0, 80, 0, 80)
    icon.Position = UDim2.new(0, 10, 0, 10)
    icon.Image = achievement.icon or "rbxassetid://4458901886"
    icon.BackgroundTransparency = 1
    icon.Parent = frame
    
    local title = Instance.new("TextLabel")
    title.Size = UDim2.new(0, 300, 0, 30)
    title.Position = UDim2.new(0, 100, 0, 10)
    title.Text = "Achievement Unlocked!"
    title.TextColor3 = Color3.fromRGB(255, 215, 0)
    title.TextScaled = true
    title.BackgroundTransparency = 1
    title.Parent = frame
    
    local desc = Instance.new("TextLabel")
    desc.Size = UDim2.new(0, 300, 0, 50)
    desc.Position = UDim2.new(0, 100, 0, 40)
    desc.Text = achievement.title
    desc.TextColor3 = Color3.fromRGB(255, 255, 255)
    desc.TextScaled = true
    desc.BackgroundTransparency = 1
    desc.Parent = frame
    
    -- Animate in
    frame:TweenPosition(
        UDim2.new(0.5, -200, 0, 50),
        Enum.EasingDirection.Out,
        Enum.EasingStyle.Back,
        0.5,
        true
    )
    
    -- Remove after 5 seconds
    wait(5)
    frame:TweenPosition(
        UDim2.new(0.5, -200, 0, -100),
        Enum.EasingDirection.In,
        Enum.EasingStyle.Back,
        0.5,
        true,
        function()
            gui:Destroy()
        end
    )
end

-- ============================================
-- LEADERBOARDS
-- ============================================

local function updateLeaderboards()
    -- Update leaderboards every minute
    while true do
        wait(60)
        
        -- Get weekly XP leaderboard
        client:getLeaderboard({
            type = "weekly_xp",
            limit = 10
        }):andThen(function(leaderboard)
            updateLeaderboardDisplay("WeeklyXP", leaderboard.entries)
        end)
        
        -- Get achievement leaderboard
        client:getLeaderboard({
            type = "achievements",
            limit = 10
        }):andThen(function(leaderboard)
            updateLeaderboardDisplay("Achievements", leaderboard.entries)
        end)
    end
end

local function updateLeaderboardDisplay(leaderboardName, entries)
    -- Find or create leaderboard display
    local leaderboard = workspace:FindFirstChild("Leaderboard_" .. leaderboardName)
    if not leaderboard then
        -- Create leaderboard display model
        leaderboard = createLeaderboardDisplay(leaderboardName)
    end
    
    -- Update entries
    for i, entry in ipairs(entries) do
        local slot = leaderboard:FindFirstChild("Slot" .. i)
        if slot then
            local nameLabel = slot:FindFirstChild("NameLabel")
            local scoreLabel = slot:FindFirstChild("ScoreLabel")
            
            if nameLabel then
                nameLabel.Text = entry.username
            end
            if scoreLabel then
                scoreLabel.Text = tostring(entry.score)
            end
        end
    end
end

-- ============================================
-- REAL-TIME COLLABORATION
-- ============================================

local function setupRealtimeCollaboration()
    -- Create remote events for real-time updates
    local remoteEvents = Instance.new("Folder")
    remoteEvents.Name = "ToolBoxAIEvents"
    remoteEvents.Parent = ReplicatedStorage
    
    local quizStarted = Instance.new("RemoteEvent")
    quizStarted.Name = "QuizStarted"
    quizStarted.Parent = remoteEvents
    
    local progressUpdate = Instance.new("RemoteEvent")
    progressUpdate.Name = "ProgressUpdate"
    progressUpdate.Parent = remoteEvents
    
    local achievementEarned = Instance.new("RemoteEvent")
    achievementEarned.Name = "AchievementEarned"
    achievementEarned.Parent = remoteEvents
    
    -- Teacher controls (if player is teacher)
    local function setupTeacherControls(player)
        if not isTeacher(player) then return end
        
        -- Give teacher a control panel
        local controlPanel = createTeacherControlPanel()
        controlPanel.Parent = player.PlayerGui
        
        -- Start quiz for all students
        local startQuizButton = controlPanel:FindFirstChild("StartQuizButton", true)
        if startQuizButton then
            startQuizButton.MouseButton1Click:Connect(function()
                quizStarted:FireAllClients({
                    quizId = "quiz-123",
                    timeLimit = 600
                })
            end)
        end
    end
end

-- ============================================
-- STUDIO PLUGIN INTEGRATION
-- ============================================

-- Check if running in Studio with plugin
if plugin then
    local toolbar = plugin:CreateToolbar("ToolBoxAI Education")
    
    -- Deploy Lesson button
    local deployButton = toolbar:CreateButton(
        "Deploy Lesson",
        "Deploy a lesson to workspace",
        "rbxasset://textures/ui/Settings/Help/PreviewIcon.png"
    )
    
    deployButton.Click:Connect(function()
        -- Get API key from plugin settings
        local apiKey = plugin:GetSetting("ToolBoxAIApiKey")
        
        if not apiKey then
            -- Prompt for API key
            warn("Please set your ToolBoxAI API key in plugin settings")
            return
        end
        
        -- Initialize plugin client
        local pluginClient = ToolBoxAI.new({ apiKey = apiKey })
        
        -- Show lesson selector widget
        local widget = plugin:CreateDockWidgetPluginGui(
            "ToolBoxAILessonSelector",
            DockWidgetPluginGuiInfo.new(
                Enum.InitialDockState.Float,
                false,
                false,
                300,
                400,
                250,
                300
            )
        )
        
        widget.Title = "Select Lesson to Deploy"
        
        -- Create lesson list
        pluginClient:getLessons({ limit = 50 }):andThen(function(lessons)
            for i, lesson in ipairs(lessons.items) do
                local button = Instance.new("TextButton")
                button.Text = lesson.title
                button.Size = UDim2.new(1, 0, 0, 30)
                button.Position = UDim2.new(0, 0, 0, (i-1) * 35)
                button.Parent = widget
                
                button.MouseButton1Click:Connect(function()
                    -- Deploy selected lesson
                    pluginClient:deployLesson(lesson.id, workspace):andThen(function(env)
                        print("Lesson deployed:", lesson.title)
                        widget:Destroy()
                    end)
                end)
            end
        end)
    end)
end

-- ============================================
-- UTILITY FUNCTIONS
-- ============================================

local function getCurrentLessonId()
    -- Return the current lesson ID
    return workspace:GetAttribute("CurrentLessonId") or "default-lesson"
end

local function isTeacher(player)
    -- Check if player has teacher role
    return player:GetAttribute("Role") == "Teacher"
end

local function createCheckpoint(player)
    -- Create checkpoint data for player
    if not player.Character then return nil end
    
    local humanoidRootPart = player.Character:FindFirstChild("HumanoidRootPart")
    if not humanoidRootPart then return nil end
    
    return {
        position = humanoidRootPart.Position,
        rotation = humanoidRootPart.Orientation,
        inventory = getPlayerInventory(player),
        objectives = getCompletedObjectives(player),
        timestamp = os.time()
    }
end

local function loadPlayerCheckpoint(player, checkpoint)
    -- Load player at checkpoint
    player.CharacterAdded:Connect(function(character)
        wait(0.1) -- Wait for character to load
        
        local humanoidRootPart = character:WaitForChild("HumanoidRootPart")
        humanoidRootPart.CFrame = CFrame.new(checkpoint.position) * 
            CFrame.Angles(math.rad(checkpoint.rotation.X), 
                         math.rad(checkpoint.rotation.Y), 
                         math.rad(checkpoint.rotation.Z))
        
        -- Restore inventory
        if checkpoint.inventory then
            restorePlayerInventory(player, checkpoint.inventory)
        end
    end)
end

local function spawnPlayerAtStart(player)
    -- Spawn player at lesson start point
    player.CharacterAdded:Connect(function(character)
        wait(0.1)
        local spawnPoint = workspace:FindFirstChild("LessonStart")
        if spawnPoint then
            character:SetPrimaryPartCFrame(spawnPoint.CFrame + Vector3.new(0, 5, 0))
        end
    end)
end

local function getPlayerInventory(player)
    -- Get player's current inventory
    local inventory = {}
    local backpack = player:FindFirstChild("Backpack")
    
    if backpack then
        for _, tool in ipairs(backpack:GetChildren()) do
            table.insert(inventory, tool.Name)
        end
    end
    
    return inventory
end

local function restorePlayerInventory(player, inventory)
    -- Restore player's inventory
    local ServerStorage = game:GetService("ServerStorage")
    local tools = ServerStorage:FindFirstChild("Tools")
    
    if tools then
        for _, toolName in ipairs(inventory) do
            local tool = tools:FindFirstChild(toolName)
            if tool then
                tool:Clone().Parent = player.Backpack
            end
        end
    end
end

local function getCompletedObjectives(player)
    -- Get list of completed objectives for player
    local objectives = {}
    
    for i = 1, 10 do
        local objKey = "Objective" .. i .. "Complete"
        if player:GetAttribute(objKey) then
            table.insert(objectives, "objective-" .. i)
        end
    end
    
    return objectives
end

local function showEducationalContent(player, content)
    -- Display educational content to player
    local gui = Instance.new("ScreenGui")
    gui.Name = "EducationalContent"
    gui.Parent = player.PlayerGui
    
    local frame = Instance.new("Frame")
    frame.Size = UDim2.new(0.8, 0, 0.8, 0)
    frame.Position = UDim2.new(0.1, 0, 0.1, 0)
    frame.BackgroundColor3 = Color3.fromRGB(255, 255, 255)
    frame.Parent = gui
    
    local textLabel = Instance.new("TextLabel")
    textLabel.Size = UDim2.new(0.9, 0, 0.8, 0)
    textLabel.Position = UDim2.new(0.05, 0, 0.05, 0)
    textLabel.Text = content.text or "Educational content here"
    textLabel.TextWrapped = true
    textLabel.TextScaled = false
    textLabel.TextSize = 18
    textLabel.BackgroundTransparency = 1
    textLabel.Parent = frame
    
    local closeButton = Instance.new("TextButton")
    closeButton.Size = UDim2.new(0.2, 0, 0.1, 0)
    closeButton.Position = UDim2.new(0.4, 0, 0.85, 0)
    closeButton.Text = "Close"
    closeButton.Parent = frame
    
    closeButton.MouseButton1Click:Connect(function()
        gui:Destroy()
    end)
end

local function showNotification(player, message)
    -- Show notification to player
    local gui = Instance.new("ScreenGui")
    gui.Name = "Notification"
    gui.Parent = player.PlayerGui
    
    local label = Instance.new("TextLabel")
    label.Size = UDim2.new(0, 400, 0, 50)
    label.Position = UDim2.new(0.5, -200, 0, 100)
    label.Text = message
    label.TextScaled = true
    label.BackgroundColor3 = Color3.fromRGB(50, 50, 50)
    label.TextColor3 = Color3.fromRGB(255, 255, 255)
    label.Parent = gui
    
    wait(3)
    gui:Destroy()
end

-- ============================================
-- MAIN INITIALIZATION
-- ============================================

local function initialize()
    print("ToolBoxAI Education System Initializing...")
    
    -- Setup systems
    deployLessonExample()
    trackPlayerProgress()
    setupRealtimeCollaboration()
    
    -- Start background tasks
    spawn(updateLeaderboards)
    
    print("ToolBoxAI Education System Ready!")
end

-- Start the system
initialize()
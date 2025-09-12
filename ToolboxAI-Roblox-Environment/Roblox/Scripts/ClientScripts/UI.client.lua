--[[
    ToolboxAI Client UI Script
    Version: 1.0.0
    Description: Comprehensive client-side UI system for educational gameplay,
                 including quiz interface, progress tracking, achievements, and animations
--]]

-- Services
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
local SoundService = game:GetService("SoundService")
local StarterGui = game:GetService("StarterGui")
local HttpService = game:GetService("HttpService")
local Lighting = game:GetService("Lighting")

-- Wait for player
local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")
local character = player.Character or player.CharacterAdded:Wait()
local humanoid = character:WaitForChild("Humanoid")

-- Remote Events and Functions
local remotes = ReplicatedStorage:WaitForChild("Remotes")
local events = remotes:WaitForChild("Events")
local functions = remotes:WaitForChild("Functions")

-- UI Configuration
local UI_CONFIG = {
    COLORS = {
        PRIMARY = Color3.fromRGB(0, 170, 255),
        SECONDARY = Color3.fromRGB(255, 170, 0),
        SUCCESS = Color3.fromRGB(100, 255, 100),
        ERROR = Color3.fromRGB(255, 100, 100),
        WARNING = Color3.fromRGB(255, 200, 100),
        BACKGROUND = Color3.fromRGB(30, 30, 30),
        SURFACE = Color3.fromRGB(45, 45, 45),
        TEXT = Color3.fromRGB(255, 255, 255),
        TEXT_SECONDARY = Color3.fromRGB(200, 200, 200)
    },
    ANIMATIONS = {
        FADE_TIME = 0.3,
        SLIDE_TIME = 0.5,
        BOUNCE_TIME = 0.4,
        PULSE_TIME = 1
    },
    FONTS = {
        TITLE = Enum.Font.SourceSansBold,
        BODY = Enum.Font.SourceSans,
        ACCENT = Enum.Font.SourceSansLight
    }
}

-- Create main screen GUI
local screenGui = Instance.new("ScreenGui")
screenGui.Name = "EducationalUI"
screenGui.ResetOnSpawn = false
screenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
screenGui.Parent = playerGui

-- Create UI Manager
local UIManager = {}
UIManager.elements = {}
UIManager.animations = {}

-- Initialize UI Components
function UIManager:Initialize()
    self:CreateMainHUD()
    self:CreateQuizInterface()
    self:CreateProgressDisplay()
    self:CreateNotificationSystem()
    self:CreateLeaderboard()
    self:CreateSettingsPanel()
    self:CreateChatSystem()
    self:CreateAchievementDisplay()
    self:SetupEventHandlers()
    
    print("[UI] Client interface initialized")
end

-- Create Main HUD
function UIManager:CreateMainHUD()
    -- Main container
    local hudFrame = Instance.new("Frame")
    hudFrame.Name = "MainHUD"
    hudFrame.Size = UDim2.new(1, 0, 0.15, 0)
    hudFrame.Position = UDim2.new(0, 0, 0, 0)
    hudFrame.BackgroundTransparency = 1
    hudFrame.Parent = screenGui
    
    -- Score display
    local scoreFrame = Instance.new("Frame")
    scoreFrame.Name = "ScoreDisplay"
    scoreFrame.Size = UDim2.new(0.2, 0, 0.3, 0)
    scoreFrame.Position = UDim2.new(0.02, 0, 0.1, 0)
    scoreFrame.BackgroundColor3 = UI_CONFIG.COLORS.SURFACE
    scoreFrame.BackgroundTransparency = 0.2
    scoreFrame.BorderSizePixel = 0
    scoreFrame.Parent = hudFrame
    
    local scoreCorner = Instance.new("UICorner")
    scoreCorner.CornerRadius = UDim.new(0, 8)
    scoreCorner.Parent = scoreFrame
    
    local scoreLabel = Instance.new("TextLabel")
    scoreLabel.Name = "ScoreLabel"
    scoreLabel.Size = UDim2.new(1, 0, 0.4, 0)
    scoreLabel.Position = UDim2.new(0, 0, 0, 0)
    scoreLabel.BackgroundTransparency = 1
    scoreLabel.Text = "SCORE"
    scoreLabel.TextColor3 = UI_CONFIG.COLORS.TEXT_SECONDARY
    scoreLabel.TextScaled = true
    scoreLabel.Font = UI_CONFIG.FONTS.ACCENT
    scoreLabel.Parent = scoreFrame
    
    local scoreValue = Instance.new("TextLabel")
    scoreValue.Name = "ScoreValue"
    scoreValue.Size = UDim2.new(1, 0, 0.6, 0)
    scoreValue.Position = UDim2.new(0, 0, 0.4, 0)
    scoreValue.BackgroundTransparency = 1
    scoreValue.Text = "0"
    scoreValue.TextColor3 = UI_CONFIG.COLORS.PRIMARY
    scoreValue.TextScaled = true
    scoreValue.Font = UI_CONFIG.FONTS.TITLE
    scoreValue.Parent = scoreFrame
    
    -- Progress bar
    local progressFrame = Instance.new("Frame")
    progressFrame.Name = "ProgressBar"
    progressFrame.Size = UDim2.new(0.4, 0, 0.15, 0)
    progressFrame.Position = UDim2.new(0.3, 0, 0.15, 0)
    progressFrame.BackgroundColor3 = UI_CONFIG.COLORS.SURFACE
    progressFrame.BackgroundTransparency = 0.5
    progressFrame.BorderSizePixel = 0
    progressFrame.Parent = hudFrame
    
    local progressCorner = Instance.new("UICorner")
    progressCorner.CornerRadius = UDim.new(0, 4)
    progressCorner.Parent = progressFrame
    
    local progressFill = Instance.new("Frame")
    progressFill.Name = "Fill"
    progressFill.Size = UDim2.new(0, 0, 1, 0)
    progressFill.BackgroundColor3 = UI_CONFIG.COLORS.SUCCESS
    progressFill.BorderSizePixel = 0
    progressFill.Parent = progressFrame
    
    local fillCorner = Instance.new("UICorner")
    fillCorner.CornerRadius = UDim.new(0, 4)
    fillCorner.Parent = progressFill
    
    -- Timer display
    local timerFrame = Instance.new("Frame")
    timerFrame.Name = "Timer"
    timerFrame.Size = UDim2.new(0.15, 0, 0.25, 0)
    timerFrame.Position = UDim2.new(0.825, 0, 0.125, 0)
    timerFrame.BackgroundColor3 = UI_CONFIG.COLORS.SURFACE
    timerFrame.BackgroundTransparency = 0.2
    timerFrame.BorderSizePixel = 0
    timerFrame.Parent = hudFrame
    
    local timerCorner = Instance.new("UICorner")
    timerCorner.CornerRadius = UDim.new(0, 8)
    timerCorner.Parent = timerFrame
    
    local timerText = Instance.new("TextLabel")
    timerText.Name = "TimerText"
    timerText.Size = UDim2.new(1, 0, 1, 0)
    timerText.BackgroundTransparency = 1
    timerText.Text = "00:00"
    timerText.TextColor3 = UI_CONFIG.COLORS.TEXT
    timerText.TextScaled = true
    timerText.Font = UI_CONFIG.FONTS.TITLE
    timerText.Parent = timerFrame
    
    self.elements.hud = hudFrame
    self.elements.scoreValue = scoreValue
    self.elements.progressFill = progressFill
    self.elements.timerText = timerText
end

-- Create Quiz Interface
function UIManager:CreateQuizInterface()
    -- Quiz container (initially hidden)
    local quizFrame = Instance.new("Frame")
    quizFrame.Name = "QuizInterface"
    quizFrame.Size = UDim2.new(0.8, 0, 0.7, 0)
    quizFrame.Position = UDim2.new(0.1, 0, 1.1, 0) -- Start off-screen
    quizFrame.BackgroundColor3 = UI_CONFIG.COLORS.BACKGROUND
    quizFrame.BackgroundTransparency = 0.1
    quizFrame.BorderSizePixel = 0
    quizFrame.Visible = false
    quizFrame.Parent = screenGui
    
    local quizCorner = Instance.new("UICorner")
    quizCorner.CornerRadius = UDim.new(0, 12)
    quizCorner.Parent = quizFrame
    
    -- Question display
    local questionFrame = Instance.new("Frame")
    questionFrame.Name = "QuestionFrame"
    questionFrame.Size = UDim2.new(0.95, 0, 0.3, 0)
    questionFrame.Position = UDim2.new(0.025, 0, 0.05, 0)
    questionFrame.BackgroundColor3 = UI_CONFIG.COLORS.SURFACE
    questionFrame.BorderSizePixel = 0
    questionFrame.Parent = quizFrame
    
    local questionCorner = Instance.new("UICorner")
    questionCorner.CornerRadius = UDim.new(0, 8)
    questionCorner.Parent = questionFrame
    
    local questionText = Instance.new("TextLabel")
    questionText.Name = "QuestionText"
    questionText.Size = UDim2.new(0.95, 0, 0.8, 0)
    questionText.Position = UDim2.new(0.025, 0, 0.1, 0)
    questionText.BackgroundTransparency = 1
    questionText.Text = "Question will appear here..."
    questionText.TextColor3 = UI_CONFIG.COLORS.TEXT
    questionText.TextScaled = false
    questionText.TextSize = 24
    questionText.TextWrapped = true
    questionText.Font = UI_CONFIG.FONTS.BODY
    questionText.Parent = questionFrame
    
    -- Answer options container
    local answersFrame = Instance.new("ScrollingFrame")
    answersFrame.Name = "AnswersFrame"
    answersFrame.Size = UDim2.new(0.95, 0, 0.5, 0)
    answersFrame.Position = UDim2.new(0.025, 0, 0.38, 0)
    answersFrame.BackgroundTransparency = 1
    answersFrame.ScrollBarThickness = 8
    answersFrame.CanvasSize = UDim2.new(0, 0, 0, 0)
    answersFrame.Parent = quizFrame
    
    local answersLayout = Instance.new("UIListLayout")
    answersLayout.Padding = UDim.new(0, 10)
    answersLayout.Parent = answersFrame
    
    -- Quiz controls
    local controlsFrame = Instance.new("Frame")
    controlsFrame.Name = "Controls"
    controlsFrame.Size = UDim2.new(0.95, 0, 0.08, 0)
    controlsFrame.Position = UDim2.new(0.025, 0, 0.9, 0)
    controlsFrame.BackgroundTransparency = 1
    controlsFrame.Parent = quizFrame
    
    local hintButton = Instance.new("TextButton")
    hintButton.Name = "HintButton"
    hintButton.Size = UDim2.new(0.2, 0, 1, 0)
    hintButton.Position = UDim2.new(0, 0, 0, 0)
    hintButton.BackgroundColor3 = UI_CONFIG.COLORS.WARNING
    hintButton.Text = "💡 Hint"
    hintButton.TextColor3 = UI_CONFIG.COLORS.TEXT
    hintButton.TextScaled = true
    hintButton.Font = UI_CONFIG.FONTS.TITLE
    hintButton.Parent = controlsFrame
    
    local hintCorner = Instance.new("UICorner")
    hintCorner.CornerRadius = UDim.new(0, 8)
    hintCorner.Parent = hintButton
    
    local skipButton = Instance.new("TextButton")
    skipButton.Name = "SkipButton"
    skipButton.Size = UDim2.new(0.2, 0, 1, 0)
    skipButton.Position = UDim2.new(0.25, 0, 0, 0)
    skipButton.BackgroundColor3 = UI_CONFIG.COLORS.SECONDARY
    skipButton.Text = "⏭️ Skip"
    skipButton.TextColor3 = UI_CONFIG.COLORS.TEXT
    skipButton.TextScaled = true
    skipButton.Font = UI_CONFIG.FONTS.TITLE
    skipButton.Parent = controlsFrame
    
    local skipCorner = Instance.new("UICorner")
    skipCorner.CornerRadius = UDim.new(0, 8)
    skipCorner.Parent = skipButton
    
    -- Timer for quiz
    local quizTimer = Instance.new("TextLabel")
    quizTimer.Name = "QuizTimer"
    quizTimer.Size = UDim2.new(0.3, 0, 1, 0)
    quizTimer.Position = UDim2.new(0.7, 0, 0, 0)
    quizTimer.BackgroundColor3 = UI_CONFIG.COLORS.SURFACE
    quizTimer.Text = "⏱️ 30s"
    quizTimer.TextColor3 = UI_CONFIG.COLORS.TEXT
    quizTimer.TextScaled = true
    quizTimer.Font = UI_CONFIG.FONTS.TITLE
    quizTimer.Parent = controlsFrame
    
    local timerCorner = Instance.new("UICorner")
    timerCorner.CornerRadius = UDim.new(0, 8)
    timerCorner.Parent = quizTimer
    
    self.elements.quizFrame = quizFrame
    self.elements.questionText = questionText
    self.elements.answersFrame = answersFrame
    self.elements.quizTimer = quizTimer
    self.elements.hintButton = hintButton
    self.elements.skipButton = skipButton
end

-- Create Progress Display
function UIManager:CreateProgressDisplay()
    local progressPanel = Instance.new("Frame")
    progressPanel.Name = "ProgressPanel"
    progressPanel.Size = UDim2.new(0.25, 0, 0.4, 0)
    progressPanel.Position = UDim2.new(1.05, 0, 0.3, 0) -- Start off-screen
    progressPanel.BackgroundColor3 = UI_CONFIG.COLORS.SURFACE
    progressPanel.BackgroundTransparency = 0.2
    progressPanel.BorderSizePixel = 0
    progressPanel.Visible = false
    progressPanel.Parent = screenGui
    
    local panelCorner = Instance.new("UICorner")
    panelCorner.CornerRadius = UDim.new(0, 12)
    panelCorner.Parent = progressPanel
    
    -- Title
    local titleLabel = Instance.new("TextLabel")
    titleLabel.Size = UDim2.new(0.9, 0, 0.15, 0)
    titleLabel.Position = UDim2.new(0.05, 0, 0.05, 0)
    titleLabel.BackgroundTransparency = 1
    titleLabel.Text = "📊 Your Progress"
    titleLabel.TextColor3 = UI_CONFIG.COLORS.TEXT
    titleLabel.TextScaled = true
    titleLabel.Font = UI_CONFIG.FONTS.TITLE
    titleLabel.Parent = progressPanel
    
    -- Stats container
    local statsFrame = Instance.new("Frame")
    statsFrame.Size = UDim2.new(0.9, 0, 0.75, 0)
    statsFrame.Position = UDim2.new(0.05, 0, 0.2, 0)
    statsFrame.BackgroundTransparency = 1
    statsFrame.Parent = progressPanel
    
    local statsLayout = Instance.new("UIListLayout")
    statsLayout.Padding = UDim.new(0, 5)
    statsLayout.Parent = statsFrame
    
    -- Create stat items
    local function createStatItem(name, icon)
        local item = Instance.new("Frame")
        item.Name = name
        item.Size = UDim2.new(1, 0, 0, 30)
        item.BackgroundTransparency = 1
        
        local label = Instance.new("TextLabel")
        label.Size = UDim2.new(0.6, 0, 1, 0)
        label.BackgroundTransparency = 1
        label.Text = icon .. " " .. name
        label.TextColor3 = UI_CONFIG.COLORS.TEXT_SECONDARY
        label.TextScaled = true
        label.Font = UI_CONFIG.FONTS.BODY
        label.TextXAlignment = Enum.TextXAlignment.Left
        label.Parent = item
        
        local value = Instance.new("TextLabel")
        value.Name = "Value"
        value.Size = UDim2.new(0.4, 0, 1, 0)
        value.Position = UDim2.new(0.6, 0, 0, 0)
        value.BackgroundTransparency = 1
        value.Text = "0"
        value.TextColor3 = UI_CONFIG.COLORS.PRIMARY
        value.TextScaled = true
        value.Font = UI_CONFIG.FONTS.TITLE
        value.TextXAlignment = Enum.TextXAlignment.Right
        value.Parent = item
        
        return item
    end
    
    local correctStat = createStatItem("Correct", "✅")
    correctStat.Parent = statsFrame
    
    local accuracyStat = createStatItem("Accuracy", "🎯")
    accuracyStat.Parent = statsFrame
    
    local streakStat = createStatItem("Streak", "🔥")
    streakStat.Parent = statsFrame
    
    local xpStat = createStatItem("XP Earned", "⭐")
    xpStat.Parent = statsFrame
    
    self.elements.progressPanel = progressPanel
    self.elements.progressStats = {
        correct = correctStat.Value,
        accuracy = accuracyStat.Value,
        streak = streakStat.Value,
        xp = xpStat.Value
    }
end

-- Create Notification System
function UIManager:CreateNotificationSystem()
    local notificationContainer = Instance.new("Frame")
    notificationContainer.Name = "Notifications"
    notificationContainer.Size = UDim2.new(0.3, 0, 0.8, 0)
    notificationContainer.Position = UDim2.new(0.69, 0, 0.19, 0)
    notificationContainer.BackgroundTransparency = 1
    notificationContainer.Parent = screenGui
    
    local notificationLayout = Instance.new("UIListLayout")
    notificationLayout.Padding = UDim.new(0, 10)
    notificationLayout.VerticalAlignment = Enum.VerticalAlignment.Bottom
    notificationLayout.Parent = notificationContainer
    
    self.elements.notificationContainer = notificationContainer
end

-- Create Leaderboard
function UIManager:CreateLeaderboard()
    local leaderboardFrame = Instance.new("Frame")
    leaderboardFrame.Name = "Leaderboard"
    leaderboardFrame.Size = UDim2.new(0.25, 0, 0.5, 0)
    leaderboardFrame.Position = UDim2.new(-0.3, 0, 0.25, 0) -- Start off-screen
    leaderboardFrame.BackgroundColor3 = UI_CONFIG.COLORS.SURFACE
    leaderboardFrame.BackgroundTransparency = 0.2
    leaderboardFrame.BorderSizePixel = 0
    leaderboardFrame.Visible = false
    leaderboardFrame.Parent = screenGui
    
    local leaderCorner = Instance.new("UICorner")
    leaderCorner.CornerRadius = UDim.new(0, 12)
    leaderCorner.Parent = leaderboardFrame
    
    -- Title
    local leaderTitle = Instance.new("TextLabel")
    leaderTitle.Size = UDim2.new(0.9, 0, 0.1, 0)
    leaderTitle.Position = UDim2.new(0.05, 0, 0.05, 0)
    leaderTitle.BackgroundTransparency = 1
    leaderTitle.Text = "🏆 Leaderboard"
    leaderTitle.TextColor3 = UI_CONFIG.COLORS.TEXT
    leaderTitle.TextScaled = true
    leaderTitle.Font = UI_CONFIG.FONTS.TITLE
    leaderTitle.Parent = leaderboardFrame
    
    -- Leaderboard list
    local leaderList = Instance.new("ScrollingFrame")
    leaderList.Name = "List"
    leaderList.Size = UDim2.new(0.9, 0, 0.8, 0)
    leaderList.Position = UDim2.new(0.05, 0, 0.15, 0)
    leaderList.BackgroundTransparency = 1
    leaderList.ScrollBarThickness = 4
    leaderList.CanvasSize = UDim2.new(0, 0, 0, 0)
    leaderList.Parent = leaderboardFrame
    
    local leaderLayout = Instance.new("UIListLayout")
    leaderLayout.Padding = UDim.new(0, 5)
    leaderLayout.Parent = leaderList
    
    self.elements.leaderboardFrame = leaderboardFrame
    self.elements.leaderList = leaderList
end

-- Create Settings Panel
function UIManager:CreateSettingsPanel()
    local settingsButton = Instance.new("ImageButton")
    settingsButton.Name = "SettingsButton"
    settingsButton.Size = UDim2.new(0, 40, 0, 40)
    settingsButton.Position = UDim2.new(1, -50, 0, 10)
    settingsButton.BackgroundColor3 = UI_CONFIG.COLORS.SURFACE
    settingsButton.Image = "rbxassetid://7059346373" -- Gear icon
    settingsButton.Parent = screenGui
    
    local settingsCorner = Instance.new("UICorner")
    settingsCorner.CornerRadius = UDim.new(0.5, 0)
    settingsCorner.Parent = settingsButton
    
    -- Settings panel (hidden by default)
    local settingsPanel = Instance.new("Frame")
    settingsPanel.Name = "SettingsPanel"
    settingsPanel.Size = UDim2.new(0.3, 0, 0.4, 0)
    settingsPanel.Position = UDim2.new(0.35, 0, 0.3, 0)
    settingsPanel.BackgroundColor3 = UI_CONFIG.COLORS.BACKGROUND
    settingsPanel.BorderSizePixel = 0
    settingsPanel.Visible = false
    settingsPanel.Parent = screenGui
    
    local panelCorner = Instance.new("UICorner")
    panelCorner.CornerRadius = UDim.new(0, 12)
    panelCorner.Parent = settingsPanel
    
    self.elements.settingsButton = settingsButton
    self.elements.settingsPanel = settingsPanel
end

-- Create Chat System
function UIManager:CreateChatSystem()
    -- Custom chat UI for educational messages
    local chatFrame = Instance.new("Frame")
    chatFrame.Name = "EducationalChat"
    chatFrame.Size = UDim2.new(0.35, 0, 0.25, 0)
    chatFrame.Position = UDim2.new(0.01, 0, 0.73, 0)
    chatFrame.BackgroundColor3 = UI_CONFIG.COLORS.SURFACE
    chatFrame.BackgroundTransparency = 0.5
    chatFrame.BorderSizePixel = 0
    chatFrame.Parent = screenGui
    
    local chatCorner = Instance.new("UICorner")
    chatCorner.CornerRadius = UDim.new(0, 8)
    chatCorner.Parent = chatFrame
    
    local chatScroll = Instance.new("ScrollingFrame")
    chatScroll.Size = UDim2.new(0.95, 0, 0.85, 0)
    chatScroll.Position = UDim2.new(0.025, 0, 0.05, 0)
    chatScroll.BackgroundTransparency = 1
    chatScroll.ScrollBarThickness = 4
    chatScroll.CanvasSize = UDim2.new(0, 0, 0, 0)
    chatScroll.Parent = chatFrame
    
    local chatLayout = Instance.new("UIListLayout")
    chatLayout.Padding = UDim.new(0, 3)
    chatLayout.Parent = chatScroll
    
    self.elements.chatFrame = chatFrame
    self.elements.chatScroll = chatScroll
end

-- Create Achievement Display
function UIManager:CreateAchievementDisplay()
    local achievementFrame = Instance.new("Frame")
    achievementFrame.Name = "Achievement"
    achievementFrame.Size = UDim2.new(0.3, 0, 0.15, 0)
    achievementFrame.Position = UDim2.new(0.35, 0, -0.2, 0) -- Start above screen
    achievementFrame.BackgroundColor3 = UI_CONFIG.COLORS.SECONDARY
    achievementFrame.BorderSizePixel = 0
    achievementFrame.Visible = false
    achievementFrame.Parent = screenGui
    
    local achieveCorner = Instance.new("UICorner")
    achieveCorner.CornerRadius = UDim.new(0, 12)
    achieveCorner.Parent = achievementFrame
    
    local achieveIcon = Instance.new("TextLabel")
    achieveIcon.Size = UDim2.new(0.2, 0, 0.8, 0)
    achieveIcon.Position = UDim2.new(0.05, 0, 0.1, 0)
    achieveIcon.BackgroundTransparency = 1
    achieveIcon.Text = "🏆"
    achieveIcon.TextScaled = true
    achieveIcon.Parent = achievementFrame
    
    local achieveText = Instance.new("TextLabel")
    achieveText.Size = UDim2.new(0.7, 0, 0.5, 0)
    achieveText.Position = UDim2.new(0.25, 0, 0.1, 0)
    achieveText.BackgroundTransparency = 1
    achieveText.Text = "Achievement Unlocked!"
    achieveText.TextColor3 = UI_CONFIG.COLORS.TEXT
    achieveText.TextScaled = true
    achieveText.Font = UI_CONFIG.FONTS.TITLE
    achieveText.Parent = achievementFrame
    
    local achieveName = Instance.new("TextLabel")
    achieveName.Size = UDim2.new(0.7, 0, 0.3, 0)
    achieveName.Position = UDim2.new(0.25, 0, 0.6, 0)
    achieveName.BackgroundTransparency = 1
    achieveName.Text = "First Steps"
    achieveName.TextColor3 = UI_CONFIG.COLORS.TEXT_SECONDARY
    achieveName.TextScaled = true
    achieveName.Font = UI_CONFIG.FONTS.BODY
    achieveName.Parent = achievementFrame
    
    self.elements.achievementFrame = achievementFrame
    self.elements.achieveName = achieveName
end

-- Animation Functions
function UIManager:AnimateElement(element, properties, duration, easingStyle)
    local tweenInfo = TweenInfo.new(
        duration or UI_CONFIG.ANIMATIONS.FADE_TIME,
        easingStyle or Enum.EasingStyle.Quad,
        Enum.EasingDirection.Out
    )
    
    local tween = TweenService:Create(element, tweenInfo, properties)
    tween:Play()
    return tween
end

function UIManager:ShowQuiz(questionData)
    local quizFrame = self.elements.quizFrame
    
    -- Clear previous answers
    for _, child in ipairs(self.elements.answersFrame:GetChildren()) do
        if child:IsA("Frame") then
            child:Destroy()
        end
    end
    
    -- Set question text
    self.elements.questionText.Text = questionData.text
    
    -- Create answer buttons
    if questionData.options then
        for i, option in ipairs(questionData.options) do
            local answerButton = Instance.new("TextButton")
            answerButton.Name = "Answer" .. i
            answerButton.Size = UDim2.new(1, 0, 0, 60)
            answerButton.BackgroundColor3 = UI_CONFIG.COLORS.SURFACE
            answerButton.Text = option
            answerButton.TextColor3 = UI_CONFIG.COLORS.TEXT
            answerButton.TextScaled = false
            answerButton.TextSize = 20
            answerButton.Font = UI_CONFIG.FONTS.BODY
            answerButton.Parent = self.elements.answersFrame
            
            local buttonCorner = Instance.new("UICorner")
            buttonCorner.CornerRadius = UDim.new(0, 8)
            buttonCorner.Parent = answerButton
            
            answerButton.MouseButton1Click:Connect(function()
                self:OnAnswerSelected(i, answerButton)
            end)
        end
        
        -- Update canvas size
        self.elements.answersFrame.CanvasSize = UDim2.new(0, 0, 0, #questionData.options * 70)
    end
    
    -- Show quiz with animation
    quizFrame.Visible = true
    self:AnimateElement(quizFrame, {Position = UDim2.new(0.1, 0, 0.15, 0)}, UI_CONFIG.ANIMATIONS.SLIDE_TIME)
    
    -- Start timer
    if questionData.time_limit then
        self:StartQuizTimer(questionData.time_limit)
    end
end

function UIManager:OnAnswerSelected(answerIndex, button)
    -- Highlight selection
    button.BackgroundColor3 = UI_CONFIG.COLORS.PRIMARY
    
    -- Disable all buttons
    for _, child in ipairs(self.elements.answersFrame:GetChildren()) do
        if child:IsA("TextButton") then
            child.Active = false
        end
    end
    
    -- Send answer to server
    events.SubmitAnswer:FireServer(answerIndex)
end

function UIManager:StartQuizTimer(duration)
    local startTime = tick()
    local connection
    
    connection = RunService.Heartbeat:Connect(function()
        local elapsed = tick() - startTime
        local remaining = math.max(0, duration - elapsed)
        
        self.elements.quizTimer.Text = string.format("⏱️ %ds", math.ceil(remaining))
        
        if remaining <= 5 then
            self.elements.quizTimer.TextColor3 = UI_CONFIG.COLORS.ERROR
        end
        
        if remaining <= 0 then
            connection:Disconnect()
            self:HideQuiz()
        end
    end)
end

function UIManager:HideQuiz()
    self:AnimateElement(self.elements.quizFrame, {Position = UDim2.new(0.1, 0, 1.1, 0)}, UI_CONFIG.ANIMATIONS.SLIDE_TIME)
    task.wait(UI_CONFIG.ANIMATIONS.SLIDE_TIME)
    self.elements.quizFrame.Visible = false
end

function UIManager:ShowNotification(message, notificationType)
    local notification = Instance.new("Frame")
    notification.Size = UDim2.new(1, 0, 0, 50)
    notification.BackgroundColor3 = UI_CONFIG.COLORS[notificationType:upper()] or UI_CONFIG.COLORS.PRIMARY
    notification.BackgroundTransparency = 0.2
    notification.Parent = self.elements.notificationContainer
    
    local notifCorner = Instance.new("UICorner")
    notifCorner.CornerRadius = UDim.new(0, 8)
    notifCorner.Parent = notification
    
    local notifText = Instance.new("TextLabel")
    notifText.Size = UDim2.new(0.95, 0, 1, 0)
    notifText.Position = UDim2.new(0.025, 0, 0, 0)
    notifText.BackgroundTransparency = 1
    notifText.Text = message
    notifText.TextColor3 = UI_CONFIG.COLORS.TEXT
    notifText.TextScaled = true
    notifText.Font = UI_CONFIG.FONTS.BODY
    notifText.Parent = notification
    
    -- Auto-remove after 5 seconds
    task.wait(5)
    self:AnimateElement(notification, {BackgroundTransparency = 1}, UI_CONFIG.ANIMATIONS.FADE_TIME)
    self:AnimateElement(notifText, {TextTransparency = 1}, UI_CONFIG.ANIMATIONS.FADE_TIME)
    task.wait(UI_CONFIG.ANIMATIONS.FADE_TIME)
    notification:Destroy()
end

function UIManager:ShowAchievement(achievementName, points)
    local frame = self.elements.achievementFrame
    self.elements.achieveName.Text = achievementName
    
    frame.Visible = true
    self:AnimateElement(frame, {Position = UDim2.new(0.35, 0, 0.1, 0)}, UI_CONFIG.ANIMATIONS.BOUNCE_TIME, Enum.EasingStyle.Bounce)
    
    -- Play sound
    local sound = Instance.new("Sound")
    sound.SoundId = "rbxassetid://1836830426" -- Achievement sound
    sound.Volume = 0.5
    sound.Parent = workspace
    sound:Play()
    
    task.wait(3)
    self:AnimateElement(frame, {Position = UDim2.new(0.35, 0, -0.2, 0)}, UI_CONFIG.ANIMATIONS.SLIDE_TIME)
    task.wait(UI_CONFIG.ANIMATIONS.SLIDE_TIME)
    frame.Visible = false
end

function UIManager:UpdateScore(score)
    self.elements.scoreValue.Text = tostring(score)
    
    -- Pulse animation
    local original = self.elements.scoreValue.TextColor3
    self:AnimateElement(self.elements.scoreValue, {TextColor3 = UI_CONFIG.COLORS.SUCCESS}, 0.2)
    task.wait(0.2)
    self:AnimateElement(self.elements.scoreValue, {TextColor3 = original}, 0.2)
end

function UIManager:UpdateProgress(progress)
    local fillSize = UDim2.new(progress / 100, 0, 1, 0)
    self:AnimateElement(self.elements.progressFill, {Size = fillSize}, UI_CONFIG.ANIMATIONS.SLIDE_TIME)
end

function UIManager:UpdateLeaderboard(leaderboardData)
    -- Clear existing entries
    for _, child in ipairs(self.elements.leaderList:GetChildren()) do
        if child:IsA("Frame") then
            child:Destroy()
        end
    end
    
    -- Create new entries
    for i, entry in ipairs(leaderboardData) do
        local entryFrame = Instance.new("Frame")
        entryFrame.Size = UDim2.new(1, 0, 0, 30)
        entryFrame.BackgroundColor3 = i == 1 and UI_CONFIG.COLORS.SECONDARY or UI_CONFIG.COLORS.SURFACE
        entryFrame.BackgroundTransparency = 0.5
        entryFrame.Parent = self.elements.leaderList
        
        local entryCorner = Instance.new("UICorner")
        entryCorner.CornerRadius = UDim.new(0, 4)
        entryCorner.Parent = entryFrame
        
        local rankLabel = Instance.new("TextLabel")
        rankLabel.Size = UDim2.new(0.15, 0, 1, 0)
        rankLabel.BackgroundTransparency = 1
        rankLabel.Text = tostring(i)
        rankLabel.TextColor3 = UI_CONFIG.COLORS.TEXT
        rankLabel.TextScaled = true
        rankLabel.Font = UI_CONFIG.FONTS.TITLE
        rankLabel.Parent = entryFrame
        
        local nameLabel = Instance.new("TextLabel")
        nameLabel.Size = UDim2.new(0.55, 0, 1, 0)
        nameLabel.Position = UDim2.new(0.15, 0, 0, 0)
        nameLabel.BackgroundTransparency = 1
        nameLabel.Text = entry.name
        nameLabel.TextColor3 = UI_CONFIG.COLORS.TEXT
        nameLabel.TextScaled = true
        nameLabel.Font = UI_CONFIG.FONTS.BODY
        nameLabel.TextXAlignment = Enum.TextXAlignment.Left
        nameLabel.Parent = entryFrame
        
        local scoreLabel = Instance.new("TextLabel")
        scoreLabel.Size = UDim2.new(0.3, 0, 1, 0)
        scoreLabel.Position = UDim2.new(0.7, 0, 0, 0)
        scoreLabel.BackgroundTransparency = 1
        scoreLabel.Text = tostring(entry.score)
        scoreLabel.TextColor3 = UI_CONFIG.COLORS.PRIMARY
        scoreLabel.TextScaled = true
        scoreLabel.Font = UI_CONFIG.FONTS.TITLE
        scoreLabel.Parent = entryFrame
    end
    
    -- Update canvas size
    self.elements.leaderList.CanvasSize = UDim2.new(0, 0, 0, #leaderboardData * 35)
end

-- Setup Event Handlers
function UIManager:SetupEventHandlers()
    -- Handle server events
    events.UpdateProgress.OnClientEvent:Connect(function(data)
        if data.type == "quiz_feedback" then
            self:ShowNotification(
                data.correct and "✅ Correct! +" .. data.points .. " points" or "❌ Incorrect",
                data.correct and "success" or "error"
            )
            self:UpdateScore(data.total_score or 0)
            
        elseif data.type == "question_presented" then
            self:ShowQuiz(data)
            
        elseif data.type == "quiz_completed" then
            self:HideQuiz()
            self:ShowNotification("Quiz completed! Well done!", "success")
            
        elseif data.type == "achievement_unlocked" then
            self:ShowAchievement(data.achievement_name, data.points)
            
        elseif data.type == "progress_update" then
            self:UpdateProgress(data.progress)
            
        elseif data.type == "leaderboard_update" then
            self:UpdateLeaderboard(data.leaderboard)
        end
    end)
    
    events.AchievementUnlocked.OnClientEvent:Connect(function(achievementId, points)
        self:ShowAchievement(achievementId, points)
    end)
    
    -- Settings button
    self.elements.settingsButton.MouseButton1Click:Connect(function()
        self.elements.settingsPanel.Visible = not self.elements.settingsPanel.Visible
    end)
    
    -- Keyboard shortcuts
    UserInputService.InputBegan:Connect(function(input, gameProcessed)
        if gameProcessed then return end
        
        if input.KeyCode == Enum.KeyCode.Tab then
            -- Toggle leaderboard
            local leaderboard = self.elements.leaderboardFrame
            leaderboard.Visible = not leaderboard.Visible
            
            if leaderboard.Visible then
                self:AnimateElement(leaderboard, {Position = UDim2.new(0.02, 0, 0.25, 0)}, UI_CONFIG.ANIMATIONS.SLIDE_TIME)
                
                -- Request updated leaderboard
                local leaderboardData = functions.GetLeaderboard:InvokeServer()
                if leaderboardData then
                    self:UpdateLeaderboard(leaderboardData)
                end
            else
                self:AnimateElement(leaderboard, {Position = UDim2.new(-0.3, 0, 0.25, 0)}, UI_CONFIG.ANIMATIONS.SLIDE_TIME)
            end
            
        elseif input.KeyCode == Enum.KeyCode.P then
            -- Toggle progress panel
            local progressPanel = self.elements.progressPanel
            progressPanel.Visible = not progressPanel.Visible
            
            if progressPanel.Visible then
                self:AnimateElement(progressPanel, {Position = UDim2.new(0.73, 0, 0.3, 0)}, UI_CONFIG.ANIMATIONS.SLIDE_TIME)
            else
                self:AnimateElement(progressPanel, {Position = UDim2.new(1.05, 0, 0.3, 0)}, UI_CONFIG.ANIMATIONS.SLIDE_TIME)
            end
        end
    end)
    
    -- Hint button
    self.elements.hintButton.MouseButton1Click:Connect(function()
        events.RequestHint:FireServer()
    end)
    
    -- Update timer
    spawn(function()
        local startTime = tick()
        while true do
            local elapsed = tick() - startTime
            local minutes = math.floor(elapsed / 60)
            local seconds = math.floor(elapsed % 60)
            self.elements.timerText.Text = string.format("%02d:%02d", minutes, seconds)
            task.wait(1)
        end
    end)
end

-- Initialize UI
UIManager:Initialize()

-- Notify server that client is ready
task.wait(1)
events.PlayerReady:FireServer()

print("[UI] Client interface ready")
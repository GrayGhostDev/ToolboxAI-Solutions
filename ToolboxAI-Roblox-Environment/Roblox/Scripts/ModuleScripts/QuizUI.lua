--[[
    ToolboxAI Quiz UI Module
    Version: 1.0.0
    Description: Creates interactive quiz interfaces for educational content
                 Supports multiple question types, scoring, and progress tracking
--]]

local QuizUI = {}
QuizUI.__index = QuizUI

-- Services
local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")
local RunService = game:GetService("RunService")
local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local StarterGui = game:GetService("StarterGui")

-- Configuration
local CONFIG = {
    COLORS = {
        primary = Color3.fromRGB(41, 128, 185),
        secondary = Color3.fromRGB(52, 152, 219),
        success = Color3.fromRGB(46, 204, 113),
        error = Color3.fromRGB(231, 76, 60),
        warning = Color3.fromRGB(241, 196, 15),
        background = Color3.fromRGB(44, 62, 80),
        text = Color3.fromRGB(236, 240, 241),
        textDark = Color3.fromRGB(52, 73, 94)
    },
    FONTS = {
        title = Enum.Font.SourceSansBold,
        body = Enum.Font.SourceSans,
        button = Enum.Font.SourceSansSemibold
    },
    ANIMATION = {
        duration = 0.3,
        style = Enum.EasingStyle.Quad,
        direction = Enum.EasingDirection.Out
    }
}

-- Constructor
function QuizUI.new(player)
    local self = setmetatable({}, QuizUI)
    self.player = player or Players.LocalPlayer
    self.currentQuiz = nil
    self.currentQuestion = 1
    self.score = 0
    self.answers = {}
    self.startTime = nil
    self.gui = nil
    self.elements = {}
    self.isActive = false
    return self
end

-- Create quiz interface
function QuizUI:create(quizData)
    if self.isActive then
        self:destroy()
    end
    
    self.currentQuiz = quizData
    self.currentQuestion = 1
    self.score = 0
    self.answers = {}
    self.startTime = tick()
    self.isActive = true
    
    -- Create ScreenGui
    self.gui = Instance.new("ScreenGui")
    self.gui.Name = "QuizInterface"
    self.gui.ResetOnSpawn = false
    self.gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
    
    -- Create main container
    local mainContainer = self:createMainContainer()
    mainContainer.Parent = self.gui
    
    -- Create header
    local header = self:createHeader(quizData)
    header.Parent = mainContainer
    
    -- Create progress bar
    local progressBar = self:createProgressBar()
    progressBar.Parent = mainContainer
    
    -- Create question container
    local questionContainer = self:createQuestionContainer()
    questionContainer.Parent = mainContainer
    
    -- Create footer
    local footer = self:createFooter()
    footer.Parent = mainContainer
    
    -- Store elements for later reference
    self.elements = {
        mainContainer = mainContainer,
        header = header,
        progressBar = progressBar,
        questionContainer = questionContainer,
        footer = footer
    }
    
    -- Display first question
    self:displayQuestion(1)
    
    -- Parent to player's GUI
    self.gui.Parent = self.player:WaitForChild("PlayerGui")
    
    -- Animate entrance
    self:animateEntrance()
    
    return self.gui
end

-- Create main container
function QuizUI:createMainContainer()
    local container = Instance.new("Frame")
    container.Name = "MainContainer"
    container.Size = UDim2.new(0, 600, 0, 500)
    container.Position = UDim2.new(0.5, -300, 0.5, -250)
    container.BackgroundColor3 = CONFIG.COLORS.background
    container.BorderSizePixel = 0
    container.ClipsDescendants = true
    
    -- Add rounded corners
    local corner = Instance.new("UICorner")
    corner.CornerRadius = UDim.new(0, 12)
    corner.Parent = container
    
    -- Add shadow
    local shadow = Instance.new("ImageLabel")
    shadow.Name = "Shadow"
    shadow.Size = UDim2.new(1, 20, 1, 20)
    shadow.Position = UDim2.new(0, -10, 0, -10)
    shadow.BackgroundTransparency = 1
    shadow.Image = "rbxasset://textures/ui/GuiImagePlaceholder.png"
    shadow.ImageColor3 = Color3.new(0, 0, 0)
    shadow.ImageTransparency = 0.5
    shadow.ZIndex = -1
    shadow.Parent = container
    
    return container
end

-- Create header
function QuizUI:createHeader(quizData)
    local header = Instance.new("Frame")
    header.Name = "Header"
    header.Size = UDim2.new(1, 0, 0, 80)
    header.Position = UDim2.new(0, 0, 0, 0)
    header.BackgroundColor3 = CONFIG.COLORS.primary
    header.BorderSizePixel = 0
    
    -- Title
    local title = Instance.new("TextLabel")
    title.Name = "Title"
    title.Size = UDim2.new(0.7, -20, 0.5, 0)
    title.Position = UDim2.new(0, 20, 0, 10)
    title.BackgroundTransparency = 1
    title.Text = quizData.title or "Quiz"
    title.TextColor3 = CONFIG.COLORS.text
    title.TextScaled = true
    title.Font = CONFIG.FONTS.title
    title.TextXAlignment = Enum.TextXAlignment.Left
    title.Parent = header
    
    -- Subject
    local subject = Instance.new("TextLabel")
    subject.Name = "Subject"
    subject.Size = UDim2.new(0.7, -20, 0.3, 0)
    subject.Position = UDim2.new(0, 20, 0.5, 0)
    subject.BackgroundTransparency = 1
    subject.Text = quizData.subject or "General Knowledge"
    subject.TextColor3 = CONFIG.COLORS.text
    subject.TextScaled = true
    subject.Font = CONFIG.FONTS.body
    subject.TextXAlignment = Enum.TextXAlignment.Left
    subject.TextTransparency = 0.3
    subject.Parent = header
    
    -- Close button
    local closeButton = Instance.new("TextButton")
    closeButton.Name = "CloseButton"
    closeButton.Size = UDim2.new(0, 40, 0, 40)
    closeButton.Position = UDim2.new(1, -50, 0.5, -20)
    closeButton.BackgroundColor3 = CONFIG.COLORS.error
    closeButton.Text = "X"
    closeButton.TextColor3 = CONFIG.COLORS.text
    closeButton.TextScaled = true
    closeButton.Font = CONFIG.FONTS.button
    closeButton.BorderSizePixel = 0
    closeButton.Parent = header
    
    local closeCorner = Instance.new("UICorner")
    closeCorner.CornerRadius = UDim.new(0, 8)
    closeCorner.Parent = closeButton
    
    closeButton.MouseButton1Click:Connect(function()
        self:close()
    end)
    
    return header
end

-- Create progress bar
function QuizUI:createProgressBar()
    local progressContainer = Instance.new("Frame")
    progressContainer.Name = "ProgressContainer"
    progressContainer.Size = UDim2.new(1, -40, 0, 30)
    progressContainer.Position = UDim2.new(0, 20, 0, 90)
    progressContainer.BackgroundTransparency = 1
    progressContainer.Parent = container
    
    -- Question counter
    local questionCounter = Instance.new("TextLabel")
    questionCounter.Name = "QuestionCounter"
    questionCounter.Size = UDim2.new(0.3, 0, 1, 0)
    questionCounter.Position = UDim2.new(0, 0, 0, 0)
    questionCounter.BackgroundTransparency = 1
    questionCounter.Text = "Question 1 of " .. #self.currentQuiz.questions
    questionCounter.TextColor3 = CONFIG.COLORS.text
    questionCounter.TextScaled = true
    questionCounter.Font = CONFIG.FONTS.body
    questionCounter.TextXAlignment = Enum.TextXAlignment.Left
    questionCounter.Parent = progressContainer
    
    -- Progress bar background
    local progressBg = Instance.new("Frame")
    progressBg.Name = "ProgressBackground"
    progressBg.Size = UDim2.new(0.65, 0, 0, 8)
    progressBg.Position = UDim2.new(0.35, 0, 0.5, -4)
    progressBg.BackgroundColor3 = Color3.new(0.2, 0.2, 0.2)
    progressBg.BorderSizePixel = 0
    progressBg.Parent = progressContainer
    
    local bgCorner = Instance.new("UICorner")
    bgCorner.CornerRadius = UDim.new(0, 4)
    bgCorner.Parent = progressBg
    
    -- Progress bar fill
    local progressFill = Instance.new("Frame")
    progressFill.Name = "ProgressFill"
    progressFill.Size = UDim2.new(0, 0, 1, 0)
    progressFill.Position = UDim2.new(0, 0, 0, 0)
    progressFill.BackgroundColor3 = CONFIG.COLORS.success
    progressFill.BorderSizePixel = 0
    progressFill.Parent = progressBg
    
    local fillCorner = Instance.new("UICorner")
    fillCorner.CornerRadius = UDim.new(0, 4)
    fillCorner.Parent = progressFill
    
    return progressContainer
end

-- Create question container
function QuizUI:createQuestionContainer()
    local container = Instance.new("Frame")
    container.Name = "QuestionContainer"
    container.Size = UDim2.new(1, -40, 1, -180)
    container.Position = UDim2.new(0, 20, 0, 130)
    container.BackgroundTransparency = 1
    
    -- Question text
    local questionFrame = Instance.new("Frame")
    questionFrame.Name = "QuestionFrame"
    questionFrame.Size = UDim2.new(1, 0, 0.3, 0)
    questionFrame.Position = UDim2.new(0, 0, 0, 0)
    questionFrame.BackgroundColor3 = Color3.new(1, 1, 1)
    questionFrame.BackgroundTransparency = 0.95
    questionFrame.BorderSizePixel = 0
    questionFrame.Parent = container
    
    local questionCorner = Instance.new("UICorner")
    questionCorner.CornerRadius = UDim.new(0, 8)
    questionCorner.Parent = questionFrame
    
    local questionText = Instance.new("TextLabel")
    questionText.Name = "QuestionText"
    questionText.Size = UDim2.new(1, -20, 1, -20)
    questionText.Position = UDim2.new(0, 10, 0, 10)
    questionText.BackgroundTransparency = 1
    questionText.Text = ""
    questionText.TextColor3 = CONFIG.COLORS.text
    questionText.TextScaled = false
    questionText.TextSize = 18
    questionText.Font = CONFIG.FONTS.body
    questionText.TextWrapped = true
    questionText.TextXAlignment = Enum.TextXAlignment.Left
    questionText.TextYAlignment = Enum.TextYAlignment.Top
    questionText.Parent = questionFrame
    
    -- Answers container
    local answersFrame = Instance.new("ScrollingFrame")
    answersFrame.Name = "AnswersFrame"
    answersFrame.Size = UDim2.new(1, 0, 0.65, 0)
    answersFrame.Position = UDim2.new(0, 0, 0.35, 0)
    answersFrame.BackgroundTransparency = 1
    answersFrame.BorderSizePixel = 0
    answersFrame.ScrollBarThickness = 6
    answersFrame.ScrollBarImageColor3 = CONFIG.COLORS.primary
    answersFrame.CanvasSize = UDim2.new(1, 0, 0, 0)
    answersFrame.Parent = container
    
    local listLayout = Instance.new("UIListLayout")
    listLayout.Name = "ListLayout"
    listLayout.SortOrder = Enum.SortOrder.LayoutOrder
    listLayout.Padding = UDim.new(0, 10)
    listLayout.Parent = answersFrame
    
    return container
end

-- Create footer
function QuizUI:createFooter()
    local footer = Instance.new("Frame")
    footer.Name = "Footer"
    footer.Size = UDim2.new(1, -40, 0, 50)
    footer.Position = UDim2.new(0, 20, 1, -60)
    footer.BackgroundTransparency = 1
    
    -- Previous button
    local prevButton = Instance.new("TextButton")
    prevButton.Name = "PreviousButton"
    prevButton.Size = UDim2.new(0.25, -5, 1, 0)
    prevButton.Position = UDim2.new(0, 0, 0, 0)
    prevButton.BackgroundColor3 = CONFIG.COLORS.secondary
    prevButton.Text = "Previous"
    prevButton.TextColor3 = CONFIG.COLORS.text
    prevButton.TextScaled = true
    prevButton.Font = CONFIG.FONTS.button
    prevButton.BorderSizePixel = 0
    prevButton.Parent = footer
    
    local prevCorner = Instance.new("UICorner")
    prevCorner.CornerRadius = UDim.new(0, 8)
    prevCorner.Parent = prevButton
    
    prevButton.MouseButton1Click:Connect(function()
        self:previousQuestion()
    end)
    
    -- Score display
    local scoreLabel = Instance.new("TextLabel")
    scoreLabel.Name = "ScoreLabel"
    scoreLabel.Size = UDim2.new(0.4, 0, 1, 0)
    scoreLabel.Position = UDim2.new(0.3, 0, 0, 0)
    scoreLabel.BackgroundTransparency = 1
    scoreLabel.Text = "Score: 0"
    scoreLabel.TextColor3 = CONFIG.COLORS.text
    scoreLabel.TextScaled = true
    scoreLabel.Font = CONFIG.FONTS.title
    scoreLabel.Parent = footer
    
    -- Next button
    local nextButton = Instance.new("TextButton")
    nextButton.Name = "NextButton"
    nextButton.Size = UDim2.new(0.25, -5, 1, 0)
    nextButton.Position = UDim2.new(0.75, 5, 0, 0)
    nextButton.BackgroundColor3 = CONFIG.COLORS.success
    nextButton.Text = "Next"
    nextButton.TextColor3 = CONFIG.COLORS.text
    nextButton.TextScaled = true
    nextButton.Font = CONFIG.FONTS.button
    nextButton.BorderSizePixel = 0
    nextButton.Parent = footer
    
    local nextCorner = Instance.new("UICorner")
    nextCorner.CornerRadius = UDim.new(0, 8)
    nextCorner.Parent = nextButton
    
    nextButton.MouseButton1Click:Connect(function()
        self:nextQuestion()
    end)
    
    return footer
end

-- Display question
function QuizUI:displayQuestion(questionIndex)
    if not self.currentQuiz or not self.currentQuiz.questions then
        return
    end
    
    local question = self.currentQuiz.questions[questionIndex]
    if not question then
        return
    end
    
    self.currentQuestion = questionIndex
    
    -- Update question counter
    local questionCounter = self.elements.questionContainer:FindFirstChild("QuestionCounter", true)
    if questionCounter then
        questionCounter.Text = "Question " .. questionIndex .. " of " .. #self.currentQuiz.questions
    end
    
    -- Update progress bar
    self:updateProgressBar()
    
    -- Update question text
    local questionText = self.elements.questionContainer:FindFirstChild("QuestionText", true)
    if questionText then
        questionText.Text = question.question or ""
    end
    
    -- Clear previous answers
    local answersFrame = self.elements.questionContainer:FindFirstChild("AnswersFrame", true)
    if answersFrame then
        for _, child in ipairs(answersFrame:GetChildren()) do
            if child:IsA("Frame") then
                child:Destroy()
            end
        end
        
        -- Create answer buttons
        local answerOptions = question.answers or question.options or {}
        for i, answer in ipairs(answerOptions) do
            local answerButton = self:createAnswerButton(answer, i)
            answerButton.Parent = answersFrame
        end
        
        -- Update canvas size
        local listLayout = answersFrame:FindFirstChild("ListLayout")
        if listLayout then
            answersFrame.CanvasSize = UDim2.new(1, 0, 0, listLayout.AbsoluteContentSize.Y)
        end
    end
    
    -- Update button states
    self:updateButtonStates()
end

-- Create answer button
function QuizUI:createAnswerButton(answer, index)
    local button = Instance.new("Frame")
    button.Name = "AnswerButton_" .. index
    button.Size = UDim2.new(1, 0, 0, 50)
    button.BackgroundColor3 = Color3.new(1, 1, 1)
    button.BackgroundTransparency = 0.9
    button.BorderSizePixel = 0
    button.LayoutOrder = index
    
    local corner = Instance.new("UICorner")
    corner.CornerRadius = UDim.new(0, 8)
    corner.Parent = button
    
    local textButton = Instance.new("TextButton")
    textButton.Name = "Button"
    textButton.Size = UDim2.new(1, 0, 1, 0)
    textButton.BackgroundTransparency = 1
    textButton.Text = ""
    textButton.Parent = button
    
    local label = Instance.new("TextLabel")
    label.Name = "Label"
    label.Size = UDim2.new(0.1, 0, 1, 0)
    label.Position = UDim2.new(0, 10, 0, 0)
    label.BackgroundTransparency = 1
    label.Text = string.char(64 + index) .. "."
    label.TextColor3 = CONFIG.COLORS.text
    label.TextScaled = true
    label.Font = CONFIG.FONTS.button
    label.Parent = button
    
    local answerText = Instance.new("TextLabel")
    answerText.Name = "AnswerText"
    answerText.Size = UDim2.new(0.85, 0, 1, -10)
    answerText.Position = UDim2.new(0.1, 0, 0, 5)
    answerText.BackgroundTransparency = 1
    answerText.Text = answer.text or answer
    answerText.TextColor3 = CONFIG.COLORS.text
    answerText.TextScaled = false
    answerText.TextSize = 16
    answerText.Font = CONFIG.FONTS.body
    answerText.TextWrapped = true
    answerText.TextXAlignment = Enum.TextXAlignment.Left
    answerText.Parent = button
    
    -- Check if already answered
    local savedAnswer = self.answers[self.currentQuestion]
    if savedAnswer and savedAnswer.index == index then
        button.BackgroundColor3 = CONFIG.COLORS.primary
        button.BackgroundTransparency = 0.7
    end
    
    -- Click handler
    textButton.MouseButton1Click:Connect(function()
        self:selectAnswer(index, answer)
        
        -- Update visual
        local parent = button.Parent
        for _, child in ipairs(parent:GetChildren()) do
            if child:IsA("Frame") then
                child.BackgroundColor3 = Color3.new(1, 1, 1)
                child.BackgroundTransparency = 0.9
            end
        end
        button.BackgroundColor3 = CONFIG.COLORS.primary
        button.BackgroundTransparency = 0.7
    end)
    
    -- Hover effect
    textButton.MouseEnter:Connect(function()
        if button.BackgroundTransparency > 0.8 then
            button.BackgroundTransparency = 0.85
        end
    end)
    
    textButton.MouseLeave:Connect(function()
        if button.BackgroundTransparency > 0.8 then
            button.BackgroundTransparency = 0.9
        end
    end)
    
    return button
end

-- Select answer
function QuizUI:selectAnswer(index, answer)
    local question = self.currentQuiz.questions[self.currentQuestion]
    
    self.answers[self.currentQuestion] = {
        index = index,
        answer = answer,
        correct = answer.correct or false,
        timestamp = tick()
    }
    
    -- Update score if correct
    if answer.correct then
        self.score = self.score + (question.points or 1)
        self:updateScore()
    end
end

-- Navigate to previous question
function QuizUI:previousQuestion()
    if self.currentQuestion > 1 then
        self:displayQuestion(self.currentQuestion - 1)
    end
end

-- Navigate to next question
function QuizUI:nextQuestion()
    if self.currentQuestion < #self.currentQuiz.questions then
        self:displayQuestion(self.currentQuestion + 1)
    elseif self.currentQuestion == #self.currentQuiz.questions then
        self:submitQuiz()
    end
end

-- Update button states
function QuizUI:updateButtonStates()
    local prevButton = self.elements.footer:FindFirstChild("PreviousButton")
    local nextButton = self.elements.footer:FindFirstChild("NextButton")
    
    if prevButton then
        prevButton.Visible = self.currentQuestion > 1
    end
    
    if nextButton then
        if self.currentQuestion == #self.currentQuiz.questions then
            nextButton.Text = "Submit"
            nextButton.BackgroundColor3 = CONFIG.COLORS.warning
        else
            nextButton.Text = "Next"
            nextButton.BackgroundColor3 = CONFIG.COLORS.success
        end
    end
end

-- Update progress bar
function QuizUI:updateProgressBar()
    local progressFill = self.elements.progressBar:FindFirstChild("ProgressFill", true)
    if progressFill then
        local progress = self.currentQuestion / #self.currentQuiz.questions
        local tween = TweenService:Create(
            progressFill,
            TweenInfo.new(CONFIG.ANIMATION.duration, CONFIG.ANIMATION.style, CONFIG.ANIMATION.direction),
            {Size = UDim2.new(progress, 0, 1, 0)}
        )
        tween:Play()
    end
end

-- Update score display
function QuizUI:updateScore()
    local scoreLabel = self.elements.footer:FindFirstChild("ScoreLabel")
    if scoreLabel then
        scoreLabel.Text = "Score: " .. self.score
    end
end

-- Submit quiz
function QuizUI:submitQuiz()
    local endTime = tick()
    local duration = endTime - self.startTime
    
    -- Calculate final score
    local totalPossible = 0
    for _, question in ipairs(self.currentQuiz.questions) do
        totalPossible = totalPossible + (question.points or 1)
    end
    
    local percentage = math.floor((self.score / totalPossible) * 100)
    
    -- Create results display
    self:showResults({
        score = self.score,
        totalPossible = totalPossible,
        percentage = percentage,
        duration = duration,
        answers = self.answers
    })
    
    -- Send results to server
    self:sendResults({
        quizId = self.currentQuiz.id,
        score = self.score,
        percentage = percentage,
        duration = duration,
        answers = self.answers
    })
end

-- Show results
function QuizUI:showResults(results)
    -- Clear question container
    local questionContainer = self.elements.questionContainer
    for _, child in ipairs(questionContainer:GetChildren()) do
        child:Destroy()
    end
    
    -- Create results display
    local resultsFrame = Instance.new("Frame")
    resultsFrame.Name = "ResultsFrame"
    resultsFrame.Size = UDim2.new(1, 0, 1, 0)
    resultsFrame.BackgroundTransparency = 1
    resultsFrame.Parent = questionContainer
    
    -- Results title
    local title = Instance.new("TextLabel")
    title.Size = UDim2.new(1, 0, 0.2, 0)
    title.Position = UDim2.new(0, 0, 0, 0)
    title.BackgroundTransparency = 1
    title.Text = "Quiz Complete!"
    title.TextColor3 = CONFIG.COLORS.text
    title.TextScaled = true
    title.Font = CONFIG.FONTS.title
    title.Parent = resultsFrame
    
    -- Score display
    local scoreFrame = Instance.new("Frame")
    scoreFrame.Size = UDim2.new(0.8, 0, 0.3, 0)
    scoreFrame.Position = UDim2.new(0.1, 0, 0.25, 0)
    scoreFrame.BackgroundColor3 = CONFIG.COLORS.primary
    scoreFrame.BorderSizePixel = 0
    scoreFrame.Parent = resultsFrame
    
    local scoreCorner = Instance.new("UICorner")
    scoreCorner.CornerRadius = UDim.new(0, 12)
    scoreCorner.Parent = scoreFrame
    
    local scoreLabel = Instance.new("TextLabel")
    scoreLabel.Size = UDim2.new(1, 0, 0.6, 0)
    scoreLabel.Position = UDim2.new(0, 0, 0.1, 0)
    scoreLabel.BackgroundTransparency = 1
    scoreLabel.Text = results.score .. " / " .. results.totalPossible
    scoreLabel.TextColor3 = CONFIG.COLORS.text
    scoreLabel.TextScaled = true
    scoreLabel.Font = CONFIG.FONTS.title
    scoreLabel.Parent = scoreFrame
    
    local percentageLabel = Instance.new("TextLabel")
    percentageLabel.Size = UDim2.new(1, 0, 0.3, 0)
    percentageLabel.Position = UDim2.new(0, 0, 0.6, 0)
    percentageLabel.BackgroundTransparency = 1
    percentageLabel.Text = results.percentage .. "%"
    percentageLabel.TextColor3 = CONFIG.COLORS.text
    percentageLabel.TextScaled = true
    percentageLabel.Font = CONFIG.FONTS.body
    percentageLabel.Parent = scoreFrame
    
    -- Time taken
    local timeLabel = Instance.new("TextLabel")
    timeLabel.Size = UDim2.new(1, 0, 0.1, 0)
    timeLabel.Position = UDim2.new(0, 0, 0.6, 0)
    timeLabel.BackgroundTransparency = 1
    timeLabel.Text = "Time: " .. string.format("%.1f", results.duration) .. " seconds"
    timeLabel.TextColor3 = CONFIG.COLORS.text
    timeLabel.TextScaled = true
    timeLabel.Font = CONFIG.FONTS.body
    timeLabel.Parent = resultsFrame
    
    -- Feedback message
    local feedback = self:getFeedbackMessage(results.percentage)
    local feedbackLabel = Instance.new("TextLabel")
    feedbackLabel.Size = UDim2.new(0.8, 0, 0.15, 0)
    feedbackLabel.Position = UDim2.new(0.1, 0, 0.75, 0)
    feedbackLabel.BackgroundTransparency = 1
    feedbackLabel.Text = feedback
    feedbackLabel.TextColor3 = CONFIG.COLORS.text
    feedbackLabel.TextScaled = true
    feedbackLabel.Font = CONFIG.FONTS.body
    feedbackLabel.TextWrapped = true
    feedbackLabel.Parent = resultsFrame
    
    -- Update footer buttons
    local prevButton = self.elements.footer:FindFirstChild("PreviousButton")
    if prevButton then
        prevButton.Visible = false
    end
    
    local nextButton = self.elements.footer:FindFirstChild("NextButton")
    if nextButton then
        nextButton.Text = "Close"
        nextButton.BackgroundColor3 = CONFIG.COLORS.primary
        nextButton.MouseButton1Click:Connect(function()
            self:close()
        end)
    end
end

-- Get feedback message based on score
function QuizUI:getFeedbackMessage(percentage)
    if percentage >= 90 then
        return "Excellent work! You've mastered this topic!"
    elseif percentage >= 80 then
        return "Great job! You have a strong understanding."
    elseif percentage >= 70 then
        return "Good effort! Keep practicing to improve."
    elseif percentage >= 60 then
        return "Not bad! Review the material and try again."
    else
        return "Keep studying! You'll do better next time."
    end
end

-- Send results to server
function QuizUI:sendResults(results)
    -- This would send results to the server
    -- Implementation depends on your server setup
    local success, error = pcall(function()
        -- Example: Send via RemoteEvent
        local remoteEvent = ReplicatedStorage:FindFirstChild("QuizSubmit")
        if remoteEvent then
            remoteEvent:FireServer(results)
        end
    end)
    
    if not success then
        warn("Failed to send quiz results:", error)
    end
end

-- Animate entrance
function QuizUI:animateEntrance()
    local mainContainer = self.elements.mainContainer
    mainContainer.Position = UDim2.new(0.5, -300, 1.5, 0)
    
    local tween = TweenService:Create(
        mainContainer,
        TweenInfo.new(0.5, Enum.EasingStyle.Back, Enum.EasingDirection.Out),
        {Position = UDim2.new(0.5, -300, 0.5, -250)}
    )
    tween:Play()
end

-- Animate exit
function QuizUI:animateExit(callback)
    local mainContainer = self.elements.mainContainer
    
    local tween = TweenService:Create(
        mainContainer,
        TweenInfo.new(0.3, Enum.EasingStyle.Back, Enum.EasingDirection.In),
        {Position = UDim2.new(0.5, -300, 1.5, 0)}
    )
    
    tween.Completed:Connect(function()
        if callback then
            callback()
        end
    end)
    
    tween:Play()
end

-- Close quiz
function QuizUI:close()
    self:animateExit(function()
        self:destroy()
    end)
end

-- Destroy quiz UI
function QuizUI:destroy()
    if self.gui then
        self.gui:Destroy()
        self.gui = nil
    end
    
    self.isActive = false
    self.currentQuiz = nil
    self.elements = {}
    self.answers = {}
end

-- Check if quiz is active
function QuizUI:isQuizActive()
    return self.isActive
end

-- Get current progress
function QuizUI:getProgress()
    return {
        currentQuestion = self.currentQuestion,
        totalQuestions = self.currentQuiz and #self.currentQuiz.questions or 0,
        score = self.score,
        answers = self.answers
    }
end

return QuizUI
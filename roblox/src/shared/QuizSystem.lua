--[[
    ToolboxAI Quiz System Module
    Version: 1.0.0
    Version: 2.0.0 - Updated for Roblox 2025
    Description: Comprehensive quiz management system for educational content
                 with AI-generated questions, real-time scoring, and backend integration

    Features:
    - Multi-format question support (7 question types)
    - Real-time multiplayer quizzes
    - Advanced scoring with time bonuses and streaks
    - Backend API integration for analytics
    - FilteringEnabled compliant architecture
--]]

local QuizSystem = {}
QuizSystem.__index = QuizSystem

-- Services
local HttpService = game:GetService("HttpService")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local SoundService = game:GetService("SoundService")

-- Constants
local QUIZ_CONFIG = {
    DEFAULT_TIME_LIMIT = 30, -- seconds per question
    BASE_POINTS = 100,
    TIME_BONUS_MULTIPLIER = 2,
    HINT_PENALTY = 25,
    STREAK_BONUS = 10,
    MIN_PASS_PERCENTAGE = 70,
    MAX_HINTS_PER_QUESTION = 2,

    -- Backend Integration (2025)
    BACKEND_URL = "http://127.0.0.1:8009",
    QUIZ_ENDPOINT = "/api/v1/quiz",
    ANALYTICS_ENDPOINT = "/api/v1/analytics/quiz",
    RESULTS_ENDPOINT = "/api/v1/quiz/results"
}

-- Question Types Enum
QuizSystem.QuestionTypes = {
    MULTIPLE_CHOICE = "multiple_choice",
    TRUE_FALSE = "true_false",
    FILL_IN_BLANK = "fill_in_blank",
    MATCHING = "matching",
    ORDERING = "ordering",
    SHORT_ANSWER = "short_answer",
    DRAG_DROP = "drag_drop"
}

-- Quiz States
QuizSystem.States = {
    IDLE = "idle",
    LOADING = "loading",
    READY = "ready",
    IN_PROGRESS = "in_progress",
    QUESTION_ACTIVE = "question_active",
    REVIEWING_ANSWER = "reviewing_answer",
    SHOWING_RESULTS = "showing_results",
    COMPLETED = "completed"
}

-- Constructor
function QuizSystem.new(quizData)
    local self = setmetatable({}, QuizSystem)
    
    -- Core properties
    self.id = quizData.id or HttpService:GenerateGUID(false)
    self.title = quizData.title or "Quiz"
    self.subject = quizData.subject or "General"
    self.gradeLevel = quizData.grade_level or 5
    self.difficulty = quizData.difficulty or "medium"
    
    -- Questions
    self.questions = quizData.questions or {}
    self.currentQuestionIndex = 0
    self.totalQuestions = #self.questions
    
    -- State
    self.state = QuizSystem.States.IDLE
    self.startTime = nil
    self.endTime = nil
    self.questionStartTime = nil
    
    -- Scoring
    self.totalPoints = 0
    self.maxPossiblePoints = self:CalculateMaxPoints()
    self.passingScore = math.floor(self.maxPossiblePoints * (QUIZ_CONFIG.MIN_PASS_PERCENTAGE / 100))
    
    -- Player tracking
    self.participants = {}
    self.playerAnswers = {}
    self.playerScores = {}
    self.playerStreaks = {}
    self.playerHints = {}
    
    -- Settings
    self.settings = {
        timeLimit = quizData.time_limit or QUIZ_CONFIG.DEFAULT_TIME_LIMIT,
        allowHints = quizData.allow_hints ~= false,
        showCorrectAnswer = quizData.show_correct ~= false,
        randomizeQuestions = quizData.randomize or false,
        randomizeOptions = quizData.randomize_options or false,
        allowSkip = quizData.allow_skip or false,
        instantFeedback = quizData.instant_feedback ~= false
    }
    
    -- Remotes (assuming they exist in ReplicatedStorage)
    self.remotes = {
        submitAnswer = ReplicatedStorage:WaitForChild("Remotes"):WaitForChild("Events"):WaitForChild("SubmitAnswer"),
        requestHint = ReplicatedStorage:WaitForChild("Remotes"):WaitForChild("Events"):WaitForChild("RequestHint"),
        updateProgress = ReplicatedStorage:WaitForChild("Remotes"):WaitForChild("Events"):WaitForChild("UpdateProgress")
    }
    
    -- Timers
    self.questionTimer = nil
    self.countdownConnection = nil
    
    -- Initialize
    self:Initialize()
    
    return self
end

-- Initialize quiz
function QuizSystem:Initialize()
    -- Validate questions
    self:ValidateQuestions()
    
    -- Randomize if needed
    if self.settings.randomizeQuestions then
        self:RandomizeQuestions()
    end
    
    -- Prepare question data
    for i, question in ipairs(self.questions) do
        question.index = i
        question.points = question.points or QUIZ_CONFIG.BASE_POINTS
        
        -- Randomize options if needed
        if self.settings.randomizeOptions and question.options then
            question.options = self:ShuffleArray(question.options)
        end
    end
    
    self.state = QuizSystem.States.READY
    print(string.format("[QuizSystem] Initialized quiz '%s' with %d questions", self.title, self.totalQuestions))
end

-- Validate questions
function QuizSystem:ValidateQuestions()
    local validQuestions = {}
    
    for i, question in ipairs(self.questions) do
        local isValid = true
        
        -- Check required fields
        if not question.text or question.text == "" then
            warn(string.format("[QuizSystem] Question %d missing text", i))
            isValid = false
        end
        
        if not question.type then
            question.type = QuizSystem.QuestionTypes.MULTIPLE_CHOICE
        end
        
        if not question.correct_answer then
            warn(string.format("[QuizSystem] Question %d missing correct answer", i))
            isValid = false
        end
        
        -- Validate based on type
        if question.type == QuizSystem.QuestionTypes.MULTIPLE_CHOICE then
            if not question.options or #question.options < 2 then
                warn(string.format("[QuizSystem] Question %d needs at least 2 options", i))
                isValid = false
            end
        end
        
        if isValid then
            table.insert(validQuestions, question)
        end
    end
    
    self.questions = validQuestions
    self.totalQuestions = #validQuestions
end

-- Start quiz
function QuizSystem:Start()
    if self.state ~= QuizSystem.States.READY then
        warn("[QuizSystem] Cannot start quiz - not in ready state")
        return false
    end
    
    self.state = QuizSystem.States.IN_PROGRESS
    self.startTime = tick()
    self.currentQuestionIndex = 1
    
    -- Notify participants
    self:BroadcastToParticipants("quiz_started", {
        quiz_id = self.id,
        title = self.title,
        total_questions = self.totalQuestions
    })
    
    -- Start first question
    self:PresentQuestion()
    
    -- Report to backend
    self:ReportToBackend("quiz_started", {
        quiz_id = self.id,
        participants = self:GetParticipantIds()
    })
    
    return true
end

-- Present current question
function QuizSystem:PresentQuestion()
    if self.currentQuestionIndex > self.totalQuestions then
        self:Complete()
        return
    end
    
    local question = self.questions[self.currentQuestionIndex]
    if not question then
        warn("[QuizSystem] No question at index " .. self.currentQuestionIndex)
        return
    end
    
    self.state = QuizSystem.States.QUESTION_ACTIVE
    self.questionStartTime = tick()
    
    -- Prepare safe question data (without answer)
    local safeQuestion = {
        index = question.index,
        text = question.text,
        type = question.type,
        options = question.options,
        points = question.points,
        time_limit = self.settings.timeLimit,
        allow_hints = self.settings.allowHints,
        media = question.media -- Images, videos, etc.
    }
    
    -- Send to all participants
    self:BroadcastToParticipants("question_presented", safeQuestion)
    
    -- Start timer if time limit exists
    if self.settings.timeLimit > 0 then
        self:StartQuestionTimer()
    end
    
    print(string.format("[QuizSystem] Presenting question %d/%d", self.currentQuestionIndex, self.totalQuestions))
end

-- Start question timer
function QuizSystem:StartQuestionTimer()
    if self.countdownConnection then
        self.countdownConnection:Disconnect()
    end
    
    local timeRemaining = self.settings.timeLimit
    
    self.countdownConnection = RunService.Heartbeat:Connect(function()
        timeRemaining = timeRemaining - RunService.Heartbeat:Wait()
        
        -- Update timer display for participants
        if timeRemaining <= 0 then
            self.countdownConnection:Disconnect()
            self:OnQuestionTimeout()
        elseif timeRemaining <= 5 then
            -- Warning for last 5 seconds
            self:BroadcastToParticipants("timer_warning", {
                time_remaining = math.ceil(timeRemaining)
            })
        end
    end)
end

-- Handle question timeout
function QuizSystem:OnQuestionTimeout()
    print("[QuizSystem] Question time limit reached")
    
    -- Mark unanswered players as incorrect
    for _, player in ipairs(self.participants) do
        local playerId = tostring(player.UserId)
        if not self:HasAnswered(playerId, self.currentQuestionIndex) then
            self:RecordAnswer(player, nil, false, 0)
        end
    end
    
    -- Move to next question
    self:NextQuestion()
end

-- Submit answer
function QuizSystem:SubmitAnswer(player, answer)
    local playerId = tostring(player.UserId)
    local question = self.questions[self.currentQuestionIndex]
    
    if not question then
        return false, "No active question"
    end
    
    if self.state ~= QuizSystem.States.QUESTION_ACTIVE then
        return false, "Question not active"
    end
    
    if self:HasAnswered(playerId, self.currentQuestionIndex) then
        return false, "Already answered"
    end
    
    -- Calculate time taken
    local timeTaken = tick() - self.questionStartTime
    
    -- Check answer
    local isCorrect = self:CheckAnswer(question, answer)
    
    -- Calculate points
    local points = 0
    if isCorrect then
        points = self:CalculatePoints(question, timeTaken)
        
        -- Update streak
        self.playerStreaks[playerId] = (self.playerStreaks[playerId] or 0) + 1
        
        -- Add streak bonus
        if self.playerStreaks[playerId] >= 3 then
            points = points + (QUIZ_CONFIG.STREAK_BONUS * (self.playerStreaks[playerId] - 2))
        end
    else
        self.playerStreaks[playerId] = 0
    end
    
    -- Record answer
    self:RecordAnswer(player, answer, isCorrect, points)
    
    -- Send feedback
    if self.settings.instantFeedback then
        self:SendFeedback(player, isCorrect, question.correct_answer, points)
    end
    
    -- Check if all players have answered
    if self:AllPlayersAnswered() then
        self:NextQuestion()
    end
    
    return isCorrect, points
end

-- Check answer correctness
function QuizSystem:CheckAnswer(question, answer)
    if not answer then return false end
    
    if question.type == QuizSystem.QuestionTypes.MULTIPLE_CHOICE or
       question.type == QuizSystem.QuestionTypes.TRUE_FALSE then
        return tostring(answer) == tostring(question.correct_answer)
        
    elseif question.type == QuizSystem.QuestionTypes.FILL_IN_BLANK or
           question.type == QuizSystem.QuestionTypes.SHORT_ANSWER then
        -- Case-insensitive comparison with trimming
        local correctAnswer = string.lower(string.gsub(question.correct_answer, "^%s*(.-)%s*$", "%1"))
        local playerAnswer = string.lower(string.gsub(tostring(answer), "^%s*(.-)%s*$", "%1"))
        return correctAnswer == playerAnswer
        
    elseif question.type == QuizSystem.QuestionTypes.MATCHING then
        -- Check if all pairs match
        if type(answer) ~= "table" or type(question.correct_answer) ~= "table" then
            return false
        end
        for key, value in pairs(question.correct_answer) do
            if answer[key] ~= value then
                return false
            end
        end
        return true
        
    elseif question.type == QuizSystem.QuestionTypes.ORDERING then
        -- Check if order matches
        if type(answer) ~= "table" or type(question.correct_answer) ~= "table" then
            return false
        end
        for i, value in ipairs(question.correct_answer) do
            if answer[i] ~= value then
                return false
            end
        end
        return true
    end
    
    return false
end

-- Calculate points for correct answer
function QuizSystem:CalculatePoints(question, timeTaken)
    local basePoints = question.points or QUIZ_CONFIG.BASE_POINTS
    
    -- Time bonus (faster = more points)
    local timeBonus = 0
    if self.settings.timeLimit > 0 then
        local timePercentage = 1 - (timeTaken / self.settings.timeLimit)
        timeBonus = math.floor(basePoints * timePercentage * QUIZ_CONFIG.TIME_BONUS_MULTIPLIER * 0.1)
        timeBonus = math.max(0, timeBonus)
    end
    
    -- Difficulty multiplier
    local difficultyMultiplier = 1
    if self.difficulty == "easy" then
        difficultyMultiplier = 0.8
    elseif self.difficulty == "hard" then
        difficultyMultiplier = 1.5
    elseif self.difficulty == "expert" then
        difficultyMultiplier = 2
    end
    
    local totalPoints = math.floor((basePoints + timeBonus) * difficultyMultiplier)
    
    return totalPoints
end

-- Record player answer
function QuizSystem:RecordAnswer(player, answer, isCorrect, points)
    local playerId = tostring(player.UserId)
    
    -- Initialize player data if needed
    if not self.playerAnswers[playerId] then
        self.playerAnswers[playerId] = {}
        self.playerScores[playerId] = 0
    end
    
    -- Record answer
    self.playerAnswers[playerId][self.currentQuestionIndex] = {
        answer = answer,
        correct = isCorrect,
        points = points,
        time = tick() - self.questionStartTime,
        timestamp = tick()
    }
    
    -- Update score
    self.playerScores[playerId] = self.playerScores[playerId] + points
    
    -- Update player leaderstats
    if player:FindFirstChild("leaderstats") then
        local score = player.leaderstats:FindFirstChild("Score")
        if score then
            score.Value = self.playerScores[playerId]
        end
    end
    
    print(string.format("[QuizSystem] Player %s answered %s (+%d points)", 
                       player.Name, isCorrect and "correctly" or "incorrectly", points))
end

-- Send feedback to player
function QuizSystem:SendFeedback(player, isCorrect, correctAnswer, points)
    self.remotes.updateProgress:FireClient(player, {
        type = "quiz_feedback",
        correct = isCorrect,
        correct_answer = self.settings.showCorrectAnswer and correctAnswer or nil,
        points = points,
        total_score = self.playerScores[tostring(player.UserId)]
    })
end

-- Request hint
function QuizSystem:RequestHint(player)
    if not self.settings.allowHints then
        return false, "Hints not allowed"
    end
    
    local playerId = tostring(player.UserId)
    local question = self.questions[self.currentQuestionIndex]
    
    if not question or not question.hints then
        return false, "No hints available"
    end
    
    -- Track hint usage
    if not self.playerHints[playerId] then
        self.playerHints[playerId] = {}
    end
    
    local questionHints = self.playerHints[playerId][self.currentQuestionIndex] or 0
    
    if questionHints >= QUIZ_CONFIG.MAX_HINTS_PER_QUESTION then
        return false, "Maximum hints used"
    end
    
    -- Get next hint
    local hintIndex = questionHints + 1
    local hint = question.hints[hintIndex]
    
    if not hint then
        return false, "No more hints available"
    end
    
    -- Deduct points for hint
    local penalty = QUIZ_CONFIG.HINT_PENALTY
    self.playerScores[playerId] = math.max(0, (self.playerScores[playerId] or 0) - penalty)
    
    -- Record hint usage
    self.playerHints[playerId][self.currentQuestionIndex] = hintIndex
    
    -- Send hint to player
    self.remotes.updateProgress:FireClient(player, {
        type = "quiz_hint",
        hint = hint,
        hint_number = hintIndex,
        penalty = penalty
    })
    
    return true, hint
end

-- Move to next question
function QuizSystem:NextQuestion()
    -- Show results for current question if enabled
    if self.settings.showCorrectAnswer then
        self:ShowQuestionResults()
        task.wait(3) -- Brief pause to show results
    end
    
    self.currentQuestionIndex = self.currentQuestionIndex + 1
    
    if self.currentQuestionIndex > self.totalQuestions then
        self:Complete()
    else
        self:PresentQuestion()
    end
end

-- Show results for current question
function QuizSystem:ShowQuestionResults()
    local question = self.questions[self.currentQuestionIndex]
    if not question then return end
    
    local results = {
        question_index = self.currentQuestionIndex,
        correct_answer = question.correct_answer,
        explanation = question.explanation,
        statistics = self:GetQuestionStatistics(self.currentQuestionIndex)
    }
    
    self:BroadcastToParticipants("question_results", results)
end

-- Complete quiz
function QuizSystem:Complete()
    self.state = QuizSystem.States.COMPLETED
    self.endTime = tick()
    
    -- Calculate final results
    local results = self:CalculateFinalResults()
    
    -- Send results to participants
    self:BroadcastToParticipants("quiz_completed", results)
    
    -- Report to backend
    self:ReportToBackend("quiz_completed", results)
    
    print(string.format("[QuizSystem] Quiz '%s' completed", self.title))
end

-- Calculate final results
function QuizSystem:CalculateFinalResults()
    local results = {
        quiz_id = self.id,
        title = self.title,
        duration = self.endTime - self.startTime,
        participants = {},
        statistics = {
            average_score = 0,
            highest_score = 0,
            lowest_score = math.huge,
            pass_rate = 0,
            average_time_per_question = 0
        }
    }
    
    local totalScore = 0
    local passCount = 0
    
    for playerId, answers in pairs(self.playerAnswers) do
        local player = self:GetPlayerById(playerId)
        local playerScore = self.playerScores[playerId] or 0
        local correctCount = 0
        local totalTime = 0
        
        for _, answer in pairs(answers) do
            if answer.correct then
                correctCount = correctCount + 1
            end
            totalTime = totalTime + answer.time
        end
        
        local accuracy = (correctCount / self.totalQuestions) * 100
        local passed = playerScore >= self.passingScore
        
        if passed then
            passCount = passCount + 1
        end
        
        local playerResult = {
            player_id = playerId,
            player_name = player and player.Name or "Unknown",
            score = playerScore,
            max_score = self.maxPossiblePoints,
            percentage = (playerScore / self.maxPossiblePoints) * 100,
            correct_answers = correctCount,
            total_questions = self.totalQuestions,
            accuracy = accuracy,
            passed = passed,
            average_time = totalTime / self.totalQuestions,
            hints_used = self:GetPlayerHintCount(playerId)
        }
        
        table.insert(results.participants, playerResult)
        
        -- Update statistics
        totalScore = totalScore + playerScore
        results.statistics.highest_score = math.max(results.statistics.highest_score, playerScore)
        results.statistics.lowest_score = math.min(results.statistics.lowest_score, playerScore)
    end
    
    -- Calculate averages
    local participantCount = #results.participants
    if participantCount > 0 then
        results.statistics.average_score = totalScore / participantCount
        results.statistics.pass_rate = (passCount / participantCount) * 100
        results.statistics.average_time_per_question = results.duration / self.totalQuestions
    end
    
    return results
end

-- Utility functions
function QuizSystem:HasAnswered(playerId, questionIndex)
    return self.playerAnswers[playerId] and self.playerAnswers[playerId][questionIndex] ~= nil
end

function QuizSystem:AllPlayersAnswered()
    for _, player in ipairs(self.participants) do
        if not self:HasAnswered(tostring(player.UserId), self.currentQuestionIndex) then
            return false
        end
    end
    return true
end

function QuizSystem:GetPlayerById(playerId)
    for _, player in ipairs(self.participants) do
        if tostring(player.UserId) == playerId then
            return player
        end
    end
    return nil
end

function QuizSystem:GetParticipantIds()
    local ids = {}
    for _, player in ipairs(self.participants) do
        table.insert(ids, tostring(player.UserId))
    end
    return ids
end

function QuizSystem:GetPlayerHintCount(playerId)
    local count = 0
    if self.playerHints[playerId] then
        for _, hints in pairs(self.playerHints[playerId]) do
            count = count + hints
        end
    end
    return count
end

function QuizSystem:GetQuestionStatistics(questionIndex)
    local correct = 0
    local total = 0
    local totalTime = 0
    
    for _, answers in pairs(self.playerAnswers) do
        local answer = answers[questionIndex]
        if answer then
            total = total + 1
            if answer.correct then
                correct = correct + 1
            end
            totalTime = totalTime + answer.time
        end
    end
    
    return {
        correct_count = correct,
        total_answers = total,
        accuracy = total > 0 and (correct / total * 100) or 0,
        average_time = total > 0 and (totalTime / total) or 0
    }
end

function QuizSystem:CalculateMaxPoints()
    local maxPoints = 0
    for _, question in ipairs(self.questions) do
        maxPoints = maxPoints + (question.points or QUIZ_CONFIG.BASE_POINTS)
    end
    -- Add potential time bonuses and streak bonuses
    maxPoints = maxPoints * (1 + QUIZ_CONFIG.TIME_BONUS_MULTIPLIER * 0.1)
    return math.floor(maxPoints)
end

function QuizSystem:ShuffleArray(array)
    local shuffled = {}
    for i, v in ipairs(array) do
        shuffled[i] = v
    end
    
    for i = #shuffled, 2, -1 do
        local j = math.random(i)
        shuffled[i], shuffled[j] = shuffled[j], shuffled[i]
    end
    
    return shuffled
end

function QuizSystem:RandomizeQuestions()
    self.questions = self:ShuffleArray(self.questions)
end

-- Communication functions
function QuizSystem:BroadcastToParticipants(eventType, data)
    for _, player in ipairs(self.participants) do
        self.remotes.updateProgress:FireClient(player, {
            type = eventType,
            data = data
        })
    end
end

function QuizSystem:ReportToBackend(eventType, data)
    spawn(function()
        local requestData = {
            event = eventType,
            quiz_id = self.id,
            timestamp = tick(),
            data = data
        }
        
        pcall(function()
            HttpService:RequestAsync({
                Url = QUIZ_CONFIG.BACKEND_URL .. "/api/roblox/quiz/events",
                Method = "POST",
                Headers = {
                    ["Content-Type"] = "application/json"
                },
                Body = HttpService:JSONEncode(requestData)
            })
        end)
    end)
end

-- Player management
function QuizSystem:AddParticipant(player)
    if not table.find(self.participants, player) then
        table.insert(self.participants, player)
        
        -- Initialize player data
        local playerId = tostring(player.UserId)
        self.playerAnswers[playerId] = {}
        self.playerScores[playerId] = 0
        self.playerStreaks[playerId] = 0
        self.playerHints[playerId] = {}
        
        print(string.format("[QuizSystem] Added participant: %s", player.Name))
        return true
    end
    return false
end

function QuizSystem:RemoveParticipant(player)
    local index = table.find(self.participants, player)
    if index then
        table.remove(self.participants, index)
        print(string.format("[QuizSystem] Removed participant: %s", player.Name))
        return true
    end
    return false
end

-- Report quiz analytics to backend (2025)
function QuizSystem:ReportAnalytics(eventType, data)
    spawn(function()
        local success, response = pcall(function()
            return HttpService:RequestAsync({
                Url = QUIZ_CONFIG.BACKEND_URL .. QUIZ_CONFIG.ANALYTICS_ENDPOINT,
                Method = "POST",
                Headers = {
                    ["Content-Type"] = "application/json",
                    ["X-Quiz-System"] = "2.0"
                },
                Body = HttpService:JSONEncode({
                    quizId = self.id,
                    eventType = eventType,
                    data = data,
                    metadata = {
                        placeId = game.PlaceId,
                        universeId = game.GameId,
                        timestamp = os.time(),
                        participantCount = #self.participants
                    }
                })
            })
        end)

        if success and response.StatusCode == 200 then
            -- Analytics reported successfully
        else
            warn("[QuizSystem] Failed to report analytics:",
                 response and response.StatusMessage or "Unknown error")
        end
    end)
end

-- Submit quiz results to backend
function QuizSystem:SubmitResults()
    local results = {
        quizId = self.id,
        title = self.title,
        subject = self.subject,
        difficulty = self.difficulty,
        completedAt = os.time(),
        participants = {}
    }

    for _, player in ipairs(self.participants) do
        local userId = player.UserId
        table.insert(results.participants, {
            userId = userId,
            username = player.Name,
            score = self.playerScores[userId] or 0,
            answers = self.playerAnswers[userId] or {},
            streak = self.playerStreaks[userId] or 0,
            hintsUsed = self.playerHints[userId] or 0,
            completed = true
        })
    end

    spawn(function()
        local success, response = pcall(function()
            return HttpService:RequestAsync({
                Url = QUIZ_CONFIG.BACKEND_URL .. QUIZ_CONFIG.RESULTS_ENDPOINT,
                Method = "POST",
                Headers = {
                    ["Content-Type"] = "application/json",
                    ["X-Quiz-Results"] = "true"
                },
                Body = HttpService:JSONEncode(results)
            })
        end)

        if success and response.StatusCode == 200 then
            print("[QuizSystem] Quiz results submitted to backend successfully")
        else
            warn("[QuizSystem] Failed to submit results to backend:",
                 response and response.StatusMessage or "Unknown error")
        end
    end)
end

-- Get comprehensive quiz statistics
function QuizSystem:GetStatistics()
    local stats = {
        quizId = self.id,
        title = self.title,
        state = self.state,
        participantCount = #self.participants,
        currentQuestionIndex = self.currentQuestionIndex,
        totalQuestions = #self.questions,
        averageScore = 0,
        completionRate = 0
    }

    -- Calculate average score
    local totalScore = 0
    local completedParticipants = 0

    for _, player in ipairs(self.participants) do
        local score = self.playerScores[player.UserId] or 0
        if score > 0 then
            totalScore = totalScore + score
            completedParticipants = completedParticipants + 1
        end
    end

    if completedParticipants > 0 then
        stats.averageScore = totalScore / completedParticipants
        stats.completionRate = (completedParticipants / #self.participants) * 100
    end

    return stats
end

-- Cleanup
function QuizSystem:Cleanup()
    -- Submit final results before cleanup
    if self.state == QuizSystem.States.COMPLETED and #self.participants > 0 then
        self:SubmitResults()
    end

    -- Report cleanup analytics
    self:ReportAnalytics("quiz_cleanup", self:GetStatistics())

    if self.countdownConnection then
        self.countdownConnection:Disconnect()
    end

    self.state = QuizSystem.States.IDLE
    self.participants = {}
    self.playerAnswers = {}
    self.playerScores = {}
    self.playerStreaks = {}
    self.playerHints = {}

    print(string.format("[QuizSystem] Cleaned up quiz '%s'", self.title))
end

return QuizSystem

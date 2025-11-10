-- Dashboard API Integration Module for ToolboxAI
-- Provides comprehensive communication between Roblox Studio and the Teacher/Admin Dashboard
-- Version: 1.0.0

local HttpService = game:GetService("HttpService")
local ServerStorage = game:GetService("ServerStorage")
local Settings = nil
pcall(function()
    Settings = require(ServerStorage:WaitForChild("Config"):WaitForChild("settings"))
end)
local RunService = game:GetService("RunService")
local Players = game:GetService("Players")
local DataStoreService = game:GetService("DataStoreService")
local MessagingService = game:GetService("MessagingService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

-- Configuration
local CONFIG = {
    DASHBOARD_URL = (Settings and Settings.API and Settings.API.getDashboardUrl and Settings.API.getDashboardUrl()) or "http://127.0.0.1:5179",
    BACKEND_URL = (Settings and Settings.API and Settings.API.getBaseUrl and Settings.API.getBaseUrl()) or "http://127.0.0.1:8009",
    -- Pusher configuration (real-time via backend bridge)
    PUSHER_KEY = "${PUSHER_KEY}",
    PUSHER_CLUSTER = "${PUSHER_CLUSTER}",
    API_VERSION = "v1",
    REQUEST_TIMEOUT = 30,
    RETRY_ATTEMPTS = 3,
    RETRY_DELAY = 2,
    BATCH_SIZE = 50,
    SYNC_INTERVAL = 30, -- seconds
    CACHE_EXPIRY = 300, -- 5 minutes
}

-- Authentication state
local authState = {
    token = nil,
    refreshToken = nil,
    expiresAt = 0,
    userId = nil,
    userRole = nil,
    organizationId = nil,
}

-- Cache for API responses
local cache = {
    lessons = {},
    quizzes = {},
    students = {},
    analytics = {},
    lastSync = 0,
}

-- Active sessions tracking
local activeSessions = {}

-- WebSocket connection
local webSocketConnection = nil

-- Dashboard API Module
local DashboardAPI = {}
DashboardAPI.__index = DashboardAPI

-- Constructor
function DashboardAPI.new(config)
    local self = setmetatable({}, DashboardAPI)
    self.config = config or CONFIG
    self.isInitialized = false
    self.syncEnabled = false
    self.eventQueue = {}
    self.pendingRequests = {}
    return self
end

-- Initialize the API connection
function DashboardAPI:initialize()
    if self.isInitialized then
        return true
    end
    
    local success = self:authenticate()
    if success then
        self.isInitialized = true
        self:setupRealtime()
        self:startSyncLoop()
        self:registerEventHandlers()
        print("[DashboardAPI] Initialized successfully")
        return true
    else
        warn("[DashboardAPI] Failed to initialize")
        return false
    end
end

-- Authentication
function DashboardAPI:authenticate(username, password)
    local credentials = username and password and {
        username = username,
        password = password
    } or {
        -- Use environment-based credentials for Studio
        api_key = self.config.API_KEY or "studio_api_key",
        studio_id = plugin and plugin:GetStudioUserId() or "unknown",
        place_id = game.PlaceId,
    }
    
    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = self.config.BACKEND_URL .. "/auth/studio-login",
            Method = "POST",
            Headers = {
                ["Content-Type"] = "application/json",
                ["X-Studio-Version"] = VERSION or "2024.1",
            },
            Body = HttpService:JSONEncode(credentials)
        })
    end)
    
    if success and response.Success then
        local data = HttpService:JSONDecode(response.Body)
        authState.token = data.access_token
        authState.refreshToken = data.refresh_token
        authState.expiresAt = tick() + (data.expires_in or 3600)
        authState.userId = data.user_id
        authState.userRole = data.role
        authState.organizationId = data.organization_id
        
        print("[DashboardAPI] Authentication successful")
        return true
    else
        warn("[DashboardAPI] Authentication failed:", response and response.Body or "Unknown error")
        return false
    end
end

-- Refresh authentication token
function DashboardAPI:refreshAuth()
    if not authState.refreshToken then
        return self:authenticate()
    end
    
    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = self.config.BACKEND_URL .. "/auth/refresh",
            Method = "POST",
            Headers = {
                ["Content-Type"] = "application/json",
                ["Authorization"] = "Bearer " .. authState.refreshToken
            }
        })
    end)
    
    if success and response.Success then
        local data = HttpService:JSONDecode(response.Body)
        authState.token = data.access_token
        authState.expiresAt = tick() + (data.expires_in or 3600)
        return true
    else
        return self:authenticate()
    end
end

-- Check and refresh auth if needed
function DashboardAPI:ensureAuth()
    if tick() >= authState.expiresAt - 60 then
        return self:refreshAuth()
    end
    return authState.token ~= nil
end

-- Setup Pusher-based realtime via backend bridge
function DashboardAPI:setupRealtime()
    -- No native Pusher client in Roblox; rely on backend bridge and polling if needed
    print("[DashboardAPI] Realtime initialized (Pusher via backend bridge)")
end

-- Handle incoming realtime messages (from backend bridge if used)
function DashboardAPI:handleRealtimeMessage(data)
    if not data then return end
    local eventType = data.type
    local payload = data.payload
    
    if eventType == "content_update" then
        self:handleContentUpdate(payload)
    elseif eventType == "quiz_submission" then
        self:handleQuizSubmission(payload)
    elseif eventType == "student_progress" then
        self:handleStudentProgress(payload)
    elseif eventType == "teacher_command" then
        self:handleTeacherCommand(payload)
    elseif eventType == "sync_request" then
        self:performSync()
    else
        print("[DashboardAPI] Unknown realtime event:", eventType)
    end
end

-- Educational Content Management

-- Get lesson content from dashboard
function DashboardAPI:getLesson(lessonId)
    if not self:ensureAuth() then
        return nil, "Authentication required"
    end
    
    -- Check cache first
    local cached = cache.lessons[lessonId]
    if cached and tick() - cached.timestamp < self.config.CACHE_EXPIRY then
        return cached.data
    end
    
    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = self.config.BACKEND_URL .. "/lessons/" .. lessonId,
            Method = "GET",
            Headers = {
                ["Authorization"] = "Bearer " .. authState.token,
                ["Content-Type"] = "application/json"
            }
        })
    end)
    
    if success and response.Success then
        local data = HttpService:JSONDecode(response.Body)
        cache.lessons[lessonId] = {
            data = data,
            timestamp = tick()
        }
        return data
    else
        return nil, response and response.Body or "Request failed"
    end
end

-- Create new lesson
function DashboardAPI:createLesson(lessonData)
    if not self:ensureAuth() then
        return nil, "Authentication required"
    end
    
    local payload = {
        title = lessonData.title,
        subject = lessonData.subject,
        grade_level = lessonData.gradeLevel,
        objectives = lessonData.objectives,
        content = lessonData.content,
        environment_type = lessonData.environmentType,
        duration = lessonData.duration,
        created_by = authState.userId,
        organization_id = authState.organizationId,
        metadata = {
            roblox_place_id = game.PlaceId,
            studio_version = VERSION,
            created_at = os.date("!%Y-%m-%dT%H:%M:%SZ")
        }
    }
    
    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = self.config.BACKEND_URL .. "/lessons",
            Method = "POST",
            Headers = {
                ["Authorization"] = "Bearer " .. authState.token,
                ["Content-Type"] = "application/json"
            },
            Body = HttpService:JSONEncode(payload)
        })
    end)
    
    if success and response.Success then
        local data = HttpService:JSONDecode(response.Body)
        -- Trigger agent pipeline for content generation
        self:triggerContentGeneration(data.id, lessonData)
        return data
    else
        return nil, response and response.Body or "Request failed"
    end
end

-- Quiz Management

-- Submit quiz results
function DashboardAPI:submitQuizResults(quizId, studentId, results)
    if not self:ensureAuth() then
        return nil, "Authentication required"
    end
    
    local payload = {
        quiz_id = quizId,
        student_id = studentId,
        answers = results.answers,
        score = results.score,
        time_spent = results.timeSpent,
        completed_at = os.date("!%Y-%m-%dT%H:%M:%SZ"),
        metadata = {
            place_id = game.PlaceId,
            session_id = results.sessionId,
            attempt_number = results.attemptNumber or 1
        }
    }
    
    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = self.config.BACKEND_URL .. "/quiz-submissions",
            Method = "POST",
            Headers = {
                ["Authorization"] = "Bearer " .. authState.token,
                ["Content-Type"] = "application/json"
            },
            Body = HttpService:JSONEncode(payload)
        })
    end)
    
    if success and response.Success then
        local data = HttpService:JSONDecode(response.Body)
        -- Update local analytics
        self:updateAnalytics("quiz_completion", {
            quiz_id = quizId,
            student_id = studentId,
            score = results.score
        })
        return data
    else
        return nil, response and response.Body or "Request failed"
    end
end

-- Get quiz by ID
function DashboardAPI:getQuiz(quizId)
    if not self:ensureAuth() then
        return nil, "Authentication required"
    end
    
    -- Check cache
    local cached = cache.quizzes[quizId]
    if cached and tick() - cached.timestamp < self.config.CACHE_EXPIRY then
        return cached.data
    end
    
    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = self.config.BACKEND_URL .. "/quizzes/" .. quizId,
            Method = "GET",
            Headers = {
                ["Authorization"] = "Bearer " .. authState.token,
                ["Content-Type"] = "application/json"
            }
        })
    end)
    
    if success and response.Success then
        local data = HttpService:JSONDecode(response.Body)
        cache.quizzes[quizId] = {
            data = data,
            timestamp = tick()
        }
        return data
    else
        return nil, response and response.Body or "Request failed"
    end
end

-- Student Progress Tracking

-- Update student progress
function DashboardAPI:updateStudentProgress(studentId, progressData)
    if not self:ensureAuth() then
        return nil, "Authentication required"
    end
    
    local payload = {
        student_id = studentId,
        lesson_id = progressData.lessonId,
        progress_percentage = progressData.percentage,
        milestones_completed = progressData.milestones,
        time_spent = progressData.timeSpent,
        interactions = progressData.interactions,
        updated_at = os.date("!%Y-%m-%dT%H:%M:%SZ"),
        metadata = {
            place_id = game.PlaceId,
            session_id = progressData.sessionId
        }
    }
    
    -- Queue for batch update
    table.insert(self.eventQueue, {
        type = "progress_update",
        payload = payload
    })
    
    -- Send immediately if queue is full
    if #self.eventQueue >= self.config.BATCH_SIZE then
        self:flushEventQueue()
    end
    
    return true
end

-- Get student analytics
function DashboardAPI:getStudentAnalytics(studentId, dateRange)
    if not self:ensureAuth() then
        return nil, "Authentication required"
    end
    
    local params = HttpService:UrlEncode({
        start_date = dateRange and dateRange.start or "",
        end_date = dateRange and dateRange.end_date or "",
        metrics = "all"
    })
    
    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = self.config.BACKEND_URL .. "/analytics/student/" .. studentId .. "?" .. params,
            Method = "GET",
            Headers = {
                ["Authorization"] = "Bearer " .. authState.token,
                ["Content-Type"] = "application/json"
            }
        })
    end)
    
    if success and response.Success then
        return HttpService:JSONDecode(response.Body)
    else
        return nil, response and response.Body or "Request failed"
    end
end

-- Classroom Management

-- Start classroom session
function DashboardAPI:startClassroomSession(sessionData)
    if not self:ensureAuth() then
        return nil, "Authentication required"
    end
    
    local payload = {
        lesson_id = sessionData.lessonId,
        teacher_id = authState.userId,
        classroom_id = sessionData.classroomId,
        max_students = sessionData.maxStudents or 30,
        session_type = sessionData.sessionType or "interactive",
        started_at = os.date("!%Y-%m-%dT%H:%M:%SZ"),
        metadata = {
            place_id = game.PlaceId,
            server_id = game.JobId
        }
    }
    
    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = self.config.BACKEND_URL .. "/sessions",
            Method = "POST",
            Headers = {
                ["Authorization"] = "Bearer " .. authState.token,
                ["Content-Type"] = "application/json"
            },
            Body = HttpService:JSONEncode(payload)
        })
    end)
    
    if success and response.Success then
        local data = HttpService:JSONDecode(response.Body)
        activeSessions[data.id] = data
        self:broadcastSessionStart(data)
        return data
    else
        return nil, response and response.Body or "Request failed"
    end
end

-- End classroom session
function DashboardAPI:endClassroomSession(sessionId)
    if not self:ensureAuth() then
        return nil, "Authentication required"
    end
    
    local session = activeSessions[sessionId]
    if not session then
        return nil, "Session not found"
    end
    
    local payload = {
        ended_at = os.date("!%Y-%m-%dT%H:%M:%SZ"),
        summary = self:generateSessionSummary(sessionId)
    }
    
    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = self.config.BACKEND_URL .. "/sessions/" .. sessionId .. "/end",
            Method = "PUT",
            Headers = {
                ["Authorization"] = "Bearer " .. authState.token,
                ["Content-Type"] = "application/json"
            },
            Body = HttpService:JSONEncode(payload)
        })
    end)
    
    if success and response.Success then
        activeSessions[sessionId] = nil
        return HttpService:JSONDecode(response.Body)
    else
        return nil, response and response.Body or "Request failed"
    end
end

-- Real-time Synchronization

-- Start synchronization loop
function DashboardAPI:startSyncLoop()
    if self.syncEnabled then
        return
    end
    
    self.syncEnabled = true
    
    spawn(function()
        while self.syncEnabled do
            wait(self.config.SYNC_INTERVAL)
            self:performSync()
        end
    end)
end

-- Perform synchronization
function DashboardAPI:performSync()
    if not self:ensureAuth() then
        return
    end
    
    -- Flush pending events
    self:flushEventQueue()
    
    -- Sync active sessions
    for sessionId, session in pairs(activeSessions) do
        self:syncSessionData(sessionId)
    end
    
    -- Update cache
    self:updateCache()
    
    cache.lastSync = tick()
end

-- Flush event queue
function DashboardAPI:flushEventQueue()
    if #self.eventQueue == 0 then
        return
    end
    
    local events = self.eventQueue
    self.eventQueue = {}
    
    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = self.config.BACKEND_URL .. "/events/batch",
            Method = "POST",
            Headers = {
                ["Authorization"] = "Bearer " .. authState.token,
                ["Content-Type"] = "application/json"
            },
            Body = HttpService:JSONEncode({
                events = events,
                timestamp = os.date("!%Y-%m-%dT%H:%M:%SZ")
            })
        })
    end)
    
    if not success or not response.Success then
        -- Re-queue events on failure
        for _, event in ipairs(events) do
            table.insert(self.eventQueue, event)
        end
        warn("[DashboardAPI] Failed to flush event queue")
    end
end

-- Agent Integration

-- Trigger content generation through agents
function DashboardAPI:triggerContentGeneration(lessonId, config)
    if not self:ensureAuth() then
        return nil, "Authentication required"
    end
    
    local payload = {
        request_id = HttpService:GenerateGUID(false),
        event_type = "content_generation",
        lesson_id = lessonId,
        config = config,
        context = {
            user_id = authState.userId,
            organization_id = authState.organizationId,
            place_id = game.PlaceId
        }
    }
    
    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = self.config.BACKEND_URL .. "/plugin/trigger-agents",
            Method = "POST",
            Headers = {
                ["Authorization"] = "Bearer " .. authState.token,
                ["Content-Type"] = "application/json"
            },
            Body = HttpService:JSONEncode(payload)
        })
    end)
    
    if success and response.Success then
        local data = HttpService:JSONDecode(response.Body)
        self.pendingRequests[payload.request_id] = {
            lessonId = lessonId,
            timestamp = tick()
        }
        return data
    else
        return nil, response and response.Body or "Request failed"
    end
end

-- Handle agent response
function DashboardAPI:handleAgentResponse(requestId, response)
    local request = self.pendingRequests[requestId]
    if not request then
        warn("[DashboardAPI] Unknown request ID:", requestId)
        return
    end
    
    self.pendingRequests[requestId] = nil
    
    if response.status == "success" then
        -- Update lesson with generated content
        self:updateLesson(request.lessonId, {
            generated_content = response.content,
            status = "ready"
        })
        
        -- Notify dashboard
        self:sendWebSocketMessage({
            type = "content_ready",
            payload = {
                lesson_id = request.lessonId,
                request_id = requestId
            }
        })
    else
        warn("[DashboardAPI] Agent request failed:", response.error)
    end
end

-- Utility Functions

-- Send realtime event via backend (Pusher trigger handled server-side)
function DashboardAPI:sendWebSocketMessage(message)
    -- Queue as generic event; backend can flush to Pusher
    table.insert(self.eventQueue, {
        type = "realtime_event",
        payload = message,
        timestamp = os.date("!%Y-%m-%dT%H:%M:%SZ")
    })
    -- Opportunistically flush
    self:flushEventQueue()
end

-- Update analytics
function DashboardAPI:updateAnalytics(eventType, data)
    table.insert(self.eventQueue, {
        type = "analytics",
        event_type = eventType,
        data = data,
        timestamp = tick()
    })
end

-- Generate session summary
function DashboardAPI:generateSessionSummary(sessionId)
    local session = activeSessions[sessionId]
    if not session then
        return {}
    end
    
    return {
        duration = tick() - session.started_at,
        students_joined = session.students_count or 0,
        activities_completed = session.activities_completed or 0,
        average_engagement = session.average_engagement or 0,
        quiz_results = session.quiz_results or {}
    }
end

-- Update cache
function DashboardAPI:updateCache()
    -- Clean expired cache entries
    local now = tick()
    
    for id, entry in pairs(cache.lessons) do
        if now - entry.timestamp > self.config.CACHE_EXPIRY then
            cache.lessons[id] = nil
        end
    end
    
    for id, entry in pairs(cache.quizzes) do
        if now - entry.timestamp > self.config.CACHE_EXPIRY then
            cache.quizzes[id] = nil
        end
    end
end

-- Event Handlers

-- Register event handlers
function DashboardAPI:registerEventHandlers()
    -- Handle player joins
    Players.PlayerAdded:Connect(function(player)
        self:onPlayerJoined(player)
    end)
    
    -- Handle player leaves
    Players.PlayerRemoving:Connect(function(player)
        self:onPlayerLeft(player)
    end)
    
    -- Listen for remote events if they exist
    local remoteEvents = ReplicatedStorage:FindFirstChild("DashboardEvents")
    if remoteEvents then
        local progressEvent = remoteEvents:FindFirstChild("ProgressUpdate")
        if progressEvent then
            progressEvent.OnServerEvent:Connect(function(player, data)
                self:updateStudentProgress(player.UserId, data)
            end)
        end
        
        local quizEvent = remoteEvents:FindFirstChild("QuizSubmit")
        if quizEvent then
            quizEvent.OnServerEvent:Connect(function(player, quizId, results)
                self:submitQuizResults(quizId, player.UserId, results)
            end)
        end
    end
end

-- Handle player joined
function DashboardAPI:onPlayerJoined(player)
    -- Track student join in active sessions
    for sessionId, session in pairs(activeSessions) do
        self:updateAnalytics("student_joined", {
            session_id = sessionId,
            student_id = player.UserId,
            student_name = player.Name
        })
    end
end

-- Handle player left
function DashboardAPI:onPlayerLeft(player)
    -- Track student leave in active sessions
    for sessionId, session in pairs(activeSessions) do
        self:updateAnalytics("student_left", {
            session_id = sessionId,
            student_id = player.UserId,
            duration = player:GetNetworkPing() -- Example metric
        })
    end
end

-- Handle content update from dashboard
function DashboardAPI:handleContentUpdate(payload)
    local lessonId = payload.lesson_id
    local content = payload.content
    
    -- Update local cache
    if cache.lessons[lessonId] then
        cache.lessons[lessonId].data = content
        cache.lessons[lessonId].timestamp = tick()
    end
    
    -- Trigger in-game update
    local updateEvent = ReplicatedStorage:FindFirstChild("ContentUpdate")
    if updateEvent then
        updateEvent:FireAllClients(lessonId, content)
    end
end

-- Handle quiz submission from dashboard
function DashboardAPI:handleQuizSubmission(payload)
    print("[DashboardAPI] Quiz submission received:", payload.quiz_id)
end

-- Handle student progress from dashboard
function DashboardAPI:handleStudentProgress(payload)
    print("[DashboardAPI] Student progress update:", payload.student_id)
end

-- Handle teacher command from dashboard
function DashboardAPI:handleTeacherCommand(payload)
    local command = payload.command
    local params = payload.params
    
    if command == "pause_lesson" then
        -- Pause current lesson
        print("[DashboardAPI] Pausing lesson")
    elseif command == "skip_activity" then
        -- Skip to next activity
        print("[DashboardAPI] Skipping activity")
    elseif command == "send_message" then
        -- Broadcast message to students
        local message = params.message
        print("[DashboardAPI] Broadcasting:", message)
    end
end

-- Broadcast session start
function DashboardAPI:broadcastSessionStart(sessionData)
    self:sendWebSocketMessage({ type = "session_started", payload = sessionData })
end

-- Update lesson
function DashboardAPI:updateLesson(lessonId, updates)
    if not self:ensureAuth() then
        return nil, "Authentication required"
    end
    
    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = self.config.BACKEND_URL .. "/lessons/" .. lessonId,
            Method = "PATCH",
            Headers = {
                ["Authorization"] = "Bearer " .. authState.token,
                ["Content-Type"] = "application/json"
            },
            Body = HttpService:JSONEncode(updates)
        })
    end)
    
    if success and response.Success then
        return HttpService:JSONDecode(response.Body)
    else
        return nil, response and response.Body or "Request failed"
    end
end

-- Cleanup
function DashboardAPI:cleanup()
    self.syncEnabled = false
    
    -- No WebSocket to close when using Pusher bridge
    
    -- Flush remaining events
    self:flushEventQueue()
    
    -- Clear cache
    cache = {
        lessons = {},
        quizzes = {},
        students = {},
        analytics = {},
        lastSync = 0
    }
    
    -- Clear sessions
    activeSessions = {}
    
    print("[DashboardAPI] Cleaned up")
end

-- Export module
return DashboardAPI

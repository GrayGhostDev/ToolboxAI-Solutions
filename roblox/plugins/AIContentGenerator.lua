--[[
    ToolboxAI Content Generator Plugin for Roblox Studio
    Version: 1.1.0
    Description: AI-powered educational content generation plugin that connects
                 to the ToolboxAI backend for real-time content creation
    
    Features:
    - Real-time WebSocket connection to backend
    - AI-powered content generation
    - Educational environment creation
    - Quiz and assessment integration
    - Live progress tracking
    - Robust HTTP polling fallback
    - Message queuing for offline scenarios
--]]

-- Services
local HttpService = game:GetService("HttpService")
local Selection = game:GetService("Selection")
local ChangeHistoryService = game:GetService("ChangeHistoryService")
local StudioService = game:GetService("StudioService")
local RunService = game:GetService("RunService")
local CoreGui = game:GetService("CoreGui")

-- Configuration
local CONFIG = {
    PLUGIN_NAME = "ToolboxAI Content Generator",
    PLUGIN_VERSION = "1.1.0",
    BACKEND_URL = "http://127.0.0.1:5001",  -- Flask bridge server
    API_URL = "http://127.0.0.1:8008",      -- FastAPI main server
    WEBSOCKET_URL = "ws://127.0.0.1:9876",  -- MCP WebSocket server
    PLUGIN_PORT = 64989,
    HEARTBEAT_INTERVAL = 30,  -- seconds
    RECONNECT_INTERVAL = 5,   -- seconds
    POLLING_INTERVAL = 2,     -- seconds for HTTP polling
    MAX_RECONNECT_ATTEMPTS = 10,
    MAX_QUEUE_SIZE = 100,     -- Maximum messages in offline queue
    JWT_TOKEN = nil,  -- Will be set after authentication
    STUDIO_ID = game:GetService("RbxAnalyticsService"):GetClientId() or "unknown"
}

-- Plugin State
local PluginState = {
    connected = false,
    authenticated = false,
    sessionId = nil,
    userId = nil,
    reconnectAttempts = 0,
    activeRequests = {},
    generatedContent = {},
    settings = {
        autoApplyContent = false,
        showNotifications = true,
        debugMode = false
    }
}

-- Enhanced WebSocket Manager with robust fallback and queuing
local WebSocketManager = {
    connection = nil,
    isAvailable = false,
    pollingActive = false,
    pollingInterval = CONFIG.POLLING_INTERVAL,
    lastMessageId = 0,
    messageQueue = {},
    offlineQueue = {},
    reconnectAttempts = 0,
    maxReconnectAttempts = 5,
    connectionState = "disconnected", -- disconnected, connecting, connected, polling
    lastSuccessfulConnection = 0,
    healthCheckInterval = 10 -- seconds
}

-- Create Plugin UI
local toolbar = plugin:CreateToolbar(CONFIG.PLUGIN_NAME)
local mainButton = toolbar:CreateButton(
    "Generate Content",
    "Open AI Content Generator",
    "rbxasset://textures/ui/GuiImagePlaceholder.png"
)

-- Plugin Widget
local widgetInfo = DockWidgetPluginGuiInfo.new(
    Enum.InitialDockState.Float,
    true,   -- Widget will be initially enabled
    false,  -- Don't override the previous enabled state
    450,    -- Default width
    600,    -- Default height
    400,    -- Minimum width
    300     -- Minimum height
)

local pluginWidget = plugin:CreateDockWidgetPluginGui("AIContentGenerator", widgetInfo)
pluginWidget.Title = "AI Content Generator"
pluginWidget.Name = "AIContentGeneratorWidget"

-- Create main frame
local mainFrame = Instance.new("Frame")
mainFrame.Size = UDim2.new(1, 0, 1, 0)
mainFrame.BackgroundColor3 = Color3.fromRGB(46, 46, 46)
mainFrame.BorderSizePixel = 0
mainFrame.Parent = pluginWidget

-- Header Frame
local headerFrame = Instance.new("Frame")
headerFrame.Size = UDim2.new(1, 0, 0, 60)
headerFrame.BackgroundColor3 = Color3.fromRGB(35, 35, 35)
headerFrame.BorderSizePixel = 0
headerFrame.Parent = mainFrame

-- Title Label
local titleLabel = Instance.new("TextLabel")
titleLabel.Size = UDim2.new(0.7, 0, 1, 0)
titleLabel.Position = UDim2.new(0, 10, 0, 0)
titleLabel.BackgroundTransparency = 1
titleLabel.Text = "🤖 AI Content Generator"
titleLabel.TextColor3 = Color3.new(1, 1, 1)
titleLabel.TextScaled = true
titleLabel.Font = Enum.Font.SourceSansBold
titleLabel.TextXAlignment = Enum.TextXAlignment.Left
titleLabel.Parent = headerFrame

-- Connection Status with detailed state
local statusLabel = Instance.new("TextLabel")
statusLabel.Size = UDim2.new(0.3, -10, 0, 20)
statusLabel.Position = UDim2.new(0.7, 0, 0.5, -10)
statusLabel.BackgroundColor3 = Color3.fromRGB(255, 100, 100)
statusLabel.Text = "Initializing..."
statusLabel.TextColor3 = Color3.new(1, 1, 1)
statusLabel.Font = Enum.Font.SourceSans
statusLabel.TextScaled = true
statusLabel.Parent = headerFrame

-- Content Frame (Scrollable)
local scrollFrame = Instance.new("ScrollingFrame")
scrollFrame.Size = UDim2.new(1, -20, 1, -140)
scrollFrame.Position = UDim2.new(0, 10, 0, 70)
scrollFrame.BackgroundColor3 = Color3.fromRGB(56, 56, 56)
scrollFrame.BorderSizePixel = 0
scrollFrame.ScrollBarThickness = 8
scrollFrame.CanvasSize = UDim2.new(0, 0, 2, 0)
scrollFrame.Parent = mainFrame

-- Subject Selection
local subjectLabel = Instance.new("TextLabel")
subjectLabel.Size = UDim2.new(1, -20, 0, 30)
subjectLabel.Position = UDim2.new(0, 10, 0, 10)
subjectLabel.BackgroundTransparency = 1
subjectLabel.Text = "Subject:"
subjectLabel.TextColor3 = Color3.new(0.9, 0.9, 0.9)
subjectLabel.Font = Enum.Font.SourceSans
subjectLabel.TextSize = 16
subjectLabel.TextXAlignment = Enum.TextXAlignment.Left
subjectLabel.Parent = scrollFrame

local subjectBox = Instance.new("TextBox")
subjectBox.Size = UDim2.new(1, -20, 0, 35)
subjectBox.Position = UDim2.new(0, 10, 0, 40)
subjectBox.BackgroundColor3 = Color3.fromRGB(70, 70, 70)
subjectBox.BorderSizePixel = 0
subjectBox.Text = "Mathematics"
subjectBox.TextColor3 = Color3.new(1, 1, 1)
subjectBox.Font = Enum.Font.SourceSans
subjectBox.TextSize = 14
subjectBox.PlaceholderText = "Enter subject..."
subjectBox.Parent = scrollFrame

-- Grade Level
local gradeLabel = Instance.new("TextLabel")
gradeLabel.Size = UDim2.new(1, -20, 0, 30)
gradeLabel.Position = UDim2.new(0, 10, 0, 85)
gradeLabel.BackgroundTransparency = 1
gradeLabel.Text = "Grade Level:"
gradeLabel.TextColor3 = Color3.new(0.9, 0.9, 0.9)
gradeLabel.Font = Enum.Font.SourceSans
gradeLabel.TextSize = 16
gradeLabel.TextXAlignment = Enum.TextXAlignment.Left
gradeLabel.Parent = scrollFrame

local gradeBox = Instance.new("TextBox")
gradeBox.Size = UDim2.new(1, -20, 0, 35)
gradeBox.Position = UDim2.new(0, 10, 0, 115)
gradeBox.BackgroundColor3 = Color3.fromRGB(70, 70, 70)
gradeBox.BorderSizePixel = 0
gradeBox.Text = "5"
gradeBox.TextColor3 = Color3.new(1, 1, 1)
gradeBox.Font = Enum.Font.SourceSans
gradeBox.TextSize = 14
gradeBox.PlaceholderText = "Enter grade level (1-12)..."
gradeBox.Parent = scrollFrame

-- Learning Objectives
local objectivesLabel = Instance.new("TextLabel")
objectivesLabel.Size = UDim2.new(1, -20, 0, 30)
objectivesLabel.Position = UDim2.new(0, 10, 0, 160)
objectivesLabel.BackgroundTransparency = 1
objectivesLabel.Text = "Learning Objectives:"
objectivesLabel.TextColor3 = Color3.new(0.9, 0.9, 0.9)
objectivesLabel.Font = Enum.Font.SourceSans
objectivesLabel.TextSize = 16
objectivesLabel.TextXAlignment = Enum.TextXAlignment.Left
objectivesLabel.Parent = scrollFrame

local objectivesBox = Instance.new("TextBox")
objectivesBox.Size = UDim2.new(1, -20, 0, 60)
objectivesBox.Position = UDim2.new(0, 10, 0, 190)
objectivesBox.BackgroundColor3 = Color3.fromRGB(70, 70, 70)
objectivesBox.BorderSizePixel = 0
objectivesBox.Text = "Fractions, Decimals, Percentages"
objectivesBox.TextColor3 = Color3.new(1, 1, 1)
objectivesBox.Font = Enum.Font.SourceSans
objectivesBox.TextSize = 14
objectivesBox.TextWrapped = true
objectivesBox.MultiLine = true
objectivesBox.PlaceholderText = "Enter learning objectives (comma separated)..."
objectivesBox.Parent = scrollFrame

-- Environment Type
local envLabel = Instance.new("TextLabel")
envLabel.Size = UDim2.new(1, -20, 0, 30)
envLabel.Position = UDim2.new(0, 10, 0, 260)
envLabel.BackgroundTransparency = 1
envLabel.Text = "Environment Type:"
envLabel.TextColor3 = Color3.new(0.9, 0.9, 0.9)
envLabel.Font = Enum.Font.SourceSans
envLabel.TextSize = 16
envLabel.TextXAlignment = Enum.TextXAlignment.Left
envLabel.Parent = scrollFrame

local envBox = Instance.new("TextBox")
envBox.Size = UDim2.new(1, -20, 0, 35)
envBox.Position = UDim2.new(0, 10, 0, 290)
envBox.BackgroundColor3 = Color3.fromRGB(70, 70, 70)
envBox.BorderSizePixel = 0
envBox.Text = "interactive_classroom"
envBox.TextColor3 = Color3.new(1, 1, 1)
envBox.Font = Enum.Font.SourceSans
envBox.TextSize = 14
envBox.PlaceholderText = "classroom, outdoor, laboratory, space..."
envBox.Parent = scrollFrame

-- Include Quiz Checkbox
local quizFrame = Instance.new("Frame")
quizFrame.Size = UDim2.new(1, -20, 0, 35)
quizFrame.Position = UDim2.new(0, 10, 0, 335)
quizFrame.BackgroundTransparency = 1
quizFrame.Parent = scrollFrame

local quizCheckbox = Instance.new("TextButton")
quizCheckbox.Size = UDim2.new(0, 25, 0, 25)
quizCheckbox.Position = UDim2.new(0, 0, 0, 5)
quizCheckbox.BackgroundColor3 = Color3.fromRGB(70, 70, 70)
quizCheckbox.BorderSizePixel = 2
quizCheckbox.BorderColor3 = Color3.new(0.5, 0.5, 0.5)
quizCheckbox.Text = "✓"
quizCheckbox.TextColor3 = Color3.new(0, 1, 0)
quizCheckbox.Font = Enum.Font.SourceSansBold
quizCheckbox.TextSize = 20
quizCheckbox.Parent = quizFrame

local quizLabel = Instance.new("TextLabel")
quizLabel.Size = UDim2.new(1, -35, 1, 0)
quizLabel.Position = UDim2.new(0, 35, 0, 0)
quizLabel.BackgroundTransparency = 1
quizLabel.Text = "Include Quiz/Assessment"
quizLabel.TextColor3 = Color3.new(0.9, 0.9, 0.9)
quizLabel.Font = Enum.Font.SourceSans
quizLabel.TextSize = 16
quizLabel.TextXAlignment = Enum.TextXAlignment.Left
quizLabel.Parent = quizFrame

-- Progress Bar
local progressFrame = Instance.new("Frame")
progressFrame.Size = UDim2.new(1, -20, 0, 30)
progressFrame.Position = UDim2.new(0, 10, 0, 380)
progressFrame.BackgroundColor3 = Color3.fromRGB(50, 50, 50)
progressFrame.BorderSizePixel = 0
progressFrame.Visible = false
progressFrame.Parent = scrollFrame

local progressBar = Instance.new("Frame")
progressBar.Size = UDim2.new(0, 0, 1, 0)
progressBar.BackgroundColor3 = Color3.fromRGB(0, 170, 255)
progressBar.BorderSizePixel = 0
progressBar.Parent = progressFrame

local progressLabel = Instance.new("TextLabel")
progressLabel.Size = UDim2.new(1, 0, 1, 0)
progressLabel.BackgroundTransparency = 1
progressLabel.Text = "Generating content..."
progressLabel.TextColor3 = Color3.new(1, 1, 1)
progressLabel.Font = Enum.Font.SourceSans
progressLabel.TextSize = 14
progressLabel.Parent = progressFrame

-- Generate Button
local generateButton = Instance.new("TextButton")
generateButton.Size = UDim2.new(1, -20, 0, 45)
generateButton.Position = UDim2.new(0, 10, 1, -55)
generateButton.BackgroundColor3 = Color3.fromRGB(0, 170, 255)
generateButton.BorderSizePixel = 0
generateButton.Text = "🚀 Generate Content"
generateButton.TextColor3 = Color3.new(1, 1, 1)
generateButton.Font = Enum.Font.SourceSansBold
generateButton.TextSize = 18
generateButton.Parent = mainFrame

-- Utility Functions
local function debugLog(message)
    if PluginState.settings.debugMode then
        print(string.format("[%s DEBUG] %s", CONFIG.PLUGIN_NAME, message))
    end
end

local function updateConnectionStatus(connected, connectionType)
    PluginState.connected = connected
    local displayText = "Disconnected"
    local color = Color3.fromRGB(255, 100, 100)
    
    if connected then
        if connectionType == "websocket" then
            displayText = "WebSocket Connected"
            color = Color3.fromRGB(100, 255, 100)
            WebSocketManager.connectionState = "connected"
        elseif connectionType == "polling" then
            displayText = "HTTP Polling"
            color = Color3.fromRGB(255, 200, 100)
            WebSocketManager.connectionState = "polling"
        else
            displayText = "Connected"
            color = Color3.fromRGB(100, 255, 100)
        end
    else
        WebSocketManager.connectionState = "disconnected"
    end
    
    statusLabel.Text = displayText
    statusLabel.BackgroundColor3 = color
    debugLog(string.format("Connection status updated: %s (%s)", displayText, connectionType or "unknown"))
end

local function showNotification(message, notificationType)
    if not PluginState.settings.showNotifications then return end
    
    local color = Color3.new(1, 1, 1)
    if notificationType == "success" then
        color = Color3.fromRGB(100, 255, 100)
    elseif notificationType == "error" then
        color = Color3.fromRGB(255, 100, 100)
    elseif notificationType == "warning" then
        color = Color3.fromRGB(255, 200, 100)
    elseif notificationType == "info" then
        color = Color3.fromRGB(100, 200, 255)
    end
    
    print(string.format("[%s] %s", CONFIG.PLUGIN_NAME, message))
    
    -- Create visual notification with auto-removal
    spawn(function()
        local notification = Instance.new("TextLabel")
        notification.Size = UDim2.new(1, -20, 0, 40)
        notification.Position = UDim2.new(0, 10, 0, 420)
        notification.BackgroundColor3 = color
        notification.Text = message
        notification.TextColor3 = Color3.new(0, 0, 0)
        notification.Font = Enum.Font.SourceSans
        notification.TextSize = 14
        notification.Parent = scrollFrame
        
        -- Auto-remove after 5 seconds
        task.wait(5)
        if notification.Parent then
            notification:Destroy()
        end
    end)
end

local function parseObjectives(text)
    local objectives = {}
    for objective in string.gmatch(text, "([^,]+)") do
        table.insert(objectives, objective:match("^%s*(.-)%s*$"))
    end
    return objectives
end

-- Enhanced HTTP Request Functions
local function makeRequest(url, method, data, timeout)
    timeout = timeout or 10
    
    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = url,
            Method = method,
            Headers = {
                ["Content-Type"] = "application/json",
                ["X-Plugin-Version"] = CONFIG.PLUGIN_VERSION,
                ["X-Studio-User"] = tostring(StudioService:GetUserId()),
                ["Authorization"] = CONFIG.JWT_TOKEN and ("Bearer " .. CONFIG.JWT_TOKEN) or nil
            },
            Body = data and HttpService:JSONEncode(data) or nil
        })
    end)
    
    if success then
        if response.StatusCode >= 200 and response.StatusCode < 300 then
            local bodyData = nil
            if response.Body and response.Body ~= "" then
                local parseSuccess, parseResult = pcall(function()
                    return HttpService:JSONDecode(response.Body)
                end)
                if parseSuccess then
                    bodyData = parseResult
                else
                    bodyData = response.Body
                end
            end
            return true, bodyData
        else
            return false, string.format("HTTP %d: %s", response.StatusCode, response.StatusMessage or "Unknown error")
        end
    else
        return false, "Request failed: " .. tostring(response)
    end
end

-- Enhanced WebSocket Detection and Management
local function checkWebSocketAvailability()
    debugLog("Checking WebSocket availability...")
    
    -- Check if WebSocket API is available
    if not HttpService.CreateWebStreamClient then
        debugLog("WebSocket API not available in this Studio version")
        WebSocketManager.isAvailable = false
        return false
    end
    
    -- Test WebSocket creation
    local success, webSocket = pcall(function()
        return HttpService:CreateWebStreamClient()
    end)
    
    if not success then
        debugLog("Failed to create WebSocket client: " .. tostring(webSocket))
        WebSocketManager.isAvailable = false
        return false
    end
    
    -- Clean up test WebSocket
    if webSocket then
        pcall(function()
            webSocket:Close()
        end)
    end
    
    debugLog("WebSocket is available")
    WebSocketManager.isAvailable = true
    return true
end

-- Message Queue Management
local function addToOfflineQueue(message)
    table.insert(WebSocketManager.offlineQueue, {
        message = message,
        timestamp = os.time(),
        id = HttpService:GenerateGUID(false)
    })
    
    -- Limit queue size
    if #WebSocketManager.offlineQueue > CONFIG.MAX_QUEUE_SIZE then
        table.remove(WebSocketManager.offlineQueue, 1)
    end
    
    debugLog(string.format("Added message to offline queue (size: %d)", #WebSocketManager.offlineQueue))
end

local function processOfflineQueue()
    if #WebSocketManager.offlineQueue == 0 then
        return
    end
    
    debugLog(string.format("Processing offline queue with %d messages", #WebSocketManager.offlineQueue))
    
    for i = #WebSocketManager.offlineQueue, 1, -1 do
        local queuedItem = WebSocketManager.offlineQueue[i]
        
        -- Try to send the message
        if sendWebSocketMessage(queuedItem.message, true) then
            table.remove(WebSocketManager.offlineQueue, i)
        else
            -- If we can't send it, break and try again later
            break
        end
    end
    
    if #WebSocketManager.offlineQueue == 0 then
        showNotification("All queued messages sent successfully", "success")
    end
end

-- Enhanced WebSocket Connection
local function connectWebSocket()
    if not checkWebSocketAvailability() then
        debugLog("WebSocket not available, starting HTTP polling")
        startHTTPPolling()
        return false
    end
    
    WebSocketManager.connectionState = "connecting"
    updateConnectionStatus(false, "connecting")
    
    local success, webSocket = pcall(function()
        return HttpService:CreateWebStreamClient()
    end)
    
    if not success then
        warn("Failed to create WebSocket client:", webSocket)
        startHTTPPolling()
        return false
    end
    
    WebSocketManager.connection = webSocket
    
    local connectSuccess, connectError = pcall(function()
        webSocket:Connect(CONFIG.WEBSOCKET_URL, {
            Headers = {
                ["Authorization"] = CONFIG.JWT_TOKEN and ("Bearer " .. CONFIG.JWT_TOKEN) or "",
                ["X-Plugin-Version"] = CONFIG.PLUGIN_VERSION,
                ["X-Studio-ID"] = CONFIG.STUDIO_ID,
                ["X-Session-ID"] = PluginState.sessionId or ""
            }
        })
    end)
    
    if not connectSuccess then
        warn("WebSocket connection failed:", connectError)
        WebSocketManager.connection = nil
        WebSocketManager.connectionState = "disconnected"
        startHTTPPolling()
        return false
    end
    
    -- WebSocket event handlers
    webSocket.OnMessage:Connect(function(message)
        local success, data = pcall(function()
            return HttpService:JSONDecode(message)
        end)
        
        if success and data then
            handleWebSocketMessage(data)
            WebSocketManager.lastMessageId = math.max(WebSocketManager.lastMessageId, data.id or 0)
        else
            warn("Failed to parse WebSocket message:", message)
        end
    end)
    
    webSocket.OnError:Connect(function(error)
        warn("WebSocket error:", error)
        WebSocketManager.connection = nil
        updateConnectionStatus(false)
        
        -- Attempt reconnection with exponential backoff
        if WebSocketManager.reconnectAttempts < WebSocketManager.maxReconnectAttempts then
            WebSocketManager.reconnectAttempts = WebSocketManager.reconnectAttempts + 1
            local delay = math.min(30, 5 * WebSocketManager.reconnectAttempts)
            debugLog(string.format("Attempting WebSocket reconnect in %d seconds (attempt %d)", delay, WebSocketManager.reconnectAttempts))
            
            spawn(function()
                task.wait(delay)
                connectWebSocket()
            end)
        else
            debugLog("Max WebSocket reconnection attempts reached, falling back to HTTP polling")
            startHTTPPolling()
        end
    end)
    
    webSocket.OnClose:Connect(function(code, reason)
        warn("WebSocket closed:", code, reason)
        WebSocketManager.connection = nil
        updateConnectionStatus(false)
        
        -- Attempt reconnection
        if WebSocketManager.reconnectAttempts < WebSocketManager.maxReconnectAttempts then
            WebSocketManager.reconnectAttempts = WebSocketManager.reconnectAttempts + 1
            local delay = math.min(30, 5 * WebSocketManager.reconnectAttempts)
            
            spawn(function()
                task.wait(delay)
                connectWebSocket()
            end)
        else
            startHTTPPolling()
        end
    end)
    
    WebSocketManager.reconnectAttempts = 0
    WebSocketManager.lastSuccessfulConnection = os.time()
    updateConnectionStatus(true, "websocket")
    showNotification("WebSocket connected successfully", "success")
    
    -- Process any queued messages
    processOfflineQueue()
    
    return true
end

-- Enhanced HTTP Polling with robust endpoint handling
local function startHTTPPolling()
    if WebSocketManager.pollingActive then
        debugLog("HTTP polling already active")
        return
    end
    
    WebSocketManager.pollingActive = true
    updateConnectionStatus(true, "polling")
    showNotification("Using HTTP polling for real-time updates", "info")
    debugLog("Starting HTTP polling with 2-second intervals")
    
    spawn(function()
        local consecutiveErrors = 0
        local maxErrors = 5
        
        while WebSocketManager.pollingActive do
            local success, result = pcall(function()
                return HttpService:RequestAsync({
                    Url = CONFIG.BACKEND_URL .. "/plugin/messages",
                    Method = "POST",
                    Headers = {
                        ["Content-Type"] = "application/json",
                        ["Authorization"] = CONFIG.JWT_TOKEN and ("Bearer " .. CONFIG.JWT_TOKEN) or "",
                        ["X-Plugin-Version"] = CONFIG.PLUGIN_VERSION,
                        ["X-Studio-ID"] = CONFIG.STUDIO_ID
                    },
                    Body = HttpService:JSONEncode({
                        plugin_id = PluginState.sessionId,
                        last_message_id = WebSocketManager.lastMessageId,
                        timestamp = os.time(),
                        connection_type = "polling"
                    })
                })
            end)
            
            if success then
                consecutiveErrors = 0
                
                if result.StatusCode == 200 then
                    local parseSuccess, data = pcall(function()
                        return HttpService:JSONDecode(result.Body)
                    end)
                    
                    if parseSuccess and data.messages and #data.messages > 0 then
                        for _, message in ipairs(data.messages) do
                            handleWebSocketMessage(message)
                            WebSocketManager.lastMessageId = math.max(WebSocketManager.lastMessageId, message.id or 0)
                        end
                    end
                elseif result.StatusCode == 404 then
                    -- Endpoint not available, try alternative endpoints
                    local alternativeEndpoints = {
                        "/plugin/poll",
                        "/poll-messages",
                        "/messages/poll"
                    }
                    
                    local foundWorkingEndpoint = false
                    for _, endpoint in ipairs(alternativeEndpoints) do
                        local altSuccess, altResult = pcall(function()
                            return HttpService:RequestAsync({
                                Url = CONFIG.BACKEND_URL .. endpoint,
                                Method = "GET",
                                Headers = {
                                    ["Authorization"] = CONFIG.JWT_TOKEN and ("Bearer " .. CONFIG.JWT_TOKEN) or "",
                                    ["X-Plugin-Version"] = CONFIG.PLUGIN_VERSION
                                }
                            })
                        end)
                        
                        if altSuccess and altResult.StatusCode == 200 then
                            debugLog(string.format("Found working polling endpoint: %s", endpoint))
                            foundWorkingEndpoint = true
                            break
                        end
                    end
                    
                    if not foundWorkingEndpoint then
                        debugLog("No working polling endpoints found, attempting WebSocket reconnection")
                        WebSocketManager.pollingActive = false
                        connectWebSocket()
                        return
                    end
                elseif result.StatusCode >= 500 then
                    consecutiveErrors = consecutiveErrors + 1
                    debugLog(string.format("Server error during polling: %d (consecutive errors: %d)", result.StatusCode, consecutiveErrors))
                end
            else
                consecutiveErrors = consecutiveErrors + 1
                debugLog(string.format("Polling request failed: %s (consecutive errors: %d)", tostring(result), consecutiveErrors))
            end
            
            -- If too many consecutive errors, try WebSocket again
            if consecutiveErrors >= maxErrors then
                debugLog("Too many polling errors, attempting WebSocket reconnection")
                WebSocketManager.pollingActive = false
                task.wait(5)
                connectWebSocket()
                return
            end
            
            task.wait(WebSocketManager.pollingInterval)
        end
    end)
end

-- Stop HTTP polling
local function stopHTTPPolling()
    WebSocketManager.pollingActive = false
    debugLog("HTTP polling stopped")
end

-- Handle WebSocket messages (works for both WebSocket and HTTP polling)
local function handleWebSocketMessage(data)
    if not data then return end
    
    debugLog(string.format("Received message type: %s", data.type or "unknown"))
    
    if data.type == "progress" then
        -- Update progress bar
        if progressBar then
            local progress = math.max(0, math.min(100, data.progress or 0))
            progressBar.Size = UDim2.new(progress / 100, 0, 1, 0)
        end
        if data.message then
            showNotification(data.message, "info")
        end
    elseif data.type == "content_ready" then
        -- Content is ready, apply to workspace
        if data.content then
            applyContentToWorkspace(data.content)
        end
    elseif data.type == "error" then
        showNotification(data.message or "Unknown error occurred", "error")
    elseif data.type == "system_notification" then
        showNotification(data.message or "System notification", data.level or "info")
    elseif data.type == "plugin_update" then
        -- Handle plugin-specific updates
        if data.update_type == "config_change" then
            showNotification("Configuration updated", "info")
        elseif data.update_type == "reconnect_required" then
            debugLog("Server requested reconnection")
            WebSocketManager.connection = nil
            connectWebSocket()
        end
    elseif data.type == "heartbeat_ack" then
        -- Heartbeat acknowledgment
        debugLog("Heartbeat acknowledged")
    elseif data.type == "queue_status" then
        -- Update on message queue status
        if data.queued_messages and data.queued_messages > 0 then
            showNotification(string.format("%d messages queued on server", data.queued_messages), "info")
        end
    end
end

-- Enhanced message sending with fallback and queuing
function sendWebSocketMessage(message, skipQueue)
    if not message then return false end
    
    local messageWithId = {
        id = HttpService:GenerateGUID(false),
        timestamp = os.time(),
        plugin_id = PluginState.sessionId,
        studio_id = CONFIG.STUDIO_ID,
        data = message
    }
    
    -- Try WebSocket first
    if WebSocketManager.connection then
        local success, error = pcall(function()
            WebSocketManager.connection:Send(HttpService:JSONEncode(messageWithId))
        end)
        
        if success then
            debugLog("Message sent via WebSocket")
            return true
        else
            warn("Failed to send WebSocket message:", error)
            WebSocketManager.connection = nil
            updateConnectionStatus(false)
        end
    end
    
    -- Try HTTP fallback
    local httpSuccess = sendHTTPMessage(messageWithId)
    if httpSuccess then
        return true
    end
    
    -- Queue message if offline and not already queuing
    if not skipQueue then
        addToOfflineQueue(messageWithId)
    end
    
    return false
end

-- Send message via HTTP when WebSocket unavailable
local function sendHTTPMessage(message)
    local endpoints = {
        "/plugin/message",
        "/plugin/send-message",
        "/send-message"
    }
    
    for _, endpoint in ipairs(endpoints) do
        local success, result = makeRequest(
            CONFIG.BACKEND_URL .. endpoint,
            "POST",
            message,
            5
        )
        
        if success then
            debugLog(string.format("Message sent via HTTP endpoint: %s", endpoint))
            return true
        else
            debugLog(string.format("Failed to send message via %s: %s", endpoint, tostring(result)))
        end
    end
    
    return false
end

-- Plugin Registration with retry logic
local function registerPlugin()
    local data = {
        port = CONFIG.PLUGIN_PORT,
        version = CONFIG.PLUGIN_VERSION,
        studio_user_id = StudioService:GetUserId(),
        studio_id = CONFIG.STUDIO_ID,
        capabilities = {
            "terrain_generation",
            "script_creation",
            "ui_building",
            "quiz_system",
            "websocket",
            "http_polling"
        },
        connection_preferences = {
            preferred_method = "websocket",
            fallback_method = "http_polling",
            polling_interval = CONFIG.POLLING_INTERVAL
        }
    }
    
    local success, result = makeRequest(
        CONFIG.BACKEND_URL .. "/register_plugin",
        "POST",
        data
    )
    
    if success then
        PluginState.sessionId = result.session_id or HttpService:GenerateGUID(false)
        updateConnectionStatus(true)
        showNotification("Plugin registered successfully!", "success")
        debugLog(string.format("Plugin registered with session ID: %s", PluginState.sessionId))
        return true
    else
        updateConnectionStatus(false)
        showNotification("Failed to register plugin: " .. tostring(result), "error")
        debugLog(string.format("Plugin registration failed: %s", tostring(result)))
        return false
    end
end

-- Content Generation
local function generateContent()
    if not PluginState.connected then
        showNotification("Not connected to server. Attempting to connect...", "warning")
        if not registerPlugin() then
            return
        end
    end
    
    -- Show progress
    progressFrame.Visible = true
    progressBar.Size = UDim2.new(0.2, 0, 1, 0)
    generateButton.Text = "Generating..."
    generateButton.BackgroundColor3 = Color3.fromRGB(150, 150, 150)
    
    local requestData = {
        subject = subjectBox.Text,
        grade_level = tonumber(gradeBox.Text) or 5,
        learning_objectives = parseObjectives(objectivesBox.Text),
        environment_type = envBox.Text,
        include_quiz = quizCheckbox.Text == "✓",
        plugin_id = PluginState.sessionId,
        studio_id = CONFIG.STUDIO_ID
    }
    
    -- Validate input
    if requestData.subject == "" then
        showNotification("Please enter a subject", "error")
        progressFrame.Visible = false
        generateButton.Text = "🚀 Generate Content"
        generateButton.BackgroundColor3 = Color3.fromRGB(0, 170, 255)
        return
    end
    
    progressBar.Size = UDim2.new(0.4, 0, 1, 0)
    
    -- Send request via WebSocket/HTTP
    sendWebSocketMessage({
        type = "content_request",
        data = requestData
    })
    
    progressBar.Size = UDim2.new(0.6, 0, 1, 0)
    
    -- Also try direct HTTP request as fallback
    spawn(function()
        local success, result = makeRequest(
            CONFIG.API_URL .. "/generate_content",
            "POST",
            requestData
        )
        
        if success then
            progressBar.Size = UDim2.new(0.8, 0, 1, 0)
            
            -- Store generated content
            local requestId = result.request_id or HttpService:GenerateGUID(false)
            PluginState.generatedContent[requestId] = result
            
            -- Apply content to workspace
            applyGeneratedContent(result)
            
            progressBar.Size = UDim2.new(1, 0, 1, 0)
            showNotification("Content generated successfully!", "success")
            
            task.wait(1)
            progressFrame.Visible = false
            generateButton.Text = "🚀 Generate Content"
            generateButton.BackgroundColor3 = Color3.fromRGB(0, 170, 255)
        else
            progressFrame.Visible = false
            generateButton.Text = "🚀 Generate Content"
            generateButton.BackgroundColor3 = Color3.fromRGB(0, 170, 255)
            showNotification("Failed to generate content: " .. tostring(result), "error")
        end
    end)
end

-- Enhanced Content Application System
local ContentApplier = {
    appliedComponents = {},
    contentFolder = nil,
    terrainService = game:GetService("Terrain"),
    lighting = game:GetService("Lighting"),
    soundService = game:GetService("SoundService")
}

-- Initialize content folder
local function initializeContentFolder()
    if not ContentApplier.contentFolder then
        ContentApplier.contentFolder = workspace:FindFirstChild("GeneratedContent")
        if not ContentApplier.contentFolder then
            ContentApplier.contentFolder = Instance.new("Folder")
            ContentApplier.contentFolder.Name = "GeneratedContent"
            ContentApplier.contentFolder.Parent = workspace
        end
    end
    return ContentApplier.contentFolder
end

-- Apply terrain generation
local function applyTerrainGeneration(terrainData)
    if not terrainData then return false end
    
    local success, error = pcall(function()
        if terrainData.script then
            -- Execute terrain generation script
            local terrainFunc = loadstring(terrainData.script)
            if terrainFunc then
                terrainFunc()
                return true
            end
        elseif terrainData.regions then
            -- Apply terrain regions
            for _, region in ipairs(terrainData.regions) do
                local regionSize = region.size or Vector3.new(4, 4, 4)
                local regionPosition = region.position or Vector3.new(0, 0, 0)
                local material = region.material or Enum.Material.Grass
                
                ContentApplier.terrainService:FillRegion(
                    Region3.new(regionPosition, regionPosition + regionSize),
                    4, -- resolution
                    material
                )
            end
            return true
        elseif terrainData.heightmap then
            -- Apply heightmap-based terrain
            local size = terrainData.size or Vector3.new(100, 20, 100)
            local position = terrainData.position or Vector3.new(0, 0, 0)
            
            -- Create basic terrain shape
            ContentApplier.terrainService:FillRegion(
                Region3.new(position, position + size),
                4,
                Enum.Material.Grass
            )
            return true
        end
        return false
    end)
    
    if success then
        table.insert(ContentApplier.appliedComponents, "terrain")
        showNotification("Terrain generated successfully", "success")
        return true
    else
        warn("Failed to apply terrain: " .. tostring(error))
        showNotification("Terrain generation failed", "error")
        return false
    end
end

-- Apply object creation
local function applyObjectCreation(objectsData)
    if not objectsData or #objectsData == 0 then return 0 end
    
    local createdCount = 0
    local objectsFolder = initializeContentFolder():FindFirstChild("Objects")
    if not objectsFolder then
        objectsFolder = Instance.new("Folder")
        objectsFolder.Name = "Objects"
        objectsFolder.Parent = ContentApplier.contentFolder
    end
    
    for _, objData in ipairs(objectsData) do
        local success, error = pcall(function()
            local object = Instance.new(objData.type or "Part")
            object.Name = objData.name or "GeneratedObject"
            object.Position = objData.position or Vector3.new(0, 5, 0)
            object.Size = objData.size or Vector3.new(4, 1, 2)
            object.Material = objData.material or Enum.Material.Plastic
            object.BrickColor = objData.color or BrickColor.new("Bright blue")
            
            -- Apply additional properties
            if objData.anchored ~= nil then
                object.Anchored = objData.anchored
            end
            if objData.canCollide ~= nil then
                object.CanCollide = objData.canCollide
            end
            if objData.transparency then
                object.Transparency = objData.transparency
            end
            
            -- Add to objects folder
            object.Parent = objectsFolder
            createdCount = createdCount + 1
            
            -- Apply any special properties
            if objData.properties then
                for propName, propValue in pairs(objData.properties) do
                    if object[propName] ~= nil then
                        object[propName] = propValue
                    end
                end
            end
        end)
        
        if not success then
            warn("Failed to create object: " .. tostring(error))
        end
    end
    
    if createdCount > 0 then
        table.insert(ContentApplier.appliedComponents, "objects:" .. createdCount)
        showNotification(string.format("Created %d objects", createdCount), "success")
    end
    
    return createdCount
end

-- Apply script creation
local function applyScriptCreation(scriptsData)
    if not scriptsData or #scriptsData == 0 then return 0 end
    
    local createdCount = 0
    local scriptsFolder = initializeContentFolder():FindFirstChild("Scripts")
    if not scriptsFolder then
        scriptsFolder = Instance.new("Folder")
        scriptsFolder.Name = "Scripts"
        scriptsFolder.Parent = ContentApplier.contentFolder
    end
    
    for i, scriptData in ipairs(scriptsData) do
        local success, error = pcall(function()
            local scriptType = scriptData.type or "Script"
            local script = Instance.new(scriptType)
            script.Name = scriptData.name or ("GeneratedScript_" .. i)
            script.Source = scriptData.source or scriptData.content or "-- Empty script"
            
            -- Set parent based on script type
            if scriptType == "LocalScript" then
                -- LocalScripts should go in StarterPlayerScripts or StarterGui
                local starterGui = game:GetService("StarterGui")
                local screenGui = starterGui:FindFirstChild("GeneratedContent") or Instance.new("ScreenGui")
                screenGui.Name = "GeneratedContent"
                screenGui.Parent = starterGui
                script.Parent = screenGui
            else
                script.Parent = scriptsFolder
            end
            
            createdCount = createdCount + 1
        end)
        
        if not success then
            warn("Failed to create script: " .. tostring(error))
        end
    end
    
    if createdCount > 0 then
        table.insert(ContentApplier.appliedComponents, "scripts:" .. createdCount)
        showNotification(string.format("Created %d scripts", createdCount), "success")
    end
    
    return createdCount
end

-- Apply quiz system creation
local function applyQuizSystem(quizData)
    if not quizData then return false end
    
    local success, error = pcall(function()
        local quizFolder = initializeContentFolder():FindFirstChild("QuizSystem")
        if not quizFolder then
            quizFolder = Instance.new("Folder")
            quizFolder.Name = "QuizSystem"
            quizFolder.Parent = ContentApplier.contentFolder
        end
        
        -- Store quiz data
        local quizDataValue = Instance.new("StringValue")
        quizDataValue.Name = "QuizData"
        quizDataValue.Value = HttpService:JSONEncode(quizData)
        quizDataValue.Parent = quizFolder
        
        -- Create quiz UI if specified
        if quizData.ui then
            local screenGui = Instance.new("ScreenGui")
            screenGui.Name = "QuizUI"
            screenGui.Parent = game:GetService("StarterGui")
            
            -- Create main frame
            local mainFrame = Instance.new("Frame")
            mainFrame.Size = UDim2.new(0, 400, 0, 300)
            mainFrame.Position = UDim2.new(0.5, -200, 0.5, -150)
            mainFrame.BackgroundColor3 = Color3.fromRGB(50, 50, 50)
            mainFrame.BorderSizePixel = 0
            mainFrame.Parent = screenGui
            
            -- Add title
            local titleLabel = Instance.new("TextLabel")
            titleLabel.Size = UDim2.new(1, 0, 0, 40)
            titleLabel.Position = UDim2.new(0, 0, 0, 0)
            titleLabel.BackgroundTransparency = 1
            titleLabel.Text = quizData.title or "Quiz"
            titleLabel.TextColor3 = Color3.new(1, 1, 1)
            titleLabel.TextScaled = true
            titleLabel.Font = Enum.Font.SourceSansBold
            titleLabel.Parent = mainFrame
            
            -- Add questions (simplified)
            if quizData.questions then
                local questionsFrame = Instance.new("ScrollingFrame")
                questionsFrame.Size = UDim2.new(1, -20, 1, -60)
                questionsFrame.Position = UDim2.new(0, 10, 0, 50)
                questionsFrame.BackgroundTransparency = 1
                questionsFrame.ScrollBarThickness = 6
                questionsFrame.CanvasSize = UDim2.new(0, 0, 0, #quizData.questions * 60)
                questionsFrame.Parent = mainFrame
                
                for i, question in ipairs(quizData.questions) do
                    local questionFrame = Instance.new("Frame")
                    questionFrame.Size = UDim2.new(1, 0, 0, 50)
                    questionFrame.Position = UDim2.new(0, 0, 0, (i-1) * 60)
                    questionFrame.BackgroundColor3 = Color3.fromRGB(70, 70, 70)
                    questionFrame.BorderSizePixel = 0
                    questionFrame.Parent = questionsFrame
                    
                    local questionLabel = Instance.new("TextLabel")
                    questionLabel.Size = UDim2.new(1, -10, 1, 0)
                    questionLabel.Position = UDim2.new(0, 5, 0, 0)
                    questionLabel.BackgroundTransparency = 1
                    questionLabel.Text = question.question or ("Question " .. i)
                    questionLabel.TextColor3 = Color3.new(1, 1, 1)
                    questionLabel.TextScaled = true
                    questionLabel.TextXAlignment = Enum.TextXAlignment.Left
                    questionLabel.Parent = questionFrame
                end
            end
        end
        
        return true
    end)
    
    if success then
        table.insert(ContentApplier.appliedComponents, "quiz")
        showNotification("Quiz system created successfully", "success")
        return true
    else
        warn("Failed to create quiz system: " .. tostring(error))
        showNotification("Quiz system creation failed", "error")
        return false
    end
end

-- Apply lighting and atmosphere
local function applyLightingAndAtmosphere(lightingData)
    if not lightingData then return false end
    
    local success, error = pcall(function()
        if lightingData.ambient then
            ContentApplier.lighting.Ambient = lightingData.ambient
        end
        if lightingData.brightness then
            ContentApplier.lighting.Brightness = lightingData.brightness
        end
        if lightingData.timeOfDay then
            ContentApplier.lighting.TimeOfDay = lightingData.timeOfDay
        end
        if lightingData.fogColor then
            ContentApplier.lighting.FogColor = lightingData.fogColor
        end
        if lightingData.fogEnd then
            ContentApplier.lighting.FogEnd = lightingData.fogEnd
        end
        return true
    end)
    
    if success then
        table.insert(ContentApplier.appliedComponents, "lighting")
        showNotification("Lighting applied successfully", "success")
        return true
    else
        warn("Failed to apply lighting: " .. tostring(error))
        return false
    end
end

-- Main content application function
function applyGeneratedContent(contentData)
    if not contentData then 
        showNotification("No content data provided", "error")
        return 
    end
    
    ChangeHistoryService:SetWaypoint("Before AI Content Generation")
    
    -- Reset applied components
    ContentApplier.appliedComponents = {}
    
    -- Initialize content folder
    initializeContentFolder()
    
    -- Apply terrain
    if contentData.terrain then
        applyTerrainGeneration(contentData.terrain)
    elseif contentData.terrain_script then
        applyTerrainGeneration({script = contentData.terrain_script})
    end
    
    -- Apply objects
    if contentData.objects then
        applyObjectCreation(contentData.objects)
    end
    
    -- Apply scripts
    if contentData.scripts then
        applyScriptCreation(contentData.scripts)
    end
    
    -- Apply quiz system
    if contentData.quiz then
        applyQuizSystem(contentData.quiz)
    end
    
    -- Apply lighting
    if contentData.lighting then
        applyLightingAndAtmosphere(contentData.lighting)
    end
    
    ChangeHistoryService:SetWaypoint("After AI Content Generation")
    
    -- Report back to server
    local reportData = {
        request_id = contentData.request_id,
        success = true,
        applied_components = ContentApplier.appliedComponents,
        timestamp = os.time(),
        component_count = #ContentApplier.appliedComponents
    }
    
    -- Send report via WebSocket or HTTP
    sendWebSocketMessage({
        type = "content_applied",
        data = reportData
    })
    
    showNotification(string.format("Applied %d component types", #ContentApplier.appliedComponents), "success")
end

-- Apply generated content to workspace
local function applyContentToWorkspace(content)
    if not content then return end
    
    -- Create folder for generated content
    local contentFolder = workspace:FindFirstChild("GeneratedContent") or Instance.new("Folder")
    contentFolder.Name = "GeneratedContent"
    contentFolder.Parent = workspace
    
    -- Apply terrain if available
    if content.terrain then
        showNotification("Terrain applied", "success")
    end
    
    -- Create scripts if available
    if content.scripts then
        for scriptName, scriptContent in pairs(content.scripts) do
            local script = Instance.new("Script")
            script.Name = scriptName
            script.Source = scriptContent
            script.Parent = contentFolder
        end
        showNotification("Scripts created", "success")
    end
    
    -- Create quiz UI if available
    if content.quiz then
        showNotification("Quiz interface created", "success")
    end
end

-- Heartbeat Function with enhanced connectivity checking
local function sendHeartbeat()
    if not PluginState.connected then return end
    
    local data = {
        session_id = PluginState.sessionId,
        timestamp = os.time(),
        status = "active",
        connection_type = WebSocketManager.connectionState,
        queue_size = #WebSocketManager.offlineQueue,
        last_message_id = WebSocketManager.lastMessageId
    }
    
    local success, result = makeRequest(
        CONFIG.BACKEND_URL .. "/heartbeat",
        "POST",
        data
    )
    
    if not success then
        PluginState.reconnectAttempts = PluginState.reconnectAttempts + 1
        debugLog(string.format("Heartbeat failed (attempt %d): %s", PluginState.reconnectAttempts, tostring(result)))
        
        if PluginState.reconnectAttempts < CONFIG.MAX_RECONNECT_ATTEMPTS then
            task.wait(CONFIG.RECONNECT_INTERVAL)
            if not registerPlugin() then
                updateConnectionStatus(false)
            end
        else
            updateConnectionStatus(false)
            showNotification("Lost connection to server", "error")
        end
    else
        PluginState.reconnectAttempts = 0
        
        -- Process any server-side updates
        if result and result.updates then
            for _, update in ipairs(result.updates) do
                handleWebSocketMessage(update)
            end
        end
    end
end

-- Authentication function
local function authenticate()
    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = CONFIG.API_URL .. "/auth/login",
            Method = "POST",
            Headers = {
                ["Content-Type"] = "application/json"
            },
            Body = HttpService:JSONEncode({
                username = "plugin_user",
                password = "plugin_pass123"  -- Should be configured securely
            })
        })
    end)
    
    if success and response.StatusCode == 200 then
        local data = HttpService:JSONDecode(response.Body)
        if data.access_token then
            CONFIG.JWT_TOKEN = data.access_token
            showNotification("Authentication successful", "success")
            return true
        end
    end
    
    showNotification("Authentication failed", "error")
    return false
end

-- Health Check System
local function performHealthCheck()
    debugLog("Performing health check...")
    
    -- Check WebSocket availability
    local wsAvailable = checkWebSocketAvailability()
    
    -- Check backend connectivity
    local backendSuccess, _ = makeRequest(CONFIG.BACKEND_URL .. "/health", "GET", nil, 5)
    
    -- Check API connectivity  
    local apiSuccess, _ = makeRequest(CONFIG.API_URL .. "/health", "GET", nil, 5)
    
    local healthStatus = {
        websocket_available = wsAvailable,
        backend_reachable = backendSuccess,
        api_reachable = apiSuccess,
        connection_state = WebSocketManager.connectionState,
        queue_size = #WebSocketManager.offlineQueue,
        timestamp = os.time()
    }
    
    debugLog(string.format("Health check: WS=%s, Backend=%s, API=%s", 
        tostring(wsAvailable), tostring(backendSuccess), tostring(apiSuccess)))
    
    -- Send health status if connected
    if PluginState.connected then
        sendWebSocketMessage({
            type = "health_status",
            data = healthStatus
        })
    end
    
    -- Take corrective action if needed
    if not backendSuccess and not apiSuccess then
        if WebSocketManager.connectionState ~= "disconnected" then
            updateConnectionStatus(false)
            showNotification("Backend services unreachable", "error")
        end
    elseif not PluginState.connected and (backendSuccess or apiSuccess) then
        -- Try to reconnect
        registerPlugin()
    end
end

-- Event Handlers
generateButton.MouseButton1Click:Connect(function()
    generateContent()
end)

quizCheckbox.MouseButton1Click:Connect(function()
    if quizCheckbox.Text == "✓" then
        quizCheckbox.Text = ""
    else
        quizCheckbox.Text = "✓"
    end
end)

mainButton.Click:Connect(function()
    pluginWidget.Enabled = not pluginWidget.Enabled
end)

-- Auto-connect on plugin load with enhanced startup sequence
spawn(function()
    debugLog("Initializing plugin...")
    task.wait(2) -- Wait for studio to fully load
    
    -- Perform initial health check
    performHealthCheck()
    
    -- Attempt registration and connection
    if registerPlugin() then
        -- Try WebSocket connection first, fallback to HTTP polling
        if not connectWebSocket() then
            startHTTPPolling()
        end
    else
        -- Even if registration fails, try polling to see if server becomes available
        task.wait(5)
        startHTTPPolling()
    end
end)

-- Enhanced heartbeat and health check loop
spawn(function()
    while true do
        task.wait(CONFIG.HEARTBEAT_INTERVAL)
        sendHeartbeat()
        
        -- Periodic health check every few heartbeats
        if math.random(1, 3) == 1 then
            performHealthCheck()
        end
        
        -- Process offline queue periodically
        if #WebSocketManager.offlineQueue > 0 then
            processOfflineQueue()
        end
    end
end)

-- Connection state monitoring
spawn(function()
    while true do
        task.wait(WebSocketManager.healthCheckInterval)
        
        -- Monitor connection health
        if WebSocketManager.connectionState == "connected" and WebSocketManager.connection then
            -- Check if WebSocket is still alive
            local testMessage = {
                type = "ping",
                timestamp = os.time()
            }
            
            local success = pcall(function()
                WebSocketManager.connection:Send(HttpService:JSONEncode(testMessage))
            end)
            
            if not success then
                debugLog("WebSocket ping failed, connection may be dead")
                WebSocketManager.connection = nil
                updateConnectionStatus(false)
                connectWebSocket()
            end
        elseif WebSocketManager.connectionState == "polling" and not WebSocketManager.pollingActive then
            debugLog("Polling stopped unexpectedly, restarting...")
            startHTTPPolling()
        elseif WebSocketManager.connectionState == "disconnected" then
            -- Periodically try to reconnect
            if os.time() - WebSocketManager.lastSuccessfulConnection > 60 then
                debugLog("Attempting automatic reconnection...")
                if registerPlugin() then
                    connectWebSocket()
                end
            end
        end
    end
end)

-- Cleanup on plugin unload
plugin.Unloading:Connect(function()
    debugLog("Plugin unloading, cleaning up...")
    
    -- Stop HTTP polling
    stopHTTPPolling()
    
    -- Close WebSocket connection
    if WebSocketManager.connection then
        pcall(function()
            WebSocketManager.connection:Close()
        end)
        WebSocketManager.connection = nil
    end
    
    -- Unregister plugin
    if PluginState.connected then
        makeRequest(
            CONFIG.BACKEND_URL .. "/unregister_plugin",
            "POST",
            { session_id = PluginState.sessionId }
        )
    end
    
    debugLog("Plugin cleanup complete")
end)

print(string.format("[%s] Plugin loaded successfully (v%s)", CONFIG.PLUGIN_NAME, CONFIG.PLUGIN_VERSION))
print(string.format("[%s] WebSocket URL: %s", CONFIG.PLUGIN_NAME, CONFIG.WEBSOCKET_URL))
print(string.format("[%s] Backend URL: %s", CONFIG.PLUGIN_NAME, CONFIG.BACKEND_URL))
print(string.format("[%s] Session ID: %s", CONFIG.PLUGIN_NAME, PluginState.sessionId or "Not assigned"))
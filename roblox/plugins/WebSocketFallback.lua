--[[
    WebSocket Fallback Module for Roblox Studio
    Version: 1.0.0
    Description: Provides HTTP polling fallback for WebSocket-like functionality
                 in Roblox Studio environments that don't support native WebSockets
--]]

local HttpService = game:GetService("HttpService")
local RunService = game:GetService("RunService")

local WebSocketFallback = {}
WebSocketFallback.__index = WebSocketFallback

-- Configuration
local CONFIG = {
    DEFAULT_POLL_INTERVAL = 1, -- seconds
    MAX_RETRY_ATTEMPTS = 3,
    RETRY_DELAY = 2, -- seconds
    CONNECTION_TIMEOUT = 10, -- seconds
    MAX_MESSAGE_QUEUE = 100,
    HEARTBEAT_INTERVAL = 30 -- seconds
}

-- Constructor
function WebSocketFallback.new(url)
    local self = setmetatable({}, WebSocketFallback)
    
    -- Convert WebSocket URL to HTTP
    self.url = url:gsub("^ws://", "http://"):gsub("^wss://", "https://")
    self.connected = false
    self.connecting = false
    self.sessionId = HttpService:GenerateGUID(false)
    self.messageQueue = {}
    self.callbacks = {}
    self.pollInterval = CONFIG.DEFAULT_POLL_INTERVAL
    self.lastPoll = 0
    self.lastHeartbeat = 0
    self.retryCount = 0
    self.pollConnection = nil
    self.heartbeatConnection = nil
    
    -- Event handlers
    self.onOpen = nil
    self.onMessage = nil
    self.onError = nil
    self.onClose = nil
    
    return self
end

-- Connect to server
function WebSocketFallback:Connect()
    if self.connected or self.connecting then
        warn("[WebSocketFallback] Already connected or connecting")
        return false
    end
    
    self.connecting = true
    print("[WebSocketFallback] Connecting via HTTP polling to", self.url)
    
    -- Register session with server
    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = self.url .. "/fallback/connect",
            Method = "POST",
            Headers = {
                ["Content-Type"] = "application/json",
                ["X-Roblox-Studio"] = "true"
            },
            Body = HttpService:JSONEncode({
                sessionId = self.sessionId,
                type = "roblox_studio",
                version = RunService:IsStudio() and "Studio" or "Game",
                capabilities = {
                    "terrain_generation",
                    "quiz_creation",
                    "object_placement",
                    "real_time_sync"
                }
            })
        })
    end)
    
    if success and response.StatusCode == 200 then
        local data = HttpService:JSONDecode(response.Body)
        self.sessionId = data.session_id or self.sessionId
        self.pollInterval = data.poll_interval or CONFIG.DEFAULT_POLL_INTERVAL
        
        self.connected = true
        self.connecting = false
        self.retryCount = 0
        
        print("[WebSocketFallback] Connected with session ID:", self.sessionId)
        
        -- Trigger onOpen callback
        if self.onOpen then
            pcall(self.onOpen)
        end
        
        -- Start polling and heartbeat
        self:StartPolling()
        self:StartHeartbeat()
        
        return true
    else
        self.connecting = false
        local errorMsg = response and response.Body or "Connection failed"
        warn("[WebSocketFallback] Failed to connect:", errorMsg)
        
        -- Trigger onError callback
        if self.onError then
            pcall(self.onError, errorMsg)
        end
        
        -- Retry connection if under retry limit
        if self.retryCount < CONFIG.MAX_RETRY_ATTEMPTS then
            self.retryCount = self.retryCount + 1
            print("[WebSocketFallback] Retrying connection in", CONFIG.RETRY_DELAY, "seconds...")
            wait(CONFIG.RETRY_DELAY)
            return self:Connect()
        end
        
        return false
    end
end

-- Start polling for messages
function WebSocketFallback:StartPolling()
    if self.pollConnection then
        self.pollConnection:Disconnect()
    end
    
    self.pollConnection = RunService.Heartbeat:Connect(function()
        if self.connected and tick() - self.lastPoll >= self.pollInterval then
            self.lastPoll = tick()
            self:Poll()
        end
    end)
end

-- Poll for new messages
function WebSocketFallback:Poll()
    if not self.connected then return end
    
    spawn(function()
        local success, response = pcall(function()
            return HttpService:RequestAsync({
                Url = self.url .. "/fallback/poll",
                Method = "GET",
                Headers = {
                    ["X-Session-Id"] = self.sessionId,
                    ["X-Roblox-Studio"] = "true"
                }
            })
        end)
        
        if success and response.StatusCode == 200 then
            local data = HttpService:JSONDecode(response.Body)
            
            -- Process incoming messages
            if data.messages and #data.messages > 0 then
                for _, message in ipairs(data.messages) do
                    self:HandleMessage(message)
                end
            end
            
            -- Send queued messages if any
            if #self.messageQueue > 0 then
                self:FlushMessageQueue()
            end
            
            -- Update poll interval if provided
            if data.poll_interval then
                self.pollInterval = data.poll_interval
            end
            
        elseif response and response.StatusCode == 404 then
            -- Session expired, reconnect
            warn("[WebSocketFallback] Session expired, reconnecting...")
            self.connected = false
            self:Connect()
        elseif response and response.StatusCode == 503 then
            -- Server temporarily unavailable, increase poll interval
            self.pollInterval = math.min(self.pollInterval * 2, 10)
            print("[WebSocketFallback] Server busy, backing off to", self.pollInterval, "seconds")
        end
    end)
end

-- Send message to server
function WebSocketFallback:Send(data)
    if not self.connected then
        warn("[WebSocketFallback] Not connected, cannot send message")
        return false
    end
    
    -- Convert to JSON if needed
    local message
    if type(data) == "table" then
        message = HttpService:JSONEncode(data)
    else
        message = tostring(data)
    end
    
    -- Add to queue if queue size limit not reached
    if #self.messageQueue >= CONFIG.MAX_MESSAGE_QUEUE then
        warn("[WebSocketFallback] Message queue full, dropping oldest message")
        table.remove(self.messageQueue, 1)
    end
    
    table.insert(self.messageQueue, {
        data = message,
        timestamp = tick(),
        attempts = 0
    })
    
    -- Try to send immediately if not currently polling
    if tick() - self.lastPoll >= self.pollInterval * 0.5 then
        self:FlushMessageQueue()
    end
    
    return true
end

-- Flush message queue
function WebSocketFallback:FlushMessageQueue()
    if #self.messageQueue == 0 then return end
    
    local messages = self.messageQueue
    self.messageQueue = {}
    
    spawn(function()
        local success, response = pcall(function()
            return HttpService:RequestAsync({
                Url = self.url .. "/fallback/send",
                Method = "POST",
                Headers = {
                    ["Content-Type"] = "application/json",
                    ["X-Session-Id"] = self.sessionId,
                    ["X-Roblox-Studio"] = "true"
                },
                Body = HttpService:JSONEncode({
                    messages = messages
                })
            })
        end)
        
        if not success or response.StatusCode ~= 200 then
            -- Re-queue messages for retry
            warn("[WebSocketFallback] Failed to send messages, re-queuing...")
            for _, msg in ipairs(messages) do
                msg.attempts = msg.attempts + 1
                if msg.attempts < CONFIG.MAX_RETRY_ATTEMPTS then
                    table.insert(self.messageQueue, 1, msg)
                else
                    warn("[WebSocketFallback] Message dropped after max retries")
                end
            end
        end
    end)
end

-- Handle incoming message
function WebSocketFallback:HandleMessage(message)
    -- Process message type
    if message.type == "ping" then
        -- Respond to ping
        self:Send({type = "pong", timestamp = tick()})
        
    elseif message.type == "config_update" then
        -- Update configuration
        if message.poll_interval then
            self.pollInterval = message.poll_interval
        end
        
    elseif message.type == "content_generated" then
        -- Handle content generation result
        if self.callbacks.content then
            pcall(self.callbacks.content, message.data)
        end
        
    elseif message.type == "error" then
        -- Handle error message
        warn("[WebSocketFallback] Server error:", message.error)
        if self.onError then
            pcall(self.onError, message.error)
        end
        
    else
        -- Generic message handler
        if self.onMessage then
            pcall(self.onMessage, message)
        end
        
        -- Check for specific callbacks
        if message.type and self.callbacks[message.type] then
            pcall(self.callbacks[message.type], message.data)
        end
    end
end

-- Start heartbeat
function WebSocketFallback:StartHeartbeat()
    if self.heartbeatConnection then
        self.heartbeatConnection:Disconnect()
    end
    
    self.heartbeatConnection = RunService.Heartbeat:Connect(function()
        if self.connected and tick() - self.lastHeartbeat >= CONFIG.HEARTBEAT_INTERVAL then
            self.lastHeartbeat = tick()
            self:SendHeartbeat()
        end
    end)
end

-- Send heartbeat
function WebSocketFallback:SendHeartbeat()
    spawn(function()
        local success, response = pcall(function()
            return HttpService:RequestAsync({
                Url = self.url .. "/fallback/heartbeat",
                Method = "POST",
                Headers = {
                    ["X-Session-Id"] = self.sessionId,
                    ["X-Roblox-Studio"] = "true"
                },
                Body = HttpService:JSONEncode({
                    timestamp = tick(),
                    memory_usage = collectgarbage("count"),
                    message_queue_size = #self.messageQueue
                })
            })
        end)
        
        if not success or response.StatusCode ~= 200 then
            warn("[WebSocketFallback] Heartbeat failed, connection may be lost")
            -- Don't immediately disconnect, let poll handle reconnection
        end
    end)
end

-- Register callback for specific message type
function WebSocketFallback:On(event, callback)
    if type(callback) == "function" then
        self.callbacks[event] = callback
    end
end

-- Remove callback
function WebSocketFallback:Off(event)
    self.callbacks[event] = nil
end

-- Request content generation
function WebSocketFallback:RequestContent(contentData)
    return self:Send({
        type = "content_request",
        data = contentData,
        request_id = HttpService:GenerateGUID(false)
    })
end

-- Request terrain generation
function WebSocketFallback:RequestTerrain(terrainData)
    return self:Send({
        type = "terrain_request",
        data = terrainData,
        request_id = HttpService:GenerateGUID(false)
    })
end

-- Request quiz creation
function WebSocketFallback:RequestQuiz(quizData)
    return self:Send({
        type = "quiz_request",
        data = quizData,
        request_id = HttpService:GenerateGUID(false)
    })
end

-- Disconnect from server
function WebSocketFallback:Disconnect()
    if not self.connected then return end
    
    self.connected = false
    
    -- Stop polling and heartbeat
    if self.pollConnection then
        self.pollConnection:Disconnect()
        self.pollConnection = nil
    end
    
    if self.heartbeatConnection then
        self.heartbeatConnection:Disconnect()
        self.heartbeatConnection = nil
    end
    
    -- Notify server
    pcall(function()
        HttpService:RequestAsync({
            Url = self.url .. "/fallback/disconnect",
            Method = "POST",
            Headers = {
                ["X-Session-Id"] = self.sessionId,
                ["X-Roblox-Studio"] = "true"
            }
        })
    end)
    
    print("[WebSocketFallback] Disconnected")
    
    -- Trigger onClose callback
    if self.onClose then
        pcall(self.onClose)
    end
end

-- Check connection status
function WebSocketFallback:IsConnected()
    return self.connected
end

-- Get session info
function WebSocketFallback:GetSessionInfo()
    return {
        sessionId = self.sessionId,
        connected = self.connected,
        pollInterval = self.pollInterval,
        messageQueueSize = #self.messageQueue,
        uptime = self.connected and (tick() - self.lastHeartbeat) or 0
    }
end

-- Reconnect with new session
function WebSocketFallback:Reconnect()
    self:Disconnect()
    wait(1)
    self.sessionId = HttpService:GenerateGUID(false)
    self.retryCount = 0
    return self:Connect()
end

-- Static method to check if fallback is needed
function WebSocketFallback.IsFallbackNeeded()
    -- Check if native WebSocket is available
    local hasWebSocket = false
    
    pcall(function()
        -- Try to access WebSocket (this will fail in most Roblox environments)
        local test = game:GetService("HttpService").WebSocket
        hasWebSocket = test ~= nil
    end)
    
    return not hasWebSocket
end

-- Create and connect helper
function WebSocketFallback.CreateAndConnect(url, callbacks)
    local fallback = WebSocketFallback.new(url)
    
    -- Set callbacks if provided
    if callbacks then
        fallback.onOpen = callbacks.onOpen
        fallback.onMessage = callbacks.onMessage
        fallback.onError = callbacks.onError
        fallback.onClose = callbacks.onClose
        
        -- Register specific event callbacks
        if callbacks.events then
            for event, callback in pairs(callbacks.events) do
                fallback:On(event, callback)
            end
        end
    end
    
    -- Connect
    local connected = fallback:Connect()
    
    if connected then
        return fallback
    else
        return nil
    end
end

return WebSocketFallback
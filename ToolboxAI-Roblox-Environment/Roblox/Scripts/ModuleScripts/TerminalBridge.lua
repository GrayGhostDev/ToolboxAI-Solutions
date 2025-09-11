--[[
    ToolboxAI Terminal Bridge Module
    Terminal 3 - Roblox Integration Orchestrator
    Handles communication between all terminals
]]

local HttpService = game:GetService("HttpService")
local RunService = game:GetService("RunService")
local DataStoreService = game:GetService("DataStoreService")
local MessagingService = game:GetService("MessagingService")

local TerminalBridge = {}
TerminalBridge.__index = TerminalBridge

-- Configuration
local TERMINAL1_URL = "http://127.0.0.1:5001"  -- Flask Bridge
local TERMINAL2_URL = "http://127.0.0.1:5179"  -- Dashboard
local SYNC_INTERVAL = 5  -- seconds

function TerminalBridge.new()
    local self = setmetatable({}, TerminalBridge)
    
    self.connected = false
    self.messageQueue = {}
    self.lastSync = 0
    self.terminalStatus = {
        terminal1 = "unknown",
        terminal2 = "unknown",
        debugger = "unknown"
    }
    
    self:initialize()
    
    return self
end

function TerminalBridge:initialize()
    -- Enable HTTP requests
    if not HttpService.HttpEnabled then
        warn("HTTP is not enabled! Enable it in Game Settings > Security")
        return
    end
    
    -- Set up message subscription
    local success, err = pcall(function()
        MessagingService:SubscribeAsync("TerminalSync", function(message)
            self:handleTerminalMessage(message)
        end)
    end)
    
    if not success then
        warn("Failed to subscribe to MessagingService: " .. tostring(err))
    end
    
    -- Start sync loop
    self:startSyncLoop()
    
    -- Verify all terminals
    self:verifyAllTerminals()
end

function TerminalBridge:verifyAllTerminals()
    -- Verify Terminal 1 (Backend)
    spawn(function()
        local success, response = pcall(function()
            return HttpService:RequestAsync({
                Url = TERMINAL1_URL .. "/health",
                Method = "GET",
                Headers = {
                    ["Content-Type"] = "application/json"
                }
            })
        end)
        
        if success and response.StatusCode == 200 then
            self.terminalStatus.terminal1 = "connected"
            print("✅ Terminal 1 (Backend): Connected")
            
            -- Register plugin with Terminal 1
            self:registerPlugin()
        else
            self.terminalStatus.terminal1 = "disconnected"
            warn("❌ Terminal 1 (Backend): Not responding")
        end
    end)
    
    -- Verify Terminal 2 (Dashboard)
    spawn(function()
        local success = pcall(function()
            -- Check if dashboard is accessible
            HttpService:GetAsync(TERMINAL2_URL)
        end)
        
        if success then
            self.terminalStatus.terminal2 = "connected"
            print("✅ Terminal 2 (Dashboard): Connected")
        else
            self.terminalStatus.terminal2 = "disconnected"
            warn("❌ Terminal 2 (Dashboard): Not responding")
        end
    end)
    
    -- Send verification to Debugger
    self:sendToDebugger({
        type = "verification",
        terminal = "terminal3",
        status = self.terminalStatus,
        timestamp = os.time()
    })
end

function TerminalBridge:registerPlugin()
    local pluginData = {
        plugin_id = game.PlaceId or "test_place",
        version = "1.0.0",
        capabilities = {
            "content_generation",
            "quiz_system",
            "progress_tracking",
            "achievements",
            "real_time_sync"
        },
        student_count = #game.Players:GetPlayers()
    }
    
    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = TERMINAL1_URL .. "/register_plugin",
            Method = "POST",
            Headers = {
                ["Content-Type"] = "application/json"
            },
            Body = HttpService:JSONEncode(pluginData)
        })
    end)
    
    if success and response.StatusCode == 200 then
        self.connected = true
        print("✅ Plugin registered with Terminal 1")
        
        -- Notify Terminal 2
        self:notifyDashboard("plugin_connected", pluginData)
    else
        warn("Failed to register plugin")
    end
end

function TerminalBridge:sendToTerminal1(endpoint, data)
    if not self.connected then
        table.insert(self.messageQueue, {terminal = 1, endpoint = endpoint, data = data})
        return nil
    end
    
    local url = TERMINAL1_URL .. endpoint
    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = url,
            Method = "POST",
            Headers = {
                ["Content-Type"] = "application/json",
                ["X-Plugin-ID"] = tostring(game.PlaceId or "test")
            },
            Body = HttpService:JSONEncode(data)
        })
    end)
    
    if success and response.StatusCode == 200 then
        local responseData = HttpService:JSONDecode(response.Body)
        
        -- Forward to Terminal 2 if needed
        if responseData.notify_dashboard then
            self:notifyDashboard(endpoint, responseData)
        end
        
        return responseData
    else
        warn("Failed to send to Terminal 1: " .. endpoint)
        return nil
    end
end

function TerminalBridge:notifyDashboard(event, data)
    -- Send via Terminal 1's WebSocket bridge
    self:sendToTerminal1("/dashboard/notify", {
        event = event,
        data = data,
        plugin_id = game.PlaceId or "test",
        timestamp = os.time()
    })
end

function TerminalBridge:sendToDebugger(data)
    -- Send monitoring data to debugger terminal
    self:sendToTerminal1("/debug/metrics", {
        source = "terminal3",
        metrics = data
    })
end

function TerminalBridge:startSyncLoop()
    RunService.Heartbeat:Connect(function()
        local now = tick()
        if now - self.lastSync >= SYNC_INTERVAL then
            self.lastSync = now
            self:syncWithAllTerminals()
        end
    end)
end

function TerminalBridge:syncWithAllTerminals()
    -- Collect current game state
    local gameState = {
        player_count = #game.Players:GetPlayers(),
        active_lessons = self:getActiveLessons(),
        performance_metrics = self:getPerformanceMetrics(),
        error_count = self:getErrorCount()
    }
    
    -- Send to Terminal 1
    spawn(function()
        self:sendToTerminal1("/sync/game-state", gameState)
    end)
    
    -- Process message queue
    if #self.messageQueue > 0 and self.connected then
        for _, message in ipairs(self.messageQueue) do
            self:sendToTerminal1(message.endpoint, message.data)
        end
        self.messageQueue = {}
    end
end

function TerminalBridge:handleTerminalMessage(message)
    local data = message.Data
    
    if data.from == "terminal1" then
        self:handleTerminal1Message(data)
    elseif data.from == "terminal2" then
        self:handleTerminal2Message(data)
    elseif data.from == "debugger" then
        self:handleDebuggerMessage(data)
    end
end

function TerminalBridge:handleTerminal1Message(data)
    if data.type == "content_update" then
        -- Deploy new content to game
        self:deployContent(data.content)
    elseif data.type == "command" then
        -- Execute command from backend
        self:executeCommand(data.command, data.parameters)
    elseif data.type == "config_update" then
        -- Update game configuration
        self:updateConfiguration(data.config)
    end
end

function TerminalBridge:handleTerminal2Message(data)
    if data.type == "ui_command" then
        -- Execute UI command from dashboard
        self:executeUICommand(data.command)
    elseif data.type == "student_query" then
        -- Respond with student data
        self:sendStudentData(data.student_id)
    end
end

function TerminalBridge:handleDebuggerMessage(data)
    if data.type == "performance_alert" then
        -- Optimize based on debugger feedback
        self:optimizePerformance(data.suggestions)
    elseif data.type == "security_warning" then
        -- Handle security issue
        self:handleSecurityWarning(data.warning)
    end
end

-- Helper functions
function TerminalBridge:getActiveLessons()
    local lessons = {}
    -- Collect active lesson data from workspace
    for _, obj in pairs(workspace:GetChildren()) do
        if obj.Name:match("^Lesson_") then
            table.insert(lessons, {
                id = obj.Name:gsub("Lesson_", ""),
                player_count = 0  -- Count players in lesson area
            })
        end
    end
    return lessons
end

function TerminalBridge:getPerformanceMetrics()
    return {
        fps = workspace:GetRealPhysicsFPS(),
        memory = game:GetService("Stats").GetTotalMemoryUsageMb and game:GetService("Stats"):GetTotalMemoryUsageMb() or 0,
        ping = game.Players.LocalPlayer and game.Players.LocalPlayer:GetNetworkPing() or 0
    }
end

function TerminalBridge:getErrorCount()
    -- Track script errors (placeholder)
    return 0
end

function TerminalBridge:deployContent(content)
    -- Delegate to ContentDeployer module
    local ContentDeployer = require(script.Parent.ContentDeployer)
    if ContentDeployer then
        ContentDeployer:deployLesson(content)
    end
end

function TerminalBridge:executeCommand(command, parameters)
    print("Executing command:", command)
    -- Command execution logic
end

function TerminalBridge:updateConfiguration(config)
    print("Updating configuration:", config)
    -- Configuration update logic
end

function TerminalBridge:executeUICommand(command)
    print("Executing UI command:", command)
    -- UI command execution logic
end

function TerminalBridge:sendStudentData(studentId)
    -- Collect and send student data
    local studentData = {
        id = studentId,
        progress = {},
        achievements = {}
    }
    self:sendToTerminal1("/student/data", studentData)
end

function TerminalBridge:optimizePerformance(suggestions)
    print("Optimizing performance based on suggestions")
    -- Performance optimization logic
end

function TerminalBridge:handleSecurityWarning(warning)
    warn("Security warning:", warning)
    -- Security handling logic
end

return TerminalBridge
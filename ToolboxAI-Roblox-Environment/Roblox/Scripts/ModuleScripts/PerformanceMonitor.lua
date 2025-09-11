--[[
    ToolboxAI Performance Monitor Module
    Terminal 3 - Performance Tracking and Optimization
    Monitors game performance and sends metrics to all terminals
]]

local RunService = game:GetService("RunService")
local Stats = game:GetService("Stats")
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")

local PerformanceMonitor = {}
PerformanceMonitor.__index = PerformanceMonitor

function PerformanceMonitor.new(terminalBridge)
    local self = setmetatable({}, PerformanceMonitor)
    
    self.bridge = terminalBridge
    self.metrics = {
        fps = {},
        memory = {},
        ping = {},
        dataReceive = {},
        dataSend = {},
        heartbeat = {},
        physics = {},
        render = {},
        errors = 0,
        warnings = 0
    }
    self.monitoring = false
    self.reportInterval = 30  -- seconds
    self.lastReport = 0
    self.performanceThresholds = {
        lowFPS = 30,
        highMemory = 500,  -- MB
        highPing = 200,    -- ms
        criticalErrors = 10
    }
    
    return self
end

function PerformanceMonitor:start()
    if self.monitoring then return end
    self.monitoring = true
    
    print("🔍 Performance monitoring started")
    
    -- FPS monitoring
    self:startFPSMonitoring()
    
    -- Memory monitoring
    self:startMemoryMonitoring()
    
    -- Network monitoring
    self:startNetworkMonitoring()
    
    -- Physics monitoring
    self:startPhysicsMonitoring()
    
    -- Error tracking
    self:startErrorTracking()
    
    -- Regular reporting
    self:startReporting()
    
    return true
end

function PerformanceMonitor:stop()
    self.monitoring = false
    print("🛑 Performance monitoring stopped")
end

function PerformanceMonitor:startFPSMonitoring()
    local frameCount = 0
    local frameTime = 0
    
    RunService.RenderStepped:Connect(function(deltaTime)
        if not self.monitoring then return end
        
        frameCount = frameCount + 1
        frameTime = frameTime + deltaTime
        
        -- Calculate FPS every second
        if frameTime >= 1 then
            local fps = frameCount / frameTime
            table.insert(self.metrics.fps, fps)
            
            -- Keep only last 60 samples
            if #self.metrics.fps > 60 then
                table.remove(self.metrics.fps, 1)
            end
            
            -- Check for low FPS
            if fps < self.performanceThresholds.lowFPS then
                self:handleLowFPS(fps)
            end
            
            frameCount = 0
            frameTime = 0
        end
    end)
end

function PerformanceMonitor:startMemoryMonitoring()
    spawn(function()
        while self.monitoring do
            local memory = self:getMemoryUsage()
            table.insert(self.metrics.memory, memory)
            
            -- Keep only last 60 samples
            if #self.metrics.memory > 60 then
                table.remove(self.metrics.memory, 1)
            end
            
            -- Alert if memory is high
            if memory > self.performanceThresholds.highMemory then
                self:alertHighMemory(memory)
            end
            
            wait(1)
        end
    end)
end

function PerformanceMonitor:startNetworkMonitoring()
    spawn(function()
        while self.monitoring do
            -- Get network stats
            local networkStats = self:getNetworkStats()
            
            table.insert(self.metrics.dataReceive, networkStats.receive)
            table.insert(self.metrics.dataSend, networkStats.send)
            table.insert(self.metrics.ping, networkStats.ping)
            
            -- Keep only last 60 samples
            if #self.metrics.dataReceive > 60 then
                table.remove(self.metrics.dataReceive, 1)
                table.remove(self.metrics.dataSend, 1)
                table.remove(self.metrics.ping, 1)
            end
            
            -- Check for high ping
            if networkStats.ping > self.performanceThresholds.highPing then
                self:handleHighPing(networkStats.ping)
            end
            
            wait(1)
        end
    end)
end

function PerformanceMonitor:startPhysicsMonitoring()
    spawn(function()
        while self.monitoring do
            local physicsFPS = workspace:GetRealPhysicsFPS()
            table.insert(self.metrics.physics, physicsFPS)
            
            -- Keep only last 60 samples
            if #self.metrics.physics > 60 then
                table.remove(self.metrics.physics, 1)
            end
            
            -- Check for physics issues
            if physicsFPS < 30 then
                self:handlePhysicsIssue(physicsFPS)
            end
            
            wait(1)
        end
    end)
end

function PerformanceMonitor:startErrorTracking()
    -- Track script errors
    game:GetService("ScriptContext").Error:Connect(function(message, stack, script)
        if not self.monitoring then return end
        
        self.metrics.errors = self.metrics.errors + 1
        
        -- Log error details
        local errorData = {
            message = message,
            stack = stack,
            script = script and script:GetFullName() or "Unknown",
            timestamp = os.time()
        }
        
        -- Send critical errors immediately
        if self.metrics.errors >= self.performanceThresholds.criticalErrors then
            self:sendCriticalAlert("errors", errorData)
        end
    end)
end

function PerformanceMonitor:startReporting()
    spawn(function()
        while self.monitoring do
            wait(self.reportInterval)
            self:sendMetricsToDebugger()
        end
    end)
end

function PerformanceMonitor:getMemoryUsage()
    -- Try multiple methods to get memory usage
    local memory = 0
    
    -- Method 1: Stats service
    local success, result = pcall(function()
        return Stats:GetTotalMemoryUsageMb()
    end)
    
    if success and result then
        memory = result
    else
        -- Method 2: Performance stats
        local perfStats = Stats.PerformanceStats
        if perfStats then
            memory = perfStats.Memory and perfStats.Memory:GetValue() or 0
        end
    end
    
    return memory
end

function PerformanceMonitor:getNetworkStats()
    local stats = {
        receive = 0,
        send = 0,
        ping = 0
    }
    
    -- Get data receive/send rates
    local networkStats = Stats.PerformanceStats
    if networkStats then
        stats.receive = networkStats.NetworkReceive and networkStats.NetworkReceive:GetValue() or 0
        stats.send = networkStats.NetworkSend and networkStats.NetworkSend:GetValue() or 0
    end
    
    -- Get ping from local player
    local localPlayer = Players.LocalPlayer
    if localPlayer then
        local success, ping = pcall(function()
            return localPlayer:GetNetworkPing()
        end)
        if success then
            stats.ping = ping * 1000  -- Convert to milliseconds
        end
    end
    
    return stats
end

function PerformanceMonitor:getAverageMetrics()
    local function average(t)
        if #t == 0 then return 0 end
        local sum = 0
        for _, v in ipairs(t) do
            sum = sum + v
        end
        return sum / #t
    end
    
    local function minimum(t)
        if #t == 0 then return 0 end
        local min = t[1]
        for _, v in ipairs(t) do
            if v < min then min = v end
        end
        return min
    end
    
    local function maximum(t)
        if #t == 0 then return 0 end
        local max = t[1]
        for _, v in ipairs(t) do
            if v > max then max = v end
        end
        return max
    end
    
    return {
        avgFPS = average(self.metrics.fps),
        minFPS = minimum(self.metrics.fps),
        maxFPS = maximum(self.metrics.fps),
        avgMemory = average(self.metrics.memory),
        maxMemory = maximum(self.metrics.memory),
        avgPing = average(self.metrics.ping),
        avgDataReceive = average(self.metrics.dataReceive),
        avgDataSend = average(self.metrics.dataSend),
        avgPhysics = average(self.metrics.physics),
        errorCount = self.metrics.errors,
        warningCount = self.metrics.warnings
    }
end

function PerformanceMonitor:sendMetricsToDebugger()
    local metrics = self:getAverageMetrics()
    metrics.timestamp = os.time()
    metrics.terminal = "terminal3"
    metrics.playerCount = #Players:GetPlayers()
    metrics.placeId = game.PlaceId
    
    -- Determine overall health
    metrics.health = self:calculateHealthScore(metrics)
    
    -- Send via Terminal Bridge if available
    if self.bridge then
        self.bridge:sendToDebugger({
            type = "performance_metrics",
            metrics = metrics
        })
        
        -- Also send to Terminal 1
        self.bridge:sendToTerminal1("/metrics/roblox", metrics)
    else
        -- Direct send if no bridge
        spawn(function()
            pcall(function()
                HttpService:PostAsync(
                    "http://127.0.0.1:5001/metrics/roblox",
                    HttpService:JSONEncode(metrics)
                )
            end)
        end)
    end
    
    -- Log summary
    print(string.format("📊 Performance: FPS=%.1f, Memory=%dMB, Ping=%dms, Health=%d%%",
        metrics.avgFPS, metrics.avgMemory, metrics.avgPing, metrics.health))
end

function PerformanceMonitor:calculateHealthScore(metrics)
    local score = 100
    
    -- FPS impact (0-40 points)
    if metrics.avgFPS < 60 then
        score = score - math.min(40, (60 - metrics.avgFPS) * 2)
    end
    
    -- Memory impact (0-20 points)
    if metrics.avgMemory > 300 then
        score = score - math.min(20, (metrics.avgMemory - 300) / 10)
    end
    
    -- Ping impact (0-20 points)
    if metrics.avgPing > 100 then
        score = score - math.min(20, (metrics.avgPing - 100) / 10)
    end
    
    -- Error impact (0-20 points)
    if metrics.errorCount > 0 then
        score = score - math.min(20, metrics.errorCount * 2)
    end
    
    return math.max(0, math.floor(score))
end

function PerformanceMonitor:handleLowFPS(fps)
    warn("⚠️ Low FPS detected:", math.floor(fps))
    
    -- Notify debugger
    if self.bridge then
        self.bridge:sendToDebugger({
            type = "performance_alert",
            severity = "warning",
            issue = "low_fps",
            value = fps,
            terminal = "terminal3"
        })
    end
    
    -- Try to optimize
    self:optimizeForFPS()
end

function PerformanceMonitor:handleHighPing(ping)
    warn("⚠️ High ping detected:", math.floor(ping), "ms")
    
    -- Notify debugger
    if self.bridge then
        self.bridge:sendToDebugger({
            type = "network_alert",
            severity = "warning",
            issue = "high_ping",
            value = ping,
            terminal = "terminal3"
        })
    end
end

function PerformanceMonitor:handlePhysicsIssue(physicsFPS)
    warn("⚠️ Physics performance issue:", math.floor(physicsFPS), "FPS")
    
    -- Notify debugger
    if self.bridge then
        self.bridge:sendToDebugger({
            type = "physics_alert",
            severity = "warning",
            issue = "low_physics_fps",
            value = physicsFPS,
            terminal = "terminal3"
        })
    end
    
    -- Try to optimize physics
    self:optimizePhysics()
end

function PerformanceMonitor:alertHighMemory(memory)
    warn("⚠️ High memory usage:", math.floor(memory), "MB")
    
    -- Notify debugger
    if self.bridge then
        self.bridge:sendToDebugger({
            type = "memory_alert",
            severity = "warning",
            message = "High memory usage in Roblox: " .. math.floor(memory) .. "MB",
            terminal = "terminal3"
        })
    end
    
    -- Try to optimize
    self:optimizeMemory()
end

function PerformanceMonitor:sendCriticalAlert(alertType, data)
    warn("🚨 CRITICAL:", alertType, "-", data.message or "Multiple issues detected")
    
    if self.bridge then
        self.bridge:sendToDebugger({
            type = "critical_alert",
            severity = "critical",
            alert_type = alertType,
            data = data,
            terminal = "terminal3",
            timestamp = os.time()
        })
    end
end

function PerformanceMonitor:optimizeMemory()
    print("🔧 Optimizing memory...")
    
    -- Clear debris
    local debris = game:GetService("Debris")
    for _, item in pairs(workspace:GetDescendants()) do
        if item:IsA("Debris") then
            item:Destroy()
        end
    end
    
    -- Clear temporary objects
    local tempFolder = workspace:FindFirstChild("TempObjects")
    if tempFolder then
        tempFolder:ClearAllChildren()
    end
    
    -- Reduce texture quality if needed
    local rendering = settings().Rendering
    if rendering.QualityLevel > Enum.QualityLevel.Level01 then
        rendering.QualityLevel = Enum.QualityLevel.Level01
        print("Reduced rendering quality to save memory")
    end
    
    -- Clear unused sounds
    for _, sound in pairs(workspace:GetDescendants()) do
        if sound:IsA("Sound") and not sound.IsPlaying then
            sound:Destroy()
        end
    end
end

function PerformanceMonitor:optimizeForFPS()
    print("🔧 Optimizing for FPS...")
    
    -- Reduce particle effects
    for _, emitter in pairs(workspace:GetDescendants()) do
        if emitter:IsA("ParticleEmitter") then
            emitter.Rate = emitter.Rate * 0.5
        end
    end
    
    -- Reduce lighting quality
    local lighting = game:GetService("Lighting")
    lighting.GlobalShadows = false
    lighting.Technology = Enum.Technology.Compatibility
    
    -- Reduce render distance
    local camera = workspace.CurrentCamera
    if camera then
        camera.FieldOfView = math.min(camera.FieldOfView, 70)
    end
end

function PerformanceMonitor:optimizePhysics()
    print("🔧 Optimizing physics...")
    
    -- Set non-essential parts to non-collidable
    for _, part in pairs(workspace:GetDescendants()) do
        if part:IsA("BasePart") and part.Name:match("Decoration") then
            part.CanCollide = false
            part.CanQuery = false
            part.CanTouch = false
        end
    end
    
    -- Reduce physics simulation rate for distant objects
    workspace.SignalBehavior = Enum.SignalBehavior.Deferred
end

function PerformanceMonitor:getReport()
    local metrics = self:getAverageMetrics()
    local health = self:calculateHealthScore(metrics)
    
    return {
        summary = {
            health = health,
            status = health > 80 and "Excellent" or health > 60 and "Good" or health > 40 and "Fair" or "Poor"
        },
        metrics = metrics,
        recommendations = self:getRecommendations(metrics),
        timestamp = os.time()
    }
end

function PerformanceMonitor:getRecommendations(metrics)
    local recommendations = {}
    
    if metrics.avgFPS < 30 then
        table.insert(recommendations, "Reduce graphics quality or particle effects")
    end
    
    if metrics.avgMemory > 400 then
        table.insert(recommendations, "Clear unused objects and reduce texture quality")
    end
    
    if metrics.avgPing > 150 then
        table.insert(recommendations, "Check network connection or reduce data transfer rate")
    end
    
    if metrics.errorCount > 5 then
        table.insert(recommendations, "Review and fix script errors")
    end
    
    return recommendations
end

return PerformanceMonitor
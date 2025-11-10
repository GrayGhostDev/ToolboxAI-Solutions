--!strict
--[[
    Enhanced ToolboxAI Integration Plugin for Roblox Studio
    Version: 2.0.0

    Features:
    - Modular MVC architecture
    - Integration with enhanced content pipeline
    - Real-time WebSocket/Pusher updates
    - Advanced UI components with Roact
    - State management system
    - Comprehensive error handling
    - Plugin settings persistence
]]

-- Services
local Selection = game:GetService("Selection")
local ChangeHistoryService = game:GetService("ChangeHistoryService")
local StudioService = game:GetService("StudioService")
local HttpService = game:GetService("HttpService")
local RunService = game:GetService("RunService")
local ServerScriptService = game:GetService("ServerScriptService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local StarterPlayer = game:GetService("StarterPlayer")
local DataStoreService = game:GetService("DataStoreService")
local CollectionService = game:GetService("CollectionService")
local TweenService = game:GetService("TweenService")
local MarketplaceService = game:GetService("MarketplaceService")

-- Plugin Configuration
local CONFIG = {
    FLASK_BRIDGE_URL = "http://127.0.0.1:5001",
    FASTAPI_URL = "http://127.0.0.1:8009",
    PUSHER_KEY = "your-pusher-key",
    PUSHER_CLUSTER = "mt1",
    VERSION = "2.0.0",
    DEBUG_MODE = true,
    AUTO_SAVE_INTERVAL = 60, -- seconds
    MAX_RETRY_ATTEMPTS = 3,
    RETRY_DELAY = 2, -- seconds
    CACHE_EXPIRY = 300, -- seconds
}

-- State Management System
local StateManager = {}
StateManager.__index = StateManager

function StateManager.new()
    local self = setmetatable({}, StateManager)
    self.state = {
        isConnected = false,
        isGenerating = false,
        currentPipeline = nil,
        generationProgress = 0,
        selectedAssets = {},
        userSettings = {},
        collaborators = {},
        history = {},
        cache = {},
    }
    self.listeners = {}
    return self
end

function StateManager:setState(key: string, value: any)
    local oldValue = self.state[key]
    self.state[key] = value
    self:notifyListeners(key, oldValue, value)
end

function StateManager:getState(key: string)
    return self.state[key]
end

function StateManager:subscribe(key: string, callback: (any, any) -> ())
    if not self.listeners[key] then
        self.listeners[key] = {}
    end
    table.insert(self.listeners[key], callback)
end

function StateManager:notifyListeners(key: string, oldValue: any, newValue: any)
    if self.listeners[key] then
        for _, callback in ipairs(self.listeners[key]) do
            task.spawn(callback, oldValue, newValue)
        end
    end
end

-- Error Handler Module
local ErrorHandler = {}
ErrorHandler.__index = ErrorHandler

function ErrorHandler.new()
    local self = setmetatable({}, ErrorHandler)
    self.errors = {}
    self.maxErrors = 100
    return self
end

function ErrorHandler:logError(error: string, context: string?)
    local errorEntry = {
        message = error,
        context = context or "Unknown",
        timestamp = os.time(),
        stackTrace = debug.traceback()
    }

    table.insert(self.errors, 1, errorEntry)

    -- Keep only the most recent errors
    if #self.errors > self.maxErrors then
        table.remove(self.errors, #self.errors)
    end

    if CONFIG.DEBUG_MODE then
        warn("[ToolboxAI Error]", context, ":", error)
    end

    return errorEntry
end

function ErrorHandler:getRecentErrors(count: number?)
    count = count or 10
    local recent = {}
    for i = 1, math.min(count, #self.errors) do
        table.insert(recent, self.errors[i])
    end
    return recent
end

function ErrorHandler:clearErrors()
    self.errors = {}
end

-- HTTP Client with retry logic
local HttpClient = {}
HttpClient.__index = HttpClient

function HttpClient.new(baseUrl: string)
    local self = setmetatable({}, HttpClient)
    self.baseUrl = baseUrl
    self.headers = {
        ["Content-Type"] = "application/json",
        ["X-Plugin-Version"] = CONFIG.VERSION,
    }
    return self
end

function HttpClient:setAuthToken(token: string)
    self.headers["Authorization"] = "Bearer " .. token
end

function HttpClient:request(method: string, endpoint: string, body: any?, retries: number?)
    retries = retries or CONFIG.MAX_RETRY_ATTEMPTS
    local url = self.baseUrl .. endpoint

    local requestOptions = {
        Url = url,
        Method = method,
        Headers = self.headers,
    }

    if body then
        requestOptions.Body = HttpService:JSONEncode(body)
    end

    for attempt = 1, retries do
        local success, response = pcall(function()
            return HttpService:RequestAsync(requestOptions)
        end)

        if success then
            if response.Success then
                return true, HttpService:JSONDecode(response.Body)
            elseif response.StatusCode == 429 then
                -- Rate limited, wait longer
                task.wait(CONFIG.RETRY_DELAY * attempt)
            else
                return false, {
                    error = "HTTP Error",
                    statusCode = response.StatusCode,
                    message = response.Body
                }
            end
        else
            if attempt < retries then
                task.wait(CONFIG.RETRY_DELAY)
            else
                return false, {
                    error = "Network Error",
                    message = tostring(response)
                }
            end
        end
    end

    return false, {error = "Max retries exceeded"}
end

-- Cache Manager for performance
local CacheManager = {}
CacheManager.__index = CacheManager

function CacheManager.new()
    local self = setmetatable({}, CacheManager)
    self.cache = {}
    return self
end

function CacheManager:set(key: string, value: any, ttl: number?)
    ttl = ttl or CONFIG.CACHE_EXPIRY
    self.cache[key] = {
        value = value,
        expiry = os.time() + ttl
    }
end

function CacheManager:get(key: string)
    local entry = self.cache[key]
    if entry and entry.expiry > os.time() then
        return entry.value
    end
    self.cache[key] = nil
    return nil
end

function CacheManager:invalidate(pattern: string?)
    if pattern then
        for key in pairs(self.cache) do
            if string.find(key, pattern) then
                self.cache[key] = nil
            end
        end
    else
        self.cache = {}
    end
end

-- Settings Manager for persistence
local SettingsManager = {}
SettingsManager.__index = SettingsManager

function SettingsManager.new(plugin: Plugin)
    local self = setmetatable({}, SettingsManager)
    self.plugin = plugin
    self.settings = {}
    self:load()
    return self
end

function SettingsManager:load()
    local savedSettings = self.plugin:GetSetting("ToolboxAI_Settings")
    if savedSettings then
        self.settings = HttpService:JSONDecode(savedSettings)
    else
        self.settings = {
            theme = "dark",
            autoSave = true,
            notifications = true,
            defaultQuality = "high",
            collaborationMode = false,
            hotReloadEnabled = true,
        }
    end
end

function SettingsManager:save()
    self.plugin:SetSetting("ToolboxAI_Settings", HttpService:JSONEncode(self.settings))
end

function SettingsManager:get(key: string)
    return self.settings[key]
end

function SettingsManager:set(key: string, value: any)
    self.settings[key] = value
    self:save()
end

-- Event Emitter for plugin-wide events
local EventEmitter = {}
EventEmitter.__index = EventEmitter

function EventEmitter.new()
    local self = setmetatable({}, EventEmitter)
    self.events = {}
    return self
end

function EventEmitter:on(event: string, callback: (...any) -> ())
    if not self.events[event] then
        self.events[event] = {}
    end
    table.insert(self.events[event], callback)
end

function EventEmitter:emit(event: string, ...: any)
    if self.events[event] then
        for _, callback in ipairs(self.events[event]) do
            task.spawn(callback, ...)
        end
    end
end

function EventEmitter:off(event: string, callback: (...any) -> ()?)
    if not self.events[event] then return end

    if callback then
        for i, cb in ipairs(self.events[event]) do
            if cb == callback then
                table.remove(self.events[event], i)
                break
            end
        end
    else
        self.events[event] = {}
    end
end

-- Main Plugin Controller
local PluginController = {}
PluginController.__index = PluginController

function PluginController.new(plugin: Plugin)
    local self = setmetatable({}, PluginController)

    self.plugin = plugin
    self.stateManager = StateManager.new()
    self.errorHandler = ErrorHandler.new()
    self.httpClient = HttpClient.new(CONFIG.FLASK_BRIDGE_URL)
    self.cacheManager = CacheManager.new()
    self.settingsManager = SettingsManager.new(plugin)
    self.eventEmitter = EventEmitter.new()

    -- UI Components (will be initialized later)
    self.toolbar = nil
    self.mainButton = nil
    self.widget = nil
    self.ui = nil

    -- Background tasks
    self.connections = {}
    self.heartbeatTask = nil

    return self
end

function PluginController:initialize()
    -- Create toolbar and button
    self.toolbar = self.plugin:CreateToolbar("ToolboxAI Enhanced")
    self.mainButton = self.toolbar:CreateButton(
        "AI Assistant",
        "Enhanced AI-powered content generation with real-time updates",
        "rbxasset://textures/ui/common/robux.png"
    )

    -- Create widget
    local widgetInfo = DockWidgetPluginGuiInfo.new(
        Enum.InitialDockState.Float,
        false,  -- Enabled
        false,  -- Override previous state
        500,    -- Default width
        700,    -- Default height
        450,    -- Min width
        400     -- Min height
    )

    self.widget = self.plugin:CreateDockWidgetPluginGui("ToolboxAI_Enhanced", widgetInfo)
    self.widget.Title = "ToolboxAI Enhanced Assistant"

    -- Set up event handlers
    self:setupEventHandlers()

    -- Initialize UI (will be implemented in separate module)
    self:initializeUI()

    -- Start background services
    self:startBackgroundServices()

    -- Connect to backend
    self:connectToBackend()

    print("[ToolboxAI] Enhanced plugin initialized successfully!")
end

function PluginController:setupEventHandlers()
    -- Button click handler
    self.mainButton.Click:Connect(function()
        self.widget.Enabled = not self.widget.Enabled
    end)

    -- Plugin unloading handler
    self.plugin.Unloading:Connect(function()
        self:cleanup()
    end)

    -- Selection change handler
    table.insert(self.connections, Selection.SelectionChanged:Connect(function()
        self.eventEmitter:emit("selectionChanged", Selection:Get())
    end))

    -- Auto-save handler
    if self.settingsManager:get("autoSave") then
        table.insert(self.connections, RunService.Heartbeat:Connect(function()
            -- Implement auto-save logic here
        end))
    end
end

function PluginController:initializeUI()
    -- This will be expanded with Roact components
    -- For now, create basic UI structure
    local frame = Instance.new("Frame")
    frame.Size = UDim2.new(1, 0, 1, 0)
    frame.BackgroundColor3 = Color3.fromRGB(30, 30, 30)
    frame.BorderSizePixel = 0
    frame.Parent = self.widget

    -- Status bar
    local statusBar = Instance.new("Frame")
    statusBar.Size = UDim2.new(1, 0, 0, 30)
    statusBar.Position = UDim2.new(0, 0, 1, -30)
    statusBar.BackgroundColor3 = Color3.fromRGB(20, 20, 20)
    statusBar.BorderSizePixel = 0
    statusBar.Parent = frame

    local statusLabel = Instance.new("TextLabel")
    statusLabel.Size = UDim2.new(1, -10, 1, 0)
    statusLabel.Position = UDim2.new(0, 5, 0, 0)
    statusLabel.BackgroundTransparency = 1
    statusLabel.Text = "Ready"
    statusLabel.TextColor3 = Color3.fromRGB(0, 255, 0)
    statusLabel.TextXAlignment = Enum.TextXAlignment.Left
    statusLabel.Font = Enum.Font.SourceSans
    statusLabel.TextSize = 14
    statusLabel.Parent = statusBar

    -- Subscribe to connection state changes
    self.stateManager:subscribe("isConnected", function(oldValue, newValue)
        statusLabel.Text = newValue and "Connected" or "Disconnected"
        statusLabel.TextColor3 = newValue and Color3.fromRGB(0, 255, 0) or Color3.fromRGB(255, 0, 0)
    end)

    self.ui = frame
end

function PluginController:startBackgroundServices()
    -- Start heartbeat for connection monitoring
    self.heartbeatTask = task.spawn(function()
        while true do
            task.wait(30) -- Check every 30 seconds
            self:checkConnection()
        end
    end)
end

function PluginController:connectToBackend()
    task.spawn(function()
        local success, response = self.httpClient:request("GET", "/api/plugin/connect", {
            version = CONFIG.VERSION,
            studioUserId = game:GetService("StudioService"):GetUserId()
        })

        if success then
            self.stateManager:setState("isConnected", true)
            if response.token then
                self.httpClient:setAuthToken(response.token)
            end
            self.eventEmitter:emit("connected", response)
        else
            self.errorHandler:logError("Failed to connect to backend", "Connection")
            self.stateManager:setState("isConnected", false)
        end
    end)
end

function PluginController:checkConnection()
    task.spawn(function()
        local success, response = self.httpClient:request("GET", "/api/plugin/ping")
        self.stateManager:setState("isConnected", success)
    end)
end

function PluginController:cleanup()
    -- Cancel background tasks
    if self.heartbeatTask then
        task.cancel(self.heartbeatTask)
    end

    -- Disconnect all connections
    for _, connection in ipairs(self.connections) do
        connection:Disconnect()
    end

    -- Save settings
    self.settingsManager:save()

    -- Clear cache
    self.cacheManager:invalidate()

    print("[ToolboxAI] Plugin cleanup completed")
end

-- Initialize the plugin
local pluginController = PluginController.new(plugin)
pluginController:initialize()

-- Export for testing and module access
return {
    Controller = pluginController,
    StateManager = StateManager,
    ErrorHandler = ErrorHandler,
    HttpClient = HttpClient,
    CacheManager = CacheManager,
    SettingsManager = SettingsManager,
    EventEmitter = EventEmitter,
    CONFIG = CONFIG
}

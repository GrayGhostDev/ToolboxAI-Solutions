--[[
    PluginConfig.lua
    Configuration management for ToolboxAI Roblox Studio Plugin
    
    This module handles all configuration settings for the AI Content Generator plugin,
    including API endpoints, user preferences, and connection settings.
]]

local HttpService = game:GetService("HttpService")
local RunService = game:GetService("RunService")

local PluginConfig = {}
PluginConfig.__index = PluginConfig

-- Default configuration values
local DEFAULT_CONFIG = {
    -- API Endpoints
    API = {
        FASTAPI_HOST = "127.0.0.1",
        FASTAPI_PORT = 8008,
        FLASK_HOST = "127.0.0.1",
        FLASK_PORT = 5001,
        MCP_HOST = "127.0.0.1",
        MCP_PORT = 9876,
        PLUGIN_PORT = 64989,
        
        -- Constructed URLs
        FASTAPI_URL = "http://127.0.0.1:8008",
        FLASK_URL = "http://127.0.0.1:5001",
        MCP_WS_URL = "ws://127.0.0.1:9876",
    },
    
    -- User Preferences
    PREFERENCES = {
        autoSave = true,
        autoBackup = true,
        debugMode = false,
        verboseLogging = false,
        maxRetries = 3,
        requestTimeout = 30, -- seconds
        defaultSubject = "Mathematics",
        defaultGradeLevel = 5,
        defaultEnvironment = "classroom",
        includeQuizByDefault = true,
    },
    
    -- Feature Flags
    FEATURES = {
        enableWebSocket = true,
        enableAutoSync = true,
        enableTerrainGeneration = true,
        enableQuizSystem = true,
        enableGamification = true,
        enableAnalytics = true,
        enableCollaboration = false, -- Coming soon
    },
    
    -- Content Generation Settings
    CONTENT = {
        maxQuizQuestions = 10,
        minQuizQuestions = 3,
        defaultQuizDifficulty = "medium",
        maxContentLength = 5000,
        supportedSubjects = {
            "Mathematics",
            "Science",
            "History",
            "English",
            "Art",
            "Geography",
            "Computer Science",
            "Physics",
            "Chemistry",
            "Biology"
        },
        supportedEnvironments = {
            "classroom",
            "laboratory",
            "outdoor",
            "museum",
            "space_station",
            "underwater",
            "historical",
            "fantasy"
        },
        difficultyLevels = {
            "easy",
            "medium",
            "hard",
            "expert"
        }
    },
    
    -- Plugin Settings
    PLUGIN = {
        widgetSize = Vector2.new(400, 600),
        widgetMinSize = Vector2.new(300, 400),
        widgetTitle = "AI Content Generator",
        autoConnect = true,
        showNotifications = true,
        soundEnabled = true,
    },
    
    -- Authentication
    AUTH = {
        requireAuth = false, -- Set to true in production
        tokenExpiry = 3600, -- seconds
        refreshThreshold = 300, -- seconds before expiry to refresh
    },
    
    -- Rate Limiting
    RATE_LIMIT = {
        maxRequestsPerMinute = 60,
        maxContentPerHour = 100,
        cooldownPeriod = 60, -- seconds
    }
}

-- Create new configuration instance
function PluginConfig.new(plugin)
    local self = setmetatable({}, PluginConfig)
    
    self.plugin = plugin
    self.config = table.clone(DEFAULT_CONFIG)
    self.configPath = "ToolboxAI_Config"
    
    -- Load saved configuration
    self:loadConfig()
    
    -- Construct API URLs
    self:updateAPIUrls()
    
    return self
end

-- Update API URLs based on host and port settings
function PluginConfig:updateAPIUrls()
    self.config.API.FASTAPI_URL = string.format(
        "http://%s:%d",
        self.config.API.FASTAPI_HOST,
        self.config.API.FASTAPI_PORT
    )
    
    self.config.API.FLASK_URL = string.format(
        "http://%s:%d",
        self.config.API.FLASK_HOST,
        self.config.API.FLASK_PORT
    )
    
    self.config.API.MCP_WS_URL = string.format(
        "ws://%s:%d",
        self.config.API.MCP_HOST,
        self.config.API.MCP_PORT
    )
end

-- Load configuration from plugin settings
function PluginConfig:loadConfig()
    if not self.plugin then
        return
    end
    
    local success, savedConfig = pcall(function()
        local configString = self.plugin:GetSetting(self.configPath)
        if configString then
            return HttpService:JSONDecode(configString)
        end
        return nil
    end)
    
    if success and savedConfig then
        -- Merge saved config with defaults (preserves new fields)
        self:mergeConfig(savedConfig)
        
        if self.config.PREFERENCES.debugMode then
            print("[PluginConfig] Configuration loaded successfully")
        end
    else
        if self.config.PREFERENCES.debugMode then
            print("[PluginConfig] No saved configuration found, using defaults")
        end
    end
end

-- Save configuration to plugin settings
function PluginConfig:saveConfig()
    if not self.plugin then
        return false
    end
    
    local success, err = pcall(function()
        local configString = HttpService:JSONEncode(self.config)
        self.plugin:SetSetting(self.configPath, configString)
    end)
    
    if success then
        if self.config.PREFERENCES.debugMode then
            print("[PluginConfig] Configuration saved successfully")
        end
        return true
    else
        warn("[PluginConfig] Failed to save configuration:", err)
        return false
    end
end

-- Merge saved configuration with defaults
function PluginConfig:mergeConfig(savedConfig)
    local function deepMerge(target, source)
        for key, value in pairs(source) do
            if type(value) == "table" and type(target[key]) == "table" then
                deepMerge(target[key], value)
            else
                target[key] = value
            end
        end
    end
    
    deepMerge(self.config, savedConfig)
end

-- Get configuration value by path (e.g., "API.FASTAPI_URL")
function PluginConfig:get(path)
    local keys = string.split(path, ".")
    local current = self.config
    
    for _, key in ipairs(keys) do
        if type(current) == "table" and current[key] ~= nil then
            current = current[key]
        else
            return nil
        end
    end
    
    return current
end

-- Set configuration value by path
function PluginConfig:set(path, value)
    local keys = string.split(path, ".")
    local current = self.config
    
    -- Navigate to parent table
    for i = 1, #keys - 1 do
        local key = keys[i]
        if type(current[key]) ~= "table" then
            current[key] = {}
        end
        current = current[key]
    end
    
    -- Set the value
    current[keys[#keys]] = value
    
    -- Update API URLs if API settings changed
    if keys[1] == "API" then
        self:updateAPIUrls()
    end
    
    -- Auto-save if enabled
    if self.config.PREFERENCES.autoSave then
        self:saveConfig()
    end
end

-- Reset configuration to defaults
function PluginConfig:reset()
    self.config = table.clone(DEFAULT_CONFIG)
    self:updateAPIUrls()
    self:saveConfig()
    
    if self.config.PREFERENCES.debugMode then
        print("[PluginConfig] Configuration reset to defaults")
    end
end

-- Validate configuration
function PluginConfig:validate()
    local errors = {}
    
    -- Validate API ports
    if self.config.API.FASTAPI_PORT < 1 or self.config.API.FASTAPI_PORT > 65535 then
        table.insert(errors, "Invalid FastAPI port")
    end
    
    if self.config.API.FLASK_PORT < 1 or self.config.API.FLASK_PORT > 65535 then
        table.insert(errors, "Invalid Flask port")
    end
    
    -- Validate preferences
    if self.config.PREFERENCES.requestTimeout < 1 then
        table.insert(errors, "Request timeout must be at least 1 second")
    end
    
    if self.config.PREFERENCES.maxRetries < 0 then
        table.insert(errors, "Max retries cannot be negative")
    end
    
    -- Validate content settings
    if self.config.CONTENT.maxQuizQuestions < self.config.CONTENT.minQuizQuestions then
        table.insert(errors, "Max quiz questions must be >= min quiz questions")
    end
    
    return #errors == 0, errors
end

-- Export configuration as JSON string
function PluginConfig:export()
    return HttpService:JSONEncode(self.config)
end

-- Import configuration from JSON string
function PluginConfig:import(jsonString)
    local success, importedConfig = pcall(function()
        return HttpService:JSONDecode(jsonString)
    end)
    
    if success and importedConfig then
        self:mergeConfig(importedConfig)
        self:updateAPIUrls()
        
        local isValid, errors = self:validate()
        if isValid then
            self:saveConfig()
            return true, "Configuration imported successfully"
        else
            return false, "Invalid configuration: " .. table.concat(errors, ", ")
        end
    else
        return false, "Failed to parse configuration JSON"
    end
end

-- Get all available subjects
function PluginConfig:getSubjects()
    return self.config.CONTENT.supportedSubjects
end

-- Get all available environments
function PluginConfig:getEnvironments()
    return self.config.CONTENT.supportedEnvironments
end

-- Get all difficulty levels
function PluginConfig:getDifficultyLevels()
    return self.config.CONTENT.difficultyLevels
end

-- Check if a feature is enabled
function PluginConfig:isFeatureEnabled(featureName)
    return self.config.FEATURES[featureName] == true
end

-- Get API endpoint URL
function PluginConfig:getAPIEndpoint(endpoint)
    if endpoint == "fastapi" then
        return self.config.API.FASTAPI_URL
    elseif endpoint == "flask" then
        return self.config.API.FLASK_URL
    elseif endpoint == "mcp" then
        return self.config.API.MCP_WS_URL
    else
        return nil
    end
end

-- Create configuration GUI (for plugin settings panel)
function PluginConfig:createGUI(parent)
    local gui = Instance.new("Frame")
    gui.Size = UDim2.new(1, 0, 1, 0)
    gui.BackgroundColor3 = Color3.fromRGB(46, 46, 46)
    gui.BorderSizePixel = 0
    gui.Parent = parent
    
    -- Scrolling frame for settings
    local scrollFrame = Instance.new("ScrollingFrame")
    scrollFrame.Size = UDim2.new(1, -20, 1, -60)
    scrollFrame.Position = UDim2.new(0, 10, 0, 50)
    scrollFrame.BackgroundTransparency = 1
    scrollFrame.ScrollBarThickness = 6
    scrollFrame.Parent = gui
    
    -- Title
    local title = Instance.new("TextLabel")
    title.Size = UDim2.new(1, -20, 0, 40)
    title.Position = UDim2.new(0, 10, 0, 5)
    title.Text = "Plugin Configuration"
    title.TextColor3 = Color3.new(1, 1, 1)
    title.TextScaled = true
    title.BackgroundTransparency = 1
    title.Parent = gui
    
    local yOffset = 10
    
    -- Function to create a setting row
    local function createSettingRow(name, path, valueType, options)
        local row = Instance.new("Frame")
        row.Size = UDim2.new(1, -20, 0, 30)
        row.Position = UDim2.new(0, 10, 0, yOffset)
        row.BackgroundTransparency = 1
        row.Parent = scrollFrame
        
        local label = Instance.new("TextLabel")
        label.Size = UDim2.new(0.5, -5, 1, 0)
        label.Position = UDim2.new(0, 0, 0, 0)
        label.Text = name
        label.TextColor3 = Color3.new(0.8, 0.8, 0.8)
        label.TextXAlignment = Enum.TextXAlignment.Left
        label.BackgroundTransparency = 1
        label.Parent = row
        
        if valueType == "boolean" then
            local checkbox = Instance.new("TextButton")
            checkbox.Size = UDim2.new(0, 25, 0, 25)
            checkbox.Position = UDim2.new(0.5, 5, 0.5, -12.5)
            checkbox.Text = self:get(path) and "✓" or ""
            checkbox.BackgroundColor3 = Color3.fromRGB(60, 60, 60)
            checkbox.TextColor3 = Color3.new(0, 1, 0)
            checkbox.Parent = row
            
            checkbox.MouseButton1Click:Connect(function()
                local newValue = not self:get(path)
                self:set(path, newValue)
                checkbox.Text = newValue and "✓" or ""
            end)
            
        elseif valueType == "number" then
            local input = Instance.new("TextBox")
            input.Size = UDim2.new(0.3, 0, 0, 25)
            input.Position = UDim2.new(0.5, 5, 0.5, -12.5)
            input.Text = tostring(self:get(path))
            input.BackgroundColor3 = Color3.fromRGB(60, 60, 60)
            input.TextColor3 = Color3.new(1, 1, 1)
            input.Parent = row
            
            input.FocusLost:Connect(function()
                local newValue = tonumber(input.Text)
                if newValue then
                    self:set(path, newValue)
                else
                    input.Text = tostring(self:get(path))
                end
            end)
            
        elseif valueType == "string" then
            local input = Instance.new("TextBox")
            input.Size = UDim2.new(0.4, 0, 0, 25)
            input.Position = UDim2.new(0.5, 5, 0.5, -12.5)
            input.Text = self:get(path) or ""
            input.BackgroundColor3 = Color3.fromRGB(60, 60, 60)
            input.TextColor3 = Color3.new(1, 1, 1)
            input.Parent = row
            
            input.FocusLost:Connect(function()
                self:set(path, input.Text)
            end)
        end
        
        yOffset = yOffset + 35
    end
    
    -- Add configuration options
    createSettingRow("Debug Mode", "PREFERENCES.debugMode", "boolean")
    createSettingRow("Auto Save", "PREFERENCES.autoSave", "boolean")
    createSettingRow("Verbose Logging", "PREFERENCES.verboseLogging", "boolean")
    createSettingRow("FastAPI Port", "API.FASTAPI_PORT", "number")
    createSettingRow("Flask Port", "API.FLASK_PORT", "number")
    createSettingRow("Request Timeout (s)", "PREFERENCES.requestTimeout", "number")
    createSettingRow("Max Retries", "PREFERENCES.maxRetries", "number")
    createSettingRow("Default Subject", "PREFERENCES.defaultSubject", "string")
    createSettingRow("Default Grade Level", "PREFERENCES.defaultGradeLevel", "number")
    createSettingRow("Enable WebSocket", "FEATURES.enableWebSocket", "boolean")
    createSettingRow("Enable Auto Sync", "FEATURES.enableAutoSync", "boolean")
    createSettingRow("Enable Analytics", "FEATURES.enableAnalytics", "boolean")
    
    -- Update scrolling frame canvas size
    scrollFrame.CanvasSize = UDim2.new(0, 0, 0, yOffset + 20)
    
    return gui
end

return PluginConfig
--[[
    ToolboxAI Configuration Settings
    Version: 3.0.0
    Updated: 2025-09-18

    Main configuration file for the blank_environment.rbxl template
    SECURITY UPDATE: Removed all hardcoded URLs and credentials
    Now uses SecureConfigurationManager for sensitive data
--]]

local Settings = {}

-- Import secure configuration manager
local SecureConfigurationManager = require(game.ServerScriptService:WaitForChild("SecureConfigurationManager"))
local configManager = SecureConfigurationManager.getInstance()

-- Environment Configuration (non-sensitive only)
Settings.ENV = {
    ROBLOX_UNIVERSE_ID = "8505376973",
    ROBLOX_API_URL = "https://api.roblox.com",
    CLIENT_ID = "2214511122270781418",
    -- URLs are now loaded from SecureConfigurationManager
    -- No hardcoded URLs or credentials should exist here
}

-- API Configuration with dynamic URL loading
Settings.API = {
    -- Base URLs are loaded dynamically from secure storage
    getBaseUrl = function()
        return configManager:getEndpoint("BACKEND_URL")
    end,

    getBridgeUrl = function()
        return configManager:getEndpoint("BRIDGE_URL")
    end,

    getDashboardUrl = function()
        return configManager:getEndpoint("DASHBOARD_URL")
    end,

    universeId = Settings.ENV.ROBLOX_UNIVERSE_ID,

    -- Endpoint paths (only paths, not full URLs)
    endpoints = {
        -- Roblox endpoints
        roblox = "/api/v1/roblox",
        sessions = "/api/v1/roblox/sessions",
        templates = "/api/v1/roblox/templates",
        push = "/api/v1/roblox/push",
        sync = "/api/v1/roblox/sync",
        analytics = "/api/v1/roblox/analytics",

        -- Content
        content = "/api/v1/content",
        generate = "/api/v1/content/generate",

        -- Progress
        progress = "/api/v1/progress",
        checkpoint = "/api/v1/progress/checkpoint",

        -- Quiz
        quiz = "/api/v1/quiz",
        quizStart = "/api/v1/quiz/start",
        quizSubmit = "/api/v1/quiz/submit"
    },

    -- Build full endpoint URL
    buildEndpointUrl = function(endpointName)
        local baseUrl = Settings.API.getBaseUrl()
        if not baseUrl then
            warn("[Settings] No base URL configured - using mock mode")
            return nil
        end

        local endpoint = Settings.API.endpoints[endpointName]
        if not endpoint then
            warn("[Settings] Unknown endpoint: " .. tostring(endpointName))
            return nil
        end

        return baseUrl .. endpoint
    end,

    -- Build WebSocket URL
    buildWebSocketUrl = function()
        local baseUrl = Settings.API.getBaseUrl()
        if not baseUrl then
            return nil
        end

        -- Convert HTTP to WebSocket URL
        local wsUrl = baseUrl:gsub("^http", "ws")
        return wsUrl .. "/ws/roblox"
    end
}

-- Game Settings (non-sensitive)
Settings.GAME = {
    name = "ToolboxAI Educational Platform",
    version = "3.0.0",
    maxPlayers = 30,
    defaultMode = "collaborative",
    defaultDifficulty = "intermediate"
}

-- Educational Settings (non-sensitive)
Settings.EDUCATION = {
    subjects = {
        "Mathematics", "Science", "History", "Language",
        "Geography", "Art", "Music", "Computer Science"
    },
    gradeLevel = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12},
    contentTypes = {"lesson", "quiz", "activity", "exploration"}
}

-- Visual Settings (non-sensitive)
Settings.VISUALS = {
    theme = "modern",
    primaryColor = Color3.fromRGB(33, 150, 243),
    secondaryColor = Color3.fromRGB(76, 175, 80),
    uiScale = 1.0
}

-- Debug Settings (controlled by environment)
Settings.DEBUG = {
    -- Debug settings now come from SecureConfigurationManager
    isEnabled = function()
        return configManager:isFeatureEnabled("DEBUG_MODE")
    end,

    getLogLevel = function()
        if configManager:isFeatureEnabled("VERBOSE_LOGGING") then
            return "DEBUG"
        else
            return "INFO"
        end
    end,

    showStats = function()
        return configManager:isFeatureEnabled("DEBUG_MODE")
    end
}

-- Security Settings (from SecureConfigurationManager)
Settings.SECURITY = {
    requireAuthentication = function()
        return configManager:getSecuritySetting("REQUIRE_AUTHENTICATION")
    end,

    validateRequests = function()
        return configManager:getSecuritySetting("VALIDATE_REQUESTS")
    end,

    encryptionEnabled = function()
        return configManager:getSecuritySetting("ENCRYPTION_ENABLED")
    end
}

-- Helper function to make secure API calls
Settings.makeSecureAPICall = function(endpoint, method, data)
    local endpointName = endpoint:gsub("/api/v1/", ""):gsub("/", "_")
    return configManager:makeSecureRequest("BACKEND_URL", endpoint, method or "GET", data)
end

-- Helper function to check environment
Settings.getEnvironment = function()
    return configManager:getEnvironment()
end

Settings.isDevelopment = function()
    return configManager:isDevelopment()
end

Settings.isProduction = function()
    return configManager:isProduction()
end

-- Initialization message
if Settings.isDevelopment() then
    print("[Settings] Loaded in DEVELOPMENT mode - using development endpoints")
else
    print("[Settings] Loaded in PRODUCTION mode - using secure configuration")
end

return Settings
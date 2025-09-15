--[[
    ToolboxAI Configuration Settings
    Version: 2.0.0
    Updated: 2025-09-15

    Main configuration file for the blank_environment.rbxl template
    This loads into the blank Roblox environment and configures all systems
--]]

local Settings = {}

-- Environment Configuration from .env file
Settings.ENV = {
    ROBLOX_UNIVERSE_ID = "8505376973",
    ROBLOX_API_URL = "https://api.roblox.com",
    BACKEND_URL = "http://127.0.0.1:8008",
    BRIDGE_URL = "http://localhost:5001",
    PLUGIN_PORT = "64989",
    CLIENT_ID = "2214511122270781418"
}

-- API Configuration
Settings.API = {
    baseUrl = Settings.ENV.BACKEND_URL,
    bridgeUrl = Settings.ENV.BRIDGE_URL,
    universeId = Settings.ENV.ROBLOX_UNIVERSE_ID,
    pluginPort = Settings.ENV.PLUGIN_PORT,

    endpoints = {
        -- Roblox endpoints
        roblox = "/api/v1/roblox",
        sessions = "/api/v1/roblox/sessions",
        templates = "/api/v1/roblox/templates",
        push = "/api/v1/roblox/push",
        sync = "/api/v1/roblox/sync",
        analytics = "/api/v1/roblox/analytics",

        -- WebSocket
        ws = "ws://127.0.0.1:8008/ws/roblox",

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
    }
}

-- Game Settings
Settings.GAME = {
    name = "ToolboxAI Educational Platform",
    version = "2.0.0",
    maxPlayers = 30,
    defaultMode = "collaborative",
    defaultDifficulty = "intermediate"
}

-- Educational Settings
Settings.EDUCATION = {
    subjects = {
        "Mathematics", "Science", "History", "Language",
        "Geography", "Art", "Music", "Computer Science"
    },
    gradeLevel = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12},
    contentTypes = {"lesson", "quiz", "activity", "exploration"}
}

-- Visual Settings
Settings.VISUALS = {
    theme = "modern",
    primaryColor = Color3.fromRGB(33, 150, 243),
    secondaryColor = Color3.fromRGB(76, 175, 80),
    uiScale = 1.0
}

-- Debug Settings
Settings.DEBUG = {
    enabled = true,
    logLevel = "INFO",
    showStats = true
}

return Settings

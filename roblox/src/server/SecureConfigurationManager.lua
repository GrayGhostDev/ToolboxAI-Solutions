--[[
    ToolboxAI Secure Configuration Manager
    Version: 1.0.0
    Description: Manages configuration securely without hardcoded values
                 Uses ServerStorage attributes and environment-based config
--]]

local SecureConfigurationManager = {}
SecureConfigurationManager.__index = SecureConfigurationManager

-- Services
local ServerStorage = game:GetService("ServerStorage")
local RunService = game:GetService("RunService")
local HttpService = game:GetService("HttpService")

-- Cache for configuration values
local configCache = {}
local cacheExpiry = 300 -- 5 minutes cache

-- Environment detection
local function getEnvironment()
    -- Check if we're in Studio
    if RunService:IsStudio() then
        return "development"
    end

    -- Check ServerStorage for environment attribute
    local env = ServerStorage:GetAttribute("Environment")
    if env then
        return env
    end

    -- Check game place ID for environment detection
    local placeId = game.PlaceId
    if placeId == 0 then
        return "development" -- Local testing
    elseif placeId == 123456789 then -- Replace with your production place ID
        return "production"
    elseif placeId == 987654321 then -- Replace with your staging place ID
        return "staging"
    else
        return "development" -- Default to development for safety
    end
end

-- Configuration schemas for different environments
local ENVIRONMENT_CONFIGS = {
    development = {
        -- Development environment - local testing
        API_ENDPOINTS = {
            BACKEND_URL = nil, -- Will be loaded from ServerStorage
            BRIDGE_URL = nil,
            DASHBOARD_URL = nil
        },
        FEATURES = {
            DEBUG_MODE = true,
            VERBOSE_LOGGING = true,
            MOCK_RESPONSES = true,
            RATE_LIMITING = false
        },
        SECURITY = {
            REQUIRE_AUTHENTICATION = false,
            VALIDATE_REQUESTS = true,
            ENCRYPTION_ENABLED = false
        }
    },
    staging = {
        -- Staging environment - pre-production testing
        API_ENDPOINTS = {
            BACKEND_URL = nil,
            BRIDGE_URL = nil,
            DASHBOARD_URL = nil
        },
        FEATURES = {
            DEBUG_MODE = false,
            VERBOSE_LOGGING = true,
            MOCK_RESPONSES = false,
            RATE_LIMITING = true
        },
        SECURITY = {
            REQUIRE_AUTHENTICATION = true,
            VALIDATE_REQUESTS = true,
            ENCRYPTION_ENABLED = true
        }
    },
    production = {
        -- Production environment
        API_ENDPOINTS = {
            BACKEND_URL = nil,
            BRIDGE_URL = nil,
            DASHBOARD_URL = nil
        },
        FEATURES = {
            DEBUG_MODE = false,
            VERBOSE_LOGGING = false,
            MOCK_RESPONSES = false,
            RATE_LIMITING = true
        },
        SECURITY = {
            REQUIRE_AUTHENTICATION = true,
            VALIDATE_REQUESTS = true,
            ENCRYPTION_ENABLED = true
        }
    }
}

-- Constructor
function SecureConfigurationManager.new()
    local self = setmetatable({}, SecureConfigurationManager)
    self.environment = getEnvironment()
    self.config = ENVIRONMENT_CONFIGS[self.environment]
    self.lastCacheUpdate = 0

    -- Initialize secure storage
    self:initializeSecureStorage()

    -- Load configuration from ServerStorage
    self:loadConfiguration()

    return self
end

-- Initialize secure storage for sensitive data
function SecureConfigurationManager:initializeSecureStorage()
    -- Create secure configuration folder if it doesn't exist
    local configFolder = ServerStorage:FindFirstChild("SecureConfiguration")
    if not configFolder then
        configFolder = Instance.new("Folder")
        configFolder.Name = "SecureConfiguration"
        configFolder.Parent = ServerStorage

        -- Set default attributes (these should be set by server scripts or manually)
        if self.environment == "development" then
            -- Development defaults - these should NEVER be production values
            ServerStorage:SetAttribute("BACKEND_URL", "http://127.0.0.1:8008")
            ServerStorage:SetAttribute("BRIDGE_URL", "http://127.0.0.1:5001")
            ServerStorage:SetAttribute("DASHBOARD_URL", "http://127.0.0.1:5179")
        else
            -- Production/staging values should be set separately, not in code
            warn("[SecureConfig] No production URLs configured - please set ServerStorage attributes")
        end
    end
end

-- Load configuration from secure storage
function SecureConfigurationManager:loadConfiguration()
    -- Load API endpoints from ServerStorage attributes
    local backendUrl = ServerStorage:GetAttribute("BACKEND_URL")
    local bridgeUrl = ServerStorage:GetAttribute("BRIDGE_URL")
    local dashboardUrl = ServerStorage:GetAttribute("DASHBOARD_URL")

    if backendUrl then
        self.config.API_ENDPOINTS.BACKEND_URL = backendUrl
    end

    if bridgeUrl then
        self.config.API_ENDPOINTS.BRIDGE_URL = bridgeUrl
    end

    if dashboardUrl then
        self.config.API_ENDPOINTS.DASHBOARD_URL = dashboardUrl
    end

    -- Load API keys and secrets (never hardcode these)
    local apiKey = ServerStorage:GetAttribute("API_KEY")
    if apiKey then
        self.config.SECURITY.API_KEY = apiKey
    end

    local secretKey = ServerStorage:GetAttribute("SECRET_KEY")
    if secretKey then
        self.config.SECURITY.SECRET_KEY = secretKey
    end

    -- Update cache timestamp
    self.lastCacheUpdate = tick()
end

-- Get configuration value with caching
function SecureConfigurationManager:get(path)
    -- Check cache expiry
    if tick() - self.lastCacheUpdate > cacheExpiry then
        self:loadConfiguration()
    end

    -- Parse path (e.g., "API_ENDPOINTS.BACKEND_URL")
    local parts = string.split(path, ".")
    local value = self.config

    for _, part in ipairs(parts) do
        if value and type(value) == "table" then
            value = value[part]
        else
            return nil
        end
    end

    return value
end

-- Get API endpoint with validation
function SecureConfigurationManager:getEndpoint(endpointName)
    local url = self:get("API_ENDPOINTS." .. endpointName)

    if not url then
        if self.environment == "production" then
            error("[SecureConfig] Critical: No " .. endpointName .. " configured for production")
        else
            warn("[SecureConfig] No " .. endpointName .. " configured, using mock mode")
            return nil
        end
    end

    -- Validate URL format
    if not string.match(url, "^https?://") then
        error("[SecureConfig] Invalid URL format for " .. endpointName)
    end

    -- Never expose localhost URLs in production
    if self.environment == "production" then
        if string.find(url, "localhost") or string.find(url, "127.0.0.1") then
            error("[SecureConfig] SECURITY: Localhost URL detected in production!")
        end
    end

    return url
end

-- Get feature flag
function SecureConfigurationManager:isFeatureEnabled(featureName)
    return self:get("FEATURES." .. featureName) == true
end

-- Get security setting
function SecureConfigurationManager:getSecuritySetting(settingName)
    return self:get("SECURITY." .. settingName)
end

-- Create HTTP headers with authentication
function SecureConfigurationManager:createAuthHeaders(additionalHeaders)
    local headers = additionalHeaders or {}

    -- Add API key if configured
    local apiKey = self:get("SECURITY.API_KEY")
    if apiKey and self:getSecuritySetting("REQUIRE_AUTHENTICATION") then
        headers["X-API-Key"] = apiKey
    end

    -- Add content type
    if not headers["Content-Type"] then
        headers["Content-Type"] = "application/json"
    end

    return headers
end

-- Validate request before sending
function SecureConfigurationManager:validateRequest(url, method, data)
    -- Check if validation is enabled
    if not self:getSecuritySetting("VALIDATE_REQUESTS") then
        return true
    end

    -- Validate URL
    if not url or not string.match(url, "^https?://") then
        return false, "Invalid URL format"
    end

    -- Validate method
    local validMethods = {GET = true, POST = true, PUT = true, DELETE = true, PATCH = true}
    if not validMethods[method] then
        return false, "Invalid HTTP method"
    end

    -- Validate data size (prevent large payloads)
    if data then
        local dataStr = HttpService:JSONEncode(data)
        if #dataStr > 1024 * 100 then -- 100KB limit
            return false, "Payload too large"
        end
    end

    return true
end

-- Make secure HTTP request
function SecureConfigurationManager:makeSecureRequest(endpoint, path, method, data)
    local url = self:getEndpoint(endpoint)
    if not url then
        if self:isFeatureEnabled("MOCK_RESPONSES") then
            -- Return mock data for development
            return true, {
                success = true,
                mock = true,
                data = data or {}
            }
        else
            return false, "Endpoint not configured: " .. endpoint
        end
    end

    -- Build full URL
    local fullUrl = url .. path

    -- Validate request
    local valid, error = self:validateRequest(fullUrl, method, data)
    if not valid then
        return false, error
    end

    -- Create headers
    local headers = self:createAuthHeaders()

    -- Make request with error handling
    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = fullUrl,
            Method = method,
            Headers = headers,
            Body = data and HttpService:JSONEncode(data) or nil
        })
    end)

    if not success then
        return false, "Request failed: " .. tostring(response)
    end

    -- Parse response
    if response.StatusCode >= 200 and response.StatusCode < 300 then
        local responseData = response.Body and HttpService:JSONDecode(response.Body) or {}
        return true, responseData
    else
        return false, "Request failed with status " .. response.StatusCode
    end
end

-- Get current environment
function SecureConfigurationManager:getEnvironment()
    return self.environment
end

-- Check if in development mode
function SecureConfigurationManager:isDevelopment()
    return self.environment == "development"
end

-- Check if in production mode
function SecureConfigurationManager:isProduction()
    return self.environment == "production"
end

-- Log configuration issue (only in development/debug mode)
function SecureConfigurationManager:logConfigIssue(issue)
    if self:isFeatureEnabled("DEBUG_MODE") or self:isFeatureEnabled("VERBOSE_LOGGING") then
        warn("[SecureConfig]", issue)
    end
end

-- Singleton instance
local instance = nil

-- Get singleton instance
function SecureConfigurationManager.getInstance()
    if not instance then
        instance = SecureConfigurationManager.new()
    end
    return instance
end

return SecureConfigurationManager


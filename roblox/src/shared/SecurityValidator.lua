--[[
    ToolboxAI Security Validator Module
    Version: 1.0.0
    Version: 2.0.0 - Updated for Roblox 2025
    Description: Provides comprehensive input validation, rate limiting, and anti-exploit measures
                 for the educational content generation system

    Features:
    - Advanced input sanitization
    - Rate limiting and DDoS protection
    - Anti-exploit detection
    - FilteringEnabled compliant
    - Backend API security integration
--]]

local SecurityValidator = {}
SecurityValidator.__index = SecurityValidator

-- Services
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local DataStoreService = game:GetService("DataStoreService")
local MessagingService = game:GetService("MessagingService")

-- Configuration
local CONFIG = {
    -- String validation
    MAX_STRING_LENGTH = 10000,
    MIN_STRING_LENGTH = 1,
    
    -- Token validation
    MIN_TOKEN_LENGTH = 20,
    JWT_PATTERN = "^[A-Za-z0-9%-_]+%.[A-Za-z0-9%-_]+%.[A-Za-z0-9%-_]+$",
    
    -- Rate limiting (2025 standards)
    RATE_LIMIT_WINDOW = 60, -- seconds
    DEFAULT_RATE_LIMIT = 100, -- requests per window
    BURST_RATE_LIMIT = 20, -- requests in 10 seconds
    STRICT_RATE_LIMIT = 10, -- for sensitive operations

    -- Anti-exploit settings
    MAX_REQUESTS_PER_SECOND = 10,
    SUSPICIOUS_PATTERN_THRESHOLD = 5,
    AUTO_BAN_THRESHOLD = 10,

    -- Backend integration
    API_BASE_URL = "http://127.0.0.1:8008",
    SECURITY_ENDPOINT = "/api/v1/security/validate"
    
    -- Content validation
    VALID_CONTENT_TYPES = {
        terrain = true,
        quiz = true,
        script = true,
        ui = true,
        object = true,
        animation = true,
        sound = true,
        particle = true
    },
    
    -- Sanitization patterns
    DANGEROUS_PATTERNS = {
        -- HTML/Script injection
        "<script",
        "</script>",
        "javascript:",
        "onclick",
        "onerror",
        "onload",
        "<iframe",
        
        -- SQL injection patterns
        "'; DROP",
        "-- ",
        "/*",
        "*/",
        "xp_",
        "sp_",
        
        -- Path traversal
        "../",
        "..\\",
        
        -- Command injection
        "&&",
        "||",
        ";",
        "|",
        "`",
        "$(",
        "${",
        
        -- Roblox specific
        "getfenv",
        "setfenv",
        "loadstring",
        "_G[",
        "game:Shutdown",
        "game.Players:GetPlayers()"
    },
    
    -- Whitelisted characters for different input types
    ALLOWED_CHARS = {
        alphanumeric = "^[A-Za-z0-9]+$",
        alphanumeric_space = "^[A-Za-z0-9%s]+$",
        username = "^[A-Za-z0-9_]+$",
        email = "^[A-Za-z0-9._%+%-]+@[A-Za-z0-9.-]+%.[A-Za-z]{2,}$",
        url = "^https?://[A-Za-z0-9.-]+%.[A-Za-z]{2,}",
        safe_text = "^[A-Za-z0-9%s%.,%!%?%-_'\"]+$"
    }
}

-- Constructor
function SecurityValidator.new()
    local self = setmetatable({}, SecurityValidator)

    -- Core components
    self.rateLimiter = self:createRateLimiter()
    self.validationCache = {}
    self.sanitizationLog = {}

    -- Anti-exploit tracking (2025)
    self.suspiciousActivity = {}
    self.bannedUsers = {}
    self.reportedUsers = {}

    -- Performance tracking
    self.validationStats = {
        totalValidations = 0,
        failedValidations = 0,
        blockedRequests = 0,
        exploitAttempts = 0
    }

    -- Setup RemoteEvent monitoring if on server
    if RunService:IsServer() then
        self:SetupAntiExploit()
    end

    return self
end

-- Setup anti-exploit monitoring (Server-side)
function SecurityValidator:SetupAntiExploit()
    -- Monitor RemoteEvent spam
    local function monitorRemoteEvent(remoteEvent)
        local originalFireServer = remoteEvent.OnServerEvent

        remoteEvent.OnServerEvent:Connect(function(player, ...)
            local userId = player.UserId
            local currentTime = tick()

            -- Track request frequency
            if not self.suspiciousActivity[userId] then
                self.suspiciousActivity[userId] = {
                    requestTimes = {},
                    violations = 0,
                    lastViolation = 0
                }
            end

            local userData = self.suspiciousActivity[userId]
            table.insert(userData.requestTimes, currentTime)

            -- Clean old requests (older than 1 second)
            local recentRequests = {}
            for _, time in ipairs(userData.requestTimes) do
                if currentTime - time <= 1 then
                    table.insert(recentRequests, time)
                end
            end
            userData.requestTimes = recentRequests

            -- Check for spam
            if #userData.requestTimes > CONFIG.MAX_REQUESTS_PER_SECOND then
                self:HandleSuspiciousActivity(player, "remote_spam", {
                    requestCount = #userData.requestTimes,
                    remoteEvent = remoteEvent.Name
                })
                return -- Block the request
            end

            -- Original handler can continue
        end)
    end

    -- Monitor all existing RemoteEvents
    for _, obj in pairs(ReplicatedStorage:GetDescendants()) do
        if obj:IsA("RemoteEvent") then
            monitorRemoteEvent(obj)
        end
    end

    -- Monitor new RemoteEvents
    ReplicatedStorage.DescendantAdded:Connect(function(obj)
        if obj:IsA("RemoteEvent") then
            monitorRemoteEvent(obj)
        end
    end)
end

-- Main validation function
function SecurityValidator:validate(data, validationType)
    if not data then
        return false, "No data provided"
    end
    
    validationType = validationType or "general"
    
    -- Type-specific validation
    local validators = {
        string = function() return self:validateString(data) end,
        token = function() return self:validateToken(data) end,
        content = function() return self:validateContentData(data) end,
        user = function() return self:validateUserData(data) end,
        request = function() return self:validateRequest(data) end,
        general = function() return self:validateGeneral(data) end
    }
    
    local validator = validators[validationType]
    if validator then
        return validator()
    else
        return false, "Unknown validation type: " .. tostring(validationType)
    end
end

-- String validation and sanitization
function SecurityValidator:validateString(input, options)
    options = options or {}
    
    if type(input) ~= "string" then
        return false, "Input must be a string"
    end
    
    -- Check length
    local maxLength = options.maxLength or CONFIG.MAX_STRING_LENGTH
    local minLength = options.minLength or CONFIG.MIN_STRING_LENGTH
    
    if #input < minLength then
        return false, "String too short (minimum " .. minLength .. " characters)"
    end
    
    if #input > maxLength then
        return false, "String too long (maximum " .. maxLength .. " characters)"
    end
    
    -- Check for dangerous patterns
    for _, pattern in ipairs(CONFIG.DANGEROUS_PATTERNS) do
        if string.find(input:lower(), pattern:lower(), 1, true) then
            return false, "String contains potentially dangerous pattern"
        end
    end
    
    -- Check against allowed character pattern if specified
    if options.pattern then
        local allowedPattern = CONFIG.ALLOWED_CHARS[options.pattern]
        if allowedPattern and not string.match(input, allowedPattern) then
            return false, "String contains invalid characters for type: " .. options.pattern
        end
    end
    
    return true, input
end

-- Sanitize string input
function SecurityValidator:sanitizeString(input, options)
    if type(input) ~= "string" then
        return ""
    end
    
    options = options or {}
    local sanitized = input
    
    -- Remove HTML tags
    sanitized = sanitized:gsub("<[^>]+>", "")
    
    -- Remove dangerous patterns
    for _, pattern in ipairs(CONFIG.DANGEROUS_PATTERNS) do
        sanitized = sanitized:gsub(pattern, "")
    end
    
    -- Escape special characters
    if options.escape then
        sanitized = sanitized:gsub("&", "&amp;")
        sanitized = sanitized:gsub("<", "&lt;")
        sanitized = sanitized:gsub(">", "&gt;")
        sanitized = sanitized:gsub('"', "&quot;")
        sanitized = sanitized:gsub("'", "&#39;")
    end
    
    -- Trim whitespace
    sanitized = sanitized:match("^%s*(.-)%s*$")
    
    -- Limit length
    local maxLength = options.maxLength or CONFIG.MAX_STRING_LENGTH
    if #sanitized > maxLength then
        sanitized = sanitized:sub(1, maxLength)
    end
    
    -- Log sanitization
    if sanitized ~= input then
        table.insert(self.sanitizationLog, {
            original = input:sub(1, 100),
            sanitized = sanitized:sub(1, 100),
            timestamp = tick()
        })
    end
    
    return sanitized
end

-- Token validation
function SecurityValidator:validateToken(token)
    if type(token) ~= "string" then
        return false, "Token must be a string"
    end
    
    if #token < CONFIG.MIN_TOKEN_LENGTH then
        return false, "Token too short"
    end
    
    -- Basic JWT structure check
    if string.match(token, CONFIG.JWT_PATTERN) then
        local parts = {}
        for part in string.gmatch(token, "[^%.]+") do
            table.insert(parts, part)
        end
        
        if #parts ~= 3 then
            return false, "Invalid JWT structure"
        end
        
        -- Validate each part is base64-like
        for _, part in ipairs(parts) do
            if not string.match(part, "^[A-Za-z0-9%-_]+$") then
                return false, "Invalid JWT encoding"
            end
        end
        
        return true, token
    else
        return false, "Invalid token format"
    end
end

-- Content data validation
function SecurityValidator:validateContentData(data)
    if type(data) ~= "table" then
        return false, "Content data must be a table"
    end
    
    -- Check required fields
    if not data.type then
        return false, "Missing content type"
    end
    
    if not data.content and not data.data then
        return false, "Missing content data"
    end
    
    -- Validate content type
    if not CONFIG.VALID_CONTENT_TYPES[data.type] then
        return false, "Invalid content type: " .. tostring(data.type)
    end
    
    -- Type-specific validation
    local typeValidators = {
        terrain = function() return self:validateTerrainData(data.content or data.data) end,
        quiz = function() return self:validateQuizData(data.content or data.data) end,
        script = function() return self:validateScriptData(data.content or data.data) end,
        ui = function() return self:validateUIData(data.content or data.data) end
    }
    
    local validator = typeValidators[data.type]
    if validator then
        return validator()
    end
    
    return true
end

-- Terrain data validation
function SecurityValidator:validateTerrainData(terrainData)
    if type(terrainData) ~= "table" then
        return false, "Terrain data must be a table"
    end
    
    -- Validate regions if present
    if terrainData.regions then
        if type(terrainData.regions) ~= "table" then
            return false, "Regions must be an array"
        end
        
        for i, region in ipairs(terrainData.regions) do
            if type(region) ~= "table" then
                return false, "Region " .. i .. " must be a table"
            end
            
            -- Validate position
            if region.position and type(region.position) ~= "table" then
                return false, "Region " .. i .. " position must be a table"
            end
            
            -- Validate size
            if region.size and type(region.size) ~= "table" then
                return false, "Region " .. i .. " size must be a table"
            end
        end
    end
    
    return true
end

-- Quiz data validation
function SecurityValidator:validateQuizData(quizData)
    if type(quizData) ~= "table" then
        return false, "Quiz data must be a table"
    end
    
    -- Check required fields
    if not quizData.questions then
        return false, "Quiz must have questions"
    end
    
    if type(quizData.questions) ~= "table" or #quizData.questions == 0 then
        return false, "Questions must be a non-empty array"
    end
    
    -- Validate each question
    for i, question in ipairs(quizData.questions) do
        if type(question) ~= "table" then
            return false, "Question " .. i .. " must be a table"
        end
        
        if not question.question or type(question.question) ~= "string" then
            return false, "Question " .. i .. " must have a question text"
        end
        
        if not question.answers and not question.options then
            return false, "Question " .. i .. " must have answers or options"
        end
        
        -- Sanitize question text
        question.question = self:sanitizeString(question.question)
    end
    
    return true
end

-- Script data validation
function SecurityValidator:validateScriptData(scriptData)
    if type(scriptData) ~= "table" then
        return false, "Script data must be a table"
    end
    
    -- Check source
    if not scriptData.source and not scriptData.content then
        return false, "Script must have source or content"
    end
    
    local source = scriptData.source or scriptData.content
    if type(source) ~= "string" then
        return false, "Script source must be a string"
    end
    
    -- Check for dangerous code patterns
    local dangerousPatterns = {
        "getfenv",
        "setfenv",
        "loadstring",
        "dofile",
        "_G%[",
        "game:Shutdown",
        "while%s+true%s+do%s+end"
    }
    
    for _, pattern in ipairs(dangerousPatterns) do
        if string.match(source, pattern) then
            return false, "Script contains dangerous pattern: " .. pattern
        end
    end
    
    return true
end

-- UI data validation
function SecurityValidator:validateUIData(uiData)
    if type(uiData) ~= "table" then
        return false, "UI data must be a table"
    end
    
    -- Validate UI elements
    if uiData.elements then
        if type(uiData.elements) ~= "table" then
            return false, "UI elements must be an array"
        end
        
        for i, element in ipairs(uiData.elements) do
            if type(element) ~= "table" then
                return false, "UI element " .. i .. " must be a table"
            end
            
            if not element.type then
                return false, "UI element " .. i .. " must have a type"
            end
        end
    end
    
    return true
end

-- User data validation
function SecurityValidator:validateUserData(userData)
    if type(userData) ~= "table" then
        return false, "User data must be a table"
    end
    
    -- Validate username
    if userData.username then
        local valid, err = self:validateString(userData.username, {
            pattern = "username",
            maxLength = 20,
            minLength = 3
        })
        if not valid then
            return false, "Invalid username: " .. err
        end
    end
    
    -- Validate email
    if userData.email then
        if not string.match(userData.email, CONFIG.ALLOWED_CHARS.email) then
            return false, "Invalid email format"
        end
    end
    
    -- Validate user ID
    if userData.userId then
        if type(userData.userId) ~= "number" or userData.userId <= 0 then
            return false, "Invalid user ID"
        end
    end
    
    return true
end

-- Request validation
function SecurityValidator:validateRequest(request)
    if type(request) ~= "table" then
        return false, "Request must be a table"
    end
    
    -- Check required fields
    if not request.endpoint then
        return false, "Request must have an endpoint"
    end
    
    -- Validate method
    local validMethods = {GET = true, POST = true, PUT = true, DELETE = true, PATCH = true}
    if request.method and not validMethods[request.method] then
        return false, "Invalid HTTP method"
    end
    
    -- Validate headers
    if request.headers then
        if type(request.headers) ~= "table" then
            return false, "Headers must be a table"
        end
        
        for key, value in pairs(request.headers) do
            if type(key) ~= "string" or type(value) ~= "string" then
                return false, "Header keys and values must be strings"
            end
        end
    end
    
    return true
end

-- General validation
function SecurityValidator:validateGeneral(data)
    if data == nil then
        return false, "Data is nil"
    end
    
    local dataType = type(data)
    
    if dataType == "string" then
        return self:validateString(data)
    elseif dataType == "table" then
        -- Recursively validate table contents
        for key, value in pairs(data) do
            local valid, err = self:validateGeneral(value)
            if not valid then
                return false, "Invalid value at key '" .. tostring(key) .. "': " .. err
            end
        end
        return true
    elseif dataType == "number" then
        -- Check for NaN and infinity
        if data ~= data then
            return false, "Number is NaN"
        end
        if data == math.huge or data == -math.huge then
            return false, "Number is infinite"
        end
        return true
    elseif dataType == "boolean" then
        return true
    else
        return false, "Unsupported data type: " .. dataType
    end
end

-- Rate limiter creation
function SecurityValidator:createRateLimiter()
    local rateLimiter = {
        requests = {},
        limits = {}
    }
    
    function rateLimiter:check(identifier, limit)
        identifier = tostring(identifier)
        limit = limit or CONFIG.DEFAULT_RATE_LIMIT
        
        local now = tick()
        local userRequests = self.requests[identifier] or {}
        
        -- Clean old requests
        local validRequests = {}
        for _, timestamp in ipairs(userRequests) do
            if now - timestamp < CONFIG.RATE_LIMIT_WINDOW then
                table.insert(validRequests, timestamp)
            end
        end
        
        -- Check if under limit
        if #validRequests >= limit then
            return false, "Rate limit exceeded. Please wait before making more requests."
        end
        
        -- Add current request
        table.insert(validRequests, now)
        self.requests[identifier] = validRequests
        
        return true
    end
    
    function rateLimiter:reset(identifier)
        self.requests[tostring(identifier)] = {}
    end
    
    function rateLimiter:setLimit(identifier, limit)
        self.limits[tostring(identifier)] = limit
    end
    
    function rateLimiter:getLimit(identifier)
        return self.limits[tostring(identifier)] or CONFIG.DEFAULT_RATE_LIMIT
    end
    
    function rateLimiter:getRemainingRequests(identifier)
        identifier = tostring(identifier)
        local limit = self:getLimit(identifier)
        local userRequests = self.requests[identifier] or {}
        
        local now = tick()
        local validCount = 0
        for _, timestamp in ipairs(userRequests) do
            if now - timestamp < CONFIG.RATE_LIMIT_WINDOW then
                validCount = validCount + 1
            end
        end
        
        return math.max(0, limit - validCount)
    end
    
    return rateLimiter
end

-- Check rate limit
function SecurityValidator:checkRateLimit(identifier, limit)
    return self.rateLimiter:check(identifier, limit)
end

-- Reset rate limit for identifier
function SecurityValidator:resetRateLimit(identifier)
    self.rateLimiter:reset(identifier)
end

-- Set custom rate limit
function SecurityValidator:setRateLimit(identifier, limit)
    self.rateLimiter:setLimit(identifier, limit)
end

-- Get remaining requests
function SecurityValidator:getRemainingRequests(identifier)
    return self.rateLimiter:getRemainingRequests(identifier)
end

-- Validate file size
function SecurityValidator:validateFileSize(size, maxSize)
    maxSize = maxSize or 10 * 1024 * 1024 -- 10MB default
    
    if type(size) ~= "number" then
        return false, "Size must be a number"
    end
    
    if size <= 0 then
        return false, "Size must be positive"
    end
    
    if size > maxSize then
        return false, "File size exceeds maximum allowed (" .. maxSize .. " bytes)"
    end
    
    return true
end

-- Validate JSON
function SecurityValidator:validateJSON(jsonString)
    if type(jsonString) ~= "string" then
        return false, "JSON must be a string"
    end
    
    local success, result = pcall(function()
        return HttpService:JSONDecode(jsonString)
    end)
    
    if success then
        return true, result
    else
        return false, "Invalid JSON: " .. tostring(result)
    end
end

-- Get validation statistics
function SecurityValidator:getStatistics()
    return {
        sanitizationCount = #self.sanitizationLog,
        rateLimitChecks = 0, -- Would need to track this
        validationCacheSize = 0 -- Would need to implement caching
    }
end

-- Clear logs
function SecurityValidator:clearLogs()
    self.sanitizationLog = {}
    self.validationCache = {}
end

-- Handle suspicious activity (Anti-exploit)
function SecurityValidator:HandleSuspiciousActivity(player, activityType, details)
    local userId = player.UserId
    local currentTime = tick()

    if not self.suspiciousActivity[userId] then
        self.suspiciousActivity[userId] = {
            violations = 0,
            lastViolation = 0,
            activityTypes = {}
        }
    end

    local userData = self.suspiciousActivity[userId]
    userData.violations = userData.violations + 1
    userData.lastViolation = currentTime
    userData.activityTypes[activityType] = (userData.activityTypes[activityType] or 0) + 1

    -- Update statistics
    self.validationStats.exploitAttempts = self.validationStats.exploitAttempts + 1

    -- Log the incident
    local incident = {
        userId = userId,
        username = player.Name,
        activityType = activityType,
        details = details,
        timestamp = currentTime,
        violationCount = userData.violations
    }

    table.insert(self.sanitizationLog, incident)

    warn(string.format("[SECURITY] Suspicious activity detected: %s from %s (Violation #%d)",
         activityType, player.Name, userData.violations))

    -- Report to backend
    self:ReportToBackend(incident)

    -- Take action based on violation count
    if userData.violations >= CONFIG.AUTO_BAN_THRESHOLD then
        self:BanUser(player, "Excessive security violations")
    elseif userData.violations >= CONFIG.SUSPICIOUS_PATTERN_THRESHOLD then
        self:FlagUser(player, "Multiple security violations")
    end
end

-- Report security incident to backend
function SecurityValidator:ReportToBackend(incident)
    spawn(function()
        pcall(function()
            HttpService:RequestAsync({
                Url = CONFIG.API_BASE_URL .. "/api/v1/security/incident",
                Method = "POST",
                Headers = {
                    ["Content-Type"] = "application/json",
                    ["X-Security-Report"] = "true"
                },
                Body = HttpService:JSONEncode(incident)
            })
        end)
    end)
end

-- Ban user (temporary implementation)
function SecurityValidator:BanUser(player, reason)
    self.bannedUsers[player.UserId] = {
        reason = reason,
        timestamp = tick(),
        username = player.Name
    }

    warn(string.format("[SECURITY] User %s has been banned: %s", player.Name, reason))

    -- Kick the player
    player:Kick("You have been banned for security violations: " .. reason)
end

-- Flag user for review
function SecurityValidator:FlagUser(player, reason)
    self.reportedUsers[player.UserId] = {
        reason = reason,
        timestamp = tick(),
        username = player.Name
    }

    warn(string.format("[SECURITY] User %s has been flagged: %s", player.Name, reason))
end

-- Check if user is banned
function SecurityValidator:IsUserBanned(userId)
    return self.bannedUsers[userId] ~= nil
end

-- Enhanced statistics with anti-exploit data
function SecurityValidator:getStatistics()
    local suspiciousCount = 0
    local bannedCount = 0

    for _ in pairs(self.suspiciousActivity) do
        suspiciousCount = suspiciousCount + 1
    end

    for _ in pairs(self.bannedUsers) do
        bannedCount = bannedCount + 1
    end

    return {
        sanitizationCount = #self.sanitizationLog,
        validationStats = self.validationStats,
        suspiciousUsers = suspiciousCount,
        bannedUsers = bannedCount,
        reportedUsers = #self.reportedUsers,
        validationCacheSize = 0 -- Would need to implement proper caching
    }
end

return SecurityValidator
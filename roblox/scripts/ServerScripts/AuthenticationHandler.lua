--[[
    AuthenticationHandler.lua - JWT authentication and security for ToolboxAI Platform
    
    Handles:
    - JWT token validation with backend
    - Player authentication flow
    - Session management and timeout
    - Permission checking for features
    - Rate limiting and anti-exploit measures
    - Secure API communication
]]

local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local MessagingService = game:GetService("MessagingService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local DataStoreService = game:GetService("DataStoreService")

-- Configuration
local CONFIG = {
    -- API Endpoints
    AUTH_API_URL = "http://127.0.0.1:8008/auth",
    VALIDATE_TOKEN_URL = "http://127.0.0.1:8008/auth/validate",
    REFRESH_TOKEN_URL = "http://127.0.0.1:8008/auth/refresh",
    PERMISSIONS_URL = "http://127.0.0.1:8008/auth/permissions",

    -- OAuth2 Endpoints
    OAUTH2_AUTHORIZE_URL = "http://127.0.0.1:8008/oauth2/authorize",
    OAUTH2_TOKEN_URL = "http://127.0.0.1:8008/oauth2/token",
    OAUTH2_USERINFO_URL = "http://127.0.0.1:8008/oauth2/userinfo",
    OAUTH2_REVOKE_URL = "http://127.0.0.1:8008/oauth2/revoke",
    
    -- Session Configuration
    SESSION_TIMEOUT = 3600, -- 1 hour in seconds
    TOKEN_REFRESH_INTERVAL = 1800, -- 30 minutes
    MAX_FAILED_ATTEMPTS = 5,
    LOCKOUT_DURATION = 300, -- 5 minutes
    
    -- Rate Limiting
    MAX_REQUESTS_PER_MINUTE = 30,
    MAX_AUTH_ATTEMPTS_PER_HOUR = 10,
    
    -- Security
    REQUIRE_AUTHENTICATION = true, -- Set to false for testing
    DEVELOPMENT_MODE = true, -- Bypasses auth in development
    ALLOWED_ORIGINS = {"127.0.0.1", "localhost"},
    
    -- Encryption (simplified for Roblox environment)
    SECRET_KEY = nil, -- Will be loaded from secure storage on init
}

-- Authentication Module
local AuthenticationHandler = {}
AuthenticationHandler.__index = AuthenticationHandler

-- Session storage
local Sessions = {}
local FailedAttempts = {}
local RateLimitTracking = {}
local PermissionsCache = {}

-- Initialize authentication system
function AuthenticationHandler:Initialize()
    print("[Auth] Initializing authentication system...")

    -- Load secret key from secure storage
    self:LoadSecureConfiguration()

    -- Create RemoteEvents for client authentication
    self:SetupRemoteEvents()

    -- Start session cleanup routine
    self:StartSessionCleanup()

    -- Setup rate limit reset
    self:SetupRateLimitReset()

    -- Subscribe to cross-server auth sync
    self:SetupCrossServerSync()

    print("[Auth] Authentication system initialized")
    return true
end

-- Load secure configuration from ServerStorage
function AuthenticationHandler:LoadSecureConfiguration()
    local ServerStorage = game:GetService("ServerStorage")

    -- Try to load from ServerStorage attributes first
    local secretKey = ServerStorage:GetAttribute("ROBLOX_SECRET_KEY")
    if not secretKey then
        -- Try to load from DataStore as fallback
        local success, dataStore = pcall(function()
            return DataStoreService:GetDataStore("SecureConfig")
        end)

        if success then
            local keySuccess, key = pcall(function()
                return dataStore:GetAsync("SECRET_KEY")
            end)

            if keySuccess and key then
                secretKey = key
            end
        end
    end

    -- If still no key, generate a secure one (only in production)
    if not secretKey and not CONFIG.DEVELOPMENT_MODE then
        warn("[Auth] No secret key found! Authentication will be disabled.")
        CONFIG.REQUIRE_AUTHENTICATION = false
    elseif secretKey then
        CONFIG.SECRET_KEY = secretKey
    end
end

-- Setup RemoteEvents for authentication
function AuthenticationHandler:SetupRemoteEvents()
    local remotes = ReplicatedStorage:FindFirstChild("Remotes")
    if not remotes then
        remotes = Instance.new("Folder")
        remotes.Name = "Remotes"
        remotes.Parent = ReplicatedStorage
    end
    
    -- Authentication request event
    local authEvent = Instance.new("RemoteEvent")
    authEvent.Name = "AuthenticationEvent"
    authEvent.Parent = remotes
    
    -- Token refresh function
    local refreshFunction = Instance.new("RemoteFunction")
    refreshFunction.Name = "RefreshTokenFunction"
    refreshFunction.Parent = remotes
    
    -- Connect handlers
    authEvent.OnServerEvent:Connect(function(player, action, data)
        self:HandleAuthenticationEvent(player, action, data)
    end)
    
    refreshFunction.OnServerInvoke = function(player, token)
        return self:RefreshPlayerToken(player, token)
    end
end

-- Validate player on join
function AuthenticationHandler:ValidatePlayer(player)
    -- Development mode bypass
    if CONFIG.DEVELOPMENT_MODE then
        print("[Auth] Development mode - bypassing authentication for", player.Name)
        return {
            success = true,
            permissions = self:GetDefaultPermissions(),
            sessionId = HttpService:GenerateGUID(false),
            message = "Development mode authentication"
        }
    end
    
    -- Check if authentication is required
    if not CONFIG.REQUIRE_AUTHENTICATION then
        return {
            success = true,
            permissions = self:GetDefaultPermissions(),
            sessionId = HttpService:GenerateGUID(false),
            message = "Authentication not required"
        }
    end
    
    -- Check for existing session
    local existingSession = Sessions[player.UserId]
    if existingSession and self:IsSessionValid(existingSession) then
        print("[Auth] Existing valid session found for", player.Name)
        return {
            success = true,
            permissions = existingSession.permissions,
            sessionId = existingSession.sessionId,
            message = "Session restored"
        }
    end
    
    -- Player needs to authenticate
    return {
        success = false,
        message = "Authentication required",
        authUrl = CONFIG.AUTH_API_URL
    }
end

-- Handle authentication events from client
function AuthenticationHandler:HandleAuthenticationEvent(player, action, data)
    -- Rate limiting check
    if not self:CheckRateLimit(player, "auth_event") then
        self:SendAuthResponse(player, false, "Rate limit exceeded")
        return
    end
    
    if action == "login" then
        self:AuthenticateWithToken(player, data.token)
        
    elseif action == "logout" then
        self:LogoutPlayer(player)
        
    elseif action == "validate" then
        self:ValidateSession(player)
        
    elseif action == "request_permissions" then
        self:SendPlayerPermissions(player)

    elseif action == "oauth2_authorize" then
        self:InitiateOAuth2Flow(player, data)

    elseif action == "oauth2_callback" then
        self:HandleOAuth2Callback(player, data)
    end
end

-- Authenticate player with JWT token
function AuthenticationHandler:AuthenticateWithToken(player, token)
    if not token then
        self:SendAuthResponse(player, false, "No token provided")
        return
    end
    
    -- Check failed attempts
    local userId = player.UserId
    if FailedAttempts[userId] and FailedAttempts[userId].locked then
        local lockoutRemaining = CONFIG.LOCKOUT_DURATION - (tick() - FailedAttempts[userId].lockoutTime)
        if lockoutRemaining > 0 then
            self:SendAuthResponse(player, false, "Account locked. Try again in " .. math.floor(lockoutRemaining) .. " seconds")
            return
        else
            FailedAttempts[userId] = nil
        end
    end
    
    -- Validate token with backend
    local success, result = pcall(function()
        return HttpService:RequestAsync({
            Url = CONFIG.VALIDATE_TOKEN_URL,
            Method = "POST",
            Headers = {
                ["Content-Type"] = "application/json",
                ["Authorization"] = "Bearer " .. token
            },
            Body = HttpService:JSONEncode({
                userId = player.UserId,
                username = player.Name,
                placeId = game.PlaceId,
                jobId = game.JobId
            })
        })
    end)
    
    if success and result.StatusCode == 200 then
        local responseData = HttpService:JSONDecode(result.Body)
        
        if responseData.valid then
            -- Create session
            local session = {
                sessionId = HttpService:GenerateGUID(false),
                userId = player.UserId,
                username = player.Name,
                token = token,
                permissions = responseData.permissions or self:GetDefaultPermissions(),
                createdAt = tick(),
                lastActivity = tick(),
                refreshToken = responseData.refreshToken
            }
            
            Sessions[player.UserId] = session
            
            -- Cache permissions
            PermissionsCache[player.UserId] = session.permissions
            
            -- Clear failed attempts
            FailedAttempts[userId] = nil
            
            -- Send success response
            self:SendAuthResponse(player, true, "Authentication successful", session)
            
            -- Log authentication
            self:LogAuthEvent(player, "login_success")
            
            -- Broadcast to other servers
            self:BroadcastAuthUpdate(player.UserId, "login")
            
            print("[Auth] Player authenticated successfully:", player.Name)
        else
            self:HandleFailedAuth(player, "Invalid token")
        end
    else
        self:HandleFailedAuth(player, "Backend validation failed")
    end
end

-- Handle failed authentication
function AuthenticationHandler:HandleFailedAuth(player, reason)
    local userId = player.UserId
    
    if not FailedAttempts[userId] then
        FailedAttempts[userId] = {
            count = 0,
            firstAttempt = tick(),
            locked = false
        }
    end
    
    FailedAttempts[userId].count = FailedAttempts[userId].count + 1
    FailedAttempts[userId].lastAttempt = tick()
    
    if FailedAttempts[userId].count >= CONFIG.MAX_FAILED_ATTEMPTS then
        FailedAttempts[userId].locked = true
        FailedAttempts[userId].lockoutTime = tick()
        
        self:SendAuthResponse(player, false, "Too many failed attempts. Account locked for " .. CONFIG.LOCKOUT_DURATION .. " seconds")
        self:LogAuthEvent(player, "account_locked")
    else
        local remaining = CONFIG.MAX_FAILED_ATTEMPTS - FailedAttempts[userId].count
        self:SendAuthResponse(player, false, reason .. ". " .. remaining .. " attempts remaining")
    end
    
    self:LogAuthEvent(player, "login_failed", {reason = reason})
end

-- Refresh player token
function AuthenticationHandler:RefreshPlayerToken(player, currentToken)
    local session = Sessions[player.UserId]
    
    if not session then
        return {success = false, message = "No active session"}
    end
    
    if not self:CheckRateLimit(player, "token_refresh") then
        return {success = false, message = "Rate limit exceeded"}
    end
    
    -- Request new token from backend
    local success, result = pcall(function()
        return HttpService:RequestAsync({
            Url = CONFIG.REFRESH_TOKEN_URL,
            Method = "POST",
            Headers = {
                ["Content-Type"] = "application/json",
                ["Authorization"] = "Bearer " .. currentToken
            },
            Body = HttpService:JSONEncode({
                userId = player.UserId,
                refreshToken = session.refreshToken
            })
        })
    end)
    
    if success and result.StatusCode == 200 then
        local responseData = HttpService:JSONDecode(result.Body)
        
        -- Update session with new token
        session.token = responseData.token
        session.refreshToken = responseData.refreshToken
        session.lastActivity = tick()
        
        self:LogAuthEvent(player, "token_refreshed")
        
        return {
            success = true,
            token = responseData.token,
            expiresIn = CONFIG.TOKEN_REFRESH_INTERVAL
        }
    else
        return {success = false, message = "Token refresh failed"}
    end
end

-- Logout player
function AuthenticationHandler:LogoutPlayer(player)
    local session = Sessions[player.UserId]

    if session then
        -- Revoke OAuth2 token if applicable
        if session.authMethod == "oauth2" then
            self:RevokeOAuth2Token(player)
        end

        -- Notify backend
        pcall(function()
            HttpService:RequestAsync({
                Url = CONFIG.AUTH_API_URL .. "/logout",
                Method = "POST",
                Headers = {
                    ["Content-Type"] = "application/json",
                    ["Authorization"] = "Bearer " .. session.token
                },
                Body = HttpService:JSONEncode({
                    userId = player.UserId,
                    sessionId = session.sessionId,
                    authMethod = session.authMethod or "jwt"
                })
            })
        end)
        
        -- Clear session
        Sessions[player.UserId] = nil
        PermissionsCache[player.UserId] = nil
        
        self:SendAuthResponse(player, true, "Logged out successfully")
        self:LogAuthEvent(player, "logout")
        self:BroadcastAuthUpdate(player.UserId, "logout")
    end
end

-- Validate active session
function AuthenticationHandler:ValidateSession(player)
    local session = Sessions[player.UserId]
    
    if not session then
        self:SendAuthResponse(player, false, "No active session")
        return
    end
    
    if not self:IsSessionValid(session) then
        Sessions[player.UserId] = nil
        self:SendAuthResponse(player, false, "Session expired")
        return
    end
    
    -- Update last activity
    session.lastActivity = tick()
    
    self:SendAuthResponse(player, true, "Session valid", {
        sessionId = session.sessionId,
        permissions = session.permissions,
        expiresIn = CONFIG.SESSION_TIMEOUT - (tick() - session.createdAt)
    })
end

-- Check if session is still valid
function AuthenticationHandler:IsSessionValid(session)
    if not session then
        return false
    end
    
    local age = tick() - session.createdAt
    local idle = tick() - session.lastActivity
    
    return age < CONFIG.SESSION_TIMEOUT and idle < CONFIG.SESSION_TIMEOUT
end

-- Get player permissions
function AuthenticationHandler:GetPlayerPermissions(player)
    local userId = player.UserId
    
    -- Check cache first
    if PermissionsCache[userId] then
        return PermissionsCache[userId]
    end
    
    -- Check session
    local session = Sessions[userId]
    if session and session.permissions then
        return session.permissions
    end
    
    -- Return default permissions
    return self:GetDefaultPermissions()
end

-- Check if player has specific permission
function AuthenticationHandler:HasPermission(player, permission)
    local permissions = self:GetPlayerPermissions(player)
    return permissions[permission] == true or permissions.admin == true
end

-- Send permissions to player
function AuthenticationHandler:SendPlayerPermissions(player)
    local permissions = self:GetPlayerPermissions(player)
    
    local remotes = ReplicatedStorage:WaitForChild("Remotes")
    local authEvent = remotes:WaitForChild("AuthenticationEvent")
    
    authEvent:FireClient(player, "permissions_update", {
        permissions = permissions,
        timestamp = tick()
    })
end

-- Get default permissions
function AuthenticationHandler:GetDefaultPermissions()
    return {
        play = true,
        chat = true,
        quiz = true,
        explore = true,
        save_progress = true,
        view_leaderboard = true,
        use_tools = false,
        create_content = false,
        moderate = false,
        admin = false
    }
end

-- Rate limiting
function AuthenticationHandler:CheckRateLimit(player, actionType)
    local userId = player.UserId
    local currentTime = tick()
    
    if not RateLimitTracking[userId] then
        RateLimitTracking[userId] = {}
    end
    
    if not RateLimitTracking[userId][actionType] then
        RateLimitTracking[userId][actionType] = {
            requests = {},
            hourlyAuth = {}
        }
    end
    
    local tracking = RateLimitTracking[userId][actionType]
    
    -- Clean old requests (older than 1 minute)
    local validRequests = {}
    for _, timestamp in ipairs(tracking.requests) do
        if currentTime - timestamp < 60 then
            table.insert(validRequests, timestamp)
        end
    end
    tracking.requests = validRequests
    
    -- Check rate limit
    if #tracking.requests >= CONFIG.MAX_REQUESTS_PER_MINUTE then
        self:LogAuthEvent(player, "rate_limit_exceeded", {actionType = actionType})
        return false
    end
    
    -- Special check for authentication attempts
    if actionType == "auth_event" then
        local validAuthAttempts = {}
        for _, timestamp in ipairs(tracking.hourlyAuth) do
            if currentTime - timestamp < 3600 then
                table.insert(validAuthAttempts, timestamp)
            end
        end
        tracking.hourlyAuth = validAuthAttempts
        
        if #tracking.hourlyAuth >= CONFIG.MAX_AUTH_ATTEMPTS_PER_HOUR then
            return false
        end
        
        table.insert(tracking.hourlyAuth, currentTime)
    end
    
    -- Add current request
    table.insert(tracking.requests, currentTime)
    
    return true
end

-- Setup rate limit reset routine
function AuthenticationHandler:SetupRateLimitReset()
    spawn(function()
        while true do
            wait(300) -- Reset every 5 minutes
            
            -- Clear old rate limit data
            for userId, data in pairs(RateLimitTracking) do
                for actionType, tracking in pairs(data) do
                    tracking.requests = {}
                end
            end
        end
    end)
end

-- Session cleanup routine
function AuthenticationHandler:StartSessionCleanup()
    spawn(function()
        while true do
            wait(60) -- Check every minute
            
            local currentTime = tick()
            local expiredSessions = {}
            
            for userId, session in pairs(Sessions) do
                if not self:IsSessionValid(session) then
                    table.insert(expiredSessions, userId)
                end
            end
            
            for _, userId in ipairs(expiredSessions) do
                Sessions[userId] = nil
                PermissionsCache[userId] = nil
                
                local player = Players:GetPlayerByUserId(userId)
                if player then
                    self:SendAuthResponse(player, false, "Session expired")
                end
            end
            
            if #expiredSessions > 0 then
                print("[Auth] Cleaned up", #expiredSessions, "expired sessions")
            end
        end
    end)
end

-- Send authentication response to client
function AuthenticationHandler:SendAuthResponse(player, success, message, data)
    local remotes = ReplicatedStorage:WaitForChild("Remotes")
    local authEvent = remotes:WaitForChild("AuthenticationEvent")
    
    authEvent:FireClient(player, "auth_response", {
        success = success,
        message = message,
        data = data,
        timestamp = tick()
    })
end

-- Cross-server synchronization
function AuthenticationHandler:SetupCrossServerSync()
    pcall(function()
        MessagingService:SubscribeAsync("AuthSync", function(message)
            local data = message.Data
            
            if data.action == "login" then
                -- Another server authenticated this user
                if Sessions[data.userId] then
                    -- Update our session
                    Sessions[data.userId].lastActivity = tick()
                end
                
            elseif data.action == "logout" then
                -- User logged out on another server
                Sessions[data.userId] = nil
                PermissionsCache[data.userId] = nil
                
                local player = Players:GetPlayerByUserId(data.userId)
                if player then
                    self:SendAuthResponse(player, false, "Logged out from another server")
                end
            end
        end)
    end)
end

-- Broadcast authentication update to other servers
function AuthenticationHandler:BroadcastAuthUpdate(userId, action)
    pcall(function()
        MessagingService:PublishAsync("AuthSync", {
            userId = userId,
            action = action,
            serverJobId = game.JobId,
            timestamp = tick()
        })
    end)
end

-- Log authentication events
function AuthenticationHandler:LogAuthEvent(player, eventType, additionalData)
    local logEntry = {
        userId = player.UserId,
        username = player.Name,
        eventType = eventType,
        timestamp = os.time(),
        serverJobId = game.JobId,
        additionalData = additionalData or {}
    }
    
    -- Send to backend for logging
    spawn(function()
        pcall(function()
            HttpService:RequestAsync({
                Url = CONFIG.AUTH_API_URL .. "/log",
                Method = "POST",
                Headers = {
                    ["Content-Type"] = "application/json"
                },
                Body = HttpService:JSONEncode(logEntry)
            })
        end)
    end)
    
    -- Also store locally if needed
    if eventType == "login_failed" or eventType == "account_locked" then
        warn("[Auth]", eventType, "for", player.Name, additionalData and additionalData.reason or "")
    end
end

-- Verify API request signature (for server-to-server communication)
function AuthenticationHandler:VerifyRequestSignature(headers, body)
    -- Simple signature verification
    -- In production, use proper HMAC or similar
    local signature = headers["X-Signature"]
    if not signature then
        return false
    end
    
    local expectedSignature = HttpService:GenerateGUID(false) -- Simplified
    return signature == expectedSignature
end

-- Get session statistics
function AuthenticationHandler:GetSessionStats()
    local stats = {
        activeSessions = 0,
        lockedAccounts = 0,
        totalPermissionsCached = 0
    }
    
    for _ in pairs(Sessions) do
        stats.activeSessions = stats.activeSessions + 1
    end
    
    for _, attempts in pairs(FailedAttempts) do
        if attempts.locked then
            stats.lockedAccounts = stats.lockedAccounts + 1
        end
    end
    
    for _ in pairs(PermissionsCache) do
        stats.totalPermissionsCached = stats.totalPermissionsCached + 1
    end
    
    return stats
end

-- OAuth2 Authorization Flow
function AuthenticationHandler:InitiateOAuth2Flow(player, data)
    if not self:CheckRateLimit(player, "oauth2_init") then
        self:SendAuthResponse(player, false, "Rate limit exceeded")
        return
    end

    local clientId = data.clientId or "ToolboxAI_Client"
    local redirectUri = data.redirectUri or "http://127.0.0.1:8008/oauth2/callback"
    local scope = data.scope or "read write"
    local state = HttpService:GenerateGUID(false)

    -- Store state for verification
    local userId = player.UserId
    if not Sessions[userId] then
        Sessions[userId] = {}
    end
    Sessions[userId].oauth2_state = state
    Sessions[userId].oauth2_initiated = tick()

    -- Generate authorization URL
    local authUrl = CONFIG.OAUTH2_AUTHORIZE_URL .. "?" ..
        "response_type=code" ..
        "&client_id=" .. HttpService:UrlEncode(clientId) ..
        "&redirect_uri=" .. HttpService:UrlEncode(redirectUri) ..
        "&scope=" .. HttpService:UrlEncode(scope) ..
        "&state=" .. HttpService:UrlEncode(state) ..
        "&user_id=" .. tostring(player.UserId)

    self:SendAuthResponse(player, true, "OAuth2 authorization initiated", {
        authorizationUrl = authUrl,
        state = state,
        expiresIn = 300 -- 5 minutes
    })

    self:LogAuthEvent(player, "oauth2_initiated", {state = state})
end

-- Handle OAuth2 Callback
function AuthenticationHandler:HandleOAuth2Callback(player, data)
    local userId = player.UserId
    local session = Sessions[userId]

    if not session or not session.oauth2_state then
        self:SendAuthResponse(player, false, "No active OAuth2 flow")
        return
    end

    -- Verify state parameter
    if data.state ~= session.oauth2_state then
        self:SendAuthResponse(player, false, "Invalid OAuth2 state")
        self:LogAuthEvent(player, "oauth2_state_mismatch")
        return
    end

    -- Check if flow hasn't expired
    local flowAge = tick() - (session.oauth2_initiated or 0)
    if flowAge > 300 then -- 5 minutes
        self:SendAuthResponse(player, false, "OAuth2 flow expired")
        return
    end

    -- Exchange authorization code for access token
    if data.code then
        self:ExchangeOAuth2Code(player, data.code)
    elseif data.error then
        self:SendAuthResponse(player, false, "OAuth2 authorization failed: " .. data.error)
        self:LogAuthEvent(player, "oauth2_error", {error = data.error})
    else
        self:SendAuthResponse(player, false, "Invalid OAuth2 callback data")
    end
end

-- Exchange OAuth2 authorization code for tokens
function AuthenticationHandler:ExchangeOAuth2Code(player, authCode)
    local tokenRequestData = {
        grant_type = "authorization_code",
        code = authCode,
        client_id = "ToolboxAI_Client",
        client_secret = CONFIG.SECRET_KEY, -- In production, use proper OAuth2 client secret
        redirect_uri = "http://127.0.0.1:8008/oauth2/callback"
    }

    local success, result = pcall(function()
        return HttpService:RequestAsync({
            Url = CONFIG.OAUTH2_TOKEN_URL,
            Method = "POST",
            Headers = {
                ["Content-Type"] = "application/json"
            },
            Body = HttpService:JSONEncode(tokenRequestData)
        })
    end)

    if success and result.StatusCode == 200 then
        local tokenData = HttpService:JSONDecode(result.Body)

        if tokenData.access_token then
            -- Get user info with access token
            self:GetOAuth2UserInfo(player, tokenData.access_token, tokenData.refresh_token)
        else
            self:SendAuthResponse(player, false, "Invalid token response")
        end
    else
        self:HandleFailedAuth(player, "OAuth2 token exchange failed")
    end
end

-- Get user information using OAuth2 access token
function AuthenticationHandler:GetOAuth2UserInfo(player, accessToken, refreshToken)
    local success, result = pcall(function()
        return HttpService:RequestAsync({
            Url = CONFIG.OAUTH2_USERINFO_URL,
            Method = "GET",
            Headers = {
                ["Authorization"] = "Bearer " .. accessToken
            }
        })
    end)

    if success and result.StatusCode == 200 then
        local userInfo = HttpService:JSONDecode(result.Body)

        -- Create authenticated session
        local session = {
            sessionId = HttpService:GenerateGUID(false),
            userId = player.UserId,
            username = player.Name,
            token = accessToken,
            refreshToken = refreshToken,
            oauth2UserInfo = userInfo,
            permissions = self:MapOAuth2Permissions(userInfo),
            createdAt = tick(),
            lastActivity = tick(),
            authMethod = "oauth2"
        }

        Sessions[player.UserId] = session
        PermissionsCache[player.UserId] = session.permissions

        -- Clear OAuth2 temporary data
        session.oauth2_state = nil
        session.oauth2_initiated = nil

        self:SendAuthResponse(player, true, "OAuth2 authentication successful", {
            sessionId = session.sessionId,
            permissions = session.permissions,
            userInfo = userInfo
        })

        self:LogAuthEvent(player, "oauth2_success")
        self:BroadcastAuthUpdate(player.UserId, "oauth2_login")

        print("[Auth] Player authenticated via OAuth2:", player.Name)
    else
        self:HandleFailedAuth(player, "Failed to get OAuth2 user info")
    end
end

-- Map OAuth2 user info to internal permissions
function AuthenticationHandler:MapOAuth2Permissions(userInfo)
    local permissions = self:GetDefaultPermissions()

    -- Map OAuth2 scopes/roles to permissions
    if userInfo.roles then
        for _, role in ipairs(userInfo.roles) do
            if role == "admin" then
                permissions.admin = true
                permissions.moderate = true
                permissions.create_content = true
                permissions.use_tools = true
            elseif role == "teacher" then
                permissions.moderate = true
                permissions.create_content = true
                permissions.use_tools = true
            elseif role == "content_creator" then
                permissions.create_content = true
                permissions.use_tools = true
            end
        end
    end

    -- Check OAuth2 scopes
    if userInfo.scope then
        local scopes = {}
        for scope in string.gmatch(userInfo.scope, "%S+") do
            scopes[scope] = true
        end

        if scopes["admin"] then
            permissions.admin = true
        end
        if scopes["moderate"] then
            permissions.moderate = true
        end
        if scopes["create"] then
            permissions.create_content = true
        end
    end

    return permissions
end

-- Revoke OAuth2 token
function AuthenticationHandler:RevokeOAuth2Token(player)
    local session = Sessions[player.UserId]
    if not session or session.authMethod ~= "oauth2" then
        return false
    end

    local success, result = pcall(function()
        return HttpService:RequestAsync({
            Url = CONFIG.OAUTH2_REVOKE_URL,
            Method = "POST",
            Headers = {
                ["Content-Type"] = "application/json",
                ["Authorization"] = "Bearer " .. session.token
            },
            Body = HttpService:JSONEncode({
                token = session.token,
                token_type_hint = "access_token"
            })
        })
    end)

    if success and result.StatusCode == 200 then
        self:LogAuthEvent(player, "oauth2_revoked")
        return true
    else
        warn("[Auth] Failed to revoke OAuth2 token for", player.Name)
        return false
    end
end

-- Handle player removal
function AuthenticationHandler:OnPlayerRemoving(player)
    local userId = player.UserId
    
    -- Clear session
    if Sessions[userId] then
        self:LogAuthEvent(player, "session_ended")
        Sessions[userId] = nil
    end
    
    -- Clear caches
    PermissionsCache[userId] = nil
    RateLimitTracking[userId] = nil
    
    -- Don't clear failed attempts - they should persist
end

-- Initialize the authentication system
AuthenticationHandler:Initialize()

-- Module export
return AuthenticationHandler
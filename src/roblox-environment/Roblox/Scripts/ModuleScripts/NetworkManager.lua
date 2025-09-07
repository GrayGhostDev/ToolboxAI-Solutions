--[[
    NetworkManager.lua
    Handles all network communication between client and server
    
    Manages RemoteEvents, RemoteFunctions, data synchronization,
    and reliable message delivery for the educational platform
]]

local NetworkManager = {}
NetworkManager.__index = NetworkManager

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local HttpService = game:GetService("HttpService")
local RunService = game:GetService("RunService")

-- Network configuration
local NETWORK_CONFIG = {
    MAX_RETRIES = 3,
    RETRY_DELAY = 1,
    TIMEOUT = 10,
    RATE_LIMIT = 60, -- requests per minute
    BATCH_SIZE = 50
}

-- Remote storage
local remoteEvents = {}
local remoteFunctions = {}
local pendingRequests = {}
local messageQueue = {}

-- Initialize network manager
-- @return NetworkManager - New network manager instance
function NetworkManager.new()
    local self = setmetatable({}, NetworkManager)
    
    -- Initialize network components
    self.isServer = RunService:IsServer()
    self.isClient = RunService:IsClient()
    self.rateLimiter = {}
    self.callbacks = {}
    self.requestId = 0
    self.messageHandlers = {}
    self.functionHandlers = {}
    self.retryTimers = {}
    self.connectionStatus = "Connected"
    self.lastHeartbeat = tick()
    self.metrics = {
        sentCount = 0,
        receivedCount = 0,
        failedCount = 0,
        averageLatency = 0,
        packetLoss = 0
    }
    
    -- Initialize on creation
    self:Initialize()
    
    return self
end

-- Initialize remote events and functions
function NetworkManager:Initialize()
    -- Set up network infrastructure
    local remoteFolder = ReplicatedStorage:FindFirstChild("Remotes") or Instance.new("Folder")
    remoteFolder.Name = "Remotes"
    remoteFolder.Parent = ReplicatedStorage
    
    -- Create event and function folders
    local eventFolder = remoteFolder:FindFirstChild("Events") or Instance.new("Folder")
    eventFolder.Name = "Events"
    eventFolder.Parent = remoteFolder
    
    local funcFolder = remoteFolder:FindFirstChild("Functions") or Instance.new("Folder")
    funcFolder.Name = "Functions"
    funcFolder.Parent = remoteFolder
    
    -- Create specific remotes for gameplay
    self:CreateRemote("PlayerAction", "RemoteEvent")
    self:CreateRemote("UpdateProgress", "RemoteEvent")
    self:CreateRemote("QuizAnswer", "RemoteEvent")
    self:CreateRemote("CollectItem", "RemoteEvent")
    self:CreateRemote("UseAbility", "RemoteEvent")
    self:CreateRemote("ChatMessage", "RemoteEvent")
    self:CreateRemote("ErrorReport", "RemoteEvent")
    self:CreateRemote("Heartbeat", "RemoteEvent")
    
    -- Create remote functions
    self:CreateRemote("FetchContent", "RemoteFunction")
    self:CreateRemote("SubmitAnswer", "RemoteFunction")
    self:CreateRemote("GetPlayerData", "RemoteFunction")
    self:CreateRemote("GetLeaderboard", "RemoteFunction")
    self:CreateRemote("ValidateInput", "RemoteFunction")
    self:CreateRemote("GetServerTime", "RemoteFunction")
    
    -- Start heartbeat monitoring
    self:StartHeartbeat()
    
    -- Start queue processor
    self:StartQueueProcessor()
end

-- Create remote instance
-- @param name: string - Name of the remote
-- @param remoteType: string - "RemoteEvent" or "RemoteFunction"
function NetworkManager:CreateRemote(name, remoteType)
    local remoteFolder = ReplicatedStorage:WaitForChild("Remotes")
    local targetFolder
    
    if remoteType == "RemoteEvent" then
        targetFolder = remoteFolder:WaitForChild("Events")
        local existing = targetFolder:FindFirstChild(name)
        if existing then
            remoteEvents[name] = existing
            return existing
        end
        
        local remote = Instance.new("RemoteEvent")
        remote.Name = name
        remote.Parent = targetFolder
        remoteEvents[name] = remote
        
        -- Set up default security handler if server
        if self.isServer then
            remote.OnServerEvent:Connect(function(player, ...)
                if self:ValidateRequest(player, {...}) then
                    self:HandleRemoteEvent(player, name, ...)
                else
                    self:LogSuspiciousActivity(player, name)
                end
            end)
        end
        
        return remote
    else
        targetFolder = remoteFolder:WaitForChild("Functions")
        local existing = targetFolder:FindFirstChild(name)
        if existing then
            remoteFunctions[name] = existing
            return existing
        end
        
        local remote = Instance.new("RemoteFunction")
        remote.Name = name
        remote.Parent = targetFolder
        remoteFunctions[name] = remote
        
        -- Set up default security handler if server
        if self.isServer then
            remote.OnServerInvoke = function(player, ...)
                if self:ValidateRequest(player, {...}) then
                    return self:HandleRemoteFunction(player, name, ...)
                else
                    self:LogSuspiciousActivity(player, name)
                    return nil, "Unauthorized"
                end
            end
        end
        
        return remote
    end
end

-- Send data to server (client-side)
-- @param eventName: string - Name of the remote event
-- @param data: any - Data to send
function NetworkManager:SendToServer(eventName, data)
    if self.isServer then
        warn("Cannot send to server from server")
        return false
    end
    
    local remote = remoteEvents[eventName]
    if not remote then
        warn("Remote event not found:", eventName)
        return false
    end
    
    -- Validate data size
    local dataSize = #HttpService:JSONEncode(data or {})
    if dataSize > 50000 then  -- 50KB limit
        data = self:CompressData(data)
    end
    
    -- Check rate limits
    if not self:CheckRateLimit(eventName) then
        self:QueueMessage(eventName, data, "server")
        return false
    end
    
    -- Send with error handling
    local success, errorMsg = pcall(function()
        remote:FireServer(data)
        self.metrics.sentCount = self.metrics.sentCount + 1
    end)
    
    if not success then
        self.metrics.failedCount = self.metrics.failedCount + 1
        warn("Failed to send to server:", errorMsg)
        self:QueueMessage(eventName, data, "server")
        return false
    end
    
    return true
end

-- Send data to client (server-side)
-- @param player: Player - Target player
-- @param eventName: string - Name of the remote event
-- @param data: any - Data to send
function NetworkManager:SendToClient(player, eventName, data)
    if not self.isServer then
        warn("Cannot send to client from client")
        return false
    end
    
    -- Validate player
    if not player or not player:IsA("Player") or not player.Parent then
        warn("Invalid player for SendToClient")
        return false
    end
    
    local remote = remoteEvents[eventName]
    if not remote then
        warn("Remote event not found:", eventName)
        return false
    end
    
    -- Compress large data
    local dataSize = #HttpService:JSONEncode(data or {})
    if dataSize > 50000 then
        data = self:CompressData(data)
    end
    
    -- Send with error handling
    local success, errorMsg = pcall(function()
        remote:FireClient(player, data)
        self.metrics.sentCount = self.metrics.sentCount + 1
    end)
    
    if not success then
        self.metrics.failedCount = self.metrics.failedCount + 1
        warn("Failed to send to client:", errorMsg)
        return false
    end
    
    return true
end

-- Broadcast to all clients (server-side)
-- @param eventName: string - Name of the remote event
-- @param data: any - Data to broadcast
-- @param except: Player - Optional player to exclude
function NetworkManager:BroadcastToClients(eventName, data, except)
    if not self.isServer then
        warn("Cannot broadcast from client")
        return false
    end
    
    local remote = remoteEvents[eventName]
    if not remote then
        warn("Remote event not found:", eventName)
        return false
    end
    
    -- Compress if large
    local dataSize = #HttpService:JSONEncode(data or {})
    if dataSize > 50000 then
        data = self:CompressData(data)
    end
    
    local successCount = 0
    local failCount = 0
    
    if except then
        -- Send to all except one player
        for _, player in ipairs(Players:GetPlayers()) do
            if player ~= except and player.Parent then
                local success = pcall(function()
                    remote:FireClient(player, data)
                end)
                
                if success then
                    successCount = successCount + 1
                else
                    failCount = failCount + 1
                end
            end
        end
    else
        -- Send to all clients
        local success = pcall(function()
            remote:FireAllClients(data)
            successCount = #Players:GetPlayers()
        end)
        
        if not success then
            failCount = #Players:GetPlayers()
        end
    end
    
    self.metrics.sentCount = self.metrics.sentCount + successCount
    self.metrics.failedCount = self.metrics.failedCount + failCount
    
    return successCount > 0
end

-- Call remote function with response
-- @param functionName: string - Name of the remote function
-- @param data: any - Data to send
-- @param player: Player - Target player (server only)
-- @return any - Response from remote
function NetworkManager:InvokeRemote(functionName, data, player)
    local remote = remoteFunctions[functionName]
    if not remote then
        warn("Remote function not found:", functionName)
        return nil, "Function not found"
    end
    
    -- Check rate limits
    if not self:CheckRateLimit(functionName) then
        return nil, "Rate limited"
    end
    
    local retries = 0
    local maxRetries = NETWORK_CONFIG.MAX_RETRIES
    
    while retries <= maxRetries do
        local success, result
        
        if self.isServer and player then
            -- Server invoking client (rare)
            success, result = pcall(function()
                return remote:InvokeClient(player, data)
            end)
        elseif self.isClient then
            -- Client invoking server
            -- Implement timeout
            local completed = false
            local response = nil
            
            spawn(function()
                local s, r = pcall(function()
                    return remote:InvokeServer(data)
                end)
                completed = true
                if s then
                    response = r
                end
            end)
            
            -- Wait for response or timeout
            local startTime = tick()
            while not completed and tick() - startTime < NETWORK_CONFIG.TIMEOUT do
                wait(0.1)
            end
            
            if completed then
                success = true
                result = response
            else
                success = false
                result = "Timeout"
            end
        else
            return nil, "Invalid context"
        end
        
        if success then
            self.metrics.sentCount = self.metrics.sentCount + 1
            return result
        else
            retries = retries + 1
            if retries <= maxRetries then
                wait(NETWORK_CONFIG.RETRY_DELAY * retries)
            end
        end
    end
    
    self.metrics.failedCount = self.metrics.failedCount + 1
    return nil, "Max retries exceeded"
end

-- Register handler for remote event
-- @param eventName: string - Name of the event
-- @param handler: function - Handler function
function NetworkManager:RegisterHandler(eventName, handler)
    if type(handler) ~= "function" then
        warn("Handler must be a function")
        return false
    end
    
    -- Store handler
    if not self.messageHandlers[eventName] then
        self.messageHandlers[eventName] = {}
    end
    table.insert(self.messageHandlers[eventName], handler)
    
    -- Connect if first handler
    if #self.messageHandlers[eventName] == 1 then
        local remote = remoteEvents[eventName]
        if not remote then
            warn("Remote event not found:", eventName)
            return false
        end
        
        if self.isServer then
            -- Server already has security handler from CreateRemote
            -- Just mark as having custom handlers
            self.messageHandlers[eventName].hasCustom = true
        else
            -- Client handler
            remote.OnClientEvent:Connect(function(...)
                self.metrics.receivedCount = self.metrics.receivedCount + 1
                self:HandleRemoteEvent(nil, eventName, ...)
            end)
        end
    end
    
    return true
end

-- Handle incoming remote event
function NetworkManager:HandleRemoteEvent(player, eventName, ...)
    local handlers = self.messageHandlers[eventName]
    if not handlers then return end
    
    for _, handler in ipairs(handlers) do
        local success, errorMsg = pcall(function()
            if player then
                handler(player, ...)
            else
                handler(...)
            end
        end)
        
        if not success then
            warn("Handler error for", eventName, ":", errorMsg)
        end
    end
end

-- Register handler for remote function
-- @param functionName: string - Name of the function
-- @param handler: function - Handler function
function NetworkManager:RegisterFunctionHandler(functionName, handler)
    if type(handler) ~= "function" then
        warn("Handler must be a function")
        return false
    end
    
    local remote = remoteFunctions[functionName]
    if not remote then
        warn("Remote function not found:", functionName)
        return false
    end
    
    -- Store handler
    self.functionHandlers[functionName] = handler
    
    if self.isServer then
        -- Override default security handler with custom
        remote.OnServerInvoke = function(player, ...)
            if self:ValidateRequest(player, {...}) then
                self.metrics.receivedCount = self.metrics.receivedCount + 1
                return self:HandleRemoteFunction(player, functionName, ...)
            else
                self:LogSuspiciousActivity(player, functionName)
                return nil, "Unauthorized"
            end
        end
    else
        remote.OnClientInvoke = function(...)
            self.metrics.receivedCount = self.metrics.receivedCount + 1
            
            local success, result = pcall(handler, ...)
            if success then
                return result
            else
                warn("Function handler error:", result)
                return nil, "Handler error"
            end
        end
    end
    
    return true
end

-- Handle incoming remote function
function NetworkManager:HandleRemoteFunction(player, functionName, ...)
    local handler = self.functionHandlers[functionName]
    if not handler then
        return nil, "No handler registered"
    end
    
    local success, result = pcall(function()
        if player then
            return handler(player, ...)
        else
            return handler(...)
        end
    end)
    
    if success then
        return result
    else
        warn("Function handler error for", functionName, ":", result)
        return nil, "Handler error"
    end
end

-- Implement rate limiting
-- @param identifier: string - Rate limit identifier
-- @return boolean - Whether action is allowed
function NetworkManager:CheckRateLimit(identifier)
    local now = tick()
    
    -- Initialize if needed
    if not self.rateLimiter[identifier] then
        self.rateLimiter[identifier] = {
            timestamps = {},
            violations = 0,
            blockedUntil = 0
        }
    end
    
    local limiter = self.rateLimiter[identifier]
    
    -- Check if currently blocked
    if now < limiter.blockedUntil then
        return false
    end
    
    -- Clean old entries (older than 60 seconds)
    local validTimestamps = {}
    for _, timestamp in ipairs(limiter.timestamps) do
        if now - timestamp < 60 then
            table.insert(validTimestamps, timestamp)
        end
    end
    limiter.timestamps = validTimestamps
    
    -- Check rate limit
    if #limiter.timestamps >= NETWORK_CONFIG.RATE_LIMIT then
        limiter.violations = limiter.violations + 1
        
        -- Progressive blocking: 1s, 5s, 30s, 5min
        local blockDurations = {1, 5, 30, 300}
        local blockIndex = math.min(limiter.violations, #blockDurations)
        limiter.blockedUntil = now + blockDurations[blockIndex]
        
        warn("Rate limit exceeded for", identifier, "- blocked for", blockDurations[blockIndex], "seconds")
        return false
    end
    
    -- Allow request
    table.insert(limiter.timestamps, now)
    
    -- Reset violations after good behavior
    if #limiter.timestamps < NETWORK_CONFIG.RATE_LIMIT / 2 then
        limiter.violations = math.max(0, limiter.violations - 1)
    end
    
    return true
end

-- Implement message queuing
-- @param eventName: string - Event name
-- @param data: any - Data to queue
-- @param target: string - "server", "client", or "broadcast"
function NetworkManager:QueueMessage(eventName, data, target, player)
    -- Limit queue size
    if #messageQueue >= 100 then
        -- Remove oldest non-critical messages
        for i = 1, 10 do
            if messageQueue[i] and not messageQueue[i].critical then
                table.remove(messageQueue, i)
            end
        end
    end
    
    -- Add to queue
    local queueItem = {
        event = eventName,
        data = data,
        target = target or "server",
        player = player,
        timestamp = tick(),
        retries = 0,
        critical = self:IsMessageCritical(eventName)
    }
    
    table.insert(messageQueue, queueItem)
    
    -- Sort by priority (critical first, then by timestamp)
    table.sort(messageQueue, function(a, b)
        if a.critical ~= b.critical then
            return a.critical
        end
        return a.timestamp < b.timestamp
    end)
end

-- Check if message is critical
function NetworkManager:IsMessageCritical(eventName)
    local criticalEvents = {
        "SaveProgress",
        "SubmitAnswer",
        "ErrorReport",
        "UpdateProgress"
    }
    
    for _, critical in ipairs(criticalEvents) do
        if eventName == critical then
            return true
        end
    end
    
    return false
end

-- Process message queue
function NetworkManager:ProcessQueue()
    if self.connectionStatus ~= "Connected" then
        return
    end
    
    local processed = 0
    local maxProcess = 10
    
    for i = #messageQueue, 1, -1 do
        if processed >= maxProcess then break end
        
        local message = messageQueue[i]
        local age = tick() - message.timestamp
        
        -- Check timeout
        if age > NETWORK_CONFIG.TIMEOUT and not message.critical then
            table.remove(messageQueue, i)
            warn("Message timed out:", message.event)
        elseif self:CheckRateLimit(message.event) then
            local success = false
            
            -- Send based on target
            if message.target == "server" then
                success = self:SendToServer(message.event, message.data)
            elseif message.target == "client" and message.player then
                success = self:SendToClient(message.player, message.event, message.data)
            elseif message.target == "broadcast" then
                success = self:BroadcastToClients(message.event, message.data)
            end
            
            if success then
                table.remove(messageQueue, i)
                processed = processed + 1
            else
                message.retries = message.retries + 1
                
                if message.retries > NETWORK_CONFIG.MAX_RETRIES and not message.critical then
                    table.remove(messageQueue, i)
                    warn("Message failed after max retries:", message.event)
                end
            end
        end
    end
end

-- Start queue processor
function NetworkManager:StartQueueProcessor()
    spawn(function()
        while true do
            wait(1)
            self:ProcessQueue()
        end
    end)
end

-- Implement reliable messaging
-- @param eventName: string - Event name
-- @param data: table - Message data
-- @param callback: function - Acknowledgment callback
function NetworkManager:SendReliable(eventName, data, callback)
    local messageId = HttpService:GenerateGUID(false)
    
    -- Wrap data with metadata
    local wrappedData = {
        messageId = messageId,
        payload = data,
        timestamp = tick(),
        requiresAck = true
    }
    
    -- Store pending request
    pendingRequests[messageId] = {
        eventName = eventName,
        data = wrappedData,
        callback = callback,
        retries = 0,
        timestamp = tick()
    }
    
    -- Send initial message
    self:SendWithRetry(messageId)
    
    -- Set timeout for acknowledgment
    self.retryTimers[messageId] = spawn(function()
        wait(NETWORK_CONFIG.TIMEOUT)
        
        if pendingRequests[messageId] then
            -- No acknowledgment received
            if callback then
                callback(false, "Timeout")
            end
            
            pendingRequests[messageId] = nil
            self.retryTimers[messageId] = nil
        end
    end)
    
    return messageId
end

-- Send with retry logic
function NetworkManager:SendWithRetry(messageId)
    local request = pendingRequests[messageId]
    if not request then return end
    
    if request.retries >= NETWORK_CONFIG.MAX_RETRIES then
        if request.callback then
            request.callback(false, "Max retries exceeded")
        end
        pendingRequests[messageId] = nil
        return
    end
    
    -- Send message
    local success = self:SendToServer(request.eventName, request.data)
    
    if not success then
        request.retries = request.retries + 1
        
        -- Exponential backoff
        wait(NETWORK_CONFIG.RETRY_DELAY * (2 ^ request.retries))
        self:SendWithRetry(messageId)
    end
end

-- Handle acknowledgment
function NetworkManager:HandleAcknowledgment(messageId)
    local request = pendingRequests[messageId]
    if not request then return end
    
    -- Cancel retry timer
    if self.retryTimers[messageId] then
        self.retryTimers[messageId] = nil
    end
    
    -- Call callback
    if request.callback then
        request.callback(true, nil)
    end
    
    -- Clean up
    pendingRequests[messageId] = nil
end

-- Implement data compression
-- @param data: table - Data to compress
-- @return table - Compressed data wrapper
function NetworkManager:CompressData(data)
    local json = HttpService:JSONEncode(data)
    local originalSize = #json
    
    -- Simple compression: remove whitespace and use short keys
    local compressed = json:gsub("%s+", "")
    
    -- Use dictionary compression for common strings
    local dictionary = {
        ["position"] = "p",
        ["rotation"] = "r",
        ["velocity"] = "v",
        ["player"] = "pl",
        ["timestamp"] = "t",
        ["message"] = "m",
        ["data"] = "d",
        ["success"] = "s",
        ["error"] = "e"
    }
    
    for original, short in pairs(dictionary) do
        compressed = compressed:gsub('"' .. original .. '"', '"' .. short .. '"')
    end
    
    local compressedSize = #compressed
    local compressionRatio = 1 - (compressedSize / originalSize)
    
    -- Only use compression if it saves > 20%
    if compressionRatio > 0.2 then
        return {
            compressed = true,
            data = compressed,
            dictionary = dictionary,
            originalSize = originalSize,
            compressedSize = compressedSize
        }
    else
        return data
    end
end

-- Implement data decompression
-- @param compressed: any - Compressed data or wrapper
-- @return table - Decompressed data
function NetworkManager:DecompressData(compressed)
    -- Check if actually compressed
    if type(compressed) ~= "table" or not compressed.compressed then
        return compressed
    end
    
    local decompressed = compressed.data
    
    -- Reverse dictionary compression
    if compressed.dictionary then
        for original, short in pairs(compressed.dictionary) do
            decompressed = decompressed:gsub('"' .. short .. '"', '"' .. original .. '"')
        end
    end
    
    -- Parse JSON
    local success, result = pcall(function()
        return HttpService:JSONDecode(decompressed)
    end)
    
    if success then
        return result
    else
        warn("Decompression failed:", result)
        return {}
    end
end

-- Implement network monitoring
function NetworkManager:MonitorNetwork()
    spawn(function()
        while true do
            wait(5)
            
            -- Measure latency
            local startTime = tick()
            local serverTime = self:InvokeRemote("GetServerTime", {})
            
            if serverTime then
                local latency = (tick() - startTime) * 1000  -- Convert to ms
                
                -- Update average latency
                if self.metrics.averageLatency == 0 then
                    self.metrics.averageLatency = latency
                else
                    self.metrics.averageLatency = (self.metrics.averageLatency * 0.9) + (latency * 0.1)
                end
                
                -- Update connection status
                if latency < 100 then
                    self.connectionStatus = "Excellent"
                elseif latency < 200 then
                    self.connectionStatus = "Good"
                elseif latency < 500 then
                    self.connectionStatus = "Fair"
                else
                    self.connectionStatus = "Poor"
                end
            else
                self.connectionStatus = "Disconnected"
            end
            
            -- Calculate packet loss
            if self.metrics.sentCount > 0 then
                self.metrics.packetLoss = (self.metrics.failedCount / self.metrics.sentCount) * 100
            end
            
            -- Report issues
            if self.connectionStatus == "Poor" or self.connectionStatus == "Disconnected" then
                warn("Network issues detected:", self.connectionStatus, "Latency:", self.metrics.averageLatency)
            end
        end
    end)
end

-- Start heartbeat monitoring
function NetworkManager:StartHeartbeat()
    if self.isClient then
        spawn(function()
            while true do
                wait(30)  -- Every 30 seconds
                
                self:SendToServer("Heartbeat", {
                    timestamp = tick(),
                    metrics = self.metrics
                })
                
                self.lastHeartbeat = tick()
            end
        end)
    end
    
    -- Start network monitoring
    self:MonitorNetwork()
end

-- Handle player disconnection
-- @param player: Player - Disconnecting player
function NetworkManager:HandleDisconnect(player)
    if not self.isServer then return end
    
    -- Clear player-specific pending requests
    for messageId, request in pairs(pendingRequests) do
        if request.player == player then
            pendingRequests[messageId] = nil
            
            if self.retryTimers[messageId] then
                self.retryTimers[messageId] = nil
            end
        end
    end
    
    -- Clear player from message queue
    for i = #messageQueue, 1, -1 do
        if messageQueue[i].player == player then
            table.remove(messageQueue, i)
        end
    end
    
    -- Clear rate limiter for player
    local playerKey = tostring(player.UserId)
    for key, _ in pairs(self.rateLimiter) do
        if key:find(playerKey) then
            self.rateLimiter[key] = nil
        end
    end
    
    -- Notify other systems
    self:BroadcastToClients("PlayerDisconnected", {
        playerId = player.UserId,
        playerName = player.Name
    }, player)
end

-- Implement request batching
-- @param requests: table - Array of requests
-- @return table - Array of results
function NetworkManager:BatchRequests(requests)
    if #requests == 0 then return {} end
    
    local results = {}
    local batches = {}
    
    -- Split into batches
    for i = 1, #requests, NETWORK_CONFIG.BATCH_SIZE do
        local batch = {}
        for j = i, math.min(i + NETWORK_CONFIG.BATCH_SIZE - 1, #requests) do
            table.insert(batch, requests[j])
        end
        table.insert(batches, batch)
    end
    
    -- Process each batch
    for _, batch in ipairs(batches) do
        -- Create batch message
        local batchMessage = {
            type = "batch",
            requests = batch,
            batchId = HttpService:GenerateGUID(false)
        }
        
        -- Send batch
        local batchResult = self:InvokeRemote("ProcessBatch", batchMessage)
        
        if batchResult and type(batchResult) == "table" then
            -- Extract individual results
            for _, result in ipairs(batchResult) do
                table.insert(results, result)
            end
        else
            -- Batch failed, try individual requests
            for _, request in ipairs(batch) do
                local result = nil
                
                if request.type == "invoke" then
                    result = self:InvokeRemote(request.name, request.data)
                elseif request.type == "event" then
                    self:SendToServer(request.name, request.data)
                    result = {success = true}
                end
                
                table.insert(results, result)
            end
        end
    end
    
    return results
end

-- Implement network security
function NetworkManager:ValidateRequest(player, data)
    if not self.isServer then return true end
    
    -- Check player exists and is valid
    if not player or not player:IsA("Player") or not player.Parent then
        return false
    end
    
    -- Check data size
    local dataStr = HttpService:JSONEncode(data or {})
    if #dataStr > 100000 then  -- 100KB limit
        warn("Data too large from", player.Name)
        return false
    end
    
    -- Check for suspicious patterns
    local suspicious = {
        "getfenv",
        "setfenv",
        "loadstring",
        "require",
        "_G",
        "rawset",
        "rawget"
    }
    
    for _, pattern in ipairs(suspicious) do
        if dataStr:find(pattern) then
            self:LogSuspiciousActivity(player, "Suspicious pattern: " .. pattern)
            return false
        end
    end
    
    -- Validate data types
    if type(data) == "table" then
        for key, value in pairs(data) do
            -- Check key type
            if type(key) ~= "string" and type(key) ~= "number" then
                return false
            end
            
            -- Check value type (no functions or userdata)
            local valueType = type(value)
            if valueType == "function" or valueType == "userdata" or valueType == "thread" then
                self:LogSuspiciousActivity(player, "Invalid data type: " .. valueType)
                return false
            end
        end
    end
    
    return true
end

-- Log suspicious activity
function NetworkManager:LogSuspiciousActivity(player, reason)
    warn("Suspicious activity from", player.Name, ":", reason)
    
    -- Send to server for logging
    if self.isClient then
        self:SendToServer("ErrorReport", {
            type = "suspicious_activity",
            player = player.Name,
            reason = reason,
            timestamp = tick()
        })
    else
        -- Server-side logging
        -- Could integrate with external logging service
    end
end

-- Clean up network resources
function NetworkManager:Destroy()
    -- Clear all timers
    for _, timer in pairs(self.retryTimers) do
        if timer then
            timer = nil
        end
    end
    
    -- Process critical messages before cleanup
    for _, message in ipairs(messageQueue) do
        if message.critical then
            -- Try to send critical messages one last time
            if message.target == "server" then
                self:SendToServer(message.event, message.data)
            end
        end
    end
    
    -- Clear all data structures
    messageQueue = {}
    pendingRequests = {}
    self.callbacks = {}
    self.rateLimiter = {}
    self.messageHandlers = {}
    self.functionHandlers = {}
    self.retryTimers = {}
    
    -- Reset metrics
    self.metrics = {
        sentCount = 0,
        receivedCount = 0,
        failedCount = 0,
        averageLatency = 0,
        packetLoss = 0
    }
    
    self.connectionStatus = "Disconnected"
end

-- Get network statistics
function NetworkManager:GetStatistics()
    return {
        connectionStatus = self.connectionStatus,
        metrics = self.metrics,
        queueSize = #messageQueue,
        pendingRequests = #pendingRequests,
        rateLimitViolations = self:GetRateLimitViolations()
    }
end

-- Get rate limit violations count
function NetworkManager:GetRateLimitViolations()
    local violations = 0
    for _, limiter in pairs(self.rateLimiter) do
        violations = violations + (limiter.violations or 0)
    end
    return violations
end

return NetworkManager
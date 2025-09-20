--!strict
--[[
    Realtime Service
    WebSocket and Pusher integration for real-time updates
    Handles bidirectional communication with the backend
]]

local HttpService = game:GetService("HttpService")
local RunService = game:GetService("RunService")

-- Types
type WebSocketMessage = {
    type: string,
    event: string,
    data: any,
    timestamp: number,
    id: string?
}

type PusherConfig = {
    key: string,
    cluster: string,
    encrypted: boolean,
    authEndpoint: string,
    authHeaders: {[string]: string}?
}

type ConnectionState =
    "disconnected" |
    "connecting" |
    "connected" |
    "reconnecting" |
    "failed"

type RealtimeConfig = {
    websocketUrl: string,
    pusherConfig: PusherConfig,
    reconnectAttempts: number,
    reconnectDelay: number,
    heartbeatInterval: number,
    messageTimeout: number,
    usePusherFallback: boolean
}

-- Realtime Service Class
local RealtimeService = {}
RealtimeService.__index = RealtimeService

function RealtimeService.new(config: RealtimeConfig, stateManager: any, eventEmitter: any)
    local self = setmetatable({}, RealtimeService)

    self.config = config
    self.stateManager = stateManager
    self.eventEmitter = eventEmitter

    -- Connection state
    self.connectionState: ConnectionState = "disconnected"
    self.websocket = nil
    self.pusherClient = nil
    self.isUsingPusher = false

    -- Reconnection
    self.reconnectAttempts = 0
    self.reconnectTimer = nil

    -- Message handling
    self.messageQueue = {}
    self.messageHandlers = {}
    self.pendingRequests = {}

    -- Heartbeat
    self.heartbeatTimer = nil
    self.lastHeartbeat = 0
    self.missedHeartbeats = 0

    -- Channels
    self.subscribedChannels = {}

    -- Statistics
    self.stats = {
        messagesSent = 0,
        messagesReceived = 0,
        reconnections = 0,
        errors = 0,
        latency = 0
    }

    return self
end

function RealtimeService:connect()
    if self.connectionState == "connected" or self.connectionState == "connecting" then
        return
    end

    self.connectionState = "connecting"
    self.stateManager:setState("realtimeConnectionState", "connecting")

    -- Try WebSocket first
    local websocketSuccess = self:connectWebSocket()

    if not websocketSuccess and self.config.usePusherFallback then
        -- Fall back to Pusher
        self:connectPusher()
    elseif not websocketSuccess then
        self:handleConnectionFailure()
    end
end

function RealtimeService:connectWebSocket(): boolean
    -- Note: Roblox Studio doesn't have native WebSocket support
    -- This uses HTTP long-polling to simulate WebSocket behavior

    local success, result = pcall(function()
        -- Establish connection via HTTP
        local response = HttpService:RequestAsync({
            Url = self.config.websocketUrl .. "/connect",
            Method = "POST",
            Headers = {
                ["Content-Type"] = "application/json"
            },
            Body = HttpService:JSONEncode({
                clientType = "roblox-studio",
                version = "2.0.0",
                capabilities = {
                    "content-generation",
                    "real-time-preview",
                    "collaborative-editing"
                }
            })
        })

        if response.Success then
            local data = HttpService:JSONDecode(response.Body)
            self.websocket = {
                sessionId = data.sessionId,
                endpoint = data.endpoint,
                token = data.token
            }
            return true
        end

        return false
    end)

    if success and result then
        self:onWebSocketConnected()
        self:startLongPolling()
        return true
    end

    return false
end

function RealtimeService:startLongPolling()
    -- Simulate WebSocket with HTTP long-polling
    task.spawn(function()
        while self.connectionState == "connected" and self.websocket do
            local success, result = pcall(function()
                return HttpService:RequestAsync({
                    Url = self.config.websocketUrl .. "/poll",
                    Method = "GET",
                    Headers = {
                        ["X-Session-Id"] = self.websocket.sessionId,
                        ["Authorization"] = "Bearer " .. self.websocket.token
                    }
                })
            end)

            if success and result.Success then
                local messages = HttpService:JSONDecode(result.Body)
                for _, message in ipairs(messages) do
                    self:handleMessage(message)
                end
            else
                -- Connection lost
                if self.connectionState == "connected" then
                    self:handleDisconnection()
                end
                break
            end

            task.wait(0.1) -- Short delay between polls
        end
    end)
end

function RealtimeService:connectPusher()
    self.isUsingPusher = true

    -- Initialize Pusher connection via HTTP bridge
    local success, result = pcall(function()
        return HttpService:RequestAsync({
            Url = self.config.websocketUrl .. "/pusher/connect",
            Method = "POST",
            Headers = {
                ["Content-Type"] = "application/json"
            },
            Body = HttpService:JSONEncode({
                key = self.config.pusherConfig.key,
                cluster = self.config.pusherConfig.cluster,
                encrypted = self.config.pusherConfig.encrypted
            })
        })
    end)

    if success and result.Success then
        local data = HttpService:JSONDecode(result.Body)
        self.pusherClient = {
            socketId = data.socket_id,
            channels = {}
        }
        self:onPusherConnected()
    else
        self:handleConnectionFailure()
    end
end

function RealtimeService:onWebSocketConnected()
    self.connectionState = "connected"
    self.reconnectAttempts = 0
    self.stateManager:setState("realtimeConnectionState", "connected")

    -- Start heartbeat
    self:startHeartbeat()

    -- Resubscribe to channels
    for channel, _ in pairs(self.subscribedChannels) do
        self:subscribe(channel)
    end

    -- Process queued messages
    self:processMessageQueue()

    -- Emit connected event
    self.eventEmitter:emit("realtimeConnected", {
        type = "websocket",
        sessionId = self.websocket.sessionId
    })

    print("[RealtimeService] WebSocket connected")
end

function RealtimeService:onPusherConnected()
    self.connectionState = "connected"
    self.reconnectAttempts = 0
    self.stateManager:setState("realtimeConnectionState", "connected")

    -- Start Pusher event polling
    self:startPusherPolling()

    -- Resubscribe to channels
    for channel, _ in pairs(self.subscribedChannels) do
        self:subscribePusherChannel(channel)
    end

    -- Process queued messages
    self:processMessageQueue()

    -- Emit connected event
    self.eventEmitter:emit("realtimeConnected", {
        type = "pusher",
        socketId = self.pusherClient.socketId
    })

    print("[RealtimeService] Pusher connected (fallback)")
end

function RealtimeService:startPusherPolling()
    task.spawn(function()
        while self.connectionState == "connected" and self.pusherClient do
            local success, result = pcall(function()
                return HttpService:RequestAsync({
                    Url = self.config.websocketUrl .. "/pusher/events",
                    Method = "GET",
                    Headers = {
                        ["X-Socket-Id"] = self.pusherClient.socketId
                    }
                })
            end)

            if success and result.Success then
                local events = HttpService:JSONDecode(result.Body)
                for _, event in ipairs(events) do
                    self:handlePusherEvent(event)
                end
            end

            task.wait(0.5) -- Pusher polling interval
        end
    end)
end

function RealtimeService:subscribe(channel: string)
    if self.subscribedChannels[channel] then
        return
    end

    self.subscribedChannels[channel] = true

    if self.connectionState == "connected" then
        if self.isUsingPusher then
            self:subscribePusherChannel(channel)
        else
            self:subscribeWebSocketChannel(channel)
        end
    end
end

function RealtimeService:subscribeWebSocketChannel(channel: string)
    self:send({
        type = "subscribe",
        channel = channel
    })
end

function RealtimeService:subscribePusherChannel(channel: string)
    local isPrivate = string.sub(channel, 1, 8) == "private-"
    local isPresence = string.sub(channel, 1, 9) == "presence-"

    if isPrivate or isPresence then
        -- Need authentication for private/presence channels
        local authData = self:authenticatePusherChannel(channel)
        if authData then
            self.pusherClient.channels[channel] = authData
        end
    else
        -- Public channel
        self.pusherClient.channels[channel] = true
    end

    -- Send subscription request
    HttpService:RequestAsync({
        Url = self.config.websocketUrl .. "/pusher/subscribe",
        Method = "POST",
        Headers = {
            ["Content-Type"] = "application/json",
            ["X-Socket-Id"] = self.pusherClient.socketId
        },
        Body = HttpService:JSONEncode({
            channel = channel,
            auth = self.pusherClient.channels[channel]
        })
    })
end

function RealtimeService:authenticatePusherChannel(channel: string)
    local success, result = pcall(function()
        return HttpService:RequestAsync({
            Url = self.config.pusherConfig.authEndpoint,
            Method = "POST",
            Headers = self.config.pusherConfig.authHeaders or {},
            Body = HttpService:JSONEncode({
                socket_id = self.pusherClient.socketId,
                channel_name = channel
            })
        })
    end)

    if success and result.Success then
        return HttpService:JSONDecode(result.Body)
    end

    return nil
end

function RealtimeService:unsubscribe(channel: string)
    if not self.subscribedChannels[channel] then
        return
    end

    self.subscribedChannels[channel] = nil

    if self.connectionState == "connected" then
        self:send({
            type = "unsubscribe",
            channel = channel
        })
    end
end

function RealtimeService:send(message: any): string?
    local messageId = HttpService:GenerateGUID(false)
    local wrappedMessage: WebSocketMessage = {
        type = message.type or "message",
        event = message.event or "default",
        data = message.data or message,
        timestamp = os.time(),
        id = messageId
    }

    if self.connectionState == "connected" then
        self:sendImmediate(wrappedMessage)
    else
        -- Queue message for later
        table.insert(self.messageQueue, wrappedMessage)

        -- Try to reconnect if not already
        if self.connectionState == "disconnected" then
            self:connect()
        end
    end

    self.stats.messagesSent = self.stats.messagesSent + 1
    return messageId
end

function RealtimeService:sendImmediate(message: WebSocketMessage)
    if self.isUsingPusher then
        self:sendPusherMessage(message)
    else
        self:sendWebSocketMessage(message)
    end
end

function RealtimeService:sendWebSocketMessage(message: WebSocketMessage)
    task.spawn(function()
        local success, result = pcall(function()
            return HttpService:RequestAsync({
                Url = self.config.websocketUrl .. "/send",
                Method = "POST",
                Headers = {
                    ["Content-Type"] = "application/json",
                    ["X-Session-Id"] = self.websocket.sessionId,
                    ["Authorization"] = "Bearer " .. self.websocket.token
                },
                Body = HttpService:JSONEncode(message)
            })
        end)

        if not success then
            self.stats.errors = self.stats.errors + 1
            self.eventEmitter:emit("realtimeError", {
                error = "Failed to send message",
                message = message
            })
        end
    end)
end

function RealtimeService:sendPusherMessage(message: WebSocketMessage)
    task.spawn(function()
        local success, result = pcall(function()
            return HttpService:RequestAsync({
                Url = self.config.websocketUrl .. "/pusher/trigger",
                Method = "POST",
                Headers = {
                    ["Content-Type"] = "application/json",
                    ["X-Socket-Id"] = self.pusherClient.socketId
                },
                Body = HttpService:JSONEncode({
                    channel = message.channel or "default",
                    event = message.event,
                    data = message.data
                })
            })
        end)

        if not success then
            self.stats.errors = self.stats.errors + 1
        end
    end)
end

function RealtimeService:request(method: string, params: any?, timeout: number?): any
    timeout = timeout or self.config.messageTimeout

    local requestId = self:send({
        type = "request",
        method = method,
        params = params
    })

    if not requestId then
        return nil, "Failed to send request"
    end

    -- Create promise for response
    local responseReceived = false
    local responseData = nil
    local responseError = nil

    self.pendingRequests[requestId] = function(data, error)
        responseReceived = true
        responseData = data
        responseError = error
    end

    -- Wait for response with timeout
    local startTime = os.clock()
    while not responseReceived and (os.clock() - startTime) < timeout do
        task.wait(0.1)
    end

    self.pendingRequests[requestId] = nil

    if responseReceived then
        return responseData, responseError
    else
        return nil, "Request timed out"
    end
end

function RealtimeService:handleMessage(message: WebSocketMessage)
    self.stats.messagesReceived = self.stats.messagesReceived + 1

    -- Update latency
    if message.timestamp then
        self.stats.latency = os.time() - message.timestamp
    end

    -- Handle different message types
    if message.type == "response" and message.id then
        -- Response to a request
        local handler = self.pendingRequests[message.id]
        if handler then
            handler(message.data, message.error)
        end
    elseif message.type == "heartbeat" then
        -- Heartbeat response
        self.lastHeartbeat = os.time()
        self.missedHeartbeats = 0
    elseif message.type == "event" then
        -- Event from server
        self:handleEvent(message)
    else
        -- Generic message
        self.eventEmitter:emit("realtimeMessage", message)
    end

    -- Call registered handlers
    local handlers = self.messageHandlers[message.event]
    if handlers then
        for _, handler in ipairs(handlers) do
            task.spawn(handler, message.data)
        end
    end
end

function RealtimeService:handlePusherEvent(event: any)
    local message: WebSocketMessage = {
        type = "event",
        event = event.event,
        data = event.data,
        timestamp = os.time(),
        channel = event.channel
    }

    self:handleMessage(message)
end

function RealtimeService:handleEvent(message: WebSocketMessage)
    -- Handle specific events
    if message.event == "content.generated" then
        self.eventEmitter:emit("contentGenerated", message.data)
    elseif message.event == "content.progress" then
        self.eventEmitter:emit("contentProgress", message.data)
    elseif message.event == "content.error" then
        self.eventEmitter:emit("contentError", message.data)
    elseif message.event == "collaboration.update" then
        self.eventEmitter:emit("collaborationUpdate", message.data)
    elseif message.event == "asset.ready" then
        self.eventEmitter:emit("assetReady", message.data)
    end
end

function RealtimeService:on(event: string, handler: (any) -> ())
    if not self.messageHandlers[event] then
        self.messageHandlers[event] = {}
    end
    table.insert(self.messageHandlers[event], handler)
end

function RealtimeService:off(event: string, handler: (any) -> ()?)
    if not self.messageHandlers[event] then
        return
    end

    if handler then
        for i, h in ipairs(self.messageHandlers[event]) do
            if h == handler then
                table.remove(self.messageHandlers[event], i)
                break
            end
        end
    else
        self.messageHandlers[event] = {}
    end
end

function RealtimeService:startHeartbeat()
    if self.heartbeatTimer then
        task.cancel(self.heartbeatTimer)
    end

    self.heartbeatTimer = task.spawn(function()
        while self.connectionState == "connected" do
            task.wait(self.config.heartbeatInterval)

            -- Send heartbeat
            self:send({
                type = "heartbeat",
                timestamp = os.time()
            })

            -- Check for missed heartbeats
            if os.time() - self.lastHeartbeat > self.config.heartbeatInterval * 2 then
                self.missedHeartbeats = self.missedHeartbeats + 1

                if self.missedHeartbeats >= 3 then
                    -- Connection seems dead
                    self:handleDisconnection()
                end
            end
        end
    end)
end

function RealtimeService:processMessageQueue()
    if #self.messageQueue == 0 then
        return
    end

    local queue = self.messageQueue
    self.messageQueue = {}

    for _, message in ipairs(queue) do
        self:sendImmediate(message)
    end
end

function RealtimeService:handleDisconnection()
    if self.connectionState == "disconnected" then
        return
    end

    self.connectionState = "disconnected"
    self.stateManager:setState("realtimeConnectionState", "disconnected")

    -- Stop heartbeat
    if self.heartbeatTimer then
        task.cancel(self.heartbeatTimer)
        self.heartbeatTimer = nil
    end

    -- Clear connection objects
    self.websocket = nil
    self.pusherClient = nil

    -- Emit disconnected event
    self.eventEmitter:emit("realtimeDisconnected")

    print("[RealtimeService] Disconnected")

    -- Attempt reconnection
    self:scheduleReconnection()
end

function RealtimeService:handleConnectionFailure()
    self.connectionState = "failed"
    self.stateManager:setState("realtimeConnectionState", "failed")

    self.stats.errors = self.stats.errors + 1

    self.eventEmitter:emit("realtimeConnectionFailed")

    print("[RealtimeService] Connection failed")

    -- Schedule reconnection
    self:scheduleReconnection()
end

function RealtimeService:scheduleReconnection()
    if self.reconnectTimer then
        task.cancel(self.reconnectTimer)
    end

    self.reconnectAttempts = self.reconnectAttempts + 1

    if self.reconnectAttempts <= self.config.reconnectAttempts then
        -- Exponential backoff
        local delay = self.config.reconnectDelay * math.pow(2, self.reconnectAttempts - 1)
        delay = math.min(delay, 60) -- Cap at 60 seconds

        self.connectionState = "reconnecting"
        self.stateManager:setState("realtimeConnectionState", "reconnecting")

        print(string.format("[RealtimeService] Reconnecting in %d seconds (attempt %d/%d)",
            delay, self.reconnectAttempts, self.config.reconnectAttempts))

        self.reconnectTimer = task.wait(delay)
        self:connect()

        self.stats.reconnections = self.stats.reconnections + 1
    else
        -- Give up
        self.connectionState = "failed"
        self.stateManager:setState("realtimeConnectionState", "failed")

        self.eventEmitter:emit("realtimeReconnectionFailed")

        print("[RealtimeService] Reconnection failed - max attempts reached")
    end
end

function RealtimeService:disconnect()
    if self.connectionState == "disconnected" then
        return
    end

    -- Cancel reconnection
    if self.reconnectTimer then
        task.cancel(self.reconnectTimer)
        self.reconnectTimer = nil
    end

    -- Send disconnect message
    if self.connectionState == "connected" then
        self:send({
            type = "disconnect"
        })
    end

    -- Clean up
    self:handleDisconnection()
end

function RealtimeService:getStatistics()
    return {
        state = self.connectionState,
        isUsingPusher = self.isUsingPusher,
        messagesSent = self.stats.messagesSent,
        messagesReceived = self.stats.messagesReceived,
        reconnections = self.stats.reconnections,
        errors = self.stats.errors,
        latency = self.stats.latency,
        queuedMessages = #self.messageQueue,
        subscribedChannels = self.subscribedChannels
    }
end

function RealtimeService:cleanup()
    self:disconnect()

    -- Clear all handlers
    self.messageHandlers = {}
    self.pendingRequests = {}

    -- Clear state
    self.messageQueue = {}
    self.subscribedChannels = {}
end

return RealtimeService
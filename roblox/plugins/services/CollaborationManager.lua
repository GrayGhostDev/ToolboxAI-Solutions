--!strict
--[[
    Collaboration Manager Service
    Handles multi-user editing, presence, and real-time synchronization
    Implements Operational Transformation for conflict resolution
]]

local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local StudioService = game:GetService("StudioService")
local CollectionService = game:GetService("CollectionService")

-- Types
type CollaboratorInfo = {
    userId: string,
    username: string,
    avatar: string?,
    color: Color3,
    position: Vector3?,
    selection: {Instance}?,
    status: "active" | "idle" | "away",
    lastActivity: number,
    permissions: {
        canEdit: boolean,
        canDelete: boolean,
        canInvite: boolean
    }
}

type CollaborationSession = {
    id: string,
    name: string,
    hostId: string,
    collaborators: {[string]: CollaboratorInfo},
    startTime: number,
    sharedAssets: {string},
    settings: {
        maxCollaborators: number,
        autoSave: boolean,
        conflictResolution: "manual" | "automatic" | "lastWrite",
        permissions: "open" | "restricted"
    }
}

type Operation = {
    id: string,
    type: "insert" | "delete" | "modify" | "move",
    target: Instance?,
    path: string,
    data: any,
    timestamp: number,
    authorId: string,
    version: number
}

type Conflict = {
    id: string,
    operations: {Operation},
    resolution: "pending" | "resolved" | "ignored",
    resolvedBy: string?,
    resolvedAt: number?
}

type PresenceUpdate = {
    userId: string,
    position: Vector3?,
    selection: {Instance}?,
    cursor: Vector2?,
    viewport: {
        camera: CFrame,
        zoom: number
    }?,
    timestamp: number
}

-- Operational Transformation functions
local OperationalTransform = {}

function OperationalTransform.transform(op1: Operation, op2: Operation): (Operation, Operation)
    -- Transform op1 against op2 for concurrent editing
    if op1.type == "insert" and op2.type == "insert" then
        if op1.path < op2.path then
            return op1, {
                id = op2.id,
                type = op2.type,
                target = op2.target,
                path = op2.path,
                data = op2.data,
                timestamp = op2.timestamp,
                authorId = op2.authorId,
                version = op2.version
            }
        elseif op1.path > op2.path then
            return {
                id = op1.id,
                type = op1.type,
                target = op1.target,
                path = op1.path,
                data = op1.data,
                timestamp = op1.timestamp,
                authorId = op1.authorId,
                version = op1.version
            }, op2
        else
            -- Same position, use timestamp to determine order
            if op1.timestamp < op2.timestamp then
                return op1, {
                    id = op2.id,
                    type = op2.type,
                    target = op2.target,
                    path = op2.path .. ".1",
                    data = op2.data,
                    timestamp = op2.timestamp,
                    authorId = op2.authorId,
                    version = op2.version
                }
            else
                return {
                    id = op1.id,
                    type = op1.type,
                    target = op1.target,
                    path = op1.path .. ".1",
                    data = op1.data,
                    timestamp = op1.timestamp,
                    authorId = op1.authorId,
                    version = op1.version
                }, op2
            end
        end
    elseif op1.type == "delete" and op2.type == "delete" then
        if op1.path == op2.path then
            -- Both trying to delete same thing, make one a no-op
            return {
                id = op1.id,
                type = "modify", -- Convert to no-op modify
                target = op1.target,
                path = op1.path,
                data = {},
                timestamp = op1.timestamp,
                authorId = op1.authorId,
                version = op1.version
            }, op2
        end
    end

    -- Default: return unchanged
    return op1, op2
end

-- Collaboration Manager Class
local CollaborationManager = {}
CollaborationManager.__index = CollaborationManager

function CollaborationManager.new(config: any, stateManager: any, eventEmitter: any, realtimeService: any)
    local self = setmetatable({}, CollaborationManager)

    self.config = config
    self.stateManager = stateManager
    self.eventEmitter = eventEmitter
    self.realtimeService = realtimeService

    -- Session management
    self.currentSession = nil :: CollaborationSession?
    self.myUserId = tostring(StudioService:GetUserId())
    self.myInfo = nil :: CollaboratorInfo?

    -- Collaboration state
    self.collaborators = {}
    self.presenceIndicators = {}
    self.selectionHighlights = {}
    self.cursorIndicators = {}

    -- Operation tracking
    self.operationHistory = {}
    self.pendingOperations = {}
    self.operationVersion = 0
    self.conflicts = {}

    -- Activity tracking
    self.activityLog = {}
    self.lastActivity = os.time()
    self.idleThreshold = 60 -- seconds

    -- UI elements
    self.collaboratorList = nil
    self.presenceOverlay = nil

    -- Initialize
    self:initialize()

    return self
end

function CollaborationManager:initialize()
    -- Set up my collaborator info
    self.myInfo = {
        userId = self.myUserId,
        username = "User_" .. self.myUserId,
        color = self:generateUserColor(self.myUserId),
        status = "active",
        lastActivity = os.time(),
        permissions = {
            canEdit = true,
            canDelete = true,
            canInvite = true
        }
    }

    -- Subscribe to realtime events
    self:setupRealtimeHandlers()

    -- Start activity monitoring
    self:startActivityMonitoring()

    -- Set up UI
    self:createCollaborationUI()

    print("[CollaborationManager] Initialized")
end

function CollaborationManager:createSession(name: string, settings: any?): string
    local sessionId = HttpService:GenerateGUID(false)

    self.currentSession = {
        id = sessionId,
        name = name,
        hostId = self.myUserId,
        collaborators = {
            [self.myUserId] = self.myInfo
        },
        startTime = os.time(),
        sharedAssets = {},
        settings = settings or {
            maxCollaborators = 10,
            autoSave = true,
            conflictResolution = "automatic",
            permissions = "open"
        }
    }

    -- Join collaboration channel
    self.realtimeService:subscribe("collaboration-" .. sessionId)

    -- Announce session creation
    self.realtimeService:send({
        event = "session.created",
        data = self.currentSession
    })

    self.eventEmitter:emit("sessionCreated", self.currentSession)
    self.stateManager:setState("collaborationSession", self.currentSession)

    print("[CollaborationManager] Session created:", sessionId)

    return sessionId
end

function CollaborationManager:joinSession(sessionId: string): boolean
    -- Request to join session
    local response = self.realtimeService:request("session.join", {
        sessionId = sessionId,
        userInfo = self.myInfo
    }, 5)

    if response and response.success then
        self.currentSession = response.session

        -- Subscribe to session channel
        self.realtimeService:subscribe("collaboration-" .. sessionId)
        self.realtimeService:subscribe("presence-" .. sessionId)

        -- Add self to collaborators
        self.currentSession.collaborators[self.myUserId] = self.myInfo

        -- Create presence indicators for existing collaborators
        for userId, info in pairs(self.currentSession.collaborators) do
            if userId ~= self.myUserId then
                self:createPresenceIndicator(info)
            end
        end

        self.eventEmitter:emit("sessionJoined", self.currentSession)
        self.stateManager:setState("collaborationSession", self.currentSession)

        print("[CollaborationManager] Joined session:", sessionId)
        return true
    end

    return false
end

function CollaborationManager:leaveSession()
    if not self.currentSession then
        return
    end

    local sessionId = self.currentSession.id

    -- Announce departure
    self.realtimeService:send({
        event = "collaborator.left",
        data = {
            sessionId = sessionId,
            userId = self.myUserId
        }
    })

    -- Unsubscribe from channels
    self.realtimeService:unsubscribe("collaboration-" .. sessionId)
    self.realtimeService:unsubscribe("presence-" .. sessionId)

    -- Clean up UI
    self:clearPresenceIndicators()

    self.currentSession = nil
    self.collaborators = {}
    self.operationHistory = {}
    self.pendingOperations = {}

    self.eventEmitter:emit("sessionLeft", sessionId)
    self.stateManager:setState("collaborationSession", nil)

    print("[CollaborationManager] Left session:", sessionId)
end

function CollaborationManager:broadcastOperation(operation: Operation)
    if not self.currentSession then
        return
    end

    -- Add to pending operations
    table.insert(self.pendingOperations, operation)

    -- Broadcast to other collaborators
    self.realtimeService:send({
        event = "operation.broadcast",
        channel = "collaboration-" .. self.currentSession.id,
        data = operation
    })

    -- Add to history
    table.insert(self.operationHistory, operation)

    -- Trim history if too long
    if #self.operationHistory > 1000 then
        table.remove(self.operationHistory, 1)
    end
end

function CollaborationManager:applyOperation(operation: Operation)
    -- Transform against pending operations
    for _, pendingOp in ipairs(self.pendingOperations) do
        operation = OperationalTransform.transform(operation, pendingOp)
    end

    -- Apply the operation
    local success, error = pcall(function()
        if operation.type == "insert" then
            self:applyInsert(operation)
        elseif operation.type == "delete" then
            self:applyDelete(operation)
        elseif operation.type == "modify" then
            self:applyModify(operation)
        elseif operation.type == "move" then
            self:applyMove(operation)
        end
    end)

    if success then
        -- Update version
        self.operationVersion = math.max(self.operationVersion, operation.version)

        -- Add to history
        table.insert(self.operationHistory, operation)

        self.eventEmitter:emit("operationApplied", operation)
    else
        warn("[CollaborationManager] Failed to apply operation:", error)

        -- Record conflict
        self:recordConflict(operation, error)
    end
end

function CollaborationManager:applyInsert(operation: Operation)
    -- Implementation for insert operation
    local parent = self:resolvePath(operation.path)
    if parent and operation.data then
        local instance = self:deserializeInstance(operation.data)
        if instance then
            instance.Parent = parent
        end
    end
end

function CollaborationManager:applyDelete(operation: Operation)
    -- Implementation for delete operation
    if operation.target and operation.target.Parent then
        operation.target:Destroy()
    end
end

function CollaborationManager:applyModify(operation: Operation)
    -- Implementation for modify operation
    if operation.target and operation.data then
        for property, value in pairs(operation.data) do
            pcall(function()
                operation.target[property] = value
            end)
        end
    end
end

function CollaborationManager:applyMove(operation: Operation)
    -- Implementation for move operation
    if operation.target and operation.data and operation.data.newParent then
        operation.target.Parent = operation.data.newParent
    end
end

function CollaborationManager:recordConflict(operation: Operation, error: string)
    local conflictId = HttpService:GenerateGUID(false)

    local conflict: Conflict = {
        id = conflictId,
        operations = {operation},
        resolution = "pending",
    }

    self.conflicts[conflictId] = conflict

    self.eventEmitter:emit("conflictDetected", {
        conflict = conflict,
        error = error
    })

    -- Attempt automatic resolution if configured
    if self.currentSession and self.currentSession.settings.conflictResolution == "automatic" then
        self:attemptAutomaticResolution(conflict)
    end
end

function CollaborationManager:attemptAutomaticResolution(conflict: Conflict)
    -- Simple last-write-wins strategy
    if #conflict.operations > 0 then
        local latestOp = conflict.operations[1]
        for _, op in ipairs(conflict.operations) do
            if op.timestamp > latestOp.timestamp then
                latestOp = op
            end
        end

        -- Retry applying the latest operation
        self:applyOperation(latestOp)

        conflict.resolution = "resolved"
        conflict.resolvedBy = "automatic"
        conflict.resolvedAt = os.time()

        self.eventEmitter:emit("conflictResolved", conflict)
    end
end

function CollaborationManager:broadcastPresence()
    if not self.currentSession then
        return
    end

    local selection = game:GetService("Selection"):Get()
    local camera = workspace.CurrentCamera

    local presence: PresenceUpdate = {
        userId = self.myUserId,
        selection = selection,
        timestamp = os.time(),
        viewport = camera and {
            camera = camera.CFrame,
            zoom = camera.FieldOfView
        } or nil
    }

    self.realtimeService:send({
        event = "presence.update",
        channel = "presence-" .. self.currentSession.id,
        data = presence
    })
end

function CollaborationManager:updateCollaboratorPresence(presence: PresenceUpdate)
    local collaborator = self.collaborators[presence.userId]
    if not collaborator then
        return
    end

    -- Update selection highlight
    self:updateSelectionHighlight(presence.userId, presence.selection)

    -- Update viewport indicator if applicable
    if presence.viewport then
        self:updateViewportIndicator(presence.userId, presence.viewport)
    end

    -- Update last activity
    collaborator.lastActivity = presence.timestamp
    collaborator.status = "active"

    self.eventEmitter:emit("presenceUpdated", presence)
end

function CollaborationManager:createPresenceIndicator(collaborator: CollaboratorInfo)
    -- Create visual indicator for collaborator
    local indicator = Instance.new("BillboardGui")
    indicator.Name = "Collaborator_" .. collaborator.userId
    indicator.Size = UDim2.new(0, 100, 0, 30)
    indicator.StudsOffset = Vector3.new(0, 3, 0)
    indicator.AlwaysOnTop = true

    local frame = Instance.new("Frame")
    frame.Size = UDim2.new(1, 0, 1, 0)
    frame.BackgroundColor3 = collaborator.color
    frame.BackgroundTransparency = 0.3
    frame.BorderSizePixel = 0
    frame.Parent = indicator

    local label = Instance.new("TextLabel")
    label.Size = UDim2.new(1, -4, 1, 0)
    label.Position = UDim2.new(0, 2, 0, 0)
    label.BackgroundTransparency = 1
    label.Text = collaborator.username
    label.TextColor3 = Color3.fromRGB(255, 255, 255)
    label.TextScaled = true
    label.Font = Enum.Font.SourceSansBold
    label.Parent = frame

    self.presenceIndicators[collaborator.userId] = indicator
end

function CollaborationManager:updateSelectionHighlight(userId: string, selection: {Instance}?)
    -- Clear existing highlight
    local existingHighlight = self.selectionHighlights[userId]
    if existingHighlight then
        for _, highlight in ipairs(existingHighlight) do
            highlight:Destroy()
        end
        self.selectionHighlights[userId] = nil
    end

    if not selection or #selection == 0 then
        return
    end

    -- Create new highlights
    local highlights = {}
    local collaborator = self.collaborators[userId]

    for _, instance in ipairs(selection) do
        if instance:IsA("BasePart") then
            local highlight = Instance.new("SelectionBox")
            highlight.Color3 = collaborator and collaborator.color or Color3.fromRGB(255, 255, 255)
            highlight.LineThickness = 0.05
            highlight.Transparency = 0.5
            highlight.Adornee = instance
            highlight.Parent = workspace

            table.insert(highlights, highlight)
        end
    end

    self.selectionHighlights[userId] = highlights
end

function CollaborationManager:updateViewportIndicator(userId: string, viewport: any)
    -- Update viewport frustum visualization
    -- This would show where other users are looking
end

function CollaborationManager:clearPresenceIndicators()
    for _, indicator in pairs(self.presenceIndicators) do
        indicator:Destroy()
    end
    self.presenceIndicators = {}

    for _, highlights in pairs(self.selectionHighlights) do
        for _, highlight in ipairs(highlights) do
            highlight:Destroy()
        end
    end
    self.selectionHighlights = {}
end

function CollaborationManager:setupRealtimeHandlers()
    -- Handle collaborator joined
    self.realtimeService:on("collaborator.joined", function(data)
        if data.sessionId == self.currentSession.id then
            self.collaborators[data.userInfo.userId] = data.userInfo
            self:createPresenceIndicator(data.userInfo)

            self.eventEmitter:emit("collaboratorJoined", data.userInfo)
        end
    end)

    -- Handle collaborator left
    self.realtimeService:on("collaborator.left", function(data)
        if data.sessionId == self.currentSession.id then
            local userId = data.userId

            -- Clean up presence
            if self.presenceIndicators[userId] then
                self.presenceIndicators[userId]:Destroy()
                self.presenceIndicators[userId] = nil
            end

            -- Clean up selection
            if self.selectionHighlights[userId] then
                for _, highlight in ipairs(self.selectionHighlights[userId]) do
                    highlight:Destroy()
                end
                self.selectionHighlights[userId] = nil
            end

            self.collaborators[userId] = nil

            self.eventEmitter:emit("collaboratorLeft", userId)
        end
    end)

    -- Handle operations
    self.realtimeService:on("operation.broadcast", function(operation: Operation)
        if operation.authorId ~= self.myUserId then
            self:applyOperation(operation)
        end
    end)

    -- Handle presence updates
    self.realtimeService:on("presence.update", function(presence: PresenceUpdate)
        if presence.userId ~= self.myUserId then
            self:updateCollaboratorPresence(presence)
        end
    end)
end

function CollaborationManager:startActivityMonitoring()
    -- Monitor local activity
    task.spawn(function()
        while true do
            task.wait(1)

            if self.currentSession then
                -- Check if idle
                local timeSinceActivity = os.time() - self.lastActivity
                local newStatus = "active"

                if timeSinceActivity > self.idleThreshold * 2 then
                    newStatus = "away"
                elseif timeSinceActivity > self.idleThreshold then
                    newStatus = "idle"
                end

                if self.myInfo and self.myInfo.status ~= newStatus then
                    self.myInfo.status = newStatus
                    self:broadcastStatusChange(newStatus)
                end

                -- Broadcast presence periodically
                if timeSinceActivity < self.idleThreshold then
                    self:broadcastPresence()
                end
            end
        end
    end)

    -- Track user interactions
    game:GetService("UserInputService").InputBegan:Connect(function()
        self.lastActivity = os.time()
    end)

    game:GetService("Selection").SelectionChanged:Connect(function()
        self.lastActivity = os.time()
        if self.currentSession then
            self:broadcastPresence()
        end
    end)
end

function CollaborationManager:broadcastStatusChange(status: string)
    if not self.currentSession then
        return
    end

    self.realtimeService:send({
        event = "status.changed",
        channel = "presence-" .. self.currentSession.id,
        data = {
            userId = self.myUserId,
            status = status
        }
    })
end

function CollaborationManager:createCollaborationUI()
    -- Create collaborator list UI
    local screenGui = Instance.new("ScreenGui")
    screenGui.Name = "CollaborationUI"
    screenGui.ResetOnSpawn = false
    screenGui.Parent = game:GetService("CoreGui")

    local frame = Instance.new("Frame")
    frame.Size = UDim2.new(0, 200, 0, 300)
    frame.Position = UDim2.new(1, -220, 0, 20)
    frame.BackgroundColor3 = Color3.fromRGB(30, 30, 30)
    frame.BorderSizePixel = 0
    frame.Parent = screenGui

    local title = Instance.new("TextLabel")
    title.Size = UDim2.new(1, 0, 0, 30)
    title.BackgroundColor3 = Color3.fromRGB(20, 20, 20)
    title.Text = "Collaborators"
    title.TextColor3 = Color3.fromRGB(255, 255, 255)
    title.TextScaled = true
    title.Font = Enum.Font.SourceSansBold
    title.Parent = frame

    local listFrame = Instance.new("ScrollingFrame")
    listFrame.Size = UDim2.new(1, 0, 1, -30)
    listFrame.Position = UDim2.new(0, 0, 0, 30)
    listFrame.BackgroundTransparency = 1
    listFrame.ScrollBarThickness = 6
    listFrame.Parent = frame

    self.collaboratorList = listFrame
    self.presenceOverlay = screenGui
end

function CollaborationManager:updateCollaboratorList()
    if not self.collaboratorList then
        return
    end

    -- Clear existing entries
    for _, child in ipairs(self.collaboratorList:GetChildren()) do
        child:Destroy()
    end

    -- Add collaborator entries
    local yPos = 0
    for userId, info in pairs(self.collaborators) do
        local entry = Instance.new("Frame")
        entry.Size = UDim2.new(1, -10, 0, 40)
        entry.Position = UDim2.new(0, 5, 0, yPos)
        entry.BackgroundColor3 = Color3.fromRGB(40, 40, 40)
        entry.Parent = self.collaboratorList

        -- Status indicator
        local statusDot = Instance.new("Frame")
        statusDot.Size = UDim2.new(0, 10, 0, 10)
        statusDot.Position = UDim2.new(0, 5, 0.5, -5)
        statusDot.BackgroundColor3 = info.status == "active" and Color3.fromRGB(0, 255, 0) or
                                     info.status == "idle" and Color3.fromRGB(255, 255, 0) or
                                     Color3.fromRGB(128, 128, 128)
        statusDot.Parent = entry

        -- Username
        local nameLabel = Instance.new("TextLabel")
        nameLabel.Size = UDim2.new(1, -25, 0.5, 0)
        nameLabel.Position = UDim2.new(0, 20, 0, 0)
        nameLabel.BackgroundTransparency = 1
        nameLabel.Text = info.username
        nameLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
        nameLabel.TextXAlignment = Enum.TextXAlignment.Left
        nameLabel.TextScaled = true
        nameLabel.Font = Enum.Font.SourceSans
        nameLabel.Parent = entry

        -- Activity
        local activityLabel = Instance.new("TextLabel")
        activityLabel.Size = UDim2.new(1, -25, 0.5, 0)
        activityLabel.Position = UDim2.new(0, 20, 0.5, 0)
        activityLabel.BackgroundTransparency = 1
        activityLabel.Text = "Active " .. self:formatTimestamp(info.lastActivity)
        activityLabel.TextColor3 = Color3.fromRGB(150, 150, 150)
        activityLabel.TextXAlignment = Enum.TextXAlignment.Left
        activityLabel.TextScaled = true
        activityLabel.Font = Enum.Font.SourceSans
        activityLabel.Parent = entry

        yPos = yPos + 45
    end

    self.collaboratorList.CanvasSize = UDim2.new(0, 0, 0, yPos)
end

function CollaborationManager:formatTimestamp(timestamp: number): string
    local diff = os.time() - timestamp
    if diff < 60 then
        return "now"
    elseif diff < 3600 then
        return math.floor(diff / 60) .. "m ago"
    elseif diff < 86400 then
        return math.floor(diff / 3600) .. "h ago"
    else
        return math.floor(diff / 86400) .. "d ago"
    end
end

function CollaborationManager:generateUserColor(userId: string): Color3
    -- Generate consistent color for user
    local hash = 0
    for i = 1, #userId do
        hash = (hash * 31 + string.byte(userId, i)) % 360
    end

    return Color3.fromHSV(hash / 360, 0.7, 0.9)
end

function CollaborationManager:resolvePath(path: string): Instance?
    -- Resolve a path string to an instance
    local parts = string.split(path, ".")
    local current = game

    for _, part in ipairs(parts) do
        current = current:FindFirstChild(part)
        if not current then
            return nil
        end
    end

    return current
end

function CollaborationManager:serializeInstance(instance: Instance): any
    -- Serialize instance for transmission
    return {
        ClassName = instance.ClassName,
        Name = instance.Name,
        Properties = {} -- Simplified
    }
end

function CollaborationManager:deserializeInstance(data: any): Instance?
    -- Deserialize instance data
    local success, instance = pcall(function()
        return Instance.new(data.ClassName)
    end)

    if success and instance then
        instance.Name = data.Name
        return instance
    end

    return nil
end

function CollaborationManager:getStatistics()
    return {
        sessionId = self.currentSession and self.currentSession.id,
        collaboratorCount = #self.collaborators,
        operationCount = #self.operationHistory,
        conflictCount = #self.conflicts,
        pendingOperations = #self.pendingOperations
    }
end

function CollaborationManager:cleanup()
    -- Leave session if active
    if self.currentSession then
        self:leaveSession()
    end

    -- Clean up UI
    if self.presenceOverlay then
        self.presenceOverlay:Destroy()
    end

    -- Clear all data
    self.collaborators = {}
    self.presenceIndicators = {}
    self.selectionHighlights = {}
    self.operationHistory = {}
    self.pendingOperations = {}
    self.conflicts = {}

    print("[CollaborationManager] Cleanup completed")
end

return CollaborationManager
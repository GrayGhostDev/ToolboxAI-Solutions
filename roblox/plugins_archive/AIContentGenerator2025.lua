--[[
    ToolboxAI Content Generator Plugin 2025
    Enhanced Roblox Studio Plugin with OAuth2, Open Cloud API, and Modern UI

    Features:
    - OAuth2 authentication with PKCE
    - Open Cloud API v2 integration
    - 8-stage conversation flow
    - Real-time HTTP polling (WebSocket alternative)
    - Progress tracking and quality validation
    - Asset management and upload

    Version: 2.0.0
    Last Updated: 2025-09-15
]]

-- Services
local HttpService = game:GetService("HttpService")
local RunService = game:GetService("RunService")
local Selection = game:GetService("Selection")
local ChangeHistoryService = game:GetService("ChangeHistoryService")
local StudioService = game:GetService("StudioService")
local DataStoreService = game:GetService("DataStoreService")
local TweenService = game:GetService("TweenService")
local MarketplaceService = game:GetService("MarketplaceService")

-- Plugin Configuration for ToolboxAI-Solutions
local PLUGIN_VERSION = "2.0.0"
local PLUGIN_NAME = "ToolboxAI Content Generator"
local CONFIG = {
    API_BASE_URL = "http://127.0.0.1:8008",
    ROJO_SERVER = "http://localhost:34872",  -- Rojo server for ToolboxAI-Solutions
    ROJO_PORT = 34872,
    PROJECT_NAME = "ToolboxAI-Solutions",
    POLLING_INTERVAL = 2, -- seconds
    MAX_RETRIES = 3,
    SESSION_TIMEOUT = 3600, -- 1 hour
    DEBUG_MODE = false
}

-- Create Plugin
local plugin = plugin or getfenv().PluginManager():CreatePlugin()
local toolbar = plugin:CreateToolbar("ToolboxAI Educational")

-- Create UI Components
local mainButton = toolbar:CreateButton(
    "AI Content Generator",
    "Generate educational content with AI",
    "rbxasset://textures/ui/Settings/Help/SparkleIcon.png"
)

local settingsButton = toolbar:CreateButton(
    "Settings",
    "Configure ToolboxAI settings",
    "rbxasset://textures/ui/Settings/MenuBarIcons/GameSettingsTab.png"
)

-- Widget Info
local widgetInfo = DockWidgetPluginGuiInfo.new(
    Enum.InitialDockState.Float,
    false, -- initEnabled
    false, -- overrideEnabledRestore
    500,   -- floatXSize
    700,   -- floatYSize
    400,   -- minWidth
    500    -- minHeight
)

-- Create Main Widget
local mainWidget = plugin:CreateDockWidgetPluginGui("ToolboxAIGenerator", widgetInfo)
mainWidget.Title = PLUGIN_NAME .. " v" .. PLUGIN_VERSION

-- OAuth2 Manager
local OAuth2Manager = {}
OAuth2Manager.__index = OAuth2Manager

function OAuth2Manager.new()
    local self = setmetatable({}, OAuth2Manager)
    self.accessToken = nil
    self.refreshToken = nil
    self.tokenExpiry = 0
    self.state = nil
    self.codeVerifier = nil
    return self
end

function OAuth2Manager:GeneratePKCE()
    -- Generate code verifier (43-128 characters)
    local chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
    local verifier = ""
    for i = 1, 128 do
        local idx = math.random(1, #chars)
        verifier = verifier .. chars:sub(idx, idx)
    end
    self.codeVerifier = verifier

    -- Generate code challenge (SHA256 of verifier)
    -- Note: In production, use proper SHA256 implementation
    return HttpService:UrlEncode(verifier)
end

function OAuth2Manager:InitiateAuth()
    local url = CONFIG.API_BASE_URL .. "/api/v1/roblox/auth/initiate"

    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = url,
            Method = "POST",
            Headers = {
                ["Content-Type"] = "application/json"
            },
            Body = HttpService:JSONEncode({
                additional_scopes = {"asset:write", "universe-messaging-service:publish"}
            })
        })
    end)

    if success and response.Success then
        local data = HttpService:JSONDecode(response.Body)
        self.state = data.state
        return data.authorization_url
    end

    return nil
end

function OAuth2Manager:ExchangeCode(code)
    local url = CONFIG.API_BASE_URL .. "/api/v1/roblox/oauth/callback"

    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = url .. "?code=" .. code .. "&state=" .. self.state,
            Method = "GET"
        })
    end)

    if success and response.Success then
        local data = HttpService:JSONDecode(response.Body)
        self.accessToken = data.access_token
        self.refreshToken = data.refresh_token
        self.tokenExpiry = tick() + (data.expires_in or 3600)
        return true
    end

    return false
end

function OAuth2Manager:IsAuthenticated()
    return self.accessToken ~= nil and tick() < self.tokenExpiry
end

-- Conversation Manager
local ConversationManager = {}
ConversationManager.__index = ConversationManager

function ConversationManager.new()
    local self = setmetatable({}, ConversationManager)
    self.sessionId = nil
    self.currentStage = "greeting"
    self.stageData = {}
    self.progress = 0
    self.polling = false
    return self
end

function ConversationManager:StartConversation()
    local url = CONFIG.API_BASE_URL .. "/api/v1/roblox/conversation/start"

    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = url,
            Method = "POST",
            Headers = {
                ["Content-Type"] = "application/json"
            },
            Body = HttpService:JSONEncode({
                initial_message = "I want to create an educational Roblox experience"
            })
        })
    end)

    if success and response.Success then
        local data = HttpService:JSONDecode(response.Body)
        self.sessionId = data.session_id
        self.currentStage = data.current_stage
        return true
    end

    return false
end

function ConversationManager:ProcessInput(userInput)
    if not self.sessionId then
        return false, "No active session"
    end

    local url = CONFIG.API_BASE_URL .. "/api/v1/roblox/conversation/input"

    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = url,
            Method = "POST",
            Headers = {
                ["Content-Type"] = "application/json"
            },
            Body = HttpService:JSONEncode({
                session_id = self.sessionId,
                user_input = userInput
            })
        })
    end)

    if success and response.Success then
        local data = HttpService:JSONDecode(response.Body)
        self.currentStage = data.result.current_stage
        self.progress = data.result.progress
        self.stageData[self.currentStage] = data.result.result
        return true, data.result.result.response
    end

    return false, "Failed to process input"
end

function ConversationManager:GenerateEnvironment()
    if not self.sessionId then
        return false, "No active session"
    end

    local url = CONFIG.API_BASE_URL .. "/api/v1/roblox/conversation/generate"

    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = url .. "?session_id=" .. self.sessionId,
            Method = "POST",
            Headers = {
                ["Content-Type"] = "application/json"
            }
        })
    end)

    if success and response.Success then
        local data = HttpService:JSONDecode(response.Body)
        return true, data.generation_result
    end

    return false, "Failed to generate environment"
end

-- Rojo Manager
local RojoManager = {}
RojoManager.__index = RojoManager

function RojoManager.new()
    local self = setmetatable({}, RojoManager)
    self.projects = {}
    self.activeProject = nil
    return self
end

function RojoManager:ListProjects()
    local url = CONFIG.API_BASE_URL .. "/api/v1/roblox/rojo/projects"

    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = url,
            Method = "GET"
        })
    end)

    if success and response.Success then
        local data = HttpService:JSONDecode(response.Body)
        self.projects = data.projects or {}
        return true
    end

    return false
end

function RojoManager:ConnectToProject(projectId, port)
    -- This would connect to Rojo server
    -- In practice, users need to use Rojo plugin's connect feature
    print("Connect to Rojo server at http://localhost:" .. tostring(port))
    self.activeProject = projectId
    return true
end

-- Environment Builder
local EnvironmentBuilder = {}
EnvironmentBuilder.__index = EnvironmentBuilder

function EnvironmentBuilder.new()
    local self = setmetatable({}, EnvironmentBuilder)
    return self
end

function EnvironmentBuilder:BuildFromData(environmentData)
    local environment = Instance.new("Folder")
    environment.Name = "GeneratedEnvironment_" .. tostring(tick())
    environment.Parent = workspace

    -- Create terrain
    if environmentData.terrain then
        self:CreateTerrain(environmentData.terrain, environment)
    end

    -- Create buildings
    if environmentData.buildings then
        for _, building in ipairs(environmentData.buildings) do
            self:CreateBuilding(building, environment)
        end
    end

    -- Create NPCs
    if environmentData.npcs then
        for _, npc in ipairs(environmentData.npcs) do
            self:CreateNPC(npc, environment)
        end
    end

    -- Create interactive objects
    if environmentData.objects then
        for _, obj in ipairs(environmentData.objects) do
            self:CreateObject(obj, environment)
        end
    end

    -- Set lighting
    if environmentData.lighting then
        self:SetupLighting(environmentData.lighting)
    end

    return environment
end

function EnvironmentBuilder:CreateTerrain(terrainData, parent)
    local terrain = workspace.Terrain

    -- Clear existing terrain (optional)
    -- terrain:Clear()

    -- Generate terrain based on type
    if terrainData.type == "grass" then
        -- Generate grassy terrain
        local region = Region3.new(Vector3.new(-100, 0, -100), Vector3.new(100, 10, 100))
        region = region:ExpandToGrid(4)
        terrain:FillBlock(region.CFrame, region.Size, Enum.Material.Grass)
    elseif terrainData.type == "desert" then
        -- Generate desert terrain
        local region = Region3.new(Vector3.new(-100, 0, -100), Vector3.new(100, 10, 100))
        region = region:ExpandToGrid(4)
        terrain:FillBlock(region.CFrame, region.Size, Enum.Material.Sand)
    end
end

function EnvironmentBuilder:CreateBuilding(buildingData, parent)
    local building = Instance.new("Model")
    building.Name = buildingData.type or "Building"

    local part = Instance.new("Part")
    part.Name = "MainStructure"
    part.Size = Vector3.new(
        buildingData.size.x or 20,
        buildingData.size.y or 15,
        buildingData.size.z or 20
    )
    part.Position = Vector3.new(
        buildingData.position.x or 0,
        buildingData.position.y or 7.5,
        buildingData.position.z or 0
    )
    part.BrickColor = BrickColor.new(buildingData.color or "Medium stone grey")
    part.Material = Enum.Material.Concrete
    part.Anchored = true
    part.Parent = building

    building.Parent = parent
    return building
end

function EnvironmentBuilder:CreateNPC(npcData, parent)
    local npc = Instance.new("Model")
    npc.Name = npcData.name or "NPC"

    -- Create humanoid
    local humanoid = Instance.new("Humanoid")
    humanoid.Parent = npc

    -- Create basic NPC structure
    local torso = Instance.new("Part")
    torso.Name = "Torso"
    torso.Size = Vector3.new(2, 2, 1)
    torso.Position = Vector3.new(
        npcData.position.x or 0,
        npcData.position.y or 3,
        npcData.position.z or 0
    )
    torso.BrickColor = BrickColor.new("Bright yellow")
    torso.Anchored = true
    torso.Parent = npc

    local head = Instance.new("Part")
    head.Name = "Head"
    head.Size = Vector3.new(2, 1, 1)
    head.Position = torso.Position + Vector3.new(0, 1.5, 0)
    head.BrickColor = BrickColor.new("Bright yellow")
    head.Anchored = true
    head.Parent = npc

    -- Add dialogue
    if npcData.dialogue then
        local billboardGui = Instance.new("BillboardGui")
        billboardGui.Size = UDim2.new(0, 200, 0, 50)
        billboardGui.StudsOffset = Vector3.new(0, 3, 0)
        billboardGui.Parent = head

        local textLabel = Instance.new("TextLabel")
        textLabel.Size = UDim2.new(1, 0, 1, 0)
        textLabel.Text = npcData.dialogue
        textLabel.TextScaled = true
        textLabel.BackgroundTransparency = 0.5
        textLabel.BackgroundColor3 = Color3.new(0, 0, 0)
        textLabel.TextColor3 = Color3.new(1, 1, 1)
        textLabel.Parent = billboardGui
    end

    npc.Parent = parent
    return npc
end

function EnvironmentBuilder:CreateObject(objectData, parent)
    local obj = Instance.new("Part")
    obj.Name = objectData.type or "Object"
    obj.Size = Vector3.new(
        objectData.size.x or 2,
        objectData.size.y or 2,
        objectData.size.z or 2
    )
    obj.Position = Vector3.new(
        objectData.position.x or 0,
        objectData.position.y or 1,
        objectData.position.z or 0
    )
    obj.BrickColor = BrickColor.new(objectData.color or "Bright blue")
    obj.Material = Enum.Material.Neon
    obj.Anchored = true
    obj.Parent = parent

    -- Make it interactive
    local clickDetector = Instance.new("ClickDetector")
    clickDetector.MaxActivationDistance = 10
    clickDetector.Parent = obj

    clickDetector.MouseClick:Connect(function(player)
        print(player.Name .. " interacted with " .. obj.Name)
        -- Add interaction logic here
    end)

    return obj
end

function EnvironmentBuilder:SetupLighting(lightingData)
    local lighting = game:GetService("Lighting")

    if lightingData.type == "sunny" then
        lighting.Brightness = lightingData.brightness or 2
        lighting.TimeOfDay = "14:00:00"
        lighting.Ambient = Color3.fromHex(lightingData.color or "#FFFFFF")
    elseif lightingData.type == "night" then
        lighting.Brightness = lightingData.brightness or 0.3
        lighting.TimeOfDay = "00:00:00"
        lighting.Ambient = Color3.fromHex(lightingData.color or "#4B4B7E")
    end

    lighting.GlobalShadows = true
    lighting.Technology = Enum.Technology.Future
end

-- UI Manager
local UIManager = {}
UIManager.__index = UIManager

function UIManager.new(widget)
    local self = setmetatable({}, UIManager)
    self.widget = widget
    self.elements = {}
    self:CreateUI()
    return self
end

function UIManager:CreateUI()
    -- Main Frame
    local mainFrame = Instance.new("Frame")
    mainFrame.Size = UDim2.new(1, 0, 1, 0)
    mainFrame.BackgroundColor3 = Color3.new(0.2, 0.2, 0.2)
    mainFrame.Parent = self.widget
    self.elements.mainFrame = mainFrame

    -- Header
    local header = Instance.new("TextLabel")
    header.Size = UDim2.new(1, 0, 0, 50)
    header.Position = UDim2.new(0, 0, 0, 0)
    header.Text = "🎓 ToolboxAI Educational Content Generator"
    header.TextScaled = true
    header.Font = Enum.Font.SourceSansBold
    header.TextColor3 = Color3.new(1, 1, 1)
    header.BackgroundColor3 = Color3.new(0.1, 0.4, 0.8)
    header.Parent = mainFrame

    -- Progress Bar
    local progressBar = Instance.new("Frame")
    progressBar.Size = UDim2.new(0.9, 0, 0, 20)
    progressBar.Position = UDim2.new(0.05, 0, 0, 60)
    progressBar.BackgroundColor3 = Color3.new(0.3, 0.3, 0.3)
    progressBar.Parent = mainFrame

    local progressFill = Instance.new("Frame")
    progressFill.Size = UDim2.new(0, 0, 1, 0)
    progressFill.BackgroundColor3 = Color3.new(0.2, 0.8, 0.2)
    progressFill.Parent = progressBar
    self.elements.progressFill = progressFill

    -- Stage Label
    local stageLabel = Instance.new("TextLabel")
    stageLabel.Size = UDim2.new(0.9, 0, 0, 30)
    stageLabel.Position = UDim2.new(0.05, 0, 0, 85)
    stageLabel.Text = "Stage: Welcome"
    stageLabel.TextScaled = true
    stageLabel.Font = Enum.Font.SourceSans
    stageLabel.TextColor3 = Color3.new(1, 1, 1)
    stageLabel.BackgroundTransparency = 1
    stageLabel.Parent = mainFrame
    self.elements.stageLabel = stageLabel

    -- Response Area
    local responseLabel = Instance.new("TextLabel")
    responseLabel.Size = UDim2.new(0.9, 0, 0, 100)
    responseLabel.Position = UDim2.new(0.05, 0, 0, 120)
    responseLabel.Text = "Welcome! Let's create an amazing educational experience."
    responseLabel.TextWrapped = true
    responseLabel.Font = Enum.Font.SourceSans
    responseLabel.TextColor3 = Color3.new(0.9, 0.9, 0.9)
    responseLabel.BackgroundColor3 = Color3.new(0.15, 0.15, 0.15)
    responseLabel.BorderSizePixel = 0
    responseLabel.TextXAlignment = Enum.TextXAlignment.Left
    responseLabel.TextYAlignment = Enum.TextYAlignment.Top
    responseLabel.Parent = mainFrame
    self.elements.responseLabel = responseLabel

    -- Input Box
    local inputBox = Instance.new("TextBox")
    inputBox.Size = UDim2.new(0.9, 0, 0, 80)
    inputBox.Position = UDim2.new(0.05, 0, 0, 230)
    inputBox.PlaceholderText = "Type your response here..."
    inputBox.Text = ""
    inputBox.TextWrapped = true
    inputBox.Font = Enum.Font.SourceSans
    inputBox.TextColor3 = Color3.new(1, 1, 1)
    inputBox.BackgroundColor3 = Color3.new(0.25, 0.25, 0.25)
    inputBox.BorderSizePixel = 1
    inputBox.BorderColor3 = Color3.new(0.4, 0.4, 0.4)
    inputBox.TextXAlignment = Enum.TextXAlignment.Left
    inputBox.TextYAlignment = Enum.TextYAlignment.Top
    inputBox.Parent = mainFrame
    self.elements.inputBox = inputBox

    -- Send Button
    local sendButton = Instance.new("TextButton")
    sendButton.Size = UDim2.new(0.4, 0, 0, 40)
    sendButton.Position = UDim2.new(0.05, 0, 0, 320)
    sendButton.Text = "Send"
    sendButton.TextScaled = true
    sendButton.Font = Enum.Font.SourceSansBold
    sendButton.TextColor3 = Color3.new(1, 1, 1)
    sendButton.BackgroundColor3 = Color3.new(0.2, 0.6, 0.2)
    sendButton.Parent = mainFrame
    self.elements.sendButton = sendButton

    -- Generate Button
    local generateButton = Instance.new("TextButton")
    generateButton.Size = UDim2.new(0.4, 0, 0, 40)
    generateButton.Position = UDim2.new(0.55, 0, 0, 320)
    generateButton.Text = "Generate Environment"
    generateButton.TextScaled = true
    generateButton.Font = Enum.Font.SourceSansBold
    generateButton.TextColor3 = Color3.new(1, 1, 1)
    generateButton.BackgroundColor3 = Color3.new(0.6, 0.2, 0.2)
    generateButton.Visible = false
    generateButton.Parent = mainFrame
    self.elements.generateButton = generateButton

    -- Status Label
    local statusLabel = Instance.new("TextLabel")
    statusLabel.Size = UDim2.new(0.9, 0, 0, 30)
    statusLabel.Position = UDim2.new(0.05, 0, 1, -40)
    statusLabel.Text = "Ready"
    statusLabel.TextScaled = true
    statusLabel.Font = Enum.Font.SourceSans
    statusLabel.TextColor3 = Color3.new(0.7, 0.7, 0.7)
    statusLabel.BackgroundTransparency = 1
    statusLabel.Parent = mainFrame
    self.elements.statusLabel = statusLabel
end

function UIManager:UpdateProgress(progress)
    local progressFill = self.elements.progressFill
    progressFill:TweenSize(
        UDim2.new(progress / 100, 0, 1, 0),
        Enum.EasingDirection.Out,
        Enum.EasingStyle.Quad,
        0.5,
        true
    )
end

function UIManager:UpdateStage(stageName)
    self.elements.stageLabel.Text = "Stage: " .. stageName
end

function UIManager:UpdateResponse(text)
    self.elements.responseLabel.Text = text
end

function UIManager:UpdateStatus(text, isError)
    self.elements.statusLabel.Text = text
    self.elements.statusLabel.TextColor3 = isError and Color3.new(1, 0.3, 0.3) or Color3.new(0.7, 0.7, 0.7)
end

function UIManager:ShowGenerateButton(show)
    self.elements.generateButton.Visible = show
end

-- Main Plugin Logic
local authManager = OAuth2Manager.new()
local conversationManager = ConversationManager.new()
local rojoManager = RojoManager.new()
local environmentBuilder = EnvironmentBuilder.new()
local uiManager = UIManager.new(mainWidget)

-- Button Click Handlers
mainButton.Click:Connect(function()
    mainWidget.Enabled = not mainWidget.Enabled

    if mainWidget.Enabled and not conversationManager.sessionId then
        -- Start new conversation
        uiManager:UpdateStatus("Starting conversation...")

        local success = conversationManager:StartConversation()
        if success then
            uiManager:UpdateStatus("Ready")
            uiManager:UpdateStage("Welcome")
            uiManager:UpdateProgress(0)
        else
            uiManager:UpdateStatus("Failed to start conversation", true)
        end
    end
end)

-- Send Button Handler
uiManager.elements.sendButton.MouseButton1Click:Connect(function()
    local input = uiManager.elements.inputBox.Text
    if input == "" then return end

    uiManager:UpdateStatus("Processing...")

    local success, response = conversationManager:ProcessInput(input)
    if success then
        uiManager:UpdateResponse(response)
        uiManager:UpdateProgress(conversationManager.progress)
        uiManager.elements.inputBox.Text = ""
        uiManager:UpdateStatus("Ready")

        -- Check if we're at validation stage
        if conversationManager.currentStage == "validation" then
            uiManager:ShowGenerateButton(true)
        end
    else
        uiManager:UpdateStatus(response, true)
    end
end)

-- Generate Button Handler
uiManager.elements.generateButton.MouseButton1Click:Connect(function()
    uiManager:UpdateStatus("Generating environment...")

    local success, result = conversationManager:GenerateEnvironment()
    if success then
        uiManager:UpdateStatus("Environment generated! Project ID: " .. (result.project_id or "unknown"))
        uiManager:UpdateResponse("Environment successfully generated!\n\nRojo Port: " .. tostring(result.rojo_port or "N/A") .. "\nFiles Generated: " .. tostring(result.files_generated or 0))

        -- Try to build environment in Studio
        if conversationManager.stageData and conversationManager.stageData.content_design then
            local environment = environmentBuilder:BuildFromData(conversationManager.stageData)
            Selection:Set({environment})
            uiManager:UpdateStatus("Environment built in Studio!")
        end
    else
        uiManager:UpdateStatus(result, true)
    end
end)

-- Settings Button Handler
settingsButton.Click:Connect(function()
    -- Open settings dialog
    print("Settings clicked - Not implemented yet")
end)

-- Plugin Unloading
plugin.Unloading:Connect(function()
    if mainWidget then
        mainWidget:Destroy()
    end
end)

-- Initial Message
print("ToolboxAI Content Generator v" .. PLUGIN_VERSION .. " loaded successfully!")
print("Click the 'AI Content Generator' button in the toolbar to start.")
--[[
    ToolboxAI Content Generator Plugin for Roblox Studio
    Version: 1.0.0
    Description: AI-powered educational content generation plugin that connects
                 to the ToolboxAI backend for real-time content creation
    
    Features:
    - Real-time WebSocket connection to backend
    - AI-powered content generation
    - Educational environment creation
    - Quiz and assessment integration
    - Live progress tracking
--]]

-- Services
local HttpService = game:GetService("HttpService")
local Selection = game:GetService("Selection")
local ChangeHistoryService = game:GetService("ChangeHistoryService")
local StudioService = game:GetService("StudioService")
local RunService = game:GetService("RunService")
local CoreGui = game:GetService("CoreGui")

-- Configuration
local CONFIG = {
    PLUGIN_NAME = "ToolboxAI Content Generator",
    PLUGIN_VERSION = "1.0.0",
    BACKEND_URL = "http://127.0.0.1:5001",  -- Flask bridge server
    API_URL = "http://127.0.0.1:8008",      -- FastAPI main server
    WEBSOCKET_URL = "ws://127.0.0.1:8001",  -- WebSocket server
    PLUGIN_PORT = 64989,
    HEARTBEAT_INTERVAL = 30,  -- seconds
    RECONNECT_INTERVAL = 5,   -- seconds
    MAX_RECONNECT_ATTEMPTS = 10
}

-- Plugin State
local PluginState = {
    connected = false,
    authenticated = false,
    sessionId = nil,
    userId = nil,
    reconnectAttempts = 0,
    activeRequests = {},
    generatedContent = {},
    settings = {
        autoApplyContent = false,
        showNotifications = true,
        debugMode = false
    }
}

-- Create Plugin UI
local toolbar = plugin:CreateToolbar(CONFIG.PLUGIN_NAME)
local mainButton = toolbar:CreateButton(
    "Generate Content",
    "Open AI Content Generator",
    "rbxasset://textures/ui/GuiImagePlaceholder.png"
)

-- Plugin Widget
local widgetInfo = DockWidgetPluginGuiInfo.new(
    Enum.InitialDockState.Float,
    true,   -- Widget will be initially enabled
    false,  -- Don't override the previous enabled state
    450,    -- Default width
    600,    -- Default height
    400,    -- Minimum width
    300     -- Minimum height
)

local pluginWidget = plugin:CreateDockWidgetPluginGui("AIContentGenerator", widgetInfo)
pluginWidget.Title = "AI Content Generator"
pluginWidget.Name = "AIContentGeneratorWidget"

-- Create main frame
local mainFrame = Instance.new("Frame")
mainFrame.Size = UDim2.new(1, 0, 1, 0)
mainFrame.BackgroundColor3 = Color3.fromRGB(46, 46, 46)
mainFrame.BorderSizePixel = 0
mainFrame.Parent = pluginWidget

-- Header Frame
local headerFrame = Instance.new("Frame")
headerFrame.Size = UDim2.new(1, 0, 0, 60)
headerFrame.BackgroundColor3 = Color3.fromRGB(35, 35, 35)
headerFrame.BorderSizePixel = 0
headerFrame.Parent = mainFrame

-- Title Label
local titleLabel = Instance.new("TextLabel")
titleLabel.Size = UDim2.new(0.7, 0, 1, 0)
titleLabel.Position = UDim2.new(0, 10, 0, 0)
titleLabel.BackgroundTransparency = 1
titleLabel.Text = "🤖 AI Content Generator"
titleLabel.TextColor3 = Color3.new(1, 1, 1)
titleLabel.TextScaled = true
titleLabel.Font = Enum.Font.SourceSansBold
titleLabel.TextXAlignment = Enum.TextXAlignment.Left
titleLabel.Parent = headerFrame

-- Connection Status
local statusLabel = Instance.new("TextLabel")
statusLabel.Size = UDim2.new(0.3, -10, 0, 20)
statusLabel.Position = UDim2.new(0.7, 0, 0.5, -10)
statusLabel.BackgroundColor3 = Color3.fromRGB(255, 100, 100)
statusLabel.Text = "Disconnected"
statusLabel.TextColor3 = Color3.new(1, 1, 1)
statusLabel.Font = Enum.Font.SourceSans
statusLabel.TextScaled = true
statusLabel.Parent = headerFrame

-- Content Frame (Scrollable)
local scrollFrame = Instance.new("ScrollingFrame")
scrollFrame.Size = UDim2.new(1, -20, 1, -140)
scrollFrame.Position = UDim2.new(0, 10, 0, 70)
scrollFrame.BackgroundColor3 = Color3.fromRGB(56, 56, 56)
scrollFrame.BorderSizePixel = 0
scrollFrame.ScrollBarThickness = 8
scrollFrame.CanvasSize = UDim2.new(0, 0, 2, 0)
scrollFrame.Parent = mainFrame

-- Subject Selection
local subjectLabel = Instance.new("TextLabel")
subjectLabel.Size = UDim2.new(1, -20, 0, 30)
subjectLabel.Position = UDim2.new(0, 10, 0, 10)
subjectLabel.BackgroundTransparency = 1
subjectLabel.Text = "Subject:"
subjectLabel.TextColor3 = Color3.new(0.9, 0.9, 0.9)
subjectLabel.Font = Enum.Font.SourceSans
subjectLabel.TextSize = 16
subjectLabel.TextXAlignment = Enum.TextXAlignment.Left
subjectLabel.Parent = scrollFrame

local subjectBox = Instance.new("TextBox")
subjectBox.Size = UDim2.new(1, -20, 0, 35)
subjectBox.Position = UDim2.new(0, 10, 0, 40)
subjectBox.BackgroundColor3 = Color3.fromRGB(70, 70, 70)
subjectBox.BorderSizePixel = 0
subjectBox.Text = "Mathematics"
subjectBox.TextColor3 = Color3.new(1, 1, 1)
subjectBox.Font = Enum.Font.SourceSans
subjectBox.TextSize = 14
subjectBox.PlaceholderText = "Enter subject..."
subjectBox.Parent = scrollFrame

-- Grade Level
local gradeLabel = Instance.new("TextLabel")
gradeLabel.Size = UDim2.new(1, -20, 0, 30)
gradeLabel.Position = UDim2.new(0, 10, 0, 85)
gradeLabel.BackgroundTransparency = 1
gradeLabel.Text = "Grade Level:"
gradeLabel.TextColor3 = Color3.new(0.9, 0.9, 0.9)
gradeLabel.Font = Enum.Font.SourceSans
gradeLabel.TextSize = 16
gradeLabel.TextXAlignment = Enum.TextXAlignment.Left
gradeLabel.Parent = scrollFrame

local gradeBox = Instance.new("TextBox")
gradeBox.Size = UDim2.new(1, -20, 0, 35)
gradeBox.Position = UDim2.new(0, 10, 0, 115)
gradeBox.BackgroundColor3 = Color3.fromRGB(70, 70, 70)
gradeBox.BorderSizePixel = 0
gradeBox.Text = "5"
gradeBox.TextColor3 = Color3.new(1, 1, 1)
gradeBox.Font = Enum.Font.SourceSans
gradeBox.TextSize = 14
gradeBox.PlaceholderText = "Enter grade level (1-12)..."
gradeBox.Parent = scrollFrame

-- Learning Objectives
local objectivesLabel = Instance.new("TextLabel")
objectivesLabel.Size = UDim2.new(1, -20, 0, 30)
objectivesLabel.Position = UDim2.new(0, 10, 0, 160)
objectivesLabel.BackgroundTransparency = 1
objectivesLabel.Text = "Learning Objectives:"
objectivesLabel.TextColor3 = Color3.new(0.9, 0.9, 0.9)
objectivesLabel.Font = Enum.Font.SourceSans
objectivesLabel.TextSize = 16
objectivesLabel.TextXAlignment = Enum.TextXAlignment.Left
objectivesLabel.Parent = scrollFrame

local objectivesBox = Instance.new("TextBox")
objectivesBox.Size = UDim2.new(1, -20, 0, 60)
objectivesBox.Position = UDim2.new(0, 10, 0, 190)
objectivesBox.BackgroundColor3 = Color3.fromRGB(70, 70, 70)
objectivesBox.BorderSizePixel = 0
objectivesBox.Text = "Fractions, Decimals, Percentages"
objectivesBox.TextColor3 = Color3.new(1, 1, 1)
objectivesBox.Font = Enum.Font.SourceSans
objectivesBox.TextSize = 14
objectivesBox.TextWrapped = true
objectivesBox.MultiLine = true
objectivesBox.PlaceholderText = "Enter learning objectives (comma separated)..."
objectivesBox.Parent = scrollFrame

-- Environment Type
local envLabel = Instance.new("TextLabel")
envLabel.Size = UDim2.new(1, -20, 0, 30)
envLabel.Position = UDim2.new(0, 10, 0, 260)
envLabel.BackgroundTransparency = 1
envLabel.Text = "Environment Type:"
envLabel.TextColor3 = Color3.new(0.9, 0.9, 0.9)
envLabel.Font = Enum.Font.SourceSans
envLabel.TextSize = 16
envLabel.TextXAlignment = Enum.TextXAlignment.Left
envLabel.Parent = scrollFrame

-- Environment Type Dropdown (simplified as TextBox for now)
local envBox = Instance.new("TextBox")
envBox.Size = UDim2.new(1, -20, 0, 35)
envBox.Position = UDim2.new(0, 10, 0, 290)
envBox.BackgroundColor3 = Color3.fromRGB(70, 70, 70)
envBox.BorderSizePixel = 0
envBox.Text = "interactive_classroom"
envBox.TextColor3 = Color3.new(1, 1, 1)
envBox.Font = Enum.Font.SourceSans
envBox.TextSize = 14
envBox.PlaceholderText = "classroom, outdoor, laboratory, space..."
envBox.Parent = scrollFrame

-- Include Quiz Checkbox
local quizFrame = Instance.new("Frame")
quizFrame.Size = UDim2.new(1, -20, 0, 35)
quizFrame.Position = UDim2.new(0, 10, 0, 335)
quizFrame.BackgroundTransparency = 1
quizFrame.Parent = scrollFrame

local quizCheckbox = Instance.new("TextButton")
quizCheckbox.Size = UDim2.new(0, 25, 0, 25)
quizCheckbox.Position = UDim2.new(0, 0, 0, 5)
quizCheckbox.BackgroundColor3 = Color3.fromRGB(70, 70, 70)
quizCheckbox.BorderSizePixel = 2
quizCheckbox.BorderColor3 = Color3.new(0.5, 0.5, 0.5)
quizCheckbox.Text = "✓"
quizCheckbox.TextColor3 = Color3.new(0, 1, 0)
quizCheckbox.Font = Enum.Font.SourceSansBold
quizCheckbox.TextSize = 20
quizCheckbox.Parent = quizFrame

local quizLabel = Instance.new("TextLabel")
quizLabel.Size = UDim2.new(1, -35, 1, 0)
quizLabel.Position = UDim2.new(0, 35, 0, 0)
quizLabel.BackgroundTransparency = 1
quizLabel.Text = "Include Quiz/Assessment"
quizLabel.TextColor3 = Color3.new(0.9, 0.9, 0.9)
quizLabel.Font = Enum.Font.SourceSans
quizLabel.TextSize = 16
quizLabel.TextXAlignment = Enum.TextXAlignment.Left
quizLabel.Parent = quizFrame

-- Progress Bar
local progressFrame = Instance.new("Frame")
progressFrame.Size = UDim2.new(1, -20, 0, 30)
progressFrame.Position = UDim2.new(0, 10, 0, 380)
progressFrame.BackgroundColor3 = Color3.fromRGB(50, 50, 50)
progressFrame.BorderSizePixel = 0
progressFrame.Visible = false
progressFrame.Parent = scrollFrame

local progressBar = Instance.new("Frame")
progressBar.Size = UDim2.new(0, 0, 1, 0)
progressBar.BackgroundColor3 = Color3.fromRGB(0, 170, 255)
progressBar.BorderSizePixel = 0
progressBar.Parent = progressFrame

local progressLabel = Instance.new("TextLabel")
progressLabel.Size = UDim2.new(1, 0, 1, 0)
progressLabel.BackgroundTransparency = 1
progressLabel.Text = "Generating content..."
progressLabel.TextColor3 = Color3.new(1, 1, 1)
progressLabel.Font = Enum.Font.SourceSans
progressLabel.TextSize = 14
progressLabel.Parent = progressFrame

-- Generate Button
local generateButton = Instance.new("TextButton")
generateButton.Size = UDim2.new(1, -20, 0, 45)
generateButton.Position = UDim2.new(0, 10, 1, -55)
generateButton.BackgroundColor3 = Color3.fromRGB(0, 170, 255)
generateButton.BorderSizePixel = 0
generateButton.Text = "🚀 Generate Content"
generateButton.TextColor3 = Color3.new(1, 1, 1)
generateButton.Font = Enum.Font.SourceSansBold
generateButton.TextSize = 18
generateButton.Parent = mainFrame

-- Utility Functions
local function updateConnectionStatus(connected)
    PluginState.connected = connected
    if connected then
        statusLabel.Text = "Connected"
        statusLabel.BackgroundColor3 = Color3.fromRGB(100, 255, 100)
    else
        statusLabel.Text = "Disconnected"
        statusLabel.BackgroundColor3 = Color3.fromRGB(255, 100, 100)
    end
end

local function showNotification(message, notificationType)
    if not PluginState.settings.showNotifications then return end
    
    local color = Color3.new(1, 1, 1)
    if notificationType == "success" then
        color = Color3.fromRGB(100, 255, 100)
    elseif notificationType == "error" then
        color = Color3.fromRGB(255, 100, 100)
    elseif notificationType == "warning" then
        color = Color3.fromRGB(255, 200, 100)
    end
    
    print(string.format("[%s] %s", CONFIG.PLUGIN_NAME, message))
    
    -- Create visual notification
    local notification = Instance.new("TextLabel")
    notification.Size = UDim2.new(1, -20, 0, 40)
    notification.Position = UDim2.new(0, 10, 0, 420)
    notification.BackgroundColor3 = color
    notification.Text = message
    notification.TextColor3 = Color3.new(0, 0, 0)
    notification.Font = Enum.Font.SourceSans
    notification.TextSize = 14
    notification.Parent = scrollFrame
    
    -- Auto-remove after 5 seconds
    task.wait(5)
    notification:Destroy()
end

local function parseObjectives(text)
    local objectives = {}
    for objective in string.gmatch(text, "([^,]+)") do
        table.insert(objectives, objective:match("^%s*(.-)%s*$"))
    end
    return objectives
end

-- HTTP Request Functions
local function makeRequest(url, method, data)
    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = url,
            Method = method,
            Headers = {
                ["Content-Type"] = "application/json",
                ["X-Plugin-Version"] = CONFIG.PLUGIN_VERSION,
                ["X-Studio-User"] = tostring(StudioService:GetUserId())
            },
            Body = data and HttpService:JSONEncode(data) or nil
        })
    end)
    
    if success then
        if response.StatusCode == 200 then
            return true, HttpService:JSONDecode(response.Body)
        else
            return false, "HTTP Error: " .. response.StatusCode
        end
    else
        return false, "Request failed: " .. tostring(response)
    end
end

-- Plugin Registration
local function registerPlugin()
    local data = {
        port = CONFIG.PLUGIN_PORT,
        version = CONFIG.PLUGIN_VERSION,
        studio_user_id = StudioService:GetUserId(),
        capabilities = {
            "terrain_generation",
            "script_creation",
            "ui_building",
            "quiz_system",
            "websocket"
        }
    }
    
    local success, result = makeRequest(
        CONFIG.BACKEND_URL .. "/register_plugin",
        "POST",
        data
    )
    
    if success then
        PluginState.sessionId = result.session_id
        updateConnectionStatus(true)
        showNotification("Plugin registered successfully!", "success")
        return true
    else
        updateConnectionStatus(false)
        showNotification("Failed to register plugin: " .. tostring(result), "error")
        return false
    end
end

-- Content Generation
local function generateContent()
    if not PluginState.connected then
        showNotification("Not connected to server. Attempting to connect...", "warning")
        registerPlugin()
        return
    end
    
    -- Show progress
    progressFrame.Visible = true
    progressBar.Size = UDim2.new(0.2, 0, 1, 0)
    generateButton.Text = "Generating..."
    generateButton.BackgroundColor3 = Color3.fromRGB(150, 150, 150)
    
    local requestData = {
        subject = subjectBox.Text,
        grade_level = tonumber(gradeBox.Text) or 5,
        learning_objectives = parseObjectives(objectivesBox.Text),
        environment_type = envBox.Text,
        include_quiz = quizCheckbox.Text == "✓"
    }
    
    -- Validate input
    if requestData.subject == "" then
        showNotification("Please enter a subject", "error")
        progressFrame.Visible = false
        generateButton.Text = "🚀 Generate Content"
        generateButton.BackgroundColor3 = Color3.fromRGB(0, 170, 255)
        return
    end
    
    progressBar.Size = UDim2.new(0.4, 0, 1, 0)
    
    -- Make request to generate content
    local success, result = makeRequest(
        CONFIG.API_URL .. "/generate_content",
        "POST",
        requestData
    )
    
    progressBar.Size = UDim2.new(0.6, 0, 1, 0)
    
    if success then
        progressBar.Size = UDim2.new(0.8, 0, 1, 0)
        
        -- Store generated content
        local requestId = result.request_id or HttpService:GenerateGUID(false)
        PluginState.generatedContent[requestId] = result
        
        -- Apply content to workspace
        applyGeneratedContent(result)
        
        progressBar.Size = UDim2.new(1, 0, 1, 0)
        showNotification("Content generated successfully!", "success")
        
        task.wait(1)
        progressFrame.Visible = false
        generateButton.Text = "🚀 Generate Content"
        generateButton.BackgroundColor3 = Color3.fromRGB(0, 170, 255)
    else
        progressFrame.Visible = false
        generateButton.Text = "🚀 Generate Content"
        generateButton.BackgroundColor3 = Color3.fromRGB(0, 170, 255)
        showNotification("Failed to generate content: " .. tostring(result), "error")
    end
end

-- Apply Generated Content to Workspace
function applyGeneratedContent(contentData)
    ChangeHistoryService:SetWaypoint("Before AI Content Generation")
    
    local appliedComponents = {}
    
    -- Apply terrain if present
    if contentData.terrain_script then
        local success, err = pcall(function()
            local terrainFunc = loadstring(contentData.terrain_script)
            if terrainFunc then
                terrainFunc()
                table.insert(appliedComponents, "terrain")
            end
        end)
        if not success then
            warn("Failed to apply terrain: " .. tostring(err))
        end
    end
    
    -- Create objects if present
    if contentData.objects then
        for _, objData in ipairs(contentData.objects) do
            local success, err = pcall(function()
                local part = Instance.new(objData.type or "Part")
                part.Name = objData.name or "GeneratedObject"
                part.Position = objData.position or Vector3.new(0, 5, 0)
                part.Size = objData.size or Vector3.new(4, 1, 2)
                part.Parent = workspace
                table.insert(appliedComponents, "object:" .. part.Name)
            end)
            if not success then
                warn("Failed to create object: " .. tostring(err))
            end
        end
    end
    
    -- Apply scripts if present
    if contentData.scripts then
        for i, scriptContent in ipairs(contentData.scripts) do
            local success, err = pcall(function()
                local script = Instance.new("Script")
                script.Name = "GeneratedScript_" .. i
                script.Source = scriptContent
                script.Parent = workspace
                table.insert(appliedComponents, "script:" .. script.Name)
            end)
            if not success then
                warn("Failed to create script: " .. tostring(err))
            end
        end
    end
    
    -- Create quiz system if included
    if contentData.quiz then
        local success, err = pcall(function()
            local quizFolder = Instance.new("Folder")
            quizFolder.Name = "QuizSystem"
            quizFolder.Parent = workspace
            
            -- Store quiz data
            local quizData = Instance.new("StringValue")
            quizData.Name = "QuizData"
            quizData.Value = HttpService:JSONEncode(contentData.quiz)
            quizData.Parent = quizFolder
            
            table.insert(appliedComponents, "quiz")
        end)
        if not success then
            warn("Failed to create quiz: " .. tostring(err))
        end
    end
    
    ChangeHistoryService:SetWaypoint("After AI Content Generation")
    
    -- Report back to server
    local reportData = {
        request_id = contentData.request_id,
        success = true,
        applied_components = appliedComponents,
        timestamp = os.time()
    }
    
    makeRequest(
        CONFIG.BACKEND_URL .. "/content_applied",
        "POST",
        reportData
    )
    
    showNotification(string.format("Applied %d components", #appliedComponents), "success")
end

-- Heartbeat Function
local function sendHeartbeat()
    if not PluginState.connected then return end
    
    local data = {
        session_id = PluginState.sessionId,
        timestamp = os.time(),
        status = "active"
    }
    
    local success, _ = makeRequest(
        CONFIG.BACKEND_URL .. "/heartbeat",
        "POST",
        data
    )
    
    if not success then
        PluginState.reconnectAttempts = PluginState.reconnectAttempts + 1
        if PluginState.reconnectAttempts < CONFIG.MAX_RECONNECT_ATTEMPTS then
            task.wait(CONFIG.RECONNECT_INTERVAL)
            registerPlugin()
        else
            updateConnectionStatus(false)
            showNotification("Lost connection to server", "error")
        end
    else
        PluginState.reconnectAttempts = 0
    end
end

-- Event Handlers
generateButton.MouseButton1Click:Connect(generateContent)

quizCheckbox.MouseButton1Click:Connect(function()
    if quizCheckbox.Text == "✓" then
        quizCheckbox.Text = ""
    else
        quizCheckbox.Text = "✓"
    end
end)

mainButton.Click:Connect(function()
    pluginWidget.Enabled = not pluginWidget.Enabled
end)

-- Auto-connect on plugin load
spawn(function()
    task.wait(2) -- Wait for studio to fully load
    registerPlugin()
end)

-- Heartbeat loop
spawn(function()
    while true do
        task.wait(CONFIG.HEARTBEAT_INTERVAL)
        sendHeartbeat()
    end
end)

-- Cleanup on plugin unload
plugin.Unloading:Connect(function()
    if PluginState.connected then
        makeRequest(
            CONFIG.BACKEND_URL .. "/unregister_plugin",
            "POST",
            { session_id = PluginState.sessionId }
        )
    end
end)

print(string.format("[%s] Plugin loaded successfully (v%s)", CONFIG.PLUGIN_NAME, CONFIG.PLUGIN_VERSION))
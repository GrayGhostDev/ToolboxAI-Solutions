--!strict
--[[
    ToolboxAI Integration Plugin for Roblox Studio
    Provides UI to interact with Flask Bridge server for AI-powered content generation
]]

-- Services
local Selection = game:GetService("Selection")
local ChangeHistoryService = game:GetService("ChangeHistoryService")
local StudioService = game:GetService("StudioService")
local HttpService = game:GetService("HttpService")
local ServerScriptService = game:GetService("ServerScriptService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local StarterPlayer = game:GetService("StarterPlayer")

-- Create toolbar and button
local toolbar = plugin:CreateToolbar("ToolboxAI Integration")
local mainButton = toolbar:CreateButton(
    "ToolboxAI Assistant",
    "AI-powered content generation and optimization",
    "rbxasset://textures/ui/common/robux.png"
)

-- Plugin configuration
local FLASK_BRIDGE_URL = "http://127.0.0.1:5001"

-- Widget creation
local widgetInfo = DockWidgetPluginGuiInfo.new(
    Enum.InitialDockState.Float,
    false,  -- Enabled
    false,  -- Override previous state
    400,    -- Default width
    600,    -- Default height
    400,    -- Min width
    300     -- Min height
)

local widget = plugin:CreateDockWidgetPluginGui("ToolboxAI_Assistant", widgetInfo)
widget.Title = "ToolboxAI Assistant"

-- Create UI
local screenGui = Instance.new("Frame")
screenGui.Size = UDim2.new(1, 0, 1, 0)
screenGui.BackgroundColor3 = Color3.fromRGB(40, 40, 40)
screenGui.BorderSizePixel = 0
screenGui.Parent = widget

-- Header
local header = Instance.new("Frame")
header.Size = UDim2.new(1, 0, 0, 50)
header.BackgroundColor3 = Color3.fromRGB(60, 60, 60)
header.BorderSizePixel = 0
header.Parent = screenGui

local titleLabel = Instance.new("TextLabel")
titleLabel.Size = UDim2.new(1, -20, 1, 0)
titleLabel.Position = UDim2.new(0, 10, 0, 0)
titleLabel.BackgroundTransparency = 1
titleLabel.Text = "ToolboxAI Content Assistant"
titleLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
titleLabel.TextScaled = true
titleLabel.Font = Enum.Font.SourceSansBold
titleLabel.Parent = header

-- Tab container
local tabContainer = Instance.new("Frame")
tabContainer.Size = UDim2.new(1, 0, 0, 40)
tabContainer.Position = UDim2.new(0, 0, 0, 50)
tabContainer.BackgroundColor3 = Color3.fromRGB(50, 50, 50)
tabContainer.BorderSizePixel = 0
tabContainer.Parent = screenGui

-- Content area
local contentArea = Instance.new("ScrollingFrame")
contentArea.Size = UDim2.new(1, -20, 1, -110)
contentArea.Position = UDim2.new(0, 10, 0, 100)
contentArea.BackgroundColor3 = Color3.fromRGB(30, 30, 30)
contentArea.BorderSizePixel = 0
contentArea.ScrollBarThickness = 8
contentArea.Parent = screenGui

-- Status bar
local statusBar = Instance.new("Frame")
statusBar.Size = UDim2.new(1, 0, 0, 20)
statusBar.Position = UDim2.new(0, 0, 1, -20)
statusBar.BackgroundColor3 = Color3.fromRGB(20, 20, 20)
statusBar.BorderSizePixel = 0
statusBar.Parent = screenGui

local statusLabel = Instance.new("TextLabel")
statusLabel.Size = UDim2.new(1, -10, 1, 0)
statusLabel.Position = UDim2.new(0, 5, 0, 0)
statusLabel.BackgroundTransparency = 1
statusLabel.Text = "Ready"
statusLabel.TextColor3 = Color3.fromRGB(0, 255, 0)
statusLabel.TextScaled = true
statusLabel.Font = Enum.Font.SourceSans
statusLabel.TextXAlignment = Enum.TextXAlignment.Left
statusLabel.Parent = statusBar

-- Tabs
local tabs = {
    {name = "Generate", content = nil},
    {name = "Optimize", content = nil},
    {name = "Security", content = nil},
    {name = "Educational", content = nil}
}

local tabButtons = {}
local currentTab = 1

-- Create tab buttons
for i, tab in ipairs(tabs) do
    local button = Instance.new("TextButton")
    button.Size = UDim2.new(0.25, -2, 1, -4)
    button.Position = UDim2.new((i-1) * 0.25, 1, 0, 2)
    button.BackgroundColor3 = i == 1 and Color3.fromRGB(70, 70, 70) or Color3.fromRGB(50, 50, 50)
    button.BorderSizePixel = 0
    button.Text = tab.name
    button.TextColor3 = Color3.fromRGB(255, 255, 255)
    button.Font = Enum.Font.SourceSans
    button.Parent = tabContainer

    tabButtons[i] = button

    button.MouseButton1Click:Connect(function()
        -- Update tab appearance
        for j, btn in ipairs(tabButtons) do
            btn.BackgroundColor3 = j == i and Color3.fromRGB(70, 70, 70) or Color3.fromRGB(50, 50, 50)
        end

        -- Show tab content
        for j, t in ipairs(tabs) do
            if t.content then
                t.content.Visible = j == i
            end
        end

        currentTab = i
    end)
end

-- Helper function: Create input field
local function createInputField(parent, label, yPos, multiline)
    local container = Instance.new("Frame")
    container.Size = UDim2.new(1, -20, 0, multiline and 120 or 60)
    container.Position = UDim2.new(0, 10, 0, yPos)
    container.BackgroundTransparency = 1
    container.Parent = parent

    local labelText = Instance.new("TextLabel")
    labelText.Size = UDim2.new(1, 0, 0, 20)
    labelText.BackgroundTransparency = 1
    labelText.Text = label
    labelText.TextColor3 = Color3.fromRGB(200, 200, 200)
    labelText.TextXAlignment = Enum.TextXAlignment.Left
    labelText.Font = Enum.Font.SourceSans
    labelText.Parent = container

    local textBox = Instance.new("TextBox")
    textBox.Size = UDim2.new(1, 0, multiline and 0.7 or 0.5, 0)
    textBox.Position = UDim2.new(0, 0, 0.3, 0)
    textBox.BackgroundColor3 = Color3.fromRGB(60, 60, 60)
    textBox.BorderSizePixel = 0
    textBox.Text = ""
    textBox.TextColor3 = Color3.fromRGB(255, 255, 255)
    textBox.Font = Enum.Font.SourceSans
    textBox.ClearTextOnFocus = false
    textBox.MultiLine = multiline or false
    textBox.TextWrapped = multiline or false
    textBox.Parent = container

    return textBox
end

-- Helper function: Create button
local function createButton(parent, text, yPos, callback)
    local button = Instance.new("TextButton")
    button.Size = UDim2.new(0.5, -20, 0, 40)
    button.Position = UDim2.new(0.25, 10, 0, yPos)
    button.BackgroundColor3 = Color3.fromRGB(0, 120, 215)
    button.BorderSizePixel = 0
    button.Text = text
    button.TextColor3 = Color3.fromRGB(255, 255, 255)
    button.Font = Enum.Font.SourceSansBold
    button.Parent = parent

    button.MouseButton1Click:Connect(callback)

    return button
end

-- Create Generate tab content
local generateContent = Instance.new("Frame")
generateContent.Size = UDim2.new(1, 0, 1, 0)
generateContent.BackgroundTransparency = 1
generateContent.Parent = contentArea
tabs[1].content = generateContent

local scriptTypeDropdown = Instance.new("Frame")
scriptTypeDropdown.Size = UDim2.new(1, -20, 0, 60)
scriptTypeDropdown.Position = UDim2.new(0, 10, 0, 10)
scriptTypeDropdown.BackgroundTransparency = 1
scriptTypeDropdown.Parent = generateContent

local scriptTypeLabel = Instance.new("TextLabel")
scriptTypeLabel.Size = UDim2.new(1, 0, 0, 20)
scriptTypeLabel.BackgroundTransparency = 1
scriptTypeLabel.Text = "Script Type:"
scriptTypeLabel.TextColor3 = Color3.fromRGB(200, 200, 200)
scriptTypeLabel.TextXAlignment = Enum.TextXAlignment.Left
scriptTypeLabel.Font = Enum.Font.SourceSans
scriptTypeLabel.Parent = scriptTypeDropdown

local scriptTypes = {"ServerScript", "LocalScript", "ModuleScript"}
local selectedScriptType = scriptTypes[1]

local scriptTypeButton = Instance.new("TextButton")
scriptTypeButton.Size = UDim2.new(1, 0, 0, 30)
scriptTypeButton.Position = UDim2.new(0, 0, 0, 25)
scriptTypeButton.BackgroundColor3 = Color3.fromRGB(60, 60, 60)
scriptTypeButton.BorderSizePixel = 0
scriptTypeButton.Text = selectedScriptType
scriptTypeButton.TextColor3 = Color3.fromRGB(255, 255, 255)
scriptTypeButton.Font = Enum.Font.SourceSans
scriptTypeButton.Parent = scriptTypeDropdown

local requirementsInput = createInputField(generateContent, "Requirements:", 80, true)
local educationalFocusInput = createInputField(generateContent, "Educational Focus (optional):", 210, false)

createButton(generateContent, "Generate Script", 280, function()
    statusLabel.Text = "Generating script..."
    statusLabel.TextColor3 = Color3.fromRGB(255, 255, 0)

    -- Make request to Flask Bridge
    local requestData = {
        script_type = selectedScriptType,
        requirements = requirementsInput.Text,
        educational_focus = educationalFocusInput.Text
    }

    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = FLASK_BRIDGE_URL .. "/roblox/generate_script",
            Method = "POST",
            Headers = {["Content-Type"] = "application/json"},
            Body = HttpService:JSONEncode(requestData)
        })
    end)

    if success and response.Success then
        local data = HttpService:JSONDecode(response.Body)

        if data.success and data.script then
            -- Create the script in workspace
            local newScript
            if selectedScriptType == "ServerScript" then
                newScript = Instance.new("Script")
                newScript.Parent = ServerScriptService
            elseif selectedScriptType == "LocalScript" then
                newScript = Instance.new("LocalScript")
                newScript.Parent = StarterPlayer.StarterPlayerScripts
            else
                newScript = Instance.new("ModuleScript")
                newScript.Parent = ReplicatedStorage
            end

            newScript.Name = "AI_Generated_" .. os.time()
            newScript.Source = data.script

            -- Select the new script
            Selection:Set({newScript})

            statusLabel.Text = "Script generated successfully!"
            statusLabel.TextColor3 = Color3.fromRGB(0, 255, 0)

            -- Record action for undo
            ChangeHistoryService:SetWaypoint("Generated AI Script")
        else
            statusLabel.Text = "Generation failed: " .. (data.message or "Unknown error")
            statusLabel.TextColor3 = Color3.fromRGB(255, 0, 0)
        end
    else
        statusLabel.Text = "Request failed: Check Flask Bridge connection"
        statusLabel.TextColor3 = Color3.fromRGB(255, 0, 0)
    end
end)

-- Create Optimize tab content
local optimizeContent = Instance.new("Frame")
optimizeContent.Size = UDim2.new(1, 0, 1, 0)
optimizeContent.BackgroundTransparency = 1
optimizeContent.Visible = false
optimizeContent.Parent = contentArea
tabs[2].content = optimizeContent

local optimizeInstructions = Instance.new("TextLabel")
optimizeInstructions.Size = UDim2.new(1, -20, 0, 40)
optimizeInstructions.Position = UDim2.new(0, 10, 0, 10)
optimizeInstructions.BackgroundTransparency = 1
optimizeInstructions.Text = "Select a script in the Explorer, then click Optimize"
optimizeInstructions.TextColor3 = Color3.fromRGB(200, 200, 200)
optimizeInstructions.TextWrapped = true
optimizeInstructions.Font = Enum.Font.SourceSans
optimizeInstructions.Parent = optimizeContent

createButton(optimizeContent, "Optimize Selected Script", 60, function()
    local selected = Selection:Get()
    if #selected == 0 then
        statusLabel.Text = "Please select a script"
        statusLabel.TextColor3 = Color3.fromRGB(255, 0, 0)
        return
    end

    local script = selected[1]
    if not (script:IsA("Script") or script:IsA("LocalScript") or script:IsA("ModuleScript")) then
        statusLabel.Text = "Please select a Script, LocalScript, or ModuleScript"
        statusLabel.TextColor3 = Color3.fromRGB(255, 0, 0)
        return
    end

    statusLabel.Text = "Optimizing script..."
    statusLabel.TextColor3 = Color3.fromRGB(255, 255, 0)

    local requestData = {
        script = script.Source,
        optimization_level = "balanced"
    }

    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = FLASK_BRIDGE_URL .. "/roblox/optimize_script",
            Method = "POST",
            Headers = {["Content-Type"] = "application/json"},
            Body = HttpService:JSONEncode(requestData)
        })
    end)

    if success and response.Success then
        local data = HttpService:JSONDecode(response.Body)

        if data.success and data.optimized_script then
            -- Update the script
            script.Source = data.optimized_script

            statusLabel.Text = "Script optimized successfully!"
            statusLabel.TextColor3 = Color3.fromRGB(0, 255, 0)

            -- Record action for undo
            ChangeHistoryService:SetWaypoint("Optimized Script")
        else
            statusLabel.Text = "Optimization failed: " .. (data.message or "Unknown error")
            statusLabel.TextColor3 = Color3.fromRGB(255, 0, 0)
        end
    else
        statusLabel.Text = "Request failed: Check Flask Bridge connection"
        statusLabel.TextColor3 = Color3.fromRGB(255, 0, 0)
    end
end)

-- Create Security tab content
local securityContent = Instance.new("Frame")
securityContent.Size = UDim2.new(1, 0, 1, 0)
securityContent.BackgroundTransparency = 1
securityContent.Visible = false
securityContent.Parent = contentArea
tabs[3].content = securityContent

local securityInstructions = Instance.new("TextLabel")
securityInstructions.Size = UDim2.new(1, -20, 0, 40)
securityInstructions.Position = UDim2.new(0, 10, 0, 10)
securityInstructions.BackgroundTransparency = 1
securityInstructions.Text = "Select scripts to validate for security issues"
securityInstructions.TextColor3 = Color3.fromRGB(200, 200, 200)
securityInstructions.TextWrapped = true
securityInstructions.Font = Enum.Font.SourceSans
securityInstructions.Parent = securityContent

local securityReport = Instance.new("TextLabel")
securityReport.Size = UDim2.new(1, -20, 0, 300)
securityReport.Position = UDim2.new(0, 10, 0, 110)
securityReport.BackgroundColor3 = Color3.fromRGB(40, 40, 40)
securityReport.BorderSizePixel = 0
securityReport.Text = "Security report will appear here"
securityReport.TextColor3 = Color3.fromRGB(180, 180, 180)
securityReport.TextWrapped = true
securityReport.TextYAlignment = Enum.TextYAlignment.Top
securityReport.Font = Enum.Font.Code
securityReport.Parent = securityContent

createButton(securityContent, "Validate Security", 60, function()
    local selected = Selection:Get()
    if #selected == 0 then
        statusLabel.Text = "Please select a script"
        statusLabel.TextColor3 = Color3.fromRGB(255, 0, 0)
        return
    end

    local script = selected[1]
    if not (script:IsA("Script") or script:IsA("LocalScript") or script:IsA("ModuleScript")) then
        statusLabel.Text = "Please select a Script, LocalScript, or ModuleScript"
        statusLabel.TextColor3 = Color3.fromRGB(255, 0, 0)
        return
    end

    statusLabel.Text = "Validating security..."
    statusLabel.TextColor3 = Color3.fromRGB(255, 255, 0)

    local scriptType = "ServerScript"
    if script:IsA("LocalScript") then
        scriptType = "LocalScript"
    elseif script:IsA("ModuleScript") then
        scriptType = "ModuleScript"
    end

    local requestData = {
        script = script.Source,
        script_type = scriptType,
        strict_mode = true
    }

    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = FLASK_BRIDGE_URL .. "/roblox/validate_security",
            Method = "POST",
            Headers = {["Content-Type"] = "application/json"},
            Body = HttpService:JSONEncode(requestData)
        })
    end)

    if success and response.Success then
        local data = HttpService:JSONDecode(response.Body)

        if data.success then
            local report = "Security Validation Report\n"
            report = report .. "========================\n\n"
            report = report .. "Risk Score: " .. tostring(data.risk_score or 0) .. "/10\n\n"

            if data.vulnerabilities and #data.vulnerabilities > 0 then
                report = report .. "Vulnerabilities Found:\n"
                for _, vuln in ipairs(data.vulnerabilities) do
                    report = report .. "- " .. (vuln.description or "Unknown") .. "\n"
                end
            else
                report = report .. "No vulnerabilities found!\n"
            end

            if data.recommendations and #data.recommendations > 0 then
                report = report .. "\nRecommendations:\n"
                for _, rec in ipairs(data.recommendations) do
                    report = report .. "- " .. rec .. "\n"
                end
            end

            securityReport.Text = report

            local riskScore = data.risk_score or 0
            if riskScore <= 3 then
                statusLabel.Text = "Security check passed (Low risk)"
                statusLabel.TextColor3 = Color3.fromRGB(0, 255, 0)
            elseif riskScore <= 7 then
                statusLabel.Text = "Security check: Medium risk"
                statusLabel.TextColor3 = Color3.fromRGB(255, 255, 0)
            else
                statusLabel.Text = "Security check: High risk!"
                statusLabel.TextColor3 = Color3.fromRGB(255, 0, 0)
            end
        else
            statusLabel.Text = "Validation failed: " .. (data.message or "Unknown error")
            statusLabel.TextColor3 = Color3.fromRGB(255, 0, 0)
        end
    else
        statusLabel.Text = "Request failed: Check Flask Bridge connection"
        statusLabel.TextColor3 = Color3.fromRGB(255, 0, 0)
    end
end)

-- Create Educational tab content
local educationalContent = Instance.new("Frame")
educationalContent.Size = UDim2.new(1, 0, 1, 0)
educationalContent.BackgroundTransparency = 1
educationalContent.Visible = false
educationalContent.Parent = contentArea
tabs[4].content = educationalContent

local subjectInput = createInputField(educationalContent, "Subject:", 10, false)
local gradeLevelInput = createInputField(educationalContent, "Grade Level (elementary/middle/high):", 80, false)
local formatInput = createInputField(educationalContent, "Format (interactive/tutorial/challenge):", 150, false)

createButton(educationalContent, "Generate Educational Content", 220, function()
    statusLabel.Text = "Generating educational content..."
    statusLabel.TextColor3 = Color3.fromRGB(255, 255, 0)

    local requestData = {
        subject = subjectInput.Text,
        grade_level = gradeLevelInput.Text,
        format = formatInput.Text
    }

    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = FLASK_BRIDGE_URL .. "/roblox/educational_content",
            Method = "POST",
            Headers = {["Content-Type"] = "application/json"},
            Body = HttpService:JSONEncode(requestData)
        })
    end)

    if success and response.Success then
        local data = HttpService:JSONDecode(response.Body)

        if data.success and data.content then
            statusLabel.Text = "Educational content generated!"
            statusLabel.TextColor3 = Color3.fromRGB(0, 255, 0)

            -- Create a folder for the educational content
            local folder = Instance.new("Folder")
            folder.Name = "Educational_" .. subjectInput.Text .. "_" .. os.time()
            folder.Parent = ServerScriptService

            -- Add a ModuleScript with the content data
            local dataModule = Instance.new("ModuleScript")
            dataModule.Name = "ContentData"
            dataModule.Source = "return " .. HttpService:JSONEncode(data.content)
            dataModule.Parent = folder

            -- Select the folder
            Selection:Set({folder})

            -- Record action for undo
            ChangeHistoryService:SetWaypoint("Generated Educational Content")
        else
            statusLabel.Text = "Generation failed: " .. (data.message or "Unknown error")
            statusLabel.TextColor3 = Color3.fromRGB(255, 0, 0)
        end
    else
        statusLabel.Text = "Request failed: Check Flask Bridge connection"
        statusLabel.TextColor3 = Color3.fromRGB(255, 0, 0)
    end
end)

-- Widget toggle
mainButton.Click:Connect(function()
    widget.Enabled = not widget.Enabled
end)

-- Initial health check
task.spawn(function()
    task.wait(1)
    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = FLASK_BRIDGE_URL .. "/health",
            Method = "GET"
        })
    end)

    if success and response.Success then
        statusLabel.Text = "Connected to Flask Bridge"
        statusLabel.TextColor3 = Color3.fromRGB(0, 255, 0)
    else
        statusLabel.Text = "Flask Bridge not responding"
        statusLabel.TextColor3 = Color3.fromRGB(255, 0, 0)
    end
end)

print("ToolboxAI Integration Plugin loaded successfully!")
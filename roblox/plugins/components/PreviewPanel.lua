--!strict
--[[
    Preview Panel Component
    Real-time preview of generated content with 3D visualization
]]

local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Debris = game:GetService("Debris")
local Lighting = game:GetService("Lighting")
local CollectionService = game:GetService("CollectionService")

-- Types
type PreviewContent = {
    type: string,
    name: string,
    description: string,
    script: string?,
    model: Model?,
    part: Part?,
    gui: ScreenGui?,
    sound: Sound?,
    properties: {[string]: any}?,
    children: {PreviewContent}?,
    metadata: {[string]: any}?
}

type ViewportSettings = {
    cameraDistance: number,
    cameraAngle: Vector3,
    lightingPreset: string,
    backgroundColor: Color3,
    showGrid: boolean,
    autoRotate: boolean,
    rotationSpeed: number
}

-- Preview Panel Class
local PreviewPanel = {}
PreviewPanel.__index = PreviewPanel

function PreviewPanel.new(parent: Frame, stateManager: any, eventEmitter: any)
    local self = setmetatable({}, PreviewPanel)

    self.parent = parent
    self.stateManager = stateManager
    self.eventEmitter = eventEmitter

    self.currentContent = nil
    self.viewport = nil
    self.viewportCamera = nil
    self.previewModel = nil
    self.connections = {}
    self.isRotating = false
    self.rotationAngle = 0

    self.viewportSettings: ViewportSettings = {
        cameraDistance = 20,
        cameraAngle = Vector3.new(-30, 45, 0),
        lightingPreset = "Realistic",
        backgroundColor = Color3.fromRGB(30, 30, 30),
        showGrid = true,
        autoRotate = true,
        rotationSpeed = 0.5
    }

    self.ui = {}

    -- Initialize UI
    self:createUI()

    -- Setup event handlers
    self:setupEventHandlers()

    -- Start render loop
    self:startRenderLoop()

    return self
end

function PreviewPanel:createUI()
    -- Main container
    local container = Instance.new("Frame")
    container.Size = UDim2.new(1, -20, 1, -20)
    container.Position = UDim2.new(0, 10, 0, 10)
    container.BackgroundColor3 = Color3.fromRGB(40, 40, 40)
    container.BorderSizePixel = 0
    container.Parent = self.parent
    self.ui.container = container

    -- Header with title and controls
    local header = Instance.new("Frame")
    header.Size = UDim2.new(1, 0, 0, 40)
    header.BackgroundColor3 = Color3.fromRGB(50, 50, 50)
    header.BorderSizePixel = 0
    header.Parent = container

    local title = Instance.new("TextLabel")
    title.Size = UDim2.new(0.5, -10, 1, 0)
    title.Position = UDim2.new(0, 10, 0, 0)
    title.BackgroundTransparency = 1
    title.Text = "Content Preview"
    title.TextColor3 = Color3.fromRGB(255, 255, 255)
    title.TextXAlignment = Enum.TextXAlignment.Left
    title.Font = Enum.Font.SourceSansBold
    title.TextScaled = true
    title.Parent = header
    self.ui.title = title

    -- Control buttons container
    local controls = Instance.new("Frame")
    controls.Size = UDim2.new(0.5, -10, 1, 0)
    controls.Position = UDim2.new(0.5, 0, 0, 0)
    controls.BackgroundTransparency = 1
    controls.Parent = header

    -- View mode buttons
    local viewModeButtons = {
        {name = "3D", icon = "🎮"},
        {name = "Code", icon = "📝"},
        {name = "Properties", icon = "⚙️"},
        {name = "Hierarchy", icon = "🌳"}
    }

    for i, buttonInfo in ipairs(viewModeButtons) do
        local button = Instance.new("TextButton")
        button.Size = UDim2.new(0.25, -5, 0, 30)
        button.Position = UDim2.new((i - 1) * 0.25, (i - 1) * 5, 0, 5)
        button.BackgroundColor3 = i == 1 and Color3.fromRGB(0, 162, 255) or Color3.fromRGB(60, 60, 60)
        button.Text = buttonInfo.icon .. " " .. buttonInfo.name
        button.TextColor3 = Color3.fromRGB(255, 255, 255)
        button.Font = Enum.Font.SourceSans
        button.TextScaled = true
        button.Parent = controls

        button.MouseButton1Click:Connect(function()
            self:switchViewMode(buttonInfo.name, button, controls)
        end)

        if buttonInfo.name == "3D" then
            self.ui.active3DButton = button
        end
    end

    -- Content area
    local contentArea = Instance.new("Frame")
    contentArea.Size = UDim2.new(1, 0, 1, -100)
    contentArea.Position = UDim2.new(0, 0, 0, 40)
    contentArea.BackgroundColor3 = Color3.fromRGB(30, 30, 30)
    contentArea.BorderSizePixel = 0
    contentArea.Parent = container
    self.ui.contentArea = contentArea

    -- Create viewport for 3D preview
    self:create3DViewport()

    -- Create code editor view
    self:createCodeView()

    -- Create properties panel
    self:createPropertiesView()

    -- Create hierarchy view
    self:createHierarchyView()

    -- Bottom toolbar
    local toolbar = Instance.new("Frame")
    toolbar.Size = UDim2.new(1, 0, 0, 60)
    toolbar.Position = UDim2.new(0, 0, 1, -60)
    toolbar.BackgroundColor3 = Color3.fromRGB(50, 50, 50)
    toolbar.BorderSizePixel = 0
    toolbar.Parent = container

    -- Zoom controls
    local zoomFrame = Instance.new("Frame")
    zoomFrame.Size = UDim2.new(0, 200, 0, 40)
    zoomFrame.Position = UDim2.new(0, 10, 0, 10)
    zoomFrame.BackgroundTransparency = 1
    zoomFrame.Parent = toolbar

    local zoomLabel = Instance.new("TextLabel")
    zoomLabel.Size = UDim2.new(0, 50, 1, 0)
    zoomLabel.BackgroundTransparency = 1
    zoomLabel.Text = "Zoom:"
    zoomLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
    zoomLabel.Font = Enum.Font.SourceSans
    zoomLabel.TextScaled = true
    zoomLabel.Parent = zoomFrame

    local zoomSlider = Instance.new("Frame")
    zoomSlider.Size = UDim2.new(1, -60, 0, 4)
    zoomSlider.Position = UDim2.new(0, 55, 0.5, -2)
    zoomSlider.BackgroundColor3 = Color3.fromRGB(60, 60, 60)
    zoomSlider.Parent = zoomFrame

    local zoomHandle = Instance.new("Frame")
    zoomHandle.Size = UDim2.new(0, 20, 0, 20)
    zoomHandle.Position = UDim2.new(0.5, -10, 0.5, -10)
    zoomHandle.BackgroundColor3 = Color3.fromRGB(0, 162, 255)
    zoomHandle.Parent = zoomSlider
    self.ui.zoomHandle = zoomHandle

    -- Action buttons
    local actionButtons = {
        {text = "Apply", position = UDim2.new(1, -220, 0, 10), color = Color3.fromRGB(0, 162, 255)},
        {text = "Export", position = UDim2.new(1, -110, 0, 10), color = Color3.fromRGB(60, 60, 60)}
    }

    for _, buttonInfo in ipairs(actionButtons) do
        local button = Instance.new("TextButton")
        button.Size = UDim2.new(0, 100, 0, 40)
        button.Position = buttonInfo.position
        button.BackgroundColor3 = buttonInfo.color
        button.Text = buttonInfo.text
        button.TextColor3 = Color3.fromRGB(255, 255, 255)
        button.Font = Enum.Font.SourceSans
        button.TextScaled = true
        button.Parent = toolbar

        button.MouseButton1Click:Connect(function()
            self:handleAction(buttonInfo.text)
        end)
    end

    -- Settings button
    local settingsButton = Instance.new("TextButton")
    settingsButton.Size = UDim2.new(0, 40, 0, 40)
    settingsButton.Position = UDim2.new(0.5, -20, 0, 10)
    settingsButton.BackgroundColor3 = Color3.fromRGB(60, 60, 60)
    settingsButton.Text = "⚙️"
    settingsButton.TextColor3 = Color3.fromRGB(255, 255, 255)
    settingsButton.Font = Enum.Font.SourceSans
    settingsButton.TextScaled = true
    settingsButton.Parent = toolbar

    settingsButton.MouseButton1Click:Connect(function()
        self:toggleSettings()
    end)
end

function PreviewPanel:create3DViewport()
    -- Create viewport frame
    local viewport = Instance.new("ViewportFrame")
    viewport.Size = UDim2.new(1, -20, 1, -20)
    viewport.Position = UDim2.new(0, 10, 0, 10)
    viewport.BackgroundColor3 = self.viewportSettings.backgroundColor
    viewport.BorderSizePixel = 1
    viewport.BorderColor3 = Color3.fromRGB(60, 60, 60)
    viewport.Parent = self.ui.contentArea
    viewport.CurrentCamera = nil
    self.viewport = viewport

    -- Create camera
    local camera = Instance.new("Camera")
    camera.CameraType = Enum.CameraType.Scriptable
    camera.FieldOfView = 70
    camera.Parent = viewport
    viewport.CurrentCamera = camera
    self.viewportCamera = camera

    -- Create base platform
    if self.viewportSettings.showGrid then
        local platform = Instance.new("Part")
        platform.Name = "PreviewPlatform"
        platform.Size = Vector3.new(50, 0.5, 50)
        platform.Position = Vector3.new(0, -5, 0)
        platform.Material = Enum.Material.SmoothPlastic
        platform.BrickColor = BrickColor.new("Dark grey")
        platform.TopSurface = Enum.SurfaceType.Smooth
        platform.BottomSurface = Enum.SurfaceType.Smooth
        platform.Anchored = true
        platform.CanCollide = false
        platform.Parent = viewport

        -- Add grid texture
        local texture = Instance.new("Texture")
        texture.Texture = "rbxasset://textures/ui/GridDefault.png"
        texture.Face = Enum.NormalId.Top
        texture.StudsPerTileU = 5
        texture.StudsPerTileV = 5
        texture.Transparency = 0.8
        texture.Parent = platform
    end

    -- Add lighting
    local light = Instance.new("PointLight")
    light.Brightness = 2
    light.Range = 60
    light.Parent = camera

    -- Set initial camera position
    self:updateCameraPosition()

    -- Hide by default (3D view is shown initially)
    self.ui.viewport3D = viewport
end

function PreviewPanel:createCodeView()
    -- Code editor container
    local codeContainer = Instance.new("ScrollingFrame")
    codeContainer.Size = UDim2.new(1, -20, 1, -20)
    codeContainer.Position = UDim2.new(0, 10, 0, 10)
    codeContainer.BackgroundColor3 = Color3.fromRGB(20, 20, 20)
    codeContainer.BorderSizePixel = 1
    codeContainer.BorderColor3 = Color3.fromRGB(60, 60, 60)
    codeContainer.ScrollBarThickness = 10
    codeContainer.Visible = false
    codeContainer.Parent = self.ui.contentArea
    self.ui.codeContainer = codeContainer

    -- Syntax highlighting colors
    local syntaxColors = {
        keyword = Color3.fromRGB(86, 156, 214),
        string = Color3.fromRGB(206, 145, 120),
        comment = Color3.fromRGB(106, 153, 85),
        number = Color3.fromRGB(181, 206, 168),
        operator = Color3.fromRGB(212, 212, 212),
        default = Color3.fromRGB(156, 220, 254)
    }

    -- Code display with line numbers
    local lineNumberFrame = Instance.new("Frame")
    lineNumberFrame.Size = UDim2.new(0, 50, 1, 0)
    lineNumberFrame.BackgroundColor3 = Color3.fromRGB(15, 15, 15)
    lineNumberFrame.BorderSizePixel = 0
    lineNumberFrame.Parent = codeContainer
    self.ui.lineNumberFrame = lineNumberFrame

    -- Code text
    local codeText = Instance.new("TextLabel")
    codeText.Size = UDim2.new(1, -60, 0, 1000)
    codeText.Position = UDim2.new(0, 55, 0, 0)
    codeText.BackgroundTransparency = 1
    codeText.Text = "-- No code to display"
    codeText.TextColor3 = syntaxColors.default
    codeText.Font = Enum.Font.Code
    codeText.TextXAlignment = Enum.TextXAlignment.Left
    codeText.TextYAlignment = Enum.TextYAlignment.Top
    codeText.TextSize = 14
    codeText.RichText = true
    codeText.Parent = codeContainer
    self.ui.codeText = codeText
end

function PreviewPanel:createPropertiesView()
    -- Properties container
    local propertiesContainer = Instance.new("ScrollingFrame")
    propertiesContainer.Size = UDim2.new(1, -20, 1, -20)
    propertiesContainer.Position = UDim2.new(0, 10, 0, 10)
    propertiesContainer.BackgroundColor3 = Color3.fromRGB(30, 30, 30)
    propertiesContainer.BorderSizePixel = 1
    propertiesContainer.BorderColor3 = Color3.fromRGB(60, 60, 60)
    propertiesContainer.ScrollBarThickness = 10
    propertiesContainer.Visible = false
    propertiesContainer.Parent = self.ui.contentArea
    self.ui.propertiesContainer = propertiesContainer

    -- Property list will be populated dynamically
    self.ui.propertyFrames = {}
end

function PreviewPanel:createHierarchyView()
    -- Hierarchy container
    local hierarchyContainer = Instance.new("ScrollingFrame")
    hierarchyContainer.Size = UDim2.new(1, -20, 1, -20)
    hierarchyContainer.Position = UDim2.new(0, 10, 0, 10)
    hierarchyContainer.BackgroundColor3 = Color3.fromRGB(30, 30, 30)
    hierarchyContainer.BorderSizePixel = 1
    hierarchyContainer.BorderColor3 = Color3.fromRGB(60, 60, 60)
    hierarchyContainer.ScrollBarThickness = 10
    hierarchyContainer.Visible = false
    hierarchyContainer.Parent = self.ui.contentArea
    self.ui.hierarchyContainer = hierarchyContainer

    -- Tree view will be populated dynamically
    self.ui.hierarchyNodes = {}
end

function PreviewPanel:switchViewMode(mode: string, button: TextButton, parent: Frame)
    -- Reset all buttons
    for _, child in ipairs(parent:GetChildren()) do
        if child:IsA("TextButton") then
            child.BackgroundColor3 = Color3.fromRGB(60, 60, 60)
        end
    end

    -- Highlight selected button
    button.BackgroundColor3 = Color3.fromRGB(0, 162, 255)

    -- Hide all views
    self.ui.viewport3D.Visible = false
    self.ui.codeContainer.Visible = false
    self.ui.propertiesContainer.Visible = false
    self.ui.hierarchyContainer.Visible = false

    -- Show selected view
    if mode == "3D" then
        self.ui.viewport3D.Visible = true
        self.isRotating = self.viewportSettings.autoRotate
    elseif mode == "Code" then
        self.ui.codeContainer.Visible = true
        self.isRotating = false
        self:updateCodeDisplay()
    elseif mode == "Properties" then
        self.ui.propertiesContainer.Visible = true
        self.isRotating = false
        self:updatePropertiesDisplay()
    elseif mode == "Hierarchy" then
        self.ui.hierarchyContainer.Visible = true
        self.isRotating = false
        self:updateHierarchyDisplay()
    end
end

function PreviewPanel:loadContent(content: PreviewContent)
    self.currentContent = content

    -- Clear previous preview
    if self.previewModel then
        self.previewModel:Destroy()
        self.previewModel = nil
    end

    -- Load based on content type
    if content.type == "Model" and content.model then
        self:loadModelPreview(content.model)
    elseif content.type == "Script" and content.script then
        self:loadScriptPreview(content.script)
    elseif content.type == "Part" and content.part then
        self:loadPartPreview(content.part)
    elseif content.type == "GUI" and content.gui then
        self:loadGUIPreview(content.gui)
    elseif content.type == "Sound" and content.sound then
        self:loadSoundPreview(content.sound)
    end

    -- Update title
    self.ui.title.Text = string.format("Preview: %s (%s)", content.name, content.type)

    -- Update all displays
    self:updateCodeDisplay()
    self:updatePropertiesDisplay()
    self:updateHierarchyDisplay()

    -- Emit event
    self.eventEmitter:emit("contentLoaded", content)
end

function PreviewPanel:loadModelPreview(model: Model)
    -- Clone and prepare model
    local previewModel = model:Clone()
    previewModel.Name = "PreviewModel"

    -- Center the model
    local cf, size = previewModel:GetBoundingBox()
    local center = cf.Position
    previewModel:PivotTo(CFrame.new(-center))

    -- Add to viewport
    previewModel.Parent = self.viewport
    self.previewModel = previewModel

    -- Adjust camera distance based on model size
    self.viewportSettings.cameraDistance = math.max(20, size.Magnitude * 2)
    self:updateCameraPosition()

    -- Start auto-rotation if enabled
    self.isRotating = self.viewportSettings.autoRotate
end

function PreviewPanel:loadScriptPreview(script: string)
    -- Display script in code view
    self.ui.codeText.Text = self:syntaxHighlight(script)

    -- Update line numbers
    local lines = string.split(script, "\n")
    self:updateLineNumbers(#lines)

    -- Switch to code view
    self:switchViewMode("Code", self.ui.active3DButton, self.ui.active3DButton.Parent)
end

function PreviewPanel:loadPartPreview(part: Part)
    -- Clone part for preview
    local previewPart = part:Clone()
    previewPart.Name = "PreviewPart"
    previewPart.Position = Vector3.new(0, 0, 0)
    previewPart.Anchored = true

    -- Add to viewport
    previewPart.Parent = self.viewport
    self.previewModel = previewPart

    -- Adjust camera
    self.viewportSettings.cameraDistance = math.max(10, part.Size.Magnitude * 2)
    self:updateCameraPosition()

    self.isRotating = self.viewportSettings.autoRotate
end

function PreviewPanel:loadGUIPreview(gui: ScreenGui)
    -- Create a surface GUI preview
    local part = Instance.new("Part")
    part.Name = "GUIPreview"
    part.Size = Vector3.new(16, 9, 0.1)
    part.Position = Vector3.new(0, 0, 0)
    part.Anchored = true
    part.Material = Enum.Material.SmoothPlastic
    part.BrickColor = BrickColor.new("Black")
    part.Parent = self.viewport

    local surfaceGui = Instance.new("SurfaceGui")
    surfaceGui.Face = Enum.NormalId.Front
    surfaceGui.Parent = part

    -- Clone GUI contents to surface
    for _, child in ipairs(gui:GetChildren()) do
        child:Clone().Parent = surfaceGui
    end

    self.previewModel = part
    self.viewportSettings.cameraDistance = 20
    self:updateCameraPosition()
end

function PreviewPanel:loadSoundPreview(sound: Sound)
    -- Create visual representation of sound
    local soundVisual = Instance.new("Part")
    soundVisual.Name = "SoundPreview"
    soundVisual.Shape = Enum.PartType.Ball
    soundVisual.Size = Vector3.new(4, 4, 4)
    soundVisual.Position = Vector3.new(0, 0, 0)
    soundVisual.Material = Enum.Material.Neon
    soundVisual.BrickColor = BrickColor.new("Cyan")
    soundVisual.Anchored = true
    soundVisual.Parent = self.viewport

    -- Add pulsing effect
    local light = Instance.new("PointLight")
    light.Brightness = 2
    light.Color = Color3.fromRGB(0, 255, 255)
    light.Range = 10
    light.Parent = soundVisual

    self.previewModel = soundVisual

    -- Create sound info display
    local info = string.format(
        "Sound: %s\nVolume: %.2f\nPitch: %.2f\nLength: %.2fs",
        sound.Name,
        sound.Volume,
        sound.Pitch,
        sound.TimeLength
    )

    -- Display info in properties
    self:updatePropertiesDisplay()
end

function PreviewPanel:updateCameraPosition()
    if not self.viewportCamera then return end

    local angle = self.rotationAngle
    local distance = self.viewportSettings.cameraDistance
    local height = math.sin(math.rad(self.viewportSettings.cameraAngle.X)) * distance
    local horizontalDistance = math.cos(math.rad(self.viewportSettings.cameraAngle.X)) * distance

    local x = math.sin(math.rad(angle)) * horizontalDistance
    local z = math.cos(math.rad(angle)) * horizontalDistance

    self.viewportCamera.CFrame = CFrame.lookAt(
        Vector3.new(x, height, z),
        Vector3.new(0, 0, 0),
        Vector3.new(0, 1, 0)
    )
end

function PreviewPanel:syntaxHighlight(code: string): string
    -- Basic Lua syntax highlighting
    local highlighted = code

    -- Keywords
    local keywords = {
        "local", "function", "end", "if", "then", "else", "elseif",
        "for", "while", "do", "repeat", "until", "return", "break",
        "and", "or", "not", "true", "false", "nil", "in"
    }

    for _, keyword in ipairs(keywords) do
        highlighted = string.gsub(
            highlighted,
            "(%s)(" .. keyword .. ")(%s)",
            '%1<font color="#5698d6">%2</font>%3'
        )
    end

    -- Strings
    highlighted = string.gsub(
        highlighted,
        '(".-")',
        '<font color="#ce9178">%1</font>'
    )
    highlighted = string.gsub(
        highlighted,
        "('.-')",
        '<font color="#ce9178">%1</font>'
    )

    -- Comments
    highlighted = string.gsub(
        highlighted,
        "(%-%-.*)",
        '<font color="#6a9955">%1</font>'
    )

    -- Numbers
    highlighted = string.gsub(
        highlighted,
        "(%d+)",
        '<font color="#b5cea8">%1</font>'
    )

    return highlighted
end

function PreviewPanel:updateLineNumbers(count: number)
    -- Clear existing line numbers
    for _, child in ipairs(self.ui.lineNumberFrame:GetChildren()) do
        child:Destroy()
    end

    -- Create line numbers
    for i = 1, count do
        local lineLabel = Instance.new("TextLabel")
        lineLabel.Size = UDim2.new(1, -5, 0, 14)
        lineLabel.Position = UDim2.new(0, 0, 0, (i - 1) * 14)
        lineLabel.BackgroundTransparency = 1
        lineLabel.Text = tostring(i)
        lineLabel.TextColor3 = Color3.fromRGB(100, 100, 100)
        lineLabel.Font = Enum.Font.Code
        lineLabel.TextXAlignment = Enum.TextXAlignment.Right
        lineLabel.TextSize = 14
        lineLabel.Parent = self.ui.lineNumberFrame
    end

    -- Update canvas size
    self.ui.codeContainer.CanvasSize = UDim2.new(0, 0, 0, count * 14 + 20)
end

function PreviewPanel:updateCodeDisplay()
    if not self.currentContent or not self.currentContent.script then
        self.ui.codeText.Text = "-- No code to display"
        return
    end

    self.ui.codeText.Text = self:syntaxHighlight(self.currentContent.script)
    local lines = string.split(self.currentContent.script, "\n")
    self:updateLineNumbers(#lines)
end

function PreviewPanel:updatePropertiesDisplay()
    -- Clear existing properties
    for _, frame in ipairs(self.ui.propertyFrames) do
        frame:Destroy()
    end
    self.ui.propertyFrames = {}

    if not self.currentContent or not self.currentContent.properties then
        return
    end

    local yOffset = 10
    for key, value in pairs(self.currentContent.properties) do
        local propertyFrame = Instance.new("Frame")
        propertyFrame.Size = UDim2.new(1, -20, 0, 30)
        propertyFrame.Position = UDim2.new(0, 10, 0, yOffset)
        propertyFrame.BackgroundColor3 = Color3.fromRGB(35, 35, 35)
        propertyFrame.BorderSizePixel = 0
        propertyFrame.Parent = self.ui.propertiesContainer

        local keyLabel = Instance.new("TextLabel")
        keyLabel.Size = UDim2.new(0.4, -5, 1, 0)
        keyLabel.Position = UDim2.new(0, 5, 0, 0)
        keyLabel.BackgroundTransparency = 1
        keyLabel.Text = key
        keyLabel.TextColor3 = Color3.fromRGB(150, 150, 150)
        keyLabel.TextXAlignment = Enum.TextXAlignment.Left
        keyLabel.Font = Enum.Font.SourceSans
        keyLabel.TextScaled = true
        keyLabel.Parent = propertyFrame

        local valueLabel = Instance.new("TextLabel")
        valueLabel.Size = UDim2.new(0.6, -5, 1, 0)
        valueLabel.Position = UDim2.new(0.4, 0, 0, 0)
        valueLabel.BackgroundTransparency = 1
        valueLabel.Text = tostring(value)
        valueLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
        valueLabel.TextXAlignment = Enum.TextXAlignment.Left
        valueLabel.Font = Enum.Font.SourceSans
        valueLabel.TextScaled = true
        valueLabel.Parent = propertyFrame

        table.insert(self.ui.propertyFrames, propertyFrame)
        yOffset = yOffset + 35
    end

    self.ui.propertiesContainer.CanvasSize = UDim2.new(0, 0, 0, yOffset)
end

function PreviewPanel:updateHierarchyDisplay()
    -- Clear existing hierarchy
    for _, node in ipairs(self.ui.hierarchyNodes) do
        node:Destroy()
    end
    self.ui.hierarchyNodes = {}

    if not self.currentContent then
        return
    end

    local function createNode(content: PreviewContent, parent: GuiObject, indent: number)
        local nodeFrame = Instance.new("Frame")
        nodeFrame.Size = UDim2.new(1, -20 - indent, 0, 25)
        nodeFrame.Position = UDim2.new(0, 10 + indent, 0, #self.ui.hierarchyNodes * 25)
        nodeFrame.BackgroundTransparency = 1
        nodeFrame.Parent = parent

        local icon = Instance.new("TextLabel")
        icon.Size = UDim2.new(0, 20, 1, 0)
        icon.BackgroundTransparency = 1
        icon.Text = content.children and #content.children > 0 and "▼" or "•"
        icon.TextColor3 = Color3.fromRGB(255, 255, 255)
        icon.Font = Enum.Font.SourceSans
        icon.TextScaled = true
        icon.Parent = nodeFrame

        local nameLabel = Instance.new("TextLabel")
        nameLabel.Size = UDim2.new(1, -25, 1, 0)
        nameLabel.Position = UDim2.new(0, 25, 0, 0)
        nameLabel.BackgroundTransparency = 1
        nameLabel.Text = content.name .. " [" .. content.type .. "]"
        nameLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
        nameLabel.TextXAlignment = Enum.TextXAlignment.Left
        nameLabel.Font = Enum.Font.SourceSans
        nameLabel.TextScaled = true
        nameLabel.Parent = nodeFrame

        table.insert(self.ui.hierarchyNodes, nodeFrame)

        -- Recursively add children
        if content.children then
            for _, child in ipairs(content.children) do
                createNode(child, parent, indent + 20)
            end
        end
    end

    createNode(self.currentContent, self.ui.hierarchyContainer, 0)
    self.ui.hierarchyContainer.CanvasSize = UDim2.new(0, 0, 0, #self.ui.hierarchyNodes * 25 + 10)
end

function PreviewPanel:handleAction(action: string)
    if action == "Apply" then
        if self.currentContent then
            self.eventEmitter:emit("applyContent", self.currentContent)
        end
    elseif action == "Export" then
        if self.currentContent then
            self.eventEmitter:emit("exportContent", self.currentContent)
        end
    end
end

function PreviewPanel:toggleSettings()
    -- Create settings popup
    -- This would show viewport settings
    self.eventEmitter:emit("toggleSettings")
end

function PreviewPanel:setupEventHandlers()
    -- Subscribe to state changes
    self.stateManager:subscribe("previewContent", function(oldContent, newContent)
        if newContent then
            self:loadContent(newContent)
        end
    end)

    -- Zoom control
    if self.ui.zoomHandle then
        local dragging = false
        local zoomSlider = self.ui.zoomHandle.Parent

        self.ui.zoomHandle.InputBegan:Connect(function(input)
            if input.UserInputType == Enum.UserInputType.MouseButton1 then
                dragging = true
            end
        end)

        self.ui.zoomHandle.InputEnded:Connect(function(input)
            if input.UserInputType == Enum.UserInputType.MouseButton1 then
                dragging = false
            end
        end)
    end
end

function PreviewPanel:startRenderLoop()
    table.insert(self.connections, RunService.Heartbeat:Connect(function(deltaTime)
        if self.isRotating and self.viewport.Visible then
            self.rotationAngle = self.rotationAngle + (self.viewportSettings.rotationSpeed * deltaTime * 60)
            if self.rotationAngle > 360 then
                self.rotationAngle = self.rotationAngle - 360
            end
            self:updateCameraPosition()
        end
    end))
end

function PreviewPanel:cleanup()
    -- Disconnect all connections
    for _, connection in ipairs(self.connections) do
        connection:Disconnect()
    end

    -- Clear preview model
    if self.previewModel then
        self.previewModel:Destroy()
    end

    -- Clear UI
    self.ui.container:Destroy()
end

return PreviewPanel
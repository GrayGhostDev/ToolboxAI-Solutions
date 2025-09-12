--[[
    ToolboxAI Object Placer Module
    Version: 1.0.0
    Description: Places educational objects in the world with interactive features
                 Supports various object types, placement patterns, and interactions
--]]

local ObjectPlacer = {}
ObjectPlacer.__index = ObjectPlacer

-- Services
local TweenService = game:GetService("TweenService")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Debris = game:GetService("Debris")

-- Educational object templates
local ObjectTemplates = {
    -- Science objects
    microscope = {
        model = "rbxassetid://1234567",
        size = Vector3.new(2, 3, 2),
        category = "science",
        interactive = true,
        description = "Use to examine specimens"
    },
    telescope = {
        model = "rbxassetid://2345678",
        size = Vector3.new(3, 5, 3),
        category = "science",
        interactive = true,
        description = "Observe celestial objects"
    },
    beaker = {
        model = "rbxassetid://3456789",
        size = Vector3.new(1, 1.5, 1),
        category = "science",
        interactive = true,
        description = "Chemistry experiment container"
    },
    periodic_table = {
        model = "rbxassetid://4567890",
        size = Vector3.new(8, 5, 0.5),
        category = "science",
        interactive = true,
        description = "Interactive periodic table of elements"
    },
    
    -- Math objects
    calculator = {
        model = "rbxassetid://5678901",
        size = Vector3.new(1, 0.5, 1.5),
        category = "math",
        interactive = true,
        description = "Perform calculations"
    },
    geometric_shapes = {
        model = "rbxassetid://6789012",
        size = Vector3.new(5, 5, 5),
        category = "math",
        interactive = false,
        description = "3D geometric shapes display"
    },
    abacus = {
        model = "rbxassetid://7890123",
        size = Vector3.new(3, 2, 1),
        category = "math",
        interactive = true,
        description = "Ancient calculating tool"
    },
    graph_board = {
        model = "rbxassetid://8901234",
        size = Vector3.new(6, 6, 0.5),
        category = "math",
        interactive = true,
        description = "Interactive graphing board"
    },
    
    -- Language objects
    book = {
        model = "rbxassetid://9012345",
        size = Vector3.new(1, 0.2, 1.5),
        category = "language",
        interactive = true,
        description = "Read educational content"
    },
    writing_board = {
        model = "rbxassetid://0123456",
        size = Vector3.new(10, 8, 0.5),
        category = "language",
        interactive = true,
        description = "Interactive writing surface"
    },
    dictionary = {
        model = "rbxassetid://1234567",
        size = Vector3.new(1.5, 0.3, 2),
        category = "language",
        interactive = true,
        description = "Look up word definitions"
    },
    globe = {
        model = "rbxassetid://2345678",
        size = Vector3.new(3, 3, 3),
        category = "geography",
        interactive = true,
        description = "Interactive world map"
    },
    
    -- History objects
    artifact = {
        model = "rbxassetid://3456789",
        size = Vector3.new(2, 2, 2),
        category = "history",
        interactive = true,
        description = "Historical artifact"
    },
    timeline = {
        model = "rbxassetid://4567890",
        size = Vector3.new(12, 3, 0.5),
        category = "history",
        interactive = true,
        description = "Interactive historical timeline"
    }
}

-- Constructor
function ObjectPlacer.new()
    local self = setmetatable({}, ObjectPlacer)
    self.placedObjects = {}
    self.interactionConnections = {}
    self.tooltips = {}
    return self
end

-- Place objects in the world
function ObjectPlacer:PlaceObjects(objectList, config)
    print("[ObjectPlacer] Placing", #objectList, "objects")
    
    config = config or {}
    local placedObjects = {}
    
    for _, objectData in ipairs(objectList) do
        local success, object = pcall(function()
            return self:CreateObject(objectData, config)
        end)
        
        if success and object then
            table.insert(placedObjects, object)
            table.insert(self.placedObjects, object)
            
            -- Add entrance animation
            self:AnimateObjectEntrance(object)
            
            -- Make interactive if specified
            if objectData.interactive ~= false then
                self:MakeInteractive(object, objectData)
            end
        else
            warn("[ObjectPlacer] Failed to create object:", objectData.name or objectData.type)
        end
    end
    
    -- Organize objects if placement pattern is specified
    if config.placement == "grid" then
        self:ArrangeInGrid(placedObjects, config)
    elseif config.placement == "circle" then
        self:ArrangeInCircle(placedObjects, config)
    elseif config.placement == "random" then
        self:ArrangeRandomly(placedObjects, config)
    elseif config.placement == "line" then
        self:ArrangeInLine(placedObjects, config)
    end
    
    return placedObjects
end

-- Create individual object
function ObjectPlacer:CreateObject(objectData, config)
    local template = ObjectTemplates[objectData.type] or {}
    
    -- Create base part or model
    local object
    if template.model and false then -- Disabled asset loading for now
        -- Load from asset ID (placeholder for actual model loading)
        object = Instance.new("Model")
        object.Name = objectData.name or objectData.type or "EducationalObject"
    else
        -- Create procedural object
        object = self:CreateProceduralObject(objectData, template)
    end
    
    -- Add metadata
    local configFolder = Instance.new("Configuration")
    configFolder.Name = "ObjectData"
    configFolder.Parent = object
    
    local typeValue = Instance.new("StringValue")
    typeValue.Name = "Type"
    typeValue.Value = objectData.type or "generic"
    typeValue.Parent = configFolder
    
    local descValue = Instance.new("StringValue")
    descValue.Name = "Description"
    descValue.Value = template.description or objectData.description or "Educational object"
    descValue.Parent = configFolder
    
    local categoryValue = Instance.new("StringValue")
    categoryValue.Name = "Category"
    categoryValue.Value = template.category or objectData.category or "general"
    categoryValue.Parent = configFolder
    
    -- Set position if specified
    if objectData.position then
        local pos = objectData.position
        local position = Vector3.new(
            pos.x or pos.X or 0,
            pos.y or pos.Y or 10,
            pos.z or pos.Z or 0
        )
        local primaryPart = object:FindFirstChildOfClass("Part") or object:FindFirstChild("Base")
        if primaryPart then
            primaryPart.Position = position
            if object:IsA("Model") then
                object.PrimaryPart = primaryPart
                object:SetPrimaryPartCFrame(CFrame.new(position))
            end
        end
    end
    
    -- Add to workspace
    object.Parent = workspace
    
    return object
end

-- Create procedural object based on type
function ObjectPlacer:CreateProceduralObject(data, template)
    local model = Instance.new("Model")
    model.Name = data.name or data.type or "Object"
    
    if data.type == "book" then
        return self:CreateBook(model, data)
    elseif data.type == "geometric_shapes" then
        return self:CreateGeometricShapes(model, data)
    elseif data.type == "writing_board" then
        return self:CreateWritingBoard(model, data)
    elseif data.type == "microscope" then
        return self:CreateMicroscope(model, data)
    elseif data.type == "telescope" then
        return self:CreateTelescope(model, data)
    elseif data.type == "calculator" then
        return self:CreateCalculator(model, data)
    elseif data.type == "globe" then
        return self:CreateGlobe(model, data)
    elseif data.type == "periodic_table" then
        return self:CreatePeriodicTable(model, data)
    else
        -- Default object
        return self:CreateDefaultObject(model, data, template)
    end
end

-- Create book object
function ObjectPlacer:CreateBook(model, data)
    -- Create book cover
    local cover = Instance.new("Part")
    cover.Name = "Cover"
    cover.Size = Vector3.new(2, 0.2, 3)
    cover.Material = Enum.Material.Fabric
    cover.BrickColor = BrickColor.new(data.color or "Really red")
    cover.Anchored = true
    cover.Parent = model
    
    -- Create pages
    local pages = Instance.new("Part")
    pages.Name = "Pages"
    pages.Size = Vector3.new(1.8, 0.15, 2.8)
    pages.Position = cover.Position + Vector3.new(0, 0.1, 0)
    pages.Material = Enum.Material.Paper
    pages.BrickColor = BrickColor.new("Institutional white")
    pages.Anchored = true
    pages.Parent = model
    
    -- Add title on cover
    local surfaceGui = Instance.new("SurfaceGui")
    surfaceGui.Face = Enum.NormalId.Top
    surfaceGui.Parent = cover
    
    local titleLabel = Instance.new("TextLabel")
    titleLabel.Size = UDim2.new(0.8, 0, 0.8, 0)
    titleLabel.Position = UDim2.new(0.1, 0, 0.1, 0)
    titleLabel.BackgroundTransparency = 1
    titleLabel.Text = data.title or "Educational Book"
    titleLabel.TextScaled = true
    titleLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
    titleLabel.Font = Enum.Font.SourceSansBold
    titleLabel.Parent = surfaceGui
    
    return model
end

-- Create geometric shapes display
function ObjectPlacer:CreateGeometricShapes(model, data)
    local shapes = {"Ball", "Block", "Wedge", "Cylinder"}
    local colors = {"Bright red", "Bright blue", "Bright yellow", "Bright green"}
    
    for i, shape in ipairs(shapes) do
        local part = Instance.new("Part")
        part.Name = shape
        part.Shape = Enum.PartType[shape]
        part.Size = Vector3.new(2, 2, 2)
        part.Position = Vector3.new((i-2.5)*3, 5, 0)
        part.Material = Enum.Material.Neon
        part.BrickColor = BrickColor.new(colors[i])
        part.Anchored = false
        part.Parent = model
        
        -- Add rotation animation
        local bodyPosition = Instance.new("BodyPosition")
        bodyPosition.Position = part.Position
        bodyPosition.MaxForce = Vector3.new(4000, 4000, 4000)
        bodyPosition.Parent = part
        
        local bodyAngularVelocity = Instance.new("BodyAngularVelocity")
        bodyAngularVelocity.AngularVelocity = Vector3.new(0, i, 0)
        bodyAngularVelocity.MaxTorque = Vector3.new(0, math.huge, 0)
        bodyAngularVelocity.Parent = part
    end
    
    return model
end

-- Create interactive whiteboard
function ObjectPlacer:CreateWritingBoard(model, data)
    -- Create board
    local board = Instance.new("Part")
    board.Name = "Board"
    board.Size = Vector3.new(10, 6, 0.5)
    board.Material = Enum.Material.SmoothPlastic
    board.BrickColor = BrickColor.new("Institutional white")
    board.Anchored = true
    board.Parent = model
    
    -- Add SurfaceGui for writing
    local surfaceGui = Instance.new("SurfaceGui")
    surfaceGui.Name = "WritingSurface"
    surfaceGui.Face = Enum.NormalId.Front
    surfaceGui.Parent = board
    
    local canvas = Instance.new("Frame")
    canvas.Name = "Canvas"
    canvas.Size = UDim2.new(1, 0, 1, 0)
    canvas.BackgroundColor3 = Color3.fromRGB(255, 255, 255)
    canvas.BorderSizePixel = 0
    canvas.Parent = surfaceGui
    
    -- Add frame
    local frame = Instance.new("Part")
    frame.Name = "Frame"
    frame.Size = Vector3.new(10.5, 6.5, 0.2)
    frame.Position = board.Position - Vector3.new(0, 0, 0.3)
    frame.Material = Enum.Material.Wood
    frame.BrickColor = BrickColor.new("Brown")
    frame.Anchored = true
    frame.Parent = model
    
    -- Add title area
    local titleLabel = Instance.new("TextLabel")
    titleLabel.Size = UDim2.new(1, 0, 0.1, 0)
    titleLabel.Position = UDim2.new(0, 0, 0, 0)
    titleLabel.BackgroundColor3 = Color3.fromRGB(240, 240, 240)
    titleLabel.BorderSizePixel = 0
    titleLabel.Text = data.title or "Interactive Whiteboard"
    titleLabel.TextScaled = true
    titleLabel.TextColor3 = Color3.fromRGB(50, 50, 50)
    titleLabel.Font = Enum.Font.SourceSansBold
    titleLabel.Parent = canvas
    
    return model
end

-- Create microscope object
function ObjectPlacer:CreateMicroscope(model, data)
    -- Base
    local base = Instance.new("Part")
    base.Name = "Base"
    base.Size = Vector3.new(3, 0.5, 2)
    base.Material = Enum.Material.Metal
    base.BrickColor = BrickColor.new("Black")
    base.Anchored = true
    base.Parent = model
    
    -- Stand
    local stand = Instance.new("Part")
    stand.Name = "Stand"
    stand.Size = Vector3.new(0.5, 3, 0.5)
    stand.Position = base.Position + Vector3.new(0, 1.75, -0.5)
    stand.Material = Enum.Material.Metal
    stand.BrickColor = BrickColor.new("Black")
    stand.Anchored = true
    stand.Parent = model
    
    -- Eyepiece
    local eyepiece = Instance.new("Part")
    eyepiece.Name = "Eyepiece"
    eyepiece.Shape = Enum.PartType.Cylinder
    eyepiece.Size = Vector3.new(1, 0.3, 0.3)
    eyepiece.Position = stand.Position + Vector3.new(0, 1.5, 0.5)
    eyepiece.Orientation = Vector3.new(45, 0, 0)
    eyepiece.Material = Enum.Material.Glass
    eyepiece.BrickColor = BrickColor.new("Really black")
    eyepiece.Anchored = true
    eyepiece.Parent = model
    
    -- Stage
    local stage = Instance.new("Part")
    stage.Name = "Stage"
    stage.Size = Vector3.new(2, 0.1, 2)
    stage.Position = base.Position + Vector3.new(0, 0.5, 0)
    stage.Material = Enum.Material.Metal
    stage.BrickColor = BrickColor.new("Medium stone grey")
    stage.Anchored = true
    stage.Parent = model
    
    -- Objective lenses
    for i = 1, 3 do
        local lens = Instance.new("Part")
        lens.Name = "Lens" .. i
        lens.Shape = Enum.PartType.Cylinder
        lens.Size = Vector3.new(0.5, 0.2, 0.2)
        lens.Position = stand.Position + Vector3.new(0.3 * math.cos(i * math.pi * 2/3), 0.5, 0.3 * math.sin(i * math.pi * 2/3))
        lens.Material = Enum.Material.Glass
        lens.BrickColor = BrickColor.new("Really blue")
        lens.Anchored = true
        lens.Parent = model
    end
    
    return model
end

-- Create telescope object
function ObjectPlacer:CreateTelescope(model, data)
    -- Tripod legs
    for i = 1, 3 do
        local leg = Instance.new("Part")
        leg.Name = "Leg" .. i
        leg.Size = Vector3.new(0.2, 4, 0.2)
        local angle = i * math.pi * 2/3
        leg.Position = Vector3.new(math.cos(angle) * 1.5, 2, math.sin(angle) * 1.5)
        leg.Orientation = Vector3.new(-20, math.deg(angle), 0)
        leg.Material = Enum.Material.Metal
        leg.BrickColor = BrickColor.new("Black")
        leg.Anchored = true
        leg.Parent = model
    end
    
    -- Main tube
    local tube = Instance.new("Part")
    tube.Name = "Tube"
    tube.Shape = Enum.PartType.Cylinder
    tube.Size = Vector3.new(5, 1, 1)
    tube.Position = Vector3.new(0, 3.5, 0)
    tube.Orientation = Vector3.new(0, 0, 90)
    tube.Material = Enum.Material.Metal
    tube.BrickColor = BrickColor.new("Dark stone grey")
    tube.Anchored = true
    tube.Parent = model
    
    -- Eyepiece
    local eyepiece = Instance.new("Part")
    eyepiece.Name = "Eyepiece"
    eyepiece.Shape = Enum.PartType.Cylinder
    eyepiece.Size = Vector3.new(0.5, 0.3, 0.3)
    eyepiece.Position = tube.Position - Vector3.new(2.25, 0, 0)
    eyepiece.Orientation = Vector3.new(0, 0, 90)
    eyepiece.Material = Enum.Material.Glass
    eyepiece.BrickColor = BrickColor.new("Really black")
    eyepiece.Anchored = true
    eyepiece.Parent = model
    
    -- Objective lens
    local lens = Instance.new("Part")
    lens.Name = "Lens"
    lens.Shape = Enum.PartType.Cylinder
    lens.Size = Vector3.new(0.1, 1.2, 1.2)
    lens.Position = tube.Position + Vector3.new(2.5, 0, 0)
    lens.Orientation = Vector3.new(0, 0, 90)
    lens.Material = Enum.Material.Glass
    lens.BrickColor = BrickColor.new("Light blue")
    lens.Transparency = 0.5
    lens.Anchored = true
    lens.Parent = model
    
    return model
end

-- Create calculator object
function ObjectPlacer:CreateCalculator(model, data)
    -- Body
    local body = Instance.new("Part")
    body.Name = "Body"
    body.Size = Vector3.new(1.5, 0.3, 2)
    body.Material = Enum.Material.Plastic
    body.BrickColor = BrickColor.new("Dark grey")
    body.Anchored = true
    body.Parent = model
    
    -- Screen
    local screen = Instance.new("Part")
    screen.Name = "Screen"
    screen.Size = Vector3.new(1.3, 0.05, 0.5)
    screen.Position = body.Position + Vector3.new(0, 0.2, -0.5)
    screen.Material = Enum.Material.Glass
    screen.BrickColor = BrickColor.new("Black")
    screen.Anchored = true
    screen.Parent = model
    
    -- Add display
    local surfaceGui = Instance.new("SurfaceGui")
    surfaceGui.Face = Enum.NormalId.Top
    surfaceGui.Parent = screen
    
    local display = Instance.new("TextLabel")
    display.Size = UDim2.new(1, 0, 1, 0)
    display.BackgroundColor3 = Color3.fromRGB(150, 180, 150)
    display.BorderSizePixel = 0
    display.Text = "0"
    display.TextScaled = true
    display.TextColor3 = Color3.fromRGB(20, 20, 20)
    display.Font = Enum.Font.Code
    display.Parent = surfaceGui
    
    -- Create buttons
    local buttons = {"7", "8", "9", "/", "4", "5", "6", "*", "1", "2", "3", "-", "0", ".", "=", "+"}
    for i, label in ipairs(buttons) do
        local row = math.floor((i-1) / 4)
        local col = (i-1) % 4
        
        local button = Instance.new("Part")
        button.Name = "Button" .. label
        button.Size = Vector3.new(0.25, 0.1, 0.25)
        button.Position = body.Position + Vector3.new(-0.45 + col * 0.3, 0.2, -0.2 + row * 0.3)
        button.Material = Enum.Material.Plastic
        button.BrickColor = BrickColor.new("Medium stone grey")
        button.Anchored = true
        button.Parent = model
        
        -- Add button label
        local buttonGui = Instance.new("SurfaceGui")
        buttonGui.Face = Enum.NormalId.Top
        buttonGui.Parent = button
        
        local buttonLabel = Instance.new("TextLabel")
        buttonLabel.Size = UDim2.new(1, 0, 1, 0)
        buttonLabel.BackgroundTransparency = 1
        buttonLabel.Text = label
        buttonLabel.TextScaled = true
        buttonLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
        buttonLabel.Font = Enum.Font.SourceSansBold
        buttonLabel.Parent = buttonGui
    end
    
    return model
end

-- Create globe object
function ObjectPlacer:CreateGlobe(model, data)
    -- Stand
    local stand = Instance.new("Part")
    stand.Name = "Stand"
    stand.Size = Vector3.new(2, 0.3, 2)
    stand.Material = Enum.Material.Wood
    stand.BrickColor = BrickColor.new("Brown")
    stand.Anchored = true
    stand.Parent = model
    
    -- Pole
    local pole = Instance.new("Part")
    pole.Name = "Pole"
    pole.Size = Vector3.new(0.2, 3, 0.2)
    pole.Position = stand.Position + Vector3.new(0, 1.65, 0)
    pole.Material = Enum.Material.Metal
    pole.BrickColor = BrickColor.new("Black")
    pole.Anchored = true
    pole.Parent = model
    
    -- Globe sphere
    local globe = Instance.new("Part")
    globe.Name = "Globe"
    globe.Shape = Enum.PartType.Ball
    globe.Size = Vector3.new(3, 3, 3)
    globe.Position = pole.Position + Vector3.new(0, 1.5, 0)
    globe.Material = Enum.Material.Neon
    globe.BrickColor = BrickColor.new("Deep blue")
    globe.Anchored = false
    globe.Parent = model
    
    -- Add rotation
    local bodyPosition = Instance.new("BodyPosition")
    bodyPosition.Position = globe.Position
    bodyPosition.MaxForce = Vector3.new(4000, 4000, 4000)
    bodyPosition.Parent = globe
    
    local bodyAngularVelocity = Instance.new("BodyAngularVelocity")
    bodyAngularVelocity.AngularVelocity = Vector3.new(0, 0.5, 0)
    bodyAngularVelocity.MaxTorque = Vector3.new(0, math.huge, 0)
    bodyAngularVelocity.Parent = globe
    
    -- Add continents texture (simplified)
    local texture = Instance.new("Texture")
    texture.Texture = "rbxasset://textures/water_normal.dds" -- Placeholder
    texture.Face = Enum.NormalId.Front
    texture.StudsPerTileU = 5
    texture.StudsPerTileV = 5
    texture.Parent = globe
    
    return model
end

-- Create periodic table
function ObjectPlacer:CreatePeriodicTable(model, data)
    -- Board
    local board = Instance.new("Part")
    board.Name = "Board"
    board.Size = Vector3.new(12, 8, 0.5)
    board.Material = Enum.Material.SmoothPlastic
    board.BrickColor = BrickColor.new("Black")
    board.Anchored = true
    board.Parent = model
    
    -- Add surface GUI
    local surfaceGui = Instance.new("SurfaceGui")
    surfaceGui.Face = Enum.NormalId.Front
    surfaceGui.Parent = board
    
    -- Title
    local title = Instance.new("TextLabel")
    title.Size = UDim2.new(1, 0, 0.1, 0)
    title.Position = UDim2.new(0, 0, 0, 0)
    title.BackgroundTransparency = 1
    title.Text = "Periodic Table of Elements"
    title.TextScaled = true
    title.TextColor3 = Color3.fromRGB(255, 255, 255)
    title.Font = Enum.Font.SourceSansBold
    title.Parent = surfaceGui
    
    -- Create grid for elements (simplified)
    local gridFrame = Instance.new("Frame")
    gridFrame.Size = UDim2.new(0.95, 0, 0.85, 0)
    gridFrame.Position = UDim2.new(0.025, 0, 0.125, 0)
    gridFrame.BackgroundTransparency = 1
    gridFrame.Parent = surfaceGui
    
    -- Add some example elements
    local elements = {
        {symbol = "H", name = "Hydrogen", number = 1, color = Color3.fromRGB(255, 255, 255)},
        {symbol = "He", name = "Helium", number = 2, color = Color3.fromRGB(217, 255, 255)},
        {symbol = "Li", name = "Lithium", number = 3, color = Color3.fromRGB(204, 128, 255)},
        {symbol = "Be", name = "Beryllium", number = 4, color = Color3.fromRGB(194, 255, 0)},
        {symbol = "B", name = "Boron", number = 5, color = Color3.fromRGB(255, 181, 181)},
        {symbol = "C", name = "Carbon", number = 6, color = Color3.fromRGB(144, 144, 144)},
        {symbol = "N", name = "Nitrogen", number = 7, color = Color3.fromRGB(48, 80, 248)},
        {symbol = "O", name = "Oxygen", number = 8, color = Color3.fromRGB(255, 13, 13)},
    }
    
    for i, element in ipairs(elements) do
        local elementFrame = Instance.new("Frame")
        elementFrame.Size = UDim2.new(0.08, 0, 0.1, 0)
        elementFrame.Position = UDim2.new((i-1) * 0.1, 0, 0, 0)
        elementFrame.BackgroundColor3 = element.color
        elementFrame.BorderSizePixel = 1
        elementFrame.BorderColor3 = Color3.fromRGB(255, 255, 255)
        elementFrame.Parent = gridFrame
        
        local symbolLabel = Instance.new("TextLabel")
        symbolLabel.Size = UDim2.new(1, 0, 0.6, 0)
        symbolLabel.Position = UDim2.new(0, 0, 0.2, 0)
        symbolLabel.BackgroundTransparency = 1
        symbolLabel.Text = element.symbol
        symbolLabel.TextScaled = true
        symbolLabel.TextColor3 = Color3.fromRGB(0, 0, 0)
        symbolLabel.Font = Enum.Font.SourceSansBold
        symbolLabel.Parent = elementFrame
        
        local numberLabel = Instance.new("TextLabel")
        numberLabel.Size = UDim2.new(1, 0, 0.2, 0)
        numberLabel.Position = UDim2.new(0, 0, 0, 0)
        numberLabel.BackgroundTransparency = 1
        numberLabel.Text = tostring(element.number)
        numberLabel.TextScaled = true
        numberLabel.TextColor3 = Color3.fromRGB(0, 0, 0)
        numberLabel.Font = Enum.Font.SourceSans
        numberLabel.Parent = elementFrame
    end
    
    return model
end

-- Create default object
function ObjectPlacer:CreateDefaultObject(model, data, template)
    local part = Instance.new("Part")
    part.Name = "Base"
    part.Size = template.size or Vector3.new(2, 2, 2)
    part.Material = Enum.Material.Plastic
    part.BrickColor = BrickColor.new(data.color or "Medium stone grey")
    part.Anchored = true
    part.Parent = model
    
    -- Add visual interest
    if data.mesh then
        local mesh = Instance.new("SpecialMesh")
        mesh.MeshType = data.mesh.type or Enum.MeshType.Brick
        mesh.Scale = data.mesh.scale or Vector3.new(1, 1, 1)
        mesh.Parent = part
    end
    
    return model
end

-- Make object interactive
function ObjectPlacer:MakeInteractive(object, data)
    local part = object:FindFirstChild("Base") or object:FindFirstChildOfClass("Part")
    if not part then return end
    
    local clickDetector = Instance.new("ClickDetector")
    clickDetector.MaxActivationDistance = 10
    clickDetector.Parent = part
    
    -- Store original properties
    local originalColor = part.BrickColor
    local originalMaterial = part.Material
    local tooltip = nil
    
    -- Hover enter
    local hoverConnection = clickDetector.MouseHoverEnter:Connect(function(player)
        -- Highlight effect
        part.BrickColor = BrickColor.new("Lime green")
        part.Material = Enum.Material.Neon
        
        -- Show tooltip
        tooltip = self:ShowTooltip(player, object, data)
    end)
    
    -- Hover leave
    local leaveConnection = clickDetector.MouseHoverLeave:Connect(function(player)
        -- Restore original appearance
        part.BrickColor = originalColor
        part.Material = originalMaterial
        
        -- Hide tooltip
        if tooltip then
            self:HideTooltip(player, tooltip)
            tooltip = nil
        end
    end)
    
    -- Click interaction
    local clickConnection = clickDetector.MouseClick:Connect(function(player)
        print("[ObjectPlacer] Player", player.Name, "interacted with", object.Name)
        
        -- Fire remote event for server handling
        local remoteEvent = ReplicatedStorage:FindFirstChild("ObjectInteraction")
        if not remoteEvent then
            remoteEvent = Instance.new("RemoteEvent")
            remoteEvent.Name = "ObjectInteraction"
            remoteEvent.Parent = ReplicatedStorage
        end
        
        remoteEvent:FireClient(player, {
            objectType = data.type,
            objectName = object.Name,
            action = "interact",
            timestamp = tick()
        })
        
        -- Local feedback
        self:PlayInteractionEffect(object)
    end)
    
    -- Store connections for cleanup
    table.insert(self.interactionConnections, {
        hover = hoverConnection,
        leave = leaveConnection,
        click = clickConnection,
        object = object
    })
end

-- Show tooltip
function ObjectPlacer:ShowTooltip(player, object, data)
    local playerGui = player:FindFirstChild("PlayerGui")
    if not playerGui then return end
    
    local tooltip = Instance.new("ScreenGui")
    tooltip.Name = "ObjectTooltip"
    tooltip.ResetOnSpawn = false
    tooltip.Parent = playerGui
    
    local frame = Instance.new("Frame")
    frame.Size = UDim2.new(0.2, 0, 0.1, 0)
    frame.Position = UDim2.new(0.4, 0, 0.8, 0)
    frame.BackgroundColor3 = Color3.fromRGB(50, 50, 50)
    frame.BorderSizePixel = 0
    frame.Parent = tooltip
    
    local corner = Instance.new("UICorner")
    corner.CornerRadius = UDim.new(0, 8)
    corner.Parent = frame
    
    local padding = Instance.new("UIPadding")
    padding.PaddingLeft = UDim.new(0, 10)
    padding.PaddingRight = UDim.new(0, 10)
    padding.PaddingTop = UDim.new(0, 5)
    padding.PaddingBottom = UDim.new(0, 5)
    padding.Parent = frame
    
    local titleLabel = Instance.new("TextLabel")
    titleLabel.Size = UDim2.new(1, 0, 0.4, 0)
    titleLabel.Position = UDim2.new(0, 0, 0, 0)
    titleLabel.BackgroundTransparency = 1
    titleLabel.Text = object.Name
    titleLabel.TextScaled = true
    titleLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
    titleLabel.Font = Enum.Font.SourceSansBold
    titleLabel.Parent = frame
    
    local descLabel = Instance.new("TextLabel")
    descLabel.Size = UDim2.new(1, 0, 0.6, 0)
    descLabel.Position = UDim2.new(0, 0, 0.4, 0)
    descLabel.BackgroundTransparency = 1
    
    local configData = object:FindFirstChild("ObjectData")
    if configData then
        local desc = configData:FindFirstChild("Description")
        descLabel.Text = desc and desc.Value or "Educational Object"
    else
        descLabel.Text = data.description or "Educational Object"
    end
    
    descLabel.TextScaled = true
    descLabel.TextColor3 = Color3.fromRGB(200, 200, 200)
    descLabel.Font = Enum.Font.SourceSans
    descLabel.Parent = frame
    
    -- Fade in animation
    frame.BackgroundTransparency = 1
    titleLabel.TextTransparency = 1
    descLabel.TextTransparency = 1
    
    local tween = TweenService:Create(
        frame,
        TweenInfo.new(0.2, Enum.EasingStyle.Quad),
        {BackgroundTransparency = 0.2}
    )
    local textTween1 = TweenService:Create(
        titleLabel,
        TweenInfo.new(0.2, Enum.EasingStyle.Quad),
        {TextTransparency = 0}
    )
    local textTween2 = TweenService:Create(
        descLabel,
        TweenInfo.new(0.2, Enum.EasingStyle.Quad),
        {TextTransparency = 0}
    )
    
    tween:Play()
    textTween1:Play()
    textTween2:Play()
    
    self.tooltips[player.Name] = tooltip
    return tooltip
end

-- Hide tooltip
function ObjectPlacer:HideTooltip(player, tooltip)
    if tooltip and tooltip.Parent then
        tooltip:Destroy()
    end
    self.tooltips[player.Name] = nil
end

-- Arrange objects in grid
function ObjectPlacer:ArrangeInGrid(objects, config)
    local rows = config.gridRows or math.ceil(math.sqrt(#objects))
    local cols = config.gridCols or rows
    local spacing = config.spacing or Vector3.new(5, 0, 5)
    local center = config.center or Vector3.new(0, 10, 0)
    
    local index = 1
    for row = 1, rows do
        for col = 1, cols do
            if index <= #objects then
                local object = objects[index]
                local position = center + Vector3.new(
                    (col - cols/2 - 0.5) * spacing.X,
                    0,
                    (row - rows/2 - 0.5) * spacing.Z
                )
                
                self:MoveObject(object, position)
                index = index + 1
            end
        end
    end
end

-- Arrange objects in circle
function ObjectPlacer:ArrangeInCircle(objects, config)
    local radius = config.radius or 20
    local center = config.center or Vector3.new(0, 10, 0)
    local angleStep = (2 * math.pi) / #objects
    
    for i, object in ipairs(objects) do
        local angle = angleStep * (i - 1)
        local position = center + Vector3.new(
            math.cos(angle) * radius,
            0,
            math.sin(angle) * radius
        )
        
        self:MoveObject(object, position)
        
        -- Face center
        local part = object:FindFirstChild("Base") or object:FindFirstChildOfClass("Part")
        if part then
            part.CFrame = CFrame.lookAt(position, center)
        end
    end
end

-- Arrange objects randomly
function ObjectPlacer:ArrangeRandomly(objects, config)
    local area = config.area or Vector3.new(50, 0, 50)
    local center = config.center or Vector3.new(0, 10, 0)
    local minSpacing = config.minSpacing or 3
    
    local positions = {}
    
    for _, object in ipairs(objects) do
        local validPosition = false
        local position
        local attempts = 0
        
        while not validPosition and attempts < 50 do
            position = center + Vector3.new(
                math.random(-area.X/2, area.X/2),
                0,
                math.random(-area.Z/2, area.Z/2)
            )
            
            validPosition = true
            for _, existingPos in ipairs(positions) do
                if (position - existingPos).Magnitude < minSpacing then
                    validPosition = false
                    break
                end
            end
            
            attempts = attempts + 1
        end
        
        if validPosition then
            self:MoveObject(object, position)
            table.insert(positions, position)
        end
    end
end

-- Arrange objects in line
function ObjectPlacer:ArrangeInLine(objects, config)
    local startPos = config.startPosition or Vector3.new(-20, 10, 0)
    local endPos = config.endPosition or Vector3.new(20, 10, 0)
    local direction = (endPos - startPos).Unit
    local totalDistance = (endPos - startPos).Magnitude
    local spacing = totalDistance / (#objects - 1)
    
    for i, object in ipairs(objects) do
        local position = startPos + direction * (spacing * (i - 1))
        self:MoveObject(object, position)
    end
end

-- Move object with animation
function ObjectPlacer:MoveObject(object, targetPosition)
    local part = object:FindFirstChild("Base") or object:FindFirstChildOfClass("Part")
    if not part then return end
    
    local tween = TweenService:Create(
        part,
        TweenInfo.new(1, Enum.EasingStyle.Quad, Enum.EasingDirection.InOut),
        {Position = targetPosition}
    )
    
    tween:Play()
    
    -- If it's a model, move all parts
    if object:IsA("Model") and object.PrimaryPart then
        object:SetPrimaryPartCFrame(CFrame.new(targetPosition))
    end
end

-- Animate object entrance
function ObjectPlacer:AnimateObjectEntrance(object)
    local part = object:FindFirstChild("Base") or object:FindFirstChildOfClass("Part")
    if not part then return end
    
    -- Store original values
    local originalSize = part.Size
    local originalTransparency = part.Transparency
    
    -- Start invisible and small
    part.Size = originalSize * 0.1
    part.Transparency = 1
    
    -- Grow and fade in
    local growTween = TweenService:Create(
        part,
        TweenInfo.new(0.5, Enum.EasingStyle.Back, Enum.EasingDirection.Out),
        {Size = originalSize}
    )
    
    local fadeTween = TweenService:Create(
        part,
        TweenInfo.new(0.5, Enum.EasingStyle.Quad),
        {Transparency = originalTransparency}
    )
    
    growTween:Play()
    fadeTween:Play()
end

-- Play interaction effect
function ObjectPlacer:PlayInteractionEffect(object)
    local part = object:FindFirstChild("Base") or object:FindFirstChildOfClass("Part")
    if not part then return end
    
    -- Create particle effect
    local attachment = Instance.new("Attachment")
    attachment.Parent = part
    
    local particle = Instance.new("ParticleEmitter")
    particle.Texture = "rbxasset://textures/particles/sparkles_main.dds"
    particle.Rate = 50
    particle.Lifetime = NumberRange.new(0.5, 1)
    particle.Speed = NumberRange.new(2, 5)
    particle.SpreadAngle = Vector2.new(360, 360)
    particle.Color = ColorSequence.new(Color3.fromRGB(255, 255, 100))
    particle.Parent = attachment
    
    -- Stop after short burst
    wait(0.2)
    particle.Enabled = false
    Debris:AddItem(attachment, 2)
    
    -- Sound effect
    local sound = Instance.new("Sound")
    sound.SoundId = "rbxasset://sounds/electronicpingshort.wav"
    sound.Volume = 0.5
    sound.Parent = part
    sound:Play()
    
    Debris:AddItem(sound, 2)
    
    -- Visual pulse effect
    local originalSize = part.Size
    local pulseTween = TweenService:Create(
        part,
        TweenInfo.new(0.1, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
        {Size = originalSize * 1.1}
    )
    
    pulseTween:Play()
    pulseTween.Completed:Connect(function()
        local shrinkTween = TweenService:Create(
            part,
            TweenInfo.new(0.1, Enum.EasingStyle.Quad, Enum.EasingDirection.In),
            {Size = originalSize}
        )
        shrinkTween:Play()
    end)
end

-- Cleanup function
function ObjectPlacer:Cleanup()
    -- Disconnect all interaction connections
    for _, connections in ipairs(self.interactionConnections) do
        if connections.hover then connections.hover:Disconnect() end
        if connections.leave then connections.leave:Disconnect() end
        if connections.click then connections.click:Disconnect() end
    end
    self.interactionConnections = {}
    
    -- Clear tooltips
    for playerName, tooltip in pairs(self.tooltips) do
        if tooltip and tooltip.Parent then
            tooltip:Destroy()
        end
    end
    self.tooltips = {}
    
    -- Remove placed objects
    for _, object in ipairs(self.placedObjects) do
        if object and object.Parent then
            object:Destroy()
        end
    end
    self.placedObjects = {}
end

return ObjectPlacer
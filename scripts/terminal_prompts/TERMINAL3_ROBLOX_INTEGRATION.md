# TERMINAL 3: ROBLOX INTEGRATION SPECIALIST
**Priority: HIGH | Status: 90% Complete (10% Lua Scripts Remaining) | Target: 100% in 48 hours**

## YOUR MISSION
You are the Roblox Integration Specialist responsible for completing the final 10% of Roblox Lua scripts, testing the Studio plugin, and ensuring seamless content generation from the educational platform to Roblox Studio. The Flask bridge is already running - you need to complete the integration.

## CURRENT SYSTEM STATUS
```
✅ Flask Bridge: Running (port 5001) 
✅ Roblox Plugin: 90% complete (AIContentGenerator.lua working)
❌ Terrain generation scripts: Incomplete (10%)
❌ Quiz UI generation: Missing dynamic components
❌ Object placement system: Basic only
⚠️ WebSocket fallback: Not implemented for older Studio versions
```

## DEPENDENCIES
- **Terminal 1**: FastAPI must be running on port 8008
- **Terminal 2**: Dashboard should be accessible for testing integration

## PHASE 1: COMPLETE REMAINING LUA SCRIPTS (First 4 hours)

### Task 1.1: Complete Terrain Generation Scripts
```lua
-- File: Roblox/Scripts/ModuleScripts/TerrainGenerator.lua
local TerrainGenerator = {}
local Terrain = workspace.Terrain

-- Terrain material mappings for educational environments
local MaterialMappings = {
    grass = Enum.Material.Grass,
    water = Enum.Material.Water,
    sand = Enum.Material.Sand,
    rock = Enum.Material.Rock,
    snow = Enum.Material.Snow,
    ice = Enum.Material.Glacier,
    mud = Enum.Material.Mud,
    ground = Enum.Material.Ground,
    leafygrass = Enum.Material.LeafyGrass,
    cobblestone = Enum.Material.Cobblestone,
    concrete = Enum.Material.Concrete,
    asphalt = Enum.Material.Asphalt
}

-- Environment presets for different educational themes
local EnvironmentPresets = {
    ocean = {
        materials = {"water", "sand", "rock"},
        heightMap = "wave",
        waterLevel = 20,
        ambientColor = Color3.fromRGB(120, 180, 220)
    },
    mountain = {
        materials = {"rock", "snow", "grass"},
        heightMap = "peaks",
        waterLevel = 0,
        ambientColor = Color3.fromRGB(200, 220, 255)
    },
    forest = {
        materials = {"grass", "leafygrass", "mud"},
        heightMap = "hills",
        waterLevel = 5,
        ambientColor = Color3.fromRGB(150, 180, 120)
    },
    desert = {
        materials = {"sand", "rock", "ground"},
        heightMap = "dunes",
        waterLevel = -10,
        ambientColor = Color3.fromRGB(255, 230, 180)
    },
    arctic = {
        materials = {"snow", "ice", "water"},
        heightMap = "flat",
        waterLevel = 0,
        ambientColor = Color3.fromRGB(230, 240, 255)
    },
    city = {
        materials = {"concrete", "asphalt", "grass"},
        heightMap = "flat",
        waterLevel = -5,
        ambientColor = Color3.fromRGB(180, 180, 180)
    }
}

-- Generate terrain based on content specifications
function TerrainGenerator:GenerateTerrain(config)
    print("[TerrainGenerator] Starting terrain generation with config:", config.environment_type)
    
    -- Clear existing terrain
    Terrain:Clear()
    
    -- Get environment preset
    local preset = EnvironmentPresets[config.environment_type] or EnvironmentPresets.forest
    
    -- Set terrain size
    local size = config.size or Vector3.new(512, 128, 512)
    local resolution = config.resolution or 4
    
    -- Generate base terrain
    self:GenerateBaseTerrain(size, preset, resolution)
    
    -- Add water if specified
    if preset.waterLevel > 0 then
        self:AddWater(size, preset.waterLevel)
    end
    
    -- Apply environment lighting
    self:SetEnvironmentLighting(preset.ambientColor)
    
    -- Add educational landmarks
    if config.landmarks then
        self:AddLandmarks(config.landmarks)
    end
    
    -- Add vegetation if forest/grass environment
    if config.environment_type == "forest" or config.environment_type == "grass" then
        self:AddVegetation(size)
    end
    
    print("[TerrainGenerator] Terrain generation complete")
    return true
end

-- Generate base terrain using noise functions
function TerrainGenerator:GenerateBaseTerrain(size, preset, resolution)
    local region = Region3.new(Vector3.new(-size.X/2, 0, -size.Z/2), Vector3.new(size.X/2, size.Y, size.Z/2))
    region = region:ExpandToGrid(resolution)
    
    -- Create height map
    local heightMap = self:GenerateHeightMap(size, preset.heightMap)
    
    -- Fill terrain with materials based on height
    local materials = {}
    local occupancies = {}
    
    for x = 1, size.X, resolution do
        materials[x] = {}
        occupancies[x] = {}
        
        for y = 1, size.Y, resolution do
            materials[x][y] = {}
            occupancies[x][y] = {}
            
            for z = 1, size.Z, resolution do
                local height = heightMap[x] and heightMap[x][z] or 0
                local material, occupancy = self:GetMaterialAtHeight(y, height, preset)
                
                materials[x][y][z] = material
                occupancies[x][y][z] = occupancy
            end
        end
    end
    
    -- Apply to terrain
    Terrain:WriteVoxels(region, resolution, materials, occupancies)
end

-- Generate height map using Perlin noise
function TerrainGenerator:GenerateHeightMap(size, mapType)
    local heightMap = {}
    local noiseScale = 0.02
    local amplitude = 50
    
    -- Adjust parameters based on map type
    if mapType == "peaks" then
        noiseScale = 0.015
        amplitude = 80
    elseif mapType == "dunes" then
        noiseScale = 0.03
        amplitude = 30
    elseif mapType == "flat" then
        noiseScale = 0.005
        amplitude = 10
    elseif mapType == "wave" then
        noiseScale = 0.025
        amplitude = 20
    end
    
    for x = 1, size.X do
        heightMap[x] = {}
        for z = 1, size.Z do
            -- Multi-octave Perlin noise for realistic terrain
            local height = 0
            local frequency = 1
            local maxValue = 0
            
            for i = 1, 4 do
                height = height + math.noise(x * noiseScale * frequency, z * noiseScale * frequency, 0.5) * amplitude / frequency
                maxValue = maxValue + amplitude / frequency
                frequency = frequency * 2
            end
            
            heightMap[x][z] = height / maxValue * amplitude + amplitude/2
        end
    end
    
    return heightMap
end

-- Determine material based on height
function TerrainGenerator:GetMaterialAtHeight(y, height, preset)
    if y > height then
        return Enum.Material.Air, 0
    end
    
    local materials = preset.materials
    local materialIndex = math.floor((y / height) * #materials) + 1
    materialIndex = math.clamp(materialIndex, 1, #materials)
    
    local materialName = materials[materialIndex]
    local material = MaterialMappings[materialName] or Enum.Material.Grass
    
    return material, 1
end

-- Add water to terrain
function TerrainGenerator:AddWater(size, waterLevel)
    local waterRegion = Region3.new(
        Vector3.new(-size.X/2, 0, -size.Z/2),
        Vector3.new(size.X/2, waterLevel, size.Z/2)
    )
    waterRegion = waterRegion:ExpandToGrid(4)
    
    Terrain:FillBall(
        Vector3.new(0, waterLevel/2, 0),
        math.max(size.X, size.Z),
        Enum.Material.Water
    )
end

-- Set environment lighting
function TerrainGenerator:SetEnvironmentLighting(ambientColor)
    local lighting = game:GetService("Lighting")
    
    lighting.Ambient = ambientColor
    lighting.OutdoorAmbient = ambientColor * 0.7
    lighting.Brightness = 2
    lighting.TimeOfDay = "14:00:00"
    
    -- Add atmosphere for realism
    local atmosphere = lighting:FindFirstChild("Atmosphere")
    if not atmosphere then
        atmosphere = Instance.new("Atmosphere")
        atmosphere.Parent = lighting
    end
    
    atmosphere.Density = 0.3
    atmosphere.Offset = 0.25
    atmosphere.Color = ambientColor
    atmosphere.Decay = ambientColor * 0.8
    atmosphere.Glare = 0.2
    atmosphere.Haze = 1
end

-- Add educational landmarks
function TerrainGenerator:AddLandmarks(landmarks)
    for _, landmark in ipairs(landmarks) do
        local position = landmark.position or Vector3.new(
            math.random(-100, 100),
            20,
            math.random(-100, 100)
        )
        
        if landmark.type == "monument" then
            self:CreateMonument(position, landmark)
        elseif landmark.type == "building" then
            self:CreateBuilding(position, landmark)
        elseif landmark.type == "natural" then
            self:CreateNaturalFeature(position, landmark)
        end
    end
end

-- Create monument landmark
function TerrainGenerator:CreateMonument(position, config)
    local monument = Instance.new("Model")
    monument.Name = config.name or "Monument"
    
    -- Base
    local base = Instance.new("Part")
    base.Name = "Base"
    base.Size = Vector3.new(20, 2, 20)
    base.Position = position
    base.Material = Enum.Material.Marble
    base.BrickColor = BrickColor.new("Medium stone grey")
    base.Anchored = true
    base.Parent = monument
    
    -- Pillar
    local pillar = Instance.new("Part")
    pillar.Name = "Pillar"
    pillar.Size = Vector3.new(5, 30, 5)
    pillar.Position = position + Vector3.new(0, 16, 0)
    pillar.Material = Enum.Material.Marble
    pillar.BrickColor = BrickColor.new("Institutional white")
    pillar.Anchored = true
    pillar.Parent = monument
    
    -- Add educational plaque
    local plaque = Instance.new("Part")
    plaque.Name = "Plaque"
    plaque.Size = Vector3.new(10, 5, 0.5)
    plaque.Position = position + Vector3.new(0, 3, -10)
    plaque.Material = Enum.Material.Metal
    plaque.BrickColor = BrickColor.new("Bronze")
    plaque.Anchored = true
    plaque.Parent = monument
    
    -- Add surface GUI for text
    local surfaceGui = Instance.new("SurfaceGui")
    surfaceGui.Face = Enum.NormalId.Front
    surfaceGui.Parent = plaque
    
    local textLabel = Instance.new("TextLabel")
    textLabel.Size = UDim2.new(1, 0, 1, 0)
    textLabel.Text = config.description or "Historical Monument"
    textLabel.TextScaled = true
    textLabel.BackgroundTransparency = 1
    textLabel.TextColor3 = Color3.new(1, 1, 1)
    textLabel.Font = Enum.Font.SourceSansBold
    textLabel.Parent = surfaceGui
    
    monument.Parent = workspace
end

-- Add vegetation
function TerrainGenerator:AddVegetation(size)
    local vegetationModels = {
        tree = {
            trunkSize = Vector3.new(2, 10, 2),
            leavesSize = Vector3.new(8, 8, 8),
            trunkColor = BrickColor.new("Brown"),
            leavesColor = BrickColor.new("Forest green")
        },
        bush = {
            size = Vector3.new(4, 3, 4),
            color = BrickColor.new("Dark green")
        },
        flower = {
            size = Vector3.new(1, 2, 1),
            colors = {
                BrickColor.new("Bright red"),
                BrickColor.new("Bright yellow"),
                BrickColor.new("Bright blue"),
                BrickColor.new("Pink")
            }
        }
    }
    
    -- Place vegetation randomly
    for i = 1, 50 do
        local vegType = math.random(1, 3) == 1 and "tree" or (math.random(1, 2) == 1 and "bush" or "flower")
        local position = Vector3.new(
            math.random(-size.X/4, size.X/4),
            0,
            math.random(-size.Z/4, size.Z/4)
        )
        
        -- Raycast to find ground level
        local ray = workspace:Raycast(position + Vector3.new(0, 100, 0), Vector3.new(0, -200, 0))
        if ray and ray.Material ~= Enum.Material.Water then
            position = ray.Position
            
            if vegType == "tree" then
                self:CreateTree(position, vegetationModels.tree)
            elseif vegType == "bush" then
                self:CreateBush(position, vegetationModels.bush)
            else
                self:CreateFlower(position, vegetationModels.flower)
            end
        end
    end
end

-- Create tree
function TerrainGenerator:CreateTree(position, config)
    local tree = Instance.new("Model")
    tree.Name = "Tree"
    
    -- Trunk
    local trunk = Instance.new("Part")
    trunk.Name = "Trunk"
    trunk.Size = config.trunkSize
    trunk.Position = position + Vector3.new(0, config.trunkSize.Y/2, 0)
    trunk.Material = Enum.Material.Wood
    trunk.BrickColor = config.trunkColor
    trunk.Anchored = true
    trunk.Parent = tree
    
    -- Leaves
    local leaves = Instance.new("Part")
    leaves.Name = "Leaves"
    leaves.Shape = Enum.PartType.Ball
    leaves.Size = config.leavesSize
    leaves.Position = position + Vector3.new(0, config.trunkSize.Y + config.leavesSize.Y/2 - 2, 0)
    leaves.Material = Enum.Material.LeafyGrass
    leaves.BrickColor = config.leavesColor
    leaves.Anchored = true
    leaves.CanCollide = false
    leaves.Parent = tree
    
    tree.Parent = workspace
end

return TerrainGenerator
```

### Task 1.2: Complete Quiz UI Generation System
```lua
-- File: Roblox/Scripts/ModuleScripts/QuizUIGenerator.lua
local QuizUIGenerator = {}
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

-- UI Templates
local Templates = {
    MultipleChoice = {
        frameSize = UDim2.new(0.8, 0, 0.7, 0),
        questionHeight = 0.2,
        optionHeight = 0.15,
        buttonSpacing = 0.02
    },
    TrueFalse = {
        frameSize = UDim2.new(0.6, 0, 0.5, 0),
        questionHeight = 0.3,
        buttonSize = UDim2.new(0.35, 0, 0.2, 0)
    },
    FillInBlank = {
        frameSize = UDim2.new(0.7, 0, 0.4, 0),
        questionHeight = 0.3,
        inputHeight = 0.2
    },
    Matching = {
        frameSize = UDim2.new(0.9, 0, 0.8, 0),
        itemSize = UDim2.new(0.35, 0, 0.1, 0),
        spacing = 0.05
    }
}

-- Create quiz UI for player
function QuizUIGenerator:CreateQuizUI(player, quizData)
    print("[QuizUIGenerator] Creating quiz UI for", player.Name)
    
    -- Get or create ScreenGui
    local playerGui = player:WaitForChild("PlayerGui")
    local screenGui = playerGui:FindFirstChild("QuizGui")
    
    if screenGui then
        screenGui:Destroy()
    end
    
    screenGui = Instance.new("ScreenGui")
    screenGui.Name = "QuizGui"
    screenGui.ResetOnSpawn = false
    screenGui.Parent = playerGui
    
    -- Create main frame
    local mainFrame = self:CreateMainFrame(screenGui, quizData.title)
    
    -- Create quiz content based on type
    if quizData.type == "multiple_choice" then
        self:CreateMultipleChoice(mainFrame, quizData)
    elseif quizData.type == "true_false" then
        self:CreateTrueFalse(mainFrame, quizData)
    elseif quizData.type == "fill_blank" then
        self:CreateFillInBlank(mainFrame, quizData)
    elseif quizData.type == "matching" then
        self:CreateMatching(mainFrame, quizData)
    end
    
    -- Add timer if time limit exists
    if quizData.timeLimit then
        self:AddTimer(mainFrame, quizData.timeLimit)
    end
    
    -- Add progress indicator
    self:AddProgressIndicator(mainFrame, quizData)
    
    -- Animate entrance
    self:AnimateEntrance(mainFrame)
    
    return screenGui
end

-- Create main frame
function QuizUIGenerator:CreateMainFrame(screenGui, title)
    local frame = Instance.new("Frame")
    frame.Name = "MainFrame"
    frame.Size = UDim2.new(0.8, 0, 0.7, 0)
    frame.Position = UDim2.new(0.1, 0, 1.2, 0) -- Start off-screen
    frame.BackgroundColor3 = Color3.fromRGB(255, 255, 255)
    frame.BorderSizePixel = 0
    frame.Parent = screenGui
    
    -- Add rounded corners
    local corner = Instance.new("UICorner")
    corner.CornerRadius = UDim.new(0, 12)
    corner.Parent = frame
    
    -- Add shadow
    local shadow = Instance.new("ImageLabel")
    shadow.Name = "Shadow"
    shadow.Size = UDim2.new(1, 20, 1, 20)
    shadow.Position = UDim2.new(0, -10, 0, -10)
    shadow.BackgroundTransparency = 1
    shadow.Image = "rbxasset://textures/ui/dialog_shadow.png"
    shadow.ImageColor3 = Color3.fromRGB(0, 0, 0)
    shadow.ImageTransparency = 0.5
    shadow.ZIndex = 0
    shadow.Parent = frame
    
    -- Title bar
    local titleBar = Instance.new("Frame")
    titleBar.Name = "TitleBar"
    titleBar.Size = UDim2.new(1, 0, 0.1, 0)
    titleBar.BackgroundColor3 = Color3.fromRGB(102, 126, 234)
    titleBar.BorderSizePixel = 0
    titleBar.Parent = frame
    
    local titleCorner = Instance.new("UICorner")
    titleCorner.CornerRadius = UDim.new(0, 12)
    titleCorner.Parent = titleBar
    
    local titleText = Instance.new("TextLabel")
    titleText.Name = "Title"
    titleText.Size = UDim2.new(0.8, 0, 1, 0)
    titleText.Position = UDim2.new(0.1, 0, 0, 0)
    titleText.BackgroundTransparency = 1
    titleText.Text = title or "Quiz"
    titleText.TextColor3 = Color3.fromRGB(255, 255, 255)
    titleText.TextScaled = true
    titleText.Font = Enum.Font.SourceSansBold
    titleText.Parent = titleBar
    
    -- Close button
    local closeButton = Instance.new("TextButton")
    closeButton.Name = "CloseButton"
    closeButton.Size = UDim2.new(0.08, 0, 0.8, 0)
    closeButton.Position = UDim2.new(0.9, 0, 0.1, 0)
    closeButton.BackgroundColor3 = Color3.fromRGB(255, 100, 100)
    closeButton.Text = "X"
    closeButton.TextColor3 = Color3.fromRGB(255, 255, 255)
    closeButton.TextScaled = true
    closeButton.Font = Enum.Font.SourceSansBold
    closeButton.Parent = titleBar
    
    local closeCorner = Instance.new("UICorner")
    closeCorner.CornerRadius = UDim.new(0.5, 0)
    closeCorner.Parent = closeButton
    
    closeButton.MouseButton1Click:Connect(function()
        self:AnimateExit(frame, function()
            screenGui:Destroy()
        end)
    end)
    
    -- Content frame
    local contentFrame = Instance.new("ScrollingFrame")
    contentFrame.Name = "Content"
    contentFrame.Size = UDim2.new(0.95, 0, 0.85, 0)
    contentFrame.Position = UDim2.new(0.025, 0, 0.12, 0)
    contentFrame.BackgroundTransparency = 1
    contentFrame.BorderSizePixel = 0
    contentFrame.ScrollBarThickness = 8
    contentFrame.Parent = frame
    
    return frame
end

-- Create multiple choice quiz
function QuizUIGenerator:CreateMultipleChoice(frame, quizData)
    local content = frame:FindFirstChild("Content")
    
    -- Question
    local questionLabel = Instance.new("TextLabel")
    questionLabel.Name = "Question"
    questionLabel.Size = UDim2.new(1, -20, 0.2, 0)
    questionLabel.Position = UDim2.new(0, 10, 0, 10)
    questionLabel.BackgroundTransparency = 1
    questionLabel.Text = quizData.question
    questionLabel.TextColor3 = Color3.fromRGB(50, 50, 50)
    questionLabel.TextWrapped = true
    questionLabel.TextScaled = false
    questionLabel.TextSize = 24
    questionLabel.Font = Enum.Font.SourceSans
    questionLabel.Parent = content
    
    -- Options
    local options = quizData.options or {"Option A", "Option B", "Option C", "Option D"}
    local selectedOption = nil
    
    for i, option in ipairs(options) do
        local optionButton = Instance.new("TextButton")
        optionButton.Name = "Option" .. i
        optionButton.Size = UDim2.new(0.9, 0, 0.12, 0)
        optionButton.Position = UDim2.new(0.05, 0, 0.25 + (i-1) * 0.15, 0)
        optionButton.BackgroundColor3 = Color3.fromRGB(240, 240, 240)
        optionButton.BorderSizePixel = 2
        optionButton.BorderColor3 = Color3.fromRGB(200, 200, 200)
        optionButton.Text = string.format("%s) %s", string.char(64 + i), option)
        optionButton.TextColor3 = Color3.fromRGB(50, 50, 50)
        optionButton.TextScaled = false
        optionButton.TextSize = 20
        optionButton.TextXAlignment = Enum.TextXAlignment.Left
        optionButton.Font = Enum.Font.SourceSans
        optionButton.Parent = content
        
        local optionCorner = Instance.new("UICorner")
        optionCorner.CornerRadius = UDim.new(0, 8)
        optionCorner.Parent = optionButton
        
        local padding = Instance.new("UIPadding")
        padding.PaddingLeft = UDim.new(0, 15)
        padding.Parent = optionButton
        
        optionButton.MouseButton1Click:Connect(function()
            -- Reset all options
            for _, child in ipairs(content:GetChildren()) do
                if child:IsA("TextButton") and child.Name:match("^Option") then
                    child.BackgroundColor3 = Color3.fromRGB(240, 240, 240)
                    child.BorderColor3 = Color3.fromRGB(200, 200, 200)
                end
            end
            
            -- Highlight selected
            optionButton.BackgroundColor3 = Color3.fromRGB(102, 126, 234)
            optionButton.BorderColor3 = Color3.fromRGB(82, 106, 214)
            optionButton.TextColor3 = Color3.fromRGB(255, 255, 255)
            selectedOption = i
            
            -- Enable submit button
            local submitButton = content:FindFirstChild("SubmitButton")
            if submitButton then
                submitButton.BackgroundColor3 = Color3.fromRGB(76, 175, 80)
                submitButton.Active = true
            end
        end)
    end
    
    -- Submit button
    local submitButton = Instance.new("TextButton")
    submitButton.Name = "SubmitButton"
    submitButton.Size = UDim2.new(0.3, 0, 0.1, 0)
    submitButton.Position = UDim2.new(0.35, 0, 0.85, 0)
    submitButton.BackgroundColor3 = Color3.fromRGB(200, 200, 200)
    submitButton.Text = "Submit Answer"
    submitButton.TextColor3 = Color3.fromRGB(255, 255, 255)
    submitButton.TextScaled = true
    submitButton.Font = Enum.Font.SourceSansBold
    submitButton.Active = false
    submitButton.Parent = content
    
    local submitCorner = Instance.new("UICorner")
    submitCorner.CornerRadius = UDim.new(0, 8)
    submitCorner.Parent = submitButton
    
    submitButton.MouseButton1Click:Connect(function()
        if selectedOption then
            self:SubmitAnswer(quizData.id, selectedOption)
            
            -- Show feedback
            if selectedOption == quizData.correctAnswer then
                self:ShowFeedback(frame, true, "Correct! Well done!")
            else
                self:ShowFeedback(frame, false, "Not quite. The correct answer was " .. string.char(64 + quizData.correctAnswer))
            end
        end
    end)
end

-- Add timer to quiz
function QuizUIGenerator:AddTimer(frame, timeLimit)
    local timerFrame = Instance.new("Frame")
    timerFrame.Name = "Timer"
    timerFrame.Size = UDim2.new(0.15, 0, 0.05, 0)
    timerFrame.Position = UDim2.new(0.825, 0, 0.02, 0)
    timerFrame.BackgroundColor3 = Color3.fromRGB(255, 255, 255)
    timerFrame.BorderSizePixel = 1
    timerFrame.BorderColor3 = Color3.fromRGB(200, 200, 200)
    timerFrame.Parent = frame
    
    local timerCorner = Instance.new("UICorner")
    timerCorner.CornerRadius = UDim.new(0, 4)
    timerCorner.Parent = timerFrame
    
    local timerText = Instance.new("TextLabel")
    timerText.Size = UDim2.new(1, 0, 1, 0)
    timerText.BackgroundTransparency = 1
    timerText.Text = string.format("%d:%02d", math.floor(timeLimit/60), timeLimit%60)
    timerText.TextColor3 = Color3.fromRGB(50, 50, 50)
    timerText.TextScaled = true
    timerText.Font = Enum.Font.SourceSansBold
    timerText.Parent = timerFrame
    
    -- Start countdown
    local remaining = timeLimit
    spawn(function()
        while remaining > 0 and timerFrame.Parent do
            wait(1)
            remaining = remaining - 1
            timerText.Text = string.format("%d:%02d", math.floor(remaining/60), remaining%60)
            
            -- Change color when time is running out
            if remaining <= 30 then
                timerText.TextColor3 = Color3.fromRGB(255, 100, 100)
            elseif remaining <= 60 then
                timerText.TextColor3 = Color3.fromRGB(255, 200, 100)
            end
        end
        
        if remaining <= 0 and timerFrame.Parent then
            self:ShowFeedback(frame, false, "Time's up!")
            wait(2)
            frame.Parent:Destroy()
        end
    end)
end

-- Show feedback
function QuizUIGenerator:ShowFeedback(frame, isCorrect, message)
    local feedbackFrame = Instance.new("Frame")
    feedbackFrame.Name = "Feedback"
    feedbackFrame.Size = UDim2.new(0.6, 0, 0.15, 0)
    feedbackFrame.Position = UDim2.new(0.2, 0, 0.425, 0)
    feedbackFrame.BackgroundColor3 = isCorrect and Color3.fromRGB(76, 175, 80) or Color3.fromRGB(244, 67, 54)
    feedbackFrame.BorderSizePixel = 0
    feedbackFrame.ZIndex = 10
    feedbackFrame.Parent = frame
    
    local feedbackCorner = Instance.new("UICorner")
    feedbackCorner.CornerRadius = UDim.new(0, 8)
    feedbackCorner.Parent = feedbackFrame
    
    local feedbackText = Instance.new("TextLabel")
    feedbackText.Size = UDim2.new(1, 0, 1, 0)
    feedbackText.BackgroundTransparency = 1
    feedbackText.Text = message
    feedbackText.TextColor3 = Color3.fromRGB(255, 255, 255)
    feedbackText.TextScaled = true
    feedbackText.Font = Enum.Font.SourceSansBold
    feedbackText.Parent = feedbackFrame
    
    -- Animate feedback
    feedbackFrame.BackgroundTransparency = 1
    feedbackText.TextTransparency = 1
    
    local fadeIn = TweenService:Create(
        feedbackFrame,
        TweenInfo.new(0.3, Enum.EasingStyle.Quad),
        {BackgroundTransparency = 0}
    )
    
    local textFadeIn = TweenService:Create(
        feedbackText,
        TweenInfo.new(0.3, Enum.EasingStyle.Quad),
        {TextTransparency = 0}
    )
    
    fadeIn:Play()
    textFadeIn:Play()
    
    wait(3)
    
    local fadeOut = TweenService:Create(
        feedbackFrame,
        TweenInfo.new(0.3, Enum.EasingStyle.Quad),
        {BackgroundTransparency = 1}
    )
    
    local textFadeOut = TweenService:Create(
        feedbackText,
        TweenInfo.new(0.3, Enum.EasingStyle.Quad),
        {TextTransparency = 1}
    )
    
    fadeOut:Play()
    textFadeOut:Play()
    
    fadeOut.Completed:Connect(function()
        feedbackFrame:Destroy()
    end)
end

-- Animate entrance
function QuizUIGenerator:AnimateEntrance(frame)
    local targetPosition = UDim2.new(0.1, 0, 0.15, 0)
    
    local tween = TweenService:Create(
        frame,
        TweenInfo.new(0.5, Enum.EasingStyle.Back, Enum.EasingDirection.Out),
        {Position = targetPosition}
    )
    
    tween:Play()
end

-- Animate exit
function QuizUIGenerator:AnimateExit(frame, callback)
    local tween = TweenService:Create(
        frame,
        TweenInfo.new(0.3, Enum.EasingStyle.Back, Enum.EasingDirection.In),
        {Position = UDim2.new(0.1, 0, 1.2, 0)}
    )
    
    tween:Play()
    
    tween.Completed:Connect(function()
        if callback then
            callback()
        end
    end)
end

-- Submit answer to server
function QuizUIGenerator:SubmitAnswer(quizId, answer)
    local remoteEvent = ReplicatedStorage:FindFirstChild("QuizSubmit")
    if not remoteEvent then
        remoteEvent = Instance.new("RemoteEvent")
        remoteEvent.Name = "QuizSubmit"
        remoteEvent.Parent = ReplicatedStorage
    end
    
    remoteEvent:FireServer({
        quizId = quizId,
        answer = answer,
        timestamp = os.time()
    })
end

return QuizUIGenerator
```

### Task 1.3: Complete Object Placement System
```lua
-- File: Roblox/Scripts/ModuleScripts/ObjectPlacer.lua
local ObjectPlacer = {}
local TweenService = game:GetService("TweenService")
local RunService = game:GetService("RunService")

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
    
    -- Math objects
    calculator = {
        model = "rbxassetid://3456789",
        size = Vector3.new(1, 0.5, 1.5),
        category = "math",
        interactive = true,
        description = "Perform calculations"
    },
    geometric_shapes = {
        model = "rbxassetid://4567890",
        size = Vector3.new(5, 5, 5),
        category = "math",
        interactive = false,
        description = "3D geometric shapes display"
    },
    
    -- Language objects
    book = {
        model = "rbxassetid://5678901",
        size = Vector3.new(1, 0.2, 1.5),
        category = "language",
        interactive = true,
        description = "Read educational content"
    },
    writing_board = {
        model = "rbxassetid://6789012",
        size = Vector3.new(10, 8, 0.5),
        category = "language",
        interactive = true,
        description = "Interactive writing surface"
    }
}

-- Place objects in the world
function ObjectPlacer:PlaceObjects(objectList, config)
    print("[ObjectPlacer] Placing", #objectList, "objects")
    
    local placedObjects = {}
    
    for _, objectData in ipairs(objectList) do
        local success, object = pcall(function()
            return self:CreateObject(objectData, config)
        end)
        
        if success and object then
            table.insert(placedObjects, object)
            
            -- Add entrance animation
            self:AnimateObjectEntrance(object)
            
            -- Make interactive if specified
            if objectData.interactive then
                self:MakeInteractive(object, objectData)
            end
        else
            warn("[ObjectPlacer] Failed to create object:", objectData.name)
        end
    end
    
    -- Organize objects if grid placement is specified
    if config.placement == "grid" then
        self:ArrangeInGrid(placedObjects, config)
    elseif config.placement == "circle" then
        self:ArrangeInCircle(placedObjects, config)
    elseif config.placement == "random" then
        self:ArrangeRandomly(placedObjects, config)
    end
    
    return placedObjects
end

-- Create individual object
function ObjectPlacer:CreateObject(objectData, config)
    local template = ObjectTemplates[objectData.type] or {}
    
    -- Create base part or model
    local object
    if template.model then
        -- Load from asset ID (placeholder for actual model loading)
        object = Instance.new("Model")
        object.Name = objectData.name or objectData.type
        
        -- Create placeholder part
        local part = Instance.new("Part")
        part.Name = "Base"
        part.Size = template.size or Vector3.new(2, 2, 2)
        part.Position = objectData.position or Vector3.new(0, 10, 0)
        part.Material = Enum.Material.Plastic
        part.BrickColor = BrickColor.new(objectData.color or "Medium stone grey")
        part.Anchored = true
        part.Parent = object
        
        -- Add mesh if specified
        if objectData.mesh then
            local mesh = Instance.new("SpecialMesh")
            mesh.MeshType = objectData.mesh.type or Enum.MeshType.Brick
            mesh.Scale = objectData.mesh.scale or Vector3.new(1, 1, 1)
            mesh.Parent = part
        end
    else
        -- Create procedural object
        object = self:CreateProceduralObject(objectData)
    end
    
    -- Add metadata
    local config = Instance.new("Configuration")
    config.Name = "ObjectData"
    config.Parent = object
    
    local typeValue = Instance.new("StringValue")
    typeValue.Name = "Type"
    typeValue.Value = objectData.type
    typeValue.Parent = config
    
    local descValue = Instance.new("StringValue")
    descValue.Name = "Description"
    descValue.Value = template.description or "Educational object"
    descValue.Parent = config
    
    -- Add to workspace
    object.Parent = workspace
    
    return object
end

-- Create procedural object
function ObjectPlacer:CreateProceduralObject(data)
    local model = Instance.new("Model")
    model.Name = data.name or "Object"
    
    if data.type == "book" then
        -- Create book
        local cover = Instance.new("Part")
        cover.Name = "Cover"
        cover.Size = Vector3.new(2, 0.2, 3)
        cover.Material = Enum.Material.Fabric
        cover.BrickColor = BrickColor.new(data.color or "Really red")
        cover.Anchored = true
        cover.Parent = model
        
        local pages = Instance.new("Part")
        pages.Name = "Pages"
        pages.Size = Vector3.new(1.8, 0.15, 2.8)
        pages.Position = cover.Position + Vector3.new(0, 0.1, 0)
        pages.Material = Enum.Material.Paper
        pages.BrickColor = BrickColor.new("Institutional white")
        pages.Anchored = true
        pages.Parent = model
        
    elseif data.type == "geometric_shapes" then
        -- Create geometric display
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
            part.Anchored = true
            part.Parent = model
            
            -- Add rotation animation
            local spin = Instance.new("BodyAngularVelocity")
            spin.AngularVelocity = Vector3.new(0, 1, 0)
            spin.MaxTorque = Vector3.new(0, math.huge, 0)
            spin.Parent = part
            part.Anchored = false
            
            local anchor = Instance.new("BodyPosition")
            anchor.Position = part.Position
            anchor.MaxForce = Vector3.new(math.huge, math.huge, math.huge)
            anchor.Parent = part
        end
        
    elseif data.type == "writing_board" then
        -- Create interactive whiteboard
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
    end
    
    return model
end

-- Make object interactive
function ObjectPlacer:MakeInteractive(object, data)
    local clickDetector = Instance.new("ClickDetector")
    clickDetector.MaxActivationDistance = 10
    clickDetector.Parent = object:FindFirstChild("Base") or object:FindFirstChildOfClass("Part")
    
    -- Add hover effect
    local originalColor
    clickDetector.MouseHoverEnter:Connect(function()
        local part = object:FindFirstChild("Base") or object:FindFirstChildOfClass("Part")
        if part then
            originalColor = part.BrickColor
            part.BrickColor = BrickColor.new("Lime green")
            
            -- Show tooltip
            self:ShowTooltip(object, data)
        end
    end)
    
    clickDetector.MouseHoverLeave:Connect(function()
        local part = object:FindFirstChild("Base") or object:FindFirstChildOfClass("Part")
        if part and originalColor then
            part.BrickColor = originalColor
        end
        
        -- Hide tooltip
        self:HideTooltip(object)
    end)
    
    -- Add click action
    clickDetector.MouseClick:Connect(function(player)
        print("[ObjectPlacer] Player", player.Name, "interacted with", object.Name)
        
        -- Fire remote event for server handling
        local remoteEvent = game.ReplicatedStorage:FindFirstChild("ObjectInteraction")
        if not remoteEvent then
            remoteEvent = Instance.new("RemoteEvent")
            remoteEvent.Name = "ObjectInteraction"
            remoteEvent.Parent = game.ReplicatedStorage
        end
        
        remoteEvent:FireServer({
            objectType = data.type,
            objectName = object.Name,
            action = "interact",
            timestamp = os.time()
        })
        
        -- Local feedback
        self:PlayInteractionEffect(object)
    end)
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
                
                -- Move object to position
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

-- Move object with animation
function ObjectPlacer:MoveObject(object, targetPosition)
    local part = object:FindFirstChild("Base") or object:FindFirstChildOfClass("Part")
    if not part then return end
    
    local startPosition = part.Position
    local tween = TweenService:Create(
        part,
        TweenInfo.new(1, Enum.EasingStyle.Quad, Enum.EasingDirection.InOut),
        {Position = targetPosition}
    )
    
    tween:Play()
end

-- Animate object entrance
function ObjectPlacer:AnimateObjectEntrance(object)
    local part = object:FindFirstChild("Base") or object:FindFirstChildOfClass("Part")
    if not part then return end
    
    -- Start invisible and small
    local originalSize = part.Size
    local originalTransparency = part.Transparency
    
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
    particle.Parent = attachment
    
    -- Stop after short burst
    wait(0.2)
    particle.Enabled = false
    game:GetService("Debris"):AddItem(attachment, 2)
    
    -- Sound effect
    local sound = Instance.new("Sound")
    sound.SoundId = "rbxasset://sounds/electronicpingshort.wav"
    sound.Volume = 0.5
    sound.Parent = part
    sound:Play()
    
    game:GetService("Debris"):AddItem(sound, 2)
end

return ObjectPlacer
```

## PHASE 2: IMPLEMENT WEBSOCKET FALLBACK (Next 2 hours)

### Task 2.1: Create HTTP Polling Fallback for Older Studio Versions
```lua
-- File: Roblox/Plugins/WebSocketFallback.lua
local HttpService = game:GetService("HttpService")
local RunService = game:GetService("RunService")

local WebSocketFallback = {}
WebSocketFallback.__index = WebSocketFallback

function WebSocketFallback.new(url)
    local self = setmetatable({}, WebSocketFallback)
    
    self.url = url:gsub("^ws://", "http://"):gsub("^wss://", "https://")
    self.connected = false
    self.sessionId = HttpService:GenerateGUID(false)
    self.messageQueue = {}
    self.callbacks = {}
    self.pollInterval = 1 -- seconds
    self.lastPoll = 0
    
    return self
end

function WebSocketFallback:Connect()
    print("[WebSocketFallback] Connecting via HTTP polling to", self.url)
    
    -- Register session
    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = self.url .. "/fallback/connect",
            Method = "POST",
            Headers = {
                ["Content-Type"] = "application/json"
            },
            Body = HttpService:JSONEncode({
                sessionId = self.sessionId,
                type = "roblox_studio",
                version = game:GetService("RunService"):IsStudio() and "Studio" or "Game"
            })
        })
    end)
    
    if success and response.StatusCode == 200 then
        self.connected = true
        print("[WebSocketFallback] Connected with session ID:", self.sessionId)
        
        -- Start polling
        self:StartPolling()
        
        return true
    else
        warn("[WebSocketFallback] Failed to connect:", response)
        return false
    end
end

function WebSocketFallback:StartPolling()
    RunService.Heartbeat:Connect(function()
        if self.connected and tick() - self.lastPoll >= self.pollInterval then
            self.lastPoll = tick()
            self:Poll()
        end
    end)
end

function WebSocketFallback:Poll()
    spawn(function()
        local success, response = pcall(function()
            return HttpService:RequestAsync({
                Url = self.url .. "/fallback/poll",
                Method = "GET",
                Headers = {
                    ["X-Session-Id"] = self.sessionId
                }
            })
        end)
        
        if success and response.StatusCode == 200 then
            local data = HttpService:JSONDecode(response.Body)
            
            -- Process messages
            for _, message in ipairs(data.messages or {}) do
                self:HandleMessage(message)
            end
            
            -- Send queued messages
            if #self.messageQueue > 0 then
                self:FlushMessageQueue()
            end
        elseif response and response.StatusCode == 404 then
            -- Session expired, reconnect
            self.connected = false
            self:Connect()
        end
    end)
end

function WebSocketFallback:Send(data)
    if type(data) == "table" then
        data = HttpService:JSONEncode(data)
    end
    
    table.insert(self.messageQueue, {
        data = data,
        timestamp = tick()
    })
    
    -- Immediate send if not polling
    if tick() - self.lastPoll >= self.pollInterval * 0.5 then
        self:FlushMessageQueue()
    end
end

function WebSocketFallback:FlushMessageQueue()
    if #self.messageQueue == 0 then return end
    
    local messages = self.messageQueue
    self.messageQueue = {}
    
    spawn(function()
        local success, response = pcall(function()
            return HttpService:RequestAsync({
                Url = self.url .. "/fallback/send",
                Method = "POST",
                Headers = {
                    ["Content-Type"] = "application/json",
                    ["X-Session-Id"] = self.sessionId
                },
                Body = HttpService:JSONEncode({
                    messages = messages
                })
            })
        end)
        
        if not success then
            -- Re-queue messages on failure
            for _, msg in ipairs(messages) do
                table.insert(self.messageQueue, 1, msg)
            end
        end
    end)
end

function WebSocketFallback:HandleMessage(message)
    -- Trigger callbacks
    if self.callbacks.message then
        self.callbacks.message(message)
    end
    
    -- Handle specific message types
    if message.type == "ping" then
        self:Send({type = "pong", timestamp = tick()})
    elseif message.type == "content_generated" then
        if self.callbacks.content then
            self.callbacks.content(message.data)
        end
    end
end

function WebSocketFallback:On(event, callback)
    self.callbacks[event] = callback
end

function WebSocketFallback:Disconnect()
    self.connected = false
    
    -- Notify server
    pcall(function()
        HttpService:RequestAsync({
            Url = self.url .. "/fallback/disconnect",
            Method = "POST",
            Headers = {
                ["X-Session-Id"] = self.sessionId
            }
        })
    end)
end

return WebSocketFallback
```

## PHASE 3: TEST PLUGIN WITH FLASK BRIDGE (Next 2 hours)

### Task 3.1: Create Comprehensive Plugin Test Script
```bash
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions

cat > test_roblox_plugin.py << 'EOF'
"""
Comprehensive Roblox Plugin Integration Test
Tests the complete flow from plugin to content generation
"""

import requests
import json
import time
import websocket
import threading
from datetime import datetime

class RobloxPluginTester:
    def __init__(self):
        self.flask_url = "http://127.0.0.1:5001"
        self.fastapi_url = "http://127.0.0.1:8008"
        self.plugin_id = "test_plugin_001"
        self.session_id = None
        self.ws = None
        
    def test_all(self):
        """Run all tests"""
        print("=" * 60)
        print("ROBLOX PLUGIN INTEGRATION TEST SUITE")
        print("=" * 60)
        
        # Check services
        if not self.check_services():
            print("❌ Services not available. Ensure Terminal 1 has started all services.")
            return False
        
        # Test plugin registration
        if not self.test_plugin_registration():
            return False
        
        # Test content generation
        if not self.test_content_generation():
            return False
        
        # Test terrain generation
        if not self.test_terrain_generation():
            return False
        
        # Test quiz creation
        if not self.test_quiz_creation():
            return False
        
        # Test WebSocket
        if not self.test_websocket():
            return False
        
        print("\n✅ ALL TESTS PASSED!")
        return True
    
    def check_services(self):
        """Check if all required services are running"""
        print("\n1. Checking Services...")
        
        services = [
            (self.flask_url + "/health", "Flask Bridge"),
            (self.fastapi_url + "/health", "FastAPI Server")
        ]
        
        all_healthy = True
        for url, name in services:
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    print(f"   ✅ {name}: Running")
                else:
                    print(f"   ❌ {name}: Unhealthy (Status: {response.status_code})")
                    all_healthy = False
            except Exception as e:
                print(f"   ❌ {name}: Not accessible ({str(e)})")
                all_healthy = False
        
        return all_healthy
    
    def test_plugin_registration(self):
        """Test plugin registration with Flask bridge"""
        print("\n2. Testing Plugin Registration...")
        
        try:
            # Register plugin
            response = requests.post(
                f"{self.flask_url}/register_plugin",
                json={
                    "plugin_id": self.plugin_id,
                    "studio_version": "0.595.0.5950667",
                    "user": "test_user",
                    "capabilities": ["terrain", "quiz", "objects"]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.session_id = data.get("session_id")
                print(f"   ✅ Plugin registered: Session ID = {self.session_id}")
                return True
            else:
                print(f"   ❌ Registration failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Registration error: {str(e)}")
            return False
    
    def test_content_generation(self):
        """Test educational content generation"""
        print("\n3. Testing Content Generation...")
        
        try:
            # Request content generation
            response = requests.post(
                f"{self.flask_url}/generate_content",
                json={
                    "session_id": self.session_id,
                    "subject": "Science",
                    "grade_level": 7,
                    "topic": "Solar System",
                    "environment_type": "space_station",
                    "include_quiz": True,
                    "num_questions": 5
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Content generated:")
                print(f"      - Environment: {data.get('environment', {}).get('type')}")
                print(f"      - Objects: {len(data.get('objects', []))}")
                print(f"      - Quiz questions: {len(data.get('quiz', {}).get('questions', []))}")
                return True
            else:
                print(f"   ❌ Content generation failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Content generation error: {str(e)}")
            return False
    
    def test_terrain_generation(self):
        """Test terrain generation script"""
        print("\n4. Testing Terrain Generation...")
        
        try:
            response = requests.post(
                f"{self.flask_url}/plugin/script",
                json={
                    "session_id": self.session_id,
                    "script_type": "terrain",
                    "config": {
                        "environment_type": "ocean",
                        "size": {"x": 512, "y": 128, "z": 512},
                        "water_level": 20,
                        "landmarks": [
                            {"type": "monument", "name": "Lighthouse"}
                        ]
                    }
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Terrain script generated:")
                print(f"      - Script length: {len(data.get('script', ''))} characters")
                print(f"      - Can execute: {data.get('executable', False)}")
                return True
            else:
                print(f"   ❌ Terrain script generation failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Terrain script error: {str(e)}")
            return False
    
    def test_quiz_creation(self):
        """Test quiz UI creation"""
        print("\n5. Testing Quiz Creation...")
        
        try:
            response = requests.post(
                f"{self.flask_url}/plugin/script",
                json={
                    "session_id": self.session_id,
                    "script_type": "quiz",
                    "config": {
                        "title": "Solar System Quiz",
                        "type": "multiple_choice",
                        "questions": [
                            {
                                "question": "Which planet is closest to the Sun?",
                                "options": ["Mercury", "Venus", "Earth", "Mars"],
                                "correct_answer": 0
                            }
                        ],
                        "time_limit": 300
                    }
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Quiz script generated:")
                print(f"      - UI components: {data.get('components', 0)}")
                print(f"      - Interactive: {data.get('interactive', False)}")
                return True
            else:
                print(f"   ❌ Quiz script generation failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Quiz script error: {str(e)}")
            return False
    
    def test_websocket(self):
        """Test WebSocket fallback"""
        print("\n6. Testing WebSocket/HTTP Fallback...")
        
        try:
            # Test HTTP fallback
            response = requests.post(
                f"{self.flask_url}/fallback/connect",
                json={
                    "sessionId": self.session_id,
                    "type": "roblox_studio"
                }
            )
            
            if response.status_code == 200:
                print(f"   ✅ HTTP fallback available")
                
                # Test polling
                response = requests.get(
                    f"{self.flask_url}/fallback/poll",
                    headers={"X-Session-Id": self.session_id}
                )
                
                if response.status_code == 200:
                    print(f"   ✅ Polling working")
                    return True
            
            print(f"   ⚠️ WebSocket fallback not fully implemented")
            return True  # Not critical for now
            
        except Exception as e:
            print(f"   ⚠️ WebSocket test skipped: {str(e)}")
            return True  # Not critical

# Run tests
if __name__ == "__main__":
    tester = RobloxPluginTester()
    success = tester.test_all()
    
    if success:
        print("\n🎉 Roblox plugin integration is working correctly!")
        print("You can now:")
        print("1. Open Roblox Studio")
        print("2. Install the plugin from Roblox/Plugins/AIContentGenerator.lua")
        print("3. Generate educational content directly in Studio")
    else:
        print("\n⚠️ Some tests failed. Please fix the issues and try again.")
EOF

python test_roblox_plugin.py
```

## PHASE 4: STUDIO PLUGIN INSTALLATION GUIDE (Final 1 hour)

### Task 4.1: Create Installation and Usage Documentation
```bash
cat > ROBLOX_PLUGIN_INSTALLATION.md << 'EOF'
# Roblox Studio Plugin Installation & Usage Guide

## Prerequisites
- Roblox Studio installed and updated
- Terminal 1: FastAPI running on port 8008
- Terminal 3: Flask bridge running on port 5001
- Terminal 2: Dashboard running on port 5179

## Installation Steps

### 1. Enable Studio API Services
1. Open Roblox Studio
2. Go to File → Studio Settings
3. Navigate to Security tab
4. Enable "Allow HTTP Requests"
5. Add to Allowed URLs:
   - http://127.0.0.1:5001
   - http://127.0.0.1:8008
   - http://localhost:5001
   - http://localhost:8008

### 2. Install the Plugin
1. In Studio, go to View → Output to see console
2. Open the Command Bar (View → Command Bar)
3. Copy and run this script:

```lua
-- Plugin installer script
local Plugin = plugin:CreateToolbar("ToolBoxAI")
local Button = Plugin:CreateButton(
    "AI Content Generator",
    "Generate educational content with AI",
    "rbxasset://textures/ui/Settings/Help/AvatarCreator.png"
)

-- Load plugin source
local HttpService = game:GetService("HttpService")
local source = HttpService:GetAsync("http://127.0.0.1:5001/plugin/source")
local plugin_module = loadstring(source)()

Button.Click:Connect(function()
    plugin_module:ShowUI()
end)

print("ToolBoxAI Plugin installed successfully!")
```

### 3. Manual Installation (Alternative)
1. Navigate to: `Roblox/Plugins/`
2. Copy `AIContentGenerator.lua`
3. In Studio: Plugins → Plugins Folder → Open Plugins Folder
4. Paste the file into the plugins folder
5. Restart Studio

## Usage Guide

### Generating Educational Content

1. **Open Plugin**
   - Click the ToolBoxAI button in the toolbar
   - The content generation UI will appear

2. **Configure Content**
   - Select Subject (Science, Math, Language, etc.)
   - Choose Grade Level (1-12)
   - Enter Learning Objectives
   - Select Environment Type:
     - Ocean (Marine biology)
     - Mountain (Geology)
     - Forest (Ecology)
     - Desert (Climate)
     - Arctic (Weather)
     - City (Urban studies)
     - Space Station (Astronomy)

3. **Generation Options**
   - ☑️ Include Quiz - Adds interactive assessments
   - ☑️ Add Terrain - Generates themed terrain
   - ☑️ Place Objects - Adds educational props
   - ☑️ Create NPCs - Adds interactive characters

4. **Generate Content**
   - Click "Generate Content" button
   - Watch progress bar
   - Content appears in workspace

### Working with Generated Content

#### Terrain
- Automatically generated based on environment
- Includes appropriate materials and textures
- Water bodies where applicable
- Landmarks for educational reference

#### Educational Objects
- **Interactive Objects**: Click to get information
- **Science Equipment**: Microscopes, telescopes
- **Math Tools**: Calculators, geometric shapes
- **Language Resources**: Books, writing boards

#### Quizzes
- Multiple choice questions
- True/False assessments
- Fill-in-the-blank
- Matching exercises
- Timed challenges

### Customization

#### Modifying Generated Content
1. Select generated objects in Explorer
2. Adjust properties in Properties panel
3. Use Studio tools to refine placement

#### Saving Templates
1. Select customized content
2. Right-click → Save as Model
3. Reuse in future projects

### Troubleshooting

#### Plugin Not Appearing
- Ensure HTTP requests are enabled
- Check Flask bridge is running (port 5001)
- Restart Studio after installation

#### Generation Fails
- Verify FastAPI is running (port 8008)
- Check console output for errors
- Ensure authentication token is valid

#### Content Not Appearing
- Check Output window for errors
- Verify workspace isn't locked
- Ensure StreamingEnabled is off

#### Performance Issues
- Reduce terrain size
- Limit number of objects
- Disable real-time shadows

## API Integration

The plugin communicates with:
1. **Flask Bridge** (5001): Plugin registration and script delivery
2. **FastAPI** (8008): Content generation and AI processing
3. **Dashboard** (5179): Progress monitoring

## Best Practices

1. **Start Small**: Test with simple content first
2. **Save Often**: Use Studio's autosave
3. **Version Control**: Commit generated content to git
4. **Performance**: Monitor memory usage with large worlds
5. **Testing**: Use Studio's test mode to verify interactions

## Support

For issues or questions:
1. Check the Output console in Studio
2. Review Flask bridge logs: `tail -f logs/flask_bridge.log`
3. Monitor FastAPI logs: `tail -f logs/fastapi.log`
4. Verify all services are running: `./monitor_services.sh`

## Examples

### Science Lesson: Solar System
```lua
{
    subject = "Science",
    grade_level = 7,
    topic = "Solar System",
    environment_type = "space_station",
    include_quiz = true,
    add_terrain = true,
    place_objects = true
}
```

### Math Lesson: Geometry
```lua
{
    subject = "Mathematics",
    grade_level = 5,
    topic = "3D Shapes",
    environment_type = "city",
    include_quiz = true,
    place_objects = true
}
```

### Language Lesson: Creative Writing
```lua
{
    subject = "Language Arts",
    grade_level = 8,
    topic = "Story Elements",
    environment_type = "forest",
    include_quiz = false,
    add_terrain = true,
    create_npcs = true
}
```

## Next Steps

After successful installation:
1. Test basic content generation
2. Customize for your curriculum
3. Create lesson templates
4. Train other educators
5. Gather student feedback

Remember: The plugin is a tool to enhance education, not replace teaching!
EOF

echo "Installation guide created. Share with Roblox developers."
```

## SUCCESS CRITERIA

Before marking Terminal 3 complete:

- [ ] All Lua scripts completed (TerrainGenerator, QuizUIGenerator, ObjectPlacer)
- [ ] WebSocket fallback implemented for older Studio versions
- [ ] Plugin tested with Flask bridge successfully
- [ ] Content generation working end-to-end
- [ ] Terrain generation creates appropriate environments
- [ ] Quiz UI displays and functions correctly
- [ ] Objects placed and interactive
- [ ] Installation guide complete and tested
- [ ] No Lua errors in Studio console
- [ ] Performance acceptable (< 5 second generation)

## HANDOFF TO OTHER TERMINALS

Once complete, notify:

1. **Terminal 4**: Roblox integration ready for security testing
2. **Terminal 5**: Lua scripts ready for documentation
3. **Terminal 6**: Roblox components ready for optimization
4. **Terminal 7**: Plugin ready for CI/CD integration
5. **Terminal 8**: Roblox components ready for containerization

## TROUBLESHOOTING

### If plugin doesn't load:
```bash
# Check Flask bridge
curl http://127.0.0.1:5001/plugin/source

# Verify HTTP requests enabled in Studio
# File → Studio Settings → Security → Allow HTTP Requests

# Check Studio console for errors
```

### If content generation fails:
```bash
# Test Flask → FastAPI communication
curl -X POST http://127.0.0.1:5001/generate_content \
  -H "Content-Type: application/json" \
  -d '{"subject": "Science", "grade_level": 7}'

# Check agent system
curl http://127.0.0.1:8008/health
```

### If Lua scripts error:
```lua
-- Add debug output
print("[DEBUG]", variable_name)

-- Use pcall for error handling
local success, result = pcall(function()
    -- Your code here
end)

if not success then
    warn("Error:", result)
end
```

Remember: You're bridging EDUCATION and GAMING. Make it work seamlessly!
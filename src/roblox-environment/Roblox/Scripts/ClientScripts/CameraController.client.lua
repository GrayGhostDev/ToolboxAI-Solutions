--[[
    CameraController.client.lua
    Advanced camera management for educational environments
    
    Handles camera movement, transitions, and view modes
    for different educational activities and scenes
]]

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local player = Players.LocalPlayer
local camera = Workspace.CurrentCamera
local character = player.Character or player.CharacterAdded:Wait()
local humanoid = character:WaitForChild("Humanoid")

-- Camera modes
local CameraModes = {
    DEFAULT = "Default",
    FIXED = "Fixed",
    FOLLOW = "Follow",
    ORBIT = "Orbit",
    CINEMATIC = "Cinematic",
    OVERVIEW = "Overview",
    FIRST_PERSON = "FirstPerson",
    PRESENTATION = "Presentation"
}

local currentMode = CameraModes.DEFAULT
local cameraSettings = {}

-- Initialize camera system
local cameraDefaults = {
    fieldOfView = 70,
    smoothSpeed = 0.1,
    zoomSpeed = 2,
    rotationSpeed = 0.005,
    shakeDecay = 0.95,
    minZoom = 10,
    maxZoom = 100,
    defaultOffset = Vector3.new(0, 10, 20)
}

-- Load user preferences
cameraSettings = {
    smoothingEnabled = true,
    shakeEnabled = true,
    cinematicBars = false,
    mouseInverted = false,
    sensitivity = 1.0,
    currentZoom = 20,
    currentOffset = cameraDefaults.defaultOffset
}

-- Camera shake system
local shakeOffset = Vector3.new()
local shakeRotation = Vector3.new()
local activeShakes = {}

-- Smooth transition state
local transitionActive = false
local transitionStart = nil
local transitionEnd = nil
local transitionDuration = 0

-- TODO: Implement camera mode switching
-- @param mode: string - The camera mode to switch to
-- @param transitionTime: number - Time for transition (optional)
function SwitchCameraMode(mode, transitionTime)
    -- Validate mode exists
    local validMode = false
    for _, m in pairs(CameraModes) do
        if m == mode then
            validMode = true
            break
        end
    end
    
    if not validMode then
        warn("Invalid camera mode: " .. tostring(mode))
        return
    end
    
    -- Save current camera state
    local previousMode = currentMode
    local previousCFrame = camera.CFrame
    
    -- Set transition parameters
    transitionTime = transitionTime or 1
    transitionActive = true
    transitionStart = previousCFrame
    transitionDuration = transitionTime
    
    -- Update mode
    currentMode = mode
    
    -- Update UI indicators
    local playerGui = player:WaitForChild("PlayerGui")
    local cameraUI = playerGui:FindFirstChild("CameraUI")
    if not cameraUI then
        cameraUI = Instance.new("ScreenGui")
        cameraUI.Name = "CameraUI"
        cameraUI.Parent = playerGui
        
        local modeLabel = Instance.new("TextLabel")
        modeLabel.Name = "ModeLabel"
        modeLabel.Size = UDim2.new(0.15, 0, 0.05, 0)
        modeLabel.Position = UDim2.new(0.85, 0, 0.1, 0)
        modeLabel.BackgroundTransparency = 0.3
        modeLabel.BackgroundColor3 = Color3.new(0, 0, 0)
        modeLabel.TextScaled = true
        modeLabel.TextColor3 = Color3.new(1, 1, 1)
        modeLabel.Parent = cameraUI
    end
    
    local modeLabel = cameraUI:FindFirstChild("ModeLabel")
    if modeLabel then
        modeLabel.Text = "Camera: " .. mode
    end
    
    -- Fire mode change event
    game.ReplicatedStorage:WaitForChild("CameraModeChanged"):FireServer(mode, previousMode)
    
    -- Start transition
    wait(transitionTime)
    transitionActive = false
end

-- TODO: Implement default third-person camera
local function UpdateDefaultCamera()
    if not character or not character:FindFirstChild("HumanoidRootPart") then
        return
    end
    
    local rootPart = character.HumanoidRootPart
    local targetPosition = rootPart.Position
    
    -- Apply offset based on character rotation
    local rotatedOffset = rootPart.CFrame:ToWorldSpace(CFrame.new(cameraSettings.currentOffset)).Position - rootPart.Position
    local desiredPosition = targetPosition + rotatedOffset
    
    -- Handle collision detection
    local ray = workspace:Raycast(targetPosition, desiredPosition - targetPosition)
    if ray then
        desiredPosition = ray.Position + (targetPosition - ray.Position).Unit * 0.5
    end
    
    -- Calculate desired camera CFrame
    local desiredCFrame = CFrame.lookAt(desiredPosition, targetPosition)
    
    -- Apply smoothing if enabled
    if cameraSettings.smoothingEnabled and not transitionActive then
        camera.CFrame = camera.CFrame:Lerp(desiredCFrame, cameraDefaults.smoothSpeed)
    else
        camera.CFrame = desiredCFrame
    end
    
    -- Apply camera shake
    if cameraSettings.shakeEnabled and shakeIntensity > 0 then
        camera.CFrame = camera.CFrame * CFrame.new(shakeOffset) * CFrame.Angles(shakeRotation.X, shakeRotation.Y, shakeRotation.Z)
    end
end

-- TODO: Implement fixed camera positions for lessons
local fixedCameraPositions = {}
local currentFixedIndex = 1

local function UpdateFixedCamera()
    -- Disable player camera control
    UserInputService.MouseBehavior = Enum.MouseBehavior.Default
    
    -- Get or create fixed positions
    if #fixedCameraPositions == 0 then
        -- Default fixed positions for common views
        fixedCameraPositions = {
            {position = Vector3.new(0, 50, 0), lookAt = Vector3.new(0, 0, 0)}, -- Top view
            {position = Vector3.new(50, 25, 50), lookAt = Vector3.new(0, 0, 0)}, -- Corner view
            {position = Vector3.new(0, 10, 30), lookAt = Vector3.new(0, 5, 0)}, -- Front view
            {position = Vector3.new(-30, 15, 0), lookAt = Vector3.new(0, 5, 0)} -- Side view
        }
    end
    
    -- Get current fixed position
    local fixedPos = fixedCameraPositions[currentFixedIndex]
    if fixedPos then
        local desiredCFrame = CFrame.lookAt(fixedPos.position, fixedPos.lookAt)
        
        -- Smooth transition to fixed position
        if cameraSettings.smoothingEnabled then
            camera.CFrame = camera.CFrame:Lerp(desiredCFrame, cameraDefaults.smoothSpeed * 2)
        else
            camera.CFrame = desiredCFrame
        end
    end
end

-- Function to switch between fixed views
function SwitchFixedView(index)
    if index and index > 0 and index <= #fixedCameraPositions then
        currentFixedIndex = index
    else
        currentFixedIndex = (currentFixedIndex % #fixedCameraPositions) + 1
    end
end

-- TODO: Implement orbit camera for 3D model viewing
local orbitTarget = nil
local orbitAngleX = 0
local orbitAngleY = math.pi / 4
local orbitDistance = 20
local orbitSpeed = 0.01

local function UpdateOrbitCamera(target)
    target = target or orbitTarget or (character and character:FindFirstChild("HumanoidRootPart"))
    if not target then return end
    
    orbitTarget = target
    local targetPosition = target.Position
    
    -- Auto-rotate if no input
    if not UserInputService:IsMouseButtonPressed(Enum.UserInputType.MouseButton2) then
        orbitAngleX = orbitAngleX + orbitSpeed
    end
    
    -- Calculate orbit position
    local x = math.cos(orbitAngleX) * math.cos(orbitAngleY) * orbitDistance
    local y = math.sin(orbitAngleY) * orbitDistance
    local z = math.sin(orbitAngleX) * math.cos(orbitAngleY) * orbitDistance
    
    local orbitPosition = targetPosition + Vector3.new(x, y, z)
    
    -- Set camera position
    local desiredCFrame = CFrame.lookAt(orbitPosition, targetPosition)
    
    -- Apply smoothing
    if cameraSettings.smoothingEnabled then
        camera.CFrame = camera.CFrame:Lerp(desiredCFrame, cameraDefaults.smoothSpeed)
    else
        camera.CFrame = desiredCFrame
    end
end

-- Handle orbit camera input
local lastMousePosition = nil
UserInputService.InputBegan:Connect(function(input)
    if currentMode == CameraModes.ORBIT and input.UserInputType == Enum.UserInputType.MouseButton2 then
        lastMousePosition = UserInputService:GetMouseLocation()
    end
end)

UserInputService.InputChanged:Connect(function(input)
    if currentMode == CameraModes.ORBIT and lastMousePosition and input.UserInputType == Enum.UserInputType.MouseMovement then
        local delta = UserInputService:GetMouseLocation() - lastMousePosition
        orbitAngleX = orbitAngleX - delta.X * cameraDefaults.rotationSpeed * cameraSettings.sensitivity
        orbitAngleY = math.clamp(orbitAngleY - delta.Y * cameraDefaults.rotationSpeed * cameraSettings.sensitivity, -math.pi/2 + 0.1, math.pi/2 - 0.1)
        lastMousePosition = UserInputService:GetMouseLocation()
    elseif currentMode == CameraModes.ORBIT and input.UserInputType == Enum.UserInputType.MouseWheel then
        orbitDistance = math.clamp(orbitDistance - input.Position.Z * cameraDefaults.zoomSpeed, cameraDefaults.minZoom, cameraDefaults.maxZoom)
    end
end)

UserInputService.InputEnded:Connect(function(input)
    if input.UserInputType == Enum.UserInputType.MouseButton2 then
        lastMousePosition = nil
    end
end)

-- TODO: Implement cinematic camera system
local CinematicCamera = {}
local cinematicKeyframes = {}

function CinematicCamera.AddKeyframe(position, lookAt, time, easingStyle)
    -- Store keyframe with all parameters
    table.insert(cinematicKeyframes, {
        position = position,
        lookAt = lookAt,
        time = time,
        easingStyle = easingStyle or Enum.EasingStyle.Linear,
        cframe = CFrame.lookAt(position, lookAt)
    })
    
    -- Sort keyframes by time
    table.sort(cinematicKeyframes, function(a, b)
        return a.time < b.time
    end)
end

function CinematicCamera.PlayCinematic()
    if #cinematicKeyframes < 2 then
        warn("Need at least 2 keyframes for cinematic")
        return
    end
    
    -- Disable player controls
    local previousMode = currentMode
    currentMode = CameraModes.CINEMATIC
    humanoid.WalkSpeed = 0
    humanoid.JumpPower = 0
    
    -- Add cinematic bars
    local playerGui = player:WaitForChild("PlayerGui")
    local cinematicGui = Instance.new("ScreenGui")
    cinematicGui.Name = "CinematicBars"
    cinematicGui.Parent = playerGui
    
    local topBar = Instance.new("Frame")
    topBar.Size = UDim2.new(1, 0, 0.15, 0)
    topBar.Position = UDim2.new(0, 0, 0, 0)
    topBar.BackgroundColor3 = Color3.new(0, 0, 0)
    topBar.BorderSizePixel = 0
    topBar.Parent = cinematicGui
    
    local bottomBar = Instance.new("Frame")
    bottomBar.Size = UDim2.new(1, 0, 0.15, 0)
    bottomBar.Position = UDim2.new(0, 0, 0.85, 0)
    bottomBar.BackgroundColor3 = Color3.new(0, 0, 0)
    bottomBar.BorderSizePixel = 0
    bottomBar.Parent = cinematicGui
    
    -- Play cinematic sequence
    spawn(function()
        local startTime = tick()
        local currentKeyframeIndex = 1
        
        while currentKeyframeIndex < #cinematicKeyframes do
            local currentKeyframe = cinematicKeyframes[currentKeyframeIndex]
            local nextKeyframe = cinematicKeyframes[currentKeyframeIndex + 1]
            
            local duration = nextKeyframe.time - currentKeyframe.time
            local elapsed = 0
            
            while elapsed < duration do
                elapsed = math.min(elapsed + RunService.RenderStepped:Wait(), duration)
                local t = elapsed / duration
                
                -- Apply easing
                local easedT = TweenService:GetValue(t, currentKeyframe.easingStyle, Enum.EasingDirection.InOut)
                
                -- Interpolate camera position
                camera.CFrame = currentKeyframe.cframe:Lerp(nextKeyframe.cframe, easedT)
                
                -- Check for events at this keyframe
                if elapsed >= duration and nextKeyframe.event then
                    nextKeyframe.event()
                end
            end
            
            currentKeyframeIndex = currentKeyframeIndex + 1
        end
        
        -- Return control after completion
        cinematicGui:Destroy()
        humanoid.WalkSpeed = 16
        humanoid.JumpPower = 50
        currentMode = previousMode
        cinematicKeyframes = {}
    end)
end

-- Add cinematic event support
function CinematicCamera.AddKeyframeWithEvent(position, lookAt, time, event, easingStyle)
    local keyframe = {
        position = position,
        lookAt = lookAt,
        time = time,
        event = event,
        easingStyle = easingStyle or Enum.EasingStyle.Quad,
        cframe = CFrame.lookAt(position, lookAt)
    }
    table.insert(cinematicKeyframes, keyframe)
    table.sort(cinematicKeyframes, function(a, b)
        return a.time < b.time
    end)
end

-- TODO: Implement overview camera for maps/boards
local overviewHeight = 100
local overviewPosition = Vector3.new(0, overviewHeight, 0)
local panSpeed = 1
local overviewBounds = {min = Vector3.new(-500, 0, -500), max = Vector3.new(500, 200, 500)}

local function UpdateOverviewCamera()
    -- Position camera above scene
    local desiredCFrame = CFrame.lookAt(
        overviewPosition,
        overviewPosition - Vector3.new(0, 1, 0)
    )
    
    -- Apply camera position
    camera.CFrame = desiredCFrame
    camera.FieldOfView = 60
    
    -- Handle panning with keyboard
    local moveVector = Vector3.new()
    if UserInputService:IsKeyDown(Enum.KeyCode.W) then
        moveVector = moveVector + Vector3.new(0, 0, -panSpeed)
    end
    if UserInputService:IsKeyDown(Enum.KeyCode.S) then
        moveVector = moveVector + Vector3.new(0, 0, panSpeed)
    end
    if UserInputService:IsKeyDown(Enum.KeyCode.A) then
        moveVector = moveVector + Vector3.new(-panSpeed, 0, 0)
    end
    if UserInputService:IsKeyDown(Enum.KeyCode.D) then
        moveVector = moveVector + Vector3.new(panSpeed, 0, 0)
    end
    
    -- Apply movement with boundaries
    local newPosition = overviewPosition + moveVector
    newPosition = Vector3.new(
        math.clamp(newPosition.X, overviewBounds.min.X, overviewBounds.max.X),
        newPosition.Y,
        math.clamp(newPosition.Z, overviewBounds.min.Z, overviewBounds.max.Z)
    )
    overviewPosition = newPosition
    
    -- Show grid overlay
    local playerGui = player:WaitForChild("PlayerGui")
    local gridGui = playerGui:FindFirstChild("GridOverlay")
    if not gridGui and currentMode == CameraModes.OVERVIEW then
        gridGui = Instance.new("ScreenGui")
        gridGui.Name = "GridOverlay"
        gridGui.Parent = playerGui
        
        -- Add coordinate display
        local coordLabel = Instance.new("TextLabel")
        coordLabel.Size = UDim2.new(0.2, 0, 0.05, 0)
        coordLabel.Position = UDim2.new(0.4, 0, 0.95, 0)
        coordLabel.BackgroundTransparency = 0.5
        coordLabel.TextScaled = true
        coordLabel.Text = string.format("X: %.1f, Z: %.1f", overviewPosition.X, overviewPosition.Z)
        coordLabel.Parent = gridGui
    elseif gridGui then
        local coordLabel = gridGui:FindFirstChildOfClass("TextLabel")
        if coordLabel then
            coordLabel.Text = string.format("X: %.1f, Z: %.1f", overviewPosition.X, overviewPosition.Z)
        end
    end
end

-- TODO: Implement first-person camera
local headBobTime = 0
local headBobIntensity = 0.1

local function UpdateFirstPersonCamera()
    if not character or not character:FindFirstChild("Head") then
        return
    end
    
    local head = character.Head
    
    -- Hide character body parts
    for _, part in pairs(character:GetChildren()) do
        if part:IsA("BasePart") and part ~= head then
            part.LocalTransparencyModifier = 1
        elseif part:IsA("Accessory") then
            local handle = part:FindFirstChild("Handle")
            if handle then
                handle.LocalTransparencyModifier = 1
            end
        end
    end
    
    -- Calculate head bob
    local velocity = character.HumanoidRootPart.Velocity
    local speed = Vector3.new(velocity.X, 0, velocity.Z).Magnitude
    if speed > 1 then
        headBobTime = headBobTime + 0.1
        local bobX = math.sin(headBobTime * 2) * headBobIntensity
        local bobY = math.abs(math.cos(headBobTime * 4)) * headBobIntensity * 0.5
        
        -- Apply head bob
        camera.CFrame = head.CFrame * CFrame.new(bobX, bobY, 0.5)
    else
        -- No movement, steady camera
        camera.CFrame = head.CFrame * CFrame.new(0, 0, 0.5)
    end
    
    -- Adjust FOV for sprinting
    if UserInputService:IsKeyDown(Enum.KeyCode.LeftShift) and speed > 10 then
        camera.FieldOfView = math.min(camera.FieldOfView + 0.5, 80)
    else
        camera.FieldOfView = math.max(camera.FieldOfView - 0.5, 70)
    end
end

-- Reset transparency when leaving first person
local function ResetCharacterTransparency()
    if not character then return end
    
    for _, part in pairs(character:GetChildren()) do
        if part:IsA("BasePart") then
            part.LocalTransparencyModifier = 0
        elseif part:IsA("Accessory") then
            local handle = part:FindFirstChild("Handle")
            if handle then
                handle.LocalTransparencyModifier = 0
            end
        end
    end
end

-- TODO: Implement presentation camera for lectures
local presentationTarget = nil
local presentationOffset = Vector3.new(0, 5, 20)
local pointerTracking = false

local function UpdatePresentationCamera()
    -- Find presentation screen or use default target
    if not presentationTarget then
        presentationTarget = workspace:FindFirstChild("PresentationScreen") or workspace:FindFirstChild("Whiteboard")
    end
    
    if presentationTarget then
        -- Focus on presentation screen
        local targetPosition = presentationTarget.Position
        local screenSize = presentationTarget.Size
        
        -- Calculate optimal viewing distance
        local viewDistance = math.max(screenSize.Magnitude * 1.5, 20)
        local viewPosition = targetPosition + presentationTarget.CFrame.LookVector * viewDistance + Vector3.new(0, 2, 0)
        
        local desiredCFrame = CFrame.lookAt(viewPosition, targetPosition)
        
        -- Apply smooth transition
        if cameraSettings.smoothingEnabled then
            camera.CFrame = camera.CFrame:Lerp(desiredCFrame, cameraDefaults.smoothSpeed)
        else
            camera.CFrame = desiredCFrame
        end
        
        -- Track presenter pointer if enabled
        if pointerTracking then
            local pointer = workspace:FindFirstChild("PresenterPointer")
            if pointer then
                -- Slight camera adjustment to follow pointer
                local pointerOffset = (pointer.Position - targetPosition) * 0.1
                camera.CFrame = camera.CFrame * CFrame.new(pointerOffset)
            end
        end
    else
        -- Fallback to default camera if no presentation screen
        UpdateDefaultCamera()
    end
    
    -- Show presentation UI
    local playerGui = player:WaitForChild("PlayerGui")
    local presentGui = playerGui:FindFirstChild("PresentationUI")
    if not presentGui and currentMode == CameraModes.PRESENTATION then
        presentGui = Instance.new("ScreenGui")
        presentGui.Name = "PresentationUI"
        presentGui.Parent = playerGui
        
        -- Add presentation controls hint
        local hintLabel = Instance.new("TextLabel")
        hintLabel.Size = UDim2.new(0.3, 0, 0.05, 0)
        hintLabel.Position = UDim2.new(0.35, 0, 0.9, 0)
        hintLabel.BackgroundTransparency = 0.5
        hintLabel.TextScaled = true
        hintLabel.Text = "Press Q/E to switch slides | ESC to exit"
        hintLabel.Parent = presentGui
    end
end

-- Function to set presentation target
function SetPresentationTarget(target)
    presentationTarget = target
    if currentMode == CameraModes.PRESENTATION then
        UpdatePresentationCamera()
    end
end

-- TODO: Implement camera shake effects
local CameraShake = {}
local shakeIntensity = 0
local shakeDuration = 0

function CameraShake.Shake(intensity, duration, frequency)
    -- Add new shake to active shakes (allows stacking)
    table.insert(activeShakes, {
        intensity = intensity or 1,
        duration = duration or 0.5,
        frequency = frequency or 30,
        startTime = tick(),
        seed = math.random() * 1000
    })
    
    shakeIntensity = intensity
    shakeDuration = duration
end

function CameraShake.Update(deltaTime)
    if not cameraSettings.shakeEnabled then
        shakeOffset = Vector3.new()
        shakeRotation = Vector3.new()
        return
    end
    
    local totalOffset = Vector3.new()
    local totalRotation = Vector3.new()
    
    -- Process all active shakes
    for i = #activeShakes, 1, -1 do
        local shake = activeShakes[i]
        local elapsed = tick() - shake.startTime
        
        if elapsed < shake.duration then
            -- Calculate shake intensity with decay
            local progress = elapsed / shake.duration
            local currentIntensity = shake.intensity * (1 - progress) * cameraDefaults.shakeDecay
            
            -- Generate shake offset using perlin noise
            local noiseX = math.sin(elapsed * shake.frequency + shake.seed) * currentIntensity
            local noiseY = math.cos(elapsed * shake.frequency * 1.1 + shake.seed) * currentIntensity
            local noiseZ = math.sin(elapsed * shake.frequency * 0.9 + shake.seed) * currentIntensity * 0.5
            
            totalOffset = totalOffset + Vector3.new(noiseX, noiseY, noiseZ)
            
            -- Add rotation shake
            totalRotation = totalRotation + Vector3.new(
                noiseX * 0.01,
                noiseY * 0.01,
                noiseZ * 0.005
            )
        else
            -- Remove completed shake
            table.remove(activeShakes, i)
        end
    end
    
    -- Apply combined shake
    shakeOffset = totalOffset
    shakeRotation = totalRotation
    
    -- Update legacy shake system
    if shakeDuration > 0 then
        shakeDuration = math.max(0, shakeDuration - deltaTime)
        if shakeDuration == 0 then
            shakeIntensity = 0
        end
    end
end

-- TODO: Implement smooth camera transitions
local CameraTransition = {}

function CameraTransition.SmoothTransition(startCFrame, endCFrame, duration, easingStyle, callback)
    -- Cancel any existing transition
    if CameraTransition.currentTween then
        CameraTransition.currentTween:Cancel()
    end
    
    -- Create tween with custom easing
    local tweenInfo = TweenInfo.new(
        duration or 1,
        easingStyle or Enum.EasingStyle.Quad,
        Enum.EasingDirection.InOut,
        0,
        false,
        0
    )
    
    -- Set start position
    camera.CFrame = startCFrame
    
    -- Create and play tween
    local tween = TweenService:Create(
        camera,
        tweenInfo,
        {CFrame = endCFrame, FieldOfView = camera.FieldOfView}
    )
    
    CameraTransition.currentTween = tween
    
    -- Handle completion
    tween.Completed:Connect(function()
        CameraTransition.currentTween = nil
        if callback then
            callback()
        end
    end)
    
    tween:Play()
    return tween
end

-- Bezier curve transition for smoother paths
function CameraTransition.BezierTransition(points, duration, callback)
    if #points < 2 then
        warn("Need at least 2 points for bezier transition")
        return
    end
    
    spawn(function()
        local startTime = tick()
        while tick() - startTime < duration do
            local t = (tick() - startTime) / duration
            
            -- Calculate bezier position
            local position = Vector3.new()
            local n = #points - 1
            for i = 0, n do
                local binomial = 1
                for j = 1, i do
                    binomial = binomial * (n - j + 1) / j
                end
                position = position + binomial * (1 - t)^(n - i) * t^i * points[i + 1]
            end
            
            -- Look at next position for smooth rotation
            local lookAhead = math.min(t + 0.1, 1)
            local lookPosition = Vector3.new()
            for i = 0, n do
                local binomial = 1
                for j = 1, i do
                    binomial = binomial * (n - j + 1) / j
                end
                lookPosition = lookPosition + binomial * (1 - lookAhead)^(n - i) * lookAhead^i * points[i + 1]
            end
            
            camera.CFrame = CFrame.lookAt(position, lookPosition)
            RunService.RenderStepped:Wait()
        end
        
        if callback then
            callback()
        end
    end)
end

-- TODO: Implement camera focus system
local CameraFocus = {}

function CameraFocus.FocusOnObject(object, offset, duration)
    if not object or not object:IsA("BasePart") then
        warn("Invalid object for camera focus")
        return
    end
    
    offset = offset or Vector3.new(5, 5, 10)
    duration = duration or 1
    
    -- Calculate target position
    local objectSize = object.Size.Magnitude
    local distance = math.max(objectSize * 2, 10)
    local targetPosition = object.Position + offset.Unit * distance
    
    -- Create smooth transition
    local startCFrame = camera.CFrame
    local endCFrame = CFrame.lookAt(targetPosition, object.Position)
    
    CameraTransition.SmoothTransition(startCFrame, endCFrame, duration)
    
    -- Track moving object
    local trackConnection
    trackConnection = RunService.Heartbeat:Connect(function()
        if object and object.Parent then
            local newTargetPos = object.Position + offset.Unit * distance
            local desiredCFrame = CFrame.lookAt(newTargetPos, object.Position)
            camera.CFrame = camera.CFrame:Lerp(desiredCFrame, cameraDefaults.smoothSpeed)
        else
            -- Object destroyed, stop tracking
            trackConnection:Disconnect()
            SwitchCameraMode(CameraModes.DEFAULT)
        end
    end)
    
    -- Store connection for cleanup
    CameraFocus.currentTrackConnection = trackConnection
end

function CameraFocus.FocusOnGroup(objects)
    if not objects or #objects == 0 then
        warn("No objects to focus on")
        return
    end
    
    -- Calculate bounding box
    local minPoint = Vector3.new(math.huge, math.huge, math.huge)
    local maxPoint = Vector3.new(-math.huge, -math.huge, -math.huge)
    
    for _, obj in pairs(objects) do
        if obj:IsA("BasePart") then
            local pos = obj.Position
            local size = obj.Size / 2
            
            minPoint = Vector3.new(
                math.min(minPoint.X, pos.X - size.X),
                math.min(minPoint.Y, pos.Y - size.Y),
                math.min(minPoint.Z, pos.Z - size.Z)
            )
            
            maxPoint = Vector3.new(
                math.max(maxPoint.X, pos.X + size.X),
                math.max(maxPoint.Y, pos.Y + size.Y),
                math.max(maxPoint.Z, pos.Z + size.Z)
            )
        end
    end
    
    -- Calculate center and size
    local center = (minPoint + maxPoint) / 2
    local size = (maxPoint - minPoint).Magnitude
    
    -- Find optimal view position
    local distance = size * 1.5
    local viewPosition = center + Vector3.new(distance/2, distance/2, distance)
    
    -- Adjust field of view to fit all objects
    local fov = math.clamp(30 + size * 0.5, 30, 90)
    camera.FieldOfView = fov
    
    -- Transition to view
    local endCFrame = CFrame.lookAt(viewPosition, center)
    CameraTransition.SmoothTransition(camera.CFrame, endCFrame, 1)
end

-- TODO: Implement camera boundaries and constraints
local CameraConstraints = {}

CameraConstraints.boundaries = {min = nil, max = nil}
CameraConstraints.boundaryFeedback = true

function CameraConstraints.SetBoundaries(min, max)
    CameraConstraints.boundaries.min = min
    CameraConstraints.boundaries.max = max
end

function CameraConstraints.ApplyBoundaries(position)
    if not CameraConstraints.boundaries.min or not CameraConstraints.boundaries.max then
        return position
    end
    
    local min = CameraConstraints.boundaries.min
    local max = CameraConstraints.boundaries.max
    
    -- Clamp position
    local clamped = Vector3.new(
        math.clamp(position.X, min.X, max.X),
        math.clamp(position.Y, min.Y, max.Y),
        math.clamp(position.Z, min.Z, max.Z)
    )
    
    -- Visual feedback when hitting boundary
    if CameraConstraints.boundaryFeedback and clamped ~= position then
        -- Flash screen edge
        local playerGui = player:WaitForChild("PlayerGui")
        local flashGui = playerGui:FindFirstChild("BoundaryFlash") or Instance.new("ScreenGui")
        flashGui.Name = "BoundaryFlash"
        flashGui.Parent = playerGui
        
        local flash = Instance.new("Frame")
        flash.Size = UDim2.new(1, 0, 1, 0)
        flash.BackgroundColor3 = Color3.new(1, 0, 0)
        flash.BackgroundTransparency = 0.8
        flash.Parent = flashGui
        
        -- Fade out
        TweenService:Create(
            flash,
            TweenInfo.new(0.3),
            {BackgroundTransparency = 1}
        ):Play()
        
        game:GetService("Debris"):AddItem(flash, 0.3)
    end
    
    return clamped
end

CameraConstraints.rotationLimits = {minPitch = -80, maxPitch = 80}

function CameraConstraints.SetRotationLimits(minPitch, maxPitch)
    CameraConstraints.rotationLimits.minPitch = math.rad(minPitch)
    CameraConstraints.rotationLimits.maxPitch = math.rad(maxPitch)
end

function CameraConstraints.ApplyRotationLimits(cframe)
    local x, y, z = cframe:ToEulerAnglesYXZ()
    
    -- Clamp pitch
    y = math.clamp(
        y,
        CameraConstraints.rotationLimits.minPitch,
        CameraConstraints.rotationLimits.maxPitch
    )
    
    -- Reconstruct CFrame with limited rotation
    return CFrame.new(cframe.Position) * CFrame.fromEulerAnglesYXZ(x, y, z)
end

-- TODO: Implement camera effects
local CameraEffects = {}

local blurEffect = nil

function CameraEffects.ApplyBlur(amount, focusDistance)
    amount = math.clamp(amount or 0, 0, 20)
    focusDistance = focusDistance or 10
    
    if not blurEffect then
        blurEffect = Instance.new("DepthOfFieldEffect")
        blurEffect.Parent = game.Lighting
    end
    
    -- Set blur properties
    blurEffect.FarIntensity = amount / 20
    blurEffect.FocusDistance = focusDistance
    blurEffect.InFocusRadius = 10
    blurEffect.NearIntensity = amount / 40
    
    -- Smooth transition
    if amount > 0 then
        blurEffect.Enabled = true
        TweenService:Create(
            blurEffect,
            TweenInfo.new(0.5),
            {FarIntensity = amount / 20}
        ):Play()
    else
        TweenService:Create(
            blurEffect,
            TweenInfo.new(0.5),
            {FarIntensity = 0}
        ):Play()
        wait(0.5)
        blurEffect.Enabled = false
    end
end

local vignetteGui = nil

function CameraEffects.ApplyVignette(intensity)
    intensity = math.clamp(intensity or 0, 0, 1)
    
    local playerGui = player:WaitForChild("PlayerGui")
    
    if not vignetteGui then
        vignetteGui = Instance.new("ScreenGui")
        vignetteGui.Name = "VignetteEffect"
        vignetteGui.Parent = playerGui
        
        local vignette = Instance.new("ImageLabel")
        vignette.Name = "Vignette"
        vignette.Size = UDim2.new(1, 0, 1, 0)
        vignette.BackgroundTransparency = 1
        vignette.Image = "rbxasset://textures/ui/LuaApp/graphic/MenuSelectionHighlight.png"
        vignette.ImageColor3 = Color3.new(0, 0, 0)
        vignette.ImageTransparency = 1
        vignette.Parent = vignetteGui
    end
    
    local vignette = vignetteGui:FindFirstChild("Vignette")
    if vignette then
        if intensity > 0 then
            vignetteGui.Enabled = true
            TweenService:Create(
                vignette,
                TweenInfo.new(0.5),
                {ImageTransparency = 1 - intensity}
            ):Play()
        else
            TweenService:Create(
                vignette,
                TweenInfo.new(0.5),
                {ImageTransparency = 1}
            ):Play()
            wait(0.5)
            vignetteGui.Enabled = false
        end
    end
end

-- Additional camera effects
function CameraEffects.ApplyChromaticAberration(amount)
    local colorCorrection = game.Lighting:FindFirstChild("ChromaticAberration") or Instance.new("ColorCorrectionEffect")
    colorCorrection.Name = "ChromaticAberration"
    colorCorrection.Parent = game.Lighting
    
    if amount > 0 then
        colorCorrection.Enabled = true
        colorCorrection.TintColor = Color3.new(1 + amount * 0.1, 1, 1 - amount * 0.1)
    else
        colorCorrection.Enabled = false
    end
end

-- TODO: Implement camera save/load system
local CameraSaveSystem = {}

function CameraSaveSystem.SaveCameraState()
    local state = {
        mode = currentMode,
        cframe = camera.CFrame,
        fov = camera.FieldOfView,
        settings = cameraSettings,
        effects = {
            blur = blurEffect and blurEffect.FarIntensity or 0,
            vignette = vignetteGui and vignetteGui.Enabled or false,
            shake = #activeShakes
        },
        timestamp = tick()
    }
    
    -- Save to datastore if needed
    game.ReplicatedStorage:WaitForChild("SaveCameraState"):FireServer(state)
    
    return state
end

function CameraSaveSystem.LoadCameraState(state)
    if not state then
        warn("No camera state to load")
        return
    end
    
    -- Restore camera position and FOV
    camera.CFrame = state.cframe
    camera.FieldOfView = state.fov
    
    -- Restore camera mode
    SwitchCameraMode(state.mode)
    
    -- Restore settings
    if state.settings then
        for key, value in pairs(state.settings) do
            cameraSettings[key] = value
        end
    end
    
    -- Restore effects
    if state.effects then
        if state.effects.blur then
            CameraEffects.ApplyBlur(state.effects.blur * 20)
        end
        if state.effects.vignette then
            CameraEffects.ApplyVignette(1)
        end
    end
    
    print("Camera state loaded from", os.date("%c", state.timestamp))
end

-- Auto-save camera state periodically
spawn(function()
    while wait(30) do -- Save every 30 seconds
        CameraSaveSystem.SaveCameraState()
    end
end)

-- TODO: Main camera update loop
RunService.RenderStepped:Connect(function(deltaTime)
    -- Update camera based on current mode
    if currentMode == CameraModes.DEFAULT then
        UpdateDefaultCamera()
    elseif currentMode == CameraModes.FIXED then
        UpdateFixedCamera()
    elseif currentMode == CameraModes.ORBIT then
        UpdateOrbitCamera()
    elseif currentMode == CameraModes.OVERVIEW then
        UpdateOverviewCamera()
    elseif currentMode == CameraModes.FIRST_PERSON then
        UpdateFirstPersonCamera()
    elseif currentMode == CameraModes.PRESENTATION then
        UpdatePresentationCamera()
    elseif currentMode == CameraModes.FOLLOW then
        -- Follow mode implementation
        if cameraSettings.currentTarget then
            local targetPos = cameraSettings.currentTarget.Position
            local offset = cameraSettings.currentOffset
            local desiredCFrame = CFrame.lookAt(
                targetPos + offset,
                targetPos
            )
            camera.CFrame = camera.CFrame:Lerp(desiredCFrame, cameraDefaults.smoothSpeed)
        else
            UpdateDefaultCamera()
        end
    elseif currentMode == CameraModes.CINEMATIC then
        -- Cinematic mode handled by CinematicCamera.PlayCinematic()
    end
    
    -- Apply camera shake
    CameraShake.Update(deltaTime)
    
    -- Apply constraints
    if CameraConstraints.boundaries.min and CameraConstraints.boundaries.max then
        local constrainedPos = CameraConstraints.ApplyBoundaries(camera.CFrame.Position)
        if constrainedPos ~= camera.CFrame.Position then
            camera.CFrame = CFrame.new(constrainedPos) * (camera.CFrame - camera.CFrame.Position)
        end
    end
    
    -- Apply rotation limits
    camera.CFrame = CameraConstraints.ApplyRotationLimits(camera.CFrame)
end)

-- TODO: Handle camera input controls
UserInputService.InputBegan:Connect(function(input, gameProcessed)
    if gameProcessed then return end
    
    -- Camera mode switching with number keys
    if input.KeyCode == Enum.KeyCode.One then
        SwitchCameraMode(CameraModes.DEFAULT)
    elseif input.KeyCode == Enum.KeyCode.Two then
        SwitchCameraMode(CameraModes.FIRST_PERSON)
    elseif input.KeyCode == Enum.KeyCode.Three then
        SwitchCameraMode(CameraModes.ORBIT)
    elseif input.KeyCode == Enum.KeyCode.Four then
        SwitchCameraMode(CameraModes.OVERVIEW)
    elseif input.KeyCode == Enum.KeyCode.Five then
        SwitchCameraMode(CameraModes.FIXED)
    elseif input.KeyCode == Enum.KeyCode.Six then
        SwitchCameraMode(CameraModes.PRESENTATION)
    
    -- Reset camera with R key
    elseif input.KeyCode == Enum.KeyCode.R then
        camera.CFrame = CFrame.lookAt(
            character.HumanoidRootPart.Position + cameraDefaults.defaultOffset,
            character.HumanoidRootPart.Position
        )
        camera.FieldOfView = cameraDefaults.fieldOfView
        cameraSettings.currentZoom = 20
        cameraSettings.currentOffset = cameraDefaults.defaultOffset
    
    -- Toggle free cam with F key
    elseif input.KeyCode == Enum.KeyCode.F and UserInputService:IsKeyDown(Enum.KeyCode.LeftControl) then
        if currentMode ~= CameraModes.FOLLOW then
            local previousMode = currentMode
            SwitchCameraMode(CameraModes.FOLLOW)
            cameraSettings.previousMode = previousMode
        else
            SwitchCameraMode(cameraSettings.previousMode or CameraModes.DEFAULT)
        end
    
    -- Save camera state with F5
    elseif input.KeyCode == Enum.KeyCode.F5 then
        local state = CameraSaveSystem.SaveCameraState()
        print("Camera state saved")
    
    -- Load camera state with F6
    elseif input.KeyCode == Enum.KeyCode.F6 then
        -- Load last saved state
        game.ReplicatedStorage:WaitForChild("LoadCameraState"):FireServer()
    
    -- Toggle smoothing with S key
    elseif input.KeyCode == Enum.KeyCode.S and UserInputService:IsKeyDown(Enum.KeyCode.LeftControl) then
        cameraSettings.smoothingEnabled = not cameraSettings.smoothingEnabled
        print("Camera smoothing:", cameraSettings.smoothingEnabled)
    
    -- Add test shake with K key
    elseif input.KeyCode == Enum.KeyCode.K then
        CameraShake.Shake(1, 0.5, 30)
    end
end)

-- Handle zoom with mouse wheel
UserInputService.InputChanged:Connect(function(input, gameProcessed)
    if gameProcessed then return end
    
    if input.UserInputType == Enum.UserInputType.MouseWheel then
        local zoom = input.Position.Z
        cameraSettings.currentZoom = math.clamp(
            cameraSettings.currentZoom - zoom * cameraDefaults.zoomSpeed,
            cameraDefaults.minZoom,
            cameraDefaults.maxZoom
        )
        
        -- Update offset magnitude
        local direction = cameraSettings.currentOffset.Unit
        cameraSettings.currentOffset = direction * cameraSettings.currentZoom
    end
end)

-- Handle character respawn
player.CharacterAdded:Connect(function(newCharacter)
    character = newCharacter
    humanoid = character:WaitForChild("Humanoid")
    
    -- Reset camera to default
    wait(0.1) -- Wait for character to fully load
    camera.CameraType = Enum.CameraType.Scriptable
    SwitchCameraMode(CameraModes.DEFAULT)
    
    -- Reset first person transparency if needed
    if currentMode ~= CameraModes.FIRST_PERSON then
        ResetCharacterTransparency()
    end
end)

-- Clean up on mode change
local lastMode = currentMode
RunService.Heartbeat:Connect(function()
    if lastMode ~= currentMode then
        -- Clean up previous mode
        if lastMode == CameraModes.FIRST_PERSON then
            ResetCharacterTransparency()
        elseif lastMode == CameraModes.OVERVIEW then
            local playerGui = player:WaitForChild("PlayerGui")
            local gridGui = playerGui:FindFirstChild("GridOverlay")
            if gridGui then
                gridGui:Destroy()
            end
        elseif lastMode == CameraModes.PRESENTATION then
            local playerGui = player:WaitForChild("PlayerGui")
            local presentGui = playerGui:FindFirstChild("PresentationUI")
            if presentGui then
                presentGui:Destroy()
            end
        end
        
        lastMode = currentMode
    end
end)

-- Export camera controller for other scripts
_G.CameraController = {
    SwitchMode = SwitchCameraMode,
    Shake = CameraShake.Shake,
    Focus = CameraFocus,
    Effects = CameraEffects,
    Transition = CameraTransition,
    Cinematic = CinematicCamera,
    SaveState = CameraSaveSystem.SaveCameraState,
    LoadState = CameraSaveSystem.LoadCameraState,
    GetCurrentMode = function() return currentMode end,
    SetTarget = function(target) cameraSettings.currentTarget = target end
}

print("CameraController initialized")
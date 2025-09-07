--[[
    Input.client.lua
    Client-side input handling for educational interactions
    
    Manages keyboard, mouse, touch, and gamepad input for
    educational activities and UI interactions
]]

local Players = game:GetService("Players")
local UserInputService = game:GetService("UserInputService")
local ContextActionService = game:GetService("ContextActionService")
local GuiService = game:GetService("GuiService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local player = Players.LocalPlayer
local mouse = player:GetMouse()

-- Initialize input system
local inputConnections = {}
local touchTracker = {}
local gestureHistory = {}
local keyStates = {}
local modifierKeys = {shift = false, ctrl = false, alt = false}
local interactableObjects = {}
local inputEnabled = true
local debugMode = false

-- TODO: Implement keyboard input handling
-- @param input: InputObject - The input object from UserInputService
-- @param gameProcessed: boolean - Whether GUI processed the input
UserInputService.InputBegan:Connect(function(input, gameProcessed)
    -- Skip if GUI processed or input disabled
    if gameProcessed or not inputEnabled then return end
    
    -- Record input for replay system
    if isRecording then
        table.insert(recordedInputs, {
            type = "InputBegan",
            input = input.KeyCode or input.UserInputType,
            timestamp = tick()
        })
    end
    
    if input.UserInputType == Enum.UserInputType.Keyboard then
        local keyCode = input.KeyCode
        keyStates[keyCode] = true
        
        -- Update modifier keys
        if keyCode == Enum.KeyCode.LeftShift or keyCode == Enum.KeyCode.RightShift then
            modifierKeys.shift = true
        elseif keyCode == Enum.KeyCode.LeftControl or keyCode == Enum.KeyCode.RightControl then
            modifierKeys.ctrl = true
        elseif keyCode == Enum.KeyCode.LeftAlt or keyCode == Enum.KeyCode.RightAlt then
            modifierKeys.alt = true
        end
        
        -- Quiz answer shortcuts (1-4 keys)
        if currentInputMode == InputModes.DEFAULT then
            if keyCode == Enum.KeyCode.One then
                ReplicatedStorage:WaitForChild("QuizAnswer"):FireServer(1)
            elseif keyCode == Enum.KeyCode.Two then
                ReplicatedStorage:WaitForChild("QuizAnswer"):FireServer(2)
            elseif keyCode == Enum.KeyCode.Three then
                ReplicatedStorage:WaitForChild("QuizAnswer"):FireServer(3)
            elseif keyCode == Enum.KeyCode.Four then
                ReplicatedStorage:WaitForChild("QuizAnswer"):FireServer(4)
            -- Tool switching
            elseif keyCode == Enum.KeyCode.Q then
                ReplicatedStorage:WaitForChild("SwitchTool"):FireServer("previous")
            elseif keyCode == Enum.KeyCode.E then
                ReplicatedStorage:WaitForChild("SwitchTool"):FireServer("next")
            -- Menu toggle
            elseif keyCode == Enum.KeyCode.Escape then
                ReplicatedStorage:WaitForChild("ToggleMenu"):FireServer()
            -- Help system
            elseif keyCode == Enum.KeyCode.H then
                ReplicatedStorage:WaitForChild("ShowHelp"):FireServer()
            -- Navigation
            elseif keyCode == Enum.KeyCode.Tab then
                ReplicatedStorage:WaitForChild("NavigateUI"):FireServer(modifierKeys.shift and "previous" or "next")
            end
        elseif currentInputMode == InputModes.TYPING then
            -- Text input mode for answers
            if keyCode == Enum.KeyCode.Return then
                ReplicatedStorage:WaitForChild("SubmitText"):FireServer()
            elseif keyCode == Enum.KeyCode.Escape then
                SwitchInputMode(InputModes.DEFAULT)
            end
        end
    elseif input.UserInputType == Enum.UserInputType.MouseButton1 then
        -- Handle mouse clicks
        local target = mouse.Target
        if target and target:FindFirstChild("Interactable") then
            ReplicatedStorage:WaitForChild("Interact"):FireServer(target)
        end
    elseif input.UserInputType == Enum.UserInputType.MouseButton2 then
        -- Right-click context menu
        local target = mouse.Target
        if target then
            ReplicatedStorage:WaitForChild("ContextMenu"):FireServer(target, mouse.X, mouse.Y)
        end
    end
end)

-- Handle input release
UserInputService.InputEnded:Connect(function(input, gameProcessed)
    if gameProcessed or not inputEnabled then return end
    
    if input.UserInputType == Enum.UserInputType.Keyboard then
        local keyCode = input.KeyCode
        keyStates[keyCode] = false
        
        -- Update modifier keys
        if keyCode == Enum.KeyCode.LeftShift or keyCode == Enum.KeyCode.RightShift then
            modifierKeys.shift = false
        elseif keyCode == Enum.KeyCode.LeftControl or keyCode == Enum.KeyCode.RightControl then
            modifierKeys.ctrl = false
        elseif keyCode == Enum.KeyCode.LeftAlt or keyCode == Enum.KeyCode.RightAlt then
            modifierKeys.alt = false
        end
    end
end)

-- TODO: Implement mouse input handling
-- @param input: InputObject - The input object
-- Variables for drag and drop
local isDragging = false
local dragObject = nil
local dragStartPos = nil
local dragConnection = nil

UserInputService.InputChanged:Connect(function(input)
    if not inputEnabled then return end
    
    if input.UserInputType == Enum.UserInputType.MouseMovement then
        -- Track mouse position for hover effects
        local target = mouse.Target
        if target and target:FindFirstChild("Hoverable") then
            -- Apply hover effect
            if target:FindFirstChild("SelectionBox") then
                target.SelectionBox.Visible = true
            else
                local selectionBox = Instance.new("SelectionBox")
                selectionBox.Adornee = target
                selectionBox.Color3 = Color3.new(0, 0.5, 1)
                selectionBox.LineThickness = 0.1
                selectionBox.Parent = target
            end
        else
            -- Remove hover effects from previous target
            for _, obj in pairs(workspace:GetDescendants()) do
                if obj:IsA("SelectionBox") and obj.Parent ~= dragObject then
                    obj:Destroy()
                end
            end
        end
        
        -- Handle drag and drop
        if isDragging and dragObject then
            local ray = workspace.CurrentCamera:ScreenPointToRay(input.Position.X, input.Position.Y)
            local hit, pos = workspace:FindPartOnRay(Ray.new(ray.Origin, ray.Direction * 1000))
            if dragObject:IsA("BasePart") then
                dragObject.Position = pos + Vector3.new(0, dragObject.Size.Y/2, 0)
            end
        end
    elseif input.UserInputType == Enum.UserInputType.MouseWheel then
        -- Handle scrolling
        local scrollDirection = input.Position.Z
        ReplicatedStorage:WaitForChild("ScrollUI"):FireServer(scrollDirection)
        
        -- Camera zoom for 3D environments
        if currentInputMode == InputModes.DEFAULT then
            local camera = workspace.CurrentCamera
            local currentZoom = (camera.CFrame.Position - camera.Focus.Position).Magnitude
            local newZoom = math.clamp(currentZoom - scrollDirection * 2, 5, 100)
            camera.CFrame = camera.CFrame * CFrame.new(0, 0, scrollDirection * 2)
        end
    end
end)

-- Mouse button events for drag and drop
mouse.Button1Down:Connect(function()
    if not inputEnabled or currentInputMode ~= InputModes.DEFAULT then return end
    
    local target = mouse.Target
    if target and target:FindFirstChild("Draggable") then
        isDragging = true
        dragObject = target
        dragStartPos = target.Position
        
        -- Visual feedback
        local selectionBox = Instance.new("SelectionBox")
        selectionBox.Adornee = target
        selectionBox.Color3 = Color3.new(0, 1, 0)
        selectionBox.LineThickness = 0.15
        selectionBox.Parent = target
    end
end)

mouse.Button1Up:Connect(function()
    if isDragging and dragObject then
        -- Check for valid drop target
        local dropTarget = mouse.Target
        if dropTarget and dropTarget:FindFirstChild("DropZone") then
            ReplicatedStorage:WaitForChild("DropItem"):FireServer(dragObject, dropTarget)
        else
            -- Return to original position if invalid drop
            if dragStartPos then
                dragObject.Position = dragStartPos
            end
        end
        
        -- Clean up
        if dragObject:FindFirstChild("SelectionBox") then
            dragObject.SelectionBox:Destroy()
        end
        isDragging = false
        dragObject = nil
        dragStartPos = nil
    end
end)

-- TODO: Implement touch input handling for mobile devices
-- Touch handling variables
local activeTouches = {}
local touchStartTime = {}
local touchStartPositions = {}
local pinchStartDistance = nil

UserInputService.TouchStarted:Connect(function(touch, gameProcessed)
    if gameProcessed or not inputEnabled then return end
    
    local touchId = touch.Id
    activeTouches[touchId] = touch
    touchStartTime[touchId] = tick()
    touchStartPositions[touchId] = touch.Position
    
    -- Check for multi-touch gestures
    local touchCount = 0
    for _ in pairs(activeTouches) do
        touchCount = touchCount + 1
    end
    
    if touchCount == 2 then
        -- Initialize pinch gesture
        local touches = {}
        for _, t in pairs(activeTouches) do
            table.insert(touches, t)
        end
        if #touches >= 2 then
            local dist = (touches[1].Position - touches[2].Position).Magnitude
            pinchStartDistance = dist
        end
    elseif touchCount == 1 then
        -- Single touch - check for tap target
        local ray = workspace.CurrentCamera:ScreenPointToRay(touch.Position.X, touch.Position.Y)
        local hit, pos = workspace:FindPartOnRay(Ray.new(ray.Origin, ray.Direction * 1000))
        if hit and hit:FindFirstChild("Touchable") then
            ReplicatedStorage:WaitForChild("TouchInteract"):FireServer(hit)
        end
    end
end)

UserInputService.TouchEnded:Connect(function(touch, gameProcessed)
    if gameProcessed then return end
    
    local touchId = touch.Id
    local startTime = touchStartTime[touchId]
    local startPos = touchStartPositions[touchId]
    
    if startTime and startPos then
        local duration = tick() - startTime
        local endPos = touch.Position
        local distance = (endPos - startPos).Magnitude
        
        -- Detect gesture type
        if duration < 0.3 and distance < 20 then
            -- Tap gesture
            ReplicatedStorage:WaitForChild("TouchTap"):FireServer(endPos.X, endPos.Y)
        elseif distance > 50 then
            -- Swipe gesture
            local swipeType = GestureRecognizer.DetectSwipe(startPos, endPos, duration)
            if swipeType then
                ReplicatedStorage:WaitForChild("TouchSwipe"):FireServer(swipeType)
            end
        end
    end
    
    -- Clean up
    activeTouches[touchId] = nil
    touchStartTime[touchId] = nil
    touchStartPositions[touchId] = nil
    
    -- Reset pinch if no more multi-touch
    local touchCount = 0
    for _ in pairs(activeTouches) do
        touchCount = touchCount + 1
    end
    if touchCount < 2 then
        pinchStartDistance = nil
    end
end)

UserInputService.TouchMoved:Connect(function(touch, gameProcessed)
    if gameProcessed or not inputEnabled then return end
    
    local touchCount = 0
    local touches = {}
    for _, t in pairs(activeTouches) do
        touchCount = touchCount + 1
        table.insert(touches, t)
    end
    
    if touchCount == 2 and pinchStartDistance then
        -- Handle pinch zoom
        if #touches >= 2 then
            local currentDist = (touches[1].Position - touches[2].Position).Magnitude
            local zoomFactor = currentDist / pinchStartDistance
            ReplicatedStorage:WaitForChild("TouchZoom"):FireServer(zoomFactor)
            pinchStartDistance = currentDist
        end
    elseif touchCount == 1 then
        -- Handle drag
        local touchId = touch.Id
        if touchStartPositions[touchId] then
            local delta = touch.Position - touchStartPositions[touchId]
            if delta.Magnitude > 10 then
                ReplicatedStorage:WaitForChild("TouchDrag"):FireServer(delta.X, delta.Y)
                touchStartPositions[touchId] = touch.Position
            end
        end
    end
end)

-- TODO: Implement gamepad support
-- Gamepad variables
local connectedGamepads = {}
local gamepadDeadzone = 0.2

UserInputService.GamepadConnected:Connect(function(gamepad)
    connectedGamepads[gamepad] = true
    
    -- Show gamepad UI hints
    ReplicatedStorage:WaitForChild("ShowGamepadHints"):FireServer(true)
    
    -- Configure gamepad input handling
    UserInputService.InputBegan:Connect(function(input, gameProcessed)
        if input.UserInputType == Enum.UserInputType.Gamepad1 and not gameProcessed then
            -- Button mappings
            if input.KeyCode == Enum.KeyCode.ButtonA then
                -- Confirm/Select
                ReplicatedStorage:WaitForChild("GamepadAction"):FireServer("confirm")
            elseif input.KeyCode == Enum.KeyCode.ButtonB then
                -- Cancel/Back
                ReplicatedStorage:WaitForChild("GamepadAction"):FireServer("cancel")
            elseif input.KeyCode == Enum.KeyCode.ButtonX then
                -- Interact
                ContextActionService:GetButton("InteractWithObject"):Click()
            elseif input.KeyCode == Enum.KeyCode.ButtonY then
                -- Special action
                ReplicatedStorage:WaitForChild("GamepadAction"):FireServer("special")
            elseif input.KeyCode == Enum.KeyCode.ButtonL1 then
                -- Previous tool
                ReplicatedStorage:WaitForChild("SwitchTool"):FireServer("previous")
            elseif input.KeyCode == Enum.KeyCode.ButtonR1 then
                -- Next tool
                ReplicatedStorage:WaitForChild("SwitchTool"):FireServer("next")
            elseif input.KeyCode == Enum.KeyCode.ButtonL2 then
                -- Secondary action
                ReplicatedStorage:WaitForChild("GamepadAction"):FireServer("secondary")
            elseif input.KeyCode == Enum.KeyCode.ButtonR2 then
                -- Primary action
                ReplicatedStorage:WaitForChild("GamepadAction"):FireServer("primary")
            elseif input.KeyCode == Enum.KeyCode.DPadUp then
                -- Navigate up
                ReplicatedStorage:WaitForChild("NavigateUI"):FireServer("up")
            elseif input.KeyCode == Enum.KeyCode.DPadDown then
                -- Navigate down
                ReplicatedStorage:WaitForChild("NavigateUI"):FireServer("down")
            elseif input.KeyCode == Enum.KeyCode.DPadLeft then
                -- Navigate left
                ReplicatedStorage:WaitForChild("NavigateUI"):FireServer("left")
            elseif input.KeyCode == Enum.KeyCode.DPadRight then
                -- Navigate right
                ReplicatedStorage:WaitForChild("NavigateUI"):FireServer("right")
            elseif input.KeyCode == Enum.KeyCode.ButtonStart then
                -- Menu
                ReplicatedStorage:WaitForChild("ToggleMenu"):FireServer()
            elseif input.KeyCode == Enum.KeyCode.ButtonSelect then
                -- Map/Help
                ReplicatedStorage:WaitForChild("ShowHelp"):FireServer()
            end
        end
    end)
    
    -- Analog stick handling
    RunService.Heartbeat:Connect(function()
        if not connectedGamepads[Enum.UserInputType.Gamepad1] then return end
        
        local gamepadState = UserInputService:GetGamepadState(Enum.UserInputType.Gamepad1)
        for _, input in pairs(gamepadState) do
            if input.KeyCode == Enum.KeyCode.Thumbstick1 then
                -- Left stick - movement
                local x = input.Position.X
                local y = input.Position.Y
                if math.abs(x) > gamepadDeadzone or math.abs(y) > gamepadDeadzone then
                    ReplicatedStorage:WaitForChild("GamepadMove"):FireServer(x, y)
                end
            elseif input.KeyCode == Enum.KeyCode.Thumbstick2 then
                -- Right stick - camera
                local x = input.Position.X
                local y = input.Position.Y
                if math.abs(x) > gamepadDeadzone or math.abs(y) > gamepadDeadzone then
                    ReplicatedStorage:WaitForChild("GamepadCamera"):FireServer(x, y)
                end
            end
        end
    end)
end)

UserInputService.GamepadDisconnected:Connect(function(gamepad)
    connectedGamepads[gamepad] = nil
    ReplicatedStorage:WaitForChild("ShowGamepadHints"):FireServer(false)
end)

-- TODO: Implement context actions for specific interactions
local function SetupContextActions()
    -- Interact with objects
    ContextActionService:BindAction("InteractWithObject", function(actionName, inputState, inputObject)
        if inputState == Enum.UserInputState.Begin and inputEnabled then
            -- Find nearest interactable object
            local character = player.Character
            if not character or not character:FindFirstChild("HumanoidRootPart") then return end
            
            local rootPart = character.HumanoidRootPart
            local nearestObject = nil
            local nearestDistance = math.huge
            
            for _, obj in pairs(workspace:GetDescendants()) do
                if obj:FindFirstChild("Interactable") and obj:IsA("BasePart") then
                    local distance = (obj.Position - rootPart.Position).Magnitude
                    if distance < 10 and distance < nearestDistance then
                        nearestObject = obj
                        nearestDistance = distance
                    end
                end
            end
            
            if nearestObject then
                -- Show interaction feedback
                local billboard = Instance.new("BillboardGui")
                billboard.Size = UDim2.new(4, 0, 1, 0)
                billboard.StudsOffset = Vector3.new(0, 3, 0)
                billboard.Parent = nearestObject
                
                local text = Instance.new("TextLabel")
                text.Text = "Interacting..."
                text.TextScaled = true
                text.BackgroundTransparency = 1
                text.TextColor3 = Color3.new(0, 1, 0)
                text.Parent = billboard
                
                -- Fire interaction event
                ReplicatedStorage:WaitForChild("Interact"):FireServer(nearestObject)
                
                -- Remove feedback after delay
                wait(1)
                billboard:Destroy()
            end
        end
    end, false, Enum.KeyCode.F, Enum.KeyCode.ButtonX)
    
    -- Sprint action
    ContextActionService:BindAction("Sprint", function(actionName, inputState, inputObject)
        if inputEnabled then
            ReplicatedStorage:WaitForChild("Sprint"):FireServer(inputState == Enum.UserInputState.Begin)
        end
    end, false, Enum.KeyCode.LeftShift, Enum.KeyCode.ButtonL3)
    
    -- Jump action (custom)
    ContextActionService:BindAction("CustomJump", function(actionName, inputState, inputObject)
        if inputState == Enum.UserInputState.Begin and inputEnabled then
            ReplicatedStorage:WaitForChild("CustomJump"):FireServer()
        end
    end, false, Enum.KeyCode.Space, Enum.KeyCode.ButtonA)
    
    -- Camera mode toggle
    ContextActionService:BindAction("ToggleCameraMode", function(actionName, inputState, inputObject)
        if inputState == Enum.UserInputState.Begin and inputEnabled then
            ReplicatedStorage:WaitForChild("ToggleCameraMode"):FireServer()
        end
    end, false, Enum.KeyCode.C, Enum.KeyCode.ButtonR3)
    
    -- Quick slot actions
    for i = 1, 9 do
        local keyCode = Enum.KeyCode[tostring(i)]
        ContextActionService:BindAction("QuickSlot" .. i, function(actionName, inputState, inputObject)
            if inputState == Enum.UserInputState.Begin and inputEnabled then
                ReplicatedStorage:WaitForChild("UseQuickSlot"):FireServer(i)
            end
        end, false, keyCode)
    end
end

-- TODO: Implement input mode management
local InputModes = {
    DEFAULT = "Default",
    TYPING = "Typing",
    DRAWING = "Drawing",
    BUILDING = "Building"
}

local currentInputMode = InputModes.DEFAULT

-- TODO: Function to switch input modes
-- @param mode: string - The input mode to switch to
local function SwitchInputMode(mode)
    if not InputModes[mode] then
        warn("Invalid input mode: " .. tostring(mode))
        return
    end
    
    local previousMode = currentInputMode
    currentInputMode = mode
    
    -- Update key bindings based on mode
    if mode == InputModes.TYPING then
        -- Disable movement and action keys
        ContextActionService:UnbindAction("InteractWithObject")
        ContextActionService:UnbindAction("Sprint")
        ContextActionService:UnbindAction("CustomJump")
        
        -- Enable text cursor
        UserInputService.MouseIconEnabled = true
        
    elseif mode == InputModes.DRAWING then
        -- Set up drawing controls
        UserInputService.MouseIconEnabled = false
        mouse.Icon = "rbxasset://textures/ui/MouseLockedCursor.png"
        
    elseif mode == InputModes.BUILDING then
        -- Enable building controls
        ContextActionService:BindAction("PlaceBlock", function(actionName, inputState, inputObject)
            if inputState == Enum.UserInputState.Begin then
                ReplicatedStorage:WaitForChild("PlaceBlock"):FireServer(mouse.Hit.Position)
            end
        end, false, Enum.KeyCode.E, Enum.KeyCode.ButtonY)
        
        ContextActionService:BindAction("RemoveBlock", function(actionName, inputState, inputObject)
            if inputState == Enum.UserInputState.Begin then
                ReplicatedStorage:WaitForChild("RemoveBlock"):FireServer(mouse.Target)
            end
        end, false, Enum.KeyCode.R, Enum.KeyCode.ButtonB)
        
    else -- DEFAULT mode
        -- Re-enable all standard controls
        SetupContextActions()
        UserInputService.MouseIconEnabled = false
    end
    
    -- Update UI to show current mode
    local playerGui = player:WaitForChild("PlayerGui")
    local inputModeGui = playerGui:FindFirstChild("InputModeDisplay")
    if not inputModeGui then
        inputModeGui = Instance.new("ScreenGui")
        inputModeGui.Name = "InputModeDisplay"
        inputModeGui.Parent = playerGui
        
        local frame = Instance.new("Frame")
        frame.Size = UDim2.new(0.15, 0, 0.05, 0)
        frame.Position = UDim2.new(0.85, 0, 0.05, 0)
        frame.BackgroundColor3 = Color3.new(0, 0, 0)
        frame.BackgroundTransparency = 0.3
        frame.Parent = inputModeGui
        
        local label = Instance.new("TextLabel")
        label.Name = "ModeLabel"
        label.Size = UDim2.new(1, 0, 1, 0)
        label.BackgroundTransparency = 1
        label.TextScaled = true
        label.TextColor3 = Color3.new(1, 1, 1)
        label.Parent = frame
    end
    
    local modeLabel = inputModeGui:FindFirstDescendant("ModeLabel")
    if modeLabel then
        modeLabel.Text = "Mode: " .. mode
    end
    
    -- Notify other systems
    ReplicatedStorage:WaitForChild("InputModeChanged"):FireServer(mode, previousMode)
end

-- Export function for other scripts
_G.SwitchInputMode = SwitchInputMode

-- TODO: Implement gesture recognition system
local GestureRecognizer = {}

function GestureRecognizer.DetectSwipe(startPos, endPos, duration)
    local delta = endPos - startPos
    local distance = delta.Magnitude
    local velocity = distance / duration
    
    -- Minimum thresholds
    local minDistance = 50
    local minVelocity = 100
    
    if distance < minDistance or velocity < minVelocity then
        return nil
    end
    
    -- Determine swipe direction
    local absX = math.abs(delta.X)
    local absY = math.abs(delta.Y)
    
    if absX > absY then
        -- Horizontal swipe
        if delta.X > 0 then
            return "right"
        else
            return "left"
        end
    else
        -- Vertical swipe
        if delta.Y > 0 then
            return "down"
        else
            return "up"
        end
    end
end

function GestureRecognizer.DetectPinch(touch1, touch2)
    if not touch1 or not touch2 then
        return 1.0
    end
    
    -- Calculate current distance between touches
    local currentDistance = (touch1.Position - touch2.Position).Magnitude
    
    -- Store previous distance for comparison
    if not GestureRecognizer.previousPinchDistance then
        GestureRecognizer.previousPinchDistance = currentDistance
        return 1.0
    end
    
    -- Calculate zoom factor
    local zoomFactor = currentDistance / GestureRecognizer.previousPinchDistance
    GestureRecognizer.previousPinchDistance = currentDistance
    
    -- Clamp zoom factor to reasonable range
    zoomFactor = math.clamp(zoomFactor, 0.5, 2.0)
    
    return zoomFactor
end

-- Additional gesture detection methods
function GestureRecognizer.DetectRotation(touch1, touch2)
    if not touch1 or not touch2 then
        return 0
    end
    
    local currentAngle = math.atan2(
        touch2.Position.Y - touch1.Position.Y,
        touch2.Position.X - touch1.Position.X
    )
    
    if not GestureRecognizer.previousRotationAngle then
        GestureRecognizer.previousRotationAngle = currentAngle
        return 0
    end
    
    local rotation = currentAngle - GestureRecognizer.previousRotationAngle
    GestureRecognizer.previousRotationAngle = currentAngle
    
    return rotation
end

function GestureRecognizer.DetectLongPress(startTime, position)
    local duration = tick() - startTime
    local longPressThreshold = 0.5 -- seconds
    
    return duration >= longPressThreshold
end

-- TODO: Implement input recording for tutorials
local InputRecorder = {}
local recordedInputs = {}
local isRecording = false

function InputRecorder.StartRecording()
    -- Clear previous recordings
    recordedInputs = {}
    InputRecorder.recordingStartTime = tick()
    
    -- Set recording flag
    isRecording = true
    
    -- Show recording indicator
    local playerGui = player:WaitForChild("PlayerGui")
    local recordingGui = Instance.new("ScreenGui")
    recordingGui.Name = "RecordingIndicator"
    recordingGui.Parent = playerGui
    
    local frame = Instance.new("Frame")
    frame.Size = UDim2.new(0.1, 0, 0.05, 0)
    frame.Position = UDim2.new(0.45, 0, 0.02, 0)
    frame.BackgroundColor3 = Color3.new(1, 0, 0)
    frame.Parent = recordingGui
    
    local label = Instance.new("TextLabel")
    label.Text = "● RECORDING"
    label.Size = UDim2.new(1, 0, 1, 0)
    label.BackgroundTransparency = 1
    label.TextScaled = true
    label.TextColor3 = Color3.new(1, 1, 1)
    label.Parent = frame
    
    -- Pulse animation
    local tweenService = game:GetService("TweenService")
    local tween = tweenService:Create(
        frame,
        TweenInfo.new(0.5, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true),
        {BackgroundTransparency = 0.5}
    )
    tween:Play()
    
    print("Input recording started")
end

function InputRecorder.StopRecording()
    -- Set recording flag to false
    isRecording = false
    
    -- Calculate recording duration
    local duration = tick() - (InputRecorder.recordingStartTime or 0)
    
    -- Process recorded inputs
    local processedInputs = {
        duration = duration,
        inputs = recordedInputs,
        metadata = {
            player = player.Name,
            timestamp = os.time(),
            inputMode = currentInputMode
        }
    }
    
    -- Save to replay system
    ReplicatedStorage:WaitForChild("SaveRecording"):FireServer(processedInputs)
    
    -- Remove recording indicator
    local playerGui = player:WaitForChild("PlayerGui")
    local recordingGui = playerGui:FindFirstChild("RecordingIndicator")
    if recordingGui then
        recordingGui:Destroy()
    end
    
    print("Input recording stopped. Recorded " .. #recordedInputs .. " inputs over " .. duration .. " seconds")
    
    return processedInputs
end

function InputRecorder.PlaybackInputs(inputs)
    if not inputs or not inputs.inputs then
        warn("No inputs to playback")
        return
    end
    
    -- Disable player input during playback
    inputEnabled = false
    
    -- Show playback indicator
    local playerGui = player:WaitForChild("PlayerGui")
    local playbackGui = Instance.new("ScreenGui")
    playbackGui.Name = "PlaybackIndicator"
    playbackGui.Parent = playerGui
    
    local frame = Instance.new("Frame")
    frame.Size = UDim2.new(0.15, 0, 0.05, 0)
    frame.Position = UDim2.new(0.425, 0, 0.02, 0)
    frame.BackgroundColor3 = Color3.new(0, 0.5, 1)
    frame.Parent = playbackGui
    
    local label = Instance.new("TextLabel")
    label.Text = "▶ PLAYBACK"
    label.Size = UDim2.new(1, 0, 1, 0)
    label.BackgroundTransparency = 1
    label.TextScaled = true
    label.TextColor3 = Color3.new(1, 1, 1)
    label.Parent = frame
    
    -- Progress bar
    local progressBar = Instance.new("Frame")
    progressBar.Size = UDim2.new(0, 0, 0.2, 0)
    progressBar.Position = UDim2.new(0, 0, 0.8, 0)
    progressBar.BackgroundColor3 = Color3.new(0, 1, 0)
    progressBar.Parent = frame
    
    -- Playback coroutine
    coroutine.wrap(function()
        local startTime = tick()
        
        for i, input in ipairs(inputs.inputs) do
            -- Wait for correct timing
            local targetTime = input.timestamp - inputs.inputs[1].timestamp
            while tick() - startTime < targetTime do
                -- Update progress bar
                local progress = (tick() - startTime) / inputs.duration
                progressBar.Size = UDim2.new(progress, 0, 0.2, 0)
                RunService.Heartbeat:Wait()
            end
            
            -- Show visual indicator for input
            local indicator = Instance.new("BillboardGui")
            indicator.Size = UDim2.new(2, 0, 2, 0)
            indicator.StudsOffset = Vector3.new(0, 5, 0)
            indicator.Parent = workspace
            
            local text = Instance.new("TextLabel")
            text.Text = tostring(input.input)
            text.Size = UDim2.new(1, 0, 1, 0)
            text.BackgroundTransparency = 1
            text.TextScaled = true
            text.TextColor3 = Color3.new(1, 1, 0)
            text.Parent = indicator
            
            -- Simulate the input
            if input.type == "InputBegan" then
                -- Simulate key press or touch
                ReplicatedStorage:WaitForChild("SimulateInput"):FireServer(input)
            end
            
            -- Remove indicator after short delay
            game:GetService("Debris"):AddItem(indicator, 0.5)
        end
        
        -- Cleanup
        playbackGui:Destroy()
        inputEnabled = true
        print("Playback completed")
    end)()
end

-- Export for tutorial system
_G.InputRecorder = InputRecorder

-- TODO: Implement accessibility features
local AccessibilityHandler = {}

function AccessibilityHandler.EnableStickyKeys()
    AccessibilityHandler.stickyKeysEnabled = true
    AccessibilityHandler.stickyKeyStates = {}
    
    -- Override input handling for sticky keys
    local originalInputBegan = UserInputService.InputBegan
    UserInputService.InputBegan:Connect(function(input, gameProcessed)
        if not AccessibilityHandler.stickyKeysEnabled then return end
        
        if input.UserInputType == Enum.UserInputType.Keyboard then
            local keyCode = input.KeyCode
            
            -- Check if this is a modifier key
            local isModifier = keyCode == Enum.KeyCode.LeftShift or
                              keyCode == Enum.KeyCode.RightShift or
                              keyCode == Enum.KeyCode.LeftControl or
                              keyCode == Enum.KeyCode.RightControl or
                              keyCode == Enum.KeyCode.LeftAlt or
                              keyCode == Enum.KeyCode.RightAlt
            
            if isModifier then
                -- Toggle sticky state
                AccessibilityHandler.stickyKeyStates[keyCode] = not AccessibilityHandler.stickyKeyStates[keyCode]
                
                -- Show visual indicator
                AccessibilityHandler.ShowKeyStateIndicator(keyCode, AccessibilityHandler.stickyKeyStates[keyCode])
                
                -- Audio feedback
                local sound = Instance.new("Sound")
                sound.SoundId = AccessibilityHandler.stickyKeyStates[keyCode] and
                               "rbxasset://sounds/electronicpingshort.wav" or
                               "rbxasset://sounds/clickfast.wav"
                sound.Volume = 0.5
                sound.Parent = workspace
                sound:Play()
                game:GetService("Debris"):AddItem(sound, 2)
            end
        end
    end)
end

function AccessibilityHandler.ShowKeyStateIndicator(keyCode, isActive)
    local playerGui = player:WaitForChild("PlayerGui")
    local indicatorGui = playerGui:FindFirstChild("StickyKeyIndicators") or Instance.new("ScreenGui")
    indicatorGui.Name = "StickyKeyIndicators"
    indicatorGui.Parent = playerGui
    
    local keyName = tostring(keyCode):gsub("Enum.KeyCode.", "")
    local indicator = indicatorGui:FindFirstChild(keyName) or Instance.new("Frame")
    indicator.Name = keyName
    indicator.Size = UDim2.new(0.05, 0, 0.05, 0)
    indicator.BackgroundColor3 = isActive and Color3.new(0, 1, 0) or Color3.new(0.5, 0.5, 0.5)
    indicator.BorderSizePixel = 2
    indicator.Parent = indicatorGui
    
    -- Position based on key type
    local positions = {
        LeftShift = UDim2.new(0.1, 0, 0.9, 0),
        RightShift = UDim2.new(0.85, 0, 0.9, 0),
        LeftControl = UDim2.new(0.05, 0, 0.9, 0),
        RightControl = UDim2.new(0.9, 0, 0.9, 0),
        LeftAlt = UDim2.new(0.15, 0, 0.9, 0),
        RightAlt = UDim2.new(0.8, 0, 0.9, 0)
    }
    
    indicator.Position = positions[keyName:gsub("Left", ""):gsub("Right", "")] or UDim2.new(0.5, 0, 0.9, 0)
    
    local label = indicator:FindFirstChild("Label") or Instance.new("TextLabel")
    label.Name = "Label"
    label.Text = keyName:gsub("Left", "L-"):gsub("Right", "R-")
    label.Size = UDim2.new(1, 0, 1, 0)
    label.BackgroundTransparency = 1
    label.TextScaled = true
    label.TextColor3 = Color3.new(1, 1, 1)
    label.Parent = indicator
    
    if not isActive then
        indicator.BackgroundTransparency = 0.7
    else
        indicator.BackgroundTransparency = 0
    end
end

function AccessibilityHandler.EnableMouseKeys()
    AccessibilityHandler.mouseKeysEnabled = true
    AccessibilityHandler.mouseKeySpeed = 5
    AccessibilityHandler.mouseKeyAcceleration = 1.1
    
    local virtualMouse = Instance.new("Frame")
    virtualMouse.Name = "VirtualMouse"
    virtualMouse.Size = UDim2.new(0, 20, 0, 20)
    virtualMouse.Position = UDim2.new(0.5, -10, 0.5, -10)
    virtualMouse.BackgroundColor3 = Color3.new(1, 1, 0)
    virtualMouse.BorderSizePixel = 2
    virtualMouse.Parent = player:WaitForChild("PlayerGui"):WaitForChild("ScreenGui") or Instance.new("ScreenGui", player.PlayerGui)
    
    -- Movement with numpad
    RunService.Heartbeat:Connect(function()
        if not AccessibilityHandler.mouseKeysEnabled then return end
        
        local moveX, moveY = 0, 0
        local speed = AccessibilityHandler.mouseKeySpeed
        
        -- Numpad movement mapping
        if keyStates[Enum.KeyCode.KeypadSeven] then -- Up-Left
            moveX, moveY = -speed, -speed
        elseif keyStates[Enum.KeyCode.KeypadEight] then -- Up
            moveY = -speed
        elseif keyStates[Enum.KeyCode.KeypadNine] then -- Up-Right
            moveX, moveY = speed, -speed
        elseif keyStates[Enum.KeyCode.KeypadFour] then -- Left
            moveX = -speed
        elseif keyStates[Enum.KeyCode.KeypadSix] then -- Right
            moveX = speed
        elseif keyStates[Enum.KeyCode.KeypadOne] then -- Down-Left
            moveX, moveY = -speed, speed
        elseif keyStates[Enum.KeyCode.KeypadTwo] then -- Down
            moveY = speed
        elseif keyStates[Enum.KeyCode.KeypadThree] then -- Down-Right
            moveX, moveY = speed, speed
        end
        
        -- Apply acceleration if held
        if moveX ~= 0 or moveY ~= 0 then
            AccessibilityHandler.mouseKeySpeed = math.min(
                AccessibilityHandler.mouseKeySpeed * AccessibilityHandler.mouseKeyAcceleration,
                20
            )
            
            -- Update virtual mouse position
            local currentPos = virtualMouse.Position
            virtualMouse.Position = UDim2.new(
                currentPos.X.Scale,
                currentPos.X.Offset + moveX,
                currentPos.Y.Scale,
                currentPos.Y.Offset + moveY
            )
        else
            -- Reset speed when not moving
            AccessibilityHandler.mouseKeySpeed = 5
        end
    end)
    
    -- Click simulation with numpad 5
    UserInputService.InputBegan:Connect(function(input, gameProcessed)
        if not AccessibilityHandler.mouseKeysEnabled or gameProcessed then return end
        
        if input.KeyCode == Enum.KeyCode.KeypadFive then
            -- Simulate click at virtual mouse position
            local absolutePos = virtualMouse.AbsolutePosition
            local ray = workspace.CurrentCamera:ScreenPointToRay(absolutePos.X, absolutePos.Y)
            local hit, pos = workspace:FindPartOnRay(Ray.new(ray.Origin, ray.Direction * 1000))
            
            if hit then
                ReplicatedStorage:WaitForChild("VirtualClick"):FireServer(hit, pos)
            end
            
            -- Visual feedback
            local clickIndicator = virtualMouse:Clone()
            clickIndicator.BackgroundColor3 = Color3.new(0, 1, 0)
            clickIndicator.Parent = virtualMouse.Parent
            game:GetService("TweenService"):Create(
                clickIndicator,
                TweenInfo.new(0.3),
                {Size = UDim2.new(0, 40, 0, 40), BackgroundTransparency = 1}
            ):Play()
            game:GetService("Debris"):AddItem(clickIndicator, 0.3)
        elseif input.KeyCode == Enum.KeyCode.KeypadZero then
            -- Right click
            local absolutePos = virtualMouse.AbsolutePosition
            ReplicatedStorage:WaitForChild("VirtualRightClick"):FireServer(absolutePos.X, absolutePos.Y)
        elseif input.KeyCode == Enum.KeyCode.KeypadPlus then
            -- Speed up
            AccessibilityHandler.mouseKeyAcceleration = math.min(AccessibilityHandler.mouseKeyAcceleration + 0.1, 2)
        elseif input.KeyCode == Enum.KeyCode.KeypadMinus then
            -- Speed down
            AccessibilityHandler.mouseKeyAcceleration = math.max(AccessibilityHandler.mouseKeyAcceleration - 0.1, 1)
        end
    end)
end

-- Export accessibility handler
_G.AccessibilityHandler = AccessibilityHandler

-- TODO: Implement input validation for educational activities
local InputValidator = {}

function InputValidator.ValidateQuizAnswer(input)
    -- Check if input is valid option (1-4 for multiple choice)
    if type(input) ~= "number" or input < 1 or input > 4 then
        return false, "Invalid answer option. Please select 1-4."
    end
    
    -- Check for duplicate submission
    InputValidator.lastSubmission = InputValidator.lastSubmission or {}
    local currentTime = tick()
    
    if InputValidator.lastSubmission.answer == input and
       InputValidator.lastSubmission.time and
       currentTime - InputValidator.lastSubmission.time < 1 then
        return false, "Duplicate submission detected. Please wait."
    end
    
    -- Validate timing constraints
    if InputValidator.quizStartTime then
        local elapsed = currentTime - InputValidator.quizStartTime
        local minTime = 0.5 -- Minimum time to read question
        local maxTime = 60 -- Maximum time per question
        
        if elapsed < minTime then
            return false, "Please read the question carefully before answering."
        elseif elapsed > maxTime then
            return false, "Time limit exceeded for this question."
        end
    end
    
    -- Update last submission
    InputValidator.lastSubmission = {
        answer = input,
        time = currentTime
    }
    
    return true, "Answer validated successfully."
end

function InputValidator.ValidateMathInput(input)
    if type(input) ~= "string" then
        return nil, "Input must be a string"
    end
    
    -- Remove whitespace
    input = input:gsub("%s+", "")
    
    -- Check for valid characters
    local validPattern = "^[0-9%.%+%-%*%/%^%(%)=xyzabc]+$"
    if not input:match(validPattern) then
        return nil, "Invalid characters in expression"
    end
    
    -- Check for balanced parentheses
    local openCount = 0
    for char in input:gmatch(".") do
        if char == "(" then
            openCount = openCount + 1
        elseif char == ")" then
            openCount = openCount - 1
            if openCount < 0 then
                return nil, "Unbalanced parentheses"
            end
        end
    end
    if openCount ~= 0 then
        return nil, "Unbalanced parentheses"
    end
    
    -- Validate operators aren't consecutive
    if input:match("[%+%-%*%/%^]{2,}") then
        return nil, "Consecutive operators not allowed"
    end
    
    -- Check for valid equation format if contains equals
    if input:match("=") then
        local parts = input:split("=")
        if #parts ~= 2 then
            return nil, "Equation must have exactly one equals sign"
        end
    end
    
    -- Parse and evaluate (safely)
    local success, result = pcall(function()
        -- Replace variables with placeholder values for validation
        local testExpr = input:gsub("[xyz]", "1")
        -- Use loadstring safely
        local func = loadstring("return " .. testExpr)
        if func then
            return func()
        end
    end)
    
    if success then
        return input, "Valid mathematical expression"
    else
        return nil, "Invalid mathematical expression"
    end
end

-- Additional validation functions
function InputValidator.ValidateTextInput(input, minLength, maxLength)
    if type(input) ~= "string" then
        return false, "Input must be text"
    end
    
    minLength = minLength or 1
    maxLength = maxLength or 500
    
    if #input < minLength then
        return false, "Input too short (minimum " .. minLength .. " characters)"
    end
    
    if #input > maxLength then
        return false, "Input too long (maximum " .. maxLength .. " characters)"
    end
    
    -- Check for inappropriate content (basic filter)
    local inappropriate = {"hack", "cheat", "exploit"}
    local lowerInput = input:lower()
    for _, word in ipairs(inappropriate) do
        if lowerInput:find(word) then
            return false, "Inappropriate content detected"
        end
    end
    
    return true, "Valid text input"
end

-- Export validator
_G.InputValidator = InputValidator

-- TODO: Implement haptic feedback for supported devices
local HapticFeedback = {}

function HapticFeedback.PlayFeedback(feedbackType)
    -- Check if device supports haptic feedback
    if not UserInputService.GamepadEnabled and not UserInputService.TouchEnabled then
        return
    end
    
    -- Get user's haptic settings (default enabled)
    local hapticEnabled = player:GetAttribute("HapticEnabled")
    if hapticEnabled == false then
        return
    end
    
    local hapticIntensity = player:GetAttribute("HapticIntensity") or 1.0
    
    -- Define feedback patterns
    local patterns = {
        light = {duration = 0.05, intensity = 0.3},
        medium = {duration = 0.1, intensity = 0.6},
        heavy = {duration = 0.2, intensity = 1.0},
        success = {duration = 0.15, intensity = 0.8, pulses = 2},
        error = {duration = 0.3, intensity = 1.0, pulses = 3},
        notification = {duration = 0.1, intensity = 0.5, pulses = 2}
    }
    
    local pattern = patterns[feedbackType] or patterns.medium
    pattern.intensity = pattern.intensity * hapticIntensity
    
    -- Trigger haptic feedback for gamepad
    if UserInputService.GamepadEnabled then
        local gamepad = Enum.UserInputType.Gamepad1
        
        if pattern.pulses then
            -- Multiple pulses
            for i = 1, pattern.pulses do
                UserInputService:SetGamepadVibrationMotor(
                    gamepad,
                    Enum.VibrationMotor.Large,
                    pattern.intensity
                )
                wait(pattern.duration / pattern.pulses)
                UserInputService:SetGamepadVibrationMotor(
                    gamepad,
                    Enum.VibrationMotor.Large,
                    0
                )
                if i < pattern.pulses then
                    wait(pattern.duration / pattern.pulses)
                end
            end
        else
            -- Single vibration
            UserInputService:SetGamepadVibrationMotor(
                gamepad,
                Enum.VibrationMotor.Large,
                pattern.intensity
            )
            wait(pattern.duration)
            UserInputService:SetGamepadVibrationMotor(
                gamepad,
                Enum.VibrationMotor.Large,
                0
            )
        end
    end
    
    -- Visual feedback for devices without haptic
    if not UserInputService.GamepadEnabled then
        local screen = player:WaitForChild("PlayerGui"):FindFirstChild("ScreenGui") or Instance.new("ScreenGui", player.PlayerGui)
        local flash = Instance.new("Frame")
        flash.Size = UDim2.new(1, 0, 1, 0)
        flash.BackgroundColor3 = feedbackType == "error" and Color3.new(1, 0, 0) or Color3.new(1, 1, 1)
        flash.BackgroundTransparency = 0.9
        flash.Parent = screen
        
        game:GetService("TweenService"):Create(
            flash,
            TweenInfo.new(pattern.duration),
            {BackgroundTransparency = 1}
        ):Play()
        
        game:GetService("Debris"):AddItem(flash, pattern.duration)
    end
end

-- Export haptic feedback
_G.HapticFeedback = HapticFeedback

-- Initialize the input system
SetupContextActions()

-- TODO: Clean up on player leaving
Players.PlayerRemoving:Connect(function(leavingPlayer)
    if leavingPlayer == player then
        -- Unbind all context actions
        ContextActionService:UnbindAllActions()
        
        -- Disconnect all event connections
        for _, connection in pairs(inputConnections) do
            if connection then
                connection:Disconnect()
            end
        end
        
        -- Clear recorded inputs
        recordedInputs = {}
        isRecording = false
        
        -- Save input preferences
        local preferences = {
            inputMode = currentInputMode,
            hapticEnabled = player:GetAttribute("HapticEnabled"),
            hapticIntensity = player:GetAttribute("HapticIntensity"),
            stickyKeysEnabled = AccessibilityHandler.stickyKeysEnabled,
            mouseKeysEnabled = AccessibilityHandler.mouseKeysEnabled
        }
        
        ReplicatedStorage:WaitForChild("SaveInputPreferences"):FireServer(preferences)
        
        -- Reset gamepad vibration
        if UserInputService.GamepadEnabled then
            UserInputService:SetGamepadVibrationMotor(
                Enum.UserInputType.Gamepad1,
                Enum.VibrationMotor.Large,
                0
            )
            UserInputService:SetGamepadVibrationMotor(
                Enum.UserInputType.Gamepad1,
                Enum.VibrationMotor.Small,
                0
            )
        end
        
        print("Input system cleaned up for player: " .. leavingPlayer.Name)
    end
end)
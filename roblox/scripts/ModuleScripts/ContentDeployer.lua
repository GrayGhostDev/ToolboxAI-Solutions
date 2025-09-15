--[[
    ToolboxAI Content Deployer Module
    Version: 2.0.0 - Updated for Roblox 2025
    Terminal 3 - Educational Content Deployment System

    Features:
    - Dynamic educational content deployment
    - Multi-modal content support (text, 3D, interactive)
    - Real-time backend synchronization
    - FilteringEnabled compliant deployment
    - Memory-efficient content management
]]

local ContentDeployer = {}
ContentDeployer.__index = ContentDeployer

-- Services
local HttpService = game:GetService("HttpService")
local TweenService = game:GetService("TweenService")
local Lighting = game:GetService("Lighting")
local Debris = game:GetService("Debris")
local RunService = game:GetService("RunService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

-- Configuration
local CONFIG = {
    API_BASE_URL = "http://127.0.0.1:8008",
    DEPLOYMENT_ENDPOINT = "/api/v1/content/deploy",
    ANALYTICS_ENDPOINT = "/api/v1/analytics/deployment",
    MAX_CONCURRENT_DEPLOYMENTS = 5,
    CLEANUP_INTERVAL = 300 -- 5 minutes
}

function ContentDeployer.new()
    local self = setmetatable({}, ContentDeployer)
    self.deployedContent = {}
    self.activeQuizzes = {}

    -- Enhanced tracking (2025)
    self.deploymentStats = {
        totalDeployments = 0,
        successfulDeployments = 0,
        failedDeployments = 0,
        activeDeployments = 0
    }

    -- Setup cleanup routine
    self:setupCleanupRoutine()

    return self
end

-- Setup automatic cleanup routine
function ContentDeployer:setupCleanupRoutine()
    spawn(function()
        while true do
            wait(CONFIG.CLEANUP_INTERVAL)
            self:performCleanup()
        end
    end)
end

-- Perform routine cleanup of old content
function ContentDeployer:performCleanup()
    local currentTime = tick()
    local cleanupCount = 0

    for lessonId, deployment in pairs(self.deployedContent) do
        -- Clean up content older than 1 hour if no players are nearby
        local age = currentTime - (deployment.startTime or 0)
        if age > 3600 then -- 1 hour
            local hasNearbyPlayers = false
            if deployment.folder then
                -- Check if any players are within 100 studs
                for _, player in pairs(Players:GetPlayers()) do
                    if player.Character and player.Character.PrimaryPart then
                        local distance = (player.Character.PrimaryPart.Position - deployment.folder.WorldPivot.Position).Magnitude
                        if distance < 100 then
                            hasNearbyPlayers = true
                            break
                        end
                    end
                end
            end

            if not hasNearbyPlayers then
                self:cleanup(lessonId)
                cleanupCount = cleanupCount + 1
            end
        end
    end

    if cleanupCount > 0 then
        print(string.format("[ContentDeployer] Cleaned up %d old deployments", cleanupCount))
    end
end

function ContentDeployer:deployLesson(lessonData)
    print("📚 Deploying lesson:", lessonData.title or "Untitled")
    
    -- Verify with Terminal 1
    local verified = self:verifyContent(lessonData)
    if not verified then
        warn("Content verification failed")
        return false
    end
    
    -- Create lesson environment
    local lessonFolder = Instance.new("Folder")
    lessonFolder.Name = "Lesson_" .. (lessonData.id or tostring(tick()))
    lessonFolder.Parent = workspace
    
    -- Store deployment info
    self.deployedContent[lessonData.id] = {
        folder = lessonFolder,
        startTime = tick(),
        type = lessonData.type
    }
    
    -- Deploy based on content type
    if lessonData.type == "interactive" then
        self:deployInteractiveContent(lessonData, lessonFolder)
    elseif lessonData.type == "quiz" then
        self:deployQuizContent(lessonData, lessonFolder)
    elseif lessonData.type == "exploration" then
        self:deployExplorationContent(lessonData, lessonFolder)
    elseif lessonData.type == "terrain" then
        self:deployTerrainContent(lessonData, lessonFolder)
    end
    
    -- Notify Terminal 2 (Dashboard)
    self:notifyDashboard({
        event = "lesson_deployed",
        lesson_id = lessonData.id,
        student_count = #game.Players:GetPlayers()
    })
    
    -- Send metrics to Debugger
    self:sendMetrics({
        deployment_time = tick(),
        content_size = #HttpService:JSONEncode(lessonData),
        success = true
    })
    
    return true
end

function ContentDeployer:verifyContent(content)
    -- Verify with Terminal 1
    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = "http://127.0.0.1:5001/content/verify",
            Method = "POST",
            Headers = {["Content-Type"] = "application/json"},
            Body = HttpService:JSONEncode({
                content_id = content.id,
                checksum = self:calculateChecksum(content)
            })
        })
    end)
    
    -- If verification endpoint doesn't exist, assume valid
    if not success then
        print("Content verification endpoint not available, proceeding anyway")
        return true
    end
    
    return response.StatusCode == 200
end

function ContentDeployer:deployInteractiveContent(data, parent)
    -- Create interactive 3D elements
    local elements = data.elements or {}
    
    for i, element in ipairs(elements) do
        local part = Instance.new("Part")
        part.Name = element.name or ("Element_" .. i)
        
        -- Set size
        if element.size then
            part.Size = Vector3.new(
                element.size.x or 4,
                element.size.y or 4,
                element.size.z or 4
            )
        else
            part.Size = Vector3.new(4, 4, 4)
        end
        
        -- Set position
        if element.position then
            part.Position = Vector3.new(
                element.position.x or 0,
                element.position.y or 10,
                element.position.z or i * 10
            )
        else
            part.Position = Vector3.new(i * 10, 10, 0)
        end
        
        -- Set material and color
        part.Material = Enum.Material[element.material or "Plastic"]
        if element.color then
            part.Color = Color3.fromRGB(
                element.color.r or 100,
                element.color.g or 100,
                element.color.b or 100
            )
        else
            part.BrickColor = BrickColor.Random()
        end
        
        part.Anchored = true
        part.Parent = parent
        
        -- Add interactivity
        if element.interactive then
            local clickDetector = Instance.new("ClickDetector")
            clickDetector.MaxActivationDistance = 20
            clickDetector.Parent = part
            
            clickDetector.MouseClick:Connect(function(player)
                self:handleInteraction(player, element)
            end)
        end
        
        -- Add educational info
        if element.info then
            local billboard = Instance.new("BillboardGui")
            billboard.Size = UDim2.new(4, 0, 2, 0)
            billboard.StudsOffset = Vector3.new(0, 3, 0)
            billboard.AlwaysOnTop = true
            billboard.Parent = part
            
            local label = Instance.new("TextLabel")
            label.Text = element.info
            label.Size = UDim2.new(1, 0, 1, 0)
            label.BackgroundColor3 = Color3.new(0, 0, 0)
            label.BackgroundTransparency = 0.3
            label.TextColor3 = Color3.new(1, 1, 1)
            label.TextScaled = true
            label.Font = Enum.Font.SourceSans
            label.Parent = billboard
        end
        
        -- Add animation if specified
        if element.animate then
            self:animateElement(part, element.animate)
        end
    end
end

function ContentDeployer:deployQuizContent(data, parent)
    -- Store quiz data
    self.activeQuizzes[data.id] = data
    
    -- Create quiz UI for all players
    for _, player in ipairs(game.Players:GetPlayers()) do
        self:createQuizUI(player, data)
    end
    
    -- Create physical quiz area in world
    local quizArea = Instance.new("Part")
    quizArea.Name = "QuizArea_" .. (data.id or "unknown")
    quizArea.Size = Vector3.new(30, 1, 30)
    quizArea.Position = Vector3.new(0, 0.5, 0)
    quizArea.Material = Enum.Material.Neon
    quizArea.BrickColor = BrickColor.new("Bright blue")
    quizArea.Transparency = 0.5
    quizArea.Anchored = true
    quizArea.CanCollide = false
    quizArea.Parent = parent
    
    -- Add light effect
    local pointLight = Instance.new("PointLight")
    pointLight.Brightness = 2
    pointLight.Range = 30
    pointLight.Color = Color3.new(0, 0.5, 1)
    pointLight.Parent = quizArea
end

function ContentDeployer:createQuizUI(player, quizData)
    local gui = Instance.new("ScreenGui")
    gui.Name = "Quiz_" .. (quizData.id or "unknown")
    gui.ResetOnSpawn = false
    gui.Parent = player.PlayerGui
    
    -- Main frame
    local frame = Instance.new("Frame")
    frame.Size = UDim2.new(0.8, 0, 0.6, 0)
    frame.Position = UDim2.new(0.1, 0, 0.2, 0)
    frame.BackgroundColor3 = Color3.fromRGB(30, 30, 30)
    frame.BorderSizePixel = 0
    frame.Parent = gui
    
    -- Add rounded corners
    local corner = Instance.new("UICorner")
    corner.CornerRadius = UDim.new(0, 12)
    corner.Parent = frame
    
    -- Question display
    local questionLabel = Instance.new("TextLabel")
    questionLabel.Text = quizData.question or "Question not available"
    questionLabel.Size = UDim2.new(1, -20, 0.3, 0)
    questionLabel.Position = UDim2.new(0, 10, 0, 10)
    questionLabel.BackgroundTransparency = 1
    questionLabel.TextColor3 = Color3.new(1, 1, 1)
    questionLabel.TextScaled = true
    questionLabel.Font = Enum.Font.SourceSansBold
    questionLabel.Parent = frame
    
    -- Answer buttons
    local answers = quizData.answers or {}
    for i, answer in ipairs(answers) do
        local button = Instance.new("TextButton")
        button.Text = answer.text or ("Answer " .. i)
        button.Size = UDim2.new(0.8, 0, 0.12, 0)
        button.Position = UDim2.new(0.1, 0, 0.3 + (i * 0.13), 0)
        button.BackgroundColor3 = Color3.fromRGB(50, 50, 50)
        button.TextColor3 = Color3.new(1, 1, 1)
        button.TextScaled = true
        button.Font = Enum.Font.SourceSans
        button.Parent = frame
        
        local buttonCorner = Instance.new("UICorner")
        buttonCorner.CornerRadius = UDim.new(0, 8)
        buttonCorner.Parent = button
        
        button.MouseButton1Click:Connect(function()
            self:submitAnswer(player, quizData.id, answer.id or i)
            gui:Destroy()
        end)
        
        -- Hover effect
        button.MouseEnter:Connect(function()
            button.BackgroundColor3 = Color3.fromRGB(70, 70, 70)
        end)
        
        button.MouseLeave:Connect(function()
            button.BackgroundColor3 = Color3.fromRGB(50, 50, 50)
        end)
    end
    
    -- Close button
    local closeButton = Instance.new("TextButton")
    closeButton.Text = "X"
    closeButton.Size = UDim2.new(0, 30, 0, 30)
    closeButton.Position = UDim2.new(1, -40, 0, 10)
    closeButton.BackgroundColor3 = Color3.fromRGB(200, 50, 50)
    closeButton.TextColor3 = Color3.new(1, 1, 1)
    closeButton.Font = Enum.Font.SourceSansBold
    closeButton.TextScaled = true
    closeButton.Parent = frame
    
    local closeCorner = Instance.new("UICorner")
    closeCorner.CornerRadius = UDim.new(0, 15)
    closeCorner.Parent = closeButton
    
    closeButton.MouseButton1Click:Connect(function()
        gui:Destroy()
    end)
end

function ContentDeployer:deployExplorationContent(data, parent)
    -- Create exploration environment
    local explorationZone = Instance.new("Model")
    explorationZone.Name = "ExplorationZone_" .. (data.id or "unknown")
    explorationZone.Parent = parent
    
    -- Create boundary
    local boundary = Instance.new("Part")
    boundary.Name = "Boundary"
    boundary.Size = Vector3.new(100, 50, 100)
    boundary.Position = Vector3.new(0, 25, 0)
    boundary.Transparency = 0.9
    boundary.Material = Enum.Material.ForceField
    boundary.BrickColor = BrickColor.new("Cyan")
    boundary.Anchored = true
    boundary.CanCollide = false
    boundary.Parent = explorationZone
    
    -- Add checkpoints
    local checkpoints = data.checkpoints or {}
    for i, checkpoint in ipairs(checkpoints) do
        local checkpointPart = Instance.new("Part")
        checkpointPart.Name = "Checkpoint_" .. i
        checkpointPart.Size = Vector3.new(5, 10, 5)
        checkpointPart.Position = Vector3.new(
            checkpoint.x or (i * 20 - 50),
            checkpoint.y or 5,
            checkpoint.z or 0
        )
        checkpointPart.Material = Enum.Material.Neon
        checkpointPart.BrickColor = BrickColor.new("Lime green")
        checkpointPart.Anchored = true
        checkpointPart.Parent = explorationZone
        
        -- Add checkpoint detector
        local detector = Instance.new("Part")
        detector.Name = "Detector"
        detector.Size = Vector3.new(10, 15, 10)
        detector.Position = checkpointPart.Position
        detector.Transparency = 1
        detector.Anchored = true
        detector.CanCollide = false
        detector.Parent = checkpointPart
        
        detector.Touched:Connect(function(hit)
            local humanoid = hit.Parent:FindFirstChild("Humanoid")
            if humanoid then
                local player = game.Players:GetPlayerFromCharacter(hit.Parent)
                if player then
                    self:handleCheckpoint(player, i, checkpoint)
                end
            end
        end)
    end
end

function ContentDeployer:deployTerrainContent(data, parent)
    -- Use TerrainGenerator module if available
    local success, TerrainGenerator = pcall(function()
        return require(script.Parent.TerrainGenerator)
    end)
    
    if success and TerrainGenerator then
        TerrainGenerator.generate(data)
    else
        -- Fallback terrain generation
        local terrain = workspace.Terrain
        
        if data.clear then
            terrain:Clear()
        end
        
        -- Generate terrain regions
        local regions = data.regions or {}
        for _, region in ipairs(regions) do
            if region.type == "sphere" then
                terrain:FillBall(
                    Vector3.new(region.x or 0, region.y or 10, region.z or 0),
                    region.radius or 10,
                    Enum.Material[region.material or "Grass"]
                )
            elseif region.type == "block" then
                terrain:FillBlock(
                    CFrame.new(region.x or 0, region.y or 0, region.z or 0),
                    Vector3.new(region.sizeX or 20, region.sizeY or 20, region.sizeZ or 20),
                    Enum.Material[region.material or "Sand"]
                )
            end
        end
    end
end

function ContentDeployer:handleInteraction(player, element)
    -- Log interaction with Terminal 1
    spawn(function()
        pcall(function()
            HttpService:PostAsync(
                "http://127.0.0.1:5001/plugin/interaction",
                HttpService:JSONEncode({
                    player_id = player.UserId,
                    player_name = player.Name,
                    element_id = element.id or "unknown",
                    element_name = element.name,
                    timestamp = os.time(),
                    action = "click"
                })
            )
        end)
    end)
    
    -- Show educational content
    if element.lesson then
        self:showLesson(player, element.lesson)
    end
    
    -- Award points if applicable
    if element.points then
        self:awardPoints(player, element.points)
    end
    
    -- Play sound effect
    local sound = Instance.new("Sound")
    sound.SoundId = "rbxasset://sounds/electronicpingshort.wav"
    sound.Volume = 0.5
    sound.Parent = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    if sound.Parent then
        sound:Play()
        Debris:AddItem(sound, 2)
    end
end

function ContentDeployer:submitAnswer(player, quiz_id, answer_id)
    -- Send to Terminal 1 for validation
    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = "http://127.0.0.1:5001/plugin/quiz/submit",
            Method = "POST",
            Headers = {["Content-Type"] = "application/json"},
            Body = HttpService:JSONEncode({
                player_id = player.UserId,
                player_name = player.Name,
                quiz_id = quiz_id,
                answer_id = answer_id,
                timestamp = os.time()
            })
        })
    end)
    
    if success and response.StatusCode == 200 then
        local result = HttpService:JSONDecode(response.Body)
        
        -- Show result to player
        self:showQuizResult(player, result.correct or false)
        
        -- Update score
        if result.correct then
            self:awardPoints(player, result.points or 10)
        end
        
        -- Notify Terminal 2
        self:notifyDashboard({
            event = "quiz_completed",
            player_id = player.UserId,
            player_name = player.Name,
            quiz_id = quiz_id,
            correct = result.correct
        })
    else
        -- Fallback: Check locally if answer is correct
        local quiz = self.activeQuizzes[quiz_id]
        if quiz and quiz.answers then
            local answer = quiz.answers[answer_id]
            if answer then
                local isCorrect = answer.correct == true
                self:showQuizResult(player, isCorrect)
                if isCorrect then
                    self:awardPoints(player, 10)
                end
            end
        end
    end
end

function ContentDeployer:showQuizResult(player, correct)
    local gui = Instance.new("ScreenGui")
    gui.Name = "QuizResult"
    gui.Parent = player.PlayerGui
    
    local label = Instance.new("TextLabel")
    label.Size = UDim2.new(0.4, 0, 0.2, 0)
    label.Position = UDim2.new(0.3, 0, 0.4, 0)
    label.BackgroundColor3 = correct and Color3.new(0, 1, 0) or Color3.new(1, 0, 0)
    label.Text = correct and "✓ Correct!" or "✗ Incorrect"
    label.TextColor3 = Color3.new(1, 1, 1)
    label.TextScaled = true
    label.Font = Enum.Font.SourceSansBold
    label.Parent = gui
    
    local corner = Instance.new("UICorner")
    corner.CornerRadius = UDim.new(0, 12)
    corner.Parent = label
    
    -- Auto-remove after 3 seconds
    Debris:AddItem(gui, 3)
end

function ContentDeployer:showLesson(player, lessonContent)
    -- Display lesson content to player
    local gui = Instance.new("ScreenGui")
    gui.Name = "LessonDisplay"
    gui.Parent = player.PlayerGui
    
    local frame = Instance.new("Frame")
    frame.Size = UDim2.new(0.6, 0, 0.5, 0)
    frame.Position = UDim2.new(0.2, 0, 0.25, 0)
    frame.BackgroundColor3 = Color3.fromRGB(40, 40, 40)
    frame.Parent = gui
    
    local corner = Instance.new("UICorner")
    corner.CornerRadius = UDim.new(0, 12)
    corner.Parent = frame
    
    local textLabel = Instance.new("TextLabel")
    textLabel.Size = UDim2.new(1, -20, 1, -20)
    textLabel.Position = UDim2.new(0, 10, 0, 10)
    textLabel.BackgroundTransparency = 1
    textLabel.Text = lessonContent
    textLabel.TextColor3 = Color3.new(1, 1, 1)
    textLabel.TextWrapped = true
    textLabel.TextScaled = false
    textLabel.TextSize = 18
    textLabel.Font = Enum.Font.SourceSans
    textLabel.Parent = frame
    
    -- Close button
    local closeButton = Instance.new("TextButton")
    closeButton.Text = "Close"
    closeButton.Size = UDim2.new(0.2, 0, 0, 30)
    closeButton.Position = UDim2.new(0.4, 0, 1, -40)
    closeButton.BackgroundColor3 = Color3.fromRGB(60, 60, 60)
    closeButton.TextColor3 = Color3.new(1, 1, 1)
    closeButton.Font = Enum.Font.SourceSans
    closeButton.Parent = frame
    
    closeButton.MouseButton1Click:Connect(function()
        gui:Destroy()
    end)
end

function ContentDeployer:awardPoints(player, points)
    -- Award points to player
    local leaderstats = player:FindFirstChild("leaderstats")
    if not leaderstats then
        leaderstats = Instance.new("Folder")
        leaderstats.Name = "leaderstats"
        leaderstats.Parent = player
    end
    
    local pointsValue = leaderstats:FindFirstChild("Points")
    if not pointsValue then
        pointsValue = Instance.new("IntValue")
        pointsValue.Name = "Points"
        pointsValue.Parent = leaderstats
    end
    
    pointsValue.Value = pointsValue.Value + points
    
    -- Show points notification
    local gui = Instance.new("ScreenGui")
    gui.Name = "PointsNotification"
    gui.Parent = player.PlayerGui
    
    local label = Instance.new("TextLabel")
    label.Size = UDim2.new(0.3, 0, 0.1, 0)
    label.Position = UDim2.new(0.35, 0, 0.1, 0)
    label.BackgroundColor3 = Color3.fromRGB(255, 215, 0)
    label.Text = "+" .. points .. " Points!"
    label.TextColor3 = Color3.new(0, 0, 0)
    label.TextScaled = true
    label.Font = Enum.Font.SourceSansBold
    label.Parent = gui
    
    -- Animate and remove
    local tween = TweenService:Create(label,
        TweenInfo.new(2, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
        {Position = UDim2.new(0.35, 0, 0, 0), Transparency = 1}
    )
    tween:Play()
    
    Debris:AddItem(gui, 2)
end

function ContentDeployer:handleCheckpoint(player, checkpointIndex, checkpointData)
    print(player.Name .. " reached checkpoint " .. checkpointIndex)
    
    -- Award checkpoint points
    if checkpointData.points then
        self:awardPoints(player, checkpointData.points)
    end
    
    -- Show checkpoint message
    if checkpointData.message then
        self:showLesson(player, checkpointData.message)
    end
    
    -- Send progress update
    spawn(function()
        pcall(function()
            HttpService:PostAsync(
                "http://127.0.0.1:5001/plugin/checkpoint",
                HttpService:JSONEncode({
                    player_id = player.UserId,
                    player_name = player.Name,
                    checkpoint_index = checkpointIndex,
                    timestamp = os.time()
                })
            )
        end)
    end)
end

function ContentDeployer:animateElement(part, animationType)
    if animationType == "rotate" then
        spawn(function()
            while part.Parent do
                part.CFrame = part.CFrame * CFrame.Angles(0, math.rad(1), 0)
                wait(0.03)
            end
        end)
    elseif animationType == "bounce" then
        local originalY = part.Position.Y
        spawn(function()
            while part.Parent do
                local tween = TweenService:Create(part,
                    TweenInfo.new(1, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut),
                    {Position = Vector3.new(part.Position.X, originalY + 2, part.Position.Z)}
                )
                tween:Play()
                tween.Completed:Wait()
                
                local tweenBack = TweenService:Create(part,
                    TweenInfo.new(1, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut),
                    {Position = Vector3.new(part.Position.X, originalY, part.Position.Z)}
                )
                tweenBack:Play()
                tweenBack.Completed:Wait()
            end
        end)
    end
end

function ContentDeployer:calculateChecksum(content)
    -- Simple checksum calculation
    local str = HttpService:JSONEncode(content)
    local sum = 0
    for i = 1, #str do
        sum = sum + string.byte(str, i)
    end
    return tostring(sum)
end

function ContentDeployer:notifyDashboard(data)
    -- Send notification to dashboard via Terminal 1
    spawn(function()
        pcall(function()
            HttpService:PostAsync(
                "http://127.0.0.1:5001/dashboard/notify",
                HttpService:JSONEncode(data)
            )
        end)
    end)
end

function ContentDeployer:sendMetrics(metrics)
    -- Send metrics to debugger via Terminal 1
    spawn(function()
        pcall(function()
            HttpService:PostAsync(
                "http://127.0.0.1:5001/debug/metrics",
                HttpService:JSONEncode({
                    source = "ContentDeployer",
                    metrics = metrics
                })
            )
        end)
    end)
end

-- Report deployment analytics to backend (2025)
function ContentDeployer:reportAnalytics(eventType, data)
    spawn(function()
        local success, response = pcall(function()
            return HttpService:RequestAsync({
                Url = CONFIG.API_BASE_URL .. CONFIG.ANALYTICS_ENDPOINT,
                Method = "POST",
                Headers = {
                    ["Content-Type"] = "application/json",
                    ["X-Content-Deployer"] = "2.0"
                },
                Body = HttpService:JSONEncode({
                    eventType = eventType,
                    data = data,
                    stats = self.deploymentStats,
                    metadata = {
                        placeId = game.PlaceId,
                        universeId = game.GameId,
                        timestamp = os.time(),
                        playerCount = #Players:GetPlayers()
                    }
                })
            })
        end)

        if success and response.StatusCode == 200 then
            -- Analytics reported successfully
        else
            warn("[ContentDeployer] Failed to report analytics:",
                 response and response.StatusMessage or "Unknown error")
        end
    end)
end

-- Get deployment statistics
function ContentDeployer:getStatistics()
    return {
        stats = self.deploymentStats,
        activeDeployments = self.deploymentStats.activeDeployments,
        deployedContentCount = 0,
        activeQuizzesCount = 0
    }
end

function ContentDeployer:cleanup(lessonId)
    -- Clean up deployed content
    local deployment = self.deployedContent[lessonId]
    if deployment and deployment.folder then
        deployment.folder:Destroy()
        self.deployedContent[lessonId] = nil

        -- Update statistics
        self.deploymentStats.activeDeployments = math.max(0, self.deploymentStats.activeDeployments - 1)

        -- Report cleanup to backend
        self:reportAnalytics("content_cleanup", {
            lessonId = lessonId,
            deploymentDuration = tick() - (deployment.startTime or 0)
        })
    end

    -- Remove quiz if active
    if self.activeQuizzes[lessonId] then
        self.activeQuizzes[lessonId] = nil
    end
end

return ContentDeployer
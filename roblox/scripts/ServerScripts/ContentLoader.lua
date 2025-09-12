--[[
    ContentLoader.lua
    Dynamic content loading system for educational materials
    
    This module handles loading educational content from the backend
    and dynamically creating game objects based on the content
]]

local ContentLoader = {}
local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local RunService = game:GetService("RunService")

-- Configuration
local API_BASE_URL = "http://127.0.0.1:8008"
local CONTENT_CACHE_TIME = 300 -- 5 minutes

-- Initialize content loader module
local ContentCache = {}
local ContentTemplates = {}
local ActiveContent = {}
local LoadingQueue = {}
local RetryAttempts = {}
local MaxRetries = 3

-- Initialize error handler
local function HandleError(errorMsg, context)
    warn("[ContentLoader Error]", errorMsg, "Context:", context)
    -- Log to analytics if available
    if game.ReplicatedStorage:FindFirstChild("LogError") then
        game.ReplicatedStorage.LogError:FireServer("ContentLoader", errorMsg, context)
    end
end

-- Initialize retry system
local function RetryWithBackoff(func, context, attempt)
    attempt = attempt or 1
    if attempt > MaxRetries then
        HandleError("Max retries exceeded", context)
        return nil
    end
    
    local success, result = pcall(func)
    if not success then
        wait(math.pow(2, attempt - 1)) -- Exponential backoff
        return RetryWithBackoff(func, context, attempt + 1)
    end
    return result
end

-- Initialize content templates
ContentTemplates.Quiz = {
    type = "Quiz",
    structure = {"Question", "Options", "CorrectAnswer", "Explanation"},
    validation = function(data) return data.Question and #data.Options >= 2 end
}

ContentTemplates.Lesson = {
    type = "Lesson",
    structure = {"Title", "Objectives", "Content", "Assessment"},
    validation = function(data) return data.Title and data.Content end
}

ContentTemplates.Activity = {
    type = "Activity",
    structure = {"Name", "Instructions", "Materials", "Duration"},
    validation = function(data) return data.Name and data.Instructions end
}

-- Implement content fetching from backend
-- @param subject: string - The subject to fetch content for
-- @param gradeLevel: number - The grade level of the content
-- @return table - The fetched content data
function ContentLoader.FetchContent(subject, gradeLevel)
    -- Check cache first
    local cacheKey = string.format("%s_%d_%d", subject, gradeLevel, math.floor(tick() / CONTENT_CACHE_TIME))
    if ContentCache[cacheKey] then
        return ContentCache[cacheKey]
    end
    
    -- Construct API endpoint URL
    local endpoint = string.format("%s/content/%s/grade/%d", API_BASE_URL, HttpService:UrlEncode(subject), gradeLevel)
    
    -- Add to loading queue to prevent duplicate requests
    if LoadingQueue[cacheKey] then
        while LoadingQueue[cacheKey] do
            wait(0.1)
        end
        return ContentCache[cacheKey] or {}
    end
    
    LoadingQueue[cacheKey] = true
    
    -- Make HTTP request with retry logic
    local function fetchData()
        local headers = {
            ["Content-Type"] = "application/json",
            ["Authorization"] = "Bearer " .. (ServerStorage:FindFirstChild("APIKey") and ServerStorage.APIKey.Value or ""),
            ["X-Request-ID"] = HttpService:GenerateGUID(false)
        }
        
        local success, response = pcall(function()
            return HttpService:RequestAsync({
                Url = endpoint,
                Method = "GET",
                Headers = headers
            })
        end)
        
        if not success then
            error("HTTP request failed: " .. tostring(response))
        end
        
        -- Handle rate limiting
        if response.StatusCode == 429 then
            local retryAfter = tonumber(response.Headers["Retry-After"]) or 5
            wait(retryAfter)
            return fetchData()
        end
        
        if response.StatusCode ~= 200 then
            error("API returned status " .. response.StatusCode)
        end
        
        return HttpService:JSONDecode(response.Body)
    end
    
    local contentData = RetryWithBackoff(fetchData, {subject = subject, gradeLevel = gradeLevel})
    
    if contentData then
        -- Cache successful response
        ContentCache[cacheKey] = contentData
        
        -- Clean old cache entries
        spawn(function()
            wait(CONTENT_CACHE_TIME)
            ContentCache[cacheKey] = nil
        end)
    end
    
    LoadingQueue[cacheKey] = nil
    return contentData or {}
end

-- Implement content validation
-- @param content: table - The content data to validate
-- @return boolean, string - Success status and error message if any
function ContentLoader.ValidateContent(content)
    if not content or type(content) ~= "table" then
        return false, "Content must be a valid table"
    end
    
    -- Check required fields exist
    if not content.type then
        return false, "Content type is required"
    end
    
    -- Validate against template if exists
    local template = ContentTemplates[content.type]
    if template then
        if not template.validation(content) then
            return false, "Content failed template validation for type: " .. content.type
        end
        
        -- Check required structure fields
        for _, field in ipairs(template.structure) do
            if content[field] == nil then
                return false, "Missing required field: " .. field
            end
        end
    end
    
    -- Validate data types
    if content.gradeLevel and type(content.gradeLevel) ~= "number" then
        return false, "Grade level must be a number"
    end
    
    if content.gradeLevel and (content.gradeLevel < 1 or content.gradeLevel > 12) then
        return false, "Grade level must be between 1 and 12"
    end
    
    -- Check for inappropriate content (basic filter)
    local inappropriateWords = {"hack", "cheat", "exploit", "bypass"}
    local contentString = HttpService:JSONEncode(content):lower()
    for _, word in ipairs(inappropriateWords) do
        if contentString:find(word) then
            return false, "Content contains inappropriate material: " .. word
        end
    end
    
    -- Verify asset references exist
    if content.assets then
        for _, assetId in ipairs(content.assets) do
            local success = pcall(function()
                game:GetService("InsertService"):LoadAsset(assetId)
            end)
            if not success then
                return false, "Invalid asset reference: " .. tostring(assetId)
            end
        end
    end
    
    -- Ensure content meets educational standards
    if content.type == "Quiz" and content.Options then
        if #content.Options < 2 then
            return false, "Quiz must have at least 2 options"
        end
        if not content.CorrectAnswer then
            return false, "Quiz must specify correct answer"
        end
    end
    
    return true, "Content validated successfully"
end

-- Implement dynamic content instantiation
-- @param contentData: table - The content data to instantiate
-- @param parent: Instance - The parent to instantiate content under
-- @return Instance - The created content instance
function ContentLoader.InstantiateContent(contentData, parent)
    parent = parent or workspace
    
    -- Validate content first
    local isValid, errorMsg = ContentLoader.ValidateContent(contentData)
    if not isValid then
        HandleError("Content validation failed: " .. errorMsg, contentData)
        return nil
    end
    
    -- Create container for content
    local contentContainer = Instance.new("Folder")
    contentContainer.Name = contentData.name or (contentData.type .. "_" .. tick())
    contentContainer.Parent = parent
    
    -- Store content ID for tracking
    local contentId = HttpService:GenerateGUID(false)
    local idValue = Instance.new("StringValue")
    idValue.Name = "ContentID"
    idValue.Value = contentId
    idValue.Parent = contentContainer
    
    -- Parse content type and create appropriate objects
    if contentData.type == "Quiz" then
        -- Create quiz UI
        local quizPart = Instance.new("Part")
        quizPart.Name = "QuizBoard"
        quizPart.Size = Vector3.new(10, 8, 0.5)
        quizPart.Anchored = true
        quizPart.Position = contentData.position or Vector3.new(0, 5, 0)
        quizPart.Parent = contentContainer
        
        local surfaceGui = Instance.new("SurfaceGui")
        surfaceGui.Face = Enum.NormalId.Front
        surfaceGui.Parent = quizPart
        
        -- Question display
        local questionLabel = Instance.new("TextLabel")
        questionLabel.Size = UDim2.new(1, 0, 0.3, 0)
        questionLabel.Text = contentData.Question or "Question"
        questionLabel.TextScaled = true
        questionLabel.BackgroundColor3 = Color3.new(0.2, 0.3, 0.5)
        questionLabel.TextColor3 = Color3.new(1, 1, 1)
        questionLabel.Parent = surfaceGui
        
        -- Create option buttons
        if contentData.Options then
            for i, option in ipairs(contentData.Options) do
                local button = Instance.new("TextButton")
                button.Name = "Option" .. i
                button.Size = UDim2.new(0.9, 0, 0.15, 0)
                button.Position = UDim2.new(0.05, 0, 0.3 + (i * 0.16), 0)
                button.Text = option
                button.TextScaled = true
                button.BackgroundColor3 = Color3.new(0.3, 0.4, 0.6)
                button.Parent = surfaceGui
                
                -- Bind interaction
                local clickDetector = Instance.new("ClickDetector")
                clickDetector.MaxActivationDistance = 20
                clickDetector.Parent = quizPart
                
                clickDetector.MouseClick:Connect(function(player)
                    ReplicatedStorage:WaitForChild("QuizAnswer"):FireClient(player, contentId, i)
                end)
            end
        end
        
    elseif contentData.type == "Lesson" then
        -- Create lesson display
        local lessonPart = Instance.new("Part")
        lessonPart.Name = "LessonDisplay"
        lessonPart.Size = Vector3.new(15, 10, 0.5)
        lessonPart.Anchored = true
        lessonPart.Position = contentData.position or Vector3.new(0, 5, 0)
        lessonPart.Parent = contentContainer
        
        local surfaceGui = Instance.new("SurfaceGui")
        surfaceGui.Face = Enum.NormalId.Front
        surfaceGui.Parent = lessonPart
        
        -- Title
        local titleLabel = Instance.new("TextLabel")
        titleLabel.Size = UDim2.new(1, 0, 0.15, 0)
        titleLabel.Text = contentData.Title or "Lesson"
        titleLabel.TextScaled = true
        titleLabel.BackgroundColor3 = Color3.new(0.1, 0.2, 0.4)
        titleLabel.TextColor3 = Color3.new(1, 1, 1)
        titleLabel.Parent = surfaceGui
        
        -- Content
        local contentFrame = Instance.new("ScrollingFrame")
        contentFrame.Size = UDim2.new(0.95, 0, 0.8, 0)
        contentFrame.Position = UDim2.new(0.025, 0, 0.18, 0)
        contentFrame.CanvasSize = UDim2.new(0, 0, 2, 0)
        contentFrame.Parent = surfaceGui
        
        local contentText = Instance.new("TextLabel")
        contentText.Size = UDim2.new(1, 0, 1, 0)
        contentText.Text = contentData.Content or "Lesson content"
        contentText.TextWrapped = true
        contentText.TextScaled = false
        contentText.TextSize = 24
        contentText.BackgroundTransparency = 1
        contentText.Parent = contentFrame
        
    elseif contentData.type == "Activity" then
        -- Create activity area
        local activityPart = Instance.new("Part")
        activityPart.Name = "ActivityZone"
        activityPart.Size = Vector3.new(20, 0.5, 20)
        activityPart.Anchored = true
        activityPart.Position = contentData.position or Vector3.new(0, 0.25, 0)
        activityPart.Material = Enum.Material.Neon
        activityPart.BrickColor = BrickColor.new("Lime green")
        activityPart.Transparency = 0.5
        activityPart.Parent = contentContainer
        
        -- Activity instructions billboard
        local billboard = Instance.new("BillboardGui")
        billboard.Size = UDim2.new(10, 0, 5, 0)
        billboard.StudsOffset = Vector3.new(0, 5, 0)
        billboard.Parent = activityPart
        
        local instructionLabel = Instance.new("TextLabel")
        instructionLabel.Size = UDim2.new(1, 0, 1, 0)
        instructionLabel.Text = contentData.Instructions or "Activity Instructions"
        instructionLabel.TextScaled = true
        instructionLabel.BackgroundColor3 = Color3.new(0, 0, 0)
        instructionLabel.BackgroundTransparency = 0.3
        instructionLabel.TextColor3 = Color3.new(1, 1, 1)
        instructionLabel.Parent = billboard
    end
    
    -- Apply styling and theming
    if contentData.theme then
        for _, part in ipairs(contentContainer:GetDescendants()) do
            if part:IsA("GuiObject") and contentData.theme.backgroundColor then
                part.BackgroundColor3 = contentData.theme.backgroundColor
            end
            if part:IsA("TextLabel") and contentData.theme.textColor then
                part.TextColor3 = contentData.theme.textColor
            end
        end
    end
    
    -- Track active content
    ActiveContent[contentId] = {
        container = contentContainer,
        data = contentData,
        createdAt = tick()
    }
    
    return contentContainer
end

-- Implement content preloading system
-- @param contentIds: table - Array of content IDs to preload
function ContentLoader.PreloadContent(contentIds)
    if not contentIds or #contentIds == 0 then
        return
    end
    
    local preloadTasks = {}
    
    -- Fetch content in parallel
    for _, contentId in ipairs(contentIds) do
        spawn(function()
            local success, contentData = pcall(function()
                -- Fetch from API
                local endpoint = API_BASE_URL .. "/content/" .. contentId
                local response = HttpService:GetAsync(endpoint)
                return HttpService:JSONDecode(response)
            end)
            
            if success and contentData then
                -- Store in cache
                ContentCache[contentId] = contentData
                
                -- Load associated assets
                if contentData.assets then
                    local assetsToLoad = {}
                    for _, assetId in ipairs(contentData.assets) do
                        table.insert(assetsToLoad, "rbxassetid://" .. assetId)
                    end
                    
                    if #assetsToLoad > 0 then
                        ContentProvider:PreloadAsync(assetsToLoad)
                    end
                end
                
                -- Prepare templates for quick instantiation
                if contentData.type and ContentTemplates[contentData.type] then
                    local template = ContentTemplates[contentData.type]
                    -- Pre-validate
                    ContentLoader.ValidateContent(contentData)
                end
                
                print("Preloaded content:", contentId)
            else
                HandleError("Failed to preload content: " .. contentId, {id = contentId})
            end
        end)
    end
    
    -- Optional: Wait for all preloads to complete
    wait(0.5) -- Give spawned threads time to start
end

-- Implement content unloading and cleanup
-- @param contentId: string - The ID of content to unload
function ContentLoader.UnloadContent(contentId)
    local content = ActiveContent[contentId]
    if not content then
        return
    end
    
    -- Clear event connections
    if content.connections then
        for _, connection in ipairs(content.connections) do
            if connection then
                connection:Disconnect()
            end
        end
    end
    
    -- Destroy game objects
    if content.container and content.container.Parent then
        content.container:Destroy()
    end
    
    -- Remove from cache
    ContentCache[contentId] = nil
    
    -- Remove from active content
    ActiveContent[contentId] = nil
    
    -- Free up memory by suggesting garbage collection
    if #ActiveContent == 0 then
        collectgarbage("collect")
    end
    
    print("Unloaded content:", contentId)
end

-- Implement content update system
-- @param contentId: string - The ID of content to update
-- @param updates: table - The updates to apply
function ContentLoader.UpdateContent(contentId, updates)
    local content = ActiveContent[contentId]
    if not content then
        HandleError("Content not found for update", {id = contentId})
        return
    end
    
    -- Merge updates with existing data
    for key, value in pairs(updates) do
        content.data[key] = value
    end
    
    -- Update cache
    ContentCache[contentId] = content.data
    
    -- Update game objects
    if content.container then
        -- Find and update text elements
        for _, obj in ipairs(content.container:GetDescendants()) do
            if obj:IsA("TextLabel") then
                if obj.Name == "QuestionLabel" and updates.Question then
                    obj.Text = updates.Question
                elseif obj.Name == "TitleLabel" and updates.Title then
                    obj.Text = updates.Title
                elseif obj.Name == "ContentLabel" and updates.Content then
                    obj.Text = updates.Content
                end
            elseif obj:IsA("TextButton") and updates.Options then
                local optionIndex = tonumber(obj.Name:match("Option(%d+)"))
                if optionIndex and updates.Options[optionIndex] then
                    obj.Text = updates.Options[optionIndex]
                end
            end
        end
        
        -- Update theme if provided
        if updates.theme then
            for _, part in ipairs(content.container:GetDescendants()) do
                if part:IsA("GuiObject") and updates.theme.backgroundColor then
                    part.BackgroundColor3 = updates.theme.backgroundColor
                end
                if part:IsA("TextLabel") and updates.theme.textColor then
                    part.TextColor3 = updates.theme.textColor
                end
            end
        end
    end
    
    -- Notify connected clients
    if ReplicatedStorage:FindFirstChild("ContentUpdated") then
        ReplicatedStorage.ContentUpdated:FireAllClients(contentId, updates)
    end
    
    content.lastUpdated = tick()
    print("Updated content:", contentId)
end

-- Implement content progress tracking
-- @param contentId: string - The ID of content being interacted with
-- @param progressData: table - Progress information
function ContentLoader.TrackProgress(contentId, progressData)
    local content = ActiveContent[contentId]
    if not content then
        return
    end
    
    -- Initialize progress tracking if not exists
    if not content.progress then
        content.progress = {
            interactions = {},
            startTime = tick(),
            completionPercentage = 0,
            achievements = {}
        }
    end
    
    -- Record interaction events
    table.insert(content.progress.interactions, {
        type = progressData.type or "interaction",
        timestamp = tick(),
        data = progressData
    })
    
    -- Calculate completion percentage
    if content.data.type == "Quiz" and progressData.answeredQuestions then
        local totalQuestions = content.data.totalQuestions or 1
        content.progress.completionPercentage = (progressData.answeredQuestions / totalQuestions) * 100
    elseif content.data.type == "Lesson" and progressData.pagesViewed then
        local totalPages = content.data.totalPages or 1
        content.progress.completionPercentage = (progressData.pagesViewed / totalPages) * 100
    elseif content.data.type == "Activity" and progressData.tasksCompleted then
        local totalTasks = content.data.totalTasks or 1
        content.progress.completionPercentage = (progressData.tasksCompleted / totalTasks) * 100
    end
    
    -- Check for achievements
    if content.progress.completionPercentage >= 100 and not content.progress.achievements.completed then
        content.progress.achievements.completed = true
        content.progress.achievements.completedAt = tick()
        
        -- Award achievement
        if progressData.userId then
            ReplicatedStorage:WaitForChild("AwardAchievement"):FireClient(
                game.Players:GetPlayerByUserId(progressData.userId),
                "ContentCompleted",
                contentId
            )
        end
    end
    
    -- Send analytics to backend
    spawn(function()
        local analyticsData = {
            contentId = contentId,
            userId = progressData.userId,
            progress = content.progress.completionPercentage,
            duration = tick() - content.progress.startTime,
            interactions = #content.progress.interactions,
            timestamp = os.time()
        }
        
        local success = pcall(function()
            HttpService:PostAsync(
                API_BASE_URL .. "/analytics/progress",
                HttpService:JSONEncode(analyticsData),
                Enum.HttpContentType.ApplicationJson
            )
        end)
        
        if not success then
            HandleError("Failed to send analytics", analyticsData)
        end
    end)
end

-- Implement content recommendation system
-- @param userId: number - The user ID to get recommendations for
-- @return table - Array of recommended content
function ContentLoader.GetRecommendations(userId)
    local recommendations = {}
    
    -- Get user data from backend
    local userData = nil
    local success = pcall(function()
        local response = HttpService:GetAsync(API_BASE_URL .. "/users/" .. userId .. "/profile")
        userData = HttpService:JSONDecode(response)
    end)
    
    if not success or not userData then
        -- Fallback to default recommendations
        return {
            {contentId = "default_1", reason = "Popular content", score = 0.8},
            {contentId = "default_2", reason = "Beginner friendly", score = 0.7}
        }
    end
    
    -- Analyze user performance data
    local userLevel = userData.gradeLevel or 5
    local completedContent = userData.completedContent or {}
    local performanceScores = userData.performanceScores or {}
    local interests = userData.interests or {}
    
    -- Get all available content
    local availableContent = {}
    success = pcall(function()
        local response = HttpService:GetAsync(API_BASE_URL .. "/content/available")
        availableContent = HttpService:JSONDecode(response)
    end)
    
    if not availableContent then
        return recommendations
    end
    
    -- Apply recommendation algorithm
    for _, content in ipairs(availableContent) do
        local score = 0
        local reasons = {}
        
        -- Skip already completed content
        if table.find(completedContent, content.id) then
            continue
        end
        
        -- Grade level matching (highest weight)
        if content.gradeLevel == userLevel then
            score = score + 0.4
            table.insert(reasons, "Matches your grade level")
        elseif math.abs(content.gradeLevel - userLevel) == 1 then
            score = score + 0.2
            table.insert(reasons, "Close to your grade level")
        end
        
        -- Interest matching
        for _, interest in ipairs(interests) do
            if content.subject == interest or content.tags and table.find(content.tags, interest) then
                score = score + 0.3
                table.insert(reasons, "Matches your interests")
                break
            end
        end
        
        -- Consider learning objectives
        if userData.currentObjectives then
            for _, objective in ipairs(userData.currentObjectives) do
                if content.objectives and table.find(content.objectives, objective) then
                    score = score + 0.2
                    table.insert(reasons, "Helps with current objectives")
                    break
                end
            end
        end
        
        -- Performance-based recommendations
        if userData.weakAreas and table.find(userData.weakAreas, content.subject) then
            score = score + 0.1
            table.insert(reasons, "Practice in area needing improvement")
        end
        
        -- Add to recommendations if score is high enough
        if score > 0.3 then
            table.insert(recommendations, {
                contentId = content.id,
                title = content.title,
                subject = content.subject,
                score = score,
                reasons = reasons
            })
        end
    end
    
    -- Sort by score (highest first)
    table.sort(recommendations, function(a, b)
        return a.score > b.score
    end)
    
    -- Return top 10 recommendations
    local topRecommendations = {}
    for i = 1, math.min(10, #recommendations) do
        topRecommendations[i] = recommendations[i]
    end
    
    return topRecommendations
end

-- Implement content search functionality
-- @param query: string - Search query
-- @param filters: table - Search filters (grade, subject, etc.)
-- @return table - Search results
function ContentLoader.SearchContent(query, filters)
    local searchResults = {}
    filters = filters or {}
    
    -- Parse search query
    query = query:lower():gsub("[^%w%s]", "") -- Remove special characters
    local searchTerms = {}
    for term in query:gmatch("%S+") do
        table.insert(searchTerms, term)
    end
    
    -- Build search request
    local searchParams = {
        q = HttpService:UrlEncode(query),
        page = filters.page or 1,
        limit = filters.limit or 20
    }
    
    -- Apply filters
    if filters.grade then
        searchParams.grade = filters.grade
    end
    if filters.subject then
        searchParams.subject = HttpService:UrlEncode(filters.subject)
    end
    if filters.type then
        searchParams.type = filters.type
    end
    if filters.difficulty then
        searchParams.difficulty = filters.difficulty
    end
    
    -- Build query string
    local queryString = ""
    for key, value in pairs(searchParams) do
        if queryString == "" then
            queryString = "?" .. key .. "=" .. tostring(value)
        else
            queryString = queryString .. "&" .. key .. "=" .. tostring(value)
        end
    end
    
    -- Query backend search API
    local success, response = pcall(function()
        return HttpService:GetAsync(API_BASE_URL .. "/content/search" .. queryString)
    end)
    
    if success then
        local data = HttpService:JSONDecode(response)
        
        -- Process search results
        for _, item in ipairs(data.results or {}) do
            -- Calculate relevance score
            local relevanceScore = 0
            local itemText = (item.title .. " " .. item.description .. " " .. item.content):lower()
            
            for _, term in ipairs(searchTerms) do
                if itemText:find(term, 1, true) then
                    relevanceScore = relevanceScore + 1
                end
            end
            
            -- Add to results with relevance score
            table.insert(searchResults, {
                id = item.id,
                title = item.title,
                description = item.description,
                type = item.type,
                subject = item.subject,
                gradeLevel = item.gradeLevel,
                relevance = relevanceScore / #searchTerms,
                thumbnail = item.thumbnail
            })
        end
        
        -- Sort by relevance (if not already sorted by backend)
        if not filters.sortBy then
            table.sort(searchResults, function(a, b)
                return a.relevance > b.relevance
            end)
        end
        
        -- Add pagination info
        searchResults.pagination = {
            page = data.page or searchParams.page,
            totalPages = data.totalPages or 1,
            totalResults = data.totalResults or #searchResults,
            hasNext = data.hasNext or false,
            hasPrevious = data.hasPrevious or false
        }
    else
        HandleError("Search failed", {query = query, filters = filters})
    end
    
    return searchResults
end

-- Implement content rating system
-- @param contentId: string - The ID of content to rate
-- @param rating: number - Rating value (1-5)
-- @param feedback: string - Optional feedback text
function ContentLoader.RateContent(contentId, rating, feedback)
    -- Validate rating value
    if type(rating) ~= "number" or rating < 1 or rating > 5 then
        HandleError("Invalid rating value. Must be between 1 and 5", {rating = rating})
        return false
    end
    
    -- Validate feedback if provided
    if feedback and type(feedback) ~= "string" then
        feedback = tostring(feedback)
    end
    if feedback and #feedback > 500 then
        feedback = feedback:sub(1, 500) -- Limit feedback length
    end
    
    -- Prepare rating data
    local ratingData = {
        contentId = contentId,
        rating = rating,
        feedback = feedback or "",
        timestamp = os.time(),
        userId = game.Players.LocalPlayer and game.Players.LocalPlayer.UserId
    }
    
    -- Send to backend API
    local success, response = pcall(function()
        return HttpService:PostAsync(
            API_BASE_URL .. "/content/" .. contentId .. "/rate",
            HttpService:JSONEncode(ratingData),
            Enum.HttpContentType.ApplicationJson
        )
    end)
    
    if success then
        -- Update local cache
        if ContentCache[contentId] then
            if not ContentCache[contentId].ratings then
                ContentCache[contentId].ratings = {}
            end
            table.insert(ContentCache[contentId].ratings, ratingData)
            
            -- Calculate new average rating
            local totalRating = 0
            for _, r in ipairs(ContentCache[contentId].ratings) do
                totalRating = totalRating + r.rating
            end
            ContentCache[contentId].averageRating = totalRating / #ContentCache[contentId].ratings
        end
        
        -- Display confirmation to user
        if game.Players.LocalPlayer then
            local playerGui = game.Players.LocalPlayer:WaitForChild("PlayerGui")
            local confirmationGui = Instance.new("ScreenGui")
            confirmationGui.Name = "RatingConfirmation"
            confirmationGui.Parent = playerGui
            
            local frame = Instance.new("Frame")
            frame.Size = UDim2.new(0.3, 0, 0.1, 0)
            frame.Position = UDim2.new(0.35, 0, 0.45, 0)
            frame.BackgroundColor3 = Color3.new(0.2, 0.8, 0.2)
            frame.Parent = confirmationGui
            
            local label = Instance.new("TextLabel")
            label.Size = UDim2.new(1, 0, 1, 0)
            label.Text = "Thank you for your feedback!"
            label.TextScaled = true
            label.BackgroundTransparency = 1
            label.TextColor3 = Color3.new(1, 1, 1)
            label.Parent = frame
            
            -- Auto-remove after 3 seconds
            wait(3)
            confirmationGui:Destroy()
        end
        
        print("Content rated successfully:", contentId, "Rating:", rating)
        return true
    else
        HandleError("Failed to submit rating", ratingData)
        return false
    end
end

return ContentLoader
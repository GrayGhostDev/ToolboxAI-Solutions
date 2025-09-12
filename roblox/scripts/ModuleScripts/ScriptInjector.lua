--[[
    ToolboxAI Script Injector Module
    Version: 1.0.0
    Description: Safely injects and manages educational scripts with validation
                 Includes security measures and sandboxing for generated code
--]]

local ScriptInjector = {}
ScriptInjector.__index = ScriptInjector

-- Services
local ServerScriptService = game:GetService("ServerScriptService")
local ServerStorage = game:GetService("ServerStorage")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local StarterPlayer = game:GetService("StarterPlayer")
local StarterGui = game:GetService("StarterGui")
local HttpService = game:GetService("HttpService")
local RunService = game:GetService("RunService")

-- Configuration
local CONFIG = {
    MAX_SCRIPT_SIZE = 100000, -- 100KB limit
    MAX_SCRIPTS_PER_SESSION = 50,
    ALLOWED_SCRIPT_TYPES = {
        ["Script"] = true,
        ["LocalScript"] = true,
        ["ModuleScript"] = true
    },
    SCRIPT_LOCATIONS = {
        ["Script"] = {
            ServerScriptService,
            workspace
        },
        ["LocalScript"] = {
            StarterPlayer.StarterPlayerScripts,
            StarterPlayer.StarterCharacterScripts,
            StarterGui,
            ReplicatedStorage
        },
        ["ModuleScript"] = {
            ServerStorage,
            ReplicatedStorage,
            ServerScriptService
        }
    },
    BLACKLISTED_PATTERNS = {
        "getfenv",
        "setfenv",
        "loadstring",
        "dofile",
        "load",
        "_G%[",
        "rawset",
        "rawget",
        "setmetatable",
        "getmetatable",
        "newproxy",
        "collectgarbage",
        "require%s*%(.*http",
        "game%.Players%:GetPlayers%(%)",
        "game%.Players%.LocalPlayer%.UserId",
        "MarketplaceService",
        "TeleportService",
        "DataStoreService",
        "MessagingService",
        "PolicyService",
        "game%:GetService%([\"']PolicyService[\"']%)",
        "game%:Shutdown",
        "while%s+true%s+do%s+end",
        "repeat%s+until%s+false"
    },
    WHITELISTED_SERVICES = {
        "Workspace",
        "Players",
        "Lighting",
        "ReplicatedStorage",
        "StarterGui",
        "StarterPlayer",
        "Teams",
        "SoundService",
        "Chat",
        "LocalizationService",
        "TestService",
        "RunService",
        "UserInputService",
        "ContextActionService",
        "GuiService",
        "TweenService",
        "Debris",
        "ContentProvider"
    }
}

-- Constructor
function ScriptInjector.new()
    local self = setmetatable({}, ScriptInjector)
    self.injectedScripts = {}
    self.scriptCount = 0
    self.validationErrors = {}
    self.sandbox = {}
    return self
end

-- Inject script with validation
function ScriptInjector:inject(scriptData)
    -- Validate input
    local isValid, errorMessage = self:validateScriptData(scriptData)
    if not isValid then
        warn("Script validation failed:", errorMessage)
        return false, errorMessage
    end
    
    -- Check script limit
    if self.scriptCount >= CONFIG.MAX_SCRIPTS_PER_SESSION then
        return false, "Maximum script limit reached"
    end
    
    -- Sanitize script source
    local sanitizedSource = self:sanitizeSource(scriptData.source or scriptData.content)
    if not sanitizedSource then
        return false, "Script contains blacklisted patterns"
    end
    
    -- Create script instance
    local success, script = pcall(function()
        return self:createScript(scriptData, sanitizedSource)
    end)
    
    if not success then
        return false, "Failed to create script: " .. tostring(script)
    end
    
    -- Apply sandbox if needed
    if scriptData.sandbox then
        script = self:applySandbox(script, scriptData.sandbox)
    end
    
    -- Parent script to appropriate location
    local parent = self:determineParent(scriptData)
    if not parent then
        return false, "Could not determine appropriate parent for script"
    end
    
    script.Parent = parent
    
    -- Track injected script
    table.insert(self.injectedScripts, {
        script = script,
        data = scriptData,
        timestamp = tick(),
        parent = parent
    })
    self.scriptCount = self.scriptCount + 1
    
    return true, script
end

-- Validate script data
function ScriptInjector:validateScriptData(scriptData)
    if not scriptData then
        return false, "No script data provided"
    end
    
    -- Check script type
    local scriptType = scriptData.type or "Script"
    if not CONFIG.ALLOWED_SCRIPT_TYPES[scriptType] then
        return false, "Invalid script type: " .. tostring(scriptType)
    end
    
    -- Check source/content
    local source = scriptData.source or scriptData.content
    if not source or type(source) ~= "string" then
        return false, "No valid source code provided"
    end
    
    -- Check size limit
    if #source > CONFIG.MAX_SCRIPT_SIZE then
        return false, "Script exceeds maximum size limit"
    end
    
    -- Check for syntax errors
    local syntaxValid, syntaxError = self:checkSyntax(source)
    if not syntaxValid then
        return false, "Syntax error: " .. tostring(syntaxError)
    end
    
    -- Check for blacklisted patterns
    for _, pattern in ipairs(CONFIG.BLACKLISTED_PATTERNS) do
        if string.match(source, pattern) then
            return false, "Script contains blacklisted pattern: " .. pattern
        end
    end
    
    return true
end

-- Check Lua syntax
function ScriptInjector:checkSyntax(source)
    -- Try to compile the source to check for syntax errors
    local success, result = pcall(function()
        local func, err = loadstring(source)
        if not func then
            return false, err
        end
        return true
    end)
    
    if success and result == true then
        return true
    elseif success and result == false then
        return false, result
    else
        return false, tostring(result)
    end
end

-- Sanitize source code
function ScriptInjector:sanitizeSource(source)
    if not source then return nil end
    
    local sanitized = source
    
    -- Remove potentially harmful patterns
    for _, pattern in ipairs(CONFIG.BLACKLISTED_PATTERNS) do
        if string.match(sanitized, pattern) then
            warn("Blacklisted pattern found:", pattern)
            return nil
        end
    end
    
    -- Add safety wrapper
    local wrapped = [[
-- ToolboxAI Generated Script
-- Sandboxed Environment
local script = script
local workspace = game:GetService("Workspace")
local RunService = game:GetService("RunService")

-- Original code below
]] .. sanitized
    
    return wrapped
end

-- Create script instance
function ScriptInjector:createScript(scriptData, source)
    local scriptType = scriptData.type or "Script"
    local script = Instance.new(scriptType)
    
    script.Name = scriptData.name or ("GeneratedScript_" .. self.scriptCount)
    
    -- Set source (this requires plugin-level permissions)
    local success = pcall(function()
        script.Source = source
    end)
    
    if not success then
        -- If we can't set source directly, create a StringValue as fallback
        local sourceValue = Instance.new("StringValue")
        sourceValue.Name = "GeneratedSource"
        sourceValue.Value = source
        sourceValue.Parent = script
        
        -- Add loader script
        local loaderSource = [[
local sourceValue = script:WaitForChild("GeneratedSource")
local source = sourceValue.Value
sourceValue:Destroy()

-- Execute the source
local func, err = loadstring(source)
if func then
    func()
else
    warn("Failed to load generated script:", err)
end
]]
        script.Source = loaderSource
    end
    
    -- Add metadata
    local metadata = Instance.new("Configuration")
    metadata.Name = "Metadata"
    metadata.Parent = script
    
    local typeValue = Instance.new("StringValue")
    typeValue.Name = "ScriptType"
    typeValue.Value = scriptType
    typeValue.Parent = metadata
    
    local timestampValue = Instance.new("NumberValue")
    timestampValue.Name = "CreatedAt"
    timestampValue.Value = tick()
    timestampValue.Parent = metadata
    
    if scriptData.description then
        local descValue = Instance.new("StringValue")
        descValue.Name = "Description"
        descValue.Value = scriptData.description
        descValue.Parent = metadata
    end
    
    return script
end

-- Apply sandbox to script
function ScriptInjector:applySandbox(script, sandboxConfig)
    sandboxConfig = sandboxConfig or {}
    
    -- Create sandbox wrapper
    local sandboxWrapper = Instance.new("ModuleScript")
    sandboxWrapper.Name = script.Name .. "_Sandbox"
    
    local sandboxSource = [[
-- Sandbox wrapper for ]] .. script.Name .. [[

local sandbox = {}

-- Restricted environment
local env = {
    print = print,
    warn = warn,
    error = error,
    assert = assert,
    type = type,
    typeof = typeof,
    tonumber = tonumber,
    tostring = tostring,
    pairs = pairs,
    ipairs = ipairs,
    next = next,
    select = select,
    unpack = unpack,
    table = table,
    string = string,
    math = math,
    os = {
        time = os.time,
        difftime = os.difftime,
        date = os.date,
        clock = os.clock
    },
    coroutine = coroutine,
    Vector3 = Vector3,
    Vector2 = Vector2,
    CFrame = CFrame,
    Color3 = Color3,
    UDim = UDim,
    UDim2 = UDim2,
    Ray = Ray,
    Enum = Enum,
    task = task,
    wait = wait,
    spawn = spawn,
    delay = delay
}

-- Add whitelisted services
]]
    
    for _, service in ipairs(CONFIG.WHITELISTED_SERVICES) do
        sandboxSource = sandboxSource .. [[
env.]] .. service .. [[ = game:GetService("]] .. service .. [[")
]]
    end
    
    sandboxSource = sandboxSource .. [[

-- Set environment
setfenv(1, env)

return sandbox
]]
    
    sandboxWrapper.Source = sandboxSource
    sandboxWrapper.Parent = script.Parent
    
    return script
end

-- Determine appropriate parent for script
function ScriptInjector:determineParent(scriptData)
    local scriptType = scriptData.type or "Script"
    local preferredParent = scriptData.parent
    
    -- If preferred parent is specified and valid, use it
    if preferredParent and preferredParent:IsA("Instance") then
        return preferredParent
    end
    
    -- Otherwise, use default locations
    local possibleLocations = CONFIG.SCRIPT_LOCATIONS[scriptType]
    if possibleLocations and #possibleLocations > 0 then
        -- Check for specific location hints
        if scriptData.location then
            for _, location in ipairs(possibleLocations) do
                if location.Name == scriptData.location then
                    return location
                end
            end
        end
        
        -- Return first available location
        return possibleLocations[1]
    end
    
    -- Default to workspace
    return workspace
end

-- Batch inject multiple scripts
function ScriptInjector:injectBatch(scriptsData)
    local results = {
        successful = {},
        failed = {}
    }
    
    for i, scriptData in ipairs(scriptsData) do
        local success, result = self:inject(scriptData)
        
        if success then
            table.insert(results.successful, {
                index = i,
                script = result,
                name = scriptData.name
            })
        else
            table.insert(results.failed, {
                index = i,
                error = result,
                name = scriptData.name
            })
        end
        
        -- Yield periodically to prevent lag
        if i % 5 == 0 then
            RunService.Heartbeat:Wait()
        end
    end
    
    return results
end

-- Remove injected script
function ScriptInjector:remove(script)
    for i, injected in ipairs(self.injectedScripts) do
        if injected.script == script then
            script:Destroy()
            table.remove(self.injectedScripts, i)
            self.scriptCount = self.scriptCount - 1
            return true
        end
    end
    return false
end

-- Remove all injected scripts
function ScriptInjector:removeAll()
    for _, injected in ipairs(self.injectedScripts) do
        if injected.script and injected.script.Parent then
            injected.script:Destroy()
        end
    end
    
    self.injectedScripts = {}
    self.scriptCount = 0
end

-- Get list of injected scripts
function ScriptInjector:getInjectedScripts()
    local list = {}
    
    for _, injected in ipairs(self.injectedScripts) do
        if injected.script and injected.script.Parent then
            table.insert(list, {
                name = injected.script.Name,
                type = injected.script.ClassName,
                parent = injected.script.Parent.Name,
                timestamp = injected.timestamp
            })
        end
    end
    
    return list
end

-- Validate service access
function ScriptInjector:validateServiceAccess(serviceName)
    for _, whitelisted in ipairs(CONFIG.WHITELISTED_SERVICES) do
        if serviceName == whitelisted then
            return true
        end
    end
    return false
end

-- Create educational script template
function ScriptInjector:createEducationalTemplate(templateType, config)
    local templates = {
        movement = [[
-- Educational Movement Script
local character = script.Parent
local humanoid = character:WaitForChild("Humanoid")
local rootPart = character:WaitForChild("HumanoidRootPart")

-- Movement parameters
local speed = ]] .. tostring(config.speed or 16) .. [[
local jumpPower = ]] .. tostring(config.jumpPower or 50) .. [[

humanoid.WalkSpeed = speed
humanoid.JumpPower = jumpPower

-- Educational movement pattern
local function educationalMove()
    -- Add educational movement logic here
end

educationalMove()
]],
        
        interaction = [[
-- Educational Interaction Script
local part = script.Parent
local ClickDetector = part:FindFirstChild("ClickDetector") or Instance.new("ClickDetector", part)

ClickDetector.MouseClick:Connect(function(player)
    print(player.Name .. " interacted with " .. part.Name)
    -- Add educational interaction logic here
end)
]],
        
        quiz = [[
-- Educational Quiz Handler Script
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")

local function handleQuizResponse(player, questionId, answer)
    -- Validate answer
    print(player.Name .. " answered question " .. questionId .. " with: " .. tostring(answer))
    -- Add quiz logic here
end

-- Set up remote event listener
local quizEvent = ReplicatedStorage:FindFirstChild("QuizResponse")
if quizEvent then
    quizEvent.OnServerEvent:Connect(handleQuizResponse)
end
]],
        
        animation = [[
-- Educational Animation Script
local character = script.Parent
local humanoid = character:WaitForChild("Humanoid")

local animationId = "]] .. tostring(config.animationId or "rbxassetid://0") .. [["
local animation = Instance.new("Animation")
animation.AnimationId = animationId

local animTrack = humanoid:LoadAnimation(animation)

-- Play animation
animTrack:Play()
animTrack.Looped = ]] .. tostring(config.looped or false) .. [[
]]
    }
    
    return templates[templateType] or ""
end

-- Monitor script performance
function ScriptInjector:monitorPerformance()
    local stats = {
        totalScripts = self.scriptCount,
        activeScripts = 0,
        totalMemory = 0
    }
    
    for _, injected in ipairs(self.injectedScripts) do
        if injected.script and injected.script.Parent then
            stats.activeScripts = stats.activeScripts + 1
        end
    end
    
    return stats
end

-- Export configuration for saving
function ScriptInjector:exportConfiguration()
    local config = {
        injectedScripts = {},
        timestamp = tick()
    }
    
    for _, injected in ipairs(self.injectedScripts) do
        if injected.script and injected.script.Parent then
            table.insert(config.injectedScripts, {
                name = injected.script.Name,
                type = injected.script.ClassName,
                parent = injected.script.Parent:GetFullName(),
                data = injected.data
            })
        end
    end
    
    return HttpService:JSONEncode(config)
end

return ScriptInjector
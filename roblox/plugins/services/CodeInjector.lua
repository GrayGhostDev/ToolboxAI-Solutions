--!strict
--[[
    Code Injector Service
    Handles live code injection and hot module replacement in Roblox Studio
    Provides safe sandboxing and state preservation
]]

local RunService = game:GetService("RunService")
local ScriptEditorService = game:GetService("ScriptEditorService")
local ChangeHistoryService = game:GetService("ChangeHistoryService")
local Selection = game:GetService("Selection")
local HttpService = game:GetService("HttpService")
local LogService = game:GetService("LogService")
local StudioService = game:GetService("StudioService")

-- Types
type InjectionTarget = Script | LocalScript | ModuleScript

type InjectionConfig = {
    preserveState: boolean,
    sandbox: boolean,
    timeout: number,
    memoryLimit: number,
    cpuLimit: number,
    autoReload: boolean,
    validation: boolean
}

type ModuleState = {
    variables: {[string]: any},
    functions: {[string]: any},
    connections: {RBXScriptConnection},
    instances: {Instance},
    metadata: {[string]: any}
}

type InjectionResult = {
    success: boolean,
    target: Instance,
    oldSource: string,
    newSource: string,
    state: ModuleState?,
    error: string?,
    performance: {
        injectionTime: number,
        compilationTime: number,
        executionTime: number,
        memoryUsed: number
    }
}

type HotReloadSession = {
    id: string,
    targets: {InjectionTarget},
    states: {[Instance]: ModuleState},
    startTime: number,
    changeCount: number,
    errors: {string}
}

type ValidationResult = {
    valid: boolean,
    errors: {string},
    warnings: {string},
    suggestions: {string}
}

-- Code Injector Class
local CodeInjector = {}
CodeInjector.__index = CodeInjector

function CodeInjector.new(config: any, stateManager: any, eventEmitter: any)
    local self = setmetatable({}, CodeInjector)

    self.config = config
    self.stateManager = stateManager
    self.eventEmitter = eventEmitter

    -- Injection state
    self.activeTargets = {} -- Currently monitored scripts
    self.savedStates = {} -- Preserved states for hot reload
    self.injectionQueue = {} -- Pending injections
    self.hotReloadSessions = {} -- Active hot reload sessions

    -- Sandboxing
    self.sandboxEnvironments = {} -- Isolated environments
    self.resourceLimits = {} -- Resource tracking

    -- Performance monitoring
    self.performanceMetrics = {
        totalInjections = 0,
        successfulInjections = 0,
        failedInjections = 0,
        averageInjectionTime = 0,
        totalMemoryUsed = 0
    }

    -- File watchers
    self.fileWatchers = {}
    self.watchInterval = 1 -- seconds

    -- Default config
    self.defaultConfig: InjectionConfig = {
        preserveState = true,
        sandbox = true,
        timeout = 5000,
        memoryLimit = 50 * 1024 * 1024, -- 50MB
        cpuLimit = 1000, -- milliseconds
        autoReload = true,
        validation = true
    }

    -- Initialize
    self:initialize()

    return self
end

function CodeInjector:initialize()
    -- Setup script change detection
    self:setupChangeDetection()

    -- Setup sandbox environments
    self:setupSandboxes()

    -- Start monitoring
    self:startMonitoring()

    print("[CodeInjector] Initialized")
end

function CodeInjector:injectCode(target: InjectionTarget, newSource: string, config: InjectionConfig?): InjectionResult
    config = config or self.defaultConfig

    local startTime = os.clock()
    local result: InjectionResult = {
        success = false,
        target = target,
        oldSource = target.Source,
        newSource = newSource,
        performance = {
            injectionTime = 0,
            compilationTime = 0,
            executionTime = 0,
            memoryUsed = 0
        }
    }

    -- Validate code if enabled
    if config.validation then
        local validation = self:validateCode(newSource, target.ClassName)
        if not validation.valid then
            result.error = "Validation failed: " .. table.concat(validation.errors, "; ")
            self.eventEmitter:emit("injectionFailed", result)
            return result
        end
    end

    -- Preserve state if enabled
    if config.preserveState then
        result.state = self:captureState(target)
        self.savedStates[target] = result.state
    end

    -- Create sandbox if enabled
    local environment = nil
    if config.sandbox then
        environment = self:createSandbox(target, config)
    end

    -- Perform injection
    local injectionSuccess = false
    local injectionError = nil

    -- Record compilation time
    local compileStart = os.clock()

    local success, error = pcall(function()
        -- Set waypoint for undo
        ChangeHistoryService:SetWaypoint("Before Code Injection")

        -- Update source
        target.Source = newSource

        -- Test compilation
        local testFunc, compileError = loadstring(newSource)
        if not testFunc then
            error("Compilation failed: " .. (compileError or "Unknown error"))
        end

        result.performance.compilationTime = os.clock() - compileStart

        -- Execute in sandbox if configured
        if environment then
            local execStart = os.clock()
            setfenv(testFunc, environment)

            -- Run with timeout
            local thread = coroutine.create(testFunc)
            local startExec = os.clock()

            while coroutine.status(thread) ~= "dead" do
                if (os.clock() - startExec) * 1000 > config.timeout then
                    error("Execution timeout exceeded")
                end

                local ok, err = coroutine.resume(thread)
                if not ok then
                    error("Execution error: " .. tostring(err))
                end

                task.wait()
            end

            result.performance.executionTime = os.clock() - execStart
        end

        injectionSuccess = true

        -- Set waypoint after successful injection
        ChangeHistoryService:SetWaypoint("After Code Injection")
    end)

    if not success then
        injectionError = error

        -- Rollback on failure
        target.Source = result.oldSource
        result.error = tostring(injectionError)

        self.performanceMetrics.failedInjections = self.performanceMetrics.failedInjections + 1
    else
        result.success = true

        -- Restore state if preserved
        if config.preserveState and result.state then
            self:restoreState(target, result.state)
        end

        self.performanceMetrics.successfulInjections = self.performanceMetrics.successfulInjections + 1
    end

    -- Calculate metrics
    result.performance.injectionTime = os.clock() - startTime
    result.performance.memoryUsed = collectgarbage("count") * 1024

    -- Update statistics
    self.performanceMetrics.totalInjections = self.performanceMetrics.totalInjections + 1
    self.performanceMetrics.averageInjectionTime =
        (self.performanceMetrics.averageInjectionTime * (self.performanceMetrics.totalInjections - 1) +
         result.performance.injectionTime) / self.performanceMetrics.totalInjections
    self.performanceMetrics.totalMemoryUsed = self.performanceMetrics.totalMemoryUsed + result.performance.memoryUsed

    -- Emit event
    if result.success then
        self.eventEmitter:emit("codeInjected", result)
    else
        self.eventEmitter:emit("injectionFailed", result)
    end

    return result
end

function CodeInjector:startHotReload(targets: {InjectionTarget}): string
    local sessionId = HttpService:GenerateGUID(false)

    local session: HotReloadSession = {
        id = sessionId,
        targets = targets,
        states = {},
        startTime = os.time(),
        changeCount = 0,
        errors = {}
    }

    -- Capture initial states
    for _, target in ipairs(targets) do
        session.states[target] = self:captureState(target)
        self:watchScript(target)
    end

    self.hotReloadSessions[sessionId] = session

    -- Start monitoring for changes
    self:startHotReloadMonitoring(sessionId)

    self.eventEmitter:emit("hotReloadStarted", {
        sessionId = sessionId,
        targetCount = #targets
    })

    print("[CodeInjector] Hot reload session started:", sessionId)

    return sessionId
end

function CodeInjector:stopHotReload(sessionId: string)
    local session = self.hotReloadSessions[sessionId]
    if not session then
        return
    end

    -- Stop watching scripts
    for _, target in ipairs(session.targets) do
        self:unwatchScript(target)
    end

    -- Clean up session
    self.hotReloadSessions[sessionId] = nil

    self.eventEmitter:emit("hotReloadStopped", {
        sessionId = sessionId,
        changeCount = session.changeCount,
        duration = os.time() - session.startTime
    })

    print("[CodeInjector] Hot reload session stopped:", sessionId)
end

function CodeInjector:watchScript(script: InjectionTarget)
    if self.fileWatchers[script] then
        return
    end

    self.fileWatchers[script] = {
        lastSource = script.Source,
        lastModified = os.time(),
        checksum = self:calculateChecksum(script.Source)
    }

    self.activeTargets[script] = true
end

function CodeInjector:unwatchScript(script: InjectionTarget)
    self.fileWatchers[script] = nil
    self.activeTargets[script] = nil
    self.savedStates[script] = nil
end

function CodeInjector:startHotReloadMonitoring(sessionId: string)
    task.spawn(function()
        while self.hotReloadSessions[sessionId] do
            local session = self.hotReloadSessions[sessionId]

            for _, target in ipairs(session.targets) do
                if target and target.Parent then
                    self:checkForChanges(target, sessionId)
                end
            end

            task.wait(self.watchInterval)
        end
    end)
end

function CodeInjector:checkForChanges(script: InjectionTarget, sessionId: string)
    local watcher = self.fileWatchers[script]
    if not watcher then
        return
    end

    local currentChecksum = self:calculateChecksum(script.Source)
    if currentChecksum ~= watcher.checksum then
        -- Source changed, trigger hot reload
        self:performHotReload(script, sessionId)
        watcher.checksum = currentChecksum
        watcher.lastModified = os.time()
    end
end

function CodeInjector:performHotReload(script: InjectionTarget, sessionId: string)
    local session = self.hotReloadSessions[sessionId]
    if not session then
        return
    end

    -- Get preserved state
    local state = session.states[script] or self.savedStates[script]

    -- Inject new code with state preservation
    local result = self:injectCode(script, script.Source, {
        preserveState = true,
        sandbox = self.defaultConfig.sandbox,
        timeout = self.defaultConfig.timeout,
        memoryLimit = self.defaultConfig.memoryLimit,
        cpuLimit = self.defaultConfig.cpuLimit,
        autoReload = false,
        validation = true
    })

    if result.success then
        session.changeCount = session.changeCount + 1
        print("[CodeInjector] Hot reloaded:", script.Name)
    else
        table.insert(session.errors, result.error or "Unknown error")
        warn("[CodeInjector] Hot reload failed:", script.Name, result.error)
    end

    self.eventEmitter:emit("hotReloadApplied", {
        sessionId = sessionId,
        script = script,
        success = result.success,
        changeNumber = session.changeCount
    })
end

function CodeInjector:captureState(script: InjectionTarget): ModuleState
    local state: ModuleState = {
        variables = {},
        functions = {},
        connections = {},
        instances = {},
        metadata = {
            capturedAt = os.time(),
            scriptName = script.Name,
            scriptClass = script.ClassName
        }
    }

    -- Try to capture environment if script is running
    local success, env = pcall(function()
        return getfenv(script)
    end)

    if success and env then
        -- Capture variables (excluding functions and Roblox services)
        for key, value in pairs(env) do
            local valueType = type(value)
            if valueType ~= "function" and
               valueType ~= "userdata" and
               not game:GetService(key) then
                state.variables[key] = value
            elseif valueType == "function" then
                state.functions[key] = true -- Mark function exists
            end
        end
    end

    -- Capture connections (simplified - would need more complex implementation)
    -- This would require tracking connections during script execution

    return state
end

function CodeInjector:restoreState(script: InjectionTarget, state: ModuleState)
    if not state or not state.variables then
        return
    end

    -- Attempt to restore variables to script environment
    local success, error = pcall(function()
        local env = getfenv(script)
        if env then
            for key, value in pairs(state.variables) do
                env[key] = value
            end
        end
    end)

    if success then
        print("[CodeInjector] State restored for:", script.Name)
    else
        warn("[CodeInjector] Failed to restore state:", error)
    end

    self.eventEmitter:emit("stateRestored", {
        script = script,
        variableCount = #state.variables
    })
end

function CodeInjector:validateCode(source: string, scriptType: string): ValidationResult
    local result: ValidationResult = {
        valid = true,
        errors = {},
        warnings = {},
        suggestions = {}
    }

    -- Check for syntax errors
    local func, error = loadstring(source)
    if not func then
        table.insert(result.errors, "Syntax error: " .. (error or "Unknown"))
        result.valid = false
        return result
    end

    -- Check for common issues
    self:checkForCommonIssues(source, result)

    -- Check for performance issues
    self:checkForPerformanceIssues(source, result)

    -- Check for security issues
    self:checkForSecurityIssues(source, result)

    -- Type-specific validation
    if scriptType == "LocalScript" then
        self:validateLocalScript(source, result)
    elseif scriptType == "ModuleScript" then
        self:validateModuleScript(source, result)
    end

    return result
end

function CodeInjector:checkForCommonIssues(source: string, result: ValidationResult)
    -- Check for infinite loops
    if string.find(source, "while%s+true%s+do") and
       not string.find(source, "wait") and
       not string.find(source, "task%.wait") then
        table.insert(result.warnings, "Potential infinite loop detected without yield")
    end

    -- Check for deprecated functions
    local deprecated = {
        "wait%(", "spawn%(", "delay%("
    }
    for _, pattern in ipairs(deprecated) do
        if string.find(source, pattern) then
            table.insert(result.warnings, "Using deprecated function: " .. pattern:gsub("%%", ""):gsub("%(", ""))
            table.insert(result.suggestions, "Consider using task library equivalents")
        end
    end

    -- Check for memory leaks
    if string.find(source, "%.Connected%s*=") and not string.find(source, ":Disconnect%(%)") then
        table.insert(result.warnings, "Potential memory leak: Connection without disconnect")
    end
end

function CodeInjector:checkForPerformanceIssues(source: string, result: ValidationResult)
    -- Check for expensive operations in loops
    local loopPatterns = {"for%s+.-%s+do", "while%s+.-%s+do", "repeat%s+"}
    local expensiveOps = {"Instance%.new", "game:GetService", ":FindFirstChild", ":WaitForChild"}

    for _, loopPattern in ipairs(loopPatterns) do
        local loopStart, loopEnd = string.find(source, loopPattern)
        if loopStart then
            local loopBody = string.sub(source, loopStart, string.find(source, "end", loopEnd) or #source)

            for _, op in ipairs(expensiveOps) do
                if string.find(loopBody, op) then
                    table.insert(result.warnings, "Expensive operation '" .. op .. "' inside loop")
                    table.insert(result.suggestions, "Consider moving " .. op .. " outside the loop")
                end
            end
        end
    end

    -- Check for excessive string concatenation
    local concatCount = select(2, string.gsub(source, "%.%.", ""))
    if concatCount > 10 then
        table.insert(result.warnings, "Excessive string concatenation detected")
        table.insert(result.suggestions, "Consider using table.concat for better performance")
    end
end

function CodeInjector:checkForSecurityIssues(source: string, result: ValidationResult)
    -- Check for loadstring usage
    if string.find(source, "loadstring") then
        table.insert(result.errors, "Security risk: loadstring usage detected")
        result.valid = false
    end

    -- Check for require with dynamic paths
    if string.find(source, "require%(.-%.\\.") then
        table.insert(result.warnings, "Security concern: Dynamic require path")
    end

    -- Check for getfenv/setfenv
    if string.find(source, "[gs]etfenv") then
        table.insert(result.warnings, "Environment manipulation detected")
    end
end

function CodeInjector:validateLocalScript(source: string, result: ValidationResult)
    -- Check for server-only services
    local serverOnlyServices = {
        "ServerScriptService",
        "ServerStorage"
    }

    for _, service in ipairs(serverOnlyServices) do
        if string.find(source, 'game:GetService%("' .. service .. '"%)')  or
           string.find(source, "game%." .. service) then
            table.insert(result.errors, "LocalScript cannot access " .. service)
            result.valid = false
        end
    end
end

function CodeInjector:validateModuleScript(source: string, result: ValidationResult)
    -- Check if module returns something
    if not string.find(source, "return%s+") then
        table.insert(result.warnings, "ModuleScript does not return anything")
        table.insert(result.suggestions, "ModuleScripts should return a value or table")
    end
end

function CodeInjector:createSandbox(script: InjectionTarget, config: InjectionConfig): any
    local sandbox = {
        -- Safe globals
        print = print,
        warn = warn,
        error = error,
        assert = assert,
        type = type,
        typeof = typeof,
        pairs = pairs,
        ipairs = ipairs,
        next = next,
        select = select,
        tonumber = tonumber,
        tostring = tostring,
        math = math,
        string = string,
        table = table,
        coroutine = coroutine,
        os = {
            time = os.time,
            clock = os.clock,
            date = os.date
        },

        -- Roblox globals
        game = game,
        workspace = workspace,
        script = script,
        shared = shared,
        _VERSION = _VERSION,

        -- Task library
        task = task,
        wait = task.wait,

        -- Controlled functions
        require = function(module)
            -- Track and validate requires
            if self:isModuleSafe(module) then
                return require(module)
            else
                error("Unsafe module require blocked: " .. tostring(module))
            end
        end,

        Instance = setmetatable({}, {
            __index = function(_, key)
                if key == "new" then
                    return function(className)
                        -- Track instance creation
                        self:trackResourceUsage("instance", 1)
                        return Instance.new(className)
                    end
                end
                return Instance[key]
            end
        })
    }

    -- Add metatables for protection
    setmetatable(sandbox, {
        __index = function(_, key)
            if key == "getfenv" or key == "setfenv" then
                error("Environment manipulation not allowed in sandbox")
            end
            return nil
        end,
        __newindex = function(_, key, value)
            error("Cannot modify sandbox environment")
        end
    })

    self.sandboxEnvironments[script] = sandbox
    return sandbox
end

function CodeInjector:isModuleSafe(module: any): boolean
    -- Implement module safety checks
    if typeof(module) ~= "Instance" then
        return false
    end

    if not module:IsA("ModuleScript") then
        return false
    end

    -- Check if module is from a trusted source
    local parent = module.Parent
    while parent do
        if parent == game.ServerScriptService or
           parent == game.ReplicatedStorage or
           parent == game.StarterPlayer then
            return true
        end
        parent = parent.Parent
    end

    return false
end

function CodeInjector:trackResourceUsage(resourceType: string, amount: number)
    if not self.resourceLimits[resourceType] then
        self.resourceLimits[resourceType] = 0
    end

    self.resourceLimits[resourceType] = self.resourceLimits[resourceType] + amount

    -- Check limits
    if resourceType == "instance" and self.resourceLimits[resourceType] > 1000 then
        error("Resource limit exceeded: Too many instances created")
    elseif resourceType == "memory" and self.resourceLimits[resourceType] > self.defaultConfig.memoryLimit then
        error("Memory limit exceeded")
    end
end

function CodeInjector:calculateChecksum(source: string): string
    -- Simple checksum for change detection
    local sum = 0
    for i = 1, #source do
        sum = (sum * 31 + string.byte(source, i)) % 2147483647
    end
    return tostring(sum)
end

function CodeInjector:setupChangeDetection()
    -- Monitor script changes in Studio
    if ScriptEditorService then
        pcall(function()
            ScriptEditorService.TextDocumentDidChange:Connect(function(document, changes)
                local script = document:GetScript()
                if script and self.activeTargets[script] then
                    self.eventEmitter:emit("scriptEdited", {
                        script = script,
                        changes = changes
                    })
                end
            end)
        end)
    end
end

function CodeInjector:setupSandboxes()
    -- Initialize sandbox environments
    self.sandboxEnvironments = {}
    self.resourceLimits = {}
end

function CodeInjector:startMonitoring()
    -- Start performance monitoring
    task.spawn(function()
        while true do
            task.wait(60) -- Check every minute

            -- Clean up old states
            local now = os.time()
            for script, state in pairs(self.savedStates) do
                if state.metadata and state.metadata.capturedAt then
                    if now - state.metadata.capturedAt > 3600 then -- 1 hour
                        self.savedStates[script] = nil
                    end
                end
            end

            -- Report metrics
            if self.performanceMetrics.totalInjections > 0 then
                self.eventEmitter:emit("metricsUpdate", self.performanceMetrics)
            end
        end
    end)
end

function CodeInjector:injectBatch(injections: {{target: InjectionTarget, source: string}}): {InjectionResult}
    local results = {}

    for _, injection in ipairs(injections) do
        local result = self:injectCode(injection.target, injection.source)
        table.insert(results, result)
    end

    return results
end

function CodeInjector:getStatistics()
    return {
        activeTargets = #self.activeTargets,
        savedStates = #self.savedStates,
        hotReloadSessions = #self.hotReloadSessions,
        performance = self.performanceMetrics,
        resourceUsage = self.resourceLimits
    }
end

function CodeInjector:cleanup()
    -- Stop all hot reload sessions
    for sessionId in pairs(self.hotReloadSessions) do
        self:stopHotReload(sessionId)
    end

    -- Clear saved states
    self.savedStates = {}

    -- Clear sandboxes
    self.sandboxEnvironments = {}
    self.resourceLimits = {}

    -- Clear watchers
    self.fileWatchers = {}
    self.activeTargets = {}

    print("[CodeInjector] Cleanup completed")
end

return CodeInjector
--!strict
--[[
    HTTPClient Module
    Handles communication with Flask Bridge server for Roblox integration

    Endpoints:
    - /roblox/generate_script - Generate educational Lua scripts
    - /roblox/optimize_script - Optimize existing scripts
    - /roblox/validate_security - Validate script security
    - /roblox/deploy_content - Deploy content (mock for now)
    - /roblox/sync_status - Get sync status
    - /roblox/educational_content - Generate educational content
]]

local HttpService = game:GetService("HttpService")
local RunService = game:GetService("RunService")

local HTTPClient = {}
HTTPClient.__index = HTTPClient

-- Configuration
local CONFIG = {
    BASE_URL = "http://127.0.0.1:5001", -- Default: bridge server (overridden by Settings if available)
    TIMEOUT = 30,
    RETRY_ATTEMPTS = 3,
    RETRY_DELAY = 2
}

-- Type definitions
export type ScriptType = "ServerScript" | "LocalScript" | "ModuleScript"
export type OptimizationLevel = "conservative" | "balanced" | "aggressive"
export type GradeLevel = "elementary" | "middle" | "high"

export type GenerateScriptRequest = {
    script_type: ScriptType,
    requirements: string,
    educational_focus: string?
}

export type OptimizeScriptRequest = {
    script: string,
    optimization_level: OptimizationLevel
}

export type ValidateSecurityRequest = {
    script: string,
    script_type: ScriptType,
    strict_mode: boolean?
}

export type DeployContentRequest = {
    content_type: string,
    content_data: string,
    target_place_id: string
}

export type EducationalContentRequest = {
    subject: string,
    grade_level: GradeLevel,
    format: string
}

export type HTTPResponse = {
    success: boolean,
    data: any?,
    error: string?,
    message: string?
}

-- Constructor
function HTTPClient.new(baseUrl: string?)
    local self = setmetatable({}, HTTPClient)
    -- Try to load dynamic bridge URL from Settings if available
    local resolvedBase = baseUrl
    if not resolvedBase then
        local ok, Settings = pcall(function()
            return require(game.ServerStorage:WaitForChild("Config"):WaitForChild("settings"))
        end)
        if ok and Settings and Settings.API and Settings.API.getBridgeUrl then
            resolvedBase = Settings.API.getBridgeUrl() or CONFIG.BASE_URL
        else
            resolvedBase = CONFIG.BASE_URL
        end
    end
    self.baseUrl = resolvedBase
    self.headers = {
        ["Content-Type"] = "application/json",
        ["Accept"] = "application/json"
    }
    return self
end

-- Helper: Make HTTP request with retry logic
function HTTPClient:_makeRequest(method: string, endpoint: string, body: any?): HTTPResponse
    local url = self.baseUrl .. endpoint
    local attempts = 0
    local lastError = nil

    while attempts < CONFIG.RETRY_ATTEMPTS do
        attempts += 1

        local success, result = pcall(function()
            local requestOptions = {
                Url = url,
                Method = method,
                Headers = self.headers
            }

            if body then
                requestOptions.Body = HttpService:JSONEncode(body)
            end

            local response = HttpService:RequestAsync(requestOptions)

            if response.Success then
                local decoded = HttpService:JSONDecode(response.Body)
                return {
                    success = true,
                    data = decoded,
                    error = nil,
                    message = decoded.message
                }
            else
                return {
                    success = false,
                    data = nil,
                    error = "HTTP " .. response.StatusCode,
                    message = response.StatusMessage
                }
            end
        end)

        if success then
            return result
        else
            lastError = result
            if attempts < CONFIG.RETRY_ATTEMPTS then
                task.wait(CONFIG.RETRY_DELAY)
            end
        end
    end

    return {
        success = false,
        data = nil,
        error = tostring(lastError),
        message = "Failed after " .. CONFIG.RETRY_ATTEMPTS .. " attempts"
    }
end

-- Generate Roblox script using AI
function HTTPClient:generateScript(request: GenerateScriptRequest): HTTPResponse
    return self:_makeRequest("POST", "/roblox/generate_script", request)
end

-- Optimize existing script
function HTTPClient:optimizeScript(request: OptimizeScriptRequest): HTTPResponse
    return self:_makeRequest("POST", "/roblox/optimize_script", request)
end

-- Validate script security
function HTTPClient:validateSecurity(request: ValidateSecurityRequest): HTTPResponse
    return self:_makeRequest("POST", "/roblox/validate_security", request)
end

-- Deploy content (currently mock)
function HTTPClient:deployContent(request: DeployContentRequest): HTTPResponse
    return self:_makeRequest("POST", "/roblox/deploy_content", request)
end

-- Get sync status
function HTTPClient:getSyncStatus(): HTTPResponse
    return self:_makeRequest("GET", "/roblox/sync_status")
end

-- Generate educational content
function HTTPClient:generateEducationalContent(request: EducationalContentRequest): HTTPResponse
    return self:_makeRequest("POST", "/roblox/educational_content", request)
end

-- Health check
function HTTPClient:healthCheck(): HTTPResponse
    return self:_makeRequest("GET", "/health")
end

-- Convenience method: Generate and validate script
function HTTPClient:generateSafeScript(
    scriptType: ScriptType,
    requirements: string,
    educationalFocus: string?
): HTTPResponse
    -- First generate the script
    local genResponse = self:generateScript({
        script_type = scriptType,
        requirements = requirements,
        educational_focus = educationalFocus
    })

    if not genResponse.success or not genResponse.data then
        return genResponse
    end

    local generatedScript = genResponse.data.script

    -- Then validate its security
    local valResponse = self:validateSecurity({
        script = generatedScript,
        script_type = scriptType,
        strict_mode = true
    })

    if not valResponse.success or not valResponse.data then
        return {
            success = false,
            data = nil,
            error = "Security validation failed",
            message = valResponse.message
        }
    end

    -- Check if risk score is acceptable
    local riskScore = valResponse.data.risk_score
    if riskScore and riskScore > 5 then
        return {
            success = false,
            data = nil,
            error = "High risk score",
            message = "Generated script has high risk score: " .. tostring(riskScore)
        }
    end

    -- Return the validated script
    return {
        success = true,
        data = {
            script = generatedScript,
            metadata = genResponse.data.metadata,
            security = valResponse.data
        },
        error = nil,
        message = "Script generated and validated successfully"
    }
end

-- Batch operations
function HTTPClient:batchOptimize(scripts: {string}): {HTTPResponse}
    local results = {}

    for i, script in ipairs(scripts) do
        local response = self:optimizeScript({
            script = script,
            optimization_level = "balanced"
        })
        table.insert(results, response)

        -- Small delay between requests
        if i < #scripts then
            task.wait(0.1)
        end
    end

    return results
end

return HTTPClient

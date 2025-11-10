-- API integration for Ghost backend
-- Aligns with Settings + ApiClient for secure requests

local ServerStorage = game:GetService("ServerStorage")
local okSettings, Settings = pcall(function()
    return require(ServerStorage:WaitForChild("Config"):WaitForChild("settings"))
end)

local okApi, ApiClient = pcall(function()
    return require(game.ServerScriptService:WaitForChild("ApiClient"))
end)

local GhostAPI = {}
GhostAPI.__index = GhostAPI

function GhostAPI.new()
    local self = setmetatable({}, GhostAPI)
    self.baseUrl = (okSettings and Settings.API and Settings.API.getBaseUrl and Settings.API.getBaseUrl()) or "http://127.0.0.1:8009"
    return self
end

-- Example: fetch content metadata from Ghost backend
function GhostAPI:getContentMetadata(contentId)
    if not okApi then
        return nil, "ApiClient unavailable"
    end
    local success, result = pcall(function()
        return ApiClient.get("/api/v1/ghost/content/" .. tostring(contentId) .. "/metadata")
    end)
    if success then
        return result
    else
        return nil, tostring(result)
    end
end

return GhostAPI

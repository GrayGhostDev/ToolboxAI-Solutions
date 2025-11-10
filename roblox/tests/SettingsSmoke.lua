--[[
    SettingsSmoke.lua
    Validates that Settings and endpoint keys are present; does not perform network.
]]

local success, Settings = pcall(function()
    return require(game.ServerStorage:WaitForChild("Config"):WaitForChild("settings"))
end)

if not success then
    warn("[SettingsSmoke] Failed to require Settings: " .. tostring(Settings))
    return
end

local endpoints = Settings and Settings.API and Settings.API.endpoints or nil
if not endpoints then
    warn("[SettingsSmoke] Settings.API.endpoints missing")
    return
end

local requiredKeys = { "progress", "sessions", "playersJoin", "playersLeave" }
for _, key in ipairs(requiredKeys) do
    if not endpoints[key] then
        warn("[SettingsSmoke] Missing endpoint key: " .. key)
    else
        print("[SettingsSmoke] Endpoint key present: " .. key .. " -> " .. endpoints[key])
    end
end


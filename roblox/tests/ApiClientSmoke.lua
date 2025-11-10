--[[
    ApiClientSmoke.lua
    Minimal smoke test to verify ApiClient loads and basic calls are safe under pcall.
    Note: This is a development helper; network calls may fail if backend is not available.
]]

local successRequire, ApiClient = pcall(function()
    return require(game.ServerScriptService:WaitForChild("ApiClient"))
end)

if not successRequire then
    warn("[ApiClientSmoke] ApiClient require failed: " .. tostring(ApiClient))
    return
end

local ok, res = pcall(function()
    -- Use a harmless GET to a likely health endpoint; wrapped in pcall to avoid throwing in Studio
    return ApiClient.get("/health")
end)

if ok then
    print("[ApiClientSmoke] ApiClient GET /health invoked (result may be nil if backend is absent)")
else
    warn("[ApiClientSmoke] ApiClient GET /health failed: " .. tostring(res))
end

-- Verify endpoint-key utility does not throw
local ok2, res2 = pcall(function()
    return ApiClient.postKey("progress", { ping = os.time() })
end)

if ok2 then
    print("[ApiClientSmoke] ApiClient.postKey('progress') invoked")
else
    warn("[ApiClientSmoke] ApiClient.postKey('progress') failed: " .. tostring(res2))
end


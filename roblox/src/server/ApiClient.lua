--[[
    ApiClient - Secure server-side HTTP wrapper
    Uses Settings.makeSecureAPICall for consistency and security.
]]

local ServerStorage = game:GetService("ServerStorage")
local Settings = require(ServerStorage:WaitForChild("Config"):WaitForChild("settings"))

local ApiClient = {}
ApiClient.__index = ApiClient

function ApiClient.get(path)
    return Settings.makeSecureAPICall(path, "GET")
end

function ApiClient.post(path, data)
    return Settings.makeSecureAPICall(path, "POST", data)
end

function ApiClient.patch(path, data)
    return Settings.makeSecureAPICall(path, "PATCH", data)
end

function ApiClient.put(path, data)
    return Settings.makeSecureAPICall(path, "PUT", data)
end

function ApiClient.delete(path)
    return Settings.makeSecureAPICall(path, "DELETE")
end

-- Build endpoint path by key from Settings.API.endpoints
function ApiClient.buildPathByKey(key)
    local endpoints = Settings.API and Settings.API.endpoints
    if not endpoints then
        return nil, "Endpoints not configured"
    end
    local path = endpoints[key]
    if not path then
        return nil, "Unknown endpoint key: " .. tostring(key)
    end
    return path
end

function ApiClient.postKey(key, data)
    local path, err = ApiClient.buildPathByKey(key)
    if not path then return false, err end
    return ApiClient.post(path, data)
end

function ApiClient.getKey(key)
    local path, err = ApiClient.buildPathByKey(key)
    if not path then return false, err end
    return ApiClient.get(path)
end

function ApiClient.postKeyWithSuffix(key, suffix, data)
    local path, err = ApiClient.buildPathByKey(key)
    if not path then return false, err end
    return ApiClient.post(path .. (suffix or ""), data)
end

function ApiClient.getKeyWithSuffix(key, suffix)
    local path, err = ApiClient.buildPathByKey(key)
    if not path then return false, err end
    return ApiClient.get(path .. (suffix or ""))
end

return ApiClient

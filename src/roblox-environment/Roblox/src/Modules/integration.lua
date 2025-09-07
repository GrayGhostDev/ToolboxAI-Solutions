-- This file contains functions and logic for integrating the Roblox environment with the ToolboxAI-Dashboard API. It exports functions for making API calls and handling responses.

local HttpService = game:GetService("HttpService")

local API_URL = "https://api.toolboxai-dashboard.com" -- Replace with the actual API URL

local IntegrationModule = {}

function IntegrationModule.makeAPICall(endpoint, method, data)
    local url = API_URL .. endpoint
    local response

    local success, err = pcall(function()
        response = HttpService:RequestAsync({
            Url = url,
            Method = method,
            Headers = {
                ["Content-Type"] = "application/json"
            },
            Body = HttpService:JSONEncode(data)
        })
    end)

    if not success then
        warn("API call failed: " .. err)
        return nil
    end

    if response.StatusCode ~= 200 then
        warn("API call returned status: " .. response.StatusCode)
        return nil
    end

    return HttpService:JSONDecode(response.Body)
end

function IntegrationModule.getDashboardData()
    return IntegrationModule.makeAPICall("/dashboard/data", "GET")
end

function IntegrationModule.sendDataToDashboard(data)
    return IntegrationModule.makeAPICall("/dashboard/data", "POST", data)
end

return IntegrationModule
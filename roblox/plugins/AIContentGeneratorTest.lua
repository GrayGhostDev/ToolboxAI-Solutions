--[[
    ToolboxAI Content Generator Plugin - Integration Test
    Terminal 3 - Roblox Integration
    
    Instructions:
    1. Open Roblox Studio
    2. File → Settings → Security → Allow HTTP Requests: ON
    3. Plugins → Plugin Manager → Install Plugin from File
    4. Select this file or build with rojo
    5. Click the plugin button in toolbar to run tests
]]

local plugin = plugin or getfenv().PluginManager():CreatePlugin()
local toolbar = plugin:CreateToolbar("ToolboxAI Integration")
local button = toolbar:CreateButton(
    "Test Integration",
    "Test ToolboxAI Integration",
    "rbxasset://textures/ui/Settings/Help/QMark.png"
)

-- Services
local HttpService = game:GetService("HttpService")
local RunService = game:GetService("RunService")
local Selection = game:GetService("Selection")

-- Configuration
local CONFIG = {
    FLASK_URL = "http://127.0.0.1:5001",
    FASTAPI_URL = "http://127.0.0.1:8009",
    PLUGIN_ID = "toolboxai_plugin_" .. tostring(tick()),
    STUDIO_ID = "studio_" .. tostring(game.PlaceId or "test"),
    PORT = 64989,
    POLL_INTERVAL = 2
}

-- Plugin state
local pluginState = {
    registered = false,
    polling = false,
    sessionId = nil,
    authToken = nil,
    messageQueue = {},
    testResults = {}
}

-- UI Creation
local function createTestUI()
    local widgetInfo = DockWidgetPluginGuiInfo.new(
        Enum.InitialDockState.Float,
        false,
        false,
        400,
        600,
        400,
        300
    )
    
    local widget = plugin:CreateDockWidgetPluginGui("ToolboxAITests", widgetInfo)
    widget.Title = "ToolboxAI Integration Tests"
    
    -- Main frame
    local scrollFrame = Instance.new("ScrollingFrame")
    scrollFrame.Size = UDim2.new(1, 0, 1, 0)
    scrollFrame.CanvasSize = UDim2.new(0, 0, 0, 0)
    scrollFrame.ScrollBarThickness = 8
    scrollFrame.Parent = widget
    
    -- Output text
    local output = Instance.new("TextLabel")
    output.Size = UDim2.new(1, -10, 0, 0)
    output.Position = UDim2.new(0, 5, 0, 5)
    output.BackgroundTransparency = 1
    output.Text = "Click 'Test Integration' to start tests..."
    output.TextXAlignment = Enum.TextXAlignment.Left
    output.TextYAlignment = Enum.TextYAlignment.Top
    output.TextWrapped = true
    output.TextScaled = false
    output.TextSize = 14
    output.Font = Enum.Font.Code
    output.RichText = true
    output.Parent = scrollFrame
    
    return widget, output, scrollFrame
end

local testWidget, testOutput, scrollFrame = createTestUI()

-- Logging function
local function log(message, isError)
    local timestamp = os.date("%H:%M:%S")
    local prefix = isError and "[ERROR]" or "[INFO]"
    local color = isError and "rgb(255,100,100)" or "rgb(100,255,100)"
    
    testOutput.Text = testOutput.Text .. string.format(
        '\n<font color="%s">[%s] %s</font> %s',
        color, timestamp, prefix, message
    )
    
    -- Auto-scroll
    local textSize = testOutput.TextBounds
    testOutput.Size = UDim2.new(1, -10, 0, textSize.Y + 20)
    scrollFrame.CanvasSize = UDim2.new(0, 0, 0, textSize.Y + 30)
    scrollFrame.CanvasPosition = Vector2.new(0, math.max(0, textSize.Y - scrollFrame.AbsoluteSize.Y + 30))
    
    print("[ToolboxAI Plugin]", prefix, message)
end

-- HTTP Request wrapper
local function httpRequest(url, method, headers, body)
    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = url,
            Method = method or "GET",
            Headers = headers or {["Content-Type"] = "application/json"},
            Body = body and HttpService:JSONEncode(body) or nil
        })
    end)
    
    if not success then
        log("HTTP Request failed: " .. tostring(response), true)
        return nil
    end
    
    if response.Success then
        local decoded = pcall(function() return HttpService:JSONDecode(response.Body) end)
        if decoded then
            return HttpService:JSONDecode(response.Body)
        else
            return response.Body
        end
    else
        log("HTTP Error " .. response.StatusCode .. ": " .. response.StatusMessage, true)
        return nil
    end
end

-- Test Functions
local tests = {}

function tests.checkServices()
    log("Checking services...")
    
    -- Check Flask bridge
    local flaskHealth = httpRequest(CONFIG.FLASK_URL .. "/health")
    if flaskHealth and flaskHealth.status == "healthy" then
        log("✅ Flask bridge is healthy")
        pluginState.testResults["flask_health"] = true
    else
        log("❌ Flask bridge not responding", true)
        pluginState.testResults["flask_health"] = false
    end
    
    -- Check FastAPI
    local apiHealth = httpRequest(CONFIG.FASTAPI_URL .. "/health")
    if apiHealth and apiHealth.status == "healthy" then
        log("✅ FastAPI is healthy")
        pluginState.testResults["api_health"] = true
    else
        log("❌ FastAPI not responding", true)
        pluginState.testResults["api_health"] = false
    end
    
    return pluginState.testResults["flask_health"] and pluginState.testResults["api_health"]
end

function tests.registerPlugin()
    log("Registering plugin...")
    
    local payload = {
        plugin_id = CONFIG.PLUGIN_ID,
        studio_id = CONFIG.STUDIO_ID,
        port = CONFIG.PORT,
        version = "1.0.0",
        capabilities = {"content_generation", "quiz", "terrain", "script"}
    }
    
    local response = httpRequest(CONFIG.FLASK_URL .. "/register_plugin", "POST", nil, payload)
    
    if response and response.success then
        log("✅ Plugin registered: " .. CONFIG.PLUGIN_ID)
        pluginState.registered = true
        pluginState.testResults["registration"] = true
        return true
    else
        log("❌ Plugin registration failed", true)
        pluginState.testResults["registration"] = false
        return false
    end
end

function tests.testContentGeneration()
    log("Testing content generation...")
    
    local payload = {
        type = "quiz",
        subject = "Math",
        grade = 5,
        topic = "Fractions",
        num_questions = 3
    }
    
    local response = httpRequest(CONFIG.FLASK_URL .. "/plugin/content/generate", "POST", nil, payload)
    
    if response and response.content then
        log("✅ Content generation working")
        log("   Generated: " .. tostring(response.content.type or "unknown"))
        pluginState.testResults["content_gen"] = true
        
        -- Try to apply the content if it's valid
        if response.content.questions then
            log("   Found " .. #response.content.questions .. " questions")
        end
        return true
    else
        log("❌ Content generation failed", true)
        pluginState.testResults["content_gen"] = false
        return false
    end
end

function tests.testTerrainGeneration()
    log("Testing terrain generation...")
    
    local payload = {
        environment = "forest",
        size = "small",
        features = ["trees", "rocks"]
    }
    
    local response = httpRequest(CONFIG.FLASK_URL .. "/generate_terrain", "POST", nil, payload)
    
    if response and response.success then
        log("✅ Terrain generation working")
        pluginState.testResults["terrain_gen"] = true
        
        -- Apply terrain if data is valid
        if response.terrain_data and response.terrain_data.regions then
            local terrain = workspace.Terrain
            for _, region in ipairs(response.terrain_data.regions) do
                log("   Would create: " .. tostring(region.type) .. " at " .. tostring(region.x) .. "," .. tostring(region.y) .. "," .. tostring(region.z))
            end
        end
        return true
    else
        log("❌ Terrain generation failed", true)
        pluginState.testResults["terrain_gen"] = false
        return false
    end
end

function tests.testScriptRetrieval()
    log("Testing script retrieval...")
    
    local response = httpRequest(CONFIG.FLASK_URL .. "/script/quiz_ui", "GET")
    
    if response and (response.script or response.source) then
        log("✅ Script retrieval working")
        local scriptContent = response.script or response.source
        log("   Script length: " .. string.len(scriptContent) .. " characters")
        pluginState.testResults["script_retrieval"] = true
        return true
    else
        log("❌ Script retrieval failed", true)
        pluginState.testResults["script_retrieval"] = false
        return false
    end
end

function tests.testPolling()
    log("Testing message polling...")
    
    local payload = {
        plugin_id = CONFIG.PLUGIN_ID,
        studio_id = CONFIG.STUDIO_ID
    }
    
    local response = httpRequest(CONFIG.FLASK_URL .. "/plugin/messages", "POST", nil, payload)
    
    if response then
        log("✅ Polling endpoint working")
        if response.messages and #response.messages > 0 then
            log("   Found " .. #response.messages .. " messages")
        else
            log("   No messages in queue")
        end
        pluginState.testResults["polling"] = true
        return true
    else
        log("❌ Polling failed", true)
        pluginState.testResults["polling"] = false
        return false
    end
end

function tests.testProgressUpdate()
    log("Testing progress update...")
    
    local payload = {
        student_id = "test_student",
        activity_type = "quiz",
        activity_id = "test_quiz_1",
        score = 85,
        time_spent = 120,
        completed = true
    }
    
    local response = httpRequest(CONFIG.FLASK_URL .. "/plugin/progress/update", "POST", nil, payload)
    
    if response and response.success then
        log("✅ Progress update working")
        pluginState.testResults["progress_update"] = true
        return true
    else
        log("❌ Progress update failed", true)
        pluginState.testResults["progress_update"] = false
        return false
    end
end

-- Polling coroutine
local pollingConnection = nil
local function startPolling()
    if pluginState.polling then return end
    
    pluginState.polling = true
    log("Starting message polling...")
    
    pollingConnection = RunService.Heartbeat:Connect(function()
        if not pluginState.polling then return end
        
        wait(CONFIG.POLL_INTERVAL)
        
        local payload = {
            plugin_id = CONFIG.PLUGIN_ID,
            studio_id = CONFIG.STUDIO_ID
        }
        
        local response = httpRequest(CONFIG.FLASK_URL .. "/plugin/messages", "POST", nil, payload)
        
        if response and response.messages and #response.messages > 0 then
            for _, message in ipairs(response.messages) do
                log("📨 Message received: " .. tostring(message.type or "unknown"))
                table.insert(pluginState.messageQueue, message)
            end
        end
    end)
end

local function stopPolling()
    if pollingConnection then
        pollingConnection:Disconnect()
        pollingConnection = nil
    end
    pluginState.polling = false
    log("Stopped message polling")
end

-- Main test runner
local function runAllTests()
    testOutput.Text = "=== ToolboxAI Integration Tests ==="
    log("Starting integration tests...")
    
    -- Run tests in sequence
    local allPassed = true
    
    if not tests.checkServices() then
        allPassed = false
    end
    
    wait(0.5)
    
    if not tests.registerPlugin() then
        allPassed = false
    end
    
    wait(0.5)
    
    if pluginState.registered then
        tests.testContentGeneration()
        wait(0.5)
        
        tests.testTerrainGeneration()
        wait(0.5)
        
        tests.testScriptRetrieval()
        wait(0.5)
        
        tests.testPolling()
        wait(0.5)
        
        tests.testProgressUpdate()
        wait(0.5)
        
        -- Start continuous polling
        startPolling()
    end
    
    -- Summary
    log("\n=== Test Summary ===")
    local passed = 0
    local total = 0
    for test, result in pairs(pluginState.testResults) do
        total = total + 1
        if result then
            passed = passed + 1
            log("✅ " .. test)
        else
            log("❌ " .. test)
        end
    end
    
    log(string.format("\nResults: %d/%d tests passed (%.1f%%)", 
        passed, total, (passed/total) * 100))
    
    if passed == total then
        log("\n🎉 All tests passed! Plugin is ready for use.")
    else
        log("\n⚠️ Some tests failed. Check the logs above.", true)
    end
    
    return allPassed
end

-- Button click handler
button.Click:Connect(function()
    testWidget.Enabled = true
    runAllTests()
end)

-- Cleanup on plugin unload
plugin.Unloading:Connect(function()
    stopPolling()
    if testWidget then
        testWidget:Destroy()
    end
end)

-- Initial message
log("ToolboxAI Plugin loaded. Click 'Test Integration' to run tests.")
log("Make sure Flask bridge is running on port " .. CONFIG.FLASK_URL:match(":(%d+)"))

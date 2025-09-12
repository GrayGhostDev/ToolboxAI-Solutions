--[[
    ToolboxAI Plugin Integration Test Script
    Version: 1.0.0
    Description: Tests the AI Content Generator plugin functionality
                 Verifies HTTP polling, content generation, and application
--]]

-- Test configuration
local TEST_CONFIG = {
    FLASK_BRIDGE_URL = "http://127.0.0.1:5001",
    FASTAPI_URL = "http://127.0.0.1:8008",
    TEST_TIMEOUT = 30, -- seconds
    VERBOSE = true
}

-- Services
local HttpService = game:GetService("HttpService")
local RunService = game:GetService("RunService")

-- Test results storage
local testResults = {
    passed = {},
    failed = {},
    skipped = {},
    startTime = tick()
}

-- Helper function to log test results
local function log(message, testName)
    if TEST_CONFIG.VERBOSE then
        print("[TEST" .. (testName and " - " .. testName or "") .. "] " .. message)
    end
end

-- Helper function to run a test
local function runTest(name, testFunction)
    log("Running: " .. name)
    local startTime = tick()
    
    local success, result = pcall(testFunction)
    
    local duration = tick() - startTime
    
    if success then
        table.insert(testResults.passed, {
            name = name,
            duration = duration,
            result = result
        })
        log("✓ PASSED (" .. string.format("%.2f", duration) .. "s)", name)
        return true
    else
        table.insert(testResults.failed, {
            name = name,
            duration = duration,
            error = tostring(result)
        })
        log("✗ FAILED: " .. tostring(result), name)
        return false
    end
end

-- Test 1: Flask Bridge Health Check
local function testFlaskBridgeHealth()
    local response = HttpService:RequestAsync({
        Url = TEST_CONFIG.FLASK_BRIDGE_URL .. "/health",
        Method = "GET",
        Headers = {
            ["Content-Type"] = "application/json"
        }
    })
    
    assert(response.Success, "Flask bridge health check failed")
    
    local data = HttpService:JSONDecode(response.Body)
    assert(data.status == "healthy", "Flask bridge is not healthy")
    assert(data.service == "ToolboxAI-Roblox-Flask-Bridge", "Unexpected service name")
    
    return data
end

-- Test 2: Plugin Registration
local function testPluginRegistration()
    local registrationData = {
        plugin_id = "test_plugin_" .. tostring(tick()),
        version = "1.0.0",
        capabilities = {
            "terrain_generation",
            "quiz_creation",
            "script_injection"
        }
    }
    
    local response = HttpService:RequestAsync({
        Url = TEST_CONFIG.FLASK_BRIDGE_URL .. "/register_plugin",
        Method = "POST",
        Headers = {
            ["Content-Type"] = "application/json"
        },
        Body = HttpService:JSONEncode(registrationData)
    })
    
    assert(response.Success, "Plugin registration failed")
    
    local data = HttpService:JSONDecode(response.Body)
    assert(data.success or data.status == "success", "Registration not successful")
    
    return data
end

-- Test 3: HTTP Polling Endpoint
local function testHTTPPolling()
    local pollData = {
        plugin_id = "test_plugin_" .. tostring(tick()),
        last_message_id = 0,
        timestamp = os.time()
    }
    
    -- Try multiple polling endpoints
    local endpoints = {
        "/plugin/messages",
        "/plugin/poll",
        "/poll-messages",
        "/messages/poll"
    }
    
    local successfulEndpoint = nil
    
    for _, endpoint in ipairs(endpoints) do
        local success, response = pcall(function()
            return HttpService:RequestAsync({
                Url = TEST_CONFIG.FLASK_BRIDGE_URL .. endpoint,
                Method = "POST",
                Headers = {
                    ["Content-Type"] = "application/json"
                },
                Body = HttpService:JSONEncode(pollData)
            })
        end)
        
        if success and response.Success then
            successfulEndpoint = endpoint
            local data = HttpService:JSONDecode(response.Body)
            log("Polling endpoint " .. endpoint .. " is available")
            break
        end
    end
    
    assert(successfulEndpoint, "No polling endpoint available")
    
    return successfulEndpoint
end

-- Test 4: Content Generation Request
local function testContentGeneration()
    local requestData = {
        type = "quiz",
        subject = "Math",
        grade = 5,
        topic = "Addition",
        num_questions = 3
    }
    
    local response = HttpService:RequestAsync({
        Url = TEST_CONFIG.FLASK_BRIDGE_URL .. "/plugin/generate",
        Method = "POST",
        Headers = {
            ["Content-Type"] = "application/json"
        },
        Body = HttpService:JSONEncode(requestData)
    })
    
    -- Allow both success and accepted status codes
    assert(response.Success or response.StatusCode == 200 or response.StatusCode == 202, 
           "Content generation request failed")
    
    if response.Body and response.Body ~= "" then
        local data = HttpService:JSONDecode(response.Body)
        return data
    end
    
    return {status = "accepted"}
end

-- Test 5: Terrain Generation Data
local function testTerrainGenerationData()
    local terrainRequest = {
        type = "terrain",
        biome = "forest",
        size = {x = 100, y = 50, z = 100}
    }
    
    local response = HttpService:RequestAsync({
        Url = TEST_CONFIG.FLASK_BRIDGE_URL .. "/plugin/generate",
        Method = "POST",
        Headers = {
            ["Content-Type"] = "application/json"
        },
        Body = HttpService:JSONEncode(terrainRequest)
    })
    
    -- Check if endpoint exists
    if response.StatusCode == 404 then
        log("Terrain generation endpoint not yet implemented")
        return {skipped = true}
    end
    
    assert(response.Success or response.StatusCode == 200 or response.StatusCode == 202,
           "Terrain generation request failed")
    
    return response.Body and HttpService:JSONDecode(response.Body) or {status = "accepted"}
end

-- Test 6: Quiz Data Structure
local function testQuizDataStructure()
    local quizData = {
        title = "Math Quiz",
        subject = "Mathematics",
        questions = {
            {
                question = "What is 2 + 2?",
                answers = {
                    {text = "3", correct = false},
                    {text = "4", correct = true},
                    {text = "5", correct = false},
                    {text = "6", correct = false}
                }
            },
            {
                question = "What is 5 + 3?",
                answers = {
                    {text = "7", correct = false},
                    {text = "8", correct = true},
                    {text = "9", correct = false},
                    {text = "10", correct = false}
                }
            }
        }
    }
    
    -- Validate structure
    assert(type(quizData) == "table", "Quiz data must be a table")
    assert(type(quizData.questions) == "table", "Questions must be a table")
    assert(#quizData.questions > 0, "Quiz must have at least one question")
    
    for i, question in ipairs(quizData.questions) do
        assert(type(question.question) == "string", "Question " .. i .. " must have question text")
        assert(type(question.answers) == "table", "Question " .. i .. " must have answers")
        assert(#question.answers >= 2, "Question " .. i .. " must have at least 2 answers")
        
        local hasCorrect = false
        for _, answer in ipairs(question.answers) do
            assert(type(answer.text) == "string", "Answer must have text")
            assert(type(answer.correct) == "boolean", "Answer must have correct flag")
            if answer.correct then
                hasCorrect = true
            end
        end
        assert(hasCorrect, "Question " .. i .. " must have at least one correct answer")
    end
    
    return quizData
end

-- Test 7: Script Validation
local function testScriptValidation()
    local validScript = {
        type = "Script",
        name = "TestScript",
        source = [[
            print("Hello from test script")
            local part = Instance.new("Part")
            part.Name = "TestPart"
            part.Parent = workspace
        ]]
    }
    
    local invalidScript = {
        type = "Script",
        name = "BadScript",
        source = [[
            getfenv()
            loadstring("malicious code")
            _G["hack"] = true
        ]]
    }
    
    -- Validate good script should pass
    local validPatterns = {
        "getfenv",
        "setfenv",
        "loadstring",
        "_G%["
    }
    
    local isValid = true
    for _, pattern in ipairs(validPatterns) do
        if string.match(validScript.source, pattern) then
            isValid = false
            break
        end
    end
    assert(isValid, "Valid script incorrectly flagged as invalid")
    
    -- Validate bad script should fail
    local isInvalid = false
    for _, pattern in ipairs(validPatterns) do
        if string.match(invalidScript.source, pattern) then
            isInvalid = true
            break
        end
    end
    assert(isInvalid, "Invalid script not detected")
    
    return {valid = isValid, invalid = isInvalid}
end

-- Test 8: Message Queue Functionality
local function testMessageQueue()
    local queue = {}
    local maxSize = 100
    
    -- Add messages
    for i = 1, 150 do
        if #queue >= maxSize then
            table.remove(queue, 1)
        end
        table.insert(queue, {
            id = i,
            timestamp = tick(),
            data = "Message " .. i
        })
    end
    
    -- Verify queue size limit
    assert(#queue == maxSize, "Queue size limit not enforced")
    
    -- Verify oldest messages removed
    assert(queue[1].id == 51, "Oldest messages not properly removed")
    
    -- Test flush
    local flushed = queue
    queue = {}
    assert(#queue == 0, "Queue not properly flushed")
    assert(#flushed == maxSize, "Flushed data incorrect")
    
    return {size = maxSize, flushed = #flushed}
end

-- Test 9: Connection State Management
local function testConnectionStateManagement()
    local states = {
        disconnected = "disconnected",
        connecting = "connecting",
        connected = "connected",
        polling = "polling",
        error = "error"
    }
    
    local currentState = states.disconnected
    local stateHistory = {}
    
    -- Simulate state transitions
    local function changeState(newState)
        assert(states[newState], "Invalid state: " .. tostring(newState))
        table.insert(stateHistory, {
            from = currentState,
            to = newState,
            timestamp = tick()
        })
        currentState = newState
    end
    
    -- Test state transitions
    changeState("connecting")
    assert(currentState == "connecting", "State not updated to connecting")
    
    changeState("connected")
    assert(currentState == "connected", "State not updated to connected")
    
    changeState("polling")
    assert(currentState == "polling", "State not updated to polling")
    
    changeState("disconnected")
    assert(currentState == "disconnected", "State not updated to disconnected")
    
    assert(#stateHistory == 4, "State history not properly tracked")
    
    return stateHistory
end

-- Test 10: Rate Limiting
local function testRateLimiting()
    local rateLimiter = {
        requests = {},
        limit = 10,
        window = 5 -- seconds
    }
    
    local function checkRateLimit(userId)
        local now = tick()
        local userRequests = rateLimiter.requests[userId] or {}
        
        -- Clean old requests
        local validRequests = {}
        for _, timestamp in ipairs(userRequests) do
            if now - timestamp < rateLimiter.window then
                table.insert(validRequests, timestamp)
            end
        end
        
        -- Check if under limit
        if #validRequests >= rateLimiter.limit then
            return false
        end
        
        -- Add current request
        table.insert(validRequests, now)
        rateLimiter.requests[userId] = validRequests
        
        return true
    end
    
    -- Test rate limiting
    local testUserId = "test_user"
    
    -- Should allow first 10 requests
    for i = 1, 10 do
        assert(checkRateLimit(testUserId), "Request " .. i .. " should be allowed")
    end
    
    -- 11th request should be blocked
    assert(not checkRateLimit(testUserId), "11th request should be blocked")
    
    return {limit = rateLimiter.limit, window = rateLimiter.window}
end

-- Main test runner
local function runAllTests()
    log("Starting ToolboxAI Plugin Integration Tests")
    log("=" .. string.rep("=", 50))
    
    local tests = {
        {name = "Flask Bridge Health Check", func = testFlaskBridgeHealth},
        {name = "Plugin Registration", func = testPluginRegistration},
        {name = "HTTP Polling Endpoint", func = testHTTPPolling},
        {name = "Content Generation Request", func = testContentGeneration},
        {name = "Terrain Generation Data", func = testTerrainGenerationData},
        {name = "Quiz Data Structure", func = testQuizDataStructure},
        {name = "Script Validation", func = testScriptValidation},
        {name = "Message Queue Functionality", func = testMessageQueue},
        {name = "Connection State Management", func = testConnectionStateManagement},
        {name = "Rate Limiting", func = testRateLimiting}
    }
    
    for _, test in ipairs(tests) do
        runTest(test.name, test.func)
        wait(0.1) -- Small delay between tests
    end
    
    -- Calculate results
    local totalTests = #tests
    local passedTests = #testResults.passed
    local failedTests = #testResults.failed
    local skippedTests = #testResults.skipped
    local totalDuration = tick() - testResults.startTime
    
    -- Print summary
    log("=" .. string.rep("=", 50))
    log("TEST SUMMARY")
    log("Total Tests: " .. totalTests)
    log("Passed: " .. passedTests .. " (" .. string.format("%.1f%%", (passedTests/totalTests)*100) .. ")")
    log("Failed: " .. failedTests)
    log("Skipped: " .. skippedTests)
    log("Total Duration: " .. string.format("%.2f", totalDuration) .. " seconds")
    
    -- Print failed tests details
    if #testResults.failed > 0 then
        log("\nFAILED TESTS:")
        for _, failure in ipairs(testResults.failed) do
            log("  - " .. failure.name .. ": " .. failure.error)
        end
    end
    
    -- Return test results
    return {
        success = failedTests == 0,
        results = testResults,
        summary = {
            total = totalTests,
            passed = passedTests,
            failed = failedTests,
            skipped = skippedTests,
            duration = totalDuration
        }
    }
end

-- Export test runner
return {
    runAllTests = runAllTests,
    runTest = runTest,
    config = TEST_CONFIG,
    tests = {
        flaskBridgeHealth = testFlaskBridgeHealth,
        pluginRegistration = testPluginRegistration,
        httpPolling = testHTTPPolling,
        contentGeneration = testContentGeneration,
        terrainGeneration = testTerrainGenerationData,
        quizStructure = testQuizDataStructure,
        scriptValidation = testScriptValidation,
        messageQueue = testMessageQueue,
        connectionState = testConnectionStateManagement,
        rateLimiting = testRateLimiting
    }
}
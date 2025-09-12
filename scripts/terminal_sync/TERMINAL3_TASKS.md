# Terminal 3: Roblox Integration Task List

## 🎯 PRIMARY OBJECTIVE
Complete Roblox Studio plugin with HTTP polling fallback, implement content injection, and test end-to-end integration.

## 🌳 BRANCH
```bash
git checkout -b feature/roblox-plugin
```

## 📋 DETAILED TASK LIST

### Phase 1: Plugin HTTP Polling (Day 1-2)

#### 1.1 Implement HTTP Polling Fallback [CRITICAL]
**Location**: `ToolboxAI-Roblox-Environment/Roblox/Plugins/AIContentGenerator.lua`
**Tools**: Task(roblox-lua-validator), MultiEdit

```lua
-- Add HTTP polling when WebSocket unavailable
local function startHTTPPolling()
    while plugin.Enabled do
        local success, response = pcall(function()
            return HttpService:GetAsync(API_URL .. "/plugin/poll")
        end)
        if success then
            processUpdate(response)
        end
        wait(2) -- Poll every 2 seconds
    end
end

-- Fallback logic
local function establishConnection()
    if HttpService.CreateWebStreamClient then
        return connectWebSocket()
    else
        warn("WebSocket not available, using HTTP polling")
        return startHTTPPolling()
    end
end
```

#### 1.2 Message Queue Implementation
**Tools**: Task(coder), MultiEdit

```lua
-- Queue messages when offline
local messageQueue = {}

local function queueMessage(message)
    table.insert(messageQueue, {
        timestamp = tick(),
        data = message
    })
end

local function processQueue()
    for _, msg in ipairs(messageQueue) do
        sendToServer(msg.data)
    end
    messageQueue = {}
end
```

### Phase 2: Content Application System (Day 3-4)

#### 2.1 Terrain Generation
**Location**: `Roblox/Scripts/ModuleScripts/TerrainGenerator.lua`
**Tools**: Write, Task(roblox-lua-validator)

```lua
local TerrainGenerator = {}

function TerrainGenerator.generate(terrainData)
    local terrain = workspace.Terrain
    
    -- Clear existing terrain
    terrain:Clear()
    
    -- Generate based on data
    for _, region in ipairs(terrainData.regions) do
        terrain:FillBall(
            region.position,
            region.size,
            Enum.Material[region.material]
        )
    end
end

return TerrainGenerator
```

#### 2.2 Quiz UI Creation
**Location**: `Roblox/Scripts/ModuleScripts/QuizUI.lua`
**Tools**: Write, Task(coder)

```lua
local QuizUI = {}

function QuizUI.create(quizData)
    local gui = Instance.new("ScreenGui")
    gui.Name = "QuizInterface"
    
    -- Create question frame
    local frame = Instance.new("Frame")
    frame.Size = UDim2.new(0.6, 0, 0.7, 0)
    frame.Position = UDim2.new(0.2, 0, 0.15, 0)
    frame.Parent = gui
    
    -- Add question text
    local question = Instance.new("TextLabel")
    question.Text = quizData.question
    question.Parent = frame
    
    -- Create answer buttons
    for i, answer in ipairs(quizData.answers) do
        local button = Instance.new("TextButton")
        button.Text = answer.text
        button.Position = UDim2.new(0, 0, 0.3 + (i * 0.1), 0)
        button.Parent = frame
    end
    
    return gui
end

return QuizUI
```

#### 2.3 Script Injection System
**Tools**: Task(roblox-lua-validator), MultiEdit

```lua
-- Safe script injection
local function injectScript(scriptData)
    local script = Instance.new(scriptData.type)
    script.Name = scriptData.name
    script.Source = scriptData.source
    script.Parent = scriptData.parent or workspace
    script.Disabled = false
end
```

### Phase 3: Plugin Security (Day 5)

#### 3.1 Input Validation
**Tools**: Task(security), MultiEdit

```lua
local Validator = {}

function Validator.sanitizeInput(input)
    -- Remove malicious patterns
    local sanitized = input:gsub("[<>\"']", "")
    return sanitized
end

function Validator.validateToken(token)
    -- JWT validation
    local parts = token:split(".")
    return #parts == 3
end
```

#### 3.2 Rate Limiting
```lua
local RateLimiter = {}
local requests = {}

function RateLimiter.check(userId)
    local now = tick()
    requests[userId] = requests[userId] or {}
    
    -- Remove old requests
    local valid = {}
    for _, time in ipairs(requests[userId]) do
        if now - time < 60 then
            table.insert(valid, time)
        end
    end
    
    requests[userId] = valid
    
    -- Check limit (100 per minute)
    if #requests[userId] >= 100 then
        return false
    end
    
    table.insert(requests[userId], now)
    return true
end
```

### Phase 4: Integration Testing (Day 6)

#### 4.1 Plugin Installation Test
**Tools**: Bash, Task(tester)

1. Build plugin file
2. Install in Roblox Studio
3. Verify toolbar button appears
4. Test authentication flow

#### 4.2 Content Generation Test
```lua
-- Test script
local testContent = {
    subject = "Science",
    grade = 7,
    topic = "Solar System"
}

-- Send to server
plugin:GenerateContent(testContent)

-- Verify response
assert(response.success, "Content generation failed")
```

## 🛠️ REQUIRED AGENTS & TOOLS

### Primary Agents:
- **roblox-lua-validator**: Validate Lua scripts
- **coder**: Write Lua code
- **tester**: Test plugin functionality
- **security**: Security validation

### Primary Tools:
- **Write**: Create Lua modules
- **MultiEdit**: Update multiple scripts
- **Task**: Complex Roblox operations
- **Grep**: Search Lua codebase

## 📊 SUCCESS METRICS

- [ ] HTTP polling working
- [ ] Message queue functional
- [ ] Terrain generation complete
- [ ] Quiz UI creation working
- [ ] Script injection safe
- [ ] Plugin secure

## 🔄 COMMUNICATION PROTOCOL

### Status Updates:
```bash
./scripts/terminal_sync/sync.sh terminal3 status "Testing plugin in Studio"
```

### Need Backend Fix:
```bash
./scripts/terminal_sync/sync.sh terminal3 message "Flask endpoint /plugin/poll returning 404" terminal1
```

### Ready for Testing:
```bash
./scripts/terminal_sync/sync.sh terminal3 message "Plugin ready for integration test" debugger
```

## 🚨 CRITICAL DEPENDENCIES

### Depends on Terminal 1:
- Flask bridge endpoints working
- Content generation API stable
- Authentication system

### Depends on Terminal 2:
- Dashboard for monitoring
- WebSocket connection reference

## 📝 ROBLOX COMMANDS

### Plugin Development:
```bash
# Build plugin
rojo build -o AIContentGenerator.rbxm

# Start sync server
rojo serve

# Watch for changes
rojo build --watch
```

### Testing in Studio:
1. Open Roblox Studio
2. Plugins → Manage Plugins
3. Install AIContentGenerator.rbxm
4. Test toolbar button
5. Generate content

## 🎮 ROBLOX API REFERENCE

### Key Services:
- `HttpService`: HTTP requests
- `DataStoreService`: Data persistence
- `RunService`: Game loop
- `TweenService`: Animations
- `UserInputService`: Input handling

### Content Types:
- ServerScript: Server-side logic
- LocalScript: Client-side logic
- ModuleScript: Shared modules
- ScreenGui: UI elements

## 📝 NOTES

- HTTP polling is critical due to WebSocket limitations
- Test on multiple Studio versions
- Coordinate with Terminal 1 for API
- Security is paramount - validate everything
- Update TODO.md after milestones
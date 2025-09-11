# Roblox Studio Plugin Installation & Usage Guide

## Prerequisites

- Roblox Studio installed and updated to latest version
- Terminal 1: FastAPI server running on port 8008
- Terminal 3: Flask bridge running on port 5001
- Terminal 2: Dashboard running (optional, for monitoring)
- External drive mounted at `/Volumes/G-DRIVE ArmorATD`

## Installation Steps

### 1. Enable Studio API Services

1. Open Roblox Studio
2. Go to **File → Studio Settings**
3. Navigate to **Security** tab
4. Enable **"Allow HTTP Requests"** ✅
5. Add to Allowed URLs (if applicable):
   - `http://127.0.0.1:5001`
   - `http://127.0.0.1:8008`
   - `http://localhost:5001`
   - `http://localhost:8008`

### 2. Install the Plugin

#### Method A: Direct Installation (Recommended)

1. In Studio, open the **Command Bar** (View → Command Bar)
2. Navigate to the plugin directory:

```lua
-- First, verify the plugin file exists
print(game:GetService("HttpService"):GetAsync("http://127.0.0.1:5001/plugin/verify"))
```

3. Load the plugin:

```lua
-- Load and install the ToolBoxAI plugin
local HttpService = game:GetService("HttpService")
local Plugin = plugin:CreateToolbar("ToolBoxAI Education")
local Button = Plugin:CreateButton(
    "AI Content Generator",
    "Generate educational content with AI",
    "rbxasset://textures/ui/Settings/Help/AvatarCreator.png"
)

-- Load plugin modules
local TerrainGenerator = require(script.Parent.TerrainGenerator)
local QuizUI = require(script.Parent.QuizUI)
local ObjectPlacer = require(script.Parent.ObjectPlacer)

-- Initialize connection
local bridge = {
    url = "http://127.0.0.1:5001",
    sessionId = nil
}

-- Register plugin
local function registerPlugin()
    local response = HttpService:RequestAsync({
        Url = bridge.url .. "/register_plugin",
        Method = "POST",
        Headers = {["Content-Type"] = "application/json"},
        Body = HttpService:JSONEncode({
            studio_id = "toolboxai_" .. game.PlaceId,
            port = 64989,
            version = "1.0.0"
        })
    })

    if response.StatusCode == 200 then
        local data = HttpService:JSONDecode(response.Body)
        bridge.sessionId = data.plugin_id
        print("✅ ToolBoxAI Plugin registered:", bridge.sessionId)
        return true
    end
    return false
end

-- Main UI handler
Button.Click:Connect(function()
    if not bridge.sessionId then
        registerPlugin()
    end
    -- Show content generation UI
    print("Opening ToolBoxAI Content Generator...")
end)

print("✅ ToolBoxAI Plugin installed successfully!")
```

#### Method B: Manual File Installation

1. Navigate to plugin files:

```bash
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions/ToolboxAI-Roblox-Environment/Roblox/Plugins
```

2. Copy the plugin file to Roblox Studio plugins folder:
   - **Windows**: `%LOCALAPPDATA%\Roblox\Plugins\`
   - **macOS**: `~/Documents/Roblox/Plugins/`
   - **Linux**: `~/.local/share/Roblox/Plugins/`

3. Copy these files:
   - `AIContentGenerator.lua` (main plugin)
   - `WebSocketFallback.lua` (HTTP polling support)

4. Restart Roblox Studio

## Usage Guide

### Generating Educational Content

1. **Open Plugin Interface**
   - Click the **ToolBoxAI** button in the plugins toolbar
   - The content generation panel will appear

2. **Configure Educational Content**

   ```
   Subject: [Dropdown Menu]
   ├── Science
   ├── Mathematics
   ├── Language Arts
   ├── History
   ├── Geography
   └── Computer Science

   Grade Level: [1-12 Slider]

   Topic: [Text Input]
   Example: "Solar System", "Pythagorean Theorem", "World War II"

   Learning Objectives: [Multi-line Text]
   - Objective 1
   - Objective 2
   - Objective 3
   ```

3. **Select Environment Type**

   ```
   Environment Presets:
   ├── 🌊 Ocean - Marine biology, water cycle
   ├── 🏔️ Mountain - Geology, ecosystems
   ├── 🌲 Forest - Ecology, photosynthesis
   ├── 🏜️ Desert - Climate, adaptation
   ├── ❄️ Arctic - Weather, polar regions
   ├── 🏙️ City - Urban studies, society
   └── 🚀 Space Station - Astronomy, physics
   ```

4. **Generation Options**
   - ☑️ **Include Quiz** - Adds interactive assessments
   - ☑️ **Add Terrain** - Generates themed terrain
   - ☑️ **Place Objects** - Adds educational props
   - ☑️ **Create NPCs** - Adds interactive characters
   - ☑️ **Use Real Data** - Connects to educational database

5. **Generate Content**
   - Click **"Generate Content"** button
   - Progress bar shows generation status
   - Content appears in workspace automatically

### Working with Generated Content

#### Terrain Features

- Automatically generated based on selected environment
- Includes appropriate materials and textures
- Water bodies with proper physics
- Educational landmarks for reference points
- Vegetation for realistic environments

#### Educational Objects

Interactive objects include:

- **Science Equipment**: Microscopes, telescopes, beakers
- **Math Tools**: Calculators, geometric shapes, graph boards
- **Language Resources**: Books, writing boards, dictionaries
- **Geography Tools**: Globes, maps, compasses
- **History Artifacts**: Timeline displays, artifacts, monuments

Click on objects to:

- View descriptions
- Trigger animations
- Access additional information
- Start mini-lessons

#### Quiz System

Generated quizzes support:

- Multiple choice questions
- True/False assessments
- Fill-in-the-blank exercises
- Matching activities
- Timed challenges
- Instant feedback
- Progress tracking
- Score reporting

### Customization Options

#### Modifying Generated Content

1. Select objects in Explorer window
2. Adjust properties in Properties panel
3. Use Studio tools for fine-tuning:
   - Move tool for positioning
   - Scale tool for sizing
   - Rotate tool for orientation

#### Saving Templates

1. Select customized content
2. Right-click → **Save as Model**
3. Name your template
4. Reuse in future projects

#### Script Customization

Access module scripts:

```
workspace
└── ToolBoxAI_Generated
    ├── TerrainGenerator
    ├── QuizUI
    ├── ObjectPlacer
    └── ContentManager
```

## Advanced Features

### Real-Time Collaboration

- Multiple educators can work simultaneously
- Changes sync across all connected Studios
- Chat integration for communication
- Version control for content iterations

### Content Library Access

Connect to pre-made content:

```lua
-- Access content library
local library = require(script.ContentLibrary)
local lessons = library:GetLessons("Science", 7)

-- Load specific lesson
library:LoadLesson("solar_system_exploration")
```

### AI-Powered Assistance

Get help while building:

- Content suggestions based on curriculum
- Automatic difficulty adjustment
- Learning objective alignment
- Assessment generation

### Performance Optimization

- Automatic LOD (Level of Detail) for large worlds
- Streaming enabled for better performance
- Optimized scripts for smooth gameplay
- Memory management for mobile devices

## Troubleshooting

### Plugin Not Appearing

```lua
-- Check if plugin is loaded
print(plugin:GetStudioUserId())

-- Verify HTTP service
print(game:GetService("HttpService").HttpEnabled)

-- Test connection to Flask bridge
local success, result = pcall(function()
    return game:GetService("HttpService"):GetAsync("http://127.0.0.1:5001/health")
end)
print("Flask bridge status:", success and "Connected" or "Not connected")
```

### Generation Fails

1. Check service status:

```bash
# Terminal 1 - Check FastAPI
curl http://127.0.0.1:8008/health

# Terminal 3 - Check Flask bridge
curl http://127.0.0.1:5001/health
```

2. Verify authentication:

```lua
-- Re-register plugin if needed
local HttpService = game:GetService("HttpService")
HttpService:RequestAsync({
    Url = "http://127.0.0.1:5001/register_plugin",
    Method = "POST",
    Headers = {["Content-Type"] = "application/json"},
    Body = HttpService:JSONEncode({
        studio_id = "reset_" .. os.time(),
        port = 64989
    })
})
```

### Content Not Appearing

- Check Output window for errors (View → Output)
- Verify workspace isn't locked
- Ensure StreamingEnabled is configured properly
- Check if content is being placed outside camera view

### Performance Issues

- Reduce terrain size in generation options
- Limit number of objects to < 100
- Disable real-time shadows for testing
- Use lower resolution textures

## Best Practices

### Educational Design

1. **Start Simple**: Test with basic content first
2. **Age Appropriate**: Match complexity to grade level
3. **Interactive Elements**: Maximize engagement
4. **Clear Objectives**: Define learning goals upfront
5. **Assessment Integration**: Include checkpoints

### Technical Guidelines

1. **Save Frequently**: Use Studio's autosave
2. **Test Regularly**: Use Play mode to test interactions
3. **Optimize Early**: Monitor performance metrics
4. **Version Control**: Commit to git regularly
5. **Document Changes**: Keep notes on customizations

### Classroom Integration

1. **Pilot Test**: Try with small group first
2. **Gather Feedback**: Use built-in analytics
3. **Iterate Content**: Refine based on usage
4. **Share Success**: Export and share templates
5. **Collaborate**: Work with other educators

## Integration with LMS

### Supported Platforms

- Canvas
- Schoology
- Google Classroom
- Moodle
- Blackboard

### Grade Syncing

```lua
-- Sync quiz scores to LMS
local LMSConnector = require(script.LMSConnector)
LMSConnector:Initialize({
    platform = "Canvas",
    api_key = "your_api_key",
    course_id = "12345"
})

-- Auto-sync grades
LMSConnector:EnableAutoSync(true)
```

## Support & Resources

### Getting Help

- **Documentation**: `/Documentation/` folder
- **API Reference**: `http://127.0.0.1:8008/docs`
- **Flask Bridge API**: `http://127.0.0.1:5001/docs`
- **Community Forum**: (Coming soon)
- **Video Tutorials**: (In development)

### Reporting Issues

1. Check the Output console in Studio
2. Review Flask bridge logs:

```bash
tail -f logs/flask_bridge.log
```

3. Check FastAPI logs:

```bash
tail -f logs/fastapi.log
```

### Feature Requests

Submit requests via:

- GitHub Issues
- In-app feedback button
- Email: support@toolboxai.edu

## Examples

### Science Lesson: Solar System

```lua
{
    subject = "Science",
    grade_level = 7,
    topic = "Solar System",
    environment_type = "space_station",
    include_quiz = true,
    add_terrain = true,
    place_objects = true,
    objects = {"telescope", "planet_models", "orbit_simulator"}
}
```

### Math Lesson: Geometry

```lua
{
    subject = "Mathematics",
    grade_level = 5,
    topic = "3D Shapes",
    environment_type = "city",
    include_quiz = true,
    place_objects = true,
    objects = {"geometric_shapes", "calculator", "graph_board"}
}
```

### History Lesson: Ancient Civilizations

```lua
{
    subject = "History",
    grade_level = 6,
    topic = "Ancient Egypt",
    environment_type = "desert",
    include_quiz = true,
    add_terrain = true,
    place_objects = true,
    objects = {"pyramid", "artifacts", "timeline"}
}
```

## Security & Privacy

### Data Protection

- All student data encrypted in transit
- No personal information stored locally
- COPPA/FERPA compliant
- Optional offline mode available

### Content Moderation

- AI-filtered content generation
- Age-appropriate material only
- Teacher review before publishing
- Safe chat features

## Updates & Maintenance

### Auto-Update Check

The plugin checks for updates on startup:

```lua
-- Disable auto-update if needed
_G.ToolBoxAI_AutoUpdate = false
```

### Manual Update

```bash
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions
git pull origin main
# Restart Studio to load updates
```

## Conclusion

The ToolBoxAI Roblox Plugin bridges education and gaming, making learning interactive and engaging. With real educational data integration, comprehensive assessment tools, and AI-powered content generation, educators can create immersive learning experiences in minutes.

Remember: **The plugin is a tool to enhance education, not replace teaching!**

---

_Version 1.0.0 | Last Updated: 2025-09-10_
_ToolBoxAI Educational Platform - Empowering Educators with Game-Based Learning_

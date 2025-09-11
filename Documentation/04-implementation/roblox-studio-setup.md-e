# Roblox Studio Plugin Setup Guide

## Overview

This guide provides comprehensive instructions for setting up and configuring the ToolboxAI Roblox Studio Plugin, which enables seamless integration between Roblox Studio and the ToolboxAI educational platform.

## Prerequisites

### System Requirements
- **Roblox Studio**: Latest version (2024.1 or higher)
- **Operating System**: Windows 10/11, macOS 10.15+
- **Network**: Stable internet connection for API communication
- **Permissions**: HTTP requests must be enabled in Studio

### Backend Requirements
- ToolboxAI Backend running (FastAPI on port 8008)
- Flask Bridge Server running (port 5001)
- MCP WebSocket Server running (port 9876)
- PostgreSQL database configured
- Redis server (optional, for caching)

## Installation Steps

### 1. Enable HTTP Requests in Roblox Studio

1. Open Roblox Studio
2. Go to **File → Studio Settings**
3. Navigate to **Security** tab
4. Enable **"Allow HTTP Requests"**
5. Click **OK** to save

### 2. Install the ToolboxAI Plugin

#### Method A: Manual Installation

1. Locate the plugin file:
   ```
   ToolboxAI-Roblox-Environment/Roblox/Plugins/AIContentGenerator.lua
   ```

2. In Roblox Studio:
   - Open the **Plugins** folder in Explorer
   - Right-click → **Insert from File**
   - Select `AIContentGenerator.lua`
   - The plugin will appear in the Plugins tab

#### Method B: Plugin Marketplace (When Published)

1. Open Roblox Studio
2. Navigate to **Plugins** tab
3. Click **Manage Plugins**
4. Search for "ToolboxAI Content Generator"
5. Click **Install**

### 3. Configure Plugin Settings

1. Click the **ToolboxAI** button in the Plugins toolbar
2. In the plugin window, click **Settings** (gear icon)
3. Configure the following:

```lua
-- Configuration Settings
API_URL = "http://127.0.0.1:8008"      -- FastAPI server
BACKEND_URL = "http://127.0.0.1:5001"  -- Flask bridge
WEBSOCKET_URL = "ws://127.0.0.1:9876"  -- MCP WebSocket
DASHBOARD_URL = "http://127.0.0.1:3000" -- Dashboard
PLUGIN_PORT = 64989                     -- Plugin communication port
```

### 4. Authenticate the Plugin

1. In the plugin window, click **Login**
2. Enter your credentials:
   - **Username**: Your teacher/admin username
   - **Password**: Your account password
   - **Organization ID**: (Optional) Your school/organization ID

3. Click **Authenticate**
4. You should see "Authentication successful" message

Alternative: API Key Authentication

1. Generate an API key from the Dashboard
2. In plugin settings, enter:
   ```lua
   API_KEY = "your-api-key-here"
   ```

## Plugin Features Configuration

### Content Generation

1. **Enable AI Content Generation**:
   ```lua
   ENABLE_AI_GENERATION = true
   AI_MODEL = "gpt-3.5-turbo"  -- or "gpt-4" for better quality
   MAX_TOKENS = 2000
   ```

2. **Configure Educational Levels**:
   ```lua
   GRADE_LEVELS = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12}
   SUBJECTS = {"Math", "Science", "History", "English", "Art"}
   ```

### Terrain Generation

1. **Terrain Templates**:
   ```lua
   TERRAIN_TYPES = {
       classroom = {size = Vector3.new(50, 20, 50)},
       laboratory = {size = Vector3.new(60, 25, 60)},
       outdoor = {size = Vector3.new(200, 50, 200)},
       space = {size = Vector3.new(500, 100, 500)}
   }
   ```

2. **Material Settings**:
   ```lua
   DEFAULT_MATERIALS = {
       Enum.Material.Grass,
       Enum.Material.Rock,
       Enum.Material.Sand,
       Enum.Material.Water
   }
   ```

### Quiz System

1. **Quiz Configuration**:
   ```lua
   QUIZ_SETTINGS = {
       max_questions = 20,
       time_limit = 600, -- seconds
       allow_hints = true,
       randomize_questions = true
   }
   ```

2. **Question Types**:
   ```lua
   QUESTION_TYPES = {
       "multiple_choice",
       "true_false",
       "fill_blank",
       "matching"
   }
   ```

## Database Integration

### 1. Connect to Database

The plugin automatically connects to the database through the backend API. Ensure the backend has proper database configuration:

```python
# Backend .env file
DATABASE_URL=postgresql://user:password@localhost/toolboxai
REDIS_URL=redis://localhost:6379
```

### 2. Enable Content Persistence

```lua
-- In plugin settings
PERSIST_CONTENT = true
AUTO_SAVE_INTERVAL = 300  -- seconds
CACHE_DURATION = 3600      -- seconds
```

## Dashboard Integration

### 1. Real-time Sync

Enable real-time synchronization with the teacher dashboard:

```lua
ENABLE_DASHBOARD_SYNC = true
SYNC_INTERVAL = 30  -- seconds
```

### 2. WebSocket Connection

The plugin maintains a WebSocket connection for real-time updates:

```lua
WEBSOCKET_SETTINGS = {
    auto_reconnect = true,
    reconnect_delay = 5,
    heartbeat_interval = 30
}
```

### 3. Session Management

Configure classroom session settings:

```lua
SESSION_SETTINGS = {
    max_students = 30,
    session_timeout = 3600,
    allow_late_join = true,
    track_progress = true
}
```

## Agent Pipeline Configuration

### 1. Enable Agent Integration

```lua
AGENT_SETTINGS = {
    enable_supervisor = true,
    enable_content_agent = true,
    enable_quiz_agent = true,
    enable_terrain_agent = true,
    enable_script_agent = true,
    enable_review_agent = true
}
```

### 2. Agent Priorities

Configure agent execution priorities:

```lua
AGENT_PRIORITIES = {
    content = "high",
    terrain = "medium",
    quiz = "medium",
    script = "low",
    review = "low"
}
```

## CI/CD Integration

### 1. GitHub Actions Setup

Configure the plugin to work with CI/CD pipelines:

```lua
CICD_SETTINGS = {
    enable_auto_deploy = false,  -- Set to true for production
    github_webhook = "https://api.github.com/repos/your-repo/dispatches",
    branch = "main"
}
```

### 2. Automated Testing

Enable automated testing on content generation:

```lua
AUTO_TEST_SETTINGS = {
    enable_tests = true,
    test_on_generate = true,
    validation_level = "strict"
}
```

## Security Configuration

### 1. Token Management

```lua
SECURITY_SETTINGS = {
    token_expiry = 3600,
    refresh_token_expiry = 86400,
    auto_refresh = true,
    secure_storage = true
}
```

### 2. Permissions

Configure plugin permissions:

```lua
PERMISSIONS = {
    content_generation = true,
    database_access = true,
    student_data_access = false,  -- Requires admin
    settings_modification = false  -- Requires admin
}
```

## Testing the Setup

### 1. Connection Test

1. Click **Test Connection** in the plugin
2. Verify all services are reachable:
   - ✅ FastAPI Server
   - ✅ Flask Bridge
   - ✅ Database
   - ✅ Dashboard
   - ✅ WebSocket

### 2. Content Generation Test

1. Click **Generate Content**
2. Select:
   - Subject: Science
   - Grade Level: 7
   - Environment: Laboratory
3. Click **Generate**
4. Verify content appears in Studio

### 3. Database Test

1. Click **Database** → **Query**
2. Select **Get Lessons**
3. Verify lesson list appears

### 4. Dashboard Sync Test

1. Open Dashboard in browser
2. Create a new lesson
3. In Studio plugin, click **Sync**
4. Verify lesson appears in plugin

## Troubleshooting

### Common Issues

#### 1. Authentication Failed
```
Error: Authentication failed
```
**Solution**:
- Verify credentials are correct
- Check backend server is running
- Ensure network connectivity

#### 2. HTTP Requests Blocked
```
Error: HttpService is not allowed to access ROBLOX resources
```
**Solution**:
- Enable HTTP requests in Studio Settings
- Restart Roblox Studio

#### 3. Connection Timeout
```
Error: Connection to server timed out
```
**Solution**:
- Check firewall settings
- Verify server URLs are correct
- Ensure all backend services are running

#### 4. WebSocket Connection Failed
```
Error: WebSocket connection failed
```
**Solution**:
- Check MCP server is running on port 9876
- Verify WebSocket URL format (ws:// not http://)
- Check for proxy/firewall blocking WebSocket

### Debug Mode

Enable debug mode for detailed logging:

```lua
DEBUG_SETTINGS = {
    enable_debug = true,
    log_level = "verbose",
    log_to_file = true,
    log_file_path = "ToolboxAI_debug.log"
}
```

### Log Locations

- **Plugin Logs**: `%LocalAppData%\Roblox\logs\`
- **Server Logs**: Check backend console output
- **Database Logs**: PostgreSQL log directory

## Performance Optimization

### 1. Caching

Enable local caching to reduce API calls:

```lua
CACHE_SETTINGS = {
    enable_cache = true,
    cache_size_mb = 100,
    cache_ttl = 3600,
    cache_lessons = true,
    cache_quizzes = true
}
```

### 2. Batch Operations

Configure batch processing:

```lua
BATCH_SETTINGS = {
    enable_batching = true,
    batch_size = 10,
    batch_delay = 100  -- milliseconds
}
```

### 3. Rate Limiting

Respect API rate limits:

```lua
RATE_LIMIT_SETTINGS = {
    max_requests_per_minute = 60,
    max_concurrent_requests = 5,
    retry_on_limit = true,
    retry_delay = 1000  -- milliseconds
}
```

## Advanced Configuration

### Custom Agent Workflows

Define custom agent workflows:

```lua
CUSTOM_WORKFLOWS = {
    math_lesson = {
        agents = {"content", "quiz", "script"},
        parallel = false,
        timeout = 60
    },
    science_lab = {
        agents = {"content", "terrain", "quiz", "script"},
        parallel = true,
        timeout = 120
    }
}
```

### Plugin Extensions

Enable additional plugin features:

```lua
EXTENSIONS = {
    enable_voice_narration = false,
    enable_multiplayer_sync = true,
    enable_vr_support = false,
    enable_analytics = true
}
```

## Deployment to Production

### 1. Production URLs

Update URLs for production environment:

```lua
-- Production Configuration
API_URL = "https://api.toolboxai.com"
BACKEND_URL = "https://bridge.toolboxai.com"
WEBSOCKET_URL = "wss://ws.toolboxai.com"
DASHBOARD_URL = "https://dashboard.toolboxai.com"
```

### 2. SSL/TLS Configuration

Enable secure connections:

```lua
SSL_SETTINGS = {
    enable_ssl = true,
    verify_certificates = true,
    certificate_path = "certs/toolboxai.crt"
}
```

### 3. Production Permissions

Restrict permissions for production:

```lua
PRODUCTION_PERMISSIONS = {
    debug_mode = false,
    local_storage = false,
    direct_database_access = false
}
```

## Support and Resources

### Documentation
- API Documentation: `/Documentation/03-api/`
- Architecture Guide: `/Documentation/02-architecture/`
- SDK Reference: `/Documentation/11-sdks/`

### Support Channels
- GitHub Issues: [Report bugs and feature requests]
- Discord: [Community support]
- Email: support@toolboxai.com

### Version Information
- Plugin Version: 1.0.0
- Minimum Studio Version: 2024.1
- API Version: v1
- Protocol Version: 1.0

## Best Practices

1. **Regular Updates**: Keep the plugin updated to the latest version
2. **Backup Content**: Regularly backup generated content
3. **Monitor Performance**: Use analytics to track usage
4. **Security**: Rotate API keys periodically
5. **Testing**: Test in a development place before production
6. **Documentation**: Document custom configurations
7. **Training**: Provide training for teachers using the plugin

## Conclusion

The ToolboxAI Roblox Studio Plugin provides powerful educational content generation capabilities directly within Roblox Studio. Proper configuration ensures optimal performance and seamless integration with the broader ToolboxAI platform.

For additional assistance or advanced configurations, consult the technical documentation or contact support.
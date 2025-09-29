# Roblox Integration Endpoints

## Overview

The Roblox Integration API provides seamless connection between the ToolBoxAI platform and Roblox Studio/experiences. This includes content deployment, environment synchronization, plugin management, and real-time collaboration features.

## Base URL
```
http://127.0.0.1:8008
```

## Content Deployment

### POST /api/v1/roblox/deploy/{content_id}
Deploy generated educational content to Roblox.

**Authentication:** Required (Bearer token)

**Parameters:**
- `content_id` (path): Unique identifier of generated content

**Request Body:**
```json
{
  "place_id": "123456789",
  "deployment_options": {
    "backup_existing": true,
    "test_mode": false,
    "publish_public": false,
    "enable_collaboration": true
  },
  "target_environment": "development|staging|production",
  "notification_settings": {
    "notify_on_completion": true,
    "notify_on_error": true,
    "email_recipients": ["teacher@school.edu"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "deployment_id": "deploy_abc123",
  "message": "Deployment initiated successfully",
  "estimated_completion": "2024-01-01T12:05:00Z",
  "deployment_status": "in_progress",
  "roblox_details": {
    "place_id": "123456789",
    "universe_id": "987654321",
    "place_url": "https://www.roblox.com/games/123456789/Math-Adventure",
    "studio_url": "roblox-studio:1+launchmode:edit+placeId:123456789"
  },
  "deployment_progress": {
    "current_stage": "uploading_scripts",
    "stages_completed": 2,
    "total_stages": 6,
    "progress_percentage": 33
  }
}
```

**cURL Example:**
```bash
curl -X POST "http://127.0.0.1:8008/api/v1/roblox/deploy/content_12345" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "place_id": "123456789",
    "deployment_options": {
      "backup_existing": true,
      "test_mode": false
    },
    "target_environment": "development"
  }'
```

### GET /api/v1/roblox/download/{content_id}
Download Roblox-compatible files for manual deployment.

**Authentication:** Required (Bearer token)

**Parameters:**
- `content_id` (path): Unique identifier of generated content

**Query Parameters:**
- `format` (optional): "rbxl" (place file), "rbxm" (model), "zip" (all files)
- `include_assets` (optional): Include texture and audio assets

**Response:**
- Content-Type: `application/octet-stream` or `application/zip`
- Content-Disposition: `attachment; filename="math_lesson_content.rbxl"`

**Example:**
```bash
curl -X GET "http://127.0.0.1:8008/api/v1/roblox/download/content_12345?format=rbxl&include_assets=true" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o "lesson_content.rbxl"
```

## Plugin Management

### POST /plugin/register
Register a Roblox Studio plugin for communication.

**Request Body:**
```json
{
  "studio_id": "user_12345",
  "plugin_id": "toolboxai_plugin_v1",
  "port": 64989,
  "version": "1.2.0",
  "capabilities": [
    "content_sync",
    "real_time_collaboration",
    "asset_management"
  ],
  "studio_version": "0.545.0.5450371"
}
```

**Response:**
```json
{
  "success": true,
  "registration_id": "reg_xyz789",
  "auth_token": "plugin_token_abc123",
  "pusher_channel": "private-plugin-reg_xyz789",  // MIGRATED: was websocket_endpoint
  "heartbeat_interval": 30,
  "supported_api_version": "2.1.0"
}
```

### POST /plugin/message
Send message to registered plugin.

**Request Body:**
```json
{
  "type": "command|response|event|heartbeat",
  "plugin_id": "toolboxai_plugin_v1",
  "payload": {
    "action": "sync_content",
    "content_id": "content_12345",
    "data": {...}
  },
  "request_id": "req_unique_123"
}
```

**Response:**
```json
{
  "success": true,
  "message_id": "msg_456",
  "delivery_status": "sent|delivered|failed",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Legacy Flask Bridge Compatibility

### POST /register_plugin
Legacy plugin registration endpoint (Flask compatibility).

**Request/Response:** Similar to `/plugin/register`

### POST /plugin/{plugin_id}/heartbeat
Plugin heartbeat endpoint.

**Parameters:**
- `plugin_id` (path): Plugin identifier

**Response:**
```json
{
  "status": "alive",
  "timestamp": "2024-01-01T12:00:00Z",
  "next_heartbeat": 30
}
```

### GET /plugin/{plugin_id}
Get plugin information.

**Response:**
```json
{
  "plugin_id": "toolboxai_plugin_v1",
  "status": "active|inactive|error",
  "last_seen": "2024-01-01T11:59:30Z",
  "version": "1.2.0",
  "studio_id": "user_12345",
  "capabilities": [...]
}
```

### GET /plugins
List all registered plugins.

**Response:**
```json
{
  "plugins": [
    {
      "plugin_id": "toolboxai_plugin_v1",
      "studio_id": "user_12345",
      "status": "active",
      "last_seen": "2024-01-01T11:59:30Z"
    }
  ],
  "total_count": 1,
  "active_count": 1
}
```

## Content Generation for Roblox

### POST /generate_simple_content
Generate simplified Roblox content (Flask compatibility).

**Request Body:**
```json
{
  "topic": "Basic Addition",
  "grade_level": 2,
  "environment": "classroom",
  "complexity": "simple|medium|complex"
}
```

**Response:**
```json
{
  "content_id": "simple_content_123",
  "scripts": [
    {
      "name": "SimpleAddition",
      "type": "ServerScript",
      "content": "-- Simple addition game logic\nlocal function createAdditionGame()\n  -- Game implementation\nend"
    }
  ],
  "models": [
    {
      "name": "NumberBlocks",
      "type": "Model",
      "description": "3D blocks representing numbers"
    }
  ]
}
```

### GET /script/{script_type}
Get pre-built script templates.

**Parameters:**
- `script_type` (path): "tutorial", "quiz", "game", "utility"

**Query Parameters:**
- `subject` (optional): Filter by subject
- `grade_level` (optional): Filter by grade level

**Response:**
```json
{
  "script_type": "quiz",
  "templates": [
    {
      "id": "quiz_template_math",
      "name": "Math Quiz Template",
      "description": "Interactive math quiz with scoring",
      "content": "-- Quiz template content...",
      "parameters": {
        "questions": "array",
        "time_limit": "number",
        "passing_score": "number"
      }
    }
  ]
}
```

## Environment Synchronization

### Real-time Communication (Pusher Channels)
> ✅ **Migration Complete**: WebSocket endpoints have been migrated to Pusher Channels. See [Migration Guide](../../WEBSOCKET_TO_PUSHER_MIGRATION_COMPLETE.md).

### ~~WebSocket Endpoints~~ (DEPRECATED)

#### ~~ws://127.0.0.1:8008/ws/roblox~~ → Pusher Channel: `roblox-sync`
Real-time Roblox environment synchronization **now uses Pusher Channels**.

**Connection:**
```javascript
// OLD WebSocket approach - DEPRECATED
// const ws = new WebSocket('ws://127.0.0.1:8008/ws/roblox');

// NEW Pusher approach
import Pusher from 'pusher-js';
const pusher = new Pusher(process.env.VITE_PUSHER_KEY, {
  cluster: 'us2',
  authEndpoint: '/api/v1/pusher/auth'
});
const channel = pusher.subscribe('roblox-sync');

channel.bind('pusher:subscription_succeeded', () => {
  console.log('Connected to Roblox sync channel');
});

channel.bind('content_update', (data) => {
  handleRobloxUpdate(data);
});

channel.bind('student_joined', (data) => {
  handleStudentJoin(data);
});
```

**Message Types:**
- `content_update` - Content modifications
- `student_joined` - Student entered experience
- `progress_update` - Learning progress changes
- `collaboration_event` - Multi-user interactions

#### ~~ws://127.0.0.1:8008/ws/plugin/{plugin_id}~~ → Pusher Channel: `private-plugin-{plugin_id}`
Direct plugin communication channel **now uses Pusher private channels**.

**Message Examples:**
```json
{
  "type": "sync_request",
  "content_id": "content_123",
  "changes": {
    "scripts_modified": ["TutorialScript", "QuizLogic"],
    "objects_added": ["Part1", "GUI2"],
    "properties_changed": {
      "Part1": {"Color": [1, 0, 0]}
    }
  }
}
```

## Rojo Integration

### Rojo Manager Service
The platform includes Rojo integration for file synchronization:

**Configuration:**
```json
{
  "rojo_config": {
    "server_host": "localhost",
    "server_port": 34872,
    "project_name": "ToolboxAI-Solutions",
    "auto_sync": true,
    "watch_directories": [
      "roblox_content/",
      "generated_scripts/"
    ]
  }
}
```

**Status Endpoint:**
```bash
curl -X GET "http://127.0.0.1:8008/rojo/status"
```

**Response:**
```json
{
  "status": "running",
  "server_url": "http://localhost:34872",
  "project_path": "/path/to/ToolboxAI-Solutions",
  "connected_clients": 2,
  "last_sync": "2024-01-01T12:00:00Z"
}
```

## Asset Management

### Asset Upload and Management
```json
{
  "asset_types": {
    "images": {
      "supported_formats": ["png", "jpg", "jpeg"],
      "max_size_mb": 50,
      "moderation": true
    },
    "audio": {
      "supported_formats": ["mp3", "ogg"],
      "max_size_mb": 10,
      "moderation": true
    },
    "meshes": {
      "supported_formats": ["obj", "fbx"],
      "max_size_mb": 100,
      "auto_optimization": true
    }
  }
}
```

## Security and Authentication

### Plugin Authentication
```lua
-- Plugin authentication example (Lua)
local HttpService = game:GetService("HttpService")

local function authenticatePlugin()
    local authData = {
        studio_id = game.CreatorId,
        plugin_version = "1.2.0",
        auth_token = plugin.GetSetting("ToolBoxAI_AuthToken")
    }

    local response = HttpService:PostAsync(
        "http://127.0.0.1:8008/plugin/auth",
        HttpService:JSONEncode(authData)
    )

    return HttpService:JSONDecode(response)
end
```

### Content Validation
All deployed content undergoes validation:

- **Script Analysis:** Malicious code detection
- **Asset Scanning:** Inappropriate content filtering
- **Performance Checks:** Memory and CPU usage validation
- **Educational Standards:** Curriculum alignment verification

## Integration Examples

### Python Roblox Client
```python
import requests
import websocket
import json
from typing import Dict, Any

class RobloxIntegration:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}
        self.ws = None

    def deploy_content(
        self,
        content_id: str,
        place_id: str,
        options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Deploy content to Roblox place."""
        payload = {
            "place_id": place_id,
            "deployment_options": options or {},
            "target_environment": "development"
        }

        response = requests.post(
            f"{self.base_url}/api/v1/roblox/deploy/{content_id}",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def download_content(
        self,
        content_id: str,
        format_type: str = "rbxl",
        filename: str = None
    ) -> str:
        """Download Roblox content file."""
        params = {"format": format_type, "include_assets": "true"}

        response = requests.get(
            f"{self.base_url}/api/v1/roblox/download/{content_id}",
            params=params,
            headers=self.headers,
            stream=True
        )
        response.raise_for_status()

        filename = filename or f"content_{content_id}.{format_type}"
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return filename

    def connect_websocket(self, on_message_callback):
        """Connect to Roblox WebSocket for real-time updates."""
        def on_message(ws, message):
            data = json.loads(message)
            on_message_callback(data)

        def on_open(ws):
            # Authenticate
            auth_msg = {
                "type": "auth",
                "token": self.headers["Authorization"].split(" ")[1]
            }
            ws.send(json.dumps(auth_msg))

        self.ws = websocket.WebSocketApp(
            f"ws://127.0.0.1:8008/ws/roblox",
            on_message=on_message,
            on_open=on_open
        )
        self.ws.run_forever()

# Usage example
roblox = RobloxIntegration("http://127.0.0.1:8008", "your_token")

# Deploy content
deployment = roblox.deploy_content(
    "content_12345",
    "123456789",
    {"backup_existing": True}
)
print(f"Deployment ID: {deployment['deployment_id']}")

# Download content
filename = roblox.download_content("content_12345", "rbxl")
print(f"Downloaded: {filename}")
```

### JavaScript Plugin Integration
```javascript
class ToolBoxAIPlugin {
    constructor(config) {
        this.config = config;
        this.websocket = null;
        this.authenticated = false;
    }

    async register() {
        const response = await fetch('http://127.0.0.1:8008/plugin/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                studio_id: this.config.studioId,
                plugin_id: this.config.pluginId,
                version: this.config.version
            })
        });

        const data = await response.json();
        this.authToken = data.auth_token;
        this.websocketEndpoint = data.websocket_endpoint;
        return data;
    }

    // OLD WebSocket approach - DEPRECATED
    /* connectWebSocket() {
        this.websocket = new WebSocket(this.websocketEndpoint);
        // ... WebSocket logic
    } */

    // NEW Pusher approach
    connectPusher() {
        this.pusher = new Pusher(process.env.VITE_PUSHER_KEY, {
            cluster: 'us2',
            authEndpoint: '/api/v1/pusher/auth',
            auth: {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            }
        });

        this.channel = this.pusher.subscribe(`private-plugin-${this.pluginId}`);

        this.channel.bind('pusher:subscription_succeeded', () => {
            console.log('Connected to plugin channel');
        });

        this.channel.bind('content_update', (data) => {
            this.handleMessage(data);
        });

        // Pusher handles reconnection automatically
    }

    // Authentication now handled by Pusher authEndpoint
    // No manual authentication needed

    handleMessage(data) {
        switch (data.type) {
            case 'content_update':
                this.handleContentUpdate(data);
                break;
            case 'sync_request':
                this.handleSyncRequest(data);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    sendHeartbeat() {
        fetch(`http://127.0.0.1:8008/plugin/${this.config.pluginId}/heartbeat`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.authToken}`
            }
        });
    }

    // Start heartbeat interval
    startHeartbeat() {
        setInterval(() => this.sendHeartbeat(), 30000);
    }
}

// Usage
const plugin = new ToolBoxAIPlugin({
    studioId: 'user_12345',
    pluginId: 'toolboxai_plugin_v1',
    version: '1.2.0'
});

plugin.register().then(() => {
    plugin.connectWebSocket();
    plugin.startHeartbeat();
});
```

## Error Handling

### Common Error Responses

#### 400 Bad Request - Invalid Place ID
```json
{
  "error": "Invalid place ID",
  "message": "Place ID must be a valid Roblox place identifier",
  "code": "INVALID_PLACE_ID"
}
```

#### 403 Forbidden - No Place Access
```json
{
  "error": "Access denied",
  "message": "User does not have edit access to this Roblox place",
  "code": "NO_PLACE_ACCESS"
}
```

#### 429 Rate Limited
```json
{
  "error": "Rate limit exceeded",
  "message": "Deployment limit: 3 deployments per hour",
  "retry_after": 1800
}
```

#### 502 Bad Gateway - Roblox API Error
```json
{
  "error": "Roblox API unavailable",
  "message": "Unable to connect to Roblox services",
  "code": "ROBLOX_API_ERROR",
  "retry_recommended": true
}
```

## Performance and Limitations

### Rate Limits
- Content deployment: 3 deployments per hour per user
- Plugin registration: 5 registrations per hour per user
- Content download: 10 downloads per hour per user
- Pusher connections: Unlimited concurrent connections (managed by Pusher)

### File Size Limits
- Place files (.rbxl): 100 MB maximum
- Model files (.rbxm): 50 MB maximum
- Script files: 1 MB maximum per script
- Total content package: 200 MB maximum

### Deployment Times
- Simple content (scripts only): 30-60 seconds
- Medium content (scripts + models): 2-5 minutes
- Complex content (full experience): 5-15 minutes

## Best Practices

### Content Organization
- Use descriptive names for scripts and objects
- Implement proper folder structure in Roblox
- Include documentation comments in generated scripts
- Test content in Studio before production deployment

### Plugin Development
- Implement proper error handling and retry logic
- Use heartbeat mechanism for connection monitoring
- Cache frequently accessed data locally
- Follow Roblox Studio plugin guidelines

### Security Considerations
- Validate all user inputs and content
- Pusher automatically uses secure connections (WSS/TLS) in all environments
- Implement proper authentication and authorization
- Monitor for suspicious plugin behavior
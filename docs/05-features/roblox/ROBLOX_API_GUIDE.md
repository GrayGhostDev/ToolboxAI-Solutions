# ToolBoxAI Roblox Integration API Guide

This guide covers the comprehensive Roblox API endpoints for the ToolBoxAI Educational Platform, providing complete integration for educational game management, AI-powered content generation, student progress tracking, and real-time communication.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [Game Management](#game-management)
- [Content Generation](#content-generation)
- [Student Progress](#student-progress)
- [Real-time Communication](#real-time-communication)
- [Analytics](#analytics)
- [Error Handling](#error-handling)
- [WebSocket Integration](#websocket-integration)
- [Code Examples](#code-examples)

## Overview

**Base URL**: `http://127.0.0.1:8008/api/v1/roblox`
**Universe ID**: `8505376973`
**Client ID**: `2214511122270781418`

### Key Features

- 🎮 **Game Management**: Create, update, and manage educational game instances
- 🤖 **AI Content Generation**: Generate educational content using advanced AI agents
- 📊 **Progress Tracking**: Monitor student progress and achievements
- 🔄 **Real-time Updates**: WebSocket support for live updates
- 📈 **Analytics**: Comprehensive analytics and reporting
- 🔒 **Security**: JWT authentication with role-based access control
- ⚡ **Rate Limiting**: Built-in API protection

## Authentication

All endpoints require JWT authentication. Include your token in the Authorization header:

```http
Authorization: Bearer your_jwt_token_here
```

### User Roles

- **Admin**: Full access to all endpoints
- **Teacher**: Can create games, generate content, view student progress
- **Student**: Can view own progress, join games

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Game Creation**: 10 requests per minute
- **Content Generation**: 5 requests per minute
- **Content Deployment**: 10 requests per minute
- **General Endpoints**: 100 requests per minute

## Game Management

### 1. Create Game Instance

Create a new educational game instance in Roblox.

```http
POST /roblox/game/create
```

**Request Body:**
```json
{
  "title": "Solar System Explorer",
  "description": "Interactive space exploration game",
  "subject": "Science",
  "grade_level": 7,
  "max_players": 25,
  "template_id": "space_station",
  "settings": {
    "enable_voice_chat": false,
    "difficulty": "medium"
  }
}
```

**Response:**
```json
{
  "game_id": "game_abc123def456",
  "title": "Solar System Explorer",
  "description": "Interactive space exploration game",
  "subject": "Science",
  "grade_level": 7,
  "status": "creating",
  "roblox_place_id": "place_78901234",
  "roblox_universe_id": "8505376973",
  "max_players": 25,
  "current_players": 0,
  "created_by": "teacher@example.com",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z",
  "settings": {
    "enable_voice_chat": false,
    "difficulty": "medium"
  },
  "join_url": "https://www.roblox.com/games/place_78901234/"
}
```

### 2. Get Game Instance

Retrieve details of a specific game instance.

```http
GET /roblox/game/{game_id}
```

**Parameters:**
- `game_id`: Unique game identifier

### 3. Update Game Settings

Modify game configuration and settings.

```http
PUT /roblox/game/{game_id}/settings
```

**Request Body:**
```json
{
  "title": "Updated Game Title",
  "max_players": 30,
  "status": "active",
  "settings": {
    "difficulty": "hard"
  }
}
```

### 4. Archive Game Instance

Archive a game instance (preserves student data).

```http
DELETE /roblox/game/{game_id}
```

## Content Generation

### 1. Generate Educational Content

Use AI agents to generate educational content.

```http
POST /roblox/content/generate
```

**Request Body:**
```json
{
  "content_type": "lesson",
  "subject": "Mathematics",
  "grade_level": 8,
  "learning_objectives": [
    "Understand quadratic equations",
    "Solve using the quadratic formula",
    "Graph parabolic functions"
  ],
  "environment_type": "classroom",
  "difficulty": "medium",
  "duration_minutes": 45,
  "include_quiz": true,
  "custom_requirements": "Focus on real-world applications"
}
```

**Response:**
```json
{
  "content_id": "content_xyz789abc123",
  "content_type": "lesson",
  "status": "generating",
  "generated_at": "2025-01-15T11:00:00Z",
  "lesson_content": null,
  "quiz_content": null,
  "terrain_config": null,
  "script_content": null,
  "metadata": {}
}
```

### 2. Get Content Templates

Retrieve available content templates.

```http
GET /roblox/content/templates?category=educational&subject=Science&grade_level=7
```

**Response:**
```json
[
  {
    "template_id": "space_station_science",
    "name": "Space Station Science Lab",
    "description": "Interactive space station for science experiments",
    "category": "educational",
    "subject": "Science",
    "grade_levels": [6, 7, 8, 9],
    "features": ["Zero Gravity Physics", "Laboratory Equipment", "Planet Observation"],
    "difficulty": "intermediate",
    "thumbnail_url": "/templates/space_station.png",
    "created_at": "2024-12-15T10:00:00Z",
    "usage_count": 45
  }
]
```

### 3. Deploy Content

Deploy generated content to a game instance.

```http
POST /roblox/content/deploy
```

**Request Body:**
```json
{
  "content_id": "content_xyz789abc123",
  "game_id": "game_abc123def456",
  "deploy_options": {
    "backup_existing": true,
    "notify_students": true
  },
  "notify_students": true
}
```

### 4. Check Deployment Status

Monitor content deployment progress.

```http
GET /roblox/content/{content_id}/status
```

## Student Progress

### 1. Update Progress

Record student progress in a game instance.

```http
POST /roblox/progress/update
```

**Request Body:**
```json
{
  "student_id": "student_123",
  "game_id": "game_abc123def456",
  "session_id": "session_789",
  "progress_data": {
    "overall_progress": 75.5,
    "current_level": 3,
    "challenges_completed": 8
  },
  "completed_objectives": [
    "Understand quadratic equations",
    "Solve basic quadratic problems"
  ],
  "score": 85.0,
  "time_spent_minutes": 30
}
```

### 2. Get Student Progress

Retrieve comprehensive progress data.

```http
GET /roblox/progress/{student_id}?game_id=game_abc123def456
```

**Response:**
```json
{
  "student_id": "student_123",
  "game_id": "game_abc123def456",
  "overall_progress": 75.5,
  "completed_objectives": [
    "Understand quadratic equations",
    "Solve basic quadratic problems"
  ],
  "current_score": 85.0,
  "time_spent_minutes": 180,
  "last_active": "2025-01-15T14:30:00Z",
  "achievements": ["first_lesson", "week_streak"],
  "checkpoints": [
    {
      "checkpoint_id": "checkpoint_abc123",
      "checkpoint_name": "Chapter 1 Complete",
      "saved_at": "2025-01-15T13:45:00Z"
    }
  ],
  "performance_metrics": {
    "accuracy_rate": 0.85,
    "speed_score": 8.2,
    "engagement_level": 9.1
  }
}
```

### 3. Save Checkpoint

Create a progress checkpoint for students.

```http
POST /roblox/progress/checkpoint
```

**Request Body:**
```json
{
  "student_id": "student_123",
  "game_id": "game_abc123def456",
  "checkpoint_data": {
    "level": 3,
    "position": {"x": 100, "y": 50, "z": 200},
    "inventory": ["tool1", "resource2"],
    "quest_state": "chapter_1_complete"
  },
  "checkpoint_name": "Chapter 1 Complete",
  "auto_save": false
}
```

### 4. Class Leaderboard

Get ranked student performance data.

```http
GET /roblox/progress/leaderboard?game_id=game_abc123def456&leaderboard_type=score&limit=20
```

**Parameters:**
- `leaderboard_type`: `score`, `progress`, or `time`
- `limit`: Number of entries (1-100)

## Real-time Communication

### 1. WebSocket - Game Updates

Connect to real-time game updates.

```javascript
const gameWs = new WebSocket('ws://127.0.0.1:8008/api/v1/roblox/ws/game/game_abc123def456');

gameWs.onmessage = function(event) {
    const data = JSON.parse(event.data);

    switch(data.type) {
        case 'game_state':
            console.log('Initial game state:', data.game);
            break;
        case 'player_joined':
            console.log('Player joined:', data.user_id);
            break;
        case 'student_progress_updated':
            console.log('Student progress:', data.progress);
            break;
        case 'game_settings_updated':
            console.log('Settings updated:', data.updates);
            break;
    }
};

// Send ping
gameWs.send(JSON.stringify({
    type: 'ping'
}));
```

### 2. WebSocket - Content Generation

Monitor AI content generation progress.

```javascript
const contentWs = new WebSocket('ws://127.0.0.1:8008/api/v1/roblox/ws/content');

contentWs.onmessage = function(event) {
    const data = JSON.parse(event.data);

    if (data.type === 'generation_progress') {
        console.log(`Progress: ${data.progress}% - ${data.phase}`);
        updateProgressBar(data.progress);
    }
};

// Subscribe to content updates
contentWs.send(JSON.stringify({
    type: 'subscribe_content',
    content_id: 'content_xyz789abc123'
}));
```

### 3. Roblox Webhooks

Handle incoming webhooks from Roblox servers.

```http
POST /roblox/webhook
```

**Request Headers:**
```
X-Roblox-Signature: sha256=abcdef123456...
Content-Type: application/json
```

**Request Body:**
```json
{
  "event_type": "player_joined",
  "universe_id": "8505376973",
  "place_id": "place_78901234",
  "user_id": "roblox_user_456",
  "data": {
    "join_time": "2025-01-15T15:00:00Z",
    "user_info": {
      "display_name": "StudentName",
      "membership_type": "None"
    }
  }
}
```

## Analytics

### 1. Session Analytics

Get detailed analytics for a gaming session.

```http
GET /roblox/analytics/session/{session_id}
```

**Response:**
```json
{
  "session_id": "session_789",
  "game_id": "game_abc123def456",
  "student_count": 23,
  "duration_minutes": 45,
  "engagement_score": 8.2,
  "completion_rate": 85.4,
  "learning_outcomes": {
    "objectives_met": 12,
    "objectives_total": 15,
    "average_score": 78.3,
    "improvement_rate": 23.5
  },
  "activity_heatmap": [
    {"minute": 0, "activity_level": 8},
    {"minute": 1, "activity_level": 9}
  ],
  "performance_metrics": {
    "response_time_avg": 1.2,
    "error_rate": 0.03,
    "memory_usage": 245.6
  }
}
```

### 2. Performance Metrics

Get system performance data (Admin only).

```http
GET /roblox/analytics/performance
```

### 3. Track Custom Events

Record custom analytics events.

```http
POST /roblox/analytics/event
```

**Request Body:**
```json
{
  "event_type": "achievement_unlock",
  "game_id": "game_abc123def456",
  "student_id": "student_123",
  "session_id": "session_789",
  "event_data": {
    "achievement": "math_master",
    "level_reached": 10,
    "time_to_unlock": 1200
  }
}
```

## Error Handling

The API uses standard HTTP status codes and returns detailed error information:

### Common Error Responses

**400 Bad Request:**
```json
{
  "detail": "Validation error: Each learning objective must be at least 10 characters"
}
```

**401 Unauthorized:**
```json
{
  "detail": "Could not validate credentials"
}
```

**403 Forbidden:**
```json
{
  "detail": "Only teachers and admins can create game instances"
}
```

**404 Not Found:**
```json
{
  "detail": "Game instance game_abc123def456 not found"
}
```

**429 Too Many Requests:**
```json
{
  "detail": "Rate limit exceeded. Try again in 60 seconds"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Internal server error occurred"
}
```

## Code Examples

### Python Client Example

```python
import requests
import json

class RobloxAPIClient:
    def __init__(self, base_url="http://127.0.0.1:8008/api/v1/roblox", token=None):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def create_game(self, title, subject, grade_level, template_id=None):
        """Create a new game instance"""
        data = {
            "title": title,
            "subject": subject,
            "grade_level": grade_level,
            "template_id": template_id
        }

        response = requests.post(
            f"{self.base_url}/game/create",
            headers=self.headers,
            json=data
        )

        return response.json()

    def generate_content(self, content_type, subject, grade_level, objectives):
        """Generate educational content"""
        data = {
            "content_type": content_type,
            "subject": subject,
            "grade_level": grade_level,
            "learning_objectives": objectives,
            "environment_type": "classroom"
        }

        response = requests.post(
            f"{self.base_url}/content/generate",
            headers=self.headers,
            json=data
        )

        return response.json()

    def update_progress(self, student_id, game_id, session_id, progress_data):
        """Update student progress"""
        data = {
            "student_id": student_id,
            "game_id": game_id,
            "session_id": session_id,
            "progress_data": progress_data
        }

        response = requests.post(
            f"{self.base_url}/progress/update",
            headers=self.headers,
            json=data
        )

        return response.json()

# Usage example
client = RobloxAPIClient(token="your_jwt_token")

# Create a math game
game = client.create_game(
    title="Algebra Adventures",
    subject="Mathematics",
    grade_level=8,
    template_id="math_adventure_castle"
)

print(f"Created game: {game['game_id']}")

# Generate lesson content
content = client.generate_content(
    content_type="lesson",
    subject="Mathematics",
    grade_level=8,
    objectives=["Solve quadratic equations", "Graph parabolas"]
)

print(f"Generating content: {content['content_id']}")
```

### JavaScript/Node.js Example

```javascript
class RobloxAPI {
    constructor(baseUrl = 'http://127.0.0.1:8008/api/v1/roblox', token = null) {
        this.baseUrl = baseUrl;
        this.headers = {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };
    }

    async createGame(gameData) {
        const response = await fetch(`${this.baseUrl}/game/create`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify(gameData)
        });

        return await response.json();
    }

    async generateContent(contentData) {
        const response = await fetch(`${this.baseUrl}/content/generate`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify(contentData)
        });

        return await response.json();
    }

    async getStudentProgress(studentId, gameId) {
        const url = `${this.baseUrl}/progress/${studentId}?game_id=${gameId}`;
        const response = await fetch(url, {
            headers: this.headers
        });

        return await response.json();
    }

    connectGameWebSocket(gameId, onMessage) {
        const ws = new WebSocket(`ws://127.0.0.1:8008/api/v1/roblox/ws/game/${gameId}`);

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            onMessage(data);
        };

        return ws;
    }
}

// Usage example
const api = new RobloxAPI(undefined, 'your_jwt_token');

// Create a science game
const game = await api.createGame({
    title: 'Space Station Science',
    subject: 'Science',
    grade_level: 7,
    template_id: 'space_station_science'
});

// Connect to real-time updates
const ws = api.connectGameWebSocket(game.game_id, (data) => {
    console.log('Game update:', data);
});
```

### Lua Script Example (For Roblox Studio)

```lua
-- Roblox Studio script for communicating with ToolBoxAI backend

local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")

local API_BASE = "http://127.0.0.1:8008/api/v1/roblox"
local GAME_ID = "your_game_id_here"

local ToolBoxAIAPI = {}

function ToolBoxAIAPI:updateProgress(player, progressData)
    local data = {
        student_id = tostring(player.UserId),
        game_id = GAME_ID,
        session_id = "session_" .. tick(),
        progress_data = progressData,
        time_spent_minutes = 5
    }

    local success, result = pcall(function()
        return HttpService:PostAsync(
            API_BASE .. "/progress/update",
            HttpService:JSONEncode(data),
            Enum.HttpContentType.ApplicationJson
        )
    end)

    if success then
        print("Progress updated for " .. player.Name)
    else
        warn("Failed to update progress: " .. tostring(result))
    end
end

function ToolBoxAIAPI:saveCheckpoint(player, checkpointData)
    local data = {
        student_id = tostring(player.UserId),
        game_id = GAME_ID,
        checkpoint_data = checkpointData,
        checkpoint_name = "Auto Save"
    }

    HttpService:PostAsync(
        API_BASE .. "/progress/checkpoint",
        HttpService:JSONEncode(data),
        Enum.HttpContentType.ApplicationJson
    )
end

-- Example usage: Update progress when player completes a task
local function onTaskCompleted(player, taskName)
    local progressData = {
        overall_progress = 75,
        tasks_completed = {taskName},
        current_level = 3
    }

    ToolBoxAIAPI:updateProgress(player, progressData)
end

-- Auto-save checkpoint every 5 minutes
spawn(function()
    while wait(300) do -- 300 seconds = 5 minutes
        for _, player in pairs(Players:GetPlayers()) do
            local checkpointData = {
                position = player.Character.HumanoidRootPart.Position,
                health = player.Character.Humanoid.Health,
                inventory = {} -- Add inventory data
            }

            ToolBoxAIAPI:saveCheckpoint(player, checkpointData)
        end
    end
end)

return ToolBoxAIAPI
```

## Environment Variables

Set these environment variables for proper integration:

```bash
# Required
ROBLOX_CLIENT_ID=2214511122270781418
ROBLOX_CLIENT_SECRET=your_client_secret
ROBLOX_API_KEY=your_api_key
ROBLOX_UNIVERSE_ID=8505376973

# Optional
ROBLOX_PLUGIN_PORT=64989
```

## Testing the API

Use the built-in FastAPI docs at `http://127.0.0.1:8008/docs` to test endpoints interactively.

### Quick Test Commands

```bash
# Check plugin status
curl http://127.0.0.1:8008/api/v1/roblox/plugin/status

# Get templates (requires auth)
curl -H "Authorization: Bearer your_token" \
     http://127.0.0.1:8008/api/v1/roblox/content/templates

# Create a game (requires auth)
curl -X POST \
     -H "Authorization: Bearer your_token" \
     -H "Content-Type: application/json" \
     -d '{"title":"Test Game","subject":"Math","grade_level":8}' \
     http://127.0.0.1:8008/api/v1/roblox/game/create
```

## Support and Documentation

- **OpenAPI Docs**: `http://127.0.0.1:8008/docs`
- **ReDoc**: `http://127.0.0.1:8008/redoc`
- **Health Check**: `http://127.0.0.1:8008/health`

For additional support or questions about the Roblox API integration, please refer to the main ToolBoxAI documentation or contact the development team.
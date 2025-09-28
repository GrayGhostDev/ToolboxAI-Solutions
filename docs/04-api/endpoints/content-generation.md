# Content Generation Endpoints

## Overview

The ToolBoxAI platform provides AI-powered educational content generation for creating immersive 3D Roblox learning experiences. These endpoints generate lessons, quizzes, terrain, and scripts tailored to specific educational requirements.

## Base URL
```
http://127.0.0.1:8008
```

## Content Generation Endpoints

### POST /api/v1/content/generate
Generate comprehensive educational content including lessons, terrain, and scripts.

**Authentication:** Required (Bearer token)

**Request Body:**
```json
{
  "subject": "Mathematics|Science|History|English|Art|Geography|Computer Science|Physics|Chemistry|Biology",
  "grade_level": 1-12,
  "learning_objectives": [
    {
      "title": "Understand basic algebra",
      "description": "Students will learn to solve linear equations",
      "bloom_level": "Apply",
      "measurable": true
    }
  ],
  "environment_type": "classroom|laboratory|outdoor|historical|futuristic|underwater|space_station|fantasy|custom",
  "terrain_size": "small|medium|large|xlarge",
  "include_quiz": true,
  "difficulty_level": "easy|medium|hard|expert",
  "duration_minutes": 30,
  "max_students": 30,
  "accessibility_features": false,
  "multilingual": false,
  "custom_requirements": "Additional specific requirements"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Content generated successfully",
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_12345",
  "content_id": "content_67890",
  "content": {
    "lesson_plan": {
      "title": "Introduction to Algebra",
      "objectives": [...],
      "activities": [...],
      "assessment_criteria": [...]
    },
    "roblox_environment": {
      "place_id": "123456789",
      "environment_settings": {...}
    }
  },
  "scripts": [
    {
      "name": "MathTutorScript",
      "content": "-- Lua script content here\nlocal Players = game:GetService('Players')\n...",
      "script_type": "server",
      "dependencies": ["PlayerService", "MathLibrary"],
      "description": "Main tutorial logic for algebra lessons"
    }
  ],
  "terrain": {
    "material": "Grass",
    "size": "medium",
    "features": ["hills", "water", "buildings"],
    "biome": "temperate",
    "elevation_map": {...}
  },
  "game_mechanics": {
    "movement_enabled": true,
    "chat_enabled": true,
    "collision_detection": true,
    "gravity_enabled": true,
    "respawn_enabled": true,
    "team_mode": false
  },
  "estimated_build_time": 45,
  "resource_requirements": {
    "memory_mb": 512,
    "cpu_cores": 2,
    "storage_mb": 100
  }
}
```

**cURL Example:**
```bash
curl -X POST "http://127.0.0.1:8008/api/v1/content/generate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Mathematics",
    "grade_level": 7,
    "learning_objectives": [
      {
        "title": "Solve linear equations",
        "description": "Students will solve equations of the form ax + b = c"
      }
    ],
    "environment_type": "classroom",
    "include_quiz": true
  }'
```

### POST /generate_content
Legacy content generation endpoint (maintained for backward compatibility).

**Request/Response:** Similar to `/api/v1/content/generate`

### POST /generate_quiz
Generate educational quizzes for specific topics.

**Authentication:** Required (Bearer token)

**Query Parameters:**
- `subject` (required): Subject area
- `topic` (required): Specific topic within subject
- `difficulty` (optional): "easy", "medium", "hard" (default: "medium")
- `num_questions` (optional): Number of questions (default: 5)
- `grade_level` (optional): Grade level 1-12 (default: 5)

**Response:**
```json
{
  "success": true,
  "message": "Quiz generated successfully",
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_12345",
  "quiz": {
    "id": "quiz_67890",
    "title": "Algebra Basics Quiz",
    "description": "Test your understanding of linear equations",
    "subject": "Mathematics",
    "grade_level": 7,
    "questions": [
      {
        "id": "q1",
        "question_type": "multiple_choice",
        "question_text": "What is the value of x in 2x + 4 = 10?",
        "options": [
          {
            "id": "a",
            "text": "2",
            "is_correct": false
          },
          {
            "id": "b",
            "text": "3",
            "is_correct": true,
            "explanation": "Subtract 4 from both sides: 2x = 6, then divide by 2"
          },
          {
            "id": "c",
            "text": "4",
            "is_correct": false
          }
        ],
        "difficulty": "medium",
        "points": 1,
        "time_limit": 60,
        "hint": "Remember to isolate the variable",
        "explanation": "To solve 2x + 4 = 10, subtract 4 from both sides to get 2x = 6, then divide by 2 to get x = 3"
      }
    ],
    "time_limit": 300,
    "passing_score": 70,
    "max_attempts": 3,
    "shuffle_questions": true,
    "shuffle_options": true,
    "show_results": true
  },
  "lua_script": "-- Quiz implementation script\nlocal QuizService = require(script.QuizService)\n...",
  "ui_elements": [
    {
      "type": "QuestionDisplay",
      "properties": {...}
    }
  ]
}
```

**cURL Example:**
```bash
curl -X POST "http://127.0.0.1:8008/generate_quiz?subject=Mathematics&topic=Linear%20Equations&difficulty=medium&num_questions=5&grade_level=7" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### POST /generate_terrain
Generate Roblox terrain for educational environments.

**Authentication:** Required (Bearer token)

**Query Parameters:**
- `theme` (required): Terrain theme
- `size` (optional): "small", "medium", "large" (default: "medium")
- `biome` (optional): Terrain biome (default: "temperate")

**Request Body:**
```json
{
  "features": ["mountains", "forests", "beaches"],
  "educational_context": ["outdoor", "indoor", "open-world"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Terrain generated successfully",
  "terrain_data": {
    "height_map": [...],
    "material_map": [...],
    "decoration_points": [...],
    "spawn_locations": [...]
  },
  "lua_script": "-- Terrain generation script\nlocal TerrainService = game:GetService('Terrain')\n...",
  "estimated_generation_time": 30
}
```

## Content Retrieval

### GET /content/{content_id}
Retrieve previously generated content by ID.

**Authentication:** Required (Bearer token)

**Parameters:**
- `content_id` (path): Unique content identifier

**Response:**
```json
{
  "content_id": "content_67890",
  "created_at": "2024-01-01T12:00:00Z",
  "subject": "Mathematics",
  "grade_level": 7,
  "status": "completed",
  "content": {...},
  "scripts": [...],
  "terrain": {...},
  "usage_stats": {
    "views": 45,
    "deployments": 3,
    "student_interactions": 127
  }
}
```

## Real-time Content Generation

Content generation can be monitored in real-time using Pusher Channels:

### Pusher Channels
- `content-generation` - General content creation progress
- `user-content-{user_id}` - User-specific content updates

### Event Types
- `generation_started` - Content generation initiated
- `progress_update` - Generation progress (percentage complete)
- `generation_completed` - Content ready for use
- `generation_failed` - Error occurred during generation

**JavaScript Example:**
```javascript
import Pusher from 'pusher-js';

const pusher = new Pusher('YOUR_PUSHER_KEY', {
  cluster: 'YOUR_CLUSTER',
  authEndpoint: 'http://127.0.0.1:8008/pusher/auth',
  auth: {
    headers: {
      'Authorization': 'Bearer YOUR_TOKEN'
    }
  }
});

const channel = pusher.subscribe('content-generation');

channel.bind('generation_started', (data) => {
  console.log('Content generation started:', data);
});

channel.bind('progress_update', (data) => {
  console.log(`Progress: ${data.percentage}%`);
});

channel.bind('generation_completed', (data) => {
  console.log('Content ready:', data.content_id);
});
```

## Content Types and Templates

### Environment Types

| Type | Description | Use Cases |
|------|-------------|-----------|
| `classroom` | Traditional classroom setup | Lectures, presentations, group work |
| `laboratory` | Science lab environment | Experiments, demonstrations |
| `outdoor` | Open outdoor environment | Field trips, nature studies |
| `historical` | Historical time periods | History lessons, cultural studies |
| `futuristic` | Sci-fi environments | Advanced science, technology |
| `underwater` | Underwater settings | Marine biology, physics |
| `space_station` | Space environments | Astronomy, physics, engineering |
| `fantasy` | Fantasy/magical settings | Literature, creative writing |
| `custom` | User-defined environment | Specialized requirements |

### Subject-Specific Templates

#### Mathematics
- Geometry playground with 3D shapes
- Algebra visualization with interactive equations
- Statistics lab with data manipulation tools

#### Science
- Chemistry lab with molecular models
- Physics simulation environments
- Biology ecosystem simulations

#### History
- Historical recreations of events
- Interactive timelines
- Cultural exploration environments

## Advanced Features

### AI Agent Integration
Content generation uses multiple AI agents:

- **Content Agent:** Generates lesson plans and educational materials
- **Script Agent:** Creates Lua scripts for Roblox implementation
- **Terrain Agent:** Designs 3D environments
- **Quiz Agent:** Develops assessments and interactive elements

### Customization Options

#### Learning Objectives Format
```json
{
  "id": "obj_001",
  "title": "Solve linear equations",
  "description": "Students will solve equations of the form ax + b = c",
  "bloom_level": "Apply|Analyze|Evaluate|Create",
  "measurable": true,
  "assessment_method": "quiz|project|observation",
  "time_allocation": 15
}
```

#### Accessibility Features
- Screen reader compatibility
- Color blind friendly palettes
- Keyboard navigation support
- Subtitle generation for audio content
- Simplified UI options

#### Multilingual Support
- Content translation (Spanish, French, Mandarin)
- Culturally appropriate examples
- Region-specific educational standards

## Error Handling

### Common Error Responses

#### 400 Bad Request
```json
{
  "error": "Invalid subject",
  "message": "Subject 'InvalidSubject' is not supported",
  "supported_subjects": ["Mathematics", "Science", "History", ...]
}
```

#### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "grade_level"],
      "msg": "ensure this value is greater than or equal to 1",
      "type": "value_error.number.not_ge"
    }
  ]
}
```

#### 429 Rate Limit
```json
{
  "error": "Rate limit exceeded",
  "message": "Content generation limited to 5 requests per hour",
  "retry_after": 3600
}
```

## Usage Examples

### Complete Integration Example (Python)
```python
import requests
import time
from typing import Dict, Any

class ContentGenerator:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}

    def generate_lesson(
        self,
        subject: str,
        grade_level: int,
        objectives: list,
        environment_type: str = "classroom"
    ) -> Dict[str, Any]:
        """Generate complete educational content."""
        payload = {
            "subject": subject,
            "grade_level": grade_level,
            "learning_objectives": objectives,
            "environment_type": environment_type,
            "include_quiz": True
        }

        response = requests.post(
            f"{self.base_url}/api/v1/content/generate",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()

        return response.json()

    def generate_quiz(
        self,
        subject: str,
        topic: str,
        difficulty: str = "medium",
        num_questions: int = 5
    ) -> Dict[str, Any]:
        """Generate quiz for specific topic."""
        params = {
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty,
            "num_questions": num_questions
        }

        response = requests.post(
            f"{self.base_url}/generate_quiz",
            params=params,
            headers=self.headers
        )
        response.raise_for_status()

        return response.json()

    def get_content(self, content_id: str) -> Dict[str, Any]:
        """Retrieve generated content."""
        response = requests.get(
            f"{self.base_url}/content/{content_id}",
            headers=self.headers
        )
        response.raise_for_status()

        return response.json()

# Usage example
generator = ContentGenerator("http://127.0.0.1:8008", "your_token")

# Generate a math lesson
lesson = generator.generate_lesson(
    subject="Mathematics",
    grade_level=7,
    objectives=[
        {
            "title": "Solve linear equations",
            "description": "Students will solve equations of the form ax + b = c"
        }
    ],
    environment_type="classroom"
)

print(f"Generated content ID: {lesson['content_id']}")
```

### React Integration Example
```typescript
import React, { useState } from 'react';

interface ContentRequest {
  subject: string;
  grade_level: number;
  learning_objectives: Array<{
    title: string;
    description: string;
  }>;
  environment_type: string;
}

const ContentGenerator: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [content, setContent] = useState(null);

  const generateContent = async (request: ContentRequest) => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/content/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getToken()}`
        },
        body: JSON.stringify(request)
      });

      const data = await response.json();
      setContent(data);
    } catch (error) {
      console.error('Content generation failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {loading ? (
        <div>Generating content...</div>
      ) : (
        <div>
          {/* Content generation form */}
          {/* Generated content display */}
        </div>
      )}
    </div>
  );
};
```

## Performance and Limitations

### Rate Limits
- Content generation: 5 requests per hour per user
- Quiz generation: 10 requests per hour per user
- Terrain generation: 3 requests per hour per user

### Generation Times
- Simple content (quiz only): 5-15 seconds
- Full lesson with terrain: 1-3 minutes
- Complex environments: 3-5 minutes

### Content Limits
- Maximum 10 learning objectives per request
- Quiz limit: 50 questions maximum
- Terrain size: Up to "xlarge" (2048x2048 studs)
- Script complexity: 10,000 lines maximum
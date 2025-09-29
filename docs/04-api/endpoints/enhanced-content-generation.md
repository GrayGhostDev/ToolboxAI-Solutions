# Enhanced Content Generation API

## Overview

The Enhanced Content Generation API provides a comprehensive 5-stage pipeline for creating educational Roblox content with AI assistance. The system leverages 91+ specialized agents coordinated through the SPARC framework to deliver high-quality, personalized educational experiences.

## Pipeline Stages

1. **Ideation**: Creative concept generation aligned with learning objectives
2. **Generation**: Content, script, and asset creation
3. **Validation**: Quality, safety, and educational value verification
4. **Optimization**: Performance and personalization enhancements
5. **Deployment**: Roblox environment packaging and deployment

## Authentication

All endpoints require JWT authentication unless otherwise noted.

```http
Authorization: Bearer <your-jwt-token>
```

## Rate Limits

- Content Generation: 10 requests per minute per user
- Content Validation: 20 requests per minute per user
- Content Personalization: 15 requests per minute per user
- Other endpoints: Standard rate limits apply

## Endpoints

### Generate Content

Initiate enhanced content generation using the 5-stage pipeline.

**Endpoint**: `POST /api/v1/content/generate`

**Request Body**:
```json
{
  "subject": "Mathematics",
  "grade_level": "6-8",
  "content_type": "lesson",
  "learning_objectives": [
    "Understand basic algebraic concepts",
    "Solve simple linear equations",
    "Apply algebra to real-world problems"
  ],
  "difficulty_level": "medium",
  "duration_minutes": 45,
  "personalization_enabled": true,
  "roblox_requirements": {
    "environment_type": "classroom",
    "max_players": 25,
    "required_assets": ["whiteboard", "calculator"]
  },
  "custom_parameters": {
    "theme": "space_exploration",
    "include_mini_games": true
  }
}
```

**Response**:
```json
{
  "pipeline_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "initiated",
  "message": "Content generation pipeline started successfully",
  "current_stage": "ideation",
  "progress_percentage": 0.0,
  "estimated_completion_time": "2025-09-19T14:30:00Z",
  "pusher_channel": "content-generation-550e8400-e29b-41d4-a716-446655440000",
  "pusher_channel": "content-generation-550e8400-e29b-41d4-a716-446655440000"  // MIGRATED: was websocket_url
}
```

**Validation Rules**:
- `subject`: 1-100 characters
- `grade_level`: Must be one of: `K-2`, `3-5`, `6-8`, `9-12`, `college`, `adult`
- `content_type`: Must be one of: `lesson`, `quiz`, `activity`, `scenario`, `assessment`, `project`, `simulation`
- `learning_objectives`: 1-10 items, each 1-500 characters
- `duration_minutes`: 5-120 minutes
- `difficulty_level`: One of: `easy`, `medium`, `hard`

### Get Generation Status

Get the current status of a content generation pipeline.

**Endpoint**: `GET /api/v1/content/status/{pipeline_id}`

**Response**:
```json
{
  "pipeline_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "current_stage": "generation",
  "progress_percentage": 65.0,
  "started_at": "2025-09-19T14:00:00Z",
  "estimated_completion": "2025-09-19T14:30:00Z",
  "completed_at": null,
  "stage_details": {
    "current_agents": ["ScriptAgent", "TerrainAgent", "AssetAgent"],
    "completed_tasks": 8,
    "total_tasks": 12
  },
  "errors": [],
  "warnings": ["Asset optimization recommended"],
  "generated_artifacts": {
    "ideas": 3,
    "scripts": 2,
    "assets": 1
  },
  "quality_metrics": {
    "educational_score": 0.85,
    "technical_score": 0.78,
    "safety_score": 0.95
  }
}
```

**Status Values**:
- `initiated`: Pipeline has been created
- `processing`: Pipeline is actively running
- `completed`: Pipeline finished successfully
- `failed`: Pipeline encountered unrecoverable errors
- `cancelled`: Pipeline was cancelled by user

**Stage Values**:
- `ideation`: Generating creative concepts
- `generation`: Creating content and assets
- `validation`: Quality and safety verification
- `optimization`: Performance and personalization
- `deployment`: Roblox packaging and deployment

### Get Generated Content

Retrieve generated content by ID.

**Endpoint**: `GET /api/v1/content/{content_id}`

**Query Parameters**:
- `include_validation` (boolean, optional): Include validation report in response

**Response**:
```json
{
  "content_id": "content-123",
  "pipeline_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user-456",
  "content_type": "lesson",
  "subject": "Mathematics",
  "grade_level": "6-8",
  "enhanced_content": {
    "title": "Introduction to Algebra",
    "description": "Interactive lesson covering basic algebraic concepts",
    "scenes": [
      {
        "id": "scene_1",
        "name": "Introduction",
        "duration": 10,
        "activities": ["video", "discussion"]
      }
    ],
    "characters": [
      {
        "name": "Professor Ada",
        "role": "instructor",
        "personality": "encouraging"
      }
    ],
    "learning_checkpoints": [
      {
        "objective": "Understand variables",
        "assessment_type": "interactive_quiz",
        "passing_score": 80
      }
    ]
  },
  "generated_scripts": [
    {
      "name": "MainGameScript",
      "type": "ServerScript",
      "code": "-- Main game logic\nlocal GameService = require(...)\n...",
      "functions": ["initialize", "handlePlayerJoin", "updateScore"],
      "complexity_score": 0.65
    }
  ],
  "generated_assets": [
    {
      "name": "ClassroomEnvironment",
      "type": "Model",
      "file_size_mb": 4.2,
      "optimization_level": "medium",
      "description": "3D classroom with interactive whiteboard"
    }
  ],
  "quality_score": 0.87,
  "personalization_applied": true,
  "validation_report": {
    "overall_score": 0.87,
    "compliant": true,
    "issues_count": 0,
    "warnings_count": 1,
    "recommendations": ["Consider adding audio descriptions for accessibility"]
  },
  "created_at": "2025-09-19T14:00:00Z",
  "generation_time_seconds": 185.3
}
```

### Validate Content

Validate existing content for quality, safety, and compliance.

**Endpoint**: `POST /api/v1/content/validate`

**Request Body**:
```json
{
  "content": {
    "title": "Math Quiz",
    "description": "Basic arithmetic quiz",
    "learning_objectives": ["Add two numbers", "Subtract numbers"],
    "scripts": [
      {
        "name": "QuizScript",
        "code": "local questions = {...}"
      }
    ],
    "assets": [
      {
        "name": "Calculator",
        "type": "Tool",
        "file_size_mb": 1.2
      }
    ]
  },
  "content_type": "quiz",
  "target_age": 10,
  "validation_categories": ["educational_value", "safety", "technical_quality"],
  "strict_mode": false
}
```

**Response**:
```json
{
  "validation_id": "val-789",
  "overall_score": 0.82,
  "educational_score": 0.85,
  "technical_score": 0.78,
  "safety_score": 0.95,
  "engagement_score": 0.73,
  "accessibility_score": 0.76,
  "compliant": true,
  "issues_count": 2,
  "warnings_count": 3,
  "detailed_report": {
    "issues": [
      {
        "category": "accessibility",
        "severity": "medium",
        "description": "Insufficient color contrast in UI elements",
        "location": "QuizInterface",
        "suggestion": "Increase contrast to at least 4.5:1",
        "auto_fixable": true
      }
    ],
    "warnings": [
      "Consider adding keyboard navigation support"
    ],
    "passed_checks": [
      "Age-appropriate content",
      "COPPA compliance",
      "Script security validation"
    ]
  },
  "recommendations": [
    "Add more interactive elements to increase engagement",
    "Include audio feedback for correct answers",
    "Implement progress tracking"
  ],
  "validated_at": "2025-09-19T14:15:00Z",
  "validation_duration_seconds": 12.5
}
```

**Validation Categories**:
- `educational_value`: Curriculum alignment and learning objectives
- `technical_quality`: Code quality, performance, and optimization
- `safety_compliance`: Age-appropriateness and safety guidelines
- `engagement_design`: Game mechanics and user engagement
- `accessibility`: WCAG compliance and inclusive design
- `performance`: Resource usage and optimization
- `localization`: Multi-language support readiness

### Get Content History

Get user's content generation history with filtering and pagination.

**Endpoint**: `GET /api/v1/content/history`

**Query Parameters**:
- `page` (integer, default: 1): Page number (1-based)
- `page_size` (integer, default: 20, max: 100): Items per page
- `content_type` (string, optional): Filter by content type
- `subject` (string, optional): Filter by subject

**Response**:
```json
{
  "items": [
    {
      "pipeline_id": "pipeline-1",
      "content_id": "content-1",
      "content_type": "lesson",
      "subject": "Mathematics",
      "grade_level": "6-8",
      "status": "completed",
      "quality_score": 0.87,
      "created_at": "2025-09-19T14:00:00Z",
      "completed_at": "2025-09-19T14:05:00Z",
      "generation_time": 305.2
    }
  ],
  "total_count": 25,
  "page": 1,
  "page_size": 20,
  "has_more": true
}
```

### Apply Personalization

Apply personalization to existing content based on user profile.

**Endpoint**: `POST /api/v1/content/personalize`

**Request Body**:
```json
{
  "content_id": "content-123",
  "personalization_params": {
    "visual_style": "colorful",
    "difficulty_adjustment": "easier",
    "interaction_frequency": "high",
    "preferred_activities": ["games", "simulations"]
  },
  "learning_style": "kinesthetic",
  "difficulty_preference": "adaptive"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Personalization applied successfully",
  "content_id": "content-123",
  "personalization_id": "pers-456",
  "applied_at": "2025-09-19T14:20:00Z",
  "parameters": {
    "visual_style": "colorful",
    "difficulty_adjustment": "easier",
    "learning_style": "kinesthetic"
  }
}
```

## Real-time Updates

### Real-time Updates (Pusher Channels)
> ✅ **Migration Complete**: WebSocket connections have been replaced with Pusher Channels. See [Migration Guide](../../WEBSOCKET_TO_PUSHER_MIGRATION_COMPLETE.md).

~~### WebSocket Connection~~ (DEPRECATED)

Connect to receive real-time updates about pipeline progress.

**Endpoint**: `WS /api/v1/content/ws/{pipeline_id}`

**Message Types**:

**Status Update**:
```json
{
  "type": "status_update",
  "pipeline_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "current_stage": "generation",
  "progress": 45.0,
  "message": "Creating content scripts and assets",
  "timestamp": "2025-09-19T14:10:00Z"
}
```

**Stage Transition**:
```json
{
  "type": "stage-started",
  "pipeline_id": "550e8400-e29b-41d4-a716-446655440000",
  "stage": "validation",
  "progress": 60.0,
  "message": "Starting content validation process",
  "timestamp": "2025-09-19T14:12:00Z"
}
```

**Completion**:
```json
{
  "type": "generation-completed",
  "pipeline_id": "550e8400-e29b-41d4-a716-446655440000",
  "content_id": "content-123",
  "quality_score": 0.87,
  "generation_time": 305.2,
  "message": "Content generation completed successfully",
  "timestamp": "2025-09-19T14:15:00Z"
}
```

**Error**:
```json
{
  "type": "generation-failed",
  "pipeline_id": "550e8400-e29b-41d4-a716-446655440000",
  "error": "Validation failed: Content does not meet safety requirements",
  "stage": "validation",
  "timestamp": "2025-09-19T14:13:00Z"
}
```

### Pusher Channels

Subscribe to Pusher channels for real-time updates (**primary method**, replaces WebSocket).

**Channel**: `content-generation-{pipeline_id}`

**Events**:
- `generation-started`: Pipeline initiation
- `stage-started`: New stage beginning
- `stage-progress`: Progress within a stage
- `generation-completed`: Successful completion
- `generation-failed`: Pipeline failure

## Error Handling

### HTTP Status Codes

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation errors
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### Error Response Format

```json
{
  "detail": "Validation failed",
  "errors": [
    {
      "field": "learning_objectives",
      "message": "At least one learning objective is required"
    }
  ],
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2025-09-19T14:00:00Z"
}
```

### Common Error Codes

- `VALIDATION_ERROR`: Request validation failed
- `PIPELINE_NOT_FOUND`: Pipeline ID not found
- `CONTENT_NOT_FOUND`: Content ID not found
- `ACCESS_DENIED`: User lacks permission
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `PIPELINE_FAILED`: Content generation failed
- `INVALID_CONTENT_TYPE`: Unsupported content type
- `INVALID_GRADE_LEVEL`: Unsupported grade level

## Usage Examples

### Python with aiohttp

```python
import aiohttp
import asyncio

async def generate_content():
    headers = {"Authorization": "Bearer your-jwt-token"}

    request_data = {
        "subject": "Science",
        "grade_level": "3-5",
        "content_type": "activity",
        "learning_objectives": [
            "Understand the water cycle",
            "Identify states of matter"
        ]
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        # Start generation
        async with session.post(
            "http://localhost:8008/api/v1/content/generate",
            json=request_data
        ) as response:
            data = await response.json()
            pipeline_id = data["pipeline_id"]

        # Poll for completion
        while True:
            async with session.get(
                f"http://localhost:8008/api/v1/content/status/{pipeline_id}"
            ) as response:
                status = await response.json()

                if status["status"] == "completed":
                    print(f"Generation completed! Content ID: {status.get('content_id')}")
                    break
                elif status["status"] == "failed":
                    print(f"Generation failed: {status.get('errors')}")
                    break

                print(f"Progress: {status['progress_percentage']:.1f}%")
                await asyncio.sleep(5)

# Run the example
asyncio.run(generate_content())
```

### JavaScript with fetch

```javascript
// Authentication
const token = 'your-jwt-token';
const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
};

// Generate content
async function generateContent() {
    const requestData = {
        subject: 'History',
        grade_level: '9-12',
        content_type: 'scenario',
        learning_objectives: [
            'Understand causes of World War I',
            'Analyze the impact of trench warfare'
        ],
        roblox_requirements: {
            environment_type: 'historical_battlefield',
            atmosphere: 'dramatic'
        }
    };

    try {
        // Start generation
        const response = await fetch('http://localhost:8008/api/v1/content/generate', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Generation started:', data.pipeline_id);

        // OLD WebSocket approach - DEPRECATED
        // const websocket = new WebSocket(`ws://localhost:8008/api/v1/content/ws/${data.pipeline_id}`);

        // NEW Pusher approach
        import Pusher from 'pusher-js';

        const pusher = new Pusher(process.env.VITE_PUSHER_KEY, {
            cluster: 'us2',
            authEndpoint: '/api/v1/pusher/auth',
            auth: {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            }
        });

        const channel = pusher.subscribe(`content-generation-${data.pipeline_id}`);

        channel.bind('progress', (update) => {
            console.log(`Update: ${update.type} - ${update.message || update.progress}%`);
        });

        channel.bind('generation-completed', (result) => {
            console.log('Content generated successfully!', result);
            pusher.unsubscribe(`content-generation-${data.pipeline_id}`);
        });

        channel.bind('error', (error) => {
            console.error('Generation error:', error);
        });

    } catch (error) {
        console.error('Error:', error);
    }
}

// Run the example
generateContent();
```

### cURL Examples

**Generate Content**:
```bash
curl -X POST "http://localhost:8008/api/v1/content/generate" \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Mathematics",
    "grade_level": "6-8",
    "content_type": "lesson",
    "learning_objectives": [
      "Solve linear equations",
      "Graph linear functions"
    ],
    "difficulty_level": "medium",
    "duration_minutes": 45
  }'
```

**Check Status**:
```bash
curl -X GET "http://localhost:8008/api/v1/content/status/pipeline-id" \
  -H "Authorization: Bearer your-jwt-token"
```

**Validate Content**:
```bash
curl -X POST "http://localhost:8008/api/v1/content/validate" \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "content": {"title": "Test Lesson", "description": "Sample content"},
    "content_type": "lesson",
    "target_age": 12
  }'
```

## Best Practices

### Content Generation
1. **Specific Learning Objectives**: Provide clear, measurable learning objectives
2. **Appropriate Difficulty**: Match difficulty to target grade level
3. **Realistic Duration**: Allow adequate time for content complexity
4. **Roblox Requirements**: Specify technical requirements upfront

### Real-time Monitoring
1. **Use Pusher**: Prefer Pusher Channels over polling for real-time updates
2. **Automatic Reconnection**: Pusher handles reconnection automatically
3. **Error Handling**: Handle Pusher connection errors gracefully
4. **Channel Management**: Properly subscribe/unsubscribe from channels

### Validation
1. **Early Validation**: Validate content during generation process
2. **Target Age**: Always specify target age for accurate validation
3. **Multiple Categories**: Run validation across all relevant categories
4. **Address Issues**: Fix critical issues before deployment

### Performance
1. **Pagination**: Use pagination for history and large result sets
2. **Filtering**: Apply filters to reduce data transfer
3. **Caching**: Cache content locally when appropriate
4. **Rate Limits**: Respect rate limits to avoid throttling

### Security
1. **JWT Expiration**: Handle token expiration gracefully
2. **Input Validation**: Validate all inputs client-side
3. **Error Information**: Don't expose sensitive information in errors
4. **Content Access**: Verify user permissions for content access
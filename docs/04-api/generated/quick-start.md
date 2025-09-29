# Quick Start Guide

## Overview

Get up and running with the ToolBoxAI API in just a few steps. This guide will walk you through authentication, making your first API call, and exploring key features.

## Prerequisites

- **Base URL**: Choose your environment
  - Development: `http://localhost:8009`
  - Staging: `https://staging-api.toolboxai.com`
  - Production: `https://api.toolboxai.com`

## Step 1: Authentication

### Get Your JWT Token

Use one of the demo accounts to get started quickly:

**Teacher Account (Recommended for testing):**
- Email: `jane.smith@school.edu`
- Password: `Teacher123!`

**Student Account:**
- Email: `alex.johnson@student.edu`
- Password: `Student123!`

**Admin Account:**
- Email: `admin@toolboxai.com`
- Password: `Admin123!`

### Login Request

```bash
curl -X POST http://localhost:8009/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "jane.smith@school.edu",
    "password": "Teacher123!"
  }'
```

### Response

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "role": "teacher",
  "user": {
    "id": "123",
    "username": "jane_smith",
    "email": "jane.smith@school.edu",
    "displayName": "Jane Smith",
    "role": "teacher"
  }
}
```

**Save the `access_token` - you'll need it for all subsequent requests!**

## Step 2: Make Your First API Call

### Get Your Classes

```bash
curl -X GET http://localhost:8009/api/v1/classes \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"
```

### Expected Response

```json
{
  "success": true,
  "data": [
    {
      "id": "class_123",
      "name": "7th Grade Science",
      "subject": "Science",
      "grade_level": 7,
      "teacher": {
        "id": "teacher_456",
        "name": "Ms. Johnson"
      },
      "student_count": 25,
      "status": "active"
    }
  ],
  "total": 12
}
```

## Step 3: Generate Educational Content

### Start Content Generation

```bash
curl -X POST http://localhost:8009/api/v1/content/generate \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Science",
    "grade_level": "6-8",
    "content_type": "interactive_lesson",
    "learning_objectives": [
      "Understand the solar system",
      "Learn about planetary orbits"
    ],
    "environment_theme": "space_station",
    "difficulty": "medium",
    "duration_minutes": 30,
    "include_quiz": true
  }'
```

### Response

```json
{
  "success": true,
  "data": {
    "session_id": "gen_abc123",
    "content_id": "content_456",
    "status": "generating",
    "progress": {
      "stage": "content_analysis",
      "progress_percent": 10,
      "estimated_completion": "2025-01-21T10:03:00Z"
    },
    "websocket_url": "ws://localhost:8009/ws/content/gen_abc123"
  },
  "message": "Content generation started"
}
```

### Check Generation Status

```bash
curl -X GET http://localhost:8009/api/v1/content/generation/gen_abc123/status \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"
```

## Step 4: Real-time Updates (Optional)

### WebSocket Connection for Live Progress

```javascript
// Connect to WebSocket for real-time updates
const ws = new WebSocket('ws://localhost:8009/ws/content/gen_abc123');

ws.onopen = function() {
  console.log('Connected to content generation stream');

  // Authenticate WebSocket
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'Bearer YOUR_JWT_TOKEN_HERE'
  }));
};

ws.onmessage = function(event) {
  const message = JSON.parse(event.data);

  if (message.type === 'progress_update') {
    console.log(`Progress: ${message.data.progress_percent}%`);
    console.log(`Stage: ${message.data.stage}`);
    console.log(`Message: ${message.data.message}`);
  }

  if (message.type === 'generation_complete') {
    console.log('Content generation completed!');
    console.log('Content ID:', message.data.content_id);
    ws.close();
  }
};
```

## Step 5: Explore More Features

### Create a Class

```bash
curl -X POST http://localhost:8009/api/v1/classes \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "8th Grade Physics",
    "subject": "Science",
    "grade_level": 8,
    "description": "Introduction to physics with Roblox simulations",
    "capacity": 25
  }'
```

### Start AI Chat Session

```bash
curl -X POST http://localhost:8009/api/v1/ai-chat/conversation/start \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "initial_message": "Help me create a lesson plan about marine biology",
    "context": {
      "subject": "Science",
      "grade_level": "9-12",
      "lesson_duration": 50
    },
    "agent_type": "educational_assistant"
  }'
```

### Get Analytics Dashboard

```bash
curl -X GET "http://localhost:8009/api/v1/analytics/dashboard?time_range=30d" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"
```

## Code Examples

### JavaScript/Node.js

```javascript
const API_BASE = 'http://localhost:8009';
let authToken = null;

// Login function
async function login(email, password) {
  const response = await fetch(`${API_BASE}/api/v1/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ email, password })
  });

  const data = await response.json();
  if (data.access_token) {
    authToken = data.access_token;
    console.log('Logged in successfully as:', data.user.displayName);
    return data;
  }
  throw new Error('Login failed');
}

// Make authenticated API calls
async function apiCall(endpoint, options = {}) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json',
      ...options.headers
    }
  });

  return response.json();
}

// Generate content
async function generateContent(contentRequest) {
  return apiCall('/api/v1/content/generate', {
    method: 'POST',
    body: JSON.stringify(contentRequest)
  });
}

// Usage
async function main() {
  try {
    await login('jane.smith@school.edu', 'Teacher123!');

    const classes = await apiCall('/api/v1/classes');
    console.log('Classes:', classes.data.length);

    const generation = await generateContent({
      subject: 'Science',
      grade_level: '6-8',
      content_type: 'interactive_lesson',
      learning_objectives: ['Understand photosynthesis'],
      difficulty: 'medium'
    });
    console.log('Generation started:', generation.data.session_id);

  } catch (error) {
    console.error('Error:', error);
  }
}

main();
```

### Python

```python
import requests
import json

class ToolBoxAIClient:
    def __init__(self, base_url="http://localhost:8009"):
        self.base_url = base_url
        self.auth_token = None

    def login(self, email, password):
        """Authenticate and get JWT token"""
        response = requests.post(f"{self.base_url}/api/v1/auth/login", json={
            "email": email,
            "password": password
        })

        if response.status_code == 200:
            data = response.json()
            self.auth_token = data["access_token"]
            print(f"Logged in as: {data['user']['displayName']}")
            return data
        else:
            raise Exception(f"Login failed: {response.text}")

    def _headers(self):
        """Get headers with authentication"""
        if not self.auth_token:
            raise Exception("Not authenticated. Call login() first.")

        return {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }

    def get_classes(self):
        """Get user's classes"""
        response = requests.get(
            f"{self.base_url}/api/v1/classes",
            headers=self._headers()
        )
        return response.json()

    def generate_content(self, content_request):
        """Start content generation"""
        response = requests.post(
            f"{self.base_url}/api/v1/content/generate",
            headers=self._headers(),
            json=content_request
        )
        return response.json()

    def get_generation_status(self, session_id):
        """Check content generation status"""
        response = requests.get(
            f"{self.base_url}/api/v1/content/generation/{session_id}/status",
            headers=self._headers()
        )
        return response.json()

# Usage example
if __name__ == "__main__":
    client = ToolBoxAIClient()

    # Login
    client.login("jane.smith@school.edu", "Teacher123!")

    # Get classes
    classes = client.get_classes()
    print(f"Found {len(classes['data'])} classes")

    # Generate content
    generation = client.generate_content({
        "subject": "Science",
        "grade_level": "6-8",
        "content_type": "interactive_lesson",
        "learning_objectives": ["Understand the water cycle"],
        "environment_theme": "natural_environment",
        "difficulty": "medium",
        "duration_minutes": 30,
        "include_quiz": True
    })

    print(f"Generation started: {generation['data']['session_id']}")

    # Check status
    import time
    session_id = generation['data']['session_id']

    while True:
        status = client.get_generation_status(session_id)
        progress = status['data']['progress']['progress_percent']
        print(f"Progress: {progress}%")

        if status['data']['status'] == 'completed':
            print("Generation completed!")
            break
        elif status['data']['status'] == 'failed':
            print("Generation failed!")
            break

        time.sleep(2)  # Wait 2 seconds before checking again
```

### cURL Script

Save this as `toolboxai-test.sh`:

```bash
#!/bin/bash

BASE_URL="http://localhost:8009"
EMAIL="jane.smith@school.edu"
PASSWORD="Teacher123!"

# Login and extract token
echo "Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')

if [ "$TOKEN" = "null" ]; then
  echo "Login failed!"
  echo $LOGIN_RESPONSE
  exit 1
fi

echo "Login successful! Token: ${TOKEN:0:20}..."

# Get classes
echo -e "\nFetching classes..."
curl -s -X GET "$BASE_URL/api/v1/classes" \
  -H "Authorization: Bearer $TOKEN" | jq '.data | length' | \
  xargs echo "Found classes:"

# Generate content
echo -e "\nStarting content generation..."
GENERATION_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/content/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Science",
    "grade_level": "6-8",
    "content_type": "interactive_lesson",
    "learning_objectives": ["Understand ecosystems"],
    "difficulty": "medium",
    "duration_minutes": 30
  }')

SESSION_ID=$(echo $GENERATION_RESPONSE | jq -r '.data.session_id')
echo "Generation session: $SESSION_ID"

# Check status periodically
echo -e "\nMonitoring progress..."
while true; do
  STATUS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/content/generation/$SESSION_ID/status" \
    -H "Authorization: Bearer $TOKEN")

  STATUS=$(echo $STATUS_RESPONSE | jq -r '.data.status')
  PROGRESS=$(echo $STATUS_RESPONSE | jq -r '.data.progress.progress_percent')

  echo "Status: $STATUS, Progress: $PROGRESS%"

  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
    break
  fi

  sleep 3
done

echo "Content generation finished!"
```

Make it executable and run:
```bash
chmod +x toolboxai-test.sh
./toolboxai-test.sh
```

## Testing with Postman

1. **Import Collection**: Import the `toolboxai-postman.json` collection
2. **Set Environment Variables**:
   - `base_url`: `http://localhost:8009`
   - `user_email`: `jane.smith@school.edu`
   - `user_password`: `Teacher123!`
3. **Run Login Request**: This will automatically set the JWT token
4. **Explore Endpoints**: All other requests will use the stored token

## Common Use Cases

### 1. Content Creation Workflow

```javascript
// Complete workflow for creating educational content
async function contentCreationWorkflow() {
  // 1. Login
  await login('jane.smith@school.edu', 'Teacher123!');

  // 2. Create or select a class
  const classes = await apiCall('/api/v1/classes');
  const classId = classes.data[0]?.id;

  // 3. Generate content
  const generation = await generateContent({
    subject: 'Science',
    grade_level: '7',
    content_type: 'interactive_lesson',
    learning_objectives: ['Understand chemical reactions'],
    environment_theme: 'laboratory',
    difficulty: 'medium'
  });

  // 4. Monitor progress via WebSocket
  const ws = new WebSocket(generation.data.websocket_url);
  ws.onopen = () => {
    ws.send(JSON.stringify({
      type: 'auth',
      token: `Bearer ${authToken}`
    }));
  };

  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    if (message.type === 'generation_complete') {
      console.log('Content ready!', message.data.content_id);
      ws.close();
    }
  };
}
```

### 2. Student Progress Monitoring

```javascript
async function monitorStudentProgress(classId) {
  // Get class analytics
  const analytics = await apiCall(`/api/v1/analytics/dashboard?time_range=30d`);

  // Get class details with student progress
  const classDetails = await apiCall(`/api/v1/classes/${classId}`);

  console.log('Class Performance:', {
    averageScore: analytics.data.performance.average_quiz_score,
    completionRate: analytics.data.engagement.completion_rate,
    activeStudents: classDetails.data.student_count
  });
}
```

### 3. Roblox Integration

```javascript
async function setupRobloxIntegration() {
  // Initiate OAuth flow
  const authData = await apiCall('/api/v1/roblox/auth/initiate', {
    method: 'POST',
    body: JSON.stringify({
      additional_scopes: ['universe-messaging-service:publish']
    })
  });

  console.log('Visit this URL to authorize:', authData.authorization_url);

  // After user authorizes, generate environment
  const environment = await apiCall('/api/v1/roblox-environment/generate', {
    method: 'POST',
    body: JSON.stringify({
      content_id: 'content_123',
      environment_type: 'space_station',
      size: 'medium'
    })
  });

  console.log('Environment generating:', environment.data.environment_id);
}
```

## Next Steps

1. **Explore the API Reference**: Check out the [complete API documentation](./api-reference.md)
2. **Set Up WebSockets**: Follow the [WebSocket guide](./websocket.md) for real-time features
3. **Review Rate Limits**: Understand usage limits in the [rate limiting guide](./rate-limiting.md)
4. **Handle Errors**: Learn about error codes in the [error reference](./error-codes.md)
5. **Production Setup**: Configure authentication and security for production use

## Need Help?

- **API Issues**: Check the health endpoint: `GET /health`
- **Authentication Problems**: Verify JWT token hasn't expired
- **WebSocket Issues**: Test with the native endpoint: `ws://localhost:8009/ws/native`
- **Rate Limiting**: Check response headers for rate limit information

## Demo Data

The API includes demo data for testing:

- **3 Demo Users**: Admin, Teacher, Student roles
- **Sample Classes**: Pre-created classes with students
- **Content Templates**: Example lessons and quizzes
- **Roblox Environments**: Sample 3D environments

Start experimenting and building amazing educational experiences! 🚀
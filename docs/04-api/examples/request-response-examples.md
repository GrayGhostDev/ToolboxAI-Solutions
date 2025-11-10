# API Request/Response Examples

## Overview

This document provides comprehensive examples of API requests and responses for the ToolBoxAI educational platform. All examples include cURL, Python, and JavaScript implementations.

## Authentication Examples

### Login Request
**Endpoint:** `POST /auth/login`

#### cURL
```bash
curl -X POST "http://127.0.0.1:8009/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "teacher@school.edu",
    "password": "SecurePassword123!"
  }'
```

#### Python
```python
import requests

response = requests.post(
    'http://127.0.0.1:8009/auth/login',
    json={
        'username': 'teacher@school.edu',
        'password': 'SecurePassword123!'
    }
)

if response.status_code == 200:
    auth_data = response.json()
    access_token = auth_data['access_token']
    print(f"Login successful. Token: {access_token[:20]}...")
else:
    error_data = response.json()
    print(f"Login failed: {error_data['message']}")
```

#### JavaScript/TypeScript
```typescript
const loginUser = async (username: string, password: string) => {
  try {
    const response = await fetch('http://127.0.0.1:8009/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    localStorage.setItem('auth_token', data.access_token);
    return data;
  } catch (error) {
    console.error('Login failed:', error);
    throw error;
  }
};

// Usage
loginUser('teacher@school.edu', 'SecurePassword123!')
  .then(data => console.log('Login successful:', data.user))
  .catch(error => console.error('Login error:', error));
```

#### Success Response
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZWFjaGVyQHNjaG9vbC5lZHUiLCJyb2xlIjoidGVhY2hlciIsImV4cCI6MTcwNzM5NjAwMH0.signature_here",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.refresh_payload.refresh_signature",
  "user": {
    "id": "teacher_001",
    "username": "teacher@school.edu",
    "email": "teacher@school.edu",
    "role": "teacher",
    "first_name": "Jane",
    "last_name": "Smith",
    "school": "Lincoln Middle School",
    "department": "Mathematics"
  }
}
```

## Content Generation Examples

### Generate Educational Content
**Endpoint:** `POST /api/v1/content/generate`

#### Complete Content Generation Request

##### cURL
```bash
curl -X POST "http://127.0.0.1:8009/api/v1/content/generate" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Mathematics",
    "grade_level": 7,
    "learning_objectives": [
      {
        "title": "Solve linear equations",
        "description": "Students will solve equations of the form ax + b = c",
        "bloom_level": "Apply",
        "measurable": true
      },
      {
        "title": "Graph linear relationships",
        "description": "Students will create graphs from linear equations",
        "bloom_level": "Create",
        "measurable": true
      }
    ],
    "environment_type": "classroom",
    "terrain_size": "medium",
    "include_quiz": true,
    "difficulty_level": "medium",
    "duration_minutes": 45,
    "max_students": 25,
    "accessibility_features": true,
    "custom_requirements": "Include visual aids for algebra concepts"
  }'
```

##### Python
```python
import requests
import json

def generate_content(token, content_request):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    response = requests.post(
        'http://127.0.0.1:8009/api/v1/content/generate',
        headers=headers,
        json=content_request
    )

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Content generation failed: {response.json()}")

# Example usage
content_request = {
    "subject": "Mathematics",
    "grade_level": 7,
    "learning_objectives": [
        {
            "title": "Solve linear equations",
            "description": "Students will solve equations of the form ax + b = c",
            "bloom_level": "Apply",
            "measurable": True
        }
    ],
    "environment_type": "classroom",
    "include_quiz": True,
    "difficulty_level": "medium",
    "duration_minutes": 45
}

try:
    result = generate_content("your_token_here", content_request)
    print(f"Content generated successfully!")
    print(f"Content ID: {result['content_id']}")
    print(f"Estimated build time: {result['estimated_build_time']} minutes")
except Exception as e:
    print(f"Error: {e}")
```

##### JavaScript/TypeScript
```typescript
interface ContentRequest {
  subject: string;
  grade_level: number;
  learning_objectives: Array<{
    title: string;
    description: string;
    bloom_level?: string;
    measurable?: boolean;
  }>;
  environment_type: string;
  terrain_size?: string;
  include_quiz?: boolean;
  difficulty_level?: string;
  duration_minutes?: number;
  max_students?: number;
  accessibility_features?: boolean;
  custom_requirements?: string;
}

const generateContent = async (token: string, request: ContentRequest) => {
  const response = await fetch('http://127.0.0.1:8009/api/v1/content/generate', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(`Content generation failed: ${error.message}`);
  }

  return response.json();
};

// Example usage
const contentRequest: ContentRequest = {
  subject: "Mathematics",
  grade_level: 7,
  learning_objectives: [
    {
      title: "Solve linear equations",
      description: "Students will solve equations of the form ax + b = c",
      bloom_level: "Apply",
      measurable: true
    }
  ],
  environment_type: "classroom",
  include_quiz: true,
  difficulty_level: "medium",
  duration_minutes: 45
};

generateContent("your_token_here", contentRequest)
  .then(result => {
    console.log('Content generated:', result.content_id);
    console.log('Scripts generated:', result.scripts.length);
  })
  .catch(error => console.error('Generation failed:', error));
```

#### Success Response
```json
{
  "success": true,
  "message": "Content generated successfully",
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_abc123",
  "content_id": "content_def456",
  "content": {
    "lesson_plan": {
      "title": "Linear Equations in Virtual Classroom",
      "description": "Interactive lesson teaching 7th grade students to solve linear equations",
      "duration_minutes": 45,
      "activities": [
        {
          "name": "Introduction to Variables",
          "duration": 10,
          "type": "tutorial",
          "description": "Visual introduction to algebraic variables using 3D objects"
        },
        {
          "name": "Equation Solving Practice",
          "duration": 25,
          "type": "interactive",
          "description": "Students solve equations by manipulating virtual blocks"
        },
        {
          "name": "Assessment Quiz",
          "duration": 10,
          "type": "assessment",
          "description": "Quick quiz to test understanding"
        }
      ],
      "learning_objectives": [
        {
          "title": "Solve linear equations",
          "assessment_method": "quiz_score >= 70%"
        }
      ]
    },
    "roblox_environment": {
      "theme": "Modern Classroom",
      "capacity": 25,
      "interactive_elements": [
        "Equation Balance Scale",
        "Variable Manipulation Board",
        "Progress Tracking Display"
      ]
    }
  },
  "scripts": [
    {
      "name": "EquationTutorScript",
      "content": "-- Linear Equation Tutorial Script\nlocal Players = game:GetService('Players')\nlocal TweenService = game:GetService('TweenService')\n\n-- Initialize equation system\nlocal EquationManager = {}\n\nfunction EquationManager:CreateEquation(a, b, c)\n    -- Create visual equation: ax + b = c\n    local equation = {\n        coefficient = a,\n        constant = b,\n        result = c,\n        solution = (c - b) / a\n    }\n    \n    return equation\nend\n\nfunction EquationManager:SolveStep(equation, step)\n    -- Guide student through solving steps\n    if step == 1 then\n        return string.format('Subtract %d from both sides', equation.constant)\n    elseif step == 2 then\n        return string.format('Divide both sides by %d', equation.coefficient)\n    end\nend\n\n-- Export for use by other scripts\nreturn EquationManager",
      "script_type": "server",
      "dependencies": ["PlayerService", "UIService"],
      "description": "Core logic for equation tutorial system"
    },
    {
      "name": "StudentProgressTracker",
      "content": "-- Student Progress Tracking\nlocal Players = game:GetService('Players')\nlocal DataStoreService = game:GetService('DataStoreService')\n\nlocal ProgressStore = DataStoreService:GetDataStore('StudentProgress')\n\nlocal ProgressTracker = {}\n\nfunction ProgressTracker:UpdateProgress(player, lesson, score)\n    local userId = player.UserId\n    local progressData = {\n        lesson_id = lesson,\n        score = score,\n        timestamp = os.time(),\n        attempts = 1\n    }\n    \n    -- Save to DataStore\n    local success, error = pcall(function()\n        ProgressStore:SetAsync(userId .. '_' .. lesson, progressData)\n    end)\n    \n    if success then\n        -- Trigger progress update event\n        game.ReplicatedStorage.ProgressUpdated:FireClient(player, progressData)\n    end\nend\n\nreturn ProgressTracker",
      "script_type": "server",
      "dependencies": ["DataStoreService"],
      "description": "Tracks and saves student progress"
    }
  ],
  "terrain": {
    "material": "Grass",
    "size": "medium",
    "features": ["classroom_building", "outdoor_garden", "playground"],
    "biome": "temperate",
    "elevation_map": {
      "classroom_area": 0,
      "garden_area": -2,
      "playground_area": 1
    }
  },
  "game_mechanics": {
    "movement_enabled": true,
    "chat_enabled": true,
    "collision_detection": true,
    "gravity_enabled": true,
    "respawn_enabled": true,
    "team_mode": false
  },
  "estimated_build_time": 35,
  "resource_requirements": {
    "memory_mb": 256,
    "cpu_cores": 1,
    "storage_mb": 45
  }
}
```

### Generate Quiz
**Endpoint:** `POST /generate_quiz`

#### cURL
```bash
curl -X POST "http://127.0.0.1:8009/generate_quiz?subject=Mathematics&topic=Linear%20Equations&difficulty=medium&num_questions=5&grade_level=7" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

#### Python
```python
def generate_quiz(token, subject, topic, difficulty="medium", num_questions=5, grade_level=7):
    headers = {'Authorization': f'Bearer {token}'}
    params = {
        'subject': subject,
        'topic': topic,
        'difficulty': difficulty,
        'num_questions': num_questions,
        'grade_level': grade_level
    }

    response = requests.post(
        'http://127.0.0.1:8009/generate_quiz',
        headers=headers,
        params=params
    )

    return response.json()

# Example usage
quiz = generate_quiz(
    token="your_token",
    subject="Mathematics",
    topic="Linear Equations",
    difficulty="medium",
    num_questions=5,
    grade_level=7
)
```

#### JavaScript
```javascript
const generateQuiz = async (token, params) => {
  const queryString = new URLSearchParams(params).toString();
  const response = await fetch(`http://127.0.0.1:8009/generate_quiz?${queryString}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  return response.json();
};

// Usage
generateQuiz("your_token", {
  subject: "Mathematics",
  topic: "Linear Equations",
  difficulty: "medium",
  num_questions: 5,
  grade_level: 7
});
```

## Dashboard Examples

### Get Student Dashboard
**Endpoint:** `GET /dashboard/student`

#### cURL
```bash
curl -X GET "http://127.0.0.1:8009/dashboard/student" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

#### Python
```python
def get_student_dashboard(token):
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(
        'http://127.0.0.1:8009/dashboard/student',
        headers=headers
    )
    return response.json()

dashboard_data = get_student_dashboard("your_token")
print(f"Current XP: {dashboard_data['gamification']['total_xp']}")
print(f"Assignments due: {len(dashboard_data['assignments']['due_soon'])}")
```

#### JavaScript
```javascript
const getStudentDashboard = async (token) => {
  const response = await fetch('http://127.0.0.1:8009/dashboard/student', {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  return response.json();
};

getStudentDashboard("your_token").then(data => {
  console.log(`Level: ${data.gamification.level}`);
  console.log(`Current lesson: ${data.current_lesson?.title}`);
});
```

## Real-time Communication Examples

### Pusher Authentication
**Endpoint:** `POST /pusher/auth`

#### JavaScript Pusher Integration
```javascript
import Pusher from 'pusher-js';

const initializePusher = (token) => {
  const pusher = new Pusher(process.env.VITE_PUSHER_KEY, {
    cluster: process.env.VITE_PUSHER_CLUSTER,
    authEndpoint: 'http://127.0.0.1:8009/pusher/auth',
    auth: {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  });

  // Subscribe to content generation updates
  const contentChannel = pusher.subscribe('content-generation');
  contentChannel.bind('generation_started', (data) => {
    console.log('Content generation started:', data.content_id);
    showProgressBar(data.content_id);
  });

  contentChannel.bind('progress_update', (data) => {
    updateProgressBar(data.content_id, data.progress);
  });

  contentChannel.bind('generation_completed', (data) => {
    hideProgressBar(data.content_id);
    showSuccessMessage('Content ready!', data.content_id);
  });

  // Subscribe to user notifications
  const userChannel = pusher.subscribe(`private-user-${userId}`);
  userChannel.bind('personal_notification', (data) => {
    showNotification(data);
  });

  return pusher;
};
```

#### Python Pusher Integration
```python
import pusher

pusher_client = pusher.Pusher(
    app_id='your_app_id',
    key='your_key',
    secret='your_secret',
    cluster='your_cluster',
    ssl=True
)

def notify_user(user_id, notification):
    pusher_client.trigger(
        f'private-user-{user_id}',
        'personal_notification',
        notification
    )

# Example: Notify user of new grade
notify_user('user_123', {
    'type': 'grade',
    'title': 'New Grade Posted',
    'message': 'Your math quiz has been graded',
    'data': {
        'assignment_id': 'assign_456',
        'grade': '85%',
        'feedback': 'Great work!'
    }
})
```

## Roblox Integration Examples

### Deploy Content to Roblox
**Endpoint:** `POST /api/v1/roblox/deploy/{content_id}`

#### Python
```python
def deploy_to_roblox(token, content_id, place_id):
    headers = {'Authorization': f'Bearer {token}'}
    payload = {
        'place_id': place_id,
        'deployment_options': {
            'backup_existing': True,
            'test_mode': False,
            'publish_public': False
        },
        'target_environment': 'development'
    }

    response = requests.post(
        f'http://127.0.0.1:8009/api/v1/roblox/deploy/{content_id}',
        headers=headers,
        json=payload
    )

    if response.status_code == 200:
        deployment = response.json()
        print(f"Deployment started: {deployment['deployment_id']}")
        print(f"Estimated completion: {deployment['estimated_completion']}")
        return deployment
    else:
        raise Exception(f"Deployment failed: {response.json()}")

# Example usage
try:
    deployment = deploy_to_roblox(
        token="your_token",
        content_id="content_123",
        place_id="987654321"
    )
    print(f"Roblox place URL: {deployment['roblox_details']['place_url']}")
except Exception as e:
    print(f"Deployment error: {e}")
```

#### JavaScript
```javascript
const deployToRoblox = async (token, contentId, placeId) => {
  const response = await fetch(`http://127.0.0.1:8009/api/v1/roblox/deploy/${contentId}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      place_id: placeId,
      deployment_options: {
        backup_existing: true,
        test_mode: false
      },
      target_environment: 'development'
    }),
  });

  if (!response.ok) {
    throw new Error(`Deployment failed: ${response.statusText}`);
  }

  return response.json();
};

// Usage with progress tracking
deployToRoblox("your_token", "content_123", "987654321")
  .then(deployment => {
    console.log('Deployment started:', deployment.deployment_id);

    // Monitor progress via Pusher
    const channel = pusher.subscribe('content-generation');
    channel.bind('deployment_progress', (data) => {
      if (data.deployment_id === deployment.deployment_id) {
        console.log(`Progress: ${data.progress}%`);
      }
    });
  })
  .catch(error => console.error('Deployment failed:', error));
```

## Error Handling Examples

### Handling Authentication Errors
```python
def handle_auth_error(response):
    if response.status_code == 401:
        error_data = response.json()
        if error_data.get('code') == 'EXPIRED_TOKEN':
            # Attempt token refresh
            new_token = refresh_token()
            return new_token
        elif error_data.get('code') == 'INVALID_TOKEN':
            # Redirect to login
            redirect_to_login()
    return None

def make_authenticated_request(url, token, **kwargs):
    headers = kwargs.pop('headers', {})
    headers['Authorization'] = f'Bearer {token}'

    response = requests.get(url, headers=headers, **kwargs)

    if response.status_code == 401:
        new_token = handle_auth_error(response)
        if new_token:
            headers['Authorization'] = f'Bearer {new_token}'
            response = requests.get(url, headers=headers, **kwargs)

    return response
```

### Handling Rate Limits
```javascript
const makeRequestWithRetry = async (url, options, maxRetries = 3) => {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(url, options);

      if (response.status === 429) {
        const errorData = await response.json();
        const retryAfter = errorData.details?.retry_after || 60;

        if (attempt < maxRetries) {
          console.log(`Rate limited. Retrying after ${retryAfter} seconds...`);
          await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
          continue;
        }
      }

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return response.json();
    } catch (error) {
      if (attempt === maxRetries) {
        throw error;
      }

      // Exponential backoff for network errors
      const delay = Math.pow(2, attempt) * 1000;
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
};
```

## Batch Operations Examples

### Bulk Content Generation
```python
def generate_multiple_content(token, content_requests):
    results = []
    headers = {'Authorization': f'Bearer {token}'}

    for i, request in enumerate(content_requests):
        try:
            print(f"Generating content {i+1}/{len(content_requests)}: {request['subject']}")

            response = requests.post(
                'http://127.0.0.1:8009/api/v1/content/generate',
                headers=headers,
                json=request
            )

            if response.status_code == 200:
                result = response.json()
                results.append({
                    'request_index': i,
                    'content_id': result['content_id'],
                    'success': True
                })
                print(f"✓ Generated: {result['content_id']}")
            else:
                error = response.json()
                results.append({
                    'request_index': i,
                    'error': error['message'],
                    'success': False
                })
                print(f"✗ Failed: {error['message']}")

        except Exception as e:
            results.append({
                'request_index': i,
                'error': str(e),
                'success': False
            })
            print(f"✗ Exception: {e}")

        # Rate limiting: wait between requests
        time.sleep(2)

    return results

# Example: Generate content for multiple subjects
content_requests = [
    {
        "subject": "Mathematics",
        "grade_level": 7,
        "learning_objectives": [{"title": "Linear Equations"}],
        "environment_type": "classroom"
    },
    {
        "subject": "Science",
        "grade_level": 7,
        "learning_objectives": [{"title": "States of Matter"}],
        "environment_type": "laboratory"
    }
]

results = generate_multiple_content("your_token", content_requests)
successful = [r for r in results if r['success']]
print(f"Successfully generated {len(successful)}/{len(content_requests)} content items")
```

## WebSocket Examples

### Real-time Content Generation Monitoring
```javascript
class ContentGenerationMonitor {
  constructor(token) {
    this.token = token;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  connect() {
    this.ws = new WebSocket('ws://127.0.0.1:8009/ws/content');

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;

      // Authenticate
      this.ws.send(JSON.stringify({
        type: 'auth',
        token: this.token
      }));
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.reconnect();
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  handleMessage(data) {
    switch (data.type) {
      case 'generation_started':
        this.onGenerationStarted(data);
        break;
      case 'progress_update':
        this.onProgressUpdate(data);
        break;
      case 'generation_completed':
        this.onGenerationCompleted(data);
        break;
      case 'generation_failed':
        this.onGenerationFailed(data);
        break;
    }
  }

  onGenerationStarted(data) {
    console.log(`Content generation started: ${data.content_id}`);
    this.showProgressDialog(data.content_id);
  }

  onProgressUpdate(data) {
    console.log(`Progress: ${data.progress}% - ${data.stage}`);
    this.updateProgress(data.content_id, data.progress, data.stage);
  }

  onGenerationCompleted(data) {
    console.log(`Content generation completed: ${data.content_id}`);
    this.hideProgressDialog(data.content_id);
    this.showSuccessMessage(data);
  }

  onGenerationFailed(data) {
    console.error(`Content generation failed: ${data.error}`);
    this.hideProgressDialog(data.content_id);
    this.showErrorMessage(data.error);
  }

  reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.pow(2, this.reconnectAttempts) * 1000;

      console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
      setTimeout(() => this.connect(), delay);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  // UI update methods
  showProgressDialog(contentId) {
    // Implementation for showing progress UI
  }

  updateProgress(contentId, progress, stage) {
    // Implementation for updating progress UI
  }

  hideProgressDialog(contentId) {
    // Implementation for hiding progress UI
  }

  showSuccessMessage(data) {
    // Implementation for showing success notification
  }

  showErrorMessage(error) {
    // Implementation for showing error notification
  }
}

// Usage
const monitor = new ContentGenerationMonitor('your_token');
monitor.connect();
```

These examples provide comprehensive coverage of the major API endpoints and common integration patterns for the ToolBoxAI educational platform. Each example includes proper error handling, authentication, and best practices for production use.

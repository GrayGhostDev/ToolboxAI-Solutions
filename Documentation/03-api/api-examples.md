# API Code Examples

This document provides practical code examples for interacting with the ToolboxAI API in various programming languages.

## Table of Contents

1. [Authentication](#authentication)
2. [Content Generation](#content-generation)
3. [Quiz Management](#quiz-management)
4. [Progress Tracking](#progress-tracking)
5. [WebSocket Connections](#websocket-connections)
6. [Error Handling](#error-handling)

## Authentication

### Register a New User

#### Python

```python
import httpx
import asyncio

async def register_user():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8008/api/auth/register",
            json={
                "email": "student@example.com",
                "password": "SecurePassword123!",
                "name": "Jane Smith",
                "role": "student",
                "grade_level": 7
            }
        )

        if response.status_code == 201:
            user = response.json()
            print(f"User created: {user['id']}")
            return user
        else:
            print(f"Error: {response.json()}")
            return None

# Run the async function
user = asyncio.run(register_user())
```text
#### JavaScript/TypeScript

```typescript
async function registerUser() {
  try {
    const response = await fetch('http://localhost:8008/api/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: 'student@example.com',
        password: 'SecurePassword123!',
        name: 'Jane Smith',
        role: 'student',
        grade_level: 7,
      }),
    })

    if (response.ok) {
      const user = await response.json()
      console.log('User created:', user.id)
      return user
    } else {
      const error = await response.json()
      console.error('Error:', error)
      return null
    }
  } catch (error) {
    console.error('Network error:', error)
    return null
  }
}

// Usage
const user = await registerUser()
```text
#### cURL

```bash
curl -X POST http://localhost:8008/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "SecurePassword123!",
    "name": "Jane Smith",
    "role": "student",
    "grade_level": 7
  }'
```text
### Login and Get Token

#### Python

```python
import httpx
import asyncio
from typing import Optional, Dict

class AuthManager:
    def __init__(self, base_url: str = "http://localhost:8008"):
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None

    async def login(self, email: str, password: str) -> bool:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/auth/login",
                json={"email": email, "password": password}
            )

            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                self.refresh_token = data["refresh_token"]
                return True
            return False

    async def refresh_access_token(self) -> bool:
        if not self.refresh_token:
            return False

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/auth/refresh",
                headers=self.get_headers(),
                json={"refresh_token": self.refresh_token}
            )

            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                return True
            return False

    def get_headers(self) -> Dict[str, str]:
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}

# Usage
async def main():
    auth = AuthManager()
    if await auth.login("student@example.com", "SecurePassword123!"):
        print("Login successful!")
        print(f"Token: {auth.access_token[:20]}...")
    else:
        print("Login failed!")

asyncio.run(main())
```text
#### JavaScript/TypeScript

```typescript
class AuthManager {
  private accessToken: string | null = null
  private refreshToken: string | null = null
  private baseUrl: string

  constructor(baseUrl: string = 'http://localhost:8008') {
    this.baseUrl = baseUrl
  }

  async login(email: string, password: string): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      })

      if (response.ok) {
        const data = await response.json()
        this.accessToken = data.access_token
        this.refreshToken = data.refresh_token

        // Store tokens in localStorage for persistence
        localStorage.setItem('access_token', this.accessToken)
        localStorage.setItem('refresh_token', this.refreshToken)

        return true
      }
      return false
    } catch (error) {
      console.error('Login error:', error)
      return false
    }
  }

  async refreshAccessToken(): Promise<boolean> {
    if (!this.refreshToken) return false

    try {
      const response = await fetch(`${this.baseUrl}/api/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...this.getHeaders(),
        },
        body: JSON.stringify({ refresh_token: this.refreshToken }),
      })

      if (response.ok) {
        const data = await response.json()
        this.accessToken = data.access_token
        localStorage.setItem('access_token', this.accessToken)
        return true
      }
      return false
    } catch (error) {
      console.error('Token refresh error:', error)
      return false
    }
  }

  getHeaders(): Record<string, string> {
    if (this.accessToken) {
      return { Authorization: `Bearer ${this.accessToken}` }
    }
    return {}
  }
}

// Usage
const auth = new AuthManager()
const success = await auth.login('student@example.com', 'SecurePassword123!')
if (success) {
  console.log('Login successful!')
}
```text
## Content Generation

### Generate Educational Content

#### Python

```python
import httpx
import asyncio
from typing import Dict, List, Optional

class ContentGenerator:
    def __init__(self, auth_manager: AuthManager):
        self.auth = auth_manager
        self.base_url = auth_manager.base_url

    async def generate_lesson(
        self,
        subject: str,
        grade_level: int,
        learning_objectives: List[str],
        environment_type: str = "classroom",
        include_quiz: bool = True
    ) -> Optional[Dict]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/content/generate",
                headers=self.auth.get_headers(),
                json={
                    "subject": subject,
                    "grade_level": grade_level,
                    "content_type": "lesson",
                    "learning_objectives": learning_objectives,
                    "environment_type": environment_type,
                    "include_quiz": include_quiz,
                    "difficulty": "medium"
                }
            )

            if response.status_code == 200:
                content = response.json()
                print(f"Generated lesson: {content['title']}")
                return content
            else:
                print(f"Error generating content: {response.status_code}")
                return None

    async def generate_quiz(
        self,
        subject: str,
        grade_level: int,
        num_questions: int = 10,
        difficulty: str = "medium"
    ) -> Optional[Dict]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/content/generate",
                headers=self.auth.get_headers(),
                json={
                    "subject": subject,
                    "grade_level": grade_level,
                    "content_type": "quiz",
                    "difficulty": difficulty,
                    "learning_objectives": [f"Assessment for {subject}"]
                }
            )

            if response.status_code == 200:
                return response.json()
            return None

# Usage
async def generate_math_lesson():
    auth = AuthManager()
    await auth.login("teacher@example.com", "TeacherPass123!")

    generator = ContentGenerator(auth)
    lesson = await generator.generate_lesson(
        subject="Mathematics",
        grade_level=7,
        learning_objectives=[
            "Understand fractions and decimals",
            "Solve fraction addition problems",
            "Convert between fractions and decimals"
        ],
        environment_type="classroom",
        include_quiz=True
    )

    if lesson:
        print(f"Lesson ID: {lesson['id']}")
        print(f"Title: {lesson['title']}")
        print(f"Roblox Scripts: {lesson.get('roblox_integration', {})}")

asyncio.run(generate_math_lesson())
```text
#### JavaScript/TypeScript

```typescript
class ContentGenerator {
  private auth: AuthManager
  private baseUrl: string

  constructor(auth: AuthManager) {
    this.auth = auth
    this.baseUrl = auth.baseUrl
  }

  async generateLesson(
    subject: string,
    gradeLevel: number,
    learningObjectives: string[],
    environmentType: string = 'classroom',
    includeQuiz: boolean = true
  ): Promise<any | null> {
    try {
      const response = await fetch(`${this.baseUrl}/api/content/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...this.auth.getHeaders(),
        },
        body: JSON.stringify({
          subject,
          grade_level: gradeLevel,
          content_type: 'lesson',
          learning_objectives: learningObjectives,
          environment_type: environmentType,
          include_quiz: includeQuiz,
          difficulty: 'medium',
        }),
      })

      if (response.ok) {
        const content = await response.json()
        console.log('Generated lesson:', content.title)
        return content
      } else {
        console.error('Error generating content:', response.status)
        return null
      }
    } catch (error) {
      console.error('Network error:', error)
      return null
    }
  }

  async generateWithRobloxIntegration(
    subject: string,
    gradeLevel: number,
    terrainType: string
  ): Promise<any | null> {
    const content = await this.generateLesson(
      subject,
      gradeLevel,
      [`Interactive ${subject} lesson`],
      terrainType,
      true
    )

    if (content && content.roblox_integration) {
      console.log('Roblox terrain script:', content.roblox_integration.terrain_script)
      console.log('Roblox UI components:', content.roblox_integration.ui_components)
    }

    return content
  }
}

// Usage
async function createInteractiveLesson() {
  const auth = new AuthManager()
  await auth.login('teacher@example.com', 'TeacherPass123!')

  const generator = new ContentGenerator(auth)
  const lesson = await generator.generateWithRobloxIntegration('Science', 8, 'laboratory')

  if (lesson) {
    // Process the lesson and Roblox scripts
    console.log('Lesson created with Roblox integration')
  }
}
```text
## Quiz Management

### Create and Submit Quiz

#### Python

```python
import httpx
import asyncio
from typing import Dict, List, Optional
from datetime import datetime

class QuizManager:
    def __init__(self, auth_manager: AuthManager):
        self.auth = auth_manager
        self.base_url = auth_manager.base_url

    async def create_quiz(
        self,
        title: str,
        subject: str,
        questions: List[Dict],
        time_limit: int = 1800  # 30 minutes
    ) -> Optional[Dict]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/quiz/create",
                headers=self.auth.get_headers(),
                json={
                    "title": title,
                    "subject": subject,
                    "grade_level": 7,
                    "difficulty": "medium",
                    "time_limit": time_limit,
                    "questions": questions
                }
            )

            if response.status_code == 201:
                return response.json()
            return None

    async def submit_quiz(
        self,
        quiz_id: str,
        answers: List[Dict],
        time_taken: int
    ) -> Optional[Dict]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/quiz/{quiz_id}/submit",
                headers=self.auth.get_headers(),
                json={
                    "answers": answers,
                    "time_taken": time_taken
                }
            )

            if response.status_code == 200:
                result = response.json()
                print(f"Quiz Score: {result['score']}/{result['total_points']}")
                print(f"Percentage: {result['percentage']}%")
                print(f"Passed: {'Yes' if result['passed'] else 'No'}")
                return result
            return None

# Example: Create a math quiz
async def create_math_quiz():
    auth = AuthManager()
    await auth.login("teacher@example.com", "TeacherPass123!")

    quiz_manager = QuizManager(auth)

    questions = [
        {
            "question_text": "What is 15 + 27?",
            "question_type": "multiple_choice",
            "options": ["42", "41", "43", "40"],
            "correct_answer": "42",
            "points": 1,
            "explanation": "15 + 27 = 42"
        },
        {
            "question_text": "Is 7 a prime number?",
            "question_type": "true_false",
            "options": ["True", "False"],
            "correct_answer": "True",
            "points": 1,
            "explanation": "7 is only divisible by 1 and itself"
        },
        {
            "question_text": "What is 3/4 as a decimal?",
            "question_type": "short_answer",
            "options": [],
            "correct_answer": "0.75",
            "points": 2,
            "explanation": "3 divided by 4 equals 0.75"
        }
    ]

    quiz = await quiz_manager.create_quiz(
        title="Math Basics Quiz",
        subject="Mathematics",
        questions=questions,
        time_limit=900  # 15 minutes
    )

    if quiz:
        print(f"Quiz created: {quiz['id']}")
        print(f"Total points: {quiz['total_points']}")

    return quiz

# Example: Submit quiz answers
async def take_quiz(quiz_id: str):
    auth = AuthManager()
    await auth.login("student@example.com", "StudentPass123!")

    quiz_manager = QuizManager(auth)

    # Student's answers
    answers = [
        {"question_id": "q1", "answer": "42"},
        {"question_id": "q2", "answer": "True"},
        {"question_id": "q3", "answer": "0.75"}
    ]

    result = await quiz_manager.submit_quiz(
        quiz_id=quiz_id,
        answers=answers,
        time_taken=300  # 5 minutes
    )

    if result:
        print(f"XP Earned: {result.get('xp_earned', 0)}")
        for achievement in result.get('achievements_unlocked', []):
            print(f"Achievement Unlocked: {achievement}")

asyncio.run(create_math_quiz())
```text
#### JavaScript/TypeScript

```typescript
interface QuizQuestion {
  question_text: string
  question_type: 'multiple_choice' | 'true_false' | 'short_answer' | 'fill_blank'
  options: string[]
  correct_answer: string | string[]
  points: number
  explanation?: string
  media?: {
    image_url?: string
    video_url?: string
  }
}

interface QuizAnswer {
  question_id: string
  answer: string | string[]
}

class QuizManager {
  private auth: AuthManager
  private baseUrl: string

  constructor(auth: AuthManager) {
    this.auth = auth
    this.baseUrl = auth.baseUrl
  }

  async createQuiz(
    title: string,
    subject: string,
    questions: QuizQuestion[],
    timeLimit: number = 1800
  ): Promise<any | null> {
    try {
      const response = await fetch(`${this.baseUrl}/api/quiz/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...this.auth.getHeaders(),
        },
        body: JSON.stringify({
          title,
          subject,
          grade_level: 7,
          difficulty: 'medium',
          time_limit: timeLimit,
          questions,
        }),
      })

      if (response.status === 201) {
        return await response.json()
      }
      return null
    } catch (error) {
      console.error('Error creating quiz:', error)
      return null
    }
  }

  async submitQuiz(quizId: string, answers: QuizAnswer[], timeTaken: number): Promise<any | null> {
    try {
      const response = await fetch(`${this.baseUrl}/api/quiz/${quizId}/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...this.auth.getHeaders(),
        },
        body: JSON.stringify({
          answers,
          time_taken: timeTaken,
        }),
      })

      if (response.ok) {
        const result = await response.json()
        this.displayResults(result)
        return result
      }
      return null
    } catch (error) {
      console.error('Error submitting quiz:', error)
      return null
    }
  }

  private displayResults(result: any): void {
    console.log(`Score: ${result.score}/${result.total_points}`)
    console.log(`Percentage: ${result.percentage}%`)
    console.log(`Passed: ${result.passed ? 'Yes' : 'No'}`)

    if (result.xp_earned) {
      console.log(`XP Earned: ${result.xp_earned}`)
    }

    if (result.achievements_unlocked?.length > 0) {
      console.log('Achievements Unlocked:')
      result.achievements_unlocked.forEach((achievement: string) => {
        console.log(`  - ${achievement}`)
      })
    }
  }
}

// Interactive quiz component
class InteractiveQuiz {
  private quizManager: QuizManager
  private currentQuiz: any
  private startTime: number = 0
  private answers: Map<string, string> = new Map()

  constructor(quizManager: QuizManager) {
    this.quizManager = quizManager
  }

  async loadQuiz(quizId: string): Promise<void> {
    // Fetch quiz details
    const response = await fetch(`${this.baseUrl}/api/quiz/${quizId}`, {
      headers: this.auth.getHeaders(),
    })

    if (response.ok) {
      this.currentQuiz = await response.json()
      this.startTime = Date.now()
      this.renderQuiz()
    }
  }

  private renderQuiz(): void {
    // Render quiz UI
    console.log(`Starting quiz: ${this.currentQuiz.title}`)
    console.log(`Time limit: ${this.currentQuiz.time_limit / 60} minutes`)
  }

  recordAnswer(questionId: string, answer: string): void {
    this.answers.set(questionId, answer)
  }

  async submitQuiz(): Promise<void> {
    const timeTaken = Math.floor((Date.now() - this.startTime) / 1000)
    const answerArray = Array.from(this.answers.entries()).map(([question_id, answer]) => ({
      question_id,
      answer,
    }))

    const result = await this.quizManager.submitQuiz(this.currentQuiz.id, answerArray, timeTaken)

    if (result) {
      this.showResults(result)
    }
  }

  private showResults(result: any): void {
    // Display results UI
    console.log('Quiz completed!')
    console.log(`Your score: ${result.percentage}%`)
  }
}
```text
## Progress Tracking

### Track Learning Progress

#### Python

```python
import httpx
import asyncio
from typing import Dict, Optional
from datetime import datetime, timedelta

class ProgressTracker:
    def __init__(self, auth_manager: AuthManager):
        self.auth = auth_manager
        self.base_url = auth_manager.base_url

    async def get_course_progress(self, course_id: str) -> Optional[Dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/progress/course/{course_id}",
                headers=self.auth.get_headers()
            )

            if response.status_code == 200:
                progress = response.json()
                self.display_progress(progress)
                return progress
            return None

    async def get_analytics_dashboard(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        metric_type: str = "engagement"
    ) -> Optional[Dict]:
        params = {"metric_type": metric_type}

        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/analytics/dashboard",
                headers=self.auth.get_headers(),
                params=params
            )

            if response.status_code == 200:
                return response.json()
            return None

    def display_progress(self, progress: Dict):
        print(f"Course Progress: {progress['overall_progress']:.1f}%")
        print(f"Lessons: {progress['lessons_completed']}/{progress['total_lessons']}")
        print(f"Quizzes: {progress['quizzes_completed']}/{progress['total_quizzes']}")
        print(f"Average Quiz Score: {progress['average_quiz_score']:.1f}%")
        print(f"Time Spent: {progress['time_spent']} minutes")

        if progress.get('achievements'):
            print("\nAchievements:")
            for achievement in progress['achievements']:
                print(f"  🏆 {achievement['name']} - {achievement['earned_at']}")

# Usage
async def track_student_progress():
    auth = AuthManager()
    await auth.login("student@example.com", "StudentPass123!")

    tracker = ProgressTracker(auth)

    # Get course progress
    course_progress = await tracker.get_course_progress("course-123")

    # Get analytics for the last week
    last_week = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")

    analytics = await tracker.get_analytics_dashboard(
        start_date=last_week,
        end_date=today,
        metric_type="performance"
    )

    if analytics:
        print(f"\nWeekly Analytics:")
        print(f"Active Users: {analytics['summary']['active_users']}")
        print(f"Content Generated: {analytics['summary']['content_generated']}")
        print(f"Quizzes Completed: {analytics['summary']['quizzes_completed']}")

asyncio.run(track_student_progress())
```text
#### JavaScript/TypeScript

```typescript
class ProgressTracker {
  private auth: AuthManager
  private baseUrl: string

  constructor(auth: AuthManager) {
    this.auth = auth
    this.baseUrl = auth.baseUrl
  }

  async getCourseProgress(courseId: string): Promise<any | null> {
    try {
      const response = await fetch(`${this.baseUrl}/api/progress/course/${courseId}`, {
        headers: this.auth.getHeaders(),
      })

      if (response.ok) {
        const progress = await response.json()
        this.displayProgress(progress)
        return progress
      }
      return null
    } catch (error) {
      console.error('Error fetching progress:', error)
      return null
    }
  }

  async getAnalyticsDashboard(
    startDate?: string,
    endDate?: string,
    metricType: string = 'engagement'
  ): Promise<any | null> {
    const params = new URLSearchParams({ metric_type: metricType })

    if (startDate) params.append('start_date', startDate)
    if (endDate) params.append('end_date', endDate)

    try {
      const response = await fetch(`${this.baseUrl}/api/analytics/dashboard?${params}`, {
        headers: this.auth.getHeaders(),
      })

      if (response.ok) {
        return await response.json()
      }
      return null
    } catch (error) {
      console.error('Error fetching analytics:', error)
      return null
    }
  }

  private displayProgress(progress: any): void {
    console.log(`Course Progress: ${progress.overall_progress.toFixed(1)}%`)
    console.log(`Lessons: ${progress.lessons_completed}/${progress.total_lessons}`)
    console.log(`Quizzes: ${progress.quizzes_completed}/${progress.total_quizzes}`)
    console.log(`Average Quiz Score: ${progress.average_quiz_score.toFixed(1)}%`)
    console.log(`Time Spent: ${progress.time_spent} minutes`)

    if (progress.achievements?.length > 0) {
      console.log('\nAchievements:')
      progress.achievements.forEach((achievement: any) => {
        console.log(`  🏆 ${achievement.name} - ${achievement.earned_at}`)
      })
    }
  }

  // Create a progress chart
  createProgressChart(canvasId: string, progress: any): void {
    const canvas = document.getElementById(canvasId) as HTMLCanvasElement
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Draw progress circle
    const centerX = canvas.width / 2
    const centerY = canvas.height / 2
    const radius = 80
    const progress_radians = (progress.overall_progress / 100) * 2 * Math.PI

    // Background circle
    ctx.beginPath()
    ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI)
    ctx.strokeStyle = '#e0e0e0'
    ctx.lineWidth = 20
    ctx.stroke()

    // Progress arc
    ctx.beginPath()
    ctx.arc(centerX, centerY, radius, -Math.PI / 2, progress_radians - Math.PI / 2)
    ctx.strokeStyle = '#4caf50'
    ctx.lineWidth = 20
    ctx.stroke()

    // Progress text
    ctx.fillStyle = '#333'
    ctx.font = 'bold 24px Arial'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(`${progress.overall_progress.toFixed(0)}%`, centerX, centerY)
  }
}

// Real-time progress updates
class ProgressDashboard {
  private tracker: ProgressTracker
  private updateInterval: number

  constructor(tracker: ProgressTracker) {
    this.tracker = tracker
    this.updateInterval = 0
  }

  startRealTimeUpdates(courseId: string, intervalMs: number = 30000): void {
    // Update every 30 seconds by default
    this.updateInterval = window.setInterval(async () => {
      const progress = await this.tracker.getCourseProgress(courseId)
      if (progress) {
        this.updateUI(progress)
      }
    }, intervalMs)
  }

  stopRealTimeUpdates(): void {
    if (this.updateInterval) {
      clearInterval(this.updateInterval)
    }
  }

  private updateUI(progress: any): void {
    // Update progress bars
    const progressBar = document.getElementById('progress-bar') as HTMLElement
    if (progressBar) {
      progressBar.style.width = `${progress.overall_progress}%`
    }

    // Update stats
    const stats = document.getElementById('progress-stats') as HTMLElement
    if (stats) {
      stats.innerHTML = `
                <div>Lessons: ${progress.lessons_completed}/${progress.total_lessons}</div>
                <div>Quizzes: ${progress.quizzes_completed}/${progress.total_quizzes}</div>
                <div>Average Score: ${progress.average_quiz_score.toFixed(1)}%</div>
            `
    }
  }
}
```text
## WebSocket Connections

### Real-time Updates

#### Python

```python
import asyncio
import websockets
import json
from typing import Callable, Optional

class WebSocketClient:
    def __init__(self, auth_manager: AuthManager):
        self.auth = auth_manager
        self.ws_url = "ws://localhost:9876/ws/connect"
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.running = False
        self.handlers = {}

    async def connect(self):
        headers = {"Authorization": f"Bearer {self.auth.access_token}"}
        self.websocket = await websockets.connect(self.ws_url, extra_headers=headers)
        self.running = True
        print("WebSocket connected")

    async def disconnect(self):
        self.running = False
        if self.websocket:
            await self.websocket.close()
        print("WebSocket disconnected")

    def on(self, event_type: str, handler: Callable):
        """Register event handler"""
        self.handlers[event_type] = handler

    async def send(self, message_type: str, data: dict):
        """Send message to server"""
        if self.websocket:
            message = {
                "type": message_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.websocket.send(json.dumps(message))

    async def listen(self):
        """Listen for incoming messages"""
        while self.running and self.websocket:
            try:
                message = await self.websocket.recv()
                data = json.loads(message)

                # Handle message based on type
                message_type = data.get("type")
                if message_type in self.handlers:
                    await self.handlers[message_type](data.get("data"))
                else:
                    print(f"Unhandled message type: {message_type}")

            except websockets.exceptions.ConnectionClosed:
                print("WebSocket connection closed")
                self.running = False
            except Exception as e:
                print(f"WebSocket error: {e}")

# Usage
async def realtime_updates():
    auth = AuthManager()
    await auth.login("student@example.com", "StudentPass123!")

    ws_client = WebSocketClient(auth)

    # Register event handlers
    async def on_content_update(data):
        print(f"Content updated: {data}")

    async def on_quiz_result(data):
        print(f"Quiz result received: Score {data['score']}/{data['total']}")

    async def on_progress_update(data):
        print(f"Progress update: {data['percentage']}% complete")

    async def on_notification(data):
        print(f"📢 Notification: {data['message']}")

    ws_client.on("content_update", on_content_update)
    ws_client.on("quiz_result", on_quiz_result)
    ws_client.on("progress_update", on_progress_update)
    ws_client.on("notification", on_notification)

    # Connect and listen
    await ws_client.connect()

    # Send a message
    await ws_client.send("subscribe", {"channel": "course_updates"})

    # Listen for messages
    try:
        await ws_client.listen()
    except KeyboardInterrupt:
        await ws_client.disconnect()

asyncio.run(realtime_updates())
```text
#### JavaScript/TypeScript

```typescript
class WebSocketClient {
    private ws: WebSocket | null = null;
    private auth: AuthManager;
    private wsUrl: string;
    private handlers: Map<string, (data: any) => void> = new Map();
    private reconnectInterval: number = 5000;
    private maxReconnectAttempts: number = 5;
    private reconnectAttempts: number = 0;

    constructor(auth: AuthManager) {
        this.auth = auth;
        this.wsUrl = 'ws://localhost:9876/ws/connect';
    }

    connect(): Promise<void> {
        return new Promise((resolve, reject) => {
            const token = this.auth.getHeaders()['Authorization'];
            this.ws = new WebSocket(`${this.wsUrl}?token=${token}`);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.reconnectAttempts = 0;
                resolve();
            };

            this.ws.onmessage = (event) => {
                this.handleMessage(event.data);
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                reject(error);
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.attemptReconnect();
            };
        });
    }

    private attemptReconnect(): void {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            setTimeout(() => {
                this.connect().catch(console.error);
            }, this.reconnectInterval);
        } else {
            console.error('Max reconnection attempts reached');
        }
    }

    disconnect(): void {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    on(eventType: string, handler: (data: any) => void): void {
        this.handlers.set(eventType, handler);
    }

    off(eventType: string): void {
        this.handlers.delete(eventType);
    }

    send(messageType: string, data: any): void {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            const message = {
                type: messageType,
                data: data,
                timestamp: new Date().toISOString()
            };
            this.ws.send(JSON.stringify(message));
        } else {
            console.error('WebSocket not connected');
        }
    }

    private handleMessage(message: string): void {
        try {
            const data = JSON.parse(message);
            const handler = this.handlers.get(data.type);

            if (handler) {
                handler(data.data);
            } else {
                console.log('Unhandled message type:', data.type);
            }
        } catch (error) {
            console.error('Error handling message:', error);
        }
    }
}

// React Hook for WebSocket
function useWebSocket(auth: AuthManager) {
    const [ws, setWs] = useState<WebSocketClient | null>(null);
    const [connected, setConnected] = useState(false);
    const [messages, setMessages] = useState<any[]>([]);

    useEffect(() => {
        const client = new WebSocketClient(auth);

        // Set up event handlers
        client.on('content_update', (data) => {
            setMessages(prev => [...prev, { type: 'content', data }]);
        });

        client.on('quiz_result', (data) => {
            setMessages(prev => [...prev, { type: 'quiz', data }]);
        });

        client.on('notification', (data) => {
            // Show notification
            if ('Notification' in window && Notification.permission === 'granted') {
                new Notification('ToolboxAI', {
                    body: data.message,
                    icon: '/logo.png'
                });
            }
            setMessages(prev => [...prev, { type: 'notification', data }]);
        });

        // Connect
        client.connect()
            .then(() => {
                setConnected(true);
                setWs(client);
            })
            .catch(console.error);

        // Cleanup
        return () => {
            client.disconnect();
        };
    }, [auth]);

    return { ws, connected, messages };
}

// Usage in React component
function RealTimeComponent() {
    const auth = useAuthContext();
    const { ws, connected, messages } = useWebSocket(auth);

    const subscribeToUpdates = () => {
        if (ws) {
            ws.send('subscribe', {
                channels: ['course_updates', 'quiz_results']
            });
        }
    };

    return (
        <div>
            <div>Status: {connected ? '🟢 Connected' : '🔴 Disconnected'}</div>
            <button onClick={subscribeToUpdates}>Subscribe to Updates</button>

            <div>
                <h3>Recent Messages</h3>
                {messages.map((msg, index) => (
                    <div key={index}>
                        <span>{msg.type}: </span>
                        <span>{JSON.stringify(msg.data)}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}
```text
## Error Handling

### Comprehensive Error Handling

#### Python

```python
import httpx
import asyncio
from typing import Optional, Dict, Any
from enum import Enum

class APIError(Exception):
    """Custom API error class"""
    def __init__(self, status_code: int, message: str, details: Optional[Dict] = None):
        self.status_code = status_code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class ErrorCode(Enum):
    NETWORK_ERROR = "NETWORK_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    RATE_LIMIT = "RATE_LIMIT"
    SERVER_ERROR = "SERVER_ERROR"

class APIClient:
    def __init__(self, auth_manager: AuthManager):
        self.auth = auth_manager
        self.base_url = auth_manager.base_url
        self.retry_count = 3
        self.retry_delay = 1  # seconds

    async def request_with_retry(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> httpx.Response:
        """Make HTTP request with automatic retry on failure"""
        last_error = None

        for attempt in range(self.retry_count):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.request(
                        method=method,
                        url=f"{self.base_url}{endpoint}",
                        headers=self.auth.get_headers(),
                        **kwargs
                    )

                    # Check for common errors
                    if response.status_code == 401:
                        # Try to refresh token
                        if await self.auth.refresh_access_token():
                            # Update headers with new token
                            kwargs['headers'] = self.auth.get_headers()
                            continue
                        else:
                            raise APIError(401, "Authentication failed",
                                         {"code": ErrorCode.AUTHENTICATION_ERROR.value})

                    elif response.status_code == 429:
                        # Rate limited - wait and retry
                        retry_after = response.headers.get('Retry-After', self.retry_delay * (attempt + 1))
                        print(f"Rate limited. Waiting {retry_after} seconds...")
                        await asyncio.sleep(int(retry_after))
                        continue

                    elif response.status_code >= 500:
                        # Server error - retry with exponential backoff
                        if attempt < self.retry_count - 1:
                            wait_time = self.retry_delay * (2 ** attempt)
                            print(f"Server error. Retrying in {wait_time} seconds...")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            raise APIError(response.status_code, "Server error",
                                         {"code": ErrorCode.SERVER_ERROR.value})

                    elif response.status_code == 404:
                        raise APIError(404, "Resource not found",
                                     {"code": ErrorCode.NOT_FOUND.value})

                    elif response.status_code >= 400:
                        error_data = response.json()
                        raise APIError(response.status_code,
                                     error_data.get('message', 'Request failed'),
                                     {"code": ErrorCode.VALIDATION_ERROR.value,
                                      "details": error_data})

                    # Success
                    return response

            except httpx.ConnectError as e:
                last_error = APIError(0, f"Connection failed: {str(e)}",
                                    {"code": ErrorCode.NETWORK_ERROR.value})
                if attempt < self.retry_count - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue

            except httpx.TimeoutException as e:
                last_error = APIError(0, f"Request timed out: {str(e)}",
                                    {"code": ErrorCode.NETWORK_ERROR.value})
                if attempt < self.retry_count - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue

        # All retries failed
        if last_error:
            raise last_error
        else:
            raise APIError(0, "Unknown error occurred")

    async def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        response = await self.request_with_retry("GET", endpoint, **kwargs)
        return response.json()

    async def post(self, endpoint: str, data: Dict, **kwargs) -> Dict[str, Any]:
        response = await self.request_with_retry("POST", endpoint, json=data, **kwargs)
        return response.json()

# Usage with error handling
async def safe_content_generation():
    auth = AuthManager()
    api_client = APIClient(auth)

    try:
        await auth.login("teacher@example.com", "TeacherPass123!")

        result = await api_client.post(
            "/api/content/generate",
            data={
                "subject": "Mathematics",
                "grade_level": 7,
                "content_type": "lesson",
                "learning_objectives": ["Basic algebra"]
            }
        )

        print(f"Content generated: {result['id']}")

    except APIError as e:
        print(f"API Error ({e.status_code}): {e.message}")

        if e.details.get('code') == ErrorCode.AUTHENTICATION_ERROR.value:
            print("Please check your credentials")
        elif e.details.get('code') == ErrorCode.RATE_LIMIT.value:
            print("You've made too many requests. Please wait.")
        elif e.details.get('code') == ErrorCode.VALIDATION_ERROR.value:
            print("Invalid request data:", e.details.get('details'))

    except Exception as e:
        print(f"Unexpected error: {e}")

asyncio.run(safe_content_generation())
```text
#### JavaScript/TypeScript

```typescript
enum ErrorCode {
    NETWORK_ERROR = 'NETWORK_ERROR',
    AUTHENTICATION_ERROR = 'AUTHENTICATION_ERROR',
    VALIDATION_ERROR = 'VALIDATION_ERROR',
    NOT_FOUND = 'NOT_FOUND',
    RATE_LIMIT = 'RATE_LIMIT',
    SERVER_ERROR = 'SERVER_ERROR'
}

class APIError extends Error {
    constructor(
        public statusCode: number,
        message: string,
        public code: ErrorCode,
        public details?: any
    ) {
        super(message);
        this.name = 'APIError';
    }
}

class APIClient {
    private auth: AuthManager;
    private baseUrl: string;
    private retryCount: number = 3;
    private retryDelay: number = 1000; // milliseconds

    constructor(auth: AuthManager) {
        this.auth = auth;
        this.baseUrl = auth.baseUrl;
    }

    private async sleep(ms: number): Promise<void> {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    async requestWithRetry(
        method: string,
        endpoint: string,
        options: RequestInit = {}
    ): Promise<Response> {
        let lastError: Error | null = null;

        for (let attempt = 0; attempt < this.retryCount; attempt++) {
            try {
                const response = await fetch(`${this.baseUrl}${endpoint}`, {
                    method,
                    ...options,
                    headers: {
                        'Content-Type': 'application/json',
                        ...this.auth.getHeaders(),
                        ...options.headers
                    }
                });

                // Handle specific status codes
                if (response.status === 401) {
                    // Try to refresh token
                    if (await this.auth.refreshAccessToken()) {
                        // Update headers with new token
                        options.headers = {
                            ...options.headers,
                            ...this.auth.getHeaders()
                        };
                        continue;
                    } else {
                        throw new APIError(
                            401,
                            'Authentication failed',
                            ErrorCode.AUTHENTICATION_ERROR
                        );
                    }
                } else if (response.status === 429) {
                    // Rate limited
                    const retryAfter = response.headers.get('Retry-After');
                    const waitTime = retryAfter
                        ? parseInt(retryAfter) * 1000
                        : this.retryDelay * (attempt + 1);

                    console.log(`Rate limited. Waiting ${waitTime}ms...`);
                    await this.sleep(waitTime);
                    continue;
                } else if (response.status >= 500) {
                    // Server error - retry with exponential backoff
                    if (attempt < this.retryCount - 1) {
                        const waitTime = this.retryDelay * Math.pow(2, attempt);
                        console.log(`Server error. Retrying in ${waitTime}ms...`);
                        await this.sleep(waitTime);
                        continue;
                    } else {
                        throw new APIError(
                            response.status,
                            'Server error',
                            ErrorCode.SERVER_ERROR
                        );
                    }
                } else if (response.status === 404) {
                    throw new APIError(
                        404,
                        'Resource not found',
                        ErrorCode.NOT_FOUND
                    );
                } else if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new APIError(
                        response.status,
                        errorData.message || 'Request failed',
                        ErrorCode.VALIDATION_ERROR,
                        errorData
                    );
                }

                // Success
                return response;

            } catch (error) {
                if (error instanceof APIError) {
                    throw error;
                }

                // Network error
                lastError = error as Error;
                if (attempt < this.retryCount - 1) {
                    await this.sleep(this.retryDelay * (attempt + 1));
                    continue;
                }
            }
        }

        // All retries failed
        throw new APIError(
            0,
            lastError?.message || 'Network error',
            ErrorCode.NETWORK_ERROR
        );
    }

    async get<T>(endpoint: string, options?: RequestInit): Promise<T> {
        const response = await this.requestWithRetry('GET', endpoint, options);
        return response.json();
    }

    async post<T>(endpoint: string, data: any, options?: RequestInit): Promise<T> {
        const response = await this.requestWithRetry('POST', endpoint, {
            ...options,
            body: JSON.stringify(data)
        });
        return response.json();
    }
}

// Error boundary for React
class ErrorBoundary extends React.Component<
    { children: React.ReactNode },
    { hasError: boolean; error: Error | null }
> {
    constructor(props: { children: React.ReactNode }) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error: Error) {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
        console.error('Error caught by boundary:', error, errorInfo);

        // Log to error reporting service
        if (error instanceof APIError) {
            this.logAPIError(error);
        }
    }

    private logAPIError(error: APIError) {
        // Send to error tracking service (e.g., Sentry)
        console.error({
            type: 'API_ERROR',
            statusCode: error.statusCode,
            code: error.code,
            message: error.message,
            details: error.details,
            timestamp: new Date().toISOString()
        });
    }

    render() {
        if (this.state.hasError) {
            const error = this.state.error;

            if (error instanceof APIError) {
                switch (error.code) {
                    case ErrorCode.AUTHENTICATION_ERROR:
                        return <div>Please log in again</div>;
                    case ErrorCode.RATE_LIMIT:
                        return <div>Too many requests. Please wait.</div>;
                    case ErrorCode.NOT_FOUND:
                        return <div>Resource not found</div>;
                    default:
                        return <div>An error occurred. Please try again.</div>;
                }
            }

            return <div>Something went wrong</div>;
        }

        return this.props.children;
    }
}

// Usage with async/await and error handling
async function safeContentGeneration() {
    const auth = new AuthManager();
    const apiClient = new APIClient(auth);

    try {
        await auth.login('teacher@example.com', 'TeacherPass123!');

        const result = await apiClient.post('/api/content/generate', {
            subject: 'Mathematics',
            grade_level: 7,
            content_type: 'lesson',
            learning_objectives: ['Basic algebra']
        });

        console.log('Content generated:', result.id);

    } catch (error) {
        if (error instanceof APIError) {
            console.error(`API Error (${error.statusCode}): ${error.message}`);

            switch (error.code) {
                case ErrorCode.AUTHENTICATION_ERROR:
                    console.error('Please check your credentials');
                    break;
                case ErrorCode.RATE_LIMIT:
                    console.error('You\'ve made too many requests. Please wait.');
                    break;
                case ErrorCode.VALIDATION_ERROR:
                    console.error('Invalid request data:', error.details);
                    break;
                default:
                    console.error('An error occurred:', error.message);
            }
        } else {
            console.error('Unexpected error:', error);
        }
    }
}
```text
## Best Practices

### API Client Wrapper

Create a comprehensive API client that handles all common scenarios:

```typescript
// api-client.ts
export class ToolboxAIClient {
  private auth: AuthManager
  private api: APIClient
  private ws: WebSocketClient | null = null
  private content: ContentGenerator
  private quiz: QuizManager
  private progress: ProgressTracker

  constructor(
    config: {
      baseUrl?: string
      wsUrl?: string
      autoRefreshToken?: boolean
    } = {}
  ) {
    this.auth = new AuthManager(config.baseUrl)
    this.api = new APIClient(this.auth)
    this.content = new ContentGenerator(this.auth)
    this.quiz = new QuizManager(this.auth)
    this.progress = new ProgressTracker(this.auth)
  }

  async initialize(email: string, password: string): Promise<boolean> {
    const success = await this.auth.login(email, password)
    if (success && this.ws) {
      await this.connectWebSocket()
    }
    return success
  }

  async connectWebSocket(): Promise<void> {
    this.ws = new WebSocketClient(this.auth)
    await this.ws.connect()
  }

  // Expose service methods
  generateContent = this.content.generateLesson.bind(this.content)
  createQuiz = this.quiz.createQuiz.bind(this.quiz)
  submitQuiz = this.quiz.submitQuiz.bind(this.quiz)
  getCourseProgress = this.progress.getCourseProgress.bind(this.progress)

  // Clean up
  async disconnect(): Promise<void> {
    if (this.ws) {
      await this.ws.disconnect()
    }
  }
}

// Usage
const client = new ToolboxAIClient()
await client.initialize('teacher@example.com', 'password')

const content = await client.generateContent('Mathematics', 7, ['Fractions'], 'classroom')
```text
## Testing API Endpoints

### Automated Testing

```python
# test_api.py
import pytest
import httpx
from typing import AsyncGenerator

@pytest.fixture
async def auth_client() -> AsyncGenerator[APIClient, None]:
    auth = AuthManager()
    await auth.login("test@example.com", "TestPass123!")
    client = APIClient(auth)
    yield client

@pytest.mark.asyncio
async def test_content_generation(auth_client: APIClient):
    result = await auth_client.post(
        "/api/content/generate",
        data={
            "subject": "Science",
            "grade_level": 6,
            "content_type": "lesson",
            "learning_objectives": ["Photosynthesis"]
        }
    )

    assert result["id"] is not None
    assert result["subject"] == "Science"
    assert result["grade_level"] == 6

@pytest.mark.asyncio
async def test_quiz_workflow(auth_client: APIClient):
    # Create quiz
    quiz = await auth_client.post(
        "/api/quiz/create",
        data={
            "title": "Test Quiz",
            "subject": "Math",
            "questions": [
                {
                    "question_text": "What is 2+2?",
                    "question_type": "multiple_choice",
                    "options": ["3", "4", "5", "6"],
                    "correct_answer": "4",
                    "points": 1
                }
            ]
        }
    )

    assert quiz["id"] is not None

    # Submit answers
    result = await auth_client.post(
        f"/api/quiz/{quiz['id']}/submit",
        data={
            "answers": [{"question_id": "q1", "answer": "4"}],
            "time_taken": 60
        }
    )

    assert result["score"] == 1
    assert result["passed"] is True
```text
This comprehensive API examples documentation provides practical, working code for all major endpoints and use cases.

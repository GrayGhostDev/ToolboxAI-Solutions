# JavaScript/TypeScript SDK

Official JavaScript SDK for ToolBoxAI-Solutions with full TypeScript support. Build modern educational applications with ease using our promise-based API.

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Authentication](#authentication)
4. [Configuration](#configuration)
5. [API Reference](#api-reference)
6. [TypeScript Support](#typescript-support)
7. [React Integration](#react-integration)
8. [Error Handling](#error-handling)
9. [Advanced Features](#advanced-features)
10. [Examples](#examples)
11. [Troubleshooting](#troubleshooting)

## Installation

### NPM

```bash
npm install @toolboxai/sdk
```text
### Yarn

```bash
yarn add @toolboxai/sdk
```text
### CDN

```html
<script src="https://cdn.toolboxai.com/sdk/latest/toolboxai.min.js"></script>
```text
### Requirements

- Node.js 14+ (for Node.js environment)
- Modern browser with ES6 support (for browser environment)

## Quick Start

### Basic Setup

```javascript
import { ToolBoxAI } from '@toolboxai/sdk'

// Initialize client
const client = new ToolBoxAI({
  apiKey: 'your-api-key-here',
  environment: 'production', // or 'sandbox'
})

// Make your first API call
async function getStarted() {
  try {
    // Get current user
    const user = await client.users.me()
    console.log('Logged in as:', user.name)

    // List lessons
    const lessons = await client.lessons.list({
      grade: 5,
      subject: 'math',
    })
    console.log('Found lessons:', lessons)
  } catch (error) {
    console.error('Error:', error.message)
  }
}

getStarted()
```text
## Authentication

### API Key Authentication

```javascript
const client = new ToolBoxAI({
  apiKey: 'your-api-key-here',
})
```text
### OAuth2 Authentication

```javascript
const client = new ToolBoxAI({
  clientId: 'your-client-id',
  clientSecret: 'your-client-secret',
  redirectUri: 'https://yourapp.com/callback',
})

// Initiate OAuth flow
const authUrl = client.auth.getAuthorizationUrl({
  scope: ['lessons:read', 'lessons:write'],
  state: 'random-state-string',
})

// Handle callback
const tokens = await client.auth.handleCallback(callbackUrl)
client.setAccessToken(tokens.accessToken)
```text
### JWT Token Authentication

```javascript
// Login with credentials
const { accessToken, refreshToken } = await client.auth.login({
  email: 'user@example.com',
  password: 'password123',
})

// Set tokens
client.setAccessToken(accessToken)
client.setRefreshToken(refreshToken)

// Auto-refresh tokens
client.on('token:refresh', (newTokens) => {
  // Store new tokens
  localStorage.setItem('accessToken', newTokens.accessToken)
})
```text
## Configuration

### Client Options

```javascript
const client = new ToolBoxAI({
  // Required
  apiKey: 'your-api-key',

  // Optional
  environment: 'production', // 'production' | 'sandbox' | 'development'
  baseUrl: 'https://api.toolboxai.com', // Custom API endpoint
  timeout: 30000, // Request timeout in ms
  retries: 3, // Number of retries
  retryDelay: 1000, // Delay between retries

  // Advanced
  cache: {
    enabled: true,
    ttl: 300000, // Cache TTL in ms
    storage: 'memory', // 'memory' | 'localStorage' | 'sessionStorage'
  },

  interceptors: {
    request: (config) => {
      // Modify request config
      return config
    },
    response: (response) => {
      // Process response
      return response
    },
  },
})
```text
## API Reference

### Users

```javascript
// Get current user
const user = await client.users.me()

// Get user by ID
const user = await client.users.get('user-id')

// Update user
const updated = await client.users.update('user-id', {
  name: 'New Name',
  preferences: { theme: 'dark' },
})

// List users (admin only)
const users = await client.users.list({
  role: 'student',
  page: 1,
  limit: 20,
})

// Delete user (admin only)
await client.users.delete('user-id')
```text
### Lessons

```javascript
// Create lesson
const lesson = await client.lessons.create({
  title: 'Introduction to Algebra',
  description: 'Learn the basics of algebra',
  gradeLevel: 7,
  subject: 'mathematics',
  content: {
    sections: [...]
  }
});

// Get lesson
const lesson = await client.lessons.get('lesson-id');

// Update lesson
const updated = await client.lessons.update('lesson-id', {
  title: 'Updated Title'
});

// List lessons
const lessons = await client.lessons.list({
  subject: 'science',
  gradeLevel: 5,
  search: 'photosynthesis',
  sort: 'popularity',
  page: 1,
  limit: 10
});

// Delete lesson
await client.lessons.delete('lesson-id');

// Deploy to Roblox
const deployment = await client.lessons.deployToRoblox('lesson-id', {
  environmentType: 'classroom',
  maxPlayers: 30
});
```text
### Quizzes

```javascript
// Create quiz
const quiz = await client.quizzes.create({
  title: 'Math Quiz',
  lessonId: 'lesson-id',
  questions: [
    {
      type: 'multiple_choice',
      question: 'What is 2 + 2?',
      options: ['3', '4', '5', '6'],
      correctAnswer: 1,
    },
  ],
  timeLimit: 600, // 10 minutes
})

// Get quiz
const quiz = await client.quizzes.get('quiz-id')

// Submit quiz attempt
const result = await client.quizzes.submit('quiz-id', {
  answers: [
    { questionId: 'q1', answer: 1 },
    { questionId: 'q2', answer: 'Paris' },
  ],
})

// Get quiz results
const results = await client.quizzes.getResults('attempt-id')

// Get quiz analytics
const analytics = await client.quizzes.getAnalytics('quiz-id')
```text
### Progress Tracking

```javascript
// Track progress
await client.progress.track({
  userId: 'user-id',
  lessonId: 'lesson-id',
  event: 'lesson_completed',
  data: {
    timeSpent: 1200, // seconds
    score: 95,
  },
})

// Get user progress
const progress = await client.progress.get('user-id', {
  courseId: 'course-id',
})

// Get analytics
const analytics = await client.progress.getAnalytics('user-id', {
  startDate: '2024-01-01',
  endDate: '2024-12-31',
})

// Generate report
const report = await client.progress.generateReport({
  userId: 'user-id',
  type: 'monthly',
  format: 'pdf',
})
```text
### Gamification

```javascript
// Award XP
await client.gamification.awardXP('user-id', {
  amount: 100,
  reason: 'Completed lesson'
});

// Get player profile
const profile = await client.gamification.getProfile('user-id');

// Unlock achievement
await client.gamification.unlockAchievement('user-id', 'first-lesson');

// Get leaderboard
const leaderboard = await client.gamification.getLeaderboard({
  type: 'weekly',
  limit: 10
});

// Create quest
const quest = await client.gamification.createQuest({
  title: 'Master Mathematics',
  objectives: [...],
  rewards: {
    xp: 500,
    badges: ['math-master']
  }
});
```text
### Content Generation (AI)

```javascript
// Generate lesson from prompt
const lesson = await client.ai.generateLesson({
  prompt: 'Create a lesson about photosynthesis for 5th graders',
  gradeLevel: 5,
  duration: 45, // minutes
  includeQuiz: true,
})

// Generate quiz from lesson
const quiz = await client.ai.generateQuiz({
  lessonId: 'lesson-id',
  questionCount: 10,
  difficulty: 'medium',
})

// Generate Roblox environment
const environment = await client.ai.generateEnvironment({
  lessonId: 'lesson-id',
  theme: 'space',
  interactiveElements: ['npcs', 'puzzles', 'collectibles'],
})

// Validate content
const validation = await client.ai.validateContent({
  content: lessonContent,
  checkFor: ['age_appropriate', 'factual_accuracy', 'bias'],
})
```text
### LMS Integration

```javascript
// Sync with Canvas
await client.lms.canvas.sync({
  courseId: 'canvas-course-id',
  syncGrades: true,
  syncAssignments: true,
})

// Import from Google Classroom
const imported = await client.lms.googleClassroom.importCourse({
  classroomId: 'classroom-id',
  importStudents: true,
})

// Export grades
const exported = await client.lms.exportGrades({
  courseId: 'course-id',
  format: 'csv',
  lmsType: 'schoology',
})
```text
### Real-time Updates

```javascript
// Connect to WebSocket
client.realtime.connect()

// Subscribe to events
client.realtime.on('progress.updated', (data) => {
  console.log('Progress updated:', data)
})

client.realtime.on('achievement.unlocked', (data) => {
  console.log('Achievement unlocked:', data)
})

// Subscribe to specific channel
client.realtime.subscribe('lesson:lesson-id', (event) => {
  console.log('Lesson event:', event)
})

// Unsubscribe
client.realtime.unsubscribe('lesson:lesson-id')

// Disconnect
client.realtime.disconnect()
```text
## TypeScript Support

### Type Definitions

```typescript
import {
  ToolBoxAI,
  Lesson,
  Quiz,
  User,
  Progress,
  Achievement
} from '@toolboxai/sdk';

// Full type safety
const client = new ToolBoxAI({
  apiKey: process.env.TOOLBOXAI_API_KEY as string
});

// Typed responses
const lesson: Lesson = await client.lessons.get('lesson-id');

// Typed parameters
interface CreateLessonParams {
  title: string;
  description: string;
  gradeLevel: number;
  subject: Subject;
  content: LessonContent;
}

const newLesson = await client.lessons.create<CreateLessonParams>({
  title: 'New Lesson',
  description: 'Description',
  gradeLevel: 5,
  subject: Subject.MATH,
  content: {...}
});

// Custom types
type CustomMetadata = {
  schoolId: string;
  districtId: string;
};

const lessonWithMetadata = await client.lessons.create<
  CreateLessonParams & { metadata: CustomMetadata }
>({...});
```text
### Enums and Constants

```typescript
import { Subject, QuestionType, UserRole, Environment, ErrorCode } from '@toolboxai/sdk'

// Use enums for type safety
const lesson = await client.lessons.create({
  subject: Subject.SCIENCE,
  // ...
})

const quiz = await client.quizzes.create({
  questions: [
    {
      type: QuestionType.MULTIPLE_CHOICE,
      // ...
    },
  ],
})
```text
## React Integration

### React Hooks

```jsx
import { useToolBoxAI, ToolBoxAIProvider } from '@toolboxai/sdk/react'

// Wrap your app with provider
function App() {
  return (
    <ToolBoxAIProvider apiKey={process.env.REACT_APP_API_KEY}>
      <YourApp />
    </ToolBoxAIProvider>
  )
}

// Use hooks in components
function LessonList() {
  const {
    data: lessons,
    loading,
    error,
  } = useToolBoxAI('lessons.list', {
    gradeLevel: 5,
    subject: 'math',
  })

  if (loading) return <div>Loading...</div>
  if (error) return <div>Error: {error.message}</div>

  return (
    <ul>
      {lessons.map((lesson) => (
        <li key={lesson.id}>{lesson.title}</li>
      ))}
    </ul>
  )
}

// Mutations
function CreateLesson() {
  const { mutate: createLesson, loading } = useToolBoxAI('lessons.create')

  const handleCreate = async () => {
    try {
      const lesson = await createLesson({
        title: 'New Lesson',
        // ...
      })
      console.log('Created:', lesson)
    } catch (error) {
      console.error('Error:', error)
    }
  }

  return (
    <button onClick={handleCreate} disabled={loading}>
      Create Lesson
    </button>
  )
}
```text
### React Query Integration

```jsx
import { useQuery, useMutation } from '@tanstack/react-query'
import { client } from './toolboxai'

// Query
function useLessons(filters) {
  return useQuery({
    queryKey: ['lessons', filters],
    queryFn: () => client.lessons.list(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// Mutation
function useCreateLesson() {
  return useMutation({
    mutationFn: (data) => client.lessons.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries(['lessons'])
    },
  })
}
```text
## Error Handling

### Error Types

```javascript
import {
  ToolBoxAIError,
  ValidationError,
  AuthenticationError,
  RateLimitError,
  NetworkError,
} from '@toolboxai/sdk'

try {
  const result = await client.lessons.create(data)
} catch (error) {
  if (error instanceof ValidationError) {
    console.error('Validation failed:', error.errors)
  } else if (error instanceof AuthenticationError) {
    console.error('Authentication failed:', error.message)
    // Redirect to login
  } else if (error instanceof RateLimitError) {
    console.error('Rate limited. Retry after:', error.retryAfter)
  } else if (error instanceof NetworkError) {
    console.error('Network error:', error.message)
  } else {
    console.error('Unknown error:', error)
  }
}
```text
### Global Error Handler

```javascript
client.on('error', (error) => {
  console.error('Global error:', error)
  // Send to error tracking service
})

// Retry configuration
client.setRetryPolicy({
  maxRetries: 3,
  retryCondition: (error) => {
    return error.code !== 'INVALID_INPUT'
  },
  retryDelay: (retryCount) => {
    return Math.min(1000 * Math.pow(2, retryCount), 10000)
  },
})
```text
## Advanced Features

### Batch Operations

```javascript
// Batch create
const lessons = await client.lessons.batchCreate([
  { title: 'Lesson 1', ... },
  { title: 'Lesson 2', ... },
  { title: 'Lesson 3', ... }
]);

// Batch update
const updated = await client.lessons.batchUpdate([
  { id: 'lesson-1', title: 'Updated 1' },
  { id: 'lesson-2', title: 'Updated 2' }
]);

// Batch delete
await client.lessons.batchDelete(['lesson-1', 'lesson-2', 'lesson-3']);
```text
### Pagination

```javascript
// Cursor-based pagination
let cursor = null
const allLessons = []

do {
  const response = await client.lessons.list({
    cursor,
    limit: 100,
  })

  allLessons.push(...response.data)
  cursor = response.nextCursor
} while (cursor)

// Page-based pagination
const page1 = await client.lessons.list({ page: 1, limit: 20 })
const page2 = await client.lessons.list({ page: 2, limit: 20 })

// Auto-pagination
const allLessons = await client.lessons.listAll({
  subject: 'math',
}) // Automatically fetches all pages
```text
### File Uploads

```javascript
// Upload file
const file = document.getElementById('file-input').files[0]
const uploaded = await client.files.upload(file, {
  type: 'lesson_resource',
  lessonId: 'lesson-id',
})

// Upload with progress
const uploaded = await client.files.upload(file, {
  onProgress: (progress) => {
    console.log(`Upload progress: ${progress.percent}%`)
  },
})

// Multipart upload for large files
const uploader = client.files.createMultipartUpload(file)
uploader.on('progress', (progress) => {
  console.log(`Progress: ${progress.percent}%`)
})
const result = await uploader.start()
```text
### Caching

```javascript
// Enable caching
const client = new ToolBoxAI({
  apiKey: 'your-key',
  cache: {
    enabled: true,
    ttl: 5 * 60 * 1000, // 5 minutes
    storage: 'localStorage',
  },
})

// Manual cache control
client.cache.set('lessons:5th-grade', lessonsData, 300000)
const cached = client.cache.get('lessons:5th-grade')
client.cache.clear()

// Skip cache for specific request
const freshData = await client.lessons.get('lesson-id', {
  cache: false,
})
```text
### Webhooks

```javascript
// Register webhook
const webhook = await client.webhooks.create({
  url: 'https://yourapp.com/webhook',
  events: ['lesson.created', 'quiz.submitted'],
  secret: 'webhook-secret',
})

// Verify webhook signature (in your webhook handler)
const isValid = client.webhooks.verifySignature(payload, signature, secret)

// List webhooks
const webhooks = await client.webhooks.list()

// Delete webhook
await client.webhooks.delete('webhook-id')
```text
## Examples

### Complete Application Example

```javascript
import { ToolBoxAI } from '@toolboxai/sdk'

class EducationApp {
  constructor() {
    this.client = new ToolBoxAI({
      apiKey: process.env.API_KEY,
    })
  }

  async createCourse(gradeLevel, subject) {
    try {
      // Generate lesson content with AI
      const lesson = await this.client.ai.generateLesson({
        prompt: `Create ${subject} lesson for grade ${gradeLevel}`,
        gradeLevel,
        includeQuiz: true,
      })

      // Deploy to Roblox
      const environment = await this.client.lessons.deployToRoblox(lesson.id)

      // Create associated quiz
      const quiz = await this.client.quizzes.create({
        lessonId: lesson.id,
        questions: lesson.generatedQuiz.questions,
      })

      // Set up progress tracking
      await this.client.progress.initializeTracking({
        lessonId: lesson.id,
        metrics: ['completion', 'score', 'timeSpent'],
      })

      return { lesson, quiz, environment }
    } catch (error) {
      console.error('Course creation failed:', error)
      throw error
    }
  }

  async trackStudentProgress(userId, lessonId, eventData) {
    // Track the event
    await this.client.progress.track({
      userId,
      lessonId,
      ...eventData,
    })

    // Check for achievements
    const achievements = await this.client.gamification.checkAchievements(userId)

    // Award XP
    if (eventData.event === 'lesson_completed') {
      await this.client.gamification.awardXP(userId, {
        amount: 100,
        reason: 'Lesson completion',
      })
    }

    return achievements
  }
}
```text
## Troubleshooting

### Common Issues

#### CORS Errors

```javascript
// Configure CORS proxy for browser environments
const client = new ToolBoxAI({
  apiKey: 'your-key',
  corsProxy: 'https://cors-proxy.yourapp.com',
})
```text
#### Token Expiration

```javascript
// Automatic token refresh
client.on('token:expired', async () => {
  const newTokens = await client.auth.refreshToken()
  client.setAccessToken(newTokens.accessToken)
})
```text
#### Network Timeouts

```javascript
// Increase timeout for slow connections
const client = new ToolBoxAI({
  apiKey: 'your-key',
  timeout: 60000, // 60 seconds
})
```text
### Debug Mode

```javascript
// Enable debug logging
const client = new ToolBoxAI({
  apiKey: 'your-key',
  debug: true,
})

// Custom logger
client.setLogger({
  log: (message, data) => console.log(message, data),
  error: (message, error) => console.error(message, error),
  warn: (message, data) => console.warn(message, data),
})
```text
### Performance Optimization

```javascript
// Connection pooling
const client = new ToolBoxAI({
  apiKey: 'your-key',
  httpAgent: {
    keepAlive: true,
    maxSockets: 10,
  },
})

// Request deduplication
client.enableRequestDeduplication()

// Compression
client.enableCompression()
```text
## Migration

### Migrating from v1 to v2

```javascript
// v1 (deprecated)
const client = new ToolBoxAIClient(apiKey)
client.getLessons(callback)

// v2 (current)
const client = new ToolBoxAI({ apiKey })
const lessons = await client.lessons.list()
```text
See [Migration Guide](https://github.com/toolboxai/sdk-js/blob/main/MIGRATION.md) for detailed instructions.

## Support

- **Documentation**: [docs.toolboxai.com](https://docs.toolboxai.com)
- **GitHub**: [github.com/toolboxai/sdk-js](https://github.com/toolboxai/sdk-js)
- **NPM**: [npmjs.com/package/@toolboxai/sdk](https://npmjs.com/package/@toolboxai/sdk)
- **Discord**: [discord.gg/toolboxai](https://discord.gg/toolboxai)
- **Email**: js-sdk@toolboxai.com

---

_SDK Version: 2.0.0 | API Version: v1 | Last Updated: September 2025_

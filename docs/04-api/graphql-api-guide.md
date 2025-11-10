# GraphQL API Guide

## Overview

The ToolboxAI platform now includes a comprehensive GraphQL API powered by Ariadne (backend) and Apollo Client (frontend). This guide documents the available endpoints, queries, mutations, and subscriptions.

## Endpoint

The GraphQL endpoint is available at:
```
http://localhost:8009/graphql
```

GraphQL Playground (for development):
```
http://localhost:8009/graphql
```

## Authentication

Include JWT token in the Authorization header:
```http
Authorization: Bearer <jwt_token>
```

## Schema Overview

### Queries

#### User Queries
```graphql
# Get current user
query GetCurrentUser {
  currentUser {
    id
    username
    email
    role
    createdAt
    profile {
      firstName
      lastName
      avatar
      school {
        id
        name
      }
    }
  }
}

# Get user by ID
query GetUser($id: ID!) {
  user(id: $id) {
    id
    username
    email
    role
  }
}

# List users with pagination
query ListUsers($page: Int, $limit: Int, $role: String) {
  users(page: $page, limit: $limit, role: $role) {
    items {
      id
      username
      email
      role
    }
    total
    page
    pages
  }
}
```

#### Course Queries
```graphql
# Get course by ID
query GetCourse($id: ID!) {
  course(id: $id) {
    id
    title
    description
    subject
    gradeLevel
    instructor {
      id
      username
    }
    modules {
      id
      title
      order
    }
    enrollmentCount
  }
}

# List courses with filters
query ListCourses($subject: String, $gradeLevel: Int) {
  courses(subject: $subject, gradeLevel: $gradeLevel) {
    items {
      id
      title
      subject
      gradeLevel
      enrollmentCount
    }
    total
  }
}
```

#### Quiz Queries
```graphql
# Get quiz by ID
query GetQuiz($id: ID!) {
  quiz(id: $id) {
    id
    title
    questions {
      id
      text
      type
      options
      correctAnswer
    }
    timeLimit
    passingScore
  }
}

# Get quiz results
query GetQuizResults($quizId: ID!, $userId: ID) {
  quizResults(quizId: $quizId, userId: $userId) {
    id
    score
    percentage
    passed
    completedAt
    answers {
      questionId
      answer
      correct
    }
  }
}
```

#### Roblox Integration Queries
```graphql
# Get Roblox environments
query GetRobloxEnvironments {
  robloxEnvironments {
    id
    name
    type
    terrain
    scripts {
      id
      name
      content
    }
    createdBy {
      id
      username
    }
  }
}

# Get generated content
query GetGeneratedContent($subject: String!, $gradeLevel: Int!) {
  generateContent(
    subject: $subject
    gradeLevel: $gradeLevel
  ) {
    content
    interactiveElements
    robloxIntegration {
      environmentType
      gameMechanics
      scripts
    }
  }
}
```

### Mutations

#### Authentication Mutations
```graphql
# User login
mutation Login($username: String!, $password: String!) {
  login(username: $username, password: $password) {
    token
    user {
      id
      username
      role
    }
  }
}

# User registration
mutation Register($input: RegisterInput!) {
  register(input: $input) {
    token
    user {
      id
      username
      email
    }
  }
}

# Refresh token
mutation RefreshToken($refreshToken: String!) {
  refreshToken(refreshToken: $refreshToken) {
    token
    refreshToken
  }
}
```

#### Course Mutations
```graphql
# Create course
mutation CreateCourse($input: CourseInput!) {
  createCourse(input: $input) {
    id
    title
    description
    subject
    gradeLevel
  }
}

# Update course
mutation UpdateCourse($id: ID!, $input: CourseUpdateInput!) {
  updateCourse(id: $id, input: $input) {
    id
    title
    description
  }
}

# Enroll in course
mutation EnrollInCourse($courseId: ID!) {
  enrollInCourse(courseId: $courseId) {
    success
    enrollment {
      id
      enrolledAt
      progress
    }
  }
}
```

#### Quiz Mutations
```graphql
# Submit quiz
mutation SubmitQuiz($quizId: ID!, $answers: [AnswerInput!]!) {
  submitQuiz(quizId: $quizId, answers: $answers) {
    id
    score
    percentage
    passed
    feedback
  }
}

# Create quiz
mutation CreateQuiz($input: QuizInput!) {
  createQuiz(input: $input) {
    id
    title
    questions {
      id
      text
    }
  }
}
```

### Subscriptions

#### Real-time Updates
```graphql
# Subscribe to content generation progress
subscription ContentGenerationProgress($sessionId: String!) {
  contentGenerationProgress(sessionId: $sessionId) {
    status
    progress
    message
    result
  }
}

# Subscribe to quiz submissions
subscription QuizSubmissions($quizId: ID!) {
  quizSubmissions(quizId: $quizId) {
    userId
    score
    completedAt
  }
}

# Subscribe to course updates
subscription CourseUpdates($courseId: ID!) {
  courseUpdates(courseId: $courseId) {
    type
    data
    timestamp
  }
}
```

## DataLoader Integration

The API uses DataLoader to prevent N+1 query problems. This is automatically handled for:
- User lookups
- Course enrollments
- Quiz results
- Related data fetching

## Error Handling

GraphQL errors follow this format:
```json
{
  "errors": [
    {
      "message": "Error description",
      "extensions": {
        "code": "ERROR_CODE",
        "details": {}
      }
    }
  ]
}
```

Common error codes:
- `UNAUTHENTICATED`: Missing or invalid authentication
- `FORBIDDEN`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `VALIDATION_ERROR`: Input validation failed
- `INTERNAL_ERROR`: Server error

## Rate Limiting

- Anonymous: 100 requests per minute
- Authenticated: 1000 requests per minute
- Subscriptions: 10 concurrent connections per user

## Frontend Integration

### Apollo Client Setup
```typescript
import { ApolloClient, InMemoryCache } from '@apollo/client';

const client = new ApolloClient({
  uri: 'http://localhost:8009/graphql',
  cache: new InMemoryCache(),
  headers: {
    authorization: localStorage.getItem('token') || '',
  },
});
```

### Using Generated Hooks
```typescript
import { useGetCurrentUserQuery, useLoginMutation } from '@/graphql/generated';

// Query example
const { data, loading, error } = useGetCurrentUserQuery();

// Mutation example
const [login, { data, loading }] = useLoginMutation({
  variables: {
    username: 'user@example.com',
    password: 'password123'
  }
});
```

## Code Generation

Generate TypeScript types and hooks:
```bash
npm run codegen
```

Watch mode for development:
```bash
npm run codegen:watch
```

## Testing

### GraphQL Playground Queries

Test authentication:
```graphql
mutation {
  login(username: "admin", password: "admin123") {
    token
    user {
      id
      username
      role
    }
  }
}
```

Test content generation:
```graphql
query {
  generateContent(
    subject: "Mathematics"
    gradeLevel: 5
  ) {
    content
    interactiveElements
  }
}
```

## Performance Tips

1. Use field selection to only request needed data
2. Implement pagination for list queries
3. Use DataLoader for batch loading
4. Cache results on the client side
5. Use subscriptions sparingly

## Security Considerations

1. Always validate input on the server
2. Use field-level permissions
3. Rate limit queries and mutations
4. Sanitize user-generated content
5. Log and monitor unusual query patterns

---

For more information, see the schema files in `/schema/` directory.

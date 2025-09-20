# ToolBoxAI-Solutions Testing Infrastructure & API Documentation

## Table of Contents

1. [Frontend Testing Infrastructure](#frontend-testing-infrastructure)
2. [API Service Layer](#api-service-layer)
3. [Backend API Endpoints](#backend-api-endpoints)
4. [Test Patterns and Best Practices](#test-patterns-and-best-practices)
5. [Known Issues and Workarounds](#known-issues-and-workarounds)
6. [Mock Service Worker (MSW) Configuration](#mock-service-worker-msw-configuration)

---

## Frontend Testing Infrastructure

### Test Setup Configuration

The frontend testing infrastructure uses **Vitest** as the test runner with comprehensive configuration for React component testing.

#### Configuration Files

**`vite.config.ts` - Test Configuration Section**
```typescript
test: {
  // Environment configuration for React/DOM testing
  globals: true,
  environment: 'jsdom',
  setupFiles: './src/test/setup.ts',

  // Timeout configuration
  testTimeout: 10000,
  hookTimeout: 10000,

  // Coverage configuration
  coverage: {
    enabled: process.env.COVERAGE === 'true',
    provider: 'v8',
    reporter: ['text', 'json', 'html', 'lcov'],
    thresholds: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  }
}
```

#### Test Utilities

**`src/test/test-utils.tsx`** - Custom render wrapper
```typescript
/**
 * Custom render function that includes all necessary providers
 * with React Router v7 future flags enabled
 */
function AllTheProviders({ children, store = defaultStore }: AllTheProvidersProps) {
  return (
    <Provider store={store}>
      <ThemeProvider theme={theme}>
        <BrowserRouter
          future={{
            v7_startTransition: true,
            v7_relativeSplatPath: true
          }}
        >
          {children}
        </BrowserRouter>
      </ThemeProvider>
    </Provider>
  );
}

/**
 * Custom render method that wraps components with all required providers
 * Use this instead of the default render from @testing-library/react
 *
 * @example
 * ```tsx
 * import { renderWithProviders } from '../test/test-utils';
 *
 * test('my component test', () => {
 *   const { getByText } = renderWithProviders(<MyComponent />);
 *   expect(getByText('Hello')).toBeInTheDocument();
 * });
 * ```
 */
export function renderWithProviders(
  ui: ReactElement,
  options?: CustomRenderOptions
): ReturnType<typeof render>
```

**Key Features:**
- Redux Provider integration with configurable store
- Material-UI ThemeProvider wrapper
- React Router with v7 future flags
- TypeScript support with proper type definitions

#### Test Environment Dependencies

**`package.json` - Testing Dependencies**
```json
{
  "devDependencies": {
    "@testing-library/jest-dom": "^6.8.0",
    "@testing-library/react": "^16.3.0",
    "@testing-library/user-event": "^14.6.1",
    "@vitest/coverage-v8": "^1.6.1",
    "happy-dom": "^18.0.1",
    "jsdom": "^24.1.3",
    "msw": "^2.11.2",
    "vitest": "^1.6.0"
  }
}
```

**Test Scripts:**
- `npm run test` - Run tests once
- `npm run test:watch` - Run tests in watch mode
- `npm run test:ui` - Run tests with Vitest UI
- `npm run test:coverage` - Run tests with coverage reporting

### Test Validation System

**`src/test/utils/test-validator.ts`** - Automated test quality validation

#### TestValidator Class

The `TestValidator` class ensures all test files meet quality requirements:

```typescript
export class TestValidator {
  private static readonly REQUIRED_PASS_RATE = 85;
  private static readonly MIN_TESTS_PER_FILE = 10;

  /**
   * Validate a single test file meets requirements
   */
  static validateTestFile(filename: string, results: TestResults): boolean

  /**
   * Generate a comprehensive test report
   */
  static generateReport(allResults: Map<string, TestResults>): TestReport

  /**
   * Print formatted test report
   */
  static printReport(report: TestReport): void

  /**
   * Create a markdown report for documentation
   */
  static generateMarkdownReport(report: TestReport): string
}
```

**Quality Gates:**
- All files must have >85% pass rate
- Overall test suite must have >85% pass rate
- Execution time must be <60 seconds
- Minimum 10 tests per file (warning threshold)

#### Test Results Interface

```typescript
export interface TestResults {
  filename: string;
  total: number;
  passed: number;
  failed: number;
  skipped: number;
  passRate: number;
  failingTests: string[];
  duration: number;
}

export interface TestReport {
  totalFiles: number;
  passedFiles: number;
  failedFiles: FileReport[];
  overallTests: number;
  overallPassed: number;
  overallFailed: number;
  overallPassRate: number;
  executionTime: number;
  timestamp: string;
}
```

---

## API Service Layer

### ApiClient Class Architecture

**`src/services/api.ts`** - Centralized API client using Axios

#### Core Configuration

```typescript
class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: API_TIMEOUT,
      headers: {
        "Content-Type": "application/json",
      },
    });
  }
}
```

#### Authentication & Token Management

**Request Interceptor:**
```typescript
this.client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  }
);
```

**Response Interceptor with Auto-Refresh:**
```typescript
this.client.interceptors.response.use(
  (response) => {
    // Auto-notification for successful operations
    if (response.config.method && ['post', 'put', 'delete'].includes(response.config.method.toLowerCase())) {
      // Display success messages based on endpoint
      store.dispatch(addNotification({
        type: 'success',
        message: 'Operation completed successfully!',
        autoHide: true,
      }));
    }
    return response;
  },
  async (error) => {
    // Handle 401 Unauthorized - Token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        await tokenRefreshManager.refreshToken();
        const newToken = localStorage.getItem(AUTH_TOKEN_KEY);
        if (newToken) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return this.client(originalRequest);
        }
      } catch (refreshError) {
        // Redirect to login
        return Promise.reject(refreshError);
      }
    }
  }
);
```

#### Error Handling Strategy

**Comprehensive Error Handling:**
```typescript
// Extract error message from response
if (data?.detail) {
  // Handle Pydantic validation errors (422)
  if (Array.isArray(data.detail)) {
    const errors = data.detail.map((err: any) => {
      if (err.loc && err.msg) {
        const field = err.loc[err.loc.length - 1];
        return `${field}: ${err.msg}`;
      }
      return err.msg || err.message || 'Validation error';
    });
    errorMessage = errors.join('; ');
  }
}

// Status-specific error messages
switch (status) {
  case 400:
    errorMessage = error.config?.url?.includes('/auth/')
      ? 'Invalid credentials or request format.'
      : 'Invalid request. Please check your input.';
    break;
  case 403:
    errorMessage = error.config?.url?.includes('/admin/')
      ? 'Administrator access required.'
      : 'You do not have permission to perform this action.';
    break;
  case 404:
    const resource = error.config?.url?.split('/').filter(Boolean).pop() || 'resource';
    errorMessage = `The requested ${resource} was not found.`;
    break;
}
```

#### Core API Methods

**Authentication Methods:**
```typescript
async login(email: string, password: string): Promise<AuthResponse>
async register(data: UserRegistrationData): Promise<AuthResponse>
async refreshToken(refreshToken: string): Promise<AuthResponse>
async logout(): Promise<void>
```

**Resource Management:**
```typescript
// Lessons
async listLessons(classId?: string): Promise<Lesson[]>
async getLesson(id: string): Promise<Lesson>
async createLesson(data: Partial<Lesson>): Promise<Lesson>
async updateLesson(id: string, data: Partial<Lesson>): Promise<Lesson>
async deleteLesson(id: string): Promise<void>

// Classes
async listClasses(): Promise<ClassSummary[]>
async getClass(id: string): Promise<ClassDetails>
async createClass(data: Partial<ClassSummary>): Promise<ClassSummary>
async updateClass(id: string, data: Partial<ClassSummary>): Promise<ClassSummary>
async deleteClass(id: string): Promise<void>

// Assessments
async listAssessments(classId?: string): Promise<Assessment[]>
async createAssessment(data: Partial<Assessment>): Promise<Assessment>
async submitAssessment(assessmentId: string, data: SubmissionData): Promise<AssessmentSubmission>
```

**Gamification & Progress:**
```typescript
async getStudentXP(studentId: string): Promise<{ xp: number; level: number }>
async addXP(studentId: string, amount: number, reason: string): Promise<XPTransaction>
async getBadges(studentId?: string): Promise<Badge[]>
async getLeaderboard(classId?: string, timeframe?: "daily" | "weekly" | "monthly" | "all"): Promise<LeaderboardEntry[]>
```

**Roblox Integration:**
```typescript
async listRobloxWorlds(lessonId?: string): Promise<RobloxWorld[]>
async pushLessonToRoblox(lessonId: string): Promise<{ jobId: string; status: string }>
async getRobloxJoinUrl(classId: string): Promise<{ joinUrl: string }>
async initRobloxOAuth(): Promise<{ oauth_url: string; state: string }>
async getRobloxTemplates(category?: string, subject?: string): Promise<any[]>
```

#### Realtime Integration

**Pusher Integration:**
```typescript
async realtimeTrigger(payload: {
  channel: string;
  event?: string;
  type?: string;
  payload?: any
}): Promise<any> {
  try {
    return this.request<any>({
      method: 'POST',
      url: '/realtime/trigger',
      data: payload,
    });
  } catch (error) {
    // Silently handle realtime trigger errors to prevent console spam
    logger.warn('Realtime trigger failed (non-critical)', error);
    return { ok: true, result: { channels: {}, event_id: 'fallback' } };
  }
}
```

---

## Backend API Endpoints

### Authentication Endpoints

**`apps/backend/api/v1/endpoints/auth.py`**

#### POST `/api/v1/auth/login`

**Purpose:** Authenticate user and return JWT access token

**Request Schema:**
```python
class UserLogin(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: str
```

**Response Schema:**
```python
{
    "access_token": str,
    "token_type": "bearer",
    "expires_in": int,  # seconds
    "role": str,
    "user": {
        "id": int,
        "username": str,
        "email": str,
        "displayName": str,
        "role": str
    }
}
```

**Authentication Flow:**
1. Accept either username or email for login
2. Verify password using bcrypt
3. Generate JWT token with user data
4. Return token with user profile

**Demo Users:**
```python
fake_users_db = {
    "admin@toolboxai.com": {
        "username": "admin",
        "email": "admin@toolboxai.com",
        "hashed_password": pwd_context.hash("Admin123!"),
        "role": "admin"
    },
    "jane.smith@school.edu": {
        "username": "jane_smith",
        "email": "jane.smith@school.edu",
        "hashed_password": pwd_context.hash("Teacher123!"),
        "role": "teacher"
    },
    "alex.johnson@student.edu": {
        "username": "alex_johnson",
        "email": "alex.johnson@student.edu",
        "hashed_password": pwd_context.hash("Student123!"),
        "role": "student"
    }
}
```

#### POST `/api/v1/auth/refresh`

**Purpose:** Refresh an existing JWT token

**Authentication:** Requires valid Bearer token

**Response:** New JWT token with same user data

#### POST `/api/v1/auth/logout`

**Purpose:** Logout endpoint (token invalidation)

**Response:** Success message

### Dashboard Endpoints

#### GET `/api/v1/dashboard/overview`

**Purpose:** Get role-specific dashboard data

**Authentication:** Required

**Response Schema:**
```typescript
interface DashboardOverview {
  metrics: {
    activeUsers: number;
    completionRate: number;
    averageScore: number;
    totalHours: number;
  };
  recentActivity: Activity[];
  upcomingEvents: Event[];
  notifications: Notification[];
}
```

### Resource Management Endpoints

#### Lessons Endpoints

- `GET /api/v1/lessons` - List lessons (optional classId filter)
- `GET /api/v1/lessons/{id}` - Get lesson details
- `POST /api/v1/lessons` - Create new lesson
- `PUT /api/v1/lessons/{id}` - Update lesson
- `DELETE /api/v1/lessons/{id}` - Delete lesson

#### Classes Endpoints

- `GET /api/v1/classes/` - List all classes
- `GET /api/v1/classes/{id}` - Get class details
- `POST /api/v1/classes/` - Create new class
- `PUT /api/v1/classes/{id}` - Update class
- `DELETE /api/v1/classes/{id}` - Delete class

#### Assessments Endpoints

- `GET /api/v1/assessments/` - List assessments (optional class_id filter)
- `GET /api/v1/assessments/{id}` - Get assessment details
- `POST /api/v1/assessments/` - Create assessment
- `POST /api/v1/assessments/{id}/submit` - Submit assessment answers
- `GET /api/v1/assessments/{id}/submissions` - Get submissions
- `PUT /api/v1/assessments/{id}/publish` - Publish assessment

### Progress & Analytics Endpoints

#### Progress Tracking

- `GET /api/v1/progress/student/{studentId}` - Get student progress
- `GET /api/v1/progress/class/{classId}` - Get class progress
- `POST /api/v1/progress/update` - Update lesson progress

#### Analytics

- `GET /api/v1/analytics/weekly_xp` - Weekly XP data
- `GET /api/v1/analytics/subject_mastery` - Subject mastery levels
- `GET /api/v1/analytics/compliance/status` - Compliance status

### Gamification Endpoints

#### XP and Levels

- `GET /api/v1/gamification/xp/{studentId}` - Get student XP/level
- `POST /api/v1/gamification/xp/{studentId}` - Add XP to student

#### Badges and Achievements

- `GET /api/v1/gamification/badges` - Get available badges
- `POST /api/v1/gamification/badges/award` - Award badge to student

#### Leaderboards

- `GET /api/v1/gamification/leaderboard` - Get leaderboard data

### Roblox Integration Endpoints

#### World Management

- `GET /api/v1/roblox/worlds` - List Roblox worlds
- `POST /api/v1/roblox/push/{lessonId}` - Push lesson to Roblox
- `GET /api/v1/roblox/join/{classId}` - Get Roblox join URL

#### OAuth and Templates

- `GET /api/v1/roblox/auth/login` - Initialize Roblox OAuth
- `GET /api/v1/roblox/templates` - Get available templates
- `POST /api/v1/roblox/templates/{templateId}/create` - Create from template

#### Session Management

- `GET /api/v1/roblox/sessions` - Get active sessions
- `GET /api/v1/roblox/analytics/{worldId}` - Get world analytics
- `POST /api/v1/roblox/sync/{worldId}` - Sync world data

### Communication Endpoints

#### Messaging System

- `GET /api/v1/messages/` - List messages (folder/filters)
- `POST /api/v1/messages/` - Send message
- `GET /api/v1/messages/{id}` - Get message details
- `PUT /api/v1/messages/{id}/read` - Mark as read
- `POST /api/v1/messages/{id}/reply` - Reply to message

### Compliance Endpoints

#### Data Protection

- `GET /api/v1/compliance/status` - Get compliance status
- `POST /api/v1/compliance/consent` - Record consent
- `POST /api/v1/compliance/export-data` - Export user data (GDPR)

### WebSocket/Realtime Endpoints

#### Pusher Integration

- `POST /pusher/auth` - Authenticate Pusher channels
- `POST /realtime/trigger` - Trigger realtime events
- `POST /pusher/webhook` - Process Pusher webhooks

#### Legacy WebSocket Support

- `/ws/content` - Content generation updates
- `/ws/roblox` - Roblox environment sync
- `/ws/agent/{agent_id}` - Individual agent communication

---

## Test Patterns and Best Practices

### Component Testing Patterns

#### 1. Provider Wrapper Pattern

Always use the custom render function for component tests:

```typescript
import { renderWithProviders } from '../test/test-utils';

describe('MyComponent', () => {
  it('should render correctly', () => {
    const { getByText } = renderWithProviders(<MyComponent />);
    expect(getByText('Expected Text')).toBeInTheDocument();
  });
});
```

#### 2. Mock Store Pattern

For Redux-dependent components:

```typescript
const mockStore = configureStore({
  reducer: {
    ui: () => ({ theme: 'light', loading: false }),
    user: () => ({ currentUser: null, isAuthenticated: false }),
    dashboard: () => ({ metrics: {} }),
  },
});

renderWithProviders(<Component />, { store: mockStore });
```

#### 3. API Mocking Pattern

Use MSW for API mocking:

```typescript
import { server, addCustomHandler } from '../test/utils/msw-handlers';

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// Custom handler for specific test
addCustomHandler(
  http.get('/api/v1/custom-endpoint', () => {
    return HttpResponse.json({ data: 'test' });
  })
);
```

### Testing Strategies

#### 1. Unit Tests
- Test individual components in isolation
- Mock external dependencies
- Focus on props, state, and event handling

#### 2. Integration Tests
- Test component interactions
- Test API integration with MSW
- Test Redux state management

#### 3. End-to-End Tests
- Use Playwright for full user flows
- Test critical user journeys
- Test cross-browser compatibility

### Test Organization

```
src/
├── __tests__/           # Main test directory
│   ├── App.test.tsx     # App component tests
│   ├── components/      # Component tests
│   └── services/        # Service tests
├── test/                # Test utilities
│   ├── test-utils.tsx   # Custom render functions
│   └── utils/           # Test helpers
│       ├── msw-handlers.ts    # MSW mock handlers
│       └── test-validator.ts  # Test validation
```

### Quality Metrics

**Required Test Coverage:**
- Lines: 80%
- Functions: 80%
- Branches: 80%
- Statements: 80%

**Performance Targets:**
- Test execution: <60 seconds
- Individual test: <5 seconds
- Setup/teardown: <1 second

---

## Mock Service Worker (MSW) Configuration

### MSW Setup

**`src/test/utils/msw-handlers.ts`** - Comprehensive API mock handlers

#### Authentication Handlers

```typescript
const authHandlers = [
  // Login
  http.post(`${API_BASE}/api/v1/auth/login`, async ({ request }) => {
    const body = await request.json() as any;

    if (body.email === 'test@example.com' && body.password === 'password123') {
      return HttpResponse.json({
        token: 'mock-jwt-token',
        user: createMockUser({
          email: body.email,
          role: 'teacher',
        }),
      });
    }

    return HttpResponse.json(
      { error: 'Invalid credentials' },
      { status: 401 }
    );
  }),

  // Register
  http.post(`${API_BASE}/api/v1/auth/register`, async ({ request }) => {
    const body = await request.json() as any;

    if (body.email === 'existing@example.com') {
      return HttpResponse.json(
        { error: 'Email already registered' },
        { status: 409 }
      );
    }

    return HttpResponse.json({
      message: 'Registration successful',
      user: createMockUser(body),
    });
  }),
];
```

#### Resource Management Handlers

```typescript
const classHandlers = [
  // List Classes
  http.get(`${API_BASE}/api/v1/classes`, ({ request }) => {
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const limit = parseInt(url.searchParams.get('limit') || '10');

    const classes = Array.from({ length: limit }, (_, i) =>
      createMockClass({
        id: `class-${page}-${i}`,
        name: `Class ${page}-${i + 1}`,
      })
    );

    return HttpResponse.json({
      data: classes,
      total: 50,
      page,
      limit,
    });
  }),

  // Get Class Details
  http.get(`${API_BASE}/api/v1/classes/:id`, ({ params }) => {
    const { id } = params;

    if (id === 'not-found') {
      return HttpResponse.json(
        { error: 'Class not found' },
        { status: 404 }
      );
    }

    return HttpResponse.json(
      createMockClass({
        id: id as string,
        name: `Class ${id}`,
        studentCount: 25,
      })
    );
  }),
];
```

#### Mock Data Factories

```typescript
export function createMockUser(overrides = {}) {
  return {
    id: 1,
    username: 'testuser',
    email: 'test@example.com',
    displayName: 'Test User',
    role: 'student',
    xp: 100,
    level: 1,
    ...overrides
  };
}

export function createMockClass(overrides = {}) {
  return {
    id: '1',
    name: 'Test Class',
    subject: 'Mathematics',
    gradeLevel: 5,
    studentCount: 20,
    teacherId: '1',
    ...overrides
  };
}
```

#### Helper Functions

```typescript
/**
 * Helper function to add custom handlers for specific tests
 */
export function addCustomHandler(handler: any) {
  server.use(handler);
}

/**
 * Helper function to simulate network errors
 */
export function simulateNetworkError(endpoint: string) {
  server.use(
    http.get(`${API_BASE}${endpoint}`, () => {
      return HttpResponse.error();
    })
  );
}

/**
 * Helper function to simulate slow network
 */
export function simulateSlowNetwork(delayMs: number = 3000) {
  server.use(
    http.all('*', async ({ request }) => {
      await new Promise(resolve => setTimeout(resolve, delayMs));
      return HttpResponse.json({});
    })
  );
}
```

### MSW Server Configuration

```typescript
export const server = setupServer(...handlers);

// Test setup
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

---

## Known Issues and Workarounds

### 1. MSW Handler Issues

**Issue:** Some API endpoints not properly mocked

**Workaround:**
```typescript
// Add missing handlers dynamically in tests
addCustomHandler(
  http.get('/api/v1/missing-endpoint', () => {
    return HttpResponse.json({ data: 'fallback' });
  })
);
```

### 2. Async Testing Issues

**Issue:** Race conditions in async component updates

**Workaround:**
```typescript
// Use waitFor for async assertions
import { waitFor } from '@testing-library/react';

await waitFor(() => {
  expect(getByText('Loading...')).not.toBeInTheDocument();
});
```

### 3. Redux Store State Issues

**Issue:** State not properly reset between tests

**Workaround:**
```typescript
// Create fresh store for each test
const mockStore = configureStore({
  reducer: {
    // ... reducers
  },
});

// Or use a store factory
const createMockStore = (initialState = {}) => {
  return configureStore({
    reducer: rootReducer,
    preloadedState: initialState,
  });
};
```

### 4. Material-UI Theme Issues

**Issue:** Theme provider not available in tests

**Workaround:**
Always use `renderWithProviders` which includes ThemeProvider.

### 5. Router Context Issues

**Issue:** Components requiring router context fail

**Workaround:**
The custom render function includes BrowserRouter with v7 future flags.

### 6. Environment Variable Issues

**Issue:** Environment variables not available in tests

**Workaround:**
```typescript
// Mock config in test setup
vi.mock('../config', () => ({
  API_BASE_URL: 'http://localhost:8008',
  WS_URL: 'http://localhost:8008',
  ENABLE_WEBSOCKET: false,
}));
```

### 7. WebSocket Testing Issues

**Issue:** WebSocket connections fail in test environment

**Workaround:**
```typescript
// Mock WebSocket in tests
const mockWebSocket = {
  send: vi.fn(),
  close: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
};

global.WebSocket = vi.fn(() => mockWebSocket);
```

### 8. Test Performance Issues

**Issue:** Slow test execution due to large dependency imports

**Workaround:**
```typescript
// Use dynamic imports for heavy dependencies
const { heavyLibrary } = await import('heavy-library');

// Or mock heavy dependencies
vi.mock('heavy-library', () => ({
  default: vi.fn(),
}));
```

---

## Maintenance and Development Guidelines

### Adding New Tests

1. Use the custom `renderWithProviders` function
2. Follow the established test patterns
3. Ensure tests meet the 85% pass rate requirement
4. Add MSW handlers for new API endpoints
5. Include both positive and negative test cases

### API Integration Testing

1. Update MSW handlers when adding new endpoints
2. Test error scenarios (4xx, 5xx responses)
3. Verify request/response data transformation
4. Test authentication requirements

### Performance Monitoring

1. Use the TestValidator for automated quality checks
2. Monitor test execution times
3. Identify and optimize slow tests
4. Maintain coverage thresholds

### Debugging Test Issues

1. Use Vitest UI for interactive debugging: `npm run test:ui`
2. Enable debug logging in development
3. Check MSW network tab for request/response verification
4. Use React Developer Tools for component state inspection

This documentation provides a comprehensive guide to the ToolBoxAI-Solutions testing infrastructure and API integration patterns. It should be updated as the codebase evolves and new testing patterns emerge.
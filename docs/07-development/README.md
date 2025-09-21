# Developer Documentation

Welcome to the ToolBoxAI Solutions developer documentation. This guide provides comprehensive information for developers, system architects, and technical contributors working with the ToolBoxAI educational platform.

## Table of Contents

1. [Quick Start for Developers](#quick-start-for-developers)
2. [System Architecture](#system-architecture)
3. [Development Environment Setup](#development-environment-setup)
4. [Code Organization](#code-organization)
5. [Contributing Guidelines](#contributing-guidelines)
6. [Testing Strategies](#testing-strategies)
7. [Deployment and DevOps](#deployment-and-devops)
8. [Security Guidelines](#security-guidelines)
9. [Performance Optimization](#performance-optimization)
10. [API Development](#api-development)

## Quick Start for Developers

### Prerequisites

- **Node.js**: 18+ (for frontend development)
- **Python**: 3.11+ (for backend development)
- **PostgreSQL**: 14+ (database)
- **Redis**: 7+ (caching and sessions)
- **Git**: Latest version
- **Docker**: Optional but recommended

### 5-Minute Setup

```bash
# 1. Clone the repository
git clone https://github.com/toolboxai/solutions.git
cd toolboxai-solutions

# 2. Set up Python environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Set up Node.js dependencies
npm install
cd apps/dashboard && npm install && cd ../..

# 4. Configure environment
cp .env.example .env
cp apps/dashboard/.env.example apps/dashboard/.env.local

# 5. Start development servers
# Terminal 1: Backend
cd apps/backend && uvicorn main:app --host 127.0.0.1 --port 8009 --reload

# Terminal 2: Frontend
cd apps/dashboard && npm run dev
```

### Verification Checklist

- [ ] Backend API accessible at http://localhost:8009/docs
- [ ] Frontend dashboard at http://localhost:5179
- [ ] Health check passes: `curl http://localhost:8009/health`
- [ ] Database connected (check logs)
- [ ] Redis connected (check logs)

## System Architecture

### High-Level Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React App     │    │   FastAPI API    │    │   PostgreSQL    │
│   (Port 5179)   │◄──►│   (Port 8009)    │◄──►│   (Port 5432)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌──────────────────┐              │
         └──────────────►│      Redis       │◄─────────────┘
                        │   (Port 6379)    │
                        └──────────────────┘
                                 │
                        ┌──────────────────┐
                        │   Pusher/WS      │
                        │  (Real-time)     │
                        └──────────────────┘
```

### Core Components

#### Frontend (React + TypeScript)
- **Location**: `apps/dashboard/`
- **Tech Stack**: React 18, TypeScript, Vite, Material-UI
- **State Management**: Redux Toolkit, React Query
- **Real-time**: Pusher.js for live updates

#### Backend (FastAPI + Python)
- **Location**: `apps/backend/`
- **Tech Stack**: FastAPI, SQLAlchemy, Pydantic v2
- **AI Integration**: Anthropic Claude, OpenAI GPT
- **Real-time**: WebSocket, Pusher Channels

#### AI Agent System
- **Location**: `core/agents/`
- **Framework**: LangChain/LangGraph
- **Agents**: Content, Environment, Object, Script, Validation
- **Coordination**: SPARC framework for structured reasoning

#### Database Layer
- **Primary**: PostgreSQL with SQLAlchemy ORM
- **Caching**: Redis for sessions and temporary data
- **Migrations**: Alembic for database versioning

### Technology Stack

#### Backend Technologies
```yaml
Language: Python 3.11+
Framework: FastAPI 0.104+
ORM: SQLAlchemy 2.0 (async)
Validation: Pydantic v2
Authentication: JWT with python-jose
AI: LangChain, Anthropic, OpenAI
Real-time: WebSocket, Pusher
Testing: pytest, httpx
```

#### Frontend Technologies
```yaml
Language: TypeScript 5+
Framework: React 18
Build Tool: Vite 5
UI Library: Material-UI (MUI) 5
State: Redux Toolkit, React Query
Testing: Vitest, React Testing Library
Real-time: Pusher.js
```

#### Infrastructure
```yaml
Database: PostgreSQL 14+
Cache: Redis 7+
Message Queue: Redis (simple) / RabbitMQ (advanced)
Monitoring: Sentry (errors), custom metrics
Deployment: Docker, Kubernetes (optional)
```

## Development Environment Setup

### Detailed Setup Instructions

#### 1. Environment Configuration

**Backend Environment (`.env`)**:
```bash
# Database
DATABASE_URL=postgresql://toolboxai:dev_password@localhost/toolboxai_dev
REDIS_URL=redis://localhost:6379

# JWT Configuration
JWT_SECRET_KEY=your_very_secure_secret_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# AI Services
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Pusher (Real-time)
PUSHER_APP_ID=your_pusher_app_id
PUSHER_KEY=your_pusher_key
PUSHER_SECRET=your_pusher_secret
PUSHER_CLUSTER=us2

# Development
DEBUG=true
LOG_LEVEL=INFO
ENVIRONMENT=development
```

**Frontend Environment (`apps/dashboard/.env.local`)**:
```bash
# API Configuration
VITE_API_BASE_URL=http://127.0.0.1:8009
VITE_WS_URL=http://127.0.0.1:8009

# Real-time
VITE_PUSHER_KEY=your_pusher_key
VITE_PUSHER_CLUSTER=us2
VITE_PUSHER_AUTH_ENDPOINT=/pusher/auth

# Development
VITE_DEBUG=true
VITE_ENABLE_WEBSOCKET=true
```

#### 2. Database Setup

```bash
# Install PostgreSQL (macOS with Homebrew)
brew install postgresql
brew services start postgresql

# Create development database
createdb toolboxai_dev

# Run migrations
cd apps/backend
alembic upgrade head

# Verify database setup
alembic current
```

#### 3. IDE Configuration

**VS Code Settings (`.vscode/settings.json`)**:
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "typescript.preferences.importModuleSpecifier": "relative",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

**Recommended Extensions**:
- Python
- TypeScript and JavaScript
- Prettier - Code formatter
- ESLint
- GitLens
- Docker
- Thunder Client (API testing)

### Development Workflow

#### Daily Development Process

1. **Start Development Services**:
```bash
# Start databases
brew services start postgresql
brew services start redis

# Activate Python environment
source venv/bin/activate

# Start backend (Terminal 1)
cd apps/backend
uvicorn main:app --host 127.0.0.1 --port 8009 --reload

# Start frontend (Terminal 2)
cd apps/dashboard
npm run dev
```

2. **Development Checks**:
```bash
# Backend health check
curl http://localhost:8009/health

# Frontend build check
cd apps/dashboard && npm run build

# Type checking
npm run typecheck

# Python linting
cd apps/backend && flake8 .
```

3. **Testing**:
```bash
# Run backend tests
pytest

# Run frontend tests
cd apps/dashboard && npm test

# Run specific test file
pytest tests/test_specific.py::test_function_name -v
```

## Code Organization

### Repository Structure

```
ToolBoxAI-Solutions/
├── apps/                          # Application modules
│   ├── backend/                   # FastAPI backend
│   │   ├── api/                   # API routes and endpoints
│   │   ├── core/                  # Core business logic
│   │   ├── models/                # Database models
│   │   ├── services/              # Business services
│   │   └── main.py               # Application entry point
│   └── dashboard/                 # React frontend
│       ├── src/
│       │   ├── components/        # React components
│       │   ├── contexts/          # React contexts
│       │   ├── hooks/             # Custom hooks
│       │   ├── services/          # API clients
│       │   └── utils/             # Utilities
│       └── package.json
├── core/                          # Core platform modules
│   ├── agents/                    # AI agent system
│   ├── mcp/                       # Model Context Protocol
│   ├── sparc/                     # SPARC framework
│   └── swarm/                     # Agent coordination
├── database/                      # Database schemas and migrations
│   ├── models.py                  # SQLAlchemy models
│   ├── connection.py              # Database connection
│   └── migrations/                # Alembic migrations
├── docs/                          # Documentation
├── tests/                         # Test suites
├── infrastructure/                # Infrastructure as code
│   ├── docker/                    # Docker configurations
│   └── kubernetes/                # K8s manifests
└── scripts/                       # Utility scripts
```

### Backend Code Organization

#### API Structure (`apps/backend/api/`)
```
api/
├── v1/
│   ├── endpoints/                 # API endpoints
│   │   ├── auth.py               # Authentication
│   │   ├── ai_chat.py            # AI content generation
│   │   ├── classes.py            # Class management
│   │   ├── lessons.py            # Lesson management
│   │   └── users.py              # User management
│   └── __init__.py
└── dependencies.py                # Shared dependencies
```

#### Core Services (`apps/backend/core/`)
```
core/
├── auth/                          # Authentication logic
├── ai/                           # AI service integrations
├── config.py                     # Configuration management
├── database.py                   # Database utilities
├── security.py                   # Security utilities
└── exceptions.py                 # Custom exceptions
```

#### Models (`apps/backend/models/`)
```
models/
├── __init__.py
├── base.py                       # Base model classes
├── user.py                       # User models
├── content.py                    # Content models
└── schemas.py                    # Pydantic schemas
```

### Frontend Code Organization

#### Component Structure (`apps/dashboard/src/components/`)
```
components/
├── common/                       # Reusable components
│   ├── Button/
│   ├── Modal/
│   └── Form/
├── layout/                       # Layout components
│   ├── Header/
│   ├── Sidebar/
│   └── Footer/
├── pages/                        # Page components
│   ├── Dashboard/
│   ├── Lessons/
│   └── Profile/
└── features/                     # Feature-specific components
    ├── Auth/
    ├── ContentCreation/
    └── Analytics/
```

#### Services (`apps/dashboard/src/services/`)
```
services/
├── api.ts                        # API client configuration
├── auth.ts                       # Authentication service
├── content.ts                    # Content management
├── pusher.ts                     # Real-time service
└── types.ts                      # TypeScript type definitions
```

### Naming Conventions

#### Python (Backend)
```python
# Files and modules: snake_case
user_service.py
content_generator.py

# Classes: PascalCase
class UserService:
class ContentGenerator:

# Functions and variables: snake_case
def create_user():
user_id = "user_123"

# Constants: UPPER_SNAKE_CASE
MAX_CONTENT_LENGTH = 5000
DEFAULT_TIMEOUT = 30
```

#### TypeScript (Frontend)
```typescript
// Files: kebab-case
user-service.ts
content-generator.tsx

// Components: PascalCase
const UserProfile = () => {...}
const ContentCreator = () => {...}

// Functions and variables: camelCase
const createUser = () => {...}
const userId = "user_123"

// Constants: UPPER_SNAKE_CASE
const MAX_CONTENT_LENGTH = 5000
const DEFAULT_TIMEOUT = 30
```

## Contributing Guidelines

### Git Workflow

#### Branch Naming Convention
```bash
# Feature branches
feature/user-authentication
feature/ai-content-generation

# Bug fixes
bugfix/login-validation-error
bugfix/dashboard-loading-issue

# Hotfixes
hotfix/security-vulnerability
hotfix/critical-api-bug

# Refactoring
refactor/database-models
refactor/api-structure
```

#### Commit Message Format
```bash
# Format: type(scope): description
feat(auth): add JWT token refresh functionality
fix(dashboard): resolve student progress loading issue
docs(api): update authentication endpoint documentation
refactor(models): simplify user model relationships
test(content): add unit tests for content generation
```

#### Pull Request Process

1. **Create Feature Branch**:
```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
```

2. **Development**:
```bash
# Make your changes
git add .
git commit -m "feat(scope): descriptive message"
```

3. **Pre-PR Checklist**:
- [ ] All tests pass
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Type checking passes
- [ ] No console.log statements left
- [ ] Environment variables documented

4. **Create Pull Request**:
- Use descriptive title
- Include detailed description
- Reference related issues
- Add reviewers
- Include testing instructions

### Code Style Guidelines

#### Python Code Style
```python
# Use Black for formatting
black apps/backend/

# Follow PEP 8 guidelines
# Example: Good function with type hints
def create_user(
    email: str,
    password: str,
    role: UserRole = UserRole.STUDENT
) -> User:
    """Create a new user with the specified email and role.

    Args:
        email: User's email address
        password: Plain text password (will be hashed)
        role: User role (defaults to STUDENT)

    Returns:
        Created user instance

    Raises:
        ValueError: If email is invalid
        UserAlreadyExistsError: If user already exists
    """
    if not validate_email(email):
        raise ValueError("Invalid email format")

    existing_user = get_user_by_email(email)
    if existing_user:
        raise UserAlreadyExistsError(f"User with email {email} already exists")

    hashed_password = hash_password(password)
    return User(email=email, password_hash=hashed_password, role=role)
```

#### TypeScript Code Style
```typescript
// Use Prettier for formatting
// Example: Good component with proper typing
interface UserProfileProps {
  userId: string;
  onUpdate?: (user: User) => void;
  readonly?: boolean;
}

const UserProfile: React.FC<UserProfileProps> = ({
  userId,
  onUpdate,
  readonly = false
}) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        setLoading(true);
        const userData = await userService.getUser(userId);
        setUser(userData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, [userId]);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;
  if (!user) return <UserNotFound />;

  return (
    <div className="user-profile">
      {/* Component JSX */}
    </div>
  );
};

export default UserProfile;
```

### Documentation Requirements

#### Code Documentation
```python
# Python docstrings (Google style)
def generate_content(
    subject: str,
    grade_level: int,
    learning_objectives: List[str]
) -> ContentGenerationResult:
    """Generate educational content using AI.

    This function coordinates multiple AI agents to create comprehensive
    educational content including lessons, assessments, and 3D environments.

    Args:
        subject: Academic subject (e.g., "Mathematics", "Science")
        grade_level: Target grade level (1-12)
        learning_objectives: List of specific learning goals

    Returns:
        ContentGenerationResult containing:
            - Generated content metadata
            - Roblox environment specifications
            - Assessment questions
            - Progress tracking setup

    Raises:
        InvalidSubjectError: If subject is not supported
        AIServiceError: If AI generation fails

    Example:
        >>> result = generate_content(
        ...     subject="Mathematics",
        ...     grade_level=7,
        ...     learning_objectives=["Solve linear equations"]
        ... )
        >>> print(result.content_id)
        'content_abc123'
    """
```

```typescript
// TypeScript JSDoc comments
/**
 * Generates educational content using AI agents
 *
 * @param request - Content generation request parameters
 * @param options - Additional options for generation process
 * @returns Promise resolving to generated content result
 *
 * @example
 * ```typescript
 * const result = await generateContent({
 *   subject: 'Mathematics',
 *   gradeLevel: 7,
 *   learningObjectives: ['Solve linear equations']
 * });
 * console.log(result.contentId);
 * ```
 */
export const generateContent = async (
  request: ContentGenerationRequest,
  options?: GenerationOptions
): Promise<ContentGenerationResult> => {
  // Implementation
};
```

## Testing Strategies

### Testing Philosophy

We follow the testing pyramid approach:
- **Unit Tests (70%)**: Fast, isolated, comprehensive
- **Integration Tests (20%)**: API endpoints, database interactions
- **End-to-End Tests (10%)**: Critical user workflows

### Backend Testing

#### Unit Testing with pytest
```python
# tests/unit/test_user_service.py
import pytest
from unittest.mock import Mock, patch
from apps.backend.services.user_service import UserService
from apps.backend.models.user import User, UserRole

class TestUserService:
    def setup_method(self):
        self.user_service = UserService()

    def test_create_user_success(self):
        """Test successful user creation"""
        email = "test@example.com"
        password = "secure_password"

        user = self.user_service.create_user(email, password)

        assert user.email == email
        assert user.role == UserRole.STUDENT
        assert user.password_hash != password  # Ensure password is hashed

    def test_create_user_duplicate_email(self):
        """Test user creation with duplicate email"""
        email = "test@example.com"

        # Create first user
        self.user_service.create_user(email, "password1")

        # Attempt to create second user with same email
        with pytest.raises(UserAlreadyExistsError):
            self.user_service.create_user(email, "password2")

    @patch('apps.backend.services.user_service.send_welcome_email')
    def test_create_user_sends_welcome_email(self, mock_send_email):
        """Test that welcome email is sent on user creation"""
        user = self.user_service.create_user("test@example.com", "password")

        mock_send_email.assert_called_once_with(user.email)
```

#### API Testing
```python
# tests/integration/test_auth_api.py
import pytest
from fastapi.testclient import TestClient
from apps.backend.main import app

client = TestClient(app)

class TestAuthAPI:
    def test_login_success(self):
        """Test successful user login"""
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "correct_password"
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "test@example.com"

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "wrong_password"
        })

        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["message"]

    def test_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without token"""
        response = client.get("/api/v1/users/profile")

        assert response.status_code == 401
        assert "Authentication required" in response.json()["message"]
```

### Frontend Testing

#### Component Testing with Vitest
```typescript
// apps/dashboard/src/components/UserProfile/UserProfile.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { UserProfile } from './UserProfile';
import { userService } from '../../services/user';

// Mock the user service
vi.mock('../../services/user', () => ({
  userService: {
    getUser: vi.fn()
  }
}));

describe('UserProfile', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('displays user information when loaded', async () => {
    const mockUser = {
      id: '123',
      email: 'test@example.com',
      displayName: 'Test User',
      role: 'student'
    };

    vi.mocked(userService.getUser).mockResolvedValue(mockUser);

    render(<UserProfile userId="123" />);

    // Initially shows loading
    expect(screen.getByText('Loading...')).toBeInTheDocument();

    // Wait for user data to load
    await waitFor(() => {
      expect(screen.getByText('Test User')).toBeInTheDocument();
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
    });
  });

  it('displays error message when user fetch fails', async () => {
    vi.mocked(userService.getUser).mockRejectedValue(new Error('User not found'));

    render(<UserProfile userId="123" />);

    await waitFor(() => {
      expect(screen.getByText('User not found')).toBeInTheDocument();
    });
  });
});
```

#### Integration Testing
```typescript
// apps/dashboard/src/test/integration/auth-flow.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from '../../store';
import { App } from '../../App';

const renderApp = () => {
  return render(
    <Provider store={store}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </Provider>
  );
};

describe('Authentication Flow', () => {
  it('allows user to login and access dashboard', async () => {
    renderApp();

    // Should show login form initially
    expect(screen.getByText('Login')).toBeInTheDocument();

    // Fill in login form
    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'test@example.com' }
    });
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'password' }
    });

    // Submit login form
    fireEvent.click(screen.getByText('Sign In'));

    // Should redirect to dashboard after successful login
    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });
  });
});
```

### Test Configuration

#### pytest Configuration (`pytest.ini`)
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=apps/backend
    --cov-report=html
    --cov-report=term-missing
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests that require external services
```

#### Vitest Configuration (`apps/dashboard/vitest.config.ts`)
```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      reporter: ['text', 'html', 'lcov'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*'
      ]
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
});
```

### Running Tests

```bash
# Backend tests
cd apps/backend

# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_user_service.py

# Run with coverage
pytest --cov=apps/backend --cov-report=html

# Run only unit tests
pytest -m unit

# Frontend tests
cd apps/dashboard

# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage

# Run specific test
npm test UserProfile.test.tsx
```

## Deployment and DevOps

### Docker Development

#### Backend Dockerfile
```dockerfile
# infrastructure/docker/backend.Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY apps/backend/ ./apps/backend/
COPY core/ ./core/
COPY database/ ./database/

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8009

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8009/health || exit 1

# Start application
CMD ["uvicorn", "apps.backend.main:app", "--host", "0.0.0.0", "--port", "8009"]
```

#### Frontend Dockerfile
```dockerfile
# infrastructure/docker/frontend.Dockerfile
FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY apps/dashboard/package*.json ./
RUN npm ci --only=production

# Copy source code
COPY apps/dashboard/ .

# Build application
RUN npm run build

# Use nginx to serve static files
FROM nginx:alpine
COPY --from=0 /app/dist /usr/share/nginx/html
COPY infrastructure/docker/nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### Docker Compose for Development
```yaml
# infrastructure/docker/docker-compose.dev.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: toolboxai_dev
      POSTGRES_USER: toolboxai
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5434:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6381:6379"

  backend:
    build:
      context: ../..
      dockerfile: infrastructure/docker/backend.Dockerfile
    ports:
      - "8009:8009"
    environment:
      - DATABASE_URL=postgresql://toolboxai:dev_password@postgres:5432/toolboxai_dev
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    volumes:
      - ../../apps/backend:/app/apps/backend
    command: uvicorn apps.backend.main:app --host 0.0.0.0 --port 8009 --reload

  frontend:
    build:
      context: ../..
      dockerfile: infrastructure/docker/frontend.dev.Dockerfile
    ports:
      - "5179:5179"
    environment:
      - VITE_API_BASE_URL=http://backend:8009
    depends_on:
      - backend
    volumes:
      - ../../apps/dashboard:/app

volumes:
  postgres_data:
```

### Production Deployment

#### Environment Configuration
```bash
# Production environment variables
NODE_ENV=production
ENVIRONMENT=production
DEBUG=false

# Database (use managed service)
DATABASE_URL=postgresql://user:pass@prod-db.amazonaws.com:5432/toolboxai_prod

# Redis (use managed service)
REDIS_URL=redis://prod-redis.cache.amazonaws.com:6379

# Security
JWT_SECRET_KEY=your_production_secret_key
CORS_ORIGINS=["https://platform.toolboxai.com"]

# External Services
OPENAI_API_KEY=prod_openai_key
ANTHROPIC_API_KEY=prod_anthropic_key
PUSHER_APP_ID=prod_pusher_app_id

# Monitoring
SENTRY_DSN=your_sentry_dsn
LOG_LEVEL=WARNING
```

#### CI/CD Pipeline (GitHub Actions)
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run tests
      run: pytest

    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'

    - name: Install frontend dependencies
      run: |
        cd apps/dashboard
        npm ci

    - name: Run frontend tests
      run: |
        cd apps/dashboard
        npm test

    - name: Build frontend
      run: |
        cd apps/dashboard
        npm run build

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v3

    - name: Deploy to production
      run: |
        # Your deployment script here
        echo "Deploying to production..."
```

## Security Guidelines

### Authentication Security

#### JWT Implementation
```python
# apps/backend/core/auth/jwt.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = settings.jwt_secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token with expiration."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return payload
    except JWTError:
        return None

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)
```

### Input Validation

#### Backend Validation with Pydantic
```python
# apps/backend/models/schemas.py
from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional
from enum import Enum

class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    role: UserRole = UserRole.STUDENT
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)

    @validator('password')
    def validate_password(cls, v):
        """Ensure password meets security requirements."""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class ContentGenerationRequest(BaseModel):
    subject: str = Field(..., min_length=1, max_length=100)
    grade_level: int = Field(..., ge=1, le=12)
    learning_objectives: List[str] = Field(..., min_items=1, max_items=10)
    duration_minutes: Optional[int] = Field(30, ge=5, le=120)

    @validator('learning_objectives')
    def validate_objectives(cls, v):
        """Ensure learning objectives are not empty."""
        for obj in v:
            if not obj.strip():
                raise ValueError('Learning objectives cannot be empty')
        return v
```

#### Frontend Validation
```typescript
// apps/dashboard/src/utils/validation.ts
import { z } from 'zod';

export const userCreateSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/\d/, 'Password must contain at least one number'),
  role: z.enum(['student', 'teacher', 'admin']),
  firstName: z.string().min(1, 'First name is required'),
  lastName: z.string().min(1, 'Last name is required')
});

export const contentGenerationSchema = z.object({
  subject: z.string().min(1, 'Subject is required'),
  gradeLevel: z.number().min(1).max(12),
  learningObjectives: z
    .array(z.string().min(1))
    .min(1, 'At least one learning objective is required')
    .max(10, 'Maximum 10 learning objectives allowed'),
  durationMinutes: z.number().min(5).max(120).optional()
});

export type UserCreateData = z.infer<typeof userCreateSchema>;
export type ContentGenerationData = z.infer<typeof contentGenerationSchema>;
```

### SQL Injection Prevention

```python
# Good: Using SQLAlchemy ORM with parameterized queries
def get_user_by_email(email: str) -> Optional[User]:
    return session.query(User).filter(User.email == email).first()

# Good: Using text() with bound parameters for complex queries
from sqlalchemy import text

def get_student_progress(student_id: str, subject: str) -> List[Progress]:
    query = text("""
        SELECT p.* FROM progress p
        JOIN lessons l ON p.lesson_id = l.id
        WHERE p.student_id = :student_id AND l.subject = :subject
    """)
    return session.execute(query, {
        'student_id': student_id,
        'subject': subject
    }).fetchall()

# Bad: String concatenation (NEVER DO THIS)
# def get_user_by_email(email: str):
#     query = f"SELECT * FROM users WHERE email = '{email}'"
#     return session.execute(query)
```

### XSS Prevention

```typescript
// Frontend XSS prevention
import DOMPurify from 'dompurify';

// Sanitize HTML content before rendering
const SanitizedContent: React.FC<{ content: string }> = ({ content }) => {
  const sanitizedContent = DOMPurify.sanitize(content);

  return (
    <div
      dangerouslySetInnerHTML={{ __html: sanitizedContent }}
    />
  );
};

// Always validate and sanitize user input
const handleSubmit = (formData: FormData) => {
  const sanitizedData = {
    title: DOMPurify.sanitize(formData.title),
    description: DOMPurify.sanitize(formData.description),
    // ... other fields
  };

  submitContent(sanitizedData);
};
```

## Performance Optimization

### Backend Optimization

#### Database Query Optimization
```python
# Use eager loading to prevent N+1 queries
def get_classes_with_students(teacher_id: str) -> List[Class]:
    return session.query(Class)\
        .options(joinedload(Class.students))\
        .filter(Class.teacher_id == teacher_id)\
        .all()

# Use pagination for large result sets
def get_lessons_paginated(offset: int = 0, limit: int = 20) -> List[Lesson]:
    return session.query(Lesson)\
        .offset(offset)\
        .limit(limit)\
        .all()

# Use database indexes for frequently queried fields
class User(Base):
    __tablename__ = "users"

    email = Column(String, unique=True, index=True)  # Index for login queries
    role = Column(Enum(UserRole), index=True)        # Index for role-based queries
    created_at = Column(DateTime, index=True)        # Index for date range queries
```

#### Caching Implementation
```python
# apps/backend/core/cache.py
from functools import wraps
import redis
import json
from typing import Any, Callable, Optional

redis_client = redis.Redis.from_url(settings.redis_url)

def cache_result(
    key_prefix: str,
    expiration: int = 300,  # 5 minutes default
    serialize_json: bool = True
):
    """Decorator to cache function results in Redis."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Generate cache key
            cache_key = f"{key_prefix}:{hash(str(args) + str(kwargs))}"

            # Try to get from cache
            cached_result = redis_client.get(cache_key)
            if cached_result:
                if serialize_json:
                    return json.loads(cached_result)
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            if serialize_json:
                redis_client.setex(cache_key, expiration, json.dumps(result))
            else:
                redis_client.setex(cache_key, expiration, result)

            return result
        return wrapper
    return decorator

# Usage example
@cache_result("dashboard_stats", expiration=300)
def get_dashboard_stats(user_id: str, role: str) -> dict:
    """Get dashboard statistics with caching."""
    # Expensive database queries here
    return {
        "total_students": get_student_count(user_id),
        "active_classes": get_active_classes(user_id),
        "recent_activity": get_recent_activity(user_id)
    }
```

### Frontend Optimization

#### Code Splitting and Lazy Loading
```typescript
// apps/dashboard/src/App.tsx
import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import { LoadingSpinner } from './components/common/LoadingSpinner';

// Lazy load page components
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Lessons = lazy(() => import('./pages/Lessons'));
const ContentCreator = lazy(() => import('./pages/ContentCreator'));
const Analytics = lazy(() => import('./pages/Analytics'));

const App = () => {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/lessons" element={<Lessons />} />
        <Route path="/create" element={<ContentCreator />} />
        <Route path="/analytics" element={<Analytics />} />
      </Routes>
    </Suspense>
  );
};
```

#### React Query for Data Fetching
```typescript
// apps/dashboard/src/hooks/useUserData.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { userService } from '../services/user';

export const useUserProfile = (userId: string) => {
  return useQuery({
    queryKey: ['user', userId],
    queryFn: () => userService.getUser(userId),
    staleTime: 5 * 60 * 1000, // Consider data fresh for 5 minutes
    cacheTime: 10 * 60 * 1000, // Keep in cache for 10 minutes
  });
};

export const useUpdateUser = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: userService.updateUser,
    onSuccess: (updatedUser) => {
      // Update the cache with the new user data
      queryClient.setQueryData(['user', updatedUser.id], updatedUser);

      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
};
```

#### Performance Monitoring
```typescript
// apps/dashboard/src/utils/performance.ts
export const measurePerformance = (name: string, fn: () => void) => {
  performance.mark(`${name}-start`);
  fn();
  performance.mark(`${name}-end`);
  performance.measure(name, `${name}-start`, `${name}-end`);

  const measure = performance.getEntriesByName(name)[0];
  console.log(`${name} took ${measure.duration.toFixed(2)}ms`);
};

// Usage in components
useEffect(() => {
  measurePerformance('dashboard-load', () => {
    // Component initialization logic
  });
}, []);
```

## API Development

### FastAPI Best Practices

#### Router Organization
```python
# apps/backend/api/v1/endpoints/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from apps.backend.api.dependencies import get_db, get_current_user
from apps.backend.models.schemas import User, UserCreate, UserUpdate
from apps.backend.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new user (admin only)."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create users"
        )

    user_service = UserService(db)
    return await user_service.create_user(user_data)

@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user by ID."""
    user_service = UserService(db)
    user = await user_service.get_user(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Users can only see their own data unless they're admin
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return user

@router.get("/", response_model=List[User])
async def list_users(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List users with pagination (admin only)."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can list users"
        )

    user_service = UserService(db)
    return await user_service.list_users(skip=skip, limit=limit)
```

#### Error Handling
```python
# apps/backend/core/exceptions.py
from fastapi import HTTPException, status

class ToolBoxAIException(Exception):
    """Base exception for ToolBoxAI application."""
    pass

class UserNotFoundError(ToolBoxAIException):
    """Raised when a user is not found."""
    pass

class InsufficientPermissionsError(ToolBoxAIException):
    """Raised when user lacks required permissions."""
    pass

class ContentGenerationError(ToolBoxAIException):
    """Raised when AI content generation fails."""
    pass

# Exception handlers
def user_not_found_handler(request, exc: UserNotFoundError):
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )

def insufficient_permissions_handler(request, exc: InsufficientPermissionsError):
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Insufficient permissions"
    )

def content_generation_handler(request, exc: ContentGenerationError):
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Content generation failed"
    )
```

#### Dependency Injection
```python
# apps/backend/api/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import Optional

from apps.backend.core.database import get_db_session
from apps.backend.core.auth.jwt import verify_token
from apps.backend.services.user_service import UserService

security = HTTPBearer()

async def get_db() -> Session:
    """Get database session."""
    async with get_db_session() as session:
        yield session

async def get_current_user(
    token: str = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    payload = verify_token(token.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    user_service = UserService(db)
    user = await user_service.get_user_by_email(payload.get("sub"))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user

def require_role(required_role: str):
    """Dependency to require specific user role."""
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        return current_user
    return role_checker

# Usage in endpoints
@router.post("/admin-only")
async def admin_endpoint(
    current_user: User = Depends(require_role("admin"))
):
    """Endpoint that requires admin role."""
    # Implementation here
```

---

## Additional Resources

### Learning Resources
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **React Documentation**: https://react.dev/
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/
- **Pydantic Documentation**: https://docs.pydantic.dev/
- **TypeScript Documentation**: https://www.typescriptlang.org/docs/

### Development Tools
- **API Testing**: Postman, Insomnia, Thunder Client (VS Code)
- **Database Management**: pgAdmin, TablePlus, DBeaver
- **Code Quality**: Black (Python), Prettier (TypeScript), ESLint
- **Debugging**: pdb (Python), React DevTools, Redux DevTools

### Community and Support
- **GitHub Repository**: https://github.com/toolboxai/solutions
- **Developer Discord**: https://discord.gg/toolboxai-dev
- **Stack Overflow**: Tag questions with `toolboxai`
- **Internal Wiki**: Confluence/Notion for team documentation

---

**Developer Documentation Version**: 2.0.0
**Last Updated**: January 2025
**Platform Compatibility**: All supported versions

*This documentation is maintained by the ToolBoxAI development team and updated with each major release.*
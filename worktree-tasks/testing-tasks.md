# Testing & Quality Assurance Worktree Tasks
**Branch**: development-infrastructure-dashboard
**Ports**: Backend(8017), Dashboard(5188), MCP(9885), Coordinator(8896)

## 🚨 CRITICAL: 2025 Implementation Standards

**MANDATORY**: Read and follow `2025-IMPLEMENTATION-STANDARDS.md` before writing ANY code!

**Requirements**:
- ✅ Vitest 3.2.4 for frontend testing
- ✅ Pytest with async support for backend
- ✅ Playwright 1.49.0 for E2E testing
- ✅ React Testing Library 16.0.0
- ✅ Coverage targets: >80% for all code
- ✅ Auto-accept enabled for corrections
- ❌ NO deprecated testing patterns or old Jest configurations

## Primary Objectives

### 1. **Comprehensive Testing Strategy**
   - Frontend unit testing with Vitest
   - Backend unit testing with Pytest
   - Integration testing across services
   - End-to-end testing with Playwright
   - Performance testing and benchmarking
   - Security testing and vulnerability scanning

### 2. **Test Automation & CI/CD**
   - Automated test execution in pipelines
   - Pre-commit hooks for quick validation
   - Test result reporting and tracking
   - Code coverage enforcement
   - Continuous quality monitoring

### 3. **Quality Assurance**
   - Code quality metrics and analysis
   - Performance benchmarking
   - Accessibility testing (WCAG 2.1 AA)
   - Security vulnerability scanning
   - API contract testing

### 4. **Test Infrastructure**
   - Test data management and fixtures
   - Mock services and test doubles
   - Test environment configuration
   - Parallel test execution
   - Test result visualization

## Current Tasks

### Phase 1: Frontend Testing Infrastructure (Priority: HIGH)
- [ ] Review existing frontend tests in `apps/dashboard/src/__tests__/`
- [ ] Setup Vitest 3.2.4 configuration
- [ ] Configure React Testing Library 16.0.0
- [ ] Create test utilities and helpers
- [ ] Setup coverage reporting (>80% target)
- [ ] Add accessibility testing with axe-core
- [ ] Configure Playwright for E2E tests
- [ ] Create test data factories

### Phase 2: Backend Testing Infrastructure (Priority: HIGH)
- [ ] Review existing backend tests in `tests/`
- [ ] Setup pytest with async support (pytest-asyncio)
- [ ] Configure test database isolation
- [ ] Create API test fixtures
- [ ] Setup coverage reporting (>80% target)
- [ ] Add security testing with Bandit
- [ ] Create mock external services
- [ ] Add performance benchmarks

### Phase 3: Frontend Unit Tests (Priority: HIGH)

#### Component Testing
- [ ] Test all Mantine components
- [ ] Test React 19 hooks and patterns
- [ ] Test Zustand stores
- [ ] Test React Query hooks
- [ ] Test Pusher integration hooks
- [ ] Test form validation
- [ ] Test error boundaries
- [ ] Test routing and navigation

#### Service Testing
- [ ] Test API client services
- [ ] Test authentication services
- [ ] Test data transformation utilities
- [ ] Test helper functions
- [ ] Test custom hooks
- [ ] Test context providers
- [ ] Test state management

### Phase 4: Backend Unit Tests (Priority: HIGH)

#### API Endpoint Testing
- [ ] Test all REST endpoints
- [ ] Test authentication/authorization
- [ ] Test request validation
- [ ] Test response formatting
- [ ] Test error handling
- [ ] Test rate limiting
- [ ] Test CORS configuration
- [ ] Test file uploads

#### Service Layer Testing
- [ ] Test business logic services
- [ ] Test database operations
- [ ] Test cache operations (Redis)
- [ ] Test Pusher event triggers
- [ ] Test background tasks
- [ ] Test email services
- [ ] Test external API integrations
- [ ] Test data transformations

#### Database Testing
- [ ] Test SQLAlchemy 2.0 models
- [ ] Test async database sessions
- [ ] Test migrations (up/down)
- [ ] Test constraints and validations
- [ ] Test relationships and joins
- [ ] Test query optimization
- [ ] Test transaction handling
- [ ] Test data integrity

### Phase 5: Integration Testing (Priority: HIGH)
- [ ] Test frontend-backend integration
- [ ] Test authentication flow end-to-end
- [ ] Test real-time features (Pusher)
- [ ] Test database transactions
- [ ] Test file upload/download flows
- [ ] Test API error handling
- [ ] Test caching layer integration
- [ ] Test external service integration

### Phase 6: E2E Testing with Playwright (Priority: MEDIUM)
- [ ] Setup Playwright 1.49.0 configuration
- [ ] Create page object models
- [ ] Test user authentication flows
- [ ] Test dashboard navigation
- [ ] Test content creation workflows
- [ ] Test real-time updates
- [ ] Test responsive design
- [ ] Test cross-browser compatibility
- [ ] Add visual regression testing
- [ ] Test accessibility features

### Phase 7: Performance Testing (Priority: MEDIUM)
- [ ] Setup performance benchmarking
- [ ] Test API response times
- [ ] Test database query performance
- [ ] Test frontend rendering performance
- [ ] Test bundle size and loading
- [ ] Test memory usage
- [ ] Test concurrent user handling
- [ ] Create performance baselines
- [ ] Add performance regression detection

### Phase 8: Security Testing (Priority: HIGH)
- [ ] Setup security scanning (Bandit, ESLint security)
- [ ] Test authentication bypass attempts
- [ ] Test authorization edge cases
- [ ] Test SQL injection protection
- [ ] Test XSS prevention
- [ ] Test CSRF protection
- [ ] Test rate limiting effectiveness
- [ ] Test data encryption
- [ ] Test secrets management
- [ ] Scan for vulnerable dependencies

### Phase 9: Accessibility Testing (Priority: MEDIUM)
- [ ] Setup axe-core for automated testing
- [ ] Test keyboard navigation
- [ ] Test screen reader compatibility
- [ ] Test ARIA labels and roles
- [ ] Test color contrast ratios
- [ ] Test focus management
- [ ] Test form accessibility
- [ ] Test semantic HTML
- [ ] Create accessibility report
- [ ] Fix WCAG 2.1 AA violations

### Phase 10: Test Automation & CI/CD (Priority: HIGH)
- [ ] Configure GitHub Actions for tests
- [ ] Setup pre-commit hooks
- [ ] Add commit message linting
- [ ] Configure coverage gates
- [ ] Setup parallel test execution
- [ ] Add test result reporting
- [ ] Configure automatic retries
- [ ] Setup test environment matrix
- [ ] Add performance benchmarking to CI
- [ ] Create test documentation

## File Locations

### Frontend Tests
- **Unit Tests**: `apps/dashboard/src/__tests__/`
  - `components/` - Component tests
  - `hooks/` - Custom hook tests
  - `services/` - Service layer tests
  - `stores/` - State management tests
  - `utils/` - Utility function tests
- **E2E Tests**: `apps/dashboard/e2e/`
- **Test Utilities**: `apps/dashboard/src/test/`
- **Configuration**: `apps/dashboard/vitest.config.ts`, `playwright.config.ts`

### Backend Tests
- **Unit Tests**: `tests/unit/`
  - `api/` - Endpoint tests
  - `services/` - Service layer tests
  - `database/` - Database tests
  - `models/` - Model tests
- **Integration Tests**: `tests/integration/`
- **Fixtures**: `tests/fixtures/`
- **Configuration**: `pytest.ini`, `tests/conftest.py`

### Shared Test Resources
- **Test Data**: `tests/data/`
- **Mocks**: `tests/mocks/`
- **Scripts**: `tests/scripts/`

## Technology Stack (2025)

### Frontend Testing
```json
{
  "vitest": "^3.2.4",
  "@testing-library/react": "^16.0.0",
  "@testing-library/user-event": "^14.5.0",
  "@testing-library/jest-dom": "^6.6.3",
  "@playwright/test": "^1.49.0",
  "@axe-core/playwright": "^4.10.0",
  "msw": "^2.6.8"
}
```

### Backend Testing
```python
dependencies = {
    "pytest": "^8.3.4",
    "pytest-asyncio": "^0.24.0",
    "pytest-cov": "^6.0.0",
    "pytest-mock": "^3.14.0",
    "httpx": "^0.28.1",
    "faker": "^30.8.0",
    "factory-boy": "^3.3.0",
}
```

### Quality & Security
```json
{
  "eslint": "^9.35.0",
  "prettier": "^3.4.0",
  "bandit": "^1.8.0",
  "safety": "^3.2.11",
  "lighthouse-ci": "^0.14.0"
}
```

## Modern Testing Patterns (2025)

### Vitest Component Test
```typescript
// ✅ CORRECT - Vitest 3.2.4 with React Testing Library
import { describe, it, expect, vi } from 'vitest';
import { render, screen, userEvent } from '@/test/utils';
import { DashboardCard } from './DashboardCard';

describe('DashboardCard', () => {
  it('renders with correct data', () => {
    render(<DashboardCard title="Users" value={1234} change={12.5} />);

    expect(screen.getByText('Users')).toBeInTheDocument();
    expect(screen.getByText('1234')).toBeInTheDocument();
    expect(screen.getByText('+12.5% from last month')).toBeInTheDocument();
  });

  it('calls onAdd when button clicked', async () => {
    const user = userEvent.setup();
    const onAdd = vi.fn();

    render(<DashboardCard title="Users" value={1234} change={12.5} onAdd={onAdd} />);

    await user.click(screen.getByRole('button', { name: /add/i }));
    expect(onAdd).toHaveBeenCalledOnce();
  });

  it('handles loading state', () => {
    render(<DashboardCard title="Users" value={1234} change={12.5} loading />);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });
});
```

### Pytest Async Test
```python
# ✅ CORRECT - Pytest with async support
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_create_user(client: AsyncClient, db: AsyncSession):
    """Test user creation endpoint."""
    response = await client.post(
        "/api/v1/users",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "SecurePass123!"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "password" not in data  # Ensure password not leaked

@pytest.mark.asyncio
async def test_user_authentication(client: AsyncClient, user_factory):
    """Test user authentication flow."""
    user = await user_factory.create()

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "password"}
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
```

### Playwright E2E Test
```typescript
// ✅ CORRECT - Playwright 1.49.0 E2E testing
import { test, expect } from '@playwright/test';

test.describe('User Authentication', () => {
  test('should login successfully', async ({ page }) => {
    await page.goto('/login');

    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'SecurePass123!');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('h1')).toContainText('Dashboard');
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/login');

    await page.fill('[name="email"]', 'wrong@example.com');
    await page.fill('[name="password"]', 'wrongpass');
    await page.click('button[type="submit"]');

    await expect(page.locator('[role="alert"]')).toContainText('Invalid credentials');
  });
});
```

### Mock Service Worker (MSW)
```typescript
// ✅ CORRECT - MSW 2.6.8 for API mocking
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

export const handlers = [
  http.get('/api/v1/users/me', () => {
    return HttpResponse.json({
      id: 1,
      email: 'test@example.com',
      username: 'testuser'
    });
  }),

  http.post('/api/v1/auth/login', async ({ request }) => {
    const body = await request.json();

    if (body.email === 'test@example.com' && body.password === 'password') {
      return HttpResponse.json({ access_token: 'mock-token' });
    }

    return HttpResponse.json(
      { message: 'Invalid credentials' },
      { status: 401 }
    );
  }),
];

export const server = setupServer(...handlers);
```

### Test Fixtures (Pytest)
```python
# ✅ CORRECT - Pytest fixtures with factories
import pytest
from factory import Factory, Faker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

@pytest.fixture
async def db() -> AsyncSession:
    """Provide async database session for tests."""
    engine = create_async_engine("postgresql+asyncpg://test:test@localhost/test_db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

    await engine.dispose()

class UserFactory(Factory):
    class Meta:
        model = User

    email = Faker('email')
    username = Faker('user_name')
    password = 'password'

@pytest.fixture
def user_factory(db: AsyncSession):
    """Provide user factory."""
    async def create(**kwargs):
        user = UserFactory.build(**kwargs)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    return create
```

## Commands

### Frontend Testing
```bash
cd apps/dashboard

# Run all tests
npm run test

# Watch mode
npm run test:watch

# Coverage report
npm run test:coverage

# E2E tests
npm run test:e2e

# E2E with UI
npm run test:e2e:ui

# Accessibility tests
npm run test:a11y

# Visual regression tests
npm run test:visual
```

### Backend Testing
```bash
# Run all tests
pytest

# Watch mode
pytest-watch

# Coverage report
pytest --cov=apps/backend --cov-report=html

# Specific test file
pytest tests/unit/test_auth.py

# Specific test function
pytest tests/unit/test_auth.py::test_login

# Run only async tests
pytest -m asyncio

# Run with verbose output
pytest -vv

# Run with debugging
pytest -s --pdb
```

### Security & Quality
```bash
# Security scanning
bandit -r apps/backend
safety check
npm audit

# Linting
npm run lint
ruff check apps/backend

# Type checking
npm run typecheck
mypy apps/backend

# Performance benchmarking
pytest tests/benchmarks/ --benchmark-only
lighthouse-ci autorun
```

## Performance Targets

- **Frontend Tests**: < 30s for full suite
- **Backend Tests**: < 60s for full suite
- **E2E Tests**: < 5 minutes for critical paths
- **Code Coverage**: > 80% for all codebases
- **Test Reliability**: > 99% pass rate
- **Accessibility**: WCAG 2.1 AA compliance
- **Performance**: Lighthouse score > 90

## Success Metrics

- ✅ >80% code coverage on frontend
- ✅ >80% code coverage on backend
- ✅ All critical user flows have E2E tests
- ✅ Zero high-severity security vulnerabilities
- ✅ WCAG 2.1 AA accessibility compliance
- ✅ All tests passing in CI/CD
- ✅ Performance baselines established
- ✅ Test documentation complete
- ✅ Automated test execution in place
- ✅ Quality gates enforced

---

**REMEMBER**: Use ONLY 2025 testing frameworks and patterns. Auto-accept is enabled. Modern testing only!

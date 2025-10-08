# 2025 Implementation Standards

**Last Updated**: October 2025
**Project**: ToolboxAI Solutions Testing Infrastructure
**Required Reading**: All developers MUST read this before writing code

## 🎯 Core Principle

**ONLY use 2025 official implementation methods from authoritative source documentation.**

## 📚 Official Documentation Sources

### Frontend (React/TypeScript)
- **React 19.1.0**: https://react.dev/
- **TypeScript 5.5+**: https://www.typescriptlang.org/docs/
- **Vite 6.x**: https://vite.dev/guide/
- **Vitest 3.x**: https://vitest.dev/guide/
- **Playwright 1.49+**: https://playwright.dev/docs/intro
- **Testing Library**: https://testing-library.com/docs/react-testing-library/intro

### Backend (Python/FastAPI)
- **Python 3.12**: https://docs.python.org/3/
- **FastAPI**: https://fastapi.tiangolo.com/
- **Pytest**: https://docs.pytest.org/
- **SQLAlchemy 2.0**: https://docs.sqlalchemy.org/
- **Pydantic v2**: https://docs.pydantic.dev/

## 🚫 Forbidden Patterns

### ❌ NO Legacy Code
- Jest (replaced by Vitest)
- React 18 patterns (use React 19)
- Class components (use functional components)
- SQLAlchemy 1.x patterns (use 2.0)
- Pydantic v1 validators (use v2 field_validator)
- Old decorator syntax (use modern decorators)

### ❌ NO Deprecated APIs
- React.FC type (deprecated)
- useEffect without cleanup for subscriptions
- SQLAlchemy declarative_base (use DeclarativeBase)
- Pydantic Config class (use ConfigDict)
- @validator (use @field_validator)

### ❌ NO Outdated Tutorials
- Medium articles from 2020-2023
- Stack Overflow answers without version checks
- YouTube tutorials pre-2025
- Unmaintained blog posts

## ✅ Required Patterns

### React 19 (Functional Components Only)
```typescript
// ✅ CORRECT - React 19 functional component
import { useState, useEffect } from 'react';

interface Props {
  title: string;
  onSave: (data: string) => void;
}

export function MyComponent({ title, onSave }: Props) {
  const [data, setData] = useState('');

  useEffect(() => {
    // Effect logic
    return () => {
      // Cleanup
    };
  }, []);

  return (
    <div>
      <h1>{title}</h1>
      <button onClick={() => onSave(data)}>Save</button>
    </div>
  );
}

// ❌ WRONG - React.FC is deprecated
export const MyComponent: React.FC<Props> = ({ title }) => {
  // Don't use React.FC
};

// ❌ WRONG - Class components are legacy
class MyComponent extends React.Component {
  // Don't use class components
}
```

### TypeScript 5.5+ Strict Mode
```typescript
// ✅ CORRECT - Proper type annotations
function processData(items: string[]): Promise<string[]> {
  return Promise.resolve(items.filter(Boolean));
}

// ❌ WRONG - Any type defeats TypeScript
function processData(items: any): any {
  // Don't use 'any'
}
```

### Vitest 3.2+ Testing
```typescript
// ✅ CORRECT - Vitest 3.x syntax
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

describe('MyComponent', () => {
  it('handles user interaction', async () => {
    const user = userEvent.setup();
    const onSave = vi.fn();

    render(<MyComponent title="Test" onSave={onSave} />);

    await user.click(screen.getByRole('button', { name: /save/i }));

    expect(onSave).toHaveBeenCalledOnce();
  });
});

// ❌ WRONG - Jest syntax (legacy)
test('handles click', () => {
  // Don't use Jest
});
```

### Playwright 1.49+ E2E Testing
```typescript
// ✅ CORRECT - Playwright modern API
import { test, expect } from '@playwright/test';

test('user can login', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[name="email"]', 'user@example.com');
  await page.fill('[name="password"]', 'password');
  await page.click('button[type="submit"]');

  await expect(page).toHaveURL('/dashboard');
});

// ❌ WRONG - Old Selenium patterns
// Don't use Selenium-style selectors
```

### Python 3.12 Type Hints
```python
# ✅ CORRECT - Modern type hints
from typing import Optional
from collections.abc import Sequence

def process_items(items: Sequence[str]) -> list[str]:
    """Process items with modern type hints."""
    return [item.upper() for item in items if item]

async def fetch_data(user_id: int) -> Optional[dict[str, str]]:
    """Async function with proper return type."""
    # Implementation
    return None

# ❌ WRONG - Old typing module
from typing import List, Dict  # Use list[], dict[] instead
```

### FastAPI Async Patterns
```python
# ✅ CORRECT - FastAPI async endpoint
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

router = APIRouter()

class UserCreate(BaseModel):
    email: str
    username: str

@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    """Create new user with async database."""
    # Async implementation
    return {"id": "user-123"}

# ❌ WRONG - Synchronous endpoint
@router.post("/users")
def create_user(user_data: UserCreate):
    # Don't use sync endpoints for I/O
    pass
```

### SQLAlchemy 2.0 Patterns
```python
# ✅ CORRECT - SQLAlchemy 2.0 declarative
from sqlalchemy import String, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    username: Mapped[str] = mapped_column(String(100))

# ❌ WRONG - SQLAlchemy 1.x patterns
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()  # Don't use old declarative_base

class User(Base):
    id = Column(Integer, primary_key=True)  # Don't use Column
```

### Pydantic v2 Validation
```python
# ✅ CORRECT - Pydantic v2 patterns
from pydantic import BaseModel, ConfigDict, field_validator

class UserSettings(BaseModel):
    model_config = ConfigDict(from_attributes=True, strict=True)

    email: str
    age: int

    @field_validator('email')
    @classmethod
    def validate_email(cls, value: str) -> str:
        if '@' not in value:
            raise ValueError('Invalid email')
        return value.lower()

# ❌ WRONG - Pydantic v1 patterns
class UserSettings(BaseModel):
    class Config:  # Don't use Config class
        orm_mode = True

    @validator('email')  # Don't use @validator
    def validate_email(cls, v):
        pass
```

### Pytest Async Testing
```python
# ✅ CORRECT - Pytest with async support
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    """Test user creation endpoint."""
    response = await client.post(
        "/api/v1/users",
        json={"email": "test@example.com", "username": "testuser"}
    )

    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"

# ❌ WRONG - Sync test for async code
def test_create_user():
    # Don't use sync tests for async endpoints
    pass
```

## 🔧 Testing Standards

### Unit Tests
- **Framework**: Vitest 3.2+ (frontend), Pytest (backend)
- **Coverage**: Minimum 80% for all code
- **Mocking**: MSW 2.x for API mocking, vi.fn() for functions
- **Assertions**: Specific, descriptive assertions

### Integration Tests
- **Database**: Use test database with fixtures
- **API**: Test full request/response cycle
- **Auth**: Test authentication flows
- **Cache**: Test Redis operations

### E2E Tests
- **Framework**: Playwright 1.49+
- **Browsers**: Chromium, Firefox, WebKit
- **Selectors**: Use accessible selectors (role, label)
- **Assertions**: Wait for conditions with expect()

### Accessibility Tests
- **Framework**: @axe-core/playwright
- **Standard**: WCAG 2.1 AA compliance
- **Coverage**: All user-facing pages
- **Automation**: Run in CI/CD pipeline

## 📊 Quality Gates

### Required Before Commit
- ✅ All tests passing
- ✅ Type checking passing (tsc --noEmit)
- ✅ Linting passing (ESLint 9)
- ✅ Code coverage >80%
- ✅ No console errors

### Required Before Merge
- ✅ All CI/CD checks passing
- ✅ E2E tests passing
- ✅ Accessibility tests passing
- ✅ Performance benchmarks met
- ✅ Code review approved

## 🚀 Performance Standards

### Frontend
- **Bundle Size**: < 500KB initial load
- **FCP**: < 1.8s (First Contentful Paint)
- **LCP**: < 2.5s (Largest Contentful Paint)
- **TTI**: < 3.8s (Time to Interactive)
- **Lighthouse**: Score > 90

### Backend
- **API Response**: < 200ms (p95)
- **Database Query**: < 100ms (p95)
- **Memory Usage**: < 512MB per process
- **CPU Usage**: < 70% under load

### Testing
- **Unit Tests**: < 30s total
- **Integration Tests**: < 60s total
- **E2E Tests**: < 5min critical paths
- **Test Reliability**: > 99% pass rate

## 🔒 Security Standards

### Code Security
- ✅ No hardcoded secrets
- ✅ Input validation on all endpoints
- ✅ SQL injection protection
- ✅ XSS prevention
- ✅ CSRF protection

### Dependency Security
- ✅ Regular security audits (npm audit, safety)
- ✅ Automated dependency updates
- ✅ Vulnerability scanning in CI/CD
- ✅ No high-severity vulnerabilities

## 📝 Documentation Standards

### Code Comments
```typescript
// ✅ CORRECT - Explain WHY, not WHAT
// Cache user preferences to reduce API calls
const preferences = useMemo(() => loadPreferences(), [userId]);

// ❌ WRONG - State the obvious
// Set the user name
const name = user.name;
```

### Function Documentation
```typescript
/**
 * Fetches user data from the API with caching.
 *
 * @param userId - Unique user identifier
 * @returns User data or null if not found
 * @throws {ApiError} If network request fails
 */
async function fetchUser(userId: string): Promise<User | null> {
  // Implementation
}
```

### Test Documentation
```typescript
it('should invalidate cache when user logs out', async () => {
  // Arrange
  const user = userEvent.setup();
  render(<Dashboard />);

  // Act
  await user.click(screen.getByRole('button', { name: /logout/i }));

  // Assert
  expect(localStorage.getItem('cache')).toBeNull();
});
```

## 🎨 Code Style

### TypeScript/JavaScript
- **Formatter**: Prettier 3.x
- **Linter**: ESLint 9 (flat config)
- **Style**: 2 spaces, semicolons, single quotes
- **Naming**: camelCase for variables, PascalCase for components

### Python
- **Formatter**: Black (line length 100)
- **Linter**: Ruff
- **Type Checker**: Basedpyright
- **Style**: PEP 8 compliance
- **Naming**: snake_case for variables, PascalCase for classes

## 🔄 CI/CD Standards

### GitHub Actions
```yaml
# ✅ CORRECT - Modern GitHub Actions workflow
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
      - run: npm ci
      - run: npm run test:coverage
      - run: npm run test:e2e
```

### Quality Checks
- **Pre-commit**: Fast checks (lint, type check)
- **On Push**: Full test suite
- **On PR**: Coverage report, E2E tests
- **Scheduled**: Security scans, dependency updates

## 📖 Learning Resources

### Official Docs (Recommended)
- React: https://react.dev/learn
- TypeScript: https://www.typescriptlang.org/docs/handbook/intro.html
- Vitest: https://vitest.dev/guide/
- Playwright: https://playwright.dev/docs/intro
- FastAPI: https://fastapi.tiangolo.com/tutorial/
- Pytest: https://docs.pytest.org/en/stable/getting-started.html

### When In Doubt
1. Check official documentation FIRST
2. Verify version compatibility
3. Test in isolation before integrating
4. Ask for code review if unsure

## 🚨 Critical Reminders

1. **NEVER** copy code from outdated tutorials
2. **ALWAYS** verify framework versions match 2025 standards
3. **READ** official documentation before implementing
4. **TEST** thoroughly with modern testing frameworks
5. **REVIEW** code for deprecated patterns before committing

---

**Remember**: This is a living document. When in doubt, consult official documentation and current project standards.

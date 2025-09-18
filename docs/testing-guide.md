# Testing Guide

## Overview

This guide covers the comprehensive testing strategy for the ToolBoxAI Solutions application, including unit tests, integration tests, end-to-end tests, and performance testing.

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Test Structure](#test-structure)
3. [Running Tests](#running-tests)
4. [Writing Tests](#writing-tests)
5. [Coverage Requirements](#coverage-requirements)
6. [CI/CD Integration](#cicd-integration)
7. [Best Practices](#best-practices)

## Testing Philosophy

Our testing approach follows these principles:

- **Test Pyramid**: More unit tests, fewer integration tests, minimal E2E tests
- **Fast Feedback**: Tests should run quickly to enable rapid development
- **Isolation**: Tests should not depend on external services when possible
- **Clarity**: Test names should clearly describe what they test
- **Maintainability**: Tests should be easy to update as code changes

## Test Structure

```
tests/
├── unit/                 # Unit tests for individual components
│   ├── core/            # Core module tests
│   ├── frontend/        # Frontend component tests
│   └── security/        # Security-focused tests
├── integration/         # Integration tests
│   ├── database/       # Database integration tests
│   └── api/           # API integration tests
├── e2e/                # End-to-end tests
├── performance/        # Performance and load tests
├── fixtures/           # Test fixtures and utilities
└── manual/            # Manual testing scripts

apps/dashboard/
├── src/__tests__/      # Frontend unit tests
│   ├── components/    # Component tests
│   ├── services/      # Service tests
│   └── performance/   # Performance tests
└── tests/             # E2E tests (Playwright)
```

## Running Tests

### Backend Tests (Python)

```bash
# Run all backend tests
pytest

# Run with coverage
pytest --cov=apps.backend --cov=core --cov-report=html

# Run specific test file
pytest tests/unit/core/test_models.py

# Run with verbose output
pytest -v

# Run tests by marker
pytest -m unit        # Unit tests only
pytest -m integration # Integration tests only
pytest -m "not slow"  # Skip slow tests

# Run tests in parallel
pytest -n auto
```

### Frontend Tests (TypeScript/React)

```bash
# Change to dashboard directory
cd apps/dashboard

# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch

# Run specific test file
npm test src/__tests__/minimal.test.tsx

# Run E2E tests
npm run test:e2e
```

### Database Tests

Some tests require a database connection. Set environment variables:

```bash
export DATABASE_URL=postgresql://eduplatform:eduplatform2024@localhost/educational_platform_dev
export REDIS_URL=redis://localhost:6379
```

### Environment-Gated Tests

Some tests are gated behind environment variables:

```bash
RUN_ENDPOINT_TESTS=1 pytest     # Enable endpoint tests
RUN_ROJO_TESTS=1 pytest         # Enable Rojo integration tests
RUN_PUSHER_E2E=1 pytest         # Enable Pusher E2E tests
RUN_PUSHER_INTEGRATION=1 pytest # Enable Pusher integration tests
```

## Writing Tests

### Backend Test Example

```python
import pytest
from unittest.mock import Mock, patch

class TestUserService:
    """Test user service functionality"""

    @pytest.fixture
    def user_service(self):
        """Create a user service instance"""
        return UserService()

    def test_create_user(self, user_service):
        """Test user creation"""
        # Arrange
        user_data = {"email": "test@example.com", "name": "Test User"}

        # Act
        user = user_service.create_user(user_data)

        # Assert
        assert user.email == "test@example.com"
        assert user.name == "Test User"

    @pytest.mark.asyncio
    async def test_async_operation(self, user_service):
        """Test async operation"""
        result = await user_service.async_method()
        assert result is not None
```

### Frontend Test Example

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button } from '@/components/Button';

describe('Button Component', () => {
  it('renders button with text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('handles click events', async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();

    render(<Button onClick={handleClick}>Click me</Button>);
    await user.click(screen.getByText('Click me'));

    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

### E2E Test Example

```typescript
import { test, expect } from '@playwright/test';

test.describe('Login Flow', () => {
  test('user can log in', async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');

    // Fill in credentials
    await page.fill('[data-testid="email-input"]', 'test@example.com');
    await page.fill('[data-testid="password-input"]', 'password123');

    // Submit form
    await page.click('[data-testid="login-button"]');

    // Verify redirect to dashboard
    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('h1')).toContainText('Dashboard');
  });
});
```

## Coverage Requirements

### Target Coverage Levels

- **Overall**: 80% minimum
- **Critical paths**: 95% minimum
- **New code**: 90% minimum

### Checking Coverage

```bash
# Backend coverage
pytest --cov --cov-report=term-missing

# Frontend coverage
cd apps/dashboard && npm run test:coverage

# View HTML reports
open htmlcov/index.html           # Backend
open coverage/lcov-report/index.html  # Frontend
```

### Coverage Configuration

**pytest.ini**:
```ini
[pytest]
addopts = --cov=core --cov=apps
          --cov-report=term-missing
          --cov-report=html
```

**vite.config.ts**:
```typescript
test: {
  coverage: {
    provider: 'v8',
    thresholds: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  }
}
```

## CI/CD Integration

### GitHub Actions Workflow

Tests run automatically on:
- Push to main/develop branches
- Pull requests
- Manual workflow dispatch

See `.github/workflows/test-automation.yml` for configuration.

### Pre-commit Hooks

Install pre-commit hooks to run tests before commits:

```bash
pip install pre-commit
pre-commit install
```

Configuration in `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

## Best Practices

### 1. Test Naming

- Use descriptive names that explain what is being tested
- Follow pattern: `test_<what>_<condition>_<expected_result>`
- Example: `test_user_creation_with_invalid_email_raises_exception`

### 2. Test Organization

- Group related tests in classes
- Use fixtures for common setup
- Keep tests focused on one behavior
- Use appropriate markers (`@pytest.mark.unit`, etc.)

### 3. Mocking

- Mock external dependencies
- Use dependency injection for testability
- Keep mocks simple and focused

### 4. Data Management

- Use factories for test data creation
- Clean up test data after tests
- Use transactions for database tests

### 5. Performance

- Keep unit tests under 100ms
- Keep integration tests under 1 second
- Use parallel execution for speed

### 6. Debugging

```bash
# Run with debugging output
pytest -vvs

# Run with debugger
pytest --pdb

# Run specific test with full traceback
pytest path/to/test.py::TestClass::test_method -vv --tb=long
```

### 7. Common Issues and Solutions

**Import Errors**:
- Ensure project root is in Python path
- Check virtual environment activation

**Database Connection Issues**:
- Verify PostgreSQL/Redis are running
- Check environment variables

**Frontend Test Failures**:
- Clear node_modules and reinstall
- Check for missing dependencies
- Verify test setup file is correct

**Flaky Tests**:
- Add proper waits for async operations
- Use deterministic test data
- Mock time-dependent operations

## Test Markers

Available pytest markers:

```python
@pytest.mark.unit          # Fast, isolated unit tests
@pytest.mark.integration   # Integration tests
@pytest.mark.e2e          # End-to-end tests
@pytest.mark.slow         # Tests taking >5 seconds
@pytest.mark.database     # Tests requiring database
@pytest.mark.api          # API endpoint tests
@pytest.mark.pusher       # Pusher realtime tests
@pytest.mark.skip_in_ci   # Skip in CI/CD pipeline
```

### Pusher-Specific Testing

The application uses Pusher for realtime communication instead of WebSockets. Here's how to test Pusher functionality:

#### Backend Pusher Tests

```python
from tests.fixtures.pusher_mocks import mock_pusher_service

def test_pusher_event(mock_pusher_service):
    """Test sending a Pusher event"""
    result = mock_pusher_service.trigger(
        'public-channel',
        'test-event',
        {'message': 'Hello'}
    )
    assert result['status'] == 'success'
```

#### Frontend Pusher Tests

```typescript
import { vi } from 'vitest';

describe('Pusher Integration', () => {
  it('subscribes to channel', async () => {
    const pusher = vi.mocked(PusherService.getInstance());
    const channel = pusher.subscribe('public-updates');

    expect(channel).toBeDefined();
    expect(pusher.subscribe).toHaveBeenCalledWith('public-updates');
  });
});
```

## Performance Testing

### Load Testing

```python
# tests/performance/test_load.py
import asyncio
import aiohttp
import time

async def test_api_load():
    """Test API under load"""
    async with aiohttp.ClientSession() as session:
        tasks = []
        for _ in range(100):
            task = session.get('http://localhost:8008/api/v1/health')
            tasks.append(task)

        start = time.time()
        responses = await asyncio.gather(*tasks)
        duration = time.time() - start

        assert duration < 5.0  # Should handle 100 requests in 5 seconds
        assert all(r.status == 200 for r in responses)
```

### Benchmark Testing

```bash
# Run benchmarks
pytest tests/performance/ --benchmark-only
```

## Maintenance

### Regular Tasks

- **Weekly**: Review and update failing tests
- **Monthly**: Check coverage trends
- **Quarterly**: Review and optimize slow tests
- **Yearly**: Audit test strategy and update guide

### Test Data Management

- Refresh test databases monthly
- Archive old test reports
- Clean up test artifacts

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Vitest Documentation](https://vitest.dev/)
- [Playwright Documentation](https://playwright.dev/)
- [Testing Library Documentation](https://testing-library.com/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

## Support

For testing issues or questions:
1. Check this guide
2. Review existing tests for examples
3. Ask in the development team channel
4. Create an issue if you find a bug

---

Last Updated: 2025-09-18
Version: 1.0.0
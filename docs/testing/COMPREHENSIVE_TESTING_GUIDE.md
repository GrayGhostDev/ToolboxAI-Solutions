# Comprehensive Testing Guide for ToolBoxAI

**Version**: 2.0
**Last Updated**: January 2025
**Status**: Production Ready

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Testing Architecture](#testing-architecture)
4. [Test Categories](#test-categories)
5. [Running Tests](#running-tests)
6. [Writing Tests](#writing-tests)
7. [CI/CD Integration](#cicd-integration)
8. [Performance Testing](#performance-testing)
9. [Security Testing](#security-testing)
10. [Troubleshooting](#troubleshooting)

## Overview

The ToolBoxAI testing infrastructure provides comprehensive coverage across multiple layers:
- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **E2E Tests**: Full workflow testing with Playwright
- **Performance Tests**: Load and stress testing with k6
- **Security Tests**: OWASP-based vulnerability testing

### Key Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Backend Coverage | 90% | Pending |
| Frontend Coverage | 90% | Pending |
| E2E Coverage | 75% | Pending |
| Security Score | A+ | Pending |
| Performance P95 | <500ms | Pending |

## Quick Start

### Prerequisites

```bash
# Install Python dependencies
pip install -r requirements.txt
pip install pytest-cov pytest-asyncio pytest-xdist

# Install Node dependencies
cd apps/dashboard
npm install

# Install testing tools
npm install -g playwright
playwright install chromium

# Install k6 for performance testing (macOS)
brew install k6

# Install security tools
pip install bandit detect-secrets
```

### Environment Setup

```bash
# Copy test environment template
cp .env.test .env.test.local

# Edit with your configuration
vim .env.test.local

# Key variables to set:
DATABASE_URL=postgresql://testuser:testpass@localhost:5432/testdb
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=test-secret-key
USE_MOCK_LLM=true
```

### Run Your First Test

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=apps --cov-report=html

# Run specific test file
pytest tests/unit/core/test_agents.py -v

# Run tests matching pattern
pytest -k "test_should_authenticate" -v
```

## Testing Architecture

### Directory Structure

```
tests/
├── unit/                 # Fast, isolated tests
│   ├── core/            # Core functionality
│   ├── api/             # API endpoints
│   └── services/        # Service layer
├── integration/         # Component interaction tests
│   ├── database/        # Database operations
│   ├── pusher/          # Real-time features
│   └── agents/          # AI agent coordination
├── e2e/                 # End-to-end workflows
│   ├── playwright/      # Browser automation
│   └── workflows/       # User journeys
├── performance/         # Load and stress tests
│   ├── k6/             # k6 load tests
│   └── benchmarks/      # Performance baselines
├── security/            # Security testing
│   └── owasp/          # OWASP vulnerability tests
└── fixtures/           # Shared test fixtures
    ├── async_helpers.py
    ├── auth.py
    ├── cleanup.py
    └── database.py
```

### Fixture Organization

The test fixtures are organized into focused modules for better maintainability:

| Module | Purpose | Key Fixtures |
|--------|---------|--------------|
| `async_helpers.py` | Async/event loop management | `event_loop`, `async_context` |
| `auth.py` | Authentication & rate limiting | `mock_jwt_token`, `bypass_auth` |
| `cleanup.py` | Resource cleanup | `temp_directory`, `cleanup_redis_data` |
| `database.py` | Database fixtures | `mock_db_session`, `test_user` |

## Test Categories

### Unit Tests

Fast, isolated tests for individual components.

```python
@pytest.mark.unit
def test_should_calculate_quiz_score_when_all_answers_correct():
    """Test quiz scoring with perfect answers."""
    quiz = Quiz(questions=[...])
    score = quiz.calculate_score(answers=[...])
    assert score == 100
```

**Coverage Target**: 90%
**Execution Time**: <0.1s per test
**Run Command**: `pytest tests/unit/ -v`

### Integration Tests

Test interactions between components.

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_should_persist_content_when_created_via_api():
    """Test content creation through API persists to database."""
    async with test_client() as client:
        response = await client.post("/api/v1/content", json={...})
        assert response.status_code == 201

        # Verify in database
        content = await db.get_content(response.json()["id"])
        assert content is not None
```

**Coverage Target**: 85%
**Execution Time**: <5s per test
**Run Command**: `pytest tests/integration/ -v`

### E2E Tests (Playwright)

Full user workflow testing with browser automation.

```python
@pytest.mark.e2e
async def test_should_complete_student_registration_workflow():
    """Test complete student registration flow."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        await page.goto("http://localhost:5179")
        await page.fill('[data-testid="email"]', "student@example.com")
        await page.fill('[data-testid="password"]', "Test123!")
        await page.click('[data-testid="register-btn"]')

        # Verify dashboard access
        await page.wait_for_url("**/dashboard")
        assert "Dashboard" in await page.title()
```

**Coverage Target**: 75%
**Execution Time**: <30s per test
**Run Command**: `pytest tests/e2e/ --run-e2e -v`

### Performance Tests (k6)

Load testing and performance benchmarking.

```javascript
export default function() {
    const response = http.get(`${BASE_URL}/api/v1/content`);
    check(response, {
        'status is 200': (r) => r.status === 200,
        'response time < 500ms': (r) => r.timings.duration < 500,
    });
}
```

**Thresholds**:
- P95 Response Time: <500ms
- P99 Response Time: <1000ms
- Error Rate: <1%

**Run Command**: `k6 run tests/performance/load-test.js`

### Security Tests (OWASP)

Comprehensive security vulnerability testing.

```python
@pytest.mark.security
def test_should_prevent_sql_injection():
    """Test SQL injection prevention."""
    payloads = ["' OR '1'='1", "'; DROP TABLE users; --"]
    for payload in payloads:
        response = client.get(f"/api/v1/search?q={payload}")
        assert response.status_code != 500
        assert "error" not in response.json()
```

**Categories Tested**:
- SQL Injection
- XSS Prevention
- CSRF Protection
- Authentication Bypass
- Rate Limiting

**Run Command**: `pytest tests/security/ --run-security -v`

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=apps --cov-report=html

# Run in parallel (faster)
pytest -n auto

# Run specific markers
pytest -m unit        # Unit tests only
pytest -m integration # Integration tests only
pytest -m "not slow"  # Skip slow tests
```

### Advanced Options

```bash
# Run tests matching name pattern
pytest -k "authentication"

# Run until first failure
pytest -x

# Run failed tests from last run
pytest --lf

# Show local variables on failure
pytest -l

# Drop into debugger on failure
pytest --pdb

# Set test timeout
pytest --timeout=10
```

### Environment-Based Test Execution

Control test execution with environment variables:

```bash
# Enable E2E tests
RUN_E2E_TESTS=1 pytest tests/e2e/

# Enable slow tests
RUN_SLOW_TESTS=1 pytest -m slow

# Run with Docker
DOCKER_AVAILABLE=1 pytest tests/integration/

# Disable external API calls
DISABLE_EXTERNAL_CALLS=true pytest
```

## Writing Tests

### Test Naming Standards

Follow the pattern: `test_should_<expected_behavior>_when_<condition>`

```python
# ✅ Good
def test_should_return_user_profile_when_authenticated():
    pass

def test_should_raise_error_when_invalid_email_provided():
    pass

# ❌ Bad
def test_user():  # Too vague
    pass

def test_1():  # Meaningless
    pass
```

### Using Fixtures

```python
def test_authenticated_request(test_client, mock_jwt_token):
    """Test with authenticated client."""
    token = mock_jwt_token(user_id=1, role="teacher")
    headers = {"Authorization": f"Bearer {token}"}

    response = test_client.get("/api/v1/profile", headers=headers)
    assert response.status_code == 200
```

### Async Tests

```python
@pytest.mark.asyncio
async def test_async_database_operation(db_session):
    """Test async database operations."""
    user = await db_session.create_user({"email": "test@example.com"})
    assert user.id is not None

    fetched_user = await db_session.get_user(user.id)
    assert fetched_user.email == "test@example.com"
```

### Mocking External Services

```python
def test_openai_integration(mock_openai):
    """Test OpenAI integration with mock."""
    mock_openai.return_value.generate.return_value = "Mocked response"

    result = generate_content("Math lesson")
    assert result == "Mocked response"
    mock_openai.return_value.generate.assert_called_once()
```

## CI/CD Integration

### GitHub Actions Workflow

The CI/CD pipeline runs automatically on:
- Push to `main` or `develop`
- Pull requests
- Daily security scans

#### Pipeline Stages

1. **Security Scanning** - GitLeaks, Trivy, Bandit
2. **Backend Tests** - Python unit and integration tests
3. **Frontend Tests** - TypeScript, React component tests
4. **E2E Tests** - Playwright browser automation
5. **Performance Tests** - k6 load testing
6. **Quality Gates** - Coverage and security thresholds

### Quality Gates

Tests must meet these thresholds:

| Gate | Threshold | Action on Failure |
|------|-----------|-------------------|
| Backend Coverage | ≥90% | Block merge |
| Frontend Coverage | ≥90% | Block merge |
| Security Issues | 0 critical | Block merge |
| Performance P95 | <500ms | Warning |
| E2E Pass Rate | ≥95% | Block merge |

## Performance Testing

### Running k6 Tests

```bash
# Basic load test
k6 run tests/performance/load-test.js

# With custom VUs and duration
k6 run --vus 100 --duration 30s tests/performance/load-test.js

# Output to JSON
k6 run --out json=results.json tests/performance/load-test.js

# Cloud execution (requires k6 Cloud account)
k6 cloud tests/performance/load-test.js
```

### Performance Baselines

| Endpoint | P50 | P95 | P99 |
|----------|-----|-----|-----|
| GET /health | 10ms | 50ms | 100ms |
| GET /content | 50ms | 200ms | 500ms |
| POST /content | 100ms | 400ms | 800ms |
| WebSocket Connect | 200ms | 500ms | 1000ms |

## Security Testing

### Running OWASP Tests

```bash
# Run all security tests
pytest tests/security/ -v

# Run specific vulnerability tests
pytest tests/security/test_owasp_security.py::TestInjection -v

# Generate security report
pytest tests/security/ --html=security-report.html
```

### Security Checklist

- [ ] SQL Injection Prevention
- [ ] XSS Protection
- [ ] CSRF Token Validation
- [ ] Authentication Bypass Tests
- [ ] Authorization Tests
- [ ] Rate Limiting
- [ ] Input Validation
- [ ] Security Headers
- [ ] HTTPS Enforcement
- [ ] Sensitive Data Exposure

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors

```bash
# Error: could not connect to database
# Solution: Ensure PostgreSQL is running
brew services start postgresql
# Or with Docker
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=testpass postgres:15
```

#### 2. Async Test Failures

```python
# Error: RuntimeError: Event loop is closed
# Solution: Use pytest-asyncio properly
@pytest.mark.asyncio  # Add this decorator
async def test_async_function():
    pass
```

#### 3. Flaky Tests

```python
# Add retry logic for flaky tests
@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_external_api_call():
    pass
```

#### 4. Coverage Not Collected

```bash
# Ensure pytest-cov is installed
pip install pytest-cov

# Run with correct source path
pytest --cov=apps --cov=core tests/
```

### Debug Mode

```bash
# Enable detailed logging
pytest -vvs --log-cli-level=DEBUG

# Drop into debugger on failure
pytest --pdb

# Show test durations
pytest --durations=10

# Profile test execution
pytest --profile
```

## Best Practices

### Do's ✅

1. **Write descriptive test names** that explain the scenario
2. **Keep tests independent** - no dependencies between tests
3. **Use fixtures** for common setup and teardown
4. **Mock external services** to avoid flakiness
5. **Test error cases** not just happy paths
6. **Run tests locally** before pushing
7. **Keep tests fast** - use mocks for slow operations

### Don'ts ❌

1. **Don't use production data** in tests
2. **Don't hardcode values** - use fixtures
3. **Don't skip tests permanently** - use conditional skips
4. **Don't test implementation details** - test behavior
5. **Don't ignore flaky tests** - fix them
6. **Don't commit commented-out tests**
7. **Don't use `time.sleep()`** - use proper waits

## Resources

### Documentation
- [Pytest Documentation](https://docs.pytest.org/)
- [Playwright Documentation](https://playwright.dev/python/)
- [k6 Documentation](https://k6.io/docs/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)

### Internal Guides
- [Test Naming Standards](./test-naming-standards.md)
- [Fixture Guide](./fixtures/README.md)
- [CI/CD Pipeline](.github/workflows/README.md)
- [Security Testing](./security/README.md)

### Support
- GitHub Issues: Report bugs and request features
- Slack: #testing channel for questions
- Wiki: Internal testing best practices

---

**Last Updated**: January 2025
**Maintained By**: ToolBoxAI Development Team
**Version**: 2.0
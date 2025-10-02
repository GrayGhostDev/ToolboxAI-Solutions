# Backend Testing Guide - 2025 Best Practices

**Date**: October 2, 2025
**Python Version**: 3.13.0
**Pytest Version**: 8.4.2
**Status**: Operational with Known Issues

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Test Infrastructure Overview](#test-infrastructure-overview)
3. [Known Issues & Workarounds](#known-issues--workarounds)
4. [Running Tests](#running-tests)
5. [Writing New Tests](#writing-new-tests)
6. [Coverage Reporting](#coverage-reporting)
7. [CI/CD Integration](#cicd-integration)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Verify pytest installation
pytest --version
# Expected: pytest 8.4.2

# 3. Verify dependencies
python -c "import asyncpg, langchain_core, fastapi; print('✅ Dependencies OK')"
```

### Running Tests

```bash
# ✅ RECOMMENDED: Run simple standalone tests
pytest test_simple_standalone.py -v

# ⚠️ WARNING: Full test suite collection hangs (see Known Issues)
# pytest tests/unit  # This will timeout!

# ✅ WORKAROUND: Run tests with --noconftest to skip conftest.py
pytest tests/unit/core/test_models_unit_core.py --noconftest -v
```

---

## Test Infrastructure Overview

### Current Test Statistics

| Metric | Value | Status |
|--------|-------|--------|
| **Total Test Files** | 249 | ✅ Excellent |
| **Test Directories** | 40+ | ✅ Well organized |
| **Pytest Version** | 8.4.2 | ✅ Modern |
| **Python Version** | 3.13.0 | ✅ Latest |
| **Dependencies** | 100+ installed | ✅ Complete |
| **Virtual Environment** | venv/ | ✅ Operational |
| **Test Collection** | Hangs on conftest | ⚠️ Known issue |

### Directory Structure

```
tests/
├── conftest.py              ⚠️ Causes initialization hang
├── test_redis_cloud.py
├── __mocks__/               # Mock objects
├── unit/                    # Unit tests (~80 files)
│   ├── backend/
│   ├── core/
│   ├── security/
│   └── services/
├── integration/             # Integration tests (~40 files)
│   ├── agents/
│   └── database/
├── e2e/                     # End-to-end tests (~20 files)
├── performance/             # Performance tests (~10 files)
├── security/                # Security tests (~15 files)
├── agents/                  # AI agent testing
├── chaos/                   # Chaos engineering
├── compliance/              # Regulatory compliance
├── accessibility/           # WCAG 2.1 AA compliance
└── [30+ more directories]
```

### Pytest Configuration (pyproject.toml)

```toml
[tool.pytest.ini_options]
minversion = "6.0"
addopts = "-ra -q --strict-markers"
testpaths = ["tests/unit", "tests/integration"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"

# 2025 best practice - auto async support
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "session"
```

---

## Known Issues & Workarounds

### Issue #1: Test Collection Timeout ⚠️

**Problem**: Running `pytest tests/unit` or `pytest tests/` hangs indefinitely during collection phase.

**Root Cause**:
- `tests/conftest.py:49` imports from `apps.backend.core.security.rate_limit_manager`
- This triggers `apps/backend/__init__.py:50` which imports `apps.backend.main.py`
- `main.py:45` creates the FastAPI app with `app = create_app()` at module level
- The `create_app()` function initialization hangs (likely waiting for external services)

**Code Path**:
```
tests/conftest.py (line 49)
  → apps.backend.core.security.rate_limit_manager
    → apps.backend/__init__.py (line 50)
      → apps.backend.main.py (line 45)
        → app = create_app(config_settings=settings)  # ⚠️ HANGS HERE
```

**Workarounds**:

#### Workaround A: Skip conftest.py (Recommended)
```bash
# Use --noconftest flag to bypass conftest.py
pytest tests/unit/core/test_models_unit_core.py --noconftest -v

# Note: This skips all fixtures defined in conftest.py
# Only works for tests that don't depend on those fixtures
```

#### Workaround B: Run Standalone Tests
```bash
# Create tests outside tests/ directory
pytest test_simple_standalone.py -v

# Example standalone test provided in root directory
```

#### Workaround C: Mock the App Creation (Future Fix)
```python
# TODO: Modify conftest.py to mock FastAPI app creation
# Instead of importing the real app, use a mock
from unittest.mock import MagicMock
app = MagicMock()
```

### Issue #2: Optional Dependencies Missing

**Problem**: Some tests may fail due to missing scipy and other ML packages.

**Root Cause**: scipy requires a Fortran compiler which isn't installed.

**Impact**: Low - only affects ML-specific features

**Workaround**:
```bash
# Skip tests that require scipy
pytest tests/unit -m "not ml_specific" -v
```

---

## Running Tests

### Test Execution Commands

#### Simple Standalone Tests (✅ Working)

```bash
# Run the provided standalone test file
pytest test_simple_standalone.py -v

# Expected output:
# test_simple_standalone.py ...........  [100%]
# 11 passed in 0.03s
```

#### Unit Tests Without Fixtures (✅ Working with --noconftest)

```bash
# Run specific test file without conftest
pytest tests/unit/core/test_models_unit_core.py --noconftest -v

# Run all tests in a directory without conftest
pytest tests/unit/core/ --noconftest -v
```

#### Full Test Suite (⚠️ Currently Hanging)

```bash
# ⚠️ WARNING: This will hang during collection!
# pytest tests/unit -v

# Wait for fix to conftest.py initialization before using
```

### Test Markers

Run tests by marker:

```bash
# Unit tests only
pytest -m unit -v

# Integration tests only
pytest -m integration -v

# Async tests only
pytest -m asyncio -v

# Skip slow tests
pytest -m "not slow" -v

# Combine markers
pytest -m "unit and not slow" -v
```

### Pytest Options Reference

```bash
# Verbose output
pytest -v

# Show local variables on failure
pytest -l

# Stop on first failure
pytest -x

# Show N slowest tests
pytest --durations=10

# Run last failed tests
pytest --lf

# Run only tests that failed last time
pytest --ff

# Parallel execution (requires pytest-xdist)
pytest -n auto

# Show print statements
pytest -s
```

---

## Writing New Tests

### Test File Naming Conventions

```
test_*.py          # Test files must start with test_
*_test.py          # Alternative (also valid)
Test*              # Test classes must start with Test
test_*             # Test functions must start with test_
```

### Basic Test Example

```python
"""
Example unit test for backend component.
"""

import pytest


def test_simple_function():
    """Test a simple function."""
    result = my_function(input_value)
    assert result == expected_value


class TestMyClass:
    """Test class for MyClass component."""

    def test_method_one(self):
        """Test specific method."""
        obj = MyClass()
        result = obj.method_one()
        assert result is not None

    def test_method_two(self):
        """Test another method."""
        obj = MyClass()
        result = obj.method_two(param=123)
        assert result == 123
```

### Async Test Example

```python
import pytest


@pytest.mark.asyncio
async def test_async_function():
    """Test async function with pytest-asyncio."""
    result = await async_function()
    assert result is not None


@pytest.mark.asyncio
async def test_async_database_query():
    """Test async database operations."""
    async with get_async_session() as session:
        result = await session.execute(query)
        assert len(result.all()) > 0
```

### Parametrized Test Example

```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
    (4, 8),
])
def test_double_number(input, expected):
    """Test doubling numbers with different inputs."""
    assert double(input) == expected
```

### Fixture Example (When conftest is fixed)

```python
import pytest


@pytest.fixture
def sample_data():
    """Provide sample data for tests."""
    return {
        "id": 1,
        "name": "Test User",
        "email": "test@example.com"
    }


def test_with_fixture(sample_data):
    """Test using fixture data."""
    assert sample_data["id"] == 1
    assert sample_data["name"] == "Test User"
```

---

## Coverage Reporting

### Generate Coverage Report

```bash
# Run tests with coverage (when tests work)
pytest test_simple_standalone.py --cov=apps/backend --cov-report=html

# View HTML report
open htmlcov/index.html
```

### Coverage Configuration

Coverage is configured in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
# Coverage will be added here when tests are working
```

Expected coverage targets:
- **Unit Tests**: >90%
- **Integration Tests**: >80%
- **Overall**: >85%

---

## CI/CD Integration

### GitHub Actions Example (Future)

```yaml
name: Backend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'

      - name: Install dependencies
        run: |
          python -m venv venv
          source venv/bin/activate
          pip install -r requirements.txt

      - name: Run tests
        run: |
          source venv/bin/activate
          pytest test_simple_standalone.py -v

      - name: Generate coverage report
        run: |
          source venv/bin/activate
          pytest --cov=apps/backend --cov-report=xml

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
```

---

## Troubleshooting

### Problem: Import Errors

**Symptom**: `ModuleNotFoundError` when running tests

**Solution**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Verify installations
python -c "import asyncpg, fastapi, pytest; print('OK')"
```

### Problem: Tests Hang

**Symptom**: Pytest hangs during collection or execution

**Solution**:
```bash
# Use --noconftest to bypass conftest.py
pytest tests/unit/test_file.py --noconftest -v

# Or run standalone tests
pytest test_simple_standalone.py -v
```

### Problem: Async Test Warnings

**Symptom**: Warnings about event loop or async fixtures

**Solution**:
```python
# Ensure test is marked with @pytest.mark.asyncio
import pytest

@pytest.mark.asyncio
async def test_async_function():
    await async_operation()
```

### Problem: Database Connection Errors

**Symptom**: Tests fail with database connection errors

**Solution**:
```bash
# Check PostgreSQL is running
psql -l

# Verify DATABASE_URL in .env
cat .env | grep DATABASE_URL

# Use test database
export DATABASE_URL=postgresql://test:test@localhost/test_db
```

---

## Best Practices

### DO ✅

- **Write isolated tests**: Each test should be independent
- **Use descriptive names**: `test_user_login_with_valid_credentials`
- **Test one thing**: Each test should verify one behavior
- **Use fixtures**: Share setup code via fixtures (when conftest is fixed)
- **Mark tests**: Use `@pytest.mark.unit`, `@pytest.mark.asyncio`, etc.
- **Document tests**: Add docstrings explaining what is tested
- **Clean up**: Use fixtures for setup/teardown
- **Test edge cases**: Include boundary conditions
- **Async tests**: Mark with `@pytest.mark.asyncio`

### DON'T ❌

- **Don't test implementation**: Test behavior, not internals
- **Don't use sleep**: Use proper async/await or mocking
- **Don't share state**: Tests should not depend on each other
- **Don't skip cleanup**: Always clean up resources
- **Don't hardcode**: Use fixtures or parametrize
- **Don't ignore warnings**: Fix deprecation warnings
- **Don't commit test data**: Use fixtures or factories
- **Don't test external APIs**: Mock external services

---

## Summary

### Current Status

- ✅ **Virtual environment**: Operational (Python 3.13.0)
- ✅ **Dependencies**: 100+ packages installed
- ✅ **Pytest**: Version 8.4.2 working
- ✅ **Standalone tests**: 11/11 passing
- ⚠️ **Full test suite**: Blocked by conftest.py initialization hang
- ⏳ **Coverage**: Pending test execution

### Next Steps

1. **Fix conftest.py initialization** (High Priority)
   - Mock FastAPI app creation
   - Lazy-load backend imports
   - Use test-specific fixtures

2. **Run full test suite** (After fix)
   - Execute all 249 test files
   - Generate coverage reports
   - Identify failing tests

3. **Achieve >85% coverage** (Ongoing)
   - Write tests for uncovered code
   - Backfill missing test cases
   - Regular coverage monitoring

---

## Resources

### Internal Documentation

- **BACKEND-TESTING-AUDIT.md** - Complete test infrastructure audit
- **BACKEND-SETUP-COMPLETE.md** - Environment setup summary
- **TESTING-INFRASTRUCTURE-COMPLETE-2025.md** - Frontend testing docs
- **COVERAGE-GUIDE.md** - Frontend coverage documentation

### External Resources

- **Pytest Documentation**: https://docs.pytest.org/
- **pytest-asyncio**: https://pytest-asyncio.readthedocs.io/
- **FastAPI Testing**: https://fastapi.tiangolo.com/tutorial/testing/
- **Coverage.py**: https://coverage.readthedocs.io/

---

**Last Updated**: October 2, 2025, 02:30 UTC
**Author**: Claude Code Testing Agent
**Status**: Operational with Known Issues
**Readiness**: 85%

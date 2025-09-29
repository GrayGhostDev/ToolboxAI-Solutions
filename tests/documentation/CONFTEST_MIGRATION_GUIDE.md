# Conftest.py Migration Guide

## Overview
The original `conftest.py` file (1008 lines) has been refactored into organized fixture modules for better maintainability, discoverability, and reduced complexity.

## New Structure

```
tests/
├── conftest.py (original - to be replaced)
├── conftest_simplified.py (new simplified version)
└── fixtures/
    ├── __init__.py
    ├── async_helpers.py    # NEW: Event loop and async utilities
    ├── auth.py            # NEW: Authentication and rate limiting
    ├── cleanup.py         # NEW: Cleanup and teardown utilities
    ├── database.py        # EXISTING: Database fixtures
    ├── api.py            # EXISTING: API client fixtures
    ├── agents.py         # EXISTING: AI agent fixtures
    ├── common.py         # EXISTING: Common utilities
    └── ...
```

## Migration Steps

### Step 1: Backup Current Setup
```bash
cp tests/conftest.py tests/conftest_backup.py
```

### Step 2: Test with New Structure
```bash
# Run tests with the new conftest to ensure everything works
PYTEST_CURRENT_TEST=tests/conftest_simplified.py pytest tests/unit/ -v

# If successful, continue to Step 3
```

### Step 3: Replace conftest.py
```bash
# Replace the old conftest with the simplified version
mv tests/conftest.py tests/conftest_old.py
mv tests/conftest_simplified.py tests/conftest.py
```

### Step 4: Update Imports (if needed)
If any tests directly import from conftest, update them:
```python
# Old
from tests.conftest import some_fixture

# New (preferred)
# Fixtures are automatically discovered, no import needed

# Or if explicit import is required
from tests.fixtures.auth import mock_jwt_token
```

## Fixture Module Organization

### `fixtures/async_helpers.py`
- `event_loop` - Session-scoped event loop
- `async_context` - Async context manager for tests
- `handle_event_loop_errors` - Event loop error handling
- `cleanup_async_tasks` - Automatic async task cleanup
- `enhanced_async_cleanup` - Comprehensive async resource cleanup

### `fixtures/auth.py`
- `reset_rate_limits` - Reset rate limits before each test
- `rate_limit_context` - Rate limit testing context
- `rate_limit_manager` - Mock rate limit manager
- `production_rate_limit_manager` - Production-like rate limiter
- `mock_jwt_token` - Create mock JWT tokens
- `mock_auth_headers` - Create auth headers
- `mock_current_user` - Mock current user
- `mock_session_manager` - Mock session management
- `bypass_auth` - Bypass authentication for testing

### `fixtures/cleanup.py`
- `cleanup_database_pools` - Clean up DB connections
- `cleanup_temp_files` - Clean up temporary files
- `temp_directory` - Provide temporary directory
- `temp_file` - Create temporary files
- `cleanup_mock_data` - Clean up mocks and patches
- `cleanup_redis_data` - Clean up Redis test data
- `cleanup_log_handlers` - Clean up log handlers
- `cleanup_on_failure` - Conditional cleanup on test failure
- `cleanup_test_artifacts` - Session-end cleanup

### Existing Fixture Modules
- `fixtures/database.py` - Database mocks and test data
- `fixtures/api.py` - API client and request mocks
- `fixtures/agents.py` - AI agent mocks and utilities
- `fixtures/common.py` - Common test utilities

## Benefits of the New Structure

1. **Better Organization**: Fixtures grouped by functionality
2. **Easier Discovery**: Clear module names indicate fixture purpose
3. **Reduced Complexity**: No more 1000+ line conftest.py
4. **Improved Maintainability**: Changes isolated to specific modules
5. **Faster Test Startup**: Only load needed fixtures
6. **Reduced Conflicts**: Multiple developers can work on different fixture modules

## Troubleshooting

### Issue: Fixture not found
**Solution**: Ensure the fixture module is imported in conftest.py or fixtures/__init__.py

### Issue: Import errors
**Solution**: Check that all fixture modules are in the Python path

### Issue: Tests fail with new structure
**Solution**: Some fixtures may have dependencies. Check the original conftest.py for fixture order.

### Issue: Async tests hanging
**Solution**: Ensure async_helpers fixtures are loaded (they have autouse=True)

## Rollback Plan

If issues arise, rollback to the original:
```bash
mv tests/conftest.py tests/conftest_new.py
mv tests/conftest_old.py tests/conftest.py
```

## Next Steps

1. Run full test suite to verify migration
2. Remove backup files once confirmed working
3. Update CI/CD if it references specific conftest structure
4. Update developer documentation

## Command to Run Tests

```bash
# Run all tests with new structure
pytest tests/ -v

# Run specific test categories
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/e2e/ --run-e2e -v

# Run with coverage
pytest tests/ --cov=apps --cov-report=html
```
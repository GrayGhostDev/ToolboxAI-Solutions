# Test Naming Standards

## Overview
This document defines the standardized naming conventions for all tests in the ToolBoxAI project. Following these standards ensures consistency, improves discoverability, and makes test intent clear.

## General Principles

1. **Descriptive**: Test names should clearly describe what is being tested
2. **Consistent**: Use the same patterns across all test files
3. **Searchable**: Names should be grep-friendly and IDE-searchable
4. **Meaningful**: Avoid generic names like `test_1` or `test_function`

## Test File Naming

### Python Test Files
```
test_<module_name>.py           # Unit tests
test_<feature>_integration.py   # Integration tests
test_<workflow>_e2e.py          # End-to-end tests
test_<metric>_performance.py    # Performance tests
test_<vulnerability>_security.py # Security tests
```

### JavaScript/TypeScript Test Files
```
<ComponentName>.test.tsx         # React component tests
<module>.test.ts                # Module tests
<api>.test.ts                   # API tests
<feature>.e2e.test.ts           # E2E tests
```

## Test Function Naming

### Pattern
```python
test_should_<expected_behavior>_when_<condition>
```

### Examples

#### Unit Tests
```python
# ✅ GOOD - Descriptive and follows pattern
def test_should_return_user_profile_when_authenticated():
    """Test that user profile is returned for authenticated requests."""
    pass

def test_should_raise_validation_error_when_email_invalid():
    """Test that validation error is raised for invalid email format."""
    pass

def test_should_calculate_quiz_score_when_all_answers_provided():
    """Test quiz score calculation with complete answers."""
    pass

# ❌ BAD - Too generic or unclear
def test_user():  # What about user?
    pass

def test_validation():  # What validation?
    pass

def test_1():  # Meaningless
    pass
```

#### Integration Tests
```python
# ✅ GOOD
def test_should_persist_content_to_database_when_created_via_api():
    """Test that content creation through API persists to database."""
    pass

def test_should_send_email_notification_when_assessment_completed():
    """Test email notification triggered by assessment completion."""
    pass

# ❌ BAD
def test_database():  # Too vague
    pass

def test_integration():  # Which integration?
    pass
```

#### E2E Tests
```python
# ✅ GOOD
def test_should_complete_student_registration_workflow_when_valid_data_provided():
    """Test complete student registration from signup to dashboard access."""
    pass

def test_should_display_error_message_when_login_fails():
    """Test error message display on login failure."""
    pass
```

## Test Class Naming

### Pattern
```python
Test<Feature><Aspect>
```

### Examples
```python
# ✅ GOOD
class TestUserAuthentication:
    """Test user authentication functionality."""

class TestContentGeneration:
    """Test content generation features."""

class TestQuizScoring:
    """Test quiz scoring logic."""

# ❌ BAD
class Tests:  # Too generic
    pass

class UserTests:  # Missing 'Test' prefix
    pass
```

## Test Markers and Categories

### Required Markers
```python
@pytest.mark.unit         # Unit tests
@pytest.mark.integration  # Integration tests
@pytest.mark.e2e          # End-to-end tests
@pytest.mark.security     # Security tests
@pytest.mark.performance  # Performance tests
```

### Conditional Markers
```python
@pytest.mark.slow              # Tests taking >5 seconds
@pytest.mark.requires_db       # Tests requiring database
@pytest.mark.requires_redis    # Tests requiring Redis
@pytest.mark.requires_docker   # Tests requiring Docker
@pytest.mark.flaky            # Known flaky tests (should be fixed!)
```

## Test Documentation

### Docstrings
Every test should have a docstring explaining:
1. What is being tested
2. Expected behavior
3. Any special setup requirements

```python
def test_should_validate_jwt_token_when_valid_signature_provided():
    """Test JWT token validation with valid signature.

    Verifies that:
    - Valid tokens are accepted
    - User claims are correctly extracted
    - Token expiration is checked

    Requires: Mock JWT service
    """
    pass
```

## Frontend Test Naming (React/TypeScript)

### Component Tests
```typescript
// ✅ GOOD
describe('DashboardHome', () => {
  it('should render student dashboard when user role is student', () => {
    // test implementation
  });

  it('should display loading spinner when data is fetching', () => {
    // test implementation
  });
});

// ❌ BAD
describe('Dashboard', () => {
  it('works', () => {  // Too vague
    // test implementation
  });
});
```

### API Tests
```typescript
// ✅ GOOD
describe('ContentAPI', () => {
  describe('createContent', () => {
    it('should return 201 when content is successfully created', () => {
      // test implementation
    });

    it('should return 400 when required fields are missing', () => {
      // test implementation
    });
  });
});
```

## Fixture Naming

### Pattern
```python
<scope>_<resource>  # For resources
mock_<service>      # For mocks
fake_<data>        # For fake data
```

### Examples
```python
# ✅ GOOD
@pytest.fixture
def authenticated_client():
    """Provide authenticated test client."""
    pass

@pytest.fixture
def mock_openai_service():
    """Provide mock OpenAI service."""
    pass

@pytest.fixture
def fake_user_data():
    """Provide fake user data for testing."""
    pass

# ❌ BAD
@pytest.fixture
def client():  # Which client? Authenticated?
    pass

@pytest.fixture
def data():  # What data?
    pass
```

## Migration Guide

### Step 1: Identify Non-Compliant Tests
```bash
# Find test functions not following naming standards
grep -r "def test_[^s]" tests/  # Tests not starting with test_should_
grep -r "def test[0-9]" tests/  # Numbered tests
```

### Step 2: Rename Tests
Use the provided script to automatically rename tests:
```bash
python scripts/standardize_test_names.py --dry-run  # Preview changes
python scripts/standardize_test_names.py --apply    # Apply changes
```

### Step 3: Update Test Markers
```python
# Before
def test_auth():
    pass

# After
@pytest.mark.unit
def test_should_authenticate_user_when_valid_credentials_provided():
    """Test user authentication with valid credentials."""
    pass
```

## Benefits of Standardization

1. **Improved Readability**: Clear understanding of test purpose
2. **Better Reporting**: Test names in reports are self-explanatory
3. **Easier Debugging**: Failing test name indicates the problem
4. **Consistent Codebase**: Uniform style across all tests
5. **Better Documentation**: Test names serve as documentation

## Enforcement

### Pre-commit Hook
Add to `.pre-commit-config.yaml`:
```yaml
- repo: local
  hooks:
    - id: check-test-naming
      name: Check test naming conventions
      entry: python scripts/check_test_naming.py
      language: system
      files: test_.*\.py$
```

### CI/CD Check
The CI pipeline will fail if tests don't follow naming conventions.

## Examples of Good Test Names

### Authentication
```python
test_should_return_jwt_token_when_valid_credentials_provided()
test_should_reject_login_when_password_incorrect()
test_should_lock_account_when_max_attempts_exceeded()
```

### Content Management
```python
test_should_create_content_when_all_required_fields_provided()
test_should_update_content_when_user_is_owner()
test_should_deny_content_deletion_when_user_not_authorized()
```

### Real-time Features
```python
test_should_establish_websocket_connection_when_authenticated()
test_should_receive_pusher_events_when_subscribed_to_channel()
test_should_reconnect_websocket_when_connection_lost()
```

## Conclusion

Following these naming standards ensures our test suite remains maintainable, understandable, and valuable as documentation. When in doubt, prioritize clarity over brevity.
# Pusher Test Suite

Comprehensive testing suite for the Pusher real-time implementation in ToolBoxAI Dashboard.

## Test Structure

### 📁 Unit Tests
- **`apps/dashboard/src/services/__tests__/pusher.test.ts`** - Pusher service unit tests
- **`apps/dashboard/src/hooks/__tests__/usePusher.test.ts`** - React hooks unit tests
- **`apps/dashboard/src/test-utils/pusher-mock.ts`** - Mock utilities and test helpers

### 📁 Integration Tests
- **`tests/integration/test_pusher_integration.py`** - Client-server integration tests

### 📁 E2E Tests
- **`tests/e2e/test_pusher_realtime.py`** - End-to-end workflow tests

### 📁 Performance Tests
- **`tests/performance/test_pusher_performance.py`** - Load and performance testing

### 📁 Configuration
- **`tests/pusher_test_config.py`** - Centralized test configuration

## Test Coverage

### ✅ Unit Tests (Frontend)

#### Pusher Service (`pusher.test.ts`)
- ✅ Singleton pattern implementation
- ✅ Connection management (connect/disconnect)
- ✅ Channel subscription/unsubscription
- ✅ Message sending and receiving
- ✅ Event handler registration
- ✅ Authentication flow
- ✅ Reconnection logic with exponential backoff
- ✅ Error handling and recovery
- ✅ Statistics tracking
- ✅ Message queuing when disconnected
- ✅ Token refresh mechanisms

#### React Hooks (`usePusher.test.ts`)
- ✅ `usePusher` - Service access and auto-connection
- ✅ `usePusherChannel` - Channel subscription with cleanup
- ✅ `usePusherConnection` - Connection monitoring
- ✅ `usePusherPresence` - Presence channel management
- ✅ `usePusherEvent` - Event listening
- ✅ `usePusherSend` - Message sending with loading states
- ✅ Hook integration and state coordination
- ✅ Memory leak prevention
- ✅ Performance optimization

#### Test Utilities (`pusher-mock.ts`)
- ✅ Mock Pusher client with full API compatibility
- ✅ Mock channel objects with event simulation
- ✅ Presence functionality mocking
- ✅ Event simulation helpers
- ✅ Connection state management
- ✅ Test scenario builders
- ✅ Assertion helpers

### ✅ Integration Tests (Backend)

#### Client-Server Communication
- ✅ Pusher authentication endpoint testing
- ✅ Webhook endpoint validation
- ✅ Real-time trigger API testing
- ✅ Message delivery verification

#### Real-time Workflows
- ✅ Content generation with progress updates
- ✅ Presence channel member management
- ✅ Private channel authentication
- ✅ System broadcast messaging
- ✅ AI agent status updates

#### Reliability Testing
- ✅ Message ordering and delivery
- ✅ Error handling and recovery
- ✅ Concurrent connection handling
- ✅ Channel limits and throttling
- ✅ Webhook signature validation

#### Security Testing
- ✅ Unauthorized access prevention
- ✅ Message content validation
- ✅ Rate limiting verification
- ✅ JWT token validation

### ✅ E2E Tests (User Workflows)

#### Critical User Flows
- ✅ Content generation with real-time progress
- ✅ Analytics dashboard live updates
- ✅ Multi-user collaboration scenarios
- ✅ Connection recovery and resilience
- ✅ Message ordering guarantees
- ✅ System notification handling

#### Browser Automation
- ✅ Playwright-based modern browser testing
- ✅ Selenium fallback for compatibility
- ✅ Real DOM interaction testing
- ✅ JavaScript execution in browser context
- ✅ Performance monitoring during tests

### ✅ Performance Tests

#### Load Testing
- ✅ Message throughput measurement
- ✅ Concurrent connection scaling
- ✅ Channel subscription limits
- ✅ Message size impact analysis
- ✅ Burst traffic handling

#### Resource Monitoring
- ✅ Memory usage tracking
- ✅ CPU usage monitoring
- ✅ Memory leak detection
- ✅ Connection recovery performance
- ✅ Latency distribution analysis

#### Stress Testing
- ✅ Extreme concurrent connections
- ✅ Message flood resilience
- ✅ System stability under load

## Running Tests

### Frontend Unit Tests
```bash
# Run all dashboard tests
npm -w apps/dashboard test

# Run specific Pusher tests
npm -w apps/dashboard test pusher

# Run with coverage
npm -w apps/dashboard run test:coverage

# Watch mode for development
npm -w apps/dashboard run test:watch
```

### Backend Integration Tests
```bash
# Run integration tests
pytest tests/integration/test_pusher_integration.py -v

# Run with specific markers
pytest -m "integration" tests/integration/ -v

# Run with environment flags
RUN_PUSHER_TESTS=1 pytest tests/integration/test_pusher_integration.py
```

### E2E Tests
```bash
# Run E2E tests (requires running frontend/backend)
pytest tests/e2e/test_pusher_realtime.py -v

# Run with Playwright (recommended)
pip install playwright
playwright install
pytest tests/e2e/test_pusher_realtime.py -v

# Run with Selenium fallback
pytest tests/e2e/test_pusher_realtime.py::TestPusherE2ESelenium -v
```

### Performance Tests
```bash
# Run performance tests
pytest tests/performance/test_pusher_performance.py -v -s

# Run specific performance scenarios
PERFORMANCE_TEST=true pytest tests/performance/test_pusher_performance.py -v

# Run stress tests
pytest tests/performance/test_pusher_performance.py::TestPusherStressTest -v
```

### All Tests
```bash
# Run complete test suite
make test

# Run Pusher-specific tests only
pytest -k "pusher" -v
```

## Test Configuration

### Environment Variables
```bash
# Test mode flags
RUN_PUSHER_TESTS=1        # Enable Pusher-specific tests
PERFORMANCE_TEST=true     # Enable performance test mode
CI=true                   # CI environment adjustments

# Service URLs
VITE_API_BASE_URL=http://localhost:8009
VITE_WS_URL=http://localhost:8009
VITE_PUSHER_KEY=test-pusher-key
VITE_PUSHER_CLUSTER=us2

# Test timeouts
TEST_TIMEOUT=30000        # Default test timeout (ms)
CONNECTION_TIMEOUT=10000  # Connection timeout (ms)
```

### Performance Thresholds

#### Connection Performance
- **Max connection time**: 2s (5s in CI)
- **Max message latency**: 100ms (200ms in CI)
- **Min throughput**: 100 msg/sec (50 in CI)

#### Resource Limits
- **Max memory usage**: 500MB
- **Max CPU usage**: 80%
- **Max concurrent connections**: 1000 (5000 in performance mode)

#### Quality Gates
- **Unit test coverage**: >90%
- **Integration test success**: >95%
- **E2E test success**: >90%
- **Performance test pass**: All thresholds met

## Mock Configurations

### Pusher Service Mock
```typescript
import { createPusherTestEnvironment } from '@/test-utils/pusher-mock';

const { service, scenarios, simulator } = createPusherTestEnvironment();

// Simulate connection
await scenarios.simulateConnection();

// Trigger events
simulator.messageReceived('test-channel', 'content_progress', { percentage: 50 });

// Simulate errors
scenarios.simulateAuthError();
```

### Test Scenarios
```typescript
// Content generation flow
scenarios.simulateMessageFlow('content-generation', [
  { type: 'content_progress', payload: { percentage: 25 } },
  { type: 'content_progress', payload: { percentage: 50 } },
  { type: 'content_complete', payload: { status: 'completed' } }
]);

// Presence simulation
scenarios.simulatePresenceScenario('presence-classroom');

// Network issues
scenarios.simulateNetworkDisconnection();
```

## Debugging Tests

### Debug Modes
```bash
# Verbose output
pytest tests/ -v -s

# Show live logs
pytest tests/ --log-cli-level=DEBUG

# Run single test with debugging
pytest tests/integration/test_pusher_integration.py::TestPusherIntegration::test_content_generation_flow -v -s
```

### Browser Debugging (E2E)
```bash
# Run with browser visible
HEADLESS=false pytest tests/e2e/test_pusher_realtime.py -v

# Enable slow motion
SLOW_MO=500 pytest tests/e2e/test_pusher_realtime.py -v

# Playwright debug mode
PWDEBUG=1 pytest tests/e2e/test_pusher_realtime.py -v
```

### Performance Debugging
```bash
# Run with detailed performance output
pytest tests/performance/test_pusher_performance.py -v -s --tb=short

# Monitor system resources during tests
htop  # In separate terminal
```

## Test Data

### Message Templates
```python
from tests.pusher_test_config import MESSAGE_TEMPLATES, generate_bulk_messages

# Generate test messages
messages = generate_bulk_messages(100, 'content_progress')

# Use predefined templates
notification = MESSAGE_TEMPLATES['system_notification']
```

### Test Users and Classrooms
```python
from tests.pusher_test_config import generate_test_user, generate_test_classroom

# Generate test users
user = generate_test_user(1)  # Creates user-1

# Generate classroom with members
classroom = generate_test_classroom(1, member_count=25)
```

## CI/CD Integration

### GitHub Actions
```yaml
- name: Run Pusher Tests
  run: |
    # Frontend tests
    npm -w apps/dashboard run test:coverage

    # Backend integration tests
    RUN_PUSHER_TESTS=1 pytest tests/integration/test_pusher_integration.py -v

    # Performance tests (lighter load in CI)
    CI=true pytest tests/performance/test_pusher_performance.py -v
  env:
    VITE_PUSHER_KEY: ${{ secrets.TEST_PUSHER_KEY }}
    DATABASE_URL: ${{ secrets.TEST_DATABASE_URL }}
```

### Quality Gates
- All unit tests must pass
- Integration tests >95% success rate
- E2E tests >90% success rate
- Performance thresholds met
- No memory leaks detected
- Security tests passing

## Troubleshooting

### Common Issues

#### Frontend Tests
```bash
# Mock not found
Error: Cannot find module '../services/pusher'
# Solution: Check import paths in test files

# React hooks not updating
# Solution: Use act() wrapper for state changes

# Async operations not completing
# Solution: Use proper async/await in tests
```

#### Integration Tests
```bash
# Connection refused
# Solution: Ensure backend is running on correct port

# Authentication failures
# Solution: Check JWT token generation in tests

# Timeout errors
# Solution: Increase timeout values or check service health
```

#### E2E Tests
```bash
# Element not found
# Solution: Check selectors in SELECTORS config

# Browser automation failures
# Solution: Install browser dependencies (playwright install)

# Timing issues
# Solution: Use proper waits instead of fixed delays
```

#### Performance Tests
```bash
# Memory usage too high
# Solution: Check for mock cleanup in tests

# Throughput below threshold
# Solution: Verify system resources and mock latency

# Stress test failures
# Solution: Adjust limits based on test environment
```

### Logs and Monitoring

#### Test Logs
- Frontend: Browser console logs
- Backend: FastAPI logs
- E2E: Playwright/Selenium logs
- Performance: Resource usage logs

#### Metrics Collection
- Test execution times
- Resource usage patterns
- Error rates and types
- Performance trend analysis

## Contributing

### Adding New Tests

1. **Unit Tests**: Add to appropriate `__tests__` directory
2. **Integration**: Extend `test_pusher_integration.py`
3. **E2E**: Add scenarios to `test_pusher_realtime.py`
4. **Performance**: Add benchmarks to `test_pusher_performance.py`

### Test Patterns

```typescript
// Unit test pattern
describe('Feature', () => {
  beforeEach(() => {
    // Setup
  });

  it('should do something', () => {
    // Arrange
    // Act
    // Assert
  });

  afterEach(() => {
    // Cleanup
  });
});
```

```python
# Integration test pattern
class TestFeature:
    @pytest.fixture
    def setup_data(self):
        # Setup test data
        return data

    @pytest.mark.asyncio
    async def test_feature(self, setup_data):
        # Arrange
        # Act
        # Assert
```

### Best Practices

1. **Isolation**: Each test should be independent
2. **Cleanup**: Always clean up resources
3. **Deterministic**: Tests should be repeatable
4. **Fast**: Unit tests should run quickly
5. **Realistic**: Use realistic test data
6. **Readable**: Clear test names and structure

---

**Test Suite Status**: ✅ Complete
**Coverage**: >90% unit, >95% integration
**Last Updated**: 2025-09-23
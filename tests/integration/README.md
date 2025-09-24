# Integration Testing Suite

This directory contains comprehensive integration tests for the ToolBoxAI educational platform. These tests verify the complete workflows and interactions between multiple system components.

## Test Structure

### Test Files

1. **`test_comprehensive_auth_flow.py`** - Complete authentication and authorization workflows
2. **`test_content_generation_pipeline.py`** - Content generation with multi-agent coordination
3. **`test_database_redis_api_integration.py`** - Database, Redis, and API integration
4. **`test_realtime_communication.py`** - WebSocket and Pusher real-time features
5. **`test_multi_agent_coordination.py`** - Multi-agent orchestration and SPARC framework
6. **`test_e2e_content_workflow.py`** - End-to-end content creation workflow

### Test Suites

- **`basic`** - Quick smoke tests (5 minutes)
- **`auth`** - Authentication tests (10 minutes)
- **`content`** - Content generation tests (30 minutes)
- **`database`** - Database integration tests (15 minutes)
- **`realtime`** - Real-time communication tests (10 minutes)
- **`agents`** - Multi-agent coordination tests (20 minutes)
- **`e2e`** - End-to-end workflow tests (60 minutes)
- **`full`** - Complete test suite (2 hours)

## Prerequisites

### Required Services

1. **PostgreSQL** (port 5434)
   ```bash
   docker run -d --name postgres-test \
     -e POSTGRES_DB=educational_platform_dev \
     -e POSTGRES_USER=eduplatform \
     -e POSTGRES_PASSWORD=eduplatform2024 \
     -p 5434:5432 postgres:15-alpine
   ```

2. **Redis** (port 6381)
   ```bash
   docker run -d --name redis-test \
     -p 6381:6379 redis:7-alpine
   ```

3. **FastAPI Backend** (port 8009)
   ```bash
   cd apps/backend
   uvicorn main:app --host 127.0.0.1 --port 8009 --reload
   ```

4. **Agent Coordinator** (port 8888) - Optional for agent tests
   ```bash
   # Start agent coordinator service
   python -m core.coordinators.main --port 8888
   ```

### Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install additional test dependencies
pip install pytest-asyncio pytest-xdist pytest-timeout httpx websockets
```

## Running Tests

### Using the Test Runner (Recommended)

```bash
# Run basic smoke tests
python tests/integration/test_runner.py basic

# Run specific test suite
python tests/integration/test_runner.py auth content

# Run full integration test suite
python tests/integration/test_runner.py full

# List available test suites
python tests/integration/test_runner.py --list

# Check service availability
python tests/integration/test_runner.py --check-services

# Run with coverage reporting
python tests/integration/test_runner.py --coverage basic
```

### Using pytest Directly

```bash
# Run all integration tests
pytest tests/integration/ -m integration -v

# Run specific test file
pytest tests/integration/test_comprehensive_auth_flow.py -v

# Run with specific markers
pytest tests/integration/ -m "integration and not slow" -v

# Run with parallel execution
pytest tests/integration/ -m integration -n auto --dist loadfile
```

### Environment Variables

```bash
# Enable specific test types
export RUN_INTEGRATION_TESTS=1
export RUN_ENDPOINT_TESTS=1
export RUN_WS_INTEGRATION=1

# Service configuration
export DATABASE_URL="postgresql://eduplatform:eduplatform2024@localhost:5434/educational_platform_dev"
export REDIS_URL="redis://localhost:6381/0"

# Mock configuration
export USE_MOCK_LLM=true
export USE_MOCK_DATABASE=false
export USE_MOCK_REDIS=false

# Pusher configuration (optional)
export PUSHER_ENABLED=true
export PUSHER_KEY=your_key
export PUSHER_SECRET=your_secret
export PUSHER_CLUSTER=us2
```

## Test Categories

### 1. Authentication Flow Tests (`test_comprehensive_auth_flow.py`)

Tests complete user authentication and authorization:

- **User Registration**: Email verification, duplicate prevention, validation
- **Login Flow**: JWT token generation, refresh mechanisms, rate limiting
- **Role-Based Access**: Admin, teacher, student permission boundaries
- **Security**: Token validation, expiration, tampering detection
- **Concurrency**: Multiple simultaneous login attempts

**Key Test Methods:**
- `test_successful_login_flow` - Basic login workflow
- `test_role_based_access_control` - Permission testing
- `test_token_security` - Security validation
- `test_concurrent_auth_operations` - Load testing

### 2. Content Generation Pipeline (`test_content_generation_pipeline.py`)

Tests the complete content creation workflow:

- **Basic Generation**: Simple content requests and responses
- **Roblox Integration**: Terrain and script generation
- **Multi-Agent Coordination**: Parallel agent execution
- **Error Handling**: Retry mechanisms, fallback strategies
- **Performance**: Benchmarking and optimization

**Key Test Methods:**
- `test_simple_content_generation` - Basic functionality
- `test_roblox_environment_generation` - Roblox-specific features
- `test_parallel_agent_execution` - Multi-agent workflows
- `test_content_persistence` - Database storage

### 3. Database + Redis + API Integration (`test_database_redis_api_integration.py`)

Tests data consistency across storage layers:

- **Transaction Integrity**: ACID compliance, rollback scenarios
- **Cache Behavior**: Hit/miss patterns, invalidation
- **API Integration**: Endpoint coordination with data layers
- **Performance**: Cache optimization, bulk operations
- **Consistency**: Data synchronization across components

**Key Test Methods:**
- `test_successful_transaction_commit` - Database reliability
- `test_cache_invalidation_on_update` - Cache consistency
- `test_concurrent_database_operations` - Concurrency handling
- `test_performance_with_both_systems` - Optimization validation

### 4. Real-time Communication (`test_realtime_communication.py`)

Tests WebSocket and Pusher integration:

- **WebSocket Connections**: Establishment, authentication, limits
- **Pusher Integration**: Channel management, event triggering
- **Message Flow**: End-to-end delivery, broadcasting
- **Cross-Platform**: WebSocket ↔ Pusher compatibility
- **Performance**: High-frequency messaging, stability

**Key Test Methods:**
- `test_websocket_connection_establishment` - Connection basics
- `test_pusher_authentication_endpoint` - Channel auth
- `test_realtime_message_flow` - Message delivery
- `test_high_frequency_message_handling` - Performance testing

### 5. Multi-Agent Coordination (`test_multi_agent_coordination.py`)

Tests agent orchestration and SPARC framework:

- **Agent Discovery**: Registration, health monitoring, load balancing
- **Task Distribution**: Assignment algorithms, priority handling
- **Consensus Mechanisms**: Decision making, result aggregation
- **SPARC Integration**: Structured reasoning chains
- **Fault Tolerance**: Recovery, retry mechanisms, circuit breakers

**Key Test Methods:**
- `test_agent_registration` - Service discovery
- `test_complex_multi_agent_task` - Orchestration workflows
- `test_consensus_decision_making` - Agreement protocols
- `test_sparc_reasoning_chain` - SPARC framework
- `test_agent_failure_recovery` - Fault tolerance

### 6. End-to-End Content Workflow (`test_e2e_content_workflow.py`)

Tests complete user-to-delivery workflows:

- **Full Pipeline**: User authentication → Content generation → Delivery
- **Quality Assurance**: Content review and approval workflows
- **Student Interaction**: Access, quiz taking, progress tracking
- **Analytics**: Performance monitoring and reporting
- **Error Scenarios**: Partial failures, timeout handling

**Key Test Methods:**
- `test_full_content_creation_pipeline` - Complete workflow
- `test_content_generation_performance` - End-to-end timing
- `test_workflow_error_handling` - Failure scenarios
- `test_database_consistency_during_workflow` - Data integrity

## Test Configuration

### Markers

Tests use pytest markers for categorization:

```python
@pytest.mark.integration      # All integration tests
@pytest.mark.asyncio         # Async tests
@pytest.mark.slow            # Long-running tests (>30s)
@pytest.mark.requires_postgres  # Requires PostgreSQL
@pytest.mark.requires_redis     # Requires Redis
@pytest.mark.websocket         # WebSocket tests
@pytest.mark.pusher           # Pusher integration tests
@pytest.mark.e2e             # End-to-end tests
```

### Fixtures

Common fixtures available across tests:

- `integration_client` - HTTP client for API testing
- `auth_headers` - Pre-configured authentication headers
- `test_users` - Multi-role user data
- `mock_agent_pool` - Controlled agent mocking
- `redis_client` - Redis connection for cache testing

### Timeouts

Tests have appropriate timeouts:

- **Unit-style integration tests**: 30 seconds
- **Content generation tests**: 60 seconds
- **Multi-agent tests**: 120 seconds
- **End-to-end tests**: 300 seconds

## Coverage Goals

The integration test suite aims for:

- **API Endpoint Coverage**: 85%+ of critical endpoints
- **Workflow Coverage**: 90%+ of user-facing workflows
- **Error Path Coverage**: 70%+ of error scenarios
- **Cross-Component Integration**: 80%+ of component interactions

## Troubleshooting

### Common Issues

1. **Service Connection Failures**
   ```bash
   # Check service status
   python tests/integration/test_runner.py --check-services

   # Verify ports are available
   lsof -i :8009 -i :5434 -i :6381
   ```

2. **Database Connection Issues**
   ```bash
   # Test database connection
   psql postgresql://eduplatform:eduplatform2024@localhost:5434/educational_platform_dev
   ```

3. **Redis Connection Issues**
   ```bash
   # Test Redis connection
   redis-cli -h localhost -p 6381 ping
   ```

4. **WebSocket Connection Failures**
   ```bash
   # Check WebSocket endpoint
   curl -i -N \
     -H "Connection: Upgrade" \
     -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Version: 13" \
     -H "Sec-WebSocket-Key: $(echo -n test | base64)" \
     http://127.0.0.1:8009/ws
   ```

### Debug Mode

Enable debug mode for detailed output:

```bash
export LOG_LEVEL=DEBUG
export TESTING_VERBOSE=true
pytest tests/integration/ -v -s --log-cli-level=DEBUG
```

### Parallel Execution Issues

If parallel tests fail:

```bash
# Run tests sequentially
pytest tests/integration/ -m integration --dist=no

# Or use fewer workers
pytest tests/integration/ -m integration -n 2
```

## Performance Benchmarks

Expected performance baselines:

| Test Category | Expected Duration | Success Rate |
|---------------|------------------|--------------|
| Basic         | < 5 minutes      | > 95%        |
| Auth          | < 10 minutes     | > 90%        |
| Content       | < 30 minutes     | > 85%        |
| Database      | < 15 minutes     | > 95%        |
| Realtime      | < 10 minutes     | > 90%        |
| Agents        | < 20 minutes     | > 80%        |
| E2E           | < 60 minutes     | > 75%        |

## Continuous Integration

### GitHub Actions Integration

```yaml
name: Integration Tests
on: [push, pull_request]
jobs:
  integration:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: educational_platform_dev
          POSTGRES_USER: eduplatform
          POSTGRES_PASSWORD: eduplatform2024
        ports:
          - 5434:5432
      redis:
        image: redis:7-alpine
        ports:
          - 6381:6379
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run integration tests
        run: python tests/integration/test_runner.py basic auth database
```

### Local CI Simulation

```bash
# Simulate CI environment
export CI=true
export GITHUB_ACTIONS=true

# Run CI test suite
python tests/integration/test_runner.py basic auth database
```

## Contributing

### Adding New Integration Tests

1. **Choose appropriate test file** based on component focus
2. **Follow naming conventions**: `test_<feature>_<scenario>`
3. **Use proper markers**: Add relevant pytest markers
4. **Include error scenarios**: Test both success and failure paths
5. **Add performance assertions**: Include timing validations
6. **Document requirements**: List any additional service dependencies

### Test Development Guidelines

- **Isolation**: Tests should not depend on execution order
- **Cleanup**: Use fixtures for proper setup/teardown
- **Timeouts**: Include appropriate timeout values
- **Logging**: Add informative log messages for debugging
- **Assertions**: Use descriptive assertion messages
- **Mock External APIs**: Mock third-party services consistently

### Review Checklist

- [ ] Test covers integration between multiple components
- [ ] Includes both success and failure scenarios
- [ ] Has appropriate timeout configuration
- [ ] Uses proper pytest markers
- [ ] Includes performance/timing assertions
- [ ] Has clear documentation and comments
- [ ] Follows project coding standards
- [ ] Includes proper error handling

---

For questions or issues with the integration test suite, please check the troubleshooting section or create an issue in the project repository.
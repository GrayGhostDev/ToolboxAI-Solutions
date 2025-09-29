# Chaos Engineering Test Suite

This directory contains comprehensive chaos engineering tests designed to validate the resilience and fault tolerance of the ToolBoxAI load balancing infrastructure under various failure conditions.

## Overview

Chaos engineering is the practice of intentionally introducing failures into a system to test its resilience and identify weaknesses before they cause outages in production. These tests validate that:

- Circuit breakers prevent cascading failures
- Rate limiting protects against overload
- Database replicas take over when primary fails
- Cache continues serving stale content during outages
- WebSocket sessions reconnect properly
- Global load balancer routes around failures
- System recovers gracefully after failures are resolved

## Test Categories

### 1. Network Partition Tests (`TestNetworkPartitionSimulation`)
- **Service Isolation**: Tests behavior when services are network isolated
- **Split-Brain Scenarios**: Validates conflict resolution when multiple regions think they're primary
- **Cross-Region Communication**: Tests failover when regions lose connectivity

### 2. Service Failure Injection (`TestServiceFailureInjection`)
- **Random Service Crashes**: Simulates unexpected service failures
- **Cascading Failure Prevention**: Validates circuit breaker effectiveness
- **Service Recovery**: Tests automatic recovery and health checks

### 3. Resource Exhaustion (`TestResourceExhaustion`)
- **CPU Exhaustion**: Tests system behavior under high CPU load
- **Memory Pressure**: Validates memory management and garbage collection
- **Connection Pool Exhaustion**: Tests connection limit handling

### 4. Database Failover (`TestDatabaseFailoverSimulation`)
- **Primary Database Failure**: Tests replica takeover scenarios
- **Split-Brain Database**: Validates write conflict resolution
- **Data Consistency**: Ensures eventual consistency across regions

### 5. Cache Poisoning (`TestCachePoisoning`)
- **Cache Corruption**: Tests fallback to database when cache is corrupted
- **Poisoning Attacks**: Validates protection against malicious cache data
- **Cache Recovery**: Tests cache health monitoring and recovery

### 6. Rate Limit Stress Testing (`TestRateLimitStressTesting`)
- **Traffic Floods**: Tests rate limiter under overwhelming traffic
- **Distributed Rate Limiting**: Validates coordination across multiple instances
- **Adaptive Rate Limiting**: Tests adjustment based on system health

### 7. WebSocket Mass Disconnection (`TestWebSocketMassDisconnection`)
- **Connection Storms**: Tests handling of massive concurrent connections
- **Mass Disconnection**: Validates graceful handling of network issues
- **Message Flooding**: Tests WebSocket message rate limiting

### 8. Region Failure Simulation (`TestRegionFailureSimulation`)
- **Entire Region Failure**: Tests global load balancer failover
- **Cross-Region Consistency**: Validates data synchronization during failures
- **Recovery Procedures**: Tests region recovery and traffic restoration

### 9. Latency Injection (`TestLatencyInjection`)
- **High Latency Handling**: Tests timeout and circuit breaker behavior
- **Gradual Latency Increase**: Validates adaptive timeout mechanisms
- **Network Degradation**: Tests system adaptation to poor network conditions

### 10. Comprehensive Scenarios
- **Multi-Failure Scenarios**: Simultaneous multiple failure modes
- **System Resilience Validation**: End-to-end resilience testing
- **Recovery Verification**: Comprehensive recovery validation

## Safety Mechanisms

### Environment Isolation
- Tests run in isolated environments to prevent production impact
- Separate test databases and Redis instances
- Mock external service dependencies
- Automated cleanup and recovery procedures

### Safety Controls
- Maximum test duration limits (10 minutes default)
- Emergency stop mechanisms
- Resource usage monitoring
- Automatic failure injection timeout

### Test Isolation
- Each test runs in isolated context
- Fixtures provide clean state for each test
- Automatic cleanup of test artifacts
- Proper exception handling and recovery

## Usage

### Prerequisites

```bash
# Ensure test environment
export ENVIRONMENT=chaos_test

# Configure test database
export DATABASE_URL=postgresql://user:pass@localhost/toolboxai_chaos_test

# Configure test Redis
export REDIS_URL=redis://localhost:6379/15
```

### Running Tests

#### Using the Test Runner (Recommended)

```bash
# Run all chaos tests
python tests/chaos/run_chaos_tests.py

# Run specific categories
python tests/chaos/run_chaos_tests.py --category network --category database

# Dry run to validate setup
python tests/chaos/run_chaos_tests.py --dry-run

# Run with custom timeout and report
python tests/chaos/run_chaos_tests.py --timeout 300 --report chaos_report.json

# Verbose output for debugging
python tests/chaos/run_chaos_tests.py --verbose
```

#### Using Pytest Directly

```bash
# Run all chaos tests
pytest tests/chaos/test_chaos_engineering.py -v -m chaos

# Run specific test class
pytest tests/chaos/test_chaos_engineering.py::TestNetworkPartitionSimulation -v

# Run with timeout
pytest tests/chaos/test_chaos_engineering.py -v --timeout=300
```

### Command Line Options

```bash
python tests/chaos/run_chaos_tests.py --help

Options:
  --category {network,service,resource,database,cache,rate_limit,websocket,region,latency}
                        Test categories to run (can be specified multiple times)
  --timeout TIMEOUT     Maximum test execution time in seconds (default: 600)
  --max-failures MAX_FAILURES
                        Maximum number of test failures before stopping (default: 5)
  --parallel            Run tests in parallel
  --no-mock-external    Disable mocking of external services (dangerous!)
  --no-isolation        Disable environment isolation (dangerous!)
  --report REPORT_FILE  Generate JSON report to specified file
  --dry-run             Validate setup without running tests
  --verbose             Enable verbose output
```

## Configuration

### Environment Variables

```bash
# Required
ENVIRONMENT=chaos_test                    # Must be test/chaos_test/development
DATABASE_URL=postgresql://...             # Test database URL
REDIS_URL=redis://localhost:6379/15      # Test Redis URL

# Optional
CHAOS_MAX_DURATION=300                    # Maximum test duration (seconds)
CHAOS_SAFETY_ENABLED=true                # Enable safety mechanisms
CHAOS_MOCK_EXTERNAL=true                 # Mock external services
CHAOS_ISOLATED=true                       # Enable environment isolation
CHAOS_MONITORING=true                     # Enable test monitoring
```

### Test Configuration

Edit `tests/chaos/conftest.py` to customize:

- Safety timeouts and limits
- Mock service configurations
- Monitoring and logging settings
- Test isolation parameters

## Safety Guidelines

### ⚠️ IMPORTANT SAFETY NOTICES

1. **Never run chaos tests in production environments**
2. **Always verify environment safety before running tests**
3. **Use isolated test databases and services**
4. **Monitor system resources during test execution**
5. **Have recovery procedures ready**

### Environment Verification

The test runner automatically verifies:
- Environment is not production
- Test databases are configured
- Required dependencies are available
- Safety mechanisms are enabled

### Emergency Procedures

If tests cause system issues:

1. **Stop tests immediately**: `Ctrl+C` or kill process
2. **Check system resources**: CPU, memory, disk usage
3. **Restart services**: Backend, database, Redis
4. **Clean test data**: Clear test databases
5. **Review logs**: Check for error patterns

## Monitoring and Reporting

### Test Monitoring

Tests automatically collect:
- Performance metrics during failures
- Error rates and response times
- Resource utilization patterns
- Recovery time measurements

### Report Generation

```bash
# Generate detailed JSON report
python tests/chaos/run_chaos_tests.py --report chaos_results.json

# View report summary
cat chaos_results.json | jq '.results[] | {name: .name, status: .status}'
```

### Log Analysis

```bash
# View test logs
tail -f /var/log/chaos_tests.log

# Monitor system during tests
watch -n 1 'ps aux | grep python; free -h; df -h'
```

## Extending the Test Suite

### Adding New Failure Scenarios

1. Create new test class in `test_chaos_engineering.py`
2. Implement failure injection method
3. Add validation logic for expected behavior
4. Include cleanup procedures
5. Add appropriate pytest markers

Example:

```python
class TestNewFailureScenario:
    @pytest.mark.asyncio
    @pytest.mark.chaos
    @pytest.mark.new_category_chaos
    async def test_new_failure_mode(self, chaos_test_environment):
        async def inject_failure():
            # Implement failure injection
            pass

        async def validate_behavior():
            # Validate expected system behavior
            pass

        await inject_failure()
        await validate_behavior()
```

### Adding New Test Categories

1. Define new marker in `conftest.py`
2. Add category to command line options
3. Update documentation
4. Add specific fixtures if needed

## Troubleshooting

### Common Issues

**Tests timeout or hang**
- Check system resources (CPU, memory)
- Verify mock services are responding
- Increase timeout or reduce test scope

**Database connection errors**
- Verify test database is running
- Check DATABASE_URL configuration
- Ensure database permissions

**Import errors**
- Verify all dependencies are installed
- Check Python path configuration
- Activate virtual environment

**Permission denied errors**
- Check file permissions
- Verify user has access to test resources
- Run with appropriate privileges

### Debug Mode

```bash
# Run single test with full debugging
python -m pytest tests/chaos/test_chaos_engineering.py::TestSpecificTest -v -s --tb=long

# Enable debug logging
PYTHONPATH=. python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
# Run specific test code
"
```

## Contributing

When contributing to the chaos engineering test suite:

1. **Follow safety guidelines** - Never compromise on safety
2. **Add comprehensive tests** - Cover both failure and recovery
3. **Include proper cleanup** - Ensure tests don't leave artifacts
4. **Document thoroughly** - Explain failure scenarios and expectations
5. **Test thoroughly** - Validate in isolated environment first

### Review Checklist

- [ ] Test runs in isolated environment
- [ ] Proper safety mechanisms implemented
- [ ] Comprehensive failure injection
- [ ] Behavior validation included
- [ ] Cleanup procedures working
- [ ] Documentation updated
- [ ] Safety review completed

## References

- [Chaos Engineering Principles](https://principlesofchaos.org/)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Rate Limiting Strategies](https://cloud.google.com/architecture/rate-limiting-strategies)
- [Database Failover Best Practices](https://docs.aws.amazon.com/rds/latest/userguide/Concepts.MultiAZ.html)
- [WebSocket Resilience Patterns](https://websockets.spec.whatwg.org/)

---

*This chaos engineering test suite is designed to improve system resilience through controlled failure injection. Always prioritize safety and follow established procedures.*
# ToolboxAI Testing Infrastructure

## Overview

This document describes the comprehensive testing infrastructure created for the ToolboxAI project. The testing suite validates WebSocket to Pusher migration, security compliance, educational regulations compliance, and complete user journeys.

## Test Structure

```
tests/
├── migration/              # WebSocket to Pusher migration tests
│   └── test_websocket_to_pusher.py
├── documentation/          # Documentation validation tests
│   └── validate_pusher_docs.py
├── security/              # Security compliance tests
│   └── test_security_compliance.py
├── compliance/            # Educational compliance tests (COPPA, FERPA, GDPR)
│   └── test_educational_compliance.py
├── flows/                 # User journey tests
│   └── test_student_journey.py
├── performance/           # Load and performance tests
│   └── locustfile.py
└── fixtures/              # Test utilities and helpers
    └── pusher_test_utils.py (already exists)
```

## Test Categories

### 1. Migration Tests
- **Purpose**: Validate WebSocket to Pusher migration
- **Location**: `tests/migration/`
- **Coverage Target**: 95%
- **Key Features**:
  - WebSocket endpoint deprecation warnings
  - Pusher channel equivalency
  - Backwards compatibility adapter
  - Real-time event triggering

### 2. Documentation Validation
- **Purpose**: Ensure documentation reflects current system state
- **Location**: `tests/documentation/`
- **Coverage Target**: 80%
- **Key Features**:
  - WebSocket references marked as deprecated
  - Pusher channels properly documented
  - API documentation consistency
  - Environment configuration validation

### 3. Security Compliance
- **Purpose**: Validate security best practices
- **Location**: `tests/security/`
- **Coverage Target**: 90%
- **Key Features**:
  - Secret detection (no exposed API keys)
  - Dependency vulnerability scanning
  - Code security analysis (bandit)
  - SQL injection prevention
  - File upload security

### 4. Educational Compliance
- **Purpose**: Ensure compliance with educational regulations
- **Location**: `tests/compliance/`
- **Coverage Target**: 85%
- **Key Features**:
  - COPPA compliance (users under 13)
  - FERPA compliance (student data privacy)
  - GDPR compliance (data deletion, portability)
  - Data retention policies
  - Accessibility compliance

### 5. User Flow Tests
- **Purpose**: Validate complete user journeys
- **Location**: `tests/flows/`
- **Coverage Target**: 80%
- **Key Features**:
  - Student journey (login to quiz completion)
  - Teacher workflow (dashboard to assignment creation)
  - Admin system management
  - Real-time collaboration
  - Roblox plugin interactions

### 6. Performance Tests
- **Purpose**: Load testing and performance validation
- **Location**: `tests/performance/`
- **Coverage Target**: 70%
- **Key Features**:
  - Pusher event triggering load tests
  - API endpoint performance
  - WebSocket legacy fallback testing
  - Concurrent user simulation

## Running Tests

### Quick Start

```bash
# Run all comprehensive tests (Bash version)
./run_comprehensive_tests.sh

# Run all comprehensive tests (Python version)
python run_comprehensive_tests.py

# Run specific category
python run_comprehensive_tests.py --category migration_tests
python run_comprehensive_tests.py --category security_compliance
```

### Available Categories

- `migration_tests` - WebSocket to Pusher migration validation
- `documentation_validation` - Documentation accuracy checks
- `security_compliance` - Security best practices validation
- `educational_compliance` - COPPA, FERPA, GDPR compliance
- `user_flow_tests` - Complete user journey testing
- `performance` - Load and performance testing
- `docker_integration` - Docker service integration
- `supabase_integration` - Database integration tests
- `mantine_ui` - Frontend UI component tests
- `end_to_end` - E2E integration tests
- `existing_integration` - Legacy integration tests

### Command Line Options

```bash
# Python runner options
python run_comprehensive_tests.py --help

Options:
  --verbose, -v          Enable verbose output
  --no-coverage         Disable coverage reporting
  --category CATEGORY   Run specific category only
  --save-results        Save results to files (default: true)

# Examples
python run_comprehensive_tests.py --verbose --category security_compliance
python run_comprehensive_tests.py --no-coverage --category performance
```

### Bash Runner Options

```bash
# The bash runner automatically handles:
# - Environment setup
# - Dependency checking
# - Service startup (if needed)
# - Report generation
# - Cleanup

./run_comprehensive_tests.sh
```

## Environment Setup

### Required Environment Variables

```bash
export TESTING=true
export USE_MOCK_LLM=true
export PUSHER_ENABLED=true
export DATABASE_URL="postgresql://testuser:testpass@localhost:5432/testdb"
export REDIS_URL="redis://localhost:6379/1"
```

### Required Dependencies

```bash
# Security tools
pip install bandit safety detect-secrets

# Performance testing
pip install locust

# Testing framework
pip install pytest pytest-cov pytest-asyncio httpx
```

## Test Reports

### Generated Reports

Tests generate multiple types of reports:

1. **JSON Report**: Detailed results in JSON format
   - Location: `test-reports/comprehensive_test_report_TIMESTAMP.json`
   - Contains: Full test results, timing, coverage data

2. **HTML Report**: Human-readable test report
   - Location: `test-reports/comprehensive_test_report_TIMESTAMP.html`
   - Contains: Visual summary, phase details, recommendations

3. **Coverage Report**: Code coverage analysis
   - Location: `test-reports/coverage/index.html`
   - Contains: Line-by-line coverage analysis

4. **Summary Report**: Quick overview
   - Location: `test-reports/test_summary_TIMESTAMP.json`
   - Contains: High-level statistics and status

### Report Analysis

The test runner provides:

- **Success Rate**: Percentage of test phases that passed
- **Coverage Analysis**: Code coverage by category
- **Performance Metrics**: Response times and throughput
- **Compliance Status**: Regulatory compliance validation
- **Security Assessment**: Security vulnerability analysis

## Integration with CI/CD

### GitHub Actions Integration

Add to `.github/workflows/comprehensive-tests.yml`:

```yaml
name: Comprehensive Tests

on: [push, pull_request]

jobs:
  comprehensive-tests:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install bandit safety detect-secrets locust

    - name: Run comprehensive tests
      run: python run_comprehensive_tests.py --save-results

    - name: Upload test reports
      uses: actions/upload-artifact@v3
      with:
        name: test-reports
        path: test-reports/
```

### Docker Integration

The test suite works with Docker services:

```bash
# Start services
docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d

# Run tests
python run_comprehensive_tests.py

# Cleanup
docker-compose -f infrastructure/docker/docker-compose.dev.yml down
```

## Customization

### Adding New Test Categories

1. Create test directory under `tests/`
2. Add test files with appropriate pytest markers
3. Update `run_comprehensive_tests.py`:
   - Add to `test_categories` dict
   - Set coverage target in `coverage_targets`
   - Add marker mapping

### Custom Test Fixtures

Test utilities are available in `tests/fixtures/`:

- `pusher_test_utils.py` - Pusher testing helpers
- `async_helpers.py` - Async test utilities
- `auth.py` - Authentication test helpers
- `database.py` - Database test fixtures

## Troubleshooting

### Common Issues

1. **Missing Dependencies**
   - Install security tools: `pip install bandit safety detect-secrets`
   - Install performance tools: `pip install locust`

2. **Service Dependencies**
   - Ensure PostgreSQL is running on port 5432
   - Ensure Redis is running on port 6379
   - Check backend server is running on port 8009

3. **Permission Issues**
   - Make scripts executable: `chmod +x run_comprehensive_tests.sh`
   - Check file permissions in test directories

4. **Environment Issues**
   - Activate virtual environment: `source venv/bin/activate`
   - Set PYTHONPATH: `export PYTHONPATH=/path/to/project:$PYTHONPATH`

### Debug Mode

```bash
# Enable verbose output
python run_comprehensive_tests.py --verbose

# Run single category with maximum detail
pytest tests/migration/ -v -s --tb=long
```

## Best Practices

1. **Regular Execution**: Run comprehensive tests before each release
2. **Coverage Monitoring**: Maintain coverage targets above 85%
3. **Security Updates**: Update security tools regularly
4. **Compliance Reviews**: Review compliance tests quarterly
5. **Performance Baselines**: Track performance metrics over time

## Success Criteria

### Ready for Production
- All critical test phases pass
- Security compliance: 90%+ coverage
- Educational compliance: All regulations validated
- User flows: All major journeys tested
- Performance: Meets baseline requirements

### Deployment Gates
- Required test phases: Must pass (exit code 0)
- Optional test phases: Warnings allowed
- Coverage targets: Must meet category minimums
- Security scans: No critical vulnerabilities

## Support

For questions about the testing infrastructure:

1. Check this documentation
2. Review test logs in `test-runner.log`
3. Examine generated reports in `test-reports/`
4. Check individual test outputs with `--verbose` flag

The testing infrastructure ensures the ToolboxAI platform meets enterprise standards for security, compliance, and reliability.
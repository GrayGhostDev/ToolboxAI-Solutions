# Supabase Migration Test Suite

This document describes the comprehensive test suite for the Supabase migration system, which provides automated testing for PostgreSQL to Supabase database migration workflows.

## Overview

The test suite covers:
- **Unit Tests**: Individual component testing with >90% coverage target
- **Integration Tests**: End-to-end workflow testing
- **Tool Tests**: Specific migration tool validation
- **Performance Tests**: Migration performance benchmarking

## Test Structure

```
tests/
├── unit/core/agents/
│   ├── test_supabase_migration_agent.py     # Main agent tests
│   ├── test_schema_analyzer_tool.py         # Schema analysis tests
│   ├── test_rls_policy_generator_tool.py    # RLS policy tests
│   ├── test_data_migration_tool.py          # Data migration tests
│   └── conftest.py                          # Unit test configuration
├── integration/
│   └── test_supabase_migration.py           # Integration workflow tests
├── fixtures/
│   └── supabase_migration.py                # Shared test fixtures
└── SUPABASE_MIGRATION_TESTS.md              # This documentation
```

## Test Components

### 1. Unit Tests (`/tests/unit/core/agents/`)

#### SupabaseMigrationAgent Tests (`test_supabase_migration_agent.py`)
- **Test Coverage**: 100+ test cases
- **Key Areas**:
  - Agent initialization and configuration
  - Database analysis workflow
  - Migration plan generation
  - Migration execution (dry-run and actual)
  - Validation and rollback procedures
  - Task processing and error handling
  - SPARC framework integration

**Sample Test Cases**:
```python
@pytest.mark.asyncio
async def test_analyze_database_success()
async def test_generate_migration_plan()
async def test_execute_migration_dry_run()
async def test_validate_migration()
```

#### SchemaAnalyzerTool Tests (`test_schema_analyzer_tool.py`)
- **Test Coverage**: 80+ test cases
- **Key Areas**:
  - Database connection and analysis
  - Table, view, and relationship extraction
  - Schema compatibility validation
  - Migration complexity assessment
  - Error handling and edge cases

**Sample Test Cases**:
```python
@pytest.mark.asyncio
async def test_analyze_success()
async def test_extract_relationships()
def test_generate_migration_report_complex()
```

#### RLSPolicyGeneratorTool Tests (`test_rls_policy_generator_tool.py`)
- **Test Coverage**: 70+ test cases
- **Key Areas**:
  - Policy generation for different table types
  - Access pattern analysis
  - SQL generation and validation
  - Multi-tenant, hierarchical, and time-based policies
  - Policy validation against schema

**Sample Test Cases**:
```python
@pytest.mark.asyncio
async def test_generate_policies_with_access_patterns()
def test_generate_user_policies()
def test_validate_policies_valid()
```

#### DataMigrationTool Tests (`test_data_migration_tool.py`)
- **Test Coverage**: 90+ test cases
- **Key Areas**:
  - Batch processing and parallel execution
  - Data validation and integrity checks
  - Incremental migration support
  - Rollback and error recovery
  - Performance optimization

**Sample Test Cases**:
```python
@pytest.mark.asyncio
async def test_migrate_table_actual()
async def test_incremental_migration()
async def test_validate_migration_basic()
```

### 2. Integration Tests (`/tests/integration/`)

#### Full Workflow Tests (`test_supabase_migration.py`)
- **Test Coverage**: 20+ comprehensive scenarios
- **Key Areas**:
  - Complete migration workflow (analysis → planning → execution → validation)
  - Complex schema migration with dependencies
  - Large dataset simulation
  - Performance validation
  - Rollback integration
  - Real-world scenario testing

**Sample Test Cases**:
```python
@pytest.mark.asyncio
async def test_full_migration_workflow()
async def test_migration_with_complex_dependencies()
async def test_migration_with_large_dataset_simulation()
```

### 3. Test Fixtures (`/tests/fixtures/`)

#### Comprehensive Test Data (`supabase_migration.py`)
- **Educational Platform Schema**: Realistic multi-table schema with:
  - Organizations, Users, Lessons, Enrollments tables
  - Complex foreign key relationships
  - Various data types (UUID, JSONB, ENUM, etc.)
  - Realistic row counts and constraints

- **Access Patterns**: Multi-tenant, hierarchical, and time-based patterns
- **Mock Objects**: Database connections, OpenAI client, state manager
- **Test Utilities**: Helper classes and validation functions

## Running Tests

### Quick Start
```bash
# Run all tests with coverage
python scripts/test_supabase_migration.py --all --verbose

# Run only unit tests
python scripts/test_supabase_migration.py --unit

# Run integration tests
python scripts/test_supabase_migration.py --integration

# Generate coverage report
python scripts/test_supabase_migration.py --coverage
```

### Tool-Specific Testing
```bash
# Test schema analyzer
python scripts/test_supabase_migration.py --tool schema_analyzer

# Test RLS policy generator
python scripts/test_supabase_migration.py --tool rls_policy

# Test data migration
python scripts/test_supabase_migration.py --tool data_migration

# Test main migration agent
python scripts/test_supabase_migration.py --tool migration_agent
```

### Environment Validation
```bash
# Validate test environment setup
python scripts/test_supabase_migration.py --validate

# Quick functionality test
python scripts/test_supabase_migration.py --quick
```

### Using pytest directly
```bash
# Run specific test file
pytest tests/unit/core/agents/test_supabase_migration_agent.py -v

# Run with coverage
pytest tests/unit/core/agents/ --cov=core.agents.supabase --cov-report=html

# Run with markers
pytest -m "supabase or schema_analysis" -v
```

## Test Configuration

### Environment Variables
```bash
# Optional: Enable real database testing (use with caution)
export SUPABASE_TEST_DB_URL="postgresql://..."
export SUPABASE_TARGET_DB_URL="postgresql://..."

# OpenAI API (mocked by default)
export OPENAI_API_KEY="test-key-for-mocking"

# Test mode configuration
export TESTING_MODE="true"
export MOCK_EXTERNAL_APIS="true"
```

### Pytest Configuration
The test suite uses custom markers:
- `@pytest.mark.supabase`: Supabase migration tests
- `@pytest.mark.schema_analysis`: Schema analysis specific tests
- `@pytest.mark.rls_policy`: RLS policy specific tests
- `@pytest.mark.data_migration`: Data migration specific tests
- `@pytest.mark.migration_agent`: Migration agent specific tests
- `@pytest.mark.slow`: Tests that take longer to run
- `@pytest.mark.performance`: Performance benchmarking tests

## Coverage Targets

### Current Coverage Goals
- **Overall Coverage**: >90%
- **Unit Test Coverage**: >95%
- **Integration Test Coverage**: >85%
- **Critical Path Coverage**: 100%

### Coverage Reports
Coverage reports are generated in:
- **Terminal**: Summary during test runs
- **HTML**: `htmlcov/supabase_migration/index.html`
- **XML**: For CI/CD integration

### Coverage Areas
1. **Core Agent Logic**: 100% coverage required
2. **Tool Functions**: >95% coverage target
3. **Error Handling**: 100% coverage required
4. **Configuration**: >90% coverage target

## Test Data and Scenarios

### Realistic Test Scenarios

#### 1. Educational Platform Migration
- **Tables**: 4 core tables with realistic relationships
- **Data Volume**: 65,600 total rows across tables
- **Complexity**: Medium complexity with foreign keys
- **Features**: Multi-tenant access, JSONB content, ENUM types

#### 2. Large Dataset Simulation
- **Scale**: 1M+ rows for performance testing
- **Batch Processing**: 5K row batches with concurrent processing
- **Validation**: Row count and data integrity verification

#### 3. Complex Schema Migration
- **Dependencies**: Multi-level foreign key dependencies
- **Constraints**: Check constraints, unique constraints
- **Advanced Types**: JSONB, UUID, custom ENUMs
- **Views and Functions**: Complex view definitions

### Mock Data Quality
- **Realistic UUIDs**: Proper UUID4 format
- **Valid Relationships**: All foreign keys reference existing records
- **Diverse Data Types**: String, numeric, JSON, timestamp data
- **Edge Cases**: NULL values, empty strings, boundary conditions

## Continuous Integration

### GitHub Actions Integration
```yaml
# Example CI configuration
- name: Run Supabase Migration Tests
  run: |
    python scripts/test_supabase_migration.py --all --verbose
    python scripts/test_supabase_migration.py --coverage
```

### Pre-commit Hooks
```bash
# Run tests before commit
python scripts/test_supabase_migration.py --quick
```

### Performance Benchmarking
- **Baseline Metrics**: Established performance baselines
- **Regression Detection**: Automatic performance regression detection
- **Optimization Tracking**: Track improvements over time

## Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Ensure project root is in PYTHONPATH
export PYTHONPATH="/path/to/project:$PYTHONPATH"

# Or use the test runner which handles this automatically
python scripts/test_supabase_migration.py --validate
```

#### 2. Async Test Issues
- All async tests use `@pytest.mark.asyncio`
- Event loop fixtures are properly configured
- Async mocks are used for database connections

#### 3. Mock Configuration
- External APIs are mocked by default
- Database connections use AsyncMock
- OpenAI embeddings return consistent test data

#### 4. Coverage Issues
```bash
# Generate detailed coverage report
python scripts/test_supabase_migration.py --coverage
open htmlcov/supabase_migration/index.html
```

### Debug Mode
```bash
# Run with debug output
pytest tests/unit/core/agents/ -v -s --tb=long

# Run single test with debugging
pytest tests/unit/core/agents/test_supabase_migration_agent.py::test_specific_function -v -s
```

## Development Workflow

### Adding New Tests

1. **Create Test File**: Follow naming convention `test_*.py`
2. **Use Fixtures**: Import from `tests.fixtures.supabase_migration`
3. **Add Markers**: Use appropriate pytest markers
4. **Mock External Deps**: Use provided mock fixtures
5. **Update Documentation**: Update this file as needed

### Test-Driven Development
1. Write failing test for new functionality
2. Implement minimum code to pass test
3. Refactor while keeping tests green
4. Ensure coverage remains >90%

### Performance Testing
```python
# Example performance test
@pytest.mark.performance
def test_migration_performance(benchmark):
    result = benchmark(migration_function, large_dataset)
    assert result.duration < 60  # seconds
```

## Maintenance

### Regular Tasks
- **Weekly**: Run full test suite with coverage
- **Before Release**: Run performance benchmarks
- **Monthly**: Review and update test data
- **Quarterly**: Performance baseline updates

### Test Data Maintenance
- Keep mock data realistic and up-to-date
- Add new edge cases as discovered
- Update schema to match real-world usage
- Maintain performance test baselines

## Contributing

### Test Guidelines
1. **High Coverage**: Aim for >95% line coverage
2. **Clear Naming**: Descriptive test function names
3. **Isolated Tests**: Each test should be independent
4. **Fast Execution**: Unit tests should run quickly
5. **Good Documentation**: Include docstrings for complex tests

### Review Checklist
- [ ] Tests cover new functionality
- [ ] Tests include error cases
- [ ] Coverage remains >90%
- [ ] Tests run quickly (<30s for unit tests)
- [ ] Mock external dependencies
- [ ] Follow existing patterns and conventions

---

**Last Updated**: September 2025
**Test Suite Version**: 1.0.0
**Coverage Target**: >90%
**Total Test Count**: 200+ tests across all components
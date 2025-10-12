"""
Backup System Test Suite

Comprehensive tests for the ToolboxAI backup and disaster recovery system.

Test Organization:
- test_backup_manager.py: Unit tests for backup creation
- test_restore_manager.py: Unit tests for backup restoration
- test_disaster_recovery.py: DR orchestration tests
- test_backup_validator.py: Validation system tests
- test_integration.py: End-to-end integration tests

Running Tests:
    # All tests
    pytest

    # Specific test file
    pytest test_backup_manager.py

    # Unit tests only
    pytest -m unit

    # Integration tests only
    pytest -m integration

    # With coverage
    pytest --cov=../scripts --cov-report=html

    # Verbose output
    pytest -v

Test Markers:
- unit: Unit tests for individual components
- integration: Integration tests for workflows
- slow: Tests that take significant time
- requires_db: Tests requiring database connection
- requires_tools: Tests requiring pg_dump/pg_restore
"""

__version__ = "1.0.0"
__author__ = "ToolboxAI Development Team"

# Test statistics (updated after test completion)
TOTAL_TESTS = 89  # Approximate total test count
COVERAGE_TARGET = 80  # Minimum coverage percentage

# Test categorization
TEST_CATEGORIES = {
    "unit": {
        "backup_manager": 20,
        "restore_manager": 18,
        "disaster_recovery": 15,
        "backup_validator": 16
    },
    "integration": {
        "workflows": 12,
        "end_to_end": 8
    }
}

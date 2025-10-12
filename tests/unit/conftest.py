"""
Minimal conftest for unit tests - avoids loading the full FastAPI app.

This configuration is optimized for fast unit test execution without
initializing the complete application stack.
"""
import os
import sys
import pytest
from pathlib import Path

# Add project root to path - calculate from tests/unit/conftest.py
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Also add to PYTHONPATH for subprocess calls
os.environ["PYTHONPATH"] = str(project_root)

# Set test environment variables early
os.environ["ENVIRONMENT"] = "testing"
os.environ["TESTING_MODE"] = "true"
os.environ["USE_MOCK_LLM"] = "true"
os.environ["BYPASS_RATE_LIMIT_IN_TESTS"] = "true"

# Prevent importing heavy modules during test collection
os.environ["SKIP_HEAVY_IMPORTS"] = "true"

# Disable full app initialization
os.environ["PYTEST_UNIT_TESTS"] = "true"

@pytest.fixture(scope="session", autouse=True)
def test_environment():
    """Set up minimal test environment"""
    # Ensure project root is in sys.path
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    yield

# No other fixtures needed - unit tests define their own minimal fixtures

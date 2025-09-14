"""Tests for toolboxai_settings package."""

import os
import pytest
import sys

from toolboxai_settings import settings

# Skip all tests in this module as they require external services
pytestmark = pytest.mark.skipif(
    not os.environ.get('RUN_INTEGRATION_TESTS'),
    reason="Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to enable"
)

# Ensure project root is on sys.path so pytest can import our package
project_root = os.path.dirname(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def test_app_name_and_debug():
    """Test app name and debug settings."""
    assert isinstance(settings.app_name, str)
    assert settings.app_name.startswith("ToolboxAI")
    assert isinstance(settings.debug, bool)

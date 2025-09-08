"""
Simple test file to ensure CI pipeline works
"""

import pytest


def test_environment():
    """Test that the test environment is working."""
    assert True, "Basic test should pass"


def test_python_version():
    """Test Python version compatibility."""
    import sys
    
    major, minor = sys.version_info[:2]
    assert major >= 3, "Python 3+ required"
    assert minor >= 10, "Python 3.10+ required"
    

def test_basic_imports():
    """Test basic Python library imports."""
    # These should always be available
    import os
    import sys
    import json
    
    assert hasattr(os, 'path')
    assert hasattr(sys, 'version')
    assert hasattr(json, 'dumps')


def test_math_operations():
    """Test basic mathematical operations."""
    assert 2 + 2 == 4
    assert 10 - 5 == 5
    assert 3 * 3 == 9
    assert 8 / 2 == 4


@pytest.mark.asyncio
async def test_async_functionality():
    """Test async functionality."""
    async def sample_async_function():
        return "async works"
    
    result = await sample_async_function()
    assert result == "async works"


def test_string_operations():
    """Test string operations."""
    test_string = "ToolboxAI Solutions"
    
    assert len(test_string) > 0
    assert "ToolboxAI" in test_string
    assert test_string.lower() == "toolboxai solutions"


class TestBasicClass:
    """Test class-based testing."""
    
    def test_class_method(self):
        """Test method inside class."""
        assert True
    
    def test_class_setup(self):
        """Test class setup."""
        self.value = 42
        assert self.value == 42


def test_list_operations():
    """Test list operations."""
    test_list = [1, 2, 3, 4, 5]
    
    assert len(test_list) == 5
    assert 3 in test_list
    assert max(test_list) == 5
    assert min(test_list) == 1


def test_dict_operations():
    """Test dictionary operations."""
    test_dict = {
        'name': 'ToolboxAI',
        'version': '1.0.0',
        'status': 'active'
    }
    
    assert test_dict['name'] == 'ToolboxAI'
    assert 'version' in test_dict
    assert len(test_dict) == 3


if __name__ == "__main__":
    pytest.main([__file__])
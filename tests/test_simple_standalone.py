"""
Simple standalone test to verify pytest works without full backend initialization.
This test file is intentionally kept simple with no backend imports.
"""

import pytest


def test_basic_math():
    """Test basic arithmetic operations."""
    assert 1 + 1 == 2
    assert 10 - 5 == 5
    assert 3 * 4 == 12
    assert 8 / 2 == 4


def test_string_operations():
    """Test string operations."""
    assert "hello".upper() == "HELLO"
    assert "WORLD".lower() == "world"
    assert "test".capitalize() == "Test"


def test_list_operations():
    """Test list operations."""
    test_list = [1, 2, 3, 4, 5]
    assert len(test_list) == 5
    assert test_list[0] == 1
    assert test_list[-1] == 5
    assert sum(test_list) == 15


@pytest.mark.parametrize("input,expected", [
    (0, 0),
    (1, 1),
    (2, 4),
    (3, 9),
    (4, 16),
])
def test_square_numbers(input, expected):
    """Test squaring numbers with parametrize."""
    assert input ** 2 == expected


class TestBasicClass:
    """Test class to verify class-based tests work."""

    def test_class_method_one(self):
        """First class-based test."""
        assert True

    def test_class_method_two(self):
        """Second class-based test."""
        result = [x * 2 for x in range(5)]
        assert result == [0, 2, 4, 6, 8]


@pytest.mark.asyncio
async def test_async_function():
    """Test async function support."""
    import asyncio
    await asyncio.sleep(0.001)
    assert True

"""
Basic test to verify test infrastructure is working.
"""

import pytest


class TestBasicSetup:
    """Verify test setup is functioning."""

    def test_simple_assertion(self):
        """Test that basic assertions work."""
        assert True

    def test_math(self):
        """Test simple math."""
        assert 2 + 2 == 4

    @pytest.mark.asyncio
    async def test_async_works(self):
        """Test that async tests work."""
        import asyncio

        await asyncio.sleep(0.001)
        assert True

    def test_imports(self):
        """Test that key imports work."""
        import httpx
        import jose
        import sqlalchemy

        assert httpx
        assert sqlalchemy
        assert jose

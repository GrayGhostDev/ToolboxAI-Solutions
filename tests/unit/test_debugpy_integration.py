#!/usr/bin/env python3
"""
Debugpy Integration Test Example

This test demonstrates how to use debugpy integration with pytest for debugging.
It shows the proper way to set breakpoints and debug test execution.

Usage:
    # Run with VS Code debugger
    python scripts/debug_pytest.py tests/unit/test_debugpy_integration.py -v
    
    # Run with remote debugging
    python scripts/debug_pytest.py tests/unit/test_debugpy_integration.py -v --no-wait
    # Then attach VS Code debugger to localhost:5678
"""

import pytest
import logging
from unittest.mock import Mock, patch

logger = logging.getLogger(__name__)


class TestDebugpyIntegration:
    """Test class demonstrating debugpy integration"""
    
    def test_basic_debugpy_integration(self, debugpy_helper):
        """Test basic debugpy integration"""
        # Check if debugpy is available
        assert debugpy_helper.debugpy_available, "debugpy should be available"
        
        # Log test information
        logger.info("Running basic debugpy integration test")
        
        # Set a breakpoint for debugging
        debugpy_helper.breakpoint("Basic integration test breakpoint")
        
        # Test some basic functionality
        result = 2 + 2
        assert result == 4, "Basic math should work"
        
        logger.info("Basic integration test completed")
    
    def test_debugpy_with_mocks(self, debugpy_helper):
        """Test debugpy integration with mocked components"""
        logger.info("Running debugpy integration test with mocks")
        
        # Set breakpoint for debugging
        debugpy_helper.breakpoint("Mock test breakpoint")
        
        # Create a mock object
        mock_service = Mock()
        mock_service.process.return_value = "processed_data"
        
        # Test the mock
        result = mock_service.process("test_data")
        assert result == "processed_data"
        mock_service.process.assert_called_once_with("test_data")
        
        logger.info("Mock integration test completed")
    
    def test_debugpy_with_patches(self, debugpy_helper):
        """Test debugpy integration with patched components"""
        logger.info("Running debugpy integration test with patches")
        
        # Set breakpoint for debugging
        debugpy_helper.breakpoint("Patch test breakpoint")
        
        # Test with patches
        with patch('builtins.print') as mock_print:
            print("This should be mocked")
            mock_print.assert_called_once_with("This should be mocked")
        
        logger.info("Patch integration test completed")
    
    def test_debugpy_async_integration(self, debugpy_helper):
        """Test debugpy integration with async functions"""
        import asyncio
        
        async def async_function():
            debugpy_helper.breakpoint("Async test breakpoint")
            return "async_result"
        
        logger.info("Running debugpy integration test with async")
        
        # Run async function
        result = asyncio.run(async_function())
        assert result == "async_result"
        
        logger.info("Async integration test completed")
    
    def test_debugpy_error_handling(self, debugpy_helper):
        """Test debugpy integration with error handling"""
        logger.info("Running debugpy integration test with error handling")
        
        # Set breakpoint for debugging
        debugpy_helper.breakpoint("Error handling test breakpoint")
        
        # Test error handling
        with pytest.raises(ValueError, match="Test error"):
            raise ValueError("Test error")
        
        logger.info("Error handling integration test completed")
    
    def test_debugpy_connection_status(self, debugpy_helper):
        """Test debugpy connection status checking"""
        logger.info("Running debugpy connection status test")
        
        # Check connection status
        is_connected = debugpy_helper.is_connected()
        logger.info(f"Debugger connected: {is_connected}")
        
        # This test should pass regardless of connection status
        assert isinstance(is_connected, bool)
        
        logger.info("Connection status test completed")


class TestDebugpyAdvancedFeatures:
    """Test class for advanced debugpy features"""
    
    def test_debugpy_with_fixtures(self, debugpy_helper, test_client):
        """Test debugpy integration with pytest fixtures"""
        logger.info("Running debugpy integration test with fixtures")
        
        # Set breakpoint for debugging
        debugpy_helper.breakpoint("Fixture test breakpoint")
        
        # Test with test client fixture
        response = test_client.get("/health")
        assert response.status_code == 200
        
        logger.info("Fixture integration test completed")
    
    def test_debugpy_with_environment(self, debugpy_helper):
        """Test debugpy integration with environment variables"""
        import os
        
        logger.info("Running debugpy integration test with environment")
        
        # Set breakpoint for debugging
        debugpy_helper.breakpoint("Environment test breakpoint")
        
        # Check environment variables
        assert os.environ.get("ENVIRONMENT") == "testing"
        assert os.environ.get("TESTING_MODE") == "true"
        assert os.environ.get("DEBUG") == "true"
        
        logger.info("Environment integration test completed")
    
    def test_debugpy_performance(self, debugpy_helper):
        """Test debugpy integration with performance considerations"""
        import time
        
        logger.info("Running debugpy integration test with performance")
        
        # Set breakpoint for debugging
        debugpy_helper.breakpoint("Performance test breakpoint")
        
        # Measure execution time
        start_time = time.time()
        
        # Do some work
        result = sum(range(1000))
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        assert result == 499500
        assert execution_time < 1.0  # Should complete quickly
        
        logger.info(f"Performance test completed in {execution_time:.4f}s")


# Example of how to use debugpy in a test
def test_example_usage():
    """Example of how to use debugpy integration in tests"""
    logger.info("This is an example of how to use debugpy integration")
    
    # You can use debugpy directly in tests
    try:
        import debugpy
        if debugpy.is_client_connected():
            logger.info("Debugger is connected - you can set breakpoints")
            # debugpy.breakpoint()  # Uncomment to set a breakpoint
        else:
            logger.info("Debugger not connected - running without debugging")
    except ImportError:
        logger.warning("debugpy not available")
    
    # Your test logic here
    assert True, "Example test should pass"

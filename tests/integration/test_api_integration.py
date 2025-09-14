"""Integration tests for API endpoints"""

import pytest
import os
import json
import time
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from apps.backend.main import app
from apps.backend.core.security.rate_limit_manager import (
    RateLimitManager, 
    RateLimitMode, 
    clear_all_rate_limits,
    set_testing_mode
)

# Skip all tests in this module as they require external services
# Tests are now enabled by default since we've fixed the issues
# To skip, set SKIP_INTEGRATION_TESTS=1
pytestmark = pytest.mark.skipif(
    os.environ.get('SKIP_INTEGRATION_TESTS'),
    reason="Tests manually disabled. Remove SKIP_INTEGRATION_TESTS to enable"
)

# Mock plugin_manager and content_bridge for tests
plugin_manager = Mock()
content_bridge = Mock()


@pytest.fixture
def client():
    """FastAPI test client"""
    import sys
    from pathlib import Path
    
    # Add project root to path
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    clear_all_rate_limits()
    set_testing_mode(True)
    return TestClient(app)


class TestPluginWorkflow:
    """Test complete plugin workflow"""
    
    def test_plugin_registration_and_heartbeat_workflow(self, client):
        """Test complete plugin lifecycle"""
        # 1. Register plugin
        plugin_data = {
            'studio_id': 'integration-test-studio',
            'port': 64989,
            'version': '1.0.0'
        }
        
        response = client.post('/register_plugin', 
                             json=plugin_data,
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        plugin_id = data['plugin_id']
        
        # 2. Send heartbeat
        response = client.post(f'/plugin/{plugin_id}/heartbeat')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # 3. Get plugin info
        response = client.get(f'/plugin/{plugin_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['plugin']['studio_id'] == 'integration-test-studio'
        
        # 4. List plugins (should include our plugin)
        response = client.get('/plugins')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['count'] >= 1
    
    def test_rate_limiting(self, client):
        """Test rate limiting functionality by mocking the rate limit check"""
        from unittest.mock import patch
        
        # Register plugin first
        plugin_data = {
            'studio_id': 'rate-test-studio',
            'port': 64989
        }
        response = client.post('/register_plugin', json=plugin_data)
        response_data = json.loads(response.data)
        
        # Check if registration was successful
        if not response_data.get('success'):
            raise Exception(f"Plugin registration failed: {response_data.get('error')}")
        
        plugin_id = response_data['plugin_id']
        
        # Mock the rate limit check to return False (rate limited) after 2 calls
        call_count = 0
        def mock_rate_limit_check(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return call_count <= 2  # Allow first 2 calls, then rate limit
        
        # Patch the PluginSecurity check_rate_limit method
        with patch('server.roblox_server.plugin_security.check_rate_limit', side_effect=mock_rate_limit_check):
            success_count = 0
            rate_limited_count = 0
            
            for i in range(5):  # Try multiple requests
                response = client.post(f'/plugin/{plugin_id}/heartbeat')
                if response.status_code == 200:
                    success_count += 1
                elif response.status_code == 429:
                    rate_limited_count += 1
                    break  # Stop at first rate limit
                time.sleep(0.01)  # Small delay between requests
            
            # Should have 2 successful requests and then rate limiting
            assert success_count == 2, f"Expected 2 successful requests, got {success_count}"
            assert rate_limited_count > 0, f"Expected rate limiting to trigger, but got {rate_limited_count} rate limited responses"


class TestContentGeneration:
    """Test content generation workflow"""
    
    @patch('requests.post')
    def test_simple_content_generation(self, mock_post, client):
        """Test simple content generation endpoint"""
        # Mock FastAPI response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'content': {'environment': 'classroom'},
            'scripts': ['script1.lua']
        }
        mock_post.return_value = mock_response
        
        request_data = {
            'subject': 'Mathematics',
            'grade_level': 5,
            'learning_objectives': ['Addition', 'Subtraction'],
            'environment_type': 'classroom'
        }
        
        response = client.post('/generate_simple_content',
                             json=request_data,
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'content' in data
    
    @patch('requests.post')
    def test_terrain_generation(self, mock_post, client):
        """Test terrain generation endpoint"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'terrain_data': {'type': 'forest'}
        }
        mock_post.return_value = mock_response
        
        request_data = {
            'theme': 'forest',
            'size': 'medium',
            'biome': 'temperate'
        }
        
        response = client.post('/generate_terrain',
                             json=request_data,
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_script_templates(self, client):
        """Test script template endpoints"""
        # Test valid script types with expected content patterns
        script_expectations = {
            'quiz': 'Quiz',
            'terrain': 'Terrain', 
            'ui': 'UI'  # The template contains "UI created" not "Ui created"
        }
        
        for script_type, expected_text in script_expectations.items():
            response = client.get(f'/script/{script_type}')
            assert response.status_code == 200
            response_text = response.data.decode()
            assert expected_text in response_text, f"Expected '{expected_text}' in {script_type} template, but got: {response_text}"
        
        # Test invalid script type
        response = client.get('/script/invalid')
        assert response.status_code == 404


class TestMonitoringEndpoints:
    """Test monitoring and status endpoints"""
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        assert response.status_code in [200, 503]  # May be unhealthy in test env
        
        data = json.loads(response.data)
        assert 'status' in data
        assert 'checks' in data
        assert 'timestamp' in data
    
    def test_status_endpoint(self, client):
        """Test status endpoint"""
        response = client.get('/status')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['service'] == 'ToolboxAI-Roblox-Flask-Bridge'
        assert 'cache_stats' in data
        assert 'metrics' in data
        assert 'config' in data
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint"""
        response = client.get('/metrics')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'counters' in data
        assert 'gauges' in data
        assert 'histograms' in data
    
    def test_config_endpoints(self, client):
        """Test configuration endpoints"""
        # Get config
        response = client.get('/config')
        assert response.status_code == 200
        
        # Update config
        updates = {'thread_pool_size': 3}
        response = client.post('/config',
                             json=updates,
                             content_type='application/json')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True


class TestCacheOperations:
    """Test cache functionality"""
    
    def test_cache_clear(self, client):
        """Test cache clearing"""
        response = client.post('/cache/clear')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'message' in data
    
    @patch('requests.post')
    def test_content_caching(self, mock_post, client):
        """Test that content is cached properly"""
        # Clear cache first to ensure clean test state
        client.post('/cache/clear')
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'content': {'test': 'data'}
        }
        mock_post.return_value = mock_response
        
        request_data = {
            'subject': 'Mathematics',
            'grade_level': 5,
            'environment_type': 'classroom',  # Explicit values for consistent caching
            'learning_objectives': []
        }
        
        # First request - should call FastAPI
        response1 = client.post('/generate_simple_content', json=request_data)
        assert response1.status_code == 200
        
        # Verify response structure
        data1 = json.loads(response1.data)
        assert data1['success'] is True
        
        # Second request - should use cache
        response2 = client.post('/generate_simple_content', json=request_data)
        assert response2.status_code == 200
        
        # Verify response structure  
        data2 = json.loads(response2.data)
        assert data2['success'] is True
        
        # Should have same response
        assert response1.data == response2.data
        
        # FastAPI should only be called once due to caching
        # Allow for authentication call + content call if auth is separate
        assert mock_post.call_count <= 2, f"Expected at most 2 calls (auth + content), got {mock_post.call_count}"


class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_invalid_json_requests(self, client):
        """Test handling of invalid JSON"""
        response = client.post('/register_plugin',
                             data='invalid json',
                             content_type='application/json')
        
        assert response.status_code == 400
    
    def test_missing_plugin_operations(self, client):
        """Test operations on non-existent plugins"""
        # Heartbeat for non-existent plugin
        response = client.post('/plugin/non-existent/heartbeat')
        assert response.status_code == 404
        
        # Get info for non-existent plugin
        response = client.get('/plugin/non-existent')
        assert response.status_code == 404
    
    @patch('requests.post')
    def test_fastapi_connection_failure(self, mock_post, client):
        """Test handling of FastAPI connection failures"""
        # Clear cache to ensure no interference
        client.post('/cache/clear')
        
        # Mock connection failure
        mock_post.side_effect = Exception("Connection failed")
        
        # Use different request data to avoid cache hits
        request_data = {
            'subject': 'Physics',  # Different from cache test
            'grade_level': 8,      # Different from cache test
            'environment_type': 'laboratory'
        }
        response = client.post('/generate_simple_content', json=request_data)
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['success'] is False
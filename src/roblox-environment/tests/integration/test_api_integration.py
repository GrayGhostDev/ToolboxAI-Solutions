"""Integration tests for API endpoints"""

import pytest
import json
import time
from unittest.mock import patch, Mock
from server.roblox_server import app, plugin_manager, content_bridge


@pytest.fixture
def client():
    """Flask test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


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
        """Test rate limiting functionality"""
        # Register plugin first
        plugin_data = {'studio_id': 'rate-test-studio'}
        response = client.post('/register_plugin', json=plugin_data)
        plugin_id = json.loads(response.data)['plugin_id']
        
        # Send many heartbeats rapidly
        success_count = 0
        rate_limited_count = 0
        
        for _ in range(70):  # Exceed default rate limit of 60
            response = client.post(f'/plugin/{plugin_id}/heartbeat')
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                rate_limited_count += 1
        
        # Should have some rate limited requests
        assert rate_limited_count > 0
        assert success_count <= 60


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
        # Test valid script types
        for script_type in ['quiz', 'terrain', 'ui']:
            response = client.get(f'/script/{script_type}')
            assert response.status_code == 200
            assert script_type.title() in response.data.decode()
        
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
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'content': {'test': 'data'}
        }
        mock_post.return_value = mock_response
        
        request_data = {
            'subject': 'Mathematics',
            'grade_level': 5
        }
        
        # First request - should call FastAPI
        response1 = client.post('/generate_simple_content', json=request_data)
        assert response1.status_code == 200
        
        # Second request - should use cache
        response2 = client.post('/generate_simple_content', json=request_data)
        assert response2.status_code == 200
        
        # Should have same response
        assert response1.data == response2.data
        
        # FastAPI should only be called once due to caching
        assert mock_post.call_count == 1


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
        # Mock connection failure
        mock_post.side_effect = Exception("Connection failed")
        
        request_data = {'subject': 'Mathematics'}
        response = client.post('/generate_simple_content', json=request_data)
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['success'] is False
"""Unit tests for roblox_server.py"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
# Import real implementations from server module
from apps.backend.roblox_server import (
    PluginManager, 
    ContentBridge, 
    PluginSecurity,  # Use real security implementation
    LRUCache  # Use real cache implementation
)
# Import Flask app from services.roblox for Flask endpoint tests
from apps.backend.services.roblox import app as flask_app


class TestPluginManager:
    """Test PluginManager class"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


    
    def setup_method(self):
        self.plugin_manager = PluginManager()
    
    def test_register_plugin(self):
        """Test plugin registration"""
        plugin_data = {
            'studio_id': 'test-studio',
            'port': 64989,
            'version': '1.0.0'
        }
        
        plugin_id = self.plugin_manager.register_plugin(plugin_data)
        
        assert plugin_id is not None
        assert len(plugin_id) > 0
        
        # Verify plugin is stored
        stored_plugin = self.plugin_manager.get_plugin(plugin_id)
        assert stored_plugin is not None
        assert stored_plugin['studio_id'] == 'test-studio'
    
    def test_update_heartbeat(self):
        """Test heartbeat update"""
        # Register plugin first
        plugin_data = {'studio_id': 'test-studio'}
        plugin_id = self.plugin_manager.register_plugin(plugin_data)
        
        # Update heartbeat
        result = self.plugin_manager.update_heartbeat(plugin_id)
        assert result is True
        
        # Test non-existent plugin
        result = self.plugin_manager.update_heartbeat('non-existent')
        assert result is False
    
    def test_list_active_plugins(self):
        """Test listing active plugins"""
        # Register a plugin
        plugin_data = {'studio_id': 'test-studio'}
        plugin_id = self.plugin_manager.register_plugin(plugin_data)
        
        active_plugins = self.plugin_manager.list_active_plugins()
        assert len(active_plugins) >= 1
        
        # Find our plugin
        our_plugin = next((p for p in active_plugins if p['plugin_id'] == plugin_id), None)
        assert our_plugin is not None


class TestContentBridge:
    """Test ContentBridge class"""
    
    def setup_method(self):
        self.content_bridge = ContentBridge()
    
    def test_generate_cache_key(self):
        """Test cache key generation"""
        request_data = {
            'subject': 'Mathematics',
            'grade_level': 5,
            'environment_type': 'classroom',
            'learning_objectives': ['obj1', 'obj2']
        }
        
        cache_key = self.content_bridge._generate_cache_key(request_data)
        
        assert isinstance(cache_key, str)
        assert len(cache_key) > 0
        assert 'mathematics' in cache_key.lower()
    
    def test_cache_operations(self):
        """Test cache operations"""
        cache_key = 'test_key'
        test_data = {'test': 'data'}
        
        # Initially not cached
        assert not self.content_bridge._is_cached(cache_key)
        
        # Cache data
        self.content_bridge._cache_response(cache_key, test_data)
        
        # Should be cached now
        assert self.content_bridge._is_cached(cache_key)
        
        # Should retrieve same data
        cached_data = self.content_bridge._get_cached(cache_key)
        assert cached_data == test_data


class TestPluginSecurity:
    """Test PluginSecurity class"""
    
    def setup_method(self):
        self.security = PluginSecurity()
    
    def test_token_generation_and_validation(self):
        """Test plugin signature verification"""
        plugin_id = 'test-plugin'
        
        # Initially plugin is not trusted
        is_valid = self.security.verify_plugin_signature(plugin_id, 'signature')
        assert is_valid is False
        
        # Add to trusted plugins
        self.security.add_trusted_plugin(plugin_id)
        
        # Now it should be trusted
        is_valid = self.security.verify_plugin_signature(plugin_id, 'signature')
        assert is_valid is True
        
        # Different plugin should not be trusted
        is_valid = self.security.verify_plugin_signature('other-plugin', 'signature')
        assert is_valid is False
    
    def test_rate_limiting(self):
        """Test rate limiting"""
        from apps.backend.rate_limit_manager import RateLimitManager, RateLimitMode
        
        # Get the manager and temporarily set to production mode for this test
        manager = RateLimitManager.get_instance()
        original_mode = manager.config.mode
        
        try:
            # Set to production mode to enable rate limiting
            manager.set_mode(RateLimitMode.PRODUCTION)
            manager.clear_all_limits()  # Clear any existing state
            
            plugin_id = 'test-plugin'
            
            # Should allow initial requests (up to limit of 10)
            for i in range(10):
                result = self.security.check_rate_limit(plugin_id, max_requests=10)
                assert result is True, f"Request {i+1} should be allowed"
            
            # Should block after limit
            result = self.security.check_rate_limit(plugin_id, max_requests=10)
            assert result is False, "Request 11 should be blocked"
        
        finally:
            # Restore original mode
            manager.set_mode(original_mode)
            manager.clear_all_limits()
    
    def test_plugin_validation(self):
        """Test request validation"""
        # Valid request
        valid_request = {
            'type': 'content',
            'payload': {'data': 'test'},
            'plugin_id': 'test-plugin'
        }
        is_valid = self.security.validate_request(valid_request, '127.0.0.1')
        assert is_valid is True
        
        # Invalid request (missing fields)
        invalid_request = {'type': 'content'}
        is_valid = self.security.validate_request(invalid_request, '127.0.0.1')
        assert is_valid is False
        
        # Blocked source
        self.security.block_source('192.168.1.1', 'test block')
        is_valid = self.security.validate_request(valid_request, '192.168.1.1')
        assert is_valid is False


class TestLRUCache:
    """Test LRUCache class"""
    
    def setup_method(self):
        self.cache = LRUCache(capacity=3)
    
    def test_basic_operations(self):
        """Test basic cache operations"""
        # Set and get
        self.cache.set('key1', 'value1')
        assert self.cache.get('key1') == 'value1'
        
        # Non-existent key
        assert self.cache.get('non-existent') is None
        
        # Delete
        assert self.cache.delete('key1') is True
        assert self.cache.get('key1') is None
        assert self.cache.delete('key1') is False
    
    def test_lru_eviction(self):
        """Test LRU eviction"""
        # Fill cache to capacity
        self.cache.set('key1', 'value1')
        self.cache.set('key2', 'value2')
        self.cache.set('key3', 'value3')
        
        # Add one more - should evict key1
        self.cache.set('key4', 'value4')
        
        assert self.cache.get('key1') is None  # Evicted
        assert self.cache.get('key2') == 'value2'
        assert self.cache.get('key3') == 'value3'
        assert self.cache.get('key4') == 'value4'
    
    def test_stats(self):
        """Test cache statistics"""
        self.cache.set('key1', 'value1')
        self.cache.get('key1')  # Hit
        self.cache.get('key2')  # Miss
        
        stats = self.cache.stats()
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['size'] == 1


@pytest.fixture
def client():
    """Flask test client"""
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client


class TestFlaskEndpoints:
    """Test Flask API endpoints"""
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'service' in data
        assert 'timestamp' in data
    
    def test_register_plugin_endpoint(self, client):
        """Test plugin registration endpoint"""
        plugin_data = {
            'studio_id': 'test-studio',
            'port': 64989,
            'version': '1.0.0'
        }
        
        response = client.post('/register_plugin', 
                             json=plugin_data,
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'plugin_id' in data
    
    def test_register_plugin_invalid_data(self, client):
        """Test plugin registration with invalid data"""
        response = client.post('/register_plugin',
                             json=None,
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_status_endpoint(self, client):
        """Test status endpoint"""
        response = client.get('/status')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'service' in data
        assert 'status' in data
        assert 'active_plugins' in data
    
    def test_script_template_endpoint(self, client):
        """Test script template endpoint"""
        response = client.get('/script/quiz')
        assert response.status_code == 200
        assert 'QuizManager' in response.data.decode()
        
        # Test invalid script type
        response = client.get('/script/invalid')
        assert response.status_code == 404
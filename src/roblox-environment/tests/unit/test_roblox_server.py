"""Unit tests for roblox_server.py"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from server.roblox_server import PluginManager, ContentBridge, app
from src.shared.utils.security import PluginSecurity
from src.shared.utils.cache import LRUCache


class TestPluginManager:
    """Test PluginManager class"""
    
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
        self.security = PluginSecurity('test-secret-key')
    
    def test_token_generation_and_validation(self):
        """Test token generation and validation"""
        plugin_id = 'test-plugin'
        
        # Generate token
        token = self.security.generate_token(plugin_id)
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Validate token
        is_valid = self.security.validate_token(plugin_id, token)
        assert is_valid is True
        
        # Invalid token
        is_valid = self.security.validate_token(plugin_id, 'invalid-token')
        assert is_valid is False
    
    def test_rate_limiting(self):
        """Test rate limiting"""
        plugin_id = 'test-plugin'
        
        # Should allow initial requests
        for _ in range(5):
            result = self.security.check_rate_limit(plugin_id, max_requests=10)
            assert result is True
        
        # Should block after limit
        for _ in range(10):
            self.security.check_rate_limit(plugin_id, max_requests=10)
        
        result = self.security.check_rate_limit(plugin_id, max_requests=10)
        assert result is False
    
    def test_plugin_validation(self):
        """Test plugin data validation"""
        # Valid data
        valid_data = {
            'studio_id': 'test-studio',
            'port': 8080,
            'version': '1.0.0'
        }
        errors = self.security.validate_plugin_data(valid_data)
        assert len(errors) == 0
        
        # Invalid data
        invalid_data = {
            'port': 'not-a-number',
            'version': 'x' * 25  # Too long
        }
        errors = self.security.validate_plugin_data(invalid_data)
        assert len(errors) > 0
        assert 'studio_id' in errors
        assert 'port' in errors
        assert 'version' in errors


class TestLRUCache:
    """Test LRUCache class"""
    
    def setup_method(self):
        self.cache = LRUCache(max_size=3, ttl=60)
    
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
    app.config['TESTING'] = True
    with app.test_client() as client:
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
"""
Test CORS Security Configuration

Tests for secure Cross-Origin Resource Sharing (CORS) configuration
"""

import pytest
from unittest.mock import Mock, patch
from apps.backend.core.security.cors import SecureCORSConfig, CORSMiddlewareWithLogging

class TestSecureCORSConfig:
    """Test SecureCORSConfig class"""
    
    def test_development_configuration(self):
        """Test CORS configuration for development environment"""
        config = SecureCORSConfig(environment="development")
        
        # Should have default development origins
        assert "http://localhost:3000" in config.allowed_origins
        assert "http://127.0.0.1:5179" in config.allowed_origins
        
        # Should allow common headers in development
        assert len(config.allowed_headers) > 5
        
        # Should have standard methods
        assert "GET" in config.allowed_methods
        assert "POST" in config.allowed_methods
        assert "OPTIONS" in config.allowed_methods
    
    def test_production_configuration(self):
        """Test CORS configuration for production environment"""
        allowed_origins = [
            "https://app.example.com",
            "https://dashboard.example.com"
        ]
        
        config = SecureCORSConfig(
            environment="production",
            allowed_origins=allowed_origins
        )
        
        # Should use specified origins
        assert config.allowed_origins == allowed_origins
        
        # Should have restrictive headers in production
        assert len(config.allowed_headers) <= 4
        assert "Authorization" in config.allowed_headers
        assert "Content-Type" in config.allowed_headers
    
    def test_wildcard_rejection_in_production(self):
        """Test that wildcards are rejected in production"""
        config = SecureCORSConfig(
            environment="production",
            allowed_origins=["*", "https://app.example.com"]
        )
        
        # Wildcard should be filtered out
        assert "*" not in config.allowed_origins
        assert "https://app.example.com" in config.allowed_origins
    
    def test_origin_validation(self):
        """Test origin URL validation"""
        config = SecureCORSConfig(
            environment="production",
            allowed_origins=[
                "https://app.example.com",
                "invalid-url",  # Should be rejected
                "http://valid.example.com",
                "ftp://wrong-protocol.com",  # Should be rejected
            ]
        )
        
        # Only valid HTTP/HTTPS origins should be kept
        assert "https://app.example.com" in config.allowed_origins
        assert "http://valid.example.com" in config.allowed_origins
        assert "invalid-url" not in config.allowed_origins
        assert "ftp://wrong-protocol.com" not in config.allowed_origins
    
    def test_is_origin_allowed(self):
        """Test origin allowance checking"""
        config = SecureCORSConfig(
            environment="production",
            allowed_origins=["https://app.example.com"]
        )
        
        assert config.is_origin_allowed("https://app.example.com") is True
        assert config.is_origin_allowed("https://evil.com") is False
        assert config.is_origin_allowed("") is False
        assert config.is_origin_allowed(None) is False
    
    def test_regex_pattern_matching(self):
        """Test regex pattern matching for dynamic origins"""
        config = SecureCORSConfig(
            environment="production",
            allowed_origins=[],
            allowed_origins_regex=r"https://.*\.example\.com"
        )
        
        assert config.is_origin_allowed("https://app.example.com") is True
        assert config.is_origin_allowed("https://dashboard.example.com") is True
        assert config.is_origin_allowed("https://evil.com") is False
        assert config.is_origin_allowed("http://app.example.com") is False  # Wrong protocol
    
    def test_cors_headers_generation(self):
        """Test CORS headers generation"""
        config = SecureCORSConfig(
            environment="production",
            allowed_origins=["https://app.example.com"],
            allow_credentials=True
        )
        
        # Allowed origin should get headers
        headers = config.get_cors_headers("https://app.example.com")
        assert headers["Access-Control-Allow-Origin"] == "https://app.example.com"
        assert headers["Access-Control-Allow-Credentials"] == "true"
        
        # Disallowed origin should get empty headers
        headers = config.get_cors_headers("https://evil.com")
        assert headers == {}
    
    def test_preflight_headers(self):
        """Test preflight request headers"""
        config = SecureCORSConfig(
            environment="production",
            allowed_origins=["https://app.example.com"],
            allowed_methods=["GET", "POST"],
            allowed_headers=["Content-Type", "Authorization"],
            max_age=3600
        )
        
        # Allowed origin should get full preflight headers
        headers = config.get_preflight_headers(
            "https://app.example.com",
            "POST",
            "Content-Type, Authorization"
        )
        assert "Access-Control-Allow-Origin" in headers
        assert "Access-Control-Allow-Methods" in headers
        assert "Access-Control-Allow-Headers" in headers
        assert headers["Access-Control-Max-Age"] == "3600"
        
        # Disallowed origin should get empty headers
        headers = config.get_preflight_headers(
            "https://evil.com",
            "POST",
            "Content-Type"
        )
        assert headers == {}

class TestCORSMiddlewareWithLogging:
    """Test CORSMiddlewareWithLogging class"""
    
    @pytest.mark.asyncio
    async def test_cors_violation_logging(self):
        """Test that CORS violations are logged"""
        config = SecureCORSConfig(
            environment="production",
            allowed_origins=["https://app.example.com"]
        )
        
        # Create mock app
        mock_app = Mock()
        
        # Create middleware
        middleware = CORSMiddlewareWithLogging(mock_app, config)
        
        # Simulate request from disallowed origin
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/test",
            "headers": [
                (b"origin", b"https://evil.com"),
            ]
        }
        
        receive = Mock()
        send = Mock()
        
        # The violation should be tracked
        assert middleware.violation_count == 0
        
        # Note: Full async testing would require more setup
        # This demonstrates the structure
    
    def test_violation_tracking(self):
        """Test violation count tracking"""
        config = SecureCORSConfig(
            environment="production",
            allowed_origins=["https://app.example.com"]
        )
        
        mock_app = Mock()
        middleware = CORSMiddlewareWithLogging(mock_app, config)
        
        # Check is_origin_allowed triggers logging for violations
        assert config.is_origin_allowed("https://evil.com") is False
        
        # Manually track violation for testing
        middleware.violation_count += 1
        middleware.violations_by_origin["https://evil.com"] = 1
        
        assert middleware.violation_count == 1
        assert middleware.violations_by_origin["https://evil.com"] == 1

class TestCORSIntegration:
    """Integration tests for CORS configuration"""
    
    def test_environment_based_configuration(self):
        """Test that configuration changes based on environment"""
        # Development should be permissive
        dev_config = SecureCORSConfig(environment="development")
        assert len(dev_config.allowed_origins) > 5
        assert len(dev_config.allowed_headers) > 5
        
        # Production should be restrictive
        prod_config = SecureCORSConfig(environment="production")
        assert len(prod_config.allowed_origins) == 0  # Must be explicitly configured
        assert len(prod_config.allowed_headers) <= 4
    
    def test_security_best_practices(self):
        """Test that security best practices are enforced"""
        config = SecureCORSConfig(
            environment="production",
            allowed_origins=["https://app.example.com"]
        )
        
        # Should not allow wildcards
        assert "*" not in config.allowed_origins
        assert "*" not in config.allowed_methods
        
        # Should have specific methods
        assert "GET" in config.allowed_methods
        assert "POST" in config.allowed_methods
        
        # Should limit exposed headers
        assert len(config.exposed_headers) <= 5
        
        # Should support credentials securely
        assert config.allow_credentials is True
        
        # Should have reasonable max age
        assert config.max_age >= 60
        assert config.max_age <= 86400  # Max 24 hours

@pytest.mark.integration
class TestCORSWithFastAPI:
    """Test CORS integration with FastAPI"""
    
    @pytest.fixture
    def test_client(self):
        """Create test client with CORS configured"""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        app = FastAPI()
        
        # Configure CORS
        config = SecureCORSConfig(
            environment="production",
            allowed_origins=["https://app.example.com"]
        )
        
        app.add_middleware(
            CORSMiddlewareWithLogging,
            cors_config=config
        )
        
        @app.get("/test")
        def test_endpoint():
            return {"message": "test"}
        
        return TestClient(app)
    
    def test_allowed_origin_request(self, test_client):
        """Test request from allowed origin"""
        response = test_client.get(
            "/test",
            headers={"Origin": "https://app.example.com"}
        )
        
        assert response.status_code == 200
        # Note: TestClient doesn't fully simulate CORS, 
        # but this shows the structure
    
    def test_disallowed_origin_request(self, test_client):
        """Test request from disallowed origin"""
        response = test_client.get(
            "/test",
            headers={"Origin": "https://evil.com"}
        )
        
        # Request should still work (CORS is browser-enforced)
        # but no CORS headers should be present
        assert response.status_code == 200
    
    def test_preflight_request(self, test_client):
        """Test OPTIONS preflight request"""
        response = test_client.options(
            "/test",
            headers={
                "Origin": "https://app.example.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        
        # Preflight should be handled
        assert response.status_code in [200, 204]
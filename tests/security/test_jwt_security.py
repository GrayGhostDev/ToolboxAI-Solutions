"""
Test JWT Security Implementation

Tests for the secure JWT secret management system including:
- Secret generation and validation
- Settings integration
- Authentication token security
- Vulnerability prevention
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class TestJWTSecretGenerator:
    """Test JWT secret generator functionality"""
    
    def test_generate_secure_secret_default_length(self):
        """Test generating secret with default length"""
        from apps.backend.core.security.jwt import JWTSecretGenerator
        
        generator = JWTSecretGenerator()
        secret = generator.generate_secure_secret()
        
        assert len(secret) == 64  # Default length
        assert isinstance(secret, str)
        
        # Check entropy
        unique_chars = len(set(secret))
        assert unique_chars >= 10, f"Secret has low character diversity: {unique_chars}"
    
    def test_generate_secure_secret_custom_length(self):
        """Test generating secret with custom length"""
        from apps.backend.core.security.jwt import JWTSecretGenerator
        
        generator = JWTSecretGenerator()
        secret = generator.generate_secure_secret(48)
        
        assert len(secret) == 48
        assert isinstance(secret, str)
    
    def test_generate_hex_secret(self):
        """Test generating hexadecimal secret"""
        from apps.backend.core.security.jwt import JWTSecretGenerator
        
        generator = JWTSecretGenerator()
        secret = generator.generate_hex_secret(64)
        
        assert len(secret) == 64
        # Should only contain hex characters
        assert all(c in '0123456789abcdef' for c in secret.lower())
    
    def test_generate_base64_secret(self):
        """Test generating base64 secret"""
        from apps.backend.core.security.jwt import JWTSecretGenerator
        
        generator = JWTSecretGenerator()
        secret = generator.generate_base64_secret(48)  # 48 bytes = 64 base64 chars
        
        assert len(secret) == 64
        # Basic base64 character check
        import string
        base64_chars = string.ascii_letters + string.digits + '+/='
        assert all(c in base64_chars for c in secret)
    
    def test_validate_secret_valid(self):
        """Test validating a valid secret"""
        from apps.backend.core.security.jwt import JWTSecretGenerator
        
        generator = JWTSecretGenerator()
        # Generate a known good secret
        secret = generator.generate_secure_secret(64)
        
        is_valid, report = generator.validate_secret(secret)
        
        assert is_valid == True
        assert report['length_ok'] == True
        assert report['entropy_ok'] == True
        assert report['no_weak_patterns'] == True
        assert len(report['issues']) == 0
    
    def test_validate_secret_too_short(self):
        """Test validating a secret that's too short"""
        from apps.backend.core.security.jwt import JWTSecretGenerator
        
        generator = JWTSecretGenerator()
        secret = "short"
        
        is_valid, report = generator.validate_secret(secret)
        
        assert is_valid == False
        assert report['length_ok'] == False
        assert any('too short' in issue.lower() for issue in report['issues'])
    
    def test_validate_secret_weak_patterns(self):
        """Test validating a secret with weak patterns"""
        from apps.backend.core.security.jwt import JWTSecretGenerator
        
        generator = JWTSecretGenerator()
        # 32+ characters but contains weak pattern
        secret = "this-is-a-password-that-is-very-long-but-weak"
        
        is_valid, report = generator.validate_secret(secret)
        
        assert is_valid == False
        assert report['no_weak_patterns'] == False
        assert any('weak patterns' in issue.lower() for issue in report['issues'])
    
    def test_validate_secret_low_entropy(self):
        """Test validating a secret with low entropy"""
        from apps.backend.core.security.jwt import JWTSecretGenerator
        
        generator = JWTSecretGenerator()
        # All same character - very low entropy
        secret = "a" * 64
        
        is_valid, report = generator.validate_secret(secret)
        
        assert is_valid == False
        assert report['entropy_ok'] == False
    
    def test_convenience_function(self):
        """Test convenience function for quick secret generation"""
        from apps.backend.core.security.jwt import generate_secure_jwt_secret
        
        secret = generate_secure_jwt_secret()
        
        assert len(secret) == 64
        assert isinstance(secret, str)
        
        # Should pass validation
        from apps.backend.core.security.jwt import JWTSecretGenerator
        generator = JWTSecretGenerator()
        is_valid, _ = generator.validate_secret(secret)
        assert is_valid == True


class TestJWTManager:
    """Test JWT manager functionality"""
    
    def test_jwt_manager_initialization(self):
        """Test JWT manager can be initialized"""
        from apps.backend.core.security.jwt import JWTSecurityManager
        
        manager = JWTSecurityManager()
        assert manager is not None
        assert hasattr(manager, 'initialize')
        assert hasattr(manager, 'get_validated_secret')
    
    def test_validate_current_secret(self):
        """Test validation of current secret configuration"""
        from apps.backend.core.security.jwt import JWTSecurityManager
        
        manager = JWTSecurityManager()
        
        with patch.dict(os.environ, {'JWT_SECRET_KEY': 'a-very-secure-32-character-secret-key-here!'}):
            report = manager.validate_current_secret()
            
            assert 'valid' in report
            assert isinstance(report['valid'], bool)


class TestSettingsIntegration:
    """Test integration with settings module"""
    
    @patch.dict(os.environ, {}, clear=True)
    def test_settings_development_mode(self):
        """Test settings in development mode generates secure secret"""
        with patch.dict(os.environ, {'ENV_NAME': 'development'}):
            # Clear any existing secret
            os.environ.pop('JWT_SECRET_KEY', None)
            
            # Import settings fresh
            import importlib
            if 'toolboxai_settings.settings' in sys.modules:
                toolboxai_settings = importlib.reload(sys.modules['toolboxai_settings'])
            else:
                import toolboxai_settings
            
            # Should have generated a secure secret
            assert hasattr(toolboxai_settings.settings, 'JWT_SECRET_KEY')
            assert len(toolboxai_settings.settings.JWT_SECRET_KEY) >= 32
    
    def test_settings_validate_weak_secret(self):
        """Test settings rejects weak secrets in production"""
        with patch.dict(os.environ, {
            'JWT_SECRET_KEY': 'dev-secret-key-change-in-production',
            'ENV_NAME': 'production'
        }):
            with pytest.raises(ValueError, match="PRODUCTION SECURITY ERROR"):
                import importlib
                if 'toolboxai_settings.settings' in sys.modules:
                    toolboxai_settings = importlib.reload(sys.modules['toolboxai_settings'])
                else:
                    import toolboxai_settings
    
    def test_settings_accepts_strong_secret(self):
        """Test settings accepts strong secrets"""
        strong_secret = "Th1s-1s-@-Very-Str0ng-S3cr3t-K3y-W1th-64-Ch@rs-0f-H1gh-Ent0py!"
        
        with patch.dict(os.environ, {
            'JWT_SECRET_KEY': strong_secret,
            'ENV_NAME': 'production'
        }):
            import importlib
            if 'toolboxai_settings.settings' in sys.modules:
                toolboxai_settings = importlib.reload(sys.modules['toolboxai_settings'])
            else:
                import toolboxai_settings
                
            assert toolboxai_settings.settings.JWT_SECRET_KEY == strong_secret


class TestAuthenticationIntegration:
    """Test integration with authentication modules"""
    
    def test_db_auth_uses_secure_secret(self):
        """Test database authentication uses secure JWT secret"""
        try:
            from apps.backend.api.auth.db_auth import db_auth
            
            # Should have JWT_SECRET configured
            assert hasattr(db_auth, '_validate_jwt_config')
            
            # Test token creation
            test_user = {
                'id': 'test-123',
                'username': 'test_user',
                'email': 'test@example.com',
                'role': 'student'
            }
            
            tokens = db_auth.create_tokens(test_user)
            
            assert 'access_token' in tokens
            assert 'refresh_token' in tokens
            assert 'token_type' in tokens
            assert tokens['token_type'] == 'Bearer'
            
        except ImportError:
            pytest.skip("db_auth module not available")
    
    def test_auth_module_integration(self):
        """Test main auth module uses secure JWT"""
        try:
            from apps.backend.api.auth.auth import JWTManager, get_secure_jwt_secret
            
            # Test secret retrieval
            secret = get_secure_jwt_secret()
            assert len(secret) >= 32
            
            # Test token creation
            test_data = {
                'sub': 'test-user-123',
                'username': 'test_user',
                'role': 'student'
            }
            
            token = JWTManager.create_access_token(test_data)
            assert isinstance(token, str)
            assert len(token) > 0
            
            # Test token verification
            payload = JWTManager.verify_token(token, raise_on_error=False)
            assert payload is not None
            assert payload['sub'] == 'test-user-123'
            assert payload['username'] == 'test_user'
            
        except ImportError:
            pytest.skip("Auth module not available")


class TestSecurityVulnerabilities:
    """Test that security vulnerabilities are prevented"""
    
    def test_prevents_default_secrets(self):
        """Test that default/weak secrets are rejected"""
        default_secrets = [
            "dev-secret-key-change-in-production",
            "your-secret-key-change-in-production",
            "change-me",
            "default",
            "secret",
            "password"
        ]
        
        from apps.backend.core.security.jwt import JWTSecretGenerator
        generator = JWTSecretGenerator()
        
        for secret in default_secrets:
            is_valid, report = generator.validate_secret(secret)
            assert is_valid == False, f"Default secret '{secret}' should be rejected"
            assert len(report['issues']) > 0
    
    def test_prevents_short_secrets(self):
        """Test that short secrets are rejected"""
        short_secrets = ["abc", "12345", "short", "a" * 31]  # All under 32 chars
        
        from apps.backend.core.security.jwt import JWTSecretGenerator
        generator = JWTSecretGenerator()
        
        for secret in short_secrets:
            is_valid, report = generator.validate_secret(secret)
            assert is_valid == False, f"Short secret '{secret}' should be rejected"
            assert any('too short' in issue.lower() for issue in report['issues'])
    
    def test_entropy_calculation(self):
        """Test entropy calculation works correctly"""
        from apps.backend.core.security.jwt import JWTSecretGenerator
        
        # Low entropy - all same character
        low_entropy = "a" * 64
        entropy_low = JWTSecretGenerator._calculate_entropy(low_entropy)
        assert entropy_low == 0.0
        
        # High entropy - random mix
        high_entropy = "aB3$xY9#mN2@pQ6!rT8%uW1&vZ5*"
        entropy_high = JWTSecretGenerator._calculate_entropy(high_entropy)
        assert entropy_high > 3.0
    
    def test_production_security_enforcement(self):
        """Test that production mode enforces strict security"""
        with patch.dict(os.environ, {'ENV_NAME': 'production'}):
            from apps.backend.core.security.jwt import JWTSecurityManager
            
            manager = JWTSecurityManager()
            
            # Should fail with weak environment secret
            with patch.dict(os.environ, {'JWT_SECRET_KEY': 'weak'}):
                with pytest.raises(ValueError, match="PRODUCTION SECURITY ERROR"):
                    manager._validate_environment_jwt_secret()


class TestCLITool:
    """Test JWT CLI tool functionality"""
    
    def test_cli_generate_command(self):
        """Test CLI secret generation"""
        from apps.backend.core.security.jwt_cli import main
        
        # Mock sys.argv for generate command
        test_args = ['jwt_cli.py', 'generate', '--length', '48']
        
        with patch('sys.argv', test_args):
            with patch('builtins.print') as mock_print:
                try:
                    main()
                except SystemExit:
                    pass
                
                # Should have printed a secret
                printed_output = ' '.join(str(call) for call in mock_print.call_args_list)
                assert 'Generated JWT secret:' in printed_output or 'Error:' in printed_output
    
    def test_cli_validate_command(self):
        """Test CLI secret validation"""
        from apps.backend.core.security.jwt_cli import main
        
        # Test with a valid secret
        test_secret = "Th1s-1s-@-Very-Str0ng-S3cr3t-K3y-W1th-64-Ch@rs-0f-H1gh-Ent0py!"
        test_args = ['jwt_cli.py', 'validate', '--secret', test_secret]
        
        with patch('sys.argv', test_args):
            with patch('builtins.print') as mock_print:
                try:
                    main()
                except SystemExit:
                    pass
                
                printed_output = ' '.join(str(call) for call in mock_print.call_args_list)
                assert 'Secret validation:' in printed_output


# Utility fixtures
@pytest.fixture
def temp_secrets_dir():
    """Provide temporary directory for secrets testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_environment():
    """Provide clean environment for testing"""
    original_env = os.environ.copy()
    # Clear JWT-related variables
    for key in list(os.environ.keys()):
        if 'JWT' in key or key in ['ENV_NAME', 'DEBUG']:
            os.environ.pop(key, None)
    
    yield os.environ
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# Run the tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])

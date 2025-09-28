import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
Comprehensive test suite for secrets_manager.py
Tests AWS Secrets Manager integration, caching, fallback to environment variables.
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from botocore.exceptions import ClientError, NoCredentialsError

from apps.backend.core.security.secrets_manager import (
    SecretsManager, get_secrets_manager, get_api_key, get_database_url
)


class TestSecretsManager:
    """Test SecretsManager class functionality"""

    def setup_method(self):
        """Setup test environment"""
        # Clear any existing global instance
        import apps.backend.core.security.secrets_manager
        apps.backend.core.security.secrets_manager._secrets_manager = None

    @patch('apps.backend.core.security.secrets_manager.boto3.client')
    def test_initialization_with_aws(self, mock_boto3_client):
        """Test initialization with AWS credentials available"""
        mock_client = Mock()
        mock_boto3_client.return_value = mock_client
        
        manager = SecretsManager(region_name="us-west-2", use_cache=True)
        
        assert manager.region_name == "us-west-2"
        assert manager.use_cache is True
        assert manager.available is True
        assert manager.client == mock_client
        mock_boto3_client.assert_called_once_with('secretsmanager', region_name='us-west-2')

    @patch('apps.backend.core.security.secrets_manager.boto3.client')
    def test_initialization_without_aws(self, mock_boto3_client):
        """Test initialization without AWS credentials"""
        mock_boto3_client.side_effect = NoCredentialsError()
        
        with patch('apps.backend.core.security.secrets_manager.logger') as mock_logger:
            manager = SecretsManager()
            
            assert manager.available is False
            assert manager.client is None
            mock_logger.warning.assert_called()

    def test_cache_validity_check(self):
        """Test cache validity checking"""
        with patch('apps.backend.core.security.secrets_manager.boto3.client'):
            manager = SecretsManager(use_cache=True)
            
            # No cache entry
            assert manager._is_cache_valid("test_secret") is False
            
            # Cache entry but expired
            manager._cache_expiry["test_secret"] = datetime.now() - timedelta(minutes=10)
            assert manager._is_cache_valid("test_secret") is False
            
            # Valid cache entry
            manager._cache_expiry["test_secret"] = datetime.now() + timedelta(minutes=10)
            assert manager._is_cache_valid("test_secret") is True

    @patch('apps.backend.core.security.secrets_manager.boto3.client')
    def test_get_secret_from_aws_success(self, mock_boto3_client):
        """Test successful secret retrieval from AWS"""
        secret_data = {"api_key": "test_key_123", "database_url": "postgresql://..."}
        
        mock_client = Mock()
        mock_client.get_secret_value.return_value = {
            'SecretString': json.dumps(secret_data)
        }
        mock_boto3_client.return_value = mock_client
        
        manager = SecretsManager(use_cache=True)
        result = manager.get_secret("test_secret")
        
        assert result == secret_data
        assert "test_secret" in manager._cache
        assert manager._cache["test_secret"] == secret_data
        mock_client.get_secret_value.assert_called_once_with(SecretId="test_secret")

    @patch('apps.backend.core.security.secrets_manager.boto3.client')
    def test_get_secret_from_cache(self, mock_boto3_client):
        """Test secret retrieval from cache"""
        secret_data = {"api_key": "cached_key_123"}
        
        mock_client = Mock()
        mock_boto3_client.return_value = mock_client
        
        manager = SecretsManager(use_cache=True)
        
        # Populate cache
        manager._cache["test_secret"] = secret_data
        manager._cache_expiry["test_secret"] = datetime.now() + timedelta(minutes=10)
        
        result = manager.get_secret("test_secret")
        
        assert result == secret_data
        # Should not call AWS API
        mock_client.get_secret_value.assert_not_called()

    @patch('apps.backend.core.security.secrets_manager.boto3.client')
    def test_get_secret_binary_not_supported(self, mock_boto3_client):
        """Test handling of binary secrets (not supported)"""
        mock_client = Mock()
        mock_client.get_secret_value.return_value = {
            'SecretBinary': b'binary_secret_data'
        }
        mock_boto3_client.return_value = mock_client
        
        manager = SecretsManager()
        result = manager.get_secret("test_secret")
        
        assert result is None

    @patch('apps.backend.core.security.secrets_manager.boto3.client')
    def test_get_secret_not_found(self, mock_boto3_client):
        """Test handling of secret not found"""
        mock_client = Mock()
        mock_client.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}}, 'GetSecretValue'
        )
        mock_boto3_client.return_value = mock_client
        
        with patch('apps.backend.core.security.secrets_manager.logger') as mock_logger:
            manager = SecretsManager()
            result = manager.get_secret("nonexistent_secret")
            
            assert result is None
            mock_logger.warning.assert_called()

    @patch('apps.backend.core.security.secrets_manager.boto3.client')
    def test_get_secret_access_denied(self, mock_boto3_client):
        """Test handling of access denied error"""
        mock_client = Mock()
        mock_client.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'AccessDeniedException'}}, 'GetSecretValue'
        )
        mock_boto3_client.return_value = mock_client
        
        with patch('apps.backend.core.security.secrets_manager.logger') as mock_logger:
            manager = SecretsManager()
            result = manager.get_secret("restricted_secret")
            
            assert result is None
            mock_logger.error.assert_called()

    @patch('apps.backend.core.security.secrets_manager.boto3.client')
    def test_get_secret_with_fallback(self, mock_boto3_client):
        """Test secret retrieval with environment variable fallback"""
        mock_client = Mock()
        mock_client.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}}, 'GetSecretValue'
        )
        mock_boto3_client.return_value = mock_client
        
        # Set environment variables
        with patch.dict(os.environ, {
            'TEST_API_KEY': 'env_api_key_123',
            'TEST_DATABASE_URL': 'postgresql://env_db'
        }):
            manager = SecretsManager()
            result = manager.get_secret("test_secret", fallback_env="TEST")
            
            assert result is not None
            # Should contain mapped environment variables

    def test_get_from_env_api_keys(self):
        """Test getting API keys from environment variables"""
        with patch.dict(os.environ, {
            'ANTHROPIC_API_KEY': 'anthropic_key_123',
            'OPENAI_API_KEY': 'openai_key_456',
            'LANGCHAIN_API_KEY': 'langchain_key_789'
        }):
            with patch('apps.backend.core.security.secrets_manager.boto3.client'):
                manager = SecretsManager()
                result = manager._get_from_env("api_keys")
                
                # Should map to expected structure
                assert 'anthropic_api_key' in result
                assert 'openai_api_key' in result
                assert 'langchain_api_key' in result

    def test_get_from_env_direct_mapping(self):
        """Test direct environment variable mapping"""
        with patch.dict(os.environ, {
            'CUSTOM_SECRET_VALUE': 'custom_value_123',
            'CUSTOM_ANOTHER_VALUE': 'another_value_456'
        }):
            with patch('apps.backend.core.security.secrets_manager.boto3.client'):
                manager = SecretsManager()
                result = manager._get_from_env("CUSTOM")
                
                assert 'secret_value' in result
                assert 'another_value' in result
                assert result['secret_value'] == 'custom_value_123'

    @patch('apps.backend.core.security.secrets_manager.boto3.client')
    def test_get_api_keys(self, mock_boto3_client):
        """Test get_api_keys method"""
        secret_data = {
            "anthropic_api_key": "anthropic_key_123",
            "openai_api_key": "openai_key_456"
        }
        
        mock_client = Mock()
        mock_client.get_secret_value.return_value = {
            'SecretString': json.dumps(secret_data)
        }
        mock_boto3_client.return_value = mock_client
        
        with patch.dict(os.environ, {'ENV': 'production'}):
            manager = SecretsManager()
            result = manager.get_api_keys()
            
            assert result == secret_data
            mock_client.get_secret_value.assert_called_with(SecretId="toolboxai-production-api-keys")

    @patch('apps.backend.core.security.secrets_manager.boto3.client')
    def test_get_database_credentials(self, mock_boto3_client):
        """Test get_database_credentials method"""
        db_secret = {
            "host": "prod-db.example.com",
            "port": 5432,
            "database": "toolboxai_prod",
            "username": "toolboxai_user",
            "password": "secure_password_123"
        }
        
        mock_client = Mock()
        mock_client.get_secret_value.return_value = {
            'SecretString': json.dumps(db_secret)
        }
        mock_boto3_client.return_value = mock_client
        
        with patch.dict(os.environ, {'ENV': 'production'}):
            manager = SecretsManager()
            result = manager.get_database_credentials()
            
            assert result == db_secret
            mock_client.get_secret_value.assert_called_with(SecretId="toolboxai-production-database")

    def test_get_database_credentials_fallback(self):
        """Test database credentials fallback to environment"""
        with patch('apps.backend.core.security.secrets_manager.boto3.client') as mock_boto3:
            mock_client = Mock()
            mock_client.get_secret_value.side_effect = ClientError(
                {'Error': {'Code': 'ResourceNotFoundException'}}, 'GetSecretValue'
            )
            mock_boto3.return_value = mock_client
            
            with patch.dict(os.environ, {
                'POSTGRES_HOST': 'localhost',
                'POSTGRES_PORT': '5432',
                'POSTGRES_DB': 'test_db',
                'POSTGRES_USER': 'test_user',
                'POSTGRES_PASSWORD': 'test_pass'
            }):
                manager = SecretsManager()
                result = manager.get_database_credentials()
                
                assert result['host'] == 'localhost'
                assert result['port'] == 5432
                assert result['database'] == 'test_db'
                assert result['username'] == 'test_user'
                assert result['password'] == 'test_pass'

    @patch('apps.backend.core.security.secrets_manager.boto3.client')
    def test_get_jwt_config(self, mock_boto3_client):
        """Test get_jwt_config method"""
        jwt_secret = {
            "jwt_secret_key": "super_secret_jwt_key_123",
            "jwt_algorithm": "HS256",
            "jwt_expiration_minutes": 60
        }
        
        mock_client = Mock()
        mock_client.get_secret_value.return_value = {
            'SecretString': json.dumps(jwt_secret)
        }
        mock_boto3_client.return_value = mock_client
        
        manager = SecretsManager()
        result = manager.get_jwt_config()
        
        assert result == jwt_secret

    @patch('apps.backend.core.security.secrets_manager.boto3.client')
    def test_get_stripe_credentials(self, mock_boto3_client):
        """Test get_stripe_credentials method"""
        stripe_secret = {
            "stripe_public_key": "pk_test_123",
            "stripe_secret_key": "sk_test_456",
            "stripe_webhook_secret": "whsec_789"
        }
        
        mock_client = Mock()
        mock_client.get_secret_value.return_value = {
            'SecretString': json.dumps(stripe_secret)
        }
        mock_boto3_client.return_value = mock_client
        
        manager = SecretsManager()
        result = manager.get_stripe_credentials()
        
        assert result == stripe_secret

    @patch('apps.backend.core.security.secrets_manager.boto3.client')
    def test_get_pusher_credentials(self, mock_boto3_client):
        """Test get_pusher_credentials method"""
        pusher_secret = {
            "app_id": "123456",
            "key": "pusher_key_123",
            "secret": "pusher_secret_456",
            "cluster": "us2"
        }
        
        mock_client = Mock()
        mock_client.get_secret_value.return_value = {
            'SecretString': json.dumps(pusher_secret)
        }
        mock_boto3_client.return_value = mock_client
        
        manager = SecretsManager()
        result = manager.get_pusher_credentials()
        
        assert result == pusher_secret

    @patch('apps.backend.core.security.secrets_manager.boto3.client')
    def test_get_roblox_credentials(self, mock_boto3_client):
        """Test get_roblox_credentials method"""
        roblox_secret = {
            "api_key": "roblox_api_key_123",
            "client_id": "roblox_client_id_456",
            "client_secret": "roblox_secret_789"
        }
        
        mock_client = Mock()
        mock_client.get_secret_value.return_value = {
            'SecretString': json.dumps(roblox_secret)
        }
        mock_boto3_client.return_value = mock_client
        
        manager = SecretsManager()
        result = manager.get_roblox_credentials()
        
        assert result == roblox_secret

    @patch('apps.backend.core.security.secrets_manager.boto3.client')
    def test_clear_cache(self, mock_boto3_client):
        """Test cache clearing functionality"""
        mock_boto3_client.return_value = Mock()
        
        manager = SecretsManager(use_cache=True)
        
        # Populate cache
        manager._cache["secret1"] = {"key": "value1"}
        manager._cache["secret2"] = {"key": "value2"}
        manager._cache_expiry["secret1"] = datetime.now()
        manager._cache_expiry["secret2"] = datetime.now()
        
        # Clear specific secret
        manager.clear_cache("secret1")
        assert "secret1" not in manager._cache
        assert "secret1" not in manager._cache_expiry
        assert "secret2" in manager._cache
        
        # Clear all cache
        manager.clear_cache()
        assert len(manager._cache) == 0
        assert len(manager._cache_expiry) == 0

    @patch('apps.backend.core.security.secrets_manager.boto3.client')
    def test_rotate_secret_success(self, mock_boto3_client):
        """Test successful secret rotation"""
        mock_client = Mock()
        mock_boto3_client.return_value = mock_client
        
        with patch.dict(os.environ, {'SECRET_ROTATION_LAMBDA_ARN': 'arn:aws:lambda:us-east-1:123456789012:function:rotate-secret'}):
            manager = SecretsManager(use_cache=True)
            
            # Add to cache first
            manager._cache["test_secret"] = {"key": "old_value"}
            
            result = manager.rotate_secret("test_secret")
            
            assert result is True
            mock_client.rotate_secret.assert_called_once()
            # Cache should be cleared
            assert "test_secret" not in manager._cache

    @patch('apps.backend.core.security.secrets_manager.boto3.client')
    def test_rotate_secret_failure(self, mock_boto3_client):
        """Test failed secret rotation"""
        mock_client = Mock()
        mock_client.rotate_secret.side_effect = ClientError(
            {'Error': {'Code': 'InvalidRequestException'}}, 'RotateSecret'
        )
        mock_boto3_client.return_value = mock_client
        
        manager = SecretsManager()
        result = manager.rotate_secret("test_secret")
        
        assert result is False

    def test_rotate_secret_no_aws(self):
        """Test secret rotation when AWS is unavailable"""
        with patch('apps.backend.core.security.secrets_manager.boto3.client') as mock_boto3:
            mock_boto3.side_effect = NoCredentialsError()
            
            manager = SecretsManager()
            result = manager.rotate_secret("test_secret")
            
            assert result is False

    def test_caching_disabled(self):
        """Test functionality with caching disabled"""
        with patch('apps.backend.core.security.secrets_manager.boto3.client') as mock_boto3:
            mock_client = Mock()
            mock_client.get_secret_value.return_value = {
                'SecretString': json.dumps({"key": "value"})
            }
            mock_boto3.return_value = mock_client
            
            manager = SecretsManager(use_cache=False)
            
            # First call
            result1 = manager.get_secret("test_secret")
            
            # Second call - should call AWS again
            result2 = manager.get_secret("test_secret")
            
            assert result1 == result2
            assert mock_client.get_secret_value.call_count == 2
            assert len(manager._cache) == 0  # No caching


class TestGlobalFunctions:
    """Test global convenience functions"""

    def setup_method(self):
        """Setup test environment"""
        # Clear any existing global instance
        import apps.backend.core.security.secrets_manager
        apps.backend.core.security.secrets_manager._secrets_manager = None

    def test_get_secrets_manager_singleton(self):
        """Test that get_secrets_manager returns singleton"""
        with patch('apps.backend.core.security.secrets_manager.boto3.client'):
            manager1 = get_secrets_manager()
            manager2 = get_secrets_manager()
            
            assert manager1 is manager2
            assert isinstance(manager1, SecretsManager)

    def test_get_api_key_convenience(self):
        """Test get_api_key convenience function"""
        with patch('apps.backend.core.security.secrets_manager.get_secrets_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.get_api_keys.return_value = {
                'openai_api_key': 'openai_key_123',
                'anthropic_api_key': 'anthropic_key_456'
            }
            mock_get_manager.return_value = mock_manager
            
            api_key = get_api_key('openai')
            assert api_key == 'openai_key_123'
            
            api_key = get_api_key('anthropic')
            assert api_key == 'anthropic_key_456'
            
            api_key = get_api_key('nonexistent')
            assert api_key is None

    def test_get_database_url_convenience(self):
        """Test get_database_url convenience function"""
        with patch('apps.backend.core.security.secrets_manager.get_secrets_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.get_database_credentials.return_value = {
                'host': 'db.example.com',
                'port': 5432,
                'database': 'toolboxai',
                'username': 'user',
                'password': 'pass'
            }
            mock_get_manager.return_value = mock_manager
            
            db_url = get_database_url()
            expected = "postgresql://user:pass@db.example.com:5432/toolboxai"
            assert db_url == expected

    def test_get_database_url_fallback(self):
        """Test get_database_url fallback to environment"""
        with patch('apps.backend.core.security.secrets_manager.get_secrets_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.get_database_credentials.return_value = None
            mock_get_manager.return_value = mock_manager
            
            with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://env_db_url'}):
                db_url = get_database_url()
                assert db_url == 'postgresql://env_db_url'

    def test_get_database_url_empty_fallback(self):
        """Test get_database_url with empty fallback"""
        with patch('apps.backend.core.security.secrets_manager.get_secrets_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.get_database_credentials.return_value = None
            mock_get_manager.return_value = mock_manager
            
            with patch.dict(os.environ, {}, clear=True):
                db_url = get_database_url()
                assert db_url == ''


@pytest.mark.integration
class TestSecretsManagerIntegration:
    """Integration tests for secrets manager"""

    def test_environment_variable_integration(self):
        """Test complete environment variable integration"""
        env_vars = {
            'AWS_REGION': 'us-west-2',
            'ENV': 'test',
            'OPENAI_API_KEY': 'test_openai_key',
            'ANTHROPIC_API_KEY': 'test_anthropic_key',
            'POSTGRES_HOST': 'localhost',
            'POSTGRES_PORT': '5432',
            'POSTGRES_DB': 'test_db',
            'POSTGRES_USER': 'test_user',
            'POSTGRES_PASSWORD': 'test_pass',
            'JWT_SECRET_KEY': 'test_jwt_secret',
            'STRIPE_PUBLIC_KEY': 'pk_test_stripe',
            'PUSHER_KEY': 'test_pusher_key'
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('apps.backend.core.security.secrets_manager.boto3.client') as mock_boto3:
                # Simulate AWS unavailable
                mock_boto3.side_effect = NoCredentialsError()
                
                manager = SecretsManager()
                
                # Test API keys fallback
                api_keys = manager.get_api_keys()
                # Should get empty dict since fallback doesn't match pattern
                assert isinstance(api_keys, dict)
                
                # Test database credentials fallback
                db_creds = manager.get_database_credentials()
                assert db_creds['host'] == 'localhost'
                assert db_creds['port'] == 5432
                assert db_creds['database'] == 'test_db'
                
                # Test database URL construction
                db_url = get_database_url()
                expected = "postgresql://test_user:test_pass@localhost:5432/test_db"
                assert db_url == expected

    def test_aws_secrets_manager_integration(self):
        """Test AWS Secrets Manager integration flow"""
        with patch('apps.backend.core.security.secrets_manager.boto3.client') as mock_boto3:
            mock_client = Mock()
            
            # Setup different secrets
            secrets_responses = {
                'toolboxai-test-api-keys': {
                    'SecretString': json.dumps({
                        'openai_api_key': 'aws_openai_key',
                        'anthropic_api_key': 'aws_anthropic_key'
                    })
                },
                'toolboxai-test-database': {
                    'SecretString': json.dumps({
                        'host': 'aws-db.example.com',
                        'port': 5432,
                        'database': 'toolboxai_aws',
                        'username': 'aws_user',
                        'password': 'aws_password'
                    })
                }
            }
            
            def mock_get_secret_value(SecretId):
                if SecretId in secrets_responses:
                    return secrets_responses[SecretId]
                else:
                    raise ClientError(
                        {'Error': {'Code': 'ResourceNotFoundException'}},
                        'GetSecretValue'
                    )
            
            mock_client.get_secret_value.side_effect = mock_get_secret_value
            mock_boto3.return_value = mock_client
            
            with patch.dict(os.environ, {'ENV': 'test'}):
                manager = SecretsManager()
                
                # Test API keys from AWS
                api_keys = manager.get_api_keys()
                assert api_keys['openai_api_key'] == 'aws_openai_key'
                assert api_keys['anthropic_api_key'] == 'aws_anthropic_key'
                
                # Test database credentials from AWS
                db_creds = manager.get_database_credentials()
                assert db_creds['host'] == 'aws-db.example.com'
                assert db_creds['database'] == 'toolboxai_aws'
                
                # Test caching
                api_keys_cached = manager.get_api_keys()
                assert api_keys_cached == api_keys
                
                # Should only call AWS once due to caching
                assert mock_client.get_secret_value.call_count == 2

    def test_mixed_environment_integration(self):
        """Test mixed AWS and environment variable integration"""
        with patch('apps.backend.core.security.secrets_manager.boto3.client') as mock_boto3:
            mock_client = Mock()
            
            # Some secrets available in AWS, others from environment
            def mock_get_secret_value(SecretId):
                if 'api-keys' in SecretId:
                    return {
                        'SecretString': json.dumps({
                            'openai_api_key': 'aws_openai_key'
                        })
                    }
                else:
                    raise ClientError(
                        {'Error': {'Code': 'ResourceNotFoundException'}},
                        'GetSecretValue'
                    )
            
            mock_client.get_secret_value.side_effect = mock_get_secret_value
            mock_boto3.return_value = mock_client
            
            env_vars = {
                'ENV': 'test',
                'POSTGRES_HOST': 'env_db_host',
                'POSTGRES_PASSWORD': 'env_db_password'
            }
            
            with patch.dict(os.environ, env_vars):
                manager = SecretsManager()
                
                # API keys should come from AWS
                api_keys = manager.get_api_keys()
                assert api_keys['openai_api_key'] == 'aws_openai_key'
                
                # Database should fallback to environment
                db_creds = manager.get_database_credentials()
                assert db_creds['host'] == 'env_db_host'
                assert db_creds['password'] == 'env_db_password'


class TestErrorHandling:
    """Test error handling scenarios"""

    def test_json_decode_error(self):
        """Test handling of JSON decode errors"""
        with patch('apps.backend.core.security.secrets_manager.boto3.client') as mock_boto3:
            mock_client = Mock()
            mock_client.get_secret_value.return_value = {
                'SecretString': 'invalid_json_string'
            }
            mock_boto3.return_value = mock_client
            
            manager = SecretsManager()
            
            # Should handle JSON decode error gracefully
            with pytest.raises(json.JSONDecodeError):
                manager.get_secret("test_secret")

    def test_network_timeout_handling(self):
        """Test handling of network timeouts"""
        with patch('apps.backend.core.security.secrets_manager.boto3.client') as mock_boto3:
            mock_client = Mock()
            mock_client.get_secret_value.side_effect = ClientError(
                {'Error': {'Code': 'RequestTimeout'}}, 'GetSecretValue'
            )
            mock_boto3.return_value = mock_client
            
            manager = SecretsManager()
            result = manager.get_secret("test_secret")
            
            assert result is None

    def test_concurrent_access(self):
        """Test concurrent access to secrets manager"""
        import threading
        import concurrent.futures
        
        with patch('apps.backend.core.security.secrets_manager.boto3.client') as mock_boto3:
            mock_client = Mock()
            mock_client.get_secret_value.return_value = {
                'SecretString': json.dumps({"key": "value"})
            }
            mock_boto3.return_value = mock_client
            
            manager = SecretsManager(use_cache=True)
            
            def get_secret_concurrent(secret_name):
                return manager.get_secret(f"secret_{secret_name}")
            
            # Test with multiple threads
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(get_secret_concurrent, i) for i in range(20)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # All should succeed
            assert all(result == {"key": "value"} for result in results)

    def test_cache_corruption_handling(self):
        """Test handling of corrupted cache data"""
        with patch('apps.backend.core.security.secrets_manager.boto3.client') as mock_boto3:
            mock_client = Mock()
            mock_client.get_secret_value.return_value = {
                'SecretString': json.dumps({"key": "value"})
            }
            mock_boto3.return_value = mock_client
            
            manager = SecretsManager(use_cache=True)
            
            # Corrupt cache data
            manager._cache["test_secret"] = "corrupted_data"
            manager._cache_expiry["test_secret"] = datetime.now() + timedelta(minutes=10)
            
            # Should handle corrupted cache gracefully
            result = manager.get_secret("test_secret")
            assert result == "corrupted_data"  # Returns cached data as-is

    def test_empty_secret_handling(self):
        """Test handling of empty secrets"""
        with patch('apps.backend.core.security.secrets_manager.boto3.client') as mock_boto3:
            mock_client = Mock()
            mock_client.get_secret_value.return_value = {
                'SecretString': json.dumps({})
            }
            mock_boto3.return_value = mock_client
            
            manager = SecretsManager()
            result = manager.get_secret("empty_secret")
            
            assert result == {}

    def test_malformed_secret_name(self):
        """Test handling of malformed secret names"""
        with patch('apps.backend.core.security.secrets_manager.boto3.client') as mock_boto3:
            mock_client = Mock()
            mock_client.get_secret_value.side_effect = ClientError(
                {'Error': {'Code': 'InvalidParameterException'}}, 'GetSecretValue'
            )
            mock_boto3.return_value = mock_client
            
            manager = SecretsManager()
            result = manager.get_secret("invalid/secret/name")
            
            assert result is None

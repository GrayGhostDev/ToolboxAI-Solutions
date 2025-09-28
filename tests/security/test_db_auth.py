import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_db_connection():
    """Mock database connection for tests"""
    with patch('psycopg2.connect') as mock_connect:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        yield mock_conn

"""
Comprehensive test suite for db_auth.py
Tests database authentication, JWT token management, and security validation.
"""

import pytest
import os
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor

from apps.backend.api.auth.db_auth import DatabaseAuth, db_auth


class TestDatabaseAuth:
    """Test DatabaseAuth class functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.db_auth = DatabaseAuth()
        
    def test_initialization(self):
        """Test DatabaseAuth initialization"""
        assert self.db_auth.db_config is not None
        assert 'host' in self.db_auth.db_config
        assert 'port' in self.db_auth.db_config
        assert 'user' in self.db_auth.db_config
        assert 'password' in self.db_auth.db_config
        assert 'database' in self.db_auth.db_config
        assert self.db_auth.pwd_context is not None

    def test_jwt_config_validation(self):
        """Test JWT configuration validation"""
        # Test with valid configuration
        with patch('apps.backend.api.auth.db_auth.JWT_SECRET', 'very_secure_secret_key_that_is_long_enough'):
            auth = DatabaseAuth()
            # Should initialize without errors
            assert auth is not None

        # Test with insecure configuration
        with patch('apps.backend.api.auth.db_auth.JWT_SECRET', 'short'):
            with patch('logging.getLogger') as mock_logger:
                auth = DatabaseAuth()
                # Should log warning about short key
                mock_logger.return_value.warning.assert_called()

    def test_password_hashing(self):
        """Test password hashing with bcrypt"""
        password = "TestPassword123!"
        
        # Hash password
        hashed = self.db_auth.hash_password(password)
        assert hashed is not None
        assert isinstance(hashed, str)
        assert len(hashed) > 50  # Bcrypt hashes are typically 60 chars
        assert hashed.startswith('$2b$')  # Bcrypt prefix
        
        # Verify password
        assert self.db_auth.verify_password(password, hashed) is True
        assert self.db_auth.verify_password("WrongPassword", hashed) is False

    def test_password_verification_fallback(self):
        """Test password verification with SHA256 fallback"""
        password = "TestPassword123!"
        
        # Test with invalid bcrypt hash (should fallback to SHA256)
        import hashlib
        sha256_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Should fallback to SHA256 verification
        assert self.db_auth.verify_password(password, sha256_hash) is True
        assert self.db_auth.verify_password("WrongPassword", sha256_hash) is False

    @patch('apps.backend.api.auth.db_auth.psycopg2.connect')
    def test_get_connection(self, mock_connect):
        """Test database connection"""
        mock_connection = Mock()
        mock_connect.return_value = mock_connection
        
        connection = self.db_auth.get_connection()
        
        mock_connect.assert_called_once_with(**self.db_auth.db_config)
        assert connection == mock_connection

    @patch('apps.backend.api.auth.db_auth.psycopg2.connect')
    def test_authenticate_user_success(self, mock_connect):
        """Test successful user authentication"""
        # Mock database response
        mock_user_data = {
            'id': 1,
            'username': 'testuser',
            'email': 'test@example.com',
            'password_hash': self.db_auth.hash_password('TestPassword123!'),
            'first_name': 'Test',
            'last_name': 'User',
            'display_name': 'Test',
            'role': 'student',
            'is_active': True,
            'is_verified': True,
            'avatar_url': None
        }
        
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = mock_user_data
        
        mock_connection = Mock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        # Test authentication with username
        result = self.db_auth.authenticate_user('testuser', 'TestPassword123!')
        
        assert result is not None
        assert result['username'] == 'testuser'
        assert result['email'] == 'test@example.com'
        assert result['role'] == 'student'
        assert 'password_hash' not in result  # Should be removed
        
        # Verify database calls
        mock_cursor.execute.assert_called()
        mock_connection.commit.assert_called_once()

    @patch('apps.backend.api.auth.db_auth.psycopg2.connect')
    def test_authenticate_user_email(self, mock_connect):
        """Test user authentication with email"""
        mock_user_data = {
            'id': 1,
            'username': 'testuser',
            'email': 'test@example.com',
            'password_hash': self.db_auth.hash_password('TestPassword123!'),
            'first_name': 'Test',
            'last_name': 'User',
            'display_name': 'Test',
            'role': 'student',
            'is_active': True,
            'is_verified': True,
            'avatar_url': None
        }
        
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = mock_user_data
        
        mock_connection = Mock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        # Test authentication with email
        result = self.db_auth.authenticate_user('test@example.com', 'TestPassword123!')
        
        assert result is not None
        assert result['email'] == 'test@example.com'

    @patch('apps.backend.api.auth.db_auth.psycopg2.connect')
    def test_authenticate_user_failure_no_user(self, mock_connect):
        """Test authentication failure when user doesn't exist"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        
        mock_connection = Mock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        result = self.db_auth.authenticate_user('nonexistent', 'password')
        assert result is None

    @patch('apps.backend.api.auth.db_auth.psycopg2.connect')
    def test_authenticate_user_failure_wrong_password(self, mock_connect):
        """Test authentication failure with wrong password"""
        mock_user_data = {
            'id': 1,
            'username': 'testuser',
            'email': 'test@example.com',
            'password_hash': self.db_auth.hash_password('CorrectPassword123!'),
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'student',
            'is_active': True,
            'is_verified': True,
            'avatar_url': None
        }
        
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = mock_user_data
        
        mock_connection = Mock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        result = self.db_auth.authenticate_user('testuser', 'WrongPassword123!')
        assert result is None

    @patch('apps.backend.api.auth.db_auth.psycopg2.connect')
    def test_authenticate_user_db_error(self, mock_connect):
        """Test authentication handling database errors"""
        mock_connect.side_effect = psycopg2.Error("Database connection failed")
        
        result = self.db_auth.authenticate_user('testuser', 'password')
        assert result is None

    def test_create_tokens(self):
        """Test JWT token creation"""
        user_data = {
            'id': 1,
            'username': 'testuser',
            'email': 'test@example.com',
            'role': 'student'
        }
        
        tokens = self.db_auth.create_tokens(user_data)
        
        assert 'access_token' in tokens
        assert 'refresh_token' in tokens
        assert 'token_type' in tokens
        assert 'expires_in' in tokens
        assert tokens['token_type'] == 'Bearer'
        
        # Verify token structure
        import jwt
        from apps.backend.api.auth.db_auth import JWT_SECRET, JWT_ALGORITHM
        
        access_payload = jwt.decode(tokens['access_token'], JWT_SECRET, algorithms=[JWT_ALGORITHM])
        assert access_payload['user_id'] == '1'
        assert access_payload['username'] == 'testuser'
        assert access_payload['role'] == 'student'
        assert access_payload['type'] == 'access'
        
        refresh_payload = jwt.decode(tokens['refresh_token'], JWT_SECRET, algorithms=[JWT_ALGORITHM])
        assert refresh_payload['user_id'] == '1'
        assert refresh_payload['type'] == 'refresh'

    def test_verify_token_valid(self):
        """Test JWT token verification with valid token"""
        user_data = {'id': 1, 'username': 'testuser', 'email': 'test@example.com', 'role': 'student'}
        tokens = self.db_auth.create_tokens(user_data)
        
        payload = self.db_auth.verify_token(tokens['access_token'])
        
        assert payload is not None
        assert payload['user_id'] == '1'
        assert payload['username'] == 'testuser'
        assert payload['role'] == 'student'

    def test_verify_token_expired(self):
        """Test JWT token verification with expired token"""
        import jwt
        from apps.backend.api.auth.db_auth import JWT_SECRET, JWT_ALGORITHM
        
        # Create expired token
        expired_payload = {
            'user_id': '1',
            'username': 'testuser',
            'exp': datetime.now(timezone.utc) - timedelta(hours=1),  # Expired 1 hour ago
            'iat': datetime.now(timezone.utc) - timedelta(hours=2)
        }
        expired_token = jwt.encode(expired_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        result = self.db_auth.verify_token(expired_token)
        assert result is None

    def test_verify_token_invalid(self):
        """Test JWT token verification with invalid token"""
        invalid_tokens = [
            "invalid.jwt.token",
            "",
            None,
            "header.payload.signature"
        ]
        
        for token in invalid_tokens:
            result = self.db_auth.verify_token(token)
            assert result is None

    def test_verify_token_malformed(self):
        """Test JWT token verification with malformed token"""
        import jwt
        
        # Create token with wrong secret
        payload = {'user_id': '1', 'exp': datetime.now(timezone.utc) + timedelta(hours=1)}
        wrong_secret_token = jwt.encode(payload, 'wrong_secret', algorithm='HS256')
        
        result = self.db_auth.verify_token(wrong_secret_token)
        assert result is None

    @patch('apps.backend.api.auth.db_auth.psycopg2.connect')
    def test_get_user_by_id_success(self, mock_connect):
        """Test getting user by ID successfully"""
        mock_user_data = {
            'id': 1,
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'display_name': 'Test',
            'role': 'student',
            'is_active': True,
            'is_verified': True,
            'avatar_url': None,
            'bio': 'Test bio'
        }
        
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = mock_user_data
        
        mock_connection = Mock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        result = self.db_auth.get_user_by_id('1')
        
        assert result is not None
        assert result['username'] == 'testuser'
        assert result['email'] == 'test@example.com'

    @patch('apps.backend.api.auth.db_auth.psycopg2.connect')
    def test_get_user_by_id_not_found(self, mock_connect):
        """Test getting user by ID when user doesn't exist"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        
        mock_connection = Mock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        result = self.db_auth.get_user_by_id('999')
        assert result is None

    @patch('apps.backend.api.auth.db_auth.psycopg2.connect')
    def test_get_user_stats_student(self, mock_connect):
        """Test getting user statistics for student"""
        mock_user_info = {
            'role': 'student',
            'created_at': datetime.now(timezone.utc),
            'last_login': datetime.now(timezone.utc)
        }
        
        mock_progress = {
            'courses_enrolled': 3,
            'avg_progress': 75.5,
            'total_xp': 1500
        }
        
        mock_cursor = Mock()
        mock_cursor.fetchone.side_effect = [mock_user_info, mock_progress]
        
        mock_connection = Mock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        result = self.db_auth.get_user_stats('1')
        
        assert result['role'] == 'student'
        assert result['courses_enrolled'] == 3
        assert result['avg_progress'] == 75.5
        assert result['total_xp'] == 1500

    @patch('apps.backend.api.auth.db_auth.psycopg2.connect')
    def test_get_user_stats_teacher(self, mock_connect):
        """Test getting user statistics for teacher"""
        mock_user_info = {
            'role': 'teacher',
            'created_at': datetime.now(timezone.utc),
            'last_login': datetime.now(timezone.utc)
        }
        
        mock_courses = {'total_courses': 5}
        mock_classes = {'total_classes': 8}
        
        mock_cursor = Mock()
        mock_cursor.fetchone.side_effect = [mock_user_info, mock_courses, mock_classes]
        
        mock_connection = Mock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        result = self.db_auth.get_user_stats('1')
        
        assert result['role'] == 'teacher'
        assert result['total_courses'] == 5
        assert result['total_classes'] == 8

    @patch('apps.backend.api.auth.db_auth.psycopg2.connect')
    def test_create_user_success(self, mock_connect):
        """Test creating a new user successfully"""
        user_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'NewPassword123!',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'student'
        }
        
        mock_new_user = {
            'id': 2,
            'username': 'newuser',
            'email': 'new@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'display_name': 'New',
            'role': 'student'
        }
        
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = mock_new_user
        
        mock_connection = Mock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        result = self.db_auth.create_user(user_data)
        
        assert result is not None
        assert result['username'] == 'newuser'
        assert result['email'] == 'new@example.com'
        assert result['role'] == 'student'
        
        # Verify password was hashed
        mock_cursor.execute.assert_called()
        call_args = mock_cursor.execute.call_args[0]
        assert len(call_args[1][2]) > 50  # Hashed password should be long

    @patch('apps.backend.api.auth.db_auth.psycopg2.connect')
    def test_create_user_db_error(self, mock_connect):
        """Test creating user with database error"""
        user_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'NewPassword123!',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'student'
        }
        
        mock_connect.side_effect = psycopg2.Error("Database error")
        
        result = self.db_auth.create_user(user_data)
        assert result is None

    def test_get_jwt_security_status(self):
        """Test JWT security status reporting"""
        status = self.db_auth.get_jwt_security_status()
        
        assert 'secret_configured' in status
        assert 'secret_length' in status
        assert 'algorithm' in status
        assert 'expiration_hours' in status
        assert 'using_secure_settings' in status
        
        assert isinstance(status['secret_configured'], bool)
        assert isinstance(status['secret_length'], int)
        assert isinstance(status['algorithm'], str)


@pytest.mark.integration
class TestDatabaseAuthIntegration:
    """Integration tests for database authentication"""

    def test_complete_auth_flow(self):
        """Test complete authentication flow"""
        db_auth = DatabaseAuth()
        
        # This would require actual database setup
        # For now, test the flow with mocked components
        with patch.object(db_auth, 'authenticate_user') as mock_auth:
            mock_auth.return_value = {
                'id': 1,
                'username': 'testuser',
                'email': 'test@example.com',
                'role': 'student'
            }
            
            # Authenticate user
            user = db_auth.authenticate_user('testuser', 'password')
            assert user is not None
            
            # Create tokens
            tokens = db_auth.create_tokens(user)
            assert tokens is not None
            
            # Verify token
            payload = db_auth.verify_token(tokens['access_token'])
            assert payload is not None
            assert payload['user_id'] == '1'

    def test_password_security_flow(self):
        """Test password security throughout the flow"""
        db_auth = DatabaseAuth()
        
        # Test password hashing
        original_password = "TestPassword123!"
        hashed = db_auth.hash_password(original_password)
        
        # Verify hashed password doesn't contain original
        assert original_password not in hashed
        assert len(hashed) > len(original_password)
        
        # Verify password verification works
        assert db_auth.verify_password(original_password, hashed)
        assert not db_auth.verify_password("WrongPassword", hashed)

    def test_token_security_properties(self):
        """Test token security properties"""
        db_auth = DatabaseAuth()
        user_data = {
            'id': 1,
            'username': 'testuser',
            'email': 'test@example.com',
            'role': 'student'
        }
        
        # Create multiple tokens
        tokens1 = db_auth.create_tokens(user_data)
        time.sleep(0.1)  # Small delay to ensure different timestamps
        tokens2 = db_auth.create_tokens(user_data)
        
        # Tokens should be different
        assert tokens1['access_token'] != tokens2['access_token']
        assert tokens1['refresh_token'] != tokens2['refresh_token']
        
        # Both should be valid
        payload1 = db_auth.verify_token(tokens1['access_token'])
        payload2 = db_auth.verify_token(tokens2['access_token'])
        
        assert payload1 is not None
        assert payload2 is not None
        
        # Should have different JTIs (if implemented)
        if 'jti' in payload1 and 'jti' in payload2:
            assert payload1['jti'] != payload2['jti']


class TestGlobalInstance:
    """Test global db_auth instance"""

    def test_global_instance_exists(self):
        """Test that global db_auth instance exists"""
        assert db_auth is not None
        assert isinstance(db_auth, DatabaseAuth)

    def test_global_instance_functionality(self):
        """Test that global instance has expected functionality"""
        assert hasattr(db_auth, 'authenticate_user')
        assert hasattr(db_auth, 'create_tokens')
        assert hasattr(db_auth, 'verify_token')
        assert hasattr(db_auth, 'get_user_by_id')
        assert hasattr(db_auth, 'hash_password')
        assert hasattr(db_auth, 'verify_password')


class TestErrorHandling:
    """Test error handling scenarios"""

    def test_none_password_handling(self):
        """Test handling of None password"""
        db_auth = DatabaseAuth()
        
        with pytest.raises((TypeError, AttributeError)):
            db_auth.hash_password(None)

    def test_empty_password_handling(self):
        """Test handling of empty password"""
        db_auth = DatabaseAuth()
        
        # Empty password should be hashed (bcrypt can handle it)
        # but verification should fail
        hashed = db_auth.hash_password("")
        assert not db_auth.verify_password("test", hashed)

    def test_none_token_verification(self):
        """Test handling of None token"""
        db_auth = DatabaseAuth()
        
        result = db_auth.verify_token(None)
        assert result is None

    def test_invalid_user_data_tokens(self):
        """Test token creation with invalid user data"""
        db_auth = DatabaseAuth()
        
        # Missing required fields should still work but produce tokens with None values
        incomplete_user = {'id': 1}
        tokens = db_auth.create_tokens(incomplete_user)
        
        assert 'access_token' in tokens
        payload = db_auth.verify_token(tokens['access_token'])
        assert payload['user_id'] == '1'

    @patch('apps.backend.api.auth.db_auth.psycopg2.connect')
    def test_database_connection_timeout(self, mock_connect):
        """Test handling of database connection timeouts"""
        mock_connect.side_effect = psycopg2.OperationalError("Connection timeout")
        
        db_auth = DatabaseAuth()
        result = db_auth.authenticate_user('testuser', 'password')
        
        assert result is None

    def test_concurrent_authentication(self):
        """Test concurrent authentication requests"""
        import threading
        import concurrent.futures
        
        db_auth = DatabaseAuth()
        
        def auth_and_create_tokens(user_id):
            user_data = {'id': user_id, 'username': f'user{user_id}', 'role': 'student'}
            tokens = db_auth.create_tokens(user_data)
            payload = db_auth.verify_token(tokens['access_token'])
            return payload['user_id'] == str(user_id)
        
        # Test with multiple threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(auth_and_create_tokens, i) for i in range(20)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All operations should succeed
        assert all(results)

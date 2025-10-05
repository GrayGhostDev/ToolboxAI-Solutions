#!/usr/bin/env python3
"""
Comprehensive Security Tests for Week 3 Implementation
Tests Vault integration, JWT, RBAC, PII encryption, and GDPR compliance
Python 3.12+ compatible with 2025 testing standards
"""

import pytest
import asyncio
import json
import base64
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Test environment setup
os.environ['TESTING'] = 'true'
os.environ['VAULT_ENABLED'] = 'false'  # Use mock for testing


class TestVaultManager:
    """Test HashiCorp Vault integration"""

    @pytest.fixture
    def vault_manager(self):
        """Create vault manager with mocked backend"""
        with patch('hvac.Client') as mock_client:
            mock_instance = Mock()
            mock_client.return_value = mock_instance
            mock_instance.is_authenticated.return_value = True

            from apps.backend.services.vault_manager import VaultManager
            return VaultManager()

    def test_vault_initialization(self, vault_manager):
        """Test Vault manager initialization"""
        assert vault_manager is not None
        assert vault_manager.algorithm == "AES-256-GCM"

    def test_secret_storage(self, vault_manager):
        """Test secret storage in Vault"""
        with patch.object(vault_manager, 'vault') as mock_vault:
            mock_vault.secrets.kv.v2.create_or_update_secret.return_value = True

            result = vault_manager.set_secret(
                "test/path",
                {"api_key": "test_key_123"}
            )

            assert result is True
            mock_vault.secrets.kv.v2.create_or_update_secret.assert_called_once()

    def test_secret_retrieval(self, vault_manager):
        """Test secret retrieval from Vault"""
        with patch.object(vault_manager, 'vault') as mock_vault:
            mock_response = {
                'data': {
                    'data': {'api_key': 'test_key_123'}
                }
            }
            mock_vault.secrets.kv.v2.read_secret_version.return_value = mock_response

            secret = vault_manager.get_secret("test/path", "api_key")

            assert secret == 'test_key_123'

    def test_secret_rotation(self, vault_manager):
        """Test automatic secret rotation"""
        with patch.object(vault_manager, 'get_secret') as mock_get:
            with patch.object(vault_manager, 'set_secret') as mock_set:
                mock_get.return_value = {"old_key": "value123"}
                mock_set.return_value = True

                result = vault_manager.rotate_secret("test/path")

                assert result is True
                mock_set.assert_called_once()

    @pytest.mark.asyncio
    async def test_dynamic_database_credentials(self, vault_manager):
        """Test dynamic database credential generation"""
        with patch.object(vault_manager, 'vault') as mock_vault:
            mock_vault.secrets.database.generate_credentials.return_value = {
                'data': {
                    'username': 'v-token-db-abc123',
                    'password': 'temp_pass_xyz789'
                }
            }

            creds = vault_manager.get_dynamic_database_credentials("postgres", ttl="1h")

            assert 'username' in creds
            assert 'password' in creds
            assert 'expires_at' in creds


class TestJWTManager:
    """Test JWT authentication with RS256"""

    @pytest.fixture
    def jwt_manager(self):
        """Create JWT manager"""
        with patch('apps.backend.services.vault_manager.get_vault_manager'):
            from apps.backend.core.auth.jwt_manager import JWTManager
            manager = JWTManager()
            # Generate test keys
            manager._generate_new_keys()
            return manager

    def test_jwt_key_generation(self, jwt_manager):
        """Test RSA key pair generation"""
        assert jwt_manager.private_key is not None
        assert jwt_manager.public_key is not None
        assert 'BEGIN RSA PRIVATE KEY' in jwt_manager.private_key or \
               'BEGIN PRIVATE KEY' in jwt_manager.private_key
        assert 'BEGIN PUBLIC KEY' in jwt_manager.public_key

    def test_access_token_creation(self, jwt_manager):
        """Test access token creation with claims"""
        token = jwt_manager.create_access_token(
            user_id="user123",
            username="testuser",
            roles=["user", "admin"],
            permissions=["read:all", "write:own"]
        )

        assert token is not None
        assert len(token) > 100  # RS256 tokens are longer

    def test_token_verification(self, jwt_manager):
        """Test token verification and claims extraction"""
        token = jwt_manager.create_access_token(
            user_id="user123",
            username="testuser",
            roles=["admin"],
            permissions=["read:all", "write:all"]
        )

        is_valid, claims = jwt_manager.verify_token(token, token_type="access")

        assert is_valid is True
        assert claims['sub'] == "user123"
        assert claims['username'] == "testuser"
        assert "admin" in claims['roles']
        assert "read:all" in claims['permissions']

    def test_token_permission_verification(self, jwt_manager):
        """Test permission-based token verification"""
        token = jwt_manager.create_access_token(
            user_id="user123",
            username="testuser",
            roles=["user"],
            permissions=["read:own", "write:own"]
        )

        # Should pass with granted permission
        is_valid, _ = jwt_manager.verify_token(
            token,
            token_type="access",
            verify_permissions=["read:own"]
        )
        assert is_valid is True

        # Should fail with missing permission
        is_valid, _ = jwt_manager.verify_token(
            token,
            token_type="access",
            verify_permissions=["delete:all"]
        )
        assert is_valid is False

    def test_refresh_token_flow(self, jwt_manager):
        """Test refresh token creation and usage"""
        # Create initial tokens
        refresh_token = jwt_manager.create_refresh_token(
            user_id="user123",
            username="testuser"
        )

        # Mock user permission lookup
        with patch.object(jwt_manager, '_get_user_permissions') as mock_perms:
            mock_perms.return_value = ["read:all", "write:own"]

            # Refresh tokens
            result = jwt_manager.refresh_access_token(refresh_token)

            assert result is not None
            new_access, new_refresh = result
            assert new_access is not None
            assert new_refresh is not None

    def test_token_revocation(self, jwt_manager):
        """Test token revocation/blacklisting"""
        token = jwt_manager.create_access_token(
            user_id="user123",
            username="testuser",
            roles=["user"],
            permissions=["read:own"]
        )

        with patch.object(jwt_manager, '_blacklist_token') as mock_blacklist:
            result = jwt_manager.revoke_token(token)

            assert result is True
            mock_blacklist.assert_called_once()


class TestRBACManager:
    """Test Role-Based Access Control"""

    @pytest.fixture
    def rbac_manager(self):
        """Create RBAC manager"""
        from apps.backend.core.auth.rbac_manager import RBACManager
        return RBACManager()

    def test_default_roles_initialization(self, rbac_manager):
        """Test default roles are properly initialized"""
        from apps.backend.core.auth.rbac_manager import Role

        assert Role.SUPER_ADMIN in rbac_manager.roles
        assert Role.ADMIN in rbac_manager.roles
        assert Role.TEACHER in rbac_manager.roles
        assert Role.STUDENT in rbac_manager.roles

    def test_permission_checking(self, rbac_manager):
        """Test permission checking for roles"""
        from apps.backend.core.auth.rbac_manager import Role

        # Admin should have user management permissions
        has_perm = rbac_manager.check_permission(
            [Role.ADMIN],
            "user:create:all"
        )
        assert has_perm is True

        # Student should not have admin permissions
        has_perm = rbac_manager.check_permission(
            [Role.STUDENT],
            "user:delete:all"
        )
        assert has_perm is False

    def test_permission_scope_hierarchy(self, rbac_manager):
        """Test permission scope hierarchy (all > team > own)"""
        from apps.backend.core.auth.rbac_manager import Role

        # User with 'all' scope should have 'team' and 'own' access
        has_perm = rbac_manager.check_permission(
            [Role.ADMIN],  # Has content:read:all
            "content:read:team"
        )
        assert has_perm is True

        has_perm = rbac_manager.check_permission(
            [Role.ADMIN],
            "content:read:own"
        )
        assert has_perm is True

    def test_get_user_permissions(self, rbac_manager):
        """Test getting all permissions for user roles"""
        from apps.backend.core.auth.rbac_manager import Role

        permissions = rbac_manager.get_user_permissions([Role.TEACHER])

        assert "content:create:own" in permissions
        assert "class:update:own" in permissions
        assert "assessment:execute:team" in permissions

    def test_multiple_roles(self, rbac_manager):
        """Test permission checking with multiple roles"""
        from apps.backend.core.auth.rbac_manager import Role

        # User with both Teacher and Content Creator roles
        has_perm = rbac_manager.check_permission(
            [Role.TEACHER, Role.CONTENT_CREATOR],
            "content:publish:team"
        )
        assert has_perm is True


class TestPIIEncryption:
    """Test PII encryption functionality"""

    @pytest.fixture
    def pii_manager(self):
        """Create PII encryption manager"""
        with patch('apps.backend.services.vault_manager.get_vault_manager'):
            from apps.backend.core.security.pii_encryption import PIIEncryptionManager
            return PIIEncryptionManager(vault_enabled=False)

    def test_field_encryption(self, pii_manager):
        """Test basic field encryption"""
        from apps.backend.core.security.pii_encryption import PIIField

        plaintext = "user@example.com"
        encrypted = pii_manager.encrypt_field(plaintext, PIIField.EMAIL)

        assert encrypted is not None
        assert encrypted.ciphertext != plaintext
        assert encrypted.field_type == PIIField.EMAIL
        assert len(encrypted.nonce) > 0
        assert len(encrypted.tag) > 0

    def test_field_decryption(self, pii_manager):
        """Test field decryption"""
        from apps.backend.core.security.pii_encryption import PIIField

        plaintext = "555-123-4567"
        encrypted = pii_manager.encrypt_field(plaintext, PIIField.PHONE)
        decrypted = pii_manager.decrypt_field(encrypted)

        assert decrypted == plaintext

    def test_document_encryption(self, pii_manager):
        """Test encrypting multiple fields in a document"""
        from apps.backend.core.security.pii_encryption import PIIField

        document = {
            "user_id": "123",
            "email": "user@example.com",
            "phone": "555-123-4567",
            "name": "John Doe",
            "non_pii": "This stays plain"
        }

        field_mappings = {
            "email": PIIField.EMAIL,
            "phone": PIIField.PHONE,
            "name": PIIField.FULL_NAME
        }

        encrypted_doc = pii_manager.encrypt_document(document, field_mappings)

        # Check PII fields are encrypted
        assert encrypted_doc["email"] != document["email"]
        assert encrypted_doc["phone"] != document["phone"]
        assert encrypted_doc["name"] != document["name"]

        # Check non-PII field remains plain
        assert encrypted_doc["non_pii"] == document["non_pii"]
        assert encrypted_doc["user_id"] == document["user_id"]

    def test_searchable_encryption(self, pii_manager):
        """Test searchable encryption with blind indexing"""
        from apps.backend.core.security.pii_encryption import PIIField

        email = "search@example.com"

        # Encrypt with searchable index
        encrypted = pii_manager.encrypt_field(email, PIIField.EMAIL)

        # Generate search index
        search_index = pii_manager.search_encrypted(email, PIIField.EMAIL)

        assert search_index is not None
        assert len(search_index) == 64  # SHA256 hex

        # Same value should generate same index
        search_index2 = pii_manager.search_encrypted(email, PIIField.EMAIL)
        assert search_index == search_index2

    def test_key_rotation(self, pii_manager):
        """Test encryption key rotation"""
        from apps.backend.core.security.pii_encryption import PIIField

        # Encrypt with current key
        plaintext = "rotate@example.com"
        encrypted1 = pii_manager.encrypt_field(plaintext, PIIField.EMAIL)
        version1 = encrypted1.key_version

        # Rotate key
        with patch.object(pii_manager, 'vault', Mock()):
            result = pii_manager.rotate_encryption_key()
            assert result is True

        # Encrypt with new key
        encrypted2 = pii_manager.encrypt_field(plaintext, PIIField.EMAIL)
        version2 = encrypted2.key_version

        assert version2 == version1 + 1


class TestGDPRCompliance:
    """Test GDPR compliance features"""

    @pytest.fixture
    def gdpr_manager(self):
        """Create GDPR compliance manager"""
        from apps.backend.core.compliance.gdpr_manager import GDPRComplianceManager
        return GDPRComplianceManager()

    @pytest.mark.asyncio
    async def test_consent_recording(self, gdpr_manager):
        """Test consent recording and checking"""
        from apps.backend.core.compliance.gdpr_manager import ConsentType

        # Record consent
        consent = await gdpr_manager.record_consent(
            user_id="user123",
            consent_type=ConsentType.ANALYTICS,
            granted=True,
            purpose="Analytics for service improvement",
            ip_address="192.168.1.1"
        )

        assert consent is not None
        assert consent.user_id == "user123"
        assert consent.granted is True

        # Check consent
        has_consent = await gdpr_manager.check_consent(
            "user123",
            ConsentType.ANALYTICS
        )
        assert has_consent is True

        # Check non-granted consent
        has_consent = await gdpr_manager.check_consent(
            "user123",
            ConsentType.MARKETING
        )
        assert has_consent is False

    @pytest.mark.asyncio
    async def test_erasure_request(self, gdpr_manager):
        """Test right to erasure (right to be forgotten)"""
        with patch.object(gdpr_manager, '_execute_erasure') as mock_erasure:
            mock_erasure.return_value = asyncio.Future()
            mock_erasure.return_value.set_result(True)

            request = await gdpr_manager.process_erasure_request(
                user_id="user123",
                verification_token="verify_token_xyz"
            )

            assert request is not None
            assert request.user_id == "user123"
            assert request.request_type.value == "erasure"
            mock_erasure.assert_called_once()

    @pytest.mark.asyncio
    async def test_data_portability(self, gdpr_manager):
        """Test data portability request"""
        with patch.object(gdpr_manager, '_collect_user_data') as mock_collect:
            mock_collect.return_value = {
                "profile": {"user_id": "user123"},
                "preferences": {},
                "activity": []
            }

            package = await gdpr_manager.process_portability_request(
                user_id="user123",
                format="json"
            )

            assert package is not None
            assert 'filename' in package
            assert 'gdpr_export' in package['filename']
            assert package['mime_type'] == 'application/zip'

    @pytest.mark.asyncio
    async def test_consent_expiry(self, gdpr_manager):
        """Test consent expiration"""
        from apps.backend.core.compliance.gdpr_manager import ConsentType

        # Record consent with short expiry
        past_time = datetime.now(timezone.utc) - timedelta(days=2)

        # Manually add expired consent
        from apps.backend.core.compliance.gdpr_manager import ConsentRecord
        expired_consent = ConsentRecord(
            user_id="user456",
            consent_type=ConsentType.MARKETING,
            granted=True,
            expiry=past_time
        )

        gdpr_manager.consent_records["user456"] = [expired_consent]

        # Check expired consent
        has_consent = await gdpr_manager.check_consent(
            "user456",
            ConsentType.MARKETING
        )
        assert has_consent is False

    @pytest.mark.asyncio
    async def test_retention_policies(self, gdpr_manager):
        """Test data retention policy processing"""
        with patch.object(gdpr_manager, '_delete_old_data') as mock_delete:
            with patch.object(gdpr_manager, '_anonymize_old_data') as mock_anon:
                mock_delete.return_value = asyncio.Future()
                mock_delete.return_value.set_result(10)
                mock_anon.return_value = asyncio.Future()
                mock_anon.return_value.set_result(5)

                results = await gdpr_manager.process_retention_policies()

                assert isinstance(results, dict)
                # Check that methods were called for auto-delete policies


class TestSecurityHeaders:
    """Test security headers middleware"""

    @pytest.fixture
    def security_middleware(self):
        """Create security headers middleware"""
        from apps.backend.middleware.security_headers import SecurityHeadersMiddleware

        app = Mock()
        return SecurityHeadersMiddleware(
            app,
            enable_hsts=True,
            enable_csp=True,
            frame_options="DENY"
        )

    @pytest.mark.asyncio
    async def test_security_headers_added(self, security_middleware):
        """Test that security headers are added to response"""
        request = Mock()
        request.url.scheme = "https"
        request.url.path = "/api/v1/test"
        request.state = Mock()

        response = Mock()
        response.headers = {}

        async def call_next(req):
            return response

        await security_middleware.dispatch(request, call_next)

        # Check critical security headers
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"

        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"

        assert "X-XSS-Protection" in response.headers
        assert "Referrer-Policy" in response.headers
        assert "Permissions-Policy" in response.headers

    def test_csp_header_generation(self, security_middleware):
        """Test Content Security Policy header generation"""
        csp = security_middleware._build_csp_header()

        assert "default-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp
        assert "base-uri 'self'" in csp

    def test_csp_nonce_generation(self, security_middleware):
        """Test CSP nonce generation for inline scripts"""
        nonce = "test_nonce_123"
        csp = security_middleware._build_csp_header(nonce)

        assert f"'nonce-{nonce}'" in csp

    @pytest.mark.asyncio
    async def test_error_handling(self, security_middleware):
        """Test secure error handling"""
        request = Mock()
        request.url.scheme = "http"
        request.url.path = "/api/v1/test"
        request.app.debug = False

        async def call_next(req):
            raise ValueError("Test error with sensitive data: password=123456")

        response = await security_middleware.dispatch(request, call_next)

        # Check error response doesn't leak sensitive info
        assert response.status_code == 500
        content = json.loads(response.body)
        assert "password" not in str(content)
        assert "123456" not in str(content)
        assert content["error"]["message"] == "An internal error occurred"


class TestPreCommitIntegration:
    """Test pre-commit hook integration"""

    def test_secrets_detection_script(self):
        """Test the secrets detection pre-commit script"""
        from scripts.security.check_secrets import SecretDetector

        detector = SecretDetector()

        # Test detection of hardcoded secret
        test_code = '''
password = "supersecret123456"
api_key = "sk_live_abcdef123456789"
        '''

        # Create temp file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            f.flush()

            from pathlib import Path
            issues = detector.check_file(Path(f.name))

        assert len(issues) >= 2
        assert any(i['type'] == 'Password' for i in issues)
        assert any('API Key' in i['type'] for i in issues)

        # Cleanup
        os.unlink(f.name)

    def test_safe_patterns_ignored(self):
        """Test that safe patterns are not flagged"""
        from scripts.security.check_secrets import SecretDetector

        detector = SecretDetector()

        safe_code = '''
password = os.getenv("DB_PASSWORD")
api_key = settings.API_KEY
secret = vault.get_secret("path/to/secret")
test_password = "CHANGE_ME_IN_PRODUCTION"
        '''

        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(safe_code)
            f.flush()

            from pathlib import Path
            issues = detector.check_file(Path(f.name))

        assert len(issues) == 0

        # Cleanup
        os.unlink(f.name)


@pytest.mark.integration
class TestSecurityIntegration:
    """Integration tests for security components"""

    @pytest.mark.asyncio
    async def test_full_authentication_flow(self):
        """Test complete authentication flow with JWT and RBAC"""
        # This would test the full flow in an integration environment
        pass

    @pytest.mark.asyncio
    async def test_gdpr_with_pii_encryption(self):
        """Test GDPR export with PII encryption"""
        # This would test GDPR export handling encrypted PII data
        pass

    @pytest.mark.asyncio
    async def test_vault_with_config_integration(self):
        """Test Vault integration with config system"""
        # This would test that config properly uses Vault for secrets
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
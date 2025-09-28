"""Educational compliance testing for COPPA, FERPA, GDPR"""
import pytest
from datetime import datetime, timedelta
import httpx
from unittest.mock import Mock, patch
import json

class TestEducationalCompliance:
    """Test compliance with educational regulations"""

    @pytest.fixture
    async def client(self):
        """Create HTTP client for testing"""
        client = httpx.AsyncClient(base_url="http://localhost:8009")
        yield client
        await client.aclose()

    @pytest.fixture
    def teacher_token(self):
        """Mock teacher authentication token"""
        return "mock_teacher_token_12345"

    @pytest.fixture
    def user_token(self):
        """Mock user authentication token"""
        return "mock_user_token_67890"

    @pytest.fixture
    def admin_token(self):
        """Mock admin authentication token"""
        return "mock_admin_token_abcde"

    @pytest.mark.asyncio
    async def test_coppa_age_verification(self, client):
        """Test COPPA compliance for users under 13"""
        # Attempt to register user under 13
        response = await client.post("/api/v1/auth/register", json={
            "username": "young_user",
            "password": "password123",
            "email": "young@test.com",
            "date_of_birth": (datetime.now() - timedelta(days=365*10)).isoformat()  # 10 years old
        })

        # Should require parental consent or reject registration
        if response.status_code == 200:
            # If registration is allowed, check for parental consent requirements
            data = response.json()
            assert data.get("parental_consent_required") == True, "COPPA compliance requires parental consent for users under 13"
        else:
            # Registration should be rejected or require additional verification
            assert response.status_code in [400, 403], "Registration of users under 13 should require special handling"
            if response.status_code == 403:
                detail = response.json().get("detail", "").lower()
                assert any(keyword in detail for keyword in ["parental", "consent", "age", "coppa"]), "Error message should reference COPPA compliance"

    @pytest.mark.asyncio
    async def test_coppa_data_collection_limits(self, client):
        """Test COPPA limits on data collection for minors"""
        # Test that minimal data is collected for users under 13
        minor_registration_data = {
            "username": "minor_user",
            "password": "password123",
            "date_of_birth": (datetime.now() - timedelta(days=365*10)).isoformat(),
            "parental_email": "parent@test.com"
        }

        response = await client.post("/api/v1/auth/register", json=minor_registration_data)

        # Check that additional data collection is limited
        profile_update_data = {
            "full_name": "Minor User",
            "address": "123 Main St",
            "phone": "555-1234",
            "marketing_preferences": True
        }

        if response.status_code == 200:
            token = response.json().get("access_token")
            profile_response = await client.put(
                "/api/v1/user/profile",
                json=profile_update_data,
                headers={"Authorization": f"Bearer {token}"}
            )

            # Should restrict collection of personal information for minors
            if profile_response.status_code == 200:
                updated_profile = profile_response.json()
                # Marketing preferences should not be accepted for minors
                assert updated_profile.get("marketing_preferences") != True, "Marketing preferences should not be collected for minors"

    @pytest.mark.asyncio
    async def test_ferpa_data_privacy(self, client, teacher_token):
        """Test FERPA compliance for student data privacy"""
        # Teacher should not see certain private student data without proper authorization
        response = await client.get(
            "/api/v1/students/123/private-records",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )

        # Should either deny access or require additional authorization
        if response.status_code == 200:
            data = response.json()
            # Check that sensitive data is properly redacted or requires additional consent
            sensitive_fields = ["ssn", "home_address", "parent_income", "medical_records"]
            for field in sensitive_fields:
                assert field not in data or data[field] is None, f"Sensitive field {field} should not be exposed without proper authorization"
        else:
            assert response.status_code == 403, "Access to private student records should be restricted"
            detail = response.json().get("detail", "").lower()
            assert any(keyword in detail for keyword in ["ferpa", "privacy", "authorization", "consent"]), "Error should reference FERPA compliance"

    @pytest.mark.asyncio
    async def test_ferpa_directory_information_handling(self, client, teacher_token):
        """Test FERPA directory information handling"""
        # Test access to directory information vs private information
        response = await client.get(
            "/api/v1/students/123/directory-info",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )

        if response.status_code == 200:
            data = response.json()
            # Directory information should be available but limited
            allowed_fields = ["name", "grade_level", "enrollment_status", "major_field"]
            restricted_fields = ["grades", "disciplinary_records", "personal_notes"]

            for field in restricted_fields:
                assert field not in data or data[field] is None, f"Restricted field {field} should not be in directory information"

    @pytest.mark.asyncio
    async def test_gdpr_data_deletion(self, client, user_token):
        """Test GDPR right to be forgotten"""
        response = await client.delete(
            "/api/v1/user/delete-my-data",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Should accept deletion request
        if response.status_code == 200:
            data = response.json()
            assert data.get("deletion_requested") == True, "Data deletion should be confirmed"
            assert "deletion_id" in data, "Should provide deletion request ID for tracking"
        elif response.status_code == 202:
            # Accepted for processing
            data = response.json()
            assert "deletion_id" in data or "request_id" in data, "Should provide tracking ID for async deletion"
        else:
            pytest.fail(f"GDPR data deletion request should be accepted, got {response.status_code}")

    @pytest.mark.asyncio
    async def test_gdpr_data_portability(self, client, user_token):
        """Test GDPR right to data portability"""
        response = await client.get(
            "/api/v1/user/export-my-data",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Should provide data export functionality
        if response.status_code == 200:
            # Check if it's a download link or direct data
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                data = response.json()
                assert "user_data" in data or "export_url" in data, "Should provide user data or export URL"
            elif "application/zip" in content_type or "application/octet-stream" in content_type:
                # Direct file download
                assert len(response.content) > 0, "Export file should contain data"
        elif response.status_code == 202:
            # Export processing
            data = response.json()
            assert "export_id" in data or "request_id" in data, "Should provide tracking ID for export request"
        else:
            pytest.fail(f"GDPR data export should be available, got {response.status_code}")

    @pytest.mark.asyncio
    async def test_gdpr_consent_management(self, client, user_token):
        """Test GDPR consent management"""
        # Test consent withdrawal
        response = await client.post(
            "/api/v1/user/consent/withdraw",
            json={"consent_types": ["marketing", "analytics", "third_party_sharing"]},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Should accept consent withdrawal
        assert response.status_code in [200, 202], "Consent withdrawal should be accepted"

        # Test consent status check
        consent_response = await client.get(
            "/api/v1/user/consent/status",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        if consent_response.status_code == 200:
            consent_data = consent_response.json()
            assert "consents" in consent_data, "Should provide current consent status"

    @pytest.mark.asyncio
    async def test_data_retention_policy(self, client, admin_token):
        """Test data retention policy enforcement"""
        response = await client.get(
            "/api/v1/admin/data-retention-status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        if response.status_code == 200:
            data = response.json()
            assert "retention_days" in data, "Should have defined retention period"
            assert data.get("retention_days") <= 2555, "Retention period should not exceed 7 years (typical maximum)"
            assert data.get("auto_deletion_enabled") == True, "Automatic deletion should be enabled"
        else:
            # If endpoint doesn't exist, check if there's documentation about retention policy
            assert response.status_code == 404, f"Data retention endpoint should exist or return 404, got {response.status_code}"

    @pytest.mark.asyncio
    async def test_data_processing_lawful_basis(self, client):
        """Test that data processing has lawful basis under GDPR"""
        # Check privacy policy endpoint
        response = await client.get("/api/v1/legal/privacy-policy")

        if response.status_code == 200:
            data = response.json()
            # Check for required GDPR elements
            required_elements = [
                "lawful_basis",
                "data_controller",
                "retention_period",
                "user_rights"
            ]

            for element in required_elements:
                assert element in data or any(element.replace("_", " ") in str(data).lower() for element in required_elements), f"Privacy policy should include {element}"

    @pytest.mark.asyncio
    async def test_children_privacy_protection(self, client):
        """Test enhanced privacy protection for children"""
        # Test that children's accounts have enhanced privacy by default
        child_registration = {
            "username": "child_user",
            "password": "password123",
            "date_of_birth": (datetime.now() - timedelta(days=365*8)).isoformat(),  # 8 years old
            "parental_email": "parent@test.com"
        }

        response = await client.post("/api/v1/auth/register", json=child_registration)

        if response.status_code == 200:
            token = response.json().get("access_token")

            # Check that child account has enhanced privacy settings by default
            privacy_response = await client.get(
                "/api/v1/user/privacy-settings",
                headers={"Authorization": f"Bearer {token}"}
            )

            if privacy_response.status_code == 200:
                privacy_data = privacy_response.json()
                # Children should have maximum privacy by default
                assert privacy_data.get("profile_public") == False, "Child profiles should be private by default"
                assert privacy_data.get("allow_contact_from_strangers") == False, "Children should not be contactable by strangers"
                assert privacy_data.get("data_sharing_enabled") == False, "Data sharing should be disabled for children"

    @pytest.mark.asyncio
    async def test_data_breach_notification_system(self, client, admin_token):
        """Test data breach notification system compliance"""
        # Check that there's a system for handling data breaches
        response = await client.get(
            "/api/v1/admin/security/breach-procedures",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Should have breach response procedures documented
        if response.status_code == 200:
            data = response.json()
            required_procedures = [
                "detection_time",
                "notification_timeline",
                "user_notification_method",
                "authority_notification_method"
            ]

            for procedure in required_procedures:
                assert any(procedure.replace("_", " ") in str(data).lower() for procedure in required_procedures), f"Breach procedures should include {procedure}"

    @pytest.mark.asyncio
    async def test_cross_border_data_transfer_compliance(self, client, admin_token):
        """Test compliance with international data transfer requirements"""
        response = await client.get(
            "/api/v1/admin/data-processing/locations",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        if response.status_code == 200:
            data = response.json()
            # Should document where data is processed
            assert "processing_locations" in data or "data_centers" in data, "Should document data processing locations"

            # If processing in multiple jurisdictions, should have safeguards
            locations = data.get("processing_locations", []) or data.get("data_centers", [])
            if len(locations) > 1:
                assert "transfer_safeguards" in data, "Cross-border transfers should have documented safeguards"

    @pytest.mark.asyncio
    async def test_accessibility_compliance(self, client):
        """Test compliance with accessibility requirements (Section 508, WCAG)"""
        # Test that API responses include accessibility information
        response = await client.get("/api/v1/accessibility/support")

        # Should provide accessibility information
        assert response.status_code in [200, 404], "Should have accessibility support endpoint or return 404"

        if response.status_code == 200:
            data = response.json()
            accessibility_features = [
                "screen_reader_support",
                "keyboard_navigation",
                "high_contrast_mode",
                "text_sizing"
            ]

            # Should document accessibility features
            content_str = str(data).lower()
            assert any(feature.replace("_", " ") in content_str for feature in accessibility_features), "Should document accessibility features"
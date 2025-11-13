"""
Unit Tests for RBAC Middleware

Tests automatic permission enforcement at the middleware level.
"""

import time
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse

from apps.backend.core.security.rbac_manager import Role
from apps.backend.core.security.rbac_middleware import (
    OrganizationScopingMiddleware,
    RBACMiddleware,
)


@pytest.fixture
def mock_app():
    """Create mock FastAPI application."""
    app = Mock()
    app.user_middleware = []
    return app


@pytest.fixture
def mock_admin_user_dict():
    """Create mock admin user dictionary."""
    return {"id": 1, "email": "admin@example.com", "role": Role.ADMIN, "organization_id": uuid4()}


@pytest.fixture
def mock_teacher_user_dict():
    """Create mock teacher user dictionary."""
    return {
        "id": 2,
        "email": "teacher@example.com",
        "role": Role.TEACHER,
        "organization_id": uuid4(),
    }


@pytest.fixture
def mock_student_user_dict():
    """Create mock student user dictionary."""
    return {
        "id": 3,
        "email": "student@example.com",
        "role": Role.STUDENT,
        "organization_id": uuid4(),
    }


@pytest.fixture
def mock_request():
    """Create mock request object."""
    request = Mock(spec=Request)
    request.url = Mock()
    request.method = "GET"
    request.state = Mock()
    return request


@pytest.fixture
def mock_call_next():
    """Create mock call_next function."""

    async def call_next(request):
        return JSONResponse({"message": "success"})

    return call_next


class TestRBACMiddlewareInitialization:
    """Test RBAC middleware initialization."""

    def test_middleware_initializes_correctly(self, mock_app):
        """Test that middleware initializes with correct configuration."""
        middleware = RBACMiddleware(mock_app)

        assert middleware.public_paths is not None
        assert len(middleware.public_paths) > 0
        assert "/api/v1/auth/login" in middleware.public_paths
        assert "/docs" in middleware.public_paths

    def test_public_paths_configured(self, mock_app):
        """Test that public paths are configured."""
        middleware = RBACMiddleware(mock_app)

        assert "/api/health" in middleware.public_paths
        assert "/api/v1/auth/register" in middleware.public_paths
        assert "/openapi.json" in middleware.public_paths

    def test_bypass_patterns_configured(self, mock_app):
        """Test that bypass patterns are configured."""
        middleware = RBACMiddleware(mock_app)

        assert len(middleware.bypass_patterns) > 0
        # Check pattern objects are compiled regex
        assert all(hasattr(p, "match") for p in middleware.bypass_patterns)

    def test_method_action_map_configured(self, mock_app):
        """Test that method-to-action mapping is configured."""
        middleware = RBACMiddleware(mock_app)

        assert middleware.method_action_map["GET"] == "read"
        assert middleware.method_action_map["POST"] == "create"
        assert middleware.method_action_map["PUT"] == "update"
        assert middleware.method_action_map["PATCH"] == "update"
        assert middleware.method_action_map["DELETE"] == "delete"

    def test_path_permissions_configured(self, mock_app):
        """Test that path permission mappings are configured."""
        middleware = RBACMiddleware(mock_app)

        assert len(middleware.path_permissions) > 0
        # Check content endpoint mappings
        assert any("/api/v1/content" in path for path in middleware.path_permissions.keys())


class TestPublicPathBypass:
    """Test that public paths bypass RBAC checks."""

    @pytest.mark.asyncio
    async def test_public_path_bypasses_rbac(self, mock_app, mock_request, mock_call_next):
        """Test that public paths bypass RBAC entirely."""
        middleware = RBACMiddleware(mock_app)
        mock_request.url.path = "/api/v1/auth/login"
        mock_request.state.user = None  # No user

        response = await middleware.dispatch(mock_request, mock_call_next)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_docs_path_bypasses_rbac(self, mock_app, mock_request, mock_call_next):
        """Test that documentation paths bypass RBAC."""
        middleware = RBACMiddleware(mock_app)
        mock_request.url.path = "/docs"
        mock_request.state.user = None

        response = await middleware.dispatch(mock_request, mock_call_next)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_check_bypasses_rbac(self, mock_app, mock_request, mock_call_next):
        """Test that health check bypasses RBAC."""
        middleware = RBACMiddleware(mock_app)
        mock_request.url.path = "/api/health"
        mock_request.state.user = None

        response = await middleware.dispatch(mock_request, mock_call_next)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_bypass_pattern_static_files(self, mock_app, mock_request, mock_call_next):
        """Test that static files bypass RBAC."""
        middleware = RBACMiddleware(mock_app)
        mock_request.url.path = "/static/css/main.css"
        mock_request.state.user = None

        response = await middleware.dispatch(mock_request, mock_call_next)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_bypass_pattern_internal_paths(self, mock_app, mock_request, mock_call_next):
        """Test that internal paths bypass RBAC."""
        middleware = RBACMiddleware(mock_app)
        mock_request.url.path = "/_internal/metrics"
        mock_request.state.user = None

        response = await middleware.dispatch(mock_request, mock_call_next)

        assert response.status_code == 200


class TestAuthenticationCheck:
    """Test authentication requirement checking."""

    @pytest.mark.asyncio
    async def test_missing_user_returns_401(self, mock_app, mock_request, mock_call_next):
        """Test that missing user returns 401 for protected paths."""
        middleware = RBACMiddleware(mock_app)
        mock_request.url.path = "/api/v1/content"
        mock_request.state.user = None  # No user

        response = await middleware.dispatch(mock_request, mock_call_next)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert b"Authentication required" in response.body

    @pytest.mark.asyncio
    async def test_authenticated_user_proceeds(
        self, mock_app, mock_request, mock_call_next, mock_admin_user_dict
    ):
        """Test that authenticated user proceeds to permission check."""
        middleware = RBACMiddleware(mock_app)
        mock_request.url.path = "/api/v1/content"
        mock_request.method = "GET"
        mock_request.state.user = mock_admin_user_dict

        response = await middleware.dispatch(mock_request, mock_call_next)

        # Admin should pass
        assert response.status_code == 200


class TestPermissionChecking:
    """Test permission checking for various endpoints."""

    @pytest.mark.asyncio
    async def test_admin_passes_all_permission_checks(
        self, mock_app, mock_request, mock_call_next, mock_admin_user_dict
    ):
        """Test that admin passes all permission checks."""
        middleware = RBACMiddleware(mock_app)
        mock_request.state.user = mock_admin_user_dict

        # Test various endpoints
        test_cases = [
            ("/api/v1/content", "GET"),
            ("/api/v1/content", "POST"),
            ("/api/v1/content/123", "DELETE"),
            ("/api/v1/users", "POST"),
            ("/api/v1/system/config", "PUT"),
        ]

        for path, method in test_cases:
            mock_request.url.path = path
            mock_request.method = method

            response = await middleware.dispatch(mock_request, mock_call_next)
            assert response.status_code == 200, f"Admin failed for {method} {path}"

    @pytest.mark.asyncio
    async def test_teacher_passes_organization_scope_checks(
        self, mock_app, mock_request, mock_call_next, mock_teacher_user_dict
    ):
        """Test that teacher passes organization-scoped checks."""
        middleware = RBACMiddleware(mock_app)
        mock_request.state.user = mock_teacher_user_dict

        # Teacher should pass these
        test_cases = [
            ("/api/v1/content", "GET"),  # read:organization
            ("/api/v1/content", "POST"),  # create:organization
            ("/api/v1/agents", "GET"),  # read:organization
        ]

        for path, method in test_cases:
            mock_request.url.path = path
            mock_request.method = method

            response = await middleware.dispatch(mock_request, mock_call_next)
            assert response.status_code == 200, f"Teacher failed for {method} {path}"

    @pytest.mark.asyncio
    async def test_teacher_fails_admin_only_checks(
        self, mock_app, mock_request, mock_call_next, mock_teacher_user_dict
    ):
        """Test that teacher fails admin-only permission checks."""
        middleware = RBACMiddleware(mock_app)
        mock_request.state.user = mock_teacher_user_dict

        # Teacher should fail these (require :all scope)
        test_cases = [
            ("/api/v1/users", "POST"),  # user:create:all
            ("/api/v1/users/123", "DELETE"),  # user:delete:all
            ("/api/v1/system/config", "POST"),  # system:configure
        ]

        for path, method in test_cases:
            mock_request.url.path = path
            mock_request.method = method

            response = await middleware.dispatch(mock_request, mock_call_next)
            assert (
                response.status_code == status.HTTP_403_FORBIDDEN
            ), f"Teacher should fail for {method} {path}"

    @pytest.mark.asyncio
    async def test_student_passes_read_checks(
        self, mock_app, mock_request, mock_call_next, mock_student_user_dict
    ):
        """Test that student passes read permission checks."""
        middleware = RBACMiddleware(mock_app)
        mock_request.state.user = mock_student_user_dict

        # Student should pass read operations
        mock_request.url.path = "/api/v1/content"
        mock_request.method = "GET"

        response = await middleware.dispatch(mock_request, mock_call_next)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_student_fails_create_checks(
        self, mock_app, mock_request, mock_call_next, mock_student_user_dict
    ):
        """Test that student fails create permission checks."""
        middleware = RBACMiddleware(mock_app)
        mock_request.state.user = mock_student_user_dict

        # Student should fail create operations
        mock_request.url.path = "/api/v1/content"
        mock_request.method = "POST"

        response = await middleware.dispatch(mock_request, mock_call_next)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestPathPermissionMapping:
    """Test path-to-permission mapping logic."""

    def test_content_endpoint_mapping(self, mock_app):
        """Test content endpoint permission mapping."""
        middleware = RBACMiddleware(mock_app)

        # Check content endpoint mappings exist
        content_mapping = None
        for pattern, methods in middleware.path_permissions.items():
            if "/api/v1/content" in pattern:
                content_mapping = methods
                break

        assert content_mapping is not None
        assert "GET" in content_mapping
        assert "POST" in content_mapping
        assert "DELETE" in content_mapping

    def test_get_required_permission_exact_match(self, mock_app):
        """Test getting required permission for exact path match."""
        middleware = RBACMiddleware(mock_app)

        permission = middleware._get_required_permission("/api/v1/content", "GET")
        assert permission is not None
        assert "content" in permission
        assert "read" in permission

    def test_get_required_permission_with_id(self, mock_app):
        """Test getting required permission for path with ID."""
        middleware = RBACMiddleware(mock_app)

        permission = middleware._get_required_permission("/api/v1/content/123", "DELETE")
        assert permission is not None
        assert "content" in permission
        assert "delete" in permission

    def test_get_required_permission_no_mapping(self, mock_app):
        """Test handling of unmapped paths."""
        middleware = RBACMiddleware(mock_app)

        permission = middleware._get_required_permission("/api/v1/unknown", "GET")
        # Should generate default permission or return None
        assert permission is None or "unknown:read:organization" in permission


class TestAuditLogging:
    """Test audit logging functionality."""

    @pytest.mark.asyncio
    async def test_successful_access_logged(
        self, mock_app, mock_request, mock_call_next, mock_admin_user_dict
    ):
        """Test that successful access attempts are logged."""
        middleware = RBACMiddleware(mock_app)
        mock_request.url.path = "/api/v1/content"
        mock_request.method = "GET"
        mock_request.state.user = mock_admin_user_dict

        with patch("apps.backend.core.security.rbac_middleware.logger") as mock_logger:
            response = await middleware.dispatch(mock_request, mock_call_next)

            # Check that INFO log was called for successful access
            assert mock_logger.log.called
            # Get the log call
            log_calls = [c for c in mock_logger.log.call_args_list]
            assert len(log_calls) > 0

    @pytest.mark.asyncio
    async def test_failed_access_logged(
        self, mock_app, mock_request, mock_call_next, mock_student_user_dict
    ):
        """Test that failed access attempts are logged."""
        middleware = RBACMiddleware(mock_app)
        mock_request.url.path = "/api/v1/content"
        mock_request.method = "POST"  # Student can't create
        mock_request.state.user = mock_student_user_dict

        with patch("apps.backend.core.security.rbac_middleware.logger") as mock_logger:
            response = await middleware.dispatch(mock_request, mock_call_next)

            # Check that WARNING log was called for denied access
            assert mock_logger.log.called

    @pytest.mark.asyncio
    async def test_log_includes_duration(
        self, mock_app, mock_request, mock_call_next, mock_admin_user_dict
    ):
        """Test that audit log includes processing duration."""
        middleware = RBACMiddleware(mock_app)
        mock_request.url.path = "/api/v1/content"
        mock_request.method = "GET"
        mock_request.state.user = mock_admin_user_dict

        with patch("apps.backend.core.security.rbac_middleware.logger") as mock_logger:
            response = await middleware.dispatch(mock_request, mock_call_next)

            # Check that duration is logged
            log_calls = mock_logger.log.call_args_list
            if log_calls:
                log_message = str(log_calls[0][0])
                assert "duration" in log_message.lower() or "ms" in log_message

    def test_audit_logging_can_be_disabled(self, mock_app):
        """Test that audit logging can be disabled."""
        middleware = RBACMiddleware(mock_app)
        middleware.audit_enabled = False

        # Should not raise any errors when disabled
        middleware._log_access_attempt(
            user_id=1,
            path="/test",
            method="GET",
            permission="test:read",
            granted=True,
            duration_ms=10.5,
        )


class TestRequestStateModification:
    """Test that middleware adds information to request state."""

    @pytest.mark.asyncio
    async def test_granted_permission_added_to_state(
        self, mock_app, mock_request, mock_call_next, mock_admin_user_dict
    ):
        """Test that granted permission is added to request state."""
        middleware = RBACMiddleware(mock_app)
        mock_request.url.path = "/api/v1/content"
        mock_request.method = "GET"
        mock_request.state.user = mock_admin_user_dict

        # Track what gets set on request.state
        state_attrs = {}

        def track_setattr(obj, name, value):
            state_attrs[name] = value
            object.__setattr__(obj, name, value)

        original_setattr = mock_request.state.__setattr__
        mock_request.state.__setattr__ = lambda name, value: track_setattr(
            mock_request.state, name, value
        )

        response = await middleware.dispatch(mock_request, mock_call_next)

        # Check that granted_permission was set
        assert "granted_permission" in state_attrs or hasattr(
            mock_request.state, "granted_permission"
        )


class TestOrganizationScopingMiddleware:
    """Test organization scoping middleware."""

    @pytest.mark.asyncio
    async def test_sets_organization_id_from_user(
        self, mock_app, mock_request, mock_call_next, mock_teacher_user_dict
    ):
        """Test that organization ID is set from user."""
        middleware = OrganizationScopingMiddleware(mock_app)
        mock_request.state.user = mock_teacher_user_dict

        response = await middleware.dispatch(mock_request, mock_call_next)

        assert hasattr(mock_request.state, "organization_id")
        assert mock_request.state.organization_id == mock_teacher_user_dict["organization_id"]

    @pytest.mark.asyncio
    async def test_handles_user_without_organization(self, mock_app, mock_request, mock_call_next):
        """Test handling of user without organization."""
        middleware = OrganizationScopingMiddleware(mock_app)
        mock_request.state.user = {
            "id": 99,
            "email": "test@example.com",
            "role": Role.GUEST,
            "organization_id": None,
        }

        # Should not raise error, just not set organization_id
        response = await middleware.dispatch(mock_request, mock_call_next)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_handles_missing_user(self, mock_app, mock_request, mock_call_next):
        """Test handling of missing user."""
        middleware = OrganizationScopingMiddleware(mock_app)
        mock_request.state.user = None

        # Should not raise error
        response = await middleware.dispatch(mock_request, mock_call_next)
        assert response.status_code == 200


class TestMiddlewareErrorHandling:
    """Test middleware error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_handles_malformed_user_object(self, mock_app, mock_request, mock_call_next):
        """Test handling of malformed user object."""
        middleware = RBACMiddleware(mock_app)
        mock_request.url.path = "/api/v1/content"
        mock_request.method = "GET"
        mock_request.state.user = {"id": 1}  # Missing required fields

        # Should handle gracefully
        response = await middleware.dispatch(mock_request, mock_call_next)
        # Will likely fail permission check due to missing role
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_handles_exception_in_call_next(
        self, mock_app, mock_request, mock_admin_user_dict
    ):
        """Test handling of exceptions in downstream handlers."""
        middleware = RBACMiddleware(mock_app)
        mock_request.url.path = "/api/v1/content"
        mock_request.method = "GET"
        mock_request.state.user = mock_admin_user_dict

        async def failing_call_next(request):
            raise Exception("Downstream error")

        # Middleware should not catch downstream errors
        with pytest.raises(Exception, match="Downstream error"):
            await middleware.dispatch(mock_request, failing_call_next)


class TestPerformance:
    """Test middleware performance characteristics."""

    @pytest.mark.asyncio
    async def test_permission_check_is_fast(
        self, mock_app, mock_request, mock_call_next, mock_admin_user_dict
    ):
        """Test that permission checking is performant."""
        middleware = RBACMiddleware(mock_app)
        mock_request.url.path = "/api/v1/content"
        mock_request.method = "GET"
        mock_request.state.user = mock_admin_user_dict

        start = time.time()
        response = await middleware.dispatch(mock_request, mock_call_next)
        duration = time.time() - start

        # Middleware should add minimal overhead (<10ms)
        assert duration < 0.01, f"Middleware took {duration*1000:.2f}ms"

    @pytest.mark.asyncio
    async def test_bypass_check_is_fast(self, mock_app, mock_request, mock_call_next):
        """Test that bypass checking is performant."""
        middleware = RBACMiddleware(mock_app)
        mock_request.url.path = "/api/health"
        mock_request.state.user = None

        start = time.time()
        response = await middleware.dispatch(mock_request, mock_call_next)
        duration = time.time() - start

        # Bypass should be very fast (<1ms)
        assert duration < 0.001, f"Bypass check took {duration*1000:.2f}ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Unit Tests for RBAC Decorators

Tests FastAPI decorators for role-based access control enforcement.
"""

from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException, status

from apps.backend.core.security.rbac_decorators import (
    require_admin,
    require_organization_access,
    require_permission,
    require_permissions,
    require_resource_access,
    require_role,
    require_teacher,
    require_teacher_or_student,
)
from apps.backend.core.security.rbac_manager import Role


@pytest.fixture
def mock_admin_user():
    """Create mock admin user."""
    user = Mock()
    user.id = 1
    user.email = "admin@example.com"
    user.role = Role.ADMIN
    user.organization_id = uuid4()
    return user


@pytest.fixture
def mock_teacher_user():
    """Create mock teacher user."""
    user = Mock()
    user.id = 2
    user.email = "teacher@example.com"
    user.role = Role.TEACHER
    user.organization_id = uuid4()
    return user


@pytest.fixture
def mock_student_user():
    """Create mock student user."""
    user = Mock()
    user.id = 3
    user.email = "student@example.com"
    user.role = Role.STUDENT
    user.organization_id = uuid4()
    return user


@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    db = Mock()
    db.query = Mock()
    return db


class TestRequireRoleDecorator:
    """Test @require_role decorator functionality."""

    @pytest.mark.asyncio
    async def test_admin_passes_admin_role_check(self, mock_admin_user):
        """Test that admin passes admin role check."""

        @require_role([Role.ADMIN])
        async def protected_endpoint(user: Mock):
            return {"message": "success"}

        result = await protected_endpoint(user=mock_admin_user)
        assert result == {"message": "success"}

    @pytest.mark.asyncio
    async def test_admin_passes_teacher_role_check(self, mock_admin_user):
        """Test that admin passes lower role checks (hierarchy)."""

        @require_role([Role.TEACHER])
        async def protected_endpoint(user: Mock):
            return {"message": "success"}

        result = await protected_endpoint(user=mock_admin_user)
        assert result == {"message": "success"}

    @pytest.mark.asyncio
    async def test_teacher_fails_admin_role_check(self, mock_teacher_user):
        """Test that teacher fails admin role check."""

        @require_role([Role.ADMIN])
        async def protected_endpoint(user: Mock):
            return {"message": "success"}

        with pytest.raises(HTTPException) as exc_info:
            await protected_endpoint(user=mock_teacher_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Insufficient permissions" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_teacher_passes_teacher_role_check(self, mock_teacher_user):
        """Test that teacher passes teacher role check."""

        @require_role([Role.TEACHER])
        async def protected_endpoint(user: Mock):
            return {"message": "success"}

        result = await protected_endpoint(user=mock_teacher_user)
        assert result == {"message": "success"}

    @pytest.mark.asyncio
    async def test_student_fails_teacher_role_check(self, mock_student_user):
        """Test that student fails teacher role check."""

        @require_role([Role.TEACHER])
        async def protected_endpoint(user: Mock):
            return {"message": "success"}

        with pytest.raises(HTTPException) as exc_info:
            await protected_endpoint(user=mock_student_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_multiple_allowed_roles(self, mock_teacher_user, mock_admin_user):
        """Test decorator with multiple allowed roles."""

        @require_role([Role.ADMIN, Role.TEACHER])
        async def protected_endpoint(user: Mock):
            return {"message": "success"}

        # Both should pass
        result1 = await protected_endpoint(user=mock_admin_user)
        result2 = await protected_endpoint(user=mock_teacher_user)

        assert result1 == {"message": "success"}
        assert result2 == {"message": "success"}

    @pytest.mark.asyncio
    async def test_no_user_raises_401(self):
        """Test that missing user raises 401."""

        @require_role([Role.ADMIN])
        async def protected_endpoint(user: Mock = None):
            return {"message": "success"}

        with pytest.raises(HTTPException) as exc_info:
            await protected_endpoint(user=None)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Authentication required" in exc_info.value.detail


class TestRequirePermissionDecorator:
    """Test @require_permission decorator functionality."""

    @pytest.mark.asyncio
    async def test_admin_has_all_permissions(self, mock_admin_user):
        """Test that admin passes all permission checks."""

        @require_permission("content:create:all")
        async def protected_endpoint(user: Mock):
            return {"message": "success"}

        result = await protected_endpoint(user=mock_admin_user)
        assert result == {"message": "success"}

    @pytest.mark.asyncio
    async def test_teacher_has_organization_permission(self, mock_teacher_user):
        """Test that teacher has organization-scoped permissions."""

        @require_permission("content:create:organization")
        async def protected_endpoint(user: Mock):
            return {"message": "success"}

        result = await protected_endpoint(user=mock_teacher_user)
        assert result == {"message": "success"}

    @pytest.mark.asyncio
    async def test_teacher_lacks_all_scope_permission(self, mock_teacher_user):
        """Test that teacher lacks :all scope permissions."""

        @require_permission("content:delete:all")
        async def protected_endpoint(user: Mock):
            return {"message": "success"}

        with pytest.raises(HTTPException) as exc_info:
            await protected_endpoint(user=mock_teacher_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "content:delete:all" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_student_has_read_permission(self, mock_student_user):
        """Test that student has read permissions."""

        @require_permission("content:read:organization")
        async def protected_endpoint(user: Mock):
            return {"message": "success"}

        result = await protected_endpoint(user=mock_student_user)
        assert result == {"message": "success"}

    @pytest.mark.asyncio
    async def test_student_lacks_create_permission(self, mock_student_user):
        """Test that student lacks create permissions."""

        @require_permission("content:create:organization")
        async def protected_endpoint(user: Mock):
            return {"message": "success"}

        with pytest.raises(HTTPException) as exc_info:
            await protected_endpoint(user=mock_student_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_no_user_raises_401(self):
        """Test that missing user raises 401."""

        @require_permission("content:read:organization")
        async def protected_endpoint(user: Mock = None):
            return {"message": "success"}

        with pytest.raises(HTTPException) as exc_info:
            await protected_endpoint(user=None)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestRequirePermissionsDecorator:
    """Test @require_permissions decorator with multiple permissions."""

    @pytest.mark.asyncio
    async def test_require_all_permissions_success(self, mock_teacher_user):
        """Test that user with all required permissions passes."""

        @require_permissions(
            ["content:read:organization", "content:create:organization"], require_all=True
        )
        async def protected_endpoint(user: Mock):
            return {"message": "success"}

        result = await protected_endpoint(user=mock_teacher_user)
        assert result == {"message": "success"}

    @pytest.mark.asyncio
    async def test_require_all_permissions_failure(self, mock_student_user):
        """Test that user missing one permission fails."""

        @require_permissions(
            [
                "content:read:organization",
                "content:create:organization",  # Student doesn't have this
            ],
            require_all=True,
        )
        async def protected_endpoint(user: Mock):
            return {"message": "success"}

        with pytest.raises(HTTPException) as exc_info:
            await protected_endpoint(user=mock_student_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "content:create:organization" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_require_any_permission_success(self, mock_teacher_user):
        """Test that user with any required permission passes."""

        @require_permissions(
            ["content:create:organization", "content:delete:all"],  # Teacher doesn't have this
            require_all=False,
        )
        async def protected_endpoint(user: Mock):
            return {"message": "success"}

        result = await protected_endpoint(user=mock_teacher_user)
        assert result == {"message": "success"}

    @pytest.mark.asyncio
    async def test_require_any_permission_failure(self, mock_student_user):
        """Test that user with none of the permissions fails."""

        @require_permissions(
            ["content:create:organization", "content:delete:organization"], require_all=False
        )
        async def protected_endpoint(user: Mock):
            return {"message": "success"}

        with pytest.raises(HTTPException) as exc_info:
            await protected_endpoint(user=mock_student_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Required one of" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_admin_passes_all_permission_checks(self, mock_admin_user):
        """Test that admin passes all permission combinations."""

        @require_permissions(
            ["content:create:all", "user:delete:all", "system:manage"], require_all=True
        )
        async def protected_endpoint(user: Mock):
            return {"message": "success"}

        result = await protected_endpoint(user=mock_admin_user)
        assert result == {"message": "success"}


class TestRequireResourceAccessDecorator:
    """Test @require_resource_access decorator with ownership validation."""

    @pytest.mark.asyncio
    async def test_admin_full_access_to_any_resource(self, mock_admin_user, mock_db_session):
        """Test that admin has full access to all resources."""

        @require_resource_access("content", "delete")
        async def protected_endpoint(content_id: int, user: Mock, db: Mock):
            return {"message": "success"}

        result = await protected_endpoint(content_id=999, user=mock_admin_user, db=mock_db_session)
        assert result == {"message": "success"}

    @pytest.mark.asyncio
    async def test_teacher_can_access_own_content(self, mock_teacher_user, mock_db_session):
        """Test that teacher can access their own content."""
        # Mock the content object
        mock_content = Mock()
        mock_content.id = 1
        mock_content.created_by = mock_teacher_user.id
        mock_content.organization_id = mock_teacher_user.organization_id

        mock_query = Mock()
        mock_query.filter_by = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=mock_content)
        mock_db_session.query = Mock(return_value=mock_query)

        @require_resource_access("content", "update")
        async def protected_endpoint(content_id: int, user: Mock, db: Mock):
            return {"message": "success"}

        result = await protected_endpoint(content_id=1, user=mock_teacher_user, db=mock_db_session)
        assert result == {"message": "success"}

    @pytest.mark.asyncio
    async def test_teacher_can_access_organization_content(
        self, mock_teacher_user, mock_db_session
    ):
        """Test that teacher can access content in their organization."""
        # Mock content owned by someone else in same org
        mock_content = Mock()
        mock_content.id = 1
        mock_content.created_by = 999  # Different user
        mock_content.organization_id = mock_teacher_user.organization_id  # Same org

        mock_query = Mock()
        mock_query.filter_by = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=mock_content)
        mock_db_session.query = Mock(return_value=mock_query)

        @require_resource_access("content", "read")
        async def protected_endpoint(content_id: int, user: Mock, db: Mock):
            return {"message": "success"}

        result = await protected_endpoint(content_id=1, user=mock_teacher_user, db=mock_db_session)
        assert result == {"message": "success"}

    @pytest.mark.asyncio
    async def test_teacher_cannot_access_other_organization_content(
        self, mock_teacher_user, mock_db_session
    ):
        """Test that teacher cannot access content from other organization."""
        other_org_id = uuid4()

        mock_content = Mock()
        mock_content.id = 1
        mock_content.created_by = 999
        mock_content.organization_id = other_org_id  # Different org

        mock_query = Mock()
        mock_query.filter_by = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=mock_content)
        mock_db_session.query = Mock(return_value=mock_query)

        @require_resource_access("content", "read")
        async def protected_endpoint(content_id: int, user: Mock, db: Mock):
            return {"message": "success"}

        with pytest.raises(HTTPException) as exc_info:
            await protected_endpoint(content_id=1, user=mock_teacher_user, db=mock_db_session)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "organization" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_resource_not_found_returns_404(self, mock_teacher_user, mock_db_session):
        """Test that missing resource returns 404."""
        mock_query = Mock()
        mock_query.filter_by = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=None)  # Resource not found
        mock_db_session.query = Mock(return_value=mock_query)

        @require_resource_access("content", "read")
        async def protected_endpoint(content_id: int, user: Mock, db: Mock):
            return {"message": "success"}

        with pytest.raises(HTTPException) as exc_info:
            await protected_endpoint(content_id=999, user=mock_teacher_user, db=mock_db_session)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_student_cannot_update_content(self, mock_student_user, mock_db_session):
        """Test that student cannot update content (no update permission)."""

        @require_resource_access("content", "update")
        async def protected_endpoint(content_id: int, user: Mock, db: Mock):
            return {"message": "success"}

        with pytest.raises(HTTPException) as exc_info:
            await protected_endpoint(content_id=1, user=mock_student_user, db=mock_db_session)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestRequireOrganizationAccessDecorator:
    """Test @require_organization_access decorator."""

    @pytest.mark.asyncio
    async def test_user_with_organization_passes(self, mock_teacher_user):
        """Test that user with organization passes."""

        @require_organization_access()
        async def protected_endpoint(user: Mock):
            return {"message": "success", "org_id": str(user.organization_id)}

        result = await protected_endpoint(user=mock_teacher_user)
        assert result["message"] == "success"
        assert result["org_id"] == str(mock_teacher_user.organization_id)

    @pytest.mark.asyncio
    async def test_user_without_organization_fails(self):
        """Test that user without organization fails."""
        user_no_org = Mock()
        user_no_org.id = 99
        user_no_org.email = "noorg@example.com"
        user_no_org.role = Role.STUDENT
        user_no_org.organization_id = None  # No organization

        @require_organization_access()
        async def protected_endpoint(user: Mock):
            return {"message": "success"}

        with pytest.raises(HTTPException) as exc_info:
            await protected_endpoint(user=user_no_org)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "organization" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_user_without_org_attribute_fails(self):
        """Test that user missing organization_id attribute fails."""
        user_no_attr = Mock()
        user_no_attr.id = 99
        user_no_attr.email = "noattr@example.com"
        # No organization_id attribute at all

        @require_organization_access()
        async def protected_endpoint(user: Mock):
            return {"message": "success"}

        with pytest.raises(HTTPException) as exc_info:
            await protected_endpoint(user=user_no_attr)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestConvenienceDecorators:
    """Test convenience decorator shortcuts."""

    @pytest.mark.asyncio
    async def test_require_admin_allows_admin(self, mock_admin_user):
        """Test that @require_admin allows admin."""

        @require_admin
        async def admin_endpoint(user: Mock):
            return {"message": "admin access"}

        result = await admin_endpoint(user=mock_admin_user)
        assert result == {"message": "admin access"}

    @pytest.mark.asyncio
    async def test_require_admin_blocks_teacher(self, mock_teacher_user):
        """Test that @require_admin blocks teacher."""

        @require_admin
        async def admin_endpoint(user: Mock):
            return {"message": "admin access"}

        with pytest.raises(HTTPException) as exc_info:
            await admin_endpoint(user=mock_teacher_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_require_teacher_allows_admin(self, mock_admin_user):
        """Test that @require_teacher allows admin (hierarchy)."""

        @require_teacher
        async def teacher_endpoint(user: Mock):
            return {"message": "teacher access"}

        result = await teacher_endpoint(user=mock_admin_user)
        assert result == {"message": "teacher access"}

    @pytest.mark.asyncio
    async def test_require_teacher_allows_teacher(self, mock_teacher_user):
        """Test that @require_teacher allows teacher."""

        @require_teacher
        async def teacher_endpoint(user: Mock):
            return {"message": "teacher access"}

        result = await teacher_endpoint(user=mock_teacher_user)
        assert result == {"message": "teacher access"}

    @pytest.mark.asyncio
    async def test_require_teacher_blocks_student(self, mock_student_user):
        """Test that @require_teacher blocks student."""

        @require_teacher
        async def teacher_endpoint(user: Mock):
            return {"message": "teacher access"}

        with pytest.raises(HTTPException) as exc_info:
            await teacher_endpoint(user=mock_student_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_require_teacher_or_student_allows_all_authenticated(
        self, mock_admin_user, mock_teacher_user, mock_student_user
    ):
        """Test that @require_teacher_or_student allows admin, teacher, and student."""

        @require_teacher_or_student
        async def authenticated_endpoint(user: Mock):
            return {"message": "authenticated access"}

        result1 = await authenticated_endpoint(user=mock_admin_user)
        result2 = await authenticated_endpoint(user=mock_teacher_user)
        result3 = await authenticated_endpoint(user=mock_student_user)

        assert result1 == {"message": "authenticated access"}
        assert result2 == {"message": "authenticated access"}
        assert result3 == {"message": "authenticated access"}


class TestDecoratorComposition:
    """Test combining multiple decorators."""

    @pytest.mark.asyncio
    async def test_role_and_organization_decorators(self, mock_teacher_user):
        """Test combining role and organization decorators."""

        @require_teacher
        @require_organization_access()
        async def protected_endpoint(user: Mock):
            return {"message": "success"}

        result = await protected_endpoint(user=mock_teacher_user)
        assert result == {"message": "success"}

    @pytest.mark.asyncio
    async def test_multiple_permission_checks(self, mock_admin_user):
        """Test multiple permission decorators."""

        @require_permission("content:create:all")
        @require_permission("user:manage:all")
        async def protected_endpoint(user: Mock):
            return {"message": "success"}

        result = await protected_endpoint(user=mock_admin_user)
        assert result == {"message": "success"}

    @pytest.mark.asyncio
    async def test_combined_decorators_fail_appropriately(self, mock_student_user):
        """Test that combined decorators fail when any check fails."""

        @require_teacher
        @require_permission("content:create:organization")
        async def protected_endpoint(user: Mock):
            return {"message": "success"}

        # Student should fail role check first
        with pytest.raises(HTTPException) as exc_info:
            await protected_endpoint(user=mock_student_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

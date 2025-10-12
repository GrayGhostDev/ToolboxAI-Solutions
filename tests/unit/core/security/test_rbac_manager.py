"""
Unit Tests for RBAC Manager

Tests role definitions, permissions, and access control logic.
"""

import pytest
from unittest.mock import Mock
from uuid import uuid4

from apps.backend.core.security.rbac_manager import (
    RBACManager,
    Role,
    Permission,
    RoleDefinition,
    rbac_manager
)


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


class TestRBACManagerInitialization:
    """Test RBAC manager initialization."""

    def test_singleton_pattern(self):
        """Test that RBACManager implements singleton pattern."""
        manager1 = RBACManager()
        manager2 = RBACManager()
        assert manager1 is manager2

    def test_roles_defined(self):
        """Test that all roles are defined."""
        assert Role.ADMIN in rbac_manager.roles
        assert Role.TEACHER in rbac_manager.roles
        assert Role.STUDENT in rbac_manager.roles
        assert Role.GUEST in rbac_manager.roles

    def test_role_hierarchy(self):
        """Test role hierarchy levels."""
        assert rbac_manager.ROLE_HIERARCHY[Role.ADMIN] > rbac_manager.ROLE_HIERARCHY[Role.TEACHER]
        assert rbac_manager.ROLE_HIERARCHY[Role.TEACHER] > rbac_manager.ROLE_HIERARCHY[Role.STUDENT]
        assert rbac_manager.ROLE_HIERARCHY[Role.STUDENT] > rbac_manager.ROLE_HIERARCHY[Role.GUEST]


class TestPermissionParsing:
    """Test permission string parsing."""

    def test_parse_basic_permission(self):
        """Test parsing basic permission format."""
        perm = Permission.from_string("content:create")
        assert perm.resource == "content"
        assert perm.action == "create"
        assert perm.scope == "own"

    def test_parse_permission_with_scope(self):
        """Test parsing permission with explicit scope."""
        perm = Permission.from_string("content:create:organization")
        assert perm.resource == "content"
        assert perm.action == "create"
        assert perm.scope == "organization"

    def test_parse_invalid_permission(self):
        """Test parsing invalid permission format."""
        with pytest.raises(ValueError):
            Permission.from_string("invalid_format")

    def test_permission_string_representation(self):
        """Test permission string conversion."""
        perm = Permission(resource="content", action="create", scope="organization")
        assert str(perm) == "content:create:organization"

        perm_own = Permission(resource="content", action="create", scope="own")
        assert str(perm_own) == "content:create"


class TestRolePermissions:
    """Test role permission definitions."""

    def test_admin_has_all_permissions(self):
        """Test that admin has comprehensive permissions."""
        admin_perms = rbac_manager.get_role_permissions(Role.ADMIN)

        assert "system:manage" in admin_perms
        assert "user:create:all" in admin_perms
        assert "content:delete:all" in admin_perms
        assert "organization:manage:all" in admin_perms

    def test_teacher_has_organization_scope(self):
        """Test that teacher has organization-scoped permissions."""
        teacher_perms = rbac_manager.get_role_permissions(Role.TEACHER)

        assert "content:create:organization" in teacher_perms
        assert "class:create:organization" in teacher_perms
        assert "analytics:read:organization" in teacher_perms

        # Teacher should NOT have "all" scope permissions
        assert "content:delete:all" not in teacher_perms
        assert "user:create:all" not in teacher_perms

    def test_student_has_limited_permissions(self):
        """Test that student has read-only permissions."""
        student_perms = rbac_manager.get_role_permissions(Role.STUDENT)

        assert "content:read:organization" in student_perms
        assert "analytics:read:own" in student_perms

        # Student should NOT be able to create or delete
        assert "content:create:organization" not in student_perms
        assert "content:delete:own" not in student_perms

    def test_guest_minimal_permissions(self):
        """Test that guest has minimal permissions."""
        guest_perms = rbac_manager.get_role_permissions(Role.GUEST)

        assert "content:read:public" in guest_perms
        assert len(guest_perms) == 1  # Only one permission


class TestUserPermissions:
    """Test user permission checking."""

    def test_get_admin_permissions(self, mock_admin_user):
        """Test getting permissions for admin user."""
        perms = rbac_manager.get_user_permissions(mock_admin_user)
        assert len(perms) > 0
        assert "system:manage" in perms

    def test_get_teacher_permissions(self, mock_teacher_user):
        """Test getting permissions for teacher user."""
        perms = rbac_manager.get_user_permissions(mock_teacher_user)
        assert "content:create:organization" in perms

    def test_get_permissions_no_user(self):
        """Test getting permissions for None user."""
        perms = rbac_manager.get_user_permissions(None)
        assert perms == set()

    def test_get_permissions_user_without_role(self):
        """Test getting permissions for user without role."""
        user = Mock()
        user.id = 99
        # No role attribute
        perms = rbac_manager.get_user_permissions(user)
        assert perms == set()


class TestPermissionChecking:
    """Test has_permission functionality."""

    def test_admin_has_all_scope(self, mock_admin_user):
        """Test that admin has :all scope permissions."""
        assert rbac_manager.has_permission(mock_admin_user, "content:create:all")
        assert rbac_manager.has_permission(mock_admin_user, "user:delete:all")
        assert rbac_manager.has_permission(mock_admin_user, "organization:manage:all")

    def test_teacher_has_organization_scope(self, mock_teacher_user):
        """Test that teacher has :organization scope."""
        assert rbac_manager.has_permission(mock_teacher_user, "content:create:organization")
        assert rbac_manager.has_permission(mock_teacher_user, "class:read:organization")

    def test_teacher_no_all_scope(self, mock_teacher_user):
        """Test that teacher doesn't have :all scope."""
        assert not rbac_manager.has_permission(mock_teacher_user, "content:delete:all")
        assert not rbac_manager.has_permission(mock_teacher_user, "user:create:all")

    def test_student_read_only(self, mock_student_user):
        """Test that student has read-only access."""
        assert rbac_manager.has_permission(mock_student_user, "content:read:organization")
        assert not rbac_manager.has_permission(mock_student_user, "content:create:organization")

    def test_permission_with_ownership(self, mock_teacher_user):
        """Test permission checking with resource ownership."""
        # Teacher trying to access their own content
        assert rbac_manager.has_permission(
            mock_teacher_user,
            "content:update:own",
            resource_owner_id=mock_teacher_user.id
        )

        # Teacher trying to access someone else's content
        assert rbac_manager.has_permission(
            mock_teacher_user,
            "content:update:own",
            resource_owner_id=999  # Different owner
        ) is False


class TestRoleHierarchy:
    """Test role hierarchy checking."""

    def test_admin_has_all_roles(self, mock_admin_user):
        """Test that admin passes all role checks."""
        assert rbac_manager.has_role(mock_admin_user, Role.ADMIN)
        assert rbac_manager.has_role(mock_admin_user, Role.TEACHER)
        assert rbac_manager.has_role(mock_admin_user, Role.STUDENT)

    def test_teacher_hierarchy(self, mock_teacher_user):
        """Test teacher role hierarchy."""
        assert not rbac_manager.has_role(mock_teacher_user, Role.ADMIN)
        assert rbac_manager.has_role(mock_teacher_user, Role.TEACHER)
        assert rbac_manager.has_role(mock_teacher_user, Role.STUDENT)

    def test_student_lowest_role(self, mock_student_user):
        """Test student is lowest privileged role."""
        assert not rbac_manager.has_role(mock_student_user, Role.ADMIN)
        assert not rbac_manager.has_role(mock_student_user, Role.TEACHER)
        assert rbac_manager.has_role(mock_student_user, Role.STUDENT)


class TestResourceAccess:
    """Test check_resource_access functionality."""

    def test_admin_full_access(self, mock_admin_user):
        """Test admin has access to all resources."""
        assert rbac_manager.check_resource_access(
            mock_admin_user,
            "content",
            "delete",
            resource_owner_id=999,
            resource_org_id=uuid4()
        )

    def test_teacher_own_content(self, mock_teacher_user):
        """Test teacher can access their own content."""
        assert rbac_manager.check_resource_access(
            mock_teacher_user,
            "content",
            "update",
            resource_owner_id=mock_teacher_user.id,
            resource_org_id=mock_teacher_user.organization_id
        )

    def test_teacher_organization_content(self, mock_teacher_user):
        """Test teacher can access organization content."""
        assert rbac_manager.check_resource_access(
            mock_teacher_user,
            "content",
            "read",
            resource_owner_id=999,  # Different owner
            resource_org_id=mock_teacher_user.organization_id  # Same org
        )

    def test_teacher_no_other_org_access(self, mock_teacher_user):
        """Test teacher cannot access other organization's content."""
        other_org_id = uuid4()
        assert not rbac_manager.check_resource_access(
            mock_teacher_user,
            "content",
            "read",
            resource_owner_id=999,
            resource_org_id=other_org_id
        )


class TestAccessibleResources:
    """Test get_accessible_resources functionality."""

    def test_admin_scope_all(self, mock_admin_user):
        """Test admin gets 'all' scope."""
        scope = rbac_manager.get_accessible_resources(mock_admin_user, "content", "read")
        assert scope["scope"] == "all"

    def test_teacher_scope_organization(self, mock_teacher_user):
        """Test teacher gets 'organization' scope."""
        scope = rbac_manager.get_accessible_resources(mock_teacher_user, "content", "read")
        assert scope["scope"] == "organization"
        assert scope["organization_id"] == mock_teacher_user.organization_id

    def test_student_scope_own(self, mock_student_user):
        """Test student gets 'own' scope for some resources."""
        scope = rbac_manager.get_accessible_resources(mock_student_user, "analytics", "read")
        assert scope["scope"] == "own"
        assert scope["user_id"] == mock_student_user.id

    def test_no_access_scope(self, mock_student_user):
        """Test scope returns 'none' for unauthorized resources."""
        scope = rbac_manager.get_accessible_resources(mock_student_user, "system", "manage")
        assert scope["scope"] == "none"


class TestPermissionCaching:
    """Test permission caching for performance."""

    def test_permission_cache_populated(self):
        """Test that permission cache is used."""
        # First call
        perms1 = rbac_manager.get_role_permissions(Role.ADMIN)

        # Cache should now contain admin permissions
        assert Role.ADMIN in rbac_manager._permission_cache

        # Second call should return cached result
        perms2 = rbac_manager.get_role_permissions(Role.ADMIN)

        assert perms1 is perms2  # Same object reference


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

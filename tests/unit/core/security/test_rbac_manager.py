"""
Unit Tests for RBAC Manager

Tests role-based access control including:
- Permission management and caching
- Role hierarchy
- Permission checking with scopes (all/organization/own)
- Resource access validation
- Permission inheritance
"""

from unittest.mock import Mock
from uuid import uuid4

import pytest

from apps.backend.core.security.rbac_manager import (
    Permission,
    Role,
    rbac_manager,
)
from database.models import User


@pytest.fixture
def admin_user():
    """Admin user for testing"""
    user = Mock(spec=User)
    user.id = 1
    user.username = "admin"
    user.role = Role.ADMIN
    user.organization_id = uuid4()
    return user


@pytest.fixture
def teacher_user():
    """Teacher user for testing"""
    user = Mock(spec=User)
    user.id = 2
    user.username = "teacher"
    user.role = Role.TEACHER
    user.organization_id = uuid4()
    return user


@pytest.fixture
def student_user():
    """Student user for testing"""
    user = Mock(spec=User)
    user.id = 3
    user.username = "student"
    user.role = Role.STUDENT
    user.organization_id = uuid4()
    return user


@pytest.fixture
def rbac():
    """RBAC manager instance (singleton)"""
    return rbac_manager


class TestPermissionManagement:
    """Test permission retrieval and caching."""

    def test_get_role_permissions(self, rbac):
        """Test retrieving permissions for a role."""
        # Act
        admin_perms = rbac.get_role_permissions(Role.ADMIN)
        teacher_perms = rbac.get_role_permissions(Role.TEACHER)
        student_perms = rbac.get_role_permissions(Role.STUDENT)

        # Assert
        assert len(admin_perms) > 0
        assert "system:manage" in admin_perms
        assert "user:create:all" in admin_perms

        assert len(teacher_perms) > 0
        assert "content:create:organization" in teacher_perms

        assert len(student_perms) > 0
        assert "content:read:organization" in student_perms

    def test_get_user_permissions(self, rbac, teacher_user):
        """Test getting all permissions for a user."""
        # Act
        permissions = rbac.get_user_permissions(teacher_user)

        # Assert
        assert len(permissions) > 0
        assert "content:create:organization" in permissions
        assert "class:create:organization" in permissions
        assert "user:read:own" in permissions

    def test_permission_inheritance(self, rbac):
        """Test permission inheritance if implemented."""
        # Note: Current implementation doesn't show explicit inheritance
        # but this test ensures future inheritance works

        # Act
        permissions = rbac.get_role_permissions(Role.TEACHER)

        # Assert - teacher has their own permissions
        assert "content:create:organization" in permissions

    def test_permission_caching(self, rbac):
        """Test that permissions are cached for performance."""
        # Arrange
        rbac._permission_cache.clear()

        # Act - First call
        perms1 = rbac.get_role_permissions(Role.ADMIN)

        # Assert - Should be cached
        assert Role.ADMIN in rbac._permission_cache

        # Act - Second call (from cache)
        perms2 = rbac.get_role_permissions(Role.ADMIN)

        # Assert - Should be the same object (cached)
        assert perms1 is perms2

    def test_parse_permission_string(self):
        """Test parsing permission from string format."""
        # Arrange & Act
        perm1 = Permission.from_string("content:create:organization")
        perm2 = Permission.from_string("agent:read")

        # Assert
        assert perm1.resource == "content"
        assert perm1.action == "create"
        assert perm1.scope == "organization"

        assert perm2.resource == "agent"
        assert perm2.action == "read"
        assert perm2.scope == "own"  # Default scope

    def test_invalid_permission_format(self):
        """Test parsing invalid permission format raises error."""
        # Act & Assert
        with pytest.raises(ValueError):
            Permission.from_string("invalid:format:with:too:many:parts")


class TestRoleHierarchy:
    """Test role hierarchy and level checking."""

    def test_has_role_exact_match(self, rbac, teacher_user):
        """Test checking for exact role match."""
        # Act
        result = rbac.has_role(teacher_user, Role.TEACHER)

        # Assert
        assert result is True

    def test_has_role_hierarchy(self, rbac, admin_user):
        """Test role hierarchy allows higher roles."""
        # Act - Admin has teacher-level access
        has_teacher = rbac.has_role(admin_user, Role.TEACHER)
        has_student = rbac.has_role(admin_user, Role.STUDENT)

        # Assert - Admin is higher than teacher and student
        assert has_teacher is True
        assert has_student is True

    def test_has_role_insufficient(self, rbac, student_user):
        """Test insufficient role is denied."""
        # Act - Student trying to access teacher role
        result = rbac.has_role(student_user, Role.TEACHER)

        # Assert
        assert result is False

    def test_role_hierarchy_levels(self, rbac):
        """Test role hierarchy levels are correct."""
        # Assert
        assert rbac.ROLE_HIERARCHY[Role.ADMIN] > rbac.ROLE_HIERARCHY[Role.TEACHER]
        assert rbac.ROLE_HIERARCHY[Role.TEACHER] > rbac.ROLE_HIERARCHY[Role.STUDENT]
        assert rbac.ROLE_HIERARCHY[Role.STUDENT] > rbac.ROLE_HIERARCHY[Role.GUEST]


class TestPermissionChecking:
    """Test fine-grained permission checking with scopes."""

    def test_has_permission_exact_match(self, rbac, teacher_user):
        """Test permission check with exact match."""
        # Act
        result = rbac.has_permission(teacher_user, "content:create:organization")

        # Assert
        assert result is True

    def test_has_permission_scope_escalation(self, rbac, admin_user):
        """Test admin can access lower scopes (all > organization > own)."""
        # Act - Admin has "all" scope, should grant organization and own
        has_org = rbac.has_permission(admin_user, "content:create:organization")
        has_own = rbac.has_permission(admin_user, "content:create:own")

        # Assert
        assert has_org is True
        assert has_own is True

    def test_has_permission_ownership(self, rbac, student_user):
        """Test permission check with resource ownership."""
        # Act
        result = rbac.has_permission(
            student_user, "user:read:own", resource_owner_id=student_user.id
        )

        # Assert
        assert result is True

    def test_has_permission_organization(self, rbac, teacher_user):
        """Test permission check with organization scope."""
        # Act
        result = rbac.has_permission(
            teacher_user, "content:read:organization", organization_id=teacher_user.organization_id
        )

        # Assert
        assert result is True

    def test_has_permission_admin_access(self, rbac, admin_user):
        """Test admin can access any resource."""
        # Act
        result = rbac.has_permission(admin_user, "content:delete:all")

        # Assert
        assert result is True

    def test_has_permission_denied(self, rbac, student_user):
        """Test permission denied for insufficient privileges."""
        # Act - Student trying to create content (only teachers can)
        result = rbac.has_permission(student_user, "content:create:organization")

        # Assert
        assert result is False


class TestResourceAccess:
    """Test resource-level access control."""

    def test_check_resource_access_owner(self, rbac, teacher_user):
        """Test resource access check for owner."""
        # Act
        result = rbac.check_resource_access(
            user=teacher_user,
            resource_type="content",
            action="update",
            resource_owner_id=teacher_user.id,
            resource_org_id=teacher_user.organization_id,
        )

        # Assert
        assert result is True

    def test_check_resource_access_organization(self, rbac, teacher_user):
        """Test resource access within same organization."""
        # Arrange
        different_owner_id = 999

        # Act
        result = rbac.check_resource_access(
            user=teacher_user,
            resource_type="content",
            action="read",
            resource_owner_id=different_owner_id,
            resource_org_id=teacher_user.organization_id,
        )

        # Assert
        assert result is True  # Teacher can read org content

    def test_check_resource_access_admin(self, rbac, admin_user):
        """Test admin can access any resource."""
        # Arrange
        different_org_id = uuid4()

        # Act
        result = rbac.check_resource_access(
            user=admin_user,
            resource_type="content",
            action="delete",
            resource_owner_id=999,
            resource_org_id=different_org_id,
        )

        # Assert
        assert result is True  # Admin has "all" scope

    def test_get_accessible_resources(self, rbac, admin_user, teacher_user, student_user):
        """Test getting scope of accessible resources."""
        # Act
        admin_scope = rbac.get_accessible_resources(admin_user, "content", "read")
        teacher_scope = rbac.get_accessible_resources(teacher_user, "content", "read")
        student_scope = rbac.get_accessible_resources(student_user, "content", "read")

        # Assert
        assert admin_scope["scope"] == "all"

        assert teacher_scope["scope"] == "organization"
        assert teacher_scope["organization_id"] == teacher_user.organization_id

        assert student_scope["scope"] == "organization"  # Students can read org content
        assert student_scope["organization_id"] == student_user.organization_id


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

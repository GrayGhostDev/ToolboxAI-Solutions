"""
Role-Based Access Control (RBAC) Manager

Comprehensive RBAC system for managing roles, permissions, and access control.

Features:
- Role hierarchy (admin > teacher > student)
- Fine-grained permissions
- Resource-level access control
- Organization-scoped permissions
- Permission inheritance
- Audit logging

Usage:
    from apps.backend.core.security.rbac_manager import rbac_manager

    # Check permission
    if rbac_manager.has_permission(user, "content:create"):
        # Allow action

    # Get user permissions
    permissions = rbac_manager.get_user_permissions(user)
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID

from database.models import User

logger = logging.getLogger(__name__)


class Role(str, Enum):
    """System roles with hierarchy."""

    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"
    GUEST = "guest"


class ResourceType(str, Enum):
    """Resource types for permission scoping."""

    CONTENT = "content"
    AGENT = "agent"
    ORGANIZATION = "organization"
    USER = "user"
    CLASS = "class"
    ANALYTICS = "analytics"
    SYSTEM = "system"


class Action(str, Enum):
    """Actions that can be performed on resources."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    MANAGE = "manage"


@dataclass
class Permission:
    """Permission definition with scope and constraints."""

    resource: str  # e.g., "content", "agent", "organization"
    action: str  # e.g., "create", "read", "update", "delete"
    scope: str = "own"  # "own", "organization", "all"
    conditions: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """String representation: resource:action[:scope]"""
        base = f"{self.resource}:{self.action}"
        if self.scope != "own":
            base += f":{self.scope}"
        return base

    @classmethod
    def from_string(cls, permission_str: str) -> "Permission":
        """Parse permission from string format."""
        parts = permission_str.split(":")
        if len(parts) == 2:
            return cls(resource=parts[0], action=parts[1])
        elif len(parts) == 3:
            return cls(resource=parts[0], action=parts[1], scope=parts[2])
        else:
            raise ValueError(f"Invalid permission format: {permission_str}")


@dataclass
class RoleDefinition:
    """Role definition with permissions and hierarchy."""

    name: str
    display_name: str
    permissions: set[str]
    inherits_from: str | None = None
    description: str = ""
    level: int = 0  # Hierarchy level (higher = more privileged)


class RBACManager:
    """
    Role-Based Access Control Manager.

    Manages roles, permissions, and access control policies.
    Implements singleton pattern for centralized management.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize RBAC manager with default roles and permissions."""
        if self._initialized:
            return

        # Role hierarchy (higher level = more privileged)
        self.ROLE_HIERARCHY = {
            Role.ADMIN: 100,
            Role.TEACHER: 50,
            Role.STUDENT: 10,
            Role.GUEST: 0,
        }

        # Define roles with permissions
        self.roles: dict[str, RoleDefinition] = self._define_roles()

        # Permission cache for performance
        self._permission_cache: dict[str, set[str]] = {}

        self._initialized = True
        logger.info("RBACManager initialized with roles: %s", list(self.roles.keys()))

    def _define_roles(self) -> dict[str, RoleDefinition]:
        """Define system roles and their permissions."""
        return {
            # ADMIN - Full system access
            Role.ADMIN: RoleDefinition(
                name=Role.ADMIN,
                display_name="Administrator",
                level=100,
                description="Full system access and management",
                permissions={
                    # System management
                    "system:manage",
                    "system:configure",
                    "system:monitor",
                    # User management
                    "user:create:all",
                    "user:read:all",
                    "user:update:all",
                    "user:delete:all",
                    "user:manage:all",
                    # Organization management
                    "organization:create:all",
                    "organization:read:all",
                    "organization:update:all",
                    "organization:delete:all",
                    "organization:manage:all",
                    # Content management
                    "content:create:all",
                    "content:read:all",
                    "content:update:all",
                    "content:delete:all",
                    "content:publish:all",
                    # Agent management
                    "agent:create:all",
                    "agent:read:all",
                    "agent:update:all",
                    "agent:delete:all",
                    "agent:execute:all",
                    # Analytics
                    "analytics:read:all",
                    "analytics:export:all",
                    # Class management
                    "class:create:all",
                    "class:read:all",
                    "class:update:all",
                    "class:delete:all",
                },
            ),
            # TEACHER - Organization-scoped access
            Role.TEACHER: RoleDefinition(
                name=Role.TEACHER,
                display_name="Teacher",
                level=50,
                description="Manage classes, students, and content within organization",
                permissions={
                    # Own profile
                    "user:read:own",
                    "user:update:own",
                    # Organization scope
                    "organization:read:organization",
                    # Content management (organization scope)
                    "content:create:organization",
                    "content:read:organization",
                    "content:update:own",
                    "content:delete:own",
                    "content:publish:organization",
                    # Agent usage
                    "agent:read:organization",
                    "agent:execute:organization",
                    # Class management (organization scope)
                    "class:create:organization",
                    "class:read:organization",
                    "class:update:own",
                    "class:delete:own",
                    # Student management (within classes)
                    "user:read:organization",
                    "user:update:organization",  # For student management
                    # Analytics (organization scope)
                    "analytics:read:organization",
                    "analytics:export:organization",
                },
            ),
            # STUDENT - Limited access
            Role.STUDENT: RoleDefinition(
                name=Role.STUDENT,
                display_name="Student",
                level=10,
                description="Access learning content and track progress",
                permissions={
                    # Own profile
                    "user:read:own",
                    "user:update:own",
                    # Content access (read only)
                    "content:read:organization",
                    # Agent usage (limited)
                    "agent:read:organization",
                    "agent:execute:own",
                    # Class access
                    "class:read:own",
                    # Own analytics
                    "analytics:read:own",
                },
            ),
            # GUEST - Minimal access
            Role.GUEST: RoleDefinition(
                name=Role.GUEST,
                display_name="Guest",
                level=0,
                description="Limited read-only access",
                permissions={
                    "content:read:public",
                },
            ),
        }

    def get_role_permissions(self, role: str) -> set[str]:
        """
        Get all permissions for a role, including inherited permissions.

        Args:
            role: Role name

        Returns:
            Set of permission strings
        """
        # Check cache
        if role in self._permission_cache:
            return self._permission_cache[role]

        if role not in self.roles:
            logger.warning(f"Unknown role: {role}")
            return set()

        role_def = self.roles[role]
        permissions = set(role_def.permissions)

        # Add inherited permissions
        if role_def.inherits_from:
            parent_permissions = self.get_role_permissions(role_def.inherits_from)
            permissions.update(parent_permissions)

        # Cache result
        self._permission_cache[role] = permissions

        return permissions

    def get_user_permissions(self, user: User) -> set[str]:
        """
        Get all permissions for a user based on their role.

        Args:
            user: User instance

        Returns:
            Set of permission strings
        """
        if not user or not hasattr(user, "role"):
            return set()

        return self.get_role_permissions(user.role)

    def has_permission(
        self,
        user: User,
        permission: str,
        resource_owner_id: int | None = None,
        organization_id: UUID | None = None,
    ) -> bool:
        """
        Check if user has a specific permission.

        Args:
            user: User to check
            permission: Permission string (e.g., "content:create:organization")
            resource_owner_id: ID of resource owner (for "own" scope)
            organization_id: Organization ID (for "organization" scope)

        Returns:
            True if user has permission
        """
        if not user or not hasattr(user, "role"):
            return False

        # Parse permission
        try:
            perm = Permission.from_string(permission)
        except ValueError:
            logger.error(f"Invalid permission format: {permission}")
            return False

        # Get user permissions
        user_permissions = self.get_user_permissions(user)

        # Check for exact match
        if permission in user_permissions:
            return True

        # Check for broader scope permissions
        # e.g., if user has "content:create:all", they also have "content:create:organization"
        if perm.scope == "own":
            # Check for organization scope
            org_perm = f"{perm.resource}:{perm.action}:organization"
            if org_perm in user_permissions:
                # Verify organization match
                if organization_id and hasattr(user, "organization_id"):
                    if user.organization_id == organization_id:
                        return True

            # Check for all scope
            all_perm = f"{perm.resource}:{perm.action}:all"
            if all_perm in user_permissions:
                return True

        elif perm.scope == "organization":
            # Check for all scope
            all_perm = f"{perm.resource}:{perm.action}:all"
            if all_perm in user_permissions:
                return True

        # Check resource ownership for "own" scope
        if perm.scope == "own" and resource_owner_id:
            base_perm = f"{perm.resource}:{perm.action}:own"
            if base_perm in user_permissions and user.id == resource_owner_id:
                return True

        return False

    def has_role(self, user: User, required_role: str) -> bool:
        """
        Check if user has a specific role or higher in hierarchy.

        Args:
            user: User to check
            required_role: Required role name

        Returns:
            True if user has role or higher
        """
        if not user or not hasattr(user, "role"):
            return False

        user_level = self.ROLE_HIERARCHY.get(user.role, -1)
        required_level = self.ROLE_HIERARCHY.get(required_role, 100)

        return user_level >= required_level

    def check_resource_access(
        self,
        user: User,
        resource_type: str,
        action: str,
        resource_owner_id: int | None = None,
        resource_org_id: UUID | None = None,
    ) -> bool:
        """
        Check if user can perform action on resource.

        Args:
            user: User attempting access
            resource_type: Type of resource (content, agent, etc.)
            action: Action to perform (create, read, update, delete)
            resource_owner_id: Owner of the resource
            resource_org_id: Organization owning the resource

        Returns:
            True if access is allowed
        """
        # Check ownership
        if resource_owner_id == user.id:
            own_perm = f"{resource_type}:{action}:own"
            if self.has_permission(user, own_perm):
                return True

        # Check organization scope
        if resource_org_id and hasattr(user, "organization_id"):
            if resource_org_id == user.organization_id:
                org_perm = f"{resource_type}:{action}:organization"
                if self.has_permission(user, org_perm):
                    return True

        # Check all scope (admin)
        all_perm = f"{resource_type}:{action}:all"
        if self.has_permission(user, all_perm):
            return True

        return False

    def get_accessible_resources(
        self, user: User, resource_type: str, action: str = "read"
    ) -> dict[str, Any]:
        """
        Get scope of resources accessible to user.

        Args:
            user: User to check
            resource_type: Type of resource
            action: Action to check (default: read)

        Returns:
            Dictionary with scope information
        """
        result = {"scope": "none", "organization_id": None, "user_id": None}

        # Check for "all" scope (admin)
        all_perm = f"{resource_type}:{action}:all"
        if self.has_permission(user, all_perm):
            result["scope"] = "all"
            return result

        # Check for organization scope
        org_perm = f"{resource_type}:{action}:organization"
        if self.has_permission(user, org_perm) and hasattr(user, "organization_id"):
            result["scope"] = "organization"
            result["organization_id"] = user.organization_id
            return result

        # Check for own scope
        own_perm = f"{resource_type}:{action}:own"
        if self.has_permission(user, own_perm):
            result["scope"] = "own"
            result["user_id"] = user.id
            return result

        return result


# Global RBAC manager instance
rbac_manager = RBACManager()

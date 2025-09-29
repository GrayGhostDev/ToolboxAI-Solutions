"""
Unit tests for RLSPolicyGeneratorTool.

This module provides comprehensive unit tests for the RLS policy generator tool
used in Supabase migration, including policy generation, validation, and SQL generation.
"""

import pytest
import asyncio
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch

from core.agents.supabase.tools.rls_policy_generator import (
    RLSPolicyGeneratorTool,
    RLSPolicy,
    PolicyType
)


@pytest.fixture
def sample_schema():
    """Provide sample schema for testing."""
    return {
        'tables': [
            {
                'name': 'users',
                'columns': [
                    {'name': 'id', 'type': 'UUID'},
                    {'name': 'email', 'type': 'VARCHAR(255)'},
                    {'name': 'created_at', 'type': 'TIMESTAMP'}
                ]
            },
            {
                'name': 'lessons',
                'columns': [
                    {'name': 'id', 'type': 'UUID'},
                    {'name': 'title', 'type': 'VARCHAR(255)'},
                    {'name': 'content', 'type': 'TEXT'},
                    {'name': 'created_by', 'type': 'UUID'},
                    {'name': 'status', 'type': 'VARCHAR(50)'}
                ]
            },
            {
                'name': 'admin_settings',
                'columns': [
                    {'name': 'id', 'type': 'UUID'},
                    {'name': 'setting_key', 'type': 'VARCHAR(255)'},
                    {'name': 'setting_value', 'type': 'TEXT'}
                ]
            },
            {
                'name': 'posts',
                'columns': [
                    {'name': 'id', 'type': 'UUID'},
                    {'name': 'title', 'type': 'VARCHAR(255)'},
                    {'name': 'user_id', 'type': 'UUID'}
                ]
            }
        ]
    }


@pytest.fixture
def sample_access_patterns():
    """Provide sample access patterns for testing."""
    return {
        'lessons': {
            'multi_tenant': True,
            'hierarchical': False,
            'time_based': True
        },
        'posts': {
            'multi_tenant': False,
            'hierarchical': True,
            'time_based': False
        },
        'admin_settings': {
            'multi_tenant': False,
            'hierarchical': False,
            'time_based': False
        }
    }


class TestRLSPolicyGeneratorTool:
    """Test cases for RLSPolicyGeneratorTool."""

    def test_tool_initialization(self):
        """Test tool initialization."""
        tool = RLSPolicyGeneratorTool()

        assert isinstance(tool.policy_templates, dict)
        assert len(tool.policy_templates) > 0
        assert tool.generated_policies == []

        # Check some expected templates
        assert 'owner_only' in tool.policy_templates
        assert 'public_read' in tool.policy_templates
        assert 'authenticated_only' in tool.policy_templates

    @pytest.mark.asyncio
    async def test_generate_policies_basic(self, sample_schema):
        """Test basic policy generation without access patterns."""
        tool = RLSPolicyGeneratorTool()

        policies = await tool.generate_policies(sample_schema)

        assert len(policies) > 0
        assert len(tool.generated_policies) == len(policies)

        # Check that policies were generated for all tables
        table_names = {policy['table'] for policy in policies}
        expected_tables = {'users', 'lessons', 'admin_settings', 'posts'}
        assert table_names == expected_tables

    @pytest.mark.asyncio
    async def test_generate_policies_with_access_patterns(self, sample_schema, sample_access_patterns):
        """Test policy generation with access patterns."""
        tool = RLSPolicyGeneratorTool()

        policies = await tool.generate_policies(sample_schema, sample_access_patterns)

        assert len(policies) > 0

        # Check that multi-tenant policies were generated
        policy_names = [policy['name'] for policy in policies]
        assert any('tenant_isolation' in name for name in policy_names)
        assert any('hierarchical' in name for name in policy_names)
        assert any('time_based' in name for name in policy_names)

    def test_is_user_table(self):
        """Test user table identification."""
        tool = RLSPolicyGeneratorTool()

        assert tool._is_user_table('users', {}) is True
        assert tool._is_user_table('user_profiles', {}) is True
        assert tool._is_user_table('accounts', {}) is True
        assert tool._is_user_table('members', {}) is True
        assert tool._is_user_table('posts', {}) is False
        assert tool._is_user_table('lessons', {}) is False

    def test_is_content_table(self):
        """Test content table identification."""
        tool = RLSPolicyGeneratorTool()

        assert tool._is_content_table('content', {}) is True
        assert tool._is_content_table('lessons', {}) is True
        assert tool._is_content_table('quizzes', {}) is True
        assert tool._is_content_table('assessments', {}) is True
        assert tool._is_content_table('courses', {}) is True
        assert tool._is_content_table('users', {}) is False
        assert tool._is_content_table('admin_settings', {}) is False

    def test_is_admin_table(self):
        """Test admin table identification."""
        tool = RLSPolicyGeneratorTool()

        assert tool._is_admin_table('admin_settings', {}) is True
        assert tool._is_admin_table('system_config', {}) is True
        assert tool._is_admin_table('audit_logs', {}) is True
        assert tool._is_admin_table('users', {}) is False
        assert tool._is_admin_table('lessons', {}) is False

    def test_generate_user_policies(self):
        """Test user table policy generation."""
        tool = RLSPolicyGeneratorTool()

        policies = tool._generate_user_policies('users')

        assert len(policies) == 3

        # Check policy names and types
        policy_names = [p['name'] for p in policies]
        assert 'users_select_own' in policy_names
        assert 'users_update_own' in policy_names
        assert 'users_admin_all' in policy_names

        # Check policy types
        select_policy = next(p for p in policies if p['name'] == 'users_select_own')
        assert select_policy['policy_type'] == 'SELECT'
        assert 'authenticated' in select_policy['roles']
        assert 'auth.uid() = user_id' in select_policy['using_clause']

        update_policy = next(p for p in policies if p['name'] == 'users_update_own')
        assert update_policy['policy_type'] == 'UPDATE'
        assert update_policy['check_clause'] is not None

        admin_policy = next(p for p in policies if p['name'] == 'users_admin_all')
        assert admin_policy['policy_type'] == 'ALL'
        assert 'service_role' in admin_policy['roles']

    def test_generate_content_policies(self):
        """Test content table policy generation."""
        tool = RLSPolicyGeneratorTool()

        policies = tool._generate_content_policies('lessons')

        assert len(policies) == 4

        # Check policy names
        policy_names = [p['name'] for p in policies]
        assert 'lessons_public_select' in policy_names
        assert 'lessons_teacher_insert' in policy_names
        assert 'lessons_creator_update' in policy_names
        assert 'lessons_student_enrolled' in policy_names

        # Check public select policy
        public_policy = next(p for p in policies if p['name'] == 'lessons_public_select')
        assert public_policy['policy_type'] == 'SELECT'
        assert 'anon' in public_policy['roles']
        assert 'authenticated' in public_policy['roles']
        assert 'published' in public_policy['using_clause'] or 'approved' in public_policy['using_clause']

        # Check teacher insert policy
        teacher_policy = next(p for p in policies if p['name'] == 'lessons_teacher_insert')
        assert teacher_policy['policy_type'] == 'INSERT'
        assert 'user_profiles' in teacher_policy['using_clause']
        assert 'teacher' in teacher_policy['using_clause']

    def test_generate_admin_policies(self):
        """Test admin table policy generation."""
        tool = RLSPolicyGeneratorTool()

        policies = tool._generate_admin_policies('admin_settings')

        assert len(policies) == 2

        # Check policy names
        policy_names = [p['name'] for p in policies]
        assert 'admin_settings_admin_only' in policy_names
        assert 'admin_settings_service_role' in policy_names

        # Check admin only policy
        admin_only = next(p for p in policies if p['name'] == 'admin_settings_admin_only')
        assert admin_only['policy_type'] == 'ALL'
        assert 'authenticated' in admin_only['roles']
        assert 'role = \'admin\'' in admin_only['using_clause']

        # Check service role policy
        service_policy = next(p for p in policies if p['name'] == 'admin_settings_service_role')
        assert service_policy['policy_type'] == 'ALL'
        assert 'service_role' in service_policy['roles']
        assert service_policy['using_clause'] == 'true'

    def test_generate_default_policies(self):
        """Test default table policy generation."""
        tool = RLSPolicyGeneratorTool()

        policies = tool._generate_default_policies('posts')

        assert len(policies) == 2

        # Check policy names
        policy_names = [p['name'] for p in policies]
        assert 'posts_authenticated_read' in policy_names
        assert 'posts_service_full' in policy_names

        # Check authenticated read policy
        auth_read = next(p for p in policies if p['name'] == 'posts_authenticated_read')
        assert auth_read['policy_type'] == 'SELECT'
        assert 'authenticated' in auth_read['roles']
        assert auth_read['using_clause'] == 'true'

    def test_generate_multi_tenant_policy(self):
        """Test multi-tenant policy generation."""
        tool = RLSPolicyGeneratorTool()

        policy = tool._generate_multi_tenant_policy('lessons')

        assert policy['name'] == 'lessons_tenant_isolation'
        assert policy['policy_type'] == 'ALL'
        assert 'authenticated' in policy['roles']
        assert 'organization_id' in policy['using_clause']
        assert 'user_profiles' in policy['using_clause']

    def test_generate_hierarchical_policy(self):
        """Test hierarchical policy generation."""
        tool = RLSPolicyGeneratorTool()

        policy = tool._generate_hierarchical_policy('posts')

        assert policy['name'] == 'posts_hierarchical'
        assert policy['policy_type'] == 'SELECT'
        assert 'authenticated' in policy['roles']
        assert 'department_id' in policy['using_clause']
        assert 'user_departments' in policy['using_clause']

    def test_generate_time_based_policy(self):
        """Test time-based policy generation."""
        tool = RLSPolicyGeneratorTool()

        policy = tool._generate_time_based_policy('lessons')

        assert policy['name'] == 'lessons_time_based'
        assert policy['policy_type'] == 'SELECT'
        assert 'authenticated' in policy['roles']
        assert 'published_at' in policy['using_clause']
        assert 'expires_at' in policy['using_clause']
        assert 'NOW()' in policy['using_clause']

    def test_analyze_access_patterns(self, sample_access_patterns):
        """Test access pattern analysis."""
        tool = RLSPolicyGeneratorTool()

        # Test lessons table with multiple patterns
        lessons_policies = tool._analyze_access_patterns('lessons', sample_access_patterns)
        assert len(lessons_policies) == 2  # multi_tenant and time_based

        policy_names = [p['name'] for p in lessons_policies]
        assert 'lessons_tenant_isolation' in policy_names
        assert 'lessons_time_based' in policy_names

        # Test posts table with hierarchical pattern
        posts_policies = tool._analyze_access_patterns('posts', sample_access_patterns)
        assert len(posts_policies) == 1  # hierarchical only

        assert posts_policies[0]['name'] == 'posts_hierarchical'

        # Test table not in patterns
        empty_policies = tool._analyze_access_patterns('unknown_table', sample_access_patterns)
        assert len(empty_policies) == 0

    def test_dict_to_policy(self):
        """Test conversion from dictionary to RLSPolicy object."""
        tool = RLSPolicyGeneratorTool()

        policy_dict = {
            'name': 'test_policy',
            'table': 'test_table',
            'policy_type': 'SELECT',
            'roles': ['authenticated'],
            'using_clause': 'auth.uid() = user_id',
            'check_clause': 'auth.uid() = user_id',
            'description': 'Test policy'
        }

        policy = tool._dict_to_policy(policy_dict)

        assert isinstance(policy, RLSPolicy)
        assert policy.name == 'test_policy'
        assert policy.table == 'test_table'
        assert policy.policy_type == PolicyType.SELECT
        assert policy.roles == ['authenticated']
        assert policy.using_clause == 'auth.uid() = user_id'
        assert policy.check_clause == 'auth.uid() = user_id'
        assert policy.description == 'Test policy'

    def test_generate_sql(self):
        """Test SQL generation for policies."""
        tool = RLSPolicyGeneratorTool()

        policies = [
            {
                'name': 'users_select_own',
                'table': 'users',
                'policy_type': 'SELECT',
                'roles': ['authenticated'],
                'using_clause': 'auth.uid() = user_id',
                'description': 'Users can view their own data'
            },
            {
                'name': 'users_update_own',
                'table': 'users',
                'policy_type': 'UPDATE',
                'roles': ['authenticated'],
                'using_clause': 'auth.uid() = user_id',
                'check_clause': 'auth.uid() = user_id',
                'description': 'Users can update their own data'
            }
        ]

        sql = tool.generate_sql(policies)

        # Check that SQL contains expected elements
        assert 'ALTER TABLE users ENABLE ROW LEVEL SECURITY' in sql
        assert 'CREATE POLICY users_select_own' in sql
        assert 'CREATE POLICY users_update_own' in sql
        assert 'FOR SELECT' in sql
        assert 'FOR UPDATE' in sql
        assert 'TO authenticated' in sql
        assert 'USING (auth.uid() = user_id)' in sql
        assert 'WITH CHECK (auth.uid() = user_id)' in sql

        # Check that policies are separated
        assert sql.count('CREATE POLICY') == 2
        assert sql.count('ALTER TABLE') == 2  # Once per table per policy

    def test_validate_policies_valid(self, sample_schema):
        """Test policy validation with valid policies."""
        tool = RLSPolicyGeneratorTool()

        valid_policies = [
            {
                'name': 'users_select',
                'table': 'users',
                'policy_type': 'SELECT',
                'roles': ['authenticated'],
                'using_clause': 'auth.uid() = user_id'
            },
            {
                'name': 'lessons_public',
                'table': 'lessons',
                'policy_type': 'SELECT',
                'roles': ['anon', 'authenticated'],
                'using_clause': 'status = \'published\''
            }
        ]

        results = tool.validate_policies(valid_policies, sample_schema)

        assert len(results) == 2
        for result in results:
            assert result['valid'] is True
            assert len(result['issues']) == 0

    def test_validate_policies_invalid_table(self, sample_schema):
        """Test policy validation with invalid table."""
        tool = RLSPolicyGeneratorTool()

        invalid_policies = [
            {
                'name': 'nonexistent_select',
                'table': 'nonexistent_table',
                'policy_type': 'SELECT',
                'roles': ['authenticated'],
                'using_clause': 'true'
            }
        ]

        results = tool.validate_policies(invalid_policies, sample_schema)

        assert len(results) == 1
        assert results[0]['valid'] is False
        assert 'nonexistent_table' in results[0]['issues'][0]

    def test_validate_policies_missing_using_clause(self, sample_schema):
        """Test policy validation with missing using clause."""
        tool = RLSPolicyGeneratorTool()

        invalid_policies = [
            {
                'name': 'users_select',
                'table': 'users',
                'policy_type': 'SELECT',
                'roles': ['authenticated']
                # Missing using_clause
            }
        ]

        results = tool.validate_policies(invalid_policies, sample_schema)

        assert len(results) == 1
        assert results[0]['valid'] is False
        assert 'Missing USING clause' in results[0]['issues'][0]

    def test_validate_policies_invalid_role(self, sample_schema):
        """Test policy validation with invalid role."""
        tool = RLSPolicyGeneratorTool()

        invalid_policies = [
            {
                'name': 'users_select',
                'table': 'users',
                'policy_type': 'SELECT',
                'roles': ['invalid_role'],
                'using_clause': 'true'
            }
        ]

        results = tool.validate_policies(invalid_policies, sample_schema)

        assert len(results) == 1
        assert results[0]['valid'] is False
        assert 'Invalid role \'invalid_role\'' in results[0]['issues'][0]

    def test_validate_policies_multiple_issues(self, sample_schema):
        """Test policy validation with multiple issues."""
        tool = RLSPolicyGeneratorTool()

        invalid_policies = [
            {
                'name': 'bad_policy',
                'table': 'nonexistent_table',
                'policy_type': 'SELECT',
                'roles': ['invalid_role', 'another_invalid_role']
                # Missing using_clause
            }
        ]

        results = tool.validate_policies(invalid_policies, sample_schema)

        assert len(results) == 1
        assert results[0]['valid'] is False
        assert len(results[0]['issues']) == 4  # table, using clause, 2 roles

    @pytest.mark.asyncio
    async def test_generate_table_policies_user_table(self):
        """Test policy generation for user table."""
        tool = RLSPolicyGeneratorTool()

        table_info = {'name': 'users', 'columns': []}
        policies = await tool._generate_table_policies('users', table_info, None)

        assert len(policies) == 3  # user policies
        policy_names = [p['name'] for p in policies]
        assert 'users_select_own' in policy_names
        assert 'users_update_own' in policy_names
        assert 'users_admin_all' in policy_names

    @pytest.mark.asyncio
    async def test_generate_table_policies_content_table(self):
        """Test policy generation for content table."""
        tool = RLSPolicyGeneratorTool()

        table_info = {'name': 'lessons', 'columns': []}
        policies = await tool._generate_table_policies('lessons', table_info, None)

        assert len(policies) == 4  # content policies
        policy_names = [p['name'] for p in policies]
        assert 'lessons_public_select' in policy_names
        assert 'lessons_teacher_insert' in policy_names
        assert 'lessons_creator_update' in policy_names
        assert 'lessons_student_enrolled' in policy_names

    @pytest.mark.asyncio
    async def test_generate_table_policies_with_access_patterns(self, sample_access_patterns):
        """Test policy generation with access patterns."""
        tool = RLSPolicyGeneratorTool()

        table_info = {'name': 'lessons', 'columns': []}
        policies = await tool._generate_table_policies(
            'lessons',
            table_info,
            sample_access_patterns
        )

        # Should have content policies + access pattern policies
        assert len(policies) > 4
        policy_names = [p['name'] for p in policies]
        assert 'lessons_tenant_isolation' in policy_names
        assert 'lessons_time_based' in policy_names

    def test_load_policy_templates(self):
        """Test policy template loading."""
        tool = RLSPolicyGeneratorTool()

        templates = tool._load_policy_templates()

        assert isinstance(templates, dict)
        assert len(templates) > 0

        # Check expected templates
        expected_templates = [
            'owner_only', 'public_read', 'authenticated_only',
            'admin_only', 'same_organization', 'created_by',
            'team_members'
        ]

        for template in expected_templates:
            assert template in templates
            assert isinstance(templates[template], str)
            assert len(templates[template]) > 0

        # Check template content
        assert 'auth.uid()' in templates['owner_only']
        assert 'true' == templates['public_read']
        assert 'authenticated' in templates['authenticated_only']
        assert 'admin' in templates['admin_only']


class TestRLSPolicy:
    """Test cases for RLSPolicy dataclass."""

    def test_rls_policy_creation(self):
        """Test RLSPolicy creation."""
        policy = RLSPolicy(
            name='test_policy',
            table='test_table',
            policy_type=PolicyType.SELECT,
            roles=['authenticated'],
            using_clause='auth.uid() = user_id',
            check_clause='auth.uid() = user_id',
            description='Test policy description'
        )

        assert policy.name == 'test_policy'
        assert policy.table == 'test_table'
        assert policy.policy_type == PolicyType.SELECT
        assert policy.roles == ['authenticated']
        assert policy.using_clause == 'auth.uid() = user_id'
        assert policy.check_clause == 'auth.uid() = user_id'
        assert policy.description == 'Test policy description'

    def test_rls_policy_without_optional_fields(self):
        """Test RLSPolicy creation without optional fields."""
        policy = RLSPolicy(
            name='minimal_policy',
            table='test_table',
            policy_type=PolicyType.INSERT,
            roles=['authenticated'],
            using_clause='true'
        )

        assert policy.name == 'minimal_policy'
        assert policy.policy_type == PolicyType.INSERT
        assert policy.check_clause is None
        assert policy.description is None


class TestPolicyType:
    """Test cases for PolicyType enum."""

    def test_policy_type_values(self):
        """Test PolicyType enum values."""
        assert PolicyType.SELECT.value == "SELECT"
        assert PolicyType.INSERT.value == "INSERT"
        assert PolicyType.UPDATE.value == "UPDATE"
        assert PolicyType.DELETE.value == "DELETE"
        assert PolicyType.ALL.value == "ALL"

    def test_policy_type_from_string(self):
        """Test PolicyType creation from string."""
        assert PolicyType['SELECT'] == PolicyType.SELECT
        assert PolicyType['INSERT'] == PolicyType.INSERT
        assert PolicyType['UPDATE'] == PolicyType.UPDATE
        assert PolicyType['DELETE'] == PolicyType.DELETE
        assert PolicyType['ALL'] == PolicyType.ALL
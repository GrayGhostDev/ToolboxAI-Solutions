"""RLS (Row Level Security) policy generator for Supabase migration."""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PolicyType(Enum):
    """Types of RLS policies."""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    ALL = "ALL"


@dataclass
class RLSPolicy:
    """Represents a Row Level Security policy."""
    name: str
    table: str
    policy_type: PolicyType
    roles: List[str]
    using_clause: str
    check_clause: Optional[str] = None
    description: Optional[str] = None


class RLSPolicyGeneratorTool:
    """
    Tool for generating Row Level Security policies for Supabase.

    Analyzes existing access patterns and generates appropriate RLS policies
    to maintain security while migrating to Supabase.
    """

    def __init__(self):
        """Initialize the RLS policy generator."""
        self.policy_templates = self._load_policy_templates()
        self.generated_policies: List[RLSPolicy] = []

    async def generate_policies(
        self,
        schema: Dict[str, Any],
        access_patterns: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate RLS policies based on schema and access patterns.

        Args:
            schema: Database schema information
            access_patterns: Optional access pattern analysis

        Returns:
            List of RLS policy definitions
        """
        logger.info("Generating RLS policies")

        policies = []

        for table in schema.get('tables', []):
            table_name = table['name']
            table_policies = await self._generate_table_policies(
                table_name,
                table,
                access_patterns
            )
            policies.extend(table_policies)

        # Store generated policies
        self.generated_policies = [
            self._dict_to_policy(p) for p in policies
        ]

        return policies

    async def _generate_table_policies(
        self,
        table_name: str,
        table_info: Dict[str, Any],
        access_patterns: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate policies for a specific table."""
        policies = []

        # Determine table type and generate appropriate policies
        if self._is_user_table(table_name, table_info):
            policies.extend(self._generate_user_policies(table_name))
        elif self._is_content_table(table_name, table_info):
            policies.extend(self._generate_content_policies(table_name))
        elif self._is_admin_table(table_name, table_info):
            policies.extend(self._generate_admin_policies(table_name))
        else:
            # Generate default policies
            policies.extend(self._generate_default_policies(table_name))

        # Add custom policies based on access patterns
        if access_patterns:
            custom_policies = self._analyze_access_patterns(
                table_name,
                access_patterns
            )
            policies.extend(custom_policies)

        return policies

    def _is_user_table(self, table_name: str, table_info: Dict[str, Any]) -> bool:
        """Check if table is user-related."""
        user_indicators = ['user', 'profile', 'account', 'member']
        return any(indicator in table_name.lower() for indicator in user_indicators)

    def _is_content_table(self, table_name: str, table_info: Dict[str, Any]) -> bool:
        """Check if table is content-related."""
        content_indicators = ['content', 'lesson', 'quiz', 'assessment', 'course']
        return any(indicator in table_name.lower() for indicator in content_indicators)

    def _is_admin_table(self, table_name: str, table_info: Dict[str, Any]) -> bool:
        """Check if table is admin-related."""
        admin_indicators = ['admin', 'system', 'config', 'audit']
        return any(indicator in table_name.lower() for indicator in admin_indicators)

    def _generate_user_policies(self, table_name: str) -> List[Dict[str, Any]]:
        """Generate policies for user-related tables."""
        policies = []

        # Users can view their own data
        policies.append({
            'name': f'{table_name}_select_own',
            'table': table_name,
            'policy_type': 'SELECT',
            'roles': ['authenticated'],
            'using_clause': f'auth.uid() = user_id',
            'description': 'Users can view their own data'
        })

        # Users can update their own data
        policies.append({
            'name': f'{table_name}_update_own',
            'table': table_name,
            'policy_type': 'UPDATE',
            'roles': ['authenticated'],
            'using_clause': f'auth.uid() = user_id',
            'check_clause': f'auth.uid() = user_id',
            'description': 'Users can update their own data'
        })

        # Admins can view all data
        policies.append({
            'name': f'{table_name}_admin_all',
            'table': table_name,
            'policy_type': 'ALL',
            'roles': ['service_role'],
            'using_clause': 'true',
            'description': 'Admins have full access'
        })

        return policies

    def _generate_content_policies(self, table_name: str) -> List[Dict[str, Any]]:
        """Generate policies for content-related tables."""
        policies = []

        # Public content is viewable by all
        policies.append({
            'name': f'{table_name}_public_select',
            'table': table_name,
            'policy_type': 'SELECT',
            'roles': ['anon', 'authenticated'],
            'using_clause': "status = 'published' OR status = 'approved'",
            'description': 'Public content is viewable by all'
        })

        # Teachers can create content
        policies.append({
            'name': f'{table_name}_teacher_insert',
            'table': table_name,
            'policy_type': 'INSERT',
            'roles': ['authenticated'],
            'using_clause': """
                EXISTS (
                    SELECT 1 FROM user_profiles
                    WHERE user_id = auth.uid()
                    AND role IN ('teacher', 'admin')
                )
            """,
            'description': 'Teachers can create content'
        })

        # Content creators can update their own content
        policies.append({
            'name': f'{table_name}_creator_update',
            'table': table_name,
            'policy_type': 'UPDATE',
            'roles': ['authenticated'],
            'using_clause': 'created_by = auth.uid()',
            'check_clause': 'created_by = auth.uid()',
            'description': 'Creators can update their own content'
        })

        # Students can view enrolled content
        policies.append({
            'name': f'{table_name}_student_enrolled',
            'table': table_name,
            'policy_type': 'SELECT',
            'roles': ['authenticated'],
            'using_clause': """
                EXISTS (
                    SELECT 1 FROM enrollments e
                    JOIN classes c ON e.class_id = c.id
                    JOIN class_content cc ON c.id = cc.class_id
                    WHERE e.student_id = auth.uid()
                    AND cc.content_id = {table_name}.id
                )
            """,
            'description': 'Students can view enrolled content'
        })

        return policies

    def _generate_admin_policies(self, table_name: str) -> List[Dict[str, Any]]:
        """Generate policies for admin-related tables."""
        policies = []

        # Only admins can access admin tables
        policies.append({
            'name': f'{table_name}_admin_only',
            'table': table_name,
            'policy_type': 'ALL',
            'roles': ['authenticated'],
            'using_clause': """
                EXISTS (
                    SELECT 1 FROM user_profiles
                    WHERE user_id = auth.uid()
                    AND role = 'admin'
                )
            """,
            'description': 'Only admins can access admin tables'
        })

        # Service role has unrestricted access
        policies.append({
            'name': f'{table_name}_service_role',
            'table': table_name,
            'policy_type': 'ALL',
            'roles': ['service_role'],
            'using_clause': 'true',
            'description': 'Service role has full access'
        })

        return policies

    def _generate_default_policies(self, table_name: str) -> List[Dict[str, Any]]:
        """Generate default policies for unclassified tables."""
        policies = []

        # Authenticated users can read
        policies.append({
            'name': f'{table_name}_authenticated_read',
            'table': table_name,
            'policy_type': 'SELECT',
            'roles': ['authenticated'],
            'using_clause': 'true',
            'description': 'Authenticated users can read'
        })

        # Service role can do everything
        policies.append({
            'name': f'{table_name}_service_full',
            'table': table_name,
            'policy_type': 'ALL',
            'roles': ['service_role'],
            'using_clause': 'true',
            'description': 'Service role has full access'
        })

        return policies

    def _analyze_access_patterns(
        self,
        table_name: str,
        access_patterns: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate policies based on access pattern analysis."""
        policies = []

        # Analyze patterns for this table
        table_patterns = access_patterns.get(table_name, {})

        # Generate policies based on patterns
        if table_patterns.get('multi_tenant'):
            policies.append(self._generate_multi_tenant_policy(table_name))

        if table_patterns.get('hierarchical'):
            policies.append(self._generate_hierarchical_policy(table_name))

        if table_patterns.get('time_based'):
            policies.append(self._generate_time_based_policy(table_name))

        return policies

    def _generate_multi_tenant_policy(self, table_name: str) -> Dict[str, Any]:
        """Generate multi-tenant isolation policy."""
        return {
            'name': f'{table_name}_tenant_isolation',
            'table': table_name,
            'policy_type': 'ALL',
            'roles': ['authenticated'],
            'using_clause': """
                organization_id = (
                    SELECT organization_id FROM user_profiles
                    WHERE user_id = auth.uid()
                )
            """,
            'description': 'Multi-tenant isolation'
        }

    def _generate_hierarchical_policy(self, table_name: str) -> Dict[str, Any]:
        """Generate hierarchical access policy."""
        return {
            'name': f'{table_name}_hierarchical',
            'table': table_name,
            'policy_type': 'SELECT',
            'roles': ['authenticated'],
            'using_clause': """
                department_id IN (
                    SELECT department_id FROM user_departments
                    WHERE user_id = auth.uid()
                    OR parent_department_id IN (
                        SELECT department_id FROM user_departments
                        WHERE user_id = auth.uid()
                    )
                )
            """,
            'description': 'Hierarchical department access'
        }

    def _generate_time_based_policy(self, table_name: str) -> Dict[str, Any]:
        """Generate time-based access policy."""
        return {
            'name': f'{table_name}_time_based',
            'table': table_name,
            'policy_type': 'SELECT',
            'roles': ['authenticated'],
            'using_clause': """
                (
                    published_at IS NULL OR
                    published_at <= NOW()
                ) AND (
                    expires_at IS NULL OR
                    expires_at >= NOW()
                )
            """,
            'description': 'Time-based content access'
        }

    def _load_policy_templates(self) -> Dict[str, str]:
        """Load common policy templates."""
        return {
            'owner_only': 'auth.uid() = user_id',
            'public_read': 'true',
            'authenticated_only': 'auth.role() = \'authenticated\'',
            'admin_only': 'auth.jwt() ->> \'role\' = \'admin\'',
            'same_organization': 'org_id = auth.jwt() ->> \'org_id\'',
            'created_by': 'created_by = auth.uid()',
            'team_members': """
                team_id IN (
                    SELECT team_id FROM team_members
                    WHERE user_id = auth.uid()
                )
            """
        }

    def _dict_to_policy(self, policy_dict: Dict[str, Any]) -> RLSPolicy:
        """Convert dictionary to RLSPolicy object."""
        return RLSPolicy(
            name=policy_dict['name'],
            table=policy_dict['table'],
            policy_type=PolicyType[policy_dict['policy_type']],
            roles=policy_dict['roles'],
            using_clause=policy_dict['using_clause'],
            check_clause=policy_dict.get('check_clause'),
            description=policy_dict.get('description')
        )

    def generate_sql(self, policies: List[Dict[str, Any]]) -> str:
        """
        Generate SQL statements for RLS policies.

        Args:
            policies: List of policy definitions

        Returns:
            SQL statements as string
        """
        sql_statements = []

        for policy in policies:
            # Enable RLS on table
            sql_statements.append(
                f"ALTER TABLE {policy['table']} ENABLE ROW LEVEL SECURITY;"
            )

            # Create policy
            sql = f"CREATE POLICY {policy['name']}\n"
            sql += f"  ON {policy['table']}\n"
            sql += f"  FOR {policy['policy_type']}\n"
            sql += f"  TO {', '.join(policy['roles'])}\n"
            sql += f"  USING ({policy['using_clause']})"

            if policy.get('check_clause'):
                sql += f"\n  WITH CHECK ({policy['check_clause']})"

            sql += ";"

            sql_statements.append(sql)

        return "\n\n".join(sql_statements)

    def validate_policies(
        self,
        policies: List[Dict[str, Any]],
        schema: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Validate generated policies against schema.

        Args:
            policies: List of policies to validate
            schema: Database schema

        Returns:
            Validation results
        """
        validation_results = []

        # Get list of valid tables
        valid_tables = {table['name'] for table in schema.get('tables', [])}

        for policy in policies:
            result = {
                'policy': policy['name'],
                'valid': True,
                'issues': []
            }

            # Check if table exists
            if policy['table'] not in valid_tables:
                result['valid'] = False
                result['issues'].append(f"Table '{policy['table']}' not found in schema")

            # Validate using clause
            if not policy.get('using_clause'):
                result['valid'] = False
                result['issues'].append("Missing USING clause")

            # Validate roles
            valid_roles = ['anon', 'authenticated', 'service_role']
            for role in policy.get('roles', []):
                if role not in valid_roles:
                    result['valid'] = False
                    result['issues'].append(f"Invalid role '{role}'")

            validation_results.append(result)

        return validation_results
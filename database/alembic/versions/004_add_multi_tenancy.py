"""
Add multi-tenancy support with organizations and tenant isolation

Revision ID: 004_add_multi_tenancy
Revises: 003_add_agent_system_tables
Create Date: 2025-01-15 10:00:00.000000

This migration adds:
1. Organizations table for tenant management
2. Organization invitations and usage tracking
3. Tenant ID (organization_id) to all relevant tables
4. Row Level Security (RLS) policies for tenant isolation
5. Indexes for performance
6. Default organization for existing data
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text
import uuid


# revision identifiers
revision = '004_add_multi_tenancy'
down_revision = '003_performance_monitoring'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add multi-tenancy support"""

    # Create enum types
    op.execute("CREATE TYPE organizationstatus AS ENUM ('active', 'suspended', 'trial', 'pending', 'cancelled')")
    op.execute("CREATE TYPE subscriptiontier AS ENUM ('free', 'basic', 'professional', 'enterprise', 'education')")

    # 1. Create organizations table
    op.create_table('organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False, unique=True),
        sa.Column('display_name', sa.String(250)),
        sa.Column('description', sa.Text()),
        sa.Column('website', sa.String(500)),
        sa.Column('email', sa.String(255)),
        sa.Column('phone', sa.String(50)),
        sa.Column('address', postgresql.JSONB(), default={}),
        sa.Column('timezone', sa.String(100), default='UTC'),
        sa.Column('locale', sa.String(10), default='en-US'),
        sa.Column('organization_type', sa.String(50), default='education'),
        sa.Column('industry', sa.String(100)),
        sa.Column('size_category', sa.String(50)),
        sa.Column('subscription_tier', sa.Enum('free', 'basic', 'professional', 'enterprise', 'education', name='subscriptiontier'), default='free', nullable=False),
        sa.Column('status', sa.Enum('active', 'suspended', 'trial', 'pending', 'cancelled', name='organizationstatus'), default='trial', nullable=False),
        sa.Column('billing_email', sa.String(255)),
        sa.Column('billing_address', postgresql.JSONB(), default={}),
        sa.Column('tax_id', sa.String(100)),
        sa.Column('trial_started_at', sa.DateTime(timezone=True)),
        sa.Column('trial_expires_at', sa.DateTime(timezone=True)),
        sa.Column('subscription_started_at', sa.DateTime(timezone=True)),
        sa.Column('subscription_expires_at', sa.DateTime(timezone=True)),
        sa.Column('last_billing_date', sa.DateTime(timezone=True)),
        sa.Column('next_billing_date', sa.DateTime(timezone=True)),
        sa.Column('max_users', sa.Integer(), default=10),
        sa.Column('max_classes', sa.Integer(), default=5),
        sa.Column('max_storage_gb', sa.Float(), default=1.0),
        sa.Column('max_api_calls_per_month', sa.Integer(), default=1000),
        sa.Column('max_roblox_sessions', sa.Integer(), default=5),
        sa.Column('current_users', sa.Integer(), default=0),
        sa.Column('current_classes', sa.Integer(), default=0),
        sa.Column('current_storage_gb', sa.Float(), default=0.0),
        sa.Column('current_api_calls_this_month', sa.Integer(), default=0),
        sa.Column('current_roblox_sessions', sa.Integer(), default=0),
        sa.Column('settings', postgresql.JSONB(), default={}),
        sa.Column('features', postgresql.JSONB(), default=[]),
        sa.Column('integrations', postgresql.JSONB(), default={}),
        sa.Column('sso_enabled', sa.Boolean(), default=False),
        sa.Column('sso_configuration', postgresql.JSONB(), default={}),
        sa.Column('data_retention_days', sa.Integer(), default=365),
        sa.Column('audit_logs_enabled', sa.Boolean(), default=True),
        sa.Column('coppa_compliance_required', sa.Boolean(), default=True),
        sa.Column('ferpa_compliance_required', sa.Boolean(), default=False),
        sa.Column('logo_url', sa.String(500)),
        sa.Column('primary_color', sa.String(7)),
        sa.Column('secondary_color', sa.String(7)),
        sa.Column('custom_domain', sa.String(255)),
        sa.Column('custom_css', sa.Text()),
        sa.Column('api_key', sa.String(255), unique=True),
        sa.Column('webhook_url', sa.String(500)),
        sa.Column('webhook_secret', sa.String(255)),
        sa.Column('rate_limit_per_minute', sa.Integer(), default=100),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('is_demo', sa.Boolean(), default=False),
        sa.Column('maintenance_mode', sa.Boolean(), default=False),
        sa.Column('emergency_contact_email', sa.String(255)),
        sa.Column('admin_notes', sa.Text()),
        sa.Column('support_level', sa.String(50), default='standard'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True)),
        sa.Column('updated_by_id', postgresql.UUID(as_uuid=True)),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
        sa.Column('deleted_by_id', postgresql.UUID(as_uuid=True)),

        # Constraints
        sa.CheckConstraint('max_users > 0', name='check_max_users_positive'),
        sa.CheckConstraint('max_classes >= 0', name='check_max_classes_non_negative'),
        sa.CheckConstraint('max_storage_gb >= 0', name='check_max_storage_non_negative'),
        sa.CheckConstraint('current_users >= 0', name='check_current_users_non_negative'),
        sa.CheckConstraint('current_classes >= 0', name='check_current_classes_non_negative'),
        sa.CheckConstraint('current_storage_gb >= 0', name='check_current_storage_non_negative'),
        sa.CheckConstraint('data_retention_days > 0', name='check_retention_days_positive'),
        sa.CheckConstraint('rate_limit_per_minute > 0', name='check_rate_limit_positive'),
    )

    # Create indexes for organizations
    op.create_index('idx_organization_slug', 'organizations', ['slug'])
    op.create_index('idx_organization_status', 'organizations', ['status'])
    op.create_index('idx_organization_subscription', 'organizations', ['subscription_tier'])
    op.create_index('idx_organization_active', 'organizations', ['is_active'])
    op.create_index('idx_organization_trial_expires', 'organizations', ['trial_expires_at'])
    op.create_index('idx_organization_subscription_expires', 'organizations', ['subscription_expires_at'])
    op.create_index('idx_organization_created', 'organizations', ['created_at'])

    # 2. Create organization_invitations table
    op.create_table('organization_invitations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), default='member'),
        sa.Column('invited_by_id', postgresql.UUID(as_uuid=True)),
        sa.Column('invitation_token', sa.String(255), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=True)),
        sa.Column('accepted_by_id', postgresql.UUID(as_uuid=True)),
        sa.Column('declined_at', sa.DateTime(timezone=True)),
        sa.Column('cancelled_at', sa.DateTime(timezone=True)),
        sa.Column('cancelled_by_id', postgresql.UUID(as_uuid=True)),
        sa.Column('invitation_message', sa.Text()),
        sa.Column('permissions', postgresql.JSONB(), default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    )

    # Create indexes for organization_invitations
    op.create_index('idx_org_invitation_token', 'organization_invitations', ['invitation_token'])
    op.create_index('idx_org_invitation_email', 'organization_invitations', ['email'])
    op.create_index('idx_org_invitation_organization', 'organization_invitations', ['organization_id'])
    op.create_index('idx_org_invitation_expires', 'organization_invitations', ['expires_at'])
    op.create_index('idx_org_invitation_status', 'organization_invitations', ['accepted_at', 'declined_at', 'cancelled_at'])

    # 3. Create organization_usage_logs table
    op.create_table('organization_usage_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('users_count', sa.Integer(), default=0),
        sa.Column('classes_count', sa.Integer(), default=0),
        sa.Column('storage_gb', sa.Float(), default=0.0),
        sa.Column('api_calls_count', sa.Integer(), default=0),
        sa.Column('roblox_sessions_count', sa.Integer(), default=0),
        sa.Column('active_users_count', sa.Integer(), default=0),
        sa.Column('content_generated_count', sa.Integer(), default=0),
        sa.Column('quizzes_completed_count', sa.Integer(), default=0),
        sa.Column('log_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('log_type', sa.String(20), default='daily'),
        sa.Column('billing_period_start', sa.DateTime(timezone=True)),
        sa.Column('billing_period_end', sa.DateTime(timezone=True)),
        sa.Column('usage_data', postgresql.JSONB(), default={}),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    )

    # Create indexes for organization_usage_logs
    op.create_index('idx_org_usage_organization_date', 'organization_usage_logs', ['organization_id', 'log_date'])
    op.create_index('idx_org_usage_type_date', 'organization_usage_logs', ['log_type', 'log_date'])
    op.create_index('idx_org_usage_billing_period', 'organization_usage_logs', ['billing_period_start', 'billing_period_end'])

    # 4. Create default organization for existing data
    default_org_id = str(uuid.uuid4())
    op.execute(f"""
        INSERT INTO organizations (id, name, slug, display_name, status, subscription_tier, is_active, is_verified)
        VALUES ('{default_org_id}', 'Default Organization', 'default-org', 'Default Organization', 'active', 'enterprise', true, true)
    """)

    # 5. Add organization_id to all relevant tables

    # Tables to add tenant isolation to
    tenant_tables = [
        'users',
        'courses',
        'lessons',
        'content',
        'quizzes',
        'quiz_questions',
        'quiz_attempts',
        'quiz_responses',
        'user_progress',
        'analytics',
        'achievements',
        'user_achievements',
        'leaderboard',
        'enrollments',
        'sessions',
        'roblox_sessions',
        'roblox_content',
        'roblox_player_progress',
        'roblox_quiz_results',
        'roblox_achievements',
        'roblox_templates',
        'student_progress',
        'classes',
        'class_enrollments',
        'plugin_requests',
        'roblox_deployments',
        'terrain_templates',
        'quiz_templates',
        'enhanced_content_generations',
        'content_generation_batches'
    ]

    # Add organization_id column to each table
    for table_name in tenant_tables:
        # Check if table exists before adding column
        op.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '{table_name}') THEN
                    -- Add organization_id column
                    ALTER TABLE {table_name} ADD COLUMN organization_id UUID;

                    -- Set default organization for existing records
                    UPDATE {table_name} SET organization_id = '{default_org_id}' WHERE organization_id IS NULL;

                    -- Make column not null after setting default values
                    ALTER TABLE {table_name} ALTER COLUMN organization_id SET NOT NULL;

                    -- Add foreign key constraint
                    ALTER TABLE {table_name} ADD CONSTRAINT fk_{table_name}_organization_id
                        FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE;

                    -- Add index for performance
                    CREATE INDEX IF NOT EXISTS idx_{table_name}_organization_id ON {table_name}(organization_id);
                END IF;
            END $$;
        """)

    # 6. Enable Row Level Security (RLS) on tenant tables
    for table_name in tenant_tables:
        op.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '{table_name}') THEN
                    ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;
                END IF;
            END $$;
        """)

    # 7. Create RLS policies for tenant isolation
    # Note: Actual policies will be created in a separate SQL file
    # for better maintainability

    print("Multi-tenancy migration completed successfully!")
    print("Next steps:")
    print("1. Apply RLS policies using database/policies/tenant_policies.sql")
    print("2. Update application code to set tenant context")
    print("3. Test tenant isolation")


def downgrade() -> None:
    """Remove multi-tenancy support"""

    # List of tables that had organization_id added
    tenant_tables = [
        'users', 'courses', 'lessons', 'content', 'quizzes', 'quiz_questions',
        'quiz_attempts', 'quiz_responses', 'user_progress', 'analytics',
        'achievements', 'user_achievements', 'leaderboard', 'enrollments',
        'sessions', 'roblox_sessions', 'roblox_content', 'roblox_player_progress',
        'roblox_quiz_results', 'roblox_achievements', 'roblox_templates',
        'student_progress', 'classes', 'class_enrollments', 'plugin_requests',
        'roblox_deployments', 'terrain_templates', 'quiz_templates',
        'enhanced_content_generations', 'content_generation_batches'
    ]

    # Disable RLS and remove organization_id columns
    for table_name in tenant_tables:
        op.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '{table_name}') THEN
                    -- Disable RLS
                    ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY;

                    -- Drop RLS policies if they exist
                    DROP POLICY IF EXISTS {table_name}_tenant_isolation_policy ON {table_name};
                    DROP POLICY IF EXISTS {table_name}_tenant_select_policy ON {table_name};
                    DROP POLICY IF EXISTS {table_name}_tenant_insert_policy ON {table_name};
                    DROP POLICY IF EXISTS {table_name}_tenant_update_policy ON {table_name};
                    DROP POLICY IF EXISTS {table_name}_tenant_delete_policy ON {table_name};

                    -- Drop index
                    DROP INDEX IF EXISTS idx_{table_name}_organization_id;

                    -- Drop foreign key constraint
                    ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS fk_{table_name}_organization_id;

                    -- Drop organization_id column
                    ALTER TABLE {table_name} DROP COLUMN IF EXISTS organization_id;
                END IF;
            END $$;
        """)

    # Drop usage logs table
    op.drop_table('organization_usage_logs')

    # Drop invitations table
    op.drop_table('organization_invitations')

    # Drop organizations table
    op.drop_table('organizations')

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS organizationstatus")
    op.execute("DROP TYPE IF EXISTS subscriptiontier")

    print("Multi-tenancy migration rolled back successfully!")
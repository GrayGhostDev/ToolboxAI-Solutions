-- ===============================================================
-- PostgreSQL Row Level Security (RLS) Policies for Multi-Tenancy
-- ===============================================================
--
-- This file contains RLS policies to enforce tenant isolation
-- in the ToolBoxAI Educational Platform. These policies ensure
-- that users can only access data belonging to their organization.
--
-- Prerequisites:
-- 1. Multi-tenancy migration (004_add_multi_tenancy) must be applied
-- 2. All tenant tables must have organization_id column
-- 3. RLS must be enabled on all tenant tables
--
-- Security Model:
-- - Each session must set current_setting('app.current_organization_id')
-- - All tenant-scoped queries are automatically filtered by organization_id
-- - Super users can bypass RLS for administrative tasks
-- - Service accounts need special privileges for cross-tenant operations
--
-- Usage:
-- Apply these policies by running:
-- psql -d your_database -f database/policies/tenant_policies.sql

-- ===============================================================
-- 1. Utility Functions for Tenant Context
-- ===============================================================

-- Function to get current organization ID from session
CREATE OR REPLACE FUNCTION current_organization_id()
RETURNS UUID AS $$
BEGIN
    RETURN current_setting('app.current_organization_id', true)::UUID;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if current user is super admin
CREATE OR REPLACE FUNCTION is_super_admin()
RETURNS BOOLEAN AS $$
BEGIN
    -- Check if user has superuser privileges or specific super admin role
    RETURN (
        current_setting('is_superuser', true)::BOOLEAN = true OR
        current_setting('app.is_super_admin', true)::BOOLEAN = true OR
        pg_has_role(current_user, 'super_admin', 'member')
    );
EXCEPTION
    WHEN OTHERS THEN
        RETURN false;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if current user can access organization
CREATE OR REPLACE FUNCTION can_access_organization(org_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    -- Super admins can access all organizations
    IF is_super_admin() THEN
        RETURN true;
    END IF;

    -- Check if the organization ID matches current session
    RETURN current_organization_id() = org_id;
EXCEPTION
    WHEN OTHERS THEN
        RETURN false;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to validate organization exists and is active
CREATE OR REPLACE FUNCTION is_organization_active(org_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM organizations
        WHERE id = org_id
        AND is_active = true
        AND deleted_at IS NULL
    );
EXCEPTION
    WHEN OTHERS THEN
        RETURN false;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ===============================================================
-- 2. Core RLS Policy Templates
-- ===============================================================

-- Create a function to generate standard tenant isolation policies
CREATE OR REPLACE FUNCTION create_tenant_policies(table_name TEXT)
RETURNS VOID AS $$
BEGIN
    -- Drop existing policies if they exist
    EXECUTE format('DROP POLICY IF EXISTS %I_tenant_isolation_policy ON %I', table_name, table_name);
    EXECUTE format('DROP POLICY IF EXISTS %I_super_admin_policy ON %I', table_name, table_name);

    -- Create comprehensive tenant isolation policy
    EXECUTE format('
        CREATE POLICY %I_tenant_isolation_policy ON %I
        FOR ALL
        TO public
        USING (
            can_access_organization(organization_id) AND
            is_organization_active(organization_id)
        )
        WITH CHECK (
            can_access_organization(organization_id) AND
            is_organization_active(organization_id)
        )', table_name, table_name);

    -- Create super admin bypass policy
    EXECUTE format('
        CREATE POLICY %I_super_admin_policy ON %I
        FOR ALL
        TO public
        USING (is_super_admin())
        WITH CHECK (is_super_admin())', table_name, table_name);

    RAISE NOTICE 'Created tenant policies for table: %', table_name;
END;
$$ LANGUAGE plpgsql;

-- ===============================================================
-- 3. Apply RLS Policies to All Tenant Tables
-- ===============================================================

-- Enable RLS and create policies for all tenant-scoped tables
DO $$
DECLARE
    table_name TEXT;
    tenant_tables TEXT[] := ARRAY[
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
    ];
BEGIN
    FOREACH table_name IN ARRAY tenant_tables
    LOOP
        -- Check if table exists before applying policies
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = table_name) THEN
            -- Enable RLS
            EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', table_name);

            -- Create tenant isolation policies
            PERFORM create_tenant_policies(table_name);

            RAISE NOTICE 'Applied RLS policies to table: %', table_name;
        ELSE
            RAISE NOTICE 'Table % does not exist, skipping', table_name;
        END IF;
    END LOOP;
END $$;

-- ===============================================================
-- 4. Special Policies for Organizations Table
-- ===============================================================

-- Organizations table needs special handling since it's the tenant root
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;

-- Policy for users to see their own organizations
CREATE POLICY organizations_user_access_policy ON organizations
FOR SELECT
TO public
USING (
    is_super_admin() OR
    id = current_organization_id() OR
    -- Allow access if user is a member of the organization
    EXISTS (
        SELECT 1 FROM users
        WHERE users.organization_id = organizations.id
        AND users.id::TEXT = current_setting('app.current_user_id', true)
    )
);

-- Policy for creating organizations (only super admins or during signup)
CREATE POLICY organizations_create_policy ON organizations
FOR INSERT
TO public
WITH CHECK (
    is_super_admin() OR
    current_setting('app.allow_org_creation', true)::BOOLEAN = true
);

-- Policy for updating organizations (only super admins or org admins)
CREATE POLICY organizations_update_policy ON organizations
FOR UPDATE
TO public
USING (
    is_super_admin() OR
    (id = current_organization_id() AND
     current_setting('app.is_org_admin', true)::BOOLEAN = true)
)
WITH CHECK (
    is_super_admin() OR
    (id = current_organization_id() AND
     current_setting('app.is_org_admin', true)::BOOLEAN = true)
);

-- Policy for deleting organizations (only super admins)
CREATE POLICY organizations_delete_policy ON organizations
FOR DELETE
TO public
USING (is_super_admin());

-- ===============================================================
-- 5. Special Policies for Cross-Tenant Tables
-- ===============================================================

-- Organization invitations - need special handling
ALTER TABLE organization_invitations ENABLE ROW LEVEL SECURITY;

CREATE POLICY org_invitations_access_policy ON organization_invitations
FOR ALL
TO public
USING (
    is_super_admin() OR
    can_access_organization(organization_id) OR
    -- Allow access to invitations sent to current user's email
    email = current_setting('app.current_user_email', true)
)
WITH CHECK (
    is_super_admin() OR
    can_access_organization(organization_id)
);

-- Organization usage logs - read-only for org members, write for system
ALTER TABLE organization_usage_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY org_usage_logs_read_policy ON organization_usage_logs
FOR SELECT
TO public
USING (
    is_super_admin() OR
    can_access_organization(organization_id)
);

CREATE POLICY org_usage_logs_write_policy ON organization_usage_logs
FOR INSERT
TO public
WITH CHECK (
    is_super_admin() OR
    current_setting('app.is_system_service', true)::BOOLEAN = true
);

-- ===============================================================
-- 6. Helper Views for Multi-Tenant Queries
-- ===============================================================

-- View for current organization's users
CREATE OR REPLACE VIEW current_org_users AS
SELECT u.* FROM users u
WHERE u.organization_id = current_organization_id()
AND u.deleted_at IS NULL;

-- View for current organization's classes
CREATE OR REPLACE VIEW current_org_classes AS
SELECT c.* FROM classes c
WHERE c.organization_id = current_organization_id()
AND c.deleted_at IS NULL;

-- View for current organization's courses
CREATE OR REPLACE VIEW current_org_courses AS
SELECT c.* FROM courses c
WHERE c.organization_id = current_organization_id()
AND c.deleted_at IS NULL;

-- ===============================================================
-- 7. Security Validation Functions
-- ===============================================================

-- Function to validate tenant isolation
CREATE OR REPLACE FUNCTION validate_tenant_isolation()
RETURNS TABLE(
    table_name TEXT,
    has_rls BOOLEAN,
    policy_count INTEGER,
    organization_id_exists BOOLEAN
) AS $$
DECLARE
    rec RECORD;
BEGIN
    FOR rec IN
        SELECT t.table_name
        FROM information_schema.tables t
        WHERE t.table_schema = 'public'
        AND t.table_type = 'BASE TABLE'
        AND t.table_name != 'organizations'
        AND EXISTS (
            SELECT 1 FROM information_schema.columns c
            WHERE c.table_name = t.table_name
            AND c.column_name = 'organization_id'
        )
    LOOP
        SELECT
            rec.table_name,
            COALESCE(r.rowlevel, false),
            COUNT(p.policyname),
            EXISTS (
                SELECT 1 FROM information_schema.columns c
                WHERE c.table_name = rec.table_name
                AND c.column_name = 'organization_id'
            )
        INTO table_name, has_rls, policy_count, organization_id_exists
        FROM pg_tables pt
        LEFT JOIN pg_class pc ON pc.relname = pt.tablename
        LEFT JOIN pg_rowlevel_policy r ON r.schemaname = pt.schemaname AND r.tablename = pt.tablename
        LEFT JOIN pg_policies p ON p.tablename = pt.tablename
        WHERE pt.tablename = rec.table_name
        GROUP BY rec.table_name, r.rowlevel;

        RETURN NEXT;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Function to test tenant isolation
CREATE OR REPLACE FUNCTION test_tenant_isolation(
    org_id1 UUID,
    org_id2 UUID,
    test_table TEXT DEFAULT 'users'
)
RETURNS TABLE(
    test_description TEXT,
    org1_count INTEGER,
    org2_count INTEGER,
    isolation_working BOOLEAN
) AS $$
DECLARE
    count1 INTEGER;
    count2 INTEGER;
BEGIN
    -- Test with first organization
    PERFORM set_config('app.current_organization_id', org_id1::TEXT, true);
    EXECUTE format('SELECT COUNT(*) FROM %I', test_table) INTO count1;

    -- Test with second organization
    PERFORM set_config('app.current_organization_id', org_id2::TEXT, true);
    EXECUTE format('SELECT COUNT(*) FROM %I', test_table) INTO count2;

    -- Clear organization context
    PERFORM set_config('app.current_organization_id', '', true);

    RETURN QUERY SELECT
        format('Tenant isolation test for %s', test_table)::TEXT,
        count1,
        count2,
        (count1 != count2 OR (count1 = 0 AND count2 = 0))::BOOLEAN;
END;
$$ LANGUAGE plpgsql;

-- ===============================================================
-- 8. Administrative Functions
-- ===============================================================

-- Function to set organization context (for application use)
CREATE OR REPLACE FUNCTION set_current_organization(org_id UUID)
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_organization_id', org_id::TEXT, true);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to clear organization context
CREATE OR REPLACE FUNCTION clear_current_organization()
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_organization_id', '', true);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to temporarily bypass RLS (for migrations/admin tasks)
CREATE OR REPLACE FUNCTION bypass_rls_start()
RETURNS VOID AS $$
BEGIN
    IF NOT is_super_admin() THEN
        RAISE EXCEPTION 'Only super admins can bypass RLS';
    END IF;
    PERFORM set_config('row_security', 'off', true);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to re-enable RLS
CREATE OR REPLACE FUNCTION bypass_rls_end()
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('row_security', 'on', true);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ===============================================================
-- 9. Monitoring and Logging
-- ===============================================================

-- Create audit log table for RLS policy violations
CREATE TABLE IF NOT EXISTS tenant_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_time TIMESTAMPTZ DEFAULT NOW(),
    user_name TEXT DEFAULT current_user,
    organization_id UUID,
    table_name TEXT,
    operation TEXT,
    denied_reason TEXT,
    session_info JSONB DEFAULT jsonb_build_object(
        'application_name', current_setting('application_name', true),
        'client_addr', inet_client_addr(),
        'session_user', session_user
    )
);

-- Enable RLS on audit log (only super admins can see all entries)
ALTER TABLE tenant_audit_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_audit_log_admin_policy ON tenant_audit_log
FOR ALL TO public
USING (is_super_admin())
WITH CHECK (is_super_admin());

-- ===============================================================
-- 10. Performance Optimization
-- ===============================================================

-- Create indexes to optimize RLS policy performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_org_active
ON users(organization_id) WHERE deleted_at IS NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_courses_org_active
ON courses(organization_id) WHERE deleted_at IS NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_classes_org_active
ON classes(organization_id) WHERE deleted_at IS NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lessons_org_active
ON lessons(organization_id) WHERE deleted_at IS NULL;

-- Partial indexes for common queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_org_role_active
ON users(organization_id, role) WHERE deleted_at IS NULL AND is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_org_active
ON sessions(organization_id) WHERE is_active = true;

-- ===============================================================
-- Summary and Next Steps
-- ===============================================================

-- Log successful policy creation
DO $$
BEGIN
    RAISE NOTICE '==============================================';
    RAISE NOTICE 'RLS Policies Applied Successfully!';
    RAISE NOTICE '==============================================';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Test tenant isolation: SELECT * FROM validate_tenant_isolation();';
    RAISE NOTICE '2. Update application to set organization context';
    RAISE NOTICE '3. Test with different organization IDs';
    RAISE NOTICE '4. Monitor performance and adjust indexes as needed';
    RAISE NOTICE '==============================================';
END $$;

-- Grant necessary permissions to application roles
-- Note: Adjust these based on your actual application roles
-- GRANT EXECUTE ON FUNCTION set_current_organization(UUID) TO application_role;
-- GRANT EXECUTE ON FUNCTION current_organization_id() TO application_role;
-- GRANT EXECUTE ON FUNCTION can_access_organization(UUID) TO application_role;
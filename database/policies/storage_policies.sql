-- ============================================
-- Row-Level Security Policies for Storage System
-- ============================================
-- This file implements comprehensive RLS policies for the storage system
-- ensuring complete tenant isolation and access control.
--
-- Author: ToolBoxAI Team
-- Created: 2025-01-27
-- ============================================

-- ============================================
-- SETUP
-- ============================================

-- Enable RLS on all storage tables
ALTER TABLE files ENABLE ROW LEVEL SECURITY;
ALTER TABLE file_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE file_shares ENABLE ROW LEVEL SECURITY;
ALTER TABLE storage_quotas ENABLE ROW LEVEL SECURITY;
ALTER TABLE file_access_logs ENABLE ROW LEVEL SECURITY;

-- ============================================
-- HELPER FUNCTIONS
-- ============================================

-- Function to get current organization_id from session
CREATE OR REPLACE FUNCTION get_current_organization_id()
RETURNS UUID AS $$
BEGIN
    RETURN current_setting('app.current_organization_id', true)::UUID;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if user is organization admin
CREATE OR REPLACE FUNCTION is_organization_admin(user_id UUID, org_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM users
        WHERE id = user_id
        AND organization_id = org_id
        AND role IN ('admin', 'organization_admin')
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if user has access to file
CREATE OR REPLACE FUNCTION user_has_file_access(user_id UUID, file_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    file_org_id UUID;
    file_uploaded_by UUID;
    is_shared BOOLEAN;
BEGIN
    -- Get file organization and uploader
    SELECT organization_id, uploaded_by INTO file_org_id, file_uploaded_by
    FROM files WHERE id = file_id;

    -- Owner has access
    IF file_uploaded_by = user_id THEN
        RETURN TRUE;
    END IF;

    -- Organization members have access to org files
    IF EXISTS (
        SELECT 1 FROM users
        WHERE id = user_id
        AND organization_id = file_org_id
    ) THEN
        RETURN TRUE;
    END IF;

    -- Check if file is shared with user
    SELECT EXISTS (
        SELECT 1 FROM file_shares
        WHERE file_id = file_id
        AND (
            share_type = 'public_link'
            OR user_id = ANY(shared_with_users)
            OR EXISTS (
                SELECT 1 FROM class_enrollments
                WHERE student_id = user_id
                AND class_id = file_shares.shared_with_class
            )
        )
    ) INTO is_shared;

    RETURN is_shared;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- FILES TABLE POLICIES
-- ============================================

-- Policy: Users can view files from their organization
CREATE POLICY files_select_own_org ON files
    FOR SELECT
    USING (
        organization_id = get_current_organization_id()
        OR uploaded_by = auth.uid()
        OR user_has_file_access(auth.uid(), id)
    );

-- Policy: Users can insert files to their organization
CREATE POLICY files_insert_own_org ON files
    FOR INSERT
    WITH CHECK (
        organization_id = get_current_organization_id()
        AND uploaded_by = auth.uid()
    );

-- Policy: Users can update their own files
CREATE POLICY files_update_own ON files
    FOR UPDATE
    USING (
        uploaded_by = auth.uid()
        OR is_organization_admin(auth.uid(), organization_id)
    )
    WITH CHECK (
        organization_id = get_current_organization_id()
    );

-- Policy: Users can soft delete their own files
CREATE POLICY files_delete_own ON files
    FOR UPDATE
    USING (
        uploaded_by = auth.uid()
        OR is_organization_admin(auth.uid(), organization_id)
    )
    WITH CHECK (
        is_deleted = TRUE
        AND organization_id = get_current_organization_id()
    );

-- ============================================
-- FILE_VERSIONS TABLE POLICIES
-- ============================================

-- Policy: Users can view versions of files they have access to
CREATE POLICY file_versions_select ON file_versions
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM files
            WHERE files.id = file_versions.file_id
            AND (
                files.organization_id = get_current_organization_id()
                OR files.uploaded_by = auth.uid()
                OR user_has_file_access(auth.uid(), files.id)
            )
        )
    );

-- Policy: Users can create versions of their own files
CREATE POLICY file_versions_insert ON file_versions
    FOR INSERT
    WITH CHECK (
        organization_id = get_current_organization_id()
        AND changed_by = auth.uid()
        AND EXISTS (
            SELECT 1 FROM files
            WHERE files.id = file_versions.file_id
            AND files.uploaded_by = auth.uid()
        )
    );

-- ============================================
-- FILE_SHARES TABLE POLICIES
-- ============================================

-- Policy: Users can view shares they created or are shared with
CREATE POLICY file_shares_select ON file_shares
    FOR SELECT
    USING (
        shared_by = auth.uid()
        OR auth.uid() = ANY(shared_with_users)
        OR EXISTS (
            SELECT 1 FROM files
            WHERE files.id = file_shares.file_id
            AND files.uploaded_by = auth.uid()
        )
        OR share_type = 'public_link'
    );

-- Policy: Users can create shares for their files
CREATE POLICY file_shares_insert ON file_shares
    FOR INSERT
    WITH CHECK (
        organization_id = get_current_organization_id()
        AND shared_by = auth.uid()
        AND EXISTS (
            SELECT 1 FROM files
            WHERE files.id = file_shares.file_id
            AND (
                files.uploaded_by = auth.uid()
                OR is_organization_admin(auth.uid(), files.organization_id)
            )
        )
    );

-- Policy: Users can update their own shares
CREATE POLICY file_shares_update ON file_shares
    FOR UPDATE
    USING (
        shared_by = auth.uid()
        OR EXISTS (
            SELECT 1 FROM files
            WHERE files.id = file_shares.file_id
            AND files.uploaded_by = auth.uid()
        )
    )
    WITH CHECK (
        organization_id = get_current_organization_id()
    );

-- Policy: Users can delete their own shares
CREATE POLICY file_shares_delete ON file_shares
    FOR DELETE
    USING (
        shared_by = auth.uid()
        OR EXISTS (
            SELECT 1 FROM files
            WHERE files.id = file_shares.file_id
            AND files.uploaded_by = auth.uid()
        )
    );

-- ============================================
-- STORAGE_QUOTAS TABLE POLICIES
-- ============================================

-- Policy: Organization admins can view their quota
CREATE POLICY storage_quotas_select ON storage_quotas
    FOR SELECT
    USING (
        organization_id = get_current_organization_id()
        OR is_organization_admin(auth.uid(), organization_id)
    );

-- Policy: Only system can insert quotas (via migration/admin)
CREATE POLICY storage_quotas_insert ON storage_quotas
    FOR INSERT
    WITH CHECK (
        is_organization_admin(auth.uid(), organization_id)
        OR current_user = 'postgres'
    );

-- Policy: Organization admins can update their quota settings
CREATE POLICY storage_quotas_update ON storage_quotas
    FOR UPDATE
    USING (
        is_organization_admin(auth.uid(), organization_id)
    )
    WITH CHECK (
        organization_id = get_current_organization_id()
    );

-- ============================================
-- FILE_ACCESS_LOGS TABLE POLICIES
-- ============================================

-- Policy: Users can view their own access logs
CREATE POLICY file_access_logs_select_own ON file_access_logs
    FOR SELECT
    USING (
        user_id = auth.uid()
        OR is_organization_admin(auth.uid(), organization_id)
    );

-- Policy: System can insert access logs
CREATE POLICY file_access_logs_insert ON file_access_logs
    FOR INSERT
    WITH CHECK (
        organization_id = get_current_organization_id()
    );

-- ============================================
-- STORAGE BUCKET POLICIES (SUPABASE STORAGE)
-- ============================================

-- Note: These policies are for Supabase Storage buckets
-- They should be applied via Supabase dashboard or API

-- Create organization-specific bucket policy function
CREATE OR REPLACE FUNCTION create_org_bucket_policies(bucket_name TEXT, org_id UUID)
RETURNS VOID AS $$
BEGIN
    -- Policy for SELECT (viewing files)
    EXECUTE format('
        CREATE POLICY %I ON storage.objects
        FOR SELECT USING (
            bucket_id = %L AND
            (storage.foldername(name))[1] = %L
        )',
        bucket_name || '_select',
        bucket_name,
        org_id::TEXT
    );

    -- Policy for INSERT (uploading files)
    EXECUTE format('
        CREATE POLICY %I ON storage.objects
        FOR INSERT WITH CHECK (
            bucket_id = %L AND
            (storage.foldername(name))[1] = %L AND
            auth.uid() IN (
                SELECT id FROM users WHERE organization_id = %L
            )
        )',
        bucket_name || '_insert',
        bucket_name,
        org_id::TEXT,
        org_id
    );

    -- Policy for UPDATE (modifying files)
    EXECUTE format('
        CREATE POLICY %I ON storage.objects
        FOR UPDATE USING (
            bucket_id = %L AND
            (storage.foldername(name))[1] = %L AND
            auth.uid() IN (
                SELECT id FROM users WHERE organization_id = %L
            )
        )',
        bucket_name || '_update',
        bucket_name,
        org_id::TEXT,
        org_id
    );

    -- Policy for DELETE (removing files)
    EXECUTE format('
        CREATE POLICY %I ON storage.objects
        FOR DELETE USING (
            bucket_id = %L AND
            (storage.foldername(name))[1] = %L AND
            auth.uid() IN (
                SELECT id FROM users WHERE organization_id = %L AND role IN (''admin'', ''teacher'')
            )
        )',
        bucket_name || '_delete',
        bucket_name,
        org_id::TEXT,
        org_id
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- SUPER ADMIN BYPASS POLICIES
-- ============================================

-- Create super admin bypass for all tables
CREATE POLICY super_admin_all_files ON files
    FOR ALL
    USING (current_setting('app.super_admin', true)::BOOLEAN = TRUE);

CREATE POLICY super_admin_all_file_versions ON file_versions
    FOR ALL
    USING (current_setting('app.super_admin', true)::BOOLEAN = TRUE);

CREATE POLICY super_admin_all_file_shares ON file_shares
    FOR ALL
    USING (current_setting('app.super_admin', true)::BOOLEAN = TRUE);

CREATE POLICY super_admin_all_storage_quotas ON storage_quotas
    FOR ALL
    USING (current_setting('app.super_admin', true)::BOOLEAN = TRUE);

CREATE POLICY super_admin_all_file_access_logs ON file_access_logs
    FOR ALL
    USING (current_setting('app.super_admin', true)::BOOLEAN = TRUE);

-- ============================================
-- PERFORMANCE INDEXES
-- ============================================

-- Add additional indexes for RLS performance
CREATE INDEX IF NOT EXISTS idx_files_org_uploaded_by ON files(organization_id, uploaded_by);
CREATE INDEX IF NOT EXISTS idx_file_shares_shared_by ON file_shares(shared_by);
CREATE INDEX IF NOT EXISTS idx_file_shares_shared_users ON file_shares USING GIN(shared_with_users);

-- ============================================
-- GRANT PERMISSIONS
-- ============================================

-- Grant necessary permissions to application role
GRANT SELECT, INSERT, UPDATE ON files TO authenticated;
GRANT SELECT, INSERT ON file_versions TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON file_shares TO authenticated;
GRANT SELECT ON storage_quotas TO authenticated;
GRANT SELECT, INSERT ON file_access_logs TO authenticated;

-- Grant execute on helper functions
GRANT EXECUTE ON FUNCTION get_current_organization_id() TO authenticated;
GRANT EXECUTE ON FUNCTION is_organization_admin(UUID, UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION user_has_file_access(UUID, UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION create_org_bucket_policies(TEXT, UUID) TO authenticated;
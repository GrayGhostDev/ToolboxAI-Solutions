-- Version: 001_create_api_keys_table
-- Description: Create API keys table with RLS policies for secure API key management
-- Type: schema
-- Requires-Maintenance: false
-- Dependencies: none

-- UP
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    key_id VARCHAR(255) UNIQUE NOT NULL,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    prefix VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    organization VARCHAR(255),
    contact_email VARCHAR(255),

    -- Scopes and permissions
    scopes TEXT[] DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active',

    -- IP and origin restrictions
    ip_whitelist INET[] DEFAULT NULL,
    allowed_origins TEXT[] DEFAULT NULL,

    -- Rate limiting
    rate_limit_per_minute INTEGER DEFAULT 60,
    rate_limit_per_hour INTEGER DEFAULT 1000,
    rate_limit_per_day INTEGER DEFAULT 10000,

    -- Usage tracking
    total_requests BIGINT DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    last_used_ip INET,

    -- Lifecycle
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    rotated_at TIMESTAMP WITH TIME ZONE,
    revoked_at TIMESTAMP WITH TIME ZONE,
    revoked_reason TEXT,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Indexes for performance
    CONSTRAINT valid_status CHECK (status IN ('active', 'inactive', 'expired', 'revoked', 'suspended'))
);

-- Create indexes for better query performance
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_status ON api_keys(status);
CREATE INDEX idx_api_keys_organization ON api_keys(organization);
CREATE INDEX idx_api_keys_expires_at ON api_keys(expires_at);
CREATE INDEX idx_api_keys_last_used_at ON api_keys(last_used_at DESC);

-- Enable Row Level Security
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- Only service role can manage API keys
CREATE POLICY "Service role can manage API keys" ON api_keys
    FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

-- Create function to validate API key
CREATE OR REPLACE FUNCTION validate_api_key(p_key_hash TEXT)
RETURNS TABLE (
    is_valid BOOLEAN,
    key_id VARCHAR,
    name VARCHAR,
    scopes TEXT[],
    rate_limits JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        CASE
            WHEN ak.status = 'active'
                AND (ak.expires_at IS NULL OR ak.expires_at > NOW())
            THEN TRUE
            ELSE FALSE
        END AS is_valid,
        ak.key_id,
        ak.name,
        ak.scopes,
        jsonb_build_object(
            'per_minute', ak.rate_limit_per_minute,
            'per_hour', ak.rate_limit_per_hour,
            'per_day', ak.rate_limit_per_day
        ) AS rate_limits
    FROM api_keys ak
    WHERE ak.key_hash = p_key_hash
    LIMIT 1;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- DOWN
DROP FUNCTION IF EXISTS validate_api_key(TEXT);
DROP POLICY IF EXISTS "Service role can manage API keys" ON api_keys;
DROP TABLE IF EXISTS api_keys;
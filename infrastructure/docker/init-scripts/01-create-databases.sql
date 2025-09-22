-- Create multiple databases for the ToolboxAI platform
-- This script runs automatically when PostgreSQL container starts

-- Create roles if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'eduplatform') THEN
        CREATE ROLE eduplatform WITH LOGIN PASSWORD 'eduplatform2024';
    END IF;

    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'toolboxai') THEN
        CREATE ROLE toolboxai WITH LOGIN PASSWORD 'secure_password';
    END IF;
END
$$;

-- Create databases if they don't exist
SELECT 'CREATE DATABASE educational_platform_dev'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'educational_platform_dev')\gexec

SELECT 'CREATE DATABASE toolboxai_prod'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'toolboxai_prod')\gexec

SELECT 'CREATE DATABASE ghost_cms'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ghost_cms')\gexec

SELECT 'CREATE DATABASE mcp_memory'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'mcp_memory')\gexec

SELECT 'CREATE DATABASE analytics'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'analytics')\gexec

SELECT 'CREATE DATABASE educational_platform_test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'educational_platform_test')\gexec

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE educational_platform_dev TO eduplatform;
GRANT ALL PRIVILEGES ON DATABASE toolboxai_prod TO toolboxai;
GRANT ALL PRIVILEGES ON DATABASE ghost_cms TO toolboxai;
GRANT ALL PRIVILEGES ON DATABASE mcp_memory TO toolboxai;
GRANT ALL PRIVILEGES ON DATABASE analytics TO toolboxai;
GRANT ALL PRIVILEGES ON DATABASE educational_platform_test TO eduplatform;
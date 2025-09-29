-- Create missing database users for ToolboxAI
-- Based on .env configuration

-- Create toolbox_ghost user for ghost_backend database
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'toolbox_ghost') THEN
        CREATE USER toolbox_ghost WITH PASSWORD 'TBGhost2024!Secure#';
        ALTER USER toolbox_ghost CREATEDB;
        GRANT ALL PRIVILEGES ON DATABASE ghost_backend TO toolbox_ghost;
    END IF;
END
$$;

-- Create toolbox_edu user for educational_platform database
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'toolbox_edu') THEN
        CREATE USER toolbox_edu WITH PASSWORD 'TBEdu2024!Secure#';
        ALTER USER toolbox_edu CREATEDB;
        GRANT ALL PRIVILEGES ON DATABASE educational_platform TO toolbox_edu;
    END IF;
END
$$;

-- Create toolbox_roblox user for roblox_data database
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'toolbox_roblox') THEN
        CREATE USER toolbox_roblox WITH PASSWORD 'TBRoblox2024!Secure#';
        ALTER USER toolbox_roblox CREATEDB;
        GRANT ALL PRIVILEGES ON DATABASE roblox_data TO toolbox_roblox;
    END IF;
END
$$;

-- Create toolbox_mcp user for mcp_memory database
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'toolbox_mcp') THEN
        CREATE USER toolbox_mcp WITH PASSWORD 'TBMCP2024!Secure#';
        ALTER USER toolbox_mcp CREATEDB;
        GRANT ALL PRIVILEGES ON DATABASE mcp_memory TO toolbox_mcp;
    END IF;
END
$$;

-- Grant permissions to existing eduplatform user
GRANT ALL PRIVILEGES ON DATABASE educational_platform TO eduplatform;

-- List all users to confirm
\du
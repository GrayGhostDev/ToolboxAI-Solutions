-- Create multiple databases for the ToolboxAI platform
-- This script runs automatically when PostgreSQL container starts

-- Create educational_platform database
CREATE DATABASE educational_platform;
GRANT ALL PRIVILEGES ON DATABASE educational_platform TO eduplatform;

-- Create ghost_backend database for CMS
CREATE DATABASE ghost_backend;
GRANT ALL PRIVILEGES ON DATABASE ghost_backend TO eduplatform;

-- Create roblox_data database for Roblox integration
CREATE DATABASE roblox_data;
GRANT ALL PRIVILEGES ON DATABASE roblox_data TO eduplatform;

-- Create mcp_memory database for MCP context storage
CREATE DATABASE mcp_memory;
GRANT ALL PRIVILEGES ON DATABASE mcp_memory TO eduplatform;

-- Create test database
CREATE DATABASE educational_platform_test;
GRANT ALL PRIVILEGES ON DATABASE educational_platform_test TO eduplatform;
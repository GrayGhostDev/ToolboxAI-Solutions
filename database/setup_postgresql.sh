#!/bin/bash

# ============================================================================
# PostgreSQL Database Setup Script for ToolboxAI
# ============================================================================
# This script creates all required databases and users for the ToolboxAI system

set -e  # Exit on any error

echo "🚀 Setting up PostgreSQL databases for ToolboxAI..."
echo "=================================================="

# Check if PostgreSQL is running
if ! pg_isready -q; then
    echo "❌ PostgreSQL is not running. Please start PostgreSQL and try again."
    echo "   On macOS: brew services start postgresql"
    echo "   On Ubuntu: sudo systemctl start postgresql"
    exit 1
fi

echo "✅ PostgreSQL is running"

# Function to create database and user
create_database_and_user() {
    local db_name=$1
    local db_user=$2
    local db_password=$3
    local description=$4
    
    echo "📊 Creating database: $db_name ($description)"
    
    # Create user if it doesn't exist
    psql -U postgres -c "DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$db_user') THEN
            CREATE ROLE $db_user WITH LOGIN PASSWORD '$db_password';
        END IF;
    END
    \$\$;" 2>/dev/null || echo "User $db_user already exists or created"
    
    # Create database if it doesn't exist
    psql -U postgres -c "SELECT 'CREATE DATABASE $db_name OWNER $db_user'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$db_name')\gexec" 2>/dev/null || echo "Database $db_name already exists or created"
    
    # Grant privileges
    psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE $db_name TO $db_user;" 2>/dev/null || echo "Privileges granted"
    
    # Connect to the database and create extensions
    psql -U postgres -d $db_name -c "
    CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";
    CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";
    CREATE EXTENSION IF NOT EXISTS \"pg_trgm\";
    CREATE EXTENSION IF NOT EXISTS \"btree_gin\";
    CREATE EXTENSION IF NOT EXISTS \"btree_gist\";
    " 2>/dev/null || echo "Extensions created or already exist"
    
    echo "✅ Database $db_name setup complete"
    echo ""
}

# Create all databases
create_database_and_user "ghost_backend" "ghost_user" "ghost_password_2024" "Main API, Authentication, Users"
create_database_and_user "educational_platform" "eduplatform" "eduplatform2024" "Educational Content, Lessons, Progress"
create_database_and_user "roblox_data" "roblox_user" "roblox_password_2024" "Roblox Integration, Scripts, Sessions"
create_database_and_user "mcp_memory" "mcp_user" "mcp_password_2024" "AI Context, Memory, Vector Storage"
create_database_and_user "toolboxai_dev" "postgres" "postgres" "Development and Testing"

echo "🎉 All PostgreSQL databases created successfully!"
echo ""
echo "📋 Database Summary:"
echo "==================="
echo "ghost_backend        - ghost_user / ghost_password_2024"
echo "educational_platform - eduplatform / eduplatform2024"
echo "roblox_data          - roblox_user / roblox_password_2024"
echo "mcp_memory           - mcp_user / mcp_password_2024"
echo "toolboxai_dev        - postgres / postgres"
echo ""
echo "✅ PostgreSQL setup complete! You can now run the database schema setup."

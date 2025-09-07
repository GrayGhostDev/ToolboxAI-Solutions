#!/bin/bash

# ============================================================================
# ToolboxAI Database Setup Script
# ============================================================================
# This script sets up the complete database infrastructure for ToolboxAI
# Run this script to initialize all databases, schemas, and connections

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATABASE_DIR="$PROJECT_ROOT/database"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"

# Database configuration
POSTGRES_USER="postgres"
POSTGRES_HOST="localhost"
POSTGRES_PORT="5432"

# Database names and users
declare -A DATABASES=(
    ["ghost_backend"]="ghost_user"
    ["educational_platform"]="eduplatform"
    ["roblox_data"]="roblox_user"
    ["mcp_memory"]="mcp_user"
    ["toolboxai_dev"]="postgres"
)

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if PostgreSQL is running
check_postgresql() {
    print_status "Checking PostgreSQL connection..."
    
    if ! command -v psql &> /dev/null; then
        print_error "PostgreSQL client (psql) is not installed"
        exit 1
    fi
    
    if ! psql -U "$POSTGRES_USER" -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -c "SELECT 1;" &> /dev/null; then
        print_error "Cannot connect to PostgreSQL. Please ensure PostgreSQL is running and accessible."
        print_error "Connection details: $POSTGRES_USER@$POSTGRES_HOST:$POSTGRES_PORT"
        exit 1
    fi
    
    print_success "PostgreSQL is running and accessible"
}

# Function to check if Python dependencies are installed
check_python_deps() {
    print_status "Checking Python dependencies..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    # Check for required Python packages
    local required_packages=("sqlalchemy" "psycopg2-binary" "alembic" "redis" "pymongo" "python-dotenv")
    
    for package in "${required_packages[@]}"; do
        if ! python3 -c "import ${package//-/_}" &> /dev/null; then
            print_warning "Package $package is not installed. Installing..."
            pip3 install "$package"
        fi
    done
    
    print_success "Python dependencies are available"
}

# Function to create databases and users
create_databases() {
    print_status "Creating databases and users..."
    
    # Create a temporary SQL script
    local temp_sql=$(mktemp)
    
    cat > "$temp_sql" << 'EOF'
-- Create users
DO $$
BEGIN
    -- Ghost Backend User
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'ghost_user') THEN
        CREATE USER ghost_user WITH PASSWORD 'ghost_password_2024';
        ALTER USER ghost_user CREATEDB;
    END IF;
    
    -- Educational Platform User
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'eduplatform') THEN
        CREATE USER eduplatform WITH PASSWORD 'eduplatform2024';
        ALTER USER eduplatform CREATEDB;
    END IF;
    
    -- Roblox Data User
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'roblox_user') THEN
        CREATE USER roblox_user WITH PASSWORD 'roblox_password_2024';
        ALTER USER roblox_user CREATEDB;
    END IF;
    
    -- MCP Memory User
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'mcp_user') THEN
        CREATE USER mcp_user WITH PASSWORD 'mcp_password_2024';
        ALTER USER mcp_user CREATEDB;
    END IF;
END
$$;

-- Create databases
DO $$
BEGIN
    -- Ghost Backend Database
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ghost_backend') THEN
        CREATE DATABASE ghost_backend OWNER ghost_user;
    END IF;
    
    -- Educational Platform Database
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'educational_platform') THEN
        CREATE DATABASE educational_platform OWNER eduplatform;
    END IF;
    
    -- Roblox Data Database
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'roblox_data') THEN
        CREATE DATABASE roblox_data OWNER roblox_user;
    END IF;
    
    -- MCP Memory Database
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'mcp_memory') THEN
        CREATE DATABASE mcp_memory OWNER mcp_user;
    END IF;
    
    -- Development Database
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'toolboxai_dev') THEN
        CREATE DATABASE toolboxai_dev OWNER postgres;
    END IF;
END
$$;
EOF

    # Execute the SQL script
    psql -U "$POSTGRES_USER" -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -f "$temp_sql"
    
    # Clean up
    rm "$temp_sql"
    
    print_success "Databases and users created successfully"
}

# Function to install extensions in databases
install_extensions() {
    print_status "Installing PostgreSQL extensions..."
    
    for db_name in "${!DATABASES[@]}"; do
        print_status "Installing extensions in $db_name..."
        
        psql -U "$POSTGRES_USER" -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -d "$db_name" << 'EOF'
-- Install required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Grant permissions
GRANT ALL ON SCHEMA public TO CURRENT_USER;
EOF
        
        print_success "Extensions installed in $db_name"
    done
}

# Function to deploy schemas
deploy_schemas() {
    print_status "Deploying database schemas..."
    
    # Deploy schemas to educational_platform database
    local schema_files=(
        "01_core_schema.sql"
        "02_ai_agents_schema.sql"
        "03_lms_integration_schema.sql"
        "04_analytics_schema.sql"
    )
    
    for schema_file in "${schema_files[@]}"; do
        local schema_path="$DATABASE_DIR/schemas/$schema_file"
        
        if [[ -f "$schema_path" ]]; then
            print_status "Deploying $schema_file..."
            psql -U "eduplatform" -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -d "educational_platform" -f "$schema_path"
            print_success "$schema_file deployed successfully"
        else
            print_warning "$schema_file not found, skipping..."
        fi
    done
}

# Function to setup Alembic migrations
setup_migrations() {
    print_status "Setting up Alembic migrations..."
    
    cd "$DATABASE_DIR"
    
    # Initialize Alembic if not already done
    if [[ ! -d "migrations/versions" ]]; then
        print_status "Initializing Alembic..."
        alembic init migrations
    fi
    
    # Create initial migration
    print_status "Creating initial migration..."
    alembic revision --autogenerate -m "Initial schema"
    
    # Run migrations
    print_status "Running migrations..."
    alembic upgrade head
    
    print_success "Alembic migrations setup completed"
}

# Function to create environment file
create_env_file() {
    print_status "Creating environment configuration..."
    
    local env_file="$PROJECT_ROOT/.env"
    local env_example="$PROJECT_ROOT/config/database.env.example"
    
    if [[ ! -f "$env_file" ]]; then
        if [[ -f "$env_example" ]]; then
            cp "$env_example" "$env_file"
            print_success "Environment file created from template"
            print_warning "Please update $env_file with your actual database credentials"
        else
            print_warning "Environment template not found, creating basic .env file"
            cat > "$env_file" << 'EOF'
# Database Configuration
EDU_DB_HOST=localhost
EDU_DB_PORT=5432
EDU_DB_NAME=educational_platform
EDU_DB_USER=eduplatform
EDU_DB_PASSWORD=eduplatform2024
EDU_DB_ECHO=false

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Environment
ENVIRONMENT=development
DEBUG=true
EOF
        fi
    else
        print_warning "Environment file already exists, skipping creation"
    fi
}

# Function to run health checks
run_health_checks() {
    print_status "Running database health checks..."
    
    cd "$PROJECT_ROOT"
    python3 database/connection_manager.py
    
    if [[ $? -eq 0 ]]; then
        print_success "All database connections are healthy"
    else
        print_error "Some database connections failed health checks"
        return 1
    fi
}

# Function to create development data
create_dev_data() {
    print_status "Creating development data..."
    
    cd "$PROJECT_ROOT"
    python3 database/setup_database.py --dev-data
    
    if [[ $? -eq 0 ]]; then
        print_success "Development data created successfully"
    else
        print_warning "Failed to create development data"
    fi
}

# Function to show setup summary
show_summary() {
    print_success "Database setup completed successfully!"
    echo
    echo "📊 Database Summary:"
    echo "  - Ghost Backend: ghost_backend (ghost_user)"
    echo "  - Educational Platform: educational_platform (eduplatform)"
    echo "  - Roblox Data: roblox_data (roblox_user)"
    echo "  - MCP Memory: mcp_memory (mcp_user)"
    echo "  - Development: toolboxai_dev (postgres)"
    echo
    echo "🔧 Next Steps:"
    echo "  1. Update your .env file with the correct database credentials"
    echo "  2. Start Redis server: redis-server"
    echo "  3. Run the application: python src/dashboard/backend/main.py"
    echo "  4. Access the dashboard at http://localhost:5176"
    echo
    echo "📚 Useful Commands:"
    echo "  - Create migration: python database/migrate.py create 'message'"
    echo "  - Run migrations: python database/migrate.py upgrade"
    echo "  - Check health: python database/migrate.py health"
    echo "  - View history: python database/migrate.py history"
}

# Main execution
main() {
    echo "🚀 ToolboxAI Database Setup"
    echo "=========================="
    echo
    
    # Check prerequisites
    check_postgresql
    check_python_deps
    
    # Setup databases
    create_databases
    install_extensions
    deploy_schemas
    setup_migrations
    create_env_file
    
    # Final checks and setup
    run_health_checks
    create_dev_data
    
    # Show summary
    show_summary
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [options]"
        echo
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --dev-data     Create development data only"
        echo "  --health       Run health checks only"
        echo
        exit 0
        ;;
    --dev-data)
        print_status "Creating development data only..."
        create_dev_data
        ;;
    --health)
        print_status "Running health checks only..."
        run_health_checks
        ;;
    *)
        main
        ;;
esac

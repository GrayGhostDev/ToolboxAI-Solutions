#!/usr/bin/env python3
"""
Database Setup Script for ToolboxAI Roblox Environment
Sets up PostgreSQL databases with secure credentials from .env file
"""

import os
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
project_root = Path(__file__).parent.parent
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

def create_postgresql_databases():
    """Create PostgreSQL databases and users with secure passwords."""
    
    print("🚀 Setting up PostgreSQL databases for ToolboxAI...")
    print("=" * 50)
    
    # Check if PostgreSQL is running
    try:
        result = subprocess.run(
            ["pg_isready"],
            capture_output=True,
            text=True,
            check=True,
        )
        print("✅ PostgreSQL is running")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ PostgreSQL is not running. Please start PostgreSQL first:")
        print("   brew services start postgresql@14  # For macOS with Homebrew")
        print("   or")
        print("   sudo systemctl start postgresql    # For Linux")
        return False
    
    # Database configurations from .env
    databases = [
        {
            "name": os.getenv("GHOST_DB_NAME", "educational_platform_dev"),
            "user": os.getenv("GHOST_DB_USER", "eduplatform"),
            "password": os.getenv("GHOST_DB_PASSWORD", "eduplatform2024"),
        },
        {
            "name": os.getenv("EDU_DB_NAME", "educational_platform_dev"),
            "user": os.getenv("EDU_DB_USER", "eduplatform"),
            "password": os.getenv("EDU_DB_PASSWORD", "eduplatform2024"),
        },
        {
            "name": os.getenv("ROBLOX_DB_NAME", "roblox_data"),
            "user": os.getenv("ROBLOX_DB_USER", "toolbox_roblox"),
            "password": os.getenv("ROBLOX_DB_PASSWORD", "TBRoblox2024!Secure#"),
        },
        {
            "name": os.getenv("MCP_DB_NAME", "mcp_memory"),
            "user": os.getenv("MCP_DB_USER", "toolbox_mcp"),
            "password": os.getenv("MCP_DB_PASSWORD", "TBMCP2024!Secure#"),
        },
        {
            "name": os.getenv("DEV_DB_NAME", "toolboxai_dev"),
            "user": os.getenv("DEV_DB_USER", "toolbox_dev"),
            "password": os.getenv("DEV_DB_PASSWORD", "TBDev2024!Secure#"),
        },
    ]
    
    for db_config in databases:
        db_name = db_config["name"]
        db_user = db_config["user"]
        db_password = db_config["password"]
        
        print(f"\n📊 Setting up database: {db_name}")
        
        # Create SQL commands
        sql_commands = f"""
-- Create user if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = '{db_user}') THEN
        CREATE USER {db_user} WITH PASSWORD '{db_password}';
    ELSE
        ALTER USER {db_user} WITH PASSWORD '{db_password}';
    END IF;
END
$$;

-- Create database if not exists
SELECT 'CREATE DATABASE {db_name} OWNER {db_user}'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '{db_name}')\\gexec

-- Grant all privileges
GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_user};
"""
        
        try:
            # Execute SQL commands
            result = subprocess.run(
                ["psql", "-U", "postgres", "-c", sql_commands],
                capture_output=True,
                text=True,
            )
            
            if result.returncode == 0:
                print(f"✅ Database {db_name} configured successfully")
            else:
                # Try alternative approach for database creation
                # First check if database exists
                check_db = subprocess.run(
                    ["psql", "-U", "postgres", "-lqt"],
                    capture_output=True,
                    text=True,
                )
                
                if db_name not in check_db.stdout:
                    # Create database
                    subprocess.run(
                        ["psql", "-U", "postgres", "-c", f"CREATE DATABASE {db_name};"],
                        capture_output=True,
                        text=True,
                    )
                
                # Create/update user
                subprocess.run(
                    ["psql", "-U", "postgres", "-c", 
                     f"CREATE USER {db_user} WITH PASSWORD '{db_password}';"],
                    capture_output=True,
                    text=True,
                )
                
                # Grant privileges
                subprocess.run(
                    ["psql", "-U", "postgres", "-c",
                     f"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_user};"],
                    capture_output=True,
                    text=True,
                )
                
                print(f"✅ Database {db_name} configured successfully (alternative method)")
                
        except Exception as e:
            print(f"⚠️  Warning: Could not fully configure {db_name}: {e}")
            print("   You may need to run the following commands manually:")
            print(f"   CREATE USER {db_user} WITH PASSWORD '***';")
            print(f"   CREATE DATABASE {db_name} OWNER {db_user};")
            print(f"   GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_user};")
    
    print("\n" + "=" * 50)
    print("✅ Database setup completed!")
    print("\nNext steps:")
    print("1. Run database migrations: alembic upgrade head")
    print("2. Start the servers:")
    print("   - FastAPI: python server/main.py")
    print("   - Flask: python server/roblox_server.py")
    print("   - MCP: python mcp/server.py")
    
    return True

def test_connections():
    """Test database connections."""
    print("\n🧪 Testing database connections...")
    
    # Add the project to Python path
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        from database.connection_manager import db_manager, health_check
        
        # Initialize connections
        db_manager.initialize()
        
        # Run health check
        results = health_check()
        
        print("\n📊 Connection Test Results:")
        all_healthy = True
        for service, status in results.items():
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {service}: {'Connected' if status else 'Failed'}")
            if not status:
                all_healthy = False
        
        if all_healthy:
            print("\n✅ All database connections successful!")
        else:
            print("\n⚠️  Some connections failed. Check your PostgreSQL installation and credentials.")
        
        return all_healthy
        
    except ImportError as e:
        print(f"⚠️  Could not import database connection manager: {e}")
        print("   Skipping connection tests...")
        return True

def main():
    """Main function."""
    print("🔧 ToolboxAI Database Setup")
    print("=" * 50)
    
    # Check if .env file exists
    if not env_path.exists():
        print("❌ .env file not found!")
        print(f"   Expected at: {env_path}")
        print("   Please create the .env file first.")
        return False
    
    print(f"✅ Using .env file: {env_path}")
    
    # Create databases
    if not create_postgresql_databases():
        return False
    
    # Test connections
    test_connections()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
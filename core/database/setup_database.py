#!/usr/bin/env python3
"""
Database Setup Script for ToolboxAI Roblox Environment

This script sets up the complete database infrastructure including:
- Database creation
- User creation
- Schema deployment
- Initial data seeding
- Migration system setup
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection_manager import db_manager, health_check


class DatabaseSetup:
    """Handles complete database setup for ToolboxAI."""

    def __init__(self):
        """Initialize database setup."""
        self.project_root = project_root
        self.database_dir = self.project_root / "database"
        self.schemas_dir = self.database_dir / "schemas"
        self.migrations_dir = self.database_dir / "migrations"

    def run_setup(self) -> bool:
        """Run complete database setup."""
        print("🚀 Starting ToolboxAI Database Setup")
        print("=" * 50)

        try:
            # Step 1: Create databases and users
            if not self._create_databases():
                return False

            # Step 2: Initialize database connections
            if not self._initialize_connections():
                return False

            # Step 3: Deploy schemas
            if not self._deploy_schemas():
                return False

            # Step 4: Setup Alembic migrations
            if not self._setup_migrations():
                return False

            # Step 5: Run health checks
            if not self._run_health_checks():
                return False

            print("\n✅ Database setup completed successfully!")
            print("🎉 ToolboxAI is ready to use!")
            return True

        except Exception as e:
            print(f"\n❌ Database setup failed: {e}")
            return False

    def _create_databases(self) -> bool:
        """Create databases and users using SQL scripts."""
        print("\n📊 Step 1: Creating databases and users...")

        # Check if PostgreSQL is running
        if not self._check_postgresql():
            print("❌ PostgreSQL is not running. Please start PostgreSQL and try again.")
            return False

        # Run database creation scripts
        setup_scripts = [
            self.project_root / "src" / "dashboard" / "backend" / "scripts" / "setup_database.sql",
            self.project_root
            / "src"
            / "api"
            / "dashboard-backend"
            / "backend"
            / "scripts"
            / "setup_database.sql",
        ]

        for script_path in setup_scripts:
            if script_path.exists():
                print(f"📝 Running {script_path.name}...")
                try:
                    result = subprocess.run(
                        ["psql", "-U", "postgres", "-f", str(script_path)],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    print(f"✅ {script_path.name} completed successfully")
                except subprocess.CalledProcessError as e:
                    print(f"❌ Failed to run {script_path.name}: {e.stderr}")
                    return False
            else:
                print(f"⚠️  {script_path} not found, skipping...")

        return True

    def _check_postgresql(self) -> bool:
        """Check if PostgreSQL is running."""
        try:
            result = subprocess.run(
                ["pg_isready"],
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _initialize_connections(self) -> bool:
        """Initialize database connections."""
        print("\n🔌 Step 2: Initializing database connections...")

        try:
            db_manager.initialize()
            print("✅ Database connections initialized")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize connections: {e}")
            return False

    def _deploy_schemas(self) -> bool:
        """Deploy database schemas."""
        print("\n📋 Step 3: Deploying database schemas...")

        schema_files = [
            "01_core_schema.sql",
            "02_ai_agents_schema.sql",
            "03_lms_integration_schema.sql",
            "04_analytics_schema.sql",
        ]

        for schema_file in schema_files:
            schema_path = self.schemas_dir / schema_file
            if schema_path.exists():
                print(f"📝 Deploying {schema_file}...")
                try:
                    with db_manager.get_session("education") as session:
                        with open(schema_path, "r") as f:
                            schema_sql = f.read()

                        # Split by semicolon and execute each statement
                        statements = [
                            stmt.strip() for stmt in schema_sql.split(";") if stmt.strip()
                        ]
                        for statement in statements:
                            if statement:
                                session.execute(statement)

                        session.commit()

                    print(f"✅ {schema_file} deployed successfully")
                except Exception as e:
                    print(f"❌ Failed to deploy {schema_file}: {e}")
                    return False
            else:
                print(f"⚠️  {schema_file} not found, skipping...")

        return True

    def _setup_migrations(self) -> bool:
        """Setup Alembic migration system."""
        print("\n🔄 Step 4: Setting up Alembic migrations...")

        try:
            # Check if Alembic is installed
            result = subprocess.run(
                ["alembic", "--version"], capture_output=True, text=True, check=True
            )

            # Initialize Alembic if not already done
            alembic_dir = self.database_dir / "migrations"
            if not (alembic_dir / "versions").exists():
                print("📝 Initializing Alembic...")
                subprocess.run(["alembic", "init", "migrations"], cwd=self.database_dir, check=True)

            # Create initial migration
            print("📝 Creating initial migration...")
            subprocess.run(
                ["alembic", "revision", "--autogenerate", "-m", "Initial schema"],
                cwd=self.database_dir,
                check=True,
            )

            # Run migrations
            print("📝 Running migrations...")
            subprocess.run(["alembic", "upgrade", "head"], cwd=self.database_dir, check=True)

            print("✅ Alembic migrations setup completed")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to setup migrations: {e}")
            return False
        except FileNotFoundError:
            print("⚠️  Alembic not found. Please install it with: pip install alembic")
            return False

    def _run_health_checks(self) -> bool:
        """Run health checks on all databases."""
        print("\n🏥 Step 5: Running health checks...")

        results = health_check()
        all_healthy = True

        for service, status in results.items():
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {service}: {'Healthy' if status else 'Unhealthy'}")
            if not status:
                all_healthy = False

        if all_healthy:
            print("✅ All services are healthy!")
        else:
            print("⚠️  Some services are unhealthy. Please check the configuration.")

        return all_healthy

    def create_development_data(self) -> bool:
        """Create development data for testing."""
        print("\n🌱 Creating development data...")

        try:
            with db_manager.get_session("education") as session:
                # Create test users
                from src.dashboard.backend.models import User, UserRole

                # Check if test users already exist
                existing_user = session.query(User).filter(User.email == "test@example.com").first()
                if not existing_user:
                    test_user = User(
                        username="testuser",
                        email="test@example.com",
                        first_name="Test",
                        last_name="User",
                        role=UserRole.TEACHER,
                        is_active=True,
                        is_verified=True,
                    )
                    test_user.set_password("testpassword")
                    session.add(test_user)

                    # Create student user
                    student_user = User(
                        username="teststudent",
                        email="student@example.com",
                        first_name="Test",
                        last_name="Student",
                        role=UserRole.STUDENT,
                        is_active=True,
                        is_verified=True,
                    )
                    student_user.set_password("testpassword")
                    session.add(student_user)

                    session.commit()
                    print("✅ Test users created")
                else:
                    print("ℹ️  Test users already exist")

            return True

        except Exception as e:
            print(f"❌ Failed to create development data: {e}")
            return False


def main():
    """Main function."""
    setup = DatabaseSetup()

    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--dev-data":
            # Create development data only
            if setup._initialize_connections():
                setup.create_development_data()
            return
        elif sys.argv[1] == "--help":
            print("Usage: python setup_database.py [--dev-data] [--help]")
            print("  --dev-data: Create development data only")
            print("  --help: Show this help message")
            return

    # Run full setup
    success = setup.run_setup()

    if success:
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Update your .env file with the correct database credentials")
        print("2. Run the application: python src/dashboard/backend/main.py")
        print("3. Access the dashboard at http://localhost:5176")
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()

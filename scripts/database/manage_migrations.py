#!/usr/bin/env python3
"""
Database Migration Management Script

Provides convenient commands for managing Alembic migrations following 2025 best practices.
Supports async SQLAlchemy with proper error handling and validation.
"""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime
import argparse
import json
from typing import Optional, List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class MigrationManager:
    """Manage Alembic database migrations"""
    
    def __init__(self):
        self.alembic_ini = project_root / "core" / "database" / "alembic.ini"
        self.migrations_dir = project_root / "core" / "database" / "migrations"
        self.versions_dir = self.migrations_dir / "versions"
        
        # Ensure directories exist
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        
    def run_command(self, cmd: List[str], capture: bool = True) -> subprocess.CompletedProcess:
        """Run an Alembic command"""
        # Use python -m alembic for better compatibility
        full_cmd = [sys.executable, "-m", "alembic", "-c", str(self.alembic_ini)] + cmd
        
        print(f"🔧 Running: {' '.join(full_cmd)}")
        
        result = subprocess.run(
            full_cmd,
            capture_output=capture,
            text=True,
            cwd=str(project_root)
        )
        
        if result.returncode != 0:
            print(f"❌ Command failed: {result.stderr}")
            sys.exit(1)
            
        return result
    
    def current(self) -> str:
        """Get current migration revision"""
        result = self.run_command(["current"])
        return result.stdout.strip()
    
    def history(self, verbose: bool = False) -> str:
        """Get migration history"""
        cmd = ["history"]
        if verbose:
            cmd.append("--verbose")
        result = self.run_command(cmd)
        return result.stdout
    
    def create(self, message: str, autogenerate: bool = True) -> str:
        """Create a new migration"""
        if not message:
            print("❌ Migration message is required")
            sys.exit(1)
        
        # Sanitize message for filename
        safe_message = message.lower().replace(" ", "_").replace("-", "_")
        safe_message = "".join(c for c in safe_message if c.isalnum() or c == "_")
        
        cmd = ["revision", "-m", safe_message]
        if autogenerate:
            cmd.append("--autogenerate")
            print("🔍 Auto-detecting schema changes...")
        
        result = self.run_command(cmd)
        
        # Extract created file path from output
        for line in result.stdout.split("\n"):
            if "Generating" in line or "generating" in line:
                print(f"✅ Created migration: {line.strip()}")
                
        return result.stdout
    
    def upgrade(self, target: str = "head") -> None:
        """Upgrade database to target revision"""
        print(f"⬆️  Upgrading database to: {target}")
        self.run_command(["upgrade", target])
        print("✅ Database upgraded successfully")
    
    def downgrade(self, target: str = "-1") -> None:
        """Downgrade database to target revision"""
        print(f"⬇️  Downgrading database to: {target}")
        
        # Confirm for production
        if os.getenv("ENVIRONMENT") == "production":
            confirm = input("⚠️  Production environment! Type 'DOWNGRADE' to confirm: ")
            if confirm != "DOWNGRADE":
                print("❌ Downgrade cancelled")
                return
        
        self.run_command(["downgrade", target])
        print("✅ Database downgraded successfully")
    
    def show(self, revision: str = "head") -> str:
        """Show a specific migration"""
        result = self.run_command(["show", revision])
        return result.stdout
    
    def heads(self) -> str:
        """Show current head revisions"""
        result = self.run_command(["heads"])
        return result.stdout
    
    def branches(self) -> str:
        """Show branch points"""
        result = self.run_command(["branches"])
        return result.stdout
    
    def check(self) -> bool:
        """Check for pending migrations"""
        current = self.current()
        heads = self.heads()
        
        if "head" in current.lower():
            print("✅ Database is up to date")
            return True
        else:
            print("⚠️  Database has pending migrations")
            print(f"   Current: {current}")
            print(f"   Latest: {heads}")
            return False
    
    def validate(self) -> bool:
        """Validate migration files"""
        print("🔍 Validating migration files...")
        
        issues = []
        
        # Check for migration files
        migration_files = list(self.versions_dir.glob("*.py"))
        if not migration_files:
            issues.append("No migration files found")
        
        # Check for duplicate revision IDs
        revision_ids = set()
        for file in migration_files:
            if file.name == "__pycache__":
                continue
            
            content = file.read_text()
            
            # Extract revision ID
            for line in content.split("\n"):
                if line.startswith("revision = "):
                    rev_id = line.split("=")[1].strip().strip("'\"")
                    if rev_id in revision_ids:
                        issues.append(f"Duplicate revision ID: {rev_id}")
                    revision_ids.add(rev_id)
        
        if issues:
            print("❌ Validation failed:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        
        print(f"✅ Validated {len(migration_files)} migration files")
        return True
    
    def clean(self) -> None:
        """Clean __pycache__ directories"""
        print("🧹 Cleaning migration cache...")
        
        pycache_dirs = list(self.migrations_dir.rglob("__pycache__"))
        for dir in pycache_dirs:
            for file in dir.iterdir():
                file.unlink()
            dir.rmdir()
            
        print(f"✅ Cleaned {len(pycache_dirs)} cache directories")
    
    def backup(self) -> str:
        """Backup migration files"""
        print("💾 Backing up migrations...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = project_root / "backups" / "migrations" / timestamp
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy migration files
        import shutil
        for file in self.versions_dir.glob("*.py"):
            shutil.copy2(file, backup_dir / file.name)
        
        # Copy alembic.ini
        shutil.copy2(self.alembic_ini, backup_dir / "alembic.ini")
        
        # Copy env.py
        env_file = self.migrations_dir / "env.py"
        if env_file.exists():
            shutil.copy2(env_file, backup_dir / "env.py")
        
        print(f"✅ Backed up to: {backup_dir}")
        return str(backup_dir)
    
    def sql(self, start: str = "head-1", end: str = "head") -> str:
        """Generate SQL for migration"""
        print(f"📝 Generating SQL from {start} to {end}...")
        result = self.run_command(["upgrade", f"{start}:{end}", "--sql"])
        return result.stdout
    
    def init_db(self) -> None:
        """Initialize database with all migrations"""
        print("🚀 Initializing database...")
        
        # Stamp database as base
        self.run_command(["stamp", "base"])
        print("   ✓ Stamped as base")
        
        # Upgrade to head
        self.upgrade("head")
        
        # Verify
        if self.check():
            print("✅ Database initialized successfully")
        else:
            print("❌ Database initialization incomplete")


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Manage database migrations for ToolboxAI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s current                    # Show current revision
  %(prog)s create "Add user table"    # Create new migration
  %(prog)s upgrade                    # Upgrade to latest
  %(prog)s downgrade                   # Downgrade one revision
  %(prog)s check                       # Check for pending migrations
  %(prog)s history                    # Show migration history
  %(prog)s validate                   # Validate migration files
  %(prog)s sql                        # Generate SQL for latest migration
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Current revision
    subparsers.add_parser("current", help="Show current migration revision")
    
    # History
    history_parser = subparsers.add_parser("history", help="Show migration history")
    history_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    # Create migration
    create_parser = subparsers.add_parser("create", help="Create new migration")
    create_parser.add_argument("message", help="Migration message")
    create_parser.add_argument("--no-autogenerate", action="store_true", 
                               help="Don't auto-detect schema changes")
    
    # Upgrade
    upgrade_parser = subparsers.add_parser("upgrade", help="Upgrade database")
    upgrade_parser.add_argument("target", nargs="?", default="head", 
                                help="Target revision (default: head)")
    
    # Downgrade
    downgrade_parser = subparsers.add_parser("downgrade", help="Downgrade database")
    downgrade_parser.add_argument("target", nargs="?", default="-1",
                                  help="Target revision (default: -1)")
    
    # Show migration
    show_parser = subparsers.add_parser("show", help="Show specific migration")
    show_parser.add_argument("revision", nargs="?", default="head", help="Revision to show")
    
    # Other commands
    subparsers.add_parser("heads", help="Show current head revisions")
    subparsers.add_parser("branches", help="Show branch points")
    subparsers.add_parser("check", help="Check for pending migrations")
    subparsers.add_parser("validate", help="Validate migration files")
    subparsers.add_parser("clean", help="Clean cache files")
    subparsers.add_parser("backup", help="Backup migration files")
    subparsers.add_parser("init", help="Initialize database with migrations")
    
    # SQL generation
    sql_parser = subparsers.add_parser("sql", help="Generate SQL for migration")
    sql_parser.add_argument("--start", default="head-1", help="Start revision")
    sql_parser.add_argument("--end", default="head", help="End revision")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    manager = MigrationManager()
    
    try:
        if args.command == "current":
            print(manager.current())
        elif args.command == "history":
            print(manager.history(verbose=args.verbose))
        elif args.command == "create":
            manager.create(args.message, autogenerate=not args.no_autogenerate)
        elif args.command == "upgrade":
            manager.upgrade(args.target)
        elif args.command == "downgrade":
            manager.downgrade(args.target)
        elif args.command == "show":
            print(manager.show(args.revision))
        elif args.command == "heads":
            print(manager.heads())
        elif args.command == "branches":
            print(manager.branches())
        elif args.command == "check":
            manager.check()
        elif args.command == "validate":
            manager.validate()
        elif args.command == "clean":
            manager.clean()
        elif args.command == "backup":
            manager.backup()
        elif args.command == "init":
            manager.init_db()
        elif args.command == "sql":
            print(manager.sql(args.start, args.end))
        else:
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        if os.getenv("DEBUG"):
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Database Migration Manager for ToolboxAI Roblox Environment

Provides commands for managing database migrations using Alembic.
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.connection_manager import health_check


class MigrationManager:
    """Manages database migrations for ToolboxAI."""

    def __init__(self):
        """Initialize migration manager."""
        self.project_root = project_root
        self.database_dir = self.project_root / "database"
        self.migrations_dir = self.database_dir / "migrations"

    def create_migration(self, message: str, autogenerate: bool = True) -> bool:
        """Create a new migration."""
        print(f"📝 Creating migration: {message}")

        try:
            cmd = ["alembic", "revision"]
            if autogenerate:
                cmd.extend(["--autogenerate", "-m", message])
            else:
                cmd.extend(["-m", message])

            result = subprocess.run(cmd, cwd=self.database_dir, check=True)
            print("✅ Migration created successfully")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create migration: {e}")
            return False

    def upgrade(self, revision: str = "head") -> bool:
        """Upgrade database to specified revision."""
        print(f"⬆️  Upgrading database to {revision}")

        try:
            result = subprocess.run(
                ["alembic", "upgrade", revision], cwd=self.database_dir, check=True
            )
            print(f"✅ Database upgraded to {revision}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to upgrade database: {e}")
            return False

    def downgrade(self, revision: str) -> bool:
        """Downgrade database to specified revision."""
        print(f"⬇️  Downgrading database to {revision}")

        try:
            result = subprocess.run(
                ["alembic", "downgrade", revision], cwd=self.database_dir, check=True
            )
            print(f"✅ Database downgraded to {revision}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to downgrade database: {e}")
            return False

    def current(self) -> Optional[str]:
        """Get current database revision."""
        try:
            result = subprocess.run(
                ["alembic", "current"],
                cwd=self.database_dir,
                capture_output=True,
                text=True,
                check=True,
            )

            current_rev = result.stdout.strip()
            print(f"📍 Current revision: {current_rev}")
            return current_rev

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to get current revision: {e}")
            return None

    def history(self) -> bool:
        """Show migration history."""
        print("📚 Migration history:")

        try:
            result = subprocess.run(
                ["alembic", "history", "--verbose"], cwd=self.database_dir, check=True
            )
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to show history: {e}")
            return False

    def show(self, revision: str) -> bool:
        """Show migration details."""
        print(f"🔍 Showing migration: {revision}")

        try:
            result = subprocess.run(
                ["alembic", "show", revision], cwd=self.database_dir, check=True
            )
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to show migration: {e}")
            return False

    def stamp(self, revision: str) -> bool:
        """Stamp database with revision without running migrations."""
        print(f"🏷️  Stamping database with {revision}")

        try:
            result = subprocess.run(
                ["alembic", "stamp", revision], cwd=self.database_dir, check=True
            )
            print(f"✅ Database stamped with {revision}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to stamp database: {e}")
            return False

    def merge(self, revisions: List[str], message: str) -> bool:
        """Merge multiple revisions."""
        print(f"🔀 Merging revisions: {', '.join(revisions)}")

        try:
            cmd = ["alembic", "merge"] + revisions + ["-m", message]
            result = subprocess.run(cmd, cwd=self.database_dir, check=True)
            print("✅ Revisions merged successfully")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to merge revisions: {e}")
            return False

    def check_health(self) -> bool:
        """Check database health before/after migrations."""
        print("🏥 Checking database health...")

        results = health_check()
        all_healthy = True

        for service, status in results.items():
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {service}: {'Healthy' if status else 'Unhealthy'}")
            if not status:
                all_healthy = False

        return all_healthy


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python migrate.py <command> [options]")
        print("\nCommands:")
        print("  create <message>     Create a new migration")
        print("  upgrade [revision]   Upgrade to revision (default: head)")
        print("  downgrade <revision> Downgrade to revision")
        print("  current             Show current revision")
        print("  history             Show migration history")
        print("  show <revision>     Show migration details")
        print("  stamp <revision>    Stamp database with revision")
        print("  merge <rev1> <rev2> [message] Merge revisions")
        print("  health              Check database health")
        return

    manager = MigrationManager()
    command = sys.argv[1]

    if command == "create":
        if len(sys.argv) < 3:
            print("❌ Please provide a migration message")
            return
        message = sys.argv[2]
        manager.create_migration(message)

    elif command == "upgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else "head"
        manager.upgrade(revision)

    elif command == "downgrade":
        if len(sys.argv) < 3:
            print("❌ Please provide a revision to downgrade to")
            return
        revision = sys.argv[2]
        manager.downgrade(revision)

    elif command == "current":
        manager.current()

    elif command == "history":
        manager.history()

    elif command == "show":
        if len(sys.argv) < 3:
            print("❌ Please provide a revision to show")
            return
        revision = sys.argv[2]
        manager.show(revision)

    elif command == "stamp":
        if len(sys.argv) < 3:
            print("❌ Please provide a revision to stamp")
            return
        revision = sys.argv[2]
        manager.stamp(revision)

    elif command == "merge":
        if len(sys.argv) < 4:
            print("❌ Please provide at least two revisions to merge")
            return
        revisions = sys.argv[2:-1] if len(sys.argv) > 4 else sys.argv[2:]
        message = sys.argv[-1] if len(sys.argv) > 4 else "Merge revisions"
        manager.merge(revisions, message)

    elif command == "health":
        manager.check_health()

    else:
        print(f"❌ Unknown command: {command}")
        print("Run 'python migrate.py' for usage information")


if __name__ == "__main__":
    main()

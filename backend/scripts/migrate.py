#!/usr/bin/env python3
"""
Migration helper script for F1 Picks application.
Provides convenient commands for database migration management.
"""

import subprocess
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


def run_alembic_command(command: list[str]) -> int:
    """Run an Alembic command and return exit code."""
    try:
        result = subprocess.run(
            ["python", "-m", "alembic"] + command,
            cwd=backend_dir,
            check=False,
            capture_output=False
        )
        return result.returncode
    except Exception as e:
        print(f"Error running Alembic command: {e}")
        return 1


def main():
    """Main CLI function."""
    if len(sys.argv) < 2:
        print("F1 Picks Migration Helper")
        print("=" * 30)
        print("Usage: python scripts/migrate.py <command>")
        print()
        print("Commands:")
        print("  status     - Show current migration status")
        print("  upgrade    - Upgrade to latest migration")
        print("  downgrade  - Downgrade one migration")
        print("  reset      - Reset database (downgrade to base)")
        print("  generate   - Generate new migration from model changes")
        print("  history    - Show migration history")
        print("  check      - Check if migrations are up to date")
        return 1

    command = sys.argv[1].lower()

    if command == "status":
        print("📊 Current migration status:")
        return run_alembic_command(["current", "-v"])

    elif command == "upgrade":
        print("⬆️  Upgrading database to latest migration...")
        return run_alembic_command(["upgrade", "head"])

    elif command == "downgrade":
        print("⬇️  Downgrading database by one migration...")
        return run_alembic_command(["downgrade", "-1"])

    elif command == "reset":
        print("🔄 Resetting database (this will delete all data!)...")
        confirm = input("Are you sure? Type 'yes' to confirm: ")
        if confirm.lower() == 'yes':
            return run_alembic_command(["downgrade", "base"])
        else:
            print("Reset cancelled.")
            return 0

    elif command == "generate":
        if len(sys.argv) < 3:
            print("Error: Please provide a migration message")
            print("Usage: python scripts/migrate.py generate 'migration message'")
            return 1

        message = sys.argv[2]
        print(f"🔧 Generating new migration: {message}")
        return run_alembic_command(["revision", "--autogenerate", "-m", message])

    elif command == "history":
        print("📜 Migration history:")
        return run_alembic_command(["history", "-v"])

    elif command == "check":
        print("✅ Checking migration status...")
        return run_alembic_command(["check"])

    else:
        print(f"Unknown command: {command}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

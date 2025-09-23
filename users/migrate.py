#!/usr/bin/env python3
"""
Database migration management script.
This script helps manage Alembic database migrations.
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a shell command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    
    if result.stdout:
        print("STDOUT:", result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    if result.returncode != 0:
        print(f"Command failed with return code {result.returncode}")
        sys.exit(1)
    
    return result

def check_database_connection():
    """Check if we can connect to the database."""
    try:
        # Try to connect using alembic
        run_command(["alembic", "current"])
        return True
    except:
        print("Cannot connect to database. Make sure PostgreSQL is running.")
        return False

def generate_migration(message=None):
    """Generate a new migration file."""
    if not message:
        message = input("Enter migration message: ").strip()
        if not message:
            message = "auto_migration"
    
    cmd = ["alembic", "revision", "--autogenerate", "-m", message]
    run_command(cmd)
    print(f"Generated migration: {message}")

def run_migrations():
    """Run pending migrations."""
    run_command(["alembic", "upgrade", "head"])
    print("All migrations applied successfully!")

def show_current_revision():
    """Show current database revision."""
    run_command(["alembic", "current", "-v"])

def show_migration_history():
    """Show migration history."""
    run_command(["alembic", "history", "-v"])

def downgrade_migration(revision=""):
    """Downgrade to a specific revision."""
    if not revision:
        revision = input("Enter revision to downgrade to (or 'base' for all): ").strip()
        if not revision:
            revision = "-1"  # Downgrade one step
    
    run_command(["alembic", "downgrade", revision])
    print(f"Downgraded to revision: {revision}")

def main():
    """Main migration management interface."""
    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "generate" or command == "g":
            message = sys.argv[2] if len(sys.argv) > 2 else None
            generate_migration(message)
        elif command == "migrate" or command == "m":
            run_migrations()
        elif command == "current" or command == "c":
            show_current_revision()
        elif command == "history" or command == "h":
            show_migration_history()
        elif command == "downgrade" or command == "d":
            revision = sys.argv[2] if len(sys.argv) > 2 else ""
            downgrade_migration(revision)
        elif command == "init":
            # Generate initial migration
            generate_migration("initial_migration")
        else:
            print(f"Unknown command: {command}")
            show_help()
    else:
        show_help()

def show_help():
    """Show help information."""
    print("""
Database Migration Management

Usage: python migrate.py <command> [args]

Commands:
  init                    - Generate initial migration
  generate <message>      - Generate new migration (alias: g)
  migrate                 - Run all pending migrations (alias: m)
  current                 - Show current revision (alias: c)
  history                 - Show migration history (alias: h)
  downgrade <revision>    - Downgrade to revision (alias: d)

Examples:
  python migrate.py init
  python migrate.py generate "add user profiles"
  python migrate.py migrate
  python migrate.py current
  python migrate.py downgrade -1
  
Environment Variables:
  DATABASE_URL - Database connection string
                 Default: postgresql+asyncpg://appuser:apppass@localhost:5432/appdb
    """)

if __name__ == "__main__":
    main()

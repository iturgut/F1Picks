#!/usr/bin/env python3
"""
Database setup script for F1 Picks application.
Handles both Alembic and Supabase migration scenarios.
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text

from app.database import get_db_session


async def check_database_exists():
    """Check if database tables exist."""
    async with get_db_session() as session:
        try:
            result = await session.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
            tables = [row[0] for row in result.fetchall()]
            return len(tables) > 0, tables
        except Exception as e:
            print(f"Error checking database: {e}")
            return False, []


async def check_alembic_version():
    """Check current Alembic version."""
    async with get_db_session() as session:
        try:
            result = await session.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()
            return version
        except Exception:
            return None


async def create_alembic_version_table():
    """Create alembic_version table and set current version."""
    async with get_db_session() as session:
        try:
            # Create alembic_version table
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS alembic_version (
                    version_num VARCHAR(32) NOT NULL,
                    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                )
            """))

            # Insert current version (from our migration file)
            await session.execute(text("""
                INSERT INTO alembic_version (version_num) 
                VALUES ('fc1bcaffb6b3')
                ON CONFLICT (version_num) DO NOTHING
            """))

            await session.commit()
            print("✓ Alembic version table created and synced")
        except Exception as e:
            print(f"Error creating alembic version table: {e}")
            await session.rollback()


async def main():
    """Main setup function."""
    print("🏁 F1 Picks Database Setup")
    print("=" * 40)

    # Check if database has tables
    has_tables, tables = await check_database_exists()

    if has_tables:
        print(f"✓ Database exists with {len(tables)} tables: {', '.join(tables[:5])}{'...' if len(tables) > 5 else ''}")

        # Check if this is a Supabase-managed database
        if 'users' in tables and 'events' in tables:
            print("✓ Detected Supabase-managed database")

            # Check Alembic version
            version = await check_alembic_version()
            if version:
                print(f"✓ Alembic version: {version}")
            else:
                print("⚠ Alembic version table missing - creating...")
                await create_alembic_version_table()
        else:
            print("⚠ Database exists but schema doesn't match expected F1 Picks schema")
    else:
        print("⚠ Database is empty - run migrations to create schema")
        print("Run: python -m alembic upgrade head")

    # Test database connection
    try:
        async with get_db_session() as session:
            result = await session.execute(text("SELECT 1"))
            print("✓ Database connection successful")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return 1

    print("\n🎯 Setup complete!")
    print("\nNext steps:")
    print("1. If using Supabase: supabase db reset --with-seed")
    print("2. If using Alembic: python -m alembic upgrade head")
    print("3. Start the FastAPI server: uvicorn app.main:app --reload")

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

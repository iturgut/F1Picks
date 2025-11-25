#!/usr/bin/env python3
"""
Ingest 2025 F1 season schedule into the database.
"""
import asyncio

from app.database import init_db, close_db
from app.ingestion import ingestion_service
from app.logger import logger


async def main():
    """Ingest 2025 season schedule."""
    print("=" * 70)
    print("Ingesting 2025 F1 Season Schedule")
    print("=" * 70)
    
    try:
        # Initialize database connection
        logger.info("Connecting to database...")
        await init_db()
        
        # Ingest the schedule
        logger.info("Fetching 2025 season schedule from FastF1...")
        events_created = await ingestion_service.ingest_season_schedule(2025)
        
        print("\n" + "=" * 70)
        print(f"✓ Successfully ingested 2025 schedule!")
        print(f"  Events created/updated: {events_created}")
        print("=" * 70)
        print("\nYou can now:")
        print("  1. View events in your database")
        print("  2. Start the frontend to see upcoming races")
        print("  3. Make predictions before races start")
        print("=" * 70)
        
    except Exception as e:
        logger.error(f"Failed to ingest schedule: {e}")
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("  1. PostgreSQL is running")
        print("  2. Database exists (f1picks)")
        print("  3. DATABASE_URL is set correctly in .env")
        print("  4. Database migrations have been run")
        return 1
    
    finally:
        await close_db()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

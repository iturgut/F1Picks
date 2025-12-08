#!/usr/bin/env python3
"""
Master data ingestion script for F1Picks.

This script handles:
1. Ingesting the current season schedule
2. Polling for and ingesting results from completed events
3. Triggering scoring for events with new results

Usage:
    python ingest_all.py [--year YEAR] [--force-rescore]
"""
import argparse
import asyncio
import sys
from datetime import datetime, timezone

from sqlalchemy import select
from app.database import init_db, close_db, get_db_session, Event, EventStatus
from app.ingestion import ingestion_service
from app.logger import logger


async def ingest_schedule(year: int) -> int:
    """
    Ingest season schedule.
    
    Args:
        year: Season year to ingest
        
    Returns:
        Number of events created/updated
    """
    logger.info(f"Ingesting {year} season schedule...")
    try:
        events_count = await ingestion_service.ingest_season_schedule(year)
        logger.info(f"Schedule ingestion complete", events_created=events_count)
        return events_count
    except Exception as e:
        logger.error(f"Failed to ingest schedule: {e}", exc_info=True)
        return 0


async def ingest_results() -> tuple[int, int]:
    """
    Poll for and ingest results from completed events.
    
    Returns:
        Tuple of (events_checked, results_ingested)
    """
    logger.info("Polling for results from completed events...")
    
    events_checked = 0
    results_ingested = 0
    
    try:
        async for session in get_db_session():
            # Find completed events (qualifying and races only)
            query = select(Event).where(
                Event.status == EventStatus.COMPLETED,
                Event.session_type.in_(['qualifying', 'race', 'sprint'])
            ).order_by(Event.start_time.desc()).limit(20)
            
            result = await session.execute(query)
            completed_events = result.scalars().all()
        
        if not completed_events:
            logger.info("No completed events found")
            return 0, 0
        
        logger.info(f"Found {len(completed_events)} completed events to check")
        
        for event in completed_events:
            events_checked += 1
            logger.info(
                f"Checking event: {event.name} ({event.session_type.value})",
                event_id=str(event.id)
            )
            
            # Poll for results
            success = await ingestion_service.poll_for_session_data(event.id)
            if success:
                results_ingested += 1
                logger.info(
                    f"✓ Ingested results for {event.name}",
                    event_id=str(event.id)
                )
            else:
                logger.debug(
                    f"No new results for {event.name}",
                    event_id=str(event.id)
                )
        
        return events_checked, results_ingested
        
    except Exception as e:
        logger.error(f"Failed to poll for results: {e}", exc_info=True)
        return events_checked, results_ingested


async def trigger_scoring_for_recent_events(force: bool = False) -> int:
    """
    Trigger scoring for recently completed events.
    
    Note: Scoring is handled by the backend API when users view their picks.
    This function is kept for future use if we want to pre-calculate scores.
    
    Args:
        force: If True, rescore all events even if already scored
        
    Returns:
        Number of events scored (always 0 for now)
    """
    logger.info("Scoring is handled by the backend API - skipping")
    return 0


async def main():
    """Main ingestion workflow."""
    parser = argparse.ArgumentParser(
        description='Ingest F1 data and update scores'
    )
    parser.add_argument(
        '--year',
        type=int,
        default=datetime.now().year,
        help='Season year to ingest (default: current year)'
    )
    parser.add_argument(
        '--force-rescore',
        action='store_true',
        help='Force rescoring of all events'
    )
    parser.add_argument(
        '--skip-schedule',
        action='store_true',
        help='Skip schedule ingestion'
    )
    parser.add_argument(
        '--skip-results',
        action='store_true',
        help='Skip results ingestion'
    )
    parser.add_argument(
        '--skip-scoring',
        action='store_true',
        help='Skip scoring'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("F1Picks Data Ingestion")
    print("=" * 70)
    print(f"Year: {args.year}")
    print(f"Time: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 70)
    
    try:
        await init_db()
        
        # Step 1: Ingest schedule
        if not args.skip_schedule:
            print("\n[1/3] Ingesting season schedule...")
            events_count = await ingest_schedule(args.year)
            print(f"✓ Schedule ingestion complete: {events_count} events")
        else:
            print("\n[1/3] Skipping schedule ingestion")
        
        # Step 2: Ingest results
        if not args.skip_results:
            print("\n[2/3] Polling for results...")
            events_checked, results_ingested = await ingest_results()
            print(f"✓ Results polling complete: {results_ingested}/{events_checked} events had new results")
        else:
            print("\n[2/3] Skipping results ingestion")
        
        # Step 3: Trigger scoring
        if not args.skip_scoring:
            print("\n[3/3] Triggering scoring...")
            scored_count = await trigger_scoring_for_recent_events(args.force_rescore)
            print(f"✓ Scoring complete: {scored_count} events scored")
        else:
            print("\n[3/3] Skipping scoring")
        
        print("\n" + "=" * 70)
        print("✅ Data ingestion complete!")
        print("=" * 70)
        
        return 0
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        return 1
        
    finally:
        await close_db()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

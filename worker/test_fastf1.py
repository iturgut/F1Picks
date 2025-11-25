#!/usr/bin/env python3
"""
Simple test script to verify FastF1 integration works.
"""
import asyncio
from datetime import datetime

from app.fastf1_client import fastf1_client
from app.logger import logger


async def test_season_schedule():
    """Test fetching the season schedule."""
    logger.info("Testing season schedule fetch")
    
    year = 2024
    schedule = await fastf1_client.get_season_schedule(year)
    
    logger.info(f"Found {len(schedule)} events for {year}")
    
    # Show first few events
    print("\nFirst 5 events:")
    for idx, row in schedule.head(5).iterrows():
        print(f"  Round {row['RoundNumber']}: {row['EventName']} at {row['Location']}")
    
    return schedule


async def test_session_data():
    """Test fetching session data for a completed race."""
    logger.info("Testing session data fetch")
    
    # Try to fetch data from a recent completed race
    # Las Vegas GP 2024 (Round 22)
    year = 2024
    round_number = 22
    session_type = 'R'  # Race
    
    logger.info(f"Attempting to fetch {year} Round {round_number} Race data")
    
    session = await fastf1_client.get_session_data(year, round_number, session_type)
    
    if session:
        logger.info("Session data loaded successfully!")
        
        # Extract and display results
        results = fastf1_client.extract_race_results(session)
        
        print(f"\nRace Results (Top 10):")
        for result in results[:10]:
            pos = result.get('position', 'N/A')
            driver = result.get('driver_name', 'Unknown')
            team = result.get('team_name', 'Unknown')
            status = result.get('status', 'Unknown')
            print(f"  P{pos}: {driver} ({team}) - {status}")
        
        # Get fastest lap
        fastest = fastf1_client.extract_fastest_lap(session)
        if fastest:
            print(f"\nFastest Lap:")
            print(f"  Driver: {fastest['driver_number']}")
            print(f"  Time: {fastest['lap_time']}")
            print(f"  Lap: {fastest['lap_number']}")
        
        return True
    else:
        logger.warning("Session data not available yet")
        return False


async def main():
    """Run tests."""
    print("=" * 60)
    print("FastF1 Integration Test")
    print("=" * 60)
    
    try:
        # Test 1: Season Schedule
        print("\n[Test 1] Fetching Season Schedule...")
        schedule = await test_season_schedule()
        print("✓ Season schedule fetch successful")
        
        # Test 2: Session Data
        print("\n[Test 2] Fetching Session Data...")
        success = await test_session_data()
        
        if success:
            print("✓ Session data fetch successful")
        else:
            print("⚠ Session data not yet available (this is normal if race just finished)")
        
        print("\n" + "=" * 60)
        print("Tests Complete!")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

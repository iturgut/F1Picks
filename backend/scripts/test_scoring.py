"""
Manual scoring test script.

This script creates sample events, picks, and results, then triggers scoring
to verify the entire scoring pipeline works correctly.

Usage:
    python -m scripts.test_scoring
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.database import get_db_session
from app.models.event import Event, EventType, EventStatus
from app.models.pick import Pick, PropType
from app.models.result import Result, ResultSource
from app.models.user import User
from app.scoring.service import ScoringService


async def create_test_user() -> User:
    """Create a test user."""
    async with get_db_session() as session:
        # Check if test user exists
        query = select(User).where(User.email == "test@f1picks.com")
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        
        if user:
            print(f"✓ Using existing test user: {user.id}")
            return user
        
        # Create new test user
        user = User(
            id=uuid4(),
            email="test@f1picks.com",
            name="Test User"
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        print(f"✓ Created test user: {user.id}")
        return user


async def create_test_event() -> Event:
    """Create a test event."""
    async with get_db_session() as session:
        event = Event(
            id=uuid4(),
            name="Test Grand Prix - Race",
            circuit_id="test-circuit",
            circuit_name="Test Circuit",
            session_type=EventType.RACE,
            round_number=1,
            year=2024,
            start_time=datetime.utcnow() - timedelta(hours=3),
            end_time=datetime.utcnow() - timedelta(hours=1),
            status=EventStatus.COMPLETED
        )
        session.add(event)
        await session.commit()
        await session.refresh(event)
        
        print(f"✓ Created test event: {event.id}")
        return event


async def create_test_picks(user: User, event: Event) -> list[Pick]:
    """Create test picks for various prediction types."""
    async with get_db_session() as session:
        picks = [
            # Race winner - exact match
            Pick(
                id=uuid4(),
                user_id=user.id,
                event_id=event.id,
                prop_type=PropType.RACE_WINNER,
                prop_value="VER",
                prop_metadata={"confidence": "high"}
            ),
            # Podium P2 - off by one
            Pick(
                id=uuid4(),
                user_id=user.id,
                event_id=event.id,
                prop_type=PropType.PODIUM_P2,
                prop_value="LEC",
                prop_metadata={"confidence": "medium"}
            ),
            # Podium P3 - exact match
            Pick(
                id=uuid4(),
                user_id=user.id,
                event_id=event.id,
                prop_type=PropType.PODIUM_P3,
                prop_value="NOR",
                prop_metadata={"confidence": "low"}
            ),
            # Fastest lap - near miss
            Pick(
                id=uuid4(),
                user_id=user.id,
                event_id=event.id,
                prop_type=PropType.FASTEST_LAP,
                prop_value="HAM",
                prop_metadata={}
            ),
            # Lap time prediction
            Pick(
                id=uuid4(),
                user_id=user.id,
                event_id=event.id,
                prop_type=PropType.LAP_TIME_PREDICTION,
                prop_value="90.5",
                prop_metadata={"lap": 1}
            ),
            # Pit window start
            Pick(
                id=uuid4(),
                user_id=user.id,
                event_id=event.id,
                prop_type=PropType.PIT_WINDOW_START,
                prop_value="15",
                prop_metadata={"driver": "VER"}
            ),
            # Safety car prediction
            Pick(
                id=uuid4(),
                user_id=user.id,
                event_id=event.id,
                prop_type=PropType.SAFETY_CAR,
                prop_value="true",
                prop_metadata={}
            ),
            # Total pit stops
            Pick(
                id=uuid4(),
                user_id=user.id,
                event_id=event.id,
                prop_type=PropType.TOTAL_PIT_STOPS,
                prop_value="3",
                prop_metadata={}
            ),
        ]
        
        for pick in picks:
            session.add(pick)
        
        await session.commit()
        
        print(f"✓ Created {len(picks)} test picks")
        return picks


async def create_test_results(event: Event) -> list[Result]:
    """Create test results."""
    async with get_db_session() as session:
        results = [
            # Race winner
            Result(
                id=uuid4(),
                event_id=event.id,
                prop_type=PropType.RACE_WINNER,
                actual_value="VER",
                result_metadata={
                    "finishing_order": {
                        "VER": 1,
                        "HAM": 2,
                        "LEC": 3,
                        "NOR": 4,
                        "SAI": 5
                    }
                },
                source=ResultSource.MANUAL
            ),
            # Podium P2
            Result(
                id=uuid4(),
                event_id=event.id,
                prop_type=PropType.PODIUM_P2,
                actual_value="HAM",
                result_metadata={
                    "finishing_order": {
                        "VER": 1,
                        "HAM": 2,
                        "LEC": 3,
                        "NOR": 4,
                        "SAI": 5
                    }
                },
                source=ResultSource.MANUAL
            ),
            # Podium P3
            Result(
                id=uuid4(),
                event_id=event.id,
                prop_type=PropType.PODIUM_P3,
                actual_value="NOR",
                result_metadata={
                    "finishing_order": {
                        "VER": 1,
                        "HAM": 2,
                        "LEC": 3,
                        "NOR": 4,
                        "SAI": 5
                    }
                },
                source=ResultSource.MANUAL
            ),
            # Fastest lap
            Result(
                id=uuid4(),
                event_id=event.id,
                prop_type=PropType.FASTEST_LAP,
                actual_value="VER",
                result_metadata={
                    "lap_times": {
                        "VER": 89.123,
                        "HAM": 89.456,
                        "LEC": 89.789,
                        "NOR": 90.012
                    }
                },
                source=ResultSource.MANUAL
            ),
            # Lap time
            Result(
                id=uuid4(),
                event_id=event.id,
                prop_type=PropType.LAP_TIME_PREDICTION,
                actual_value="90.8",
                result_metadata={"lap": 1},
                source=ResultSource.MANUAL
            ),
            # Pit window
            Result(
                id=uuid4(),
                event_id=event.id,
                prop_type=PropType.PIT_WINDOW_START,
                actual_value="16",
                result_metadata={"driver": "VER"},
                source=ResultSource.MANUAL
            ),
            # Safety car
            Result(
                id=uuid4(),
                event_id=event.id,
                prop_type=PropType.SAFETY_CAR,
                actual_value="true",
                result_metadata={},
                source=ResultSource.MANUAL
            ),
            # Total pit stops
            Result(
                id=uuid4(),
                event_id=event.id,
                prop_type=PropType.TOTAL_PIT_STOPS,
                actual_value="4",
                result_metadata={},
                source=ResultSource.MANUAL
            ),
        ]
        
        for result in results:
            session.add(result)
        
        await session.commit()
        
        print(f"✓ Created {len(results)} test results")
        return results


async def run_scoring(event: Event):
    """Run scoring for the test event."""
    async with get_db_session() as session:
        scoring_service = ScoringService(session)
        
        print(f"\n🏁 Running scoring for event {event.id}...")
        result = await scoring_service.score_event(event.id)
        
        print(f"\n✓ Scoring complete!")
        print(f"  - Picks scored: {result['picks_scored']}")
        print(f"  - Scores created: {result['scores_created']}")
        print(f"  - Scores updated: {result['scores_updated']}")
        print(f"  - Total points: {result['total_points']}")
        
        return result


async def display_scores(event: Event):
    """Display the calculated scores."""
    async with get_db_session() as session:
        scoring_service = ScoringService(session)
        scores = await scoring_service.get_event_scores(event.id, limit=100)
        
        print(f"\n📊 Detailed Scores:")
        print("=" * 80)
        
        for score in scores:
            print(f"\n{score['prop_type'].upper()}")
            print(f"  Predicted: {score['predicted_value']}")
            print(f"  Points: {score['points']}")
            print(f"  Margin: {score['margin']}")
            print(f"  Exact Match: {score['exact_match']}")
            if score['metadata']:
                print(f"  Details: {score['metadata']}")


async def cleanup_test_data(event: Event, user: User):
    """Clean up test data."""
    async with get_db_session() as session:
        # Delete event (cascades to picks, results, scores)
        await session.delete(event)
        
        # Optionally delete test user
        # await session.delete(user)
        
        await session.commit()
        print(f"\n✓ Cleaned up test data")


async def main():
    """Run the scoring test."""
    print("=" * 80)
    print("F1 Picks Scoring System Test")
    print("=" * 80)
    
    try:
        # Create test data
        print("\n📝 Creating test data...")
        user = await create_test_user()
        event = await create_test_event()
        picks = await create_test_picks(user, event)
        results = await create_test_results(event)
        
        # Run scoring
        await run_scoring(event)
        
        # Display results
        await display_scores(event)
        
        # Summary
        print("\n" + "=" * 80)
        print("Expected Results:")
        print("=" * 80)
        print("1. Race Winner (VER → VER): 10 points (exact match)")
        print("2. Podium P2 (LEC → HAM): 7 points (off by 1 position)")
        print("3. Podium P3 (NOR → NOR): 10 points (exact match)")
        print("4. Fastest Lap (HAM → VER): 7 points (within 0.5s)")
        print("5. Lap Time (90.5 → 90.8): 8 points (within 1%)")
        print("6. Pit Window (15 → 16): 7 points (off by 1 lap)")
        print("7. Safety Car (true → true): 10 points (exact match)")
        print("8. Total Pit Stops (3 → 4): 6 points (off by 1)")
        print("\nExpected Total: 65 points")
        print("=" * 80)
        
        # Cleanup
        cleanup = input("\n🗑️  Delete test data? (y/N): ")
        if cleanup.lower() == 'y':
            await cleanup_test_data(event, user)
        else:
            print(f"\n✓ Test data preserved:")
            print(f"  - Event ID: {event.id}")
            print(f"  - User ID: {user.id}")
        
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

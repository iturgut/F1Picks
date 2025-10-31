#!/usr/bin/env python3
"""
Development data seeding script for F1 Picks application.
Creates sample data for local development and testing.
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.database import get_db_session
from app.models import Event, League, Pick, User
from app.models.event import EventStatus, EventType
from app.models.pick import PropType


async def create_sample_users():
    """Create sample users for development."""
    users_data = [
        {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "email": "alice@example.com",
            "name": "Alice Johnson",
            "photo_url": "https://example.com/alice.jpg"
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440002",
            "email": "bob@example.com",
            "name": "Bob Smith",
            "photo_url": "https://example.com/bob.jpg"
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440003",
            "email": "charlie@example.com",
            "name": "Charlie Brown",
            "photo_url": None
        }
    ]

    async with get_db_session() as session:
        for user_data in users_data:
            # Check if user already exists
            existing = await session.get(User, user_data["id"])
            if not existing:
                user = User(**user_data)
                session.add(user)

        await session.commit()
        print(f"✓ Created {len(users_data)} sample users")


async def create_sample_leagues():
    """Create sample leagues."""
    async with get_db_session() as session:
        # Create private league
        private_league_id = "660e8400-e29b-41d4-a716-446655440001"
        existing = await session.get(League, private_league_id)

        if not existing:
            private_league = League(
                id=private_league_id,
                name="Friends League",
                description="Private league for friends",
                is_global=False
            )
            session.add(private_league)
            await session.commit()
            print("✓ Created private league")


async def create_sample_events():
    """Create sample F1 events."""
    now = datetime.utcnow()

    events_data = [
        {
            "id": "770e8400-e29b-41d4-a716-446655440001",
            "name": "Las Vegas Grand Prix - Qualifying",
            "circuit_id": "las_vegas",
            "circuit_name": "Las Vegas Street Circuit",
            "session_type": EventType.QUALIFYING,
            "round_number": 22,
            "year": 2024,
            "start_time": now + timedelta(days=7),
            "end_time": now + timedelta(days=7, hours=1),
            "status": EventStatus.SCHEDULED
        },
        {
            "id": "770e8400-e29b-41d4-a716-446655440002",
            "name": "Las Vegas Grand Prix - Race",
            "circuit_id": "las_vegas",
            "circuit_name": "Las Vegas Street Circuit",
            "session_type": EventType.RACE,
            "round_number": 22,
            "year": 2024,
            "start_time": now + timedelta(days=8),
            "end_time": now + timedelta(days=8, hours=2),
            "status": EventStatus.SCHEDULED
        },
        {
            "id": "770e8400-e29b-41d4-a716-446655440007",
            "name": "Brazilian Grand Prix - Race",
            "circuit_id": "interlagos",
            "circuit_name": "Autódromo José Carlos Pace",
            "session_type": EventType.RACE,
            "round_number": 21,
            "year": 2024,
            "start_time": now - timedelta(days=7),
            "end_time": now - timedelta(days=7, hours=-2),
            "status": EventStatus.COMPLETED
        }
    ]

    async with get_db_session() as session:
        for event_data in events_data:
            existing = await session.get(Event, event_data["id"])
            if not existing:
                event = Event(**event_data)
                session.add(event)

        await session.commit()
        print(f"✓ Created {len(events_data)} sample events")


async def create_sample_picks():
    """Create sample picks."""
    picks_data = [
        {
            "user_id": "550e8400-e29b-41d4-a716-446655440001",
            "event_id": "770e8400-e29b-41d4-a716-446655440002",
            "prop_type": PropType.RACE_WINNER,
            "prop_value": "Max Verstappen",
            "prop_metadata": {"confidence": 0.8}
        },
        {
            "user_id": "550e8400-e29b-41d4-a716-446655440002",
            "event_id": "770e8400-e29b-41d4-a716-446655440002",
            "prop_type": PropType.RACE_WINNER,
            "prop_value": "Charles Leclerc",
            "prop_metadata": {"confidence": 0.9}
        }
    ]

    async with get_db_session() as session:
        for pick_data in picks_data:
            pick = Pick(**pick_data)
            session.add(pick)

        await session.commit()
        print(f"✓ Created {len(picks_data)} sample picks")


async def main():
    """Main seeding function."""
    print("🌱 Seeding F1 Picks development data")
    print("=" * 40)

    try:
        await create_sample_users()
        await create_sample_leagues()
        await create_sample_events()
        await create_sample_picks()

        print("\n🎯 Development data seeding complete!")
        print("You can now test the application with sample data.")

    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

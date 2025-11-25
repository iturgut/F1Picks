"""
Event repository for database operations.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.event import Event
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class EventRepository(BaseRepository[Event]):
    """Repository for Event model operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Event, session)

    async def get_by_season_and_round(self, season: int, round_number: int) -> Optional[Event]:
        """
        Get event by season and round number.
        
        Args:
            season: F1 season year
            round_number: Round number in season
            
        Returns:
            Event instance or None if not found
        """
        query = select(Event).where(
            and_(
                Event.season == season,
                Event.round_number == round_number
            )
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_current_season_events(self, season: Optional[int] = None) -> List[Event]:
        """
        Get all events for a season (current year if not specified).
        
        Args:
            season: F1 season year (defaults to current year)
            
        Returns:
            List of events for the season
        """
        if season is None:
            season = datetime.now(timezone.utc).year

        return await self.get_all(
            filters={"season": season},
            order_by="round_number"
        )

    async def get_upcoming_events(self, limit: int = 10) -> List[Event]:
        """
        Get upcoming events (not yet finished).
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of upcoming events
        """
        now = datetime.now(timezone.utc)

        query = (
            select(Event)
            .where(
                or_(
                    Event.race_datetime > now,
                    Event.status.in_(["scheduled", "practice", "qualifying"])
                )
            )
            .order_by(Event.race_datetime)
            .limit(limit)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_completed_events(self, season: Optional[int] = None, limit: int = 50) -> List[Event]:
        """
        Get completed events.
        
        Args:
            season: Optional season filter
            limit: Maximum number of events to return
            
        Returns:
            List of completed events
        """
        filters = {"status": "completed"}
        if season:
            filters["season"] = season

        return await self.get_all(
            filters=filters,
            order_by="-race_datetime",
            limit=limit
        )

    async def get_events_with_picks(self, user_id: UUID, season: Optional[int] = None) -> List[Event]:
        """
        Get events with user's picks.
        
        Args:
            user_id: User ID
            season: Optional season filter
            
        Returns:
            List of events with picks loaded
        """
        query = select(Event).options(
            selectinload(Event.picks).where(Event.picks.property.mapper.class_.user_id == user_id)
        )

        if season:
            query = query.where(Event.season == season)

        query = query.order_by(Event.race_datetime)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_events_with_results(self, season: Optional[int] = None) -> List[Event]:
        """
        Get events with results loaded.
        
        Args:
            season: Optional season filter
            
        Returns:
            List of events with results
        """
        query = select(Event).options(selectinload(Event.results))

        if season:
            query = query.where(Event.season == season)

        query = query.order_by(Event.race_datetime)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_next_event(self) -> Optional[Event]:
        """
        Get the next upcoming event.
        
        Returns:
            Next event or None if no upcoming events
        """
        upcoming = await self.get_upcoming_events(limit=1)
        return upcoming[0] if upcoming else None

    async def get_current_event(self) -> Optional[Event]:
        """
        Get the current event (happening now or recently finished).
        
        Returns:
            Current event or None
        """
        now = datetime.now(timezone.utc)

        # Look for events in the current weekend (Friday to Sunday + 1 day)
        query = (
            select(Event)
            .where(
                and_(
                    Event.race_datetime >= now - timezone.utc.localize(datetime.now()).replace(days=3),
                    Event.race_datetime <= now + timezone.utc.localize(datetime.now()).replace(days=1)
                )
            )
            .order_by(Event.race_datetime.desc())
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_event_status(self, event_id: UUID, status: str) -> Optional[Event]:
        """
        Update event status.
        
        Args:
            event_id: Event ID
            status: New status
            
        Returns:
            Updated event or None if not found
        """
        return await self.update(event_id, status=status)

    async def search_events(self, search_term: str, season: Optional[int] = None) -> List[Event]:
        """
        Search events by name or location.
        
        Args:
            search_term: Search term
            season: Optional season filter
            
        Returns:
            List of matching events
        """
        query = select(Event)

        # Add season filter if provided
        if season:
            query = query.where(Event.season == season)

        # Search in name and location
        search_conditions = [
            Event.name.ilike(f"%{search_term}%"),
            Event.location.ilike(f"%{search_term}%"),
            Event.country.ilike(f"%{search_term}%")
        ]

        query = query.where(or_(*search_conditions)).order_by(Event.race_datetime)

        result = await self.session.execute(query)
        return list(result.scalars().all())

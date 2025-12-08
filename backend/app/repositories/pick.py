"""
Pick repository for database operations.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.pick import Pick
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class PickRepository(BaseRepository[Pick]):
    """Repository for Pick model operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Pick, session)

    async def get_user_pick_for_event(self, user_id: UUID, event_id: UUID) -> Optional[Pick]:
        """
        Get user's pick for a specific event.
        
        Args:
            user_id: User ID
            event_id: Event ID
            
        Returns:
            Pick instance or None if not found
        """
        query = select(Pick).where(
            and_(
                Pick.user_id == user_id,
                Pick.event_id == event_id
            )
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_event_picks(self, event_id: UUID, load_users: bool = False) -> List[Pick]:
        """
        Get all picks for an event.
        
        Args:
            event_id: Event ID
            load_users: Whether to load user information
            
        Returns:
            List of picks for the event
        """
        query = select(Pick).where(Pick.event_id == event_id)

        if load_users:
            query = query.options(selectinload(Pick.user))

        query = query.order_by(Pick.created_at)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_user_picks(
        self,
        user_id: UUID,
        season: Optional[int] = None,
        load_events: bool = False
    ) -> List[Pick]:
        """
        Get all picks for a user.
        
        Args:
            user_id: User ID
            season: Optional season filter
            load_events: Whether to load event information
            
        Returns:
            List of user's picks
        """
        query = select(Pick).where(Pick.user_id == user_id)

        if load_events:
            query = query.options(selectinload(Pick.event))
            if season:
                query = query.join(Pick.event).where(Pick.event.has(season=season))

        query = query.order_by(Pick.created_at.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_league_picks(
        self,
        league_id: UUID,
        event_id: Optional[UUID] = None,
        load_users: bool = False
    ) -> List[Pick]:
        """
        Get picks from all members of a league.
        
        Args:
            league_id: League ID
            event_id: Optional event ID filter
            load_users: Whether to load user information
            
        Returns:
            List of picks from league members
        """
        from app.models.league import LeagueMember

        query = (
            select(Pick)
            .join(LeagueMember, Pick.user_id == LeagueMember.user_id)
            .where(LeagueMember.league_id == league_id)
        )

        if event_id:
            query = query.where(Pick.event_id == event_id)

        if load_users:
            query = query.options(selectinload(Pick.user))

        query = query.order_by(Pick.created_at)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create_or_update_pick(
        self,
        user_id: UUID,
        event_id: UUID,
        predictions: Dict[str, Any],
        confidence: Optional[int] = None
    ) -> Pick:
        """
        Create a new pick or update existing one for user and event.
        
        Args:
            user_id: User ID
            event_id: Event ID
            predictions: Pick predictions data
            confidence: Confidence level (1-10)
            
        Returns:
            Created or updated Pick instance
        """
        existing_pick = await self.get_user_pick_for_event(user_id, event_id)

        if existing_pick:
            # Update existing pick
            existing_pick.predictions = predictions
            existing_pick.confidence = confidence
            # updated_at will be automatically set by onupdate

            await self.session.flush()
            await self.session.refresh(existing_pick)

            logger.debug(f"Updated pick for user {user_id}, event {event_id}")
            return existing_pick
        else:
            # Create new pick
            new_pick = Pick(
                user_id=user_id,
                event_id=event_id,
                predictions=predictions,
                confidence=confidence
                # created_at will be automatically set by server_default
            )

            self.session.add(new_pick)
            await self.session.flush()
            await self.session.refresh(new_pick)

            logger.debug(f"Created pick for user {user_id}, event {event_id}")
            return new_pick

    async def get_picks_by_prediction_type(
        self,
        event_id: UUID,
        prediction_type: str
    ) -> List[Pick]:
        """
        Get picks that contain a specific prediction type.
        
        Args:
            event_id: Event ID
            prediction_type: Type of prediction to filter by
            
        Returns:
            List of picks containing the prediction type
        """
        query = (
            select(Pick)
            .where(
                and_(
                    Pick.event_id == event_id,
                    Pick.predictions.has_key(prediction_type)
                )
            )
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pick_statistics(self, event_id: UUID) -> Dict[str, Any]:
        """
        Get statistics for picks on an event.
        
        Args:
            event_id: Event ID
            
        Returns:
            Dictionary with pick statistics
        """
        # Get total pick count
        total_picks = await self.count({"event_id": event_id})

        # Get average confidence
        query = select(func.avg(Pick.confidence)).where(
            and_(
                Pick.event_id == event_id,
                Pick.confidence.is_not(None)
            )
        )
        result = await self.session.execute(query)
        avg_confidence = result.scalar()

        return {
            "total_picks": total_picks,
            "average_confidence": float(avg_confidence) if avg_confidence else None,
        }

    async def get_user_pick_history(
        self,
        user_id: UUID,
        limit: int = 50
    ) -> List[Pick]:
        """
        Get user's recent pick history.
        
        Args:
            user_id: User ID
            limit: Maximum number of picks to return
            
        Returns:
            List of recent picks with events loaded
        """
        query = (
            select(Pick)
            .options(selectinload(Pick.event))
            .where(Pick.user_id == user_id)
            .order_by(Pick.submitted_at.desc())
            .limit(limit)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete_user_pick(self, user_id: UUID, event_id: UUID) -> bool:
        """
        Delete a user's pick for an event.
        
        Args:
            user_id: User ID
            event_id: Event ID
            
        Returns:
            True if deleted, False if not found
        """
        pick = await self.get_user_pick_for_event(user_id, event_id)
        if not pick:
            return False

        await self.session.delete(pick)
        logger.debug(f"Deleted pick for user {user_id}, event {event_id}")
        return True

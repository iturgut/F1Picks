"""
Score repository for database operations.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.score import Score
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ScoreRepository(BaseRepository[Score]):
    """Repository for Score model operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Score, session)

    async def get_user_score_for_event(self, user_id: UUID, event_id: UUID) -> Optional[Score]:
        """
        Get user's score for a specific event.
        
        Args:
            user_id: User ID
            event_id: Event ID
            
        Returns:
            Score instance or None if not found
        """
        query = select(Score).where(
            and_(
                Score.user_id == user_id,
                Score.event_id == event_id
            )
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_event_scores(self, event_id: UUID, load_users: bool = False) -> List[Score]:
        """
        Get all scores for an event, ordered by total points descending.
        
        Args:
            event_id: Event ID
            load_users: Whether to load user information
            
        Returns:
            List of scores for the event
        """
        query = select(Score).where(Score.event_id == event_id)

        if load_users:
            query = query.options(selectinload(Score.user))

        query = query.order_by(desc(Score.total_points))

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_user_scores(
        self,
        user_id: UUID,
        season: Optional[int] = None,
        load_events: bool = False
    ) -> List[Score]:
        """
        Get all scores for a user.
        
        Args:
            user_id: User ID
            season: Optional season filter
            load_events: Whether to load event information
            
        Returns:
            List of user's scores
        """
        query = select(Score).where(Score.user_id == user_id)

        if load_events:
            query = query.options(selectinload(Score.event))
            if season:
                query = query.join(Score.event).where(Score.event.has(season=season))

        query = query.order_by(desc(Score.calculated_at))

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_league_scores(
        self,
        league_id: UUID,
        event_id: Optional[UUID] = None,
        season: Optional[int] = None,
        load_users: bool = False
    ) -> List[Score]:
        """
        Get scores from all members of a league.
        
        Args:
            league_id: League ID
            event_id: Optional event ID filter
            season: Optional season filter
            load_users: Whether to load user information
            
        Returns:
            List of scores from league members
        """
        from app.models.league import LeagueMember

        query = (
            select(Score)
            .join(LeagueMember, Score.user_id == LeagueMember.user_id)
            .where(LeagueMember.league_id == league_id)
        )

        if event_id:
            query = query.where(Score.event_id == event_id)

        if season:
            query = query.join(Score.event).where(Score.event.has(season=season))

        if load_users:
            query = query.options(selectinload(Score.user))

        query = query.order_by(desc(Score.total_points))

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_season_leaderboard(
        self,
        season: int,
        league_id: Optional[UUID] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get season leaderboard with total points per user.
        
        Args:
            season: F1 season year
            league_id: Optional league filter
            limit: Maximum number of users to return
            
        Returns:
            List of dictionaries with user totals
        """
        from app.models.league import LeagueMember
        from app.models.user import User

        query = (
            select(
                Score.user_id,
                User.username,
                func.sum(Score.total_points).label('total_points'),
                func.count(Score.id).label('events_scored'),
                func.avg(Score.total_points).label('avg_points')
            )
            .join(User, Score.user_id == User.id)
            .join(Score.event)
            .where(Score.event.has(season=season))
            .group_by(Score.user_id, User.username)
        )

        # Add league filter if specified
        if league_id:
            query = query.join(LeagueMember, Score.user_id == LeagueMember.user_id).where(
                LeagueMember.league_id == league_id
            )

        query = query.order_by(desc('total_points')).limit(limit)

        result = await self.session.execute(query)
        rows = result.all()

        return [
            {
                "user_id": row.user_id,
                "username": row.username,
                "total_points": int(row.total_points or 0),
                "events_scored": row.events_scored,
                "average_points": float(row.avg_points or 0),
            }
            for row in rows
        ]

    async def create_or_update_score(
        self,
        user_id: UUID,
        event_id: UUID,
        points_breakdown: Dict[str, Any],
        total_points: int
    ) -> Score:
        """
        Create a new score or update existing one.
        
        Args:
            user_id: User ID
            event_id: Event ID
            points_breakdown: Detailed points breakdown
            total_points: Total points earned
            
        Returns:
            Created or updated Score instance
        """
        existing_score = await self.get_user_score_for_event(user_id, event_id)

        if existing_score:
            # Update existing score
            existing_score.points_breakdown = points_breakdown
            existing_score.total_points = total_points
            existing_score.calculated_at = func.now()

            await self.session.flush()
            await self.session.refresh(existing_score)

            logger.debug(f"Updated score for user {user_id}, event {event_id}: {total_points} points")
            return existing_score
        else:
            # Create new score
            new_score = Score(
                user_id=user_id,
                event_id=event_id,
                points_breakdown=points_breakdown,
                total_points=total_points,
                calculated_at=func.now()
            )

            self.session.add(new_score)
            await self.session.flush()
            await self.session.refresh(new_score)

            logger.debug(f"Created score for user {user_id}, event {event_id}: {total_points} points")
            return new_score

    async def get_user_season_total(self, user_id: UUID, season: int) -> int:
        """
        Get user's total points for a season.
        
        Args:
            user_id: User ID
            season: F1 season year
            
        Returns:
            Total points for the season
        """
        query = (
            select(func.sum(Score.total_points))
            .join(Score.event)
            .where(
                and_(
                    Score.user_id == user_id,
                    Score.event.has(season=season)
                )
            )
        )

        result = await self.session.execute(query)
        total = result.scalar()
        return int(total or 0)

    async def get_user_rank_in_league(self, user_id: UUID, league_id: UUID, season: int) -> Optional[int]:
        """
        Get user's rank in a league for a season.
        
        Args:
            user_id: User ID
            league_id: League ID
            season: F1 season year
            
        Returns:
            User's rank (1-based) or None if not found
        """
        leaderboard = await self.get_season_leaderboard(season, league_id)

        for rank, entry in enumerate(leaderboard, 1):
            if entry["user_id"] == user_id:
                return rank

        return None

    async def get_score_statistics(self, event_id: UUID) -> Dict[str, Any]:
        """
        Get statistics for scores on an event.
        
        Args:
            event_id: Event ID
            
        Returns:
            Dictionary with score statistics
        """
        query = select(
            func.count(Score.id).label('total_scores'),
            func.avg(Score.total_points).label('avg_points'),
            func.max(Score.total_points).label('max_points'),
            func.min(Score.total_points).label('min_points')
        ).where(Score.event_id == event_id)

        result = await self.session.execute(query)
        row = result.first()

        return {
            "total_scores": row.total_scores or 0,
            "average_points": float(row.avg_points or 0),
            "max_points": row.max_points or 0,
            "min_points": row.min_points or 0,
        }

    async def bulk_create_scores(self, scores_data: List[Dict[str, Any]]) -> List[Score]:
        """
        Bulk create scores for an event.
        
        Args:
            scores_data: List of score dictionaries
            
        Returns:
            List of created Score instances
        """
        return await self.bulk_create(scores_data)

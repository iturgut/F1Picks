"""
League repository for database operations.
"""

import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.league import League, LeagueMember
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class LeagueRepository(BaseRepository[League]):
    """Repository for League model operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(League, session)

    async def get_global_league(self) -> Optional[League]:
        """
        Get the global league.
        
        Returns:
            Global league instance or None if not found
        """
        return await self.get_by_field("is_global", True)

    async def get_by_code(self, code: str) -> Optional[League]:
        """
        Get league by invite code.
        
        Args:
            code: League invite code
            
        Returns:
            League instance or None if not found
        """
        return await self.get_by_field("invite_code", code)

    async def get_with_members(self, league_id: UUID) -> Optional[League]:
        """
        Get league with all members.
        
        Args:
            league_id: League ID
            
        Returns:
            League instance with members or None if not found
        """
        query = (
            select(League)
            .options(selectinload(League.members).selectinload(LeagueMember.user))
            .where(League.id == league_id)
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_leagues(self, user_id: UUID, active_only: bool = True) -> List[League]:
        """
        Get all leagues a user is a member of.
        
        Args:
            user_id: User ID
            active_only: Only return active leagues
            
        Returns:
            List of leagues the user is a member of
        """
        query = (
            select(League)
            .join(LeagueMember)
            .where(LeagueMember.user_id == user_id)
        )

        if active_only:
            query = query.where(League.is_active == True)

        query = query.order_by(League.created_at.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_public_leagues(self, skip: int = 0, limit: int = 100) -> List[League]:
        """
        Get all public leagues.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of public leagues
        """
        return await self.get_all(
            skip=skip,
            limit=limit,
            filters={"is_public": True, "is_active": True},
            order_by="-created_at"
        )

    async def search_leagues(self, search_term: str, limit: int = 20) -> List[League]:
        """
        Search leagues by name or description.
        
        Args:
            search_term: Search term
            limit: Maximum number of results
            
        Returns:
            List of matching leagues
        """
        return await self.search(
            search_term=search_term,
            search_fields=["name", "description"],
            limit=limit
        )

    async def get_league_member(self, league_id: UUID, user_id: UUID) -> Optional[LeagueMember]:
        """
        Get league membership for a specific user.
        
        Args:
            league_id: League ID
            user_id: User ID
            
        Returns:
            LeagueMember instance or None if not found
        """
        query = select(LeagueMember).where(
            and_(
                LeagueMember.league_id == league_id,
                LeagueMember.user_id == user_id
            )
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def add_member(
        self,
        league_id: UUID,
        user_id: UUID,
        role: str = "member"
    ) -> LeagueMember:
        """
        Add a user to a league.
        
        Args:
            league_id: League ID
            user_id: User ID
            role: Member role (admin, member)
            
        Returns:
            Created LeagueMember instance
        """
        member = LeagueMember(
            league_id=league_id,
            user_id=user_id,
            role=role
        )

        self.session.add(member)
        await self.session.flush()
        await self.session.refresh(member)

        logger.debug(f"Added user {user_id} to league {league_id} with role {role}")
        return member

    async def remove_member(self, league_id: UUID, user_id: UUID) -> bool:
        """
        Remove a user from a league.
        
        Args:
            league_id: League ID
            user_id: User ID
            
        Returns:
            True if removed, False if not found
        """
        member = await self.get_league_member(league_id, user_id)
        if not member:
            return False

        await self.session.delete(member)
        logger.debug(f"Removed user {user_id} from league {league_id}")
        return True

    async def update_member_role(
        self,
        league_id: UUID,
        user_id: UUID,
        role: str
    ) -> Optional[LeagueMember]:
        """
        Update a member's role in a league.
        
        Args:
            league_id: League ID
            user_id: User ID
            role: New role
            
        Returns:
            Updated LeagueMember instance or None if not found
        """
        member = await self.get_league_member(league_id, user_id)
        if not member:
            return None

        member.role = role
        await self.session.flush()
        await self.session.refresh(member)

        logger.debug(f"Updated user {user_id} role in league {league_id} to {role}")
        return member

    async def get_league_stats(self, league_id: UUID) -> dict:
        """
        Get league statistics.
        
        Args:
            league_id: League ID
            
        Returns:
            Dictionary with league statistics
        """
        # Get member count
        member_count = await self.session.execute(
            select(LeagueMember).where(LeagueMember.league_id == league_id)
        )
        member_count = len(list(member_count.scalars().all()))

        return {
            "member_count": member_count,
            # Add more statistics as needed
        }


class LeagueMemberRepository(BaseRepository[LeagueMember]):
    """Repository for LeagueMember model operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(LeagueMember, session)

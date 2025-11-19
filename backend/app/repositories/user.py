"""
User repository for database operations.
"""

import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[User]):
    """Repository for User model operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            email: User email address
            
        Returns:
            User instance or None if not found
        """
        return await self.get_by_field("email", email)

    async def get_by_supabase_id(self, supabase_id: UUID) -> Optional[User]:
        """
        Get user by Supabase user ID.
        
        Args:
            supabase_id: Supabase user ID
            
        Returns:
            User instance or None if not found
        """
        return await self.get_by_field("supabase_id", supabase_id)

    async def get_with_leagues(self, user_id: UUID) -> Optional[User]:
        """
        Get user with their league memberships.
        
        Args:
            user_id: User ID
            
        Returns:
            User instance with leagues or None if not found
        """
        query = (
            select(User)
            .options(selectinload(User.league_memberships))
            .where(User.id == user_id)
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_with_picks(self, user_id: UUID, event_id: Optional[UUID] = None) -> Optional[User]:
        """
        Get user with their picks, optionally filtered by event.
        
        Args:
            user_id: User ID
            event_id: Optional event ID to filter picks
            
        Returns:
            User instance with picks or None if not found
        """
        query = select(User).where(User.id == user_id)

        if event_id:
            query = query.options(
                selectinload(User.picks).where(User.picks.property.mapper.class_.event_id == event_id)
            )
        else:
            query = query.options(selectinload(User.picks))

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def search_by_username(self, username_pattern: str, limit: int = 10) -> List[User]:
        """
        Search users by username pattern.
        
        Args:
            username_pattern: Username search pattern
            limit: Maximum number of results
            
        Returns:
            List of matching users
        """
        return await self.search(
            search_term=username_pattern,
            search_fields=["username"],
            limit=limit
        )

    async def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get all active users.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of active users
        """
        return await self.get_all(
            skip=skip,
            limit=limit,
            filters={"is_active": True},
            order_by="created_at"
        )

    async def update_last_login(self, user_id: UUID) -> Optional[User]:
        """
        Update user's last login timestamp.
        
        Args:
            user_id: User ID
            
        Returns:
            Updated user instance or None if not found
        """
        from datetime import datetime, timezone

        return await self.update(
            user_id,
            last_login_at=datetime.now(timezone.utc)
        )

    async def deactivate_user(self, user_id: UUID) -> Optional[User]:
        """
        Deactivate a user account.
        
        Args:
            user_id: User ID
            
        Returns:
            Updated user instance or None if not found
        """
        return await self.update(user_id, is_active=False)

    async def activate_user(self, user_id: UUID) -> Optional[User]:
        """
        Activate a user account.
        
        Args:
            user_id: User ID
            
        Returns:
            Updated user instance or None if not found
        """
        return await self.update(user_id, is_active=True)

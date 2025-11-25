"""
Result repository for database operations.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.result import Result
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ResultRepository(BaseRepository[Result]):
    """Repository for Result model operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Result, session)

    async def get_event_results(self, event_id: UUID, result_type: Optional[str] = None) -> List[Result]:
        """
        Get all results for an event.
        
        Args:
            event_id: Event ID
            result_type: Optional filter by result type (race, qualifying, practice, etc.)
            
        Returns:
            List of results for the event
        """
        filters = {"event_id": event_id}
        if result_type:
            filters["result_type"] = result_type

        return await self.get_all(
            filters=filters,
            order_by="position"
        )

    async def get_race_results(self, event_id: UUID) -> List[Result]:
        """
        Get race results for an event.
        
        Args:
            event_id: Event ID
            
        Returns:
            List of race results ordered by position
        """
        return await self.get_event_results(event_id, "race")

    async def get_qualifying_results(self, event_id: UUID) -> List[Result]:
        """
        Get qualifying results for an event.
        
        Args:
            event_id: Event ID
            
        Returns:
            List of qualifying results ordered by position
        """
        return await self.get_event_results(event_id, "qualifying")

    async def get_driver_results(self, driver_name: str, season: Optional[int] = None) -> List[Result]:
        """
        Get all results for a specific driver.
        
        Args:
            driver_name: Driver name
            season: Optional season filter
            
        Returns:
            List of driver results
        """
        query = select(Result).where(Result.driver == driver_name)

        if season:
            query = query.options(selectinload(Result.event)).where(
                Result.event.has(season=season)
            )

        query = query.order_by(Result.event_id, Result.result_type, Result.position)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_constructor_results(self, constructor_name: str, season: Optional[int] = None) -> List[Result]:
        """
        Get all results for a specific constructor.
        
        Args:
            constructor_name: Constructor name
            season: Optional season filter
            
        Returns:
            List of constructor results
        """
        query = select(Result).where(Result.constructor == constructor_name)

        if season:
            query = query.options(selectinload(Result.event)).where(
                Result.event.has(season=season)
            )

        query = query.order_by(Result.event_id, Result.result_type, Result.position)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create_or_update_result(
        self,
        event_id: UUID,
        result_type: str,
        position: int,
        driver: str,
        constructor: str,
        **kwargs
    ) -> Result:
        """
        Create a new result or update existing one.
        
        Args:
            event_id: Event ID
            result_type: Type of result (race, qualifying, etc.)
            position: Finishing position
            driver: Driver name
            constructor: Constructor name
            **kwargs: Additional result data
            
        Returns:
            Created or updated Result instance
        """
        # Check if result already exists
        query = select(Result).where(
            and_(
                Result.event_id == event_id,
                Result.result_type == result_type,
                Result.position == position
            )
        )

        result = await self.session.execute(query)
        existing_result = result.scalar_one_or_none()

        if existing_result:
            # Update existing result
            existing_result.driver = driver
            existing_result.constructor = constructor
            for key, value in kwargs.items():
                setattr(existing_result, key, value)

            await self.session.flush()
            await self.session.refresh(existing_result)

            logger.debug(f"Updated result for event {event_id}, {result_type}, position {position}")
            return existing_result
        else:
            # Create new result
            new_result = Result(
                event_id=event_id,
                result_type=result_type,
                position=position,
                driver=driver,
                constructor=constructor,
                **kwargs
            )

            self.session.add(new_result)
            await self.session.flush()
            await self.session.refresh(new_result)

            logger.debug(f"Created result for event {event_id}, {result_type}, position {position}")
            return new_result

    async def get_podium_finishers(self, event_id: UUID) -> List[Result]:
        """
        Get podium finishers (top 3) for a race.
        
        Args:
            event_id: Event ID
            
        Returns:
            List of top 3 race results
        """
        query = (
            select(Result)
            .where(
                and_(
                    Result.event_id == event_id,
                    Result.result_type == "race",
                    Result.position <= 3
                )
            )
            .order_by(Result.position)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_fastest_lap(self, event_id: UUID) -> Optional[Result]:
        """
        Get the fastest lap result for a race.
        
        Args:
            event_id: Event ID
            
        Returns:
            Result with fastest lap or None
        """
        query = select(Result).where(
            and_(
                Result.event_id == event_id,
                Result.result_type == "race",
                Result.fastest_lap == True
            )
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def bulk_create_results(self, results_data: List[Dict[str, Any]]) -> List[Result]:
        """
        Bulk create results for an event.
        
        Args:
            results_data: List of result dictionaries
            
        Returns:
            List of created Result instances
        """
        return await self.bulk_create(results_data)

    async def delete_event_results(self, event_id: UUID, result_type: Optional[str] = None) -> int:
        """
        Delete all results for an event.
        
        Args:
            event_id: Event ID
            result_type: Optional filter by result type
            
        Returns:
            Number of deleted results
        """
        query = select(Result).where(Result.event_id == event_id)

        if result_type:
            query = query.where(Result.result_type == result_type)

        results = await self.session.execute(query)
        results_to_delete = results.scalars().all()

        count = 0
        for result in results_to_delete:
            await self.session.delete(result)
            count += 1

        logger.debug(f"Deleted {count} results for event {event_id}")
        return count

"""
Base repository pattern for database operations.
"""

import logging
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from uuid import UUID

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.base import Base

# Type variable for model classes
ModelType = TypeVar("ModelType", bound=Base)

logger = logging.getLogger(__name__)


class BaseRepository(Generic[ModelType]):
    """Base repository class with common CRUD operations."""

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """
        Initialize repository with model class and database session.
        
        Args:
            model: SQLAlchemy model class
            session: Database session
        """
        self.model = model
        self.session = session

    async def create(self, **kwargs) -> ModelType:
        """
        Create a new record.
        
        Args:
            **kwargs: Model field values
            
        Returns:
            Created model instance
            
        Raises:
            IntegrityError: If unique constraint is violated
        """
        try:
            instance = self.model(**kwargs)
            self.session.add(instance)
            await self.session.flush()
            await self.session.refresh(instance)
            logger.debug(f"Created {self.model.__name__} with id: {instance.id}")
            return instance
        except IntegrityError as e:
            logger.error(f"Failed to create {self.model.__name__}: {e}")
            await self.session.rollback()
            raise

    async def get_by_id(self, id: Union[UUID, int], load_relationships: List[str] = None) -> Optional[ModelType]:
        """
        Get record by ID.
        
        Args:
            id: Record ID
            load_relationships: List of relationship names to eager load
            
        Returns:
            Model instance or None if not found
        """
        query = select(self.model).where(self.model.id == id)

        # Add eager loading for relationships
        if load_relationships:
            for relationship in load_relationships:
                query = query.options(selectinload(getattr(self.model, relationship)))

        result = await self.session.execute(query)
        instance = result.scalar_one_or_none()

        if instance:
            logger.debug(f"Found {self.model.__name__} with id: {id}")
        else:
            logger.debug(f"{self.model.__name__} with id {id} not found")

        return instance

    async def get_by_field(self, field: str, value: Any, load_relationships: List[str] = None) -> Optional[ModelType]:
        """
        Get record by field value.
        
        Args:
            field: Field name
            value: Field value
            load_relationships: List of relationship names to eager load
            
        Returns:
            Model instance or None if not found
        """
        query = select(self.model).where(getattr(self.model, field) == value)

        # Add eager loading for relationships
        if load_relationships:
            for relationship in load_relationships:
                query = query.options(selectinload(getattr(self.model, relationship)))

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Dict[str, Any] = None,
        order_by: str = None,
        load_relationships: List[str] = None
    ) -> List[ModelType]:
        """
        Get all records with optional filtering, pagination, and ordering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Dictionary of field filters
            order_by: Field name to order by (prefix with '-' for descending)
            load_relationships: List of relationship names to eager load
            
        Returns:
            List of model instances
        """
        query = select(self.model)

        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)

        # Apply ordering
        if order_by:
            if order_by.startswith('-'):
                field_name = order_by[1:]
                if hasattr(self.model, field_name):
                    query = query.order_by(getattr(self.model, field_name).desc())
            else:
                if hasattr(self.model, order_by):
                    query = query.order_by(getattr(self.model, order_by))

        # Add eager loading for relationships
        if load_relationships:
            for relationship in load_relationships:
                query = query.options(selectinload(getattr(self.model, relationship)))

        # Apply pagination
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        instances = result.scalars().all()

        logger.debug(f"Retrieved {len(instances)} {self.model.__name__} records")
        return list(instances)

    async def update(self, id: Union[UUID, int], **kwargs) -> Optional[ModelType]:
        """
        Update record by ID.
        
        Args:
            id: Record ID
            **kwargs: Fields to update
            
        Returns:
            Updated model instance or None if not found
            
        Raises:
            IntegrityError: If unique constraint is violated
        """
        try:
            # Remove None values and empty strings
            update_data = {k: v for k, v in kwargs.items() if v is not None and v != ""}

            if not update_data:
                return await self.get_by_id(id)

            query = update(self.model).where(self.model.id == id).values(**update_data)
            result = await self.session.execute(query)

            if result.rowcount == 0:
                logger.debug(f"{self.model.__name__} with id {id} not found for update")
                return None

            # Fetch updated instance
            updated_instance = await self.get_by_id(id)
            logger.debug(f"Updated {self.model.__name__} with id: {id}")
            return updated_instance

        except IntegrityError as e:
            logger.error(f"Failed to update {self.model.__name__} with id {id}: {e}")
            await self.session.rollback()
            raise

    async def delete(self, id: Union[UUID, int]) -> bool:
        """
        Delete record by ID.
        
        Args:
            id: Record ID
            
        Returns:
            True if deleted, False if not found
        """
        query = delete(self.model).where(self.model.id == id)
        result = await self.session.execute(query)

        deleted = result.rowcount > 0
        if deleted:
            logger.debug(f"Deleted {self.model.__name__} with id: {id}")
        else:
            logger.debug(f"{self.model.__name__} with id {id} not found for deletion")

        return deleted

    async def count(self, filters: Dict[str, Any] = None) -> int:
        """
        Count records with optional filtering.
        
        Args:
            filters: Dictionary of field filters
            
        Returns:
            Number of matching records
        """
        query = select(func.count(self.model.id))

        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)

        result = await self.session.execute(query)
        count = result.scalar()

        logger.debug(f"Counted {count} {self.model.__name__} records")
        return count

    async def exists(self, id: Union[UUID, int]) -> bool:
        """
        Check if record exists by ID.
        
        Args:
            id: Record ID
            
        Returns:
            True if exists, False otherwise
        """
        query = select(func.count(self.model.id)).where(self.model.id == id)
        result = await self.session.execute(query)
        return result.scalar() > 0

    async def bulk_create(self, instances_data: List[Dict[str, Any]]) -> List[ModelType]:
        """
        Create multiple records in bulk.
        
        Args:
            instances_data: List of dictionaries with model field values
            
        Returns:
            List of created model instances
            
        Raises:
            IntegrityError: If unique constraint is violated
        """
        try:
            instances = [self.model(**data) for data in instances_data]
            self.session.add_all(instances)
            await self.session.flush()

            # Refresh all instances to get generated IDs
            for instance in instances:
                await self.session.refresh(instance)

            logger.debug(f"Bulk created {len(instances)} {self.model.__name__} records")
            return instances

        except IntegrityError as e:
            logger.error(f"Failed to bulk create {self.model.__name__} records: {e}")
            await self.session.rollback()
            raise

    async def search(
        self,
        search_term: str,
        search_fields: List[str],
        skip: int = 0,
        limit: int = 100,
        load_relationships: List[str] = None
    ) -> List[ModelType]:
        """
        Search records by text in specified fields.
        
        Args:
            search_term: Text to search for
            search_fields: List of field names to search in
            skip: Number of records to skip
            limit: Maximum number of records to return
            load_relationships: List of relationship names to eager load
            
        Returns:
            List of matching model instances
        """
        query = select(self.model)

        # Build search conditions
        search_conditions = []
        for field in search_fields:
            if hasattr(self.model, field):
                field_attr = getattr(self.model, field)
                search_conditions.append(field_attr.ilike(f"%{search_term}%"))

        if search_conditions:
            query = query.where(or_(*search_conditions))

        # Add eager loading for relationships
        if load_relationships:
            for relationship in load_relationships:
                query = query.options(selectinload(getattr(self.model, relationship)))

        # Apply pagination
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        instances = result.scalars().all()

        logger.debug(f"Search found {len(instances)} {self.model.__name__} records")
        return list(instances)


class TransactionManager:
    """Context manager for database transactions."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self._transaction = None

    async def __aenter__(self):
        """Start transaction."""
        self._transaction = await self.session.begin()
        logger.debug("Started database transaction")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Commit or rollback transaction."""
        if exc_type is not None:
            await self._transaction.rollback()
            logger.debug("Rolled back database transaction due to exception")
        else:
            await self._transaction.commit()
            logger.debug("Committed database transaction")

        self._transaction = None

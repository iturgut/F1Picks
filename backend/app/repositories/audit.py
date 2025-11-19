"""
Audit repository for database operations.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit import Audit
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class AuditRepository(BaseRepository[Audit]):
    """Repository for Audit model operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Audit, session)

    async def create_audit_log(
        self,
        entity_type: str,
        entity_id: UUID,
        action: str,
        user_id: Optional[UUID] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Audit:
        """
        Create an audit log entry.
        
        Args:
            entity_type: Type of entity (USER, LEAGUE, EVENT, etc.)
            entity_id: ID of the entity being audited
            action: Action performed (CREATE, UPDATE, DELETE)
            user_id: ID of user performing the action
            old_values: Previous values (for updates)
            new_values: New values (for creates/updates)
            metadata: Additional metadata
            
        Returns:
            Created Audit instance
        """
        audit_entry = Audit(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            user_id=user_id,
            old_values=old_values or {},
            new_values=new_values or {},
            metadata=metadata or {},
            timestamp=datetime.now(timezone.utc)
        )

        self.session.add(audit_entry)
        await self.session.flush()
        await self.session.refresh(audit_entry)

        logger.debug(f"Created audit log: {entity_type} {entity_id} {action}")
        return audit_entry

    async def get_entity_audit_trail(
        self,
        entity_type: str,
        entity_id: UUID,
        limit: int = 100
    ) -> List[Audit]:
        """
        Get audit trail for a specific entity.
        
        Args:
            entity_type: Type of entity
            entity_id: Entity ID
            limit: Maximum number of entries to return
            
        Returns:
            List of audit entries for the entity
        """
        return await self.get_all(
            filters={
                "entity_type": entity_type,
                "entity_id": entity_id
            },
            order_by="-timestamp",
            limit=limit
        )

    async def get_user_activity(
        self,
        user_id: UUID,
        limit: int = 100,
        load_details: bool = False
    ) -> List[Audit]:
        """
        Get audit trail for a specific user's actions.
        
        Args:
            user_id: User ID
            limit: Maximum number of entries to return
            load_details: Whether to load user details
            
        Returns:
            List of audit entries for the user
        """
        query = select(Audit).where(Audit.user_id == user_id)

        if load_details:
            query = query.options(selectinload(Audit.user))

        query = query.order_by(desc(Audit.timestamp)).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_recent_activity(
        self,
        entity_types: Optional[List[str]] = None,
        actions: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[Audit]:
        """
        Get recent activity across the system.
        
        Args:
            entity_types: Optional filter by entity types
            actions: Optional filter by actions
            limit: Maximum number of entries to return
            
        Returns:
            List of recent audit entries
        """
        query = select(Audit).options(selectinload(Audit.user))

        # Apply filters
        conditions = []
        if entity_types:
            conditions.append(Audit.entity_type.in_(entity_types))
        if actions:
            conditions.append(Audit.action.in_(actions))

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(desc(Audit.timestamp)).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_league_activity(
        self,
        league_id: UUID,
        limit: int = 100
    ) -> List[Audit]:
        """
        Get audit trail for league-related activities.
        
        Args:
            league_id: League ID
            limit: Maximum number of entries to return
            
        Returns:
            List of audit entries related to the league
        """
        # Get direct league audits
        direct_audits = await self.get_entity_audit_trail("LEAGUE", league_id, limit // 2)

        # Get member-related audits (joins, leaves, role changes)
        query = (
            select(Audit)
            .where(
                and_(
                    Audit.entity_type == "LEAGUE_MEMBER",
                    Audit.metadata.has_key("league_id"),
                    Audit.metadata["league_id"].astext == str(league_id)
                )
            )
            .order_by(desc(Audit.timestamp))
            .limit(limit // 2)
        )

        result = await self.session.execute(query)
        member_audits = list(result.scalars().all())

        # Combine and sort by timestamp
        all_audits = direct_audits + member_audits
        all_audits.sort(key=lambda x: x.timestamp, reverse=True)

        return all_audits[:limit]

    async def search_audit_logs(
        self,
        search_term: str,
        entity_types: Optional[List[str]] = None,
        actions: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Audit]:
        """
        Search audit logs by various criteria.
        
        Args:
            search_term: Text to search in metadata and values
            entity_types: Optional filter by entity types
            actions: Optional filter by actions
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Maximum number of entries to return
            
        Returns:
            List of matching audit entries
        """
        query = select(Audit).options(selectinload(Audit.user))

        conditions = []

        # Text search in old_values, new_values, and metadata
        if search_term:
            search_conditions = [
                Audit.old_values.astext.ilike(f"%{search_term}%"),
                Audit.new_values.astext.ilike(f"%{search_term}%"),
                Audit.metadata.astext.ilike(f"%{search_term}%")
            ]
            conditions.append(or_(*search_conditions))

        # Filter by entity types
        if entity_types:
            conditions.append(Audit.entity_type.in_(entity_types))

        # Filter by actions
        if actions:
            conditions.append(Audit.action.in_(actions))

        # Date range filters
        if start_date:
            conditions.append(Audit.timestamp >= start_date)
        if end_date:
            conditions.append(Audit.timestamp <= end_date)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(desc(Audit.timestamp)).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_audit_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get audit statistics for a date range.
        
        Args:
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            Dictionary with audit statistics
        """
        from sqlalchemy import func

        query = select(
            Audit.entity_type,
            Audit.action,
            func.count(Audit.id).label('count')
        )

        conditions = []
        if start_date:
            conditions.append(Audit.timestamp >= start_date)
        if end_date:
            conditions.append(Audit.timestamp <= end_date)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.group_by(Audit.entity_type, Audit.action)

        result = await self.session.execute(query)
        rows = result.all()

        # Organize statistics
        stats = {
            "by_entity_type": {},
            "by_action": {},
            "total_entries": 0
        }

        for row in rows:
            entity_type = row.entity_type
            action = row.action
            count = row.count

            # By entity type
            if entity_type not in stats["by_entity_type"]:
                stats["by_entity_type"][entity_type] = 0
            stats["by_entity_type"][entity_type] += count

            # By action
            if action not in stats["by_action"]:
                stats["by_action"][action] = 0
            stats["by_action"][action] += count

            stats["total_entries"] += count

        return stats

    async def cleanup_old_audits(self, days_to_keep: int = 365) -> int:
        """
        Clean up old audit entries.
        
        Args:
            days_to_keep: Number of days of audit history to keep
            
        Returns:
            Number of deleted entries
        """
        cutoff_date = datetime.now(timezone.utc) - timezone.utc.localize(datetime.now()).replace(days=days_to_keep)

        query = select(Audit).where(Audit.timestamp < cutoff_date)
        result = await self.session.execute(query)
        old_audits = result.scalars().all()

        count = 0
        for audit in old_audits:
            await self.session.delete(audit)
            count += 1

        logger.info(f"Cleaned up {count} old audit entries")
        return count

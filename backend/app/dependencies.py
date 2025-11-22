"""
Dependency injection for FastAPI endpoints.
"""

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories import (
    AuditRepository,
    EventRepository,
    LeagueRepository,
    PickRepository,
    ResultRepository,
    ScoreRepository,
    TransactionManager,
    UserRepository,
)


# Database session dependency
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    async for session in get_db():
        yield session


# Repository dependencies
async def get_user_repository(session: AsyncSession = Depends(get_session)) -> UserRepository:
    """Get UserRepository dependency."""
    return UserRepository(session)


async def get_league_repository(session: AsyncSession = Depends(get_session)) -> LeagueRepository:
    """Get LeagueRepository dependency."""
    return LeagueRepository(session)


async def get_event_repository(session: AsyncSession = Depends(get_session)) -> EventRepository:
    """Get EventRepository dependency."""
    return EventRepository(session)


async def get_pick_repository(session: AsyncSession = Depends(get_session)) -> PickRepository:
    """Get PickRepository dependency."""
    return PickRepository(session)


async def get_result_repository(session: AsyncSession = Depends(get_session)) -> ResultRepository:
    """Get ResultRepository dependency."""
    return ResultRepository(session)


async def get_score_repository(session: AsyncSession = Depends(get_session)) -> ScoreRepository:
    """Get ScoreRepository dependency."""
    return ScoreRepository(session)


async def get_audit_repository(session: AsyncSession = Depends(get_session)) -> AuditRepository:
    """Get AuditRepository dependency."""
    return AuditRepository(session)


async def get_transaction_manager(session: AsyncSession = Depends(get_session)) -> TransactionManager:
    """Get TransactionManager dependency."""
    return TransactionManager(session)

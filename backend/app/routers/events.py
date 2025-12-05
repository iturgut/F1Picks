"""
Events API router for F1 event management.
"""
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user_optional
from ..database import get_db
from ..models import Event, User
from ..models.event import EventStatus, EventType

router = APIRouter(prefix="/events", tags=["events"])


# Pydantic schemas
class EventBase(BaseModel):
    """Base event schema."""
    name: str
    circuit_id: str
    circuit_name: str
    session_type: str
    round_number: int
    year: int
    start_time: datetime
    end_time: datetime
    status: str


class EventResponse(EventBase):
    """Event response schema."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    is_locked: bool = Field(description="Whether predictions are locked for this event")
    
    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    """Paginated event list response."""
    events: List[EventResponse]
    total: int
    page: int
    page_size: int


@router.get("", response_model=EventListResponse)
async def list_events(
    status: Optional[str] = Query(None, description="Filter by status: scheduled, live, completed"),
    session_type: Optional[str] = Query(None, description="Filter by session type"),
    year: Optional[int] = Query(None, description="Filter by year"),
    upcoming_only: bool = Query(False, description="Show only upcoming events"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    List F1 events with optional filtering and pagination.
    
    - **status**: Filter by event status (scheduled, live, completed, cancelled)
    - **session_type**: Filter by session type (race, qualifying, practice_1, etc.)
    - **year**: Filter by F1 season year
    - **upcoming_only**: Show only events that haven't started yet
    - **page**: Page number for pagination
    - **page_size**: Number of events per page
    """
    # Build query
    query = select(Event)
    
    # Apply filters
    if status:
        try:
            status_enum = EventStatus[status.upper()]
            query = query.where(Event.status == status_enum)
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    if session_type:
        try:
            type_enum = EventType[session_type.upper()]
            query = query.where(Event.session_type == type_enum)
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid session_type: {session_type}")
    
    if year:
        query = query.where(Event.year == year)
    
    if upcoming_only:
        query = query.where(Event.start_time > datetime.now(timezone.utc))
    
    # Order by start time
    query = query.order_by(Event.start_time.asc())
    
    # Get total count
    count_query = select(Event.id)
    if status:
        count_query = count_query.where(Event.status == status_enum)
    if session_type:
        count_query = count_query.where(Event.session_type == type_enum)
    if year:
        count_query = count_query.where(Event.year == year)
    if upcoming_only:
        count_query = count_query.where(Event.start_time > datetime.now(timezone.utc))
    
    result = await db.execute(count_query)
    total = len(result.all())
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Execute query
    result = await db.execute(query)
    events = result.scalars().all()
    
    # Convert to response format with is_locked
    now = datetime.now(timezone.utc)
    event_responses = [
        EventResponse(
            id=event.id,
            name=event.name,
            circuit_id=event.circuit_id,
            circuit_name=event.circuit_name,
            session_type=event.session_type.value,
            round_number=event.round_number,
            year=event.year,
            start_time=event.start_time,
            end_time=event.end_time,
            status=event.status.value,
            created_at=event.created_at,
            updated_at=event.updated_at,
            is_locked=event.start_time <= now,
        )
        for event in events
    ]
    
    return EventListResponse(
        events=event_responses,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Get a specific event by ID.
    
    - **event_id**: UUID of the event
    """
    query = select(Event).where(Event.id == event_id)
    result = await db.execute(query)
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    now = datetime.utcnow()
    return EventResponse(
        id=event.id,
        name=event.name,
        circuit_id=event.circuit_id,
        circuit_name=event.circuit_name,
        session_type=event.session_type.value,
        round_number=event.round_number,
        year=event.year,
        start_time=event.start_time,
        end_time=event.end_time,
        status=event.status.value,
        created_at=event.created_at,
        updated_at=event.updated_at,
        is_locked=event.start_time <= now,
    )

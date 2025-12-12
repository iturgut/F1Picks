"""
Picks API router for user predictions.
"""
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user
from ..database import get_db
from ..models import Event, Pick, User
from ..models.pick import PropType

router = APIRouter(prefix="/picks", tags=["picks"])
logger = logging.getLogger(__name__)


# Pydantic schemas
class PickCreate(BaseModel):
    """Schema for creating a pick."""
    event_id: UUID
    prop_type: str
    prop_value: str
    prop_metadata: Optional[dict] = None


class PickUpdate(BaseModel):
    """Schema for updating a pick."""
    prop_value: str
    prop_metadata: Optional[dict] = None


class PickResponse(BaseModel):
    """Pick response schema."""
    id: UUID
    user_id: UUID
    event_id: UUID
    prop_type: str
    prop_value: str
    prop_metadata: Optional[dict]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PickWithUserResponse(BaseModel):
    """Pick response with user information."""
    id: UUID
    user_id: UUID
    user_name: str
    user_email: str
    event_id: UUID
    prop_type: str
    prop_value: str
    prop_metadata: Optional[dict]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PickListResponse(BaseModel):
    """Paginated pick list response."""
    picks: List[PickResponse]
    total: int
    page: int
    page_size: int


@router.post("", response_model=PickResponse, status_code=201)
async def create_pick(
    pick_data: PickCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new pick for an event.
    
    Picks can only be created before the event starts.
    """
    logger.info(f"🔍 Creating pick for user {current_user.id} ({current_user.email})")
    logger.info(f"🔍 Pick data: event_id={pick_data.event_id}, prop_type={pick_data.prop_type}, prop_value={pick_data.prop_value}")
    
    # Verify event exists and is not locked
    event_query = select(Event).where(Event.id == pick_data.event_id)
    event_result = await db.execute(event_query)
    event = event_result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if event has started (predictions locked)
    if event.start_time <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=400,
            detail="Cannot create picks for events that have already started"
        )
    
    # Validate prop_type
    try:
        prop_type_enum = PropType[pick_data.prop_type.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid prop_type: {pick_data.prop_type}")
    
    # Check if user already has a pick for this event and prop_type
    existing_pick_query = select(Pick).where(
        and_(
            Pick.user_id == current_user.id,
            Pick.event_id == pick_data.event_id,
            Pick.prop_type == prop_type_enum,
        )
    )
    existing_result = await db.execute(existing_pick_query)
    existing_pick = existing_result.scalar_one_or_none()
    
    if existing_pick:
        raise HTTPException(
            status_code=400,
            detail=f"You already have a pick for this event and prop_type. Use PUT to update it."
        )
    
    # Create new pick
    new_pick = Pick(
        user_id=current_user.id,
        event_id=pick_data.event_id,
        prop_type=prop_type_enum,
        prop_value=pick_data.prop_value,
        prop_metadata=pick_data.prop_metadata,
    )
    
    db.add(new_pick)
    await db.commit()
    await db.refresh(new_pick)
    
    return PickResponse(
        id=new_pick.id,
        user_id=new_pick.user_id,
        event_id=new_pick.event_id,
        prop_type=new_pick.prop_type.value,
        prop_value=new_pick.prop_value,
        prop_metadata=new_pick.prop_metadata,
        created_at=new_pick.created_at,
        updated_at=new_pick.updated_at,
    )


@router.get("", response_model=PickListResponse)
async def list_picks(
    event_id: Optional[UUID] = Query(None, description="Filter by event ID"),
    prop_type: Optional[str] = Query(None, description="Filter by prop type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List current user's picks with optional filtering.
    
    - **event_id**: Filter picks for a specific event
    - **prop_type**: Filter by prediction type
    """
    logger.info(f"🔍 Fetching picks for user {current_user.id} ({current_user.email})")
    logger.info(f"🔍 Filters: event_id={event_id}, prop_type={prop_type}")
    
    # Build query for current user's picks
    query = select(Pick).where(Pick.user_id == current_user.id)
    
    # Apply filters
    if event_id:
        query = query.where(Pick.event_id == event_id)
    
    if prop_type:
        try:
            prop_type_enum = PropType[prop_type.upper()]
            query = query.where(Pick.prop_type == prop_type_enum)
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid prop_type: {prop_type}")
    
    # Order by created_at descending
    query = query.order_by(Pick.created_at.desc())
    
    # Get total count
    count_query = select(Pick.id).where(Pick.user_id == current_user.id)
    if event_id:
        count_query = count_query.where(Pick.event_id == event_id)
    if prop_type:
        count_query = count_query.where(Pick.prop_type == prop_type_enum)
    
    result = await db.execute(count_query)
    total = len(result.all())
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Execute query
    result = await db.execute(query)
    picks = result.scalars().all()
    
    # Convert to response format
    pick_responses = [
        PickResponse(
            id=pick.id,
            user_id=pick.user_id,
            event_id=pick.event_id,
            prop_type=pick.prop_type.value,
            prop_value=pick.prop_value,
            prop_metadata=pick.prop_metadata,
            created_at=pick.created_at,
            updated_at=pick.updated_at,
        )
        for pick in picks
    ]
    
    return PickListResponse(
        picks=pick_responses,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{pick_id}", response_model=PickResponse)
async def get_pick(
    pick_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific pick by ID.
    
    Users can only view their own picks.
    """
    query = select(Pick).where(
        and_(
            Pick.id == pick_id,
            Pick.user_id == current_user.id,
        )
    )
    result = await db.execute(query)
    pick = result.scalar_one_or_none()
    
    if not pick:
        raise HTTPException(status_code=404, detail="Pick not found")
    
    return PickResponse(
        id=pick.id,
        user_id=pick.user_id,
        event_id=pick.event_id,
        prop_type=pick.prop_type.value,
        prop_value=pick.prop_value,
        prop_metadata=pick.prop_metadata,
        created_at=pick.created_at,
        updated_at=pick.updated_at,
    )


@router.put("/{pick_id}", response_model=PickResponse)
async def update_pick(
    pick_id: UUID,
    pick_data: PickUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an existing pick.
    
    Picks can only be updated before the event starts.
    """
    # Get the pick
    query = select(Pick).where(
        and_(
            Pick.id == pick_id,
            Pick.user_id == current_user.id,
        )
    )
    result = await db.execute(query)
    pick = result.scalar_one_or_none()
    
    if not pick:
        raise HTTPException(status_code=404, detail="Pick not found")
    
    # Get the associated event
    event_query = select(Event).where(Event.id == pick.event_id)
    event_result = await db.execute(event_query)
    event = event_result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(status_code=404, detail="Associated event not found")
    
    # Check if event has started (predictions locked)
    if event.start_time <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=400,
            detail="Cannot update picks for events that have already started"
        )
    
    # Update the pick
    pick.prop_value = pick_data.prop_value
    if pick_data.prop_metadata is not None:
        pick.prop_metadata = pick_data.prop_metadata
    
    await db.commit()
    await db.refresh(pick)
    
    return PickResponse(
        id=pick.id,
        user_id=pick.user_id,
        event_id=pick.event_id,
        prop_type=pick.prop_type.value,
        prop_value=pick.prop_value,
        prop_metadata=pick.prop_metadata,
        created_at=pick.created_at,
        updated_at=pick.updated_at,
    )


@router.delete("/{pick_id}", status_code=204)
async def delete_pick(
    pick_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a pick.
    
    Picks can only be deleted before the event starts.
    """
    # Get the pick
    query = select(Pick).where(
        and_(
            Pick.id == pick_id,
            Pick.user_id == current_user.id,
        )
    )
    result = await db.execute(query)
    pick = result.scalar_one_or_none()
    
    if not pick:
        raise HTTPException(status_code=404, detail="Pick not found")
    
    # Get the associated event
    event_query = select(Event).where(Event.id == pick.event_id)
    event_result = await db.execute(event_query)
    event = event_result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(status_code=404, detail="Associated event not found")
    
    # Check if event has started (predictions locked)
    if event.start_time <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=400,
            detail="Cannot delete picks for events that have already started"
        )
    
    # Delete the pick
    await db.delete(pick)
    await db.commit()
    
    return None


@router.get("/events/{event_id}/league-picks", response_model=List[PickWithUserResponse])
async def get_event_league_picks(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all picks for an event from users in the same leagues as the current user.
    
    This endpoint returns picks from:
    - The current user
    - All users who share at least one league with the current user
    
    Useful for displaying predictions on the event detail page.
    """
    from ..models.league import LeagueMember
    
    # Get all leagues the current user is a member of
    leagues_query = select(LeagueMember.league_id).where(
        LeagueMember.user_id == current_user.id
    )
    leagues_result = await db.execute(leagues_query)
    user_league_ids = [row[0] for row in leagues_result.all()]
    
    if not user_league_ids:
        # User is not in any leagues, return only their own picks
        query = select(Pick).join(User).where(
            and_(
                Pick.event_id == event_id,
                Pick.user_id == current_user.id
            )
        )
    else:
        # Get all users in the same leagues
        league_members_query = select(LeagueMember.user_id).where(
            LeagueMember.league_id.in_(user_league_ids)
        ).distinct()
        league_members_result = await db.execute(league_members_query)
        league_member_ids = [row[0] for row in league_members_result.all()]
        
        # Get picks from all league members for this event
        query = select(Pick).join(User).where(
            and_(
                Pick.event_id == event_id,
                Pick.user_id.in_(league_member_ids)
            )
        )
    
    # Order by user name, then prop type
    query = query.order_by(User.name, Pick.prop_type)
    
    result = await db.execute(query)
    picks = result.scalars().all()
    
    # Fetch user data for each pick
    pick_responses = []
    for pick in picks:
        user_query = select(User).where(User.id == pick.user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        if user:
            pick_responses.append(PickWithUserResponse(
                id=pick.id,
                user_id=pick.user_id,
                user_name=user.name,
                user_email=user.email,
                event_id=pick.event_id,
                prop_type=pick.prop_type.value,
                prop_value=pick.prop_value,
                prop_metadata=pick.prop_metadata,
                created_at=pick.created_at,
                updated_at=pick.updated_at,
            ))
    
    return pick_responses

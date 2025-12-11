"""
League management API endpoints.

Handles league creation, membership, and management.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models.league import League, LeagueMember
from app.models.user import User
from app.repositories.league import LeagueRepository
from app.repositories.user import UserRepository

router = APIRouter(prefix="/api/leagues", tags=["leagues"])


# Pydantic schemas for request/response
class LeagueCreate(BaseModel):
    """Schema for creating a new league."""
    name: str
    description: Optional[str] = None


class LeagueUpdate(BaseModel):
    """Schema for updating a league."""
    name: Optional[str] = None
    description: Optional[str] = None


class LeagueResponse(BaseModel):
    """Schema for league response."""
    id: UUID
    name: str
    description: Optional[str] = None
    is_global: bool
    owner_id: Optional[UUID] = None
    created_at: datetime
    member_count: Optional[int] = None

    class Config:
        from_attributes = True


class LeagueMemberResponse(BaseModel):
    """Schema for league member response."""
    id: UUID
    user_id: UUID
    league_id: UUID
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    """Schema for user profile in league context."""
    id: UUID
    email: str
    name: str
    photo_url: Optional[str] = None

    class Config:
        from_attributes = True


@router.post("", response_model=LeagueResponse, status_code=status.HTTP_201_CREATED)
async def create_league(
    league_data: LeagueCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new league.
    
    The creator becomes the owner and is automatically added as a member.
    """
    league_repo = LeagueRepository(db)
    
    # Create the league
    created_league = await league_repo.create(
        name=league_data.name,
        description=league_data.description,
        is_global=False,
        owner_id=current_user.id
    )
    
    # Add creator as admin member
    await league_repo.add_member(
        league_id=created_league.id,
        user_id=current_user.id,
        role="admin"
    )
    
    await db.commit()
    
    # Get stats
    stats = await league_repo.get_league_stats(created_league.id)
    
    return LeagueResponse(
        id=created_league.id,
        name=created_league.name,
        description=created_league.description,
        is_global=created_league.is_global,
        owner_id=created_league.owner_id,
        created_at=created_league.created_at,
        member_count=stats.get("member_count", 0)
    )


@router.get("", response_model=List[LeagueResponse])
async def get_user_leagues(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all leagues the current user is a member of.
    """
    league_repo = LeagueRepository(db)
    
    leagues = await league_repo.get_user_leagues(current_user.id)
    
    # Get stats for each league
    response = []
    for league in leagues:
        stats = await league_repo.get_league_stats(league.id)
        response.append(LeagueResponse(
            id=league.id,
            name=league.name,
            description=league.description,
            is_global=league.is_global,
            owner_id=league.owner_id,
            created_at=league.created_at,
            member_count=stats.get("member_count", 0)
        ))
    
    return response


@router.get("/{league_id}", response_model=LeagueResponse)
async def get_league(
    league_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific league by ID.
    
    User must be a member of the league to view it.
    """
    league_repo = LeagueRepository(db)
    
    league = await league_repo.get_by_id(league_id)
    if not league:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found"
        )
    
    # Check if user is a member
    member = await league_repo.get_league_member(league_id, current_user.id)
    if not member and not league.is_global:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this league"
        )
    
    stats = await league_repo.get_league_stats(league_id)
    
    return LeagueResponse(
        id=league.id,
        name=league.name,
        description=league.description,
        is_global=league.is_global,
        owner_id=league.owner_id,
        created_at=league.created_at,
        member_count=stats.get("member_count", 0)
    )


@router.put("/{league_id}", response_model=LeagueResponse)
async def update_league(
    league_id: UUID,
    league_data: LeagueUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a league.
    
    Only the league owner can update the league.
    """
    league_repo = LeagueRepository(db)
    
    league = await league_repo.get_by_id(league_id)
    if not league:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found"
        )
    
    # Check if user is the owner
    if league.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the league owner can update the league"
        )
    
    # Update fields
    update_data = league_data.model_dump(exclude_unset=True)
    updated_league = await league_repo.update(league_id, update_data)
    await db.commit()
    
    stats = await league_repo.get_league_stats(league_id)
    
    return LeagueResponse(
        id=updated_league.id,
        name=updated_league.name,
        description=updated_league.description,
        is_global=updated_league.is_global,
        owner_id=updated_league.owner_id,
        created_at=updated_league.created_at,
        member_count=stats.get("member_count", 0)
    )


@router.delete("/{league_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_league(
    league_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a league.
    
    Only the league owner can delete the league.
    """
    league_repo = LeagueRepository(db)
    
    league = await league_repo.get_by_id(league_id)
    if not league:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found"
        )
    
    # Check if user is the owner
    if league.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the league owner can delete the league"
        )
    
    await league_repo.delete(league_id)
    await db.commit()


@router.post("/{league_id}/join", response_model=LeagueMemberResponse)
async def join_league(
    league_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Join a league.
    """
    league_repo = LeagueRepository(db)
    
    league = await league_repo.get_by_id(league_id)
    if not league:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found"
        )
    
    # Check if already a member
    existing_member = await league_repo.get_league_member(league_id, current_user.id)
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already a member of this league"
        )
    
    # Add member
    member = await league_repo.add_member(
        league_id=league_id,
        user_id=current_user.id,
        role="member"
    )
    
    await db.commit()
    
    return LeagueMemberResponse(
        id=member.id,
        user_id=member.user_id,
        league_id=member.league_id,
        role=member.role,
        joined_at=member.joined_at
    )


@router.post("/{league_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_league(
    league_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Leave a league.
    
    League owners cannot leave their own league.
    """
    league_repo = LeagueRepository(db)
    
    league = await league_repo.get_by_id(league_id)
    if not league:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found"
        )
    
    # Check if user is the owner
    if league.owner_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="League owners cannot leave their own league. Delete the league instead."
        )
    
    # Remove member
    removed = await league_repo.remove_member(league_id, current_user.id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not a member of this league"
        )
    
    await db.commit()


@router.delete("/{league_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def kick_member(
    league_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove a member from a league (kick).
    
    Only the league owner can kick members.
    """
    league_repo = LeagueRepository(db)
    
    league = await league_repo.get_by_id(league_id)
    if not league:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found"
        )
    
    # Check if user is the owner
    if league.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the league owner can remove members"
        )
    
    # Cannot kick yourself
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot kick yourself from the league"
        )
    
    # Remove member
    removed = await league_repo.remove_member(league_id, user_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member of this league"
        )
    
    await db.commit()


@router.post("/{league_id}/invite/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def invite_user_to_league(
    league_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Invite a user to a league.
    
    Only the league owner can invite users.
    For now, this directly adds the user (auto-accept).
    """
    league_repo = LeagueRepository(db)
    user_repo = UserRepository(db)
    
    league = await league_repo.get_by_id(league_id)
    if not league:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found"
        )
    
    # Check if current user is the owner
    if league.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the league owner can invite users"
        )
    
    # Check if user exists
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if already a member
    existing_member = await league_repo.get_league_member(league_id, user_id)
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this league"
        )
    
    # Add member
    await league_repo.add_member(
        league_id=league_id,
        user_id=user_id,
        role="member"
    )
    
    await db.commit()


@router.get("/{league_id}/members", response_model=List[UserProfileResponse])
async def get_league_members(
    league_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all members of a league.
    
    User must be a member of the league to view members.
    """
    league_repo = LeagueRepository(db)
    
    league = await league_repo.get_with_members(league_id)
    if not league:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found"
        )
    
    # Check if user is a member
    member = await league_repo.get_league_member(league_id, current_user.id)
    if not member and not league.is_global:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this league"
        )
    
    # Return user profiles
    return [
        UserProfileResponse(
            id=member.user.id,
            email=member.user.email,
            name=member.user.name,
            photo_url=member.user.photo_url
        )
        for member in league.members
    ]

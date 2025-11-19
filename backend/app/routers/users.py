"""
User management API endpoints.

Handles user profile creation, retrieval, and updates.
Integrates with Supabase authentication.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models.league import League, LeagueMember
from app.models.user import User
from app.repositories.league import LeagueRepository
from app.repositories.user import UserRepository

router = APIRouter(prefix="/api/users", tags=["users"])


# Pydantic schemas for request/response
class UserCreate(BaseModel):
    """Schema for creating a new user."""
    email: EmailStr
    name: str
    photo_url: Optional[str] = None


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    name: Optional[str] = None
    photo_url: Optional[str] = None


class UserResponse(BaseModel):
    """Schema for user response."""
    id: UUID
    email: str
    name: str
    photo_url: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current authenticated user's profile.
    
    Returns:
        User profile information
    """
    return current_user


@router.post("/me", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_user_profile(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Create or update the current user's profile.
    
    This endpoint is called after successful Supabase authentication to:
    1. Create a user record in our database if it doesn't exist
    2. Auto-join the user to the global league on first creation
    3. Update user information if it already exists
    
    Args:
        user_data: User profile data from Supabase
        current_user: Authenticated user from JWT token
        db: Database session
        
    Returns:
        Created or updated user profile
    """
    user_repo = UserRepository(db)
    
    # Check if user already exists
    existing_user = await user_repo.get_by_id(str(current_user.id))
    
    if existing_user:
        # Update existing user
        updated_user = await user_repo.update(
            str(current_user.id),
            name=user_data.name,
            photo_url=user_data.photo_url,
        )
        return updated_user
    
    # Create new user
    new_user = await user_repo.create(
        id=current_user.id,
        email=user_data.email,
        name=user_data.name,
        photo_url=user_data.photo_url,
    )
    
    # Auto-join user to global league
    league_repo = LeagueRepository(db)
    global_league = await league_repo.get_global_league()
    
    if global_league:
        # Create league membership
        await db.execute(
            LeagueMember.__table__.insert().values(
                user_id=new_user.id,
                league_id=global_league.id,
            )
        )
        await db.commit()
    
    return new_user


@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Update the current user's profile.
    
    Args:
        user_data: Updated user profile data
        current_user: Authenticated user from JWT token
        db: Database session
        
    Returns:
        Updated user profile
    """
    user_repo = UserRepository(db)
    
    # Build update dict with only provided fields
    update_data = {}
    if user_data.name is not None:
        update_data["name"] = user_data.name
    if user_data.photo_url is not None:
        update_data["photo_url"] = user_data.photo_url
    
    if not update_data:
        # No fields to update
        return current_user
    
    updated_user = await user_repo.update(str(current_user.id), **update_data)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return updated_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get a user's public profile by ID.
    
    Args:
        user_id: User UUID
        db: Database session
        
    Returns:
        User profile information
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(str(user_id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return user

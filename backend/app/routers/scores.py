"""
Scoring API endpoints.

Handles scoring operations, leaderboards, and score retrieval.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, get_current_user_optional
from app.database import get_db
from app.models.user import User
from app.repositories.score import ScoreRepository
from app.scoring.service import ScoringService

router = APIRouter(prefix="/scores", tags=["scores"])


# Pydantic schemas
class ScoreResponse(BaseModel):
    """Schema for score response."""
    id: UUID
    pick_id: UUID
    user_id: UUID
    points: int
    margin: Optional[float]
    exact_match: bool
    metadata: Optional[Dict[str, Any]]
    created_at: str

    class Config:
        from_attributes = True


class LeaderboardEntry(BaseModel):
    """Schema for leaderboard entry."""
    user_id: UUID
    username: str
    total_points: int
    events_scored: int
    average_points: float
    rank: int


class ScoringTriggerRequest(BaseModel):
    """Schema for triggering scoring."""
    event_id: UUID


class ScoringResultResponse(BaseModel):
    """Schema for scoring operation result."""
    event_id: str
    picks_scored: int
    scores_created: int
    scores_updated: int
    total_points: int


@router.get("", response_model=List[ScoreResponse])
async def list_scores(
    pick_id: Optional[List[UUID]] = Query(None, description="Filter by pick IDs"),
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    event_id: Optional[UUID] = Query(None, description="Filter by event ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get scores with optional filtering.
    
    Args:
        pick_id: Optional list of pick IDs to filter by
        user_id: Optional user ID to filter by
        event_id: Optional event ID to filter by
        db: Database session
        
    Returns:
        List of scores
    """
    from sqlalchemy import select
    from app.models.score import Score
    from app.models.pick import Pick
    
    # Build query
    query = select(Score)
    
    # Apply filters
    if pick_id:
        query = query.where(Score.pick_id.in_(pick_id))
    if user_id:
        query = query.where(Score.user_id == user_id)
    if event_id:
        # Join with picks to filter by event
        query = query.join(Pick, Score.pick_id == Pick.id).where(Pick.event_id == event_id)
    
    # Execute query
    result = await db.execute(query)
    scores = result.scalars().all()
    
    # Convert to response models
    score_responses = []
    for score in scores:
        score_responses.append(ScoreResponse(
            id=score.id,
            pick_id=score.pick_id,
            user_id=score.user_id,
            points=score.points,
            margin=score.margin,
            exact_match=score.exact_match,
            metadata=score.scoring_metadata,
            created_at=score.created_at.isoformat(),
        ))
    
    return score_responses


@router.post("/trigger", response_model=ScoringResultResponse)
async def trigger_scoring(
    request: ScoringTriggerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Trigger scoring for a completed event.
    
    This endpoint is typically called by the worker after ingesting results,
    but can also be manually triggered by authenticated users.
    
    Args:
        request: Scoring trigger request with event_id
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Scoring operation results
    """
    scoring_service = ScoringService(db)
    
    try:
        result = await scoring_service.score_event(request.event_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scoring failed: {str(e)}"
        )


@router.get("/event/{event_id}", response_model=List[Dict[str, Any]])
async def get_event_scores(
    event_id: UUID,
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """
    Get all scores for a specific event.
    
    Args:
        event_id: Event UUID
        limit: Maximum number of scores to return
        db: Database session
        
    Returns:
        List of scores with pick information
    """
    scoring_service = ScoringService(db)
    scores = await scoring_service.get_event_scores(event_id, limit=limit)
    return scores


@router.get("/user/{user_id}/event/{event_id}")
async def get_user_event_score(
    user_id: UUID,
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get a user's score for a specific event.
    
    Args:
        user_id: User UUID
        event_id: Event UUID
        db: Database session
        
    Returns:
        User's score for the event
    """
    score_repo = ScoreRepository(db)
    score = await score_repo.get_user_score_for_event(user_id, event_id)
    
    if not score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Score not found for this user and event"
        )
    
    return {
        "id": str(score.id),
        "user_id": str(score.user_id),
        "pick_id": str(score.pick_id),
        "points": score.points,
        "margin": score.margin,
        "exact_match": score.exact_match,
        "metadata": score.scoring_metadata,
        "created_at": score.created_at.isoformat()
    }


@router.get("/user/me")
async def get_my_scores(
    season: Optional[int] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """
    Get current user's scores.
    
    Args:
        season: Optional season filter
        current_user: Authenticated user
        db: Database session
        
    Returns:
        List of user's scores
    """
    score_repo = ScoreRepository(db)
    scores = await score_repo.get_user_scores(
        current_user.id,
        season=season,
        load_events=True
    )
    
    return [
        {
            "id": str(score.id),
            "pick_id": str(score.pick_id),
            "points": score.points,
            "margin": score.margin,
            "exact_match": score.exact_match,
            "metadata": score.scoring_metadata,
            "created_at": score.created_at.isoformat()
        }
        for score in scores
    ]


@router.get("/leaderboard/season/{season}", response_model=List[LeaderboardEntry])
async def get_season_leaderboard(
    season: int,
    league_id: Optional[UUID] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> List[LeaderboardEntry]:
    """
    Get season leaderboard.
    
    Args:
        season: F1 season year
        league_id: Optional league filter
        limit: Maximum number of entries to return
        db: Database session
        
    Returns:
        Leaderboard entries with rankings
    """
    score_repo = ScoreRepository(db)
    leaderboard_data = await score_repo.get_season_leaderboard(
        season=season,
        league_id=league_id,
        limit=limit
    )
    
    # Add rank to each entry
    leaderboard = [
        LeaderboardEntry(
            rank=rank,
            user_id=entry["user_id"],
            username=entry["username"],
            total_points=entry["total_points"],
            events_scored=entry["events_scored"],
            average_points=entry["average_points"]
        )
        for rank, entry in enumerate(leaderboard_data, 1)
    ]
    
    return leaderboard


@router.get("/leaderboard/event/{event_id}")
async def get_event_leaderboard(
    event_id: UUID,
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """
    Get leaderboard for a specific event.
    
    Args:
        event_id: Event UUID
        limit: Maximum number of entries to return
        db: Database session
        
    Returns:
        Event leaderboard with rankings
    """
    score_repo = ScoreRepository(db)
    scores = await score_repo.get_event_scores(event_id, load_users=True)
    
    # Limit and add rankings
    limited_scores = scores[:limit]
    
    leaderboard = []
    for rank, score in enumerate(limited_scores, 1):
        leaderboard.append({
            "rank": rank,
            "user_id": str(score.user_id),
            "username": score.user.name if score.user else "Unknown",
            "points": score.points,
            "exact_matches": score.exact_match,
            "created_at": score.created_at.isoformat()
        })
    
    return leaderboard


@router.get("/statistics/event/{event_id}")
async def get_event_statistics(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get scoring statistics for an event.
    
    Args:
        event_id: Event UUID
        db: Database session
        
    Returns:
        Event scoring statistics
    """
    score_repo = ScoreRepository(db)
    stats = await score_repo.get_score_statistics(event_id)
    return stats


@router.get("/user/{user_id}/season/{season}/total")
async def get_user_season_total(
    user_id: UUID,
    season: int,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get user's total points for a season.
    
    Args:
        user_id: User UUID
        season: F1 season year
        db: Database session
        
    Returns:
        User's season total
    """
    score_repo = ScoreRepository(db)
    total = await score_repo.get_user_season_total(user_id, season)
    
    return {
        "user_id": str(user_id),
        "season": season,
        "total_points": total
    }


@router.get("/user/{user_id}/league/{league_id}/rank")
async def get_user_league_rank(
    user_id: UUID,
    league_id: UUID,
    season: int = Query(..., description="F1 season year"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get user's rank in a league for a season.
    
    Args:
        user_id: User UUID
        league_id: League UUID
        season: F1 season year
        db: Database session
        
    Returns:
        User's rank information
    """
    score_repo = ScoreRepository(db)
    rank = await score_repo.get_user_rank_in_league(user_id, league_id, season)
    
    if rank is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in league leaderboard"
        )
    
    return {
        "user_id": str(user_id),
        "league_id": str(league_id),
        "season": season,
        "rank": rank
    }

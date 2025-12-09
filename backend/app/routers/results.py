"""
Results API endpoints for F1 event results.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.result import Result

router = APIRouter(prefix="/results", tags=["results"])


class ResultResponse(BaseModel):
    """Result response schema."""
    id: UUID
    event_id: UUID
    prop_type: str
    actual_value: str
    result_metadata: Optional[dict] = None
    source: str
    ingested_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class ResultListResponse(BaseModel):
    """Paginated result list response."""
    results: List[ResultResponse]
    total: int


@router.get("", response_model=ResultListResponse)
async def list_results(
    event_id: Optional[UUID] = Query(None, description="Filter by event ID"),
    prop_type: Optional[str] = Query(None, description="Filter by prop type"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get results with optional filtering.
    
    Args:
        event_id: Optional event ID to filter by
        prop_type: Optional prop type to filter by
        db: Database session
        
    Returns:
        List of results
    """
    # Build query
    query = select(Result)
    
    # Apply filters
    if event_id:
        query = query.where(Result.event_id == event_id)
    if prop_type:
        query = query.where(Result.prop_type == prop_type)
    
    # Execute query
    result = await db.execute(query)
    results = result.scalars().all()
    
    # Convert to response models
    result_responses = []
    for res in results:
        result_responses.append(ResultResponse(
            id=res.id,
            event_id=res.event_id,
            prop_type=res.prop_type.value,  # Convert enum to string
            actual_value=res.actual_value,
            result_metadata=res.result_metadata,
            source=res.source.value if hasattr(res.source, 'value') else res.source,
            ingested_at=res.ingested_at.isoformat(),
            updated_at=res.updated_at.isoformat(),
        ))
    
    return ResultListResponse(
        results=result_responses,
        total=len(result_responses)
    )


@router.get("/{result_id}", response_model=ResultResponse)
async def get_result(
    result_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific result by ID.
    
    Args:
        result_id: Result UUID
        db: Database session
        
    Returns:
        Result details
    """
    query = select(Result).where(Result.id == result_id)
    result = await db.execute(query)
    res = result.scalar_one_or_none()
    
    if not res:
        raise HTTPException(status_code=404, detail="Result not found")
    
    return ResultResponse(
        id=res.id,
        event_id=res.event_id,
        prop_type=res.prop_type.value,
        actual_value=res.actual_value,
        result_metadata=res.result_metadata,
        source=res.source.value if hasattr(res.source, 'value') else res.source,
        ingested_at=res.ingested_at.isoformat(),
        updated_at=res.updated_at.isoformat(),
    )

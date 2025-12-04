"""
Scoring service for processing predictions and calculating scores.

This service is called after FastF1 data is ingested to score all
user predictions for a completed event.
"""

import json
from typing import Dict, List, Optional, Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event, EventStatus
from app.models.pick import Pick, PropType
from app.models.result import Result
from app.models.score import Score
from app.models.audit import Audit, AuditAction, EntityType
from app.repositories.score import ScoreRepository
from .algorithms import ScoringAlgorithms, ScoringResult


class ScoringService:
    """Service for scoring user predictions against actual results."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize scoring service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.score_repo = ScoreRepository(db)
        self.algorithms = ScoringAlgorithms()
    
    async def score_event(self, event_id: UUID) -> Dict[str, Any]:
        """
        Score all predictions for a completed event.
        
        Args:
            event_id: Event UUID
            
        Returns:
            Dict with scoring statistics
        """
        # Verify event is completed
        event = await self.db.get(Event, event_id)
        if not event:
            raise ValueError(f"Event {event_id} not found")
        
        if event.status != EventStatus.COMPLETED:
            raise ValueError(f"Event {event_id} is not completed (status: {event.status.value})")
        
        # Get all results for this event
        results_query = select(Result).where(Result.event_id == event_id)
        results_result = await self.db.execute(results_query)
        results = results_result.scalars().all()
        
        if not results:
            raise ValueError(f"No results found for event {event_id}")
        
        # Organize results by prop type
        results_by_type = self._organize_results(results)
        
        # Get all picks for this event
        picks_query = select(Pick).where(Pick.event_id == event_id)
        picks_result = await self.db.execute(picks_query)
        picks = picks_result.scalars().all()
        
        # Score each pick
        scores_created = 0
        scores_updated = 0
        total_points = 0
        
        for pick in picks:
            try:
                score_result = await self._score_pick(pick, results_by_type)
                
                # Check if score already exists
                existing_score = await self.score_repo.get_by_pick_id(str(pick.id))
                
                if existing_score:
                    # Update existing score
                    await self.score_repo.update(
                        str(existing_score.id),
                        points=score_result.points,
                        margin=score_result.margin,
                        exact_match=score_result.exact_match,
                        scoring_metadata=score_result.metadata
                    )
                    scores_updated += 1
                else:
                    # Create new score
                    await self.score_repo.create(
                        pick_id=pick.id,
                        user_id=pick.user_id,
                        points=score_result.points,
                        margin=score_result.margin,
                        exact_match=score_result.exact_match,
                        scoring_metadata=score_result.metadata
                    )
                    scores_created += 1
                
                total_points += score_result.points
                
            except Exception as e:
                # Log error but continue scoring other picks
                print(f"Error scoring pick {pick.id}: {e}")
                continue
        
        # Create audit log
        await self._create_audit_log(
            event_id=event_id,
            picks_scored=len(picks),
            scores_created=scores_created,
            scores_updated=scores_updated,
            total_points=total_points
        )
        
        await self.db.commit()
        
        return {
            "event_id": str(event_id),
            "picks_scored": len(picks),
            "scores_created": scores_created,
            "scores_updated": scores_updated,
            "total_points": total_points
        }
    
    async def _score_pick(
        self,
        pick: Pick,
        results_by_type: Dict[PropType, List[Result]]
    ) -> ScoringResult:
        """
        Score a single pick against results.
        
        Args:
            pick: User's prediction
            results_by_type: Results organized by prop type
            
        Returns:
            ScoringResult with points and metadata
        """
        prop_type = pick.prop_type
        results = results_by_type.get(prop_type, [])
        
        if not results:
            # No results available for this prop type
            return ScoringResult(
                points=0,
                margin=None,
                exact_match=False,
                metadata={"error": "No results available for this prediction type"}
            )
        
        # Route to appropriate scoring algorithm based on prop type
        if prop_type in [
            PropType.RACE_WINNER,
            PropType.PODIUM_P1,
            PropType.PODIUM_P2,
            PropType.PODIUM_P3,
            PropType.POLE_POSITION,
            PropType.FIRST_RETIREMENT
        ]:
            return await self._score_driver_position(pick, results)
        
        elif prop_type == PropType.FASTEST_LAP:
            return await self._score_fastest_lap(pick, results)
        
        elif prop_type in [PropType.LAP_TIME_PREDICTION, PropType.SECTOR_TIME_PREDICTION]:
            return await self._score_time_prediction(pick, results)
        
        elif prop_type in [PropType.PIT_WINDOW_START, PropType.PIT_WINDOW_END]:
            return await self._score_pit_window(pick, results)
        
        elif prop_type == PropType.SAFETY_CAR:
            return await self._score_boolean(pick, results)
        
        elif prop_type == PropType.TOTAL_PIT_STOPS:
            return await self._score_count(pick, results)
        
        else:
            return ScoringResult(
                points=0,
                margin=None,
                exact_match=False,
                metadata={"error": f"Unsupported prop type: {prop_type.value}"}
            )
    
    async def _score_driver_position(
        self,
        pick: Pick,
        results: List[Result]
    ) -> ScoringResult:
        """Score driver position predictions."""
        predicted_driver = self.algorithms.parse_driver_code(pick.prop_value)
        
        # Get the actual driver for this position
        actual_result = results[0] if results else None
        if not actual_result:
            return ScoringResult(points=0, margin=None, exact_match=False)
        
        actual_driver = self.algorithms.parse_driver_code(actual_result.actual_value)
        
        # Get all finishing positions from metadata
        all_results = {}
        if actual_result.result_metadata:
            all_results = actual_result.result_metadata.get("finishing_order", {})
        
        return self.algorithms.score_driver_position(
            predicted_driver,
            actual_driver,
            all_results,
            pick.prop_type
        )
    
    async def _score_fastest_lap(
        self,
        pick: Pick,
        results: List[Result]
    ) -> ScoringResult:
        """Score fastest lap predictions."""
        predicted_driver = self.algorithms.parse_driver_code(pick.prop_value)
        
        actual_result = results[0] if results else None
        if not actual_result:
            return ScoringResult(points=0, margin=None, exact_match=False)
        
        actual_driver = self.algorithms.parse_driver_code(actual_result.actual_value)
        
        # Get all lap times from metadata
        all_lap_times = {}
        if actual_result.result_metadata:
            all_lap_times = actual_result.result_metadata.get("lap_times", {})
        
        return self.algorithms.score_fastest_lap(
            predicted_driver,
            actual_driver,
            all_lap_times
        )
    
    async def _score_time_prediction(
        self,
        pick: Pick,
        results: List[Result]
    ) -> ScoringResult:
        """Score time-based predictions."""
        predicted_time = self.algorithms.parse_time_value(pick.prop_value)
        
        actual_result = results[0] if results else None
        if not actual_result:
            return ScoringResult(points=0, margin=None, exact_match=False)
        
        actual_time = self.algorithms.parse_time_value(actual_result.actual_value)
        
        return self.algorithms.score_lap_time(predicted_time, actual_time)
    
    async def _score_pit_window(
        self,
        pick: Pick,
        results: List[Result]
    ) -> ScoringResult:
        """Score pit window predictions."""
        predicted_lap = self.algorithms.parse_lap_number(pick.prop_value)
        
        actual_result = results[0] if results else None
        if not actual_result:
            return ScoringResult(points=0, margin=None, exact_match=False)
        
        actual_lap = self.algorithms.parse_lap_number(actual_result.actual_value)
        
        return self.algorithms.score_pit_window(predicted_lap, actual_lap)
    
    async def _score_boolean(
        self,
        pick: Pick,
        results: List[Result]
    ) -> ScoringResult:
        """Score boolean predictions."""
        predicted_value = self.algorithms.parse_boolean_value(pick.prop_value)
        
        actual_result = results[0] if results else None
        if not actual_result:
            return ScoringResult(points=0, margin=None, exact_match=False)
        
        actual_value = self.algorithms.parse_boolean_value(actual_result.actual_value)
        
        return self.algorithms.score_boolean_prediction(predicted_value, actual_value)
    
    async def _score_count(
        self,
        pick: Pick,
        results: List[Result]
    ) -> ScoringResult:
        """Score count predictions."""
        predicted_count = self.algorithms.parse_lap_number(pick.prop_value)  # Reuse lap parser
        
        actual_result = results[0] if results else None
        if not actual_result:
            return ScoringResult(points=0, margin=None, exact_match=False)
        
        actual_count = self.algorithms.parse_lap_number(actual_result.actual_value)
        
        return self.algorithms.score_count_prediction(predicted_count, actual_count)
    
    def _organize_results(self, results: List[Result]) -> Dict[PropType, List[Result]]:
        """
        Organize results by prop type for efficient lookup.
        
        Args:
            results: List of Result objects
            
        Returns:
            Dict mapping PropType to list of Results
        """
        results_by_type: Dict[PropType, List[Result]] = {}
        
        for result in results:
            if result.prop_type not in results_by_type:
                results_by_type[result.prop_type] = []
            results_by_type[result.prop_type].append(result)
        
        return results_by_type
    
    async def _create_audit_log(
        self,
        event_id: UUID,
        picks_scored: int,
        scores_created: int,
        scores_updated: int,
        total_points: int
    ):
        """Create audit log entry for scoring operation."""
        audit = Audit(
            entity_type=EntityType.EVENT,
            entity_id=event_id,
            action=AuditAction.SCORE_CALCULATED,
            audit_metadata={
                "picks_scored": picks_scored,
                "scores_created": scores_created,
                "scores_updated": scores_updated,
                "total_points": total_points
            }
        )
        self.db.add(audit)
    
    async def get_event_scores(
        self,
        event_id: UUID,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all scores for an event with user information.
        
        Args:
            event_id: Event UUID
            limit: Maximum number of scores to return
            
        Returns:
            List of score dictionaries with user info
        """
        query = (
            select(Score, Pick)
            .join(Pick, Score.pick_id == Pick.id)
            .where(Pick.event_id == event_id)
            .order_by(Score.points.desc())
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        rows = result.all()
        
        scores = []
        for score, pick in rows:
            scores.append({
                "score_id": str(score.id),
                "user_id": str(score.user_id),
                "pick_id": str(pick.id),
                "prop_type": pick.prop_type.value,
                "predicted_value": pick.prop_value,
                "points": score.points,
                "margin": score.margin,
                "exact_match": score.exact_match,
                "metadata": score.scoring_metadata
            })
        
        return scores

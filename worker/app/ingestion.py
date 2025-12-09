"""
Database ingestion service for storing FastF1 data.
"""
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .database import Event, EventStatus, Result, get_db_session
from .fastf1_client import fastf1_client
from .logger import logger
from .transformers import transformer


class IngestionService:
    """Service for ingesting FastF1 data into the database."""
    
    def __init__(self):
        """Initialize ingestion service."""
        self.logger = logger.bind(component="ingestion")
    
    async def ingest_season_schedule(self, year: int) -> int:
        """
        Ingest the complete season schedule for a year.
        
        Args:
            year: F1 season year
            
        Returns:
            Number of events created/updated
        """
        try:
            self.logger.info("Starting season schedule ingestion", year=year)
            
            # Fetch schedule from FastF1
            schedule = await fastf1_client.get_season_schedule(year)
            
            # Transform to Event models
            events = transformer.transform_schedule_to_events(schedule, year)
            
            # Store in database
            events_created = 0
            async for session in get_db_session():
                for event in events:
                    # Check if event already exists
                    query = select(Event).where(
                        Event.year == event.year,
                        Event.round_number == event.round_number,
                        Event.session_type == event.session_type
                    )
                    result = await session.execute(query)
                    existing_event = result.scalar_one_or_none()
                    
                    if existing_event:
                        # Update existing event
                        existing_event.name = event.name
                        existing_event.circuit_id = event.circuit_id
                        existing_event.circuit_name = event.circuit_name
                        existing_event.start_time = event.start_time
                        existing_event.end_time = event.end_time
                        existing_event.status = event.status
                        self.logger.debug(
                            "Updated existing event",
                            event_id=str(existing_event.id),
                            event_name=event.name
                        )
                    else:
                        # Create new event
                        session.add(event)
                        events_created += 1
                        self.logger.debug(
                            "Created new event",
                            event_id=str(event.id),
                            event_name=event.name
                        )
                
                await session.commit()
            
            self.logger.info(
                "Season schedule ingestion complete",
                year=year,
                events_created=events_created,
                total_events=len(events)
            )
            
            return events_created
            
        except Exception as e:
            self.logger.error(
                "Failed to ingest season schedule",
                year=year,
                error=str(e)
            )
            raise
    
    async def ingest_session_results(
        self,
        event_id: UUID,
        year: int,
        round_number: int,
        session_type: str
    ) -> bool:
        """
        Ingest results for a specific session.
        
        Args:
            event_id: Event UUID
            year: Season year
            round_number: Round number
            session_type: FastF1 session type code ('R', 'Q', etc.)
            
        Returns:
            True if results were successfully ingested
        """
        try:
            self.logger.info(
                "Starting session results ingestion",
                event_id=str(event_id),
                year=year,
                round=round_number,
                session=session_type
            )
            
            # Fetch session data from FastF1
            session_data = await fastf1_client.get_session_data(
                year, round_number, session_type
            )
            
            if not session_data:
                self.logger.warning(
                    "No session data available yet",
                    event_id=str(event_id)
                )
                return False
            
            # Extract results based on session type
            if session_type == 'R':  # Race
                results_data = fastf1_client.extract_race_results(session_data)
                result_type = "race"
            elif session_type == 'Q':  # Qualifying
                results_data = fastf1_client.extract_qualifying_results(session_data)
                result_type = "qualifying"
            else:
                self.logger.info(
                    "Session type not supported for results ingestion",
                    session_type=session_type
                )
                return False
            
            if not results_data:
                self.logger.warning(
                    "No results data extracted",
                    event_id=str(event_id)
                )
                return False
            
            # Transform to Result models
            results = transformer.transform_results_to_db(
                results_data, str(event_id), result_type
            )
            
            # Store in database
            async for db_session in get_db_session():
                # Delete existing results for this event (idempotent)
                delete_query = select(Result).where(Result.event_id == event_id)
                existing_results = await db_session.execute(delete_query)
                for existing_result in existing_results.scalars():
                    await db_session.delete(existing_result)
                
                # Add new results
                for result in results:
                    db_session.add(result)
                
                # Update event status
                event_query = select(Event).where(Event.id == event_id)
                event_result = await db_session.execute(event_query)
                event = event_result.scalar_one_or_none()
                
                if event:
                    event.status = EventStatus.COMPLETED
                
                await db_session.commit()
            
            self.logger.info(
                "Session results ingestion complete",
                event_id=str(event_id),
                results_count=len(results)
            )
            
            # Trigger scoring after successful ingestion
            try:
                await self._trigger_scoring(event_id)
            except Exception as e:
                self.logger.error(
                    "Failed to trigger scoring",
                    event_id=str(event_id),
                    error=str(e)
                )
                # Don't fail the ingestion if scoring fails
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Failed to ingest session results",
                event_id=str(event_id),
                error=str(e)
            )
            return False
    
    async def poll_for_session_data(self, event_id: UUID) -> bool:
        """
        Poll for session data availability and ingest if ready.
        
        Args:
            event_id: Event UUID
            
        Returns:
            True if data was ingested, False if not yet available
        """
        try:
            # Get event from database
            async for session in get_db_session():
                query = select(Event).where(Event.id == event_id)
                result = await session.execute(query)
                event = result.scalar_one_or_none()
                
                if not event:
                    self.logger.error(
                        "Event not found",
                        event_id=str(event_id)
                    )
                    return False
                
                # Check if session has ended
                from datetime import timezone as tz
                now = datetime.now(tz.utc)
                # Ensure end_time is timezone-aware for comparison
                end_time = event.end_time
                if end_time.tzinfo is None:
                    end_time = end_time.replace(tzinfo=tz.utc)
                if end_time > now:
                    self.logger.info(
                        "Session not yet ended",
                        event_id=str(event_id),
                        end_time=event.end_time.isoformat()
                    )
                    return False
                
                # Check if enough time has passed (30 min delay)
                time_since_end = now - end_time
                if time_since_end < timedelta(minutes=30):
                    self.logger.info(
                        "Too soon to check for data",
                        event_id=str(event_id),
                        time_since_end=str(time_since_end)
                    )
                    return False
                
                # Map session type to FastF1 code
                session_type_map = {
                    'practice_1': 'FP1',
                    'practice_2': 'FP2',
                    'practice_3': 'FP3',
                    'sprint_qualifying': 'SQ',
                    'sprint': 'S',
                    'qualifying': 'Q',
                    'race': 'R',
                }
                
                fastf1_session_type = session_type_map.get(event.session_type.value)
                if not fastf1_session_type:
                    self.logger.warning(
                        "Unknown session type",
                        event_id=str(event_id),
                        session_type=event.session_type.value
                    )
                    return False
                
                # Attempt to ingest results
                return await self.ingest_session_results(
                    event_id,
                    event.year,
                    event.round_number,
                    fastf1_session_type
                )
                
        except Exception as e:
            self.logger.error(
                "Failed to poll for session data",
                event_id=str(event_id),
                error=str(e)
            )
            return False
    
    async def _trigger_scoring(self, event_id: UUID):
        """
        Trigger scoring for a completed event.
        
        This calls the backend API to score all predictions for the event.
        
        Args:
            event_id: Event UUID
        """
        import httpx
        import os
        
        # Get backend API URL from environment
        api_url = os.getenv("BACKEND_API_URL", "http://localhost:8000")
        
        self.logger.info(
            "Triggering scoring for event",
            event_id=str(event_id),
            api_url=api_url
        )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{api_url}/api/scores/trigger",
                    json={"event_id": str(event_id)},
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.logger.info(
                        "Scoring completed successfully",
                        event_id=str(event_id),
                        picks_scored=result.get("picks_scored", 0),
                        scores_created=result.get("scores_created", 0)
                    )
                else:
                    self.logger.warning(
                        "Scoring request failed",
                        event_id=str(event_id),
                        status_code=response.status_code,
                        response=response.text
                    )
        except Exception as e:
            self.logger.error(
                "Failed to call scoring API",
                event_id=str(event_id),
                error=str(e)
            )
            raise


# Global ingestion service instance
ingestion_service = IngestionService()

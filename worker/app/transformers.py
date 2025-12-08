"""
Data transformation functions to convert FastF1 data to database schema.
"""
from datetime import datetime, timedelta
from typing import Dict, List
from uuid import uuid4

import pandas as pd
import pytz

from .database import Event, EventStatus, EventType, Result
from .logger import logger
from .models import PropType, Result, ResultSource


class DataTransformer:
    """Transform FastF1 data to database models."""
    
    def __init__(self):
        """Initialize transformer."""
        self.logger = logger.bind(component="transformer")
    
    def transform_schedule_to_events(
        self,
        schedule: pd.DataFrame,
        year: int
    ) -> List[Event]:
        """
        Transform FastF1 schedule to Event models.
        
        Args:
            schedule: FastF1 schedule DataFrame
            year: Season year
            
        Returns:
            List of Event model instances
        """
        events = []
        
        try:
            for idx, row in schedule.iterrows():
                round_number = int(row['RoundNumber'])
                event_name = str(row['EventName'])
                
                # Get circuit information
                circuit_name = str(row['Location']) if 'Location' in row else event_name
                circuit_id = self._normalize_circuit_id(circuit_name)
                
                # Map session names to types
                session_type_map = {
                    'Practice 1': 'practice_1',
                    'Practice 2': 'practice_2',
                    'Practice 3': 'practice_3',
                    'Sprint Shootout': 'sprint_qualifying',
                    'Sprint': 'sprint',
                    'Qualifying': 'qualifying',
                    'Race': 'race',
                }
                
                # Iterate through Session1-5
                for session_num in range(1, 6):
                    session_col = f'Session{session_num}'
                    session_date_col = f'Session{session_num}DateUtc'
                    
                    if session_col in row and pd.notna(row[session_col]):
                        session_name = str(row[session_col])
                        
                        # Get session type
                        session_type_str = session_type_map.get(session_name)
                        if not session_type_str:
                            continue  # Skip unknown session types
                        
                        # Skip practice sessions - we only care about qualifying and races
                        if session_type_str in ['practice_1', 'practice_2', 'practice_3']:
                            continue
                        
                        # Get session date
                        if session_date_col in row and pd.notna(row[session_date_col]):
                            session_date = pd.to_datetime(row[session_date_col])
                            
                            # Ensure timezone aware
                            if session_date.tzinfo is None:
                                session_date = pytz.UTC.localize(session_date)
                            
                            # Estimate session duration
                            duration = self._estimate_session_duration(session_type_str)
                            
                            # Determine status based on current time
                            now = datetime.now(pytz.UTC)
                            session_dt = session_date.to_pydatetime()
                            if session_dt > now:
                                status = EventStatus.SCHEDULED
                            elif session_dt <= now < (session_dt + duration):
                                status = EventStatus.LIVE
                            else:
                                status = EventStatus.COMPLETED
                            
                            event = Event(
                                id=uuid4(),
                                name=f"{event_name} - {session_name}",
                                circuit_id=circuit_id,
                                circuit_name=circuit_name,
                                session_type=EventType[session_type_str.upper()],
                                round_number=round_number,
                                year=year,
                                start_time=session_dt,
                                end_time=session_dt + duration,
                                status=status,
                            )
                            
                            events.append(event)
            
            self.logger.info(
                "Transformed schedule to events",
                year=year,
                events_count=len(events)
            )
            
            return events
            
        except Exception as e:
            self.logger.error(
                "Failed to transform schedule",
                year=year,
                error=str(e)
            )
            raise
    
    def transform_results_to_db(
        self,
        results_data: List[Dict],
        event_id: str,
        result_type: str = "race"
    ) -> List[Result]:
        """
        Transform FastF1 results to Result models.
        
        Args:
            results_data: List of result dictionaries from FastF1
            event_id: Event UUID
            result_type: Type of result ('race', 'qualifying', etc.)
            
        Returns:
            List of Result model instances
        """
        results = []
        
        try:
            for result_data in results_data:
                position = result_data.get('position')
                
                # Determine prop_type based on result type and position
                # Only create results for positions we have prop types for
                prop_type_str = None
                
                if result_type == "race":
                    if position == 1:
                        prop_type_str = "race_winner"
                    elif position == 2:
                        prop_type_str = "podium_p2"
                    elif position == 3:
                        prop_type_str = "podium_p3"
                    # Skip other positions - we don't have prop types for them
                elif result_type == "qualifying":
                    if position == 1:
                        prop_type_str = "pole_position"
                    # Skip other qualifying positions for now
                
                # Skip if we don't have a prop type for this position
                if not prop_type_str:
                    continue
                
                # Convert string to PropType enum
                try:
                    prop_type = PropType(prop_type_str)
                except ValueError:
                    self.logger.warning(f"Unknown prop_type: {prop_type_str}, skipping")
                    continue
                
                # Create result record
                result = Result(
                    id=uuid4(),
                    event_id=event_id,
                    prop_type=prop_type,
                    actual_value=result_data.get('driver_name', ''),
                    source=ResultSource.FASTF1,
                    result_metadata={
                        'position': result_data.get('position'),
                        'driver_number': result_data.get('driver_number'),
                        'driver_code': result_data.get('driver_code'),
                        'team_name': result_data.get('team_name'),
                        'status': result_data.get('status'),
                        'points': result_data.get('points'),
                        **{k: v for k, v in result_data.items() 
                           if k not in ['position', 'driver_number', 'driver_code', 'team_name', 'status', 'points']}
                    }
                )
                
                results.append(result)
            
            self.logger.info(
                "Transformed results to database models",
                event_id=event_id,
                results_count=len(results)
            )
            
            return results
            
        except Exception as e:
            self.logger.error(
                "Failed to transform results",
                event_id=event_id,
                error=str(e)
            )
            raise
    
    def _normalize_circuit_id(self, circuit_name: str) -> str:
        """
        Normalize circuit name to a consistent ID.
        
        Args:
            circuit_name: Circuit name from FastF1
            
        Returns:
            Normalized circuit ID
        """
        # Simple normalization - lowercase and replace spaces with underscores
        return circuit_name.lower().replace(' ', '_').replace('-', '_')
    
    def _estimate_session_duration(self, session_type: str) -> timedelta:
        """
        Estimate session duration based on type.
        
        Args:
            session_type: Session type string
            
        Returns:
            Estimated duration as timedelta
        """
        durations = {
            'practice_1': timedelta(hours=1),
            'practice_2': timedelta(hours=1),
            'practice_3': timedelta(hours=1),
            'sprint_qualifying': timedelta(hours=1),
            'sprint': timedelta(hours=1),
            'qualifying': timedelta(hours=1),
            'race': timedelta(hours=2),
        }
        
        return durations.get(session_type, timedelta(hours=2))


# Global transformer instance
transformer = DataTransformer()

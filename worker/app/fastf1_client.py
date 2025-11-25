"""
FastF1 client for fetching Formula 1 data.
"""
from datetime import datetime
from typing import Dict, List, Optional

import fastf1
import pandas as pd

from .config import settings
from .logger import logger

# Configure FastF1 cache
fastf1.Cache.enable_cache(str(settings.FASTF1_CACHE_DIR))


class FastF1Client:
    """Client for fetching F1 data using FastF1 library."""
    
    def __init__(self):
        """Initialize FastF1 client."""
        self.logger = logger.bind(component="fastf1_client")
    
    async def get_season_schedule(self, year: int) -> pd.DataFrame:
        """
        Fetch the complete season schedule for a given year.
        
        Args:
            year: F1 season year
            
        Returns:
            DataFrame with season schedule
        """
        try:
            self.logger.info("Fetching season schedule", year=year)
            schedule = fastf1.get_event_schedule(year)
            self.logger.info(
                "Season schedule fetched",
                year=year,
                events_count=len(schedule)
            )
            return schedule
        except Exception as e:
            self.logger.error(
                "Failed to fetch season schedule",
                year=year,
                error=str(e)
            )
            raise
    
    async def get_session_data(
        self,
        year: int,
        round_number: int,
        session_type: str
    ) -> Optional[fastf1.core.Session]:
        """
        Fetch session data for a specific event and session type.
        
        Args:
            year: F1 season year
            round_number: Round number in the season
            session_type: Type of session ('FP1', 'FP2', 'FP3', 'Q', 'S', 'R')
            
        Returns:
            Session object with loaded data, or None if not available
        """
        try:
            self.logger.info(
                "Fetching session data",
                year=year,
                round=round_number,
                session=session_type
            )
            
            # Get the session
            session = fastf1.get_session(year, round_number, session_type)
            
            # Load session data (this can take time and may fail if data not available)
            session.load()
            
            self.logger.info(
                "Session data loaded",
                year=year,
                round=round_number,
                session=session_type,
                event_name=session.event['EventName']
            )
            
            return session
            
        except Exception as e:
            self.logger.warning(
                "Session data not available or failed to load",
                year=year,
                round=round_number,
                session=session_type,
                error=str(e)
            )
            return None
    
    def extract_race_results(self, session: fastf1.core.Session) -> List[Dict]:
        """
        Extract race results from a session.
        
        Args:
            session: Loaded FastF1 session object
            
        Returns:
            List of result dictionaries
        """
        try:
            results = []
            
            if session.results is None or session.results.empty:
                self.logger.warning("No results available for session")
                return results
            
            for idx, row in session.results.iterrows():
                result = {
                    'position': int(row['Position']) if pd.notna(row['Position']) else None,
                    'driver_number': str(row['DriverNumber']) if pd.notna(row['DriverNumber']) else None,
                    'driver_code': str(row['Abbreviation']) if pd.notna(row['Abbreviation']) else None,
                    'driver_name': f"{row['FirstName']} {row['LastName']}" if pd.notna(row['FirstName']) else None,
                    'team_name': str(row['TeamName']) if pd.notna(row['TeamName']) else None,
                    'grid_position': int(row['GridPosition']) if pd.notna(row['GridPosition']) else None,
                    'status': str(row['Status']) if pd.notna(row['Status']) else None,
                    'points': float(row['Points']) if pd.notna(row['Points']) else 0.0,
                }
                
                # Add timing data if available
                if 'Time' in row and pd.notna(row['Time']):
                    result['finish_time'] = str(row['Time'])
                
                results.append(result)
            
            self.logger.info(
                "Extracted race results",
                results_count=len(results)
            )
            
            return results
            
        except Exception as e:
            self.logger.error(
                "Failed to extract race results",
                error=str(e)
            )
            return []
    
    def extract_qualifying_results(self, session: fastf1.core.Session) -> List[Dict]:
        """
        Extract qualifying results from a session.
        
        Args:
            session: Loaded FastF1 session object
            
        Returns:
            List of result dictionaries
        """
        try:
            results = []
            
            if session.results is None or session.results.empty:
                self.logger.warning("No qualifying results available")
                return results
            
            for idx, row in session.results.iterrows():
                result = {
                    'position': int(row['Position']) if pd.notna(row['Position']) else None,
                    'driver_number': str(row['DriverNumber']) if pd.notna(row['DriverNumber']) else None,
                    'driver_code': str(row['Abbreviation']) if pd.notna(row['Abbreviation']) else None,
                    'driver_name': f"{row['FirstName']} {row['LastName']}" if pd.notna(row['FirstName']) else None,
                    'team_name': str(row['TeamName']) if pd.notna(row['TeamName']) else None,
                }
                
                # Add Q1, Q2, Q3 times if available
                for q_session in ['Q1', 'Q2', 'Q3']:
                    if q_session in row and pd.notna(row[q_session]):
                        result[f'{q_session.lower()}_time'] = str(row[q_session])
                
                results.append(result)
            
            self.logger.info(
                "Extracted qualifying results",
                results_count=len(results)
            )
            
            return results
            
        except Exception as e:
            self.logger.error(
                "Failed to extract qualifying results",
                error=str(e)
            )
            return []
    
    def extract_fastest_lap(self, session: fastf1.core.Session) -> Optional[Dict]:
        """
        Extract fastest lap information from a session.
        
        Args:
            session: Loaded FastF1 session object
            
        Returns:
            Dictionary with fastest lap info, or None
        """
        try:
            if session.laps is None or session.laps.empty:
                return None
            
            # Get the fastest lap
            fastest_lap = session.laps.pick_fastest()
            
            if fastest_lap is None or fastest_lap.empty:
                return None
            
            return {
                'driver_number': str(fastest_lap['DriverNumber']),
                'lap_time': str(fastest_lap['LapTime']),
                'lap_number': int(fastest_lap['LapNumber']),
            }
            
        except Exception as e:
            self.logger.error(
                "Failed to extract fastest lap",
                error=str(e)
            )
            return None
    
    def is_session_data_available(
        self,
        year: int,
        round_number: int,
        session_type: str
    ) -> bool:
        """
        Check if session data is available without fully loading it.
        
        Args:
            year: F1 season year
            round_number: Round number
            session_type: Session type
            
        Returns:
            True if data appears to be available
        """
        try:
            session = fastf1.get_session(year, round_number, session_type)
            # Try to load just the results without full telemetry
            session.load(telemetry=False, weather=False, messages=False)
            return session.results is not None and not session.results.empty
        except Exception:
            return False


# Global client instance
fastf1_client = FastF1Client()

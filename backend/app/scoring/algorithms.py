"""
Scoring algorithms for different prediction types.

Each algorithm takes a user's prediction and the actual result,
then calculates points, margin of error, and whether it's an exact match.
"""

from typing import Dict, Any, Optional
import json
from app.models.pick import PropType


class ScoringResult:
    """Result of a scoring calculation."""
    
    def __init__(
        self,
        points: int,
        margin: Optional[float] = None,
        exact_match: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.points = points
        self.margin = margin
        self.exact_match = exact_match
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            "points": self.points,
            "margin": self.margin,
            "exact_match": self.exact_match,
            "metadata": self.metadata
        }


class ScoringAlgorithms:
    """Collection of scoring algorithms for different prediction types."""
    
    # Point values for different accuracy levels
    EXACT_MATCH_POINTS = 10
    NEAR_MATCH_POINTS = {
        1: 7,  # Off by 1 position
        2: 4,  # Off by 2 positions
        3: 2,  # Off by 3 positions
    }
    
    @staticmethod
    def score_driver_position(
        predicted_driver: str,
        actual_driver: str,
        all_results: Dict[str, int],
        prop_type: PropType
    ) -> ScoringResult:
        """
        Score predictions for driver positions (race winner, podium, pole, etc.).
        
        Args:
            predicted_driver: Driver code predicted by user (e.g., "VER", "HAM")
            actual_driver: Actual driver who achieved the position
            all_results: Dict mapping driver codes to finishing positions
            prop_type: Type of prediction being scored
            
        Returns:
            ScoringResult with points and margin
        """
        # Exact match
        if predicted_driver == actual_driver:
            return ScoringResult(
                points=ScoringAlgorithms.EXACT_MATCH_POINTS,
                margin=0.0,
                exact_match=True,
                metadata={
                    "predicted_driver": predicted_driver,
                    "actual_driver": actual_driver,
                    "result": "exact_match"
                }
            )
        
        # Get predicted driver's actual position
        predicted_position = all_results.get(predicted_driver)
        
        # Driver didn't finish (DNF, DNS, DSQ)
        if predicted_position is None:
            return ScoringResult(
                points=0,
                margin=20.0,  # Maximum penalty
                exact_match=False,
                metadata={
                    "predicted_driver": predicted_driver,
                    "actual_driver": actual_driver,
                    "result": "dnf",
                    "reason": "Predicted driver did not finish"
                }
            )
        
        # Get expected position based on prop type
        expected_position = ScoringAlgorithms._get_expected_position(prop_type)
        position_diff = abs(predicted_position - expected_position)
        
        # Award partial points based on how close the prediction was
        points = ScoringAlgorithms.NEAR_MATCH_POINTS.get(position_diff, 0)
        
        return ScoringResult(
            points=points,
            margin=float(position_diff),
            exact_match=False,
            metadata={
                "predicted_driver": predicted_driver,
                "actual_driver": actual_driver,
                "predicted_position": predicted_position,
                "expected_position": expected_position,
                "position_diff": position_diff,
                "result": "near_match" if points > 0 else "miss"
            }
        )
    
    @staticmethod
    def score_fastest_lap(
        predicted_driver: str,
        actual_driver: str,
        all_lap_times: Dict[str, float]
    ) -> ScoringResult:
        """
        Score fastest lap predictions.
        
        Args:
            predicted_driver: Driver predicted to have fastest lap
            actual_driver: Driver who actually had fastest lap
            all_lap_times: Dict mapping driver codes to their fastest lap times
            
        Returns:
            ScoringResult with points and margin
        """
        # Exact match
        if predicted_driver == actual_driver:
            return ScoringResult(
                points=ScoringAlgorithms.EXACT_MATCH_POINTS,
                margin=0.0,
                exact_match=True,
                metadata={
                    "predicted_driver": predicted_driver,
                    "actual_driver": actual_driver,
                    "result": "exact_match"
                }
            )
        
        # Get time difference
        predicted_time = all_lap_times.get(predicted_driver)
        actual_time = all_lap_times.get(actual_driver)
        
        if predicted_time is None or actual_time is None:
            return ScoringResult(
                points=0,
                margin=None,
                exact_match=False,
                metadata={
                    "predicted_driver": predicted_driver,
                    "actual_driver": actual_driver,
                    "result": "no_data"
                }
            )
        
        # Award partial points based on time difference
        time_diff = abs(predicted_time - actual_time)
        
        if time_diff < 0.5:  # Within 0.5 seconds
            points = 7
        elif time_diff < 1.0:  # Within 1 second
            points = 4
        elif time_diff < 2.0:  # Within 2 seconds
            points = 2
        else:
            points = 0
        
        return ScoringResult(
            points=points,
            margin=time_diff,
            exact_match=False,
            metadata={
                "predicted_driver": predicted_driver,
                "actual_driver": actual_driver,
                "predicted_time": predicted_time,
                "actual_time": actual_time,
                "time_diff": time_diff,
                "result": "near_match" if points > 0 else "miss"
            }
        )
    
    @staticmethod
    def score_lap_time(
        predicted_time: float,
        actual_time: float
    ) -> ScoringResult:
        """
        Score lap time predictions.
        
        Args:
            predicted_time: Predicted lap time in seconds
            actual_time: Actual lap time in seconds
            
        Returns:
            ScoringResult with points based on percentage accuracy
        """
        time_diff = abs(predicted_time - actual_time)
        percentage_error = (time_diff / actual_time) * 100
        
        # Award points based on percentage accuracy
        if percentage_error < 0.5:  # Within 0.5%
            points = 10
        elif percentage_error < 1.0:  # Within 1%
            points = 8
        elif percentage_error < 2.0:  # Within 2%
            points = 6
        elif percentage_error < 3.0:  # Within 3%
            points = 4
        elif percentage_error < 5.0:  # Within 5%
            points = 2
        else:
            points = 0
        
        exact_match = time_diff < 0.01  # Within 0.01 seconds
        
        return ScoringResult(
            points=points,
            margin=time_diff,
            exact_match=exact_match,
            metadata={
                "predicted_time": predicted_time,
                "actual_time": actual_time,
                "time_diff": time_diff,
                "percentage_error": percentage_error
            }
        )
    
    @staticmethod
    def score_pit_window(
        predicted_lap: int,
        actual_lap: int
    ) -> ScoringResult:
        """
        Score pit window predictions.
        
        Args:
            predicted_lap: Predicted lap number for pit stop
            actual_lap: Actual lap number of pit stop
            
        Returns:
            ScoringResult with points based on lap accuracy
        """
        lap_diff = abs(predicted_lap - actual_lap)
        
        # Award points based on lap accuracy
        if lap_diff == 0:
            points = 10
            exact_match = True
        elif lap_diff == 1:
            points = 7
            exact_match = False
        elif lap_diff == 2:
            points = 5
            exact_match = False
        elif lap_diff == 3:
            points = 3
            exact_match = False
        elif lap_diff <= 5:
            points = 1
            exact_match = False
        else:
            points = 0
            exact_match = False
        
        return ScoringResult(
            points=points,
            margin=float(lap_diff),
            exact_match=exact_match,
            metadata={
                "predicted_lap": predicted_lap,
                "actual_lap": actual_lap,
                "lap_diff": lap_diff
            }
        )
    
    @staticmethod
    def score_boolean_prediction(
        predicted_value: bool,
        actual_value: bool
    ) -> ScoringResult:
        """
        Score boolean predictions (e.g., safety car yes/no).
        
        Args:
            predicted_value: User's prediction (True/False)
            actual_value: Actual outcome (True/False)
            
        Returns:
            ScoringResult with full points for correct, zero for incorrect
        """
        exact_match = predicted_value == actual_value
        points = ScoringAlgorithms.EXACT_MATCH_POINTS if exact_match else 0
        
        return ScoringResult(
            points=points,
            margin=0.0 if exact_match else 1.0,
            exact_match=exact_match,
            metadata={
                "predicted_value": predicted_value,
                "actual_value": actual_value
            }
        )
    
    @staticmethod
    def score_count_prediction(
        predicted_count: int,
        actual_count: int
    ) -> ScoringResult:
        """
        Score count predictions (e.g., total pit stops).
        
        Args:
            predicted_count: Predicted count
            actual_count: Actual count
            
        Returns:
            ScoringResult with points based on accuracy
        """
        diff = abs(predicted_count - actual_count)
        
        if diff == 0:
            points = 10
            exact_match = True
        elif diff == 1:
            points = 6
            exact_match = False
        elif diff == 2:
            points = 3
            exact_match = False
        else:
            points = 0
            exact_match = False
        
        return ScoringResult(
            points=points,
            margin=float(diff),
            exact_match=exact_match,
            metadata={
                "predicted_count": predicted_count,
                "actual_count": actual_count,
                "diff": diff
            }
        )
    
    @staticmethod
    def _get_expected_position(prop_type: PropType) -> int:
        """Get the expected finishing position for a prop type."""
        position_map = {
            PropType.RACE_WINNER: 1,
            PropType.PODIUM_P1: 1,
            PropType.PODIUM_P2: 2,
            PropType.PODIUM_P3: 3,
            PropType.POLE_POSITION: 1,
        }
        return position_map.get(prop_type, 1)
    
    @staticmethod
    def parse_driver_code(value: str) -> str:
        """
        Parse and normalize driver code from prediction value.
        
        Args:
            value: Raw prediction value (could be JSON or plain string)
            
        Returns:
            Normalized driver code (e.g., "VER", "HAM")
        """
        try:
            # Try parsing as JSON first
            data = json.loads(value)
            if isinstance(data, dict):
                return data.get("driver_code", "").upper()
            return str(data).upper()
        except (json.JSONDecodeError, ValueError):
            # Plain string
            return value.upper().strip()
    
    @staticmethod
    def parse_time_value(value: str) -> float:
        """
        Parse time value from prediction.
        
        Args:
            value: Time value (could be JSON or plain string)
            
        Returns:
            Time in seconds
        """
        try:
            data = json.loads(value)
            if isinstance(data, dict):
                return float(data.get("time", 0))
            return float(data)
        except (json.JSONDecodeError, ValueError):
            return float(value)
    
    @staticmethod
    def parse_lap_number(value: str) -> int:
        """
        Parse lap number from prediction.
        
        Args:
            value: Lap number (could be JSON or plain string)
            
        Returns:
            Lap number as integer
        """
        try:
            data = json.loads(value)
            if isinstance(data, dict):
                return int(data.get("lap", 0))
            return int(data)
        except (json.JSONDecodeError, ValueError):
            return int(value)
    
    @staticmethod
    def parse_boolean_value(value: str) -> bool:
        """
        Parse boolean value from prediction.
        
        Args:
            value: Boolean value (could be JSON or plain string)
            
        Returns:
            Boolean value
        """
        try:
            data = json.loads(value)
            if isinstance(data, dict):
                return bool(data.get("value", False))
            return bool(data)
        except (json.JSONDecodeError, ValueError):
            return value.lower() in ("true", "yes", "1")

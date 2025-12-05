"""
Unit tests for scoring algorithms.
"""

import pytest
from app.scoring.algorithms import ScoringAlgorithms, ScoringResult
from app.models.pick import PropType


class TestDriverPositionScoring:
    """Test driver position scoring (race winner, podium, pole)."""
    
    def test_exact_match(self):
        """Test exact match scoring."""
        result = ScoringAlgorithms.score_driver_position(
            predicted_driver="VER",
            actual_driver="VER",
            all_results={"VER": 1, "HAM": 2, "LEC": 3},
            prop_type=PropType.RACE_WINNER
        )
        
        assert result.points == 10
        assert result.exact_match is True
        assert result.margin == 0.0
        assert result.metadata["result"] == "exact_match"
    
    def test_off_by_one_position(self):
        """Test prediction off by one position."""
        result = ScoringAlgorithms.score_driver_position(
            predicted_driver="HAM",
            actual_driver="VER",
            all_results={"VER": 1, "HAM": 2, "LEC": 3},
            prop_type=PropType.RACE_WINNER
        )
        
        assert result.points == 7
        assert result.exact_match is False
        assert result.margin == 1.0
        assert result.metadata["position_diff"] == 1
    
    def test_off_by_two_positions(self):
        """Test prediction off by two positions."""
        result = ScoringAlgorithms.score_driver_position(
            predicted_driver="LEC",
            actual_driver="VER",
            all_results={"VER": 1, "HAM": 2, "LEC": 3},
            prop_type=PropType.RACE_WINNER
        )
        
        assert result.points == 4
        assert result.exact_match is False
        assert result.margin == 2.0
    
    def test_off_by_three_positions(self):
        """Test prediction off by three positions."""
        result = ScoringAlgorithms.score_driver_position(
            predicted_driver="SAI",
            actual_driver="VER",
            all_results={"VER": 1, "HAM": 2, "LEC": 3, "SAI": 4},
            prop_type=PropType.RACE_WINNER
        )
        
        assert result.points == 2
        assert result.exact_match is False
        assert result.margin == 3.0
    
    def test_driver_dnf(self):
        """Test prediction for driver who didn't finish."""
        result = ScoringAlgorithms.score_driver_position(
            predicted_driver="BOT",
            actual_driver="VER",
            all_results={"VER": 1, "HAM": 2, "LEC": 3},
            prop_type=PropType.RACE_WINNER
        )
        
        assert result.points == 0
        assert result.exact_match is False
        assert result.margin == 20.0
        assert result.metadata["result"] == "dnf"
    
    def test_podium_p2_exact(self):
        """Test P2 podium prediction exact match."""
        result = ScoringAlgorithms.score_driver_position(
            predicted_driver="HAM",
            actual_driver="HAM",
            all_results={"VER": 1, "HAM": 2, "LEC": 3},
            prop_type=PropType.PODIUM_P2
        )
        
        assert result.points == 10
        assert result.exact_match is True


class TestFastestLapScoring:
    """Test fastest lap scoring."""
    
    def test_exact_match(self):
        """Test exact fastest lap prediction."""
        result = ScoringAlgorithms.score_fastest_lap(
            predicted_driver="VER",
            actual_driver="VER",
            all_lap_times={"VER": 90.123, "HAM": 90.456, "LEC": 90.789}
        )
        
        assert result.points == 10
        assert result.exact_match is True
        assert result.margin == 0.0
    
    def test_within_half_second(self):
        """Test prediction within 0.5 seconds."""
        result = ScoringAlgorithms.score_fastest_lap(
            predicted_driver="HAM",
            actual_driver="VER",
            all_lap_times={"VER": 90.123, "HAM": 90.456, "LEC": 90.789}
        )
        
        assert result.points == 7
        assert result.exact_match is False
        assert result.margin == pytest.approx(0.333, abs=0.01)
    
    def test_within_one_second(self):
        """Test prediction within 1 second."""
        result = ScoringAlgorithms.score_fastest_lap(
            predicted_driver="LEC",
            actual_driver="VER",
            all_lap_times={"VER": 90.123, "HAM": 90.456, "LEC": 90.789}
        )
        
        assert result.points == 4
        assert result.margin == pytest.approx(0.666, abs=0.01)
    
    def test_no_lap_time_data(self):
        """Test when lap time data is missing."""
        result = ScoringAlgorithms.score_fastest_lap(
            predicted_driver="BOT",
            actual_driver="VER",
            all_lap_times={"VER": 90.123, "HAM": 90.456}
        )
        
        assert result.points == 0
        assert result.margin is None
        assert result.metadata["result"] == "no_data"


class TestLapTimeScoring:
    """Test lap time prediction scoring."""
    
    def test_within_half_percent(self):
        """Test prediction within 0.5% accuracy."""
        result = ScoringAlgorithms.score_lap_time(
            predicted_time=90.0,
            actual_time=90.4  # 0.44% error
        )
        
        assert result.points == 10
        assert result.margin == pytest.approx(0.4, abs=0.01)
    
    def test_within_one_percent(self):
        """Test prediction within 1% accuracy."""
        result = ScoringAlgorithms.score_lap_time(
            predicted_time=90.0,
            actual_time=90.8  # 0.89% error
        )
        
        assert result.points == 8
        assert result.metadata["percentage_error"] < 1.0
    
    def test_within_two_percent(self):
        """Test prediction within 2% accuracy."""
        result = ScoringAlgorithms.score_lap_time(
            predicted_time=90.0,
            actual_time=91.5  # 1.67% error
        )
        
        assert result.points == 6
    
    def test_within_three_percent(self):
        """Test prediction within 3% accuracy."""
        result = ScoringAlgorithms.score_lap_time(
            predicted_time=90.0,
            actual_time=92.5  # 2.78% error
        )
        
        assert result.points == 4
    
    def test_within_five_percent(self):
        """Test prediction within 5% accuracy."""
        result = ScoringAlgorithms.score_lap_time(
            predicted_time=90.0,
            actual_time=94.0  # 4.44% error
        )
        
        assert result.points == 2
    
    def test_more_than_five_percent(self):
        """Test prediction with more than 5% error."""
        result = ScoringAlgorithms.score_lap_time(
            predicted_time=90.0,
            actual_time=95.0  # 5.56% error
        )
        
        assert result.points == 0


class TestPitWindowScoring:
    """Test pit window prediction scoring."""
    
    def test_exact_lap(self):
        """Test exact lap prediction."""
        result = ScoringAlgorithms.score_pit_window(
            predicted_lap=15,
            actual_lap=15
        )
        
        assert result.points == 10
        assert result.exact_match is True
        assert result.margin == 0.0
    
    def test_off_by_one_lap(self):
        """Test prediction off by one lap."""
        result = ScoringAlgorithms.score_pit_window(
            predicted_lap=15,
            actual_lap=16
        )
        
        assert result.points == 7
        assert result.exact_match is False
        assert result.margin == 1.0
    
    def test_off_by_two_laps(self):
        """Test prediction off by two laps."""
        result = ScoringAlgorithms.score_pit_window(
            predicted_lap=15,
            actual_lap=17
        )
        
        assert result.points == 5
        assert result.margin == 2.0
    
    def test_off_by_five_laps(self):
        """Test prediction off by five laps."""
        result = ScoringAlgorithms.score_pit_window(
            predicted_lap=15,
            actual_lap=20
        )
        
        assert result.points == 1
        assert result.margin == 5.0
    
    def test_off_by_more_than_five_laps(self):
        """Test prediction off by more than five laps."""
        result = ScoringAlgorithms.score_pit_window(
            predicted_lap=15,
            actual_lap=22
        )
        
        assert result.points == 0
        assert result.margin == 7.0


class TestBooleanScoring:
    """Test boolean prediction scoring."""
    
    def test_correct_true(self):
        """Test correct true prediction."""
        result = ScoringAlgorithms.score_boolean_prediction(
            predicted_value=True,
            actual_value=True
        )
        
        assert result.points == 10
        assert result.exact_match is True
        assert result.margin == 0.0
    
    def test_correct_false(self):
        """Test correct false prediction."""
        result = ScoringAlgorithms.score_boolean_prediction(
            predicted_value=False,
            actual_value=False
        )
        
        assert result.points == 10
        assert result.exact_match is True
    
    def test_incorrect_prediction(self):
        """Test incorrect prediction."""
        result = ScoringAlgorithms.score_boolean_prediction(
            predicted_value=True,
            actual_value=False
        )
        
        assert result.points == 0
        assert result.exact_match is False
        assert result.margin == 1.0


class TestCountScoring:
    """Test count prediction scoring."""
    
    def test_exact_count(self):
        """Test exact count prediction."""
        result = ScoringAlgorithms.score_count_prediction(
            predicted_count=3,
            actual_count=3
        )
        
        assert result.points == 10
        assert result.exact_match is True
        assert result.margin == 0.0
    
    def test_off_by_one(self):
        """Test count off by one."""
        result = ScoringAlgorithms.score_count_prediction(
            predicted_count=3,
            actual_count=4
        )
        
        assert result.points == 6
        assert result.exact_match is False
        assert result.margin == 1.0
    
    def test_off_by_two(self):
        """Test count off by two."""
        result = ScoringAlgorithms.score_count_prediction(
            predicted_count=3,
            actual_count=5
        )
        
        assert result.points == 3
        assert result.margin == 2.0
    
    def test_off_by_more_than_two(self):
        """Test count off by more than two."""
        result = ScoringAlgorithms.score_count_prediction(
            predicted_count=3,
            actual_count=7
        )
        
        assert result.points == 0
        assert result.margin == 4.0


class TestValueParsing:
    """Test value parsing utilities."""
    
    def test_parse_driver_code_plain_string(self):
        """Test parsing plain string driver code."""
        result = ScoringAlgorithms.parse_driver_code("VER")
        assert result == "VER"
    
    def test_parse_driver_code_json(self):
        """Test parsing JSON driver code."""
        result = ScoringAlgorithms.parse_driver_code('{"driver_code": "HAM"}')
        assert result == "HAM"
    
    def test_parse_driver_code_lowercase(self):
        """Test parsing lowercase driver code."""
        result = ScoringAlgorithms.parse_driver_code("ver")
        assert result == "VER"
    
    def test_parse_time_value_plain(self):
        """Test parsing plain time value."""
        result = ScoringAlgorithms.parse_time_value("90.5")
        assert result == 90.5
    
    def test_parse_time_value_json(self):
        """Test parsing JSON time value."""
        result = ScoringAlgorithms.parse_time_value('{"time": 90.5}')
        assert result == 90.5
    
    def test_parse_lap_number_plain(self):
        """Test parsing plain lap number."""
        result = ScoringAlgorithms.parse_lap_number("15")
        assert result == 15
    
    def test_parse_lap_number_json(self):
        """Test parsing JSON lap number."""
        result = ScoringAlgorithms.parse_lap_number('{"lap": 15}')
        assert result == 15
    
    def test_parse_boolean_true(self):
        """Test parsing boolean true."""
        assert ScoringAlgorithms.parse_boolean_value("true") is True
        assert ScoringAlgorithms.parse_boolean_value("yes") is True
        assert ScoringAlgorithms.parse_boolean_value("1") is True
    
    def test_parse_boolean_false(self):
        """Test parsing boolean false."""
        assert ScoringAlgorithms.parse_boolean_value("false") is False
        assert ScoringAlgorithms.parse_boolean_value("no") is False
        assert ScoringAlgorithms.parse_boolean_value("0") is False
    
    def test_parse_boolean_json(self):
        """Test parsing JSON boolean."""
        result = ScoringAlgorithms.parse_boolean_value('{"value": true}')
        assert result is True

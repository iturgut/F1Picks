"""
Simplified database models for the worker.
These mirror the backend models but are self-contained.
"""
from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import Column, DateTime, Enum as SQLEnum, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class EventType(str, Enum):
    """Event session types."""
    PRACTICE_1 = "practice_1"
    PRACTICE_2 = "practice_2"
    PRACTICE_3 = "practice_3"
    SPRINT_QUALIFYING = "sprint_qualifying"
    SPRINT = "sprint"
    QUALIFYING = "qualifying"
    RACE = "race"


class EventStatus(str, Enum):
    """Event status."""
    SCHEDULED = "scheduled"
    LIVE = "live"
    COMPLETED = "completed"


class ResultSource(str, Enum):
    """Result data sources."""
    FASTF1 = "fastf1"
    MANUAL = "manual"


class PropType(str, Enum):
    """Prediction/Result property types - must match backend exactly."""
    RACE_WINNER = "race_winner"
    PODIUM_P1 = "podium_p1"
    PODIUM_P2 = "podium_p2"
    PODIUM_P3 = "podium_p3"
    FASTEST_LAP = "fastest_lap"
    POLE_POSITION = "pole_position"
    FIRST_RETIREMENT = "first_retirement"
    SAFETY_CAR = "safety_car"
    LAP_TIME_PREDICTION = "lap_time_prediction"
    SECTOR_TIME_PREDICTION = "sector_time_prediction"
    PIT_WINDOW_START = "pit_window_start"
    PIT_WINDOW_END = "pit_window_end"
    TOTAL_PIT_STOPS = "total_pit_stops"
    QUALIFYING_POSITION = "qualifying_position"
    RACE_POSITION = "race_position"
    SPRINT_WINNER = "sprint_winner"
    SPRINT_POSITION = "sprint_position"


class Event(Base):
    """F1 Event/Session model."""
    __tablename__ = "events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    circuit_id = Column(String(100), nullable=False)
    circuit_name = Column(String(255), nullable=False)
    session_type = Column(SQLEnum(EventType), nullable=False)
    round_number = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(SQLEnum(EventStatus), nullable=False, default=EventStatus.SCHEDULED)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Result(Base):
    """Race/Session result model."""
    __tablename__ = "results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    event_id = Column(UUID(as_uuid=True), nullable=False)
    prop_type = Column(SQLEnum(PropType), nullable=False)
    actual_value = Column(Text, nullable=False)
    source = Column(SQLEnum(ResultSource), nullable=False, default=ResultSource.FASTF1)
    source_reference = Column(String(200))  # Reference ID from source system
    result_metadata = Column("metadata", JSON)  # Use column name 'metadata' but attribute 'result_metadata'
    ingested_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

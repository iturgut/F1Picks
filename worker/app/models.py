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
    CANCELLED = "cancelled"


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
    prop_type = Column(String(50), nullable=False)
    actual_value = Column(Text, nullable=False)
    source = Column(String(50), nullable=False, default="fastf1")
    prop_metadata = Column("metadata", JSON)  # Use column name 'metadata' but attribute 'prop_metadata'
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

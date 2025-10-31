import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class EventType(enum.Enum):
    """Enum for different F1 session types."""
    PRACTICE_1 = "practice_1"
    PRACTICE_2 = "practice_2"
    PRACTICE_3 = "practice_3"
    SPRINT_QUALIFYING = "sprint_qualifying"
    SPRINT = "sprint"
    QUALIFYING = "qualifying"
    RACE = "race"

class EventStatus(enum.Enum):
    """Enum for event status."""
    SCHEDULED = "scheduled"
    LIVE = "live"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Event(Base):
    """Event model for F1 sessions (practice, qualifying, race, etc.)."""
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)  # e.g., "Monaco Grand Prix - Race"
    circuit_id = Column(String(50), nullable=False, index=True)  # e.g., "monaco", "silverstone"
    circuit_name = Column(String(100), nullable=False)  # e.g., "Circuit de Monaco"

    # Session details
    session_type = Column(Enum(EventType), nullable=False, index=True)
    round_number = Column(Integer, nullable=False, index=True)  # F1 season round
    year = Column(Integer, nullable=False, index=True)

    # Timing
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False)

    # Status
    status = Column(Enum(EventStatus), default=EventStatus.SCHEDULED, nullable=False, index=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    picks = relationship("Pick", back_populates="event", cascade="all, delete-orphan")
    results = relationship("Result", back_populates="event", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, name='{self.name}', type={self.session_type.value}, status={self.status.value})>"

import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class PropType(enum.Enum):
    """Enum for different prediction types."""
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

class Pick(Base):
    """User predictions for F1 events."""
    __tablename__ = "picks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)

    # Prediction details
    prop_type = Column(Enum(PropType), nullable=False, index=True)
    prop_value = Column(Text, nullable=False)  # Flexible storage for different prediction types
    prop_metadata = Column("metadata", JSONB, nullable=True)  # Additional data (e.g., confidence, reasoning)

    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="picks")
    event = relationship("Event", back_populates="picks")
    scores = relationship("Score", back_populates="pick", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Pick(id={self.id}, user_id={self.user_id}, prop_type={self.prop_type.value}, value='{self.prop_value}')>"

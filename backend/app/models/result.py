import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base
from .pick import PropType


class ResultSource(enum.Enum):
    """Enum for data sources."""
    FASTF1 = "fastf1"
    MANUAL = "manual"
    FIA_TIMING = "fia_timing"

class Result(Base):
    """Actual results from F1 events, ingested from FastF1 or other sources."""
    __tablename__ = "results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)

    # Result details
    prop_type = Column(Enum(PropType), nullable=False, index=True)
    actual_value = Column(Text, nullable=False)  # The actual outcome
    result_metadata = Column("metadata", JSONB, nullable=True)  # Additional data from FastF1

    # Data source tracking
    source = Column(Enum(ResultSource), default=ResultSource.FASTF1, nullable=False)
    source_reference = Column(String(200), nullable=True)  # Reference ID from source system

    # Timing
    ingested_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    event = relationship("Event", back_populates="results")

    def __repr__(self) -> str:
        return f"<Result(id={self.id}, event_id={self.event_id}, prop_type={self.prop_type.value}, value='{self.actual_value}')>"

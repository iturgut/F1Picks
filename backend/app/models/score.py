import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class Score(Base):
    """Scoring results for user predictions."""
    __tablename__ = "scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pick_id = Column(UUID(as_uuid=True), ForeignKey("picks.id", ondelete="CASCADE"), nullable=False, unique=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Scoring details
    points = Column(Integer, nullable=False, default=0)
    margin = Column(Float, nullable=True)  # Margin of error (e.g., seconds off for time predictions)
    exact_match = Column(Boolean, nullable=False, default=False)

    # Scoring metadata
    scoring_metadata = Column("metadata", JSONB, nullable=True)  # Additional scoring details

    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    pick = relationship("Pick", back_populates="scores")
    user = relationship("User", back_populates="scores")

    def __repr__(self) -> str:
        return f"<Score(id={self.id}, pick_id={self.pick_id}, points={self.points}, exact_match={self.exact_match})>"

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class League(Base):
    """League model for organizing users into competition groups."""
    __tablename__ = "leagues"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_global = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    members = relationship("LeagueMember", back_populates="league", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<League(id={self.id}, name='{self.name}', is_global={self.is_global})>"


class LeagueMember(Base):
    """Association table for users and leagues with join metadata."""
    __tablename__ = "league_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    league_id = Column(UUID(as_uuid=True), ForeignKey("leagues.id", ondelete="CASCADE"), nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="league_memberships")
    league = relationship("League", back_populates="members")

    def __repr__(self) -> str:
        return f"<LeagueMember(user_id={self.user_id}, league_id={self.league_id})>"

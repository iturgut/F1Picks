import enum
import uuid

from sqlalchemy import Column, DateTime, Enum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from .base import Base


class EntityType(enum.Enum):
    """Enum for different entity types that can be audited."""
    USER = "user"
    LEAGUE = "league"
    EVENT = "event"
    PICK = "pick"
    RESULT = "result"
    SCORE = "score"

class AuditAction(enum.Enum):
    """Enum for different audit actions."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    SCORE_CALCULATED = "score_calculated"
    SCORE_OVERRIDDEN = "score_overridden"
    DATA_INGESTED = "data_ingested"

class Audit(Base):
    """Audit log for tracking changes and operations."""
    __tablename__ = "audit"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Entity being audited
    entity_type = Column(Enum(EntityType), nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Action details
    action = Column(Enum(AuditAction), nullable=False, index=True)

    # Metadata about the change
    audit_metadata = Column("metadata", JSONB, nullable=True)  # Before/after values, user info, etc.

    # Who/when
    performed_by = Column(UUID(as_uuid=True), nullable=True)  # User ID who performed action
    performed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<Audit(id={self.id}, entity_type={self.entity_type.value}, action={self.action.value}, performed_at={self.performed_at})>"

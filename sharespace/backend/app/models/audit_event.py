import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, Optional
from sqlalchemy import DateTime, ForeignKey, Index, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User


class AuditEvent(Base, UUIDPrimaryKeyMixin):
    """
    Immutable institutional audit log recording security, booking, compliance,
    and administrative events across tenant domains.
    """
    __tablename__ = "audit_events"

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    actor_ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    actor_user_agent: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    payload_before: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    payload_after: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index("ix_audit_events_org_time", "organization_id", "timestamp"),
        Index("ix_audit_events_entity", "entity_type", "entity_id"),
    )

    organization: Mapped[Optional["Organization"]] = relationship("Organization", back_populates="audit_events")
    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_events")

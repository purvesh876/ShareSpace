import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import PermitStatus

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User


class SafetyPermit(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Institutional safety permit (e.g. Laser Safety Level 3, Biohazard Level 2).
    Pre-requisite for reserving certain high-hazard equipment.
    """
    __tablename__ = "safety_permits"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    permit_type: Mapped[str] = mapped_column(String(100), nullable=False)
    issuer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    issue_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expiry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        default=PermitStatus.ACTIVE.value,
        nullable=False,
        index=True,
    )
    document_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    __table_args__ = (
        Index("ix_safety_permits_org_user", "organization_id", "user_id"),
        Index("ix_safety_permits_user_status", "user_id", "status"),
    )

    organization: Mapped["Organization"] = relationship("Organization", back_populates="safety_permits")
    user: Mapped["User"] = relationship("User", back_populates="safety_permits")

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import QualificationStatus

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.resource import Resource
    from app.models.user import User


class Qualification(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    User certification or practical training clearance for specialized equipment.
    Can be tied to a specific Resource or an institutional qualification code.
    """
    __tablename__ = "qualifications"

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
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("resources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    qualification_code: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    certified_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    certified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        default=QualificationStatus.ACTIVE.value,
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index("ix_qualifications_org_user", "organization_id", "user_id"),
    )

    organization: Mapped["Organization"] = relationship("Organization", back_populates="qualifications")
    user: Mapped["User"] = relationship("User", back_populates="qualifications")
    resource: Mapped[Optional["Resource"]] = relationship("Resource", back_populates="qualifications")

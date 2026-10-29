import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import BookingStatus

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.resource import Resource
    from app.models.user import User


class Booking(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Time-slot reservation for an institutional Resource.
    """
    __tablename__ = "bookings"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resource_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("resources.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        default=BookingStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    purpose: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    total_credits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    checkin_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    checkout_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_bookings_res_time", "resource_id", "start_time", "end_time"),
        Index("ix_bookings_user_status", "user_id", "status"),
        Index("ix_bookings_org_status", "organization_id", "status"),
    )

    organization: Mapped["Organization"] = relationship("Organization", back_populates="bookings")
    resource: Mapped["Resource"] = relationship("Resource", back_populates="bookings")
    user: Mapped["User"] = relationship("User", back_populates="bookings")

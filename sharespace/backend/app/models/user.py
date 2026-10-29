from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.membership import OrganizationMembership
    from app.models.booking import Booking
    from app.models.safety_permit import SafetyPermit
    from app.models.qualification import Qualification
    from app.models.audit_event import AuditEvent


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    User account with institutional email, verified status, and auth link.
    """
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    auth_provider_id: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, index=True, nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # User-scoped relationships
    memberships: Mapped[List["OrganizationMembership"]] = relationship(
        "OrganizationMembership",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    bookings: Mapped[List["Booking"]] = relationship(
        "Booking",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    safety_permits: Mapped[List["SafetyPermit"]] = relationship(
        "SafetyPermit",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    qualifications: Mapped[List["Qualification"]] = relationship(
        "Qualification",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    audit_events: Mapped[List["AuditEvent"]] = relationship(
        "AuditEvent",
        back_populates="user",
    )

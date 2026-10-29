from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import Boolean, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.membership import OrganizationMembership
    from app.models.resource import Resource
    from app.models.booking import Booking
    from app.models.safety_permit import SafetyPermit
    from app.models.qualification import Qualification
    from app.models.audit_event import AuditEvent


class Organization(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Institution or campus community tenant (e.g. 'Apex Institute of Technology').
    Root tenant entity for strict institutional isolation.
    """
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    domain: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    settings_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Tenant-scoped relationships
    memberships: Mapped[List["OrganizationMembership"]] = relationship(
        "OrganizationMembership",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    resources: Mapped[List["Resource"]] = relationship(
        "Resource",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    bookings: Mapped[List["Booking"]] = relationship(
        "Booking",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    safety_permits: Mapped[List["SafetyPermit"]] = relationship(
        "SafetyPermit",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    qualifications: Mapped[List["Qualification"]] = relationship(
        "Qualification",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    audit_events: Mapped[List["AuditEvent"]] = relationship(
        "AuditEvent",
        back_populates="organization",
    )

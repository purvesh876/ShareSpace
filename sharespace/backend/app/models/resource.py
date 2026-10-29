import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import Boolean, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ResourceCategory

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.booking import Booking
    from app.models.qualification import Qualification


class Resource(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Institutional resource (laboratory equipment, workshop tools, testing spaces, computing nodes).
    Scoped strictly to an Organization for multi-tenant isolation.
    """
    __tablename__ = "resources"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(
        String(50),
        default=ResourceCategory.LAB_INSTRUMENT.value,
        nullable=False,
        index=True,
    )
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    requires_permit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_qualification: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hourly_rate_credits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    specifications_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_resource_org_slug"),
        Index("ix_resources_org_category", "organization_id", "category"),
    )

    organization: Mapped["Organization"] = relationship("Organization", back_populates="resources")
    bookings: Mapped[List["Booking"]] = relationship(
        "Booking",
        back_populates="resource",
        cascade="all, delete-orphan",
    )
    qualifications: Mapped[List["Qualification"]] = relationship(
        "Qualification",
        back_populates="resource",
    )

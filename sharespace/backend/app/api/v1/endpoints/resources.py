from datetime import datetime, timedelta, timezone
import re
from typing import List, Optional
import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    OrganizationContext,
    require_org_manager_or_admin,
    require_org_member,
)
from app.db.session import get_db
from app.models.audit_event import AuditEvent
from app.models.booking import Booking
from app.models.enums import BookingStatus, ResourceCategory
from app.models.resource import Resource
from app.schemas.resource import (
    ResourceAvailabilityResponse,
    ResourceCreate,
    ResourceResponse,
    ResourceUpdate,
    TimeSlot,
)

router = APIRouter()


def slugify(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return cleaned or "res"


@router.get("", response_model=List[ResourceResponse])
async def list_resources(
    category: Optional[str] = Query(None, description="Filter by resource category"),
    available_only: bool = Query(False, description="Filter for operational assets only"),
    search: Optional[str] = Query(None, description="Text search on name, location, or description"),
    context: OrganizationContext = Depends(require_org_member),
    db: AsyncSession = Depends(get_db),
):
    """
    List institutional resources strictly scoped to the requesting user's active organization.
    Multi-tenant isolation guaranteed: users cannot view resources from other organizations.
    """
    stmt = select(Resource).where(Resource.organization_id == context.organization_id)

    if category:
        stmt = stmt.where(Resource.category == category.lower().strip())

    if available_only:
        stmt = stmt.where(Resource.is_available.is_(True))

    if search and search.strip():
        term = f"%{search.strip().lower()}%"
        stmt = stmt.where(
            Resource.name.ilike(term)
            | Resource.location.ilike(term)
            | Resource.description.ilike(term)
        )

    stmt = stmt.order_by(Resource.name.asc())
    result = await db.execute(stmt)
    resources = result.scalars().all()
    return [ResourceResponse.model_validate(r) for r in resources]


@router.post("", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED)
async def create_resource(
    request: ResourceCreate,
    context: OrganizationContext = Depends(require_org_manager_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new laboratory equipment or institutional facility asset.
    Strictly restricted to Lab Managers and Administrators of this organization.
    """
    # Validate category against ResourceCategory enum
    valid_categories = {c.value for c in ResourceCategory}
    cat = request.category.lower().strip()
    if cat not in valid_categories:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid resource category '{request.category}'. Allowed categories: {sorted(list(valid_categories))}",
        )

    now = datetime.now(timezone.utc)
    base_slug = slugify(request.name)
    slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"

    resource = Resource(
        id=uuid.uuid4(),
        organization_id=context.organization_id,
        name=request.name.strip(),
        slug=slug,
        description=request.description.strip() if request.description else None,
        category=cat,
        location=request.location.strip() if request.location else None,
        is_available=True,
        requires_approval=request.requires_approval,
        requires_permit=request.requires_permit,
        requires_qualification=request.requires_qualification,
        hourly_rate_credits=request.hourly_rate_credits,
        specifications_json=request.specifications_json or {},
        created_at=now,
        updated_at=now,
    )
    db.add(resource)

    # Log immutable audit event
    audit = AuditEvent(
        id=uuid.uuid4(),
        organization_id=context.organization_id,
        user_id=context.user.id,
        action="RESOURCE_CREATED",
        entity_type="resource",
        entity_id=str(resource.id),
        payload_after={
            "name": resource.name,
            "category": resource.category,
            "location": resource.location,
            "requires_approval": resource.requires_approval,
        },
        timestamp=now,
    )
    db.add(audit)

    await db.commit()
    await db.refresh(resource)
    return ResourceResponse.model_validate(resource)


@router.get("/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    resource_id: UUID,
    context: OrganizationContext = Depends(require_org_member),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve full details for an institutional resource.
    Guarantees tenant isolation: verifies asset belongs to the caller's organization.
    """
    stmt = select(Resource).where(
        Resource.id == resource_id,
        Resource.organization_id == context.organization_id,
    )
    result = await db.execute(stmt)
    resource = result.scalars().first()

    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found in this organization.",
        )

    return ResourceResponse.model_validate(resource)


@router.patch("/{resource_id}", response_model=ResourceResponse)
async def update_resource(
    resource_id: UUID,
    request: ResourceUpdate,
    context: OrganizationContext = Depends(require_org_manager_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Update resource attributes, operational status, or reservation rules.
    Restricted to Lab Managers and Administrators.
    """
    stmt = select(Resource).where(
        Resource.id == resource_id,
        Resource.organization_id == context.organization_id,
    )
    result = await db.execute(stmt)
    resource = result.scalars().first()

    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found in this organization.",
        )

    payload_before = {
        "name": resource.name,
        "is_available": resource.is_available,
        "requires_approval": resource.requires_approval,
        "hourly_rate_credits": resource.hourly_rate_credits,
    }

    if request.name is not None:
        resource.name = request.name.strip()
    if request.category is not None:
        valid_categories = {c.value for c in ResourceCategory}
        cat = request.category.lower().strip()
        if cat not in valid_categories:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid category '{request.category}'.",
            )
        resource.category = cat
    if request.description is not None:
        resource.description = request.description.strip()
    if request.location is not None:
        resource.location = request.location.strip()
    if request.is_available is not None:
        resource.is_available = request.is_available
    if request.requires_approval is not None:
        resource.requires_approval = request.requires_approval
    if request.requires_permit is not None:
        resource.requires_permit = request.requires_permit
    if request.requires_qualification is not None:
        resource.requires_qualification = request.requires_qualification
    if request.hourly_rate_credits is not None:
        resource.hourly_rate_credits = request.hourly_rate_credits
    if request.specifications_json is not None:
        resource.specifications_json = request.specifications_json

    now = datetime.now(timezone.utc)
    resource.updated_at = now

    audit = AuditEvent(
        id=uuid.uuid4(),
        organization_id=context.organization_id,
        user_id=context.user.id,
        action="RESOURCE_UPDATED",
        entity_type="resource",
        entity_id=str(resource.id),
        payload_before=payload_before,
        payload_after={
            "name": resource.name,
            "is_available": resource.is_available,
            "requires_approval": resource.requires_approval,
            "hourly_rate_credits": resource.hourly_rate_credits,
        },
        timestamp=now,
    )
    db.add(audit)

    await db.commit()
    await db.refresh(resource)
    return ResourceResponse.model_validate(resource)


@router.get("/{resource_id}/availability", response_model=ResourceAvailabilityResponse)
async def get_resource_availability(
    resource_id: UUID,
    start_time: Optional[datetime] = Query(None, description="Start of window (ISO 8601 UTC)"),
    end_time: Optional[datetime] = Query(None, description="End of window (ISO 8601 UTC)"),
    context: OrganizationContext = Depends(require_org_member),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve reservation availability for a resource within a given time range.
    Returns reserved/pending intervals so users can choose non-conflicting slots.
    """
    stmt = select(Resource).where(
        Resource.id == resource_id,
        Resource.organization_id == context.organization_id,
    )
    result = await db.execute(stmt)
    resource = result.scalars().first()

    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found in this organization.",
        )

    now = datetime.now(timezone.utc)
    window_start = start_time or now
    window_end = end_time or (window_start + timedelta(days=7))

    if window_end <= window_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_time must be strictly after start_time.",
        )

    # Active reservations that conflict with the window
    booking_stmt = (
        select(Booking)
        .where(
            Booking.resource_id == resource_id,
            Booking.status.in_([
                BookingStatus.APPROVED.value,
                BookingStatus.PENDING.value,
                BookingStatus.IN_USE.value,
            ]),
            Booking.end_time > window_start,
            Booking.start_time < window_end,
        )
        .order_by(Booking.start_time.asc())
    )
    booking_res = await db.execute(booking_stmt)
    bookings = booking_res.scalars().all()

    reserved_slots = [
        TimeSlot(
            start_time=b.start_time,
            end_time=b.end_time,
            status=b.status,
        )
        for b in bookings
    ]

    return ResourceAvailabilityResponse(
        resource_id=resource.id,
        resource_name=resource.name,
        is_available=resource.is_available,
        requires_approval=resource.requires_approval,
        reserved_slots=reserved_slots,
    )

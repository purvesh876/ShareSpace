from datetime import datetime, timedelta, timezone
from typing import List, Optional
import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.deps import (
    OrganizationContext,
    require_org_manager_or_admin,
    require_org_member,
)
from app.db.session import get_db
from app.models.audit_event import AuditEvent
from app.models.booking import Booking
from app.models.enums import BookingStatus, MembershipRole, PermitStatus, QualificationStatus
from app.models.qualification import Qualification
from app.models.resource import Resource
from app.models.safety_permit import SafetyPermit
from app.models.user import User
from app.schemas.booking import (
    BookingCancelRequest,
    BookingCheckinRequest,
    BookingCreate,
    BookingDecisionRequest,
    BookingResponse,
    BookingReturnRequest,
)

router = APIRouter()


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    request: BookingCreate,
    context: OrganizationContext = Depends(require_org_member),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new time-slot reservation for an institutional resource.
    - Strictly scoped to the caller's active organization.
    - Transactional exclusive row locking prevents double-booking concurrency races.
    - Enforces future start time and status rules.
    """
    now = datetime.now(timezone.utc)

    # 1. Reject past start times (with 5 min grace for clock skew)
    if request.start_time < now - timedelta(minutes=5):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reservation start time cannot be in the past.",
        )

    # 2. Transactional locking: acquire exclusive row lock on Resource to serialize concurrent bookings
    resource_stmt = (
        select(Resource)
        .where(
            Resource.id == request.resource_id,
            Resource.organization_id == context.organization_id,
        )
        .with_for_update()
    )
    resource_res = await db.execute(resource_stmt)
    resource = resource_res.scalars().first()

    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found in this organization.",
        )

    if not resource.is_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Resource '{resource.name}' is currently offline or under maintenance.",
        )

    # 3. Enforce equipment eligibility: safety permits & qualifications
    if resource.requires_permit:
        permit_stmt = (
            select(SafetyPermit)
            .where(
                SafetyPermit.organization_id == context.organization_id,
                SafetyPermit.user_id == context.user.id,
                SafetyPermit.status == PermitStatus.ACTIVE.value,
                SafetyPermit.expiry_date >= request.start_time,
            )
        )
        permit_res = await db.execute(permit_stmt)
        if not permit_res.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Safety permit required: You must hold an active institutional safety permit "
                    f"valid through your reservation start time to book '{resource.name}'."
                ),
            )

    if resource.requires_qualification:
        qual_stmt = (
            select(Qualification)
            .where(
                Qualification.organization_id == context.organization_id,
                Qualification.user_id == context.user.id,
                or_(
                    Qualification.resource_id == resource.id,
                    Qualification.resource_id.is_(None),
                ),
                Qualification.status == QualificationStatus.ACTIVE.value,
                or_(
                    Qualification.expires_at.is_(None),
                    Qualification.expires_at >= request.start_time,
                ),
            )
        )
        qual_res = await db.execute(qual_stmt)
        if not qual_res.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Equipment qualification required: You must hold an active certified training qualification "
                    f"for '{resource.name}' to book this equipment."
                ),
            )

    # 4. Concurrency check: verify no overlapping active/approved/pending reservation exists
    overlap_stmt = (
        select(Booking)
        .where(
            Booking.resource_id == resource.id,
            Booking.status.in_([
                BookingStatus.APPROVED.value,
                BookingStatus.PENDING.value,
                BookingStatus.IN_USE.value,
            ]),
            Booking.start_time < request.end_time,
            Booking.end_time > request.start_time,
        )
    )
    overlap_res = await db.execute(overlap_stmt)
    conflicting = overlap_res.scalars().first()

    if conflicting:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Requested time slot conflicts with an existing reservation "
                f"({conflicting.start_time.isoformat()} to {conflicting.end_time.isoformat()})."
            ),
        )

    # 4. Determine initial status and credit cost
    duration_hours = (request.end_time - request.start_time).total_seconds() / 3600.0
    total_credits = max(0, int(duration_hours * resource.hourly_rate_credits))

    # Managers and Admins bypass approval for their own bookings
    is_elevated = context.role in [MembershipRole.ADMIN.value, MembershipRole.LAB_MANAGER.value]
    if not resource.requires_approval or is_elevated:
        initial_status = BookingStatus.APPROVED.value
    else:
        initial_status = BookingStatus.PENDING.value

    booking = Booking(
        id=uuid.uuid4(),
        organization_id=context.organization_id,
        resource_id=resource.id,
        user_id=context.user.id,
        start_time=request.start_time,
        end_time=request.end_time,
        status=initial_status,
        purpose=request.purpose.strip() if request.purpose else None,
        total_credits=total_credits,
        created_at=now,
        updated_at=now,
    )
    db.add(booking)

    audit = AuditEvent(
        id=uuid.uuid4(),
        organization_id=context.organization_id,
        user_id=context.user.id,
        action="BOOKING_CREATED",
        entity_type="booking",
        entity_id=str(booking.id),
        payload_after={
            "resource_id": str(resource.id),
            "resource_name": resource.name,
            "status": initial_status,
            "start_time": booking.start_time.isoformat(),
            "end_time": booking.end_time.isoformat(),
            "total_credits": total_credits,
        },
        timestamp=now,
    )
    db.add(audit)

    await db.commit()
    await db.refresh(booking)

    return BookingResponse(
        id=booking.id,
        organization_id=booking.organization_id,
        resource_id=booking.resource_id,
        resource_name=resource.name,
        user_id=context.user.id,
        user_email=context.user.email,
        user_full_name=context.user.full_name,
        start_time=booking.start_time,
        end_time=booking.end_time,
        status=booking.status,
        purpose=booking.purpose,
        total_credits=booking.total_credits,
        rejection_reason=booking.rejection_reason,
        checkin_time=booking.checkin_time,
        checkout_time=booking.checkout_time,
        created_at=booking.created_at,
        updated_at=booking.updated_at,
    )


@router.get("/my", response_model=List[BookingResponse])
async def list_my_bookings(
    context: OrganizationContext = Depends(require_org_member),
    db: AsyncSession = Depends(get_db),
):
    """
    List reservations belonging to the authenticated user within their active organization.
    """
    stmt = (
        select(Booking, Resource)
        .join(Resource, Booking.resource_id == Resource.id)
        .where(
            Booking.organization_id == context.organization_id,
            Booking.user_id == context.user.id,
        )
        .order_by(Booking.start_time.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    return [
        BookingResponse(
            id=b.id,
            organization_id=b.organization_id,
            resource_id=b.resource_id,
            resource_name=r.name,
            user_id=context.user.id,
            user_email=context.user.email,
            user_full_name=context.user.full_name,
            start_time=b.start_time,
            end_time=b.end_time,
            status=b.status,
            purpose=b.purpose,
            total_credits=b.total_credits,
            rejection_reason=b.rejection_reason,
            checkin_time=b.checkin_time,
            checkout_time=b.checkout_time,
            created_at=b.created_at,
            updated_at=b.updated_at,
        )
        for b, r in rows
    ]


@router.get("", response_model=List[BookingResponse])
async def list_organization_bookings(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by booking status"),
    resource_id: Optional[UUID] = Query(None, description="Filter by specific resource ID"),
    context: OrganizationContext = Depends(require_org_manager_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    List all reservations in the organization for facility management and approval review.
    Restricted to Lab Managers and Administrators.
    """
    stmt = (
        select(Booking, Resource, User)
        .join(Resource, Booking.resource_id == Resource.id)
        .join(User, Booking.user_id == User.id)
        .where(Booking.organization_id == context.organization_id)
    )

    if status_filter:
        stmt = stmt.where(Booking.status == status_filter.lower().strip())

    if resource_id:
        stmt = stmt.where(Booking.resource_id == resource_id)

    stmt = stmt.order_by(Booking.start_time.desc())
    result = await db.execute(stmt)
    rows = result.all()

    return [
        BookingResponse(
            id=b.id,
            organization_id=b.organization_id,
            resource_id=b.resource_id,
            resource_name=r.name,
            user_id=u.id,
            user_email=u.email,
            user_full_name=u.full_name,
            start_time=b.start_time,
            end_time=b.end_time,
            status=b.status,
            purpose=b.purpose,
            total_credits=b.total_credits,
            rejection_reason=b.rejection_reason,
            checkin_time=b.checkin_time,
            checkout_time=b.checkout_time,
            created_at=b.created_at,
            updated_at=b.updated_at,
        )
        for b, r, u in rows
    ]


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: UUID,
    request: Optional[BookingCancelRequest] = None,
    context: OrganizationContext = Depends(require_org_member),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel an existing reservation.
    Allowed for:
    - The booking owner (user who reserved the slot)
    - Organization Lab Managers and Administrators
    """
    stmt = (
        select(Booking, Resource)
        .join(Resource, Booking.resource_id == Resource.id)
        .where(
            Booking.id == booking_id,
            Booking.organization_id == context.organization_id,
        )
    )
    result = await db.execute(stmt)
    row = result.first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found in this organization.",
        )

    booking, resource = row

    is_owner = booking.user_id == context.user.id
    is_manager = context.role in [MembershipRole.ADMIN.value, MembershipRole.LAB_MANAGER.value]

    if not is_owner and not is_manager:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only cancel your own bookings.",
        )

    if booking.status in [BookingStatus.CANCELLED.value, BookingStatus.COMPLETED.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel a booking that is already {booking.status}.",
        )

    now = datetime.now(timezone.utc)
    booking.status = BookingStatus.CANCELLED.value
    booking.updated_at = now
    if request and request.reason:
        booking.rejection_reason = f"Cancelled: {request.reason.strip()}"

    audit = AuditEvent(
        id=uuid.uuid4(),
        organization_id=context.organization_id,
        user_id=context.user.id,
        action="BOOKING_CANCELLED",
        entity_type="booking",
        entity_id=str(booking.id),
        payload_after={
            "status": BookingStatus.CANCELLED.value,
            "cancelled_by": str(context.user.id),
            "reason": request.reason if request else None,
        },
        timestamp=now,
    )
    db.add(audit)

    await db.commit()
    await db.refresh(booking)

    return BookingResponse(
        id=booking.id,
        organization_id=booking.organization_id,
        resource_id=booking.resource_id,
        resource_name=resource.name,
        user_id=booking.user_id,
        user_email=context.user.email if is_owner else None,
        user_full_name=context.user.full_name if is_owner else None,
        start_time=booking.start_time,
        end_time=booking.end_time,
        status=booking.status,
        purpose=booking.purpose,
        total_credits=booking.total_credits,
        rejection_reason=booking.rejection_reason,
        checkin_time=booking.checkin_time,
        checkout_time=booking.checkout_time,
        created_at=booking.created_at,
        updated_at=booking.updated_at,
    )


@router.post("/{booking_id}/decision", response_model=BookingResponse)
async def review_booking_decision(
    booking_id: UUID,
    request: BookingDecisionRequest,
    context: OrganizationContext = Depends(require_org_manager_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Approve or reject a pending booking request.
    Restricted to Lab Managers and Administrators.
    Verifies no overlapping reservation has been approved in the interim.
    """
    stmt = (
        select(Booking, Resource)
        .join(Resource, Booking.resource_id == Resource.id)
        .where(
            Booking.id == booking_id,
            Booking.organization_id == context.organization_id,
        )
    )
    result = await db.execute(stmt)
    row = result.first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found in this organization.",
        )

    booking, resource = row

    if booking.status != BookingStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only pending bookings can be approved or rejected. Current status: {booking.status}",
        )

    now = datetime.now(timezone.utc)

    if request.action == "approve":
        # Check eligibility requirements for the reserving user before manager approval
        if resource.requires_permit:
            permit_stmt = (
                select(SafetyPermit)
                .where(
                    SafetyPermit.organization_id == context.organization_id,
                    SafetyPermit.user_id == booking.user_id,
                    SafetyPermit.status == PermitStatus.ACTIVE.value,
                    SafetyPermit.expiry_date >= booking.start_time,
                )
            )
            permit_res = await db.execute(permit_stmt)
            if not permit_res.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot approve: Reserving user no longer holds a valid active safety permit for this resource.",
                )

        if resource.requires_qualification:
            qual_stmt = (
                select(Qualification)
                .where(
                    Qualification.organization_id == context.organization_id,
                    Qualification.user_id == booking.user_id,
                    or_(
                        Qualification.resource_id == resource.id,
                        Qualification.resource_id.is_(None),
                    ),
                    Qualification.status == QualificationStatus.ACTIVE.value,
                    or_(
                        Qualification.expires_at.is_(None),
                        Qualification.expires_at >= booking.start_time,
                    ),
                )
            )
            qual_res = await db.execute(qual_stmt)
            if not qual_res.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot approve: Reserving user no longer holds an active certified qualification for this resource.",
                )

        # Check concurrency conflict before approving
        overlap_stmt = (
            select(Booking)
            .where(
                Booking.resource_id == booking.resource_id,
                Booking.id != booking.id,
                Booking.status.in_([BookingStatus.APPROVED.value, BookingStatus.IN_USE.value]),
                Booking.start_time < booking.end_time,
                Booking.end_time > booking.start_time,
            )
        )
        overlap_res = await db.execute(overlap_stmt)
        if overlap_res.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot approve: another confirmed reservation occupies this time slot.",
            )
        booking.status = BookingStatus.APPROVED.value
        booking.rejection_reason = None
        action_name = "BOOKING_APPROVED"
    else:  # reject
        booking.status = BookingStatus.REJECTED.value
        booking.rejection_reason = request.reason.strip() if request.reason else "Rejected by facility manager."
        action_name = "BOOKING_REJECTED"

    booking.updated_at = now

    audit = AuditEvent(
        id=uuid.uuid4(),
        organization_id=context.organization_id,
        user_id=context.user.id,
        action=action_name,
        entity_type="booking",
        entity_id=str(booking.id),
        payload_after={
            "status": booking.status,
            "decision_by": str(context.user.id),
            "reason": booking.rejection_reason,
        },
        timestamp=now,
    )
    db.add(audit)

    await db.commit()
    await db.refresh(booking)

    return BookingResponse(
        id=booking.id,
        organization_id=booking.organization_id,
        resource_id=booking.resource_id,
        resource_name=resource.name,
        user_id=booking.user_id,
        start_time=booking.start_time,
        end_time=booking.end_time,
        status=booking.status,
        purpose=booking.purpose,
        total_credits=booking.total_credits,
        rejection_reason=booking.rejection_reason,
        checkin_time=booking.checkin_time,
        checkout_time=booking.checkout_time,
        created_at=booking.created_at,
        updated_at=booking.updated_at,
    )


@router.post("/{booking_id}/checkin", response_model=BookingResponse)
async def checkin_booking(
    booking_id: UUID,
    request: BookingCheckinRequest,
    context: OrganizationContext = Depends(require_org_member),
    db: AsyncSession = Depends(get_db),
):
    """
    Check-in handover for an approved equipment reservation.
    - Validates reservation is approved and caller is authorized (reserver or facility manager).
    - Enforces mandatory condition checklist.
    - Transitions booking status to 'in_use' and records checkin timestamp.
    - Atomically writes BOOKING_CHECKIN audit event.
    """
    now = datetime.now(timezone.utc)

    # 1. Fetch booking with lock
    stmt = (
        select(Booking, Resource)
        .join(Resource, Booking.resource_id == Resource.id)
        .where(
            Booking.id == booking_id,
            Booking.organization_id == context.organization_id,
        )
        .with_for_update()
    )
    result = await db.execute(stmt)
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found in this organization.",
        )

    booking, resource = row

    # 2. Authorization check: reserver or manager/admin
    is_elevated = context.role in [MembershipRole.ADMIN.value, MembershipRole.LAB_MANAGER.value]
    if booking.user_id != context.user.id and not is_elevated:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to check in for this reservation.",
        )

    # 3. State check
    if booking.status == BookingStatus.IN_USE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reservation is already active and checked in.",
        )
    if booking.status == BookingStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reservation has already been completed.",
        )
    if booking.status == BookingStatus.CANCELLED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot check in: this reservation was cancelled.",
        )
    if booking.status != BookingStatus.APPROVED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot check in: reservation is in '{booking.status}' status (must be 'approved').",
        )

    # 4. Mandatory checklist check
    if not request.checklist_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mandatory pre-use condition checklist must be completed before equipment activation.",
        )

    # 5. Window check
    if now > booking.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reservation window has already passed. Please schedule a new time slot.",
        )

    # 6. Apply state transition
    booking.status = BookingStatus.IN_USE.value
    booking.checkin_time = now
    booking.updated_at = now

    audit = AuditEvent(
        id=uuid.uuid4(),
        organization_id=context.organization_id,
        user_id=context.user.id,
        action="BOOKING_CHECKIN",
        entity_type="booking",
        entity_id=str(booking.id),
        payload_after={
            "checkin_time": now.isoformat(),
            "condition_notes": request.condition_notes,
            "photo_evidence_url": request.photo_evidence_url,
            "checked_in_by": str(context.user.id),
        },
        timestamp=now,
    )
    db.add(audit)

    await db.commit()
    await db.refresh(booking)

    return BookingResponse(
        id=booking.id,
        organization_id=booking.organization_id,
        resource_id=booking.resource_id,
        resource_name=resource.name,
        user_id=booking.user_id,
        start_time=booking.start_time,
        end_time=booking.end_time,
        status=booking.status,
        purpose=booking.purpose,
        total_credits=booking.total_credits,
        rejection_reason=booking.rejection_reason,
        checkin_time=booking.checkin_time,
        checkout_time=booking.checkout_time,
        created_at=booking.created_at,
        updated_at=booking.updated_at,
    )


@router.post("/{booking_id}/return", response_model=BookingResponse)
async def return_booking(
    booking_id: UUID,
    request: BookingReturnRequest,
    context: OrganizationContext = Depends(require_org_member),
    db: AsyncSession = Depends(get_db),
):
    """
    Return and complete equipment usage.
    - Validates reservation is currently active ('in_use').
    - Requires post-use condition checklist verification.
    - Transitions booking status to 'completed' and records checkout timestamp.
    - Atomically writes BOOKING_RETURN audit event.
    """
    now = datetime.now(timezone.utc)

    # 1. Fetch booking with lock
    stmt = (
        select(Booking, Resource)
        .join(Resource, Booking.resource_id == Resource.id)
        .where(
            Booking.id == booking_id,
            Booking.organization_id == context.organization_id,
        )
        .with_for_update()
    )
    result = await db.execute(stmt)
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found in this organization.",
        )

    booking, resource = row

    # 2. Authorization check
    is_elevated = context.role in [MembershipRole.ADMIN.value, MembershipRole.LAB_MANAGER.value]
    if booking.user_id != context.user.id and not is_elevated:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to return equipment for this reservation.",
        )

    # 3. State check: must be currently IN_USE
    if booking.status == BookingStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Equipment has already been returned and checked out.",
        )
    if booking.status != BookingStatus.IN_USE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot return equipment: reservation must be in active 'in_use' status (currently '{booking.status}').",
        )

    # 4. Mandatory checklist check
    if not request.checklist_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mandatory post-use return checklist must be confirmed.",
        )

    # 5. Apply state transition
    booking.status = BookingStatus.COMPLETED.value
    booking.checkout_time = now
    booking.updated_at = now

    audit = AuditEvent(
        id=uuid.uuid4(),
        organization_id=context.organization_id,
        user_id=context.user.id,
        action="BOOKING_RETURN",
        entity_type="booking",
        entity_id=str(booking.id),
        payload_after={
            "checkout_time": now.isoformat(),
            "condition_notes": request.condition_notes,
            "incident_reported": request.incident_reported,
            "photo_evidence_url": request.photo_evidence_url,
            "returned_by": str(context.user.id),
        },
        timestamp=now,
    )
    db.add(audit)

    await db.commit()
    await db.refresh(booking)

    return BookingResponse(
        id=booking.id,
        organization_id=booking.organization_id,
        resource_id=booking.resource_id,
        resource_name=resource.name,
        user_id=booking.user_id,
        start_time=booking.start_time,
        end_time=booking.end_time,
        status=booking.status,
        purpose=booking.purpose,
        total_credits=booking.total_credits,
        rejection_reason=booking.rejection_reason,
        checkin_time=booking.checkin_time,
        checkout_time=booking.checkout_time,
        created_at=booking.created_at,
        updated_at=booking.updated_at,
    )

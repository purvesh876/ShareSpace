import uuid
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import OrganizationContext, require_org_member
from app.db.session import get_db
from app.models.audit_event import AuditEvent
from app.models.booking import Booking
from app.models.enums import MembershipRole
from app.schemas.evidence import (
    EvidenceUploadResponse,
    SignedUrlResponse,
    StorageStatusResponse,
)
from app.services.storage_service import StorageService

router = APIRouter()


@router.get("/evidence/status", response_model=StorageStatusResponse)
async def get_storage_status(
    context: OrganizationContext = Depends(require_org_member),
) -> StorageStatusResponse:
    """
    Check if private evidence storage is configured and ready for photographic handover.
    """
    status_info = StorageService.get_status()
    return StorageStatusResponse(**status_info)


@router.post(
    "/bookings/{booking_id}/evidence/upload",
    response_model=EvidenceUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_booking_evidence(
    organization_id: UUID,
    booking_id: UUID,
    file: UploadFile = File(...),
    handover_type: str = Form("checkin"),
    context: OrganizationContext = Depends(require_org_member),
    db: AsyncSession = Depends(get_db),
) -> EvidenceUploadResponse:
    """
    Securely upload a condition photograph for an authorized booking handover.
    Only the booking owner, lab managers, or organization admins can upload evidence.
    """
    # 1. Verify booking exists and belongs to this organization
    stmt = select(Booking).where(
        Booking.id == booking_id,
        Booking.organization_id == organization_id,
    )
    result = await db.execute(stmt)
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking reservation not found in this organization.",
        )

    # 2. Check authorization: owner or manager/admin
    is_owner = booking.user_id == context.user.id
    is_manager_or_admin = context.role in (
        MembershipRole.ADMIN.value,
        MembershipRole.LAB_MANAGER.value,
    )

    if not (is_owner or is_manager_or_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Only the reservation owner or lab managers may attach evidence.",
        )

    # 3. Read uploaded file payload
    file_bytes = await file.read()
    content_type = file.content_type or "image/jpeg"
    filename = file.filename or "evidence.jpg"

    # 4. Upload to private storage service
    upload_result = await StorageService.upload_evidence(
        organization_id=organization_id,
        booking_id=booking_id,
        handover_type=handover_type,
        file_bytes=file_bytes,
        original_filename=filename,
        content_type=content_type,
    )

    # 5. Append immutable audit record
    audit_event = AuditEvent(
        id=uuid.uuid4(),
        organization_id=organization_id,
        user_id=context.user.id,
        action="EVIDENCE_UPLOADED",
        entity_type="booking",
        entity_id=str(booking_id),
        payload_before=None,
        payload_after={
            "storage_path": upload_result["storage_path"],
            "filename": filename,
            "content_type": content_type,
            "size_bytes": upload_result["size_bytes"],
            "handover_type": upload_result["handover_type"],
            "uploaded_by_email": context.user.email,
        },
        timestamp=datetime.now(timezone.utc),
    )
    db.add(audit_event)
    await db.commit()

    return EvidenceUploadResponse(**upload_result)


@router.get(
    "/bookings/{booking_id}/evidence/signed-url",
    response_model=SignedUrlResponse,
)
async def get_evidence_signed_url(
    organization_id: UUID,
    booking_id: UUID,
    storage_path: str = Query(..., description="Object key in private storage"),
    expires_in: int = Query(3600, ge=60, le=86400, description="Expiry in seconds"),
    context: OrganizationContext = Depends(require_org_member),
    db: AsyncSession = Depends(get_db),
) -> SignedUrlResponse:
    """
    Retrieve a fresh, short-lived signed download URL for an existing private evidence photo.
    Restricted to authorized organization members with access to the reservation.
    """
    # 1. Verify booking exists in this organization
    stmt = select(Booking).where(
        Booking.id == booking_id,
        Booking.organization_id == organization_id,
    )
    result = await db.execute(stmt)
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking reservation not found in this organization.",
        )

    # 2. Check authorization: owner, manager, admin, or auditor
    is_owner = booking.user_id == context.user.id
    is_privileged = context.role in (
        MembershipRole.ADMIN.value,
        MembershipRole.LAB_MANAGER.value,
        MembershipRole.AUDITOR.value,
    )

    if not (is_owner or is_privileged):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not have permission to view evidence for this booking.",
        )

    # 3. Generate short-lived signed URL
    signed_url = await StorageService.generate_signed_url(
        organization_id=organization_id,
        booking_id=booking_id,
        storage_path=storage_path,
        expires_in=expires_in,
    )

    return SignedUrlResponse(
        storage_path=storage_path,
        signed_url=signed_url,
        expires_in=expires_in,
    )

from datetime import datetime, timezone
from typing import List, Optional
import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.deps import (
    OrganizationContext,
    require_org_auditor_or_admin,
    require_org_manager_or_admin,
    require_org_member,
)
from app.db.session import get_db
from app.models.audit_event import AuditEvent
from app.models.enums import MembershipRole, PermitStatus, QualificationStatus
from app.models.membership import OrganizationMembership
from app.models.qualification import Qualification
from app.models.resource import Resource
from app.models.safety_permit import SafetyPermit
from app.models.user import User
from app.schemas.compliance import (
    AuditEventResponse,
    QualificationCreate,
    QualificationResponse,
    SafetyPermitCreate,
    SafetyPermitResponse,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Qualifications
# ---------------------------------------------------------------------------

@router.get("/qualifications/my", response_model=List[QualificationResponse])
async def list_my_qualifications(
    context: OrganizationContext = Depends(require_org_member),
    db: AsyncSession = Depends(get_db),
):
    """
    List active qualifications and certifications held by the authenticated user
    in the active organization.
    """
    stmt = (
        select(Qualification, Resource)
        .outerjoin(Resource, Qualification.resource_id == Resource.id)
        .where(
            Qualification.organization_id == context.organization_id,
            Qualification.user_id == context.user.id,
        )
        .order_by(desc(Qualification.certified_at))
    )
    result = await db.execute(stmt)
    records = []
    for qual, res in result.all():
        records.append(
            QualificationResponse(
                id=qual.id,
                organization_id=qual.organization_id,
                user_id=qual.user_id,
                user_email=context.user.email,
                user_full_name=context.user.full_name,
                resource_id=qual.resource_id,
                resource_name=res.name if res else None,
                qualification_code=qual.qualification_code,
                title=qual.title,
                certified_by=qual.certified_by,
                certified_at=qual.certified_at,
                expires_at=qual.expires_at,
                status=qual.status,
                created_at=qual.created_at,
                updated_at=qual.updated_at,
            )
        )
    return records


@router.get("/qualifications", response_model=List[QualificationResponse])
async def list_org_qualifications(
    context: OrganizationContext = Depends(require_org_manager_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Manager/Admin endpoint: List all user equipment qualifications recorded within the organization.
    """
    stmt = (
        select(Qualification, Resource, User)
        .outerjoin(Resource, Qualification.resource_id == Resource.id)
        .join(User, Qualification.user_id == User.id)
        .where(Qualification.organization_id == context.organization_id)
        .order_by(desc(Qualification.certified_at))
    )
    result = await db.execute(stmt)
    records = []
    for qual, res, u in result.all():
        records.append(
            QualificationResponse(
                id=qual.id,
                organization_id=qual.organization_id,
                user_id=qual.user_id,
                user_email=u.email,
                user_full_name=u.full_name,
                resource_id=qual.resource_id,
                resource_name=res.name if res else None,
                qualification_code=qual.qualification_code,
                title=qual.title,
                certified_by=qual.certified_by,
                certified_at=qual.certified_at,
                expires_at=qual.expires_at,
                status=qual.status,
                created_at=qual.created_at,
                updated_at=qual.updated_at,
            )
        )
    return records


@router.post("/qualifications", response_model=QualificationResponse, status_code=status.HTTP_201_CREATED)
async def grant_qualification(
    request: QualificationCreate,
    context: OrganizationContext = Depends(require_org_manager_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Manager/Admin endpoint: Grant or record a certified training qualification for a member.
    """
    now = datetime.now(timezone.utc)

    # 1. Verify target user exists and is a member of the organization
    mem_stmt = (
        select(OrganizationMembership, User)
        .join(User, OrganizationMembership.user_id == User.id)
        .where(
            OrganizationMembership.organization_id == context.organization_id,
            OrganizationMembership.user_id == request.user_id,
            OrganizationMembership.is_active.is_(True),
        )
    )
    mem_res = await db.execute(mem_stmt)
    mem_row = mem_res.first()
    if not mem_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user is not an active member of this organization.",
        )
    _, target_user = mem_row

    # 2. Verify resource if resource_id provided
    res_name = None
    if request.resource_id:
        res_stmt = select(Resource).where(
            Resource.id == request.resource_id,
            Resource.organization_id == context.organization_id,
        )
        res_res = await db.execute(res_stmt)
        res = res_res.scalars().first()
        if not res:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found in this organization.",
            )
        res_name = res.name

    qual = Qualification(
        id=uuid.uuid4(),
        organization_id=context.organization_id,
        user_id=request.user_id,
        resource_id=request.resource_id,
        qualification_code=request.qualification_code.strip(),
        title=request.title.strip(),
        certified_by=request.certified_by or context.user.full_name,
        certified_at=request.certified_at,
        expires_at=request.expires_at,
        status=QualificationStatus.ACTIVE.value,
        created_at=now,
        updated_at=now,
    )
    db.add(qual)

    audit = AuditEvent(
        id=uuid.uuid4(),
        organization_id=context.organization_id,
        user_id=context.user.id,
        action="QUALIFICATION_GRANTED",
        entity_type="qualification",
        entity_id=str(qual.id),
        payload_after={
            "user_id": str(request.user_id),
            "qualification_code": qual.qualification_code,
            "title": qual.title,
            "granted_by": str(context.user.id),
        },
        timestamp=now,
    )
    db.add(audit)

    await db.commit()
    await db.refresh(qual)

    return QualificationResponse(
        id=qual.id,
        organization_id=qual.organization_id,
        user_id=qual.user_id,
        user_email=target_user.email,
        user_full_name=target_user.full_name,
        resource_id=qual.resource_id,
        resource_name=res_name,
        qualification_code=qual.qualification_code,
        title=qual.title,
        certified_by=qual.certified_by,
        certified_at=qual.certified_at,
        expires_at=qual.expires_at,
        status=qual.status,
        created_at=qual.created_at,
        updated_at=qual.updated_at,
    )


# ---------------------------------------------------------------------------
# Safety Permits
# ---------------------------------------------------------------------------

@router.get("/safety-permits/my", response_model=List[SafetyPermitResponse])
async def list_my_safety_permits(
    context: OrganizationContext = Depends(require_org_member),
    db: AsyncSession = Depends(get_db),
):
    """
    List safety permits issued to the authenticated user in the active organization.
    """
    stmt = (
        select(SafetyPermit)
        .where(
            SafetyPermit.organization_id == context.organization_id,
            SafetyPermit.user_id == context.user.id,
        )
        .order_by(desc(SafetyPermit.issue_date))
    )
    result = await db.execute(stmt)
    records = []
    for permit in result.scalars().all():
        records.append(
            SafetyPermitResponse(
                id=permit.id,
                organization_id=permit.organization_id,
                user_id=permit.user_id,
                user_email=context.user.email,
                user_full_name=context.user.full_name,
                permit_type=permit.permit_type,
                issuer=permit.issuer,
                issue_date=permit.issue_date,
                expiry_date=permit.expiry_date,
                status=permit.status,
                document_url=permit.document_url,
                created_at=permit.created_at,
                updated_at=permit.updated_at,
            )
        )
    return records


@router.get("/safety-permits", response_model=List[SafetyPermitResponse])
async def list_org_safety_permits(
    context: OrganizationContext = Depends(require_org_manager_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Manager/Admin endpoint: List all institutional safety permits recorded in the organization.
    """
    stmt = (
        select(SafetyPermit, User)
        .join(User, SafetyPermit.user_id == User.id)
        .where(SafetyPermit.organization_id == context.organization_id)
        .order_by(desc(SafetyPermit.issue_date))
    )
    result = await db.execute(stmt)
    records = []
    for permit, u in result.all():
        records.append(
            SafetyPermitResponse(
                id=permit.id,
                organization_id=permit.organization_id,
                user_id=permit.user_id,
                user_email=u.email,
                user_full_name=u.full_name,
                permit_type=permit.permit_type,
                issuer=permit.issuer,
                issue_date=permit.issue_date,
                expiry_date=permit.expiry_date,
                status=permit.status,
                document_url=permit.document_url,
                created_at=permit.created_at,
                updated_at=permit.updated_at,
            )
        )
    return records


@router.post("/safety-permits", response_model=SafetyPermitResponse, status_code=status.HTTP_201_CREATED)
async def issue_safety_permit(
    request: SafetyPermitCreate,
    context: OrganizationContext = Depends(require_org_manager_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Manager/Admin endpoint: Issue or log an active institutional safety permit.
    """
    now = datetime.now(timezone.utc)

    # 1. Target member validation
    mem_stmt = (
        select(OrganizationMembership, User)
        .join(User, OrganizationMembership.user_id == User.id)
        .where(
            OrganizationMembership.organization_id == context.organization_id,
            OrganizationMembership.user_id == request.user_id,
            OrganizationMembership.is_active.is_(True),
        )
    )
    mem_res = await db.execute(mem_stmt)
    mem_row = mem_res.first()
    if not mem_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user is not an active member of this organization.",
        )
    _, target_user = mem_row

    if request.expiry_date <= request.issue_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="expiry_date must be strictly after issue_date.",
        )

    permit = SafetyPermit(
        id=uuid.uuid4(),
        organization_id=context.organization_id,
        user_id=request.user_id,
        permit_type=request.permit_type.strip(),
        issuer=request.issuer or context.user.full_name,
        issue_date=request.issue_date,
        expiry_date=request.expiry_date,
        status=PermitStatus.ACTIVE.value,
        document_url=request.document_url,
        created_at=now,
        updated_at=now,
    )
    db.add(permit)

    audit = AuditEvent(
        id=uuid.uuid4(),
        organization_id=context.organization_id,
        user_id=context.user.id,
        action="PERMIT_ISSUED",
        entity_type="safety_permit",
        entity_id=str(permit.id),
        payload_after={
            "user_id": str(request.user_id),
            "permit_type": permit.permit_type,
            "issued_by": str(context.user.id),
        },
        timestamp=now,
    )
    db.add(audit)

    await db.commit()
    await db.refresh(permit)

    return SafetyPermitResponse(
        id=permit.id,
        organization_id=permit.organization_id,
        user_id=permit.user_id,
        user_email=target_user.email,
        user_full_name=target_user.full_name,
        permit_type=permit.permit_type,
        issuer=permit.issuer,
        issue_date=permit.issue_date,
        expiry_date=permit.expiry_date,
        status=permit.status,
        document_url=permit.document_url,
        created_at=permit.created_at,
        updated_at=permit.updated_at,
    )


# ---------------------------------------------------------------------------
# Audit Events (Governance & Compliance Review)
# ---------------------------------------------------------------------------

@router.get("/audit-events", response_model=List[AuditEventResponse])
async def list_audit_events(
    limit: int = Query(50, ge=1, le=200),
    context: OrganizationContext = Depends(require_org_auditor_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Manager/Admin/Auditor endpoint: Immutable append-only audit trail for compliance review.
    """
    stmt = (
        select(AuditEvent, User)
        .outerjoin(User, AuditEvent.user_id == User.id)
        .where(AuditEvent.organization_id == context.organization_id)
        .order_by(desc(AuditEvent.timestamp))
        .limit(limit)
    )
    result = await db.execute(stmt)
    records = []
    for event, u in result.all():
        records.append(
            AuditEventResponse(
                id=event.id,
                organization_id=event.organization_id,
                user_id=event.user_id,
                user_email=u.email if u else None,
                action=event.action,
                entity_type=event.entity_type,
                entity_id=event.entity_id,
                payload_before=event.payload_before,
                payload_after=event.payload_after,
                timestamp=event.timestamp,
            )
        )
    return records

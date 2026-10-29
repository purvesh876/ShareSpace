from datetime import datetime, timezone
from typing import List
import uuid
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    OrganizationContext,
    get_current_user,
    require_org_admin,
    require_org_auditor_or_admin,
    require_org_manager_or_admin,
    require_org_member,
)
from app.db.session import get_db
from app.models.audit_event import AuditEvent
from app.models.enums import MembershipRole
from app.models.membership import OrganizationMembership
from app.models.organization import Organization
from app.models.user import User
from app.schemas.organization import (
    AssignMemberRequest,
    AuditEventResponse,
    OrganizationContextResponse,
    OrganizationMemberResponse,
    OrganizationResponse,
)

router = APIRouter()


@router.get("", response_model=List[OrganizationResponse])
async def list_my_organizations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all organizations in which the verified user holds an active membership.
    Strict tenant boundary: users only see institutions where they are members.
    """
    stmt = (
        select(Organization)
        .join(OrganizationMembership, OrganizationMembership.organization_id == Organization.id)
        .where(
            OrganizationMembership.user_id == current_user.id,
            OrganizationMembership.is_active.is_(True),
            Organization.is_active.is_(True),
        )
    )
    result = await db.execute(stmt)
    orgs = result.scalars().all()
    return [OrganizationResponse.model_validate(org) for org in orgs]


@router.get("/{organization_id}", response_model=OrganizationContextResponse)
async def get_organization(
    context: OrganizationContext = Depends(require_org_member),
):
    """
    Retrieve details of an organization.
    Requires verified server-side active membership in this specific organization.
    Client-supplied organization_id is never trusted on its own.
    """
    return OrganizationContextResponse(
        organization=OrganizationResponse.model_validate(context.organization),
        user_role=context.role,
        membership_id=context.membership.id,
    )


@router.get("/{organization_id}/members", response_model=List[OrganizationMemberResponse])
async def list_organization_members(
    context: OrganizationContext = Depends(require_org_manager_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    List members of an organization.
    Restricted to lab managers and administrators within this organization.
    """
    stmt = (
        select(OrganizationMembership, User)
        .join(User, OrganizationMembership.user_id == User.id)
        .where(
            OrganizationMembership.organization_id == context.organization_id,
            OrganizationMembership.is_active.is_(True),
        )
        .order_by(OrganizationMembership.role, User.full_name)
    )
    result = await db.execute(stmt)
    rows = result.all()

    return [
        OrganizationMemberResponse(
            membership_id=m.id,
            user_id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=m.role,
            department=m.department,
            is_active=m.is_active,
            joined_at=m.created_at,
        )
        for m, u in rows
    ]


@router.get("/{organization_id}/audit-events", response_model=List[AuditEventResponse])
async def list_organization_audit_events(
    context: OrganizationContext = Depends(require_org_auditor_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    List compliance audit events for this organization.
    Restricted to institutional auditors and administrators within this organization.
    """
    stmt = (
        select(AuditEvent)
        .where(AuditEvent.organization_id == context.organization_id)
        .order_by(AuditEvent.timestamp.desc())
        .limit(100)
    )
    result = await db.execute(stmt)
    events = result.scalars().all()
    return [AuditEventResponse.model_validate(e) for e in events]


@router.post(
    "/{organization_id}/members",
    response_model=OrganizationMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def assign_organization_member(
    request: AssignMemberRequest,
    context: OrganizationContext = Depends(require_org_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Assign or invite a user to an organization with a specific role.
    Strictly administrator-only.
    Validates user existence, enforces unique membership constraint,
    and creates audit log event.
    """
    clean_email = request.email.strip().lower()

    # Validate role value against MembershipRole enum
    valid_roles = {r.value for r in MembershipRole}
    target_role = request.role.lower().strip()
    if target_role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid membership role '{request.role}'. Allowed roles: {sorted(list(valid_roles))}",
        )

    # Find target user by email
    stmt = select(User).where(User.email == clean_email)
    res = await db.execute(stmt)
    target_user = res.scalars().first()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{clean_email}' not found. Target user must register or sign in first.",
        )

    if not target_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot assign membership to a deactivated user account.",
        )

    # Check for existing membership (active or inactive)
    mem_stmt = select(OrganizationMembership).where(
        OrganizationMembership.organization_id == context.organization_id,
        OrganizationMembership.user_id == target_user.id,
    )
    mem_res = await db.execute(mem_stmt)
    existing_membership = mem_res.scalars().first()

    now = datetime.now(timezone.utc)

    if existing_membership:
        if existing_membership.is_active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User is already an active member of this organization with role '{existing_membership.role}'.",
            )
        # Reactivate and update role/department
        payload_before = {
            "role": existing_membership.role,
            "department": existing_membership.department,
            "is_active": existing_membership.is_active,
        }
        existing_membership.role = target_role
        existing_membership.department = request.department
        existing_membership.is_active = True
        existing_membership.updated_at = now
        membership = existing_membership
        payload_after = {
            "role": membership.role,
            "department": membership.department,
            "is_active": True,
            "target_user_id": str(target_user.id),
        }
        action_name = "MEMBERSHIP_REACTIVATED"
    else:
        membership = OrganizationMembership(
            id=uuid.uuid4(),
            organization_id=context.organization_id,
            user_id=target_user.id,
            role=target_role,
            department=request.department,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        db.add(membership)
        payload_before = None
        payload_after = {
            "role": membership.role,
            "department": membership.department,
            "is_active": True,
            "target_user_id": str(target_user.id),
        }
        action_name = "MEMBERSHIP_ASSIGNED"

    # Record immutable audit event
    audit = AuditEvent(
        id=uuid.uuid4(),
        organization_id=context.organization_id,
        user_id=context.user.id,
        action=action_name,
        entity_type="organization_membership",
        entity_id=str(membership.id),
        payload_before=payload_before,
        payload_after=payload_after,
        timestamp=now,
    )
    db.add(audit)

    await db.commit()
    await db.refresh(membership)

    return OrganizationMemberResponse(
        membership_id=membership.id,
        user_id=target_user.id,
        email=target_user.email,
        full_name=target_user.full_name,
        role=membership.role,
        department=membership.department,
        is_active=membership.is_active,
        joined_at=membership.created_at,
    )


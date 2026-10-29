from datetime import datetime, timezone
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, is_real_db_session
from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.models.enums import MembershipRole
from app.models.membership import OrganizationMembership
from app.models.organization import Organization
from app.models.user import User
from app.schemas.auth import (
    DemoTokenRequest,
    DemoTokenResponse,
    MembershipSummary,
    UserProfileResponse,
    UserResponse,
)

router = APIRouter()


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve the verified user's profile and list of active institutional memberships.
    """
    stmt = (
        select(OrganizationMembership, Organization)
        .join(Organization, OrganizationMembership.organization_id == Organization.id)
        .where(
            OrganizationMembership.user_id == current_user.id,
            OrganizationMembership.is_active.is_(True),
            Organization.is_active.is_(True),
        )
    )
    result = await db.execute(stmt)
    rows = result.all()

    memberships = [
        MembershipSummary(
            membership_id=m.id,
            organization_id=org.id,
            organization_name=org.name,
            organization_slug=org.slug,
            role=m.role,
            department=m.department,
            is_active=m.is_active,
        )
        for m, org in rows
    ]

    return UserProfileResponse(
        user=UserResponse.model_validate(current_user),
        memberships=memberships,
    )


# Demo persona mapping for testing & local development
DEMO_PERSONAS = {
    "student": {
        "email": "student@apex.edu",
        "full_name": "Maya Lin",
        "role": MembershipRole.STUDENT.value,
        "department": "Robotics Engineering",
    },
    "manager": {
        "email": "manager@apex.edu",
        "full_name": "Dr. Aris Vance",
        "role": MembershipRole.LAB_MANAGER.value,
        "department": "Advanced Optics Laboratory",
    },
    "admin": {
        "email": "admin@apex.edu",
        "full_name": "Dean Sarah Connor",
        "role": MembershipRole.ADMIN.value,
        "department": "School of Engineering",
    },
    "technician": {
        "email": "tech@apex.edu",
        "full_name": "Alex Mercer",
        "role": MembershipRole.TECHNICIAN.value,
        "department": "Central Fabrication Facility",
    },
    "researcher": {
        "email": "researcher@apex.edu",
        "full_name": "Dr. Jordan Hayes",
        "role": MembershipRole.RESEARCHER.value,
        "department": "Quantum Physics Group",
    },
    "auditor": {
        "email": "auditor@apex.edu",
        "full_name": "Elena Rostova",
        "role": MembershipRole.AUDITOR.value,
        "department": "Institutional Compliance Office",
    },
}


@router.post("/demo-token", response_model=DemoTokenResponse)
async def generate_demo_token(
    request: DemoTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a cryptographic JWT for a simulated demo persona.
    Strictly restricted to local development and test environments.
    """
    if settings.app_env == "production" or settings.app_env not in ("development", "test"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo token generation is disabled in production environments.",
        )

    persona = DEMO_PERSONAS.get(request.persona)
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown demo persona '{request.persona}'. Available: {list(DEMO_PERSONAS.keys())}",
        )

    if is_real_db_session(db):
        try:
            await db.execute(text("SET LOCAL app.bypass_rls = 'on';"))
        except Exception:
            pass

    # Check or provision user in DB
    stmt = select(User).where(User.email == persona["email"])
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        now = datetime.now(timezone.utc)
        user = User(
            id=uuid.uuid4(),
            email=persona["email"],
            full_name=persona["full_name"],
            auth_provider_id=f"demo-sub-{request.persona}",
            is_active=True,
            is_verified=True,
            created_at=now,
            updated_at=now,
        )
        db.add(user)
        await db.flush()

    # Ensure demo organization exists
    org_stmt = select(Organization).where(Organization.slug == "apex-institute")
    org_res = await db.execute(org_stmt)
    org = org_res.scalars().first()

    if not org:
        now = datetime.now(timezone.utc)
        org = Organization(
            id=uuid.uuid4(),
            name="Apex Institute of Technology",
            slug="apex-institute",
            domain="apex.edu",
            is_active=True,
            settings_json={"campus": "Main Campus", "allow_guest_browse": True},
            created_at=now,
            updated_at=now,
        )
        db.add(org)
        await db.flush()

    # Ensure membership exists with persona role
    mem_stmt = select(OrganizationMembership).where(
        OrganizationMembership.organization_id == org.id,
        OrganizationMembership.user_id == user.id,
    )
    mem_res = await db.execute(mem_stmt)
    membership = mem_res.scalars().first()

    if not membership:
        membership = OrganizationMembership(
            organization_id=org.id,
            user_id=user.id,
            role=persona["role"],
            department=persona["department"],
            is_active=True,
        )
        db.add(membership)
    else:
        membership.role = persona["role"]
        membership.department = persona["department"]
        membership.is_active = True

    await db.commit()
    await db.refresh(user)

    token = create_access_token(
        subject=user.auth_provider_id or str(user.id),
        email=user.email,
        expires_delta_seconds=86400,
        user_metadata={"full_name": user.full_name},
        extra_claims={"org_slug": org.slug, "role": persona["role"]},
    )

    return DemoTokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
        active_role=persona["role"],
    )

"""
Administrative membership management utility for ShareSpace.
Provides controlled, secure assignment of organization memberships
without granting arbitrary users elevated privileges or exposing credentials.
"""
import argparse
import asyncio
from datetime import datetime, timezone
import sys
import uuid
from typing import Optional

from sqlalchemy import select

from app.db.session import async_sessionmaker, get_async_engine, AsyncSession
from app.models.audit_event import AuditEvent
from app.models.enums import MembershipRole
from app.models.membership import OrganizationMembership
from app.models.organization import Organization
from app.models.user import User


async def assign_member(
    email: str,
    org_slug: str,
    role_name: str,
    department: Optional[str] = None,
) -> bool:
    clean_email = email.strip().lower()
    clean_slug = org_slug.strip().lower()
    clean_role = role_name.strip().lower()

    valid_roles = {r.value for r in MembershipRole}
    if clean_role not in valid_roles:
        print(f"Error: Invalid role '{role_name}'. Allowed roles: {sorted(list(valid_roles))}", file=sys.stderr)
        return False

    engine = get_async_engine()
    if not engine:
        print("Error: Database connection is not configured.", file=sys.stderr)
        return False

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        # 1. Resolve organization
        org_stmt = select(Organization).where(Organization.slug == clean_slug)
        org_res = await session.execute(org_stmt)
        org = org_res.scalars().first()
        if not org:
            print(f"Error: Organization with slug '{clean_slug}' not found.", file=sys.stderr)
            return False

        if not org.is_active:
            print(f"Error: Organization '{org.name}' is deactivated.", file=sys.stderr)
            return False

        # 2. Resolve user
        user_stmt = select(User).where(User.email == clean_email)
        user_res = await session.execute(user_stmt)
        user = user_res.scalars().first()
        if not user:
            print(f"Error: User with email '{clean_email}' not found. User must sign in first.", file=sys.stderr)
            return False

        if not user.is_active:
            print(f"Error: User account for '{clean_email}' is deactivated.", file=sys.stderr)
            return False

        # 3. Check membership
        mem_stmt = select(OrganizationMembership).where(
            OrganizationMembership.organization_id == org.id,
            OrganizationMembership.user_id == user.id,
        )
        mem_res = await session.execute(mem_stmt)
        existing = mem_res.scalars().first()

        now = datetime.now(timezone.utc)
        if existing:
            action_desc = "Reactivated and updated" if not existing.is_active else "Updated"
            existing.role = clean_role
            if department is not None:
                existing.department = department
            existing.is_active = True
            existing.updated_at = now
            membership = existing
            action_name = "CLI_MEMBERSHIP_UPDATED"
        else:
            action_desc = "Assigned"
            membership = OrganizationMembership(
                id=uuid.uuid4(),
                organization_id=org.id,
                user_id=user.id,
                role=clean_role,
                department=department,
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            session.add(membership)
            action_name = "CLI_MEMBERSHIP_ASSIGNED"

        # 4. Audit trail
        audit = AuditEvent(
            id=uuid.uuid4(),
            organization_id=org.id,
            user_id=user.id,
            action=action_name,
            entity_type="organization_membership",
            entity_id=str(membership.id),
            payload_after={
                "role": clean_role,
                "department": department,
                "is_active": True,
                "org_slug": clean_slug,
            },
            timestamp=now,
        )
        session.add(audit)

        await session.commit()

        email_prefix = clean_email.split("@")[0]
        masked = f"{email_prefix[:2]}***@{clean_email.split('@')[1]}"
        print(f"Success: {action_desc} membership for {masked} in '{org.name}' ({org.slug}) with role '{clean_role}'.")
        return True


async def list_members(org_slug: str) -> bool:
    clean_slug = org_slug.strip().lower()
    engine = get_async_engine()
    if not engine:
        print("Error: Database connection is not configured.", file=sys.stderr)
        return False

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        org_stmt = select(Organization).where(Organization.slug == clean_slug)
        org_res = await session.execute(org_stmt)
        org = org_res.scalars().first()
        if not org:
            print(f"Error: Organization '{clean_slug}' not found.", file=sys.stderr)
            return False

        stmt = (
            select(OrganizationMembership, User)
            .join(User, OrganizationMembership.user_id == User.id)
            .where(OrganizationMembership.organization_id == org.id)
            .order_by(OrganizationMembership.role, User.email)
        )
        res = await session.execute(stmt)
        rows = res.all()

        print(f"\n=== Members of '{org.name}' ({len(rows)}) ===")
        for mem, u in rows:
            email_parts = u.email.split("@")
            masked = f"{email_parts[0][:2]}***@{email_parts[1]}"
            status_str = "ACTIVE" if mem.is_active else "INACTIVE"
            print(f"[{status_str}] {masked:20} | Role: {mem.role:12} | Dept: {mem.department or 'N/A'}")
        return True


def main():
    parser = argparse.ArgumentParser(description="ShareSpace Administrative Membership Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    assign_parser = subparsers.add_parser("assign", help="Assign or update organization membership")
    assign_parser.add_argument("--email", required=True, help="User institutional email")
    assign_parser.add_argument("--org-slug", default="apex-institute", help="Organization slug (default: apex-institute)")
    assign_parser.add_argument("--role", default="researcher", help="Role (admin, lab_manager, technician, researcher, student, auditor)")
    assign_parser.add_argument("--department", default=None, help="Department name")

    list_parser = subparsers.add_parser("list", help="List organization members")
    list_parser.add_argument("--org-slug", default="apex-institute", help="Organization slug")

    args = parser.parse_args()

    if args.command == "assign":
        success = asyncio.run(assign_member(args.email, args.org_slug, args.role, args.department))
        sys.exit(0 if success else 1)
    elif args.command == "list":
        success = asyncio.run(list_members(args.org_slug))
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

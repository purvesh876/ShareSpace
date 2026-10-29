from datetime import datetime, timezone
import uuid
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.db.session import get_db
from app.main import app
from app.models.enums import MembershipRole
from app.models.membership import OrganizationMembership
from app.models.organization import Organization
from app.models.user import User


def test_list_my_organizations_requires_authentication(client: TestClient):
    """Accessing organizations list without token returns HTTP 401."""
    response = client.get("/api/v1/organizations")
    assert response.status_code == 401


def test_get_organization_access_denied_for_non_member(client: TestClient):
    """
    User cannot access organization details if they are not an active member.
    Server denies access with HTTP 403.
    """
    user_id = uuid.uuid4()
    foreign_org_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    mock_user = User(
        id=user_id,
        email="outsider@external.edu",
        full_name="External Visitor",
        auth_provider_id="sub-outsider",
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    token = create_access_token(subject="sub-outsider", email="outsider@external.edu")

    mock_db = AsyncMock()
    mock_user_res = MagicMock()
    mock_user_res.scalars.return_value.first.return_value = mock_user

    mock_mem_res = MagicMock()
    mock_mem_res.first.return_value = None

    mock_db.execute.side_effect = [mock_user_res, mock_mem_res]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get(
            f"/api/v1/organizations/{foreign_org_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
        assert "not an active member" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_client_cannot_bypass_authorization_by_modifying_organization_id(client: TestClient):
    """
    Submitting a different organization_id in headers or path cannot bypass server checks.
    The server validates membership strictly against the authenticated user.
    """
    user_id = uuid.uuid4()
    target_org_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    mock_user = User(
        id=user_id,
        email="student@apex.edu",
        full_name="Student",
        auth_provider_id="sub-student",
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    token = create_access_token(subject="sub-student", email="student@apex.edu")

    mock_db = AsyncMock()
    mock_user_res = MagicMock()
    mock_user_res.scalars.return_value.first.return_value = mock_user

    mock_mem_res = MagicMock()
    mock_mem_res.first.return_value = None

    mock_db.execute.side_effect = [mock_user_res, mock_mem_res]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get(
            "/api/v1/organizations/00000000-0000-0000-0000-000000000000",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Organization-Id": str(target_org_id),
            },
        )
        assert response.status_code == 403
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_member_list_role_restriction_denies_student(client: TestClient):
    """
    Student role is forbidden from viewing organization member rosters.
    Requires manager or admin role.
    """
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    mock_user = User(
        id=user_id,
        email="student@apex.edu",
        full_name="Student",
        auth_provider_id="sub-student",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_org = Organization(
        id=org_id,
        name="Apex Tech",
        slug="apex-tech",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_membership = OrganizationMembership(
        id=uuid.uuid4(),
        organization_id=org_id,
        user_id=user_id,
        role=MembershipRole.STUDENT.value,
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    token = create_access_token(subject="sub-student", email="student@apex.edu")

    mock_db = AsyncMock()
    mock_user_res = MagicMock()
    mock_user_res.scalars.return_value.first.return_value = mock_user

    mock_mem_res = MagicMock()
    mock_mem_res.first.return_value = (mock_membership, mock_org)

    mock_db.execute.side_effect = [mock_user_res, mock_mem_res]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get(
            f"/api/v1/organizations/{org_id}/members",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
        assert "insufficient role permissions" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_member_list_allowed_for_manager_or_admin(client: TestClient):
    """
    Lab manager role is authorized to view organization members.
    """
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    mock_user = User(
        id=user_id,
        email="manager@apex.edu",
        full_name="Dr. Vance",
        auth_provider_id="sub-manager",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_org = Organization(
        id=org_id,
        name="Apex Tech",
        slug="apex-tech",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_membership = OrganizationMembership(
        id=uuid.uuid4(),
        organization_id=org_id,
        user_id=user_id,
        role=MembershipRole.LAB_MANAGER.value,
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    token = create_access_token(subject="sub-manager", email="manager@apex.edu")

    mock_db = AsyncMock()
    mock_user_res = MagicMock()
    mock_user_res.scalars.return_value.first.return_value = mock_user

    mock_mem_res = MagicMock()
    mock_mem_res.first.return_value = (mock_membership, mock_org)

    mock_members_list = MagicMock()
    mock_members_list.all.return_value = [(mock_membership, mock_user)]

    mock_db.execute.side_effect = [mock_user_res, mock_mem_res, mock_members_list]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get(
            f"/api/v1/organizations/{org_id}/members",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["email"] == "manager@apex.edu"
        assert data[0]["role"] == "lab_manager"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_audit_events_endpoint_role_restriction(client: TestClient):
    """
    Audit events endpoint is restricted to auditors and administrators only.
    Lab manager is rejected with HTTP 403.
    """
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    mock_user = User(
        id=user_id,
        email="manager@apex.edu",
        full_name="Manager",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_org = Organization(
        id=org_id,
        name="Apex Tech",
        slug="apex-tech",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_membership = OrganizationMembership(
        id=uuid.uuid4(),
        organization_id=org_id,
        user_id=user_id,
        role=MembershipRole.LAB_MANAGER.value,
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    token = create_access_token(subject="sub-manager", email="manager@apex.edu")

    mock_db = AsyncMock()
    mock_user_res = MagicMock()
    mock_user_res.scalars.return_value.first.return_value = mock_user
    mock_mem_res = MagicMock()
    mock_mem_res.first.return_value = (mock_membership, mock_org)

    mock_db.execute.side_effect = [mock_user_res, mock_mem_res]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get(
            f"/api/v1/organizations/{org_id}/audit-events",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
        assert "insufficient role permissions" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_get_organization_inactive_membership_rejected(client: TestClient):
    """Users with deactivated membership are denied access with HTTP 403."""
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    mock_user = User(
        id=user_id,
        email="inactive.member@apex.edu",
        full_name="Former Member",
        auth_provider_id="sub-former",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    token = create_access_token(subject="sub-former", email="inactive.member@apex.edu")

    mock_db = AsyncMock()
    mock_user_res = MagicMock()
    mock_user_res.scalars.return_value.first.return_value = mock_user

    # Membership query returns None because is_active is False
    mock_mem_res = MagicMock()
    mock_mem_res.first.return_value = None

    mock_db.execute.side_effect = [mock_user_res, mock_mem_res]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get(
            f"/api/v1/organizations/{org_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
        assert "not an active member" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_get_organization_inactive_organization_rejected(client: TestClient):
    """Members of a deactivated organization are denied access with HTTP 403."""
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    mock_user = User(
        id=user_id,
        email="user@dormant.edu",
        full_name="Dormant User",
        auth_provider_id="sub-dormant",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    token = create_access_token(subject="sub-dormant", email="user@dormant.edu")

    mock_db = AsyncMock()
    mock_user_res = MagicMock()
    mock_user_res.scalars.return_value.first.return_value = mock_user

    # Query returns None because Organization.is_active is False
    mock_mem_res = MagicMock()
    mock_mem_res.first.return_value = None

    mock_db.execute.side_effect = [mock_user_res, mock_mem_res]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get(
            f"/api/v1/organizations/{org_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
        assert "not an active member" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_audit_events_endpoint_allowed_for_auditor_and_admin(client: TestClient):
    """Auditors and Administrators can access compliance audit events."""
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    mock_user = User(
        id=user_id,
        email="auditor@apex.edu",
        full_name="Elena Rostova",
        auth_provider_id="sub-auditor",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_org = Organization(
        id=org_id,
        name="Apex Tech",
        slug="apex-tech",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_membership = OrganizationMembership(
        id=uuid.uuid4(),
        organization_id=org_id,
        user_id=user_id,
        role=MembershipRole.AUDITOR.value,
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    token = create_access_token(subject="sub-auditor", email="auditor@apex.edu")

    mock_db = AsyncMock()
    mock_user_res = MagicMock()
    mock_user_res.scalars.return_value.first.return_value = mock_user
    mock_mem_res = MagicMock()
    mock_mem_res.first.return_value = (mock_membership, mock_org)

    # Empty list of audit events
    mock_events_res = MagicMock()
    mock_events_res.scalars.return_value.all.return_value = []

    mock_db.execute.side_effect = [mock_user_res, mock_mem_res, mock_events_res]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get(
            f"/api/v1/organizations/{org_id}/audit-events",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json() == []
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_member_list_allowed_for_admin(client: TestClient):
    """Administrators are authorized to view organization members."""
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    mock_admin = User(
        id=user_id,
        email="admin@apex.edu",
        full_name="Dean Connor",
        auth_provider_id="sub-admin",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_org = Organization(
        id=org_id,
        name="Apex Tech",
        slug="apex-tech",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_membership = OrganizationMembership(
        id=uuid.uuid4(),
        organization_id=org_id,
        user_id=user_id,
        role=MembershipRole.ADMIN.value,
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    token = create_access_token(subject="sub-admin", email="admin@apex.edu")

    mock_db = AsyncMock()
    mock_user_res = MagicMock()
    mock_user_res.scalars.return_value.first.return_value = mock_admin
    mock_mem_res = MagicMock()
    mock_mem_res.first.return_value = (mock_membership, mock_org)

    mock_members_list = MagicMock()
    mock_members_list.all.return_value = [(mock_membership, mock_admin)]

    mock_db.execute.side_effect = [mock_user_res, mock_mem_res, mock_members_list]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get(
            f"/api/v1/organizations/{org_id}/members",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["email"] == "admin@apex.edu"
        assert data[0]["role"] == "admin"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_get_organization_succeeds_for_active_member(client: TestClient):
    """Real authenticated user with active membership accesses their organization successfully."""
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    mock_user = User(
        id=user_id,
        email="researcher@apex.edu",
        full_name="Researcher",
        auth_provider_id="sub-researcher",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_org = Organization(
        id=org_id,
        name="Apex Tech",
        slug="apex-tech",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_membership = OrganizationMembership(
        id=uuid.uuid4(),
        organization_id=org_id,
        user_id=user_id,
        role=MembershipRole.RESEARCHER.value,
        department="Quantum Group",
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    token = create_access_token(subject="sub-researcher", email="researcher@apex.edu")

    mock_db = AsyncMock()
    mock_user_res = MagicMock()
    mock_user_res.scalars.return_value.first.return_value = mock_user
    mock_mem_res = MagicMock()
    mock_mem_res.first.return_value = (mock_membership, mock_org)

    mock_db.execute.side_effect = [mock_user_res, mock_mem_res]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get(
            f"/api/v1/organizations/{org_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["organization"]["slug"] == "apex-tech"
        assert data["user_role"] == "researcher"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_assign_member_by_admin_success(client: TestClient):
    """Authorized administrator assigns a user membership with designated role."""
    admin_id = uuid.uuid4()
    target_user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    mock_admin = User(
        id=admin_id,
        email="admin@apex.edu",
        full_name="Dean Connor",
        auth_provider_id="sub-admin",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_org = Organization(
        id=org_id,
        name="Apex Tech",
        slug="apex-tech",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_admin_membership = OrganizationMembership(
        id=uuid.uuid4(),
        organization_id=org_id,
        user_id=admin_id,
        role=MembershipRole.ADMIN.value,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_target_user = User(
        id=target_user_id,
        email="candidate@apex.edu",
        full_name="Candidate Member",
        auth_provider_id="sub-candidate",
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    token = create_access_token(subject="sub-admin", email="admin@apex.edu")

    mock_db = AsyncMock()
    # 1. get_current_user (admin)
    mock_admin_res = MagicMock()
    mock_admin_res.scalars.return_value.first.return_value = mock_admin

    # 2. require_org_admin (admin check)
    mock_mem_res = MagicMock()
    mock_mem_res.first.return_value = (mock_admin_membership, mock_org)

    # 3. assign endpoint: find target user
    mock_target_res = MagicMock()
    mock_target_res.scalars.return_value.first.return_value = mock_target_user

    # 4. assign endpoint: check existing membership (None)
    mock_existing_mem_res = MagicMock()
    mock_existing_mem_res.scalars.return_value.first.return_value = None

    mock_db.add = MagicMock()
    mock_db.execute.side_effect = [
        mock_admin_res,
        mock_mem_res,
        mock_target_res,
        mock_existing_mem_res,
    ]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            f"/api/v1/organizations/{org_id}/members",
            json={
                "email": "candidate@apex.edu",
                "role": "researcher",
                "department": "Nanotechnology",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "candidate@apex.edu"
        assert data["role"] == "researcher"
        assert data["department"] == "Nanotechnology"
        assert data["is_active"] is True
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_assign_member_reactivates_inactive_membership(client: TestClient):
    """Assigning an inactive member reactivates the membership with updated role."""
    admin_id = uuid.uuid4()
    target_user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    mock_admin = User(
        id=admin_id,
        email="admin@apex.edu",
        full_name="Dean Connor",
        auth_provider_id="sub-admin",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_org = Organization(
        id=org_id,
        name="Apex Tech",
        slug="apex-tech",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_admin_membership = OrganizationMembership(
        id=uuid.uuid4(),
        organization_id=org_id,
        user_id=admin_id,
        role=MembershipRole.ADMIN.value,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_target_user = User(
        id=target_user_id,
        email="former@apex.edu",
        full_name="Former Member",
        auth_provider_id="sub-former",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_inactive_mem = OrganizationMembership(
        id=uuid.uuid4(),
        organization_id=org_id,
        user_id=target_user_id,
        role=MembershipRole.STUDENT.value,
        is_active=False,
        created_at=now,
        updated_at=now,
    )

    token = create_access_token(subject="sub-admin", email="admin@apex.edu")

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_admin_res = MagicMock()
    mock_admin_res.scalars.return_value.first.return_value = mock_admin
    mock_mem_res = MagicMock()
    mock_mem_res.first.return_value = (mock_admin_membership, mock_org)

    mock_target_res = MagicMock()
    mock_target_res.scalars.return_value.first.return_value = mock_target_user

    mock_existing_mem_res = MagicMock()
    mock_existing_mem_res.scalars.return_value.first.return_value = mock_inactive_mem

    mock_db.execute.side_effect = [
        mock_admin_res,
        mock_mem_res,
        mock_target_res,
        mock_existing_mem_res,
    ]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            f"/api/v1/organizations/{org_id}/members",
            json={
                "email": "former@apex.edu",
                "role": "technician",
                "department": "Fabrication",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "former@apex.edu"
        assert data["role"] == "technician"
        assert data["department"] == "Fabrication"
        assert data["is_active"] is True
    finally:
        app.dependency_overrides.pop(get_db, None)



def test_assign_member_denied_for_regular_member(client: TestClient):
    """Regular member (student) is forbidden from assigning organization memberships."""
    student_id = uuid.uuid4()
    org_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    mock_student = User(
        id=student_id,
        email="student@apex.edu",
        full_name="Maya Lin",
        auth_provider_id="sub-student",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_org = Organization(
        id=org_id,
        name="Apex Tech",
        slug="apex-tech",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_student_mem = OrganizationMembership(
        id=uuid.uuid4(),
        organization_id=org_id,
        user_id=student_id,
        role=MembershipRole.STUDENT.value,
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    token = create_access_token(subject="sub-student", email="student@apex.edu")

    mock_db = AsyncMock()
    mock_user_res = MagicMock()
    mock_user_res.scalars.return_value.first.return_value = mock_student
    mock_mem_res = MagicMock()
    mock_mem_res.first.return_value = (mock_student_mem, mock_org)

    mock_db.execute.side_effect = [mock_user_res, mock_mem_res]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            f"/api/v1/organizations/{org_id}/members",
            json={"email": "someone@apex.edu", "role": "student"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
        assert "insufficient role permissions" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_assign_member_denied_for_non_member(client: TestClient):
    """User without active membership in the organization cannot assign members."""
    outsider_id = uuid.uuid4()
    foreign_org_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    mock_outsider = User(
        id=outsider_id,
        email="outsider@external.edu",
        full_name="External Visitor",
        auth_provider_id="sub-outsider",
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    token = create_access_token(subject="sub-outsider", email="outsider@external.edu")

    mock_db = AsyncMock()
    mock_user_res = MagicMock()
    mock_user_res.scalars.return_value.first.return_value = mock_outsider
    mock_mem_res = MagicMock()
    mock_mem_res.first.return_value = None

    mock_db.execute.side_effect = [mock_user_res, mock_mem_res]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            f"/api/v1/organizations/{foreign_org_id}/members",
            json={"email": "target@external.edu", "role": "student"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
        assert "not an active member" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_assign_member_duplicate_prevention(client: TestClient):
    """Assigning an already active member returns HTTP 409 Conflict."""
    admin_id = uuid.uuid4()
    target_user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    mock_admin = User(
        id=admin_id,
        email="admin@apex.edu",
        full_name="Dean Connor",
        auth_provider_id="sub-admin",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_org = Organization(
        id=org_id,
        name="Apex Tech",
        slug="apex-tech",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_admin_membership = OrganizationMembership(
        id=uuid.uuid4(),
        organization_id=org_id,
        user_id=admin_id,
        role=MembershipRole.ADMIN.value,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_target_user = User(
        id=target_user_id,
        email="active@apex.edu",
        full_name="Active Member",
        auth_provider_id="sub-active",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_existing_mem = OrganizationMembership(
        id=uuid.uuid4(),
        organization_id=org_id,
        user_id=target_user_id,
        role=MembershipRole.STUDENT.value,
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    token = create_access_token(subject="sub-admin", email="admin@apex.edu")

    mock_db = AsyncMock()
    mock_admin_res = MagicMock()
    mock_admin_res.scalars.return_value.first.return_value = mock_admin
    mock_mem_res = MagicMock()
    mock_mem_res.first.return_value = (mock_admin_membership, mock_org)

    mock_target_res = MagicMock()
    mock_target_res.scalars.return_value.first.return_value = mock_target_user

    mock_existing_mem_res = MagicMock()
    mock_existing_mem_res.scalars.return_value.first.return_value = mock_existing_mem

    mock_db.execute.side_effect = [
        mock_admin_res,
        mock_mem_res,
        mock_target_res,
        mock_existing_mem_res,
    ]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            f"/api/v1/organizations/{org_id}/members",
            json={"email": "active@apex.edu", "role": "researcher"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 409
        assert "already an active member" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_assign_member_nonexistent_user_returns_404(client: TestClient):
    """Assigning membership for a user who has not registered returns HTTP 404."""
    admin_id = uuid.uuid4()
    org_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    mock_admin = User(
        id=admin_id,
        email="admin@apex.edu",
        full_name="Dean Connor",
        auth_provider_id="sub-admin",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_org = Organization(
        id=org_id,
        name="Apex Tech",
        slug="apex-tech",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_admin_membership = OrganizationMembership(
        id=uuid.uuid4(),
        organization_id=org_id,
        user_id=admin_id,
        role=MembershipRole.ADMIN.value,
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    token = create_access_token(subject="sub-admin", email="admin@apex.edu")

    mock_db = AsyncMock()
    mock_admin_res = MagicMock()
    mock_admin_res.scalars.return_value.first.return_value = mock_admin
    mock_mem_res = MagicMock()
    mock_mem_res.first.return_value = (mock_admin_membership, mock_org)

    mock_target_res = MagicMock()
    mock_target_res.scalars.return_value.first.return_value = None

    mock_db.execute.side_effect = [
        mock_admin_res,
        mock_mem_res,
        mock_target_res,
    ]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            f"/api/v1/organizations/{org_id}/members",
            json={"email": "unregistered@apex.edu", "role": "student"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_assign_member_invalid_role_returns_422(client: TestClient):
    """Submitting an invalid membership role returns HTTP 422 Unprocessable Entity."""
    admin_id = uuid.uuid4()
    org_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    mock_admin = User(
        id=admin_id,
        email="admin@apex.edu",
        full_name="Dean Connor",
        auth_provider_id="sub-admin",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_org = Organization(
        id=org_id,
        name="Apex Tech",
        slug="apex-tech",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_admin_membership = OrganizationMembership(
        id=uuid.uuid4(),
        organization_id=org_id,
        user_id=admin_id,
        role=MembershipRole.ADMIN.value,
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    token = create_access_token(subject="sub-admin", email="admin@apex.edu")

    mock_db = AsyncMock()
    mock_admin_res = MagicMock()
    mock_admin_res.scalars.return_value.first.return_value = mock_admin
    mock_mem_res = MagicMock()
    mock_mem_res.first.return_value = (mock_admin_membership, mock_org)

    mock_db.execute.side_effect = [
        mock_admin_res,
        mock_mem_res,
    ]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            f"/api/v1/organizations/{org_id}/members",
            json={"email": "anyone@apex.edu", "role": "super_root_admin"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422
        assert "invalid membership role" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_invalid_bearer_token_rejected(client: TestClient):
    """Requests with malformed or invalid Bearer tokens are rejected with HTTP 401."""
    org_id = uuid.uuid4()
    response = client.get(
        f"/api/v1/organizations/{org_id}",
        headers={"Authorization": "Bearer invalid.tampered.token"},
    )
    assert response.status_code == 401
    assert "detail" in response.json()



from datetime import datetime, timezone
import uuid
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.db.session import get_db
from app.main import app
from app.models.enums import MembershipRole, ResourceCategory
from app.models.membership import OrganizationMembership
from app.models.organization import Organization
from app.models.resource import Resource
from app.models.user import User


def test_list_resources_unauthenticated_rejected(client: TestClient):
    """Unauthenticated requests to resources endpoint are rejected with HTTP 401."""
    org_id = uuid.uuid4()
    response = client.get(f"/api/v1/organizations/{org_id}/resources")
    assert response.status_code == 401


def test_list_resources_denied_for_non_member(client: TestClient):
    """Users without active membership in the target organization are rejected with HTTP 403."""
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
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
            f"/api/v1/organizations/{org_id}/resources",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
        assert "not an active member" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_list_resources_scoped_to_organization(client: TestClient):
    """Authorized members can list operational resources in their organization."""
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    mock_user = User(
        id=user_id,
        email="researcher@apex.edu",
        full_name="Dr. Jordan",
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
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_res = Resource(
        id=uuid.uuid4(),
        organization_id=org_id,
        name="Cryo-TEM Microscope",
        slug="cryo-tem",
        category=ResourceCategory.LAB_INSTRUMENT.value,
        location="Hall B, Room 12",
        is_available=True,
        requires_approval=True,
        requires_permit=False,
        requires_qualification=False,
        hourly_rate_credits=50,
        specifications_json={},
        created_at=now,
        updated_at=now,
    )

    token = create_access_token(subject="sub-researcher", email="researcher@apex.edu")

    mock_db = AsyncMock()
    mock_user_res = MagicMock()
    mock_user_res.scalars.return_value.first.return_value = mock_user
    mock_mem_res = MagicMock()
    mock_mem_res.first.return_value = (mock_membership, mock_org)
    mock_res_list = MagicMock()
    mock_res_list.scalars.return_value.all.return_value = [mock_res]

    mock_db.execute.side_effect = [mock_user_res, mock_mem_res, mock_res_list]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get(
            f"/api/v1/organizations/{org_id}/resources",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Cryo-TEM Microscope"
        assert data[0]["hourly_rate_credits"] == 50
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_create_resource_by_lab_manager_success(client: TestClient):
    """Lab managers can create new institutional resources."""
    manager_id = uuid.uuid4()
    org_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    mock_manager = User(
        id=manager_id,
        email="manager@apex.edu",
        full_name="Dr. Aris Vance",
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
        user_id=manager_id,
        role=MembershipRole.LAB_MANAGER.value,
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    token = create_access_token(subject="sub-manager", email="manager@apex.edu")

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_user_res = MagicMock()
    mock_user_res.scalars.return_value.first.return_value = mock_manager
    mock_mem_res = MagicMock()
    mock_mem_res.first.return_value = (mock_membership, mock_org)

    mock_db.execute.side_effect = [mock_user_res, mock_mem_res]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            f"/api/v1/organizations/{org_id}/resources",
            json={
                "name": "5-Axis CNC Mill",
                "category": "workshop_tool",
                "location": "Fabrication High Bay",
                "description": "High precision milling center",
                "requires_approval": False,
                "hourly_rate_credits": 30,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "5-Axis CNC Mill"
        assert data["category"] == "workshop_tool"
        assert data["requires_approval"] is False
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_create_resource_denied_for_student(client: TestClient):
    """Students are forbidden from creating resources (HTTP 403)."""
    student_id = uuid.uuid4()
    org_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    mock_student = User(
        id=student_id,
        email="student@apex.edu",
        full_name="Student Lin",
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
    mock_mem_res.first.return_value = (mock_membership, mock_org)

    mock_db.execute.side_effect = [mock_user_res, mock_mem_res]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            f"/api/v1/organizations/{org_id}/resources",
            json={
                "name": "Unauthorized Instrument",
                "category": "lab_instrument",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
        assert "insufficient role permissions" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_update_resource_availability_by_manager(client: TestClient):
    """Managers can toggle resource availability (e.g. maintenance state)."""
    manager_id = uuid.uuid4()
    org_id = uuid.uuid4()
    res_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    mock_manager = User(
        id=manager_id,
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
        user_id=manager_id,
        role=MembershipRole.LAB_MANAGER.value,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_res = Resource(
        id=res_id,
        organization_id=org_id,
        name="Laser Cutter",
        slug="laser-cutter",
        category=ResourceCategory.WORKSHOP_TOOL.value,
        is_available=True,
        requires_approval=False,
        hourly_rate_credits=20,
        created_at=now,
        updated_at=now,
    )

    token = create_access_token(subject="sub-manager", email="manager@apex.edu")

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_user_res = MagicMock()
    mock_user_res.scalars.return_value.first.return_value = mock_manager
    mock_mem_res = MagicMock()
    mock_mem_res.first.return_value = (mock_membership, mock_org)
    mock_res_find = MagicMock()
    mock_res_find.scalars.return_value.first.return_value = mock_res

    mock_db.execute.side_effect = [mock_user_res, mock_mem_res, mock_res_find]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.patch(
            f"/api/v1/organizations/{org_id}/resources/{res_id}",
            json={"is_available": False},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["is_available"] is False
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_get_resource_availability_returns_slots(client: TestClient):
    """Resource availability endpoint returns scheduled slots."""
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    res_id = uuid.uuid4()
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
    mock_res = Resource(
        id=res_id,
        organization_id=org_id,
        name="Spectrometer",
        slug="spectrometer",
        category=ResourceCategory.LAB_INSTRUMENT.value,
        is_available=True,
        requires_approval=True,
        hourly_rate_credits=15,
        created_at=now,
        updated_at=now,
    )

    token = create_access_token(subject="sub-student", email="student@apex.edu")

    mock_db = AsyncMock()
    mock_user_res = MagicMock()
    mock_user_res.scalars.return_value.first.return_value = mock_user
    mock_mem_res = MagicMock()
    mock_mem_res.first.return_value = (mock_membership, mock_org)
    mock_res_find = MagicMock()
    mock_res_find.scalars.return_value.first.return_value = mock_res
    mock_bookings_res = MagicMock()
    mock_bookings_res.scalars.return_value.all.return_value = []

    mock_db.execute.side_effect = [
        mock_user_res,
        mock_mem_res,
        mock_res_find,
        mock_bookings_res,
    ]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get(
            f"/api/v1/organizations/{org_id}/resources/{res_id}/availability",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["resource_id"] == str(res_id)
        assert data["reserved_slots"] == []
    finally:
        app.dependency_overrides.pop(get_db, None)

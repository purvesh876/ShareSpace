from datetime import datetime, timedelta, timezone
import uuid
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.db.session import get_db
from app.main import app
from app.models.booking import Booking
from app.models.enums import BookingStatus, MembershipRole, ResourceCategory
from app.models.membership import OrganizationMembership
from app.models.organization import Organization
from app.models.resource import Resource
from app.models.user import User


def test_create_booking_unauthenticated_rejected(client: TestClient):
    """Unauthenticated requests are rejected with HTTP 401."""
    org_id = uuid.uuid4()
    response = client.post(
        f"/api/v1/organizations/{org_id}/bookings",
        json={
            "resource_id": str(uuid.uuid4()),
            "start_time": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            "end_time": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
        },
    )
    assert response.status_code == 401


def test_create_booking_past_start_time_rejected_400(client: TestClient):
    """Booking requests in the past are rejected with HTTP 400."""
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
        response = client.post(
            f"/api/v1/organizations/{org_id}/bookings",
            json={
                "resource_id": str(uuid.uuid4()),
                "start_time": (now - timedelta(hours=2)).isoformat(),
                "end_time": (now + timedelta(hours=1)).isoformat(),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 400
        assert "past" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_create_booking_end_before_start_rejected_422(client: TestClient):
    """Schema validation rejects requests where end_time <= start_time."""
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
        response = client.post(
            f"/api/v1/organizations/{org_id}/bookings",
            json={
                "resource_id": str(uuid.uuid4()),
                "start_time": (now + timedelta(hours=2)).isoformat(),
                "end_time": (now + timedelta(hours=1)).isoformat(),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.pop(get_db, None)



def test_create_booking_success_pending_approval(client: TestClient):
    """Creating a reservation on an approval-gated asset sets status PENDING."""
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    res_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    mock_user = User(
        id=user_id,
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
    mock_membership = OrganizationMembership(
        id=uuid.uuid4(),
        organization_id=org_id,
        user_id=user_id,
        role=MembershipRole.STUDENT.value,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_resource = Resource(
        id=res_id,
        organization_id=org_id,
        name="Cryo-TEM",
        slug="cryo-tem",
        category=ResourceCategory.LAB_INSTRUMENT.value,
        is_available=True,
        requires_approval=True,
        hourly_rate_credits=50,
        created_at=now,
        updated_at=now,
    )

    token = create_access_token(subject="sub-student", email="student@apex.edu")

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_user_res = MagicMock()
    mock_user_res.scalars.return_value.first.return_value = mock_user
    mock_mem_res = MagicMock()
    mock_mem_res.first.return_value = (mock_membership, mock_org)

    mock_res_stmt = MagicMock()
    mock_res_stmt.scalars.return_value.first.return_value = mock_resource

    # Overlap check returns None (no conflict)
    mock_overlap_res = MagicMock()
    mock_overlap_res.scalars.return_value.first.return_value = None

    mock_db.execute.side_effect = [
        mock_user_res,
        mock_mem_res,
        mock_res_stmt,
        mock_overlap_res,
    ]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            f"/api/v1/organizations/{org_id}/bookings",
            json={
                "resource_id": str(res_id),
                "start_time": (now + timedelta(hours=1)).isoformat(),
                "end_time": (now + timedelta(hours=3)).isoformat(),
                "purpose": "Protein crystal structure determination",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "pending"
        assert data["resource_name"] == "Cryo-TEM"
        assert data["total_credits"] == 100  # 2 hours * 50 credits/hr
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_create_booking_overlapping_time_rejected_409(client: TestClient):
    """Overlapping booking requests on the same resource are rejected with HTTP 409 Conflict."""
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    res_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    mock_user = User(
        id=user_id,
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
    mock_membership = OrganizationMembership(
        id=uuid.uuid4(),
        organization_id=org_id,
        user_id=user_id,
        role=MembershipRole.STUDENT.value,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_resource = Resource(
        id=res_id,
        organization_id=org_id,
        name="Cryo-TEM",
        slug="cryo-tem",
        category=ResourceCategory.LAB_INSTRUMENT.value,
        is_available=True,
        requires_approval=True,
        hourly_rate_credits=50,
        created_at=now,
        updated_at=now,
    )
    existing_conflicting_booking = Booking(
        id=uuid.uuid4(),
        organization_id=org_id,
        resource_id=res_id,
        user_id=uuid.uuid4(),
        start_time=now + timedelta(hours=1),
        end_time=now + timedelta(hours=3),
        status=BookingStatus.APPROVED.value,
        created_at=now,
        updated_at=now,
    )

    token = create_access_token(subject="sub-student", email="student@apex.edu")

    mock_db = AsyncMock()
    mock_user_res = MagicMock()
    mock_user_res.scalars.return_value.first.return_value = mock_user
    mock_mem_res = MagicMock()
    mock_mem_res.first.return_value = (mock_membership, mock_org)

    mock_res_stmt = MagicMock()
    mock_res_stmt.scalars.return_value.first.return_value = mock_resource

    # Overlap check returns conflicting booking
    mock_overlap_res = MagicMock()
    mock_overlap_res.scalars.return_value.first.return_value = existing_conflicting_booking

    mock_db.execute.side_effect = [
        mock_user_res,
        mock_mem_res,
        mock_res_stmt,
        mock_overlap_res,
    ]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            f"/api/v1/organizations/{org_id}/bookings",
            json={
                "resource_id": str(res_id),
                "start_time": (now + timedelta(hours=2)).isoformat(),
                "end_time": (now + timedelta(hours=4)).isoformat(),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 409
        assert "conflicts" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_list_my_bookings_returns_records(client: TestClient):
    """Users can view their active bookings."""
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    res_id = uuid.uuid4()
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
    mock_resource = Resource(
        id=res_id,
        organization_id=org_id,
        name="GPU Cluster Node",
        slug="gpu-node",
        category=ResourceCategory.COMPUTING_CLUSTER.value,
        is_available=True,
        hourly_rate_credits=40,
        created_at=now,
        updated_at=now,
    )
    mock_booking = Booking(
        id=uuid.uuid4(),
        organization_id=org_id,
        resource_id=res_id,
        user_id=user_id,
        start_time=now + timedelta(days=1),
        end_time=now + timedelta(days=1, hours=2),
        status=BookingStatus.APPROVED.value,
        purpose="Model fine-tuning",
        total_credits=80,
        created_at=now,
        updated_at=now,
    )

    token = create_access_token(subject="sub-researcher", email="researcher@apex.edu")

    mock_db = AsyncMock()
    mock_user_res = MagicMock()
    mock_user_res.scalars.return_value.first.return_value = mock_user
    mock_mem_res = MagicMock()
    mock_mem_res.first.return_value = (mock_membership, mock_org)

    mock_bookings_res = MagicMock()
    mock_bookings_res.all.return_value = [(mock_booking, mock_resource)]

    mock_db.execute.side_effect = [
        mock_user_res,
        mock_mem_res,
        mock_bookings_res,
    ]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get(
            f"/api/v1/organizations/{org_id}/bookings/my",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["resource_name"] == "GPU Cluster Node"
        assert data[0]["status"] == "approved"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_cancel_booking_by_owner_success(client: TestClient):
    """The booking owner can cancel their reservation."""
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    res_id = uuid.uuid4()
    booking_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    mock_user = User(
        id=user_id,
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
    mock_membership = OrganizationMembership(
        id=uuid.uuid4(),
        organization_id=org_id,
        user_id=user_id,
        role=MembershipRole.STUDENT.value,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_resource = Resource(
        id=res_id,
        organization_id=org_id,
        name="3D Printer",
        slug="3d-printer",
        is_available=True,
        created_at=now,
        updated_at=now,
    )
    mock_booking = Booking(
        id=booking_id,
        organization_id=org_id,
        resource_id=res_id,
        user_id=user_id,
        start_time=now + timedelta(hours=4),
        end_time=now + timedelta(hours=6),
        status=BookingStatus.PENDING.value,
        created_at=now,
        updated_at=now,
    )

    token = create_access_token(subject="sub-student", email="student@apex.edu")

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_user_res = MagicMock()
    mock_user_res.scalars.return_value.first.return_value = mock_user
    mock_mem_res = MagicMock()
    mock_mem_res.first.return_value = (mock_membership, mock_org)

    mock_find_booking = MagicMock()
    mock_find_booking.first.return_value = (mock_booking, mock_resource)

    mock_db.execute.side_effect = [
        mock_user_res,
        mock_mem_res,
        mock_find_booking,
    ]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            f"/api/v1/organizations/{org_id}/bookings/{booking_id}/cancel",
            json={"reason": "Experiment rescheduled"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_cancel_booking_by_unauthorized_user_forbidden_403(client: TestClient):
    """A regular member cannot cancel another user's reservation."""
    owner_id = uuid.uuid4()
    caller_id = uuid.uuid4()
    org_id = uuid.uuid4()
    res_id = uuid.uuid4()
    booking_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    mock_caller = User(
        id=caller_id,
        email="intruder@apex.edu",
        full_name="Another Student",
        auth_provider_id="sub-intruder",
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
        user_id=caller_id,
        role=MembershipRole.STUDENT.value,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_resource = Resource(
        id=res_id,
        organization_id=org_id,
        name="Laser Cutter",
        slug="laser-cutter",
        is_available=True,
        created_at=now,
        updated_at=now,
    )
    mock_booking = Booking(
        id=booking_id,
        organization_id=org_id,
        resource_id=res_id,
        user_id=owner_id,  # Owned by someone else
        start_time=now + timedelta(hours=4),
        end_time=now + timedelta(hours=6),
        status=BookingStatus.APPROVED.value,
        created_at=now,
        updated_at=now,
    )

    token = create_access_token(subject="sub-intruder", email="intruder@apex.edu")

    mock_db = AsyncMock()
    mock_user_res = MagicMock()
    mock_user_res.scalars.return_value.first.return_value = mock_caller
    mock_mem_res = MagicMock()
    mock_mem_res.first.return_value = (mock_membership, mock_org)

    mock_find_booking = MagicMock()
    mock_find_booking.first.return_value = (mock_booking, mock_resource)

    mock_db.execute.side_effect = [
        mock_user_res,
        mock_mem_res,
        mock_find_booking,
    ]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            f"/api/v1/organizations/{org_id}/bookings/{booking_id}/cancel",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
        assert "only cancel your own" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_manager_approve_booking_success(client: TestClient):
    """Lab managers can review and approve pending booking requests."""
    manager_id = uuid.uuid4()
    requester_id = uuid.uuid4()
    org_id = uuid.uuid4()
    res_id = uuid.uuid4()
    booking_id = uuid.uuid4()
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
    mock_resource = Resource(
        id=res_id,
        organization_id=org_id,
        name="Cleanroom Bench",
        slug="cleanroom-bench",
        is_available=True,
        created_at=now,
        updated_at=now,
    )
    mock_booking = Booking(
        id=booking_id,
        organization_id=org_id,
        resource_id=res_id,
        user_id=requester_id,
        start_time=now + timedelta(days=2),
        end_time=now + timedelta(days=2, hours=3),
        status=BookingStatus.PENDING.value,
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

    mock_find_booking = MagicMock()
    mock_find_booking.first.return_value = (mock_booking, mock_resource)

    # Overlap check returns None
    mock_overlap = MagicMock()
    mock_overlap.scalars.return_value.first.return_value = None

    mock_db.execute.side_effect = [
        mock_user_res,
        mock_mem_res,
        mock_find_booking,
        mock_overlap,
    ]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            f"/api/v1/organizations/{org_id}/bookings/{booking_id}/decision",
            json={"action": "approve"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "approved"
    finally:
        app.dependency_overrides.pop(get_db, None)

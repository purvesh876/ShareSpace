from datetime import datetime, timedelta, timezone
import uuid
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.db.session import get_db
from app.main import app
from app.models.booking import Booking
from app.models.enums import BookingStatus, MembershipRole, PermitStatus, QualificationStatus, ResourceCategory
from app.models.membership import OrganizationMembership
from app.models.organization import Organization
from app.models.qualification import Qualification
from app.models.resource import Resource
from app.models.safety_permit import SafetyPermit
from app.models.user import User


def test_booking_checkin_success(client: TestClient):
    """Reserver can check in an approved booking, transitioning status to in_use."""
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    booking_id = uuid.uuid4()
    res_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    mock_user = User(
        id=user_id,
        email="reserver@apex.edu",
        full_name="Reserver User",
        auth_provider_id="sub-checkin-1",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_org = Organization(
        id=org_id,
        name="Apex Institute",
        slug="apex-institute",
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
        name="DGX H100 Node",
        slug="dgx-h100",
        category=ResourceCategory.COMPUTING_CLUSTER.value,
        is_available=True,
        requires_approval=False,
        requires_permit=False,
        requires_qualification=False,
        hourly_rate_credits=40,
        created_at=now,
        updated_at=now,
    )
    mock_booking = Booking(
        id=booking_id,
        organization_id=org_id,
        resource_id=res_id,
        user_id=user_id,
        start_time=now - timedelta(minutes=10),
        end_time=now + timedelta(hours=2),
        status=BookingStatus.APPROVED.value,
        total_credits=80,
        created_at=now,
        updated_at=now,
    )

    token = create_access_token(subject="sub-checkin-1", email="reserver@apex.edu")

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_user_res = MagicMock()
    mock_user_res.scalars.return_value.first.return_value = mock_user
    mock_mem_res = MagicMock()
    mock_mem_res.first.return_value = (mock_membership, mock_org)
    mock_booking_query = MagicMock()
    mock_booking_query.first.return_value = (mock_booking, mock_resource)

    mock_db.execute.side_effect = [
        mock_user_res,
        mock_mem_res,
        mock_booking_query,
    ]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            f"/api/v1/organizations/{org_id}/bookings/{booking_id}/checkin",
            json={
                "checklist_completed": True,
                "condition_notes": "Equipment clean and intact upon arrival.",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_use"
        assert data["checkin_time"] is not None
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_booking_checkin_unauthorized_other_user_rejected(client: TestClient):
    """A non-owner researcher cannot check in another user's reservation."""
    reserver_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    booking_id = uuid.uuid4()
    res_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    mock_other_user = User(
        id=other_user_id,
        email="other@apex.edu",
        full_name="Other User",
        auth_provider_id="sub-other-1",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_org = Organization(
        id=org_id,
        name="Apex Institute",
        slug="apex-institute",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_membership = OrganizationMembership(
        id=uuid.uuid4(),
        organization_id=org_id,
        user_id=other_user_id,
        role=MembershipRole.RESEARCHER.value,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_resource = Resource(
        id=res_id,
        organization_id=org_id,
        name="DGX H100 Node",
        slug="dgx-h100",
        category=ResourceCategory.COMPUTING_CLUSTER.value,
        is_available=True,
        requires_approval=False,
        requires_permit=False,
        requires_qualification=False,
        hourly_rate_credits=40,
        created_at=now,
        updated_at=now,
    )
    # Booking belongs to reserver_id, not other_user_id
    mock_booking = Booking(
        id=booking_id,
        organization_id=org_id,
        resource_id=res_id,
        user_id=reserver_id,
        start_time=now - timedelta(minutes=10),
        end_time=now + timedelta(hours=2),
        status=BookingStatus.APPROVED.value,
        total_credits=80,
        created_at=now,
        updated_at=now,
    )

    token = create_access_token(subject="sub-other-1", email="other@apex.edu")

    mock_db = AsyncMock()
    mock_user_res = MagicMock()
    mock_user_res.scalars.return_value.first.return_value = mock_other_user
    mock_mem_res = MagicMock()
    mock_mem_res.first.return_value = (mock_membership, mock_org)
    mock_booking_query = MagicMock()
    mock_booking_query.first.return_value = (mock_booking, mock_resource)

    mock_db.execute.side_effect = [
        mock_user_res,
        mock_mem_res,
        mock_booking_query,
    ]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            f"/api/v1/organizations/{org_id}/bookings/{booking_id}/checkin",
            json={"checklist_completed": True},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
        assert "not authorized" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_booking_return_success(client: TestClient):
    """Reserver can return an in_use booking, transitioning status to completed."""
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    booking_id = uuid.uuid4()
    res_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    mock_user = User(
        id=user_id,
        email="reserver@apex.edu",
        full_name="Reserver User",
        auth_provider_id="sub-return-1",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_org = Organization(
        id=org_id,
        name="Apex Institute",
        slug="apex-institute",
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
        name="DGX H100 Node",
        slug="dgx-h100",
        category=ResourceCategory.COMPUTING_CLUSTER.value,
        is_available=True,
        requires_approval=False,
        requires_permit=False,
        requires_qualification=False,
        hourly_rate_credits=40,
        created_at=now,
        updated_at=now,
    )
    mock_booking = Booking(
        id=booking_id,
        organization_id=org_id,
        resource_id=res_id,
        user_id=user_id,
        start_time=now - timedelta(hours=1),
        end_time=now + timedelta(hours=1),
        status=BookingStatus.IN_USE.value,
        checkin_time=now - timedelta(hours=1),
        total_credits=80,
        created_at=now,
        updated_at=now,
    )

    token = create_access_token(subject="sub-return-1", email="reserver@apex.edu")

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_user_res = MagicMock()
    mock_user_res.scalars.return_value.first.return_value = mock_user
    mock_mem_res = MagicMock()
    mock_mem_res.first.return_value = (mock_membership, mock_org)
    mock_booking_query = MagicMock()
    mock_booking_query.first.return_value = (mock_booking, mock_resource)

    mock_db.execute.side_effect = [
        mock_user_res,
        mock_mem_res,
        mock_booking_query,
    ]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            f"/api/v1/organizations/{org_id}/bookings/{booking_id}/return",
            json={
                "checklist_completed": True,
                "condition_notes": "All workspace cleaned, logged out successfully.",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["checkout_time"] is not None
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_list_my_qualifications_and_permits(client: TestClient):
    """User can list their active qualifications and safety permits scoped to organization."""
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    mock_user = User(
        id=user_id,
        email="student@apex.edu",
        full_name="Student Scholar",
        auth_provider_id="sub-student-1",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_org = Organization(
        id=org_id,
        name="Apex Institute",
        slug="apex-institute",
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
    mock_qual = Qualification(
        id=uuid.uuid4(),
        organization_id=org_id,
        user_id=user_id,
        qualification_code="QUAL-CNC-BASIC",
        title="Basic CNC Safety Clearance",
        certified_by="Lab Staff",
        certified_at=now - timedelta(days=30),
        status=QualificationStatus.ACTIVE.value,
        created_at=now,
        updated_at=now,
    )
    mock_permit = SafetyPermit(
        id=uuid.uuid4(),
        organization_id=org_id,
        user_id=user_id,
        permit_type="General Lab Safety",
        issuer="Safety Board",
        issue_date=now - timedelta(days=60),
        expiry_date=now + timedelta(days=300),
        status=PermitStatus.ACTIVE.value,
        created_at=now,
        updated_at=now,
    )

    token = create_access_token(subject="sub-student-1", email="student@apex.edu")

    mock_db = AsyncMock()
    mock_user_res = MagicMock()
    mock_user_res.scalars.return_value.first.return_value = mock_user
    mock_mem_res = MagicMock()
    mock_mem_res.first.return_value = (mock_membership, mock_org)

    mock_qual_res = MagicMock()
    mock_qual_res.all.return_value = [(mock_qual, None)]

    mock_db.execute.side_effect = [
        mock_user_res,
        mock_mem_res,
        mock_qual_res,
    ]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get(
            f"/api/v1/organizations/{org_id}/qualifications/my",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        quals = response.json()
        assert len(quals) == 1
        assert quals[0]["qualification_code"] == "QUAL-CNC-BASIC"
    finally:
        app.dependency_overrides.pop(get_db, None)

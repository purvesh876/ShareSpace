from datetime import datetime, timedelta, timezone
import uuid
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.db.session import get_db
from app.main import app
from app.models.enums import BookingStatus, MembershipRole, PermitStatus, QualificationStatus, ResourceCategory
from app.models.membership import OrganizationMembership
from app.models.organization import Organization
from app.models.qualification import Qualification
from app.models.resource import Resource
from app.models.safety_permit import SafetyPermit
from app.models.user import User


def test_booking_rejected_when_safety_permit_missing(client: TestClient):
    """When resource.requires_permit is True and user lacks active permit, booking is rejected with 403."""
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    res_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    mock_user = User(
        id=user_id,
        email="researcher@apex.edu",
        full_name="Researcher User",
        auth_provider_id="sub-researcher-1",
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
    # Hazardous equipment requiring safety permit
    mock_resource = Resource(
        id=res_id,
        organization_id=org_id,
        name="High-Field NMR Spectrometer",
        slug="high-field-nmr",
        category=ResourceCategory.LAB_INSTRUMENT.value,
        is_available=True,
        requires_approval=False,
        requires_permit=True,
        requires_qualification=False,
        hourly_rate_credits=50,
        created_at=now,
        updated_at=now,
    )

    token = create_access_token(subject="sub-researcher-1", email="researcher@apex.edu")

    mock_db = AsyncMock()
    mock_user_res = MagicMock()
    mock_user_res.scalars.return_value.first.return_value = mock_user
    mock_mem_res = MagicMock()
    mock_mem_res.first.return_value = (mock_membership, mock_org)
    mock_res_query = MagicMock()
    mock_res_query.scalars.return_value.first.return_value = mock_resource
    # Permit query returns None (no permit found)
    mock_permit_query = MagicMock()
    mock_permit_query.scalars.return_value.first.return_value = None

    mock_db.execute.side_effect = [
        mock_user_res,
        mock_mem_res,
        mock_res_query,
        mock_permit_query,
    ]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            f"/api/v1/organizations/{org_id}/bookings",
            json={
                "resource_id": str(res_id),
                "start_time": (now + timedelta(hours=2)).isoformat(),
                "end_time": (now + timedelta(hours=4)).isoformat(),
                "purpose": "Cryo-probe NMR experiment",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
        assert "Safety permit required" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_booking_rejected_when_qualification_missing(client: TestClient):
    """When resource.requires_qualification is True and user lacks certification, booking is rejected with 403."""
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    res_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    mock_user = User(
        id=user_id,
        email="student@apex.edu",
        full_name="Student User",
        auth_provider_id="sub-student-qual",
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
    mock_resource = Resource(
        id=res_id,
        organization_id=org_id,
        name="5-Axis CNC Milling Center",
        slug="5-axis-cnc",
        category=ResourceCategory.WORKSHOP_TOOL.value,
        is_available=True,
        requires_approval=False,
        requires_permit=False,
        requires_qualification=True,
        hourly_rate_credits=30,
        created_at=now,
        updated_at=now,
    )

    token = create_access_token(subject="sub-student-qual", email="student@apex.edu")

    mock_db = AsyncMock()
    mock_user_res = MagicMock()
    mock_user_res.scalars.return_value.first.return_value = mock_user
    mock_mem_res = MagicMock()
    mock_mem_res.first.return_value = (mock_membership, mock_org)
    mock_res_query = MagicMock()
    mock_res_query.scalars.return_value.first.return_value = mock_resource
    # Qualification query returns None
    mock_qual_query = MagicMock()
    mock_qual_query.scalars.return_value.first.return_value = None

    mock_db.execute.side_effect = [
        mock_user_res,
        mock_mem_res,
        mock_res_query,
        mock_qual_query,
    ]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            f"/api/v1/organizations/{org_id}/bookings",
            json={
                "resource_id": str(res_id),
                "start_time": (now + timedelta(hours=2)).isoformat(),
                "end_time": (now + timedelta(hours=4)).isoformat(),
                "purpose": "Precision prototype machining",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
        assert "Equipment qualification required" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_booking_succeeds_when_eligible_with_permit_and_qualification(client: TestClient):
    """When user has valid unexpired permit and qualification, booking succeeds."""
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    res_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    start_time = now + timedelta(hours=2)
    end_time = now + timedelta(hours=4)

    mock_user = User(
        id=user_id,
        email="qualified@apex.edu",
        full_name="Qualified Senior Researcher",
        auth_provider_id="sub-qualified-1",
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
        name="Titan Krios G4 Cryo-TEM",
        slug="titan-krios-g4",
        category=ResourceCategory.LAB_INSTRUMENT.value,
        is_available=True,
        requires_approval=False,
        requires_permit=True,
        requires_qualification=True,
        hourly_rate_credits=60,
        created_at=now,
        updated_at=now,
    )
    mock_permit = SafetyPermit(
        id=uuid.uuid4(),
        organization_id=org_id,
        user_id=user_id,
        permit_type="Electron Microscopy Radiation Safety",
        issue_date=now - timedelta(days=30),
        expiry_date=now + timedelta(days=335),
        status=PermitStatus.ACTIVE.value,
        created_at=now,
        updated_at=now,
    )
    mock_qual = Qualification(
        id=uuid.uuid4(),
        organization_id=org_id,
        user_id=user_id,
        resource_id=res_id,
        qualification_code="EM-KRIOS-LVL3",
        title="Cryo-TEM Independent Operator",
        certified_at=now - timedelta(days=60),
        expires_at=now + timedelta(days=300),
        status=QualificationStatus.ACTIVE.value,
        created_at=now,
        updated_at=now,
    )

    token = create_access_token(subject="sub-qualified-1", email="qualified@apex.edu")

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_user_res = MagicMock()
    mock_user_res.scalars.return_value.first.return_value = mock_user
    mock_mem_res = MagicMock()
    mock_mem_res.first.return_value = (mock_membership, mock_org)
    mock_res_query = MagicMock()
    mock_res_query.scalars.return_value.first.return_value = mock_resource
    mock_permit_query = MagicMock()
    mock_permit_query.scalars.return_value.first.return_value = mock_permit
    mock_qual_query = MagicMock()
    mock_qual_query.scalars.return_value.first.return_value = mock_qual
    mock_overlap_query = MagicMock()
    mock_overlap_query.scalars.return_value.first.return_value = None

    mock_db.execute.side_effect = [
        mock_user_res,
        mock_mem_res,
        mock_res_query,
        mock_permit_query,
        mock_qual_query,
        mock_overlap_query,
    ]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            f"/api/v1/organizations/{org_id}/bookings",
            json={
                "resource_id": str(res_id),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "purpose": "Atomic resolution protein structure determination",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "approved"
        assert data["total_credits"] == 120
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_booking_succeeds_without_permit_or_qualification_for_unrestricted_equipment(client: TestClient):
    """
    Regression test: When resource.requires_permit is False and requires_qualification is False
    (e.g. NVIDIA DGX H100 Supercomputing Node), a researcher without safety credentials
    can reserve the equipment without encountering HTTP 403.
    """
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    res_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    start_time = now + timedelta(hours=2)
    end_time = now + timedelta(hours=4)

    mock_user = User(
        id=user_id,
        email="unrestricted@apex.edu",
        full_name="Standard Researcher",
        auth_provider_id="sub-unrestricted-1",
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
    # Unrestricted equipment (no permit, no qualification)
    mock_resource = Resource(
        id=res_id,
        organization_id=org_id,
        name="NVIDIA DGX H100 Supercomputing Node",
        slug="nvidia-dgx-h100",
        category=ResourceCategory.COMPUTING_CLUSTER.value,
        is_available=True,
        requires_approval=False,
        requires_permit=False,
        requires_qualification=False,
        hourly_rate_credits=40,
        created_at=now,
        updated_at=now,
    )

    token = create_access_token(subject="sub-unrestricted-1", email="unrestricted@apex.edu")

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_user_res = MagicMock()
    mock_user_res.scalars.return_value.first.return_value = mock_user
    mock_mem_res = MagicMock()
    mock_mem_res.first.return_value = (mock_membership, mock_org)
    mock_res_query = MagicMock()
    mock_res_query.scalars.return_value.first.return_value = mock_resource
    mock_overlap_query = MagicMock()
    mock_overlap_query.scalars.return_value.first.return_value = None

    mock_db.execute.side_effect = [
        mock_user_res,
        mock_mem_res,
        mock_res_query,
        mock_overlap_query,
    ]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            f"/api/v1/organizations/{org_id}/bookings",
            json={
                "resource_id": str(res_id),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "purpose": "Distributed transformer inference benchmark",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "approved"
        assert data["total_credits"] == 80
        assert data["resource_id"] == str(res_id)
    finally:
        app.dependency_overrides.pop(get_db, None)

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_current_user, require_org_member
from app.core.config import settings
from app.db.session import get_db
from app.main import app
from app.models.booking import Booking
from app.models.enums import BookingStatus, MembershipRole
from app.models.membership import OrganizationMembership
from app.models.organization import Organization
from app.models.user import User
from app.services.storage_service import StorageService, validate_image_file_content


# Sample 1x1 valid JPEG bytes
VALID_JPEG_BYTES = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00"
    b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t"
    b"\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a"
    b"\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342"
    b"\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00"
    b"\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b"
    b"\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9"
)

# Sample 1x1 valid PNG bytes
VALID_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00"
    b"\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_validate_image_content_valid():
    ext_jpg = validate_image_file_content(VALID_JPEG_BYTES, "image/jpeg")
    assert ext_jpg == ".jpg"

    ext_png = validate_image_file_content(VALID_PNG_BYTES, "image/png")
    assert ext_png == ".png"


def test_validate_image_content_disguised_rejected():
    with pytest.raises(Exception) as exc_info:
        validate_image_file_content(b"not a real jpeg", "image/jpeg")
    assert "File signature does not match" in str(exc_info.value)


def test_validate_image_content_unsupported_mime():
    with pytest.raises(Exception) as exc_info:
        validate_image_file_content(b"%PDF-1.4...", "application/pdf")
    assert "Unsupported file type" in str(exc_info.value)


@pytest.mark.asyncio
async def test_storage_status_endpoint():
    org_id = uuid.uuid4()
    user_id = uuid.uuid4()

    mock_user = User(id=user_id, email="researcher@test.edu", is_active=True)
    mock_org = Organization(id=org_id, name="Test Org", is_active=True)
    mock_membership = OrganizationMembership(
        id=uuid.uuid4(),
        organization_id=org_id,
        user_id=user_id,
        role=MembershipRole.RESEARCHER.value,
        is_active=True,
    )

    from app.api.deps import OrganizationContext

    async def override_org_member():
        return OrganizationContext(organization=mock_org, membership=mock_membership, user=mock_user)

    app.dependency_overrides[require_org_member] = override_org_member

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res = await ac.get(f"/api/v1/organizations/{org_id}/evidence/status")
            assert res.status_code == 200
            data = res.json()
            assert "configured" in data
            assert data["configured"] is True
            assert data["provider"] == "supabase"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_upload_evidence_success():
    org_id = uuid.uuid4()
    user_id = uuid.uuid4()
    booking_id = uuid.uuid4()

    mock_user = User(id=user_id, email="researcher@test.edu", is_active=True)
    mock_org = Organization(id=org_id, name="Test Org", is_active=True)
    mock_membership = OrganizationMembership(
        id=uuid.uuid4(),
        organization_id=org_id,
        user_id=user_id,
        role=MembershipRole.RESEARCHER.value,
        is_active=True,
    )
    mock_booking = Booking(
        id=booking_id,
        organization_id=org_id,
        resource_id=uuid.uuid4(),
        user_id=user_id,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        status=BookingStatus.APPROVED.value,
    )

    from app.api.deps import OrganizationContext

    async def override_org_member():
        return OrganizationContext(organization=mock_org, membership=mock_membership, user=mock_user)

    from unittest.mock import MagicMock
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_booking
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[require_org_member] = override_org_member
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch.object(
        StorageService,
        "upload_evidence",
        new_callable=AsyncMock,
        return_value={
            "storage_path": f"org_{org_id}/booking_{booking_id}/checkin_abc123.jpg",
            "signed_url": "https://supabase.co/storage/v1/object/sign/sharespace-evidence/test.jpg?token=abc",
            "filename": "test.jpg",
            "content_type": "image/jpeg",
            "size_bytes": len(VALID_JPEG_BYTES),
            "handover_type": "checkin",
            "uploaded_at": datetime.now(timezone.utc),
        },
    ):
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                files = {"file": ("test.jpg", VALID_JPEG_BYTES, "image/jpeg")}
                data = {"handover_type": "checkin"}
                res = await ac.post(
                    f"/api/v1/organizations/{org_id}/bookings/{booking_id}/evidence/upload",
                    files=files,
                    data=data,
                )
                assert res.status_code == 201
                body = res.json()
                assert body["storage_path"] == f"org_{org_id}/booking_{booking_id}/checkin_abc123.jpg"
                assert "signed_url" in body
                assert body["handover_type"] == "checkin"
        finally:
            app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_signed_url_path_traversal_rejected():
    org_id = uuid.uuid4()
    user_id = uuid.uuid4()
    booking_id = uuid.uuid4()
    other_booking_id = uuid.uuid4()

    mock_user = User(id=user_id, email="researcher@test.edu", is_active=True)
    mock_org = Organization(id=org_id, name="Test Org", is_active=True)
    mock_membership = OrganizationMembership(
        id=uuid.uuid4(),
        organization_id=org_id,
        user_id=user_id,
        role=MembershipRole.RESEARCHER.value,
        is_active=True,
    )
    mock_booking = Booking(
        id=booking_id,
        organization_id=org_id,
        resource_id=uuid.uuid4(),
        user_id=user_id,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        status=BookingStatus.APPROVED.value,
    )

    from app.api.deps import OrganizationContext

    async def override_org_member():
        return OrganizationContext(organization=mock_org, membership=mock_membership, user=mock_user)

    from unittest.mock import MagicMock
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_booking
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[require_org_member] = override_org_member
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # Attempt to request a path from another booking
            malicious_path = f"org_{org_id}/booking_{other_booking_id}/return_secret.jpg"
            res = await ac.get(
                f"/api/v1/organizations/{org_id}/bookings/{booking_id}/evidence/signed-url",
                params={"storage_path": malicious_path},
            )
            # Must be rejected with 403 Forbidden
            assert res.status_code == 403
            assert "Access denied" in res.json()["detail"]
    finally:
        app.dependency_overrides.clear()

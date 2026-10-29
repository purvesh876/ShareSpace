from datetime import datetime, timedelta, timezone
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import create_access_token, get_jwt_secret, verify_token
from app.db.session import get_db
from app.main import app
from app.models.enums import MembershipRole
from app.models.membership import OrganizationMembership
from app.models.organization import Organization
from app.models.user import User


def test_create_and_verify_valid_token():
    """Verify cryptographic token generation and claim extraction."""
    sub = str(uuid.uuid4())
    email = "researcher@apex.edu"
    token = create_access_token(
        subject=sub,
        email=email,
        expires_delta_seconds=3600,
        user_metadata={"full_name": "Dr. Jordan Hayes"},
    )
    payload = verify_token(token)
    assert payload["sub"] == sub
    assert payload["email"] == email
    assert payload["aud"] == "authenticated"
    assert "exp" in payload
    assert payload["user_metadata"]["full_name"] == "Dr. Jordan Hayes"


def test_verify_expired_token_raises_error():
    """Expired tokens must be strictly rejected with a clear ValueError."""
    token = create_access_token(
        subject="expired-user",
        email="expired@apex.edu",
        expires_delta_seconds=-60,
    )
    with pytest.raises(ValueError) as exc:
        verify_token(token)
    assert "expired" in str(exc.value).lower()


def test_verify_tampered_signature_raises_error():
    """Tokens with altered payload or signature must be rejected."""
    token = create_access_token(subject="valid-sub", email="valid@apex.edu")
    parts = token.split(".")
    tampered_token = f"{parts[0]}.{parts[1]}.invalidsignaturexyz"
    with pytest.raises(ValueError) as exc:
        verify_token(tampered_token)
    assert "invalid" in str(exc.value).lower()


def test_verify_wrong_audience_raises_error():
    """Tokens intended for another audience claim must be rejected."""
    token = create_access_token(
        subject="sub",
        email="user@apex.edu",
        extra_claims={"aud": "wrong-audience"},
    )
    with pytest.raises(ValueError) as exc:
        verify_token(token)
    assert "audience" in str(exc.value).lower() or "invalid" in str(exc.value).lower()


def test_get_my_profile_missing_credentials_rejected(client: TestClient):
    """Protected endpoint returns HTTP 401 when Authorization header is absent."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert "Missing authentication credentials" in response.json()["detail"]


def test_get_my_profile_invalid_token_rejected(client: TestClient):
    """Protected endpoint returns HTTP 401 when token is malformed."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer bad.token.signature"},
    )
    assert response.status_code == 401
    detail = response.json()["detail"].lower()
    assert "invalid" in detail or "malformed" in detail


def test_get_my_profile_expired_token_rejected(client: TestClient):
    """Protected endpoint returns HTTP 401 when token has expired."""
    expired_token = create_access_token(
        subject="expired-sub",
        email="expired@apex.edu",
        expires_delta_seconds=-30,
    )
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    assert "expired" in response.json()["detail"]


def test_get_my_profile_success(client: TestClient):
    """Verified token resolves user and returns active institutional memberships."""
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    mock_user = User(
        id=user_id,
        email="maya.lin@apex.edu",
        full_name="Maya Lin",
        auth_provider_id="sub-maya-123",
        is_active=True,
        is_verified=True,
        created_at=now,
        updated_at=now,
    )
    mock_org = Organization(
        id=org_id,
        name="Apex Institute of Technology",
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
        department="Robotics",
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    valid_token = create_access_token(
        subject="sub-maya-123",
        email="maya.lin@apex.edu",
    )

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    # Mock user query result
    mock_user_res = MagicMock()
    mock_user_res.scalars.return_value.first.return_value = mock_user

    # Mock memberships query result
    mock_mem_res = MagicMock()
    mock_mem_res.all.return_value = [(mock_membership, mock_org)]

    mock_db.execute.side_effect = [mock_user_res, mock_mem_res]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "maya.lin@apex.edu"
        assert len(data["memberships"]) == 1
        assert data["memberships"][0]["organization_slug"] == "apex-tech"
        assert data["memberships"][0]["role"] == "student"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_demo_token_generation_in_development(client: TestClient):
    """In development/test, demo personas generate valid cryptographic tokens."""
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.flush = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    # Mock user and org lookups
    mock_res_empty = MagicMock()
    mock_res_empty.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_res_empty

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            "/api/v1/auth/demo-token",
            json={"persona": "manager"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["active_role"] == "lab_manager"

        # Verify the generated token decodes properly
        payload = verify_token(data["access_token"])
        assert payload["email"] == "manager@apex.edu"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_demo_token_rejected_in_production(client: TestClient, monkeypatch):
    """Demo token generation must be strictly forbidden in production environments."""
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "debug", False)

    response = client.post(
        "/api/v1/auth/demo-token",
        json={"persona": "admin"},
    )
    assert response.status_code == 403
    assert "disabled in production" in response.json()["detail"]


def test_algorithm_none_rejected():
    """Tokens with 'alg: none' must be unconditionally rejected."""
    # Construct an unverified token with alg: none
    import jwt as pyjwt
    header = {"alg": "none", "typ": "JWT"}
    payload = {
        "sub": "attacker-user",
        "email": "attacker@fake.edu",
        "aud": "authenticated",
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    }
    raw_token = pyjwt.encode(payload, key="", algorithm="none")
    with pytest.raises(ValueError) as exc:
        verify_token(raw_token)
    assert "none" in str(exc.value).lower()


def test_unallowlisted_algorithm_rejected():
    """Tokens using algorithms not in the allowlist must be rejected."""
    import jwt as pyjwt
    payload = {
        "sub": "some-user",
        "email": "user@apex.edu",
        "aud": "authenticated",
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    }
    # HS512 is not in ALLOWED_JWT_ALGORITHMS ("HS256", "RS256", "ES256")
    raw_token = pyjwt.encode(payload, key="a" * 64, algorithm="HS512")
    with pytest.raises(ValueError) as exc:
        verify_token(raw_token)
    assert "not allowlisted" in str(exc.value).lower()


def test_algorithm_mismatch_rejected(monkeypatch):
    """Token algorithm must match the configured server algorithm."""
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    import jwt as pyjwt

    # Generate RSA key pair
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    payload = {
        "sub": "user-123",
        "email": "user@apex.edu",
        "aud": "authenticated",
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    }
    rs256_token = pyjwt.encode(payload, key=private_pem, algorithm="RS256")

    # Server configured strictly for HS256
    monkeypatch.setattr(settings, "jwt_algorithm", "HS256")
    monkeypatch.setattr(settings, "jwt_algorithms", ["HS256"])
    with pytest.raises(ValueError) as exc:
        verify_token(rs256_token)
    assert "does not match expected algorithm" in str(exc.value)


def test_missing_subject_claim_rejected():
    """Tokens lacking a subject ('sub') claim must be rejected."""
    token = create_access_token(subject="", email="test@apex.edu")
    # Replace sub with empty
    import jwt as pyjwt
    payload = {
        "email": "test@apex.edu",
        "aud": "authenticated",
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    }
    token_without_sub = pyjwt.encode(payload, get_jwt_secret(), algorithm="HS256")
    with pytest.raises(ValueError) as exc:
        verify_token(token_without_sub)
    assert "subject" in str(exc.value).lower() or "sub" in str(exc.value).lower()


def test_production_fail_closed_without_supabase_jwt_secret(monkeypatch):
    """In production mode, missing SUPABASE_JWT_SECRET fails closed with RuntimeError."""
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "supabase_jwt_secret", None)
    monkeypatch.setattr(settings, "jwt_algorithm", "HS256")

    with pytest.raises(RuntimeError) as exc:
        get_jwt_secret()
    assert "Production authentication misconfigured" in str(exc.value)

    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMifQ.abc"
    with pytest.raises(RuntimeError) as exc:
        verify_token(token)
    assert "Production authentication misconfigured" in str(exc.value)


def test_production_rejects_tokens_signed_with_dev_key(monkeypatch):
    """Tokens signed with dev fallback key must be rejected when production secret is configured."""
    dev_token = create_access_token(subject="user-123", email="user@apex.edu")

    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "supabase_jwt_secret", "a-different-strong-production-secret-999")

    with pytest.raises(ValueError) as exc:
        verify_token(dev_token)
    assert "invalid authentication token" in str(exc.value).lower()


def test_asymmetric_rs256_verification_with_public_key(monkeypatch):
    """Verify that RS256 token verification works with an asymmetric public key."""
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    import jwt as pyjwt

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    monkeypatch.setattr(settings, "jwt_algorithm", "RS256")
    monkeypatch.setattr(settings, "supabase_jwt_public_key", public_pem)
    monkeypatch.setattr(settings, "supabase_url", None)

    payload = {
        "sub": "asymmetric-user-id",
        "email": "rs256@apex.edu",
        "aud": "authenticated",
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    }
    rs256_token = pyjwt.encode(payload, key=private_pem, algorithm="RS256")

    decoded = verify_token(rs256_token)
    assert decoded["sub"] == "asymmetric-user-id"
    assert decoded["email"] == "rs256@apex.edu"


def test_get_my_profile_deactivated_user_rejected(client: TestClient):
    """Deactivated user account returns HTTP 403 Forbidden."""
    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    mock_deactivated_user = User(
        id=user_id,
        email="inactive@apex.edu",
        full_name="Inactive User",
        auth_provider_id="sub-inactive",
        is_active=False,
        is_verified=True,
        created_at=now,
        updated_at=now,
    )

    token = create_access_token(subject="sub-inactive", email="inactive@apex.edu")

    mock_db = AsyncMock()
    mock_user_res = MagicMock()
    mock_user_res.scalars.return_value.first.return_value = mock_deactivated_user
    mock_db.execute.return_value = mock_user_res

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
        assert "deactivated" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_es256_valid_token_verification_with_jwks_mock(monkeypatch):
    """Verify that an ES256 token signed with EC P-256 key is verified against JWKS."""
    from cryptography.hazmat.primitives.asymmetric import ec
    import jwt as pyjwt

    # Generate EC P-256 key pair
    ec_private_key = ec.generate_private_key(ec.SECP256R1())
    ec_public_key = ec_private_key.public_key()

    kid = "supabase-ec-key-1"
    payload = {
        "sub": "supabase-es256-user-uuid",
        "email": "researcher@apex.edu",
        "aud": "authenticated",
        "iss": "supabase",
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    }
    es256_token = pyjwt.encode(payload, ec_private_key, algorithm="ES256", headers={"kid": kid})

    # Mock JWKS key resolution
    mock_jwk = MagicMock()
    mock_jwk.key = ec_public_key
    mock_client = MagicMock()
    mock_client.get_signing_key_from_jwt.return_value = mock_jwk

    monkeypatch.setattr("app.core.security.get_jwks_client", lambda url: mock_client)
    monkeypatch.setattr(settings, "supabase_url", "https://zyvtpsvcxfehtthzpfix.supabase.co")

    decoded = verify_token(es256_token)
    assert decoded["sub"] == "supabase-es256-user-uuid"
    assert decoded["email"] == "researcher@apex.edu"
    assert decoded["aud"] == "authenticated"


def test_es256_invalid_signature_rejected(monkeypatch):
    """An ES256 token with a signature that does not match the public key must be rejected."""
    from cryptography.hazmat.primitives.asymmetric import ec
    import jwt as pyjwt

    # Key pair 1: used to sign
    priv1 = ec.generate_private_key(ec.SECP256R1())
    # Key pair 2: returned by JWKS
    priv2 = ec.generate_private_key(ec.SECP256R1())

    payload = {
        "sub": "user-456",
        "email": "user@apex.edu",
        "aud": "authenticated",
        "iss": "supabase",
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    }
    es256_token = pyjwt.encode(payload, priv1, algorithm="ES256", headers={"kid": "key-1"})

    mock_jwk = MagicMock()
    mock_jwk.key = priv2.public_key()
    mock_client = MagicMock()
    mock_client.get_signing_key_from_jwt.return_value = mock_jwk

    monkeypatch.setattr("app.core.security.get_jwks_client", lambda url: mock_client)
    monkeypatch.setattr(settings, "supabase_url", "https://zyvtpsvcxfehtthzpfix.supabase.co")

    with pytest.raises(ValueError) as exc:
        verify_token(es256_token)
    assert "signature verification failed" in str(exc.value).lower()


def test_es256_unknown_key_id_rejected(monkeypatch):
    """When the JWKS cannot find the requested key ID, verification fails closed."""
    from cryptography.hazmat.primitives.asymmetric import ec
    from jwt.exceptions import PyJWKClientError
    import jwt as pyjwt

    priv = ec.generate_private_key(ec.SECP256R1())
    payload = {
        "sub": "user-unknown-kid",
        "email": "unknown@apex.edu",
        "aud": "authenticated",
        "iss": "supabase",
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    }
    token = pyjwt.encode(payload, priv, algorithm="ES256", headers={"kid": "nonexistent-kid"})

    mock_client = MagicMock()
    mock_client.get_signing_key_from_jwt.side_effect = PyJWKClientError("Unable to find key with kid nonexistent-kid")

    monkeypatch.setattr("app.core.security.get_jwks_client", lambda url: mock_client)
    monkeypatch.setattr(settings, "supabase_url", "https://zyvtpsvcxfehtthzpfix.supabase.co")

    with pytest.raises(ValueError) as exc:
        verify_token(token)
    assert "invalid authentication token" in str(exc.value).lower()


def test_es256_expired_token_rejected(monkeypatch):
    """An expired ES256 token must be rejected."""
    from cryptography.hazmat.primitives.asymmetric import ec
    import jwt as pyjwt

    priv = ec.generate_private_key(ec.SECP256R1())
    payload = {
        "sub": "expired-es256-user",
        "email": "expired@apex.edu",
        "aud": "authenticated",
        "iss": "supabase",
        "exp": int((datetime.now(timezone.utc) - timedelta(minutes=5)).timestamp()),
    }
    expired_token = pyjwt.encode(payload, priv, algorithm="ES256", headers={"kid": "key-1"})

    mock_jwk = MagicMock()
    mock_jwk.key = priv.public_key()
    mock_client = MagicMock()
    mock_client.get_signing_key_from_jwt.return_value = mock_jwk

    monkeypatch.setattr("app.core.security.get_jwks_client", lambda url: mock_client)
    monkeypatch.setattr(settings, "supabase_url", "https://zyvtpsvcxfehtthzpfix.supabase.co")

    with pytest.raises(ValueError) as exc:
        verify_token(expired_token)
    assert "expired" in str(exc.value).lower()


def test_es256_jwks_unreachable_fails_closed(monkeypatch):
    """When the JWKS endpoint is unreachable, verification fails closed."""
    from cryptography.hazmat.primitives.asymmetric import ec
    import jwt as pyjwt

    priv = ec.generate_private_key(ec.SECP256R1())
    payload = {
        "sub": "user-unreachable-jwks",
        "email": "user@apex.edu",
        "aud": "authenticated",
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    }
    token = pyjwt.encode(payload, priv, algorithm="ES256", headers={"kid": "key-1"})

    mock_client = MagicMock()
    mock_client.get_signing_key_from_jwt.side_effect = RuntimeError("Connection refused by auth service")

    monkeypatch.setattr("app.core.security.get_jwks_client", lambda url: mock_client)
    monkeypatch.setattr(settings, "supabase_url", "https://zyvtpsvcxfehtthzpfix.supabase.co")

    with pytest.raises(ValueError) as exc:
        verify_token(token)
    assert "authentication service unreachable" in str(exc.value).lower()


def test_legacy_hs256_rejected_when_excluded_from_jwt_algorithms(monkeypatch):
    """When the server restricts algorithms to ES256, legacy HS256 tokens are rejected."""
    token = create_access_token(subject="user-hs256", email="hs256@apex.edu")

    monkeypatch.setattr(settings, "jwt_algorithms", ["ES256"])
    with pytest.raises(ValueError) as exc:
        verify_token(token)
    assert "does not match expected algorithm" in str(exc.value)


def test_get_current_user_rejects_identity_conflict_on_email_hijack(client: TestClient):
    """
    If an authenticated token claims an email belonging to an existing account with
    a different auth_provider_id, the server rejects with HTTP 403.
    """
    existing_user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    mock_existing_user = User(
        id=existing_user_id,
        email="target@apex.edu",
        full_name="Legitimate User",
        auth_provider_id="sub-legit-original",
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    # Malicious/conflicting token with same email but different sub
    token = create_access_token(subject="sub-attacker", email="target@apex.edu")

    mock_db = AsyncMock()
    # 1. First lookup by auth_provider_id == sub-attacker -> returns None
    mock_sub_res = MagicMock()
    mock_sub_res.scalars.return_value.first.return_value = None

    # 2. Second lookup by email == target@apex.edu -> returns mock_existing_user
    mock_email_res = MagicMock()
    mock_email_res.scalars.return_value.first.return_value = mock_existing_user

    mock_db.execute.side_effect = [mock_sub_res, mock_email_res]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 403
        assert "identity conflict" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_db, None)




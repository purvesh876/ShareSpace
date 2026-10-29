import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    "origin",
    [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ],
)
def test_cors_preflight_allowed_origins(client: TestClient, origin: str):
    """Verify that OPTIONS preflight requests from all allowed development origins return 200."""
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_preflight_disallowed_origin(client: TestClient):
    """Verify that an arbitrary disallowed origin is rejected with 400 on preflight."""
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://malicious-site.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_cors_get_health_from_port_5174(client: TestClient):
    """Verify GET /api/v1/health from port 5174 succeeds with correct CORS headers."""
    response = client.get(
        "/api/v1/health",
        headers={"Origin": "http://localhost:5174"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5174"
    data = response.json()
    assert data["status"] == "ok"


def test_cors_get_ready_from_port_5174(client: TestClient):
    """
    Verify GET /api/v1/ready from port 5174 includes CORS headers,
    while honestly returning HTTP 503 when DATABASE_URL is unconfigured.
    """
    from unittest.mock import patch
    with patch("app.core.config.settings.database_url", None):
        response = client.get(
            "/api/v1/ready",
            headers={"Origin": "http://localhost:5174"},
        )
        assert response.status_code == 503
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5174"
        data = response.json()
        assert data["status"] == "unavailable"
        assert data["database"] == "not configured"


def test_cors_get_ready_connected_from_port_5174(client: TestClient):
    """
    Verify GET /api/v1/ready includes CORS headers when returning HTTP 200 connected.
    """
    from unittest.mock import AsyncMock, patch
    with patch(
        "app.services.health_service.check_db_connection",
        new=AsyncMock(return_value=(True, "connected", "Active")),
    ):
        response = client.get(
            "/api/v1/ready",
            headers={"Origin": "http://localhost:5174"},
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5174"
        data = response.json()
        assert data["status"] == "ready"
        assert data["database"] == "connected"

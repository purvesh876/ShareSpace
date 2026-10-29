from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient


def test_readiness_when_database_not_configured(client: TestClient):
    """
    When DATABASE_URL is not set, /ready should honestly report 503 Service Unavailable
    with database status 'not configured', never falsely claiming healthy.
    """
    with patch("app.core.config.settings.database_url", None):
        response = client.get("/api/v1/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unavailable"
        assert data["database"] == "not configured"
        assert "timestamp" in data


def test_readiness_when_database_unreachable(client: TestClient):
    """
    When database connection fails or times out, /ready should return 503 with 'unreachable'.
    """
    with patch(
        "app.services.health_service.check_db_connection",
        new=AsyncMock(return_value=(False, "unreachable", "Connection refused")),
    ):
        response = client.get("/api/v1/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unavailable"
        assert data["database"] == "unreachable"


def test_readiness_when_database_connected(client: TestClient):
    """
    When database connection succeeds, /ready should return 200 with 'connected'.
    """
    with patch(
        "app.services.health_service.check_db_connection",
        new=AsyncMock(return_value=(True, "connected", "Active")),
    ):
        response = client.get("/api/v1/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["database"] == "connected"

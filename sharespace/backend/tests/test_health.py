from fastapi.testclient import TestClient
from app.core.config import settings


def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "health" in data
    assert "ready" in data


def test_health_endpoint_when_database_unconfigured(client: TestClient, monkeypatch):
    """Verify health endpoint reports database_configured=False when DATABASE_URL is None."""
    monkeypatch.setattr(settings, "database_url", None)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app_name"] == "ShareSpace API"
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data
    assert "database_configured" in data
    assert data["database_configured"] is False


def test_health_endpoint_reports_configured_database(client: TestClient, monkeypatch):
    """Verify health endpoint reports database_configured=True when DATABASE_URL is present."""
    monkeypatch.setattr(settings, "database_url", "postgresql+asyncpg://postgres:postgres@localhost:5432/sharespace")
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database_configured"] is True

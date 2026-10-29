import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.db.session import (
    check_db_connection,
    close_db_engine,
    get_async_engine,
    get_db,
    reset_db_engine,
)
from app.main import app


def test_database_settings_validation_rejects_non_postgres():
    """Verify that SQLite or unsupported database engines are strictly rejected."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(database_url="sqlite:///test.db")
    assert "ShareSpace strictly requires PostgreSQL" in str(exc_info.value)


def test_database_settings_accepts_postgres_variants():
    """Verify valid PostgreSQL dialect connection strings are accepted."""
    s1 = Settings(database_url="postgresql://user:pass@localhost:5432/db")
    assert s1.database_url == "postgresql://user:pass@localhost:5432/db"

    s2 = Settings(database_url="postgresql+asyncpg://user:pass@localhost:5432/db")
    assert s2.database_url == "postgresql+asyncpg://user:pass@localhost:5432/db"

    s3 = Settings(database_url="postgresql+psycopg://user:pass@localhost:5432/db")
    assert s3.database_url == "postgresql+psycopg://user:pass@localhost:5432/db"


def test_database_settings_normalizes_empty_url():
    """Whitespace or empty strings should normalize to None (detached dev mode)."""
    s = Settings(database_url="   ")
    assert s.database_url is None


def test_missing_database_configuration_engine_is_none(monkeypatch):
    """When DATABASE_URL is None, get_async_engine returns None."""
    reset_db_engine()
    from app.core.config import settings

    monkeypatch.setattr(settings, "database_url", None)
    engine = get_async_engine()
    assert engine is None


@pytest.mark.asyncio
async def test_missing_database_configuration_get_db_raises(monkeypatch):
    """Calling get_db() without DATABASE_URL raises a descriptive RuntimeError."""
    reset_db_engine()
    from app.core.config import settings

    monkeypatch.setattr(settings, "database_url", None)

    with pytest.raises(RuntimeError) as exc_info:
        gen = get_db()
        await anext(gen)
    assert "Database is not configured" in str(exc_info.value)


@pytest.mark.asyncio
async def test_missing_database_check_db_connection(monkeypatch):
    """check_db_connection returns (False, 'not configured', ...) when unset."""
    reset_db_engine()
    from app.core.config import settings

    monkeypatch.setattr(settings, "database_url", None)
    is_ready, status_label, err_msg = await check_db_connection()
    assert is_ready is False
    assert status_label == "not configured"
    assert "DATABASE_URL is not set" in err_msg


@pytest.mark.asyncio
async def test_safe_database_session_cleanup():
    """Verify that get_db rolls back on exception and closes the session."""
    mock_session = AsyncMock()
    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__.return_value = mock_session

    with patch("app.db.session.get_async_engine", return_value=MagicMock()):
        with patch("app.db.session._session_factory", mock_factory):
            # Test exception handling and rollback
            with pytest.raises(ValueError):
                gen = get_db()
                session = await anext(gen)
                assert session is mock_session
                await gen.athrow(ValueError("Simulated query failure"))

            mock_session.rollback.assert_awaited_once()
            mock_session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_close_db_engine_disposes_engine():
    """Verify close_db_engine cleanly calls engine.dispose()."""
    mock_engine = AsyncMock()
    with patch("app.db.session._engine", mock_engine):
        await close_db_engine()
        mock_engine.dispose.assert_awaited_once()


def test_demo_mode_startup_without_database():
    """
    Ensure the application boots without database configuration,
    serving endpoints cleanly in detached demo mode.
    """
    with patch("app.core.config.settings.database_url", None):
        with TestClient(app) as client:
            # Root health & meta
            resp_root = client.get("/")
            assert resp_root.status_code == 200
            assert resp_root.json()["status"] == "online"

            # Health endpoint
            resp_health = client.get("/api/v1/health")
            assert resp_health.status_code == 200
            assert resp_health.json()["status"] == "ok"
            assert resp_health.json()["database_configured"] is False

            # Readiness endpoint truthfully reports 503
            resp_ready = client.get("/api/v1/ready")
            assert resp_ready.status_code == 503
            assert resp_ready.json()["status"] == "unavailable"
            assert resp_ready.json()["database"] == "not configured"


@pytest.mark.asyncio
async def test_database_connection_when_configured():
    """
    When database connection is mocked or active, check_db_connection verifies connectivity.
    """
    with patch(
        "tests.test_database.check_db_connection",
        new=AsyncMock(return_value=(True, "connected", None)),
    ):
        is_ready, status_label, err_msg = await check_db_connection()
        assert is_ready is True
        assert status_label == "connected"
        assert err_msg is None

from datetime import datetime, timezone
from typing import Tuple
from app.core.config import settings
from app.db.session import check_db_connection
from app.schemas.health import HealthResponse, ReadinessResponse


class HealthService:
    @staticmethod
    def get_health() -> HealthResponse:
        is_db_configured = bool(settings.database_url and settings.database_url.strip())
        return HealthResponse(
            status="ok",
            app_name=settings.app_name,
            version=settings.app_version,
            environment=settings.app_env,
            timestamp=datetime.now(timezone.utc),
            database_configured=is_db_configured,
        )

    @staticmethod
    async def get_readiness() -> Tuple[ReadinessResponse, bool]:
        """
        Check database connectivity.
        Returns: (ReadinessResponse, is_ready)
        """
        is_connected, db_status, message = await check_db_connection()
        response = ReadinessResponse(
            status="ready" if is_connected else "unavailable",
            database=db_status,
            timestamp=datetime.now(timezone.utc),
            message=message or ("PostgreSQL connection active." if is_connected else "Database not ready."),
        )
        return response, is_connected

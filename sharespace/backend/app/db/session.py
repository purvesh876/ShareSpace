import asyncio
from typing import AsyncGenerator, Optional, Tuple
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import settings
from app.core.logging import logger

_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def get_async_engine() -> Optional[AsyncEngine]:
    """
    Retrieve or initialize the centralized SQLAlchemy AsyncEngine.
    Returns None if settings.database_url is not configured.
    """
    global _engine, _session_factory
    if _engine is not None:
        return _engine

    if not settings.database_url:
        return None

    url = settings.database_url
    # Ensure asyncpg driver for async SQLAlchemy if bare postgresql:// is provided
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    connect_args = {}
    if "supabase.co" in url or "pooler.supabase.com" in url or "ssl=require" in url:
        connect_args["ssl"] = "require"

    _engine = create_async_engine(
        url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_pre_ping=True,
        echo=settings.debug,
        connect_args=connect_args,
    )
    _session_factory = async_sessionmaker(
        bind=_engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    return _engine


def reset_db_engine() -> None:
    """
    Reset engine and session factory references (useful for testing environments).
    """
    global _engine, _session_factory
    _engine = None
    _session_factory = None


async def close_db_engine() -> None:
    """
    Cleanly dispose of engine connections on application shutdown.
    """
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an asynchronous database session.
    Raises RuntimeError if database is not configured.
    Ensures safe rollback on exception and cleanup on exit.
    """
    engine = get_async_engine()
    if engine is None or _session_factory is None:
        raise RuntimeError("Database is not configured. Please set DATABASE_URL.")

    async with _session_factory() as session:
        try:
            if settings.db_enforce_app_role:
                try:
                    await session.execute(text("SET LOCAL ROLE sharespace_app;"))
                except Exception as exc:
                    logger.debug("Database role sharespace_app could not be set: %s", exc)
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_connection() -> Tuple[bool, str, Optional[str]]:
    """
    Check PostgreSQL database availability without holding long-lived connections.
    Returns: (is_ready: bool, status_label: str, error_message: Optional[str])
    """
    if not settings.database_url:
        return False, "not configured", "DATABASE_URL is not set."

    try:
        engine = get_async_engine()
        if engine is None:
            return False, "not configured", "Engine could not be initialized."

        async with asyncio.timeout(settings.db_timeout):
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        return True, "connected", None
    except asyncio.TimeoutError:
        logger.warning("Database readiness check timed out after %s seconds", settings.db_timeout)
        return False, "unreachable", f"Connection timed out after {settings.db_timeout}s"
    except Exception as exc:
        logger.warning("Database readiness check failed: %s", str(exc))
        return False, "unreachable", "Failed to connect to configured PostgreSQL instance."

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool
from app.core.config import settings


def get_test_engine():
    url = settings.database_url
    if not url:
        return None
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    connect_args = {}
    if "supabase.co" in url or "pooler.supabase.com" in url or "ssl=require" in url:
        connect_args["ssl"] = "require"
    return create_async_engine(url, poolclass=NullPool, connect_args=connect_args)


@pytest.mark.asyncio
async def test_sharespace_app_role_attributes():
    """Verify that sharespace_app role exists and strictly has NOBYPASSRLS and NO SUPERUSER privileges."""
    engine = get_test_engine()
    if engine is None:
        pytest.skip("DATABASE_URL not configured")

    async with engine.connect() as conn:
        res = await conn.execute(
            text("SELECT rolname, rolsuper, rolbypassrls FROM pg_roles WHERE rolname = 'sharespace_app';")
        )
        row = res.fetchone()
        assert row is not None, "Role sharespace_app must exist in pg_roles"
        rolname, rolsuper, rolbypassrls = row
        assert rolname == "sharespace_app"
        assert rolsuper is False, "sharespace_app must not be a superuser"
        assert rolbypassrls is False, "sharespace_app must strictly not have BYPASSRLS"
    await engine.dispose()


@pytest.mark.asyncio
async def test_all_eight_tables_have_rls_policies():
    """Verify that all 8 core tables have active RLS policies for sharespace_app."""
    engine = get_test_engine()
    if engine is None:
        pytest.skip("DATABASE_URL not configured")

    expected_tables = {
        "organizations",
        "users",
        "organization_memberships",
        "resources",
        "bookings",
        "safety_permits",
        "qualifications",
        "audit_events",
    }

    async with engine.connect() as conn:
        res = await conn.execute(
            text("""
                SELECT tablename, policyname
                FROM pg_policies
                WHERE schemaname = 'public';
            """)
        )
        rows = res.fetchall()
        covered_tables = {row[0] for row in rows}
        missing = expected_tables - covered_tables
        assert not missing, f"Tables missing RLS policies: {missing}"
    await engine.dispose()


@pytest.mark.asyncio
async def test_tenant_isolation_boundary_enforced_by_database_engine():
    """
    Verify that PostgreSQL engine strictly enforces tenant boundaries under sharespace_app role:
    - Without organization context -> 0 rows returned
    - With wrong organization context -> 0 rows returned
    - With matching organization context -> matching rows returned
    """
    engine = get_test_engine()
    if engine is None:
        pytest.skip("DATABASE_URL not configured")

    async with engine.connect() as conn:
        async with conn.begin() as trans:
            # 1. Fetch live Apex Institute organization id as admin
            org_id = (
                await conn.execute(text("SELECT id FROM organizations WHERE slug = 'apex-institute';"))
            ).scalar()
            assert org_id is not None, "Apex Institute test organization should exist in database"

            # 2. Switch connection to least-privilege sharespace_app role
            await conn.execute(text("SET LOCAL ROLE sharespace_app;"))

            # 3. Query without any organization context -> Storage engine denies all
            c_empty = (await conn.execute(text("SELECT count(*) FROM resources;"))).scalar()
            assert c_empty == 0, "Query without organization context must return 0 rows"

            # 4. Query with non-matching organization context -> Storage engine denies all
            await conn.execute(text("SET LOCAL app.current_organization_id = '00000000-0000-0000-0000-000000000000';"))
            c_wrong = (await conn.execute(text("SELECT count(*) FROM resources;"))).scalar()
            assert c_wrong == 0, "Query with non-matching organization ID must return 0 rows"

            # 5. Query with matching organization context -> Storage engine returns resources
            await conn.execute(text(f"SET LOCAL app.current_organization_id = '{org_id}';"))
            c_right = (await conn.execute(text("SELECT count(*) FROM resources;"))).scalar()
            assert c_right >= 5, "Query with matching organization ID must return tenant resources"

            # Clean rollback
            await trans.rollback()
    await engine.dispose()

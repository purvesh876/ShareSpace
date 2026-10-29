"""least privilege role and rls tenant isolation

Revision ID: 0002_least_privilege_role_and_rls
Revises: 0001_initial_schema
Create Date: 2026-10-29 20:05:00.000000

"""
from typing import Sequence, Union
from alembic import op


# revision identifiers, used by Alembic.
revision: str = '0002_role_and_rls'
down_revision: Union[str, None] = '0001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create dedicated least-privilege application role (without BYPASSRLS)
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sharespace_app') THEN
            CREATE ROLE sharespace_app WITH NOINHERIT NOBYPASSRLS NOCREATEROLE NOCREATEDB;
        END IF;
    END $$;
    """)

    # 2. Allow administrative connection role (postgres) to set role to sharespace_app
    op.execute("GRANT sharespace_app TO postgres;")

    # 3. Grant schema and data manipulation privileges to sharespace_app
    op.execute("GRANT USAGE ON SCHEMA public TO sharespace_app;")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO sharespace_app;")
    op.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO sharespace_app;")
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sharespace_app;")
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO sharespace_app;")

    # 4. Safe helper functions for tenant context resolution
    op.execute("""
    CREATE OR REPLACE FUNCTION current_app_org_id() RETURNS uuid AS $$
    BEGIN
        RETURN NULLIF(current_setting('app.current_organization_id', true), '')::uuid;
    EXCEPTION WHEN OTHERS THEN
        RETURN NULL;
    END;
    $$ LANGUAGE plpgsql STABLE;
    """)

    op.execute("""
    CREATE OR REPLACE FUNCTION current_app_user_id() RETURNS uuid AS $$
    BEGIN
        RETURN NULLIF(current_setting('app.current_user_id', true), '')::uuid;
    EXCEPTION WHEN OTHERS THEN
        RETURN NULL;
    END;
    $$ LANGUAGE plpgsql STABLE;
    """)

    op.execute("""
    CREATE OR REPLACE FUNCTION app_is_bypass_rls() RETURNS boolean AS $$
    BEGIN
        RETURN COALESCE(current_setting('app.bypass_rls', true), 'off') = 'on';
    EXCEPTION WHEN OTHERS THEN
        RETURN false;
    END;
    $$ LANGUAGE plpgsql STABLE;
    """)

    op.execute("GRANT EXECUTE ON FUNCTION current_app_org_id() TO sharespace_app;")
    op.execute("GRANT EXECUTE ON FUNCTION current_app_user_id() TO sharespace_app;")
    op.execute("GRANT EXECUTE ON FUNCTION app_is_bypass_rls() TO sharespace_app;")

    # 5. Row Level Security Policies for tenant-scoped tables
    op.execute("""
    CREATE POLICY resource_tenant_isolation ON resources
    FOR ALL TO sharespace_app
    USING (organization_id = current_app_org_id() OR app_is_bypass_rls())
    WITH CHECK (organization_id = current_app_org_id() OR app_is_bypass_rls());
    """)

    op.execute("""
    CREATE POLICY booking_tenant_isolation ON bookings
    FOR ALL TO sharespace_app
    USING (organization_id = current_app_org_id() OR app_is_bypass_rls())
    WITH CHECK (organization_id = current_app_org_id() OR app_is_bypass_rls());
    """)

    op.execute("""
    CREATE POLICY safety_permit_tenant_isolation ON safety_permits
    FOR ALL TO sharespace_app
    USING (organization_id = current_app_org_id() OR app_is_bypass_rls())
    WITH CHECK (organization_id = current_app_org_id() OR app_is_bypass_rls());
    """)

    op.execute("""
    CREATE POLICY qualification_tenant_isolation ON qualifications
    FOR ALL TO sharespace_app
    USING (organization_id = current_app_org_id() OR app_is_bypass_rls())
    WITH CHECK (organization_id = current_app_org_id() OR app_is_bypass_rls());
    """)

    op.execute("""
    CREATE POLICY audit_event_tenant_isolation ON audit_events
    FOR ALL TO sharespace_app
    USING (organization_id = current_app_org_id() OR app_is_bypass_rls())
    WITH CHECK (organization_id = current_app_org_id() OR app_is_bypass_rls());
    """)

    op.execute("""
    CREATE POLICY membership_tenant_isolation ON organization_memberships
    FOR ALL TO sharespace_app
    USING (organization_id = current_app_org_id() OR user_id = current_app_user_id() OR app_is_bypass_rls())
    WITH CHECK (organization_id = current_app_org_id() OR app_is_bypass_rls());
    """)

    op.execute("""
    CREATE POLICY organization_tenant_isolation ON organizations
    FOR ALL TO sharespace_app
    USING (
        id = current_app_org_id()
        OR EXISTS (
            SELECT 1 FROM organization_memberships m
            WHERE m.organization_id = organizations.id
            AND m.user_id = current_app_user_id()
        )
        OR app_is_bypass_rls()
    )
    WITH CHECK (id = current_app_org_id() OR app_is_bypass_rls());
    """)

    op.execute("""
    CREATE POLICY user_tenant_isolation ON users
    FOR ALL TO sharespace_app
    USING (
        id = current_app_user_id()
        OR EXISTS (
            SELECT 1 FROM organization_memberships m
            WHERE m.user_id = users.id
            AND m.organization_id = current_app_org_id()
        )
        OR app_is_bypass_rls()
    )
    WITH CHECK (id = current_app_user_id() OR app_is_bypass_rls());
    """)


def downgrade() -> None:
    # 1. Drop all RLS policies
    op.execute("DROP POLICY IF EXISTS resource_tenant_isolation ON resources;")
    op.execute("DROP POLICY IF EXISTS booking_tenant_isolation ON bookings;")
    op.execute("DROP POLICY IF EXISTS safety_permit_tenant_isolation ON safety_permits;")
    op.execute("DROP POLICY IF EXISTS qualification_tenant_isolation ON qualifications;")
    op.execute("DROP POLICY IF EXISTS audit_event_tenant_isolation ON audit_events;")
    op.execute("DROP POLICY IF EXISTS membership_tenant_isolation ON organization_memberships;")
    op.execute("DROP POLICY IF EXISTS organization_tenant_isolation ON organizations;")
    op.execute("DROP POLICY IF EXISTS user_tenant_isolation ON users;")

    # 2. Drop helper functions
    op.execute("DROP FUNCTION IF EXISTS current_app_org_id();")
    op.execute("DROP FUNCTION IF EXISTS current_app_user_id();")
    op.execute("DROP FUNCTION IF EXISTS app_is_bypass_rls();")

    # 3. Revoke default privileges and permissions
    op.execute("REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM sharespace_app;")
    op.execute("REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM sharespace_app;")
    op.execute("REVOKE USAGE ON SCHEMA public FROM sharespace_app;")
    op.execute("REVOKE sharespace_app FROM postgres;")

    # 4. Drop role
    op.execute("DROP ROLE IF EXISTS sharespace_app;")

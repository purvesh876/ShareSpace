from pathlib import Path
from alembic.config import Config
from alembic.script import ScriptDirectory
from app.db.base import Base


def test_alembic_config_and_script_directory():
    """Verify Alembic configuration loads properly and discovers version scripts."""
    backend_dir = Path(__file__).resolve().parent.parent
    alembic_ini_path = backend_dir / "alembic.ini"
    assert alembic_ini_path.exists(), f"alembic.ini not found at {alembic_ini_path}"

    cfg = Config(str(alembic_ini_path))
    cfg.set_main_option("script_location", str(backend_dir / "migrations"))
    script_dir = ScriptDirectory.from_config(cfg)
    heads = script_dir.get_heads()
    assert len(heads) == 1
    assert heads[0] in ["0001_initial_schema", "0002_role_and_rls"]


def test_migration_file_has_upgrade_and_downgrade():
    """Verify that the initial migration file defines both upgrade() and downgrade()."""
    backend_dir = Path(__file__).resolve().parent.parent
    versions_dir = backend_dir / "migrations" / "versions"
    migration_files = list(versions_dir.glob("*_initial_schema*.py"))
    assert len(migration_files) == 1, "Expected exactly one initial schema migration file"

    content = migration_files[0].read_text(encoding="utf-8")
    assert "def upgrade() -> None:" in content
    assert "def downgrade() -> None:" in content
    for table in [
        "organizations",
        "users",
        "organization_memberships",
        "resources",
        "bookings",
        "safety_permits",
        "qualifications",
        "audit_events",
    ]:
        assert f"op.create_table(\n        '{table}'" in content or f"'{table}'" in content


def test_base_metadata_is_populated_for_migrations():
    """Verify that Base.metadata has all 8 tables ready for Alembic autogeneration."""
    table_names = list(Base.metadata.tables.keys())
    assert len(table_names) == 8
    assert "organizations" in table_names
    assert "bookings" in table_names

import uuid
from sqlalchemy import Uuid
from sqlalchemy.orm import class_mapper

from app.models import (
    AuditEvent,
    Base,
    Booking,
    BookingStatus,
    MembershipRole,
    Organization,
    OrganizationMembership,
    PermitStatus,
    Qualification,
    QualificationStatus,
    Resource,
    ResourceCategory,
    SafetyPermit,
    User,
)


def test_base_metadata_contains_all_tables():
    """Verify that all 8 core entities are registered in SQLAlchemy metadata."""
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
    actual_tables = set(Base.metadata.tables.keys())
    assert expected_tables.issubset(actual_tables), f"Missing tables: {expected_tables - actual_tables}"


def test_models_primary_keys_are_uuid():
    """All models must use UUID primary keys for secure institutional distributed ID generation."""
    models = [
        Organization,
        User,
        OrganizationMembership,
        Resource,
        Booking,
        SafetyPermit,
        Qualification,
        AuditEvent,
    ]
    for model in models:
        mapper = class_mapper(model)
        pk_cols = mapper.primary_key
        assert len(pk_cols) == 1, f"{model.__name__} has composite or missing PK"
        pk_col = pk_cols[0]
        assert pk_col.name == "id", f"{model.__name__} PK column name is {pk_col.name}, expected 'id'"
        assert isinstance(pk_col.type, Uuid), f"{model.__name__} PK type is {type(pk_col.type)}, expected Uuid"


def test_organization_model_structure():
    """Verify Organization table constraints, indexes, and relationships."""
    table = Base.metadata.tables["organizations"]
    assert "name" in table.columns
    assert "slug" in table.columns
    assert "domain" in table.columns
    assert "is_active" in table.columns
    assert "created_at" in table.columns
    assert "updated_at" in table.columns

    # Verify relationships
    mapper = class_mapper(Organization)
    rel_names = {rel.key for rel in mapper.relationships}
    expected_rels = {"memberships", "resources", "bookings", "safety_permits", "qualifications", "audit_events"}
    assert expected_rels.issubset(rel_names)


def test_user_model_structure():
    """Verify User table constraints, indexes, and relationships."""
    table = Base.metadata.tables["users"]
    assert "email" in table.columns
    assert "full_name" in table.columns
    assert "auth_provider_id" in table.columns
    assert "is_active" in table.columns
    assert "is_verified" in table.columns

    # Email index is unique
    email_unique = any(col.unique for col in [table.columns["email"]]) or any(
        idx.unique and "email" in [c.name for c in idx.columns] for idx in table.indexes
    )
    assert email_unique is True

    # Relationships
    mapper = class_mapper(User)
    rel_names = {rel.key for rel in mapper.relationships}
    expected_rels = {"memberships", "bookings", "safety_permits", "qualifications", "audit_events"}
    assert expected_rels.issubset(rel_names)


def test_organization_membership_tenant_isolation():
    """Verify OrganizationMembership foreign keys, cascade delete, and unique constraint."""
    table = Base.metadata.tables["organization_memberships"]
    fks = {fk.target_fullname: fk for fk in table.foreign_keys}
    assert "organizations.id" in fks
    assert fks["organizations.id"].ondelete.upper() == "CASCADE"
    assert "users.id" in fks
    assert fks["users.id"].ondelete.upper() == "CASCADE"

    # Unique constraint on (organization_id, user_id)
    uq_names = [uq.name for uq in table.constraints if hasattr(uq, "columns") and len(uq.columns) == 2]
    assert "uq_org_membership_user" in uq_names


def test_resource_model_structure():
    """Verify Resource organization foreign key, unique slug per org, and category index."""
    table = Base.metadata.tables["resources"]
    fks = {fk.target_fullname: fk for fk in table.foreign_keys}
    assert "organizations.id" in fks
    assert fks["organizations.id"].ondelete.upper() == "CASCADE"

    # Unique constraint on (organization_id, slug)
    uq_names = [uq.name for uq in table.constraints if hasattr(uq, "columns") and len(uq.columns) == 2]
    assert "uq_resource_org_slug" in uq_names

    # Relationships
    mapper = class_mapper(Resource)
    rel_names = {rel.key for rel in mapper.relationships}
    assert "organization" in rel_names
    assert "bookings" in rel_names
    assert "qualifications" in rel_names


def test_booking_model_foreign_keys_and_indexes():
    """Verify Booking foreign keys to org, resource, user with indexes."""
    table = Base.metadata.tables["bookings"]
    fks = {fk.target_fullname: fk for fk in table.foreign_keys}
    assert "organizations.id" in fks
    assert fks["organizations.id"].ondelete.upper() == "CASCADE"
    assert "resources.id" in fks
    assert fks["resources.id"].ondelete.upper() == "RESTRICT"
    assert "users.id" in fks
    assert fks["users.id"].ondelete.upper() == "CASCADE"

    # Schedule index on (resource_id, start_time, end_time)
    index_names = {idx.name for idx in table.indexes}
    assert "ix_bookings_res_time" in index_names


def test_domain_enums():
    """Verify domain enums have expected institutional values."""
    assert MembershipRole.ADMIN.value == "admin"
    assert MembershipRole.LAB_MANAGER.value == "lab_manager"
    assert MembershipRole.STUDENT.value == "student"

    assert ResourceCategory.LAB_INSTRUMENT.value == "lab_instrument"
    assert ResourceCategory.WORKSHOP_TOOL.value == "workshop_tool"

    assert BookingStatus.PENDING.value == "pending"
    assert BookingStatus.APPROVED.value == "approved"
    assert BookingStatus.REJECTED.value == "rejected"

    assert PermitStatus.ACTIVE.value == "active"
    assert PermitStatus.EXPIRED.value == "expired"

    assert QualificationStatus.ACTIVE.value == "active"
    assert QualificationStatus.SUSPENDED.value == "suspended"

"""initial_schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-10-29 00:58:52.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Organizations
    op.create_table(
        'organizations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('settings_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_organizations_slug', 'organizations', ['slug'], unique=True)
    op.create_index('ix_organizations_domain', 'organizations', ['domain'], unique=False)

    # 2. Users
    op.create_table(
        'users',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('avatar_url', sa.String(length=1024), nullable=True),
        sa.Column('auth_provider_id', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('is_verified', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_auth_provider_id', 'users', ['auth_provider_id'], unique=True)

    # 3. Organization Memberships
    op.create_table(
        'organization_memberships',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('role', sa.String(length=50), server_default='student', nullable=False),
        sa.Column('department', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'user_id', name='uq_org_membership_user')
    )
    op.create_index('ix_organization_memberships_organization_id', 'organization_memberships', ['organization_id'])
    op.create_index('ix_organization_memberships_user_id', 'organization_memberships', ['user_id'])
    op.create_index('ix_organization_memberships_role', 'organization_memberships', ['role'])

    # 4. Resources
    op.create_table(
        'resources',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), server_default='lab_instrument', nullable=False),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('is_available', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('requires_approval', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('requires_permit', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('requires_qualification', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('hourly_rate_credits', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('specifications_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'slug', name='uq_resource_org_slug')
    )
    op.create_index('ix_resources_organization_id', 'resources', ['organization_id'])
    op.create_index('ix_resources_category', 'resources', ['category'])
    op.create_index('ix_resources_org_category', 'resources', ['organization_id', 'category'])

    # 5. Bookings
    op.create_table(
        'bookings',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Uuid(), nullable=False),
        sa.Column('resource_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='pending', nullable=False),
        sa.Column('purpose', sa.Text(), nullable=True),
        sa.Column('total_credits', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('checkin_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('checkout_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resource_id'], ['resources.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_bookings_organization_id', 'bookings', ['organization_id'])
    op.create_index('ix_bookings_resource_id', 'bookings', ['resource_id'])
    op.create_index('ix_bookings_user_id', 'bookings', ['user_id'])
    op.create_index('ix_bookings_status', 'bookings', ['status'])
    op.create_index('ix_bookings_res_time', 'bookings', ['resource_id', 'start_time', 'end_time'])
    op.create_index('ix_bookings_user_status', 'bookings', ['user_id', 'status'])
    op.create_index('ix_bookings_org_status', 'bookings', ['organization_id', 'status'])

    # 6. Safety Permits
    op.create_table(
        'safety_permits',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('permit_type', sa.String(length=100), nullable=False),
        sa.Column('issuer', sa.String(length=255), nullable=True),
        sa.Column('issue_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expiry_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='active', nullable=False),
        sa.Column('document_url', sa.String(length=1024), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_safety_permits_organization_id', 'safety_permits', ['organization_id'])
    op.create_index('ix_safety_permits_user_id', 'safety_permits', ['user_id'])
    op.create_index('ix_safety_permits_status', 'safety_permits', ['status'])
    op.create_index('ix_safety_permits_org_user', 'safety_permits', ['organization_id', 'user_id'])
    op.create_index('ix_safety_permits_user_status', 'safety_permits', ['user_id', 'status'])

    # 7. Qualifications
    op.create_table(
        'qualifications',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('resource_id', sa.Uuid(), nullable=True),
        sa.Column('qualification_code', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('certified_by', sa.String(length=255), nullable=True),
        sa.Column('certified_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='active', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resource_id'], ['resources.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_qualifications_organization_id', 'qualifications', ['organization_id'])
    op.create_index('ix_qualifications_user_id', 'qualifications', ['user_id'])
    op.create_index('ix_qualifications_resource_id', 'qualifications', ['resource_id'])
    op.create_index('ix_qualifications_status', 'qualifications', ['status'])
    op.create_index('ix_qualifications_org_user', 'qualifications', ['organization_id', 'user_id'])

    # 8. Audit Events
    op.create_table(
        'audit_events',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Uuid(), nullable=True),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=False),
        sa.Column('entity_id', sa.String(length=255), nullable=True),
        sa.Column('actor_ip', sa.String(length=64), nullable=True),
        sa.Column('actor_user_agent', sa.String(length=512), nullable=True),
        sa.Column('payload_before', sa.JSON(), nullable=True),
        sa.Column('payload_after', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_events_organization_id', 'audit_events', ['organization_id'])
    op.create_index('ix_audit_events_user_id', 'audit_events', ['user_id'])
    op.create_index('ix_audit_events_action', 'audit_events', ['action'])
    op.create_index('ix_audit_events_entity_type', 'audit_events', ['entity_type'])
    op.create_index('ix_audit_events_timestamp', 'audit_events', ['timestamp'])
    op.create_index('ix_audit_events_org_time', 'audit_events', ['organization_id', 'timestamp'])
    op.create_index('ix_audit_events_entity', 'audit_events', ['entity_type', 'entity_id'])


def downgrade() -> None:
    op.drop_table('audit_events')
    op.drop_table('qualifications')
    op.drop_table('safety_permits')
    op.drop_table('bookings')
    op.drop_table('resources')
    op.drop_table('organization_memberships')
    op.drop_table('users')
    op.drop_table('organizations')

"""initial_schema

Revision ID: 0001
Revises: 
Create Date: 2026-07-18 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Create registered_clients table
    op.create_table(
        'registered_clients',
        sa.Column('hospital_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('hospital_name', sa.String(length=255), nullable=False),
        sa.Column('certificate_fingerprint', sa.String(length=64), nullable=False),
        sa.Column('registered_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.PrimaryKeyConstraint('hospital_id'),
        sa.UniqueConstraint('certificate_fingerprint')
    )

    # 2. Create model_versions table
    op.create_table(
        'model_versions',
        sa.Column('round_id', sa.Integer(), nullable=False),
        sa.Column('checkpoint_path', sa.String(length=512), nullable=False),
        sa.Column('val_dice', sa.Float(), nullable=False),
        sa.Column('val_iou', sa.Float(), nullable=False),
        sa.Column('epsilon', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='false', nullable=False),
        sa.PrimaryKeyConstraint('round_id')
    )

    # 3. Create round_schedules table
    op.create_table(
        'round_schedules',
        sa.Column('round_id', sa.Integer(), nullable=False),
        sa.Column('window_seconds', sa.Integer(), nullable=False),
        sa.Column('expiry_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('OPEN', 'CLOSED', 'AGGREGATING', 'COMPLETED')", name='check_round_schedule_status'),
        sa.PrimaryKeyConstraint('round_id')
    )

    # 4. Create audit_events table
    op.create_table(
        'audit_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('round_id', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('audit_events')
    op.drop_table('round_schedules')
    op.drop_table('model_versions')
    op.drop_table('registered_clients')

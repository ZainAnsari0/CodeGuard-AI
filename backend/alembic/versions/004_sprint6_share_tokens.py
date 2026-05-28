"""Add share_tokens table for report sharing

Revision ID: 004_sprint6_share_tokens
Revises: 003_sprint5_tables
Create Date: 2026-05-26
"""

from alembic import op
import sqlalchemy as sa


revision = '004_sprint6_share_tokens'
down_revision = '003_sprint5_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'share_tokens',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('token', sa.String(64), unique=True, nullable=False, index=True),
        sa.Column('analysis_id', sa.String(36), sa.ForeignKey('analyses.id'), nullable=False, index=True),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_revoked', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('view_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('share_tokens')
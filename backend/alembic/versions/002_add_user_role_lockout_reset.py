"""Add role, lockout, and password reset fields to users table

Revision ID: 002_add_user_role_lockout_reset
Revises: 001_initial
Create Date: 2026-05-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_add_user_role_lockout_reset'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add role column
    op.add_column('users', sa.Column('role', sa.String(20), nullable=False, server_default='developer'))

    # Add account lockout columns
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('locked_until', sa.DateTime(), nullable=True))

    # Add password reset columns
    op.add_column('users', sa.Column('password_reset_token', sa.String(), nullable=True, unique=True))
    op.add_column('users', sa.Column('password_reset_expires', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Remove password reset columns
    op.drop_column('users', 'password_reset_expires')
    op.drop_column('users', 'password_reset_token')

    # Remove lockout columns
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_login_attempts')

    # Remove role column
    op.drop_column('users', 'role')
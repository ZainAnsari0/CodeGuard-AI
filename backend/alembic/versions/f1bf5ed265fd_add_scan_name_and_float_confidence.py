"""add_scan_name_and_float_confidence

Revision ID: f1bf5ed265fd
Revises: 006_add_ai_enrichment_fields
Create Date: 2026-06-16 10:38:20.549064

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1bf5ed265fd'
down_revision: Union[str, None] = '006_add_ai_enrichment_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- analyses ---
    with op.batch_alter_table('analyses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('scan_name', sa.String(), nullable=True))

    with op.batch_alter_table('analyses', schema=None) as batch_op:
        batch_op.alter_column('project_id',
                   existing_type=sa.VARCHAR(length=36),
                   nullable=True)
        batch_op.alter_column('branch',
                   existing_type=sa.VARCHAR(),
                   nullable=True)
        batch_op.create_foreign_key('fk_analyses_users', 'users', ['user_id'], ['id'])
        batch_op.create_index('ix_analyses_user_id', ['user_id'], unique=False)

    # --- code_files ---
    with op.batch_alter_table('code_files', schema=None) as batch_op:
        batch_op.alter_column('project_id',
                   existing_type=sa.VARCHAR(length=36),
                   nullable=True)

    # --- findings ---
    with op.batch_alter_table('findings', schema=None) as batch_op:
        batch_op.alter_column('code_file_id',
                   existing_type=sa.VARCHAR(length=36),
                   nullable=True)
        batch_op.alter_column('project_id',
                   existing_type=sa.VARCHAR(length=36),
                   nullable=True)

    # --- fix_suggestions ---
    with op.batch_alter_table('fix_suggestions', schema=None) as batch_op:
        batch_op.alter_column('confidence',
                   existing_type=sa.VARCHAR(),
                   type_=sa.Float(),
                   existing_nullable=True,
                   postgresql_using="confidence::double precision")

    # --- users ---
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('role',
                   existing_type=sa.VARCHAR(length=20),
                   nullable=False,
                   existing_server_default=sa.text('("developer")'))
        batch_op.create_unique_constraint('uq_users_password_reset_token', ['password_reset_token'])


def downgrade() -> None:
    # --- users ---
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('uq_users_password_reset_token', type_='unique')
        batch_op.alter_column('role',
                   existing_type=sa.VARCHAR(length=20),
                   nullable=True,
                   existing_server_default=sa.text('("developer")'))

    # --- fix_suggestions ---
    with op.batch_alter_table('fix_suggestions', schema=None) as batch_op:
        batch_op.alter_column('confidence',
                   existing_type=sa.Float(),
                   type_=sa.VARCHAR(),
                   existing_nullable=True,
                   postgresql_using="confidence::varchar")

    # --- findings ---
    with op.batch_alter_table('findings', schema=None) as batch_op:
        batch_op.alter_column('project_id',
                   existing_type=sa.VARCHAR(length=36),
                   nullable=False)
        batch_op.alter_column('code_file_id',
                   existing_type=sa.VARCHAR(length=36),
                   nullable=False)

    # --- code_files ---
    with op.batch_alter_table('code_files', schema=None) as batch_op:
        batch_op.alter_column('project_id',
                   existing_type=sa.VARCHAR(length=36),
                   nullable=False)

    # --- analyses ---
    with op.batch_alter_table('analyses', schema=None) as batch_op:
        batch_op.drop_index('ix_analyses_user_id')
        batch_op.drop_constraint('fk_analyses_users', type_='foreignkey')
        batch_op.alter_column('branch',
                   existing_type=sa.VARCHAR(),
                   nullable=False)
        batch_op.alter_column('project_id',
                   existing_type=sa.VARCHAR(length=36),
                   nullable=False)
        batch_op.drop_column('scan_name')
        batch_op.drop_column('user_id')
    # ### end Alembic commands ###

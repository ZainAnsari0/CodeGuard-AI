"""Add classes, enrollments, system_events, kb_articles tables

Revision ID: 003_sprint5_tables
Revises: 002_add_user_role_lockout_reset
Create Date: 2026-05-26
"""

from alembic import op
import sqlalchemy as sa


revision = '003_sprint5_tables'
down_revision = '002_add_user_role_lockout_reset'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'classes',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('instructor_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('join_code', sa.String(16), unique=True, nullable=False, index=True),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    op.create_table(
        'enrollments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('class_id', sa.String(36), sa.ForeignKey('classes.id'), nullable=False, index=True),
        sa.Column('student_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('status', sa.String(20), server_default='active', nullable=False),
        sa.Column('enrolled_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.UniqueConstraint('class_id', 'student_id', name='uq_enrollment_class_student'),
    )

    op.create_table(
        'system_events',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('event_type', sa.String(50), nullable=False, index=True),
        sa.Column('severity', sa.String(10), server_default='info', nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True, index=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
    )
    op.create_index('ix_system_events_severity_created', 'system_events', ['severity', sa.text('created_at DESC')])

    op.create_table(
        'kb_articles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('slug', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('category', sa.String(50), server_default='general', nullable=False),
        sa.Column('cwe_ids', sa.String(200), nullable=True),
        sa.Column('owasp_category', sa.String(50), nullable=True),
        sa.Column('content_markdown', sa.Text(), nullable=False),
        sa.Column('vulnerable_example', sa.Text(), nullable=True),
        sa.Column('safe_example', sa.Text(), nullable=True),
        sa.Column('is_published', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('view_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('kb_articles')
    op.drop_table('system_events')
    op.drop_table('enrollments')
    op.drop_table('classes')
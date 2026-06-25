"""Add performance indexes for common queries

Revision ID: 005_performance_indexes
Revises: 004_sprint6_share_tokens
Create Date: 2026-05-28
"""

from alembic import op
import sqlalchemy as sa


revision = '005_performance_indexes'
down_revision = '004_sprint6_share_tokens'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Findings indexes - most queried table
    # Note: idx_findings_analysis_id duplicates ix_findings_analysis_id from migration 001,
    # but uses a different naming convention. Only add truly new indexes here.
    op.create_index('idx_findings_severity', 'findings', ['severity'])
    op.create_index('idx_findings_status', 'findings', ['status'])

    # Analyses indexes - status filtering, dashboard queries, and ordering
    op.create_index('idx_analyses_status', 'analyses', ['status'])
    op.create_index('idx_analyses_project_status', 'analyses', ['project_id', 'status'])
    op.create_index('idx_analyses_created_at', 'analyses', ['created_at'])
    
    # Convert analysis_metadata to JSONB so we can create a GIN index on it (PostgreSQL only)
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute("ALTER TABLE analyses ALTER COLUMN analysis_metadata TYPE jsonb USING analysis_metadata::jsonb")
        op.create_index('idx_analyses_metadata_gin', 'analyses', ['analysis_metadata'], postgresql_using='gin')

    # Share tokens - created_by index (token already has unique constraint from migration 004)
    op.create_index('idx_share_tokens_created_by', 'share_tokens', ['created_by'])

    # Enrollment - index on student_id for "find classes for student" queries
    op.create_index('idx_enrollments_student_id', 'enrollments', ['student_id'])


def downgrade() -> None:
    op.drop_index('idx_enrollments_student_id', 'enrollments')
    op.drop_index('idx_share_tokens_created_by', 'share_tokens')
    
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.drop_index('idx_analyses_metadata_gin', 'analyses')
        op.execute("ALTER TABLE analyses ALTER COLUMN analysis_metadata TYPE json USING analysis_metadata::json")
    
    op.drop_index('idx_analyses_created_at', 'analyses')
    op.drop_index('idx_analyses_project_status', 'analyses')
    op.drop_index('idx_analyses_status', 'analyses')
    op.drop_index('idx_findings_status', 'findings')
    op.drop_index('idx_findings_severity', 'findings')
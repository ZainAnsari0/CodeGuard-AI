"""Initial migration - create users, projects, code_files, analyses, findings, fix_suggestions tables

Revision ID: 001_initial
Revises:
Create Date: 2026-05-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types for PostgreSQL
    severity_enum = postgresql.ENUM('critical', 'high', 'medium', 'low', 'info', name='severity', create_type=True)
    severity_enum.create(op.get_bind(), checkfirst=True)

    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('email', sa.String(), nullable=False, unique=True),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('is_superuser', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_id', 'users', ['id'], unique=False)

    # Projects table
    op.create_table(
        'projects',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('repository_url', sa.String(), nullable=True),
        sa.Column('branch', sa.String(), server_default='main', nullable=False),
        sa.Column('config', postgresql.JSON(), nullable=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_projects_id', 'projects', ['id'], unique=False)
    op.create_index('ix_projects_user_id', 'projects', ['user_id'], unique=False)

    # Analyses table
    op.create_table(
        'analyses',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('branch', sa.String(), nullable=False),
        sa.Column('commit_hash', sa.String(), nullable=True),
        sa.Column('status', sa.String(), server_default='running', nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('summary', postgresql.JSON(), nullable=True),
        sa.Column('analysis_metadata', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_analyses_id', 'analyses', ['id'], unique=False)
    op.create_index('ix_analyses_project_id', 'analyses', ['project_id'], unique=False)

    # Code files table
    op.create_table(
        'code_files',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('file_name', sa.String(), nullable=False),
        sa.Column('file_extension', sa.String(), nullable=False),
        sa.Column('file_size', sa.Integer(), server_default='0', nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('language', sa.String(), nullable=True),
        sa.Column('line_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_commit_hash', sa.String(), nullable=True),
        sa.Column('last_commit_date', sa.DateTime(), nullable=True),
        sa.Column('file_metadata', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_code_files_id', 'code_files', ['id'], unique=False)
    op.create_index('ix_code_files_project_id', 'code_files', ['project_id'], unique=False)

    # Findings table
    op.create_table(
        'findings',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('code_file_id', sa.String(36), sa.ForeignKey('code_files.id'), nullable=False),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('analysis_id', sa.String(36), sa.ForeignKey('analyses.id'), nullable=False),
        sa.Column('analyzer_type', sa.String(), nullable=False),
        sa.Column('vulnerability_type', sa.String(), nullable=False),
        sa.Column('severity', severity_enum, nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('cwe_id', sa.String(), nullable=True),
        sa.Column('cvss_score', sa.String(), nullable=True),
        sa.Column('cve_id', sa.String(), nullable=True),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('line_start', sa.Integer(), server_default='0', nullable=False),
        sa.Column('line_end', sa.Integer(), server_default='0', nullable=False),
        sa.Column('column_start', sa.Integer(), server_default='0', nullable=False),
        sa.Column('column_end', sa.Integer(), server_default='0', nullable=False),
        sa.Column('code_snippet', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), server_default='new', nullable=False),
        sa.Column('confidence', sa.Integer(), server_default='100', nullable=False),
        sa.Column('finding_metadata', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_findings_id', 'findings', ['id'], unique=False)
    op.create_index('ix_findings_code_file_id', 'findings', ['code_file_id'], unique=False)
    op.create_index('ix_findings_project_id', 'findings', ['project_id'], unique=False)
    op.create_index('ix_findings_analysis_id', 'findings', ['analysis_id'], unique=False)

    # Fix suggestions table
    op.create_table(
        'fix_suggestions',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('finding_id', sa.String(36), sa.ForeignKey('findings.id'), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('priority', sa.Integer(), server_default='0', nullable=False),
        sa.Column('code_before', sa.Text(), nullable=True),
        sa.Column('code_after', sa.Text(), nullable=True),
        sa.Column('language', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_fix_suggestions_id', 'fix_suggestions', ['id'], unique=False)
    op.create_index('ix_fix_suggestions_finding_id', 'fix_suggestions', ['finding_id'], unique=False)


def downgrade() -> None:
    op.drop_table('fix_suggestions')
    op.drop_table('findings')
    op.drop_table('code_files')
    op.drop_table('analyses')
    op.drop_table('projects')
    op.drop_table('users')

    severity_enum = postgresql.ENUM('critical', 'high', 'medium', 'low', 'info', name='severity', create_type=False)
    severity_enum.drop(op.get_bind(), checkfirst=True)
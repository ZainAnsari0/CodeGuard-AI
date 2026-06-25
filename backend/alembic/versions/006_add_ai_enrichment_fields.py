"""Add AI enrichment fields to findings and fix_suggestions

Revision ID: 006_add_ai_enrichment_fields
Revises: 005_performance_indexes
Create Date: 2026-06-09

Adds:
  - findings.explanation (Text) — stores AI-generated explanation JSON
  - findings.explanation_provider (String) — which AI provider generated it
  - findings.explanation_generated_at (DateTime) — when explanation was generated
  - fix_suggestions.ast_validated (Boolean) — whether AST validation passed
  - fix_suggestions.validation_warnings (JSON) — validation warnings list
  - fix_suggestions.confidence (String) — AI confidence score for the fix
"""

from alembic import op
import sqlalchemy as sa


revision = '006_add_ai_enrichment_fields'
down_revision = '005_performance_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add AI enrichment columns to findings
    op.add_column('findings', sa.Column('explanation', sa.Text(), nullable=True))
    op.add_column('findings', sa.Column('explanation_provider', sa.String(), nullable=True))
    op.add_column('findings', sa.Column('explanation_generated_at', sa.DateTime(timezone=True), nullable=True))

    # Add AI validation columns to fix_suggestions
    op.add_column('fix_suggestions', sa.Column('ast_validated', sa.Boolean(), nullable=True))
    op.add_column('fix_suggestions', sa.Column('validation_warnings', sa.JSON(), nullable=True))
    op.add_column('fix_suggestions', sa.Column('confidence', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove AI validation columns from fix_suggestions
    op.drop_column('fix_suggestions', 'confidence')
    op.drop_column('fix_suggestions', 'validation_warnings')
    op.drop_column('fix_suggestions', 'ast_validated')

    # Remove AI enrichment columns from findings
    op.drop_column('findings', 'explanation_generated_at')
    op.drop_column('findings', 'explanation_provider')
    op.drop_column('findings', 'explanation')
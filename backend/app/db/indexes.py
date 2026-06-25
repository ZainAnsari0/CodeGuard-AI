"""
CodeGuard AI - Database Composite Indexes
Defines composite indexes for optimization of common queries on findings and analyses.
"""

import logging
from sqlalchemy import Index
from app.models.analysis import Finding, Analysis

logger = logging.getLogger(__name__)

# Composite indexes on findings
# Optimize queries fetching findings by severity or status for a scan
idx_findings_analysis_severity = Index("idx_findings_analysis_severity", Finding.analysis_id, Finding.severity)
idx_findings_analysis_status = Index("idx_findings_analysis_status", Finding.analysis_id, Finding.status)

# Composite indexes on analyses
# Optimize project status check queries and ordering user scans by creation date
idx_analyses_project_status = Index("idx_analyses_project_status", Analysis.project_id, Analysis.status)
idx_analyses_user_created_at = Index("idx_analyses_user_created_at", Analysis.user_id, Analysis.created_at)

logger.info("Database composite indexes registered successfully")

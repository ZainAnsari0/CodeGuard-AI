"""
CodeGuard AI - Models Module
"""

from app.models.user import User
from app.models.project import Project
from app.models.code_file import CodeFile
from app.models.analysis import Analysis, Finding, FixSuggestion
from app.models.class_ import Class_, Enrollment
from app.models.system_event import SystemEvent
from app.models.kb_article import KBArticle
from app.models.share_token import ShareToken

__all__ = [
    "User", "Project", "CodeFile", "Analysis", "Finding", "FixSuggestion",
    "Class_", "Enrollment", "SystemEvent", "KBArticle", "ShareToken",
]

# Register composite indexes
import app.db.indexes
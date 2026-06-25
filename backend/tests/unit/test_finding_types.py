import pytest
import os
import tempfile
from uuid import uuid4
from sqlalchemy import text, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.core.config import settings
from app.tasks.scan_tasks import _persist_findings
from app.models.analysis import Analysis
from app.models.code_file import CodeFile
from app.models.project import Project
from app.models.user import User

@pytest.mark.asyncio
async def test_persist_findings_normalizes_severity_and_confidence():
    # Set up a temporary file-based SQLite database
    fd, temp_db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    db_url = f"sqlite+aiosqlite:///{temp_db_path}"
    sync_db_url = f"sqlite:///{temp_db_path}"
    
    # Save original database URL
    old_db_url = settings.DATABASE_URL
    settings.DATABASE_URL = db_url
    
    try:
        # Initialize the database schema
        async_engine = create_async_engine(db_url, echo=False)
        async with async_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
            
        async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            user_id = str(uuid4())
            user = User(
                id=user_id,
                email="test_user@codeguard.test",
                full_name="Test User",
                hashed_password="hashedpassword",
                role="developer"
            )
            session.add(user)

            project_id = str(uuid4())
            project = Project(id=project_id, name="Test Project", user_id=user_id)
            session.add(project)
            
            file_id = str(uuid4())
            code_file = CodeFile(
                id=file_id,
                file_path="test_file.py",
                file_name="test_file.py",
                file_extension="py",
                file_size=13,
                content="print('test')",
                language="python"
            )
            session.add(code_file)
            
            scan_id = str(uuid4())
            analysis = Analysis(id=scan_id, project_id=project_id, status="pending")
            session.add(analysis)
            await session.commit()

        # Mock _get_sync_engine to return a sync engine to our temp database
        sync_engine = create_engine(sync_db_url)
        
        findings = [
            {
                "vulnerability_type": "SQL Injection",
                "severity": "high",  # Raw severity High (needs normalization)
                "cwe_id": "CWE-89",
                "file_path": "test_file.py",
                "line_number": 5,
                "code_snippet": "query = SELECT * FROM users",
                "confidence": 0.85,
                "fix_suggestion": {
                    "explanation": "Use param query",
                    "original_code": "query = SELECT * FROM users",
                    "fixed_code": "query = SELECT * FROM users WHERE id = ?",
                    "confidence": 0.95,  # Float confidence score
                }
            }
        ]

        from unittest.mock import patch
        with patch("app.tasks.scan_tasks._get_sync_engine", return_value=sync_engine):
            _persist_findings(scan_id, [file_id], findings)
            
        # Verify findings are persisted and normalized correctly
        async with async_session() as session:
            # Check finding
            result = await session.execute(text("SELECT severity, confidence FROM findings WHERE analysis_id = :scan_id"), {"scan_id": scan_id})
            finding_row = result.fetchone()
            assert finding_row is not None
            assert finding_row[0] == "HIGH"  # Normalized to HIGH
            assert finding_row[1] == 85      # 0.85 * 100
            
            # Check fix suggestion confidence
            result = await session.execute(text("SELECT confidence FROM fix_suggestions"))
            fix_row = result.fetchone()
            assert fix_row is not None
            assert fix_row[0] == 0.95        # Stored as float 0.95
            
        await async_engine.dispose()
        sync_engine.dispose()
    finally:
        settings.DATABASE_URL = old_db_url
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

import pytest
import os
import json
import tempfile
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import text, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from httpx import ASGITransport, AsyncClient

from app.core.config import settings

@pytest.mark.asyncio
async def test_full_scan_pipeline_integration(test_user):
    # Create a temporary file-based SQLite database
    fd, temp_db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    db_url = f"sqlite+aiosqlite:///{temp_db_path}"
    sync_db_url = f"sqlite:///{temp_db_path}"
    
    # Save original database URL
    old_db_url = settings.DATABASE_URL
    settings.DATABASE_URL = db_url
    
    try:
        # Initialize schema
        async_engine = create_async_engine(db_url, echo=False)
        async with async_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
            
        async_session_factory = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
        
        # Create the test user in the new database
        async with async_session_factory() as session:
            from app.models.user import User
            
            db_user = User(
                id=test_user["id"],
                email=test_user["email"],
                full_name="Test User",
                hashed_password="hashedpassword",
                role="developer",
                is_active=True
            )
            session.add(db_user)
            await session.commit()
            
        # Set up standard httpx client with dependency override for get_session
        from main import app
        from app.db.session import get_session
        
        async def override_get_session():
            async with async_session_factory() as session:
                yield session
                
        app.dependency_overrides[get_session] = override_get_session
        
        python_code = """
import os
def run_command(user_input):
    os.system("ping " + user_input)
"""
        
        mock_ai_response = {
            "response": json.dumps({
                "findings": [
                    {
                        "vulnerability_type": "Command Injection",
                        "severity": "critical",
                        "cwe_id": "CWE-78",
                        "file_path": "vuln.py",
                        "line_number": 4,
                        "code_snippet": 'os.system("ping " + user_input)',
                        "explanation": "String formatting in shell command",
                        "remediation": "Use subprocess with shell=False",
                        "confidence": 0.95
                    }
                ],
                "summary": "1 finding",
                "language": "python",
                "total_findings": 1
            }),
            "provider": "mock-ai",
            "model": "mock-model"
        }
        
        sync_engine = create_engine(sync_db_url)
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            with patch("app.ai.fallback_chain.ai_chain.generate", new_callable=AsyncMock, return_value=mock_ai_response), \
                 patch("app.tasks.scan_tasks.celery_app.task") as _, \
                 patch("app.tasks.scan_tasks._get_sync_engine", return_value=sync_engine), \
                 patch("app.tasks.scan_tasks.run_scan_task.delay") as mock_delay:
                
                with patch("app.ai.fallback_chain.ai_chain.get_provider_status", return_value={"mock": True}):
                    response = await client.post(
                        "/api/v1/scanner/upload",
                        headers={"Authorization": f"Bearer {test_user['token']}"},
                        files={"files": ("vuln.py", python_code.encode(), "text/x-python")},
                        data={"language": "python"},
                    )
                    
                    assert response.status_code == 200
                    res_data = response.json()
                    scan_id = res_data["data"]["scan_id"]
                    assert scan_id is not None
                    
                    # Fetch code files created
                    async with async_session_factory() as session:
                        result = await session.execute(
                            text("SELECT id FROM code_files")
                        )
                        file_ids = [row[0] for row in result.fetchall()]
                    
                    # Run the scan task synchronously
                    from app.tasks.scan_tasks import _run_scan_async
                    from app.services.temp_workspace import workspace_service
                    
                    upload_dir = workspace_service.get_workspace_path(scan_id)
                    scan_config = {
                        "file_ids": file_ids,
                        "user_id": test_user["id"],
                        "scan_id": scan_id,
                    }
                    
                    await _run_scan_async(scan_id, file_ids, test_user["id"], upload_dir, scan_config)
                    
                    # Verify database results
                    async with async_session_factory() as session:
                        stmt = text("SELECT status FROM analyses WHERE id = :scan_id")
                        res = await session.execute(stmt, {"scan_id": scan_id})
                        analysis_row = res.fetchone()
                        assert analysis_row is not None
                        assert analysis_row[0] == "completed"
                        
                        finding_stmt = text("SELECT vulnerability_type, severity, cwe_id, confidence, line_start FROM findings WHERE analysis_id = :scan_id")
                        finding_res = await session.execute(finding_stmt, {"scan_id": scan_id})
                        finding_rows = finding_res.fetchall()
                        assert len(finding_rows) >= 1
                        
                        # Verify we found the command injection
                        cmd_inj_findings = [f for f in finding_rows if f[0] == "Command Injection"]
                        assert len(cmd_inj_findings) >= 1
                        
                        # Confidences should contain 90 (from AST scanner) or 95 (from mocked AI)
                        confidences = [f[3] for f in cmd_inj_findings]
                        assert any(c in (90, 95) for c in confidences)
                        
        await async_engine.dispose()
        sync_engine.dispose()
        app.dependency_overrides.clear()
    finally:
        settings.DATABASE_URL = old_db_url
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from app.api.endpoints.scanner import get_scan_status
from app.models.analysis import Analysis
from app.models.user import User

def _get_progress(response):
    data = response["data"]
    if isinstance(data, dict):
        return data["progress"]
    return data.progress

def _get_total_files(response):
    data = response["data"]
    if isinstance(data, dict):
        return data["total_files"]
    return data.total_files

def _get_files_scanned(response):
    data = response["data"]
    if isinstance(data, dict):
        return data["files_scanned"]
    return data.files_scanned

def _get_status(response):
    data = response["data"]
    if isinstance(data, dict):
        return data["status"]
    return data.status

@pytest.mark.asyncio
async def test_progress_tracking_one_of_five_done():
    analysis = Analysis(
        id=str(uuid4()),
        status="running",
        analysis_metadata={"files_completed": 1, "file_count": 5}
    )
    db = AsyncMock()
    db_result = MagicMock()
    db_result.scalar_one_or_none.return_value = analysis
    db.execute.return_value = db_result

    current_user = User(id=str(uuid4()), email="test@test.com", role="developer")
    
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr("app.api.endpoints.scanner.check_analysis_ownership", MagicMock())
        response = await get_scan_status(scan_id=uuid4(), db=db, current_user=current_user)
        
        assert response["success"] is True
        assert _get_progress(response) == pytest.approx(0.2)
        assert _get_total_files(response) == 5
        assert _get_files_scanned(response) == 1
        assert _get_status(response) == "running"

@pytest.mark.asyncio
async def test_progress_tracking_zero_files():
    analysis = Analysis(
        id=str(uuid4()),
        status="running",
        analysis_metadata={"files_completed": 0, "file_count": 0}
    )
    db = AsyncMock()
    db_result = MagicMock()
    db_result.scalar_one_or_none.return_value = analysis
    db.execute.return_value = db_result

    current_user = User(id=str(uuid4()), email="test@test.com", role="developer")
    
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr("app.api.endpoints.scanner.check_analysis_ownership", MagicMock())
        response = await get_scan_status(scan_id=uuid4(), db=db, current_user=current_user)
        
        assert response["success"] is True
        assert _get_progress(response) == 0.5
        assert _get_total_files(response) == 0
        assert _get_files_scanned(response) == 0

@pytest.mark.asyncio
async def test_progress_tracking_all_files_done_but_running():
    analysis = Analysis(
        id=str(uuid4()),
        status="running",
        analysis_metadata={"files_completed": 5, "file_count": 5}
    )
    db = AsyncMock()
    db_result = MagicMock()
    db_result.scalar_one_or_none.return_value = analysis
    db.execute.return_value = db_result

    current_user = User(id=str(uuid4()), email="test@test.com", role="developer")
    
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr("app.api.endpoints.scanner.check_analysis_ownership", MagicMock())
        response = await get_scan_status(scan_id=uuid4(), db=db, current_user=current_user)
        
        assert response["success"] is True
        assert _get_progress(response) == 0.95
        assert _get_total_files(response) == 5
        assert _get_files_scanned(response) == 5

@pytest.mark.asyncio
async def test_progress_tracking_completed_scan():
    analysis = Analysis(
        id=str(uuid4()),
        status="completed",
        analysis_metadata={"files_completed": 5, "file_count": 5}
    )
    db = AsyncMock()
    db_result = MagicMock()
    db_result.scalar_one_or_none.return_value = analysis
    db.execute.return_value = db_result

    current_user = User(id=str(uuid4()), email="test@test.com", role="developer")
    
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr("app.api.endpoints.scanner.check_analysis_ownership", MagicMock())
        response = await get_scan_status(scan_id=uuid4(), db=db, current_user=current_user)
        
        assert response["success"] is True
        assert _get_progress(response) == 1.0
        assert _get_status(response) == "completed"

@pytest.mark.asyncio
async def test_progress_tracking_failed_scan():
    analysis = Analysis(
        id=str(uuid4()),
        status="failed",
        analysis_metadata={"files_completed": 2, "file_count": 5}
    )
    db = AsyncMock()
    db_result = MagicMock()
    db_result.scalar_one_or_none.return_value = analysis
    db.execute.return_value = db_result

    current_user = User(id=str(uuid4()), email="test@test.com", role="developer")
    
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr("app.api.endpoints.scanner.check_analysis_ownership", MagicMock())
        response = await get_scan_status(scan_id=uuid4(), db=db, current_user=current_user)
        
        assert response["success"] is True
        assert _get_progress(response) == 0.0
        assert _get_status(response) == "failed"

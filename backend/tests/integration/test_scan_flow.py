"""Integration tests for scan flow: upload, status, results."""

import pytest


class TestScanUpload:
    """Tests for file upload and scan initiation."""

    @pytest.mark.asyncio
    async def test_upload_requires_auth(self, client, sample_python_file):
        """Upload without authentication should return 401."""
        response = await client.post(
            "/api/v1/scanner/upload",
            files={"files": ("test.py", sample_python_file, "text/x-python")},
            data={"language": "python"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_upload_rejected_extension(self, client, test_user):
        """Uploading a .exe file should be rejected."""
        response = await client.post(
            "/api/v1/scanner/upload",
            headers={"Authorization": f"Bearer {test_user['token']}"},
            files={"files": ("malware.exe", b"binary data", "application/octet-stream")},
            data={"language": "python"},
        )
        assert response.status_code in (400, 422)


class TestScanStatus:
    """Tests for checking scan status."""

    @pytest.mark.asyncio
    async def test_get_scan_status_unauthenticated(self, client):
        """Getting scan status without auth should return 401."""
        response = await client.get("/api/v1/scanner/nonexistent-id/status")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_scan_status_nonexistent(self, client, test_user):
        """Getting status for a nonexistent scan should return 404."""
        response = await client.get(
            "/api/v1/scanner/00000000-0000-0000-0000-000000000000/status",
            headers={"Authorization": f"Bearer {test_user['token']}"},
        )
        assert response.status_code == 404
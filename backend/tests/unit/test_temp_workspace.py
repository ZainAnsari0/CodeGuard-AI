"""
Unit tests for TempWorkspaceService.
Validates workspace lifecycle: create, write, read, list, cleanup, and staleness.
"""

import os
import tempfile
import time
import pytest

from app.services.temp_workspace import TempWorkspaceService


@pytest.fixture
def workspace_svc(tmp_path):
    """Create a TempWorkspaceService with a temporary base directory."""
    svc = TempWorkspaceService()
    svc._workspace_base = str(tmp_path / "scans")
    return svc


class TestTempWorkspaceService:
    """Tests for TempWorkspaceService."""

    def test_create_workspace(self, workspace_svc):
        """Creating a workspace should return a valid path that exists on disk."""
        workspace_info = workspace_svc.create_workspace("scan-001")
        path = workspace_info["path"]
        assert os.path.isdir(path)
        assert "scan-001" in path

    def test_create_workspace_is_idempotent(self, workspace_svc):
        """Creating a workspace with the same scan_id twice should not error."""
        workspace_info1 = workspace_svc.create_workspace("scan-002")
        workspace_info2 = workspace_svc.create_workspace("scan-002")
        assert workspace_info1["path"] == workspace_info2["path"]

    def test_write_and_read_file(self, workspace_svc):
        """Writing a file and reading it back should return the same content."""
        workspace_svc.create_workspace("scan-003")
        workspace_svc.write_file("scan-003", "test.py", b"print('hello')")
        content = workspace_svc.read_file("scan-003", "test.py")
        assert content == "print('hello')"

    def test_write_file_creates_subdirs(self, workspace_svc):
        """Writing to a nested path should create intermediate directories."""
        workspace_svc.create_workspace("scan-004")
        workspace_svc.write_file("scan-004", "sub/dir/test.py", b"x = 1")
        content = workspace_svc.read_file("scan-004", "sub/dir/test.py")
        assert content == "x = 1"

    def test_read_nonexistent_file_raises(self, workspace_svc):
        """Reading a file that doesn't exist should return None."""
        workspace_svc.create_workspace("scan-005")
        assert workspace_svc.read_file("scan-005", "missing.py") is None

    def test_list_files(self, workspace_svc):
        """list_files should return all files written to the workspace."""
        workspace_svc.create_workspace("scan-006")
        workspace_svc.write_file("scan-006", "a.py", b"a = 1")
        workspace_svc.write_file("scan-006", "b.py", b"b = 2")
        files = workspace_svc.list_files("scan-006")
        assert "a.py" in files
        assert "b.py" in files

    def test_list_files_empty_workspace(self, workspace_svc):
        """An empty workspace should return an empty list."""
        workspace_svc.create_workspace("scan-007")
        files = workspace_svc.list_files("scan-007")
        assert files == []

    def test_cleanup_workspace(self, workspace_svc):
        """Cleaning up a workspace should remove the directory."""
        workspace_info = workspace_svc.create_workspace("scan-008")
        path = workspace_info["path"]
        workspace_svc.write_file("scan-008", "test.py", b"x = 1")
        workspace_svc.cleanup_workspace("scan-008")
        assert not os.path.exists(path)

    def test_cleanup_nonexistent_workspace_no_error(self, workspace_svc):
        """Cleaning up a nonexistent workspace should not raise."""
        workspace_svc.cleanup_workspace("nonexistent-scan")  # Should not raise

    def test_check_available_writable(self, workspace_svc):
        """check_available should return True when base dir is writable."""
        result = workspace_svc.check_available()
        assert result["available"] is True

    def test_check_available_not_writable(self, tmp_path):
        """check_available should return False when base dir is not writable."""
        svc = TempWorkspaceService()
        # Use a path that doesn't exist and can't be created
        svc._workspace_base = "/proc/nonexistent_path_for_test"
        result = svc.check_available()
        assert result["available"] is False

    def test_cleanup_stale_workspaces(self, workspace_svc):
        """Stale workspaces (beyond max age) should be cleaned up."""
        workspace_info = workspace_svc.create_workspace("stale-scan")
        path = workspace_info["path"]
        workspace_svc.write_file("stale-scan", "test.py", b"x = 1")

        # Make the workspace directory appear old by modifying mtime
        from app.services.temp_workspace import _MAX_WORKSPACE_AGE
        max_age = _MAX_WORKSPACE_AGE
        old_time = time.time() - max_age - 100
        os.utime(path, (old_time, old_time))

        workspace_svc.cleanup_stale_workspaces()
        assert not os.path.exists(path)

    def test_cleanup_stale_preserves_recent(self, workspace_svc):
        """Recent workspaces should not be cleaned up."""
        workspace_info = workspace_svc.create_workspace("recent-scan")
        path = workspace_info["path"]
        workspace_svc.write_file("recent-scan", "test.py", b"x = 1")

        workspace_svc.cleanup_stale_workspaces()
        assert os.path.exists(path)
"""CodeGuard AI - Temporary Scan Workspace Service

Manages ephemeral scan workspaces for static code analysis.

Instead of Docker containers, scans run in isolated temporary directories.
Each scan gets its own workspace under /tmp/scans/{scan_id}/, which is
automatically cleaned up after the scan completes.

Security Model:
  - Uploaded code is NEVER executed, interpreted, or compiled.
  - Code is only PARSED (AST/tokenized) for static analysis.
  - Workspaces are deleted immediately after scan completion.
  - Only vulnerability metadata is persisted to the database.

Privacy Model:
  - Source code exists only in the temporary workspace during scan.
  - Workspaces are auto-deleted after scan completion or timeout.
  - No source code is stored permanently in the database.
  - Only findings metadata (vulnerability type, severity, line numbers, etc.)
    is persisted.
"""

import logging
import os
import shutil
import tempfile
import time
from typing import Dict, Any, Optional, List

from app.core.config import settings

logger = logging.getLogger(__name__)

# Base directory for all scan workspaces
_WORKSPACE_BASE = getattr(settings, "UPLOAD_DIR", "/tmp/codeguard_uploads")

# Maximum workspace age in seconds before forced cleanup (1 hour)
_MAX_WORKSPACE_AGE = 3600

# Maximum number of concurrent workspaces
_MAX_CONCURRENT_WORKSPACES = getattr(settings, "MAX_CONCURRENT_SCANS", 5)


class TempWorkspaceService:
    """Manages ephemeral temporary scan workspaces.

    Each scan gets an isolated directory under the configured upload path.
    Workspaces are created before a scan and deleted after completion.
    This replaces the previous Docker container-based isolation model.

    Since CodeGuard AI performs **static analysis only** — code is parsed
    and analyzed via AST/tokenization, never executed — container-level
    isolation is not required. Filesystem-level workspace isolation provides
    sufficient separation between concurrent scans.
    """

    def __init__(self):
        self._workspace_base = _WORKSPACE_BASE
        self._active_workspaces: Dict[str, Dict[str, Any]] = {}
        self._ensure_base_dir()

    def _ensure_base_dir(self) -> None:
        """Ensure the base workspace directory exists with proper permissions.

        Falls back to a user-writable directory if the configured path
        is not writable (e.g., owned by root from a previous run).
        """
        try:
            os.makedirs(self._workspace_base, exist_ok=True)
            # Test that we can actually write to it
            test_file = os.path.join(self._workspace_base, ".write_test")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            try:
                os.chmod(self._workspace_base, 0o777)
            except OSError:
                pass  # May not have permission in restricted environments
        except (OSError, PermissionError) as e:
            logger.warning(f"Upload dir {self._workspace_base} not writable ({e}), falling back to user cache")
            self._workspace_base = os.path.join(os.path.expanduser("~"), ".cache", "codeguard_uploads")
            os.makedirs(self._workspace_base, exist_ok=True)

    def create_workspace(self, scan_id: str) -> Dict[str, Any]:
        """Create a new temporary workspace for a scan.

        Args:
            scan_id: Unique identifier for the scan.

        Returns:
            Dict with workspace path and metadata.

        Raises:
            FileException: If workspace cannot be created.
        """
        workspace_path = os.path.join(self._workspace_base, scan_id)

        if os.path.exists(workspace_path):
            logger.warning(f"Workspace already exists for scan {scan_id}, cleaning up")
            self.cleanup_workspace(scan_id)

        os.makedirs(workspace_path, exist_ok=True)

        workspace_info = {
            "scan_id": scan_id,
            "path": workspace_path,
            "created_at": time.time(),
            "status": "active",
        }

        self._active_workspaces[scan_id] = workspace_info
        logger.info(f"Created workspace for scan {scan_id} at {workspace_path}")

        return workspace_info

    def get_workspace_path(self, scan_id: str) -> Optional[str]:
        """Get the filesystem path for a scan's workspace.

        Args:
            scan_id: Unique identifier for the scan.

        Returns:
            Workspace path string, or None if workspace doesn't exist.
        """
        workspace_path = os.path.join(self._workspace_base, scan_id)
        if os.path.exists(workspace_path):
            return workspace_path
        return None

    def cleanup_workspace(self, scan_id: str) -> bool:
        """Delete a scan's workspace and all its contents.

        This removes all uploaded source code files from disk.
        Only the findings metadata persisted in the database remains.

        Args:
            scan_id: Unique identifier for the scan.

        Returns:
            True if cleanup succeeded, False otherwise.
        """
        workspace_path = os.path.join(self._workspace_base, scan_id)

        try:
            if os.path.isdir(workspace_path):
                shutil.rmtree(workspace_path)
                logger.info(f"Cleaned up workspace for scan {scan_id}")
            else:
                logger.debug(f"Workspace for scan {scan_id} already removed")

            self._active_workspaces.pop(scan_id, None)
            return True

        except Exception as e:
            logger.error(f"Failed to cleanup workspace for scan {scan_id}: {e}")
            return False

    def write_file(self, scan_id: str, filename: str, content: bytes) -> str:
        """Write a file to a scan's workspace.

        Args:
            scan_id: Unique identifier for the scan.
            filename: Name of the file to write.
            content: File content as bytes.

        Returns:
            Full path to the written file.

        Raises:
            FileNotFoundError: If workspace doesn't exist.
        """
        workspace_path = self.get_workspace_path(scan_id)
        if not workspace_path:
            raise FileNotFoundError(f"No workspace found for scan {scan_id}")

        file_path = os.path.join(workspace_path, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "wb") as f:
            f.write(content)

        logger.debug(f"Wrote file {filename} to workspace for scan {scan_id}")
        return file_path

    def read_file(self, scan_id: str, filename: str) -> Optional[str]:
        """Read a file from a scan's workspace.

        Args:
            scan_id: Unique identifier for the scan.
            filename: Name of the file to read.

        Returns:
            File content as string, or None if not found.
        """
        workspace_path = self.get_workspace_path(scan_id)
        if not workspace_path:
            return None

        file_path = os.path.join(workspace_path, filename)
        if not os.path.exists(file_path):
            return None

        with open(file_path, "r", errors="replace") as f:
            return f.read()

    def list_files(self, scan_id: str) -> List[str]:
        """List all files in a scan's workspace.

        Args:
            scan_id: Unique identifier for the scan.

        Returns:
            List of file paths relative to the workspace root.
        """
        workspace_path = self.get_workspace_path(scan_id)
        if not workspace_path:
            return []

        files = []
        for root, _, filenames in os.walk(workspace_path):
            for filename in filenames:
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, workspace_path)
                files.append(rel_path)

        return files

    def get_active_workspace_count(self) -> int:
        """Return the number of currently active workspaces."""
        return len(self._active_workspaces)

    def get_workspace_info(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata about a scan's workspace."""
        return self._active_workspaces.get(scan_id)

    def cleanup_stale_workspaces(self) -> int:
        """Remove workspaces older than the maximum age.

        This is a safety net in case cleanup_workspace wasn't called
        (e.g., due to a crash). Runs periodically or on startup.

        Returns:
            Number of stale workspaces cleaned up.
        """
        cleaned = 0
        now = time.time()

        # Clean tracked workspaces
        stale_ids = [
            scan_id for scan_id, info in self._active_workspaces.items()
            if now - info.get("created_at", 0) > _MAX_WORKSPACE_AGE
        ]
        for scan_id in stale_ids:
            if self.cleanup_workspace(scan_id):
                cleaned += 1

        # Also clean up orphaned directories in the base path
        try:
            for entry in os.listdir(self._workspace_base):
                entry_path = os.path.join(self._workspace_base, entry)
                if os.path.isdir(entry_path):
                    try:
                        dir_age = now - os.path.getmtime(entry_path)
                        if dir_age > _MAX_WORKSPACE_AGE:
                            shutil.rmtree(entry_path)
                            cleaned += 1
                            logger.info(f"Cleaned up stale workspace directory: {entry}")
                    except OSError:
                        pass
        except OSError:
            pass

        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} stale workspace(s)")

        return cleaned

    def check_available(self) -> Dict[str, Any]:
        """Check if the workspace service is available and healthy.

        Returns:
            Dict with availability status and configuration info.
        """
        try:
            # Check base directory is writable
            test_path = os.path.join(self._workspace_base, ".health_check")
            os.makedirs(self._workspace_base, exist_ok=True)
            with open(test_path, "w") as f:
                f.write("ok")
            os.remove(test_path)

            return {
                "available": True,
                "workspace_base": self._workspace_base,
                "active_workspaces": len(self._active_workspaces),
                "max_concurrent": _MAX_CONCURRENT_WORKSPACES,
                "max_age_seconds": _MAX_WORKSPACE_AGE,
                "error": None,
            }
        except Exception as e:
            logger.error(f"Workspace health check failed: {e}")
            return {
                "available": False,
                "workspace_base": self._workspace_base,
                "active_workspaces": len(self._active_workspaces),
                "max_concurrent": _MAX_CONCURRENT_WORKSPACES,
                "max_age_seconds": _MAX_WORKSPACE_AGE,
                "error": str(e),
            }


# Singleton instance
workspace_service = TempWorkspaceService()
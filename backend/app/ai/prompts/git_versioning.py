"""
CodeGuard AI - Git-based Prompt Versioning
Tracks prompt template changes through git history, enabling version
pinning, diffs, and rollback of prompt templates.
"""

import logging
import subprocess
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

TEMPLATES_REL_PATH = "backend/app/ai/prompts/templates"


class PromptVersionManager:
    """Manages prompt template versions using git history."""

    def __init__(self, repo_root: Optional[str] = None):
        self.repo_root = repo_root or self._find_repo_root()
        self._validate_git_repo()

    def _find_repo_root(self) -> str:
        """Walk up from CWD to find git repo root."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        import os
        return os.getcwd()

    def _validate_git_repo(self) -> None:
        """Raise if not in a git repo."""
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=self.repo_root, capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Not a git repository: {self.repo_root}. "
                "Initialize git to enable prompt versioning."
            )

    def _run_git(self, *args: str) -> str:
        """Run a git command and return stdout."""
        result = subprocess.run(
            ["git", *args],
            cwd=self.repo_root, capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError(f"git {args[0]} failed: {result.stderr.strip()}")
        return result.stdout.strip()

    def _template_path(self, template_name: str) -> str:
        """Get the repo-relative path for a template."""
        return f"{TEMPLATES_REL_PATH}/{template_name}.j2"

    def commit_version(self, template_name: str, message: Optional[str] = None) -> str:
        """Stage and commit a template file, return the commit hash."""
        rel_path = self._template_path(template_name)
        msg = message or f"Update prompt template: {template_name}"

        self._run_git("add", rel_path)
        self._run_git("commit", "-m", msg, "--no-verify")
        return self._run_git("rev-parse", "HEAD")

    def tag_version(self, template_name: str, version: str, message: Optional[str] = None) -> str:
        """Create a git tag for a specific template version."""
        tag = f"prompt/{template_name}/{version}"
        msg = message or f"Prompt template {template_name} v{version}"
        self._run_git("tag", "-a", tag, "-m", msg)
        return tag

    def get_version(self, template_name: str, version: Optional[str] = None) -> str:
        """Get template content at a specific version.

        Args:
            template_name: Template name without .j2 extension
            version: Tag name, commit hash, or None for current

        Returns:
            Template source string at the specified version
        """
        rel_path = self._template_path(template_name)

        if version is None:
            return self._run_git("show", f"HEAD:{rel_path}")

        # Try as a tag first
        tag = f"prompt/{template_name}/{version}"
        try:
            return self._run_git("show", f"{tag}:{rel_path}")
        except RuntimeError:
            pass

        # Fall back to treating version as a commit hash
        return self._run_git("show", f"{version}:{rel_path}")

    def diff_versions(self, template_name: str, v1: str, v2: str) -> str:
        """Return git diff between two versions of a template.

        Args:
            v1: First version (tag or commit hash)
            v2: Second version (tag or commit hash)
        """
        def resolve(ref: str) -> str:
            tag = f"prompt/{template_name}/{ref}"
            try:
                self._run_git("rev-parse", tag)
                return tag
            except RuntimeError:
                return ref

        return self._run_git("diff", resolve(v1), resolve(v2), "--", self._template_path(template_name))

    def list_versions(self, template_name: str) -> List[Dict[str, Any]]:
        """Return git log entries for a template file."""
        rel_path = self._template_path(template_name)
        log_format = "%H|%ai|%s"
        output = self._run_git("log", f"--format={log_format}", "--", rel_path)

        if not output:
            return []

        versions = []
        for line in output.split("\n"):
            if not line.strip():
                continue
            parts = line.split("|", 2)
            if len(parts) == 3:
                versions.append({
                    "commit": parts[0],
                    "date": parts[1],
                    "message": parts[2],
                })
        return versions

    def get_current_version_info(self, template_name: str) -> Dict[str, Any]:
        """Get current version metadata including latest commit and tags."""
        rel_path = self._template_path(template_name)

        try:
            latest_commit = self._run_git("log", "-1", f"--format=%H|%ai|%s", "--", rel_path)
        except RuntimeError:
            return {"name": template_name, "exists": False, "versions": []}

        parts = latest_commit.split("|", 2)
        commit_hash = parts[0] if len(parts) >= 1 else ""
        commit_date = parts[1] if len(parts) >= 2 else ""
        commit_msg = parts[2] if len(parts) >= 3 else ""

        # Find tags for this template
        tag_prefix = f"prompt/{template_name}/"
        try:
            all_tags = self._run_git("tag", "-l", f"{tag_prefix}*")
        except RuntimeError:
            all_tags = ""

        tags = [t.replace(tag_prefix, "") for t in all_tags.split("\n") if t.strip()]

        return {
            "name": template_name,
            "exists": True,
            "latest_commit": commit_hash,
            "latest_date": commit_date,
            "latest_message": commit_msg,
            "versions": tags,
            "current_tag": tags[-1] if tags else None,
        }
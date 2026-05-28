"""
CodeGuard AI - Prompt Version Manager
Manages Jinja2-based prompt templates for LLM interactions.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from jinja2 import Environment, FileSystemLoader, TemplateError
from jinja2.sandbox import SandboxedEnvironment

logger = logging.getLogger(__name__)

# Template directory
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")


class PromptManager:
    """Manages prompt templates using Jinja2 with version tracking."""

    def __init__(self, templates_dir: Optional[str] = None):
        self.templates_dir = templates_dir or TEMPLATES_DIR
        self._env = SandboxedEnvironment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def load_template(self, template_name: str) -> str:
        """Load a raw template string by name.

        Args:
            template_name: Name of the template (without .j2 extension)

        Returns:
            Raw template string
        """
        try:
            template = self._env.get_template(f"{template_name}.j2")
            return template.source
        except TemplateError as e:
            logger.error(f"Failed to load template '{template_name}': {e}")
            raise

    def render_template(self, template_name: str, variables: Dict[str, Any], version: Optional[str] = None) -> str:
        """Render a template with the given variables, optionally pinning to a version.

        Args:
            template_name: Name of the template (without .j2 extension)
            variables: Dict of template variables
            version: Optional version tag or commit hash to pin the template to.
                      If None, uses the current file on disk.

        Returns:
            Rendered template string
        """
        try:
            if version:
                from app.ai.prompts.git_versioning import PromptVersionManager
                version_manager = PromptVersionManager()
                template_source = version_manager.get_version(template_name, version)
                template = self._env.from_string(template_source)
                return template.render(**variables)

            template = self._env.get_template(f"{template_name}.j2")
            return template.render(**variables)
        except TemplateError as e:
            logger.error(f"Failed to render template '{template_name}': {e}")
            raise

    def list_templates(self) -> List[str]:
        """List all available prompt template names."""
        try:
            templates = self._env.list_templates()
            return [t.replace(".j2", "") for t in templates if t.endswith(".j2")]
        except Exception as e:
            logger.error(f"Failed to list templates: {e}")
            return []

    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """Get metadata about a template.

        Args:
            template_name: Name of the template

        Returns:
            Dict with template info including version, last modified, etc.
        """
        from app.ai.prompts.versions import PROMPT_VERSIONS

        template_path = os.path.join(self.templates_dir, f"{template_name}.j2")

        if not os.path.exists(template_path):
            return {"name": template_name, "exists": False}

        stat = os.stat(template_path)
        version_info = PROMPT_VERSIONS.get(template_name, {})

        return {
            "name": template_name,
            "exists": True,
            "path": template_path,
            "size_bytes": stat.st_size,
            "last_modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            "current_version": version_info.get("current", "unknown"),
            "description": version_info.get("versions", {}).get(
                version_info.get("current", "1.0.0"), {}
            ).get("description", ""),
        }
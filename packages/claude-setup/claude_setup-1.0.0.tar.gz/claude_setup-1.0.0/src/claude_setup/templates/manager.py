"""Template manager for Claude Code configurations."""

import json
import shutil
import tarfile
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import yaml


@dataclass
class Template:
    """Represents a Claude Code template."""

    name: str
    description: str
    source: str
    path: Optional[Path] = None
    remote_url: Optional[str] = None
    tags: list[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class TemplateManager:
    """Manages Claude Code configuration templates."""

    def __init__(self):
        """Initialize template manager."""
        # Get package directory
        package_dir = Path(__file__).parent.parent
        self.builtin_templates_dir = package_dir / "templates" / "builtin"

        # User templates directory
        self.user_templates_dir = Path.home() / ".claude-setup" / "templates"
        self.user_templates_dir.mkdir(parents=True, exist_ok=True)

        # Template cache directory
        self.cache_dir = Path.home() / ".claude-setup" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def list_templates(self) -> list[Template]:
        """List all available templates.

        Returns:
            List of available templates
        """
        templates = []

        # Built-in templates
        builtin_templates = {
            "generic": "Universal template for any project type",
            "web": "Web application (React, Vue, Next.js)",
            "api": "Backend API (FastAPI, Express, Django)",
            "cli": "Command-line tools and libraries",
            "data-science": "Data science and ML projects",
        }

        for name, description in builtin_templates.items():
            template_dir = self.builtin_templates_dir / name
            if template_dir.exists():
                templates.append(
                    Template(
                        name=name,
                        description=description,
                        source="built-in",
                        path=template_dir,
                        tags=self._get_template_tags(name),
                    )
                )

        # User templates
        for template_dir in self.user_templates_dir.glob("*/"):
            if template_dir.is_dir():
                meta = self._load_template_meta(template_dir)
                if meta:
                    templates.append(
                        Template(
                            name=template_dir.name,
                            description=meta.get("description", "User template"),
                            source="user",
                            path=template_dir,
                            tags=meta.get("tags", []),
                        )
                    )

        # Remote templates from registry
        remote_templates = self._fetch_remote_templates()
        templates.extend(remote_templates)

        return templates

    def get_template(self, name: str) -> dict[str, Any]:
        """Get template data by name.

        Args:
            name: Template name

        Returns:
            Template configuration data

        Raises:
            ValueError: If template not found
        """
        # Check built-in templates
        builtin_path = self.builtin_templates_dir / name
        if builtin_path.exists():
            return self._load_template_data(builtin_path)

        # Check user templates
        user_path = self.user_templates_dir / name
        if user_path.exists():
            return self._load_template_data(user_path)

        # Check if it's a remote template
        if "/" in name:  # GitHub format: owner/repo
            return self._fetch_github_template(name)

        # Generate template on-the-fly for common types
        if name in ["react", "vue", "angular", "fastapi", "django", "flask"]:
            return self._generate_framework_template(name)

        raise ValueError(f"Template '{name}' not found")

    def add_template(self, source: str, name: Optional[str] = None) -> str:
        """Add a new template from source.

        Args:
            source: GitHub URL, file path, or archive
            name: Optional template name

        Returns:
            Name of added template
        """
        if source.startswith(("http://", "https://")):
            return self._add_remote_template(source, name)
        elif source.endswith((".zip", ".tar.gz", ".tar")):
            return self._add_archive_template(source, name)
        else:
            return self._add_local_template(Path(source), name)

    def remove_template(self, name: str) -> bool:
        """Remove a user template.

        Args:
            name: Template name

        Returns:
            True if removed, False if not found or built-in
        """
        user_path = self.user_templates_dir / name
        if user_path.exists():
            shutil.rmtree(user_path)
            return True
        return False

    def export_template(self, project_path: Path, name: str) -> str:
        """Export current project configuration as a template.

        Args:
            project_path: Path to project
            name: Template name

        Returns:
            Path to exported template
        """
        template_dir = self.user_templates_dir / name
        template_dir.mkdir(exist_ok=True)

        # Copy .claude directory contents
        claude_dir = project_path / ".claude"
        if claude_dir.exists():
            for item in claude_dir.iterdir():
                if item.is_file():
                    shutil.copy2(item, template_dir)
                elif item.is_dir() and item.name not in [".git", "__pycache__"]:
                    shutil.copytree(item, template_dir / item.name, dirs_exist_ok=True)

        # Copy CLAUDE.md
        claude_md = project_path / "CLAUDE.md"
        if claude_md.exists():
            shutil.copy2(claude_md, template_dir)

        # Create template metadata
        meta = {
            "name": name,
            "description": f"Exported from {project_path.name}",
            "version": "1.0.0",
            "tags": ["exported", "custom"],
        }

        meta_file = template_dir / "template.yaml"
        with open(meta_file, "w") as f:
            yaml.dump(meta, f)

        return str(template_dir)

    # Private helper methods

    def _load_template_meta(self, path: Path) -> Optional[dict[str, Any]]:
        """Load template metadata."""
        meta_file = path / "template.yaml"
        if not meta_file.exists():
            meta_file = path / "template.json"

        if meta_file.exists():
            with open(meta_file) as f:
                if meta_file.suffix == ".yaml":
                    return yaml.safe_load(f)
                else:
                    return json.load(f)

        return None

    def _load_template_data(self, path: Path) -> dict[str, Any]:
        """Load complete template data."""
        data = {}

        # Load settings
        settings_file = path / "settings.json"
        if settings_file.exists():
            with open(settings_file) as f:
                data["settings"] = json.load(f)

        # Load CLAUDE.md
        claude_md = path / "CLAUDE.md"
        if claude_md.exists():
            data["claude_md"] = claude_md.read_text()

        # Load commands
        commands_dir = path / "commands"
        if commands_dir.exists():
            data["commands"] = {}
            for cmd_file in commands_dir.glob("*.md"):
                data["commands"][cmd_file.stem] = cmd_file.read_text()

        # Load agents
        agents_dir = path / "agents"
        if agents_dir.exists():
            data["agents"] = {}
            for agent_file in agents_dir.glob("*.md"):
                data["agents"][agent_file.stem] = agent_file.read_text()

        # Load hooks
        hooks_file = path / "hooks.json"
        if hooks_file.exists():
            with open(hooks_file) as f:
                data["hooks"] = json.load(f)

        # Load MCP servers
        mcp_file = path / "mcp.json"
        if mcp_file.exists():
            with open(mcp_file) as f:
                data["mcp_servers"] = json.load(f)

        return data

    def _add_remote_template(self, url: str, name: Optional[str]) -> str:
        """Add template from remote URL."""
        # Parse GitHub URL
        if "github.com" in url:
            parts = url.replace("https://", "").replace("http://", "").split("/")
            if len(parts) >= 3:
                owner = parts[1]
                repo = parts[2].replace(".git", "")
                return self._fetch_github_template(f"{owner}/{repo}", save=True, name=name)

        raise NotImplementedError("Only GitHub templates are currently supported")

    def _fetch_github_template(
        self, repo: str, save: bool = False, name: Optional[str] = None
    ) -> Any:
        """Fetch template from GitHub."""
        # This would use GitHub API to fetch template
        # For now, return a placeholder
        raise NotImplementedError(f"GitHub template fetching for {repo} coming soon")

    def _add_archive_template(self, archive_path: str, name: Optional[str]) -> str:
        """Add template from archive file."""
        archive = Path(archive_path)
        if not archive.exists():
            raise ValueError(f"Archive {archive_path} not found")

        template_name = name or archive.stem
        dest = self.user_templates_dir / template_name

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            if archive.suffix == ".zip":
                with zipfile.ZipFile(archive) as zf:
                    zf.extractall(tmppath)
            elif archive.suffix in [".tar", ".gz"]:
                with tarfile.open(archive) as tf:
                    tf.extractall(tmppath)

            # Find template root (directory with settings.json or CLAUDE.md)
            template_root = self._find_template_root(tmppath)
            if template_root:
                shutil.copytree(template_root, dest, dirs_exist_ok=True)
            else:
                raise ValueError("No valid template found in archive")

        return template_name

    def _add_local_template(self, source: Path, name: Optional[str]) -> str:
        """Add template from local path."""
        if not source.exists():
            raise ValueError(f"Source path {source} does not exist")

        template_name = name or source.name
        dest = self.user_templates_dir / template_name

        if dest.exists():
            raise ValueError(f"Template '{template_name}' already exists")

        shutil.copytree(source, dest)
        return template_name

    def _find_template_root(self, path: Path) -> Optional[Path]:
        """Find template root directory in extracted archive."""
        # Check if current directory is template root
        if (path / "settings.json").exists() or (path / "CLAUDE.md").exists():
            return path

        # Check subdirectories
        for subdir in path.iterdir():
            if subdir.is_dir():
                if (subdir / "settings.json").exists() or (subdir / "CLAUDE.md").exists():
                    return subdir

        return None

    def _fetch_remote_templates(self) -> list[Template]:
        """Fetch remote templates from registry."""
        # This would fetch from a central registry
        # For now, return empty list
        return []

    def _get_template_tags(self, name: str) -> list[str]:
        """Get tags for a template."""
        tag_map = {
            "generic": ["universal", "starter"],
            "web": ["frontend", "javascript", "react", "vue"],
            "api": ["backend", "rest", "graphql"],
            "cli": ["terminal", "command-line"],
            "data-science": ["ml", "ai", "jupyter", "pandas"],
        }
        return tag_map.get(name, [])

    def _generate_framework_template(self, framework: str) -> dict[str, Any]:
        """Generate a template for a specific framework."""
        # This would generate framework-specific templates
        # For now, return a basic template
        return self._load_template_data(self.builtin_templates_dir / "generic")

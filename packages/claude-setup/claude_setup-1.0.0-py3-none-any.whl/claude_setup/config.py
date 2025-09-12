"""Configuration management for Claude Setup."""

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class ProjectType(str, Enum):
    """Project type enumeration."""

    WEB_APP = "Web Application"
    BACKEND_API = "Backend API"
    CLI_TOOL = "CLI Tool"
    LIBRARY = "Library"
    DATA_SCIENCE = "Data Science"
    MOBILE_APP = "Mobile App"
    DOCUMENTATION = "Documentation"
    OTHER = "Other"


class Language(str, Enum):
    """Programming language enumeration."""

    PYTHON = "Python"
    JAVASCRIPT_TYPESCRIPT = "JavaScript/TypeScript"
    GO = "Go"
    RUST = "Rust"
    JAVA = "Java"
    CPP = "C/C++"
    OTHER = "Other"


@dataclass
class ProjectConfig:
    """Project configuration data."""

    project_type: str = "Other"
    language: str = "Other"
    frameworks: list[str] = field(default_factory=list)
    needs: list[str] = field(default_factory=list)
    team_size: str = "Solo"
    tools: list[str] = field(default_factory=list)
    model: str = "claude-opus-4-1-20250805"
    custom_agents: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def generate_claude_config(self) -> str:
        """Generate Claude configuration JSON."""
        config = {
            "project": {
                "type": self.project_type,
                "language": self.language,
                "frameworks": self.frameworks,
                "team_size": self.team_size,
                "tools": self.tools,
            },
            "requirements": self.needs,
            "model": self.model,
            "custom_agents": self.custom_agents,
            "generated_by": "claude-setup",
            "version": "1.0.0",
        }
        return json.dumps(config, indent=2)


@dataclass
class ClaudeConfig:
    """Complete Claude Code configuration."""

    settings: dict[str, Any] = field(default_factory=dict)
    claude_md: str = ""
    commands: dict[str, str] = field(default_factory=dict)
    agents: dict[str, str] = field(default_factory=dict)
    hooks: Optional[dict[str, Any]] = None
    mcp_servers: Optional[list[dict[str, Any]]] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "settings": self.settings,
            "claude_md": self.claude_md,
            "commands": self.commands,
            "agents": self.agents,
            "hooks": self.hooks or {},
            "mcp_servers": self.mcp_servers or [],
        }


def load_config(path: Path) -> Optional[ProjectConfig]:
    """Load project configuration from file.

    Args:
        path: Path to project root

    Returns:
        ProjectConfig object or None if not found
    """
    config_file = path / ".claude" / "project.json"

    if not config_file.exists():
        # Try to reconstruct from existing files
        return load_config_from_claude_dir(path)

    try:
        with open(config_file) as f:
            data = json.load(f)
        return ProjectConfig(**data)
    except Exception:
        return None


def load_config_from_claude_dir(path: Path) -> Optional[ProjectConfig]:
    """Load configuration from .claude directory structure.

    Args:
        path: Path to project root

    Returns:
        ProjectConfig object or None if not found
    """
    claude_dir = path / ".claude"
    if not claude_dir.exists():
        return None

    config = ProjectConfig()

    # Try to load from settings.json
    settings_file = claude_dir / "settings.json"
    if settings_file.exists():
        try:
            with open(settings_file) as f:
                settings = json.load(f)
                if "env" in settings:
                    env = settings["env"]
                    config.project_type = env.get("PROJECT_TYPE", "Other")
                    config.language = env.get("PRIMARY_LANGUAGE", "Other")
                if "model" in settings:
                    config.model = settings["model"]
        except Exception:
            pass

    return config


def save_config(path: Path, config: ProjectConfig) -> None:
    """Save project configuration to file.

    Args:
        path: Path to project root
        config: ProjectConfig object to save
    """
    config_file = path / ".claude" / "project.json"
    config_file.parent.mkdir(parents=True, exist_ok=True)

    with open(config_file, "w") as f:
        json.dump(asdict(config), f, indent=2)


def merge_configs(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Merge two configuration dictionaries.

    Args:
        base: Base configuration
        overlay: Configuration to overlay on top

    Returns:
        Merged configuration
    """
    result = base.copy()

    for key, value in overlay.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        elif key in result and isinstance(result[key], list) and isinstance(value, list):
            # Merge lists without duplicates
            result[key] = list(set(result[key] + value))
        else:
            result[key] = value

    return result

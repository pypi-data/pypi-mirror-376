"""Configuration validation utilities."""

import json
from pathlib import Path

import yaml


class ConfigValidator:
    """Validates Claude Code configurations."""

    def __init__(self, project_path: Path):
        """Initialize validator with project path.

        Args:
            project_path: Path to project root
        """
        self.project_path = Path(project_path)
        self.claude_dir = self.project_path / ".claude"

    def validate(self) -> list[str]:
        """Validate the complete configuration.

        Returns:
            List of validation issues (empty if valid)
        """
        issues = []

        # Check directory structure
        structure_issues = self._validate_structure()
        issues.extend(structure_issues)

        # Validate settings.json
        settings_issues = self._validate_settings()
        issues.extend(settings_issues)

        # Validate CLAUDE.md
        claude_md_issues = self._validate_claude_md()
        issues.extend(claude_md_issues)

        # Validate commands
        command_issues = self._validate_commands()
        issues.extend(command_issues)

        # Validate agents
        agent_issues = self._validate_agents()
        issues.extend(agent_issues)

        # Validate hooks
        hook_issues = self._validate_hooks()
        issues.extend(hook_issues)

        # Validate MCP servers
        mcp_issues = self._validate_mcp_servers()
        issues.extend(mcp_issues)

        return issues

    def _validate_structure(self) -> list[str]:
        """Validate directory structure."""
        issues = []

        if not self.claude_dir.exists():
            issues.append("Missing .claude directory")
            return issues  # Can't validate further without directory

        required_dirs = ["commands", "agents"]
        for dir_name in required_dirs:
            if not (self.claude_dir / dir_name).exists():
                issues.append(f"Missing .claude/{dir_name} directory")

        return issues

    def _validate_settings(self) -> list[str]:
        """Validate settings.json file."""
        issues = []
        settings_file = self.claude_dir / "settings.json"

        if not settings_file.exists():
            issues.append("Missing settings.json")
            return issues

        try:
            with open(settings_file) as f:
                settings = json.load(f)
        except json.JSONDecodeError as e:
            issues.append(f"Invalid JSON in settings.json: {e}")
            return issues
        except Exception as e:
            issues.append(f"Error reading settings.json: {e}")
            return issues

        # Check required fields
        required_fields = ["model", "permissions"]
        for field in required_fields:
            if field not in settings:
                issues.append(f"Missing required field '{field}' in settings.json")

        # Validate model
        if "model" in settings:
            valid_models = [
                "claude-opus-4-1-20250805",
                "claude-3-5-sonnet-20241022",
                "claude-3-5-haiku-20241022",
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307",
            ]
            if settings["model"] not in valid_models:
                issues.append(f"Invalid model '{settings['model']}' in settings.json")

        # Validate permissions
        if "permissions" in settings:
            perms = settings["permissions"]
            if not isinstance(perms, dict):
                issues.append("Permissions must be a dictionary")
            else:
                if "allow" in perms and not isinstance(perms["allow"], list):
                    issues.append("Permissions 'allow' must be a list")
                if "deny" in perms and not isinstance(perms["deny"], list):
                    issues.append("Permissions 'deny' must be a list")

                # Check for dangerous permissions
                if "allow" in perms:
                    dangerous = [
                        "Delete(**)",
                        "Bash(rm:*)",
                        "Bash(sudo:*)",
                        "Read(.env)",
                        "Read(**/*.key)",
                        "Read(**/*.pem)",
                    ]
                    for perm in perms["allow"]:
                        if any(d in perm for d in dangerous):
                            issues.append(f"Dangerous permission in allow list: {perm}")

        return issues

    def _validate_claude_md(self) -> list[str]:
        """Validate CLAUDE.md file."""
        issues = []
        claude_md = self.project_path / "CLAUDE.md"

        if not claude_md.exists():
            issues.append("Missing CLAUDE.md file")
            return issues

        try:
            content = claude_md.read_text()

            # Check minimum content
            if len(content) < 100:
                issues.append("CLAUDE.md seems too short (less than 100 characters)")

            # Check for required sections
            recommended_sections = ["## Project", "## Development", "## Commands", "## Quick Start"]

            missing_sections = []
            for section in recommended_sections:
                if section.lower() not in content.lower():
                    missing_sections.append(section)

            if len(missing_sections) > 2:
                issues.append(
                    f"CLAUDE.md missing recommended sections: {', '.join(missing_sections[:2])}"
                )

        except Exception as e:
            issues.append(f"Error reading CLAUDE.md: {e}")

        return issues

    def _validate_commands(self) -> list[str]:
        """Validate command files."""
        issues = []
        commands_dir = self.claude_dir / "commands"

        if not commands_dir.exists():
            return []  # Already checked in structure validation

        command_files = list(commands_dir.glob("*.md"))

        for cmd_file in command_files:
            try:
                content = cmd_file.read_text()

                # Check for YAML frontmatter
                if not content.startswith("---"):
                    issues.append(f"Command {cmd_file.name} missing YAML frontmatter")
                    continue

                # Parse frontmatter
                parts = content.split("---", 2)
                if len(parts) < 3:
                    issues.append(f"Command {cmd_file.name} has invalid frontmatter format")
                    continue

                try:
                    frontmatter = yaml.safe_load(parts[1])
                    if "description" not in frontmatter:
                        issues.append(
                            f"Command {cmd_file.name} missing 'description' in frontmatter"
                        )
                except yaml.YAMLError:
                    issues.append(f"Command {cmd_file.name} has invalid YAML frontmatter")

            except Exception as e:
                issues.append(f"Error reading command {cmd_file.name}: {e}")

        return issues

    def _validate_agents(self) -> list[str]:
        """Validate agent files."""
        issues = []
        agents_dir = self.claude_dir / "agents"

        if not agents_dir.exists():
            return []  # Already checked in structure validation

        agent_files = list(agents_dir.glob("*.md"))

        for agent_file in agent_files:
            try:
                content = agent_file.read_text()

                # Check for YAML frontmatter
                if not content.startswith("---"):
                    issues.append(f"Agent {agent_file.name} missing YAML frontmatter")
                    continue

                # Parse frontmatter
                parts = content.split("---", 2)
                if len(parts) < 3:
                    issues.append(f"Agent {agent_file.name} has invalid frontmatter format")
                    continue

                try:
                    frontmatter = yaml.safe_load(parts[1])
                    required_fields = ["name", "description"]
                    for field in required_fields:
                        if field not in frontmatter:
                            issues.append(
                                f"Agent {agent_file.name} missing '{field}' in frontmatter"
                            )
                except yaml.YAMLError:
                    issues.append(f"Agent {agent_file.name} has invalid YAML frontmatter")

            except Exception as e:
                issues.append(f"Error reading agent {agent_file.name}: {e}")

        return issues

    def _validate_hooks(self) -> list[str]:
        """Validate hook configurations."""
        issues = []
        hooks_dir = self.claude_dir / "hooks"

        if not hooks_dir.exists():
            return []  # Hooks are optional

        hook_files = list(hooks_dir.glob("*.json"))

        for hook_file in hook_files:
            try:
                with open(hook_file) as f:
                    hooks = json.load(f)

                # Validate hook structure
                if not isinstance(hooks, (list, dict)):
                    issues.append(f"Hook {hook_file.name} must contain a list or dictionary")

            except json.JSONDecodeError:
                issues.append(f"Hook {hook_file.name} contains invalid JSON")
            except Exception as e:
                issues.append(f"Error reading hook {hook_file.name}: {e}")

        return issues

    def _validate_mcp_servers(self) -> list[str]:
        """Validate MCP server configurations."""
        issues = []
        mcp_config = self.claude_dir / "mcp" / "config.json"

        if not mcp_config.exists():
            return []  # MCP is optional

        try:
            with open(mcp_config) as f:
                config = json.load(f)

            if "mcpServers" not in config:
                issues.append("MCP config missing 'mcpServers' field")
            elif not isinstance(config["mcpServers"], list):
                issues.append("MCP 'mcpServers' must be a list")
            else:
                for i, server in enumerate(config["mcpServers"]):
                    if not isinstance(server, dict):
                        issues.append(f"MCP server {i} must be a dictionary")
                    elif "name" not in server:
                        issues.append(f"MCP server {i} missing 'name' field")

        except json.JSONDecodeError:
            issues.append("MCP config contains invalid JSON")
        except Exception as e:
            issues.append(f"Error reading MCP config: {e}")

        return issues

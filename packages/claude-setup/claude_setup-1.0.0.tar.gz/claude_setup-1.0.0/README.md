# claude-setup

Intelligent scaffolding system for optimal Claude Code configurations.

[![CI](https://github.com/kieranveyl/claude-setup/actions/workflows/ci.yml/badge.svg)](https://github.com/kieranveyl/claude-setup/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/pypi/pyversions/claude-setup.svg)](https://pypi.org/project/claude-setup/)
[![PyPI version](https://badge.fury.io/py/claude-setup.svg)](https://badge.fury.io/py/claude-setup)

## Description

Generate optimal `.claude` configurations for any project by automatically detecting your tech stack and project structure. Creates customized settings, commands, agents, and workflows tailored to your specific development needs.

## Installation

### Using uv (Recommended)

```bash
uvx claude-setup init
```

### Using pipx

```bash
pipx install claude-setup
```

### Using pip

```bash
pip install claude-setup
```

## Quick Start

Initialize Claude in your project:

```bash
cd your-project
claude-setup init
```

Configure automatically:

```bash
claude-setup configure --auto
```

Or interactively:

```bash
claude-setup configure --interactive
```

## Usage

### Core Commands

```bash
# Initialize new configuration
claude-setup init [--template NAME] [--force]

# Configure project
claude-setup configure [--auto] [--interactive]

# List templates
claude-setup template list

# Apply template
claude-setup template apply <name>

# Check status
claude-setup status [--check] [--validate]

# Export configuration
claude-setup export -o config.json
```

### Self-Configuration

Start Claude and request:

```
"Analyze this project and configure yourself optimally for [your project description]"
```

Claude will generate the perfect configuration using the built-in scaffolding agent.

## Configuration

### Directory Structure

```
.claude/
├── settings.json      # Permissions and model config
├── CLAUDE.md         # Project context
├── commands/         # Custom slash commands
├── agents/           # Specialized AI agents
├── hooks/            # Event automation
└── templates/        # Code templates
```

### settings.json

```json
{
    "model": "claude-opus-4-1-20250805",
    "permissions": {
        "allow": ["Read(**/*.py)", "Bash(pytest:*)"],
        "deny": ["Delete(**)", "Read(.env*)"]
    },
    "env": {
        "PROJECT_TYPE": "python-fastapi"
    }
}
```

## Templates

Available built-in templates:

- **generic** - Universal starting point
- **web** - Frontend applications
- **api** - Backend services
- **cli** - Command-line tools
- **data-science** - ML/Data projects

## Best Practices Runbook

1. Run `claude-setup init` in project root
2. Execute `claude-setup configure --auto` for detection
3. Review `.claude/settings.json` permissions
4. Test with `claude-setup status --validate`
5. Commit `.claude/` and `CLAUDE.md` to git
6. Create project-specific commands in `.claude/commands/`
7. Add specialized agents to `.claude/agents/`
8. Document project context in `CLAUDE.md`
9. Use minimal necessary permissions
10. Update configuration as project evolves

## License

MIT License - see [LICENSE](LICENSE) for details.

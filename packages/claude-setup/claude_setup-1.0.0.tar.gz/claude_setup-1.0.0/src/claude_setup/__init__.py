"""Claude Setup - Intelligent scaffolding for Claude Code configurations.

Generate optimal .claude configurations tailored to your specific project needs.
"""

__version__ = "1.0.0"
__author__ = "Claude Setup Contributors"
__email__ = "hello@claude-setup.dev"

from claude_setup.config import ClaudeConfig, ProjectConfig
from claude_setup.scaffolder import Scaffolder

__all__ = [
    "__version__",
    "Scaffolder",
    "ProjectConfig",
    "ClaudeConfig",
]

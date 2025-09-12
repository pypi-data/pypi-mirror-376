"""CLI interface for claude-setup using Click and Rich."""

import json
import sys
from pathlib import Path
from typing import Optional

import click
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from rich.syntax import Syntax
from rich.table import Table

from claude_setup import __version__
from claude_setup.config import ProjectConfig, load_config
from claude_setup.scaffolder import Scaffolder
from claude_setup.templates.manager import TemplateManager
from claude_setup.utils.detector import ProjectDetector
from claude_setup.utils.validator import ConfigValidator

console = Console()


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="claude-setup")
@click.pass_context
def cli(ctx):
    """Claude Setup - Intelligent scaffolding for Claude Code configurations.

    Create optimized Claude Code setups tailored to your project needs.
    """
    if ctx.invoked_subcommand is None:
        # Show interactive menu if no command specified
        show_interactive_menu()


@cli.command()
@click.option(
    "--path", "-p", type=click.Path(), default=".", help="Path to initialize Claude configuration"
)
@click.option("--force", "-f", is_flag=True, help="Overwrite existing configuration")
@click.option(
    "--template",
    "-t",
    default="auto",
    help="Template to use (auto, generic, web, api, cli, data-science)",
)
@click.option("--no-interactive", is_flag=True, help="Skip interactive prompts")
def init(path: str, force: bool, template: str, no_interactive: bool):
    """Initialize a new Claude Code configuration."""
    project_path = Path(path).resolve()

    # Check for existing configuration
    if (project_path / ".claude").exists() and not force:
        if no_interactive:
            console.print(
                "[red]⚠️  .claude directory already exists! Use --force to overwrite.[/red]"
            )
            sys.exit(1)
        else:
            if not Confirm.ask("[yellow]⚠️  .claude directory exists. Overwrite?[/yellow]"):
                console.print("[yellow]Aborted.[/yellow]")
                return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task("Initializing Claude configuration...", total=5)

        scaffolder = Scaffolder(project_path)

        # Create directory structure
        progress.update(task, advance=1, description="Creating directory structure...")
        scaffolder.create_structure()

        # Auto-detect if template is "auto"
        if template == "auto":
            progress.update(task, advance=1, description="Auto-detecting project type...")
            detector = ProjectDetector(project_path)
            detected_config = detector.detect()
            template = detected_config.get("project_type", "generic").lower().replace(" ", "-")
            console.print(f"[cyan]🔍 Detected project type: {template}[/cyan]")
        else:
            progress.update(task, advance=1)

        # Apply template
        progress.update(task, advance=1, description=f"Applying {template} template...")
        try:
            scaffolder.apply_template(template)
        except ValueError as e:
            console.print(f"[red]❌ {e}. Using generic template.[/red]")
            scaffolder.apply_template("generic")

        # Generate base configuration
        progress.update(task, advance=1, description="Generating configuration...")
        scaffolder.generate_base_config()

        # Finalize
        progress.update(task, advance=1, description="Complete!")

    # Show success message
    console.print(
        Panel.fit(
            f"[green]✅ Claude configuration initialized at {project_path / '.claude'}[/green]\n\n"
            "[cyan]Next steps:[/cyan]\n"
            "1. Run [yellow]claude-setup configure[/yellow] to customize for your project\n"
            "2. Start Claude Code with [yellow]claude[/yellow]\n"
            "3. Use [yellow]/help[/yellow] to see available commands",
            title="Success",
            border_style="green",
        )
    )


@cli.command()
@click.option(
    "--interactive", "-i", is_flag=True, default=True, help="Interactive configuration mode"
)
@click.option("--auto", "-a", is_flag=True, help="Auto-detect project configuration")
@click.option("--path", "-p", type=click.Path(), default=".", help="Project path")
@click.option("--show", "-s", is_flag=True, help="Show current configuration")
def configure(interactive: bool, auto: bool, path: str, show: bool):
    """Configure Claude Code for your specific project."""
    project_path = Path(path).resolve()

    if not (project_path / ".claude").exists():
        console.print("[red]No .claude directory found. Run 'claude-setup init' first.[/red]")
        sys.exit(1)

    if show:
        show_current_config(project_path)
        return

    if auto:
        console.print("[cyan]🔍 Auto-detecting project configuration...[/cyan]")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Analyzing project...", total=None)

            detector = ProjectDetector(project_path)
            detected = detector.detect()
            config = ProjectConfig(**detected)

            scaffolder = Scaffolder(project_path)
            scaffolder.apply_configuration(config)

            progress.update(task, description="Configuration applied!")

        console.print("[green]✅ Configuration auto-detected and applied![/green]")
        show_config_summary(config)
        return

    if interactive:
        config = interactive_configure(project_path)
        if config:
            scaffolder = Scaffolder(project_path)
            scaffolder.apply_configuration(config)
            console.print("[green]✅ Configuration saved and applied![/green]")


def interactive_configure(project_path: Path) -> Optional[ProjectConfig]:
    """Interactive configuration wizard."""
    console.print(
        Panel.fit(
            "[cyan]Claude Setup Configuration Wizard[/cyan]\n"
            "Answer a few questions to optimize Claude Code for your project.",
            title="Configuration",
            border_style="cyan",
        )
    )

    # Project type
    project_type = questionary.select(
        "What type of project is this?",
        choices=[
            "Web Application (React, Vue, Next.js, etc.)",
            "Backend API (FastAPI, Django, Express, etc.)",
            "CLI Tool / Library",
            "Data Science / ML",
            "Mobile App",
            "Documentation",
            "Other",
        ],
    ).ask()

    if not project_type:
        return None

    # Primary language
    language = questionary.select(
        "Primary programming language?",
        choices=["Python", "JavaScript/TypeScript", "Go", "Rust", "Java", "C/C++", "Other"],
    ).ask()

    if not language:
        return None

    # Frameworks
    frameworks = questionary.checkbox(
        "Select all frameworks/tools you're using:",
        choices=[
            "React",
            "Vue",
            "Next.js",
            "Angular",
            "Svelte",
            "FastAPI",
            "Django",
            "Flask",
            "Express",
            "PostgreSQL",
            "MongoDB",
            "Redis",
            "MySQL",
            "Docker",
            "Kubernetes",
            "GitHub Actions",
            "GitLab CI",
            "pytest",
            "Jest",
            "Vitest",
            "Tailwind CSS",
            "Material UI",
        ],
    ).ask()

    if frameworks is None:
        return None

    # Development needs
    needs = questionary.checkbox(
        "What do you need help with?",
        choices=[
            "Writing new features",
            "Refactoring existing code",
            "Writing tests",
            "Debugging",
            "Documentation",
            "Performance optimization",
            "Security review",
            "CI/CD setup",
            "Code review",
            "Architecture design",
        ],
    ).ask()

    if needs is None:
        return None

    # Team size
    team_size = questionary.select("Team size?", choices=["Solo", "2-5", "6-20", "20+"]).ask()

    if not team_size:
        return None

    # Advanced options
    if Confirm.ask("Configure advanced options?", default=False):
        # Model selection
        model = questionary.select(
            "Preferred Claude model?",
            choices=[
                "claude-opus-4-1-20250805 (Most capable)",
                "claude-3-5-sonnet-20241022 (Balanced)",
                "claude-3-5-haiku-20241022 (Fast)",
            ],
        ).ask()

        # Custom agents
        custom_agents = questionary.checkbox(
            "Additional specialized agents?",
            choices=[
                "Database Expert",
                "Security Auditor",
                "Performance Analyst",
                "UI/UX Designer",
                "DevOps Engineer",
                "Data Scientist",
            ],
        ).ask()
    else:
        model = "claude-opus-4-1-20250805"
        custom_agents = []

    # Generate configuration
    config = ProjectConfig(
        project_type=project_type.split(" (")[0],
        language=language,
        frameworks=frameworks,
        needs=needs,
        team_size=team_size,
        model=model.split(" (")[0] if model else "claude-opus-4-1-20250805",
        custom_agents=custom_agents or [],
    )

    # Show preview
    console.print("\n[cyan]Generated Configuration:[/cyan]")
    show_config_summary(config)

    if Confirm.ask("Apply this configuration?"):
        return config
    return None


@cli.group()
def template():
    """Manage Claude Code templates."""
    pass


@template.command("list")
def template_list():
    """List available templates."""
    manager = TemplateManager()
    templates = manager.list_templates()

    if not templates:
        console.print("[yellow]No templates found.[/yellow]")
        return

    table = Table(title="Available Templates", show_header=True, header_style="bold cyan")
    table.add_column("Name", style="yellow", width=20)
    table.add_column("Description", width=50)
    table.add_column("Source", style="dim", width=15)

    for tmpl in templates:
        table.add_row(tmpl.name, tmpl.description, tmpl.source)

    console.print(table)


@template.command("apply")
@click.argument("template_name")
@click.option("--path", "-p", type=click.Path(), default=".", help="Project path")
@click.option("--force", "-f", is_flag=True, help="Force apply without confirmation")
def template_apply(template_name: str, path: str, force: bool):
    """Apply a template to current project."""
    project_path = Path(path).resolve()

    if not (project_path / ".claude").exists():
        console.print("[red]No .claude directory found. Run 'claude-setup init' first.[/red]")
        sys.exit(1)

    if not force:
        if not Confirm.ask(f"Apply template '{template_name}' to current configuration?"):
            console.print("[yellow]Aborted.[/yellow]")
            return

    manager = TemplateManager()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Applying template '{template_name}'...", total=3)

        try:
            progress.update(task, advance=1, description="Loading template...")
            template_data = manager.get_template(template_name)

            progress.update(task, advance=1, description="Applying to project...")
            scaffolder = Scaffolder(project_path)
            scaffolder.apply_template_data(template_data)

            progress.update(task, advance=1, description="Complete!")

            console.print(f"[green]✅ Template '{template_name}' applied successfully![/green]")
        except Exception as e:
            console.print(f"[red]❌ Error applying template: {e}[/red]")
            sys.exit(1)


@template.command("add")
@click.argument("source")
@click.option("--name", "-n", help="Template name")
def template_add(source: str, name: Optional[str]):
    """Add a new template from GitHub or local path."""
    manager = TemplateManager()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Adding template...", total=2)

        try:
            progress.update(task, advance=1, description="Fetching template...")
            template_name = manager.add_template(source, name)

            progress.update(task, advance=1, description="Complete!")

            console.print(f"[green]✅ Template '{template_name}' added successfully![/green]")
        except Exception as e:
            console.print(f"[red]❌ Error adding template: {e}[/red]")
            sys.exit(1)


@cli.command()
@click.option("--check", "-c", is_flag=True, help="Check current configuration")
@click.option("--validate", "-v", is_flag=True, help="Validate configuration")
def status(check: bool, validate: bool):
    """Show Claude Setup status and configuration."""
    cwd = Path.cwd()
    claude_dir = cwd / ".claude"

    if not claude_dir.exists():
        console.print("[yellow]No .claude directory found in current directory.[/yellow]")
        console.print("\nRun [cyan]claude-setup init[/cyan] to initialize.")
        return

    # Show configuration status
    console.print(
        Panel.fit(
            f"[cyan]Claude Configuration Status[/cyan]\n\n"
            f"📁 Location: {claude_dir}\n"
            f"✅ Status: Active",
            title="Status",
            border_style="green",
        )
    )

    # Show installed components
    components = []
    if (claude_dir / "settings.json").exists():
        components.append("settings.json")
    if (cwd / "CLAUDE.md").exists():
        components.append("CLAUDE.md")

    commands_dir = claude_dir / "commands"
    if commands_dir.exists():
        num_commands = len(list(commands_dir.glob("*.md")))
        if num_commands > 0:
            components.append(f"{num_commands} commands")

    agents_dir = claude_dir / "agents"
    if agents_dir.exists():
        num_agents = len(list(agents_dir.glob("*.md")))
        if num_agents > 0:
            components.append(f"{num_agents} agents")

    console.print(f"\n[cyan]Components:[/cyan] {', '.join(components) if components else 'None'}")

    if validate or check:
        # Run validation checks
        console.print("\n[cyan]Running configuration checks...[/cyan]")
        validator = ConfigValidator(cwd)
        issues = validator.validate()

        if not issues:
            console.print("[green]✅ All checks passed![/green]")
        else:
            console.print("[yellow]⚠️  Issues found:[/yellow]")
            for issue in issues:
                console.print(f"  - {issue}")


@cli.command()
@click.option("--output", "-o", type=click.Path(), help="Output file for export")
def export(output: Optional[str]):
    """Export current configuration."""
    cwd = Path.cwd()
    claude_dir = cwd / ".claude"

    if not claude_dir.exists():
        console.print("[red]No .claude directory found.[/red]")
        sys.exit(1)

    config = load_config(cwd)
    if not config:
        console.print("[red]Could not load configuration.[/red]")
        sys.exit(1)

    export_data = config.to_dict()

    if output:
        output_path = Path(output)
        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2)
        console.print(f"[green]✅ Configuration exported to {output_path}[/green]")
    else:
        syntax = Syntax(json.dumps(export_data, indent=2), "json", theme="monokai")
        console.print(syntax)


def show_interactive_menu():
    """Show interactive menu when no command is specified."""
    console.print(
        Panel.fit(
            f"[cyan]Claude Setup v{__version__}[/cyan]\n"
            "Intelligent scaffolding for Claude Code configurations",
            title="Welcome",
            border_style="cyan",
        )
    )

    action = questionary.select(
        "What would you like to do?",
        choices=[
            "Initialize new project",
            "Configure existing project",
            "List templates",
            "Check status",
            "Exit",
        ],
    ).ask()

    if action == "Initialize new project":
        ctx = click.Context(init)
        init.invoke(ctx)
    elif action == "Configure existing project":
        ctx = click.Context(configure)
        configure.invoke(ctx)
    elif action == "List templates":
        ctx = click.Context(template_list)
        template_list.invoke(ctx)
    elif action == "Check status":
        ctx = click.Context(status)
        status.invoke(ctx)


def show_config_summary(config: ProjectConfig):
    """Display configuration summary."""
    table = Table(show_header=False, box=None)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Project Type", config.project_type)
    table.add_row("Language", config.language)
    table.add_row("Frameworks", ", ".join(config.frameworks) if config.frameworks else "None")
    table.add_row("Team Size", config.team_size)
    table.add_row("Model", config.model)

    if config.needs:
        table.add_row(
            "Focus Areas", ", ".join(config.needs[:3]) + ("..." if len(config.needs) > 3 else "")
        )

    console.print(table)


def show_current_config(project_path: Path):
    """Show current configuration."""
    config = load_config(project_path)
    if config:
        console.print("[cyan]Current Configuration:[/cyan]\n")
        show_config_summary(config)
    else:
        console.print("[yellow]No configuration found.[/yellow]")


def main():
    """Main entry point."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user.[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()

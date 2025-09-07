"""
CommandHelp - Help system for OpenCode commands
"""

from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich.markdown import Markdown

from specify_cli.services.command_registry import CommandRegistry


class CommandHelp:
    """Help system for displaying command information"""

    def __init__(self, registry: CommandRegistry, console: Optional[Console] = None):
        self.registry = registry
        self.console = console or Console()

    def show_command_help(self, command_name: str) -> None:
        """Show detailed help for a specific command"""
        command = self.registry.get_command(command_name)
        if not command:
            self.console.print(f"[red]Command '{command_name}' not found[/red]")
            self.show_available_commands()
            return

        help_info = self.registry.get_command_help(command_name)
        if not help_info:
            self.console.print(f"[red]No help available for '{command_name}'[/red]")
            return

        # Create help panel
        help_text = self._format_command_help(help_info)
        panel = Panel(
            help_text,
            title=f"Command: {command_name}",
            border_style="blue",
            padding=(1, 2)
        )

        self.console.print(panel)

    def show_available_commands(self, category: Optional[str] = None) -> None:
        """Show all available commands"""
        commands = self.registry.list_commands(category=category, include_hidden=False)

        if not commands:
            if category:
                self.console.print(f"[yellow]No commands found in category '{category}'[/yellow]")
            else:
                self.console.print("[yellow]No commands available[/yellow]")
            return

        # Group commands by category
        categories = {}
        for cmd in commands:
            cat = cmd.metadata.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(cmd)

        # Display commands by category
        for cat_name, cat_commands in categories.items():
            self._show_category_commands(cat_name, cat_commands)

    def show_category_help(self, category: str) -> None:
        """Show help for all commands in a category"""
        commands = self.registry.list_commands(category=category, include_hidden=False)

        if not commands:
            self.console.print(f"[yellow]No commands found in category '{category}'[/yellow]")
            return

        # Create table for category commands
        table = Table(title=f"Commands in '{category}' category", show_header=True, header_style="bold blue")
        table.add_column("Command", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Aliases", style="dim")

        for cmd in commands:
            aliases = ", ".join(cmd.metadata.aliases) if cmd.metadata.aliases else ""
            table.add_row(cmd.metadata.name, cmd.metadata.description, aliases)

        self.console.print(table)

    def show_command_summary(self) -> None:
        """Show a summary of all available commands"""
        stats = self.registry.get_stats()

        # Create summary panel
        summary_text = f"""
Total Commands: {stats['total_commands']}
Enabled Commands: {stats['enabled_commands']}
Categories: {stats['categories']}

Commands by Category:
"""

        for cat, count in stats['commands_per_category'].items():
            summary_text += f"  {cat}: {count} commands\n"

        panel = Panel(
            summary_text.strip(),
            title="Command Summary",
            border_style="green",
            padding=(1, 2)
        )

        self.console.print(panel)

    def search_commands(self, query: str) -> None:
        """Search and display commands matching a query"""
        results = self.registry.search_commands(query)

        if not results:
            self.console.print(f"[yellow]No commands found matching '{query}'[/yellow]")
            return

        # Create search results table
        table = Table(title=f"Search Results for '{query}'", show_header=True, header_style="bold magenta")
        table.add_column("Command", style="cyan", no_wrap=True)
        table.add_column("Category", style="blue")
        table.add_column("Description", style="white")

        for cmd in results:
            table.add_row(
                cmd.metadata.name,
                cmd.metadata.category,
                cmd.metadata.description
            )

        self.console.print(table)

    def show_command_signature(self, command_name: str) -> None:
        """Show the function signature for a command"""
        signature = self.registry.get_command_signature(command_name)

        if not signature:
            self.console.print(f"[red]No signature available for '{command_name}'[/red]")
            return

        panel = Panel(
            f"[cyan]{signature}[/cyan]",
            title=f"Signature: {command_name}",
            border_style="yellow",
            padding=(1, 2)
        )

        self.console.print(panel)

    def _format_command_help(self, help_info: Dict[str, Any]) -> str:
        """Format command help information"""
        lines = []

        # Description
        lines.append(f"[bold]Description:[/bold]\n{help_info['description']}\n")

        # Category
        lines.append(f"[bold]Category:[/bold] {help_info['category']}\n")

        # Aliases
        if help_info.get('aliases'):
            aliases = ", ".join(help_info['aliases'])
            lines.append(f"[bold]Aliases:[/bold] {aliases}\n")

        # Parameters
        if help_info.get('parameters'):
            lines.append("[bold]Parameters:[/bold]")
            for param_name, param_info in help_info['parameters'].items():
                param_type = param_info.get('type', 'any')
                default = f" (default: {param_info['default']})" if param_info.get('default') else ""
                required = " [red](required)[/red]" if param_info.get('required') else ""
                lines.append(f"  [cyan]{param_name}[/cyan] [{param_type}]{default}{required}")
            lines.append("")

        # Examples
        if help_info.get('examples'):
            lines.append("[bold]Examples:[/bold]")
            for example in help_info['examples']:
                lines.append(f"  [green]{example}[/green]")
            lines.append("")

        # Tags
        if help_info.get('tags'):
            tags = ", ".join(help_info['tags'])
            lines.append(f"[bold]Tags:[/bold] {tags}\n")

        # Additional info
        if help_info.get('requires_project'):
            lines.append("[yellow]⚠ This command requires a project context[/yellow]\n")

        if not help_info.get('enabled', True):
            lines.append("[red]⚠ This command is currently disabled[/red]\n")

        return "\n".join(lines)

    def _show_category_commands(self, category: str, commands: List) -> None:
        """Show commands for a specific category"""
        # Create table for category
        table = Table(title=f"Category: {category}", show_header=True, header_style="bold blue")
        table.add_column("Command", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Status", style="green")

        for cmd in commands:
            status = "[green]enabled[/green]" if cmd.enabled else "[red]disabled[/red]"
            table.add_row(cmd.metadata.name, cmd.metadata.description, status)

        self.console.print(table)
        self.console.print()  # Add spacing between categories

    def show_help_overview(self) -> None:
        """Show general help overview"""
        overview_text = """
# OpenCode Spec-Kit Help

Welcome to the OpenCode Spec-Driven Development toolkit!

## Getting Started

- Type `/help` to see this overview
- Type `/help <command>` to get help for a specific command
- Type `/commands` to list all available commands
- Type `/commands <category>` to list commands in a category

## Available Categories

- **specification**: Create and manage specifications
- **planning**: Generate implementation plans
- **task-management**: Handle development tasks
- **research**: Research and documentation
- **analysis**: Code analysis and migration
- **general**: General utility commands

## Command Syntax

Commands follow the format: `/<command> [arguments]`

Example:
  `/spec "Create user authentication" --template=default`
  `/plan --from-spec=user-auth-spec`
  `/tasks --list`

## Tips

- Use tab completion for command names and arguments
- Most commands support `--help` for detailed usage
- Commands marked with ⚠ require a project context
- Use `/search <query>` to find commands by keyword

For more information, visit: https://opencode.ai/spec-kit
"""

        markdown = Markdown(overview_text)
        self.console.print(markdown)
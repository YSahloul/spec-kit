#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer",
#     "rich",
#     "platformdirs",
#     "readchar",
#     "httpx",
# ]
# ///
"""
OpenCode Spec Kit - Setup tool for OpenCode Spec-Driven Development

Usage:
    uvx opencode-spec-kit.py init <project-name>
    uvx opencode-spec-kit.py init --here

Or install globally:
    uv tool install --from opencode-spec-kit.py opencode-spec-kit
    opencode-spec init <project-name>
    opencode-spec init --here
"""

import os
import subprocess
import sys
import zipfile
import tempfile
import shutil
import json
from pathlib import Path
from typing import Optional

import typer
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from rich.live import Live
from rich.align import Align
from rich.table import Table
from rich.tree import Tree
from typer.core import TyperGroup

# For cross-platform keyboard input
import readchar

# Constants
AI_CHOICES = {
    "opencode": "OpenCode CLI"
}

# ASCII Art Banner
BANNER = """
███████╗██████╗ ███████╗ ██████╗██╗███████╗██╗   ██╗
██╔════╝██╔══██╗██╔════╝██╔════╝██║██╔════╝╚██╗ ██╔╝
███████╗██████╔╝█████╗  ██║     ██║█████╗   ╚████╔╝ 
╚════██║██╔═══╝ ██╔══╝  ██║     ██║██╔══╝    ╚██╔╝  
███████║██║     ███████╗╚██████╗██║██║        ██║   
╚══════╝╚═╝     ╚══════╝ ╚═════╝╚═╝╚═╝        ╚═╝   
"""

TAGLINE = "OpenCode Spec-Driven Development Toolkit"
class StepTracker:
    """Track and render hierarchical steps without emojis, similar to Claude Code tree output.
    Supports live auto-refresh via an attached refresh callback.
    """
    def __init__(self, title: str):
        self.title = title
        self.steps = []  # list of dicts: {key, label, status, detail}
        self.status_order = {"pending": 0, "running": 1, "done": 2, "error": 3, "skipped": 4}
        self._refresh_cb = None  # callable to trigger UI refresh

    def attach_refresh(self, cb):
        self._refresh_cb = cb

    def add(self, key: str, label: str):
        if key not in [s["key"] for s in self.steps]:
            self.steps.append({"key": key, "label": label, "status": "pending", "detail": ""})
            self._maybe_refresh()

    def start(self, key: str, detail: str = ""):
        self._update(key, status="running", detail=detail)

    def complete(self, key: str, detail: str = ""):
        self._update(key, status="done", detail=detail)

    def error(self, key: str, detail: str = ""):
        self._update(key, status="error", detail=detail)

    def skip(self, key: str, detail: str = ""):
        self._update(key, status="skipped", detail=detail)

    def _update(self, key: str, status: str, detail: str):
        for s in self.steps:
            if s["key"] == key:
                s["status"] = status
                if detail:
                    s["detail"] = detail
                self._maybe_refresh()
                return
        # If not present, add it
        self.steps.append({"key": key, "label": key, "status": status, "detail": detail})
        self._maybe_refresh()

    def _maybe_refresh(self):
        if self._refresh_cb:
            try:
                self._refresh_cb()
            except Exception:
                pass

    def render(self):
        tree = Tree(f"[bold cyan]{self.title}[/bold cyan]", guide_style="grey50")
        for step in self.steps:
            label = step["label"]
            detail_text = step["detail"].strip() if step["detail"] else ""

            # Circles (unchanged styling)
            status = step["status"]
            if status == "done":
                symbol = "[green]●[/green]"
            elif status == "pending":
                symbol = "[green dim]○[/green dim]"
            elif status == "running":
                symbol = "[cyan]○[/cyan]"
            elif status == "error":
                symbol = "[red]●[/red]"
            elif status == "skipped":
                symbol = "[yellow]○[/yellow]"
            else:
                symbol = " "

            if status == "pending":
                # Entire line light gray (pending)
                if detail_text:
                    line = f"{symbol} [bright_black]{label} ({detail_text})[/bright_black]"
                else:
                    line = f"{symbol} [bright_black]{label}[/bright_black]"
            else:
                # Label white, detail (if any) light gray in parentheses
                if detail_text:
                    line = f"{symbol} [white]{label}[/white] [bright_black]({detail_text})[/bright_black]"
                else:
                    line = f"{symbol} [white]{label}[/white]"

            tree.add(line)
        return tree



MINI_BANNER = """
╔═╗╔═╗╔═╗╔═╗╦╔═╗╦ ╦
╚═╗╠═╝║╣ ║  ║╠╣ ╚╦╝
╚═╝╩  ╚═╝╚═╝╩╚   ╩ 
"""

def get_key():
    """Get a single keypress in a cross-platform way using readchar with fallback."""
    try:
        key = readchar.readkey()

        # Arrow keys
        if key == readchar.key.UP:
            return 'up'
        if key == readchar.key.DOWN:
            return 'down'

        # Enter/Return
        if key == readchar.key.ENTER:
            return 'enter'

        # Escape
        if key == readchar.key.ESC:
            return 'escape'

        # Ctrl+C
        if key == readchar.key.CTRL_C:
            raise KeyboardInterrupt

        return key
    except Exception:
        # Fallback to standard input if readchar fails
        try:
            import sys
            if sys.stdin.isatty():
                response = input().strip().lower()
                if response in ['y', 'yes', 'n', 'no']:
                    return response[0]  # Return just 'y' or 'n'
                elif response == '':
                    return 'enter'
                else:
                    return response
            else:
                # Not a TTY, can't get interactive input
                raise RuntimeError("Non-interactive terminal")
        except Exception:
            # Final fallback - assume 'y' for non-interactive environments
            return 'y'



def select_with_arrows(options: dict, prompt_text: str = "Select an option", default_key: str = None) -> str:
    """
    Interactive selection using arrow keys with Rich Live display.
    
    Args:
        options: Dict with keys as option keys and values as descriptions
        prompt_text: Text to show above the options
        default_key: Default option key to start with
        
    Returns:
        Selected option key
    """
    option_keys = list(options.keys())
    if default_key and default_key in option_keys:
        selected_index = option_keys.index(default_key)
    else:
        selected_index = 0
    
    selected_key = None

    def create_selection_panel():
        """Create the selection panel with current selection highlighted."""
        table = Table.grid(padding=(0, 2))
        table.add_column(style="bright_cyan", justify="left", width=3)
        table.add_column(style="white", justify="left")
        
        for i, key in enumerate(option_keys):
            if i == selected_index:
                table.add_row("▶", f"[bright_cyan]{key}: {options[key]}[/bright_cyan]")
            else:
                table.add_row(" ", f"[white]{key}: {options[key]}[/white]")
        
        table.add_row("", "")
        table.add_row("", "[dim]Use ↑/↓ to navigate, Enter to select, Esc to cancel[/dim]")
        
        return Panel(
            table,
            title=f"[bold]{prompt_text}[/bold]",
            border_style="cyan",
            padding=(1, 2)
        )
    
    console.print()

    def run_selection_loop():
        nonlocal selected_key, selected_index
        with Live(create_selection_panel(), console=console, transient=True, auto_refresh=False) as live:
            while True:
                try:
                    key = get_key()
                    if key == 'up':
                        selected_index = (selected_index - 1) % len(option_keys)
                    elif key == 'down':
                        selected_index = (selected_index + 1) % len(option_keys)
                    elif key == 'enter':
                        selected_key = option_keys[selected_index]
                        break
                    elif key == 'escape':
                        console.print("\n[yellow]Selection cancelled[/yellow]")
                        raise typer.Exit(1)
                    
                    live.update(create_selection_panel(), refresh=True)

                except KeyboardInterrupt:
                    console.print("\n[yellow]Selection cancelled[/yellow]")
                    raise typer.Exit(1)

    run_selection_loop()

    if selected_key is None:
        console.print("\n[red]Selection failed.[/red]")
        raise typer.Exit(1)

    # Suppress explicit selection print; tracker / later logic will report consolidated status
    return selected_key



console = Console()


class BannerGroup(TyperGroup):
    """Custom group that shows banner before help."""
    
    def format_help(self, ctx, formatter):
        # Show banner before help
        show_banner()
        super().format_help(ctx, formatter)


app = typer.Typer(
    name="opencode-spec",
    help="Setup tool for OpenCode spec-driven development projects",
    add_completion=False,
    invoke_without_command=True,
    cls=BannerGroup,
)


def show_banner():
    """Display the ASCII art banner."""
    # Create gradient effect with different colors
    banner_lines = BANNER.strip().split('\n')
    colors = ["bright_blue", "blue", "cyan", "bright_cyan", "white", "bright_white"]
    
    styled_banner = Text()
    for i, line in enumerate(banner_lines):
        color = colors[i % len(colors)]
        styled_banner.append(line + "\n", style=color)
    
    console.print(Align.center(styled_banner))
    console.print(Align.center(Text(TAGLINE, style="italic bright_yellow")))
    console.print()


@app.callback()
def callback(ctx: typer.Context):
    """Show banner when no subcommand is provided."""
    # Show banner only when no subcommand and no help flag
    # (help is handled by BannerGroup)
    if ctx.invoked_subcommand is None and "--help" not in sys.argv and "-h" not in sys.argv:
        show_banner()
        console.print(Align.center("[dim]Run 'specify --help' for usage information[/dim]"))
        console.print()


def run_command(cmd: list[str], check_return: bool = True, capture: bool = False, shell: bool = False) -> Optional[str]:
    """Run a shell command and optionally capture output."""
    try:
        if capture:
            result = subprocess.run(cmd, check=check_return, capture_output=True, text=True, shell=shell)
            return result.stdout.strip()
        else:
            subprocess.run(cmd, check=check_return, shell=shell)
            return None
    except subprocess.CalledProcessError as e:
        if check_return:
            console.print(f"[red]Error running command:[/red] {' '.join(cmd)}")
            console.print(f"[red]Exit code:[/red] {e.returncode}")
            if hasattr(e, 'stderr') and e.stderr:
                console.print(f"[red]Error output:[/red] {e.stderr}")
            raise
        return None


def check_tool(tool: str, install_hint: str) -> bool:
    """Check if a tool is installed."""
    # First check PATH
    if shutil.which(tool):
        return True

    # Special handling for OpenCode CLI - check common installation locations
    if tool == "opencode":
        opencode_paths = [
            Path.home() / ".opencode" / "bin" / "opencode",
            Path.home() / ".local" / "bin" / "opencode",
            Path("/usr/local/bin/opencode"),
            Path("/opt/opencode/bin/opencode"),
        ]
        for path in opencode_paths:
            if path.exists() and path.is_file():
                console.print(f"[green]✓[/green] Found OpenCode CLI at: {path}")
                return True

    console.print(f"[yellow]⚠️  {tool} not found[/yellow]")
    console.print(f"   Install with: [cyan]{install_hint}[/cyan]")
    return False


def is_git_repo(path: Path = None) -> bool:
    """Check if the specified path is inside a git repository."""
    if path is None:
        path = Path.cwd()
    
    if not path.is_dir():
        return False

    try:
        # Use git command to check if inside a work tree
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            check=True,
            capture_output=True,
            cwd=path,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def init_git_repo(project_path: Path, quiet: bool = False) -> bool:
    """Initialize a git repository in the specified path.
    quiet: if True suppress console output (tracker handles status)
    """
    try:
        original_cwd = Path.cwd()
        os.chdir(project_path)
        if not quiet:
            console.print("[cyan]Initializing git repository...[/cyan]")
        subprocess.run(["git", "init"], check=True, capture_output=True)
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit from Specify template"], check=True, capture_output=True)
        if not quiet:
            console.print("[green]✓[/green] Git repository initialized")
        return True
        
    except subprocess.CalledProcessError as e:
        if not quiet:
            console.print(f"[red]Error initializing git repository:[/red] {e}")
        return False
    finally:
        os.chdir(original_cwd)


def download_template_from_github(ai_assistant: str, download_dir: Path, *, verbose: bool = True, show_progress: bool = True):
    """Download the latest template release from GitHub using HTTP requests.
    Returns (zip_path, metadata_dict)
    """
    repo_owner = "github"
    repo_name = "spec-kit"
    
    if verbose:
        console.print("[cyan]Fetching latest release information...[/cyan]")
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
    
    try:
        response = httpx.get(api_url, timeout=30, follow_redirects=True)
        response.raise_for_status()
        release_data = response.json()
    except httpx.RequestError as e:
        if verbose:
            console.print(f"[red]Error fetching release information:[/red] {e}")
        raise typer.Exit(1)
    
    ## Find the template asset for the specified AI assistant
    pattern = f"spec-kit-template-{ai_assistant}"
    matching_assets = [
        asset for asset in release_data.get("assets", [])
        if pattern in asset["name"] and asset["name"].endswith(".zip")
    ]
    
    if not matching_assets:
        if verbose:
            console.print(f"[red]Error:[/red] No template found for AI assistant '{ai_assistant}'")
            console.print(f"[yellow]Available assets:[/yellow]")
            for asset in release_data.get("assets", []):
                console.print(f"  - {asset['name']}")
        raise typer.Exit(1)
    
    # Use the first matching asset
    asset = matching_assets[0]
    download_url = asset["browser_download_url"]
    filename = asset["name"]
    file_size = asset["size"]
    
    if verbose:
        console.print(f"[cyan]Found template:[/cyan] {filename}")
        console.print(f"[cyan]Size:[/cyan] {file_size:,} bytes")
        console.print(f"[cyan]Release:[/cyan] {release_data['tag_name']}")
    
    # Download the file
    zip_path = download_dir / filename
    if verbose:
        console.print(f"[cyan]Downloading template...[/cyan]")
    
    try:
        with httpx.stream("GET", download_url, timeout=30, follow_redirects=True) as response:
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            
            with open(zip_path, 'wb') as f:
                if total_size == 0:
                    # No content-length header, download without progress
                    for chunk in response.iter_bytes(chunk_size=8192):
                        f.write(chunk)
                else:
                    if show_progress:
                        # Show progress bar
                        with Progress(
                            SpinnerColumn(),
                            TextColumn("[progress.description]{task.description}"),
                            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                            console=console,
                        ) as progress:
                            task = progress.add_task("Downloading...", total=total_size)
                            downloaded = 0
                            for chunk in response.iter_bytes(chunk_size=8192):
                                f.write(chunk)
                                downloaded += len(chunk)
                                progress.update(task, completed=downloaded)
                    else:
                        # Silent download loop
                        for chunk in response.iter_bytes(chunk_size=8192):
                            f.write(chunk)
    
    except httpx.RequestError as e:
        if verbose:
            console.print(f"[red]Error downloading template:[/red] {e}")
        if zip_path.exists():
            zip_path.unlink()
        raise typer.Exit(1)
    if verbose:
        console.print(f"Downloaded: {filename}")
    metadata = {
        "filename": filename,
        "size": file_size,
        "release": release_data["tag_name"],
        "asset_url": download_url
    }
    return zip_path, metadata


def download_and_extract_template(project_path: Path, ai_assistant: str, is_current_dir: bool = False, *, verbose: bool = True, tracker: StepTracker | None = None) -> Path:
    """Copy local templates to create a new project.
    Returns project_path. Uses tracker if provided (with keys: fetch, download, extract, cleanup)
    """
    current_dir = Path.cwd()

    # Step: fetch + download combined (using local templates)
    if tracker:
        tracker.start("fetch", "using local templates")
    try:
        # Get the path to the spec-kit templates directory
        spec_kit_path = Path(__file__).parent.parent.parent
        templates_path = spec_kit_path / "templates"

        if not templates_path.exists():
            raise FileNotFoundError(f"Templates directory not found: {templates_path}")

        if tracker:
            tracker.complete("fetch", f"local templates ({templates_path})")
            tracker.add("download", "Copy template files")
            tracker.complete("download", "local files")
    except Exception as e:
        if tracker:
            tracker.error("fetch", str(e))
        else:
            if verbose:
                console.print(f"[red]Error accessing templates:[/red] {e}")
        raise
    
    if tracker:
        tracker.add("extract", "Copy template files")
        tracker.start("extract")
    elif verbose:
        console.print("Copying template files...")

    try:
        # Create project directory only if not using current directory
        if not is_current_dir:
            project_path.mkdir(parents=True)

        # List all template files
        template_files = list(templates_path.rglob('*'))
        template_files = [f for f in template_files if f.is_file()]

        if tracker:
            tracker.start("zip-list")
            tracker.complete("zip-list", f"{len(template_files)} files")
        elif verbose:
            console.print(f"[cyan]Found {len(template_files)} template files[/cyan]")

        # Copy template files to project directory - everything goes under .opencode/
        for template_file in template_files:
            # Get relative path from templates directory
            rel_path = template_file.relative_to(templates_path)
            
            # Everything goes under .opencode/
            if rel_path.parts[0] in ('command', 'scripts', 'memory'):
                # These directories keep their names under .opencode/
                dest_path = project_path / '.opencode' / rel_path
            else:
                # All other files (templates) go in .opencode/templates/
                dest_path = project_path / '.opencode' / 'templates' / rel_path

            # Create parent directories if needed
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy the file
            shutil.copy2(template_file, dest_path)

            if verbose and not tracker:
                console.print(f"[cyan]Copied:[/cyan] {rel_path}")

        if tracker:
            tracker.start("extracted-summary")
            tracker.complete("extracted-summary", f"copied {len(template_files)} files")
        elif verbose:
            console.print(f"[cyan]Copied {len(template_files)} template files[/cyan]")

        if tracker:
            tracker.complete("extract")

    except Exception as e:
        if tracker:
            tracker.error("extract", str(e))
        else:
            if verbose:
                console.print(f"[red]Error copying templates:[/red] {e}")
        # Clean up project directory if created and not current directory
        if not is_current_dir and project_path.exists():
            shutil.rmtree(project_path)
        raise typer.Exit(1)

    return project_path


@app.command()
def init(
    project_name: str = typer.Argument(None, help="Name for your new project directory (leave empty to initialize in current directory)"),
    ignore_agent_tools: bool = typer.Option(True, "--ignore-agent-tools/--check-agent-tools", help="Skip checks for OpenCode CLI (default: skip)"),
    no_git: bool = typer.Option(False, "--no-git", help="Skip git repository initialization"),
    here: bool = typer.Option(False, "--here", help="Initialize project in the current directory (deprecated - just use 'specify init')"),
):
    """
    Initialize a new OpenCode Spec-Driven Development project.

    This command will:
    1. Check that required tools are installed (git is optional)
    2. Configure for OpenCode CLI (the exclusive AI assistant)
    3. Download the OpenCode-optimized template from GitHub
    4. Extract the template to a new project directory or current directory
    5. Initialize a fresh git repository (if not --no-git and no existing repo)
    6. Set up OpenCode spec-driven development commands

    Examples:
        specify init              # Initialize in current directory
        specify init my-project   # Create new directory 'my-project'
        specify init --here       # Initialize in current directory (deprecated)
    """
    # Show banner first
    show_banner()
    
    # If no project name and not using --here, default to current directory
    if not project_name and not here:
        here = True
    
    # Validate arguments
    if here and project_name:
        console.print("[red]Error:[/red] Cannot specify both project name and --here flag")
        raise typer.Exit(1)
    
    # Determine project directory
    if here:
        project_name = Path.cwd().name
        project_path = Path.cwd()
        
        # Check if current directory has any files
        existing_items = list(project_path.iterdir())
        if existing_items:
            console.print(f"[yellow]Warning:[/yellow] Current directory is not empty ({len(existing_items)} items)")
            console.print("[yellow]Template files will be merged with existing content and may overwrite existing files[/yellow]")
            
            # Ask for confirmation using custom function
            console.print("[yellow]Continue? (y/n)[/yellow] ", end="")
            try:
                key = get_key()
                console.print(key)  # Echo the key that was pressed
                if key.lower() not in ['y', 'yes']:
                    console.print("\n[yellow]Operation cancelled[/yellow]")
                    raise typer.Exit(0)
            except KeyboardInterrupt:
                console.print("\n[yellow]Operation cancelled[/yellow]")
                raise typer.Exit(0)
            except Exception as e:
                # If we can't read input interactively, fall back to typer.confirm
                console.print("\n[yellow]Falling back to standard prompt...[/yellow]")
                try:
                    response = typer.confirm("Do you want to continue?")
                    if not response:
                        console.print("[yellow]Operation cancelled[/yellow]")
                        raise typer.Exit(0)
                except Exception:
                    # Final fallback for completely non-interactive environments
                    console.print("\n[yellow]Non-interactive environment detected, proceeding automatically...[/yellow]")
    else:
        project_path = Path(project_name).resolve()
        # Check if project directory already exists
        if project_path.exists():
            console.print(f"[red]Error:[/red] Directory '{project_name}' already exists")
            raise typer.Exit(1)
    
    console.print(Panel.fit(
        "[bold cyan]Specify Project Setup[/bold cyan]\n"
        f"{'Initializing in current directory:' if here else 'Creating new project:'} [green]{project_path.name}[/green]"
        + (f"\n[dim]Path: {project_path}[/dim]" if here else ""),
        border_style="cyan"
    ))
    
    # Check git only if we might need it (not --no-git)
    git_available = True
    if not no_git:
        git_available = check_tool("git", "https://git-scm.com/downloads")
        if not git_available:
            console.print("[yellow]Git not found - will skip repository initialization[/yellow]")

    # AI assistant selection (OpenCode only)
    selected_ai = "opencode"
    console.print("[cyan]Using OpenCode CLI for spec-driven development[/cyan]")
    
    # Check agent tools unless ignored
    opencode_available = False
    if not ignore_agent_tools:
        if selected_ai == "opencode":
            opencode_available = check_tool("opencode", "Install from: https://opencode.ai/install")
            if not opencode_available:
                console.print("[yellow]⚠️  OpenCode CLI not found[/yellow]")
                console.print("[cyan]ℹ️  Spec-kit will work in standalone mode[/cyan]")
                console.print("[cyan]   Install OpenCode CLI for full integration: https://opencode.ai/install[/cyan]")
                console.print()
    else:
        # When ignoring agent tools, assume OpenCode is not available
        opencode_available = False
    
    # Download and set up project
    # New tree-based progress (no emojis); include earlier substeps
    tracker = StepTracker("Initialize Specify Project")
    # Flag to allow suppressing legacy headings
    sys._specify_tracker_active = True
    # Pre steps recorded as completed before live rendering
    tracker.add("precheck", "Check required tools")
    tracker.complete("precheck", "ok")
    tracker.add("ai-select", "Select AI assistant")
    tracker.complete("ai-select", f"{selected_ai}")
    for key, label in [
        ("fetch", "Fetch latest release"),
        ("download", "Download template"),
        ("extract", "Extract template"),
        ("zip-list", "Archive contents"),
        ("extracted-summary", "Extraction summary"),
        ("cleanup", "Cleanup"),
        ("git", "Initialize git repository"),
        ("final", "Finalize")
    ]:
        tracker.add(key, label)

    # Use transient so live tree is replaced by the final static render (avoids duplicate output)
    with Live(tracker.render(), console=console, refresh_per_second=8, transient=True) as live:
        tracker.attach_refresh(lambda: live.update(tracker.render()))
        try:
            download_and_extract_template(project_path, selected_ai, here, verbose=False, tracker=tracker)

            # Git step
            if not no_git:
                tracker.start("git")
                if is_git_repo(project_path):
                    tracker.complete("git", "existing repo detected")
                elif git_available:
                    if init_git_repo(project_path, quiet=True):
                        tracker.complete("git", "initialized")
                    else:
                        tracker.error("git", "init failed")
                else:
                    tracker.skip("git", "git not available")
            else:
                tracker.skip("git", "--no-git flag")

            tracker.complete("final", "project ready")
        except Exception as e:
            tracker.error("final", str(e))
            if not here and project_path.exists():
                shutil.rmtree(project_path)
            raise typer.Exit(1)
        finally:
            # Force final render
            pass

    # Final static tree (ensures finished state visible after Live context ends)
    console.print(tracker.render())
    console.print("\n[bold green]Project ready.[/bold green]")
    
    # Boxed "Next steps" section
    steps_lines = []
    if not here:
        steps_lines.append(f"1. [bold green]cd {project_name}[/bold green]")
        step_num = 2
    else:
        steps_lines.append("1. You're already in the project directory!")
        step_num = 2

    if selected_ai == "opencode":
        steps_lines.append(f"{step_num}. Start using OpenCode CLI commands")
        steps_lines.append("   - Type / in any file to see available commands")
        steps_lines.append("   - Use /spec to create specifications")
        steps_lines.append("   - Use /plan to create implementation plans")
        steps_lines.append("   - Use /tasks to generate tasks")
        steps_lines.append("   - Use /research for technical research")
        steps_lines.append("   - Use /analyze to analyze existing codebases")

    step_num += 1
    steps_lines.append(f"{step_num}. Update [bold magenta]CONSTITUTION.md[/bold magenta] with your project's non-negotiable principles")

    steps_panel = Panel("\n".join(steps_lines), title="Next steps", border_style="cyan", padding=(1,2))
    console.print()  # blank line
    console.print(steps_panel)
    
    # Removed farewell line per user request


@app.command()
def check():
    """Check that all required tools are installed."""
    show_banner()
    console.print("[bold]Checking Specify requirements...[/bold]\n")
    
    # Check if we have internet connectivity by trying to reach GitHub API
    console.print("[cyan]Checking internet connectivity...[/cyan]")
    try:
        response = httpx.get("https://api.github.com", timeout=5, follow_redirects=True)
        console.print("[green]✓[/green] Internet connection available")
    except httpx.RequestError:
        console.print("[red]✗[/red] No internet connection - required for downloading templates")
        console.print("[yellow]Please check your internet connection[/yellow]")
    
    console.print("\n[cyan]Optional tools:[/cyan]")
    git_ok = check_tool("git", "https://git-scm.com/downloads")
    
    console.print("\n[cyan]Required AI tools:[/cyan]")
    opencode_ok = check_tool("opencode", "Install from: https://opencode.ai/install")

    console.print("\n[green]✓ OpenCode Spec Kit is ready to use![/green]")
    if not git_ok:
        console.print("[yellow]Consider installing git for repository management[/yellow]")
    if not opencode_ok:
        console.print("[red]OpenCode CLI is required for the best experience[/red]")
        console.print("[yellow]Install from: https://opencode.ai/install[/yellow]")


def main():
    app()


if __name__ == "__main__":
    main()

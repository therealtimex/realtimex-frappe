"""Run command - unified setup and start for production use."""

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel

from ..config.env import (
    config_from_environment,
    get_missing_required_env_vars,
    print_env_var_help,
)
from ..config.schema import RealtimexConfig
from ..utils.bench import (
    bench_exists,
    create_site,
    init_bench,
    install_all_apps,
    site_exists,
    start_bench,
    update_common_site_config,
)
from ..utils.environment import (
    get_prerequisite_install_hint,
    validate_all_prerequisites,
    validate_system_prerequisites,
)

console = Console()


def run_setup_and_start(config: Optional[RealtimexConfig] = None) -> None:
    """Set up a new Frappe site and start the server.

    This is the primary production command that:
    1. Validates system prerequisites (git, pkg-config)
    2. Reads configuration from environment variables
    3. Validates bundled binaries (node, npm)
    4. Initializes bench (if needed)
    5. Creates the site (if needed)
    6. Installs apps (if needed)
    7. Starts the bench server

    The function uses os.execvpe to replace the current process with
    the bench server, ensuring proper signal handling.

    Args:
        config: Optional pre-loaded configuration. If not provided,
            configuration is read from environment variables.
    """
    console.print(Panel.fit("🚀 Realtimex Frappe", style="bold blue"))

    # Step 1: Validate system prerequisites
    console.print("\n[bold]Checking system prerequisites...[/bold]")

    prereq_result = validate_system_prerequisites()
    if not prereq_result.is_valid:
        console.print("[red]✗ Missing required system prerequisites:[/red]")
        for binary in prereq_result.missing_required:
            hint = get_prerequisite_install_hint(binary)
            console.print(f"  [red]•[/red] {binary}")
            if hint:
                console.print(f"    [dim]Install: {hint}[/dim]")
        console.print("\n[yellow]Please install the missing prerequisites and try again.[/yellow]")
        raise SystemExit(1)

    console.print(f"[green]✓[/green] System prerequisites found: {', '.join(prereq_result.available)}")

    # Step 2: Load configuration from environment
    console.print("\n[bold]Loading configuration...[/bold]")

    if config is None:
        # Check for missing required environment variables
        missing = get_missing_required_env_vars()
        if missing:
            console.print("[red]✗ Missing required environment variables:[/red]")
            for var in missing:
                console.print(f"  [red]•[/red] {var}")
            console.print("\n[yellow]Set the following environment variables:[/yellow]")
            print_env_var_help()
            raise SystemExit(1)

        config = config_from_environment()

    console.print(f"  Site: [cyan]{config.site.name}[/cyan]")
    console.print(f"  Bench: [cyan]{config.bench.path}[/cyan]")
    console.print(
        f"  Database: [cyan]{config.database.host}:{config.database.port}/{config.database.name}[/cyan]"
    )

    # Step 3: Validate bundled binaries
    console.print("\n[bold]Validating bundled binaries...[/bold]")

    _, binaries_result = validate_all_prerequisites(config)
    if not binaries_result.is_valid:
        console.print(f"[red]✗ Missing required binaries: {', '.join(binaries_result.missing)}[/red]")
        console.print("\n[yellow]Set REALTIMEX_NODE_BIN_DIR to the path of your Node.js bin directory.[/yellow]")
        raise SystemExit(1)

    console.print(f"[green]✓[/green] Bundled binaries found: {', '.join(binaries_result.available)}")

    # Step 3: Initialize bench (if needed)
    console.print("\n[bold]Setting up bench...[/bold]")

    if bench_exists(config):
        console.print(f"[green]✓[/green] Using existing bench at {config.bench.path}")
    else:
        console.print("[blue]Initializing new bench...[/blue]")
        if not init_bench(config):
            console.print("[red]✗ Failed to initialize bench[/red]")
            raise SystemExit(1)
        console.print("[green]✓[/green] Bench initialized")

    # Step 4: Update common_site_config.json
    console.print("\n[bold]Configuring site settings...[/bold]")
    update_common_site_config(config)

    # Step 5: Create site (if needed)
    console.print("\n[bold]Setting up site...[/bold]")

    if site_exists(config):
        console.print(f"[green]✓[/green] Site {config.site.name} already exists")
    else:
        console.print(f"[blue]Creating site {config.site.name}...[/blue]")
        if not create_site(config):
            console.print("[red]✗ Failed to create site[/red]")
            raise SystemExit(1)
        console.print(f"[green]✓[/green] Site created")

        # Step 6: Install apps (only for new sites)
        if config.apps:
            console.print("\n[bold]Installing apps...[/bold]")
            if not install_all_apps(config):
                console.print("[red]✗ Failed to install apps[/red]")
                raise SystemExit(1)
            console.print("[green]✓[/green] Apps installed")

    # Step 7: Start the bench server
    console.print("\n" + "=" * 50)
    console.print(Panel.fit("✅ Setup complete! Starting server...", style="bold green"))

    # This replaces the current process with bench start
    start_bench(config)

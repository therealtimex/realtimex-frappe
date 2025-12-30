"""Run command - unified setup and start for production use."""

import time
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
    get_all_apps,
    init_bench,
    install_apps_on_site,
    run_bench_start_subprocess,
    site_exists,
    site_is_healthy,
    start_bench,
    update_common_site_config,
)
from ..utils.environment import (
    get_prerequisite_install_hint,
    validate_all_prerequisites,
    validate_system_prerequisites,
)
from ..utils.paths import ensure_bench_directory

console = Console()


def wait_for_bench_ready(port: int = 8000, timeout: int = 60) -> bool:
    """Wait for bench to be ready (web server available on specified port).

    Args:
        port: The port to check for webserver availability.
        timeout: Maximum seconds to wait.

    Returns:
        True if bench is ready, False if timeout.
    """
    import socket

    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(("127.0.0.1", port))
            sock.close()
            if result == 0:
                return True
        except Exception:
            pass
        time.sleep(2)
        console.print("[dim]Waiting for bench to be ready...[/dim]")

    return False


def run_setup_and_start(config: Optional[RealtimexConfig] = None) -> None:
    """Set up a new Frappe site and start the server.

    This command handles the full setup flow:
    1. Validates system prerequisites (git, pkg-config, wkhtmltopdf)
    2. Reads configuration from environment variables
    3. Validates bundled binaries (node, npm)
    4. Initializes bench (if needed)
    5. Gets apps (clone repositories)
    6. Creates the site (if needed)
    7. Starts bench temporarily for app installation
    8. Installs apps on site (requires Redis to be running)
    9. Starts the bench server for production

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

    console.print(f"[green]✓[/green] System prerequisites: {', '.join(prereq_result.available)}")

    # Step 2: Load configuration from environment
    console.print("\n[bold]Loading configuration...[/bold]")

    if config is None:
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
    console.print(f"  Database: [cyan]{config.database.host}:{config.database.port}/{config.database.name}[/cyan]")

    # Step 3: Validate bundled binaries
    console.print("\n[bold]Validating bundled binaries...[/bold]")

    _, binaries_result = validate_all_prerequisites(config)
    if not binaries_result.is_valid:
        console.print(f"[red]✗ Missing required binaries: {', '.join(binaries_result.missing)}[/red]")
        console.print("\n[yellow]Set REALTIMEX_NODE_BIN_DIR to the path of your Node.js bin directory.[/yellow]")
        raise SystemExit(1)

    console.print(f"[green]✓[/green] Bundled binaries: {', '.join(binaries_result.available)}")

    # Step 4: Initialize bench (if needed)
    console.print("\n[bold]Setting up bench...[/bold]")

    if bench_exists(config):
        console.print(f"[green]✓[/green] Using existing bench at {config.bench.path}")
    else:
        ensure_bench_directory()
        console.print("[blue]Initializing new bench...[/blue]")
        if not init_bench(config):
            console.print("[red]✗ Failed to initialize bench[/red]")
            raise SystemExit(1)
        console.print("[green]✓[/green] Bench initialized")

    # Step 5: Update common_site_config.json with Redis/DB settings
    console.print("\n[bold]Configuring site settings...[/bold]")
    update_common_site_config(config)

    # Step 6: Get apps (clone repositories only, no install yet)
    if config.apps:
        console.print("\n[bold]Getting apps...[/bold]")
        if not get_all_apps(config):
            console.print("[red]✗ Failed to get apps[/red]")
            raise SystemExit(1)

    # Step 7: Create site (if needed) or repair if in partial state
    console.print("\n[bold]Setting up site...[/bold]")
    needs_app_install = False

    healthy, reason = site_is_healthy(config)

    if healthy:
        console.print(f"[green]✓[/green] Site {config.site.name} is healthy")
    elif reason == "not_found":
        # Fresh install
        console.print(f"[blue]Creating new site {config.site.name}...[/blue]")
        if not create_site(config):
            console.print("[red]✗ Failed to create site[/red]")
            raise SystemExit(1)
        console.print(f"[green]✓[/green] Site created")
        needs_app_install = True
    else:
        # Partial state detected - repair with --force
        console.print(f"[yellow]⚠[/yellow] Site in partial state ({reason}), repairing...")
        if not create_site(config, force=True):
            console.print("[red]✗ Failed to repair site[/red]")
            raise SystemExit(1)
        console.print(f"[green]✓[/green] Site repaired")
        needs_app_install = True

    # Step 8: Install apps (requires bench to be running for after_install hooks)
    if needs_app_install and config.apps:
        console.print("\n[bold]Installing apps...[/bold]")
        console.print("[dim]Starting bench temporarily for app installation (Redis required)...[/dim]")

        # Start bench as subprocess
        bench_process = run_bench_start_subprocess(config)

        try:
            # Wait for bench to be ready
            if not wait_for_bench_ready(port=config.bench.port, timeout=120):
                console.print("[red]✗ Timeout waiting for bench to start[/red]")
                bench_process.terminate()
                raise SystemExit(1)

            console.print("[green]✓[/green] Bench is ready")

            # Install apps
            if not install_apps_on_site(config):
                console.print("[red]✗ Failed to install apps[/red]")
                bench_process.terminate()
                raise SystemExit(1)

            console.print("[green]✓[/green] Apps installed")

        finally:
            # Stop the temporary bench process
            console.print("[dim]Stopping temporary bench...[/dim]")
            bench_process.terminate()
            try:
                bench_process.wait(timeout=10)
            except Exception:
                bench_process.kill()

    # Step 9: Start the bench server (final - replaces current process)
    console.print("\n" + "=" * 50)
    console.print(Panel.fit("✅ Setup complete! Starting server...", style="bold green"))

    # This replaces the current process with bench start
    start_bench(config)

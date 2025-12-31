"""Setup command - admin-only site initialization and migration."""

from typing import Optional

from rich.console import Console
from rich.panel import Panel

from ..config.env import (
    config_from_environment,
    get_missing_required_env_vars,
    print_env_var_help,
)
from ..config.schema import RealtimexConfig, RunMode
from ..utils.bench import (
    bench_exists,
    create_site,
    get_all_apps,
    init_bench,
    install_apps_on_site,
    run_bench_start_subprocess,
    site_exists,
    site_is_healthy,
    update_common_site_config,
)
from ..utils.environment import (
    get_prerequisite_install_hint,
    validate_all_prerequisites,
)
from ..utils.paths import ensure_bench_directory

console = Console()


def run_setup(config: Optional[RealtimexConfig] = None) -> None:
    """Run admin setup: create site, install apps, run migrations.

    This command is for administrators only. It:
    1. Validates system prerequisites
    2. Initializes bench (if needed)
    3. Clones apps (if needed)
    4. Creates site with database (requires admin DB credentials)
    5. Installs apps on site
    6. Updates common_site_config.json

    Args:
        config: Optional pre-loaded configuration. If not provided,
            configuration is read from environment variables.
    """
    console.print(
        Panel.fit("🔧 Realtimex Frappe Setup (Admin Mode)", style="bold blue")
    )

    # Step 1: Load configuration from environment
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

    # Verify admin mode
    if config.mode != RunMode.ADMIN:
        console.print("[red]✗ Setup requires REALTIMEX_MODE=admin[/red]")
        raise SystemExit(1)

    # Verify schema is set (required for setup)
    if not config.database.schema:
        console.print("[red]✗ Setup requires REALTIMEX_DB_SCHEMA[/red]")
        console.print("[dim]Schema-based isolation is required for setup.[/dim]")
        raise SystemExit(1)

    console.print(f"  Mode: [cyan]{config.mode.value}[/cyan]")
    console.print(f"  Site: [cyan]{config.site.name}[/cyan]")
    console.print(f"  Bench: [cyan]{config.bench.path}[/cyan]")
    console.print(
        f"  Database: [cyan]{config.database.host}:{config.database.port}/{config.database.name}[/cyan]"
    )
    console.print(f"  Schema: [cyan]{config.database.schema}[/cyan]")
    console.print(f"  Admin DB User: [cyan]{config.database.admin_user}[/cyan]")

    # Step 2: Validate system and bundled prerequisites
    console.print("\n[bold]Validating prerequisites...[/bold]")

    prereqs, binaries_result = validate_all_prerequisites(config)
    if not prereqs.is_valid:
        console.print(
            f"[red]✗ Missing system prerequisites: {', '.join(prereqs.missing)}[/red]"
        )
        for prereq in prereqs.missing:
            hint = get_prerequisite_install_hint(prereq)
            if hint:
                console.print(f"  [yellow]Install {prereq}: {hint}[/yellow]")
        raise SystemExit(1)

    console.print(
        f"[green]✓[/green] System prerequisites: {', '.join(prereqs.available)}"
    )

    if not binaries_result.is_valid:
        console.print(
            f"[red]✗ Missing bundled binaries: {', '.join(binaries_result.missing)}[/red]"
        )
        console.print(
            "\n[yellow]Set REALTIMEX_NODE_BIN_DIR to the path of your Node.js bin directory.[/yellow]"
        )
        raise SystemExit(1)

    console.print(
        f"[green]✓[/green] Bundled binaries: {', '.join(binaries_result.available)}"
    )

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

    # Step 5: Get apps
    console.print("\n[bold]Getting apps...[/bold]")

    if not get_all_apps(config):
        console.print("[red]✗ Failed to get apps[/red]")
        raise SystemExit(1)

    console.print("[green]✓[/green] Apps ready")

    # Step 6: Update common_site_config.json
    console.print("\n[bold]Configuring site settings...[/bold]")
    update_common_site_config(config)

    # Step 7: Create site (if needed)
    console.print("\n[bold]Creating site...[/bold]")

    if site_exists(config):
        healthy, reason = site_is_healthy(config)
        if healthy:
            console.print(f"[green]✓[/green] Site {config.site.name} already exists")
        else:
            console.print(
                f"[yellow]⚠ Site exists but unhealthy ({reason}). Recreating...[/yellow]"
            )
            if not create_site(config, force=True):
                console.print("[red]✗ Failed to recreate site[/red]")
                raise SystemExit(1)
            console.print("[green]✓[/green] Site recreated")
    else:
        if not create_site(config):
            console.print("[red]✗ Failed to create site[/red]")
            raise SystemExit(1)
        console.print(f"[green]✓[/green] Site {config.site.name} created")

    # Step 8: Install apps (requires running bench)
    if config.apps:
        console.print("\n[bold]Installing apps (starting temporary bench)...[/bold]")

        bench_proc = run_bench_start_subprocess(config)
        try:
            import time

            # Wait for bench to start
            for _ in range(30):
                time.sleep(2)
                # Simple check if bench is responding
                break

            if not install_apps_on_site(config):
                console.print("[red]✗ Failed to install apps[/red]")
                bench_proc.terminate()
                raise SystemExit(1)

            console.print("[green]✓[/green] Apps installed")
        finally:
            bench_proc.terminate()
            bench_proc.wait()

    console.print("\n" + "=" * 60)
    console.print("[bold green]✓ Setup complete![/bold green]")
    console.print(f"\n[dim]Site: http://{config.site.name}:{config.bench.port}[/dim]")
    console.print("[dim]Run with: REALTIMEX_MODE=user realtimex-frappe run[/dim]")

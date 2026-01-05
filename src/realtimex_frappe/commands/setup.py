"""Setup command - administrator site initialization.

Orchestrates complete site setup:
1. Validate configuration
2. Check system requirements
3. Check for existing installation (handle force reinstall)
4. Initialize development environment (bench init)
5. Download applications
6. Configure database connection (common_site_config.json)
7. Start development server (Redis required for site creation)
8. Create site and database schema (Frappe creates user = schema name)
9. Install applications
10. Output team credentials
"""

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
    """Run administrator setup to create a new site.

    Creates a fully configured Frappe site with:
    - Database schema (isolated within shared database)
    - Schema-owner user (for admin/migrations)
    - Runtime user (for team members, limited privileges)
    - Installed applications

    Args:
        config: Pre-loaded configuration, or None to load from environment.

    Raises:
        SystemExit: On validation or setup failures.
    """
    console.print(
        Panel.fit("🔧 Realtimex Frappe Setup", style="bold blue")
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Step 1: Validate configuration
    # ─────────────────────────────────────────────────────────────────────────
    console.print("\n[bold]Checking environment...[/bold]")

    if config is None:
        missing = get_missing_required_env_vars()
        if missing:
            console.print("[red]✗ Missing required settings:[/red]")
            for var in missing:
                console.print(f"  • {var}")
            console.print("\n[dim]Run 'realtimex-frappe env-help' for details[/dim]")
            print_env_var_help()
            raise SystemExit(1)

        config = config_from_environment()

    # Mode validation
    if config.mode != RunMode.ADMIN:
        console.print("[red]✗ Setup requires REALTIMEX_MODE=admin[/red]")
        raise SystemExit(1)

    # Schema validation
    if not config.database.schema:
        console.print("[red]✗ Setup requires REALTIMEX_DB_SCHEMA[/red]")
        raise SystemExit(1)

    # Admin credentials validation
    if not config.database.admin_user or not config.database.admin_password:
        console.print("[red]✗ Setup requires admin database credentials[/red]")
        console.print("[dim]Set REALTIMEX_ADMIN_DB_USER and REALTIMEX_ADMIN_DB_PASSWORD[/dim]")
        raise SystemExit(1)

    console.print("[green]✓[/green] All required settings found")
    console.print(f"  Site: [cyan]{config.site.name}[/cyan]")
    console.print(f"  Database: [cyan]{config.database.host}[/cyan]")
    console.print(f"  Schema: [cyan]{config.database.schema}[/cyan]")

    # ─────────────────────────────────────────────────────────────────────────
    # Step 2: Check system requirements
    # ─────────────────────────────────────────────────────────────────────────
    console.print("\n[bold]Checking system requirements...[/bold]")

    prereqs, binaries = validate_all_prerequisites(config)

    if not prereqs.is_valid:
        console.print(f"[red]✗ Missing: {', '.join(prereqs.missing)}[/red]")
        for prereq in prereqs.missing:
            hint = get_prerequisite_install_hint(prereq)
            if hint:
                console.print(f"  [dim]{prereq}: {hint}[/dim]")
        raise SystemExit(1)

    if not binaries.is_valid:
        console.print(f"[red]✗ Missing binaries: {', '.join(binaries.missing)}[/red]")
        console.print("[dim]Set REALTIMEX_NODE_BIN_DIR to your Node.js installation[/dim]")
        raise SystemExit(1)

    console.print(f"[green]✓[/green] Python, Node.js, Redis available")

    # ─────────────────────────────────────────────────────────────────────────
    # Step 3: Check for existing installation
    # ─────────────────────────────────────────────────────────────────────────
    from pathlib import Path
    import shutil

    bench_path = Path(config.bench.path)

    if bench_path.exists():
        if config.force_reinstall:
            console.print(f"\n[yellow]Force reinstall enabled. Removing existing installation...[/yellow]")
            try:
                shutil.rmtree(bench_path)
                console.print(f"[green]✓[/green] Removed {bench_path}")
            except Exception as e:
                console.print(f"[red]✗ Failed to remove {bench_path}: {e}[/red]")
                raise SystemExit(1)
        elif site_exists(config):
            # Site exists - check if it's healthy
            console.print(f"\n[yellow]Existing installation found at {bench_path}[/yellow]")
            console.print(f"  Site '{config.site.name}' already exists.")
            console.print("")
            console.print("[bold]To force reinstall, set:[/bold]")
            console.print("  [cyan]export REALTIMEX_FORCE_REINSTALL=true[/cyan]")
            console.print("")
            console.print("[bold]Or delete manually:[/bold]")
            console.print(f"  [cyan]rm -rf {bench_path}[/cyan]")
            raise SystemExit(1)

    # ─────────────────────────────────────────────────────────────────────────
    # Step 4: Initialize development environment
    # ─────────────────────────────────────────────────────────────────────────
    console.print("\n[bold]Setting up development environment...[/bold]")

    if bench_exists(config):
        console.print("[green]✓[/green] Frappe framework ready")
    else:
        ensure_bench_directory()
        console.print("[dim]Initializing Frappe framework...[/dim]")
        if not init_bench(config):
            console.print("[red]✗ Failed to initialize framework[/red]")
            raise SystemExit(1)
        console.print("[green]✓[/green] Frappe framework ready")

    # ─────────────────────────────────────────────────────────────────────────
    # Step 5: Download applications
    # ─────────────────────────────────────────────────────────────────────────
    console.print("\n[bold]Downloading applications...[/bold]")

    if not get_all_apps(config):
        console.print("[red]✗ Failed to download applications[/red]")
        raise SystemExit(1)

    app_names = [app.name for app in config.apps] if config.apps else []
    console.print(f"[green]✓[/green] Applications ready: {', '.join(app_names) or 'frappe'}")

    # ─────────────────────────────────────────────────────────────────────────
    # Step 6: Configure database connection
    # ─────────────────────────────────────────────────────────────────────────
    console.print("\n[bold]Configuring database connection...[/bold]")

    update_common_site_config(config)
    console.print(f"[green]✓[/green] Connected to {config.database.host}")

    # ─────────────────────────────────────────────────────────────────────────
    # Step 7: Start bench (Redis required for site creation)
    # ─────────────────────────────────────────────────────────────────────────
    console.print("\n[bold]Starting development server...[/bold]")
    console.print("[dim]Redis must be running for site creation and app installation[/dim]")

    bench_proc = run_bench_start_subprocess(config)
    try:
        import time

        # Wait for bench (including Redis) to be ready
        time.sleep(5)
        console.print("[green]✓[/green] Development server started")

        # ─────────────────────────────────────────────────────────────────────
        # Step 8: Create site and database schema
        # ─────────────────────────────────────────────────────────────────────
        console.print("\n[bold]Creating site...[/bold]")

        if site_exists(config):
            healthy, reason = site_is_healthy(config)
            if healthy:
                console.print(f"[green]✓[/green] Site '{config.site.name}' exists")
            else:
                console.print(f"[yellow]⚠ Recreating unhealthy site ({reason})...[/yellow]")
                if not create_site(config, force=True):
                    console.print("[red]✗ Failed to create site[/red]")
                    raise SystemExit(1)
                console.print(f"[green]✓[/green] Site '{config.site.name}' recreated")
        else:
            console.print(f"[dim]Creating site '{config.site.name}' with schema '{config.database.schema}'...[/dim]")
            if not create_site(config):
                console.print("[red]✗ Failed to create site[/red]")
                raise SystemExit(1)
            console.print(f"[green]✓[/green] Site '{config.site.name}' created with database schema")

        # ─────────────────────────────────────────────────────────────────────
        # Step 9: Install applications
        # ─────────────────────────────────────────────────────────────────────
        if config.apps:
            console.print("\n[bold]Installing applications...[/bold]")

            if not install_apps_on_site(config):
                console.print("[red]✗ Failed to install applications[/red]")
                raise SystemExit(1)

            console.print(f"[green]✓[/green] {', '.join(app_names)} installed")

    finally:
        # Stop the temporary bench process
        console.print("[dim]Stopping development server...[/dim]")
        bench_proc.terminate()
        try:
            bench_proc.wait(timeout=10)
        except Exception:
            bench_proc.kill()

    # ─────────────────────────────────────────────────────────────────────────
    # Step 10: Output team credentials
    # ─────────────────────────────────────────────────────────────────────────
    # Frappe creates a user named after the schema (e.g., mysite_schema)
    # with the password provided via REALTIMEX_DB_PASSWORD
    site_db_user = config.database.schema  # Frappe's design: user = schema name

    console.print("\n" + "=" * 60)
    console.print("[bold green]✓ Setup complete![/bold green]")
    console.print("\n[bold]Share these with your team:[/bold]\n")

    env_block = f"""export REALTIMEX_MODE=user
export REALTIMEX_SITE_NAME={config.site.name}
export REALTIMEX_DB_HOST={config.database.host}
export REALTIMEX_DB_PORT={config.database.port}
export REALTIMEX_DB_NAME={config.database.name}
export REALTIMEX_DB_SCHEMA={config.database.schema}
export REALTIMEX_DB_USER={site_db_user}
export REALTIMEX_DB_PASSWORD={config.database.password}"""

    console.print(f"[cyan]{env_block}[/cyan]")
    console.print(f"\n[dim]Run: realtimex-frappe run[/dim]")
    console.print(f"[dim]URL: http://{config.site.name}:{config.bench.port}[/dim]")

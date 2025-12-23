"""New site command implementation."""

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel

from ..config.loader import load_config, merge_config_with_cli
from ..config.schema import RealtimexConfig
from ..utils.bench import (
    bench_exists,
    create_site,
    init_bench,
    install_all_apps,
    update_common_site_config,
)
from ..utils.environment import validate_binaries

console = Console()


def create_new_site(
    config_path: Optional[str] = None,
    site_name: Optional[str] = None,
    admin_password: Optional[str] = None,
    db_host: Optional[str] = None,
    db_port: Optional[int] = None,
    db_name: Optional[str] = None,
    db_user: Optional[str] = None,
    db_password: Optional[str] = None,
    bench_path: Optional[str] = None,
) -> bool:
    """Create a new Frappe site with all configured apps.

    This orchestrates the full site creation flow:
    1. Load and merge configuration
    2. Validate required binaries
    3. Initialize bench (if needed)
    4. Update common_site_config.json
    5. Create the site
    6. Install all configured apps

    Args:
        config_path: Path to the configuration JSON file.
        site_name: Site name (overrides config).
        admin_password: Admin password (overrides config).
        db_host: Database host (overrides config).
        db_port: Database port (overrides config).
        db_name: Database name (overrides config).
        db_user: Database user (overrides config).
        db_password: Database password (overrides config).
        bench_path: Bench path (overrides config).

    Returns:
        True if site creation succeeded, False otherwise.
    """
    console.print(Panel.fit("🚀 Realtimex Frappe - New Site Setup", style="bold blue"))

    # Step 1: Load configuration
    console.print("\n[bold]Step 1:[/bold] Loading configuration...")

    config: Optional[RealtimexConfig] = None
    if config_path:
        try:
            config = load_config(config_path)
            console.print(f"[green]✓[/green] Loaded config from {config_path}")
        except Exception as e:
            console.print(f"[red]✗ Failed to load config: {e}[/red]")
            return False

    # Merge with CLI options
    config = merge_config_with_cli(
        config,
        site_name=site_name,
        admin_password=admin_password,
        db_host=db_host,
        db_port=db_port,
        db_name=db_name,
        db_user=db_user,
        db_password=db_password,
        bench_path=bench_path,
    )

    # Validate required fields
    if not config.site.name:
        console.print("[red]✗ Site name is required[/red]")
        return False

    if not config.site.admin_password:
        console.print("[red]✗ Admin password is required[/red]")
        return False

    if not config.database.name:
        console.print("[red]✗ Database name is required[/red]")
        return False

    console.print(f"  Site: [cyan]{config.site.name}[/cyan]")
    console.print(f"  Bench: [cyan]{config.bench.path}[/cyan]")
    console.print(f"  Database: [cyan]{config.database.host}:{config.database.port}/{config.database.name}[/cyan]")

    # Step 2: Validate binaries
    console.print("\n[bold]Step 2:[/bold] Validating binaries...")

    # Determine which binaries to check
    # wkhtmltopdf is optional for initial setup
    required = ["node", "npm"]
    optional = ["yarn", "wkhtmltopdf"]

    result = validate_binaries(config, required)
    if not result.is_valid:
        console.print(f"[red]✗ Missing required binaries: {', '.join(result.missing)}[/red]")
        console.print("\n[yellow]Hint: Configure binary paths in your config file:[/yellow]")
        console.print('[dim]  "binaries": { "node": { "bin_dir": "/path/to/node/bin" } }[/dim]')
        return False

    console.print(f"[green]✓[/green] Required binaries available: {', '.join(result.available)}")

    # Check optional binaries
    opt_result = validate_binaries(config, optional)
    if opt_result.missing:
        console.print(f"[yellow]⚠[/yellow] Optional binaries missing: {', '.join(opt_result.missing)}")
    if opt_result.available:
        console.print(f"[green]✓[/green] Optional binaries available: {', '.join(opt_result.available)}")

    # Step 3: Initialize bench (if needed)
    console.print("\n[bold]Step 3:[/bold] Setting up bench...")

    if bench_exists(config):
        console.print(f"[green]✓[/green] Using existing bench at {config.bench.path}")
    else:
        if not init_bench(config):
            console.print("[red]✗ Failed to initialize bench[/red]")
            return False
        console.print("[green]✓[/green] Bench initialized")

    # Step 4: Update common_site_config.json
    console.print("\n[bold]Step 4:[/bold] Configuring site settings...")

    update_common_site_config(config)

    # Step 5: Create site
    console.print("\n[bold]Step 5:[/bold] Creating site...")

    if not create_site(config):
        console.print("[red]✗ Failed to create site[/red]")
        return False

    console.print(f"[green]✓[/green] Site {config.site.name} created")

    # Step 6: Install apps
    if config.apps:
        console.print("\n[bold]Step 6:[/bold] Installing apps...")

        if not install_all_apps(config):
            console.print("[red]✗ Failed to install apps[/red]")
            return False

        console.print("[green]✓[/green] All apps installed")
    else:
        console.print("\n[bold]Step 6:[/bold] No apps configured, skipping...")

    # Success!
    console.print("\n" + "=" * 50)
    console.print(Panel.fit("✅ Site created successfully!", style="bold green"))
    console.print("\n[bold]Next steps:[/bold]")
    console.print(f"  1. cd {config.bench.path}")
    console.print("  2. bench start")
    console.print(f"  3. Open http://{config.site.name}:8000")

    return True

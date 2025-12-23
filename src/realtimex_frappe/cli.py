"""CLI entry point for realtimex-frappe."""

from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from . import __version__
from .config.loader import load_config, write_default_config
from .utils.environment import get_binary_path, validate_binaries

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="realtimex-frappe")
def main():
    """Realtimex Frappe - Streamlined Frappe/ERPNext site setup.

    A CLI tool to create and configure Frappe sites with ERPNext,
    supporting PostgreSQL (including Supabase), external Redis,
    and bundled Node.js/wkhtmltopdf binaries.
    """
    pass


@main.command("init-config")
@click.option(
    "--output",
    "-o",
    default="./realtimex.json",
    help="Output path for the configuration file.",
)
def init_config(output: str):
    """Generate a default configuration file.

    Creates a JSON configuration file with default settings that you
    can customize for your environment.

    Example:
        realtimex-frappe init-config -o ./my-config.json
    """
    from pathlib import Path

    path = Path(output)

    if path.exists():
        if not click.confirm(f"{output} already exists. Overwrite?"):
            console.print("[yellow]Aborted.[/yellow]")
            return

    write_default_config(output)
    console.print(f"[green]✓[/green] Configuration file created at: [cyan]{output}[/cyan]")
    console.print("\n[dim]Edit this file to configure:[/dim]")
    console.print("  • Database credentials (PostgreSQL/Supabase)")
    console.print("  • Bundled binary paths (Node.js, wkhtmltopdf)")
    console.print("  • Apps to install (ERPNext, custom apps)")
    console.print("  • Redis connection settings")


@main.command("validate")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    required=True,
    help="Path to the configuration JSON file.",
)
def validate_config(config: str):
    """Validate configuration and check for required binaries.

    Checks that:
    - The configuration file is valid JSON
    - All required binaries (node, npm, yarn, wkhtmltopdf) are available
    - Binary paths in the config are correct

    Example:
        realtimex-frappe validate --config ./my-config.json
    """
    console.print("[bold]Validating configuration...[/bold]\n")

    # Load config
    try:
        cfg = load_config(config)
        console.print(f"[green]✓[/green] Configuration loaded from [cyan]{config}[/cyan]")
    except Exception as e:
        console.print(f"[red]✗ Failed to load configuration: {e}[/red]")
        raise click.Abort()

    # Show config summary
    console.print("\n[bold]Configuration Summary:[/bold]")
    console.print(f"  Frappe branch: [cyan]{cfg.frappe.branch}[/cyan]")
    console.print(f"  Apps to install: [cyan]{len(cfg.apps)}[/cyan]")
    console.print(f"  Database type: [cyan]{cfg.database.type}[/cyan]")
    console.print(f"  Redis URL: [cyan]{cfg.redis.url}[/cyan]")

    # Check binaries
    console.print("\n[bold]Checking binaries...[/bold]")

    required_binaries = ["node", "npm"]
    optional_binaries = ["yarn", "wkhtmltopdf"]

    # Create a table for binary status
    table = Table(show_header=True, header_style="bold")
    table.add_column("Binary")
    table.add_column("Status")
    table.add_column("Path")

    all_binaries = required_binaries + optional_binaries

    for binary in all_binaries:
        path = get_binary_path(binary, cfg)
        is_required = binary in required_binaries

        if path:
            status = "[green]✓ Found[/green]"
            path_display = f"[dim]{path}[/dim]"
        else:
            if is_required:
                status = "[red]✗ Missing (required)[/red]"
            else:
                status = "[yellow]⚠ Missing (optional)[/yellow]"
            path_display = "[dim]-[/dim]"

        table.add_row(binary, status, path_display)

    console.print(table)

    # Final result
    result = validate_binaries(cfg, required_binaries)
    if result.is_valid:
        console.print("\n[green]✓ All required binaries found[/green]")
    else:
        console.print(f"\n[red]✗ Missing required binaries: {', '.join(result.missing)}[/red]")
        console.print("\n[yellow]Hint: Configure binary paths in your config file:[/yellow]")
        console.print('[dim]  "binaries": { "node": { "bin_dir": "/path/to/node/bin" } }[/dim]')
        raise click.Abort()


@main.command("new-site")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to configuration JSON file.",
)
@click.option(
    "--site-name",
    prompt="Site name",
    help="Name for the new site (e.g., mysite.localhost).",
)
@click.option(
    "--admin-password",
    prompt="Admin password",
    hide_input=True,
    confirmation_prompt=True,
    help="Administrator password for the site.",
)
@click.option(
    "--db-host",
    prompt="Database host",
    default="localhost",
    help="PostgreSQL host (e.g., localhost or db.xxx.supabase.co).",
)
@click.option(
    "--db-port",
    prompt="Database port",
    default=5432,
    type=int,
    help="PostgreSQL port.",
)
@click.option(
    "--db-name",
    prompt="Database name",
    help="PostgreSQL database name.",
)
@click.option(
    "--db-user",
    prompt="Database user",
    help="PostgreSQL username.",
)
@click.option(
    "--db-password",
    prompt="Database password",
    hide_input=True,
    help="PostgreSQL password.",
)
@click.option(
    "--bench-path",
    default="./frappe-bench",
    help="Path for the bench installation.",
)
def new_site(
    config: Optional[str],
    site_name: str,
    admin_password: str,
    db_host: str,
    db_port: int,
    db_name: str,
    db_user: str,
    db_password: str,
    bench_path: str,
):
    """Create a new Frappe site with ERPNext.

    This command will:
    1. Initialize a new bench (if needed)
    2. Configure Redis and database settings
    3. Create a new Frappe site
    4. Install ERPNext and any other configured apps

    Example:
        realtimex-frappe new-site --config ./my-config.json
    """
    from .commands.new_site import create_new_site

    success = create_new_site(
        config_path=config,
        site_name=site_name,
        admin_password=admin_password,
        db_host=db_host,
        db_port=db_port,
        db_name=db_name,
        db_user=db_user,
        db_password=db_password,
        bench_path=bench_path,
    )

    if not success:
        raise click.Abort()


@main.command("run")
def run():
    """Set up and start a Frappe site (production mode).

    This is the primary command for production use. It reads configuration
    from environment variables, sets up the site if needed, and starts the
    bench server.

    Required environment variables:
        REALTIMEX_SITE_NAME: Site name (e.g., mysite.localhost)
        REALTIMEX_ADMIN_PASSWORD: Administrator password
        REALTIMEX_DB_NAME: PostgreSQL database name
        REALTIMEX_DB_USER: PostgreSQL username
        REALTIMEX_DB_PASSWORD: PostgreSQL password

    Optional environment variables:
        REALTIMEX_DB_HOST: PostgreSQL host (default: localhost)
        REALTIMEX_DB_PORT: PostgreSQL port (default: 5432)
        REALTIMEX_REDIS_HOST: Redis host (default: 127.0.0.1)
        REALTIMEX_REDIS_PORT: Redis port (default: 6379)
        REALTIMEX_BENCH_PATH: Bench path (default: ./frappe-bench)
        REALTIMEX_NODE_BIN_DIR: Path to Node.js bin directory
        REALTIMEX_FRAPPE_BRANCH: Frappe branch (default: version-15)

    Example:
        REALTIMEX_SITE_NAME=mysite.localhost \\
        REALTIMEX_ADMIN_PASSWORD=secret \\
        REALTIMEX_DB_NAME=mysite \\
        REALTIMEX_DB_USER=postgres \\
        REALTIMEX_DB_PASSWORD=postgres \\
        uvx realtimex-frappe run
    """
    from .commands.run import run_setup_and_start

    run_setup_and_start()


@main.command("env-help")
def env_help():
    """Show available environment variables.

    Lists all environment variables that can be used to configure
    the 'run' command, along with their default values and descriptions.

    Example:
        realtimex-frappe env-help
    """
    from .config.env import print_env_var_help

    console.print("[bold]Environment Variables for 'realtimex-frappe run'[/bold]\n")
    print_env_var_help()
    console.print("\n[dim]Example usage:[/dim]")
    console.print('''
[cyan]REALTIMEX_SITE_NAME[/cyan]=mysite.localhost \\
[cyan]REALTIMEX_ADMIN_PASSWORD[/cyan]=secret \\
[cyan]REALTIMEX_DB_NAME[/cyan]=mysite \\
[cyan]REALTIMEX_DB_USER[/cyan]=postgres \\
[cyan]REALTIMEX_DB_PASSWORD[/cyan]=postgres \\
uvx realtimex-frappe run
''')


if __name__ == "__main__":
    main()


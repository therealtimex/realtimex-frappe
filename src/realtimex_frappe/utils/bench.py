"""Bench command wrapper utilities."""

import json
import subprocess
from pathlib import Path
from typing import Optional

from rich.console import Console

from ..config.schema import RealtimexConfig
from .environment import build_environment

console = Console()


def run_bench_command(
    args: list[str],
    config: RealtimexConfig,
    cwd: Path | str | None = None,
    capture_output: bool = False,
) -> subprocess.CompletedProcess:
    """Run a bench command with custom environment (bundled binaries in PATH).

    Args:
        args: Arguments to pass to bench (e.g., ["init", "path"]).
        config: The realtimex configuration.
        cwd: Working directory for the command.
        capture_output: Whether to capture stdout/stderr.

    Returns:
        The completed process result.
    """
    env = build_environment(config)
    cmd = ["bench"] + args

    console.print(f"[dim]$ {' '.join(cmd)}[/dim]")

    return subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        capture_output=capture_output,
        text=True,
    )


def init_bench(config: RealtimexConfig) -> bool:
    """Initialize a new bench with external Redis and bundled binaries.

    Args:
        config: The realtimex configuration.

    Returns:
        True if initialization succeeded, False otherwise.
    """
    args = [
        "init",
        config.bench.path,
        "--frappe-branch",
        config.frappe.branch,
        "--frappe-path",
        config.frappe.repo,
    ]

    if config.bench.developer_mode:
        args.append("--dev")

    console.print("[blue]Initializing bench...[/blue]")
    result = run_bench_command(args, config)
    return result.returncode == 0


def update_common_site_config(config: RealtimexConfig) -> None:
    """Update common_site_config.json with Redis, DB, and port settings.

    Writes directly to the JSON file rather than using 'bench config'
    command, which fails on Redis URLs containing '://' due to
    ast.literal_eval in the bench library.

    After writing the config, regenerates derived config files (Procfile,
    redis configs) to ensure they match.

    Args:
        config: The realtimex configuration.
    """
    bench_path = Path(config.bench.path)
    config_path = bench_path / "sites" / "common_site_config.json"

    # Load existing config or start fresh
    site_config: dict = {}
    if config_path.exists():
        with open(config_path) as f:
            site_config = json.load(f)

    # Set Redis URLs (separate ports for cache and queue)
    cache_url = config.redis.cache_url
    queue_url = config.redis.queue_url
    console.print(f"[dim]Setting Redis cache URL: {cache_url}[/dim]")
    console.print(f"[dim]Setting Redis queue URL: {queue_url}[/dim]")

    site_config.update(
        {
            "redis_cache": cache_url,
            "redis_queue": queue_url,
            "redis_socketio": cache_url,  # socketio uses cache port
        }
    )

    # Set webserver port
    site_config["webserver_port"] = config.bench.port

    # Set PostgreSQL config
    if config.database.type == "postgres":
        site_config.update(
            {
                "db_host": config.database.host,
                "db_port": config.database.port,
            }
        )
        # Set db_schema for schema-based isolation (Supabase compatibility)
        if config.database.schema:
            site_config["db_schema"] = config.database.schema

    # Write config
    with open(config_path, "w") as f:
        json.dump(site_config, f, indent=2)

    console.print(f"[green]✓[/green] Updated common_site_config.json")
    console.print(f"[dim]  Redis cache: {cache_url}[/dim]")
    console.print(f"[dim]  Redis queue: {queue_url}[/dim]")
    console.print(f"[dim]  Port: {config.bench.port}[/dim]")
    if config.database.schema:
        console.print(f"[dim]  DB Schema: {config.database.schema} (schema-based isolation enabled)[/dim]")
    console.print(f"[dim]  DB Host: {config.database.host}:{config.database.port}[/dim]")

    # Regenerate derived config files to match common_site_config.json
    regenerate_bench_config(config)


def regenerate_bench_config(config: RealtimexConfig) -> None:
    """Regenerate Bench config files after updating common_site_config.json.

    This ensures:
    - Procfile has correct webserver_port and includes Redis
    - Redis .conf files have correct ports (if not using external Redis)

    Uses Bench's built-in functions for best practice compliance.

    Args:
        config: The realtimex configuration.
    """
    from bench.config.procfile import setup_procfile

    bench_path = config.bench.path

    # Regenerate Redis configs if not using external Redis
    # When use_external=True, we use the external Redis URL from config
    # but still include Redis in Procfile for local development
    if not config.redis.use_external:
        from bench.config.redis import generate_config as generate_redis_config
        console.print("[dim]Regenerating Redis configs...[/dim]")
        generate_redis_config(bench_path)
    else:
        # For external Redis, still regenerate configs to match the URL
        from bench.config.redis import generate_config as generate_redis_config
        console.print("[dim]Regenerating Redis configs for external Redis...[/dim]")
        generate_redis_config(bench_path)

    # Always include Redis in Procfile - bench manages Redis startup
    # skip_redis=False means Redis will be started by bench
    console.print("[dim]Regenerating Procfile...[/dim]")
    setup_procfile(bench_path, yes=True, skip_redis=False)

    console.print(f"[green]✓[/green] Regenerated Bench config files")




def create_site(config: RealtimexConfig, force: bool = False) -> bool:
    """Create a new Frappe site.

    Uses provided credentials as root credentials to create the database
    and user. Frappe's setup_database() will:
    1. Create user if not exists (or update password)
    2. Create database
    3. Grant permissions

    Args:
        config: The realtimex configuration.
        force: If True, recreate site even if it exists (for recovery).

    Returns:
        True if site creation succeeded, False otherwise.
    """
    if not config.site.name:
        console.print("[red]✗ Site name is required[/red]")
        return False

    if not config.site.admin_password:
        console.print("[red]✗ Admin password is required[/red]")
        return False

    bench_path = Path(config.bench.path)

    args = [
        "new-site",
        config.site.name,
        "--admin-password",
        config.site.admin_password,
    ]

    # Force recreate if recovering from partial state
    if force:
        args.append("--force")

    # Database type
    if config.database.type:
        args.extend(["--db-type", config.database.type])

    # Database connection settings
    if config.database.host:
        args.extend(["--db-host", config.database.host])
    if config.database.port:
        args.extend(["--db-port", str(config.database.port)])
    if config.database.name:
        args.extend(["--db-name", config.database.name])

    # Pass credentials as root credentials for database setup
    # Frappe will use these to create the database and user
    if config.database.user:
        args.extend(["--db-root-username", config.database.user])
    if config.database.password:
        args.extend(["--db-root-password", config.database.password])

    console.print(f"[blue]Creating site {config.site.name}...[/blue]")
    result = run_bench_command(args, config, cwd=bench_path)
    return result.returncode == 0


def get_app(
    config: RealtimexConfig,
    app_url: str,
    branch: str,
) -> bool:
    """Get (clone) an app into the bench.

    Args:
        config: The realtimex configuration.
        app_url: URL of the app repository.
        branch: Branch to checkout.

    Returns:
        True if successful, False otherwise.
    """
    bench_path = Path(config.bench.path)

    args = [
        "get-app",
        app_url,
        "--branch",
        branch,
    ]

    result = run_bench_command(args, config, cwd=bench_path)
    return result.returncode == 0


def install_app(
    config: RealtimexConfig,
    app_name: str,
) -> bool:
    """Install an app on the configured site.

    Args:
        config: The realtimex configuration.
        app_name: Name of the app to install.

    Returns:
        True if successful, False otherwise.
    """
    if not config.site.name:
        console.print("[red]✗ Site name is required[/red]")
        return False

    bench_path = Path(config.bench.path)

    args = [
        "--site",
        config.site.name,
        "install-app",
        app_name,
    ]

    result = run_bench_command(args, config, cwd=bench_path)
    return result.returncode == 0


def install_all_apps(config: RealtimexConfig) -> bool:
    """Get and install all apps from configuration.

    Args:
        config: The realtimex configuration.

    Returns:
        True if all apps were installed successfully, False otherwise.
    """
    for app in config.apps:
        if not app.install:
            console.print(f"[dim]Skipping {app.name} (install=false)[/dim]")
            continue

        # Get the app
        console.print(f"[blue]Getting {app.name}...[/blue]")
        if not get_app(config, app.url, app.branch):
            console.print(f"[red]✗ Failed to get {app.name}[/red]")
            return False

        # Install on site
        console.print(f"[blue]Installing {app.name} on {config.site.name}...[/blue]")
        if not install_app(config, app.name):
            console.print(f"[red]✗ Failed to install {app.name}[/red]")
            return False

        console.print(f"[green]✓[/green] Installed {app.name}")

    return True


def get_all_apps(config: RealtimexConfig) -> bool:
    """Get (clone) all apps from configuration without installing.

    This step only clones the app repositories into the bench.
    Use install_apps_on_site() after bench start to install them.

    Args:
        config: The realtimex configuration.

    Returns:
        True if all apps were cloned successfully, False otherwise.
    """
    for app in config.apps:
        if not app.install:
            console.print(f"[dim]Skipping {app.name} (install=false)[/dim]")
            continue

        # Check if app already exists
        bench_path = Path(config.bench.path)
        app_path = bench_path / "apps" / app.name
        if app_path.exists():
            console.print(f"[green]✓[/green] App {app.name} already exists")
            continue

        console.print(f"[blue]Getting {app.name}...[/blue]")
        if not get_app(config, app.url, app.branch):
            console.print(f"[red]✗ Failed to get {app.name}[/red]")
            return False

        console.print(f"[green]✓[/green] Got {app.name}")

    return True


def install_apps_on_site(config: RealtimexConfig) -> bool:
    """Install all apps on the site (requires bench to be running).

    This step installs apps that have been cloned but not yet installed.
    Should be called after bench start.

    Args:
        config: The realtimex configuration.

    Returns:
        True if all apps were installed successfully, False otherwise.
    """
    for app in config.apps:
        if not app.install:
            continue

        console.print(f"[blue]Installing {app.name} on {config.site.name}...[/blue]")
        if not install_app(config, app.name):
            console.print(f"[red]✗ Failed to install {app.name}[/red]")
            return False

        console.print(f"[green]✓[/green] Installed {app.name}")

    return True


def bench_exists(config: RealtimexConfig) -> bool:
    """Check if the bench directory already exists.

    Args:
        config: The realtimex configuration.

    Returns:
        True if the bench directory exists and appears valid.
    """
    bench_path = Path(config.bench.path)
    return (bench_path / "sites").exists() and (bench_path / "apps").exists()


def site_exists(config: RealtimexConfig) -> bool:
    """Check if the site directory exists.

    Args:
        config: The realtimex configuration.

    Returns:
        True if the site directory exists.
    """
    if not config.site.name:
        return False

    bench_path = Path(config.bench.path)
    site_path = bench_path / "sites" / config.site.name

    return site_path.exists()


def site_is_healthy(config: RealtimexConfig) -> tuple[bool, str]:
    """Check if site is properly configured.

    Performs multi-level validation:
    1. Site directory exists
    2. site_config.json exists and is valid JSON
    3. site_config.json contains required db_name field

    Args:
        config: The realtimex configuration.

    Returns:
        Tuple of (is_healthy, reason).
        Reasons: 'healthy', 'not_found', 'missing_config', 'invalid_config', 'incomplete_config'
    """
    if not config.site.name:
        return False, "not_found"

    bench_path = Path(config.bench.path)
    site_path = bench_path / "sites" / config.site.name

    # Level 1: Site directory exists
    if not site_path.exists():
        return False, "not_found"

    # Level 2: site_config.json exists
    config_file = site_path / "site_config.json"
    if not config_file.exists():
        return False, "missing_config"

    # Level 3: site_config.json is valid and has db_name
    try:
        with open(config_file) as f:
            site_cfg = json.load(f)
        if not site_cfg.get("db_name"):
            return False, "incomplete_config"
    except (json.JSONDecodeError, OSError):
        return False, "invalid_config"

    return True, "healthy"


def start_bench(config: RealtimexConfig) -> None:
    """Start the bench server (blocking).

    This function does not return - it replaces the current process
    with the bench start command.

    Args:
        config: The realtimex configuration.
    """
    import os
    import sys

    bench_path = Path(config.bench.path).resolve()
    env = build_environment(config)

    console.print(f"\n[bold green]Starting bench at {bench_path}...[/bold green]")
    console.print(f"[dim]Site will be available at: http://{config.site.name}:{config.bench.port}[/dim]\n")

    # Change to bench directory and exec bench start
    os.chdir(bench_path)

    # Use os.execvpe to replace the current process with bench start
    # This ensures the process keeps running and handles signals properly
    os.execvpe("bench", ["bench", "start"], env)


def run_bench_start_subprocess(config: RealtimexConfig) -> subprocess.Popen:
    """Start the bench server as a subprocess.

    Args:
        config: The realtimex configuration.

    Returns:
        The subprocess.Popen object for the running bench.
    """
    bench_path = Path(config.bench.path).resolve()
    env = build_environment(config)

    console.print(f"\n[bold green]Starting bench at {bench_path}...[/bold green]")
    console.print(f"[dim]Site will be available at: http://{config.site.name}:{config.bench.port}[/dim]\n")

    return subprocess.Popen(
        ["bench", "start"],
        cwd=bench_path,
        env=env,
    )


"""Environment variable configuration support."""

import os
from typing import Optional

from .schema import RealtimexConfig, AppConfig


# Environment variable prefix
ENV_PREFIX = "REALTIMEX_"

# Environment variable names
ENV_SITE_NAME = f"{ENV_PREFIX}SITE_NAME"
ENV_SITE_PASSWORD = f"{ENV_PREFIX}SITE_PASSWORD"
ENV_DB_TYPE = f"{ENV_PREFIX}DB_TYPE"
ENV_DB_HOST = f"{ENV_PREFIX}DB_HOST"
ENV_DB_PORT = f"{ENV_PREFIX}DB_PORT"
ENV_DB_NAME = f"{ENV_PREFIX}DB_NAME"
ENV_DB_USER = f"{ENV_PREFIX}DB_USER"
ENV_DB_PASSWORD = f"{ENV_PREFIX}DB_PASSWORD"
ENV_DB_SCHEMA = f"{ENV_PREFIX}DB_SCHEMA"
ENV_ADMIN_DB_USER = f"{ENV_PREFIX}ADMIN_DB_USER"
ENV_ADMIN_DB_PASSWORD = f"{ENV_PREFIX}ADMIN_DB_PASSWORD"
ENV_REDIS_HOST = f"{ENV_PREFIX}REDIS_HOST"
ENV_REDIS_CACHE_PORT = f"{ENV_PREFIX}REDIS_CACHE_PORT"
ENV_REDIS_QUEUE_PORT = f"{ENV_PREFIX}REDIS_QUEUE_PORT"
ENV_BENCH_PATH = f"{ENV_PREFIX}BENCH_PATH"
ENV_PORT = f"{ENV_PREFIX}PORT"
ENV_NODE_BIN_DIR = f"{ENV_PREFIX}NODE_BIN_DIR"
ENV_WKHTMLTOPDF_BIN_DIR = f"{ENV_PREFIX}WKHTMLTOPDF_BIN_DIR"
ENV_FRAPPE_BRANCH = f"{ENV_PREFIX}FRAPPE_BRANCH"
ENV_DEVELOPER_MODE = f"{ENV_PREFIX}DEVELOPER_MODE"
ENV_MODE = f"{ENV_PREFIX}MODE"
ENV_FORCE_REINSTALL = f"{ENV_PREFIX}FORCE_REINSTALL"


def get_env_or_none(key: str) -> Optional[str]:
    """Get environment variable or None if not set or empty."""
    value = os.environ.get(key, "").strip()
    return value if value else None


def get_env_int(key: str, default: Optional[int] = None) -> Optional[int]:
    """Get environment variable as integer."""
    value = get_env_or_none(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_env_bool(key: str, default: bool = False) -> bool:
    """Get environment variable as boolean."""
    value = get_env_or_none(key)
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes", "on")


def config_from_environment() -> RealtimexConfig:
    """Create a configuration from environment variables.

    Environment variables:
        REALTIMEX_SITE_NAME: Name of the site (e.g., mysite.localhost)
        REALTIMEX_ADMIN_PASSWORD: Administrator password
        REALTIMEX_DB_TYPE: Database type (postgres or mariadb)
        REALTIMEX_DB_HOST: Database host
        REALTIMEX_DB_PORT: Database port
        REALTIMEX_DB_NAME: Database name
        REALTIMEX_DB_USER: Database username
        REALTIMEX_DB_PASSWORD: Database password
        REALTIMEX_REDIS_HOST: Redis host (default: 127.0.0.1)
        REALTIMEX_REDIS_PORT: Redis port (default: 6379)
        REALTIMEX_BENCH_PATH: Path for bench installation (default: ~/.realtimex.ai/storage/local-apps/frappe-bench)
        REALTIMEX_NODE_BIN_DIR: Path to Node.js bin directory
        REALTIMEX_WKHTMLTOPDF_BIN_DIR: Path to wkhtmltopdf bin directory
        REALTIMEX_FRAPPE_BRANCH: Frappe branch (default: version-15)
        REALTIMEX_DEVELOPER_MODE: Enable developer mode (default: true)

    Returns:
        RealtimexConfig populated from environment variables.
    """
    from .loader import get_default_config

    # Start with default config
    config = get_default_config()
    data = config.model_dump()

    # Site settings
    if site_name := get_env_or_none(ENV_SITE_NAME):
        data["site"]["name"] = site_name
    if site_password := get_env_or_none(ENV_SITE_PASSWORD):
        data["site"]["site_password"] = site_password

    # Database settings
    if db_type := get_env_or_none(ENV_DB_TYPE):
        data["database"]["type"] = db_type
    if db_host := get_env_or_none(ENV_DB_HOST):
        data["database"]["host"] = db_host
    if db_port := get_env_int(ENV_DB_PORT):
        data["database"]["port"] = db_port
    if db_name := get_env_or_none(ENV_DB_NAME):
        data["database"]["name"] = db_name
    if db_user := get_env_or_none(ENV_DB_USER):
        data["database"]["user"] = db_user
    if db_password := get_env_or_none(ENV_DB_PASSWORD):
        data["database"]["password"] = db_password
    if db_schema := get_env_or_none(ENV_DB_SCHEMA):
        data["database"]["schema"] = db_schema
    if admin_db_user := get_env_or_none(ENV_ADMIN_DB_USER):
        data["database"]["admin_user"] = admin_db_user
    if admin_db_password := get_env_or_none(ENV_ADMIN_DB_PASSWORD):
        data["database"]["admin_password"] = admin_db_password

    # Redis settings
    if redis_host := get_env_or_none(ENV_REDIS_HOST):
        data["redis"]["host"] = redis_host
    if redis_cache_port := get_env_int(ENV_REDIS_CACHE_PORT):
        data["redis"]["cache_port"] = redis_cache_port
    if redis_queue_port := get_env_int(ENV_REDIS_QUEUE_PORT):
        data["redis"]["queue_port"] = redis_queue_port

    # Bench settings
    if bench_path := get_env_or_none(ENV_BENCH_PATH):
        data["bench"]["path"] = bench_path
    if bench_port := get_env_int(ENV_PORT):
        data["bench"]["port"] = bench_port
    data["bench"]["developer_mode"] = get_env_bool(ENV_DEVELOPER_MODE, default=True)

    # Binary paths
    if node_bin_dir := get_env_or_none(ENV_NODE_BIN_DIR):
        data["binaries"]["node"]["bin_dir"] = node_bin_dir
    if wkhtmltopdf_bin_dir := get_env_or_none(ENV_WKHTMLTOPDF_BIN_DIR):
        data["binaries"]["wkhtmltopdf"]["bin_dir"] = wkhtmltopdf_bin_dir

    # Frappe settings
    if frappe_branch := get_env_or_none(ENV_FRAPPE_BRANCH):
        data["frappe"]["branch"] = frappe_branch
        # Also update apps to use the same branch
        for app in data["apps"]:
            app["branch"] = frappe_branch

    # Mode setting
    if mode := get_env_or_none(ENV_MODE):
        mode_lower = mode.lower()
        if mode_lower not in ("admin", "user"):
            raise ValueError(f"Invalid {ENV_MODE}: '{mode}'. Must be 'admin' or 'user'")
        data["mode"] = mode_lower

    # Force reinstall setting
    data["force_reinstall"] = get_env_bool(ENV_FORCE_REINSTALL, default=False)

    return RealtimexConfig.model_validate(data)


def get_missing_required_env_vars() -> list[str]:
    """Get list of missing required environment variables.

    REALTIMEX_MODE must be explicitly set (no default).
    Admin mode requires: schema, site_password, admin_db credentials.
    User mode only requires base DB credentials.

    Returns:
        List of missing environment variable names.
    """
    # Mode is always required - no silent defaults
    required = [ENV_MODE]

    mode = (get_env_or_none(ENV_MODE) or "").lower()

    # Base requirements for both modes
    required.extend([
        ENV_SITE_NAME,
        ENV_DB_NAME,
        ENV_DB_USER,
        ENV_DB_PASSWORD,
    ])

    # Admin mode requires additional credentials for setup
    if mode == "admin":
        required.extend([
            ENV_DB_SCHEMA,           # Schema name (required for setup)
            ENV_SITE_PASSWORD,       # Frappe Administrator password
            ENV_ADMIN_DB_USER,       # Root DB user for CREATE DATABASE
            ENV_ADMIN_DB_PASSWORD,   # Root DB password
        ])

    return [var for var in required if not get_env_or_none(var)]


def print_env_var_help() -> None:
    """Print help for environment variables."""
    from rich.console import Console
    from rich.table import Table

    console = Console()

    table = Table(title="Environment Variables", show_header=True, header_style="bold")
    table.add_column("Variable", style="cyan")
    table.add_column("Required", style="yellow")
    table.add_column("Default")
    table.add_column("Description")

    env_vars = [
        (ENV_MODE, "Yes", "-", "Operational mode: 'admin' (setup) or 'user' (run only)"),
        (ENV_SITE_NAME, "Yes", "-", "Site name (e.g., mysite.localhost)"),
        (ENV_SITE_PASSWORD, "Admin", "-", "Frappe Administrator password (required in admin mode)"),
        (ENV_DB_NAME, "Yes", "-", "PostgreSQL database name"),
        (ENV_DB_USER, "Yes", "-", "PostgreSQL username (site credentials)"),
        (ENV_DB_PASSWORD, "Yes", "-", "PostgreSQL password (site credentials)"),
        (ENV_ADMIN_DB_USER, "Admin", "-", "Root DB username for CREATE DATABASE (admin mode)"),
        (ENV_ADMIN_DB_PASSWORD, "Admin", "-", "Root DB password for CREATE DATABASE (admin mode)"),
        (ENV_DB_HOST, "No", "localhost", "PostgreSQL host"),
        (ENV_DB_PORT, "No", "5432", "PostgreSQL port"),
        (ENV_DB_SCHEMA, "Admin", "-", "PostgreSQL schema (required for setup)"),
        (ENV_DB_TYPE, "No", "postgres", "Database type"),
        (ENV_REDIS_HOST, "No", "127.0.0.1", "Redis host"),
        (ENV_BENCH_PATH, "No", "~/.realtimex.ai/storage/local-apps/frappe-bench", "Bench path"),
        (ENV_NODE_BIN_DIR, "No", "-", "Path to bundled Node.js bin directory"),
        (ENV_DEVELOPER_MODE, "No", "true", "Enable developer mode"),
        (ENV_FORCE_REINSTALL, "No", "false", "Force delete and reinstall (for recovery)"),
    ]

    for var, required, default, desc in env_vars:
        table.add_row(var, required, default, desc)

    console.print(table)

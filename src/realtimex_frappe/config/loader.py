"""Configuration file loading and writing utilities."""

import json
from pathlib import Path
from typing import Optional

from .schema import AppConfig, RealtimexConfig


# Path to the bundled default.json
DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "config" / "default.json"


def load_config(config_path: str | Path) -> RealtimexConfig:
    """Load configuration from a JSON file."""
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with open(path) as f:
        data = json.load(f)

    return RealtimexConfig.model_validate(data)


def get_default_config() -> RealtimexConfig:
    """Get the default configuration from bundled default.json.

    Loads configuration from the package's config/default.json file,
    which contains the configured Frappe/ERPNext repositories and branches.
    Falls back to hardcoded defaults if the file is not found.
    """
    if DEFAULT_CONFIG_PATH.exists():
        return load_config(DEFAULT_CONFIG_PATH)

    # Fallback to hardcoded defaults only if bundled config is missing
    return RealtimexConfig(
        apps=[
            AppConfig(
                name="erpnext",
                url="https://github.com/frappe/erpnext.git",
                branch="version-15",
                install=True,
            )
        ]
    )


def write_default_config(output_path: str | Path) -> None:
    """Write the default configuration to a JSON file."""
    path = Path(output_path)
    config = get_default_config()

    # Convert to dict and handle Path objects
    data = json.loads(config.model_dump_json())

    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def write_config(config: RealtimexConfig, output_path: str | Path) -> None:
    """Write a configuration to a JSON file."""
    path = Path(output_path)
    data = json.loads(config.model_dump_json())

    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def merge_config_with_cli(
    config: Optional[RealtimexConfig],
    site_name: Optional[str] = None,
    admin_password: Optional[str] = None,
    db_host: Optional[str] = None,
    db_port: Optional[int] = None,
    db_name: Optional[str] = None,
    db_user: Optional[str] = None,
    db_password: Optional[str] = None,
    bench_path: Optional[str] = None,
) -> RealtimexConfig:
    """Merge configuration file with CLI options.

    CLI options take precedence over config file values.
    """
    base_config = config or get_default_config()

    return base_config.with_overrides(
        site_name=site_name,
        admin_password=admin_password,
        db_host=db_host,
        db_port=db_port,
        db_name=db_name,
        db_user=db_user,
        db_password=db_password,
        bench_path=bench_path,
    )

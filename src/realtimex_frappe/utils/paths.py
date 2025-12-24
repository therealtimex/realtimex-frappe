"""RealTimeX path utilities for persistent storage."""

import os
from pathlib import Path


def get_realtimex_user_dir() -> str:
    """Returns the path to the .realtimex.ai user directory.

    This is the base directory for all RealTimeX persistent storage.

    Returns:
        Path to the user directory (e.g., ~/.realtimex.ai)
    """
    return os.path.join(os.path.expanduser("~"), ".realtimex.ai")


def get_default_bench_path() -> str:
    """Returns the default path for Frappe bench installation.

    The bench is stored in a persistent, well-defined location rather
    than the current working directory. This ensures the bench persists
    across application restarts and is not affected by where the command
    is run from.

    Structure:
        ~/.realtimex.ai/storage/local-apps/frappe-bench/
        
    The `local-apps` directory hosts multiple applications, with
    `frappe-bench` being the dedicated subfolder for the Frappe bench.

    Returns:
        Path to the default bench location (~/.realtimex.ai/storage/local-apps/frappe-bench)
    """
    return os.path.join(get_realtimex_user_dir(), "storage", "local-apps", "frappe-bench")


def ensure_bench_directory() -> Path:
    """Ensure the bench parent directory exists.

    Creates the ~/.realtimex.ai/storage directory if it doesn't exist.

    Returns:
        Path to the storage directory.
    """
    bench_path = Path(get_default_bench_path())
    storage_dir = bench_path.parent

    if not storage_dir.exists():
        storage_dir.mkdir(parents=True, exist_ok=True)

    return storage_dir

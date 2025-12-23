"""Environment configuration utilities for bundled binaries."""

import os
import shutil
from pathlib import Path
from typing import NamedTuple

from ..config.schema import RealtimexConfig


class BinaryValidationResult(NamedTuple):
    """Result of binary validation."""

    available: list[str]
    missing: list[str]

    @property
    def is_valid(self) -> bool:
        """Check if all required binaries are available."""
        return len(self.missing) == 0


def build_environment(config: RealtimexConfig) -> dict[str, str]:
    """Build environment variables with custom binary paths prepended to PATH.

    This allows bench commands to find bundled Node.js, yarn, npm, and wkhtmltopdf
    binaries instead of system-installed ones.

    Args:
        config: The realtimex configuration.

    Returns:
        A copy of the current environment with custom paths prepended.
    """
    env = os.environ.copy()

    # Collect custom bin directories
    custom_paths: list[str] = []

    # Add Node.js bin directory (contains node, npm, yarn if installed globally)
    if config.binaries.node.bin_dir:
        node_bin = Path(config.binaries.node.bin_dir)
        if node_bin.exists():
            custom_paths.append(str(node_bin.resolve()))

    # Add wkhtmltopdf bin directory
    if config.binaries.wkhtmltopdf.bin_dir:
        wk_bin = Path(config.binaries.wkhtmltopdf.bin_dir)
        if wk_bin.exists():
            custom_paths.append(str(wk_bin.resolve()))

    # Prepend custom paths to PATH
    if custom_paths:
        current_path = env.get("PATH", "")
        env["PATH"] = os.pathsep.join(custom_paths + [current_path])

    return env


def validate_binaries(
    config: RealtimexConfig,
    required_binaries: list[str] | None = None,
) -> BinaryValidationResult:
    """Validate that required binaries are available.

    This temporarily updates PATH to include bundled binary directories,
    then checks for the presence of each required binary.

    Args:
        config: The realtimex configuration.
        required_binaries: List of binary names to check. Defaults to
            ["node", "npm", "yarn", "wkhtmltopdf"].

    Returns:
        A BinaryValidationResult with lists of available and missing binaries.
    """
    if required_binaries is None:
        required_binaries = ["node", "npm", "yarn", "wkhtmltopdf"]

    env = build_environment(config)
    original_path = os.environ.get("PATH", "")

    try:
        # Temporarily update PATH for shutil.which to use
        os.environ["PATH"] = env["PATH"]

        available: list[str] = []
        missing: list[str] = []

        for binary in required_binaries:
            if shutil.which(binary):
                available.append(binary)
            else:
                missing.append(binary)

        return BinaryValidationResult(available=available, missing=missing)
    finally:
        os.environ["PATH"] = original_path


def get_binary_path(
    binary_name: str,
    config: RealtimexConfig,
) -> str | None:
    """Get the full path to a binary using the custom environment.

    Args:
        binary_name: Name of the binary to find.
        config: The realtimex configuration.

    Returns:
        The full path to the binary, or None if not found.
    """
    env = build_environment(config)
    original_path = os.environ.get("PATH", "")

    try:
        os.environ["PATH"] = env["PATH"]
        return shutil.which(binary_name)
    finally:
        os.environ["PATH"] = original_path

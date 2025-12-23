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


# System prerequisites that must be installed on the host system
# These cannot be bundled and must be validated before running
SYSTEM_PREREQUISITES = {
    "git": {
        "required": True,
        "description": "Git version control system",
        "install_hint": {
            "darwin": "xcode-select --install",
            "linux": "sudo apt install git",
        },
    },
    "pkg-config": {
        "required": True,
        "description": "Package config tool (required for building Python packages)",
        "install_hint": {
            "darwin": "xcode-select --install",
            "linux": "sudo apt install pkg-config",
        },
    },
    "wkhtmltopdf": {
        "required": True,
        "description": "PDF generation tool (required for printing)",
        "install_hint": {
            "darwin": (
                "Download from https://github.com/wkhtmltopdf/packaging/releases\n"
                "    Or: brew install wkhtmltopdf"
            ),
            "linux": (
                "sudo apt install xvfb libfontconfig\n"
                "    Download .deb from https://wkhtmltopdf.org/downloads.html\n"
                "    Then: sudo dpkg -i wkhtmltox_*.deb"
            ),
        },
    },
}

# Bundled binaries that can be provided via config
BUNDLED_BINARIES = {
    "node": {
        "required": True,
        "description": "Node.js runtime",
    },
    "npm": {
        "required": True,
        "description": "Node.js package manager",
    },
    "yarn": {
        "required": False,
        "description": "Yarn package manager (optional)",
    },
}


class PrerequisiteValidationResult(NamedTuple):
    """Result of system prerequisite validation."""

    available: list[str]
    missing_required: list[str]
    missing_optional: list[str]

    @property
    def is_valid(self) -> bool:
        """Check if all required prerequisites are available."""
        return len(self.missing_required) == 0


def validate_system_prerequisites() -> PrerequisiteValidationResult:
    """Validate that system prerequisites are installed.

    These are dependencies that must be installed on the host system
    and cannot be bundled (e.g., git, pkg-config).

    Returns:
        PrerequisiteValidationResult with available and missing prerequisites.
    """
    available: list[str] = []
    missing_required: list[str] = []
    missing_optional: list[str] = []

    for binary, info in SYSTEM_PREREQUISITES.items():
        if shutil.which(binary):
            available.append(binary)
        elif info["required"]:
            missing_required.append(binary)
        else:
            missing_optional.append(binary)

    return PrerequisiteValidationResult(
        available=available,
        missing_required=missing_required,
        missing_optional=missing_optional,
    )


def get_prerequisite_install_hint(binary: str) -> str | None:
    """Get installation hint for a missing prerequisite.

    Args:
        binary: Name of the prerequisite.

    Returns:
        Installation command hint, or None if not found.
    """
    import sys

    if binary not in SYSTEM_PREREQUISITES:
        return None

    hints = SYSTEM_PREREQUISITES[binary].get("install_hint", {})

    if sys.platform == "darwin":
        return hints.get("darwin")
    else:
        return hints.get("linux")


def validate_all_prerequisites(
    config: RealtimexConfig,
) -> tuple[PrerequisiteValidationResult, BinaryValidationResult]:
    """Validate both system prerequisites and bundled binaries.

    Args:
        config: The realtimex configuration.

    Returns:
        Tuple of (system_result, binaries_result).
    """
    system_result = validate_system_prerequisites()

    required_binaries = [
        name for name, info in BUNDLED_BINARIES.items() if info["required"]
    ]
    binaries_result = validate_binaries(config, required_binaries)

    return system_result, binaries_result


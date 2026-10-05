#!/usr/bin/env python3
"""Check and install Image Sorter's declared Python dependencies."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


class PackageUpdateError(RuntimeError):
    """Raised when required packages cannot be installed."""


def ensure_packages(requirements_file: Path | None = None) -> None:
    """Use the current interpreter's pip to satisfy the requirements file."""
    requirements = requirements_file or Path(__file__).with_name("requirements.txt")
    if not requirements.is_file():
        raise PackageUpdateError(f"Requirements file not found: {requirements}")

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "-r",
                str(requirements),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError as error:
        raise PackageUpdateError(f"Could not run pip: {error}") from error

    if result.returncode:
        details = (result.stderr or result.stdout).strip()
        message = f"Could not install required packages using {sys.executable}."
        if details:
            message = f"{message}\n\n{details}"
        raise PackageUpdateError(message)


def main() -> int:
    try:
        ensure_packages()
    except PackageUpdateError as error:
        print(error, file=sys.stderr)
        return 1
    print(f"Required packages are ready for {sys.executable}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

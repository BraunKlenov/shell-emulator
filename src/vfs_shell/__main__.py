"""Entry point: ``python -m vfs_shell``."""

import sys

from .gui import run_gui


def main():
    """Start the graphical shell and return its exit code."""
    return run_gui()


if __name__ == "__main__":
    sys.exit(main())
